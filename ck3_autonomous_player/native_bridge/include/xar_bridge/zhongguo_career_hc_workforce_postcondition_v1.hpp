#pragma once

#include "xar_bridge/zhongguo_case_snapshot_v1.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class ZhongguoCareerHcWorkforcePostconditionStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

struct ZhongguoCareerHcWorkforceIdentityV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;

  friend bool operator==(const ZhongguoCareerHcWorkforceIdentityV1 &,
                         const ZhongguoCareerHcWorkforceIdentityV1 &) =
      default;
};

struct ZhongguoCareerHcWorkforceReceiptV1 {
  ZhongguoCareerHcWorkforceIdentityV1 identity;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedIntegerV1 choice;

  friend bool operator==(const ZhongguoCareerHcWorkforceReceiptV1 &,
                         const ZhongguoCareerHcWorkforceReceiptV1 &) =
      default;
};

struct ZhongguoCareerHcPartitionV1 {
  ZhongguoTypedIntegerV1 authorized;
  ZhongguoTypedIntegerV1 available;
  ZhongguoTypedIntegerV1 reserved;
  ZhongguoTypedIntegerV1 occupied;
  ZhongguoTypedIntegerV1 frozen;
  ZhongguoTypedIntegerV1 reclaimed;
  ZhongguoTypedBooleanV1 conserved;

  friend bool operator==(const ZhongguoCareerHcPartitionV1 &,
                         const ZhongguoCareerHcPartitionV1 &) = default;
};

struct ZhongguoCareerHcWorkforceRouteCostV1 {
  ZhongguoTypedIntegerV1 manager_cost_total;

  friend bool operator==(const ZhongguoCareerHcWorkforceRouteCostV1 &,
                         const ZhongguoCareerHcWorkforceRouteCostV1 &) =
      default;
};

struct ZhongguoCareerHcWorkforcePostconditionReadinessV1 {
  bool player_subject_binding_ready = false;
  bool owner_binding_ready = false;
  bool m360_identity_ready = false;
  bool m360_route_b_receipt_ready = false;
  bool career_hc_partition_ready = false;
  bool career_hc_conservation_ready = false;
  bool route_b_manager_cost_zero_ready = false;
  bool same_frame_ready = false;
  bool ready = false;

  friend bool operator==(
      const ZhongguoCareerHcWorkforcePostconditionReadinessV1 &,
      const ZhongguoCareerHcWorkforcePostconditionReadinessV1 &) = default;
};

struct ZhongguoCareerHcWorkforcePostconditionV1 {
  ZhongguoCareerHcWorkforcePostconditionStatusV1 status =
      ZhongguoCareerHcWorkforcePostconditionStatusV1::unavailable;
  std::string case_kind;
  std::string request_nonce;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t player_character_id = -1;
  std::int32_t subject_character_id = -1;
  std::int32_t requested_owner_character_id = -1;
  ZhongguoCareerHcWorkforceIdentityV1 m360_identity;
  ZhongguoCareerHcWorkforceReceiptV1 m360_receipt;
  ZhongguoCareerHcPartitionV1 career_hc_partition;
  ZhongguoCareerHcWorkforceRouteCostV1 route_b_cost;
  ZhongguoCareerHcWorkforcePostconditionReadinessV1 readiness;
  std::string unavailable_reason;

  friend bool operator==(const ZhongguoCareerHcWorkforcePostconditionV1 &,
                         const ZhongguoCareerHcWorkforcePostconditionV1 &) =
      default;
};

enum class ReadZhongguoCareerHcWorkforcePostconditionResultV1
    : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view
    kZhongguoCareerHcWorkforcePostconditionV1Capability =
        "game.command.query-zhongguo-career-hc-workforce-postcondition-v1";
inline constexpr std::string_view
    kZhongguoCareerHcWorkforcePostconditionV1Step =
        "query-zhongguo-career-hc-workforce-postcondition-v1";
inline constexpr std::string_view
    kZhongguoCareerHcWorkforcePostconditionV1CaseKind =
        "zhongguo.career-hc.workforce.route-b-no-hc-debit";
inline constexpr std::string_view
    kZhongguoCareerHcWorkforcePostconditionV1BackendId =
        "ck3-1.19.0.6-native-zhongguo-career-hc-workforce-postcondition-v1";
inline constexpr std::string_view
    kZhongguoCareerHcWorkforcePostconditionV1ConsumerId =
        "xar-autoplayer-zhongguo-career-hc-workforce-postcondition-v1";
inline constexpr std::string_view
    kZhongguoCareerHcWorkforcePostconditionV1AllowlistId =
        "zg361-m360-route-b-career-hc-ledger-v1";

inline constexpr std::array<std::string_view, 14>
    kZhongguoCareerHcWorkforcePostconditionV1VariableAllowlist{
        "zg361_we_m360_receipt_owner",
        "zg361_we_m360_receipt_subject",
        "zg361_we_m360_receipt_cycle",
        "zg361_we_m360_receipt_case",
        "zg361_we_m360_receipt_state",
        "zg361_we_m360_receipt_choice",
        "zg361_ch_hc_authorized",
        "zg361_ch_hc_available",
        "zg361_ch_hc_reserved",
        "zg361_ch_hc_occupied",
        "zg361_ch_hc_frozen",
        "zg361_ch_hc_reclaimed",
        "zg361_ch_hc_conserved",
        "zg361_we_al_external_collective_manager_cost_total",
    };

using ZhongguoCareerHcWorkforceNativeEnvironmentV1 =
    ZhongguoCaseNativeEnvironmentV1;
using ZhongguoCareerHcWorkforceAccessV1 = ZhongguoCaseAccessV1;
using ZhongguoCareerHcWorkforceRawVariableV1 = ZhongguoRawVariableV1;
using ZhongguoCareerHcWorkforceFrameV1 = game::ZhongguoCaseFrameV1;

struct ZhongguoCareerHcWorkforcePostconditionRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
  std::int32_t owner_character_id = -1;
  std::string request_nonce;
};

ZhongguoCareerHcWorkforceNativeEnvironmentV1
BindZhongguoCareerHcWorkforceNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

game::ReadZhongguoCareerHcWorkforcePostconditionResultV1
ReadZhongguoCareerHcWorkforcePostconditionV1(
    const ZhongguoCareerHcWorkforceNativeEnvironmentV1 &environment,
    const ZhongguoCareerHcWorkforceAccessV1 &access,
    const ZhongguoCareerHcWorkforcePostconditionRequestV1 &request,
    game::ZhongguoCareerHcWorkforcePostconditionV1 &output) noexcept;

std::string SerializeZhongguoCareerHcWorkforcePostconditionV1(
    const game::ZhongguoCareerHcWorkforcePostconditionV1 &snapshot);

} // namespace xar::ck3_11906
