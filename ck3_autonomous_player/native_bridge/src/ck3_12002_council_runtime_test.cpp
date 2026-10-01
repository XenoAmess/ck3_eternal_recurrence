#include "xar_bridge/ck3_12002_council_runtime.hpp"
#include "ck3_12002_council_fixture.hpp"

#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>

namespace {
using namespace xar;
using namespace xar::ck3_12002;
using SourceFixture = test::CouncilCandidatesFixture12002;
using Operation = bridge::CouncilApplicationMainOperationV1;
using Completion = bridge::CouncilApplicationMainCompletionV1;
using Failure = game::CouncilAssignCouncillorFailureV1;

void Require(bool condition, const char *message) {
  if (!condition) { std::cerr << message << '\n'; std::exit(1); }
}

struct SourceChainFixture;
SourceChainFixture *active = nullptr;
struct SourceChainFixture {
  SourceFixture source{};
  test::Blob<0x20> pending_manager{};
  std::int32_t played_id = SourceFixture::kOwner;
  bool councillor = false, guest = false, pending = false, fireable = true;
  bool drift_during_gate = false;
  std::uint32_t native_gate_calls = 0, confirm_calls = 0, helper_calls = 0;
  std::int32_t submitted_candidate = -1, submitted_task = -1;
  CouncilMailboxState12002 state{};
  CouncilMailboxContext12002 context{};
  ck3_11906::MainThreadExecutionStampV1 stamp{};
  std::uint64_t sequence = 0;

  explicit SourceChainFixture(bool vacant = false) {
    active = this;
    if (vacant) source.tasks[0].Put(0x40, std::int32_t{-1});
    pending_manager.Put(0x8, played_id);
    context.candidates_environment = source.environment;
    context.candidates_access = source.access;
    context.query_request = source.request;
    auto &e = context.gates_environment;
    e.exact_build_admitted = true;
    e.admitted_executable_sha256 = kExecutableSha256;
    e.offline_fixture = true;
    e.played_character_id_slot = &played_id;
    e.read_context = this; e.read_memory = Read;
    e.is_councillor = IsCouncillor; e.is_guest = IsGuest;
    e.pending_setup = PendingSetup; e.has_pending = HasPending;
    e.can_confirm = CanConfirm;
    auto &submit = context.submit;
    submit.environment.exact_build_admitted = true;
    submit.environment.admitted_executable_sha256 = kExecutableSha256;
    submit.environment.native_command_abi_certified = true;
    submit.environment.offline_fixture = true;
    submit.fixture_context = this; submit.fixture_helper = Submit;
    context.shared_state = &state;
    context.private_action_enabled = true;
    stamp.thread_id = 7; stamp.paused = true; stamp.game_state = 1;
  }

