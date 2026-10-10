#include "xar_bridge/conception_pair_list_bonus_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

namespace xar::ck3_12004 {
namespace {
constexpr std::uint32_t kNoId = 0xFFFFFFFFU;
constexpr std::uint32_t kCharacterMagic = 0x43686172U;
constexpr std::uintptr_t kDefaultCharacterSlot = 0x5C67570;
constexpr std::uintptr_t kDefaultChildList = 0x5D59588;

template <typename T>
bool Copy(const ConceptionPairListBonus12004Bindings &b,
          std::uintptr_t address, T &value) noexcept {
  return b.read_memory(b.read_context, reinterpret_cast<const void *>(address),
                       &value, sizeof(value));
}

bool Identity(const ConceptionPairListBonus12004Bindings &b,
              std::uintptr_t character, std::uint32_t expected) noexcept {
  std::uint32_t id = kNoId, magic = 0;
  return character != 0 && expected != kNoId &&
      Copy(b, character + 0x18, id) && id == expected &&
      Copy(b, character + 0x1C, magic) && magic == kCharacterMagic;
}

// Actual2B955C0..2B95664: resolving a stale roster ID selects the native
// default Character; no death/alive filter or direct other-ID membership.
std::optional<bool> ParentWitness(
    const ConceptionPairListBonus12004Bindings &b, std::uintptr_t list,
    std::int32_t count, std::uint32_t other_full_id) noexcept {
  if (count == 0) return false;
  if (count < 0) return std::nullopt;
  std::uintptr_t data = 0, storage = 0, fallback = 0;
  if (!Copy(b, list, data) || data == 0 ||
      !Copy(b, b.image_base + kCharacterStorageSlotRva, storage) ||
      !Copy(b, b.image_base + kDefaultCharacterSlot, fallback))
    return std::nullopt;
  for (std::int32_t i = 0; i < count; ++i) {
    std::uint32_t raw = 0;
    if (!Copy(b, data + static_cast<std::uintptr_t>(i) * 4, raw))
      return std::nullopt;
    std::uintptr_t child = 0;
    if (storage != 0) {
      std::uint32_t capacity = 0;
      if (!Copy(b, storage + 0x2C, capacity)) return std::nullopt;
      const auto index = raw & 0xFFFFFFU;
      if (index < capacity) {
        std::uintptr_t slots = 0;
        if (!Copy(b, storage + 0x20, slots) || slots == 0 ||
            !Copy(b, slots + static_cast<std::uintptr_t>(index) * 16 + 8,
                  child)) return std::nullopt;
        if (child != 0) {
          std::uint32_t actual = 0;
          if (!Copy(b, child + 0x18, actual)) return std::nullopt;
          if (actual != raw) child = 0;
        }
      }
    }
    if (child == 0) child = fallback;
    if (child == 0) return std::nullopt;
    std::uintptr_t family = 0;
    if (!Copy(b, child + 0x1A8, family)) return std::nullopt;
    if (family != 0) {
      std::uint32_t parent = kNoId;
      if (!Copy(b, family + 4, parent)) return std::nullopt;
      if (parent == other_full_id) return true;
      if (!Copy(b, family, parent)) return std::nullopt;
      if (parent == other_full_id) return true;
    }
  }
  return false;
}
} // namespace

ConceptionPairListBonus12004Bindings BindConceptionPairListBonus12004(
    std::uintptr_t image_base, std::string_view build,
    std::string_view executable_sha256,
    ConceptionPairListBonus12004ReadMemory read_memory,
    void *read_context) noexcept {
  if (image_base == 0 || build != kGameVersion ||
      executable_sha256 != kExecutableSha256 || read_memory == nullptr)
    return {};
  return {true, image_base, read_memory, read_context};
}

std::optional<bool> ConceptionPairRelationBonusCondition12004(
    bool primary_relation_match, std::optional<std::int32_t> first_count,
    std::optional<std::int32_t> second_count,
    std::optional<bool> first_witness,
    std::optional<bool> second_witness) noexcept {
  if (!primary_relation_match) return false;
  if (first_count == 0) return true;
  if (!first_count.has_value()) return std::nullopt;
  if (second_count == 0) return true;
  if (!second_count.has_value()) return std::nullopt;
  if (*first_count < 0 || *second_count < 0) return std::nullopt;
  if (!first_witness.has_value()) return std::nullopt;
  if (*first_witness) return false;
  if (!second_witness.has_value()) return std::nullopt;
  return !*second_witness;
}

ConceptionPairListBonus12004Read ReadConceptionPairListBonusForCharacters12004(
    const ConceptionPairListBonus12004Bindings &b, std::uintptr_t first,
    std::uint32_t first_full_id, std::uintptr_t second,
    std::uint32_t second_full_id) noexcept {
  ConceptionPairListBonus12004Read r;
  if (!b.enabled || b.read_memory == nullptr) return r;
  if (!Identity(b, first, first_full_id) ||
      !Identity(b, second, second_full_id)) {
    r.unavailable_reason = "conception_pair_list_character_identity_unavailable";
    return r;
  }
  std::uintptr_t first_family = 0, second_family = 0;
  if (!Copy(b, first + 0x1A8, first_family) ||
      !Copy(b, second + 0x1A8, second_family)) {
    r.unavailable_reason = "conception_pair_list_family_pointer_unread";
    return r;
  }
  std::uint32_t second_primary = kNoId, first_primary = kNoId;
  if (second_family != 0 &&
      !Copy(b, second_family + 0x14, second_primary)) {
    r.unavailable_reason = "conception_pair_list_primary_id_unread";
    return r;
  }
  if (second_primary != first_full_id && first_family != 0 &&
      !Copy(b, first_family + 0x14, first_primary)) {
    r.unavailable_reason = "conception_pair_list_primary_id_unread";
    return r;
  }
  r.primary_relation_match = second_primary == first_full_id ||
      first_primary == second_full_id;
  if (*r.primary_relation_match) {
    const auto first_list = first_family != 0 ? first_family + 0x38 :
        b.image_base + kDefaultChildList;
    const auto second_list = second_family != 0 ? second_family + 0x38 :
        b.image_base + kDefaultChildList;
    std::int32_t count = 0;
    if (!Copy(b, first_list + 0xC, count)) {
      r.unavailable_reason = "conception_pair_list_count_unread";
      return r;
    }
    r.first_child_count_raw = count;
    if (count != 0) {
      if (!Copy(b, second_list + 0xC, count)) {
        r.unavailable_reason = "conception_pair_list_count_unread";
        return r;
      }
      r.second_child_count_raw = count;
      if (count != 0) {
        r.first_list_has_second_parent_witness = ParentWitness(
            b, first_list, *r.first_child_count_raw, second_full_id);
        if (r.first_list_has_second_parent_witness == false)
          r.second_list_has_first_parent_witness = ParentWitness(
              b, second_list, count, first_full_id);
      }
    }
  }
  r.apply_relation_bonus = ConceptionPairRelationBonusCondition12004(
      *r.primary_relation_match, r.first_child_count_raw,
      r.second_child_count_raw, r.first_list_has_second_parent_witness,
      r.second_list_has_first_parent_witness);
  if (!r.apply_relation_bonus.has_value()) {
    r.unavailable_reason = "conception_pair_list_parent_witness_unavailable";
    return r;
  }
  r.apply_land_state_bonus = false;
  if (*r.apply_relation_bonus) {
    std::uintptr_t land = 0;
    if (!Copy(b, second + 0x1C0, land) ||
        (land == 0 && !Copy(b, first + 0x1C0, land))) {
      r.apply_land_state_bonus.reset();
      r.unavailable_reason = "conception_pair_list_land_state_unread";
      return r;
    }
    r.either_land_state_present = land != 0;
    r.apply_land_state_bonus = land != 0;
  }
  r.status = "available";
  r.unavailable_reason = {};
  return r;
}
} // namespace xar::ck3_12004
