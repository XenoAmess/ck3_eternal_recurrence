#include "xar_bridge/religion_rite_governance12002_clergy_mailbox.hpp"

#include <stdexcept>
#include <sstream>
#include <string>
#include <string_view>

namespace xar::ck3_12002 {

// No main, native getter, query dispatch, packet construction or old fixture.
// The future execution owner supplies the context completed by the existing
// ExecutePlayerClergyAppointmentMailbox12002 path for its one fresh query.
std::string SerializeActualClergyMode0QueryForNewCase12004(
    const PlayerClergyAppointmentMailboxContext12002 &query,
    std::string_view request_id) {
  const auto require = [](bool condition, const char *reason) {
    if (!condition) throw std::runtime_error(reason);
  };
  require(query.completed && query.envelope.frame_stable && query.failure.empty(),
          "03e existing completed paused query required");
  require(query.bindings12004.has_value(), "03e exact actual4 query required");
  require(query.observation.available, "03e actual available clergy observation required");
  require(query.mode0_source_capture.borrowed_frame == nullptr,
          "03e borrowed frame survived the existing callback");
  require(query.mode0_source_capture.packet.has_value(),
          "03e actual collector packet required; do not fabricate a replacement");

  const auto &packet = *query.mode0_source_capture.packet;
  const auto &observation = query.observation;
  const auto &frame = packet.source_read_frame;
  require(packet.input_scope_confirmed &&
              packet.capture_epoch == observation.capture_epoch &&
              packet.date_raw == observation.date_raw &&
              packet.owner_character_id == observation.owner_character_id &&
              packet.candidate_character_id == observation.candidate_character_id &&
              packet.active_task_id == observation.active_task_id &&
              packet.incumbent_character_id == observation.incumbent_character_id,
          "03e source packet changed the actual observation tuple");
  require(frame.native_revision == query.envelope.expected_snapshot_revision &&
              frame.query_sequence == query.envelope.ticket.sequence &&
              frame.proof_epoch == packet.capture_epoch && frame.date_raw == packet.date_raw,
          "03e source packet metadata belongs to another existing query");
  require(!frame.frame_identity && !frame.snapshot_identity && !frame.ready,
          "03e current published source has no original snapshot identity");
  require(!packet.generic_trigger.source_value_ready && !packet.generic_trigger.raw_al,
          "03e missing actual identity cannot admit a dynamic generic result");

  // This is the original complete command_result serializer. All aggregate
  // predicates/availability and any sibling observations come from query.
  const auto wire = SerializePlayerClergyAppointmentResult12002(query, request_id);
  require(!wire.empty(), "03e existing production serializer returned no wire");
  return wire;
}

std::string SerializeActualClergyQueryFrameReceiptForNewCase12004(
    const PlayerClergyAppointmentMailboxContext12002 &query) {
  if (!query.completed || !query.envelope.frame_stable || !query.failure.empty() ||
      !query.mode0_source_capture.packet || query.mode0_source_capture.borrowed_frame)
    throw std::runtime_error("03e frame receipt requires the completed same source query");
  const auto &frame = query.envelope.expected_snapshot;
  std::ostringstream out;
  out << std::boolalpha
      << "{\"schema\":\"xar.clergy-source-query-frame-receipt/v1\","
      << "\"capture_scope\":\"owned_software_existing_query_context\","
      << "\"Game_query_observed\":false,\"snapshot_identity\":null,\"query_frame\":{"
      << "\"public_revision\":" << query.request.expected_public_revision
      << ",\"native_revision\":" << query.envelope.expected_snapshot_revision
      << ",\"capture_epoch\":" << query.envelope.execution_stamp.pump_epoch
      << ",\"date_raw\":" << frame.date_raw
      << ",\"owner_character_id\":" << frame.played_character_id
      << ",\"candidate_character_id\":" << query.request.candidate_character_id
      << ",\"paused\":" << frame.paused << ",\"map_ready\":" << frame.map_ready
      << ",\"played_character_alive\":" << frame.played_character_alive << "}}";
  return out.str();
}

} // namespace xar::ck3_12002
