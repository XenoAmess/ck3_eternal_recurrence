#include "xar_bridge/event_window_context_v1.hpp"

#include <algorithm>
#include <array>
#include <charconv>
#include <string>

namespace xar::ck3_11906 {
namespace {

template <typename T> std::string Number(T value) {
  std::array<char, 32> buffer{};
  const auto result =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  return result.ec == std::errc{} ? std::string(buffer.data(), result.ptr)
                                  : std::string{};
}

void AppendString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output.push_back('"');
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      output.push_back('\\');
      output.push_back(static_cast<char>(character));
    } else if (character < 0x20U) {
      output += "\\u00";
      output.push_back(hex[(character >> 4U) & 0xFU]);
      output.push_back(hex[character & 0xFU]);
    } else {
      output.push_back(static_cast<char>(character));
    }
  }
  output.push_back('"');
}

} // namespace

std::string SerializeEventWindowContextV1(
    const game::EventWindowContextV1 &context) {
  if (context.snapshot_revision == 0 ||
      context.current_event_instance_id <= 0) {
    return {};
  }
  const bool available =
      context.status == game::EventWindowContextStatusV1::available;
  if ((available && (!context.unavailable_reason.empty() ||
                     context.window_match_count != 1 ||
                     !context.option_presentation_ready ||
                     context.effect_preview_ready ||
                     context.semantic_decision_ready)) ||
      (!available && (context.unavailable_reason.empty() ||
                      !context.options.empty() ||
                      context.option_presentation_ready ||
                      context.effect_preview_ready ||
                      context.semantic_decision_ready))) {
    return {};
  }
  std::string output;
  output.reserve(4096);
  output += "{\"schema\":\"current-event-window-context-v1\","
            "\"schema_version\":1,\"status\":";
  AppendString(output, available ? "available" : "unavailable");
  output += ",\"snapshot_revision\":" + Number(context.snapshot_revision);
  output += ",\"date_raw\":" + Number(context.date_raw);
  output += ",\"current_event_instance_id\":" +
            Number(context.current_event_instance_id);
  output += ",\"window_match_count\":" +
            Number(context.window_match_count);
  output += ",\"unavailable_reason\":";
  if (available) {
    output += "null,\"event_definition_key\":null,\"root_scope\":null,"
              "\"saved_scopes\":null,\"options\":[";
    for (std::size_t index = 0; index < context.options.size(); ++index) {
      if (index != 0) {
        output.push_back(',');
      }
      const auto &option = context.options[index];
      const bool duplicate_native_index = std::any_of(
          context.options.begin(), context.options.begin() + index,
          [&option](const game::EventWindowOptionV1 &existing) {
            return existing.native_option_index ==
                   option.native_option_index;
          });
      if (option.rendered_index != static_cast<std::int32_t>(index) ||
          option.native_option_index < 0 || duplicate_native_index ||
          !option.shown) {
        return {};
      }
      output += "{\"rendered_index\":" + Number(option.rendered_index);
      output += ",\"native_option_index\":" +
                Number(option.native_option_index);
      output += ",\"shown\":true,\"enabled\":";
      output += option.enabled ? "true" : "false";
      output += ",\"fallback\":";
      output += option.fallback ? "true" : "false";
      output += ",\"cancel\":";
      output += option.cancel ? "true" : "false";
      output += ",\"resolved_name\":";
      AppendString(output, option.resolved_name);
      output += ",\"unavailable_reason\":";
      AppendString(output, option.unavailable_reason);
      output += ",\"effect_preview\":{\"status\":\"unavailable\","
                "\"reason\":\"full_effect_preview_unavailable\"}}";
    }
    output.push_back(']');
  } else {
    AppendString(output, context.unavailable_reason);
    output += ",\"event_definition_key\":null,\"root_scope\":null,"
              "\"saved_scopes\":null,\"options\":null";
  }
  output += ",\"readiness\":{\"option_presentation_ready\":";
  output += context.option_presentation_ready ? "true" : "false";
  output += ",\"effect_preview_ready\":";
  output += context.effect_preview_ready ? "true" : "false";
  output += ",\"semantic_decision_ready\":";
  output += context.semantic_decision_ready ? "true" : "false";
  output +=
      "},\"provenance\":{\"root\":\"module+0x570F7B8->+0x10\","
      "\"idler_vtable_rva\":\"0x40B1D30\","
      "\"manager_offset\":\"+0x28\","
      "\"backend_id\":\"ck3-1.19.0.6-native-event-window-v1\"}}";
  return output;
}

} // namespace xar::ck3_11906
