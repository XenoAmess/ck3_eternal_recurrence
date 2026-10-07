#pragma once

#include "xar_bridge/army_current_character_detachment_inputs_v1.hpp"
#include "xar_bridge/ck3_12003_current_detachment_data.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <string_view>
#include <utility>

namespace xar::ck3_12004 {

inline CurrentCharacterDetachmentBindings12004 BindCurrentCharacterDetachmentInputs12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  CurrentCharacterDetachmentBindings12004 out{};
  if (!image_base || executable_sha256 != kExecutableSha256) return out;
  out.enabled = true;
  out.source_parent = reinterpret_cast<const void *>(image_base + 0x28CBE50);
  return out;
}

namespace current_character_detachment_detail {
using ck3_12003::daily_assault_table_detail::Read;
using ck3_12003::daily_assault_table_detail::Identity;
using ck3_12003::candidate_mapper_detail::CapturedPointer;

inline game::ArmyCharacterDetachmentResolutionV1 CopyResolution(
    const game::ArmyDailyAssaultResolutionV1 &seed) {
  game::ArmyCharacterDetachmentResolutionV1 out{};
  out.status = seed.status; out.ready = seed.ready;
  if (!seed.unavailable_reason.empty()) out.unavailable_reason = seed.unavailable_reason;
  out.requested_full_id_u32 = seed.requested_full_id_u32;
  out.registry_loaded = seed.registry_loaded;
  out.registry_capacity_u32 = seed.registry_capacity_u32;
  out.registry_index_u32 = seed.registry_index_u32;
  out.indexed_identity = seed.indexed_identity;
  out.indexed_full_id_u32 = seed.indexed_full_id_u32;
  out.selection = seed.selection; out.used_fallback = seed.used_fallback;
  out.object_identity = seed.object_identity;
  out.selected_full_id_u32 = seed.selected_full_id_u32;
  return out;
}

struct Resolved {
  const void *object = nullptr;
  game::ArmyCharacterDetachmentResolutionV1 observation{};
};

// Actual28CBE50 selects registry first. A later object's member ID is only
// consumed when that registry is nonnull; source fallback IDs are context.
inline Resolved Resolve(
    const ck3_12003::CurrentDetachmentDataBindings12003 &binding,
    const void *registry_slot, const void *fallback_slot,
    std::optional<std::uint32_t> &requested,
    const void *member_object = nullptr,
    std::optional<std::size_t> member_offset = std::nullopt) {
  Resolved result{};
  auto &out = result.observation;
  out.requested_full_id_u32 = requested;
  const auto fail = [&](const char *reason) {
    out.status = "partial"; out.unavailable_reason = reason; return result;
  };
  const auto available = [&]() {
    out.status = "available"; out.ready = true; return result;
  };
  const auto registry = Read<const void *>(binding.common, registry_slot);
  if (!registry) return fail("character_detachment_registry_unavailable");
  out.registry_loaded = *registry != nullptr;
  if (*registry) {
    if (member_offset) requested = Read<std::uint32_t>(binding.common, member_object, *member_offset);
    out.requested_full_id_u32 = requested;
    if (!requested) return fail("character_detachment_demanded_full_id_unavailable");
    out.registry_index_u32 = *requested & 0xFFFFFFU;
    out.registry_capacity_u32 = Read<std::uint32_t>(binding.common, *registry, 0x2C);
    if (!out.registry_capacity_u32) return fail("character_detachment_registry_count_unavailable");
    if (*out.registry_index_u32 < *out.registry_capacity_u32) {
      const auto table = Read<const void *>(binding.common, *registry, 0x20);
      if (!table || !*table) return fail("character_detachment_registry_table_unavailable");
      const auto selected = Read<const void *>(binding.common, *table,
          static_cast<std::size_t>(*out.registry_index_u32) * 16 + 8);
      if (!selected) return fail("character_detachment_registry_selected_pointer_unavailable");
      if (*selected) {
        out.indexed_identity = Identity(*selected);
        out.indexed_full_id_u32 = Read<std::uint32_t>(binding.common, *selected, 0x10);
        if (!out.indexed_full_id_u32)
          return fail("character_detachment_registry_selected_full_id_unavailable");
        if (*out.indexed_full_id_u32 == *requested) {
          out.selection = "registry_full_id"; out.used_fallback = false;
          out.object_identity = out.indexed_identity;
          out.selected_full_id_u32 = out.indexed_full_id_u32;
          result.object = *selected;
          return available();
        }
      }
    }
  }
  const auto fallback = Read<const void *>(binding.common, fallback_slot);
  if (!fallback) return fail("character_detachment_fallback_unavailable");
  out.selection = "native_fallback"; out.used_fallback = true;
  out.object_identity = Identity(*fallback);
  if (!*fallback) return fail("character_detachment_fallback_null");
  // Native uses the fallback pointer, not this optional context ID test.
  out.selected_full_id_u32 = Read<std::uint32_t>(binding.common, *fallback, 0x10);
  result.object = *fallback;
  return available();
}

inline game::ArmyCurrentCharacterDetachmentRequestV1 CaptureRequest(
    const ck3_12003::CurrentDetachmentDataBindings12003 &binding,
    const game::ArmyCurrentDetachmentIncomingV1 &seed) {
  game::ArmyCurrentCharacterDetachmentRequestV1 out{};
  out.seed_incoming_native_index = seed.native_index;
  out.arrg_identity = seed.arrg_identity;
  out.character_full_id_148_u32 = seed.character_full_id_148_u32;
  out.character_resolution = CopyResolution(seed.character_resolution);
  out.passed_province_identity = seed.passed_province_identity;
  const auto partial = [&](const char *reason) {
    out.status = "partial"; out.unavailable_reason = reason; return out;
  };
  const auto available = [&]() {
    out.status = "available"; out.ready = true; return out;
  };
  if (!out.character_full_id_148_u32)
    return partial("character_detachment_seed_character_id_unavailable");
  if (*out.character_full_id_148_u32 == 0xFFFFFFFFU) return available();
  if (!seed.character_resolution.ready)
    return partial("character_detachment_seed_character_resolution_unavailable");
  const void *character = CapturedPointer(seed.character_resolution.object_identity);
  if (!character) return partial("character_detachment_seed_character_pointer_unavailable");
  const auto extension = Read<const void *>(binding.common, character, 0x1B8);
  if (!extension) return partial("character_detachment_current_extension_pointer_unavailable");
  out.current_extension_1b8_present = *extension != nullptr;
  out.current_extension_1b8_identity = Identity(*extension);
  if (!*extension) return available();
  // Source-defined reset descriptors do not consume either before-value.
  out.extension_reset_inputs_ready = true;
  out.extension_f8_raw_u32 = Read<std::uint32_t>(binding.common, *extension, 0xF8);
  out.extension_100_raw64 = Read<std::int64_t>(binding.common, *extension, 0x100);
  auto requested_arrg = out.extension_f8_raw_u32;
  auto arrg = Resolve(binding, binding.common.arrg_registry_slot,
      binding.common.arrg_fallback_slot, requested_arrg);
  out.arrg_resolution = std::move(arrg.observation);
  auto army = Resolve(binding, binding.common.army_registry_slot,
      binding.common.army_fallback_slot, out.army_full_id_140_u32, arrg.object, 0x140);
  out.army_resolution = std::move(army.observation);
  auto unit = Resolve(binding, binding.unit_registry_slot, binding.unit_fallback_slot,
      out.unit_full_id_124_u32, army.object, 0x124);
  out.unit_resolution = std::move(unit.observation);
  out.source_chain_ready = out.arrg_resolution.ready &&
      out.army_resolution.ready && out.unit_resolution.ready;
  // Missing selected source roles remain nested partial current context only.
  return available();
}

} // namespace current_character_detachment_detail

