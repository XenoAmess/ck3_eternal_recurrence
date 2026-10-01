#include "xar_bridge/ck3_12002_religion_conversion_reasons_mailbox.hpp"

#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace q = xar::ck3_12002::religion_conversion::reasons;
namespace r = xar::ck3_12002::religion_conversion_rite;
namespace c = xar::ck3_12002;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename B, typename T> void Put(B &bytes, std::size_t at, T value) {
  std::memcpy(bytes.data()+at, &value, sizeof(value));
}
struct Fixture {
  Bytes<0xA8> state{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> characters{}, rites{};
  Bytes<0x80> character_slots{}, rite_slots{};
  Bytes<0x1D8> character{};
  Bytes<0x500> current{}, target{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *characters_ptr = characters.data(), *rites_ptr = rites.data();
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::uint32_t target_id = 0x82000002U;
  std::string text = "Not adult.";
  bool native_accepted = false, initialized_string = true, command_shape = true;
  bool malformed_text = false, owner_called = true;
  const DWORD owner = GetCurrentThreadId();
  std::uint32_t expected_target = target_id;
  int calls = 0, destroys = 0, allocations = 0, heap_destroys = 0;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2});
    Put(state, 0xA0, data.data()); Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset+0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset+0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(characters, 0x20, character_slots.data()); Put(characters, 0x2C, std::int32_t{8});
    Put(character_slots, 4*0x10+8, character.data()); Put(character, 0x18, actor_id);
    Put(character, 0xB4, std::uint32_t{0});
    Put(rites, 0x20, rite_slots.data()); Put(rites, 0x2C, std::int32_t{8});
    Put(rite_slots, 8, current.data()); Put(rite_slots, 2*0x10+8, target.data());
    Put(current, 8, std::uint32_t{0}); Put(target, 8, target_id);
  }
};
Fixture *f = nullptr;
void *LocalPlayer(void *) { return f->player.data(); }
bool NativeValidate(const r::FaithAndRiteConversionCommand *command, void *raw) {
  ++f->calls;
  f->owner_called &= GetCurrentThreadId() == f->owner;
  auto &reason = *static_cast<q::NativeReasonString *>(raw);
  f->initialized_string = f->initialized_string && reason.size == 0 && reason.capacity == 15 &&
      reason.storage[0] == std::byte{0};
  f->command_shape = f->command_shape && command->primary_vtable == 0x144770340 &&
      command->secondary_vtable == 0x1447703D8 && command->actor_id == Fixture::actor_id &&
      command->target_rite_id == f->expected_target && command->pay_piety == 1;
  if (f->malformed_text) { reason.size = 16; return f->native_accepted; }
  reason.size = static_cast<std::uint64_t>(f->text.size());
  if (f->text.size() < 16) {
    std::memcpy(reason.storage.data(), f->text.c_str(), f->text.size()+1);
  } else {
    auto *heap = new char[f->text.size()+1]; ++f->allocations;
    std::memcpy(heap, f->text.c_str(), f->text.size()+1);
    std::memcpy(reason.storage.data(), &heap, sizeof(heap));
    reason.capacity = static_cast<std::uint64_t>(f->text.size());
  }
  return f->native_accepted;
}
void NativeDestroy(q::NativeReasonString *string) {
  ++f->destroys;
  if (string->capacity >= 16) {
    char *data = nullptr; std::memcpy(&data, string->storage.data(), sizeof(data));
    delete[] data; ++f->heap_destroys;
  }
  string->size = 0; string->capacity = 15; string->storage[0] = std::byte{0};
}
q::Bindings Bind(Fixture &fixture) {
  f = &fixture; q::Bindings b{};
  b.rite.enabled = true; b.rite.module_base = 0x140000000;
  b.rite.core = {true, &f->state_ptr, &f->jomini_ptr, &f->characters_ptr, &LocalPlayer};
  b.rite.rite_storage_slot = &f->rites_ptr; b.rite.validate = &NativeValidate;
  b.destroy_string = &NativeDestroy; return b;
}
} // namespace

#include <atomic>
#include <chrono>
#include <stdexcept>
#include <thread>

