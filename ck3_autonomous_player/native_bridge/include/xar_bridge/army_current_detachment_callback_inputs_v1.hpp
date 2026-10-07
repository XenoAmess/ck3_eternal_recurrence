#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {

struct ArmyCurrentDetachmentCallbackRecordV1 {
  std::int32_t native_index = 0;
  std::optional<std::string> record_identity;
  std::optional<std::string> vtable_identity;
  std::optional<std::string> slot0_target_identity;
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::string> unavailable_reason;
};

struct ArmyCurrentDetachmentCallbackIncomingV1 {
  std::vector<std::int32_t> seed_incoming_native_indices;
  std::optional<std::string> arrg_identity;
  std::optional<std::uint32_t> arrg_full_id_u32;
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::string> unavailable_reason;
  std::optional<std::string> arrg_primary_vtable_identity;
  std::optional<std::string> arrg_primary_slot0_target_identity;
  std::optional<bool> data_pointer_present;
  std::optional<std::string> data_buffer_identity;
  std::optional<std::int32_t> data_count_2c_raw_i32;
  std::optional<std::int32_t> data_capacity_28_raw_i32;
  std::optional<std::string> data_allocator_identity;
  std::optional<std::string> data_allocator_vtable_identity;
  std::optional<std::string> data_allocator_slot10_target_identity;
  std::vector<ArmyCurrentDetachmentCallbackRecordV1> records;
};

// Standalone current selected-callback inputs, not a callback execution trace.
struct ArmyCurrentDetachmentCallbackInputsV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::string> unavailable_reason;
  bool seed_selection_ready = false;
  bool seed_roster_ready = false;
  std::optional<std::int64_t> current_date_storage_raw64;
  std::optional<std::int32_t> source_parent_wrapper_mode_i32;
  std::optional<std::string> known_primary_vtable_identity;
  std::optional<std::string> known_primary_slot0_target_identity;
  std::optional<std::string> known_core_identity;
  std::optional<std::string> known_mode0_record_callback_identity;
  std::optional<std::string> known_secondary_base_vtable_identity;
  std::vector<ArmyCurrentDetachmentCallbackIncomingV1> incoming;
};

} // namespace xar::game

namespace xar::ck3_12004 {
// Exact4 source witnesses only. None is installed or invoked as a callback.
struct CurrentDetachmentCallbackBindings12004 {
  bool enabled = false;
  std::optional<std::int32_t> source_parent_wrapper_mode_i32;
  const void *known_primary_vtable = nullptr;
  const void *known_primary_slot0_target = nullptr;
  const void *known_core = nullptr;
  const void *known_mode0_record_callback = nullptr;
  const void *known_secondary_base_vtable = nullptr;
};
} // namespace xar::ck3_12004
