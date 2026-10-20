// Deterministic kinematic playback for Gazebo Harmonic (gz-sim8).
// This intentionally prescribes link poses. No contact forces, wheel traction,
// flexible luggage, obstacle detection, grasp success or autonomy is simulated.
#include <gz/plugin/Register.hh>
#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/components/Model.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/math/Pose3.hh>
#include <gz/common/Console.hh>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <cstdlib>
#include <algorithm>
#include <chrono>
#include <stdexcept>
namespace cargo {
class ScenarioReplay final:public gz::sim::System,public gz::sim::ISystemConfigure,public gz::sim::ISystemPreUpdate {
 struct Track {std::string model,link;gz::sim::Entity entity{gz::sim::kNullEntity};};
 struct Frame {double t;std::vector<gz::math::Pose3d> poses;};
 std::vector<Track> tracks;std::vector<Frame> frames;size_t index=0;double speed=1,nextPub=0;bool bound=false,done=false;std::string root;
 public:
 void Configure(const gz::sim::Entity&,const std::shared_ptr<const sdf::Element>&,gz::sim::EntityComponentManager&,gz::sim::EventManager&)override{
  const char *r=std::getenv("CARGO_PROJECT_ROOT");if(!r)throw std::runtime_error("CARGO_PROJECT_ROOT unset: use run_gazebo.sh");root=r;
  if(const char *s=std::getenv("CARGO_REPLAY_SPEED"))speed=std::clamp(std::stod(s),.1,1000.);
  std::ifstream tf(root+"/config/tracks.txt");std::string line;
  while(std::getline(tf,line)){auto p=line.find('/');if(p!=std::string::npos)tracks.push_back({line.substr(0,p),line.substr(p+1)});}
  std::ifstream in(root+"/config/trajectory.csv");
  while(std::getline(in,line)){if(line.empty()||line[0]=='#')continue;std::replace(line.begin(),line.end(),',',' ');std::istringstream s(line);Frame f;s>>f.t;
   for(size_t i=0;i<tracks.size();++i){double x,y,z,w,qx,qy,qz;if(!(s>>x>>y>>z>>w>>qx>>qy>>qz))throw std::runtime_error("Incomplete trajectory row");f.poses.emplace_back(gz::math::Vector3d(x,y,z),gz::math::Quaterniond(w,qx,qy,qz));}frames.push_back(std::move(f));}
  if(tracks.empty()||frames.size()<2)throw std::runtime_error("Missing replay data");
  gzmsg<<"CARGO_REPLAY_READY samples="<<frames.size()<<" tracks="<<tracks.size()<<" speed="<<speed<<" kinematic=true\n";
 }
 void PreUpdate(const gz::sim::UpdateInfo&info,gz::sim::EntityComponentManager&ecm)override{
  if(info.paused)return;
  if(!bound){
   for(auto &t:tracks){ecm.Each<gz::sim::components::Model,gz::sim::components::Name>([&](const gz::sim::Entity&e,const auto*,const auto*n){if(n->Data()==t.model)t.entity=gz::sim::Model(e).LinkByName(ecm,t.link);return true;});}
   bound=std::all_of(tracks.begin(),tracks.end(),[](const Track&t){return t.entity!=gz::sim::kNullEntity;});
   if(!bound){gzerr<<"Replay could not resolve all links\n";return;}
   gzmsg<<"CARGO_REPLAY_BOUND "<<tracks.size()<<"/"<<tracks.size()<<" links\n";
  }
  double t=std::chrono::duration<double>(info.simTime).count()*speed;t=std::min(t,frames.back().t);
  if(t<frames[index].t)index=0;while(index+1<frames.size()-1&&frames[index+1].t<t)++index;
  const auto &a=frames[index],&b=frames[index+1];double u=std::clamp((t-a.t)/(b.t-a.t),0.,1.);
  for(size_t i=0;i<tracks.size();++i){const auto &p=a.poses[i],&q=b.poses[i];gz::math::Pose3d pose(p.Pos()*(1-u)+q.Pos()*u,gz::math::Quaterniond::Slerp(u,p.Rot(),q.Rot(),true));
   ecm.SetComponentData<gz::sim::components::Pose>(tracks[i].entity,pose);
   ecm.SetChanged(tracks[i].entity,gz::sim::components::Pose::typeId,gz::sim::ComponentState::OneTimeChange);
  }
  if(!done&&t>=frames.back().t){done=true;gzmsg<<"CARGO_REPLAY_COMPLETE scenario_seconds="<<t<<" links="<<tracks.size()<<"\n";
   if(const char *log=std::getenv("CARGO_REPLAY_RECEIPT")){std::ofstream f(log);f<<"{\"completed\":true,\"mode\":\"kinematic\",\"scenario_seconds\":"<<t<<",\"tracks_resolved\":"<<tracks.size()<<",\"samples\":"<<frames.size()<<",\"physics_validated\":false}\n";}
  }
 }
};}
#ifndef CARGO_REPLAY_TEST
GZ_ADD_PLUGIN(cargo::ScenarioReplay,gz::sim::System,cargo::ScenarioReplay::ISystemConfigure,cargo::ScenarioReplay::ISystemPreUpdate)

#endif
