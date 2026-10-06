// FIRST_NOTRUN. Owned synthetic memory and synthetic native callbacks only.
// Runs the actual new reader, existing owner mailbox, serializer and .3
// renderer. No older fixture main or production image-factory stub is used.
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12003_player_tenet_knowledge_catalogue.hpp"
#include "xar_bridge/religion_doctrine12002_tenet_rows_mailbox.hpp"

#include <windows.h>

#include <array>
#include <atomic>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <initializer_list>
#include <iostream>
#include <stdexcept>
#include <thread>
#include <utility>

namespace {
namespace game = xar::game;
namespace api = xar::ck3_11906;
namespace c = xar::ck3_12002;
namespace r = c::religion;
namespace d = r::doctrine12002;
namespace knowledge = xar::ck3_12003::religion::tenet_knowledge;
namespace target = xar::ck3_12003::religion::target_tenet;

unsigned checks = 0;
void Assert(bool condition, const char *message) {
  ++checks;
  if (!condition) throw std::runtime_error(message);
}
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <class Buffer, class T> void Put(Buffer &buffer, std::size_t at, T value) {
  std::memcpy(buffer.data() + at, &value, sizeof(value));
}
template <class T> T Load(const void *buffer, std::size_t at = 0) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(buffer) + at, sizeof(value));
  return value;
}
template <class Buffer, class P>
void SetArray(Buffer &buffer, std::size_t at, P data, std::int32_t count) {
  Put(buffer, at, data);
  Put(buffer, at + 8, count);
  Put(buffer, at + 0xC, count);
}

class FrameAdapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  const DWORD owner = GetCurrentThreadId();
  mutable unsigned reads{};
  game::AdapterDescriptor identity{xar::ck3_12003::kAdapterId, xar::ck3_12003::kGameVersion,
      xar::ck3_12003::kExecutableSha256, "tenet-knowledge-synthetic-fixture", {}};
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

