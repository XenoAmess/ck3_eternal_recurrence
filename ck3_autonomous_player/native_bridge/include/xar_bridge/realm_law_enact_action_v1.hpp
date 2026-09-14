#pragma once

#include "xar_bridge/realm_law_governance_snapshot_v1.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::bridge {

inline constexpr std::size_t kRealmLawEnactMaximumResourcesV1 =
    kRealmLawGovernanceMaximumCostsV1;
inline constexpr std::size_t kRealmLawEnactRequestIdCapacityV1 = 64;

enum class RealmLawEnactActionFailureV1 : std::uint8_t {
  none,
  request_contract_invalid,
  exact_build_mismatch,
  application_main_thread_required,
  callbacks_unavailable,
  observation_unavailable,
  not_paused,
  snapshot_unavailable,
  stale_snapshot,
  candidate_not_found,
  authority_denied,
  final_legality_denied,
  resource_observation_invalid,
  budget_not_authorized,
  insufficient_resources,
  state_changed_before_submit,
  working_storage_unavailable,
  native_submit_rejected,
};

enum class RealmLawEnactActionAckStatusV1 : std::uint8_t {
  rejected_before_submit,
  submitted_verification_pending,
};

enum class RealmLawEnactActionReceiptStatusV1 : std::uint8_t {
  rejected,
  enacted,
  failed,
};

enum class RealmLawEnactActionReceiptFailureV1 : std::uint8_t {
  none,
  action_rejected,
  invalid_ack,
  post_observation_unavailable,
  no_new_paused_snapshot,
  player_identity_changed,
  group_or_candidate_unavailable,
  effective_law_not_enacted,
  resource_recheck_failed,
  succession_shape_changed,
};

struct RealmLawEnactBudgetV1 {
  RealmLawGovernanceKeyV1 currency_key{};
  std::int64_t maximum_spend_raw = 0;

  friend bool operator==(const RealmLawEnactBudgetV1 &,
                         const RealmLawEnactBudgetV1 &) = default;
};

struct RealmLawEnactResourceBalanceV1 {
  RealmLawGovernanceKeyV1 currency_key{};
  std::int64_t amount_raw = 0;

  friend bool operator==(const RealmLawEnactResourceBalanceV1 &,
                         const RealmLawEnactResourceBalanceV1 &) = default;
};

struct RealmLawEnactActionRequestV1 {
  std::string request_id;
  RealmLawGovernanceKeyV1 group_key{};
  RealmLawGovernanceKeyV1 law_key{};
  std::uint64_t expected_public_revision = 0;
  std::uint64_t expected_native_revision = 0;
  std::uint64_t expected_proof_epoch = 0;
  std::int64_t expected_date_raw = 0;
  std::int32_t expected_player_character_id = -1;
  std::uint32_t budget_count = 0;
  std::array<RealmLawEnactBudgetV1, kRealmLawEnactMaximumResourcesV1>
      budgets{};
};

// Shared glue must construct this value from one completed LAW2 observation
// and resource reads belonging to that exact paused frame. The action core
// captures it twice immediately before submit and never accepts a pointer or
// borrowed engine lifetime.
struct RealmLawEnactActionObservationV1 {
  bool available = false;
  bool paused = false;
  RealmLawGovernanceSnapshotV1 law_snapshot{};
  bool resources_complete = false;
  std::uint32_t resource_count = 0;
  std::array<RealmLawEnactResourceBalanceV1,
             kRealmLawEnactMaximumResourcesV1>
      resources{};
};

struct RealmLawEnactChargeV1 {
  RealmLawGovernanceKeyV1 currency_key{};
  std::int64_t cost_raw = 0;
  std::int64_t pre_balance_raw = 0;
  std::int64_t post_balance_raw = 0;

  friend bool operator==(const RealmLawEnactChargeV1 &,
                         const RealmLawEnactChargeV1 &) = default;
};

