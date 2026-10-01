// Exercise the real production dispatcher only. Domain spies make no claim
// about native providers, command execution, or live CK3 qualification.
#include "xar_bridge/ck3_12002_nonwar_router.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/faction_gift_mitigation_async_glue_v1.hpp"
#include "active_scheme_sway_private_transport_v1.hpp"
#include "active_scheme_sway_formal_private_transport_v1.hpp"
#include "ck3_12002_activity_feast_router.hpp"

#include <array>
#include <cstdlib>
#include <iostream>

namespace {
using namespace xar;
using namespace xar::ck3_12002;
std::size_t checks = 0;
std::size_t gift_calls = 0;
std::size_t sway_calls = 0;
std::size_t prisoner_calls = 0;
std::size_t fallback_calls = 0;
void Check(bool value, const char *message) {
  ++checks;
  if (!value) {
    std::cerr << "router regression failed: " << message << '\n';
    std::abort();
  }
}

class RouterAdapter final : public game::GameAdapter {
public:
  const game::AdapterDescriptor &descriptor() const noexcept override {
    static const game::AdapterDescriptor value{
        "ck3-1.20.0.2-msvc-x64", "1.20.0.2", "router-fixture", "fixture", {}};
    return value;
  }
  bool enabled() const noexcept override { return true; }
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

struct ForwardedArguments {
  const game::GameAdapter *adapter = nullptr;
  ck3_11906::MainThreadQueryMailboxV1 *mailbox = nullptr;
  const game::Snapshot *published = nullptr;
  NonwarPrivateState12002 *state = nullptr;
  std::uint64_t revision = 0;
  std::string_view step{}, payload{}, request_id{};
} expected;

void CheckForwarded(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload,
    std::string_view request_id, const std::string &serialized,
    const std::string &failure) {
  Check(&adapter == expected.adapter, "native adapter identity");
  Check(&mailbox == expected.mailbox, "mailbox identity");
  Check(&published == expected.published, "snapshot identity");
  Check(revision == expected.revision, "published revision");
  Check(step == expected.step, "canonical selector");
  Check(payload == expected.payload, "request payload");
  Check(request_id == expected.request_id, "request identity");
  Check(serialized.empty() && failure.empty(), "outputs cleared before dispatch");
}

constexpr std::array<std::string_view, 4> gift_steps{
    "private-query-faction-gift-member-v1",
    "private-submit-faction-gift-member-v1",
    "private-query-faction-gift-receipt-v1",
    "private-query-faction-gift-cold-recovery-v1"};
constexpr std::array<std::string_view, 3> sway_steps{
    "query-active-scheme-sway-target-v1-private-43699",
    "submit-active-scheme-sway-v1-private-43699",
    "receipt-active-scheme-sway-v1-private-43699"};
constexpr std::array<std::string_view, 3> prisoner_steps{
    "query-player-prisoner-collection-private-v1",
    "submit-player-prisoner-ransom-private-v1",
    "query-war-prisoner-release-pairs-v1-83886083"};
} // namespace

namespace xar::ck3_12002 {
// The test supplies a direct synthetic adapter, so no WorkerAdapter or native
// snapshot implementation is linked or invoked.
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept {
  return adapter;
}
bool IsActivityFeastPrivateStep12002(std::string_view) noexcept { return false; }
bool HandleActivityFeastPrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &,
    std::uint64_t, std::string_view, std::string_view, std::string_view,
    std::string &, std::string &, bridge::ActivityCostSlot12ObserverV1 *,
    bridge::ActivityGuestRuleProvenanceObserverV1 *) noexcept {
  ++fallback_calls;
  return false;
}

#if defined(XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1)
bool ExecuteFactionGiftPrivateMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandleFactionGiftPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    FactionGiftPrivateState12002 &state, std::string &serialized,
    std::string &failure, const FactionGiftPrivateFixtureBindings12002 *bindings) noexcept {
  CheckForwarded(adapter, mailbox, published, revision, step, payload,
                 request_id, serialized, failure);
  Check(&state == &expected.state->gift, "persistent gift ledger identity");
  Check(bindings == nullptr, "production default domain binding");
  Check(state.action_may_have_submitted, "prior gift pending flag retained");
  Check(state.claimed_idempotency_keys.contains("prior-gift"), "prior gift claim retained");
  Check(state.claimed_idempotency_keys.size() == gift_calls + 1, "gift ledger retained between requests");
  state.claimed_idempotency_keys.emplace(step);
  ++gift_calls;
  serialized = "gift-forwarded";
  return true;
}
#endif

