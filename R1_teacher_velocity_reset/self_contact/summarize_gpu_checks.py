"""완료한 GPU 원시 결과·hash를 검증하고 작은 보고서와 강도 비교 그림을 보존한다."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenes',type=Path,required=True)
    parser.add_argument('--samples',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args(); args.out.mkdir(parents=True,exist_ok=False)
    cfg = read(args.scenes/'suite.json'); manifest = read(args.scenes/'manifest.json')
    for name,sha in manifest.items():
        if digest(args.scenes/name) != sha: raise ValueError('동결 씬 hash 불일치: '+name)
    strength = read(args.samples/'report.json')
    if not strength['passed']: raise ValueError('GPU 이식 대조 실패 결과')
    # 실행 당시 source를 현재 code와 대조한 뒤 보존한다. 나중에 추측해 복원하지 않는다.
    for name,sha in strength['source_sha256'].items():
        source = Path('code/wind3dgs')/name
        if digest(source) != sha: raise ValueError('실행 후 source 변경: '+name)
        target = args.samples/'source/wind3dgs'/name
        target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target)
    for name in ('report.json',): shutil.copy2(args.samples/name,args.out/('strength_'+name))
    for name in ('manifest.json','suite.json','reference_inputs.json'):
        shutil.copy2(args.scenes/name,args.out/('scenes_'+name))
    files = {}
    for path in sorted(args.scenes.rglob('*')):
        if path.is_file() and ('checks' in path.parts or path.suffix == '.log'):
            files[str(path.relative_to(args.scenes))] = digest(path)
            if path.suffix == '.json':
                target=args.out/'scenes'/path.relative_to(args.scenes)
                target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(path,target)
    for case in strength['cases']:
        source = args.samples/(case['name']+'.npz')
        if digest(source) != case['raw_sha256']: raise ValueError('표본 raw hash 불일치')
        shutil.copy2(source,args.out/source.name)
    summary = dict(schema='gpu_contact_evidence_v1',scenes=str(args.scenes),samples=str(args.samples),
        scenes_output_sha256=files,source_strength_report_sha256=digest(args.samples/'report.json'),
        source_scenes_manifest_sha256=digest(args.scenes/'manifest.json'),
        all_frames_passed=True,verified_frames=0,verified_substeps=0,full_scene_simulations_started=False)
    for shape in cfg['shapes']:
        for phase in ('preload','wind'):
            report = read(args.scenes/shape/'checks/smoke'/phase/'report.json')
            summary['all_frames_passed'] &= report['status'] == 'complete'
            for frame in report['frames']:
                summary['verified_frames'] += 1
                with np.load(args.scenes/shape/'checks/smoke'/phase/f'frame_{frame["frame"]:04d}.npz') as z:
                    if np.any(z['flags']): raise ValueError('씬 GPU flags 오류')
                    summary['verified_substeps'] += len(z['flags'])
    (args.out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.family'] = 'Noto Sans CJK JP'
    fig,axes = plt.subplots(1,3,figsize=(12,3.8))
    for ax,name,title in zip(axes,('face','edge','fast'),('면 접근 0.2m/s','엣지 접근 0.2m/s','고속 접근 1m/s')):
        for stiffness in (1000,10000):
            with np.load(args.samples/f'{name}_k{stiffness}.npz') as z:
                line,=ax.plot(z['time_s']*1000,z['signed_mean_gap_m']*1000,label=f'k={stiffness:,}')
                key='coarse_geometry_flags' if 'coarse_geometry_flags' in z else 'flags'
                failed=np.flatnonzero(z[key])+1
                ax.scatter(z['time_s'][failed]*1000,z['signed_mean_gap_m'][failed]*1000,
                           marker='x',color=line.get_color(),s=32)
        ax.axhline(1,color='gray',ls=':',label='시험 최소 간격 1mm')
        ax.set(title=title,xlabel='시간 (ms)',ylabel='평균 층 간격 (mm)'); ax.legend(fontsize=8)
    fig.suptitle('GPU barrier 비교: ×는 기존 scalar 기하 충분조건의 미인증 단계',fontsize=12)
    fig.tight_layout(); fig.savefig(args.out/'strength_comparison.png',dpi=170)
    fig.savefig(args.out/'strength_comparison.svg'); plt.close(fig)
    print(f'GPU 근거 집계 완료: {summary["verified_frames"]}프레임 / {summary["verified_substeps"]}단계',flush=True)


if __name__ == '__main__': main()
