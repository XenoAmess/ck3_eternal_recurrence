// Actual production reader included verbatim; owned native-layout memory only.
#include "ck3_12004_campaign.cpp"
#include <stdexcept>

// Unrelated full-TU dependencies are fatal sentinels, never exercised by this
// reader. No campaign-metrics or Council behavior is claimed by this fixture.
namespace xar::ck3_12004 {
bool ReadCampaignRootTaskOwnerMonthlyPiety12004(
    std::uintptr_t,void *,const void *,std::int64_t &) noexcept {std::abort();}
}
namespace xar::ck3_12002 {
game::CampaignRootMaxMonthlyGoldMaintenanceV1 ReadOptionalMaxMonthlyGoldMaintenance12003(
    ck3_11906::NativeCampaignRootMaxMonthlyMaintenanceV1,void *) noexcept {std::abort();}
}

namespace {
namespace r = xar::ck3_12004::campaign_root_detail::realm_detail;
using Detail = xar::ck3_12002::HeldTitlePartitionFailure12002;
template<size_t N> using Blob = std::array<std::byte,N>;
template<class B,class T> void Put(B &b,size_t o,T v) {std::memcpy(b.data()+o,&v,sizeof(v));}
struct Fixture;
Fixture *active{};
void *Liege(void *p);
std::int32_t *Holder(void *p,std::int32_t *out);
struct Fixture {
  static constexpr std::int32_t player=0x01000001, external=0x02000002, dead=0x03000003;
  Blob<0x150> data{};
  Blob<0x30> store{};
  Blob<0x80> slots{};
  std::array<Blob<0x1D8>,3> chars{};
  std::array<Blob<0x20>,4> provinces{};
  std::array<Blob<0x60>,4> nodes{};
  std::array<void*,5> province_ptrs{};
  std::array<Blob<0x60>,4> rows{};
  std::array<std::int32_t,5> holders{-1,player,external,dead,external};
  void *store_ptr=store.data(), *fallback=nullptr;
  const void *denied=nullptr;
  bool bad_holder_return=false;
  xar::ck3_12004::CampaignRootNativeEnvironmentV1 env{};
  xar::ck3_12004::CampaignRootAccessV1 access{};
  r::ObservationV1 observed{};
  Detail detail{};
  std::vector<std::pair<const void*,size_t>> spans;
  template<class B> void Span(B &b) {spans.emplace_back(b.data(),b.size()*sizeof(typename B::value_type));}
  Fixture() {
    active=this;
    Put(data,0x140,province_ptrs.data()); Put(data,0x14C,std::int32_t{5});
    Put(store,0x20,slots.data()); Put(store,0x2C,std::int32_t{8});
    for(size_t i=0;i<chars.size();++i) {
      Put(chars[i],0x18,std::array<std::int32_t,3>{player,external,dead}[i]);
      Put(slots,(i+1)*0x10+8,chars[i].data()); Span(chars[i]);
    }
    // Valid, positively observed dead character: it is not a live neighbor.
    Put(chars[2],0x1D0,chars[2].data());
    for(size_t i=0;i<4;++i) {
      province_ptrs[i+1]=provinces[i].data();
      Put(provinces[i],0x10,static_cast<std::int32_t>(i+1));
      Put(provinces[i],0x08,nodes[i].data());
      Put(nodes[i],0x50,rows[i].data()); Put(nodes[i],0x5C,std::int32_t{0});
      Span(provinces[i]); Span(nodes[i]); Span(rows[i]);
    }
    Put(nodes[0],0x5C,std::int32_t{2});
    Put(rows[0],0,std::int32_t{0}); Put(rows[0],4,std::int32_t{2});
    Put(rows[0],0x30,std::int32_t{1}); Put(rows[0],0x34,std::int32_t{3});
    Span(data);Span(store);Span(slots);Span(province_ptrs);
    spans.emplace_back(&store_ptr,sizeof(store_ptr));spans.emplace_back(&fallback,sizeof(fallback));
    env.character_storage_slot=&store_ptr; env.character_fallback_slot=&fallback;
    env.immediate_liege=&Liege; env.province_holder_character_id=&Holder;
    access.context=this;
    access.read_memory=[](void *raw,const void *src,void *dst,size_t bytes) noexcept {
      auto &f=*static_cast<Fixture*>(raw);
      if(src==f.denied)return false;
      const auto p=reinterpret_cast<std::uintptr_t>(src);
      for(const auto &[base,size]:f.spans) {
        const auto begin=reinterpret_cast<std::uintptr_t>(base);
        if(p>=begin && bytes<=size && p-begin<=size-bytes) {
          std::memcpy(dst,src,bytes);return true;
        }
      }
      return false;
    };
    observed.game_data=data.data();observed.player_character=chars[0].data();
    observed.player_character_id=player;
    detail.sample=2;detail.actor_id=player;
  }
  bool Run() {return r::ReadAdjacentExternalProvinceHolders(env,access,observed,&detail);}
};
void *Liege(void *p) {return p;}
std::int32_t *Holder(void *p,std::int32_t *out) {
  std::int32_t id{};std::memcpy(&id,static_cast<std::byte*>(p)+0x10,sizeof(id));
  *out=active->holders[static_cast<size_t>(id)];
  return active->bad_holder_return?nullptr:out;
}
unsigned checks{};
void Check(bool b,const char *s) {++checks;if(!b)throw std::runtime_error(s);}
std::string report;
}

