import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from wind3dgs.evaluation import teacher_shell_dynamics_audit as audit
from wind3dgs.teacher import shell_dynamics as dynamics
from wind3dgs.teacher.physics_registry import content_hash
from wind3dgs.evaluation.teacher_plate_reference import _array_identity

workspace = Path.cwd()
base = workspace/'experiments/artifacts/runs/teacher_shell_dynamics'
names = ('20260907_reference_v1', '20260907_reference_v1_replay')
reports, arrays_by_run, results = [], [], []
for name in names:
    folder = base/name
    report = json.loads((folder/'report.json').read_text())
    manifest = json.loads((folder/'manifest.json').read_text())
    environment = json.loads((folder/'environment.json').read_text())
    assert content_hash({k: v for k, v in report.items() if k != 'report_sha256'}) == report['report_sha256']
    assert manifest['status'] == 'completed' and not manifest['pending_cases'] and manifest['failure'] is None
    assert manifest['report_sha256'] == report['report_sha256']
    assert len(manifest['cases']) == len(report['rows']) == 19
    assert manifest['config_sha256'] == content_hash(json.loads((folder/'config.json').read_text()))
    assert json.loads((folder/'config.json').read_text()) == report['spec']
    for source, sha in environment['sources_sha256'].items():
        assert hashlib.sha256((workspace/'code'/source).read_bytes()).hexdigest() == sha, source
    files = {str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    assert files == set(manifest['outputs'])
    for filename, entry in manifest['outputs'].items():
        data = (folder/filename).read_bytes()
        assert len(data) == entry['bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256'], filename
    for expected, actual in zip(report['rows'], csv.DictReader((folder/'cases.csv').open())):
        assert all(str(expected[k]) == v for k, v in actual.items())
    spec = audit.TeacherShellDynamicsSpec.from_dict(report['spec'])
    result = {'run': str(folder.relative_to(workspace/'experiments')), 'status': 'passed',
              'source_files': len(environment['sources_sha256']), 'inventoried_files': len(files),
              'accepted_steps': 0, 'state_arrays': 0, 'max_newmark_x_error_m': 0.,
              'max_newmark_v_error_m_s': 0., 'max_residual_to_limit_ratio': 0.,
              'max_energy_record_difference_j': 0., 'step_elapsed_s': 0.}
    saved = {}
    for row in report['rows']:
        case_id = row['case_id']; case = folder/'cases'/case_id
        summary = json.loads((case/'summary.json').read_text())
        assert all(row[k] == v for k, v in summary.items())
        trace = [json.loads(line) for line in (case/'steps.jsonl').read_text().splitlines()]
        assert content_hash([{k: v for k, v in t.items() if k != 'elapsed_s'} for t in trace]) == row['step_payload_sha256']
        with np.load(case/'states.npz', allow_pickle=False) as data:
            arrays = {k: data[k] for k in data.files}
        saved[case_id] = arrays
        assert set(arrays) == set(row['state_arrays'])
        for key, array in arrays.items():
            assert _array_identity(array, row['state_arrays'][key]['unit']) == row['state_arrays'][key]
        pins = 'all' if case_id == 'all_pinned_reaction' else ('none' if case_id in ('translation', 'constant_acceleration', 'force_transition') else 'left')
        diagonal = case_id.split('_')[1] if case_id.startswith('linear_') else 'forward'
        model = audit._fixture(spec, 4, diagonal, row['structure_mode'], pins=pins)
        assert model.model_sha256 == row['model_sha256']
        state = dynamics.initialize_shell_dynamics(model, arrays['positions_m'][0], arrays['velocities_m_s'][0], held_force_n=arrays['held_force_n'][0])
        assert state.identity() == row['initial_state']
        for i, t in enumerate(trace, 1):
            x, v, a, force = (arrays[k][i] for k in ('positions_m', 'velocities_m_s', 'accelerations_m_s2', 'held_force_n'))
            dt = row['duration_s']/row['requested_steps']
            start = dynamics._elastic(model, state.positions_m)
            elastic = dynamics._elastic(model, x)
            start_a = dynamics._acceleration(model, start, force)
            assert _array_identity(start_a, 'm/s^2') == t['start_acceleration']
            dynamics._pins(model, x, v, a)
            assert not np.any(arrays['reaction_n'][i-1][model.free_mask])
            residual = model.masses_kg[:, None]*a-elastic['force_n']-force-arrays['reaction_n'][i-1]
            norm = dynamics._force_norm(model, residual)
            assert norm <= t['residual_limit_m_s2'] and not np.any(residual[model.pinned_mask])
            result['max_residual_to_limit_ratio'] = max(result['max_residual_to_limit_ratio'], norm/t['residual_limit_m_s2'])
            ex = float(np.max(np.abs(x-state.positions_m-dt*state.velocities_m_s-.25*dt**2*(start_a+a))))
            ev = float(np.max(np.abs(v-state.velocities_m_s-.5*dt*(start_a+a))))
            assert ex < 1e-12 and ev < 1e-12
            result['max_newmark_x_error_m'] = max(result['max_newmark_x_error_m'], ex)
            result['max_newmark_v_error_m_s'] = max(result['max_newmark_v_error_m_s'], ev)
            energy_error = max(abs(elastic[k]-t[k]) for k in ('membrane_energy_j', 'bending_energy_j'))
            assert energy_error < 1e-15
            result['max_energy_record_difference_j'] = max(result['max_energy_record_difference_j'], energy_error)
            inputs = {'previous_state_sha256': state.state_sha256, 'force': _array_identity(force, 'N'), 'policy': report['policy'], 'dt_s': dt}
            state = dynamics._state(model, x, v, a, force, float(arrays['time_s'][i]), i, t['residual_limit_m_s2'], inputs)
            assert state.state_sha256 == t['state_sha256']
            result['step_elapsed_s'] += t['elapsed_s']
        assert state.identity() == row['final_state']
        result['accepted_steps'] += len(trace); result['state_arrays'] += len(arrays)
    reports.append(report); arrays_by_run.append(saved); results.append(result)

assert reports[0] == reports[1]
for case, arrays in arrays_by_run[0].items():
    for key, array in arrays.items():
        assert np.array_equal(array, arrays_by_run[1][case][key])
model = audit._fixture(spec, 4, 'forward')
_, omega, _ = audit._mode(model)
free = model.free_mask; weights = model.masses_kg[free]/model.masses_kg[free].sum()
reference = arrays_by_run[0]['nonlinear_320']['velocities_m_s']
split = []
for steps in (40, 80, 160):
    difference = arrays_by_run[0][f'nonlinear_{steps}']['velocities_m_s'][:, free]-reference[::320//steps, free]
    values = {key: float(np.sqrt(np.sum(difference[:, :, axes]**2*weights[None, :, None], axis=(1, 2))).max()/(.001*omega))
              for key, axes in (('xy', [0, 1]), ('z', [2]), ('xyz', [0, 1, 2]))}
    split.append({'steps': steps, **values})
rest = model.structure.rest_positions_m; w = 1/np.sqrt(model.masses_kg[free, None]); columns = []
for y in np.eye(3*int(free.sum())):
    direction = np.zeros_like(rest); direction[free] = w*y.reshape(-1, 3)
    columns.append((w*dynamics._hvp(model, rest, direction)[free]).ravel())
matrix = np.column_stack(columns)
omega_max = math.sqrt(float(np.linalg.eigvalsh((matrix+matrix.T)/2)[-1]))
output = {'schema_version': 'wind3dgs.shell_dynamics_verification.v1', 'status': 'passed',
          'teacher_eligible': False, 'convergence_status': 'not_assessed', 'solver_check': 'passed', 'response_check': 'failed',
          'report_sha256': reports[0]['report_sha256'], 'runs': results,
          'replay': {'reports_equal': True, 'state_arrays_equal': True, 'state_and_trace_hashes_equal': True},
          'velocity_components': {'method': '동일 free mass RMS의 공통 시각 최대값 / (A omega1), A=0.001m; 320-step 기준', 'rows': split},
          'rest_frequency': {'model_sha256': model.model_sha256, 'omega1_rad_s': omega, 'omega_max_rad_s': omega_max,
                             'omega_max_over_omega1': omega_max/omega, 'dt320_omega_max': 2*math.pi/320*omega_max/omega},
          'interpretation': '속도 차이는 XY 성분이 지배한다. 빠른 면내 진동의 시간 해상도 부족 가능성을 후속 검증한다. 원인 확정이나 수렴 통과 판정은 아니다.'}
Path('/tmp/wind3dgs_shell_dynamics_verification.json').write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)+'\n')
print(json.dumps(output, ensure_ascii=False, indent=2))
