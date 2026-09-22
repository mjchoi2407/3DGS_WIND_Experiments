import pathlib,json,numpy as np,trimesh,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.family']='Noto Sans CJK JP'
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from PIL import Image
ROOT=pathlib.Path('experiments/artifacts/datasets/mesh_candidates_20260912');OUT=pathlib.Path('experiments/mesh_candidate_audit/evidence')
assets=['calathea_orbifolia_01','anthurium_botany_01','potted_plant_02','pachira_aquatica_01','flower_heliophila']
fig=plt.figure(figsize=(15,10),facecolor='white')
for i,a in enumerate(assets):
 s=trimesh.load_scene(ROOT/a/(a+'_4k.gltf'),process=False)
 gs=list(s.geometry.values())
 if a=='potted_plant_02':m=next(g for g in gs if 'leaves' in g.visual.material.name)
 elif a=='pachira_aquatica_01':m=next(g for g in gs if 'leaves' in g.visual.material.name)
 else:m=gs[0]
 v,inv=np.unique(m.vertices,axis=0,return_inverse=True);f=inv[m.faces];e=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1)
 n,l=connected_components(coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(len(v),len(v))).tocsr(),directed=False)
 colors=plt.get_cmap('tab20')((l[f[:,0]]%20)/19);colors[:,3]=.95
 ax=fig.add_subplot(2,3,i+1,projection='3d');ax.add_collection3d(Poly3DCollection(v[f],facecolors=colors,edgecolors='none',rasterized=True))
 lo=v.min(0);hi=v.max(0);mid=(lo+hi)/2;r=(hi-lo).max()/2
 ax.set(xlim=(mid[0]-r,mid[0]+r),ylim=(mid[1]-r,mid[1]+r),zlim=(mid[2]-r,mid[2]+r));ax.set_box_aspect([1,1,1]);ax.view_init(elev=15,azim=-65,vertical_axis='y');ax.set_axis_off();ax.set_title(a+'\n'+str(n)+'개 연결 조각 (대표 메시 1개)',fontsize=10)
ax=fig.add_subplot(2,3,6)
p=ROOT/'calathea_orbifolia_01/textures';im=np.array(Image.open(p/'calathea_orbifolia_01_diff_4k.jpg'));a=np.array(Image.open(p/'calathea_orbifolia_01_alpha_4k.png')).astype(float)/65535
rgba=np.dstack([im,(a*255).astype('uint8')]);ax.imshow(rgba);ax.set_title('Calathea: 원본 색상 + 투명도 텍스처',fontsize=10);ax.axis('off')
fig.suptitle('다운로드 메시 구조 검사 — 색상은 연결 조각을 구분\n구조 확인용 시각화 · 시뮬레이션 및 최종 렌더링 아님',fontsize=14)
fig.tight_layout();fig.savefig(OUT/'structure_preview.png',dpi=120);plt.close(fig)