#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
bool ExecuteActiveSwayMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandleActiveSwayPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    ActiveSwayState12002 &state, std::string &serialized, std::string &failure) noexcept {
  CheckForwarded(adapter, mailbox, published, revision, step, payload,
                 request_id, serialized, failure);
  Check(&state == &expected.state->sway, "persistent Sway ledger identity");
  Check(state.may_have_submitted, "prior Sway pending flag retained");
  ++sway_calls;
  serialized = "sway-forwarded";
  return true;
}
#endif

#if defined(XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1)
bool ExecutePlayerPrisonerCollection12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
#if defined(XAR_CK3_ENABLE_G2_PRISONER_RANSOM_ACTION_PRIVATE_V1)
bool ExecutePlayerPrisonerRansom12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
#endif
bool HandlePlayerPrisonerPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    PrisonerPrivateWorkerState12002 &state, std::string &serialized,
    std::string &failure) {
  CheckForwarded(adapter, mailbox, published, revision, step, payload,
                 request_id, serialized, failure);
  Check(&state == &expected.state->prisoner, "persistent prisoner ledger identity");
  Check(state.may_have_submitted, "prior prisoner pending flag retained");
  Check(state.query_sequence == 17 + prisoner_calls,
        "prisoner ledger retained between collection/action/release requests");
  Check(state.war_query_sequence == 29 && state.quote_revision == 888 &&
        state.quote_query_sequence == 21, "prisoner query and quote state retained");
  ++state.query_sequence;
  ++prisoner_calls;
  serialized = "prisoner-forwarded";
  return true;
}
#endif
} // namespace xar::ck3_12002

int main() {
  using namespace xar;
  using namespace xar::ck3_12002;
  RouterAdapter adapter;
  ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  game::Snapshot published{};
  published.date_raw = 53175816;
  published.played_character_id = 29829;
  NonwarPrivateState12002 state{};
  state.faction_query_sequence = 42;
  NonwarMailboxExecutorsV1 executors{};
  PopulateNonwarRouterExecutors12002(executors);
#if defined(XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1)
  state.gift.action_may_have_submitted = true;
  state.gift.claimed_idempotency_keys.emplace("prior-gift");
  Check(executors.faction_gift == &ExecuteFactionGiftPrivateMailbox12002, "gift callback registered");
#else
  Check(executors.faction_gift == nullptr, "default gift callback absent");
#endif
  // Release-pairs shares the existing collection callback and worker state;
  // it does not add a general war executor or duplicate quote ledger.
#if defined(XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1)
  state.prisoner.may_have_submitted = true;
  state.prisoner.query_sequence = 17;
  state.prisoner.war_query_sequence = 29;
  state.prisoner.quote_revision = 888;
  state.prisoner.quote_query_sequence = 21;
  Check(executors.prisoner_collection == &ExecutePlayerPrisonerCollection12002,
        "prisoner collection/release callback registered");
#if defined(XAR_CK3_ENABLE_G2_PRISONER_RANSOM_ACTION_PRIVATE_V1)
  Check(executors.prisoner_ransom == &ExecutePlayerPrisonerRansom12002,
        "prisoner ransom callback registered");
#else
  Check(executors.prisoner_ransom == nullptr, "disabled prisoner ransom callback absent");
#endif
#else
  Check(executors.prisoner_collection == nullptr && executors.prisoner_ransom == nullptr,
        "default prisoner callbacks absent");
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  state.sway.may_have_submitted = true;
  Check(executors.sway_state == &ExecuteActiveSwayMailbox12002, "Sway query callback registered");
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1)
  Check(executors.sway_action == &ExecuteActiveSwayMailbox12002, "Sway formal callback registered");