  static bool Read(void *raw, const void *address, void *output,
                   std::size_t size) noexcept {
    auto &f = *static_cast<SourceChainFixture *>(raw);
    if (SourceFixture::Span(&f.played_id, sizeof(f.played_id), address, size) ||
        SourceFixture::Span(f.pending_manager.Data(), 0x20, address, size)) {
      std::memcpy(output, address, size); return true;
    }
    return SourceFixture::Memory(&f.source, address, output, size);
  }
  static bool IsCouncillor(void *candidate) {
    Require(SourceFixture::Span(active->source.characters.data(),
        sizeof(active->source.characters), candidate, 0x20), "gate candidate receiver");
    ++active->native_gate_calls; return active->councillor;
  }
  static bool IsGuest(void *) {
    ++active->native_gate_calls;
    if (active->drift_during_gate) {
      ++active->source.frame.native_revision;
      active->drift_during_gate = false;
    }
    return active->guest;
  }
  static void PendingSetup(void *window) {
    auto *bytes = static_cast<std::byte *>(window);
    for (std::size_t i = 0; i < kCouncilGatesPendingWindowSize12002; ++i)
      Require(bytes[i] == std::byte{}, "native pending window initialization");
    void *manager = active->pending_manager.Data();
    std::memcpy(bytes + 0x5D8, &manager, sizeof(manager));
  }
  static bool HasPending(void *manager, std::int32_t candidate) {
    Require(manager == active->pending_manager.Data(), "pending manager receiver");
    Require(candidate == SourceFixture::kCandidate ||
        candidate == SourceFixture::kCandidate + 1, "pending full candidate ID");
    ++active->native_gate_calls; return active->pending;
  }
  static bool CanConfirm(void *confirmation) {
    auto *bytes = static_cast<std::byte *>(confirmation);
    std::int32_t incumbent = -1, candidate = -1;
    std::memcpy(&incumbent, bytes + 0x130, sizeof(incumbent));
    std::memcpy(&candidate, bytes + 0x134, sizeof(candidate));
    const auto expected_incumbent = active->context.query_request.position_key ==
        kCouncilCandidatesChancellorPosition12002 ? SourceFixture::kChancellorIncumbent :
        active->context.query_request.position_key == kCouncilCandidatesSpymasterPosition12002 ?
        SourceFixture::kSpymasterIncumbent :
        SourceFixture::kIncumbent;
    Require(incumbent == expected_incumbent, "native incumbent payload");
    Require((candidate == SourceFixture::kCandidate ||
        candidate == SourceFixture::kCandidate + 1) &&
        candidate != SourceFixture::kTask, "native candidate payload must differ from task");
    ++active->confirm_calls; return active->fireable;
  }
  static void Submit(void *raw, std::int32_t candidate,
                     std::int32_t task) noexcept {
    auto &f = *static_cast<SourceChainFixture *>(raw);
    ++f.helper_calls; f.submitted_candidate = candidate; f.submitted_task = task;
    // Native helper invocation is not an independently observed state change.
  }
  void Execute(Operation op) {
    active = this;
    context.operation = op; context.ticket.sequence = ++sequence;
    Require(ExecuteCouncilMailbox12002(&context, stamp), "production mailbox executor");
    Require(context.active_stamp == nullptr, "stamp escaped production transaction");
  }
  void QueryAndPrepare() {
    Execute(Operation::query_candidates);
    Require(context.wire.completion == Completion::query_available &&
        context.wire.query_result.readiness.ready &&
        context.wire.query_result.candidate_count == 2 &&
        context.wire.query_result.candidates[0].character_id == SourceFixture::kCandidate &&
        context.wire.query_result.candidates[0].native_collection_ordinal == 1,
        "actual native candidate reader/projector");
    Require(source.producer_calls == 1 && source.release_calls == 1 &&
        source.allocator_shape_valid && source.producer_inputs_valid,
        "native producer/vector lifetime source chain");
    Require(ck3_11906::PrepareCouncilAssignCouncillorActionRequestV1(
        context.wire.query_result, SourceFixture::kCandidate,
        "assign:council12002", context.action_request), "actual request preparation");
  }
  void AdvanceFrame() {
    source.frame.snapshot_id.fill('\0');
    constexpr std::string_view next = "native:council12002:next";
    std::copy(next.begin(), next.end(), source.frame.snapshot_id.begin());
    ++source.frame.public_revision; ++source.frame.native_revision;
    ++source.frame.date_raw;
  }
};

void WriteWire(const std::filesystem::path &directory, std::string_view filename,
               const SourceChainFixture &f) {
  const auto wire = SerializeCouncilMailbox12002(f.context, "wire:council12002");
  Require(!wire.empty() && wire.front() == '{' && wire.back() == '}', "actual native wire serializer");
  if (directory.empty()) return;
  std::ofstream output(directory / filename, std::ios::binary);
  output << wire << '\n';
  Require(static_cast<bool>(output), "write actual native wire artifact");
}

} // namespace

