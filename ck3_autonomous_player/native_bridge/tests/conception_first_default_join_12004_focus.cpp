#include "xar_bridge/conception_first_value_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <map>
#include <stdexcept>

namespace {
using namespace xar::ck3_12004;
constexpr std::uintptr_t kBase = 0x100000000ULL;
constexpr std::uintptr_t kCharacter = 0x100000ULL;
constexpr std::uintptr_t kFamily = 0x200000ULL;
constexpr std::uintptr_t kExtension = 0x300000ULL;
constexpr std::uintptr_t kModel = 0x400000ULL;
constexpr std::uintptr_t kThresholds = 0x500000ULL;
constexpr std::uintptr_t kFactors = 0x600000ULL;
constexpr std::uintptr_t kDefault = kBase + 0x5D67B90;
constexpr std::uint32_t kFullId = 38822;

struct DefaultFirstFixture {
  std::map<std::uintptr_t, std::byte> memory;
  bool reset_values_after_bf_count = false;
  template<class T> void Store(std::uintptr_t address, T value) {
    std::array<std::byte, sizeof(T)> bytes{};
    std::memcpy(bytes.data(), &value, sizeof(T));
    for (std::size_t i = 0; i != bytes.size(); ++i)
      memory[address + i] = bytes[i];
  }
  bool Copy(std::uintptr_t address, void *output, std::size_t size) {
    auto *bytes = static_cast<std::byte *>(output);
    for (std::size_t i = 0; i != size; ++i) {
      const auto found = memory.find(address + i);
      if (found == memory.end()) return false;
      bytes[i] = found->second;
    }
    if (reset_values_after_bf_count && address == kDefault + 0x74 && size == 4) {
      reset_values_after_bf_count = false;
      Store(kDefault + 0xD0, std::uintptr_t{0});
      Store(kDefault + 0xD8, std::int32_t{0});
      Store(kDefault + 0xDC, std::int32_t{0});
    }
    return true;
  }
};

bool ReadAddress(void *context, std::uintptr_t address, void *output,
                 std::size_t size) noexcept {
  return static_cast<DefaultFirstFixture *>(context)->Copy(address, output, size);
}
bool ReadPointer(void *context, const void *address, void *output,
                 std::size_t size) noexcept {
  return ReadAddress(context, reinterpret_cast<std::uintptr_t>(address), output, size);
}
void Require(bool value, const char *reason) {
  if (!value) throw std::runtime_error(reason);
}
DefaultFirstFixture MakeFixture() {
  DefaultFirstFixture fixture;
  fixture.Store(kCharacter + 0x18, kFullId);
  fixture.Store(kCharacter + 0x1C, std::uint32_t{0x43686172});
  fixture.Store(kCharacter + 0x1A8, kFamily);
  fixture.Store(kCharacter + 0x1B0, std::uintptr_t{0});
  for (const auto offset : {0x1C8U, 0x1C0U, 0x1B8U})
    fixture.Store(kCharacter + offset, std::uint64_t{0});
  fixture.Store(kFamily + 0x44, std::int32_t{2});
  fixture.Store(kBase + 0x5C69ED8, std::int64_t{10000});
  fixture.Store(kBase + 0x5D67B80, std::int32_t{-2147483647});
  fixture.Store(kDefault + 0x68, kDefault + 0x88);
  fixture.Store(kDefault + 0x70, std::int32_t{32});
  fixture.Store(kDefault + 0x74, std::int32_t{0});
  fixture.Store(kDefault + 0xD0, kDefault + 0xF0);
  fixture.Store(kDefault + 0xD8, std::int32_t{32});
  fixture.Store(kDefault + 0xDC, std::int32_t{0});
  fixture.Store(kBase + 0x544FC04, std::uint64_t{2});
  fixture.Store(kBase + 0x544FBF8, kThresholds);
  fixture.Store(kThresholds, std::int32_t{45});
  fixture.Store(kThresholds + 4, std::int32_t{30});
  fixture.Store(kBase + 0x544FCA8, kFactors);
  fixture.Store(kFactors, std::int64_t{100000});
  fixture.Store(kFactors + 8, std::int64_t{75000});
  fixture.Store(kFactors + 16, std::int64_t{0});
  fixture.Store(kBase + 0x5C69E10, std::int64_t{50000});
  return fixture;
}
} // namespace

