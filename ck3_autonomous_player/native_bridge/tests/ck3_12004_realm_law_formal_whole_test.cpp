// Offline synthetic native memory and native-call substitutions exercise the
// production actual4 source factories, mailbox, LAW4/LAW5 binder and wire.
// This fixture does not load CK3 and makes no claim about loaded CanEnact.
#if defined(NDEBUG)
#undef NDEBUG
#endif

#include "xar_bridge/ck3_12004_realm_law_action_mailbox.hpp"
#include "xar_bridge/ck3_12004_realm_law_enact_command_v1.hpp"

#include <algorithm>
#include <array>
#include <atomic>
#include <cassert>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <memory>
#include <string>
#include <string_view>
#include <tuple>
#include <thread>
#include <vector>
#include <windows.h>

namespace {
namespace game = xar::game;
namespace bridge = xar::bridge;
namespace actual4 = xar::ck3_12004;
namespace law = xar::ck3_12004::private_law;

constexpr std::uintptr_t kBase = 0x140000000ULL;
constexpr std::uintptr_t kActor = 0x71000000, kLand = 0x71100000,
    kResource = 0x71200000, kPrimary = 0x71300000,
    kSecondary = 0x71400000, kCharacterStorage = 0x71500000,
    kCharacterSlots = 0x71600000, kTitleStorage = 0x71700000,
    kTitleSlots = 0x71800000, kLawDatabase = 0x71900000,
    kCrown = 0x71A00000, kSuccession = 0x71B00000;
constexpr std::int32_t kActorId = 29'829, kFirstId = 201, kSecondId = 301,
    kPrimaryId = 101, kSecondaryId = 102;
constexpr std::int64_t kDate = 53'169'072;
constexpr std::int64_t kInfluenceRaw = 11'000'000, kMeritRaw = 13'000'000;
constexpr std::string_view kActionId = "formal-crown-12004";

// Actual4 sealed USED fields: FIELD07/FIELD12 source receipts. The native
// registry locators are explicit .4 evidence, rather than old-image aliases.
constexpr std::uintptr_t kTitleStorageRva12004 = 0x5D1DAF8;
constexpr std::uintptr_t kTitleFallbackRva12004 = 0x5D1DAE0;

struct Fixture;
Fixture *current = nullptr;

struct Fixture {
  std::map<std::uintptr_t, std::vector<unsigned char>> blocks;
  std::map<std::uintptr_t, std::size_t> law_indices;
  std::uintptr_t allocation = 0x73000000;
  std::uintptr_t active_slots = 0;
  std::uintptr_t selected_law = 0;
  std::size_t validated = 0, cloned = 0, queued = 0;

  void Add(std::uintptr_t address, std::size_t size) {
    blocks[address].resize(size);
  }

  template <typename T> void Put(std::uintptr_t address, T value) {
    auto it = blocks.upper_bound(address);
    assert(it != blocks.begin());
    --it;
    const auto offset = address - it->first;
    assert(offset + sizeof(value) <= it->second.size());
    std::memcpy(it->second.data() + offset, &value, sizeof(value));
  }

  std::uintptr_t Allocate(std::size_t size) {
    const auto address = allocation;
    allocation += 0x10000;
    Add(address, size);
    return address;
  }

  void NativeKey(std::uintptr_t address, std::string_view key) {
    Put(address + 0x10, static_cast<std::uint64_t>(key.size()));
    Put(address + 0x18, static_cast<std::uint64_t>(
        key.size() <= 15 ? 15 : key.size()));
    const auto bytes = key.size() <= 15 ? address : Allocate(key.size() + 1);
    if (key.size() > 15) Put(address, bytes);
    for (std::size_t i = 0; i < key.size(); ++i) Put(bytes + i, key[i]);
  }

  static bool Memory(void *opaque, std::uintptr_t address, void *out,
                     std::size_t size) noexcept {
    auto &fixture = *static_cast<Fixture *>(opaque);
    auto it = fixture.blocks.upper_bound(address);
    if (it == fixture.blocks.begin()) return false;
    --it;
    const auto offset = address - it->first;
    if (offset + size > it->second.size()) return false;
    std::memcpy(out, it->second.data() + offset, size);
    return true;
  }

