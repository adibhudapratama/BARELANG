#!/usr/bin/env python3
"""Feedback-driven known-pose demo: receive, direct stack, return, unload.
Target: ROS 2 Jazzy + Gazebo Harmonic. Rigid bags; ideal grip in C++ plugin.
No pose teleportation. Real autonomy requires perception, planning and safety PLC.
"""
import math, subprocess, time
from pathlib import Path
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64, Bool, String
from geometry_msgs.msg import Pose, Twist
from sensor_msgs.msg import JointState,BatteryState
from ament_index_python.packages import get_package_share_directory
from packing_plan import slots, height_axes, DOOR_X, mecanum, standoff_x, DOCK_X,DOCK_Y,DOCK_YAW,TURN_X,TURN_Y

class Demo(Node):
    def __init__(self):
        super().__init__('cargo_demo_cycle')
        self.declare_parameter('mode','stack');self.declare_parameter('layers',3)
        self.declare_parameter('unload',True)
        self.targets=slots(self.get_parameter('mode').value,self.get_parameter('layers').value)
        self.transfer_ready=False
        self.q={};self.base=None;self.bag=None;self.grasped=False;self.selected=''
        self.target_q={};self.belt_value=0.0;self.grip_value=False;self.active='bag_01'
        self.drive_goal=None;self.drive_creep=False;self.fault=False;self.waiting=None;self.step_started=0;self.last_base=0
        self.power_assumption=95.0;self.battery_soc=1.0
        self.power_pub=self.create_publisher(Float64,'/cargo_robot/power_assumption',10)
        self.create_subscription(BatteryState,'/battery_state',lambda m:setattr(self,'battery_soc',m.percentage),10)
        self.pub={n:self.create_publisher(Float64,'/cargo_robot/'+n+'/cmd',10) for n in [
            'lift_height_joint','conveyor_yaw_joint','extension_joint','head_z_joint',
            'support_blade_joint','jaw_lift_joint','left_jaw_joint','right_jaw_joint',
            'main_belt_joint','nose_belt_joint']}
        self.belt_pub={n:self.create_publisher(Float64,'/cargo_robot/'+n+'_belt_speed',10)
                       for n in ['main','nose','external']}
        self.vel=self.create_publisher(Twist,'/cargo_robot/cmd_vel',10)
        self.grip_pub=self.create_publisher(Bool,'/cargo_robot/grip',10)
        self.active_pub=self.create_publisher(String,'/cargo_robot/active_bag',10)
        self.estop=self.create_publisher(Bool,'/cargo_robot/estop',10)
        self.create_subscription(JointState,'/joint_states',self.joints,10)
        self.create_subscription(Pose,'/cargo_robot/base_pose',self.base_feedback,10)
        self.create_subscription(Pose,'/cargo_robot/bag_pose',lambda m:setattr(self,'bag',m),10)
        self.create_subscription(Bool,'/cargo_robot/transfer_ready',lambda m:setattr(self,'transfer_ready',m.data),10)
        self.create_subscription(Bool,'/cargo_robot/grasped',lambda m:setattr(self,'grasped',m.data),10)
        self.create_subscription(String,'/cargo_robot/selected_bag',lambda m:setattr(self,'selected',m.data),10)
        self.workflow=self.cycle();self.timer=self.create_timer(.05,self.tick)
    def now(self):return self.get_clock().now().nanoseconds*1e-9
    def base_feedback(self,m):self.base=m;self.last_base=self.now()
    def joints(self,m):self.q.update(zip(m.name,m.position))
    def stop(self,reason):
        self.fault=True;self.drive_goal=None;self.belt_value=0;self.power_assumption=95.0
        self.vel.publish(Twist());self.estop.publish(Bool(data=True));self.refresh()
        self.get_logger().error(reason+'; stopped, held payload retained')
    def refresh(self):
        self.power_pub.publish(Float64(data=180.0 if abs(self.belt_value)>.001 else self.power_assumption))
        for n,v in self.target_q.items():self.pub[n].publish(Float64(data=float(v)))
        transfer_speed=self.belt_value if self.transfer_ready else 0.0
        for n,p in self.belt_pub.items():p.publish(Float64(data=transfer_speed))
        self.pub['main_belt_joint'].publish(Float64(data=transfer_speed/.025))
        self.pub['nose_belt_joint'].publish(Float64(data=transfer_speed/.008))
        self.grip_pub.publish(Bool(data=self.grip_value));self.active_pub.publish(String(data=self.active))
    def tick(self):
        self.refresh()
        if self.fault:return
        if self.battery_soc<=.15:self.stop('Battery estimate reached 15 percent reserve');return
        if self.base is not None and self.now()-self.last_base>.6:
            self.stop('Base telemetry stale');return
        if self.drive_goal is not None:self.drive_control()
        try:
            if self.waiting:
                label,predicate,limit=self.waiting
                if predicate():self.waiting=None
                elif self.now()-self.step_started>limit:self.stop('Timeout: '+label);return
                else:return
            self.waiting=next(self.workflow);self.step_started=self.now()
            self.get_logger().info(self.waiting[0])
        except StopIteration:
            self.vel.publish(Twist());self.belt_value=0;self.power_assumption=95.0;self.refresh();self.timer.cancel()
            self.get_logger().info('Completed direct-floor stack and external-conveyor handoff')
        except Exception as e:self.stop(str(e))
    def wait(self,label,predicate,timeout=25):return (label,predicate,timeout)
    def pause(self,seconds,label='Settle'):
        self.power_assumption=95.0
        end=self.now()+seconds;return self.wait(label,lambda:self.now()>=end,seconds+3)
    def axes(self,label,**values):
        self.power_assumption=700.0
        if self.grasped and abs(values.get('conveyor_yaw_joint',self.target_q.get('conveyor_yaw_joint',0)))>math.radians(30):
            raise RuntimeError('Loaded yaw exceeds 30 degrees')
        yaw=values.get('conveyor_yaw_joint',self.target_q.get('conveyor_yaw_joint',0))
        lift=values.get('lift_height_joint',self.target_q.get('lift_height_joint',0))
        if abs(yaw)>math.radians(1) and lift<.05:
            raise RuntimeError('Raise scissor 50 mm before yaw')
        self.target_q.update(values)
        return self.wait(label,lambda:all(n in self.q and abs(self.q[n]-v)<.004
                                          for n,v in values.items()),35)
    def goto(self,x,y,label,creep=False,yaw=0.0):
        if self.target_q.get('extension_joint',0)>.004 or self.target_q.get('head_z_joint',0)<-.004:
            raise RuntimeError('Base motion prohibited with head deployed or lowered')
        if self.target_q.get('lift_height_joint',0)>(.25 if creep else .08):
            raise RuntimeError('Lower main lift before travel')
        if creep and (not self.grasped or self.base is None or
                      abs(y-self.base.position.y)>.02 or abs(x-self.base.position.x)>.35):
            raise RuntimeError('Elevated creep is only a short, aligned, supported-bag approach')
        if abs(self.target_q.get('conveyor_yaw_joint',0))>math.radians(1):
            raise RuntimeError('Stow yaw before base travel')
        if creep and abs(yaw)>.015:raise RuntimeError('Elevated creep cannot rotate')
        self.power_assumption=400.0 if self.grasped else 300.0
        self.drive_creep=creep;self.drive_goal=(x,y,yaw)
        return self.wait(label,lambda:self.drive_goal is None,100)
    def turn_in_bay(self,yaw,label):
        if self.base is None or math.hypot(self.base.position.x-TURN_X,self.base.position.y-TURN_Y)>.025:
            raise RuntimeError('90-degree rotation requires reserved clear reception bay')
        if self.q.get('lift_height_joint',0)>.004 or self.q.get('extension_joint',0)>.004 or abs(self.q.get('head_z_joint',0))>.004:
            raise RuntimeError('Rotate only with low, retracted, level head')
        self.power_assumption=480.0 if self.grasped else 340.0
        self.drive_creep=False;self.drive_goal=(TURN_X,TURN_Y,yaw)
        return self.wait(label,lambda:self.drive_goal is None,30)
    def body_forward(self):
        if self.base is None or self.bag is None:return -999.0
        o=self.base.orientation;yaw=math.atan2(2*(o.w*o.z+o.x*o.y),1-2*(o.y*o.y+o.z*o.z))
        return math.cos(yaw)*(self.bag.position.x-self.base.position.x)+math.sin(yaw)*(self.bag.position.y-self.base.position.y)
    def drive_control(self):
        if self.base is None:return
        gx,gy,target_yaw=self.drive_goal;p=self.base.position;o=self.base.orientation
        yaw=math.atan2(2*(o.w*o.z+o.x*o.y),1-2*(o.y*o.y+o.z*o.z))
        dx,dy=gx-p.x,gy-p.y
        error_yaw=math.atan2(math.sin(target_yaw-yaw),math.cos(target_yaw-yaw))
        tolerance=.003 if abs(gx-DOCK_X)<.001 and abs(gy-DOCK_Y)<.001 else .012
        if math.hypot(dx,dy)<tolerance and abs(error_yaw)<.015:
            self.drive_goal=None;self.vel.publish(Twist());return
        if self.drive_creep and (not self.grasped or self.q.get('lift_height_joint',0)>.258):
            self.stop('Elevated approach feedback limit');return
        c,s=math.cos(yaw),math.sin(yaw);v=Twist();limit=.05 if self.drive_creep else (.15 if self.grasped else .30)
        ux,uy=c*dx+s*dy,-s*dx+c*dy;norm=math.hypot(ux,uy)
        scale=min(1,limit/max(norm*.8,1e-9));v.linear.x=.8*ux*scale;v.linear.y=.8*uy*scale
        v.angular.z=max(-.15,min(.15,error_yaw))
        if abs(error_yaw)>.035:
            if math.hypot(p.x-TURN_X,p.y-TURN_Y)>.04:self.stop('Rotation outside reserved bay');return
            v.linear.x=0.0;v.linear.y=0.0
        self.vel.publish(v)
    def spawn(self,name):
        f=Path(get_package_share_directory('cargo_robot_description'))/'models/bag_template.sdf'
        subprocess.run(['ros2','run','ros_gz_sim','create','-world','cargo_demo',
                        '-name',name,'-file',str(f),'-x','1.0','-y','-1.44','-z','.495','-Y',str(DOCK_YAW)],
                       check=True,timeout=20,capture_output=True)
    def leave_world(self,name):
        # Delete only AFTER the bag is supported on the external conveyor.
        # This represents leaving the simulated handling boundary, not placement.
        result=subprocess.run(['gz','service','-s','/world/cargo_demo/remove',
            '--reqtype','gz.msgs.Entity','--reptype','gz.msgs.Boolean','--timeout','2000',
            '--req','name: "'+name+'" type: MODEL'],capture_output=True,text=True,timeout=6)
        if result.returncode or 'true' not in result.stdout:
            raise RuntimeError('External handoff complete, entity removal not confirmed')
    def cycle(self):
        yield self.wait('Wait for pose and joint feedback',lambda:self.base is not None and len(self.q)>12,45)
        yield self.axes('Home',lift_height_joint=0,conveyor_yaw_joint=0,extension_joint=0,
                        head_z_joint=0,support_blade_joint=0,jaw_lift_joint=0,
                        left_jaw_joint=0,right_jaw_joint=0)
        for i,t in enumerate(self.targets):
            name='bag_%02d'%(i+1)
            if i:self.spawn(name)
            self.active=name
            yield self.wait('Select incoming '+name,lambda:self.selected==name and self.bag is not None,12)
            yield self.axes('Extend receiving support',support_blade_joint=0,jaw_lift_joint=0)
            yield self.wait('Verify full open passage before intake',lambda:self.transfer_ready,10)
            self.belt_value=.20
            yield self.wait('Receive '+name+' from external doorway conveyor',
                            lambda:self.body_forward()>=.493,20)
            self.belt_value=0
            yield self.axes('Close compliant pads',left_jaw_joint=.120,right_jaw_joint=.120)
            self.grip_value=True;yield self.wait('Confirm grip',lambda:self.grasped,8)
            yield self.goto(TURN_X,TURN_Y,'Clear side door, keep receiver facing conveyor',yaw=DOCK_YAW)
            yield self.turn_in_bay(0.0,'Rotate loaded base 90 degrees in clear bay')
            bed=t['bottom']+.021;safe=standoff_x(t['x'])
            yield self.goto(safe,0,'Travel to clear standoff')
            yield self.goto(safe,t['y'],'Mecanum lateral alignment outside stack')
            if bed>.366:
                yield self.axes('Raise bag above lower stack before approach',**height_axes(bed))
            yield self.goto(t['base_x'],t['y'],'Short aligned stack approach',creep=bed>.366)
            yield self.axes('Extend head',extension_joint=.44)
            yield self.axes('Set direct stack level',**height_axes(bed))
            yield self.axes('Withdraw support completely',support_blade_joint=-.56)
            self.grip_value=False;yield self.wait('Release onto floor / previous bag',lambda:not self.grasped,8)
            yield self.axes('Open pads',left_jaw_joint=0,right_jaw_joint=0)
            yield self.pause(.7,'Check settling on direct stack')
            yield self.wait('Verify placement height',lambda:abs(self.bag.position.z-(t['bottom']+.13))<.03,5)
            yield self.axes('Restore travel height',head_z_joint=0,lift_height_joint=0)
            yield self.axes('Retract raised head clear of stack',extension_joint=0)
            yield self.goto(safe,t['y'],'Back away before lateral exit')
            yield self.goto(safe,0,'Leave stack through reserved corridor')
            yield self.goto(TURN_X,TURN_Y,'Return empty to reserved reception bay')
            yield self.turn_in_bay(DOCK_YAW,'Face side conveyor before docking')
            yield self.goto(DOCK_X,DOCK_Y,'Dock at side door for next bag',yaw=DOCK_YAW)
        if not self.get_parameter('unload').value:return
        for i in reversed(range(len(self.targets))):
            t=self.targets[i];name='bag_%02d'%(i+1);self.active=name
            yield self.wait('Select top accessible '+name,lambda:self.selected==name,12)
            yield self.axes('Pickup preparation',support_blade_joint=-.56,jaw_lift_joint=0,
                            left_jaw_joint=0,right_jaw_joint=0)
            yield self.goto(TURN_X,TURN_Y,'Exit side dock before unloading',yaw=DOCK_YAW)
            yield self.turn_in_bay(0.0,'Turn empty toward baggage stack')
            safe=standoff_x(t['x'])
            yield self.goto(safe,0,'Approach clear standoff')
            yield self.goto(safe,t['y'],'Lateral alignment outside stack')
            yield self.goto(t['base_x'],t['y'],'Aligned empty-head approach')
            yield self.axes('Reach bag',extension_joint=.44)
            yield self.axes('Align pickup support',**height_axes(t['bottom']+.021))
            yield self.axes('Clamp sides with measured force',left_jaw_joint=.120,right_jaw_joint=.120)
            self.grip_value=True;yield self.wait('Confirm pickup grip',lambda:self.grasped,8)
            yield self.axes('Micro-lift creates bottom clearance',jaw_lift_joint=.035)
            yield self.axes('Insert support below bag',support_blade_joint=0)
            yield self.axes('Settle onto support',jaw_lift_joint=.021)
            # Lift 50 mm before pulling horizontally across the lower stack.
            bed=max(.366,t['bottom']+.071)
            yield self.axes('Lift clear of lower bag',**height_axes(bed))
            yield self.axes('Retract supported bag',extension_joint=0)
            yield self.goto(safe,t['y'],'Back clear of lower stack before lowering',creep=bed>.366)
            yield self.axes('Set travel height',head_z_joint=0,lift_height_joint=0,jaw_lift_joint=.021)
            yield self.goto(safe,0,'Exit stack aisle')
            yield self.goto(TURN_X,TURN_Y,'Return loaded to clear reception bay')
            yield self.turn_in_bay(DOCK_YAW,'Rotate supported bag toward side conveyor')
            yield self.goto(DOCK_X,DOCK_Y,'Dock loaded at side door',yaw=DOCK_YAW)
            self.grip_value=False;yield self.wait('Release onto robot belt',lambda:not self.grasped,8)
            yield self.axes('Open pads for reverse transfer',left_jaw_joint=0,right_jaw_joint=0,jaw_lift_joint=0)
            yield self.wait('Verify full open passage before reverse',lambda:self.transfer_ready,10)
            self.belt_value=-.20
            yield self.wait('Reverse belts through side doorway',lambda:self.bag.position.y<-1.49,20)
            self.belt_value=0;yield self.pause(.8,'External conveyor handoff')
            self.leave_world(name)
        yield self.axes('Park with support retracted',support_blade_joint=-.56)

def main():
    rclpy.init();node=Demo()
    try:rclpy.spin(node)
    except KeyboardInterrupt:node.stop('Operator stop')
    finally:node.vel.publish(Twist());node.destroy_node();rclpy.shutdown()
if __name__=='__main__':main()
