#pragma once

#include "xar_bridge/zhongguo_case_snapshot_v1.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class ZhongguoB2PipSnapshotStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

struct ZhongguoB2PipGateV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 threshold;
  ZhongguoTypedIntegerV1 negative_component_count;
  ZhongguoTypedBooleanV1 evidence_complete;
  ZhongguoTypedIntegerV1 status;
  ZhongguoTypedIntegerV1 result_case_serial;
  ZhongguoTypedIntegerV1 result_grade;
  ZhongguoTypedIntegerV1 absolute_grade;
  ZhongguoTypedIntegerV1 kpi_frozen_q100000;
  ZhongguoTypedIntegerV1 governance_q100000;
  ZhongguoTypedIntegerV1 capability_q100000;
  ZhongguoTypedIntegerV1 growth_q100000;
  ZhongguoTypedIntegerV1 superior_q100000;
  ZhongguoTypedIntegerV1 values_q100000;
  ZhongguoTypedIntegerV1 collaboration_q100000;
  ZhongguoTypedIntegerV1 jingcha_q100000;
  ZhongguoTypedIntegerV1 organization_q100000;
};

struct ZhongguoB2PipIdentityV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedIntegerV1 task_kind;
  ZhongguoTypedBooleanV1 task_controllable;
  ZhongguoTypedIntegerV1 policy_route;
};

struct ZhongguoB2PipResponseV1 {
  ZhongguoTypedIntegerV1 subject_response;
  ZhongguoTypedIntegerV1 response_case_serial;
  ZhongguoTypedIntegerV1 response_author_character_id;
  ZhongguoTypedIntegerV1 acknowledgement_receipt_serial;
  ZhongguoTypedBooleanV1 goal_revision_used;
  ZhongguoTypedIntegerV1 refusal_receipt_serial;
};

struct ZhongguoB2PipSupportV1 {
  ZhongguoTypedBooleanV1 capacity_reserved;
  ZhongguoTypedIntegerV1 owner_capacity_used;
  ZhongguoTypedBooleanV1 support_absent;
  ZhongguoTypedIntegerV1 hours;
  ZhongguoTypedIntegerV1 attention_units;
  ZhongguoTypedIntegerV1 mentor_character_id;
  ZhongguoTypedIntegerV1 budget_owner_character_id;
  ZhongguoTypedIntegerV1 treasury_budget_allocated;
  ZhongguoTypedIntegerV1 treasury_budget_spent;
  ZhongguoTypedIntegerV1 support_receipt_serial;
  ZhongguoTypedBooleanV1 released;
  ZhongguoTypedBooleanV1 withheld;
  ZhongguoTypedBooleanV1 atomic_shortfall;
};

struct ZhongguoB2PipBudgetLedgerV1 {
  ZhongguoTypedIntegerV1 result_case_serial;
  ZhongguoTypedIntegerV1 treasury_penalty_paid;
  ZhongguoTypedIntegerV1 personal_gold_penalty_paid;
  ZhongguoTypedIntegerV1 support_treasury_allocated;
  ZhongguoTypedIntegerV1 support_treasury_spent;
};

struct ZhongguoB2PipTicketV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 expected_state;
  ZhongguoTypedIntegerV1 due_date_raw;
};

struct ZhongguoB2PipMidpointV1 {
  ZhongguoTypedIntegerV1 receipt_serial;
  ZhongguoTypedBooleanV1 resource_delivery_valid;
  ZhongguoTypedIntegerV1 progress_status;
  ZhongguoTypedIntegerV1 progress_red_code;
  ZhongguoTypedIntegerV1 state;
};

struct ZhongguoB2PipOutcomeV1 {
  ZhongguoTypedIntegerV1 code;
  ZhongguoTypedIntegerV1 settlement_receipt_serial;
  ZhongguoTypedIntegerV1 result_cycle_serial;
  ZhongguoTypedIntegerV1 result_case_serial;
  ZhongguoTypedIntegerV1 result_grade;
  ZhongguoTypedIntegerV1 stability_days_observed;
  ZhongguoTypedIntegerV1 independent_review_status;
  ZhongguoTypedIntegerV1 independent_review_red_code;
  ZhongguoTypedIntegerV1 graduation_receipt_serial;
  ZhongguoTypedIntegerV1 failure_receipt_serial;
  ZhongguoTypedBooleanV1 no_support_liability;
};

