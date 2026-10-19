#include "xar_bridge/activity_typed_full_cost_v1.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <windows.h>
#include <array>
#include <cstdlib>
#include <cstring>
#include <map>
#include <string_view>

namespace {
using namespace xar::bridge;
constexpr std::uintptr_t B=0x180000000ULL, R=0x700010000ULL;
constexpr std::uintptr_t I=R+0x1000,G=R+0x2000,H=R+0x3000,P=R+0x4000;
constexpr std::uintptr_t T=R+0x5000,S=R+0x6000,L=R+0x7000,A=R+0x8000;
constexpr std::uintptr_t HOST=R+0x9000,KEY=R+0xA000,ROWS=R+0xB000;
constexpr std::array<std::uint32_t,4> NATIVE_INDEX{3,2,0,4};
constexpr std::int32_t ACTOR=0x01000001;
void Need(bool value) { if(!value) std::abort(); }

struct Fixture {
  std::map<std::uintptr_t,unsigned char> memory{};
  ActivityPlannerDiagFrameV1 frame{51,43800000,ACTOR,true,true,true,true};
  ActivityCostSlot12ObserverV1 observer{};
  std::array<std::int64_t,10> totals{300000,0,0,18500000,0,0,0,0,0,0};
  int named_calls=0,canstart_calls=0,selection_calls=0;
  bool final_allowed=true,final_failed=false,named_mismatch=false;
  bool named_unknown=false,named_duplicate=false,mutate_configuration=false;
  bool mutate_selection=false,mutate_total=false,mutate_revision=false;
  std::uintptr_t unreadable=0;
  template<class V> void Put(std::uintptr_t at,const V &value) {
    const auto *bytes=reinterpret_cast<const unsigned char *>(&value);
    for(std::size_t i=0;i<sizeof(value);++i) memory[at+i]=bytes[i];
  }
  void Zero(std::uintptr_t at,std::size_t size) {
    for(std::size_t i=0;i<size;++i) memory[at+i]=0;
  }
  void Bytes(std::uintptr_t at,const void *data,std::size_t size) {
    const auto *bytes=static_cast<const unsigned char *>(data);
    for(std::size_t i=0;i<size;++i) memory[at+i]=bytes[i];
  }
  void Code(std::uintptr_t rva,std::initializer_list<unsigned char> data) {
    Bytes(B+rva,data.begin(),data.size());
  }
  void Type(std::string_view key) {
    Zero(T+0x18,0x20); Put(T,B+0x48BFE60);
    if(key.size()>15) { Put(T+0x18,KEY);Bytes(KEY,key.data(),key.size()); }
    else Bytes(T+0x18,key.data(),key.size());
    Put(T+0x28,std::uint64_t{key.size()});
    Put(T+0x30,std::uint64_t{key.size()>15?31U:15U});
  }
  void Total(std::size_t index,std::int64_t value) {
    totals[index]=value;Put(P+0x1B10+index*8,value);
  }
  Fixture();
  void Record() { Need(RecordActivityCostSlot12NormalReturnV1(observer,B+0x11B5B3F,P)); }
  ActivityTypedFullCostEnvironmentV1 Environment();
  ActivityTypedFullCostResultV1 Read() {
    return ReadActivityTypedPlannerFullCostV1(Environment(),frame,
        kOrdinaryPilgrimagePiousContractV1);
  }
};
bool Memory(void *opaque,std::uintptr_t address,void *out,std::size_t size) noexcept {
  auto &f=*static_cast<Fixture *>(opaque);
  if(!out || !size || address==f.unreadable) return false;
  auto *bytes=static_cast<unsigned char *>(out);
  for(std::size_t i=0;i<size;++i) {
    const auto at=f.memory.find(address+i);if(at==f.memory.end()) return false;
    bytes[i]=at->second;
  }
  return true;
}
bool Frame(void *opaque,ActivityPlannerDiagFrameV1 &out) noexcept {
  out=static_cast<Fixture *>(opaque)->frame;return true;
}
bool CostFrame(void *opaque,ActivityCostSlot12FrameV1 &out) noexcept {
  const auto &f=*static_cast<Fixture *>(opaque);
  out={static_cast<std::int32_t>(f.frame.date_raw),ACTOR,GetCurrentThreadId(),true};
  return true;
}
std::uintptr_t Cast(void *,std::uintptr_t from,std::uintptr_t source,
                    std::uintptr_t target) noexcept {
  return from==I && source==B+0x5514438 && target==B+0x5514460?G:0;
}
bool Visible(void *,std::uintptr_t planner,std::uintptr_t entry,bool &out) noexcept {
  out=planner==P && entry==B+0x2160380;return out;
}
bool Selection(void *opaque,const ActivityPlannerDiagFrameV1 &expected,
                std::int32_t stage,ActivityTypedPlannerSelectionV1 &out) noexcept {
  auto &f=*static_cast<Fixture *>(opaque);++f.selection_calls;
  if(expected!=f.frame || stage!=5) return false;
  out={};out.observed=true;out.kind=kOrdinaryPilgrimagePiousContractV1.kind;
  out.frame=f.frame;out.planner=P;out.activity_type=T;out.planning_stage=stage;
  out.native_selected_option=R+0xC000;out.native_option_id=17;
  const std::string_view key=f.mutate_selection && f.selection_calls>1?
      "pilgrimage_type_worldly":"pilgrimage_type_pious";
  std::memcpy(out.option_key.data(),key.data(),key.size());
  out.option_key_size=static_cast<std::uint16_t>(key.size());return true;
}
bool Named(void *opaque,std::uintptr_t base,std::uintptr_t breakdown,
            std::string_view key,std::uint32_t &index,std::int64_t &value) noexcept {
  auto &f=*static_cast<Fixture *>(opaque);++f.named_calls;
  if(base!=B || breakdown!=P+0x1B10) return false;
  for(std::size_t n=0;n<kActivityTypedPlannerKnownCostNamesV1.size();++n) {
    if(key!=kActivityTypedPlannerKnownCostNamesV1[n]) continue;
    index=f.named_unknown?10:NATIVE_INDEX[n];
    if(f.named_duplicate && n==1) index=NATIVE_INDEX[0];
    value=index<10?f.totals[index]:0;
    if(f.named_mismatch) ++value;
    if(f.mutate_configuration && n==0) f.memory[ROWS+8]^=1;
    return true;
  }
  return false;
}
bool CanStart(void *opaque,std::uintptr_t planner,bool &out) noexcept {
  auto &f=*static_cast<Fixture *>(opaque);++f.canstart_calls;
  if(planner!=P || f.final_failed) return false;
  if(f.mutate_total) f.Total(3,f.totals[3]+1);
  if(f.mutate_revision) ++f.frame.revision;
  out=f.final_allowed;return true;
}
int owned_string_destroy_calls=0;
bool DeniedLongNativeString(void *,void *string) {
  // A bool-only reader must not dereference this pointer or reject the bool
  // merely because the (owned) native failure text exceeds a copy buffer.
  const std::uintptr_t sentinel=1;
  const std::uint64_t long_size=20000;
  auto *bytes=static_cast<unsigned char *>(string);
  std::memcpy(bytes,&sentinel,sizeof(sentinel));
  std::memcpy(bytes+16,&long_size,sizeof(long_size));
  std::memcpy(bytes+24,&long_size,sizeof(long_size));return false;
}
void DestroyLongNativeString(void *) { ++owned_string_destroy_calls; }
Fixture::Fixture() {
  Code(0x11B2865,{0x49,0x89,0xB4,0x24,0xA0,0,0,0});
  Code(0x216038A,{0x48,0x8B,0x59,0x60});
  Code(0x11B8673,{0x48,0x63,0x81,0xE8,0x1A,0,0});
  Code(0x11B8650,{0x48,0x89,0x5C,0x24,0x10,0x48,0x89});
  Code(0x11B88C8,{0x48,0x8D,0x91,0x00,0x15,0,0});
  Code(0x310ADF0,{0x48,0x89,0x5C,0x24,0x18,0x56,0x57,0x41,0x56,0x48,0x83,0xEC,0x30});
  Code(0x310AEC5,{0x49,0x8B,0x0C,0xC6});
  Put(B+0x45325D8,B+0x11B2E10);Put(B+0x45325D8+7*8,B+0x2160380);
  Put(B+0x45325D8+11*8,B+0xB1F0A0);Put(B+0x45325D8+12*8,B+0x11B5B10);
  Put(B+0x45326B0,B+0x11D33E4);Put(B+0x5C6A520,R);Put(R+0x10,I);
  Put(G,B+0x44BC418);Put(G+0x88,H);Put(H,B+0x44BA8A0);
  Put(H+0x3C0,P);Put(H+0x3D8,HOST);Put(B+0x54DBC00,ACTOR);
  Put(B+0x5C67568,S);Put(B+0x5C67570,std::uintptr_t{0});
  Put(S+0x20,L);Put(S+0x2C,std::int32_t{2});Put(L+0x18,A);Put(A+0x18,ACTOR);
  Zero(P+0x1500,0x610);Put(P,B+0x45325D8);Put(P+0x10,B+0x45326B0);
  Put(P+0x60,R+0xD000);Put(P+0xA0,H);Put(P+0x1500,T);
  Put(P+0x1AE8,std::int32_t{5});Put(P+0x15B0,ROWS);
  Put(P+0x15BC,std::int32_t{1});Zero(ROWS,0x38);
  Put(HOST,B+0x457A148);Put(HOST+0x10,B+0x457A120);
  Put(HOST+0xA0,H);Put(HOST+0xD0,ACTOR);Put(HOST+0x238,T);
  Type("activity_pilgrimage");
  for(std::size_t i=0;i<10;++i) {
    Total(i,totals[i]);
    Put(P+0x1B10+0x50+i*0x90+0x78,std::int64_t{i==3?10000000:0});
  }
  observer.environment={true,false,xar::ck3_12004::kExecutableSha256,B,this,
                         &Memory,&CostFrame,&kOrdinaryPilgrimagePiousContractV1};
  observer.installed=true;Record();
}
ActivityTypedFullCostEnvironmentV1 Fixture::Environment() {
  ActivityTypedFullCostEnvironmentV1 out{};out.enabled=true;
  out.diagnostic={true,xar::ck3_12004::kExecutableSha256,B,this,
                  &Memory,&Frame,&Cast,&Visible};
  out.passive_cost=&observer;out.read_selection=&Selection;out.selection_context=this;
  out.invoke_named_cost=&Named;out.named_context=this;
  out.evaluate_final_can_start=&CanStart;out.can_start_context=this;return out;
}
} // namespace

