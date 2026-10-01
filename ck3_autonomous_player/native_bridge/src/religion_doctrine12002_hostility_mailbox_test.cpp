#include "xar_bridge/religion_doctrine12002_hostility_mailbox.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace d = xar::ck3_12002::religion::doctrine12002;
namespace r = xar::ck3_12002::religion;
namespace c = xar::ck3_12002;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename Buffer, typename T> void Put(Buffer &buffer, std::size_t at, T value) {
  std::memcpy(buffer.data() + at, &value, sizeof(value));
}
template <typename T> T Get(const void *object, std::size_t at) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(object) + at, sizeof(value)); return value;
}
struct Fixture {
  Bytes<0xA8> state{}; Bytes<0x28> jomini{}; Bytes<0x1F8> players{}; Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{}; std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> character_storage{}, rite_storage{};
  Bytes<0x80> character_slots{}, rite_slots{};
  Bytes<0x1D8> character{};
  Bytes<0x900> actor_rite{}, target_rite{}, actor_main{}, target_main{};
  Bytes<0x320> actor_faith{}, target_faith{};
  Bytes<0x40> actor_religion{}, target_religion{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *character_storage_ptr = character_storage.data(), *rite_storage_ptr = rite_storage.data();
  static constexpr std::int32_t character_id = 0x03000004;
  static constexpr std::uint32_t actor_rite_id = 0x02000001, target_rite_id = 0x83000002;
  static constexpr std::uint32_t actor_faith_id = 0x82000003, target_faith_id = 0x83000004;
  static constexpr std::uint32_t actor_main_id = 0x04000005, target_main_id = 0x06000006;
  static constexpr std::uint32_t actor_religion_id = 0x87000001, target_religion_id = 0x88000002;
  std::uint8_t forward_rite = 2, reverse_rite = 0, forward_faith = 3, reverse_faith = 1;
  int rite_calls = 0, faith_calls = 0;
  bool bad_call = false, drift = false;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, character_id);
    Put(character_storage, 0x20, character_slots.data()); Put(character_storage, 0x2C, std::int32_t{8});
    Put(character_slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, character_id);
    Put(character, r::kCharacterRiteIdOffset, actor_rite_id);
    Put(rite_storage, 0x20, rite_slots.data()); Put(rite_storage, 0x2C, std::uint32_t{8});
    Put(rite_slots, 1 * 0x10 + 8, actor_rite.data()); Put(rite_slots, 2 * 0x10 + 8, target_rite.data());
    Put(rite_slots, 5 * 0x10 + 8, actor_main.data()); Put(rite_slots, 6 * 0x10 + 8, target_main.data());
    Rite(actor_rite, actor_rite_id, actor_faith_id); Rite(target_rite, target_rite_id, target_faith_id);
    Rite(actor_main, actor_main_id, actor_faith_id); Rite(target_main, target_main_id, target_faith_id);
    Faith(actor_faith, actor_faith_id, actor_religion_id, actor_main_id);
    Faith(target_faith, target_faith_id, target_religion_id, target_main_id);
    Put(actor_religion, 8, actor_religion_id); Put(target_religion, 8, target_religion_id);
  }
  static void Rite(Bytes<0x900> &rite, std::uint32_t id, std::uint32_t faith) {
    Put(rite, 8, id); Put(rite, 0x0C, d::kHostilityRiteTypeTag); Put(rite, r::kRiteFaithIdOffset, faith);
  }
  static void Faith(Bytes<0x320> &faith, std::uint32_t id, std::uint32_t religion, std::uint32_t main) {
    Put(faith, 8, id); Put(faith, r::kFaithReligionIdOffset, religion); Put(faith, r::kFaithMainRiteIdOffset, main);
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *CharacterRite(void *) { return f->actor_rite.data(); }
void *CharacterFaith(void *) { return f->actor_faith.data(); }
void *RiteFaith(void *rite) {
  return Get<std::uint32_t>(rite, r::kRiteFaithIdOffset) == Fixture::actor_faith_id ?
      f->actor_faith.data() : f->target_faith.data();
}
void *FaithReligion(void *faith) {
  return Get<std::uint32_t>(faith, r::kFaithReligionIdOffset) == Fixture::actor_religion_id ?
      f->actor_religion.data() : f->target_religion.data();
}
void *FaithMain(void *faith) { return faith == f->actor_faith.data() ? f->actor_main.data() : f->target_main.data(); }
std::uint8_t RiteLevel(void *component, void *source, void *target) {
  ++f->rite_calls;
  if (component != static_cast<std::byte *>(source) + d::kHostilityRiteComponentOffset ||
      (source != f->actor_rite.data() && source != f->target_rite.data()) ||
      (target != f->actor_rite.data() && target != f->target_rite.data())) f->bad_call = true;
  if (Get<std::uint32_t>(source, r::kRiteFaithIdOffset) == Get<std::uint32_t>(target, r::kRiteFaithIdOffset)) return 0;
  if (f->drift && f->rite_calls == 3) return 1;
  return source == f->actor_rite.data() ? f->forward_rite : f->reverse_rite;
}
std::uint8_t FaithLevel(void *source, void *target, bool offset) {
  ++f->faith_calls;
  if (offset || (source != f->actor_faith.data() && source != f->target_faith.data()) ||
      (target != f->actor_faith.data() && target != f->target_faith.data())) f->bad_call = true;
  if (source == target) return 0;
  return source == f->actor_faith.data() ? f->forward_faith : f->reverse_faith;
}
d::HostilityBindings Bind(Fixture &fixture) {
  f = &fixture;
  d::HostilityBindings b{}; b.enabled = true; b.context.enabled = true;
  b.context.core = {true, &f->state_ptr, &f->jomini_ptr, &f->character_storage_ptr, &Player};
  b.context.character_rite = &CharacterRite; b.context.character_faith = &CharacterFaith;
  b.context.rite_faith = &RiteFaith; b.context.faith_religion = &FaithReligion; b.context.faith_main_rite = &FaithMain;
  b.rite_storage_slot = &f->rite_storage_ptr; b.rite_hostility = &RiteLevel; b.faith_hostility = &FaithLevel;
  return b;
}
} // namespace

