#pragma once

#include "xar_bridge/ck3_12002_event_window_context.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12003 {

enum class FamilyTerminalEventKindV1 : std::uint8_t {
  no_match = 0,
  refusal,
  acceptance,
  ambiguous,
};

enum class FamilyTerminalEventFailureV1 : std::uint8_t {
  none = 0,
  invalid_request,
  bindings_unavailable,
  core_snapshot_unavailable,
  player_or_date_mismatch,
  paused_map_required,
  event_manager_unavailable,
  queue_invalid,
  event_record_invalid,
  event_key_invalid,
  saved_scope_vector_invalid,
  saved_scope_name_invalid,
  duplicate_saved_scope_name,
  character_scope_identity_invalid,
  queue_changed,
  core_snapshot_changed,
  memory_read_failed,
  allocation_failed,
};

struct FamilyTerminalEventsRequestV1 {
  std::int32_t expected_date_raw = 0;
  std::int32_t played_character_id = -1;
  std::int32_t actor_character_id = -1;
  std::int32_t recipient_character_id = -1;
  std::int32_t subject_character_id = -1;
  std::int32_t candidate_character_id = -1;
};

struct FamilyTerminalEventScopeV1 {
  std::uint16_t raw_type_index = 0;
  std::uint16_t subtype = 0;
  std::uint64_t raw_payload = 0;
  bool character_scope_is_null = false;
  bool character_identity_verified = false;
  std::optional<std::int32_t> character_id;

  friend bool operator==(const FamilyTerminalEventScopeV1 &,
                         const FamilyTerminalEventScopeV1 &) = default;
};

struct FamilyTerminalEventSavedScopeV1 {
  std::int32_t name_identifier = -1;
  std::string name;
  FamilyTerminalEventScopeV1 scope;

  friend bool operator==(const FamilyTerminalEventSavedScopeV1 &,
                         const FamilyTerminalEventSavedScopeV1 &) = default;
};

struct FamilyTerminalEventRecordV1 {
  std::uint32_t queue_ordinal = 0;
  std::uintptr_t event_address = 0;
  std::uintptr_t definition_address = 0;
  std::int32_t event_instance_id = -1;
  std::int32_t calculated_event_id = 0;
  std::int32_t runtime_stats_ordinal = 0;
  std::string event_definition_key;
  std::int32_t receiver_character_id = -1;
  std::uint8_t primary_raw = 0;
  FamilyTerminalEventKindV1 letter_kind = FamilyTerminalEventKindV1::no_match;
  bool scopes_sampled = false;
  FamilyTerminalEventScopeV1 root_scope;
  std::vector<FamilyTerminalEventSavedScopeV1> saved_scopes;
  bool original_roles_match = false;

  friend bool operator==(const FamilyTerminalEventRecordV1 &,
                         const FamilyTerminalEventRecordV1 &) = default;
};

struct FamilyTerminalEventsSnapshotV1 {
  bool available = false;
  FamilyTerminalEventFailureV1 failure = FamilyTerminalEventFailureV1::none;
  FamilyTerminalEventKindV1 kind = FamilyTerminalEventKindV1::no_match;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  bool paused = false;
  bool map_ready = false;
  bool queue_read_complete = false;
  bool queue_stable = false;
  std::int32_t queue_count = 0;
  std::int32_t queue_capacity = 0;
  std::uint32_t matched_count = 0;
  std::vector<FamilyTerminalEventRecordV1> records;
};

std::string_view FamilyTerminalEventKindNameV1(
    FamilyTerminalEventKindV1 kind) noexcept;
std::string_view FamilyTerminalEventFailureNameV1(
    FamilyTerminalEventFailureV1 failure) noexcept;

// The owning bridge supplies the existing exact .3 EventWindowBindings and
// snapshot revision admission. This reads the complete retained player queue,
// not the current window, and never consumes/selects an event or sends a command.
// The same entry accepts fixture-owned layouts and existing callback bindings.
// Only .0010/.0011 with receiver/root and four exact named roles can match.
// A complete stable no_match is only retained-letter absence, never a refusal,
// expiry, timeout or proof that the original proposal has no history elsewhere.
// These native letters do not contain the original source date or pending ID.
bool ReadFamilyTerminalEventsV1(
    const ck3_12002::EventWindowBindings &bindings,
    const FamilyTerminalEventsRequestV1 &request,
    FamilyTerminalEventsSnapshotV1 &output) noexcept;

} // namespace xar::ck3_12003
