#pragma once

#include "xar_bridge/frame_write_diagnostic_v1.hpp"
#include "xar_bridge/protocol.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::bridge {

// Owned by the existing bridge WorkerState and read by its heartbeat writer.
// A plain fallback WriteFrame must leave the original Army outcome intact.
struct ArmyStrengthResultWriteDiagnosticV1 {
  bool recorded = false;
  std::uint64_t query_sequence = 0;
  FrameWriteDiagnostic frame;
};

inline bool WriteArmyStrengthResultFrameV1(
    HANDLE pipe, std::string_view rendered_payload,
    std::uint64_t query_sequence,
    ArmyStrengthResultWriteDiagnosticV1 &diagnostic) noexcept {
  diagnostic.recorded = true;
  diagnostic.query_sequence = query_sequence;
  diagnostic.frame = {};
  return WriteFrame(pipe, rendered_payload, &diagnostic.frame);
}

inline std::string SerializeArmyStrengthResultWriteDiagnosticV1(
    const ArmyStrengthResultWriteDiagnosticV1 &diagnostic) {
  if (!diagnostic.recorded) return "null";
  const auto &frame = diagnostic.frame;
  std::string result = "{\"query_sequence\":";
  result += std::to_string(diagnostic.query_sequence);
  result += ",\"payload_bytes\":" + std::to_string(frame.payload_bytes);
  result += ",\"limit_bytes\":" + std::to_string(frame.limit_bytes);
  result += ",\"stage\":\"";
  result += FrameWriteStageName(frame.stage);
  result += "\",\"success\":";
  result += frame.success ? "true" : "false";
  result += ",\"windows_error\":";
  result += frame.windows_error ? std::to_string(*frame.windows_error) : "null";
  result += '}';
  return result;
}

inline std::string ArmyStrengthResultSizeLimitErrorV1(
    const FrameWriteDiagnostic &diagnostic) {
  return "CK3 army-strength result exceeds existing native frame limit "
         "(payload_bytes=" + std::to_string(diagnostic.payload_bytes) +
         ";limit_bytes=" + std::to_string(diagnostic.limit_bytes) + ')';
}

} // namespace xar::bridge