// Included as one production-join cell in 46b's sole fresh compound fixture.
// No main, separate execution, native initializer or old arithmetic replay.
bool VerifyConceptionFirstDefaultJoin12004() {
  try {
    auto fixture = MakeFixture();
    const auto original = fixture.memory;
    auto first = BindConceptionFirstValue12004(
        kGameVersion, kExecutableSha256, kBase, ReadPointer, &fixture);
    auto modifier = BindConceptionModifierContext12004(
        kBase, kGameVersion, kExecutableSha256, ReadAddress, &fixture);
    xar::ck3_12002::family_value::CharacterValue current;
    current.character_id = static_cast<std::int32_t>(kFullId);
    current.age_raw = std::int16_t{35};
    current.scorer_age_override_raw = std::int16_t{-1};
    current.fertility.available = true;
    current.fertility.effective_raw = 0;
    std::string_view reason;
    auto context = ResolveConceptionModifierContext12004(
        modifier, kCharacter, static_cast<std::int32_t>(kFullId));
    auto input = ReadConceptionFirstValueInputsWithModifierContext12004(
        first, modifier, kCharacter, kFullId, current, context, &reason);
    auto value = EvaluateConceptionFirstValue12004(input);
    Require(context.ready && context.source ==
        ConceptionModifierContextSource12004::InitializedDefault && input &&
        reason.empty() && value.status == "available" &&
        input->modifier_bf_raw == 0 && !input->final_multiplier_applies &&
        value.seed_after_children_raw == -20000 && value.first_output_raw == -15000,
        "null extension initialized default did not feed exact signed first output");
    Require(fixture.memory == original, "default first observer changed source memory");

    // Wrong-owner actual getter branch selects the same initialized default.
    fixture.Store(kCharacter + 0x1B0, kExtension);
    fixture.Store(kExtension + 0x258, kModel);
    fixture.Store(kModel + 8, kCharacter + 0x1000);
    current.fertility.effective_raw = 80000;
    context = ResolveConceptionModifierContext12004(
        modifier, kCharacter, static_cast<std::int32_t>(kFullId));
    input = ReadConceptionFirstValueInputsWithModifierContext12004(
        first, modifier, kCharacter, kFullId, current, context, &reason);
    value = EvaluateConceptionFirstValue12004(input);
    Require(input && context.source == ConceptionModifierContextSource12004::InitializedDefault &&
        value.status == "available" && value.first_output_raw == 22500,
        "wrong owner initialized default failed first final-writer join");

    // Current data are copied, rather than replaced by static count-zero input.
    fixture.Store(kDefault + 0x74, std::int32_t{1});
    fixture.Store(kDefault + 0xDC, std::int32_t{1});
    fixture.Store(kDefault + 0x88, std::uint16_t{0xBF});
    fixture.Store(kDefault + 0xF0, std::int64_t{550000});
    context = ResolveConceptionModifierContext12004(
        modifier, kCharacter, static_cast<std::int32_t>(kFullId));
    input = ReadConceptionFirstValueInputsWithModifierContext12004(
        first, modifier, kCharacter, kFullId, current, context, &reason);
    value = EvaluateConceptionFirstValue12004(input);
    Require(input && input->modifier_bf_raw == 550000 &&
        value.adjusted_age_raw == 29 && value.status == "available" &&
        value.first_output_raw == 0,
        "current default BF value was fabricated or zero output was lost");

    // A completed guard does not hide storage reset between resolution/copy.
    fixture.Store(kDefault + 0x74, std::int32_t{0});
    fixture.Store(kDefault + 0xDC, std::int32_t{0});
    context = ResolveConceptionModifierContext12004(
        modifier, kCharacter, static_cast<std::int32_t>(kFullId));
    fixture.reset_values_after_bf_count = true;
    input = ReadConceptionFirstValueInputsWithModifierContext12004(
        first, modifier, kCharacter, kFullId, current, context, &reason);
    value = EvaluateConceptionFirstValue12004(input);
    Require(!input && reason == "native_conception_first_modifier_context_changed" &&
        !value.first_output_raw && value.status == "unavailable",
        "default reset during BF copy became available or fabricated zero");
    std::cout << "{\"check\":\"first_default_current_context_join\",\"status\":\"GREEN\","
                 "\"native_initializer_called\":false,\"game_or_sdk\":false}\n";
    return true;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return false;
  }
}
