#include "xar_bridge/council_composition_candidate_observer_v1.hpp"

#include <charconv>
#include <string>

namespace xar::bridge {
namespace {

void Number(std::string &output, std::uint64_t value) {
  char buffer[32]{};
  const auto result = std::to_chars(buffer, buffer + sizeof(buffer), value);
  output.append(buffer, result.ptr);
}

void Hex64(std::string &output, std::uint64_t value) {
  constexpr char digits[] = "0123456789ABCDEF";
  output.push_back('"');
  for (int shift = 60; shift >= 0; shift -= 4) {
    output.push_back(digits[(value >> shift) & 0xFU]);
  }
  output.push_back('"');
}

void JsonString(std::string &output, const char *value) {
  output.push_back('"');
  for (; value != nullptr && *value != '\0'; ++value) {
    if (*value == '"' || *value == '\\') output.push_back('\\');
    output.push_back(*value);
  }
  output.push_back('"');
}

} // namespace

std::string SerializeCouncilCompositionCandidateObserverDiagnosticsV1(
    const CouncilCompositionCandidateObserverDiagnosticsV1 &diagnostics) {
  const auto &capture = diagnostics.observation;
  std::string output;
  output.reserve(512 + capture.last_captured_row_count * 72);
  output += "{\"private_build\":true,\"read_only\":true,\"advertised\":false";
  output += ",\"exact_build_sha256\":\"";
  output += kCouncilCompositionCandidateObserverExecutableSha256V1;
  output += "\",\"installed\":";
  output += diagnostics.installed ? "true" : "false";
  output += ",\"failure_flags\":";
  Number(output, diagnostics.failure_flags);
  output += ",\"capture\":{\"status\":\"";
  output += !capture.capture_consistent ? "inconsistent"
      : capture.capture_complete ? "captured" : "waiting";
  output += "\",\"call_count\":";
  Number(output, capture.call_count);
  output += ",\"accepted_count\":";
  Number(output, capture.accepted_count);
  output += ",\"rejected_count\":";
  Number(output, capture.rejected_count);
  output += ",\"ignored_after_capture_count\":";
  Number(output, capture.ignored_after_capture_count);
  output += ",\"capture_failure_flags\":";
  Number(output, capture.last_capture_failure_flags);
  output += ",\"consistent\":";
  output += capture.capture_consistent ? "true" : "false";
  output += ",\"complete\":";
  output += capture.capture_complete ? "true" : "false";
  output += ",\"ui_thread_id\":";
  Number(output, capture.last_ui_thread_id);
  output += ",\"thread_id\":";
  Number(output, capture.last_thread_id);
  output += ",\"timestamp_qpc\":";
  Number(output, capture.last_timestamp_qpc);
  output += ",\"owner_character_id\":";
  Number(output, capture.last_owner_character_id);
  output += ",\"active_task_id\":";
  Number(output, capture.last_active_task_id);
  output += ",\"position_key\":";
  JsonString(output, capture.last_position_key.data());
  output += ",\"vector_capacity\":";
  Number(output, static_cast<std::uint64_t>(capture.last_vector_capacity));
  output += ",\"vector_count\":";
  Number(output, static_cast<std::uint64_t>(capture.last_vector_count));
  output += ",\"captured_row_count\":";
  Number(output, capture.last_captured_row_count);
  output += ",\"duplicate_character_id_count\":";
  Number(output, capture.last_duplicate_character_id_count);
  output += ",\"rows\":[";
  for (std::uint32_t index = 0; index < capture.last_captured_row_count &&
       index < capture.rows.size(); ++index) {
    if (index != 0) output.push_back(',');
    output += "{\"character_id\":";
    Number(output, capture.rows[index].character_id);
    output += ",\"raw_row_bytes_hex\":";
    Hex64(output, capture.rows[index].raw_row_bytes);
    output.push_back('}');
  }
  output += "]}}";
  return output;
}

} // namespace xar::bridge
