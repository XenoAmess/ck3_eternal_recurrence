#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"

#include <array>
#include <charconv>
#include <cstdint>
#include <limits>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kWindowIndex = 1;
constexpr std::size_t kModalIndex = 2;
constexpr std::array<std::size_t, 3> kEntryIndices{4, 5, 6};
constexpr std::array<std::size_t, 3> kTabIndices{7, 8, 9};
constexpr std::size_t kHeaderCloseIndex = 14;
constexpr std::array<std::string_view, 3> kTabs{"managed", "received",
                                                        "system"};

bool ValidNonce(std::string_view value) noexcept {
  if (value.empty() || value.size() > 64) return false;
  for (std::size_t index = 0; index < value.size(); ++index) {
    const char current = value[index];
    const bool alpha = (current >= 'A' && current <= 'Z') ||
                       (current >= 'a' && current <= 'z');
    const bool digit = current >= '0' && current <= '9';
    const bool punctuation = current == '.' || current == '_' ||
                             current == ':' || current == '-';
    if ((!alpha && !digit && !punctuation) ||
        (index == 0 && !alpha && !digit)) {
      return false;
    }
  }
  return true;
}

bool ValidPointer(std::string_view value) noexcept {
  if (value.size() < 3 || value[0] != '0' || value[1] != 'x') return false;
  for (std::size_t index = 2; index < value.size(); ++index) {
    const char current = value[index];
    if (!((current >= '0' && current <= '9') ||
          (current >= 'A' && current <= 'F'))) {
      return false;
    }
  }
  return true;
}

std::string_view ActionName(game::ZhongguoScoreboardActionV1 value) noexcept {
  switch (value) {
  case game::ZhongguoScoreboardActionV1::open:
    return "open";
  case game::ZhongguoScoreboardActionV1::switch_managed:
    return "switch-managed";
  case game::ZhongguoScoreboardActionV1::switch_received:
    return "switch-received";
  case game::ZhongguoScoreboardActionV1::switch_system:
    return "switch-system";
  case game::ZhongguoScoreboardActionV1::close:
    return "close";
  case game::ZhongguoScoreboardActionV1::reopen:
    return "reopen";
  }
  return {};
}

game::ZhongguoScoreboardActionResultV1 Reject(
    const game::ZhongguoScoreboardActionRequestV1 &request,
    const game::ZhongguoScoreboardActionBindingV1 &binding,
    std::string_view reason,
    game::ZhongguoScoreboardActionAckV1 &ack) noexcept {
  ack = {};
  ack.request_nonce = request.request_nonce;
  ack.action = request.action;
  ack.source = binding;
  ack.rejection_reason.assign(reason);
  return game::ZhongguoScoreboardActionResultV1::rejected;
}

bool AvailableBool(const game::ZhongguoTypedBooleanV1 &field,
                   bool &value) noexcept {
  if (!field.available || !field.value.has_value()) return false;
  value = *field.value;
  return true;
}

bool AvailableString(const game::ZhongguoTypedStringV1 &field,
                     std::string_view &value) noexcept {
  if (!field.available || !field.value.has_value() ||
      !ValidPointer(*field.value)) {
    return false;
  }
  value = *field.value;
  return true;
}

bool FixedProjection(const game::ZhongguoScoreboardStateV1 &source) noexcept {
  for (std::size_t index = 0; index < source.widgets.size(); ++index) {
    if (source.widgets[index].stable_identity !=
            kZhongguoScoreboardStateV1WidgetIdentities[index] ||
        source.widgets[index].runtime_name !=
            kZhongguoScoreboardStateV1WidgetNames[index]) {
      return false;
    }
  }
  return true;
}

bool AppendNumber(std::string &output, std::uint64_t value) {
  std::array<char, 32> buffer{};
  const auto converted =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (converted.ec != std::errc{}) return false;
  output.append(buffer.data(), converted.ptr);
  return true;
}

bool AppendSigned(std::string &output, std::int32_t value) {
  std::array<char, 16> buffer{};
  const auto converted =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (converted.ec != std::errc{}) return false;
  output.append(buffer.data(), converted.ptr);
  return true;
}

