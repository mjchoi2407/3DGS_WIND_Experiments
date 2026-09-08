import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from wind3dgs.evaluation import teacher_shell_precision_audit as audit
from wind3dgs.evaluation import teacher_shell_refinement_audit as refinement
from wind3dgs.evaluation import teacher_shell_temporal_audit as temporal
from wind3dgs.teacher import shell_dynamics as dynamics
from wind3dgs.teacher import shell_newmark_acceleration as acceleration
from wind3dgs.teacher.physics_registry import content_hash

workspace = Path.cwd()
source = audit._validate_sources(workspace/'experiments/artifacts/runs/teacher_shell_dynamics/20260907_reference_v1',
    workspace/'experiments/artifacts/runs/teacher_shell_temporal/20260908_reference_v1', temporal._Budget(300))
precision_folder = workspace/'experiments/artifacts/runs/teacher_shell_precision/20260908_reference_v1'
precision_report, precision_identity = refinement._validate_precision_header(precision_folder, source, temporal._Budget(120))
baseline_row, baseline_comparison = refinement._load_baseline(precision_folder, precision_report, source, temporal._Budget(120))
baseline_arrays = audit._load_arrays(precision_folder/'cases'/refinement.BASELINE_ID/'sample.npz', baseline_row['sample_arrays'])
source_identity = {**source['identity'], **precision_identity}
model, initial = source['model'], source['initial']
zero = np.zeros_like(initial.positions_m)
base = workspace/'experiments/artifacts/runs/teacher_shell_refinement'
reports, results, prior_arrays = [], [], {}
for name in ('20260908_reference_v1', '20260908_reference_v1_replay'):
    folder = base/name
    report, manifest, environment = (temporal._json(folder/k) for k in ('report.json', 'manifest.json', 'environment.json'))
    assert report['report_sha256'] == content_hash({k:v for k,v in report.items() if k != 'report_sha256'}) == manifest['report_sha256']
    assert report['source'] == source_identity
    assert not report['teacher_eligible'] and report['convergence_status'] == 'not_assessed'
    assert report['full_response_check'] == 'not_assessed' and not manifest['pending_cases']
    assert report['policy'] == temporal._json(folder/'config.json')['policy'] == refinement.TeacherShellRefinementPolicy().to_dict()
    assert report['solver_policy'] == acceleration.ShellAccelerationNewmarkPolicy().to_dict()
    assert environment['sources_sha256'] == manifest['software'] == refinement._environment()['sources_sha256']
    for key in refinement.CHECKS: assert report[key] == manifest[key]
    actual_files = {str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    assert actual_files == set(manifest['outputs'])
    for filename, entry in manifest['outputs'].items(): assert temporal._file_entry(folder/filename) == entry
    for filename, sha in environment['sources_sha256'].items():
        assert hashlib.sha256((workspace/'code'/filename).read_bytes()).hexdigest() == sha
    assert content_hash(temporal._json(folder/'config.json')) == manifest['config_sha256']
    stats = {'run': str(folder.relative_to(workspace/'experiments')), 'status': 'passed',
        'source_files': len(environment['sources_sha256']), 'inventoried_files': len(actual_files),
        'checked_frames': 0, 'accepted_candidate_steps': 0, 'iteration_vectors': 0, 'checked_trial_vectors': 0,
        'checked_chunks': 0, 'checked_linear_corrections': 0, 'max_recomputed_linear_ratio': 0., 'case_elapsed_s': 0., 'max_residual_to_limit_ratio': 0., 'max_kinematic_ratio': 0.}
    def replay_array(key, value):
        if not reports: prior_arrays[key] = value.copy()
        else: np.testing.assert_array_equal(value, prior_arrays[key])
    with np.load(folder/'modal_basis.npz', allow_pickle=False) as modal_arrays:
        for k in modal_arrays.files:
            np.testing.assert_array_equal(modal_arrays[k], source['modal'][k]); replay_array('modal/'+k, modal_arrays[k])
    sample_groups = {refinement.BASELINE_ID: baseline_arrays}
    for row in report['cases']:
        case_id = row['case_id']
        if row['origin'] == 'reused_verified_precision_v1':
            assert row == {**baseline_row, 'origin': 'reused_verified_precision_v1'}
            assert not (folder/'cases'/case_id).exists()
            continue
        assert row['origin'] == 'new_acceleration_rollout'
        case = folder/'cases'/case_id
        assert temporal._json(case/'summary.json') == {k:v for k,v in row.items() if k != 'origin'}
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
        refinement._verify_acceleration_states(model, initial, arrays, traces, row, temporal._Budget(120))
        state = initial
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
            kin = acceleration._kinematic_summary(acceleration._kinematic_arrays(state.positions_m,state.velocities_m_s,a0,x,v,b,dt))
            assert kin == trace['kinematics'] and kin['passed']
            stats['max_kinematic_ratio'] = max(stats['max_kinematic_ratio'],kin['position_defect_m_max_ratio'],kin['velocity_defect_m_s_max_ratio'])
            def vector(entry,key): return vectors[entry['vectors'][key]['npz_key']]
            next_acceleration = a0
            for iteration,entry in enumerate(trace['iterations']):
                bi,xi = vector(entry,'acceleration_m_s2'),vector(entry,'position_m')
                assert entry['iteration'] == iteration
                np.testing.assert_array_equal(bi,next_acceleration)
                expected_x = state.positions_m+(dt*state.velocities_m_s+c*(a0+bi))
                np.testing.assert_array_equal(xi,expected_x)
                ri = model.masses_kg[:,None]*bi-dynamics._elastic(model,xi)['force_n']
                assert dynamics._force_norm(model,ri) == entry['residual_m_s2']
                db,dx = vector(entry,'acceleration_correction_m_s2'),vector(entry,'position_correction_m')
                np.testing.assert_array_equal(dx,c*db)
                assert dynamics._displacement_norm(model,dx)/dynamics._scales(model)[0] == entry['correction_over_length']
                predictor = state.positions_m+dt*state.velocities_m_s+c*a0
                correction_limit = row['policy']['correction_atol_length']+row['policy']['correction_rtol']*max(
                    dynamics._displacement_norm(model,xi-model.structure.rest_positions_m),
                    dynamics._displacement_norm(model,predictor-model.structure.rest_positions_m))/dynamics._scales(model)[0]
                assert entry['correction_limit'] == correction_limit
                if 'linear' in entry:
                    assert entry['linear']['passed'] and entry['linear']['true_residual_norm'] <= entry['linear']['residual_bound']
                    mass = model.masses_kg[:,None]
                    hvp = dynamics._hvp(model,xi,db)
                    w = 1/np.sqrt(mass[model.free_mask])
                    rhs_norm = float(np.linalg.norm(w*ri[model.free_mask]))
                    assert entry['linear']['residual_bound'] == row['policy']['linear_rtol']*rhs_norm
                    tangent = mass*db+c*hvp
                    scaled_residual = float(np.linalg.norm(w*(tangent+ri)[model.free_mask]))
                    terms = rhs_norm+float(np.linalg.norm(w*(mass*db)[model.free_mask]))+float(np.linalg.norm(c*w*hvp[model.free_mask]))
                    bound_linear = row['policy']['linear_rtol']*rhs_norm+256*np.finfo(float).eps*terms
                    assert scaled_residual <= bound_linear, (case_id,i,scaled_residual,bound_linear)
                    stats['checked_linear_corrections'] += 1
                    stats['max_recomputed_linear_ratio'] = max(stats['max_recomputed_linear_ratio'],scaled_residual/bound_linear)
                if 'line_search' in entry:
                    assert entry['merit'] == .5*float(np.sum((w*ri[model.free_mask])**2))
                    assert entry['slope'] == float(np.sum((w*ri[model.free_mask])*(w*tangent[model.free_mask])))
                    assert entry['linear_residual_force_norm_n'] == float(np.linalg.norm((tangent+ri)[model.free_mask]))
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
                    if trial['accepted']: next_acceleration = bt
                    stats['checked_trial_vectors'] += 1
            final = trace['iterations'][-1]
            assert final['correction_over_length'] <= final['correction_limit']
            np.testing.assert_array_equal(vector(final,'acceleration_m_s2'),b)
            np.testing.assert_array_equal(vector(final,'position_m'),x)
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
        for path in (folder/'chunks'/case_id).glob('steps_*.jsonl'):
            start = max(0,int(path.stem.rsplit('_',1)[1])-1)
            chunk_trace = audit._read_traces(path)
            assert chunk_trace == traces[start:start+len(chunk_trace)]
        sample_groups[case_id] = arrays
        print('사례·반복 벡터 검산 통과:',name,case_id,flush=True)
    for row in report['comparisons']['short']:
        n = row['integration_steps_per_T1']
        calculated = refinement._comparison(source,sample_groups[row['case_id']],n)
        assert calculated == {k:v for k,v in row.items() if k != 'case_id'}
        # Primary와 native energy를 원래 배열에서 따로 계산한다.
        sampled = {k:v[::n//10240] for k,v in sample_groups[row['case_id']].items()}
        weights = model.masses_kg[model.free_mask]/model.masses_kg[model.free_mask].sum()
        for key,scale in (('positions_m',.001),('velocities_m_s',.001*source['omega'])):
            delta = sampled[key][:,model.free_mask]-source['arrays']['reference_b'][key][:513,model.free_mask]
            values = np.sqrt(np.sum(delta*delta*weights[None,:,None],axis=(1,2)))/scale
            np.testing.assert_allclose(float(values.max()),row['metrics'][key]['total']['normalized'],rtol=3e-14,atol=1e-15)
        energy = sum(sample_groups[row['case_id']][k] for k in ('kinetic_energy_j','membrane_energy_j','bending_energy_j'))
        np.testing.assert_allclose(float(np.max(abs(energy-energy[0]))/abs(energy[0])),row['max_relative_energy_drift'],rtol=0,atol=2*np.finfo(float).eps)
        assert row['comparison_scope'] == 'maximum_on_fixed_513_sample_times' and row['energy_scope'] == 'all_native_frames'
    with (folder/'comparisons.csv').open() as stream: csv_rows = list(csv.DictReader(stream))
    expected_csv = [{k:str(v) for k,v in row.items()} for row in refinement._csv_rows(report)]
    assert csv_rows == expected_csv
    floor = {k:source['reference_comparison']['metrics'][k]['total']['normalized'] for k in ('positions_m','velocities_m_s')}
    details = temporal._response_status(report['comparisons']['short'],refinement.TeacherShellRefinementPolicy(),floor)
    assert details == report['short_response_details'] and details['status'] == report['short_response_check']
    assert report['baseline_origin'] == 'reused_verified_precision_v1' and report['reference_origin'] == 'reused_verified_temporal_v1'
    reports.append(report);results.append(stats)
assert reports[0] == reports[1]
result = {'schema_version':'wind3dgs.shell_refinement_verification.v1','status':'passed','teacher_eligible':False,
    'convergence_status':'not_assessed','runs':results,'report_sha256':reports[0]['report_sha256'],
    'replay_reports_arrays_trace_hashes_equal':True,'state_and_iteration_physics_recomputed':True,'baseline_reused_steps_verified':512, 'linear_correction_residuals_recomputed':True,'comparisons_csv_recomputed':True,
    'meaning':'기록 무결성·수치 재검산·독립 재실행 일치이며 물리 수렴 판정과 구분한다.'}
Path('/tmp/wind3dgs_shell_refinement_verification.json').write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
