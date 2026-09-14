#include "xar_bridge/military_preparation_summary_v1.hpp"

#include <array>

namespace xar::bridge {
namespace {

using RawValues =
    std::array<std::int64_t, kMilitaryPreparationSummaryFieldCountV1>;

void Fail(MilitaryPreparationSummaryResultV1 &output,
          std::uint32_t failure) noexcept {
  output = {};
  output.status = MilitaryPreparationSummaryStatusV1::unavailable;
  output.failure_flags = failure;
}

MilitaryPreparationSummaryValuesV1 Decode(const RawValues &raw) noexcept {
  return {raw[0], raw[1], raw[2], raw[3], raw[4],
          raw[5], raw[6], raw[7], raw[8], raw[9]};
}

bool EvaluatePass(const MilitaryPreparationSummaryEnvironmentV1 &environment,
                  void *session, RawValues &values,
                  std::uint32_t &failure) noexcept {
  for (std::size_t index = 0;
       index < kMilitaryPreparationSummaryDefinitionKeysV1.size(); ++index) {
    const void *definition = nullptr;
    if (!environment.resolve_definition(
            environment.callback_context,
            kMilitaryPreparationSummaryDefinitionKeysV1[index], definition) ||
        definition == nullptr ||
        !environment.definition_is_valid(environment.callback_context,
                                         definition)) {
      failure = military_preparation_summary_failure_definition;
      return false;
    }
    std::int64_t value = 0;
    if (!environment.evaluate_fixed(environment.callback_context, definition,
                                    session, value)) {
      failure = military_preparation_summary_failure_evaluation;
      return false;
    }
    values[index] = value;
  }
  return true;
}

bool CallbacksComplete(
    const MilitaryPreparationSummaryEnvironmentV1 &environment) noexcept {
  return environment.read_frame != nullptr &&
         environment.begin_session != nullptr &&
         environment.end_session != nullptr &&
         environment.resolve_definition != nullptr &&
         environment.definition_is_valid != nullptr &&
         environment.evaluate_fixed != nullptr;
}

} // namespace

bool ReadMilitaryPreparationSummaryV1(
    const MilitaryPreparationSummaryEnvironmentV1 &environment,
    std::uint64_t expected_revision,
    MilitaryPreparationSummaryResultV1 &output) noexcept {
  output = {};
  if (!environment.observer_enabled) {
    output.status = MilitaryPreparationSummaryStatusV1::disabled;
    output.failure_flags = military_preparation_summary_failure_disabled;
    return false;
  }
  if (!environment.exact_build_admitted ||
      environment.admitted_executable_sha256 !=
          kMilitaryPreparationSummaryExecutableSha256V1) {
    Fail(output, military_preparation_summary_failure_exact_build);
    return false;
  }
  if (!CallbacksComplete(environment)) {
    Fail(output, military_preparation_summary_failure_callbacks);
    return false;
  }
  if (environment.current_thread_id == 0 ||
      environment.current_thread_id != environment.application_main_thread_id) {
    Fail(output, military_preparation_summary_failure_application_main);
    return false;
  }

  MilitaryPreparationFrameIdentityV1 before{};
  if (!environment.read_frame(environment.callback_context, before)) {
    Fail(output, military_preparation_summary_failure_frame_read);
    return false;
  }
  if (!before.paused) {
    Fail(output, military_preparation_summary_failure_not_paused);
    return false;
  }
  if (expected_revision == 0 || before.snapshot_revision != expected_revision) {
    Fail(output, military_preparation_summary_failure_revision);
    return false;
  }
  if (before.played_character_id <= 0) {
    Fail(output, military_preparation_summary_failure_character);
    return false;
  }

  void *session = nullptr;
  const bool session_begun = environment.begin_session(
      environment.callback_context, before.played_character_id, session);
  if (!session_begun || session == nullptr) {
    const bool teardown_ok =
        session == nullptr ||
        environment.end_session(environment.callback_context, session);
    Fail(output, military_preparation_summary_failure_session |
                     (teardown_ok
                          ? 0U
                          : military_preparation_summary_failure_teardown));
    return false;
  }

  RawValues first{};
  RawValues second{};
  std::uint32_t failure = military_preparation_summary_failure_none;
  if (!EvaluatePass(environment, session, first, failure) ||
      !EvaluatePass(environment, session, second, failure)) {
    const bool teardown_ok =
        environment.end_session(environment.callback_context, session);
    Fail(output, failure | (teardown_ok ? 0U
                                        : military_preparation_summary_failure_teardown));
    return false;
  }
  if (first != second) {
    const bool teardown_ok =
        environment.end_session(environment.callback_context, session);
    Fail(output, military_preparation_summary_failure_unstable_values |
                     (teardown_ok
                          ? 0U
                          : military_preparation_summary_failure_teardown));
    return false;
  }

  MilitaryPreparationFrameIdentityV1 after{};
  const bool after_read =
      environment.read_frame(environment.callback_context, after);
  const bool teardown_ok =
      environment.end_session(environment.callback_context, session);
  if (!after_read) {
    Fail(output, military_preparation_summary_failure_frame_read |
                     (teardown_ok
                          ? 0U
                          : military_preparation_summary_failure_teardown));
    return false;
  }
  if (after != before) {
    Fail(output, military_preparation_summary_failure_frame_changed |
                     (teardown_ok
                          ? 0U
                          : military_preparation_summary_failure_teardown));
    return false;
  }
  if (!teardown_ok) {
    Fail(output, military_preparation_summary_failure_teardown);
    return false;
  }

  output.status = MilitaryPreparationSummaryStatusV1::available;
  output.failure_flags = military_preparation_summary_failure_none;
  output.frame = before;
  output.values = Decode(first);
  output.observation_ready = true;
  output.offline_fixture = environment.offline_fixture;
  return true;
}

} // namespace xar::bridge
