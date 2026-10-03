#include "xar_bridge/ck3_12002_religion_mailbox.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include <cstdlib>

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace r = xar::ck3_12002::religion;
namespace c = xar::ck3_12002;
namespace {
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
  Bytes<0x978> rite{}, main_rite{}, wrong_faith{};
  Bytes<0x320> faith{};
  Bytes<0x40> religion{};
  Bytes<0x50> religion_definition{};
  Bytes<0xB0> extension{};
  Bytes<0x128> values{};
  Bytes<0x10> devotion_vector{};
  std::array<std::int64_t, 4> devotion_thresholds{11100000, 22200000, 33300000, 44400000};
  std::int32_t devotion_level = 1, devotion_cap = 2;
  int numeric_calls = 0;
  std::array<std::int32_t, 4> trait_ids{101, 102, 103, 104};
  std::array<Bytes<0x10>, 4> trait_definitions{};
  std::array<Bytes<0x28>, 3> trait_records{};
  std::byte trait_database{}, decision_database{}, decision_cost{};
  void *decision_database_pointer = &decision_database;
  const void *decision_fallback = nullptr;
  Bytes<0x40> decision_definition{};
  std::string vow_reasons = "Synthetic native reason \"vows\" \xe5\xae\x97\xe6\x95\x99\n#N current Rite has no vows#!";
  int classification_calls = 0, reason_destroys = 0, root_destroys = 0;
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
    Put(character, 0x1B0, values.data());
    Put(values, 0x110, std::int64_t{36576250});
    Put(values, 0x118, std::int64_t{15000000});
    Put(devotion_vector, 0, devotion_thresholds.data());
    Put(devotion_vector, 0xC, std::int32_t{4});
    Put(character, 0xF8, trait_ids.data());
    Put(character, 0x104, std::int32_t{4});
    Put(trait_records[0], 0, std::int32_t{1});
    Put(trait_records[0], 0x18, std::int64_t{100000});
    Put(trait_records[0], 0x20, std::int64_t{200000});
    Put(trait_records[1], 0, std::int32_t{1});
    Put(trait_records[1], 0x18, std::int64_t{300000});
    Put(trait_records[1], 0x20, std::int64_t{400000});
    Put(trait_records[2], 0, std::int32_t{2});
    Put(trait_records[2], 0x18, std::int64_t{-500000});
    Put(trait_records[2], 0x20, std::int64_t{600000});
    Tag(decision_definition, 0x18, xar::ck3_12003::religion::vow_of_poverty_terms12003::kDecisionId);
    Put(rite, 8, std::uint32_t{0}); Put(rite, r::kRiteFaithIdOffset, faith_id);
    Put(main_rite, 8, std::uint32_t{0x02000002});
    Put(faith, 8, faith_id); Put(faith, r::kFaithReligionIdOffset, religion_id);
    Put(faith, r::kFaithMainRiteIdOffset, std::uint32_t{0x02000002});
    Put(faith, 0x2F8, std::int64_t{0}); Put(extension, 0xA0, std::int64_t{0});
    Put(religion, 8, religion_id); Put(religion, 0x10, std::int32_t{7});
    Put(religion, 0x20, religion_definition.data());
    Tag(faith, 0xE0, "faith\"key");
    Tag(religion_definition, 0x18, "christianity_religion");
  }
  template <typename Buffer> static void Tag(Buffer &object, std::size_t at, std::string_view value) {
    std::memset(object.data() + at, 0, 0x20);
    if (value.size() < 16) std::memcpy(object.data() + at, value.data(), value.size());
    else Put(object, at, value.data());
    Put(object, at + 0x10, static_cast<std::uint64_t>(value.size()));
    Put(object, at + 0x18, static_cast<std::uint64_t>(value.size() < 16 ? 15 : 31));
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *CharacterRite(void *) { return f->missing_rite ? nullptr : f->rite.data(); }
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
r::Bindings Bind(Fixture &fixture) {
  f = &fixture;
  r::Bindings b{}; b.enabled = true;
  b.core = {true, &f->state_ptr, &f->jomini_ptr, &f->storage_ptr, &Player};
  b.character_rite = &CharacterRite; b.character_faith = &CharacterFaith;
  b.rite_faith = &RiteFaith; b.faith_religion = &FaithReligion; b.faith_main_rite = &FaithMainRite;
  b.faith_fervor = &Fervor; b.character_spiritual_fulfillment = &Fulfillment;
  b.faith_tag = &FaithTag;
  b.religion_tag = r::BindReligionContextImage12002(0x140000000, c::kExecutableSha256).religion_tag;
  return b;
}
} // namespace

