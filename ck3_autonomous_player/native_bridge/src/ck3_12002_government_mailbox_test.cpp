#include "xar_bridge/ck3_12002_government_mailbox.hpp"
#include "xar_bridge/ck3_12002_campaign.hpp"
#include "xar_bridge/government_runtime_adapter_bridge_binder_v1.hpp"

#include <windows.h>

#include <array>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <string_view>
#include <thread>

#if defined(XAR_GOVERNMENT_MAILBOX_STANDALONE_NATIVE_ADAPTER)
// The standalone target uses a bare fake adapter. Its identity mapping is
// the production unwrap function's bare-adapter branch; WorkerAdapter unwrapping
// remains covered by the retained semantic-adapter fixture and full bridge.
namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(
    const game::GameAdapter &adapter) noexcept {
  return adapter;
}
} // namespace xar::ck3_12002
#endif

namespace {

namespace game = xar::game;
namespace mailbox_api = xar::ck3_11906;
namespace provider = xar::bridge::private_observer;
constexpr std::uint64_t kRevision = 701;
constexpr std::int32_t kDateRaw = 1'220'410;
std::string g_wire_json;

class FakeAdapter final : public game::GameAdapter {
public:
  game::AdapterDescriptor identity{
      "ck3-1.20.0.2-msvc-x64", "1.20.0.2",
      xar::ck3_12002::kCampaignRootContextV1ExecutableSha256, "fixture", {}};
  bool admitted = true;
  game::Snapshot snapshot;
  mutable std::atomic<std::size_t> snapshot_reads{0};

