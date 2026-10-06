#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/religion_rite_governance12002_clergy_mailbox.hpp"
#include "ck3_12002_council_fixture.hpp"

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <thread>
#include <utility>
#include <vector>

namespace c = xar::ck3_12002;
namespace r = c::religion::clergy;
namespace t = xar::ck3_12003::religion::clergy_candidate_terms;
namespace game = xar::game;
namespace api = xar::ck3_11906;

namespace {
constexpr std::int32_t kOwner = 29829;
constexpr std::int32_t kIncumbent = 56513;
constexpr std::int32_t kTask = 7162;
constexpr std::int32_t kCandidate = 0x01000010;
constexpr std::int32_t kOtherCandidate = 0x02000011;
constexpr std::int32_t kDate = 53222304;
constexpr std::uint64_t kPublicRevision = 2;
constexpr std::uint64_t kNativeRevision = 9;
constexpr std::uint64_t kCaptureEpoch = 991;
constexpr std::array<const char *, 6> kWireFiles{
    "occupied-confirm-false.json", "occupied-confirm-true.json",
    "guest-pending-true.json", "incumbent-not-in-collection.json",
    "vacant-confirm-null.json", "native-terms-unavailable.json"};
constexpr std::array<const char *, 6> kRequestIds{
    "g2-read-00000000000000000000000000004301",
    "g2-read-00000000000000000000000000004302",
    "g2-read-00000000000000000000000000004303",
    "g2-read-00000000000000000000000000004304",
    "g2-read-00000000000000000000000000004305",
    "g2-read-00000000000000000000000000004306"};
unsigned checks = 0;
unsigned unused_adapter_calls = 0;
void Check(bool condition, const char *message) {
  ++checks;
  if (!condition) throw std::runtime_error(message);
}

// Core and council memory are one fixture-owned world. The owning mailbox's
// production capture callback reads this actual CoreBindings source; no frozen
// leaf DTO, archived wire, repaired row or hand-built result is supplied.
struct Fixture {
  c::test::CouncilCandidatesFixture12002 source{};
  c::test::Blob<0xA8> state{};
  c::test::Blob<0x28> jomini{};
  c::test::Blob<0x1F8> players{};
  c::test::Blob<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  c::test::Blob<0xE0> entry{};
  std::array<void *, 1> entries{entry.Data()};
  c::test::Blob<0x20> pending_manager{};
  void *state_pointer = state.Data();
  void *jomini_pointer = jomini.Data();
  std::int32_t played_id = kOwner;
  std::int32_t requested_id = kCandidate;
  bool councillor = false, guest = false, pending = false, confirm = false;
  bool missing_pending_manager = false;
  bool bad_arguments = false;
  unsigned base_predicate_calls = 0;
  unsigned character_predicate_calls = 0;
  unsigned pending_setup_calls = 0, pending_calls = 0, confirm_calls = 0;
  c::PlayerClergyAppointmentMailboxContext12002 *owning_query = nullptr;