#include <atomic>
#include <chrono>
#include <thread>
#include <stdexcept>

#if defined(XAR_HOSTILITY_MAILBOX_STANDALONE_ADAPTER)
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
      c::kExecutableSha256, "hostility-fixture", {}};
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
    // Standalone fixture uses the existing primary permit. Central integration
    // registers permitted_executor_religion_hostility12002 in the next build.
    mailbox.permitted_executor = &c::ExecutePlayerReligionHostilityMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2; ++i)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};


bool Query(Fixture &fixture, FrameAdapter &adapter, const std::filesystem::path &directory,
           const char *filename, std::string_view payload, d::HostilityObservation &observed) {
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(fixture, mailbox);
  c::PlayerReligionHostilityMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 701;
  query.bindings = Bind(fixture);
  std::uint64_t expectation = 0;
  Check(c::ParsePlayerReligionHostilityRequest12002(payload, query.target_rite_id, expectation), "actual request parser");
  Check(expectation == 0 || expectation == 701, "fixture matches requested revision");
  adapter.reads = 0;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::RunPlayerReligionHostilityMailbox12002(query, "hostility\"mailbox-fixture", serialized, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Check(drained, "actual queued executor drained on fixture owner");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual mailbox reclaimed");
  observed = query.observation;
  if (result) {
    Check(failure.empty() && query.completed && query.envelope.frame_stable && !serialized.empty(), "actual command result ready");
    Check(query.observation.capture_epoch == query.envelope.execution_stamp.pump_epoch &&
          query.observation.capture_epoch != query.envelope.expected_snapshot_revision, "actual epoch differs from revision");
    std::ofstream(directory / filename) << serialized << '\n';
  } else Check(serialized.empty() && !failure.empty(), "unstable request produces no success packet");
  return result;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory argument");
    const std::filesystem::path directory(argv[1]);
    Fixture fixture; FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::character_id;
    adapter.frame.date_raw = Get<std::int32_t>(fixture.state.data(), 8);
    d::HostilityObservation observed{};
    constexpr std::string_view request = "{\"target_rite_id\":2197815298,\"expected_snapshot_revision\":701}";
    Check(Query(fixture, adapter, directory, "asymmetric.json", request, observed) && observed.available &&
          observed.target_rite_id == Fixture::target_rite_id &&
          observed.actor_rite_towards_target == d::HostilityLevel::hostile &&
          observed.target_rite_towards_actor == d::HostilityLevel::righteous &&
          observed.actor_faith_towards_target == d::HostilityLevel::evil &&
          observed.target_faith_towards_actor == d::HostilityLevel::astray,
          "actual full-direction provider through mailbox");
    Check(!fixture.bad_call && observed.actor_rite_id != observed.actor_main_rite_id,
          "source is played actor; main Rite is independent; Faith offset false");
    Put(fixture.target_rite, r::kRiteFaithIdOffset, Fixture::actor_faith_id);
    Check(Query(fixture, adapter, directory, "same-faith.json", request, observed) && observed.same_faith == true &&
          observed.actor_rite_towards_target == d::HostilityLevel::righteous &&
          observed.actor_faith_towards_target == d::HostilityLevel::righteous &&
          observed.actor_rite_id != observed.target_rite_id, "same Faith different personal Rites");
    Put(fixture.target_rite, r::kRiteFaithIdOffset, Fixture::target_faith_id);
    Put(fixture.target_rite, 8, std::uint32_t{0}); Put(fixture.rite_slots, 8, fixture.target_rite.data());
    Check(Query(fixture, adapter, directory, "zero-target-id.json", "{\"target_rite_id\":0}", observed) &&
          observed.available && observed.target_rite_id == 0U, "required full target reference zero is legal");
    Put(fixture.target_rite, 8, Fixture::target_rite_id);
    Check(Query(fixture, adapter, directory, "target-unavailable.json", "{\"target_rite_id\":2181038082,\"expected_revision\":701}", observed) &&
          !observed.available && observed.failure == d::HostilityFailure::target_rite_unavailable &&
          !observed.actor_rite_towards_target && observed.played_character_id == Fixture::character_id &&
          observed.date_raw == adapter.frame.date_raw, "unavailable target keeps observed frame and nullable levels");
    fixture.forward_rite = 4;
    Check(Query(fixture, adapter, directory, "native-sentinel.json", request, observed) &&
          !observed.available && observed.failure == d::HostilityFailure::native_level_unavailable &&
          !observed.actor_rite_towards_target, "native invalid sentinel is unavailable packet");
    fixture.forward_rite = 2; adapter.drift = true;
    Check(!Query(fixture, adapter, directory, "frame-drift.json", request, observed), "actual owner frame changed after capture");
    adapter.drift = false;
    std::uint32_t target = r::kAbsentReference; std::uint64_t revision = 0;
    Check(!c::ParsePlayerReligionHostilityRequest12002("{}", target, revision), "required target field");
    Check(!c::ParsePlayerReligionHostilityRequest12002("{\"target_rite_id\":4294967296}", target, revision), "uint32 target bound");
    Check(c::ParsePlayerReligionHostilityRequest12002("{\"target_rite_id\":0,\"expected_snapshot_revision\":701,\"expected_revision\":701}", target, revision) &&
          target == 0U && revision == 701, "matching revision aliases and zero target");
    Check(!c::ParsePlayerReligionHostilityRequest12002("{\"target_rite_id\":0,\"expected_snapshot_revision\":701,\"expected_revision\":702}", target, revision),
          "different revision aliases");
    api::MainThreadQueryMailboxV1 mailbox{}; std::string wire, failure;
    Check(!c::HandlePlayerReligionHostilityPrivate12002(adapter, mailbox, adapter.frame, 701,
          c::kPlayerReligionHostilityPrivateStep12002, "{\"target_rite_id\":0,\"expected_revision\":702}", "stale", wire, failure) &&
          wire.empty() && failure == "player_religion_hostility_current_frame_unavailable" && mailbox.next_sequence == 0,
          "actual handler stale request before submission");
    Check(!c::HandlePlayerReligionHostilityPrivate12002(adapter, mailbox, adapter.frame, 701,
          c::kPlayerReligionHostilityPrivateStep12002, "{}", "missing", wire, failure) &&
          wire.empty() && failure == "player_religion_hostility_request_invalid" && mailbox.next_sequence == 0,
          "actual handler missing target before submission");
    Check(c::IsPlayerReligionHostilityPrivateStep12002(c::kPlayerReligionHostilityPrivateStep12002) &&
          !c::IsPlayerReligionHostilityPrivateStep12002("query-player-religion-context-v1"), "exact hostility selector");
    std::cout << "PASS checks=" << checks << " actual_provider=true actual_mailbox_submit_drain_wait_reclaim=true actual_command_result=true live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
