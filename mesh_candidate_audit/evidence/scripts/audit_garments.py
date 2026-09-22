import pathlib,json,numpy as np,trimesh,sys,hashlib,struct
# Load only diagnostic helpers, without rerunning asset scans.
src=pathlib.Path(__file__).with_name('audit_mesh_candidates.py').read_text().split('results=[]')[0];exec(src)
base=ROOT/'berkeley_garments/BerkeleyGarmentLibrary';out=[]
for p in sorted((base/'Garments').glob('*/*/*.obj')):
 if p.stem.endswith(('-m','-w')):continue
 vv=[];ff=[];vt=[];refs=[];mtls=[]
 for line in p.read_text().splitlines():
  a=line.split()
  if not a:continue
  if a[0]=='v':vv.append(list(map(float,a[1:4])))
  if a[0]=='vt':vt.append(list(map(float,a[1:3])))
  if a[0]=='f':
   q=[int(x.split('/')[0])-1 for x in a[1:]]
   assert len(q)==3,(p,len(q))
   ff.append(q)
   refs.extend(int(x.split('/')[1])-1 for x in a[1:] if '/' in x and x.split('/')[1])
  if a[0]=='mtllib':mtls+=a[1:]
 m=trimesh.Trimesh(vv,ff,process=False);s=meshstats(m)
 s.update(file=str(p.relative_to(ROOT)),garment=p.parent.parent.name,resolution=p.parent.name,source_vertices=len(vv),reference_coordinates=len(vt),reference_indices_valid=bool(refs and min(refs)>=0 and max(refs)<len(vt)),mtllib=mtls)
 out.append(s)
 print(s['garment'],s['resolution'],s['faces'],s['components'],s['nonmanifold_edges'],s['degenerate_faces'],flush=True)
(OUT/'garment_structure.json').write_text(json.dumps(out,indent=2))
p=ROOT/'flag_simple';a=np.load(p/'first_trajectory.npz');v=np.column_stack([a['mesh_pos'][0],np.zeros(1579)]);m=trimesh.Trimesh(v,a['cells'][0],process=False);s=meshstats(m)
s.update(node_types={str(k):int(v) for k,v in zip(*np.unique(a['node_type'][0],return_counts=True))},world_frames=len(a['world_pos']),world_all_finite=bool(np.isfinite(a['world_pos']).all()),dt=.02)
# Independent TFRecord CRC32C verification, header and payload.
table=[]
for i in range(256):
 c=i
 for _ in range(8):c=(c>>1)^ (0x82F63B78 if c&1 else 0)
 table.append(c)
def masked_crc(b):
 c=0xffffffff
 for x in b:c=table[(c^x)&255]^(c>>8)
 c^=0xffffffff
 return (((c>>15)|(c<<17))+0xa282ead8)&0xffffffff
raw=(p/'valid_first_record.tfrecord').read_bytes()
assert masked_crc(raw[:8])==struct.unpack('<I',raw[8:12])[0]
assert masked_crc(raw[12:-4])==struct.unpack('<I',raw[-4:])[0]
s['tfrecord_crc32c_verified']=True
(OUT/'flag_structure.json').write_text(json.dumps(s,indent=2))
print('FlagSimple',s['faces'],s['components'],s['boundary_edges'],s['node_types'],flush=True)
