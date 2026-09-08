"""20260908_sample_v1의 원본 연결·inventory 검산과 고정 3사례 그림을 재현한다."""
from pathlib import Path
import hashlib
import json

import numpy as np

from wind3dgs.teacher.sample_dataset import TeacherSampleDataset
from wind3dgs.teacher.trajectory_io import _json_load

WORKSPACE=Path(__file__).resolve().parents[3]
RUN=WORKSPACE/'experiments/artifacts/runs/teacher_sample_dataset/20260908_sample_v1'
DATASET=WORKSPACE/'experiments/artifacts/datasets/teacher_samples/20260908_sample_v1'
EVIDENCE=Path(__file__).resolve().parent


def main():
    data=TeacherSampleDataset.open(DATASET,allow_development=True)
    manifest=_json_load((RUN/'manifest.json').read_bytes())
    environment=_json_load((RUN/'environment.json').read_bytes())
    report=_json_load((RUN/'report.json').read_bytes())
    assert manifest['status']=='completed' and report['status']=='passed'
    assert manifest['dataset_sha256_or_manifest_version']==data.manifest['manifest_sha256']==report['dataset_manifest_sha256']
    actual={str(p.relative_to(RUN)) for p in RUN.rglob('*') if p.is_file() and p!=RUN/'manifest.json'}
    assert actual==set(manifest['outputs'])
    for name,entry in manifest['outputs'].items():
        p=RUN/name
        assert p.stat().st_size==entry['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256']
    for name,digest in environment['sources_sha256'].items():
        assert hashlib.sha256((WORKSPACE/'code'/name).read_bytes()).hexdigest()==digest
    sources={c['case_id']:(RUN/c['case_id']/'raw',RUN/c['case_id']/'probe') for c in data.manifest['cases']}
    source_check=data.verify_sources(sources)
    batches=list(data.iter_batches(4))
    assert [len(b['sample_ids']) for b in batches]==[4,4,4,3]
    assert all(c['replay']['passed'] and max(c['replay']['max_absolute_errors'].values())==0. for c in report['cases'])
    verification={'status':'passed','source_check':source_check,'sample_count':15,'batch_sizes':[4,4,4,3],
        'dataset_manifest_sha256':data.manifest['manifest_sha256'],'run_inventory_files':len(actual),
        'run_inventory_bytes':sum(v['bytes'] for v in manifest['outputs'].values()),
        'dataset_files_including_manifest':len(list(DATASET.iterdir())),
        'dataset_bytes_including_manifest':sum(p.stat().st_size for p in DATASET.iterdir()),
        'producer_source_files':len(environment['sources_sha256']),'all_three_cpu_replays_max_error':0.,
        'training_eligible':False,'physical_acceptance':'not_assessed'}
    (EVIDENCE/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.family']='Noto Sans CJK JP'
    plt.rcParams['axes.unicode_minus']=False
    fig,axes=plt.subplots(3,3,figsize=(11,7),sharex=True,layout='constrained')
    titles={'wind_pulse':'바람 펄스','step_on_off':'바람 켜짐 / 꺼짐','aero_off_decay':'공력 off 자유감쇠'}
    ids=[b['sample_ids'] for b in batches];assert sum(map(len,ids))==15
    tip=int(np.flatnonzero(np.all(data.static['rest_positions_m']==[1.,0.,0.],axis=1))[0])
    for row,case in enumerate(data.manifest['cases']):
        windows=[]
        for sample in data.manifest['samples']:
            if sample['case_id']==case['case_id']:
                with np.load(DATASET/sample['file'],allow_pickle=False) as values:windows.append({k:values[k] for k in values.files})
        times=np.concatenate([w['time_s'] if i==0 else w['time_s'][1:] for i,w in enumerate(windows)])
        u=np.concatenate([w['rest_displacements_m'] if i==0 else w['rest_displacements_m'][1:] for i,w in enumerate(windows)])
        v=np.concatenate([w['velocities_m_s'] if i==0 else w['velocities_m_s'][1:] for i,w in enumerate(windows)])
        wind=np.concatenate([w['air_velocity_m_s'] for w in windows])
        axes[row,0].step(times[:-1],wind[:,1],where='post',color='#267dba')
        axes[row,1].plot(times,u[:,tip,1]*1000,color='#b14b26')
        axes[row,2].plot(times,v[:,tip,1],color='#308454')
        axes[row,0].set_ylabel(titles[case['case_id']])
        for col in range(3):axes[row,col].grid(alpha=.25);axes[row,col].axhline(0,color='grey',lw=.5)
    for ax,title in zip(axes[0],('주변 바람 Y [m/s]','끝점 변위 Y [mm]','끝점 속도 Y [m/s]')):ax.set_title(title)
    for ax in axes[-1]:ax.set_xlabel('시각 [s]')
    fig.suptitle('Teacher 개발용 샘플 — 물리 수렴·본 학습용 채택은 미완료',fontsize=13)
    fig.savefig(EVIDENCE/'sample_response.png',dpi=160);plt.close(fig)
    print(json.dumps(verification,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