  static void *Primary(void *character) {
    assert(character == reinterpret_cast<void *>(kActor));
    return reinterpret_cast<void *>(kPrimary);
  }
  static bool Kind(const void *) { return true; }
  static bool Active(const void *, const void *definition) {
    const auto address = reinterpret_cast<std::uintptr_t>(definition);
    std::uintptr_t effective = 0;
    assert(Memory(current, current->active_slots, &effective, sizeof(effective)));
    return address == effective || current->law_indices.at(address) == 4;
  }
  static bool Final(const void *, const void *, void *) { return true; }
  static std::int64_t *Cost(std::int64_t *out, const void *block,
                            std::uint32_t actor_id) {
    assert(actor_id == static_cast<std::uint32_t>(kActorId));
    std::fill_n(out, 10, std::int64_t{0});
    const auto index = current->law_indices.at(
        reinterpret_cast<std::uintptr_t>(block) -
        law::kRealmLawCompiledCostOffset12004);
    if (index > 0 && index < 4) out[1] = 20'000'000;
    return out;
  }
  static bool Reason(const void *definition, const void *, void *sink) {
    const bool active = Active(nullptr, definition);
    const std::string_view reason = active ? "already_active" : "";
    const auto size = static_cast<std::uint64_t>(reason.size());
    std::memcpy(sink, reason.data(), reason.size());
    std::memcpy(static_cast<char *>(sink) + 0x10, &size, sizeof(size));
    return !active;
  }
  static void DestroyReason(void *) {}
  static void *Scope(void *out, const void *actor) {
    assert(actor == reinterpret_cast<const void *>(kActor));
    return out;
  }
  static bool Component(const void *, const void *) { return true; }
  static void DestroyScope(void *) {}

  template <typename T>
  static T CommandField(const law::AddLawCommandV1 &command,
                        std::size_t offset) {
    T value{};
    std::memcpy(&value, command.bytes.data() + offset, sizeof(value));
    return value;
  }
  static void CheckCommand(const law::AddLawCommandV1 &command) {
    assert(CommandField<std::uintptr_t>(command, 0) ==
           kBase + law::kAddLawCommandPrimaryVtableRva12004V1);
    assert(CommandField<std::uintptr_t>(command, 0x18) ==
           kBase + law::kAddLawCommandSecondaryVtableRva12004V1);
    assert(CommandField<std::int32_t>(command, 0x20) == kActorId);
    assert(CommandField<std::uintptr_t>(command, 0x28) == current->selected_law);
  }
  static bool Validate(void *opaque, const law::AddLawCommandV1 &command) noexcept {
    CheckCommand(command);
    ++static_cast<Fixture *>(opaque)->validated;
    return true;
  }
  static bool Clone(void *opaque, const law::AddLawCommandV1 &command,
                    void *&out) noexcept {
    CheckCommand(command);
    ++static_cast<Fixture *>(opaque)->cloned;
    out = new law::AddLawCommandV1(command);
    return true;
  }
  static bool Queue(void *opaque, std::uintptr_t manager, void *&owned,
                    std::uint32_t flags) noexcept {
    assert(manager == kBase + law::kCommandManagerRva12004V1);
    assert(flags == law::kAddLawCommandSubmitFlags12004V1);
    assert(owned != nullptr);
    CheckCommand(*static_cast<law::AddLawCommandV1 *>(owned));
    ++static_cast<Fixture *>(opaque)->queued;
    delete static_cast<law::AddLawCommandV1 *>(owned);
    owned = nullptr;
    return true;
  }
  static void DestroyCommand(void *, void *owned) noexcept {
    delete static_cast<law::AddLawCommandV1 *>(owned);
  }

