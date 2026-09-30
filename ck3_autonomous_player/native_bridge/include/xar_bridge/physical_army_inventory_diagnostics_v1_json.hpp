#pragma once

#include "xar_bridge/ck3_11906.hpp"

namespace xar::ck3_11906 {

inline void AppendPhysicalArmyInventoryScanDiagnosticsV1(
    std::string &output, const PhysicalArmyInventoryScanDiagnosticsV1 &scan) {
  output += "{\"performed\":";
  output += scan.performed ? "true" : "false";
  output += ",\"date_raw\":" + std::to_string(scan.date_raw);
  output += ",\"war_id\":" + std::to_string(scan.war_id);
  output += ",\"subject_army_id\":" + std::to_string(scan.subject_army_id);
  output += ",\"storage_capacity\":" + std::to_string(scan.storage_capacity);
  output += ",\"noncanonical_slots\":" + std::to_string(scan.noncanonical_slots);
  output += ",\"sample_limit\":" +
      std::to_string(kPhysicalArmyNoncanonicalSampleLimitV1);
  output += ",\"sample_count\":" + std::to_string(scan.sample_count);
  output += ",\"truncated\":";
  output += scan.truncated ? "true" : "false";
  output += ",\"samples\":[";
  for (std::size_t index = 0; index < scan.sample_count; ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &sample = scan.samples[index];
    output += "{\"slot_index\":" + std::to_string(sample.slot_index);
    output += ",\"public_cunit_id\":" + std::to_string(sample.public_cunit_id);
    output += ",\"raw_kind\":" + std::to_string(sample.raw_kind);
    output += ",\"carmy_resolution_attempted\":";
    output += sample.carmy_resolution_attempted ? "true" : "false";
    output += ",\"native_carmy_id\":";
    output += sample.carmy_resolution_attempted
        ? std::to_string(sample.native_carmy_id) : "null";
    output += ",\"carmy_resolved\":";
    output += sample.carmy_resolved ? "true" : "false";
    output += ",\"canonical_cunit_id\":";
    output += sample.carmy_resolved
        ? std::to_string(sample.canonical_cunit_id) : "null";
    // Reasons are fixed classifier literals, never external/native text.
    output += ",\"reason\":\"";
    output += sample.reason;
    output += "\"}";
  }
  output += "]}";
}

inline void AppendPhysicalArmyInventoryDiagnosticsV1(
    std::string &output, const PhysicalArmyInventoryDiagnosticsV1 &diagnostic,
    PhysicalArmyInventoryStatusV1 reader_status) {
  const std::string_view status =
      reader_status == PhysicalArmyInventoryStatusV1::complete ? "complete" :
      reader_status == PhysicalArmyInventoryStatusV1::partial ? "partial" :
      reader_status == PhysicalArmyInventoryStatusV1::requires_paused
          ? "requires_paused" : "unavailable";
  output += "{\"reader_status\":\"";
  output += status;
  output += "\",\"first_scan\":";
  AppendPhysicalArmyInventoryScanDiagnosticsV1(output, diagnostic.first_scan);
  output += ",\"second_scan\":";
  AppendPhysicalArmyInventoryScanDiagnosticsV1(output, diagnostic.second_scan);
  output += '}';
}

} // namespace xar::ck3_11906
