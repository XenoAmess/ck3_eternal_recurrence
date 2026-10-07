// AUTHORED_NOTRUN: six new M7 raw observer whole packets. Engine memory,
// callbacks, public frame and pump epoch are synthetic. No game is invoked.
// The real mailbox executor, law capture, actual4 providers, raw reader,
// whole command-result serializer and actual4 renderer are linked unchanged.
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12002_realm_law.hpp"
#include "xar_bridge/crown_authority_cooldown_observer_12004.hpp"
#include "xar_bridge/realm_law_12004_native.hpp"

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
namespace law = xar::ck3_12002;
namespace actual = xar::ck3_12004;
namespace native_law = actual::private_law;
namespace raw = actual::crown_cooldown;
namespace game = xar::game;
namespace api = xar::ck3_11906;
constexpr std::int32_t kActor = 29829, kDate = 53288256, kClock = 100;
constexpr std::int32_t kToken = 73;
constexpr std::uint64_t kPublicRevision = 2, kNativeRevision = 9, kEpoch = 1007;
constexpr std::uintptr_t kBase = 0x10000000, kImage = 0x140000000;
constexpr std::uintptr_t kLawContext = kBase + 0x400, kActiveSlots = kBase + 0x800;
constexpr std::uintptr_t kDatabase = kBase + 0x1000, kCrown = kBase + 0x1400;
constexpr std::uintptr_t kSuccession = kBase + 0x1800, kGroups = kBase + 0x1C00;
constexpr std::uintptr_t kCrownSlots = kBase + 0x2000, kSuccessionSlots = kBase + 0x2100;
constexpr std::array<std::uintptr_t, 3> kLaws{kBase + 0x3000, kBase + 0x4000, kBase + 0x5000};
constexpr std::array<const char *, 6> kFiles{
    "absent.json", "positive.json", "zero.json", "negative-minus-one.json",
    "untimed.json", "read-failure.json"};
