"""성능 후보v3의 저장 상태 동치·메모리 산술값·공유 GPU 측정 한계를 집계한다. GPU 실행 없음."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import numpy as np


def read(path): return json.loads(path.read_text())
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old',type=Path,required=True)
    parser.add_argument('--new',type=Path,required=True)
    parser.add_argument('--shared',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    if args.out.exists(): raise ValueError('기존 집계는 덮어쓰지 않습니다')
    rows = []
    for new in sorted(args.new.glob('*/checks/smoke/*/frame_0000.npz')):
        rel = new.relative_to(args.new); old = args.old/rel
        with np.load(new) as a,np.load(old) as b:
            errors = {}
            for key in ('u_hi','u_lo','v_hi','v_lo','held_force_n'):
                np.testing.assert_allclose(a[key],b[key],rtol=1e-7,atol=2e-9)
                errors[key] = float(np.max(np.abs(a[key]-b[key])))
            np.testing.assert_array_equal(a['flags'],b['flags'])
            assert not a['flags'].any()
        old_report,new_report = [read(p.parent/'report.json') for p in (old,new)]
        assert old_report['status'] == new_report['status'] == 'complete'
        old_counts,new_counts = [r['frames'][0]['counts'] for r in (old_report,new_report)]
        # 반복 횟수는 진단값이다. 같은 허용오차의 풀이도 마지막 선형 반복1회의 차이가 날 수 있다.
        # 동치 기준은 위 raw 상태 오차와 원래 GPU 검산 통과이며, 카운터 차이는 숨기지 않는다.
        rows.append(dict(case=str(rel),old_sha256=digest(old),new_sha256=digest(new),
            max_abs_difference=errors,old_counts=old_counts,new_counts=new_counts,
            counts_equal=old_counts == new_counts,flags_equal=True))
    assert len(rows) == 6
    memory = {}
    for path in sorted(args.new.glob('*/checks/smoke/report.json')):
        report = read(path); n = report['initial_contact']['proxy_vertices']; capacity = max(4096,32*n)
        memory[report['shape']] = dict(active_capacity=capacity,
            old_hessian_bytes=2*capacity*12*12*8,new_hessian_bytes=capacity*12*12*8+8,
            scope='접촉 국소 Hessian 배열만의 산술값. 총 VRAM/peak 아님')
    shared = read(args.shared/'report.json'); shared_status = read(args.shared/'measurement_status.json')
    report = dict(status='passed',performance_eligible=False,
        reason='최종v3 기능·상태 동치 검증. 공유 GPU의 부분 성능 측정은 최종 가속 배수로 채택하지 않음',
        new_manifest_sha256=digest(args.new/'manifest.json'),old_manifest_sha256=digest(args.old/'manifest.json'),
        acceptance_tolerance=dict(rtol=1e-7,atol=2e-9),state_comparison=rows,hessian_memory=memory,
        shared_measurement_status=shared_status,shared_report_sha256=digest(args.shared/'report.json'),
        shared_prototype_source_sha256=shared['source_sha256'])
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    target = args.out.parent/'shared_gpu_prototype_report.json'
    if target.exists(): raise FileExistsError(target)
    shutil.copy2(args.shared/'report.json',target)
    print('6프레임 상태 동치·카운터 차이와 메모리 집계 완료. GPU 성능 배수는 미확정입니다.')


if __name__ == '__main__': main()
