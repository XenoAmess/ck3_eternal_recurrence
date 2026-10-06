#include "xar_bridge/battle_current_warscore_caps_v1.hpp"
#include "xar_bridge/ck3_12003.hpp"

#include <cstddef>
#include <cstring>

namespace xar::ck3_12002 {
namespace {

template <typename T>
T At(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset,
              sizeof(value));
  return value;
}

} // namespace

BattleCurrentWarscoreCapsBindings12003 BindBattleCurrentWarscoreCaps12003(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  if (image_base == 0 || executable_sha256 != ck3_12003::kExecutableSha256)
    return {};
  return {
      reinterpret_cast<const std::int64_t *>(
          image_base + kBattleWarAttackerWinnerCap12003Rva),
      reinterpret_cast<const std::int64_t *>(
          image_base + kBattleWarDefenderWinnerCap12003Rva)};
}

std::optional<game::BattleControlCurrentWarscoreCapsV1>
ReadBattleCurrentWarscoreCaps12003(
    const BattleCurrentWarscoreCapsBindings12003 &bindings,
    const void *strict_combat, std::int32_t requested_full_combat_id) noexcept {
  if (!bindings.war_attacker_winner_cap || !bindings.war_defender_winner_cap ||
      !strict_combat || requested_full_combat_id == -1)
    return std::nullopt;
  if (At<std::int32_t>(strict_combat, 0x08) != requested_full_combat_id ||
      At<std::uint32_t>(strict_combat, 0x0C) != 0x436F6D62U)
    return std::nullopt;
  return game::BattleControlCurrentWarscoreCapsV1{
      requested_full_combat_id,
      At<std::int64_t>(bindings.war_attacker_winner_cap, 0),
      At<std::int64_t>(bindings.war_defender_winner_cap, 0)};
}

} // namespace xar::ck3_12002

namespace xar::bridge {

void AppendCurrentWarscoreCapsV1(
    std::string &output,
    const std::optional<game::BattleControlCurrentWarscoreCapsV1> &value) {
  if (!value) {
    output += "null";
    return;
  }
  output += "{\"source_combat_id\":" +
            std::to_string(value->source_combat_id) +
            ",\"war_attacker_winner_cap_raw_q100000\":" +
            std::to_string(value->war_attacker_winner_cap_raw_q100000) +
            ",\"war_defender_winner_cap_raw_q100000\":" +
            std::to_string(value->war_defender_winner_cap_raw_q100000) + "}";
}

} // namespace xar::bridge
