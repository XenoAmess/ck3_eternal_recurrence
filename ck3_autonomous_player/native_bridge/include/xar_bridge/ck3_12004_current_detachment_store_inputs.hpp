#pragma once

#include "xar_bridge/army_current_detachment_store_inputs_v1.hpp"
#include "xar_bridge/ck3_12003_current_detachment_data.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <string_view>
#include <utility>

namespace xar::ck3_12004 {

inline CurrentDetachmentStoreBindings12004 BindCurrentDetachmentStoreInputs12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  CurrentDetachmentStoreBindings12004 out{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return out;
  out.enabled = true;
  out.source_parent = reinterpret_cast<const void *>(image_base + 0x2A9E620);
  out.source_parent_wrapper_mode_i32 = 0;
  return out;
}

namespace current_detachment_store_detail {
using ck3_12003::daily_assault_table_detail::Read;
using ck3_12003::daily_assault_table_detail::Identity;
using ck3_12003::detachment_data_detail::Offset;

inline game::ArmyCurrentDetachmentStoreRequestV1 CaptureRequest(
    const ck3_12003::CurrentDetachmentDataBindings12003 &binding,
    const void *registry, game::ArmyCurrentDetachmentStoreInputsV1 &family,
    std::optional<const void *> &captured_table,
    const game::ArmyCurrentDetachmentIncomingV1 &seed) {
  game::ArmyCurrentDetachmentStoreRequestV1 out{};
  out.seed_incoming_native_indices.push_back(seed.native_index);
  out.incoming_arrg_identity = seed.arrg_identity;
  out.requested_full_id_u32 = seed.arrg_full_id_u32;
  if (out.requested_full_id_u32)
    out.index_low24_u32 = *out.requested_full_id_u32 & 0xFFFFFFU;
  const auto partial = [&](const char *reason) {
    out.status = "partial"; out.unavailable_reason = reason; return out;
  };
  const auto available = [&]() {
    out.status = "available"; out.ready = true; return out;
  };
  if (!family.store_48_raw_u8)
    return partial("current_detachment_store_admission_flag_unavailable");
  if (*family.store_48_raw_u8 != 0) return available();
  if (!out.requested_full_id_u32)
    return partial("current_detachment_store_requested_full_id_unavailable");
  if (!family.slot_count_2c_raw_u32)
    return partial("current_detachment_store_slot_count_unavailable");
  if (*out.index_low24_u32 >= *family.slot_count_2c_raw_u32) return available();
  // Table20 is demanded only by an in-range request after byte48 admitted.
  if (!captured_table) {
    captured_table = Read<const void *>(binding.common, registry, 0x20);
    if (captured_table) family.slot_table_identity = Identity(*captured_table);
  }
  if (!captured_table || !*captured_table)
    return partial("current_detachment_store_slot_table_unavailable");
  const void *slot = Offset(*captured_table,
      static_cast<std::int64_t>(*out.index_low24_u32) * 16);
  out.slot_identity = Identity(slot);
  const auto selected = Read<const void *>(binding.common, slot, 8);
  if (!selected) return partial("current_detachment_store_selected_pointer_unavailable");
  out.selected_pointer_present = *selected != nullptr;
  out.selected_object_identity = Identity(*selected);
  if (*selected == nullptr) return available();
  out.selected_full_id_10_raw_u32 = Read<std::uint32_t>(binding.common, *selected, 0x10);
  if (!out.selected_full_id_10_raw_u32)
    return partial("current_detachment_store_selected_full_id_unavailable");
  if (*out.selected_full_id_10_raw_u32 != *out.requested_full_id_u32) return available();

  // Matching ID proves admission independently of subsequent context reads.
  const auto primary = Read<const void *>(binding.common, *selected);
  if (primary) {
    out.selected_primary_vtable_identity = Identity(*primary);
    const auto target = Read<const void *>(binding.common, *primary);
    if (target) out.selected_slot0_target_identity = Identity(*target);
  }
  if (family.high_water_38_raw_u32 &&
      *family.high_water_38_raw_u32 == *out.index_low24_u32) {
    for (std::int64_t index = static_cast<std::int64_t>(*out.index_low24_u32) - 1;
         index >= 0; --index) {
      game::ArmyCurrentDetachmentStoreTrailingSlotV1 row{};
      row.slot_index_u32 = static_cast<std::uint32_t>(index);
      const void *address = Offset(*captured_table, index * 16);
      row.slot_identity = Identity(address);
      const auto object = Read<const void *>(binding.common, address, 8);
      if (object) {
        row.object_pointer_present = *object != nullptr;
        row.object_identity = Identity(*object);
        row.status = "available"; row.ready = true;
      } else {
        row.status = "partial";
        row.unavailable_reason = "current_detachment_store_trailing_pointer_unavailable";
      }
      out.trailing_slot_scan.push_back(std::move(row));
      // Retain a missing-read prefix; native stops at first nonnull or -1.
      if (!object || *object != nullptr) break;
    }
  }
  return available();
}

} // namespace current_detachment_store_detail

// AUTHORED_NOTRUN. Current admission and optional suffix seed only. Never
// calls store/core/record/resource/4226F10 or fabricates post-callback values.
inline game::ArmyCurrentDetachmentStoreInputsV1 ReadCurrentDetachmentStoreInputs12004(
    const CurrentDetachmentStoreBindings12004 &binding,
    const ck3_12003::CurrentDetachmentDataBindings12003 &software_binding,
    const game::ArmyCurrentDetachmentDataInputsV1 *same_query_seed) {
  using namespace current_detachment_store_detail;
  game::ArmyCurrentDetachmentStoreInputsV1 out{};
  const auto unavailable = [&](std::string_view reason) {
    out.unavailable_reason = std::string(reason); return out;
  };
  if (!binding.enabled)
    return unavailable("current_detachment_store_exact4_bindings_unavailable");
  out.source_parent_identity = Identity(binding.source_parent);
  out.source_parent_wrapper_mode_i32 = binding.source_parent_wrapper_mode_i32;
  if (!software_binding.common.enabled)
    return unavailable("current_detachment_store_software_read_bindings_unavailable");
  if (same_query_seed == nullptr)
    return unavailable("current_detachment_store_same_query_seed_unavailable");
  out.seed_selection_ready = same_query_seed->selection_ready;
  out.seed_roster_ready = same_query_seed->roster_ready;
  out.current_date_storage_raw64 = same_query_seed->current_date_storage_raw64;
  const auto loaded_registry = Read<const void *>(software_binding.common,
      software_binding.common.arrg_registry_slot);
  const void *registry = nullptr;
  if (loaded_registry) {
    registry = *loaded_registry; out.registry_identity = Identity(registry);
  }
  out.store_48_raw_u8 = Read<std::uint8_t>(software_binding.common, registry, 0x48);
  // Independent current context; none gates the request admission predicate.
  out.active_count_3c_raw_u32 = Read<std::uint32_t>(software_binding.common, registry, 0x3C);
  out.registry_mark_4a_raw_u8 = Read<std::uint8_t>(software_binding.common, registry, 0x4A);
  out.high_water_38_raw_u32 = Read<std::uint32_t>(software_binding.common, registry, 0x38);
  out.free_head_40_raw_u32 = Read<std::uint32_t>(software_binding.common, registry, 0x40);
  if (out.store_48_raw_u8 && *out.store_48_raw_u8 == 0)
    out.slot_count_2c_raw_u32 = Read<std::uint32_t>(software_binding.common, registry, 0x2C);
  std::optional<const void *> captured_table;
  bool complete = out.seed_selection_ready && out.seed_roster_ready &&
      out.store_48_raw_u8.has_value();
  for (const auto &seed : same_query_seed->incoming) {
    if (seed.arrg_full_id_u32 && seed.arrg_identity) {
      const auto alias = std::find_if(out.requests.begin(), out.requests.end(),
          [&](const auto &request) {
            return request.requested_full_id_u32 == seed.arrg_full_id_u32 &&
                request.incoming_arrg_identity == seed.arrg_identity;
          });
      if (alias != out.requests.end()) {
        alias->seed_incoming_native_indices.push_back(seed.native_index);
        continue;
      }
    }
    auto request = CaptureRequest(software_binding, registry, out, captured_table, seed);
    complete = complete && request.ready;
    out.requests.push_back(std::move(request));
  }
  out.status = complete ? "available" : "partial";
  out.ready = complete;
  if (!complete)
    out.unavailable_reason = "current_detachment_store_seed_or_admission_inputs_partial";
  return out;
}

} // namespace xar::ck3_12004
