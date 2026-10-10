#include "xar_bridge/conception_second_value_12004.hpp"
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <cstring>
#include <map>
#include <string>
#include <vector>

using namespace xar::ck3_12004;
bool VerifyConceptionFirstDefaultJoin12004();
namespace {
constexpr std::uintptr_t base = 0x10000000, character = 0x20000000;
constexpr std::uintptr_t extension = 0x21000000, model = 0x22000000;
constexpr std::uintptr_t default_context = base + 0x5D67B90;
constexpr std::uintptr_t default_guard = base + 0x5D67B80;
constexpr auto sha = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
struct Memory {
  std::map<std::uintptr_t, std::vector<unsigned char>> rows;
  bool change_guard_after_bf = false;
  template<class T> void put(std::uintptr_t address, T value) {
    std::vector<unsigned char> bytes(sizeof(T));
    std::memcpy(bytes.data(), &value, sizeof(T));
    rows[address] = std::move(bytes);
  }
  template<class T> void array(std::uintptr_t address, std::vector<T> values) {
    std::vector<unsigned char> bytes(values.size() * sizeof(T));
    std::memcpy(bytes.data(), values.data(), bytes.size());
    rows[address] = std::move(bytes);
  }
  static bool read(void *opaque, std::uintptr_t address, void *output,
                   std::size_t count) noexcept {
    auto &self = *static_cast<Memory *>(opaque);
    auto found = self.rows.upper_bound(address);
    if (found == self.rows.begin()) return false;
    --found;
    const auto offset = address - found->first;
    if (offset > found->second.size() || count > found->second.size() - offset)
      return false;
    std::memcpy(output, found->second.data() + offset, count);
    if (self.change_guard_after_bf && address == base + 0x545FE08) {
      self.put<std::int32_t>(default_guard, -18);
      self.change_guard_after_bf = false;
    }
    return true;
  }
};
void live_default(Memory &memory) {
  memory.put<std::int32_t>(default_guard, -17);
  memory.put<std::uintptr_t>(default_context + 0x68, default_context + 0x88);
  memory.put<std::int32_t>(default_context + 0x70, 32);
  memory.put<std::int32_t>(default_context + 0x74, 0);
  memory.put<std::uintptr_t>(default_context + 0xD0, default_context + 0xF0);
  memory.put<std::int32_t>(default_context + 0xD8, 32);
  memory.put<std::int32_t>(default_context + 0xDC, 0);
}
}
int main() {
  Memory memory;
  memory.put<std::int32_t>(character + 0x18, 38822);
  memory.put<std::int16_t>(character + 0x68, 35);
  memory.put<std::int16_t>(character + 0x6C, -1);
  memory.put<std::uintptr_t>(character + 0x1B0, extension);
  memory.put<std::uintptr_t>(extension + 0x258, 0);
  memory.put<std::uintptr_t>(character + 0x1B8, 0);
  memory.put<std::uintptr_t>(character + 0x1C0, 0);
  memory.put<std::uintptr_t>(character + 0x1C8, 0);
  live_default(memory);
  auto contexts = BindConceptionModifierContext12004(base, "1.20.0.4", sha, Memory::read, &memory);
  auto observation = ResolveConceptionModifierContext12004(contexts, character, 38822);
  assert(observation.ready && observation.context_address == default_context);
  assert(observation.source == ConceptionModifierContextSource12004::InitializedDefault);
  assert(observation.keys_stamp.capacity_raw == 32 && observation.keys_stamp.count_raw == 0);
  std::string reason;
  assert(CheckConceptionModifierContextStillCurrent12004(contexts, observation, reason));

  constexpr std::uintptr_t thresholds = 0x25000000, multipliers = 0x26000000;
  memory.put<std::uint64_t>(base + 0x545FD64, 3);
  memory.put<std::uintptr_t>(base + 0x545FD58, thresholds);
  memory.put<std::uintptr_t>(base + 0x545FE08, multipliers);
  memory.array<std::int32_t>(thresholds, {50, 35, 30});
  memory.array<std::int64_t>(multipliers, {0, 25000, 75000, 100000});
  memory.put<std::int64_t>(base + 0x5C69E10, 25000);
  auto second = BindConceptionSecondValue12004(base, "1.20.0.4", sha, Memory::read, &memory);
  xar::ck3_12002::family_value::FertilityRead seed;
  seed.available = seed.extension_present = seed.native_gate_evaluated = seed.native_gate_allows = true;
  seed.effective_raw = 40000;
  ConceptionSecondValueInputs12004 inputs;
  assert(ReadConceptionSecondValueInputs12004(second, character, 38822, seed, inputs, reason));
  assert(inputs.modifier_bf_raw == 0 && inputs.modifier_context.ready);
  assert(inputs.modifier_context.source == ConceptionModifierContextSource12004::InitializedDefault);
  assert(ComputeConceptionSecondValue12004(inputs).value_raw == 2500);

  // Known owner mismatch follows the actual native default branch too.
  memory.put<std::uintptr_t>(extension + 0x258, model);
  memory.put<std::uintptr_t>(model + 8, character + 0x1000);
  assert(ReadConceptionSecondValueInputs12004(second, character, 38822, seed, inputs, reason));
  assert(ComputeConceptionSecondValue12004(inputs).value_raw == 2500);

  for (const std::int32_t guard : {0, -1}) {
    memory.put<std::int32_t>(default_guard, guard);
    assert(!ReadConceptionSecondValueInputs12004(second, character, 38822, seed, inputs, reason));
    assert(reason == "modifier_default_not_initialized" && !inputs.modifier_context.ready);
  }
  live_default(memory);
  memory.put<std::uintptr_t>(default_context + 0x68, 0);
  assert(!ReadConceptionSecondValueInputs12004(second, character, 38822, seed, inputs, reason));
  assert(reason == "modifier_default_storage_unavailable");
  live_default(memory);
  memory.put<std::int32_t>(default_context + 0xD8, 0);
  assert(!ReadConceptionSecondValueInputs12004(second, character, 38822, seed, inputs, reason));
  assert(reason == "modifier_default_storage_unavailable");
  live_default(memory);
  memory.change_guard_after_bf = true;
  assert(!ReadConceptionSecondValueInputs12004(second, character, 38822, seed, inputs, reason));
  assert(reason == "modifier_context_changed_during_read" && !inputs.modifier_context.ready);

  // Guard state is not consulted when the owned receiver is actually selected.
  memory.put<std::uintptr_t>(model + 8, character);
  memory.put<std::int32_t>(default_guard, 0);
  memory.put<std::int32_t>(model + 0x10 + 0x74, 0);
  assert(ReadConceptionSecondValueInputs12004(second, character, 38822, seed, inputs, reason));
  assert(inputs.modifier_context.source == ConceptionModifierContextSource12004::OwnedCharacter);
  assert(ComputeConceptionSecondValue12004(inputs).value_raw == 2500);

  // Missing extension can legitimately yield native seed0 with a ready default.
  live_default(memory);
  memory.put<std::uintptr_t>(character + 0x1B0, 0);
  seed.extension_present = seed.native_gate_evaluated = seed.native_gate_allows = false;
  seed.effective_raw = 0;
  assert(ReadConceptionSecondValueInputs12004(second, character, 38822, seed, inputs, reason));
  assert(ComputeConceptionSecondValue12004(inputs).value_raw == 0);
  assert(!ReadConceptionSecondValueInputs12004(second, character, 38823, seed, inputs, reason));
  assert(reason == "second_character_full_id_mismatch");
  assert(VerifyConceptionFirstDefaultJoin12004());
  return 0;
}