int main(int argc, char **argv) {
  const std::filesystem::path directory = argc > 1 ? argv[1] : "";
  if (!directory.empty()) std::filesystem::create_directories(directory);
  int checks = 0;
  for (int index = 0; index < 4; ++index) {
    auto owned = std::make_unique<SourceChainFixture>();
    auto &f = *owned;
    f.QueryAndPrepare();
    const Failure failures[] = {Failure::candidate_already_councillor,
        Failure::candidate_is_guest, Failure::pending_character_interaction,
        Failure::incumbent_cannot_be_replaced};
    const std::string_view files[] = {"reject-councillor.json", "reject-guest.json",
        "reject-pending.json", "reject-fireability.json"};
    if (index == 0) f.councillor = true;
    if (index == 1) f.guest = true;
    if (index == 2) f.pending = true;
    if (index == 3) f.fireable = false;
    f.Execute(Operation::submit_assignment);
    Require(f.context.wire.completion == Completion::action_rejected &&
        f.context.wire.action_ack.failure == failures[index] &&
        f.context.wire.action_ack.status == game::CouncilAssignCouncillorAckStatusV1::rejected_before_submit &&
        !f.context.wire.action_ack.native_helper_invoked &&
        f.helper_calls == 0 && f.context.submit.invocation_count == 0 && !f.state.has_pending_ack,
        "isolated typed final-gate rejection submitted a helper");
    WriteWire(directory, files[index], f); ++checks;
  }
  for (bool vacant : {false, true}) {
    auto owned = std::make_unique<SourceChainFixture>(vacant);
    auto &f = *owned;
    f.QueryAndPrepare(); ++checks;
    WriteWire(directory, vacant ? "vacant-query.json" : "query.json", f);
    f.Execute(Operation::query_final_gates);
    Require(f.context.wire.completion == Completion::query_available &&
        f.context.wire.final_gate_row_count == 2 && f.helper_calls == 0 &&
        f.context.wire.final_gate_rows[0].available &&
        !f.context.wire.final_gate_rows[0].already_councillor &&
        !f.context.wire.final_gate_rows[0].guest &&
        !f.context.wire.final_gate_rows[0].pending_interaction &&
        f.context.wire.final_gate_rows[0].fireability_evaluated == !vacant &&
        f.context.wire.final_gate_rows[0].incumbent_can_be_fired == !vacant &&
        f.confirm_calls == (vacant ? 0U : 2U), "actual native gate query"); ++checks;
    WriteWire(directory, vacant ? "vacant-gates.json" : "gates.json", f);
    f.Execute(Operation::submit_assignment);
    const auto &ack = f.context.wire.action_ack;
    Require(f.context.wire.completion == Completion::submitted_verification_pending &&
        ack.status == game::CouncilAssignCouncillorAckStatusV1::native_helper_invoked_verification_pending &&
        ack.native_helper_invoked && ack.verification_pending &&
        !ack.queue_acceptance_observed &&
        ack.route == (vacant ? game::CouncilAssignCouncillorRouteV1::assign_vacant :
                              game::CouncilAssignCouncillorRouteV1::replace_incumbent) &&
        f.helper_calls == 1 && f.context.submit.invocation_count == 1 &&
        f.submitted_candidate == SourceFixture::kCandidate &&
        f.submitted_task == SourceFixture::kTask && f.state.has_pending_ack,
        "real new submit adapter ACK semantics"); ++checks;
    WriteWire(directory, vacant ? "vacant-ack.json" : "ack.json", f);
    f.Execute(Operation::verify_assignment_receipt);
    Require(f.context.wire.completion == Completion::receipt_rejected &&
        f.context.wire.action_receipt.reason == "no_new_paused_frame" &&
        !f.context.wire.action_receipt.postcondition_verified && f.state.has_pending_ack,
        "ACK or same frame falsely satisfied independent receipt"); ++checks;
    WriteWire(directory, vacant ? "vacant-same-frame-receipt.json" : "same-frame-receipt.json", f);
    f.AdvanceFrame();
    f.Execute(Operation::verify_assignment_receipt);
    Require(f.context.wire.completion == Completion::receipt_rejected &&
        f.context.wire.action_receipt.reason == "candidate_not_observed_as_incumbent" &&
        f.state.has_pending_ack, "new frame alone falsely satisfied material receipt"); ++checks;
    f.source.tasks[0].Put(0x40, SourceFixture::kCandidate);
    f.Execute(Operation::verify_assignment_receipt);
    Require(f.context.wire.completion == Completion::receipt_applied &&
        f.context.wire.action_receipt.status == game::CouncilAssignCouncillorReceiptStatusV1::applied &&
        f.context.wire.action_receipt.postcondition_verified &&
        f.context.wire.action_receipt.incumbent_character_id == SourceFixture::kCandidate &&
        f.context.wire.action_receipt.incumbent_identity_round_trip &&
        !f.state.has_pending_ack && f.helper_calls == 1,
        "independent actual task/character receipt failed"); ++checks;
    WriteWire(directory, vacant ? "vacant-receipt.json" : "receipt.json", f);
  }
  {
    auto owned = std::make_unique<SourceChainFixture>();
    auto &f = *owned;
    f.QueryAndPrepare(); f.drift_during_gate = true;
    f.Execute(Operation::submit_assignment);
    Require(f.context.wire.action_ack.failure == Failure::state_changed_before_submit &&
        f.helper_calls == 0, "native gate frame drift not rechecked"); ++checks;
    WriteWire(directory, "reject-drift.json", f);
  }
  {
    auto owned = std::make_unique<SourceChainFixture>();
    auto &f = *owned;
    f.QueryAndPrepare();
    f.source.count = 1; f.source.rows[0] =
        reinterpret_cast<std::uintptr_t>(f.source.characters[16].Data());
    f.Execute(Operation::submit_assignment);
    Require(f.context.wire.action_ack.failure == Failure::candidate_not_in_exact_collection &&
        f.helper_calls == 0 && f.native_gate_calls == 0,
        "final candidate collection was not refreshed"); ++checks;
    WriteWire(directory, "reject-absent.json", f);
  }
  for (bool vacant : {false, true}) {
    auto owned = std::make_unique<SourceChainFixture>();
    auto &f = *owned;
    f.source.EnableChancellor();
    if (vacant) f.source.tasks[1].Put(0x40, std::int32_t{-1});
    f.context.query_request = f.source.request;
    f.Execute(Operation::query_final_gates);
    const auto &result = f.context.wire.query_result;
    Require(f.context.wire.completion == Completion::query_available &&
        std::string_view(result.position_key.data()) == SourceFixture::kChancellorPosition &&
        std::string_view(result.candidates[0].main_skill.key.data()) == "diplomacy" &&
        result.candidates[0].main_skill.value == 28 &&
        result.incumbent_character_id == (vacant ? -1 : SourceFixture::kChancellorIncumbent) &&
        f.source.producer_inputs_valid && f.context.wire.final_gate_row_count == 2 &&
        f.native_gate_calls == 6 && f.confirm_calls == (vacant ? 0U : 2U) &&
        f.context.wire.final_gate_rows[0].available &&
        f.context.wire.final_gate_rows[0].fireability_evaluated == !vacant &&
        f.helper_calls == 0, "Chancellor readonly native gates bind the requested task"); ++checks;
    WriteWire(directory, vacant ? "chancellor-vacant-gates.json" : "chancellor-gates.json", f);
    game::CouncilAssignCouncillorActionRequestV1 request{};
    Require(!ck3_11906::PrepareCouncilAssignCouncillorActionRequestV1(result,
        SourceFixture::kCandidate, "chancellor-not-an-action", request) &&
        f.helper_calls == 0 && !f.state.has_pending_ack,
        "readonly Chancellor projection does not enable Steward assignment"); ++checks;
  }
  {
    auto owned = std::make_unique<SourceChainFixture>();
    auto &f = *owned;
    f.source.EnableChancellor(); f.context.query_request = f.source.request;
    f.drift_during_gate = true;
    f.Execute(Operation::query_final_gates);
    Require(f.context.wire.completion == Completion::query_unavailable &&
        f.context.wire.failure_reason == "final_gate_frame_changed" &&
        f.context.wire.final_gate_row_count == 0 && f.helper_calls == 0,
        "Chancellor gate query independently recaptures the requested role frame"); ++checks;
  }
  for (bool vacant : {false, true}) {
    auto owned = std::make_unique<SourceChainFixture>();
    auto &f = *owned;
    f.source.EnableSpymaster();
    if (vacant) f.source.tasks[2].Put(0x40, std::int32_t{-1});
    f.context.query_request = f.source.request;
    f.Execute(Operation::query_final_gates);
    const auto &result = f.context.wire.query_result;
    Require(f.context.wire.completion == Completion::query_available && result.readiness.ready &&
        std::string_view(result.position_key.data()) == SourceFixture::kSpymasterPosition &&
        std::string_view(result.candidates[0].main_skill.key.data()) == "intrigue" &&
        result.candidates[0].main_skill.value == 23 && result.candidates[1].main_skill.value == 13 &&
        result.incumbent_character_id == (vacant ? -1 : SourceFixture::kSpymasterIncumbent) &&
        (vacant || result.incumbent_main_skill.value == 17) &&
        f.source.producer_inputs_valid && f.context.wire.final_gate_row_count == 2 &&
        f.native_gate_calls == 6 && f.confirm_calls == (vacant ? 0U : 2U) &&
        f.context.wire.final_gate_rows[0].available &&
        f.context.wire.final_gate_rows[0].fireability_evaluated == !vacant &&
        f.helper_calls == 0, "Spymaster native final gates use its own incumbent and intrigue"); ++checks;
    WriteWire(directory, vacant ? "spymaster-vacant-gates.json" : "spymaster-gates.json", f);
    game::CouncilAssignCouncillorActionRequestV1 request{};
    Require(!ck3_11906::PrepareCouncilAssignCouncillorActionRequestV1(result,
        SourceFixture::kCandidate, "spymaster-not-an-action", request) &&
        f.helper_calls == 0 && !f.state.has_pending_ack,
        "Spymaster readonly observation does not enable typed Steward assignment"); ++checks;
  }
  {
    auto owned = std::make_unique<SourceChainFixture>();
    auto &f = *owned;
    f.source.EnableSpymaster(); f.context.query_request = f.source.request;
    f.drift_during_gate = true;
    f.Execute(Operation::query_final_gates);
    Require(f.context.wire.completion == Completion::query_unavailable &&
        f.context.wire.failure_reason == "final_gate_frame_changed" &&
        f.context.wire.final_gate_row_count == 0 && f.helper_calls == 0,
        "Spymaster gate query recaptures its requested role after native final predicates"); ++checks;
  }
  std::cout << "{\"status\":\"GREEN\",\"checks\":" << checks
      << ",\"isolated_gate_rejections\":4,\"routes\":2,\"source_chain\":\"candidate_reader-native_gates-semantic_action-new_submit_adapter-independent_receipt-actual_serializer\",\"live_verified\":false}\n";
}
