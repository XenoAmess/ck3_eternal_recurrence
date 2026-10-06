// AUTHORED_NOTRUN. Six new actual4 whole packets from the production parser,
// named owning mailbox, actual4 Core/Clergy readers, serializer and renderer.
// Engine memory/callbacks/frame are synthetic; no production function is stubbed.
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_clergy_appointment.hpp"
#include "xar_bridge/religion_rite_governance12002_clergy_mailbox.hpp"
#include "xar_bridge/ck3_12002_council_candidates.hpp"

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
namespace game = xar::game;
namespace api = xar::ck3_11906;
constexpr std::int32_t kOwner = 29829;
constexpr std::int32_t kCandidate = 16777232;
constexpr std::int32_t kIncumbent = 56513;
constexpr std::int32_t kTask = 7162;
constexpr std::int32_t kDate = 53288256;
constexpr std::uint64_t kPublicRevision = 2;
constexpr std::uint64_t kNativeRevision = 11;
constexpr std::uint64_t kEpoch = 1007;
constexpr std::array<const char *, 6> kFiles{
    "occupied-reassign-true-fire-false.json", "occupied-reassign-false-fire-true.json",
    "vacant-fire-null.json", "absent-position.json", "candidate-unavailable.json",
    "bindings-unavailable.json"};
constexpr std::array<const char *, 6> kRequests{
    "g2-read-00000000000000000000000000004401", "g2-read-00000000000000000000000000004402",
    "g2-read-00000000000000000000000000004403", "g2-read-00000000000000000000000000004404",
    "g2-read-00000000000000000000000000004405", "g2-read-00000000000000000000000000004406"};
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
  Bytes<0x1D8> owner{}, candidate{}, incumbent{};
  Bytes<0x240> landed{};
  Bytes<0x50> task{}, type{};
  Bytes<0x60> position{};
  std::array<std::int32_t, 1> task_ids{kTask};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *characters_ptr = character_storage.data(), *tasks_ptr = task_storage.data();
  unsigned core_calls{}, predicate_calls{}, fire_calls{};
  bool reassign = true, fire = false, arguments_valid = true;
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
  active->arguments_valid &= candidate == active->candidate.data() &&
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
  active->arguments_valid &= position == active->position.data() && candidate == kCandidate;
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

