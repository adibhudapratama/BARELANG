#!/usr/bin/env python3
"""Move Gazebo GUI camera using the official CameraTracking service."""
import math,sys,subprocess
views={'overview':((6.3,-6.7,5.6),(2.05,-.45,.25)), 'interior':((.16,.83,1.035),(2.35,-.10,.43)), 'handling':((.10,-2.2,1.55),(1.9,0,.45))}
key=sys.argv[1] if len(sys.argv)>1 else 'overview'
if key not in views:raise SystemExit('Choose overview | interior | handling')
p,t=views[key];dx,dy,dz=[b-a for a,b in zip(p,t)];yaw=math.atan2(dy,dx);pitch=-math.atan2(dz,math.hypot(dx,dy));cy,sy=math.cos(yaw/2),math.sin(yaw/2);cp,sp=math.cos(pitch/2),math.sin(pitch/2);qw,qx,qy,qz=cy*cp,-sy*sp,cy*sp,sy*cp
req=f'pose: {{position: {{x: {p[0]}, y: {p[1]}, z: {p[2]}}}, orientation: {{w: {qw}, x: {qx}, y: {qy}, z: {qz}}}}}, duration: 1'
subprocess.run(['gz','service','-s','/gui/move_to/pose','--reqtype','gz.msgs.GUICamera','--reptype','gz.msgs.Boolean','--timeout','3000','--req',req],check=True)
