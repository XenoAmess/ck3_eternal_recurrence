// Synthetic production-reader fixture. Added cases are source-only until the
// Native owner builds this existing target; no Game or Native26/27 credit.
#include "xar_bridge/ck3_12002_faction_alerts.hpp"
#include <array>
#include <cstddef>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>

namespace {
using Bytes = std::array<std::byte, 4096>;
template<class T> void Put(Bytes &b, std::size_t at, T v) {
  std::memcpy(b.data()+at,&v,sizeof(v));
}
void *Pointer(void *object) {
  void *v=nullptr; std::memcpy(&v,static_cast<std::byte *>(object)+0x300,sizeof(v)); return v;
}
struct Storage {
  Bytes header{}, slots{}; void *pointer=header.data();
  Storage() { Put(header,0x20,slots.data()); Put(header,0x2C,std::int32_t{64}); }
  void Add(std::int32_t id, Bytes &object, std::size_t identity) {
    Put(slots,static_cast<std::size_t>(id)*0x10+8,object.data()); Put(object,identity,id);
  }
};
struct Fixture {
  Storage characters,titles,contracts;
  Bytes actor{},child{},grand{},sibling{},a_land{},c_land{},g_land{},a_county{},c_county{},
      g_county{},duchy{},family{},county_def{},duchy_def{},a_contract{},c_contract{},back{},
      a_province{},c_province{},g_province{},a_data{},c_data{},g_data{};
  std::array<std::int32_t,4> own{11,13,11,16};
  std::array<std::int32_t,1> child_titles{12},grand_titles{14},child_edges{22},back_edges{23};
  std::array<std::int32_t,2> actor_edges{21,21};
  xar::ck3_12002::PlayerFactionAlertsNativeEnvironmentV1 env{};
  xar::ck3_12002::PlayerFactionAlertsAccessV1 access{};
  const void *fail_address=nullptr;
  int actor_reads=0,captures=0;
  bool membership_drift=false,frame_drift=false;
  Fixture() {
    characters.Add(1,actor,0x18); characters.Add(2,child,0x18);
    characters.Add(3,grand,0x18); characters.Add(4,sibling,0x18);
    Put(actor,0x1C0,a_land.data()); Put(child,0x1C0,c_land.data()); Put(grand,0x1C0,g_land.data());
    Put(child,0x300,actor.data()); Put(grand,0x300,child.data());
    titles.Add(11,a_county,0x10); titles.Add(12,c_county,0x10);
    titles.Add(13,duchy,0x10); titles.Add(14,g_county,0x10); titles.Add(16,family,0x10);
    Put(county_def,0x64,std::int32_t{2}); Put(duchy_def,0x64,std::int32_t{3});
    Put(duchy,0x48,duchy_def.data()); Put(family,0x48,county_def.data());
    const auto county=[&](Bytes &title,Bytes &province,Bytes &data,std::int32_t id,std::int32_t holder) {
      Put(title,0x48,county_def.data()); Put(title,0x11C,std::int32_t{1});
      Put(title,0x128,holder); Put(title,0x300,province.data());
      Put(province,0x10,id+100); Put(province,0x85C,std::uint32_t{0x50726F76U});
      Put(province,0x848,data.data()); Put(data,0x18,id);
    };
    county(a_county,a_province,a_data,11,1); county(c_county,c_province,c_data,12,2);
    county(g_county,g_province,g_data,14,3);
    Put(a_land,0x1E0,own.data()); Put(a_land,0x1EC,std::int32_t{4});
    Put(c_land,0x1E0,child_titles.data()); Put(c_land,0x1EC,std::int32_t{1});
    Put(g_land,0x1E0,grand_titles.data()); Put(g_land,0x1EC,std::int32_t{1});
    contracts.Add(21,a_contract,8); Put(a_contract,0x20,child.data());
    contracts.Add(22,c_contract,8); Put(c_contract,0x20,grand.data());
    contracts.Add(23,back,8); Put(back,0x20,actor.data());
    Put(a_land,0x218,actor_edges.data()); Put(a_land,0x224,std::int32_t{2});
    Put(c_land,0x218,child_edges.data()); Put(c_land,0x224,std::int32_t{1});
    env.exact_build_admitted=true; env.offline_fixture_function_overrides=true;
    env.character_storage_slot=&characters.pointer; env.landed_title_storage_slot=&titles.pointer;
    env.vassal_contract_storage_slot=&contracts.pointer; env.immediate_liege=&Pointer; env.title_province=&Pointer;
    access.context=this; access.read_memory=&Memory; access.is_main_thread=&Main; access.capture_frame=&Capture;
  }
  static bool Main(void *) noexcept { return true; }
  static bool Memory(void *context,const void *address,void *out,std::size_t size) noexcept {
    auto &f=*static_cast<Fixture *>(context);
    if(address==f.fail_address) return false;
    if(address==f.actor.data()+0x1C0 && ++f.actor_reads==3 && f.membership_drift)
      Put(f.c_land,0x1EC,std::int32_t{0});
    std::memcpy(out,address,size); return true;
  }
  static bool Capture(void *context,xar::game::PlayerFactionAlertsFrameV1 &frame) noexcept {
    auto &f=*static_cast<Fixture *>(context); ++f.captures;
    frame={}; frame.snapshot_revision=41; frame.date_raw=53144328;
    frame.paused=true; frame.map_ready=true; frame.has_played_character=true;
    frame.played_character_alive=true; frame.played_character_id=1;
    if(f.frame_drift && f.captures==2) ++frame.date_raw;
    return true;
  }
};
bool ReaderCase(int n) {
  Fixture f;
  switch(n) {
  case 1: Put(f.a_county,0x10,std::int32_t{0x100000B}); break;
  case 2: Put(f.c_county,0x128,std::int32_t{1}); break;
  case 3: Put(f.child,0x300,f.sibling.data()); break;
  case 4: Put(f.actor,0x300,f.child.data()); Put(f.c_land,0x218,f.back_edges.data()); break;
  case 5: f.actor_edges[1]=22; break;
  case 6: Put(f.a_land,0x224,std::int32_t{16'385}); break;
  case 7: Put(f.child,0x1C0,static_cast<void *>(nullptr)); break;
  case 8: f.fail_address=f.c_county.data()+0x128; break;
  case 9: f.env.exact_build_admitted=false; break;
  default: break;
  }
  std::vector<std::int32_t> counties{999};
  const bool ok=xar::ck3_12002::ReadSubrealmCountyIdsV1(f.env,f.access,1,counties);
  return n==0 ? ok && counties==std::vector<std::int32_t>{11,12,14} : !ok && counties.empty();
}
bool WholeCase(int n) {
  Fixture f; f.membership_drift=n==1; f.frame_drift=n==2;
  if(n==3) Put(f.c_data,0x18,std::int32_t{0x100000C});
  xar::game::PlayerFactionAlertsV1 output;
  xar::ck3_12002::PlayerFactionAlertsRequestV1 request{}; request.expected_snapshot_revision=41;
  const auto result=xar::ck3_12002::ReadPlayerFactionAlertsV1(f.env,f.access,request,output);
  if(n!=0) return result==xar::game::ReadPlayerFactionAlertsResultV1::unavailable &&
      !output.player_subrealm_geographic_counties_v1;
  if(result!=xar::game::ReadPlayerFactionAlertsResultV1::available ||
      !output.player_subrealm_geographic_counties_v1 || !output.targeting_factions.empty()) return false;
  const auto &r=*output.player_subrealm_geographic_counties_v1;
  if(!r.complete || r.actor_character_id!=1 || r.snapshot_revision!=41 ||
      r.county_title_ids!=std::vector<std::int32_t>{11,12,14}) return false;
  const auto wire=xar::ck3_12002::SerializePlayerFactionAlertsV1(output);
  if(wire.find("\"county_title_ids\":[11,12,14]")==std::string::npos) return false;
  output.player_subrealm_geographic_counties_v1->county_title_ids={14,11};
  return xar::ck3_12002::SerializePlayerFactionAlertsV1(output).empty();
}
} // namespace
int main() {
  for(int i=0;i<10;++i) if(!ReaderCase(i)) { std::cerr<<"reader case "<<i<<'\n'; return i+1; }
  for(int i=0;i<4;++i) if(!WholeCase(i)) { std::cerr<<"whole case "<<i<<'\n'; return i+20; }
  std::cout<<"real actor/vassal county reader, failure clear and double-sample source cases passed\n";
  return 0;
}
