#include "xar_bridge/construction_owner_factor_2b9cba0_12004.hpp"

#include <cstring>
#include <stdexcept>

namespace xar::ck3_12004 {
namespace {
struct FactorReadFixture {
  std::uintptr_t expected_address = 0;
  std::uint8_t raw = 0;
  bool available = true;
  std::size_t reads = 0;
  bool exact_one_byte = true;
};
bool ReadFactorFixture(void *context, std::uintptr_t address, void *output,
                       std::size_t size) noexcept {
  auto &fixture = *static_cast<FactorReadFixture *>(context);
  ++fixture.reads;
  fixture.exact_one_byte &= address == fixture.expected_address && size == 1;
  if (!fixture.available || !fixture.exact_one_byte) return false;
  std::memcpy(output, &fixture.raw, 1);
  return true;
}
void RequireFactor(bool condition, const char *case_name) {
  if (!condition) throw std::runtime_error(case_name);
}
} // namespace

// No main and no standalone execution. Called once by 03's next connected
// producer compound; these cases never invoke any active native function.
int RunArmyFactor2B9CBA012004NewCases() {
  int count = 0;
  ConstructionOwnerFactorBinding12004 binding{0x1000, 0x2000, 71, true};
  FactorReadFixture fixture{0x24D6, 0};
  auto inputs = ReadConstructionOwnerFactorInputs12004(
      binding, ReadFactorFixture, &fixture);
  auto result = EvaluateNullDetailFactor12004(inputs);
  RequireFactor(fixture.reads == 1 && fixture.exact_one_byte &&
                    result.factor_raw == 100000 && !result.modifier_branch_taken,
                "2B9CBA0 actual one-byte read and default branch");
  ++count;

  fixture.raw = 5;
  inputs = ReadConstructionOwnerFactorInputs12004(
      binding, ReadFactorFixture, &fixture);
  result = EvaluateNullDetailFactor12004(inputs);
  RequireFactor(!result.factor_raw && result.modifier_branch_taken &&
                    !result.unavailable_reason.empty(),
                "2B9CBA0 conditional missing source stays unknown");
  ++count;

  ConstructionOwnerModifier4EInput12004 modifier{0x1000, 71, 0x4E, -11, true};
  inputs.modifier_4e = modifier;
  result = EvaluateNullDetailFactor12004(inputs);
  RequireFactor(result.factor_raw == 0 && result.modifier_4e_returned_q64 == -11,
                "2B9CBA0 negative signed native result is clamped");
  ++count;

  inputs.modifier_4e->returned_q64 = 0;
  result = EvaluateNullDetailFactor12004(inputs);
  RequireFactor(result.factor_raw == 0 && result.unavailable_reason.empty(),
                "2B9CBA0 native zero is available");
  ++count;

  inputs.modifier_4e->returned_q64 = 170001;
  result = EvaluateNullDetailFactor12004(inputs);
  RequireFactor(result.factor_raw == 170001,
                "2B9CBA0 factor is not capped at one");
  ++count;

  inputs.modifier_4e->returned_q64 = std::numeric_limits<std::int64_t>::max();
  result = EvaluateNullDetailFactor12004(inputs);
  RequireFactor(result.factor_raw == std::numeric_limits<std::int64_t>::max(),
                "2B9CBA0 retains full signed Q64 width");
  ++count;

  inputs.modifier_4e->context_receiver = 0x1001;
  result = EvaluateNullDetailFactor12004(inputs);
  RequireFactor(!result.factor_raw,
                "2B9CBA0 context from another receiver is not ready");
  ++count;

  inputs.modifier_4e->context_receiver = binding.input_receiver;
  inputs.modifier_4e->frame_key = 70;
  result = EvaluateNullDetailFactor12004(inputs);
  RequireFactor(!result.factor_raw,
                "2B9CBA0 context from another frame is not ready");
  ++count;

  inputs.modifier_4e->frame_key = binding.frame_key;
  inputs.modifier_4e->modifier_index = 0x4F;
  result = EvaluateNullDetailFactor12004(inputs);
  RequireFactor(!result.factor_raw,
                "2B9CBA0 numeric modifier identity must be 4E");
  ++count;

  inputs.selector_byte_4d6 = std::uint8_t{6};
  result = EvaluateNullDetailFactor12004(inputs);
  RequireFactor(result.factor_raw == 100000 && !result.modifier_branch_taken,
                "2B9CBA0 other byte does not depend on rejected modifier");
  ++count;

  fixture.available = false;
  inputs = ReadConstructionOwnerFactorInputs12004(
      binding, ReadFactorFixture, &fixture, modifier);
  result = EvaluateNullDetailFactor12004(inputs);
  RequireFactor(!result.factor_raw && !inputs.selector_byte_4d6,
                "2B9CBA0 memory failure is not a guessed default");
  ++count;

  binding.source_ready = false;
  const auto reads_before = fixture.reads;
  inputs = ReadConstructionOwnerFactorInputs12004(
      binding, ReadFactorFixture, &fixture, modifier);
  result = EvaluateNullDetailFactor12004(inputs);
  RequireFactor(!result.factor_raw && fixture.reads == reads_before,
                "2B9CBA0 unqualified source performs no memory read");
  ++count;
  return count;
}

} // namespace xar::ck3_12004
