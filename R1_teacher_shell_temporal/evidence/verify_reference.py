import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from wind3dgs.evaluation import teacher_shell_temporal_audit as audit
from wind3dgs.teacher import shell_dynamics as dynamics
from wind3dgs.teacher.physics_registry import content_hash

workspace = Path.cwd()
base = workspace/'experiments/artifacts/runs/teacher_shell_temporal'
source = workspace/'experiments/artifacts/runs/teacher_shell_dynamics/20260907_reference_v1'
model, initial, amplitude, omega1, period, source_cases, source_identity = audit._validate_source(source, audit._Budget(60))
reports, payloads, results = [], [], []
for name in ('20260908_reference_v1', '20260908_reference_v1_replay'):
    folder = base/name
    report = audit._json(folder/'report.json')
    manifest = audit._json(folder/'manifest.json')
    environment = audit._json(folder/'environment.json')
    assert report['report_sha256'] == content_hash({k: v for k, v in report.items() if k != 'report_sha256'})
    assert report['report_sha256'] == manifest['report_sha256']
    assert report['source'] == source_identity
    assert report['source_check'] == report['modal_check'] == report['reference_check'] == 'passed'
    assert not report['teacher_eligible'] and report['convergence_status'] == 'not_assessed'
    assert not manifest['pending_cases'] and manifest['status'] == 'completed'
    all_files = {str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    assert all_files == set(manifest['outputs'])
    for filename, entry in manifest['outputs'].items():
        assert audit._file_entry(folder/filename) == entry
    for filename, sha in environment['sources_sha256'].items():
        assert hashlib.sha256((workspace/'code'/filename).read_bytes()).hexdigest() == sha
    assert content_hash(audit._json(folder/'config.json')) == manifest['config_sha256']
    with (folder/'comparisons.csv').open() as stream:
        csv_rows = list(csv.DictReader(stream))
    expected_rows = []
    for rows in report['comparisons'].values():
        for row in rows:
            metrics = row['metrics']
            expected_rows.append({'horizon': row['horizon'], 'steps_per_T1': row['steps_per_T1'],
                'duration_s': row['duration_s'], 'position_error': metrics['positions_m']['total']['normalized'],
                'velocity_error': metrics['velocities_m_s']['total']['normalized'],
                'velocity_xy_error': metrics['velocities_m_s']['xy']['normalized'],
                'velocity_z_error': metrics['velocities_m_s']['z']['normalized'],
                'energy_drift': row['max_relative_energy_drift']})
    assert csv_rows == [{k: str(v) for k, v in row.items()} for row in expected_rows]
    with np.load(folder/'modal_basis.npz', allow_pickle=False) as data:
        modal_arrays = {k: data[k] for k in data.files}
    assert audit.plate._array_identity(modal_arrays['basis'], 'dimensionless') == report['modal']['basis']
    modal = {'basis': modal_arrays['basis'], 'sqrt_mass': modal_arrays['sqrt_mass'], 'omega': modal_arrays['omega'],
             'groups': report['modal']['clusters']}
    stored_payload = {'modal': modal_arrays}
    statistics = {'run': str(folder.relative_to(workspace/'experiments')), 'status': 'passed',
                  'source_files': len(environment['sources_sha256']), 'inventoried_files': len(all_files),
                  'case_arrays': 0, 'checked_frames': 0, 'checked_chunks': 0, 'newmark_accepted_steps': 0,
                  'max_newmark_x_error_m': 0., 'max_newmark_v_error_m_s': 0.,
                  'max_residual_to_limit_ratio': 0., 'case_elapsed_s': 0.}
    for row in report['cases']:
        case_id = row['case_id']; case = folder/'cases'/case_id
        assert audit._json(case/'summary.json') == row
        traces = [json.loads(line) for line in (case/'steps.jsonl').read_text().splitlines()]
        assert content_hash(audit._clean(traces)) == row['trace_sha256']
        statistics['case_elapsed_s'] += audit._json(case/'runtime.json')['elapsed_s']
        groups = {}
        for kind in ('sample', 'internal') if case_id.startswith('reference_') else ('sample',):
            with np.load(case/(kind+'.npz'), allow_pickle=False) as data:
                arrays = {k: data[k] for k in data.files}
            assert audit._identities(arrays) == row[kind+'_arrays']
            statistics['case_arrays'] += len(arrays)
            statistics['checked_frames'] += len(arrays['time_s'])
            groups[kind] = arrays
            for index, (t, x, v, acceleration, reaction) in enumerate(zip(arrays['time_s'], arrays['positions_m'],
                    arrays['velocities_m_s'], arrays['accelerations_m_s2'], arrays['reaction_n'])):
                dynamics._pins(model, x, v, acceleration)
                elastic = dynamics._elastic(model, x)
                np.testing.assert_array_equal(reaction[model.pinned_mask], -elastic['force_n'][model.pinned_mask])
                assert not np.any(reaction[model.free_mask])
                residual = model.masses_kg[:, None]*acceleration-elastic['force_n']-reaction
                norm = dynamics._force_norm(model, residual)
                if case_id.startswith('reference_'):
                    assert norm < 1e-12
                elif index:
                    bound = traces[index-1]['residual_limit_m_s2']
                    assert norm <= bound
                    statistics['max_residual_to_limit_ratio'] = max(statistics['max_residual_to_limit_ratio'], norm/bound)
                for key in ('membrane_energy_j', 'bending_energy_j'):
                    assert arrays[key][index] == elastic[key]
                assert abs(arrays['kinetic_energy_j'][index]-.5*float(np.sum(model.masses_kg[:, None]*v*v))) < 1e-18
        for path in sorted((folder/'chunks'/case_id).glob('*.npz')):
            kind, start = path.stem.rsplit('_', 1); start = int(start)
            source_kind = 'sample' if kind == 'states' else kind
            with np.load(path, allow_pickle=False) as data:
                for key in data.files:
                    np.testing.assert_array_equal(data[key], groups[source_kind][key][start:start+len(data[key])])
            statistics['checked_chunks'] += 1
        if case_id.startswith('newmark_'):
            arrays = groups['sample']; state = initial
            for i, trace in enumerate(traces, 1):
                dt = row['dt_s']; x, v, acc = (arrays[k][i] for k in ('positions_m', 'velocities_m_s', 'accelerations_m_s2'))
                start = dynamics._elastic(model, state.positions_m)
                start_a = dynamics._acceleration(model, start, np.zeros_like(x))
                ex = float(np.max(np.abs(x-state.positions_m-dt*state.velocities_m_s-.25*dt**2*(start_a+acc))))
                ev = float(np.max(np.abs(v-state.velocities_m_s-.5*dt*(start_a+acc))))
                assert ex < 1e-12 and ev < 1e-12
                statistics['max_newmark_x_error_m'] = max(statistics['max_newmark_x_error_m'], ex)
                statistics['max_newmark_v_error_m_s'] = max(statistics['max_newmark_v_error_m_s'], ev)
                inputs = {'previous_state_sha256': state.state_sha256,
                          'force': audit.plate._array_identity(np.zeros_like(x), 'N'), 'policy': row['policy'], 'dt_s': dt}
                state = dynamics._state(model, x, v, acc, np.zeros_like(x), float(arrays['time_s'][i]), i,
                                        trace['residual_limit_m_s2'], inputs)
                assert state.state_sha256 == trace['state_sha256']
            assert state.identity() == row['final_state']
            assert row['completed_steps'] == len(traces) == len(arrays['time_s'])-1
            statistics['newmark_accepted_steps'] += len(traces)
            if row['failure']:
                assert row['failure']['last_state_sha256'] == state.state_sha256
        stored_payload[case_id] = groups
        print('사례 검산 통과:', name, case_id, flush=True)
    reference = stored_payload['reference_b']['sample']
    assert audit._comparison(model, modal, stored_payload['reference_a']['sample'], reference,
        amplitude, omega1, period, 10240, 'full') == report['reference_comparison']
    for row in report['previous_320_comparisons']:
        n = row['steps_per_T1']
        assert audit._comparison(model, modal, audit._source_frames(model, source_cases[n]),
            audit._slice(source_cases[320]['arrays'], stride=320//n), amplitude, omega1, period, n, 'full') == row
    for horizon, rows in report['comparisons'].items():
        for row in rows:
            n = row['steps_per_T1']; steps = row['compared_steps']; stride = 10240//n
            if n in source_cases:
                actual = audit._source_frames(model, source_cases[n])
            else:
                case_id = f'newmark_full_{n}' if n <= 2560 else f'newmark_short_{n}'
                actual = stored_payload[case_id]['sample']
            recalculated = audit._comparison(model, modal, audit._slice(actual, steps+1),
                audit._slice(reference, (steps+1)*stride, stride), amplitude, omega1, period, n, horizon)
            assert recalculated == row
    reports.append(report); payloads.append(stored_payload); results.append(statistics)
assert reports[0] == reports[1]
for case_id, groups in payloads[0].items():
    if case_id == 'modal':
        for key, array in groups.items(): np.testing.assert_array_equal(array, payloads[1][case_id][key])
    else:
        for kind, arrays in groups.items():
            for key, array in arrays.items(): np.testing.assert_array_equal(array, payloads[1][case_id][kind][key])
result = {'schema_version': 'wind3dgs.shell_temporal_verification.v1', 'status': 'passed',
          'teacher_eligible': False, 'convergence_status': 'not_assessed', 'runs': results,
          'report_sha256': reports[0]['report_sha256'], 'replay_reports_equal': True,
          'replay_arrays_and_trace_hashes_equal': True, 'comparisons_recomputed': True,
          'meaning': '무결성·기록 수치의 재검산과 독립 재실행 일치이며 물리 수렴 판정과 구분한다.'}
Path('/tmp/wind3dgs_shell_temporal_verification.json').write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)+'\n')
print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
