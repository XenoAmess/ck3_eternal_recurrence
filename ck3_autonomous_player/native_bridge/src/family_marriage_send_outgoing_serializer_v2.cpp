#include "xar_bridge/family_marriage_send_outgoing_v2.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <stdexcept>
#include <cstdio>

namespace xar::bridge {

namespace {

void AppendJsonString(std::string &out, std::string_view value) {
  out += '"';
  for (char c : value) {
    switch (c) {
      case '"': out += "\\\""; break;
      case '\\': out += "\\\\"; break;
      case '\b': out += "\\b"; break;
      case '\f': out += "\\f"; break;
      case '\n': out += "\\n"; break;
      case '\r': out += "\\r"; break;
      case '\t': out += "\\t"; break;
      default:
        if (static_cast<unsigned char>(c) < 0x20) {
          char buf[8];
          std::snprintf(buf, sizeof(buf), "\\u%04x", static_cast<unsigned int>(static_cast<unsigned char>(c)));
          out += buf;
        } else {
          out += c;
        }
        break;
    }
  }
  out += '"';
}

std::string SerializeFamilyOutgoingUnavailableGroup(const FamilyMarriageOutgoingFrameV2 &frame) {
  std::string result = R"json({"schema":"ck3-family-outgoing-storage-12004-v4","status":"unavailable","source":"native_complete_outgoing_pending_storage_1.20.0.4","producer_scope":"complete_outgoing_storage","read_only":true,"complete":false,"passes":0,"scanned_slots":null,"actor_id":)json";
  result += std::to_string(frame.played_character_id);
  result += R"json(,"sender_character_id":null,"interaction_key":"arrange_marriage_interaction","definition_stable_hash":null,"occupied_pending_full_ids":[],"candidates":[],"unavailable_reason":"complete_outgoing_storage_provider_unavailable"})json";
  return result;
}

std::string SerializeFamilyMarriageOutgoingUnavailablePreparedContext() {
  return R"json({"schema":"ck3-marriage-materialized-send-context-12004-v2","status":"unavailable","source":"original_native_marriage_context_builder","read_only":true,"send_invoked":false,"command_constructed":false,"role_arity":null,"sixth_role_id":null,"definition_stable_hash":null,"interaction_key":"arrange_marriage_interaction","complete_can_send":null,"matrilineal_option_selected":null,"grand_wedding_option_selected":null,"effective_matrilineal_if_accepted":null,"effective_roles":null,"selected_option_rows":[],"copy_passes":0,"unavailable_reason":"materialized_marriage_context_provider_unavailable"})json";
}

} // namespace

std::string FamilyMarriageOutgoingUnavailableResultV2(
    std::string_view request_id, const FamilyMarriageOutgoingRequestV2 &request,
    const FamilyMarriageOutgoingFrameV2 &frame, std::uint64_t query_sequence) {
  if (request_id.empty()) {
    throw std::invalid_argument("empty request id");
  }
  if (query_sequence == 0) {
    throw std::invalid_argument("zero query sequence");
  }
  if (!ValidateFamilyMarriageOutgoingRequestV2(request, frame)) {
    throw std::invalid_argument("invalid request/frame");
  }

  std::string result = R"json({"type":"command_result","protocol_version":1,"request_id":)json";
  AppendJsonString(result, request_id);
  result += R"json(,"ok":true,"result":{"schema":"ck3-family-marriage-outgoing-query-12004-v2","step":"query-family-marriage-send-outgoing-v1-private","accepted":true,"status":"unavailable","private_build":true,"read_only":true,"advertised":false,"backend_id":"native-headless","query_sequence":)json";
  result += std::to_string(query_sequence);
  result += R"json(,"snapshot_revision":)json";
  result += std::to_string(frame.revision);
  result += R"json(,"date_raw":)json";
  result += std::to_string(frame.date_raw);
  result += R"json(,"played_character_id":)json";
  result += std::to_string(frame.played_character_id);
  result += R"json(,"read_scope":)json";
  if (request.scope == FamilyMarriageOutgoingScopeV2::action_preparation) {
    result += "\"ACTION_PREPARATION\"";
  } else {
    result += "\"POST_SUBMISSION\"";
  }
  result += R"json(,"prepared_context":)json";
  if (request.scope == FamilyMarriageOutgoingScopeV2::action_preparation) {
    result += SerializeFamilyMarriageOutgoingUnavailablePreparedContext();
  } else {
    result += "null";
  }
  result += R"json(,"family_outgoing_requests":)json";
  result += SerializeFamilyOutgoingUnavailableGroup(frame);
  result += "}}";
  return result;
}

} // namespace xar::bridge