#include <atomic>
#include <chrono>
#include <thread>
#include <stdexcept>

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
  game::AdapterDescriptor identity{xar::ck3_12003::kAdapterId, xar::ck3_12003::kGameVersion,
      xar::ck3_12003::kExecutableSha256, "synthetic-devotion-virtues-vow", {}};
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
    // Use the same named religion permit as the deployed DLL, with fixture-owned memory.
    mailbox.permitted_executor_religion12002 = &c::ExecutePlayerReligionMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2; ++i)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};


namespace d = r::devotion_profile12003;
namespace v = r::rite_virtue_sin_profile12003;
namespace p = xar::ck3_12003::religion::vow_of_poverty_terms12003;
void Scope(d::PlayerValueItemScope *scope) {
  Check(scope->character == f->character.data() && scope->tag == 0,
      "native numeric scope contains actual player and piety tag zero");
}
std::int32_t DevotionLevel(void *actor) {
  Check(actor == f->character.data(), "level receives actual played Character");
  ++f->numeric_calls; return f->devotion_level;
}
std::int32_t DevotionCap(d::PlayerValueItemScope *scope) {
  Scope(scope); ++f->numeric_calls; return f->devotion_cap;
}
const void *DevotionThresholds(d::PlayerValueItemScope *scope) {
  Scope(scope); ++f->numeric_calls; return f->devotion_vector.data();
}
std::int64_t *DevotionPercent(std::int64_t *out, void *actor) {
  Check(actor == f->character.data(), "progress receives actual Character");
  ++f->numeric_calls; *out = f->devotion_level == 1 ? 3513510 : 0; return out;
}
void DevotionProgress(d::PlayerValueItemScope *scope, std::int64_t *numerator, std::int64_t *denominator) {
  Scope(scope); ++f->numeric_calls;
  *numerator = f->devotion_level == 1 ? 3900000 : 0;
  *denominator = f->devotion_level == 1 ? 11100000 : 100000;
}
void *TraitDatabase() { return &f->trait_database; }
void *TraitLookup(void *database, std::int32_t id) {
  Check(database == &f->trait_database && id >= 101 && id <= 104,
      "trait lookup consumes actual Character trait IDs and database");
  return f->trait_definitions[static_cast<std::size_t>(id - 101)].data();
}
std::int32_t ClassifyTrait(void *trait, void *effective_map, void **record) {
  Check(effective_map == f->rite.data() + 0x950,
      "classifier receives effective current Rite map, including tenet overrides");
  ++f->classification_calls;
  for (std::size_t i = 0; i != 4; ++i) {
    if (trait == f->trait_definitions[i].data()) {
      *record = i == 3 ? nullptr : f->trait_records[i].data();
      return i == 3 ? 0 : Get<std::int32_t>(*record, 0);
    }
  }
  throw std::runtime_error("wrong actual trait passed to native classifier");
}
std::uint32_t DecisionHash(void *database, const char *key, std::uint32_t size) {
  Check(database == &f->decision_database && std::string_view(key, size) == p::kDecisionId,
      "existing decision hash consumes fixed take-vow key");
  return 42;
}
const void *DecisionLookup(void *database, std::uint32_t hash) {
  Check(database == &f->decision_database && hash == 42, "native exact decision lookup");
  return f->decision_definition.data();
}
void *RootConstruct(void *root) { return root; }
void RootDestroy(void *) { ++f->root_destroys; }
void VerifyRoot(void *root) {
  Check(Get<std::uint16_t>(root, 0) == 4 && Get<std::int64_t>(root, 8) == Fixture::character_id,
      "decision root uses actual full played Character identity");
}
bool DecisionShown(const void *definition, void *actor) {
  Check(definition == f->decision_definition.data() && actor == f->character.data(),
      "native IsShown consumes actual fixed decision and player");
  return false;
}
bool DecisionCanTake(const void *definition, void *actor, void *root, const void *unused, void *reason) {
  VerifyRoot(root);
  Check(definition == f->decision_definition.data() && actor == f->character.data() && unused == nullptr,
      "native CanTake uses actual root and final reasons");
  auto *owned = new char[f->vow_reasons.size() + 1];
  std::memcpy(owned, f->vow_reasons.c_str(), f->vow_reasons.size() + 1);
  std::memcpy(reason, &owned, sizeof(owned));
  const auto size = f->vow_reasons.size();
  std::memcpy(static_cast<std::byte *>(reason) + 0x10, &size, sizeof(size));
  std::memcpy(static_cast<std::byte *>(reason) + 0x18, &size, sizeof(size));
  return false;
}
const void *DecisionCost(const void *definition) {
  Check(definition == f->decision_definition.data(), "actual decision CCost input");
  return &f->decision_cost;
}
void EvaluateCost(const void *cost, void *root, std::int64_t *resources) {
  VerifyRoot(root);
  Check(cost == &f->decision_cost, "native cost evaluates current root");
  resources[0] = 0; resources[6] = 0; resources[1] = 0; resources[2] = 0;
}
bool Affordable(const void *cost, void *root, void *actor, void *text) {
  VerifyRoot(root);
  Check(cost == &f->decision_cost && actor == f->character.data() && text == nullptr,
      "native affordable checks evaluated CCost on actual player");
  return true;
}
void DestroyReason(void *reason) { ++f->reason_destroys; delete[] Get<char *>(reason, 0); }
void BindNew(c::PlayerReligionMailboxContext12002 &query) {
  query.devotion_bindings = {true, &DevotionLevel, &DevotionPercent, &DevotionCap,
      &DevotionProgress, &DevotionThresholds};
  query.rite_virtue_sin_bindings = {true, &TraitDatabase, &TraitLookup, &CharacterRite, &ClassifyTrait};
  query.vow_of_poverty_bindings = {true, &f->decision_database_pointer, &f->decision_fallback,
      &DecisionHash, &DecisionLookup, &RootConstruct, &RootDestroy, &DecisionShown,
      &DecisionCanTake, &DecisionCost, &EvaluateCost, &Affordable, &DestroyReason};
}
} // namespace