  Fixture() {
    current = this;
    for (const auto [address, size] :
         std::vector<std::pair<std::uintptr_t, std::size_t>>{
             {kActor, 0x300}, {kLand, 0x300}, {kResource, 0x300},
             {kPrimary, 0x400}, {kSecondary, 0x400},
             {kCharacterStorage, 0x40}, {kCharacterSlots, 32768 * 16},
             {kTitleStorage, 0x40}, {kTitleSlots, 128 * 16},
             {kLawDatabase, 0x80}, {kCrown, 0x100}, {kSuccession, 0x100}})
      Add(address, size);
    const auto global = [&](std::uintptr_t rva, std::uintptr_t value) {
      Add(kBase + rva, sizeof(value));
      Put(kBase + rva, value);
    };
    global(actual4::kCharacterStorageSlotRva, kCharacterStorage);
    global(actual4::kCrownCharacterFallbackSlotRva12004, 0);
    global(kTitleStorageRva12004, kTitleStorage);
    global(kTitleFallbackRva12004, 0);
    global(law::kLawGroupDatabaseSingletonRva12004, kLawDatabase);

    Put(kActor + actual4::kCharacterFullIdOffset, kActorId);
    Put(kActor + law::kCharacterLawContextOffset12004, kLand);
    Put(kActor + 0x1B0, kResource);
    Put(kResource + 0x100, std::int64_t{8'000'000});
    Put(kResource + 0x110, std::int64_t{7'000'000});
    Put(kResource + 0x130, std::int64_t{50'000'000});
    Put(kResource + actual4::kCrownResourceBalanceOffsets12004[3], kInfluenceRaw);
    Put(kResource + actual4::kCrownResourceBalanceOffsets12004[4], kMeritRaw);

    Put(kCharacterStorage + actual4::kCharacterStorageSlotsOffset,
        kCharacterSlots);
    Put(kCharacterStorage + actual4::kCharacterStorageCapacityOffset,
        std::int32_t{32768});
    const auto character_slot = [&](std::int32_t id, std::uintptr_t address) {
      Put(kCharacterSlots + static_cast<std::uintptr_t>(id) *
          actual4::kCharacterStorageSlotStride +
          actual4::kCharacterStorageObjectOffset, address);
    };
    character_slot(kActorId, kActor);
    for (const auto id : {kFirstId, kSecondId}) {
      const auto character = Allocate(0x30);
      Put(character + actual4::kCharacterFullIdOffset, id);
      character_slot(id, character);
    }

    Put(kTitleStorage + 0x20, kTitleSlots);
    Put(kTitleStorage + 0x2C, std::int32_t{128});
    Put(kTitleSlots + kPrimaryId * 16 + 8, kPrimary);
    Put(kTitleSlots + kSecondaryId * 16 + 8, kSecondary);
    const auto held = Allocate(8);
    Put(held, kPrimaryId);
    Put(held + 4, kSecondaryId);
    Put(kLand + 0x1E0, held);
    Put(kLand + 0x1E8, std::int32_t{2});
    Put(kLand + 0x1EC, std::int32_t{2});
    const auto primary_successors = Allocate(8);
    Put(primary_successors, kFirstId);
    Put(primary_successors + 4, kSecondId);
    const auto secondary_successors = Allocate(8);
    Put(secondary_successors, kSecondId);
    Put(secondary_successors + 4, kFirstId);
    for (const auto [title, id, successors] :
         std::vector<std::tuple<std::uintptr_t, std::int32_t, std::uintptr_t>>{
             {kPrimary, kPrimaryId, primary_successors},
             {kSecondary, kSecondaryId, secondary_successors}}) {
      Put(title + 0x10, id);
      Put(title + 0x128, kActorId);
      Put(title + 0x150, successors);
      Put(title + 0x158, std::int32_t{2});
      Put(title + 0x15C, std::int32_t{2});
    }

    NativeKey(kCrown + law::kLawNativeKeyOffset12004, "crown_authority");
    NativeKey(kSuccession + law::kLawNativeKeyOffset12004,
              "succession_order_laws");
    const auto groups = Allocate(16);
    Put(groups, kCrown);
    Put(groups + 8, kSuccession);
    Put(kLawDatabase + law::kLawGroupDatabaseArrayOffset12004, groups);
    Put(kLawDatabase + law::kLawGroupDatabaseCountOffset12004, std::int32_t{2});
    const auto crown_candidates = Allocate(32);
    const auto succession_candidates = Allocate(32);
    Put(kCrown + law::kLawGroupCandidateArrayOffset12004, crown_candidates);
    Put(kCrown + law::kLawGroupCandidateCountOffset12004, std::int32_t{4});
    Put(kSuccession + law::kLawGroupCandidateArrayOffset12004,
        succession_candidates);
    Put(kSuccession + law::kLawGroupCandidateCountOffset12004, std::int32_t{4});
    constexpr std::array<std::string_view, 8> keys{
        "crown_authority_0", "crown_authority_1", "crown_authority_2",
        "crown_authority_3", "confederate_partition_succession_law",
        "partition_succession_law", "high_partition_succession_law",
        "single_heir_succession_law"};
    std::array<std::uintptr_t, keys.size()> definitions{};
    for (std::size_t i = 0; i < keys.size(); ++i) {
      const auto definition = Allocate(0xD00);
      definitions[i] = definition;
      law_indices[definition] = i;
      NativeKey(definition + law::kLawNativeKeyOffset12004, keys[i]);
      if (i < 4) {
        // Actual4 enum sentinels represent the unchanged absent succession
        // policy on every Crown level; the full title baseline is independent.
        Put(definition + law::kRealmLawSuccessionPolicyOffset12004,
            std::uint8_t{9});
        Put(definition + law::kRealmLawSuccessionPolicyOffset12004 + 1,
            std::uint8_t{3});
        Put(definition + law::kRealmLawSuccessionPolicyOffset12004 + 3,
            std::uint8_t{2});
        Put(definition + law::kRealmLawSuccessionPolicyOffset12004 + 4,
            std::uint8_t{2});
      }
      Put(definition + law::kLawOwningGroupOffset12004,
          i < 4 ? kCrown : kSuccession);
      Put((i < 4 ? crown_candidates : succession_candidates) + (i % 4) * 8,
          definition);
    }
    selected_law = definitions[1];
    active_slots = Allocate(16);
    Put(active_slots, definitions[0]);
    Put(active_slots + 8, definitions[4]);
    Put(kLand + law::kLawCollectionOffset12004, active_slots);
    Put(kLand + law::kLawCollectionOffset12004 + 8, std::int32_t{2});
    Put(kLand + law::kLawCollectionOffset12004 + 12, std::int32_t{2});
  }
};

class RouterAdapter final : public game::GameAdapter {
public:
  game::Snapshot snapshot{};
  RouterAdapter() {
    snapshot.date_raw = kDate;
    snapshot.paused = snapshot.map_ready = snapshot.has_played_character =
        snapshot.played_character_alive = true;
    snapshot.played_character_id = kActorId;
  }
  const game::AdapterDescriptor &descriptor() const noexcept override {
    static const game::AdapterDescriptor descriptor{
        actual4::kAdapterId, actual4::kGameVersion, actual4::kExecutableSha256,
        "fixture", {}};
    return descriptor;
  }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    out = snapshot;
    return true;
  }
#define XAR4_R0(T, M) game::T M() const noexcept override { return {}; }
#define XAR4_R1(T, M, A) game::T M(A) const noexcept override { return {}; }
#define XAR4_R2(T, M, A, B) game::T M(A, B) const noexcept override { return {}; }
  XAR4_R1(PauseSubmitResult, submit_pause_map, game::Snapshot *)
  XAR4_R1(ResumeSubmitResult, submit_resume_map, game::Snapshot *)
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  XAR4_R1(SelectEventOptionResult, submit_select_event_option, std::int32_t)
  XAR4_R0(SaveCheckpointResult, submit_save_checkpoint)
  XAR4_R1(ReplyPendingInteractionResult, submit_reply_to_pending_interaction,
          game::PendingInteractionReply)
  XAR4_R0(RaiseTroopsResult, submit_raise_troops_default)
  XAR4_R2(MoveArmyResult, submit_move_army, std::int32_t, std::int32_t)
  XAR4_R2(PreviewMoveArmyResult, preview_move_army, std::int32_t, std::int32_t)
  XAR4_R1(DisbandArmyResult, submit_disband_army, std::int32_t)
  XAR4_R1(SplitArmyHalfResult, submit_split_army_half, std::int32_t)
  XAR4_R2(MergeArmiesResult, submit_merge_armies, std::int32_t, std::int32_t)
  XAR4_R1(StartAssaultResult, submit_start_assault, std::int32_t)
  XAR4_R1(StopAssaultResult, submit_stop_assault, std::int32_t)
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &)
      const noexcept override { return false; }
  XAR4_R2(ReadDeclarableWarsResult, read_declarable_wars_for_target, std::int32_t,
          std::vector<game::DeclarableWarSnapshot> &)
  XAR4_R2(ReadArrangeMarriageChoicesResult, read_arrange_marriage_choices,
          std::vector<game::ArrangeMarriageChoice> &,
          game::ArrangeMarriageQueryDiagnostics &)
  XAR4_R1(DeclareWarResult, submit_declare_war, const game::DeclarableWarSnapshot &)
  XAR4_R1(ArrangeMarriageResult, submit_arrange_marriage,
          const game::ArrangeMarriageChoice &)
  XAR4_R1(EnforceDemandsResult, submit_enforce_demands, std::int32_t)
  XAR4_R1(ReadArmyStrengthsResult, read_army_strengths,
          std::vector<game::ArmyStrengthSnapshot> &)
  XAR4_R2(ReadCombatSimulationInputsResult, read_combat_simulation_inputs,
          const game::CombatSimulationInputsRequest &,
          game::CombatSimulationInputsSnapshot &)
  XAR4_R2(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3,
          const game::CombatSimulationInputsRequest &,
          game::CombatSimulationInputsV3Snapshot &)
  XAR4_R2(ReadWarTerminationOptionsResult, read_war_termination_options,
          std::int32_t, game::WarTerminationOptionsSnapshot &)
  XAR4_R2(ReadWarTerminationTermsResult, read_war_termination_terms,
          std::int32_t, game::WarTerminationTermsSnapshot &)
  XAR4_R2(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms,
          std::int32_t, game::WarTerminationExitTermsSnapshot &)
  XAR4_R1(SurrenderWarResult, submit_surrender_war, std::int32_t)
  XAR4_R1(OfferWhitePeaceResult, submit_offer_white_peace, std::int32_t)
