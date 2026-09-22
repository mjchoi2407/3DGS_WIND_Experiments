"""저장된 완료 원본의 짧은 구간을 변경 없는 solver로 재생하는 CPU wall-time 진단."""
import argparse, cProfile, hashlib, json, pstats, time
from pathlib import Path
import numpy as np
from wind3dgs.evaluation.teacher_p3_shell_random import inspect_run, sources, file_identity
from wind3dgs.teacher.p3_shell import P3Shell
from wind3dgs.teacher.p3_shell_warp import P3ShellWarp, P3ShellWarpStepper

p=argparse.ArgumentParser(); p.add_argument('--parent',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=False)
def write(name,data): (a.output/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
config,_=inspect_run(a.parent)
assert config['source_sha256']==sources(), '원본과 현행 source 불일치'
rows=[]
for f in sorted((a.parent/'frames').glob('*.json')):
 d=json.loads(f.read_text()); h=[s['hvp_calls'] for s in d['steps']]
 for i in range(0,len(h)-3,4): rows.append((sum(h[i:i+4]),d['frame'],i))
selected=[('가벼운 구간',min(rows)),('무거운 구간',max(rows)),('바람 종료 구간',max(r for r in rows if r[1]>=72))]
t=time.perf_counter(); model=P3ShellWarp(P3Shell(config['resolution'],diagonal=config['diagonal']),device='cuda:0'); stepper=P3ShellWarpStepper(model)
setup=time.perf_counter()-t
results=[]
for label,(h,frame,start) in selected:
 path=a.parent/'frames'/f'{frame:03d}.npz'
 with np.load(path,allow_pickle=False) as z: arrays={k:z[k] for k in z.files}
 def state():return stepper.state(displacement=arrays['u_m'][start],velocity=arrays['v_m_s'][start],time_s=float(arrays['time_s'][start]))
 dt=1/(60*config['substeps']); force=arrays['held_force_n']
 stepper.step(state(),force,dt) # compilation / preconditioner warmup
 def replay():
  s=state(); diagnostics=[]
  for _ in range(4): s,d=stepper.step(s,force,dt); diagnostics.append(d)
  return s,diagnostics
 t=time.perf_counter(); baseline,_=replay(); baseline_s=time.perf_counter()-t
 pr=cProfile.Profile(); t=time.perf_counter(); pr.enable(); result,diag=replay(); pr.disable(); elapsed=time.perf_counter()-t
 stats=pstats.Stats(pr); functions=[]
 for (filename,line,name),(cc,nc,tt,ct,callers) in stats.stats.items():
  functions.append(dict(file=Path(filename).name,line=line,name=name,calls=nc,self_s=tt,inclusive_s=ct))
 functions.sort(key=lambda x:x['self_s'],reverse=True)
 # cProfile 자체 시간 only: disjoint buckets, no inclusive-time double counting.
 groups={k:0. for k in ['GPU 동기화 대기','CPU 희소 직접 풀이','CPU GMRES','기타']}
 for r in functions:
  name=r['name']; file=r['file']
  key='기타'
  if 'synchronize' in name:key='GPU 동기화 대기'
  elif 'SuperLU' in name or file=='linsolve.py':key='CPU 희소 직접 풀이'
  elif file=='iterative.py':key='CPU GMRES'
  groups[key]+=r['self_s']
 diffu=float(np.max(np.abs(result.displacement_m-arrays['u_m'][start+4])))
 diffv=float(np.max(np.abs(result.velocity_m_s-arrays['v_m_s'][start+4])))
 item=dict(label=label,frame=frame,start_substep=start,steps=4,original_hvp=h,replay_hvp=sum(d['hvp_calls'] for d in diag),baseline_s=baseline_s,profiled_s=elapsed,max_displacement_difference_m=diffu,max_velocity_difference_m_s=diffv,repeat_exact=bool(np.array_equal(baseline.displacement_m,result.displacement_m) and np.array_equal(baseline.velocity_m_s,result.velocity_m_s)),within_1e_10=diffu<=1e-10 and diffv<=1e-10,exclusive_groups_s=groups,functions=functions,frame_identity=file_identity(path))
 results.append(item); write('report.json',dict(status='진행 중',setup_s=setup,results=results)); print(label,elapsed,groups, '원본 차이',diffu,diffv,flush=True)
write('report.json',dict(status='완료',scope='시간 구간 3개 × 4 substep; 시뮬레이션 step만 측정, 전체 raw 검산/저장 비용 제외',caveat='cProfile CPU wall-time; GPU kernel 실제 실행시간과 전송시간은 직접 분리 측정하지 않음. 다른 GPU 부하 영향 가능. inclusive 시간 합산 금지.',setup_s=setup,parent_name=a.parent.name,parent_manifest=file_identity(a.parent/'manifest.json'),source_sha256=sources(),profiler_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),device=str(model.device),results=results))
