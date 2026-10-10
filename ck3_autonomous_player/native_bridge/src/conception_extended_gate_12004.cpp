#include "xar_bridge/conception_extended_gate_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

namespace xar::ck3_12004 {
namespace {

// Frozen native71-conception-extended-gate-12004.md, actual664B2929B40:
// first RDI+1B0 at2929BBD -> QWORD288 at2929BC9 -> JNE2929DC9;
// second RSI+1B0 at2929BE7 -> QWORD288 at2929BF3 -> JNE2929DC9.
constexpr std::uintptr_t kExtendedDataOffset = 0x1B0;
constexpr std::uintptr_t kExtendedGateOffset = 0x288;
constexpr std::uint32_t kCharacterMagic = 0x43686172U;

template <typename T>
bool Copy(const ConceptionExtendedGate12004Bindings &bindings,
          std::uintptr_t address, T &value) noexcept {
  return bindings.read_memory(bindings.read_context,
      reinterpret_cast<const void *>(address), &value, sizeof(value));
}

} // namespace

ConceptionExtendedGate12004Bindings BindConceptionExtendedGate12004(
    std::string_view build_version, std::string_view executable_sha256,
    ConceptionExtendedGate12004ReadMemory read_memory,
    void *read_context) noexcept {
  if (build_version != kGameVersion || executable_sha256 != kExecutableSha256 ||
      read_memory == nullptr) return {};
  return {true, read_memory, read_context};
}

ConceptionExtendedGate12004Read ReadConceptionExtendedGateForCharacter12004(
    const ConceptionExtendedGate12004Bindings &bindings,
    std::uintptr_t character, std::uint32_t expected_full_id) noexcept {
  ConceptionExtendedGate12004Read result;
  if (!bindings.enabled || bindings.read_memory == nullptr) return result;
  if (character == 0 || expected_full_id == 0xFFFFFFFFU) {
    result.unavailable_reason = "native_conception_extended_character_unavailable";
    return result;
  }
  std::uint32_t magic = 0;
  if (!Copy(bindings, character + 0x1C, magic)) {
    result.unavailable_reason = "native_conception_extended_character_magic_unread";
    return result;
  }
  if (magic != kCharacterMagic) {
    result.unavailable_reason = "native_conception_extended_character_identity_mismatch";
    return result;
  }
  std::uint32_t actual_full_id = 0;
  if (!Copy(bindings, character + 0x18, actual_full_id)) {
    result.unavailable_reason = "native_conception_extended_character_id_unread";
    return result;
  }
  if (actual_full_id == 0xFFFFFFFFU ||
      actual_full_id != expected_full_id) {
    result.unavailable_reason = "native_conception_extended_character_identity_mismatch";
    return result;
  }
  static_assert(sizeof(std::uintptr_t) == 8);
  std::uintptr_t extended = 0;
  if (!Copy(bindings, character + kExtendedDataOffset, extended)) {
    result.unavailable_reason = "native_conception_extended_pointer_unread";
    return result;
  }
  result.extended_data_present = extended != 0;
  if (extended == 0) {
    // Actual JE2929BD7 / JE2929C01 bypass the qword read entirely.
    result.blocks_pair_conception = false;
  } else {
    std::uint64_t raw = 0;
    if (!Copy(bindings, extended + kExtendedGateOffset, raw)) {
      result.unavailable_reason = "native_conception_extended_288_unread";
      return result;
    }
    result.extended_288_raw_u64 = raw;
    result.blocks_pair_conception = raw != 0;
  }
  result.status = "available";
  result.unavailable_reason = {};
  return result;
}

} // namespace xar::ck3_12004
