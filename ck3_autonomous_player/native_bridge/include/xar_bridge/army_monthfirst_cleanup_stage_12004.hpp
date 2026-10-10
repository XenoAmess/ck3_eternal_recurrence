#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::game {

enum class ArmyMonthfirstCleanupFrame12004 {
  captured_current_context,
  conditional_cleanup_entry
};

struct ArmyMonthfirstCleanupRecord12004 {
  std::uintptr_t record_address = 0, vtable_address = 0;
  std::optional<std::uintptr_t> actual_slot0_target;
  std::optional<std::uint32_t> requested_full_id;
  std::optional<std::int32_t> ordinal;
};

// Only data and signedcount are consumed by this native callee. Capacity and
// allocator do not become new gates. A supplied same-frame queue seed reuses
// the existing primary468 pending capture instead of reading it a second time.
struct ArmyMonthfirstCleanupQueue12004 {
  std::optional<std::uintptr_t> buffer_address;
  std::optional<std::int32_t> count;
  std::vector<ArmyMonthfirstCleanupRecord12004> records;
};

struct ArmyMonthfirstCleanupRegi12004 {
  std::uint32_t requested_full_id = 0;
  bool selection_ready = false, used_native_fallback = false;
  std::uintptr_t selected_address = 0;
  std::optional<std::uint32_t> indexed_full_id, selected_full_id, magic_14;
  std::string unavailable_reason;
};

struct ArmyMonthfirstCleanupChunk12004 {
  std::uint32_t requested_full_id = 0;
  std::int32_t ordinal = 0;
  std::optional<std::uintptr_t> computed_address;
  std::optional<std::uint64_t> date_1c_raw64;
};

struct ArmyMonthfirstCleanupInputs12004 {
  ArmyMonthfirstCleanupFrame12004 frame =
      ArmyMonthfirstCleanupFrame12004::captured_current_context;
  bool exact_build_enabled = false, queue_capture_bounded = false;
  bool reused_same_frame_queue_seed = false;
  std::uintptr_t primary_address = 0, known_mode0_callback = 0;
  std::optional<std::uint8_t> saved_mask2;
  std::optional<std::uint64_t> passed_date_raw64;
  ArmyMonthfirstCleanupQueue12004 queue;
  std::vector<ArmyMonthfirstCleanupRegi12004> regi;
  std::vector<ArmyMonthfirstCleanupChunk12004> chunks;
  std::string unavailable_reason;
};

struct ArmyMonthfirstCleanupDateWrite12004 {
  std::int32_t outer_physical_index = 0;
  std::uintptr_t chunk_address = 0;
  std::uint64_t before_raw64 = 0, after_raw64 = 0;
};

struct ArmyMonthfirstCleanupResult12004 {
  bool ready = false, returned = false, caller_skipped = false;
  bool queue_postimage_ready = false, other_fields_unchanged = false;
  bool actual_poststage_observed = false, whole_daily_monthly = false;
  std::string unavailable_reason;
  // When unavailable, these are exact effects preceding the blocking read or
  // callback, not final returned values. Unknown callbacks may change them.
  std::vector<ArmyMonthfirstCleanupRecord12004> backing_records_after_prefix;
  std::optional<std::int32_t> count_after_known_prefix, returned_count;
  std::vector<ArmyMonthfirstCleanupDateWrite12004> date_writes_before_block;
  std::vector<std::int32_t> visited_outer_physical_indices;
  std::vector<std::int32_t> completed_mode0_callback_physical_indices;
  std::optional<std::int32_t> blocked_callback_physical_index;
  std::optional<std::uintptr_t> blocked_callback_target;
};

ArmyMonthfirstCleanupResult12004 EvaluateArmyMonthfirstCleanupStage12004(
    const ArmyMonthfirstCleanupInputs12004 &input);

} // namespace xar::game

namespace xar::ck3_12004 {

struct ArmyMonthfirstCleanupBindings12004 {
  bool enabled = false;
  std::uintptr_t image_base = 0, regi_registry_slot = 0,
      regi_fallback_slot = 0, known_mode0_callback = 0;
  static constexpr std::size_t kMaximumCapturedRecords = 256;
};

ArmyMonthfirstCleanupBindings12004 BindArmyMonthfirstCleanupStage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

struct ArmyMonthfirstCleanupReadView12004 {
  using ReadBytes = bool (*)(void *, std::uintptr_t, void *, std::size_t);
  void *context = nullptr;
  ReadBytes read_bytes = nullptr;
};

struct ArmyMonthfirstCleanupEntry12004 {
  game::ArmyMonthfirstCleanupFrame12004 frame =
      game::ArmyMonthfirstCleanupFrame12004::captured_current_context;
  std::uintptr_t primary_address = 0;
  std::optional<std::uint8_t> saved_mask2;
  std::optional<std::uint64_t> passed_date_raw64;
};

// Readonly software capture. The caller supplies the existing full passed CDate
// and saved flag: no calendar arithmetic or current-C0 observer is duplicated.
// Supply only a same-primary/same-frame queue seed converted from existing
// ArmyDetachmentPendingInputsV1; never supply another stage's current capture.
// No native cleanup, helper, record virtual method or allocator is invoked.
game::ArmyMonthfirstCleanupInputs12004 ReadArmyMonthfirstCleanupStage12004(
    const ArmyMonthfirstCleanupBindings12004 &binding,
    const ArmyMonthfirstCleanupReadView12004 &memory,
    const ArmyMonthfirstCleanupEntry12004 &entry,
    const game::ArmyMonthfirstCleanupQueue12004 *same_frame_queue_seed = nullptr);

} // namespace xar::ck3_12004
