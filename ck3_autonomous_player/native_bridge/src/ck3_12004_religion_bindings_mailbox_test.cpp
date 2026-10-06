// FIRST_NOTRUN: seven new whole .4 command_result packets. Only owned
// synthetic memory/native callbacks are used. The production .4 adapter,
// selected core reader, topic mailboxes, DTO serializers and renderer run.
// No old fixture main, production stub, macro replacement or game process.
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_religion_bindings.hpp"
#include "xar_bridge/ck3_12004_religion_profile.hpp"
#include "xar_bridge/religion_doctrine12002_mailbox.hpp"
#include "xar_bridge/religion_doctrine12002_choices_mailbox.hpp"
#include "xar_bridge/religion_doctrine12002_tenet_rows_mailbox.hpp"
#include "xar_bridge/religion_reform12002_query_mailbox.hpp"

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
#include <vector>

namespace {
namespace old = xar::ck3_12002;
namespace actual = xar::ck3_12004;
namespace bindings4 = actual::religion;
namespace profile = bindings4::profile;
namespace religion = old::religion;
namespace doctrine = religion::doctrine12002;
namespace reform = old::religion_reform;
namespace api = xar::ck3_11906;
namespace game = xar::game;
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
template <class Buffer> void Key(Buffer &buffer, std::size_t offset, std::string_view value) {
  Assert(value.size() < 16U, "synthetic key fits the native inline CString");
  std::memcpy(buffer.data() + offset, value.data(), value.size());
  Put(buffer, offset + 0x10, static_cast<std::uint64_t>(value.size()));
  Put(buffer, offset + 0x18, std::uint64_t{15});
}
template <class Buffer, class Pointer, std::size_t N>
void Collection(Buffer &buffer, std::size_t offset, std::array<Pointer, N> &rows) {
  Put(buffer, offset, rows.data());
  Put(buffer, offset + 8, static_cast<std::int32_t>(N));
  Put(buffer, offset + 0xC, static_cast<std::int32_t>(N));
}

struct Fixture {
  static constexpr std::uintptr_t image_base = 0x140000000;
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::int32_t date = 53175816;
  static constexpr std::uint32_t rite_id = 0x82000002;
  static constexpr std::uint32_t main_id = 0x83000002;
  static constexpr std::uint32_t faith_id = 0x84000001;
  static constexpr std::uint32_t religion_id = 0x85000001;
  static constexpr std::uint32_t target_id = 0x86000003;
  const DWORD owner = GetCurrentThreadId();
  Bytes<0xA8> state{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> character_storage{}, rite_storage{};
  Bytes<0x80> character_slots{}, rite_slots{};
  Bytes<0x1D8> character{};
  Bytes<0x100> extension{};
  Bytes<0x230> perk_extension{};
  Bytes<0x8D0> rite{}, main_rite{}, target_rite{};
  Bytes<0x100> faith{};
  Bytes<0x28> native_religion{};
  Bytes<0x40> religion_definition{};
  Bytes<0xB20> doctrine_a{}, doctrine_b{}, doctrine_c{};
  Bytes<0x40> group_a{}, group_b{};
  Bytes<0x70> doctrine_database{};
  Bytes<0x40> tenet_a{}, tenet_b{}, tenet_c{}, prophet{};
  Bytes<0xF00> tenet_database{}, perk_database{};
  Bytes<0x28> token_a{}, token_b{}, token_c{};
  Bytes<0x90> idler{};
  Bytes<0x280> handler{};
  Bytes<0xD0> window{};
  Bytes<0x30> current_states{};
  Bytes<0x10> target_states{};
  std::array<const void *, 2> current_doctrines{doctrine_a.data(), doctrine_b.data()};
  std::array<const void *, 1> main_doctrines{doctrine_c.data()};
  std::array<const void *, 3> learned{doctrine_b.data(), doctrine_a.data(), doctrine_b.data()};
  std::array<const void *, 3> doctrine_registry{doctrine_a.data(), doctrine_b.data(), doctrine_c.data()};
  std::array<std::int32_t, 3> current_tokens{11, 22, 11};
  std::array<std::int32_t, 1> main_tokens{33};
  std::array<const void *, 1> current_core{tenet_a.data()};
  std::array<const void *, 2> main_core{tenet_b.data(), tenet_c.data()};
  std::array<const void *, 2> target_core{tenet_b.data(), tenet_b.data()};
  std::array<const void *, 1> personal{tenet_c.data()};
  std::array<const void *, 2> extra{tenet_b.data(), tenet_b.data()};
  std::array<const void *, 3> tenet_registry{tenet_b.data(), tenet_a.data(), tenet_b.data()};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *character_storage_ptr = character_storage.data(), *rite_storage_ptr = rite_storage.data();
  void *doctrine_database_ptr = doctrine_database.data();
  void *tenet_database_ptr = tenet_database.data(), *perk_database_ptr = perk_database.data();
  unsigned core_calls{}, knows_calls{}, extra_calls{}, perks_calls{}, contains_calls{}, target_status_calls{};
  bool callback_scope_valid = true;

  Fixture() {
    Put(state, actual::kGameStateDateOffset, date);
    Put(state, actual::kGameStateSpeedOffset, std::int32_t{2});
    Put(state, actual::kGameStateDataOffset, data.data());
    Put(jomini, actual::kJominiPlayersOffset, players.data());
    jomini[actual::kJominiPausedOffset] = std::byte{1};
    Put(players, actual::kPlayersLocalPlayerIdOffset, std::int32_t{7});
    Put(player, actual::kPlayerIdOffset, std::int32_t{7});
    Put(data, actual::kPlayerCharacterManagerOffset + actual::kPlayerManagerEntriesOffset, entries.data());
    Put(data, actual::kPlayerCharacterManagerOffset + actual::kPlayerManagerCountOffset, std::int32_t{1});
    Put(entry, actual::kPlayerEntryLocalPlayerIdOffset, std::int32_t{7});
    Put(entry, actual::kPlayerEntryCharacterIdOffset, actor_id);
    Put(character_storage, 0x20, character_slots.data());
    Put(character_storage, 0x2C, std::int32_t{8});
    Put(character_slots, 4 * 0x10 + 8, character.data());
    Put(character, actual::kCharacterFullIdOffset, actor_id);
    Put(character, 0xB4, rite_id);
    Put(character, 0x1C8, extension.data());
    Put(character, 0x1B0, perk_extension.data());
    Put(rite, 8, rite_id); Put(main_rite, 8, main_id); Put(target_rite, 8, target_id);
    for (auto *object : {&rite, &main_rite, &target_rite}) {
      Put(*object, 0xC, std::uint32_t{0x52697465});
      Put(*object, 0x4B8, faith_id);
      Put(*object, 0x4BC, std::uint32_t{0xFFFFFFFF});
      Put(*object, 0x4C0, std::uint32_t{0xFFFFFFFF});
    }
    main_rite[0x8B0] = std::byte{1};
    Put(faith, 8, faith_id); Put(faith, 0x8C, religion_id); Put(faith, 0x98, main_id);
    Key(faith, 0xE0, "faith_a");
    Put(native_religion, 8, religion_id); Put(native_religion, 0x20, religion_definition.data());
    Key(religion_definition, 0x18, "religion_a");
    Key(group_a, 0x18, "group_a"); Key(group_b, 0x18, "group_b");
    Key(doctrine_a, 0x18, "doctrine_a"); Key(doctrine_b, 0x18, "doctrine_b");
    Key(doctrine_c, 0x18, "doctrine_c");
    Put(doctrine_a, 0xB08, group_a.data()); Put(doctrine_b, 0xB08, group_a.data());
    Put(doctrine_c, 0xB08, group_b.data());
    Collection(rite, 0x7A0, current_doctrines); Collection(main_rite, 0x7A0, main_doctrines);
    Collection(extension, 0xE0, learned); Collection(doctrine_database, 0x50, doctrine_registry);
    Collection(rite, 0x7B8, current_tokens); Collection(main_rite, 0x7B8, main_tokens);
    Key(token_a, 0, "parameter_a"); Key(token_b, 0, "parameter_b"); Key(token_c, 0, "parameter_c");
    Key(tenet_a, 0x18, "tenet_a"); Key(tenet_b, 0x18, "tenet_b"); Key(tenet_c, 0x18, "tenet_c");
    for (auto *definition : {&tenet_a, &tenet_b, &tenet_c})
      Put(*definition, 0x38, std::uint32_t{0x4744624F});
    Collection(rite, 0x758, current_core); Collection(main_rite, 0x758, main_core);
    Collection(target_rite, 0x758, target_core); Collection(extension, 0x88, personal);
    Collection(extension, 0xC8, extra); Collection(tenet_database, 0xEF0, tenet_registry);
    Put(perk_database, 0xEF0, prophet.data());
    const std::array<const void *, 3> state_definitions{tenet_a.data(), tenet_b.data(), tenet_c.data()};
    for (std::size_t index = 0; index < state_definitions.size(); ++index) {
      Put(current_states, index * 0x10, state_definitions[index]);
      Put(current_states, index * 0x10 + 8, static_cast<std::uint8_t>(index));
    }
    Put(rite, 0x788, current_states.data()); Put(rite, 0x794, std::int32_t{3});
    Put(target_states, 0, tenet_b.data()); Put(target_states, 8, std::uint8_t{3});
    Put(target_rite, 0x788, target_states.data()); Put(target_rite, 0x794, std::int32_t{1});
    Put(rite_storage, 0x20, rite_slots.data()); Put(rite_storage, 0x2C, std::uint32_t{8});
    Put(rite_slots, 3 * 0x10 + 8, target_rite.data());
    Put(jomini, 0x10, idler.data());
    Put(idler, 0, image_base + profile::kDraftIdlerVtableRva); Put(idler, 0x88, handler.data());
    Put(handler, 0, image_base + profile::kDraftHandlerVtableRva);
    Put(window, 0, image_base + profile::kDraftWindowPrimaryVtableRva);
    Put(window, 0x10, image_base + profile::kDraftWindowSecondaryVtableRva);
    Put(window, 0xA0, handler.data()); Put(window, 0xC8, rite_id);
    Put(window, 0xCC, static_cast<std::uint32_t>(actor_id));
    SetWindow(false);
  }
  void SetWindow(bool present) { Put(handler, 0x278, present ? window.data() : nullptr); }
  void ResetCounters() {
    core_calls = knows_calls = extra_calls = perks_calls = contains_calls = target_status_calls = 0;
    callback_scope_valid = true;
  }
};
Fixture *fixture_state = nullptr;
bool Owner() { return GetCurrentThreadId() == fixture_state->owner; }
void *Player(void *owner) {
  auto &memory = *fixture_state;
  ++memory.core_calls;
  memory.callback_scope_valid &= Owner() && owner == memory.jomini.data();
  return memory.player.data();
}
void *CharacterRite(void *actor) {
  auto &memory = *fixture_state;
  memory.callback_scope_valid &= Owner() && actor == memory.character.data();
  return memory.rite.data();
}
void *CharacterFaith(void *actor) {
  auto &memory = *fixture_state;
  memory.callback_scope_valid &= Owner() && actor == memory.character.data();
  return memory.faith.data();
}
void *RiteFaith(void *rite) {
  auto &memory = *fixture_state;
  memory.callback_scope_valid &= Owner() &&
      (rite == memory.rite.data() || rite == memory.main_rite.data() || rite == memory.target_rite.data());
  return memory.faith.data();
}
void *FaithReligion(void *faith) {
  auto &memory = *fixture_state;
  memory.callback_scope_valid &= Owner() && faith == memory.faith.data();
  return memory.native_religion.data();
}
void *FaithMainRite(void *faith) {
  auto &memory = *fixture_state;
  memory.callback_scope_valid &= Owner() && faith == memory.faith.data();
  return memory.main_rite.data();
}
const void *FaithKey(void *faith) {
  fixture_state->callback_scope_valid &= Owner() && faith == fixture_state->faith.data();
  return static_cast<const std::byte *>(faith) + 0xE0;
}
std::int64_t *Fervor(void *faith, std::int64_t *out) {
  fixture_state->callback_scope_valid &= Owner() && faith == fixture_state->faith.data();
  *out = 6'250'000; return out;
}
std::int64_t *Fulfillment(void *actor, std::int64_t *out) {
  fixture_state->callback_scope_valid &= Owner() && actor == fixture_state->character.data();
  *out = 125'000; return out;
}
bool IsMain(void *rite) { return rite == fixture_state->main_rite.data(); }
std::int64_t *Divergence(std::int64_t *out, void *rite, void *tooltip) {
  fixture_state->callback_scope_valid &= Owner() && rite == fixture_state->rite.data() && tooltip == nullptr;
  *out = 15'000'000; return out;
}
std::int64_t *Heresy(void *faith, std::int64_t *out) {
  fixture_state->callback_scope_valid &= Owner() && faith == fixture_state->faith.data();
  *out = 20'000'000; return out;
}
bool IsUnreformed(void *faith) {
  return FaithMainRite(faith) == fixture_state->main_rite.data() &&
      Load<std::uint8_t>(fixture_state->main_rite.data(), 0x8B0) != std::uint8_t{0};
}
bool Visible(const void *window) {
  fixture_state->callback_scope_valid &= Owner() && window == fixture_state->window.data();
  return true;
}
bool BooleanMember(const void *collection, const std::int32_t *token) {
  auto &memory = *fixture_state;
  memory.callback_scope_valid &= Owner() && token != nullptr &&
      (collection == memory.rite.data() + 0x7B8 || collection == memory.main_rite.data() + 0x7B8);
  const auto *rows = Load<const std::int32_t *>(collection, 0);
  const auto count = Load<std::int32_t>(collection, 0xC);
  for (std::int32_t index = 0; index < count; ++index) if (rows[index] == *token) return true;
  return false;
}
const void *ParameterKey(std::int32_t token) {
  auto &memory = *fixture_state;
  memory.callback_scope_valid &= Owner() && (token == 11 || token == 22 || token == 33);
  return token == 11 ? memory.token_a.data() : (token == 22 ? memory.token_b.data() : memory.token_c.data());
}
bool NativeKnown(void *actor, const void *definition) {
  auto &memory = *fixture_state;
  ++memory.knows_calls;
  memory.callback_scope_valid &= Owner() && actor == memory.character.data() &&
      (definition == memory.doctrine_a.data() || definition == memory.doctrine_b.data() || definition == memory.doctrine_c.data());
  const auto *rows = Load<const void *const *>(memory.extension.data(), 0xE0);
  const auto count = Load<std::int32_t>(memory.extension.data(), 0xEC);
  for (std::int32_t index = 0; index < count; ++index) if (rows[index] == definition) return true;
  return false;
}
std::uint8_t NativeStatus(void *rite, const void *definition) {
  auto &memory = *fixture_state;
  memory.callback_scope_valid &= Owner() && (rite == memory.rite.data() || rite == memory.target_rite.data()) &&
      (definition == memory.tenet_a.data() || definition == memory.tenet_b.data() || definition == memory.tenet_c.data());
  if (rite == memory.target_rite.data()) ++memory.target_status_calls;
  const auto *rows = Load<const std::byte *>(rite, 0x788);
  const auto count = Load<std::int32_t>(rite, 0x794);
  for (std::int32_t index = 0; index < count; ++index)
    if (Load<const void *>(rows, static_cast<std::size_t>(index) * 0x10) == definition)
      return Load<std::uint8_t>(rows, static_cast<std::size_t>(index) * 0x10 + 8);
  return 0;
}
const void *Extra(void *actor) {
  ++fixture_state->extra_calls;
  fixture_state->callback_scope_valid &= Owner() && actor == fixture_state->character.data();
  return fixture_state->extension.data() + 0xC8;
}
const void *Perks(void *actor) {
  ++fixture_state->perks_calls;
  fixture_state->callback_scope_valid &= Owner() && actor == fixture_state->character.data();
  return fixture_state->perk_extension.data() + 0x220;
}
bool DefinitionMember(const void *collection, const void *definition_slot) {
  auto &memory = *fixture_state;
  ++memory.contains_calls;
  memory.callback_scope_valid &= Owner() &&
      (collection == memory.extension.data() + 0xC8 || collection == memory.perk_extension.data() + 0x220);
  const auto definition = Load<const void *>(definition_slot, 0);
  const auto *rows = Load<const void *const *>(collection, 0);
  const auto count = Load<std::int32_t>(collection, 0xC);
  for (std::int32_t index = 0; index < count; ++index) if (rows[index] == definition) return true;
  return false;
}
actual::CoreBindings Core(Fixture &memory) {
  return {true, &memory.state_ptr, &memory.jomini_ptr, &memory.character_storage_ptr, &Player};
}
bindings4::ContextBindings Context(Fixture &memory) {
  auto value = bindings4::BindReligionContextImage12004(Fixture::image_base, actual::kExecutableSha256);
  value.core = Core(memory);
  value.character_rite = &CharacterRite; value.character_faith = &CharacterFaith;
  value.rite_faith = &RiteFaith; value.faith_religion = &FaithReligion;
  value.faith_main_rite = &FaithMainRite; value.faith_fervor = &Fervor;
  value.character_spiritual_fulfillment = &Fulfillment; value.faith_tag = &FaithKey;
  // religion_tag remains the actual profile's manual proved +20/+18 copier.
  return value;
}
bindings4::ReformQueryBindings Reform(Fixture &memory) {
  auto value = bindings4::BindReformQueryImage12004(Fixture::image_base, actual::kExecutableSha256);
  value.core = Core(memory); value.context = Context(memory);
  value.rite_model.core = value.core; value.rite_model.character_rite = &CharacterRite;
  value.rite_model.rite_faith = &RiteFaith; value.rite_model.faith_main_rite = &FaithMainRite;
  value.rite_model.rite_is_main = &IsMain; value.rite_model.divergence_to_main = &Divergence;
  value.rite_model.faith_heresy_threshold = &Heresy;
  value.main_rite.main_rite = &FaithMainRite; value.main_rite.is_unreformed = &IsUnreformed;
  value.window.core = value.core; value.window.is_visible = &Visible;
  return value;
}
bindings4::CurrentDoctrineBindings Current(Fixture &memory) {
  auto value = bindings4::BindCurrentDoctrineImage12004(Fixture::image_base, actual::kExecutableSha256);
  value.context = Context(memory);
  value.parameters.contains_boolean_parameter = &BooleanMember;
  value.parameters.parameter_key = &ParameterKey;
  return value;
}
bindings4::DoctrineKnowledgeBindings Knowledge(Fixture &memory) {
  auto value = bindings4::BindDoctrineKnowledgeImage12004(Fixture::image_base, actual::kExecutableSha256);
  value.context = Context(memory); value.knows_doctrine = &NativeKnown;
  value.definition_database_global = &memory.doctrine_database_ptr;
  return value;
}
bindings4::PlayerTenetBindings Tenets(Fixture &memory) {
  auto value = bindings4::BindPlayerTenetImage12004(Fixture::image_base, actual::kExecutableSha256);
  value.context = Context(memory); value.rows.tenet_state = &NativeStatus;
  value.comparison.context = value.context; value.comparison.tenet_state = &NativeStatus;
  value.comparison.rite_storage_global = &memory.rite_storage_ptr;
  value.comparison.tenet_database_global = &memory.tenet_database_ptr;
  value.knowledge.context = value.context; value.knowledge.tenet_database_global = &memory.tenet_database_ptr;
  value.knowledge.perk_database_global = &memory.perk_database_ptr;
  value.knowledge.actor_extra_collection = &Extra; value.knowledge.actor_perks_collection = &Perks;
  value.knowledge.contains = &DefinitionMember;
  return value;
}

void *tls_context = nullptr;
void *__fastcall FixtureTls() noexcept { return tls_context; }
struct Pump {
  Bytes<0x28> tls{};
  std::uint8_t initialized = 1;
  std::uintptr_t unused_rng{};
  Pump(Fixture &memory, api::MainThreadQueryMailboxV1 &mailbox) {
    tls[0x20] = std::byte{1}; tls_context = tls.data();
    mailbox.global_rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&unused_rng);
    mailbox.jomini_state_slot = reinterpret_cast<std::uintptr_t>(&memory.jomini_ptr);
    mailbox.game_state_slot = reinterpret_cast<std::uintptr_t>(&memory.state_ptr);
    mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter = &FixtureTls;
    mailbox.executor_submission_enabled = true;
    mailbox.permitted_executor_religion_reform12002 = &old::ExecutePlayerReligionReformMailbox12002;
    mailbox.permitted_executor_religion_doctrines12002 = &old::ExecutePlayerReligionDoctrinesMailbox12002;
    mailbox.permitted_executor_religion_doctrine_knowledge12002 = &old::ExecutePlayerReligionDoctrineKnowledgeMailbox12002;
    mailbox.permitted_executor_religion_tenets12002 = &old::ExecutePlayerReligionTenetsMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned index = 0; index < 2; ++index)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};

template <class Query, class Run>
std::string WholeWire(Fixture &memory, const game::GameAdapter &adapter,
    const game::Snapshot &frame, Query &query, Run run,
    const std::filesystem::path &directory, const char *filename,
    std::string_view selected_schema) {
  memory.ResetCounters();
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(memory, mailbox);
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = frame;
  query.envelope.expected_snapshot_revision = 701;
  query.envelope.snapshot_comparison = old::QuerySnapshotComparison12002::core_frame;
  std::atomic<bool> done{false};
  bool complete = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    complete = run(query, "religion-12004-synthetic-fixture", serialized, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Assert(complete && drained && failure.empty() && query.completed && query.envelope.frame_stable,
      "production named owner mailbox completes on actual .4 selected core frame");
  Assert(mailbox.state == api::MainThreadQueryMailboxStateV1::idle,
      "production owner mailbox is terminal and reclaimed");
  Assert(memory.callback_scope_valid && memory.core_calls > 0U,
      "synthetic native callbacks execute only on actual owner and consume actual pointers");
  const auto epoch = query.envelope.execution_stamp.pump_epoch;
  Assert(epoch > 0 && epoch != std::uint64_t{701}, "actual pump epoch is independent of published revision");
  auto rendered = game::Render12004BuildIdentity(std::move(serialized), adapter.descriptor());
  Assert(rendered.find("\"type\":\"command_result\"") != std::string::npos &&
      rendered.find("\"snapshot_revision\":701") != std::string::npos &&
      rendered.find("\"game_version\":\"1.20.0.4\"") != std::string::npos &&
      rendered.find(actual::kExecutableSha256) != std::string::npos &&
      rendered.find(selected_schema) != std::string::npos,
      "actual .4 production renderer supplies complete whole-command build identity");
  std::ofstream output(directory / filename, std::ios::binary);
  output << rendered << '\n';
  Assert(static_cast<bool>(output), "complete native business wire is written without body reconstruction");
  return rendered;
}

void BinderCases() {
  const auto base = Fixture::image_base;
  const auto basic = bindings4::BindReformQueryImage12004(base, actual::kExecutableSha256);
  Assert(basic.enabled && basic.core.enabled && basic.context.enabled && basic.rite_model.enabled &&
      basic.main_rite.enabled && basic.window.enabled && !basic.costs.enabled &&
      !basic.eligibility.enabled && !basic.choices.enabled && !basic.creation_terms.enabled,
      "exact actual .4 basic factory enables only the closed families");
  Assert(reinterpret_cast<std::uintptr_t>(basic.core.get_local_player) == base + actual::kGetLocalPlayerRva &&
      reinterpret_cast<std::uintptr_t>(basic.context.character_rite) == base + profile::kCharacterRiteRva &&
      reinterpret_cast<std::uintptr_t>(basic.context.character_faith) == base + profile::kCharacterFaithRva &&
      basic.window.window_vtable == base + profile::kDraftWindowPrimaryVtableRva,
      "actual .4 core, actor and window addresses come from independently closed profile");
  const auto knowledge = bindings4::BindDoctrineKnowledgeImage12004(base, actual::kExecutableSha256);
  Assert(reinterpret_cast<std::uintptr_t>(knowledge.knows_doctrine) == base + profile::kCharacterKnowsDoctrineRva &&
      reinterpret_cast<std::uintptr_t>(knowledge.definition_database_global) == base + profile::kDoctrineDatabaseSlotRva,
      "Doctrine factory selects actual .4 native knowledge callback and loaded registry");
  const auto tenets = bindings4::BindPlayerTenetImage12004(base, actual::kExecutableSha256);
  Assert(tenets.rows.enabled && reinterpret_cast<std::uintptr_t>(tenets.rows.tenet_state) == base + profile::kNativeTenetStateRva &&
      reinterpret_cast<std::uintptr_t>(tenets.knowledge.actor_extra_collection) == base + profile::kCharacterExtraTenetsRva &&
      reinterpret_cast<std::uintptr_t>(tenets.knowledge.actor_perks_collection) == base + profile::kCharacterActualPerksRva &&
      reinterpret_cast<std::uintptr_t>(tenets.comparison.tenet_database_global) == base + profile::kTenetDatabaseSlotRva,
      "Tenet factory preserves actual4 current, target and knowledge ABI sources");
  Assert(!bindings4::BindReformQueryImage12004(base, old::kExecutableSha256).enabled &&
      !bindings4::BindDoctrineKnowledgeImage12004(0, actual::kExecutableSha256).context.enabled &&
      !bindings4::BindPlayerTenetImage12004(base, "unreviewed").context.enabled,
      "actual .4 factories preserve exact own-build admission without invoking legacy factories");
}
template <class Observation, class Query>
void OwnerFields(const Observation &value, const Query &query) {
  Assert(value.available && value.capture_epoch == query.envelope.execution_stamp.pump_epoch &&
      value.date_raw == Fixture::date &&
      static_cast<std::uint32_t>(value.played_character_id) == static_cast<std::uint32_t>(Fixture::actor_id),
      "actual owner metadata binds the complete domain observation to the admitted frame");
}
void TenetRows(const doctrine::TenetRowsContext &value) {
  Assert(value.current_rite && value.faith_main_rite && value.current_rite->rite_id == Fixture::rite_id &&
      value.faith_main_rite->rite_id == Fixture::main_id && value.personal_tenets.size() == std::size_t{1} &&
      value.personal_tenets[0].key == "tenet_c" &&
      value.effective_tenet_states.size() == std::size_t{3}, "actual current/main/personal scopes remain independently observed");
  const std::array<std::string_view, 3> keys{"tenet_a", "tenet_b", "tenet_c"};
  for (std::size_t index = 0; index < keys.size(); ++index)
    Assert(value.effective_tenet_states[index].key == keys[index] &&
        value.effective_tenet_states[index].current_rite_status == static_cast<std::uint8_t>(index),
        "native Tenet state0 is a legal observed value and remains separate from membership");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Assert(argc == 2, "one output directory argument");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    BinderCases();
    Fixture memory;
    fixture_state = &memory;
    game::Ck3_12004AdapterBindings adapter_bindings{};
    adapter_bindings.core = Core(memory);
    auto adapter = game::CreateCk3_12004AdapterFromBindings(std::move(adapter_bindings));
    Assert(adapter && adapter->enabled() && game::IsCk3_12004Descriptor(adapter->descriptor()),
        "fixture uses the actual production .4 adapter factory");
    game::Snapshot frame{};
    Assert(game::ReadCk3_12002TimelineCoreSnapshot(*adapter, frame) && frame.paused && frame.map_ready &&
        frame.has_played_character && frame.played_character_alive &&
        frame.played_character_id == Fixture::actor_id && frame.date_raw == Fixture::date,
        "actual4 selected core callback creates only the supported owner frame");
    game::Snapshot full_snapshot{};
    Assert(!adapter->read_snapshot(full_snapshot), "unsupported full gameplay snapshot remains unavailable");
    constexpr std::string_view request = "{\"expected_snapshot_revision\":701}";
    for (const bool present : {false, true}) {
      memory.SetWindow(present);
      old::PlayerReligionReformMailboxContext12002 query{};
      std::uint64_t revision{};
      Assert(old::ParsePlayerReligionReformRevision12002(request, revision) && revision == std::uint64_t{701},
          "production basic reform parser retains requested native revision");
      query.bindings = Reform(memory);
      const auto wire = WholeWire(memory, *adapter, frame, query, &old::RunPlayerReligionReformMailbox12002,
          directory, present ? "basic-reform-visible-window.json" : "basic-reform-absent-window.json",
          "ck3_12004_player_religion_reform_query_v1");
      OwnerFields(query.observation, query);
      const auto &value = query.observation;
      Assert(value.context.available && value.rite_model.available &&
          value.main_rite.status == reform::MainRiteStatus::observed && value.current_window.available &&
          value.current_window.present == present && value.current_window.visible == present &&
          (value.current_window.window != nullptr) == present &&
          value.current_window.failure == reform::DraftWindowFailure::none,
          "absent and visible actual windows are independent valid current observations");
      Assert(!value.draft_costs.available && !value.draft_eligibility.available &&
          !value.popup_choices.available && !value.current_doctrine_selection.available &&
          !value.publish_creation_terms && wire.find("current_draft_creation_terms") == std::string::npos,
          "unmapped draft components retain typed unavailable output and no creation-terms publication");
    }

    old::PlayerReligionDoctrinesMailboxContext12002 current{};
    std::uint64_t revision{};
    Assert(old::ParsePlayerReligionDoctrinesRevision12002(request, revision) && revision == std::uint64_t{701},
        "production current Doctrine request parser is used");
    current.bindings = Current(memory);
    WholeWire(memory, *adapter, frame, current, &old::RunPlayerReligionDoctrinesMailbox12002,
        directory, "current-doctrines.json", "ck3_12004_current_doctrines_v1");
    OwnerFields(current.observation, current);
    Assert(current.observation.current_rite.rows.size() == std::size_t{2} &&
        current.observation.faith_main_rite.rows.size() == std::size_t{1} &&
        current.observation.boolean_parameters.current_rite &&
        current.observation.boolean_parameters.current_rite->parameters.size() == std::size_t{3} &&
        current.observation.boolean_parameters.faith_main_rite &&
        current.observation.boolean_parameters.faith_main_rite->parameters.size() == std::size_t{1},
        "actual current/main Doctrine and duplicate Boolean token scopes survive the production composite");

    old::PlayerReligionDoctrineKnowledgeMailboxContext12002 learned{};
    Assert(old::ParsePlayerReligionDoctrineKnowledgeRequest12002(request, revision, learned.doctrine_key) &&
        revision == std::uint64_t{701} && !learned.doctrine_key, "production learned mode parser is used");
    learned.bindings = Knowledge(memory);
    WholeWire(memory, *adapter, frame, learned, &old::RunPlayerReligionDoctrineKnowledgeMailbox12002,
        directory, "learned-e0-order-duplicates.json", "ck3_12004_played_doctrine_knowledge_v1");
    OwnerFields(learned.learned_observation, learned);
    const std::array<std::string_view, 3> learned_keys{"doctrine_b", "doctrine_a", "doctrine_b"};
    Assert(learned.learned_observation.learned_rows.size() == learned_keys.size() && memory.knows_calls == 6U,
        "actual learned E0 collection receives two native samples per occurrence");
    for (std::size_t index = 0; index < learned_keys.size(); ++index)
      Assert(learned.learned_observation.learned_rows[index].definition.doctrine_key == learned_keys[index] &&
          learned.learned_observation.learned_rows[index].native_knows_doctrine,
          "actual E0 order and duplicate native true remain preserved");

    old::PlayerReligionDoctrineKnowledgeMailboxContext12002 lookup{};
    Assert(old::ParsePlayerReligionDoctrineKnowledgeRequest12002(
        "{\"expected_snapshot_revision\":701,\"doctrine_key\":\"doctrine_c\"}", revision, lookup.doctrine_key) &&
        lookup.doctrine_key == std::optional<std::string>{"doctrine_c"}, "production named Doctrine lookup parser is used");
    lookup.bindings = Knowledge(memory);
    WholeWire(memory, *adapter, frame, lookup, &old::RunPlayerReligionDoctrineKnowledgeMailbox12002,
        directory, "lookup-native-false.json", "ck3_12004_played_doctrine_knowledge_lookup_v1");
    OwnerFields(lookup.lookup_observation, lookup);
    Assert(lookup.lookup_observation.definition && lookup.lookup_observation.native_knows_doctrine == false &&
        lookup.lookup_observation.definition->doctrine_key == "doctrine_c" && memory.knows_calls == 2U,
        "actual loaded definition preserves native known false as an observed value");

    for (const bool extras : {true, false}) {
      old::PlayerReligionTenetsMailboxContext12002 query{};
      const auto payload = extras
          ? "{\"expected_snapshot_revision\":701,\"target_rite_id\":2248146947,\"tenet_key\":\"tenet_b\",\"include_knowledge_catalogue\":true}"
          : "{\"expected_snapshot_revision\":701}";
      Assert(old::ParsePlayerReligionTenetsRevision12002(payload, revision) &&
          old::ParsePlayerReligionTenetsComparisonRequest12003(payload, query.target_rite_id, query.tenet_key) &&
          old::ParsePlayerReligionTenetsKnowledgeRequest12003(payload, query.include_knowledge_catalogue) &&
          revision == std::uint64_t{701} && query.include_knowledge_catalogue == extras,
          "production request parses optional target and knowledge only when requested");
      auto value = Tenets(memory);
      query.bindings = value.context; query.tenet_bindings = value.rows;
      query.comparison_bindings = value.comparison; query.knowledge_bindings = value.knowledge;
      const auto wire = WholeWire(memory, *adapter, frame, query, &old::RunPlayerReligionTenetsMailbox12002,
          directory, extras ? "tenets-target-knowledge.json" : "tenets-current-only.json", "ck3_12004_tenet_rows_v1");
      OwnerFields(query.observation, query); TenetRows(query.observation);
      if (extras) {
        OwnerFields(query.comparison, query); OwnerFields(query.knowledge_catalogue, query);
        Assert(query.target_rite_id == Fixture::target_id && query.comparison.actor_rite && query.comparison.target_rite &&
            query.comparison.actor_rite->named_tenet_status == std::uint8_t{1} &&
            query.comparison.target_rite->named_tenet_status == std::uint8_t{3} &&
            !query.comparison.actor_rite->named_tenet_core_member && query.comparison.target_rite->named_tenet_core_member &&
            query.comparison.target_rite->core_tenet_keys == std::vector<std::string>{"tenet_b", "tenet_b"} &&
            memory.target_status_calls == 2U, "four actual Core collections and named native statuses remain independent");
        const auto &catalogue = query.knowledge_catalogue;
        Assert(catalogue.native_has_prophet == false && catalogue.extra_tenet_keys &&
            *catalogue.extra_tenet_keys == std::vector<std::string>{"tenet_b", "tenet_b"} && catalogue.rows &&
            catalogue.rows->size() == std::size_t{3} &&
            (*catalogue.rows)[0].knowledge && !(*catalogue.rows)[1].knowledge && (*catalogue.rows)[2].knowledge &&
            memory.extra_calls == 2U && memory.perks_calls == 2U && memory.contains_calls == 8U,
            "actual C8/native Prophet inputs preserve registry order, duplicates and independent Boolean knowledge");
      } else {
        Assert(!query.target_rite_id && memory.extra_calls == 0U && memory.perks_calls == 0U &&
            memory.contains_calls == 0U && memory.target_status_calls == 0U &&
            wire.find("target_rite_tenet_comparison") == std::string::npos &&
            wire.find("player_tenet_knowledge_catalogue") == std::string::npos,
            "new actual4 current-only request keeps the original DTO shape and skips optional native callbacks");
      }
    }
    std::cout << "PASS cases=7 checks=" << checks
        << " actual_adapter=true actual_core_reader=true actual_named_mailbox=true actual_serializer=true"
        << " actual_renderer=true actual_full_wire=true synthetic_memory=true synthetic_callbacks=true"
        << " legacy_main_executed=false production_stubs=false live=false\n";
    fixture_state = nullptr;
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
