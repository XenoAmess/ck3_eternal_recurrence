#pragma once

#include "xar_bridge/zhongguo_case_snapshot_v1.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

struct ZhongguoCompensationAf5IdentityV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
};

struct ZhongguoCompensationAf5ReceiptV1 {
  ZhongguoCompensationAf5IdentityV1 identity;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedBooleanV1 active;
  ZhongguoTypedBooleanV1 consumed;
  ZhongguoTypedIntegerV1 route;
};

struct ZhongguoCompensationAf5PortfolioV1 {
  ZhongguoTypedIntegerV1 domain;
  ZhongguoTypedIntegerV1 stage;
  ZhongguoTypedIntegerV1 completed_cycle;
  ZhongguoTypedBooleanV1 visible_pending;
  ZhongguoCompensationAf5IdentityV1 result_identity;
};

struct ZhongguoCompensationAf5CaseV1 {
  ZhongguoCompensationAf5IdentityV1 identity;
  ZhongguoTypedIntegerV1 revision;
  ZhongguoTypedIntegerV1 result_case_serial;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedBooleanV1 active;
  ZhongguoTypedIntegerV1 last_operation;
  ZhongguoTypedIntegerV1 last_route;
  ZhongguoTypedBooleanV1 repurchase_resolved;
  ZhongguoTypedBooleanV1 unit_conserved;
};

struct ZhongguoCompensationAf5ReadinessV1 {
  bool player_owner_binding_ready = false;
  bool portfolio_subject_binding_ready = false;
  bool same_case_identity_ready = false;
  bool same_frame_ready = false;
  bool ready = false;
};

enum class ZhongguoCompensationAf5StatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

struct ZhongguoCompensationAf5SnapshotV1 {
  ZhongguoCompensationAf5StatusV1 status =
      ZhongguoCompensationAf5StatusV1::unavailable;
  std::string request_nonce;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t player_character_id = -1;
  std::int32_t subject_character_id = -1;
  ZhongguoCompensationAf5PortfolioV1 portfolio;
  ZhongguoCompensationAf5CaseV1 af_case;
  ZhongguoCompensationAf5ReceiptV1 m299;
  ZhongguoCompensationAf5ReceiptV1 m300;
  ZhongguoCompensationAf5ReadinessV1 readiness;
  bool terminal = false;
  std::string unavailable_reason;
};

enum class ReadZhongguoCompensationAf5ResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kZhongguoCompensationAf5SnapshotV1Capability =
    "game.command.query-zhongguo-compensation-af5-snapshot-v1";
inline constexpr std::string_view kZhongguoCompensationAf5SnapshotV1Step =
    "query-zhongguo-compensation-af5-snapshot-v1";
inline constexpr std::string_view kZhongguoCompensationAf5SnapshotV1BackendId =
    "ck3-1.19.0.6-native-zhongguo-compensation-af5-snapshot-v1";

inline constexpr std::array<std::string_view, 9>
    kZhongguoCompensationAf5OwnerVariableAllowlist{
        "zg361_comp_portfolio_domain",
        "zg361_comp_portfolio_stage",
        "zg361_comp_portfolio_completed_cycle",
        "zg361_comp_portfolio_visible_pending",
        "zg361_comp_portfolio_result_owner",
        "zg361_comp_portfolio_result_subject",
        "zg361_comp_portfolio_result_cycle",
        "zg361_comp_portfolio_result_case",
        "zg361_comp_portfolio_subject",
    };
inline constexpr std::array<std::string_view, 28>
    kZhongguoCompensationAf5SubjectVariableAllowlist{
        "zg361_case_af_owner",
        "zg361_case_af_subject",
        "zg361_case_af_cycle_serial",
        "zg361_case_af_case_serial",
        "zg361_case_af_revision",
        "zg361_case_af_state",
        "zg361_case_af_active",
        "zg361_comp_af_last_operation",
        "zg361_comp_af_last_route",
        "zg361_comp_af_repurchase_resolved",
        "zg361_comp_af_unit_conserved",
        "zg361_comp_m299_receipt_owner",
        "zg361_comp_m299_receipt_subject",
        "zg361_comp_m299_receipt_cycle",
        "zg361_comp_m299_receipt_case",
        "zg361_comp_m299_receipt_state",
        "zg361_comp_m299_receipt_active",
        "zg361_comp_m299_consumed",
        "zg361_comp_m299_receipt_route",
        "zg361_comp_m300_receipt_owner",
        "zg361_comp_m300_receipt_subject",
        "zg361_comp_m300_receipt_cycle",
        "zg361_comp_m300_receipt_case",
        "zg361_comp_m300_receipt_state",
        "zg361_comp_m300_receipt_active",
        "zg361_comp_m300_consumed",
        "zg361_comp_m300_receipt_route",
        "zg361_comp_result_case",
    };

using ZhongguoCompensationAf5NativeEnvironmentV1 = ZhongguoCaseNativeEnvironmentV1;
using ZhongguoCompensationAf5AccessV1 = ZhongguoCaseAccessV1;

struct ZhongguoCompensationAf5RequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
  std::string request_nonce;
};

ZhongguoCompensationAf5NativeEnvironmentV1
BindZhongguoCompensationAf5NativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

game::ReadZhongguoCompensationAf5ResultV1 ReadZhongguoCompensationAf5SnapshotV1(
    const ZhongguoCompensationAf5NativeEnvironmentV1 &environment,
    const ZhongguoCompensationAf5AccessV1 &access,
    const ZhongguoCompensationAf5RequestV1 &request,
    game::ZhongguoCompensationAf5SnapshotV1 &output) noexcept;

std::string SerializeZhongguoCompensationAf5SnapshotV1(
    const game::ZhongguoCompensationAf5SnapshotV1 &snapshot);

} // namespace xar::ck3_11906