void AppendJsonString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output.push_back('"');
  for (const unsigned char current : value) {
    if (current == '"' || current == '\\') {
      output.push_back('\\');
      output.push_back(static_cast<char>(current));
    } else if (current < 0x20) {
      output += "\\u00";
      output.push_back(hex[(current >> 4U) & 0x0FU]);
      output.push_back(hex[current & 0x0FU]);
    } else {
      output.push_back(static_cast<char>(current));
    }
  }
  output.push_back('"');
}

} // namespace

game::ZhongguoScoreboardActionResultV1 ExecuteZhongguoScoreboardActionV1(
    const game::ZhongguoScoreboardActionRequestV1 &request,
    const game::ZhongguoScoreboardActionBindingV1 &binding,
    const game::ZhongguoScoreboardStateV1 &source,
    const ZhongguoScoreboardActionAccessV1 &access,
    game::ZhongguoScoreboardActionAckV1 &ack) noexcept {
  const auto action_name = ActionName(request.action);
  if (action_name.empty() || !ValidNonce(request.request_nonce) ||
      request.expected_native_revision == 0 ||
      request.expected_connection_generation == 0 ||
      request.expected_player_character_id <= 0 ||
      !ValidPointer(request.expected_window_instance_pointer) ||
      !ValidPointer(request.expected_target_instance_pointer) ||
      !ValidPointer(request.expected_target_vtable_pointer)) {
    return Reject(request, binding, "invalid_request", ack);
  }
  if (request.expected_revision == std::numeric_limits<std::uint64_t>::max() ||
      request.expected_native_revision ==
          std::numeric_limits<std::uint64_t>::max()) {
    return Reject(request, binding, "revision_overflow", ack);
  }
  if (binding.revision != request.expected_revision) {
    return Reject(request, binding, "revision_mismatch", ack);
  }
  if (binding.native_revision != request.expected_native_revision ||
      source.snapshot_revision != request.expected_native_revision) {
    return Reject(request, binding, "native_revision_mismatch", ack);
  }
  if (binding.connection_generation !=
      request.expected_connection_generation) {
    return Reject(request, binding, "connection_generation_mismatch", ack);
  }
  if (binding.player_character_id != request.expected_player_character_id ||
      source.player_character_id != request.expected_player_character_id) {
    return Reject(request, binding, "player_binding_mismatch", ack);
  }
  if (source.status != game::ZhongguoScoreboardStateStatusV1::available ||
      !source.paused || source.date_raw != binding.date_raw ||
      !source.readiness.player_binding_ready ||
      !source.readiness.gui_root_ready ||
      !source.readiness.entry_window_state_ready ||
      !source.readiness.acl_ready || !source.readiness.same_frame_ready ||
      !source.readiness.state_acl_query_ready || !FixedProjection(source)) {
    return Reject(request, binding, "source_state_unavailable", ack);
  }

  const auto &window = source.widgets[kWindowIndex];
  bool window_exists = false;
  std::string_view window_instance;
  if (!AvailableBool(window.exists, window_exists) || !window_exists ||
      !AvailableString(window.instance_pointer, window_instance)) {
    return Reject(request, binding, "window_not_instantiated", ack);
  }
  if (window_instance != request.expected_window_instance_pointer) {
    return Reject(request, binding, "window_instance_mismatch", ack);
  }
  bool modal_visible = false;
  if (!AvailableBool(source.widgets[kModalIndex].effective_visible,
                     modal_visible)) {
    return Reject(request, binding, "modal_visibility_unavailable", ack);
  }

  std::size_t target_index = source.widgets.size();
  std::size_t active_tab_index = 0;
  bool active_tab_available = false;
  if (request.action == game::ZhongguoScoreboardActionV1::open ||
      request.action == game::ZhongguoScoreboardActionV1::reopen) {
    if (modal_visible) {
      return Reject(request, binding, "scoreboard_already_open", ack);
    }
    std::size_t visible_count = 0;
    for (std::size_t index = 0; index < kEntryIndices.size(); ++index) {
      bool visible = false;
      if (!AvailableBool(source.widgets[kEntryIndices[index]].effective_visible,
                         visible)) {
        return Reject(request, binding, "entry_visibility_unavailable", ack);
      }
      if (visible) {
        ++visible_count;
        target_index = kEntryIndices[index];
        active_tab_index = index;
      }
    }
    if (visible_count != 1) {
      return Reject(request, binding, "entry_target_not_unique", ack);
    }
    active_tab_available = true;
  } else if (request.action ==
                 game::ZhongguoScoreboardActionV1::switch_managed ||
             request.action ==
                 game::ZhongguoScoreboardActionV1::switch_received ||
             request.action ==
                 game::ZhongguoScoreboardActionV1::switch_system) {
    if (!modal_visible) {
      return Reject(request, binding, "scoreboard_not_open", ack);
    }
    active_tab_index =
        request.action == game::ZhongguoScoreboardActionV1::switch_managed
            ? 0
            : request.action ==
                      game::ZhongguoScoreboardActionV1::switch_received
                  ? 1
                  : 2;
    if (active_tab_index == 0 &&
        !source.managed_acl.current_player_can_assess_others) {
      return Reject(request, binding, "managed_acl_denied", ack);
    }
    if (active_tab_index == 1 &&
        !source.received_self_acl.surface_available) {
      return Reject(request, binding, "received_acl_denied", ack);
    }
    target_index = kTabIndices[active_tab_index];
    active_tab_available = true;
  } else if (request.action == game::ZhongguoScoreboardActionV1::close) {
    if (!modal_visible) {
      return Reject(request, binding, "scoreboard_not_open", ack);
    }
    target_index = kHeaderCloseIndex;
  } else {
    return Reject(request, binding, "invalid_request", ack);
  }

  const auto &target = source.widgets[target_index];
  bool exists = false;
  bool visible = false;
  bool enabled = false;
  std::string_view instance;
  std::string_view vtable;
  if (!AvailableBool(target.exists, exists)) {
    return Reject(request, binding, "target_exists_unavailable", ack);
  }
  if (!exists) {
    return Reject(request, binding, "target_not_instantiated", ack);
  }
  if (!AvailableBool(target.effective_visible, visible)) {
    return Reject(request, binding, "target_visibility_unavailable", ack);
  }
  if (!visible) {
    return Reject(request, binding, "target_not_visible", ack);
  }
  if (!AvailableBool(target.enabled, enabled)) {
    return Reject(request, binding, "target_enabled_unavailable", ack);
  }
  if (!enabled) {
    return Reject(request, binding, "target_disabled", ack);
  }
  if (!AvailableString(target.instance_pointer, instance)) {
    return Reject(request, binding, "target_instance_unavailable", ack);
  }
  if (!AvailableString(target.vtable_pointer, vtable)) {
    return Reject(request, binding, "target_vtable_unavailable", ack);
  }
  if (instance != request.expected_target_instance_pointer) {
    return Reject(request, binding, "target_instance_mismatch", ack);
  }
  if (vtable != request.expected_target_vtable_pointer) {
    return Reject(request, binding, "target_vtable_mismatch", ack);
  }
  if (access.dispatch == nullptr) {
    return Reject(request, binding, "action_dispatch_unavailable", ack);
  }
  if (!access.dispatch(access.context, request.action, target.stable_identity,
                       target.runtime_name, instance, vtable)) {
    return Reject(request, binding, "action_dispatch_rejected", ack);
  }

  ack = {};
  ack.result =
      game::ZhongguoScoreboardActionResultV1::acknowledged_verification_pending;
  ack.accepted = true;
  ack.request_nonce = request.request_nonce;
  ack.action = request.action;
  ack.source = binding;
  ack.window_instance_pointer.assign(window_instance);
  ack.target.stable_identity = target.stable_identity;
  ack.target.runtime_name = target.runtime_name;
  ack.target.instance_pointer.assign(instance);
  ack.target.vtable_pointer.assign(vtable);
  ack.expected_postcondition.minimum_revision = binding.revision + 1;
  ack.expected_postcondition.minimum_native_revision =
      binding.native_revision + 1;
  ack.expected_postcondition.modal_effective_visible =
      request.action != game::ZhongguoScoreboardActionV1::close;
  ack.expected_postcondition.active_tab_available = active_tab_available;
  if (active_tab_available) {
    ack.expected_postcondition.active_tab.assign(kTabs[active_tab_index]);
  }
  ack.expected_postcondition.list_view_required = active_tab_available;
  ack.expected_postcondition.expected_window_instance_pointer.assign(
      window_instance);
  ack.postcondition_verified = false;
  return ack.result;
}

