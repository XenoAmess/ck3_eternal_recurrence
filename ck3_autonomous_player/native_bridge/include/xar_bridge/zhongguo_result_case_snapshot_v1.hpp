#pragma once

#include "xar_bridge/zhongguo_case_snapshot_v1.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class ZhongguoResultCaseSnapshotStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

struct ZhongguoResultCaseIdentityV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedIntegerV1 grade;

  friend bool operator==(const ZhongguoResultCaseIdentityV1 &,
                         const ZhongguoResultCaseIdentityV1 &) = default;
};

struct ZhongguoResultNoticeV1 {
  ZhongguoTypedIntegerV1 absolute_grade;
  // Exact Jomini fixed-point payload.  Consumers must retain the Q100000
  // scale instead of rounding or converting it to a binary float.
  ZhongguoTypedIntegerV1 kpi_frozen_q100000;
  ZhongguoTypedIntegerV1 rank_frozen;
  ZhongguoTypedIntegerV1 cohort_n_frozen;

  friend bool operator==(const ZhongguoResultNoticeV1 &,
                         const ZhongguoResultNoticeV1 &) = default;
};

struct ZhongguoResultDeliveryV1 {
  ZhongguoTypedIntegerV1 method;
  ZhongguoTypedBooleanV1 objection_recorded;
  ZhongguoTypedIntegerV1 settlement_posted_serial;
  ZhongguoTypedBooleanV1 appeal_open;

  friend bool operator==(const ZhongguoResultDeliveryV1 &,
                         const ZhongguoResultDeliveryV1 &) = default;
};

struct ZhongguoResultCaseReadinessV1 {
  bool player_subject_binding_ready = false;
  bool owner_binding_ready = false;
  bool case_identity_ready = false;
  bool notice_facts_ready = false;
  bool delivery_state_ready = false;
  bool same_frame_ready = false;
  bool ready = false;

  friend bool operator==(const ZhongguoResultCaseReadinessV1 &,
                         const ZhongguoResultCaseReadinessV1 &) = default;
};

struct ZhongguoResultCaseSnapshotV1 {
  ZhongguoResultCaseSnapshotStatusV1 status =
      ZhongguoResultCaseSnapshotStatusV1::unavailable;
  std::string case_kind;
  std::string request_nonce;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t player_character_id = -1;
  std::int32_t subject_character_id = -1;
  std::int32_t requested_owner_character_id = -1;
  ZhongguoResultCaseIdentityV1 case_identity;
  ZhongguoResultNoticeV1 notice;
  ZhongguoResultDeliveryV1 delivery;
  ZhongguoResultCaseReadinessV1 readiness;
  std::string unavailable_reason;

  friend bool operator==(const ZhongguoResultCaseSnapshotV1 &,
                         const ZhongguoResultCaseSnapshotV1 &) = default;
};

enum class ReadZhongguoResultCaseSnapshotResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kZhongguoResultCaseSnapshotV1Capability =
    "game.command.query-zhongguo-result-case-snapshot-v1";
inline constexpr std::string_view kZhongguoResultCaseSnapshotV1Step =
    "query-zhongguo-result-case-snapshot-v1";
inline constexpr std::string_view kZhongguoResultCaseSnapshotV1CaseKind =
    "zhongguo.result.received-self";
inline constexpr std::string_view kZhongguoResultCaseSnapshotV1BackendId =
    "ck3-1.19.0.6-native-zhongguo-result-case-snapshot-v1";
inline constexpr std::string_view kZhongguoResultCaseSnapshotV1ConsumerId =
    "xar-autoplayer-zhongguo-result-case-snapshot-v1";
inline constexpr std::string_view kZhongguoResultCaseSnapshotV1AllowlistId =
    "zg361-result-received-self-v1";

inline constexpr std::array<std::string_view, 13>
    kZhongguoResultCaseSnapshotV1VariableAllowlist{
        "zg361_result_case_owner",
        "zg361_result_cycle_serial",
        "zg361_result_case_serial",
        "zg361_result_case_state",
        "zg361_result_grade",
        "zg361_result_absolute_grade",
        "zg361_result_kpi_frozen",
        "zg361_result_rank_frozen",
        "zg361_result_cohort_n_frozen",
        "zg361_result_delivery_method",
        "zg361_result_objection_recorded",
        "zg361_result_settlement_posted_serial",
        "zg361_result_appeal_open",
    };

// The result provider shares only the frozen low-level CK3 variable ABI and
// application-main access shape with the B1 provider.  Its request ACL,
// allowlist and semantic reader are independent.
using ZhongguoResultNativeEnvironmentV1 = ZhongguoCaseNativeEnvironmentV1;
using ZhongguoResultAccessV1 = ZhongguoCaseAccessV1;
using ZhongguoResultRawVariableV1 = ZhongguoRawVariableV1;
using ZhongguoResultFrameV1 = game::ZhongguoCaseFrameV1;

struct ZhongguoResultCaseSnapshotRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
  std::int32_t owner_character_id = -1;
  std::string request_nonce;
};

ZhongguoResultNativeEnvironmentV1 BindZhongguoResultNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

game::ReadZhongguoResultCaseSnapshotResultV1
ReadZhongguoResultCaseSnapshotV1(
    const ZhongguoResultNativeEnvironmentV1 &environment,
    const ZhongguoResultAccessV1 &access,
    const ZhongguoResultCaseSnapshotRequestV1 &request,
    game::ZhongguoResultCaseSnapshotV1 &output) noexcept;

std::string SerializeZhongguoResultCaseSnapshotV1(
    const game::ZhongguoResultCaseSnapshotV1 &snapshot);

} // namespace xar::ck3_11906
