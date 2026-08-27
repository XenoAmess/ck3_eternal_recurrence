#pragma once

#include "xar_bridge/game_contract.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::game {

enum class EventWindowContextStatusV1 {
  available,
  unavailable,
};

enum class EventEffectIndicatorKindV1 {
  trait,
  stress,
  death,
  scheme,
  unknown,
};

struct EventEffectIndicatorRowV1 {
  EventEffectIndicatorKindV1 kind = EventEffectIndicatorKindV1::unknown;
  std::int32_t raw_kind = -1;
  bool gain = false;
  bool affected_by_trait = false;
  bool critical = false;
  bool identity_available = false;
  std::optional<std::int32_t> native_id;
  std::string stable_key;

  friend bool operator==(const EventEffectIndicatorRowV1 &,
                         const EventEffectIndicatorRowV1 &) = default;
};

struct EventWindowOptionV1 {
  std::int32_t rendered_index = -1;
  std::int32_t native_option_index = -1;
  bool shown = false;
  bool enabled = false;
  bool fallback = false;
  bool cancel = false;
  std::string resolved_name;
  std::string unavailable_reason;
  std::vector<EventEffectIndicatorRowV1> effect_indicators;

  friend bool operator==(const EventWindowOptionV1 &,
                         const EventWindowOptionV1 &) = default;
};

struct EventScopeTypedIdentityV1 {
  bool available = false;
  std::optional<std::int32_t> character_id;
  std::string unavailable_reason;

  friend bool operator==(const EventScopeTypedIdentityV1 &,
                         const EventScopeTypedIdentityV1 &) = default;
};

struct EventScopeV1 {
  std::uint16_t raw_type_index = 0;
  std::string type_key;
  std::uint16_t subtype = 0;
  EventScopeTypedIdentityV1 typed_identity;

  friend bool operator==(const EventScopeV1 &, const EventScopeV1 &) =
      default;
};

struct EventSavedScopeV1 {
  std::string name;
  std::int32_t name_identifier = -1;
  EventScopeV1 scope;

  friend bool operator==(const EventSavedScopeV1 &,
                         const EventSavedScopeV1 &) = default;
};

struct EventWindowContextV1 {
  EventWindowContextStatusV1 status =
      EventWindowContextStatusV1::unavailable;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t current_event_instance_id = -1;
  std::int32_t window_match_count = 0;
  std::string unavailable_reason;
  std::string event_definition_key;
  std::optional<std::int32_t> calculated_event_id;
  std::optional<std::int32_t> runtime_stats_ordinal;
  std::optional<EventScopeV1> root_scope;
  std::vector<EventSavedScopeV1> saved_scopes;
  std::vector<EventWindowOptionV1> options;
  bool event_definition_identity_ready = false;
  bool root_scope_ready = false;
  bool saved_scopes_ready = false;
  bool option_presentation_ready = false;
  bool effect_indicators_ready = false;
  bool effect_preview_ready = false;
  bool semantic_decision_ready = false;

  friend bool operator==(const EventWindowContextV1 &,
                         const EventWindowContextV1 &) = default;
};

enum class ReadEventWindowContextResultV1 {
  available,
  unavailable,
};

} // namespace xar::game

namespace xar::ck3_11906 {

struct Bindings;

inline constexpr std::string_view kEventWindowContextV1Capability =
    "game.command.query-current-event-window-context-v1";
inline constexpr std::string_view kEventWindowContextV1Step =
    "query-current-event-window-context-v1";
inline constexpr std::uintptr_t kIngameInterfaceIdlerVtableRva = 0x40B1D30;
inline constexpr std::uintptr_t kEventWindowPrimaryVtableRva = 0x417F758;

game::ReadEventWindowContextResultV1 ReadEventWindowContextV1(
    const Bindings &bindings, std::uint64_t expected_snapshot_revision,
    std::int32_t expected_event_instance_id,
    game::EventWindowContextV1 &output) noexcept;

std::string SerializeEventWindowContextV1(
    const game::EventWindowContextV1 &context);

bool ParseEventWindowContextRequestV1(
    std::string_view json, std::uint64_t &expected_revision,
    std::int32_t &event_instance_id) noexcept;

} // namespace xar::ck3_11906
