#include "ck3_121003_full111_event_read_v1.hpp"
#include <array>
#include <cstring>
#include <limits>
#include <optional>
#include <type_traits>
#include <vector>
#include <windows.h>

#if defined(XAR_CK3_ENABLE_121003_OWNED_ARMY123)
// Private declaration: preserve the shared Military/Full/Date header ABI.
namespace xar::ck3_1210 {
bool ReadActiveWarsEmptyV1(const MilitaryEmptyBindingsV1 &,
    const CoreSnapshotPrefix &, MilitaryEmptyObservationV1 &,
    MilitaryEmptyReadAccessV1 access = {}) noexcept;
}
#endif

namespace xar::ck3_121003::full111 {
namespace {
#if defined(XAR_CK3_ENABLE_121003_FULL111)
using EventWitness=build26785313::Full111OrdinaryEventWitnessV1;
using namespace ck3_1210;
constexpr std::uintptr_t kUnitRegistry=0x6A66AA0,kWarRegistry=0x6A669D0;
constexpr std::uintptr_t kPendingRegistry=0x6A67480;
constexpr std::uintptr_t kUnitManagerVt=0x4EA42E0,kUnitRegistryVt=0x4EA41E8;
constexpr std::uintptr_t kWarManagerVt=0x4E9C470,kWarRegistryVt=0x4E9C368;
constexpr std::uintptr_t kPendingManagerVt=0x4E981B0,kPendingRegistryVt=0x4E982F8;
constexpr std::uintptr_t kPendingObjectVt=0x4E769B8;
constexpr std::uintptr_t kSpouseDefault=0x5D3E6F8;
constexpr std::size_t kUnitManager=0x3ABF8,kWarManager=0x3F2D8,kPendingManager=0x113C0;
constexpr std::size_t kEventManager=0x44BC0;
bool Copy(const void *from,void *to,std::size_t n) noexcept {
 if(!from||!to)return false;
 __try {std::memcpy(to,from,n);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
template<class T> bool At(const void *from,std::size_t offset,T &v) noexcept {
 const auto a=reinterpret_cast<std::uintptr_t>(from);
 const auto max=(std::numeric_limits<std::uintptr_t>::max)();
 return a&&offset<=max-a&&sizeof(T)-1<=max-a-offset&&
     Copy(reinterpret_cast<const void *>(a+offset),&v,sizeof(v));
}
bool Core(const CoreBindings &b,CoreSnapshotPrefix &p) noexcept {
 __try {return ReadCoreSnapshot(b,p);}
 __except(EXCEPTION_EXECUTE_HANDLER){p={};return false;}
}
bool Same(const CoreSnapshotPrefix&a,const CoreSnapshotPrefix&b) noexcept {
 return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&
 a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&
 a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;
}
bool Fail(FullSnapshotDiagnosticsV1 &d,std::string_view stage,std::string_view why) noexcept {
 d.complete=false;d.stage=stage;d.reason=why;return false;
}
struct Roots {
 void *game=nullptr,*jomini=nullptr,*data=nullptr,*storage=nullptr,*actor=nullptr,*family=nullptr,*living=nullptr;
 #if defined(XAR_CK3_ENABLE_121003_OWNED_ARMY123)
 std::vector<std::uint64_t> owned_words;
 #endif
 friend bool operator==(const Roots&,const Roots&)=default;
};
bool Resolve(const void *storage,std::int32_t id,void *&result) noexcept {
 result=nullptr;if(id==-1)return false;
 void *slots=nullptr,*p=nullptr;std::int32_t capacity=0,actual=-1;std::uint32_t tag=0;
 const auto index=static_cast<std::uint32_t>(id)&0xFFFFFFU;
 if(!At(storage,0x20,slots)||!At(storage,0x2C,capacity)||capacity<=0||capacity>16'777'216||
 index>=static_cast<std::uint32_t>(capacity)||!At(slots,static_cast<std::size_t>(index)*16+8,p)||!p||
 !At(p,0x18,actual)||actual!=id||!At(p,0x1C,tag)||tag!=0x43686172U)return false;
 result=p;return true;
}
bool Capture(const CoreBindings &b,const CoreSnapshotPrefix &p,Roots &r) noexcept {
 if(!At(b.game_state_slot,0,r.game)||!At(b.jomini_state_slot,0,r.jomini)||
 !At(b.character_storage_slot,0,r.storage)||!At(r.game,0xA0,r.data)||!r.data||!r.jomini||
 !Resolve(r.storage,p.played_character_id,r.actor)||!At(r.actor,0x1A8,r.family)||!At(r.actor,0x1B0,r.living))return false;
 void *death=nullptr;return At(r.actor,0x1D0,death)&&!death;
}
bool ScalarRelation(const Roots &r,std::size_t offset,std::int32_t &id) noexcept {
 id=-1;if(r.family&&!At(r.family,offset,id))return false;
 if(id==-1)return true;void *peer=nullptr;return Resolve(r.storage,id,peer);
}
bool Foundation(const Roots&r,std::uintptr_t module,xar::game::Snapshot&s) {
 std::int64_t gold=0,prestige=0,piety=0;std::int32_t stress=0;
 if(r.living&&(!At(r.living,0x100,gold)||!At(r.living,0x130,prestige)||!At(r.living,0x110,piety)||!At(r.living,0x2F8,stress)))return false;
 if(stress<0)return false;
 s.played_character_gold={gold,100'000};s.played_character_prestige={prestige,100'000};
 s.played_character_piety={piety,100'000};s.played_character_stress_points=stress;
 if(!ScalarRelation(r,0x10,s.played_character_betrothed_id)||!ScalarRelation(r,0x14,s.played_character_primary_spouse_id))return false;
 const void *vector=r.family?static_cast<const std::byte*>(r.family)+0x20:
 reinterpret_cast<const void*>(module+kSpouseDefault);
 void *items=nullptr;std::int32_t count=0;
 // Current CSpouseListBuilder reads pointer/+C count. Capacity is not borrowed
 // from the previous executable. The bound below is our finite read scope.
 if(!At(vector,0,items)||!At(vector,0xC,count)||count<0||count>64||(count&&!items))return false;
 s.played_character_spouse_ids.clear();s.played_character_spouse_ids.reserve(static_cast<std::size_t>(count));
 for(std::int32_t i=0;i<count;++i){std::int32_t id=-1;void *peer=nullptr;
  if(!At(items,static_cast<std::size_t>(i)*4,id)||!Resolve(r.storage,id,peer))return false;
  s.played_character_spouse_ids.push_back(id);
 }
 return true;
}
bool PendingOwner(const Roots&r,std::uintptr_t base) noexcept {
 std::uintptr_t vt=0;void *owned=nullptr,*global=nullptr;
 // The current registry ctor allocates heap RSI and stores it into the
 // incoming manager+50 pointer cell. Singleton publication is conditional,
 // so the gate independently requires that cell value to match the current global.
 return At(r.data,kPendingManager,vt)&&vt==base+kPendingManagerVt&&
 At(r.data,kPendingManager+0x50,owned)&&At(reinterpret_cast<void*>(base+kPendingRegistry),0,global)&&
 owned&&owned==global&&At(global,0,vt)&&vt==base+kPendingRegistryVt;
}
bool ReadEventQueue(const Roots &r,const CoreSnapshotPrefix &p,xar::game::Snapshot &s,
 const OrdinaryEventReaderV1 *reader,std::optional<EventWitness> &observed,
 FullSnapshotDiagnosticsV1 &d) {
 const auto *manager=static_cast<const std::byte*>(r.data)+kEventManager;
 void *items=nullptr;std::int32_t count=0;
 // The current selector's complete native CFG consumes this exact queue.
 if(!At(manager,0x1F18,items))return Fail(d,"event","current111_event_items_slot_unreadable");
 if(!At(manager,0x1F24,count))return Fail(d,"event","current111_event_count_slot_unreadable");
 if(count<0||(count>0&&!items))return Fail(d,"event","current111_event_queue_header_invalid");
 if(count==0)return true;
 if(!reader||!reader->read)return Fail(d,"event","current111_nonempty_event_lifetime_unavailable");
 if(count!=1)return Fail(d,"event","current111_ordinary_event_queue_not_single");
 auto &witness=observed.emplace();
 if(!reader->read(reader->context,p,witness))
  return Fail(d,"event","current111_ordinary_event_owner_observation_unavailable");
 const auto &queue=witness.queue;
 const auto &roots=witness.scene.event_roots;
 const auto &raw=witness.raw;
 const auto &source=raw.source.events;
 if(queue.game_data!=reinterpret_cast<std::uintptr_t>(r.data)||
     queue.items!=reinterpret_cast<std::uintptr_t>(items)||queue.count!=count||
     witness.scene.kind!=build26785313::LydKind267V1::events||raw.source.kind!=witness.scene.kind||
     witness.scene.jomini!=reinterpret_cast<std::uintptr_t>(r.jomini)||
     roots.size()!=1||!roots.front().visible||!source||!source->census_complete||
     source->named_root_count!=1||source->events.size()!=1||raw.event_rows.size()!=1||
     !raw.cleanup_known||raw.manager_census.game!=reinterpret_cast<std::uintptr_t>(r.game))
  return Fail(d,"event","current111_ordinary_event_witness_mismatch");
 const auto &event=source->events.front();
 const auto &row=raw.event_rows.front();
 if(event.instance_id<=0||event.instance_id!=row.instance_id||
     event.recipient_character_id!=p.played_character_id||!event.window_visible||!event.named_root_bound||
     event.authored_option_count<0||event.authored_option_count>64||
     event.authored_option_count!=row.material.authored_option_count||
     !row.controller||!row.root||row.root!=roots.front().widget||
     !row.runtime||row.runtime!=queue.rows.front()||!row.definition)
  return Fail(d,"event","current111_ordinary_event_identity_mismatch");
 s.has_active_event=true;
 s.active_event_instance_id=event.instance_id;
 s.active_event_option_count=event.authored_option_count;
 return true;
}
#if defined(XAR_CK3_ENABLE_121003_OWNED_ARMY123)
#include "owned_army_identity123.inc"
#endif
bool Pass(const FullSnapshotBindingsV1 &b,const CoreSnapshotPrefix &p,std::uintptr_t base,
 Roots &r,xar::game::Snapshot &s,FullSnapshotDiagnosticsV1 &d,const OrdinaryEventReaderV1 *reader,
 std::optional<EventWitness> &event) {
 s={};if(!Capture(b.core,p,r))return Fail(d,"root","current111_root_or_actor_unavailable");
 if(!Foundation(r,base,s))return Fail(d,"foundation","current111_resources_or_family3_unavailable");
 if(!ReadEventQueue(r,p,s,reader,event,d))return false;
 if(!PendingOwner(r,base))return Fail(d,"pending","current111_pending_owner_mismatch");
 PendingSnapshotObservationV1 pending{};
 if(!ReadPendingSnapshotV1(b.pending,p,pending))return Fail(d,"pending",pending.unavailable_reason);
 MilitaryEmptyObservationV1 military{};
#if defined(XAR_CK3_ENABLE_121003_OWNED_ARMY123)
 if(!ReadActiveWarsEmptyV1(b.military,p,military)||!military.active_wars_empty_proven)
  return Fail(d,"military",military.unavailable_reason);
 OwnedUnitPass123 owned{r,b,p,base};
 if(!owned.Capture(s.player_armies))return Fail(d,"military",owned.reason);
 d.unit_slots_scanned=owned.scanned;
#else
 if(!ReadMilitaryEmptyV1(b.military,p,military)||!military.player_armies_empty_proven||!military.active_wars_empty_proven)
  return Fail(d,"military",military.unavailable_reason);
 d.unit_slots_scanned=military.unit_slots_scanned;
#endif
 s.date_raw=p.clock.date_raw;s.speed=p.clock.speed;s.paused=p.clock.paused;s.player_id=p.local_player_id;
 s.map_ready=p.map_ready;s.has_played_character=p.has_played_character;s.played_character_id=p.played_character_id;
 s.played_character_alive=p.played_character_alive;
 s.has_pending_character_interaction=pending.found;s.pending_character_interaction_id=pending.pending_character_interaction_id;
 s.pending_sender_character_id=pending.pending_sender_character_id;s.pending_auto_accept_notification=pending.pending_auto_accept_notification;
 d.pending_slots_scanned=pending.slots_scanned;d.war_slots_scanned=military.war_slots_scanned;
 CoreSnapshotPrefix after{};return Core(b.core,after)&&Same(p,after);
}
#endif
}
ck3_1210::CoreBindings BindCore(std::uintptr_t base,std::string_view sha) noexcept {
#if defined(XAR_CK3_ENABLE_121003_FULL111)
 auto core=build26785313::BindReadonlyImage(base,sha).core;
 if(core.enabled)core.image_build=ck3_1210::ImageBuildV1::full11126785313;
 return core;
#else
 static_cast<void>(base);static_cast<void>(sha);return {};
#endif
}
ck3_1210::FullSnapshotBindingsV1 BindFull(std::uintptr_t base,std::string_view sha) noexcept {
#if defined(XAR_CK3_ENABLE_121003_FULL111)
 using namespace ck3_1210;FullSnapshotBindingsV1 b{};b.core=BindCore(base,sha);
 if(!b.core.enabled)return b;
 b.military.core=b.core;b.military.exact_build_admitted=true;
 b.military.unit_registry_slot=reinterpret_cast<void**>(base+kUnitRegistry);b.military.war_registry_slot=reinterpret_cast<void**>(base+kWarRegistry);
 b.military.unit_manager_vtable=base+kUnitManagerVt;b.military.unit_registry_vtable=base+kUnitRegistryVt;
 b.military.war_manager_vtable=base+kWarManagerVt;b.military.war_registry_vtable=base+kWarRegistryVt;
 b.pending.core=b.core;b.pending.pending_storage_slot=reinterpret_cast<void**>(base+kPendingRegistry);
 b.pending.is_pending_for_character=reinterpret_cast<PendingForCharacterV1>(base+0x14DECD0);
 b.pending.validate_reply=reinterpret_cast<PendingReplyValidatorV1>(base+0x2E4F7A0);
 b.pending.database_vtable=base+kPendingRegistryVt;b.pending.pending_vtable=base+kPendingObjectVt;
 // Current CReplyCharacterInteractionCommand COL/TD and its two tables are
 // retained by CACHE561. Validation is read-only; no reply command is queued.
 b.pending.reply_primary_vtable=base+0x4AF4900;b.pending.reply_secondary_vtable=base+0x4AF48C8;
 b.pending.exact_build_admitted=true;b.enable_army_base=false;b.exact_build_admitted=true;
 return b;
#else
 static_cast<void>(base);static_cast<void>(sha);return {};
#endif
}
namespace {
bool ReadFullImpl(const ck3_1210::FullSnapshotBindingsV1&b,xar::game::Snapshot &out,
 ck3_1210::FullSnapshotDiagnosticsV1 &d,[[maybe_unused]]const OrdinaryEventReaderV1 *reader) noexcept {
#if defined(XAR_CK3_ENABLE_121003_FULL111)
 using namespace ck3_1210;out={};d={};
 if(!b.exact_build_admitted||!b.core.enabled)return Fail(d,"binding","current111_exact_profile_unavailable");
 const auto base=reinterpret_cast<std::uintptr_t>(b.core.game_state_slot)-build26785313::kGameStateSlotRva;
 try {
  CoreSnapshotPrefix p{};
  if(!Core(b.core,p)||!p.clock.paused||!p.map_ready||!p.has_played_character||!p.played_character_alive)
   return Fail(d,"core","full_snapshot_requires_paused_played_map");
  Roots first_roots{},second_roots{};xar::game::Snapshot first{},second{};
  std::optional<EventWitness> first_event,second_event;
  if(!Pass(b,p,base,first_roots,first,d,reader,first_event))return false;d.completed_passes=1;
  if(!Pass(b,p,base,second_roots,second,d,reader,second_event))return false;d.completed_passes=2;
  if(first_roots!=second_roots||first!=second||first_event!=second_event)
   return Fail(d,"coherence","current111_full_observations_changed");
  out=std::move(second);d.complete=true;d.stage="complete";d.reason={};return true;
 }catch(...){out={};return Fail(d,"exception","current111_full_read_exception");}
#else
 static_cast<void>(b);out={};d={};d.stage="binding";d.reason="current111_feature_disabled";return false;
#endif
}
}
bool ReadFull(const ck3_1210::FullSnapshotBindingsV1&b,xar::game::Snapshot &out,
 ck3_1210::FullSnapshotDiagnosticsV1 &d) noexcept {
 return ReadFullImpl(b,out,d,nullptr);
}
bool ReadFullWithOrdinaryEventV1(const ck3_1210::FullSnapshotBindingsV1&b,xar::game::Snapshot &out,
 ck3_1210::FullSnapshotDiagnosticsV1 &d,const OrdinaryEventReaderV1 &reader) noexcept {
 return ReadFullImpl(b,out,d,&reader);
}
}