void Case(const std::filesystem::path &directory, std::size_t scenario) {
  Fixture fixture; active = &fixture;
  if (scenario == 1U) { fixture.reassign = false; fixture.fire = true; }
  if (scenario == 2U) Put(fixture.task, clergy::kTaskIncumbentOffset, std::int32_t{-1});
  if (scenario == 3U) Put(fixture.landed, clergy::kTaskCountOffset, std::int32_t{0});
  if (scenario == 4U) Put(fixture.character_slots, 16U * 0x10U + 8U, static_cast<void *>(nullptr));
  game::Ck3_12004AdapterBindings adapter_bindings{};
  adapter_bindings.core = Core(fixture);
  auto adapter = game::CreateCk3_12004AdapterFromBindings(std::move(adapter_bindings));
  Check(adapter && adapter->enabled() && game::IsCk3_12004Descriptor(adapter->descriptor()),
      "genuine production actual4 adapter with synthetic actual4 core inputs");
  game::Snapshot frame{};
  Check(game::ReadCk3_12002TimelineCoreSnapshot(*adapter, frame) && frame.paused && frame.map_ready &&
      frame.played_character_id == kOwner && frame.player_id == 7 && frame.date_raw == kDate,
      "genuine actual4 core selector publishes only the supported owner frame");
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(fixture, mailbox);
  old::PlayerClergyAppointmentMailboxContext12002 query{};
  const std::string payload = "{\"candidate_character_id\":" + std::to_string(kCandidate) +
      ",\"expected_snapshot_revision\":" + std::to_string(kNativeRevision) +
      ",\"expected_revision\":" + std::to_string(kNativeRevision) +
      ",\"expected_public_revision\":" + std::to_string(kPublicRevision) + "}";
  Check(old::ParsePlayerClergyAppointmentRequest12002(payload, query.request) &&
      query.request.candidate_character_id == kCandidate && query.request.expected_revision == kNativeRevision &&
      query.request.expected_public_revision == kPublicRevision, "actual unchanged clergy request parser");
  query.envelope.game = adapter.get(); query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = frame; query.envelope.expected_snapshot_revision = kNativeRevision;
  query.bindings12004 = Bind(fixture);
  if (scenario == 5U) query.bindings12004->enabled = false;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
  std::string wire, failure;
  std::thread worker([&] {
    result = old::RunPlayerClergyAppointmentMailbox12002(query, kRequests[scenario], wire, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Check(result && drained && failure.empty() && query.completed && query.envelope.frame_stable,
      "actual named owning mailbox executes complete clergy producer");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle && mailbox.executed_requests == 1 &&
      query.envelope.execution_stamp.pump_epoch == kEpoch &&
      query.envelope.snapshot_comparison == old::QuerySnapshotComparison12002::core_frame &&
      query.bindings12004->application_main_thread_id == GetCurrentThreadId(),
      "actual4 core-frame ticket drains once and is reclaimed on actual owner");
  const auto &value = query.observation;
  Check(value.capture_epoch == kEpoch && value.owner_character_id == kOwner &&
      value.date_raw == kDate && value.candidate_character_id == kCandidate && fixture.arguments_valid && fixture.core_calls > 0U,
      "existing whole mailbox binds actual owner/date even for early unavailable reader");
  if (scenario < 2U) {
    Check(value.available && value.native_valid_position == true && value.native_valid_character == true &&
        value.native_can_reassign == fixture.reassign && value.native_can_fire == fixture.fire &&
        value.incumbent_character_id == kIncumbent && value.active_task_id == kTask &&
        fixture.predicate_calls == 3U && fixture.fire_calls == 1U,
        "independent native true/false uses actual incumbent and requested full candidate");
  } else if (scenario == 2U) {
    Check(value.available && value.position_present && !value.incumbent_character_id && !value.native_can_fire &&
        value.native_can_reassign == true && fixture.fire_calls == 0U, "vacancy has null CanFire and no fire call");
  } else if (scenario == 3U) {
    Check(value.available && !value.position_present && !value.active_task_id && !value.native_valid_position &&
        !value.native_valid_character && !value.native_can_reassign && !value.native_can_fire &&
        fixture.predicate_calls == 0U && fixture.fire_calls == 0U, "legal absent position preserves null terms");
  } else {
    Check(!value.available && value.failure == (scenario == 4U ? clergy::Failure::candidate_unavailable : clergy::Failure::bindings_unavailable) &&
        !value.native_valid_position && !value.native_valid_character && !value.native_can_reassign && !value.native_can_fire &&
        fixture.predicate_calls == 0U && fixture.fire_calls == 0U, "typed unavailable retains null native predicates");
  }
  Check(!query.candidate_terms_environment && !query.candidate_terms_observation &&
      !query.county_conversion_environment && !query.county_conversion_environment12004 && !query.county_conversion_observation,
      "base migration fixture does not fabricate independent optional siblings");
  const auto body = clergy::SerializeClergyAppointment12004(value);
  Check(wire.find("\"player_clergy_appointment\":" + body) != std::string::npos,
      "whole production serializer retains exact actual4 reader body");
  wire = game::Render12004BuildIdentity(std::move(wire), adapter->descriptor());
  Check(wire.find(actual::kExecutableSha256) != std::string::npos &&
      wire.find("\"game_version\":\"1.20.0.4\"") != std::string::npos &&
      wire.find("ck3-1.20.0.4-native-player-clergy-appointment-v1") != std::string::npos &&
      wire.find("\"snapshot_revision\":11") != std::string::npos &&
      wire.find("\"action_eligibility_complete\":false") != std::string::npos &&
      wire.find("\"candidate_terms\"") == std::string::npos,
      "genuine production actual4 renderer retains exact whole identity without new candidate capability");
  Emit(directory, kFiles[scenario], wire);
  active = nullptr;
}
void Receipt(const std::filesystem::path &directory) {
  const auto chaplain = old::CouncilCandidatesProfile12002(old::kCouncilCandidatesChaplainPosition12002);
  Check(chaplain.position_key.empty() &&
      !old::CouncilCandidatesProfile12002(old::kCouncilCandidatesStewardPosition12002).position_key.empty() &&
      !old::CouncilCandidatesProfile12002(old::kCouncilCandidatesChancellorPosition12002).position_key.empty() &&
      !old::CouncilCandidatesProfile12002(old::kCouncilCandidatesSpymasterPosition12002).position_key.empty(),
      "original three-seat software assignment profile remains unchanged");
  std::ostringstream output;
  output << "{\"schema\":\"xar.ck3.clergy-appointment-12004-native-whole-fixture/v1\",\"status\":\"GREEN\",\"cases\":6,\"checks\":" << (checks + 1U)
      << ",\"whole_wire_files\":[";
  for (std::size_t index = 0; index < kFiles.size(); ++index) {
    if (index) output << ',';
    output << '\"' << kFiles[index] << '\"';
  }
  output << "],\"exact_build\":{\"game_version\":\"1.20.0.4\",\"executable_sha256\":\"" << actual::kExecutableSha256
      << "\"},\"frame\":{\"public_revision\":2,\"native_revision\":11,\"capture_epoch\":1007,\"date_raw\":53288256,"
         "\"owner_character_id\":29829,\"active_task_id\":7162,\"incumbent_character_id\":56513,\"candidate_character_id\":16777232,\"paused\":true,\"map_ready\":true},"
         "\"provenance\":{\"native_memory\":\"fixture-synthetic\",\"native_callbacks\":\"fixture-synthetic\",\"source_frame\":\"fixture-synthetic\","
         "\"public_revision\":\"fixture-synthetic\",\"capture_epoch\":\"fixture-synthetic\",\"whole_wires\":\"compiled-production-serializer\",\"whole_wire_rows_repaired\":false},"
         "\"original_action_profile\":{\"positions\":[\"councillor_steward\",\"councillor_chancellor\",\"councillor_spymaster\"],"
         "\"chaplain_assignment_supported\":false,\"action_eligibility_complete\":false},"
         "\"pipeline\":{\"actual_adapter\":true,\"actual_core_reader\":true,\"actual_request_parser\":true,\"actual_named_mailbox\":true,"
         "\"actual_clergy_reader\":true,\"actual_full_serializer\":true,\"actual_actual4_renderer\":true,\"offline_native_image_handler_invoked\":false,"
         "\"production_stubs\":false,\"legacy_main_executed\":false,\"live\":false}}";
  Emit(directory, "native-whole-receipt.json", output.str());
}
} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "one fresh whole-wire output directory argument");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    for (std::size_t index = 0; index < kFiles.size(); ++index) Case(directory, index);
    Receipt(directory);
    std::cout << "PASS actual4_clergy_cases=6 checks=" << checks << " genuine_whole_serializer=true live=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
