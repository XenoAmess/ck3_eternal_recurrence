#pragma once

#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/phase_event_role_compatibility_v1.hpp"
#include <cstddef>
#include <cstring>
#include <string_view>
#include <utility>

namespace xar::ck3_12004 {
inline constexpr std::string_view kPhaseRoleExecutableSha256 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
// actual2653864: MOV rax,[RIP+036D4325], nextRIP265386B -> 5D27B90.
// Root selector343-getter11-first01 closes the loaded registry and role reads.
inline constexpr std::uintptr_t kPhaseRoleRegistryPointerSlotRva = 0x5D27B90;
using PhaseRoleReadBytesV1 = bool (*)(
    std::uintptr_t, void *, std::size_t, void *) noexcept;
inline bool ReadLocalPhaseRoleBytes12004(
    std::uintptr_t address, void *output, std::size_t size, void *) noexcept {
#if defined(_WIN32) && defined(_MSC_VER)
  __try {
    std::memcpy(output, reinterpret_cast<const void *>(address), size);
    return true;
  } __except (1) { return false; }
#else
  (void)address; (void)output; (void)size;
  return false;
#endif
}
struct PhaseEventRoleCompatibilityBindings12004 {
  bool enabled = false;
  std::uintptr_t registry_pointer_slot = 0;
  PhaseRoleReadBytesV1 read_bytes = nullptr;
  void *read_context = nullptr;
};
inline PhaseEventRoleCompatibilityBindings12004 BindPhaseEventRoleImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    PhaseRoleReadBytesV1 reader = ReadLocalPhaseRoleBytes12004,
    void *context = nullptr) noexcept {
  if (!image_base || executable_sha256 != kPhaseRoleExecutableSha256) return {};
  return {true, image_base + kPhaseRoleRegistryPointerSlotRva, reader, context};
}
inline game::PhaseEventRoleCompatibilityV1 ReadPhaseEventRoleInputs12004(
    const PhaseEventRoleCompatibilityBindings12004 &bindings,
    const game::CombatSimulationInputsSnapshot &inputs) {
  game::PhaseEventRoleCompatibilityV1 output;
  output.loaded_registry_source_closed = bindings.enabled;
  output.role_compare_source_closed = bindings.enabled;
  const auto add = [&](const game::CombatArmyInputsSnapshot &army,
                       std::int32_t character, std::optional<std::int32_t> regiment,
                       std::string_view role, std::uint32_t requested) {
    game::PhaseEventRoleOccurrenceV1 row;
    row.occurrence_index = static_cast<std::uint32_t>(output.occurrences.size());
    row.character_id = static_cast<std::uint32_t>(character);
    row.source_public_cunit_id = army.army_id;
    if (army.native_carmy_id_observable) row.source_native_carmy_id = army.native_carmy_id;
    row.source_regiment_id = regiment;
    row.encounter_role = army.encounter_role;
    row.phase_role = role;
    row.requested_role_raw = requested;
    // Only the actual21B Knight EDX=1 caller is closed. Commander role0 is
    // a conditional software input; its distinct old47B caller is not mapped.
    row.native_role_argument_source_closed = bindings.enabled && requested == 1;
    output.occurrences.push_back(std::move(row));
  };
  for (const auto &army : inputs.armies) {
    if (army.commander.status == game::CombatObservationStatus::available &&
        army.commander.character_id != -1)
      add(army, army.commander.character_id, std::nullopt, "commander", 0);
    for (const auto &knight : army.knights.members)
      if (knight.character_id != -1)
        add(army, knight.character_id, knight.source_regiment_id, "knight", 1);
  }
  auto &registry = output.loaded_registry;
  const auto unavailable = [&](std::string_view reason) {
    output.unavailable_reason = reason;
    registry.unavailable_reason = reason;
  };
  if (!bindings.enabled || !bindings.read_bytes) {
    unavailable("actual4_loaded_role_binding_unavailable"); return output;
  }
  const auto read = [&](std::uintptr_t address, auto &value) {
    return bindings.read_bytes(address, &value, sizeof(value), bindings.read_context);
  };
  std::uintptr_t database = 0;
  if (!read(bindings.registry_pointer_slot, database)) {
    unavailable("loaded_role_registry_pointer_read_unavailable"); return output;
  }
  if (!database) {
    unavailable("loaded_role_registry_not_initialized"); return output;
  }
  std::uintptr_t rows = 0;
  std::int32_t count = 0;
  const auto rows_read = read(database + 0x50, rows);
  if (read(database + 0x5C, count)) registry.count_raw = count;
  if (!registry.count_raw) {
    unavailable("loaded_role_row_count_read_unavailable"); return output;
  }
  if (count < 0) {
    output.status = registry.status = "partial";
    unavailable("observed_negative_loaded_role_row_count"); return output;
  }
  if (count && (!rows_read || !rows)) {
    output.status = registry.status = "partial";
    unavailable("loaded_role_row_array_read_unavailable"); return output;
  }
  bool complete = true;
  for (std::int32_t index = 0; index < count; ++index) {
    game::PhaseEventLoadedRoleRowV1 row;
    row.loaded_row_index = static_cast<std::uint32_t>(index);
    std::uintptr_t event = 0;
    std::uint32_t role = 0;
    if (!read(rows + static_cast<std::uintptr_t>(index) * 8, event))
      row.unavailable_reason = "loaded_event_row_pointer_read_unavailable";
    else if (!event)
      row.unavailable_reason = "loaded_event_row_pointer_null";
    else if (!read(event + 0x1B0, role))
      row.unavailable_reason = "loaded_event_role_operand_read_unavailable";
    else {
      row.role_operand_raw = role;
      row.status = "available";
    }
    if (!row.role_operand_raw) complete = false;
    registry.rows.push_back(std::move(row));
  }
  for (auto &occurrence : output.occurrences) {
    for (const auto &row : registry.rows) {
      game::PhaseEventRoleConditionV1 condition;
      condition.loaded_row_index = row.loaded_row_index;
      if (row.role_operand_raw)
        condition.role_compatible = *row.role_operand_raw == occurrence.requested_role_raw;
      else condition.unavailable_reason = row.unavailable_reason;
      occurrence.conditions.push_back(std::move(condition));
    }
  }
  output.status = registry.status = complete ? "available" : "partial";
  if (complete) output.unavailable_reason.clear();
  else unavailable("loaded_event_role_operand_partial");
  return output;
}
// Root integrates this optional leaf into the existing available V2 branch.
// Its status does not change the base query, full-phase fidelity or MC readiness.
inline void AttachPhaseEventRoleInputs12004(
    const PhaseEventRoleCompatibilityBindings12004 &bindings,
    game::CombatSimulationInputsSnapshot &inputs) noexcept {
  if (!bindings.enabled) return;
  try {
    inputs.phase_event_role_compatibility_v1 = ReadPhaseEventRoleInputs12004(bindings, inputs);
  } catch (...) { inputs.phase_event_role_compatibility_v1.reset(); }
}
} // namespace xar::ck3_12004
