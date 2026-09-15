#include "player_construction_view_probe_v1_mailbox.hpp"

#include "player_construction_view_probe_v1_process.hpp"

#include <windows.h>

#include <atomic>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

using ProbeFailure =
    xar::ck3::shared::PlayerConstructionViewProbeFailureV1;
using ProbeResult = xar::ck3::shared::PlayerConstructionViewProbeResultV1;
using ProbeStatus = xar::ck3::shared::PlayerConstructionViewProbeStatusV1;

bool IsExecutingExactSlot(
    const PlayerConstructionViewProbeMailboxContextV1& query,
    const MainThreadExecutionStampV1& stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0U ||
      query.module_base == 0U || stamp.pump_epoch == 0U ||
      stamp.thread_id == 0U || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0U ||
      stamp.tls_initialized != 1 || stamp.tls_context == 0U ||
      stamp.tls_main_thread_marker != 1 || stamp.jomini_state == 0U ||
      stamp.game_state == 0U || GetCurrentThreadId() != stamp.thread_id) {
    return false;
  }
  const auto& mailbox = *query.mailbox;
  return mailbox.state.load(std::memory_order_acquire) ==
             MainThreadQueryMailboxStateV1::executing &&
         !mailbox.stop_requested.load(std::memory_order_acquire) &&
         mailbox.failure_flags.load(std::memory_order_acquire) == 0U &&
         mailbox.published_sequence.load(std::memory_order_acquire) ==
             query.ticket.sequence &&
         mailbox.owner_thread_id.load(std::memory_order_acquire) ==
             stamp.thread_id &&
         mailbox.paused_owner_verified_pump_epochs.load(
             std::memory_order_acquire) >=
             kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs &&
         mailbox.executor == &ExecutePlayerConstructionViewProbeMailboxV1 &&
         mailbox.executor_context == &query;
}

bool CaptureSameSnapshot(
    const PlayerConstructionViewProbeMailboxContextV1& query,
    const MainThreadExecutionStampV1& stamp) noexcept {
  game::Snapshot current{};
  return ReadSnapshot(query.bindings, current) &&
         current == query.expected_snapshot && current.map_ready &&
         current.paused && current.has_played_character &&
         current.played_character_alive &&
         current.date_raw == stamp.date_raw;
}

ProbeResult FrameChanged() noexcept {
  ProbeResult result{};
  result.failure = ProbeFailure::frame_changed;
  return result;
}

std::string_view StatusKey(ProbeStatus status) noexcept {
  switch (status) {
    case ProbeStatus::view_candidate_cache_empty:
      return "view_candidate_cache_empty";
    case ProbeStatus::view_candidate_cache_present:
      return "view_candidate_cache_present";
    case ProbeStatus::unavailable:
      return "unavailable";
  }
  return "unavailable";
}

std::string_view FailureKey(ProbeFailure failure) noexcept {
  switch (failure) {
    case ProbeFailure::none: return "none";
    case ProbeFailure::exact_build: return "exact_build";
    case ProbeFailure::application_main: return "application_main";
    case ProbeFailure::session: return "session";
    case ProbeFailure::owner_path: return "owner_path";
    case ProbeFailure::view_missing: return "view_missing";
    case ProbeFailure::view_identity: return "view_identity";
    case ProbeFailure::candidate_span: return "candidate_span";
    case ProbeFailure::source_read: return "source_read";
    case ProbeFailure::frame_changed: return "frame_changed";
  }
  return "source_read";
}

}  // namespace

bool ExecutePlayerConstructionViewProbeMailboxV1(
    void* context, const MainThreadExecutionStampV1& stamp) noexcept {
  auto* query =
      static_cast<PlayerConstructionViewProbeMailboxContextV1*>(context);
  if (query == nullptr || !IsExecutingExactSlot(*query, stamp) ||
      query->completion !=
          PlayerConstructionViewProbeMailboxCompletionV1::not_executed ||
      query->executor_invocations != 0U) {
    if (query != nullptr) {
      query->completion =
          PlayerConstructionViewProbeMailboxCompletionV1::
              infrastructure_rejected;
    }
    return false;
  }
  ++query->executor_invocations;
  query->execution_stamp = stamp;
  if (!CaptureSameSnapshot(*query, stamp)) {
    query->result = FrameChanged();
    query->completion =
        PlayerConstructionViewProbeMailboxCompletionV1::completed;
    return true;
  }

  xar::ck3::shared::PlayerConstructionViewProcessAccessV1 process{};
  process.module_base = query->module_base;
  const auto source = xar::ck3::shared::
      BindCurrentProcessPlayerConstructionViewProbeSourceV1(process);
  xar::ck3::shared::PlayerConstructionViewProbeAdmissionV1 admission{};
  admission.exact_build_admitted = true;
  admission.application_main_thread = true;
  admission.session_live = true;
  admission.module_base = query->module_base;
  const auto first = xar::ck3::shared::ProbePlayerConstructionViewCacheV1(
      admission, source);
  const auto second = xar::ck3::shared::ProbePlayerConstructionViewCacheV1(
      admission, source);
  if (!CaptureSameSnapshot(*query, stamp) || first.status != second.status ||
      first.failure != second.failure ||
      first.view_present != second.view_present ||
      first.candidate_capacity != second.candidate_capacity ||
      first.cached_candidate_count != second.cached_candidate_count) {
    query->result = FrameChanged();
  } else {
    query->result = second;
  }
  query->completion =
      PlayerConstructionViewProbeMailboxCompletionV1::completed;
  return true;
}

std::string SerializePlayerConstructionViewProbePrivateV1(
    const PlayerConstructionViewProbeMailboxContextV1& query) {
  const auto& result = query.result;
  std::string json =
      "{\"schema_version\":1,\"private_key\":\"g2_player_construction_view_probe_v1\",\"advertised\":false,\"status\":\"";
  json += StatusKey(result.status);
  json += "\",\"failure\":\"";
  json += FailureKey(result.failure);
  json += "\",\"view_present\":";
  json += result.view_present ? "true" : "false";
  json += ",\"candidate_capacity\":";
  json += std::to_string(result.candidate_capacity);
  json += ",\"cached_candidate_count\":";
  json += std::to_string(result.cached_candidate_count);
  json += ",\"executor_invocations\":";
  json += std::to_string(query.executor_invocations);
  json += '}';
  return json;
}

}  // namespace xar::ck3_11906
