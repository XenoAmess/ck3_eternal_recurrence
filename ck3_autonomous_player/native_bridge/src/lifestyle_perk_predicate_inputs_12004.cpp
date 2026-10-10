#include "xar_bridge/lifestyle_perk_predicate_inputs_12004.hpp"
#include <limits>

namespace xar::ck3_12004::lifestyle {
namespace {
template <class T>
bool ReadAt(const LifestylePerkReadonlyAccess12004 &access,
            std::uintptr_t object, std::uintptr_t offset,
            std::optional<T> &output) noexcept {
  if (!access.read_memory || !object ||
      offset > std::numeric_limits<std::uintptr_t>::max() - object) return false;
  try {
    T value{};
    if (!access.read_memory(access.read_context, object + offset, &value, sizeof(value)))
      return false;
    output = value;
    return true;
  } catch (...) {
    return false;
  }
}
}

LifestylePerkPredicateInputs12004 ReadLifestylePerkPredicateInputs288B1B012004(
    const LifestylePerkReadonlyAccess12004 &access,
    std::uintptr_t command_identity) noexcept {
  LifestylePerkPredicateInputs12004 out{};
  out.command_identity = command_identity;
  const auto fail = [&](const char *reason) {
    out.unavailable_reason = reason;
    return out;
  };
  if (!ReadAt(access, access.module_base, 0x5C67568, out.registry_identity))
    return fail("lifestyle_perk_character_registry_unavailable");
  bool fallback = *out.registry_identity == 0;
  if (!fallback) {
    if (!ReadAt(access, command_identity, 0x20, out.requested_full_character_id_u32))
      return fail("lifestyle_perk_requested_character_full_id_unavailable");
    const auto index = *out.requested_full_character_id_u32 & 0xFFFFFFU;
    if (!ReadAt(access, *out.registry_identity, 0x2C, out.registry_capacity_u32))
      return fail("lifestyle_perk_character_registry_capacity_unavailable");
    fallback = index >= *out.registry_capacity_u32;
    if (!fallback) {
      std::optional<std::uintptr_t> data{};
      if (!ReadAt(access, *out.registry_identity, 0x20, data) ||
          !ReadAt(access, *data, static_cast<std::uintptr_t>(index) * 16 + 8,
                  out.indexed_character_identity))
        return fail("lifestyle_perk_character_registry_row_unavailable");
      fallback = *out.indexed_character_identity == 0;
      if (!fallback) {
        if (!ReadAt(access, *out.indexed_character_identity, 0x18,
                    out.indexed_character_full_id_u32))
          return fail("lifestyle_perk_indexed_character_full_id_unavailable");
        fallback = *out.indexed_character_full_id_u32 != *out.requested_full_character_id_u32;
      }
    }
  }
  out.used_fallback = fallback;
  if (fallback) {
    if (!ReadAt(access, access.module_base, 0x5C67570, out.selected_character_identity))
      return fail("lifestyle_perk_character_fallback_unavailable");
  } else {
    out.selected_character_identity = out.indexed_character_identity;
  }
  if (!ReadAt(access, *out.selected_character_identity, 0x1C,
              out.selected_character_magic_u32))
    return fail("lifestyle_perk_character_magic_unavailable");
  if (*out.selected_character_magic_u32 != 0x43686172U) {
    out.prefix_admitted = false;
    return out;
  }
  if (!ReadAt(access, *out.selected_character_identity, 0x18,
              out.selected_character_full_id_u32))
    return fail("lifestyle_perk_selected_character_full_id_unavailable");
  if (*out.selected_character_full_id_u32 == 0xFFFFFFFFU) {
    out.prefix_admitted = false;
    return out;
  }
  if (!ReadAt(access, *out.selected_character_identity, 0x1D0,
              out.selected_character_field_1d0_u64))
    return fail("lifestyle_perk_character_field_1d0_unavailable");
  if (*out.selected_character_field_1d0_u64 != 0) {
    out.prefix_admitted = false;
    return out;
  }
  if (!ReadAt(access, command_identity, 0x28, out.selected_perk_identity) ||
      !ReadAt(access, *out.selected_perk_identity, 0x38, out.selected_perk_magic_u32))
    return fail("lifestyle_perk_selected_definition_magic_unavailable");
  out.prefix_admitted = *out.selected_perk_magic_u32 == 0x4744624FU;
  return out;
}

} // namespace xar::ck3_12004::lifestyle
