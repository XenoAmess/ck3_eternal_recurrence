#include "xar_bridge/ck3_12004_epidemic.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_thread_runtime.hpp"
#include "xar_bridge/ck3_12002_epidemic_recovery_mailbox.hpp"
#include "xar_bridge/ck3_12002_epidemic_treatment_mailbox.hpp"

// Reuse existing caller-owned provider memory and callbacks, never its old main.
// Both new cases run the actual .4-selected domain mailbox/production reader.
#define main FrozenRecoveryMemoryMainNotInvoked12004
#include "ck3_12002_epidemic_recovery_test.cpp"
#undef main

#include <atomic>
#include <bit>
#include <chrono>
#include <thread>

#if defined(XAR_EPIDEMIC_RECOVERY_MAILBOX_STANDALONE_NATIVE_ADAPTER)
namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept {
  return adapter;
}
}
#endif

namespace {
namespace n = xar::ck3_12004;
namespace game = xar::game;
class EpidemicAdapter final : public game::GameAdapter {
public:
  game::AdapterDescriptor identity{n::kAdapterId, n::kGameVersion,
                                   n::kExecutableSha256, "fixture", {}};
  game::Snapshot snapshot{};
  bool admitted = true;
  mutable std::atomic<int> snapshot_reads{0};
  EpidemicAdapter() {
    snapshot.date_raw = Fixture::date; snapshot.paused = true;
    snapshot.map_ready = true; snapshot.player_id = 7;
    snapshot.has_played_character = true; snapshot.played_character_alive = true;
    snapshot.played_character_id = Fixture::actor;
    snapshot.has_active_event = true; snapshot.active_event_instance_id = 73;
    snapshot.active_event_option_count = 2;
  }
  const game::AdapterDescriptor &descriptor() const noexcept override { return identity; }
  bool enabled() const noexcept override { return admitted; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    ++snapshot_reads; out = snapshot; return true;
  }
#define UNAVAILABLE(Type, Method, Arguments) \
  game::Type Method Arguments const noexcept override { return game::Type::unavailable; }
  UNAVAILABLE(PauseSubmitResult, submit_pause_map, (game::Snapshot *))
  UNAVAILABLE(ResumeSubmitResult, submit_resume_map, (game::Snapshot *))
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  UNAVAILABLE(SelectEventOptionResult, submit_select_event_option, (std::int32_t))
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override { return {}; }
  UNAVAILABLE(ReplyPendingInteractionResult, submit_reply_to_pending_interaction,
              (game::PendingInteractionReply))
  UNAVAILABLE(RaiseTroopsResult, submit_raise_troops_default, ())
  UNAVAILABLE(MoveArmyResult, submit_move_army, (std::int32_t, std::int32_t))
  game::PreviewMoveArmyResult preview_move_army(std::int32_t, std::int32_t) const noexcept override { return {}; }
  UNAVAILABLE(DisbandArmyResult, submit_disband_army, (std::int32_t))
  UNAVAILABLE(SplitArmyHalfResult, submit_split_army_half, (std::int32_t))
  UNAVAILABLE(MergeArmiesResult, submit_merge_armies, (std::int32_t, std::int32_t))
  UNAVAILABLE(StartAssaultResult, submit_start_assault, (std::int32_t))
  UNAVAILABLE(StopAssaultResult, submit_stop_assault, (std::int32_t))
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &) const noexcept override { return false; }
  UNAVAILABLE(ReadDeclarableWarsResult, read_declarable_wars_for_target,
              (std::int32_t, std::vector<game::DeclarableWarSnapshot> &))
  UNAVAILABLE(DeclareWarResult, submit_declare_war, (const game::DeclarableWarSnapshot &))
  UNAVAILABLE(ReadArrangeMarriageChoicesResult, read_arrange_marriage_choices,
              (std::vector<game::ArrangeMarriageChoice> &, game::ArrangeMarriageQueryDiagnostics &))
  UNAVAILABLE(ArrangeMarriageResult, submit_arrange_marriage, (const game::ArrangeMarriageChoice &))
  UNAVAILABLE(EnforceDemandsResult, submit_enforce_demands, (std::int32_t))
  UNAVAILABLE(ReadArmyStrengthsResult, read_army_strengths, (std::vector<game::ArmyStrengthSnapshot> &))
  UNAVAILABLE(ReadCombatSimulationInputsResult, read_combat_simulation_inputs,
              (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &))
  UNAVAILABLE(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3,
              (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &))
  UNAVAILABLE(ReadWarTerminationOptionsResult, read_war_termination_options,
              (std::int32_t, game::WarTerminationOptionsSnapshot &))
  UNAVAILABLE(ReadWarTerminationTermsResult, read_war_termination_terms,
              (std::int32_t, game::WarTerminationTermsSnapshot &))
  UNAVAILABLE(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms,
              (std::int32_t, game::WarTerminationExitTermsSnapshot &))
  UNAVAILABLE(SurrenderWarResult, submit_surrender_war, (std::int32_t))
  UNAVAILABLE(OfferWhitePeaceResult, submit_offer_white_peace, (std::int32_t))
#undef UNAVAILABLE
};

