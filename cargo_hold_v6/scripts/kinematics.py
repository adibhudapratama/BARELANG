from pathlib import Path
import json,math
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'config/design_manifest.json').read_text())
def rotation(rpy):
    r,p,y=rpy;cx,sx,cy,sy,cz,sz=math.cos(r),math.sin(r),math.cos(p),math.sin(p),math.cos(y),math.sin(y)
    return np.array([[cz*cy,cz*sy*sx-sz*cx,cz*sy*cx+sz*sx],[sz*cy,sz*sy*sx+cz*cx,sz*sy*cx-cz*sx],[-sy,cy*sx,cy*cx]])
def fk(q=None,base=(0,0,0)):
    q=dict(q or {});h=.12+q.get('lift_height_joint',0);da=math.asin(h/.65)-math.asin(.12/.65);dx=math.sqrt(.65**2-h*h)-math.sqrt(.65**2-.12**2)
    for side in ['left','right']:q[side+'_up_arm_joint']=-da;q[side+'_down_arm_joint']=da
    q['lower_slider_joint']=dx;q['upper_slider_joint']=dx
    b=np.eye(4);b[:3,3]=base[:3];b[:3,:3]=rotation([0,0,base[3] if len(base)>3 else 0]);out={'base_link':b}
    for j in D['joints']:
        v=q.get(j['name'],0)
        if j['mimic']:v=q.get(j['mimic']['joint'],0)*j['mimic']['multiplier']
        t=np.eye(4);t[:3,:3]=rotation(j['rpy']);t[:3,3]=j['xyz'];m=np.eye(4);a=np.array(j['axis'],float)
        if j['type']=='prismatic':m[:3,3]=a*v
        elif j['type'] in ['continuous','revolute']:
            k=np.array([[0,-a[2],a[1]],[a[2],0,-a[0]],[-a[1],a[0],0]])
            m[:3,:3]=np.eye(3)+math.sin(v)*k+(1-math.cos(v))*(k@k)
        out[j['child']]=out[j['parent']]@t@m
    return out
