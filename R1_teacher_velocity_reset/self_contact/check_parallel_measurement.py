"""측정 도구의 세 접촉 ON 경로를 작은2단계 입력으로 기능 검사한다. 속도 채택 시험이 아니다."""
import argparse
from pathlib import Path
import numpy as np
import warp as wp

from wind3dgs.evaluation.p3_contact_validation import patch_pair
from wind3dgs.evaluation.p3_gpu_contact_performance import components, frames
from wind3dgs.evaluation.teacher_gravity_wrinkles import write, digest
from wind3dgs.teacher.p3_shell_contact import ShellContactPolicy
from wind3dgs.teacher.p3_shell_dynamics import ShellSolvePolicy
import wind3dgs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    if args.out.exists(): raise FileExistsError(args.out)
    wp.config.kernel_cache_dir = '/tmp/wind3dgs-gpu-contact-cache'; wp.init()
    m,u,moving = patch_pair(); v = np.zeros_like(u); v[moving,1] = -.2
    cp = ShellContactPolicy(minimum_distance_m=.001,activation_distance_m=.01,barrier_stiffness=1000.)
    package = Path(wind3dgs.__file__).parent
    report = dict(status='running',performance_eligible=False,
        reason='공유 GPU에서 측정 도구의 실행·상태 대조만 검사. 최종 가속/접촉 증가율 근거로 사용하지 않음',
        source_sha256={str(p.relative_to(package)):digest(p) for p in sorted(package.rglob('*.py'))})
    write(args.out,report)
    try:
        report['components'] = components(m,u,cp)
        report['frames'] = frames(m,np.stack([u,np.zeros_like(u),v,np.zeros_like(u)]),
            [[0.,0.,0.]],[[0.,0.,0.]],ShellSolvePolicy(max_newton=40,line_search_steps=24,
            linear_cycles=12,linear_restart=60),cp,.001,2,1,allow_off=False)
        report['status'] = 'passed'
    except Exception as error:
        report.update(status='failed',reason=str(error)); raise
    finally: write(args.out,report)
    print('병렬 측정 도구의 요소별3경로·프레임3경로 기능 검증 완료. 속도 채택 근거는 아닙니다.')


if __name__ == '__main__': main()
