#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/ck3_12004_thread_runtime.hpp"
#include <atomic>
#include <thread>
#include "xar_bridge/ck3_12004_player_claims_v1.hpp"
#include "xar_bridge/ck3_12004_war_cash_claim_terms.hpp"
#include "xar_bridge/player_claims_v1_serializer.hpp"
#include "ck3_12004_foundation_fixture_support.hpp"

#include <array>
#include <bit>
#include <cstring>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

// Caller-owned component memory and a synthetic getter, never a CK3 module.
// The getter writes the independently qualified Crozier optional layout.
// Reader, full-ID resolvers, parser and serializer are the production functions.
// The getter is synthetic; the new test below uses the actual owner mailbox in caller-owned memory.
namespace {
namespace current = xar::ck3_12004;
namespace old_layout = xar::ck3_12002;
namespace game = xar::game;
using Result = game::ReadPlayerClaimsV1Result;
constexpr std::int32_t kDate = 53288256;
constexpr std::int32_t kActor = current::fixture::CoreMemory::kCharacterId;
constexpr std::int32_t kNextActor = kActor | 0x01000000;
constexpr std::int32_t kAbsent = 0;
constexpr std::int32_t kStrongExplicit = 0x01000001;
constexpr std::int32_t kStrongImplicit = 0x03000002;
constexpr std::int32_t kWeakImplicit = 0x7F000003;
constexpr std::int32_t kWeakExplicit = 0x06000004;
constexpr std::int32_t kMissing = 0x05000005;
constexpr std::uint64_t kRevision = 73;

static_assert(sizeof(void *) == 8, "This fixture exercises the qualified x64 layout");
static_assert(sizeof(old_layout::ClaimTermsStorage) == 0x20);

int checks = 0;
int scenarios = 0;
std::uint64_t wire_sequence = 0;
void Check(bool condition, std::string_view message) {
  ++checks;
  if (!condition) throw std::runtime_error(std::string(message));
}
template <class T> void Put(void *object, std::size_t offset, const T &value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template <class T> T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}

enum class Fault {
  none, wrong_return, invalid_present, wrong_vtable, wrong_claim_generation,
  invalid_strong, invalid_implicit, row_changes_on_second_read,
  played_character_changes, title_pointer_changes,
  title_generation_changes_after_second_read, date_changes, pause_changes,
  speed_changes
};
struct ClaimRow {
  bool present;
  std::uint8_t strong;
  std::uint8_t implicit;
};

struct Fixture {
  current::fixture::CoreMemory core{kDate, 4, true};
  std::array<std::byte, 0x30> title_storage{};
  std::array<std::byte, 8 * 0x10> title_slots{};
  std::map<std::int32_t, std::array<std::byte, 0x20>> titles;
  std::map<std::int32_t, ClaimRow> rows;
  std::array<std::byte, 0x20> replacement_title{};
  std::array<void *, 1> vtable{};
  std::array<void *, 1> foreign_vtable{};
  void *title_storage_slot = title_storage.data();
  current::PlayerClaimsBindingsV1 bindings{};
  Fault fault = Fault::none;
  std::size_t getter_calls = 0;
  std::size_t destructor_calls = 0;
  bool bad_destructor_call = false;
  void *last_optional = nullptr;
  std::map<std::int32_t, std::size_t> row_reads;
  std::vector<std::int32_t> observed_actors;
  static inline Fixture *active = nullptr;

  Fixture() {
    active = this;
    vtable[0] = reinterpret_cast<void *>(&DestroyClaim);
    Put(title_storage.data(), 0x20, static_cast<void *>(title_slots.data()));
    Put(title_storage.data(), 0x2C, std::int32_t{8});
    AddTitle(kAbsent, {false, 0xFF, 0xFF});
    AddTitle(kStrongExplicit, {true, 1, 0});
    AddTitle(kStrongImplicit, {true, 1, 1});
    AddTitle(kWeakImplicit, {true, 0, 1});
    AddTitle(kWeakExplicit, {true, 0, 0});
    bindings.enabled = true;
    bindings.core = core.Bindings();
    bindings.provinces.enabled = true;
    bindings.provinces.landed_title_storage_slot = &title_storage_slot;
    bindings.read_character_claim = &ReadClaim;
    bindings.character_claim_vtable = reinterpret_cast<std::uintptr_t>(vtable.data());
  }
  ~Fixture() { active = nullptr; }
  Fixture(const Fixture &) = delete;
  Fixture &operator=(const Fixture &) = delete;

