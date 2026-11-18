#include "xar_bridge/ck3_1210_full_snapshot_v1.hpp"
#include <array>
#include <bit>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <limits>
#include <vector>

// NoGame: only underlying native ABI calls have RAM-fixture replacements.
// ReadFullSnapshotV1 and every foundation/event/pending/military Read are real.
// Never call the Full binder on an unmapped fake image: it owns actual PE pins.
namespace {
using namespace xar::ck3_1210;
namespace game = xar::game;
constexpr auto kActor = std::bit_cast<std::int32_t>(std::uint32_t{0x81000001});
constexpr auto kPeer2 = std::bit_cast<std::int32_t>(std::uint32_t{0x82000002});
constexpr auto kPeer3 = std::bit_cast<std::int32_t>(std::uint32_t{0xFF000003});
constexpr auto kPending = std::bit_cast<std::int32_t>(std::uint32_t{0x83000000});
void Require(bool value, const char *message) {
  if (!value) { std::cerr << "FAIL " << message << std::endl; std::exit(1); }
}
template <class B, class T> void Put(B &b, std::size_t offset, T value) {
  Require(offset <= b.size() && sizeof(value) <= b.size() - offset, "RAM fixture bounds");
  std::memcpy(b.data() + offset, &value, sizeof(value));
}
template <class T> T Get(const void *p, std::size_t offset) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(p) + offset, sizeof(value)); return value;
}
enum class Mutation { none, core_date, event_within, event_between, pending_within,
  pending_between, resource_between, ingame_epoch, ingame_transition };
