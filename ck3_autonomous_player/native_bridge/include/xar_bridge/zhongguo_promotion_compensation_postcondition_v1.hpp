#pragma once

#include "xar_bridge/zhongguo_case_snapshot_v1.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

struct ZhongguoPromotionCompensationIdentityV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 revision;

  friend bool operator==(const ZhongguoPromotionCompensationIdentityV1 &,
                         const ZhongguoPromotionCompensationIdentityV1 &) =
      default;
};

struct ZhongguoPromotionCompensationChoiceReceiptV1 {
  ZhongguoPromotionCompensationIdentityV1 identity;
  ZhongguoTypedIntegerV1 option_number;
  ZhongguoTypedIntegerV1 receipt_serial;
  ZhongguoTypedBooleanV1 active;
  ZhongguoTypedBooleanV1 consumed;
};

struct ZhongguoPromotionCompensationPostedReceiptV1 {
  ZhongguoPromotionCompensationIdentityV1 identity;
  ZhongguoTypedIntegerV1 operation_id;
  ZhongguoTypedIntegerV1 option_number;
  ZhongguoTypedIntegerV1 receipt_serial;
  ZhongguoTypedBooleanV1 active;
  ZhongguoTypedBooleanV1 consumed;
  ZhongguoTypedBooleanV1 posted;
};

struct ZhongguoPromotionCompensationReadinessV1 {
  bool player_owner_binding_ready = false;
  bool portfolio_subject_binding_ready = false;
  bool source_identity_ready = false;
  bool result_identity_ready = false;
  bool frozen_case_identity_ready = false;
  bool promotion_choice_receipt_ready = false;
  bool compensation_receipt_posted = false;
  bool same_case_identity_ready = false;
  bool revision_binding_ready = false;
  bool receipt_serials_ready = false;
  bool same_frame_ready = false;
  bool ready = false;
};

enum class ZhongguoPromotionCompensationStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

struct ZhongguoPromotionCompensationPostconditionV1 {
  ZhongguoPromotionCompensationStatusV1 status =
      ZhongguoPromotionCompensationStatusV1::unavailable;
  std::string request_nonce;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t player_character_id = -1;
  std::int32_t subject_character_id = -1;
  ZhongguoTypedIntegerV1 portfolio_domain;
  ZhongguoPromotionCompensationIdentityV1 source_identity;
  ZhongguoPromotionCompensationIdentityV1 result_identity;
  ZhongguoPromotionCompensationIdentityV1 frozen_case;
  ZhongguoPromotionCompensationChoiceReceiptV1 promotion_choice;
  ZhongguoPromotionCompensationPostedReceiptV1 compensation_receipt;
  ZhongguoPromotionCompensationReadinessV1 readiness;
  std::string unavailable_reason;
};

enum class ReadZhongguoPromotionCompensationResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view
    kZhongguoPromotionCompensationPostconditionV1Capability =
        "game.command.query-zhongguo-promotion-compensation-postcondition-v1";
inline constexpr std::string_view
    kZhongguoPromotionCompensationPostconditionV1Step =
        "query-zhongguo-promotion-compensation-postcondition-v1";
inline constexpr std::string_view
    kZhongguoPromotionCompensationPostconditionV1BackendId =
        "ck3-1.19.0.6-native-zhongguo-promotion-compensation-postcondition-v1";
inline constexpr std::string_view
    kZhongguoPromotionCompensationPostconditionV1AllowlistId =
        "zg361-promotion-compensation-postcondition-v1";

inline constexpr std::array<std::string_view, 7>
    kZhongguoPromotionCompensationOwnerVariableAllowlist{
        "zg361_comp_portfolio_domain",
        "zg361_comp_portfolio_subject",
        "zg361_comp_portfolio_result_owner",
        "zg361_comp_portfolio_result_subject",
        "zg361_comp_portfolio_result_cycle",
        "zg361_comp_portfolio_result_case",
        "zg361_comp_portfolio_result_snapshot_applied",
    };

inline constexpr std::array<std::string_view, 46>
    kZhongguoPromotionCompensationSubjectBaseVariableAllowlist{
        "zg361_pp_m147_receipt_active",
        "zg361_pp_m147_consumed",
        "zg361_pp_m147_receipt_owner",
        "zg361_pp_m147_receipt_subject",
        "zg361_pp_m147_receipt_cycle",
        "zg361_pp_m147_receipt_case",
        "zg361_pp_m147_receipt_route",
        "zg361_pp_m147_consumer_revision",
        "zg361_pp_m147_receipt_serial",
        "zg361_pp_m147_receipt_revision",
        "zg361_comp_promotion_receipt_active",
        "zg361_comp_promotion_receipt_posted",
        "zg361_comp_promotion_receipt_owner",
        "zg361_comp_promotion_receipt_subject",
        "zg361_comp_promotion_receipt_cycle",
        "zg361_comp_promotion_receipt_case",
        "zg361_comp_promotion_receipt_choice_serial",
        "zg361_comp_promotion_receipt_serial",
        "zg361_comp_promotion_receipt_choice_revision",
        "zg361_comp_promotion_receipt_revision",
        "zg361_comp_promotion_receipt_operation",
        "zg361_comp_promotion_receipt_route",
        "zg361_case_l_owner",
        "zg361_case_l_subject",
        "zg361_case_l_cycle_serial",
        "zg361_case_l_case_serial",
        "zg361_case_l_revision",
        "zg361_comp_l_last_operation",
        "zg361_comp_l_last_route",
        "zg361_case_l_active",
        "zg361_case_ae_owner",
        "zg361_case_ae_subject",
        "zg361_case_ae_cycle_serial",
        "zg361_case_ae_case_serial",
        "zg361_case_ae_revision",
        "zg361_comp_ae_last_operation",
        "zg361_comp_ae_last_route",
        "zg361_case_ae_active",
        "zg361_case_af_owner",
        "zg361_case_af_subject",
        "zg361_case_af_cycle_serial",
        "zg361_case_af_case_serial",
        "zg361_case_af_revision",
        "zg361_comp_af_last_operation",
        "zg361_comp_af_last_route",
        "zg361_case_af_active",
    };

inline constexpr std::array<std::int32_t, 33>
    kZhongguoPromotionCompensationMechanismAllowlist{
        82,  83,  84,  85,  86,  87,  88,  89,  90,  91,  278,
        279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289,
        290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300,
    };

using ZhongguoPromotionCompensationNativeEnvironmentV1 =
    ZhongguoCaseNativeEnvironmentV1;
using ZhongguoPromotionCompensationAccessV1 = ZhongguoCaseAccessV1;
using ZhongguoPromotionCompensationRawVariableV1 = ZhongguoRawVariableV1;
using ZhongguoPromotionCompensationFrameV1 = game::ZhongguoCaseFrameV1;

struct ZhongguoPromotionCompensationRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
  std::string request_nonce;
};

ZhongguoPromotionCompensationNativeEnvironmentV1
BindZhongguoPromotionCompensationNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

game::ReadZhongguoPromotionCompensationResultV1
ReadZhongguoPromotionCompensationPostconditionV1(
    const ZhongguoPromotionCompensationNativeEnvironmentV1 &environment,
    const ZhongguoPromotionCompensationAccessV1 &access,
    const ZhongguoPromotionCompensationRequestV1 &request,
    game::ZhongguoPromotionCompensationPostconditionV1 &output) noexcept;

std::string SerializeZhongguoPromotionCompensationPostconditionV1(
    const game::ZhongguoPromotionCompensationPostconditionV1 &snapshot);

} // namespace xar::ck3_11906
