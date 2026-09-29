#include "xar_bridge/marriage_character_fertility_v1.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace {

bool GateTrue(void *) { return true; }
bool GateFalse(void *) { return false; }

} // namespace

int main() {
  std::array<std::byte, 0x200> character{};
  std::array<std::byte, 0x300> extension{};
  auto *extension_pointer = extension.data();
  constexpr std::int64_t raw = 87543;
  std::memcpy(character.data() +
                  xar::bridge::kMarriageFertilityExtensionOffsetV1,
              &extension_pointer, sizeof(extension_pointer));
  std::memcpy(extension.data() + xar::bridge::kMarriageFertilityRawOffsetV1,
              &raw, sizeof(raw));
  using xar::bridge::ReadMarriageCharacterFertilityV1;
  assert(!ReadMarriageCharacterFertilityV1(
              character.data(), 0, false, true, GateTrue).available);
  const auto positive = ReadMarriageCharacterFertilityV1(
      character.data(), 0, true, true, GateTrue);
  assert(positive.available && positive.extension_present &&
         positive.native_gate_evaluated && positive.native_gate_allows &&
         positive.effective_raw == raw);
  const auto gated = ReadMarriageCharacterFertilityV1(
      character.data(), 0, true, true, GateFalse);
  assert(gated.available && gated.extension_present &&
         gated.native_gate_evaluated && !gated.native_gate_allows &&
         gated.effective_raw == 0);
  extension_pointer = nullptr;
  std::memcpy(character.data() +
                  xar::bridge::kMarriageFertilityExtensionOffsetV1,
              &extension_pointer, sizeof(extension_pointer));
  const auto missing = ReadMarriageCharacterFertilityV1(
      character.data(), 0, true, true, GateTrue);
  assert(missing.available && !missing.extension_present &&
         !missing.native_gate_evaluated && missing.effective_raw == 0);
  assert(!ReadMarriageCharacterFertilityV1(
              character.data(), 0, true, false).available);
}
