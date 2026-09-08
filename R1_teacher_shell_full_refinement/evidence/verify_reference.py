"""고정된 두 full run의 실험 검산. 실행 중이면 성공 checkpoint의 chunk부터 읽는다."""
import csv
import json
from pathlib import Path
import time

import numpy as np

from wind3dgs.evaluation import teacher_shell_full_refinement_audit as full

audit, temporal, dynamics, acceleration, refinement = full.p, full.t, full.d, full.acceleration, full.short
content_hash = full.content_hash
workspace = Path.cwd()
started = time.perf_counter()
budget = temporal._Budget(14400)
base = workspace/'experiments/artifacts/runs/teacher_shell_full_refinement'
folders = [base/name for name in ('20260908_reference_v1', '20260908_reference_v1_replay')]
source = audit._validate_sources(workspace/'experiments/artifacts/runs/teacher_shell_dynamics/20260907_reference_v1',
    workspace/'experiments/artifacts/runs/teacher_shell_temporal/20260908_reference_v1', budget)
precision_folder = workspace/'experiments/artifacts/runs/teacher_shell_precision/20260908_reference_v1'
short_folder = workspace/'experiments/artifacts/runs/teacher_shell_refinement/20260908_reference_v1'
precision_report, precision_identity = refinement._validate_precision_header(precision_folder, source, budget)
short_report, short_identity = full._validate_short_header(short_folder, source, precision_identity, budget)
prefixes = full._validate_short_states(short_folder, short_report, precision_folder, precision_report, source, budget)
source_identity = {**source['identity'], **precision_identity, **short_identity}
model, initial = source['model'], source['initial']
zero = np.zeros_like(initial.positions_m)
mass, free = model.masses_kg[:, None], model.free_mask
w = 1/np.sqrt(mass[free])
length, ab = dynamics._scales(model)
zero_identity = temporal.plate._array_identity(zero, 'N')
print('Full 검산: 네 선행 원본과 short 회귀 재검산 통과', flush=True)
stats = [{'run': str(folder.relative_to(workspace/'experiments')), 'checked_frames': 0, 'accepted_candidate_steps': 0,
    'iteration_vectors': 0, 'checked_trial_vectors': 0, 'checked_chunks': 0, 'checked_linear_corrections': 0,
    'max_recomputed_linear_ratio': 0., 'max_residual_to_limit_ratio': 0., 'max_kinematic_ratio': 0., 'case_elapsed_s': 0.,
    'status': 'running'} for folder in folders]
saved_rows, saved_comparisons = [[], []], [[], []]


class LiveChunks:
    def __init__(self, folder, name, row):
        self.folder, self.name, self.row, self.index = folder, name, row, 0

    def __len__(self):
        return self.index+1

    def __iter__(self):
        while True:
            budget.check()
            manifest = temporal._json(self.folder/'manifest.json')
            committed = manifest['committed_chunks'][self.name]
            if self.index < len(committed):
                record = temporal._json(self.folder/'chunks'/self.name/f'{self.index:06d}'/'chunk.json')['record']
                assert committed[self.index] == {'index': record['index'], 'last_step': record['last_step'], 'chunk_sha256': record['chunk_sha256']}
                yield record
                self.index += 1
            elif any(row['case_id'] == self.name for row in manifest['cases']):
                summary = temporal._json(self.folder/'cases'/self.name/'summary.json')
                assert len(summary['chunks']) == self.index
                self.row.update(summary)
                return
            else:
                assert manifest['status'] == 'running', 'Case 요약 없는 실행 중단은 별도 recovery 검토가 필요합니다'
                time.sleep(5)


