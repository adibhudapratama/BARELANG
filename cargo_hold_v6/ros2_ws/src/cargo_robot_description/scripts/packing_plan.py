#!/usr/bin/env python3
"""Known-space rigid-bag demonstration. Does not replace perception/packing."""
import json,math
BAG_SIZE=(.65,.36,.26)
DOOR_X=1.0
DOCK_X=1.0
DOCK_Y=-.53
DOCK_YAW=math.pi/2
TURN_X=1.0
TURN_Y=0.0
HEAD_CENTRE_X=.16+.44+.34
HEAD_HOME_CENTRE_X=.16+.34
def standoff_x(target_x):
    return target_x-HEAD_HOME_CENTRE_X-BAG_SIZE[0]-.06

def slots(mode='stack',layers=3):
    if not 1<=layers<=3:raise ValueError('demo supports 1..3 rigid layers')
    cells=[(2.6,0.0)] if mode=='stack' else [(x,y) for x in [3.90,3.10,2.35] for y in [-.68,.68]]
    # Fill deepest row before approaching the door. Keep a centre exit corridor.
    return [dict(x=x,y=y,bottom=k*BAG_SIZE[2],layer=k,base_x=x-HEAD_CENTRE_X)
            for x,y in cells for k in range(layers)]

def height_axes(bed):
    if not .021-1e-6<=bed<=.676:raise ValueError('outside head workspace')
    return {'lift_height_joint':max(0.0,bed-.366),
            'head_z_joint':min(0.0,(bed-.366)/2)}

def mecanum(vx,vy,wz,r=.075,lx=.36,ly=.29):
    k=lx+ly
    return [(vx-vy-k*wz)/r,(vx+vy+k*wz)/r,(vx+vy-k*wz)/r,(vx-vy+k*wz)/r]

if __name__=='__main__':print(json.dumps(slots('fill'),indent=2))
