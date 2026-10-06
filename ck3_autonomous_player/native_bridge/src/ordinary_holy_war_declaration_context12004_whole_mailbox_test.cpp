#include "xar_bridge/ordinary_holy_war_declaration_context12003_mailbox.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_core_frame_v1.hpp"
#include "xar_bridge/ck3_12004_holy_war.hpp"

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
namespace actual4 = xar::ck3_12004;
namespace game = xar::game;
namespace api = xar::ck3_11906;
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
constexpr std::uintptr_t kFixtureBase = 0x140000000;
constexpr std::int32_t kActor = 0x0B000001, kTarget = 0x0C000002, kAdditional = 0x0D000003;
constexpr std::int32_t kDate = 53222312;
constexpr std::uint64_t kNativeRevision = 17, kPublicRevision = 4, kCaptureEpoch = 1007;
constexpr char kWireFile[] = "native-wire-actual4-redirected-claimant-fallback.json";
constexpr char kRequestId[] = "g2-read-00000000000000000000000000004901";
constexpr std::array<std::int64_t, 10> kNativeCosts{
    -375001, 2234567, 25000001, 0, 103, 104, 105, 106, 107, 108};
unsigned checks = 0;
void Check(bool condition, const char *message) {
  ++checks; if (!condition) throw std::runtime_error(message);
}
struct War {
  Bytes<0x58> bytes{};
  std::vector<std::int32_t> titles;
  void Sync() {
    Array(bytes.data() + c::kDeclarationsWarTitlesOffset, titles.data(), static_cast<std::int32_t>(titles.size()));
  }
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
  Bytes<0x40> slots{};
  Bytes<0x1D8> actor{}, target{}, additional{}, fallback{};
  Bytes<0x98> cb_database{};
  Bytes<0xF80> interaction_database{};
  Bytes<0x1550> type{};
  Bytes<0x218> rule{};
  std::array<void *, 1> types{type.data()};
  Bytes<0x18> scratch{};
  Bytes<c::kDeclarationsConfigurationSize> configuration{};
  std::array<std::int32_t, 2> titles{0x0E000031, 0x0F000021};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  void *fallback_ptr = fallback.data();
  c::DeclarationsBindings declarations{};
  c::OrdinaryHolyWarCbCostBindingsV1 cost{};
  bool bad_arguments = false;
  unsigned evaluations = 0, configuration_destroys = 0, context_constructs = 0, context_destroys = 0;
  unsigned refreshes = 0, finalizes = 0, validations = 0, scope_constructs = 0, scope_populates = 0;
  unsigned scope_destroys = 0, cost_evaluations = 0;
  const void *populated_scope = nullptr;
  const void *actual_native_titles = nullptr;
  c::OrdinaryHolyWarDeclarationContextMailbox12003 *owning_query = nullptr;
  Fixture() {
    Put(state.data(), actual4::kGameStateDateOffset, kDate);
    Put(state.data(), actual4::kGameStateSpeedOffset, std::int32_t{2});
    Put(state.data(), actual4::kGameStateDataOffset, data.data());
    Put(jomini.data(), actual4::kJominiPlayersOffset, players.data());
    jomini[actual4::kJominiPausedOffset] = std::byte{1};
    Put(players.data(), actual4::kPlayersLocalPlayerIdOffset, std::int32_t{7});
    Put(player.data(), actual4::kPlayerIdOffset, std::int32_t{7});
    Put(data.data(), actual4::kPlayerCharacterManagerOffset + actual4::kPlayerManagerEntriesOffset, entries.data());
    Put(data.data(), actual4::kPlayerCharacterManagerOffset + actual4::kPlayerManagerCountOffset, std::int32_t{1});
    Put(entry.data(), actual4::kPlayerEntryLocalPlayerIdOffset, std::int32_t{7});
    Put(entry.data(), actual4::kPlayerEntryCharacterIdOffset, kActor);
    Put(storage.data(), actual4::kCharacterStorageSlotsOffset, slots.data());
    Put(storage.data(), actual4::kCharacterStorageCapacityOffset, std::int32_t{4});
    Put(slots.data(), 0x18, actor.data()); Put(slots.data(), 0x28, target.data()); Put(slots.data(), 0x38, additional.data());
    Put(actor.data(), actual4::kCharacterFullIdOffset, kActor);
    Put(target.data(), actual4::kCharacterFullIdOffset, kTarget);
    Put(additional.data(), actual4::kCharacterFullIdOffset, kAdditional);
    Put(fallback.data(), actual4::kCharacterFullIdOffset, std::int32_t{-1});
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
    return {kTarget, 0, "religious_war", 0, -1, std::vector<std::int32_t>(titles.begin(), titles.end())};
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
  Put(f.configuration.data(), 0, std::int32_t{-1});
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
  Put(context, c::kDeclarationsAdditionalRoleOffset, actor);
  auto *war = new War;
  Put(war->bytes.data(), 0, f.declarations.war_declaration_vtable);
  Put(context, c::kDeclarationsSpecialDataOffset, war->bytes.data());
  return context;
}
void Refresh(void *, bool refresh) {
  ++active->refreshes; if (!active->OwnsCallback() || !refresh) active->bad_arguments = true;
}
void Finalize(void *context) {
  ++active->finalizes;
  if (!active->OwnsCallback() || Get<std::int32_t>(context, c::kDeclarationsAdditionalRoleOffset) != kActor)
    active->bad_arguments = true;
  // Fixture-native finalization redirects the independent role. The actual
  // production collector must read it after finalization, without replacing it.
  Put(context, c::kDeclarationsAdditionalRoleOffset, kAdditional);
}
bool Validate(void *context, void *reason) {
  auto &f = *active;
  ++f.validations;
  const auto *war = Get<const void *>(context, c::kDeclarationsSpecialDataOffset);
  if (!f.OwnsCallback() || reason || Get<const void *>(war, c::kDeclarationsWarCbOffset) != f.type.data() ||
      Get<std::int32_t>(context, c::kDeclarationsAdditionalRoleOffset) != kAdditional) f.bad_arguments = true;
  return false;
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
  if (!active->OwnsCallback() || reinterpret_cast<std::uintptr_t>(scope) % 16 != 0) active->bad_arguments = true;
  Put(scope, 0, std::uint64_t{0x16812004});
}
void ScopePopulate(void *scope, void *additional, void *recipient, void *claimant, const void *titles, std::int32_t extra) {
  auto &f = *active;
  ++f.scope_populates; f.populated_scope = scope;
  if (!f.OwnsCallback() || Get<std::uint64_t>(scope, 0) != 0x16812004 || additional != f.additional.data() ||
      recipient != f.target.data() || claimant != f.fallback.data() || titles != f.actual_native_titles ||
      extra != 0 || Get<std::int32_t>(titles, 12) != 2) f.bad_arguments = true;
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
  if (!f.OwnsCallback() || cost != f.type.data() + c::kOrdinaryHolyWarCompiledCostOffsetV1 ||
      scope != f.populated_scope || !out) f.bad_arguments = true;
  std::memcpy(out, kNativeCosts.data(), sizeof(kNativeCosts));
}
void Bind(Fixture &f) {
  active = &f;
  // Production .4 factories perform address arithmetic only. Every native
  // function and global that is dereferenced below is replaced by fixture material.
  f.declarations = actual4::BindOrdinaryHolyWarDeclarationsImage12004(kFixtureBase, actual4::kExecutableSha256);
  f.cost = actual4::BindOrdinaryHolyWarCbCostImage12004(kFixtureBase, actual4::kExecutableSha256);
  Check(f.declarations.enabled && f.declarations.core.enabled && f.declarations.war_declaration_vtable &&
      f.cost.enabled && f.cost.construct_scope && f.cost.populate_scope && f.cost.destroy_scope && f.cost.evaluate_cost,
      "actual .4 native factories supply admitted declaration and CB scope bindings");
  auto &b = f.declarations;
  b.core.game_state_slot = &f.state_ptr; b.core.jomini_state_slot = &f.jomini_ptr;
  b.core.character_storage_slot = &f.storage_ptr; b.core.get_local_player = &Player;
  b.configuration_scratch = f.scratch.data(); b.get_cb_database = &CbDatabase;
  b.get_interaction_database = &InteractionDatabase; b.evaluate_cb = &Evaluate;
  b.destroy_configuration = &DestroyConfiguration; b.construct_context = &Construct;
  b.refresh_context = &Refresh; b.finalize_context = &Finalize; b.validate_context = &Validate;
  b.destroy_context = &DestroyContext; b.copy_int_array = &Copy; b.append_int_array = &Append;
  b.commands = {}; b.construct_send = nullptr; b.send_primary_vtable = 0; b.send_secondary_vtable = 0;
  f.cost.construct_scope = &ScopeConstruct; f.cost.populate_scope = &ScopePopulate;
  f.cost.destroy_scope = &ScopeDestroy; f.cost.evaluate_cost = &CostEvaluate;
  f.cost.native_character_fallback_slot = &f.fallback_ptr;
}
class FrameAdapter final : public game::GameAdapter {
 public:
  game::Snapshot frame{};
  const DWORD owner = GetCurrentThreadId();
  mutable unsigned reads = 0, commands = 0;
  game::AdapterDescriptor identity{actual4::kAdapterId, actual4::kGameVersion,
      actual4::kExecutableSha256, "ordinary-holy-war-actual4-native-whole-fixture", {}};
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
#define ABSENT(Result, Name, Params) game::Result Name Params const noexcept override { ++commands; return game::Result::unavailable; }
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
BOOL WINAPI FixturePeek(LPMSG, HWND, UINT, UINT, UINT) { return FALSE; }
struct Pump {
  Bytes<0x28> tls{};
  Bytes<0x18> rng{};
  std::uint8_t initialized = 1;
  std::uintptr_t rng_wrapper = 0, rng_slot = 0;
  void *peek_slot = reinterpret_cast<void *>(&FixturePeek);
  DWORD protection = PAGE_READONLY;
  api::MainThreadQueryMailboxV1 &mailbox;
  Pump(Fixture &f, api::MainThreadQueryMailboxV1 &state) : mailbox(state) {
    tls[0x20] = std::byte{1}; tls_context = tls.data();
    Put(rng.data(), 0x10, GetCurrentThreadId());
    rng_wrapper = reinterpret_cast<std::uintptr_t>(rng.data());
    rng_slot = reinterpret_cast<std::uintptr_t>(&rng_wrapper);
    auto environment = actual4::BindCoreFrameMailboxEnvironmentV1(kFixtureBase, actual4::kExecutableSha256);
    Check(environment.exact_build_admitted && environment.build_profile,
        "actual .4 core-frame mailbox factory supplies the exact current pump profile");
    environment.offline_fixture = true;
    environment.peek_message_iat_slot_override = &peek_slot;
    environment.resolved_peek_message_override = &FixturePeek;
    environment.global_rng_wrapper_slot_override = reinterpret_cast<std::uintptr_t>(&rng_slot);
    environment.jomini_state_slot_override = reinterpret_cast<std::uintptr_t>(&f.jomini_ptr);
    environment.game_state_slot_override = reinterpret_cast<std::uintptr_t>(&f.state_ptr);
    environment.tls_initialized_flag_override = reinterpret_cast<std::uintptr_t>(&initialized);
    environment.tls_context_getter_override = &FixtureTls;
    environment.memory_protection_context = this;
    environment.memory_query_override = &Query;
    environment.memory_protect_override = &Protect;
    environment.system_page_size_override = 4096;
    environment.permitted_executor_ordinary_holy_war_declaration_context12003 = &c::ExecuteOrdinaryHolyWarDeclarationContextMailbox12003;
    Check(api::InstallMainThreadQueryMailboxV1(mailbox, environment), "actual .4 profiled mailbox installs into fixture-owned IAT");
    Check(mailbox.pump_exact_return_rva == environment.build_profile->pump_exact_return_rva,
        "drain boundary comes from the actual .4 production pump profile");
    mailbox.pump_epochs = kCaptureEpoch - 3;
    for (unsigned i = 0; i < 2; ++i)
      (void)api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() {
    (void)api::UninstallMainThreadQueryMailboxV1(mailbox, 1000);
    tls_context = nullptr;
  }
  static bool Query(void *opaque, const void *address, MEMORY_BASIC_INFORMATION &information) noexcept {
    auto &pump = *static_cast<Pump *>(opaque);
    if (address != &pump.peek_slot) return false;
    const auto page = reinterpret_cast<std::uintptr_t>(address) & ~std::uintptr_t{4095};
    information = {};
    information.BaseAddress = reinterpret_cast<void *>(page);
    information.AllocationBase = information.BaseAddress;
    information.RegionSize = 4096; information.State = MEM_COMMIT;
    information.Protect = pump.protection; information.Type = MEM_IMAGE;
    return true;
  }
  static bool Protect(void *opaque, void *, std::size_t bytes, DWORD requested, DWORD &previous) noexcept {
    auto &pump = *static_cast<Pump *>(opaque);
    if (bytes != 4096) return false;
    previous = pump.protection; pump.protection = requested; return true;
  }
};
std::string Request(const Fixture &f) {
  return "{\"expected_revision\":17,\"expected_snapshot_revision\":17,\"expected_public_revision\":4,"
      "\"declaration_id\":\"" + std::to_string(kTarget) + "-0-0\",\"target_character_id\":" + std::to_string(kTarget) +
      ",\"casus_belli_index\":0,\"configuration_index\":0,\"claimant_character_id\":-1,"
      "\"casus_belli_key\":\"religious_war\",\"target_title_ids\":[" + std::to_string(f.titles[0]) + ',' +
      std::to_string(f.titles[1]) + "]}";
}
void Query(Fixture &f, const std::filesystem::path &directory) {
  Bind(f); FrameAdapter adapter;
  actual4::CoreSnapshotPrefix prefix{};
  Check(actual4::ReadCoreSnapshot(f.declarations.core, prefix) && prefix.played_character_id == kActor,
      "actual .4 core reader resolves the new fixture's complete CharacterID");
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
      query.request.selected == f.Selected(), "existing production request parser retains the new full row and both revisions");
  query.declarations = f.declarations; query.cost = f.cost; f.owning_query = &query;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
  std::string wire, failure;
  std::thread worker([&] {
    result = c::RunOrdinaryHolyWarDeclarationContextMailbox12003(query, kRequestId, wire, failure);
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
      "actual owner mailbox executes the production collector and complete serializer");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle && mailbox.executed_requests == 1 &&
      query.envelope.execution_stamp.pump_epoch == kCaptureEpoch && adapter.reads == 2,
      "one actual .4 pump transaction is reclaimed with the same paused frame");
  const auto &out = query.observation;
  Check(out.available && out.capture_epoch == kCaptureEpoch && out.native_revision == kNativeRevision &&
      out.public_revision == kPublicRevision && out.date_raw == kDate && out.played_character_id == kActor &&
      out.selected == f.Selected() && out.context_actor_character_id == kActor && out.context_recipient_character_id == kTarget &&
      out.context_additional_role_character_id == kAdditional && out.context_claimant_character_id == -1 &&
      out.final_can_send == false && !out.recipient_uses_native_fallback && !out.additional_role_uses_native_fallback &&
      out.claimant_uses_native_fallback, "finalized independent additional role and claimant fallback survive the false final gate");
  Check(out.cb_cost.available && out.cb_cost.resource_costs_raw == kNativeCosts &&
      f.evaluations == 1 && f.configuration_destroys == 1 && f.context_constructs == 1 && f.context_destroys == 1 &&
      f.refreshes == 1 && f.finalizes == 1 && f.validations == 1 && f.scope_constructs == 1 && f.scope_populates == 1 &&
      f.scope_destroys == 1 && f.cost_evaluations == 1 && Get<std::int32_t>(f.scratch.data(), 12) == 0,
      "one selected context and native CB scope publish all ten signed Q100000 values with complete cleanup");
  Check(!f.bad_arguments && adapter.commands == 0 && !f.declarations.commands.enabled && !f.declarations.construct_send,
      "only fixture-native callbacks run with the exact actual scope and no gameplay command path");
  const auto rendered_context = game::Render12004BuildIdentity(c::SerializeOrdinaryHolyWarDeclarationContextV1(out), adapter.descriptor());
  Check(wire.find("\"player_ordinary_holy_war_declaration_context\":" + rendered_context) != std::string::npos &&
      wire.find("\"game_version\":\"1.20.0.4\"") != std::string::npos && wire.find(actual4::kExecutableSha256) != std::string::npos &&
      wire.find("\"game_version\":\"1.20.0.3\"") == std::string::npos &&
      wire.find("\"generic_interaction_cost_raw\":null") != std::string::npos &&
      wire.find("\"total_declaration_cost_raw\":null") != std::string::npos,
      "actual production whole serializer selects the .4 descriptor renderer without packet repair");
  std::ofstream file(directory / kWireFile, std::ios::binary);
  Check(static_cast<bool>(file), "open sole new actual .4 whole wire");
  file << wire << '\n'; Check(static_cast<bool>(file), "write unchanged complete production packet");
  f.owning_query = nullptr;
}
void Receipt(const Fixture &f, const std::filesystem::path &directory) {
  std::ofstream out(directory / "actual4-producer-receipt.json", std::ios::binary);
  Check(static_cast<bool>(out), "open actual .4 compiled producer receipt");
  out << "{\"schema\":\"xar.ck3.ordinary-holy-war-declaration-context-actual4-native-whole-fixture/v1\","
      "\"status\":\"GREEN\",\"cases\":1,\"whole_wire_files\":[\"" << kWireFile << "\"],"
      "\"frame\":{\"public_revision\":4,\"native_revision\":17,\"capture_epoch\":1007,"
      "\"date_raw\":53222312,\"played_character_id\":" << kActor << ",\"paused\":true,\"map_ready\":true},"
      "\"exact_build\":{\"game_version\":\"1.20.0.4\",\"executable_sha256\":\"" << actual4::kExecutableSha256 << "\"},"
      "\"provenance\":{\"native_memory\":\"fixture-synthetic\",\"native_callbacks\":\"fixture-synthetic\","
      "\"source_frame\":\"fixture-synthetic\",\"public_revision\":\"fixture-synthetic\",\"capture_epoch\":\"fixture-synthetic\","
      "\"whole_wires\":\"compiled-production-serializer\",\"whole_wire_rows_repaired\":false},"
      "\"pipeline\":{\"actual4_declaration_factory\":true,\"actual4_cb_cost_factory\":true,\"actual4_core_reader\":true,"
      "\"actual4_pump_profile\":true,\"actual_request_parser\":true,\"actual_named_mailbox\":true,"
      "\"actual_selected_context_reader\":true,\"actual_cb_cost_reader\":true,\"actual_full_serializer\":true,"
      "\"actual4_build_identity_renderer\":true,\"offline_native_image_handler_invoked\":false,\"live\":false},"
      "\"native_calls\":{\"evaluate_cb\":" << f.evaluations << ",\"construct_context\":" << f.context_constructs
      << ",\"refresh_context\":" << f.refreshes << ",\"finalize_context\":" << f.finalizes << ",\"validate_context\":" << f.validations
      << ",\"construct_scope\":" << f.scope_constructs << ",\"populate_scope\":" << f.scope_populates
      << ",\"evaluate_cost\":" << f.cost_evaluations << "},\"cleanup\":{\"destroy_configuration\":" << f.configuration_destroys
      << ",\"destroy_context\":" << f.context_destroys << ",\"destroy_scope\":" << f.scope_destroys
      << ",\"scratch_count\":" << Get<std::int32_t>(f.scratch.data(), 12) << ",\"mailbox_reclaimed\":true},"
      "\"gameplay_commands\":0,\"checks\":" << checks << "}\n";
  Check(static_cast<bool>(out), "write actual .4 compiled assertion receipt");
}
} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "one fresh existing output directory argument required");
    const std::filesystem::path directory(argv[1]);
    Check(std::filesystem::is_directory(directory), "Root prepares the first actual .4 fixture output directory");
    Fixture fixture; Query(fixture, directory); Receipt(fixture, directory);
    std::cout << "GREEN actual4_cases=1 checks=" << checks
        << " actual4_factories=true actual4_pump=true actual_named_mailbox=true actual_full_serializer=true"
           " synthetic_native_memory=true gameplay_commands=0 live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "RED " << error.what() << '\n'; return 1; }
}
