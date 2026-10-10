#include "xar_bridge/piety_price_numeric_31df3b0_12004.hpp"
#include "xar_bridge/construction_owner_mode3_raw_receiver_12004.hpp"

#include <array>
#include <cstdint>
#include <cstring>
#include <map>
#include <stdexcept>

namespace xar::ck3_12004::piety_price_raw_inputs {
namespace numeric_31df3b0_cases {

constexpr std::uintptr_t kDefinition = 0x1000012345000ULL;
constexpr std::uint64_t kFrame = 0xFEDCBA9876543210ULL;
constexpr std::uintptr_t kMode = kDefinition + 0x360;
constexpr std::uintptr_t kValue = kDefinition + 0x340;

struct Memory {
  std::map<std::uintptr_t, std::array<unsigned char, 4>> words;
  std::array<std::uintptr_t, 64> reads{};
  std::size_t read_count = 0;
  bool mutate_first_value = false;
  std::size_t value_read_count = 0;

  void Set(std::uintptr_t address, std::int32_t value) {
    auto& bytes = words[address];
    std::memcpy(bytes.data(), &value, sizeof(value));
  }

  static bool Guarded(void* context, const void* source, void* destination,
                      std::size_t bytes) noexcept {
    auto& memory = *static_cast<Memory*>(context);
    if (bytes != 4 || memory.read_count == memory.reads.size()) return false;
    const auto address = reinterpret_cast<std::uintptr_t>(source);
    memory.reads[memory.read_count++] = address;
    const auto found = memory.words.find(address);
    if (found == memory.words.end()) return false;
    std::memcpy(destination, found->second.data(), bytes);
    if (address == kValue) {
      ++memory.value_read_count;
      if (memory.mutate_first_value && memory.value_read_count == 1) {
        const std::int32_t changed = 6;
        std::memcpy(found->second.data(), &changed, sizeof(changed));
      }
    }
    return true;
  }

  bool Touched(std::uintptr_t address) const {
    for (std::size_t index = 0; index < read_count; ++index)
      if (reads[index] == address) return true;
    return false;
  }

  bool OnlyNumericOperands() const {
    for (std::size_t index = 0; index < read_count; ++index)
      if (reads[index] != kMode && reads[index] != kValue) return false;
    return true;
  }

  Numeric31DF3B0Bindings12004 Bind() {
    return BindPietyPriceNumeric31DF3B012004(
        0, kPietyPrice31DF3B0SourcePin12004, &Guarded, this);
  }

  construction_owner_mode3::RawReceiverAccessV1 Raw() {
    return {this, &Guarded, 0, true};
  }
};

void Need(bool condition, const char* reason) {
  if (!condition) throw std::runtime_error(reason);
}

} // namespace numeric_31df3b0_cases

void VerifyPietyPriceNumeric31DF3B0OwnedCases12004() {
  using namespace numeric_31df3b0_cases;
  {
    Memory memory;
    memory.Set(kMode, 0);
    memory.Set(kValue, -13);
    // A different literal selector (+760) must never replace this child's +2A8.
    memory.Set(kDefinition + 0x760 + 0xB8, 0);
    memory.Set(kDefinition + 0x760 + 0x98, 99);
    const auto result = ReadPietyPriceNumeric31DF3B012004(
        memory.Bind(), kDefinition, 0, kFrame);
    Need(result.source_ready && result.native_eax_raw == std::int32_t{-13} &&
             result.definition_pointer == kDefinition &&
             result.current_rite_pointer == 0 && result.frame_key == kFrame &&
             result.selected_expression_identity == kDefinition + 0x2A8 &&
             result.copied_diagnostics.has_value() &&
             !result.actual_original_consumed_values && memory.OnlyNumericOperands(),
         "31DF3B0 did not use the exact full-width selected expression and frame");
    std::int32_t adapted = 77;
    Need(ReadPietyPriceNumeric31DF3B0Adapter12004(
             nullptr, memory.Raw(), kDefinition, 0, kFrame, adapted) && adapted == -13,
         "31DF3B0 raw callback did not reuse the actual numeric producer");
  }
  {
    Memory memory;
    memory.Set(kMode, 0);
    memory.Set(kValue, 0);
    const auto result = ReadPietyPriceNumeric31DF3B012004(
        memory.Bind(), kDefinition, 0, 0);
    std::int32_t adapted = 77;
    Need(result.source_ready && result.native_eax_raw == std::int32_t{0} &&
             result.frame_key == 0 && ReadPietyPriceNumeric31DF3B0Adapter12004(
                 nullptr, memory.Raw(), kDefinition, 0, 0, adapted) && adapted == 0,
         "31DF3B0 lost an observed zero or invented a revision prerequisite");
  }
  {
    Memory memory;
    memory.Set(kMode, 1);
    memory.Set(kValue, -999);
    const auto result = ReadPietyPriceNumeric31DF3B012004(
        memory.Bind(), kDefinition, 0xABCDE0, kFrame);
    Need(!result.source_ready && !result.native_eax_raw &&
             result.copied_diagnostics.has_value() &&
             result.reason == result.copied_diagnostics->unavailable_reason &&
             !result.reason.empty() && !memory.Touched(kValue) &&
             memory.OnlyNumericOperands(),
         "31DF3B0 promoted an unknown dynamic branch or discarded its reason");
  }
  {
    Memory memory;
    memory.Set(kMode, 0);
    const auto result = ReadPietyPriceNumeric31DF3B012004(
        memory.Bind(), kDefinition, 0, kFrame);
    std::int32_t adapted = 77;
    Need(!result.source_ready && !result.native_eax_raw &&
             !ReadPietyPriceNumeric31DF3B0Adapter12004(
                 nullptr, memory.Raw(), kDefinition, 0, kFrame, adapted) && adapted == 77,
         "31DF3B0 substituted zero for an unread required DWORD");
  }
  {
    Memory memory;
    memory.Set(kMode, 0);
    memory.Set(kValue, 5);
    memory.mutate_first_value = true;
    const auto result = ReadPietyPriceNumeric31DF3B012004(
        memory.Bind(), kDefinition, 0, kFrame);
    Need(!result.source_ready && !result.native_eax_raw &&
             memory.value_read_count == 2 && result.copied_diagnostics.has_value() &&
             !result.reason.empty() &&
             result.reason == result.copied_diagnostics->unavailable_reason,
         "31DF3B0 accepted changed required raw input between operand copies");
  }
  {
    Memory memory;
    memory.Set(kMode, 0);
    memory.Set(kValue, 1);
    auto binding = memory.Bind();
    binding.exact_12004_bound = false;
    const auto result = ReadPietyPriceNumeric31DF3B012004(
        binding, kDefinition, 0, kFrame);
    auto raw = memory.Raw();
    raw.exact_12004_bound = false;
    std::int32_t adapted = 77;
    Need(!result.source_ready && !result.native_eax_raw && memory.read_count == 0 &&
             !ReadPietyPriceNumeric31DF3B0Adapter12004(
                 nullptr, raw, kDefinition, 0, kFrame, adapted) && adapted == 77,
         "31DF3B0 used an unbound source or mutated unavailable callback output");
  }
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
