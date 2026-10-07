// Root-only FIRST. Synthetic memory/callbacks do not represent a paused frame.
#include "xar_bridge/ck3_12004_phase_event_commander_chance_weights.hpp"
#include "xar_bridge/ck3_12004_phase_event_commander_side_identity.hpp"
#include "xar_bridge/combat_simulation_inputs_v2_wire.hpp"
#include "xar_bridge/phase_rite_parameters_v1_serializer.hpp"
#include <algorithm>
#include <cstring>
#include <fstream>
#include <iostream>
#include <map>
#include "phase-role-base-seed.inc"

namespace {
constexpr std::uintptr_t kImage = 0x140000000, kArmySlot = 0x160000000;
constexpr std::uintptr_t kArmyFallback = kArmySlot + 8, kCombatSlot = kArmySlot + 16, kCombatFallback = kArmySlot + 24;
constexpr std::uintptr_t kArmyStore = 0x170000000, kCombatStore = kArmyStore + 0x1000;
constexpr std::uintptr_t kArmyTable = 0x180000000, kCombatTable = 0x200000000;
constexpr std::uintptr_t kDatabase = 0x400000000, kRows = kDatabase + 0x1000;
constexpr std::int32_t kSideName = -1701;
const void *Pointer(std::uintptr_t value) { return reinterpret_cast<const void *>(value); }
std::uintptr_t Event(std::uint32_t index) { return kDatabase + 0x10000 + index * 0x1000; }
struct Memory {
  std::map<std::uintptr_t, std::vector<std::byte>> operands;
  bool reject_second_commander_row = false;
  template <class T> void Put(std::uintptr_t address, const T &value) {
    auto &bytes = operands[address]; bytes.resize(sizeof(value)); std::memcpy(bytes.data(), &value, sizeof(value));
  }
};
bool ReadBytes(std::uintptr_t address, void *out, std::size_t size, void *context) noexcept {
  const auto &memory = *static_cast<const Memory *>(context);
  if (memory.reject_second_commander_row && address == kRows + 16) return false;
  const auto found = memory.operands.find(address);
  if (found == memory.operands.end() || found->second.size() != size) return false;
  std::memcpy(out, found->second.data(), size); return true;
}
bool ReadArmy(void *context, const void *address, void *out, std::size_t size) noexcept {
  return ReadBytes(reinterpret_cast<std::uintptr_t>(address), out, size, context);
}
Memory MakeMemory(const xar::game::CombatSimulationInputsSnapshot &inputs, bool mismatched) {
  Memory memory;
  memory.Put(kImage + xar::ck3_12004::kPhaseRoleRegistryPointerSlotRva, kDatabase);
  memory.Put(kImage + 0x5D4BD6C, kSideName);
  memory.Put(kDatabase + 0x50, kRows); memory.Put(kDatabase + 0x5C, std::int32_t{6});
  const std::uint32_t roles[]{0, 1, 0, 0, 0, 0};
  for (std::uint32_t index = 0; index < 6; ++index) {
    memory.Put(kRows + index * 8, Event(index)); memory.Put(Event(index) + 0x1B0, roles[index]);
  }
  memory.Put(kArmySlot, Pointer(kArmyStore)); memory.Put(kCombatSlot, Pointer(kCombatStore));
  memory.Put(kArmyFallback, Pointer(0)); memory.Put(kCombatFallback, Pointer(0));
  memory.Put(kArmyStore + 0x20, Pointer(kArmyTable)); memory.Put(kCombatStore + 0x20, Pointer(kCombatTable));
  std::uint32_t capacity = 0;
  for (const auto &army : inputs.armies)
    capacity = std::max(capacity, (static_cast<std::uint32_t>(army.native_carmy_id) & 0xFFFFFFU) + 1);
  memory.Put(kArmyStore + 0x2C, capacity); memory.Put(kCombatStore + 0x2C, std::uint32_t{0x1000});
  for (std::size_t index = 0; index < inputs.armies.size(); ++index) {
    const auto &army = inputs.armies[index]; const auto army_id = static_cast<std::uint32_t>(army.native_carmy_id);
    const auto combat_id = std::uint32_t{0x87000321} + static_cast<std::uint32_t>(index);
    const auto physical = std::uintptr_t{0x300000000} + index * 0x10000, combat = physical + 0x1000;
    memory.Put(kArmyTable + (army_id & 0xFFFFFFU) * 16 + 8, Pointer(physical));
    memory.Put(physical + 0x10, army_id); memory.Put(physical + 0x128, combat_id);
    memory.Put(kCombatTable + (combat_id & 0xFFFFFFU) * 16 + 8, Pointer(combat));
    memory.Put(combat + 8, combat_id); memory.Put(combat + 0xC, std::uint32_t{0x436F6D62});
    const auto selected = army.encounter_role == "attacker" ? 1U : 0U;
    for (std::uint32_t side_index = 0; side_index < 2; ++side_index) {
      const auto side = combat + (side_index ? 0x368 : 0x20), data = physical + 0x3000 + side_index * 0x100;
      const std::int32_t count = side_index == selected ? 2 : 0;
      memory.Put(side + 0x10, Pointer(count ? data : 0));
      memory.Put(side + 0x18, static_cast<std::uint32_t>(count)); memory.Put(side + 0x1C, count);
      for (std::int32_t row = 0; row < count; ++row) memory.Put(data + static_cast<std::uintptr_t>(row) * 4, army_id);
      memory.Put(side + 0xB8, Pointer(combat));
      auto commander = static_cast<std::uint32_t>(army.commander.character_id);
      if (mismatched) commander ^= 0x01000000U;
      memory.Put(side + 0x74, commander);
    }
  }
  return memory;
}
struct ExpectedContext { std::uint32_t character, combat, side; };
struct Trace {
  std::vector<ExpectedContext> expected;
  std::uint32_t constructs = 0, saves = 0, trigger_evaluations = 0, chance_evaluations = 0, destroys = 0, faults = 0;
  bool no_admitted_rows = false;
  std::vector<std::uint32_t> chance_rows;
};
Trace *trace = nullptr;
template <class T> T Load(const void *p, std::size_t offset = 0) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(p) + offset, sizeof(value)); return value;
}
void *Construct(void *scope) { ++trace->constructs; std::memset(scope, 0, 0x168); return scope; }
void Destroy(void *) { ++trace->destroys; }
void Save(void *map, std::int32_t name, const xar::ck3_12004::PhaseCommanderSideToken12004 *token) {
  ++trace->saves;
  const auto *scope = static_cast<const std::byte *>(map) - 0x18;
  if (trace->expected.empty()) { ++trace->faults; return; }
  const auto ordinal = (trace->saves - 1) % trace->expected.size();
  const auto &expected = trace->expected[ordinal];
  const auto signed_combat = static_cast<std::int32_t>(expected.combat);
  const auto payload = static_cast<std::uint64_t>(static_cast<std::int64_t>(signed_combat));
  if (name != kSideName || Load<std::uint64_t>(scope) != 4 ||
      Load<std::uint64_t>(scope, 8) != expected.character || token->kind != 11 ||
      token->auxiliary != expected.side || token->reserved != 0 || token->payload != payload)
    ++trace->faults;
  std::memcpy(static_cast<std::byte *>(map) + 0x20, token, sizeof(*token));
}
bool EvaluateTrigger(const void *receiver, void *scope) {
  ++trace->trigger_evaluations;
  const auto address = reinterpret_cast<std::uintptr_t>(receiver);
  std::uint32_t index = 6;
  for (std::uint32_t row = 0; row < 6; ++row) if (address == Event(row) + 0x40) index = row;
  if (index >= 6 || index == 1 || Load<std::uint16_t>(scope, 0x38) != 11) ++trace->faults;
  return !trace->no_admitted_rows && index != 4;
}
std::int64_t *EvaluateChance(const void *receiver, std::int64_t *out, void *scope) {
  ++trace->chance_evaluations;
  const auto address = reinterpret_cast<std::uintptr_t>(receiver);
  std::uint32_t index = 6;
  for (std::uint32_t row = 0; row < 6; ++row) if (address == Event(row) + 0x110) index = row;
  trace->chance_rows.push_back(index);
  if (index >= 6 || index == 1 || index == 4 || Load<std::uint16_t>(scope, 0x38) != 11)
    ++trace->faults;
  constexpr std::int64_t raw[]{250001, 0, -199999, 99999, 0, 100000};
  *out = index < 6 ? raw[index] : 0;
  return out;
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 3) { std::cerr << "usage: commander-chance-whole-fixture bundle.json trace.json\n"; return 2; }
  const char *names[]{"signed_weights", "demanded_receiver_missing", "no_admitted_rows"};
  std::string bundle = "{\"schema_version\":1,\"scene_order\":[\"signed_weights\",\"demanded_receiver_missing\",\"no_admitted_rows\"],\"samples\":{";
  std::string receipt = "{\"schema\":\"commander-chance-native-callback-first-v1\",\"actual_paused_frame\":false,\"scenes\":[";
  bool qualified = true;
  for (int scene = 0; scene < 3; ++scene) {
    auto inputs = SeedPhaseRoleWholeV2Fixture(); auto memory = MakeMemory(inputs, false);
    const auto roles = xar::ck3_12004::BindPhaseEventRoleImage12004(
        kImage, xar::ck3_12004::kPhaseRoleExecutableSha256, ReadBytes, &memory);
    xar::ck3_12004::AttachPhaseEventRoleInputs12004(roles, inputs);
    xar::ck3_12003::CurrentArmyCombatRolesPhaseBindings12003 current;
    current.common.enabled = true; current.common.read_memory = ReadArmy; current.common.read_context = &memory;
    current.common.army_registry_slot = Pointer(kArmySlot); current.common.army_fallback_slot = Pointer(kArmyFallback);
    current.combat_registry_slot = Pointer(kCombatSlot); current.combat_fallback_slot = Pointer(kCombatFallback);
    xar::ck3_12004::AttachPhaseCommanderSideIdentity12004(
        xar::ck3_12004::BindPhaseCommanderSideIdentity12004(current, xar::ck3_12004::kPhaseRoleExecutableSha256), inputs);
    Trace observed;
    observed.no_admitted_rows = scene == 2;
    for (std::size_t index = 0; index < inputs.armies.size(); ++index) {
      const auto &army = inputs.armies[index];
      if (army.commander.status == xar::game::CombatObservationStatus::available && army.commander.character_id != -1)
        observed.expected.push_back({static_cast<std::uint32_t>(army.commander.character_id),
            std::uint32_t{0x87000321} + static_cast<std::uint32_t>(index), army.encounter_role == "attacker" ? 1U : 0U});
    }
    trace = &observed;
    auto bindings = xar::ck3_12004::BindPhaseCommanderTriggerImage12004(kImage, xar::ck3_12004::kPhaseRoleExecutableSha256, roles);
    bindings.root_construct = Construct; bindings.root_destroy = Destroy;
    bindings.named_scope_save = Save; bindings.evaluate_trigger = EvaluateTrigger;
    xar::ck3_12004::AttachPhaseCommanderTriggerConditions12004(bindings, inputs);
    // Preserve observed role/trigger facts; only the new demanded chance
    // receiver becomes unreadable in this scene, after those attachments.
    memory.reject_second_commander_row = scene == 1;
    auto chance = xar::ck3_12004::BindPhaseCommanderChanceImage12004(
        kImage, xar::ck3_12004::kPhaseRoleExecutableSha256, bindings);
    chance.evaluate_chance = EvaluateChance;
    xar::ck3_12004::AttachPhaseCommanderChanceWeights12004(chance, inputs);
    const auto commanders = static_cast<std::uint32_t>(observed.expected.size());
    const auto expected_scopes = commanders * (scene == 2 ? 1U : 2U);
    const auto expected_chance = commanders * (scene == 2 ? 0U : scene == 1 ? 3U : 4U);
    bool values_correct = inputs.phase_event_commander_chance_weights_v1.has_value();
    constexpr std::int64_t expected_raw[]{250001, 0, -199999, 99999, 0, 100000};
    constexpr std::int32_t expected_weight[]{2, 0, -1, 0, 0, 1};
    if (inputs.phase_event_commander_chance_weights_v1) {
      for (const auto &row : inputs.phase_event_commander_chance_weights_v1->occurrences) {
        values_correct = values_correct && row.conditions.size() == 6 &&
            row.chance_weight_observation_ready == (scene != 1);
        for (const auto &value : row.conditions) {
          const auto index = value.loaded_row_index;
          const bool evaluated = scene != 2 && index != 1 && index != 4 && !(scene == 1 && index == 2);
          if (evaluated) values_correct = values_correct && index < 6 &&
              value.chance_raw == expected_raw[index] && value.selection_weight_raw == expected_weight[index];
          else values_correct = values_correct && !value.chance_raw && !value.selection_weight_raw;
        }
      }
    }
    const bool success = values_correct && observed.faults == 0 && observed.constructs == expected_scopes &&
        observed.saves == expected_scopes && observed.destroys == expected_scopes &&
        observed.trigger_evaluations == commanders * 5 && observed.chance_evaluations == expected_chance;
    qualified = qualified && success;
    if (scene) { bundle += ','; receipt += ','; }
    xar::game::AppendPhaseRiteStringV1(bundle, names[scene]); bundle += ':';
    bundle += xar::bridge::SerializeCombatSimulationInputsV2(inputs);
    receipt += "{\"scene\":"; xar::game::AppendPhaseRiteStringV1(receipt, names[scene]);
    receipt += ",\"qualified\":"; receipt += success ? "true" : "false";
    receipt += ",\"constructs\":" + std::to_string(observed.constructs) + ",\"named_saves\":" + std::to_string(observed.saves);
    receipt += ",\"trigger_evaluations\":" + std::to_string(observed.trigger_evaluations);
    receipt += ",\"chance_evaluations\":" + std::to_string(observed.chance_evaluations) + ",\"destroys\":" + std::to_string(observed.destroys);
    receipt += ",\"faults\":" + std::to_string(observed.faults) + ",\"chance_rows\":[";
    for (std::size_t index = 0; index < observed.chance_rows.size(); ++index) {
      if (index) receipt += ','; receipt += std::to_string(observed.chance_rows[index]);
    }
    receipt += "]}";
  }
  std::ofstream output(argv[1], std::ios::binary); output << bundle << "}}\n";
  std::ofstream trace_output(argv[2], std::ios::binary); trace_output << receipt << "]}\n";
  if (!output || !trace_output) return 5;
  return qualified ? 0 : 6;
}
