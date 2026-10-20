#!/usr/bin/env python3
"""Base keyboard teleop, with conservative deployment interlocks."""
import select,sys,termios,tty
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import JointState
from std_msgs.msg import Bool
class Manual(Node):
    def __init__(self):
        super().__init__('cargo_manual');self.q={}
        self.pub=self.create_publisher(Twist,'/cargo_robot/cmd_vel',10)
        self.stop=self.create_publisher(Bool,'/cargo_robot/estop',10)
        self.create_subscription(JointState,'/joint_states',lambda m:self.q.update(zip(m.name,m.position)),10)
    def send(self,key):
        msg=Twist()
        safe=bool(self.q) and self.q.get('extension_joint',1)<.004 and self.q.get('head_z_joint',-1)>-.004 and self.q.get('lift_height_joint',1)<.08 and abs(self.q.get('conveyor_yaw_joint',1))<.017
        if safe:
            msg.linear.x=.12*({'w':1,'s':-1}.get(key,0));msg.linear.y=.12*({'a':1,'d':-1}.get(key,0))
            msg.angular.z=.12*({'q':1,'e':-1}.get(key,0))
        self.pub.publish(msg)
        if key==' ':self.stop.publish(Bool(data=True))
def main():
    rclpy.init();n=Manual();old=termios.tcgetattr(sys.stdin)
    print('w/s forward/back, a/d strafe, q/e yaw; space latches stop. Restart demo/world to reset.')
    try:
        tty.setcbreak(sys.stdin.fileno())
        while rclpy.ok():
            rclpy.spin_once(n,timeout_sec=.03)
            key=sys.stdin.read(1) if select.select([sys.stdin],[],[],.07)[0] else ''
            if key=='\x03':break
            n.send(key)
    finally:termios.tcsetattr(sys.stdin,termios.TCSADRAIN,old);n.pub.publish(Twist());n.destroy_node();rclpy.shutdown()
if __name__=='__main__':main()