constexpr std::array<const char *, 6> kRequests{
    "realm-law-read-00000000000000000000000000000001",
    "realm-law-read-00000000000000000000000000000002",
    "realm-law-read-00000000000000000000000000000003",
    "realm-law-read-00000000000000000000000000000004",
    "realm-law-read-00000000000000000000000000000005",
    "realm-law-read-00000000000000000000000000000006"};
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
  Bytes<0x30> character_storage{};
  std::vector<std::byte> character_slots = std::vector<std::byte>(30000U * 0x10U);
  Bytes<0x1D8> actor{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *characters_ptr = character_storage.data();
  Bytes<0x20000> memory{};
  Bytes<0x30> variable_context{};
  Bytes<0x20> variable_row{};
  const std::string variable_name = "crown_authority_cooldown";
  bool read_failure = false, arguments_valid = true;
  unsigned core_calls{}, law_memory_reads{}, profile_reads{}, context_calls{};

  template <class T> void Store(std::uintptr_t address, T value) {
    Put(memory, static_cast<std::size_t>(address - kBase), value);
  }
  void Key(std::uintptr_t object, std::string_view key, std::uintptr_t heap) {
    const auto storage = object + native_law::kLawNativeKeyOffset12004;
    Store(storage, heap);
    Store(storage + 0x10, static_cast<std::uint64_t>(key.size()));
    Store(storage + 0x18, std::uint64_t{127});
    std::memcpy(memory.data() + heap - kBase, key.data(), key.size());
  }
  explicit Fixture(std::size_t scenario) {
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
    Put(entry, actual::kPlayerEntryCharacterIdOffset, kActor);
    Put(character_storage, actual::kCharacterStorageSlotsOffset, character_slots.data());
    Put(character_storage, actual::kCharacterStorageCapacityOffset, std::int32_t{30000});
    Put(character_slots, static_cast<std::size_t>(kActor) * actual::kCharacterStorageSlotStride +
        actual::kCharacterStorageObjectOffset, actor.data());
    Put(actor, actual::kCharacterFullIdOffset, kActor);
    Put(actor, native_law::kCharacterLawContextOffset12004, kLawContext);
    Store(kLawContext + native_law::kLawCollectionOffset12004, kActiveSlots);
    Store(kLawContext + native_law::kLawCollectionOffset12004 + 0x0C, std::int32_t{2});
    Store(kActiveSlots, kLaws[0]); Store(kActiveSlots + 8, kLaws[2]);
    Store(kDatabase + native_law::kLawGroupDatabaseArrayOffset12004, kGroups);
    Store(kDatabase + native_law::kLawGroupDatabaseCountOffset12004, std::int32_t{2});
    Store(kGroups, kCrown); Store(kGroups + 8, kSuccession);
    Key(kCrown, "crown_authority", kBase + 0xC000);
    Key(kSuccession, "succession_order_laws", kBase + 0xC100);
    Store(kCrown + native_law::kLawGroupCandidateArrayOffset12004, kCrownSlots);
    Store(kCrown + native_law::kLawGroupCandidateCountOffset12004, std::int32_t{2});
    Store(kSuccession + native_law::kLawGroupCandidateArrayOffset12004, kSuccessionSlots);
    Store(kSuccession + native_law::kLawGroupCandidateCountOffset12004, std::int32_t{1});
    constexpr std::array<std::string_view, 3> keys{
        "crown_authority_0", "crown_authority_1", "confederate_partition_succession_law"};
    for (std::size_t index = 0; index < kLaws.size(); ++index) {
      Store(index < 2 ? kCrownSlots + index * 8 : kSuccessionSlots, kLaws[index]);
      Store(kLaws[index] + native_law::kLawOwningGroupOffset12004,
          index < 2 ? kCrown : kSuccession);
      Key(kLaws[index], keys[index], kBase + 0xC200 + index * 0x100);
    }
    const auto policy = kLaws[2] + native_law::kRealmLawSuccessionPolicyOffset12004;
    Store(policy + 4, std::uint8_t{1});
    Store(policy + native_law::kRealmLawCreatePrimaryTierTitlesOffset12004, std::uint8_t{1});
    Put(variable_context, 0x10, variable_row.data());
    Put(variable_context, 0x1C, scenario == 0U ? std::int32_t{0} : std::int32_t{1});
    Put(variable_context, 0x28, kClock);
    Put(variable_row, 8, kToken);
    constexpr std::array<std::int32_t, 6> expiry{0, 140, 100, 99, -1, 140};
    Put(variable_row, 0x0C, expiry[scenario]);
    read_failure = scenario == 5U;
  }
  static bool ReadMemory(void *opaque, std::uintptr_t address, void *out, std::size_t size) noexcept {
    auto &fixture = *static_cast<Fixture *>(opaque);
    ++fixture.law_memory_reads;
    fixture.arguments_valid &= GetCurrentThreadId() == fixture.owner_thread;
    if (address == kImage + native_law::kLawGroupDatabaseSingletonRva12004 && size == sizeof(kDatabase)) {
      std::memcpy(out, &kDatabase, size); return true;
    }
    const auto actor_address = reinterpret_cast<std::uintptr_t>(fixture.actor.data());
    if (address >= actor_address && size <= fixture.actor.size() &&
        address - actor_address <= fixture.actor.size() - size) {
      std::memcpy(out, fixture.actor.data() + address - actor_address, size); return true;
    }
    if (address < kBase || size > fixture.memory.size() || address - kBase > fixture.memory.size() - size)
      return false;
    if (size == native_law::kRealmLawSuccessionPolicyBytes12004) ++fixture.profile_reads;
    std::memcpy(out, fixture.memory.data() + address - kBase, size); return true;
  }
};
Fixture *active{};
void Record(bool valid) {
  active->arguments_valid &= valid && GetCurrentThreadId() == active->owner_thread;
}
void *Player(void *) { ++active->core_calls; Record(true); return active->player.data(); }
actual::CoreBindings Core(Fixture &fixture) {
  return {true, &fixture.state_ptr, &fixture.jomini_ptr, &fixture.characters_ptr, &Player};
}
std::size_t LawIndex(const void *law_pointer) {
  for (std::size_t index = 0; index < kLaws.size(); ++index)
    if (reinterpret_cast<std::uintptr_t>(law_pointer) == kLaws[index]) return index;
  Record(false); return kLaws.size();
}
bool Kind(const void *law_pointer) { return LawIndex(law_pointer) < kLaws.size(); }
bool Active(const void *actor, const void *law_pointer) {
  Record(actor == active->actor.data());
  const auto index = LawIndex(law_pointer); return index == 0U || index == 2U;
}
bool Final(const void *law_pointer, const void *actor, void *tooltip) {
  Record(LawIndex(law_pointer) == 1U && actor == active->actor.data() && tooltip == nullptr);
  return false;
}
std::int64_t *Cost(std::int64_t *out, const void *block, std::uint32_t actor_id) {
  const auto index = LawIndex(reinterpret_cast<const void *>(
      reinterpret_cast<std::uintptr_t>(block) - native_law::kRealmLawCompiledCostOffset12004));
  Record(actor_id == static_cast<std::uint32_t>(kActor));
  for (std::size_t slot = 0; slot < 10; ++slot)
    out[slot] = index == 1U ? static_cast<std::int64_t>(slot + 1U) * 300003 : 0;
  return out;
}
bool Reason(const void *law_pointer, const void *actor, void *out) {
  const auto index = LawIndex(law_pointer);
  Record(actor == active->actor.data());
  static constexpr char blocked[] = "Fixture existing native final denial";
  const char *text = index == 1U ? blocked : "";
  const std::uint64_t size = std::strlen(text), capacity = size > 15 ? size : 15;
  auto *sink = static_cast<std::byte *>(out);
  if (size > 15) std::memcpy(sink, &text, sizeof(text));
  std::memcpy(sink + 0x10, &size, sizeof(size));
  std::memcpy(sink + 0x18, &capacity, sizeof(capacity));
  return false;
}
void DestroyReason(void *) { Record(true); }
void *VariableTable() { Record(true); return active; }
std::int32_t *LookupVariable(void *table, std::int32_t *out, const law::PhaseStringView32 *key) {
  Record(table == active && key != nullptr && key->size == static_cast<std::int32_t>(active->variable_name.size()) &&
      std::string_view(key->data, static_cast<std::size_t>(key->size)) == active->variable_name);
  *out = kToken; return out;
}
const std::string *VariableName(void *table, std::int32_t token) {
  Record(table == active && token == kToken); return &active->variable_name;
}
void *VariableContext(const law::PhaseVariableTarget *target) {
  ++active->context_calls;
  Record(target != nullptr && target->kind == 4 &&
      target->payload == static_cast<std::int64_t>(kActor));
  return active->read_failure ? nullptr : active->variable_context.data();
}
raw::Bindings RawBindings() {
  raw::Bindings result{};
  result.identifiers.enabled = true;
  result.identifiers.variable_table = &VariableTable;
  result.identifiers.lookup_variable_identifier = &LookupVariable;
  result.identifiers.variable_identifier_name = &VariableName;
  result.identifiers.variable_context = &VariableContext;
  return result;
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
    mailbox.permitted_executor = &law::ExecuteRealmLawPausedPrivateQuery12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    mailbox.pump_epochs = kEpoch - 3;
    for (unsigned index = 0; index < 2; ++index)
      (void)api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    Check(mailbox.pump_epochs == kEpoch - 1, "real mailbox receives two synthetic owner warmups");
  }
  ~Pump() { tls_context = nullptr; }
};
void Emit(const std::filesystem::path &directory, const char *file, const std::string &wire) {
  std::ofstream output(directory / file, std::ios::binary);
  output << wire << '\n';
  Check(static_cast<bool>(output), "compiled production bytes written unchanged");
}

