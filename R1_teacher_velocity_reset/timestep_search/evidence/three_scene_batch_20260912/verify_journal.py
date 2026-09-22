import json,os,subprocess,sys
from pathlib import Path
import numpy as np
root=Path('experiments/artifacts/runs/teacher_timestep_search/20260912_three_scene_journal_validation_v1');shape='handkerchief'
env=dict(os.environ,PYTHONPATH=str((root/'runtime/code').resolve()),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
command=[sys.executable,'-u','-m','wind3dgs.evaluation.teacher_three_scene_run',str(root),'--worker',shape]
with (root/'validation.log').open('w') as log:
 subprocess.run(command+['--stop-after-frames','2'],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=240,check=True)
 partial=root/shape/'frames/002.npz.pending';partial.write_bytes(b'interrupted-test')
 subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=240,check=True)
r=json.loads((root/shape/'report.json').read_text());assert r['status']=='complete'
assert any(p.read_bytes()==b'interrupted-test' for p in (root/shape/'recovery').rglob('*.pending'))
assert all(len((root/shape/'frames'/f'{i:03d}.steps.jsonl').read_text().splitlines())==64 for i in range(3))
original=root.parent/'20260912_three_scene_validation_v1'/shape/'frames/002.npz'
with np.load(original) as a,np.load(root/shape/'frames/002.npz') as b:assert all(np.array_equal(a[k],b[k]) for k in a.files)
(root/'checks.json').write_text(json.dumps({'status':'passed','orphan_preserved':True,'journal_rows':192,'trace_exact':True},indent=2)+'\n')
print('단계 로그·부분 파일 보존·재시작 검증 통과',flush=True)
