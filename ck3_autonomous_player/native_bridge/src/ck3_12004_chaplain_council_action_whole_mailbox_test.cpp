// New Chaplain action contract only. Engine memory and native callbacks are
// explicit synthetic fixtures; the actual4 Core, collection, gates, typed
// action, main-thread mailbox and independent receipt are production code.
// The helper override records invocation and never claims engine CanSend/queue
// acceptance. Delivery is a separate, disclosed fixture-memory operation.
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_council_runtime.hpp"
#include "xar_bridge/protocol.hpp"

#include <windows.h>
#include <algorithm>
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {
namespace actual = xar::ck3_12004;
namespace api = xar::ck3_11906;
namespace bridge = xar::bridge;
namespace game = xar::game;
using Operation = bridge::CouncilApplicationMainOperationV1;
using Completion = bridge::CouncilApplicationMainCompletionV1;
constexpr std::int32_t kOwner = 29829;
constexpr std::int32_t kCandidate = 16777232;
constexpr std::int32_t kOther = 0x02000011;
constexpr std::int32_t kIncumbent = 56513;
constexpr std::int32_t kTask = 7162;
constexpr std::int32_t kDate = 53222304;
constexpr std::uint64_t kPreRevision = 9;
constexpr std::string_view kPosition = actual::kCouncilAssignChaplainPosition12004;
constexpr std::array<const char *, 4> kCases{
    "occupied-applied", "vacant-applied", "occupied-confirm-denied",
    "helper-pending-seat-unchanged"};
unsigned checks{};
void Check(bool value, const char *message) {
  ++checks;
  if (!value) throw std::runtime_error(message);
}
template<std::size_t N> using Bytes = std::array<std::byte, N>;
template<class Buffer, class T> void Put(Buffer &buffer, std::size_t offset, T value) {
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}
struct Fixture;
Fixture *active{};
void *Player(void *);
bool Read(void *, const void *, void *, std::size_t) noexcept;
bool Main(void *) noexcept;
bool Capture(void *, actual::CouncilCandidatesFrameV1 &) noexcept;
bool Lookup(void *, const actual::CouncilCandidatesEnvironmentV1 &, const void *,
            std::string_view, const void *&) noexcept;
bool Initialize(void *, const actual::CouncilCandidatesEnvironmentV1 &, void *,
                std::size_t, actual::CouncilCandidatesNativeVectorV1 &) noexcept;
bool Produce(void *, const actual::CouncilCandidatesEnvironmentV1 &, const void *,
             const void *, bool, actual::CouncilCandidatesNativeVectorV1 &) noexcept;
bool Release(void *, const actual::CouncilCandidatesEnvironmentV1 &,
             actual::CouncilCandidatesNativeVectorV1 &) noexcept;
bool Councillor(void *);
bool Guest(void *);
void PendingSetup(void *);
bool Pending(void *, std::int32_t);
bool Confirm(void *);
void Submit(void *, std::int32_t, std::int32_t) noexcept;

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
  Bytes<0x1D8> owner{}, candidate{}, incumbent{}, other{};
  Bytes<0x240> landed{};
  Bytes<0x50> task{}, type{};
  Bytes<0x60> position{};
  Bytes<0x20> pending_manager{};
  std::array<std::int32_t, 1> task_ids{kTask};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *characters_ptr = character_storage.data(), *tasks_ptr = task_storage.data();
  void *character_fallback = nullptr, *task_fallback = nullptr;
  std::int32_t played_id = kOwner;
  std::uint64_t revision = kPreRevision;
  bool confirmation_allowed = true, arguments_valid = true;
  const void *allocator_address{};
  unsigned producer_calls{}, release_calls{}, confirm_calls{}, helper_calls{};
  std::int32_t submitted_candidate = -1, submitted_task = -1;
  actual::CoreBindings core{};
  std::unique_ptr<game::GameAdapter> adapter;
  game::Snapshot expected{};
  actual::CouncilMailboxState12004 shared{};
  actual::CouncilMailboxContext12004 context{};

  explicit Fixture(bool vacant) {
    active = this;
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
    Put(character_slots, 17U * 0x10U + 8U, other.data());
    Put(character_slots, static_cast<std::size_t>(kIncumbent) * 0x10 + 8, incumbent.data());
    Put(owner, actual::kCharacterFullIdOffset, kOwner);
    Put(candidate, actual::kCharacterFullIdOffset, kCandidate);
    Put(other, actual::kCharacterFullIdOffset, kOther);
    Put(incumbent, actual::kCharacterFullIdOffset, kIncumbent);
    Put(candidate, actual::kCouncilCandidatesCharacterLearningOffset12004, std::int32_t{29});
    Put(other, actual::kCouncilCandidatesCharacterLearningOffset12004, std::int32_t{0});
    Put(incumbent, actual::kCouncilCandidatesCharacterLearningOffset12004, std::int32_t{17});
    Put(owner, actual::kCouncilCandidatesCharacterExtensionOffset12004, landed.data());
    Put(landed, actual::kCouncilCandidatesTaskIdsOffset12004, task_ids.data());
    Put(landed, actual::kCouncilCandidatesTaskCountOffset12004, std::int32_t{1});
    Put(task_storage, 0x20, task_slots.data());
    Put(task_storage, 0x2C, std::int32_t{7200});
    Put(task_slots, static_cast<std::size_t>(kTask) * 0x10 + 8, task.data());
    Put(task, actual::kCouncilCandidatesTaskIdentityOffset12004, kTask);
    Put(task, actual::kCouncilCandidatesTaskTypeOffset12004, type.data());
    Put(task, actual::kCouncilCandidatesTaskOwnerOffset12004, kOwner);
    Put(task, actual::kCouncilCandidatesTaskIncumbentOffset12004, vacant ? -1 : kIncumbent);
    Put(type, actual::kCouncilCandidatesTaskTypePositionOffset12004, position.data());
    Put(pending_manager, 8, kOwner);
    core = {true, &state_ptr, &jomini_ptr, &characters_ptr, &Player};
    game::Ck3_12004AdapterBindings bindings{};
    bindings.core = core;
    adapter = game::CreateCk3_12004AdapterFromBindings(std::move(bindings));
    Check(adapter && adapter->enabled() &&
        game::ReadCk3_12002TimelineCoreSnapshot(*adapter, expected),
        "actual4 adapter reads the explicitly synthetic paused Core frame");
    constexpr std::uintptr_t base = 0x140000000;
    auto &e = context.candidates_environment;
    e = actual::BindCouncilCandidates12004(base, actual::kExecutableSha256);
    e.offline_fixture_function_overrides = true;
    e.character_storage_slot = &characters_ptr;
    e.character_fallback_slot = &character_fallback;
    e.active_task_storage_slot = &tasks_ptr;
    e.active_task_fallback_slot = &task_fallback;
    context.candidates_access = {this, &Capture, &Main, &Read, &Initialize,
        &Produce, &Release, &Lookup};
    auto &g = context.gates_environment;
    g = actual::BindCouncilGates12004(base, actual::kExecutableSha256);
    g.offline_fixture = true; g.module_base = 0;
    g.played_character_id_slot = &played_id;
    g.read_context = this; g.read_memory = &Read;
    g.is_councillor = &Councillor; g.is_guest = &Guest;
    g.pending_setup = &PendingSetup; g.has_pending = &Pending; g.can_confirm = &Confirm;
    context.submit.environment = actual::BindCouncilAssign12004(base, actual::kExecutableSha256);
    context.submit.environment.offline_fixture = true;
    context.submit.environment.module_base = 0;
    context.submit.fixture_context = this; context.submit.fixture_helper = &Submit;
    context.shared_state = &shared; context.private_action_enabled = true;
    SetRequest();
  }
  void SetRequest() {
    snapshot_id = "native:" + std::to_string(revision);
    context.query_request = {snapshot_id, revision, revision, kDate, kOwner, kPosition};
  }
  std::string snapshot_id;
};
void *Player(void *) {
  active->arguments_valid &= GetCurrentThreadId() == active->owner_thread;
  return active->player.data();
}
bool Read(void *, const void *address, void *output, std::size_t size) noexcept {
  if (!address || !output || size == 0) return false;
  std::memcpy(output, address, size); return true;
}
bool Main(void *raw) noexcept {
  auto &f = *static_cast<Fixture *>(raw);
  return f.context.active_stamp &&
      f.context.active_stamp->thread_id == GetCurrentThreadId() &&
      GetCurrentThreadId() == f.owner_thread;
}
bool Capture(void *raw, actual::CouncilCandidatesFrameV1 &out) noexcept {
  auto &f = *static_cast<Fixture *>(raw);
  out = {};
  actual::CoreSnapshotPrefix current{};
  if (!Main(raw) || !actual::ReadCoreSnapshot(f.core, current) ||
      !current.clock.paused || !current.map_ready || !current.has_played_character ||
      !current.played_character_alive || current.played_character_id != kOwner ||
      current.clock.date_raw != kDate || current.clock.date_raw != f.context.active_stamp->date_raw)
    return false;
  std::copy(f.snapshot_id.begin(), f.snapshot_id.end(), out.snapshot_id.begin());
  out.public_revision = f.revision; out.native_revision = f.revision;
  out.date_raw = current.clock.date_raw; out.paused = current.clock.paused;
  out.map_ready = current.map_ready; out.has_played_character = true;
  out.played_character_alive = current.played_character_alive;
  out.played_character_id = current.played_character_id;
  out.played_character = reinterpret_cast<std::uintptr_t>(f.owner.data());
  return true; // production resolver sets owner/task full-ID round trips.
}
bool Lookup(void *raw, const actual::CouncilCandidatesEnvironmentV1 &,
            const void *owner, std::string_view key, const void *&task) noexcept {
  auto &f = *static_cast<Fixture *>(raw);
  task = f.task.data();
  return Main(raw) && owner == f.owner.data() && key == kPosition;
}
bool Initialize(void *raw, const actual::CouncilCandidatesEnvironmentV1 &e,
                void *allocator, std::size_t size,
                actual::CouncilCandidatesNativeVectorV1 &v) noexcept {
  auto &f = *static_cast<Fixture *>(raw);
  std::uintptr_t vtable = 0, fallback = 0;
  std::memcpy(&vtable, allocator, sizeof(vtable));
  std::memcpy(&fallback, static_cast<std::byte *>(allocator) +
      actual::kCouncilCandidatesAllocatorFallbackOffset12004, sizeof(fallback));
  f.allocator_address = allocator;
  if (!Main(raw) || size != actual::kCouncilCandidatesAllocatorSize12004 ||
      vtable != e.allocator_vtable || fallback != e.fallback_allocator) return false;
  v.data_address = reinterpret_cast<std::uintptr_t>(allocator) + 8;
  v.capacity = 64; v.count = 0; v.allocator = allocator; return true;
}
bool Produce(void *raw, const actual::CouncilCandidatesEnvironmentV1 &,
             const void *owner, const void *task, bool gui,
             actual::CouncilCandidatesNativeVectorV1 &v) noexcept {
  auto &f = *static_cast<Fixture *>(raw);
  ++f.producer_calls;
  if (!Main(raw) || owner != f.owner.data() || task != f.task.data() || !gui) return false;
  const std::array<std::uintptr_t, 2> rows{
      reinterpret_cast<std::uintptr_t>(f.other.data()),
      reinterpret_cast<std::uintptr_t>(f.candidate.data())};
  std::memcpy(reinterpret_cast<void *>(v.data_address), rows.data(), sizeof(rows));
  v.count = 2; return true;
}
bool Release(void *raw, const actual::CouncilCandidatesEnvironmentV1 &,
             actual::CouncilCandidatesNativeVectorV1 &v) noexcept {
  auto &f = *static_cast<Fixture *>(raw);
  ++f.release_calls;
  const bool valid = Main(raw) && v.allocator == f.allocator_address;
  v = {}; return valid;
}
bool Councillor(void *candidate) {
  active->arguments_valid &= candidate == active->candidate.data() || candidate == active->other.data();
  return false;
}
bool Guest(void *candidate) {
  active->arguments_valid &= candidate == active->candidate.data() || candidate == active->other.data();
  return false;
}
void PendingSetup(void *window) {
  void *manager = active->pending_manager.data();
  std::memcpy(static_cast<std::byte *>(window) + actual::kCouncilGatesPendingManagerOffset12004,
      &manager, sizeof(manager));
}
bool Pending(void *manager, std::int32_t candidate) {
  active->arguments_valid &= manager == active->pending_manager.data() &&
      (candidate == kCandidate || candidate == kOther);
  return false;
}
bool Confirm(void *confirmation) {
  ++active->confirm_calls;
  std::int32_t incumbent = -1, candidate = -1;
  const auto *bytes = static_cast<const std::byte *>(confirmation);
  std::memcpy(&incumbent, bytes + actual::kCouncilGatesConfirmationIncumbentOffset12004, sizeof(incumbent));
  std::memcpy(&candidate, bytes + actual::kCouncilGatesConfirmationCandidateOffset12004, sizeof(candidate));
  active->arguments_valid &= incumbent == kIncumbent && (candidate == kCandidate || candidate == kOther);
  return active->confirmation_allowed;
}
void Submit(void *raw, std::int32_t candidate, std::int32_t task) noexcept {
  auto &f = *static_cast<Fixture *>(raw);
  ++f.helper_calls; f.submitted_candidate = candidate; f.submitted_task = task;
  f.arguments_valid &= Main(raw) && candidate == kCandidate && task == kTask;
  // No task mutation here. Queue acceptance and native CanSend are not observed.
}
void *tls_context{};
void *__fastcall FixtureTls() noexcept { return tls_context; }
struct Pump {
  Bytes<0x28> tls{};
  std::uint8_t initialized = 1;
  std::uintptr_t unused_rng{};
  api::MainThreadQueryMailboxV1 mailbox{};
  explicit Pump(Fixture &f) {
    tls[0x20] = std::byte{1}; tls_context = tls.data();
    mailbox.global_rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&unused_rng);
    mailbox.jomini_state_slot = reinterpret_cast<std::uintptr_t>(&f.jomini_ptr);
    mailbox.game_state_slot = reinterpret_cast<std::uintptr_t>(&f.state_ptr);
    mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter = &FixtureTls;
    mailbox.executor_submission_enabled = true;
    mailbox.permitted_executor_unquadragintary = &actual::ExecuteCouncilMailbox12004;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2; ++i)
      (void)api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
  void Execute(Fixture &f, Operation operation) {
    f.context.operation = operation;
    f.context.wire.failure = bridge::CouncilApplicationMainFailureV1::none;
    f.context.wire.failure_reason.clear();
    Check(api::TrySubmitMainThreadQueryV1(mailbox, &actual::ExecuteCouncilMailbox12004,
        &f.context, f.context.ticket) == api::MainThreadQuerySubmitResultV1::submitted,
        "new-role operation queues through the actual owning main-thread mailbox");
    Check(api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva,
        GetCurrentThreadId()), "actual main-thread pump executes the queued operation");
    Check(mailbox.state == api::MainThreadQueryMailboxStateV1::completed &&
        mailbox.executor_succeeded && !f.context.active_stamp,
        "current native frame remains inside one production transaction");
    Check(api::ReclaimMainThreadQueryV1(mailbox, f.context.ticket) ==
        api::MainThreadQueryReclaimResultV1::reclaimed, "actual completed ticket reclaimed");
  }
};
void Emit(const std::filesystem::path &directory, const std::string &file,
          const Fixture &f, const std::string &request_id) {
  const auto whole = actual::SerializeCouncilActionMailbox12004(f.context, request_id);
  Check(!whole.empty(), "actual4 full native envelope serialized without body repair");
  std::ofstream out(directory / file, std::ios::binary);
  out << whole << '\n';
  Check(static_cast<bool>(out), "whole production bytes saved");
}
std::string ReadNonce(std::size_t scene, unsigned stage) {
  const auto suffix = std::to_string(6100U + static_cast<unsigned>(scene) * 10U + stage);
  return "council-read-" + std::string(32U - suffix.size(), '0') + suffix;
}
std::string Frame(std::uint64_t revision) {
  return "{\"public_revision\":" + std::to_string(revision) +
      ",\"native_revision\":" + std::to_string(revision) +
      ",\"date_raw\":53222304,\"owner_character_id\":29829,\"paused\":true,\"map_ready\":true}";
}
std::string Case(const std::filesystem::path &directory, std::size_t scene) {
  const bool vacant = scene == 1U, denied = scene == 2U, delivered = scene < 2U;
  Fixture f(vacant); Pump pump(f);
  const std::string name = kCases[scene];
  // Parse the same finite control fields as the existing bridge, then the
  // production request builder binds the current native query. No body DTOs
  // are fabricated and no production handler or serializer is replaced.
  const std::string payload = "{\"expected_revision\":9,\"position_key\":\"" +
      std::string(kPosition) + "\"}";
  std::uint64_t parsed_revision = 0;
  std::string parsed_position;
  Check(bridge::JsonUnsignedField(payload, "expected_revision", parsed_revision) &&
      bridge::JsonStringField(payload, "position_key", parsed_position, 128) &&
      parsed_revision == f.revision && parsed_position == kPosition,
      "production control parser consumes the explicitly declared request fields");
  pump.Execute(f, Operation::query_final_gates);
  const auto &query = f.context.wire.query_result;
  Check(f.context.wire.completion == Completion::query_available && query.readiness.ready &&
      query.candidate_count == 2 && f.context.wire.final_gate_row_count == 2 &&
      query.candidates[0].character_id == kCandidate &&
      query.candidates[0].native_collection_ordinal == 1,
      "fresh Chaplain collection and final native terms available in current frame");
  const std::string query_file = name + "-query.json", ack_file = name + "-ack.json";
  const std::string receipt_file = name + "-receipt.json";
  Emit(directory, query_file, f, ReadNonce(scene, 1));
  const std::string action_id = "chaplain:" + name;
  Check(api::PrepareCouncilAssignCouncillorActionRequestV1(query, kCandidate,
      action_id, f.context.action_request, kPosition), "actual generic typed Chaplain request preparation");
  if (denied) f.confirmation_allowed = false; // actual submit re-evaluates the callback.
  pump.Execute(f, Operation::submit_assignment);
  const auto &ack = f.context.wire.action_ack;
  Check(f.arguments_valid && f.producer_calls == 2 && f.release_calls == 2,
      "query and submit each use the real current collection and typed native callback receivers");
  if (denied) {
    Check(ack.status == game::CouncilAssignCouncillorAckStatusV1::rejected_before_submit &&
        ack.failure == game::CouncilAssignCouncillorFailureV1::incumbent_cannot_be_replaced &&
        !ack.native_helper_invoked && f.helper_calls == 0 && !f.shared.has_pending_ack,
        "current occupied native confirmation denial prevents helper invocation");
  } else {
    Check(ack.status == game::CouncilAssignCouncillorAckStatusV1::native_helper_invoked_verification_pending &&
        ack.failure == game::CouncilAssignCouncillorFailureV1::none && ack.native_helper_invoked &&
        !ack.queue_acceptance_observed && ack.verification_pending && f.helper_calls == 1 &&
        f.submitted_candidate == kCandidate && f.submitted_task == kTask &&
        ack.route == (vacant ? game::CouncilAssignCouncillorRouteV1::assign_vacant :
            game::CouncilAssignCouncillorRouteV1::replace_incumbent),
        "actual task-bound helper ACK is pending, not an independently applied appointment");
    std::int32_t still_incumbent = -2;
    std::memcpy(&still_incumbent, f.task.data() + actual::kCouncilCandidatesTaskIncumbentOffset12004,
        sizeof(still_incumbent));
    Check(still_incumbent == (vacant ? -1 : kIncumbent), "helper itself leaves fixture seat unchanged");
  }
  Emit(directory, ack_file, f, action_id);
  if (!denied) {
    if (delivered) Put(f.task, actual::kCouncilCandidatesTaskIncumbentOffset12004, kCandidate);
    ++f.revision; f.SetRequest(); // distinct later paused frame, no game-day advance.
    pump.Execute(f, Operation::verify_assignment_receipt);
    const auto &receipt = f.context.wire.action_receipt;
    Check(receipt.status == (delivered ? game::CouncilAssignCouncillorReceiptStatusV1::applied :
        game::CouncilAssignCouncillorReceiptStatusV1::postcondition_failed) &&
        receipt.postcondition_verified == delivered && receipt.position_key == kPosition &&
        receipt.post_native_revision == 10 && f.helper_calls == 1,
        "separate later actual task/full-ID readback determines the new Chaplain receipt");
    Check(delivered ? receipt.incumbent_character_id == kCandidate && !f.shared.has_pending_ack :
        receipt.reason == "candidate_not_observed_as_incumbent" && f.shared.has_pending_ack,
        "an unchanged incumbent cannot gain applied material from helper ACK");
    Emit(directory, receipt_file, f, ReadNonce(scene, 2));
  }
  Check(vacant ? f.confirm_calls == 0 : f.confirm_calls == 3,
      "vacancy has no occupied confirmation; occupied query and submit use exact candidate predicates");
  std::ostringstream out;
  out << "{\"name\":\"" << name << "\",\"query_file\":\"" << query_file
      << "\",\"ack_file\":\"" << ack_file << "\",\"receipt_file\":"
      << (denied ? "null" : "\"" + receipt_file + "\"")
      << ",\"candidate_character_id\":16777232,\"pre_frame\":" << Frame(9)
      << ",\"post_frame\":" << (denied ? "null" : Frame(10))
      << ",\"expected_query_status\":\"available\",\"expected_ack_status\":\""
      << (denied ? "rejected_before_submit" : "native_helper_invoked_verification_pending")
      << "\",\"expected_ack_failure\":\"" << (denied ? "incumbent_cannot_be_replaced" : "none")
      << "\",\"expected_receipt_status\":" << (denied ? "null" : delivered ? "\"applied\"" : "\"postcondition_failed\"")
      << ",\"synthetic_delivery\":" << (delivered ? "true" : "false")
      << ",\"pump_operations\":" << pump.mailbox.executed_requests << '}';
  return out.str();
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) { std::cerr << "usage: chaplain-action-whole OUTPUT_DIR\n"; return 2; }
  try {
    const std::filesystem::path directory = argv[1];
    std::filesystem::create_directories(directory);
    std::array<std::string, 4> cases;
    for (std::size_t i = 0; i < cases.size(); ++i) cases[i] = Case(directory, i);
    active = nullptr;
    std::ofstream receipt(directory / "native-whole-receipt.json", std::ios::binary);
    receipt << "{\"schema\":\"xar.ck3.chaplain-council-action-12004-native-whole-fixture/v1\","
        "\"status\":\"GREEN\",\"exact_build\":{\"game_version\":\"1.20.0.4\",\"executable_sha256\":\""
        << actual::kExecutableSha256 << "\"},\"cases\":[";
    for (std::size_t i = 0; i < cases.size(); ++i) {
      if (i) receipt << ',';
      receipt << cases[i];
    }
    receipt << "],\"whole_packets\":11,\"checks\":" << checks
        << ",\"synthetic_engine_memory_callbacks\":true,\"production_replacement_definitions\":false,"
        "\"actual4_core_reader\":true,\"actual4_candidate_reader\":true,\"actual4_final_gate_evaluator\":true,"
        "\"actual4_typed_action\":true,\"actual_main_thread_pump\":true,\"independent_task_incumbent_readback\":true,"
        "\"actual4_whole_serializer\":true,\"control_parser_only_not_full_bridge_handler\":true,"
        "\"native_can_send_executed\":false,\"queue_acceptance_observed\":false,\"game_operations\":0,"
        "\"game_days\":0,\"g2_credit\":0,\"old_candidate_six_case_reruns\":0,\"production_live\":false}\n";
    Check(static_cast<bool>(receipt), "new-role receipt written");
    std::cout << "actual4 Chaplain action: four cases, eleven whole packets\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n'; return 1;
  }
}
