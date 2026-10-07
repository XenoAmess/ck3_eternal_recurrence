// Root's new single-sample FIRST. The original three-scene FIRST is not run.
// Production binder/collector/whole serializer; fake memory is not live data.
#include "xar_bridge/ck3_12004_phase_event_role_compatibility.hpp"
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
constexpr std::array<std::uint32_t, 4> kRoles{0, 1, 7, 1};
bool ReadOperandMemory(std::uintptr_t address, void *out, std::size_t size,
                       void *) noexcept {
  const auto copy = [&](const auto &value) {
    if (size != sizeof(value)) return false;
    std::memcpy(out, &value, size); return true;
  };
  if (address == kImageBase + xar::ck3_12004::kPhaseRoleRegistryPointerSlotRva)
    return copy(kDatabase);
  if (address == kDatabase + 0x50) return copy(kRows);
  if (address == kDatabase + 0x5C) return copy(std::int32_t{4});
  for (std::size_t index = 0; index < kEvents.size(); ++index) {
    if (address == kRows + index * 8) return copy(kEvents[index]);
    if (address == kEvents[index] + 0x1B0) return copy(kRoles[index]);
  }
  return false;
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "usage: commander-caller-whole-fixture output.json\n"; return 2;
  }
  auto inputs = SeedPhaseRoleWholeV2Fixture();
  const auto bindings = xar::ck3_12004::BindPhaseEventRoleImage12004(
      kImageBase, xar::ck3_12004::kPhaseRoleExecutableSha256, ReadOperandMemory);
  xar::ck3_12004::AttachPhaseEventRoleInputs12004(bindings, inputs);
  std::ofstream output(argv[1], std::ios::binary);
  output << xar::bridge::SerializeCombatSimulationInputsV2(inputs) << '\n';
  return output ? 0 : 5;
}
