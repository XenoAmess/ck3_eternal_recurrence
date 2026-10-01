#include "xar_bridge/ck3_12002_council_gates.hpp"

#include <array>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <limits>

using namespace xar;
using namespace xar::ck3_12002;
namespace {

void Require(bool condition, const char *message) {
  if (!condition) { std::cerr << message << '\n'; std::exit(1); }
}

struct Fixture {
  std::int32_t played_id = 0x01000011;
  std::int32_t candidate_id = 0x02000021;
  std::int32_t incumbent_id = 0x03000031;
  std::int32_t task_id = 0x04000041;
  std::array<std::byte, 0x20> candidate{}, manager{};
  bool councillor = false, guest = false, pending = false, fireable = true;
  bool missing_manager = false, change_player = false;
  int predicate_calls = 0, pending_calls = 0, confirm_calls = 0;
} *fixture = nullptr;

bool IsCouncillor(void *candidate) {
  Require(candidate == fixture->candidate.data(), "wrong councillor receiver");
  ++fixture->predicate_calls; return fixture->councillor;
}
bool IsGuest(void *candidate) {
  Require(candidate == fixture->candidate.data(), "wrong guest receiver");
  ++fixture->predicate_calls; return fixture->guest;
}
void PendingSetup(void *window) {
  for (std::size_t i = 0; i < kCouncilGatesPendingWindowSize12002; ++i)
    Require(static_cast<std::byte *>(window)[i] == std::byte{},
            "native setup footprint must be zero initialized");
  void *manager = fixture->missing_manager ? nullptr : fixture->manager.data();
  std::memcpy(static_cast<std::byte *>(window) + kCouncilGatesPendingManagerOffset12002,
              &manager, sizeof(manager));
}
bool HasPending(void *manager, std::int32_t candidate_id) {
  Require(manager == fixture->manager.data(), "wrong pending receiver");
  Require(candidate_id == fixture->candidate_id, "pending must use full candidate ID");
  ++fixture->pending_calls;
  if (fixture->change_player) ++fixture->played_id;
  return fixture->pending;
}
bool CanConfirm(void *confirmation) {
  std::int32_t incumbent = -1, candidate = -1;
  auto *bytes = static_cast<std::byte *>(confirmation);
  std::memcpy(&incumbent, bytes + 0x130, sizeof(incumbent));
  std::memcpy(&candidate, bytes + 0x134, sizeof(candidate));
  Require(incumbent == fixture->incumbent_id, "confirmation incumbent payload");
  Require(candidate == fixture->candidate_id && candidate != fixture->task_id,
          "confirmation second field must be candidate CharacterID, never TaskID");
  for (std::size_t i = 0; i < kCouncilGatesConfirmationSize12002; ++i)
    if (i < 0x130 || i >= 0x138)
      Require(bytes[i] == std::byte{}, "confirmation unused bytes/view must remain zero");
  ++fixture->confirm_calls; return fixture->fireable;
}

CouncilGatesEnvironment12002 Environment(Fixture &f) {
  fixture = &f;
  std::memcpy(f.candidate.data() + 0x18, &f.candidate_id, sizeof(f.candidate_id));
  std::memcpy(f.manager.data() + 0x8, &f.played_id, sizeof(f.played_id));
  CouncilGatesEnvironment12002 e{};
  e.exact_build_admitted = true;
  e.admitted_executable_sha256 = kCouncilGatesExecutableSha25612002;
  e.offline_fixture = true;
  e.current_thread_id = e.application_main_thread_id = 7;
  e.played_character_id_slot = &f.played_id;
  e.is_councillor = IsCouncillor; e.is_guest = IsGuest;
  e.pending_setup = PendingSetup; e.has_pending = HasPending;
  e.can_confirm = CanConfirm;
  return e;
}
game::CouncilAssignCouncillorFrameV1 Frame(const Fixture &f) {
  game::CouncilAssignCouncillorFrameV1 frame{};
  frame.available = frame.paused = frame.map_ready = true;
  frame.owner_character_id = f.played_id;
  frame.owner_identity_round_trip = true;
  frame.active_task_id = f.task_id;
  frame.active_task_identity_round_trip = true;
  frame.position_key = "councillor_steward";
  frame.has_incumbent = true;
  frame.incumbent_character_id = f.incumbent_id;
  frame.incumbent_identity_round_trip = true;
  return frame;
}
game::CouncilAssignCouncillorFinalLegalityV1 Legality(
    const game::CouncilAssignCouncillorFrameV1 &frame, const Fixture &f) {
  game::CouncilAssignCouncillorFinalLegalityV1 out{};
  out.owner_character_id = frame.owner_character_id;
  out.active_task_id = frame.active_task_id;
  out.position_key = frame.position_key;
  out.candidate_character_id = f.candidate_id;
  out.candidate_match_count = 1;
  out.candidate_identity_round_trip = true;
  return out;
}

} // namespace

