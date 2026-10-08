#include "xar_bridge/ordinary_holy_war_declaration_context12003_mailbox.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_holy_war_defender_join_inputs.hpp"
#include "xar_bridge/ck3_12003_holy_war_defender_join_inputs.hpp"

#include <array>
#include <atomic>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <thread>
#include <vector>

namespace c = xar::ck3_12002;
namespace game = xar::game;
namespace api = xar::ck3_11906;
namespace h = c::religion::holy_war_defender_join;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template <typename T> T Get(const void *object, std::size_t offset) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value)); return value;
}
void Array(void *object, const std::int32_t *ids, std::int32_t count) {
  Put(object, 0, ids); Put(object, 8, count); Put(object, 12, count);
}
constexpr std::int32_t kActor = 0x03000001, kTarget = 0x04000002, kAdditional = 0x05000003;
constexpr std::int32_t kDate = 53222304;
constexpr std::uint64_t kNativeRevision = 9, kPublicRevision = 2, kCaptureEpoch = 991;
constexpr std::int32_t kNpcFirst = 0x08000006, kNpcSecond = 0x06000004;
constexpr std::uint32_t kActorRite = 0x30000001U, kAdditionalRite = 0x31000002U;
constexpr std::uint32_t kTargetRite = 0x32000003U, kFirstRite = 0x33000004U, kSecondRite = 0x34000005U;
constexpr std::uint32_t kActorFaith = 0x20000001U, kAdditionalFaith = 0x21000002U, kTargetFaith = 0x22000003U;
constexpr std::array<const char *, 6> kWireFiles{
    "ordered_npc_rows_positive_values.json", "legal_zero_and_same_faith.json", "empty_native_joiner_set.json",
    "defender_faith_branch_disabled.json", "row_fervor_failure_retains_native_set.json",
    "native_role_fallback_independent_of_old_status.json"};
constexpr std::array<const char *, 6> kRequestIds{
    "g2-read-00000000000000000000000000004707", "g2-read-00000000000000000000000000004708",
    "g2-read-00000000000000000000000000004709", "g2-read-00000000000000000000000000004710",
    "g2-read-00000000000000000000000000004711", "g2-read-00000000000000000000000000004712"};
constexpr std::array<std::int64_t, 10> kNonzeroCosts{
    -250000, 1234567, 20000000, 0, 33, 44, 55, 66, 77, 88};
