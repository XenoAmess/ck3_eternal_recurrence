#include "xar_bridge/ck3_12002_sway_completion_termination_mailbox.hpp"

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

std::string SerializeSwayCompletionTerminationCommandResultV1(
    const SwayTerminationQueryResult12002 &output, std::uint64_t snapshot_revision,
    std::int32_t date_raw, std::string_view request_id,
    std::string_view build_version, std::string_view executable_sha256) {
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" +
      Quoted(request_id) + ",\"ok\":true,\"result\":{\"step\":" + Quoted(kSwayCompletionTerminationStepV1) +
      ",\"accepted\":true,\"status\":" + Quoted(output.available ? "available" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"snapshot_revision\":" +
      std::to_string(snapshot_revision) + ",\"date_raw\":" + std::to_string(date_raw) +
      ",\"build_version\":" + Quoted(build_version) +
      ",\"executable_sha256\":" + Quoted(executable_sha256) +
      ",\"sway_completion_termination\":" + SerializeSwayCompletionTermination12002(output) +
      ",\"backend_id\":\"native-headless\"}}";
}

} // namespace xar::ck3_12002
