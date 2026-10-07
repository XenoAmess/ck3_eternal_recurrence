#include "xar_bridge/ordinary_interaction_mailbox_v1.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"

#include <windows.h>
#include <array>
#include <cstring>
#include <sstream>

namespace xar::ck3_12003 {
namespace {
struct CodePin { std::uintptr_t rva; std::array<std::uint8_t, 32> bytes; };
// Exact .3 prefixes come from the frozen installed image and existing reviewed
// spans. Vtable entries are ASLR-adjusted pointers and are verified on the
// constructed command, never compared to unrelocated disk pointer bytes.
#include "ordinary_interaction_code_pins_v1.inc"
#include "ordinary_interaction_code_pins_12004_v1.inc"

bool PinMatches(std::uintptr_t image_base, const CodePin &pin) noexcept {
  if (image_base == 0) return false;
#if defined(_MSC_VER)
  __try {
#endif
    return std::memcmp(reinterpret_cast<const void *>(image_base + pin.rva),
                       pin.bytes.data(), pin.bytes.size()) == 0;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

void Quote(std::ostream &out, std::string_view value) {
  out << '"';
  for (const char c : value) {
    if (c == '"' || c == '\\') out << '\\';
    out << c;
  }
  out << '"';
}
void Bool(std::ostream &out, bool value) { out << (value ? "true" : "false"); }
template <typename T> void Optional(std::ostream &out, const std::optional<T> &v) {
  if (v) out << +*v;
  else out << "null";
}
void Optional(std::ostream &out, const std::optional<bool> &v) {
  if (v) Bool(out, *v);
  else out << "null";
}
void Reason(std::ostream &out, const char *value, bool absent) {
  if (absent) out << "null";
  else Quote(out, value != nullptr && value[0] != '\0' ? value : "unavailable");
}
bool Actual4(const OrdinaryInteractionMailboxContextV1 &q) noexcept {
  return q.envelope.game != nullptr && game::IsCk3_12004Descriptor(q.envelope.game->descriptor());
}
std::string_view BuildVersion(const OrdinaryInteractionMailboxContextV1 &q) noexcept {
  return Actual4(q) ? "1.20.0.4" : "1.20.0.3";
}
void Metadata(std::ostream &out, const OrdinaryInteractionMailboxContextV1 &q) {
  out << ",\"exact_build\":"; Quote(out, BuildVersion(q));
  out << ",\"executable_sha256\":";
  Quote(out, Actual4(q) ? ck3_12004::kExecutableSha256 : ordinary_interaction::kExecutableSha256);
  out << ",\"snapshot_revision\":" << q.request.expected_revision <<
      ",\"date_raw\":" << q.envelope.expected_snapshot.date_raw <<
      ",\"game_pid\":" << q.request.expected_game_pid <<
      ",\"connection_generation\":" << q.request.expected_connection_generation <<
      ",\"player_character_id\":" << q.request.expected_player_character_id <<
      ",\"recipient_id\":" << q.request.recipient_id << ",\"interaction_key\":";
  Quote(out, q.request.interaction_key);
}
void Proof(std::ostream &out, const OrdinaryInteractionMailboxContextV1 &q,
           const ordinary_interaction::Observation &o, bool frame_verified) {
  out << ",\"source_code_pins_verified\":"; Bool(out, q.proof.source_code_pins_verified);
  out << ",\"actor_binding_verified\":"; Bool(out, o.actor_binding_verified);
  out << ",\"recipient_binding_verified\":"; Bool(out, o.recipient_binding_verified);
  out << ",\"owner_thread_verified\":"; Bool(out, q.proof.owner_thread_verified);
  out << ",\"tls_verified\":"; Bool(out, q.proof.tls_verified);
  out << ",\"frame_verified\":"; Bool(out, frame_verified);
  out << ",\"owner_thread_id\":" << q.proof.owner_thread_id <<
      ",\"owner_pump_epoch\":" << q.proof.owner_pump_epoch;
}
bool Available(const OrdinaryInteractionMailboxContextV1 &q,
               const ordinary_interaction::Observation &o) noexcept {
  return o.native_context_available && q.proof.source_code_pins_verified &&
      o.actor_alive.has_value() && o.recipient_alive.has_value() &&
      o.definition_stable_hash.has_value() && o.declared_option_count.has_value() &&
      o.selected_option_count.has_value() && o.special_payload_present.has_value() &&
      o.shown.has_value() && o.can_send.has_value() && o.costs_raw.has_value() &&
      o.auto_accept.has_value() && o.recipient_score_raw.has_value() &&
      o.intermediary_score_raw.has_value() && o.outer_answer_status.has_value() &&
      *o.outer_answer_status <= 2 && *o.selected_option_count <= *o.declared_option_count &&
      (!o.ordinary_context_supported ||
       (*o.declared_option_count == 0 && !*o.special_payload_present)) &&
      o.actor_binding_verified && o.recipient_binding_verified &&
      q.proof.owner_thread_verified && q.proof.tls_verified &&
      q.proof.frame_verified && q.proof.owner_thread_id != 0 &&
      q.proof.owner_pump_epoch != 0;
}
bool VerifyDispatchFrame(void *opaque) noexcept {
  game::Snapshot observed{};
  return ck3_12002::CaptureQuerySnapshot(opaque, observed);
}
void QueryPayload(std::ostream &out, const OrdinaryInteractionMailboxContextV1 &q,
                  const ordinary_interaction::Observation &o) {
  const bool available = Available(q, o);
  out << "{\"schema\":\"ck3-character-interaction-ordinary-context-v1\",\"status\":";
  Quote(out, available ? "available" : "unavailable");
  out << ",\"source\":\"native_current_ordinary_interaction_context_" << BuildVersion(q) << "\",\"read_only\":true";
  Metadata(out, q);
  out << ",\"actor_alive\":"; Optional(out, available ? o.actor_alive : std::optional<bool>{});
  out << ",\"recipient_alive\":"; Optional(out, available ? o.recipient_alive : std::optional<bool>{});
  out << ",\"definition_stable_hash\":"; Optional(out, available ? o.definition_stable_hash : std::optional<std::uint32_t>{});
  out << ",\"effective_roles\":{";
  constexpr std::array<std::string_view, 6> names{
      "actor_id", "recipient_id", "secondary_actor_id", "secondary_recipient_id",
      "intermediary_id", "sixth_role_id"};
  for (std::size_t i = 0; i < names.size(); ++i) {
    if (i != 0) out << ',';
    Quote(out, names[i]); out << ':';
    Optional(out, available ? o.effective_roles[i] : std::optional<std::uint32_t>{});
  }
  out << "},\"declared_option_count\":"; Optional(out, available ? o.declared_option_count : std::optional<std::uint32_t>{});
  out << ",\"selected_option_count\":"; Optional(out, available ? o.selected_option_count : std::optional<std::uint32_t>{});
  out << ",\"special_payload_present\":"; Optional(out, available ? o.special_payload_present : std::optional<bool>{});
  out << ",\"shown\":"; Optional(out, available ? o.shown : std::optional<bool>{});
  out << ",\"can_send\":"; Optional(out, available ? o.can_send : std::optional<bool>{});
  out << ",\"costs_raw\":";
  if (available && o.costs_raw) {
    out << '[';
    for (std::size_t i = 0; i < o.costs_raw->size(); ++i) {
      if (i != 0) out << ',';
      out << (*o.costs_raw)[i];
    }
    out << ']';
  } else out << "null";
  out << ",\"cost_scale\":100000,\"cost_order\":[\"gold\",\"prestige\",\"piety\",\"renown\",\"influence\",\"herd\",\"treasury\",\"treasury_or_gold\",\"merit\",\"barter_goods\"]";
  out << ",\"auto_accept\":"; Optional(out, available ? o.auto_accept : std::optional<bool>{});
  out << ",\"recipient_score_raw\":"; Optional(out, available ? o.recipient_score_raw : std::optional<std::int64_t>{});
  out << ",\"intermediary_score_raw\":"; Optional(out, available ? o.intermediary_score_raw : std::optional<std::int64_t>{});
  out << ",\"outer_answer_status\":"; Optional(out, available ? o.outer_answer_status : std::optional<std::uint8_t>{});
  out << ",\"native_context_available\":"; Bool(out, available);
  out << ",\"ordinary_context_supported\":"; Bool(out, available && o.ordinary_context_supported);
  out << ",\"active_event_present\":"; Bool(out, q.envelope.expected_snapshot.has_active_event);
  out << ",\"incoming_interaction_present\":"; Bool(out, q.envelope.expected_snapshot.has_pending_character_interaction);
  Proof(out, q, o, q.proof.frame_verified);
  out << ",\"ready_to_initiate\":";
  Bool(out, available && OrdinaryInteractionReadyV1(o, q.proof, q.envelope.expected_snapshot));
  out << ",\"unavailable_reason\":"; Reason(out, o.unavailable_reason, available);
  out << ",\"unsupported_reason\":"; Reason(out, o.unsupported_reason, available && o.ordinary_context_supported);
  out << ",\"business_postcondition_verified\":false}";
}
std::string_view QueueName(ordinary_interaction::QueueResult result) noexcept {
  using R = ordinary_interaction::QueueResult;
  switch (result) {
    case R::not_attempted: return "not_attempted";
    case R::unavailable: return "unavailable";
    case R::rejected: return "rejected";
    case R::submitted: return "submitted";
  }
  return "unavailable";
}
} // namespace

bool OrdinaryInteractionCodePinsMatchV1(std::uintptr_t image_base) noexcept {
  return OrdinaryInteractionCodePinsMatchV1(image_base, ordinary_interaction::kExecutableSha256);
}

bool OrdinaryInteractionCodePinsMatchV1(std::uintptr_t image_base,
                                      std::string_view executable_sha256) noexcept {
  if (image_base == 0) return false;
  const auto *pins = executable_sha256 == ordinary_interaction::kExecutableSha256 ? &kOrdinaryInteractionCodePinsV1 :
      executable_sha256 == ck3_12004::kExecutableSha256 ? &kOrdinaryInteractionCodePins12004V1 : nullptr;
  if (pins == nullptr) return false;
  for (const auto &pin : *pins)
    if (!PinMatches(image_base, pin)) return false;
  return true;
}

bool OrdinaryInteractionControlFrameMatchesV1(
    const game::Snapshot &before, const game::Snapshot &after) noexcept {
  return before.paused && before.map_ready && before.has_played_character &&
      before.played_character_alive && before.played_character_id > 0 &&
      after.paused && after.map_ready && after.has_played_character &&
      after.played_character_alive && after.date_raw == before.date_raw &&
      after.speed == before.speed && after.player_id == before.player_id &&
      after.played_character_id == before.played_character_id &&
      after.has_one_life_settlement == before.has_one_life_settlement;
}

bool OrdinaryInteractionReadyV1(
    const ordinary_interaction::Observation &o,
    const OrdinaryInteractionMailboxProofV1 &p,
    const game::Snapshot &frame) noexcept {
  return o.native_context_available && o.ordinary_context_supported &&
      o.actor_binding_verified && o.recipient_binding_verified &&
      o.actor_alive.value_or(false) && o.recipient_alive.value_or(false) &&
      o.shown.value_or(false) && o.can_send.value_or(false) &&
      p.source_code_pins_verified && p.owner_thread_verified && p.tls_verified &&
      p.frame_verified && p.owner_thread_id != 0 && p.owner_pump_epoch != 0 &&
      frame.paused && frame.map_ready && frame.has_played_character &&
      frame.played_character_alive && frame.played_character_id > 0 &&
      !frame.has_active_event && !frame.has_pending_character_interaction;
}

bool ExecuteOrdinaryInteractionMailboxV1(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr ||
      !ck3_12002::EnterQueryMailbox(
          *envelope, stamp, &ExecuteOrdinaryInteractionMailboxV1)) return false;
  auto &q = *static_cast<OrdinaryInteractionMailboxContextV1 *>(envelope->typed_context);
  if (envelope != &q.envelope || q.completed ||
      (!game::IsCk3_12003Descriptor(envelope->game->descriptor()) &&
       !game::IsCk3_12004Descriptor(envelope->game->descriptor())) ||
      !OrdinaryInteractionRequestValidV1(q.request) ||
      q.request.expected_revision != envelope->expected_snapshot_revision ||
      q.request.expected_game_pid != GetCurrentProcessId() ||
      q.request.expected_player_character_id != envelope->expected_snapshot.played_character_id ||
      stamp.thread_id != GetCurrentThreadId() || stamp.pump_epoch == 0 ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_main_thread_marker != 1 || stamp.tls_context == 0) return false;
  q.proof.owner_thread_verified = true;
  q.proof.tls_verified = true;
  q.proof.owner_thread_id = stamp.thread_id;
  q.proof.owner_pump_epoch = stamp.pump_epoch;
  q.proof.source_code_pins_verified = OrdinaryInteractionCodePinsMatchV1(
      q.image_base, envelope->game->descriptor().executable_sha256);
  q.proof.frame_verified = true;
  if (!q.proof.source_code_pins_verified) {
    q.observation.unavailable_reason = "current_interaction_code_pins_changed";
    q.observation.unsupported_reason = "native_context_unavailable";
    q.initiation.reason = "current_interaction_code_pins_changed";
  } else {
    auto bindings = Actual4(q) ? ordinary_interaction::BindOrdinaryInteractionImage12004(
        q.image_base, envelope->game->descriptor().executable_sha256) :
        ordinary_interaction::BindOrdinaryInteractionImage12003(
            q.image_base, envelope->game->descriptor().executable_sha256);
    bindings.dispatch_frame_context = envelope;
    bindings.verify_dispatch_frame = &VerifyDispatchFrame;
    if (!q.initiate) {
      (void)ordinary_interaction::ReadOrdinaryInteractionContextV1(
          bindings, q.request, q.observation);
    } else if (envelope->expected_snapshot.has_active_event ||
               envelope->expected_snapshot.has_pending_character_interaction) {
      (void)ordinary_interaction::ReadOrdinaryInteractionContextV1(
          bindings, q.request, q.initiation.preflight_context);
      q.initiation.reason = "current_event_or_incoming_interaction_blocks_initiation";
    } else {
      // EnterQueryMailbox captured the exact published frame. Capture again
      // immediately before the ordinary leaf's freshly rebuilt final context.
      game::Snapshot immediate{};
      if (!ck3_12002::CaptureQuerySnapshot(envelope, immediate)) return false;
      ordinary_interaction::InitiateOrdinaryInteractionV1(
          bindings, q.request, q.initiation);
    }
  }
  q.completed = true;
  if (!q.initiate) {
    q.proof.frame_verified = ck3_12002::FinishQueryMailbox(*envelope);
  } else {
    game::Snapshot after{};
    envelope->frame_stable = ck3_12002::IsQueryOwningThread(envelope) &&
        game::ReadSnapshot(*envelope->game, after) &&
        OrdinaryInteractionControlFrameMatchesV1(envelope->expected_snapshot, after);
    q.proof.frame_verified = envelope->frame_stable;
  }
  return envelope->frame_stable;
}

std::string SerializeOrdinaryInteractionV1(
    const OrdinaryInteractionMailboxContextV1 &q, std::uint64_t sequence) {
  const auto &o = q.initiate ? q.initiation.preflight_context : q.observation;
  const bool available = Available(q, o);
  const bool dispatched = q.initiate && q.initiation.dispatch_invoked;
  const auto status = q.initiate ? (dispatched ? "pending" : "not_dispatched") :
      (available ? "available" : "unavailable");
  std::ostringstream out;
  out << "{\"step\":";
  Quote(out, q.initiate ? kOrdinaryInteractionInitiateV1Step : kOrdinaryInteractionQueryV1Step);
  out << ",\"accepted\":true,\"status\":"; Quote(out, status);
  out << ",\"read_only\":"; Bool(out, !q.initiate);
  out << ",\"query_sequence\":" << sequence <<
      ",\"snapshot_revision\":" << q.request.expected_revision <<
      ",\"date_raw\":" << q.envelope.expected_snapshot.date_raw <<
      ",\"game_pid\":" << q.request.expected_game_pid <<
      ",\"connection_generation\":" << q.request.expected_connection_generation;
  if (!q.initiate) {
    out << ",\"character_interaction_ordinary_context\":";
    QueryPayload(out, q, o);
  } else {
    out << ",\"character_interaction_ordinary_initiation\":{\"schema\":\"ck3-character-interaction-ordinary-initiation-v1\",\"status\":";
    Quote(out, status);
    out << ",\"source\":\"native_current_ordinary_interaction_command_" << BuildVersion(q) << "\",\"read_only\":false";
    Metadata(out, q);
    Proof(out, q, o, q.proof.frame_verified);
    out << ",\"native_call_completed\":"; Bool(out, q.initiation.native_call_completed);
    out << ",\"dispatch_invoked\":"; Bool(out, dispatched);
    out << ",\"native_queue_result\":"; Quote(out, QueueName(q.initiation.native_queue_result));
    out << ",\"queue_submitted\":";
    Bool(out, q.initiation.native_queue_result == ordinary_interaction::QueueResult::submitted);
    out << ",\"verification_pending\":"; Bool(out, dispatched);
    out << ",\"postcondition_verified\":false,\"business_postcondition_verified\":false,\"reason\":";
    Reason(out, q.initiation.reason,
           q.initiation.native_queue_result == ordinary_interaction::QueueResult::submitted);
    out << ",\"preflight_context\":"; QueryPayload(out, q, o);
    out << '}';
  }
  out << ",\"backend_id\":\"native-headless\"}";
  return out.str();
}

} // namespace xar::ck3_12003
