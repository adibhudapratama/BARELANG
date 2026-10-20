// Gazebo Harmonic / gz-sim8 concept handling system.
// Force-driven belts, ideal successful grip, ideal nonlinear scissor closure.
// Bags are never teleported. This is not a compliant-gripper or load-path proof.
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <memory>
#include <mutex>
#include <string>
#include <vector>
#include <gz/plugin/Register.hh>
#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Link.hh>
#include <gz/sim/Util.hh>
#include <gz/sim/components/Model.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/JointPosition.hh>
#include <gz/sim/components/JointPositionReset.hh>
#include <gz/sim/components/DetachableJoint.hh>
#include <gz/transport/Node.hh>
#include <gz/msgs/double.pb.h>
#include <gz/msgs/boolean.pb.h>
#include <gz/msgs/pose.pb.h>
#include <gz/msgs/stringmsg.pb.h>

namespace cargo {
class CargoHandling final : public gz::sim::System,
    public gz::sim::ISystemConfigure, public gz::sim::ISystemPreUpdate,
    public gz::sim::ISystemPostUpdate {
  using Entity = gz::sim::Entity;
  using ECM = gz::sim::EntityComponentManager;
  gz::sim::Model model;
  Entity mainLink{gz::sim::kNullEntity}, bladeLink{gz::sim::kNullEntity};
  Entity jawLink{gz::sim::kNullEntity}, baseLink{gz::sim::kNullEntity};
  Entity bagLink{gz::sim::kNullEntity}, gripJoint{gz::sim::kNullEntity};
  std::atomic<double> mainSpeed{0}, noseSpeed{0}, externalSpeed{0};
  std::atomic<bool> grip{false}, estop{false};
  std::mutex nameMutex;
  std::string desiredBag{"bag_01"}, selectedBag;
  double nextPublish{0};
  gz::transport::Node node;
  gz::transport::Node::Publisher gripPub, basePub, bagPub, selectedPub, transferPub;
  double Q(const std::string &n, const ECM &ecm) const {
    auto e=model.JointByName(ecm,n);
    const auto *q=ecm.Component<gz::sim::components::JointPosition>(e);
    return q && !q->Data().empty() ? q->Data()[0] : 0.0;
  }
  void Reset(const std::string &n, double value, ECM &ecm) {
    auto e=model.JointByName(ecm,n);if(e==gz::sim::kNullEntity)return;
    auto *c=ecm.Component<gz::sim::components::JointPositionReset>(e);
    if(c){c->Data()=std::vector<double>{value};
      ecm.SetChanged(e,gz::sim::components::JointPositionReset::typeId,
                     gz::sim::ComponentState::OneTimeChange);}
    else ecm.CreateComponent(e,gz::sim::components::JointPositionReset(std::vector<double>{value}));
  }
  void Followers(ECM &ecm) {
    const double L=.65, h=std::clamp(.12+Q("lift_height_joint",ecm),.12,.43);
    const double da=std::asin(h/L)-std::asin(.12/L);
    const double dx=std::sqrt(L*L-h*h)-std::sqrt(L*L-.12*.12);
    for(const std::string side:{"left","right"}) {
      Reset(side+"_up_arm_joint",-da,ecm);Reset(side+"_down_arm_joint",da,ecm);
    }
    Reset("lower_slider_joint",dx,ecm);Reset("upper_slider_joint",dx,ecm);
    Reset("head_z_follower_joint",Q("head_z_joint",ecm),ecm);
    // These are kinematic follower resets, NOT resets of any bag pose.
  }
  bool IsClosed(const ECM &ecm) const {
    return Q("left_jaw_joint",ecm)>=.115 && Q("right_jaw_joint",ecm)>=.115;
  }
  bool PassageOpen(const ECM &ecm) const {
    auto v=gz::sim::Link(baseLink).WorldLinearVelocity(ecm);
    auto w=gz::sim::Link(baseLink).WorldAngularVelocity(ecm);
    return v && w && v->Length()<.015 && w->Length()<.015
        && Q("left_jaw_joint",ecm)<.004 && Q("right_jaw_joint",ecm)<.004
        && Q("lift_height_joint",ecm)<.004 && std::abs(Q("head_z_joint",ecm))<.004
        && Q("extension_joint",ecm)<.004 && std::abs(Q("conveyor_yaw_joint",ecm))<.01
        && std::abs(Q("support_blade_joint",ecm))<.004 && Q("jaw_lift_joint",ecm)<.004;
  }
  static gz::msgs::Pose PoseMsg(const gz::math::Pose3d &p) {
    gz::msgs::Pose msg;
    msg.mutable_position()->set_x(p.Pos().X());msg.mutable_position()->set_y(p.Pos().Y());
    msg.mutable_position()->set_z(p.Pos().Z());msg.mutable_orientation()->set_w(p.Rot().W());
    msg.mutable_orientation()->set_x(p.Rot().X());msg.mutable_orientation()->set_y(p.Rot().Y());
    msg.mutable_orientation()->set_z(p.Rot().Z());return msg;
  }
 public:
  void Configure(const Entity &entity, const std::shared_ptr<const sdf::Element> &,
      ECM &ecm, gz::sim::EventManager &) override {
    model=gz::sim::Model(entity);
    mainLink=model.LinkByName(ecm,"conveyor_yaw_link");
    bladeLink=model.LinkByName(ecm,"support_blade_link");
    jawLink=model.LinkByName(ecm,"jaw_frame_link");baseLink=model.LinkByName(ecm,"base_link");
    gz::sim::Link(baseLink).EnableVelocityChecks(ecm);
    gz::sim::Link(mainLink).EnableVelocityChecks(ecm);gz::sim::Link(bladeLink).EnableVelocityChecks(ecm);
    node.Subscribe("/cargo_robot/main_belt_speed",&CargoHandling::Main,this);
    node.Subscribe("/cargo_robot/nose_belt_speed",&CargoHandling::Nose,this);
    node.Subscribe("/cargo_robot/external_belt_speed",&CargoHandling::External,this);
    node.Subscribe("/cargo_robot/active_bag",&CargoHandling::Select,this);
    node.Subscribe("/cargo_robot/grip",&CargoHandling::Grip,this);
    node.Subscribe("/cargo_robot/estop",&CargoHandling::Stop,this);
    gripPub=node.Advertise<gz::msgs::Boolean>("/cargo_robot/grasped");
    basePub=node.Advertise<gz::msgs::Pose>("/cargo_robot/base_pose");
    bagPub=node.Advertise<gz::msgs::Pose>("/cargo_robot/bag_pose");
    selectedPub=node.Advertise<gz::msgs::StringMsg>("/cargo_robot/selected_bag");
    transferPub=node.Advertise<gz::msgs::Boolean>("/cargo_robot/transfer_ready");
  }
  void Main(const gz::msgs::Double &m){mainSpeed=std::clamp(m.data(),-.25,.25);}
  void Nose(const gz::msgs::Double &m){noseSpeed=std::clamp(m.data(),-.25,.25);}
  void External(const gz::msgs::Double &m){externalSpeed=std::clamp(m.data(),-.25,.25);}
  void Grip(const gz::msgs::Boolean &m){grip=m.data();}
  void Stop(const gz::msgs::Boolean &m){estop=m.data();}
  void Select(const gz::msgs::StringMsg &m){std::lock_guard<std::mutex> lock(nameMutex);desiredBag=m.data();}
  void PreUpdate(const gz::sim::UpdateInfo &info, ECM &ecm) override {
    if(info.paused)return;Followers(ecm);
    if(!estop && !grip && gripJoint!=gz::sim::kNullEntity){
      ecm.RequestRemoveEntity(gripJoint);gripJoint=gz::sim::kNullEntity;
    }
    std::string wanted;{std::lock_guard<std::mutex> lock(nameMutex);wanted=desiredBag;}
    if(gripJoint==gz::sim::kNullEntity && wanted!=selectedBag){
      bagLink=gz::sim::kNullEntity;selectedBag=wanted;
    }
    if(bagLink==gz::sim::kNullEntity){
      ecm.Each<gz::sim::components::Model,gz::sim::components::Name>(
        [&](const Entity &e,const auto *,const auto *n){
          if(n->Data()==selectedBag)bagLink=gz::sim::Model(e).LinkByName(ecm,"body");return true;
        });
      if(bagLink!=gz::sim::kNullEntity)gz::sim::Link(bagLink).EnableVelocityChecks(ecm);
    }
    if(bagLink==gz::sim::kNullEntity)return;
    auto bp=gz::sim::worldPose(bagLink,ecm),jp=gz::sim::worldPose(jawLink,ecm);
    auto rj=jp.Inverse()*bp;
    if(!estop && grip && gripJoint==gz::sim::kNullEntity && IsClosed(ecm)
        && std::abs(rj.Pos().X()-.34)<.085 && std::abs(rj.Pos().Y())<.025
        && rj.Pos().Z()>.11 && rj.Pos().Z()<.19){
      gz::sim::components::DetachableJointInfo di;
      di.parentLink=jawLink;di.childLink=bagLink;di.jointType="fixed";
      gripJoint=ecm.CreateEntity();ecm.CreateComponent(gripJoint,gz::sim::components::DetachableJoint(di));
    }
    // Transfer cannot drive against a closed jaw, deployed head or moving base.
    if(estop || gripJoint!=gz::sim::kNullEntity || !PassageOpen(ecm))return;
    auto vel=gz::sim::Link(bagLink).WorldLinearVelocity(ecm);if(!vel)return;
    auto np=gz::sim::worldPose(bladeLink,ecm),mp=gz::sim::worldPose(mainLink,ecm);
    auto rn=np.Inverse()*bp,rm=mp.Inverse()*bp;
    Entity carrier=gz::sim::kNullEntity;gz::math::Vector3d dir(1,0,0);double speed=0;
    // Zones check the supported centre of the 650 x 360 x 260 mm demo bag.
    if(std::abs(rn.Pos().Y())<.23 && rn.Pos().X()>-.06 && rn.Pos().X()<.48
        && std::abs(rn.Pos().Z()-.161)<.035){
      carrier=bladeLink;dir=np.Rot().RotateVector(dir);speed=noseSpeed;
    }else if(std::abs(rm.Pos().Y())<.26 && rm.Pos().X()>-.72 && rm.Pos().X()<.25
        && std::abs(rm.Pos().Z()-.161)<.035){
      carrier=mainLink;dir=mp.Rot().RotateVector(dir);speed=mainSpeed;
    }else if(bp.Pos().Y()>-1.95 && bp.Pos().Y()<-1.08
        && std::abs(bp.Pos().X()-1.0)<.24 && std::abs(bp.Pos().Z()-.495)<.035){
      speed=externalSpeed;dir=gz::math::Vector3d(0,1,0);}
    if(std::abs(speed)<.001)return;
    double force=32.0*(12*(speed-vel->Dot(dir))+.12*9.81*std::tanh(speed*20));
    force=std::clamp(force,-180.0,180.0);
    gz::sim::Link(bagLink).AddWorldForce(ecm,dir*force);
    if(carrier!=gz::sim::kNullEntity)gz::sim::Link(carrier).AddWorldForce(ecm,-dir*force);
  }
  void PostUpdate(const gz::sim::UpdateInfo &info,const ECM &ecm) override {
    double t=std::chrono::duration<double>(info.simTime).count();if(t<nextPublish)return;nextPublish=t+.04;
    gz::msgs::Boolean m;m.set_data(gripJoint!=gz::sim::kNullEntity);gripPub.Publish(m);
    gz::msgs::Boolean ready;ready.set_data(!estop && PassageOpen(ecm));transferPub.Publish(ready);
    if(baseLink!=gz::sim::kNullEntity)basePub.Publish(PoseMsg(gz::sim::worldPose(baseLink,ecm)));
    if(bagLink!=gz::sim::kNullEntity){bagPub.Publish(PoseMsg(gz::sim::worldPose(bagLink,ecm)));
      gz::msgs::StringMsg s;s.set_data(selectedBag);selectedPub.Publish(s);}
  }
};
}
GZ_ADD_PLUGIN(cargo::CargoHandling,gz::sim::System,
  cargo::CargoHandling::ISystemConfigure,cargo::CargoHandling::ISystemPreUpdate,
  cargo::CargoHandling::ISystemPostUpdate)
GZ_ADD_PLUGIN_ALIAS(cargo::CargoHandling,"cargo::CargoHandling")
