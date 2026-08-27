#include "xar_bridge/event_window_context_v1.hpp"

#include <algorithm>
#include <array>
#include <charconv>
#include <cstddef>
#include <string>

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kMaximumEventDefinitionKeyBytes = 16'384;
constexpr std::size_t kMaximumEffectIndicators = 128;
constexpr std::size_t kMaximumSavedScopes = 1'024;
constexpr std::uint16_t kCharacterScopeTypeIndex = 4;
constexpr std::string_view kCharacterScopeTypeKey = "character";
constexpr std::string_view kGenericScopeIdentityUnavailableReason =
    "generic_scope_payload_identity_not_closed";

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

bool ValidEffectIndicator(const game::EventEffectIndicatorRowV1 &row) {
  const bool no_identity = !row.identity_available &&
                           !row.native_id.has_value() && row.stable_key.empty();
  switch (row.kind) {
  case game::EventEffectIndicatorKindV1::trait:
    return row.raw_kind == 0 && !row.affected_by_trait && !row.critical &&
           ((row.identity_available && row.native_id.has_value() &&
             *row.native_id >= 0 && !row.stable_key.empty() &&
             row.stable_key.size() <= kMaximumEventDefinitionKeyBytes) ||
            no_identity);
  case game::EventEffectIndicatorKindV1::stress:
    return row.raw_kind == 1 && no_identity;
  case game::EventEffectIndicatorKindV1::death:
    return row.raw_kind == 2 && !row.gain && !row.affected_by_trait &&
           !row.critical && no_identity;
  case game::EventEffectIndicatorKindV1::scheme:
    return row.raw_kind == 3 && !row.gain && !row.affected_by_trait &&
           !row.critical &&
           ((row.identity_available && !row.native_id.has_value() &&
             !row.stable_key.empty() &&
             row.stable_key.size() <= kMaximumEventDefinitionKeyBytes) ||
            no_identity);
  case game::EventEffectIndicatorKindV1::unknown:
    return (row.raw_kind < 0 || row.raw_kind > 3) && !row.gain &&
           !row.affected_by_trait && !row.critical && no_identity;
  }
  return false;
}

void AppendEffectIndicator(std::string &output,
                           const game::EventEffectIndicatorRowV1 &row) {
  switch (row.kind) {
  case game::EventEffectIndicatorKindV1::trait:
    output += "{\"kind\":\"trait\",\"operation\":\"";
    output += row.gain ? "add" : "remove";
    output += "\",\"trait\":{";
    if (row.identity_available) {
      output +=
          "\"status\":\"available\",\"native_id\":" + Number(*row.native_id) +
          ",\"key\":";
      AppendString(output, row.stable_key);
    } else {
      output += "\"status\":\"unavailable\",\"reason\":"
                "\"trait_identity_unavailable\"";
    }
    output += "}}";
    return;
  case game::EventEffectIndicatorKindV1::stress:
    output += "{\"kind\":\"stress\",\"direction\":\"";
    output += row.gain ? "increase" : "decrease";
    output += "\",\"magnitude\":{\"status\":\"unavailable\"},"
              "\"affected_by_trait\":";
    output += row.affected_by_trait ? "true" : "false";
    output += ",\"critical\":";
    output += row.critical ? "true" : "false";
    output.push_back('}');
    return;
  case game::EventEffectIndicatorKindV1::death:
    output += "{\"kind\":\"death\",\"subject\":\"played_character\","
              "\"direction\":\"not_applicable\"}";
    return;
  case game::EventEffectIndicatorKindV1::scheme:
    output += "{\"kind\":\"scheme\",\"subject\":\"played_character\","
              "\"operation\":\"start\",\"direction\":"
              "\"not_applicable\",\"scheme\":{";
    if (row.identity_available) {
      output += "\"status\":\"available\",\"scheme_type_key\":";
      AppendString(output, row.stable_key);
    } else {
      output += "\"status\":\"unavailable\",\"reason\":"
                "\"scheme_type_identity_unavailable\"";
    }
    output += "}}";
    return;
  case game::EventEffectIndicatorKindV1::unknown:
    output +=
        "{\"kind\":\"unknown\",\"raw_kind\":" + Number(row.raw_kind) + "}";
    return;
  }
}

bool ValidScope(const game::EventScopeV1 &scope) {
  if (scope.raw_type_index == 0 || scope.type_key.empty() ||
      scope.type_key.size() > kMaximumEventDefinitionKeyBytes) {
    return false;
  }
  const auto &identity = scope.typed_identity;
  if (scope.raw_type_index == kCharacterScopeTypeIndex) {
    return scope.type_key == kCharacterScopeTypeKey && identity.available &&
           identity.character_id.has_value() &&
           *identity.character_id > 0 && identity.unavailable_reason.empty();
  }
  return scope.type_key != kCharacterScopeTypeKey && !identity.available &&
         !identity.character_id.has_value() &&
         identity.unavailable_reason ==
             kGenericScopeIdentityUnavailableReason;
}

