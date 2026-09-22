"""전체 natural 응답의 baseline/fast 순차 실행·원식 검산·시간 비교. 물리 구현은 재사용한다."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import traceback


def write(path, value):
    temporary=path.with_suffix('.pending.json')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    temporary.replace(path)


def identity(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return {'sha256':h.hexdigest(),'bytes':path.stat().st_size}


def arguments():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--device',default='cuda:0',choices=['cuda:0','cpu'])
    p.add_argument('--resolution',type=int,default=32)
    p.add_argument('--substeps',type=int,default=256)
    p.add_argument('--frames',type=int,default=90)
    p.add_argument('--smoke',action='store_true')
    p.add_argument('--worker',choices=['baseline','fast','audit_baseline','audit_fast','compare'])
    a=p.parse_args();a.output=a.output.resolve()
    if not a.smoke and (a.resolution,a.substeps,a.frames,a.device)!=(32,256,90,'cuda:0'):
        p.error('전체 비교는 n32/sub256/90 frame/CUDA0 고정. 작은 실행에는 --smoke 필요')
    if not 1<=a.frames<=90 or a.substeps<1:p.error('잘못된 frame/substep 범위')
    return a


def worker(a):
    sys.path.insert(0,str(a.output/'runtime/code'))
    import numpy as np
    from wind3dgs.teacher.p3_shell import P3Shell
    from wind3dgs.teacher.p3_shell_warp import P3ShellWarp,P3ShellWarpStepper
    from wind3dgs.teacher.p3_shell_warp_fast import P3ShellWarpFast,P3ShellWarpFastStepper
    from wind3dgs.teacher.p3_shell_dynamics import ShellSolvePolicy
    from wind3dgs.evaluation.teacher_p3_shell_random import advance_frame,wind_program,write_arrays,file_identity
    from wind3dgs.evaluation.teacher_p3_shell_random_validation import load_frame,verify_frame
    from wind3dgs.evaluation.teacher_p3_shell_random_comparison import SpatialComparison,area_rms
    stage=a.worker
    if stage in ('baseline','fast'):
        folder=a.output/stage
        resume=getattr(a,'resume',False) and (folder/'report.json').exists()
        if resume:
            r=json.loads((folder/'report.json').read_text())
            start=r['completed_frames']
            if r['backend']!=stage or not 0<=start<=a.frames or len(r['frames'])!=start:
                raise ValueError('이어하기 report 불일치')
            if [x['frame'] for x in r['frames']]!=list(range(start)):
                raise ValueError('이어하기 frame 순서 불일치')
            # 저장/보고서 갱신 사이에 중단된 파일은 보존하고 해당 frame을 다시 계산한다.
            orphan=[p for p in (folder/'frames').iterdir() if p.name[:3].isdigit() and int(p.name[:3])>=start]
            if orphan:
                backup=folder/'recovery'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%f');backup.mkdir(parents=True)
                for p in orphan:p.rename(backup/p.name)
        else:
            folder.mkdir(exist_ok=getattr(a,'resume',False));(folder/'frames').mkdir(exist_ok=getattr(a,'resume',False))
            if any((folder/'frames').iterdir()):raise ValueError('report 없는 기존 frame은 자동 덮어쓰지 않습니다')
            r={'status':'준비 중','backend':stage,'completed_frames':0,'frames':[]};start=0
            write(folder/'report.json',r)
        t=time.perf_counter()
        base=P3Shell(a.resolution)
        model=P3ShellWarp(base,device=a.device) if stage=='baseline' else P3ShellWarpFast(base,device=a.device,capture=True)
        stepper=P3ShellWarpStepper(model) if stage=='baseline' else P3ShellWarpFastStepper(model)
        setup=time.perf_counter()-t;t=time.perf_counter()
        u=np.zeros_like(base.rest_positions);u[:,1]=.001*(base.xy[:,0]-.25)**2;u[~base.free]=0.
        warm=stepper.state(displacement=u)
        f=model.aerodynamic_force_displacement(u,warm.velocity_m_s,[0.,1.,0.])['force_n']
        stepper.step(warm,f,1/(60*a.substeps))
        state=stepper.state();warmup=time.perf_counter()-t
        if resume:
            r.setdefault('resume_events',[]).append({'utc':datetime.now(timezone.utc).isoformat(),'completed_frames':start,'setup_s':setup,'warmup_s':warmup})
            r.setdefault('setup_s',setup);r.setdefault('warmup_s',warmup)
            if start:
                trace,steps=load_frame(folder,start-1)
                if len(steps)!=a.substeps or trace['u_m'].shape[0]!=a.substeps+1 or not bool(trace['completed']):
                    raise ValueError('이어하기 경계 frame 불완전')
                state=stepper.state(displacement=trace['u_m'][-1],velocity=trace['v_m_s'][-1],time_s=float(trace['time_s'][-1]))
        else:r.update(setup_s=setup,warmup_s=warmup)
        wind,_=wind_program(4.);r['status']='계산 중'
        r.setdefault('simulation_s',0.);r.setdefault('write_s',0.)
        write(folder/'report.json',r)
        for frame in range(start,a.frames):
            started_utc=datetime.now(timezone.utc).isoformat()
            t=time.perf_counter();state,arrays,diagnostics,error=advance_frame(stepper,state,wind[frame],a.substeps)
            elapsed=time.perf_counter()-t
            if error is not None:raise error
            t=time.perf_counter();path=folder/'frames'/f'{frame:03d}.npz';write_arrays(path,arrays)
            write(path.with_suffix('.json'),{'frame':frame,'completed':True,'array_identity':file_identity(path),'steps':diagnostics})
            io=time.perf_counter()-t
            r['simulation_s']+=elapsed;r['write_s']+=io
            r['frames'].append({'frame':frame,'started_utc':started_utc,'finished_utc':datetime.now(timezone.utc).isoformat(),'simulation_s':elapsed,'write_s':io,'hvp_calls':sum(x['hvp_calls'] for x in diagnostics)})
            r['completed_frames']=frame+1;write(folder/'report.json',r)
            print(f'{stage}: 계산 {frame+1}/{a.frames}, 계산 {elapsed:.2f}초, 저장 {io:.2f}초',flush=True)
        r['status']='계산 완료';write(folder/'report.json',r)
        return
    if stage.startswith('audit_'):
        folder=a.output/stage.removeprefix('audit_');r={'status':'검산 중','frames':[],'audit_s':0.,'read_s':0.}
        m=P3ShellWarp(P3Shell(a.resolution),device=a.device);previous=None
        for frame in range(a.frames):
            t=time.perf_counter();trace,steps=load_frame(folder,frame);r['read_s']+=time.perf_counter()-t
            if previous is not None:
                for name,value in zip(['u_m','v_m_s','time_s'],previous):np.testing.assert_array_equal(trace[name][0],value)
            previous=[trace[name][-1].copy() for name in ['u_m','v_m_s','time_s']]
            t=time.perf_counter();audit=verify_frame(m,trace,steps,frame=frame,substeps=a.substeps,policy=ShellSolvePolicy(),cpu_reference=m.reference,wind_scale=4.)
            r['audit_s']+=time.perf_counter()-t;r['frames'].append(audit)
            write(folder/'audit.json',r);print(f'{stage}: 원식·기하 검산 {frame+1}/{a.frames}',flush=True)
        r['status']='검산 통과';write(folder/'audit.json',r);return
    model=P3Shell(a.resolution);spatial=SpatialComparison(model,model)
    upper={'u_m':0.,'v_m_s':0.};ref={k:0. for k in upper};absolute={k:0. for k in upper};rows=[]
    dt=1/(60*a.substeps)
    for frame in range(a.frames):
        b,_=load_frame(a.output/'baseline',frame);f,_=load_frame(a.output/'fast',frame)
        for key in ['time_s','wind_m_s']:np.testing.assert_array_equal(b[key],f[key])
        defects=[float(area_rms(model,2*(t['u_m'][1:]-t['u_m'][:-1])/dt-t['v_m_s'][:-1]-t['v_m_s'][1:]).max()) for t in [b,f]]
        peaks={k:spatial.peaks(f[k],b[k]) for k in upper}
        padding=.5*dt*(peaks['v_m_s'][0]+sum(defects))
        for k,(error,reference) in peaks.items():
            upper[k]=max(upper[k],error+(padding if k=='u_m' else 0.));ref[k]=max(ref[k],reference)
            absolute[k]=max(absolute[k],float(np.max(np.abs(f[k]-b[k]))))
        rows.append({'frame':frame,'rms_peaks':peaks,'position_padding_m':padding})
        print(f'비교: 전체 보간 차이 {frame+1}/{a.frames}',flush=True)
    bounds={k:{'absolute_rms_upper':upper[k],'reference_peak_lower':ref[k],'relative_upper':upper[k]/max(ref[k],1e-15),'max_nodal_component_difference':absolute[k]} for k in upper}
    times={}
    for name in ['baseline','fast']:
        r=json.loads((a.output/name/'report.json').read_text());audit=json.loads((a.output/name/'audit.json').read_text())
        if r['status']!='계산 완료' or audit['status']!='검산 통과':raise ValueError('미완료 결과')
        times[name]={k:r[k] for k in ['setup_s','warmup_s','simulation_s','write_s']}
        times[name].update(audit_s=audit['audit_s'],audit_read_s=audit['read_s'])
        times[name]['resume_setup_warmup_s']=sum(x['setup_s']+x['warmup_s'] for x in r.get('resume_events',[]))
    passes=max(x['relative_upper'] for x in bounds.values())<.01
    out={'status':'통과' if passes else '차이 기준 미달','interpolant_bounds':bounds,'threshold_relative':.01,
         'position_increment_equals_displacement':True,'scope':'rest natural 전체 보간 수치 비교. R1 전체/ODE 인증 아님.',
         'timing_s':times,'simulation_speedup':times['baseline']['simulation_s']/times['fast']['simulation_s'],
         'simulation_speed_improved':times['fast']['simulation_s']<times['baseline']['simulation_s'],
         'simulation_time_reduction_fraction':1-times['fast']['simulation_s']/times['baseline']['simulation_s'],
         'contains_resumed_simulation':any(json.loads((a.output/name/'report.json').read_text()).get('resume_events',[]) for name in ('baseline','fast')),
         'timing_is_provisional_due_to_other_gpu_load':True,'frame_results':rows,'training_eligible':False,'r1_complete':False}
    write(a.output/'comparison.json',out)
    if not passes:raise ValueError('기존 1% 응답 차이 기준 미달')


def run(a):
    if a.worker:
        worker(a);return
    a.output.mkdir(parents=True,exist_ok=False)
    workspace=Path.cwd();runtime=a.output/'runtime';runtime.mkdir();code=workspace/'code'
    files=list((code/'wind3dgs').rglob('*.py'))+[code/'pyproject.toml']
    manifest={}
    for src in files:
        rel=src.relative_to(code);dest=runtime/'code'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(src.read_bytes())
        manifest[str(rel)]=identity(dest)
    driver=runtime/'driver.py';driver.write_bytes(Path(__file__).read_bytes())
    write(runtime/'manifest.json',{'code':manifest,'driver':identity(driver)})
    write(a.output/'config.json',{'schema':'wind3dgs.p3_shell_full_backend_comparison.v1','resolution':a.resolution,'substeps':a.substeps,'frames':a.frames,'fps':60,'wind_scale':4.,'seed':20260909,
        'device':a.device,'smoke':a.smoke,'order':['baseline','fast','audit_baseline','audit_fast','compare'],
        'threshold_relative':.01,'scope':'CPU 반복 풀이 유지. 새로운 GPU 보조 풀이 선택을 대신하지 않음.',
        'other_gpu_load_accepted':True,'training_eligible':False,'r1_complete':False,'generated_training_samples':0})
    status={'status':'실행 중','started_utc':datetime.now(timezone.utc).isoformat(),'completed_stages':[]}
    write(a.output/'status.json',status)
    stop=threading.Event()
    def telemetry():
        with (a.output/'gpu_load.jsonl').open('a') as log:
            while not stop.is_set():
                try:
                    q=subprocess.run(['nvidia-smi','--query-gpu=utilization.gpu,memory.used,temperature.gpu,power.draw','--format=csv,noheader,nounits'],text=True,capture_output=True,timeout=5)
                    log.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'value':q.stdout.strip(),'returncode':q.returncode})+'\n');log.flush()
                except Exception as e:log.write(json.dumps({'error':type(e).__name__})+'\n');log.flush()
                stop.wait(10)
    monitor=threading.Thread(target=telemetry,daemon=True);monitor.start()
    try:
        for stage in ['baseline','fast','audit_baseline','audit_fast','compare']:
            status['stage']=stage;write(a.output/'status.json',status)
            cmd=[sys.executable,'-u',str(driver),'--output',str(a.output),'--worker',stage,'--device',a.device,'--resolution',str(a.resolution),'--substeps',str(a.substeps),'--frames',str(a.frames)]
            if a.smoke:cmd.append('--smoke')
            env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONUNBUFFERED='1',WARP_CACHE_PATH=str(workspace/'code/outputs/warp-cache'))
            with (a.output/(stage+'.log')).open('x') as log:
                process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,env=env)
                for line in process.stdout:
                    safe=line.replace(str(workspace),'<workspace>');log.write(safe);log.flush();print(safe,end='',flush=True)
                result=process.wait()
            if result:raise RuntimeError(f'{stage}: 종료 코드 {result}')
            status['completed_stages'].append(stage);write(a.output/'status.json',status)
        status['status']='완료';status['finished_utc']=datetime.now(timezone.utc).isoformat();write(a.output/'status.json',status)
        result=json.loads((a.output/'comparison.json').read_text())
        (a.output/'summary.md').write_text('# 전체 시뮬레이션 비교\n\n원식·기하 검산 및 전체 보간 차이 기준 통과.\n\n계산 시간 비율: '+str(result['simulation_speedup'])+'배. 다른 GPU 부하가 있어 잠정 성능 결과다.\n\n상세 시간·정확도는 comparison.json, 설정은 config.json, 소스는 runtime/manifest.json을 확인한다.\n')
    except BaseException as error:
        status.update(status='중단 또는 실패',error=str(error).replace(str(workspace),'<workspace>'))
        write(a.output/'status.json',status);raise
    finally:stop.set();monitor.join(timeout=6)


if __name__=='__main__':
    run(arguments())
