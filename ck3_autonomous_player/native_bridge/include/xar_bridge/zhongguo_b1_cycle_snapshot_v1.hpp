#pragma once

#include "xar_bridge/zhongguo_case_snapshot_v1.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class ZhongguoB1CycleSnapshotStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

struct ZhongguoB1CycleIdentityV1 {
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedIntegerV1 open_year;
  ZhongguoTypedIntegerV1 runtime_schema;
  ZhongguoTypedBooleanV1 active;
};

struct ZhongguoB1CycleRosterV1 {
  ZhongguoTypedIntegerV1 subject_count;
  ZhongguoTypedIntegerV1 before_prune_count;
  ZhongguoTypedIntegerV1 pruned_count;
  ZhongguoTypedIntegerV1 amendment_count;
  ZhongguoTypedIntegerV1 audit_version;
  ZhongguoTypedBooleanV1 reopen_required;
};

struct ZhongguoB1CycleProcessingV1 {
  ZhongguoTypedIntegerV1 count;
  ZhongguoTypedIntegerV1 agenda_count;
  ZhongguoTypedIntegerV1 local_candidate_count;
  ZhongguoTypedIntegerV1 pre_calibration_valid_count;
};

struct ZhongguoB1CycleQuotaV1 {
  ZhongguoTypedIntegerV1 rebuild_generation;
  ZhongguoTypedIntegerV1 built_case_serial;
  ZhongguoTypedIntegerV1 book_version;
  ZhongguoTypedIntegerV1 target_top;
  ZhongguoTypedIntegerV1 target_middle;
  ZhongguoTypedIntegerV1 target_bottom;
  ZhongguoTypedIntegerV1 recount_top;
  ZhongguoTypedIntegerV1 recount_middle;
  ZhongguoTypedIntegerV1 recount_bottom;
  ZhongguoTypedIntegerV1 pre_calibration_expected_count;
  ZhongguoTypedBooleanV1 pre_calibration_mismatch;
  ZhongguoTypedBooleanV1 pool_membership;
};

struct ZhongguoB1CycleClosureV1 {
  ZhongguoTypedBooleanV1 calibration_finalized;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedBooleanV1 rewards_issued;
  ZhongguoTypedBooleanV1 publication_blocked;
};

struct ZhongguoB1CyclePendingV1 {
  ZhongguoTypedIntegerV1 open_count;
  ZhongguoTypedIntegerV1 slot_used;
  ZhongguoTypedIntegerV1 reward_expected_count;
  ZhongguoTypedIntegerV1 rewards_paid_count;
  ZhongguoTypedBooleanV1 rewards_committed;
  ZhongguoTypedIntegerV1 watchdog_cancelled_count;
  ZhongguoTypedIntegerV1 watchdog_orphan_count;
};

struct ZhongguoB1CycleReadinessV1 {
  bool manager_binding_ready = false;
  bool cycle_identity_ready = false;
  bool roster_ready = false;
  bool processing_ready = false;
  bool quota_ready = false;
  bool closure_ready = false;
  bool pending_ready = false;
  bool same_frame_ready = false;
  bool ready = false;
};

struct ZhongguoB1CycleSnapshotV1 {
  ZhongguoB1CycleSnapshotStatusV1 status =
      ZhongguoB1CycleSnapshotStatusV1::unavailable;
  std::string case_kind;
  std::string request_nonce;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t player_character_id = -1;
  std::int32_t manager_character_id = -1;
  ZhongguoB1CycleIdentityV1 cycle;
  ZhongguoB1CycleRosterV1 roster;
  ZhongguoB1CycleProcessingV1 processing;
  ZhongguoB1CycleQuotaV1 quota;
  ZhongguoB1CycleClosureV1 closure;
  ZhongguoB1CyclePendingV1 pending;
  ZhongguoB1CycleReadinessV1 readiness;
  std::string unavailable_reason;
};

