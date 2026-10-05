// Offline fixture-owned data only; no CK3 instructions/process/pipe execute.
#include "xar_bridge/ordinary_interaction_mailbox_v1.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "current_actor_stress_adjustment_fixture_adapter.hpp"

#include <windows.h>
#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
#include <vector>

namespace {
using namespace xar::ck3_12003;
using namespace xar::ck3_11906;
unsigned checks = 0;
struct CodePin { std::uintptr_t rva; std::array<std::uint8_t, 32> bytes; };
#include "../src/ordinary_interaction_code_pins_v1.inc"

OrdinaryInteractionMailboxContextV1 Sample() {
  OrdinaryInteractionMailboxContextV1 q{};
  q.request = {"ordinary_fixture_interaction", 0xFE000002U, 7, 0x01000001, 991, 2};
  auto &frame = q.envelope.expected_snapshot;
  frame.paused = true; frame.map_ready = true; frame.has_played_character = true;
  frame.played_character_alive = true; frame.played_character_id = 0x01000001;
  frame.player_id = 19; frame.date_raw = 53146848; frame.speed = 1;
  q.envelope.expected_snapshot_revision = 7;
  q.proof = {true, true, true, true, GetCurrentThreadId(), 19};
  auto &o = q.observation;
  o.native_context_available = true; o.ordinary_context_supported = true;
  o.actor_binding_verified = true; o.recipient_binding_verified = true;
  o.actor_alive = true; o.recipient_alive = true;
  o.definition_stable_hash = 0xF1234567U;
  o.effective_roles[0] = 0x01000001U; o.effective_roles[1] = 0xFE000002U;
  o.declared_option_count = 0; o.selected_option_count = 0; o.special_payload_present = false;
  o.shown = true; o.can_send = true;
  o.costs_raw = std::array<std::int64_t, 10>{100000, -9007199254740993LL, 0, 0, 0, 0, 0, 0, 0, 9007199254740993LL};
  o.auto_accept = true; o.recipient_score_raw = -5000; o.intermediary_score_raw = 0;
  o.outer_answer_status = std::uint8_t{1}; o.unavailable_reason = nullptr; o.unsupported_reason = nullptr;
  q.initiation.preflight_context = o;
  return q;
}
void SerializerAndReady() {
  auto q = Sample();
  assert(OrdinaryInteractionReadyV1(q.observation, q.proof, q.envelope.expected_snapshot)); ++checks;
  const auto available = SerializeOrdinaryInteractionV1(q, 41);
  assert(available.find("\"recipient_id\":4261412866") != std::string::npos);
  assert(available.find("9007199254740993") != std::string::npos);
  assert(available.find("-9007199254740993") != std::string::npos);
  assert(available.find("\"ready_to_initiate\":true") != std::string::npos); checks += 4;
  std::cout << "FIXTURE_QUERY_AVAILABLE " << available << '\n';
  for (int v = 0; v < 13; ++v) {
    q = Sample();
    switch (v) {
      case 0: q.observation.shown = false; break;
      case 1: q.observation.can_send = false; break;
      case 2: q.observation.actor_alive = false; break;
      case 3: q.observation.recipient_alive = false; break;
      case 4: q.observation.ordinary_context_supported = false; q.observation.special_payload_present = true; q.observation.unsupported_reason = "special_payload_unsupported"; break;
      case 5: q.proof.source_code_pins_verified = false; break;
      case 6: q.proof.owner_thread_verified = false; break;
      case 7: q.proof.tls_verified = false; break;
      case 8: q.proof.frame_verified = false; break;
      case 9: q.envelope.expected_snapshot.has_active_event = true; break;
      case 10: q.envelope.expected_snapshot.has_pending_character_interaction = true; break;
      case 11: q.proof.owner_thread_id = 0; break;
      case 12: q.proof.owner_pump_epoch = 0; break;
    }
    assert(!OrdinaryInteractionReadyV1(q.observation, q.proof, q.envelope.expected_snapshot)); ++checks;
    assert(SerializeOrdinaryInteractionV1(q, 42).find("\"ready_to_initiate\":false") != std::string::npos); ++checks;
  }
  q = Sample(); q.proof.source_code_pins_verified = false;
  q.observation.unavailable_reason = "source_code_pins_unavailable";
  const auto unavailable = SerializeOrdinaryInteractionV1(q, 43);
  for (auto key : {"actor_alive", "recipient_alive", "definition_stable_hash", "declared_option_count", "selected_option_count", "special_payload_present", "shown", "can_send", "costs_raw", "auto_accept", "recipient_score_raw", "intermediary_score_raw", "outer_answer_status"}) {
    assert(unavailable.find(std::string("\"") + key + "\":null") != std::string::npos); ++checks;
  }
  std::cout << "FIXTURE_QUERY_UNAVAILABLE " << unavailable << '\n';
  // Defensive serialization does not publish available with missing raw terms.
  q = Sample(); q.observation.costs_raw.reset();
  assert(SerializeOrdinaryInteractionV1(q, 44).find("\"status\":\"unavailable\"") != std::string::npos); ++checks;
  for (auto result : {ordinary_interaction::QueueResult::submitted,
                     ordinary_interaction::QueueResult::rejected,
                     ordinary_interaction::QueueResult::unavailable}) {
    q = Sample(); q.initiate = true;
    q.initiation.dispatch_invoked = true; q.initiation.native_call_completed = true;
    q.initiation.native_queue_result = result;
    q.initiation.reason = result == ordinary_interaction::QueueResult::submitted ? nullptr : "native_queue_unavailable";
    auto wire = SerializeOrdinaryInteractionV1(q, 45);
    assert(wire.find("\"status\":\"pending\"") != std::string::npos);
    assert(wire.find("\"verification_pending\":true") != std::string::npos);
    assert(wire.find("\"postcondition_verified\":false") != std::string::npos);
    assert(wire.find("\"business_postcondition_verified\":true") == std::string::npos); checks += 4;
    std::cout << "FIXTURE_INITIATION_PENDING " << wire << '\n';
  }
  q = Sample(); q.initiate = true;
  q.initiation.reason = "native_can_send_false";
  q.initiation.preflight_context.can_send = false;
  auto wire = SerializeOrdinaryInteractionV1(q, 46);
  assert(wire.find("\"status\":\"not_dispatched\"") != std::string::npos);
  assert(wire.find("\"verification_pending\":false") != std::string::npos); checks += 2;
  std::cout << "FIXTURE_INITIATION_NOT_DISPATCHED " << wire << '\n';
}
void ControlFrames() {
  auto q = Sample(); auto before = q.envelope.expected_snapshot; auto after = before;
  after.has_active_event = true; after.active_event_instance_id = 0x01000099;
  after.has_pending_character_interaction = true; after.pending_character_interaction_id = 55;
  after.played_character_stress_points = 4; after.played_character_gold.raw = 9000;
  after.played_character_primary_spouse_id = 991; after.active_wars.resize(1);
  assert(after != before && OrdinaryInteractionControlFrameMatchesV1(before, after)); ++checks;
  for (int v = 0; v < 9; ++v) {
    after = before;
    switch (v) {
      case 0: ++after.date_raw; break;
      case 1: ++after.speed; break;
      case 2: after.paused = false; break;
      case 3: after.map_ready = false; break;
      case 4: ++after.player_id; break;
      case 5: after.has_played_character = false; break;
      case 6: ++after.played_character_id; break;
      case 7: after.played_character_alive = false; break;
      case 8: after.has_one_life_settlement = true; break;
    }
    assert(!OrdinaryInteractionControlFrameMatchesV1(before, after)); ++checks;
  }
}
void Pins() {
  std::vector<std::uint8_t> image(0x3F7E240 + 4096);
  for (const auto &pin : kOrdinaryInteractionCodePinsV1)
    std::memcpy(image.data() + pin.rva, pin.bytes.data(), pin.bytes.size());
  const auto base = reinterpret_cast<std::uintptr_t>(image.data());
  assert(OrdinaryInteractionCodePinsMatchV1(base)); ++checks;
  for (const auto &pin : kOrdinaryInteractionCodePinsV1) {
    image[pin.rva + pin.bytes.size() - 1] ^= 1;
    assert(!OrdinaryInteractionCodePinsMatchV1(base)); ++checks;
    image[pin.rva + pin.bytes.size() - 1] ^= 1;
  }
  assert(!OrdinaryInteractionCodePinsMatchV1(0)); ++checks;
  assert(!OrdinaryInteractionCodePinsMatchV1(1)); ++checks;
}
void Mailbox() {
  FixtureAdapter adapter{};
  MainThreadQueryMailboxV1 mailbox{};
  for (int variant = 0; variant < 18; ++variant) {
    auto q = Sample(); q.proof = {}; q.observation = {}; q.initiation = {};
    q.request.expected_game_pid = GetCurrentProcessId(); q.image_base = 0;
    q.envelope.game = &adapter; q.envelope.mailbox = &mailbox; q.envelope.typed_context = &q;
    q.envelope.ticket.sequence = 77;
    adapter.frame = q.envelope.expected_snapshot; adapter.admitted = true;
    mailbox.state.store(MainThreadQueryMailboxStateV1::executing);
    mailbox.published_sequence.store(77); mailbox.owner_thread_id.store(GetCurrentThreadId());
    mailbox.failure_flags.store(0); mailbox.stop_requested.store(false);
    mailbox.executor = &ExecuteOrdinaryInteractionMailboxV1; mailbox.executor_context = &q.envelope;
    MainThreadExecutionStampV1 stamp{};
    stamp.thread_id = GetCurrentThreadId(); stamp.pump_epoch = 19; stamp.paused = true;
    stamp.date_raw = adapter.frame.date_raw; stamp.tls_initialized = 1;
    stamp.tls_main_thread_marker = 1; stamp.tls_context = 1;
    stamp.tls_initialized_flag_address = 1; stamp.jomini_state = 1; stamp.game_state = 1;
    switch (variant) {
      case 1: stamp.tls_initialized = 0; break;
      case 2: stamp.tls_main_thread_marker = 0; break;
      case 3: stamp.tls_context = 0; break;
      case 4: stamp.tls_initialized_flag_address = 0; break;
      case 5: stamp.pump_epoch = 0; break;
      case 6: ++stamp.thread_id; break;
      case 7: stamp.paused = false; break;
      case 8: stamp.jomini_state = 0; break;
      case 9: stamp.game_state = 0; break;
      case 10: ++stamp.date_raw; break;
      case 11: ++q.request.expected_revision; break;
      case 12: ++q.request.expected_game_pid; break;
      case 13: adapter.admitted = false; break;
      case 14: mailbox.published_sequence.store(78); break;
      case 15: mailbox.failure_flags.store(1); break;
      case 16: mailbox.stop_requested.store(true); break;
      case 17: ++adapter.frame.played_character_stress_points; break;
    }
    const bool result = ExecuteOrdinaryInteractionMailboxV1(&q.envelope, stamp);
    if (variant == 0) {
      assert(result && q.completed && q.envelope.frame_stable &&
             !q.proof.source_code_pins_verified && q.proof.owner_thread_verified &&
             q.proof.tls_verified && !q.observation.native_context_available);
    } else assert(!result && !q.completed);
    ++checks;
  }
}
} // namespace
int main() {
  SerializerAndReady(); ControlFrames(); Pins(); Mailbox();
  std::cout << "ORDINARY_MAILBOX_SERIALIZER_CHECKS " << checks << " PASS; offline fixtures only\n";
}