int main() {
  int passed = 0;
  // Independent positive/negative native branch values must all be observable.
  for (unsigned mask = 0; mask != 16; ++mask) {
    Fixture f{}; auto e = Environment(f); auto frame = Frame(f);
    auto out = Legality(frame, f);
    f.councillor = (mask & 1) != 0; f.guest = (mask & 2) != 0;
    f.pending = (mask & 4) != 0; f.fireable = (mask & 8) != 0;
    Require(EvaluateCouncilGates12002(e, frame, f.candidate_id, f.candidate.data(), out),
            "gate matrix read failed");
    Require(out.available && out.candidate_already_councillor == f.councillor &&
                out.candidate_is_guest == f.guest &&
                out.pending_character_interaction == f.pending &&
                out.incumbent_fireability_evaluated &&
                out.incumbent_can_be_fired == f.fireable,
            "native gate values not preserved");
    Require(out.candidate_match_count == 1 && out.candidate_identity_round_trip &&
                out.owner_character_id == frame.owner_character_id &&
                out.active_task_id == f.task_id && out.position_key == frame.position_key &&
                out.candidate_character_id == f.candidate_id,
            "candidate provider identity/match fields overwritten");
    Require(f.predicate_calls == 2 && f.pending_calls == 1 && f.confirm_calls == 1,
            "unexpected native receiver invocation");
    ++passed;
  }
  {
    Fixture f{}; auto e = Environment(f); auto frame = Frame(f);
    frame.has_incumbent = false; frame.incumbent_character_id = -1;
    frame.incumbent_identity_round_trip = false; auto out = Legality(frame, f);
    Require(EvaluateCouncilGates12002(e, frame, f.candidate_id, f.candidate.data(), out) &&
                out.available && !out.incumbent_fireability_evaluated &&
                !out.incumbent_can_be_fired && f.confirm_calls == 0,
            "vacant seat must bypass CanConfirm"); ++passed;
  }
  for (int fault = 0; fault != 7; ++fault) {
    Fixture f{}; auto e = Environment(f); auto frame = Frame(f); auto out = Legality(frame, f);
    switch (fault) {
      case 0: f.missing_manager = true; break;
      case 1: { std::int32_t wrong = f.played_id + 1;
                std::memcpy(f.manager.data() + 8, &wrong, sizeof(wrong)); break; }
      case 2: e.admitted_executable_sha256 = "old-build"; break;
      case 3: e.current_thread_id = 8; break;
      case 4: out.candidate_match_count = 0; break;
      case 5: { std::int32_t wrong = f.candidate_id + 0x01000000;
                std::memcpy(f.candidate.data() + 0x18, &wrong, sizeof(wrong)); break; }
      case 6: f.change_player = true; break;
    }
    out.available = true;
    Require(!EvaluateCouncilGates12002(e, frame, f.candidate_id, f.candidate.data(), out) &&
                !out.available && !out.incumbent_fireability_evaluated,
            "unavailable frame/native read must not become legal false");
    ++passed;
  }
  const auto bound = BindCouncilGates12002(0x140000000,
                                          kCouncilGatesExecutableSha25612002);
  Require(bound.exact_build_admitted && !bound.offline_fixture &&
              reinterpret_cast<std::uintptr_t>(bound.can_confirm) == 0x1411604A0 &&
              reinterpret_cast<std::uintptr_t>(bound.played_character_id_slot) == 0x1454DBC00,
          "exact native binding incorrect");
  Require(!BindCouncilGates12002(0x140000000, "old-build").exact_build_admitted &&
              !BindCouncilGates12002(0, kCouncilGatesExecutableSha25612002).exact_build_admitted &&
              !BindCouncilGates12002((std::numeric_limits<std::uintptr_t>::max)(),
                                    kCouncilGatesExecutableSha25612002).exact_build_admitted,
          "invalid build binding admitted"); ++passed;
  std::cout << "{\"status\":\"GREEN\",\"checks\":" << passed
            << ",\"gate_matrix\":16,\"production_function\":true,\"live_verified\":false}\n";
}
