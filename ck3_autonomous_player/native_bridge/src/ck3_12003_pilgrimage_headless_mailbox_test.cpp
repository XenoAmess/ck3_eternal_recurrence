// Synthetic native-memory callbacks; one focused production mailbox and renderer case.
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
  Bytes<0x900> faith{};
  Bytes<0x40> religion{};
  Bytes<0x50> religion_definition{};
  Bytes<0xB0> extension{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  static constexpr std::int32_t character_id = 0x03000004;
  static constexpr std::uint32_t faith_id = 0x83000003, religion_id = 0x84000005;
  std::int64_t fallback_value = 7654321;
  int fallback_calls = 0, fervor_calls = 0;
  bool bad_faith = false, missing_rite = false, bad_fervor = false, drift = false;
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
      xar::ck3_12003::kExecutableSha256, "synthetic-pilgrimage-headless-mailbox", {}};
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


} // namespace

// Production renderer remains real. These unused game image/adapter routes
// cannot be reached by this external native-memory fixture.
#if defined(XAR_PILGRIMAGE_COMBINED_STANDALONE_RENDERER)
namespace xar::game {
Ck3_12002AdapterBindings BindCk3_12002AdapterImage(std::uintptr_t, std::string_view) noexcept { std::abort(); }
const AdapterDescriptor &Ck3_12002AdapterDescriptor() noexcept { std::abort(); }
std::unique_ptr<GameAdapter> CreateCk3_12003AdapterFromBindings(Ck3_12003AdapterBindings) noexcept { std::abort(); }
} // namespace xar::game
#endif


#include "xar_bridge/ck3_12003_pilgrimage_activity_terms.hpp"

#include <algorithm>
#include <map>
#include <memory>

namespace {
namespace factory = xar::ck3_12003::religion::pilgrimage_candidate_factory;
namespace quote = xar::ck3_12003::religion::pilgrimage_activity_terms;

template <class T> void Store(void *object, std::size_t at, T value) {
  std::memcpy(static_cast<std::byte *>(object) + at, &value, sizeof(value));
}
struct ScopeState {
  std::int32_t actor = -1, location = -1;
  bool host = false, special = false;
};
struct ConfigState {
  std::byte *phases = nullptr, *options = nullptr, *defaults = nullptr;
  std::vector<std::byte *> children;
  bool inserted = false, normalized = false;
};
struct PilgrimageFixture : Fixture {
  Bytes<0x3C00> activity_type{};
  Bytes<0x60> activity_database{};
  void *activity_database_pointer = activity_database.data();
  std::array<const void *, 1> activity_types{activity_type.data()};
  std::array<const void *, 1> ordinary_phases{offered_phase.data()};
  std::string activity_key = "activity_pilgrimage";
  static constexpr std::uintptr_t type_vtable = 0x44440000;
  Bytes<0x860> rejected_province{}, legal_province{};
  std::array<void *, 3> province_rows{nullptr, rejected_province.data(), legal_province.data()};
  Bytes<0xC0> holy_rejected{}, holy_legal{};
  Bytes<0x100> title_rejected{}, title_legal{};
  Bytes<0x30> holy_storage{}, title_storage{};
  Bytes<0x30> holy_slots{}, title_slots{};
  void *holy_storage_pointer = holy_storage.data(), *title_storage_pointer = title_storage.data();
  static constexpr std::uint32_t rejected_holy_id = 0x83000001U, legal_holy_id = 0x83000002U;
  static constexpr std::uint32_t rejected_title_id = 0x84000001U, legal_title_id = 0x84000002U;
  std::array<std::uint32_t, 2> faith_holy_ids{rejected_holy_id, legal_holy_id};
  Bytes<0x700> initial_phase{}, offered_phase{}, child_phase{};
  Bytes<0x80> pomp_category{}, other_category{}, pomp_option{}, other_option{};
  Bytes<0x18> allocator_vtable{};
  Bytes<8> province_allocator{}, phase_allocator{};
  const std::int32_t host_token = 101, special_token = 102, location_token = 103;
  std::map<void *, ScopeState> scopes;
  std::map<void *, std::string> evaluators;
  std::map<void *, ConfigState> configs;
  int filter_calls = 0, phase_offer_calls = 0, same_cap_calls = 0, total_cap_calls = 0;
  int root_constructs = 0, root_destroys = 0, evaluator_constructs = 0, evaluator_destroys = 0;
  int array_releases = 0, reason_destroys = 0, native_config_initializes = 0;
  int native_config_destroys = 0, native_phase_inserts = 0, native_normalizes = 0;
  int native_cost_calls = 0, native_afford_calls = 0;
  const DWORD callback_owner = GetCurrentThreadId();
  std::string rejected_reason = std::string("Native holy site \"refused\" \xe6\x8b\x92\xe7\xbb\x9d\n\t") + char(1) + std::string(" tail\0end", 9);
  std::string afford_reason = std::string("Native gold \xe4\xb8\x8d\xe8\xb6\xb3\n") + char(2) + std::string(" keep\0tail", 10);
  const std::array<std::int64_t, 10> costs{125000, -700000, 0, 1234567890123LL, -900000000000LL, 5, 6, 7, 8, -12345};

