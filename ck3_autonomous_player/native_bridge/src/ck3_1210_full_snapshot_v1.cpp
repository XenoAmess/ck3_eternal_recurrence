#include "xar_bridge/ck3_1210_hotfix26757580_v1.hpp"
#include "xar_bridge/ck3_1210_full_snapshot_v1.hpp"
#include "xar_bridge/ck3_1210_current_event_hotfix26757580_v1.hpp"
#include <cstring>
#include <utility>
#if defined(_MSC_VER)
#include <windows.h>
#endif
namespace xar::ck3_1210 {
namespace {
bool Copy(const void *source, void *dest, std::size_t count) noexcept {
  if (!source || !dest) return false;
#if defined(_MSC_VER)
  __try { std::memcpy(dest,source,count); return true; }
  __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  std::memcpy(dest,source,count); return true;
#endif
}
struct Anchor {
  void *state=nullptr,*jomini=nullptr,*storage=nullptr,*data=nullptr,*actor=nullptr;
  friend bool operator==(const Anchor&,const Anchor&)=default;
};
bool SameCore(const CoreSnapshotPrefix &a,const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw==b.clock.date_raw && a.clock.speed==b.clock.speed &&
    a.clock.paused==b.clock.paused && a.local_player_id==b.local_player_id &&
    a.map_ready==b.map_ready && a.has_played_character==b.has_played_character &&
    a.played_character_id==b.played_character_id && a.played_character_alive==b.played_character_alive;
}
bool Capture(const CoreBindings &b,const CoreSnapshotPrefix &p,Anchor &a) noexcept {
  return Copy(b.game_state_slot,&a.state,sizeof(void*)) && a.state &&
    Copy(b.jomini_state_slot,&a.jomini,sizeof(void*)) && a.jomini &&
    Copy(b.character_storage_slot,&a.storage,sizeof(void*)) && a.storage &&
    Copy(static_cast<std::byte*>(a.state)+kGameStateDataOffset,&a.data,sizeof(void*)) && a.data &&
    (a.actor=ResolveCoreCharacter(b,p.played_character_id))!=nullptr;
}
bool Fail(FullSnapshotDiagnosticsV1 &d,std::string_view stage,std::string_view why) noexcept {
 d.complete=false;d.stage=stage;d.reason=why;return false;
}
bool ReadPass(const FullSnapshotBindingsV1 &b,const CoreSnapshotPrefix &p,
    xar::game::Snapshot &s,FullSnapshotDiagnosticsV1 &d,
    IngameReadyWitnessV1 &witness,const IngameReadyGraphV1 &ingame) {
  std::string_view ingame_reason;
  if(!IsHotfix(b.core.image_build) && !ConfirmIngameReadyV1(b.ingame_ready,witness,ingame,ingame_reason))
    return Fail(d,"ingame",ingame_reason);
  ActorFoundationObservationV1 f{};
  if(!ReadActorFoundationV1(b.foundation,p,f) || !f.resources_ready || !f.relationships_ready ||
     !f.gold_raw || !f.prestige_raw || !f.piety_raw || !f.stress_points || !f.relationships)
    return Fail(d,"foundation",f.unavailable_reason);
  if(*f.stress_points<0) return Fail(d,"foundation","negative_stress_not_gameplay_qualified");
  CurrentEventSnapshotObservationV1 e{};
  if(!ReadCurrentEventSnapshotV1(b.event,p,e)) return Fail(d,"event",e.unavailable_reason);
  PendingSnapshotObservationV1 q{};
  if(!ReadPendingSnapshotV1(b.pending,p,q)) return Fail(d,"pending",q.unavailable_reason);
  std::vector<xar::game::ArmySnapshot> armies;
#if defined(XAR_CK3_ENABLE_1210_ARMY_BASE_FULL_V1)
  if(b.enable_army_base) {
    ActiveWarsObservationV1 wars{};
    if(!ReadActiveWarsV1(b.war_identity,p,wars) || !wars.identity_complete || !wars.active_wars)
      return Fail(d,"military",wars.unavailable_reason);
    if(!wars.active_wars->empty())return Fail(d,"military","active_wars_nonempty_rich_observation_unavailable");
    ArmyBaseObservationV1 m{};
    const bool read=ReadArmyBaseV1(b.army_base,p,m,b.army_fixture_access);
    d.army_state_calls_attempted+=m.native_state_calls_attempted;
    if(!read || !m.available ||
        !m.same_frame_ready || !m.collection_complete || !m.army_base_qualified || !m.player_armies)
      return Fail(d,"military",m.unavailable_reason);
    armies=std::move(*m.player_armies);
    d.unit_slots_scanned=m.unit_slots_scanned;d.war_slots_scanned=wars.war_slots_scanned;
  } else
#endif
  {
    MilitaryEmptyObservationV1 m{};
    if(!ReadMilitaryEmptyV1(b.military,p,m) || !m.player_armies_empty_proven || !m.active_wars_empty_proven)
      return Fail(d,"military",m.unavailable_reason);
    d.unit_slots_scanned=m.unit_slots_scanned;d.war_slots_scanned=m.war_slots_scanned;
  }
  d.pending_slots_scanned=q.slots_scanned;
  if(!IsHotfix(b.core.image_build) && !ConfirmIngameReadyV1(b.ingame_ready,witness,ingame,ingame_reason))
    return Fail(d,"ingame",ingame_reason);
  CoreSnapshotPrefix after{};
  if(!ReadCoreSnapshot(b.core,after) || !SameCore(p,after)) return Fail(d,"core","full_snapshot_core_changed");
  s={};s.date_raw=p.clock.date_raw;s.speed=p.clock.speed;s.paused=p.clock.paused;
  s.player_id=p.local_player_id;s.map_ready=p.map_ready;s.has_played_character=p.has_played_character;
  s.played_character_id=p.played_character_id;s.played_character_alive=p.played_character_alive;
  s.played_character_stress_points=*f.stress_points;
  s.played_character_gold={*f.gold_raw,f.resource_scale};
  s.played_character_prestige={*f.prestige_raw,f.resource_scale};
  s.played_character_piety={*f.piety_raw,f.resource_scale};
  s.played_character_betrothed_id=f.relationships->betrothed_character_id;
  s.played_character_primary_spouse_id=f.relationships->primary_spouse_character_id;
  s.played_character_spouse_ids=f.relationships->spouse_character_ids;
  s.has_active_event=e.found;s.active_event_instance_id=e.active_event_instance_id;
  s.active_event_option_count=e.active_event_option_count;
  s.has_pending_character_interaction=q.found;s.pending_character_interaction_id=q.pending_character_interaction_id;
  s.pending_sender_character_id=q.pending_sender_character_id;
  s.pending_auto_accept_notification=q.pending_auto_accept_notification; // Legacy wire alias: native is_notification.
  s.player_armies=std::move(armies);
  // War emptiness and every army row follow complete typed military transcripts.
  // Optional settlement unsupported: no capability. Traits remain omitted.
  return true;
}
}
FullSnapshotBindingsV1 BindFullSnapshotImageV1(std::uintptr_t base,std::string_view sha) noexcept {
 FullSnapshotBindingsV1 b{};b.core=BindCoreImage(base,sha);
 if(!b.core.enabled) return b;
 b.ingame_ready=BindIngameReadyImageV1(base,sha);
 b.foundation=BindActorFoundationImageV1(base,sha);b.event=BindCurrentEventSnapshotImageV1(base,sha);
 b.pending=BindPendingSnapshotImageV1(base,sha);b.military=BindMilitaryEmptyImageV1(base,sha);
#if defined(XAR_CK3_ENABLE_1210_ARMY_BASE_FULL_V1)
 b.army_base=BindArmyBaseImageV1(base,sha);b.war_identity=BindActiveWarsImageV1(base,sha);b.enable_army_base=!IsHotfix(b.core.image_build);
#endif
 const bool pending_hotfix = sha == pending_hotfix26757580::kExecutableSha256;
 const auto &pending_predicate_pin = pending_hotfix ? pending_hotfix26757580::kPredicateEntry32 : kPendingPredicateEntry32V1;
 const auto &pending_validator_pin = pending_hotfix ? pending_hotfix26757580::kValidatorEntry32 : kPendingValidatorEntry32V1;
 std::array<std::uint8_t,32> a{},c{},d{};
 const bool pins=Copy(reinterpret_cast<void*>(b.event.get_current_event),a.data(),a.size()) &&
   Copy(reinterpret_cast<void*>(b.pending.is_pending_for_character),c.data(),c.size()) &&
   Copy(reinterpret_cast<void*>(b.pending.validate_reply),d.data(),d.size()) &&
   a==(IsHotfix(b.core.image_build)?bb3_current_event_profile36::kCurrentEventSelectorEntry32V1:kCurrentEventSelectorEntry32V1) && c==pending_predicate_pin && d==pending_validator_pin;
 b.exact_build_admitted=pins && b.core.enabled &&
   (IsHotfix(b.core.image_build) || b.ingame_ready.exact_build_admitted) &&
   b.foundation.exact_build_admitted && b.event.exact_build_admitted &&
   b.pending.exact_build_admitted && b.military.exact_build_admitted;
 return b;
}
bool ReadFullSnapshotV1(const FullSnapshotBindingsV1 &b,xar::game::Snapshot &out,
 FullSnapshotDiagnosticsV1 &d,IngameReadyWitnessV1 &witness) noexcept {
 out={};d={};
 const auto same=[&](const CoreBindings &c) noexcept {
   return c.enabled && c.image_build==b.core.image_build && c.game_state_slot==b.core.game_state_slot && c.jomini_state_slot==b.core.jomini_state_slot &&
    c.character_storage_slot==b.core.character_storage_slot && c.get_local_player==b.core.get_local_player;
 };
 if(!b.exact_build_admitted || !b.core.enabled || (!IsHotfix(b.core.image_build) && (!b.ingame_ready.exact_build_admitted ||
    !same(b.ingame_ready.core))) || !b.foundation.exact_build_admitted ||
    !b.event.exact_build_admitted || !b.pending.exact_build_admitted || !b.military.exact_build_admitted ||
    !same(b.foundation.core) || !same(b.event.core) || !same(b.pending.core) || !same(b.military.core)) {
   witness={};return Fail(d,"binding","full_snapshot_exact_build_unavailable");
 }
#if defined(XAR_CK3_ENABLE_1210_ARMY_BASE_FULL_V1)
 if(b.enable_army_base && (!b.army_base.exact_build_admitted || !b.war_identity.exact_build_admitted ||
    !same(b.army_base.player_armies.core) || !same(b.war_identity.core)))
   {witness={};return Fail(d,"binding","full_snapshot_army_base_binding_mismatch");}
#endif
 try {
  IngameReadyObservationV1 ready{};
  // The remote lifecycle reader is qualified only for the original image.
  // BB3 keeps basic36 empty-only Full and never mints that lifecycle witness.
  if(IsHotfix(b.core.image_build))witness={};
  else if(!ObserveIngameReadyV1(b.ingame_ready,witness,ready)) return Fail(d,"ingame",ready.unavailable_reason);
  CoreSnapshotPrefix p{};
  if(!ReadCoreSnapshot(b.core,p) || !p.clock.paused || !p.map_ready || !p.has_played_character || !p.played_character_alive)
   return Fail(d,"core","full_snapshot_requires_paused_played_map");
  Anchor before{},after{};
  if(!Capture(b.core,p,before)) return Fail(d,"root","full_snapshot_root_unavailable");
  xar::game::Snapshot first{},second{};
  if(!ReadPass(b,p,first,d,witness,ready.graph)) return false;
  d.completed_passes=1;
  if(!Capture(b.core,p,after) || before!=after) return Fail(d,"root","full_snapshot_root_changed");
  std::string_view ingame_reason;
  if(!IsHotfix(b.core.image_build) && !ConfirmIngameReadyV1(b.ingame_ready,witness,ready.graph,ingame_reason)) return Fail(d,"ingame",ingame_reason);
  if(!ReadPass(b,p,second,d,witness,ready.graph)) return false;
  d.completed_passes=2;
  if(!Capture(b.core,p,after) || before!=after) return Fail(d,"root","full_snapshot_root_changed");
  if(!IsHotfix(b.core.image_build) && !ConfirmIngameReadyV1(b.ingame_ready,witness,ready.graph,ingame_reason)) return Fail(d,"ingame",ingame_reason);
  if(first!=second) return Fail(d,"coherence","full_snapshot_observations_changed");
  out=std::move(second);d.complete=true;d.stage="complete";d.reason={};return true;
 } catch(...) {out={};witness={};return Fail(d,"exception","full_snapshot_read_exception");}
}
}
