#pragma once

#include "xar_bridge/zhongguo_case_snapshot_v1.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class ZhongguoWorkforceCollectiveSnapshotStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

enum class ZhongguoWorkforceCollectivePhaseV1 : std::uint32_t {
  unavailable = 0,
  not_reached = 1,
  route_a_exception = 2,
  route_b_forced = 3,
  route_c_debt = 4,
};

enum class ZhongguoWorkforceHistoryStatusV1 : std::uint32_t {
  unavailable = 0,
  empty = 1,
  partial = 2,
  three_cycle = 3,
};

enum class ZhongguoWorkforceCharterGateStatusV1 : std::uint32_t {
  unavailable = 0,
  not_eligible = 1,
  awaiting_gate = 2,
  ready = 3,
  consumed = 4,
};

struct ZhongguoWorkforceCaseV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedBooleanV1 active;
  ZhongguoTypedIntegerV1 revision;
};

struct ZhongguoWorkforceM360ReceiptV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedIntegerV1 choice;
};

struct ZhongguoWorkforceCollectiveV1 {
  ZhongguoWorkforceCollectivePhaseV1 phase =
      ZhongguoWorkforceCollectivePhaseV1::unavailable;
  ZhongguoTypedBooleanV1 submission_active;
  ZhongguoTypedBooleanV1 submission_sealed;
  ZhongguoTypedBooleanV1 submission_consumed;
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedIntegerV1 collective_case_serial;
  ZhongguoTypedIntegerV1 submitted_cycle_serial;
  ZhongguoTypedIntegerV1 cohort_count;
  ZhongguoTypedIntegerV1 settlement_id;
  ZhongguoTypedIntegerV1 settlement_hash;
  ZhongguoTypedBooleanV1 settled;
  ZhongguoTypedIntegerV1 route;
  ZhongguoTypedIntegerV1 total_members;
  ZhongguoTypedIntegerV1 total_quota;
  ZhongguoTypedIntegerV1 forced_count;
  ZhongguoTypedIntegerV1 exception_count;
  ZhongguoTypedIntegerV1 manager_cost_total;
};

struct ZhongguoWorkforceCohortV1 {
  ZhongguoTypedIntegerV1 cohort_id;
  ZhongguoTypedIntegerV1 manager_character_id;
  ZhongguoTypedIntegerV1 member_count;
  ZhongguoTypedIntegerV1 member_hash;
  ZhongguoTypedIntegerV1 quota;
  ZhongguoTypedIntegerV1 forced_count;
  ZhongguoTypedIntegerV1 exception_count;
  ZhongguoTypedIntegerV1 manager_cost;
  ZhongguoTypedBooleanV1 partition_verified;
  ZhongguoTypedBooleanV1 approval_verified;
  ZhongguoTypedIntegerV1 b1_cycle_serial;
  ZhongguoTypedIntegerV1 b1_case_serial;
  ZhongguoTypedIntegerV1 b1_source_id;
  ZhongguoTypedIntegerV1 b1_source_hash;
  ZhongguoTypedIntegerV1 mg_cycle_serial;
  ZhongguoTypedIntegerV1 mg_case_serial;
  ZhongguoTypedIntegerV1 mg_snapshot_source_serial;
  ZhongguoTypedIntegerV1 mg_snapshot_revision;
};

struct ZhongguoWorkforceDebtV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedBooleanV1 open;
  ZhongguoTypedBooleanV1 consumed;
  ZhongguoTypedIntegerV1 due_cycle_serial;
};

struct ZhongguoWorkforceHistorySlotV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 m357_receipt_id;
  ZhongguoTypedIntegerV1 m357_receipt_hash;
  ZhongguoTypedIntegerV1 m358_receipt_id;
  ZhongguoTypedIntegerV1 m358_receipt_hash;
  ZhongguoTypedIntegerV1 m359_receipt_id;
  ZhongguoTypedIntegerV1 m359_receipt_hash;
};