enum class ReadZhongguoB1CycleSnapshotResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kZhongguoB1CycleSnapshotV1Capability =
    "game.command.query-zhongguo-b1-cycle-snapshot-v1";
inline constexpr std::string_view kZhongguoB1CycleSnapshotV1Step =
    "query-zhongguo-b1-cycle-snapshot-v1";
inline constexpr std::string_view kZhongguoB1CycleSnapshotV1CaseKind =
    "zhongguo.b1.cycle";
inline constexpr std::string_view kZhongguoB1CycleSnapshotV1BackendId =
    "ck3-1.19.0.6-native-zhongguo-b1-cycle-snapshot-v1";
inline constexpr std::string_view kZhongguoB1CycleSnapshotV1ConsumerId =
    "xar-autoplayer-zhongguo-b1-cycle-snapshot-v1";
inline constexpr std::string_view kZhongguoB1CycleSnapshotV1AllowlistId =
    "zg361-b1-cycle-manager-v1";

inline constexpr auto kZhongguoB1CycleSnapshotV1VariableAllowlist =
    std::to_array<std::string_view>({
        "zg361_b1_manager_cycle_serial",
        "zg361_b1_manager_case_serial",
        "zg361_b1_cycle_state",
        "zg361_b1_cycle_open_year",
        "zg361_b1_cycle_runtime_schema",
        "zg361_b1_subject_n",
        "zg361_b1_roster_before_prune_n",
        "zg361_b1_roster_pruned_n",
        "zg361_b1_roster_amendment_n",
        "zg361_b1_roster_audit_version",
        "zg361_b1_roster_reopen_required",
        "zg361_b1_processing_n",
        "zg361_b1_agenda_n",
        "zg361_b1_local_candidate_n",
        "zg361_b1_pre_calibration_valid_n",
        "zg361_b1_quota_rebuild_generation",
        "zg361_b1_quota_built_serial",
        "zg361_b1_quota_book_version",
        "zg361_pending_375_n",
        "zg361_pending_35_n",
        "zg361_pending_325_n",
        "zg361_b1_quota_recount_top",
        "zg361_b1_quota_recount_middle",
        "zg361_b1_quota_recount_bottom",
        "zg361_b1_pre_calibration_expected_n",
        "zg361_b1_pre_calibration_quota_mismatch",
        "zg361_b1_quota_pool_membership",
        "zg361_b1_calibration_finalized",
        "zg361_b1_closure_state",
        "zg361_b1_rewards_issued",
        "zg361_b1_publication_blocked",
        "zg361_b1_pending_open_n",
        "zg361_b1_pending_slot_used",
        "zg361_b1_pending_reward_expected_n",
        "zg361_b1_pending_rewards_paid_n",
        "zg361_b1_pending_rewards_committed",
        "zg361_b1_pending_watchdog_cancelled_n",
        "zg361_b1_pending_watchdog_orphan_n",
    });
static_assert(kZhongguoB1CycleSnapshotV1VariableAllowlist.size() == 38);

using ZhongguoB1CycleNativeEnvironmentV1 = ZhongguoCaseNativeEnvironmentV1;
using ZhongguoB1CycleAccessV1 = ZhongguoCaseAccessV1;

struct ZhongguoB1CycleSnapshotRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
  std::string request_nonce;
};

ZhongguoB1CycleNativeEnvironmentV1 BindZhongguoB1CycleNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;
game::ReadZhongguoB1CycleSnapshotResultV1 ReadZhongguoB1CycleSnapshotV1(
    const ZhongguoB1CycleNativeEnvironmentV1 &environment,
    const ZhongguoB1CycleAccessV1 &access,
    const ZhongguoB1CycleSnapshotRequestV1 &request,
    game::ZhongguoB1CycleSnapshotV1 &output) noexcept;
std::string SerializeZhongguoB1CycleSnapshotV1(
    const game::ZhongguoB1CycleSnapshotV1 &snapshot);

} // namespace xar::ck3_11906
