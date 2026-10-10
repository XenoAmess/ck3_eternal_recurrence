#include "xar_bridge/conception_reverse_close_or_extended_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_family_abi.hpp"

#if defined(_MSC_VER)
#include <windows.h>
#endif

namespace xar::ck3_12004 {
namespace {

constexpr std::uint32_t kCharacterMagic = 0x43686172U;
constexpr std::uint32_t kInvalidFullId = 0xFFFFFFFFU;

bool ReadOwnedIdentity(
    const ConceptionReverseCloseOrExtended12004Bindings &bindings,
    std::uintptr_t character, std::uint32_t expected_full_id) noexcept {
  std::uint32_t magic = 0, full_id = 0;
  return character != 0 && expected_full_id != kInvalidFullId &&
      bindings.read_memory(bindings.read_context,
          reinterpret_cast<const void *>(character + 0x1C), &magic,
          sizeof(magic)) && magic == kCharacterMagic &&
      bindings.read_memory(bindings.read_context,
          reinterpret_cast<const void *>(character + 0x18), &full_id,
          sizeof(full_id)) && full_id == expected_full_id;
}

// Same narrow native read boundary already used by family readers. It carries
// only POD arguments; output publication remains outside the SEH boundary.
bool InvokeReverseGetter(
    ConceptionReverseCloseOrExtended12004Getter getter,
    std::uintptr_t second, std::uintptr_t first, bool &value) noexcept {
#if defined(_MSC_VER)
  __try {
    value = getter(reinterpret_cast<void *>(second),
                   reinterpret_cast<void *>(first));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  try {
    value = getter(reinterpret_cast<void *>(second),
                   reinterpret_cast<void *>(first));
    return true;
  } catch (...) {
    return false;
  }
#endif
}

} // namespace

ConceptionReverseCloseOrExtended12004Bindings
BindConceptionReverseCloseOrExtended12004(
    std::uintptr_t module_base, std::string_view executable_sha256,
    ConceptionReverseCloseOrExtended12004ReadMemory read_memory,
    void *read_context) noexcept {
  if (module_base == 0 || executable_sha256 != kExecutableSha256 ||
      read_memory == nullptr) return {};
  // Exact same typed getter/qualified actual4 constant used by the existing
  // FamilyBreakPenaltyImage binder. No penalty resources or other feature
  // bindings are needed to supply this one already-qualified readonly input.
  return {true, module_base,
      reinterpret_cast<ConceptionReverseCloseOrExtended12004Getter>(
          module_base + kFamilyCloseOrExtendedFamilyRva),
      read_memory, read_context};
}

ConceptionReverseCloseOrExtended12004Read
ReadConceptionReverseCloseOrExtended12004(
    const ConceptionReverseCloseOrExtended12004Bindings &bindings,
    std::uintptr_t second_character, std::uint32_t expected_second_full_id,
    std::uintptr_t first_character,
    std::uint32_t expected_first_full_id) noexcept {
  ConceptionReverseCloseOrExtended12004Read output;
  if (!bindings.enabled || bindings.module_base == 0 ||
      bindings.getter == nullptr || bindings.read_memory == nullptr)
    return output;
  if (!ReadOwnedIdentity(bindings, second_character, expected_second_full_id) ||
      !ReadOwnedIdentity(bindings, first_character, expected_first_full_id)) {
    output.unavailable_reason =
        "native_reverse_close_or_extended_owned_identity_unavailable";
    return output;
  }
  bool value = false;
  if (!InvokeReverseGetter(bindings.getter, second_character,
                           first_character, value)) {
    output.unavailable_reason =
        "native_reverse_close_or_extended_getter_unavailable";
    return output;
  }
  if (!ReadOwnedIdentity(bindings, second_character, expected_second_full_id) ||
      !ReadOwnedIdentity(bindings, first_character, expected_first_full_id)) {
    output.unavailable_reason =
        "native_reverse_close_or_extended_owned_identity_changed";
    return output;
  }
  output.alternate_close_or_extended = value;
  output.status = "available";
  output.unavailable_reason = {};
  return output;
}

} // namespace xar::ck3_12004
