#include "xar_bridge/ck3_12002_religion_conversion_mailbox.hpp"

#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace r = xar::ck3_12002::religion::conversion_cost;
namespace c = xar::ck3_12002;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename B, typename T> void Put(B &b, std::size_t offset, T value) {
  std::memcpy(b.data() + offset, &value, sizeof(value));
}
struct Fixture {
  Bytes<0xA8> state{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> character_db{}, rite_db{};
  Bytes<0x80> character_slots{}, rite_slots{};
  Bytes<0x1D8> character{};
  Bytes<0x120> resources{};
  Bytes<0x4C0> current_rite{}, target_rite{}, same_faith_rite{};
  Bytes<0x10> current_faith{}, target_faith{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *character_db_ptr = character_db.data(), *rite_db_ptr = rite_db.data();
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::uint32_t target_rite_id = 0xA0000002;
  static constexpr std::uint32_t same_faith_rite_id = 0xB0000003;
  static constexpr std::uint32_t current_faith_id = 0x81000001, target_faith_id = 0x82000002;
  bool command_valid = true;
  bool target_faith_missing = false;
  bool drift = false;
  int calls = 0;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(character_db, 0x20, character_slots.data()); Put(character_db, 0x2C, std::uint32_t{8});
    Put(character_slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, actor_id);
    Put(character, 0xB4, std::uint32_t{0}); Put(character, 0x1B0, resources.data());
    Put(resources, 0x110, std::int64_t{40'000'000});
    Put(current_rite, 8, std::uint32_t{0}); Put(current_rite, 0x4B8, current_faith_id);
    Put(target_rite, 8, target_rite_id); Put(target_rite, 0x4B8, target_faith_id);
    Put(same_faith_rite, 8, same_faith_rite_id); Put(same_faith_rite, 0x4B8, current_faith_id);
    Put(current_faith, 8, current_faith_id); Put(target_faith, 8, target_faith_id);
    Put(rite_db, 0x20, rite_slots.data()); Put(rite_db, 0x2C, std::uint32_t{8});
    Put(rite_slots, 8, current_rite.data()); Put(rite_slots, 2 * 0x10 + 8, target_rite.data());
    Put(rite_slots, 3 * 0x10 + 8, same_faith_rite.data());
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *CurrentRite(void *) { return f->current_rite.data(); }
void *CurrentFaith(void *) { return f->current_faith.data(); }
void *RiteFaith(void *rite) {
  return rite == f->target_rite.data() ?
      (f->target_faith_missing ? nullptr : f->target_faith.data()) : f->current_faith.data();
}
std::int32_t NativeCost(const r::NativeCostCommand *cmd, void *tooltip) {
  ++f->calls;
  bool base_zero = cmd->flags == 0;
  for (const auto b : cmd->reserved) base_zero &= b == std::byte{};
  f->command_valid &= cmd->actor_id == Fixture::actor_id &&
      cmd->pay_piety == 1 && !tooltip && base_zero &&
      cmd->primary_vtable == 0x144770340 && cmd->secondary_vtable == 0x1447703D8;
  const auto points = cmd->target_rite_id == Fixture::same_faith_rite_id ? 251 : 377;
  return points + (f->drift && f->calls % 2 == 0 ? 1 : 0);
}
r::Bindings Bind(Fixture &fixture) {
  f = &fixture; r::Bindings b{}; b.enabled = true;
  b.core = {true, &f->state_ptr, &f->jomini_ptr, &f->character_db_ptr, &Player};
  b.rite_database = &f->rite_db_ptr;
  b.character_rite = &CurrentRite; b.character_faith = &CurrentFaith; b.rite_faith = &RiteFaith;
  b.final_piety_cost = &NativeCost;
  b.command_vtable = 0x144770340; b.command_secondary_vtable = 0x1447703D8;
  return b;
}

bool allow_conversion = true;
bool NativeValidator(const xar::ck3_12002::religion_conversion_rite::FaithAndRiteConversionCommand *command, void *reasons) {
  f->command_valid &= !reasons && command->actor_id == Fixture::actor_id &&
      command->primary_vtable == 0x144770340 && command->secondary_vtable == 0x1447703D8;
  return allow_conversion && (command->pay_piety == 0 ||
      *reinterpret_cast<const std::int64_t *>(f->resources.data() + 0x110) >= 37'700'000);
}
const void *FaithRites(void *) { return f->current_faith.data(); }
xar::ck3_12002::religion_conversion::terms::Bindings BindTerms(Fixture &fixture) {
  auto cost_bindings = Bind(fixture);
  xar::ck3_12002::religion_conversion_rite::Bindings gate{};
  gate.enabled = true; gate.module_base = 0x140000000; gate.core = cost_bindings.core;
  gate.rite_storage_slot = cost_bindings.rite_database;
  gate.validate = &NativeValidator; gate.character_faith = &CurrentFaith;
  gate.faith_rites = &FaithRites;
  return {gate, cost_bindings};
}
} // namespace

#include <atomic>
#include <chrono>
#include <thread>
#include <stdexcept>

namespace t = xar::ck3_12002::religion_conversion::terms;
#if defined(XAR_RELIGION_MAILBOX_STANDALONE_ADAPTER)
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
    // The central owner registers a named conversion permit; fixture uses the existing primary permit.
    mailbox.permitted_executor = &c::ExecutePlayerReligionConversionTermsMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2; ++i)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};

