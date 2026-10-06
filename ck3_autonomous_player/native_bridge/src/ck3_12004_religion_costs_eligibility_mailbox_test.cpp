// FIRST_NOTRUN: one new adopted costs/final-reasons/creation-terms whole .4 packet. Only owned
// synthetic memory/native callbacks are used. The production .4 adapter,
// selected core reader, topic mailboxes, DTO serializers and renderer run.
// No old fixture main, production stub, macro replacement or game process.
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_religion_bindings.hpp"
#include "xar_bridge/ck3_12004_religion_profile.hpp"
#include "xar_bridge/ck3_12004_religion_costs_eligibility_bindings.hpp"
#include "xar_bridge/ck3_12004_religion_draft_bindings.hpp"
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
  Bytes<0x40> group_a{}, group_b{};
  Bytes<0x70> doctrine_database{};
  Bytes<0x40> tenet_a{}, tenet_b{}, tenet_c{}, prophet{};
  Bytes<0xF00> tenet_database{}, perk_database{};
  Bytes<0x28> token_a{}, token_b{}, token_c{};
  Bytes<0x90> idler{};
  Bytes<0x280> handler{};
  Bytes<0xB30> window{};
  Bytes<0x30> faith_storage{};
  Bytes<0x80> faith_slots{};
  void *faith_storage_ptr = faith_storage.data();
  std::int64_t threshold{};
  unsigned cost_calls{}, missing_calls{}, owned_calls{}, create_calls{}, edit_calls{}, destroy_calls{}, divergence_calls{}, lane_calls{};
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
    Put(rite_slots, 2 * 0x10 + 8, rite.data());
    Put(rite_slots, 3 * 0x10 + 8, main_rite.data());
    Put(faith_storage, 0x20, faith_slots.data()); Put(faith_storage, 0x2C, std::uint32_t{8});
    Put(faith_slots, 1 * 0x10 + 8, faith.data());
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

constexpr std::string_view kCreateReason =
    "Synthetic native create gate: \"blocked\"\\detail\n"
    "\xE5\x8E\x9F\xE7\x94\x9F\xE5\x8E\x9F\xE5\x9B\xA0\xE4\xBF\x9D\xE7\x95\x99";