#else
  Check(executors.sway_action == nullptr, "disabled Sway formal callback absent");
#endif
#else
  Check(executors.sway_state == nullptr && executors.sway_action == nullptr,
        "default Sway callbacks absent");
#endif
  Check(executors.council == nullptr && executors.law_action == nullptr &&
        executors.feast_open == nullptr && executors.factions == nullptr &&
        executors.government == nullptr, "unselected domain callbacks absent");
  Check(gift_steps[0] == ck3_11906::kFactionGiftPrivateQueryStepV1 &&
        gift_steps[1] == ck3_11906::kFactionGiftPrivateSubmitStepV1 &&
        gift_steps[2] == ck3_11906::kFactionGiftPrivateReceiptStepV1 &&
        gift_steps[3] == ck3_11906::kFactionGiftPrivateColdRecoveryStepV1,
        "gift callers use production constants");

  const auto exercise = [&](std::string_view step, bool enabled,
                            std::string_view expected_output) {
    Check(IsNonwarPrivateStep12002(step) == enabled, "canonical selector visibility");
    const std::string payload = "{\"persistent_action_id\":\"already-pending\"}";
    const std::string request_id = "router-request-" + std::to_string(checks);
    expected = {&adapter, &mailbox, &published, &state, 916, step, payload, request_id};
    std::string serialized = "stale-output", failure = "stale-failure";
    const bool handled = HandleNonwarPrivate12002(adapter, mailbox, published,
        916, step, payload, request_id, state, serialized, failure);
    Check(handled == enabled, "canonical selector dispatch result");
    Check(serialized == expected_output, "domain result returned unchanged");
    Check(failure.empty(), "domain failure returned unchanged");
    Check(state.faction_query_sequence == 42, "unrelated persistent sequence retained");
  };
  for (const auto step : gift_steps) {
#if defined(XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1)
    exercise(step, true, "gift-forwarded");
#else
    exercise(step, false, "");
#endif
  }
  for (const auto step : prisoner_steps) {
#if defined(XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1)
    exercise(step, true, "prisoner-forwarded");
#else
    exercise(step, false, "");
#endif
  }
  for (std::size_t index = 0; index != sway_steps.size(); ++index) {
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1)
    exercise(sway_steps[index], true, "sway-forwarded");
#else
    if (index == 0) exercise(sway_steps[index], true, "sway-forwarded");
    else Check(!IsNonwarPrivateStep12002(sway_steps[index]),
               "disabled Sway formal selector not selected");
#endif
  Check(prisoner_calls ==
#if defined(XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1)
        3,
#else
        0,
#endif
        "prisoner selectors obey the selected build flag");
#else
    exercise(sway_steps[index], false, "");
#endif
  }
  exercise("query-unregistered-router-fixture", false, "");
  Check(!IsNonwarPrivateStep12002("query-active-scheme-sway-v1-private-43699"),
        "obsolete Sway query prefix not selected");
  PollNonwarPrivateState12002(state);
#if defined(XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1)
  Check(gift_calls == 4 && state.gift.claimed_idempotency_keys.size() == 5,
        "all four gift selectors forwarded to the persistent ledger");
#else
  Check(gift_calls == 0, "default build invokes no gift domain");
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1) && defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1)
  Check(sway_calls == 3, "all three Sway selectors forwarded");
#elif defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  Check(sway_calls == 1, "query-only Sway build forwards only the query");
#else
  Check(sway_calls == 0, "default build invokes no Sway domain");
#endif
  std::cout << "{\"status\":\"GREEN\",\"checks\":" << checks
            << ",\"gift_selectors_forwarded\":" << gift_calls
            << ",\"sway_selectors_forwarded\":" << sway_calls
            << ",\"prisoner_selectors_forwarded\":" << prisoner_calls
            << ",\"fallback_calls\":" << fallback_calls
            << ",\"live_verified\":false,\"ck3_touched\":false}\n";
}