extern "C" __declspec(dllexport) const char *RunRootAdjacencyFocused() {
  try {
    {Fixture f;const bool ok=f.Run();
     if(!ok)throw std::runtime_error(std::string(f.detail.guard)+":"+std::string(f.detail.resolver_guard)+":"+std::to_string(f.detail.index));
     Check(ok,"readable dead holder must not poison root");
     Check(f.observed.adjacent_external_province_holder_character_ids==std::vector<std::int32_t>{Fixture::external},"only actual living neighbor retained");
     Check(f.detail.guard.empty(),"no failure diagnostic on success");}
    {Fixture f;f.holders[3]=-1;Check(f.Run(),"existing unowned province behavior unchanged");}
    {Fixture f;f.holders[3]=Fixture::external;Check(f.Run(),"duplicate living neighbors deduplicated");
     Check(f.observed.adjacent_external_province_holder_character_ids.size()==1,"dedup output");}
    {Fixture f;Put(f.chars[1],0x18,std::int32_t{0x05000002});
     Check(!f.Run() && f.detail.guard=="adjacent_holder_component_unavailable" && f.detail.resolver_guard=="generation_mismatch" && f.detail.index==2,"generation mismatch fails with exact resolver guard");}
    {Fixture f;f.denied=f.chars[2].data()+0x1D0;
     Check(!f.Run() && f.detail.guard=="adjacent_holder_death_marker_read" && f.detail.index==3,"unreadable death is not dead");}
    {Fixture f;Put(f.provinces[3],0x10,std::int32_t{999});
     Check(!f.Run() && f.detail.guard=="adjacent_province_identity_mismatch" && f.detail.index==4,"remote invalid province still fails");}
    {Fixture f;f.denied=f.provinces[1].data()+0x10;
     Check(!f.Run() && f.detail.guard=="adjacent_province_identity_read" && f.detail.index==2,"identity read failure still fails");}
    {Fixture f;f.bad_holder_return=true;
     Check(!f.Run() && f.detail.guard=="adjacent_province_holder_resolver" && f.detail.index==1,"stock holder call failure still fails");}
    {Fixture f;f.province_ptrs[2]=nullptr;
     Check(!f.Run() && f.detail.guard=="adjacent_target_province_missing" && f.detail.index==1,"missing referenced target is not skipped");}
    {Fixture f;Put(f.rows[0],0,std::int32_t{4});
     Check(!f.Run() && f.detail.guard=="adjacent_row_kind_bounds" && f.detail.index==1,"unknown adjacency kind still fails");}
    {Fixture f;f.holders[4]=0;
     Check(!f.Run() && f.detail.guard=="adjacent_holder_id_invalid" && f.detail.index==4,"invalid holder ID not treated unowned");}
    {Fixture f;Put(f.chars[1],0x1D0,f.chars[1].data());
     Check(f.Run() && f.observed.adjacent_external_province_holder_character_ids.empty(),"all positively dead external holders produce truthful empty live set");}
    report="{\"status\":\"GREEN\",\"checks\":"+std::to_string(checks)+",\"fixture_only\":true}";
  } catch(const std::exception &e) {
    report=std::string("{\"status\":\"RED\",\"reason\":\"")+e.what()+"\"}";
  }
  return report.c_str();
}

#if !defined(ROOT_ADJACENCY_FIXTURE_DLL)
#include <iostream>
int main() {
  const std::string value=RunRootAdjacencyFocused();
  std::cout<<value<<"\n";
  return value.find("\"GREEN\"")==std::string::npos ? 1 : 0;
}
#endif
