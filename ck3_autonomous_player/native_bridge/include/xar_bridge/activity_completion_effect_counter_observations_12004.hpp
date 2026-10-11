#pragma once

#include "xar_bridge/activity_terminal_observations_12004.hpp"
#include "xar_bridge/activity_completion_effect_counter_observer_12004.hpp"

#include <array>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

inline constexpr std::size_t kActivityCompletionEffectCounterCapacity12004 = 64;
inline constexpr std::uintptr_t kActivityCompletionEffectCounterObservationCallRva12004 =
    0x23F6B82;
inline constexpr std::uintptr_t kActivityCompletionEffectCounterObservationReturnRva12004 =
    0x23F6B87;

// Each face is independently copied around the one original natural call.
// XP is specifically unavailable: the existing XP helper invokes a native
// TraitDB/track getter and is not used by these guarded raw readers.
struct ActivityCompletionEffectCounterFace12004 {
  bool frame_observed = false;
  ActivityTerminalCaptureFrame12004 frame{};
  bool activity_full_id_observed = false;
  std::uint32_t activity_full_id = 0;
  bool host_observed = false;
  std::int32_t host_character_id = -1;
  bool type_observed = false;
  std::uintptr_t type_identity = 0;
  bool type_key_observed = false;
  std::array<char, 64> type_key{};
  std::uint8_t type_key_size = 0;
  bool participant_full_id_observed = false;
  std::uint32_t participant_full_id = 0;
  bool resource_extension_observed = false;
  std::uintptr_t resource_extension_identity = 0;
  bool prestige_observed = false;
  std::int64_t prestige_raw = 0;
  bool stress_observed = false;
  std::int32_t stress_raw = 0;
  bool reveler_xp_observed = false;
  std::int64_t reveler_xp_raw = 0;
  const char *reveler_xp_unavailable_reason = "no_raw_only_reveler_xp_reader";
};

struct ActivityCompletionEffectCounterObservation12004 {
  // Both sequence fields are software order counters, not game clocks.
  std::uint64_t capture_sequence = 0;
  std::uint64_t observer_invocation_sequence = 0;
  std::uint32_t capture_thread_id = 0;
  std::uintptr_t activity_identity = 0;
  std::uintptr_t participant_identity = 0;
  std::uintptr_t effect_identity = 0;
  std::uintptr_t native_context_identity = 0;
  std::uintptr_t original_parent_rsp = 0;
  bool original_call_return_observed = false;
  ActivityCompletionEffectCounterFace12004 before{};
  ActivityCompletionEffectCounterFace12004 after{};
  bool same_activity_full_id_observed = false;
  bool same_activity_full_id = false;
  bool same_participant_full_id_observed = false;
  bool same_participant_full_id = false;
};

struct ActivityCompletionEffectCounterSnapshot12004 {
  bool available = false;
  bool observer_attached = false;
  const char *unavailable_reason = "activity_completion_effect_counter_observer_unavailable";
  std::uint32_t query_thread_id = 0;
  std::uint32_t query_actor_full_id = 0;
  std::uint64_t earliest_retained_sequence = 0;
  std::uint64_t latest_capture_sequence = 0;
  std::uint64_t overflow_dropped_count = 0;
  std::uint64_t pairing_dropped_count = 0;
  std::uint32_t record_count = 0;
  std::array<ActivityCompletionEffectCounterObservation12004,
             kActivityCompletionEffectCounterCapacity12004> records{};
};

// Bind source callbacks only; Bridge owns the cold Install and its proof.
bool BuildActivityCompletionEffectCounterObservations12004Environment(
    std::uintptr_t module_base, std::string_view executable_sha256,
    void *callback_context, ActivityTerminalReadMemory12004 read_memory,
    ActivityTerminalReadFrame12004 read_frame,
    ActivityCompletionEffectCounterObserver12004Environment &output) noexcept;

// A fixed process-lifetime reason literal; never-configured remains nullopt.
void SetActivityCompletionEffectCounterObservations12004Attached(
    bool attached, const char *reason = nullptr) noexcept;

// Existing paused hosted-post query. Filter current participant full32 ID and
// raw activity_feast type; host is retained independently from participant.
std::optional<ActivityCompletionEffectCounterSnapshot12004>
ReadActivityCompletionEffectCounterObservations12004(
    const bridge::ActivityHostedIdentityFrameV1 &query_frame,
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004
