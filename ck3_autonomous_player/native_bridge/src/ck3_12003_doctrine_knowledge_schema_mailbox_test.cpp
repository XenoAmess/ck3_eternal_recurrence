// FIRST_NOTRUN: five new complete .3 command_result packets. Fixture-owned
// synthetic memory and callbacks exercise existing production readers,
// named owner mailbox, serializers and the real reviewed .3 renderer.
// No old fixture main, replacement DTO/API or production linkage stub.
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/religion_doctrine12002_choices_mailbox.hpp"

#include <windows.h>

#include <array>
#include <atomic>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <thread>
#include <utility>

namespace {
namespace c = xar::ck3_12002;
namespace r = c::religion;
namespace d = r::doctrine12002;
namespace game = xar::game;
namespace api = xar::ck3_11906;

unsigned checks{};
void Assert(bool condition, const char *message) {
  ++checks;
  if (!condition) throw std::runtime_error(message);
}
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <class Buffer, class T> void Put(Buffer &buffer, std::size_t offset, T value) {
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}
template <class T> T Load(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
template <class Buffer> void Key(Buffer &buffer, std::size_t offset, std::string_view text) {
  std::memcpy(buffer.data() + offset, text.data(), text.size());
  Put(buffer, offset + 0x10, static_cast<std::uint64_t>(text.size()));
  Put(buffer, offset + 0x18, std::uint64_t{15});
}

class FrameAdapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  const DWORD owner = GetCurrentThreadId();
  mutable unsigned reads{};
  game::AdapterDescriptor identity{xar::ck3_12003::kAdapterId, xar::ck3_12003::kGameVersion,
      xar::ck3_12003::kExecutableSha256, "doctrine-schema-synthetic-fixture", {}};
  const game::AdapterDescriptor &descriptor() const noexcept override { return identity; }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    if (GetCurrentThreadId() != owner) return false;
    out = frame; ++reads; return true;
  }
  game::PauseSubmitResult submit_pause_map(game::Snapshot *) const noexcept override { return game::PauseSubmitResult::unavailable; }
  game::ResumeSubmitResult submit_resume_map(game::Snapshot *) const noexcept override { return game::ResumeSubmitResult::unavailable; }
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  game::SelectEventOptionResult submit_select_event_option(std::int32_t) const noexcept override { return game::SelectEventOptionResult::unavailable; }
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override { return {}; }
  game::ReplyPendingInteractionResult submit_reply_to_pending_interaction(game::PendingInteractionReply) const noexcept override { return game::ReplyPendingInteractionResult::unavailable; }
  game::RaiseTroopsResult submit_raise_troops_default() const noexcept override { return game::RaiseTroopsResult::unavailable; }
  game::MoveArmyResult submit_move_army(std::int32_t, std::int32_t) const noexcept override { return game::MoveArmyResult::unavailable; }
  game::PreviewMoveArmyResult preview_move_army(std::int32_t, std::int32_t) const noexcept override { return {}; }
  game::DisbandArmyResult submit_disband_army(std::int32_t) const noexcept override { return game::DisbandArmyResult::unavailable; }
  game::SplitArmyHalfResult submit_split_army_half(std::int32_t) const noexcept override { return game::SplitArmyHalfResult::unavailable; }
  game::MergeArmiesResult submit_merge_armies(std::int32_t, std::int32_t) const noexcept override { return game::MergeArmiesResult::unavailable; }
  game::StartAssaultResult submit_start_assault(std::int32_t) const noexcept override { return game::StartAssaultResult::unavailable; }
  game::StopAssaultResult submit_stop_assault(std::int32_t) const noexcept override { return game::StopAssaultResult::unavailable; }
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &) const noexcept override { return false; }
  game::ReadDeclarableWarsResult read_declarable_wars_for_target(std::int32_t, std::vector<game::DeclarableWarSnapshot> &) const noexcept override { return game::ReadDeclarableWarsResult::unavailable; }
  game::DeclareWarResult submit_declare_war(const game::DeclarableWarSnapshot &) const noexcept override { return game::DeclareWarResult::unavailable; }
  game::ReadArrangeMarriageChoicesResult read_arrange_marriage_choices(std::vector<game::ArrangeMarriageChoice> &, game::ArrangeMarriageQueryDiagnostics &) const noexcept override { return game::ReadArrangeMarriageChoicesResult::unavailable; }
  game::ArrangeMarriageResult submit_arrange_marriage(const game::ArrangeMarriageChoice &) const noexcept override { return game::ArrangeMarriageResult::unavailable; }
  game::EnforceDemandsResult submit_enforce_demands(std::int32_t) const noexcept override { return game::EnforceDemandsResult::unavailable; }
  game::SurrenderWarResult submit_surrender_war(std::int32_t) const noexcept override { return game::SurrenderWarResult::unavailable; }
  game::OfferWhitePeaceResult submit_offer_white_peace(std::int32_t) const noexcept override { return game::OfferWhitePeaceResult::unavailable; }
  game::ReadArmyStrengthsResult read_army_strengths(std::vector<game::ArmyStrengthSnapshot> &) const noexcept override { return game::ReadArmyStrengthsResult::unavailable; }
  game::ReadCombatSimulationInputsResult read_combat_simulation_inputs(const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &) const noexcept override { return game::ReadCombatSimulationInputsResult::unavailable; }
  game::ReadCombatSimulationInputsV3Result read_combat_simulation_inputs_v3(const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &) const noexcept override { return game::ReadCombatSimulationInputsV3Result::unavailable; }
  game::ReadWarTerminationOptionsResult read_war_termination_options(std::int32_t, game::WarTerminationOptionsSnapshot &) const noexcept override { return game::ReadWarTerminationOptionsResult::unavailable; }
  game::ReadWarTerminationTermsResult read_war_termination_terms(std::int32_t, game::WarTerminationTermsSnapshot &) const noexcept override { return game::ReadWarTerminationTermsResult::unavailable; }
  game::ReadWarTerminationExitTermsResult read_war_termination_exit_terms(std::int32_t, game::WarTerminationExitTermsSnapshot &) const noexcept override { return game::ReadWarTerminationExitTermsResult::unavailable; }
};

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
  std::array<const void *, 3> learned{doctrine_b.data(), doctrine_a.data(), doctrine_b.data()};
  std::array<const void *, 1> main_doctrines{doctrine_c.data()};
  std::array<const void *, 3> registry{doctrine_a.data(), doctrine_b.data(), doctrine_c.data()};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  void *database_ptr = database.data();
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::int32_t date = 53175816;
  static constexpr std::uint32_t rite_id = 0x82000002;
  unsigned knows_calls{}, rite_calls{};
  bool callback_scope_valid = true;

  Fixture() {
    Put(state, 8, date); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, actor_id);
    Put(character, r::kCharacterRiteIdOffset, rite_id);
    SetExtension(true);
    Put(rite, 8, rite_id); Put(main_rite, 8, std::uint32_t{0x83000002});
    Put(extension, d::kLearnedDoctrineArrayOffset, learned.data());
    Put(extension, d::kLearnedDoctrineCountOffset, std::int32_t{3});
    // A real current-Rite empty collection is distinct from this nonempty
    // main-Rite collection, which the knowledge reader must never substitute.
    Put(rite, d::kMainRiteDoctrineArrayOffset, static_cast<const void *const *>(nullptr));
    Put(rite, d::kMainRiteDoctrineCountOffset, std::int32_t{0});
    Put(main_rite, d::kMainRiteDoctrineArrayOffset, main_doctrines.data());
    Put(main_rite, d::kMainRiteDoctrineCountOffset, std::int32_t{1});
    Put(database, d::kDefinitionRegistryArrayOffset, registry.data());
    Put(database, d::kDefinitionRegistryCountOffset, std::int32_t{3});
    Key(group_a, d::kDoctrineGroupStableKeyOffset, "group_a");
    Key(group_b, d::kDoctrineGroupStableKeyOffset, "group_b");
    Key(doctrine_a, d::kDoctrineStableKeyOffset, "doctrine_a");
    Key(doctrine_b, d::kDoctrineStableKeyOffset, "doctrine_b");
    Key(doctrine_c, d::kDoctrineStableKeyOffset, "doctrine_c");
    Put(doctrine_a, d::kDoctrineGroupPointerOffset, group_a.data());
    Put(doctrine_b, d::kDoctrineGroupPointerOffset, group_a.data());
    Put(doctrine_c, d::kDoctrineGroupPointerOffset, group_b.data());
  }
  void SetExtension(bool present) {
    Put(character, d::kCharacterKnowledgeExtensionOffset, present ? extension.data() : nullptr);
  }
  void ResetCounters() { knows_calls = rite_calls = 0; callback_scope_valid = true; }
};
Fixture *fixture_state = nullptr;
void *Player(void *) { return fixture_state->player.data(); }
void *CharacterRite(void *actor) {
  auto &f = *fixture_state;
  ++f.rite_calls;
  f.callback_scope_valid = f.callback_scope_valid && actor == f.character.data();
  return f.rite.data();
}
bool NativeKnown(void *actor, const void *definition) {
  auto &f = *fixture_state;
  ++f.knows_calls;
  f.callback_scope_valid = f.callback_scope_valid && actor == f.character.data() &&
      (definition == f.doctrine_a.data() || definition == f.doctrine_b.data() || definition == f.doctrine_c.data());
  const auto *extension = Load<const void *>(actor, d::kCharacterKnowledgeExtensionOffset);
  const auto *owner = extension ? extension : f.rite.data();
  const auto array_at = extension ? d::kLearnedDoctrineArrayOffset : d::kMainRiteDoctrineArrayOffset;
  const auto count_at = extension ? d::kLearnedDoctrineCountOffset : d::kMainRiteDoctrineCountOffset;
  const auto *rows = Load<const void *const *>(owner, array_at);
  const auto count = Load<std::int32_t>(owner, count_at);
  for (std::int32_t i = 0; i < count; ++i)
    if (rows[i] == definition) return true;
  return false;
}
d::KnowledgeBindings Bind(Fixture &f) {
  fixture_state = &f;
  d::KnowledgeBindings b{};
  b.context.enabled = true;
  b.context.core = {true, &f.state_ptr, &f.jomini_ptr, &f.storage_ptr, &Player};
  b.context.character_rite = &CharacterRite;
  b.knows_doctrine = &NativeKnown;
  b.definition_database_global = &f.database_ptr;
  return b;
}