void Case(const std::filesystem::path &directory, std::size_t scenario) {
  Fixture fixture(scenario); active = &fixture;
  game::Ck3_12004AdapterBindings adapter_bindings{};
  adapter_bindings.core = Core(fixture);
  auto adapter = game::CreateCk3_12004AdapterFromBindings(std::move(adapter_bindings));
  Check(adapter && adapter->enabled() && game::IsCk3_12004Descriptor(adapter->descriptor()),
      "genuine actual4 adapter binds synthetic actual4 core memory");
  game::Snapshot frame{};
  Check(game::ReadCk3_12002TimelineCoreSnapshot(*adapter, frame) && frame.paused && frame.map_ready &&
      frame.played_character_id == kActor && frame.player_id == 7 && frame.date_raw == kDate,
      "genuine core reader selects the played owner/date");
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(fixture, mailbox);
  const law::private_law::RealmLawActiveCollectionAccess access{
      actual::kExecutableSha256, reinterpret_cast<std::uintptr_t>(fixture.actor.data()),
      &fixture, &Fixture::ReadMemory};
  const law::private_law::RealmLawFinalTerms12002Operations operations{
      {&Kind, &Active, &Final, &Cost}, &Reason, &DestroyReason};
  const auto cooldown_bindings = RawBindings();
  law::RealmLawReadbackQuery12002 query{};
  query.envelope.game = adapter.get(); query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = frame;
  query.envelope.expected_snapshot_revision = kNativeRevision;
  query.envelope.snapshot_comparison = law::QuerySnapshotComparison12002::core_frame;
  query.envelope.typed_context = &query;
  query.bindings = Core(fixture); query.module_base = kImage;
  query.actual_executable_sha256 = actual::kExecutableSha256;
  query.collection_access_override = &access;
  query.final_operations_override = &operations;
  query.cooldown_bindings_override = &cooldown_bindings;
  std::atomic<bool> done{false};
  auto submitted = api::MainThreadQuerySubmitResultV1::invalid_request;
  auto waited = api::MainThreadQueryWaitResultV1::ticket_mismatch;
  auto reclaimed = api::MainThreadQueryReclaimResultV1::ticket_mismatch;
  std::thread worker([&] {
    submitted = api::TrySubmitMainThreadQueryV1(mailbox,
        &law::ExecuteRealmLawPausedPrivateQuery12002, &query.envelope, query.envelope.ticket);
    if (submitted == api::MainThreadQuerySubmitResultV1::submitted) {
      waited = api::WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 5000);
      while (waited == api::MainThreadQueryWaitResultV1::timeout_executor_already_running)
        waited = api::WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 100);
      reclaimed = api::ReclaimMainThreadQueryV1(mailbox, query.envelope.ticket);
    }
    done.store(true, std::memory_order_release);
  });
  bool drained = false;
  while (!done.load(std::memory_order_acquire)) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Check(submitted == api::MainThreadQuerySubmitResultV1::submitted &&
      waited == api::MainThreadQueryWaitResultV1::completed &&
      reclaimed == api::MainThreadQueryReclaimResultV1::reclaimed && drained &&
      query.envelope.frame_stable && query.readback.available,
      "actual named mailbox executor captures and reclaims the complete readback");
  Check(query.envelope.execution_stamp.pump_epoch == kEpoch && query.envelope.ticket.sequence == 1 &&
      mailbox.executed_requests == 1 && mailbox.state == api::MainThreadQueryMailboxStateV1::idle &&
      fixture.arguments_valid && fixture.core_calls > 0U && fixture.law_memory_reads > 0U &&
      fixture.profile_reads == 1U && fixture.context_calls == 1U,
      "same owning frame captures genuine law and raw observer providers once");
  const auto &readback = query.readback;
  Check(readback.frame.snapshot_revision == kNativeRevision && readback.frame.date_raw == kDate &&
      readback.frame.actor_character_id == kActor && readback.collection.groups[0].candidate_count == 2 &&
      readback.collection.groups[1].candidate_count == 1 &&
      readback.final[0][1].terms.status == law::private_law::RealmLawFinalTerms12002Status::engine_blocked &&
      readback.final[0][1].terms.cost_raw[0] == 300003 &&
      readback.final[0][1].native_reason == "Fixture existing native final denial",
      "raw observation never overrides actual FinalCanEnact false/cost/reason");
  Check(readback.crown_authority_cooldown_observed, "actual4 capture includes raw observer even on read failure");
  const auto &value = readback.crown_authority_cooldown;
  Check(value.expiry_type == "signed32_scalar_clock_counter" &&
      value.remaining_unit == "scalar_clock_step_calendar_unqualified",
      "raw scalar is explicitly calendar unqualified");
  if (scenario == 0U) {
    Check(value.read_available && value.present == false && value.timed == false && !value.expiry_raw &&
        value.current_clock_raw == kClock && value.remaining_raw == -1 && value.retry_date_raw == kDate,
        "absent variable preserves absence and current-frame retry only");
  } else if (scenario == 5U) {
    Check(!value.read_available && !value.present && !value.timed && !value.expiry_raw &&
        !value.current_clock_raw && !value.remaining_raw && !value.retry_date_raw,
        "raw read failure remains null while complete legal collection survives");
  } else {
    constexpr std::array<std::int32_t, 4> expiry{140, 100, 99, -1};
    constexpr std::array<std::int32_t, 4> remaining{40, 0, -1, -1};
    Check(value.read_available && value.present == true && value.timed == (scenario != 4U) &&
        value.expiry_raw == expiry[scenario - 1U] && value.current_clock_raw == kClock &&
        value.remaining_raw == remaining[scenario - 1U] && !value.retry_date_raw,
        "signed scalar subtraction distinguishes computed-minus-one from untimed marker");
  }
  const auto body = law::SerializeRealmLawReadback12002(readback);
  auto wire = law::SerializeRealmLawReadbackCommandResult12002(kRequests[scenario], body, kNativeRevision);
  Check(!body.empty() && wire.find("\"realm_law_final_terms\":" + body) != std::string::npos &&
      wire.find(kRequests[scenario]) != std::string::npos &&
      wire.find("\"type\":\"command_result\"") != std::string::npos &&
      wire.find("\"crown_authority_cooldown\":") != std::string::npos,
      "actual full serializer wraps unchanged body and request identity");
  wire = game::Render12004BuildIdentity(std::move(wire), adapter->descriptor());
  Check(wire.find("\"snapshot_revision\":9") != std::string::npos &&
      wire.find("scalar_clock_step_calendar_unqualified") != std::string::npos &&
      wire.find("\"final_can_enact\":false") != std::string::npos,
      "actual4 rendered whole wire retains independent native final qualification");
  Emit(directory, kFiles[scenario], wire);
  active = nullptr;
}

