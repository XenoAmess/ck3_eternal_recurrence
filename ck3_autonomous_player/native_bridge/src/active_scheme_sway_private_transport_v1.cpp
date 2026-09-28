#include "active_scheme_sway_private_transport_v1.hpp"

#include <windows.h>

#include <atomic>
#include <charconv>
#include <cstring>
#include <limits>

namespace xar::ck3_11906 {
namespace {

using namespace xar::bridge;

struct ReadContext {
  ActiveSchemeSwayPrivateQueryV1 *query = nullptr;
  const MainThreadExecutionStampV1 *stamp = nullptr;
};

bool CaptureFrame(void *opaque,
                  ActiveSchemeStateV1PrivateSourceFrame &frame) noexcept {
  const auto *context = static_cast<ReadContext *>(opaque);
  if (context == nullptr || context->query == nullptr ||
      context->stamp == nullptr) return false;
  game::Snapshot current{};
  if (!ReadSnapshot(context->query->bindings, current) ||
      current != context->query->expected_snapshot || !current.paused ||
      !current.map_ready || !current.has_played_character ||
      !current.played_character_alive ||
      current.date_raw != context->stamp->date_raw) {
    context->query->frame_changed = true;
    return false;
  }
  frame = {context->stamp->pump_epoch, current.date_raw,
           current.played_character_id, true};
  return true;
}

bool MatchesSway(const ActiveSchemeStateV1PrivateRow &row,
                 std::int64_t actor, std::uint32_t target) noexcept {
  return row.owner_character_id == actor &&
         std::strncmp(row.scheme_type_key.data(), "sway", 5) == 0 &&
         row.target_kind == ActiveSchemeStateV1PrivateTargetKind::character &&
         row.target_id == target;
}

} // namespace

bool ParseActiveSchemeSwayPrivateQueryStepV1(std::string_view step,
                                             std::uint32_t &target_id) noexcept {
  target_id = 0;
  if (!step.starts_with(kActiveSchemeSwayPrivateQueryPrefixV1)) return false;
  const auto suffix = step.substr(kActiveSchemeSwayPrivateQueryPrefixV1.size());
  if (suffix.empty() || suffix.front() == '0') return false;
  const auto [end, error] = std::from_chars(
      suffix.data(), suffix.data() + suffix.size(), target_id);
  return error == std::errc{} && end == suffix.data() + suffix.size() &&
         target_id != 0;
}

bool ExecuteActiveSchemeSwayPrivateQueryV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<ActiveSchemeSwayPrivateQueryV1 *>(opaque);
  if (query == nullptr || query->mailbox == nullptr ||
      query->ticket.sequence == 0 || query->expected_revision == 0 ||
      query->target_character_id == 0 || query->invocations != 0 ||
      stamp.pump_epoch == 0 || stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      stamp.jomini_state == 0 || stamp.game_state == 0 ||
      GetCurrentThreadId() != stamp.thread_id) return false;
  auto &mailbox = *query->mailbox;
  if (mailbox.state.load(std::memory_order_acquire) !=
          MainThreadQueryMailboxStateV1::executing ||
      mailbox.stop_requested.load(std::memory_order_acquire) ||
      mailbox.failure_flags.load(std::memory_order_acquire) != 0 ||
      mailbox.published_sequence.load(std::memory_order_acquire) !=
          query->ticket.sequence ||
      mailbox.owner_thread_id.load(std::memory_order_acquire) !=
          stamp.thread_id ||
      mailbox.paused_owner_verified_pump_epochs.load(
          std::memory_order_acquire) <
          kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
      mailbox.executor != &ExecuteActiveSchemeSwayPrivateQueryV1 ||
      mailbox.executor_context != query) return false;
  try {
    ++query->invocations;
    game::Snapshot current{};
    if (!ReadSnapshot(query->bindings, current) ||
        current != query->expected_snapshot || !current.paused ||
        !current.map_ready || !current.has_played_character ||
        !current.played_character_alive || current.date_raw != stamp.date_raw) {
      query->frame_changed = true;
      query->failure = "published_frame_changed";
      query->completed = true;
      return true;
    }
    ReadContext read_context{query, &stamp};
    ActiveSchemeStateV1PrivateSourceAccess access{};
    access.context = &read_context;
    access.capture_frame = &CaptureFrame;
    access.current_thread_id = GetCurrentThreadId();
    access.application_main_thread_id = stamp.thread_id;
    const auto module_base =
        reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    ActiveSchemeStateV1PrivateNativeEnvironment source_environment{};
    source_environment.binding_enabled = true;
    source_environment.exact_build_admitted = query->bindings.enabled;
    source_environment.admitted_executable_sha256 =
        kActiveSchemeStateV1PrivateObserverExecutableSha256;
    source_environment.admitted_game_version =
        kActiveSchemeStateV1PrivateNativeBinderGameVersion;
    source_environment.module_base = module_base;
    ActiveSchemeStateV1PrivateNativeBindingState source_state{};
    if (!BindActiveSchemeStateV1PrivateNative(
            source_environment, source_state, access)) {
      query->failure = "native_scheme_source_bind_red";
      query->completed = true;
      return true;
    }
    ActiveSchemePreconditionCommandBindersV1PrivateEnvironment environment{};
    environment.binding_enabled = true;
    environment.exact_build_admitted = query->bindings.enabled;
    environment.admitted_executable_sha256 =
        kActiveSchemeStateV1PrivateObserverExecutableSha256;
    environment.admitted_game_version =
        kActiveSchemeStateV1PrivateNativeBinderGameVersion;
    environment.module_base = module_base;
    environment.source_access = access;
    ActiveSchemePreconditionCommandBindersV1PrivateState binder{};
    ActiveSchemePreconditionCommandBindersV1PrivateReadiness readiness{};
    if (!BindActiveSchemePreconditionCommandBindersV1Private(
            environment, binder, readiness)) {
      query->failure = "native_scheme_precondition_bind_red";
      query->completed = true;
      return true;
    }
    const ActiveSchemePausedLiveNativeGlueV1PrivateExecution execution{
        GetCurrentThreadId(), stamp.thread_id};
    ActiveSchemePreconditionCommandBindersV1PrivateFailure failure{};
    if (!CaptureActiveSchemePreconditionCommandSnapshotV1Private(
            binder, execution, query->active, failure)) {
      query->failure = "native_scheme_observation_red";
      query->completed = true;
      return true;
    }
    for (std::size_t i = 0; i < query->active.row_count; ++i) {
      if (MatchesSway(query->active.rows[i], current.played_character_id,
                      query->target_character_id)) {
        query->matching_active_scheme = true;
        break;
      }
    }
    ActiveSchemeSemanticActionV1PrivateRequest request{};
    request.request_id = "private-sway-readonly";
    request.interaction_key = "sway_interaction";
    request.actor_character_id = current.played_character_id;
    request.target_kind = ActiveSchemeStateV1PrivateTargetKind::character;
    request.target_id = query->target_character_id;
    request.expected_capture_epoch = query->active.capture_epoch;
    request.expected_container_generation = query->active.container_generation;
    request.expected_date_raw = query->active.date_raw;
    if (!CaptureActiveSchemePreconditionCommandPreconditionV1Private(
            binder, execution, request, query->precondition, failure)) {
      query->failure = "native_sway_precondition_red";
      query->completed = true;
      return true;
    }
    query->completed = true;
    return true;
  } catch (...) {
    return false;
  }
}