  PilgrimageFixture() {
    Put(activity_type, 0, type_vtable);
    Tag(activity_type, 0x18, activity_key);
    Put(activity_type, 0x3BC0, std::int32_t{5});
    Put(activity_type, 0x980, ordinary_phases.data()); Put(activity_type, 0x98C, std::int32_t{1});
    activity_type[0x3BED] = std::byte{1};
    Put(activity_database, 0x50, activity_types.data());
    Put(activity_database, 0x5C, std::int32_t{1});
    Put(faith, 0x890, faith_holy_ids.data());
    Put(faith, 0x89C, std::int32_t{2});
    Put(holy_rejected, 0x10, rejected_holy_id); Put(holy_rejected, 0xB0, rejected_title_id);
    Put(holy_legal, 0x10, legal_holy_id); Put(holy_legal, 0xB0, legal_title_id);
    Put(title_rejected, 0x10, rejected_title_id); Put(title_legal, 0x10, legal_title_id);
    Put(holy_storage, 0x20, holy_slots.data()); Put(holy_storage, 0x2C, std::int32_t{3});
    Put(title_storage, 0x20, title_slots.data()); Put(title_storage, 0x2C, std::int32_t{3});
    Put(holy_slots, 0x18, holy_rejected.data()); Put(holy_slots, 0x28, holy_legal.data());
    Put(title_slots, 0x18, title_rejected.data()); Put(title_slots, 0x28, title_legal.data());
    Put(rejected_province, 0x10, std::int32_t{1}); Put(legal_province, 0x10, std::int32_t{2});
    Put(rejected_province, 0x85C, std::uint32_t{0x50726F76U}); Put(legal_province, 0x85C, std::uint32_t{0x50726F76U});
    Put(data, c::kObjectiveProvinceArrayOffset, province_rows.data());
    Put(data, c::kObjectiveProvinceCountOffset, std::int32_t{3});
    Put(initial_phase, 8, std::int32_t{11}); Put(initial_phase, 0x698, std::int32_t{20}); initial_phase[0x69C] = std::byte{1};
    Put(offered_phase, 8, std::int32_t{12}); Put(offered_phase, 0x698, std::int32_t{10});
    Put(child_phase, 8, std::int32_t{13}); Put(child_phase, 0x698, std::int32_t{30}); child_phase[0x69C] = std::byte{1};
    Put(pomp_category, 8, std::int32_t{5}); Put(other_category, 8, std::int32_t{6});
    Put(pomp_option, 8, std::int32_t{21}); Put(other_option, 8, std::int32_t{22});
    Put(province_allocator, 0, allocator_vtable.data()); Put(phase_allocator, 0, allocator_vtable.data());
  }
};
PilgrimageFixture *p = nullptr;

void NativeString(void *sink, std::string_view text) {
  const auto size = static_cast<std::uint64_t>(text.size());
  if (size < 16) {
    std::memcpy(sink, text.data(), text.size());
    Store(sink, 0x10, size); Store(sink, 0x18, std::uint64_t{15});
  } else {
    auto *bytes = new char[text.size() + 1];
    std::memcpy(bytes, text.data(), text.size()); bytes[text.size()] = '\0';
    Store(sink, 0, bytes); Store(sink, 0x10, size); Store(sink, 0x18, size);
  }
}
void DestroyReason(void *sink) {
  ++p->reason_destroys;
  if (Get<std::uint64_t>(sink, 0x18) >= 16) delete[] Get<char *>(sink, 0);
}
void ReleaseNativeArray(const void *allocator, void *data, std::size_t alignment) {
  Check((allocator == p->province_allocator.data() || allocator == p->phase_allocator.data()) && alignment == 8,
      "production owned array uses its genuine native allocator release slot");
  ++p->array_releases; delete[] static_cast<std::byte *>(data);
}
void FilterProvinces(const void *filter, void *actor, factory::NativeArray *out) {
  Check(GetCurrentThreadId() == p->callback_owner, "factory callback remains on genuine mailbox owner");
  Check(filter == p->activity_type.data() + 0x3BC0 && actor == p->character.data(),
      "native filter receives actual pilgrimage filter/player");
  auto *rite = CharacterRite(actor);
  auto *faith = RiteFaith(rite);
  Check(rite == p->rite.data() && faith == p->faith.data(), "native provider discovers candidates from actual actor Rite/Faith");
  const auto count = Get<std::int32_t>(faith, 0x89C);
  const auto *ids = Get<const std::uint32_t *>(faith, 0x890);
  auto *bytes = new std::byte[static_cast<std::size_t>(count) * sizeof(void *)];
  for (std::int32_t index = 0; index < count; ++index) {
    const auto full_id = ids[index];
    const auto *holy = Get<const void *>(p->holy_slots.data(), (full_id & 0xFFFFFFU) * 0x10 + 8);
    Check(Get<std::uint32_t>(holy, 0x10) == full_id, "native provider retains real Faith HolySite full identity");
    const auto title_id = Get<std::uint32_t>(holy, 0xB0);
    const auto *title = Get<const void *>(p->title_slots.data(), (title_id & 0xFFFFFFU) * 0x10 + 8);
    Check(Get<std::uint32_t>(title, 0x10) == title_id, "native provider uses HolySite's native Title full identity");
    const auto province = p->province_rows[static_cast<std::size_t>(title_id & 0xFFFFFFU)];
    Store(bytes, static_cast<std::size_t>(index) * sizeof(void *), province);
  }
  out->data = bytes; out->capacity = out->count = count; ++p->filter_calls;
}
void *RootConstruct(void *scope) { ++p->root_constructs; p->scopes[scope] = {}; return scope; }
void *ActorRootConstruct(void *scope, const std::int32_t *id) {
  Check(*id == Fixture::character_id, "actual actor root keeps full played reference");
  RootConstruct(scope); p->scopes[scope].actor = *id;
  Store(scope, 0, std::int32_t{4}); Store(scope, 8, static_cast<std::uint64_t>(*id)); return scope;
}
void RootDestroy(void *scope) { Check(p->scopes.erase(scope) == 1, "native scope destroyed once"); ++p->root_destroys; }
void NamedScopeSave(void *named, std::int32_t token, const factory::ScopeToken *value) {
  auto *scope = static_cast<std::byte *>(named) - 0x18;
  auto &state = p->scopes.at(scope);
  if (token == p->host_token) { Check(value->kind == 4 && value->payload == Fixture::character_id, "province selection scope has actual host"); state.actor = Fixture::character_id; state.host = true; }
  else if (token == p->special_token) { Check(value->kind == 3 && value->payload == 21, "selection scope uses native selected special definition index"); state.special = true; }
  else { Check(token == p->location_token && value->kind == 8, "location named scope uses native Province kind"); state.location = static_cast<std::int32_t>(value->payload); }
}
bool PredicateValue(const void *definition, void *scope, std::string &reason) {
  const auto &state = p->scopes.at(scope);
  Check(state.actor == Fixture::character_id && state.special, "actual selection scope retains full actor and selected special");
  if (definition == p->activity_type.data() + 0x450) {
    Check(state.host && Get<std::int32_t>(scope, 0) == 8, "candidate location predicate uses Province root plus named host");
    const auto province = Get<std::uint64_t>(scope, 8);
    if (province == 1) { reason = p->rejected_reason; return false; }
    Check(province == 2, "candidate native root is actual legal Province"); reason.clear(); return true;
  }
  Check(definition == p->offered_phase.data() + 0x10 || definition == p->offered_phase.data() + 0xE0,
      "phase choices execute genuine shown and location predicates independently");
  if (definition == p->offered_phase.data() + 0xE0) Check(state.location == 1 || state.location == 2, "phase location carries named actual candidate Province");
  reason.clear(); return true;
}
bool Predicate(const void *definition, void *scope) { std::string reason; return PredicateValue(definition, scope, reason); }
bool PredicateWithEvaluator(const void *definition, void *scope, void *evaluator) {
  return PredicateValue(definition, scope, p->evaluators.at(evaluator));
}
void *Allocate(std::size_t size) { Check(size == 0xD8, "actual evaluator allocation size"); return new std::byte[size]{}; }
void Deallocate(void *bytes, std::size_t size) { Check(size == 0xD8, "actual evaluator deallocation size"); delete[] static_cast<std::byte *>(bytes); }
void *EvaluatorConstruct(void *bytes) { ++p->evaluator_constructs; p->evaluators[bytes] = {}; return bytes; }
void EvaluatorPrepare(void *bytes) { Check(p->evaluators.contains(bytes) && Get<std::uint8_t>(bytes, 0xD0) == 0, "native evaluator prepares before formatter ready flag"); }
void EvaluatorFormat(void **evaluator, const void *parameters, void *sink) {
  const auto *bytes = static_cast<const std::byte *>(parameters);
  Check(bytes[0] == std::byte{2} && bytes[1] == std::byte{2} && bytes[2] == std::byte{0} &&
      Get<void *>(parameters, 8) == sink && Get<void *>(parameters, 0x10) == *evaluator && Get<std::uint8_t>(*evaluator, 0xD0) == 1,
      "actual native reason parameter modes/pointers survive evaluator lifecycle");
  NativeString(sink, p->evaluators.at(*evaluator));
}
void EvaluatorDestroy(void *bytes) { Check(p->evaluators.erase(bytes) == 1, "actual evaluator destroyed once"); ++p->evaluator_destroys; }
std::int32_t TotalPhaseCap(const void *type, void *scope) {
  Check(type == p->activity_type.data() && p->scopes.at(scope).actor == Fixture::character_id, "total cap uses actual actor scope");
  ++p->total_cap_calls; return 1;
}
std::int32_t SameProvinceCap(const void *type, void *scope) {
  Check(type == p->activity_type.data() && p->scopes.at(scope).actor == Fixture::character_id, "same Province cap uses actual actor scope");
  ++p->same_cap_calls; return 2;
}
void PhaseOffers(const factory::PhaseContext *context, std::int32_t mode, const void *province, factory::NativeArray *out) {
  Check(context->activity_type == p->activity_type.data() && context->actual_actor == p->character.data() &&
      context->selected_special == p->pomp_option.data() && mode == 1 && (province == p->rejected_province.data() || province == p->legal_province.data()),
      "native mode1 phasechildren provider receives actual player/type/special/Province");
  auto *row = new std::byte[0x18]{};
  Store(row, 0, p->offered_phase.data()); Store(row, 8, province); Store(row, 0x10, std::int32_t{-17});
  out->data = row; out->capacity = out->count = 1; ++p->phase_offer_calls;
}

void AddOwnedChild(ConfigState &state, std::byte *row) {
  auto *owned = new std::byte[0x28]{};
  state.children.push_back(owned);
  Store(row, 0x18, owned); Store(row, 0x20, std::int32_t{1}); Store(row, 0x24, std::int32_t{1});
}
void *ConfigInitialize(void *config, const void *type, std::int32_t actor) {
  Check(type == p->activity_type.data() && actor == Fixture::character_id && !p->configs.contains(config),
      "native constructor initializes a fresh owned config for the actual player/type");
  ConfigState state;
  state.phases = new std::byte[3 * 0x38]{};
  state.options = new std::byte[2 * 0x10]{};
  state.defaults = new std::byte[0x10]{};
  Store(config, 0, type); Store(config, 8, actor); Store(config, 0x20, Get<std::int32_t>(p->state.data(), 8));
  Store(config, 0x98, state.options); Store(config, 0xA0, std::int32_t{2}); Store(config, 0xA4, std::int32_t{2});
  Store(state.options, 0, p->pomp_category.data()); Store(state.options, 8, p->pomp_option.data());
  Store(state.options, 0x10, p->other_category.data()); Store(state.options, 0x18, p->other_option.data());
  Store(config, 0xB0, state.phases); Store(config, 0xB8, std::int32_t{3}); Store(config, 0xBC, std::int32_t{1});
  Store(state.phases, 0, p->initial_phase.data()); Store(state.phases, 8, std::int32_t{2});
  AddOwnedChild(state, state.phases);
  Store(config, 0x1B0, state.defaults); Store(config, 0x1B8, std::int32_t{1}); Store(config, 0x1BC, std::int32_t{1});
  Store(state.defaults, 0, p->initial_phase.data()); Store(state.defaults, 8, p->legal_province.data());
  Store(config, 0x520, std::uint8_t{0});
  p->configs.emplace(config, std::move(state)); ++p->native_config_initializes;
  return config;
}
const void *SelectedSpecial(const void *config) {
  Check(Get<const void *>(config, 0) == p->activity_type.data() && Get<std::int32_t>(config, 8) == Fixture::character_id,
      "selected special is read from the fresh actual actor config");
  const auto *options = Get<const std::byte *>(config, 0x98);
  Check(Get<std::int32_t>(config, 0xA4) == 2 && Get<const void *>(options, 0) == p->pomp_category.data(),
      "native selected-special getter resolves initialized default option rows");
  return Get<const void *>(options, 8);
}
void *PhaseInsert(void *array, std::int32_t index, const void *type) {
  auto *config = static_cast<std::byte *>(array) - 0xB0;
  auto &state = p->configs.at(config);
  Check(type == p->activity_type.data() && index == 0 && !state.inserted && !state.normalized &&
      Get<std::int32_t>(array, 0xC) == 1,
      "actual production native-order block inserts before default phase above ordinary threshold");
  std::memmove(state.phases + 0x38, state.phases, 0x38);
  std::memset(state.phases, 0, 0x38);
  AddOwnedChild(state, state.phases);
  Store(array, 0xC, std::int32_t{2}); state.inserted = true; ++p->native_phase_inserts;
  return state.phases;
}
void ConfigNormalize(void *config) {
  auto &state = p->configs.at(config);
  Check(state.inserted && !state.normalized && Get<const void *>(state.phases, 0) == p->offered_phase.data() &&
      Get<std::int32_t>(state.phases, 8) == 2 && Get<const void *>(state.phases, 0x38) == p->initial_phase.data(),
      "native normalization receives real factory offer and configured Province after ordered insertion");
  auto *child = state.phases + 2 * 0x38;
  Store(child, 0, p->child_phase.data()); Store(child, 8, std::int32_t{2});
  AddOwnedChild(state, child);
  Store(config, 0xBC, std::int32_t{3});
  state.normalized = true; ++p->native_normalizes;
}
void ActivityCost(const void *config, std::int64_t *out) {
  const auto &state = p->configs.at(const_cast<void *>(config));
  Check(state.normalized && Get<std::int32_t>(config, 0xBC) == 3 && Get<std::uint8_t>(config, 0x520) == 0,
      "native ten-slot quote runs only after full local phase/default normalization, without journey data");
  Check(Get<const void *>(state.phases, 0) == p->offered_phase.data() &&
      Get<const void *>(state.phases, 0x38) == p->initial_phase.data() &&
      Get<const void *>(state.phases, 0x70) == p->child_phase.data(),
      "native quote sees ordered selected/default/native child configured phases");
  std::copy(p->costs.begin(), p->costs.end(), out); ++p->native_cost_calls;
}
bool ActivityAffordable(const std::int64_t *costs, void *actor, void *sink) {
  Check(actor == p->character.data() && std::equal(p->costs.begin(), p->costs.end(), costs),
      "native affordability evaluates genuine complete quote and actual actor independently");
  NativeString(sink, p->afford_reason); ++p->native_afford_calls; return false;
}
void ConfigDestroy(void *config) {
  auto &state = p->configs.at(config);
  for (auto *child : state.children) delete[] child;
  delete[] state.phases; delete[] state.options; delete[] state.defaults;
  p->configs.erase(config); ++p->native_config_destroys;
}
quote::Bindings BindQuote(PilgrimageFixture &fixture) {
  p = &fixture;
  using Release = void (*)(const void *, void *, std::size_t);
  Put(p->allocator_vtable, 0x10, static_cast<Release>(&ReleaseNativeArray));
  quote::Bindings b{}; b.enabled = true; b.activity_type.enabled = true;
  b.activity_type.activity_type_database = &p->activity_database_pointer;
  b.activity_type.activity_type_vtable = PilgrimageFixture::type_vtable;
  auto &candidate = b.candidates;
  candidate.enabled = true; candidate.provinces.enabled = true;
  candidate.provinces.game_state_slot = &p->state_ptr;
  candidate.character_rite = &CharacterRite; candidate.rite_faith = &RiteFaith;
  candidate.holy_site_storage = &p->holy_storage_pointer; candidate.title_storage = &p->title_storage_pointer;
  candidate.province_array_allocator = p->province_allocator.data(); candidate.phase_choice_allocator = p->phase_allocator.data();
  candidate.filter_provinces = &FilterProvinces; candidate.root_construct = &RootConstruct;
  candidate.actor_root_construct = &ActorRootConstruct; candidate.root_destroy = &RootDestroy;
  candidate.named_scope_save = &NamedScopeSave; candidate.host_token = &p->host_token;
  candidate.special_token = &p->special_token; candidate.location_token = &p->location_token;
  candidate.predicate = &Predicate; candidate.predicate_with_evaluator = &PredicateWithEvaluator;
  candidate.allocate = &Allocate; candidate.deallocate = &Deallocate;
  candidate.evaluator_construct = &EvaluatorConstruct; candidate.evaluator_prepare_first = &EvaluatorPrepare;
  candidate.evaluator_prepare_second = &EvaluatorPrepare; candidate.evaluator_format = &EvaluatorFormat;
  candidate.evaluator_destroy = &EvaluatorDestroy; candidate.reason_destroy = &DestroyReason;
  candidate.total_phase_cap = &TotalPhaseCap; candidate.same_province_phase_cap = &SameProvinceCap;
  candidate.phase_offers = &PhaseOffers;
  b.config_initialize = &ConfigInitialize; b.selected_special = &SelectedSpecial; b.phase_insert = &PhaseInsert;
  b.config_normalize = &ConfigNormalize; b.activity_cost = &ActivityCost; b.activity_affordable = &ActivityAffordable;
  b.config_destroy = &ConfigDestroy; b.reason_destroy = &DestroyReason;
  return b;
}

namespace route_fixture {
namespace route = xar::ck3_12003::religion::pilgrimage_route;
constexpr std::uint64_t kDefaultDate = 0xFFFF0000FFFFFFFFULL;
Bytes<8> participant_allocator{}, option_allocator{}, descriptor_allocator{};
const void *seen_input = nullptr;
void *seen_data = nullptr;
std::int32_t *input_ids = nullptr, *data_ids = nullptr;
std::int32_t current_candidate = -1;
int ids_initialized = 0, waypoints_initialized = 0, root_initialized = 0;
int ids_appended = 0, data_constructed = 0, start_resolved = 0;
int route_evaluated = 0, eta_evaluated = 0, data_destroyed = 0, input_destroyed = 0;

void Owner() { Check(GetCurrentThreadId() == p->callback_owner, "route callback remains on genuine mailbox owner"); }
void *InitializeIds(void *array) {
  Owner(); ++ids_initialized;
  Check(Get<void *>(array, 0) == nullptr && Get<std::uint64_t>(array, 8) == 0,
      "candidate route IDs begin in canonical empty owned storage");
  Store<void *>(array, 0x10, static_cast<std::byte *>(array) + 0x18); return array;
}
void *InitializeWaypoints(void *array) {
  Owner(); ++waypoints_initialized;
  Check(Get<void *>(array, 0) == nullptr && Get<std::uint64_t>(array, 8) == 0,
      "candidate route waypoints begin in canonical empty owned storage");
  Store<void *>(array, 0x10, static_cast<std::byte *>(array) + 0x18); return array;
}
void *ConstructRoot(void *scope) {
  Owner(); ++root_initialized; Store(scope, 0, new std::uint64_t(0x12345678)); return scope;
}
void AppendIds(void *array, std::int32_t index, const std::int32_t *begin, const std::int32_t *end) {
  Owner(); ++ids_appended;
  Check(index == 0 && end == begin + 1 && *begin == ids_appended && (*begin == 1 || *begin == 2),
      "mailbox route list uses each actual factory candidate once in native order");
  current_candidate = *begin;
  input_ids = new std::int32_t[1]{*begin};
  Store(array, 0, input_ids); Store(array, 8, std::int32_t{1}); Store(array, 12, std::int32_t{1});
}
void *ConstructData(void *data, const void *input) {
  Owner(); ++data_constructed; seen_input = input; seen_data = data;
  Check(reinterpret_cast<std::uintptr_t>(data) % 16 == 0 && reinterpret_cast<std::uintptr_t>(input) % 16 == 0,
      "route native owned data and input are aligned");
  Check(Get<std::int32_t>(input, 0) == Fixture::character_id && Get<std::int32_t>(input, 4) == -1,
      "route creation owner is same actual played full reference");
  Check(Get<const void *>(input, 0x18) == participant_allocator.data() &&
      Get<const void *>(input, 0xB8) == option_allocator.data() && Get<const void *>(input, 0xD0) == descriptor_allocator.data(),
      "route receives native allocator objects");
  Check(Get<const std::int32_t *>(input, 0x20) == input_ids && Get<std::int32_t>(input, 0x2C) == 1,
      "route data constructor receives exact candidate vector");
  Check(Get<std::uint64_t>(input, 0xA8) == 0 && Get<std::uint64_t>(input, 0xB0) == 0,
      "route retains native default travel options");
  Check(Get<std::int32_t>(input, 0xD8) == -1 && Get<std::uint64_t>(input, 0xDC) == kDefaultDate &&
      Get<std::int32_t>(input, 0xE4) == -1 && Get<std::int32_t>(input, 0xE8) == -1,
      "route defaults retain native Date and start fields");
  for (const auto offset : {0xF0U, 0x110U, 0x140U, 0x160U, 0x190U, 0x1B0U})
    Check(Get<std::uint64_t>(input, offset + 0x10) == 0 && Get<std::uint64_t>(input, offset + 0x18) == 15 &&
        Get<std::uint8_t>(input, offset) == 0, "route native strings begin empty SSO");
  Check(Get<std::int32_t>(input, 0x348) == 3 && Get<std::int32_t>(input, 0x34C) == -1 &&
      Get<std::uint16_t>(input, 0x350) == 0 && Get<std::uint8_t>(input, 0x352) == 1 && Get<std::int32_t>(input, 0x354) == -1,
      "route exact creation defaults are passed to native constructor");
  std::memcpy(static_cast<std::byte *>(data) + 8, input, route::kCreationInputBytes);
  data_ids = new std::int32_t[1]{input_ids[0]}; Store(data, 0x28, data_ids);
  Store<void *>(data, 0x38, static_cast<std::byte *>(data) + 0x40);
  Store<void *>(data, 0x68, static_cast<std::byte *>(data) + 0x70);
  Store(data, 0x1E8, new std::uint64_t(*Get<const std::uint64_t *>(input, 0x1E0)));
  auto *destination = new std::byte[0x48]{};
  Store<const void *>(destination, 8, p->province_rows.at(static_cast<std::size_t>(current_candidate)));
  Store(destination, 0x38, kDefaultDate); Store(data, 0x360, destination);
  Store(data, 0x368, std::int32_t{1}); Store(data, 0x36C, std::int32_t{1});
  Store(data, 0x83C, std::int32_t{0}); Store(data, 0x3B8, std::uint8_t{0}); return data;
}
const void *ResolveStart(const void *data) {
  Owner(); ++start_resolved;
  Check(data == seen_data && Get<std::int32_t>(data, 8) == Fixture::character_id,
      "native start lookup uses candidate owned data and actual player");
  return p->rejected_province.data();
}
bool EvaluateRoute(void *data) {
  Owner(); ++route_evaluated;
  Check(data == seen_data && start_resolved == route_evaluated && eta_evaluated + 1 == route_evaluated,
      "native route follows start lookup for each candidate");
  auto *points = new const void *[2]{p->rejected_province.data(), p->province_rows.at(static_cast<std::size_t>(current_candidate))};
  Store(data, 0x390, points); Store(data, 0x398, std::int32_t{2}); Store(data, 0x39C, std::int32_t{2});
  Store(data, 0x3B8, std::uint8_t{1}); return true;
}
void EvaluateArrival(void *data) {
  Owner(); ++eta_evaluated;
  Check(data == seen_data && eta_evaluated == route_evaluated && Get<std::uint8_t>(data, 0x3B8) == 1,
      "arrival native evaluation follows route success");
  auto *destination = Get<std::byte *>(data, 0x360);
  const auto *province = Get<const void *>(destination, 8);
  const auto arrival = Get<std::int32_t>(p->state.data(), 8) + Get<std::int32_t>(province, 0x10) * 3;
  Store(destination, 0x38, std::uint64_t{0x0123000000000000ULL} | static_cast<std::uint32_t>(arrival));
}
void DestroyData(void *data) {
  Owner(); ++data_destroyed;
  Check(data == seen_data && data_destroyed == eta_evaluated && input_destroyed + 1 == data_destroyed,
      "each owned route data is destroyed after readback and before input");
  Check(Get<const std::int32_t *>(data, 0x28) == data_ids && data_ids != input_ids,
      "native route constructor owns an independent candidate copy");
  delete[] Get<std::byte *>(data, 0x360); delete[] Get<const void **>(data, 0x390);
  delete[] data_ids; data_ids = nullptr; delete Get<std::uint64_t *>(data, 0x1E8); seen_data = nullptr;
}
void DestroyInput(void *input) {
  Owner(); ++input_destroyed;
  Check(input == seen_input && input_destroyed == data_destroyed && input_ids[0] == current_candidate,
      "each route input remains separately owned until data cleanup");
  delete[] input_ids; input_ids = nullptr; delete Get<std::uint64_t *>(input, 0x1E0); seen_input = nullptr;
}
route::Bindings BindRoute(PilgrimageFixture &fixture) {
  p = &fixture;
  route::Bindings b{}; b.enabled = true; b.provinces.enabled = true;
  b.provinces.game_state_slot = &p->state_ptr;
  b.participant_allocator = participant_allocator.data(); b.travel_option_allocator = option_allocator.data();
  b.descriptor_allocator = descriptor_allocator.data(); b.native_default_date = &kDefaultDate;
  b.province_ids_initialize = &InitializeIds; b.waypoints_initialize = &InitializeWaypoints;
  b.province_ids_append = &AppendIds; b.root_construct = &ConstructRoot;
  b.creation_input_destroy = &DestroyInput; b.data_construct = &ConstructData; b.data_destroy = &DestroyData;
  b.start_province = &ResolveStart; b.evaluate_route = &EvaluateRoute; b.evaluate_arrival = &EvaluateArrival;
  return b;
}
} // namespace route_fixture

void RunMailboxCase(PilgrimageFixture &fixture, const std::filesystem::path &directory) {

  FrameAdapter adapter;
  adapter.frame.paused = adapter.frame.map_ready = true;
  adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
  adapter.frame.played_character_id = Fixture::character_id;
  adapter.frame.date_raw = Get<std::int32_t>(fixture.state.data(), 8);
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(fixture, mailbox);
  c::PlayerReligionMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 1901;
  query.bindings = Bind(fixture);
  query.pilgrimage_activity_bindings = BindQuote(fixture);
  query.pilgrimage_route_bindings = route_fixture::BindRoute(fixture);
  std::atomic<bool> done{false};
  bool read = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    read = c::RunPlayerReligionMailbox12002(query, "pilgrimage\"headless-mailbox-fixture", serialized, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Check(read && drained && failure.empty() && query.completed && query.envelope.frame_stable && !serialized.empty(),
      "genuine mailbox submit owner drain wait reclaim produces command result");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle && adapter.reads == 2,
      "mailbox reclaimed after same owner before and after snapshot reads");
  const auto &context = query.observation;
  const auto &observed = query.pilgrimage_activity_terms;
  Check(context.available && context.capture_epoch == query.envelope.execution_stamp.pump_epoch &&
      context.capture_epoch != query.envelope.expected_snapshot_revision,
      "actual native Context capture epoch remains distinct from public revision");
  Check(observed.available && observed.capture_epoch == context.capture_epoch && observed.date_raw == context.date_raw &&
      observed.played_character_id == Fixture::character_id && observed.rite_id == 0U && observed.faith_id == Fixture::faith_id,
      "actual factory/quote preserves same player Context and full Rite/Faith identity");
  Check(observed.candidates.size() == 2 && fixture.filter_calls == 1 && fixture.phase_offer_calls == 2,
      "actual factory discovers native Faith providers without a caller candidate list");
  const auto &rejected = observed.candidates[0];
  Check(rejected.holy_site_id == PilgrimageFixture::rejected_holy_id && rejected.title_id == PilgrimageFixture::rejected_title_id &&
      rejected.province_id == 1 && rejected.can_select == false && !rejected.location_predicate.value &&
      rejected.location_predicate.reasons_available && rejected.location_predicate.reasons == fixture.rejected_reason &&
      rejected.phase_choices.size() == 1 && !rejected.phase_choices[0].activity_quote &&
      rejected.phase_choices[0].quote_unavailable_reason == "native_destination_not_selectable",
      "native root rejection preserves complete UTF8/control reason and prevents activity quote");
  const auto &legal = observed.candidates[1];
  Check(legal.holy_site_id == PilgrimageFixture::legal_holy_id && legal.title_id == PilgrimageFixture::legal_title_id &&
      legal.province_id == 2 && legal.can_select == true && legal.location_predicate.value &&
      legal.same_province_cap_applies && legal.same_province_phase_count == 1 && legal.same_province_phase_cap == 2 &&
      legal.same_province_cap_allows && !legal.total_cap_applies && legal.total_cap_allows == true &&
      observed.single_location == true && !observed.resolved_location_phase_count && fixture.same_cap_calls == 1,
      "single_location bypasses only total gate while genuine same-Province duplicate cap remains active");
  const auto &phase = legal.phase_choices.at(0);
  Check(phase.phase_definition_index == 12 && phase.province_id == 2 && phase.native_ai_choice_score_raw == -17 &&
      phase.shown.value && phase.location.value && phase.can_select_phase && phase.activity_quote && !phase.quote_unavailable_reason,
      "negative native AI score remains selectable with independent true native shown/location predicates");
  const auto &activity = *phase.activity_quote;
  Check(activity.activity_cost_raw_slots == fixture.costs && activity.affordable == false &&
      activity.affordability_reasons_available && activity.affordability_reasons == fixture.afford_reason &&
      activity.native_config_date_raw == context.date_raw,
      "complete signed native ten slots, actual quote date and independent affordability false survive");
  Check(observed.default_options.size() == 2 && observed.default_options[0].category_definition_index == 5 &&
      observed.default_options[0].option_definition_index == 21 && observed.default_options[0].selected_special &&
      !observed.default_options[1].selected_special && observed.selected_special_definition_index == 21 &&
      activity.default_options_used.size() == 2 && activity.default_options_used[0].option_definition_index == 21 &&
      observed.initial_configured_phases.size() == 1 && observed.initial_configured_phases[0].phase_definition_index == 11,
      "native actual-actor default options and baseline configured phase are read back");
  Check(activity.configured_phases.size() == 3 && activity.configured_phases[0].phase_definition_index == 12 &&
      activity.configured_phases[1].phase_definition_index == 11 && activity.configured_phases[2].phase_definition_index == 13 &&
      activity.configured_phases[0].native_default_phase == false && activity.configured_phases[1].native_default_phase == true &&
      activity.configured_phases[2].native_default_phase == true && activity.configured_phases[0].native_phase_order_raw == 10 &&
      activity.configured_phases[1].native_phase_order_raw == 20 && activity.configured_phases[2].native_phase_order_raw == 30,
      "genuine native ordered insertion/normalization includes default child phases in exact configured readback");
  Check(fixture.native_config_initializes == 2 && fixture.native_config_destroys == 2 && fixture.native_phase_inserts == 1 &&
      fixture.native_normalizes == 1 && fixture.native_cost_calls == 1 && fixture.native_afford_calls == 1 && fixture.configs.empty() &&
      fixture.root_constructs == fixture.root_destroys && fixture.scopes.empty() &&
      fixture.evaluator_constructs == 6 && fixture.evaluator_destroys == 6 && fixture.evaluators.empty() &&
      fixture.array_releases == 3 && fixture.reason_destroys == 7,
      "all native owned configs, child maps, arrays, roots, evaluators and reason sinks cleaned exactly once");
  const xar::game::AdapterDescriptor descriptor{xar::ck3_12003::kAdapterId, xar::ck3_12003::kGameVersion,
      xar::ck3_12003::kExecutableSha256, "synthetic-pilgrimage-leaf", {}};
  const auto rendered = xar::game::RenderCrozierBuildIdentity(serialized, descriptor);
  Check(rendered.find("\"schema\":\"ck3_12003_player_pilgrimage_headless_activity_terms_v1\"") != std::string::npos &&
      rendered.find("\"journey_cost_included\":false") != std::string::npos &&
      rendered.find("\"quote_scope\":\"activity_host_phase_and_selected_options\"") != std::string::npos &&
      rendered.find("\\u0000") != std::string::npos && rendered.find("\\u0001") != std::string::npos,
      "production serializer and genuine .3 renderer emit component scope and complete escaped reason bytes");

  Check(query.pilgrimage_candidate_routes.size() == observed.candidates.size(),
      "mailbox serializes one route sibling for every genuine factory candidate");
  for (std::size_t index = 0; index < query.pilgrimage_candidate_routes.size(); ++index) {
    const auto &route = query.pilgrimage_candidate_routes[index];
    Check(route.available && route.unavailable_reason.empty() && route.route_valid == true &&
        route.native_start_province_id == 1 && route.candidate_province_id == observed.candidates[index].province_id &&
        route.played_character_id == context.played_character_id && route.date_raw == context.date_raw &&
        route.capture_epoch == context.capture_epoch && route.outbound_arrival_date_raw == context.date_raw + route.candidate_province_id * 3,
        "route sibling preserves actual candidate, owner frame and native Date raw result");
  }
  Check(route_fixture::ids_initialized == 2 && route_fixture::waypoints_initialized == 2 && route_fixture::root_initialized == 2 &&
      route_fixture::ids_appended == 2 && route_fixture::data_constructed == 2 && route_fixture::start_resolved == 2 &&
      route_fixture::route_evaluated == 2 && route_fixture::eta_evaluated == 2 && route_fixture::data_destroyed == 2 &&
      route_fixture::input_destroyed == 2 && !route_fixture::seen_input && !route_fixture::seen_data &&
      !route_fixture::input_ids && !route_fixture::data_ids,
      "all route native primitives run and all separately owned inputs and data are cleaned once");
  Check(rendered.find("\"type\":\"command_result\"") != std::string::npos &&
      rendered.find("\"player_pilgrimage_headless_activity_terms\":{") != std::string::npos &&
      rendered.find("\"player_pilgrimage_candidate_routes\":[{") != std::string::npos &&
      rendered.find("\"game_version\":\"1.20.0.3\"") != std::string::npos &&
      rendered.find(xar::ck3_12003::kExecutableSha256) != std::string::npos &&
      rendered.find(xar::ck3_12002::kExecutableSha256) == std::string::npos &&
      rendered.find("\"snapshot_revision\":1901") != std::string::npos,
      "genuine full serializer and .3 renderer preserve nested siblings and exact build identity");
  std::ofstream output(directory / "native-command-result.json", std::ios::binary);
  output << rendered << '\n'; output.close(); Check(output.good(), "complete genuine command result saved");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory argument");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    PilgrimageFixture fixture;
    RunMailboxCase(fixture, directory);
    std::cout << "PASS cases=1 checks=" << checks << " actual_context_factory_owned_quote_routes_serializer_renderer=true synthetic_native_callbacks=true full_mailbox_query=true game=false live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
