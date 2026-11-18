// Reuse the actual complete foundation/event/pending RAM model, not a fake
// Full provider. This source adds only the newly observed military graph.
#include <Windows.h>
#define main LegacyEmptyFullFixtureMain
#include "ck3_1210_full_snapshot_v1_test.cpp"
#undef main

namespace {
struct FullArmyFixture;
FullArmyFixture *army_active=nullptr;
std::int32_t ArmyNativeState(void *);
bool ArmyCopy(void *,const void *,void *,std::size_t) noexcept;
struct FullArmyFixture {
  Fixture full;
  std::array<std::byte,0x40> registry{};
  std::array<std::byte,0x10> rows{};
  std::array<std::byte,0x208> army{},fallback{};
  std::array<std::byte,0xB30> province0{},province1{};
  std::array<void *,3> provinces{nullptr,province0.data(),province1.data()};
  std::array<std::int32_t,2> route_ids{1,2};
  std::array<void *,2> route{&route_ids[0],&route_ids[1]};
  void *registry_slot=registry.data(),*fallback_slot=fallback.data();
  std::int32_t native_id=std::bit_cast<std::int32_t>(std::uint32_t{0x85000000});
  unsigned state_calls=0;
  bool change_identity=false;
  explicit FullArmyFixture(std::int32_t actor=kActor):full(actor) {
    army_active=this;
    auto &b=full.bindings;
    b.enable_army_base=true;
    b.army_base=BindArmyBaseImageV1(0x140000000,kExecutableSha256);
    b.army_base.player_armies.core=b.core;
    b.army_base.player_armies.unit_registry_slot=&full.unit_slot;
    b.army_base.player_armies.get_unit_state=&ArmyNativeState;
    b.army_base.player_armies.integration_native_calls_permitted=true;
    b.army_base.native_army_registry_slot=&registry_slot;
    b.army_base.no_army_fallback_slot=&fallback_slot;
    b.army_fixture_access={this,ArmyCopy};
    b.war_identity=BindActiveWarsImageV1(0x140000000,kExecutableSha256);
    b.war_identity.core=b.core;b.war_identity.war_registry_slot=&full.war_slot;
    full.UnitPresent(full.actor_id);
    Put(full.unit,0,std::uintptr_t{0x144E42B20});
    Put(full.unit,0x20,province0.data());Put(full.unit,0x38,route.data());
    Put(full.unit,0x40,std::int32_t{2});Put(full.unit,0x44,std::int32_t{2});
    Put(full.unit,0x178,native_id);
    Put(full.data,0x4140,provinces.data());Put(full.data,0x414C,std::int32_t{3});
    Put(province0,0x10,std::int32_t{1});Put(province1,0x10,std::int32_t{2});
    Put(province0,0xB24,std::uint32_t{0x50726F76});Put(province1,0xB24,std::uint32_t{0x50726F76});
    Put(full.data,kArmyBaseManagerOffsetV1,b.army_base.native_army_manager_vtable);
    Put(full.data,kArmyBaseManagerOffsetV1+kArmyBaseManagerRegistryOffsetV1,registry_slot);
    Put(registry,0,b.army_base.native_army_registry_vtable);
    Put(registry,0x20,rows.data());Put(registry,0x2C,std::int32_t{1});Put(rows,8,army.data());
    Put(army,0,b.army_base.native_army_vtable);Put(army,0x10,native_id);
    Put(army,0x14,std::uint32_t{0x41726D79});
  }
};
std::int32_t ArmyNativeState(void *unit) {
  auto &m=*army_active;++m.state_calls;
  Require(unit==m.full.unit.data(),"actual Unit receiver reaches native state seam");
  if(m.change_identity)Put(m.army,0x10,std::int32_t{0});
  return Get<std::int32_t>(unit,0x178)==-1?1:7;
}
bool ArmyCopy(void *,const void *source,void *dest,std::size_t size) noexcept {
  const auto start=reinterpret_cast<std::uintptr_t>(&ArmyNativeState);
  const auto address=reinterpret_cast<std::uintptr_t>(source);
  if(address>=start && address-start<kPlayerArmyStateEntryGuardV1.size() &&
      size<=kPlayerArmyStateEntryGuardV1.size()-(address-start)) {
    std::memcpy(dest,kPlayerArmyStateEntryGuardV1.data()+(address-start),size);return true;
  }
#if defined(_MSC_VER)
  __try {std::memcpy(dest,source,size);return true;}
  __except(EXCEPTION_EXECUTE_HANDLER) {return false;}
#else
  std::memcpy(dest,source,size);return true;
#endif
}
void FullArmyPass(FullArmyFixture &m,bool route_expected) {
  game::Snapshot out{};FullSnapshotDiagnosticsV1 d{};
  const bool read=ReadFullSnapshotV1(m.full.bindings,out,d,m.full.ingame_witness);
  if(!read)std::cerr<<"FULL_ARMY_DIAG stage="<<d.stage<<" reason="<<d.reason<<" calls="<<d.army_state_calls_attempted<<std::endl;
  Require(read,"real complete Full with nonempty base army");
  Require(d.complete && d.completed_passes==2 && out.active_wars.empty() &&
      out.player_armies.size()==1 && d.army_state_calls_attempted==4,"Full retains complete scan and all native call attempts");
  const auto &a=out.player_armies.front();
  Require(a.army_id==Get<std::int32_t>(m.full.unit.data(),0x10) && a.owner_character_id==m.full.actor_id &&
      a.has_current_province && a.current_province_id==1 && a.controllable,"full signed Unit/owner and current Province preserved");
  Require(a.route_source_count==(route_expected?2:0) &&
      a.move_target_observable==route_expected && a.route_province_ids==(route_expected?std::vector<std::int32_t>{1,2}:std::vector<std::int32_t>{}),
      "complete route and no-target semantics preserved");
  Require(!a.siege_days_left && !a.siege_province_holder_character_id && !a.siege_province_in_player_subrealm,
      "unobserved optional siege sidecars remain absent");
}
} // namespace
#if !defined(XAR_FULL_ARMY_FIXTURE_NO_MAIN)
int main() {
  {FullArmyFixture m;FullArmyPass(m,true);}
  {FullArmyFixture m;Put(m.full.unit,0x44,std::int32_t{0});FullArmyPass(m,false);}
  {FullArmyFixture m;Put(m.full.unit,0x178,std::int32_t{-1});Put(m.full.unit,0x44,std::int32_t{0});FullArmyPass(m,false);}
  {FullArmyFixture m;m.full.bindings.army_base.player_armies.integration_native_calls_permitted=false;
    Unavailable(m.full);Require(m.state_calls==0,"closed native gate cannot publish an owned Army Full");}
  {FullArmyFixture m;Put(m.army,0x10,std::int32_t{0});Unavailable(m.full);
    Require(m.state_calls==0,"stale generation rejected before native call");}
  {FullArmyFixture m;m.change_identity=true;auto out=Stale(m.full);FullSnapshotDiagnosticsV1 d{};
    Require(!ReadFullSnapshotV1(m.full.bindings,out,d,m.full.ingame_witness) && out==game::Snapshot{} && d.army_state_calls_attempted==1,
        "mid-call native dependency drift clears whole Full and retains attempt");}
  {FullArmyFixture m;m.full.WarPresent(true);Put(m.full.war,0,m.full.bindings.war_identity.war_vtable);
    Put(m.full.defender,8,kPeer2);Put(m.full.war,0x290,m.full.actor_id);Put(m.full.war,0x294,kPeer2);
    const auto d=Unavailable(m.full);
    Require(d.reason=="active_wars_nonempty_rich_observation_unavailable" && m.state_calls==0,
        "nonempty War cannot be fabricated as empty or admitted through army-only migration");}
  std::cout<<"PASS full positive-Army/empty-War NoGame; complete actual child readers, no live or action permission"<<std::endl;
  return 0;
}
#endif
