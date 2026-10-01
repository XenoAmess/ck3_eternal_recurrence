#include "ck3_12002_construction.hpp"
#include <windows.h>
#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <vector>
namespace {
std::array<std::byte,0x6F600> definition{};
std::array<std::byte,0x20> province{};
std::array<std::byte,0x1E0> actor{};
bool cost_called=false,legal_called=false;
template<class T> void Put(void* data,std::size_t offset,T value) {std::memcpy(static_cast<std::byte*>(data)+offset,&value,sizeof(value));}
void Require(bool good,const char* label) {if(!good)throw std::runtime_error(label);}
bool Legal(std::int32_t a,std::int32_t p,const void* d,std::int32_t s,bool flag,const void* tooltip) {
  legal_called=true;return a==29829&&p==2619&&d==definition.data()&&s==1&&flag&&tooltip==nullptr;
}
std::int64_t* Cost(std::int64_t* output,const void* p,const void* field,const void* context,const void* a) {
  cost_called=p==province.data()&&field==definition.data()+0x6F518&&context==reinterpret_cast<void*>(0xABC000)&&a==actor.data();
  for(int i=0;i<10;++i)output[i]=(i+1)*100000;
  return output;
}
void Trampoline(void* base,std::uintptr_t rva,const void* fn) {
  auto* dst=static_cast<unsigned char*>(base)+rva;
  const std::uintptr_t target=reinterpret_cast<std::uintptr_t>(fn);
  dst[0]=0x48;dst[1]=0xB8;std::memcpy(dst+2,&target,8);dst[10]=0xFF;dst[11]=0xE0;
}
}
int main() {
  using namespace xar::ck3_12002;
  auto* module=VirtualAlloc(nullptr,0x61C5000,MEM_RESERVE|MEM_COMMIT,PAGE_EXECUTE_READWRITE);
  Require(module!=nullptr,"fixture image allocation");
  Trampoline(module,kConstructionCostRva,reinterpret_cast<const void*>(&Cost));
  Trampoline(module,kConstructionFinalLegalityRva,reinterpret_cast<const void*>(&Legal));
  std::array<std::byte,0x30> storage{};
  std::vector<std::byte> slots(30000*0x10);
  Put(storage.data(),0x20,slots.data());Put(storage.data(),0x2C,std::int32_t{30000});
  Put(slots.data(),29829*0x10+8,actor.data());Put(actor.data(),0x18,std::int32_t{29829});
  Put(module,0x5C67568,storage.data());Put(province.data(),0x10,std::int32_t{2619});
  Put(definition.data(),0x10,std::int32_t{22});Put(definition.data(),0x6F510,std::uintptr_t{0xABC000});
  PlayerWorldBuildingNativeCallAccessV1 access{reinterpret_cast<std::uintptr_t>(module),true};
  auto legal=xar::ck3_12002::BindCurrentProcessPlayerWorldBuildingFinalLegalityV1(access);
  auto cost=xar::ck3_12002::BindCurrentProcessPlayerWorldBuildingCostV1(access);
  bool allowed=false;std::array<std::int64_t,10> values{};
  Require(legal&&cost&&legal(&access,29829,2619,reinterpret_cast<std::uintptr_t>(definition.data()),1,allowed)&&allowed&&legal_called,"six native legality arguments");
  Require(cost(&access,29829,2619,reinterpret_cast<std::uintptr_t>(province.data()),22,reinterpret_cast<std::uintptr_t>(definition.data()),1,values)&&cost_called&&values[9]==1000000,"cost fifth argument is resolved actor, 10 signed slots");
  cost_called=false;
  Put(actor.data(),0x18,std::int32_t{29830});
  Require(!cost(&access,29829,2619,reinterpret_cast<std::uintptr_t>(province.data()),22,reinterpret_cast<std::uintptr_t>(definition.data()),1,values)&&!cost_called,"generation mismatch cannot call stock cost");
  access.exact_build_admitted=false;
  Require(xar::ck3_12002::BindCurrentProcessPlayerWorldBuildingCostV1(access)==nullptr,"unsupported build is unbound");
  Require(VirtualFree(module,0,MEM_RELEASE)!=0,"fixture image release");
  std::cout<<"GREEN 1.20 construction native signature fixtures (6 legality / 5 cost arguments)\n";
}