struct Fixture;
Fixture *active = nullptr;
void *LocalPlayer(void *);
void *Current(void *);
bool PendingFor(void *, void *);
bool Validate(void *);
struct Fixture {
  std::array<std::byte, 0xB0> state{};
  std::array<std::byte, 0x48> jomini{};
  std::array<std::byte, 0x200> players{};
  std::array<std::byte, 0x98> ingame_gfx{};
  std::array<std::byte, 0x48> ingame_handler{};
  std::array<std::byte, 0x80> player{};
  std::vector<std::byte> data = std::vector<std::byte>(kCurrentEventManagerOffsetV1 + 0x1F28);
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x40> characters{};
  std::array<std::byte, 0x40> character_rows{};
  std::array<std::byte, 0x1E0> actor{}, peer0{}, peer2{}, peer3{};
  std::array<std::byte, 0x300> living{};
  std::array<std::byte, 0x30> family{};
  std::array<std::int32_t, 2> spouses{};
  std::array<std::byte, 0x1C8> event{};
  std::array<std::byte, 0x148> definition{};
  std::array<std::byte, 2> authored_payload{};
  std::array<void *, 2> authored{authored_payload.data(),authored_payload.data()+1};
  std::array<void *, 1> event_queue{event.data()};
  std::array<std::byte, 0x58> pending_store{}, units{}, wars{};
  std::array<std::byte, 0x20> pending_rows{};
  std::array<std::byte, 0x5D8> pending{};
  std::array<std::byte, 0x10> unit_rows{}, war_rows{};
  std::array<std::byte, 0x180> unit{};
  std::array<std::byte, 0x370> war{};
  std::array<std::byte, 0x10> attacker{}, defender{};
  std::array<void *, 1> attackers{attacker.data()}, defenders{defender.data()};
  void *state_slot = state.data(), *jomini_slot = jomini.data(), *character_slot = characters.data();
  void *pending_slot = pending_store.data(), *unit_slot = units.data(), *war_slot = wars.data();
  void *current = nullptr;
  std::int32_t actor_id, zero_peer, selector_character;
  std::int64_t gold = -1234567, prestige = 2222222, piety = -333333;
  std::int32_t stress = 42;
  unsigned core_calls = 0, selectors = 0, predicates = 0, validators = 0, queue_calls = 0;
  Mutation mutation = Mutation::none;
  bool map_ready = true;
  FullSnapshotBindingsV1 bindings{};
  IngameReadyWitnessV1 ingame_witness{};
  explicit Fixture(std::int32_t id = kActor) : actor_id(id),
      zero_peer((static_cast<std::uint32_t>(id)&0xFFFFFFU)==0 ? 0x22000001 : 0), selector_character(id) {
    active = this;
    CoreBindings core{true,&state_slot,&jomini_slot,&character_slot,&LocalPlayer};
    constexpr std::uintptr_t fake_base = 0x140000000;
    bindings.exact_build_admitted = true; bindings.core = core;
    bindings.ingame_ready = {true,core,fake_base+kIngameRootVtableRvaV1,
      fake_base+kIngameApplicationVtableRvaV1,fake_base+kIngameGfxVtableRvaV1,
      fake_base+kIngameHandlerVtableRvaV1};
    bindings.foundation = BindActorFoundationImageV1(fake_base,kExecutableSha256);
    bindings.event = BindCurrentEventSnapshotImageV1(fake_base,kExecutableSha256);
    bindings.pending = BindPendingSnapshotImageV1(fake_base,kExecutableSha256);
    bindings.military = BindMilitaryEmptyImageV1(fake_base,kExecutableSha256);
    bindings.foundation.core = bindings.event.core = bindings.pending.core = bindings.military.core = core;
    bindings.event.get_current_event = &Current; bindings.event.selector_character_id_slot = &selector_character;
    bindings.pending.pending_storage_slot = &pending_slot;
    bindings.pending.is_pending_for_character = &PendingFor; bindings.pending.validate_reply = &Validate;
    bindings.military.unit_registry_slot = &unit_slot; bindings.military.war_registry_slot = &war_slot;
    Init();
    // The actual readiness reducer first observes an Enter-era graph at epoch0,
    // then the RAM producer completes a real-model application frame at epoch1.
    // This only supplies the underlying ABI model; Full itself is never mocked.
    IngameReadyObservationV1 first{};
    Require(!ObserveIngameReadyV1(bindings.ingame_ready,ingame_witness,first) &&
      first.unavailable_reason=="full_snapshot_ingame_first_completed_frame_required",
      "first graph cannot borrow a completed-frame witness");
    Put(players,kIngameCompletedFrameEpochOffsetV1,std::uint64_t{1});
  }
  void InitCharacter(std::array<std::byte,0x1E0> &c, std::int32_t id) {
    Put(c,0x18,id); Put(c,0x1C,std::uint32_t{0x43686172});
    Put(character_rows,(static_cast<std::uint32_t>(id)&0xFFFFFFU)*0x10+8,c.data());
  }
  void Init() {
    Put(state,8,std::int32_t{123456}); Put(state,0x70,std::int32_t{4}); Put(state,0xA0,data.data());
    Put(jomini,0x18,players.data()); Put(jomini,0x20,std::uint8_t{1});
    Put(jomini,0,bindings.ingame_ready.root_vtable); Put(jomini,0x10,ingame_gfx.data());
    Put(players,0,bindings.ingame_ready.application_vtable); Put(players,0x28,jomini.data());
    Put(ingame_gfx,0,bindings.ingame_ready.gfx_vtable); Put(ingame_gfx,0x20,jomini.data());
    Put(ingame_gfx,0x88,ingame_handler.data()); Put(ingame_gfx,0x90,players.data());
    Put(ingame_handler,0,bindings.ingame_ready.handler_vtable); Put(ingame_handler,0x40,jomini.data());
    Put(players,0x1F0,std::int32_t{7}); Put(player,0x70,std::int32_t{7});
    Put(entry,0xD8,std::int32_t{7}); Put(entry,0xB0,actor_id);
    Put(data,kPlayerCharacterManagerOffset+0x58,entries.data());
    Put(data,kPlayerCharacterManagerOffset+0x64,std::int32_t{1});
    Put(characters,0x20,character_rows.data()); Put(characters,0x2C,std::int32_t{4});
    InitCharacter(actor,actor_id); InitCharacter(peer0,zero_peer); InitCharacter(peer2,kPeer2); InitCharacter(peer3,kPeer3);
    Put(peer3,0x1D0,peer3.data()); // Dead spouse remains in the raw native family vector.
    Put(actor,0x1B0,living.data()); Put(actor,0x1A8,family.data());
    Put(living,0x100,gold); Put(living,0x130,prestige); Put(living,0x110,piety); Put(living,0x2F8,stress);
    spouses={zero_peer,kPeer3}; Put(family,0x10,kPeer2); Put(family,0x14,zero_peer);
    Put(family,0x20,spouses.data()); Put(family,0x28,std::int32_t{2}); Put(family,0x2C,std::int32_t{2});
    Put(definition,0,bindings.event.definition_vtable); Put(definition,0x138,authored.data());
    Put(definition,0x140,std::int32_t{2}); Put(definition,0x144,std::int32_t{2});
    Put(event,0x1B8,definition.data()); Put(event,0x1C0,actor_id); Put(event,0x1C4,std::int32_t{42});
    Put(pending_store,0,bindings.pending.database_vtable); Put(pending_store,0x20,pending_rows.data());
    Put(pending_store,0x2C,std::int32_t{2});
    Put(data,kMilitaryUnitManagerOffsetV1,bindings.military.unit_manager_vtable);
    Put(data,kMilitaryUnitManagerOffsetV1+0x20,unit_slot);
    Put(data,kMilitaryWarManagerOffsetV1,bindings.military.war_manager_vtable);
    Put(data,kMilitaryWarManagerOffsetV1+0x20,war_slot);
    Put(units,0,bindings.military.unit_registry_vtable); Put(wars,0,bindings.military.war_registry_vtable);
    // Real typed zero-capacity military headers, no made-up observations.
  }
  void EventPresent() {
    current=event.data(); Put(data,kCurrentEventManagerOffsetV1+0x1F18,event_queue.data());
    Put(data,kCurrentEventManagerOffsetV1+0x1F24,std::int32_t{1});
  }
  void PendingPresent(bool notification=false) {
    Put(pending_rows,8,pending.data()); Put(pending,0,bindings.pending.pending_vtable);
    Put(pending,0x10,kPending); Put(pending,0x14,kPendingSnapshotTypeV1);
    Put(pending,0x300,kPeer3); Put(pending,0x304,actor_id); Put(pending,0x310,actor_id);
    Put(pending,0x5D0,std::int32_t{0}); Put(pending,0x5D6,static_cast<std::uint8_t>(notification));
  }
  void UnitPresent(std::int32_t owner) {
    Put(units,0x20,unit_rows.data()); Put(units,0x2C,std::int32_t{1}); Put(unit_rows,8,unit.data());
    Put(unit,0x10,std::bit_cast<std::int32_t>(std::uint32_t{0x84000000}));
    Put(unit,0x14,std::uint32_t{0x556E6974}); Put(unit,0x174,owner);
  }
  void WarPresent(bool player_participates, bool ended=false) {
    Put(wars,0x20,war_rows.data()); Put(wars,0x2C,std::int32_t{1}); Put(war_rows,8,war.data());
    Put(war,8,std::bit_cast<std::int32_t>(std::uint32_t{0x85000000}));
    Put(war,0xC,std::uint32_t{0x5761725F}); Put(war,0x360,static_cast<std::uint8_t>(ended));
    Put(attacker,8,player_participates?actor_id:kPeer2); Put(defender,8,kPeer3);
    Put(war,0x28,attackers.data()); Put(war,0x30,std::int32_t{1}); Put(war,0x34,std::int32_t{1});
    Put(war,0x88,defenders.data()); Put(war,0x90,std::int32_t{1}); Put(war,0x94,std::int32_t{1});
  }
  game::Snapshot Expected() const {
    game::Snapshot out{};
    out.date_raw=123456; out.speed=5; out.paused=true; out.player_id=7;
    out.map_ready=out.has_played_character=out.played_character_alive=true; out.played_character_id=actor_id;
    out.played_character_stress_points=stress;
    out.played_character_gold={gold,100000}; out.played_character_prestige={prestige,100000};
    out.played_character_piety={piety,100000}; out.played_character_betrothed_id=kPeer2;
    out.played_character_primary_spouse_id=zero_peer; out.played_character_spouse_ids={zero_peer,kPeer3};
    if(current) { out.has_active_event=true; out.active_event_instance_id=42; out.active_event_option_count=2; }
    if(Get<void *>(pending_rows.data(),8)) {
      out.has_pending_character_interaction=true; out.pending_character_interaction_id=kPending;
      out.pending_sender_character_id=kPeer3;
      out.pending_auto_accept_notification=Get<std::uint8_t>(pending.data(),0x5D6)!=0;
    }
    return out;
  }
};
void *LocalPlayer(void *) {
  auto &f=*active; ++f.core_calls;
  if(f.mutation==Mutation::core_date && f.core_calls==1) Put(f.state,8,std::int32_t{123457});
  return f.map_ready?f.player.data():nullptr;
}
void *Current(void *manager) {
  auto &f=*active; ++f.selectors;
  Require(manager==f.data.data()+kCurrentEventManagerOffsetV1,"selector receives real manager RAM");
  if((f.mutation==Mutation::event_within && f.selectors==2) ||
     (f.mutation==Mutation::event_between && f.selectors==3)) Put(f.event,0x1C4,std::int32_t{43});
  if(f.mutation==Mutation::resource_between && f.selectors==2) Put(f.living,0x100,f.gold+1);
  if(f.mutation==Mutation::ingame_epoch && f.selectors==1)
    Put(f.players,kIngameCompletedFrameEpochOffsetV1,std::uint64_t{2});
  if(f.mutation==Mutation::ingame_transition && f.selectors==1) Put(f.players,0x30,std::uint8_t{1});
  return f.current;
}
bool PendingFor(void *pending, void *actor) {
  auto &f=*active; ++f.predicates;
  Require(pending==f.pending.data() && actor==f.actor.data(),"real pending/actor RAM reaches native ABI");
  if(f.mutation==Mutation::pending_within && f.predicates==1) Put(f.pending,0x300,f.zero_peer);
  return !(f.mutation==Mutation::pending_between && f.predicates>1);
}
bool Validate(void *opaque) {
  auto &f=*active; ++f.validators;
  const auto &c=*static_cast<PendingReplyValidationCommandV1 *>(opaque);
  Require(c.primary_vtable==f.bindings.pending.reply_primary_vtable &&
      c.secondary_vtable==f.bindings.pending.reply_secondary_vtable && c.flags==0 &&
      c.instance_id==kPending && c.choice==0,"new28-byte validation DTO preserves full signed ID/choice");
  for(const auto b:c.reserved) Require(b==std::byte{},"validation DTO reserved bytes");
  Require(f.queue_calls==0,"readonly validation never queues"); return true;
}
game::Snapshot Stale(const Fixture &f) {
  auto out=f.Expected(); out.date_raw=999; out.active_event_instance_id=777;
  out.pending_character_interaction_id=888; out.player_armies.emplace_back(); out.active_wars.emplace_back();
  out.played_character_event_trait_membership.emplace(); out.has_one_life_settlement=true;
  out.one_life_settlement.commit_serial=999; return out;
}
FullSnapshotDiagnosticsV1 Unavailable(Fixture &f) {
  auto out=Stale(f); FullSnapshotDiagnosticsV1 d{};
  d.complete=true;d.completed_passes=99;d.reason="stale";
  Require(!ReadFullSnapshotV1(f.bindings,out,d,f.ingame_witness),"full read must be unavailable");
  Require(out==game::Snapshot{},"every output field/vector/optional is cleared on insufficient proof");
  Require(!d.complete && d.completed_passes<=2 && !d.stage.empty() && !d.reason.empty(),
      "failure diagnostics never retain complete proof");
  Require(f.queue_calls==0,"no failure path performs an action"); return d;
}
void Observed(Fixture &f) {
  const auto expected=f.Expected(); auto out=Stale(f); FullSnapshotDiagnosticsV1 d{};
  Require(ReadFullSnapshotV1(f.bindings,out,d,f.ingame_witness),"two full passes over actual child readers");
  Require(out==expected,"Snapshot exactly preserves every Core/resource/family/event/pending/empty-military field");
  Require(d.complete && d.completed_passes==2 && d.stage=="complete" && d.reason.empty() &&
      d.pending_slots_scanned==2,"complete two-pass diagnostics and actual pending scan");
  Require(d.unit_slots_scanned==Get<std::int32_t>(f.units.data(),0x2C) &&
      d.war_slots_scanned==Get<std::int32_t>(f.wars.data(),0x2C),"actual complete typed military scan bounds");
  Require(out.played_character_gold.scale==100000 && out.played_character_prestige.scale==100000 &&
      out.played_character_piety.scale==100000,"three exact fixed-point scales");
  Require(!out.played_character_event_trait_membership && !out.has_one_life_settlement,
      "unqualified traits omitted and settlement unsupported");
  Require(out.player_armies.empty() && out.active_wars.empty() && f.selectors==4 && f.queue_calls==0,
      "two real selectors per pass and typed empty military proof, zero actions");
}
void FoundationGroups(Fixture &f,bool resources,bool relationships) {
  CoreSnapshotPrefix core{}; ActorFoundationObservationV1 partial{};
  Require(ReadCoreSnapshot(f.bindings.core,core) && ReadActorFoundationV1(f.bindings.foundation,core,partial),
      "real foundation child exposes at least one group");
  Require(partial.resources_ready==resources && partial.relationships_ready==relationships &&
      partial.partial && !partial.full_snapshot_available,"actual partial group state");
  f.core_calls=0;
}
} // namespace
int main() {
  using namespace xar::ck3_1210;
  { Fixture f; Observed(f); Require(f.predicates==0 && f.validators==0,"true empty pending no native validation"); }
  { Fixture f; f.EventPresent(); Observed(f); }
  {
    Fixture f; f.PendingPresent(); Observed(f);
    Require(f.predicates==2 && f.validators==2,"actual non-notification validation once per pass");
  }
  {
    Fixture f; f.EventPresent(); f.PendingPresent(true); Observed(f);
    Require(f.predicates==2 && f.validators==0,"native notification flag bypasses reply validation, no queue");
  }
  for(const auto raw:{0U,1U,0x7F000001U,0x80000000U,0x80000001U,0xFF000001U}) {
    Fixture f(std::bit_cast<std::int32_t>(raw)); f.EventPresent(); f.PendingPresent(); Observed(f);
    Require(static_cast<std::uint32_t>(f.actor_id)==raw,"full32 actor identity roundtrip including zero/high sign bit");
  }
  {
    Fixture f; f.gold=(std::numeric_limits<std::int64_t>::min)();
    f.prestige=(std::numeric_limits<std::int64_t>::max)(); f.piety=-1; f.stress=0;
    Put(f.living,0x100,f.gold); Put(f.living,0x130,f.prestige); Put(f.living,0x110,f.piety);
    Put(f.living,0x2F8,f.stress); Observed(f);
  }
  {
    Fixture f; f.gold=f.prestige=f.piety=0; f.stress=0;
    Put(f.actor,0x1B0,static_cast<void *>(nullptr)); Observed(f);
  }
  {
    Fixture f; f.UnitPresent(kPeer2); f.WarPresent(false); Observed(f);
    // Registries can contain real unrelated entities; the player's [] proof is
    // obtained by typed owner/participant walks, never by ignoring the registry.
  }
  { Fixture f; f.WarPresent(true,true); Observed(f); }
  { Fixture f; f.bindings.exact_build_admitted=false; Unavailable(f); }
  { Fixture f; f.bindings.foundation.exact_build_admitted=false; Unavailable(f); }
  {
    Fixture f; Put(f.actor,0x1B0,reinterpret_cast<void *>((std::numeric_limits<std::uintptr_t>::max)()-0x80));
    FoundationGroups(f,false,true); Unavailable(f); // Available family must not mask unreadable resources.
  }
  {
    Fixture f; Put(f.family,0x2C,std::int32_t{3});
    FoundationGroups(f,true,false); Unavailable(f); // Available resources must not mask invalid family.
  }
  {
    Fixture f; Put(f.peer2,0x18,std::bit_cast<std::int32_t>(std::uint32_t{0x84000002}));
    FoundationGroups(f,true,false); Unavailable(f); // Correct low index, wrong spouse generation.
  }
  {
    Fixture f; Put(f.actor,0x1A8,reinterpret_cast<void *>((std::numeric_limits<std::uintptr_t>::max)()-8));
    FoundationGroups(f,true,false); Unavailable(f);
  }
  {
    Fixture f; Put(f.family,0x28,std::int32_t{65}); Put(f.family,0x2C,std::int32_t{65});
    FoundationGroups(f,true,false); Unavailable(f); // Scope failure is not an empty family.
  }
  {
    Fixture f; f.spouses[1]=-1; FoundationGroups(f,true,false); Unavailable(f);
  }
  {
    Fixture f; Put(f.living,0x2F8,std::int32_t{-1});
    CoreSnapshotPrefix core{}; ActorFoundationObservationV1 partial{};
    Require(ReadCoreSnapshot(f.bindings.core,core) && ReadActorFoundationV1(f.bindings.foundation,core,partial) &&
        partial.resources_ready && partial.stress_points && *partial.stress_points==-1,
        "partial observer preserves signed negative stress truth");
    f.core_calls=0;
    const auto d=Unavailable(f); Require(d.reason=="negative_stress_not_gameplay_qualified",
        "full gameplay refuses negative stress while partial truth remains available");
  }
  {
    Fixture f; f.EventPresent(); Put(f.event,0x1C0,std::int32_t{7}); Unavailable(f);
  }
  {
    Fixture f; f.EventPresent(); Put(f.event,0x1C4,std::int32_t{0}); Unavailable(f);
  }
  {
    Fixture f; f.EventPresent(); Put(f.definition,0x144,std::int32_t{3}); Unavailable(f);
  }
  {
    Fixture f; f.EventPresent();
    Put(f.definition,0x138,reinterpret_cast<void *>((std::numeric_limits<std::uintptr_t>::max)()-3));
    Unavailable(f);
  }
  { Fixture f; f.selector_character=-1; Unavailable(f); }
  { Fixture f; f.PendingPresent(); Put(f.pending,0x10,std::int32_t{-1}); Unavailable(f); }
  { Fixture f; f.PendingPresent(); Put(f.pending,0x10,std::int32_t{1}); Unavailable(f); }
  { Fixture f; Put(f.pending_store,0x2C,std::int32_t{-1}); Unavailable(f); }
  {
    Fixture f; f.EventPresent(); f.mutation=Mutation::event_within; Unavailable(f);
  }
  {
    Fixture f; f.PendingPresent(); f.mutation=Mutation::pending_within; Unavailable(f);
  }
  for(const auto mutation:{Mutation::event_between,Mutation::resource_between,Mutation::pending_between}) {
    Fixture f; f.EventPresent(); f.PendingPresent(); f.mutation=mutation;
    const auto d=Unavailable(f);
    Require(d.completed_passes==2 && d.stage=="coherence" &&
        d.reason=="full_snapshot_observations_changed","two separately successful child passes must agree");
  }
  { Fixture f; f.UnitPresent(f.actor_id); const auto d=Unavailable(f);
    Require(d.stage=="military" && d.reason=="player_armies_nonempty","nonempty player army cannot become successful []"); }
  { Fixture f; f.WarPresent(true); const auto d=Unavailable(f);
    Require(d.stage=="military" && d.reason=="active_wars_nonempty_rich_observation_unavailable",
        "active player war cannot become successful []"); }
  { Fixture f; f.unit_slot=nullptr; Unavailable(f); }
  { Fixture f; Put(f.units,0,std::uintptr_t{1}); Unavailable(f); }
  { Fixture f; Put(f.units,0x2C,std::int32_t{1}); Unavailable(f); }
  { Fixture f; Put(f.wars,0x2C,kMilitaryEmptyStorageLimitV1+1); Unavailable(f); }
  {
    Fixture f; f.UnitPresent(kPeer2); Put(f.unit,0x174,std::int32_t{0x05000002}); Unavailable(f);
  }
  {
    Fixture f; f.WarPresent(true); Put(f.war,0x28,static_cast<void *>(nullptr)); Unavailable(f);
  }
  { Fixture f; Put(f.jomini,0x20,std::uint8_t{0}); Unavailable(f); }
  { Fixture f; f.map_ready=false; Unavailable(f); }
  { Fixture f; Put(f.actor,0x1D0,f.actor.data()); Unavailable(f); }
  { Fixture f; Put(f.actor,0x1C,std::uint32_t{0}); Unavailable(f); }
  { Fixture f; Put(f.actor,0x18,std::int32_t{1}); Unavailable(f); }
  { Fixture f; Put(f.entry,0xB0,std::int32_t{-1}); Unavailable(f); }
  { Fixture f; f.mutation=Mutation::core_date; Unavailable(f); }
  std::cout << "PASS ck3_1210_full_snapshot_v1 real-child NoGame fixtures; two passes; queue=0" << std::endl;
  return 0;
}
