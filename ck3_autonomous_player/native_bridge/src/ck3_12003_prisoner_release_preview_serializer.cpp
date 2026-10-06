#include "xar_bridge/ck3_12003_prisoner_release_preview.hpp"

namespace xar::ck3_12003 {
namespace {

void AppendEscaped(std::string &output, std::string_view value) {
  static constexpr char hex[] = "0123456789ABCDEF";
  output.push_back('"');
  for (const unsigned char character : value) {
    switch (character) {
    case '"': output += "\\\""; break;
    case '\\': output += "\\\\"; break;
    case '\b': output += "\\b"; break;
    case '\f': output += "\\f"; break;
    case '\n': output += "\\n"; break;
    case '\r': output += "\\r"; break;
    case '\t': output += "\\t"; break;
    default:
      if (character < 0x20U) {
        output += "\\u00";
        output.push_back(hex[(character >> 4U) & 0x0FU]);
        output.push_back(hex[character & 0x0FU]);
      } else {
        output.push_back(static_cast<char>(character));
      }
    }
  }
  output.push_back('"');
}

} // namespace

std::string SerializePrisonerReleasePreview12003(
    const PrisonerReleasePreview12003 &preview) {
  std::string output =
      "{\"private_build\":true,\"read_only\":true,"
      "\"advertised\":false,\"action_surface_present\":false";
  if (!preview.available) {
    output += ",\"status\":\"unavailable\",\"unavailable_reason\":";
    AppendEscaped(output, preview.unavailable_reason.empty() ?
        std::string_view{"native_evaluation_unavailable"} :
        std::string_view{preview.unavailable_reason});
    output += '}';
    return output;
  }
  output += ",\"status\":\"available\",\"snapshot_id\":";
  AppendEscaped(output, "native:" + std::to_string(preview.frame.native_revision));
  // Private collection wires use the native revision as their inner public
  // revision. The existing transport binds it to the actual public snapshot.
  output += ",\"public_revision\":" + std::to_string(preview.frame.native_revision);
  output += ",\"native_revision\":" + std::to_string(preview.frame.native_revision);
  output += ",\"proof_epoch\":" + std::to_string(preview.frame.proof_epoch);
  output += ",\"date_raw\":" + std::to_string(preview.frame.date_raw);
  output += ",\"definition\":{\"canonical_key\":";
  AppendEscaped(output, preview.definition_key);
  output += ",\"deterministic_key_hash\":" + std::to_string(preview.definition_stable_hash);
  output += ",\"runtime_ordinal\":" + std::to_string(preview.definition_ordinal) + '}';
  output += ",\"payload_shape\":\"two_role_all_release_options_off\"";
  output += ",\"roles\":{\"actor_character_id\":" +
      std::to_string(preview.actor_character_id);
  output += ",\"recipient_character_id\":" +
      std::to_string(preview.recipient_character_id) + '}';
  output += ",\"puppet_or_actor_character_id\":" +
      std::to_string(preview.puppet_or_actor_character_id);
  output += ",\"unconditional_prisoner_release\":true,\"option_keys\":[";
  for (std::size_t i = 0; i < kPrisonerReleaseOptionKeys12003.size(); ++i) {
    if (i != 0) output.push_back(',');
    AppendEscaped(output, kPrisonerReleaseOptionKeys12003[i]);
  }
  output += "],\"selected_option_mask_bits\":" +
      std::to_string(preview.selected_option_mask_bits);
  output += ",\"can_send\":";
  output += preview.can_send ? "true" : "false";
  output += ",\"costs\":{\"raw_scale\":" + std::to_string(preview.raw_scale) +
      ",\"payer_role\":\"actor\",\"application_timing\":\"on_send\",\"entries\":[";
  for (std::size_t i = 0; i < kPrisonerReleaseCostKeys12003.size(); ++i) {
    if (i != 0) output.push_back(',');
    output += "{\"resource_key\":";
    AppendEscaped(output, kPrisonerReleaseCostKeys12003[i]);
    output += ",\"raw\":" + std::to_string(preview.send_costs_raw[i]) + '}';
  }
  output += "]},\"acceptance\":{\"kind\":\"auto_accept\",\"auto_accept\":";
  output += preview.auto_accept ? "true" : "false";
  output += ",\"would_accept_now\":";
  output += preview.auto_accept ? "true" : "false";
  output += "},\"readiness\":{\"definition_ready\":true,\"actor_ready\":true,"
      "\"recipient_ready\":true,\"finalized_context_ready\":true,"
      "\"can_send_ready\":true,\"costs_ready\":true,"
      "\"acceptance_ready\":true,\"same_frame_ready\":true}}";
  return output;
}

} // namespace xar::ck3_12003
