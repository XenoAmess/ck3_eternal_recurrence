#pragma once

#include "xar_bridge/zhongguo_case_snapshot_v1.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class ZhongguoManagerGovernanceSnapshotStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

enum class ZhongguoManagerSubjectBindingKindV1 : std::uint32_t {
  unavailable = 0,
  played_character = 1,
  bounded_ai_direct_manager = 2,
};

struct ZhongguoManagerSubjectBindingV1 {
  ZhongguoManagerSubjectBindingKindV1 kind =
      ZhongguoManagerSubjectBindingKindV1::unavailable;
  ZhongguoTypedIntegerV1 manager_character_id;
  ZhongguoTypedIntegerV1 owner_character_id;
  // Available only for the AI path.  The value names the typed selector that
  // admitted the direct-vassal manager; it is never a caller assertion.
  ZhongguoTypedStringV1 bounded_ai_manager_dependency;

  friend bool operator==(const ZhongguoManagerSubjectBindingV1 &,
                         const ZhongguoManagerSubjectBindingV1 &) = default;
};

struct ZhongguoManagerFCaseV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedBooleanV1 active;
  ZhongguoTypedIntegerV1 revision;

  friend bool operator==(const ZhongguoManagerFCaseV1 &,
                         const ZhongguoManagerFCaseV1 &) = default;
};

struct ZhongguoManagerTeamSnapshotV1 {
  ZhongguoTypedIntegerV1 status;
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 revision;
  ZhongguoTypedIntegerV1 source_cycle;
  ZhongguoTypedIntegerV1 cohort_n;
  ZhongguoTypedIntegerV1 targets;
  ZhongguoTypedIntegerV1 jingcha;
  ZhongguoTypedIntegerV1 calibration;
  ZhongguoTypedIntegerV1 pip_success;
  ZhongguoTypedIntegerV1 appeal_overturn;
  ZhongguoTypedIntegerV1 retention;
  ZhongguoTypedIntegerV1 hc_efficiency;

  friend bool operator==(const ZhongguoManagerTeamSnapshotV1 &,
                         const ZhongguoManagerTeamSnapshotV1 &) = default;
};

struct ZhongguoManagerReceiptV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedIntegerV1 choice;

  friend bool operator==(const ZhongguoManagerReceiptV1 &,
                         const ZhongguoManagerReceiptV1 &) = default;
};

struct ZhongguoManagerDistributionSnapshotV1 {
  ZhongguoTypedBooleanV1 available;
  ZhongguoTypedIntegerV1 mode;
  ZhongguoTypedIntegerV1 rule_source;
  ZhongguoTypedIntegerV1 top_slots;
  ZhongguoTypedIntegerV1 middle_slots;
  ZhongguoTypedIntegerV1 bottom_slots;
  ZhongguoTypedIntegerV1 conserved_slots;

  friend bool operator==(const ZhongguoManagerDistributionSnapshotV1 &,
                         const ZhongguoManagerDistributionSnapshotV1 &) =
      default;
};

struct ZhongguoManagerNextCyclePolicyV1 {
  ZhongguoTypedIntegerV1 status;
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 source_reviewer_character_id;
  ZhongguoTypedIntegerV1 source_cycle;
  ZhongguoTypedIntegerV1 source_case;
  ZhongguoTypedIntegerV1 source_revision;
  ZhongguoTypedIntegerV1 input_revision;
  ZhongguoTypedIntegerV1 mode;
  ZhongguoTypedIntegerV1 rule_source;
  ZhongguoTypedIntegerV1 due_cycle;

  friend bool operator==(const ZhongguoManagerNextCyclePolicyV1 &,
                         const ZhongguoManagerNextCyclePolicyV1 &) = default;
};

struct ZhongguoManagerEffectiveDistributionV1 {
  ZhongguoTypedIntegerV1 mode;
  ZhongguoTypedIntegerV1 cycle;
  ZhongguoTypedIntegerV1 source_cycle;
  ZhongguoTypedIntegerV1 source_case;
  ZhongguoTypedIntegerV1 input_revision;
  ZhongguoTypedIntegerV1 settled_cycle;
  ZhongguoTypedIntegerV1 settlement_receipt;
  ZhongguoTypedIntegerV1 actual_cohort_n;
  ZhongguoTypedIntegerV1 actual_bottom_slots;

  friend bool operator==(const ZhongguoManagerEffectiveDistributionV1 &,
                         const ZhongguoManagerEffectiveDistributionV1 &) =
      default;
};

struct ZhongguoManagerScoreV1 {
  ZhongguoTypedIntegerV1 sum;
  ZhongguoTypedIntegerV1 mode;

  friend bool operator==(const ZhongguoManagerScoreV1 &,
                         const ZhongguoManagerScoreV1 &) = default;
};

struct ZhongguoManagerComponent8V1 {
  ZhongguoTypedIntegerV1 status;
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 source_cycle;
  ZhongguoTypedIntegerV1 source_case;
  ZhongguoTypedIntegerV1 source_revision;
  ZhongguoTypedIntegerV1 input_revision;
  ZhongguoTypedIntegerV1 component;
  ZhongguoTypedIntegerV1 value;
  ZhongguoTypedIntegerV1 due_cycle;
  ZhongguoTypedIntegerV1 settled_by_owner_character_id;
  ZhongguoTypedIntegerV1 settled_cycle;
  ZhongguoTypedIntegerV1 settled_value;
  ZhongguoTypedIntegerV1 settlement_receipt;

