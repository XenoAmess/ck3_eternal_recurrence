#include "xar_bridge/conversion_outcome12002_mailbox.hpp"
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
namespace r = c::religion;
namespace o = c::religion_conversion::outcome;
namespace state = o::state;
#if defined(XAR_RELIGION_MAILBOX_STANDALONE_ADAPTER)
namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept { return adapter; }
}
#endif
namespace {
namespace game = xar::game;
namespace api = xar::ck3_11906;
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename Buffer, typename T> void Put(Buffer &bytes, std::size_t at, T value) {
  std::memcpy(bytes.data() + at, &value, sizeof(value));
}
template <typename T> T Get(const void *object, std::size_t at) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(object) + at, sizeof(value)); return value;
}
struct Fixture {
  Bytes<0xA8> state{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> storage{};
  Bytes<0x80> slots{};
  Bytes<0x1D8> character{};
  Bytes<0x500> rite{}, main_rite{}, wrong_faith{};
  Bytes<0x320> faith{};
  Bytes<0x40> religion{};
  Bytes<0x50> religion_definition{};
  Bytes<0xB0> extension{};
  Bytes<0x308> resources{};
  Bytes<0x30> rite_storage{}, flag_set{};
  Bytes<0x28> atom_pool{};
  Bytes<0x80> rite_slots{};
  Bytes<0x40> flag_rows{};
  void *rite_storage_ptr = rite_storage.data();
  bool native_invocations_ok = true;
  int knowledge_calls = 0, lookup_calls = 0;
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  static constexpr std::int32_t character_id = 0x03000004;
  static constexpr std::uint32_t faith_id = 0x83000003, religion_id = 0x84000005;
  std::int64_t fallback_value = 7654321;
  int fallback_calls = 0, fervor_calls = 0;
  bool bad_faith = false, missing_rite = false, bad_fervor = false, drift = false;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, character_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, character_id);
    Put(character, r::kCharacterRiteIdOffset, std::uint32_t{0});
    Put(character, 0x1C8, extension.data());
    Put(rite, 8, std::uint32_t{0}); Put(rite, r::kRiteFaithIdOffset, faith_id);
    Put(main_rite, 8, std::uint32_t{0x84000001u});
    Put(faith, 8, faith_id); Put(faith, r::kFaithReligionIdOffset, religion_id);
    Put(faith, r::kFaithMainRiteIdOffset, std::uint32_t{0x84000001u});
    Put(faith, 0x2F8, std::int64_t{0}); Put(extension, 0xA0, std::int64_t{0});
    Put(religion, 8, religion_id); Put(religion, 0x10, std::int32_t{7});
    Put(religion, 0x20, religion_definition.data());
    Put(character, 0x1B0, resources.data());
    Put(resources, 0x100, std::int64_t{-123456}); Put(resources, 0x130, std::int64_t{-7654321});
    Put(resources, 0x110, std::int64_t{0}); Put(resources, 0x300, std::int64_t{456789});
    Put(extension, 0xA0, std::int64_t{345678});
    Put(rite_storage, 0x20, rite_slots.data()); Put(rite_storage, 0x2C, std::int32_t{8});
    Put(rite_slots, 8, rite.data()); Put(rite_slots, 16 + 8, main_rite.data());
    Put(main_rite, r::kRiteFaithIdOffset, faith_id);
    Put(flag_set, 0x10, flag_rows.data()); Put(flag_set, 0x1C, std::int32_t{2});
    Put(flag_set, 0x28, std::int32_t{150});
    Put(atom_pool, 0x10, flag_rows.data()); Put(atom_pool, 0x1C, std::int32_t{3});
    Put(flag_rows, 8, std::uint32_t{101}); Put(flag_rows, 0x0C, std::int32_t{200});
    Put(flag_rows, 0x20 + 8, std::uint32_t{103}); Put(flag_rows, 0x20 + 0x0C, std::int32_t{-1});
    Tag(faith, 0xE0, "faith\"key"); Tag(religion_definition, 0x28, "christianity");
  }
  template <typename Buffer> static void Tag(Buffer &object, std::size_t at, std::string_view value) {
    std::memcpy(object.data() + at, value.data(), value.size());
    Put(object, at + 0x10, static_cast<std::uint64_t>(value.size()));
    Put(object, at + 0x18, std::uint64_t{15});
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *CharacterRite(void *) { return f->missing_rite ? nullptr : Get<std::uint32_t>(f->character.data(), 0xB4) == 0 ? f->rite.data() : f->main_rite.data(); }
void *CharacterFaith(void *) { return f->bad_faith ? f->wrong_faith.data() : f->faith.data(); }
void *RiteFaith(void *) { return f->faith.data(); }
void *FaithReligion(void *) { return f->religion.data(); }
void *FaithMainRite(void *) { return f->main_rite.data(); }
std::int64_t *Fervor(void *faith, std::int64_t *out) {
  if (f->bad_fervor) return nullptr;
  *out = Get<std::int64_t>(faith, 0x2F8);
  if (f->drift && (++f->fervor_calls % 2 == 0)) ++*out;
  return out;
}
std::int64_t *Fulfillment(void *character, std::int64_t *out) {
  const auto *extension = Get<const void *>(character, 0x1C8);
  if (extension) *out = Get<std::int64_t>(extension, 0xA0);
  else { ++f->fallback_calls; *out = f->fallback_value; }
  return out;
}
const void *FaithTag(void *faith) { return static_cast<const std::byte *>(faith) + 0xE0; }
const void *ReligionTag(void *religion) {
  return static_cast<const std::byte *>(Get<const void *>(religion, 0x20)) + 0x28;
}
r::Bindings Bind(Fixture &fixture) {
  f = &fixture;
  r::Bindings b{}; b.enabled = true;
  b.core = {true, &f->state_ptr, &f->jomini_ptr, &f->storage_ptr, &Player};
  b.character_rite = &CharacterRite; b.character_faith = &CharacterFaith;
  b.rite_faith = &RiteFaith; b.faith_religion = &FaithReligion; b.faith_main_rite = &FaithMainRite;
  b.faith_fervor = &Fervor; b.character_spiritual_fulfillment = &Fulfillment;
  b.faith_tag = &FaithTag; b.religion_tag = &ReligionTag; return b;
}

bool Memory(void *, std::uintptr_t at, void *out, std::size_t size) noexcept {
  if (!at || !out) return false;
  std::memcpy(out, reinterpret_cast<const void *>(at), size); return true;
}
std::int64_t *Knowledge(std::int64_t *out, void *actor, void *rite) {
  ++f->knowledge_calls;
  f->native_invocations_ok &= actor == f->character.data() &&
      (rite == f->rite.data() || rite == f->main_rite.data());
  *out = rite == f->rite.data() ? 0 : 25000; return out;
}
std::uint32_t *ExistingAtom(void *pool, std::uint32_t *out, const state::NativeStringView *view) {
  ++f->lookup_calls;
  f->native_invocations_ok &= pool == f->atom_pool.data() && view && view->range_comparison == 1;
  const std::string_view key(view->data, static_cast<std::size_t>(view->length));
  if (key == state::kRecentConversionFlag) *out = 101;
  else if (key == state::kConversionMemoryFlag) *out = 102;
  else if (key == state::kNarrativeRecentConvertFlag) *out = 103;
  else { f->native_invocations_ok = false; *out = 0; }
  return out;
}
void *FlagCollection(void *script_data) {
  f->native_invocations_ok &= script_data == f->resources.data(); return f->flag_set.data();
}
void BindQuery(Fixture &fixture, c::PlayerReligionConversionOutcomeMailboxContext12002 &query) {
  query.bindings.actor.current_religion = Bind(fixture);
  query.bindings.actor.read_memory = &Memory;
  auto &b = query.bindings.state;
  b.enabled = true; b.core = query.bindings.actor.current_religion.core;
  b.rite_storage_slot = &f->rite_storage_ptr; b.rite_knowledge = &Knowledge;
  b.existing_atom = &ExistingAtom; b.atom_pool = f->atom_pool.data(); b.character_flag_collection = &FlagCollection;
  b.character_spiritual_fulfillment = &Fulfillment;
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
    mailbox.permitted_executor = &c::ExecutePlayerReligionConversionOutcomeMailbox12002;
    mailbox.iat_hook_installed = true; mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2; ++i)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};