std::string SerializeActiveSchemeSwayPrivateQueryV1(
    const ActiveSchemeSwayPrivateQueryV1 &query) {
  if (!query.completed || !query.failure.empty() ||
      query.active.status != ActiveSchemeStateV1PrivateStatus::available ||
      !query.precondition.available ||
      query.precondition.capture_epoch != query.active.capture_epoch ||
      query.precondition.date_raw != query.active.date_raw ||
      query.precondition.actor_character_id !=
          query.active.played_character_id ||
      query.precondition.target_id != query.target_character_id ||
      query.precondition.interaction_key != "sway_interaction" ||
      query.precondition.scheme_type_key != "sway") return {};
  std::string result = "{\"schema\":\"active-scheme-sway-private-read-v1\","
                       "\"snapshot_revision\":" +
                       std::to_string(query.expected_revision);
  result += ",\"capture_epoch\":" +
            std::to_string(query.active.capture_epoch);
  result += ",\"container_generation\":" +
            std::to_string(query.active.container_generation);
  result += ",\"date_raw\":" + std::to_string(query.active.date_raw);
  result += ",\"actor_character_id\":" +
            std::to_string(query.active.played_character_id);
  result += ",\"target_character_id\":" +
            std::to_string(query.target_character_id);
  result += ",\"active_scheme_count\":" +
            std::to_string(query.active.row_count);
  result += ",\"matching_sway_active\":";
  result += query.matching_active_scheme ? "true" : "false";
  result += ",\"native_complete_can_send\":";
  result += query.precondition.can_start_scheme ? "true" : "false";
  result += ",\"native_legal_now\":";
  result += (!query.matching_active_scheme &&
             query.precondition.shown_evaluated &&
             query.precondition.validity_evaluated &&
             query.precondition.can_start_scheme_evaluated &&
             query.precondition.shown && query.precondition.valid &&
             query.precondition.can_start_scheme) ? "true" : "false";
  result += ",\"native_failure_classification\":\"";
  result += query.precondition.native_reason_key;
  result += "\"}";
  return result;
}

} // namespace xar::ck3_11906