struct RealmLawEnactSubmissionV1 {
  std::int32_t player_character_id = -1;
  RealmLawGovernanceKeyV1 group_key{};
  RealmLawGovernanceKeyV1 previous_effective_law_key{};
  RealmLawGovernanceKeyV1 requested_law_key{};
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::uint32_t charge_count = 0;
  std::array<RealmLawEnactChargeV1, kRealmLawEnactMaximumResourcesV1>
      charges{};
};

struct RealmLawEnactActionAckV1 {
  RealmLawEnactActionAckStatusV1 status =
      RealmLawEnactActionAckStatusV1::rejected_before_submit;
  bool verification_pending = false;
  RealmLawEnactActionFailureV1 failure =
      RealmLawEnactActionFailureV1::callbacks_unavailable;
  std::string request_id;
  std::uint64_t pre_public_revision = 0;
  std::uint64_t pre_native_revision = 0;
  std::uint64_t pre_proof_epoch = 0;
  std::int64_t pre_date_raw = 0;
  std::int32_t player_character_id = -1;
  RealmLawGovernanceKeyV1 group_key{};
  RealmLawGovernanceKeyV1 previous_effective_law_key{};
  RealmLawGovernanceKeyV1 requested_law_key{};
  std::uint32_t charge_count = 0;
  std::array<RealmLawEnactChargeV1, kRealmLawEnactMaximumResourcesV1>
      charges{};
  RealmLawGovernanceSuccessionShapeV1 expected_succession{};
  RealmLawGovernanceTitleBaselineV1 pre_title_successors{};
  RealmLawGovernanceReasonV1 blocked_reason{};
};

struct RealmLawEnactActionReceiptV1 {
  RealmLawEnactActionReceiptStatusV1 status =
      RealmLawEnactActionReceiptStatusV1::failed;
  RealmLawEnactActionReceiptFailureV1 failure =
      RealmLawEnactActionReceiptFailureV1::invalid_ack;
  RealmLawEnactActionFailureV1 rejected_action_failure =
      RealmLawEnactActionFailureV1::none;
  std::string request_id;
  std::uint64_t post_public_revision = 0;
  std::uint64_t post_native_revision = 0;
  std::uint64_t post_proof_epoch = 0;
  std::int64_t post_date_raw = 0;
  RealmLawGovernanceKeyV1 effective_law_key{};
  std::uint32_t charge_count = 0;
  std::array<RealmLawEnactChargeV1, kRealmLawEnactMaximumResourcesV1>
      charges{};
  RealmLawGovernanceSuccessionShapeV1 observed_succession{};
  RealmLawGovernanceTitleBaselineV1 post_title_successors{};
  bool effective_law_verified = false;
  bool resources_verified = false;
  bool succession_verified = false;
};

using CaptureRealmLawEnactActionObservationV1 = bool (*)(
    void *context, RealmLawEnactActionObservationV1 &output) noexcept;
using SubmitRealmLawEnactActionV1 = bool (*)(
    void *context, const RealmLawEnactSubmissionV1 &submission) noexcept;

struct RealmLawEnactActionAccessV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uint32_t current_thread_id = 0;
  std::uint32_t application_main_thread_id = 0;
  void *context = nullptr;
  CaptureRealmLawEnactActionObservationV1 capture_observation = nullptr;
  SubmitRealmLawEnactActionV1 submit = nullptr;
};

RealmLawEnactActionAckStatusV1 ExecuteRealmLawEnactActionV1(
    const RealmLawEnactActionAccessV1 &access,
    const RealmLawEnactActionRequestV1 &request,
    RealmLawEnactActionAckV1 &ack) noexcept;

RealmLawEnactActionReceiptStatusV1 VerifyRealmLawEnactActionReceiptV1(
    const RealmLawEnactActionAckV1 &ack,
    const RealmLawEnactActionObservationV1 &post_observation,
    RealmLawEnactActionReceiptV1 &receipt) noexcept;

std::string_view RealmLawEnactActionFailureNameV1(
    RealmLawEnactActionFailureV1 failure) noexcept;
std::string_view RealmLawEnactActionReceiptFailureNameV1(
    RealmLawEnactActionReceiptFailureV1 failure) noexcept;

} // namespace xar::bridge