void *tls_context = nullptr;
void *__fastcall FixtureTls() noexcept { return tls_context; }
struct Pump {
  Bytes<0x28> tls{};
  std::uint8_t initialized = 1;
  std::uintptr_t unused_rng{};
  Pump(Fixture &f, api::MainThreadQueryMailboxV1 &mailbox) {
    tls[0x20] = std::byte{1}; tls_context = tls.data();
    mailbox.global_rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&unused_rng);
    mailbox.jomini_state_slot = reinterpret_cast<std::uintptr_t>(&f.jomini_ptr);
    mailbox.game_state_slot = reinterpret_cast<std::uintptr_t>(&f.state_ptr);
    mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter = &FixtureTls;
    mailbox.executor_submission_enabled = true;
    mailbox.permitted_executor_religion_doctrine_knowledge12002 = &c::ExecutePlayerReligionDoctrineKnowledgeMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2; ++i)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};

struct Result {
  d::PlayedDoctrineKnowledge learned;
  d::PlayedDoctrineKnowledgeLookup lookup;
};
Result Query(Fixture &f, FrameAdapter &adapter, const std::filesystem::path &directory,
    const char *filename, std::string_view payload) {
  f.ResetCounters();
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(f, mailbox);
  c::PlayerReligionDoctrineKnowledgeMailboxContext12002 query{};
  std::uint64_t revision{};
  Assert(c::ParsePlayerReligionDoctrineKnowledgeRequest12002(payload, revision, query.doctrine_key) &&
      revision == std::uint64_t{701}, "existing request parser preserves actual revision and query mode");
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = revision;
  query.bindings = Bind(f);
  adapter.reads = 0;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::RunPlayerReligionDoctrineKnowledgeMailbox12002(query,
        "doctrine-schema-synthetic-fixture", serialized, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Assert(result && drained && failure.empty() && query.completed && query.envelope.frame_stable,
      "actual existing named owner mailbox and serializer complete");
  Assert(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual mailbox reclaimed");
  const auto epoch = query.doctrine_key ? query.lookup_observation.capture_epoch : query.learned_observation.capture_epoch;
  const auto actor = query.doctrine_key ? query.lookup_observation.played_character_id : query.learned_observation.played_character_id;
  const auto date = query.doctrine_key ? query.lookup_observation.date_raw : query.learned_observation.date_raw;
  Assert(epoch == query.envelope.execution_stamp.pump_epoch && epoch > 0 && epoch != revision &&
      actor == Fixture::actor_id && date == Fixture::date, "actual native owner metadata is independent of published revision");
  Assert(f.callback_scope_valid, "synthetic native callbacks receive actual actor and actual definition pointers");
  const auto mode = query.doctrine_key ? "by_key" : "learned_rows";
  const auto original_schema = query.doctrine_key ? "ck3_12002_played_doctrine_knowledge_lookup_v1"
      : "ck3_12002_played_doctrine_knowledge_v1";
  const auto selected_schema = query.doctrine_key ? "ck3_12003_played_doctrine_knowledge_lookup_v1"
      : "ck3_12003_played_doctrine_knowledge_v1";
  Assert(serialized.find(original_schema) != std::string::npos &&
      serialized.find(std::string{"\"query_mode\":\""} + mode + '"') != std::string::npos,
      "existing unchanged domain DTO and serializer provide selected learned or lookup mode");
  const auto rendered = game::RenderCrozierBuildIdentity(std::move(serialized), adapter.descriptor());
  Assert(rendered.find("\"type\":\"command_result\"") != std::string::npos &&
      rendered.find("\"snapshot_revision\":701") != std::string::npos &&
      rendered.find("\"game_version\":\"1.20.0.3\"") != std::string::npos &&
      rendered.find(xar::ck3_12003::kExecutableSha256) != std::string::npos &&
      rendered.find(selected_schema) != std::string::npos && rendered.find(original_schema) == std::string::npos,
      "actual reviewed .3 renderer supplies complete production schema and build identity");
  std::ofstream output(directory / filename, std::ios::binary);
  output << rendered << '\n';
  Assert(static_cast<bool>(output), "native complete business wire written");
  return {std::move(query.learned_observation), std::move(query.lookup_observation)};
}

void Lookup(Fixture &f, const Result &out, const char *key, const char *group, bool known) {
  const auto &value = out.lookup;
  Assert(value.available && value.unavailable_reason.empty() && value.requested_doctrine_key == key &&
      value.definition && value.native_knows_doctrine == known, "lookup preserves independent native true and false");
  Assert(value.definition->doctrine_key == key && value.definition->group_key == group &&
      value.definition->source == "definition_registry", "lookup copies actual loaded registry definition");
  Assert(f.knows_calls == 2U && f.rite_calls == 0U, "lookup samples native predicate twice using actual actor");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Assert(argc == 2, "output directory argument");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    Fixture f; FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::actor_id; adapter.frame.date_raw = Fixture::date;
    constexpr auto learned_request = "{\"expected_snapshot_revision\":701}";
    auto out = Query(f, adapter, directory, "learned-e0-order-duplicates.json", learned_request);
    const auto &learned = out.learned;
    Assert(learned.available && learned.unavailable_reason.empty() && learned.rite_id == Fixture::rite_id &&
        learned.knowledge_source == "character_extension" && learned.learned_rows.size() == std::size_t{3},
        "existing actual E0 reader retains complete rows and full current Rite reference");
    const std::array<std::string_view, 3> keys{"doctrine_b", "doctrine_a", "doctrine_b"};
    for (std::size_t i = 0; i < keys.size(); ++i) {
      const auto &row = learned.learned_rows[i];
      Assert(row.definition.doctrine_key == keys[i] && row.definition.group_key == "group_a" &&
          row.definition.source == "character_extension" && row.native_knows_doctrine,
          "E0 source order and duplicate occurrences remain actual native observations");
    }
    Assert(f.knows_calls == 6U && f.rite_calls == 0U, "E0 rows receive two actual native-predicate samples");

    f.SetExtension(false);
    out = Query(f, adapter, directory, "learned-rite-default-empty.json", learned_request);
    Assert(out.learned.available && out.learned.unavailable_reason.empty() &&
        out.learned.rite_id == Fixture::rite_id && out.learned.knowledge_source == "rite_default" &&
        out.learned.learned_rows.empty() && f.rite_calls == 2U && f.knows_calls == 0U,
        "native fallback reads actual current-Rite empty collection instead of main-Rite nonempty data");

    f.SetExtension(true);
    out = Query(f, adapter, directory, "lookup-known-true.json",
        "{\"expected_snapshot_revision\":701,\"doctrine_key\":\"doctrine_a\"}");
    Lookup(f, out, "doctrine_a", "group_a", true);
    out = Query(f, adapter, directory, "lookup-known-false.json",
        "{\"expected_snapshot_revision\":701,\"doctrine_key\":\"doctrine_c\"}");
    Lookup(f, out, "doctrine_c", "group_b", false);
    out = Query(f, adapter, directory, "lookup-definition-not-found.json",
        "{\"expected_snapshot_revision\":701,\"doctrine_key\":\"doctrine_absent\"}");
    Assert(out.lookup.available && out.lookup.unavailable_reason.empty() &&
        out.lookup.requested_doctrine_key == "doctrine_absent" && !out.lookup.definition &&
        !out.lookup.native_knows_doctrine && f.knows_calls == 0U && f.rite_calls == 0U,
        "legitimate missing registry definition is null, independently of known false and capture failure");
    std::cout << "PASS cases=5 checks=" << checks
        << " actual_existing_reader=true actual_named_mailbox=true actual_serializer=true actual_renderer=true"
        << " actual_full_wire=true synthetic_memory=true synthetic_callbacks=true legacy_main_executed=false live=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
