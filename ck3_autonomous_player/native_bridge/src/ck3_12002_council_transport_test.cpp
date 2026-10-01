#include "xar_bridge/ck3_12002_council_transport.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12002_nonwar_mailbox.hpp"
#include "xar_bridge/council_application_main_private_transport_v1.hpp"
#include "ck3_12002_council_fixture.hpp"

#include <array>
#include <cassert>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <span>
#include <utility>
#include <vector>

namespace {
using namespace xar;
using namespace xar::ck3_12002;

void* local_player = nullptr;
void* LocalPlayer(void*) { return local_player; }

void* tls_context = nullptr;
void* __fastcall TlsContext() noexcept { return tls_context; }
BOOL WINAPI FixturePeek(LPMSG, HWND, UINT, UINT, UINT) { return FALSE; }

// Reuse the mailbox's existing offline fixture page model. The hook slot is
// fixture-owned storage, never a real application or game import table.
struct FixtureProtection {
  void** slot = nullptr;
  DWORD current_protect = PAGE_READONLY;
};
bool FixtureMemoryQuery(void* raw, const void* address,
    MEMORY_BASIC_INFORMATION& information) noexcept {
  const auto& protection = *static_cast<FixtureProtection*>(raw);
  if (address != protection.slot) return false;
  const auto slot_address = reinterpret_cast<std::uintptr_t>(address);
  information = {};
  information.BaseAddress = reinterpret_cast<void*>((slot_address / 4096) * 4096);
  information.AllocationBase = information.BaseAddress;
  information.AllocationProtect = PAGE_READONLY;
  information.RegionSize = 4096;
  information.State = MEM_COMMIT;
  information.Protect = protection.current_protect;
  information.Type = MEM_IMAGE;
  return true;
}
bool FixtureMemoryProtect(void* raw, void*, std::size_t size,
    DWORD desired, DWORD& previous) noexcept {
  auto& protection = *static_cast<FixtureProtection*>(raw);
  previous = protection.current_protect;
  if (size != 4096) return false;
  protection.current_protect = desired;
  return true;
}

using ProviderFixture = test::CouncilCandidatesFixture12002;
ProviderFixture* active_provider = nullptr;
CouncilTransportState12002* provider_transport = nullptr;
bool ProviderMemory(void* context, const void* address, void* output,
    std::size_t size) noexcept {
  assert(context == provider_transport && active_provider != nullptr);
  return ProviderFixture::Memory(active_provider, address, output, size);
}
bool ProviderInitialize(void* context, const CouncilCandidatesEnvironmentV1& environment,
    void* allocator, std::size_t size, CouncilCandidatesNativeVectorV1& vector) noexcept {
  assert(context == provider_transport && active_provider != nullptr);
  return ProviderFixture::Initialize(active_provider, environment, allocator, size, vector);
}
bool ProviderProduce(void* context, const CouncilCandidatesEnvironmentV1& environment,
    const void* owner, const void* task, bool gui,
    CouncilCandidatesNativeVectorV1& vector) noexcept {
  assert(context == provider_transport && active_provider != nullptr);
  return ProviderFixture::Produce(active_provider, environment, owner, task, gui, vector);
}
bool ProviderRelease(void* context, const CouncilCandidatesEnvironmentV1& environment,
    CouncilCandidatesNativeVectorV1& vector) noexcept {
  assert(context == provider_transport && active_provider != nullptr);
  return ProviderFixture::Release(active_provider, environment, vector);
}

// The same owned native callback shapes used by the existing source-chain
// fixture. The helper records invocation and never mutates the active task.
struct TypedActionFixture {
  ProviderFixture* provider = nullptr;
  test::Blob<0x20> pending_manager{};
  std::int32_t played_id = ProviderFixture::kOwner;
  unsigned native_gate_calls = 0, confirm_calls = 0, helper_calls = 0;
  std::int32_t submitted_candidate = -1, submitted_task = -1;
};
TypedActionFixture* active_action = nullptr;
bool ActionMemory(void* context, const void* address, void* output,
    std::size_t size) noexcept {
  auto& action = *static_cast<TypedActionFixture*>(context);
  if (ProviderFixture::Span(&action.played_id, sizeof(action.played_id), address, size) ||
      ProviderFixture::Span(action.pending_manager.Data(), 0x20, address, size)) {
    std::memcpy(output, address, size); return true;
  }
  return ProviderFixture::Memory(action.provider, address, output, size);
}
bool ActionIsCouncillor(void* candidate) {
  assert(active_action != nullptr &&
      (candidate == active_action->provider->characters[15].Data() ||
       candidate == active_action->provider->characters[16].Data()));
  ++active_action->native_gate_calls;
  return false;
}
bool ActionIsGuest(void*) {
  ++active_action->native_gate_calls;
  return false;
}
void ActionPendingSetup(void* window) {
  auto* bytes = static_cast<std::byte*>(window);
  for (std::size_t i = 0; i < kCouncilGatesPendingWindowSize12002; ++i)
    assert(bytes[i] == std::byte{});
  void* manager = active_action->pending_manager.Data();
  std::memcpy(bytes + kCouncilGatesPendingManagerOffset12002, &manager, sizeof(manager));
}
bool ActionHasPending(void* manager, std::int32_t candidate) {
  assert(manager == active_action->pending_manager.Data() &&
      (candidate == ProviderFixture::kCandidate || candidate == ProviderFixture::kCandidate + 1));
  ++active_action->native_gate_calls;
  return false;
}
bool ActionCanConfirm(void* confirmation) {
  const auto* bytes = static_cast<const std::byte*>(confirmation);
  std::int32_t incumbent = -1, candidate = -1;
  std::memcpy(&incumbent, bytes + kCouncilGatesConfirmationIncumbentOffset12002, sizeof(incumbent));
  std::memcpy(&candidate, bytes + kCouncilGatesConfirmationCandidateOffset12002, sizeof(candidate));
  const auto expected_incumbent = provider_transport->context.query_request.position_key ==
      kCouncilCandidatesChancellorPosition12002 ? ProviderFixture::kChancellorIncumbent :
      provider_transport->context.query_request.position_key == kCouncilCandidatesSpymasterPosition12002 ?
      ProviderFixture::kSpymasterIncumbent :
      ProviderFixture::kIncumbent;
  assert(incumbent == expected_incumbent &&
      (candidate == ProviderFixture::kCandidate || candidate == ProviderFixture::kCandidate + 1));
  ++active_action->confirm_calls;
  return true;
}
void ActionSubmit(void* context, std::int32_t candidate, std::int32_t task) noexcept {
  auto& action = *static_cast<TypedActionFixture*>(context);
  ++action.helper_calls;
  action.submitted_candidate = candidate;
  action.submitted_task = task;
}

template<typename T>
void Put(std::span<std::byte> bytes, std::size_t offset, T value) {
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

// Only the exact descriptor is consumed by the private handler. Any attempt
// to read a full snapshot or call gameplay through this adapter is counted.
class FixtureAdapter final : public game::GameAdapter {
public:
  explicit FixtureAdapter(bool current_build = false) : current_build_(current_build) {}
  mutable unsigned full_snapshot_reads = 0;
  const game::AdapterDescriptor& descriptor() const noexcept override {
    static const game::AdapterDescriptor value{
        "ck3-1.20.0.2-msvc-x64", "1.20.0.2", kExecutableSha256, "fixture-only", {}};
    static const game::AdapterDescriptor current{
        "ck3-1.20.0.3-msvc-x64", "1.20.0.3", ck3_12003::kExecutableSha256, "fixture-only", {}};
    return current_build_ ? current : value;
  }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot&) const noexcept override {
    ++full_snapshot_reads; return false;
  }
  game::PauseSubmitResult submit_pause_map(game::Snapshot*) const noexcept override { return {}; }
  game::ResumeSubmitResult submit_resume_map(game::Snapshot*) const noexcept override { return {}; }
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  game::SelectEventOptionResult submit_select_event_option(std::int32_t) const noexcept override { return {}; }
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override { return {}; }
  game::ReplyPendingInteractionResult submit_reply_to_pending_interaction(game::PendingInteractionReply) const noexcept override { return {}; }
  game::RaiseTroopsResult submit_raise_troops_default() const noexcept override { return {}; }
  game::MoveArmyResult submit_move_army(std::int32_t, std::int32_t) const noexcept override { return {}; }
  game::PreviewMoveArmyResult preview_move_army(std::int32_t, std::int32_t) const noexcept override { return {}; }
  game::DisbandArmyResult submit_disband_army(std::int32_t) const noexcept override { return {}; }
  game::SplitArmyHalfResult submit_split_army_half(std::int32_t) const noexcept override { return {}; }
  game::MergeArmiesResult submit_merge_armies(std::int32_t, std::int32_t) const noexcept override { return {}; }
  game::StartAssaultResult submit_start_assault(std::int32_t) const noexcept override { return {}; }
  game::StopAssaultResult submit_stop_assault(std::int32_t) const noexcept override { return {}; }
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot>&) const noexcept override { return false; }
  game::ReadDeclarableWarsResult read_declarable_wars_for_target(std::int32_t, std::vector<game::DeclarableWarSnapshot>&) const noexcept override { return {}; }
  game::DeclareWarResult submit_declare_war(const game::DeclarableWarSnapshot&) const noexcept override { return {}; }
  game::ReadArrangeMarriageChoicesResult read_arrange_marriage_choices(std::vector<game::ArrangeMarriageChoice>&, game::ArrangeMarriageQueryDiagnostics&) const noexcept override { return {}; }
  game::ArrangeMarriageResult submit_arrange_marriage(const game::ArrangeMarriageChoice&) const noexcept override { return {}; }
  game::EnforceDemandsResult submit_enforce_demands(std::int32_t) const noexcept override { return {}; }
  game::ReadArmyStrengthsResult read_army_strengths(std::vector<game::ArmyStrengthSnapshot>&) const noexcept override { return {}; }
  game::ReadCombatSimulationInputsResult read_combat_simulation_inputs(const game::CombatSimulationInputsRequest&, game::CombatSimulationInputsSnapshot&) const noexcept override { return {}; }
  game::ReadCombatSimulationInputsV3Result read_combat_simulation_inputs_v3(const game::CombatSimulationInputsRequest&, game::CombatSimulationInputsV3Snapshot&) const noexcept override { return {}; }
  game::ReadWarTerminationOptionsResult read_war_termination_options(std::int32_t, game::WarTerminationOptionsSnapshot&) const noexcept override { return {}; }
  game::ReadWarTerminationTermsResult read_war_termination_terms(std::int32_t, game::WarTerminationTermsSnapshot&) const noexcept override { return {}; }
  game::ReadWarTerminationExitTermsResult read_war_termination_exit_terms(std::int32_t, game::WarTerminationExitTermsSnapshot&) const noexcept override { return {}; }
  game::SurrenderWarResult submit_surrender_war(std::int32_t) const noexcept override { return {}; }
  game::OfferWhitePeaceResult submit_offer_white_peace(std::int32_t) const noexcept override { return {}; }
private:
  bool current_build_ = false;
};

