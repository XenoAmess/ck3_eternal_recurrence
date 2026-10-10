#include "xar_bridge/conception_related_pair_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

namespace xar::ck3_12004 {
namespace {

constexpr std::uint32_t kInvalidId = 0xFFFFFFFFU;
constexpr std::uint32_t kCharacterMagic = 0x43686172U;
constexpr std::uintptr_t kStorageSlot = 0x5C67568;
constexpr std::uintptr_t kFallbackSlot = 0x5C67570;
constexpr std::uintptr_t kRelationOffset = 0x1A8;

struct Reader {
  const ConceptionRelatedPair12004Bindings &bindings;
  ConceptionRelatedPair12004Read &output;

  template <typename T>
  bool Copy(std::uintptr_t address, T &value,
            std::string_view failure) noexcept {
    if (address == 0 || !bindings.read_memory(bindings.read_context,
            reinterpret_cast<const void *>(address), &value, sizeof(value))) {
      output.unavailable_reason = failure;
      return false;
    }
    return true;
  }

  std::size_t RawRow(std::uintptr_t character) {
    for (std::size_t i = 0; i < output.raw_characters.size(); ++i)
      if (output.raw_characters[i].character == character) return i;
    ConceptionRelatedCharacterRaw12004 row;
    row.character = character;
    output.raw_characters.push_back(row);
    return output.raw_characters.size() - 1;
  }

  bool Valid(std::uintptr_t character, bool &valid) {
    valid = false;
    if (character == 0) {
      output.unavailable_reason =
          "native_conception_related_pair_resolved_pointer_unavailable";
      return false;
    }
    const auto index = RawRow(character);
    std::uint32_t magic = 0;
    if (!Copy(character + 0x1C, magic,
              "native_conception_related_pair_character_magic_unread"))
      return false;
    output.raw_characters[index].magic_raw_u32 = magic;
    if (magic != kCharacterMagic) return true;
    std::uint32_t full_id = 0;
    if (!Copy(character + 0x18, full_id,
              "native_conception_related_pair_character_id_unread"))
      return false;
    output.raw_characters[index].full_id_raw_u32 = full_id;
    valid = full_id != kInvalidId;
    return true;
  }

  bool OwnIdentity(std::uintptr_t character, std::uint32_t expected) {
    if (character == 0 || expected == kInvalidId) {
      output.unavailable_reason =
          "native_conception_related_pair_household_identity_unavailable";
      return false;
    }
    bool valid = false;
    if (!Valid(character, valid)) return false;
    const auto index = RawRow(character);
    if (!valid || output.raw_characters[index].full_id_raw_u32 != expected) {
      output.unavailable_reason =
          "native_conception_related_pair_household_identity_mismatch";
      return false;
    }
    return true;
  }

  bool ParentId(std::uintptr_t character, std::uint32_t position,
                std::uint32_t &id, bool &block_present) {
    if (character == 0) {
      output.unavailable_reason =
          "native_conception_related_pair_resolved_pointer_unavailable";
      return false;
    }
    const auto index = RawRow(character);
    std::uintptr_t block = 0;
    if (!Copy(character + kRelationOffset, block,
              "native_conception_related_pair_relationship_pointer_unread"))
      return false;
    block_present = block != 0;
    output.raw_characters[index].relationship_block_present = block_present;
    if (block_present) {
      if (!Copy(block + position * 4, id,
                "native_conception_related_pair_parent_id_unread"))
        return false;
    } else {
      id = kInvalidId;
      // One observed null relationship pointer supplies both native sentinels.
      output.raw_characters[index].parent_slot0_full_id = kInvalidId;
      output.raw_characters[index].parent_slot1_full_id = kInvalidId;
    }
    if (position == 0)
      output.raw_characters[index].parent_slot0_full_id = id;
    else
      output.raw_characters[index].parent_slot1_full_id = id;
    return true;
  }

  bool Resolve(std::uint32_t id, std::uintptr_t &character) {
    std::uintptr_t storage = 0;
    if (!Copy(bindings.module_base + kStorageSlot, storage,
              "native_conception_related_pair_storage_slot_unread"))
      return false;
    if (storage != 0) {
      std::uint32_t capacity = 0;
      if (!Copy(storage + 0x2C, capacity,
                "native_conception_related_pair_storage_capacity_unread"))
        return false;
      const auto index = id & 0x00FFFFFFU;
      if (index < capacity) {
        std::uintptr_t slots = 0;
        if (!Copy(storage + 0x20, slots,
                  "native_conception_related_pair_storage_array_unread"))
          return false;
        if (slots == 0) {
          output.unavailable_reason =
              "native_conception_related_pair_storage_array_unavailable";
          return false;
        }
        std::uintptr_t candidate = 0;
        if (!Copy(slots + static_cast<std::uintptr_t>(index) * 0x10 + 8,
                  candidate,
                  "native_conception_related_pair_storage_object_unread"))
          return false;
        if (candidate != 0) {
          std::uint32_t actual = 0;
          if (!Copy(candidate + 0x18, actual,
                    "native_conception_related_pair_resolved_id_unread"))
            return false;
          if (actual == id) {
            character = candidate;
            return true;
          }
        }
      }
    }
    if (!Copy(bindings.module_base + kFallbackSlot, character,
              "native_conception_related_pair_fallback_slot_unread"))
      return false;
    if (character == 0) {
      output.unavailable_reason =
          "native_conception_related_pair_fallback_pointer_unavailable";
      return false;
    }
    return true;
  }

