"""기존 동결 코드를 보존 복사하고 고른 삼각 깃발의 0.1초 별도 입력을 준비한다."""
import copy
from pathlib import Path
import shutil

import numpy as np
from wind3dgs.evaluation.teacher_three_scene_run import digest, verify, write
from wind3dgs.teacher.sample_meshes import make_triangular_flag, write_sample_npz

source = Path('experiments/artifacts/runs/teacher_timestep_search/20260912_three_scenes_10s_v4')
target = source.parent / '20260912_triangle_regular_01s_v1'
old = verify(source)
if target.exists():
    raise FileExistsError('기존 실행은 덮어쓰지 않습니다: '+str(target))
target.mkdir()
(target/'inputs').mkdir()
for path in sorted((source/'runtime').rglob('*.py')):
    destination = target/path.relative_to(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)
shutil.copy2(source/'inputs/wind.npz', target/'inputs/wind.npz')
with np.load(source/'inputs/triangular_flag.npz', allow_pickle=False) as z:
    original = z['vertices'].copy()
    old_pins = z['pinned'].copy()
mesh = make_triangular_flag(width_m=1.2, height_m=.75, resolution=(24, 16))
np.testing.assert_array_equal(original.min(axis=0), mesh.vertices.min(axis=0))
np.testing.assert_array_equal(original.max(axis=0), mesh.vertices.max(axis=0))
np.testing.assert_array_equal(original[old_pins].min(axis=0), mesh.vertices[mesh.pinned].min(axis=0))
np.testing.assert_array_equal(original[old_pins].max(axis=0), mesh.vertices[mesh.pinned].max(axis=0))
assert np.all(mesh.vertices[mesh.pinned, 0] == 0)
write_sample_npz(mesh, target/'inputs/triangular_flag.npz')
plan = copy.deepcopy(old)
plan.update(shapes=['triangular_flag'], frames=6,
            scene_budget_s={'triangular_flag': old['scene_budget_s']['triangular_flag']})
assert {k: v for k, v in plan.items() if k not in ('shapes','frames','scene_budget_s')} == {
    k: v for k, v in old.items() if k not in ('shapes','frames','scene_budget_s')}
write(target/'plan.json', plan)
files = [target/'plan.json', *sorted((target/'inputs').iterdir()), *sorted((target/'runtime').rglob('*.py'))]
write(target/'manifest.json', {str(p.relative_to(target)): digest(p) for p in files})
provenance = {'source': str(source), 'source_manifest_sha256': digest(source/'manifest.json'),
              'original_mesh_sha256': digest(source/'inputs/triangular_flag.npz'),
              'new_mesh_sha256': digest(target/'inputs/triangular_flag.npz'),
              'generator_sha256': digest(target/'runtime/code/wind3dgs/teacher/sample_meshes.py'),
              'preparation_script_sha256': digest(Path(__file__)),
              'same_bounds_and_fixed_edge': True, 'same_physics_wind_dt_tolerances': True,
              'initial_state': 'rest에서 시작; 기존 궤적을 전송하지 않음',
              'scope': '6프레임·384단계·0.1초 개발 검증, 10초 채택 아님'}
write(target/'input_change.json', provenance)
verify(target)
print('고른 삼각 깃발 0.1초 동결 준비 완료: '+str(target))
