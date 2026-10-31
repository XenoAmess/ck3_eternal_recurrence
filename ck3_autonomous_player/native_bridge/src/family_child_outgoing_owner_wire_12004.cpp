#include "xar_bridge/family_child_outgoing_owner_12004.hpp"
#include "xar_bridge/family_heir_outgoing_owner_12004.hpp"
#include "xar_bridge/family_child_matrilineal_materializer_12004.hpp"
#include "xar_bridge/family_heir_betrothal_materializer_12004.hpp"
#include "xar_bridge/family_ruler_default_materializer_12004.hpp"
#include "xar_bridge/family_marriage_outgoing_storage_12004.hpp"
#include "xar_bridge/family_marriage_send_outgoing_v2.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <stdexcept>
#include <cstdio>

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)

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

std::string SerializeUnavailablePreparedContext() {
  return R"json({"schema":"ck3-marriage-materialized-send-context-12004-v2","status":"unavailable","source":"original_native_marriage_context_builder","read_only":true,"send_invoked":false,"command_constructed":false,"role_arity":null,"sixth_role_id":null,"definition_stable_hash":null,"interaction_key":"arrange_marriage_interaction","complete_can_send":null,"matrilineal_option_selected":null,"grand_wedding_option_selected":null,"effective_matrilineal_if_accepted":null,"effective_roles":null,"selected_option_rows":[],"copy_passes":0,"unavailable_reason":"materialized_marriage_context_provider_unavailable"})json";
}

std::string SerializeUnavailableGroup(const FamilyMarriageOutgoingFrameV2 &frame) {
  std::string result = R"json({"schema":"ck3-family-outgoing-storage-12004-v4","status":"unavailable","source":"native_complete_outgoing_pending_storage_1.20.0.4","producer_scope":"complete_outgoing_storage","read_only":true,"complete":false,"passes":0,"scanned_slots":null,"actor_id":)json";
  result += std::to_string(frame.played_character_id);
  result += R"json(,"sender_character_id":null,"interaction_key":"arrange_marriage_interaction","definition_stable_hash":null,"occupied_pending_full_ids":[],"candidates":[],"unavailable_reason":"complete_outgoing_storage_provider_unavailable"})json";
  return result;
}

} // namespace

