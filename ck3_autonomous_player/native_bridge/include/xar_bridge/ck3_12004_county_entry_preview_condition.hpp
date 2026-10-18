#pragma once
#include "xar_bridge/army_county_entry_preview_condition_v1.hpp"
#include "xar_bridge/ck3_12004_origin_adjacency.hpp"
#include "xar_bridge/ck3_12003_current_stored_context.hpp"
#include <cstddef>
#include <cstdint>
#include <optional>

namespace xar::ck3_12004::county_preview_detail {
template<class T>
inline std::optional<T> Read(const void *object, std::size_t offset) noexcept {
  return ck3_12002::current_stored_context_12003::Read<T>(object, offset);
}

inline game::ArmyCountyEntryPreviewConditionV1 Sample(
    const game::ArmyCountyEntryPreviewConditionV1 &context,
    const void *army, const void *unit, const void *actor,
    const void *source, const void *target, std::int32_t carmy_id,
    std::int32_t actor_id) {
  auto out = context;
  out.native_carmy_id = carmy_id;
  out.actor_character_id = actor_id;
  if (Read<std::int32_t>(unit, 0x10) != out.subject_army_id ||
      Read<std::int32_t>(army, 0x10) != carmy_id ||
      Read<std::int32_t>(army, 0x124) != out.subject_army_id ||
      Read<std::int32_t>(unit, 0x178) != carmy_id ||
      Read<std::int32_t>(unit, 0x174) != actor_id ||
      Read<std::int32_t>(actor, 0x18) != actor_id ||
      Read<const void *>(unit, 0x20) != source ||
      Read<std::int32_t>(source, 0x10) != out.source_province_id ||
      Read<std::int32_t>(target, 0x10) != out.target_province_id ||
      Read<std::uint32_t>(source, 0x85C) != 0x50726F76U ||
      Read<std::uint32_t>(target, 0x85C) != 0x50726F76U) {
    out.unavailable_reason = "preview_county_full_identity_unavailable";
    return out;
  }
  out.army_1d4_raw = Read<std::uint8_t>(army, 0x1D4);
  const auto source_definition = Read<const void *>(source, 8);
  const auto target_definition = Read<const void *>(target, 8);
  if (!out.army_1d4_raw || !source_definition || !*source_definition ||
      !target_definition || !*target_definition) {
    out.unavailable_reason = "preview_county_mode_or_definition_pointer_unavailable";
    return out;
  }
  out.mode = *out.army_1d4_raw == 0 ? 1 : 0;
  out.source_definition_1b_u8 = Read<std::uint8_t>(*source_definition, 0x1B);
  out.target_definition_1b_u8 = Read<std::uint8_t>(*target_definition, 0x1B);
  const auto source_county = Read<const void *>(source, 0x848);
  const auto target_county = Read<const void *>(target, 0x848);
  if (!out.source_definition_1b_u8 || !out.target_definition_1b_u8 ||
      !source_county || !target_county) {
    out.unavailable_reason = "preview_county_definition_or_county_pointer_read_failed";
    return out;
  }
  out.source_county_present = *source_county != nullptr;
  out.target_county_present = *target_county != nullptr;
  out.county_objects_differ = *source_county != *target_county;
  if (*source_county)
    out.source_county_identity = ck3_12002::current_stored_context_12003::Address(*source_county);
  if (*target_county) {
    out.target_county_identity = ck3_12002::current_stored_context_12003::Address(*target_county);
    out.target_county_magic_3e0_u32 = Read<std::uint32_t>(*target_county, 0x3E0);
    if (!out.target_county_magic_3e0_u32) {
      out.unavailable_reason = "preview_target_county_magic_read_failed";
      return out;
    }
  }
  out.inputs_observation_ready = true;
  out.unavailable_reason.clear();
  return out;
}

inline game::ArmyOriginAdjacencyV1 ReadOriginAdjacency(
    const void *source, std::int32_t source_id) {
  const auto safe_read = [](const void *base, std::size_t offset,
                            void *out, std::size_t size) noexcept {
    return base && ck3_12002::current_stored_context_12003::CopyBytes(
        out, static_cast<const std::byte *>(base) + offset, size);
  };
  return ReadOriginAdjacency12004(source, source_id, safe_read);
}

// Separate SEH leaf: it has no C++ objects that need unwinding. The bound
// predicate is called once; its internal repeated target tests are untouched.
inline bool Invoke(bool (*predicate)(void *, void *, void *, std::int32_t),
                   void *actor, void *source, void *target, std::int32_t mode,
                   bool &returned) noexcept {
#if defined(_MSC_VER)
  __try {
    returned = predicate(actor, source, target, mode);
    return true;
  } __except (1) {
    return false;
  }
#else
  returned = predicate(actor, source, target, mode);
  return true;
#endif
}
} // namespace xar::ck3_12004::county_preview_detail
