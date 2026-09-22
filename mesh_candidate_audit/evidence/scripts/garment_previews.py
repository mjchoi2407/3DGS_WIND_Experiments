import pathlib,trimesh,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
plt.rcParams['font.family']='Noto Sans CJK JP'
r=pathlib.Path('experiments/artifacts/datasets/mesh_candidates_20260912');b=r/'berkeley_garments/BerkeleyGarmentLibrary/Garments/tshirt/isotropic';a=np.load(r/'flag_simple/first_trajectory.npz')
ms=[trimesh.load(b/'tshirt-iso.obj',force='mesh',process=False),trimesh.load(b/'tshirt-iso-m.obj',force='mesh',process=False),trimesh.load(r/'flag_simple/rest.obj',force='mesh',process=False),trimesh.Trimesh(a['world_pos'][50],a['cells'][0],process=False)]
fig=plt.figure(figsize=(12,9))
for i,(m,t) in enumerate(zip(ms,['Berkeley 티셔츠: 제공된 공간 형상','Berkeley 티셔츠: 원단 기준 형상','FlagSimple: 평면 기준 메시','FlagSimple: 제공된 궤적의 50번 프레임'])):
 ax=fig.add_subplot(2,2,i+1,projection='3d');v=m.vertices;lo=v.min(0);hi=v.max(0);mid=(lo+hi)/2;rad=(hi-lo).max()/2
 ax.add_collection3d(Poly3DCollection(v[m.faces],facecolors='#96bed4',edgecolors='#315976',linewidths=.08,rasterized=True))
 ax.set(xlim=(mid[0]-rad,mid[0]+rad),ylim=(mid[1]-rad,mid[1]+rad),zlim=(mid[2]-rad,mid[2]+rad));ax.set_box_aspect([1,1,1]);ax.view_init(elev=15,azim=-70)
 if i in [1,2]:ax.view_init(elev=90,azim=-90)
 ax.set_title(t,fontsize=11);ax.set_axis_off()
fig.suptitle('실제 다운로드한 논문용 메시 · 구조 확인용 시각화',fontsize=15);fig.tight_layout();fig.savefig('experiments/mesh_candidate_audit/evidence/benchmark_preview.png',dpi=120)
