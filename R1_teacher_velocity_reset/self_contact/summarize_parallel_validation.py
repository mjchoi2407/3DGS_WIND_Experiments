"""v3/v4 저장 상태·병렬 실행 폭·공통 항 버퍼를 집계한다. 시뮬레이션은 실행하지 않는다."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path

import numpy as np
import warp as wp
from wind3dgs.teacher.gpu_contact_parallel import PairTerms


def read(path): return json.loads(path.read_text())
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old',type=Path,required=True)
    parser.add_argument('--new',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    if args.out.exists(): raise FileExistsError(args.out)
    device = wp.get_device('cuda:0')  # 장치 메타데이터만 조회하며 GPU kernel을 실행하지 않는다.
    rows = []
    for new in sorted(args.new.glob('*/checks/smoke/*/frame_0000.npz')):
        rel = new.relative_to(args.new); old = args.old/rel
        with np.load(new) as a,np.load(old) as b:
            errors = {}
            for key in ('u_hi','u_lo','v_hi','v_lo','held_force_n'):
                np.testing.assert_allclose(a[key],b[key],rtol=1e-7,atol=2e-9)
                errors[key] = float(np.max(np.abs(a[key]-b[key])))
            np.testing.assert_array_equal(a['flags'],b['flags']); assert not a['flags'].any()
        reports = [read(p.parent/'report.json') for p in (old,new)]
        assert all(r['status'] == 'complete' for r in reports)
        counts = [r['frames'][0]['counts'] for r in reports]
        rows.append(dict(case=str(rel),old_sha256=digest(old),new_sha256=digest(new),
            max_abs_difference=errors,old_counts=counts[0],new_counts=counts[1],counts_equal=counts[0] == counts[1]))
    assert len(rows) == 6
    memory = {}; itemsize = ctypes.sizeof(PairTerms.ctype)
    for path in sorted(args.new.glob('*/checks/smoke/report.json')):
        r = read(path); initial = r['initial_contact']; capacity = max(4096,32*initial['proxy_vertices'])
        workers = min(capacity,max(32,32*device.sm_count))
        memory[r['shape']] = dict(active_capacity=capacity,pair_workers=workers,
            old_derivative_logical_threads=12*capacity,new_derivative_logical_threads=12*workers,
            pair_terms_bytes_per_entry=itemsize,new_pair_terms_bytes_solver_and_audit=2*capacity*itemsize,
            hessian_bytes_solver_and_audit=capacity*12*12*8+8,
            scope='배열 산술값과 고정 launch 폭. 총 VRAM/실행시간/occupancy 측정이 아님')
    report = dict(status='passed',performance_eligible=False,
        reason='공유 GPU 환경의 기능 검증. 병렬 구조 개선을 가속 배수로 환산하지 않음',
        gpu=device.name,sm_count=device.sm_count,ccd_block_size=128,ccd_blocks_limit=2*device.sm_count,
        old_manifest_sha256=digest(args.old/'manifest.json'),new_manifest_sha256=digest(args.new/'manifest.json'),
        tolerance=dict(rtol=1e-7,atol=2e-9),state_comparison=rows,launch_and_memory=memory)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('v3/v4의6프레임 상태·카운터·추가 버퍼·고정 실행 폭 대조 완료. 속도 배수는 미확정입니다.')


if __name__ == '__main__': main()
