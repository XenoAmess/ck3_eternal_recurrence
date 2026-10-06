// Include once after the release serializer's closing namespace; reuse AppendEscaped.
#include "xar_bridge/ck3_12003_prisoner_native_kinship.hpp"
namespace xar::ck3_12003 {
std::string SerializePrisonerNativeKinship12003(const PrisonerNativeKinship12003 &input) {
  std::string out = "{\"private_build\":true,\"read_only\":true,"
      "\"advertised\":false,\"action_surface_present\":false";
  if (!input.available) {
    out += ",\"status\":\"unavailable\",\"unavailable_reason\":";
    AppendEscaped(out, input.unavailable_reason.empty() ?
        std::string_view{"native_evaluation_unavailable"} : std::string_view{input.unavailable_reason});
    return out + '}';
  }
  out += ",\"status\":\"available\",\"snapshot_id\":";
  AppendEscaped(out, "native:" + std::to_string(input.frame.native_revision));
  out += ",\"native_revision\":" + std::to_string(input.frame.native_revision);
  out += ",\"proof_epoch\":" + std::to_string(input.frame.proof_epoch);
  out += ",\"date_raw\":" + std::to_string(input.frame.date_raw);
  out += ",\"source_ordinal\":" + std::to_string(input.source_ordinal);
  out += ",\"jailer_character_id\":" + std::to_string(input.jailer_character_id);
  out += ",\"prisoner_character_id\":" + std::to_string(input.prisoner_character_id);
  out += ",\"is_close_family_of_played_character\":";
  out += input.is_close_family_of_played_character ? "true" : "false";
  out += ",\"is_close_or_extended_family_of_played_character\":";
  out += input.is_close_or_extended_family_of_played_character ? "true" : "false";
  return out + '}';
}
} // namespace xar::ck3_12003
