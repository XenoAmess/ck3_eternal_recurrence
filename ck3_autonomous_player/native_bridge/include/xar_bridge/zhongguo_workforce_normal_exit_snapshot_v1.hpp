#pragma once

#include "xar_bridge/zhongguo_case_snapshot_v1.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class ZhongguoWorkforceNormalExitSnapshotStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

enum class ZhongguoWorkforceNormalExitLifecycleV1 : std::uint32_t {
  unavailable = 0,
  pre = 1,
  migrating = 2,
  sealed = 3,
  rehire_captured = 4,
};

struct ZhongguoWorkforceHcPartitionV1 {
  ZhongguoTypedIntegerV1 authorized;
  ZhongguoTypedIntegerV1 available;
  ZhongguoTypedIntegerV1 reserved;
  ZhongguoTypedIntegerV1 occupied;
  ZhongguoTypedIntegerV1 frozen;
  ZhongguoTypedIntegerV1 reclaimed;
  friend bool operator==(const ZhongguoWorkforceHcPartitionV1 &,
                         const ZhongguoWorkforceHcPartitionV1 &) = default;
};

struct ZhongguoWorkforceNormalExitSourceV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedIntegerV1 route;
  ZhongguoTypedIntegerV1 offer_gold;
  ZhongguoTypedIntegerV1 receipt_serial;
  ZhongguoTypedIntegerV1 object_owner_character_id;
  ZhongguoTypedIntegerV1 object_subject_character_id;
  ZhongguoTypedIntegerV1 object_cycle_serial;
  ZhongguoTypedIntegerV1 object_receipt_case_serial;
  ZhongguoTypedIntegerV1 object_route;
  ZhongguoTypedBooleanV1 object_active;
  ZhongguoTypedBooleanV1 object_consumed;
  ZhongguoTypedIntegerV1 consumer_receipt_case_serial;
  friend bool operator==(const ZhongguoWorkforceNormalExitSourceV1 &,
                         const ZhongguoWorkforceNormalExitSourceV1 &) = default;
};

struct ZhongguoWorkforceNormalExitWorkflowV1 {
  ZhongguoTypedBooleanV1 pending;
  ZhongguoTypedIntegerV1 pending_owner_character_id;
  ZhongguoTypedIntegerV1 pending_subject_character_id;
  ZhongguoTypedIntegerV1 pending_cycle_serial;
  ZhongguoTypedIntegerV1 pending_case_serial;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedBooleanV1 pending_hc_migration_authorized;
  ZhongguoWorkforceHcPartitionV1 pending_hc_before;
  ZhongguoTypedIntegerV1 pending_slot_case_serial;
  friend bool operator==(const ZhongguoWorkforceNormalExitWorkflowV1 &,
                         const ZhongguoWorkforceNormalExitWorkflowV1 &) = default;
};

struct ZhongguoWorkforceCurrentHcV1 {
  ZhongguoWorkforceHcPartitionV1 partition;
  ZhongguoTypedBooleanV1 formal_active;
  ZhongguoTypedIntegerV1 formal_case_serial;
  friend bool operator==(const ZhongguoWorkforceCurrentHcV1 &,
                         const ZhongguoWorkforceCurrentHcV1 &) = default;
};

struct ZhongguoWorkforceNormalExitReceiptV1 {
  ZhongguoTypedBooleanV1 active;
  ZhongguoTypedBooleanV1 sealed;
  ZhongguoTypedBooleanV1 published;
  ZhongguoTypedBooleanV1 consumed;
  ZhongguoTypedIntegerV1 consumed_operation;
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedIntegerV1 receipt_id;
  ZhongguoTypedIntegerV1 receipt_hash;
  ZhongguoTypedBooleanV1 hc_ledger_settled;
  ZhongguoTypedBooleanV1 hc_destination_frozen;
  ZhongguoTypedBooleanV1 hc_conservation_verified;
  ZhongguoWorkforceHcPartitionV1 hc_before;
  ZhongguoWorkforceHcPartitionV1 hc_after;
  ZhongguoTypedBooleanV1 formal_hc_active_before;
  ZhongguoTypedBooleanV1 formal_hc_active_after;
  ZhongguoTypedIntegerV1 formal_hc_case_serial;
  friend bool operator==(const ZhongguoWorkforceNormalExitReceiptV1 &,
                         const ZhongguoWorkforceNormalExitReceiptV1 &) = default;
};

