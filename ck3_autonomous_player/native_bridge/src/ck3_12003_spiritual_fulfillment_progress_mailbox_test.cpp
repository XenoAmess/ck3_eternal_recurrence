#include "xar_bridge/ck3_12002_religion_mailbox.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"

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
  Bytes<0x500> rite{}, main_rite{}, wrong_faith{};
  Bytes<0x320> faith{};
  Bytes<0x40> religion{};
  Bytes<0x50> religion_definition{};
  Bytes<0xB0> extension{};
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
      xar::ck3_12003::kExecutableSha256, "synthetic-progress-mailbox-fixture", {}};
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

namespace progress = r::fulfillment_progress12003;
struct ProgressFixture {
  Bytes<0x70> type{};
  Bytes<progress::kLevelStride * 2> levels{};
  std::byte database{};
  void *database_ptr = &database;
  std::int64_t minimum = -10'000'000, maximum = 10'000'000;
  int type_calls = 0, level_calls = 0, progress_calls = 0;
  ProgressFixture() {
    Put(type, progress::kTypeLevelRowsOffset, levels.data());
    Put(type, progress::kTypeLevelCountOffset, std::int32_t{2});
    Put(levels, progress::kLevelLowerBoundOffset, std::int64_t{-3'000'000});
    Put(levels, progress::kLevelUpperBoundOffset, std::int64_t{3'000'000});
    Put(levels, progress::kLevelIndexOffset, std::int32_t{3});
    Put(levels, progress::kLevelStride + progress::kLevelIndexOffset, std::int32_t{4});
  }
};
ProgressFixture *pf = nullptr;
void *TypeForCharacter(void *database, void *character) {
  Check(database == &pf->database && character == f->character.data(), "actual resolved player receiver and database slot");
  ++pf->type_calls; return pf->type.data();
}
void *LevelForValue(void *type, std::int64_t value) {
  Check(type == pf->type.data() && value == 750'000, "native level selector uses existing Context current value");
  ++pf->level_calls; return pf->levels.data();
}
std::int64_t *ProgressForValue(std::int64_t *out, std::int64_t value,
                             std::int64_t lower, std::int64_t upper) {
  Check(value == 750'000 && lower == -3'000'000 && upper == 3'000'000,
        "native progress callback receives signed interval and exact current");
  ++pf->progress_calls;
  // Explicit synthetic native callback material, not a current game observation.
  *out = 6'250'000;
  return out;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory argument");
    const std::filesystem::path directory(argv[1]);
    Fixture fixture; FrameAdapter adapter; ProgressFixture material; pf = &material;
    Put(fixture.extension, 0xA0, std::int64_t{750'000});
    Put(fixture.faith, 0x2F8, std::int64_t{-123456});
    Fixture::Tag(fixture.faith, 0xE0, "faith\"信");
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::character_id;
    adapter.frame.date_raw = Get<std::int32_t>(fixture.state.data(), 8);
    api::MainThreadQueryMailboxV1 mailbox{};
    Pump pump(fixture, mailbox);
    c::PlayerReligionMailboxContext12002 query{};
    query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = adapter.frame;
    query.envelope.expected_snapshot_revision = 701;
    query.bindings = Bind(fixture);
    query.progress_bindings = {true, &material.database_ptr, &TypeForCharacter,
        &LevelForValue, &ProgressForValue, &material.minimum, &material.maximum};
    std::uint64_t expected_revision = 0;
    Check(c::IsPlayerReligionPrivateStep12002("query-player-religion-context-v1") &&
          c::ParsePlayerReligionRevision12002("{\"expected_revision\":701}", expected_revision) &&
          expected_revision == 701, "existing selector and request revision parser");
    std::atomic<bool> done{false};
    bool result = false, drained = false;
    std::string serialized, failure;
    std::thread worker([&] {
      result = c::RunPlayerReligionMailbox12002(query, "synthetic-progress-mailbox-01", serialized, failure);
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
          "real owner executor and mailbox submit/drain/wait/reclaim result");
    Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "real mailbox reclaimed");
    Check(query.observation.available && query.observation.rite_id == 0U &&
          query.observation.faith_id == Fixture::faith_id && query.observation.religion_id == Fixture::religion_id &&
          query.observation.spiritual_fulfillment_raw == 750'000 && query.observation.faith_fervor_raw == -123456,
          "existing Context full IDs and signed material unchanged");
    const auto &p = query.progress;
    Check(p.available && p.failure == progress::Failure::none &&
          p.capture_epoch == query.observation.capture_epoch && p.date_raw == query.observation.date_raw &&
          p.played_character_id == query.observation.played_character_id &&
          p.current_fulfillment_raw == query.observation.spiritual_fulfillment_raw,
          "independent progress inherits actual old Context owner frame");
    Check(p.active_level_index == 3 && p.level_count == 2 && p.highest_level == false &&
          p.level_lower_bound_raw == -3'000'000 && p.level_upper_bound_raw == 3'000'000 &&
          p.progress_percent_raw == 6'250'000 && p.runtime_minimum_raw == -10'000'000 &&
          p.runtime_maximum_raw == 10'000'000 && material.type_calls == 1 &&
          material.level_calls == 1 && material.progress_calls == 1,
          "actual reader publishes supplied native percent, interval and runtime bounds once");
    Check(serialized.find(r::SerializePlayedReligionContext12002(query.observation)) != std::string::npos &&
          serialized.find(progress::SerializeSpiritualFulfillmentProgress12003(p)) != std::string::npos,
          "actual command-result serializer retains unmodified old Context and independent component");
    // Use the deployed identity renderer, not Python replacement or fabricated JSON.
    const auto wire = game::RenderCrozierBuildIdentity(serialized, adapter.descriptor());
    Check(wire.find("\"game_version\":\"1.20.0.3\"") != std::string::npos &&
          wire.find(xar::ck3_12003::kExecutableSha256) != std::string::npos &&
          wire.find("\"player_spiritual_fulfillment_progress\":") != std::string::npos,
          "production .3 identity renderer and sibling key");
    std::ofstream(directory / "native-wire.json", std::ios::binary) << wire << '\n';
    std::cout << "PASS cases=1 checks=" << checks
              << " actual_mailbox_executor=true actual_core=true actual_context_reader=true actual_progress_reader=true"
                 " actual_serializer=true actual_build_identity_renderer=true synthetic_material=true live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
