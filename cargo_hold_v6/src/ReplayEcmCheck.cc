// Runs the real plugin against Gazebo's EntityComponentManager, without Server
// or sockets. This is a core execution test, NOT a Gazebo GUI/server run.
#define CARGO_REPLAY_TEST
#include "ScenarioReplay.cc"
#include <gz/sim/EventManager.hh>
#include <gz/sim/components/Link.hh>
#include <gz/sim/components/ParentEntity.hh>
#include <map>
#include <gz/sim/SdfEntityCreator.hh>
#include <sdf/Root.hh>
#include <iomanip>
int main(){
 try{
  const char *root=std::getenv("CARGO_PROJECT_ROOT");if(!root)return 2;
  gz::sim::EntityComponentManager ecm;gz::sim::EventManager events;std::map<std::string,gz::sim::Entity> models;std::vector<gz::sim::Entity> links;
  sdf::Root sdfRoot;auto sdfErrors=sdfRoot.Load(std::string(root)+"/worlds/cargo_hold_cutaway.sdf");
  if(!sdfErrors.empty()){for(const auto&e:sdfErrors)std::cerr<<e.Message()<<'\n';return 4;}
  gz::sim::SdfEntityCreator creator(ecm,events);creator.CreateEntities(sdfRoot.WorldByIndex(0));
  std::ifstream input(std::string(root)+"/config/tracks.txt");std::string line;
  while(std::getline(input,line)){auto k=line.find('/');auto mn=line.substr(0,k),ln=line.substr(k+1);gz::sim::Entity model=gz::sim::kNullEntity;
   ecm.Each<gz::sim::components::Model,gz::sim::components::Name>([&](const gz::sim::Entity&e,const auto*,const auto*n){if(n->Data()==mn)model=e;return true;});
   if(model==gz::sim::kNullEntity)return 5;auto link=gz::sim::Model(model).LinkByName(ecm,ln);if(link==gz::sim::kNullEntity)return 6;links.push_back(link);
  }
  cargo::ScenarioReplay replay;replay.Configure(gz::sim::kNullEntity,{},ecm,events);
  std::ofstream out(std::string(root)+"/validation/ecm_probe.csv");out<<std::setprecision(12);
  for(int i=0;i<=2202;i++){double t=i*.5;gz::sim::UpdateInfo u;u.paused=false;u.simTime=std::chrono::duration_cast<std::chrono::steady_clock::duration>(std::chrono::duration<double>(t));replay.PreUpdate(u,ecm);
   if(i%200==0||i==2202){out<<t;for(auto e:links){auto*p=ecm.Component<gz::sim::components::Pose>(e);if(!p)return 3;const auto&v=p->Data();out<<','<<v.Pos().X()<<','<<v.Pos().Y()<<','<<v.Pos().Z()<<','<<v.Rot().W()<<','<<v.Rot().X()<<','<<v.Rot().Y()<<','<<v.Rot().Z();}out<<'\n';}
  }
  std::cout<<"ECM_CORE_EXECUTION_PASS updates=2203 tracks="<<links.size()<<" (no Gazebo server / no physics)\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