BOOL WINAPI PeekFixture(LPMSG, HWND, UINT, UINT, UINT) { return FALSE; }
struct Protection { void **slot = nullptr; DWORD protection = PAGE_READONLY; };
bool QueryFixture(void *opaque, const void *address, MEMORY_BASIC_INFORMATION &information) noexcept {
  auto &memory = *static_cast<Protection *>(opaque);
  if (address != memory.slot) return false;
  const auto page = reinterpret_cast<std::uintptr_t>(address) & ~std::uintptr_t{4095};
  information = {}; information.BaseAddress = reinterpret_cast<void *>(page);
  information.AllocationBase = information.BaseAddress; information.AllocationProtect = PAGE_READONLY;
  information.RegionSize = 4096; information.State = MEM_COMMIT;
  information.Protect = memory.protection; information.Type = MEM_IMAGE; return true;
}
bool ProtectFixture(void *opaque, void *, std::size_t size, DWORD protection, DWORD &before) noexcept {
  if (size != 4096) return false;
  auto &memory = *static_cast<Protection *>(opaque);
  before = memory.protection; memory.protection = protection; return true;
}
Bytes<0x28> tls{};
void *__fastcall TlsFixture() noexcept { return tls.data(); }

struct EpidemicRuntime {
  old::MainThreadQueryMailboxV1 mailbox{};
  Bytes<0x18> rng{};
  std::uintptr_t rng_pointer = reinterpret_cast<std::uintptr_t>(rng.data());
  std::uintptr_t rng_wrapper = reinterpret_cast<std::uintptr_t>(&rng_pointer);
  std::uint8_t initialized = 1;
  void *iat = reinterpret_cast<void *>(&PeekFixture);
  Protection protection{&iat};
  bool Install(Fixture &material) {
    const auto thread = GetCurrentThreadId(); Put(rng, 0x10, thread); tls[0x20] = std::byte{1};
    auto env = n::BindThreadRuntimeImage(0x100000, n::kExecutableSha256);
    env.offline_fixture = true; env.executor_submission_enabled = true;
    env.permitted_executor_epidemic_recovery12002 = &c::ExecutePlayerEpidemicRecoveryMailbox12002;
    env.permitted_executor_epidemic_treatment12002 = &c::ExecutePlayerEpidemicTreatmentMailbox12002;
    env.peek_message_iat_slot_override = &iat; env.resolved_peek_message_override = &PeekFixture;
    env.global_rng_wrapper_slot_override = reinterpret_cast<std::uintptr_t>(&rng_wrapper);
    env.jomini_state_slot_override = reinterpret_cast<std::uintptr_t>(&material.jomini_ptr);
    env.game_state_slot_override = reinterpret_cast<std::uintptr_t>(&material.state_ptr);
    env.tls_initialized_flag_override = reinterpret_cast<std::uintptr_t>(&initialized);
    env.tls_context_getter_override = &TlsFixture;
    env.memory_protection_context = &protection; env.memory_query_override = &QueryFixture;
    env.memory_protect_override = &ProtectFixture; env.system_page_size_override = 4096;
    if (!old::InstallMainThreadQueryMailboxV1(mailbox, env)) return false;
    for (int i = 0; i < 3; ++i)
      old::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, thread);
    return old::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready &&
      mailbox.permitted_executor_epidemic_recovery12002 == &c::ExecutePlayerEpidemicRecoveryMailbox12002 &&
      iat == reinterpret_cast<void *>(&old::XarMainThreadPeekMessageWHookV1);
  }
};

