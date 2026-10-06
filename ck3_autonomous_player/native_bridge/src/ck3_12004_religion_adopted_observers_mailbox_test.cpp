// FIRST_NOTRUN: four new complete .4 owner-mailbox wires. Synthetic memory and
// callbacks feed production binders/readers/serializers/renderer; no old main.
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_religion_adopted_observers.hpp"
#include "xar_bridge/ck3_12004_religion_costs_eligibility_bindings.hpp"
#include "xar_bridge/ck3_12004_religion_profile.hpp"
#include "xar_bridge/religion_reform12002_resource_costs_mailbox.hpp"
#include "xar_bridge/religion_rite_governance12002_mailbox.hpp"
#include "xar_bridge/religion_rite_governance12002_members_mailbox.hpp"

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
namespace binding = actual::religion;
namespace adopted = binding::adopted;
namespace profile = binding::profile;
namespace religion = old::religion;
namespace reform = old::religion_reform;
namespace members = religion::organization::members;
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
struct Fixture {
  static constexpr std::uintptr_t image_base = 0x140000000;
  static constexpr std::int32_t actor_id = 0x03000004, date = 53175816;
  static constexpr std::uint32_t rite_id = 0x82000002, main_id = 0x83000002;
  static constexpr std::uint32_t faith_id = 0x84000001, religion_id = 0x85000001;
  static constexpr std::uint32_t player_title_id = 0x86000001, realm_title_id = 0x87000002;
  static constexpr std::uint32_t state_rite_id = 0x88000003, county_id = 0x89000003;
  static constexpr std::uint32_t faith_head_title_id = 0x8A000004;
  const DWORD owner = GetCurrentThreadId();
  Bytes<0xA8> state{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x2EE80);
  Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> character_storage{}, title_storage{};
  Bytes<0x80> character_slots{}, title_slots{};
  std::array<Bytes<0x1D8>, 4> characters{};
  Bytes<0x1F0> actor_landed{}, liege_landed{};
  std::array<std::uint32_t, 1> actor_titles{player_title_id}, liege_titles{realm_title_id};
  Bytes<0x8D0> rite{}, main_rite{}, state_rite{};
  Bytes<0x310> faith{};
  Bytes<0x210> native_religion{};
  Bytes<0x310> player_title{}, realm_title{}, county{}, faith_head_title{};
  Bytes<0x68> county_definition{};
  std::array<void *, 3> alive{characters[0].data(), characters[1].data(), characters[2].data()};
  std::array<std::uint32_t, 1> counties{county_id};
  Bytes<0x28> holder{};
  std::array<Bytes<0x30>, 4> ai{};
  std::array<Bytes<0x2A0>, 2> ai_extensions{};
  std::array<const void *, 4> ai_rows{ai[0].data(), ai[1].data(), ai[2].data(), ai[3].data()};
  std::array<std::int32_t, 7> rare_periods{10, 20, 30, 40, 50, 60, 70};
  const std::int32_t *rare_periods_ptr = rare_periods.data();
  std::uint8_t reformation_toggle{1};
  Bytes<0x90> idler{};
  Bytes<0x280> handler{};
  Bytes<0xD0> window{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *character_storage_ptr = character_storage.data(), *title_storage_ptr = title_storage.data();
  unsigned core_calls{}, piety_calls{}, collector_calls{};
  bool callback_scope_valid{true};
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
    for (std::size_t index = 0; index < characters.size(); ++index) {
      Put(character_slots, (index + 4) * 0x10 + 8, characters[index].data());
      Put(characters[index], actual::kCharacterFullIdOffset, actor_id + static_cast<std::int32_t>(index));
      Put(characters[index], 0x1C, std::uint32_t{0x43686172});
      Put(characters[index], 0xB4, index == 2 ? main_id : rite_id);
    }
    Put(characters[0], 0x1C0, actor_landed.data());
    Put(characters[1], 0x1C0, liege_landed.data());
    Put(actor_landed, 0x1E0, actor_titles.data()); Put(actor_landed, 0x1EC, std::int32_t{1});
    Put(liege_landed, 0x1E0, liege_titles.data()); Put(liege_landed, 0x1EC, std::int32_t{1});
    const std::array<std::uint32_t, 3> rite_ids{rite_id, main_id, state_rite_id};
    const std::array<Bytes<0x8D0> *, 3> rites{&rite, &main_rite, &state_rite};
    for (std::size_t index = 0; index < rites.size(); ++index) {
      Put(*rites[index], 8, rite_ids[index]);
      Put(*rites[index], 0xC, std::uint32_t{0x52697465});
      Put(*rites[index], 0x4B8, faith_id);
    }
    Put(rite, 0x4C0, std::uint32_t{0x03000007});
    Put(main_rite, 0x4C0, std::uint32_t{0x03000006});
    Put(rite, 0x18, std::int32_t{0}); Put(rite, 0x1C, std::int32_t{0});
    Put(faith, 8, faith_id); Put(faith, 0x8C, religion_id); Put(faith, 0x98, main_id);
    Put(faith, 0x300, faith_head_title_id);
    Put(native_religion, 8, religion_id);
    Put(native_religion, 0x200, counties.data()); Put(native_religion, 0x20C, std::int32_t{1});
    Put(data, members::kAlivePoolOffset, alive.data());
    Put(data, members::kAlivePoolSizeOffset, std::int32_t{3});
    Put(player_title, 0x10, player_title_id); Put(player_title, 0x308, main_id);
    Put(realm_title, 0x10, realm_title_id); Put(realm_title, 0x308, state_rite_id);
    Put(county, 0x10, county_id); Put(county, 0x48, county_definition.data());
    Put(county_definition, 0x64, std::int32_t{2});
    Put(faith_head_title, 0x10, faith_head_title_id);
    Put(faith_head_title, 0x128, std::uint32_t{0x03000005});
    Put(title_storage, 0x20, title_slots.data()); Put(title_storage, 0x2C, std::int32_t{8});
    const std::array<void *, 4> titles{player_title.data(), realm_title.data(), county.data(), faith_head_title.data()};
    for (std::size_t index = 0; index < titles.size(); ++index) Put(title_slots, (index + 1) * 0x10 + 8, titles[index]);
    Put(data, reform::kAIContextManagerOffset + reform::kAIContextHolderOffset, holder.data());
    Put(holder, 8, ai[0].data()); Put(holder, 0x10, ai_rows.data()); Put(holder, 0x1C, std::int32_t{4});
    for (std::size_t index = 0; index < ai.size(); ++index) {
      Put(ai[index], 0x18, index == 2 ? characters[1].data() : characters[0].data());
      Put(ai[index], 0x28, std::uint32_t{0x41495374});
    }
    Put(ai[1], 0x14, std::uint16_t{64}); Put(ai[1], 0x16, std::uint8_t{1});
    Put(ai[1], 0x20, ai_extensions[0].data());
    Put(ai_extensions[0], 0x284, std::int32_t{-3}); Put(ai_extensions[0], 0x29B, std::uint8_t{0});
    Put(ai[3], 0x14, std::uint16_t{0}); Put(ai[3], 0x16, std::uint8_t{1});
    Put(ai[3], 0x2C, std::uint8_t{1}); Put(ai[3], 0x2E, std::uint8_t{1});
    Put(ai[3], 0x20, ai_extensions[1].data());
    Put(ai_extensions[1], 0x284, std::int32_t{11}); Put(ai_extensions[1], 0x29B, std::uint8_t{1});
    Put(jomini, 0x10, idler.data());
    Put(idler, 0, image_base + profile::kDraftIdlerVtableRva); Put(idler, 0x88, handler.data());
    Put(handler, 0, image_base + profile::kDraftHandlerVtableRva); Put(handler, 0x278, window.data());
    Put(window, 0, image_base + profile::kDraftWindowPrimaryVtableRva);
    Put(window, 0x10, image_base + profile::kDraftWindowSecondaryVtableRva);
    Put(window, 0xA0, handler.data()); Put(window, 0xC8, rite_id);
    Put(window, 0xCC, static_cast<std::uint32_t>(actor_id));
  }
  void Reset() { core_calls = piety_calls = collector_calls = 0; callback_scope_valid = true; }
};
Fixture *memory{};
bool Owner() { return GetCurrentThreadId() == memory->owner; }
void *Player(void *owner) {
  ++memory->core_calls;
  memory->callback_scope_valid &= Owner() && owner == memory->jomini.data();
  return memory->player.data();
}
void *CharacterRite(void *actor) {
  memory->callback_scope_valid &= Owner();
  for (std::size_t index = 0; index < memory->characters.size(); ++index)
    if (actor == memory->characters[index].data()) return index == 2 ? memory->main_rite.data() : memory->rite.data();
  memory->callback_scope_valid = false; return nullptr;
}
void *CharacterFaith(void *actor) {
  memory->callback_scope_valid &= Owner() && actor == memory->characters[0].data();
  return memory->faith.data();
}
void *RiteFaith(void *rite) {
  memory->callback_scope_valid &= Owner() && (rite == memory->rite.data() ||
      rite == memory->main_rite.data() || rite == memory->state_rite.data());
  return memory->faith.data();
}
void *FaithReligion(void *faith) {
  memory->callback_scope_valid &= Owner() && faith == memory->faith.data();
  return memory->native_religion.data();
}
void *FaithMainRite(void *faith) {
  memory->callback_scope_valid &= Owner() && faith == memory->faith.data();
  return memory->main_rite.data();
}
void *TopLiege(void *actor) {
  memory->callback_scope_valid &= Owner() && actor == memory->characters[0].data();
  return memory->characters[1].data();
}
void *PrimaryTitle(void *actor) {
  memory->callback_scope_valid &= Owner() &&
      (actor == memory->characters[0].data() || actor == memory->characters[1].data());
  return actor == memory->characters[0].data() ? memory->player_title.data() : memory->realm_title.data();
}
void *TitleStateRite(void *title) {
  memory->callback_scope_valid &= Owner() &&
      (title == memory->player_title.data() || title == memory->realm_title.data());
  return title == memory->player_title.data() ? memory->main_rite.data() : memory->state_rite.data();
}
std::uint32_t *RiteHeadId(void *rite, std::uint32_t *out) {
  memory->callback_scope_valid &= Owner() && (rite == memory->rite.data() || rite == memory->main_rite.data());
  *out = Load<std::uint32_t>(rite, 0x4C0); return out;
}
void *RiteHead(void *rite) {
  memory->callback_scope_valid &= Owner() && (rite == memory->rite.data() || rite == memory->main_rite.data());
  return rite == memory->rite.data() ? memory->characters[3].data() : memory->characters[2].data();
}
void *FaithHead(void *faith) {
  memory->callback_scope_valid &= Owner() && faith == memory->faith.data();
  return memory->characters[1].data();
}
void *FaithHeadTitle(void *faith) {
  memory->callback_scope_valid &= Owner() && faith == memory->faith.data();
  return memory->faith_head_title.data();
}
std::int32_t CountyCount(void *rite) {
  memory->callback_scope_valid &= Owner() && rite == memory->rite.data(); return 0;
}
std::int32_t FollowerCount(void *rite) {
  memory->callback_scope_valid &= Owner() && rite == memory->rite.data(); return 0;
}
std::int32_t HighestTier(void *actor) {
  memory->callback_scope_valid &= Owner() && actor == memory->characters[0].data(); return 3;
}
bool Independent(void *actor) {
  memory->callback_scope_valid &= Owner() && actor == memory->characters[0].data(); return true;
}
bool Visible(const void *window) {
  memory->callback_scope_valid &= Owner() && window == memory->window.data(); return true;
}
std::int64_t *Piety(void *window, std::int64_t *out) {
  ++memory->piety_calls;
  memory->callback_scope_valid &= Owner() && window == memory->window.data();
  *out = 45'000'000; return out;
}
std::int64_t *Missing(void *window, std::int64_t *out) {
  memory->callback_scope_valid &= Owner() && window == memory->window.data();
  *out = -2'500'000; return out;
}
bool Editing(void *window) {
  memory->callback_scope_valid &= Owner() && window == memory->window.data(); return false;
}
void FaithCharacters(void *receiver, members::ScopeArray *out, const members::ScopeRoot *root) {
  ++memory->collector_calls;
  memory->callback_scope_valid &= Owner() && receiver == nullptr && root && root->root &&
      root->root->kind == members::kFaithScope && root->root->identity == Fixture::faith_id &&
      out && out->capacity == 3 && out->size == 0 && out->allocator == nullptr;
  // Deliberate unsorted output: the production member reader publishes sorted IDs.
  out->data[0] = {members::kCharacterScope, 0, 0, 0x03000006};
  out->data[1] = {members::kCharacterScope, 0, 0, 0x03000004};
  out->data[2] = {members::kCharacterScope, 0, 0, 0x03000005}; out->size = 3;
}
void RiteCounties(void *receiver, members::ScopeArray *out, const members::ScopeRoot *root) {
  ++memory->collector_calls;
  memory->callback_scope_valid &= Owner() && receiver == nullptr && root && root->root &&
      root->root->kind == members::kRiteScope && root->root->identity == Fixture::rite_id &&
      out && out->capacity == 1 && out->size == 0 && out->allocator == nullptr;
  out->data[0] = {members::kTitleScope, 0, 0, Fixture::county_id}; out->size = 1;
}
actual::CoreBindings Core() {
  return {true, &memory->state_ptr, &memory->jomini_ptr, &memory->character_storage_ptr, &Player};
}
binding::ContextBindings Context() {
  auto out = binding::BindReligionContextImage12004(Fixture::image_base, actual::kExecutableSha256);
  out.core = Core(); out.character_rite = &CharacterRite; out.character_faith = &CharacterFaith;
  out.rite_faith = &RiteFaith; out.faith_religion = &FaithReligion; out.faith_main_rite = &FaithMainRite;
  return out;
}
adopted::AIReformInputsBindings AI() {
  auto out = adopted::BindPlayerReligionAIReformInputsImage12004(Fixture::image_base, actual::kExecutableSha256);
  out.core = Core(); out.context.game_state_slot = &memory->state_ptr;
  out.schedule.highest_tier = &HighestTier; out.schedule.independent_ruler = &Independent;
  out.schedule.rare_periods = &memory->rare_periods_ptr; out.schedule.reformation_toggle = &memory->reformation_toggle;
  return out;
}
adopted::GovernanceBindings Governance() {
  auto out = adopted::BindRiteGovernanceImage12004(Fixture::image_base, actual::kExecutableSha256);
  out.core = Core(); out.state_rite.context = Context(); out.heads.context = Context();
  out.state_rite.character_top_liege = &TopLiege; out.state_rite.character_primary_title = &PrimaryTitle;
  out.state_rite.title_state_rite = &TitleStateRite; out.heads.rite_head_id = &RiteHeadId;
  out.heads.rite_head = &RiteHead; out.heads.faith_religious_head = &FaithHead;
  out.heads.faith_religious_head_title = &FaithHeadTitle;
  out.organization.core = Core(); out.organization.character_rite = &CharacterRite;
  out.organization.county_count = &CountyCount; out.organization.character_follower_count = &FollowerCount;
  return out;
}
adopted::MembersBindings Members() {
  auto out = adopted::BindOrganizationMembersImage12004(Fixture::image_base, actual::kExecutableSha256);
  out.core = Core(); out.character_rite = &CharacterRite; out.rite_faith = &RiteFaith;
  out.faith_religion = &FaithReligion; out.title_storage_slot = &memory->title_storage_ptr;
  out.faith_characters = &FaithCharacters; out.rite_counties = &RiteCounties; return out;
}
void *tls_context{};
void *__fastcall FixtureTls() noexcept { return tls_context; }
struct Pump {
  Bytes<0x28> tls{};
  std::uint8_t initialized = 1;
  std::uintptr_t unused_rng{};
  Pump(api::MainThreadQueryMailboxV1 &mailbox) {
    tls[0x20] = std::byte{1}; tls_context = tls.data();
    mailbox.global_rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&unused_rng);
    mailbox.jomini_state_slot = reinterpret_cast<std::uintptr_t>(&memory->jomini_ptr);
    mailbox.game_state_slot = reinterpret_cast<std::uintptr_t>(&memory->state_ptr);
    mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter = &FixtureTls;
    mailbox.executor_submission_enabled = true;
    mailbox.permitted_executor_religion_draft_resource_costs12002 = &old::ExecutePlayerReligionDraftResourceCostsMailbox12002;
    mailbox.permitted_executor_religion_ai_reform_inputs12002 = &old::ExecutePlayerReligionAIReformInputsMailbox12002;
    mailbox.permitted_executor_rite_governance12002 = &old::ExecutePlayerRiteGovernanceMailbox12002;
    mailbox.permitted_executor_rite_members12002 = &old::ExecutePlayerRiteMembersMailbox12002;
    mailbox.iat_hook_installed = true; mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned index = 0; index < 2; ++index)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};
