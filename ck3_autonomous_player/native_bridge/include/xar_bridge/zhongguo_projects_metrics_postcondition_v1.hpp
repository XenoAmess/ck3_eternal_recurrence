#pragma once

#include "xar_bridge/zhongguo_case_snapshot_v1.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class ZhongguoProjectsMetricsPostconditionStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

struct ZhongguoProjectsMetricsIdentityV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;

  friend bool operator==(const ZhongguoProjectsMetricsIdentityV1 &,
                         const ZhongguoProjectsMetricsIdentityV1 &) = default;
};

struct ZhongguoProjectsContributionV1 {
  ZhongguoProjectsMetricsIdentityV1 identity;
  ZhongguoTypedIntegerV1 receipt_id;
  ZhongguoTypedIntegerV1 receipt_revision;
  ZhongguoTypedIntegerV1 value;

  friend bool operator==(const ZhongguoProjectsContributionV1 &,
                         const ZhongguoProjectsContributionV1 &) = default;
};

struct ZhongguoProjectsMetricsResultV1 {
  ZhongguoProjectsMetricsIdentityV1 identity;
  ZhongguoTypedIntegerV1 source_contribution_receipt_id;
  ZhongguoTypedIntegerV1 source_contribution_receipt_revision;
  ZhongguoTypedIntegerV1 metrics_revision;
  ZhongguoTypedStringV1 dictionary_key;

  friend bool operator==(const ZhongguoProjectsMetricsResultV1 &,
                         const ZhongguoProjectsMetricsResultV1 &) = default;
};

struct ZhongguoProjectsMetricsPostconditionReadinessV1 {
  bool player_subject_binding_ready = false;
  bool owner_binding_ready = false;
  bool source_identity_ready = false;
  bool result_identity_ready = false;
  bool contribution_ready = false;
  bool metrics_ready = false;
  bool same_project_case_identity = false;
  bool receipt_lineage_ready = false;
  bool result_operation_committed = false;
  bool same_frame_ready = false;
  bool ready = false;

  friend bool operator==(
      const ZhongguoProjectsMetricsPostconditionReadinessV1 &,
      const ZhongguoProjectsMetricsPostconditionReadinessV1 &) = default;
};

struct ZhongguoProjectsMetricsPostconditionV1 {
  ZhongguoProjectsMetricsPostconditionStatusV1 status =
      ZhongguoProjectsMetricsPostconditionStatusV1::unavailable;
  std::string case_kind;
  std::string request_nonce;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t player_character_id = -1;
  std::int32_t requested_owner_character_id = -1;
  std::string checkpoint_state;
  ZhongguoProjectsMetricsIdentityV1 source_identity;
  ZhongguoProjectsMetricsIdentityV1 result_identity;
  ZhongguoProjectsContributionV1 contribution;
  ZhongguoProjectsMetricsResultV1 metrics_result;
  ZhongguoProjectsMetricsPostconditionReadinessV1 readiness;
  std::string unavailable_reason;

  friend bool operator==(const ZhongguoProjectsMetricsPostconditionV1 &,
                         const ZhongguoProjectsMetricsPostconditionV1 &) =
      default;
};

enum class ReadZhongguoProjectsMetricsPostconditionResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view
    kZhongguoProjectsMetricsPostconditionV1Capability =
        "game.command.query-zhongguo-projects-metrics-postcondition-v1";
inline constexpr std::string_view kZhongguoProjectsMetricsPostconditionV1Step =
    "query-zhongguo-projects-metrics-postcondition-v1";
inline constexpr std::string_view
    kZhongguoProjectsMetricsPostconditionV1CaseKind =
        "zhongguo.projects-metrics.project-correlation";
inline constexpr std::string_view
    kZhongguoProjectsMetricsPostconditionV1BackendId =
        "ck3-1.19.0.6-native-zhongguo-projects-metrics-postcondition-v1";
inline constexpr std::string_view
    kZhongguoProjectsMetricsPostconditionV1ConsumerId =
        "xar-autoplayer-zhongguo-projects-metrics-postcondition-v1";
inline constexpr std::string_view
    kZhongguoProjectsMetricsPostconditionV1AllowlistId =
        "zg361-cp26-direct-p3m229-lineage-v2";

inline constexpr std::array<std::string_view, 40>
    kZhongguoProjectsMetricsPostconditionV1VariableAllowlist{
        "zg361_cp_m26_receipt_owner",
        "zg361_cp_m26_receipt_subject",
        "zg361_cp_m26_receipt_cycle",
        "zg361_cp_m26_receipt_case",
        "zg361_cp_m26_receipt_state",
        "zg361_cp_m26_receipt_choice",
        "zg361_cp_m26_contribution_receipt_id",
        "zg361_cp_m26_contribution_receipt_revision",
        "zg361_cp_m26_visible_value",
        "zg361_cp_m26_consumed_owner",
        "zg361_cp_m26_consumed_subject",
        "zg361_cp_m26_consumed_cycle",
        "zg361_cp_m26_consumed_case",
        "zg361_cp_m26_consumed_state",
        "zg361_cp_m26_visible_provenance_case",
        "zg361_p3_portfolio_cycle",
        "zg361_p3_project_source_ready",
        "zg361_p3_project_source_owner",
        "zg361_p3_project_source_subject",
        "zg361_p3_project_source_cycle",
        "zg361_p3_project_source_case",
        "zg361_p3_project_source_contribution_receipt_id",
        "zg361_p3_project_source_contribution_receipt_revision",
        "zg361_p3_project_source_contribution_value",
        "zg361_p3_m229_result_owner",
        "zg361_p3_m229_result_subject",
        "zg361_p3_m229_result_cycle",
        "zg361_p3_m229_result_case",
        "zg361_p3_m229_source_contribution_receipt_id",
        "zg361_p3_m229_source_contribution_receipt_revision",
        "zg361_p3_m229_metrics_revision",
        "zg361_p3_m229_dictionary_key_code",
        "zg361_p3_m229_consumed_owner",
        "zg361_p3_m229_consumed_subject",
        "zg361_p3_m229_consumed_cycle",
        "zg361_p3_m229_consumed_case",
        "zg361_p3_m229_consumed_state",
        "zg361_p3_m229_receipt_choice",
        "zg361_p3_m229_visible_value",
        "zg361_p3_m229_visible_provenance_case",
    };

using ZhongguoProjectsMetricsNativeEnvironmentV1 =
    ZhongguoCaseNativeEnvironmentV1;
using ZhongguoProjectsMetricsAccessV1 = ZhongguoCaseAccessV1;
using ZhongguoProjectsMetricsRawVariableV1 = ZhongguoRawVariableV1;
using ZhongguoProjectsMetricsFrameV1 = game::ZhongguoCaseFrameV1;

struct ZhongguoProjectsMetricsPostconditionRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
  std::int32_t owner_character_id = -1;
  std::string request_nonce;
};

ZhongguoProjectsMetricsNativeEnvironmentV1
BindZhongguoProjectsMetricsNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

game::ReadZhongguoProjectsMetricsPostconditionResultV1
ReadZhongguoProjectsMetricsPostconditionV1(
    const ZhongguoProjectsMetricsNativeEnvironmentV1 &environment,
    const ZhongguoProjectsMetricsAccessV1 &access,
    const ZhongguoProjectsMetricsPostconditionRequestV1 &request,
    game::ZhongguoProjectsMetricsPostconditionV1 &output) noexcept;

std::string SerializeZhongguoProjectsMetricsPostconditionV1(
    const game::ZhongguoProjectsMetricsPostconditionV1 &snapshot);

} // namespace xar::ck3_11906