std::string SerializeFamilyChildOutgoingOwnerResult12004(
    std::string_view request_id, const FamilyMarriageOutgoingRequestV2 &request,
    const FamilyMarriageOutgoingFrameV2 &actual_frame,
    std::uint64_t query_sequence, const FamilyChildOwnerResult12004 &result) {

  if (request_id.empty()) {
    throw std::invalid_argument("empty request id");
  }
  if (query_sequence == 0) {
    throw std::invalid_argument("zero query sequence");
  }
  if (!ValidateFamilyMarriageOutgoingRequestV2(request, actual_frame)) {
    throw std::invalid_argument("invalid request/frame");
  }
  if (result.outcome != FamilyHeirOwnerOutcome12004::observed) {
    throw std::invalid_argument("result not observed");
  }
  if (!result.frame_observed) {
    throw std::invalid_argument("frame not observed");
  }
  if (request.route != FamilyMarriageOutgoingRouteV2::child_matrilineal &&
      request.route != FamilyMarriageOutgoingRouteV2::child_default) {
    throw std::invalid_argument("non-child route");
  }

  bool storage_complete = (result.storage_status == FamilyOutgoingStorageCopyStatus12004::complete);
  bool prepared_complete = (result.materialize_status == FamilyRulerMaterializeStatus12004::complete);
  bool has_prepared = result.prepared.has_value();

  // Consistency checks specific to child routes
  if (request.scope == FamilyMarriageOutgoingScopeV2::action_preparation) {
    // Identity is required only when claiming complete prepared or storage
    if ((prepared_complete || has_prepared || storage_complete) && !result.identity_observed) {
      throw std::invalid_argument("complete prepared/storage requires identity_observed");
    }

    if (storage_complete && !prepared_complete) {
      throw std::invalid_argument("complete storage with incomplete materialization");
    }
    if (prepared_complete && !has_prepared) {
      throw std::invalid_argument("complete materialization without prepared context");
    }
    if (has_prepared && !prepared_complete) {
      throw std::invalid_argument("prepared context with incomplete materialization");
    }

    // Verify roles against request for ANY complete prepared value, independent of storage status
    if (has_prepared && prepared_complete) {
      const auto &roles = result.prepared->materialized.roles;
      if (roles[0] != request.actor) {
        throw std::invalid_argument("prepared actor mismatch");
      }
      if (request.expected_recipient.has_value() && roles[1] != request.expected_recipient.value()) {
        throw std::invalid_argument("prepared recipient mismatch");
      }
      if (roles[2] != request.subject) {
        throw std::invalid_argument("prepared subject mismatch");
      }
      if (roles[3] != request.candidate) {
        throw std::invalid_argument("prepared candidate mismatch");
      }
      // Child route specific: selected matrilineal option must be true ONLY for child_matrilineal
      if (request.route == FamilyMarriageOutgoingRouteV2::child_matrilineal) {
        if (!result.prepared->materialized.matrilineal) {
          throw std::invalid_argument("child_matrilineal prepared context lacks selected matrilineal option");
        }
      }
      // child_default preserves actual copied raw Mat/effective Boolean/CanSend without policy enforcement here
    }

    // Cross-check hash/sender only when complete stock exists
    if (storage_complete && has_prepared) {
      if (result.storage.definition_hash != result.prepared->materialized.definition_hash) {
        throw std::invalid_argument("prepared/storage definition mismatch");
      }
      if (result.storage.sender_id != result.prepared->materialized.roles[0]) {
        throw std::invalid_argument("prepared/storage sender mismatch");
      }
    }
  } else {
    // POST_SUBMISSION
    if (has_prepared || prepared_complete) {
      throw std::invalid_argument("POST submission must not have prepared context");
    }
    if (storage_complete) {
      if (!request.sender.has_value()) {
        throw std::invalid_argument("POST storage complete without retained sender");
      }
      if (result.storage.sender_id != request.sender.value()) {
        throw std::invalid_argument("storage sender mismatch with request");
      }
    }
  }

  std::string out = R"json({"type":"command_result","protocol_version":1,"request_id":)json";
  AppendJsonString(out, request_id);
  out += R"json(,"ok":true,"result":{"schema":"ck3-family-marriage-outgoing-query-12004-v2","step":"query-family-marriage-send-outgoing-v1-private","accepted":true,"status":)json";

  out += storage_complete ? "\"available\"" : "\"unavailable\"";

  out += R"json(,"private_build":true,"read_only":true,"advertised":false,"backend_id":"native-headless","query_sequence":)json";
  out += std::to_string(query_sequence);
  out += R"json(,"snapshot_revision":)json";
  out += std::to_string(actual_frame.revision);
  out += R"json(,"date_raw":)json";
  out += std::to_string(actual_frame.date_raw);
  out += R"json(,"played_character_id":)json";
  out += std::to_string(actual_frame.played_character_id);
  out += R"json(,"read_scope":)json";

  if (request.scope == FamilyMarriageOutgoingScopeV2::action_preparation) {
    out += "\"ACTION_PREPARATION\"";
  } else {
    out += "\"POST_SUBMISSION\"";
  }

  out += R"json(,"prepared_context":)json";

  if (request.scope == FamilyMarriageOutgoingScopeV2::action_preparation) {
    if (prepared_complete && has_prepared) {
      out += SerializeFamilyHeirBetrothalPreparedContext12004(*result.prepared);
    } else {
      out += SerializeUnavailablePreparedContext();
    }
  } else {
    out += "null";
  }

  out += R"json(,"family_outgoing_requests":)json";

  if (storage_complete) {
    out += SerializeFamilyOutgoingStorageGroup12004(result.storage, actual_frame.played_character_id);
  } else {
    out += SerializeUnavailableGroup(actual_frame);
  }

  out += "}}";
  return out;
}

} // namespace xar::bridge

#endif
