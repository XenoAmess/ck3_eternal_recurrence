#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"

#include <algorithm>
#include <array>
#include <charconv>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

void AppendJsonString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output.push_back('"');
  for (const unsigned char character : value) {
    switch (character) {
    case '"': output += "\\\""; break;
    case '\\': output += "\\\\"; break;
    case '\b': output += "\\b"; break;
    case '\f': output += "\\f"; break;
    case '\n': output += "\\n"; break;
    case '\r': output += "\\r"; break;
    case '\t': output += "\\t"; break;
    default:
      if (character < 0x20U) {
        output += "\\u00";
        output.push_back(hex[(character >> 4U) & 0x0FU]);
        output.push_back(hex[character & 0x0FU]);
      } else {
        output.push_back(static_cast<char>(character));
      }
      break;
    }
  }
  output.push_back('"');
}

template <typename Value>
bool AppendNumber(std::string &output, Value value) {
  std::array<char, 32> buffer{};
  const auto converted =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (converted.ec != std::errc{}) return false;
  output.append(buffer.data(), converted.ptr);
  return true;
}

bool ValidFieldReason(std::string_view reason) noexcept {
  constexpr std::array<std::string_view, 14> reasons{
      "snapshot_unavailable",
      "widget_not_instantiated",
      "named_clickable_child_not_stable",
      "enabled_state_abi_not_frozen",
      "focus_owner_abi_not_frozen",
      "modal_blocking_abi_not_frozen",
      "screen_rect_abi_not_frozen",
      "scroll_area_extent_abi_not_frozen",
      "surface_not_available",
      "variable_absent",
      "value_type_mismatch",
      "value_out_of_range",
      "read_only_provider_action_not_exposed",
      "state_projection_unavailable"};
  return std::find(reasons.begin(), reasons.end(), reason) != reasons.end();
}

bool ValidTopReason(std::string_view reason) noexcept {
  constexpr std::array<std::string_view, 11> reasons{
      "unsupported_build", "requires_application_main", "requires_paused",
      "map_not_ready", "gui_root_unavailable",
      "state_projection_unavailable", "widget_state_unavailable",
      "widget_not_instantiated", "acl_inconsistent", "state_changed",
      "internal_error"};
  return std::find(reasons.begin(), reasons.end(), reason) != reasons.end();
}

template <typename Value>
bool ValidTyped(const game::ZhongguoTypedValueV1<Value> &field) noexcept {
  return field.available
             ? field.value.has_value() && field.unavailable_reason.empty()
             : !field.value.has_value() &&
                   ValidFieldReason(field.unavailable_reason);
}

template <typename Value, typename AppendValue>
bool AppendTyped(std::string &output,
                 const game::ZhongguoTypedValueV1<Value> &field,
                 AppendValue append_value) {
  if (!ValidTyped(field)) return false;
  output += "{\"status\":\"";
  output += field.available ? "available" : "unavailable";
  output += "\",\"value\":";
  if (field.available) {
    if (!append_value(output, *field.value)) return false;
  } else {
    output += "null";
  }
  output += ",\"unavailable_reason\":";
  if (field.available) {
    output += "null";
  } else {
    AppendJsonString(output, field.unavailable_reason);
  }
  output.push_back('}');
  return true;
}

bool AppendTypedInteger(std::string &output,
                        const game::ZhongguoTypedIntegerV1 &field) {
  return AppendTyped(output, field,
                     [](std::string &target, std::int64_t value) {
                       return AppendNumber(target, value);
                     });
}

bool AppendTypedBoolean(std::string &output,
                        const game::ZhongguoTypedBooleanV1 &field) {
  return AppendTyped(output, field,
                     [](std::string &target, bool value) {
                       target += value ? "true" : "false";
                       return true;
                     });
}

template <typename Field, typename Append>
bool AppendNamed(std::string &output, std::string_view name,
                 const Field &field, Append append, bool first = false) {
  if (!first) output.push_back(',');
  AppendJsonString(output, name);
  output.push_back(':');
  return append(output, field);
}

