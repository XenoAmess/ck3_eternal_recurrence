// Real actual4 router -> real Sway Handler; stale revision ends before bindings/queue.
#include "xar_bridge/ck3_12002_nonwar_router.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/ck3_12002_sway_mailbox.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12004_sway.hpp"
#include "xar_bridge/ck3_12004_sway_stop.hpp"
#include "active_scheme_sway_private_transport_v1.hpp"
#include "active_scheme_sway_formal_private_transport_v1.hpp"
#include "ck3_12002_activity_feast_router.hpp"
#include <array>
#include <cstdlib>
#include <iostream>
#include <string>

namespace native = xar::ck3_12002;
namespace api = xar::ck3_11906;
namespace game = xar::game;
namespace {
int checks = 0, failures = 0, infrastructure_calls = 0;
void Verify(bool value, const char *message) {
  ++checks;
  if (!value) { ++failures; std::cerr << "FAILED: " << message << '\n'; }
}
[[noreturn]] void Forbidden() noexcept { ++infrastructure_calls; std::abort(); }

class RouterAdapter final : public game::GameAdapter {
public:
  game::AdapterDescriptor identity{xar::ck3_12004::kAdapterId, xar::ck3_12004::kGameVersion, xar::ck3_12004::kExecutableSha256, "router-fixture", {}};
  bool available = true;
  const game::AdapterDescriptor &descriptor() const noexcept override { return identity; }
  bool enabled() const noexcept override { return available; }
  bool read_snapshot(game::Snapshot &) const noexcept override { return false; }
#define XAR_R0(T, M) game::T M() const noexcept override { return {}; }
#define XAR_R1(T, M, A) game::T M(A) const noexcept override { return {}; }
#define XAR_R2(T, M, A, B) game::T M(A, B) const noexcept override { return {}; }
  XAR_R1(PauseSubmitResult, submit_pause_map, game::Snapshot *)
  XAR_R1(ResumeSubmitResult, submit_resume_map, game::Snapshot *)
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  XAR_R1(SelectEventOptionResult, submit_select_event_option, std::int32_t)
  XAR_R0(SaveCheckpointResult, submit_save_checkpoint)
  XAR_R1(ReplyPendingInteractionResult, submit_reply_to_pending_interaction, game::PendingInteractionReply)
  XAR_R0(RaiseTroopsResult, submit_raise_troops_default)
  XAR_R2(MoveArmyResult, submit_move_army, std::int32_t, std::int32_t)
  XAR_R2(PreviewMoveArmyResult, preview_move_army, std::int32_t, std::int32_t)
  XAR_R1(DisbandArmyResult, submit_disband_army, std::int32_t)
  XAR_R1(SplitArmyHalfResult, submit_split_army_half, std::int32_t)
  XAR_R2(MergeArmiesResult, submit_merge_armies, std::int32_t, std::int32_t)
  XAR_R1(StartAssaultResult, submit_start_assault, std::int32_t)
  XAR_R1(StopAssaultResult, submit_stop_assault, std::int32_t)
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &) const noexcept override { return false; }
  XAR_R2(ReadDeclarableWarsResult, read_declarable_wars_for_target, std::int32_t, std::vector<game::DeclarableWarSnapshot> &)
  XAR_R1(DeclareWarResult, submit_declare_war, const game::DeclarableWarSnapshot &)
  XAR_R2(ReadArrangeMarriageChoicesResult, read_arrange_marriage_choices, std::vector<game::ArrangeMarriageChoice> &, game::ArrangeMarriageQueryDiagnostics &)
  XAR_R1(ArrangeMarriageResult, submit_arrange_marriage, const game::ArrangeMarriageChoice &)
  XAR_R1(EnforceDemandsResult, submit_enforce_demands, std::int32_t)
  XAR_R1(ReadArmyStrengthsResult, read_army_strengths, std::vector<game::ArmyStrengthSnapshot> &)
  XAR_R2(ReadCombatSimulationInputsResult, read_combat_simulation_inputs, const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &)
  XAR_R2(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3, const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &)
  XAR_R2(ReadWarTerminationOptionsResult, read_war_termination_options, std::int32_t, game::WarTerminationOptionsSnapshot &)
  XAR_R2(ReadWarTerminationTermsResult, read_war_termination_terms, std::int32_t, game::WarTerminationTermsSnapshot &)
  XAR_R2(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms, std::int32_t, game::WarTerminationExitTermsSnapshot &)
  XAR_R1(SurrenderWarResult, submit_surrender_war, std::int32_t)
  XAR_R1(OfferWhitePeaceResult, submit_offer_white_peace, std::int32_t)
#undef XAR_R0
#undef XAR_R1
#undef XAR_R2
};