  void AddTitle(std::int32_t id, ClaimRow row) {
    auto &bytes = titles[id];
    Put(bytes.data(), 0x10, id);
    const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
    Put(title_slots.data(), static_cast<std::size_t>(index) * 0x10 + 8,
        static_cast<void *>(bytes.data()));
    rows[id] = row;
  }
  static void *DestroyClaim(void *claim, std::int32_t delete_flags) {
    auto &f = *active;
    ++f.destructor_calls;
    f.bad_destructor_call = f.bad_destructor_call || delete_flags != 0 ||
        claim != f.last_optional || Get<std::uint8_t>(claim, 0x18) != 1;
    return claim;
  }
  static void *ReadClaim(void *output, void *claimant, void *title) {
    auto &f = *active;
    ++f.getter_calls;
    const auto title_id = Get<std::int32_t>(title, 0x10);
    const auto found = f.rows.find(title_id);
    if (found == f.rows.end()) return nullptr;
    auto row = found->second;
    const auto visit = ++f.row_reads[title_id];
    f.observed_actors.push_back(Get<std::int32_t>(claimant, 0x18));
    f.last_optional = output;
    if (f.fault == Fault::row_changes_on_second_read && visit == 2)
      row.strong = static_cast<std::uint8_t>(row.strong == 0 ? 1 : 0);

    // Literals come from the already qualified 0x20 return object, rather than
    // computing an oracle from the decoder's current field constants.
    std::memset(output, 0xCC, 0x20);
    Put(output, 0x00, f.fault == Fault::wrong_vtable ? f.foreign_vtable.data()
                                                     : f.vtable.data());
    Put(output, 0x08, f.fault == Fault::wrong_claim_generation
                         ? title_id ^ 0x01000000 : title_id);
    Put(output, 0x0C, std::uint32_t{0x436C6169});
    Put(output, 0x10, f.fault == Fault::invalid_strong ? std::uint8_t{2} : row.strong);
    Put(output, 0x11, f.fault == Fault::invalid_implicit ? std::uint8_t{2} : row.implicit);
    Put(output, 0x18, f.fault == Fault::invalid_present ? std::uint8_t{2}
                                                     : std::uint8_t(row.present));
    // Exercise the last four bytes of the qualified optional object as well.
    Put(output, 0x1C, std::uint32_t{0xA5A5A5A5});

    if (f.getter_calls == 1) {
      switch (f.fault) {
      case Fault::played_character_changes:
        f.core.SetPlayingCharacterFullId(kNextActor);
        break;
      case Fault::title_pointer_changes:
        f.replacement_title = f.titles.at(title_id);
        Put(f.title_slots.data(),
            static_cast<std::size_t>(static_cast<std::uint32_t>(title_id) &
                                     0x00FFFFFFU) * 0x10 + 8,
            static_cast<void *>(f.replacement_title.data()));
        break;
      case Fault::date_changes: f.core.SetClock(kDate + 24, 4, true); break;
      case Fault::pause_changes: f.core.SetClock(kDate, 4, false); break;
      case Fault::speed_changes: f.core.SetClock(kDate, 3, true); break;
      default: break;
      }
    }
    if (f.fault == Fault::title_generation_changes_after_second_read &&
        f.getter_calls == 2)
      Put(title, 0x10, title_id ^ 0x01000000);
    return f.fault == Fault::wrong_return ? nullptr : output;
  }
};

} // namespace

