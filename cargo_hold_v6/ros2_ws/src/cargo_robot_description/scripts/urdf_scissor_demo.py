#!/usr/bin/env python3
"""RViz preview with nonlinear scissor follower positions; no physics."""
import json,math
from pathlib import Path
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from ament_index_python.packages import get_package_share_directory
class Preview(Node):
    def __init__(self):
        super().__init__('urdf_scissor_preview');self.declare_parameter('height',.12)
        d=json.loads((Path(get_package_share_directory('cargo_robot_description'))/'config/design_manifest.json').read_text())
        self.names=[j['name'] for j in d['joints'] if j['type']!='fixed']
        self.pub=self.create_publisher(JointState,'/joint_states',10);self.create_timer(.05,self.tick)
    def tick(self):
        h=max(.12,min(.43,float(self.get_parameter('height').value)))
        da=math.asin(h/.65)-math.asin(.12/.65);dx=math.sqrt(.65**2-h*h)-math.sqrt(.65**2-.12**2)
        q={n:0.0 for n in self.names};q['lift_height_joint']=h-.12
        q.update(lower_slider_joint=dx,upper_slider_joint=dx)
        for side in ['left','right']:q[side+'_up_arm_joint']=-da;q[side+'_down_arm_joint']=da
        msg=JointState();msg.header.stamp=self.get_clock().now().to_msg();msg.name=self.names;msg.position=[q[n] for n in self.names];self.pub.publish(msg)
def main():
    rclpy.init();n=Preview()
    try:rclpy.spin(n)
    except KeyboardInterrupt:pass
    finally:n.destroy_node();rclpy.shutdown()
if __name__=='__main__':main()