void CheckCanonicalTargets(const xar::game::GameAdapter &adapter) {
  using namespace xar::ck3_11906;
  using namespace xar::ck3_12002;
  MainThreadQueryMailboxV1 mailbox{};
  NonwarPrivateState12002 state{};
  xar::game::Snapshot published{};
  published.paused = true;
  published.map_ready = true;
  published.has_played_character = true;
  published.played_character_alive = true;
  published.played_character_id = 17;
  const std::uint64_t revision = 7;
  const std::string payload = R"({"expected_revision":6})";
  const std::string request_id = "req";
  std::string serialized, failure;

  const std::string_view prefixes[] = {
    "query-active-scheme-sway-target-v1-private-",
    "submit-active-scheme-sway-v1-private-",
    "receipt-active-scheme-sway-v1-private-"
  };
  const std::int32_t targets[] = {0, -2, 23, -2147483648, 2147483647};

  for (std::size_t p = 0; p < 3; ++p) {
    for (std::int32_t t : targets) {
      std::string step = std::string(prefixes[p]) + std::to_string(t);
      bool recognized = false;
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
      if (p == 0) recognized = true;
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1)
      if (p == 1 || p == 2) recognized = true;
#endif
#endif
      if (recognized) {
        Verify(IsNonwarPrivateStep12004(adapter, step), "classifier should recognize valid target");
        Verify(!HandleNonwarPrivate12002(adapter, mailbox, published, revision, step, payload, request_id, state, serialized, failure), "handle should reject stale revision");
        Verify(serialized.empty(), "serialized must be empty on rejection");
        Verify(failure == "sway frame or request invalid", "exact failure expected");
      } else {
        Verify(!IsNonwarPrivateStep12004(adapter, step), "classifier should reject disabled family");
        Verify(!HandleNonwarPrivate12002(adapter, mailbox, published, revision, step, payload, request_id, state, serialized, failure), "handle should fail");
        Verify(serialized.empty(), "serialized must be empty");
        Verify(failure.empty(), "failure must be empty on router rejection");
      }
    }
  }

  const std::string_view bad_suffixes[] = {
    "-1", "-0", "00", "01", "-02", "+2", "2147483648", "-2147483649", "4294967294", "1.0", "true", "abc", ""
  };
  for (std::size_t p = 0; p < 3; ++p) {
    for (std::string_view s : bad_suffixes) {
      std::string step = std::string(prefixes[p]) + std::string(s);
      Verify(!IsNonwarPrivateStep12004(adapter, step), "classifier must reject invalid suffix");
      Verify(!HandleNonwarPrivate12002(adapter, mailbox, published, revision, step, payload, request_id, state, serialized, failure), "handle must fail");
      Verify(serialized.empty(), "serialized must be empty");
      Verify(failure.empty(), "failure must be empty on router rejection");
    }
  }
}


