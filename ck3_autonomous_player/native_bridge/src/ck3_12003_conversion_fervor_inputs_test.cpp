#include "xar_bridge/ck3_12002_religion_conversion_inputs_mailbox.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace c = xar::ck3_12002;
namespace r = c::religion;
namespace s = r::state_rite;
namespace g = r::conversion_gates;
namespace ai = c::religion_conversion_ai_inputs;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename B, typename T> void Put(B &b, std::size_t at, T value) {
  std::memcpy(b.data() + at, &value, sizeof(value));
}
struct Fixture {
  Bytes<0xA8> state{}; Bytes<0x28> jomini{}; Bytes<0x1F8> players{};
  Bytes<0x78> player{}; std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{}; std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> storage{}, rite_storage{}; Bytes<0x100> slots{}, rite_slots{};
  Bytes<0x1D8> actor{}, liege{}; Bytes<0x200> own_land{}, realm_land{};
  Bytes<0x310> own_title{}, realm_title{};
  Bytes<0x500> actor_rite{}, target_rite{}, main_rite{}, state_rite{};
  Bytes<0xB0> actor_faith{}, target_faith{}; Bytes<0x10> actor_religion{}, target_religion{};
  Bytes<0x4> script{}; Bytes<0x30> flags{}, flag_rows{}, atom_pool{};
  std::array<std::uint32_t, 1> own_titles{0x82000001U}, realm_titles{0x83000002U};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  void *rite_storage_ptr = rite_storage.data();
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::uint32_t liege_id = 0x84000006U, target_id = 0x85000007U;
  static constexpr std::uint32_t actor_faith_id = 0x86000009U, target_faith_id = 0x8700000AU;
  static constexpr std::uint32_t religion_id = 0x8800000BU, state_rite_id = 0x8900000CU;
  static constexpr std::uint32_t recent_atom = 0x07000123U;
  std::int64_t knowledge = 40'000;
  std::int64_t actor_fervor = 7'500'000, target_fervor = 6'000'000;
  bool target_fervor_fails = false;
  unsigned fervor_calls = 0;
  std::int64_t current_base = 0, target_base = 0;
  bool base_fails = false, core_date_changes = false;
  bool key_registered = true, lookup_fails = false, collection_missing = false, knowledge_fails = false;
  bool knowledge_changes = false, same_faith = false, same_religion = true;
  int knowledge_calls = 0;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, actor.data()); Put(slots, 6 * 0x10 + 8, liege.data());
    Put(actor, s::kCharacterIdentityOffset, actor_id); Put(liege, s::kCharacterIdentityOffset, liege_id);
    Put(actor, s::kCharacterLandedDataOffset, own_land.data()); Put(liege, s::kCharacterLandedDataOffset, realm_land.data());
    Put(own_land, s::kLandedTitlesOffset, own_titles.data()); Put(realm_land, s::kLandedTitlesOffset, realm_titles.data());
    Put(own_land, s::kLandedTitlesCountOffset, std::int32_t{1}); Put(realm_land, s::kLandedTitlesCountOffset, std::int32_t{1});
    Put(own_title, s::kTitleIdentityOffset, own_titles[0]); Put(realm_title, s::kTitleIdentityOffset, realm_titles[0]);
    Put(own_title, s::kTitleStateRiteIdOffset, target_id); Put(realm_title, s::kTitleStateRiteIdOffset, state_rite_id);
    Put(actor, r::kCharacterRiteIdOffset, std::uint32_t{0}); Put(actor_rite, 8, std::uint32_t{0});
    Put(actor_rite, r::kRiteFaithIdOffset, actor_faith_id);
    Put(main_rite, 8, std::uint32_t{0x8A00000D});
    Put(target_rite, 8, target_id); Put(target_rite, r::kRiteFaithIdOffset, target_faith_id);
    Put(state_rite, 8, state_rite_id); Put(state_rite, r::kRiteFaithIdOffset, target_faith_id);
    Put(actor_faith, 8, actor_faith_id); Put(target_faith, 8, target_faith_id);
    Put(actor_faith, r::kFaithMainRiteIdOffset, std::uint32_t{0x8A00000D});
    Put(actor_faith, r::kFaithReligionIdOffset, religion_id); Put(target_faith, r::kFaithReligionIdOffset, religion_id);
    Put(actor_religion, 8, religion_id); Put(target_religion, 8, religion_id);
    Put(rite_storage, 0x20, rite_slots.data()); Put(rite_storage, 0x2C, std::int32_t{16});
    Put(rite_slots, 7 * 0x10 + 8, target_rite.data());
    Put(rite_slots, 8, actor_rite.data());
    Put(actor, g::kCharacterScriptDataOffset, script.data()); Put(script, 0, std::int32_t{4});
    Put(flags, g::kFlagRowsOffset, flag_rows.data()); Put(flags, g::kFlagCountOffset, std::int32_t{1});
    Put(flag_rows, g::kFlagKeyOffset, recent_atom);
    Put(atom_pool, 0x10, flag_rows.data()); Put(atom_pool, 0x1C, std::int32_t{15});
  }
};
Fixture *q = nullptr;
void *Player(void *) { return q->player.data(); }
void *CharacterRite(void *) { return q->actor_rite.data(); }
void *CharacterFaith(void *) { return q->actor_faith.data(); }
void *FaithMainRite(void *) { return q->main_rite.data(); }
void *RiteFaith(void *rite) {
  return rite == q->actor_rite.data() || q->same_faith ? q->actor_faith.data() : q->target_faith.data();
}
std::int64_t *Fervor(void *faith, std::int64_t *out) {
  ++q->fervor_calls;
  if (faith == q->target_faith.data() && q->target_fervor_fails) return nullptr;
  *out = faith == q->actor_faith.data() ? q->actor_fervor : q->target_fervor;
  return out;
}
void *FaithReligion(void *faith) { return faith == q->actor_faith.data() ? q->actor_religion.data() : q->target_religion.data(); }
void *TopLiege(void *) { return q->liege.data(); }
void *PrimaryTitle(void *actor) { return actor == q->actor.data() ? q->own_title.data() : q->realm_title.data(); }
void *TitleStateRite(void *title) { return title == q->own_title.data() ? q->target_rite.data() : q->state_rite.data(); }
void *FlagCollection(void *script) {
  if (script != q->script.data()) return nullptr;
  return q->collection_missing ? nullptr : q->flags.data();
}
std::uint32_t *Lookup(void *pool, std::uint32_t *out, const g::NativeStringView *key) {
  if (pool != q->atom_pool.data() || std::string_view(key->data, key->length) != g::kRecentConversionFlag ||
      key->range_comparison != 1 || q->lookup_fails) return nullptr;
  *out = q->key_registered ? Fixture::recent_atom : r::kAbsentReference;
  return out;
}
std::int64_t *Knowledge(std::int64_t *out, void *actor, void *rite) {
  if (actor != q->actor.data() || (rite != q->target_rite.data() && rite != q->actor_rite.data()) || q->knowledge_fails) return nullptr;
  *out = q->knowledge + (q->knowledge_changes ? q->knowledge_calls++ : 0);
  return out;
}
g::Bindings Bind(Fixture &fixture) {
  q = &fixture; g::Bindings b{}; b.enabled = true; b.state.enabled = true; b.state.context.enabled = true;
  b.state.context.core = {true, &q->state_ptr, &q->jomini_ptr, &q->storage_ptr, &Player};
  b.state.context.character_rite = &CharacterRite; b.state.context.character_faith = &CharacterFaith;
  b.state.context.rite_faith = &RiteFaith; b.state.context.faith_main_rite = &FaithMainRite;
  b.state.context.faith_religion = &FaithReligion; b.state.context.faith_fervor = &Fervor;
  b.state.character_top_liege = &TopLiege; b.state.character_primary_title = &PrimaryTitle;
  b.state.title_state_rite = &TitleStateRite; b.rite_storage_slot = &q->rite_storage_ptr;
  b.rite_knowledge = &Knowledge; b.existing_atom = &Lookup; b.atom_pool = q->atom_pool.data();
  b.character_flag_collection = &FlagCollection; return b;
}
std::int64_t *PredictedBase(std::int64_t *out, void *actor, void *rite) {
  if (actor != q->actor.data() || q->base_fails) return nullptr;
  *out = rite == q->target_rite.data() ? q->target_base : q->current_base;
  if (q->core_date_changes) Put(q->state, 8, std::int32_t{53175817});
  return out;
}
ai::Bindings BindPrediction(const g::Bindings &gates) {
  ai::Bindings b{}; b.enabled = true; b.core = gates.state.context.core;
  b.rite_storage_slot = &q->rite_storage_ptr; b.base_fulfillment = &PredictedBase;
  return b;
}
} // namespace

