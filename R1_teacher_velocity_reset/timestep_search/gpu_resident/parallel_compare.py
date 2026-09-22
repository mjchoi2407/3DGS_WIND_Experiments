"""완료된 하이브리드·GPU 기준을 재사용하고 새 방법만 계산·검산한다."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def read(path):return json.loads(path.read_text())
def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=Path('experiments/artifacts/runs/teacher_timestep_search/20260913_gpu_parallel_cached_v1'))
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--method',choices=['parallel','preconditioner','current-first','reuse-uncompressed'],default='parallel')
    parser.add_argument('--baseline',type=Path,default=Path('experiments/artifacts/runs/teacher_timestep_search/20260913_gpu_resident_10frames_v1'))
    parser.add_argument('--gpu-baseline',type=Path,default=Path('experiments/artifacts/runs/teacher_timestep_search/20260913_gpu_parallel_v1/reference'))
    parser.add_argument('--parallel-baseline',type=Path,default=Path('experiments/artifacts/runs/teacher_timestep_search/20260913_gpu_parallel_v1/parallel'))
    parser.add_argument('--preconditioner-baseline',type=Path,default=Path('experiments/artifacts/runs/teacher_timestep_search/20260913_gpu_preconditioner_v1/candidate'))
    parser.add_argument('--current-first-baseline',type=Path,default=Path('experiments/artifacts/runs/teacher_timestep_search/20260913_gpu_current_first_v1/candidate'))
    a=parser.parse_args()
    sources={'hybrid':(a.baseline,'hybrid'),'gpu':(a.gpu_baseline,'gpu'),'parallel':(a.parallel_baseline,'gpu')}
    if a.method in ('current-first','reuse-uncompressed'):sources['preconditioner']=(a.preconditioner_baseline,'gpu')
    if a.method=='reuse-uncompressed':sources['current_first']=(a.current_first_baseline,'gpu')
    fixture=read(a.baseline/'fixture/manifest.json');cache={}
    for name,(folder,backend) in sources.items():
        result=read(folder/'comparison.json')
        if result['status']!='passed' or not result['audits'][backend]['passed']:raise ValueError('실패한 기준: '+name)
        f=read(folder/'fixture/manifest.json')
        for key in ['config','source_plan','initial_sha256','wind_sha256']:
            if f[key]!=fixture[key]:raise ValueError('기준 입력/정책 불일치: '+name+'/'+key)
        for path,h in read(folder/'manifest.json')['files'].items():
            if digest(folder/path)!=h:raise ValueError('기준 소스 불일치: '+name+'/'+path)
        report=result['backends'][backend]
        if report!=read(folder/backend/'report.json'):raise ValueError('기준 report 불일치: '+name)
        for path,h in report['files'].items():
            if digest(folder/backend/path)!=h:raise ValueError('기준 결과 불일치: '+name+'/'+path)
        cache[name]={'source':str(folder),'result_sha256':digest(folder/'comparison.json'),'manifest_sha256':digest(folder/'manifest.json'),'report':report}
    a.out.mkdir(parents=True,exist_ok=False)
    def write(name,data):(a.out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    write('cached_references.json',cache)
    write('status.json',{'phase':'새 방법 준비' if a.prepare_only else '새 방법 계산·검산','completed':False})
    cmd=[sys.executable,'-u',str(Path(__file__).with_name('profile_run.py')),'--'+a.method,'--reuse-audit','--baseline',str(a.baseline),'--out',str(a.out/'candidate')]
    if a.prepare_only:cmd.append('--prepare-only')
    try:
        subprocess.run(cmd,check=True)
        if a.prepare_only:
            write('status.json',{'phase':'준비 검증 완료; 실제 실행은 새 경로','completed':False})
            return
        checked=read(a.out/'candidate/comparison.json');new=checked['backends']['gpu']
        passed=checked['status']=='passed' and checked['trajectory_equivalent']
        speedups={name:{'generation':v['report']['generation_s']/new['generation_s'],'compute_and_buffer':v['report']['compute_and_buffer_s']/new['compute_and_buffer_s']} for name,v in cache.items()} if passed else None
        write('summary.json',{'passed':passed,'method':a.method,'candidate':new,'cached_references':cache,'speedups_vs_cached':speedups,
              'comparison':'기준 실행·검산은 캐시 재사용. 새 GPU만 계산·검산. 서로 다른 시점의 시간 비교로 동일 부하를 보장하지 않음.',
              'training_eligible':False,'r1_complete':False})
        write('status.json',{'phase':'passed' if passed else 'failed','completed':True})
        print('새 방법만 실행·검산 완료. summary.json의 이전 결과 대비 시간을 확인하세요.',flush=True)
        if not passed:raise RuntimeError('검산 실패')
    except Exception:
        write('status.json',{'phase':'실패: 로그 확인, 재실행은 새 출력 경로','completed':False})
        raise

if __name__=='__main__':main()
