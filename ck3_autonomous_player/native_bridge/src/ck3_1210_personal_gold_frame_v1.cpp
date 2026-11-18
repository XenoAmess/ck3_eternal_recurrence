#include "xar_bridge/ck3_1210_personal_gold_frame_v1.hpp"
#include "xar_bridge/ck3_1210_adapter.hpp"
#if defined(XAR_CK3_ENABLE_1210_PERSONAL_CASH_V1)
#include "xar_bridge/ck3_1210_personal_cash_frame_v1.hpp"
#endif
#include <windows.h>
namespace xar::ck3_1210 {
namespace {
bool Read(PersonalGoldMailboxContextV1 &q,
    const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  q.observation={};q.foundation={};q.application_main_observed=false;
  if(q.kind==ActorObservationKindV1::personal_cash) {
#if defined(XAR_CK3_ENABLE_1210_PERSONAL_CASH_V1)
    return ExecutePersonalCashOnActorOwnerV1(q,s);
#else
    return true; // Default-off build never enters personal CASH native calls.
#endif
  }
  if (q.game==nullptr || !q.game->enabled() ||
      !game::IsCk3_1210Descriptor(q.game->descriptor()) ||
      !q.game->supports(q.kind==ActorObservationKindV1::foundation ? kActorFoundationCapabilityV1 : kPersonalGoldCapabilityV1) || q.mailbox==nullptr ||
      !q.bindings.exact_build_admitted || q.ticket.sequence==0) return true;
  const auto &m=*q.mailbox;const auto &b=q.bindings.core;
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
  if (!ReadCoreSnapshot(b,prefix)) { q.observation.unavailable_reason="core_read_failed";q.foundation.unavailable_reason="core_read_failed";return true; }
  if (prefix.clock.date_raw!=s.date_raw || prefix.clock.paused!=s.paused) {
    q.observation.unavailable_reason="core_frame_changed";q.foundation.unavailable_reason="core_frame_changed";return true;
  }
  if(q.kind==ActorObservationKindV1::foundation)
    (void)ReadActorFoundationV1({q.bindings.exact_build_admitted,q.bindings.core},prefix,q.foundation);
  else (void)ReadPersonalGoldV1(q.bindings,prefix,q.observation);
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
  q.observation={};q.foundation={};q.observation.unavailable_reason="memory_read_failed";
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
