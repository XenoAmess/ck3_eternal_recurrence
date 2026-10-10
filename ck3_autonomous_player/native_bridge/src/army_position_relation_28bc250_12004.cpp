#include "xar_bridge/army_position_relation_28bc250_12004.hpp"

namespace xar::ck3_12004 {
namespace {

template <class T>
bool Copy(const ArmyRegularCoreReadonlyAccess12004 &access,
          std::uintptr_t address, T &value) noexcept {
  return access.read != nullptr &&
      access.read(access.read_context, address, &value, sizeof(value));
}

} // namespace

ArmyPositionRelation28BC25012004 ReadArmyPositionRelation28BC25012004(
    const ArmyRegularCoreReadonlyAccess12004 &access,
    std::uintptr_t owner, std::uintptr_t toward) noexcept {
  ArmyPositionRelation28BC25012004 out{};
  if (access.read == nullptr || owner == 0 || toward == 0) {
    out.unavailable_reason = "relation_lookup_receiver_unavailable";
    return out;
  }
  std::uintptr_t pair_map = 0;
  if (!Copy(access, owner + 0x1B0, pair_map)) {
    out.unavailable_reason = "relation_lookup_input_unreadable";
    return out;
  }

  std::uintptr_t relation = 0;
  bool matching_row = false;
  if (pair_map != 0) {
    std::int32_t count = 0;
    if (!Copy(access, pair_map + 0x2C, count)) {
      out.unavailable_reason = "relation_count_unreadable";
      return out;
    }
    if (count < 0 || static_cast<std::size_t>(count) >
                         access.maximum_occurrences) {
      out.unavailable_reason = "relation_count_outside_capture_bound";
      return out;
    }
    std::uintptr_t rows = 0;
    std::uint32_t toward_full_id = 0;
    if (!Copy(access, pair_map + 0x20, rows) ||
        !Copy(access, toward + 0x18, toward_full_id)) {
      out.unavailable_reason = "relation_lookup_input_unreadable";
      return out;
    }
    if (count != 0) {
      if (rows == 0) {
        out.unavailable_reason = "relation_vector_unavailable";
        return out;
      }
      std::size_t first = 0;
      std::size_t end = static_cast<std::size_t>(count);
      while (first < end) {
        const auto middle = first + (end - first) / 2;
        std::uint32_t stored_full_id = 0;
        if (!Copy(access, rows + middle * 16, stored_full_id)) {
          out.unavailable_reason = "relation_key_unreadable";
          return out;
        }
        // Held CMP/CMOVB use unsigned complete ID bits, not index24.
        if (stored_full_id < toward_full_id) first = middle + 1;
        else end = middle;
      }
      if (first < static_cast<std::size_t>(count)) {
        std::uint32_t stored_full_id = 0;
        if (!Copy(access, rows + first * 16, stored_full_id)) {
          out.unavailable_reason = "relation_key_unreadable";
          return out;
        }
        if (stored_full_id == toward_full_id) {
          if (!Copy(access, rows + first * 16 + 8, relation)) {
            out.unavailable_reason = "relation_pointer_unreadable";
            return out;
          }
          matching_row = true;
        }
      }
    }
  }
  if (!matching_row) {
    if (access.image_base == 0 || !Copy(
            access, access.image_base + kArmyPositionRelationFallbackSlot12004,
            relation)) {
      out.unavailable_reason = "relation_fallback_unreadable";
      return out;
    }
  }
  out.relation_identity = relation;
  std::int32_t raw_war_id = -1;
  if (relation == 0 || !Copy(access, relation + 0x20, raw_war_id)) {
    out.unavailable_reason = "relation_war_id_unreadable";
    return out;
  }
  out.war_id = raw_war_id;
  return out;
}

} // namespace xar::ck3_12004
