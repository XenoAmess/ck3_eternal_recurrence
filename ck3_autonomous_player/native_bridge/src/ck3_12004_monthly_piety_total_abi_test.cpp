// Exact4 public binder -> original661B selected total ABI -> complete Root/serializer.
// All memory/frames and lower gross/cost/final terms are owned software inputs.
// No CK3 process, EXE file, pipe, network, DLL deployment or model call is used.
#include <windows.h>
#include <stdexcept>
#include "ck3_12002_campaign_test_support.hpp"
#include "xar_bridge/ck3_12004_campaign.hpp"
#include "xar_bridge/ck3_12004_council_task_owner_monthly_piety.hpp"
#include <filesystem>
#include <limits>

namespace {
namespace actual=xar::ck3_12004;
namespace game=xar::game;
unsigned checks=0;
void Check(bool ok,const char* label) {++checks;if(!ok){std::cerr<<label<<"\n";std::exit(1);}}
struct Complete;
Complete* current=nullptr;
struct Complete {
  Fixture f;
  Blob<0x60> slots{};
  std::array<Blob<0x60>,2> added_tasks{};
  std::array<Blob<0x58>,2> added_types{};
  std::array<Blob<0x40>,2> added_positions{};
  std::array<std::int32_t,5> ids{Fixture::kChancellorTaskId,Fixture::kStewardTaskId,Fixture::kSpymasterTaskId,0x13000004,0x14000005};
  std::array<void*,5> tasks{},types{};
  const std::array<std::string_view,5> keys{"councillor_chancellor","councillor_steward","councillor_spymaster","councillor_court_chaplain","councillor_marshal"};
  std::array<unsigned,5> adapter{},builds{},values{},destroys{};
  std::array<std::int64_t,5> amounts{0,-5000,25000,45000,0};
  std::array<std::array<std::byte,32>,5> scopes{};
  Blob<32> keyword{};
  actual::CampaignRootNativeEnvironmentV1 env{};
  const std::int32_t owner;
  unsigned selected=5,total_calls=0;
  bool total_drift=false,total_missing_second=false,component_drift=false;
  void* owned=nullptr;
  explicit Complete(std::int32_t owner_id=Fixture::kPlayerCharacterId):owner(owner_id) {
    current=this;g_fixture=&f;
    Put(f.player_character,0x18,owner);Put(f.player_entry,0xB0,owner);f.frame.played_character_id=owner;
    Put(f.primary_title,0x128,owner);Put(f.secondary_title,0x128,owner);Put(f.barony_title,0x128,owner);
    const auto slot=static_cast<std::size_t>(static_cast<std::uint32_t>(owner)&0x00FFFFFFU);
    Check(slot<10,"mapped player slot in owned storage");
    if(slot!=1)Put(f.character_slots,0x10+8,static_cast<void*>(nullptr));
    Put(f.character_slots,slot*0x10+8,Address(f.player_character));
    static_cast<xar::ck3_12002::CampaignRootNativeEnvironmentV1&>(env)=Environment(f);
    tasks={Address(f.chancellor_active_task),Address(f.steward_active_task),Address(f.spymaster_active_task),Address(added_tasks[0]),Address(added_tasks[1])};
    types={Address(f.chancellor_task_type),Address(f.steward_task_type),Address(f.spymaster_task_type),Address(added_types[0]),Address(added_types[1])};
    for(std::size_t i=0;i<5;++i) {
      Put(slots,(i+1)*0x10+8,tasks[i]);
      if(i>=3) {
        Put(added_tasks[i-3],0x10,ids[i]);Put(added_tasks[i-3],0x18,types[i]);
        Put(added_tasks[i-3],0x40,Fixture::kTopLiegeId);Put(added_tasks[i-3],0x44,owner);
        Put(added_types[i-3],0x40,Address(added_positions[i-3]));
        f.native_strings[Address(added_positions[i-3],0x18)]=std::string(keys[i]);
        f.native_strings[Address(added_types[i-3],0x18)]="task_"+std::to_string(i);
      }
      std::memcpy(static_cast<std::byte*>(tasks[i])+0x44,&owner,4);
      std::memcpy(scopes[i].data(),static_cast<const std::byte*>(tasks[i])+0x40,32);
    }
    Put(f.active_task_storage,0x20,Address(slots));Put(f.active_task_storage,0x2C,std::int32_t{6});
    Put(f.player_land_state,0x230,ids.data());Put(f.player_land_state,0x23C,std::int32_t{5});
    constexpr std::string_view name="monthly_piety";
    std::memcpy(keyword.data(),name.data(),name.size());Put(keyword,0x10,std::uint64_t{name.size()});Put(keyword,0x18,std::uint64_t{15});
    env.council_position_lookup=&Lookup;env.task_owner_monthly_piety=&Piety;
    env.monthly_piety=&Total;env.province_holder_character_id=&ProvinceHolder;
  }
  static const void* Lookup(const void* owner,const std::string* key) {
    Check(owner==Address(current->f.player_character)&&key,"full getter current owner/key");
    for(std::size_t i=0;i<5;++i) if(*key==current->keys[i]) return current->tasks[i];
    return nullptr;
  }
  static std::int32_t* ProvinceHolder(void* province,std::int32_t* out) noexcept {
    if(province==Address(current->f.province)){*out=current->owner;return out;}
    return ResolveProvinceHolderCharacterId(province,out);
  }
  static const std::string* Keyword(std::int32_t id) {
    Check(id==11117,"piety actual keyword");return reinterpret_cast<const std::string*>(current->keyword.data());
  }
  static void* Build(const void* type,void* out,const void* scopes) {
    Check(type==current->types[current->selected]&&current->owned==nullptr,"full getter leaf type/lifetime");
    Check(std::memcmp(scopes,current->scopes[current->selected].data(),32)==0,"full getter leaf32 scopes");
    ++current->builds[current->selected];current->owned=out;return out;
  }
  static std::int64_t* Value(const void* whole,std::int64_t* out,std::uint16_t id) {
    Check(whole==current->owned&&id==97,"full getter whole numeric");
    const auto i=current->selected;++current->values[i];*out=current->amounts[i];
    if(current->component_drift&&i==3&&current->values[i]>1)++*out;
    return out;
  }
  static void Destroy(void* whole) {Check(whole==current->owned,"full getter destroy aggregate");++current->destroys[current->selected];current->owned=nullptr;}
  static bool Piety(std::uintptr_t,void* type,const void* scopes,std::int64_t& raw) noexcept {
    current->selected=5;for(unsigned i=0;i<5;++i)if(current->types[i]==type)current->selected=i;
    Check(current->selected<5,"full getter original task");++current->adapter[current->selected];
    const auto got=actual::ReadCouncilTaskOwnerMonthlyPiety12004({Build,Value,Destroy,Keyword},type,scopes,ReadMemory,&current->f);
    Check(got.owner_character_id==current->owner,"full getter actual piety owner");
    if(!got.raw)return false;raw=*got.raw;return true;
  }
  static std::int64_t* Total(const void* scope,std::int64_t* raw,void* tooltip) noexcept {
    std::array<std::uintptr_t,2> value{};std::memcpy(value.data(),scope,16);
    Check(value[0]==reinterpret_cast<std::uintptr_t>(Address(current->f.player_character))&&value[1]==0&&tooltip==nullptr,"total piety exact scope actor and empty context");++current->total_calls;
    *raw=-125000;if(current->total_drift&&current->total_calls==2)++*raw;
    return current->total_missing_second&&current->total_calls==2?nullptr:raw;
  }
};
void Save(const std::filesystem::path& path,const game::CampaignRootContextV1& root) {
  const auto wire=actual::SerializeCampaignRootContextV1(root);Check(!wire.empty(),"actual full getter serializer");
  std::ofstream out(path,std::ios::binary);out<<wire;Check(out.good(),"actual full packet write");
}

} // namespace