def wait_for_case(folder, name, n):
    while True:
        budget.check()
        manifest = temporal._json(folder/'manifest.json')
        # summary 파일 작성 도중 읽지 않도록 case 완료 checkpoint를 기다린다.
        if any(row['case_id'] == name for row in manifest['cases']):
            return temporal._json(folder/'cases'/name/'summary.json')
        if manifest.get('active_case') == name:
            dt = source['period']/n
            row = {'case_id': name, 'storage_id': full.STORAGE, 'initial_state': initial.identity(),
                'model_sha256': model.model_sha256, 'policy': acceleration.ShellAccelerationNewmarkPolicy().to_dict(),
                'integration_steps_per_T1': n, 'requested_steps': n, 'dt_s': dt, 'duration_s': n*dt,
                'comparison_steps_per_T1': 10240, 'native_sample_stride': n//10240, 'status': 'running',
                'initial_arrays': temporal._identities(temporal._arrays([temporal._frame(model, 0., initial.positions_m,
                    initial.velocities_m_s, acceleration=initial.accelerations_m_s2)]))}
            row['chunks'] = LiveChunks(folder, name, row)
            return row
        if manifest['status'] != 'running': return None
        time.sleep(5)


def verify_iterations(entries, vectors, state, a0, dt, policy, counts, *, endpoint=None):
    c = .25*dt*dt
    def vector(entry, key): return vectors[entry['vectors'][key]['npz_key']]
    next_acceleration = a0
    predictor = state.positions_m+dt*state.velocities_m_s+c*a0
    for iteration, entry in enumerate(entries):
        bi, xi = vector(entry, 'acceleration_m_s2'), vector(entry, 'position_m')
        assert entry['iteration'] == iteration
        np.testing.assert_array_equal(bi, next_acceleration)
        np.testing.assert_array_equal(xi, state.positions_m+(dt*state.velocities_m_s+c*(a0+bi)))
        ri = mass*bi-dynamics._elastic(model, xi)['force_n']
        assert dynamics._force_norm(model, ri) == entry['residual_m_s2']
        db, dx = vector(entry, 'acceleration_correction_m_s2'), vector(entry, 'position_correction_m')
        np.testing.assert_array_equal(dx, c*db)
        assert dynamics._displacement_norm(model, dx)/length == entry['correction_over_length']
        correction_limit = policy['correction_atol_length']+policy['correction_rtol']*max(
            dynamics._displacement_norm(model, xi-model.structure.rest_positions_m),
            dynamics._displacement_norm(model, predictor-model.structure.rest_positions_m))/length
        assert entry['correction_limit'] == correction_limit
        if 'linear' in entry:
            assert entry['linear']['passed'] and entry['linear']['true_residual_norm'] <= entry['linear']['residual_bound']
            hvp = dynamics._hvp(model, xi, db)
            rhs_norm = float(np.linalg.norm(w*ri[free]))
            assert entry['linear']['residual_bound'] == policy['linear_rtol']*rhs_norm
            tangent = mass*db+c*hvp
            scaled_residual = float(np.linalg.norm(w*(tangent+ri)[free]))
            terms = rhs_norm+float(np.linalg.norm(w*(mass*db)[free]))+float(np.linalg.norm(c*w*hvp[free]))
            # Solver의 저장 bound는 그대로 검사한다. 재구성된 scaled 연산에는 선행 검산과 같은 roundoff 항을 더한다.
            bound_linear = policy['linear_rtol']*rhs_norm+256*np.finfo(float).eps*terms
            assert scaled_residual <= bound_linear, (state.step_index+1, scaled_residual, bound_linear)
            counts['checked_linear_corrections'] += 1
            counts['max_recomputed_linear_ratio'] = max(counts['max_recomputed_linear_ratio'], scaled_residual/bound_linear)
        if 'line_search' in entry:
            assert entry['merit'] == .5*float(np.sum((w*ri[free])**2))
            assert entry['slope'] == float(np.sum((w*ri[free])*(w*tangent[free])))
            assert entry['linear_residual_force_norm_n'] == float(np.linalg.norm((tangent+ri)[free]))
        for backtrack, trial in enumerate(entry.get('line_search', [])):
            assert trial['alpha'] == .5**backtrack
            bt, xt = vector(trial, 'acceleration_m_s2'), vector(trial, 'position_m')
            np.testing.assert_array_equal(bt, bi+trial['alpha']*db)
            np.testing.assert_array_equal(xt, state.positions_m+(dt*state.velocities_m_s+c*(a0+bt)))
            np.testing.assert_array_equal(vector(trial, 'realized_position_change_m'), xt-xi)
            rt = mass*bt-dynamics._elastic(model, xt)['force_n']
            merit = .5*float(np.sum((w*rt[free])**2))
            assert merit == trial['merit']
            assert trial['accepted'] == (merit <= entry['merit']+policy['armijo_c1']*trial['alpha']*entry['slope'])
            if trial['accepted']:
                assert backtrack == len(entry['line_search'])-1
                next_acceleration = bt
            counts['checked_trial_vectors'] += 1
    if endpoint is not None:
        final = entries[-1]
        assert final['correction_over_length'] <= final['correction_limit']
        np.testing.assert_array_equal(vector(final, 'acceleration_m_s2'), endpoint['accelerations_m_s2'])
        np.testing.assert_array_equal(vector(final, 'position_m'), endpoint['positions_m'])


