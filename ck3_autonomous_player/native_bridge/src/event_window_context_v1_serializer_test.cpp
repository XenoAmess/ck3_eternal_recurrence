#include "xar_bridge/event_window_context_v1.hpp"

#include <iostream>
#include <string>

namespace {

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
  available.event_definition_identity_ready = true;
  available.option_presentation_ready = true;
  xar::game::EventWindowOptionV1 option{};
  option.rendered_index = 0;
  option.native_option_index = 3;
  option.shown = true;
  option.enabled = false;
  option.fallback = true;
  option.cancel = true;
  option.resolved_name = "Wait \"here\"";
  option.unavailable_reason = "Not today";
  available.options.push_back(option);
  const auto serialized =
      xar::ck3_11906::SerializeEventWindowContextV1(available);
  if (!Contains(serialized, "\"current_event_instance_id\":16777257") ||
      !Contains(serialized,
                "\"event_definition_key\":\"xar_test.0001\"") ||
      !Contains(serialized, "\"calculated_event_id\":-712345") ||
      !Contains(serialized, "\"runtime_stats_ordinal\":37") ||
      !Contains(serialized,
                "\"event_definition_identity_ready\":true") ||
      !Contains(serialized, "\"native_option_index\":3") ||
      !Contains(serialized, "\"shown\":true") ||
      !Contains(serialized, "\"enabled\":false") ||
      !Contains(serialized, "\"fallback\":true") ||
      !Contains(serialized, "\"cancel\":true") ||
      !Contains(serialized, "Wait \\\"here\\\"") ||
      !Contains(serialized,
                "\"effect_preview\":{\"status\":\"unavailable\",")) {
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
  unavailable.event_definition_identity_ready = false;
  unavailable.option_presentation_ready = false;
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
  return 0;
}
