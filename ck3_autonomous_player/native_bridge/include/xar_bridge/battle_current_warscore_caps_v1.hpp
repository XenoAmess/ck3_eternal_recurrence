#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::game {

// Current loaded native operands. They do not identify a winner or admit a row.
struct BattleControlCurrentWarscoreCapsV1 {
  std::int32_t source_combat_id = -1;
  std::int64_t war_attacker_winner_cap_raw_q100000 = 0;
  std::int64_t war_defender_winner_cap_raw_q100000 = 0;

  friend bool operator==(const BattleControlCurrentWarscoreCapsV1 &,
                         const BattleControlCurrentWarscoreCapsV1 &) = default;
};

} // namespace xar::game

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kBattleWarAttackerWinnerCap12003Rva = 0x5C69B60;
inline constexpr std::uintptr_t kBattleWarDefenderWinnerCap12003Rva = 0x5C69B58;

struct BattleCurrentWarscoreCapsBindings12003 {
  const std::int64_t *war_attacker_winner_cap = nullptr;
  const std::int64_t *war_defender_winner_cap = nullptr;
};

// Exact .3 only. No legacy binder offsets or native functions are used.
BattleCurrentWarscoreCapsBindings12003 BindBattleCurrentWarscoreCaps12003(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// Use the existing paused owner-thread ControlSample's strict actual Combat.
std::optional<game::BattleControlCurrentWarscoreCapsV1>
ReadBattleCurrentWarscoreCaps12003(
    const BattleCurrentWarscoreCapsBindings12003 &, const void *strict_combat,
    std::int32_t requested_full_combat_id) noexcept;

} // namespace xar::ck3_12002

namespace xar::bridge {

void AppendCurrentWarscoreCapsV1(
    std::string &,
    const std::optional<game::BattleControlCurrentWarscoreCapsV1> &);

} // namespace xar::bridge