unsigned checks = 0;
void Check(bool condition, const char *message) {
  ++checks; if (!condition) throw std::runtime_error(message);
}
struct War {
  Bytes<0x58> bytes{};
  std::vector<std::int32_t> titles;
  void Sync() { Array(bytes.data() + c::kDeclarationsWarTitlesOffset, titles.data(), static_cast<std::int32_t>(titles.size())); }
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
  Bytes<0x70> slots{};
  Bytes<0x1D8> actor{}, target{}, additional{}, fallback{}, npc_first{}, npc_second{};
  Bytes<0x4C0> actor_rite{}, target_rite{}, additional_rite{}, first_rite{}, second_rite{};
  Bytes<0x300> actor_faith{}, additional_faith{}, target_faith{};
  Bytes<0x18> engine_allocator{};
  std::array<std::uint32_t, 1> same_faith_parameters{0x9001U};
  h::Bindings defender_join{};
  void **allocated_rows = nullptr;
  std::int32_t last_fervor_character = -1;
  unsigned collector_calls = 0, row_frees = 0, fervor_calls = 0;
  Bytes<0x98> cb_database{};
  Bytes<0xF80> interaction_database{};
  Bytes<0x18B8> type{};
  Bytes<0x218> rule{};
  std::array<void *, 1> types{type.data()};
  Bytes<0x18> scratch{};
  Bytes<c::kDeclarationsConfigurationSize> configuration{};
  std::array<std::int32_t, 2> titles{0x010000A2, 0x020000A1};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  void *fallback_ptr = fallback.data();
  c::DeclarationsBindings declarations{};
  c::OrdinaryHolyWarCbCostBindingsV1 cost{};
  std::size_t scenario = 0;
  bool bad_arguments = false;
  unsigned evaluations = 0, configuration_destroys = 0, context_constructs = 0, context_destroys = 0;
  unsigned refreshes = 0, finalizes = 0, validations = 0, scope_constructs = 0, scope_populates = 0;
  unsigned scope_destroys = 0, cost_evaluations = 0, commands = 0;
  const void *populated_scope = nullptr;
  const void *actual_native_titles = nullptr;
  c::OrdinaryHolyWarDeclarationContextMailbox12003 *owning_query = nullptr;
  explicit Fixture(std::size_t which) : scenario(which) {
    Put(state.data(), 8, kDate); Put(state.data(), 0x70, std::int32_t{2}); Put(state.data(), 0xA0, data.data());
    Put(jomini.data(), 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players.data(), 0x1F0, std::int32_t{7}); Put(player.data(), 0x70, std::int32_t{7});
    Put(data.data(), c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data.data(), c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry.data(), 0xD8, std::int32_t{7}); Put(entry.data(), 0xB0, kActor);
    Put(storage.data(), 0x20, slots.data()); Put(storage.data(), 0x2C, std::int32_t{7});
    Put(slots.data(), 0x18, actor.data()); Put(slots.data(), 0x28, target.data()); Put(slots.data(), 0x38, additional.data());
    Put(actor.data(), 0x18, kActor); Put(target.data(), 0x18, kTarget); Put(additional.data(), 0x18, kAdditional);
    Put(fallback.data(), 0x18, std::int32_t{-1});
    Put(slots.data(), 0x68, npc_first.data()); Put(slots.data(), 0x48, npc_second.data());
    Put(npc_first.data(), 0x18, kNpcFirst); Put(npc_second.data(), 0x18, kNpcSecond);
    Put(actor.data(), 0xB4, kActorRite); Put(additional.data(), 0xB4, kAdditionalRite);
    Put(target.data(), 0xB4, kTargetRite); Put(npc_first.data(), 0xB4, kFirstRite); Put(npc_second.data(), 0xB4, kSecondRite);
    Put(actor_rite.data(), 8, kActorRite); Put(additional_rite.data(), 8, kAdditionalRite);
    Put(target_rite.data(), 8, kTargetRite); Put(first_rite.data(), 8, kFirstRite); Put(second_rite.data(), 8, kSecondRite);
    Put(actor_rite.data(), 0x4B8, kActorFaith);
    Put(additional_rite.data(), 0x4B8, scenario == 1 ? kTargetFaith : kAdditionalFaith);
    Put(target_rite.data(), 0x4B8, kTargetFaith); Put(first_rite.data(), 0x4B8, kTargetFaith); Put(second_rite.data(), 0x4B8, kTargetFaith);
    Put(actor_faith.data(), 8, kActorFaith); Put(additional_faith.data(), 8, kAdditionalFaith); Put(target_faith.data(), 8, kTargetFaith);
    Put(actor_faith.data(), 0x2F8, std::int64_t{5000000}); Put(additional_faith.data(), 0x2F8, std::int64_t{2500000});
    Put(target_faith.data(), 0x2F8, scenario == 1 ? std::int64_t{0} : std::int64_t{7500000});
    Put(type.data(), c::kDeclarationsCbFlagsOffset, scenario == 3 ? std::uint32_t{0} : std::uint32_t{1U << 15});
    if (scenario == 1) {
      Put(type.data(), 0x18A8, same_faith_parameters.data()); Put(type.data(), 0x18B4, std::int32_t{1});
    }
    Put(cb_database.data(), c::kDeclarationsCbArrayOffset, types.data());
    Put(cb_database.data(), c::kDeclarationsCbCountOffset, std::int32_t{1});
    Put(type.data(), c::kDeclarationsCbRuleOffset, rule.data());
    const char key[] = "religious_war";
    std::memcpy(type.data() + 0x18, key, sizeof(key));
    Put(type.data(), 0x28, std::size_t{sizeof(key) - 1}); Put(type.data(), 0x30, std::size_t{15});
    Put(type.data(), 0x38, std::uint32_t{0x4744624F});
    Put(interaction_database.data(), c::kDeclarationsInteractionOffset, rule.data());
  }
  game::DeclarableWarSnapshot Selected() const {
    return {kTarget, 0, "religious_war", 0, kActor,
        std::vector<std::int32_t>(titles.begin(), titles.end())};
  }
  bool OwnsCallback() const noexcept {
    return owning_query && c::IsQueryOwningThread(&owning_query->envelope);
  }
};
Fixture *active = nullptr;
void *Player(void *) { return active->player.data(); }
void *CbDatabase() { return active->cb_database.data(); }
void *InteractionDatabase() { return active->interaction_database.data(); }
bool Evaluate(void *type, void *actor, void *target, void *scratch, bool first, bool second, void *context) {
  auto &f = *active;
  ++f.evaluations;
  if (!f.OwnsCallback() || type != f.type.data() || actor != f.actor.data() || target != f.target.data() ||
      scratch != f.scratch.data() || first || second || context) f.bad_arguments = true;
  Put(scratch, 0, f.configuration.data()); Put(scratch, 8, std::int32_t{1}); Put(scratch, 12, std::int32_t{1});
  Put(f.configuration.data(), 0, kActor);
  Array(f.configuration.data() + 8, f.titles.data(), static_cast<std::int32_t>(f.titles.size()));
  return true;
}
void DestroyConfiguration(void *configuration) {
  ++active->configuration_destroys;
  if (!active->OwnsCallback() || configuration != active->configuration.data()) active->bad_arguments = true;
}
void *Construct(void *context, void *interaction, std::int32_t actor, std::int32_t target, void *extra, bool redirect) {
  auto &f = *active;
  ++f.context_constructs;
  if (!f.OwnsCallback() || interaction != f.rule.data() || actor != kActor || target != kTarget || extra || !redirect)
    f.bad_arguments = true;
  Put(context, 0, interaction); Put(context, 0x2D8, actor); Put(context, 0x2DC, target);
  Put(context, c::kDeclarationsAdditionalRoleOffset, f.scenario == 5 ? std::int32_t{-1} : kAdditional);
  auto *war = new War;
  Put(war->bytes.data(), 0, f.declarations.war_declaration_vtable);
  Put(context, c::kDeclarationsSpecialDataOffset, war->bytes.data());
  return context;
}
void Refresh(void *, bool refresh) { ++active->refreshes; if (!active->OwnsCallback() || !refresh) active->bad_arguments = true; }
void Finalize(void *) { ++active->finalizes; if (!active->OwnsCallback()) active->bad_arguments = true; }
bool Validate(void *context, void *reason) {
  auto &f = *active;
  ++f.validations;
  const auto *war = Get<const void *>(context, c::kDeclarationsSpecialDataOffset);
  if (!f.OwnsCallback() || reason || Get<const void *>(war, c::kDeclarationsWarCbOffset) != f.type.data()) f.bad_arguments = true;
  return false; // Legality remains observed independently of this readonly child.
}
void DestroyContext(void *context) {
  ++active->context_destroys;
  if (!active->OwnsCallback()) active->bad_arguments = true;
  auto *war = reinterpret_cast<War *>(Get<void *>(context, c::kDeclarationsSpecialDataOffset));
  delete war; Put(context, c::kDeclarationsSpecialDataOffset, static_cast<void *>(nullptr));
}
void Copy(void *destination, const void *source) {
  auto *war = reinterpret_cast<War *>(static_cast<std::byte *>(destination) - c::kDeclarationsWarTitlesOffset);
  const auto *ids = Get<const std::int32_t *>(source, 0);
  const auto count = Get<std::int32_t>(source, 12);
  if (!active->OwnsCallback() || source != active->configuration.data() + 8) active->bad_arguments = true;
  war->titles.assign(ids, ids + count); war->Sync(); active->actual_native_titles = destination;
}
void Append(void *destination, std::int32_t insertion, const std::int32_t *begin, const std::int32_t *end) {
  auto *war = reinterpret_cast<War *>(static_cast<std::byte *>(destination) - c::kDeclarationsWarTitlesOffset);
  if (!active->OwnsCallback() || insertion != static_cast<std::int32_t>(war->titles.size())) active->bad_arguments = true;
  war->titles.insert(war->titles.end(), begin, end); war->Sync(); active->actual_native_titles = destination;
}
void ScopeConstruct(void *scope) {
  ++active->scope_constructs;
  if (!active->OwnsCallback()) active->bad_arguments = true;
  Put(scope, 0, std::uint64_t{0x168889F60});
}
void ScopePopulate(void *scope, void *additional, void *recipient, void *claimant, const void *titles, std::int32_t extra) {
  auto &f = *active;
  ++f.scope_populates; f.populated_scope = scope;
  if (!f.OwnsCallback() || Get<std::uint64_t>(scope, 0) != 0x168889F60 ||
      additional != (f.scenario == 5 ? f.fallback.data() : f.additional.data()) || recipient != f.target.data() ||
      claimant != f.actor.data() ||
      titles != f.actual_native_titles || extra != 0 || Get<std::int32_t>(titles, 12) != 2) f.bad_arguments = true;
  const auto *ids = Get<const std::int32_t *>(titles, 0);
  if (!ids || ids[0] != f.titles[0] || ids[1] != f.titles[1]) f.bad_arguments = true;
}
void ScopeDestroy(void *scope) {
  ++active->scope_destroys;
  if (!active->OwnsCallback() || scope != active->populated_scope) active->bad_arguments = true;
}
void CostEvaluate(const void *cost, const void *scope, std::int64_t *out) {
  auto &f = *active;
  ++f.cost_evaluations;
  if (!f.OwnsCallback() || cost != f.type.data() + c::kOrdinaryHolyWarCompiledCostOffsetV1 || scope != f.populated_scope || !out)
    f.bad_arguments = true;
  std::memcpy(out, kNonzeroCosts.data(), sizeof(kNonzeroCosts));
}

