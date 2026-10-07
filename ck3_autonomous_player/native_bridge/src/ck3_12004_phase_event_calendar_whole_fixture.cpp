// Root-only FIRST: the real collector and JSON leaf serializer cross into the
// production registered V2 service using one complete base-wire bundle.
// Fake operand memory is not actual4 paused/live evidence.
#include "xar_bridge/ck3_12004_phase_event_calendar.hpp"
#include "xar_bridge/phase_event_calendar_observation_v1_serializer.hpp"
#include "xar_bridge/combat_simulation_inputs_v2_wire.hpp"
#include <fstream>
#include <iostream>
#include <iterator>
#include <sstream>
#include "phase-calendar-base-seed.inc"

namespace {
constexpr std::uintptr_t kImageBase = 0x140000000;
constexpr std::uintptr_t kDateObject = 0x170000000;
struct OperandMemory {
  std::uint32_t interval = 7;
  std::uint32_t date = 53288448;
  bool readable = true;
};
bool ReadOperandMemory(std::uintptr_t address, void *out, std::size_t size,
                       void *context) noexcept {
  const auto &memory = *static_cast<const OperandMemory *>(context);
  if (!memory.readable) return false;
  if (address == kImageBase + xar::ck3_12004::kPhaseCalendarIntervalSlotRva &&
      size == sizeof(memory.interval)) {
    std::memcpy(out, &memory.interval, size); return true;
  }
  if (address == kImageBase + xar::ck3_12004::kPhaseCalendarDatePointerSlotRva &&
      size == sizeof(kDateObject)) {
    std::memcpy(out, &kDateObject, size); return true;
  }
  if (address == kDateObject + 8 && size == sizeof(memory.date)) {
    std::memcpy(out, &memory.date, size); return true;
  }
  return false;
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "usage: calendar-whole-fixture output.json\n";
    return 2;
  }
  auto inputs = SeedPhaseCalendarWholeV2Fixture();
  const char *names[] = {"available", "zero_interval", "unavailable"};
  std::string bundle = "{\"schema_version\":1,\"scene_order\":[\"available\",\"zero_interval\",\"unavailable\"],\"samples\":{";
  OperandMemory memory;
  for (int scene = 0; scene < 3; ++scene) {
    memory.interval = scene == 1 ? 0 : 7;
    memory.readable = scene != 2;
    const auto binding = xar::ck3_12004::BindPhaseEventCalendarImage12004(
        kImageBase, xar::ck3_12004::kPhaseCalendarExecutableSha256,
        ReadOperandMemory, &memory);
    xar::ck3_12004::AttachPhaseEventCalendarInputs12004(binding, inputs);
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
