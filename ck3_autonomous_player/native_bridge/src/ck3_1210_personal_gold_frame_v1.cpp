#if defined(XAR_CK3_ENABLE_1210_CHARACTER_ROSTER_V1)
#include "xar_bridge/ck3_1210_character_roster_frame_v1.hpp"
#endif
#include "xar_bridge/ck3_1210_personal_gold_frame_v1.hpp"
#include "xar_bridge/ck3_1210_adapter.hpp"
#if defined(XAR_CK3_ENABLE_1210_PERSONAL_CASH_V1)
#include "xar_bridge/ck3_1210_personal_cash_frame_v1.hpp"
#endif
#if defined(XAR_CK3_ENABLE_1210_ACTIVE_WARS_IDENTITY_V1)
#include "xar_bridge/ck3_1210_active_wars_frame_v1.hpp"
#endif
#if defined(XAR_CK3_ENABLE_26757580_OPENING_READONLY56)
#include "xar_bridge/ck3_1210_opening_frame56.hpp"
#endif
#include <windows.h>
#include <cstring>
#include "xar_bridge/ck3_1210_thread_runtime.hpp"
#if defined(XAR_CK3_ENABLE_1210_ACTOR_RESOURCE_LEAF_V2)
#include "xar_bridge/ck3_1210_scoped_image_roots_v1.hpp"
#endif
namespace xar::ck3_1210 {
namespace {
#if defined(XAR_CK3_ENABLE_1210_ACTOR_RESOURCE_LEAF_V2)
// The source reader receives no free-standing caller bool as final proof.
// Revalidate the ACTUAL module, installed exact1210 TLS source, active ticket,
// current TLS marker/context, physical Game/Jomini objects and paused date.
bool ResourceTargetsCurrentV2(const PersonalGoldMailboxContextV1 &q,
    const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  if(q.game==nullptr || !game::IsCk3_1210Descriptor(q.game->descriptor()) || q.mailbox==nullptr ||
      q.image_base==0 || q.ticket.sequence==0 ||
      q.image_base!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)))return false;
  const auto rebound=BindCoreImage(q.image_base,q.game->descriptor().executable_sha256);
  const auto &core=q.bindings.core;
  // This comparison precedes every arbitrary Core-slot dereference/getter.
  if(!q.bindings.exact_build_admitted || !core.enabled || !rebound.enabled ||
      core.game_state_slot!=rebound.game_state_slot || core.jomini_state_slot!=rebound.jomini_state_slot ||
      core.character_storage_slot!=rebound.character_storage_slot || core.get_local_player!=rebound.get_local_player)return false;
  const auto &m=*q.mailbox;
  if(m.offline_fixture || m.module_base!=q.image_base || s.thread_id==0 || s.thread_id!=GetCurrentThreadId() ||
      s.pump_epoch==0 || s.tls_initialized!=1 || s.tls_main_thread_marker!=1 || s.tls_context==0 || !s.paused ||
      !m.iat_hook_installed.load() || m.owner_thread_id.load()!=s.thread_id || m.failure_flags.load()!=0 ||
      m.stop_requested.load() || m.proof_reset_requested.load() || m.active_hook_calls.load()==0 ||
      m.pump_epochs.load()!=s.pump_epoch || m.executor_started_sequence.load()!=q.ticket.sequence ||
      m.executor_started_pump_epoch.load()!=s.pump_epoch ||
      m.paused_owner_verified_pump_epochs.load()<ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
      m.state.load()!=ck3_11906::MainThreadQueryMailboxStateV1::executing ||
      m.published_sequence.load()!=q.ticket.sequence || m.executor_context!=&q || m.executor.load()!=&ExecutePersonalGoldMailboxV1 ||
      m.tls_initialized_flag!=q.image_base+kMainThreadTlsInitializedFlagRva ||
      s.tls_initialized_flag_address!=m.tls_initialized_flag ||
      reinterpret_cast<std::uintptr_t>(m.tls_context_getter)!=q.image_base+kMainThreadTlsContextGetterRva ||
      m.game_state_slot!=q.image_base+kGameStateSlotRva || m.jomini_state_slot!=q.image_base+kJominiStateSlotRva)return false;
#if defined(_MSC_VER)
  __try {
#endif
    if(*reinterpret_cast<const std::uint8_t *>(m.tls_initialized_flag)!=1)return false;
    const auto tls=reinterpret_cast<std::uintptr_t>(m.tls_context_getter());
    const auto game_state=*reinterpret_cast<const std::uintptr_t *>(m.game_state_slot);
    const auto jomini_state=*reinterpret_cast<const std::uintptr_t *>(m.jomini_state_slot);
    return tls==s.tls_context && *reinterpret_cast<const std::uint8_t *>(tls+ck3_11906::kMainThreadTlsMarkerOffset)==1 &&
        game_state!=0 && jomini_state!=0 && game_state==s.game_state && jomini_state==s.jomini_state &&
        *reinterpret_cast<const std::int32_t *>(game_state+kGameStateDateOffset)==s.date_raw &&
        *reinterpret_cast<const std::uint8_t *>(jomini_state+kJominiPausedOffset)!=0 &&
        !m.stop_requested.load() && !m.proof_reset_requested.load() && m.failure_flags.load()==0 &&
        m.iat_hook_installed.load() && m.active_hook_calls.load()>0 && m.pump_epochs.load()==s.pump_epoch &&
        m.executor_started_sequence.load()==q.ticket.sequence && m.executor_started_pump_epoch.load()==s.pump_epoch &&
        m.state.load()==ck3_11906::MainThreadQueryMailboxStateV1::executing &&
        m.published_sequence.load()==q.ticket.sequence && m.executor_context==&q && m.executor.load()==&ExecutePersonalGoldMailboxV1;
#if defined(_MSC_VER)
  } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
bool ResourceOwnerCurrentV2(const PersonalGoldMailboxContextV1 &q,
    const ck3_11906::MainThreadExecutionStampV1 &s,const CoreSnapshotPrefix &expected) noexcept {
  if(!ResourceTargetsCurrentV2(q,s))return false;
#if defined(_MSC_VER)
  __try {
#endif
    CoreSnapshotPrefix current{};
    return ReadCoreSnapshot(q.bindings.core,current) && current.clock.date_raw==expected.clock.date_raw &&
        current.clock.speed==expected.clock.speed && current.clock.paused==expected.clock.paused &&
        current.local_player_id==expected.local_player_id && current.map_ready==expected.map_ready &&
        current.has_played_character==expected.has_played_character && current.played_character_id==expected.played_character_id &&
        current.played_character_alive==expected.played_character_alive && ResourceTargetsCurrentV2(q,s);
#if defined(_MSC_VER)
  } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
struct ResourceScopeContextV2 {
  const PersonalGoldMailboxContextV1 *query;
  const ck3_11906::MainThreadExecutionStampV1 *stamp;
};
bool ResourceScopeCopyV2(void *,const void *source,void *target,std::size_t size) noexcept {
#if defined(_MSC_VER)
  __try {std::memcpy(target,source,size);return true;} __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
  (void)source;(void)target;(void)size;return false;
#endif
}
bool ResourceScopeValidateV2(void *context,const Scoped1210ImageSourceV1 &source,
    const CoreSnapshotPrefix &expected) noexcept {
  if(context==nullptr)return false;
  const auto &owner=*static_cast<ResourceScopeContextV2 *>(context);
  return owner.query!=nullptr && owner.stamp!=nullptr && owner.query->game!=nullptr &&
      source.image_base==owner.query->image_base && source.descriptor==&owner.query->game->descriptor() &&
      ResourceOwnerCurrentV2(*owner.query,*owner.stamp,expected);
}
#endif
// Private ordinary Actor readers only. Cash/War keep their own early routes;
// the Resource prefix is independently owned by slot43.
bool GoldFoundationTargetsV1(const PersonalGoldMailboxContextV1 &q,
    const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  const auto &m=*q.mailbox;
  if(m.offline_fixture)return true; // Explicit RAM model, never mapped-image proof.
  const auto base=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  const auto exact=BindCoreImage(base,q.game->descriptor().executable_sha256);
  const auto &b=q.bindings.core;
  // Validate the entire bundle before dereferencing a source slot or invoking
  // its GetLocalPlayer. Matching Game/Jomini pointers alone is insufficient.
  if(base==0 || !exact.enabled || !b.enabled || m.module_base!=base ||
      b.game_state_slot!=exact.game_state_slot || b.jomini_state_slot!=exact.jomini_state_slot ||
      b.character_storage_slot!=exact.character_storage_slot || b.get_local_player!=exact.get_local_player ||
      m.game_state_slot!=base+kGameStateSlotRva || m.jomini_state_slot!=base+kJominiStateSlotRva ||
      m.tls_initialized_flag!=base+kMainThreadTlsInitializedFlagRva ||
      s.tls_initialized_flag_address!=m.tls_initialized_flag ||
      reinterpret_cast<std::uintptr_t>(m.tls_context_getter)!=base+kMainThreadTlsContextGetterRva)return false;
  return *reinterpret_cast<const std::uint8_t *>(m.tls_initialized_flag)==1 &&
      reinterpret_cast<std::uintptr_t>(m.tls_context_getter())==s.tls_context &&
      *reinterpret_cast<const std::uint8_t *>(s.tls_context+ck3_11906::kMainThreadTlsMarkerOffset)==1;
}
bool GoldFoundationOwnerV1(const PersonalGoldMailboxContextV1 &q,
    const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  const bool gold=q.kind==ActorObservationKindV1::personal_gold;
  const bool foundation=q.kind==ActorObservationKindV1::foundation;
  if((!gold && !foundation) || !q.game || !q.game->enabled() ||
      !game::IsCk3_1210Descriptor(q.game->descriptor()) ||
      !q.game->supports(foundation?kActorFoundationCapabilityV1:kPersonalGoldCapabilityV1) ||
      !q.mailbox || q.ticket.sequence==0 || !q.bindings.exact_build_admitted)return false;
  const auto &m=*q.mailbox;const auto &b=q.bindings.core;
  if(s.thread_id==0 || s.thread_id!=GetCurrentThreadId() || s.pump_epoch==0 ||
      s.tls_initialized!=1 || s.tls_main_thread_marker!=1 || s.tls_context==0 ||
      !s.paused || s.game_state==0 || s.jomini_state==0 ||
      !m.iat_hook_installed.load() || m.active_hook_calls.load()==0 ||
      m.pump_epochs.load()!=s.pump_epoch || m.owner_thread_id.load()!=s.thread_id ||
      m.failure_flags.load()!=0 || m.stop_requested.load() || m.proof_reset_requested.load() ||
      m.paused_owner_verified_pump_epochs.load()<ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
      m.state.load()!=ck3_11906::MainThreadQueryMailboxStateV1::executing ||
      m.published_sequence.load()!=q.ticket.sequence || m.executor_started_sequence.load()!=q.ticket.sequence ||
      m.executor_started_pump_epoch.load()!=s.pump_epoch || m.executor_context!=&q ||
      m.executor.load()!=&ExecutePersonalGoldMailboxV1 ||
      !GoldFoundationTargetsV1(q,s) || !b.game_state_slot || !b.jomini_state_slot ||
      reinterpret_cast<std::uintptr_t>(*b.game_state_slot)!=s.game_state ||
      reinterpret_cast<std::uintptr_t>(*b.jomini_state_slot)!=s.jomini_state)return false;
  return true;
}
void GoldFoundationOwnerChangedV1(PersonalGoldMailboxContextV1 &q) noexcept {
  // Preserve the historical main-thread observation; close current DATA.
  q.observation={};q.foundation={};
  q.observation.unavailable_reason="actor_owner_source_changed";
  q.foundation.unavailable_reason="actor_owner_source_changed";
}

bool Read(PersonalGoldMailboxContextV1 &q,
    const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  q.observation={};q.foundation={};q.resource_leaf={};q.application_main_observed=false;
#if defined(XAR_CK3_ENABLE_1210_RESOURCE_OWNER_SOURCES_V3)
  q.additional_sources={};
#endif
  if(q.kind==ActorObservationKindV1::opening_readonly56) {
#if defined(XAR_CK3_ENABLE_26757580_OPENING_READONLY56)
    return ExecuteOpeningOnActorOwner56(q,s);
#else
    return true;
#endif
  }
  if(q.kind==ActorObservationKindV1::character_roster) {
#if defined(XAR_CK3_ENABLE_1210_CHARACTER_ROSTER_V1)
    return ExecuteCharacterRosterOnActorOwnerV1(q,s);
#else
    return true;
#endif
  }
  if(q.kind==ActorObservationKindV1::active_wars) {
#if defined(XAR_CK3_ENABLE_1210_ACTIVE_WARS_IDENTITY_V1)
    return ExecuteActiveWarsOnActorOwnerV1(q,s);
#else
    return true;
#endif
  }
  if(q.kind==ActorObservationKindV1::personal_cash) {
#if defined(XAR_CK3_ENABLE_1210_PERSONAL_CASH_V1)
    return ExecutePersonalCashOnActorOwnerV1(q,s);
#else
    return true; // Default-off build never enters personal CASH native calls.
#endif
  }
  const auto required_capability=q.kind==ActorObservationKindV1::resource_leaf ? kActorResourceLeafCapabilityV2 :
      q.kind==ActorObservationKindV1::foundation ? kActorFoundationCapabilityV1 : kPersonalGoldCapabilityV1;
  if (q.game==nullptr || !q.game->enabled() ||
      !game::IsCk3_1210Descriptor(q.game->descriptor()) ||
      !q.game->supports(required_capability) || q.mailbox==nullptr ||
      !q.bindings.exact_build_admitted || q.ticket.sequence==0) return true;
#if defined(XAR_CK3_ENABLE_1210_ACTOR_RESOURCE_LEAF_V2)
  // Resource-only preflight precedes the SHARED old slot dereferences and
  // ReadCoreSnapshot, so a wrong getter cannot execute before source admission.
  if(q.kind==ActorObservationKindV1::resource_leaf && !ResourceTargetsCurrentV2(q,s)) {
    q.resource_leaf.unavailable_reason="resource_targets_before_unavailable";return true;
  }
#endif
  const auto &m=*q.mailbox;const auto &b=q.bindings.core;
  const bool guarded_actor=q.kind==ActorObservationKindV1::personal_gold ||
      q.kind==ActorObservationKindV1::foundation;
  if(guarded_actor && !GoldFoundationOwnerV1(q,s))return true;
  if (s.thread_id==0 || s.thread_id!=GetCurrentThreadId() || s.pump_epoch==0 ||
      s.tls_initialized!=1 || s.tls_main_thread_marker!=1 || s.tls_context==0 ||
      !s.paused || s.game_state==0 || s.jomini_state==0 ||
      !m.iat_hook_installed.load() || m.owner_thread_id.load()!=s.thread_id || m.failure_flags.load()!=0 || m.stop_requested.load() ||
      m.paused_owner_verified_pump_epochs.load()<ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
      m.state.load()!=ck3_11906::MainThreadQueryMailboxStateV1::executing ||
      m.published_sequence.load()!=q.ticket.sequence || m.executor_context!=&q ||
      m.executor.load()!=&ExecutePersonalGoldMailboxV1 ||
      b.game_state_slot==nullptr || b.jomini_state_slot==nullptr ||
      reinterpret_cast<std::uintptr_t>(*b.game_state_slot)!=s.game_state ||
      reinterpret_cast<std::uintptr_t>(*b.jomini_state_slot)!=s.jomini_state) return true;
  q.application_main_observed=true;
  CoreSnapshotPrefix prefix{};
  if (!ReadCoreSnapshot(b,prefix)) { q.observation.unavailable_reason="core_read_failed";q.foundation.unavailable_reason="core_read_failed";q.resource_leaf.unavailable_reason="core_read_failed";return true; }
  if (prefix.clock.date_raw!=s.date_raw || prefix.clock.paused!=s.paused) {
    q.observation.unavailable_reason="core_frame_changed";q.foundation.unavailable_reason="core_frame_changed";q.resource_leaf.unavailable_reason="core_frame_changed";return true;
  }
  if(q.kind==ActorObservationKindV1::resource_leaf) {
#if defined(XAR_CK3_ENABLE_1210_ACTOR_RESOURCE_LEAF_V2)
    ResourceScopeContextV2 owner{&q,&s};
    const Scoped1210ImageSourceV1 scope{q.image_base,&q.game->descriptor(),q.bindings.core};
    const Scoped1210SourceAccessV1 access{&owner,&ResourceScopeCopyV2,&ResourceScopeValidateV2};
    Scoped1210ImageRootsV1 roots_before{},roots_after{};
    if(!ResolveScoped1210ImageRootsV1(scope,prefix,access,roots_before)) {
      q.resource_leaf.unavailable_reason="resource_owner_before_unavailable";return true;
    }
    const auto &descriptor=q.game->descriptor();ActorResourceLeafSourceInputV2 input{};
    input.image_base=q.image_base;input.game_version=descriptor.game_version;
    input.executable_sha256=descriptor.executable_sha256;input.adapter_id=descriptor.adapter_id;
    input.application_main_owner_admitted=true;input.gold_bindings=q.bindings;input.expected=prefix;
    const bool source_read=ReadActorResourceLeafV2(input,q.resource_leaf);
#if defined(XAR_CK3_ENABLE_1210_RESOURCE_OWNER_SOURCES_V3)
    if(source_read) {
      (void)ReadNonCashOwnerSourcesV3(input,q.additional_sources);
      if(!q.additional_sources.owner_source_interval_verified) {
        q.resource_leaf={};q.resource_leaf.unavailable_reason="additional_owner_source_interval_unavailable";
      }
    }
#else
    (void)source_read;
#endif
    if(!ResolveScoped1210ImageRootsV1(scope,prefix,access,roots_after) || roots_before!=roots_after) {
      q.resource_leaf={};q.resource_leaf.unavailable_reason="resource_owner_interval_changed";
#if defined(XAR_CK3_ENABLE_1210_RESOURCE_OWNER_SOURCES_V3)
      q.additional_sources={};q.additional_sources.unavailable_reason="resource_owner_interval_changed";
#endif
    }
#else
    q.resource_leaf.unavailable_reason="actor_resource_leaf_build_disabled";
#endif
    return true;
  }
  if(guarded_actor && !GoldFoundationOwnerV1(q,s)) {GoldFoundationOwnerChangedV1(q);return true;}
  if(q.kind==ActorObservationKindV1::foundation)
    (void)ReadActorFoundationV1({q.bindings.exact_build_admitted,q.bindings.core},prefix,q.foundation);
  else (void)ReadPersonalGoldV1(q.bindings,prefix,q.observation);
  if(guarded_actor && !GoldFoundationOwnerV1(q,s))GoldFoundationOwnerChangedV1(q);
  return true;
}
void Quoted(std::string &s,std::string_view value) {
  constexpr char hex[]="0123456789abcdef";s+=static_cast<char>(34);
  for (const unsigned char c:value) {
    if(c==34 || c==92) { s+=static_cast<char>(92);s+=static_cast<char>(c); }
    else if(c<32) { s+=static_cast<char>(92);s+="u00";s+=hex[c>>4];s+=hex[c&15]; }
    else s+=static_cast<char>(c);
  }
  s+=static_cast<char>(34);

}
}
// Keep STL destruction outside the thin SEH boundary.
static void MarkActorReadFailure(PersonalGoldMailboxContextV1 &q) noexcept {
  q.observation={};q.foundation={};q.resource_leaf={};q.observation.unavailable_reason="memory_read_failed";
  q.resource_leaf.unavailable_reason="memory_read_failed";
#if defined(XAR_CK3_ENABLE_1210_RESOURCE_OWNER_SOURCES_V3)
  q.additional_sources={};q.additional_sources.unavailable_reason="memory_read_failed";
#endif
  q.foundation.unavailable_reason="memory_read_failed";
}
bool ExecutePersonalGoldMailboxV1(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  if(opaque==nullptr) return false;
  auto &q=*static_cast<PersonalGoldMailboxContextV1 *>(opaque);
#if defined(_MSC_VER)
  __try { return Read(q,stamp); }
  __except(EXCEPTION_EXECUTE_HANDLER) {
    MarkActorReadFailure(q);return true;
  }
#else
  return Read(q,stamp);
#endif
}
std::string SerializePersonalGoldCommandResultV1(std::string_view id,
    const PersonalGoldMailboxContextV1 &q) {
  const auto &o=q.observation;
  const bool available=o.available && o.same_frame_ready && o.personal_gold_raw.has_value();
  CoreFrameObservationV1 core{};core.application_main_observed=q.application_main_observed;
  core.core_available=available;core.core=o.frame;core.unavailable_reason=o.unavailable_reason;
  std::string out=R"({"type":"command_result","protocol_version":1,"request_id":)";
  Quoted(out,id);out+=R"(,"ok":true,"result":{"step":)";Quoted(out,kPersonalGoldStepV1);
  out+=R"(,"schema":)";Quoted(out,kPersonalGoldSchemaV1);
  out+=R"(,"game_version":)";Quoted(out,kGameVersion);
  out+=R"(,"executable_sha256":)";Quoted(out,kExecutableSha256);
  out+=R"(,"adapter_id":)";Quoted(out,kAdapterId);
  out+=R"(,"backend":"ck3-1.21.0-native-headless-main-thread","status":)";
  Quoted(out,available?"partial":"unavailable");
  out+=R"(,"personal_gold_available":)";out+=available?"true":"false";
  out+=R"(,"application_main_observed":)";out+=q.application_main_observed?"true":"false";
  out+=R"(,"complete_snapshot":false,"treasury_observed":false,"monthly_flow_observed":false,"core_frame":)";
  out+=SerializeCoreFrameV1(core);out+=R"(,"personal_gold":)";
  if(available) out+=R"({"raw":)"+std::to_string(*o.personal_gold_raw)+R"(,"scale":100000})";
  else out+="null";
  out+=R"(,"unavailable_reason":)";
  if(available) out+="null";else Quoted(out,o.unavailable_reason);
  out+="}}";return out;
}
std::string SerializeActorFoundationCommandResultV1(std::string_view id,
    const PersonalGoldMailboxContextV1 &q) {
  const auto &o=q.foundation;
  const bool resources=o.resources_ready && o.gold_raw && o.prestige_raw && o.piety_raw && o.stress_points;
  const bool relations=o.relationships_ready && o.relationships.has_value();
  const bool available=o.same_frame_ready && (resources||relations);
  CoreFrameObservationV1 core{};core.application_main_observed=q.application_main_observed;
  core.core_available=o.same_frame_ready;core.core=o.frame;core.unavailable_reason=o.unavailable_reason;
  std::string out=R"({"type":"command_result","protocol_version":1,"request_id":)";
  Quoted(out,id);out+=R"(,"ok":true,"result":{"step":)";Quoted(out,kActorFoundationStepV1);
  out+=R"(,"schema":)";Quoted(out,kActorFoundationFrameSchemaV1);
  out+=R"(,"game_version":)";Quoted(out,kGameVersion);
  out+=R"(,"executable_sha256":)";Quoted(out,kExecutableSha256);
  out+=R"(,"adapter_id":)";Quoted(out,kAdapterId);
  out+=R"(,"backend":"ck3-1.21.0-native-headless-main-thread","status":)";Quoted(out,available?"partial":"unavailable");
  out+=R"(,"foundation_available":)";out+=available?"true":"false";
  out+=R"(,"resources_available":)";out+=resources?"true":"false";
  out+=R"(,"relationships_available":)";out+=relations?"true":"false";
  out+=R"(,"application_main_observed":)";out+=q.application_main_observed?"true":"false";
  out+=R"(,"complete_snapshot":false,"treasury_observed":false,"monthly_flow_observed":false,"core_frame":)";
  out+=SerializeCoreFrameV1(core);out+=R"(,"resources":)";
  if(resources) {
    const auto amount=[](std::int64_t raw) { return R"({"raw":)"+std::to_string(raw)+R"(,"scale":100000})"; };
    out+=R"({"gold":)"+amount(*o.gold_raw)+R"(,"prestige":)"+amount(*o.prestige_raw)+
        R"(,"piety":)"+amount(*o.piety_raw)+R"(,"stress_points":)"+std::to_string(*o.stress_points)+"}";
  } else out+="null";
  out+=R"(,"relationships":)";
  if(relations) {
    const auto &f=*o.relationships;
    out+=R"({"betrothed_character_id":)"+std::to_string(f.betrothed_character_id)+
        R"(,"primary_spouse_character_id":)"+std::to_string(f.primary_spouse_character_id)+R"(,"spouse_character_ids":[)";
    bool first=true;for(const auto peer:f.spouse_character_ids) { if(!first)out+=',';first=false;out+=std::to_string(peer); }
    out+="]}";
  } else out+="null";
  out+=R"(,"resources_unavailable_reason":)";if(resources)out+="null";else Quoted(out,o.resources_unavailable_reason);
  out+=R"(,"relationships_unavailable_reason":)";if(relations)out+="null";else Quoted(out,o.relationships_unavailable_reason);
  out+=R"(,"unavailable_reason":)";if(available)out+="null";else Quoted(out,o.unavailable_reason);
  out+="}}";return out;
}

}