  friend bool operator==(const ZhongguoManagerComponent8V1 &,
                         const ZhongguoManagerComponent8V1 &) = default;
};

struct ZhongguoManagerGovernanceReadinessV1 {
  bool subject_binding_ready = false;
  bool bounded_ai_dependency_ready = false;
  bool case_identity_ready = false;
  bool team_snapshot_ready = false;
  bool f035_receipt_ready = false;
  bool distribution_snapshot_ready = false;
  bool distribution_conservation_ready = false;
  bool next_cycle_policy_ready = false;
  bool effective_distribution_ready = false;
  bool distribution_settlement_ready = false;
  bool actual_bottom_slots_ready = false;
  bool distribution_lifecycle_ready = false;
  bool f032_receipt_ready = false;
  bool manager_score_ready = false;
  bool component8_token_ready = false;
  bool component8_settlement_ready = false;
  bool component8_lifecycle_ready = false;
  bool same_frame_ready = false;
  bool ready = false;

  friend bool operator==(const ZhongguoManagerGovernanceReadinessV1 &,
                         const ZhongguoManagerGovernanceReadinessV1 &) =
      default;
};

struct ZhongguoManagerGovernanceSnapshotV1 {
  ZhongguoManagerGovernanceSnapshotStatusV1 status =
      ZhongguoManagerGovernanceSnapshotStatusV1::unavailable;
  std::string case_kind;
  std::string request_nonce;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t player_character_id = -1;
  std::int32_t subject_character_id = -1;
  std::int32_t requested_owner_character_id = -1;
  ZhongguoManagerSubjectBindingV1 subject_binding;
  ZhongguoManagerFCaseV1 f_case;
  ZhongguoManagerTeamSnapshotV1 team_snapshot;
  ZhongguoManagerReceiptV1 f035_receipt;
  ZhongguoManagerDistributionSnapshotV1 distribution_snapshot;
  ZhongguoManagerNextCyclePolicyV1 next_cycle_policy;
  ZhongguoManagerEffectiveDistributionV1 effective_distribution;
  ZhongguoManagerReceiptV1 f032_receipt;
  ZhongguoManagerScoreV1 manager_score;
  ZhongguoManagerComponent8V1 component8;
  ZhongguoManagerGovernanceReadinessV1 readiness;
  std::string unavailable_reason;

  friend bool operator==(const ZhongguoManagerGovernanceSnapshotV1 &,
                         const ZhongguoManagerGovernanceSnapshotV1 &) =
      default;
};

enum class ReadZhongguoManagerGovernanceSnapshotResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view
    kZhongguoManagerGovernanceSnapshotV1Capability =
        "game.command.query-zhongguo-manager-governance-snapshot-v1";
inline constexpr std::string_view kZhongguoManagerGovernanceSnapshotV1Step =
    "query-zhongguo-manager-governance-snapshot-v1";
inline constexpr std::string_view
    kZhongguoManagerGovernanceSnapshotV1CaseKind =
        "zhongguo.manager-governance";
inline constexpr std::string_view
    kZhongguoManagerGovernanceSnapshotV1BackendId =
        "ck3-1.19.0.6-native-zhongguo-manager-governance-snapshot-v1";
inline constexpr std::string_view
    kZhongguoManagerGovernanceSnapshotV1ConsumerId =
        "xar-autoplayer-zhongguo-manager-governance-snapshot-v1";
inline constexpr std::string_view
    kZhongguoManagerGovernanceSnapshotV1AllowlistId =
        "zg361-manager-governance-v1";
inline constexpr std::string_view kZhongguoBoundedAiManagerDependencyV1 =
    "zg361-bounded-ai-direct-manager-selection-v1";

