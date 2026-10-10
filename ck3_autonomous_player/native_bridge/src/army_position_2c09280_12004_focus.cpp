#include "xar_bridge/army_position_2c09280_12004.hpp"
#include <cstring>
#include <unordered_map>
#include <vector>

namespace {
struct PositionReadFixture {
  std::unordered_map<std::uintptr_t, std::vector<std::uint8_t>> atoms;
  std::vector<std::uintptr_t> reads;
  std::uintptr_t failed_address = 0;

  template <class T> void Put(std::uintptr_t address, T value) {
    std::vector<std::uint8_t> bytes(sizeof value);
    std::memcpy(bytes.data(), &value, sizeof value);
    atoms[address] = bytes;
  }

  static bool Read(void *context, std::uintptr_t address, void *out,
                   std::size_t count) noexcept {
    auto &fixture = *static_cast<PositionReadFixture *>(context);
    fixture.reads.push_back(address);
    if (address == fixture.failed_address) return false;
    const auto found = fixture.atoms.find(address);
    if (found == fixture.atoms.end() || found->second.size() != count) return false;
    std::memcpy(out, found->second.data(), count);
    return true;
  }
};
} // namespace

// One new source-bound fragment, no main or independent EXE/run.
bool RunArmyPosition2C09280Focus12004() {
  using namespace xar::ck3_12004;
  constexpr std::uintptr_t image = 0x10000000;
  constexpr std::uintptr_t manager = 0x6000;
  constexpr std::uintptr_t table = 0x7000;
  constexpr std::uintptr_t row_war = 0x8000;
  constexpr std::uintptr_t fallback_war = 0x9000;
  constexpr std::int32_t requested = 0x12000002;
  PositionReadFixture fixture;
  fixture.Put(image + 0x5D1DE58, manager);
  fixture.Put(manager + 0x2C, std::uint32_t{3});
  fixture.Put(manager + 0x20, table);
  fixture.Put(table + 2 * 16 + 8, row_war);
  // Same low24 index, different full generation: actual source chooses fallback.
  fixture.Put(row_war + 8, std::uint32_t{0x11000002});
  fixture.Put(image + 0x5D1DE40, fallback_war);
  fixture.Put(fallback_war + 0x358, std::uint8_t{0});
  ArmyRegularCoreReadonlyAccess12004 access{image, &fixture, &PositionReadFixture::Read, 8};
  const auto operands = ReadArmyPositionWarOperands12004(access, requested, fallback_war);
  const auto accepted = EvaluateArmyPositionWarGate12004(operands);
  if (accepted.value != std::optional<bool>{true} || !operands.failures.empty() ||
      operands.row_full_war_id != std::optional<std::uint32_t>{0x11000002} ||
      operands.fallback_used != std::optional<bool>{true} ||
      operands.resolved_war_identity != std::optional<std::uintptr_t>{fallback_war}) return false;
  auto different_filter = operands;
  different_filter.optional_war_identity = row_war;
  if (EvaluateArmyPositionWarGate12004(different_filter).value != std::optional<bool>{false}) return false;

  // Unreadable capacity is independent missing evidence, never native fallback.
  fixture.failed_address = manager + 0x2C;
  fixture.reads.clear();
  const auto missing = ReadArmyPositionWarOperands12004(access, requested, fallback_war);
  const auto unknown = EvaluateArmyPositionWarGate12004(missing);
  if (unknown.value || unknown.unavailable_reason != "war_capacity:guarded_read_failed" ||
      missing.manager_identity != std::optional<std::uintptr_t>{manager} ||
      missing.capacity || missing.fallback_used || missing.resolved_war_identity ||
      fixture.reads.size() != 2) return false;
  return true;
}