struct ZhongguoB2PipNextCycleEvidenceV1 {
  ZhongguoTypedIntegerV1 status;
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 source_cycle_serial;
  ZhongguoTypedIntegerV1 source_case_serial;
  ZhongguoTypedIntegerV1 due_cycle_serial;
  ZhongguoTypedIntegerV1 delta;
  ZhongguoTypedIntegerV1 consumed_cycle_serial;
  ZhongguoTypedIntegerV1 consumed_case_serial;
};

struct ZhongguoB2PipReadinessV1 {
  bool player_subject_binding_ready = false;
  bool owner_binding_ready = false;
  bool gate_ready = false;
  bool gate_evidence_ready = false;
  bool pip_identity_ready = false;
  bool response_ready = false;
  bool support_ready = false;
  bool budget_ledger_ready = false;
  bool midpoint_ready = false;
  bool outcome_ready = false;
  bool next_cycle_evidence_ready = false;
  bool d180_ticket_observation_ready = false;
  bool d365_ticket_observation_ready = false;
  bool modifier_observation_ready = false;
  bool same_frame_ready = false;
  bool ready = false;
};

struct ZhongguoB2PipSnapshotV1 {
  ZhongguoB2PipSnapshotStatusV1 status =
      ZhongguoB2PipSnapshotStatusV1::unavailable;
  std::string case_kind;
  std::string request_nonce;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t player_character_id = -1;
  std::int32_t subject_character_id = -1;
  std::int32_t requested_owner_character_id = -1;
  ZhongguoB2PipGateV1 gate;
  ZhongguoB2PipIdentityV1 pip;
  ZhongguoB2PipResponseV1 response;
  ZhongguoB2PipSupportV1 support;
  ZhongguoB2PipBudgetLedgerV1 budget_ledger;
  ZhongguoB2PipTicketV1 d180_ticket;
  ZhongguoB2PipTicketV1 d365_ticket;
  ZhongguoB2PipMidpointV1 midpoint;
  ZhongguoB2PipOutcomeV1 outcome;
  ZhongguoB2PipNextCycleEvidenceV1 next_cycle_evidence;
  ZhongguoTypedBooleanV1 pip_modifier_present;
  ZhongguoB2PipReadinessV1 readiness;
  std::string unavailable_reason;
};

enum class ReadZhongguoB2PipSnapshotResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kZhongguoB2PipSnapshotV1Capability =
    "game.command.query-zhongguo-b2-pip-snapshot-v1";
inline constexpr std::string_view kZhongguoB2PipSnapshotV1Step =
    "query-zhongguo-b2-pip-snapshot-v1";
inline constexpr std::string_view kZhongguoB2PipSnapshotV1CaseKind =
    "zhongguo.b2.pip";
inline constexpr std::string_view kZhongguoB2PipSnapshotV1BackendId =
    "ck3-1.19.0.6-native-zhongguo-b2-pip-snapshot-v1";
inline constexpr std::string_view kZhongguoB2PipSnapshotV1ConsumerId =
    "xar-autoplayer-zhongguo-b2-pip-snapshot-v1";
inline constexpr std::string_view kZhongguoB2PipSnapshotV1AllowlistId =
    "zg361-b2-pip-received-self-v1";