// Fixture-only unresolved image-construction stubs; the real renderer is used.
#if defined(XAR_RELIGION_TYPE_TAX_STANDALONE_RENDERER)
namespace xar::game {
Ck3_12002AdapterBindings BindCk3_12002AdapterImage(std::uintptr_t, std::string_view) noexcept { std::abort(); }
const AdapterDescriptor &Ck3_12002AdapterDescriptor() noexcept { std::abort(); }
std::unique_ptr<GameAdapter> CreateCk3_12003AdapterFromBindings(Ck3_12003AdapterBindings) noexcept { std::abort(); }
}
#endif

namespace {
void RunCase(Fixture &fixture, FrameAdapter &adapter, const std::filesystem::path &directory, bool terminal) {
  if (terminal) {
    fixture.devotion_level = 3;
    Put(fixture.character, 0x104, std::int32_t{0});
    Put(fixture.character, 0xF8, static_cast<void *>(nullptr));
  }
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(fixture, mailbox);
  c::PlayerReligionMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 2701;
  query.bindings = Bind(fixture); BindNew(query); adapter.reads = 0;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::RunPlayerReligionMailbox12002(query, "synthetic-devotion-virtues-vow", serialized, failure);
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
      "actual production mailbox completes all three new readers on synthetic owner");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "same actual owner ticket reclaimed");
  const auto &numeric = query.devotion_profile;
  const auto &traits = query.rite_virtue_sin_profile;
  const auto &vow = query.vow_of_poverty_terms;
  Check(numeric.available && numeric.current_devotion_total_raw == 15000000 && numeric.effective_cap == 2 &&
      numeric.runtime_threshold_count == 4 && f->numeric_calls == (terminal ? 10 : 5),
      "production numeric reader observes cumulative value distinct from spendable cash and dynamic cap");
  if (!terminal) {
    Check(numeric.effective_level == 1 && numeric.level_lower_threshold_raw == 11100000 &&
        numeric.level_upper_threshold_raw == 22200000 && numeric.progress_numerator_raw == 3900000 &&
        numeric.progress_denominator_raw == 11100000 && numeric.progress_percent_raw == 3513510 &&
        numeric.native_terminal_threshold_branch == false, "ordinary interval preserves exact native outputs");
    Check(traits.available && traits.rite_id == 0U && traits.trait_count == 4 &&
        traits.num_virtuous_traits == 2 && traits.num_sinful_traits == 1 && traits.traits.size() == 4 &&
        traits.traits[0].opinion_weight_input_raw == 100000 &&
        traits.traits[0].owner_modifier_scale_input_raw == 200000 &&
        traits.traits[2].opinion_weight_input_raw == -500000 &&
        traits.traits[3].classification == 0 && !traits.traits[3].opinion_weight_input_raw &&
        fixture.classification_calls == 4, "native current Rite classification and independent record consumers");
  } else {
    Check(numeric.effective_level == 3 && numeric.native_terminal_threshold_branch == true &&
        numeric.progress_numerator_raw == 0 && numeric.progress_denominator_raw == 100000 &&
        numeric.progress_percent_raw == 0 && !numeric.level_lower_threshold_raw && !numeric.level_upper_threshold_raw,
        "native terminal above dynamic cap preserves zero percent and null thresholds");
    Check(traits.available && traits.trait_count == 0 && traits.num_virtuous_traits == 0 &&
        traits.num_sinful_traits == 0 && traits.traits.empty() && fixture.classification_calls == 4,
        "legitimate zero current trait count remains observed and never fabricates classifications");
  }
  Check(vow.available && vow.is_shown == false && vow.can_take == false && vow.affordable == true &&
      vow.costs_raw->piety == 0 && vow.can_take_reasons == fixture.vow_reasons &&
      fixture.reason_destroys == (terminal ? 2 : 1) && fixture.root_destroys == (terminal ? 2 : 1),
      "fixed vow terms retain native shown/CanTake/CCost/final UTF8 reason, releasing temporary owned values");
  const auto epoch = query.envelope.execution_stamp.pump_epoch;
  Check(numeric.capture_epoch == epoch && traits.capture_epoch == epoch && vow.capture_epoch == epoch &&
      numeric.date_raw == adapter.frame.date_raw && traits.played_character_id == Fixture::character_id &&
      query.observation.available, "all new independent siblings share real fixture frame and old Context");
  const auto rendered = xar::game::RenderCrozierBuildIdentity(std::move(serialized), adapter.descriptor());
  Check(rendered.find("\"game_version\":\"1.20.0.3\"") != std::string::npos &&
      rendered.find(std::string(xar::ck3_12003::kExecutableSha256)) != std::string::npos,
      "genuine production command_result and exact .3 renderer");
  std::ofstream(directory / (terminal ? "terminal-native-wire.json" : "ordinary-native-wire.json"), std::ios::binary)
      << rendered << '\n';
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory argument");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    Fixture fixture; FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::character_id;
    adapter.frame.date_raw = Get<std::int32_t>(fixture.state.data(), 8);
    RunCase(fixture, adapter, directory, false);
    RunCase(fixture, adapter, directory, true);
    std::cout << "PASS focused_fixture=1 cases=2 checks=" << checks
        << " production_mailbox_reader_serializer_renderer=true synthetic_native_callbacks=true game=false live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
