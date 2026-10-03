#include "xar_bridge/ck3_12003_county_conversion_task_action_v1.hpp"

namespace xar::ck3_12003::religion::county_conversion::action {
namespace {
namespace action = xar::ck3_12003::religion::county_conversion::action;
std::string Quote(std::string_view value) {
  std::string out = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char ch : value) {
    if (ch == '"' || ch == '\\') { out += '\\'; out += static_cast<char>(ch); }
    else if (ch < 0x20) {
      out += "\\u00";
      out += hex[ch >> 4]; out += hex[ch & 0x0f];
    } else out += static_cast<char>(ch);
  }
  return out + '"';
}
const char *Bool(bool value) noexcept { return value ? "true" : "false"; }
std::string Optional(const std::optional<bool> &value) {
  return value.has_value() ? Bool(*value) : "null";
}
template <class T> std::string Optional(const std::optional<T> &value) {
  return value.has_value() ? std::to_string(*value) : "null";
}
const char *Status(action::SubmitStatus value) noexcept {
  switch (value) {
  case action::SubmitStatus::already_active_noop: return "already_active_noop";
  case action::SubmitStatus::queued_verification_pending: return "queued_verification_pending";
  default: return "not_submitted";
  }
}
std::string SerializeTaskState(const action::TaskState &value) {
  return "{\"available\":" + std::string(Bool(value.available)) +
      ",\"failure\":" + Quote(value.failure) +
      ",\"capture_epoch\":" + std::to_string(value.capture_epoch) +
      ",\"date_raw\":" + std::to_string(value.date_raw) +
      ",\"owner_character_id\":" + std::to_string(value.owner_character_id) +
      ",\"incumbent_character_id\":" + Optional(value.incumbent_character_id) +
      ",\"active_task_id\":" + Optional(value.active_task_id) +
      ",\"task_key\":" + Quote(value.task_key) +
      ",\"target_scope_tag\":" + Optional(value.target_scope_tag) +
      ",\"target_province_id\":" + Optional(value.target_province_id) +
      ",\"target_county_title_id\":" + Optional(value.target_county_title_id) +
      ",\"progress_kind\":" + Optional(value.progress_kind) +
      ",\"percentage_progress_raw\":" + Optional(value.percentage_progress_raw) + "}";
}
} // namespace

std::string SerializeCountyConversionTaskSubmission12003(const action::Submission &value) {
  return "{\"status\":" + Quote(Status(value.status)) +
      ",\"failure\":" + Quote(value.failure) +
      ",\"request_id\":" + Quote(value.request_id) +
      ",\"request\":{\"expected_revision\":" + std::to_string(value.request.expected_revision) +
      ",\"expected_active_task_id\":" + std::to_string(value.request.expected_active_task_id) +
      ",\"expected_incumbent_character_id\":" + std::to_string(value.request.expected_incumbent_character_id) +
      ",\"province_id\":" + std::to_string(value.request.province_id) +
      ",\"replace_existing_task\":" + Bool(value.request.replace_existing_task) +
      ",\"action_id\":" + Quote(value.request.action_id) + "}" +
      ",\"native_revision\":" + std::to_string(value.native_revision) +
      ",\"capture_epoch\":" + std::to_string(value.capture_epoch) +
      ",\"date_raw\":" + std::to_string(value.date_raw) +
      ",\"played_character_id\":" + std::to_string(value.played_character_id) +
      ",\"target_county_title_id\":" + Optional(value.target_county_title_id) +
      ",\"native_final_can_dispatch\":" + Optional(value.native_final_can_dispatch) +
      ",\"command_channel\":" + std::to_string(value.command_channel) +
      ",\"native_submit_copy_called\":" + Bool(value.native_submit_copy_called) +
      ",\"before\":" + SerializeTaskState(value.before) + "}";
}
std::string SerializeCountyConversionTaskIndependentResult12003(const action::IndependentResult &value) {
  return "{\"request_id\":" + Quote(value.request_id) +
      ",\"action_id\":" + Quote(value.action_id) +
      ",\"submit_status\":" + Quote(Status(value.submit_status)) +
      ",\"verification_pending\":" + Bool(value.verification_pending) +
      ",\"after\":" + SerializeTaskState(value.after) +
      ",\"actual_task_id_unchanged\":" + Optional(value.actual_task_id_unchanged) +
      ",\"actual_task_assignment_matches\":" + Optional(value.actual_task_assignment_matches) +
      ",\"task_assignment_material_observed\":" + Bool(value.task_assignment_material_observed) +
      ",\"county_conversion_completed\":" + Bool(value.county_conversion_completed) + "}";
}
} // namespace xar::ck3_12003::religion::county_conversion::action