struct TreatmentMaterial {
  Bytes<0x200> extension{};
  Bytes<0x90> rows{};
  Bytes<0x50> definition{}, other{};
  std::string key{old::kPlayerEpidemicTreatmentModifierKeyV1};
  bool fallback = false;
  bool hash_checked = false;
  bool full_hash_checked = false;
  TreatmentMaterial() {
    Put(f->character, c::kTreatmentCharacterExtensionOffset12002, extension.data());
    Put(extension, c::kTreatmentModifierRowsOffset12002, rows.data());
    Put(extension, c::kTreatmentModifierCountOffset12002, std::int32_t{2});
    Put(rows, 0, other.data());
    Put(rows, c::kTreatmentModifierRowStride12002, definition.data());
    Fixture::Name(definition, key);
  }
};
TreatmentMaterial *t = nullptr;
std::uint32_t TreatmentHash(void *database, const char *key, std::uint32_t size) {
  t->hash_checked = database == f && std::string_view(key, size) == t->key;
  return 0xE0000042U;
}
void *TreatmentLookup(void *database, std::int32_t hash) {
  t->full_hash_checked = database == f && std::bit_cast<std::uint32_t>(hash) == 0xE0000042U;
  return t->fallback ? f->fallback_ptr : t->definition.data();
}
struct WholeResponse { bool success = false; bool drained = false; std::string packet{}, failure{}; };
WholeResponse InvokeWhole(EpidemicAdapter &adapter, EpidemicRuntime &runtime,
    const r::Bindings &recovery, const c::TreatmentPresenceBindings12002 &treatment,
    bool treatment_mode, std::string_view step, std::string_view name) {
  WholeResponse out{};
  std::atomic<bool> done{false};
  std::thread worker([&] {
    if (treatment_mode) {
      out.success = c::HandlePlayerEpidemicTreatmentPrivate12002(adapter, runtime.mailbox,
          adapter.snapshot, 88, step, "{\"expected_revision\":88}", name,
          out.packet, out.failure, &treatment);
    } else {
      out.success = c::HandleEpidemicRecoveryPrivateBound12002(adapter, runtime.mailbox,
          adapter.snapshot, 88, step, "{\"expected_revision\":88}", name,
          recovery, out.packet, out.failure);
    }
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(5);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (runtime.mailbox.state.load(std::memory_order_acquire) == old::MainThreadQueryMailboxStateV1::queued)
      out.drained = old::ObserveMainThreadPumpAndDrainV1(runtime.mailbox,
          runtime.mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  return out;
}
bool StoreWhole(const std::filesystem::path &directory, const char *name,
    const WholeResponse &response, const EpidemicRuntime &runtime,
    std::string_view expected) {
  if (!Check(response.success && response.drained && response.failure.empty() &&
      runtime.mailbox.state.load() == old::MainThreadQueryMailboxStateV1::idle &&
      response.packet.find(expected) != std::string::npos,
      name)) return false;
  std::ofstream stream(directory / name, std::ios::binary);
  stream << response.packet << '\n';
  return stream.good();
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path directory(argv[1]);
  std::filesystem::create_directories(directory);
  Fixture material;
  const auto fixture_recovery = Bind(material);
  auto recovery = n::BindEpidemicRecoveryImage(0x100000, n::kExecutableSha256);
  auto treatment = n::BindEpidemicTreatmentImage(0x100000, n::kExecutableSha256);
  if (!Check(recovery.enabled && treatment.enabled &&
      n::EpidemicProfile().actual4_operands_verified,
      "actual .4 independent profile admits both image bindings")) return 3;
  // The profile admits the actual .4 image. Only this offline owner supplies
  // caller-owned memory/callbacks in place of native image addresses.
  recovery.core = fixture_recovery.core;
  recovery.identifiers = fixture_recovery.identifiers;
  recovery.landed_title_store_slot = fixture_recovery.landed_title_store_slot;
  recovery.modifier_fallback_slot = fixture_recovery.modifier_fallback_slot;
  recovery.modifier_database = fixture_recovery.modifier_database;
  recovery.stable_key_hash = fixture_recovery.stable_key_hash;
  recovery.modifier_lookup = fixture_recovery.modifier_lookup;
  recovery.county_modifier_getter = fixture_recovery.county_modifier_getter;
  TreatmentMaterial treatment_material;
  t = &treatment_material;
  treatment.core = recovery.core;
  treatment.get_modifier_database = &Database;
  treatment.hash_stable_key = &TreatmentHash;
  treatment.lookup_modifier = &TreatmentLookup;
  treatment.fallback_definition_slot = &material.fallback_ptr;
  EpidemicAdapter adapter;
  EpidemicRuntime runtime;
  if (!runtime.Install(material)) return 3;
  const auto recovery_step = std::string_view(old::kPlayerEpidemicRecoveryStepV1);
  const auto treatment_step = c::kPlayerEpidemicTreatmentPrivateStep12002;
  auto recovery_case = [&](const char *name, std::string_view expected, std::string_view step = {}) {
    const auto response = InvokeWhole(adapter, runtime, recovery, treatment, false,
        step.empty() ? recovery_step : step, name);
    return StoreWhole(directory, name, response, runtime, expected);
  };
  auto treatment_case = [&](const char *name, std::string_view expected) {
    const auto response = InvokeWhole(adapter, runtime, recovery, treatment, true, treatment_step, name);
    return StoreWhole(directory, name, response, runtime, expected);
  };
  if (!recovery_case("recovery-two-counties.json", "\"status\":\"available\"")) return 4;
  Put(material.context, 0x3C, std::int32_t{0});
  if (!recovery_case("recovery-empty-list.json", "\"counties\":[]")) return 5;
  material.context_fails = true;
  if (!recovery_case("recovery-list-unavailable.json", "\"counties\":null")) return 6;
  material.context_fails = false;
  material.minor[0] = false; material.tiny[0] = false;
  const auto title_step = std::string(recovery_step) + "-title-" + std::to_string(Fixture::county_a);
  adapter.snapshot.has_active_event = false;
  if (!recovery_case("recovery-explicit-absent.json", "\"minor_present\":false,\"tiny_present\":false", title_step)) return 7;
  material.lookup_fails = true;
  if (!recovery_case("recovery-definition-unavailable.json", "\"counties\":null", title_step)) return 8;
  material.lookup_fails = false;
  if (!treatment_case("treatment-present.json", "\"present\":true") ||
      !Check(t->hash_checked && t->full_hash_checked, "actual fixed key and full32 hash inputs")) return 9;
  Put(t->rows, c::kTreatmentModifierRowStride12002, t->other.data());
  if (!treatment_case("treatment-absent.json", "\"present\":false")) return 10;
  Put(material.character, c::kTreatmentCharacterExtensionOffset12002, static_cast<void *>(nullptr));
  if (!treatment_case("treatment-empty-extension.json", "\"present\":false")) return 11;
  Put(material.character, c::kTreatmentCharacterExtensionOffset12002, t->extension.data());
  Put(t->extension, c::kTreatmentModifierRowsOffset12002, static_cast<void *>(nullptr));
  Put(t->extension, c::kTreatmentModifierCountOffset12002, std::int32_t{0});
  if (!treatment_case("treatment-empty-rows.json", "\"present\":false")) return 12;
  Put(t->extension, c::kTreatmentModifierCountOffset12002, std::int32_t{1});
  if (!treatment_case("treatment-rows-unavailable.json", "\"present\":null")) return 13;
  t->fallback = true;
  if (!treatment_case("treatment-definition-unavailable.json", "\"present\":null")) return 14;
  // Exact .4 admission is exercised on the real controllers, not a duplicate
  // predicate: replacing only its hash rejects before any native query is queued.
  adapter.identity.executable_sha256 = c::kExecutableSha256;
  auto rejected = InvokeWhole(adapter, runtime, recovery, treatment, true, treatment_step, "wrong-build-treatment");
  if (!Check(!rejected.success && !rejected.drained && rejected.packet.empty(), "wrong exact .4 hash rejected")) return 15;
  rejected = InvokeWhole(adapter, runtime, recovery, treatment, false, title_step, "wrong-build-recovery");
  if (!Check(!rejected.success && !rejected.drained && rejected.packet.empty(), "recovery wrong exact .4 hash rejected")) return 15;
  adapter.identity.executable_sha256 = n::kExecutableSha256;
  const auto removal = old::UninstallMainThreadQueryMailboxV1(runtime.mailbox, 0);
  if (!Check(removal == old::MainThreadQueryUninstallResultV1::uninstalled &&
      runtime.iat == reinterpret_cast<void *>(&PeekFixture), "actual .4 fixture owner reclaimed")) return 16;
  std::ofstream provenance(directory / "provenance.json");
  provenance << "{\"schema\":\"actual4-epidemic-whole-native-fixture-v1\","
      "\"fixture_context\":true,\"native_callbacks_synthetic\":true,"
      "\"actual4_profile_bindings_verified\":true,"
      "\"old_fixture_main_invoked\":false,\"live\":false,"
      "\"game_version\":\"1.20.0.4\",\"steam_build_id\":25734779,"
      "\"executable_sha256\":\"" << n::kExecutableSha256 << "\","
      "\"snapshot_revision\":88,\"date_raw\":" << Fixture::date << ','
      << "\"played_character_id\":" << Fixture::actor << ','
      << "\"checks\":" << checks << "}\n";
  return provenance.good() ? 0 : 17;
}