#include <windows.h>
#include "ck3_12004_monthly_piety_total_test_bytes.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <limits>
#include <stdexcept>

namespace total_software90 {
using Numeric = std::int64_t* (*)(const void*,std::int64_t*,void*);
using Aggregate = std::int64_t* (*)(std::int64_t*,const void*,const void*,void*,void*);
struct Scenario {
  std::array<std::byte,0x1D8> actor{};
  const void* expected_actor=nullptr;
  std::array<std::byte,8> context{};
  std::int64_t gross{},cost{},final_delta{};
  unsigned resolver_calls{},gross_calls{},cost_calls{},final_calls{},cleanup_calls{},unexpected_calls{};
  bool arguments_valid=true;
  std::byte* profile{};
};
Scenario* active=nullptr;
unsigned checks=0;
void Check(bool value,const char* text) {
  ++checks;
  if(!value)throw std::runtime_error(text);
}
template<class T>void Put(Scenario& s,std::size_t offset,T value) {
  std::memcpy(s.actor.data()+offset,&value,sizeof value);
}
const void* Resolve(const void* actor) {
  ++active->resolver_calls;
  active->arguments_valid &= actor==active->expected_actor;
  return active->context.data();
}
std::int64_t* Gross(std::int64_t* out,const void* actor,void* tooltip) {
  ++active->gross_calls;
  active->arguments_valid &= out!=nullptr && actor==active->expected_actor && tooltip==nullptr;
  *out=active->gross;return out;
}
std::int64_t* Cost(std::int64_t* out,const void* actor,const void* context,void* tooltip,void* optional) {
  ++active->cost_calls;
  active->arguments_valid &= out!=nullptr && actor==active->expected_actor && context==active->context.data() && tooltip==nullptr && optional==nullptr;
  *out=active->cost;return out;
}
std::int64_t* Final(std::int64_t* out,const void* actor,const void* context,std::int64_t raw,const void* profile,void* tooltip) {
  ++active->final_calls;
  active->arguments_valid &= out!=nullptr && actor==active->expected_actor && context==active->context.data() && raw==active->gross-active->cost && profile==active->profile && tooltip==nullptr;
  *out=raw+active->final_delta;return out;
}
void Cleanup(void*) {++active->cleanup_calls;}
std::int64_t* Unexpected(std::int64_t* out) {
  ++active->unexpected_calls;
  return out;
}
class OwnedCode {
  std::byte* memory_{};
  static constexpr std::size_t kSize=4096;
  std::size_t thunk_=2048;
 public:
  std::byte* numeric{};
  std::byte* aggregate{};
  std::byte* profile{};
  OwnedCode() {
    memory_=static_cast<std::byte*>(VirtualAlloc(nullptr,kSize,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
    if(!memory_)throw std::runtime_error("VirtualAlloc owned fixture");
    numeric=memory_;aggregate=memory_+512;profile=memory_+1024;
    std::memcpy(numeric,exact4_total_bytes90::numeric.data(),exact4_total_bytes90::numeric.size());
    std::memcpy(aggregate,exact4_total_bytes90::aggregate.data(),exact4_total_bytes90::aggregate.size());
    std::memcpy(profile,exact4_total_bytes90::profile.data(),exact4_total_bytes90::profile.size());
    // All exact numeric external direct calls are patched. Only tag0 is entered.
    Call(numeric,0x63,&Resolve);Call(numeric,0x74,&Unexpected);
    Call(numeric,0x92,&Resolve);Call(numeric,0xA3,&Unexpected);
    Call(numeric,0x141,&Unexpected);Call(numeric,0x15F,&Resolve);
    Call(numeric,0x179,&Unexpected);Call(numeric,0x197,&Resolve);
    DirectCall(numeric,0x1B1,aggregate);
    Call(aggregate,0x53,&Gross);Call(aggregate,0x6B,&Cost);
    Call(aggregate,0x97,&Final);Call(aggregate,0xA4,&Cleanup);
    // Exact aggregate RIP-relative profile reference is retargeted into owned data.
    Relative(aggregate+0x8B+3,aggregate+0x8B+7,profile);
    DWORD old=0;
    if(!VirtualProtect(memory_,kSize,PAGE_EXECUTE_READ,&old) || !FlushInstructionCache(GetCurrentProcess(),memory_,kSize))
      throw std::runtime_error("Owned fixture executable protection");
  }
  OwnedCode(const OwnedCode&)=delete;
  OwnedCode& operator=(const OwnedCode&)=delete;
  ~OwnedCode(){if(memory_)VirtualFree(memory_,0,MEM_RELEASE);}
  static void Relative(std::byte* operand,const std::byte* after,const std::byte* target) {
    const auto delta=target-after;
    if(delta<std::numeric_limits<std::int32_t>::min() || delta>std::numeric_limits<std::int32_t>::max())throw std::runtime_error("fixture rel32 overflow");
    const auto value=static_cast<std::int32_t>(delta);
    std::memcpy(operand,&value,sizeof value);
  }
  void DirectCall(std::byte* code,std::size_t offset,std::byte* target) {
    if(code[offset]!=std::byte{0xE8})throw std::runtime_error("Expected exact call instruction");
    Relative(code+offset+1,code+offset+5,target);
  }
  template<class Function>void Call(std::byte* code,std::size_t offset,Function function) {
    if(thunk_+12>kSize)throw std::runtime_error("Fixture thunk capacity");
    auto* stub=memory_+thunk_;thunk_+=16;
    stub[0]=std::byte{0x48};stub[1]=std::byte{0xB8};
    const auto address=reinterpret_cast<std::uintptr_t>(function);
    std::memcpy(stub+2,&address,8);stub[10]=std::byte{0xFF};stub[11]=std::byte{0xE0};
    DirectCall(code,offset,stub);
  }
  Numeric Get()const{return reinterpret_cast<Numeric>(numeric);}
};

}


int main(int argc,char** argv) {
  try {
    if(argc!=2)return 2;
    const std::filesystem::path dir=argv[1];std::filesystem::create_directories(dir);
    total_software90::OwnedCode code;
    constexpr std::array<std::int32_t,3> owners{0,std::numeric_limits<std::int32_t>::min(),std::numeric_limits<std::int32_t>::min()+1};
    constexpr std::array<std::int64_t,3> gross{200000,0,50000},cost{100000,125000,100000},delta{-100000,0,75000};
    for(std::size_t scene=0;scene<owners.size();++scene) {
      Complete fixture(owners[scene]);
      Put(fixture.f.player_character,0x1C,std::uint32_t{0x43686172});
      total_software90::Scenario terms;
      terms.expected_actor=Address(fixture.f.player_character);terms.profile=code.profile;
      terms.gross=gross[scene];terms.cost=cost[scene];terms.final_delta=delta[scene];
      total_software90::active=&terms;
      const auto software_base=reinterpret_cast<std::uintptr_t>(code.numeric)-0x2696F20;
      const auto bound=actual::BindCampaignRootNativeEnvironmentV1(software_base,actual::kExecutableSha256);
      Check(bound.monthly_piety==code.Get(),"candidate public binder chooses actual4 total numeric RVA");
      fixture.env.monthly_piety=bound.monthly_piety;
      game::CampaignRootContextV1 root;
      const auto result=actual::ReadCampaignRootContextV1(fixture.env,Access(fixture.f),{41},root);
      Check(result==game::ReadCampaignRootContextResultV1::available&&root.readiness.ready,"full getter reads mapped native total bodies");
      Check(root.player_character_id==owners[scene]&&root.council&&root.council->owner_character_id==owners[scene],"mapped full player identity remains signed");
      Check(root.player_monthly_piety_v1&&root.player_monthly_piety_v1->raw==gross[scene]-cost[scene]+delta[scene]&&root.player_monthly_piety_v1->scale==100000,"native total is final net in full Root");
      Check(terms.resolver_calls==2&&terms.gross_calls==2&&terms.cost_calls==2&&terms.final_calls==2&&terms.cleanup_calls==0&&terms.unexpected_calls==0&&terms.arguments_valid,"two full native total ABI lifecycles");
      for(unsigned i=0;i<5;++i)Check(fixture.builds[i]==2&&fixture.values[i]==2&&fixture.destroys[i]==2,"two independent current task component lifecycles");
      Check(fixture.f.capture_calls==2&&fixture.owned==nullptr,"full frame bookends and aggregate cleanup");
      Save(dir/("native-total-full-root-"+std::to_string(scene)+".json"),root);
    }
    std::cout<<"full_root_native_total_checks="<<checks<<" scenes=3 full_getter_calls=3 actual_numeric_bytes=457 actual_aggregate_bytes=204 lower_terms=synthetic game_calls=0\n";
    return 0;
  }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