struct ZhongguoWorkforceRehireExitV1 {
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 exit_owner_character_id;
  ZhongguoTypedIntegerV1 exit_cycle_serial;
  ZhongguoTypedIntegerV1 exit_case_serial;
  ZhongguoTypedIntegerV1 exit_state;
  ZhongguoTypedIntegerV1 exit_receipt_id;
  ZhongguoTypedIntegerV1 exit_receipt_hash;
  ZhongguoTypedBooleanV1 normal_exit_verified;
  ZhongguoWorkforceHcPartitionV1 exit_hc_before;
  ZhongguoWorkforceHcPartitionV1 exit_hc_after;
  ZhongguoTypedBooleanV1 exit_hc_destination_frozen;
  ZhongguoTypedBooleanV1 exit_hc_conservation_verified;
  ZhongguoTypedBooleanV1 exit_formal_hc_active_before;
  ZhongguoTypedBooleanV1 exit_formal_hc_active_after;
  ZhongguoTypedIntegerV1 exit_formal_hc_case_serial;
  friend bool operator==(const ZhongguoWorkforceRehireExitV1 &,
                         const ZhongguoWorkforceRehireExitV1 &) = default;
};

struct ZhongguoWorkforceNormalExitReadinessV1 {
  bool player_subject_binding_ready = false;
  bool owner_binding_ready = false;
  bool source_object_ready = false;
  bool pending_snapshot_ready = false;
  bool current_hc_partition_ready = false;
  bool migration_delta_ready = false;
  bool sealed_receipt_ready = false;
  bool rehire_capture_ready = false;
  bool current_hc_matches_stage_ready = false;
  bool lifecycle_ready = false;
  bool same_frame_ready = false;
  bool ready = false;
  friend bool operator==(const ZhongguoWorkforceNormalExitReadinessV1 &,
                         const ZhongguoWorkforceNormalExitReadinessV1 &) = default;
};

struct ZhongguoWorkforceNormalExitSnapshotV1 {
  ZhongguoWorkforceNormalExitSnapshotStatusV1 status =
      ZhongguoWorkforceNormalExitSnapshotStatusV1::unavailable;
  ZhongguoWorkforceNormalExitLifecycleV1 lifecycle =
      ZhongguoWorkforceNormalExitLifecycleV1::unavailable;
  std::string case_kind;
  std::string request_nonce;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t player_character_id = -1;
  std::int32_t subject_character_id = -1;
  std::int32_t requested_owner_character_id = -1;
  ZhongguoWorkforceNormalExitSourceV1 source;
  ZhongguoWorkforceNormalExitWorkflowV1 workflow;
  ZhongguoWorkforceCurrentHcV1 current_hc;
  ZhongguoWorkforceNormalExitReceiptV1 receipt;
  ZhongguoWorkforceRehireExitV1 rehire;
  ZhongguoWorkforceNormalExitReadinessV1 readiness;
  std::string unavailable_reason;
  friend bool operator==(const ZhongguoWorkforceNormalExitSnapshotV1 &,
                         const ZhongguoWorkforceNormalExitSnapshotV1 &) = default;
};

enum class ReadZhongguoWorkforceNormalExitSnapshotResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view
    kZhongguoWorkforceNormalExitSnapshotV1Capability =
        "game.command.query-zhongguo-workforce-normal-exit-snapshot-v1";
inline constexpr std::string_view kZhongguoWorkforceNormalExitSnapshotV1Step =
    "query-zhongguo-workforce-normal-exit-snapshot-v1";
inline constexpr std::string_view
    kZhongguoWorkforceNormalExitSnapshotV1CaseKind =
        "zhongguo.workforce.normal-exit.received-self";
inline constexpr std::string_view
    kZhongguoWorkforceNormalExitSnapshotV1BackendId =
        "ck3-1.19.0.6-native-zhongguo-workforce-normal-exit-snapshot-v1";
