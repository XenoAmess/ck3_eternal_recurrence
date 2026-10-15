#include "xar_bridge/frontend_gui_result_v1.hpp"
#include "xar_bridge/protocol.hpp"
#include "xar_bridge/ck3_12004_generic_gui.hpp"
#include "xar_bridge/ck3_12004_gui_callback_thunk.hpp"
#include "xar_bridge/ck3_12004_gui_expression_descriptor.hpp"

namespace xar::ck3_11906 {
namespace {
std::string Number(std::uint64_t value) { return std::to_string(value); }
void AppendJsonString(std::string &result, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  result += '"';
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      result += '\\';
      result += static_cast<char>(character);
    } else if (character < 0x20U) {
      result += "\\u00";
      result += hex[(character >> 4U) & 0x0FU];
      result += hex[character & 0x0FU];
    } else {
      result += static_cast<char>(character);
    }
  }
  result += '"';
}

} // namespace

std::string GenericGuiCommandResultFrameV1(std::string_view request_id,
                               std::string_view step, bool ok,
                               std::string_view status) {
  std::string result = "{\"type\":\"command_result\",\"protocol_version\":1,"
                       "\"request_id\":\"";
  result += request_id;
  result += "\",\"ok\":";
  result += ok ? "true" : "false";
  if (ok) {
    result += ",\"result\":{\"step\":\"";
    result += step;
    result += "\",\"accepted\":true,\"status\":\"";
    result += status;
    result += "\"}}";
  } else {
    result += ",\"error\":\"";
    result += status;
    result += "\"}";
  }
  return result;
}

