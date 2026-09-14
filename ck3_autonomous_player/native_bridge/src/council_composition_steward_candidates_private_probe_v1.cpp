#include "xar_bridge/council_composition_steward_candidates_private_probe_v1.hpp"

#include <algorithm>
#include <charconv>
#include <cstring>

namespace xar::bridge {
namespace {

using Failure = xar::game::CouncilCompositionStewardCandidatesFailureV1;
using Status = xar::game::CouncilCompositionStewardCandidatesStatusV1;
using Result = xar::game::CouncilCompositionStewardCandidatesV1;
using Access = xar::ck3_11906::CouncilCompositionStewardCandidatesAccessV1;

template <std::size_t Size>
std::string_view FixedString(const std::array<char, Size> &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  if (end == value.end())
    return {};
  return {value.data(), static_cast<std::size_t>(end - value.begin())};
}

void SetUnavailable(Result &result, Failure reason) noexcept {
  result = {};
  result.status = Status::unavailable;
  result.unavailable_reason = reason;
}

bool AccessComplete(const Access &access) noexcept {
  return access.context != nullptr && access.capture_frame != nullptr &&
         access.is_main_thread != nullptr && access.produce != nullptr &&
         access.release != nullptr && access.is_readable_span != nullptr &&
         access.read_candidate_pointer != nullptr &&
         access.read_candidate_id != nullptr &&
         access.resolve_candidate != nullptr;
}

bool IsExecutingExactMailboxSlot(
    const CouncilCompositionStewardCandidatesPrivateProbeV1 &probe,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  if (!probe.installed || !probe.request_prepared || probe.mailbox == nullptr ||
      probe.ticket.sequence == 0 || stamp.pump_epoch == 0 ||
      stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      stamp.jomini_state == 0 || stamp.game_state == 0 ||
      GetCurrentThreadId() != stamp.thread_id) {
    return false;
  }
  const auto &mailbox = *probe.mailbox;
  return mailbox.state.load(std::memory_order_acquire) ==
             xar::ck3_11906::MainThreadQueryMailboxStateV1::executing &&
         !mailbox.stop_requested.load(std::memory_order_acquire) &&
         mailbox.failure_flags.load(std::memory_order_acquire) == 0 &&
         mailbox.published_sequence.load(std::memory_order_acquire) ==
             probe.ticket.sequence &&
         mailbox.owner_thread_id.load(std::memory_order_acquire) ==
             stamp.thread_id &&
         mailbox.paused_owner_verified_pump_epochs.load(
             std::memory_order_acquire) >=
             xar::ck3_11906::
                 kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs &&
         mailbox.executor ==
             &ExecuteCouncilCompositionStewardCandidatesPrivateProbeV1 &&
         mailbox.executor_context ==
             const_cast<CouncilCompositionStewardCandidatesPrivateProbeV1 *>(
                 &probe);
}

bool ProbeIsMainThread(void *opaque) noexcept {
  const auto *probe =
      static_cast<const CouncilCompositionStewardCandidatesPrivateProbeV1 *>(
          opaque);
  return probe != nullptr && probe->active_stamp != nullptr &&
         IsExecutingExactMailboxSlot(*probe, *probe->active_stamp);
}

bool ProbeCaptureFrame(
    void *opaque, xar::ck3_11906::CouncilCompositionStewardCandidatesFrameV1
                      &output) noexcept {
  auto *probe =
      static_cast<CouncilCompositionStewardCandidatesPrivateProbeV1 *>(opaque);
  if (probe == nullptr || probe->active_stamp == nullptr ||
      probe->binding_state == nullptr ||
      !IsExecutingExactMailboxSlot(*probe, *probe->active_stamp)) {
    return false;
  }
  xar::game::Snapshot snapshot{};
  if (!xar::ck3_11906::ReadSnapshot(probe->bindings, snapshot) ||
      snapshot != probe->expected_snapshot || !snapshot.paused ||
      snapshot.date_raw != probe->active_stamp->date_raw ||
      snapshot.played_character_id <= 0) {
    return false;
  }
  auto &binding = *probe->binding_state;
  std::uintptr_t played_character = 0;
  if (!binding.attached || binding.operations.resolve_character == nullptr ||
      !binding.operations.resolve_character(
          binding.operation_context, binding.module_base,
          snapshot.played_character_id, played_character) ||
      played_character == 0) {
    return false;
  }

  output = {};
  output.snapshot_id = probe->expected_snapshot_id;
  output.public_revision = probe->request.expected_public_revision;
  output.native_revision = probe->request.expected_native_revision;
  output.date_raw = snapshot.date_raw;
  output.paused = snapshot.paused;
  output.map_ready = snapshot.map_ready;
  output.has_played_character = snapshot.has_played_character;
  output.played_character_alive = snapshot.played_character_alive;
  output.played_character_id = snapshot.played_character_id;
  output.played_character = played_character;
  output.played_character_identity_round_trip = true;
  return true;
}

bool TypedResult(const Result &result) noexcept {
  if (result.status == Status::available) {
    return result.unavailable_reason == Failure::none && result.paused &&
           result.owner_character_id > 0 &&
           result.candidate_collection_complete &&
           result.candidate_count <=
               xar::game::kCouncilCompositionStewardCandidatesMaximumRowsV1 &&
           result.temporary_vector_released &&
           result.readiness.identity_ready &&
           result.readiness.candidate_collection_ready;
  }
  return result.status == Status::unavailable &&
         result.unavailable_reason != Failure::none &&
         !result.readiness.identity_ready &&
         !result.readiness.candidate_collection_ready;
}

void AppendBool(std::string &output, bool value) {
  output += value ? "true" : "false";
}

std::string_view StatusName(Status status) noexcept {
  return status == Status::available ? "available" : "unavailable";
}

} // namespace

bool ConfigureCouncilCompositionStewardCandidatesPrivateProbeTransportV1(
    CouncilCompositionStewardCandidatesPrivateProbeV1 &probe,
    xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const xar::ck3_11906::Bindings &bindings,
    xar::ck3_11906::CouncilCompositionStewardCandidatesBindingStateV1
        &binding_state) noexcept {
  probe = {};
  probe.mailbox = &mailbox;
  probe.bindings = bindings;
  probe.binding_state = &binding_state;
  probe.transport_configured = true;
  SetUnavailable(probe.published_result, Failure::native_bindings_unavailable);
  return true;
}

Access CouncilCompositionStewardCandidatesProbeAccessV1(
    CouncilCompositionStewardCandidatesPrivateProbeV1 &probe) noexcept {
  Access access{};
  if (!probe.transport_configured)
    return access;
  access.context = &probe;
  access.capture_frame = &ProbeCaptureFrame;
  access.is_main_thread = &ProbeIsMainThread;
  return access;
}

bool InstallCouncilCompositionStewardCandidatesPrivateProbeV1(
    CouncilCompositionStewardCandidatesPrivateProbeV1 &probe,
    const xar::ck3_11906::CouncilCompositionStewardCandidatesEnvironmentV1
        &environment,
    const Access &access) noexcept {
  if (!probe.transport_configured || probe.mailbox == nullptr ||
      probe.binding_state == nullptr || !probe.binding_state->attached ||
      !environment.exact_build_admitted ||
      environment.admitted_executable_sha256 !=
          xar::ck3_11906::
              kCouncilCompositionStewardCandidatesReaderExecutableSha256V1 ||
      environment.module_base == 0 ||
      environment.producer_address !=
          environment.module_base +
              xar::ck3_11906::
                  kCouncilCompositionStewardCandidatesProducerRvaV1 ||
      !AccessComplete(access)) {
    return false;
  }
  probe.environment = environment;
  probe.access = access;
  probe.installed = true;
  return true;
}

bool PrepareCouncilCompositionStewardCandidatesPrivateProbeV1(
    CouncilCompositionStewardCandidatesPrivateProbeV1 &probe,
    const xar::game::Snapshot &snapshot, std::uint64_t public_revision,
    std::uint64_t native_revision) noexcept {
  if (!probe.installed || probe.request_prepared || probe.result_published ||
      public_revision == 0 || native_revision == 0 || !snapshot.paused ||
      !snapshot.map_ready || !snapshot.has_played_character ||
      !snapshot.played_character_alive || snapshot.played_character_id <= 0) {
    return false;
  }
  probe.expected_snapshot_id.fill('\0');
  constexpr std::string_view prefix = "native:";
  std::copy(prefix.begin(), prefix.end(), probe.expected_snapshot_id.begin());
  auto *begin = probe.expected_snapshot_id.data() + prefix.size();
  auto *end =
      probe.expected_snapshot_id.data() + probe.expected_snapshot_id.size() - 1;
  const auto encoded = std::to_chars(begin, end, native_revision);
  if (encoded.ec != std::errc{})
    return false;
  *encoded.ptr = '\0';

  probe.expected_snapshot = snapshot;
  probe.request = {};
  probe.request.expected_snapshot_id = FixedString(probe.expected_snapshot_id);
  probe.request.expected_public_revision = public_revision;
  probe.request.expected_native_revision = native_revision;
  probe.request.expected_date_raw = snapshot.date_raw;
  probe.request.expected_owner_character_id = snapshot.played_character_id;
  probe.execution_result = {};
  probe.execution_result_ready = false;
  probe.request_prepared = true;
  return true;
}

bool ExecuteCouncilCompositionStewardCandidatesPrivateProbeV1(
    void *context,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *probe =
      static_cast<CouncilCompositionStewardCandidatesPrivateProbeV1 *>(context);
  if (probe == nullptr || probe->execution_result_ready ||
      !IsExecutingExactMailboxSlot(*probe, stamp)) {
    return false;
  }
  if (!stamp.paused || stamp.date_raw != probe->request.expected_date_raw) {
    SetUnavailable(probe->execution_result,
                   !stamp.paused ? Failure::not_paused : Failure::date_drift);
    probe->execution_result_ready = true;
    return true;
  }
  probe->active_stamp = &stamp;
  (void)xar::ck3_11906::ReadCouncilCompositionStewardCandidatesV1(
      probe->environment, probe->access, probe->request,
      probe->execution_result);
  probe->active_stamp = nullptr;
  if (!TypedResult(probe->execution_result)) {
    SetUnavailable(probe->execution_result,
                   Failure::native_bindings_unavailable);
  }
  probe->execution_result_ready = true;
  return true;
}

bool PublishCouncilCompositionStewardCandidatesPrivateProbeV1(
    CouncilCompositionStewardCandidatesPrivateProbeV1 &probe) noexcept {
  if (!probe.installed || !probe.request_prepared ||
      !probe.execution_result_ready || probe.result_published) {
    return false;
  }
  probe.published_result = probe.execution_result;
  probe.result_published = true;
  ++probe.published_execution_count;
  return true;
}

bool PublishCouncilCompositionStewardCandidatesPrivateProbeFailureV1(
    CouncilCompositionStewardCandidatesPrivateProbeV1 &probe,
    Failure reason) noexcept {
  if (!probe.installed || !probe.request_prepared || probe.result_published ||
      reason == Failure::none) {
    return false;
  }
  SetUnavailable(probe.published_result, reason);
  probe.result_published = true;
  ++probe.published_execution_count;
  return true;
}

std::string SerializeCouncilCompositionStewardCandidatesPrivateProbeV1(
    const CouncilCompositionStewardCandidatesPrivateProbeV1 &probe) {
  const auto &result = probe.published_result;
  std::string output;
  output.reserve(2048);
  output += "{\"private_build\":true,\"read_only\":true,";
  output += "\"advertised\":false,\"private_key\":\"";
  output += kCouncilCompositionStewardCandidatesPrivateProbeKeyV1;
  output += "\",\"installed\":";
  AppendBool(output, probe.installed);
  output += ",\"request_prepared\":";
  AppendBool(output, probe.request_prepared);
  output += ",\"result_published\":";
  AppendBool(output, probe.result_published);
  output += ",\"published_execution_count\":" +
            std::to_string(probe.published_execution_count);
  output += ",\"result\":{\"schema\":\"xar.ck3.private.council_";
  output += "composition_steward_candidates/v1\",\"schema_version\":1,";
  output += "\"status\":\"";
  output += StatusName(result.status);
  output += "\",\"unavailable_reason\":\"";
  output += xar::ck3_11906::CouncilCompositionStewardCandidatesFailureKeyV1(
      result.unavailable_reason);
  output += "\",\"exact_build\":{\"game_version\":\"1.19.0.6\",";
  output += "\"executable_sha256\":\"";
  output += xar::ck3_11906::
      kCouncilCompositionStewardCandidatesReaderExecutableSha256V1;
  output += "\"},\"snapshot\":{\"snapshot_id\":\"";
  output += FixedString(result.snapshot_id);
  output += "\",\"public_revision\":" + std::to_string(result.public_revision);
  output += ",\"native_revision\":" + std::to_string(result.native_revision);
  output += ",\"date_raw\":" + std::to_string(result.date_raw);
  output += ",\"paused\":";
  AppendBool(output, result.paused);
  output +=
      "},\"owner_character_id\":" + std::to_string(result.owner_character_id);
  output += ",\"position_key\":\"";
  output += FixedString(result.position_key);
  output += "\",\"candidate_collection_complete\":";
  AppendBool(output, result.candidate_collection_complete);
  output += ",\"candidate_count\":" + std::to_string(result.candidate_count);
  output += ",\"candidates\":[";
  for (std::uint32_t index = 0; index < result.candidate_count; ++index) {
    if (index != 0)
      output += ',';
    output += "{\"character_id\":" +
              std::to_string(result.candidates[index].character_id);
    output +=
        ",\"native_collection_ordinal\":" +
        std::to_string(result.candidates[index].native_collection_ordinal) +
        '}';
  }
  output += "],\"temporary_vector_released\":";
  AppendBool(output, result.temporary_vector_released);
  output += ",\"readiness\":{\"identity_ready\":";
  AppendBool(output, result.readiness.identity_ready);
  output += ",\"candidate_collection_ready\":";
  AppendBool(output, result.readiness.candidate_collection_ready);
  output += "},\"raw_pointer_fields_persisted\":false}}";
  return output;
}

} // namespace xar::bridge
