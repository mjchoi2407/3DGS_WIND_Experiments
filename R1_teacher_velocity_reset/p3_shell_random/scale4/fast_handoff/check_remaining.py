"""보존형 이어하기와 수동 재개의 작은 end-to-end 검사. 긴 계산을 실행하지 않는다."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np

import run_remaining as runner
from wind3dgs.evaluation.teacher_p3_shell_continuation import Bundle,adopt,simulate


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reference',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--device',default='cpu',choices=('cpu','cuda:0'));a=p.parse_args();a.output=a.output.resolve();a.output.mkdir(parents=True)
    original=a.reference.resolve();fixture=a.output/'legacy';shutil.copytree(original,fixture)
    config=runner.read(fixture/'config.json')
    assert (config['resolution'],config['substeps'],config['start_frame'],config['end_frame'])==(4,8,0,4)
    r=runner.read(fixture/'report.json');r.update(status='running',completed_frames=2,last_completed_frame=1);runner.write(fixture/'report.json',r)
    ids={Path(n).stem:runner.ref(fixture/n) for n in ('config.json','report.json','source_snapshot.zip','wind.npz','manifest.json')}
    runs={'m4_natural':{'config':config,'parent':None,'legacy':{'path':str(fixture.relative_to(Path.cwd())),'identities':ids}},
          'm4_reset2':{'config':dict(config,start_frame=2,reset_velocity=True,parent_name=fixture.name),'parent':'m4_natural'}}
    bundle_path=a.output/'bundle';bundle_path.mkdir()
    runner.write(bundle_path/'plan.json',{'schema':'wind3dgs.p3_shell_segmented_continuation.v1','runs':runs,
        'tasks':runner.make_tasks(runs,conditions=[('m4',4,8,'forward')],pairs=[('same','m4','m4',True)],checkpoints=(2,)),
        'replay_frame':1,'smoke':True})
    runner.freeze(bundle_path);runner.write(bundle_path/'status.json',{'status':'준비 완료','completed':0,'total':10})
    bundle=Bundle(bundle_path);before={str(f.relative_to(fixture)):runner.identity(f) for f in fixture.rglob('*') if f.is_file()}
    adopt(bundle,'m4_natural')
    assert not simulate(bundle,'m4_natural',a.device,limit=1)
    assert len(bundle.index('m4_natural')['frames'])==3
    # 실제 사용자 supervisor가 완료되지 않은 frame부터 이어 계산한다.
    result=subprocess.run([sys.executable,'-u',str(bundle_path/'runtime/run_remaining.py'),'--output',str(bundle_path),
                           '--device',a.device,'--gpu-jobs','1','--cpu-jobs','2'])
    assert result.returncode==0
    assert runner.read(bundle_path/'status.json')['status']=='완료'
    for f,digest in before.items():assert runner.identity(fixture/f)==digest
    for frame in range(4):
        actual,_=bundle.frame('m4_natural',frame)
        with np.load(original/'frames'/f'{frame:03d}.npz') as expected:
            np.testing.assert_allclose(actual['u_m'],expected['u_m'],rtol=2e-8,atol=2e-12)
            np.testing.assert_allclose(actual['v_m_s'],expected['v_m_s'],rtol=2e-8,atol=2e-10)
    for frame in (2,3):
        previous,_=bundle.frame('m4_natural',frame-1);current,_=bundle.frame('m4_natural',frame)
        for key in ('u_m','v_m_s','time_s'):np.testing.assert_array_equal(previous[key][-1],current[key][0])
    branch,_=bundle.frame('m4_reset2',2);np.testing.assert_array_equal(branch['v_m_s'][0],0.)
    assert bundle.audit('m4_reset2')['removed_kinetic_j']>0
    item=bundle.index('m4_natural')['frames'][0];array=bundle.resolve(item['array']['path']);raw=array.read_bytes()
    try:
        array.write_bytes(raw+b'tampered')
        try:bundle.frame('m4_natural',0)
        except ValueError:pass
        else:raise AssertionError('원본 변조 허용')
    finally:array.write_bytes(raw)
    runner.write(a.output/'checks.json',{'passed':True,'device':a.device,'legacy_prefix_frames':2,'interrupted_after_new_frames':1,
        'resume_exact_boundary':True,'reference_trajectory_within_existing_tolerance':True,'legacy_files_unchanged':True,
        'reset_and_replay_verified':True,'all_tasks_completed':True,'tampered_array_rejected':True,
        'scope':'n4/sub8/4 frame natural 및2 frame reset. 실제 n32 전체 검증 아님.'})
    print('이어하기·재개·검산·비교 전체 흐름 검사 통과',flush=True)


if __name__=='__main__':main()
