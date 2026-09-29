#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace xar::bridge {

inline constexpr std::uintptr_t kMarriageFertilityGateRvaV1 = 0x260FAF0;
inline constexpr std::size_t kMarriageFertilityExtensionOffsetV1 = 0x1A8;
inline constexpr std::size_t kMarriageFertilityRawOffsetV1 = 0x2E0;

using MarriageFertilityGateV1 = bool (*)(void *character);

struct MarriageCharacterFertilityReadV1 {
  bool available = false;
  bool extension_present = false;
  bool native_gate_evaluated = false;
  bool native_gate_allows = false;
  std::int64_t effective_raw = 0;
  friend bool operator==(const MarriageCharacterFertilityReadV1 &,
                         const MarriageCharacterFertilityReadV1 &) = default;
};

// The stock UI fertility filter and marriage AI score both use this same
// eligibility call and extension qword, falling back to zero otherwise. The
// raw scale and pair-specific future childbearing result are not established.
inline MarriageCharacterFertilityReadV1 ReadMarriageCharacterFertilityV1(
    void *character, std::uintptr_t module_base, bool exact_build_admitted,
    bool offline_fixture = false,
    MarriageFertilityGateV1 fixture_gate = nullptr) noexcept {
  MarriageCharacterFertilityReadV1 result{};
  if (character == nullptr || !exact_build_admitted) return result;
  MarriageFertilityGateV1 gate = nullptr;
  if (offline_fixture) {
    gate = fixture_gate;
  } else if (module_base != 0) {
    constexpr std::array<std::uint8_t, 16> prefix{
        0x40, 0x53, 0x48, 0x83, 0xEC, 0x20, 0x80, 0xB9,
        0x99, 0x01, 0x00, 0x00, 0x00, 0x48, 0x8B, 0xD9};
    const auto *source = reinterpret_cast<const void *>(
        module_base + kMarriageFertilityGateRvaV1);
    if (std::memcmp(source, prefix.data(), prefix.size()) == 0)
      gate = reinterpret_cast<MarriageFertilityGateV1>(
          module_base + kMarriageFertilityGateRvaV1);
  }
  if (gate == nullptr) return result;
  result.available = true;
  void *extension = nullptr;
  std::memcpy(&extension,
              static_cast<const std::byte *>(character) +
                  kMarriageFertilityExtensionOffsetV1,
              sizeof(extension));
  if (extension == nullptr) return result;
  result.extension_present = true;
  result.native_gate_evaluated = true;
  result.native_gate_allows = gate(character);
  if (!result.native_gate_allows) return result;
  std::memcpy(&result.effective_raw,
              static_cast<const std::byte *>(extension) +
                  kMarriageFertilityRawOffsetV1,
              sizeof(result.effective_raw));
  return result;
}

} // namespace xar::bridge
