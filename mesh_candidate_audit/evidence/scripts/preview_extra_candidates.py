import pathlib,json,numpy as np,trimesh,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.family']='Noto Sans CJK JP'
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from PIL import Image
ROOT=pathlib.Path('experiments/artifacts/datasets/mesh_candidates_20260912');OUT=pathlib.Path('experiments/mesh_candidate_audit/evidence')
assets=['grass_medium_01','fern_02','celandine_01']
ROOT=pathlib.Path('experiments/artifacts/datasets/mesh_candidates_extra_20260912')
OUT=pathlib.Path('experiments/mesh_candidate_audit/evidence/extra')
fig=plt.figure(figsize=(12,12),facecolor='white')
for i,a in enumerate(assets):
 s=trimesh.load_scene(ROOT/a/(a+'_4k.gltf'),process=False)
 name={'grass_medium_01':'Plane.056','fern_02':'Plane.006','celandine_01':'Plane.010'}[a]
 m=s.geometry[name];v=np.asarray(m.vertices);f=np.asarray(m.faces)
 ax=fig.add_subplot(3,2,2*i+1,projection='3d')
 ax.add_collection3d(Poly3DCollection(v[f],facecolors='#77aa66',edgecolors='#334433',linewidths=.25,rasterized=True))
 lo=v.min(0);hi=v.max(0);mid=(lo+hi)/2;r=(hi-lo).max()/2
 ax.set(xlim=(mid[0]-r,mid[0]+r),ylim=(mid[1]-r,mid[1]+r),zlim=(mid[2]-r,mid[2]+r));ax.set_box_aspect([1,1,1]);ax.view_init(elev=25,azim=-65,vertical_axis='y');ax.set_axis_off();ax.set_title(a+' / '+name+' / '+str(len(f))+'면')
 ax=fig.add_subplot(3,2,2*i+2)
 d=ROOT/a/'textures';rgb=np.asarray(Image.open(d/(a+'_diff_4k.jpg')));alpha=np.asarray(Image.open(d/(a+'_alpha_4k.png')))
 alpha=(alpha.astype(float)/(65535 if alpha.dtype.itemsize>1 else 255)*255).astype('uint8')
 ax.imshow(np.dstack([rgb,alpha]));ax.axis('off');ax.set_title('원본 색상 + 별도 알파 (텍스처 지도)')
fig.suptitle('추가 후보: 실제 삼각형과 보이는 윤곽 비교\n대표 기하 · 물리 실행 및 최종 렌더링 아님')
fig.tight_layout();fig.savefig(OUT/'preview.png',dpi=130);plt.close(fig)
