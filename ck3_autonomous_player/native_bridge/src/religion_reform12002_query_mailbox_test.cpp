#include "xar_bridge/religion_reform12002_query_mailbox.hpp"

#include <array>
#include <atomic>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <thread>
#include <vector>

namespace c = xar::ck3_12002;
namespace r = c::religion;
namespace f = c::religion_reform;
namespace q = f::query;
namespace api = xar::ck3_11906;
namespace game = xar::game;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename Buffer, typename T> void Put(Buffer &buffer, std::size_t offset, T value) {
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}
template <typename T> T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
template <typename Buffer> void Key(Buffer &buffer, const char *value) {
  const auto size = std::strlen(value);
  std::memcpy(buffer.data() + 0x18, value, size);
  Put(buffer, 0x28, static_cast<std::uint64_t>(size));
  Put(buffer, 0x30, std::uint64_t{15});
}
template <typename Buffer, typename T> void Array(Buffer &buffer, std::size_t at, T data, std::int32_t count) {
  Put(buffer, at, data); Put(buffer, at + 8, count + 2); Put(buffer, at + 0xC, count);
}

// Native reader backing only. No query DTO, successful command envelope or
// serializer field is fabricated here; the actual provider assembles each one.
struct Fixture {
  Bytes<0xA8> state{}; Bytes<0x28> jomini{};
  Bytes<0x1F8> players{}; Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{}; std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> storage{}; Bytes<0x80> slots{}; Bytes<0x1D8> actor{};
  Bytes<0x8B8> current_rite{}, main_rite{};
  Bytes<0x320> faith{}; Bytes<0x40> religion{}; Bytes<0x50> religion_definition{};
  Bytes<0xB0> extension{}; Bytes<0x90> idler{}; Bytes<0x280> handler{};
  Bytes<0xC00> window{}; Bytes<0xB20> doctrine{}; Bytes<0x40> doctrine_group{};
  Bytes<0x50> doctrine_item{}; Bytes<0x40> tenet{}; Bytes<0x70> tenet_item{};
  Bytes<0x20> tenet_group{}; Bytes<0xF00> perk_database{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *storage_ptr = storage.data(), *perk_ptr = perk_database.data();
  static constexpr std::int32_t actor_id = 0x03000004, date = 53175816;
  static constexpr std::uint32_t rite_id = 0x80000000U, main_id = 0x81000002U;
  static constexpr std::uint32_t faith_id = 0x82000003U, religion_id = 0x83000005U;
  bool visible = true, create = true, edit = false, bad_quote = false;
  bool native_doctrine = true, should_display = true, known = true, prophet = false, native_tenet = false;
  bool bad_fervor = false;
  bool no_player = false;
  std::int64_t price = 9000000, missing = -2500000;
  unsigned draft_calls = 0, native_calls = 0;
  bool arguments_correct = true;

  Fixture() {
    Put(state, 8, date); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, actor.data()); Put(actor, 0x18, actor_id);
    Put(actor, r::kCharacterRiteIdOffset, rite_id); Put(actor, 0x1C8, extension.data());
    Put(current_rite, 8, rite_id); Put(current_rite, r::kRiteFaithIdOffset, faith_id);
    Put(current_rite, f::rite::kRiteFounderCharacterIdOffset, std::uint32_t{0xF3000007U});
    Put(current_rite, f::rite::kRiteHeadCharacterIdOffset, r::kAbsentReference);
    Put(main_rite, 8, main_id); Put(main_rite, r::kRiteFaithIdOffset, faith_id);
    main_rite[f::kRiteUnreformedOffset] = std::byte{1};
    Put(faith, 8, faith_id); Put(faith, r::kFaithReligionIdOffset, religion_id);
    Put(faith, r::kFaithMainRiteIdOffset, main_id);
    Put(faith, 0x2F8, std::int64_t{0}); Put(extension, 0xA0, std::int64_t{-345678});
    Put(religion, 8, religion_id); Put(religion, 0x10, std::int32_t{7});
    Put(religion, 0x20, religion_definition.data());
    Tag(faith, 0xE0, "faith\"key"); Tag(religion_definition, 0x28, "christianity");
    Put(jomini, 0x10, idler.data()); Put(idler, 0, std::uintptr_t{11});
    Put(idler, f::kDraftHandlerFromIdlerOffset, handler.data());
    Put(handler, 0, std::uintptr_t{22}); Put(handler, f::kDraftWindowFromHandlerOffset, window.data());
    Put(window, 0, std::uintptr_t{33}); Put(window, 0x10, std::uintptr_t{44});
    Put(window, f::kDraftWindowOwnerOffset, handler.data());
    Put(window, f::kDraftWindowRiteIdOffset, rite_id);
    Put(window, f::kDraftWindowActorIdOffset, static_cast<std::uint32_t>(actor_id));
    Key(doctrine, "doctrine_a"); Key(doctrine_group, "group_a");
    Put(doctrine, 0xB08, doctrine_group.data()); Put(doctrine_item, 0x28, doctrine.data());
    Array(window, 0x8A8, doctrine_item.data(), 1);
    Key(tenet, "tenet_a"); Put(tenet, 0x38, std::uint32_t{0x4744624F});
    Put(tenet_item, 0x28, tenet.data()); tenet_item[0x24] = std::byte{1};
    Array(tenet_group, 8, tenet_item.data(), 1); Array(window, 0x7A8, tenet_group.data(), 1);
    Put(perk_database, 0xEF0, player.data());
  }
  template <typename Buffer> static void Tag(Buffer &object, std::size_t at, std::string_view value) {
    std::memcpy(object.data() + at, value.data(), value.size());
    Put(object, at + 0x10, static_cast<std::uint64_t>(value.size()));
    Put(object, at + 0x18, std::uint64_t{15});
  }
};
Fixture *current_fixture = nullptr;
void *Player(void *) {
  ++current_fixture->native_calls;
  return current_fixture->no_player ? nullptr : current_fixture->player.data();
}
void *CharacterRite(void *) { return current_fixture->current_rite.data(); }
void *CharacterFaith(void *) { return current_fixture->faith.data(); }
void *RiteFaith(void *) { return current_fixture->faith.data(); }
void *FaithReligion(void *) { return current_fixture->religion.data(); }
void *FaithMainRite(void *) { return current_fixture->main_rite.data(); }
std::int64_t *Fervor(void *faith, std::int64_t *out) {
  if (current_fixture->bad_fervor) return nullptr;
  *out = Get<std::int64_t>(faith, 0x2F8); return out;
}
std::int64_t *Fulfillment(void *actor, std::int64_t *out) {
  *out = Get<std::int64_t>(Get<void *>(actor, 0x1C8), 0xA0); return out;
}
const void *FaithTag(void *faith) { return static_cast<const std::byte *>(faith) + 0xE0; }
const void *ReligionTag(void *) { return current_fixture->religion_definition.data() + 0x28; }
bool IsMain(void *) { return false; }
std::int64_t *Divergence(std::int64_t *out, void *rite, void *tooltip) {
  current_fixture->arguments_correct &= rite == current_fixture->current_rite.data() && tooltip == nullptr;
  *out = 7500000; return out;
}
std::int64_t *Threshold(void *, std::int64_t *out) { *out = 8000000; return out; }
bool Unreformed(void *faith) {
  current_fixture->arguments_correct &= faith == current_fixture->faith.data();
  return current_fixture->main_rite[f::kRiteUnreformedOffset] != std::byte{0};
}
bool Visible(const void *) { return current_fixture->visible; }
std::int64_t *Cost(void *window, std::int64_t *out) {
  ++current_fixture->draft_calls; current_fixture->arguments_correct &= window == current_fixture->window.data();
  if (current_fixture->bad_quote) return nullptr;
  *out = current_fixture->price; return out;
}
std::int64_t *Missing(void *, std::int64_t *out) {
  ++current_fixture->draft_calls; *out = current_fixture->missing; return out;
}
bool Editing(void *) { ++current_fixture->draft_calls; return current_fixture->edit; }
bool Create(const void *window, void *reason) {
  ++current_fixture->draft_calls; current_fixture->arguments_correct &= window == current_fixture->window.data() && reason == nullptr;
  return current_fixture->create;
}
bool Edit(const void *window, void *reason) {
  ++current_fixture->draft_calls; current_fixture->arguments_correct &= window == current_fixture->window.data() && reason == nullptr;
  return current_fixture->edit;
}
bool Trigger(const void *trigger, const void *scope) {
  ++current_fixture->draft_calls;
  current_fixture->arguments_correct &= scope == current_fixture->window.data() + 0xD0 &&
      (trigger == current_fixture->doctrine.data() + 0x1B8 || trigger == current_fixture->doctrine.data() + 0xE8);
  return trigger == current_fixture->doctrine.data() + 0x1B8
      ? current_fixture->should_display : current_fixture->native_doctrine;
}
bool Knows(void *actor, const void *definition) {
  ++current_fixture->draft_calls;
  current_fixture->arguments_correct &= actor == current_fixture->actor.data() && definition == current_fixture->doctrine.data();
  return current_fixture->known;
}
bool HasPerk(void *actor, const void *perk) {
  ++current_fixture->draft_calls;
  current_fixture->arguments_correct &= actor == current_fixture->actor.data() && perk == current_fixture->player.data();
  return current_fixture->prophet;
}
bool Tenet(const void *item, void *actor, const void *scope) {
  ++current_fixture->draft_calls;
  current_fixture->arguments_correct &= item == current_fixture->tenet_item.data() && actor == current_fixture->actor.data() &&
      scope == current_fixture->window.data() + 0xD0;
  return current_fixture->native_tenet;
}
q::Bindings Bind(Fixture &fixture) {
  current_fixture = &fixture;
  q::Bindings b{}; b.enabled = true;
  b.core = {true, &fixture.state_ptr, &fixture.jomini_ptr, &fixture.storage_ptr, &Player};
  b.context = {true, b.core, &CharacterRite, &CharacterFaith, &RiteFaith, &FaithReligion,
      &FaithMainRite, &Fervor, &Fulfillment, &FaithTag, &ReligionTag};
  b.rite_model = {true, b.core, &CharacterRite, &RiteFaith, &FaithMainRite,
      &IsMain, &Divergence, &Threshold};
  b.main_rite = {true, &FaithMainRite, &Unreformed};
  b.window = {true, b.core, 11, 22, 33, 44, &Visible};
  b.costs = {true, &Cost, &Missing, &Editing};
  b.eligibility = {true, &Create, &Edit};
  b.choices = {b.window, &Knows, &Trigger, &Tenet, &HasPerk, &fixture.perk_ptr};
  return b;
}

