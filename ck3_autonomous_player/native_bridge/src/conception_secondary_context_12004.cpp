#include "xar_bridge/conception_secondary_context_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

namespace xar::ck3_12004 {
namespace {

constexpr std::uintptr_t kStoreA = 0x5D1E2F8;
constexpr std::uintptr_t kFallbackA = 0x5C67670;
constexpr std::uintptr_t kStoreB = 0x5D1E300;
constexpr std::uintptr_t kFallbackB = 0x5D1E2E0;

template <class T>
bool Copy(const ConceptionSecondaryContext12004Bindings &bindings,
          std::uintptr_t address, T &value) noexcept {
  return bindings.read_memory(bindings.read_context,
      reinterpret_cast<const void *>(address), &value, sizeof(value));
}

// Actual parent2B961BE..2B962BD and helper2BD89A0..2BD89E7:
// complete DWORD ID, low24 index, unsigned bound, stride16 pointer+8,
// complete DWORD object+8 equality. Every native miss uses its actual fallback.
bool Resolve(const ConceptionSecondaryContext12004Bindings &bindings,
             std::uintptr_t source_object, std::uintptr_t id_offset,
             std::uintptr_t store_slot, std::uintptr_t fallback_slot,
             ConceptionSecondaryContext12004Step &step) noexcept {
  std::uintptr_t store = 0;
  if (!Copy(bindings, bindings.image_base + store_slot, store)) return false;
  std::uintptr_t fallback = 0;
  // Parent preloads both fallbacks. Helper loads A fallback only on miss.
  // The observer preserves values, but avoids reading an unused fallback.
  bool miss = store == 0;
  if (!miss) {
    std::uint32_t id = 0;
    if (!Copy(bindings, source_object + id_offset, id)) return false;
    step.requested_full_id = id;
    const auto index = id & 0x00FFFFFFU;
    std::uint32_t count = 0;
    if (!Copy(bindings, store + 0x2C, count)) return false;
    miss = index >= count;
    if (!miss) {
      std::uintptr_t table = 0;
      if (!Copy(bindings, store + 0x20, table)) return false;
      std::uintptr_t object = 0;
      if (!Copy(bindings, table + std::uintptr_t{index} * 16 + 8, object))
        return false;
      miss = object == 0;
      if (!miss) {
        std::uint32_t resolved_id = 0;
        if (!Copy(bindings, object + 8, resolved_id)) return false;
        miss = resolved_id != id;
        if (!miss) {
          step.status = "resolved_full_id";
          step.resolved_object = object;
          return true;
        }
      }
    }
  }
  if (!Copy(bindings, bindings.image_base + fallback_slot, fallback))
    return false;
  // Native dereferences this fallback. A failed copy/null has no scalar result.
  if (fallback == 0) return false;
  step.status = "native_fallback";
  step.resolved_object = fallback;
  return true;
}

} // namespace

ConceptionSecondaryContext12004Bindings BindConceptionSecondaryContext12004(
    std::string_view version, std::string_view sha, std::uintptr_t image_base,
    ConceptionSecondaryContext12004ReadMemory read_memory,
    void *context) noexcept {
  if (version != kGameVersion || sha != kExecutableSha256 ||
      image_base == 0 || read_memory == nullptr) return {};
  return {true, image_base, read_memory, context};
}

ConceptionSecondaryContext12004Read
ReadConceptionSecondaryContextForCharacter12004(
    const ConceptionSecondaryContext12004Bindings &bindings,
    std::uintptr_t character, std::uint32_t expected_full_id) noexcept {
  ConceptionSecondaryContext12004Read result;
  if (!bindings.enabled || bindings.read_memory == nullptr) return result;
  std::uint32_t actual_id = 0, magic = 0;
  if (character == 0 || !Copy(bindings, character + 0x18, actual_id) ||
      !Copy(bindings, character + 0x1C, magic)) {
    result.unavailable_reason = "native_conception_secondary_character_unread";
    return result;
  }
  if (actual_id != expected_full_id || magic != 0x43686172U) {
    result.unavailable_reason = "native_conception_secondary_character_mismatch";
    return result;
  }
  if (!Resolve(bindings, character, 0xB4, kStoreA, kFallbackA,
               result.resolution[0])) {
    result.unavailable_reason = "native_conception_secondary_level1_unread";
    return result;
  }
  if (!Resolve(bindings, result.resolution[0].resolved_object, 0x4B8,
               kStoreB, kFallbackB, result.resolution[1])) {
    result.unavailable_reason = "native_conception_secondary_level2_unread";
    return result;
  }
  if (!Resolve(bindings, result.resolution[1].resolved_object, 0x98,
               kStoreA, kFallbackA, result.resolution[2])) {
    result.unavailable_reason = "native_conception_secondary_level3_unread";
    return result;
  }
  std::int32_t raw = 0;
  if (!Copy(bindings, result.resolution[2].resolved_object + 0x7D8, raw)) {
    result.unavailable_reason = "native_conception_secondary_7d8_unread";
    return result;
  }
  result.context_7d8_raw_i32 = raw;
  result.selects_alternate_relation_path = raw > 0;
  result.status = "available";
  result.unavailable_reason = {};
  return result;
}

std::optional<bool> SelectConceptionSecondaryRelationPath12004(
    std::optional<bool> first, std::optional<bool> second) noexcept {
  if (!first.has_value()) return std::nullopt;
  if (*first) return true;
  return second;
}

} // namespace xar::ck3_12004
