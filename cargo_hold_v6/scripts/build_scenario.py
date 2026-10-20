"""One scenario source for Gazebo replay and all rendered POVs.
Explicitly kinematic: pose trajectory, no force/contact or autonomous planning claim.
"""
from pathlib import Path
import json,math,copy
import numpy as np
from kinematics import fk
R=Path(__file__).resolve().parents[1]
FIXED=[]
for x in [3.40,4.15]:
 for y in [-.72,-.24,.24,.72]:
  for k in range(3):FIXED.append(dict(name=f'stored_{len(FIXED)+1:02d}',pose=[x,y,.13+.26*k,0],color=len(FIXED)%7))
for y in [-.62,.62]:FIXED.append(dict(name=f'stored_{len(FIXED)+1:02d}',pose=[2.6,y,.13,0],color=len(FIXED)%7))
states=[];q={};base=[1,-2.60,0,math.pi/2];bags={};held=None;rel=.161;feeder=4.2;bridge=0.;time=0
loaded=0;unloaded=0;stage='ENTRY'
def axes(bed):return dict(lift_height_joint=max(0.,bed-.366),head_z_joint=min(0.,(bed-.366)/2))
def add(label,dt=2):
 global time
 time+=dt
 if states:
  b=states[-1]['base'];dx,dy=base[0]-b[0],base[1]-b[1];a=(base[3]+b[3])/2;da=base[3]-b[3];ux=math.cos(a)*dx+math.sin(a)*dy;uy=-math.sin(a)*dx+math.cos(a)*dy
  for tag,v in zip(['fl','fr','rl','rr'],[(ux-uy-.65*da)/.075,(ux+uy+.65*da)/.075,(ux+uy-.65*da)/.075,(ux-uy+.65*da)/.075]):q[tag+'_wheel_joint']=q.get(tag+'_wheel_joint',0)+v
 if held:
  t=fk(q,base)['jaw_frame_link'];p=t@np.array([.34,0,rel,1]);bags[held]=list(p[:3])+[base[3]+q.get('conveyor_yaw_joint',0)]
 states.append(dict(t=time,q=q.copy(),base=base.copy(),bags=copy.deepcopy(bags),held=dict(name=held,rel=rel) if held else None,feeder_x=feeder,bridge_x=bridge,label=label,stage=stage,loaded=loaded,unloaded=unloaded))
add('Jembatan servis rata lantai; conveyor diparkir di samping',0)
add('Persiapan masuk: kepala tersimpan, pintu terbuka',3)
base[1]=0;add('Robot masuk melalui pintu samping ke area putar',15)
bridge=-4.;add('Platform servis keluar dari jalur conveyor setelah robot masuk',8)
feeder=1;add('Conveyor bergerak ke pintu setelah robot masuk',8)
base[1]=-.53;add('Dock penerimaan, robot menghadap +Y',5)
order=[(-.62,1),(-.62,2),(.62,1),(.62,2)]
for i,(y,k) in enumerate(order):
 stage='LOADING';n=f'active_{i+1}';bed=k*.26+.021
 q.update(support_blade_joint=0,jaw_lift_joint=0,left_jaw_joint=0,right_jaw_joint=0,head_z_joint=0,lift_height_joint=0,extension_joint=0)
 bags[n]=[1,-1.78,.496,math.pi/2];add(f'Loading {i+1}/4: koper datang dari conveyor luar',2)
 bags[n]=[1,-.03,.496,math.pi/2];add('Koper melewati portal terbuka ke posisi jepit',14)
 q.update(left_jaw_joint=.120,right_jaw_joint=.120);held=n;rel=.161;add('Jepit koper dan pastikan ditopang pelat',3)
 base[1]=0;add('Keluar dari docking ke pusat area putar',6)
 base[3]=0;add('Putar seluruh base 90 derajat ke arah +X',12)
 base[1]=y;add('Mecanum menggeser robot ke lajur tumpukan',7)
 base[0]=1.39;add('Maju ke standoff tumpukan',5)
 # All approaches to an occupied base layer keep the payload above it.
 q.update(axes(max(.366,bed)));add('Set tinggi angkut sebelum pendekatan terakhir',4)
 base[0]=1.66;add('Creep lurus menuju tumpukan; tidak berputar',7)
 q['extension_joint']=.44;add('Julurkan kepala di atas lapisan yang sudah ada',5)
 q.update(axes(bed));add(f'Setarakan dengan lapisan ke-{k+1}',4)
 q['support_blade_joint']=-.56;add('Tarik pelat; rahang tetap menopang koper',5)
 held=None;q.update(left_jaw_joint=0,right_jaw_joint=0);add('Buka rahang setelah area tumpuan terkonfirmasi',2)
 bags[n]=[2.6,y,k*.26+.13,0];loaded+=1;add('Koper menetap pada tumpukan; tanpa platform tambahan',1)
 q.update(head_z_joint=0);add('Kepala bebas, pertahankan lift sampai retract selesai',4)
 q['extension_joint']=0;add('Retract kepala transfer',4)
 base[0]=1.39;add('Mundur dari tumpukan',5)
 q['lift_height_joint']=0;base[0]=1;add('Turunkan lift setelah bebas tumpukan, kembali ke area putar',4)
 base[1]=0;add('Kembali ke sumbu tengah',6)
 base[3]=math.pi/2;add('Putar base menghadap conveyor samping',9)
 base[1]=-.53;add('Dock untuk siklus berikutnya',5)
 q['support_blade_joint']=0;add('Pulihkan pelat dan cek jalur masuk terbuka',2)
