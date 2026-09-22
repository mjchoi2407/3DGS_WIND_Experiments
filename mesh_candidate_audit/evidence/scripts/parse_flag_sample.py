import pathlib,struct,json,numpy as np,sys
root=pathlib.Path('experiments/artifacts/datasets/mesh_candidates_20260912');p=root/'flag_simple'
def varint(b,i):
 v=0;s=0
 while True:
  x=b[i];i+=1;v|=(x&127)<<s
  if x<128:return v,i
  s+=7
  assert s<70

def fields(b):
 i=0
 while i<len(b):
  key,i=varint(b,i);tag,wt=key>>3,key&7
  if wt==2:
   n,i=varint(b,i);x=b[i:i+n];i+=n
  elif wt==0:x,i=varint(b,i)
  elif wt==5:x=b[i:i+4];i+=4
  elif wt==1:x=b[i:i+8];i+=8
  else:raise ValueError(wt)
  yield tag,x
raw=(p/'valid_first_record.tfrecord').read_bytes();n=struct.unpack('<Q',raw[:8])[0];meta=json.loads((root/'flag_meta.txt').read_text())
# tf.train.Example -> Features map -> Feature -> BytesList
example=dict(fields(raw[12:12+n]));arrays={}
for tag,entry in fields(example[1]):
 d=dict(fields(entry));key=d[1].decode();feature=dict(fields(d[2]));blist=[x for t,x in fields(feature[1]) if t==1]
 spec=meta['features'][key];a=np.frombuffer(b''.join(blist),dtype=spec['dtype']).reshape(spec['shape']);arrays[key]=a
np.savez_compressed(p/'first_trajectory.npz',**arrays)
v=np.column_stack([arrays['mesh_pos'][0],np.zeros(len(arrays['mesh_pos'][0]))]);f=arrays['cells'][0]
with (p/'rest.obj').open('w') as out:
 for xyz in v:out.write('v '+' '.join(map(str,xyz))+'\n')
 for xy in arrays['mesh_pos'][0]:out.write('vt '+' '.join(map(str,xy))+'\n')
 for abc in f+1:out.write('f '+' '.join(f'{i}/{i}' for i in abc)+'\n')
print({k:list(v.shape) for k,v in arrays.items()});print('node types',np.unique(arrays['node_type'],return_counts=True))