// The established played-frame and TenetRows memory layouts, independently
// instantiated here so only these seven FIRST cases can execute.
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
  Bytes<0x800> rite{}, main_rite{}, target_rite{};
  Bytes<0x320> faith{};
  Bytes<0xD8> extension{};
  std::array<Bytes<64>, 5> definitions{};
  std::array<const void *, 2> core{definitions[4].data(), definitions[4].data()};
  std::array<const void *, 1> main_core{definitions[3].data()};
  std::array<const void *, 2> target_core{definitions[2].data(), definitions[2].data()};
  std::array<const void *, 1> personal{definitions[2].data()};
  std::array<Bytes<16>, 3> states{};
  Bytes<0x30> rite_storage{};
  Bytes<0x40> rite_slots{};
  Bytes<0xF00> tenet_database{}, perk_database{};
  Bytes<0x10> default_extra{}, perks_collection{};
  Bytes<0x40> prophet_definition{};
  std::vector<const void *> loaded, extra, perks;
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  void *rite_storage_ptr = rite_storage.data();
  void *tenet_database_ptr = tenet_database.data(), *perk_database_ptr = perk_database.data();
  static constexpr std::int32_t character_id = 0x03000004;
  static constexpr std::int32_t date = 53175816;
  static constexpr std::uint32_t current_id = 0, main_id = 0x82000002, faith_id = 0x83000003;
  static constexpr std::uint32_t target_id = 0x85000003;
  unsigned extra_calls{}, perks_calls{}, contains_extra_calls{}, contains_perks_calls{};
  bool callback_scope_valid = true;

  Fixture() {
    Put(state, 8, date); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, character_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, character_id);
    Put(character, r::kCharacterRiteIdOffset, current_id);
    SetExtension(true);
    Put(rite, 8, current_id); Put(main_rite, 8, main_id); Put(target_rite, 8, target_id);
    Put(rite, 0xC, std::uint32_t{0x52697465});
    Put(main_rite, 0xC, std::uint32_t{0x52697465});
    Put(target_rite, 0xC, std::uint32_t{0x52697465});
    Put(rite, r::kRiteFaithIdOffset, faith_id);
    Put(main_rite, r::kRiteFaithIdOffset, faith_id);
    Put(target_rite, r::kRiteFaithIdOffset, faith_id);
    Put(faith, 8, faith_id); Put(faith, r::kFaithMainRiteIdOffset, main_id);
    SetArray(rite, d::kRiteCoreTenetsOffset, core.data(), 2);
    SetArray(main_rite, d::kRiteCoreTenetsOffset, main_core.data(), 1);
    SetArray(target_rite, d::kRiteCoreTenetsOffset, target_core.data(), 2);
    SetArray(extension, d::kPersonalTenetsOffset, personal.data(), 1);
    for (std::size_t i = 0; i < definitions.size(); ++i) {
      const auto key = "tenet_" + std::to_string(i);
      std::memcpy(definitions[i].data() + 0x18, key.data(), key.size());
      Put(definitions[i], 0x28, static_cast<std::uint64_t>(key.size()));
      Put(definitions[i], 0x30, std::uint64_t{15});
      Put(definitions[i], 0x38, std::uint32_t{0x4744624F});
    }
    for (std::size_t i = 0; i < states.size(); ++i) {
      Put(states[i], 0, definitions[i].data());
      Put(states[i], 8, static_cast<std::uint8_t>(i));
    }
    SetArray(main_rite, d::kRiteTenetStatesOffset, states.data(), 3);
    Put(rite_storage, 0x20, rite_slots.data()); Put(rite_storage, 0x2C, std::uint32_t{4});
    Put(rite_slots, 8, rite.data());
    Put(rite_slots, 2 * 0x10 + 8, main_rite.data());
    Put(rite_slots, 3 * 0x10 + 8, target_rite.data());
    SetLoaded({0, 1, 2}); SetExtra({1}); SetProphet(false);
  }
  void SetExtension(bool present) {
    Put(character, d::kCharacterExtensionOffset, present ? extension.data() : nullptr);
  }
  void SetLoaded(std::initializer_list<std::size_t> indices) {
    loaded.clear();
    for (const auto i : indices) loaded.push_back(definitions[i].data());
    SetArray(tenet_database, 0xEF0, loaded.data(), static_cast<std::int32_t>(loaded.size()));
  }
  void SetExtra(std::initializer_list<std::size_t> indices) {
    extra.clear();
    for (const auto i : indices) extra.push_back(definitions[i].data());
    SetArray(extension, 0xC8, extra.data(), static_cast<std::int32_t>(extra.size()));
  }
  void SetProphet(bool present, bool fixed_definition_available = true) {
    Put(perk_database, 0xEF0, fixed_definition_available ? prophet_definition.data() : nullptr);
    perks.clear();
    if (present) perks.push_back(prophet_definition.data());
    SetArray(perks_collection, 0, perks.data(), static_cast<std::int32_t>(perks.size()));
  }
  void ResetCounters() {
    extra_calls = perks_calls = contains_extra_calls = contains_perks_calls = 0;
    callback_scope_valid = true;
  }
};
Fixture *fixture_state = nullptr;
void *Player(void *) { return fixture_state->player.data(); }
void *CharacterRite(void *) { return fixture_state->rite.data(); }
void *CharacterFaith(void *) { return fixture_state->faith.data(); }
void *RiteFaith(void *) { return fixture_state->faith.data(); }
void *FaithMainRite(void *) { return fixture_state->main_rite.data(); }
std::uint8_t State(void *, const void *definition) {
  for (std::size_t i = 0; i < fixture_state->definitions.size(); ++i)
    if (definition == fixture_state->definitions[i].data()) return static_cast<std::uint8_t>(i);
  return 0;
}
std::uint8_t ComparisonState(void *rite, const void *definition) {
  if (rite == fixture_state->target_rite.data() && definition == fixture_state->definitions[1].data())
    return 3;
  return State(rite, definition);
}
const void *Extra(void *actor) {
  auto &f = *fixture_state;
  ++f.extra_calls;
  f.callback_scope_valid = f.callback_scope_valid && actor == f.character.data();
  const auto *extension = Load<const std::byte *>(actor, d::kCharacterExtensionOffset);
  return extension ? extension + 0xC8 : f.default_extra.data();
}
const void *Perks(void *actor) {
  auto &f = *fixture_state;
  ++f.perks_calls;
  f.callback_scope_valid = f.callback_scope_valid && actor == f.character.data();
  return f.perks_collection.data();
}
bool Contains(const void *collection, const void *definition_argument) {
  auto &f = *fixture_state;
  const auto *definition = definition_argument ? Load<const void *>(definition_argument) : nullptr;
  if (collection == f.perks_collection.data()) {
    ++f.contains_perks_calls;
    f.callback_scope_valid = f.callback_scope_valid && definition == f.prophet_definition.data();
  } else if (collection == f.extension.data() + 0xC8 || collection == f.default_extra.data()) {
    ++f.contains_extra_calls;
    bool loaded_pointer = false;
    for (const auto *item : f.loaded) loaded_pointer = loaded_pointer || item == definition;
    f.callback_scope_valid = f.callback_scope_valid && loaded_pointer;
  } else {
    f.callback_scope_valid = false;
    return false;
  }
  const auto *data = Load<const std::byte *>(collection);
  const auto count = Load<std::int32_t>(collection, 0xC);
  for (std::int32_t i = 0; i < count; ++i)
    if (Load<const void *>(data, static_cast<std::size_t>(i) * sizeof(void *)) == definition)
      return true;
  return false;
}
r::Bindings Bind(Fixture &f) {
  fixture_state = &f;
  r::Bindings b{}; b.enabled = true;
  b.core = {true, &f.state_ptr, &f.jomini_ptr, &f.storage_ptr, &Player};
  b.character_rite = &CharacterRite; b.character_faith = &CharacterFaith;
  b.rite_faith = &RiteFaith; b.faith_main_rite = &FaithMainRite;
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
    mailbox.permitted_executor = &c::ExecutePlayerReligionTenetsMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2; ++i)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};