#undef XAR4_R0
#undef XAR4_R1
#undef XAR4_R2
};

std::string Payload(std::uint64_t revision) {
  return "{\"expected_revision\":" + std::to_string(revision) +
      ",\"expected_date_raw\":" + std::to_string(kDate) +
      ",\"expected_player_character_id\":" + std::to_string(kActorId);
}

void Write(const std::filesystem::path &directory, std::string_view name,
           const std::string &wire) {
  if (directory.empty()) return;
  std::ofstream output(directory / std::string(name), std::ios::binary);
  output << wire << '\n';
  assert(output.good());
}

void CheckEnvelope(const std::string &wire, std::string_view request_id) {
  assert(wire.starts_with("{\"type\":\"command_result\",\"protocol_version\":1,"));
  assert(wire.find("\"request_id\":\"" + std::string(request_id) + "\"") !=
         std::string::npos);
  assert(wire.find("\"ok\":true") != std::string::npos);
  assert(wire.find("\"game_version\":\"1.20.0.4\"") != std::string::npos);
  assert(wire.find("\"executable_sha256\":\"" +
      std::string(actual4::kExecutableSha256) + "\"") != std::string::npos);
  assert(wire.find("\"backend_id\":\"native-headless\"") != std::string::npos);
  assert(wire.find("\"accepted\":true,\"private_build\":true,\"advertised\":false") !=
         std::string::npos);
}