def verify_frame(frame, trace, vectors, state, row, counts):
    x, v, b = (frame[key] for key in ('positions_m', 'velocities_m_s', 'accelerations_m_s2'))
    dynamics._pins(model, x, v, b)
    elastic = dynamics._elastic(model, x)
    recalculated = temporal._frame(model, frame['time_s'], x, v, acceleration=b, elastic=elastic)
    for key in temporal.UNITS: np.testing.assert_array_equal(recalculated[key], frame[key])
    start_elastic = dynamics._elastic(model, state.positions_m)
    a0 = dynamics._acceleration(model, start_elastic, zero)
    policy, dt = row['policy'], row['dt_s']
    bound = policy['residual_atol_bending']*ab+policy['residual_rtol']*dynamics._force_norm(model, start_elastic['force_n'])
    norm = dynamics._force_norm(model, mass*b-elastic['force_n'])
    assert bound == trace['residual_limit_m_s2'] and norm == trace['end_residual_m_s2'] and norm <= bound
    assert trace['start_residual_m_s2'] == dynamics._force_norm(model, mass*a0-start_elastic['force_n'])
    counts['max_residual_to_limit_ratio'] = max(counts['max_residual_to_limit_ratio'], norm/bound)
    kin = acceleration._kinematic_summary(acceleration._kinematic_arrays(state.positions_m, state.velocities_m_s, a0, x, v, b, dt))
    assert kin == trace['kinematics'] and kin['passed']
    counts['max_kinematic_ratio'] = max(counts['max_kinematic_ratio'], kin['position_defect_m_max_ratio'], kin['velocity_defect_m_s_max_ratio'])
    assert trace['status'] == 'accepted' and trace['step_index'] == state.step_index+1
    assert trace['time_s'] == frame['time_s'] == state.time_s+dt
    assert trace['integrator_id'] == policy['integrator_id'] and trace['initial_guess_id'] == policy['initial_guess_id']
    assert trace['previous_endpoint_acceleration'] == temporal.plate._array_identity(state.accelerations_m_s2, 'm/s^2')
    assert trace['start_acceleration'] == temporal.plate._array_identity(a0, 'm/s^2')
    assert trace['previous_force'] == trace['interval_force'] == zero_identity
    for key in ('kinetic_energy_j', 'membrane_energy_j', 'bending_energy_j'): assert trace[key] == frame[key]
    k0 = .5*float(np.sum(mass*state.velocities_m_s*state.velocities_m_s))
    defect = frame['kinetic_energy_j']+elastic['energy_j']-k0-start_elastic['energy_j']
    assert trace['external_work_j'] == 0. and trace['energy_defect_j'] == defect
    verify_iterations(trace['iterations'], vectors, state, a0, dt, policy, counts, endpoint=frame)
    assert trace['iterations'][-1]['residual_m_s2'] == norm
    assert all(entry['residual_limit_m_s2'] == bound for entry in trace['iterations'])
    inputs = {'previous_state_sha256': state.state_sha256, 'force': zero_identity, 'policy': policy, 'dt_s': dt}
    new = dynamics._state(model, x, v, b, zero, float(frame['time_s']), state.step_index+1, bound, inputs)
    assert new.state_sha256 == trace['state_sha256']
    return new