struct Result {
  knowledge::Catalogue catalogue;
  target::Comparison comparison;
  d::TenetRowsContext old;
};
Result Query(Fixture &f, FrameAdapter &adapter, const std::filesystem::path &directory,
    const char *filename, std::string_view payload) {
  f.ResetCounters();
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(f, mailbox);
  c::PlayerReligionTenetsMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 701;
  query.bindings = Bind(f); query.tenet_bindings = {true, &State};
  Assert(c::ParsePlayerReligionTenetsKnowledgeRequest12003(payload, query.include_knowledge_catalogue),
      "request knowledge flag parsed by actual parser");
  Assert(c::ParsePlayerReligionTenetsComparisonRequest12003(payload, query.target_rite_id, query.tenet_key),
      "independent target/key pair parsed by actual parser");
  query.knowledge_bindings = {query.bindings, &f.tenet_database_ptr, &f.perk_database_ptr,
      &Extra, &Perks, &Contains};
  // These unrelated getters are deliberately absent from the knowledge leaf.
  query.knowledge_bindings.context.character_rite = nullptr;
  query.knowledge_bindings.context.character_faith = nullptr;
  query.knowledge_bindings.context.rite_faith = nullptr;
  query.knowledge_bindings.context.faith_main_rite = nullptr;
  query.comparison_bindings = {query.bindings, &f.rite_storage_ptr, &f.tenet_database_ptr, &ComparisonState};
  adapter.reads = 0;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::RunPlayerReligionTenetsMailbox12002(query, "tenet-knowledge-synthetic-fixture", serialized, failure);
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
      "actual queue executor and complete serializer close");
  Assert(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual mailbox reclaimed");
  Assert(query.observation.available && query.observation.current_rite &&
      query.observation.current_rite->core_tenets.size() == 2, "old result preserved with actual Core duplicates");
  Assert(query.observation.capture_epoch == query.envelope.execution_stamp.pump_epoch &&
      query.observation.capture_epoch > 0 && query.observation.capture_epoch != 701,
      "actual owner epoch differs from published revision");
  auto old_dto = d::SerializeTenetRows12002(query.observation);
  if (query.include_knowledge_catalogue) {
    const auto &k = query.knowledge_catalogue;
    Assert(k.capture_epoch == query.observation.capture_epoch &&
        k.played_character_id == static_cast<std::uint32_t>(Fixture::character_id) &&
        k.date_raw == Fixture::date, "new input owner metadata retained even on typed failure");
    if (!query.target_rite_id) {
      old_dto.pop_back();
      Assert(serialized.find("\"player_religion_tenets\":" + old_dto +
          ",\"player_tenet_knowledge_catalogue\":") != std::string::npos,
          "existing DTO bytes retained before optional knowledge composition");
    }
    Assert(f.callback_scope_valid, "Contains receives actual collection and actual fixed/loaded pointer arguments");
  } else {
    Assert(f.extra_calls == 0 && f.perks_calls == 0 && f.contains_extra_calls == 0 && f.contains_perks_calls == 0,
        "missing and false flag skip every new native callback");
    Assert(serialized.find("\"player_religion_tenets\":" + old_dto + "}}") != std::string::npos &&
        serialized.find("player_tenet_knowledge_catalogue") == std::string::npos,
        "unrequested original DTO serialized bytes unchanged");
  }
  const auto rendered = game::RenderCrozierBuildIdentity(std::move(serialized), adapter.descriptor());
  Assert(rendered.find("\"game_version\":\"1.20.0.3\"") != std::string::npos &&
      rendered.find(xar::ck3_12003::kExecutableSha256) != std::string::npos &&
      rendered.find("\"type\":\"command_result\"") != std::string::npos,
      "actual .3 renderer carries native complete command_result");
  if (filename) {
    std::ofstream output(directory / filename, std::ios::binary);
    output << rendered << '\n';
    Assert(static_cast<bool>(output), "native full wire written");
  }
  return {std::move(query.knowledge_catalogue), std::move(query.comparison), std::move(query.observation)};
}

