#pragma once

#include "xar_bridge/zhongguo_case_snapshot_v1.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

struct ZhongguoWorkforceOwnerCentralV1 {
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 stage11_status;
};

struct ZhongguoWorkforceOwnerSourceV1 {
  ZhongguoTypedIntegerV1 status;
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 p2c_cycle_serial;
  ZhongguoTypedIntegerV1 p2c_case_serial;
  ZhongguoTypedIntegerV1 al_cycle_serial;
  ZhongguoTypedIntegerV1 al_case_serial;
};

struct ZhongguoWorkforceOwnerAlCaseV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedBooleanV1 active;
  ZhongguoTypedIntegerV1 revision;
};

struct ZhongguoWorkforceOwnerM360ReceiptV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedIntegerV1 choice;
};

struct ZhongguoWorkforceOwnerPortfolioV1 {
  ZhongguoTypedBooleanV1 closed;
  ZhongguoTypedIntegerV1 status;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedBooleanV1 final_conservation_ok;
  ZhongguoTypedBooleanV1 terminal_history_accruing;
  ZhongguoTypedIntegerV1 history_cycle_count;
  ZhongguoTypedBooleanV1 terminal_success;
  ZhongguoTypedBooleanV1 terminal_na;
  ZhongguoTypedIntegerV1 terminal_reason;
  ZhongguoTypedIntegerV1 terminal_owned_operations;
  ZhongguoTypedIntegerV1 terminal_skipped_manager_only;
  ZhongguoTypedIntegerV1 terminal_skipped_charter;
};

struct ZhongguoWorkforceOwnerReadinessV1 {
  bool player_owner_binding_ready = false;
  bool portfolio_subject_binding_ready = false;
  bool case_identity_ready = false;
  bool same_frame_ready = false;
  bool ready = false;
};

enum class ZhongguoWorkforceOwnerStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

struct ZhongguoWorkforceOwnerSnapshotV1 {
  ZhongguoWorkforceOwnerStatusV1 status = ZhongguoWorkforceOwnerStatusV1::unavailable;
  std::string request_nonce;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t player_character_id = -1;
  std::int32_t subject_character_id = -1;
  ZhongguoWorkforceOwnerCentralV1 central;
  ZhongguoWorkforceOwnerSourceV1 source;
  ZhongguoWorkforceOwnerAlCaseV1 al_case;
  ZhongguoWorkforceOwnerM360ReceiptV1 m360_receipt;
  ZhongguoWorkforceOwnerPortfolioV1 portfolio;
  ZhongguoWorkforceOwnerReadinessV1 readiness;
  bool terminal = false;
  std::string terminal_kind = "none";
  std::string unavailable_reason;
};

enum class ReadZhongguoWorkforceOwnerResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kZhongguoWorkforceOwnerSnapshotV1Capability =
    "game.command.query-zhongguo-workforce-owner-snapshot-v1";
inline constexpr std::string_view kZhongguoWorkforceOwnerSnapshotV1Step =
    "query-zhongguo-workforce-owner-snapshot-v1";
inline constexpr std::string_view kZhongguoWorkforceOwnerSnapshotV1BackendId =
    "ck3-1.19.0.6-native-zhongguo-workforce-owner-snapshot-v1";

inline constexpr std::array<std::string_view, 11>
    kZhongguoWorkforceOwnerOwnerVariableAllowlist{
        "zg361_p2c_subject",
        "zg361_p2c_cycle",
        "zg361_p2c_case_serial",
        "zg361_p2c_stage_11_status",
        "zg361_p2c_m360_source_status",
        "zg361_p2c_m360_source_owner",
        "zg361_p2c_m360_source_subject",
        "zg361_p2c_m360_source_p2c_cycle",
        "zg361_p2c_m360_source_p2c_case",
        "zg361_p2c_m360_source_al_cycle",
        "zg361_p2c_m360_source_al_case",
    };

inline constexpr std::array<std::string_view, 25>
    kZhongguoWorkforceOwnerSubjectVariableAllowlist{
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
        "zg361_we_portfolio_closed",
        "zg361_we_portfolio_status",
        "zg361_we_portfolio_cycle",
        "zg361_we_final_conservation_ok",
        "zg361_we_portfolio_terminal_history_accruing",
        "zg361_we_portfolio_history_cycle_count",
        "zg361_we_portfolio_terminal_success",
        "zg361_we_portfolio_terminal_na",
        "zg361_we_portfolio_terminal_reason",
        "zg361_we_portfolio_terminal_owned_operations",
        "zg361_we_portfolio_terminal_skipped_manager_only",
        "zg361_we_portfolio_terminal_skipped_charter",
    };

using ZhongguoWorkforceOwnerNativeEnvironmentV1 = ZhongguoCaseNativeEnvironmentV1;
using ZhongguoWorkforceOwnerAccessV1 = ZhongguoCaseAccessV1;

struct ZhongguoWorkforceOwnerRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
  std::string request_nonce;
};

ZhongguoWorkforceOwnerNativeEnvironmentV1 BindZhongguoWorkforceOwnerNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;
game::ReadZhongguoWorkforceOwnerResultV1 ReadZhongguoWorkforceOwnerSnapshotV1(
    const ZhongguoWorkforceOwnerNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceOwnerAccessV1 &access,
    const ZhongguoWorkforceOwnerRequestV1 &request,
    game::ZhongguoWorkforceOwnerSnapshotV1 &output) noexcept;
std::string SerializeZhongguoWorkforceOwnerSnapshotV1(
    const game::ZhongguoWorkforceOwnerSnapshotV1 &snapshot);

} // namespace xar::ck3_11906
