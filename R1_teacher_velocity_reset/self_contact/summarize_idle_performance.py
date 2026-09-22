"""유휴 조건 접촉 성능 재측정의 분모·변동·검산·동결 버전 차이를 집계한다."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np


def read(path): return json.loads(path.read_text())
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(rows):
    values = np.array([r['compute_audit_s'] for r in rows if not r.get('warmup',False)])
    return dict(samples_s=values.tolist(),median_s=float(np.median(values)),minimum_s=float(values.min()),
        maximum_s=float(values.max()),range_over_median=float(np.ptp(values)/np.median(values)))


def inventories(value):
    if isinstance(value,dict):
        if 'host_copies' in value:
            assert value['host_copies'] == value['host_callbacks'] == 0
        for item in value.values(): inventories(item)
    elif isinstance(value,list):
        for item in value: inventories(item)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--controlled',type=Path,required=True)
    parser.add_argument('--frozen',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if (args.out/'summary.json').exists(): raise FileExistsError(args.out/'summary.json')
    a,b=[read(p/'report.json') for p in (args.controlled,args.frozen)]
    assert a['status'] == b['status'] == 'passed'
    inventories(a)
    frames=[]; contacts=[]; count=0; substeps=0
    for case,value in a['cases'].items():
        rows=value.get('frames',{'contact':value.get('frame')})
        for phase,row in rows.items():
            if row is None: continue
            lanes={name:stats(v['rows']) for name,v in row['lanes'].items()}
            target=contacts if phase == 'contact' else frames
            ref,new,reuse=[lanes[k]['median_s'] for k in ('old_on','new_on','reuse_on')]
            target.append(dict(case=case,phase=phase,lanes=lanes,old_to_new_time_reduction=1-new/ref,
                parallel_time_reduction=1-new/reuse,
                matched_off_extra_fraction=new/lanes['matched_off']['median_s']-1 if 'matched_off' in lanes else None))
            for lane,details in row['lanes'].items():
                for item in details['rows']:
                    assert item['flags'] == [0]
                    if phase != 'contact' and lane != 'matched_off':
                        assert all(obs[1] == 0 for obs in item['evaluations'])
                    count+=1; substeps+=64 if phase != 'contact' else 12 if case == 'fast' else 8
    frozen=[]
    for case,row in b['cases'].items():
        lanes={name:stats(v['rows']) for name,v in row['versions'].items()}
        frozen.append(dict(case=case,lanes=lanes,speedup=row['speedup'],
            time_reduction=1-lanes['v4']['median_s']/lanes['v1']['median_s'],
            max_abs_state_difference=row['max_abs_state_difference']))
        for version in ('v1','v4'):
            r=read(args.frozen/version/case/'report.json'); inventories(r)
            assert r['status'] == 'passed'
            for item in r['rows']:
                assert item['flags'] == [0] and item['contact_status'] == item['contact_path_status'] == 0
    with (args.out/'gpu_telemetry.csv').open() as stream:
        telemetry=[r for r in csv.DictReader(stream,skipinitialspace=True) if r.get('temperature.gpu')]
    numeric={}
    for key in ('clocks.current.sm [MHz]','clocks.current.memory [MHz]','power.draw [W]','temperature.gpu'):
        vals=[float(r[key].strip().split()[0]) for r in telemetry if r.get(key)]
        numeric[key]=dict(min=min(vals),median=float(np.median(vals)),max=max(vals))
    result=dict(status='passed',measurement_condition='사용자가 다른 GPU 작업 종료를 확인; WSL 드라이버 비영 대기 사용률은 별도 기록',
        gpu=a['gpu'],controlled_report_sha256=digest(args.controlled/'report.json'),
        frozen_report_sha256=digest(args.frozen/'report.json'),telemetry_sha256=digest(args.out/'gpu_telemetry.csv'),
        telemetry_samples=len(telemetry),telemetry_ranges=numeric,controlled_scene_frames=frames,
        active_contact_cases=contacts,actual_frozen_versions=frozen,
        controlled_measured_frames=count,controlled_measured_substeps=substeps,
        frozen_measured_frames=6*2*b['repeats'],frozen_measured_substeps=6*2*b['repeats']*64,
        warmup_excluded=True,full_simulations_started=False,
        interpretation='짧은 초기/국소 표본의 중앙값. v4 병렬화의 추가 이득은 변동 폭과 비교하며 장기/고밀도 접촉에 외삽하지 않음')
    for src,name in ((args.controlled/'report.json','controlled_report.json'),(args.frozen/'report.json','frozen_report.json')):
        target=args.out/name
        if target.exists(): raise FileExistsError(target)
        shutil.copy2(src,target)
    for path in sorted(args.frozen.glob('v*/*/*/report.json')):
        dest=args.out/'frozen'/path.relative_to(args.frozen); dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,dest)
    (args.out/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('유휴 조건의 동결 버전·통제된 ON/OFF·실접촉 비교 집계 완료')


if __name__ == '__main__': main()
