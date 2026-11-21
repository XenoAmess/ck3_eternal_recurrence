// Reuse the qualified current Core/Full own-RAM setup, not a native getter.
#define main OriginalFull112FixtureMain
#include "ck3_121003_full111_static_test.cpp"
#undef main
#include "xar_bridge/ck3_1210_adapter.hpp"
#include "xar_bridge/ck3_1210_application_exit_v1.hpp"
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include "xar_bridge/ck3_1210_date_sentinel_request_v1.hpp"
namespace xar::ck3_1210 {bool ReadActiveWarsEmptyV1(const MilitaryEmptyBindingsV1&,const CoreSnapshotPrefix&,MilitaryEmptyObservationV1&,MilitaryEmptyReadAccessV1={}) noexcept;}
namespace xar::combined142_fixture {
std::string Serialize(const game::Snapshot&,const game::GameAdapter*);
std::string ArmNonempty(const game::GameAdapter&,const game::Snapshot&,std::string_view,std::string_view,bool&);
}

namespace {
struct ArmyFixture123 : Fixture {
 std::vector<std::byte> unit=std::vector<std::byte>(0x76000);
 std::array<void*,1> unit_blocks{unit.data()};
 std::array<std::byte,0x20> unit_slots{};
 std::array<std::byte,0x368> war{};
 std::array<std::byte,0x10> war_slots{},participant{};
 std::array<void*,1> participants{participant.data()};
 std::int32_t unit_id=std::bit_cast<std::int32_t>(0x83000001U);
 enum class ReadMode { normal, deny_slot, mutate_unowned } mode=ReadMode::normal;
 unsigned owner_reads=0;
 ArmyFixture123(){
  const auto b=image.base();
  for(std::size_t i=0;i<1024;++i)Put(unit,i*0x1D8+0x10,std::int32_t{-1});
  Put(units,8,unit_blocks.data());Put(units,0x14,std::int32_t{1});
  Put(units,0x20,unit_slots.data());Put(units,0x2C,std::int32_t{2});
  Put(unit_slots,0x18,unit.data());Put(unit,0,b+0x4E42B98);
  Put(unit,0x10,unit_id);Put(unit,0x14,std::uint32_t{0xDEADBEEF});
  Put(unit,0x174,actor_id);
  bindings.army_fixture_access={this,&CopyOwned};
 }
 static bool CopyOwned(void *context,const void *from,void *to,std::size_t size) noexcept {
  auto &f=*static_cast<ArmyFixture123*>(context);
  if(f.mode==ReadMode::deny_slot&&from==f.unit_slots.data()+0x18)return false;
  if(from==f.unit.data()+0x174) {
   ++f.owner_reads;
   if(f.mode==ReadMode::mutate_unowned&&f.owner_reads==2)
    std::memcpy(f.unit.data()+0x174,&f.dead_id,sizeof(f.dead_id));
  }
  std::memcpy(to,from,size);return true;
 }
 void ActiveWar(){
  Put(wars,0x20,war_slots.data());Put(wars,0x2C,std::int32_t{1});
  Put(war_slots,8,war.data());Put(war,8,std::int32_t{0});
  Put(war,0xC,std::uint32_t{0x5761725F});Put(war,0x360,std::uint8_t{0});
  Put(war,0x28,participants.data());Put(war,0x30,std::int32_t{1});
  Put(war,0x34,std::int32_t{1});Put(participant,8,actor_id);
 }
};
void Unavailable123(ArmyFixture123 &f,const char *reason=nullptr){
 xar::game::Snapshot s{};ck::FullSnapshotDiagnosticsV1 d{};
 Need(!current::ReadFull(f.bindings,s,d),"bad owned source must be unavailable");
 Need(!d.complete&&s.player_armies.empty(),"failure must not publish partial rows");
 if(reason)Need(d.reason==reason,"specific unavailable reason");
}
}

