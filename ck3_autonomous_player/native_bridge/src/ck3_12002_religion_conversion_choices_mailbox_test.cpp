#include "xar_bridge/ck3_12002_religion_conversion_choices_mailbox.hpp"
#include <atomic>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <thread>
#include <vector>

namespace c = xar::ck3_12002;
namespace faith = c::religion_conversion::faith;
namespace rite = c::religion_conversion_rite;
#if defined(XAR_RELIGION_MAILBOX_STANDALONE_ADAPTER)
namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept { return adapter; }
}
#endif
namespace {
namespace game = xar::game;
namespace api = xar::ck3_11906;
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename B, typename T> void Put(B &b, std::size_t offset, T value) {
  std::memcpy(b.data() + offset, &value, sizeof(value));
}
struct Fixture {
  Bytes<0xA8> state{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> world = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> character_storage{}, faith_storage{}, rite_storage{};
  Bytes<0x80> character_slots{}, faith_slots{}, rite_slots{};
  Bytes<0x1D8> actor{};
  Bytes<0x120> current_faith{}, target_faith{};
  Bytes<0x4C0> current_rite{}, target_rite{}, sibling_rite{};
  std::array<void *, 2> faiths{current_faith.data(), target_faith.data()};
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::uint32_t current_faith_id = 0x81000002u, target_faith_id = 0x83000003u;
  static constexpr std::uint32_t target_rite_id = 0x84000001u, sibling_rite_id = 0xB0000003u;
  std::array<std::uint32_t, 2> current_rite_ids{0, sibling_rite_id};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *character_storage_ptr = character_storage.data(), *faith_storage_ptr = faith_storage.data();
  void *rite_storage_ptr = rite_storage.data();
  bool invocation_ok = true;
  int rule_calls = 0, validator_calls = 0;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, world.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(world, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(world, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(character_storage, 0x20, character_slots.data()); Put(character_storage, 0x2C, std::int32_t{8});
    Put(character_slots, 4 * 16 + 8, actor.data()); Put(actor, 0x18, actor_id); Put(actor, 0xB4, std::uint32_t{0});
    Put(faith_storage, 0x20, faith_slots.data()); Put(faith_storage, 0x2C, std::int32_t{8});
    Put(faith_slots, 2 * 16 + 8, current_faith.data()); Put(faith_slots, 3 * 16 + 8, target_faith.data());
    Put(current_faith, 8, current_faith_id); Put(target_faith, 8, target_faith_id);
    Put(current_faith, 0x98, std::uint32_t{0}); Put(target_faith, 0x98, target_rite_id);
    Put(current_faith, 0x20, current_rite_ids.data());
    Put(current_faith, 0x28, std::int32_t{2}); Put(current_faith, 0x2C, std::int32_t{2});
    Put(current_rite, 8, std::uint32_t{0}); Put(target_rite, 8, target_rite_id); Put(sibling_rite, 8, sibling_rite_id);
    Put(current_rite, 0x4B8, current_faith_id); Put(target_rite, 0x4B8, target_faith_id);
    Put(sibling_rite, 0x4B8, current_faith_id);
    Put(rite_storage, 0x20, rite_slots.data()); Put(rite_storage, 0x2C, std::int32_t{8});
    Put(rite_slots, 8, current_rite.data()); Put(rite_slots, 16 + 8, target_rite.data());
    Put(rite_slots, 3 * 16 + 8, sibling_rite.data());
    Put(world, faith::kWorldFaithsOffset, faiths.data()); Put(world, faith::kWorldFaithCountOffset, std::int32_t{2});
    NativeTag(current_faith, "current"); NativeTag(target_faith, "target\"faith");
  }
  static void NativeTag(Bytes<0x120> &object, std::string_view value) {
    std::memcpy(object.data() + 0xE0, value.data(), value.size());
    Put(object, 0xF0, static_cast<std::uint64_t>(value.size())); Put(object, 0xF8, std::uint64_t{15});
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *CurrentFaith(void *) { return f->current_faith.data(); }
void *MainRite(void *object) { return object == f->current_faith.data() ? f->current_rite.data() : f->target_rite.data(); }
void *RiteFaith(void *object) { return object == f->target_rite.data() ? f->target_faith.data() : f->current_faith.data(); }
const void *Tag(void *object) { return static_cast<const std::byte *>(object) + 0xE0; }
const void *FaithRites(void *object) { return static_cast<const std::byte *>(object) + 0x20; }
bool NativeFaithRule(void *actor, std::uint32_t target, void *reasons) {
  ++f->rule_calls;
  f->invocation_ok &= actor == f->actor.data() && !reasons &&
      (target == Fixture::current_faith_id || target == Fixture::target_faith_id);
  return target == Fixture::target_faith_id;
}
bool UnusedValidator(const rite::FaithAndRiteConversionCommand *, void *) { ++f->validator_calls; return false; }
void Bind(Fixture &fixture, c::PlayerReligionConversionChoicesMailboxContext12002 &query) {
  f = &fixture;
  auto &a = query.faith_bindings; a.enabled = true;
  a.core = {true, &f->state_ptr, &f->jomini_ptr, &f->character_storage_ptr, &Player};
  a.faith_storage_slot = &f->faith_storage_ptr; a.character_faith = &CurrentFaith;
  a.faith_main_rite = &MainRite; a.rite_faith = &RiteFaith; a.faith_tag = &Tag; a.conversion_rule = &NativeFaithRule;
  auto &b = query.rite_bindings; b.enabled = true; b.module_base = 0x140000000; b.core = a.core;
  b.rite_storage_slot = &f->rite_storage_ptr; b.validate = &UnusedValidator;
  b.character_faith = &CurrentFaith; b.faith_rites = &FaithRites;
}
int checks = 0;
void Check(bool condition, const char *message) {
  ++checks; if (!condition) throw std::runtime_error(message);
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
    mailbox.tls_context_getter = &FixtureTls; mailbox.executor_submission_enabled = true;
    mailbox.permitted_executor_religion_conversion_choices12002 = &c::ExecutePlayerReligionConversionChoicesMailbox12002;
    mailbox.iat_hook_installed = true; mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2; ++i)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};
bool Query(Fixture &fixture, FrameAdapter &adapter, const std::filesystem::path &directory,
           const char *filename, bool faith_enabled, bool rites_enabled,
           c::PlayerReligionConversionChoicesSnapshot12002 &observed) {
  api::MainThreadQueryMailboxV1 mailbox{}; Pump pump(fixture, mailbox);
  c::PlayerReligionConversionChoicesMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame; query.envelope.expected_snapshot_revision = 801;
  Bind(fixture, query); query.faith_bindings.enabled = faith_enabled; query.rite_bindings.enabled = rites_enabled;
  adapter.reads = 0;
  std::atomic<bool> done{false}; bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::RunPlayerReligionConversionChoicesMailbox12002(query, "religion-choices\"mailbox-fixture", serialized, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Check(drained, "actual queued callback drained on owner");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual mailbox reclaimed");
  observed = query.observation;
  if (result) {
    Check(failure.empty() && query.completed && query.envelope.frame_stable && !serialized.empty(), "actual serialized result");
    Check(observed.capture_epoch == query.envelope.execution_stamp.pump_epoch && observed.capture_epoch != 801,
          "capture epoch is actual owner pump, not published revision");
    std::ofstream(directory / filename) << serialized << '\n';
  } else Check(serialized.empty() && !failure.empty(), "unstable published query does not serialize success");
  return result;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory"); const std::filesystem::path directory(argv[1]);
    Fixture fixture; FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::actor_id; adapter.frame.date_raw = 53175816;
    c::PlayerReligionConversionChoicesSnapshot12002 observed;
    Check(Query(fixture, adapter, directory, "choices.json", true, true, observed) && observed.available &&
          observed.faith_choices.choices.size() == 2 && observed.current_faith_rites.rite_ids.size() == 2 &&
          observed.faith_choices.choices[1].faith_id == Fixture::target_faith_id &&
          observed.faith_choices.choices[1].main_rite_id == Fixture::target_rite_id &&
          observed.current_faith_rites.rite_ids[0] == 0 && fixture.invocation_ok && fixture.validator_calls == 0,
          "actual component rows/full IDs and membership never inferred as final legality");
    Put(fixture.world, faith::kWorldFaithCountOffset, std::int32_t{0}); Put(fixture.current_faith, 0x2C, std::int32_t{0});
    Check(Query(fixture, adapter, directory, "empty.json", true, true, observed) && observed.available &&
          observed.faith_choices.choices.empty() && observed.current_faith_rites.rite_ids.empty(), "known empty observed");
    Put(fixture.world, faith::kWorldFaithCountOffset, std::int32_t{2}); Put(fixture.current_faith, 0x2C, std::int32_t{2});
    Check(Query(fixture, adapter, directory, "faith-unavailable.json", false, true, observed) && !observed.available &&
          !observed.faith_choices.available && observed.current_faith_rites.available &&
          observed.unavailable_reason == "faith_choices_unavailable", "typed Faith component failure preserves actual Rite observations");
    Check(Query(fixture, adapter, directory, "rites-unavailable.json", true, false, observed) && !observed.available &&
          observed.faith_choices.available && !observed.current_faith_rites.available &&
          observed.unavailable_reason == "current_faith_rites_unavailable", "typed Rite failure preserves actual Faith observations");
    Check(Query(fixture, adapter, directory, "both-unavailable.json", false, false, observed) && !observed.available &&
          !observed.faith_choices.available && !observed.current_faith_rites.available &&
          observed.faith_choices.date_raw == adapter.frame.date_raw && observed.current_faith_rites.date_raw == adapter.frame.date_raw,
          "both failed components still carry actual published frame");
    Put(fixture.state, 8, std::int32_t{53175817});
    Check(!Query(fixture, adapter, directory, "source-mismatch.json", true, true, observed),
          "native pump date differing from published frame is refused before observation");
    Put(fixture.state, 8, std::int32_t{53175816}); adapter.drift = true;
    Check(!Query(fixture, adapter, directory, "published-drift.json", true, true, observed), "full published frame changes during capture");
    adapter.drift = false;
    std::uint64_t revision = 0;
    Check(c::ParsePlayerReligionConversionChoicesRequest12002("{}", revision) && revision == 0, "optional expected frame");
    Check(c::ParsePlayerReligionConversionChoicesRequest12002("{\"expected_revision\":801}", revision) && revision == 801, "revision alias");
    Check(c::ParsePlayerReligionConversionChoicesRequest12002("{\"expected_snapshot_revision\":801,\"expected_revision\":801}", revision), "matching aliases");
    Check(!c::ParsePlayerReligionConversionChoicesRequest12002("{\"expected_snapshot_revision\":801,\"expected_revision\":802}", revision) &&
          !c::ParsePlayerReligionConversionChoicesRequest12002("{\"expected_revision\":0}", revision), "conflicting or zero explicit expectation");
    Check(!c::ParsePlayerReligionConversionChoicesRequest12002("{\"actor_id\":4}", revision) &&
          !c::ParsePlayerReligionConversionChoicesRequest12002("{\"target_rite_id\":0}", revision), "no actor or target parameters");
    api::MainThreadQueryMailboxV1 mailbox{}; std::string wire, failure;
    Check(!c::HandlePlayerReligionConversionChoicesPrivate12002(adapter, mailbox, adapter.frame, 801,
          c::kPlayerReligionConversionChoicesPrivateStep12002, "{\"expected_revision\":802}", "stale", wire, failure) &&
          wire.empty() && failure == "player_religion_conversion_choices_current_frame_unavailable" && mailbox.next_sequence == 0,
          "actual handler rejects stale revision before submission");
    Check(c::IsPlayerReligionConversionChoicesPrivateStep12002(c::kPlayerReligionConversionChoicesPrivateStep12002) &&
          !c::IsPlayerReligionConversionChoicesPrivateStep12002("query-player-religion-conversion-terms-v1"), "distinct exact selector");
    std::cout << "PASS checks=" << checks << " cases=7 actual_core=true actual_components=true actual_submit_drain_wait_reclaim=true actual_wrapper=true live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
