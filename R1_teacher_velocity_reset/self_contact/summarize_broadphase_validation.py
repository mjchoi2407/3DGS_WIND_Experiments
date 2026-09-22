"""v5의 원본/hash·제한 프레임·동결 씬 검증을 집계한다. GPU 계산은 실행하지 않는다."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import numpy as np

from wind3dgs.evaluation.p3_gpu_contact_frozen_benchmark import verify_inputs, SHAPES


def read(path): return json.loads(path.read_text())
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def timing(values):
    median = float(np.median(values))
    return dict(median_s=median,min_s=min(values),max_s=max(values),
                spread_percent=100*(max(values)-min(values))/median,samples_s=values)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('old','new','benchmark','samples','out'):
        parser.add_argument('--'+name,type=Path,required=True)
    args = parser.parse_args()
    if args.out.exists(): raise FileExistsError(args.out)
    verify_inputs((args.old,args.new))
    measured = read(args.benchmark/'report.json')
    assert measured['status'] == 'passed' and measured['compare'] and measured['gpu_idle_confirmed']
    assert measured['input_manifest_sha256'] in {digest(root/'manifest.json') for root in (args.old,args.new)}
    for rel,sha in measured['source_sha256'].items():
        for base in (Path('code/wind3dgs'),args.benchmark/'runtime/wind3dgs',args.new/'runtime/wind3dgs'):
            assert digest(base/rel) == sha, str(base/rel)
    # v4 대조군이 원래 수치 구현을 공유하는지 검증한다. 변경한 접촉 orchestration은 명시적으로 제외한다.
    changed = []
    for old in sorted((args.old/'runtime/wind3dgs/teacher').glob('*.py')):
        new = args.new/'runtime/wind3dgs/teacher'/old.name
        if digest(old) != digest(new): changed.append(old.name)
    assert changed == ['gpu_shell_contact.py'], changed
    summary = dict(status='passed',gpu=measured['gpu'],repeats=measured['repeats'],
        old=str(args.old),new=str(args.new),benchmark=str(args.benchmark),samples=str(args.samples),
        old_manifest_sha256=digest(args.old/'manifest.json'),new_manifest_sha256=digest(args.new/'manifest.json'),
        benchmark_report_sha256=digest(args.benchmark/'report.json'),
        source_count=len(measured['source_sha256']),old_teacher_changed=changed,
        measured_frames=0,measured_substeps=0,components={},frames={},scene_smoke=[],
        full_scene_simulations_started=False)
    totals = np.zeros(2)
    for name,case in measured['cases'].items():
        row = {}
        for stage in ('bounds_bvh_query','evaluate','path'):
            rows = {lane:timing([sample for group in case['components'][lane][stage] for sample in group['samples_s']])
                    for lane in ('v4','split')}
            rows['reduction_percent'] = 100*(1-rows['split']['median_s']/rows['v4']['median_s'])
            row[stage] = rows
        row['extra_raw_bytes_solver_and_audit'] = 2*case['components']['split']['raw_bytes']
        summary['components'][name] = row
        frames = case.get('frames') or ({'local':case['frame']} if 'frame' in case else {})
        for phase,frame in frames.items():
            stem = name if phase == 'local' else name+'_'+phase
            path = args.benchmark/'states'/(stem+'.npz')
            assert digest(path) == frame['state_sha256']
            with np.load(path) as raw:
                reference = raw['v4_0']; errors = []
                for key in raw:
                    np.testing.assert_allclose(raw[key],reference,rtol=1e-7,atol=2e-9)
                    errors.append(np.max(np.abs(raw[key]-reference),axis=(1,2)))
            rows = {}
            for lane,data in frame['lanes'].items():
                for trial in data['rows']:
                    assert trial['flags'] == [0]
                    assert all(obs[6] == 0 for obs in trial['observations'])
                for key in ('graph_inventory','step_graph_inventory','audit_graph_inventory'):
                    assert data[key]['host_copies'] == data[key]['host_callbacks'] == 0
                rows[lane] = timing([r['compute_audit_s'] for r in data['rows']])
                rows[lane]['observations'] = data['rows'][0]['observations']
                summary['measured_frames'] += len(data['rows'])
                summary['measured_substeps'] += len(data['rows'])*(12 if name=='fast' else 8 if phase=='local' else 64)
            rows['reduction_percent'] = 100*(1-rows['split']['median_s']/rows['v4']['median_s'])
            rows['state_max_abs_difference'] = np.max(errors,axis=0).tolist()
            rows['state_sha256'] = digest(path)
            summary['frames'][stem] = rows
            if phase != 'local': totals += [rows[lane]['median_s'] for lane in ('v4','split')]
    summary['six_scene_median_sum_s'] = dict(zip(('v4','split'),totals.tolist()))
    summary['six_scene_reduction_percent'] = 100*(1-totals[1]/totals[0])
    for shape in SHAPES:
        assert not (args.new/shape/'outputs').exists()
        for phase in ('preload','wind'):
            rel = Path(shape)/'checks/smoke'/phase/'frame_0000.npz'
            new,old = args.new/rel,args.old/rel
            report = read(new.parent/'report.json'); assert report['status'] == 'complete'
            assert report['frames'][0]['state_sha256'] == digest(new)
            with np.load(new) as a,np.load(old) as b:
                errors = {}
                assert not a['flags'].any() and len(a['flags']) == 64
                np.testing.assert_array_equal(a['flags'],b['flags'])
                for key in ('u_hi','u_lo','v_hi','v_lo','held_force_n'):
                    np.testing.assert_allclose(a[key],b[key],rtol=1e-7,atol=2e-9)
                    errors[key] = float(np.max(np.abs(a[key]-b[key])))
            summary['scene_smoke'].append(dict(case=str(rel),max_abs_difference=errors,
                old_sha256=digest(old),new_sha256=digest(new)))
    strength = read(args.samples/'report.json')
    assert strength['passed'] and strength['source_sha256'] == measured['source_sha256']
    for case in strength['cases']:
        assert case['gpu_accepted'] and case['port_validation_passed']
        assert digest(args.samples/(case['name']+'.npz')) == case['raw_sha256']
    summary['strength_steps'] = sum(c['steps'] for c in strength['cases'])
    xml = ET.parse(args.benchmark/'regression.xml').getroot().find('testsuite')
    assert all(int(xml.attrib[k]) == 0 for k in ('failures','errors','skipped'))
    summary['regression'] = {k:xml.attrib[k] for k in ('tests','failures','errors','skipped','time')}
    args.out.mkdir(parents=True)
    for source,dest in ((args.benchmark/'report.json','comparison.json'),
                        (args.samples/'report.json','strength.json'),
                        (args.new/'suite.json','suite.json'),(args.new/'manifest.json','manifest.json')):
        shutil.copy2(source,args.out/dest)
    for report in sorted(args.new.glob('*/checks/smoke/**/report.json')):
        dest = args.out/'smoke'/report.relative_to(args.new)
        dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(report,dest)
    (args.out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(f'검산·원본 대조 완료: {summary["measured_frames"]}측정 프레임, {summary["measured_substeps"]}단계')


if __name__ == '__main__': main()