namespace {
template <class Value, std::size_t Size>
void Store(std::array<std::byte, Size> &bytes, std::size_t offset, Value value) {
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

struct MemoryFixture {
  void *iat = nullptr;
  DWORD page_protect = PAGE_READONLY;
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x18> state{};
  std::array<std::byte, 0x28> tls{};
  std::uintptr_t jomini_slot = 0;
  std::uintptr_t state_slot = 0;
  std::uintptr_t null_rng_slot = 0;
  std::uint8_t tls_initialized = 1;
};
MemoryFixture *g_memory = nullptr;

BOOL WINAPI FakePeek(LPMSG, HWND, UINT, UINT, UINT) { return FALSE; }
void *__fastcall FakeTls() noexcept { return g_memory->tls.data(); }
bool FakeQuery(void *opaque, const void *address,
               MEMORY_BASIC_INFORMATION &output) noexcept {
  auto &memory = *static_cast<MemoryFixture *>(opaque);
  if (address != &memory.iat) return false;
  output = {};
  output.BaseAddress = reinterpret_cast<void *>(
      reinterpret_cast<std::uintptr_t>(address) & ~4095ULL);
  output.AllocationBase = output.BaseAddress;
  output.RegionSize = 4096;
  output.State = MEM_COMMIT;
  output.Type = MEM_IMAGE;
  output.Protect = memory.page_protect;
  return true;
}
bool FakeProtect(void *opaque, void *, std::size_t size, DWORD desired,
                 DWORD &previous) noexcept {
  auto &memory = *static_cast<MemoryFixture *>(opaque);
  if (size != 4096) return false;
  previous = memory.page_protect;
  memory.page_protect = desired;
  return true;
}

}

namespace {
enum class SourceMutation { none, actor, date, titles, unavailable };
class RouteAdapter : public game::GameAdapter {
public:
  Fixture *fixture;
  mutable int snapshot_reads = 0;
  mutable int claim_calls = 0;
  bool invalid_descriptor = false;
  bool completion_changes = false;
  SourceMutation source_mutation = SourceMutation::none;
  explicit RouteAdapter(Fixture &value) : fixture(&value) {}
  const game::AdapterDescriptor &descriptor() const noexcept override {
    static constexpr std::array<std::string_view, 1> snapshot_caps{"game.state.snapshot"};
    static const game::AdapterDescriptor good{
        "ck3-1.20.0.4-msvc-x64", "1.20.0.4", current::kExecutableSha256,
        "owned-memory-software-route-fixture", snapshot_caps};
    static const game::AdapterDescriptor bad{"wrong", "wrong", "wrong", "wrong", {}};
    return invalid_descriptor ? bad : good;
  }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    ++snapshot_reads;
    current::CoreSnapshotPrefix frame{};
    if (!current::ReadCoreSnapshot(fixture->bindings.core, frame)) return false;
    out = {};
    out.date_raw = frame.clock.date_raw;
    out.speed = frame.clock.speed;
    out.paused = frame.clock.paused;
    out.player_id = frame.local_player_id;
    out.map_ready = frame.map_ready;
    out.has_played_character = frame.has_played_character;
    out.played_character_id = frame.played_character_id;
    out.played_character_alive = frame.played_character_alive;
    if (completion_changes && snapshot_reads == 2) out.date_raw += 24;
    return true;
  }
  Result read_player_claims_v1(const std::vector<std::int32_t> &ids,
      game::PlayerClaimsV1 &out) const noexcept override {
    ++claim_calls;
    if (source_mutation == SourceMutation::unavailable) { out = {}; return Result::unavailable; }
    const auto result = current::ReadPlayerClaimsV1(fixture->bindings, ids, out);
    if (source_mutation == SourceMutation::actor) out.actor_character_id ^= 0x01000000;
    if (source_mutation == SourceMutation::date) out.date_raw += 24;
    if (source_mutation == SourceMutation::titles) out.title_ids = {kWeakExplicit};
    return result;
  }
#define OFF(Type, Name, Args) game::Type Name Args const noexcept override { return game::Type::unavailable; }
  OFF(PauseSubmitResult, submit_pause_map, (game::Snapshot *))
  OFF(ResumeSubmitResult, submit_resume_map, (game::Snapshot *))
  bool submit_set_speed(std::int32_t) const noexcept override { std::abort(); }
  OFF(SelectEventOptionResult, submit_select_event_option, (std::int32_t))
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override { std::abort(); }
  OFF(ReplyPendingInteractionResult, submit_reply_to_pending_interaction, (game::PendingInteractionReply))
  OFF(RaiseTroopsResult, submit_raise_troops_default, ())
  OFF(MoveArmyResult, submit_move_army, (std::int32_t, std::int32_t))
  game::PreviewMoveArmyResult preview_move_army(std::int32_t, std::int32_t) const noexcept override { std::abort(); }
  OFF(DisbandArmyResult, submit_disband_army, (std::int32_t))
  OFF(SplitArmyHalfResult, submit_split_army_half, (std::int32_t))
  OFF(MergeArmiesResult, submit_merge_armies, (std::int32_t, std::int32_t))
  OFF(StartAssaultResult, submit_start_assault, (std::int32_t))
  OFF(StopAssaultResult, submit_stop_assault, (std::int32_t))
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &) const noexcept override { std::abort(); }
  OFF(ReadDeclarableWarsResult, read_declarable_wars_for_target, (std::int32_t, std::vector<game::DeclarableWarSnapshot> &))
  OFF(DeclareWarResult, submit_declare_war, (const game::DeclarableWarSnapshot &))
  OFF(ReadArrangeMarriageChoicesResult, read_arrange_marriage_choices, (std::vector<game::ArrangeMarriageChoice> &, game::ArrangeMarriageQueryDiagnostics &))
  OFF(ArrangeMarriageResult, submit_arrange_marriage, (const game::ArrangeMarriageChoice &))
  OFF(EnforceDemandsResult, submit_enforce_demands, (std::int32_t))
  OFF(ReadArmyStrengthsResult, read_army_strengths, (std::vector<game::ArmyStrengthSnapshot> &))
  OFF(ReadCombatSimulationInputsResult, read_combat_simulation_inputs, (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &))
  OFF(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3, (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &))
  OFF(ReadWarTerminationOptionsResult, read_war_termination_options, (std::int32_t, game::WarTerminationOptionsSnapshot &))
  OFF(ReadWarTerminationTermsResult, read_war_termination_terms, (std::int32_t, game::WarTerminationTermsSnapshot &))
  OFF(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms, (std::int32_t, game::WarTerminationExitTermsSnapshot &))
  OFF(SurrenderWarResult, submit_surrender_war, (std::int32_t))
  OFF(OfferWhitePeaceResult, submit_offer_white_peace, (std::int32_t))
#undef OFF
};
}


