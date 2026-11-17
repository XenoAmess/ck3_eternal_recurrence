#include "xar_bridge/ck3_1210_personal_gold_frame_v1.hpp"
#include "xar_bridge/ck3_1210_adapter.hpp"
#include <windows.h>
namespace xar::ck3_1210 {
namespace {
bool Read(PersonalGoldMailboxContextV1 &q,
    const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  q.observation={};q.application_main_observed=false;
  if (q.game==nullptr || !q.game->enabled() ||
      !game::IsCk3_1210Descriptor(q.game->descriptor()) ||
      !q.game->supports(kPersonalGoldCapabilityV1) || q.mailbox==nullptr ||
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
  if (!ReadCoreSnapshot(b,prefix)) { q.observation.unavailable_reason="core_read_failed";return true; }
  if (prefix.clock.date_raw!=s.date_raw || prefix.clock.paused!=s.paused) {
    q.observation.unavailable_reason="core_frame_changed";return true;
  }
  (void)ReadPersonalGoldV1(q.bindings,prefix,q.observation);
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
bool ExecutePersonalGoldMailboxV1(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  if(opaque==nullptr) return false;
  auto &q=*static_cast<PersonalGoldMailboxContextV1 *>(opaque);
#if defined(_MSC_VER)
  __try { return Read(q,stamp); }
  __except(EXCEPTION_EXECUTE_HANDLER) {
    q.observation={};q.observation.unavailable_reason="memory_read_failed";return true;
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
}