bool AppendWidget(std::string &output,
                  const game::ZhongguoScoreboardWidgetStateV1 &widget) {
  output += "{\"stable_identity\":";
  AppendJsonString(output, widget.stable_identity);
  output += ",\"runtime_name\":";
  AppendJsonString(output, widget.runtime_name);
  if (!AppendNamed(output, "exists", widget.exists, AppendTypedBoolean) ||
      !AppendNamed(output, "local_visible", widget.local_visible,
                   AppendTypedBoolean) ||
      !AppendNamed(output, "effective_visible", widget.effective_visible,
                   AppendTypedBoolean) ||
      !AppendNamed(output, "enabled", widget.enabled, AppendTypedBoolean) ||
      !AppendNamed(output, "focused", widget.focused, AppendTypedBoolean) ||
      !AppendNamed(output, "modal_blocking", widget.modal_blocking,
                   AppendTypedBoolean) ||
      !AppendNamed(output, "screen_x", widget.screen_x,
                   AppendTypedInteger) ||
      !AppendNamed(output, "screen_y", widget.screen_y,
                   AppendTypedInteger) ||
      !AppendNamed(output, "screen_width", widget.screen_width,
                   AppendTypedInteger) ||
      !AppendNamed(output, "screen_height", widget.screen_height,
                   AppendTypedInteger) ||
      !AppendNamed(output, "scroll_min", widget.scroll_min,
                   AppendTypedInteger) ||
      !AppendNamed(output, "scroll_max", widget.scroll_max,
                   AppendTypedInteger) ||
      !AppendNamed(output, "scroll_value", widget.scroll_value,
                   AppendTypedInteger)) {
    return false;
  }
  output.push_back('}');
  return true;
}

bool AppendManagedAcl(
    std::string &output,
    const game::ZhongguoScoreboardManagedAclV1 &acl) {
  output += "{\"surface_available\":";
  output += acl.surface_available ? "true" : "false";
  output += ",\"current_player_can_assess_others\":";
  output += acl.current_player_can_assess_others ? "true" : "false";
  return AppendNamed(output, "owner_character_id", acl.owner_character_id,
                     AppendTypedInteger) &&
         AppendNamed(output, "first_subject_character_id",
                     acl.first_subject_character_id, AppendTypedInteger) &&
         (output.push_back('}'), true);
}

bool AppendReceivedAcl(
    std::string &output,
    const game::ZhongguoScoreboardReceivedSelfAclV1 &acl) {
  output += "{\"surface_available\":";
  output += acl.surface_available ? "true" : "false";
  output += ",\"current_player_is_subject\":";
  output += acl.current_player_is_subject ? "true" : "false";
  if (!AppendNamed(output, "first_row_character_id",
                   acl.first_row_character_id, AppendTypedInteger) ||
      !AppendNamed(output, "owner_character_id", acl.owner_character_id,
                   AppendTypedInteger) ||
      !AppendNamed(output, "subject_character_id", acl.subject_character_id,
                   AppendTypedInteger) ||
      !AppendNamed(output, "cycle_serial", acl.cycle_serial,
                   AppendTypedInteger) ||
      !AppendNamed(output, "result_case_serial", acl.result_case_serial,
                   AppendTypedInteger) ||
      !AppendNamed(output, "b1_case_serial", acl.b1_case_serial,
                   AppendTypedInteger) ||
      !AppendNamed(output, "disclosure_acl_mode", acl.disclosure_acl_mode,
                   AppendTypedInteger) ||
      !AppendNamed(output, "disclosure_policy_available",
                   acl.disclosure_policy_available, AppendTypedInteger) ||
      !AppendNamed(output, "disclosure_policy_id", acl.disclosure_policy_id,
                   AppendTypedInteger) ||
      !AppendNamed(output, "disclosure_self_mode",
                   acl.disclosure_self_mode, AppendTypedInteger) ||
      !AppendNamed(output, "disclosure_team_mode",
                   acl.disclosure_team_mode, AppendTypedInteger) ||
      !AppendNamed(output, "disclosure_evaluator_identity_mode",
                   acl.disclosure_evaluator_identity_mode,
                   AppendTypedInteger) ||
      !AppendNamed(output, "disclosure_blackbox_risk",
                   acl.disclosure_blackbox_risk, AppendTypedInteger)) {
    return false;
  }
  output.push_back('}');
  return true;
}

bool AppendActions(
    std::string &output,
    const game::ZhongguoScoreboardUnsupportedActionsV1 &actions) {
  output.push_back('{');
  if (!AppendNamed(output, "activate", actions.activate, AppendTypedBoolean,
                   true) ||
      !AppendNamed(output, "close", actions.close, AppendTypedBoolean) ||
      !AppendNamed(output, "reopen", actions.reopen, AppendTypedBoolean)) {
    return false;
  }
  output.push_back('}');
  return true;
}