std::string SerializeZhongguoScoreboardActionAckV1(
    const game::ZhongguoScoreboardActionAckV1 &ack) {
  const auto action = ActionName(ack.action);
  if (ack.result != game::ZhongguoScoreboardActionResultV1::
                        acknowledged_verification_pending ||
      !ack.accepted || !ack.rejection_reason.empty() || action.empty() ||
      !ValidNonce(ack.request_nonce) || ack.source.native_revision == 0 ||
      ack.source.connection_generation == 0 ||
      ack.source.player_character_id <= 0 ||
      !ValidPointer(ack.window_instance_pointer) ||
      !ValidPointer(ack.target.instance_pointer) ||
      !ValidPointer(ack.target.vtable_pointer) ||
      ack.target.stable_identity != ack.target.runtime_name ||
      !ack.expected_postcondition.requires_independent_query ||
      ack.expected_postcondition.minimum_revision != ack.source.revision + 1 ||
      ack.expected_postcondition.minimum_native_revision !=
          ack.source.native_revision + 1 ||
      ack.expected_postcondition.expected_window_instance_pointer !=
          ack.window_instance_pointer ||
      ack.postcondition_verified) {
    return {};
  }
  std::string output =
      "{\"schema_version\":1,\"status\":"
      "\"acknowledged_verification_pending\",\"accepted\":true,"
      "\"capability\":\"game.command.activate-zhongguo-scoreboard-v1\","
      "\"step\":\"activate-zhongguo-scoreboard-v1\",\"request_nonce\":";
  AppendJsonString(output, ack.request_nonce);
  output += ",\"action\":";
  AppendJsonString(output, action);
  output += ",\"source\":{\"revision\":";
  if (!AppendNumber(output, ack.source.revision)) return {};
  output += ",\"native_revision\":";
  if (!AppendNumber(output, ack.source.native_revision)) return {};
  output += ",\"connection_generation\":";
  if (!AppendNumber(output, ack.source.connection_generation)) return {};
  output += ",\"date_raw\":";
  if (!AppendSigned(output, ack.source.date_raw)) return {};
  output += ",\"player_character_id\":";
  if (!AppendSigned(output, ack.source.player_character_id)) return {};
  output += ",\"window_instance_pointer\":";
  AppendJsonString(output, ack.window_instance_pointer);
  output += "},\"target\":{\"stable_identity\":";
  AppendJsonString(output, ack.target.stable_identity);
  output += ",\"runtime_name\":";
  AppendJsonString(output, ack.target.runtime_name);
  output += ",\"instance_pointer\":";
  AppendJsonString(output, ack.target.instance_pointer);
  output += ",\"vtable_pointer\":";
  AppendJsonString(output, ack.target.vtable_pointer);
  output +=
      "},\"expected_postcondition\":{\"requires_independent_query\":true,"
      "\"minimum_revision\":";
  if (!AppendNumber(output, ack.expected_postcondition.minimum_revision)) {
    return {};
  }
  output += ",\"minimum_native_revision\":";
  if (!AppendNumber(output,
                    ack.expected_postcondition.minimum_native_revision)) {
    return {};
  }
  output += ",\"modal_effective_visible\":";
  output += ack.expected_postcondition.modal_effective_visible ? "true" : "false";
  output += ",\"active_tab\":";
  if (ack.expected_postcondition.active_tab_available) {
    AppendJsonString(output, ack.expected_postcondition.active_tab);
  } else {
    output += "null";
  }
  output += ",\"list_view_required\":";
  output += ack.expected_postcondition.list_view_required ? "true" : "false";
  output += ",\"expected_window_instance_pointer\":";
  AppendJsonString(
      output, ack.expected_postcondition.expected_window_instance_pointer);
  output +=
      "},\"postcondition_verified\":false,\"provenance\":{"
      "\"game_version\":\"1.19.0.6\","
      "\"executable_sha256\":"
      "\"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86\","
      "\"backend_id\":\"ck3-1.19.0.6-native-zhongguo-scoreboard-action-v1\","
      "\"consumer_id\":\"xar-autoplayer-zhongguo-scoreboard-action-v1\","
      "\"allowlist_id\":\"zg361-scoreboard-named-widget-action-v1\","
      "\"contract_stage\":\"static_action_contract_live_unverified\"}}";
  return output;
}

} // namespace xar::ck3_11906