inline constexpr std::string_view
    kZhongguoWorkforceNormalExitSnapshotV1ConsumerId =
        "xar-autoplayer-zhongguo-workforce-normal-exit-snapshot-v1";
inline constexpr std::string_view
    kZhongguoWorkforceNormalExitSnapshotV1AllowlistId =
        "zg361-workforce-normal-exit-received-self-v1";

inline constexpr auto kZhongguoWorkforceNormalExitVariableAllowlist =
    std::to_array<std::string_view>({
        "zg361_b2_m075_owner",
        "zg361_b2_m075_subject",
        "zg361_b2_m075_cycle",
        "zg361_b2_m075_case",
        "zg361_b2_m075_state",
        "zg361_b2_m075_route",
        "zg361_b2_m075_offer_gold",
        "zg361_b2_m075_receipt_serial",
        "zg361_b2_m075_object_owner",
        "zg361_b2_m075_object_subject",
        "zg361_b2_m075_object_cycle",
        "zg361_b2_m075_object_receipt_case",
        "zg361_b2_m075_object_route",
        "zg361_b2_m075_object_active",
        "zg361_b2_m075_object_consumed",
        "zg361_b2_m075_consumer_receipt_case",
        "zg361_workforce_normal_exit_fact_pending",
        "zg361_workforce_normal_exit_fact_pending_owner",
        "zg361_workforce_normal_exit_fact_pending_subject",
        "zg361_workforce_normal_exit_fact_pending_cycle",
        "zg361_workforce_normal_exit_fact_pending_case",
        "zg361_workforce_normal_exit_fact_state",
        "zg361_workforce_normal_exit_fact_pending_hc_migration_authorized",
        "zg361_workforce_normal_exit_fact_pending_hc_authorized_before",
        "zg361_workforce_normal_exit_fact_pending_hc_available_before",
        "zg361_workforce_normal_exit_fact_pending_hc_reserved_before",
        "zg361_workforce_normal_exit_fact_pending_hc_occupied_before",
        "zg361_workforce_normal_exit_fact_pending_hc_frozen_before",
        "zg361_workforce_normal_exit_fact_pending_hc_reclaimed_before",
        "zg361_workforce_normal_exit_fact_pending_slot_case",
        "zg361_ch_hc_authorized",
        "zg361_ch_hc_available",
        "zg361_ch_hc_reserved",
        "zg361_ch_hc_occupied",
        "zg361_ch_hc_frozen",
        "zg361_ch_hc_reclaimed",
        "zg361_we_formal_hc_active",
        "zg361_we_formal_hc_active_case",
        "zg361_workforce_normal_exit_fact_receipt_active",
        "zg361_workforce_normal_exit_fact_receipt_sealed",
        "zg361_workforce_normal_exit_fact_receipt_published",
        "zg361_workforce_normal_exit_fact_receipt_consumed",
        "zg361_workforce_normal_exit_fact_receipt_consumed_operation",
        "zg361_workforce_normal_exit_fact_receipt_owner",
        "zg361_workforce_normal_exit_fact_receipt_subject",
        "zg361_workforce_normal_exit_fact_receipt_cycle",
        "zg361_workforce_normal_exit_fact_receipt_case",
        "zg361_workforce_normal_exit_fact_receipt_state",
        "zg361_workforce_normal_exit_fact_receipt_id",
        "zg361_workforce_normal_exit_fact_receipt_hash",
        "zg361_workforce_normal_exit_fact_receipt_hc_ledger_settled",
        "zg361_workforce_normal_exit_fact_receipt_hc_destination_frozen",
        "zg361_workforce_normal_exit_fact_receipt_hc_conservation_verified",
        "zg361_workforce_normal_exit_fact_receipt_hc_authorized_before",
        "zg361_workforce_normal_exit_fact_receipt_hc_available_before",
        "zg361_workforce_normal_exit_fact_receipt_hc_reserved_before",
        "zg361_workforce_normal_exit_fact_receipt_hc_occupied_before",
        "zg361_workforce_normal_exit_fact_receipt_hc_frozen_before",
        "zg361_workforce_normal_exit_fact_receipt_hc_reclaimed_before",
        "zg361_workforce_normal_exit_fact_receipt_hc_authorized_after",
        "zg361_workforce_normal_exit_fact_receipt_hc_available_after",
        "zg361_workforce_normal_exit_fact_receipt_hc_reserved_after",
        "zg361_workforce_normal_exit_fact_receipt_hc_occupied_after",
        "zg361_workforce_normal_exit_fact_receipt_hc_frozen_after",
        "zg361_workforce_normal_exit_fact_receipt_hc_reclaimed_after",
        "zg361_workforce_normal_exit_fact_receipt_formal_hc_active_before",
        "zg361_workforce_normal_exit_fact_receipt_formal_hc_active_after",
        "zg361_workforce_normal_exit_fact_receipt_formal_hc_case",
        "zg361_workforce_rehire_fact_state",
        "zg361_workforce_rehire_fact_subject",
        "zg361_workforce_rehire_fact_exit_owner",
        "zg361_workforce_rehire_fact_exit_cycle",
        "zg361_workforce_rehire_fact_exit_case",
        "zg361_workforce_rehire_fact_exit_state",
        "zg361_workforce_rehire_fact_exit_receipt_id",
        "zg361_workforce_rehire_fact_exit_receipt_hash",
        "zg361_workforce_rehire_fact_normal_exit_verified",
        "zg361_workforce_rehire_fact_exit_hc_authorized_before",
        "zg361_workforce_rehire_fact_exit_hc_available_before",
        "zg361_workforce_rehire_fact_exit_hc_reserved_before",
        "zg361_workforce_rehire_fact_exit_hc_occupied_before",
        "zg361_workforce_rehire_fact_exit_hc_frozen_before",
        "zg361_workforce_rehire_fact_exit_hc_reclaimed_before",
        "zg361_workforce_rehire_fact_exit_hc_authorized_after",
        "zg361_workforce_rehire_fact_exit_hc_available_after",
        "zg361_workforce_rehire_fact_exit_hc_reserved_after",
        "zg361_workforce_rehire_fact_exit_hc_occupied_after",
        "zg361_workforce_rehire_fact_exit_hc_frozen_after",
        "zg361_workforce_rehire_fact_exit_hc_reclaimed_after",
        "zg361_workforce_rehire_fact_exit_hc_destination_frozen",
        "zg361_workforce_rehire_fact_exit_hc_conservation_verified",
        "zg361_workforce_rehire_fact_exit_formal_hc_active_before",
        "zg361_workforce_rehire_fact_exit_formal_hc_active_after",
        "zg361_workforce_rehire_fact_exit_formal_hc_case",
    });