int checks = 0;
void Check(bool condition, const char *message) {
  ++checks; if (!condition) throw std::runtime_error(message);
}
// Frame adapter only supplies the published semantic snapshot; all reform data
// is read by the actual native providers against fixture-owned memory.
class FrameAdapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  const DWORD owner = GetCurrentThreadId();
  mutable unsigned reads = 0;
  bool drift = false;
  game::AdapterDescriptor identity{"ck3-1.20.0.2-msvc-x64", "1.20.0.2",
      c::kExecutableSha256, "reform-fixture", {}};
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
    // This library fixture exercises the existing permitted executor; central
    // registration of the dedicated reform slot is verified by its owner.
    mailbox.permitted_executor = &c::ExecutePlayerReligionReformMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned index = 0; index < 2; ++index)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};

bool Query(Fixture &fixture, FrameAdapter &adapter, const std::filesystem::path &directory,
           const char *filename, q::Observation &observed) {
  api::MainThreadQueryMailboxV1 mailbox{}; Pump pump(fixture, mailbox);
  c::PlayerReligionReformMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 701;
  query.bindings = Bind(fixture); adapter.reads = 0;
  std::atomic<bool> done{false}; bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::RunPlayerReligionReformMailbox12002(query, "reform\"mailbox-fixture", serialized, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Check(drained, "actual queued executor drained on owner");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual terminal ticket reclaimed");
  observed = query.observation;
  if (result) {
    Check(query.completed && query.envelope.frame_stable && failure.empty() && !serialized.empty(),
          "actual stable mailbox returned complete wire");
    Check(observed.capture_epoch == query.envelope.execution_stamp.pump_epoch && observed.capture_epoch != 701,
          "native capture epoch differs from published revision");
    std::ofstream(directory / filename) << serialized << '\n';
  } else {
    Check(serialized.empty() && !failure.empty(), "unstable query returns no success wire");
    std::ofstream(directory / "frame-changed-rejection.json")
        << "{\"success_wire_emitted\":false,\"mailbox_reclaimed\":true,\"failure\":\""
        << failure << "\"}\n";
  }
  return result;
}
} // namespace