void AppendReadiness(std::string &output,
                     const game::ZhongguoScoreboardStateReadinessV1 &value) {
  output += "{\"player_binding_ready\":";
  output += value.player_binding_ready ? "true" : "false";
  output += ",\"gui_root_ready\":";
  output += value.gui_root_ready ? "true" : "false";
  output += ",\"entry_window_state_ready\":";
  output += value.entry_window_state_ready ? "true" : "false";
  output += ",\"acl_ready\":";
  output += value.acl_ready ? "true" : "false";
  output += ",\"same_frame_ready\":";
  output += value.same_frame_ready ? "true" : "false";
  output += ",\"state_acl_query_ready\":";
  output += value.state_acl_query_ready ? "true" : "false";
  output += ",\"full_widget_gate_ready\":";
  output += value.full_widget_gate_ready ? "true" : "false";
  output += ",\"production_live_ready\":";
  output += value.production_live_ready ? "true" : "false";
  output.push_back('}');
}

} // namespace

std::string SerializeZhongguoScoreboardStateV1(
    const game::ZhongguoScoreboardStateV1 &snapshot) {
  const bool available =
      snapshot.status == game::ZhongguoScoreboardStateStatusV1::available;
  if (snapshot.case_kind != kZhongguoScoreboardStateV1CaseKind ||
      snapshot.request_nonce.empty() || snapshot.snapshot_revision == 0 ||
      snapshot.player_character_id <= 0 || !snapshot.paused ||
      (available ? !snapshot.unavailable_reason.empty()
                 : !ValidTopReason(snapshot.unavailable_reason))) {
    return {};
  }
  for (std::size_t index = 0; index < snapshot.widgets.size(); ++index) {
    if (snapshot.widgets[index].stable_identity !=
            kZhongguoScoreboardStateV1WidgetIdentities[index] ||
        snapshot.widgets[index].runtime_name !=
            kZhongguoScoreboardStateV1WidgetNames[index]) {
      return {};
    }
  }
  std::string output = "{\"schema_version\":1,\"status\":\"";
  output += available ? "available" : "unavailable";
  output += "\",\"case_kind\":";
  AppendJsonString(output, snapshot.case_kind);
  output += ",\"request_nonce\":";
  AppendJsonString(output, snapshot.request_nonce);
  output += ",\"snapshot_revision\":";
  if (!AppendNumber(output, snapshot.snapshot_revision)) return {};
  output += ",\"date_raw\":";
  if (!AppendNumber(output, snapshot.date_raw)) return {};
  output += ",\"paused\":true,\"player_character_id\":";
  if (!AppendNumber(output, snapshot.player_character_id)) return {};
  output += ",\"widgets\":[";
  for (std::size_t index = 0; index < snapshot.widgets.size(); ++index) {
    if (index != 0) output.push_back(',');
    if (!AppendWidget(output, snapshot.widgets[index])) return {};
  }
  output += "],\"acl\":{\"managed\":";
  if (!AppendManagedAcl(output, snapshot.managed_acl)) return {};
  output += ",\"received_self\":";
  if (!AppendReceivedAcl(output, snapshot.received_self_acl)) return {};
  output += "},\"actions\":";
  if (!AppendActions(output, snapshot.actions)) return {};
  output += ",\"readiness\":";
  AppendReadiness(output, snapshot.readiness);
  output += ",\"unavailable_reason\":";
  if (available) {
    output += "null";
  } else {
    AppendJsonString(output, snapshot.unavailable_reason);
  }
  output +=
      ",\"provenance\":{"
      "\"game_version\":\"1.19.0.6\","
      "\"executable_sha256\":\"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86\",";
  output += "\"backend_id\":";
  AppendJsonString(output, kZhongguoScoreboardStateV1BackendId);
  output += ",\"consumer_id\":";
  AppendJsonString(output, kZhongguoScoreboardStateV1ConsumerId);
  output += ",\"allowlist_id\":";
  AppendJsonString(output, kZhongguoScoreboardStateV1AllowlistId);
  output +=
      ",\"gui_global_slot_rva\":\"0x576CC68\","
      "\"find_top_level_widget_rva\":\"0x36D0B20\","
      "\"widget_hidden_flags_offset\":\"0xD0\","
      "\"widget_parent_offset\":\"0xE8\","
      "\"widget_children_offset\":\"0xF0\","
      "\"widget_name_offset\":\"0x1B8\","
      "\"query_scope\":\"fixed_scoreboard_instances_and_player_frozen_acl\","
      "\"contract_stage\":\"static_exact_build_live_unverified\"}}";
  return output;
}

} // namespace xar::ck3_11906
