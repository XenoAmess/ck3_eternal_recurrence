// Root-only FIRST: real borrowed bindings/collector and integrated full V2 wire.
// Fake pointer storage is fixture data, never an actual paused/live capture.
#include "xar_bridge/ck3_12004_phase_event_commander_side_identity.hpp"
#include "xar_bridge/phase_rite_parameters_v1_serializer.hpp"
#include "xar_bridge/combat_simulation_inputs_v2_wire.hpp"
#include <algorithm>
#include <cstring>
#include <fstream>
#include <iostream>
#include <map>
#include "phase-role-base-seed.inc"

namespace {
constexpr std::uintptr_t kArmySlot = 0x160000000, kArmyFallbackSlot = kArmySlot + 8;
constexpr std::uintptr_t kCombatSlot = kArmySlot + 16, kCombatFallbackSlot = kArmySlot + 24;
constexpr std::uintptr_t kArmyStore = 0x170000000, kCombatStore = kArmyStore + 0x1000;
constexpr std::uintptr_t kArmyTable = 0x180000000, kCombatTable = 0x200000000;
const void *Pointer(std::uintptr_t address) { return reinterpret_cast<const void *>(address); }
struct Memory {
  std::map<std::uintptr_t, std::vector<std::byte>> operands;
  template <class T> void Put(std::uintptr_t address, const T &value) {
    auto &bytes = operands[address]; bytes.resize(sizeof(value));
    std::memcpy(bytes.data(), &value, sizeof(value));
  }
};
bool ReadMemory(void *context, const void *address, void *out, std::size_t size) noexcept {
  const auto &memory = *static_cast<const Memory *>(context);
  const auto found = memory.operands.find(reinterpret_cast<std::uintptr_t>(address));
  if (found == memory.operands.end() || found->second.size() != size) return false;
  std::memcpy(out, found->second.data(), size); return true;
}
Memory MakeMemory(const xar::game::CombatSimulationInputsSnapshot &inputs, int scene) {
  Memory memory;
  memory.Put(kArmySlot, Pointer(kArmyStore)); memory.Put(kCombatSlot, Pointer(kCombatStore));
  memory.Put(kArmyFallbackSlot, Pointer(0)); memory.Put(kCombatFallbackSlot, Pointer(0));
  memory.Put(kArmyStore + 0x20, Pointer(kArmyTable));
  memory.Put(kCombatStore + 0x20, Pointer(kCombatTable));
  std::uint32_t army_capacity = 0;
  for (const auto &army : inputs.armies)
    army_capacity = std::max(army_capacity, (static_cast<std::uint32_t>(army.native_carmy_id) & 0xFFFFFFU) + 1);
  memory.Put(kArmyStore + 0x2C, army_capacity);
  memory.Put(kCombatStore + 0x2C, std::uint32_t{0x1000});
  for (std::size_t index = 0; index < inputs.armies.size(); ++index) {
    const auto &army = inputs.armies[index];
    const auto army_id = static_cast<std::uint32_t>(army.native_carmy_id);
    const auto combat_id = std::uint32_t{0x07000321} + static_cast<std::uint32_t>(index);
    const auto physical = std::uintptr_t{0x300000000} + index * 0x10000;
    const auto combat = physical + 0x1000;
    memory.Put(kArmyTable + (army_id & 0xFFFFFFU) * 16 + 8, Pointer(physical));
    memory.Put(physical + 0x10, army_id); memory.Put(physical + 0x128, combat_id);
    memory.Put(kCombatTable + (combat_id & 0xFFFFFFU) * 16 + 8, Pointer(combat));
    memory.Put(combat + 8, combat_id); memory.Put(combat + 0xC, std::uint32_t{0x436F6D62});
    // Actual current orientation deliberately differs from hypothetical role.
    const auto selected = army.encounter_role == "attacker" ? 1U : 0U;
    for (std::uint32_t side_index = 0; side_index < 2; ++side_index) {
      const auto side = combat + (side_index ? 0x368 : 0x20);
      const auto data = physical + 0x3000 + side_index * 0x100;
      const std::int32_t count = side_index == selected ? 2 : (scene == 2 ? 1 : 0);
      memory.Put(side + 0x10, Pointer(count ? data : 0));
      memory.Put(side + 0x18, static_cast<std::uint32_t>(count)); memory.Put(side + 0x1C, count);
      for (std::int32_t row = 0; row < count; ++row) memory.Put(data + static_cast<std::uintptr_t>(row) * 4, army_id);
      memory.Put(side + 0xB8, Pointer(combat));
      auto commander = static_cast<std::uint32_t>(army.commander.character_id);
      if (scene == 1) commander ^= 0x01000000U;
      memory.Put(side + 0x74, commander);
    }
    // No owner70, owner unit/character, manager, phase or threshold operands.
  }
  return memory;
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) { std::cerr << "usage: commander-side-whole-fixture output.json\n"; return 2; }
  auto inputs = SeedPhaseRoleWholeV2Fixture();
  const char *names[] = {"matched", "different_generation", "ambiguous_side"};
  std::string bundle = "{\"schema_version\":1,\"scene_order\":[\"matched\",\"different_generation\",\"ambiguous_side\"],\"samples\":{";
  for (int scene = 0; scene < 3; ++scene) {
    auto memory = MakeMemory(inputs, scene);
    xar::ck3_12003::CurrentArmyCombatRolesPhaseBindings12003 roles;
    roles.common.enabled = true; roles.common.read_memory = ReadMemory; roles.common.read_context = &memory;
    roles.common.army_registry_slot = Pointer(kArmySlot); roles.common.army_fallback_slot = Pointer(kArmyFallbackSlot);
    roles.combat_registry_slot = Pointer(kCombatSlot); roles.combat_fallback_slot = Pointer(kCombatFallbackSlot);
    const auto bindings = xar::ck3_12004::BindPhaseCommanderSideIdentity12004(
        roles, xar::ck3_12004::kCommanderSideIdentityExecutableSha256);
    xar::ck3_12004::AttachPhaseCommanderSideIdentity12004(bindings, inputs);
    if (scene) bundle += ',';
    xar::game::AppendPhaseRiteStringV1(bundle, names[scene]); bundle += ':';
    bundle += xar::bridge::SerializeCombatSimulationInputsV2(inputs);
  }
  std::ofstream output(argv[1], std::ios::binary); output << bundle << "}}\n";
  return output ? 0 : 5;
}