void AppendScope(std::string &output, const game::EventScopeV1 &scope) {
  output += "{\"status\":\"available\",\"raw_type_index\":" +
            Number(scope.raw_type_index) + ",\"type_key\":";
  AppendString(output, scope.type_key);
  output += ",\"subtype\":" + Number(scope.subtype) +
            ",\"typed_identity\":";
  if (scope.typed_identity.available) {
    output += "{\"status\":\"available\",\"kind\":\"character\","
              "\"character_id\":" +
              Number(*scope.typed_identity.character_id) + "}";
  } else {
    output += "{\"status\":\"unavailable\",\"reason\":";
    AppendString(output, scope.typed_identity.unavailable_reason);
    output.push_back('}');
  }
  output.push_back('}');
}

bool ValidSavedScopes(const std::vector<game::EventSavedScopeV1> &scopes) {
  if (scopes.size() > kMaximumSavedScopes) {
    return false;
  }
  for (std::size_t index = 0; index < scopes.size(); ++index) {
    const auto &scope = scopes[index];
    const bool duplicate = std::any_of(
        scopes.begin(), scopes.begin() + index,
        [&scope](const game::EventSavedScopeV1 &existing) {
          return existing.name_identifier == scope.name_identifier ||
                 existing.name == scope.name;
        });
    if (scope.name.empty() ||
        scope.name.size() > kMaximumEventDefinitionKeyBytes || duplicate ||
        !ValidScope(scope.scope)) {
      return false;
    }
  }
  return true;
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
                     !context.event_definition_identity_ready ||
                     context.event_definition_key.empty() ||
                     context.event_definition_key.size() >
                         kMaximumEventDefinitionKeyBytes ||
                     !context.calculated_event_id.has_value() ||
                     !context.runtime_stats_ordinal.has_value() ||
                     !context.root_scope.has_value() ||
                     !ValidScope(*context.root_scope) ||
                     !ValidSavedScopes(context.saved_scopes) ||
                     !context.root_scope_ready ||
                     !context.saved_scopes_ready ||
                     !context.option_presentation_ready ||
                     !context.effect_indicators_ready ||
                     context.effect_preview_ready ||
                     context.semantic_decision_ready)) ||
      (!available && (context.unavailable_reason.empty() ||
                      context.event_definition_identity_ready ||
                      !context.event_definition_key.empty() ||
                      context.calculated_event_id.has_value() ||
                      context.runtime_stats_ordinal.has_value() ||
                      context.root_scope.has_value() ||
                      !context.saved_scopes.empty() ||
                      !context.options.empty() ||
                      context.root_scope_ready ||
                      context.saved_scopes_ready ||
                      context.option_presentation_ready ||
                      context.effect_indicators_ready ||
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
    output += "null,\"event_definition_key\":";
    AppendString(output, context.event_definition_key);
    output += ",\"calculated_event_id\":" +
              Number(*context.calculated_event_id);
    output += ",\"runtime_stats_ordinal\":" +
              Number(*context.runtime_stats_ordinal);
    output += ",\"root_scope\":";
    AppendScope(output, *context.root_scope);
    output += ",\"saved_scopes\":[";
    for (std::size_t index = 0; index < context.saved_scopes.size(); ++index) {
      if (index != 0) {
        output.push_back(',');
      }
      const auto &saved = context.saved_scopes[index];
      output += "{\"name\":";
      AppendString(output, saved.name);
      output += ",\"name_identifier\":" + Number(saved.name_identifier) +
                ",\"scope\":";
      AppendScope(output, saved.scope);
      output.push_back('}');
    }
    output += "],\"options\":[";
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
          !option.shown ||
          option.effect_indicators.size() > kMaximumEffectIndicators ||
          !std::all_of(option.effect_indicators.begin(),
                       option.effect_indicators.end(), ValidEffectIndicator)) {
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
      output += ",\"effect_indicators\":{\"status\":\"available\","
                "\"coverage\":"
                "\"played-character-event-icon-indicators-1.19.0.6-v1\","
                "\"complete_effect_set\":false,\"rows\":[";
      for (std::size_t row_index = 0;
           row_index < option.effect_indicators.size(); ++row_index) {
        if (row_index != 0) {
          output.push_back(',');
        }
        AppendEffectIndicator(output, option.effect_indicators[row_index]);
      }
      output += "]},\"effect_preview\":{\"status\":\"unavailable\","
                "\"reason\":"
                "\"indicator_subset_has_no_completeness_signal\"},"
                "\"resource_deltas\":{\"status\":\"unavailable\"},"
                "\"relationship_deltas\":{\"status\":"
                "\"unavailable\"}}";
    }
    output.push_back(']');
  } else {
    AppendString(output, context.unavailable_reason);
    output += ",\"event_definition_key\":null,"
              "\"calculated_event_id\":null,"
              "\"runtime_stats_ordinal\":null,\"root_scope\":null,"
              "\"saved_scopes\":null,\"options\":null";
  }
  output +=
      ",\"readiness\":{\"event_definition_identity_ready\":";
  output += context.event_definition_identity_ready ? "true" : "false";
  output += ",\"root_scope_ready\":";
  output += context.root_scope_ready ? "true" : "false";
  output += ",\"saved_scopes_ready\":";
  output += context.saved_scopes_ready ? "true" : "false";
  output += ",\"option_presentation_ready\":";
  output += context.option_presentation_ready ? "true" : "false";
  output += ",\"effect_indicators_ready\":";
  output += context.effect_indicators_ready ? "true" : "false";
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
