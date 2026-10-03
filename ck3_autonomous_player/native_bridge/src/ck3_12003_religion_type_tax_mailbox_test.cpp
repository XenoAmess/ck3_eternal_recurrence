#include "xar_bridge/ck3_12002_religion_mailbox.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include <cstdlib>

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
  Bytes<0x70> fulfillment_type{};
  Bytes<2 * r::fulfillment_progress12003::kLevelStride> fulfillment_levels{};
  std::string fulfillment_key = "christian_fulfillment";
  std::byte fulfillment_database{};
  void *fulfillment_database_pointer = &fulfillment_database;
  std::int64_t minimum_fulfillment = -10000000, maximum_fulfillment = 10000000;
  int type_getter_calls = 0;
  Bytes<0x1C0> church_land{};
  Bytes<0x30> church_context{}, church_lessee{}, church_faith{};
  Bytes<0x400> church_contract{};
  std::byte first_label{}, second_label{};
  static constexpr std::int32_t church_context_id = 0x05000002;
  static constexpr std::int32_t lessee_id = 0x03000006;
  static constexpr std::int32_t superior_id = 0x04000002;
  static constexpr std::int32_t top_id = 0x05000003;
  static constexpr std::uint32_t church_faith_id = 0x82000009;
  std::string income_rules_text = "Synthetic church tax \"rule\" \xe6\x94\xb6\xe7\x9b\x8a\n#P +3.333%#!";
  int prior_calls = 0, ruler_calls = 0, formatter_calls = 0, destroy_calls = 0;
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
    Put(extension, 0xA0, std::int64_t{750000});
    Tag(fulfillment_type, 0x18, fulfillment_key);
    Put(fulfillment_type, r::fulfillment_progress12003::kTypeLevelRowsOffset, fulfillment_levels.data());
    Put(fulfillment_type, r::fulfillment_progress12003::kTypeLevelCountOffset, std::int32_t{2});
    Put(fulfillment_levels, r::fulfillment_progress12003::kLevelLowerBoundOffset, std::int64_t{-3000000});
    Put(fulfillment_levels, r::fulfillment_progress12003::kLevelUpperBoundOffset, std::int64_t{3000000});
    Put(fulfillment_levels, r::fulfillment_progress12003::kLevelIndexOffset, std::int32_t{0});
    Put(fulfillment_levels, r::fulfillment_progress12003::kLevelStride + r::fulfillment_progress12003::kLevelIndexOffset, std::int32_t{1});
    Put(character, 0x1C0, church_land.data());
    Put(church_land, 0x1B8, lessee_id);
    Put(church_context, 0x18, church_context_id);
    Put(church_lessee, 0x18, lessee_id);
    Put(church_faith, 0x8, church_faith_id);
    Put(slots, 6 * 0x10 + 8, church_lessee.data());
    Put(church_contract, 0x68 + 0x8, std::int64_t{11000});
    Put(church_contract, 0x68 + 0x10, std::int64_t{12000});
    Put(church_contract, 0x68 + 0x2E8, std::int64_t{21000});
    Put(church_contract, 0x68 + 0x2F0, std::int64_t{22000});
    Put(church_contract, 0x68 + 0x2F8, std::int64_t{80000});
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
      xar::ck3_12003::kExecutableSha256, "synthetic-type-tax-combined-mailbox", {}};
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
void *TypeForCharacter(void *database, void *actor) {
  Check(database == &f->fulfillment_database && actor == f->character.data(),
        "existing type getter received fixture-owned actual database/player");
  ++f->type_getter_calls;
  return f->fulfillment_type.data();
}
void *LevelForValue(void *type, std::int64_t value) {
  Check(type == f->fulfillment_type.data() && value == 750000,
        "existing progress receives the same current fulfillment and type");
  return f->fulfillment_levels.data();
}
std::int64_t *ProgressWithinLevel(std::int64_t *out, std::int64_t value,
    std::int64_t lower, std::int64_t upper) {
  Check(value == 750000 && lower == -3000000 && upper == 3000000,
        "existing progress callback receives actual synthetic interval");
  *out = 6250000;
  return out;
}
void BindProgress(c::PlayerReligionMailboxContext12002 &query) {
  query.progress_bindings = {true, &f->fulfillment_database_pointer,
      &TypeForCharacter, &LevelForValue, &ProgressWithinLevel,
      &f->minimum_fulfillment, &f->maximum_fulfillment};
}
} // namespace

