#pragma once

#include "xar_bridge/major_decision_found_kingdom_observer_v1.hpp"

#include <cstdint>
#include <string_view>

namespace xar::bridge {

struct MajorDecisionFoundKingdomSourcePlayerLeaseV1 {
  bool identity_round_trip = false;
  std::uintptr_t native_address = 0;
  std::int32_t character_id = -1;
};

struct MajorDecisionFoundKingdomSourceDatabaseLeaseV1 {
  bool identity_round_trip = false;
  std::uintptr_t native_address = 0;
  std::uint64_t identity = 0;
  std::uint64_t generation = 0;
};

struct MajorDecisionFoundKingdomSourceDefinitionLeaseV1 {
  bool identity_round_trip = false;
  bool source_block_sha256_round_trip = false;
  std::uintptr_t native_address = 0;
  std::uint64_t identity = 0;
  std::uint64_t generation = 0;
  std::string_view decision_id{};
};

struct MajorDecisionFoundKingdomSourceEligibilityV1 {
  bool is_shown = false;
  bool is_valid = false;
  bool is_valid_showing_failures_only = false;

  friend bool operator==(
      const MajorDecisionFoundKingdomSourceEligibilityV1 &,
      const MajorDecisionFoundKingdomSourceEligibilityV1 &) = default;
};

struct MajorDecisionFoundKingdomSourceCostV1 {
  std::int64_t gold_q100000 = 0;
  std::int64_t treasury_q100000 = 0;
  std::int64_t prestige_q100000 = 0;
  std::int64_t piety_q100000 = 0;

  friend bool operator==(const MajorDecisionFoundKingdomSourceCostV1 &,
                         const MajorDecisionFoundKingdomSourceCostV1 &) =
      default;
};

enum class MajorDecisionFoundKingdomSourceAdapterFailureV1 : std::uint8_t {
  none = 0,
  exact_build_mismatch,
  callbacks_unavailable,
  application_main_thread_required,
  frame_unavailable,
  not_paused,
  frame_invalid,
  played_character_unavailable,
  played_character_drift,
  decision_database_unavailable,
  decision_database_drift,
  decision_definition_missing,
  decision_definition_identity_mismatch,
  decision_definition_drift,
  eligibility_evaluation_failed,
  evaluated_cost_evaluation_failed,
  affordability_evaluation_failed,
  can_take_evaluation_failed,
  source_sample_drift,
  frame_drift,
  core_rejected,
};

using CaptureMajorDecisionFoundKingdomSourceFrameV1 = bool (*)(
    void *context, MajorDecisionFoundKingdomFrameV1 &output) noexcept;
using ResolveMajorDecisionFoundKingdomSourcePlayerV1 = bool (*)(
    void *context, std::int32_t expected_character_id,
    MajorDecisionFoundKingdomSourcePlayerLeaseV1 &output) noexcept;
using ResolveMajorDecisionFoundKingdomSourceDatabaseV1 = bool (*)(
    void *context,
    MajorDecisionFoundKingdomSourceDatabaseLeaseV1 &output) noexcept;
using LookupMajorDecisionFoundKingdomSourceDefinitionV1 = bool (*)(
    void *context,
    const MajorDecisionFoundKingdomSourceDatabaseLeaseV1 &database,
    std::string_view decision_id,
    MajorDecisionFoundKingdomSourceDefinitionLeaseV1 &output) noexcept;
using EvaluateMajorDecisionFoundKingdomSourceEligibilityV1 = bool (*)(
    void *context,
    const MajorDecisionFoundKingdomSourceDefinitionLeaseV1 &definition,
    const MajorDecisionFoundKingdomSourcePlayerLeaseV1 &player,
    MajorDecisionFoundKingdomSourceEligibilityV1 &output) noexcept;
using EvaluateMajorDecisionFoundKingdomSourceCostV1 = bool (*)(
    void *context,
    const MajorDecisionFoundKingdomSourceDefinitionLeaseV1 &definition,
    const MajorDecisionFoundKingdomSourcePlayerLeaseV1 &player,
    MajorDecisionFoundKingdomSourceCostV1 &output) noexcept;
using EvaluateMajorDecisionFoundKingdomSourceBoolV1 = bool (*)(
    void *context,
    const MajorDecisionFoundKingdomSourceDefinitionLeaseV1 &definition,
    const MajorDecisionFoundKingdomSourcePlayerLeaseV1 &player,
    bool &output) noexcept;

struct MajorDecisionFoundKingdomSourceAccessV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uint32_t current_thread_id = 0;
  std::uint32_t application_main_thread_id = 0;
  void *context = nullptr;
  CaptureMajorDecisionFoundKingdomSourceFrameV1 capture_frame = nullptr;
  ResolveMajorDecisionFoundKingdomSourcePlayerV1 resolve_player = nullptr;
  ResolveMajorDecisionFoundKingdomSourceDatabaseV1 resolve_decision_database =
      nullptr;
  LookupMajorDecisionFoundKingdomSourceDefinitionV1 lookup_definition =
      nullptr;
  EvaluateMajorDecisionFoundKingdomSourceEligibilityV1 evaluate_eligibility =
      nullptr;
  EvaluateMajorDecisionFoundKingdomSourceCostV1 evaluate_cost = nullptr;
  EvaluateMajorDecisionFoundKingdomSourceBoolV1 evaluate_affordability =
      nullptr;
  EvaluateMajorDecisionFoundKingdomSourceBoolV1 evaluate_can_take = nullptr;
};

struct MajorDecisionFoundKingdomSourceResultV1 {
  MajorDecisionFoundKingdomSourceAdapterFailureV1 failure =
      MajorDecisionFoundKingdomSourceAdapterFailureV1::callbacks_unavailable;
  MajorDecisionFoundKingdomFailureV1 core_failure =
      MajorDecisionFoundKingdomFailureV1::source_sample_incomplete;
  MajorDecisionFoundKingdomSnapshotV1 snapshot{};
};

// Runs one synchronous, paused application-main transaction. The database,
// definition and played-character leases are resolved independently for both
// samples. Only copied evaluator results reach the pointer-free semantic core.
// There is deliberately no effect, preview or command callback in this API.
bool ObserveMajorDecisionFoundKingdomSourceV1(
    const MajorDecisionFoundKingdomSourceAccessV1 &access,
    MajorDecisionFoundKingdomSourceResultV1 &output) noexcept;

std::string_view MajorDecisionFoundKingdomSourceAdapterFailureNameV1(
    MajorDecisionFoundKingdomSourceAdapterFailureV1 failure) noexcept;

} // namespace xar::bridge