  Fixture() {
    source.EnableChaplainLearning();
    source.count = 2;
    source.characters[15].Put(0x18, kCandidate);
    source.characters[16].Put(0x18, kOtherCandidate);
    source.characters[15].Put(0xD8, std::int32_t{3});
    source.characters[15].Put(0xE0, std::int32_t{22});
    source.characters[15].Put(0xE4, std::int32_t{4});
    source.characters[15].Put(0xE8, std::int32_t{29});
    source.characters[16].Put(0xE8, std::int32_t{0});
    source.chaplain_character_slots[16].object = source.characters[15].Data();
    source.chaplain_character_slots[17].object = source.characters[16].Data();
    source.characters[0].Put(r::kCharacterRiteOffset, std::uint32_t{0});
    source.characters[1].Put(r::kCharacterRiteOffset, std::uint32_t{0});
    source.characters[15].Put(r::kCharacterRiteOffset, std::uint32_t{0});
    source.characters[16].Put(r::kCharacterRiteOffset, std::uint32_t{0});
    state.Put(8, kDate);
    state.Put(0x70, std::int32_t{2}); // Actual core decoder yields public speed 3.
    state.Put(0xA0, data.data());
    jomini.Put(0x18, players.Data());
    jomini.bytes[0x20] = std::byte{1};
    players.Put(0x1F0, std::int32_t{7});
    player.Put(0x70, std::int32_t{7});
    PutData(c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    PutData(c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    entry.Put(0xD8, std::int32_t{7});
    entry.Put(0xB0, kOwner);
    pending_manager.Put(8, kOwner);
  }

  template <typename T> void PutData(std::size_t offset, T value) noexcept {
    std::memcpy(data.data() + offset, &value, sizeof(value));
  }
  void *RequestedCharacter() noexcept {
    return requested_id == kIncumbent ? source.characters[1].Data()
                                     : source.characters[15].Data();
  }
  bool OwnsNativeCallback(void *context) const noexcept {
    return owning_query && context == owning_query &&
        c::IsPlayerClergyCandidateTermsMainThread12002(context);
  }
};
Fixture *active = nullptr;

// Only engine function pointers and owned memory are synthetic. All reader,
// composition/profile, main-thread mailbox, serializer and renderer code is
// production source. Engine callbacks record argument errors without throwing
// through the production noexcept/SEH native boundary.
void *LocalPlayer(void *) { return active->player.Data(); }
void *CourtOwner(void *candidate) {
  if (candidate != active->RequestedCharacter()) active->bad_arguments = true;
  return active->source.characters[0].Data();
}
bool ValidPosition(void *position, std::int32_t owner) {
  ++active->base_predicate_calls;
  if (position != active->source.position.Data() || owner != kOwner)
    active->bad_arguments = true;
  return true;
}
bool ValidCharacter(void *position, std::int32_t candidate) {
  ++active->base_predicate_calls;
  if (position != active->source.position.Data() || candidate != active->requested_id)
    active->bad_arguments = true;
  return true;
}
bool CanReassign(void *task, void *tooltip) {
  ++active->base_predicate_calls;
  if (task != active->source.tasks[0].Data() || tooltip != nullptr)
    active->bad_arguments = true;
  return false;
}
bool CanFire(void *owner, void *incumbent, void *task,
             std::uint32_t mode, void *tooltip) {
  ++active->base_predicate_calls;
  if (owner != active->source.characters[0].Data() ||
      incumbent != active->source.characters[1].Data() ||
      task != active->source.tasks[0].Data() || mode != 0U || tooltip != nullptr)
    active->bad_arguments = true;
  return false; // Independent base CanFire remains false even if confirm=true.
}
bool Memory(void *, const void *address, void *out, std::size_t size) noexcept {
  auto &f = *active;
  using Original = c::test::CouncilCandidatesFixture12002;
  const bool extra = Original::Span(&f.state_pointer, sizeof(f.state_pointer), address, size) ||
      Original::Span(&f.jomini_pointer, sizeof(f.jomini_pointer), address, size) ||
      Original::Span(f.state.Data(), sizeof(f.state), address, size) ||
      Original::Span(f.jomini.Data(), sizeof(f.jomini), address, size) ||
      Original::Span(f.players.Data(), sizeof(f.players), address, size) ||
      Original::Span(f.player.Data(), sizeof(f.player), address, size) ||
      Original::Span(f.data.data(), f.data.size(), address, size) ||
      Original::Span(f.entry.Data(), sizeof(f.entry), address, size) ||
      Original::Span(f.entries.data(), sizeof(f.entries), address, size) ||
      Original::Span(&f.played_id, sizeof(f.played_id), address, size) ||
      Original::Span(f.pending_manager.Data(), sizeof(f.pending_manager), address, size);
  if (extra && out) { std::memcpy(out, address, size); return true; }
  return Original::Memory(&f.source, address, out, size);
}
bool Initialize(void *context, const c::CouncilCandidatesEnvironmentV1 &environment,
                void *allocator, std::size_t size,
                c::CouncilCandidatesNativeVectorV1 &vector) noexcept {
  if (!active->OwnsNativeCallback(context)) active->bad_arguments = true;
  return c::test::CouncilCandidatesFixture12002::Initialize(
      &active->source, environment, allocator, size, vector);
}
bool Produce(void *context, const c::CouncilCandidatesEnvironmentV1 &environment,
             const void *owner, const void *task, bool gui,
             c::CouncilCandidatesNativeVectorV1 &vector) noexcept {
  if (!active->OwnsNativeCallback(context)) active->bad_arguments = true;
  return c::test::CouncilCandidatesFixture12002::Produce(
      &active->source, environment, owner, task, gui, vector);
}
bool Release(void *context, const c::CouncilCandidatesEnvironmentV1 &environment,
             c::CouncilCandidatesNativeVectorV1 &vector) noexcept {
  if (!active->OwnsNativeCallback(context)) active->bad_arguments = true;
  return c::test::CouncilCandidatesFixture12002::Release(
      &active->source, environment, vector);
}
bool Councillor(void *candidate) {
  ++active->character_predicate_calls;
  if (candidate != active->source.characters[15].Data()) active->bad_arguments = true;
  return active->councillor;
}
bool Guest(void *candidate) {
  ++active->character_predicate_calls;
  if (candidate != active->source.characters[15].Data()) active->bad_arguments = true;
  return active->guest;
}
void PendingSetup(void *storage) {
  ++active->pending_setup_calls;
  const auto *bytes = static_cast<const std::byte *>(storage);
  if (!std::all_of(bytes, bytes + c::kCouncilGatesPendingWindowSize12002,
      [](std::byte value) { return value == std::byte{}; })) active->bad_arguments = true;
  void *manager = active->missing_pending_manager ? nullptr : active->pending_manager.Data();
  std::memcpy(static_cast<std::byte *>(storage) + c::kCouncilGatesPendingManagerOffset12002,
      &manager, sizeof(manager));
}
bool Pending(void *manager, std::int32_t candidate) {
  ++active->pending_calls;
  if (manager != active->pending_manager.Data() || candidate != kCandidate)
    active->bad_arguments = true;
  return active->pending;
}
bool Confirm(void *storage) {
  ++active->confirm_calls;
  std::int32_t incumbent = -1, candidate = -1;
  const auto *bytes = static_cast<const std::byte *>(storage);
  std::memcpy(&incumbent, bytes + c::kCouncilGatesConfirmationIncumbentOffset12002,
      sizeof(incumbent));
  std::memcpy(&candidate, bytes + c::kCouncilGatesConfirmationCandidateOffset12002,
      sizeof(candidate));
  if (incumbent != kIncumbent || candidate != kCandidate || candidate == kTask)
    active->bad_arguments = true;
  return active->confirm;
}

r::Bindings ClergyBindings(Fixture &f) {
  r::Bindings b{};
  b.enabled = true; b.offline_fixture = true;
  b.executable_sha256 = c::kExecutableSha256;
  b.core = {true, &f.state_pointer, &f.jomini_pointer,
      &f.source.character_storage_pointer, &LocalPlayer};
  b.task_storage_slot = &f.source.task_storage_pointer;
  b.valid_position = &ValidPosition; b.valid_character = &ValidCharacter;
  b.can_reassign = &CanReassign; b.can_fire = &CanFire; b.court_owner = &CourtOwner;
  b.read_memory = &Memory;
  return b;
}
t::Environment TermsEnvironment(Fixture &f) {
  t::Environment e{};
  e.enabled = true; e.executable_sha256 = xar::ck3_12003::kExecutableSha256;
  e.candidates = f.source.environment;
  e.access = f.source.access;
  // Execute installs actual owning callbacks/context. The native-only wrappers
  // below deliberately ignore the old source's context and use fixture active.
  e.access.read_memory = &Memory;
  e.access.initialize_vector = &Initialize;
  e.access.invoke_producer = &Produce;
  e.access.release_allocation = &Release;
  e.gates.exact_build_admitted = true;
  e.gates.admitted_executable_sha256 = c::kCouncilGatesExecutableSha25612002;
  e.gates.offline_fixture = true;
  e.gates.current_thread_id = e.gates.application_main_thread_id = GetCurrentThreadId();
  e.gates.played_character_id_slot = &f.played_id;
  e.gates.read_memory = &Memory;
  e.gates.is_councillor = &Councillor; e.gates.is_guest = &Guest;
  e.gates.pending_setup = &PendingSetup; e.gates.has_pending = &Pending;
  e.gates.can_confirm = &Confirm;
  return e;
}

class FrameAdapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  const DWORD owner = GetCurrentThreadId();
  mutable unsigned reads = 0;
  game::AdapterDescriptor identity{xar::ck3_12003::kAdapterId,
      xar::ck3_12003::kGameVersion, xar::ck3_12003::kExecutableSha256,
      "clergy-candidate-terms-native-whole-fixture", {}};
  const game::AdapterDescriptor &descriptor() const noexcept override { return identity; }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    if (GetCurrentThreadId() != owner) return false;
    ++reads; out = frame; return true;
  }
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override { return {}; }
  game::PreviewMoveArmyResult preview_move_army(std::int32_t, std::int32_t) const noexcept override { return {}; }
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &) const noexcept override { return false; }
#define ABSENT(Result, Name, Params) game::Result Name Params const noexcept override { return game::Result::unavailable; }
  ABSENT(PauseSubmitResult, submit_pause_map, (game::Snapshot *))
  ABSENT(ResumeSubmitResult, submit_resume_map, (game::Snapshot *))
  ABSENT(SelectEventOptionResult, submit_select_event_option, (std::int32_t))
  ABSENT(ReplyPendingInteractionResult, submit_reply_to_pending_interaction, (game::PendingInteractionReply))
  ABSENT(RaiseTroopsResult, submit_raise_troops_default, ())
  ABSENT(MoveArmyResult, submit_move_army, (std::int32_t, std::int32_t))
  ABSENT(DisbandArmyResult, submit_disband_army, (std::int32_t))
  ABSENT(SplitArmyHalfResult, submit_split_army_half, (std::int32_t))
  ABSENT(MergeArmiesResult, submit_merge_armies, (std::int32_t, std::int32_t))
  ABSENT(StartAssaultResult, submit_start_assault, (std::int32_t))
  ABSENT(StopAssaultResult, submit_stop_assault, (std::int32_t))
  ABSENT(ReadDeclarableWarsResult, read_declarable_wars_for_target, (std::int32_t, std::vector<game::DeclarableWarSnapshot> &))
  ABSENT(DeclareWarResult, submit_declare_war, (const game::DeclarableWarSnapshot &))
  ABSENT(ReadArrangeMarriageChoicesResult, read_arrange_marriage_choices, (std::vector<game::ArrangeMarriageChoice> &, game::ArrangeMarriageQueryDiagnostics &))
  ABSENT(ArrangeMarriageResult, submit_arrange_marriage, (const game::ArrangeMarriageChoice &))
  ABSENT(EnforceDemandsResult, submit_enforce_demands, (std::int32_t))
  ABSENT(SurrenderWarResult, submit_surrender_war, (std::int32_t))
  ABSENT(OfferWhitePeaceResult, submit_offer_white_peace, (std::int32_t))
  ABSENT(ReadArmyStrengthsResult, read_army_strengths, (std::vector<game::ArmyStrengthSnapshot> &))
  ABSENT(ReadCombatSimulationInputsResult, read_combat_simulation_inputs, (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &))
  ABSENT(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3, (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &))
  ABSENT(ReadWarTerminationOptionsResult, read_war_termination_options, (std::int32_t, game::WarTerminationOptionsSnapshot &))
  ABSENT(ReadWarTerminationTermsResult, read_war_termination_terms, (std::int32_t, game::WarTerminationTermsSnapshot &))
  ABSENT(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms, (std::int32_t, game::WarTerminationExitTermsSnapshot &))
#undef ABSENT
};