// Standalone fixture-only abort stubs: the real production renderer is linked
// in full, but this case never constructs a game adapter or binds a game image.
#if defined(XAR_RELIGION_TYPE_TAX_STANDALONE_RENDERER)
namespace xar::game {
Ck3_12002AdapterBindings BindCk3_12002AdapterImage(std::uintptr_t, std::string_view) noexcept { std::abort(); }
const AdapterDescriptor &Ck3_12002AdapterDescriptor() noexcept { std::abort(); }
std::unique_ptr<GameAdapter> CreateCk3_12003AdapterFromBindings(Ck3_12003AdapterBindings) noexcept { std::abort(); }
} // namespace xar::game
#endif

namespace {
namespace tax = xar::ck3_12003::religion::church_tax_inputs;
void *IncomeContext(void *owner) {
  Check(owner == f->character.data(), "tax context receives actual played actor");
  return f->church_context.data();
}
void *IncomeContextFaith(void *context) {
  Check(context == f->church_context.data(), "tax Faith comes from actual income context");
  return f->church_faith.data();
}
void *FaithLeaseContract(void *faith) {
  Check(faith == f->church_faith.data(), "tax rule comes from income-context Faith, not player Faith");
  return f->church_contract.data();
}
std::int32_t *LeaseLiege(void *manager, std::int32_t *out, std::int32_t lessee) {
  Check(manager == f->data.data() + 0x1F1E0 && lessee == Fixture::lessee_id,
        "native lease manager receives actual resolved lessee");
  *out = Fixture::superior_id; return out;
}
std::int32_t *TopLeaseLiege(std::int32_t *out, std::int32_t lessee) {
  Check(lessee == Fixture::lessee_id, "native top lease getter uses same actual lessee");
  *out = Fixture::top_id; return out;
}
std::int64_t *PriorShare(void *rule, std::int64_t *out, void *trigger,
    std::int64_t multiplier, std::int64_t ceiling, std::int32_t lessee,
    std::int32_t recipient, std::int64_t remaining, const void *label, void *text) {
  auto *expected = f->church_contract.data() + 0x68;
  Check(rule == expected && lessee == Fixture::lessee_id && text == nullptr,
        "native prior share receives selected rule and actual lessee");
  ++f->prior_calls;
  if (f->prior_calls == 1) {
    Check(trigger == expected + 0x108 && multiplier == 11000 && ceiling == 21000 &&
        recipient == Fixture::superior_id && remaining == 100000 && label == &f->first_label,
        "first native rule call starts with full fraction");
    *out = 1111;
  } else {
    Check(f->prior_calls == 2 && trigger == expected + 0x1F8 && multiplier == 12000 &&
        ceiling == 22000 && recipient == Fixture::top_id && remaining == 98889 && label == &f->second_label,
        "second native rule call consumes actual remaining fraction");
    *out = 2222;
  }
  return out;
}
std::int64_t *RulerShare(void *rule, std::int64_t *out, void *ruler,
    std::int32_t lessee, bool levy, std::int64_t remaining, void *text) {
  Check(rule == f->church_contract.data() + 0x68 && ruler == f->character.data() &&
      lessee == Fixture::lessee_id && !levy && remaining == 96667 && text == nullptr,
      "effective ruler tax receives actual rule owner and remaining fraction");
  ++f->ruler_calls; *out = 3333; return out;
}
tax::NativeString32 *IncomeRules(void *rule, tax::NativeString32 *out,
    void *ruler, void *lessee) {
  Check(rule == f->church_contract.data() + 0x68 && ruler == f->character.data() &&
      lessee == f->church_lessee.data(), "fresh formatter receives selected rule/player/resolved lessee");
  ++f->formatter_calls;
  auto *owned = new char[f->income_rules_text.size() + 1];
  std::memcpy(owned, f->income_rules_text.c_str(), f->income_rules_text.size() + 1);
  std::memcpy(out->bytes.data(), &owned, sizeof(owned));
  const auto size = static_cast<std::uint64_t>(f->income_rules_text.size());
  std::memcpy(out->bytes.data() + 0x10, &size, sizeof(size));
  std::memcpy(out->bytes.data() + 0x18, &size, sizeof(size));
  return out;
}
void DestroyIncomeRules(tax::NativeString32 *text) {
  ++f->destroy_calls;
  delete[] Get<char *>(text, 0);
}
void BindTax(c::PlayerReligionMailboxContext12002 &query) {
  auto &b = query.church_tax_bindings;
  b.enabled = true; b.core = query.bindings.core; b.game_state_slot = &f->state_ptr;
  b.income_context = &IncomeContext; b.character_faith = &IncomeContextFaith;
  b.faith_lease_contract = &FaithLeaseContract; b.lease_liege = &LeaseLiege;
  b.top_lease_liege_direct = &TopLeaseLiege; b.prior_share = &PriorShare;
  b.ruler_share = &RulerShare; b.income_rules = &IncomeRules;
  b.string_destroy = &DestroyIncomeRules;
  b.lease_liege_label = &f->first_label; b.top_lease_liege_direct_label = &f->second_label;
}

void RunCombinedCase(Fixture &fixture, FrameAdapter &adapter, const std::filesystem::path &directory) {
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(fixture, mailbox);
  c::PlayerReligionMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 1701;
  query.bindings = Bind(fixture);
  BindProgress(query); BindTax(query);
  adapter.reads = 0;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::RunPlayerReligionMailbox12002(query, "synthetic-type-tax-mailbox-one-case", serialized, failure);
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
        "actual production mailbox completed both new readers on the fixture owner");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual mailbox ticket reclaimed");
  Check(query.observation.available && query.progress.available &&
      query.progress.progress_percent_raw == 6250000, "existing Context/progress remains independent and observed");
  Check(query.spiritual_fulfillment_type.available &&
      query.spiritual_fulfillment_type.spiritual_fulfillment_type_key == fixture.fulfillment_key &&
      query.spiritual_fulfillment_type.has_christian_fulfillment_type == true && fixture.type_getter_calls == 2,
      "new type reader reuses existing type callback, retaining full stable key");
  const auto &observed = query.church_tax_inputs;
  Check(observed.available && observed.income_context_character_id == Fixture::church_context_id &&
      observed.income_context_faith_id == Fixture::church_faith_id &&
      observed.income_context_faith_id != query.observation.faith_id,
      "new tax reader uses income-context Faith rather than current player Faith");
  Check(observed.actual_lessee_character_id == Fixture::lessee_id &&
      observed.lease_liege_character_id == Fixture::superior_id &&
      observed.top_lease_liege_direct_character_id == Fixture::top_id &&
      observed.lease_liege_share_raw == 1111 && observed.top_lease_liege_direct_share_raw == 2222 &&
      observed.remaining_before_ruler_share_raw == 96667 && observed.effective_ruler_tax_share_raw == 3333 &&
      observed.native_configured_ruler_tax_ceiling_raw == 80000,
      "same mailbox publishes actual native share components and independent ceiling");
  Check(observed.income_rules_text == fixture.income_rules_text && fixture.prior_calls == 2 &&
      fixture.ruler_calls == 1 && fixture.formatter_calls == 1 && fixture.destroy_calls == 1,
      "same mailbox copied complete fresh native UTF8 rules and destroyed once");
  const auto epoch = query.envelope.execution_stamp.pump_epoch;
  Check(query.observation.capture_epoch == epoch && query.progress.capture_epoch == epoch &&
      query.spiritual_fulfillment_type.capture_epoch == epoch && observed.capture_epoch == epoch &&
      observed.date_raw == adapter.frame.date_raw && observed.played_character_id == Fixture::character_id,
      "both new siblings carry same actual synthetic owner date/actor/epoch");
  Check(!query.mystical_communion_terms.available && !query.pilgrimage_terms.available &&
      !query.confession_terms.available && !query.church_income_terms.available &&
      serialized.find("\"status\":\"observed\"") != std::string::npos,
      "unavailable independent old siblings do not change outer Context status");
  const auto rendered = xar::game::RenderCrozierBuildIdentity(std::move(serialized), adapter.descriptor());
  Check(rendered.find("\"game_version\":\"1.20.0.3\"") != std::string::npos &&
      rendered.find(std::string(xar::ck3_12003::kExecutableSha256)) != std::string::npos &&
      rendered.find("\"player_spiritual_fulfillment_type\":") != std::string::npos &&
      rendered.find("\"player_church_tax_inputs\":") != std::string::npos,
      "genuine full command_result and actual production .3 renderer retained both siblings");
  std::ofstream(directory / "native-wire.json", std::ios::binary) << rendered << '\n';
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory argument");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    Fixture fixture; FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::character_id;
    adapter.frame.date_raw = Get<std::int32_t>(fixture.state.data(), 8);
    RunCombinedCase(fixture, adapter, directory);
    std::cout << "PASS cases=1 checks=" << checks
        << " production_mailbox_reader_serializer_renderer=true synthetic_native_callbacks=true game=false live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
