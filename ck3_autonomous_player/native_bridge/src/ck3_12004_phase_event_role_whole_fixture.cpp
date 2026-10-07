// Root-only FIRST of the integrated production V2 serializer and service.
// Fake loaded-registry memory is fixture evidence, never paused/live values.
#include "xar_bridge/ck3_12004_phase_event_role_compatibility.hpp"
#include "xar_bridge/phase_event_role_compatibility_v1_serializer.hpp"
#include "xar_bridge/combat_simulation_inputs_v2_wire.hpp"
#include <array>
#include <fstream>
#include <iostream>
#include "phase-role-base-seed.inc"

namespace {
constexpr std::uintptr_t kImageBase = 0x140000000;
constexpr std::uintptr_t kDatabase = 0x170000000;
constexpr std::uintptr_t kRows = 0x180000000;
constexpr std::array<std::uintptr_t, 4> kEvents{
    0x190000000, 0x190001000, 0x190002000, 0x190003000};
struct OperandMemory {
  std::array<std::uint32_t, 4> roles{0, 1, 7, 1};
  bool singleton_present = true;
  bool row2_readable = true;
};
bool ReadOperandMemory(std::uintptr_t address, void *out, std::size_t size,
                       void *context) noexcept {
  const auto &memory = *static_cast<const OperandMemory *>(context);
  const auto copy = [&](const auto &value) {
    if (size != sizeof(value)) return false;
    std::memcpy(out, &value, size); return true;
  };
  if (address == kImageBase + xar::ck3_12004::kPhaseRoleRegistryPointerSlotRva)
    return copy(memory.singleton_present ? kDatabase : std::uintptr_t{0});
  if (address == kDatabase + 0x50) return copy(kRows);
  if (address == kDatabase + 0x5C) return copy(std::int32_t{4});
  for (std::size_t index = 0; index < kEvents.size(); ++index) {
    if (address == kRows + index * 8) return copy(kEvents[index]);
    if (address == kEvents[index] + 0x1B0) {
      if (index == 2 && !memory.row2_readable) return false;
      return copy(memory.roles[index]);
    }
  }
  return false;
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "usage: role-whole-fixture output.json\n"; return 2;
  }
  auto inputs = SeedPhaseRoleWholeV2Fixture();
  const char *names[] = {"available", "partial", "unavailable"};
  std::string bundle = "{\"schema_version\":1,\"scene_order\":[\"available\",\"partial\",\"unavailable\"],\"samples\":{";
  OperandMemory memory;
  for (int scene = 0; scene < 3; ++scene) {
    memory.row2_readable = scene != 1;
    memory.singleton_present = scene != 2;
    const auto bindings = xar::ck3_12004::BindPhaseEventRoleImage12004(
        kImageBase, xar::ck3_12004::kPhaseRoleExecutableSha256,
        ReadOperandMemory, &memory);
    xar::ck3_12004::AttachPhaseEventRoleInputs12004(bindings, inputs);
    if (scene) bundle += ',';
    xar::game::AppendPhaseRiteStringV1(bundle, names[scene]);
    bundle += ':';
    bundle += xar::bridge::SerializeCombatSimulationInputsV2(inputs);
  }
  bundle += "}}\n";
  std::ofstream output(argv[1], std::ios::binary);
  output << bundle;
  return output ? 0 : 5;
}
