#include "xar_bridge/religion_doctrine12002_choices_mailbox.hpp"

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
template <typename Buffer, typename T> void Put(Buffer &b, std::size_t offset, T value) {
  std::memcpy(b.data() + offset, &value, sizeof(value));
}
template <typename T> T Load(const void *object, std::size_t offset) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value)); return value;
}
template <typename Buffer> void Key(Buffer &b, std::size_t offset, std::string_view text) {
  std::memcpy(b.data() + offset, text.data(), text.size());
  Put(b, offset + 0x10, static_cast<std::uint64_t>(text.size()));
  Put(b, offset + 0x18, std::uint64_t{15});
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
  Bytes<0x100> extension{};
  Bytes<0x8D0> rite{}, main_rite{};
  Bytes<0xB20> doctrine_a{}, doctrine_b{}, doctrine_c{};
  Bytes<0x40> group_a{}, group_b{};
  Bytes<0x70> database{};
  std::array<const void *, 2> learned{doctrine_a.data(), doctrine_b.data()};
  std::array<const void *, 1> rite_doctrines{doctrine_c.data()};
  std::array<const void *, 3> registry{doctrine_a.data(), doctrine_b.data(), doctrine_c.data()};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  void *database_ptr = database.data();
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::uint32_t rite_id = 0x82000002;
  int knows_calls = 0;
  bool wrong_subject = false, drift = false;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, actor_id);
    Put(character, r::kCharacterRiteIdOffset, rite_id);
    Put(character, d::kCharacterKnowledgeExtensionOffset, extension.data());
    Put(rite, 8, rite_id); Put(main_rite, 8, std::uint32_t{0x83000002});
    Put(extension, d::kLearnedDoctrineArrayOffset, learned.data());
    Put(extension, d::kLearnedDoctrineCountOffset, std::int32_t{2});
    Put(rite, d::kMainRiteDoctrineArrayOffset, rite_doctrines.data());
    Put(rite, d::kMainRiteDoctrineCountOffset, std::int32_t{1});
    Put(database, d::kDefinitionRegistryArrayOffset, registry.data());
    Put(database, d::kDefinitionRegistryCountOffset, std::int32_t{3});
    Key(group_a, d::kDoctrineGroupStableKeyOffset, "group_a");
    Key(group_b, d::kDoctrineGroupStableKeyOffset, "group_b");
    Key(doctrine_a, d::kDoctrineStableKeyOffset, "doctrine_a");
    Key(doctrine_b, d::kDoctrineStableKeyOffset, "doc\"\xe4\xbf\xa1");
    Key(doctrine_c, d::kDoctrineStableKeyOffset, "doctrine_c");
    Put(doctrine_a, d::kDoctrineGroupPointerOffset, group_a.data());
    Put(doctrine_b, d::kDoctrineGroupPointerOffset, group_a.data());
    Put(doctrine_c, d::kDoctrineGroupPointerOffset, group_b.data());
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *CharacterRite(void *character) {
  if (character != f->character.data()) f->wrong_subject = true;
  return f->rite.data();
}
bool NativeKnown(void *character, const void *definition) {
  if (character != f->character.data()) f->wrong_subject = true;
  ++f->knows_calls;
  if (f->drift) return f->knows_calls % 2 != 0;
  const auto *extension = Load<const void *>(character, d::kCharacterKnowledgeExtensionOffset);
  const auto *owner = extension ? extension : f->rite.data();
  const auto array_at = extension ? d::kLearnedDoctrineArrayOffset : d::kMainRiteDoctrineArrayOffset;
  const auto count_at = extension ? d::kLearnedDoctrineCountOffset : d::kMainRiteDoctrineCountOffset;
  const auto *rows = Load<const void *const *>(owner, array_at);
  const auto count = Load<std::int32_t>(owner, count_at);
  for (std::int32_t i = 0; i < count; ++i) if (rows[i] == definition) return true;
  return false;
}
d::KnowledgeBindings Bind(Fixture &value) {
  f = &value;
  d::KnowledgeBindings b{};
  b.context.enabled = true;
  b.context.core = {true, &f->state_ptr, &f->jomini_ptr, &f->storage_ptr, &Player};
  b.context.character_rite = &CharacterRite;
  b.knows_doctrine = &NativeKnown;
  b.definition_database_global = &f->database_ptr;
  return b;
}

} // namespace

#include <atomic>
#include <chrono>
#include <thread>
#include <stdexcept>

#if defined(XAR_DOCTRINE_KNOWLEDGE_MAILBOX_STANDALONE_ADAPTER)
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
    // Existing primary fixture permit. The central deployed DLL assigns the
    // named permitted_executor_religion_doctrine_knowledge12002 separately.
    mailbox.permitted_executor = &c::ExecutePlayerReligionDoctrineKnowledgeMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2; ++i)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};

