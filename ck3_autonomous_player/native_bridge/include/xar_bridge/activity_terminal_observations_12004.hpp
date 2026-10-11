#pragma once

#include "xar_bridge/activity_hosted_identity_v1.hpp"
#include "xar_bridge/activity_invalidation_precall_observer_12004.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

inline constexpr std::size_t kActivityTerminalObservations12004Capacity = 64;
inline constexpr std::uintptr_t kActivityTerminalObservations12004CutRva =
    0x29BF68C;

// Copied by the existing Core/GetPlayer adapter at the natural callback.
// There is no published query revision or additional date/clock in this frame.
struct ActivityTerminalCaptureFrame12004 {
  std::int64_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  std::uint32_t owner_thread_id = 0;
  bool paused = false;
  bool map_ready = false;
  bool has_played_character = false;
  bool played_character_alive = false;
};

using ActivityTerminalReadMemory12004 = bool (*)(
    void *, std::uintptr_t, void *, std::size_t) noexcept;
using ActivityTerminalReadFrame12004 = bool (*)(
    void *, ActivityTerminalCaptureFrame12004 &) noexcept;

struct ActivityTerminalObservation12004 {
  // Software journal sequence, never a native game clock or frame number.
  std::uint64_t capture_sequence = 0;
  std::uint32_t capture_thread_id = 0;
  ActivityTerminalCaptureFrame12004 capture_frame{};
  std::uintptr_t manager_identity = 0;
  std::uintptr_t activity_identity = 0;
  std::uintptr_t type_identity = 0;
  std::uint32_t activity_full_id = 0;
  std::uint8_t activity_instance_generation = 0;
  std::int32_t host_character_id = -1;
  std::array<char, 64> type_key{};
  std::uint8_t type_key_size = 0;
  bool completed_observed = false;
  std::uint8_t completed_raw_u8 = 0;
  bool invalidated_observed = false;
  std::uint8_t invalidated_raw_u8 = 0;
  bool native_completion_stamp_observed = false;
  std::uint64_t native_completion_stamp_raw = 0;
};

struct ActivityTerminalObservationsSnapshot12004 {
  bool available = false;
  bool observer_attached = false;
  const char *unavailable_reason = "activity_terminal_observer_unavailable";
  std::uint32_t query_thread_id = 0;
  std::uint32_t query_actor_full_id = 0;
  std::uint64_t earliest_retained_sequence = 0;
  std::uint64_t latest_capture_sequence = 0;
  std::uint64_t overflow_dropped_count = 0;
  std::uint32_t record_count = 0;
  std::array<ActivityTerminalObservation12004,
             kActivityTerminalObservations12004Capacity> records{};
};

// Cold source binding only. The Bridge owns Install and its suspension proof.
// The memory/frame callbacks and their context remain valid for process life.
bool BuildActivityTerminalObservations12004Environment(
    std::uintptr_t module_base, std::string_view executable_sha256,
    void *callback_context, ActivityTerminalReadMemory12004 read_memory,
    ActivityTerminalReadFrame12004 read_frame,
    ActivityInvalidationPrecallObserver12004Environment &output) noexcept;

// reason is a process-lifetime literal; false suppresses later appends.
void SetActivityTerminalObservations12004Attached(
    bool attached, const char *reason = nullptr) noexcept;

// Existing paused hosted-post query only: current-host and Feast filtering.
// A consumer still needs an exact persisted full-ID/generation/host/type match.
// Never configured -> nullopt; configured but unavailable -> status object.
std::optional<ActivityTerminalObservationsSnapshot12004>
ReadActivityTerminalObservations12004(
    const bridge::ActivityHostedIdentityFrameV1 &query_frame,
    std::uintptr_t module_base,
    std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004