inline constexpr std::array<std::string_view, 73>
    kZhongguoB2PipSubjectVariableAllowlist{
        "zg361_b2_pip_gate_owner",
        "zg361_b2_pip_gate_subject",
        "zg361_b2_pip_gate_cycle",
        "zg361_b2_pip_gate_case",
        "zg361_b2_pip_gate_threshold",
        "zg361_b2_pip_gate_component_count",
        "zg361_b2_pip_gate_evidence_complete",
        "zg361_b2_pip_gate_status",
        "zg361_result_case_serial",
        "zg361_result_grade",
        "zg361_result_absolute_grade",
        "zg361_result_kpi_frozen",
        "zg361_result_evidence_governance",
        "zg361_result_evidence_capability",
        "zg361_result_evidence_growth",
        "zg361_result_evidence_superior",
        "zg361_result_evidence_values",
        "zg361_result_evidence_collaboration",
        "zg361_result_evidence_jingcha",
        "zg361_result_evidence_organization",
        "zg361_b2_pip_owner",
        "zg361_b2_pip_subject",
        "zg361_b2_pip_cycle",
        "zg361_b2_pip_case",
        "zg361_b2_pip_state",
        "zg361_b2_pip_task_kind",
        "zg361_b2_pip_task_controllable",
        "zg361_b2_pip_policy_route",
        "zg361_b2_m015_receipt_serial",
        "zg361_b2_pip_subject_response",
        "zg361_b2_pip_subject_response_case",
        "zg361_b2_pip_subject_response_author",
        "zg361_b2_pip_goal_revision_used",
        "zg361_b2_pip_refusal_receipt",
        "zg361_b2_pip_support_reserved",
        "zg361_b2_pip_support_absent",
        "zg361_b2_pip_support_hours",
        "zg361_b2_pip_support_attention",
        "zg361_b2_pip_support_mentor",
        "zg361_b2_pip_support_budget_owner",
        "zg361_b2_pip_support_budget_allocated",
        "zg361_b2_pip_support_budget_spent",
        "zg361_b2_m016_receipt_serial",
        "zg361_b2_pip_support_released",
        "zg361_b2_pip_support_withheld",
        "zg361_b2_pip_support_atomic_shortfall",
        "zg361_result_treasury_paid",
        "zg361_result_gold_paid",
        "zg361_b2_pip_midpoint_receipt",
        "zg361_b2_pip_midpoint_resource_delivery_valid",
        "zg361_b2_pip_midpoint_progress_status",
        "zg361_b2_pip_midpoint_progress_red_code",
        "zg361_b2_pip_midpoint_state",
        "zg361_b2_pip_outcome_code",
        "zg361_b2_pip_settlement_receipt",
        "zg361_b2_pip_outcome_result_cycle",
        "zg361_b2_pip_outcome_result_case",
        "zg361_b2_pip_outcome_result_grade",
        "zg361_b2_pip_stability_days_observed",
        "zg361_b2_pip_independent_review_status",
        "zg361_b2_pip_independent_review_red_code",
        "zg361_b2_pip_graduation_receipt",
        "zg361_b2_pip_failure_receipt",
        "zg361_b2_pip_no_support_liability",
        "zg361_b2_pip_performance_evidence_status",
        "zg361_b2_pip_performance_evidence_owner",
        "zg361_b2_pip_performance_evidence_subject",
        "zg361_b2_pip_performance_evidence_source_cycle",
        "zg361_b2_pip_performance_evidence_source_case",
        "zg361_b2_pip_performance_evidence_due_cycle",
        "zg361_b2_pip_performance_evidence_delta",
        "zg361_b2_pip_performance_evidence_consumed_cycle",
        "zg361_b2_pip_performance_evidence_consumed_case",
    };

inline constexpr std::array<std::string_view, 1>
    kZhongguoB2PipOwnerVariableAllowlist{
        "zg361_b2_pip_capacity_used",
    };

using ZhongguoB2PipNativeEnvironmentV1 = ZhongguoCaseNativeEnvironmentV1;
using ZhongguoB2PipAccessV1 = ZhongguoCaseAccessV1;
using ZhongguoB2PipRawVariableV1 = ZhongguoRawVariableV1;
using ZhongguoB2PipFrameV1 = game::ZhongguoCaseFrameV1;

struct ZhongguoB2PipSnapshotRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
  std::int32_t owner_character_id = -1;
  std::string request_nonce;
};

ZhongguoB2PipNativeEnvironmentV1 BindZhongguoB2PipNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

game::ReadZhongguoB2PipSnapshotResultV1 ReadZhongguoB2PipSnapshotV1(
    const ZhongguoB2PipNativeEnvironmentV1 &environment,
    const ZhongguoB2PipAccessV1 &access,
    const ZhongguoB2PipSnapshotRequestV1 &request,
    game::ZhongguoB2PipSnapshotV1 &output) noexcept;

std::string SerializeZhongguoB2PipSnapshotV1(
    const game::ZhongguoB2PipSnapshotV1 &snapshot);

} // namespace xar::ck3_11906
