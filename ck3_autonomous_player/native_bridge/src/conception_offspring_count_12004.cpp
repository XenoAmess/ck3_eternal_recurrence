#include "xar_bridge/conception_offspring_count_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <limits>

namespace xar::ck3_12004 {
namespace {

// Frozen SOURCE-FREEZE.json before implementation: provider2B95ADF..2B95BAF,
// actual113B2BAE290 and reused239B C85E80. No native accessor/predicate/lock call.
constexpr std::uintptr_t kCharacterFallbackRva = 0x5C67570;
constexpr std::uintptr_t kDefaultChildrenRva = 0x5D59588;
constexpr std::uintptr_t kTraitDatabaseRva = 0x5C67528;
constexpr std::uintptr_t kInvalidTraitRva = 0x5D1E318;

template <typename T>
bool Copy(const ConceptionOffspringCount12004Bindings &bindings,
          std::uintptr_t address, T &value) noexcept {
  return address != 0 && bindings.read_memory(bindings.read_context,
      reinterpret_cast<const void *>(address), &value, sizeof(value));
}

bool ResolveChild(const ConceptionOffspringCount12004Bindings &bindings,
                  std::uint32_t id, std::uintptr_t &child,
                  ConceptionOffspringCount12004Row &row,
                  std::string_view &failure) noexcept {
  std::uintptr_t store = 0;
  if (!Copy(bindings, bindings.image_base + kCharacterStorageSlotRva, store)) {
    failure = "native_conception_offspring_character_store_unread";
    return false;
  }
  if (store != 0) {
    const auto index = id & 0xFFFFFFU;
    std::uint32_t capacity = 0;
    if (!Copy(bindings, store + 0x2C, capacity)) {
      failure = "native_conception_offspring_character_capacity_unread";
      return false;
    }
    if (index < capacity) {
      std::uintptr_t slots = 0;
      if (!Copy(bindings, store + 0x20, slots) || slots == 0 ||
          !Copy(bindings, slots + std::uintptr_t(index) * 16 + 8, child)) {
        failure = "native_conception_offspring_character_slot_unread";
        return false;
      }
      if (child != 0) {
        std::uint32_t actual_id = 0;
        if (!Copy(bindings, child + 0x18, actual_id)) {
          failure = "native_conception_offspring_child_full_id_unread";
          return false;
        }
        if (actual_id == id) {
          row.used_character_fallback = false;
          row.matched_full_id = actual_id;
          return true;
        }
      }
    }
  }
  row.used_character_fallback = true;
  if (!Copy(bindings, bindings.image_base + kCharacterFallbackRva, child) ||
      child == 0) {
    failure = "native_conception_offspring_character_fallback_unavailable";
    return false;
  }
  return true;
}

bool ReadPredicate(const ConceptionOffspringCount12004Bindings &bindings,
                   std::uintptr_t child, ConceptionOffspringCount12004Row &row,
                   std::string_view &failure) noexcept {
  std::int32_t count = 0;
  if (!Copy(bindings, child + 0x104, count)) {
    failure = "native_conception_offspring_trait_count_unread";
    return false;
  }
  row.trait_count_raw_i32 = count;
  // Actual2BAE2C0 uses equality, not signed<=0. Negative count is not a
  // native known-false branch and must not inherit the separate bit3 reader.
  if (count < 0 || std::size_t(count) > bindings.max_entries) {
    failure = "native_conception_offspring_trait_count_outside_read_budget";
    return false;
  }
  if (count == 0) {
    row.trait_4a9_equals_one = false;
    return true;
  }
  std::uintptr_t ids = 0, database = 0;
  if (!Copy(bindings, child + 0xF8, ids) || ids == 0) {
    failure = "native_conception_offspring_trait_rows_unavailable";
    return false;
  }
  if (!Copy(bindings, bindings.image_base + kTraitDatabaseRva, database) ||
      database == 0) {
    failure = "native_conception_offspring_trait_database_unavailable";
    return false;
  }
  std::int32_t definition_count = 0;
  if (!Copy(bindings, database + 0x5C, definition_count)) {
    failure = "native_conception_offspring_trait_database_count_unread";
    return false;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    std::int32_t id = 0;
    std::uintptr_t definition = 0;
    if (!Copy(bindings, ids + std::uintptr_t(index) * 4, id)) {
      failure = "native_conception_offspring_trait_id_unread";
      return false;
    }
    if (id >= 0 && id < definition_count) {
      std::uintptr_t entries = 0;
      if (!Copy(bindings, database + 0x50, entries) || entries == 0 ||
          !Copy(bindings, entries + std::uintptr_t(id) * 8, definition)) {
        failure = "native_conception_offspring_trait_definition_unread";
        return false;
      }
    } else if (!Copy(bindings, bindings.image_base + kInvalidTraitRva,
                     definition)) {
      failure = "native_conception_offspring_invalid_trait_fallback_unread";
      return false;
    }
    std::uint8_t byte = 0;
    if (definition == 0 || !Copy(bindings, definition + 0x4A9, byte)) {
      failure = "native_conception_offspring_trait_4a9_unavailable";
      return false;
    }
    if (byte == 1) {
      row.trait_4a9_equals_one = true;
      row.first_matching_trait_id = id;
      return true;
    }
  }
  row.trait_4a9_equals_one = false;
  return true;
}

} // namespace

ConceptionOffspringCount12004Bindings BindConceptionOffspringCount12004(
    std::uintptr_t image_base, std::string_view build_version,
    std::string_view executable_sha256,
    ConceptionOffspringCount12004ReadMemory read_memory, void *read_context,
    std::size_t max_entries) noexcept {
  if (image_base == 0 ||
      image_base > std::numeric_limits<std::uintptr_t>::max() - kDefaultChildrenRva - 16 ||
      build_version != kGameVersion || executable_sha256 != kExecutableSha256 ||
      read_memory == nullptr || max_entries == 0) return {};
  return {true, image_base, read_memory, read_context, max_entries};
}

ConceptionOffspringCount12004Read ReadConceptionOffspringCountForCharacter12004(
    const ConceptionOffspringCount12004Bindings &bindings,
    std::uintptr_t selected_character, std::uint32_t expected_full_id) noexcept {
  ConceptionOffspringCount12004Read result;
  if (!bindings.enabled || bindings.read_memory == nullptr) return result;
  std::uint32_t magic = 0, actual_id = 0;
  if (selected_character == 0 || expected_full_id == 0xFFFFFFFFU ||
      !Copy(bindings, selected_character + 0x1C, magic) ||
      !Copy(bindings, selected_character + 0x18, actual_id) ||
      magic != 0x43686172U || actual_id != expected_full_id) {
    result.unavailable_reason = "native_conception_offspring_selected_identity_unavailable";
    return result;
  }
  static_assert(sizeof(std::uintptr_t) == 8);
  std::uintptr_t family = 0;
  if (!Copy(bindings, selected_character + 0x1A8, family)) {
    result.unavailable_reason = "native_conception_offspring_family_pointer_unread";
    return result;
  }
  result.family_component_present = family != 0;
  const auto list = family == 0 ? bindings.image_base + kDefaultChildrenRva :
      family + 0x38;
  std::uintptr_t ids = 0;
  std::int32_t count = 0;
  if (!Copy(bindings, list, ids) || !Copy(bindings, list + 0xC, count)) {
    result.unavailable_reason = "native_conception_offspring_array_unread";
    return result;
  }
  result.offspring_list_count_raw_i32 = count;
  if (count < 0 || std::size_t(count) > bindings.max_entries) {
    result.unavailable_reason = "native_conception_offspring_count_outside_read_budget";
    return result;
  }
  if (count > 0 && ids == 0) {
    result.unavailable_reason = "native_conception_offspring_ids_unavailable";
    return result;
  }
  std::int32_t native_count = 0;
  for (std::int32_t index = 0; index < count; ++index) {
    ConceptionOffspringCount12004Row row;
    if (!Copy(bindings, ids + std::uintptr_t(index) * 4, row.requested_full_id)) {
      result.unavailable_reason = "native_conception_offspring_id_unread";
      return result;
    }
    result.rows.push_back(row);
    auto &current = result.rows.back();
    std::uintptr_t child = 0;
    if (!ResolveChild(bindings, current.requested_full_id, child, current,
                      result.unavailable_reason)) return result;
    std::uint64_t raw = 0;
    if (!Copy(bindings, child + 0x1D0, raw)) {
      result.unavailable_reason = "native_conception_offspring_child_1d0_unread";
      return result;
    }
    current.character_1d0_raw_u64 = raw;
    if (raw != 0) {
      current.counted = false;
      continue;
    }
    if (!ReadPredicate(bindings, child, current, result.unavailable_reason))
      return result;
    current.counted = !*current.trait_4a9_equals_one;
    if (*current.counted) ++native_count;
  }
  result.native_count = native_count;
  result.status = "available";
  result.unavailable_reason = {};
  return result;
}

} // namespace xar::ck3_12004