void CheckActual4SourceFactory(const actual4::RealmLawActionMailboxState12004 &state) {
  const auto expected = actual4::MakeRealmLawCrownSourceOperations12004();
  const auto &actual = state.binder.operations;
  assert(state.binder.attached && state.binder.offline_fixture);
  assert(state.binder.native_context == &state.source);
  assert(state.source.admitted_executable_sha256 == actual4::kExecutableSha256);
  assert(std::string_view(state.binder.executable_sha256.data()) ==
         actual4::kExecutableSha256);
  assert(std::string_view(state.binder.signature_manifest_sha256.data()) ==
         law::kRealmLawEnactMutationManifestSha25612004V1);
  assert(actual.read_runtime_proof == expected.read_runtime_proof);
  assert(actual.capture_frame == expected.capture_frame);
  assert(actual.resolve_player == expected.resolve_player);
  assert(actual.resolve_container == expected.resolve_container);
  assert(actual.read_group == expected.read_group);
  assert(actual.read_candidate == expected.read_candidate);
  assert(actual.read_title_baseline == expected.read_title_baseline);
  assert(actual.read_resources == expected.read_resources);
  assert(actual.submit_enact == expected.submit_enact);
}

void *tls_context = nullptr;
void *__fastcall FixtureTls() noexcept { return tls_context; }

// Reuse the existing deterministic pump surface used by the qualified raw
// Crown fixture. Inputs are synthetic; TrySubmit/Wait/Reclaim and the owner
// drain are the complete production definitions from the full Bridge link.
struct Pump {
  std::array<std::byte, 0x28> tls{}, jomini{};
  std::array<std::byte, 0x10> game_state{};
  void *jomini_pointer = jomini.data(), *game_state_pointer = game_state.data();
  std::uint8_t initialized = 1;
  std::uintptr_t unused_rng = 0;