namespace {
namespace api = xar::ck3_11906;
namespace build = xar::ck3_12002;

class MailboxAdapter final : public RouteAdapter {
public:
  DWORD owner = GetCurrentThreadId();
  mutable int wrong_owner = 0;
  mutable bool world_changed = false;
  bool change_world_after_read = false;
  mutable Result actual_reader_result = Result::unavailable;
  explicit MailboxAdapter(Fixture &value) : RouteAdapter(value) {}
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    if (GetCurrentThreadId() != owner) { ++wrong_owner; return false; }
    const bool value = RouteAdapter::read_snapshot(out);
    if (world_changed) out.player_armies.push_back({});
    return value;
  }
  Result read_player_claims_v1(const std::vector<std::int32_t> &ids,
      game::PlayerClaimsV1 &out) const noexcept override {
    if (GetCurrentThreadId() != owner) { ++wrong_owner; return Result::unavailable; }
    actual_reader_result = RouteAdapter::read_player_claims_v1(ids, out);
    if (change_world_after_read) world_changed = true;
    return actual_reader_result;
  }
};

void Pump(api::MainThreadQueryMailboxV1 &mailbox) {
  api::ObserveMainThreadPumpAndDrainV1(mailbox,
      current::kSdlWindowsPumpFirstPeekReturnRva, GetCurrentThreadId());
}

struct Scene {
  const char *name;
  std::int32_t actor;
  bool expected_available;
  int getter_calls;
  bool stale = false;
  bool invalid_title = false;
  bool changed_rows = false;
  bool finish_changed = false;
  bool admission_changed = false;
};

