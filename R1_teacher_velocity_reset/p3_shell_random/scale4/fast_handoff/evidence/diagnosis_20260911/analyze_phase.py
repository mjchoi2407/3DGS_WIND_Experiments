import json,numpy as np
from wind3dgs.evaluation.teacher_p3_shell_continuation import Bundle,P3Shell
b=Bundle('experiments/artifacts/runs/teacher_p3_shell_random/scale4_fast_continuation_v2');names=['m16_s256_reset66','m32_s256_reset66'];points=np.array([(x,y) for x in [.5,.75,1.] for y in [.25,.5,.75]]);signals=[]
for name in names:
 model=P3Shell(b.index(name)['config']['resolution']);A=model.moving_surface_map(points);chunks=[]
 for frame in range(72,90):
  z,_=b.frame(name,frame);chunks.append((A@z['v_m_s'][:-1,:,1].T).T)
 signals.append(np.concatenate(chunks));print(name,'선택 위치의 무풍 구간 신호 확인 완료',flush=True)
x=np.linspace(-1,1,len(signals[0]));P=np.polynomial.polynomial.polyvander(x,3);window=np.hanning(len(x));freq=np.fft.rfftfreq(len(x),1/(60*256));results=[];transforms=[]
for name,v in zip(names,signals):
 v=v-P@np.linalg.lstsq(P,v,rcond=None)[0];F=np.fft.rfft(window[:,None]*v,axis=0);transforms.append(F);power=np.sum(abs(F)**2,axis=1);power[freq<60]=0;order=np.argsort(power)[-5:][::-1];results.append({'name':name,'top_high_frequency_bins_hz':freq[order].tolist(),'fractions_within_high_band':(power[order]/power.sum()).tolist()})
difference=np.sum(abs(transforms[0]-transforms[1])**2,axis=1);difference[freq<60]=0;j=int(np.argmax(difference));a=transforms[0][j];c=transforms[1][j];cross=np.vdot(c,a);r={'scope':'주변 풍속 0인 frame72–89, 고정 물리 위치 9개 수직 속도 진단. 공간 RMS/고유모드 인증 아님. 3차 추세 제거와 Hann 창 사용.','points_xy':points.tolist(),'frequency_spacing_hz':float(freq[1]),'individual':results,'largest_difference_bin_hz':float(freq[j]),'amplitude_norm_ratio_n16_n32':float(np.linalg.norm(a)/np.linalg.norm(c)),'spatial_complex_coherence':float(abs(cross)/(np.linalg.norm(a)*np.linalg.norm(c))),'phase_difference_degrees':float(np.degrees(np.angle(cross)))};print(json.dumps(r,ensure_ascii=False,indent=2));open('/tmp/wind3dgs_reset_phase_probe.json','w').write(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
