#pragma once

// Source candidate: same-query raw link observation only. No native mutator,
// getter, command submission, hooks or game-process access is performed here.
#include "xar_bridge/army_regiment_character_role_v1.hpp"
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004::regiment_character_role {

struct CharacterResolution {
  std::uintptr_t object = 0;
  bool used_fallback = false;
};
struct Access {
  void *context = nullptr;
  bool (*read)(void *, std::uintptr_t, void *, std::size_t) = nullptr;
  bool (*resolve_character)(void *, std::int32_t, CharacterResolution &) = nullptr;
};
using Snapshot = game::ArmyRegimentCharacterRoleV1;

template<class T>
inline std::optional<T> Field(const Access &access, std::uintptr_t object,
                              std::size_t offset) noexcept {
  T value{};
  if (!object || !access.read || !access.read(access.context, object + offset, &value, sizeof value))
    return std::nullopt;
  return value;
}

inline Snapshot Read(const Access &access, std::string_view executable_sha256,
                     std::uintptr_t resolved_arrg, std::int32_t arrg_id,
                     std::int32_t full_carmy_id) noexcept {
  Snapshot out; out.army_regiment_id = arrg_id; out.native_carmy_id = full_carmy_id;
  if (executable_sha256 != "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518" || !access.read || !access.resolve_character)
    return out;
  const auto identity = Field<std::int32_t>(access, resolved_arrg, 0x10);
  const auto magic = Field<std::uint32_t>(access, resolved_arrg, 0x14);
  out.arrg_army_id_140 = Field<std::int32_t>(access, resolved_arrg, 0x140);
  if (!identity || *identity != arrg_id || arrg_id == -1 || !magic || *magic != 0x41725267U ||
      out.arrg_army_id_140 != full_carmy_id) {
    out.unavailable_reason = "ArRg_full_generation_or_Army_backlink_mismatch";
    return out;
  }
  out.character_raw_id_148 = Field<std::int32_t>(access, resolved_arrg, 0x148);
  if (!out.character_raw_id_148) return out;
  out.status = "partial";
  if (*out.character_raw_id_148 == -1) {
    out.native_character_predicate = false;
  } else {
    CharacterResolution selected;
    if (!access.resolve_character(access.context, *out.character_raw_id_148, selected) || !selected.object)
      return out;
    out.resolution_used_fallback = selected.used_fallback;
    out.resolved_character_id = Field<std::int32_t>(access, selected.object, 0x18);
    out.character_magic_1c = Field<std::uint32_t>(access, selected.object, 0x1C);
    if (!out.resolved_character_id || !out.character_magic_1c) return out;
    if (!selected.used_fallback && out.resolved_character_id != out.character_raw_id_148) {
      out.unavailable_reason = "Character_full_generation_resolution_mismatch";
      return out;
    }
    out.native_character_predicate = *out.character_magic_1c == 0x43686172U && *out.resolved_character_id != -1;
    if (*out.native_character_predicate) {
      const auto extension = Field<std::uintptr_t>(access, selected.object, 0x1B8);
      if (!extension) return out;
      out.character_extension_present = *extension != 0;
      if (*extension) {
        out.extension_army_id_f4 = Field<std::int32_t>(access, *extension, 0xF4);
        out.extension_arrg_id_f8 = Field<std::int32_t>(access, *extension, 0xF8);
        if (!out.extension_army_id_f4 || !out.extension_arrg_id_f8) return out;
      }
      if (Field<std::uintptr_t>(access, selected.object, 0x1B8) != extension ||
          Field<std::int32_t>(access, selected.object, 0x18) != out.resolved_character_id ||
          Field<std::uint32_t>(access, selected.object, 0x1C) != out.character_magic_1c ||
          (*extension && (Field<std::int32_t>(access, *extension, 0xF4) != out.extension_army_id_f4 ||
                          Field<std::int32_t>(access, *extension, 0xF8) != out.extension_arrg_id_f8))) {
        out.unavailable_reason = "Character_instance_changed_during_current_copy";
        return out;
      }
    }
  }
  out.same_ArRg_instance_after = Field<std::int32_t>(access, resolved_arrg, 0x10) == identity &&
      Field<std::uint32_t>(access, resolved_arrg, 0x14) == magic &&
      Field<std::int32_t>(access, resolved_arrg, 0x140) == out.arrg_army_id_140 &&
      Field<std::int32_t>(access, resolved_arrg, 0x148) == out.character_raw_id_148;
  if (!out.same_ArRg_instance_after) {
    out.unavailable_reason = "ArRg_instance_changed_during_current_copy";
    return out;
  }
  out.status = "available";
  out.unavailable_reason = {};
  return out;
}

} // namespace xar::ck3_12004::regiment_character_role