int main() {
  { bool allowed=true;Need(InvokeActivityTypedPlannerCanStartBoolOwnedV1(
        reinterpret_cast<void *>(P),&DeniedLongNativeString,
        &DestroyLongNativeString,allowed));
    Need(!allowed && owned_string_destroy_calls==1); }
  { Fixture f;const auto r=f.Read();Need(r.status==ActivityTypedFullCostStatusV1::observed);
    Need(r.quote.observed && r.quote.final_can_start_observed && r.quote.final_can_start);
    Need(r.quote.configured_cost_raw==f.totals && r.quote.known_name_resource_indices==NATIVE_INDEX);
    Need(r.quote.configured_cost_raw[3]!=r.quote.diagnostic_aggregate_raw[3]);
    Need(!r.unknown_positive_configured_cost && !r.quote.failure_display_known);
    Need(f.named_calls==4 && f.canstart_calls==1); }
  { Fixture f;auto e=f.Environment();e.enabled=false;
    Need(ReadActivityTypedPlannerFullCostV1(e,f.frame,kOrdinaryPilgrimagePiousContractV1).status==
      ActivityTypedFullCostStatusV1::disabled_or_exact_build_rejected);Need(f.named_calls==0); }
  { Fixture f;f.Put(H+0x3D8,std::uintptr_t{0});
    Need(f.Read().status==ActivityTypedFullCostStatusV1::planner_or_type_mismatch);Need(f.named_calls==0); }
  { Fixture f;f.observer.environment.typed_contract=nullptr;
    Need(f.Read().status==ActivityTypedFullCostStatusV1::passive_observer_contract_mismatch); }
  { Fixture f;f.observer.latest.sequence=0;
    Need(f.Read().status==ActivityTypedFullCostStatusV1::no_normal_refresh); }
  { Fixture f;f.unreadable=P+0x1B10+9*8;
    Need(f.Read().status==ActivityTypedFullCostStatusV1::configured_cost_unreadable); }
  { Fixture f;f.named_unknown=true;
    Need(f.Read().status==ActivityTypedFullCostStatusV1::named_cost_unmapped); }
  { Fixture f;f.named_duplicate=true;
    Need(f.Read().status==ActivityTypedFullCostStatusV1::named_cost_duplicate_index); }
  { Fixture f;f.named_mismatch=true;
    Need(f.Read().status==ActivityTypedFullCostStatusV1::named_cost_indexed_disagreement); }
  { Fixture f;f.final_failed=true;
    Need(f.Read().status==ActivityTypedFullCostStatusV1::final_can_start_failed); }
  { Fixture f;f.final_allowed=false;const auto r=f.Read();
    Need(r.status==ActivityTypedFullCostStatusV1::observed && !r.quote.final_can_start); }
  { Fixture f;f.mutate_configuration=true;
    Need(f.Read().status==ActivityTypedFullCostStatusV1::configuration_changed); }
  { Fixture f;f.mutate_selection=true;
    Need(f.Read().status==ActivityTypedFullCostStatusV1::configuration_changed); }
  { Fixture f;f.mutate_total=true;
    Need(f.Read().status==ActivityTypedFullCostStatusV1::configuration_changed); }
  { Fixture f;f.mutate_revision=true;
    Need(f.Read().status==ActivityTypedFullCostStatusV1::configuration_changed); }
  { Fixture f;f.Total(9,200000);const auto r=f.Read();
    Need(r.status==ActivityTypedFullCostStatusV1::observed && r.unknown_positive_configured_cost);
    Need(!r.quote.named_cost_verified[9] && r.quote.configured_cost_raw[9]==200000); }
  { Fixture f;f.Total(9,-200000);const auto r=f.Read();
    Need(r.status==ActivityTypedFullCostStatusV1::observed && !r.unknown_positive_configured_cost);
    Need(!r.quote.named_cost_verified[9] && r.quote.configured_cost_raw[9]==-200000); }
  { Fixture f;f.observer.environment.typed_contract=nullptr;
    Need(!RecordActivityCostSlot12NormalReturnV1(f.observer,B+0x11B5B3F,P));
    f.Type("activity_feast");Need(RecordActivityCostSlot12NormalReturnV1(f.observer,B+0x11B5B3F,P)); }
  { Fixture f;f.Put(P+0x15BC,std::int32_t{129});
    Need(!RecordActivityCostSlot12NormalReturnV1(f.observer,B+0x11B5B3F,P)); }
  return 0;
}