void *tls_context = nullptr;
void *__fastcall FixtureTls() noexcept { return tls_context; }
struct Pump {
  c::test::Blob<0x28> tls{};
  std::uint8_t initialized = 1;
  std::uintptr_t unused_rng = 0;
  Pump(Fixture &f, api::MainThreadQueryMailboxV1 &mailbox) {
    tls.bytes[0x20] = std::byte{1}; tls_context = tls.Data();
    mailbox.global_rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&unused_rng);
    mailbox.jomini_state_slot = reinterpret_cast<std::uintptr_t>(&f.jomini_pointer);
    mailbox.game_state_slot = reinterpret_cast<std::uintptr_t>(&f.state_pointer);
    mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter = &FixtureTls;
    mailbox.executor_submission_enabled = true;
    mailbox.permitted_executor_clergy12002 = &c::ExecutePlayerClergyAppointmentMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    mailbox.pump_epochs = kCaptureEpoch - 3;
    for (unsigned i = 0; i < 2; ++i)
      (void)api::ObserveMainThreadPumpAndDrainV1(
          mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    Check(mailbox.pump_epochs == kCaptureEpoch - 1,
        "two real synthetic owner warmups establish expected pump epoch");
  }
  ~Pump() { tls_context = nullptr; }
};

void CheckTerms(const Fixture &f, const t::Observation &out, std::size_t scenario) {
  Check(out.capture_epoch == kCaptureEpoch && out.public_revision == kPublicRevision &&
      out.native_revision == kNativeRevision && out.date_raw == kDate &&
      out.owner_character_id == kOwner && out.active_task_id == kTask &&
      out.candidate_character_id == f.requested_id,
      "actual owning capture binds separate public/native/epoch and full candidate");
  Check(out.candidate_collection_available && out.candidate_count == 2U &&
      f.source.producer_calls == 1 && f.source.release_calls == 1 &&
      f.source.allocator_shape_valid && f.source.producer_inputs_valid,
      "one actual production composition collection/release transaction");
  if (scenario == 3) {
    Check(out.available && out.failure == t::Failure::none &&
        out.incumbent_character_id == kIncumbent && out.candidate_match_count == 0U &&
        out.candidate_in_native_collection == false && !out.candidate_learning &&
        !out.native_collection_ordinal && !out.final_predicates_available &&
        !out.candidate_already_councillor && !out.candidate_is_guest &&
        !out.pending_character_interaction && !out.native_can_confirm_replacement &&
        f.character_predicate_calls == 0 && f.pending_setup_calls == 0 &&
        f.pending_calls == 0 && f.confirm_calls == 0,
        "incumbent omitted from collection retains available false membership and null route");
  } else if (scenario == 5) {
    Check(!out.available && out.failure == t::Failure::native_predicate_unavailable &&
        out.incumbent_character_id == kIncumbent && out.candidate_match_count == 1U &&
        out.candidate_in_native_collection == true && out.candidate_learning == 29 &&
        out.native_collection_ordinal == 1U && !out.final_predicates_available &&
        !out.candidate_already_councillor && !out.candidate_is_guest &&
        !out.pending_character_interaction && !out.native_can_confirm_replacement &&
        f.character_predicate_calls == 2 && f.pending_setup_calls == 1 &&
        f.pending_calls == 0 && f.confirm_calls == 0,
        "failed native pending setup preserves collection and null final predicates");
  } else {
    Check(out.available && out.failure == t::Failure::none &&
        out.candidate_match_count == 1U && out.candidate_in_native_collection == true &&
        out.candidate_learning == 29 && out.native_collection_ordinal == 1U &&
        out.final_predicates_available && out.candidate_already_councillor == f.councillor &&
        out.candidate_is_guest == f.guest && out.pending_character_interaction == f.pending &&
        f.character_predicate_calls == 2 && f.pending_setup_calls == 1 && f.pending_calls == 1,
        "production observation evaluator preserves independent true/false final terms");
    if (scenario == 4)
      Check(!out.incumbent_character_id && !out.native_can_confirm_replacement &&
          f.confirm_calls == 0, "vacancy emits null confirm without invoking occupied route");
    else
      Check(out.incumbent_character_id == kIncumbent &&
          out.native_can_confirm_replacement == f.confirm && f.confirm_calls == 1,
          "occupied candidate-specific confirmation retains native true/false");
  }
}

