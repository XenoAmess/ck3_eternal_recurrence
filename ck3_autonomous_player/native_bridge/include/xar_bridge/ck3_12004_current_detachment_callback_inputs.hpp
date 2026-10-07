#pragma once

#include "xar_bridge/army_current_detachment_callback_inputs_v1.hpp"
#include "xar_bridge/ck3_12003_current_detachment_data.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <string_view>
#include <unordered_map>
#include <utility>

namespace xar::ck3_12004 {

inline CurrentDetachmentCallbackBindings12004 BindCurrentDetachmentCallbackInputs12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  CurrentDetachmentCallbackBindings12004 out{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return out;
  const auto at = [image_base](std::uintptr_t rva) {
    return reinterpret_cast<const void *>(image_base + rva);
  };
  out.enabled = true;
  out.source_parent_wrapper_mode_i32 = 0;
  out.known_primary_vtable = at(0x4744DB0);
  out.known_primary_slot0_target = at(0x2632D90);
  out.known_core = at(0x2632DD0);
  out.known_mode0_record_callback = at(0x8863D0);
  out.known_secondary_base_vtable = at(0x4744DF8);
  return out;
}

namespace current_detachment_callback_detail {
using ck3_12003::daily_assault_table_detail::Read;
using ck3_12003::daily_assault_table_detail::Identity;
using ck3_12003::candidate_mapper_detail::CapturedPointer;
using ck3_12003::detachment_data_detail::Offset;

inline game::ArmyCurrentDetachmentCallbackIncomingV1 CaptureIncoming(
    const ck3_12003::CurrentDetachmentDataBindings12003 &binding,
    const void *arrg, std::int32_t seed_index) {
  game::ArmyCurrentDetachmentCallbackIncomingV1 out{};
  out.seed_incoming_native_indices.push_back(seed_index);
  out.arrg_identity = Identity(arrg);
  if (arrg == nullptr) {
    out.status = "partial";
    out.unavailable_reason = "current_detachment_callback_arrg_pointer_unavailable";
    return out;
  }
  out.arrg_full_id_u32 = Read<std::uint32_t>(binding.common, arrg, 0x10);
  const auto primary = Read<const void *>(binding.common, arrg);
  bool complete = primary.has_value();
  if (primary) {
    out.arrg_primary_vtable_identity = Identity(*primary);
    const auto target = Read<const void *>(binding.common, *primary);
    if (target) out.arrg_primary_slot0_target_identity = Identity(*target);
    else complete = false;
  }
  const auto data = Read<const void *>(binding.common, arrg, 0x20);
  // Independent current context. The null-data core consumes neither field.
  out.data_count_2c_raw_i32 = Read<std::int32_t>(binding.common, arrg, 0x2C);
  out.data_capacity_28_raw_i32 = Read<std::int32_t>(binding.common, arrg, 0x28);
  complete = complete && data.has_value();
  if (data) {
    out.data_pointer_present = *data != nullptr;
    out.data_buffer_identity = Identity(*data);
    if (*data != nullptr) {
      complete = complete && out.data_count_2c_raw_i32.has_value() &&
          out.data_capacity_28_raw_i32.has_value();
      if (out.data_count_2c_raw_i32 && *out.data_count_2c_raw_i32 > 0) {
        const auto captured_count = *out.data_count_2c_raw_i32;
        for (std::int64_t index = 0; index < captured_count; ++index) {
          game::ArmyCurrentDetachmentCallbackRecordV1 record{};
          record.native_index = static_cast<std::int32_t>(index);
          const void *address = Offset(*data, index * 16);
          record.record_identity = Identity(address);
          const auto vtable = Read<const void *>(binding.common, address);
          bool record_complete = vtable.has_value();
          if (vtable) {
            record.vtable_identity = Identity(*vtable);
            const auto target = Read<const void *>(binding.common, *vtable);
            if (target) record.slot0_target_identity = Identity(*target);
            else record_complete = false;
          }
          record.ready = record_complete;
          record.status = record_complete ? "available" : "partial";
          if (!record_complete) {
            record.unavailable_reason = "current_detachment_callback_record_target_unavailable";
            complete = false;
          }
          out.records.push_back(std::move(record));
        }
      }
      // The actual nonnull branch loads allocator30 and virtual slot10.
      // Capture only; invoking or expanding this resource callback is excluded.
      const auto allocator = Read<const void *>(binding.common, arrg, 0x30);
      bool allocator_complete = allocator.has_value();
      if (allocator) {
        out.data_allocator_identity = Identity(*allocator);
        const auto vtable = Read<const void *>(binding.common, *allocator);
        if (vtable) {
          out.data_allocator_vtable_identity = Identity(*vtable);
          const auto target = Read<const void *>(binding.common, *vtable, 0x10);
          if (target) out.data_allocator_slot10_target_identity = Identity(*target);
          else allocator_complete = false;
        } else allocator_complete = false;
      }
      complete = complete && allocator_complete;
    }
    // Null DATA skips record/helper/allocator reads. A signed nonpositive
    // count with nonnull DATA is a complete no-record helper input.
  }
  out.ready = complete;
  out.status = complete ? "available" : "partial";
  if (!complete)
    out.unavailable_reason = "current_detachment_callback_incoming_inputs_partial";
  return out;
}

} // namespace current_detachment_callback_detail

// AUTHORED_NOTRUN. Existing baseline supplies actual same-query ArRg pointer
// identities and current date. No registry selector, native callback, record
// method, allocator, core helper, current date reread or runtime store occurs.
inline game::ArmyCurrentDetachmentCallbackInputsV1 ReadCurrentDetachmentCallbackInputs12004(
    const CurrentDetachmentCallbackBindings12004 &binding,
    const ck3_12003::CurrentDetachmentDataBindings12003 &software_binding,
    const game::ArmyCurrentDetachmentDataInputsV1 *same_query_seed) {
  using namespace current_detachment_callback_detail;
  game::ArmyCurrentDetachmentCallbackInputsV1 out{};
  const auto unavailable = [&](std::string_view reason) {
    out.unavailable_reason = std::string(reason);
    return out;
  };
  if (!binding.enabled)
    return unavailable("current_detachment_callback_exact4_bindings_unavailable");
  out.source_parent_wrapper_mode_i32 = binding.source_parent_wrapper_mode_i32;
  out.known_primary_vtable_identity = Identity(binding.known_primary_vtable);
  out.known_primary_slot0_target_identity = Identity(binding.known_primary_slot0_target);
  out.known_core_identity = Identity(binding.known_core);
  out.known_mode0_record_callback_identity = Identity(binding.known_mode0_record_callback);
  out.known_secondary_base_vtable_identity = Identity(binding.known_secondary_base_vtable);
  if (!software_binding.common.enabled)
    return unavailable("current_detachment_callback_software_read_bindings_unavailable");
  if (same_query_seed == nullptr)
    return unavailable("current_detachment_callback_same_query_seed_unavailable");
  out.seed_selection_ready = same_query_seed->selection_ready;
  out.seed_roster_ready = same_query_seed->roster_ready;
  out.current_date_storage_raw64 = same_query_seed->current_date_storage_raw64;
  // Physical DATA/date readiness of the old seed does not gate this new raw
  // callback capture. Known pointer scope and each incoming remain independent.
  bool complete = out.seed_selection_ready && out.seed_roster_ready;
  std::unordered_map<const void *, std::size_t> captured;
  for (const auto &seed : same_query_seed->incoming) {
    const void *arrg = CapturedPointer(seed.arrg_identity);
    if (arrg != nullptr) {
      const auto found = captured.find(arrg);
      if (found != captured.end()) {
        out.incoming[found->second].seed_incoming_native_indices.push_back(seed.native_index);
        continue;
      }
      captured.emplace(arrg, out.incoming.size());
    }
    auto incoming = CaptureIncoming(software_binding, arrg, seed.native_index);
    if (arrg == nullptr) incoming.arrg_identity = seed.arrg_identity;
    complete = complete && incoming.ready;
    out.incoming.push_back(std::move(incoming));
  }
  out.ready = complete;
  out.status = complete ? "available" : "partial";
  if (!complete)
    out.unavailable_reason = "current_detachment_callback_seed_or_inputs_partial";
  return out;
}

} // namespace xar::ck3_12004