inline constexpr std::array<std::string_view, 77>
    kZhongguoManagerGovernanceSnapshotV1VariableAllowlist{
        "zg361_case_f_owner",
        "zg361_case_f_subject",
        "zg361_case_f_cycle_serial",
        "zg361_case_f_case_serial",
        "zg361_case_f_state",
        "zg361_case_f_active",
        "zg361_case_f_revision",
        "zg361_mg_team_snapshot_status",
        "zg361_mg_team_snapshot_owner",
        "zg361_mg_team_snapshot_subject",
        "zg361_mg_team_snapshot_cycle",
        "zg361_mg_team_snapshot_case",
        "zg361_mg_team_snapshot_revision",
        "zg361_mg_team_snapshot_source_cycle",
        "zg361_mg_team_n",
        "zg361_mg_team_targets",
        "zg361_mg_team_jingcha",
        "zg361_mg_team_calibration",
        "zg361_mg_team_pip_success",
        "zg361_mg_team_appeal_overturn",
        "zg361_mg_team_retention",
        "zg361_mg_team_hc_efficiency",
        "zg361_mg_m035_receipt_owner",
        "zg361_mg_m035_receipt_subject",
        "zg361_mg_m035_receipt_cycle",
        "zg361_mg_m035_receipt_case",
        "zg361_mg_m035_receipt_state",
        "zg361_mg_m035_receipt_choice",
        "zg361_mg_distribution_policy_available",
        "zg361_mg_distribution_mode",
        "zg361_mg_distribution_rule_source",
        "zg361_mg_distribution_top_slots",
        "zg361_mg_distribution_middle_slots",
        "zg361_mg_distribution_bottom_slots",
        "zg361_mg_distribution_conserved",
        "zg361_mg_distribution_policy_status",
        "zg361_mg_distribution_policy_owner",
        "zg361_mg_distribution_policy_subject",
        "zg361_mg_distribution_policy_source_reviewer",
        "zg361_mg_distribution_policy_source_cycle",
        "zg361_mg_distribution_policy_source_case",
        "zg361_mg_distribution_policy_source_revision",
        "zg361_mg_distribution_policy_input_revision",
        "zg361_mg_distribution_policy_mode",
        "zg361_mg_distribution_policy_rule_source",
        "zg361_mg_distribution_policy_due_cycle",
        "zg361_mg_distribution_effective_mode",
        "zg361_mg_distribution_effective_cycle",
        "zg361_mg_distribution_effective_source_cycle",
        "zg361_mg_distribution_effective_source_case",
        "zg361_mg_distribution_effective_input_revision",
        "zg361_mg_distribution_policy_settled_cycle",
        "zg361_mg_distribution_policy_settlement_receipt",
        "zg361_cohort_n",
        "zg361_bottom_slots",
        "zg361_mg_m032_receipt_owner",
        "zg361_mg_m032_receipt_subject",
        "zg361_mg_m032_receipt_cycle",
        "zg361_mg_m032_receipt_case",
        "zg361_mg_m032_receipt_state",
        "zg361_mg_m032_receipt_choice",
        "zg361_mg_manager_score",
        "zg361_mg_manager_score_mode",
        "zg361_mg_organization_input_status",
        "zg361_mg_organization_input_owner",
        "zg361_mg_organization_input_subject",
        "zg361_mg_organization_input_source_cycle",
        "zg361_mg_organization_input_source_case",
        "zg361_mg_organization_input_source_revision",
        "zg361_mg_organization_input_revision",
        "zg361_mg_organization_input_component",
        "zg361_mg_organization_input_value",
        "zg361_mg_organization_input_due_cycle",
        "zg361_mg_organization_settled_by_owner",
        "zg361_mg_organization_settled_cycle",
        "zg361_mg_organization_settled_value",
        "zg361_mg_organization_settlement_receipt",
    };

using ZhongguoManagerGovernanceNativeEnvironmentV1 =
    ZhongguoCaseNativeEnvironmentV1;
using ZhongguoManagerGovernanceRawVariableV1 = ZhongguoRawVariableV1;
using ZhongguoManagerGovernanceFrameV1 = game::ZhongguoCaseFrameV1;

enum class ZhongguoBoundedAiManagerAuthorizationV1 : std::uint32_t {
  dependency_unavailable = 0,
  authorized_direct_manager = 1,
  rejected = 2,
};

using AuthorizeZhongguoBoundedAiManagerV1 =
    ZhongguoBoundedAiManagerAuthorizationV1 (*)(
        void *, std::int32_t, std::int32_t, std::int32_t) noexcept;

struct ZhongguoManagerGovernanceAccessV1 {
  void *context = nullptr;
  CaptureZhongguoCaseFrameV1 capture_frame = nullptr;
  IsZhongguoCaseMainThreadV1 is_main_thread = nullptr;
  ReadZhongguoCaseMemoryV1 read_memory = nullptr;
  ValidateZhongguoCharacterV1 validate_character = nullptr;
  ReadZhongguoAllowlistedVariableV1 read_allowlisted_variable = nullptr;
  // Required only when subject != the paused played character.  Production
  // must bind this to a typed native selector proving that subject is a
  // direct vassal of player, AI-controlled, celestial, landed and duke+.
  AuthorizeZhongguoBoundedAiManagerV1 authorize_bounded_ai_manager = nullptr;
};

struct ZhongguoManagerGovernanceSnapshotRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
  std::int32_t subject_character_id = -1;
  std::int32_t owner_character_id = -1;
  std::string request_nonce;
};

ZhongguoManagerGovernanceNativeEnvironmentV1
BindZhongguoManagerGovernanceNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

game::ReadZhongguoManagerGovernanceSnapshotResultV1
ReadZhongguoManagerGovernanceSnapshotV1(
    const ZhongguoManagerGovernanceNativeEnvironmentV1 &environment,
    const ZhongguoManagerGovernanceAccessV1 &access,
    const ZhongguoManagerGovernanceSnapshotRequestV1 &request,
    game::ZhongguoManagerGovernanceSnapshotV1 &output) noexcept;

std::string SerializeZhongguoManagerGovernanceSnapshotV1(
    const game::ZhongguoManagerGovernanceSnapshotV1 &snapshot);

} // namespace xar::ck3_11906