int main(){
 try {
#if !defined(XAR_CK3_ENABLE_121003_OWNED_ARMY123)
  throw std::runtime_error("actual owned123 producer must be compiled ON");
#endif
  {
   ArmyFixture123 f;xar::game::Snapshot s{};ck::FullSnapshotDiagnosticsV1 d{};
   Need(current::ReadFull(f.bindings,s,d)&&d.complete&&d.completed_passes==2,"actual Full owned identity positive");
   Need(s.player_armies.size()==1,"owned row present");
   const auto &a=s.player_armies[0];
   Need(a.army_id==f.unit_id&&a.owner_character_id==f.actor_id&&a.controllable,"full32 ownership values preserved");
   Need(!f.bindings.enable_army_base,"no legacy rich-state getter admission");
   Need(s.active_wars.empty(),"only proven war empty");
  }
  {ArmyFixture123 f;Put(f.unit,0x174,std::int32_t{0});xar::game::Snapshot s{};ck::FullSnapshotDiagnosticsV1 d{};
   Need(current::ReadFull(f.bindings,s,d)&&d.complete&&s.player_armies.empty(),"nonowned complete scan");}
  {ArmyFixture123 f;Put(f.unit,0x174,f.dead_id);xar::game::Snapshot s{};ck::FullSnapshotDiagnosticsV1 d{};
   Need(current::ReadFull(f.bindings,s,d)&&s.player_armies.empty(),"other dead owner is not filtered by invented alive semantics");}
  {ArmyFixture123 f;Put(f.unit_slots,0x18,static_cast<void*>(nullptr));Put(f.unit,0x10,std::int32_t{-1});xar::game::Snapshot s{};ck::FullSnapshotDiagnosticsV1 d{};
   Need(current::ReadFull(f.bindings,s,d)&&d.complete&&s.player_armies.empty(),"native -1 records with canonical null are valid empty");}
  {ArmyFixture123 f;Put(f.unit,0,f.image.base()+0x4E42B90);Unavailable123(f,"current123_unit_identity_invalid");}
  {ArmyFixture123 f;Put(f.unit,0x10,std::int32_t{-1});Put(f.unit,0,std::uintptr_t{0});xar::game::Snapshot s{};ck::FullSnapshotDiagnosticsV1 d{};
   Need(current::ReadFull(f.bindings,s,d)&&d.complete&&s.player_armies.empty(),"native -1 skip precedes vptr use");}
  {ArmyFixture123 f;Put(f.unit,0x10,std::int32_t{0});Unavailable123(f,"current123_unit_identity_invalid");}
  {ArmyFixture123 f;Put(f.unit,0x174,std::bit_cast<std::int32_t>(0x82000001U));Unavailable123(f,"current123_unit_owner_unresolved");}
  {ArmyFixture123 f;Put(f.data,0x3ABF8+0x20,f.other_pending.data());Unavailable123(f);}
  {ArmyFixture123 f;f.mode=ArmyFixture123::ReadMode::deny_slot;Unavailable123(f,"current123_owned_unit_read_failed");}
  {ArmyFixture123 f;Put(f.unit,0x174,std::int32_t{0});f.mode=ArmyFixture123::ReadMode::mutate_unowned;
   Unavailable123(f,"current111_full_observations_changed");Need(f.owner_reads==2,"both actual passes observed nonowned source");}
  {ArmyFixture123 f;f.ActiveWar();Unavailable123(f,"active_wars_nonempty_rich_observation_unavailable");}
  {ArmyFixture123 f;Put(f.unit,0x14,std::uint32_t{0x556E6974});ck::CoreSnapshotPrefix expected{};
   Need(ck::ReadCoreSnapshot(f.bindings.core,expected),"actual fixture Core");
   ck::MilitaryEmptyObservationV1 e{};
   Need(!ck::ReadMilitaryEmptyV1(f.bindings.military,expected,e),"old empty-both API remains strict");
   Need(ck::ReadActiveWarsEmptyV1(f.bindings.military,expected,e)&&e.active_wars_empty_proven&&!e.player_armies_empty_proven,"war-only API never claims unit emptiness");}
  {
   ArmyFixture123 f;xar::game::Snapshot snapshot{};ck::FullSnapshotDiagnosticsV1 diag{};
   Need(current::ReadFull(f.bindings,snapshot,diag),"actual combined Full provider positive");
   namespace build=xar::ck3_121003::build26785313;
   auto &im=f.image;im.Value(0,std::uint16_t{0x5A4D});im.Value(0x3C,std::uint32_t{0x100});
   im.Value(0x100,std::uint32_t{0x4550});im.Value(0x104,std::uint16_t{0x8664});im.Value(0x108,build::kPeTimestamp);
   im.Value(0x118,std::uint16_t{0x20B});im.Value(0x130,std::uint64_t(im.base()));im.Value(0x150,std::uint32_t(build::kImageSize));
   for(const auto &pin:build::ReadonlyImagePins())for(std::size_t i=0;i<pin.bytes.size();++i)im.Value(pin.rva+i,pin.bytes[i]);
   auto adapter=xar::game::CreateCk3_1210AdapterForImage125(build::kExecutableSha256,im.base());
   Need(adapter&&adapter->enabled(),"actual combined Factory admission");
   const auto frame=xar::combined142_fixture::Serialize(snapshot,adapter.get());
   const auto row=std::string("\"player_armies\":[{\"army_id\":")+std::to_string(f.unit_id)+",\"owner_character_id\":"+std::to_string(f.actor_id)+",\"controllable\":true}]";
   Need(frame.find(row)!=std::string::npos,"actual private descriptor serializer emits exactly three signed fields");
   Need(xar::combined142_fixture::Serialize(snapshot,nullptr).find(row)==std::string::npos,"no descriptor never silently uses identity mode");
   snapshot.date_raw=53179344;snapshot.speed=5;
   const std::string step="research-arm-tactical-daily-sentinel-v1-53179344-to-53179368-speed-5-mode-terminal-a-0";
   const auto payload=std::string("{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"own142\",\"step\":\"")+step+"\",\"expected_revision\":7,\"date_sentinel_arm\":{\"schema\":\"ck3_1210_date_sentinel_arm_v1\",\"game_version\":\"1.21.0.3\",\"executable_sha256\":\""+build::kExecutableSha256+"\",\"adapter_id\":\"ck3-1.21.0.3-26785313-full111-msvc-x64\",\"backend\":\"ck3-1.21.0.3-native-headless-main-thread\",\"snapshot_id\":\"native:7\",\"native_revision\":7,\"deadline_unix_ms\":2000000}}";
   ck::DateSentinelArmRequestV1 parsed{};Need(ck::ParseDateSentinelArmRequestV1(payload,parsed,ck::ImageBuildV1::full11126785313),"actual combined current parser");
   Need(adapter->supports_step(step)&&snapshot.paused&&snapshot.map_ready&&snapshot.has_played_character&&snapshot.played_character_alive&&!snapshot.player_armies.empty(),"all pre-ARM source prerequisites except military emptiness");
   bool unchanged=false;const auto result=xar::combined142_fixture::ArmNonempty(*adapter,snapshot,step,payload,unchanged);
   Need(unchanged&&result.find("\"effect_attempted\":false")!=std::string::npos,"actual private ARM nonempty refuses without queue/generation/effect");
   Need(adapter->supports_step("research-query-tactical-daily-sentinel-v1")&&adapter->supports_step("research-cancel-tactical-daily-sentinel-v1-generation-1")&&adapter->supports("game.command.normal-exit-application-v1"),"same Factory keeps Status Cancel Exit capability with observed nonempty basis");
  }
  std::cout<<"owned123 actual Full/typed/full32/coherence/empty/war cases PASS\n";return 0;
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
