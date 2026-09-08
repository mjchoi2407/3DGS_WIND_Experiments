import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from wind3dgs.evaluation import teacher_shell_precision_audit as audit
from wind3dgs.evaluation import teacher_shell_temporal_audit as temporal
from wind3dgs.teacher import shell_dynamics as dynamics
from wind3dgs.teacher import shell_newmark_acceleration as acceleration
from wind3dgs.teacher.physics_registry import content_hash

workspace = Path.cwd()
source = audit._validate_sources(workspace/'experiments/artifacts/runs/teacher_shell_dynamics/20260907_reference_v1',
    workspace/'experiments/artifacts/runs/teacher_shell_temporal/20260908_reference_v1', temporal._Budget(180))
model, initial, restart = source['model'], source['initial'], source['restart']
zero = np.zeros_like(initial.positions_m)
base = workspace/'experiments/artifacts/runs/teacher_shell_precision'
reports, results, prior_arrays = [], [], {}
for name in ('20260908_reference_v1', '20260908_reference_v1_replay'):
    folder = base/name
    report, manifest, environment = (temporal._json(folder/k) for k in ('report.json', 'manifest.json', 'environment.json'))
    assert report['report_sha256'] == content_hash({k:v for k,v in report.items() if k != 'report_sha256'}) == manifest['report_sha256']
    assert report['source'] == source['identity']
    assert not report['teacher_eligible'] and report['convergence_status'] == 'not_assessed'
    assert report['full_response_check'] == 'not_assessed' and not manifest['pending_cases']
    actual_files = {str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    assert actual_files == set(manifest['outputs'])
    for filename, entry in manifest['outputs'].items(): assert temporal._file_entry(folder/filename) == entry
    for filename, sha in environment['sources_sha256'].items():
        assert hashlib.sha256((workspace/'code'/filename).read_bytes()).hexdigest() == sha
    assert content_hash(temporal._json(folder/'config.json')) == manifest['config_sha256']
    stats = {'run': str(folder.relative_to(workspace/'experiments')), 'status': 'passed',
        'source_files': len(environment['sources_sha256']), 'inventoried_files': len(actual_files),
        'checked_frames': 0, 'accepted_candidate_steps': 0, 'iteration_vectors': 0, 'checked_trial_vectors': 0,
        'checked_chunks': 0, 'case_elapsed_s': 0., 'max_residual_to_limit_ratio': 0., 'max_kinematic_ratio': 0.}
    def replay_array(key, value):
        if not reports: prior_arrays[key] = value.copy()
        else: np.testing.assert_array_equal(value, prior_arrays[key])
    with np.load(folder/'modal_basis.npz', allow_pickle=False) as modal_arrays:
        for k in modal_arrays.files:
            np.testing.assert_array_equal(modal_arrays[k], source['modal'][k]); replay_array('modal/'+k, modal_arrays[k])
    sample_groups = {}
    for row in report['cases']:
        case_id = row['case_id']; case = folder/'cases'/case_id
        assert temporal._json(case/'summary.json') == row
        stats['case_elapsed_s'] += temporal._json(case/'runtime.json')['elapsed_s']
        traces = audit._read_traces(case/'steps.jsonl')
        assert content_hash(temporal._clean(traces)) == row['trace_sha256']
        with np.load(case/'sample.npz', allow_pickle=False) as data: arrays = {k:data[k] for k in data.files}
        assert temporal._identities(arrays) == row['sample_arrays']
        with np.load(case/'iteration_vectors.npz', allow_pickle=False) as data: vectors = {k:data[k] for k in data.files}
        identities = {k:temporal.plate._array_identity(v, 'm/s^2' if k.endswith('m_s2') else 'm') for k,v in vectors.items()}
        assert row['iteration_vectors'] == {'count': len(vectors), 'inventory_sha256': content_hash(identities)}
        used = set()
        def check_references(value):
            if isinstance(value, list):
                for item in value: check_references(item)
            elif isinstance(value, dict):
                if 'npz_key' in value:
                    used.add(value['npz_key']); assert identities[value['npz_key']] == value['identity']
                else:
                    for item in value.values(): check_references(item)
        check_references(traces); check_references(row['failure'])
        assert used == set(vectors)
        for k,v in arrays.items(): replay_array(case_id+'/sample/'+k,v)
        for k,v in vectors.items(): replay_array(case_id+'/vectors/'+k,v)
        stats['iteration_vectors'] += len(vectors);stats['checked_frames'] += len(arrays['time_s'])
        state = restart if row['horizon'] == 'single_step_restart' else initial
        assert row['initial_state'] == state.identity()
        assert row['completed_steps'] == len(traces) == len(arrays['time_s'])-1
        assert np.max(abs(arrays['time_s']-state.time_s-row['dt_s']*np.arange(len(arrays['time_s'])))) < 1e-10*source['period']
        for i in range(len(arrays['time_s'])):
            x,v,b,reaction = (arrays[k][i] for k in ('positions_m','velocities_m_s','accelerations_m_s2','reaction_n'))
            elastic = dynamics._elastic(model,x)
            recalculated = temporal._frame(model, arrays['time_s'][i], x,v,acceleration=b,elastic=elastic)
            for k in temporal.UNITS: np.testing.assert_array_equal(recalculated[k], arrays[k][i])
            norm = dynamics._force_norm(model, model.masses_kg[:,None]*b-elastic['force_n']-reaction)
            if not i:
                for k in ('positions_m','velocities_m_s','accelerations_m_s2'): np.testing.assert_array_equal(arrays[k][0],getattr(state,k))
                continue
            trace = traces[i-1];dt = row['dt_s'];c = .25*dt*dt
            start_elastic = dynamics._elastic(model,state.positions_m)
            a0 = dynamics._acceleration(model,start_elastic,zero)
            bound = 1e-8*dynamics._scales(model)[1]+1e-8*dynamics._force_norm(model,start_elastic['force_n'])
            assert bound == trace['residual_limit_m_s2'] and norm == trace['end_residual_m_s2'] and norm <= bound
            stats['max_residual_to_limit_ratio'] = max(stats['max_residual_to_limit_ratio'],norm/bound)
            if case_id == 'acceleration_restart_5':
                predictor = state.positions_m+dt*state.velocities_m_s+c*a0
                recovered = (x-predictor)/c
                stats['restart_same_position'] = {'direct_acceleration_residual_m_s2': norm,
                    'position_recovered_residual_m_s2': dynamics._force_norm(model,model.masses_kg[:,None]*recovered-elastic['force_n']),
                    'residual_limit_m_s2':bound}
            kin = acceleration._kinematic_summary(acceleration._kinematic_arrays(state.positions_m,state.velocities_m_s,a0,x,v,b,dt))
            assert kin == trace['kinematics'] and kin['passed']
            stats['max_kinematic_ratio'] = max(stats['max_kinematic_ratio'],kin['position_defect_m_max_ratio'],kin['velocity_defect_m_s_max_ratio'])
            def vector(entry,key): return vectors[entry['vectors'][key]['npz_key']]
            for entry in trace['iterations']:
                bi,xi = vector(entry,'acceleration_m_s2'),vector(entry,'position_m')
                expected_x = state.positions_m+(dt*state.velocities_m_s+c*(a0+bi))
                np.testing.assert_array_equal(xi,expected_x)
                ri = model.masses_kg[:,None]*bi-dynamics._elastic(model,xi)['force_n']
                assert dynamics._force_norm(model,ri) == entry['residual_m_s2']
                db,dx = vector(entry,'acceleration_correction_m_s2'),vector(entry,'position_correction_m')
                np.testing.assert_array_equal(dx,c*db)
                assert dynamics._displacement_norm(model,dx)/dynamics._scales(model)[0] == entry['correction_over_length']
                if 'linear' in entry:
                    assert entry['linear']['passed'] and entry['linear']['true_residual_norm'] <= entry['linear']['residual_bound']
                for trial in entry.get('line_search',[]):
                    bt,xt = vector(trial,'acceleration_m_s2'),vector(trial,'position_m')
                    np.testing.assert_array_equal(bt,bi+trial['alpha']*db)
                    np.testing.assert_array_equal(xt,state.positions_m+(dt*state.velocities_m_s+c*(a0+bt)))
                    np.testing.assert_array_equal(vector(trial,'realized_position_change_m'),xt-xi)
                    rt = model.masses_kg[:,None]*bt-dynamics._elastic(model,xt)['force_n']
                    w = 1/np.sqrt(model.masses_kg[model.free_mask,None])
                    merit = .5*float(np.sum((w*rt[model.free_mask])**2))
                    assert merit == trial['merit']
                    assert trial['accepted'] == (merit <= entry['merit']+row['policy']['armijo_c1']*trial['alpha']*entry['slope'])
                    stats['checked_trial_vectors'] += 1
            final = trace['iterations'][-1]
            assert final['correction_over_length'] <= final['correction_limit']
            inputs = {'previous_state_sha256':state.state_sha256,'force':temporal.plate._array_identity(zero,'N'),'policy':row['policy'],'dt_s':dt}
            state = dynamics._state(model,x,v,b,zero,float(arrays['time_s'][i]),state.step_index+1,bound,inputs)
            assert state.state_sha256 == trace['state_sha256']
        assert state.identity() == row['final_state']
        if row['failure']: assert row['failure']['last_state_sha256'] == state.state_sha256
        assert temporal._energy_error(arrays) == row['max_relative_energy_drift']
        stats['accepted_candidate_steps'] += row['completed_steps']
        for path in (folder/'chunks'/case_id).glob('*.npz'):
            kind,start = path.stem.rsplit('_',1);start=int(start)
            with np.load(path,allow_pickle=False) as chunk:
                for k in chunk.files:
                    np.testing.assert_array_equal(chunk[k], arrays[k][start:start+len(chunk[k])] if kind == 'states' else vectors[k])
            stats['checked_chunks'] += 1
        sample_groups[case_id] = arrays
        print('사례·반복 벡터 검산 통과:',name,case_id,flush=True)
    expected_csv = []
    for label, rows in (('reference_b',sum(report['comparisons'].values(),[])),('legacy',report['legacy_comparisons'])):
        for row in rows:
            n,steps,horizon = row['steps_per_T1'],row['compared_steps'],row['horizon']
            actual = sample_groups[row['case_id']]
            reference = temporal._slice(source['arrays']['reference_b'],(steps+1)*(10240//n),10240//n) if label=='reference_b' else temporal._slice(source['arrays'][row['legacy_case_id']],steps+1)
            calculated = temporal._comparison(model,source['modal'],actual,reference,.001,source['omega'],source['period'],n,horizon)
            assert calculated == {k:v for k,v in row.items() if k not in ('case_id','legacy_case_id')}
            m=row['metrics']
            expected_csv.append({'comparison':label,'case_id':row['case_id'],'horizon':horizon,'steps_per_T1':n,'duration_s':row['duration_s'],
                'position_error':m['positions_m']['total']['normalized'],'velocity_error':m['velocities_m_s']['total']['normalized'],
                'velocity_xy_error':m['velocities_m_s']['xy']['normalized'],'velocity_z_error':m['velocities_m_s']['z']['normalized'],'energy_drift':row['max_relative_energy_drift']})
    with (folder/'comparisons.csv').open() as stream: csv_rows = list(csv.DictReader(stream))
    ordering = lambda row: (row['comparison'], row['case_id'])
    assert sorted(csv_rows, key=ordering) == sorted([{k:str(v) for k,v in r.items()} for r in expected_csv], key=ordering)
    if report.get('prefix_check') == 'passed':
        for k,v in sample_groups['acceleration_short_2560'].items():np.testing.assert_array_equal(v,sample_groups['acceleration_full_2560'][k][:len(v)])
    reports.append(report);results.append(stats)
assert reports[0] == reports[1]
result = {'schema_version':'wind3dgs.shell_precision_verification.v1','status':'passed','teacher_eligible':False,
    'convergence_status':'not_assessed','runs':results,'report_sha256':reports[0]['report_sha256'],
    'replay_reports_arrays_trace_hashes_equal':True,'state_and_iteration_physics_recomputed':True,'comparisons_csv_recomputed':True,
    'meaning':'기록 무결성·수치 재검산·독립 재실행 일치이며 물리 수렴 판정과 구분한다.'}
Path('/tmp/wind3dgs_shell_precision_verification.json').write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
