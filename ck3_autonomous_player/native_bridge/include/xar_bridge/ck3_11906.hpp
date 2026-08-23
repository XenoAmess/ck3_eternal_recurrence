#pragma once

#include <cstddef>
#include <cstdint>

namespace xar::ck3_11906 {

inline constexpr char kExecutableSha256[] =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

using SubmitCommand = void (*)(void *manager, void *command,
                               std::uint32_t channel_flags);
using GetLocalPlayer = void *(*)(void *jomini_state);
using GetCurrentEvent = void *(*)(void *event_manager);

// Absolute addresses resolved only after the main executable matches the
// pinned 1.19.0.6 SHA-256. Tests may supply a small in-memory fixture instead.
struct Bindings {
  bool enabled = false;
  void **game_state_slot = nullptr;
  void **jomini_state_slot = nullptr;
  void *command_manager = nullptr;
  std::uintptr_t pause_primary_vtable = 0;
  std::uintptr_t pause_secondary_vtable = 0;
  std::uintptr_t set_speed_primary_vtable = 0;
  std::uintptr_t set_speed_secondary_vtable = 0;
  std::uintptr_t select_event_option_primary_vtable = 0;
  std::uintptr_t select_event_option_secondary_vtable = 0;
  std::size_t event_manager_offset = 0;
  SubmitCommand submit_command = nullptr;
  GetLocalPlayer get_local_player = nullptr;
  GetCurrentEvent get_current_event = nullptr;
};

struct Snapshot {
  std::int32_t date_raw = 0;
  std::int32_t speed = 0;
  bool paused = false;
  std::int32_t player_id = -1;
  bool has_active_event = false;
  std::int32_t active_event_instance_id = -1;
  std::int32_t active_event_option_count = 0;

  friend bool operator==(const Snapshot &, const Snapshot &) = default;
};

enum class PauseSubmitResult {
  submitted,
  already_paused,
  unavailable,
};

enum class ResumeSubmitResult {
  submitted,
  already_running,
  unavailable,
};

// Hashes the current process image on disk. A mismatch returns disabled
// bindings and therefore cannot advertise or execute CK3 gameplay features.
Bindings BindCurrentProcess() noexcept;

bool ReadSnapshot(const Bindings &bindings, Snapshot &output) noexcept;

// pause-map is an idempotent action: it reports already_paused without adding
// a command, otherwise it submits the same 0x28-byte CPauseGameCommand shape
// used by CK3's own UI through the engine's locked command queue path.
PauseSubmitResult SubmitPauseMap(const Bindings &bindings) noexcept;

// resume-map is the inverse idempotent operation.  It is required for a
// freshly loaded headless map because changing the speed does not clear
// Jomini's paused bit.
ResumeSubmitResult SubmitResumeMap(const Bindings &bindings) noexcept;

// Fixed public speeds 1..5 deliberately map to separate advertised gameplay
// steps.  CK3's native CSetGameSpeedCommand payload is zero based (0..4).
bool SubmitSetSpeed(const Bindings &bindings, std::int32_t speed) noexcept;

enum class SelectEventOptionResult {
  submitted,
  no_active_event,
  option_out_of_range,
  unavailable,
};

// Selects a zero-based native option on the same current local-player event
// returned in Snapshot. The public select-event-option-1..N step is translated
// to this zero-based payload at the protocol boundary. CK3's executor performs
// the same 0 <= index < option_count check before dispatching the effect.
SelectEventOptionResult
SubmitSelectEventOption(const Bindings &bindings,
                        std::int32_t option_index) noexcept;

} // namespace xar::ck3_11906
