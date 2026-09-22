"""4배 바람의 보존형 이어하기 묶음 준비·실행·진행도 표시."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time

DEFAULT='experiments/artifacts/runs/teacher_p3_shell_random/scale4_fast_continuation_v2'
RAW='experiments/artifacts/runs/teacher_p3_shell_random'
CONDITIONS=[('m8_s128',8,128,'forward'),('m16_s128',16,128,'forward'),
            ('m16_s256',16,256,'forward'),('m16_s256_backward',16,256,'backward'),
            ('m32_s256',32,256,'forward'),('m32_s128',32,128,'forward'),('m32_s256_backward',32,256,'backward')]
PAIRS=[('space8_16_s128','m8_s128','m16_s128',False),('time16_s128_256','m16_s128','m16_s256',True),
       ('direction16_s256','m16_s256','m16_s256_backward',True),('space16_32_s256','m16_s256','m32_s256',True),
       ('time32_s128_256','m32_s128','m32_s256',True),('direction32_s256','m32_s256','m32_s256_backward',True)]


def read(p):return json.loads(Path(p).read_text())


def write(p,value):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);temporary=p.with_suffix('.pending.json')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n');temporary.replace(p)


def identity(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return {'size_bytes':Path(p).stat().st_size,'sha256':h.hexdigest()}


def ref(p):return {'path':str(Path(p).resolve().relative_to(Path.cwd())),**identity(p)}


def make_tasks(runs,conditions=CONDITIONS,pairs=PAIRS,checkpoints=(18,42,66)):
    tasks=[]
    for key,*_ in conditions:
        natural=key+'_natural'
        for suffix in ('natural',*(f'reset{x}' for x in checkpoints)):
            name=key+'_'+suffix
            tasks.append({'id':'adopt_'+name,'kind':'adopt','run':name,'resource':'cpu','deps':[]})
            dependencies=['adopt_'+name]+(['replay_'+natural] if suffix!='natural' else [])
            tasks.append({'id':'simulate_'+name,'kind':'simulate','run':name,'resource':'gpu','deps':dependencies})
            tasks.append({'id':'audit_'+name,'kind':'audit','run':name,'resource':'gpu','deps':['simulate_'+name]})
        tasks.append({'id':'replay_'+natural,'kind':'replay','run':natural,'resource':'gpu','deps':['audit_'+natural]})
    for label,a,b,required in pairs:
        for suffix in ('natural',*(f'reset{x}' for x in checkpoints)):
            first,second=a+'_'+suffix,b+'_'+suffix
            tasks.append({'id':'compare_'+label+'_'+suffix,'kind':'compare','first':first,'second':second,
                          'required':required,'resource':'cpu','deps':['audit_'+first,'audit_'+second]})
    natural=('m32_s256' if 'm32_s256_natural' in runs else conditions[0][0])+'_natural'
    tasks.append({'id':'quadrature','kind':'quadrature','run':natural,'resource':'cpu','deps':['audit_'+natural]})
    return tasks


def prepare(output):
    if output.exists():raise ValueError('이미 준비한 폴더입니다. --prepare 없이 실행하세요')
    workspace=Path.cwd();runs={}
    for key,n,sub,diagonal in CONDITIONS:
        stem='20260909_scale4_natural_'+key+'_v1';natural=workspace/RAW/stem
        base=read(natural/'config.json')
        if (base['resolution'],base['substeps'],base['diagonal'],base['wind_scale'],base['end_frame'])!=(n,sub,diagonal,4.,90):
            raise ValueError('예상 실험 조건 불일치: '+stem)
        for suffix,checkpoint in [('natural',0),('reset18',18),('reset42',42),('reset66',66)]:
            old=natural if not checkpoint else natural.with_name(stem+'_'+suffix)
            config=dict(base,start_frame=checkpoint,reset_velocity=bool(checkpoint),parent_name=stem if checkpoint else None)
            spec={'config':config,'parent':key+'_natural' if checkpoint else None}
            if old.exists():
                config=read(old/'config.json');spec['config']=config
                required=['config.json','report.json','source_snapshot.zip','wind.npz']
                if checkpoint:required.append('reset_event.npz')
                if (old/'manifest.json').exists():required.append('manifest.json')
                ids={Path(nm).stem:ref(old/nm) for nm in required}
                legacy={'path':str(old.relative_to(workspace)),'identities':ids}
                audit=workspace/RAW/'verification'/('scale4_natural_'+key+'_v1')/(suffix+'.json')
                if audit.exists():legacy['audit']=ref(audit)
                spec['legacy']=legacy
            else:
                # 새 구간의 producer identity는 bundle runtime으로 기록한다.
                for field in ('source_sha256','environment'):config.pop(field,None)
            if not checkpoint:
                replay=natural.with_name(stem+'_checkpoint42_replay')
                if (replay/'manifest.json').exists() and read(replay/'report.json')['status']=='completed':
                    spec['replay']={'path':str(replay.relative_to(workspace)),
                                    'identities':{f:ref(replay/f) for f in ('config.json','report.json','manifest.json','frames/042.json')}}
            runs[key+'_'+suffix]=spec
    output.mkdir(parents=True)
    plan={'schema':'wind3dgs.p3_shell_segmented_continuation.v1','created_utc':datetime.now(timezone.utc).isoformat(),
          'runs':runs,'tasks':make_tasks(runs),'replay_frame':42,'training_eligible':False,'r1_complete':False,
          'scope':'승인된4배 바람7조건/4분기, 기존6비교와 선택 구적. 원본 보존 후 HVP/graph 이어하기.'}
    write(output/'plan.json',plan);freeze(output)
    write(output/'status.json',{'status':'준비 완료 — 사용자 실행 대기','completed':0,'total':len(plan['tasks'])})
    print('준비 완료: '+str(output.relative_to(workspace)),flush=True)


def freeze(output):
    code=Path.cwd()/'code';runtime=output/'runtime';target=runtime/'code'
    files=list((code/'wind3dgs').rglob('*.py'))+list((code/'tests').rglob('*.py'))+list((code/'scripts').glob('*.sh'))+[code/'pyproject.toml']
    manifest={}
    for src in files:
        p=target/src.relative_to(code);p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,p)
        manifest[str(p.relative_to(runtime))]=identity(p)
    runner=runtime/'run_remaining.py';shutil.copy2(Path(__file__),runner);manifest[runner.name]=identity(runner)
    manifest['../plan.json']=identity(output/'plan.json')
    write(runtime/'manifest.json',manifest)


def verify_runtime(output):
    for name,expected in read(output/'runtime/manifest.json').items():
        if name!='../plan.json' and (Path(name).is_absolute() or '..' in Path(name).parts):raise ValueError('Runtime 경로 불일치')
        if identity(output/'runtime'/name)!=expected:raise ValueError('동결 runtime/plan hash 불일치: '+name)


def active(output):
    found=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit() or int(p.name)==os.getpid():continue
        try:
            args=(p/'cmdline').read_bytes().decode().strip('\0').split('\0')
            marker='--bundle' if '--bundle' in args else '--output'
            if marker not in args:continue
            known='wind3dgs.evaluation.teacher_p3_shell_continuation' in args or (any(Path(x).name=='run_remaining.py' for x in args[:3]) and '--supervise' in args)
            if not known:continue
            target=Path(args[args.index(marker)+1])
            if not target.is_absolute():target=Path(os.readlink(p/'cwd'))/target
            if target.resolve()==output and (p/'stat').read_text().rsplit(')',1)[1].split()[0]!='Z':found.append(int(p.name))
        except (OSError,ValueError,IndexError):continue
    return found


def task_output(output,t):
    if t['kind'] in ('compare','quadrature'):return output/'results'/(t['id']+'.json')
    return output/'views'/t['run']/({'adopt':'adoption','simulate':'index','audit':'audit','replay':'replay'}[t['kind']]+'.json')


def launch_task(output,t,device,children,stopping):
    verify_runtime(output)
    if stopping.is_set():raise RuntimeError('사용자 중단으로 새 task를 시작하지 않습니다')
    log=output/'logs'/(t['id']+'_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%f')+'.log')
    env=dict(os.environ,PYTHONPATH=str(output/'runtime/code'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',
             WARP_CACHE_PATH=str(Path.cwd()/'code/outputs/warp-cache'),PYTHONUNBUFFERED='1')
    with log.open('x') as f:
        cmd=[sys.executable,'-u','-m','wind3dgs.evaluation.teacher_p3_shell_continuation','--bundle',str(output),'--task',t['id'],'--device',device]
        p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,env=env)
        children[t['id']]=p
        if stopping.is_set() and p.poll() is None:p.terminate()
        for line in p.stdout:
            safe=line.replace(str(Path.cwd()),'<workspace>');f.write(safe);f.flush()
        code=p.wait();children.pop(t['id'],None)
    if code:raise RuntimeError(t['id']+' 실패 — '+str(log.relative_to(Path.cwd())))
    artifact=task_output(output,t)
    write(output/'done'/(t['id']+'.json'),{'task':t['id'],'artifact':str(artifact.relative_to(output)),**identity(artifact)})
    return t['id']


def supervise(output,gpu_jobs,cpu_jobs,device):
    with (output/'scheduler.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if active(output):raise RuntimeError('기존 실행이 있어 중복 시작하지 않습니다')
        verify_runtime(output);plan=read(output/'plan.json');tasks=plan['tasks'];done=set();running={};children={};stopping=threading.Event()
        for folder in ('done','results','logs'): (output/folder).mkdir(exist_ok=True)
        for t in tasks:
            p=output/'done'/(t['id']+'.json')
            if p.exists():
                marker=read(p)
                if identity(task_output(output,t))!={k:marker[k] for k in ('size_bytes','sha256')}:raise ValueError('완료 task 산출물 hash 불일치')
                done.add(t['id'])
        limits={'gpu':gpu_jobs,'cpu':cpu_jobs};failed=None
        def interrupted(signum,frame):raise KeyboardInterrupt()
        signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
        try:
            with ThreadPoolExecutor(max_workers=gpu_jobs+cpu_jobs) as pool:
                try:
                    while len(done)<len(tasks):
                        for future,t in list(running.items()):
                            if future.done():
                                try:done.add(future.result())
                                except Exception as e:failed=str(e)
                                del running[future]
                        if failed:
                            stopping.set()
                            for child in list(children.values()):
                                if child.poll() is None:child.terminate()
                            if not running:raise RuntimeError(failed)
                        else:
                            in_progress={t['id'] for t in running.values()}
                            for t in tasks:
                                if t['id'] in done or t['id'] in in_progress or not set(t['deps'])<=done:continue
                                if sum(x['resource']==t['resource'] for x in running.values())>=limits[t['resource']]:continue
                                future=pool.submit(launch_task,output,t,device,children,stopping);running[future]=t;in_progress.add(t['id'])
                        write(output/'status.json',{'status':'실패 후 실행 중 작업 정리' if failed else '실행 중','completed':len(done),'total':len(tasks),
                                                  'active':[t['id'] for t in running.values()],'error':failed,'utc':datetime.now(timezone.utc).isoformat()})
                        if not running and len(done)<len(tasks):raise RuntimeError('의존성 교착 또는 선행 task 누락')
                        time.sleep(1)
                finally:
                    if sys.exc_info()[0]:
                        stopping.set()
                        for p in list(children.values()):
                            if p.poll() is None:p.terminate()
            comparisons={t['id']:read(task_output(output,t)) for t in tasks if t['kind']=='compare'}
            required=[t['id'] for t in tasks if t['kind']=='compare' and t['required']]
            quad=read(output/'results/quadrature.json')
            passed=all(comparisons[k]['interpolant_threshold_passed'] for k in required) and quad['selected_state_quadrature_passed']
            summary={'status':'통과' if passed else '기준 미달','required_comparisons':required,
                     'comparisons':{k:{'passed':v['interpolant_threshold_passed'],'bounds':v['interpolant_bounds']} for k,v in comparisons.items()},
                     'quadrature':quad,'threshold_relative':.01,'training_eligible':False,'r1_complete':False,
                     'scope':'4배 바람 세분 보완 진단. Coarse 실패는 별도 보존. 학습 적격성 채택 아님.'}
            write(output/'summary.json',summary);write(output/'status.json',{'status':'완료','result':summary['status'],'completed':len(done),'total':len(tasks)})
        except BaseException as e:
            write(output/'status.json',{'status':'중단 또는 실패','error':str(e).replace(str(Path.cwd()),'<workspace>'),'completed':len(done),'total':len(tasks)})
            raise


def watch(output,gpu_jobs,cpu_jobs,device):
    if not output.exists():prepare(output)
    verify_runtime(output)
    if not active(output) and read(output/'status.json')['status']!='완료':
        with (output/'scheduler.log').open('a') as log:
            p=subprocess.Popen([sys.executable,'-u',str(output/'runtime/run_remaining.py'),'--output',str(output),'--supervise',
                                '--gpu-jobs',str(gpu_jobs),'--cpu-jobs',str(cpu_jobs),'--device',device],
                               stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        for _ in range(50):
            if active(output) or p.poll() is not None:break
            time.sleep(.1)
    print('Ctrl+C는 표시만 종료합니다. 계산 중단: --stop / 같은 명령으로 이어하기.',flush=True)
    last=None;printed=0.
    while True:
        status=read(output/'status.json');progress=[]
        for task in status.get('active',[]):
            spec=next(t for t in read(output/'plan.json')['tasks'] if t['id']==task)
            f=output/'views'/spec.get('run','')/'progress.json'
            progress.append(task+(' '+str(read(f)['completed'])+'/'+str(read(f)['total']) if f.exists() else ''))
        message=f'{status["status"]}: {status.get("completed",0)}/{status.get("total",0)} task | '+', '.join(progress)
        if message!=last or time.monotonic()-printed>30:
            print(datetime.now().strftime('%H:%M:%S')+' '+message,flush=True);last=message;printed=time.monotonic()
        if not active(output):
            if status['status']=='완료':
                print('완료 판정: '+status['result']+' / summary.json을 검토하세요.',flush=True);return 0 if status['result']=='통과' else 2
            print('중단/실패: status.json, scheduler.log, logs/를 확인하세요.',flush=True);return 1
        time.sleep(5)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=Path(DEFAULT))
    p.add_argument('--prepare',action='store_true');p.add_argument('--status-only',action='store_true');p.add_argument('--stop',action='store_true')
    p.add_argument('--supervise',action='store_true',help=argparse.SUPPRESS);p.add_argument('--gpu-jobs',type=int,default=1);p.add_argument('--cpu-jobs',type=int,default=2)
    p.add_argument('--device',choices=('cuda:0','cpu'),default='cuda:0');a=p.parse_args();a.output=a.output.resolve()
    if not 1<=a.gpu_jobs<=2 or not 1<=a.cpu_jobs<=4:p.error('GPU 작업1~2개, CPU 작업1~4개 범위입니다')
    if a.prepare:prepare(a.output);return 0
    if a.status_only:print(json.dumps({'pids':active(a.output),'status':read(a.output/'status.json') if a.output.exists() else '준비 전'},ensure_ascii=False,indent=2));return 0
    if a.stop:
        processes=active(a.output)
        for pid in processes:
            try:os.kill(pid,signal.SIGTERM)
            except ProcessLookupError:pass
        deadline=time.monotonic()+12
        while active(a.output) and time.monotonic()<deadline:time.sleep(.2)
        if active(a.output):
            print('종료 요청 후 아직 프로세스가 남아 있습니다. --status-only로 확인하세요.');return 1
        print('계산 프로세스 종료 확인. 확정 frame은 보존됐으며 같은 명령으로 이어갑니다.');return 0
    if a.supervise:supervise(a.output,a.gpu_jobs,a.cpu_jobs,a.device);return 0
    return watch(a.output,a.gpu_jobs,a.cpu_jobs,a.device)


if __name__=='__main__':
    try:sys.exit(main())
    except KeyboardInterrupt:
        print('\n계산 중단. 확정 frame은 보존됩니다.' if '--supervise' in sys.argv else '\n표시 종료. 계산 중단은 --stop을 사용하세요.');sys.exit(130)
    except Exception as e:print('오류: '+str(e).replace(str(Path.cwd()),'<workspace>'),file=sys.stderr);sys.exit(1)
