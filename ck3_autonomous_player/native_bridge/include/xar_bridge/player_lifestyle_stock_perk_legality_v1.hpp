#pragma once

#include "xar_bridge/player_lifestyle_window_candidates_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kStockPerkLegalityKeyV1 =
    "g2_player_lifestyle_stock_perk_legality_v1";
inline constexpr std::string_view kStockPerkLegalityExeSha256V1 =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view kStockPerkLegalityTargetV1 =
    "cutting_corners_perk";
inline constexpr std::string_view kStockPerkLegalityLifestyleV1 =
    "stewardship_lifestyle";

struct StockPerkLegalityFrameV1 {
  std::array<char, 64> episode_run_id{};
  std::array<char, 48> snapshot_id{};
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int32_t date_raw = 0;
  std::uint32_t played_character_id = 0xFFFFFFFFU;
  std::uintptr_t played_character = 0;
  bool paused = false;
  bool map_ready = false;
  bool played_character_alive = false;
  bool storage_round_trip = false;

  friend bool operator==(const StockPerkLegalityFrameV1 &,
                         const StockPerkLegalityFrameV1 &) = default;
};

struct StockPerkLegalityPlayerStateV1 {
  game::PlayerLifestyleWindowStableKeyV1 target_lifestyle_key{};
  std::int64_t target_xp_total_raw = -1;
  std::int64_t target_xp_within_level_raw = -1;
  std::int32_t target_xp_per_level = -1;
  std::int32_t unspent_perk_points = -1;
  std::int32_t used_perk_points = -1;
  bool owned_perk_state_known = false;
  bool target_perk_owned = false;

  friend bool operator==(const StockPerkLegalityPlayerStateV1 &,
                         const StockPerkLegalityPlayerStateV1 &) = default;
};

using StockPerkCaptureFrameV1 = bool (*)(void *,
                                         StockPerkLegalityFrameV1 &) noexcept;
using StockPerkReadMemoryV1 = bool (*)(void *, std::uintptr_t, void *,
                                       std::size_t) noexcept;
using StockPerkReadPlayerStateV1 = bool (*)(
    void *, const StockPerkLegalityFrameV1 &, std::uintptr_t target_lifestyle,
    StockPerkLegalityPlayerStateV1 &) noexcept;
using StockPerkProbeMainThreadV1 = bool (*)(void *) noexcept;
using StockPerkGetDatabaseV1 = void *(*)();
using StockPerkValidateCommandV1 = bool (*)(void *, void *);

struct StockPerkLegalityEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_exe_sha256{};
  std::uintptr_t module_base = 0;
  bool offline_fixture = false;
  StockPerkGetDatabaseV1 get_character_perk_database = nullptr;
  StockPerkValidateCommandV1 validate_perk_command = nullptr;
};

struct StockPerkLegalityAccessV1 {
  void *context = nullptr;
  StockPerkProbeMainThreadV1 is_application_main_thread = nullptr;
  StockPerkCaptureFrameV1 capture_frame = nullptr;
  StockPerkReadMemoryV1 read_memory = nullptr;
  StockPerkReadPlayerStateV1 read_player_state = nullptr;
};

enum class StockPerkLegalityStatusV1 : std::uint32_t {
  unavailable_exact_build = 0,
  unavailable_binding,
  unavailable_frame,
  unavailable_player,
  unavailable_database,
  unavailable_candidate,
  unavailable_state,
  unavailable_validator,
  unavailable_drift,
  observed_native_illegal,
  observed_native_legal,
};

struct StockPerkLegalityResultV1 {
  StockPerkLegalityStatusV1 status =
      StockPerkLegalityStatusV1::unavailable_binding;
  StockPerkLegalityFrameV1 frame{};
  game::PlayerLifestyleWindowStableKeyV1 target_key{};
  game::PlayerLifestyleWindowStableKeyV1 lifestyle_key{};
  std::int32_t observed_unspent_points = -1;
  std::int32_t observed_used_points = -1;
  std::int64_t observed_target_xp_total_raw = -1;
  std::int64_t observed_target_xp_within_level_raw = -1;
  std::int32_t observed_target_xp_per_level = -1;
  bool observed_target_owned = false;
  std::int32_t scanned_database_rows = -1;
  bool validator_invoked_twice = false;
  // Valid only for the captured application-main transaction. The private
  // formal wire may use it for one immediate revalidation/submit; it must
  // never be retained across another capture or published over JSON.
  std::uintptr_t target_definition = 0;
};

StockPerkLegalityEnvironmentV1 BindStockPerkLegalityEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_exe_sha256) noexcept;

// Private perk-only source. It evaluates a stock command twice, never submits
// it and never reads, opens or binds the lifestyle GUI window. Unknown input
// stays unavailable; only two matching exact native booleans are observations.
StockPerkLegalityResultV1 ReadStockPerkLegalityV1(
    const StockPerkLegalityEnvironmentV1 &environment,
    const StockPerkLegalityAccessV1 &access) noexcept;

std::string_view StockPerkLegalityStatusKeyV1(
    StockPerkLegalityStatusV1 status) noexcept;

} // namespace xar::ck3_11906
