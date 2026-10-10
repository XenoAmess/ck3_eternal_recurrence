#include "xar_bridge/army_position_2c3a0e0_readonly_12004.hpp"

#include <cstring>
#include <map>
#include <set>
#include <stdexcept>
#include <vector>

namespace xar::ck3_12004 {
namespace {
constexpr std::uintptr_t kImage = 0x10000000U;
constexpr std::uintptr_t kHolder = 0x20000000U;
constexpr std::uintptr_t kActor = 0x20001000U;
constexpr std::uintptr_t kOther = 0x20002000U;
constexpr std::uintptr_t kStateHolder = 0x30000000U;
constexpr std::uintptr_t kStateActor = 0x30001000U;
constexpr std::uintptr_t kLinkHolder = 0x40000000U;
constexpr std::uintptr_t kLinkActor = 0x40001000U;
constexpr std::uintptr_t kSecondaryState = 0x50000000U;
constexpr std::uintptr_t kInvalidSecondary = 0x60000000U;
constexpr std::uintptr_t kAlternate = 0x70000000U;
constexpr std::uint32_t kChar = 0x43686172U;

struct Memory {
  std::map<std::uintptr_t, std::vector<std::byte>> fields;
  std::map<std::uintptr_t, std::size_t> reads;
  std::set<std::uintptr_t> denied;
  std::uintptr_t deny_on_second_address = 0;

