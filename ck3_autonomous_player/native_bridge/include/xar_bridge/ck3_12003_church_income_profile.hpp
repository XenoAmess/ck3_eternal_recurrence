#pragma once

#include "xar_bridge/ck3_12003.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12003::religion::church_income {

inline constexpr std::string_view kSchema = "ck3_12003_player_church_income_profile_v1";
inline constexpr std::uintptr_t kMonthlyIncomeRva = 0x2642320;

// Exact .3 numeric consumer shared by the current and maximum GUI getters.
// GUI callers pass false for the third argument and no optional breakdown.
using MonthlyIncome = std::int64_t *(*)(std::int64_t *, void *, bool, bool, void *);

struct Bindings {
  bool enabled = false;
  MonthlyIncome monthly_income = nullptr;
};

struct Terms {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0, played_character_id = -1;
  std::optional<std::int64_t> current_monthly_income_raw;
  std::optional<std::int64_t> maximum_monthly_income_raw;
  static constexpr std::int64_t raw_scale = 100'000;
};

Bindings BindPlayerChurchIncomeProfileImage12003(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// Existing owner callback resolves the actual played Character and frame.
// These are the receiver's final gold/month values, not its priest's account.
// The maximum is a native ceiling; no derived reward or action lives here.
bool ReadPlayerChurchIncomeProfile12003(const Bindings &, void *actual_played_character,
    std::int32_t played_character_id, std::int32_t date_raw,
    std::uint64_t capture_epoch, Terms &) noexcept;
std::string SerializePlayerChurchIncomeProfile12003(const Terms &);

} // namespace xar::ck3_12003::religion::church_income
