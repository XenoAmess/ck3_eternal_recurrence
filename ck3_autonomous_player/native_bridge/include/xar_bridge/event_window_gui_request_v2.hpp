#pragma once

#include <cstddef>
#include <string_view>

namespace xar::ck3_12002 {

enum class EventWindowGuiRequestVersionV2 {
  presentation_v1,
  gui_v2,
};

// Read the optional top-level field from the original wire bytes. The existing
// event-window request parser retains responsibility for its original fields.
// A missing field keeps v1, including quoted/nested mentions of its name.
inline bool ParseEventWindowGuiRequestVersionV2(
    std::string_view json, EventWindowGuiRequestVersionV2 &output) noexcept {
  output = EventWindowGuiRequestVersionV2::presentation_v1;
  const auto space = [](char value) noexcept {
    return value == ' ' || value == '\t' || value == '\r' || value == '\n';
  };
  const auto skip_space = [&](std::size_t position) noexcept {
    while (position < json.size() && space(json[position])) ++position;
    return position;
  };
  const auto first = skip_space(0);
  const bool object = first < json.size() && json[first] == '{';
  std::size_t depth = 0;
  bool found = false;
  bool malformed = false;
  bool root_finished = false;
  for (std::size_t position = first; position < json.size(); ++position) {
    const auto value = json[position];
    if (root_finished && !space(value)) malformed = true;
    if (value == '"') {
      const auto begin = position + 1;
      auto end = begin;
      bool escaped = false;
      while (end < json.size() && json[end] != '"') {
        if (json[end] == '\\') {
          escaped = true;
          if (++end == json.size()) break;
        }
        ++end;
      }
      if (end == json.size()) return !found;
      const auto colon = skip_space(end + 1);
      if (object && depth == 1 && !escaped &&
          json.substr(begin, end - begin) == "gui_observation_version" &&
          colon < json.size() && json[colon] == ':') {
        if (found) return false;
        const auto token = skip_space(colon + 1);
        if (token == json.size() || json[token] != '2') return false;
        const auto delimiter = skip_space(token + 1);
        // Inspect the literal token before any JSON normalization. In
        // particular, 2.0 and 2e0 must never become an accepted integer2.
        if (delimiter == json.size() ||
            (json[delimiter] != ',' && json[delimiter] != '}')) return false;
        found = true;
      }
      position = end;
    } else if (value == '{' || value == '[') {
      ++depth;
    } else if (value == '}' || value == ']') {
      if (depth == 0) malformed = true;
      else if (--depth == 0) root_finished = true;
    } else if (depth == 0 && !space(value)) {
      malformed = true;
    }
  }
  if (found && (malformed || depth != 0)) return false;
  if (found) output = EventWindowGuiRequestVersionV2::gui_v2;
  return true;
}

} // namespace xar::ck3_12002