bool Query(Fixture &fixture, FrameAdapter &adapter, const std::filesystem::path &directory,
           const char *filename, std::optional<std::string> key,
           c::PlayerReligionDoctrineKnowledgeMailboxContext12002 &query) {
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(fixture, mailbox);
  query = {};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 709;
  query.bindings = Bind(fixture);
  query.doctrine_key = std::move(key);
  adapter.reads = 0;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::RunPlayerReligionDoctrineKnowledgeMailbox12002(query,
        "doctrine\"knowledge-fixture", serialized, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Check(drained, "actual queued knowledge executor drained on owner");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual mailbox reclaimed");
  if (result) {
    Check(failure.empty() && query.completed && query.envelope.frame_stable && !serialized.empty(), "real wrapped result");
    const auto epoch = query.doctrine_key ? query.lookup_observation.capture_epoch : query.learned_observation.capture_epoch;
    Check(epoch == query.envelope.execution_stamp.pump_epoch && epoch != 709,
          "actual pump epoch distinct from published revision");
    std::ofstream(directory / filename) << serialized << '\n';
  } else Check(serialized.empty() && !failure.empty(), "unstable query has no successful packet");
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
    adapter.frame.played_character_id = Fixture::actor_id;
    adapter.frame.date_raw = Load<std::int32_t>(fixture.state.data(), 8);
    c::PlayerReligionDoctrineKnowledgeMailboxContext12002 query{};
    Check(Query(fixture, adapter, directory, "learned-current.json", std::nullopt, query) &&
          query.learned_observation.available && query.learned_observation.learned_rows.size() == 2,
          "actual learned provider through slot runtime");
    Check(Query(fixture, adapter, directory, "lookup-known.json", std::string("doctrine_a"), query) &&
          query.lookup_observation.available && query.lookup_observation.native_knows_doctrine == true,
          "actual stable key mode native known");
    Check(Query(fixture, adapter, directory, "lookup-not-known.json", std::string("doctrine_c"), query) &&
          query.lookup_observation.available && query.lookup_observation.native_knows_doctrine == false,
          "actual key mode native false not nullable absence");
    Check(Query(fixture, adapter, directory, "lookup-absent.json", std::string("not_a_definition"), query) &&
          query.lookup_observation.available && !query.lookup_observation.definition &&
          !query.lookup_observation.native_knows_doctrine,
          "registry missing authored definition stays distinct from native false");
    fixture.database_ptr = nullptr;
    Check(Query(fixture, adapter, directory, "lookup-registry-unavailable.json", std::string("doctrine_a"), query) &&
          !query.lookup_observation.available && query.lookup_observation.played_character_id == Fixture::actor_id &&
          query.lookup_observation.date_raw == adapter.frame.date_raw,
          "typed native unavailable still has actual query frame");
    fixture.database_ptr = fixture.database.data();
    Put(fixture.extension, d::kLearnedDoctrineCountOffset, std::int32_t{0});
    Check(Query(fixture, adapter, directory, "learned-empty.json", std::nullopt, query) &&
          query.learned_observation.available && query.learned_observation.learned_rows.empty(),
          "actual known empty cached list through wrapper");
    adapter.drift = true;
    Check(!Query(fixture, adapter, directory, "frame-drift.json", std::nullopt, query),
          "real published owner frame changed after capture");
    adapter.drift = false;
    std::uint64_t revision = 0; std::optional<std::string> key;
    Check(c::ParsePlayerReligionDoctrineKnowledgeRequest12002("{}", revision, key) && revision == 0 && !key,
          "optional revision and no-key learned mode");
    Check(c::ParsePlayerReligionDoctrineKnowledgeRequest12002("{\"expected_revision\":709,\"doctrine_key\":\"doctrine_a\"}",
          revision, key) && revision == 709 && key == "doctrine_a", "key and revision alias parsed");
    Check(c::ParsePlayerReligionDoctrineKnowledgeRequest12002("{\"expected_snapshot_revision\":709,\"expected_revision\":709}",
          revision, key), "matching revision aliases");
    Check(!c::ParsePlayerReligionDoctrineKnowledgeRequest12002("{\"expected_snapshot_revision\":709,\"expected_revision\":710}",
          revision, key), "conflicting aliases rejected");
    Check(!c::ParsePlayerReligionDoctrineKnowledgeRequest12002("{\"doctrine_key\":1}", revision, key), "non-string key rejected");
    Check(!c::ParsePlayerReligionDoctrineKnowledgeRequest12002("{\"doctrine_key\":\"\"}", revision, key), "empty authored key rejected");
    api::MainThreadQueryMailboxV1 mailbox{};
    std::string wire, failure;
    Check(!c::HandlePlayerReligionDoctrineKnowledgePrivate12002(adapter, mailbox, adapter.frame, 709,
          c::kPlayerReligionDoctrineKnowledgePrivateStep12002, "{\"expected_revision\":710}", "stale", wire, failure) &&
          wire.empty() && failure == "player_religion_doctrine_knowledge_current_frame_unavailable" && mailbox.next_sequence == 0,
          "actual handler rejects stale revision before real submission");
    Check(c::IsPlayerReligionDoctrineKnowledgePrivateStep12002(c::kPlayerReligionDoctrineKnowledgePrivateStep12002) &&
          !c::IsPlayerReligionDoctrineKnowledgePrivateStep12002("query-player-religion-doctrine-knowledge-v1-other"),
          "exact private selector");
    std::cout << "PASS checks=" << checks << " actual_core=true actual_provider=true actual_mailbox_submit_drain_wait_reclaim=true actual_wrapper=true live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