template <class Query, class Run>
void WholeWire(const game::GameAdapter &adapter, const game::Snapshot &frame,
    Query &query, Run run, const std::filesystem::path &directory,
    const char *filename, std::string_view schema) {
  memory->Reset();
  api::MainThreadQueryMailboxV1 mailbox{}; Pump pump(mailbox);
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = frame; query.envelope.expected_snapshot_revision = 701;
  query.envelope.snapshot_comparison = old::QuerySnapshotComparison12002::core_frame;
  std::atomic<bool> done{false}; bool complete = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    complete = run(query, "religion-12004-adopted-synthetic-fixture", serialized, failure);
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
      "actual named production owner mailbox completes and retains the selected core frame");
  Assert(mailbox.state == api::MainThreadQueryMailboxStateV1::idle &&
      memory->callback_scope_valid && memory->core_calls > 0, "terminal reclaim and actual owner callback scope");
  const auto epoch = query.envelope.execution_stamp.pump_epoch;
  Assert(query.observation.available && query.observation.capture_epoch == epoch && epoch > 0 && epoch != std::uint64_t{701} &&
      query.observation.date_raw == Fixture::date &&
      static_cast<std::uint32_t>(query.observation.played_character_id) == static_cast<std::uint32_t>(Fixture::actor_id),
      "whole domain observation has actual independent pump epoch and published actor/date");
  auto rendered = game::Render12004BuildIdentity(std::move(serialized), adapter.descriptor());
  Assert(rendered.find("\"type\":\"command_result\"") != std::string::npos &&
      rendered.find("\"snapshot_revision\":701") != std::string::npos &&
      rendered.find("\"game_version\":\"1.20.0.4\"") != std::string::npos &&
      rendered.find(actual::kExecutableSha256) != std::string::npos && rendered.find(schema) != std::string::npos,
      "central production .4 renderer stamps the complete native wire");
  std::ofstream output(directory / filename, std::ios::binary); output << rendered << '\n';
  Assert(static_cast<bool>(output), "complete native business packet is written once without reconstruction");
}
void BinderCases() {
  const auto base = Fixture::image_base;
  const auto ai = adopted::BindPlayerReligionAIReformInputsImage12004(base, actual::kExecutableSha256);
  Assert(ai.core.enabled && ai.context.enabled && ai.schedule.enabled &&
      reinterpret_cast<std::uintptr_t>(ai.schedule.highest_tier) == base + 0x28AC690 &&
      reinterpret_cast<std::uintptr_t>(ai.schedule.independent_ruler) == base + 0x28BFFE0 &&
      reinterpret_cast<std::uintptr_t>(ai.schedule.rare_periods) == base + 0x5449D90 &&
      reinterpret_cast<std::uintptr_t>(ai.schedule.reformation_toggle) == base + 0x5448579,
      "actual .4 AI callbacks and retained used RIP globals select the qualified finite rows");
  const auto gov = adopted::BindRiteGovernanceImage12004(base, actual::kExecutableSha256);
  Assert(gov.enabled && gov.state_rite.enabled && gov.heads.enabled && gov.organization.enabled &&
      reinterpret_cast<std::uintptr_t>(gov.state_rite.character_top_liege) == base + 0x28BFD80 &&
      reinterpret_cast<std::uintptr_t>(gov.state_rite.character_primary_title) == base + 0x289DA10 &&
      reinterpret_cast<std::uintptr_t>(gov.state_rite.title_state_rite) == base + 0x2315010 &&
      reinterpret_cast<std::uintptr_t>(gov.heads.rite_head_id) == base + 0xD55CF0 &&
      reinterpret_cast<std::uintptr_t>(gov.heads.rite_head) == base + 0x24FC5F0 &&
      reinterpret_cast<std::uintptr_t>(gov.heads.faith_religious_head) == base + 0x2439DF0 &&
      reinterpret_cast<std::uintptr_t>(gov.heads.faith_religious_head_title) == base + 0x2443F80 &&
      reinterpret_cast<std::uintptr_t>(gov.organization.county_count) == base + 0xB80410 &&
      reinterpret_cast<std::uintptr_t>(gov.organization.character_follower_count) == base + 0xEDDB90,
      "all actual governance callback addresses retain their independent source roles");
  const auto member = adopted::BindOrganizationMembersImage12004(base, actual::kExecutableSha256);
  Assert(member.enabled && member.core.enabled &&
      reinterpret_cast<std::uintptr_t>(member.title_storage_slot) == base + 0x5D1DAF8 &&
      reinterpret_cast<std::uintptr_t>(member.faith_characters) == base + 0x1C610C0 &&
      reinterpret_cast<std::uintptr_t>(member.rite_counties) == base + 0x1D2B6D0,
      "actual collector callbacks and reached typed title slot select the qualified bodies");
  Assert(binding::BindRiteCreationCostsImage12004(base, actual::kExecutableSha256).enabled &&
      !adopted::BindPlayerReligionAIReformInputsImage12004(base, old::kExecutableSha256).core.enabled &&
      !adopted::BindRiteGovernanceImage12004(0, actual::kExecutableSha256).enabled &&
      !adopted::BindOrganizationMembersImage12004(base, "unreviewed").enabled,
      "shared native cost factory and own actual build admission are exercised without legacy factory aliases");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Assert(argc == 2, "one complete-wire output directory");
    const std::filesystem::path directory(argv[1]); std::filesystem::create_directories(directory);
    BinderCases(); Fixture storage; memory = &storage;
    game::Ck3_12004AdapterBindings adapter_bindings{}; adapter_bindings.core = Core();
    auto adapter = game::CreateCk3_12004AdapterFromBindings(std::move(adapter_bindings));
    Assert(adapter && adapter->enabled() && game::IsCk3_12004Descriptor(adapter->descriptor()),
        "production actual .4 adapter is selected");
    game::Snapshot frame{};
    Assert(game::ReadCk3_12002TimelineCoreSnapshot(*adapter, frame) && frame.paused && frame.map_ready &&
        frame.has_played_character && frame.played_character_alive &&
        frame.played_character_id == Fixture::actor_id && frame.date_raw == Fixture::date,
        "actual selected core path supplies only the supported owner frame");
    constexpr std::string_view payload = "{\"expected_snapshot_revision\":701}";
    std::uint64_t revision{};
    old::PlayerReligionDraftResourceCostsMailboxContext12002 resource{};
    Assert(old::ParsePlayerReligionDraftResourceCostsRevision12002(payload, revision) && revision == std::uint64_t{701},
        "production resource request parser");
    resource.window_bindings = binding::BindCurrentRiteCreationWindow12004(Fixture::image_base, actual::kExecutableSha256);
    resource.window_bindings.core = Core(); resource.window_bindings.is_visible = &Visible;
    resource.cost_bindings = binding::BindRiteCreationCostsImage12004(Fixture::image_base, actual::kExecutableSha256);
    resource.cost_bindings.piety_cost = &Piety; resource.cost_bindings.piety_missing = &Missing;
    resource.cost_bindings.editing_owned_current_rite = &Editing;
    WholeWire(*adapter, frame, resource, &old::RunPlayerReligionDraftResourceCostsMailbox12002,
        directory, "resource-costs.json", "ck3_12004_player_religion_draft_resource_costs_query_v1");
    const auto &base = resource.observation.base_resource_cost_quote;
    const std::array<std::int64_t, 10> expected_slots{0, 0, 45'000'000, 0, 0, 0, 0, 0, 0, 0};
    Assert(resource.observation.draft_observed && base.base_resource_cost_vector_observed &&
        base.native_base_fee_slots_raw && *base.native_base_fee_slots_raw == expected_slots &&
        base.draft_quote.available && base.draft_quote.piety_cost_raw == std::int64_t{45'000'000} &&
        base.draft_quote.piety_missing_signed_raw == std::int64_t{-2'500'000} && base.draft_quote.has_enough_piety == true &&
        base.draft_quote.editing_owned_current_rite == false && base.draft_quote.source_rite_id == Fixture::rite_id &&
        memory->piety_calls == 2U, "signed quote, legal zero slots and non-action base fee survive the actual native composite");

    old::PlayerReligionAIReformInputsMailboxContext12002 ai{};
    Assert(old::ParsePlayerReligionAIReformInputsRevision12002(payload, revision) && revision == std::uint64_t{701},
        "production AI inputs request parser");
    ai.bindings = AI();
    WholeWire(*adapter, frame, ai, &old::RunPlayerReligionAIReformInputsMailbox12002,
        directory, "reform-ai-inputs.json", "ck3_12004_player_religion_ai_reform_inputs_v1");
    const auto &inputs = ai.observation;
    Assert(inputs.context.status == reform::AIContextStatus::observed_controllers &&
        inputs.context.actual_holder_count == std::int32_t{4} && inputs.context.controllers.size() == std::size_t{2} &&
        inputs.controller_inputs.size() == std::size_t{2} && inputs.gate_inputs_observation_complete &&
        inputs.schedule_base.highest_tier == std::int32_t{3} && inputs.schedule_base.rare_period == std::int32_t{40} &&
        inputs.schedule_base.current_independent_ruler && inputs.schedule_base.reformation_enabled &&
        inputs.schedule_base.ai_status == reform::ScheduleAIStatus::not_supplied,
        "actual holder excludes default and other actor while preserving inactive and special controllers");
    const auto &ordinary = inputs.controller_inputs[0].schedule, &special = inputs.controller_inputs[1].schedule;
    Assert(inputs.context.controllers[0].active_raw == std::uint8_t{0} && inputs.context.controllers[0].special_raw == std::uint8_t{0} &&
        inputs.context.controllers[1].active_raw == std::uint8_t{1} && inputs.context.controllers[1].special_raw == std::uint8_t{1} &&
        ordinary.ai_status == reform::ScheduleAIStatus::observed && ordinary.handler_cache_gates_pass &&
        ordinary.ai_government_flags == std::uint16_t{64} && ordinary.ai_independent_flags == std::uint8_t{1} &&
        ordinary.rare_countdown_prepare_ticks == std::int32_t{-3} && ordinary.rare_selected_raw == std::uint8_t{0} &&
        special.ai_status == reform::ScheduleAIStatus::observed && !special.handler_cache_gates_pass &&
        special.ai_government_flags == std::uint16_t{0} && special.ai_independent_flags == std::uint8_t{1} &&
        special.rare_countdown_prepare_ticks == std::int32_t{11} && special.rare_selected_raw == std::uint8_t{1},
        "signed prepare countdown and independent observed false gates remain actual native input values");

    old::PlayerRiteGovernanceMailboxContext12002 governance{};
    Assert(old::ParsePlayerRiteGovernanceRevision12002(payload, revision) && revision == std::uint64_t{701},
        "production governance request parser");
    governance.bindings = Governance();
    WholeWire(*adapter, frame, governance, &old::RunPlayerRiteGovernanceMailbox12002,
        directory, "rite-governance.json", "ck3_12004_player_rite_governance_v1");
    const auto &gov = governance.observation;
    Assert(gov.frame_available && gov.state_rite.available && gov.heads.available && gov.organization.available &&
        gov.state_rite.actor_rite_id == Fixture::rite_id && gov.state_rite.actor_faith_main_rite_id == Fixture::main_id &&
        gov.state_rite.top_liege_character_id == std::uint32_t{0x03000005} &&
        gov.state_rite.player_primary_title.title_id == Fixture::player_title_id &&
        gov.state_rite.player_primary_title.state_rite_id == Fixture::main_id &&
        gov.state_rite.realm_primary_title.title_id == Fixture::realm_title_id &&
        gov.state_rite.realm_primary_title.state_rite_id == Fixture::state_rite_id &&
        gov.heads.actor_rite_head_character_id == std::uint32_t{0x03000007} &&
        gov.heads.faith_main_rite_head_character_id == std::uint32_t{0x03000006} &&
        gov.heads.faith_religious_head_title_id == Fixture::faith_head_title_id &&
        gov.heads.faith_religious_head_holder_character_id == std::uint32_t{0x03000005} &&
        gov.organization.county_count == std::int32_t{0} && gov.organization.character_follower_count == std::int32_t{0},
        "three actual governance components preserve distinct Rite/title/head sources and literal zero counts");

    old::PlayerRiteMembersMailboxContext12002 member{};
    Assert(old::ParsePlayerRiteMembersRevision12002(payload, revision) && revision == std::uint64_t{701},
        "production member request parser");
    member.bindings = Members();
    WholeWire(*adapter, frame, member, &old::RunPlayerRiteMembersMailbox12002,
        directory, "rite-members.json", "ck3_12004_rite_organization_members_v1");
    const auto &ids = member.observation;
    Assert(ids.rite_id == Fixture::rite_id && ids.faith_id == Fixture::faith_id && ids.religion_id == Fixture::religion_id &&
        ids.faith_character_ids == std::vector<std::uint32_t>{0x03000004, 0x03000005, 0x03000006} &&
        ids.rite_character_ids == std::vector<std::uint32_t>{0x03000004, 0x03000005} &&
        ids.county_title_ids == std::vector<std::uint32_t>{Fixture::county_id} && memory->collector_calls == 2U,
        "actual full references, caller-buffer scopes and existing native published ordering survive the member reader");
    std::cout << "PASS cases=4 checks=" << checks
        << " actual_adapter=true actual_core_reader=true actual_named_mailbox=true actual_serializer=true"
        << " actual_renderer=true actual_full_wire=true synthetic_memory=true synthetic_callbacks=true"
        << " legacy_main_executed=false production_stubs=false live=false\n";
    memory = nullptr; return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n'; return 1;
  }
}
