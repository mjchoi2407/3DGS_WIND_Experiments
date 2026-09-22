"""고정된 작은 후보 세 개로 dt와 iteration 영향을 분리하는 실험 wrapper."""
from dataclasses import replace
import json
from pathlib import Path
import time

from wind3dgs.teacher.trajectory_io import _atomic_json, _file_hash, _read_arrays, _write_arrays, _json_load
from wind3dgs.teacher.velocity_reset import VelocityResetSpec, make_wind_program, trace_simulation, validate_trace, compare_traces
from wind3dgs.evaluation.teacher_velocity_reset import verify_run


def main():
    root = Path(__file__).resolve().parents[4]
    source = root/'experiments/artifacts/runs/teacher_velocity_reset/20260909_strip_initial_v2'
    output = root/'experiments/artifacts/runs/teacher_velocity_reset/20260909_strip_temporal_pilot_v2'
    output.mkdir(parents=True, exist_ok=False)
    began = time.monotonic()
    manifest = {'status': 'running', 'quality': {'training_eligible': False}, 'outputs': {},
                'source_manifest_sha256': verify_run(source)['manifest_sha256'], 'failure': None,
                'purpose': '고정 폭 BC의 시간 간격·내부 반복 분리; 물리 채택 또는 dataset source 아님'}
    spec = VelocityResetSpec(attachment='left_quarter_strip', resolutions=(4, 8), substeps=(32, 64, 128))
    wind = make_wind_program(spec)[0]
    sm = _json_load((source/'manifest.json').read_bytes())
    baseline = _read_arrays(source, 'mesh8_sub32_natural.npz', sm['arrays']['mesh8_sub32_natural.npz'])
    traces = {'sub32_iter10': baseline}; rows = []
    def save():
        _atomic_json(output/'manifest.json', manifest)
    def log(message):
        print(message, flush=True)
        with (output/'run.log').open('a') as f: f.write(message+'\n')
    def budget():
        if time.monotonic()-began > 360: raise TimeoutError()
    save()
    try:
        for steps, iterations, reference in [(32, 20, 'sub32_iter10'), (64, 10, 'sub32_iter10'), (128, 10, 'sub64_iter10')]:
            current = replace(spec, iterations=iterations)
            name = f'sub{steps}_iter{iterations}'
            log(f'시간/반복 분리 시작: {name}')
            arrays, record = trace_simulation(current, 8, steps, wind, check_budget=budget)
            manifest['outputs'][name+'.npz'] = _write_arrays(output/(name+'.npz'), arrays)
            _atomic_json(output/(name+'.json'), {'spec': current.to_dict(), 'trace': record})
            save()
            validate_trace(arrays, record, current, wind)
            metric = compare_traces(traces[reference], arrays)
            rows.append({'case': name, 'reference': reference, 'metric': metric})
            traces[name] = arrays
            log(f"검산 완료: {name}, 위치 {100*metric['position']['relative_max']:.4f}%, 속도 {100*metric['velocity']['relative_max']:.4f}%")
        _atomic_json(output/'report.json', {'quality': {'training_eligible': False}, 'comparisons': rows})
        manifest['status'] = 'completed'
    except (Exception, KeyboardInterrupt) as error:
        manifest['status'] = 'failed'; manifest['failure'] = type(error).__name__
        raise
    finally:
        manifest['elapsed_s'] = time.monotonic()-began
        manifest['inventory'] = {p.name: {'bytes': p.stat().st_size, 'sha256': _file_hash(p)}
                                 for p in output.iterdir() if p.is_file() and p.name != 'manifest.json'}
        save()


if __name__ == '__main__': main()