#include <atomic>
#include <chrono>
#include <thread>
#include <stdexcept>

#if defined(XAR_RELIGION_CONVERSION_INPUTS_MAILBOX_STANDALONE_ADAPTER)
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
      xar::ck3_12003::kExecutableSha256, "synthetic-conversion-fervor-first-fixture", {}};
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
    // Existing offline primary permit; central production uses the inputs named slot.
    mailbox.permitted_executor_religion_conversion_inputs12002 = &c::ExecutePlayerReligionConversionInputsMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2; ++i)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};

bool Query(Fixture &fixture, FrameAdapter &adapter, const std::filesystem::path &directory,
    const char *filename, std::uint32_t target, c::PlayerReligionConversionInputsMailboxContext12002 &query) {
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(fixture, mailbox);
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame; query.envelope.expected_snapshot_revision = 701;
  query.target_rite_id = target; query.gates_bindings = Bind(fixture);
  query.prediction_bindings = BindPrediction(query.gates_bindings);
  adapter.reads = 0;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::RunPlayerReligionConversionInputsMailbox12002(query,
        "inputs\"mailbox-fixture", serialized, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Check(drained, "real queued inputs executor drained by fixture owner");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual mailbox reclaim");
  if (result) {
    Check(failure.empty() && query.completed && query.envelope.frame_stable && !serialized.empty(), "complete actual result");
    Check(query.conversion_gates.capture_epoch == query.predicted_base_fulfillment.capture_epoch &&
          query.conversion_gates.capture_epoch == query.envelope.execution_stamp.pump_epoch &&
          query.conversion_gates.capture_epoch != query.envelope.expected_snapshot_revision, "same pump epoch differs from revision");
    const auto wire = game::RenderCrozierBuildIdentity(serialized, adapter.descriptor());
    Check(wire.find("\"conversion_fervor\":") != std::string::npos &&
          wire.find(xar::ck3_12003::kExecutableSha256) != std::string::npos,
          "actual sibling serializer and deployed exact .3 identity renderer");
    std::ofstream(directory / filename, std::ios::binary) << wire << '\n';
  } else Check(serialized.empty() && !failure.empty(), "changed published frame has no success JSON");
  return result;
}
} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory argument");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    constexpr std::array<const char *, 4> names{
        "distinct_faith_positive_values.json", "legal_zero.json", "same_faith.json",
        "getter_failure_independent_of_old_gate.json"};
    for (std::size_t scenario = 0; scenario < names.size(); ++scenario) {
      Fixture f; FrameAdapter adapter;
      adapter.frame.paused = adapter.frame.map_ready = true;
      adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
      adapter.frame.played_character_id = Fixture::actor_id;
      adapter.frame.date_raw = 53175816;
      if (scenario == 1) { f.actor_fervor = 0; f.target_fervor = 0; }
      if (scenario == 2) {
        f.same_faith = true; f.actor_fervor = 5'500'000;
        Put(f.target_rite, r::kRiteFaithIdOffset, Fixture::actor_faith_id);
        Put(f.state_rite, r::kRiteFaithIdOffset, Fixture::actor_faith_id);
      }
      if (scenario == 3) f.target_fervor_fails = true;
      c::PlayerReligionConversionInputsMailboxContext12002 result{};
      Check(Query(f, adapter, directory, names[scenario], Fixture::target_id, result),
            "actual compiled owner query returns complete wire");
      Check(result.available && result.conversion_gates.available &&
            result.predicted_base_fulfillment.available && result.unavailable_reason.empty(),
            "new sibling does not redefine old gate/prediction/top result");
      Check(result.conversion_gates.knowledge_level_raw == 40'000 &&
            result.conversion_gates.recently_converted == true &&
            result.predicted_base_fulfillment.expected_base_change_raw == 0,
            "old actual knowledge flag and prediction material retained");
      const auto &v = result.conversion_fervor;
      Check(result.conversion_fervor_enabled && v.capture_epoch == result.conversion_gates.capture_epoch &&
            v.date_raw == result.conversion_gates.date_raw &&
            v.played_character_id == result.conversion_gates.played_character_id &&
            v.requested_target_rite_id == Fixture::target_id &&
            v.actor_faith_id == result.conversion_gates.actor_faith_id &&
            v.target_faith_id == result.conversion_gates.target_faith_id,
            "actual child belongs to same owner epoch and resolved Faith pair");
      if (scenario == 3) {
        Check(!v.available && v.failure == r::conversion_fervor::Failure::target_fervor_unavailable &&
              !v.actor_fervor_raw && !v.target_fervor_raw,
              "target getter failure retains independent old result and no invented zero");
      } else {
        const auto expected_target = scenario == 2 ? f.actor_fervor : f.target_fervor;
        Check(v.available && v.actor_fervor_raw == f.actor_fervor &&
              v.target_fervor_raw == expected_target,
              "actual production reader preserves supplied positive zero and same-Faith values");
        Check(f.fervor_calls > 0, "existing fervor getter called on real fixture receivers");
      }
    }
    std::cout << "PASS cases=4 checks=" << checks
              << " actual_core=true actual_old_readers=true actual_fervor_reader=true"
                 " actual_owner_mailbox_submit_drain_wait_reclaim=true actual_serializer=true"
                 " actual_build_identity_renderer=true synthetic_material=true live=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n'; return 1;
  }
}