  template <typename T> void Put(std::uintptr_t address, T value) {
    auto &bytes = fields[address];
    bytes.resize(sizeof(value));
    std::memcpy(bytes.data(), &value, sizeof(value));
  }
  void Character(std::uintptr_t address, std::uint32_t id) {
    Put(address + 0x18U, id);
    Put(address + 0x1CU, kChar);
  }
  static bool Read(void *context, std::uintptr_t address, void *out,
                   std::size_t size) noexcept {
    auto &self = *static_cast<Memory *>(context);
    const std::size_t occurrence = ++self.reads[address];
    if (self.denied.contains(address) ||
        (address == self.deny_on_second_address && occurrence == 2U))
      return false;
    const auto found = self.fields.find(address);
    if (found == self.fields.end() || found->second.size() != size)
      return false;
    std::memcpy(out, found->second.data(), size);
    return true;
  }
  ArmyRegularCoreReadonlyAccess12004 Access(std::size_t maximum = 8U) {
    return {kImage, this, &Memory::Read, maximum};
  }
};

Memory Directed(std::uint32_t actor_id = 0xAB000005U) {
  Memory memory;
  memory.Character(kHolder, 0x12000001U);
  memory.Character(kActor, actor_id);
  memory.Put(kHolder + 0x1C0U, kStateHolder);
  memory.Put(kStateHolder + 0x1C8U, kLinkHolder);
  memory.Put(kLinkHolder + 0x28U, kActor);
  memory.Put(kStateHolder + 0x1ECU, std::uint32_t{1U});
  memory.Put(kActor + 0x1D0U, std::uintptr_t{0U});
  memory.Put(kActor + 0x1C0U, kStateActor);
  memory.Put(kStateActor + 0x1C0U, kSecondaryState);
  memory.Put(kSecondaryState + 0x28U, kInvalidSecondary);
  memory.Put(kInvalidSecondary + 0x1CU, std::uint32_t{0x5469746CU});
  // Advancing to actor returns actor itself, which terminates the main loop.
  memory.Put(kStateActor + 0x1C8U, kLinkActor);
  memory.Put(kLinkActor + 0x28U, kActor);
  return memory;
}

void Check(bool condition, const char *label, int &checks) {
  if (!condition)
    throw std::runtime_error(label);
  ++checks;
}
void Value(const ArmyRegularCoreReadonlyPredicate12004 &result,
           bool expected, const char *label, int &checks) {
  Check(result.value.has_value() && *result.value == expected &&
            result.unavailable_reason.empty(), label, checks);
}
} // namespace

// Exported to the new 34b/33 compound fixture; no independent executable/main.
int RunArmyPosition2C3A0E012004Cases() {
  int checks = 0;
  {
    Memory memory = Directed();
    Value(ReadArmyPosition2C3A0E012004(memory.Access(), kHolder, kActor),
          true, "holder_to_actor_active", checks);
    Check(memory.reads[kHolder + 0x1C0U] == 3U,
          "two_independent_steps_then_activity", checks);
  }
  {
    Memory memory = Directed();
    Value(ReadArmyPosition2C3A0E012004(memory.Access(), kActor, kHolder),
          false, "reverse_direction_is_distinct", checks);
    Check(memory.reads[kHolder + 0x18U] == 0U,
          "self_return_skips_target_id", checks);
  }
  {
    Memory memory = Directed();
    memory.Character(kOther, 0xCD000005U);
    Value(ReadArmyPosition2C3A0E012004(memory.Access(), kHolder, kOther),
          false, "same_low24_different_generation", checks);
    Check(memory.reads[kStateHolder + 0x1ECU] == 0U,
          "full_id_mismatch_skips_activity", checks);
  }
  {
    Memory memory = Directed();
    memory.Put(kHolder + 0x1C0U, std::uintptr_t{0U});
    memory.Put(kImage + 0x5C67570U, kActor);
    memory.Put(kHolder + 0x1D0U, kAlternate);
    memory.Put(kAlternate + 0x74U, std::uint32_t{0x80000000U});
    Value(ReadArmyPosition2C3A0E012004(memory.Access(), kHolder, kActor),
          true, "loaded_fallback_and_unsigned_nonzero_alternate", checks);
    Check(memory.reads[kStateHolder + 0x1C8U] == 0U,
          "null_state_skips_intermediate", checks);
  }
  {
    Memory memory = Directed();
    memory.Put(kHolder + 0x1C0U, std::uintptr_t{0U});
    memory.Put(kImage + 0x5C67570U, kOther);
    memory.Put(kOther + 0x1CU, std::uint32_t{0U});
    memory.denied.insert(kOther + 0x18U);
    Value(ReadArmyPosition2C3A0E012004(memory.Access(), kHolder, kActor),
          false, "wrong_returned_domain_is_false", checks);
    Check(memory.reads[kOther + 0x18U] == 0U,
          "wrong_domain_skips_id", checks);
  }
  {
    Memory memory = Directed();
    memory.Put(kActor + 0x1CU, std::uint32_t{0U});
    memory.denied.insert(kActor + 0x18U);
    Value(ReadArmyPosition2C3A0E012004(memory.Access(), kHolder, kActor),
          false, "invalid_candidate_returns_original_holder", checks);
    Check(memory.reads[kActor + 0x18U] == 0U,
          "leaf_candidate_domain_skips_id", checks);
  }
  {
    Memory memory = Directed();
    memory.Put(kActor + 0x1D0U, kAlternate);
    memory.denied.insert(kActor + 0x1C0U);
    Value(ReadArmyPosition2C3A0E012004(memory.Access(), kHolder, kActor),
          false, "candidate_alternate_state_returns_self", checks);
    Check(memory.reads[kActor + 0x1C0U] == 0U,
          "candidate_alternate_skips_secondary_chain", checks);
  }
  {
    Memory memory = Directed();
    memory.Put(kStateHolder + 0x1ECU, std::uint32_t{0U});
    memory.Put(kHolder + 0x1D0U, kAlternate);
    memory.Put(kAlternate + 0x74U, std::uint32_t{1U});
    Value(ReadArmyPosition2C3A0E012004(memory.Access(), kHolder, kActor),
          false, "present_primary_zero_does_not_select_alternate", checks);
    Check(memory.reads[kHolder + 0x1D0U] == 0U &&
              memory.reads[kAlternate + 0x74U] == 0U,
          "primary_state_controls_read_demand", checks);
  }
  {
    Memory memory = Directed();
    memory.denied.insert(kHolder + 0x1C0U);
    const auto result = ReadArmyPosition2C3A0E012004(memory.Access(), kHolder, kActor);
    Check(!result.value && result.unavailable_reason == "hierarchy_state_unreadable",
          "failed_state_read_is_unknown", checks);
    Check(memory.reads[kImage + 0x5C67570U] == 0U,
          "failed_read_does_not_select_fallback", checks);
  }
  {
    Memory memory = Directed();
    const auto result = ReadArmyPosition2C3A0E012004(memory.Access(0U), kHolder, kActor);
    Check(!result.value && result.unavailable_reason == "hierarchy_occurrence_limit_reached",
          "zero_occurrence_budget_is_unknown", checks);
    Check(memory.reads.empty(), "zero_budget_reads_nothing", checks);
  }
  {
    Memory memory = Directed();
    memory.deny_on_second_address = kHolder + 0x1C0U;
    const auto result = ReadArmyPosition2C3A0E012004(memory.Access(), kHolder, kActor);
    Check(!result.value && result.unavailable_reason == "hierarchy_state_unreadable",
          "second_step_read_failure_remains_unknown", checks);
    Check(memory.reads[kHolder + 0x1C0U] == 2U &&
              memory.reads[kStateHolder + 0x1ECU] == 0U,
          "independent_second_call_not_cached", checks);
  }
  {
    Memory memory = Directed();
    memory.Character(kOther, 0x00000005U);
    memory.Put(kHolder + 0x1D0U, std::uintptr_t{0U});
    memory.Put(kStateHolder + 0x1C0U, kSecondaryState);
    memory.Put(kStateHolder + 0x1ECU, std::uint32_t{0U});
    memory.Put(kLinkActor + 0x28U, kHolder);
    const auto result = ReadArmyPosition2C3A0E012004(memory.Access(2U), kHolder, kOther);
    Check(!result.value && result.unavailable_reason == "hierarchy_occurrence_limit_reached",
          "finite_cycle_bound_is_unknown", checks);
  }
  return checks;
}
} // namespace xar::ck3_12004
