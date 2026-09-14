#include "xar_bridge/domain_construction_candidate_observer_v1_serializer.hpp"

#include <array>
#include <cstdint>
#include <string>

namespace xar::bridge {
namespace {

constexpr std::array<char, 16> kHex{
    '0', '1', '2', '3', '4', '5', '6', '7',
    '8', '9', 'A', 'B', 'C', 'D', 'E', 'F'};

void AppendBool(std::string &output, bool value) {
  output += value ? "true" : "false";
}

void AppendHexBytes(std::string &output, const std::uint8_t *bytes,
                    std::size_t size) {
  output.push_back('"');
  for (std::size_t index = 0; index < size; ++index) {
    output.push_back(kHex[(bytes[index] >> 4) & 0xF]);
    output.push_back(kHex[bytes[index] & 0xF]);
  }
  output.push_back('"');
}

void AppendHexU64(std::string &output, std::uint64_t value) {
  output.push_back('"');
  for (int shift = 60; shift >= 0; shift -= 4) {
    output.push_back(kHex[(value >> shift) & 0xF]);
  }
  output.push_back('"');
}

} // namespace

std::string SerializeDomainConstructionCandidateObserverV1(
    const DomainConstructionCandidateObserverDiagnosticsV1 &diagnostics) {
  const auto &capture = diagnostics.observation;
  const bool captured = capture.accepted_capture_count != 0;
  std::string output;
  output.reserve(2048 +
                 capture.last_captured_row_count * 192);
  output += "{\"schema_version\":1,\"private_key\":\"";
  output += kDomainConstructionCandidateObserverPrivateKeyV1;
  output += "\",\"artifact_stem\":\"";
  output += kDomainConstructionCandidateObserverArtifactStemV1;
  output += "\",\"status\":\"";
  output += captured
      ? (diagnostics.offline_fixture
             ? "fixture-captured-private-raw"
             : "production-captured-private-raw")
      : "waiting-for-paused-application-main";
  output += "\",\"exact_build\":{\"product_version\":\"1.19.0.6\","
            "\"executable_sha256\":\"";
  output += kDomainConstructionCandidateObserverExecutableSha256V1;
  output += "\"},\"installed\":";
  AppendBool(output, diagnostics.installed);
  output += ",\"offline_fixture\":";
  AppendBool(output, diagnostics.offline_fixture);
  output += ",\"failure_flags\":";
  output += std::to_string(diagnostics.failure_flags);
  output += ",\"readiness\":{\"paused_application_main_capture\":";
  AppendBool(output, captured);
  output += ",\"candidate_identity_decoded\":false,"
            "\"native_legality_decoded\":false},\"counters\":{";
  output += "\"producer_calls\":" +
      std::to_string(capture.producer_call_count);
  output += ",\"rejected_application_main\":" +
      std::to_string(capture.rejected_application_main_count);
  output += ",\"rejected_paused\":" +
      std::to_string(capture.rejected_paused_count);
  output += ",\"capture_read_failures\":" +
      std::to_string(capture.capture_read_failure_count);
  output += ",\"accepted_captures\":" +
      std::to_string(capture.accepted_capture_count);
  output += "},\"capture\":{\"published_generation\":" +
      std::to_string(capture.published_generation);
  output += ",\"proof_epoch\":" +
      std::to_string(capture.last_proof_epoch);
  output += ",\"date_raw\":" + std::to_string(capture.last_date_raw);
  output += ",\"thread_id\":" +
      std::to_string(capture.last_thread_id);
  output += ",\"timestamp_qpc\":" +
      std::to_string(capture.last_timestamp_qpc);
  output += ",\"vector_capacity\":" +
      std::to_string(capture.last_vector_capacity);
  output += ",\"vector_count\":" +
      std::to_string(capture.last_vector_count);
  output += ",\"captured_row_count\":" +
      std::to_string(capture.last_captured_row_count);
  output += ",\"rows_truncated\":";
  AppendBool(output, capture.last_rows_truncated);
  output += ",\"rows\":[";
  for (std::size_t index = 0;
       index < capture.last_captured_row_count &&
       index < capture.rows.size(); ++index) {
    if (index != 0) output.push_back(',');
    output += "{\"index\":" + std::to_string(index);
    output += ",\"score_raw\":" +
        std::to_string(capture.rows[index].score_raw);
    output += ",\"row_bytes_hex\":";
    AppendHexBytes(output, capture.rows[index].row_bytes.data(),
                   capture.rows[index].row_bytes.size());
    output += ",\"row_bytes_fnv1a64\":";
    AppendHexU64(output, capture.rows[index].row_bytes_fnv1a64);
    output.push_back('}');
  }
  output += "]},\"raw_pointer_fields_persisted\":false,"
            "\"row_bytes_reinterpreted_after_capture\":false,"
            "\"next_reverse_engineering_entry\":\"";
  output += kDomainConstructionCandidateObserverNextReverseEngineeringEntryV1;
  output += "\"}";
  return output;
}

} // namespace xar::bridge