static_assert(kZhongguoWorkforceNormalExitVariableAllowlist.size() == 94);

using ZhongguoWorkforceNormalExitNativeEnvironmentV1 =
    ZhongguoCaseNativeEnvironmentV1;
using ZhongguoWorkforceNormalExitAccessV1 = ZhongguoCaseAccessV1;
using ZhongguoWorkforceNormalExitRawVariableV1 = ZhongguoRawVariableV1;
using ZhongguoWorkforceNormalExitFrameV1 = game::ZhongguoCaseFrameV1;

struct ZhongguoWorkforceNormalExitSnapshotRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
  std::int32_t owner_character_id = -1;
  std::string request_nonce;
};

ZhongguoWorkforceNormalExitNativeEnvironmentV1
BindZhongguoWorkforceNormalExitNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

game::ReadZhongguoWorkforceNormalExitSnapshotResultV1
ReadZhongguoWorkforceNormalExitSnapshotV1(
    const ZhongguoWorkforceNormalExitNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceNormalExitAccessV1 &access,
    const ZhongguoWorkforceNormalExitSnapshotRequestV1 &request,
    game::ZhongguoWorkforceNormalExitSnapshotV1 &output) noexcept;

std::string SerializeZhongguoWorkforceNormalExitSnapshotV1(
    const game::ZhongguoWorkforceNormalExitSnapshotV1 &snapshot);

} // namespace xar::ck3_11906
