#include "xar_bridge/entry_preceding_capture_12004.hpp"

namespace xar::ck3_12004 {
namespace {
void Boolean(std::string &output, bool value) { output += value ? "true" : "false"; }
void Id(std::string &output, const std::optional<std::uint32_t> &id) {
  output += id ? std::to_string(*id) : "null";
}
void Event(std::string &output, const PersonInstalledTransferEvent12004 &event) {
  output += "{\"clock_identity\":" + std::to_string(event.clock_identity) +
      ",\"sequence\":" + std::to_string(event.sequence) +
      ",\"thread_id\":";
  Id(output, event.thread_id);
  output += "}";
}
} // namespace

std::string SerializeEntryPrecedingCapture12004(const EntryPrecedingQuery12004 &query) {
  std::string output = "{\"schema\":\"xar.ck3.entry-preceding-capture-12004-v1\",\"configured\":";
  Boolean(output, query.configured);
  output += ",\"installed\":"; Boolean(output, query.installed);
  output += ",\"request_filtered\":"; Boolean(output, query.request_filtered);
  output += ",\"install_failure_flags\":" + std::to_string(query.install_failure_flags) +
      ",\"latest_record_sequence\":" + std::to_string(query.latest_record_sequence) +
      ",\"overwritten_records\":" + std::to_string(query.overwritten_records) +
      ",\"full_entry\":false,\"records\":[";
  bool comma = false;
  for (const auto &record : query.records) {
    if (comma) output += ',';
    comma = true;
    output += "{\"record_sequence\":" + std::to_string(record.record_sequence) +
        ",\"install_epoch\":" + std::to_string(record.install_epoch) +
        ",\"offline_fixture\":"; Boolean(output, record.offline_fixture);
    output += ",\"original_returned\":"; Boolean(output, record.original_returned);
    output += ",\"identity_stable\":"; Boolean(output, record.identity_stable);
    output += ",\"combat_identity\":" + std::to_string(record.combat_identity) +
        ",\"combat_full_id_before\":"; Id(output, record.combat_full_id_before);
    output += ",\"combat_full_id_after\":"; Id(output, record.combat_full_id_after);
    output += ",\"caller_return_rva\":" + std::to_string(record.caller_return_rva) +
        ",\"caller_return_slot\":" + std::to_string(record.caller_return_slot) +
        ",\"original_begin\":"; Event(output, record.original_begin);
    output += ",\"original_completion\":"; Event(output, record.original_completion);
    output += ",\"raw_return_bits\":" + std::to_string(record.raw_return_bits) +
        ",\"outer_invocation\":null}";
  }
  output += "]}";
  return output;
}

} // namespace xar::ck3_12004
