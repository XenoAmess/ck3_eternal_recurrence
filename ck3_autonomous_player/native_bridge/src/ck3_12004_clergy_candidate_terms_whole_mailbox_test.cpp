// AUTHORED_NOTRUN. Six new actual4 candidate-terms whole scenes reuse held
// scenario definitions and the qualified actual4 Core/Clergy fixture scaffold.
// Engine memory/callbacks/frame are synthetic; all producer/serializer functions
// are production code, with no replacement production definitions or old run.
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_clergy_appointment.hpp"
#include "xar_bridge/religion_rite_governance12002_clergy_mailbox.hpp"
#include "xar_bridge/ck3_12004_clergy_candidate_terms.hpp"
#include <algorithm>

#include <windows.h>
#include <array>
#include <atomic>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <utility>
#include <vector>

namespace {
namespace old = xar::ck3_12002;
namespace actual = xar::ck3_12004;
namespace clergy = actual::religion::clergy;
namespace t = actual::religion::clergy_candidate_terms;
namespace game = xar::game;
namespace api = xar::ck3_11906;
constexpr std::int32_t kOwner = 29829;
constexpr std::int32_t kCandidate = 16777232;
constexpr std::int32_t kOtherCandidate = 0x02000011;
constexpr std::int32_t kIncumbent = 56513;
constexpr std::int32_t kTask = 7162;
constexpr std::int32_t kDate = 53222304;
constexpr std::uint64_t kPublicRevision = 2;
constexpr std::uint64_t kNativeRevision = 9;
constexpr std::uint64_t kEpoch = 991;
constexpr std::array<const char *, 6> kFiles{
    "occupied-confirm-false.json", "occupied-confirm-true.json",
    "guest-pending-true.json", "incumbent-not-in-collection.json",
    "vacant-confirm-null.json", "native-terms-unavailable.json"};
constexpr std::array<const char *, 6> kRequests{
    "g2-read-00000000000000000000000000004301",
    "g2-read-00000000000000000000000000004302",
    "g2-read-00000000000000000000000000004303",
    "g2-read-00000000000000000000000000004304",
    "g2-read-00000000000000000000000000004305",
    "g2-read-00000000000000000000000000004306"};
std::array<std::uint64_t, 6> executed_epochs{};
unsigned checks{};
void Check(bool value, const char *message) {
  ++checks;
  if (!value) throw std::runtime_error(message);
}
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <class Buffer, class T> void Put(Buffer &buffer, std::size_t offset, T value) {
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}

struct Fixture {
  const DWORD owner_thread = GetCurrentThreadId();
  Bytes<0xA8> state{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> character_storage{}, task_storage{};
  std::vector<std::byte> character_slots = std::vector<std::byte>(60000U * 0x10U);
  std::vector<std::byte> task_slots = std::vector<std::byte>(7200U * 0x10U);
  Bytes<0x1D8> owner{}, candidate{}, incumbent{}, other_candidate{};
  Bytes<0x240> landed{};
  Bytes<0x50> task{}, type{};
  Bytes<0x60> position{};
  std::array<std::int32_t, 1> task_ids{kTask};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *characters_ptr = character_storage.data(), *tasks_ptr = task_storage.data();
  void *character_fallback = nullptr, *task_fallback = nullptr;
  std::int32_t played_id = kOwner, requested_id = kCandidate;
  unsigned core_calls{}, predicate_calls{}, fire_calls{};
  unsigned producer_calls{}, release_calls{}, character_predicate_calls{};
  unsigned pending_setup_calls{}, pending_calls{}, confirm_calls{};
  bool reassign = false, fire = false, arguments_valid = true;
  bool councillor = false, guest = false, pending = false, confirm = false;
  bool missing_pending_manager = false, allocator_shape_valid = true, producer_inputs_valid = true;
  Bytes<0x20> pending_manager{};
  const void *allocator_address = nullptr;
  old::PlayerClergyAppointmentMailboxContext12002 *owning_query = nullptr;
  void *RequestedCharacter() noexcept {
    return requested_id == kIncumbent ? incumbent.data() : candidate.data();
  }
  bool OwnsNativeCallback(void *context) const noexcept {
    return owning_query && context == owning_query &&
        old::IsPlayerClergyCandidateTermsMainThread12004(context);
  }
  Fixture() {
    Put(state, actual::kGameStateDateOffset, kDate);
    Put(state, actual::kGameStateSpeedOffset, std::int32_t{2});
    Put(state, actual::kGameStateDataOffset, data.data());
    Put(jomini, actual::kJominiPlayersOffset, players.data());
    jomini[actual::kJominiPausedOffset] = std::byte{1};
    Put(players, actual::kPlayersLocalPlayerIdOffset, std::int32_t{7});
    Put(player, actual::kPlayerIdOffset, std::int32_t{7});
    Put(data, actual::kPlayerCharacterManagerOffset + actual::kPlayerManagerEntriesOffset, entries.data());
    Put(data, actual::kPlayerCharacterManagerOffset + actual::kPlayerManagerCountOffset, std::int32_t{1});
    Put(entry, actual::kPlayerEntryLocalPlayerIdOffset, std::int32_t{7});
    Put(entry, actual::kPlayerEntryCharacterIdOffset, kOwner);
    Put(character_storage, actual::kCharacterStorageSlotsOffset, character_slots.data());
    Put(character_storage, actual::kCharacterStorageCapacityOffset, std::int32_t{60000});
    Put(character_slots, static_cast<std::size_t>(kOwner) * 0x10 + 8, owner.data());
    Put(character_slots, 16U * 0x10U + 8U, candidate.data());
    Put(character_slots, 17U * 0x10U + 8U, other_candidate.data());
    Put(other_candidate, actual::kCharacterFullIdOffset, kOtherCandidate);
    Put(other_candidate, clergy::kCharacterRiteOffset, std::uint32_t{0});
    Put(candidate, actual::kCouncilCandidatesCharacterDiplomacyOffset12004, std::int32_t{3});
    Put(candidate, actual::kCouncilCandidatesCharacterStewardshipOffset12004, std::int32_t{22});
    Put(candidate, actual::kCouncilCandidatesCharacterIntrigueOffset12004, std::int32_t{4});
    Put(candidate, actual::kCouncilCandidatesCharacterLearningOffset12004, std::int32_t{29});
    Put(other_candidate, actual::kCouncilCandidatesCharacterLearningOffset12004, std::int32_t{0});
    Put(incumbent, actual::kCouncilCandidatesCharacterLearningOffset12004, std::int32_t{17});
    Put(pending_manager, 8, kOwner);
    Put(character_slots, static_cast<std::size_t>(kIncumbent) * 0x10 + 8, incumbent.data());
    Put(owner, actual::kCharacterFullIdOffset, kOwner);
    Put(candidate, actual::kCharacterFullIdOffset, kCandidate);
    Put(incumbent, actual::kCharacterFullIdOffset, kIncumbent);
    Put(owner, clergy::kCharacterRiteOffset, std::uint32_t{0});
    Put(candidate, clergy::kCharacterRiteOffset, std::uint32_t{0});
    Put(owner, clergy::kLandedOffset, landed.data());
    Put(landed, clergy::kTaskIdsOffset, task_ids.data());
    Put(landed, clergy::kTaskCountOffset, std::int32_t{1});
    Put(task_storage, 0x20, task_slots.data());
    Put(task_storage, 0x2C, std::int32_t{7200});
    Put(task_slots, static_cast<std::size_t>(kTask) * 0x10 + 8, task.data());
    Put(task, clergy::kTaskIdentityOffset, kTask);
    Put(task, clergy::kTaskTypeOffset, type.data());
    Put(task, clergy::kTaskOwnerOffset, kOwner);
    Put(task, clergy::kTaskIncumbentOffset, kIncumbent);
    Put(type, clergy::kTypePositionOffset, position.data());
  }
};
Fixture *active{};
void *Player(void *) {
  ++active->core_calls;
  active->arguments_valid &= GetCurrentThreadId() == active->owner_thread;
  return active->player.data();
}
void *CourtOwner(void *candidate) {
  active->arguments_valid &= candidate == active->RequestedCharacter() &&
      GetCurrentThreadId() == active->owner_thread;
  return active->owner.data();
}
const void *PositionTask(const void *owner, const std::string *key) {
  active->arguments_valid &= owner == active->owner.data() && key != nullptr &&
      *key == clergy::kPositionKey && GetCurrentThreadId() == active->owner_thread;
  std::int32_t count = 0;
  std::memcpy(&count, active->landed.data() + clergy::kTaskCountOffset, sizeof(count));
  return count == 0 ? nullptr : active->task.data();
}
bool ValidPosition(void *position, std::int32_t owner) {
  ++active->predicate_calls;
  active->arguments_valid &= position == active->position.data() && owner == kOwner;
  return true;
}
bool ValidCharacter(void *position, std::int32_t candidate) {
  ++active->predicate_calls;
  active->arguments_valid &= position == active->position.data() && candidate == active->requested_id;
  return true;
}
bool CanReassign(void *task, void *tooltip) {
  ++active->predicate_calls;
  active->arguments_valid &= task == active->task.data() && tooltip == nullptr;
  return active->reassign;
}
bool CanFire(void *owner, void *incumbent, void *task, std::uint32_t mode, void *tooltip) {
  ++active->fire_calls;
  active->arguments_valid &= owner == active->owner.data() && incumbent == active->incumbent.data() &&
      incumbent != active->candidate.data() && task == active->task.data() && mode == 0U && tooltip == nullptr;
  return active->fire;
}
bool Read(void *, const void *address, void *output, std::size_t size) noexcept {
  std::memcpy(output, address, size);
  return true;
}
actual::CoreBindings Core(Fixture &fixture) {
  return {true, &fixture.state_ptr, &fixture.jomini_ptr, &fixture.characters_ptr, &Player};
}
clergy::Bindings Bind(Fixture &fixture) {
  clergy::Bindings value{};
  value.enabled = true; value.offline_fixture = true;
  value.executable_sha256 = actual::kExecutableSha256;
  value.core = Core(fixture); value.task_storage_slot = &fixture.tasks_ptr;
  value.position_lookup = &PositionTask;
  value.valid_position = &ValidPosition; value.valid_character = &ValidCharacter;
  value.can_reassign = &CanReassign; value.can_fire = &CanFire;
  value.court_owner = &CourtOwner; value.read_memory = &Read;
  return value;
}
void *tls_context{};
void *__fastcall FixtureTls() noexcept { return tls_context; }
struct Pump {
  Bytes<0x28> tls{};
  std::uint8_t initialized = 1;
  std::uintptr_t unused_rng{};
  Pump(Fixture &fixture, api::MainThreadQueryMailboxV1 &mailbox) {
    tls[0x20] = std::byte{1}; tls_context = tls.data();
    mailbox.global_rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&unused_rng);
    mailbox.jomini_state_slot = reinterpret_cast<std::uintptr_t>(&fixture.jomini_ptr);
    mailbox.game_state_slot = reinterpret_cast<std::uintptr_t>(&fixture.state_ptr);
    mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter = &FixtureTls;
    mailbox.executor_submission_enabled = true;
    mailbox.permitted_executor_clergy12002 = &old::ExecutePlayerClergyAppointmentMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    mailbox.pump_epochs = kEpoch - 3;
    for (unsigned index = 0; index < 2; ++index)
      (void)api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    Check(mailbox.pump_epochs == kEpoch - 1, "actual synthetic owner warmups retain separate pump epoch");
  }
  ~Pump() { tls_context = nullptr; }
};
void Emit(const std::filesystem::path &directory, const char *file, const std::string &wire) {
  std::ofstream output(directory / file, std::ios::binary);
  output << wire << '\n';
  Check(static_cast<bool>(output), "whole production bytes written without reconstruction");
}


bool Lookup(void *context, const actual::CouncilCandidatesEnvironmentV1 &,
            const void *owner, std::string_view key, const void *&task) noexcept {
  active->arguments_valid &= active->OwnsNativeCallback(context) &&
      owner == active->owner.data() && key == clergy::kPositionKey;
  task = active->task.data();
  return active->arguments_valid;
}
bool Initialize(void *context, const actual::CouncilCandidatesEnvironmentV1 &environment,
                void *allocator, std::size_t size,
                actual::CouncilCandidatesNativeVectorV1 &vector) noexcept {
  active->arguments_valid &= active->OwnsNativeCallback(context);
  active->allocator_address = allocator;
  std::uintptr_t vtable = 0, fallback = 0;
  std::memcpy(&vtable, allocator, sizeof(vtable));
  std::memcpy(&fallback, static_cast<std::byte *>(allocator) +
      actual::kCouncilCandidatesAllocatorFallbackOffset12004, sizeof(fallback));
  active->allocator_shape_valid = size == actual::kCouncilCandidatesAllocatorSize12004 &&
      reinterpret_cast<std::uintptr_t>(allocator) % 16U == 0U &&
      vtable == environment.module_base + actual::kCouncilCandidatesAllocatorVtableRva12004 &&
      fallback == environment.module_base + actual::kCouncilCandidatesFallbackAllocatorRva12004;
  vector.data_address = reinterpret_cast<std::uintptr_t>(allocator) + 8;
  vector.capacity = 64; vector.count = 0; vector.allocator = allocator;
  return active->allocator_shape_valid;
}
bool Produce(void *context, const actual::CouncilCandidatesEnvironmentV1 &,
             const void *owner, const void *task, bool gui,
             actual::CouncilCandidatesNativeVectorV1 &vector) noexcept {
  ++active->producer_calls;
  active->arguments_valid &= active->OwnsNativeCallback(context);
  active->producer_inputs_valid = owner == active->owner.data() && task == active->task.data() && gui;
  const std::array<std::uintptr_t, 2> rows{
      reinterpret_cast<std::uintptr_t>(active->other_candidate.data()),
      reinterpret_cast<std::uintptr_t>(active->candidate.data())};
  std::memcpy(reinterpret_cast<void *>(vector.data_address), rows.data(), sizeof(rows));
  vector.count = 2;
  return active->producer_inputs_valid;
}
bool Release(void *context, const actual::CouncilCandidatesEnvironmentV1 &,
             actual::CouncilCandidatesNativeVectorV1 &vector) noexcept {
  ++active->release_calls;
  active->arguments_valid &= active->OwnsNativeCallback(context);
  const bool matched = vector.allocator == active->allocator_address &&
      vector.data_address == reinterpret_cast<std::uintptr_t>(active->allocator_address) + 8;
  vector = {};
  return matched;
}
bool Councillor(void *candidate) {
  ++active->character_predicate_calls;
  active->arguments_valid &= candidate == active->candidate.data();
  return active->councillor;
}
bool Guest(void *candidate) {
  ++active->character_predicate_calls;
  active->arguments_valid &= candidate == active->candidate.data();
  return active->guest;
}
void PendingSetup(void *storage) {
  ++active->pending_setup_calls;
  const auto *bytes = static_cast<const std::byte *>(storage);
  active->arguments_valid &= std::all_of(bytes, bytes + actual::kCouncilGatesPendingWindowSize12004,
      [](std::byte value) { return value == std::byte{}; });
  void *manager = active->missing_pending_manager ? nullptr : active->pending_manager.data();
  std::memcpy(static_cast<std::byte *>(storage) + actual::kCouncilGatesPendingManagerOffset12004,
      &manager, sizeof(manager));
}
bool Pending(void *manager, std::int32_t candidate) {
  ++active->pending_calls;
  active->arguments_valid &= manager == active->pending_manager.data() && candidate == kCandidate;
  return active->pending;
}
bool Confirm(void *storage) {
  ++active->confirm_calls;
  std::int32_t incumbent = -1, candidate = -1;
  const auto *bytes = static_cast<const std::byte *>(storage);
  std::memcpy(&incumbent, bytes + actual::kCouncilGatesConfirmationIncumbentOffset12004, sizeof(incumbent));
  std::memcpy(&candidate, bytes + actual::kCouncilGatesConfirmationCandidateOffset12004, sizeof(candidate));
  active->arguments_valid &= incumbent == kIncumbent && candidate == kCandidate && candidate != kTask;
  return active->confirm;
}
t::Environment TermsEnvironment(Fixture &fixture) {
  constexpr std::uintptr_t base = 0x140000000;
  auto environment = t::BindClergyCandidateTermsImage12004(base, actual::kExecutableSha256);
  Check(environment.enabled && environment.executable_sha256 == actual::kExecutableSha256 &&
      environment.candidates.admitted_executable_sha256 == actual::kExecutableSha256 &&
      environment.gates.admitted_executable_sha256 == actual::kExecutableSha256 &&
      reinterpret_cast<std::uintptr_t>(environment.candidates.produce_candidates) ==
          base + actual::kCouncilCandidatesProducerRva12004 &&
      reinterpret_cast<std::uintptr_t>(environment.gates.can_confirm) ==
          base + actual::kCouncilGatesCanConfirmRva12004 &&
      !t::BindClergyCandidateTermsImage12004(base, xar::ck3_12003::kExecutableSha256).enabled,
      "independent actual4 factory uses actual4 providers and rejects old3 image identity");
  environment.candidates.offline_fixture_function_overrides = true;
  environment.candidates.character_storage_slot = &fixture.characters_ptr;
  environment.candidates.character_fallback_slot = &fixture.character_fallback;
  environment.candidates.active_task_storage_slot = &fixture.tasks_ptr;
  environment.candidates.active_task_fallback_slot = &fixture.task_fallback;
  environment.access.read_memory = &Read;
  environment.access.lookup_position = &Lookup;
  environment.access.initialize_vector = &Initialize;
  environment.access.invoke_producer = &Produce;
  environment.access.release_allocation = &Release;
  environment.gates.offline_fixture = true;
  environment.gates.module_base = 0;
  environment.gates.current_thread_id = environment.gates.application_main_thread_id = GetCurrentThreadId();
  environment.gates.played_character_id_slot = &fixture.played_id;
  environment.gates.read_memory = &Read;
  environment.gates.is_councillor = &Councillor;
  environment.gates.is_guest = &Guest;
  environment.gates.pending_setup = &PendingSetup;
  environment.gates.has_pending = &Pending;
  environment.gates.can_confirm = &Confirm;
  return environment;
}
void CheckTerms(const Fixture &f, const t::Observation &out, std::size_t scenario) {
  Check(out.capture_epoch == kEpoch && out.public_revision == kPublicRevision &&
      out.native_revision == kNativeRevision && out.date_raw == kDate &&
      out.owner_character_id == kOwner && out.active_task_id == kTask &&
      out.candidate_character_id == f.requested_id,
      "actual owning capture binds separate public/native/epoch and full candidate");
  Check(out.candidate_collection_available && out.candidate_count == 2U &&
      f.producer_calls == 1 && f.release_calls == 1 &&
      f.allocator_shape_valid && f.producer_inputs_valid,
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


void Case(const std::filesystem::path &directory, std::size_t scenario) {
  Fixture fixture; active = &fixture;
  if (scenario == 1U) fixture.confirm = true;
  if (scenario == 2U) { fixture.councillor = true; fixture.guest = true; fixture.pending = true; }
  if (scenario == 3U) fixture.requested_id = kIncumbent;
  if (scenario == 4U) Put(fixture.task, clergy::kTaskIncumbentOffset, std::int32_t{-1});
  if (scenario == 5U) fixture.missing_pending_manager = true;
  game::Ck3_12004AdapterBindings adapter_bindings{};
  adapter_bindings.core = Core(fixture);
  auto adapter = game::CreateCk3_12004AdapterFromBindings(std::move(adapter_bindings));
  Check(adapter && adapter->enabled() && game::IsCk3_12004Descriptor(adapter->descriptor()),
      "actual production actual4 adapter with explicitly synthetic Core inputs");
  game::Snapshot frame{};
  Check(game::ReadCk3_12002TimelineCoreSnapshot(*adapter, frame) && frame.paused && frame.map_ready &&
      frame.played_character_id == kOwner && frame.player_id == 7 && frame.date_raw == kDate,
      "actual4 core selector publishes the owning fixture frame");
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(fixture, mailbox);
  old::PlayerClergyAppointmentMailboxContext12002 query{};
  const std::string payload = "{\"candidate_character_id\":" + std::to_string(fixture.requested_id) +
      ",\"expected_snapshot_revision\":" + std::to_string(kNativeRevision) +
      ",\"expected_revision\":" + std::to_string(kNativeRevision) +
      ",\"expected_public_revision\":" + std::to_string(kPublicRevision) + "}";
  Check(old::ParsePlayerClergyAppointmentRequest12002(payload, query.request) &&
      query.request.candidate_character_id == fixture.requested_id && query.request.expected_revision == kNativeRevision &&
      query.request.expected_public_revision == kPublicRevision, "actual existing explicit-candidate parser");
  query.envelope.game = adapter.get(); query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = frame; query.envelope.expected_snapshot_revision = kNativeRevision;
  query.bindings12004 = Bind(fixture);
  query.candidate_terms_environment12004 = TermsEnvironment(fixture);
  fixture.owning_query = &query;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
  std::string wire, failure;
  std::thread worker([&] {
    result = old::RunPlayerClergyAppointmentMailbox12002(query, kRequests[scenario], wire, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (!drained && mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  executed_epochs[scenario] = query.envelope.execution_stamp.pump_epoch;
  Check(result && drained && failure.empty() && query.completed && query.envelope.frame_stable && !wire.empty(),
      "actual named owning mailbox executes the full new candidate sibling");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle && mailbox.executed_requests == 1 &&
      executed_epochs[scenario] == kEpoch && query.envelope.ticket.sequence != 0 &&
      query.envelope.snapshot_comparison == old::QuerySnapshotComparison12002::core_frame &&
      query.bindings12004->application_main_thread_id == GetCurrentThreadId(),
      "actual4 core-frame ticket drains once and is reclaimed on its actual owner");
  auto &environment = *query.candidate_terms_environment12004;
  Check(environment.access.context == &query &&
      environment.access.capture_frame == &old::CapturePlayerClergyCandidateTermsFrame12004 &&
      environment.access.is_main_thread == &old::IsPlayerClergyCandidateTermsMainThread12004 &&
      environment.gates.current_thread_id == GetCurrentThreadId() &&
      environment.gates.application_main_thread_id == GetCurrentThreadId() &&
      query.candidate_terms_snapshot_id == "native:9" && !query.candidate_terms_environment,
      "actual4 owning executor installs actual4 frame and thread callbacks without a legacy image path");
  const auto &value = query.observation;
  Check(value.available && value.failure == clergy::Failure::none && value.capture_epoch == executed_epochs[scenario] &&
      value.owner_character_id == kOwner && value.date_raw == kDate && value.candidate_character_id == fixture.requested_id &&
      value.position_present && value.active_task_id == kTask && value.native_valid_position == true &&
      value.native_valid_character == true && value.native_can_reassign == false &&
      value.candidate_court_owner_id == kOwner && value.owner_rite_id == 0U && value.candidate_rite_id == 0U &&
      value.candidate_matches_owner_context == true && value.candidate_is_incumbent == (scenario == 3U) &&
      fixture.predicate_calls == 3U && fixture.core_calls > 0U,
      "base Clergy remains independently available with legal Rite zero and native false");
  Check((scenario == 4U && !value.incumbent_character_id && !value.native_can_fire && fixture.fire_calls == 0U) ||
      (scenario != 4U && value.incumbent_character_id == kIncumbent && value.native_can_fire == false && fixture.fire_calls == 1U),
      "base CanFire false or vacant null stays independent of the candidate confirmation");
  Check(query.candidate_terms_observation.has_value(), "existing full query includes the new actual4 sibling");
  CheckTerms(fixture, *query.candidate_terms_observation, scenario);
  Check(fixture.arguments_valid, "synthetic native callbacks receive the actual owner/task/candidate/mode");
  const auto terms_bytes = t::SerializeClergyCandidateTerms12004(*query.candidate_terms_observation);
  const auto base_bytes = clergy::SerializeClergyAppointment12004(value);
  Check(wire.find("\"candidate_terms\":" + terms_bytes) != std::string::npos &&
      wire.find("\"player_clergy_appointment\":" + base_bytes) != std::string::npos &&
      wire.find("\"snapshot_revision\":9") != std::string::npos && wire.find("\"status\":\"observed\"") != std::string::npos &&
      wire.find("\"action_eligibility_complete\":false") != std::string::npos &&
      wire.find(actual::kExecutableSha256) != std::string::npos &&
      wire.find("\"game_version\":\"1.20.0.4\"") != std::string::npos &&
      wire.find("ck3-1.20.0.4-native-player-clergy-appointment-v1") != std::string::npos &&
      wire.find(xar::ck3_12003::kExecutableSha256) == std::string::npos,
      "actual owning full serializer and actual4 renderer preserve complete native sibling bytes");
  Emit(directory, kFiles[scenario], wire);
  fixture.owning_query = nullptr; active = nullptr;
}
void Receipt(const std::filesystem::path &directory) {
  std::ostringstream output;
  output << "{\"schema\":\"xar.ck3.clergy-candidate-terms-12004-native-whole-fixture/v1\","
      "\"status\":\"GREEN\",\"cases\":6,\"whole_wire_files\":[";
  for (std::size_t index = 0; index < kFiles.size(); ++index) {
    if (index) output << ',';
    output << '\"' << kFiles[index] << '\"';
  }
  output << "],\"frame\":{\"public_revision\":2,\"native_revision\":9,\"capture_epoch\":" << executed_epochs[0]
      << ",\"date_raw\":53222304,\"owner_character_id\":29829,\"active_task_id\":7162,"
         "\"paused\":true,\"map_ready\":true},\"exact_build\":{\"game_version\":\"1.20.0.4\",\"executable_sha256\":\""
      << actual::kExecutableSha256 << "\"},\"provenance\":{\"native_memory\":\"fixture-synthetic\","
         "\"native_callbacks\":\"fixture-synthetic\",\"source_frame\":\"fixture-synthetic\","
         "\"public_revision\":\"fixture-synthetic\",\"capture_epoch\":\"fixture-synthetic\","
         "\"whole_wires\":\"compiled-production-serializer\",\"whole_wire_rows_repaired\":false},"
         "\"pipeline\":{\"actual_adapter\":true,\"actual_core_reader\":true,\"actual_request_parser\":true,"
         "\"actual_named_mailbox\":true,\"actual_owning_core_capture\":true,\"actual_clergy_reader\":true,"
         "\"actual_candidate_terms_reader\":true,\"actual_full_serializer\":true,\"actual_actual4_renderer\":true,"
         "\"offline_native_image_handler_invoked\":false,\"production_stubs\":false,\"live\":false},\"checks\":"
      << checks << "}";
  Emit(directory, "native-whole-receipt.json", output.str());
}
} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "one fresh Root-precreated output directory argument");
    const std::filesystem::path directory(argv[1]);
    Check(std::filesystem::is_directory(directory), "Root prepares the fresh whole output directory");
    for (std::size_t scenario = 0; scenario < kFiles.size(); ++scenario) Case(directory, scenario);
    Receipt(directory);
    std::cout << "GREEN actual4_candidate_terms_cases=6 checks=" << checks
        << " actual_named_mailbox=true actual_candidate_terms_reader=true live=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n';
    return 1;
  }
}