void WriteWire(const std::filesystem::path& directory,
    std::string_view name, std::string_view value) {
  if (directory.empty()) return;
  std::ofstream file(directory / name, std::ios::binary);
  file << value << '\n';
  assert(file.good());
}

void CheckSourceFrame(const std::filesystem::path& wire_directory) {
  ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  CouncilTransportState12002 transport{};
  assert(!ConfigureCouncilTransport12002(transport, mailbox,
      0x140000000, "old-or-unknown", true, true));
  assert(ConfigureCouncilTransport12002(transport, mailbox,
      0x140000000, kExecutableSha256, true, true));
  assert(transport.context.shared_state == &transport.shared);
  assert(transport.context.candidates_access.context == &transport);
  assert(transport.context.private_action_enabled);
  assert(!ConfigureCouncilTransport12002(transport, mailbox,
      0x140000000, kExecutableSha256, true, true));

  constexpr std::int32_t actor_id = 0x03000004;
  constexpr std::int32_t date = 53175816;
  std::array<std::byte, 0xA8> game_state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> player{};
  std::vector<std::byte> data(0x36780);
  std::array<std::byte, 0xE0> player_entry{};
  std::array<void*, 1> entries{player_entry.data()};
  std::array<std::byte, 0x30> storage{};
  std::array<std::byte, 0x80> slots{};
  std::array<std::byte, 0x1D8> character{};
  Put(game_state, 8, date);
  Put(game_state, 0x70, std::int32_t{2});
  Put(game_state, 0xA0, data.data());
  Put(jomini, 0x18, players.data());
  jomini[0x20] = std::byte{1};
  Put(players, 0x1F0, std::int32_t{7});
  Put(player, 0x70, std::int32_t{7});
  Put(std::span(data), 0x222E8 + 0x58, entries.data());
  Put(std::span(data), 0x222E8 + 0x64, std::int32_t{1});
  Put(player_entry, 0xD8, std::int32_t{7});
  Put(player_entry, 0xB0, actor_id);
  Put(storage, 0x20, slots.data());
  Put(storage, 0x2C, std::int32_t{8});
  Put(slots, 4 * 0x10 + 8, character.data());
  Put(character, 0x18, actor_id);

  void* game_pointer = game_state.data();
  void* jomini_pointer = jomini.data();
  void* storage_pointer = storage.data();
  void* fallback_pointer = nullptr;
  local_player = player.data();
  transport.core = {true, &game_pointer, &jomini_pointer, &storage_pointer,
      &LocalPlayer};
  auto& environment = transport.context.candidates_environment;
  environment.offline_fixture_function_overrides = true;
  environment.character_storage_slot = &storage_pointer;
  environment.character_fallback_slot = &fallback_pointer;

  transport.expected_snapshot.date_raw = date;
  transport.expected_snapshot.paused = true;
  transport.expected_snapshot.player_id = 7;
  transport.expected_snapshot.map_ready = true;
  transport.expected_snapshot.has_played_character = true;
  transport.expected_snapshot.played_character_id = actor_id;
  transport.expected_snapshot.played_character_alive = true;
  transport.expected_snapshot_id = "native:12";
  transport.expected_revision = 12;
  transport.context.query_request = {transport.expected_snapshot_id,
      12, 12, date, actor_id};
  ck3_11906::MainThreadExecutionStampV1 stamp{};
  stamp.thread_id = GetCurrentThreadId();
  stamp.game_state = reinterpret_cast<std::uintptr_t>(game_pointer);
  stamp.jomini_state = reinterpret_cast<std::uintptr_t>(jomini_pointer);
  stamp.date_raw = date;
  stamp.paused = true;
  transport.context.active_stamp = &stamp;
  const auto& access = transport.context.candidates_access;
  CouncilCandidatesFrameV1 frame{};
  assert(access.is_main_thread(access.context));
  assert(access.capture_frame(access.context, frame));
  assert(frame.public_revision == 12 && frame.native_revision == 12);
  assert(frame.date_raw == date && frame.played_character_id == actor_id);
  assert(frame.played_character_identity_round_trip &&
      frame.played_character == reinterpret_cast<std::uintptr_t>(character.data()));
  assert(frame.active_task == 0 && frame.active_task_id == -1);

  // The worker's published frame cannot authorize a changed core date.
  Put(game_state, 8, std::int32_t{date + 1});
  assert(!access.capture_frame(access.context, frame));
  assert(frame.played_character == 0 && frame.public_revision == 0);
  Put(game_state, 8, date);
  // A reused low storage index cannot authorize a different generation.
  Put(character, 0x18, std::int32_t{0x04000004});
  assert(!access.capture_frame(access.context, frame));
  assert(frame.played_character == 0 && frame.public_revision == 0);
  Put(character, 0x18, actor_id);
  transport.context.active_stamp = nullptr;
  assert(!access.is_main_thread(access.context));
  assert(!access.capture_frame(access.context, frame));

  // Exercise the actual async handler, fixed executor and real reclaim.
  // This owned actor has no active steward task. The new native provider
  // therefore produces its real query_unavailable result, never a fabricated
  // available candidate payload.
  FixtureAdapter adapter{};
  const auto published = transport.expected_snapshot;
  void* iat_slot = reinterpret_cast<void*>(&FixturePeek);
  FixtureProtection protection{&iat_slot};
  std::array<std::byte, 0x28> tls{};
  tls[0x20] = std::byte{1};
  tls_context = tls.data();
  std::uint8_t tls_initialized = 1;
  std::uintptr_t rng_wrapper_slot = 0;
  auto install = BindThreadRuntimeImage(0x140000000, kExecutableSha256);
  install.offline_fixture = true;
  install.peek_message_iat_slot_override = &iat_slot;
  install.resolved_peek_message_override = &FixturePeek;
  install.global_rng_wrapper_slot_override = reinterpret_cast<std::uintptr_t>(&rng_wrapper_slot);
  install.jomini_state_slot_override = reinterpret_cast<std::uintptr_t>(&jomini_pointer);
  install.game_state_slot_override = reinterpret_cast<std::uintptr_t>(&game_pointer);
  install.tls_initialized_flag_override = reinterpret_cast<std::uintptr_t>(&tls_initialized);
  install.tls_context_getter_override = &TlsContext;
  install.memory_protection_context = &protection;
  install.memory_query_override = &FixtureMemoryQuery;
  install.memory_protect_override = &FixtureMemoryProtect;
  install.system_page_size_override = 4096;
  install.executor_submission_enabled = true;
  NonwarMailboxExecutorsV1 executors{};
  executors.council = &ExecuteCouncilMailbox12002;
  RegisterNonwarMailboxExecutorsV1(install, executors);
  assert(install.permitted_executor_unquadragintary == &ExecuteCouncilMailbox12002);
  assert(ck3_11906::InstallMainThreadQueryMailboxV1(mailbox, install));
  assert(!ck3_11906::ObserveMainThreadPumpAndDrainV1(mailbox,
      kSdlWindowsPumpFirstPeekReturnRva, stamp.thread_id));
  assert(!ck3_11906::ObserveMainThreadPumpAndDrainV1(mailbox,
      kSdlWindowsPumpFirstPeekReturnRva, stamp.thread_id));
  std::string serialized, failure;
  assert(HandleCouncilPrivate12002(adapter, mailbox, published, 12,
      bridge::kCouncilPrivateQueryStepV1, "{\"expected_revision\":12}",
      "query-12", transport, serialized, failure));
  assert(failure.empty() && serialized.find("\"status\":\"pending\"") != std::string::npos);
  WriteWire(wire_directory, "query_pending.json", serialized);
  assert(transport.in_flight && transport.context.ticket.sequence == 1);
  assert(mailbox.executor == &ExecuteCouncilMailbox12002 &&
      mailbox.executor_context == &transport.context);
  const auto ticket_sequence = mailbox.next_sequence.load();

  // Status requires neither an expected_revision nor a ready map snapshot.
  assert(HandleCouncilPrivate12002(adapter, mailbox, {}, 0,
      bridge::kCouncilPrivateStatusStepV1, "{}", "status-pending",
      transport, serialized, failure));
  assert(serialized.find("\"status\":\"pending\"") != std::string::npos);
  assert(mailbox.next_sequence.load() == ticket_sequence);
  WriteWire(wire_directory, "status_pending.json", serialized);

  assert(ck3_11906::ObserveMainThreadPumpAndDrainV1(mailbox,
      kSdlWindowsPumpFirstPeekReturnRva, stamp.thread_id));
  assert(mailbox.executor_succeeded);
  assert(mailbox.state.load() == ck3_11906::MainThreadQueryMailboxStateV1::completed);
  assert(HandleCouncilPrivate12002(adapter, mailbox, {}, 0,
      bridge::kCouncilPrivateStatusStepV1, "{}", "status-result",
      transport, serialized, failure));
  assert(failure.empty() && serialized.find("\"status\":\"unavailable\"") != std::string::npos);
  assert(serialized.find("active_steward_task_unavailable") != std::string::npos);
  assert(serialized.find("\"query_sequence\":1") != std::string::npos);
  assert(serialized.find("\"game_version\":\"1.20.0.2\"") != std::string::npos);
  assert(!transport.in_flight && !transport.has_completed);
  assert(mailbox.state.load() == ck3_11906::MainThreadQueryMailboxStateV1::idle);
  assert(mailbox.next_sequence.load() == ticket_sequence);
  WriteWire(wire_directory, "status_result.json", serialized);

  assert(HandleCouncilPrivate12002(adapter, mailbox, {}, 0,
      bridge::kCouncilPrivateStatusStepV1, "{}", "status-idle",
      transport, serialized, failure));
  assert(serialized.find("\"status\":\"idle\"") != std::string::npos);
  assert(mailbox.next_sequence.load() == ticket_sequence && adapter.full_snapshot_reads == 0);
  WriteWire(wire_directory, "status_idle.json", serialized);

  // Compose the existing full provider fixture with the owned core source.
  // The provider's standalone 8/7 source frame is untouched. The real handler
  // prepares native:13 with 13/13 and its own capture callback reads the core.
  ProviderFixture provider{};
  active_provider = &provider;
  provider_transport = &transport;
  transport.context.candidates_environment = provider.environment;
  auto& provider_access = transport.context.candidates_access;
  provider_access.read_memory = &ProviderMemory;
  provider_access.initialize_vector = &ProviderInitialize;
  provider_access.invoke_producer = &ProviderProduce;
  provider_access.release_allocation = &ProviderRelease;
  transport.core.character_storage_slot = &provider.character_storage_pointer;
  Put(player_entry, 0xB0, ProviderFixture::kOwner);
  auto available_published = published;
  available_published.played_character_id = ProviderFixture::kOwner;
  assert(HandleCouncilPrivate12002(adapter, mailbox, available_published, 13,
      bridge::kCouncilPrivateQueryStepV1, "{\"expected_revision\":13}",
      "query-13", transport, serialized, failure));
  assert(serialized.find("\"status\":\"pending\"") != std::string::npos);
  WriteWire(wire_directory, "query_pending_available.json", serialized);
  const auto available_sequence = mailbox.next_sequence.load();
  assert(transport.context.query_request.expected_snapshot_id == "native:13" &&
      transport.context.query_request.expected_public_revision == 13 &&
      transport.context.query_request.expected_native_revision == 13);
  assert(HandleCouncilPrivate12002(adapter, mailbox, {}, 0,
      bridge::kCouncilPrivateStatusStepV1, "{}", "status-available-pending",
      transport, serialized, failure));
  assert(serialized.find("\"status\":\"pending\"") != std::string::npos);
  assert(mailbox.next_sequence.load() == available_sequence);
  WriteWire(wire_directory, "status_pending_available.json", serialized);
  assert(ck3_11906::ObserveMainThreadPumpAndDrainV1(mailbox,
      kSdlWindowsPumpFirstPeekReturnRva, stamp.thread_id));
  assert(provider.producer_calls == 1 && provider.release_calls == 1 &&
      provider.allocator_shape_valid && provider.producer_inputs_valid);
  assert(HandleCouncilPrivate12002(adapter, mailbox, {}, 0,
      bridge::kCouncilPrivateStatusStepV1, "{}", "status-available-result",
      transport, serialized, failure));
  assert(failure.empty() && serialized.find("\"status\":\"available\"") != std::string::npos);
  assert(serialized.find("\"snapshot_id\":\"native:13\"") != std::string::npos);
  assert(serialized.find("\"public_revision\":13") != std::string::npos &&
      serialized.find("\"native_revision\":13") != std::string::npos);
  assert(transport.context.wire.query_result.readiness.ready &&
      transport.context.wire.query_result.candidate_count == 2 &&
      transport.context.wire.query_result.candidates[0].character_id == ProviderFixture::kCandidate &&
      transport.context.wire.query_result.candidates[0].native_collection_ordinal == 1);
  assert(provider.frame.public_revision == 8 && provider.frame.native_revision == 7);
  assert(!transport.has_completed && !transport.in_flight &&
      mailbox.next_sequence.load() == available_sequence);
  WriteWire(wire_directory, "status_available.json", serialized);
  assert(HandleCouncilPrivate12002(adapter, mailbox, {}, 0,
      bridge::kCouncilPrivateStatusStepV1, "{}", "status-available-idle",
      transport, serialized, failure));
  assert(serialized.find("\"status\":\"idle\"") != std::string::npos);
  assert(mailbox.next_sequence.load() == available_sequence && adapter.full_snapshot_reads == 0);
  WriteWire(wire_directory, "status_idle_available.json", serialized);

  TypedActionFixture action{};
  action.provider = &provider;
  action.pending_manager.Put(0x8, action.played_id);
  active_action = &action;
  auto& gates = transport.context.gates_environment;
  gates = {};
  gates.exact_build_admitted = true;
  gates.admitted_executable_sha256 = kExecutableSha256;
  gates.offline_fixture = true;
  gates.played_character_id_slot = &action.played_id;
  gates.read_context = &action;
  gates.read_memory = &ActionMemory;
  gates.is_councillor = &ActionIsCouncillor;
  gates.is_guest = &ActionIsGuest;
  gates.pending_setup = &ActionPendingSetup;
  gates.has_pending = &ActionHasPending;
  gates.can_confirm = &ActionCanConfirm;
  auto& submit = transport.context.submit;
  submit.environment = {};
  submit.environment.exact_build_admitted = true;
  submit.environment.admitted_executable_sha256 = kExecutableSha256;
  submit.environment.native_command_abi_certified = true;
  submit.environment.offline_fixture = true;
  submit.fixture_context = &action;
  submit.fixture_helper = &ActionSubmit;

  const auto assign_payload = "{\"expected_revision\":13,\"candidate_character_id\":" +
      std::to_string(ProviderFixture::kCandidate) + "}";
  assert(HandleCouncilPrivate12002(adapter, mailbox, available_published, 13,
      bridge::kCouncilPrivateAssignStepV1, assign_payload, "assign-13",
      transport, serialized, failure));
  assert(failure.empty() && serialized.find("\"status\":\"pending\"") != std::string::npos);
  assert(transport.context.operation == bridge::CouncilApplicationMainOperationV1::submit_assignment);
  const auto assign_sequence = mailbox.next_sequence.load();
  WriteWire(wire_directory, "assign_pending.json", serialized);
  assert(HandleCouncilPrivate12002(adapter, mailbox, {}, 0,
      bridge::kCouncilPrivateStatusStepV1, "{}", "status-assign-pending",
      transport, serialized, failure));
  assert(serialized.find("\"status\":\"pending\"") != std::string::npos &&
      mailbox.next_sequence.load() == assign_sequence);
  WriteWire(wire_directory, "status_assign_pending.json", serialized);
  assert(ck3_11906::ObserveMainThreadPumpAndDrainV1(mailbox,
      kSdlWindowsPumpFirstPeekReturnRva, stamp.thread_id));
  assert(action.helper_calls == 1 && action.native_gate_calls == 3 && action.confirm_calls == 1);
  assert(action.submitted_candidate == ProviderFixture::kCandidate && action.submitted_task == ProviderFixture::kTask);
  assert(provider.producer_calls == 2 && provider.release_calls == 2);
  std::int32_t incumbent_after_helper = -1;
  std::memcpy(&incumbent_after_helper, provider.tasks[0].bytes.data() + 0x40, sizeof(incumbent_after_helper));
  assert(incumbent_after_helper == ProviderFixture::kIncumbent);
  assert(HandleCouncilPrivate12002(adapter, mailbox, {}, 0,
      bridge::kCouncilPrivateStatusStepV1, "{}", "status-ack",
      transport, serialized, failure));
  assert(failure.empty() && serialized.find("native_helper_invoked_verification_pending") != std::string::npos);
  assert(transport.context.wire.action_ack.native_helper_invoked &&
      transport.context.wire.action_ack.verification_pending &&
      !transport.context.wire.action_ack.queue_acceptance_observed);
  assert(transport.shared.has_pending_ack && transport.shared.pending_submit_sequence == assign_sequence);
  assert(transport.shared.pending_ack.request_id == "assign-13" &&
      transport.shared.pending_ack.pre_native_revision == 13);
  assert(mailbox.next_sequence.load() == assign_sequence);
  WriteWire(wire_directory, "status_ack.json", serialized);
  assert(HandleCouncilPrivate12002(adapter, mailbox, {}, 0,
      bridge::kCouncilPrivateStatusStepV1, "{}", "status-assign-idle",
      transport, serialized, failure));
  assert(serialized.find("\"status\":\"idle\"") != std::string::npos && transport.shared.has_pending_ack);
  assert(mailbox.next_sequence.load() == assign_sequence);
  WriteWire(wire_directory, "status_assign_idle.json", serialized);

  // The helper ACK proves invocation only. This independent owned paused
  // frame explicitly advances core date/revision and changes task state.
  Put(game_state, 8, std::int32_t{date + 1});
  auto receipt_published = available_published;
  receipt_published.date_raw = date + 1;
  provider.tasks[0].Put(0x40, ProviderFixture::kCandidate);
  assert(HandleCouncilPrivate12002(adapter, mailbox, receipt_published, 14,
      bridge::kCouncilPrivateReceiptStepV1, "{\"expected_revision\":14}",
      "receipt-14", transport, serialized, failure));
  assert(failure.empty() && serialized.find("\"status\":\"pending\"") != std::string::npos);
  const auto receipt_sequence = mailbox.next_sequence.load();
  assert(receipt_sequence > assign_sequence && transport.context.query_request.expected_snapshot_id == "native:14");
  WriteWire(wire_directory, "receipt_pending.json", serialized);
  assert(HandleCouncilPrivate12002(adapter, mailbox, {}, 0,
      bridge::kCouncilPrivateStatusStepV1, "{}", "status-receipt-pending",
      transport, serialized, failure));
  assert(serialized.find("\"status\":\"pending\"") != std::string::npos &&
      mailbox.next_sequence.load() == receipt_sequence);
  WriteWire(wire_directory, "status_receipt_pending.json", serialized);
  assert(ck3_11906::ObserveMainThreadPumpAndDrainV1(mailbox,
      kSdlWindowsPumpFirstPeekReturnRva, stamp.thread_id));
  assert(HandleCouncilPrivate12002(adapter, mailbox, {}, 0,
      bridge::kCouncilPrivateStatusStepV1, "{}", "status-receipt",
      transport, serialized, failure));
  assert(failure.empty() && serialized.find("\"status\":\"applied\"") != std::string::npos);
  const auto& receipt = transport.context.wire.action_receipt;
  assert(receipt.postcondition_verified && receipt.incumbent_identity_round_trip &&
      receipt.incumbent_character_id == ProviderFixture::kCandidate &&
      receipt.post_public_revision == 14 && receipt.post_native_revision == 14 &&
      receipt.request_id == "assign-13");
  assert(!transport.shared.has_pending_ack && action.helper_calls == 1 &&
      mailbox.next_sequence.load() == receipt_sequence);
  WriteWire(wire_directory, "status_receipt.json", serialized);
  assert(HandleCouncilPrivate12002(adapter, mailbox, {}, 0,
      bridge::kCouncilPrivateStatusStepV1, "{}", "status-receipt-idle",
      transport, serialized, failure));
  assert(serialized.find("\"status\":\"idle\"") != std::string::npos &&
      mailbox.next_sequence.load() == receipt_sequence && adapter.full_snapshot_reads == 0);
  WriteWire(wire_directory, "status_receipt_idle.json", serialized);

  // The receipt's changed date starts a new paused pump identity. Observe
  // its next real idle pump before submitting another independent query.
  assert(!ck3_11906::ObserveMainThreadPumpAndDrainV1(mailbox,
      kSdlWindowsPumpFirstPeekReturnRva, stamp.thread_id));
  assert(mailbox.paused_owner_verified_pump_epochs.load() >=
      ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);

  // A current-build private query owns its role string after the incoming
  // payload is gone and independently selects the Chancellor task/skill.
  provider.EnableChancellor();
  FixtureAdapter current_adapter{true};
  std::string chancellor_payload = "{\"expected_revision\":14,\"position_key\":\"councillor_chancellor\"}";
  const bool chancellor_query_accepted = HandleCouncilPrivate12002(
      current_adapter, mailbox, receipt_published, 14,
      bridge::kCouncilPrivateQueryStepV1, chancellor_payload,
      "chancellor-query-14", transport, serialized, failure);
  if (!chancellor_query_accepted)
    std::cerr << "Chancellor private query failed: " << failure << '\n';
  assert(chancellor_query_accepted);
  chancellor_payload.clear();
  assert(transport.query_position_key == ProviderFixture::kChancellorPosition &&
      transport.context.query_request.position_key == transport.query_position_key);
  assert(ck3_11906::ObserveMainThreadPumpAndDrainV1(mailbox,
      kSdlWindowsPumpFirstPeekReturnRva, stamp.thread_id));
  assert(HandleCouncilPrivate12002(current_adapter, mailbox, {}, 0,
      bridge::kCouncilPrivateStatusStepV1, "{}", "chancellor-query-result",
      transport, serialized, failure));
  assert(transport.context.wire.query_result.readiness.ready && provider.producer_inputs_valid &&
      transport.context.wire.query_result.incumbent_character_id == ProviderFixture::kChancellorIncumbent &&
      transport.context.wire.query_result.incumbent_main_skill.value == 14 &&
      transport.context.wire.query_result.candidates[0].main_skill.value == 28 &&
      serialized.find("councillor_chancellor") != std::string::npos &&
      serialized.find("\"key\":\"diplomacy\"") != std::string::npos);
  WriteWire(wire_directory, "chancellor_status_available.json", serialized);
  const auto before_chancellor_assignment = mailbox.next_sequence.load();
  const auto current_assign_payload = "{\"expected_revision\":14,\"candidate_character_id\":" +
      std::to_string(ProviderFixture::kCandidate) + "}";
  assert(!HandleCouncilPrivate12002(current_adapter, mailbox, receipt_published, 14,
      bridge::kCouncilPrivateAssignStepV1, current_assign_payload, "chancellor-not-an-action",
      transport, serialized, failure));
  assert(failure == "private_candidate_frame_changed" && action.helper_calls == 1 &&
      !transport.shared.has_pending_ack && mailbox.next_sequence.load() == before_chancellor_assignment);
  assert(HandleCouncilPrivate12002(current_adapter, mailbox, receipt_published, 14,
      bridge::kCouncilFinalGatesPrivateStepV1,
      "{\"expected_revision\":14,\"position_key\":\"councillor_chancellor\"}",
      "chancellor-gates-14", transport, serialized, failure));
  assert(ck3_11906::ObserveMainThreadPumpAndDrainV1(mailbox,
      kSdlWindowsPumpFirstPeekReturnRva, stamp.thread_id));
  assert(HandleCouncilPrivate12002(current_adapter, mailbox, {}, 0,
      bridge::kCouncilPrivateStatusStepV1, "{}", "chancellor-gates-result",
      transport, serialized, failure));
  assert(transport.context.wire.completion == bridge::CouncilApplicationMainCompletionV1::query_available &&
      transport.context.wire.final_gate_row_count == 2 &&
      transport.context.wire.final_gate_rows[0].fireability_evaluated &&
      action.helper_calls == 1 && current_adapter.full_snapshot_reads == 0);
  WriteWire(wire_directory, "chancellor_status_gates.json", serialized);

  // The current descriptor selects the reviewed ABI binder. The actual .3
  // production identity renderer emits the final wire, as it does in bridge.
  provider.EnableSpymaster();
  assert(current_adapter.descriptor().game_version == "1.20.0.3" &&
      current_adapter.descriptor().executable_sha256 == ck3_12003::kExecutableSha256 &&
      game::ReviewedCrozierAbiSha256(current_adapter.descriptor()) == kExecutableSha256);
  std::string spymaster_payload = "{\"expected_revision\":14,\"position_key\":\"councillor_spymaster\"}";
  assert(HandleCouncilPrivate12002(current_adapter, mailbox, receipt_published, 14,
      bridge::kCouncilPrivateQueryStepV1, spymaster_payload,
      "spymaster-query-14", transport, serialized, failure));
  spymaster_payload.clear();
  assert(transport.query_position_key == ProviderFixture::kSpymasterPosition &&
      transport.context.query_request.position_key == transport.query_position_key);
  assert(ck3_11906::ObserveMainThreadPumpAndDrainV1(mailbox,
      kSdlWindowsPumpFirstPeekReturnRva, stamp.thread_id));
  assert(HandleCouncilPrivate12002(current_adapter, mailbox, {}, 0,
      bridge::kCouncilPrivateStatusStepV1, "{}", "spymaster-query-result",
      transport, serialized, failure));
  assert(transport.context.wire.query_result.readiness.ready && provider.producer_inputs_valid &&
      transport.context.wire.query_result.incumbent_character_id == ProviderFixture::kSpymasterIncumbent &&
      transport.context.wire.query_result.incumbent_main_skill.value == 17 &&
      transport.context.wire.query_result.candidates[0].main_skill.value == 23 &&
      transport.context.wire.query_result.candidates[1].main_skill.value == 13 &&
      transport.context.wire.query_result.candidate_count == 2 &&
      transport.context.wire.query_result.candidate_collection_complete);
  serialized = game::RenderCrozierBuildIdentity(std::move(serialized), current_adapter.descriptor());
  assert(serialized.find("\"game_version\":\"1.20.0.3\"") != std::string::npos &&
      serialized.find(ck3_12003::kExecutableSha256) != std::string::npos &&
      serialized.find(kExecutableSha256) == std::string::npos &&
      serialized.find("councillor_spymaster") != std::string::npos &&
      serialized.find("\"key\":\"intrigue\"") != std::string::npos);
  WriteWire(wire_directory, "spymaster_status_available.json", serialized);

  const auto before_spymaster_assignment = mailbox.next_sequence.load();
  assert(!HandleCouncilPrivate12002(current_adapter, mailbox, receipt_published, 14,
      bridge::kCouncilPrivateAssignStepV1, current_assign_payload, "spymaster-not-an-action",
      transport, serialized, failure));
  assert(failure == "private_candidate_frame_changed" && action.helper_calls == 1 &&
      !transport.shared.has_pending_ack && mailbox.next_sequence.load() == before_spymaster_assignment);
  const auto confirms_before_spymaster_gates = action.confirm_calls;
  assert(HandleCouncilPrivate12002(current_adapter, mailbox, receipt_published, 14,
      bridge::kCouncilFinalGatesPrivateStepV1,
      "{\"expected_revision\":14,\"position_key\":\"councillor_spymaster\"}",
      "spymaster-gates-14", transport, serialized, failure));
  assert(ck3_11906::ObserveMainThreadPumpAndDrainV1(mailbox,
      kSdlWindowsPumpFirstPeekReturnRva, stamp.thread_id));
  assert(HandleCouncilPrivate12002(current_adapter, mailbox, {}, 0,
      bridge::kCouncilPrivateStatusStepV1, "{}", "spymaster-gates-result",
      transport, serialized, failure));
  assert(transport.context.wire.completion == bridge::CouncilApplicationMainCompletionV1::query_available &&
      transport.context.wire.query_result.incumbent_character_id == ProviderFixture::kSpymasterIncumbent &&
      transport.context.wire.query_result.incumbent_main_skill.value == 17 &&
      transport.context.wire.final_gate_row_count == 2 &&
      transport.context.wire.final_gate_rows[0].available &&
      transport.context.wire.final_gate_rows[0].fireability_evaluated &&
      transport.context.wire.final_gate_rows[1].available &&
      transport.context.wire.final_gate_rows[1].fireability_evaluated &&
      action.confirm_calls == confirms_before_spymaster_gates + 2 &&
      action.helper_calls == 1 && current_adapter.full_snapshot_reads == 0);
  serialized = game::RenderCrozierBuildIdentity(std::move(serialized), current_adapter.descriptor());
  assert(serialized.find("\"game_version\":\"1.20.0.3\"") != std::string::npos &&
      serialized.find(ck3_12003::kExecutableSha256) != std::string::npos &&
      serialized.find(kExecutableSha256) == std::string::npos &&
      serialized.find("councillor_spymaster") != std::string::npos &&
      serialized.find("\"key\":\"intrigue\"") != std::string::npos);
  WriteWire(wire_directory, "spymaster_status_gates.json", serialized);
  const auto before_unknown_role = mailbox.next_sequence.load();
  assert(!HandleCouncilPrivate12002(current_adapter, mailbox, receipt_published, 14,
      bridge::kCouncilPrivateQueryStepV1,
      "{\"expected_revision\":14,\"position_key\":\"councillor_marshal\"}",
      "unknown-role", transport, serialized, failure));
  assert(failure == "private_position_outside_coverage" &&
      mailbox.next_sequence.load() == before_unknown_role && !transport.in_flight);
  assert(ck3_11906::UninstallMainThreadQueryMailboxV1(mailbox, 10) ==
      ck3_11906::MainThreadQueryUninstallResultV1::uninstalled);
  assert(iat_slot == reinterpret_cast<void*>(&FixturePeek));
  active_provider = nullptr;
  provider_transport = nullptr;
  active_action = nullptr;
}

