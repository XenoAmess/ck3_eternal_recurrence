#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {

struct ArmyCurrentDetachmentStoreTrailingSlotV1 {
  std::uint32_t slot_index_u32 = 0;
  std::optional<std::string> slot_identity;
  std::optional<bool> object_pointer_present;
  std::optional<std::string> object_identity;
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::string> unavailable_reason;
};

struct ArmyCurrentDetachmentStoreRequestV1 {
  std::vector<std::int32_t> seed_incoming_native_indices;
  std::optional<std::string> incoming_arrg_identity;
  std::optional<std::uint32_t> requested_full_id_u32;
  std::optional<std::uint32_t> index_low24_u32;
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::string> unavailable_reason;
  std::optional<std::string> slot_identity;
  std::optional<bool> selected_pointer_present;
  std::optional<std::string> selected_object_identity;
  std::optional<std::uint32_t> selected_full_id_10_raw_u32;
  std::optional<std::string> selected_primary_vtable_identity;
  std::optional<std::string> selected_slot0_target_identity;
  std::vector<ArmyCurrentDetachmentStoreTrailingSlotV1> trailing_slot_scan;
};

// Current registry and selected-slot inputs. Suffix context is independent of
// admission and is never labeled an actual post-callback store observation.
struct ArmyCurrentDetachmentStoreInputsV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::string> unavailable_reason;
  bool seed_selection_ready = false;
  bool seed_roster_ready = false;
  std::optional<std::int64_t> current_date_storage_raw64;
  std::optional<std::string> source_parent_identity;
  std::optional<std::int32_t> source_parent_wrapper_mode_i32;
  std::optional<std::string> registry_identity;
  std::optional<std::uint8_t> store_48_raw_u8;
  std::optional<std::uint32_t> slot_count_2c_raw_u32;
  std::optional<std::string> slot_table_identity;
  std::optional<std::uint32_t> active_count_3c_raw_u32;
  std::optional<std::uint8_t> registry_mark_4a_raw_u8;
  std::optional<std::uint32_t> high_water_38_raw_u32;
  std::optional<std::uint32_t> free_head_40_raw_u32;
  std::vector<ArmyCurrentDetachmentStoreRequestV1> requests;
};

} // namespace xar::game

namespace xar::ck3_12004 {
struct CurrentDetachmentStoreBindings12004 {
  bool enabled = false;
  const void *source_parent = nullptr;
  std::optional<std::int32_t> source_parent_wrapper_mode_i32;
};
} // namespace xar::ck3_12004