void Available(Fixture &f, const Result &out, const std::vector<std::string> &keys,
    const std::vector<bool> &membership, const std::vector<std::string> &extra_keys,
    bool has_prophet, bool has_extension = true) {
  const auto &k = out.catalogue;
  Assert(k.available && k.failure == knowledge::Failure::none && k.extra_collection_complete &&
      k.loaded_registry_complete && k.knowledge_inputs_complete, "all actual knowledge inputs complete");
  Assert(k.has_character_extension == has_extension &&
      k.extra_collection_source == (has_extension ? knowledge::ExtraCollectionSource::character_extension_c8
          : knowledge::ExtraCollectionSource::native_default_collection), "actual extension and native accessor source observed");
  Assert(k.extra_tenet_keys == extra_keys &&
      k.loaded_definition_count == static_cast<std::uint32_t>(keys.size()) &&
      k.native_has_prophet == has_prophet && k.rows && k.rows->size() == keys.size(),
      "actual arrays preserve native order, duplicates and observed empty zero");
  Assert(f.extra_calls == 2 && f.perks_calls == 2 && f.contains_perks_calls == 2 &&
      f.contains_extra_calls == 2 * keys.size(), "two actual samples include Prophet even for empty registry");
  for (std::size_t i = 0; i < keys.size(); ++i) {
    const auto &row = (*k.rows)[i];
    Assert(row.source_index == i && row.tenet_key == keys[i] &&
        row.native_extra_knowledge == membership[i] && row.knowledge == (membership[i] || has_prophet),
        "native pointer Contains and knowledge OR, independently of Rite status");
  }
}