  explicit Pump(xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox) {
    namespace api = xar::ck3_11906;
    tls[api::kMainThreadTlsMarkerOffset] = std::byte{1};
    jomini[api::kJominiPausedOffset] = std::byte{1};
    const auto date = static_cast<std::int32_t>(kDate);
    std::memcpy(game_state.data() + api::kGameStateDateRawOffset, &date, sizeof(date));
    tls_context = tls.data();
    mailbox.global_rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&unused_rng);
    mailbox.jomini_state_slot = reinterpret_cast<std::uintptr_t>(&jomini_pointer);
    mailbox.game_state_slot = reinterpret_cast<std::uintptr_t>(&game_state_pointer);
    mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter = &FixtureTls;
    mailbox.executor_submission_enabled = true;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2U; ++i)
      (void)api::ObserveMainThreadPumpAndDrainV1(
          mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    assert(mailbox.paused_owner_verified_pump_epochs.load(std::memory_order_acquire) >= 2U);
    assert(mailbox.owner_thread_id.load(std::memory_order_acquire) == GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};
} // namespace

int main(int argc, char **argv) {
  assert(argc <= 2);
  const std::filesystem::path output = argc == 2 ? argv[1] : "";
  if (!output.empty()) std::filesystem::create_directories(output);
  Fixture fixture;
  RouterAdapter adapter;
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  mailbox.offline_fixture = true;
  mailbox.permitted_executor_septentrigintary =
      &actual4::ExecuteRealmLawPrivateAction12004;
  Pump pump(mailbox);
  law::AddLawCommandOfflineCallsV1 calls{
      &fixture, Fixture::Validate, Fixture::Clone, Fixture::Queue,
      Fixture::DestroyCommand};
  actual4::RealmLawActionMailboxFixture12004 bindings{};
  bindings.module_base = kBase;
  bindings.context = &fixture;
  bindings.read_memory = Fixture::Memory;
  bindings.final_operations = {
      {Fixture::Kind, Fixture::Active, Fixture::Final, Fixture::Cost},
      Fixture::Reason, Fixture::DestroyReason};
  bindings.component_operations = {
      true, Fixture::Scope, Fixture::Component, Fixture::DestroyScope,
      Fixture::DestroyScope};
  bindings.primary_title = Fixture::Primary;
  bindings.command_access.module_base = kBase;
  bindings.command_access.submit_enabled = true;
  bindings.command_access.offline_calls = &calls;
  auto &proof = bindings.command_access.mutation_abi_proof;
  // Signature admission is an explicit offline substitution. Actual native
  // bytes were source-mapped separately; this fixture does not read a game
  // image or execute its validator, clone, queue or trigger callbacks.
  proof.verified = true;
  proof.failure = law::RealmLawMutationAbiFailureV1::none;
  proof.failed_evidence = nullptr;
  proof.contract = law::kRealmLawEnactMutationAbi12004V1;
  proof.build = actual4::kGameVersion;
  proof.executable_sha256 = actual4::kExecutableSha256;
  proof.manifest_sha256 = law::kRealmLawEnactMutationManifestSha25612004V1;

  auto state = std::make_unique<actual4::RealmLawActionMailboxState12004>();
  std::string wire, failure;
  const auto call = [&](std::string_view step, const std::string &payload,
                        std::uint64_t revision, std::string_view request_id) {
    std::atomic<bool> done{false};
    bool ok = false, drained = false;
    std::thread worker([&] {
      ok = actual4::HandleRealmLawPrivateWithState12004(
          *state, adapter, mailbox, adapter.snapshot, revision, step, payload,
          request_id, wire, failure, &bindings);
      done.store(true, std::memory_order_release);
    });
    while (!done.load(std::memory_order_acquire)) {
      if (mailbox.state.load(std::memory_order_acquire) ==
          xar::ck3_11906::MainThreadQueryMailboxStateV1::queued)
        drained = xar::ck3_11906::ObserveMainThreadPumpAndDrainV1(
            mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId()) || drained;
      std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    worker.join();
    assert(!ok || drained);
    assert(mailbox.state == xar::ck3_11906::MainThreadQueryMailboxStateV1::idle);
    if (!ok)
      std::cerr << "failure: " << failure << "; source: "
                << state->source.failure << '\n';
    if (ok) CheckEnvelope(wire, request_id);
    return ok;
  };

  assert(call(actual4::kRealmLawCrownActionQueryStep12004, Payload(40) + "}",
              40, "wire-law-crown-query"));
  CheckActual4SourceFactory(*state);
  assert(wire.find("\"status\":\"available\"") != std::string::npos);
  assert(wire.find("\"snapshot_revision\":40,\"native_snapshot_revision\":40,\"proof_epoch\":40") != std::string::npos);
  assert(wire.find("\"player_character_id\":29829") != std::string::npos);
  assert(wire.find("\"active_law_key\":\"crown_authority_0\"") != std::string::npos);
  assert(wire.find("\"currency_key\":\"prestige\",\"amount_raw\":50000000") != std::string::npos);
  assert(wire.find("\"currency_key\":\"influence\",\"amount_raw\":11000000") != std::string::npos);
  assert(wire.find("\"currency_key\":\"merit\",\"amount_raw\":13000000") != std::string::npos);
  assert(wire.find("\"currency_key\":\"prestige\",\"cost_raw\":20000000") != std::string::npos);
  assert(wire.find("\"successor_character_ids\":[201,301]") != std::string::npos);
  assert(wire.find("\"successor_character_ids\":[301,201]") != std::string::npos);
  assert(fixture.queued == 0 && !state->has_pending_ack);
  Write(output, "wire-law-crown-query.json", wire);

  const auto submit = Payload(40) + ",\"submitted_request_id\":\"" +
      std::string(kActionId) + "\",\"group_key\":\"crown_authority\","
      "\"law_key\":\"crown_authority_1\",\"expected_native_revision\":40,"
      "\"expected_proof_epoch\":40,\"budget_prestige_raw\":20000000}";
  assert(call(actual4::kRealmLawCrownEnactStep12004, submit, 40,
              "wire-law-crown-submit-pending"));
  assert(state->has_pending_ack && state->binder.submit_pending);
  assert(state->pending_ack.request_id == kActionId);
  assert(fixture.validated == 1 && fixture.cloned == 1 && fixture.queued == 1);
  assert(wire.find("\"status\":\"submitted_verification_pending\"") != std::string::npos);
  assert(wire.find("\"verification_pending\":true") != std::string::npos);
  Write(output, "wire-law-crown-submit-pending.json", wire);

  const auto receipt_payload = [&](std::uint64_t revision) {
    return Payload(revision) + ",\"submitted_request_id\":\"" +
        std::string(kActionId) + "\"}";
  };
  assert(call(actual4::kRealmLawCrownReceiptStep12004, receipt_payload(41), 41,
              "wire-law-crown-receipt-unchanged"));
  assert(wire.find("\"status\":\"failed\"") != std::string::npos);
  assert(wire.find("\"failure\":\"effective_law_not_enacted\"") != std::string::npos);
  assert(state->has_pending_ack && state->binder.submit_pending && fixture.queued == 1);
  Write(output, "wire-law-crown-receipt-unchanged.json", wire);

  // Queue ACK did not change the fixture. A separate later paused native
  // observation now reports both the requested law and its exact charge.
  fixture.Put(fixture.active_slots, fixture.selected_law);
  fixture.Put(kResource + 0x130, std::int64_t{30'000'000});
  assert(call(actual4::kRealmLawCrownReceiptStep12004, receipt_payload(42), 42,
              "wire-law-crown-receipt-enacted"));
  assert(wire.find("\"status\":\"enacted\"") != std::string::npos);
  assert(wire.find("\"effective_law_key\":\"crown_authority_1\"") != std::string::npos);
  assert(wire.find("\"effective_law_verified\":true") != std::string::npos);
  assert(wire.find("\"resources_verified\":true") != std::string::npos);
  assert(wire.find("\"succession_verified\":true") != std::string::npos);
  assert(wire.find("\"pre_balance_raw\":50000000,\"post_balance_raw\":30000000") != std::string::npos);
  assert(!state->has_pending_ack && !state->binder.submit_pending && fixture.queued == 1);
  Write(output, "wire-law-crown-receipt-enacted.json", wire);
  std::cout << "PASS actual4 formal Crown production source/mailbox/binder/wire: "
               "query, typed submit once with actual4 command vtables/manager, "
               "ACK pending, independent unchanged failed receipt, then "
               "effective law/resource/full successor verification; offline, no CK3 access\n";
}