stage='FULL';add('Bagasi terisi: 30 koper, area putar dan jalur kerja tetap bebas',12)
for ii in reversed(range(4)):
 stage='UNLOADING';y,k=order[ii];n=f'active_{ii+1}';bed=k*.26+.021
 q.update(support_blade_joint=-.56,jaw_lift_joint=0,left_jaw_joint=0,right_jaw_joint=0)
 base[1]=0;add(f'Unloading {unloaded+1}/4: keluar dock',6)
 base[3]=0;add('Putar base ke tumpukan sebelum masuk lajur',9)
 base[1]=y;add('Geser ke lajur pengambilan',7)
 base[0]=1.39;add('Dekati standoff',5)
 q.update(axes(max(.366,bed)));add('Atur tinggi sebelum mendekati koper teratas',4)
 base[0]=1.66;add('Creep mendekat, pelat sudah ditarik',7)
 q['extension_joint']=.44;add('Julurkan rahang terbuka',5)
 q.update(axes(bed));add('Sejajarkan rahang pada sisi koper',4)
 q.update(left_jaw_joint=.120,right_jaw_joint=.120);held=n;rel=.140;add('Jepit koper teratas pada kedua sisi',3)
 q['jaw_lift_joint']=.035;add('Micro-lift 35 mm membuka celah di bawah koper',4)
 q['support_blade_joint']=0;add('Sisipkan pelat penopang ke celah',5)
 q['jaw_lift_joint']=.021;add('Turunkan berat koper ke pelat',2)
 q.update(axes(max(.366,k*.26+.071)));add('Angkat bebas dari lapisan bawah',4)
 q['extension_joint']=0;add('Retract koper ke robot',5)
 base[0]=1.39;add('Mundur sebelum menurunkan beban',7)
 q.update(head_z_joint=0,lift_height_joint=0);add('Turunkan ke posisi angkut rendah',5)
 base[0]=1;add('Kembali ke area putar',5)
 base[1]=0;add('Geser ke pusat area putar',7)
 base[3]=math.pi/2;add('Putar berbeban menuju conveyor samping',12)
 base[1]=-.53;add('Dock tepat di pintu',6)
 held=None;q.update(left_jaw_joint=0,right_jaw_joint=0,jaw_lift_joint=0);add('Buka rahang; aktifkan belt reverse setelah berhenti',3)
 bags[n]=[1,-1.78,.496,math.pi/2];add('Koper keluar melalui jalur portal yang sama',14)
 # Continue down the external inclined conveyor before removing the bag from scene.
 bags[n]=[1,-1.78,.496,math.pi/2];add('Serah-terima di batas conveyor luar; conveyor hulu di luar skenario',5)
 del bags[n];unloaded+=1;add('Koper diterima di luar pesawat',2)
stage='EXIT';base[1]=0;add('Robot meninggalkan docking; conveyor dihentikan',6)
feeder=4.2;add('Conveyor kembali ke posisi parkir, jembatan bebas',8)
bridge=0.;add('Platform servis kembali dan rata dengan lantai bagasi',8)
base[1]=-2.6;add('Robot keluar melalui jembatan servis',15)
stage='DONE';add('Selesai: 4 koper dimuat dan 4 dibongkar, 26 koper tetap tersusun',5)
result=dict(version=6,mode='kinematic_scenario',bag_dimensions_m=[.65,.36,.26],fixed_bags=FIXED,frames=states,duration_s=time,active_count=4,fixed_count=26,peak_count=30,operational_full_definition='Designated stacking bays occupied; working aisle and turning bay intentionally reserved',entry='Level service bridge, conveyor parked laterally until robot is inside',aircraft='Generic non-OEM 4.5 x 2.2 x 1.2 m bulk hold')
(R/'config/scenario.json').write_text(json.dumps(result,indent=2))
print('scenario',len(states),'keyframes',time,'s; full phase:',[s['t'] for s in states if s['stage']=='FULL'])
