"""선택한 P3 shell 개발 run의 완료 원본을 불변 경로에 재검산하는 실험 wrapper."""
from pathlib import Path
import hashlib,json,time
from wind3dgs.evaluation.teacher_p3_shell_validation import verify_wind,compare_runs,validation_sources

root=Path('experiments/artifacts/runs/teacher_p3_shell')
out=root/'verification_final_v5'
out.mkdir(exist_ok=False)
sources=validation_sources()
pending=[p for p in sorted(root.iterdir()) if (p/'config.json').exists()
         and json.loads((p/'config.json').read_text())['phase']=='wind']
completed=[]
while pending:
    ready=[p for p in pending if (p/'manifest.json').exists()]
    if not ready:
        time.sleep(5)
        continue
    for p in ready:
        assert sources==validation_sources(),'검산 중 source가 변경되었습니다'
        result=verify_wind(p)
        with (out/(p.name+'.json')).open('x') as f:
            json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
        pending.remove(p);completed.append(p.name)
        print(f'최종 원본 검산 완료: {p.name} / 누적 {len(completed)}, 대기 {len(pending)}',flush=True)

pairs=[
('weak_time4','wind_m4_s64_v1','wind_m4_s128_v1'),
('weak_time8','wind_m8_s64_v1','wind_m8_s128_v1'),
('weak_time16','wind_m16_s128_v1','wind_m16_s256_v1'),
('weak_time32','wind_m32_s128_v1','wind_m32_s256_forward_v1'),
('weak_space4_8','wind_m4_s64_v1','wind_m8_s64_v1'),
('weak_space8_16','wind_m8_s128_v1','wind_m16_s128_v1'),
('weak_space16_32','wind_m16_s128_v1','wind_m32_s128_v1'),
('weak_space16_32_finer_time','wind_m16_s256_v1','wind_m32_s256_forward_v1'),
('weak_direction16','wind_m16_s128_v1','wind_m16_s128_backward_v1'),
('bent_time128_256','bent_m4_s128_v2','bent_m4_s256_v2'),
('bent_time256_1024','bent_m4_s256_v2','bent_m4_s1024_v3'),
('bent_time1024_2048','bent_m4_s1024_v3','bent_m4_s2048_v3'),
('bent_space4_8','bent_m4_s256_v2','bent_m8_s256_v2'),
('strong_time4','strong_reset_m4_s128_v4','strong_reset_m4_s256_v4'),
('strong_time8','strong_reset_m8_s128_v4','strong_reset_m8_s256_v4'),
('strong_time16','strong_reset_m16_s128_v4','strong_reset_m16_s256_v4'),
('strong_space4_8','strong_reset_m4_s128_v4','strong_reset_m8_s128_v4'),
('strong_space8_16','strong_reset_m8_s128_v4','strong_reset_m16_s128_v4'),
('strong_space16_32','strong_reset_m16_s128_v4','strong_reset_m32_s128_v4'),
('strong_direction16','strong_reset_m16_s128_v4','strong_reset_m16_s128_backward_v4'),
]
comparisons={}
for name,a,b in pairs:
    comparisons[name]=compare_runs(root/('20260909_'+a),root/('20260909_'+b))
    print('최종 비교 완료:',name,'속도 차이',comparisons[name]['errors']['v_m_s']['relative'],flush=True)
value={'training_eligible':False,'r1_complete':False,'generated_training_samples':0,
       'validation_source_sha256':sources,'verified_runs':sorted(completed),'comparisons':comparisons}
with (out/'comparison_summary.json').open('x') as f:
    json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
print('최종 선택 run 검산 종료',flush=True)