void CheckLegacyAndScope() {
  RouterAdapter adapter;
  constexpr std::array<std::string_view, 3> prefixes{
      "query-active-scheme-sway-target-v1-private-",
      "submit-active-scheme-sway-v1-private-",
      "receipt-active-scheme-sway-v1-private-"};
  for (const auto prefix : prefixes) {
    adapter.available = false;
    Verify(!native::IsNonwarPrivateStep12004(adapter, std::string(prefix) + "23"), "disabled actual4 remains invisible");
    adapter.available = true;
    adapter.identity.game_version = "1.20.0.2";
    adapter.identity.adapter_id = "ck3-1.20.0.2-msvc-x64";
    adapter.identity.executable_sha256 = native::kExecutableSha256;
    Verify(!native::IsNonwarPrivateStep12004(adapter, std::string(prefix) + "0"), ".2 does not enter .4 classifier");
    adapter.identity = {xar::ck3_12003::kAdapterId, xar::ck3_12003::kGameVersion,
        xar::ck3_12003::kExecutableSha256, "router-fixture", {}};
    Verify(!native::IsNonwarPrivateStep12004(adapter, std::string(prefix) + "-2"), ".3 does not enter .4 classifier");
    adapter.identity = {xar::ck3_12004::kAdapterId, xar::ck3_12004::kGameVersion,
        xar::ck3_12004::kExecutableSha256, "router-fixture", {}};
  }
  Verify(!native::IsNonwarPrivateStep12004(adapter, "query-sway-outcome-event-v1-private"), "Event route remains absent");
  Verify(!native::IsNonwarPrivateStep12004(adapter, "query-sway-completion-invalidation-reason-v1-private"), "invalidation route remains absent from .4");
  std::uint32_t target = 0;
  Verify(!api::ParseActiveSchemeSwayPrivateQueryStepV1(std::string(prefixes[0]) + "0", target), "actual legacy query parser still rejects zero");
  Verify(!api::ParseActiveSchemeSwayPrivateQueryStepV1(std::string(prefixes[0]) + "-2", target), "actual legacy query parser still rejects signed negative");
  Verify(api::ParseActiveSchemeSwayPrivateQueryStepV1(std::string(prefixes[0]) + "4294967294", target) && target == 4294967294U, "actual legacy query parser keeps uint32 domain");
  api::ActiveSchemeSwayFormalModeV1 mode{};
  for (std::size_t index = 1; index != prefixes.size(); ++index) {
    Verify(!api::ParseActiveSchemeSwayFormalStepV1(std::string(prefixes[index]) + "0", mode, target), "actual legacy formal parser still rejects zero");
    Verify(!api::ParseActiveSchemeSwayFormalStepV1(std::string(prefixes[index]) + "-2", mode, target), "actual legacy formal parser still rejects signed negative");
    Verify(api::ParseActiveSchemeSwayFormalStepV1(std::string(prefixes[index]) + "4294967294", mode, target) && target == 4294967294U, "actual legacy formal parser keeps uint32 domain");
  }
}
} // namespace

// Exact fail-closed seams exist only to link the real Handler before its stale
// revision exit. Any binding, queue, serializer or unrelated handler entry aborts.
namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept { return adapter; }
bool IsActivityFeastPrivateStep12002(std::string_view) noexcept { return false; }
bool HandleActivityFeastPrivate12002(const game::GameAdapter &, api::MainThreadQueryMailboxV1 &,
    const game::Snapshot &, std::uint64_t, std::string_view, std::string_view, std::string_view,
    std::string &, std::string &, bridge::ActivityCostSlot12ObserverV1 *, bridge::ActivityGuestRuleProvenanceObserverV1 *) noexcept { Forbidden(); }
SwayStateBindings12002 BindSwayStateImage12002(std::uintptr_t, std::string_view) noexcept { Forbidden(); }
SwayCommandBindingsV1 BindSwayCommandImage(std::uintptr_t, std::string_view) noexcept { Forbidden(); }
bool ExecuteActiveSwayMailbox12002(void *, const api::MainThreadExecutionStampV1 &) noexcept { Forbidden(); }
std::string SerializeActiveSwayRead12002(const ActiveSwayMailboxContext12002 &) { Forbidden(); }
std::string SerializeActiveSwayFormal12002(const ActiveSwayMailboxContext12002 &) { Forbidden(); }
std::string SerializeActiveSwayEnvelope12002(const ActiveSwayMailboxContext12002 &, std::string_view, std::string_view) { Forbidden(); }
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
#define XAR_EXECUTOR_STUB(NAME) bool NAME(void *, const api::MainThreadExecutionStampV1 &) noexcept { Forbidden(); }
XAR_EXECUTOR_STUB(ExecuteSwayCompletionMailboxV1)
XAR_EXECUTOR_STUB(ExecuteSwayCompletionExecutionMailboxV1)
XAR_EXECUTOR_STUB(ExecuteSwayCompletionTerminationMailboxV1)
XAR_EXECUTOR_STUB(ExecuteSwayCompletionInvalidationReasonMailboxV1)
#undef XAR_EXECUTOR_STUB
bool HandleSwayCompletionV1(const game::GameAdapter &, api::MainThreadQueryMailboxV1 &, const game::Snapshot &,
    std::uint64_t, std::string_view, std::string_view, std::string_view, std::string &, std::string &) noexcept { Forbidden(); }