  // Actual28B3C10: c.parent[0/1] compared with s through matching positions.
  // Every return below separates a known predicate value from copy success.
  bool H(std::uintptr_t c, std::uintptr_t s, bool &result) {
    result = false;
    for (std::uint32_t c_position = 0; c_position < 2; ++c_position) {
      std::uint32_t parent_id = 0;
      bool block_present = false;
      if (!ParentId(c, c_position, parent_id, block_present)) return false;
      std::uintptr_t parent = 0;
      if (!Resolve(parent_id, parent)) return false;
      bool parent_valid = false;
      if (!Valid(parent, parent_valid)) return false;
      if (!parent_valid || parent == s) continue;
      bool s_valid = false;
      if (!Valid(s, s_valid)) return false;
      if (!s_valid) continue;
      for (std::uint32_t position = 0; position < 2; ++position) {
        std::uint32_t s_parent_id = 0;
        if (!ParentId(s, position, s_parent_id, block_present)) return false;
        std::uintptr_t s_parent = 0;
        if (!Resolve(s_parent_id, s_parent)) return false;
        bool s_parent_valid = false;
        if (!Valid(s_parent, s_parent_valid)) return false;
        if (!s_parent_valid) continue;
        const auto s_parent_row = RawRow(s_parent);
        const auto s_parent_full_id =
            *output.raw_characters[s_parent_row].full_id_raw_u32;
        std::uint32_t comparison_id = 0;
        if (!ParentId(parent, position, comparison_id, block_present))
          return false;
        if (block_present && comparison_id == s_parent_full_id) {
          result = true;
          return true;
        }
      }
    }
    return true;
  }

  // Actual28B3E50: resolve first parent[0], H(second,parent), then parent[1].
  bool E(std::uintptr_t first, std::uintptr_t second, bool &result) {
    result = false;
    for (std::uint32_t position = 0; position < 2; ++position) {
      std::uint32_t parent_id = 0;
      bool block_present = false;
      if (!ParentId(first, position, parent_id, block_present)) return false;
      std::uintptr_t parent = 0;
      if (!Resolve(parent_id, parent) || !H(second, parent, result)) return false;
      if (result) return true;
    }
    return true;
  }
};

} // namespace

ConceptionRelatedPair12004Bindings BindConceptionRelatedPair12004(
    std::string_view build_version, std::string_view executable_sha256,
    std::uintptr_t module_base,
    ConceptionRelatedPair12004ReadMemory read_memory,
    void *read_context) noexcept {
  if (build_version != kGameVersion || executable_sha256 != kExecutableSha256 ||
      module_base == 0 || read_memory == nullptr) return {};
  return {true, module_base, read_memory, read_context};
}

ConceptionRelatedPair12004Read ReadConceptionRelatedPairForHousehold12004(
    const ConceptionRelatedPair12004Bindings &bindings,
    std::uintptr_t first_character, std::uint32_t expected_first_full_id,
    std::uintptr_t second_character,
    std::uint32_t expected_second_full_id) noexcept {
  ConceptionRelatedPair12004Read output;
  if (!bindings.enabled || bindings.module_base == 0 ||
      bindings.read_memory == nullptr) return output;
  Reader reader{bindings, output};
  if (!reader.OwnIdentity(first_character, expected_first_full_id) ||
      !reader.OwnIdentity(second_character, expected_second_full_id))
    return output;
  bool result = false;
  if (!reader.H(second_character, first_character, result)) return output;
  output.second_to_first_28b3c10 = result;
  if (!result) {
    if (!reader.H(first_character, second_character, result)) return output;
    output.first_to_second_28b3c10 = result;
    if (!result) {
      if (!reader.E(first_character, second_character, result)) return output;
      output.first_second_28b3e50 = result;
    }
  }
  output.related_pair_predicate = result;
  output.status = "available";
  output.unavailable_reason = {};
  return output;
}

} // namespace xar::ck3_12004