void CheckWindow(const void *window) {
  fixture_state->callback_scope_valid &= Owner() && window == fixture_state->window.data();
}
std::int64_t *Cost(void *window, std::int64_t *out) {
  CheckWindow(window); ++fixture_state->cost_calls;
  *out = 1'250'000; return out;
}
std::int64_t *Missing(void *window, std::int64_t *out) {
  CheckWindow(window); ++fixture_state->missing_calls;
  *out = 0; return out;
}
bool Owned(void *window) { CheckWindow(window); ++fixture_state->owned_calls; return true; }
bool CanCreate(const void *window, void *reason) {
  CheckWindow(window); ++fixture_state->create_calls;
  fixture_state->callback_scope_valid &= reason != nullptr &&
      Load<std::uint64_t>(reason, 0x10) == std::uint64_t{0} &&
      Load<std::uint64_t>(reason, 0x18) == std::uint64_t{15};
  auto *text = new char[kCreateReason.size() + 1];
  std::memcpy(text, kCreateReason.data(), kCreateReason.size());
  text[kCreateReason.size()] = 0;
  std::memcpy(reason, &text, sizeof(text));
  const auto size = static_cast<std::uint64_t>(kCreateReason.size());
  std::memcpy(static_cast<std::byte *>(reason) + 0x10, &size, sizeof(size));
  std::memcpy(static_cast<std::byte *>(reason) + 0x18, &size, sizeof(size));
  return false;
}
bool CanEdit(const void *window, void *reason) {
  CheckWindow(window); ++fixture_state->edit_calls;
  fixture_state->callback_scope_valid &= reason != nullptr &&
      Load<std::uint64_t>(reason, 0x10) == std::uint64_t{0} &&
      Load<std::uint64_t>(reason, 0x18) == std::uint64_t{15};
  return true;
}
void DestroyReason(void *reason) {
  ++fixture_state->destroy_calls;
  fixture_state->callback_scope_valid &= Owner() && reason != nullptr;
  if (Load<std::uint64_t>(reason, 0x18) >= std::uint64_t{16})
    delete[] Load<char *>(reason, 0);
}
std::int64_t *DraftDivergence(std::int64_t *out, const void *window) {
  CheckWindow(window); ++fixture_state->divergence_calls;
  *out = 0; return out;
}
bool NativeLane(const void *faith, const void *price_draft) {
  ++fixture_state->lane_calls;
  fixture_state->callback_scope_valid &= Owner() && faith == fixture_state->faith.data() &&
      price_draft == fixture_state->window.data() + 0xB28;
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
  value.costs = bindings4::BindRiteCreationCostsImage12004(Fixture::image_base, actual::kExecutableSha256);
  value.costs.piety_cost = &Cost; value.costs.piety_missing = &Missing;
  value.costs.editing_owned_current_rite = &Owned;
  value.eligibility = bindings4::BindEligibilityImage12004(Fixture::image_base, actual::kExecutableSha256);
  value.eligibility.can_create_rite = &CanCreate; value.eligibility.can_edit_rite = &CanEdit;
  value.eligibility.destroy_reason_string = &DestroyReason;
  value.creation_terms = bindings4::BindDraftCreationTermsImage12004(Fixture::image_base, actual::kExecutableSha256);
  value.creation_terms.rite_storage_global = &memory.rite_storage_ptr;
  value.creation_terms.faith_storage_global = &memory.faith_storage_ptr;
  value.creation_terms.draft_divergence = &DraftDivergence;
  value.creation_terms.creation_threshold_raw = &memory.threshold;
  value.creation_terms.native_create_faith_or_reform = &NativeLane;
  // Separate new popup producer owns that scene and its callbacks.
  value.choices = {};
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
  constexpr auto base = Fixture::image_base;
  const auto cost = bindings4::BindRiteCreationCostsImage12004(base, actual::kExecutableSha256);
  const auto eligibility = bindings4::BindEligibilityImage12004(base, actual::kExecutableSha256);
  Assert(cost.enabled && reinterpret_cast<std::uintptr_t>(cost.piety_cost) == base + 0x14F57A0 &&
      reinterpret_cast<std::uintptr_t>(cost.piety_missing) == base + 0x14F58C0 &&
      reinterpret_cast<std::uintptr_t>(cost.editing_owned_current_rite) == base + 0x14F43E0,
      "cost factory supplies three complete actual4 mapped roots");
  Assert(eligibility.enabled && reinterpret_cast<std::uintptr_t>(eligibility.can_create_rite) == base + 0x14F56B0 &&
      reinterpret_cast<std::uintptr_t>(eligibility.can_edit_rite) == base + 0x14F5030 &&
      reinterpret_cast<std::uintptr_t>(eligibility.destroy_reason_string) == base + 0x856050,
      "actual4 final-gate predicates and complete native string destructor");
  Assert(!bindings4::BindRiteCreationCostsImage12004(base, old::kExecutableSha256).enabled &&
      !bindings4::BindEligibilityImage12004(0, actual::kExecutableSha256).enabled,
      "exact actual4 identity and image admission retained");
  const auto composite = bindings4::BindReformQueryImage12004(base, actual::kExecutableSha256);
  Assert(composite.costs.enabled && composite.eligibility.enabled && composite.creation_terms.enabled,
      "production composite restores adopted providers");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Assert(argc == 2, "one output directory argument is required");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    BinderCases();
    Fixture memory;
    fixture_state = &memory;
    memory.SetWindow(true);
    game::Ck3_12004AdapterBindings adapter_bindings{};
    adapter_bindings.core = Core(memory);
    auto adapter = game::CreateCk3_12004AdapterFromBindings(std::move(adapter_bindings));
    Assert(adapter && adapter->enabled() && game::IsCk3_12004Descriptor(adapter->descriptor()),
        "actual production4 adapter factory selected");
    game::Snapshot frame{};
    Assert(game::ReadCk3_12002TimelineCoreSnapshot(*adapter, frame) && frame.paused && frame.map_ready &&
        frame.has_played_character && frame.played_character_alive &&
        frame.played_character_id == Fixture::actor_id && frame.date_raw == Fixture::date,
        "selected actual4 core callback supplies supported owner frame");
    std::uint64_t revision{};
    Assert(old::ParsePlayerReligionReformRevision12002("{\"expected_snapshot_revision\":701}", revision) &&
        revision == std::uint64_t{701}, "production request parser supplies native revision");
    old::PlayerReligionReformMailboxContext12002 query{};
    query.bindings = Reform(memory);
    const auto wire = WholeWire(memory, *adapter, frame, query, &old::RunPlayerReligionReformMailbox12002,
        directory, "visible-composite-costs-reasons.json", "ck3_12004_player_religion_reform_query_v1");
    const auto epoch = query.envelope.execution_stamp.pump_epoch;
    const auto &value = query.observation;
    Assert(value.capture_epoch == epoch && value.date_raw == Fixture::date && value.played_character_id == Fixture::actor_id &&
        value.available && value.context.available && value.rite_model.available &&
        value.main_rite.status == reform::MainRiteStatus::observed && value.current_window.available &&
        value.current_window.present && value.current_window.visible,
        "restored components consume same actual visible owner window");
    const auto &cost = value.draft_costs;
    Assert(cost.available && cost.failure == reform::CostFailure::none && cost.capture_epoch == epoch &&
        cost.date_raw == Fixture::date && cost.played_character_id == Fixture::actor_id &&
        cost.source_rite_id == Fixture::rite_id && cost.editing_owned_current_rite == true &&
        cost.piety_cost_raw == std::int64_t{1'250'000} && cost.piety_missing_signed_raw == std::int64_t{0} &&
        cost.has_enough_piety == true && memory.cost_calls == 2U && memory.missing_calls == 2U && memory.owned_calls == 2U,
        "two native quotes preserve legal zero signed missing and true budget gate");
    const auto &eligibility = value.draft_eligibility;
    Assert(eligibility.available && eligibility.failure == reform::EligibilityFailure::none &&
        eligibility.draft_actor_id == static_cast<std::uint32_t>(Fixture::actor_id) &&
        eligibility.can_create_rite == false && eligibility.can_edit_rite == true &&
        eligibility.can_create_rite_native_text == std::string(kCreateReason) &&
        eligibility.can_edit_rite_native_text == std::string{} &&
        memory.create_calls == 1U && memory.edit_calls == 1U && memory.destroy_calls == 2U,
        "independent native final bools retain full heap and empty inline text");
    const auto &terms = value.draft_creation_terms;
    Assert(value.publish_creation_terms && terms.available && terms.failure == "none" &&
        terms.capture_epoch == epoch && terms.date_raw == Fixture::date &&
        terms.played_character_id == static_cast<std::uint32_t>(Fixture::actor_id) &&
        terms.source_rite_id == Fixture::rite_id && terms.source_faith_id == Fixture::faith_id &&
        terms.source_main_rite_id == Fixture::main_id && terms.actor_faith_id == Fixture::faith_id &&
        terms.draft_divergence_raw == std::int64_t{0} && terms.faith_creation_threshold_raw == std::int64_t{0} &&
        terms.divergence_results_in_faith_creation == true && terms.native_create_faith_or_reform == false &&
        memory.divergence_calls == 2U && memory.lane_calls == 2U,
        "actual fullref source storage preserves zero UI equality and independent native lane");
    Assert(!value.popup_choices.available && !value.current_doctrine_selection.available &&
        wire.find("ck3_12004_current_draft_creation_terms_v1") != std::string::npos,
        "new wholewire publishes restored terms; separate producer owns popup inputs");
    std::cout << "PASS cases=1 checks=" << checks
        << " actual_adapter=true actual_core_reader=true actual_named_mailbox=true actual_serializer=true"
        << " actual_renderer=true actual_full_wire=true synthetic_memory=true synthetic_callbacks=true"
        << " native_cost_calls=2 native_missing_calls=2 native_owned_calls=2 native_create_calls=1"
        << " native_edit_calls=1 native_reason_destroy_calls=2 native_divergence_calls=2 native_lane_calls=2"
        << " legacy_main_executed=false production_stubs=false live=false\n";
    fixture_state = nullptr;
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