void RunScene(const Scene &scene, const std::filesystem::path &directory) {
  Fixture fixture;
  void *zero = scene.actor == 0 ? current::ResolveCoreCharacter(fixture.bindings.core, kActor) : nullptr;
  fixture.core.SetPlayingCharacterFullId(scene.actor);
  if (scene.actor == 0) {
    void *storage = *fixture.bindings.core.character_storage_slot;
    void *slots = Get<void *>(storage, current::kCharacterStorageSlotsOffset);
    Put(slots, current::kCharacterStorageObjectOffset, zero);
  }
  if (scene.stale) fixture.core.SetCharacterFullId(scene.actor ^ 0x01000000);
  if (scene.changed_rows) fixture.fault = Fault::row_changes_on_second_read;
  MailboxAdapter native(fixture);
  native.change_world_after_read = scene.finish_changed;
  MemoryFixture memory;
  g_memory = &memory;
  memory.iat = reinterpret_cast<void *>(&FakePeek);
  memory.jomini_slot = reinterpret_cast<std::uintptr_t>(memory.jomini.data());
  memory.state_slot = reinterpret_cast<std::uintptr_t>(memory.state.data());
  Store(memory.tls, 0x20, std::uint8_t{1});
  Store(memory.jomini, 0x20, std::uint8_t{1});
  Store(memory.state, 0x08, kDate);
  api::MainThreadQueryMailboxV1 mailbox;
  build::WorkerAdapter proxy(native, mailbox, build::ConsoleFixtureBindings{});
  std::array<api::MainThreadQueryExecutorV1, 14> executors{};
  executors[13] = &build::ExecuteSemanticAdapter12002;
  auto environment = current::BindThreadRuntimeImage(
      0x140000000ULL, current::kExecutableSha256, executors);
  environment.offline_fixture = true;
  environment.peek_message_iat_slot_override = &memory.iat;
  environment.resolved_peek_message_override = &FakePeek;
  environment.global_rng_wrapper_slot_override = reinterpret_cast<std::uintptr_t>(&memory.null_rng_slot);
  environment.jomini_state_slot_override = reinterpret_cast<std::uintptr_t>(&memory.jomini_slot);
  environment.game_state_slot_override = reinterpret_cast<std::uintptr_t>(&memory.state_slot);
  environment.tls_initialized_flag_override = reinterpret_cast<std::uintptr_t>(&memory.tls_initialized);
  environment.tls_context_getter_override = &FakeTls;
  environment.memory_protection_context = &memory;
  environment.memory_query_override = &FakeQuery;
  environment.memory_protect_override = &FakeProtect;
  environment.system_page_size_override = 4096;
  environment.snapshot_observer_callback = &build::ObserveAdapterSnapshot12002;
  environment.snapshot_observer_context = &proxy;
  Check(api::InstallMainThreadQueryMailboxV1(mailbox, environment), "owned offline mailbox install failed");
  Pump(mailbox);
  Pump(mailbox);
  Check(api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready, "paused mailbox not ready");

  std::atomic<bool> done{false};
  Result result = Result::unavailable;
  game::PlayerClaimsV1 output;
  std::vector<std::int32_t> ids{scene.invalid_title ? -1 : kStrongExplicit};
  std::thread worker([&] {
    result = proxy.read_player_claims_v1(ids, output);
    done.store(true);
  });
  const auto deadline = GetTickCount64() + 5'000;
  while (!done.load() && mailbox.state.load() != api::MainThreadQueryMailboxStateV1::queued && GetTickCount64() < deadline) Sleep(1);
  const bool queued = mailbox.state.load() == api::MainThreadQueryMailboxStateV1::queued;
  bool executor_identity = false, envelope_identity = false;
  if (queued) {
    executor_identity = mailbox.executor.load() == &build::ExecuteSemanticAdapter12002;
    const auto *envelope = static_cast<const build::QueryMailboxEnvelope *>(mailbox.executor_context);
    envelope_identity = envelope != nullptr && envelope->typed_context != nullptr &&
        envelope->snapshot_comparison == build::QuerySnapshotComparison12002::full_snapshot &&
        envelope->expected_snapshot_revision != 0 && envelope->ticket.sequence == mailbox.published_sequence.load();
    if (scene.admission_changed) native.world_changed = true;
    Pump(mailbox);
  }
  while (!done.load() && GetTickCount64() < deadline) Sleep(1);
  if (!done.load()) {
    api::MainThreadQueryTicketV1 ticket{mailbox.published_sequence.load()};
    api::CancelMainThreadQueryV1(mailbox, ticket);
  }
  worker.join();
  const auto diagnostic = api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox);
  const bool available = result == Result::available && output.available;
  const auto wire = game::SerializePlayerClaimsV1(output, result, diagnostic.completed_sequence, kRevision,
      scene.invalid_title ? "query-player-claims-v1--1" : "query-player-claims-v1-16777217");
  std::ofstream saved(directory / (std::string(scene.name) + ".inner-result.json"), std::ios::binary);
  saved << wire << '\n';
  Check(saved.good(), "could not preserve actual reader result");
  Check(queued && executor_identity && envelope_identity, "actual semantic request not queued with expected producer identity");
  Check(available == scene.expected_available, "wrong semantic claims outcome");
  Check(fixture.getter_calls == static_cast<std::size_t>(scene.getter_calls), "wrong actual getter reachability");
  Check(native.wrong_owner == 0 && !fixture.bad_destructor_call, "owner or optional lifetime changed");
  Check(diagnostic.completed_sequence == 1 && diagnostic.published_sequence == 1 &&
      diagnostic.executor_started_requests == 1 && diagnostic.executed_requests == 1,
      "actual pump did not complete its one semantic request");
  Check(diagnostic.state == api::MainThreadQueryMailboxStateV1::idle && mailbox.executor.load() == nullptr &&
      mailbox.executor_context == nullptr && diagnostic.failure_flags == 0, "actual wait/reclaim did not return mailbox to idle");
  if (scene.expected_available) {
    Check(output.actor_character_id == scene.actor && output.title_ids == ids && output.claims.size() == 1,
        "signed identity or ordered request changed through SemanticRequest");
  }
  if (scene.finish_changed || scene.admission_changed)
    Check(output.unavailable_reason == "not_read" && output.title_ids.empty() && output.claims.empty(),
        "failed frame proof leaked a partial SemanticRequest result");
  if (scene.finish_changed) Check(native.actual_reader_result == Result::available,
      "finish failure did not occur after successful actual claims reader");
  if (scene.admission_changed) Check(native.claim_calls == 0, "admission drift reached actual reader");
  if (scene.changed_rows) Check(output.unavailable_reason == "player_claim_rows_changed", "unavailable native reason was lost by move");
  ++scenarios;
  std::cout << "{\"case\":\"" << scene.name << "\",\"pass\":true,\"queued\":true,\"completed_sequence\":"
            << diagnostic.completed_sequence << ",\"reclaimed_idle\":true,\"getter_calls\":" << fixture.getter_calls
            << ",\"destructor_calls\":" << fixture.destructor_calls << ",\"native_claim_calls\":" << native.claim_calls
            << ",\"wrong_owner\":" << native.wrong_owner << ",\"available\":" << (available ? "true" : "false") << "}\n";
  Check(api::UninstallMainThreadQueryMailboxV1(mailbox, 1'000) == api::MainThreadQueryUninstallResultV1::uninstalled,
      "owned offline mailbox not uninstalled");
  g_memory = nullptr;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "new output directory required");
    std::filesystem::path directory = std::filesystem::path(argv[1]) / ("run-" + std::to_string(GetCurrentProcessId()) + "-" + std::to_string(GetTickCount64()));
    Check(!std::filesystem::exists(directory) && std::filesystem::create_directories(directory), "preserve old outputs");
    const auto negative = std::bit_cast<std::int32_t>(static_cast<std::uint32_t>(kActor) | 0x80000000U);
    RunScene({"positive", kActor, true, 2}, directory);
    RunScene({"signed80", negative, true, 2}, directory);
    RunScene({"zero_actor", 0, true, 2}, directory);
    RunScene({"stale_actor", negative, false, 0, true}, directory);
    RunScene({"invalid_title", negative, false, 0, false, true}, directory);
    RunScene({"rows_changed", negative, false, 2, false, false, true}, directory);
    RunScene({"finish_snapshot_changed", negative, false, 2, false, false, false, true}, directory);
    RunScene({"admission_snapshot_changed", negative, false, 0, false, false, false, false, true}, directory);
    std::cout << "PASS checks=" << checks << " scenarios=" << scenarios
              << "; actual current WorkerAdapter/semantic enum/ExecuteSemantic/owned pump/query mailbox/wait/reclaim/claims reader"
                 "; synthetic snapshot/getter; no full Bridge/Game/DLL credit\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL: " << error.what() << '\n'; return 1; }
}
