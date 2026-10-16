#pragma once
#include "xar_bridge/army_county_predicate_trace_v1.hpp"
#include <cstdint>
#include <optional>
#include <string>

namespace xar::game {
// Current native predicate inputs for the existing preview's first remaining
// edge. This is neither an arrival callback nor an applied-loss observation.
struct ArmyCountyEntryPreviewConditionV1 {
  bool available = false;
  std::string unavailable_reason = "preview_county_inputs_unavailable";
  std::int32_t subject_army_id = -1;
  std::int32_t requested_target_province_id = -1;
  std::int32_t source_province_id = -1;
  std::optional<std::int32_t> target_province_id;
  std::optional<std::int32_t> native_carmy_id, actor_character_id, mode;
  std::optional<std::uint8_t> army_1d4_raw;
  std::optional<std::uint8_t> source_definition_1b_u8, target_definition_1b_u8;
  std::optional<bool> source_county_present, target_county_present, county_objects_differ;
  // Opaque process-local identities, never a TitleID or a cross-query join key.
  std::optional<std::uint64_t> source_county_identity, target_county_identity;
  std::optional<std::uint32_t> target_county_magic_3e0_u32;
  bool inputs_observation_ready = false;
  bool native_condition_called = false;
  std::optional<bool> native_condition_passes;
  bool identity_before_after_match = false;
  std::optional<ArmyCountyPredicateTraceV1> predicate_trace_v1;
  friend bool operator==(const ArmyCountyEntryPreviewConditionV1 &,
                         const ArmyCountyEntryPreviewConditionV1 &) = default;
};
} // namespace xar::game
