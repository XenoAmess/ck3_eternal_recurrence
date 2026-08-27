#include "xar_bridge/event_window_context_v1.hpp"

#include <iostream>
#include <string>

namespace {

constexpr std::int32_t kSavedRootNameIdentifier = -2'130'706'232;

bool Contains(const std::string &value, const char *token) {
  return value.find(token) != std::string::npos;
}

} // namespace

int main() {
  xar::game::EventWindowContextV1 available{};
  available.status = xar::game::EventWindowContextStatusV1::available;
  available.snapshot_revision = 7;
  available.date_raw = 741221;
  available.current_event_instance_id = 0x01000029;
  available.window_match_count = 1;
  available.event_definition_key = "xar_test.0001";
  available.calculated_event_id = -712'345;
  available.runtime_stats_ordinal = 37;
  xar::game::EventScopeV1 root_scope{};
  root_scope.raw_type_index = 4;
  root_scope.type_key = "character";
  root_scope.subtype = 0;
  root_scope.typed_identity.available = true;
  root_scope.typed_identity.character_id = 42;
  available.root_scope = root_scope;
  xar::game::EventSavedScopeV1 saved_character{};
  saved_character.name = "xar_scope_root_control";
  saved_character.name_identifier = kSavedRootNameIdentifier;
  saved_character.scope = root_scope;
  saved_character.scope.subtype = 2;
  available.saved_scopes.push_back(saved_character);
  xar::game::EventSavedScopeV1 saved_province{};
  saved_province.name = "province_control";
  saved_province.name_identifier = 201;
  saved_province.scope.raw_type_index = 3;
  saved_province.scope.type_key = "province";
  saved_province.scope.subtype = 1;
  saved_province.scope.typed_identity.unavailable_reason =
      "generic_scope_payload_identity_not_closed";
  available.saved_scopes.push_back(saved_province);
  available.event_definition_identity_ready = true;
  available.root_scope_ready = true;
  available.saved_scopes_ready = true;
  available.option_presentation_ready = true;
  available.effect_indicators_ready = true;
  xar::game::EventWindowOptionV1 option{};
  option.rendered_index = 0;
  option.native_option_index = 3;
  option.shown = true;
  option.enabled = false;
  option.fallback = true;
  option.cancel = true;
  option.resolved_name = "Wait \"here\"";
  option.unavailable_reason = "Not today";
  xar::game::EventEffectIndicatorRowV1 trait{};
  trait.kind = xar::game::EventEffectIndicatorKindV1::trait;
  trait.raw_kind = 0;
  trait.gain = true;
  trait.identity_available = true;
  trait.native_id = 123;
  trait.stable_key = "brave";
  option.effect_indicators.push_back(trait);
  xar::game::EventEffectIndicatorRowV1 stress{};
  stress.kind = xar::game::EventEffectIndicatorKindV1::stress;
  stress.raw_kind = 1;
  stress.gain = false;
  stress.affected_by_trait = true;
  stress.critical = false;
  option.effect_indicators.push_back(stress);
  xar::game::EventEffectIndicatorRowV1 death{};
  death.kind = xar::game::EventEffectIndicatorKindV1::death;
  death.raw_kind = 2;
  option.effect_indicators.push_back(death);
  xar::game::EventEffectIndicatorRowV1 scheme{};
  scheme.kind = xar::game::EventEffectIndicatorKindV1::scheme;
  scheme.raw_kind = 3;
  scheme.identity_available = true;
  scheme.stable_key = "murder";
  option.effect_indicators.push_back(scheme);
  xar::game::EventEffectIndicatorRowV1 unknown{};
  unknown.kind = xar::game::EventEffectIndicatorKindV1::unknown;
  unknown.raw_kind = 17;
  option.effect_indicators.push_back(unknown);
  available.options.push_back(option);
  const auto serialized =
      xar::ck3_11906::SerializeEventWindowContextV1(available);
  if (!Contains(serialized, "\"current_event_instance_id\":16777257") ||
      !Contains(serialized, "\"event_definition_key\":\"xar_test.0001\"") ||
      !Contains(serialized, "\"calculated_event_id\":-712345") ||
      !Contains(serialized, "\"runtime_stats_ordinal\":37") ||
      !Contains(serialized, "\"event_definition_identity_ready\":true") ||
      !Contains(serialized,
                "\"root_scope\":{\"status\":\"available\","
                "\"raw_type_index\":4,\"type_key\":\"character\"") ||
      !Contains(serialized,
                "\"typed_identity\":{\"status\":\"available\","
                "\"kind\":\"character\",\"character_id\":42}") ||
      !Contains(serialized,
                "\"name\":\"xar_scope_root_control\","
                "\"name_identifier\":-2130706232") ||
      !Contains(serialized,
                "\"type_key\":\"province\",\"subtype\":1,"
                "\"typed_identity\":{\"status\":\"unavailable\","
                "\"reason\":\"generic_scope_payload_identity_not_closed\"}") ||
      !Contains(serialized, "\"root_scope_ready\":true") ||
      !Contains(serialized, "\"saved_scopes_ready\":true") ||
      !Contains(serialized, "\"native_option_index\":3") ||
      !Contains(serialized, "\"shown\":true") ||
      !Contains(serialized, "\"enabled\":false") ||
      !Contains(serialized, "\"fallback\":true") ||
      !Contains(serialized, "\"cancel\":true") ||
      !Contains(serialized, "Wait \\\"here\\\"") ||
      !Contains(serialized,
                "\"effect_indicators\":{\"status\":\"available\",") ||
      !Contains(serialized,
                "\"operation\":\"add\",\"trait\":{\"status\":"
                "\"available\",\"native_id\":123,\"key\":\"brave\"") ||
      !Contains(serialized,
                "\"direction\":\"decrease\",\"magnitude\":{\"status\":"
                "\"unavailable\"},\"affected_by_trait\":true") ||
      !Contains(serialized,
                "\"kind\":\"death\",\"subject\":\"played_character\"") ||
      !Contains(serialized, "\"scheme_type_key\":\"murder\"") ||
      !Contains(serialized, "\"kind\":\"unknown\",\"raw_kind\":17") ||
      !Contains(serialized,
                "\"reason\":"
                "\"indicator_subset_has_no_completeness_signal\"") ||
      !Contains(serialized,
                "\"resource_deltas\":{\"status\":\"unavailable\"}") ||
      !Contains(serialized, "\"effect_indicators_ready\":true")) {
    std::cerr << "available event-window serialization drifted\n";
    return 1;
  }

  auto unavailable = available;
  unavailable.status = xar::game::EventWindowContextStatusV1::unavailable;
  unavailable.window_match_count = 0;
  unavailable.options.clear();
  unavailable.event_definition_key.clear();
  unavailable.calculated_event_id.reset();
  unavailable.runtime_stats_ordinal.reset();
  unavailable.root_scope.reset();
  unavailable.saved_scopes.clear();
  unavailable.event_definition_identity_ready = false;
  unavailable.root_scope_ready = false;
  unavailable.saved_scopes_ready = false;
  unavailable.option_presentation_ready = false;
  unavailable.effect_indicators_ready = false;
  unavailable.unavailable_reason = "event_window_not_materialized";
  const auto unavailable_json =
      xar::ck3_11906::SerializeEventWindowContextV1(unavailable);
  if (!Contains(unavailable_json, "\"status\":\"unavailable\"") ||
      !Contains(unavailable_json,
                "\"unavailable_reason\":\"event_window_not_materialized\"") ||
      !Contains(unavailable_json, "\"event_definition_key\":null") ||
      !Contains(unavailable_json, "\"calculated_event_id\":null") ||
      !Contains(unavailable_json, "\"runtime_stats_ordinal\":null") ||
      !Contains(unavailable_json, "\"options\":null")) {
    std::cerr << "unavailable event-window serialization drifted\n";
    return 1;
  }

  available.options.front().shown = false;
  if (!xar::ck3_11906::SerializeEventWindowContextV1(available).empty()) {
    std::cerr << "invalid materialized option was serialized\n";
    return 1;
  }
  available.options.front().shown = true;
  const auto valid = available;
  auto invalid = valid;
  invalid.event_definition_key.clear();
  if (!xar::ck3_11906::SerializeEventWindowContextV1(invalid).empty()) {
    std::cerr << "empty event definition key was serialized\n";
    return 1;
  }
  invalid = valid;
  invalid.calculated_event_id.reset();
  if (!xar::ck3_11906::SerializeEventWindowContextV1(invalid).empty()) {
    std::cerr << "missing calculated event ID was serialized\n";
    return 1;
  }
  invalid = valid;
  invalid.runtime_stats_ordinal.reset();
  if (!xar::ck3_11906::SerializeEventWindowContextV1(invalid).empty()) {
    std::cerr << "missing runtime stats ordinal was serialized\n";
    return 1;
  }
  invalid = valid;
  invalid.event_definition_identity_ready = false;
  if (!xar::ck3_11906::SerializeEventWindowContextV1(invalid).empty()) {
    std::cerr << "unready event definition identity was serialized\n";
    return 1;
  }
  invalid = valid;
  invalid.root_scope.reset();
  if (!xar::ck3_11906::SerializeEventWindowContextV1(invalid).empty()) {
    std::cerr << "missing event root scope was serialized\n";
    return 1;
  }
  invalid = valid;
  invalid.root_scope->typed_identity.character_id = 0;
  if (!xar::ck3_11906::SerializeEventWindowContextV1(invalid).empty()) {
    std::cerr << "stale event character scope was serialized\n";
    return 1;
  }
  invalid = valid;
  invalid.saved_scopes[1].name = invalid.saved_scopes[0].name;
  if (!xar::ck3_11906::SerializeEventWindowContextV1(invalid).empty()) {
    std::cerr << "duplicate named event scope was serialized\n";
    return 1;
  }
  invalid = unavailable;
  invalid.event_definition_key = "leaked.key";
  if (!xar::ck3_11906::SerializeEventWindowContextV1(invalid).empty()) {
    std::cerr << "unavailable event definition identity was serialized\n";
    return 1;
  }
  invalid = unavailable;
  invalid.calculated_event_id = 0;
  if (!xar::ck3_11906::SerializeEventWindowContextV1(invalid).empty()) {
    std::cerr << "unavailable calculated event ID was serialized\n";
    return 1;
  }
  invalid = unavailable;
  invalid.runtime_stats_ordinal = 0;
  if (!xar::ck3_11906::SerializeEventWindowContextV1(invalid).empty()) {
    std::cerr << "unavailable runtime stats ordinal was serialized\n";
    return 1;
  }
  invalid = unavailable;
  invalid.event_definition_identity_ready = true;
  if (!xar::ck3_11906::SerializeEventWindowContextV1(invalid).empty()) {
    std::cerr << "unavailable identity readiness was serialized\n";
    return 1;
  }
  invalid = unavailable;
  invalid.root_scope = root_scope;
  if (!xar::ck3_11906::SerializeEventWindowContextV1(invalid).empty()) {
    std::cerr << "unavailable root scope was serialized\n";
    return 1;
  }
  invalid = unavailable;
  invalid.saved_scopes.push_back(saved_character);
  if (!xar::ck3_11906::SerializeEventWindowContextV1(invalid).empty()) {
    std::cerr << "unavailable saved scope was serialized\n";
    return 1;
  }
  invalid = unavailable;
  invalid.root_scope_ready = true;
  if (!xar::ck3_11906::SerializeEventWindowContextV1(invalid).empty()) {
    std::cerr << "unavailable scope readiness was serialized\n";
    return 1;
  }
  return 0;
}
