#pragma once
#include <cstdint>
#include <string_view>

namespace xar::presentation::tracked {
enum class Failure : std::uint32_t {
  none = 0, not_started = 1, invalid_request = 2, core_read = 3,
  actor_or_date = 4, clock_scope = 5, army_identity = 6,
  combat_or_position = 7, modal_not_clear = 8, event_not_clear = 9,
  pending_binding = 10, pending_storage_read = 11, pending_capacity = 12,
  pending_slot_read = 13, pending_present = 14, pending_storage_changed = 15,
  final_identity = 16, fault_or_exception = 17, cooperative_yield = 18,
};
using ContinueRead = bool (*)(void *) noexcept;
// Owner-thread, one-subject software API; not a shared-memory/wire layout.
// Scope is the existing Native clock request generation, NOT an army lifetime.
struct Request {
  std::int32_t actor = -1;
  std::int32_t fullarmy_id = -1;
  std::uint64_t scope_generation = 0;
  std::int32_t start_date_raw = 0;
  std::int32_t max_date_raw = 0;
};
struct Frame {
  Failure reason = Failure::not_started;
  // OS QPC wall time, not engine CPU. UINT64_MAX means clock unavailable.
  std::uint64_t elapsed_us = ~std::uint64_t{0};
  bool complete = false, alive = false, map_ready = false, paused = false;
  bool ui_clear = false, full_id_valid = false, retreating = false;
  std::int32_t actor = -1, date_raw = 0, subject_owner = -1;
  std::int32_t current_province_id = -1, combat_id = -1;
  std::int32_t battle_province_id = -1;
  // Storage high-water slot capacity, NOT active interaction count.
  std::int32_t pending_slot_capacity = -1, pending_slots_visited = 0;
  std::uint64_t scope_generation = 0;
  bool scope_armed = false;
  std::int32_t scope_start_date_raw = 0, scope_target_date_raw = 0;
};
inline constexpr std::int32_t kMaximumPendingSlotsPerRead = 4096;
// Caller must prove current owner/main thread, mailbox idle, native connection
// epoch and request lease, and recheck them before a camera write. This reader
// neither submits commands nor arms/cancels the clock. False always cancels.
// All native pointers are local to this call. There is no semantic DTO cache.
bool ReadTrackedSubject12004V1(std::uintptr_t image_base,
    std::string_view exact_sha, const Request &request, Frame &frame,
    ContinueRead continue_read = nullptr, void *context = nullptr) noexcept;
} // namespace xar::presentation::tracked
