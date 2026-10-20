#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

// External source candidate only: not compiled, registered, deployed or live.
namespace xar::ck3_12004::religion::ghw_variables_candidate {
inline constexpr std::string_view kExactSha =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
inline constexpr std::uint16_t kFaithScopeKind = 13;
inline constexpr std::uint16_t kReligionScopeKind = 15;
inline constexpr std::uint32_t kNullReference = 0xffffffffU;
enum class Scope { global, religion, faith };
enum class Field : std::size_t {
  religion_unlocked = 0, religion_first_wait = 1,
  faith_ghw_cooldown = 2, global_unlocking_interval = 3
};
inline constexpr std::array<std::string_view, 4> kKeys{
    "variable_ghw_unlocked", "variable_first_ghw_cooldown",
    "variable_ghw_cooldown", "variable_ghw_global_unlocking_cooldown"};
inline constexpr std::array<Scope, 4> kScopes{
    Scope::religion, Scope::religion, Scope::faith, Scope::global};

// Internal only: pointers are caller-owned bindings, never wire fields.
struct BoundFrame {
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::uint32_t faith_id = kNullReference;
  std::uint32_t religion_id = kNullReference;
  std::uintptr_t faith_object = 0;
  std::uintptr_t religion_object = 0;
  bool paused = false;
  bool map_ready = false;
  bool actor_alive = false;
  bool operator==(const BoundFrame &) const = default;
};
using ReadMemory = bool (*)(void *, std::uintptr_t, void *, std::size_t) noexcept;
using ReadBoundFrame = bool (*)(void *, BoundFrame &) noexcept;
using ResolveIdentifier = bool (*)(void *, std::string_view, std::int32_t &) noexcept;
// Production wiring is fixed to actual .4 scope callbacks 13/15 through
// variable_context370EAF0, and the existing global accessor slot5C6A4B0.
// No arbitrary scope, actor or variable key is exposed by this reader.
using ResolveContext = bool (*)(void *, Scope, std::uint32_t,
                               std::uintptr_t &) noexcept;
struct Access {
  void *context = nullptr;
  ReadMemory read_memory = nullptr;
  ReadBoundFrame read_bound_frame = nullptr;
  ResolveIdentifier resolve_identifier = nullptr;
  ResolveContext resolve_context = nullptr;
  std::string_view executable_sha256;
};
enum class Failure {
  none, input_not_admitted, frame_unavailable, identity_changed,
  memory_unreadable, arithmetic_overflow, object_identity_mismatch,
  identifier_unavailable, context_unavailable, count_invalid,
  rows_unavailable, duplicate_key, collection_changed, observations_changed
};
struct Scalar {
  bool read_available = false;
  std::optional<bool> present;
  std::optional<bool> timed;
  std::optional<std::int32_t> expiry_raw;
  std::optional<std::int32_t> current_counter_raw;
  std::optional<std::int32_t> remaining_raw;
  std::optional<std::uint16_t> value_kind_raw;
  // Retain numeric values only. Non-numeric payloads may be pointers and are
  // deliberately not exported or interpreted by this finite flags reader.
  std::optional<std::int64_t> numeric_value_raw;
  // No calendar deadline is fabricated from a counter or authored duration.
  std::optional<std::int64_t> expiry_date_raw;
  Failure failure = Failure::none;
  bool operator==(const Scalar &) const = default;
};
struct Observation {
  bool available_any = false;
  bool all_fields_observed = false;
  bool frame_verified = false;
  bool stable_two_pass = false;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::uint32_t faith_id = kNullReference;
  std::uint32_t religion_id = kNullReference;
  std::array<Scalar, 4> fields{};
  Failure failure = Failure::none;
  static constexpr std::string_view remaining_unit =
      "signed32_native_scalar_counter_calendar_unqualified";
  // Collection-key presence is not a fabricated evaluation of launch CanTake.
  static constexpr bool launch_permission_inferred = false;
  static constexpr bool raw_pointer_fields_persisted = false;
};
bool ReadCurrentPlayerGhwVariables12004(const Access &, Observation &) noexcept;
const char *FailureKey(Failure) noexcept;
} // namespace xar::ck3_12004::religion::ghw_variables_candidate