#if defined(XAR_RELIGION_CONVERSION_REASONS_MAILBOX_STANDALONE_ADAPTER)
namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept { return adapter; }
}
#endif
namespace {
namespace game = xar::game;
namespace api = xar::ck3_11906;
int checks = 0;
void Check(bool condition, const char *message) {
  ++checks;
  if (!condition) throw std::runtime_error(message);
}
class FrameAdapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  const DWORD owner = GetCurrentThreadId();
  mutable unsigned reads = 0;
  bool drift = false;
  game::AdapterDescriptor identity{"ck3-1.20.0.2-msvc-x64", "1.20.0.2",
      c::kExecutableSha256, "religion-fixture", {}};
  const game::AdapterDescriptor &descriptor() const noexcept override { return identity; }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    if (GetCurrentThreadId() != owner) return false;
    out = frame;
    if (++reads > 1 && drift) ++out.date_raw;
    return true;
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
  Bytes<0x28> tls{};
  std::uint8_t initialized = 1;
  std::uintptr_t unused_rng = 0;
  Pump(Fixture &fixture, api::MainThreadQueryMailboxV1 &mailbox) {
    tls[0x20] = std::byte{1}; tls_context = tls.data();
    mailbox.global_rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&unused_rng);
    mailbox.jomini_state_slot = reinterpret_cast<std::uintptr_t>(&fixture.jomini_ptr);
    mailbox.game_state_slot = reinterpret_cast<std::uintptr_t>(&fixture.state_ptr);
    mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter = &FixtureTls;
    mailbox.executor_submission_enabled = true;
    // The fixture uses the existing primary permit; central integration registers a named reasons permit.
    mailbox.permitted_executor = &c::ExecutePlayerReligionConversionReasonsMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2; ++i)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};

