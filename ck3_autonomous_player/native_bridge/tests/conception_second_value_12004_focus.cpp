#include "xar_bridge/conception_second_value_12004.hpp"
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <cstring>
#include <limits>
#include <map>
#include <string>
#include <vector>

using namespace xar::ck3_12004;
struct Memory {
  std::map<std::uintptr_t, std::vector<unsigned char>> rows;
  std::vector<std::uintptr_t> reads;
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
  static bool read(void *opaque, std::uintptr_t address, void *out,
                   std::size_t count) noexcept {
    auto &self = *static_cast<Memory *>(opaque);
    self.reads.push_back(address);
    auto row = self.rows.upper_bound(address);
    if (row == self.rows.begin()) return false;
    --row;
    const auto offset = address - row->first;
    if (offset > row->second.size() || count > row->second.size() - offset)
      return false;
    std::memcpy(out, row->second.data() + offset, count);
    return true;
  }
};

int main() {
  // Source-declared fast bounds, signed division and split low64 behavior.
  assert(MultiplyConceptionRaw12004(100000, 50000) == 50000);
  assert(MultiplyConceptionRaw12004(-100000, 50000) == -50000);
  assert(MultiplyConceptionRaw12004(3037000499LL, 3037000499LL) == 92233720309262LL);
  assert(MultiplyConceptionRaw12004(-3037000499LL, 3037000499LL) == -92233720309262LL);
  assert(MultiplyConceptionRaw12004(std::numeric_limits<std::int64_t>::max(), 100000) == std::numeric_limits<std::int64_t>::max());
  assert(MultiplyConceptionRaw12004(std::numeric_limits<std::int64_t>::min(), 100000) == std::numeric_limits<std::int64_t>::min());
  assert(ConceptionAdjustedAgeRaw12004(35, 49999) == 35);
  assert(ConceptionAdjustedAgeRaw12004(35, 50000) == 34);
  assert(ConceptionAdjustedAgeRaw12004(35, -49999) == 35);
  assert(ConceptionAdjustedAgeRaw12004(35, -50000) == 36);

  constexpr std::uintptr_t base = 0x10000000, character = 0x20000000;
  constexpr std::uintptr_t extension = 0x21000000, model = 0x22000000;
  constexpr std::uintptr_t keys = 0x23000000, values = 0x24000000;
  constexpr std::uintptr_t thresholds = 0x25000000, multipliers = 0x26000000;
  Memory memory;
  memory.put<std::int32_t>(character + 0x18, 38822);
  memory.put<std::int16_t>(character + 0x68, 35);
  memory.put<std::int16_t>(character + 0x6C, -1);
  memory.put<std::uintptr_t>(character + 0x1B0, extension);
  memory.put<std::uintptr_t>(character + 0x1B8, 0x28000000);
  memory.put<std::uintptr_t>(character + 0x1C0, 0);
  memory.put<std::uintptr_t>(character + 0x1C8, 0);
  memory.put<std::uintptr_t>(extension + 0x258, model);
  memory.put<std::uintptr_t>(model + 8, character);
  memory.put<std::uintptr_t>(model + 0x10 + 0x68, keys);
  memory.put<std::int32_t>(model + 0x10 + 0x74, 3);
  memory.put<std::uintptr_t>(model + 0x10 + 0xD0, values);
  memory.array<std::uint16_t>(keys, {1, 191, 300});
  memory.array<std::int64_t>(values, {42, 50000, 99});
  // Native tests only the low DWORD of this loaded QWORD count.
  memory.put<std::uint64_t>(base + kConceptionSecondThresholdCount12004, 0xDEADBEEF00000003ULL);
  memory.put<std::uintptr_t>(base + kConceptionSecondThresholdPointer12004, thresholds);
  memory.put<std::uintptr_t>(base + kConceptionSecondMultiplierPointer12004, multipliers);
  memory.array<std::int32_t>(thresholds, {50, 35, 30});
  memory.array<std::int64_t>(multipliers, {0, 25000, 75000, 100000});
  auto binding = BindConceptionSecondValue12004(base, "1.20.0.4",
      "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518", Memory::read, &memory);
  xar::ck3_12002::family_value::FertilityRead seed;
  seed.available = true;
  seed.extension_present = true;
  seed.native_gate_evaluated = true;
  seed.native_gate_allows = true;
  seed.effective_raw = 40000;
  ConceptionSecondValueInputs12004 input;
  std::string reason;
  assert(ReadConceptionSecondValueInputs12004(binding, character, 38822, seed, input, reason));
  assert(input.selected_age_raw == 35 && input.modifier_bf_raw == 50000);
  assert(input.threshold_count_raw == 3 && input.thresholds_prefix == std::vector<std::int32_t>({50,35,30}));
  assert(input.selected_band_index == 2 && !input.conditional_final_factor_raw);
  auto value = ComputeConceptionSecondValue12004(input);
  assert(value.ready && value.adjusted_age_raw == 34 && value.value_raw == 30000);
  // A linked pointer keeps the final factor branch off; the absent slot is
  // intentionally never read by the real guarded source reader above.
  for (const auto address : memory.reads)
    assert(address != base + kConceptionFinalConditionalFactor12004);

  memory.put<std::uintptr_t>(character + 0x1B8, 0);
  memory.put<std::int64_t>(base + kConceptionFinalConditionalFactor12004, 25000);
  assert(ReadConceptionSecondValueInputs12004(binding, character, 38822, seed, input, reason));
  value = ComputeConceptionSecondValue12004(input);
  assert(value.ready && value.prefinal_raw == 30000 && value.value_raw == 7500);
  input.conditional_final_factor_raw.reset();
  value = ComputeConceptionSecondValue12004(input);
  assert(!value.ready && !value.value_raw && value.reason == "conditional_final_factor_unavailable");

  // Prefix exhaustion does not invent an unseen multiplier/band.
  input.thresholds_prefix = {50};
  input.selected_band_index = 1;
  value = ComputeConceptionSecondValue12004(input);
  assert(!value.ready && !value.value_raw);

  memory.put<std::uintptr_t>(model + 8, character + 0x1000);
  assert(!ReadConceptionSecondValueInputs12004(binding, character, 38822, seed, input, reason));
  assert(reason == "modifier_context_owned_model_unavailable" && input.thresholds_prefix.empty());
  memory.put<std::uintptr_t>(model + 8, character);
  assert(!ReadConceptionSecondValueInputs12004(binding, character, 38823, seed, input, reason));
  assert(reason == "second_character_full_id_mismatch");
  seed.available = false;
  assert(!ReadConceptionSecondValueInputs12004(binding, character, 38822, seed, input, reason));
  assert(reason == "existing_family_fertility_seed_unavailable");
  seed.available = true;

  // Native zero-count chooses multiplier index0 and needs no threshold pointer.
  memory.put<std::uint64_t>(base + kConceptionSecondThresholdCount12004, 0);
  memory.rows.erase(base + kConceptionSecondThresholdPointer12004);
  assert(ReadConceptionSecondValueInputs12004(binding, character, 38822, seed, input, reason));
  value = ComputeConceptionSecondValue12004(input);
  assert(value.ready && value.selected_band_index == 0 && value.value_raw == 0);
  binding.age_threshold_read_budget = 2;
  memory.put<std::uint64_t>(base + kConceptionSecondThresholdCount12004, 3);
  assert(!ReadConceptionSecondValueInputs12004(binding, character, 38822, seed, input, reason));
  assert(reason == "age_threshold_count_exceeds_observer_read_budget");
  assert(!BindConceptionSecondValue12004(base, "1.20.0.3", "wrong", Memory::read, &memory).enabled);
  return 0;
}