  FakeAdapter() {
    snapshot.date_raw = kDateRaw;
    snapshot.paused = true;
    snapshot.map_ready = true;
    snapshot.player_id = 1;
    snapshot.has_played_character = true;
    snapshot.played_character_id = 29'829;
    snapshot.played_character_alive = true;
  }
  const game::AdapterDescriptor &descriptor() const noexcept override {
    return identity;
  }
  bool enabled() const noexcept override { return admitted; }
  bool read_snapshot(game::Snapshot &output) const noexcept override {
    ++snapshot_reads;
    output = snapshot;
    return true;
  }

#define UNAVAILABLE(Type, Method, Arguments) \
  game::Type Method Arguments const noexcept override { \
    return game::Type::unavailable; \
  }
  UNAVAILABLE(PauseSubmitResult, submit_pause_map, (game::Snapshot *))
  UNAVAILABLE(ResumeSubmitResult, submit_resume_map, (game::Snapshot *))
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  UNAVAILABLE(SelectEventOptionResult, submit_select_event_option, (std::int32_t))
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override {
    return {};
  }
  UNAVAILABLE(ReplyPendingInteractionResult, submit_reply_to_pending_interaction,
              (game::PendingInteractionReply))
  UNAVAILABLE(RaiseTroopsResult, submit_raise_troops_default, ())
  UNAVAILABLE(MoveArmyResult, submit_move_army, (std::int32_t, std::int32_t))
  game::PreviewMoveArmyResult preview_move_army(
      std::int32_t, std::int32_t) const noexcept override { return {}; }
  UNAVAILABLE(DisbandArmyResult, submit_disband_army, (std::int32_t))
  UNAVAILABLE(SplitArmyHalfResult, submit_split_army_half, (std::int32_t))
  UNAVAILABLE(MergeArmiesResult, submit_merge_armies, (std::int32_t, std::int32_t))
  UNAVAILABLE(StartAssaultResult, submit_start_assault, (std::int32_t))
  UNAVAILABLE(StopAssaultResult, submit_stop_assault, (std::int32_t))
  bool read_declarable_wars(
      std::vector<game::DeclarableWarSnapshot> &) const noexcept override {
    return false;
  }
  UNAVAILABLE(ReadDeclarableWarsResult, read_declarable_wars_for_target,
              (std::int32_t, std::vector<game::DeclarableWarSnapshot> &))
  UNAVAILABLE(DeclareWarResult, submit_declare_war,
              (const game::DeclarableWarSnapshot &))
  UNAVAILABLE(ReadArrangeMarriageChoicesResult, read_arrange_marriage_choices,
              (std::vector<game::ArrangeMarriageChoice> &,
               game::ArrangeMarriageQueryDiagnostics &))
  UNAVAILABLE(ArrangeMarriageResult, submit_arrange_marriage,
              (const game::ArrangeMarriageChoice &))
  UNAVAILABLE(EnforceDemandsResult, submit_enforce_demands, (std::int32_t))
  UNAVAILABLE(ReadArmyStrengthsResult, read_army_strengths,
              (std::vector<game::ArmyStrengthSnapshot> &))
  UNAVAILABLE(ReadCombatSimulationInputsResult, read_combat_simulation_inputs,
              (const game::CombatSimulationInputsRequest &,
               game::CombatSimulationInputsSnapshot &))
  UNAVAILABLE(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3,
              (const game::CombatSimulationInputsRequest &,
               game::CombatSimulationInputsV3Snapshot &))
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

bool TestParserAndRejectedAdmission() {
  if (!xar::ck3_12002::IsGovernmentRuntimeAdapterQuery12002(
          "query-government-runtime-adapter-v1") ||
      xar::ck3_12002::IsGovernmentRuntimeAdapterQuery12002(
          "query-government-runtime-adapter-v1-extra")) {
    return false;
  }
  FakeAdapter adapter;
  mailbox_api::MainThreadQueryMailboxV1 mailbox;
  std::string serialized;
  std::string failure;
  adapter.admitted = false;
  if (xar::ck3_12002::ReadGovernmentRuntimeAdapterOnApplicationMain12002(
          adapter, mailbox, adapter.snapshot, kRevision, "disabled",
          serialized, failure) ||
      failure.empty() || mailbox.next_sequence.load() != 0) {
    return false;
  }
  adapter.admitted = true;
  adapter.identity.executable_sha256 = "unsupported";
  if (xar::ck3_12002::ReadGovernmentRuntimeAdapterOnApplicationMain12002(
          adapter, mailbox, adapter.snapshot, kRevision, "unsupported",
          serialized, failure) ||
      failure.empty() || mailbox.next_sequence.load() != 0) {
    return false;
  }
  adapter.identity.executable_sha256 =
      xar::ck3_12002::kCampaignRootContextV1ExecutableSha256;
  return !xar::ck3_12002::ReadGovernmentRuntimeAdapterOnApplicationMain12002(
             adapter, mailbox, adapter.snapshot, 0, "zero-revision",
             serialized, failure) &&
         !failure.empty() && mailbox.next_sequence.load() == 0;
}

void *g_tls_context = nullptr;
void *__fastcall FixtureTlsContext() noexcept { return g_tls_context; }

struct FixtureRuntime {
  std::array<std::byte, 0x28> tls{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x18> game_state{};
  std::uintptr_t jomini_slot = reinterpret_cast<std::uintptr_t>(jomini.data());
  std::uintptr_t game_slot = reinterpret_cast<std::uintptr_t>(game_state.data());
  std::uintptr_t rng_slot = 0;
  std::uint8_t initialized = 1;

  void Prepare(mailbox_api::MainThreadQueryMailboxV1 &mailbox) {
    tls[0x20] = std::byte{1};
    jomini[0x20] = std::byte{1};
    std::memcpy(game_state.data() + 0x08, &kDateRaw, sizeof(kDateRaw));
    g_tls_context = tls.data();
    mailbox.global_rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&rng_slot);
    mailbox.jomini_state_slot = reinterpret_cast<std::uintptr_t>(&jomini_slot);
    mailbox.game_state_slot = reinterpret_cast<std::uintptr_t>(&game_slot);
    mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter = &FixtureTlsContext;
    mailbox.executor_submission_enabled = true;
    mailbox.permitted_executor_government12002 =
        &provider::ExecuteGovernmentRuntimeAdapterPrivateOperationV1;
    mailbox.iat_hook_installed.store(true);
    mailbox.state.store(mailbox_api::MainThreadQueryMailboxStateV1::idle);
    const auto owner = GetCurrentThreadId();
    // Observe the actual deterministic application-main boundary, using only
    // memory owned by this fixture process. No IAT or desktop hook is installed.
    mailbox_api::ObserveMainThreadPumpAndDrainV1(
        mailbox, mailbox.pump_exact_return_rva, owner);
    mailbox_api::ObserveMainThreadPumpAndDrainV1(
        mailbox, mailbox.pump_exact_return_rva, owner);
  }
};

bool TestRealCallerAndMailboxTypedUnavailable() {
  FakeAdapter adapter;
  mailbox_api::MainThreadQueryMailboxV1 mailbox;
  FixtureRuntime runtime;
  runtime.Prepare(mailbox);
  std::atomic<bool> done{false};
  bool query_result = false;
  std::string failure;
  std::thread worker([&] {
    query_result =
        xar::ck3_12002::ReadGovernmentRuntimeAdapterOnApplicationMain12002(
            adapter, mailbox, adapter.snapshot, kRevision, "caller-fixture",
            g_wire_json, failure);
    done.store(true, std::memory_order_release);
  });
  bool drained = false;
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(5);
  while (!done.load(std::memory_order_acquire) &&
         std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) ==
        mailbox_api::MainThreadQueryMailboxStateV1::queued) {
      drained = mailbox_api::ObserveMainThreadPumpAndDrainV1(
          mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  g_tls_context = nullptr;
  // The current EXE is this test program and contains no native CK3 roots.
  // Reaching a typed collector failure proves the production caller executes
  // its registered provider and preserves wire identity through the mailbox.
  return drained && query_result && failure.empty() &&
         mailbox.executed_requests.load() == 1 &&
         mailbox.executor_started_requests.load() == 1 &&
         mailbox.state.load() == mailbox_api::MainThreadQueryMailboxStateV1::idle &&
         adapter.snapshot_reads.load() >= 1 &&
         g_wire_json.find("\"status\":\"unavailable\"") != std::string::npos &&
         g_wire_json.find("\"type\":\"command_result\"") != std::string::npos &&
         g_wire_json.find("\"accepted\":true") != std::string::npos &&
         g_wire_json.find("\"private_build\":true") != std::string::npos &&
         g_wire_json.find("\"read_only\":true") != std::string::npos &&
         g_wire_json.find("\"advertised\":false") != std::string::npos &&
         g_wire_json.find("\"snapshot_revision\":701") != std::string::npos &&
         g_wire_json.find("1.20.0.2") != std::string::npos;
}

} // namespace

int main(int argc, char **argv) {
  if (!TestParserAndRejectedAdmission()) {
    std::cerr << "government12002 caller admission: RED\n";
    return 1;
  }
  if (!TestRealCallerAndMailboxTypedUnavailable()) {
    std::cerr << "government12002 real caller mailbox typed response: RED\n";
    return 1;
  }
  if (argc == 3 && std::string_view(argv[1]) == "--wire-json") {
    std::ofstream output(argv[2], std::ios::binary);
    output << g_wire_json << '\n';
    if (!output) return 1;
  } else if (argc != 1) {
    return 2;
  }
  std::cout << "government12002 caller: GREEN (parser, disabled/unknown build, "
               "zero revision, actual queued provider, private metadata, "
               "typed unavailable, reclaim)\n";
  return 0;
}