bool Query(Fixture &fixture, FrameAdapter &adapter, const std::filesystem::path &directory,
    const char *filename, std::uint32_t target, c::PlayerReligionConversionReasonsMailboxContext12002 &query) {
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(fixture, mailbox);
  query = {};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame; query.envelope.expected_snapshot_revision = 701;
  query.target_rite_id = target; query.bindings = Bind(fixture);
  fixture.expected_target = target;
  adapter.reads = 0;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::RunPlayerReligionConversionReasonsMailbox12002(query,
        "reasons\"mailbox-fixture", serialized, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Check(drained, "real queued reasons executor drained by fixture owner");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual mailbox reclaim");
  if (result) {
    Check(failure.empty() && query.completed && query.envelope.frame_stable && !serialized.empty(), "complete actual result");
    Check(query.observation.capture_epoch == query.envelope.execution_stamp.pump_epoch &&
          query.observation.capture_epoch != query.envelope.expected_snapshot_revision, "same pump epoch differs from revision");
    std::ofstream(directory/filename) << serialized << '\n';
  } else {
    Check(serialized.empty() && !failure.empty(), "changed published frame has no success JSON");
    std::ofstream(directory / (std::string(filename) + ".rejection.json")) <<
        "{\"success_wire_emitted\":false,\"mailbox_reclaimed\":true,\"failure\":\"" << failure << "\"}\n";
  }
  return result;
}

} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory argument"); const std::filesystem::path directory(argv[1]);
    Fixture fixture; FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::actor_id; adapter.frame.date_raw = 53175816;
    c::PlayerReligionConversionReasonsMailboxContext12002 query{};
    Check(Query(fixture, adapter, directory, "native-refusal-sso.json", Fixture::target_id, query) &&
          query.observation.available && query.observation.native_paid_validator_passes == false &&
          query.observation.raw_native_text == "Not adult." && query.observation.ui_blocker_text == "Not adult.\n",
          "real paid rejection formatter and inline buffer through owner mailbox");
    Check(fixture.initialized_string && fixture.command_shape && fixture.owner_called &&
          fixture.calls == 1 && fixture.destroys == 1 && fixture.heap_destroys == 0,
          "native constructor, paid command, owner thread and one destructor");
    fixture.text = "#N Cannot adopt \"target Rite\".#!\n知晓程度不足。\n";
    Check(Query(fixture, adapter, directory, "native-refusal-heap.json", Fixture::target_id, query) &&
          query.observation.available && query.observation.raw_native_text == fixture.text &&
          query.observation.ui_blocker_text == fixture.text && fixture.allocations == 1 &&
          fixture.heap_destroys == 1 && fixture.destroys == 2,
          "native heap formatter copied and freed through actual mailbox");
    fixture.native_accepted = true; fixture.text.clear();
    Check(Query(fixture, adapter, directory, "native-allowed-empty.json", Fixture::target_id, query) &&
          query.observation.available && query.observation.native_paid_validator_passes == true &&
          query.observation.raw_native_text == "" && query.observation.ui_blocker_text == "",
          "known empty native reasons remain available");
    fixture.text = "A native formatted explanation.";
    Check(Query(fixture, adapter, directory, "native-allowed-with-text.json", Fixture::target_id, query) &&
          query.observation.available && query.observation.native_paid_validator_passes == true &&
          query.observation.raw_native_text == fixture.text,
          "formatter text never substitutes for native boolean");
    fixture.native_accepted = false; fixture.text.clear();
    Check(Query(fixture, adapter, directory, "native-refusal-empty.json", Fixture::target_id, query) &&
          query.observation.available && query.observation.native_paid_validator_passes == false &&
          query.observation.ui_blocker_text == "", "rejection can have known empty native reasons");
    Check(Query(fixture, adapter, directory, "target-zero.json", 0, query) &&
          query.observation.available && query.observation.target_rite_id == 0,
          "legal full Rite ID zero passes through actual source");
    const int calls = fixture.calls, destroys = fixture.destroys;
    Check(Query(fixture, adapter, directory, "target-unavailable.json", 0x81000002, query) &&
          !query.observation.available && query.observation.failure == q::Failure::target_rite_unavailable &&
          !query.observation.ui_blocker_text && fixture.calls == calls && fixture.destroys == destroys &&
          query.observation.played_character_id == Fixture::actor_id,
          "unavailable full ID preserves query owner without calling formatter");
    fixture.malformed_text = true;
    Check(Query(fixture, adapter, directory, "native-text-unavailable.json", Fixture::target_id, query) &&
          !query.observation.available && query.observation.failure == q::Failure::native_text_unavailable &&
          !query.observation.native_paid_validator_passes && !query.observation.raw_native_text &&
          fixture.destroys == destroys + 1, "actual formatter read failure has typed unavailable and destructor");
    fixture.malformed_text = false;
    adapter.drift = true;
    Check(!Query(fixture, adapter, directory, "frame-drift.json", Fixture::target_id, query),
          "actual published frame change yields no command_result");
    adapter.drift = false;
    std::uint32_t target = 0; std::uint64_t revision = 0;
    Check(c::ParsePlayerReligionConversionReasonsRequest12002("{\"target_rite_id\":0}", target, revision) &&
          target == 0 && revision == 0, "required full ID zero and optional expectation");
    Check(c::ParsePlayerReligionConversionReasonsRequest12002(
          "{\"target_rite_id\":2181038082,\"expected_revision\":701}", target, revision) &&
          target == Fixture::target_id && revision == 701, "high generation ID preserved");
    Check(c::ParsePlayerReligionConversionReasonsRequest12002(
          "{\"target_rite_id\":0,\"expected_revision\":701,\"expected_snapshot_revision\":701}", target, revision),
          "matching expected revision aliases");
    Check(!c::ParsePlayerReligionConversionReasonsRequest12002(
          "{\"target_rite_id\":0,\"expected_revision\":701,\"expected_snapshot_revision\":702}", target, revision),
          "conflicting expected revisions rejected");
    for (const auto invalid : {"{}", "{\"target_rite_id\":-1}", "{\"target_rite_id\":4294967295}",
         "{\"target_rite_id\":4294967296}", "{\"target_rite_id\":0.5}", "{\"target_rite_id\":0,\"expected_revision\":0}"})
      Check(!c::ParsePlayerReligionConversionReasonsRequest12002(invalid, target, revision), "invalid request rejected");
    api::MainThreadQueryMailboxV1 mailbox{}; std::string wire, failure;
    Check(!c::HandlePlayerReligionConversionReasonsPrivate12002(adapter, mailbox, adapter.frame, 701,
          c::kPlayerReligionConversionReasonsPrivateStep12002, "{\"target_rite_id\":0,\"expected_revision\":702}",
          "stale", wire, failure) && wire.empty() &&
          failure == "player_religion_conversion_reasons_current_frame_unavailable" && mailbox.next_sequence == 0,
          "actual private handler rejects stale revision before submit");
    std::ofstream(directory/"stale-request-rejection.json") <<
        "{\"success_wire_emitted\":false,\"native_submit_sequence\":" << mailbox.next_sequence <<
        ",\"failure\":\"" << failure << "\"}\n";
    auto running = adapter.frame; running.paused = false;
    Check(!c::HandlePlayerReligionConversionReasonsPrivate12002(adapter, mailbox, running, 701,
          c::kPlayerReligionConversionReasonsPrivateStep12002, "{\"target_rite_id\":0}", "running", wire, failure) &&
          wire.empty() && mailbox.next_sequence == 0, "running published frame refused before submission");
    Check(c::IsPlayerReligionConversionReasonsPrivateStep12002(c::kPlayerReligionConversionReasonsPrivateStep12002) &&
          !c::IsPlayerReligionConversionReasonsPrivateStep12002("query-player-religion-conversion-terms-v1"),
          "distinct reasons selector");
    std::cout << "PASS checks=" << checks << " actual_core=true actual_providers=true actual_mailbox_submit_drain_wait_reclaim=true actual_wrapper=true live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