void RequestCases(Fixture &f, FrameAdapter &adapter) {
  bool include = true;
  Assert(c::ParsePlayerReligionTenetsKnowledgeRequest12003("{}", include) && !include, "missing flag preserves old route");
  Assert(c::ParsePlayerReligionTenetsKnowledgeRequest12003("{\"include_knowledge_catalogue\":false}", include) && !include,
      "false is a legal unrequested flag");
  Assert(c::ParsePlayerReligionTenetsKnowledgeRequest12003("{\"include_knowledge_catalogue\":true}", include) && include,
      "true parsed as native knowledge request");
  f.ResetCounters();
  for (const auto payload : {"{\"include_knowledge_catalogue\":0}", "{\"include_knowledge_catalogue\":null}",
      "{\"include_knowledge_catalogue\":\"true\"}"}) {
    Assert(!c::ParsePlayerReligionTenetsKnowledgeRequest12003(payload, include), "non-bool flag rejected by actual parser");
    api::MainThreadQueryMailboxV1 mailbox{};
    std::string serialized, failure;
    Assert(!c::HandlePlayerReligionTenetsPrivate12002(adapter, mailbox, adapter.frame, 701,
        c::kPlayerReligionTenetsPrivateStep12002, payload, "invalid-knowledge-request", serialized, failure) &&
        failure == "player_religion_tenets_request_invalid" && serialized.empty() &&
        mailbox.state == api::MainThreadQueryMailboxStateV1::idle,
        "non-bool rejected before native dispatch");
  }
  const auto exact = adapter.identity;
  adapter.identity = game::Ck3_12002AdapterDescriptor();
  api::MainThreadQueryMailboxV1 mailbox{};
  std::string serialized, failure;
  Assert(!c::HandlePlayerReligionTenetsPrivate12002(adapter, mailbox, adapter.frame, 701,
      c::kPlayerReligionTenetsPrivateStep12002, "{\"include_knowledge_catalogue\":true}",
      "wrong-build-knowledge-request", serialized, failure) && failure == "player_religion_tenets_request_invalid" &&
      mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "true requires exact .3 before dispatch");
  adapter.identity = exact;
  Assert(f.extra_calls == 0 && f.perks_calls == 0 && f.contains_extra_calls == 0 && f.contains_perks_calls == 0,
      "invalid requests invoke no native knowledge callbacks");
  std::optional<std::uint32_t> id; std::string key;
  Assert(c::ParsePlayerReligionTenetsComparisonRequest12003("{}", id, key) && !id && key.empty(), "old target absence retained");
  Assert(c::ParsePlayerReligionTenetsComparisonRequest12003(
      "{\"target_rite_id\":0,\"tenet_key\":\"tenet_4\"}", id, key) && id == std::uint32_t{0} && key == "tenet_4",
      "existing target full zero pair retained");
  for (const auto payload : {"{\"target_rite_id\":0}", "{\"tenet_key\":\"tenet_4\"}",
      "{\"target_rite_id\":0,\"tenet_key\":\"\"}",
      "{\"target_rite_id\":4294967296,\"tenet_key\":\"tenet_4\"}"})
    Assert(!c::ParsePlayerReligionTenetsComparisonRequest12003(payload, id, key), "existing invalid pair rejected");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Assert(argc == 2, "output directory argument");
    const std::filesystem::path output(argv[1]);
    std::filesystem::create_directories(output);
    Fixture f; FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::character_id; adapter.frame.date_raw = Fixture::date;
    RequestCases(f, adapter);
    constexpr auto request = "{\"include_knowledge_catalogue\":true}";
    auto out = Query(f, adapter, output, "no-draft-extra-input.json", request);
    Available(f, out, {"tenet_0", "tenet_1", "tenet_2"}, {false, true, false}, {"tenet_1"}, false);
    Assert(out.old.personal_tenets.size() == 1 && out.old.personal_tenets[0].key == "tenet_2" &&
        !(*out.catalogue.rows)[2].native_extra_knowledge, "personal88 is distinct from actual extra C8");
    bool actual_zero = false;
    for (const auto &row : out.old.effective_tenet_states)
      actual_zero = actual_zero || (row.key == "tenet_0" && row.current_rite_status == std::uint8_t{0});
    Assert(actual_zero, "old effective native status zero retained independently of knowledge");

    f.SetLoaded({0, 1}); f.SetExtra({}); f.SetProphet(true);
    out = Query(f, adapter, output, "no-draft-prophet-input.json", request);
    Available(f, out, {"tenet_0", "tenet_1"}, {false, false}, {}, true);

    f.SetExtension(false); f.SetProphet(false);
    out = Query(f, adapter, output, "native-default-empty.json", request);
    Available(f, out, {"tenet_0", "tenet_1"}, {false, false}, {}, false, false);
    Assert(out.old.personal_tenets.empty(), "old personal collection remains independently absent");

    f.SetExtension(true); f.SetLoaded({1, 0, 1}); f.SetExtra({1, 1});
    out = Query(f, adapter, output, "native-order-and-duplicates.json",
        "{\"include_knowledge_catalogue\":true,\"target_rite_id\":2231369731,\"tenet_key\":\"tenet_1\"}");
    Available(f, out, {"tenet_1", "tenet_0", "tenet_1"}, {true, false, true}, {"tenet_1", "tenet_1"}, false);
    Assert(out.comparison.available && out.comparison.named_comparison_ready && out.comparison.actor_rite &&
        out.comparison.target_rite && out.comparison.requested_target_rite_id == Fixture::target_id &&
        out.comparison.tenet_key == "tenet_1" && out.comparison.same_rite == false &&
        out.comparison.same_faith == true &&
        out.comparison.actor_rite->named_tenet_status == std::uint8_t{1} &&
        out.comparison.target_rite->named_tenet_status == std::uint8_t{3} &&
        !out.comparison.actor_rite->named_tenet_core_member && !out.comparison.target_rite->named_tenet_core_member &&
        out.comparison.capture_epoch == out.catalogue.capture_epoch,
        "simultaneous target/named sibling independently retains native status and owner");

    f.SetLoaded({}); f.SetExtra({});
    out = Query(f, adapter, output, "observed-empty-registry.json", request);
    Available(f, out, {}, {}, {}, false);

    f.SetLoaded({0, 1, 2}); f.SetExtra({1}); f.SetProphet(false, false);
    out = Query(f, adapter, output, "missing-prophet-definition.json", request);
    const auto &failed = out.catalogue;
    Assert(!failed.available && failed.failure == knowledge::Failure::prophet_definition_unavailable &&
        !failed.has_character_extension && !failed.extra_collection_source && !failed.extra_tenet_keys &&
        !failed.loaded_definition_count && !failed.native_has_prophet && !failed.rows &&
        !failed.extra_collection_complete && !failed.loaded_registry_complete && !failed.knowledge_inputs_complete,
        "missing fixed Prophet is typed unavailable with dependent nulls");
    Assert(out.old.available && out.old.personal_tenets.size() == 1 &&
        f.extra_calls == 1 && f.perks_calls == 0 && f.contains_extra_calls == 0 && f.contains_perks_calls == 0,
        "new failure preserves old query and avoids invented Prophet membership");

    // Keep the new fixed pointer missing: unrequested paths must still use
    // only the old reader. Explicit false creates no eighth business wire.
    (void)Query(f, adapter, output, "old-unrequested-result.json", "{}");
    (void)Query(f, adapter, output, nullptr, "{\"include_knowledge_catalogue\":false}");
    std::cout << "PASS cases=7 checks=" << checks
        << " actual_domain_mailbox=true actual_knowledge_reader=true actual_full_wire=true actual_renderer=true"
        << " synthetic_memory=true synthetic_callbacks=true legacy_main_executed=false live=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