#define XAR_RECORDER_HANDLER_STUB(NAME, RECORDER) \
  bool NAME(const game::GameAdapter &, api::MainThreadQueryMailboxV1 &, const RECORDER &, const game::Snapshot &, \
      std::uint64_t, std::string_view, std::string_view, std::string_view, std::string &, std::string &) noexcept { Forbidden(); }
XAR_RECORDER_HANDLER_STUB(HandleSwayCompletionExecutionV1, SwayExecutionRecorder12002)
XAR_RECORDER_HANDLER_STUB(HandleSwayCompletionTerminationV1, SwayTerminationRecorder12002)
XAR_RECORDER_HANDLER_STUB(HandleSwayCompletionInvalidationReasonV1, SwayInvalidationReasonRecorder12002)
#undef XAR_RECORDER_HANDLER_STUB
#endif
} // namespace xar::ck3_12002
namespace xar::ck3_12004 {
ck3_12002::SwayStateBindings12002 BindSwayStateImage12004(std::uintptr_t, std::string_view) noexcept { Forbidden(); }
ck3_12002::SwayCommandBindingsV1 BindSwayCommandImage12004(std::uintptr_t, std::string_view) noexcept { Forbidden(); }
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
bool ExecuteSwayTerminalMailbox12004(void *, const api::MainThreadExecutionStampV1 &) noexcept { Forbidden(); }
bool HandleSwayTerminal12004(const game::GameAdapter &, api::MainThreadQueryMailboxV1 &, const game::Snapshot &,
    std::uint64_t, std::string_view, std::string_view, std::string_view, std::string &, std::string &) noexcept { Forbidden(); }
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1)
bool ExecuteSelectedSwayStop12004(void *, const api::MainThreadExecutionStampV1 &) noexcept { Forbidden(); }
bool HandleSelectedSwayStop12004(const game::GameAdapter &, api::MainThreadQueryMailboxV1 &, const game::Snapshot &,
    std::uint64_t, std::string_view, std::string_view, std::string_view, std::string &, std::string &) noexcept { Forbidden(); }
#endif
#endif
} // namespace xar::ck3_12004
namespace xar::ck3_11906 {
MainThreadQuerySubmitResultV1 TrySubmitMainThreadQueryV1(MainThreadQueryMailboxV1 &, MainThreadQueryExecutorV1,
    void *, MainThreadQueryTicketV1 &, MainThreadQueryQueuedWakeTraceV1 *) noexcept { Forbidden(); }
MainThreadQueryWaitResultV1 WaitForMainThreadQueryV1(MainThreadQueryMailboxV1 &, const MainThreadQueryTicketV1 &,
    std::uint32_t, MainThreadQueryQueuedWakeTraceV1 *, std::uint32_t) noexcept { Forbidden(); }
MainThreadQueryReclaimResultV1 ReclaimMainThreadQueryV1(MainThreadQueryMailboxV1 &, const MainThreadQueryTicketV1 &) noexcept { Forbidden(); }
} // namespace xar::ck3_11906

int main() {
  RouterAdapter adapter;
  CheckCanonicalTargets(adapter);
  CheckLegacyAndScope();
  Verify(infrastructure_calls == 0, "all image/queue/unrelated-handler seams remain uncalled");
  std::cout << "CHECKS " << checks << " FAILED " << failures
      << " actual4-router+real-Handler stale-revision; image/queue/Game NOT_RUN\n";
  return failures == 0 ? 0 : 1;
}
