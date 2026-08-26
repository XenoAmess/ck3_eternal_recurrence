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
  unavailable.option_presentation_ready = false;
  unavailable.unavailable_reason = "event_window_not_materialized";
  const auto unavailable_json =
      xar::ck3_11906::SerializeEventWindowContextV1(unavailable);
  if (!Contains(unavailable_json, "\"status\":\"unavailable\"") ||
      !Contains(unavailable_json,
                "\"unavailable_reason\":\"event_window_not_materialized\"") ||
      !Contains(unavailable_json, "\"options\":null")) {
    std::cerr << "unavailable event-window serialization drifted\n";
    return 1;
  }

  available.options.front().shown = false;
  if (!xar::ck3_11906::SerializeEventWindowContextV1(available).empty()) {
    std::cerr << "invalid materialized option was serialized\n";
    return 1;
  }
  return 0;
}
