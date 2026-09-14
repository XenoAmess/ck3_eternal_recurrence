#include "xar_bridge/military_preparation_summary_v1_private_probe.hpp"

#include "xar_bridge/military_preparation_summary_v1_serializer.hpp"

namespace xar::bridge {
namespace {

bool CallbacksComplete(
    const MilitaryPreparationSummaryEnvironmentV1 &environment) noexcept {
  return environment.read_frame != nullptr &&
         environment.begin_session != nullptr &&
         environment.end_session != nullptr &&
         environment.resolve_definition != nullptr &&
         environment.definition_is_valid != nullptr &&
         environment.evaluate_fixed != nullptr;
}

void SetUnavailable(MilitaryPreparationSummaryResultV1 &result,
                    std::uint32_t failure) noexcept {
  result = {};
  result.status = MilitaryPreparationSummaryStatusV1::unavailable;
  result.failure_flags = failure;
}

} // namespace

bool InstallMilitaryPreparationSummaryPrivateProbeV1(
    MilitaryPreparationSummaryPrivateProbeV1 &probe,
    const MilitaryPreparationSummaryEnvironmentV1 &environment) noexcept {
  probe = {};
  probe.published_result.status =
      MilitaryPreparationSummaryStatusV1::disabled;
  probe.published_result.failure_flags =
      military_preparation_summary_failure_disabled;
  if (!environment.observer_enabled || !environment.exact_build_admitted ||
      environment.admitted_executable_sha256 !=
          kMilitaryPreparationSummaryExecutableSha256V1 ||
      !CallbacksComplete(environment)) {
    return false;
  }
  probe.environment = environment;
  probe.environment.current_thread_id = 0;
  probe.environment.application_main_thread_id = 0;
  probe.installed = true;
  return true;
}

bool PrepareMilitaryPreparationSummaryPrivateProbeV1(
    MilitaryPreparationSummaryPrivateProbeV1 &probe,
    const MilitaryPreparationFrameIdentityV1 &frame,
    std::uint64_t expected_revision) noexcept {
  if (!probe.installed || probe.request_prepared || probe.result_published ||
      expected_revision == 0 || frame.snapshot_revision != expected_revision ||
      frame.played_character_id <= 0 || !frame.paused) {
    return false;
  }
  probe.requested_frame = frame;
  probe.expected_revision = expected_revision;
  probe.execution_result = {};
  probe.execution_result_ready = false;
  probe.request_prepared = true;
  return true;
}

bool ReadMilitaryPreparationSummaryPrivateProbeFrameV1(
    void *context, MilitaryPreparationFrameIdentityV1 &output) noexcept {
  if (context == nullptr) return false;
  const auto &probe =
      *static_cast<MilitaryPreparationSummaryPrivateProbeV1 *>(context);
  if (!probe.installed || !probe.request_prepared) return false;
  output = probe.requested_frame;
  return true;
}

bool ExecuteMilitaryPreparationSummaryPrivateProbeV1(
    void *context,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  if (context == nullptr) return false;
  auto &probe =
      *static_cast<MilitaryPreparationSummaryPrivateProbeV1 *>(context);
  if (!probe.installed || !probe.request_prepared ||
      probe.execution_result_ready) {
    return false;
  }
  if (stamp.thread_id == 0 || !stamp.paused ||
      stamp.date_raw != probe.requested_frame.date_raw) {
    SetUnavailable(
        probe.execution_result,
        !stamp.paused ? military_preparation_summary_failure_not_paused
                      : military_preparation_summary_failure_frame_changed);
    probe.execution_result_ready = true;
    return true;
  }
  probe.environment.current_thread_id = stamp.thread_id;
  probe.environment.application_main_thread_id = stamp.thread_id;
  (void)ReadMilitaryPreparationSummaryV1(
      probe.environment, probe.expected_revision, probe.execution_result);
  probe.execution_result_ready = true;
  return true;
}

bool PublishMilitaryPreparationSummaryPrivateProbeV1(
    MilitaryPreparationSummaryPrivateProbeV1 &probe) noexcept {
  if (!probe.installed || !probe.request_prepared ||
      !probe.execution_result_ready || probe.result_published) {
    return false;
  }
  probe.published_result = probe.execution_result;
  probe.result_published = true;
  ++probe.published_execution_count;
  return true;
}

bool PublishMilitaryPreparationSummaryPrivateProbeFailureV1(
    MilitaryPreparationSummaryPrivateProbeV1 &probe,
    std::uint32_t failure_flags) noexcept {
  if (!probe.installed || !probe.request_prepared ||
      probe.result_published || failure_flags == 0) {
    return false;
  }
  SetUnavailable(probe.published_result, failure_flags);
  probe.result_published = true;
  ++probe.published_execution_count;
  return true;
}

std::string SerializeMilitaryPreparationSummaryPrivateProbeV1(
    const MilitaryPreparationSummaryPrivateProbeV1 &probe) {
  std::string output =
      "{\"private_build\":true,\"read_only\":true,\"advertised\":false";
  output += ",\"private_key\":\"";
  output += kMilitaryPreparationSummaryPrivateProbeKeyV1;
  output += "\",\"installed\":";
  output += probe.installed ? "true" : "false";
  output += ",\"request_prepared\":";
  output += probe.request_prepared ? "true" : "false";
  output += ",\"result_published\":";
  output += probe.result_published ? "true" : "false";
  output += ",\"published_execution_count\":" +
            std::to_string(probe.published_execution_count);
  output += ",\"result\":";
  output += SerializeMilitaryPreparationSummaryV1(probe.published_result);
  output += '}';
  return output;
}

} // namespace xar::bridge