bool Query(Fixture &fixture, FrameAdapter &adapter, const std::filesystem::path &directory,
           const char *filename, std::uint32_t target, bool actor_enabled, bool state_enabled,
           o::Context &observed) {
  api::MainThreadQueryMailboxV1 mailbox{}; Pump pump(fixture, mailbox);
  c::PlayerReligionConversionOutcomeMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame; query.envelope.expected_snapshot_revision = 901;
  query.target_rite_id = target; BindQuery(fixture, query);
  query.bindings.actor.current_religion.enabled = actor_enabled;
  query.bindings.state.enabled = state_enabled; adapter.reads = 0;
  std::atomic<bool> done{false}; bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::RunPlayerReligionConversionOutcomeMailbox12002(query, "religion-outcome\"mailbox-fixture", serialized, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join(); observed = query.observation;
  Check(drained, "actual queued owner callback drained");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual mailbox reclaimed");
  if (result) {
    Check(query.completed && query.envelope.frame_stable && failure.empty() && !serialized.empty(), "actual full serialized result");
    Check(observed.capture_epoch == query.envelope.execution_stamp.pump_epoch && observed.capture_epoch != 901,
          "actual capture epoch distinct from published revision");
    std::ofstream(directory / filename) << serialized << '\n';
  } else Check(serialized.empty() && !failure.empty(), "changed published frame has no success packet");
  return result;
}
} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory"); const std::filesystem::path directory(argv[1]);
    Fixture fixture; FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::character_id; adapter.frame.date_raw = 53175816;
    o::Context observed;
    Check(Query(fixture, adapter, directory, "current.json", 0x84000001u, true, true, observed) && observed.available &&
          observed.target_reached == false && observed.actor.current_religion.rite_id == 0u &&
          observed.state.target_rite_id == 0x84000001u && observed.actor.piety_raw == 0 &&
          observed.actor.gold_raw == -123456 && observed.actor.prestige_raw == -7654321 &&
          observed.state.knowledge_level_raw == 25000 && fixture.native_invocations_ok,
          "actual identities/signed balances/knowledge do not infer conversion from a target");
    Check(observed.state.faith_conversion_recently_converted.present == true &&
          observed.state.faith_conversion_recently_converted.timed == true &&
          observed.state.faith_conversion_recently_converted.expiry_counter_raw == 200 &&
          observed.state.faith_conversion_recently_converted.current_counter_raw == 150 &&
          observed.state.faith_conversion_recently_converted.remaining_updates == 50 &&
          observed.state.conversion_memory_recently_created.present == false &&
          observed.state.recent_convert.present == true && observed.state.recent_convert.timed == false &&
          observed.state.recent_convert.expiry_counter_raw == -1 && !observed.state.recent_convert.remaining_updates,
          "native timed/absent/permanent flags preserve actual counters and sentinels");
    Check(Query(fixture, adapter, directory, "zero-target.json", 0, true, true, observed) && observed.available &&
          observed.target_reached == true && observed.state.target_rite_id == 0u && observed.state.knowledge_level_raw == 0,
          "full target zero and knowledge zero are legal observed values");
    Put(fixture.character, 0xB4, std::uint32_t{0x84000001u});
    Check(Query(fixture, adapter, directory, "target-current.json", 0x84000001u, true, true, observed) &&
          observed.available && observed.target_reached == true && observed.actor.current_religion.rite_id == 0x84000001u,
          "target reached compares independently read complete current Rite identity only");
    Put(fixture.character, 0xB4, std::uint32_t{0});
    Check(Query(fixture, adapter, directory, "actor-unavailable.json", 0x84000001u, false, true, observed) &&
          !observed.available && !observed.actor.available && observed.state.available && !observed.actor.piety_raw &&
          !observed.target_reached && observed.failure == o::Failure::actor_unavailable,
          "typed actor failure preserves actual state without invented resources or identity");
    Check(Query(fixture, adapter, directory, "state-unavailable.json", 0x84000001u, true, false, observed) &&
          !observed.available && observed.actor.available && !observed.state.available && !observed.state.knowledge_level_raw &&
          observed.target_reached == false && observed.failure == o::Failure::state_unavailable,
          "typed state failure preserves actual actor identity comparison");
    Check(Query(fixture, adapter, directory, "both-unavailable.json", 0x84000001u, false, false, observed) &&
          !observed.available && !observed.actor.available && !observed.state.available &&
          observed.date_raw == adapter.frame.date_raw && observed.actor.date_raw == observed.date_raw &&
          observed.state.date_raw == observed.date_raw && observed.failure == o::Failure::actor_and_state_unavailable,
          "both failed components retain actual published frame and typed failures");
    Put(fixture.state, 8, std::int32_t{53175817});
    Check(!Query(fixture, adapter, directory, "source-mismatch.json", 0x84000001u, true, true, observed),
          "pump differing from published date refused before components");
    Put(fixture.state, 8, std::int32_t{53175816}); adapter.drift = true;
    Check(!Query(fixture, adapter, directory, "published-drift.json", 0x84000001u, true, true, observed),
          "actual full published snapshot changed during query");
    adapter.drift = false;
    std::uint32_t target = r::kAbsentReference; std::uint64_t revision = 0;
    Check(c::ParsePlayerReligionConversionOutcomeRequest12002("{\"target_rite_id\":0}", target, revision) &&
          target == 0 && revision == 0, "required zero target optional revision");
    Check(c::ParsePlayerReligionConversionOutcomeRequest12002("{\"target_rite_id\":2214592513,\"expected_revision\":901}", target, revision) &&
          target == 0x84000001u && revision == 901, "full generation target and revision alias");
    Check(c::ParsePlayerReligionConversionOutcomeRequest12002("{\"target_rite_id\":0,\"expected_snapshot_revision\":901,\"expected_revision\":901}", target, revision),
          "matching expected revision aliases");
    Check(!c::ParsePlayerReligionConversionOutcomeRequest12002("{}", target, revision) &&
          !c::ParsePlayerReligionConversionOutcomeRequest12002("{\"target_rite_id\":4294967295}", target, revision), "absent/missing target invalid");
    Check(!c::ParsePlayerReligionConversionOutcomeRequest12002("{\"target_rite_id\":0,\"expected_revision\":0}", target, revision) &&
          !c::ParsePlayerReligionConversionOutcomeRequest12002("{\"target_rite_id\":0,\"expected_revision\":902,\"expected_snapshot_revision\":901}", target, revision),
          "zero and conflicting explicit expectations invalid");
    Check(!c::ParsePlayerReligionConversionOutcomeRequest12002("{\"target_rite_id\":0,\"actor_id\":4}", target, revision), "no actor override");
    api::MainThreadQueryMailboxV1 mailbox{}; std::string wire, failure;
    Check(!c::HandlePlayerReligionConversionOutcomePrivate12002(adapter, mailbox, adapter.frame, 901,
          c::kPlayerReligionConversionOutcomePrivateStep12002, "{\"target_rite_id\":0,\"expected_revision\":902}",
          "stale", wire, failure) && wire.empty() && mailbox.next_sequence == 0 &&
          failure == "player_religion_conversion_outcome_current_frame_unavailable", "actual handler stale frame before submission");
    Check(c::IsPlayerReligionConversionOutcomePrivateStep12002(c::kPlayerReligionConversionOutcomePrivateStep12002) &&
          !c::IsPlayerReligionConversionOutcomePrivateStep12002("query-player-religion-conversion-terms-v1"), "distinct exact selector");
    std::cout << "PASS checks=" << checks << " cases=8 actual_core=true actual_actor_state=true actual_submit_drain_wait_reclaim=true actual_wrapper=true live=false\n";
    return 0;
  } catch (const std::exception &e) { std::cerr << "FAIL " << e.what() << '\n'; return 1; }
}
