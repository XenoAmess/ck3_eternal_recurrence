#include "xar_bridge/ck3_12002_sway_completion_invalidation_reason_mailbox.hpp"

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

std::string SerializeSwayCompletionInvalidationReasonCommandResultV1(
    const SwayInvalidationReasonQueryResult12002 &output, std::uint64_t snapshot_revision,
    std::int32_t date_raw, std::string_view request_id) {
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" +
      Quoted(request_id) + ",\"ok\":true,\"result\":{\"step\":" + Quoted(kSwayCompletionInvalidationReasonStepV1) +
      ",\"accepted\":true,\"status\":" + Quoted(output.available ? "available" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"snapshot_revision\":" +
      std::to_string(snapshot_revision) + ",\"date_raw\":" + std::to_string(date_raw) +
      ",\"build_version\":\"1.20.0.2\",\"executable_sha256\":" + Quoted(kExecutableSha256) +
      ",\"sway_completion_invalidation_reason\":" + SerializeSwayInvalidationReason12002(output) +
      ",\"backend_id\":\"native-headless\"}}";
}

} // namespace xar::ck3_12002
