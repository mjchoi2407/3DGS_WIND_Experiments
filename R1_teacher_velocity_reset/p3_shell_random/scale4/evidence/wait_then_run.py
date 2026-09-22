"""승인된 세분 검사를 선행 작업 종료 뒤 실행해 GPU 동시 작업 수를 유지한다."""
import argparse,json,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--after',type=Path,required=True)
p.add_argument('command',nargs=argparse.REMAINDER)
a=p.parse_args();command=a.command
if command[0]=='--':command=command[1:]
print('선행 검증 완료 대기:',a.after,flush=True)
while True:
 if a.after.exists():
  try:d=json.loads(a.after.read_text())
  except json.JSONDecodeError:d={}
  if d.get('status')=='completed':break
  if d.get('status')=='failed':raise RuntimeError('선행 검증 실패: '+str(a.after))
 time.sleep(5)
print('선행 검증 완료, 승인된 다음 세분 계산을 시작합니다.',flush=True)
raise SystemExit(subprocess.call(command))
