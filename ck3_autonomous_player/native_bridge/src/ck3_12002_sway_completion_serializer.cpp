#include "xar_bridge/ck3_12002_sway_completion_mailbox.hpp"

#include <sstream>

namespace xar::ck3_12002 {
namespace {
std::string Quoted(std::string_view value) {
  std::string output = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char ch : value) {
    if (ch == '\\' || ch == '"') {
      output += '\\';
      output += static_cast<char>(ch);
    } else if (ch < 32) {
      output += "\\u00";
      output += hex[ch >> 4];
      output += hex[ch & 15];
    } else {
      output += static_cast<char>(ch);
    }
  }
  return output + '"';
}
} // namespace

std::string SerializeSwayCompletion12002(const SwayCompletionStateV1 &output,
                                       std::uint64_t snapshot_revision,
                                       std::int32_t date_raw) {
  std::ostringstream stream;
  stream << std::boolalpha
      << "{\"schema\":\"xar.ck3.sway_completion.v1\",\"schema_version\":1"
      << ",\"build_version\":\"1.20.0.2\",\"executable_sha256\":" << Quoted(kExecutableSha256)
      << ",\"adapter_id\":\"ck3-1.20.0.2-msvc-x64\",\"private_build\":true,\"read_only\":true,\"advertised\":false"
      << ",\"available\":" << output.available
      << ",\"unavailable_reason\":" << Quoted(output.unavailable_reason)
      << ",\"snapshot_revision\":" << snapshot_revision
      << ",\"date_raw\":" << date_raw
      << ",\"actor_character_id\":" << output.request.actor_character_id
      << ",\"target_character_id\":" << output.request.target_character_id
      << ",\"scheme_instance_id\":" << output.request.scheme_id
      << ",\"scheme_instance_generation\":" << output.scheme_instance_generation
      << ",\"native_source_kind\":\"native_scheme_storage\""
      << ",\"current_instance_retention\":\"until_native_manager_purge\""
      << ",\"instance_source_observed\":" << output.instance_source_observed
      << ",\"instance_present\":" << output.instance_present
      << ",\"storage_slot_reused\":" << output.storage_slot_reused
      << ",\"exact_instance_join_ready\":" << output.exact_instance_join_ready
      << ",\"native_owner_raw\":";
  if (output.instance_present) {
    stream << output.native_owner_raw;
  } else {
    stream << "null";
  }
  stream << ",\"owner_matches_actor\":" << output.owner_matches_actor
      << ",\"owner_cleared\":" << output.owner_cleared
      << ",\"native_status_observed\":" << output.native_status_observed
      << ",\"native_status_raw\":";
  if (output.native_status_observed) {
    stream << output.native_status_raw;
  } else {
    stream << "null";
  }
  stream << ",\"native_status_key\":" << Quoted(output.native_status_key)
      << ",\"native_terminal_state_observed\":" << output.native_terminal_state_observed
      << ",\"native_success_chance_observed\":" << output.native_success_chance_observed
      << ",\"native_success_chance_raw\":";
  if (output.native_success_chance_observed) {
    stream << output.native_success_chance_raw;
  } else {
    stream << "null";
  }
  stream << ",\"native_success_chance_scale\":" << output.native_success_chance_scale
      << ",\"native_success_chance_unit\":\"percent\""
      << ",\"native_can_continue_observed\":" << output.native_can_continue_observed
      << ",\"native_can_continue\":";
  if (output.native_can_continue_observed) {
    stream << output.native_can_continue;
  } else {
    stream << "null";
  }
  stream
      << ",\"terminal_cause_observed\":" << output.terminal_cause_observed
      << ",\"terminal_cause\":" << Quoted(output.terminal_cause)
      << '}';
  return stream.str();
}

std::string SerializeSwayCompletionCommandResultV1(
    const SwayCompletionStateV1 &output, std::uint64_t snapshot_revision,
    std::int32_t date_raw, std::string_view request_id) {
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" +
      Quoted(request_id) + ",\"ok\":true,\"result\":{\"step\":" + Quoted(kSwayCompletionStepV1) +
      ",\"accepted\":true,\"status\":" + Quoted(output.available ? "available" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"sway_completion\":" +
      SerializeSwayCompletion12002(output, snapshot_revision, date_raw) +
      ",\"backend_id\":\"native-headless\"}}";
}

} // namespace xar::ck3_12002