void *CharacterRite(void *character) {
  auto &f = *active;
  if (!f.OwnsCallback()) f.bad_arguments = true;
  f.last_fervor_character = Get<std::int32_t>(character, 0x18);
  if (character == f.actor.data()) return f.actor_rite.data();
  if (character == f.additional.data()) return f.additional_rite.data();
  if (character == f.target.data()) return f.target_rite.data();
  if (character == f.npc_first.data()) return f.first_rite.data();
  if (character == f.npc_second.data()) return f.second_rite.data();
  f.bad_arguments = true; return nullptr;
}
void *RiteFaith(void *rite) {
  auto &f = *active;
  if (!f.OwnsCallback()) f.bad_arguments = true;
  if (rite == f.actor_rite.data()) return f.actor_faith.data();
  if (rite == f.additional_rite.data()) return f.scenario == 1 ? f.target_faith.data() : f.additional_faith.data();
  if (rite == f.target_rite.data() || rite == f.first_rite.data() || rite == f.second_rite.data()) return f.target_faith.data();
  f.bad_arguments = true; return nullptr;
}
void *CharacterFaith(void *character) { return RiteFaith(CharacterRite(character)); }
std::int64_t *FaithFervor(void *faith, std::int64_t *out) {
  auto &f = *active;
  ++f.fervor_calls;
  if (!f.OwnsCallback() || !out ||
      (faith != f.actor_faith.data() && faith != f.additional_faith.data() && faith != f.target_faith.data())) {
    f.bad_arguments = true; return nullptr;
  }
  // One explicitly synthetic row callback fault; actual Faith identity stays intact.
  if (f.scenario == 4 && f.last_fervor_character == kNpcSecond) return nullptr;
  *out = Get<std::int64_t>(faith, 0x2F8); return out;
}
void CollectDefenders(void *cb, void *attacker, void *defender, h::NativeCharacterVector *out) {
  auto &f = *active;
  ++f.collector_calls;
  if (!f.OwnsCallback() || cb != f.type.data() || attacker != f.additional.data() ||
      defender != f.target.data() || !out || f.scenario == 3 || f.scenario == 5) {
    f.bad_arguments = true; return;
  }
  if (f.scenario == 1 &&
      (Get<const void *>(cb, 0x18A8) != f.same_faith_parameters.data() || Get<std::int32_t>(cb, 0x18B4) != 1))
    f.bad_arguments = true;
  // This is a synthetic engine result, not a Python reconstruction of its rule or score.
  // In particular, the same-Faith case reaches this callback and has no external early return.
  if (f.scenario == 2) return;
  f.allocated_rows = new void *[2]{f.npc_first.data(), f.npc_second.data()};
  out->rows = f.allocated_rows; out->capacity = 2; out->count = 2; out->allocator = f.engine_allocator.data();
}
void FreeDefenderRows(void *allocator, void *rows, std::size_t element_size) {
  auto &f = *active;
  ++f.row_frees;
  if (!f.OwnsCallback() || allocator != f.engine_allocator.data() || rows != f.allocated_rows || element_size != sizeof(void *))
    f.bad_arguments = true;
  delete[] static_cast<void **>(rows); f.allocated_rows = nullptr;
}