std::string FrontendGuiTreeInspectionResultFrameV1(
    std::string_view request_id,
    std::string_view step,
    const xar::ck3_11906::NamedGuiTreeInspectionV1 &inspection) {
  static_assert(xar::ck3_11906::kNamedGuiTreeInspectionMaximumFrameBytesV1 == xar::bridge::kMaximumFrameBytes);
  if (inspection.widget_count > inspection.widgets.size() ||
      inspection.widget_count > xar::ck3_11906::kNamedGuiTreeInspectionMaximumWidgetsV1)
    return GenericGuiCommandResultFrameV1(request_id, step, false, "native GUI tree row budget is inconsistent");
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  AppendJsonString(result, request_id);
  result += ",\"ok\":true,\"result\":{\"step\":";
  AppendJsonString(result, step);
  result += ',';
  result += "\"accepted\":true,\"status\":\"";
  result += inspection.root_available ? "available" : "unavailable";
  result += "\",\"scope_root_name\":";
  AppendJsonString(result, inspection.scope_root_name);
  result += ",\"root_available\":";
  result += inspection.root_available ? "true" : "false";
  result += ",\"truncated\":";
  result += inspection.truncated ? "true" : "false";
  result += ",\"widget_count\":";
  result += Number(inspection.widget_count);
  if (inspection.standard_click_bindings_12004) {
    result += ",\"callback_binding_source_12004\":{\"executable_sha256\":";
    AppendJsonString(result, ck3_12004::kExecutableSha256);
    result += ",\"button_base_slot13_rva\":61476128,\"group_dispatch_rva\":61471280,\"input_modifier\":0";
    if (inspection.callback_thunk_3aa30e0_pin_verified) {
      result += ",\"indirect_target_thunk_rva\":" + Number(ck3_12004::kGuiCallbackThunkRva12004V1) +
          ",\"indirect_target_thunk_bytes_sha256\":";
      AppendJsonString(result, ck3_12004::kGuiCallbackThunkBytesSha25612004V1);
    }
    if (inspection.expression_layout_3a9f960_pin_verified) {
      result += ",\"expression_target_bridge_rva\":" + Number(ck3_12004::kGuiExpression3A9F960Rva12004V1) +
          ",\"expression_builder_rva\":" + Number(ck3_12004::kGuiExpression3AC38C0Rva12004V1) +
          ",\"expression_eval_rva\":" + Number(ck3_12004::kGuiExpression3E4C090Rva12004V1) +
          ",\"expression_layout_bytes_sha256\":";
      AppendJsonString(result, ck3_12004::kGuiExpressionLayoutBytesSha25612004V1);
    }
    result += '}';
  }
  result += ",\"widgets\":[";
  for (std::size_t index = 0; index < inspection.widget_count; ++index) {
    if (index != 0) result += ',';
    const auto &widget = inspection.widgets[index];
    result += "{\"runtime_name\":";
    AppendJsonString(result, widget.runtime_name);
    result += ",\"child_path\":";
    AppendJsonString(result, widget.child_path);
    result += ",\"depth\":";
    result += Number(widget.depth);
    result += ",\"child_count\":";
    result += Number(widget.child_count);
    result += ",\"vtable_rva\":";
    result += Number(widget.vtable_rva);
    result += ",\"effective_visible\":";
    result += widget.effective_visible ? "true" : "false";
    result += ",\"enabled\":";
    result += widget.enabled ? "true" : "false";
    if (inspection.standard_click_bindings_12004) {
      const auto &binding = widget.standard_click_binding_12004;
      if (binding.callbacks.size() > 256 ||
          (!binding.button_base_slot13 && (!binding.callbacks.empty() || binding.primary_group)) ||
          (binding.primary_group && binding.callbacks.empty()))
        return GenericGuiCommandResultFrameV1(request_id, step, false, "invalid standard click callback binding");
      result += ",\"standard_click_binding_12004\":{\"button_base_slot13\":";
      result += binding.button_base_slot13 ? "true" : "false";
      result += ",\"group\":";
      AppendJsonString(result, !binding.button_base_slot13 ? "not_button_base" :
                       binding.primary_group ? "primary" : "fallback");
      result += ",\"callbacks\":[";
      for (std::size_t callback_index = 0; callback_index < binding.callbacks.size(); ++callback_index) {
        if (callback_index != 0) result += ',';
        const auto &callback = binding.callbacks[callback_index];
        if (callback.index != callback_index || callback.callback_vtable_rva == 0 ||
            callback.callback_vtable_rva > ck3_12004::kGuiImageSize12004V1 - 24U ||
            callback.callback_slot2_rva == 0 ||
            callback.callback_slot2_rva >= ck3_12004::kGuiImageSize12004V1)
          return GenericGuiCommandResultFrameV1(request_id, step, false, "callback target outside exact image");
        const bool expected_indirect = inspection.callback_thunk_3aa30e0_pin_verified &&
            callback.callback_slot2_rva == ck3_12004::kGuiCallbackThunkRva12004V1;
        if (callback.indirect_target_3aa30e0 != expected_indirect ||
            (expected_indirect && (callback.native_target_8_rva == 0 ||
              callback.native_target_8_rva >= ck3_12004::kGuiImageSize12004V1)))
          return GenericGuiCommandResultFrameV1(request_id, step, false, "indirect callback source pin or target is inconsistent");
        const bool expected_expression = expected_indirect && inspection.expression_layout_3a9f960_pin_verified &&
            callback.native_target_8_rva == ck3_12004::kGuiExpression3A9F960Rva12004V1;
        const auto &expression = callback.expression_3a9f960;
        if (callback.expression_descriptor_3a9f960 != expected_expression ||
            (expected_expression && (expression.chain_count_24_raw != expression.chain_calls.size() ||
              expression.chain_count_24_raw > ck3_12004::kGuiExpressionMaximumChain12004V1 ||
              ((expression.final_kind_34_raw == 3 || expression.final_kind_34_raw == 4) ?
                (expression.final_target_38_rva == 0 || expression.final_target_38_rva >= ck3_12004::kGuiImageSize12004V1) :
                expression.final_target_38_rva != 0))))
          return GenericGuiCommandResultFrameV1(request_id, step, false, "invalid expression descriptor source or bounds");
        result += "{\"index\":" + Number(callback.index) +
            ",\"callback_vtable_rva\":" + Number(callback.callback_vtable_rva) +
            ",\"callback_slot2_rva\":" + Number(callback.callback_slot2_rva);
        if (expected_indirect) {
          result += ",\"indirect_target_3aa30e0\":{\"native_target_8_rva\":" + Number(callback.native_target_8_rva) +
              ",\"receiver_f0_present\":";
          result += callback.receiver_f0_present ? "true" : "false";
          if (expected_expression) {
            result += ",\"expression_3a9f960\":{\"chain_count_24_raw\":" + Number(expression.chain_count_24_raw) +
                ",\"final_type_id_30\":" + Number(expression.final_type_id_30) +
                ",\"final_kind_34_raw\":" + Number(expression.final_kind_34_raw) +
                ",\"final_target_38_rva\":" + Number(expression.final_target_38_rva) +
                ",\"final_user_data_40_present\":";
            result += expression.final_user_data_40_present ? "true" : "false";
            result += ",\"receiver_type_id_48\":" + Number(expression.receiver_type_id_48) +
                ",\"receiver_flag_4c_raw\":" + Number(expression.receiver_flag_4c_raw) + ",\"chain_calls\":[";
            for (std::size_t n = 0; n < expression.chain_calls.size(); ++n) {
              const auto &item = expression.chain_calls[n];
              if (item.index != n || item.native_target_8_rva == 0 || item.native_target_8_rva >= ck3_12004::kGuiImageSize12004V1)
                return GenericGuiCommandResultFrameV1(request_id, step, false, "invalid expression receiver-chain target");
              if (n != 0) result += ',';
              result += "{\"index\":" + Number(item.index) + ",\"type_id_0\":" + Number(item.type_id_0) +
                  ",\"kind_4_raw\":" + Number(item.kind_4_raw) + ",\"native_target_8_rva\":" + Number(item.native_target_8_rva) +
                  ",\"user_data_10_present\":";
              result += item.user_data_10_present ? "true" : "false"; result += '}';
            }
            result += "]}";
          }
          result += '}';
        }
        result += '}';
      }
      result += "]}";
    }
    result += '}';
    if (!xar::ck3_11906::NamedGuiTreeInspectionFrameBytesFitV1(result.size() + 3U))
      return GenericGuiCommandResultFrameV1(request_id, step, false, "native GUI tree exceeds bounded response byte budget");
  }
  result += "]}}";
  return result;
}

} // namespace xar::ck3_11906