void Emit(const std::filesystem::path &directory, const char *name, const std::string &wire) {
  std::ofstream out(directory / name, std::ios::binary);
  Check(static_cast<bool>(out), "open first actual whole wire output");
  out << wire << '\n';
  Check(static_cast<bool>(out), "write actual production whole wire bytes");
}

void Query(Fixture &f, const std::filesystem::path &directory, std::size_t scenario) {
  active = &f;
  FrameAdapter adapter;
  adapter.frame.paused = adapter.frame.map_ready = true;
  adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
  adapter.frame.player_id = 7; adapter.frame.speed = 3;
  adapter.frame.played_character_id = kOwner; adapter.frame.date_raw = kDate;
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(f, mailbox);
  c::PlayerClergyAppointmentMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = kNativeRevision;
  const auto payload = "{\"candidate_character_id\":" + std::to_string(f.requested_id) +
      ",\"expected_snapshot_revision\":9,\"expected_public_revision\":2}";
  Check(c::ParsePlayerClergyAppointmentRequest12002(payload, query.request) &&
      query.request.candidate_character_id == f.requested_id &&
      query.request.expected_revision == kNativeRevision &&
      query.request.expected_public_revision == kPublicRevision,
      "actual existing request parser keeps explicit full candidate and both revisions");
  query.bindings = ClergyBindings(f);
  query.candidate_terms_environment = TermsEnvironment(f);
  f.owning_query = &query;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
  std::string wire, failure;
  std::thread worker([&] {
    result = c::RunPlayerClergyAppointmentMailbox12002(
        query, kRequestIds[scenario], wire, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (!drained && mailbox.state.load(std::memory_order_acquire) ==
        api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(
          mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Check(drained && result && failure.empty() && query.completed &&
      query.envelope.frame_stable && !wire.empty(),
      "actual worker request executes through existing owning mailbox and full serializer");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle &&
      mailbox.executed_requests == 1 && query.envelope.ticket.sequence != 0 &&
      query.envelope.execution_stamp.pump_epoch == kCaptureEpoch &&
      query.envelope.execution_stamp.thread_id == GetCurrentThreadId() && adapter.reads == 2,
      "actual named ticket drains once on owner and is reclaimed after stable frame");
  Check(query.bindings.application_main_thread_id == GetCurrentThreadId() &&
      query.candidate_terms_environment->access.context == &query &&
      query.candidate_terms_environment->access.capture_frame ==
          &c::CapturePlayerClergyCandidateTermsFrame12002 &&
      query.candidate_terms_environment->access.is_main_thread ==
          &c::IsPlayerClergyCandidateTermsMainThread12002 &&
      query.candidate_terms_snapshot_id == "native:9" &&
      query.candidate_terms_environment->gates.current_thread_id == GetCurrentThreadId() &&
      query.candidate_terms_environment->gates.application_main_thread_id == GetCurrentThreadId(),
      "production clergy executor installs actual same-source owning frame callbacks and stamp");
  const auto &base = query.observation;
  Check(base.available && base.failure == r::Failure::none && base.capture_epoch == kCaptureEpoch &&
      base.date_raw == kDate && base.owner_character_id == kOwner &&
      base.candidate_character_id == f.requested_id && base.active_task_id == kTask &&
      base.position_present && base.native_valid_position == true &&
      base.native_valid_character == true && base.native_can_reassign == false &&
      base.candidate_court_owner_id == kOwner && base.owner_rite_id == 0U &&
      base.candidate_rite_id == 0U && base.candidate_matches_owner_context == true &&
      base.candidate_is_incumbent == (scenario == 3),
      "actual base clergy observation remains available and independent of new terms");
  Check((scenario == 4 && !base.incumbent_character_id && !base.native_can_fire &&
          f.base_predicate_calls == 3) ||
      (scenario != 4 && base.incumbent_character_id == kIncumbent &&
          base.native_can_fire == false && f.base_predicate_calls == 4),
      "base standalone CanFire false/null is preserved independently from replacement confirm");
  Check(query.candidate_terms_observation.has_value(), "existing full query captures new sibling");
  CheckTerms(f, *query.candidate_terms_observation, scenario);
  Check(!f.bad_arguments, "all synthetic native callbacks receive actual owner/task/full candidate arguments");
  const auto terms_bytes = t::SerializeClergyCandidateTerms12003(*query.candidate_terms_observation);
  Check(wire.find("\"candidate_terms\":" + terms_bytes) != std::string::npos &&
      wire.find("\"snapshot_revision\":9") != std::string::npos &&
      wire.find("\"status\":\"observed\"") != std::string::npos &&
      wire.find("\"action_eligibility_complete\":false") != std::string::npos,
      "actual whole serializer includes exact actual reader sibling and unchanged observed base");
  wire = game::RenderCrozierBuildIdentity(std::move(wire), adapter.descriptor());
  Check(wire.find("\"game_version\":\"1.20.0.2\"") == std::string::npos &&
      wire.find(c::kExecutableSha256) == std::string::npos &&
      wire.find("ck3-1.20.0.3-native-player-clergy-appointment-v1") != std::string::npos &&
      wire.find(xar::ck3_12003::kExecutableSha256) != std::string::npos &&
      wire.find("\"candidate_terms\":" + terms_bytes) != std::string::npos,
      "actual Crozier renderer publishes exact .3 identities and preserves new sibling bytes");
  Emit(directory, kWireFiles[scenario], wire);
  f.owning_query = nullptr;
}

void CheckOriginalActionProfile() {
  Fixture f; active = &f;
  const auto environment = TermsEnvironment(f);
  game::CouncilAssignCouncillorFrameV1 frame{};
  frame.available = frame.paused = frame.map_ready = true;
  frame.owner_character_id = kOwner; frame.owner_identity_round_trip = true;
  frame.active_task_id = kTask; frame.active_task_identity_round_trip = true;
  frame.position_key = "councillor_court_chaplain";
  frame.has_incumbent = frame.incumbent_identity_round_trip = true;
  frame.incumbent_character_id = kIncumbent;
  game::CouncilAssignCouncillorFinalLegalityV1 out{};
  out.owner_character_id = kOwner; out.active_task_id = kTask;
  out.position_key = frame.position_key; out.candidate_character_id = kCandidate;
  out.candidate_match_count = 1; out.candidate_identity_round_trip = true;
  Check(!c::EvaluateCouncilGates12002(environment.gates, frame, kCandidate,
      f.source.characters[15].Data(), out) && !out.available &&
      f.character_predicate_calls == 0 && f.pending_setup_calls == 0 &&
      f.pending_calls == 0 && f.confirm_calls == 0 && !f.bad_arguments,
      "original action evaluator retains three-seat chaplain rejection with no native predicates");
}

void EmitReceipt(const std::filesystem::path &directory) {
  // A compiled receipt summarizes assertions above. It is never a substitute
  // for any of the six actual production command_result bytes.
  std::ofstream out(directory / "native-whole-receipt.json", std::ios::binary);
  Check(static_cast<bool>(out), "open compiled assertion receipt");
  out << "{\"schema\":\"xar.ck3.clergy-candidate-terms-native-whole-fixture/v1\","
      "\"status\":\"GREEN\",\"cases\":6,\"whole_wire_files\":[";
  for (std::size_t i = 0; i < kWireFiles.size(); ++i) {
    if (i) out << ',';
    out << '\"' << kWireFiles[i] << '\"';
  }
  out << "],\"frame\":{\"public_revision\":2,\"native_revision\":9,\"capture_epoch\":991,"
      "\"date_raw\":53222304,\"owner_character_id\":29829,\"active_task_id\":7162,"
      "\"paused\":true,\"map_ready\":true},\"exact_build\":{\"game_version\":\"1.20.0.3\","
      "\"executable_sha256\":\"" << xar::ck3_12003::kExecutableSha256 << "\"},"
      "\"provenance\":{\"native_memory\":\"fixture-synthetic\","
      "\"native_callbacks\":\"fixture-synthetic\",\"source_frame\":\"fixture-synthetic\","
      "\"public_revision\":\"fixture-synthetic\",\"capture_epoch\":\"fixture-synthetic\","
      "\"whole_wires\":\"compiled-production-serializer\",\"whole_wire_rows_repaired\":false},"
      "\"original_action_profile\":{\"function\":\"EvaluateCouncilGates12002\","
      "\"position_key\":\"councillor_court_chaplain\",\"returned\":false,\"available\":false,"
      "\"native_predicate_calls\":0},\"pipeline\":{\"actual_request_parser\":true,"
      "\"actual_named_mailbox\":true,\"actual_owning_core_capture\":true,"
      "\"actual_clergy_reader\":true,\"actual_candidate_terms_reader\":true,"
      "\"actual_full_serializer\":true,\"actual_crozier_renderer\":true,"
      "\"offline_native_image_handler_invoked\":false,\"live\":false},\"checks\":"
      << checks << "}\n";
  Check(static_cast<bool>(out), "write compiled assertion receipt");
}
} // namespace

// Link-only seams are the same constructor/unwrap paths used by the existing
// focused full-wire target. They are outside the exercised Run/Execute/read/
// serialize/render path; the fixture asserts zero calls at the end.
namespace xar::game {
Ck3_12002AdapterBindings BindCk3_12002AdapterImage(std::uintptr_t, std::string_view) noexcept {
  ++unused_adapter_calls; return {};
}
const AdapterDescriptor &Ck3_12002AdapterDescriptor() noexcept {
  ++unused_adapter_calls; static const AdapterDescriptor descriptor{}; return descriptor;
}
std::unique_ptr<GameAdapter> CreateCk3_12003AdapterFromBindings(Ck3_12003AdapterBindings) noexcept {
  ++unused_adapter_calls; return {};
}
} // namespace xar::game
namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept {
  ++unused_adapter_calls; return adapter;
}
} // namespace xar::ck3_12002

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "one fresh existing output directory argument required");
    const std::filesystem::path directory(argv[1]);
    Check(std::filesystem::is_directory(directory), "Root prepares the first fixture output directory");
    for (std::size_t scenario = 0; scenario < kWireFiles.size(); ++scenario) {
      Fixture f;
      if (scenario == 1) f.confirm = true;
      if (scenario == 2) { f.councillor = true; f.guest = true; f.pending = true; }
      if (scenario == 3) f.requested_id = kIncumbent;
      if (scenario == 4) f.source.tasks[0].Put(r::kTaskIncumbentOffset, std::int32_t{-1});
      if (scenario == 5) f.missing_pending_manager = true;
      Query(f, directory, scenario);
    }
    CheckOriginalActionProfile();
    Check(unused_adapter_calls == 0, "unexercised constructor/native-image handler link seams remain unused");
    EmitReceipt(directory);
    std::cout << "GREEN new_cases=6 checks=" << checks
        << " actual_named_mailbox=true actual_reader=true actual_full_serializer=true"
           " actual_crozier_renderer=true synthetic_native_bindings=true live=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n';
    return 1;
  }
}
