#pragma once

#include "xar_bridge/military_preparation_summary_v1_abi.hpp"

#include <array>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

enum MilitaryPreparationSummaryFailureV1 : std::uint32_t {
  military_preparation_summary_failure_none = 0,
  military_preparation_summary_failure_disabled = 1U << 0,
  military_preparation_summary_failure_exact_build = 1U << 1,
  military_preparation_summary_failure_callbacks = 1U << 2,
  military_preparation_summary_failure_application_main = 1U << 3,
  military_preparation_summary_failure_frame_read = 1U << 4,
  military_preparation_summary_failure_not_paused = 1U << 5,
  military_preparation_summary_failure_revision = 1U << 6,
  military_preparation_summary_failure_character = 1U << 7,
  military_preparation_summary_failure_session = 1U << 8,
  military_preparation_summary_failure_definition = 1U << 9,
  military_preparation_summary_failure_evaluation = 1U << 10,
  military_preparation_summary_failure_unstable_values = 1U << 11,
  military_preparation_summary_failure_frame_changed = 1U << 12,
  military_preparation_summary_failure_teardown = 1U << 13,
};

enum class MilitaryPreparationSummaryStatusV1 : std::uint8_t {
  disabled,
  unavailable,
  available,
};

struct MilitaryPreparationFrameIdentityV1 {
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = 0;
  std::uint64_t gameplay_rng_fingerprint = 0;
  bool paused = false;

  bool operator==(const MilitaryPreparationFrameIdentityV1 &) const = default;
};

struct MilitaryPreparationSummaryValuesV1 {
  std::int64_t current_military_strength_raw = 0;
  std::int64_t max_military_strength_raw = 0;
  std::int64_t number_of_knights_raw = 0;
  std::int64_t max_number_of_knights_raw = 0;
  std::int64_t maa_gold_expense_relative_raw = 0;
  std::int64_t maa_gold_min_raw = 0;
  std::int64_t maa_gold_ideal_raw = 0;
  std::int64_t maa_gold_max_raw = 0;
  std::int64_t maa_gold_chance_below_min_raw = 0;
  std::int64_t maa_gold_chance_below_ideal_raw = 0;

  bool operator==(const MilitaryPreparationSummaryValuesV1 &) const = default;
};

struct MilitaryPreparationSummaryResultV1 {
  MilitaryPreparationSummaryStatusV1 status =
      MilitaryPreparationSummaryStatusV1::unavailable;
  std::uint32_t failure_flags = military_preparation_summary_failure_none;
  MilitaryPreparationFrameIdentityV1 frame{};
  MilitaryPreparationSummaryValuesV1 values{};
  bool observation_ready = false;
  bool offline_fixture = false;
};

using MilitaryPreparationReadFrameV1 = bool (*)(
    void *context, MilitaryPreparationFrameIdentityV1 &output) noexcept;
using MilitaryPreparationBeginEvaluationSessionV1 = bool (*)(
    void *context, std::int32_t played_character_id,
    void *&session) noexcept;
using MilitaryPreparationEndEvaluationSessionV1 = bool (*)(
    void *context, void *session) noexcept;
using MilitaryPreparationResolveDefinitionV1 = bool (*)(
    void *context, std::string_view key,
    const void *&definition) noexcept;
using MilitaryPreparationDefinitionIsValidV1 = bool (*)(
    void *context, const void *definition) noexcept;
using MilitaryPreparationEvaluateFixedV1 = bool (*)(
    void *context, const void *definition, void *session,
    std::int64_t &output_raw) noexcept;

struct MilitaryPreparationSummaryEnvironmentV1 {
  bool observer_enabled = kMilitaryPreparationSummaryEnabledByDefaultV1;
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uint32_t current_thread_id = 0;
  std::uint32_t application_main_thread_id = 0;
  bool offline_fixture = false;
  void *callback_context = nullptr;
  MilitaryPreparationReadFrameV1 read_frame = nullptr;
  MilitaryPreparationBeginEvaluationSessionV1 begin_session = nullptr;
  MilitaryPreparationEndEvaluationSessionV1 end_session = nullptr;
  MilitaryPreparationResolveDefinitionV1 resolve_definition = nullptr;
  MilitaryPreparationDefinitionIsValidV1 definition_is_valid = nullptr;
  MilitaryPreparationEvaluateFixedV1 evaluate_fixed = nullptr;
};

// Executes a single synchronous application-main transaction. Native session
// and definition pointers are borrowed only inside this call and never enter
// the result or process-global storage.
bool ReadMilitaryPreparationSummaryV1(
    const MilitaryPreparationSummaryEnvironmentV1 &environment,
    std::uint64_t expected_revision,
    MilitaryPreparationSummaryResultV1 &output) noexcept;

} // namespace xar::bridge
