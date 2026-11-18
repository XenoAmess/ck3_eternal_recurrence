#include "xar_bridge/ck3_1210_date_worker_game_access_v1.hpp"
#include "xar_bridge/ck3_1210.hpp"
#include <Windows.h>
#include <cstdio>
#include <limits>
using namespace xar::ck3_1210;
namespace {
struct Model {
  DateWorkerGameAccessSampleV1 state{0x1000,0x2000,1,0};
  unsigned acquired=0,destroyed=0,bodies=0;
  bool result=true,body_fault=false,acquire_fault=false,no_access=false,descriptor_valid=true;
  bool read_failure=false,destroy_fault=false,change_tls=false;
};
bool Sample(void *p,DateWorkerGameAccessSampleV1 &s) {
  auto &m=*static_cast<Model *>(p);s=m.state;return !m.read_failure;
}
void Acquire(void *p) {
  auto &m=*static_cast<Model *>(p);++m.acquired;
  if(!m.no_access)m.state.native_access=1;
  if(m.acquire_fault)RaiseException(0xE0001210,0,0,nullptr);
}
void Destroy(void *p,void *v) {
  auto &m=*static_cast<Model *>(p);++m.destroyed;
  const auto *d=static_cast<const unsigned char *>(v);
  if(d[0]!=1)m.descriptor_valid=false;
  for(unsigned i=1;i<0x48;++i)if(d[i])m.descriptor_valid=false;
  m.state.native_access=0;
  if(m.destroy_fault)RaiseException(0xE0001211,0,0,nullptr);
}
bool Body(void *p) noexcept {
  auto &m=*static_cast<Model *>(p);++m.bodies;
  if(m.state.native_access!=1 || m.state.command_scope!=1)return false;
  if(m.body_fault)RaiseException(0xE0001212,0,0,nullptr);
  if(m.change_tls)m.state.command_scope=0;
  return m.result;
}
DateWorkerGameAccessBindingsV1 Bind(Model &m) {
  DateWorkerGameAccessBindingsV1 b{};b.offline_fixture=true;
  b.fixture={&m,Sample,Acquire,Destroy};return b;
}
int errors=0;
void Check(bool ok,const char *name) {if(!ok){++errors;std::fprintf(stderr,"FAIL %s\n",name);}}
bool Run(Model &m) {auto b=Bind(m);return WithDateWorkerGameAccessV1(&b,Body,&m);}
}
int main() {
  {Model m;Check(Run(m)&&m.acquired==1&&m.destroyed==1&&m.bodies==1&&
      m.state.native_access==0&&m.descriptor_valid,"owned native pair and exact descriptor");}
  {Model m;m.state.native_access=1;Check(Run(m)&&m.acquired==0&&m.destroyed==0&&
      m.bodies==1&&m.state.native_access==1,"borrow retains outer native scope");}
  {Model m;m.result=false;Check(!Run(m)&&m.acquired==1&&m.destroyed==1&&m.bodies==1,
      "false body releases owned scope");}
  {Model m;m.body_fault=true;Check(!Run(m)&&m.acquired==1&&m.destroyed==1&&m.bodies==1,
      "SEH body releases owned scope");}
  {Model m;m.body_fault=true;m.state.native_access=1;Check(!Run(m)&&m.acquired==0&&m.destroyed==0,
      "SEH borrowed body retains outer scope");}
  {Model m;m.acquire_fault=true;Check(!Run(m)&&m.acquired==1&&m.destroyed==1&&m.bodies==0,
      "acquire final-trace fault pairs committed native access");}
  {Model m;m.no_access=true;Check(!Run(m)&&m.acquired==1&&m.destroyed==0&&m.bodies==0,
      "uncommitted acquire cannot authorize body or fabricated release");}
  {Model m;m.destroy_fault=true;Check(!Run(m)&&m.destroyed==1,"release fault fails closed once");}
  {Model m;m.state.command_scope=0;Check(!Run(m)&&m.acquired==0&&m.bodies==0,
      "scope acquisition cannot mint worker command authority");}
  {Model m;m.state.native_access=2;Check(!Run(m)&&m.acquired==0&&m.bodies==0,"invalid access byte");}
  {Model m;m.state.application=0;Check(!Run(m)&&m.acquired==0&&m.bodies==0,"application required");}
  {Model m;m.read_failure=true;Check(!Run(m)&&m.acquired==0&&m.bodies==0,"unreadable scope");}
  {Model m;m.change_tls=true;Check(!Run(m)&&m.destroyed==1,"body scope drift rejected and released");}
  {Model m;auto b=Bind(m);b.offline_fixture=false;Check(!WithDateWorkerGameAccessV1(&b,Body,&m)&&
      m.acquired==0&&m.bodies==0,"runtime rejects fixture callbacks");}
  {auto b=BindDateWorkerGameAccessImageV1(0x140000000,"wrong");Check(!b.exact_build_admitted,"wrong build");}
  {auto b=BindDateWorkerGameAccessImageV1(std::numeric_limits<std::uintptr_t>::max(),kExecutableSha256);
    Check(!b.exact_build_admitted,"address overflow");}
  Check(!WithDateWorkerGameAccessV1(nullptr,Body,nullptr),"null binding");
  std::printf("native game-access scope cases: %s (%d failures)\n",errors?"FAIL":"PASS",errors);
  return errors?1:0;
}