struct ZhongguoWorkforceHistoryV1 {
  ZhongguoWorkforceHistoryStatusV1 status =
      ZhongguoWorkforceHistoryStatusV1::unavailable;
  ZhongguoTypedIntegerV1 count;
  std::array<ZhongguoWorkforceHistorySlotV1, 3> slots{};
};

struct ZhongguoWorkforceCharterGateV1 {
  ZhongguoWorkforceCharterGateStatusV1 status =
      ZhongguoWorkforceCharterGateStatusV1::unavailable;
  ZhongguoTypedIntegerV1 evidence_count;
  ZhongguoTypedBooleanV1 evidence_ready;
  ZhongguoTypedBooleanV1 evidence_consumed;
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedIntegerV1 prepared_report_id;
  ZhongguoTypedIntegerV1 prepared_charter_id;
  ZhongguoTypedIntegerV1 previous_charter_id;
  ZhongguoTypedIntegerV1 previous_version;
  ZhongguoTypedIntegerV1 adopted_cycle_serial;
  ZhongguoTypedIntegerV1 effective_cycle_serial;
  ZhongguoTypedIntegerV1 portfolio_status;
  ZhongguoTypedBooleanV1 portfolio_closed;
  ZhongguoTypedBooleanV1 terminal_history_accruing;
  ZhongguoTypedIntegerV1 portfolio_history_cycle_count;
  ZhongguoTypedBooleanV1 terminal_success;
};

struct ZhongguoWorkforceCollectiveReadinessV1 {
  bool player_subject_binding_ready = false;
  bool owner_binding_ready = false;
  bool case_identity_ready = false;
  bool m360_receipt_projection_ready = false;
  bool collective_lifecycle_ready = false;
  bool cohort_identity_ready = false;
  bool cohort_conservation_ready = false;
  bool route_conservation_ready = false;
  bool history_ledger_ready = false;
  bool history_order_ready = false;
  bool three_cycle_ready = false;
  bool charter_gate_lifecycle_ready = false;
  bool same_frame_ready = false;
  bool ready = false;
};

struct ZhongguoWorkforceCollectiveSnapshotV1 {
  ZhongguoWorkforceCollectiveSnapshotStatusV1 status =
      ZhongguoWorkforceCollectiveSnapshotStatusV1::unavailable;
  std::string case_kind;
  std::string request_nonce;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t player_character_id = -1;
  std::int32_t subject_character_id = -1;
  std::int32_t requested_owner_character_id = -1;
  ZhongguoWorkforceCaseV1 al_case;
  ZhongguoWorkforceM360ReceiptV1 m360_receipt;
  ZhongguoWorkforceCollectiveV1 collective;
  std::array<ZhongguoWorkforceCohortV1, 3> cohorts{};
  ZhongguoWorkforceDebtV1 route_c_debt;
  ZhongguoWorkforceHistoryV1 history;
  ZhongguoWorkforceCharterGateV1 charter_gate;
  ZhongguoWorkforceCollectiveReadinessV1 readiness;
  std::string unavailable_reason;
};

enum class ReadZhongguoWorkforceCollectiveSnapshotResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view
    kZhongguoWorkforceCollectiveSnapshotV1Capability =
        "game.command.query-zhongguo-workforce-collective-snapshot-v1";
inline constexpr std::string_view
    kZhongguoWorkforceCollectiveSnapshotV1Step =
        "query-zhongguo-workforce-collective-snapshot-v1";
inline constexpr std::string_view
    kZhongguoWorkforceCollectiveSnapshotV1CaseKind =
        "zhongguo.workforce-collective";
inline constexpr std::string_view
    kZhongguoWorkforceCollectiveSnapshotV1BackendId =
        "ck3-1.19.0.6-native-zhongguo-workforce-collective-snapshot-v1";
inline constexpr std::string_view
    kZhongguoWorkforceCollectiveSnapshotV1ConsumerId =
        "xar-autoplayer-zhongguo-workforce-collective-snapshot-v1";