for case_id, n in full.CASES:
    rows = [wait_for_case(folder, case_id, n) for folder in folders]
    if rows == [None, None]: break
    assert all(row is not None for row in rows)
    states = [initial, initial]
    samples, max_energy, max_residual, max_kinematic = [], [0., 0.], [0., 0.], [0., 0.]
    initial_frame = temporal._frame(model, 0., initial.positions_m, initial.velocities_m_s, acceleration=initial.accelerations_m_s2)
    energy0 = full._energy(initial_frame)
    for j, (folder, row) in enumerate(zip(folders, rows)):
        assert row['initial_state'] == initial.identity() and row['model_sha256'] == model.model_sha256
        assert row['policy'] == acceleration.ShellAccelerationNewmarkPolicy().to_dict()
        assert row['integration_steps_per_T1'] == row['requested_steps'] == n and row['dt_s'] == source['period']/n
        assert row['comparison_steps_per_T1'] == 10240 and row['native_sample_stride'] == n//10240
        case = folder/'cases'/case_id
        assert temporal._json(case/'initial_state.json') == initial.identity()
        native_initial = audit._load_arrays(case/'initial.npz', row['initial_arrays'])
        for key in temporal.UNITS: np.testing.assert_array_equal(native_initial[key], np.asarray(initial_frame[key])[None])
        samples.append([initial_frame])
        stats[j]['checked_frames'] += 1
    readers = [full._read_chunks(folder, row, budget) for folder, row in zip(folders, rows)]
    for index, (chunk_a, chunk_b) in enumerate(zip(*readers, strict=True)):
        record, arrays, traces, vectors = chunk_a
        other_record, other_arrays, other_traces, other_vectors = chunk_b
        assert record == other_record and temporal._clean(traces) == temporal._clean(other_traces)
        for key in arrays: np.testing.assert_array_equal(arrays[key], other_arrays[key])
        assert set(vectors) == set(other_vectors)
        for key in vectors: np.testing.assert_array_equal(vectors[key], other_vectors[key])
        for j, (record, arrays, traces, vectors) in enumerate((chunk_a, chunk_b)):
            row = rows[j]; state = states[j]
            assert record['start_state_sha256'] == state.state_sha256
            for i, trace in enumerate(traces):
                budget.check()
                frame = {key: value[i] for key, value in arrays.items()}
                state = verify_frame(frame, trace, vectors, state, row, stats[j])
                max_energy[j] = max(max_energy[j], abs(full._energy(frame)/energy0-1))
                max_residual[j] = max(max_residual[j], trace['end_residual_m_s2']/trace['residual_limit_m_s2'])
                kin = trace['kinematics']
                max_kinematic[j] = max(max_kinematic[j], kin['position_defect_m_max_ratio'], kin['velocity_defect_m_s_max_ratio'])
                if n in prefixes and state.step_index <= len(prefixes[n]['traces']):
                    full._check_prefix(prefixes[n], frame, trace, state)
                if state.step_index % (n//10240) == 0:
                    samples[j].append({key: np.array(value, copy=True) for key, value in frame.items()})
            assert record['end_state_sha256'] == state.state_sha256
            states[j] = state
            stats[j]['checked_frames'] += len(traces); stats[j]['accepted_candidate_steps'] += len(traces)
            stats[j]['iteration_vectors'] += len(vectors); stats[j]['checked_chunks'] += 1
        if (index+1) % 8 == 0:
            print(f"Full 상태·반복 재검산: 두 run / {case_id} / {record['last_step']}/{n} step", flush=True)
            Path('/tmp/wind3dgs_shell_full_refinement_verification_progress.json').write_text(json.dumps(stats, ensure_ascii=False, indent=2)+'\n')
    assert rows[0] == rows[1]
    for j, (folder, row, state, frames) in enumerate(zip(folders, rows, states, samples)):
        case = folder/'cases'/case_id
        sample = audit._load_arrays(case/'comparison.npz', row['comparison_arrays'])
        recovered = temporal._arrays(frames)
        for key in sample: np.testing.assert_array_equal(sample[key], recovered[key])
        stats[j]['case_elapsed_s'] += temporal._json(case/'runtime.json')['elapsed_s']
        assert state.identity() == row['final_state'] and state.step_index == row['persisted_steps'] == row['completed_steps']
        assert max_energy[j] == row['max_relative_energy_drift']
        assert max_residual[j] == row['max_residual_to_limit_ratio'] and max_kinematic[j] == row['max_kinematic_ratio']
        assert row['max_buffer_frames'] <= 256
        failure_vectors = full._load_vectors(folder/'cases'/case_id/'failure_vectors.npz') if row['failure_vectors']['count'] else {}
        full._check_vector_references([], row['failure'], failure_vectors, row['failure_vectors'])
        if row['failure']:
            assert row['failure']['last_state_sha256'] == state.state_sha256
            if row['failure'].get('iterations'):
                a0 = dynamics._acceleration(model, dynamics._elastic(model, state.positions_m), zero)
                verify_iterations(row['failure']['iterations'], failure_vectors, state, a0, row['dt_s'], row['policy'], stats[j])
        if row['status'] == 'completed':
            comparison = full._comparison(source, sample, row)
            # Primary를 공통 원본 배열에서 독립 산술로 확인한다.
            weights = model.masses_kg[free]/model.masses_kg[free].sum()
            for key, scale in (('positions_m', .001), ('velocities_m_s', .001*source['omega'])):
                delta = sample[key][:, free]-source['arrays']['reference_b'][key][:, free]
                values = np.sqrt(np.sum(delta*delta*weights[None, :, None], axis=(1, 2)))/scale
                np.testing.assert_allclose(float(values.max()), comparison['metrics'][key]['total']['normalized'], rtol=3e-14, atol=1e-15)
            saved_comparisons[j].append({'case_id': case_id, **comparison})
        saved_rows[j].append(row)
    print('Full 사례 검산 통과: 두 run / '+case_id, flush=True)

reports = []
for j, folder in enumerate(folders):
    while temporal._json(folder/'manifest.json')['status'] == 'running':
        budget.check(); time.sleep(5)
    report, manifest, environment, config = (temporal._json(folder/key) for key in ('report.json', 'manifest.json', 'environment.json', 'config.json'))
    assert report['schema_version'] == manifest['schema_version'] == full.SCHEMA
    assert report['storage_id'] == manifest['storage_id'] == full.STORAGE
    assert report['report_sha256'] == content_hash({k: v for k, v in report.items() if k != 'report_sha256'}) == manifest['report_sha256']
    assert report['source'] == manifest['source'] == source_identity
    assert report['cases'] == saved_rows[j] and report['comparisons']['full'] == saved_comparisons[j]
    assert report['policy'] == config['policy'] == full.TeacherShellFullRefinementPolicy().to_dict()
    assert report['solver_policy'] == config['solver_policy'] == acceleration.ShellAccelerationNewmarkPolicy().to_dict()
    assert manifest['config_sha256'] == content_hash(config)
    assert environment['sources_sha256'] == manifest['software'] == full._environment()['sources_sha256']
    assert report['reference_comparison'] == source['reference_comparison']
    assert report['short_response_details'] == short_report['short_response_details']
    assert report['reference_origin'] == 'reused_verified_temporal_v1'
    assert report['model'] == model.identity() and manifest['models'] == [model.identity()]
    assert report['modal'] == source['modal']['summary']
    assert not report['teacher_eligible'] and report['convergence_status'] == 'not_assessed'
    assert not manifest['pending_cases'] and not manifest['partial_files']
    for key in full.CHECKS: assert report[key] == manifest[key]
    assert all(report[key] == 'passed' for key in ('source_check', 'reference_check', 'short_regression_check'))
    expected_prefix = 'passed' if sum(row['prefix_check'] == 'passed' for row in saved_rows[j]) == 2 else 'not_assessed'
    assert report['prefix_check'] == expected_prefix
    floor = {key: source['reference_comparison']['metrics'][key]['total']['normalized'] for key in ('positions_m', 'velocities_m_s')}
    details = temporal._response_status(saved_comparisons[j], full.TeacherShellFullRefinementPolicy(), floor)
    assert details == report['full_response_details'] and details['status'] == report['full_response_check']
    actual_files = {str(path.relative_to(folder)) for path in folder.rglob('*') if path.is_file() and path.name != 'manifest.json'}
    assert actual_files == set(manifest['outputs'])
    for filename, entry in manifest['outputs'].items():
        budget.check(); assert temporal._file_entry(temporal._source_path(folder, filename)) == entry
    for row in saved_rows[j]:
        expected = [{'index': c['index'], 'last_step': c['last_step'], 'chunk_sha256': c['chunk_sha256']} for c in row['chunks']]
        assert manifest['committed_chunks'][row['case_id']] == expected
    last = saved_rows[j][-1]
    assert manifest['last_checkpoint'] == {'case_id': last['case_id'], 'last_step': last['persisted_steps'],
        'state_sha256': last['final_state']['state_sha256'], 'chunk_sha256': last['last_chunk_sha256']}
    with np.load(folder/'modal_basis.npz', allow_pickle=False) as modal:
        for key in ('basis', 'sqrt_mass', 'omega'): np.testing.assert_array_equal(modal[key], source['modal'][key])
    with (folder/'comparisons.csv').open() as stream: actual_csv = list(csv.DictReader(stream))
    assert actual_csv == [{key: str(value) for key, value in row.items()} for row in full._csv_rows(report)]
    stats[j].update(status='passed', source_files=len(environment['sources_sha256']), inventoried_files=len(actual_files),
        inventoried_bytes=sum(entry['bytes'] for entry in manifest['outputs'].values()), audit_elapsed_s=temporal._json(folder/'runtime.json')['elapsed_s'])
    reports.append(report)
assert reports[0] == reports[1]
assert temporal._json(folders[0]/'manifest.json')['reproducibility_key'] == temporal._json(folders[1]/'manifest.json')['reproducibility_key']
result = {'schema_version': 'wind3dgs.shell_full_refinement_verification.v1', 'status': 'passed', 'teacher_eligible': False,
    'convergence_status': 'not_assessed', 'runs': stats, 'report_sha256': reports[0]['report_sha256'],
    'full_response_check': reports[0]['full_response_check'], 'replay_reports_arrays_trace_hashes_equal': True,
    'state_and_iteration_physics_recomputed_for_each_run': True, 'linear_correction_residuals_recomputed': True,
    'comparisons_csv_recomputed': True, 'elapsed_s_including_wait_for_live_cases': time.perf_counter()-started,
    'meaning': '두 run 각각의 모든 보존 상태·반복 벡터 검산과 독립 재실행 일치이며 물리 수렴 판정과 구분한다.'}
Path('/tmp/wind3dgs_shell_full_refinement_verification.json').write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)+'\n')
print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
