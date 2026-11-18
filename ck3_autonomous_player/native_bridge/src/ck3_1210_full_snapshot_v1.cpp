#include "xar_bridge/ck3_1210_full_snapshot_v1.hpp"
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
    xar::game::Snapshot &s,FullSnapshotDiagnosticsV1 &d) {
  ActorFoundationObservationV1 f{};
  if(!ReadActorFoundationV1(b.foundation,p,f) || !f.resources_ready || !f.relationships_ready ||
     !f.gold_raw || !f.prestige_raw || !f.piety_raw || !f.stress_points || !f.relationships)
    return Fail(d,"foundation",f.unavailable_reason);
  if(*f.stress_points<0) return Fail(d,"foundation","negative_stress_not_gameplay_qualified");
  CurrentEventSnapshotObservationV1 e{};
  if(!ReadCurrentEventSnapshotV1(b.event,p,e)) return Fail(d,"event",e.unavailable_reason);
  PendingSnapshotObservationV1 q{};
  if(!ReadPendingSnapshotV1(b.pending,p,q)) return Fail(d,"pending",q.unavailable_reason);
  MilitaryEmptyObservationV1 m{};
  if(!ReadMilitaryEmptyV1(b.military,p,m) || !m.player_armies_empty_proven || !m.active_wars_empty_proven)
    return Fail(d,"military",m.unavailable_reason);
  d.pending_slots_scanned=q.slots_scanned;d.unit_slots_scanned=m.unit_slots_scanned;d.war_slots_scanned=m.war_slots_scanned;
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
  // Empty arrays are populated only after complete typed military transcripts.
  // Optional settlement unsupported: no capability. Traits remain omitted.
  return true;
}
}
FullSnapshotBindingsV1 BindFullSnapshotImageV1(std::uintptr_t base,std::string_view sha) noexcept {
 FullSnapshotBindingsV1 b{};b.core=BindCoreImage(base,sha);
 if(!b.core.enabled) return b;
 b.foundation=BindActorFoundationImageV1(base,sha);b.event=BindCurrentEventSnapshotImageV1(base,sha);
 b.pending=BindPendingSnapshotImageV1(base,sha);b.military=BindMilitaryEmptyImageV1(base,sha);
 std::array<std::uint8_t,32> a{},c{},d{};
 const bool pins=Copy(reinterpret_cast<void*>(base+kCurrentEventSelectorRvaV1),a.data(),a.size()) &&
   Copy(reinterpret_cast<void*>(base+kPendingSnapshotPredicateRvaV1),c.data(),c.size()) &&
   Copy(reinterpret_cast<void*>(base+kPendingSnapshotValidatorRvaV1),d.data(),d.size()) &&
   a==kCurrentEventSelectorEntry32V1 && c==kPendingPredicateEntry32V1 && d==kPendingValidatorEntry32V1;
 b.exact_build_admitted=pins && b.core.enabled && b.foundation.exact_build_admitted && b.event.exact_build_admitted &&
   b.pending.exact_build_admitted && b.military.exact_build_admitted;
 return b;
}
bool ReadFullSnapshotV1(const FullSnapshotBindingsV1 &b,xar::game::Snapshot &out,
 FullSnapshotDiagnosticsV1 &d) noexcept {
 out={};d={};
 const auto same=[&](const CoreBindings &c) noexcept {
   return c.enabled && c.game_state_slot==b.core.game_state_slot && c.jomini_state_slot==b.core.jomini_state_slot &&
    c.character_storage_slot==b.core.character_storage_slot && c.get_local_player==b.core.get_local_player;
 };
 if(!b.exact_build_admitted || !b.core.enabled || !b.foundation.exact_build_admitted ||
    !b.event.exact_build_admitted || !b.pending.exact_build_admitted || !b.military.exact_build_admitted ||
    !same(b.foundation.core) || !same(b.event.core) || !same(b.pending.core) || !same(b.military.core))
   return Fail(d,"binding","full_snapshot_exact_build_unavailable");
 try {
  CoreSnapshotPrefix p{};
  if(!ReadCoreSnapshot(b.core,p) || !p.clock.paused || !p.map_ready || !p.has_played_character || !p.played_character_alive)
   return Fail(d,"core","full_snapshot_requires_paused_played_map");
  Anchor before{},after{};
  if(!Capture(b.core,p,before)) return Fail(d,"root","full_snapshot_root_unavailable");
  xar::game::Snapshot first{},second{};
  if(!ReadPass(b,p,first,d)) return false;
  d.completed_passes=1;
  if(!Capture(b.core,p,after) || before!=after) return Fail(d,"root","full_snapshot_root_changed");
  if(!ReadPass(b,p,second,d)) return false;
  d.completed_passes=2;
  if(!Capture(b.core,p,after) || before!=after) return Fail(d,"root","full_snapshot_root_changed");
  if(first!=second) return Fail(d,"coherence","full_snapshot_observations_changed");
  out=std::move(second);d.complete=true;d.stage="complete";d.reason={};return true;
 } catch(...) {out={};return Fail(d,"exception","full_snapshot_read_exception");}
}
}
