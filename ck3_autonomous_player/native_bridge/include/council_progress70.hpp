#pragma once
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::council_progress70 {
inline constexpr std::string_view kExecutableSha256 =
    "BB3FEF106240E95ECDB6F1532982E89E9432C92A99D33DB623521572F06E6F79";
inline constexpr std::size_t kRowLimit = 64;
inline constexpr std::size_t kKeyLimit = 95;
// Address calculation only. Public construction is an algorithm/test seam;
// this type grants no image admission, Main/TLS custody, lease or capability.
struct Bindings {
  std::uintptr_t image_base = 0;
};
Bindings BindImage(std::uintptr_t image_base, std::string_view sha256) noexcept;
struct Access {
  void *context = nullptr;
  bool (*copy)(void *, std::uintptr_t, void *, std::size_t) noexcept = nullptr;
  // Mandatory external consistency signal; this reader does not establish
  // what it proves. Future Frame integration must supply actual module/Core,
  // Main/TLS/ticket/epoch/currentFull checks, not a permissive boolean.
  bool (*consistent)(void *) noexcept = nullptr;
};
struct FrameSource {
  std::uint64_t native_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t actor_id = -1; // full signed32; only -1 is absent
  std::uintptr_t game_state = 0;
  std::uintptr_t game_data = 0;
  std::uintptr_t character_store = 0;
  std::uintptr_t actor = 0;
};
inline constexpr std::int64_t kProgressScale = 100000;
// A physical backing observation, not an invocation or reconstruction of the
// native float property. Native CVTSI2SS/DIVSS can round the backing integer.
struct ProgressObservation {
  std::int32_t kind_raw = -1;
  std::int64_t backing_raw = 0;
  std::uint8_t frozen_raw = 0;
  std::optional<bool> frozen;
  std::optional<std::int64_t> current_raw;
  std::optional<std::int64_t> maximum_raw;
  bool current_source_verified = false;
  std::string_view current_reason = "council70_current_holder_unverified";
  friend bool operator==(const ProgressObservation &, const ProgressObservation &) = default;
};
struct TaskRow {
  std::int32_t task_id = -1;
  std::optional<std::int32_t> holder_id;
  bool holder_alive = false;
  // Set only for a live full-ID holder with its +108 reverse reference to
  // this task. This describes source identity, not progress or performing.
  bool current_type_source_verified = false;
  std::string position_key;
  std::string stored_task_type_key;
  ProgressObservation progress;
  friend bool operator==(const TaskRow &, const TaskRow &) = default;
};
struct Observation {
  std::vector<TaskRow> rows;
  std::string_view reason = "council70_not_read";
};
// Internal owned-task observation, NOT an enumeration of all Council seats.
// No native calls, raw dereference fallback, wire, status=available, Full,
// candidate/legality/assignment readiness, native evaluator/float result or action projection.
// Two equal read transcripts detect observed pointer/value drift; they do
// not establish allocation lifetime or exclude an unobserved ABA.
bool Read(const Bindings &, const Access &, const FrameSource &,
          Observation &) noexcept;
} // namespace xar::council_progress70
