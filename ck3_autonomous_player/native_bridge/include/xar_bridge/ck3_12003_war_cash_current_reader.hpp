#pragma once

#include "xar_bridge/ck3_12003.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12003::war_cash_current {

inline constexpr std::uintptr_t kMonthlyNetIncomeRva = 0x2BCA960;
inline constexpr std::uintptr_t kCurrentMaintenanceRva = 0x2C13F80;
inline constexpr std::uintptr_t kAllRaisedMaintenanceRva = 0x2C152D0;
inline constexpr std::int64_t kResourceScale = 100000;
inline constexpr std::size_t kGoldResourceSlot = 0;
inline constexpr std::size_t kTreasuryResourceSlot = 6;

using MonthlyNetIncome = std::int64_t *(*)(
    std::int64_t *output, void *character, void *optional_breakdown,
    void *evaluation_context);
using CurrentMaintenance = std::int64_t *(*)(
    std::int64_t *output, void *character, void *optional_breakdown);
using AllRaisedMaintenance = std::int64_t *(*)(
    std::int64_t *output, void *character);

struct Bindings {
  bool enabled = false;
  MonthlyNetIncome monthly_net_income = nullptr;
  CurrentMaintenance current_maintenance = nullptr;
  AllRaisedMaintenance all_raised_maintenance = nullptr;
};

struct MilitaryResources {
  bool available = false;
  std::array<std::int64_t, 10> resources_raw{};
  std::string unavailable_reason = "not_sampled";
};

struct ActorResources {
  // Personal stock GetGold balance; distinct from military resource slot 6.
  std::optional<std::int64_t> current_treasury_raw;
  // Independent native scalar, never derived from maintenance or save deltas.
  std::optional<std::int64_t> monthly_net_income_raw;
  MilitaryResources current;
  MilitaryResources all_raised;
  std::string treasury_unavailable_reason = "not_sampled";
  std::string income_unavailable_reason = "not_sampled";
  std::string unavailable_reason = "not_sampled";
};

// Exact .3 identity; the production path binds these actual native getters.
// The function pointers are also the focused production-reader fixture seam.
Bindings BindImage(std::uintptr_t image_base, std::string_view game_version,
                   std::string_view executable_sha256) noexcept;

// Called only by the existing paused owning-thread current-cash mailbox.
// Its caller supplies a real, generation-resolved played Character and owns
// the unchanged-frame envelope, date/revision, and active WarID/army-ID scope.
// Returns false for an unavailable binding/actor; individual unavailable
// values remain null. Legitimate zero and negative personal balances survive.
// Current and all-raised are alternative actor-global monthly totals.
bool ReadActor(const Bindings &, void *actual_played_character,
               std::int32_t actor_full_id, ActorResources &) noexcept;

} // namespace xar::ck3_12003::war_cash_current