void Bind(Fixture &f) {
  active = &f;
  auto &b = f.declarations;
  b.enabled = true; b.core = {true, &f.state_ptr, &f.jomini_ptr, &f.storage_ptr, &Player};
  b.configuration_scratch = f.scratch.data(); b.get_cb_database = &CbDatabase;
  b.get_interaction_database = &InteractionDatabase; b.evaluate_cb = &Evaluate;
  b.destroy_configuration = &DestroyConfiguration; b.construct_context = &Construct;
  b.refresh_context = &Refresh; b.finalize_context = &Finalize; b.validate_context = &Validate;
  b.destroy_context = &DestroyContext; b.copy_int_array = &Copy; b.append_int_array = &Append;
  b.war_declaration_vtable = c::kDeclarationsWarVtableRva;
  // No CommandBindings or send/queue function exists in this read-only path.
  f.cost = {true, &ScopeConstruct, &ScopePopulate, &ScopeDestroy, &CostEvaluate, &f.fallback_ptr};
  constexpr std::uintptr_t base = 0x140000000;
  auto faith = xar::ck3_12004::religion::BindReligionContextImage12004(base, xar::ck3_12004::kExecutableSha256);
  f.defender_join = xar::ck3_12004::religion::holy_war_defender_join::BindHolyWarDefenderJoinInputsImage12004(
      base, xar::ck3_12004::kExecutableSha256, faith);
  Check(f.defender_join.enabled && f.defender_join.faith.core.enabled &&
      reinterpret_cast<std::uintptr_t>(f.defender_join.collector) == base + 0x2C0AA90 &&
      reinterpret_cast<std::uintptr_t>(f.defender_join.engine_allocator) == base + 0x54DEDE0,
      "actual4 factory supplies source-proved collector and caller allocator");
  Check(!xar::ck3_12004::religion::holy_war_defender_join::BindHolyWarDefenderJoinInputsImage12004(
      base, c::kOrdinaryHolyWarExactSha12003, faith).enabled,
      "new factory preserves independent actual4 identity");
  f.defender_join.faith.core = b.core;
  f.defender_join.faith.character_rite = &CharacterRite;
  f.defender_join.faith.rite_faith = &RiteFaith;
  f.defender_join.faith.character_faith = &CharacterFaith;
  f.defender_join.faith.faith_fervor = &FaithFervor;
  f.defender_join.collector = &CollectDefenders;
  f.defender_join.engine_allocator = f.engine_allocator.data();
  f.defender_join.free_rows = &FreeDefenderRows;
}
class FrameAdapter final : public game::GameAdapter {
 public:
  game::Snapshot frame{};
  const DWORD owner = GetCurrentThreadId();
  mutable unsigned reads = 0, commands = 0;
  game::AdapterDescriptor identity{xar::ck3_12004::kAdapterId, xar::ck3_12004::kGameVersion,
      xar::ck3_12004::kExecutableSha256, "holy-war-npc-defender-join-whole-fixture", {}};
  const game::AdapterDescriptor &descriptor() const noexcept override { return identity; }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    if (GetCurrentThreadId() != owner) return false;
    ++reads; out = frame; return true;
  }
  bool submit_set_speed(std::int32_t) const noexcept override { ++commands; return false; }
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override { ++commands; return {}; }
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
  Pump(Fixture &f, api::MainThreadQueryMailboxV1 &mailbox) {
    tls[0x20] = std::byte{1}; tls_context = tls.data();
    mailbox.global_rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&unused_rng);
    mailbox.jomini_state_slot = reinterpret_cast<std::uintptr_t>(&f.jomini_ptr);
    mailbox.game_state_slot = reinterpret_cast<std::uintptr_t>(&f.state_ptr);
    mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter = &FixtureTls;
    mailbox.executor_submission_enabled = true;
    mailbox.permitted_executor_ordinary_holy_war_declaration_context12003 = &c::ExecuteOrdinaryHolyWarDeclarationContextMailbox12003;
    mailbox.iat_hook_installed = true; mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    mailbox.pump_epochs = kCaptureEpoch - 3;
    for (unsigned i = 0; i < 2; ++i)
      (void)api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};
