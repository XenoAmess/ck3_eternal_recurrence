// FIRST_NOTRUN: three new whole .4 command_result packets. Only owned
// synthetic memory/native callbacks are used. The production .4 adapter,
// selected core reader, topic mailboxes, DTO serializers and renderer run.
// Shared synthetic memory/owner helpers are copied as source; no old cases/main are included or run.
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_religion_bindings.hpp"
#include "xar_bridge/ck3_12004_religion_draft_bindings.hpp"
#include "xar_bridge/religion_reform12002_fullchoices_mailbox.hpp"
#include "xar_bridge/religion_reform12002_group_mailbox.hpp"
#include "xar_bridge/religion_reform12002_tenet_sources_mailbox.hpp"
#include "xar_bridge/ck3_12004_religion_profile.hpp"

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
  static constexpr std::uint32_t main_id = 0x83000003;
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
  Bytes<0x160> group_a{}, group_b{};
  Bytes<0x70> doctrine_database{};
  Bytes<0x680> tenet_a{}, tenet_b{}, tenet_c{}, prophet{};
  Bytes<0xF00> tenet_database{}, perk_database{};
  Bytes<0x28> token_a{}, token_b{}, token_c{};
  Bytes<0x90> idler{};
  Bytes<0x280> handler{};
  Bytes<0xBA0> window{};
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
bool Visible(const void *window) {
  fixture_state->callback_scope_valid &= Owner() && window == fixture_state->window.data();
  return true;
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
    mailbox.permitted_executor_religion_draft_doctrine_choices12002 = &old::ExecutePlayerReligionDraftDoctrineChoicesMailbox12002;
    mailbox.permitted_executor_religion_draft_groups12002 = &old::ExecutePlayerReligionDraftGroupsMailbox12002;
    mailbox.permitted_executor_religion_draft_tenet_choices12002 = &old::ExecutePlayerReligionDraftTenetChoicesMailbox12002;
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

struct DraftBacking {
  Fixture base{};
  Bytes<0x48 * 2> selected_doctrines{};
  Bytes<0x70 * 2> selected_tenets{}, popup_tenets{};
  Bytes<0x20> popup_group{};
  Bytes<0x48> doctrine_popup{};
  Bytes<0x30> faith_storage{};
  Bytes<0x80> faith_slots{};
  Bytes<0x40> native_default{};
  std::array<const void *, 3> group_a_sources{
      base.doctrine_a.data(), base.doctrine_b.data(), base.doctrine_a.data()};
  std::array<const void *, 1> group_b_sources{base.doctrine_c.data()};
  void *faith_storage_ptr = faith_storage.data();
  void *native_default_ptr = native_default.data();
  unsigned trigger_calls{}, prophet_calls{}, filter_calls{}, main_status_calls{}, faith_status_calls{}, item_calls{};

  DraftBacking() {
    base.SetWindow(true);
    Collection(base.group_a, 0x140, group_a_sources);
    Collection(base.group_b, 0x140, group_b_sources);
    Put(selected_doctrines, 0x28, base.doctrine_a.data());
    Put(selected_doctrines, 0x48 + 0x28, base.doctrine_c.data());
    RawArray(base.window, 0x790, selected_doctrines.data(), 2);
    Put(base.window, 0x888, base.window.data());
    Put(base.window, 0x890, base.group_a.data());
    Put(base.window, 0x898, base.doctrine_a.data());
    Put(base.window, 0x8A0, static_cast<void *>(nullptr));
    Put(base.window, 0x8D8, std::int32_t{0});
    Put(doctrine_popup, 0x28, base.doctrine_a.data());
    RawArray(base.window, 0x8A8, doctrine_popup.data(), 1);
    Collection(base.window, 0x8C0, base.tenet_registry);
    Put(popup_tenets, 0x24, std::uint8_t{1});
    Put(popup_tenets, 0x28, base.tenet_b.data());
    Put(popup_tenets, 0x70 + 0x24, std::uint8_t{5});
    Put(popup_tenets, 0x70 + 0x28, base.tenet_c.data());
    RawArray(popup_group, 8, popup_tenets.data(), 2);
    RawArray(base.window, 0x7A8, popup_group.data(), 1);
    Put(selected_tenets, 0x20, std::uint32_t{7});
    Put(selected_tenets, 0x28, base.tenet_a.data());
    Put(selected_tenets, 0x70 + 0x20, std::uint32_t{11});
    Put(selected_tenets, 0x70 + 0x28, native_default.data());
    RawArray(base.window, 0x778, selected_tenets.data(), 2);
    Put(base.rite_slots, 2 * 0x10 + 8, base.rite.data());
    Put(base.rite_slots, 3 * 0x10 + 8, base.main_rite.data());
    Put(faith_storage, 0x20, faith_slots.data());
    Put(faith_storage, 0x2C, std::uint32_t{8});
    Put(faith_slots, 1 * 0x10 + 8, base.faith.data());
    Key(native_default, 0x18, "");
  }

  template <typename Buffer> static void RawArray(Buffer &out,
      std::size_t offset, void *rows, std::int32_t count) {
    Put(out, offset, rows); Put(out, offset + 8, count); Put(out, offset + 0xC, count);
  }
};
DraftBacking *draft_state = nullptr;

bool DraftTrigger(const void *trigger, const void *scope) {
  auto &d = *draft_state;
  ++d.trigger_calls;
  d.base.callback_scope_valid &= scope == d.base.window.data() + 0xD0;
  for (const auto *definition : {&d.base.doctrine_a, &d.base.doctrine_b, &d.base.doctrine_c}) {
    if (trigger == definition->data() + 0x1B8) return definition != &d.base.doctrine_c;
    if (trigger == definition->data() + 0xE8) return true;
  }
  for (const auto *definition : {&d.base.tenet_a, &d.base.tenet_b, &d.base.tenet_c})
    if (trigger == definition->data() + 0x658 || trigger == definition->data() + 0x4B8) return true;
  d.base.callback_scope_valid = false;
  return false;
}

bool DraftKnown(void *actor, const void *definition) {
  auto &d = *draft_state;
  d.base.callback_scope_valid &= actor == d.base.character.data();
  return definition == d.base.doctrine_a.data();
}

bool DraftProphet(void *actor, const void *perk) {
  auto &d = *draft_state;
  ++d.prophet_calls;
  d.base.callback_scope_valid &= actor == d.base.character.data() && perk == d.base.prophet.data();
  return false;
}

bool DraftItemGate(const void *item, void *actor, const void *scope) {
  auto &d = *draft_state;
  ++d.item_calls;
  d.base.callback_scope_valid &= (item == d.popup_tenets.data() || item == d.popup_tenets.data() + 0x70)
      && actor == d.base.character.data() && scope == d.base.window.data() + 0xD0;
  return Load<std::uint8_t>(item, 0x24) == std::uint8_t{1};
}

bool DraftSourceFilter(const void *category, const void *definition) {
  auto &d = *draft_state;
  ++d.filter_calls;
  d.base.callback_scope_valid &= category == d.base.window.data() + 0x888;
  return definition == d.base.tenet_b.data();
}

std::uint8_t DraftMainStatus(void *rite, const void *definition) {
  auto &d = *draft_state;
  ++d.main_status_calls;
  d.base.callback_scope_valid &= rite == d.base.main_rite.data();
  return definition == d.base.tenet_b.data() ? std::uint8_t{0} : std::uint8_t{5};
}

std::uint8_t DraftFaithStatus(void *faith, const void *definition) {
  auto &d = *draft_state;
  ++d.faith_status_calls;
  d.base.callback_scope_valid &= faith == d.base.faith.data();
  return definition == d.base.tenet_b.data() ? std::uint8_t{7} : std::uint8_t{0};
}

bindings4::DraftChoiceBindings Choices(DraftBacking &d) {
  auto b = bindings4::BindCurrentDraftChoices12004(Fixture::image_base, actual::kExecutableSha256);
  b.window.core = Core(d.base); b.window.is_visible = &Visible;
  b.knows_doctrine = &DraftKnown; b.evaluate_trigger = &DraftTrigger;
  b.has_perk = &DraftProphet; b.tenet_can_pick = &DraftItemGate;
  b.perk_database_global = &d.base.perk_database_ptr;
  return b;
}

bindings4::TenetSourcesBindings Sources(DraftBacking &d) {
  auto b = bindings4::BindCurrentDraftTenetSources12004(Fixture::image_base, actual::kExecutableSha256);
  b.window.core = Core(d.base); b.window.is_visible = &Visible;
  b.tenet_database_global = &d.base.tenet_database_ptr;
  b.default_tenet_definition_global = &d.native_default_ptr;
  b.rite_storage_global = &d.base.rite_storage_ptr;
  b.faith_storage_global = &d.faith_storage_ptr;
  b.perk_database_global = &d.base.perk_database_ptr;
  b.source_filter = &DraftSourceFilter; b.source_main_rite_status = &DraftMainStatus;
  b.actor_faith_status = &DraftFaithStatus; b.actor_extra_collection = &Extra;
  b.actor_perks_collection = &Perks; b.contains = &DefinitionMember;
  b.evaluate_trigger = &DraftTrigger;
  return b;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Assert(argc == 2, "output directory argument");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    DraftBacking memory;
    fixture_state = &memory.base; draft_state = &memory;
    game::Ck3_12004AdapterBindings adapter_bindings{};
    adapter_bindings.core = Core(memory.base);
    auto adapter = game::CreateCk3_12004AdapterFromBindings(std::move(adapter_bindings));
    Assert(adapter && adapter->enabled(), "actual .4 core adapter is enabled");
    game::Snapshot frame{};
    Assert(game::ReadCk3_12002TimelineCoreSnapshot(*adapter, frame), "actual .4 current owner core frame");
    const auto bound_choices = bindings4::BindCurrentDraftChoices12004(Fixture::image_base, actual::kExecutableSha256);
    const auto bound_sources = bindings4::BindCurrentDraftTenetSources12004(Fixture::image_base, actual::kExecutableSha256);
    const auto bound_terms = bindings4::BindDraftCreationTermsImage12004(Fixture::image_base, actual::kExecutableSha256);
    Assert(bound_choices.window.enabled && bound_sources.enabled && bound_terms.enabled &&
        reinterpret_cast<std::uintptr_t>(bound_choices.has_perk) == Fixture::image_base + 0x2919050 &&
        reinterpret_cast<std::uintptr_t>(bound_choices.tenet_can_pick) == Fixture::image_base + 0xEE0AD0 &&
        reinterpret_cast<std::uintptr_t>(bound_sources.source_filter) == Fixture::image_base + 0x14F2010 &&
        reinterpret_cast<std::uintptr_t>(bound_sources.actor_faith_status) == Fixture::image_base + 0x2442590 &&
        reinterpret_cast<std::uintptr_t>(bound_terms.draft_divergence) == Fixture::image_base + 0x14F1490 &&
        reinterpret_cast<std::uintptr_t>(bound_terms.creation_threshold_raw) == Fixture::image_base + 0x5C68C68 &&
        reinterpret_cast<std::uintptr_t>(bound_terms.native_create_faith_or_reform) == Fixture::image_base + 0x2BDCA70,
        "actual .4 binder supplies the separately mapped callback and loaded-define addresses");
    old::PlayerReligionDraftDoctrineChoicesMailboxContext12002 doctrine_query{};
    doctrine_query.bindings = Choices(memory);
    WholeWire(memory.base, *adapter, frame, doctrine_query,
        &old::RunPlayerReligionDraftDoctrineChoicesMailbox12002, directory,
        "draft-doctrine-choices.json", "ck3_12004_current_draft_full_doctrine_choices_v1");
    const auto &full = doctrine_query.observation;
    Assert(full.available && full.draft_observed && full.doctrine_gates_complete &&
        full.slots.size() == std::size_t{2} && full.slots[0].sources.size() == std::size_t{3} &&
        full.slots[1].sources.size() == std::size_t{1}, "all actual selected-slot group sources and duplicates remain complete");
    Assert(full.slots[0].sources[0].final_selectable &&
        !full.slots[0].sources[1].final_selectable && full.slots[0].sources[1].native_has_prophet == false &&
        full.slots[0].sources[2].final_selectable && full.slots[1].sources[0].passed_shown == false &&
        !full.slots[1].sources[0].native_knows_doctrine.has_value(), "actual true/false and short-circuit typed null preserved");
    old::PlayerReligionDraftGroupsMailboxContext12002 group_query{};
    group_query.bindings = Choices(memory);
    WholeWire(memory.base, *adapter, frame, group_query,
        &old::RunPlayerReligionDraftGroupsMailbox12002, directory,
        "draft-groups.json", "ck3_12004_current_draft_group_model_v1");
    const auto &groups = group_query.observation;
    Assert(groups.available && groups.category_materialized && groups.current_tenet_gate_complete &&
        groups.selected_slots.size() == std::size_t{2} && groups.current_tenet_choices.size() == std::size_t{2} &&
        groups.current_tenet_choices[0].final_can_pick && !groups.current_tenet_choices[1].final_can_pick,
        "actual current materialized two-item gates remain distinct from all-group source rows");
    old::PlayerReligionDraftTenetChoicesMailboxContext12002 tenet_query{};
    tenet_query.bindings = Sources(memory);
    WholeWire(memory.base, *adapter, frame, tenet_query,
        &old::RunPlayerReligionDraftTenetChoicesMailbox12002, directory,
        "draft-tenet-choices.json", "ck3_12004_current_draft_tenet_sources_v1");
    const auto &tenets = tenet_query.observation;
    Assert(tenets.available && tenets.draft_observed && tenets.tenet_gates_complete &&
        tenets.slots.size() == std::size_t{2} && tenets.slots[1].selected_tenet_key.empty() &&
        tenets.slots[1].slot_index == std::uint32_t{11} && tenets.sources.size() == std::size_t{3},
        "actual Null singleton preserves the blank slot and ordered duplicate loaded sources");
    Assert(tenets.sources[0].native_status_raw == std::uint8_t{0} &&
        tenets.sources[0].actor_faith_status_raw == std::uint8_t{7} &&
        tenets.sources[0].knowledge && tenets.sources[0].final_selectable &&
        tenets.sources[1].duplicate_excluded && !tenets.sources[1].final_selectable &&
        tenets.sources[2].final_selectable, "native uint8 zero/seven, extra knowledge and final predicates remain independent");
    std::cout << "PASS cases=3 actual_whole_mailbox=true old_cases_run=0 live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
