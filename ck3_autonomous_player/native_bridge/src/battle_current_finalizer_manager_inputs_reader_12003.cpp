#include "xar_bridge/battle_current_finalizer_manager_inputs_reader_12003.hpp"
#include "xar_bridge/ck3_12002_battle.hpp"
#include "xar_bridge/ck3_12003.hpp"

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

void EnableBattleCurrentFinalizerManagerInputs12003(
    BattleBindings &bindings, std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept {
  bindings.current_finalizer_manager_secondary_vtable =
      bindings.enabled && image_base != 0 &&
              executable_sha256 == ck3_12003::kExecutableSha256
          ? image_base + kBattleFinalizerManagerSecondaryVtable12003Rva
          : 0;
}

std::optional<game::BattleControlCurrentFinalizerManagerInputsV1>
ReadCurrentFinalizerManagerInputs12003(
    const BattleBindings &bindings, const void *strict_actual_combat,
    std::int32_t requested_full_combat_id) noexcept {
  if (!bindings.enabled ||
      bindings.current_finalizer_manager_secondary_vtable == 0 ||
      !bindings.game_state_slot || !*bindings.game_state_slot ||
      !strict_actual_combat || requested_full_combat_id == -1)
    return std::nullopt;

  if (At<std::int32_t>(strict_actual_combat, 0x08) != requested_full_combat_id ||
      At<std::uint32_t>(strict_actual_combat, 0x0C) != 0x436F6D62U)
    return std::nullopt;

  const auto *domain = At<const void *>(
      *bindings.game_state_slot,
      kBattleFinalizerManagerGameStateDomain12003Offset);
  if (!domain)
    return std::nullopt;
  const auto *manager = static_cast<const std::byte *>(domain) +
                        kBattleFinalizerManagerDomain12003Offset;
  if (At<std::uintptr_t>(manager, 0x08) !=
      bindings.current_finalizer_manager_secondary_vtable)
    return std::nullopt;

  const auto *combat_ids = At<const void *>(manager, 0x28);
  const auto capacity = At<std::int32_t>(manager, 0x30);
  const auto count = At<std::int32_t>(manager, 0x34);
  if (count < 0 || capacity < count || (count != 0 && !combat_ids))
    return std::nullopt;

  bool listed = false;
  for (std::int32_t index = 0; index < count; ++index) {
    if (At<std::int32_t>(combat_ids, static_cast<std::size_t>(index) * 4) ==
        requested_full_combat_id)
      listed = true;
  }

  const auto raw = At<std::uint8_t>(manager, 0x60);
  return game::BattleControlCurrentFinalizerManagerInputsV1{
      requested_full_combat_id, listed, raw, raw != 0};
}

} // namespace xar::ck3_12002