#if defined(XAR_REFORM_MAILBOX_STANDALONE_ADAPTER)
namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept { return adapter; }
}
#endif

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory argument");
    const std::filesystem::path directory(argv[1]);
    // Allocate the backing on the heap so /Od remains independent of the
    // compiler's lifetime stack reservations for this combined reader fixture.
    auto fixture = std::make_unique<Fixture>(); FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::actor_id;
    adapter.frame.date_raw = Fixture::date;
    q::Observation out{};
    Check(Query(*fixture, adapter, directory, "visible-create.json", out) && out.available &&
          out.context.faith_id == Fixture::faith_id && out.rite_model.current_is_main == false &&
          out.main_rite.status == f::MainRiteStatus::observed && out.main_rite.is_unreformed &&
          out.current_window.visible && out.draft_eligibility.can_create_rite == true &&
          out.draft_eligibility.can_edit_rite == false && out.draft_costs.piety_missing_signed_raw == -2500000 &&
          out.popup_choices.doctrines.size() == 1 && out.popup_choices.tenets.size() == 1 &&
          out.current_doctrine_selection.selection_ready &&
          out.current_doctrine_selection.selectable_doctrine_keys == std::vector<std::string>{"doctrine_a"} &&
          fixture->arguments_correct,
          "actual components combine through owning mailbox");
    fixture->price = 0; fixture->missing = 0;
    Check(Query(*fixture, adapter, directory, "visible-zero-cost.json", out) && out.available &&
          out.draft_costs.piety_cost_raw == 0 && out.draft_costs.piety_missing_signed_raw == 0 &&
          out.draft_costs.has_enough_piety == true && out.current_doctrine_selection.selection_ready,
          "native observed zero quote survives complete result wire");
    fixture->price = 9000000; fixture->missing = -2500000;
    fixture->create = false; fixture->edit = true; fixture->known = false;
    Check(Query(*fixture, adapter, directory, "visible-denied.json", out) && out.available &&
          out.draft_eligibility.can_create_rite == false && out.draft_eligibility.can_edit_rite == true &&
          !out.popup_choices.doctrines[0].button_enabled && !out.popup_choices.tenets[0].native_can_pick &&
          out.current_doctrine_selection.selection_ready &&
          out.current_doctrine_selection.selectable_doctrine_keys.empty(),
          "native final false remains an observed result");
    fixture->known = true; fixture->should_display = false;
    Check(Query(*fixture, adapter, directory, "doctrine-hidden-row.json", out) && out.available &&
          out.current_doctrine_selection.selection_ready && out.current_doctrine_selection.rows.size() == 1 &&
          !out.current_doctrine_selection.rows[0].native_should_display &&
          out.current_doctrine_selection.rows[0].selection_blocker == "hidden_by_native_should_display" &&
          out.current_doctrine_selection.selectable_doctrine_keys.empty(),
          "actual native ShouldDisplay denial excludes materialized Doctrine row");
    fixture->should_display = true;
    Array(fixture->window, 0x8A8, fixture->doctrine_item.data(), 0);
    Array(fixture->window, 0x7A8, fixture->tenet_group.data(), 0);
    Check(Query(*fixture, adapter, directory, "empty-popup.json", out) && out.available &&
          out.popup_choices.available && out.popup_choices.draft_observed &&
          out.current_doctrine_selection.selection_ready && out.current_doctrine_selection.rows.empty() &&
          out.current_doctrine_selection.selectable_doctrine_keys.empty(),
          "visible current popup with zero rows is observed and selection ready");
    Array(fixture->window, 0x8A8, fixture->doctrine_item.data(), 1);
    Array(fixture->window, 0x7A8, fixture->tenet_group.data(), 1);
    fixture->visible = false; const auto calls = fixture->draft_calls;
    Check(Query(*fixture, adapter, directory, "hidden-window.json", out) && out.available &&
          out.current_window.present && !out.current_window.visible && !out.draft_costs.available &&
          !out.draft_eligibility.can_create_rite && !out.current_doctrine_selection.selection_ready &&
          fixture->draft_calls == calls,
          "hidden cached draft exposes no draft-only values or native calls");
    Put(fixture->handler, f::kDraftWindowFromHandlerOffset, static_cast<void *>(nullptr));
    Check(Query(*fixture, adapter, directory, "absent-window.json", out) && out.available &&
          !out.current_window.present && !out.current_window.window && fixture->draft_calls == calls,
          "known no materialized draft stays observed with null draft values");
    Put(fixture->handler, f::kDraftWindowFromHandlerOffset, fixture->window.data());
    fixture->visible = true; fixture->bad_quote = true;
    Check(Query(*fixture, adapter, directory, "cost-unavailable.json", out) && out.available &&
          !out.draft_costs.available && !out.draft_costs.piety_cost_raw && out.draft_eligibility.available,
          "actual failed quote retains independent final eligibility");
    fixture->bad_quote = false; fixture->perk_ptr = nullptr; fixture->known = false;
    fixture->tenet_item[0x24] = std::byte{0};
    Check(Query(*fixture, adapter, directory, "choices-unavailable.json", out) && out.available &&
          !out.popup_choices.available && out.popup_choices.doctrines.empty() && out.popup_choices.tenets.empty() &&
          out.draft_costs.available, "actual popup failure retains independent cost query");
    fixture->perk_ptr = fixture->perk_database.data(); fixture->tenet_item[0x24] = std::byte{1};
    fixture->bad_fervor = true;
    Check(Query(*fixture, adapter, directory, "context-unavailable.json", out) && out.available &&
          !out.context.available && !out.context.faith_fervor_raw && out.rite_model.available,
          "current-context failed getter leaves independently observed Rite model");
    fixture->bad_fervor = false; fixture->no_player = true;
    Check(Query(*fixture, adapter, directory, "query-unavailable.json", out) && !out.available &&
          out.failure == "played_character_unavailable" && !out.context.available && !out.draft_costs.piety_cost_raw,
          "new query read callback failure serializes actual typed unavailable result");
    fixture->no_player = false; adapter.drift = true;
    Check(!Query(*fixture, adapter, directory, "frame-changed.json", out), "owner full snapshot changed after capture");
    std::uint64_t revision = 0;
    Check(c::ParsePlayerReligionReformRevision12002("{}", revision) && revision == 0, "optional revision");
    Check(c::ParsePlayerReligionReformRevision12002("{\"expected_snapshot_revision\":701}", revision) &&
          revision == 701, "canonical revision parsed");
    Check(c::ParsePlayerReligionReformRevision12002("{\"expected_revision\":701}", revision) &&
          revision == 701, "revision alias parsed");
    Check(!c::ParsePlayerReligionReformRevision12002("{\"expected_revision\":701,\"expected_snapshot_revision\":702}", revision),
          "conflicting expected revisions rejected");
    api::MainThreadQueryMailboxV1 mailbox{}; std::string wire, failure;
    Check(!c::HandlePlayerReligionReformPrivate12002(adapter, mailbox, adapter.frame, 701,
          c::kPlayerReligionReformPrivateStep12002, "{\"expected_revision\":702}", "stale", wire, failure) &&
          wire.empty() && mailbox.next_sequence == 0, "actual handler rejects stale frame before native submission");
    Check(c::IsPlayerReligionReformPrivateStep12002(c::kPlayerReligionReformPrivateStep12002) &&
          !c::IsPlayerReligionReformPrivateStep12002("query-player-religion-context-v1"), "exact reform selector");
    std::cout << "PASS checks=" << checks << " cases=12 actual_core=true actual_assembly=true "
                 "actual_submit_owner_drain_wait_reclaim=true actual_command_result=true live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