// AUTHORED_NOTRUN. Current entry operands only. No native getter, mutator,
// constructor, extension store, callback or future-state observation is made.
inline game::ArmyCurrentCharacterDetachmentInputsV1 ReadCurrentCharacterDetachmentInputs12004(
    const CurrentCharacterDetachmentBindings12004 &binding,
    const ck3_12003::CurrentDetachmentDataBindings12003 &software_binding,
    const game::ArmyCurrentDetachmentDataInputsV1 *same_query_seed) {
  using namespace current_character_detachment_detail;
  game::ArmyCurrentCharacterDetachmentInputsV1 out{};
  const auto unavailable = [&](const char *reason) {
    out.unavailable_reason = reason; return out;
  };
  if (!binding.enabled)
    return unavailable("current_character_detachment_exact4_bindings_unavailable");
  out.source_parent_identity = Identity(binding.source_parent);
  if (same_query_seed) {
    out.seed_selection_ready = same_query_seed->selection_ready;
    out.seed_roster_ready = same_query_seed->roster_ready;
    out.current_date_storage_raw64 = same_query_seed->current_date_storage_raw64;
  }
  if (!software_binding.common.enabled)
    return unavailable("current_character_detachment_software_read_bindings_unavailable");
  if (!same_query_seed)
    return unavailable("current_character_detachment_same_query_seed_unavailable");
  bool complete = out.seed_selection_ready && out.seed_roster_ready;
  for (const auto &seed : same_query_seed->incoming) {
    auto request = CaptureRequest(software_binding, seed);
    complete = complete && request.ready;
    out.requests.push_back(std::move(request));
  }
  out.status = complete ? "available" : "partial";
  out.ready = complete;
  if (!complete)
    out.unavailable_reason = "current_character_detachment_seed_or_extension_inputs_partial";
  return out;
}

} // namespace xar::ck3_12004