void CheckAsyncReclaim() {
  ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  CouncilTransportState12002 state{};
  assert(ConfigureCouncilTransport12002(state, mailbox,
      0x140000000, kExecutableSha256));
  state.context.ticket.sequence = 9;
  state.context.operation = bridge::CouncilApplicationMainOperationV1::query_candidates;
  state.context.wire.ticket = state.context.ticket;
  state.context.wire.operation = state.context.operation;
  state.context.wire.completion = bridge::CouncilApplicationMainCompletionV1::query_unavailable;
  state.context.wire.query_result.unavailable_reason =
      game::CouncilCompositionCandidatesPublicFailureV1::private_reader_unavailable;
  state.shared.has_pending_ack = true;
  state.shared.pending_submit_sequence = 8;
  state.shared.pending_ack.request_id = "assignment-8";
  state.in_flight = true;
  mailbox.published_sequence.store(9);
  mailbox.state.store(ck3_11906::MainThreadQueryMailboxStateV1::executing);
  PollCouncilTransport12002(state);
  assert(state.in_flight && !state.has_completed);

  mailbox.completed_sequence.store(9);
  mailbox.state.store(ck3_11906::MainThreadQueryMailboxStateV1::completed);
  PollCouncilTransport12002(state);
  assert(!state.in_flight && state.has_completed);
  assert(mailbox.state.load() == ck3_11906::MainThreadQueryMailboxStateV1::idle);
  assert(state.shared.has_pending_ack && state.shared.pending_submit_sequence == 8);
  assert(state.shared.pending_ack.request_id == "assignment-8");
  const auto serialized = SerializeCouncilMailbox12002(state.completed, "status-9");
  assert(serialized.find("\"query_sequence\":9") != std::string::npos);
  assert(serialized.find("\"game_version\":\"1.20.0.2\"") != std::string::npos);
  assert(serialized.find(kExecutableSha256) != std::string::npos);
}
} // namespace

int main(int argc, char** argv) {
  const std::filesystem::path wire_directory = argc > 1 ? argv[1] : "";
  CheckSourceFrame(wire_directory);
  CheckAsyncReclaim();
  std::cout << "PASS 1.20.0.2 council private transport source/reclaim/Handle query-assign-receipt fixtures\n";
}
