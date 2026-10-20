#!/usr/bin/env python3
"""Publish simulated SOC from explicit assumed phase power; no measured current."""
import json
from pathlib import Path
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
from sensor_msgs.msg import BatteryState
from ament_index_python.packages import get_package_share_directory
from battery_model import update_soc

class BatteryEstimator(Node):
    def __init__(self):
        super().__init__('cargo_battery_estimator')
        f=Path(get_package_share_directory('cargo_robot_description'))/'config/battery_budget.json'
        self.b=json.loads(f.read_text());self.soc=1.0;self.power=95.0;self.last=self.now()
        self.pub=self.create_publisher(BatteryState,'/battery_state',10)
        self.create_subscription(Float64,'/cargo_robot/power_assumption',lambda m:setattr(self,'power',max(0,m.data)),10)
        self.create_timer(.2,self.tick)
    def now(self):return self.get_clock().now().nanoseconds/1e9
    def tick(self):
        now=self.now();dt=max(0,now-self.last);self.last=now;b=self.b
        self.soc=update_soc(self.soc,self.power,dt,b['nominal_Wh'],b['capacity_derate'],b['distribution_efficiency'])
        m=BatteryState();m.header.stamp=self.get_clock().now().to_msg();m.header.frame_id='base_link'
        m.voltage=b['nominal_voltage_V'];m.current=-self.power/(m.voltage*b['distribution_efficiency'])
        m.percentage=self.soc;m.capacity=b['capacity_Ah']*b['capacity_derate'];m.design_capacity=b['capacity_Ah']
        m.charge=m.capacity*self.soc;m.present=True;m.power_supply_status=BatteryState.POWER_SUPPLY_STATUS_DISCHARGING
        m.location='Assumed phase-power model';self.pub.publish(m)

def main():
    rclpy.init();n=BatteryEstimator()
    try:rclpy.spin(n)
    finally:n.destroy_node();rclpy.shutdown()
if __name__=='__main__':main()
