import numpy as np,json
from wind3dgs.evaluation.teacher_p3_shell_continuation import Bundle,P3Shell,SpatialComparison
from wind3dgs.evaluation.teacher_p3_shell_random_comparison import map_time
b=Bundle('experiments/artifacts/runs/teacher_p3_shell_random/scale4_fast_continuation_v2');names=['m16_s256_reset66','m32_s256_reset66'];models=[P3Shell(b.index(n)['config']['resolution']) for n in names];sp=SpatialComparison(*models)
for frame in [66,89]:
 traces=[b.frame(n,frame)[0] for n in names];square=np.zeros((257,3));mean_square=0.;diff_square=0.;u_square=np.zeros(257);spectrum=np.zeros(129)
 for A,B,w in sp.batches:
  dv=map_time(A,traces[0]['v_m_s'])-map_time(B,traces[1]['v_m_s']);du=map_time(A,traces[0]['u_m'])-map_time(B,traces[1]['u_m'])
  square+=np.einsum('p,tpc,tpc->tc',w,dv,dv);u_square+=np.einsum('p,tpc,tpc->t',w,du,du)
  avg=dv.mean(axis=0);mean_square+=np.einsum('p,pc,pc->',w,avg,avg)
  diff=np.diff(dv,axis=0);diff_square+=np.einsum('p,tpc,tpc->',w,diff,diff)/256
  # 마지막 중복 경계 제외. 1 frame FFT는 원인 확정이 아닌 주파수 진단이다.
  ft=np.fft.rfft(dv[:-1],axis=0)/256;spectrum+=np.einsum('p,fpc,fpc->f',w,ft.conj(),ft).real
 total=float(square.sum(axis=1).mean());spectrum[1:-1]*=2;freq=np.fft.rfftfreq(256,1/(60*256));order=np.argsort(spectrum)[-5:][::-1]
 print(json.dumps({'frame':frame,'peak_velocity_error_m_s':float(np.sqrt(square.sum(axis=1).max()/sp.area_m2)),'component_rms_time_m_s':np.sqrt(square.mean(axis=0)/sp.area_m2).tolist(),'mean_field_energy_fraction':mean_square/total,'adjacent_difference_over_error_rms':float(np.sqrt(diff_square/total)),'peak_displacement_error_m':float(np.sqrt(u_square.max()/sp.area_m2)),'fft_energy_fraction_above_600hz':float(spectrum[freq>=600].sum()/spectrum.sum()),'fft_top_hz_fraction':[(float(freq[i]),float(spectrum[i]/spectrum.sum())) for i in order]}),flush=True)
