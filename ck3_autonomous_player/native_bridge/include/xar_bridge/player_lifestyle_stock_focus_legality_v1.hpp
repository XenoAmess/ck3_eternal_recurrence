#pragma once

#include "xar_bridge/player_lifestyle_stock_perk_legality_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kStockFocusLegalityKeyV1 =
    "g2_player_lifestyle_stock_focus_legality_v1";
inline constexpr std::string_view kStockFocusLegalityExeSha256V1 =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view kStockFocusLegalityTargetV1 =
    "stewardship_wealth_focus";
inline constexpr std::string_view kStockFocusLegalityLifestyleV1 =
    "stewardship_lifestyle";

using StockFocusLegalityFrameV1 = StockPerkLegalityFrameV1;
using StockFocusValidateCommandV1 = bool (*)(void *, void *);

struct StockFocusLegalityEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_exe_sha256{};
  std::uintptr_t module_base = 0;
  bool offline_fixture = false;
  StockFocusValidateCommandV1 validate_focus_command = nullptr;
};

// Values returned by exact native getters for the target focus's lifestyle.
// A missing XP map row is not synthesized as zero by this contract.
struct StockFocusTargetProgressV1 {
  bool available = false;
  std::int64_t xp_total_raw = -1;
  std::int64_t xp_within_level_raw = -1;
  std::int32_t xp_per_level = -1;
  std::int32_t unspent_perk_points = -1;
  std::int32_t used_perk_points = -1;

  friend bool operator==(const StockFocusTargetProgressV1 &,
                         const StockFocusTargetProgressV1 &) = default;
};

using StockFocusCaptureTargetProgressV1 = bool (*)(
    void *context, const StockFocusLegalityFrameV1 &frame,
    std::uintptr_t target_lifestyle,
    StockFocusTargetProgressV1 &output) noexcept;

struct StockFocusLegalityAccessV1 {
  void *context = nullptr;
  StockPerkProbeMainThreadV1 is_application_main_thread = nullptr;
  StockPerkCaptureFrameV1 capture_frame = nullptr;
  StockPerkReadMemoryV1 read_memory = nullptr;
  StockFocusCaptureTargetProgressV1 capture_target_progress = nullptr;
};

enum class StockFocusLegalityStatusV1 : std::uint32_t {
  unavailable_exact_build = 0,
  unavailable_binding,
  unavailable_frame,
  unavailable_player,
  unavailable_database,
  unavailable_candidate,
  unavailable_validator,
  unavailable_drift,
  observed_native_illegal,
  observed_native_legal,
};

struct StockFocusLegalityResultV1 {
  StockFocusLegalityStatusV1 status =
      StockFocusLegalityStatusV1::unavailable_binding;
  StockFocusLegalityFrameV1 frame{};
  game::PlayerLifestyleWindowStableKeyV1 target_key{};
  game::PlayerLifestyleWindowStableKeyV1 lifestyle_key{};
  std::int32_t scanned_database_rows = -1;
  bool validator_invoked_twice = false;
  StockFocusTargetProgressV1 target_progress{};
  // Transaction-local only: never publish a native pointer over JSON or keep
  // it across a later paused-frame capture.
  std::uintptr_t target_definition = 0;
};

StockFocusLegalityEnvironmentV1 BindStockFocusLegalityEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_exe_sha256) noexcept;

// Private fixed-key read only. Does not bind/open the lifestyle window,
// submit a command, or treat an unavailable source as native false.
StockFocusLegalityResultV1 ReadStockFocusLegalityV1(
    const StockFocusLegalityEnvironmentV1 &environment,
    const StockFocusLegalityAccessV1 &access) noexcept;

std::string_view StockFocusLegalityStatusKeyV1(
    StockFocusLegalityStatusV1 status) noexcept;

} // namespace xar::ck3_11906