void Receipt(const std::filesystem::path &directory) {
  std::ostringstream output;
  output << "{\"schema\":\"xar.ck3.crown-authority-cooldown-raw-native-whole-fixture12004/v1\","
      "\"status\":\"GREEN\",\"cases\":6,\"checks\":" << (checks + 1U) << ",\"whole_wire_files\":[";
  for (std::size_t index = 0; index < kFiles.size(); ++index) {
    if (index) output << ',';
    output << '"' << kFiles[index] << '"';
  }
  output << "],\"exact_build\":{\"game_version\":\"" << actual::kGameVersion
      << "\",\"executable_sha256\":\"" << actual::kExecutableSha256
      << "\",\"steam_build_id\":\"" << actual::kSteamBuildId
      << "\"},\"frame\":{\"public_revision\":" << kPublicRevision << ",\"native_revision\":" << kNativeRevision
      << ",\"date_raw\":" << kDate << ",\"actor_character_id\":" << kActor
      << ",\"player_id\":7,\"paused\":true,\"map_ready\":true},\"case_frames\":[";
  for (std::size_t index = 0; index < kFiles.size(); ++index) {
    if (index) output << ',';
    output << "{\"file\":\"" << kFiles[index] << "\",\"request_id\":\"" << kRequests[index]
        << "\",\"capture_epoch\":" << kEpoch << ",\"mailbox_sequence\":1,\"hello_file\":null,"
           "\"initial_state_file\":null,\"final_state_file\":null}";
  }
  output << "],\"state_packet_source\":\"fixture-synthetic-snapshot\","
      "\"provenance\":{\"native_memory\":\"fixture-synthetic\",\"native_callbacks\":\"fixture-synthetic\","
      "\"source_frame\":\"fixture-synthetic\",\"public_revision\":\"fixture-synthetic\","
      "\"capture_epoch\":\"fixture-synthetic\",\"whole_wires\":\"compiled-production-serializer\","
      "\"whole_wire_rows_repaired\":false,\"live\":false},\"pipeline\":{\"actual_adapter\":true,\"actual_core_reader\":true,"
      "\"actual_named_mailbox_executor\":true,\"actual_law_capture\":true,\"actual4_law_provider\":true,"
      "\"actual_raw_cooldown_reader\":true,\"actual_full_serializer\":true,\"actual4_renderer\":true,"
      "\"default_image_bindings_used\":false,\"production_stubs\":false,\"legacy_main_executed\":false},"
      "\"raw_unit\":\"scalar_clock_step_calendar_unqualified\",\"calendar_ready\":false,\"live\":false,"
      "\"old_cases_executed\":0,\"law_action_calls\":0}";
  Emit(directory, "fixture-receipt.json", output.str());
}
} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "usage: fixture <fresh M7 whole-wire output directory>");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    for (std::size_t scenario = 0; scenario < kFiles.size(); ++scenario) Case(directory, scenario);
    Receipt(directory);
    std::cout << "PASS new_raw_cooldown_cases=6 old_cases=0 live=false checks=" << checks << '\n';
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