inline constexpr std::string_view
    kZhongguoWorkforceCollectiveSnapshotV1AllowlistId =
        "zg361-workforce-collective-received-self-v1";

inline constexpr auto kZhongguoWorkforceSubjectVariableAllowlist =
    std::to_array<std::string_view>({
        "zg361_case_al_owner",
        "zg361_case_al_subject",
        "zg361_case_al_cycle_serial",
        "zg361_case_al_case_serial",
        "zg361_case_al_state",
        "zg361_case_al_active",
        "zg361_case_al_revision",
        "zg361_we_m360_receipt_owner",
        "zg361_we_m360_receipt_subject",
        "zg361_we_m360_receipt_cycle",
        "zg361_we_m360_receipt_case",
        "zg361_we_m360_receipt_state",
        "zg361_we_m360_receipt_choice",
        "zg361_we_al_external_collective_submission_active",
        "zg361_we_al_external_collective_submission_sealed",
        "zg361_we_al_external_collective_submission_consumed",
        "zg361_we_al_external_collective_submission_owner",
        "zg361_we_al_external_collective_submission_subject",
        "zg361_we_al_external_collective_submission_cycle",
        "zg361_we_al_external_collective_submission_case",
        "zg361_we_al_external_collective_submission_state",
        "zg361_we_al_external_collective_case",
        "zg361_we_al_external_collective_submitted_cycle",
        "zg361_we_al_external_collective_cohort_count",
        "zg361_we_al_external_collective_settlement_id",
        "zg361_we_al_external_collective_settlement_hash",
        "zg361_we_al_external_collective_settled",
        "zg361_we_al_external_collective_route",
        "zg361_we_al_external_collective_total_members",
        "zg361_we_al_external_collective_total_quota",
        "zg361_we_al_external_collective_forced_count",
        "zg361_we_al_external_collective_exception_count",
        "zg361_we_al_external_collective_manager_cost_total",
        "zg361_we_al_external_collective_1_cohort_id",
        "zg361_we_al_external_collective_1_manager",
        "zg361_we_al_external_collective_1_member_count",
        "zg361_we_al_external_collective_1_member_hash",
        "zg361_we_al_external_collective_1_quota",
        "zg361_we_al_external_collective_1_forced_count",
        "zg361_we_al_external_collective_1_exception_count",
        "zg361_we_al_external_collective_1_manager_cost",
        "zg361_we_al_external_collective_1_partition_verified",
        "zg361_we_al_external_collective_1_approval_verified",
        "zg361_we_al_external_collective_1_b1_cycle",
        "zg361_we_al_external_collective_1_b1_case",
        "zg361_we_al_external_collective_1_b1_source_id",
        "zg361_we_al_external_collective_1_b1_source_hash",
        "zg361_we_al_external_collective_1_mg_cycle",
        "zg361_we_al_external_collective_1_mg_case",
        "zg361_we_al_external_collective_1_mg_snapshot_source_serial",
        "zg361_we_al_external_collective_1_mg_snapshot_revision",
        "zg361_we_al_external_collective_2_cohort_id",
        "zg361_we_al_external_collective_2_manager",
        "zg361_we_al_external_collective_2_member_count",
        "zg361_we_al_external_collective_2_member_hash",
        "zg361_we_al_external_collective_2_quota",
        "zg361_we_al_external_collective_2_forced_count",
        "zg361_we_al_external_collective_2_exception_count",
        "zg361_we_al_external_collective_2_manager_cost",
        "zg361_we_al_external_collective_2_partition_verified",
        "zg361_we_al_external_collective_2_approval_verified",
        "zg361_we_al_external_collective_2_b1_cycle",
        "zg361_we_al_external_collective_2_b1_case",
        "zg361_we_al_external_collective_2_b1_source_id",
        "zg361_we_al_external_collective_2_b1_source_hash",
        "zg361_we_al_external_collective_2_mg_cycle",
        "zg361_we_al_external_collective_2_mg_case",
        "zg361_we_al_external_collective_2_mg_snapshot_source_serial",
        "zg361_we_al_external_collective_2_mg_snapshot_revision",
        "zg361_we_al_external_collective_3_cohort_id",
        "zg361_we_al_external_collective_3_manager",
        "zg361_we_al_external_collective_3_member_count",
        "zg361_we_al_external_collective_3_member_hash",
        "zg361_we_al_external_collective_3_quota",
        "zg361_we_al_external_collective_3_forced_count",
        "zg361_we_al_external_collective_3_exception_count",
        "zg361_we_al_external_collective_3_manager_cost",
        "zg361_we_al_external_collective_3_partition_verified",
        "zg361_we_al_external_collective_3_approval_verified",
        "zg361_we_al_external_collective_3_b1_cycle",
        "zg361_we_al_external_collective_3_b1_case",
        "zg361_we_al_external_collective_3_b1_source_id",
        "zg361_we_al_external_collective_3_b1_source_hash",
        "zg361_we_al_external_collective_3_mg_cycle",
        "zg361_we_al_external_collective_3_mg_case",
        "zg361_we_al_external_collective_3_mg_snapshot_source_serial",
        "zg361_we_al_external_collective_3_mg_snapshot_revision",
        "zg361_we_m360_debt_owner",
        "zg361_we_m360_debt_subject",
        "zg361_we_m360_debt_cycle",
        "zg361_we_m360_debt_case",
        "zg361_we_m360_debt_state",
        "zg361_we_m360_debt_open",
        "zg361_we_m360_debt_consumed",
        "zg361_we_m360_debt_due_cycle",
        "zg361_we_m361_evidence_count",
        "zg361_we_m361_evidence_ready",
        "zg361_we_m361_evidence_consumed",
        "zg361_we_m361_evidence_owner",
        "zg361_we_m361_evidence_subject",
        "zg361_we_m361_evidence_cycle",
        "zg361_we_m361_evidence_case",
        "zg361_we_m361_evidence_state",
        "zg361_we_m361_prepared_report_id",
        "zg361_we_m361_prepared_charter_id",
        "zg361_we_m361_prepared_previous_charter_id",
        "zg361_we_m361_prepared_previous_version",
        "zg361_we_m361_prepared_adopted_cycle",
        "zg361_we_m361_prepared_effective_cycle",
        "zg361_we_m361_evidence_owner_1",
        "zg361_we_m361_evidence_subject_1",
        "zg361_we_m361_evidence_cycle_1",
        "zg361_we_m361_evidence_case_1",
        "zg361_we_m361_evidence_m357_receipt_id_1",
        "zg361_we_m361_evidence_m357_receipt_hash_1",
        "zg361_we_m361_evidence_m358_receipt_id_1",
        "zg361_we_m361_evidence_m358_receipt_hash_1",
        "zg361_we_m361_evidence_m359_receipt_id_1",
        "zg361_we_m361_evidence_m359_receipt_hash_1",
        "zg361_we_m361_evidence_owner_2",
        "zg361_we_m361_evidence_subject_2",
        "zg361_we_m361_evidence_cycle_2",
        "zg361_we_m361_evidence_case_2",
        "zg361_we_m361_evidence_m357_receipt_id_2",
        "zg361_we_m361_evidence_m357_receipt_hash_2",
        "zg361_we_m361_evidence_m358_receipt_id_2",
        "zg361_we_m361_evidence_m358_receipt_hash_2",
        "zg361_we_m361_evidence_m359_receipt_id_2",
        "zg361_we_m361_evidence_m359_receipt_hash_2",
        "zg361_we_m361_evidence_owner_3",
        "zg361_we_m361_evidence_subject_3",
        "zg361_we_m361_evidence_cycle_3",
        "zg361_we_m361_evidence_case_3",
        "zg361_we_m361_evidence_m357_receipt_id_3",
        "zg361_we_m361_evidence_m357_receipt_hash_3",
        "zg361_we_m361_evidence_m358_receipt_id_3",
        "zg361_we_m361_evidence_m358_receipt_hash_3",
        "zg361_we_m361_evidence_m359_receipt_id_3",
        "zg361_we_m361_evidence_m359_receipt_hash_3",
        "zg361_we_portfolio_status",
        "zg361_we_portfolio_closed",
        "zg361_we_portfolio_terminal_history_accruing",
        "zg361_we_portfolio_history_cycle_count",
        "zg361_we_portfolio_terminal_success",
    });

