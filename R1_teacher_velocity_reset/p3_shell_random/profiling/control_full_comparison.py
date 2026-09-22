"""기존 전체 비교에 연결하거나 저장된 frame부터 이어서 실행한다."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import full_comparison as driver

DEFAULT_OUTPUT='experiments/artifacts/runs/teacher_p3_shell_profile/20260910_full_pair_v1'
STAGES=['baseline','fast','audit_baseline','audit_fast','compare']


def read(path):
    return json.loads(path.read_text()) if path.exists() else {}


def active(output):
    """시작 PID 파일만 신뢰하지 않고 명령·output·프로세스 상태를 확인한다."""
    found=[]
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
        try:
            args=(proc/'cmdline').read_bytes().decode().strip('\0').split('\0')
            if '--output' not in args:continue
            names={Path(x).name for x in args[:3]}
            known=bool(names & {'full_comparison.py','driver.py'})
            known|='control_full_comparison.py' in names and ('--supervise' in args or '--worker' in args)
            if not known:continue
            target=Path(args[args.index('--output')+1])
            if not target.is_absolute():target=Path(os.readlink(proc/'cwd'))/target
            if target.resolve()!=output:continue
            stat=(proc/'stat').read_text().rsplit(')',1)[1].split()
            if stat[0]!='Z':found.append(int(proc.name))
        except (OSError,ValueError,IndexError):continue
    return found


def verify_snapshot(output):
    manifest=read(output/'runtime/manifest.json')
    if not manifest.get('code') or not manifest.get('driver'):raise ValueError('동결 소스 manifest 없음')
    for name,expected in manifest['code'].items():
        path=Path(name)
        if path.is_absolute() or '..' in path.parts:raise ValueError('소스 경로 불일치')
        if driver.identity(output/'runtime/code'/path)!=expected:raise ValueError('동결 소스 hash 불일치: '+name)
    if driver.identity(output/'runtime/driver.py')!=manifest['driver']:raise ValueError('원 실행기 hash 불일치')


def options(output,stage):
    c=read(output/'config.json')
    if c.get('schema')!='wind3dgs.p3_shell_full_backend_comparison.v1':raise ValueError('지원하지 않는 실행 schema')
    if c.get('wind_scale')!=4. or c.get('fps')!=60 or c.get('seed')!=20260909:raise ValueError('바람/시간 설정 불일치')
    if c.get('threshold_relative')!=.01 or c.get('order')!=STAGES:raise ValueError('검증 기준/순서 불일치')
    return SimpleNamespace(output=output,worker=stage,resume=True,**{k:c[k] for k in ('resolution','substeps','frames','device','smoke')})


def done(output,stage,frames):
    if stage in ('baseline','fast'):
        r=read(output/stage/'report.json')
        return r.get('status')=='계산 완료' and r.get('completed_frames')==frames and len(r.get('frames',[]))==frames
    if stage.startswith('audit_'):
        r=read(output/stage[6:]/'audit.json')
        return r.get('status')=='검산 통과' and len(r.get('frames',[]))==frames
    r=read(output/'comparison.json')
    return r.get('status')=='통과' and len(r.get('frame_results',[]))==frames


def supervise(output):
    with (output/'control.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if active(output):raise RuntimeError('기존 계산 프로세스가 있어 중복 실행하지 않습니다')
        verify_snapshot(output);a=options(output,'baseline')
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%f')
        history=output/'continuations'/stamp;history.mkdir(parents=True)
        if (output/'status.json').exists():shutil.copy2(output/'status.json',history/'previous_status.json')
        status={'status':'실행 중','stage':'이어하기 확인','completed_stages':[],
                'started_utc':datetime.now(timezone.utc).isoformat(),'continuation':stamp}
        driver.write(output/'status.json',status)
        stop=threading.Event()
        def telemetry():
            with (output/'gpu_load.jsonl').open('a') as log:
                while not stop.is_set():
                    try:
                        q=subprocess.run(['nvidia-smi','--query-gpu=utilization.gpu,memory.used,temperature.gpu,power.draw','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=5)
                        value={'utc':datetime.now(timezone.utc).isoformat(),'value':q.stdout.strip(),'returncode':q.returncode}
                    except Exception as e:value={'utc':datetime.now(timezone.utc).isoformat(),'error':type(e).__name__}
                    log.write(json.dumps(value)+'\n');log.flush();stop.wait(10)
        monitor=threading.Thread(target=telemetry,daemon=True);monitor.start()
        try:
            invalidated=set()
            for stage in STAGES:
                if stage not in invalidated and done(output,stage,a.frames):
                    status['completed_stages'].append(stage);continue
                if stage in ('baseline','fast'):invalidated.update(('audit_'+stage,'compare'))
                if stage.startswith('audit_'):invalidated.add('compare')
                stale=[]
                if stage in ('baseline','fast'):stale.append(output/stage/'audit.json')
                if stage!='compare':stale.extend((output/'comparison.json',output/'summary.md'))
                for old in stale:
                    if old.exists():old.rename(history/(stage+'_invalidated_'+old.name))
                status['stage']=stage;driver.write(output/'status.json',status)
                # 중단된 검산/비교는 원본 보고서를 보존하고 해당 단계 전체를 재검산한다.
                artifact=output/stage[6:]/'audit.json' if stage.startswith('audit_') else output/'comparison.json' if stage=='compare' else output/stage/'report.json'
                if artifact.exists():shutil.copy2(artifact,history/(stage+'_previous.json'))
                cmd=[sys.executable,'-u',str(Path(__file__).resolve()),'--output',str(output),'--worker',stage]
                env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONUNBUFFERED='1',WARP_CACHE_PATH=str(Path.cwd()/'code/outputs/warp-cache'))
                with (history/(stage+'.log')).open('x') as log:
                    p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,env=env)
                    for line in p.stdout:
                        safe=line.replace(str(Path.cwd()),'<workspace>');log.write(safe);log.flush();print(safe,end='',flush=True)
                    if p.wait():raise RuntimeError(stage+' 계산 실패: continuation 로그를 확인하세요')
                status['completed_stages'].append(stage);driver.write(output/'status.json',status)
            status.update(status='완료',finished_utc=datetime.now(timezone.utc).isoformat());driver.write(output/'status.json',status)
            r=read(output/'comparison.json')
            (output/'summary.md').write_text('# 전체 시뮬레이션 비교\n\n원식·기하 검산과 기존 1% 응답 차이 기준 통과.\n\n계산 시간 비율: '+str(r['simulation_speedup'])+'배. 다른 GPU 부하와 재시작 영향을 포함하는 잠정 성능값이다.\n\n상세 결과는 comparison.json, 재시작 준비 비용은 각 report.json의 resume_events를 확인한다.\n')
        except BaseException as e:
            status.update(status='중단 또는 실패',error=str(e).replace(str(Path.cwd()),'<workspace>'));driver.write(output/'status.json',status);raise
        finally:stop.set();monitor.join(timeout=6)


def launch(output):
    verify_snapshot(output);options(output,'baseline')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%f')
    source=output/'runtime/controls'/stamp;source.mkdir(parents=True)
    for name in ('control_full_comparison.py','full_comparison.py'):
        shutil.copy2(Path(__file__).parent/name,source/name)
    driver.write(source/'manifest.json',{p.name:driver.identity(p) for p in source.glob('*.py')})
    with (output/'continuation.launch.log').open('a') as log:
        p=subprocess.Popen([sys.executable,'-u',str(source/'control_full_comparison.py'),'--output',str(output),'--supervise'],
                           stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
                           env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'))
    driver.write(source/'launch.json',{'pid':p.pid,'utc':datetime.now(timezone.utc).isoformat()})
    print(f'저장 결과부터 이어하기 시작: PID {p.pid}',flush=True)
    for _ in range(50):
        if active(output) or p.poll() is not None:break
        time.sleep(.1)
    return p


def watch(output,interval):
    if not output.is_dir():raise ValueError('기존 결과 폴더가 없습니다: --output으로 지정하세요')
    config=read(output/'config.json');frames=config.get('frames',90)
    processes=active(output)
    if processes:print(f'실행 중인 작업에 연결: PID {processes}. 중복 실행하지 않습니다.',flush=True)
    elif read(output/'status.json').get('status')!='완료':launch(output)
    print('Ctrl+C는 진행도 표시만 종료합니다. 계산은 계속됩니다. 같은 명령으로 다시 연결할 수 있습니다.',flush=True)
    last=None;last_time=0.
    while True:
        status=read(output/'status.json');parts=[]
        for backend in ('baseline','fast'):
            r=read(output/backend/'report.json');audit=read(output/backend/'audit.json')
            count=r.get('completed_frames',0);label='기존' if backend=='baseline' else '개선'
            parts.append(f'{label} 계산 {count}/{frames} ({100*count/frames:.1f}%), 검산 {len(audit.get("frames",[]))}/{frames}')
        result=read(output/'comparison.json')
        msg=f'{status.get("status","확인 중")} / {status.get("stage","준비")} | '+ ' | '.join(parts)
        now=time.monotonic()
        if msg!=last or now-last_time>=30:
            stage=status.get('stage');report=output/str(stage)/'report.json'
            age=f' | 마지막 frame 보고 후 {time.time()-report.stat().st_mtime:.0f}초' if stage in ('baseline','fast') and report.exists() else ''
            print(datetime.now().astimezone().strftime('%H:%M:%S')+' '+msg+age,flush=True);last=msg;last_time=now
        processes=active(output)
        if not processes:
            if status.get('status')=='완료' and result.get('status')=='통과':
                print(f'완료: 전체 검산·비교 통과. 잠정 계산 속도 비율 {result["simulation_speedup"]:.3f}배.',flush=True)
                print('검토할 파일: '+str(output.relative_to(Path.cwd()) if output.is_relative_to(Path.cwd()) else output)+'/comparison.json',flush=True);return 0
            print('실행 프로세스가 종료됐지만 전체 검증 완료가 아닙니다. 오류 로그를 확인하세요. 자동 재시도하지 않습니다.',flush=True)
            print('기존 로그: *.log / 재시작 로그: continuation.launch.log 및 continuations/',flush=True);return 1
        time.sleep(interval)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=Path(DEFAULT_OUTPUT))
    p.add_argument('--interval',type=float,default=10.);p.add_argument('--worker',choices=STAGES,help=argparse.SUPPRESS)
    p.add_argument('--supervise',action='store_true',help=argparse.SUPPRESS);p.add_argument('--status-only',action='store_true')
    a=p.parse_args();a.output=a.output.resolve()
    if not 1<=a.interval<=60:p.error('확인 간격은 1~60초입니다')
    if a.worker:driver.worker(options(a.output,a.worker));return 0
    if a.supervise:supervise(a.output);return 0
    if a.status_only:
        print(json.dumps({'pids':active(a.output),'status':read(a.output/'status.json')},ensure_ascii=False,indent=2));return 0
    return watch(a.output,a.interval)


if __name__=='__main__':
    try:sys.exit(main())
    except KeyboardInterrupt:print('\n진행도 표시를 종료했습니다. 계산 프로세스는 유지됩니다.');sys.exit(130)
    except Exception as e:print('실행 오류: '+str(e).replace(str(Path.cwd()),'<workspace>'),file=sys.stderr);sys.exit(1)