std::string Request(const Fixture &f) {
  const auto selected = f.Selected();
  return "{\"expected_revision\":9,\"expected_snapshot_revision\":9,\"expected_public_revision\":2,"
      "\"declaration_id\":\"67108866-0-0\",\"target_character_id\":67108866,\"casus_belli_index\":0,"
      "\"configuration_index\":0,\"claimant_character_id\":" + std::to_string(selected.claimant_character_id) +
      ",\"casus_belli_key\":\"religious_war\",\"target_title_ids\":[16777378,33554593]}";
}

void Query(Fixture &f, const std::filesystem::path &directory) {
  Bind(f); FrameAdapter adapter;
  c::CoreSnapshotPrefix prefix{};
  Check(c::ReadCoreSnapshot(f.declarations.core, prefix) && prefix.played_character_id == kActor,
      "actual core reads the full played identity independently of additional attacker");
  adapter.frame.paused = prefix.clock.paused; adapter.frame.speed = prefix.clock.speed;
  adapter.frame.map_ready = prefix.map_ready; adapter.frame.player_id = prefix.local_player_id;
  adapter.frame.date_raw = prefix.clock.date_raw; adapter.frame.has_played_character = prefix.has_played_character;
  adapter.frame.played_character_alive = prefix.played_character_alive; adapter.frame.played_character_id = prefix.played_character_id;
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(f, mailbox);
  c::OrdinaryHolyWarDeclarationContextMailbox12003 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame; query.envelope.expected_snapshot_revision = kNativeRevision;
  Check(c::ParseOrdinaryHolyWarDeclarationContextRequest12003(Request(f), query.request) &&
      query.request.expected_revision == kNativeRevision && query.request.expected_public_revision == kPublicRevision &&
      query.request.selected == f.Selected(), "production parser retains the explicit selected declaration and revisions");
  query.declarations = f.declarations; query.cost = f.cost; query.defender_join = f.defender_join;
  f.owning_query = &query;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
  std::string wire, failure;
  std::thread worker([&] {
    result = c::RunOrdinaryHolyWarDeclarationContextMailbox12003(query, kRequestIds[f.scenario], wire, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(9);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (!drained && mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Check(result && drained && failure.empty() && query.completed && query.envelope.frame_stable && !wire.empty(),
      "actual selected reader owner submit drain wait reclaim and whole serializer");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle && mailbox.executed_requests == 1 &&
      query.envelope.execution_stamp.pump_epoch == kCaptureEpoch && adapter.reads == 2,
      "one owner transaction and the genuine mailbox execution stamp");
  const auto &old = query.observation;
  const auto &child = query.defender_join_observation;
  Check(old.available && old.selected == f.Selected() && old.context_actor_character_id == kActor &&
      old.context_recipient_character_id == kTarget && old.context_claimant_character_id == kActor &&
      old.final_can_send.has_value() && !*old.final_can_send && old.cb_cost.available &&
      old.cb_cost.resource_costs_raw == kNonzeroCosts,
      "old finalized context final false and signed CB vector remain independent observations");
  Check(old.context_additional_role_character_id == (f.scenario == 5 ? std::int32_t{-1} : kAdditional) &&
      old.additional_role_uses_native_fallback == (f.scenario == 5) && !old.recipient_uses_native_fallback &&
      !old.claimant_uses_native_fallback, "raw finalized additional role and native fallback are not replaced by played ID");
  Check(child.capture_epoch == old.capture_epoch && child.capture_epoch == kCaptureEpoch &&
      child.native_revision == kNativeRevision && child.public_revision == kPublicRevision &&
      child.date_raw == kDate && child.played_character_id == kActor && child.declaration_id == old.declaration_id &&
      child.selected == old.selected, "new sibling joins exactly the existing frame and selected declaration");
  Check(f.evaluations == 1 && f.configuration_destroys == 1 && f.context_constructs == 1 && f.context_destroys == 1 &&
      f.refreshes == 1 && f.finalizes == 1 && f.validations == 1 && f.scope_constructs == 1 &&
      f.scope_populates == 1 && f.scope_destroys == 1 && f.cost_evaluations == 1,
      "one existing native context and actual CB evaluation, with their genuine cleanup");
  if (f.scenario == 5) {
    Check(!child.available && child.failure == h::Failure::native_role_fallback &&
        !child.native_joiner_set_observed && child.joiners.empty() && f.collector_calls == 0 && f.row_frees == 0,
        "native role fallback disables only new child and never invents an attacker or joins");
  } else {
    Check(child.available && child.failure == h::Failure::none && child.native_joiner_set_observed &&
        child.primary_attacker_character_id == static_cast<std::uint32_t>(kAdditional) &&
        child.primary_defender_character_id == static_cast<std::uint32_t>(kTarget) &&
        child.primary_defender_faith_available && child.primary_defender_rite_id == kTargetRite &&
        child.primary_defender_faith_id == kTargetFaith,
        "complete observed native set uses actual additional attacker and actual recipient Faith");
    if (f.scenario == 2 || f.scenario == 3) {
      Check(child.joiners.empty() && child.defender_faith_can_join == (f.scenario != 3) &&
          f.collector_calls == (f.scenario == 2 ? 1U : 0U) && f.row_frees == 0,
          "native evaluated empty and CB-disabled empty are distinct successful observations");
    } else {
      Check(child.joiners.size() == 2 && f.collector_calls == 1 && f.row_frees == 1 && !f.allocated_rows,
          "collector invoked once and actual ordered pointer vector freed once");
      const auto &first = child.joiners[0], &second = child.joiners[1];
      Check(first.character_id == static_cast<std::uint32_t>(kNpcFirst) &&
          second.character_id == static_cast<std::uint32_t>(kNpcSecond) && first.rite_id == kFirstRite &&
          second.rite_id == kSecondRite && first.faith_id == kTargetFaith && second.faith_id == kTargetFaith &&
          first.row_faith_available && second.row_faith_available && first.matches_primary_defender_faith == true &&
          second.matches_primary_defender_faith == true,
          "unsorted native NPC order full generations Rite identities and defender Faith domain survive");
      const auto expected = f.scenario == 1 ? std::int64_t{0} : std::int64_t{7500000};
      Check(first.row_fervor_available && first.faith_fervor_raw == expected && first.failure == h::FaithFailure::none,
          "actual joiner Faith receiver yields signed Q100000, including legal zero");
      if (f.scenario == 4) {
        Check(!second.row_fervor_available && !second.faith_fervor_raw && second.failure == h::FaithFailure::fervor_unavailable,
            "one row getter failure preserves complete native set and both NPC/Faith identities");
      } else {
        Check(second.row_fervor_available && second.faith_fervor_raw == expected && second.failure == h::FaithFailure::none,
            "both NPCs in the same actual Faith observe the same current fervor");
      }
      if (f.scenario == 1) {
        Check(Get<std::uint32_t>(f.additional_rite.data(), 0x4B8) == kTargetFaith && kAdditionalRite != kTargetRite,
            "same-Faith different-Rite additional attacker still reaches native collector under loaded CB parameter");
      }
    }
  }
  Check(!f.bad_arguments && f.commands == 0 && adapter.commands == 0 && !f.declarations.commands.enabled &&
      !f.declarations.construct_send, "all callbacks run in actual owner context and no gameplay command path exists");
  Check(wire.find("\"player_ordinary_holy_war_declaration_context\":" +
      game::Render12004BuildIdentity(c::SerializeOrdinaryHolyWarDeclarationContextV1(old), adapter.descriptor())) != std::string::npos &&
      wire.find("\"player_holy_war_defender_join_inputs\":" + game::Render12004BuildIdentity(h::SerializeHolyWarDefenderJoinInputs12003(child), adapter.descriptor())) != std::string::npos &&
      wire.find("\"status\":\"observed\"") != std::string::npos,
      "complete existing command_result serializer includes actual child without changing old top status");
  Check(wire.find("\"game_version\":\"1.20.0.4\"") != std::string::npos &&
      wire.find(xar::ck3_12004::kExecutableSha256) != std::string::npos, "production actual4 whole identity rendering");
  std::ofstream file(directory / kWireFiles[f.scenario], std::ios::binary);
  Check(static_cast<bool>(file), "open new compiled whole wire output");
  file << wire << '\n'; Check(static_cast<bool>(file), "write untouched compiled production packet");
  f.owning_query = nullptr;
}
void Receipt(const std::filesystem::path &directory) {
  std::ofstream out(directory / "producer-receipt.json", std::ios::binary);
  Check(static_cast<bool>(out), "open compiled new producer receipt");
  out << "{\"schema\":\"xar.ck3.holy-war-npc-defender-join-native-whole-fixture/v1\","
      "\"status\":\"GREEN\",\"cases\":6,\"whole_wire_files\":[";
  for (std::size_t i = 0; i < kWireFiles.size(); ++i) { if (i) out << ','; out << '"' << kWireFiles[i] << '"'; }
  out << "],\"frame\":{\"public_revision\":2,\"native_revision\":9,\"capture_epoch\":991,"
      "\"date_raw\":53222304,\"played_character_id\":50331649,\"paused\":true,\"map_ready\":true},"
      "\"exact_build\":{\"game_version\":\"1.20.0.4\",\"executable_sha256\":\""
      << xar::ck3_12004::kExecutableSha256 << "\"},\"provenance\":{\"native_memory\":\"fixture-synthetic\","
      "\"native_callbacks\":\"fixture-synthetic\",\"source_frame\":\"fixture-synthetic\","
      "\"public_revision\":\"fixture-synthetic\",\"capture_epoch\":\"fixture-synthetic\","
      "\"whole_wires\":\"compiled-production-serializer\",\"whole_wire_rows_repaired\":false},"
      "\"pipeline\":{\"actual_request_parser\":true,\"actual_named_mailbox\":true,\"actual_core_reader\":true,"
      "\"actual_selected_context_reader\":true,\"actual_cb_cost_reader\":true,\"actual_defender_join_reader\":true,"
      "\"actual_full_serializer\":true,\"actual12004_renderer\":true,\"offline_native_image_handler_invoked\":false,"
      "\"live\":false},\"counts\":{\"selected_contexts\":6,\"cb_cost_evaluations\":6,"
      "\"native_collector_calls\":4,\"native_vector_frees\":3,\"synthetic_row_fervor_faults\":1,"
      "\"gameplay_commands\":0},\"checks\":" << checks << "}\n";
  Check(static_cast<bool>(out), "write actual compiled assertion receipt");
}
} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "one fresh existing output directory argument required");
    const std::filesystem::path directory(argv[1]);
    Check(std::filesystem::is_directory(directory), "Root prepares the new first fixture output directory");
    for (std::size_t i = 0; i < kWireFiles.size(); ++i) { Fixture f(i); Query(f, directory); }
    Receipt(directory);
    std::cout << "GREEN cases=6 checks=" << checks
        << " actual_named_mailbox=true actual_selected_context=true actual_defender_join=true actual_full_serializer=true"
           " synthetic_native_memory=true gameplay_commands=0 live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "RED " << error.what() << '\n'; return 1; }
}