bool Query(Fixture &fixture, FrameAdapter &adapter, const std::filesystem::path &directory,
           const char *filename, std::uint32_t target_id, t::Terms &observed) {
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(fixture, mailbox);
  c::PlayerReligionConversionTermsMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 701;
  query.bindings = BindTerms(fixture);
  query.target_rite_id = target_id;
  adapter.reads = 0;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::RunPlayerReligionConversionTermsMailbox12002(query, "religion-conversion\"mailbox-fixture", serialized, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Check(drained, "real queued executor drained on fixture owner");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual mailbox reclaimed");
  observed = query.observation;
  if (result) {
    Check(failure.empty() && query.completed && query.envelope.frame_stable && !serialized.empty(), "serialized-ready actual result");
    Check(query.observation.capture_epoch == query.envelope.execution_stamp.pump_epoch &&
          query.observation.capture_epoch != query.envelope.expected_snapshot_revision, "epoch differs from published revision");
    std::ofstream(directory / filename) << serialized << '\n';
  } else Check(serialized.empty() && !failure.empty(), "unstable query has no success JSON");
  return result;
}
} // namespace


int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory");
    const std::filesystem::path directory(argv[1]);
    Fixture fixture; FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::actor_id;
    adapter.frame.date_raw = 53175816;
    t::Terms observed{};
    Check(Query(fixture, adapter, directory, "permitted.json", Fixture::target_rite_id, observed) &&
          observed.available && observed.can_convert == true && observed.cost.piety_points == 377 &&
          observed.cost.can_afford_piety == true && fixture.command_valid,
          "actual paid native final gate and independently evaluated current cost");
    allow_conversion = false;
    Check(Query(fixture, adapter, directory, "native-rule-rejected.json", Fixture::target_rite_id, observed) &&
          observed.available && observed.can_convert == false && observed.cost.can_afford_piety == true,
          "enough piety cannot override a real native rule rejection");
    allow_conversion = true; Put(fixture.resources, 0x110, std::int64_t{37'699'999});
    Check(Query(fixture, adapter, directory, "piety-short.json", Fixture::target_rite_id, observed) &&
          observed.available && observed.can_convert == false &&
          observed.final_gate.validator_without_payment && !observed.final_gate.validator_with_payment &&
          observed.cost.can_afford_piety == false,
          "unpaid diagnostic does not become paid conversion permission");
    Put(fixture.resources, 0x110, std::int64_t{40'000'000});
    Check(Query(fixture, adapter, directory, "current-rite.json", 0, observed) &&
          observed.available && observed.can_convert == false &&
          observed.final_gate.validator_with_payment && !observed.final_gate.different_from_current_rite,
          "native entry target-identity gate prevents current Rite from being selectable");
    Check(Query(fixture, adapter, directory, "target-unavailable.json", 0xA1000002, observed) &&
          !observed.available && !observed.can_convert &&
          observed.final_gate.failure == c::religion_conversion_rite::Failure::target_rite_unavailable &&
          observed.played_character_id == Fixture::actor_id,
          "typed unavailable target keeps actual published query frame");
    fixture.target_faith_missing = true;
    Check(Query(fixture, adapter, directory, "cost-unavailable.json", Fixture::target_rite_id, observed) &&
          !observed.available && !observed.can_convert && observed.failure == t::Failure::cost_unavailable,
          "final gate alone cannot hide a failed evaluated cost");
    fixture.target_faith_missing = false;
    adapter.drift = true;
    Check(!Query(fixture, adapter, directory, "frame-drift.json", Fixture::target_rite_id, observed),
          "actual owning query frame drift does not emit success JSON");
    adapter.drift = false;
    std::uint32_t target = 0; std::uint64_t revision = 0;
    Check(c::ParsePlayerReligionConversionTermsRequest12002("{\"target_rite_id\":0}", target, revision) &&
          target == 0 && revision == 0, "legal zero full ID and optional expectation");
    Check(c::ParsePlayerReligionConversionTermsRequest12002(
          "{\"target_rite_id\":2684354562,\"expected_revision\":701}", target, revision) &&
          target == Fixture::target_rite_id && revision == 701, "high generation full Rite ID preserved");
    Check(c::ParsePlayerReligionConversionTermsRequest12002(
          "{\"target_rite_id\":0,\"expected_snapshot_revision\":701,\"expected_revision\":701}", target, revision),
          "matching expectation aliases");
    Check(!c::ParsePlayerReligionConversionTermsRequest12002(
          "{\"target_rite_id\":0,\"expected_snapshot_revision\":701,\"expected_revision\":702}", target, revision),
          "actual request conflicting aliases");
    Check(!c::ParsePlayerReligionConversionTermsRequest12002("{}", target, revision) &&
          !c::ParsePlayerReligionConversionTermsRequest12002("{\"target_rite_id\":4294967295}", target, revision) &&
          !c::ParsePlayerReligionConversionTermsRequest12002("{\"target_rite_id\":4294967296}", target, revision),
          "missing absent and wider-than-full ID rejected before native read");
    api::MainThreadQueryMailboxV1 mailbox{};
    std::string wire, failure;
    Check(!c::HandlePlayerReligionConversionTermsPrivate12002(adapter, mailbox, adapter.frame, 701,
          c::kPlayerReligionConversionTermsPrivateStep12002,
          "{\"target_rite_id\":0,\"expected_revision\":702}", "stale", wire, failure) &&
          wire.empty() && failure == "player_religion_conversion_terms_current_frame_unavailable" &&
          mailbox.next_sequence == 0, "actual handler uses revision before native submission");
    Check(c::IsPlayerReligionConversionTermsPrivateStep12002(c::kPlayerReligionConversionTermsPrivateStep12002) &&
          !c::IsPlayerReligionConversionTermsPrivateStep12002("query-player-religion-context-v1"),
          "conversion terms uses exact distinct selector");
    std::cout << "PASS checks=" << checks << " cases=7 actual_core=true actual_provider=true actual_mailbox_submit_drain_wait_reclaim=true actual_wrapper=true live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
