#include "xar_bridge/ck3_12004_conception_pair_max_input.hpp"

#include <array>

namespace xar::ck3_12004 {
namespace {

// Source54 entry: MOV saved RBX, PUSH RDI, SUB RSP, CMP type DWORD 'Char'.
constexpr std::array<std::uint8_t, 17> kEntryPrefix{
    0x48, 0x89, 0x5C, 0x24, 0x10, 0x57, 0x48, 0x83, 0xEC,
    0x20, 0x81, 0x79, 0x1C, 0x72, 0x61, 0x68, 0x43};

bool FullIdMatches(const ConceptionPairMaxInputBindings &bindings,
                   std::uintptr_t character, std::uint32_t full_id) noexcept {
  if (character == 0 || full_id == 0xFFFFFFFFU) return false;
  std::uint32_t observed = 0xFFFFFFFFU;
  return bindings.read_memory(bindings.memory_context,
             reinterpret_cast<const void *>(character + kCharacterFullIdOffset),
             &observed, sizeof(observed)) && observed == full_id;
}

// The closed261B helper and its reused140B highest-tier child only read native
// receiver/global fields. Their writes are saved registers on the native stack.
// The existing query owns same-frame/read access and calling-thread admission.
bool InvokeReadOnlyGetter(NativeConceptionLineageTierMax getter,
                         std::uintptr_t character,
                         std::int32_t &raw) noexcept {
#if defined(_WIN32) && defined(_MSC_VER)
  __try {
    raw = getter(reinterpret_cast<void *>(character));
    return true;
  } __except (1) {
    return false;
  }
#else
  (void)getter;
  (void)character;
  (void)raw;
  return false;
#endif
}

} // namespace

ConceptionPairMaxInputBindings BindConceptionPairMaxInputImage(
    std::string_view build_version, std::string_view executable_sha256,
    std::uintptr_t module_base, ConceptionPairMaxReadMemory read_memory,
    void *memory_context) noexcept {
  ConceptionPairMaxInputBindings bindings{};
  if (build_version != kGameVersion || executable_sha256 != kExecutableSha256) {
    bindings.unavailable_reason = "exact_build_not_admitted";
    return bindings;
  }
  if (module_base == 0 || read_memory == nullptr) return bindings;
  const auto entry = module_base + kConceptionLineageTierMaxRva;
  std::array<std::uint8_t, kEntryPrefix.size()> actual{};
  if (!read_memory(memory_context, reinterpret_cast<const void *>(entry),
                   actual.data(), actual.size()) || actual != kEntryPrefix) {
    bindings.unavailable_reason = "getter_signature_unavailable";
    return bindings;
  }
  bindings.enabled = true;
  bindings.unavailable_reason = {};
  bindings.read_lineage_tier_max =
      reinterpret_cast<NativeConceptionLineageTierMax>(entry);
  bindings.read_memory = read_memory;
  bindings.memory_context = memory_context;
  return bindings;
}

ConceptionPairMaxInput ReadConceptionPairMaxInput(
    const ConceptionPairMaxInputBindings &bindings,
    std::uintptr_t first, std::uint32_t first_full_id,
    std::uintptr_t second, std::uint32_t second_full_id) noexcept {
  ConceptionPairMaxInput result{};
  result.first_full_id = first_full_id;
  result.second_full_id = second_full_id;
  if (!bindings.enabled || bindings.read_memory == nullptr ||
      bindings.read_lineage_tier_max == nullptr) {
    result.unavailable_reason = bindings.unavailable_reason;
    return result;
  }
  std::int32_t first_raw = 0;
  std::int32_t second_raw = 0;
  const bool first_available = FullIdMatches(bindings, first, first_full_id) &&
      InvokeReadOnlyGetter(bindings.read_lineage_tier_max, first, first_raw);
  if (first_available) result.first_lineage_tier_max_raw = first_raw;
  const bool second_available = FullIdMatches(bindings, second, second_full_id) &&
      InvokeReadOnlyGetter(bindings.read_lineage_tier_max, second, second_raw);
  if (second_available) result.second_lineage_tier_max_raw = second_raw;
  if (!first_available || !second_available) {
    result.unavailable_reason = !first_available ? "first_helper_unavailable"
                                                : "second_helper_unavailable";
    return result;
  }
  const bool take_second = first_raw < second_raw;
  result.pair_lineage_tier_max_raw = take_second ? second_raw : first_raw;
  result.maximum_return_role = take_second ? ConceptionPairMaxReturnRole::second
                                          : ConceptionPairMaxReturnRole::first;
  result.status = "available";
  result.unavailable_reason = {};
  return result;
}

} // namespace xar::ck3_12004