inline constexpr auto kZhongguoWorkforceOwnerVariableAllowlist =
    std::to_array<std::string_view>({
        "zg361_we_completed_cycle_ledger_count",
        "zg361_we_completed_cycle_ledger_owner_1",
        "zg361_we_completed_cycle_ledger_subject_1",
        "zg361_we_completed_cycle_ledger_cycle_1",
        "zg361_we_completed_cycle_ledger_case_1",
        "zg361_we_completed_cycle_ledger_m357_receipt_id_1",
        "zg361_we_completed_cycle_ledger_m357_receipt_hash_1",
        "zg361_we_completed_cycle_ledger_m358_receipt_id_1",
        "zg361_we_completed_cycle_ledger_m358_receipt_hash_1",
        "zg361_we_completed_cycle_ledger_m359_receipt_id_1",
        "zg361_we_completed_cycle_ledger_m359_receipt_hash_1",
        "zg361_we_completed_cycle_ledger_owner_2",
        "zg361_we_completed_cycle_ledger_subject_2",
        "zg361_we_completed_cycle_ledger_cycle_2",
        "zg361_we_completed_cycle_ledger_case_2",
        "zg361_we_completed_cycle_ledger_m357_receipt_id_2",
        "zg361_we_completed_cycle_ledger_m357_receipt_hash_2",
        "zg361_we_completed_cycle_ledger_m358_receipt_id_2",
        "zg361_we_completed_cycle_ledger_m358_receipt_hash_2",
        "zg361_we_completed_cycle_ledger_m359_receipt_id_2",
        "zg361_we_completed_cycle_ledger_m359_receipt_hash_2",
        "zg361_we_completed_cycle_ledger_owner_3",
        "zg361_we_completed_cycle_ledger_subject_3",
        "zg361_we_completed_cycle_ledger_cycle_3",
        "zg361_we_completed_cycle_ledger_case_3",
        "zg361_we_completed_cycle_ledger_m357_receipt_id_3",
        "zg361_we_completed_cycle_ledger_m357_receipt_hash_3",
        "zg361_we_completed_cycle_ledger_m358_receipt_id_3",
        "zg361_we_completed_cycle_ledger_m358_receipt_hash_3",
        "zg361_we_completed_cycle_ledger_m359_receipt_id_3",
        "zg361_we_completed_cycle_ledger_m359_receipt_hash_3",
    });

using ZhongguoWorkforceNativeEnvironmentV1 = ZhongguoCaseNativeEnvironmentV1;
using ZhongguoWorkforceAccessV1 = ZhongguoCaseAccessV1;
using ZhongguoWorkforceRawVariableV1 = ZhongguoRawVariableV1;
using ZhongguoWorkforceFrameV1 = game::ZhongguoCaseFrameV1;

struct ZhongguoWorkforceCollectiveSnapshotRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
  std::int32_t owner_character_id = -1;
  std::string request_nonce;
};

ZhongguoWorkforceNativeEnvironmentV1
BindZhongguoWorkforceNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

game::ReadZhongguoWorkforceCollectiveSnapshotResultV1
ReadZhongguoWorkforceCollectiveSnapshotV1(
    const ZhongguoWorkforceNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceAccessV1 &access,
    const ZhongguoWorkforceCollectiveSnapshotRequestV1 &request,
    game::ZhongguoWorkforceCollectiveSnapshotV1 &output) noexcept;

std::string SerializeZhongguoWorkforceCollectiveSnapshotV1(
    const game::ZhongguoWorkforceCollectiveSnapshotV1 &snapshot);

} // namespace xar::ck3_11906
