#include "xar_bridge/ck3_12004_snapshot_foundation.hpp"
#include <array>
#include <bit>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <cstdlib>
#include <stdexcept>
#include <windows.h>
namespace {
template<class T> void Put(void *p, std::size_t offset, T value) { std::memcpy(static_cast<std::byte *>(p)+offset,&value,sizeof(value)); }
void Require(bool value, const char *message) { if(!value)throw std::runtime_error(message); }
struct World {
  std::array<std::byte,0x30> storage{};
  std::array<std::byte,0x1D8> character{};
  std::array<std::byte,0x300> extension{};
  void *storage_pointer=storage.data(),*slots=nullptr;
  xar::ck3_12004::CoreBindings core{};
  explicit World(std::int32_t id) {
    slots=VirtualAlloc(nullptr,0x10000000,MEM_RESERVE,PAGE_NOACCESS);Require(slots!=nullptr,"owned slot reserve");
    SYSTEM_INFO info{};GetSystemInfo(&info);
    const auto at=(static_cast<std::uint32_t>(id)&0xFFFFFFU)*16ULL+8;
    const auto page=at-at%info.dwPageSize;
    Require(VirtualAlloc(static_cast<std::byte *>(slots)+page,info.dwPageSize,MEM_COMMIT,PAGE_READWRITE)!=nullptr,"owned slot commit");
    Put(slots,static_cast<std::size_t>(at),character.data());Put(character.data(),0x18,id);
    Put(character.data(),0x1B0,extension.data());Put(storage.data(),0x20,slots);Put(storage.data(),0x2C,std::int32_t{0x1000000});
    Put(extension.data(),0x100,std::int64_t{-200000});Put(extension.data(),0x130,std::int64_t{900000});
    Put(extension.data(),0x110,std::int64_t{500000});Put(extension.data(),0x2F8,std::int32_t{7});
    core.enabled=true;core.character_storage_slot=&storage_pointer;
  }
  ~World(){if(slots)VirtualFree(slots,0,MEM_RELEASE);}
};
}
// Unused source-closure leaves only: these abort if resource-only coverage
// accidentally enters a full foundation factory or settlement path.
namespace xar::ck3_12004::person_events {
Bindings BindImage(std::uintptr_t, std::string_view) noexcept { std::abort(); }
}
namespace xar::ck3_12002 {
SettlementReadResult ReadSettlement(const SettlementBindings &, const CoreBindings &, game::Snapshot &) noexcept { std::abort(); }
}
namespace {
bool Memory(void *,std::uintptr_t at,void *out,std::size_t size) noexcept {
  SIZE_T copied=0;return ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void *>(at),out,size,&copied)!=FALSE&&copied==size;
}
using Values=xar::ck3_12002::ActorResourceBalances12002;
using Domain=xar::ck3_12002::ActorResourceCharacterDomain12002;
bool Shared(World &world,std::int32_t id,Domain domain,Values &out){
  return xar::ck3_12002::ReadActorResourceBalances12002(&Memory,nullptr,reinterpret_cast<std::uintptr_t>(world.character.data()),id,domain,out);
}
}
int main(int argc,char **argv){
  try{
    Require(argc==2,"output argument");const std::filesystem::path out(argv[1]);std::filesystem::create_directories(out);
    int semantic_checks=0;
    const auto check=[&](bool value,const char *message){++semantic_checks;Require(value,message);};
    const Values expected{-200000,900000,500000,7},untouched{91,92,93,94};
    std::string rows="[";bool first=true;
    for(const auto id:{std::int32_t{-2},std::int32_t{0},std::int32_t{0x03000002}}){
      World world(id);Values values{};
      check(xar::ck3_12004::ResolveCoreCharacter(world.core,id)==world.character.data(),"real actual4 full resolver identity");
      check(xar::ck3_12004::ReadActorResourceBalances(world.core,id,values)&&values==expected,"actual4 true resource reader returns all signed balances and observed stress for canonical full ID");
      if(!first)rows+=',';first=false;rows+="{\"full_id\":"+std::to_string(id)+",\"resource_read\":true,\"gold_raw\":"+std::to_string(values.gold_raw)+",\"stress_points\":"+std::to_string(values.stress_points)+"}";
      Values old=untouched;
      const bool legacy=xar::ck3_12002::ReadActorResourceBalances12002(&Memory,nullptr,reinterpret_cast<std::uintptr_t>(world.character.data()),id,old);
      check(legacy==(id>0)&&(legacy?old==expected:old==untouched),"old five-argument .2/.3 entry remains positive and failed output unchanged");
      Put(world.character.data(),0x1B0,static_cast<void *>(nullptr));values=untouched;
      check(xar::ck3_12004::ReadActorResourceBalances(world.core,id,values)&&values==Values{},"actual4 canonical null extension is lawful observed zero");
    }
    for(const auto id:{std::int32_t{-2},std::int32_t{0}}){
      World world(id);Put(world.character.data(),0x18,std::bit_cast<std::int32_t>(static_cast<std::uint32_t>(id)^0x01000000U));
      check(xar::ck3_12004::ResolveCoreCharacter(world.core,id)==nullptr,"same slot other generation does not resolve");
      Values values=untouched;
      check(!xar::ck3_12004::ReadActorResourceBalances(world.core,id,values)&&values==Values{},"actual4 failed full-ID wrapper keeps original clear-output contract");
      values=untouched;
      check(!Shared(world,id,Domain::canonical_signed_full32,values)&&values==untouched,"canonical shared leaf rejects generation mismatch without changing output");
    }
    World world(0);Values values=untouched;
    check(!Shared(world,-1,Domain::canonical_signed_full32,values)&&values==untouched,"canonical -1 sentinel rejected and output preserved");
    check(!Shared(world,0,static_cast<Domain>(255),values)&&values==untouched,"unknown explicit domain rejected without changing output");
    Put(world.character.data(),0x1B0,reinterpret_cast<void *>(std::uintptr_t{1}));values=untouched;
    check(!Shared(world,0,Domain::canonical_signed_full32,values)&&values==untouched,"actual failed native memory read preserves output");
    rows+=']';std::ofstream file(out/"RESOURCE-CANDIDATE-ACTUAL.json",std::ios::binary);
    file<<"{\"machine_id\":\"xenoamess-full-tower-eb9d2c1186\",\"schema\":\"isolated-resource-producer-observations-not-business-snapshot\",\"semantic_checks\":"<<semantic_checks<<",\"failed\":0,\"legacy_positive_preserved\":true,\"actual4_explicit_canonical_domain\":true,\"rows\":"<<rows<<"}\n";file.close();Require(file.good(),"candidate actual metadata saved");
    std::cout<<"RESOURCE_CANDIDATE_CHECKS "<<semantic_checks<<" FAILED 0; actual4 resolver/resource/shared real reads; .2/.3 old positive entry preserved; zero/fullgeneration/sentinel/null/output semantics covered; Game NOT_RUN\n";
    return 0;
  }catch(const std::exception &error){std::cerr<<"ERROR "<<error.what()<<'\n';return 1;}
}
