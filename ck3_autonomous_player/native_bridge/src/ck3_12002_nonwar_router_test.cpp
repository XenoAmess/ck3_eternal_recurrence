// Exercise the real production dispatcher only. Domain spies make no claim
// about native providers, command execution, or live CK3 qualification.
#include "xar_bridge/ck3_12002_nonwar_router.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/faction_gift_mitigation_async_glue_v1.hpp"
#include "active_scheme_sway_private_transport_v1.hpp"
#include "active_scheme_sway_formal_private_transport_v1.hpp"
#include "ck3_12002_activity_feast_router.hpp"
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_religion_mailbox.hpp"
#endif

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
std::size_t religion_calls = 0;
std::size_t fallback_calls = 0;
std::array<std::size_t, 3> r5_calls{};
[[maybe_unused]] const void *expected_sway_termination_recorder = nullptr;
constexpr std::array<std::string_view, 3> r5_steps{
    "query-player-religion-conversion-outcome-v1",
    "query-player-religion-numeric-special-parameters-v1",
    "query-sway-completion-termination-v1-private"};
constexpr std::array<std::string_view, 3> r5_outputs{
    "conversion-outcome-forwarded", "numeric-special-parameters-forwarded",
    "sway-termination-forwarded"};
std::array<std::size_t, 6> r4_calls{};
[[maybe_unused]] const void *expected_sway_execution_recorder = nullptr;
constexpr std::array<std::string_view, 6> r4_steps{
    "query-player-epidemic-treatment-presence-v1",
    "query-player-epidemic-recovery-v1",
    "query-player-religion-conversion-reasons-v1",
    "query-sway-completion-execution-v1-private",
    "query-player-religion-reform-context-v1",
    "query-player-religion-doctrine-catalogue-v1"};
constexpr std::string_view recovery_title_step =
    "query-player-epidemic-recovery-v1-title-50331653";
constexpr std::array<std::string_view, 6> r4_outputs{
    "epidemic-treatment-forwarded", "epidemic-recovery-forwarded",
    "conversion-reasons-forwarded", "sway-execution-forwarded",
    "reform-context-forwarded", "doctrine-catalogue-forwarded"};
std::array<std::size_t, 11> readonly_calls{};
constexpr std::array<std::string_view, 11> readonly_steps{
    "query-player-rite-governance-v1",
    "query-player-clergy-appointment-v1",
    "query-player-religion-conversion-terms-v1",
    "query-player-religion-doctrines-v1",
    "query-player-religion-hostility-v1",
    "query-player-religion-doctrine-knowledge-v1",
    "query-player-religion-tenets-v1",
    "query-player-rite-members-v1",
    "query-player-religion-conversion-choices-v1",
    "query-player-religion-conversion-inputs-v1",
    "query-sway-completion-v1-private"};
constexpr std::array<std::string_view, 11> readonly_outputs{
    "rite-governance-forwarded", "clergy-forwarded", "conversion-terms-forwarded",
    "doctrines-forwarded", "hostility-forwarded", "doctrine-knowledge-forwarded",
    "tenets-forwarded", "rite-members-forwarded", "conversion-choices-forwarded",
    "conversion-inputs-forwarded", "sway-completion-forwarded"};
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

// Distinct readonly spies verify exact central domain selection and raw forwarding.
[[maybe_unused]] bool ReadonlySpy(std::size_t index,
    const game::GameAdapter &adapter, ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) {
  CheckForwarded(adapter, mailbox, published, revision, step, payload,
                 request_id, serialized, failure);
  Check(step == readonly_steps[index], "readonly handler matches its exact selector");
  ++readonly_calls[index];
  serialized = readonly_outputs[index];
  return true;
}

[[maybe_unused]] bool R4ReadonlySpy(std::size_t index,
    const game::GameAdapter &adapter, ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) {
  CheckForwarded(adapter, mailbox, published, revision, step, payload,
                 request_id, serialized, failure);
  Check(step == r4_steps[index] || (index == 1 && step == recovery_title_step),
        "R4 readonly handler matches its exact canonical selector");
  ++r4_calls[index];
  serialized = r4_outputs[index];
  return true;
}

[[maybe_unused]] bool R5ReadonlySpy(std::size_t index,
    const game::GameAdapter &adapter, ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) {
  CheckForwarded(adapter, mailbox, published, revision, step, payload,
                 request_id, serialized, failure);
  Check(step == r5_steps[index], "R5 readonly handler matches its exact canonical selector");
  ++r5_calls[index];
  serialized = r5_outputs[index];
  return true;
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

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1)
bool IsPlayerReligionPrivateStep12002(std::string_view step) noexcept {
  return step == kPlayerReligionPrivateStep12002;
}
bool ExecutePlayerReligionMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandlePlayerReligionPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  CheckForwarded(adapter, mailbox, published, revision, step, payload,
                 request_id, serialized, failure);
  ++religion_calls;
  serialized = "religion-forwarded";
  return true;
}
#endif

// R3 readonly domain spies: production providers are deliberately not linked.
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1)
bool IsPlayerRiteGovernancePrivateStep12002(std::string_view step) noexcept {
  return step == readonly_steps[0];
}
bool ExecutePlayerRiteGovernanceMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandlePlayerRiteGovernancePrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  return ReadonlySpy(0, adapter, mailbox, published, revision, step, payload,
                     request_id, serialized, failure);
}
#endif

#if defined(XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1)
bool IsPlayerClergyAppointmentPrivateStep12002(std::string_view step) noexcept {
  return step == readonly_steps[1];
}
bool ExecutePlayerClergyAppointmentMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandlePlayerClergyAppointmentPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  return ReadonlySpy(1, adapter, mailbox, published, revision, step, payload,
                     request_id, serialized, failure);
}
#endif

#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
bool IsPlayerReligionConversionTermsPrivateStep12002(std::string_view step) noexcept {
  return step == readonly_steps[2];
}
bool ExecutePlayerReligionConversionTermsMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandlePlayerReligionConversionTermsPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  return ReadonlySpy(2, adapter, mailbox, published, revision, step, payload,
                     request_id, serialized, failure);
}
#endif

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1)
bool IsPlayerReligionDoctrinesPrivateStep12002(std::string_view step) noexcept {
  return step == readonly_steps[3];
}
bool ExecutePlayerReligionDoctrinesMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandlePlayerReligionDoctrinesPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  return ReadonlySpy(3, adapter, mailbox, published, revision, step, payload,
                     request_id, serialized, failure);
}
#endif

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_HOSTILITY_PRIVATE_QUERY_V1)
bool IsPlayerReligionHostilityPrivateStep12002(std::string_view step) noexcept {
  return step == readonly_steps[4];
}
bool ExecutePlayerReligionHostilityMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandlePlayerReligionHostilityPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  return ReadonlySpy(4, adapter, mailbox, published, revision, step, payload,
                     request_id, serialized, failure);
}
#endif

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1)
bool IsPlayerReligionDoctrineKnowledgePrivateStep12002(std::string_view step) noexcept {
  return step == readonly_steps[5];
}
bool ExecutePlayerReligionDoctrineKnowledgeMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandlePlayerReligionDoctrineKnowledgePrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  return ReadonlySpy(5, adapter, mailbox, published, revision, step, payload,
                     request_id, serialized, failure);
}
#endif

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1)
bool IsPlayerReligionTenetsPrivateStep12002(std::string_view step) noexcept {
  return step == readonly_steps[6];
}
bool ExecutePlayerReligionTenetsMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandlePlayerReligionTenetsPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  return ReadonlySpy(6, adapter, mailbox, published, revision, step, payload,
                     request_id, serialized, failure);
}
#endif

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1)
bool IsPlayerRiteMembersPrivateStep12002(std::string_view step) noexcept {
  return step == readonly_steps[7];
}
bool ExecutePlayerRiteMembersMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandlePlayerRiteMembersPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  return ReadonlySpy(7, adapter, mailbox, published, revision, step, payload,
                     request_id, serialized, failure);
}
#endif

#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
bool IsPlayerReligionConversionChoicesPrivateStep12002(std::string_view step) noexcept {
  return step == readonly_steps[8];
}
bool ExecutePlayerReligionConversionChoicesMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandlePlayerReligionConversionChoicesPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  return ReadonlySpy(8, adapter, mailbox, published, revision, step, payload,
                     request_id, serialized, failure);
}
#endif

#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
bool IsPlayerReligionConversionInputsPrivateStep12002(std::string_view step) noexcept {
  return step == readonly_steps[9];
}
bool ExecutePlayerReligionConversionInputsMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandlePlayerReligionConversionInputsPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  return ReadonlySpy(9, adapter, mailbox, published, revision, step, payload,
                     request_id, serialized, failure);
}
#endif

#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
bool ExecuteSwayCompletionMailboxV1(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandleSwayCompletionV1(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  return ReadonlySpy(10, adapter, mailbox, published, revision, step, payload,
                     request_id, serialized, failure);
}
#endif

// R4 six readonly domain spies: real domain parsers remain provider-fixture owned.
#if defined(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_TREATMENT_PRIVATE_QUERY_V1)
bool IsPlayerEpidemicTreatmentPrivateStep12002(std::string_view step) noexcept {
  return step == r4_steps[0];
}
bool ExecutePlayerEpidemicTreatmentMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandlePlayerEpidemicTreatmentPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure,
    const TreatmentPresenceBindings12002 *fixture_bindings) noexcept {
  Check(fixture_bindings == nullptr, "treatment production dispatch uses default native binding");
  return R4ReadonlySpy(0, adapter, mailbox, published, revision, step, payload,
                       request_id, serialized, failure);
}
#endif

#if defined(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_RECOVERY_PRIVATE_QUERY_V1)
bool IsEpidemicRecoveryPrivate12002(std::string_view step) noexcept {
  return step == r4_steps[1] || step == recovery_title_step;
}
bool ExecutePlayerEpidemicRecoveryMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandleEpidemicRecoveryPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  return R4ReadonlySpy(1, adapter, mailbox, published, revision, step, payload,
                       request_id, serialized, failure);
}
#endif

#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
bool IsPlayerReligionConversionReasonsPrivateStep12002(std::string_view step) noexcept {
  return step == r4_steps[2];
}
bool ExecutePlayerReligionConversionReasonsMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandlePlayerReligionConversionReasonsPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  return R4ReadonlySpy(2, adapter, mailbox, published, revision, step, payload,
                       request_id, serialized, failure);
}
#endif

#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
bool ExecuteSwayCompletionExecutionMailboxV1(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandleSwayCompletionExecutionV1(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const SwayExecutionRecorder12002 &recorder,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  Check(&recorder == expected_sway_execution_recorder,
        "Sway execution receives the fixture-owned long-lived recorder identity");
  Check(expected.state->sway_execution_recorder == &recorder,
        "Sway execution preserves its worker state recorder binding");
  return R4ReadonlySpy(3, adapter, mailbox, published, revision, step, payload,
                       request_id, serialized, failure);
}
#endif

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1)
bool IsPlayerReligionReformPrivateStep12002(std::string_view step) noexcept {
  return step == r4_steps[4];
}
bool ExecutePlayerReligionReformMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandlePlayerReligionReformPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  return R4ReadonlySpy(4, adapter, mailbox, published, revision, step, payload,
                       request_id, serialized, failure);
}
#endif

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_CATALOGUE_PRIVATE_QUERY_V1)
bool IsPlayerReligionDoctrineCataloguePrivateStep12002(std::string_view step) noexcept {
  return step == r4_steps[5];
}
bool ExecutePlayerReligionDoctrineCatalogueMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandlePlayerReligionDoctrineCataloguePrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  return R4ReadonlySpy(5, adapter, mailbox, published, revision, step, payload,
                       request_id, serialized, failure);
}
#endif

// R5 three readonly domain spies: no native/provider/parser validation inferred.
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
bool IsPlayerReligionConversionOutcomePrivateStep12002(std::string_view step) noexcept {
  return step == r5_steps[0];
}
bool ExecutePlayerReligionConversionOutcomeMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandlePlayerReligionConversionOutcomePrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  return R5ReadonlySpy(0, adapter, mailbox, published, revision, step, payload,
                       request_id, serialized, failure);
}
#endif

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_NUMERIC_SPECIAL_PARAMETERS_PRIVATE_QUERY_V1)
bool IsPlayerReligionNumericSpecialParametersPrivateStep12002(std::string_view step) noexcept {
  return step == r5_steps[1];
}
bool ExecutePlayerReligionNumericSpecialParametersMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandlePlayerReligionNumericSpecialParametersPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  return R5ReadonlySpy(1, adapter, mailbox, published, revision, step, payload,
                       request_id, serialized, failure);
}
#endif

#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
bool ExecuteSwayCompletionTerminationMailboxV1(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
bool HandleSwayCompletionTerminationV1(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const SwayTerminationRecorder12002 &recorder,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  Check(&recorder == expected_sway_termination_recorder,
        "Sway termination receives the fixture-owned long-lived recorder identity");
  Check(expected.state->sway_termination_recorder == &recorder,
        "Sway termination preserves its worker state recorder binding");
  return R5ReadonlySpy(2, adapter, mailbox, published, revision, step, payload,
                       request_id, serialized, failure);
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
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1)
  Check(executors.religion == &ExecutePlayerReligionMailbox12002,
        "religion query callback registered");
#else
  Check(executors.religion == nullptr, "default religion callback absent");
#endif
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
  SwayExecutionRecorder12002 owned_sway_execution_recorder{};
  state.sway_execution_recorder = &owned_sway_execution_recorder;
  expected_sway_execution_recorder = &owned_sway_execution_recorder;
  SwayTerminationRecorder12002 owned_sway_termination_recorder{};
  state.sway_termination_recorder = &owned_sway_termination_recorder;
  expected_sway_termination_recorder = &owned_sway_termination_recorder;
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
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1)
  Check(executors.rite_governance == &ExecutePlayerRiteGovernanceMailbox12002, "rite_governance callback registered");
#else
  Check(executors.rite_governance == nullptr, "disabled rite_governance callback absent");
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1)
  Check(executors.clergy == &ExecutePlayerClergyAppointmentMailbox12002, "clergy callback registered");
#else
  Check(executors.clergy == nullptr, "disabled clergy callback absent");
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  Check(executors.religion_conversion == &ExecutePlayerReligionConversionTermsMailbox12002, "religion_conversion callback registered");
#else
  Check(executors.religion_conversion == nullptr, "disabled religion_conversion callback absent");
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1)
  Check(executors.religion_doctrines == &ExecutePlayerReligionDoctrinesMailbox12002, "religion_doctrines callback registered");
#else
  Check(executors.religion_doctrines == nullptr, "disabled religion_doctrines callback absent");
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_HOSTILITY_PRIVATE_QUERY_V1)
  Check(executors.religion_hostility == &ExecutePlayerReligionHostilityMailbox12002, "religion_hostility callback registered");
#else
  Check(executors.religion_hostility == nullptr, "disabled religion_hostility callback absent");
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1)
  Check(executors.religion_doctrine_knowledge == &ExecutePlayerReligionDoctrineKnowledgeMailbox12002, "religion_doctrine_knowledge callback registered");
#else
  Check(executors.religion_doctrine_knowledge == nullptr, "disabled religion_doctrine_knowledge callback absent");
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1)
  Check(executors.religion_tenets == &ExecutePlayerReligionTenetsMailbox12002, "religion_tenets callback registered");
#else
  Check(executors.religion_tenets == nullptr, "disabled religion_tenets callback absent");
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1)
  Check(executors.rite_members == &ExecutePlayerRiteMembersMailbox12002, "rite_members callback registered");
#else
  Check(executors.rite_members == nullptr, "disabled rite_members callback absent");
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  Check(executors.religion_conversion_choices == &ExecutePlayerReligionConversionChoicesMailbox12002, "religion_conversion_choices callback registered");
#else
  Check(executors.religion_conversion_choices == nullptr, "disabled religion_conversion_choices callback absent");
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  Check(executors.religion_conversion_inputs == &ExecutePlayerReligionConversionInputsMailbox12002, "religion_conversion_inputs callback registered");
#else
  Check(executors.religion_conversion_inputs == nullptr, "disabled religion_conversion_inputs callback absent");
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  Check(executors.sway_completion == &ExecuteSwayCompletionMailboxV1, "sway_completion callback registered");
#else
  Check(executors.sway_completion == nullptr, "disabled sway_completion callback absent");
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_TREATMENT_PRIVATE_QUERY_V1)
  Check(executors.epidemic_treatment == &ExecutePlayerEpidemicTreatmentMailbox12002, "epidemic_treatment R4 callback registered");
#else
  Check(executors.epidemic_treatment == nullptr, "disabled epidemic_treatment R4 callback absent");
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_RECOVERY_PRIVATE_QUERY_V1)
  Check(executors.epidemic_recovery == &ExecutePlayerEpidemicRecoveryMailbox12002, "epidemic_recovery R4 callback registered");
#else
  Check(executors.epidemic_recovery == nullptr, "disabled epidemic_recovery R4 callback absent");
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  Check(executors.religion_conversion_reasons == &ExecutePlayerReligionConversionReasonsMailbox12002, "religion_conversion_reasons R4 callback registered");
#else
  Check(executors.religion_conversion_reasons == nullptr, "disabled religion_conversion_reasons R4 callback absent");
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  Check(executors.sway_completion_execution == &ExecuteSwayCompletionExecutionMailboxV1, "sway_completion_execution R4 callback registered");
#else
  Check(executors.sway_completion_execution == nullptr, "disabled sway_completion_execution R4 callback absent");
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1)
  Check(executors.religion_reform == &ExecutePlayerReligionReformMailbox12002, "religion_reform R4 callback registered");
#else
  Check(executors.religion_reform == nullptr, "disabled religion_reform R4 callback absent");
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_CATALOGUE_PRIVATE_QUERY_V1)
  Check(executors.religion_doctrine_catalogue == &ExecutePlayerReligionDoctrineCatalogueMailbox12002, "religion_doctrine_catalogue R4 callback registered");
#else
  Check(executors.religion_doctrine_catalogue == nullptr, "disabled religion_doctrine_catalogue R4 callback absent");
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  Check(executors.religion_conversion_outcome == &ExecutePlayerReligionConversionOutcomeMailbox12002, "religion_conversion_outcome R5 callback registered");
#else
  Check(executors.religion_conversion_outcome == nullptr, "disabled religion_conversion_outcome R5 callback absent");
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_NUMERIC_SPECIAL_PARAMETERS_PRIVATE_QUERY_V1)
  Check(executors.religion_numeric_special_parameters == &ExecutePlayerReligionNumericSpecialParametersMailbox12002, "religion_numeric_special_parameters R5 callback registered");
#else
  Check(executors.religion_numeric_special_parameters == nullptr, "disabled religion_numeric_special_parameters R5 callback absent");
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  Check(executors.sway_completion_termination == &ExecuteSwayCompletionTerminationMailboxV1, "sway_completion_termination R5 callback registered");
#else
  Check(executors.sway_completion_termination == nullptr, "disabled sway_completion_termination R5 callback absent");
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
                            std::string_view expected_output,
                            std::string_view payload = "{\"persistent_action_id\":\"already-pending\"}") {
    Check(IsNonwarPrivateStep12002(step) == enabled, "canonical selector visibility");
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
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1)
  exercise("query-player-religion-context-v1", true, "religion-forwarded");
#else
  exercise("query-player-religion-context-v1", false, "");
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1)
  exercise(readonly_steps[0], true, readonly_outputs[0], R"json({"expected_snapshot_revision":916,"expected_revision":916})json");
#else
  exercise(readonly_steps[0], false, "", R"json({"expected_snapshot_revision":916,"expected_revision":916})json");
#endif
  Check(!IsNonwarPrivateStep12002(std::string(readonly_steps[0]) + "-unregistered"),
        "readonly selector requires an exact match");
#if defined(XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1)
  exercise(readonly_steps[1], true, readonly_outputs[1], R"json({"candidate_character_id":50331653,"expected_revision":916})json");
#else
  exercise(readonly_steps[1], false, "", R"json({"candidate_character_id":50331653,"expected_revision":916})json");
#endif
  Check(!IsNonwarPrivateStep12002(std::string(readonly_steps[1]) + "-unregistered"),
        "readonly selector requires an exact match");
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  exercise(readonly_steps[2], true, readonly_outputs[2], R"json({"target_rite_id":0,"expected_revision":916})json");
#else
  exercise(readonly_steps[2], false, "", R"json({"target_rite_id":0,"expected_revision":916})json");
#endif
  Check(!IsNonwarPrivateStep12002(std::string(readonly_steps[2]) + "-unregistered"),
        "readonly selector requires an exact match");
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1)
  exercise(readonly_steps[3], true, readonly_outputs[3], R"json({"expected_revision":916})json");
#else
  exercise(readonly_steps[3], false, "", R"json({"expected_revision":916})json");
#endif
  Check(!IsNonwarPrivateStep12002(std::string(readonly_steps[3]) + "-unregistered"),
        "readonly selector requires an exact match");
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_HOSTILITY_PRIVATE_QUERY_V1)
  exercise(readonly_steps[4], true, readonly_outputs[4], R"json({"target_rite_id":4294967295,"expected_revision":916})json");
#else
  exercise(readonly_steps[4], false, "", R"json({"target_rite_id":4294967295,"expected_revision":916})json");
#endif
  Check(!IsNonwarPrivateStep12002(std::string(readonly_steps[4]) + "-unregistered"),
        "readonly selector requires an exact match");
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1)
  exercise(readonly_steps[5], true, readonly_outputs[5], R"json({"doctrine_key":"fixture-doctrine","expected_revision":916})json");
#else
  exercise(readonly_steps[5], false, "", R"json({"doctrine_key":"fixture-doctrine","expected_revision":916})json");
#endif
  Check(!IsNonwarPrivateStep12002(std::string(readonly_steps[5]) + "-unregistered"),
        "readonly selector requires an exact match");
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1)
  exercise(readonly_steps[6], true, readonly_outputs[6], R"json({})json");
#else
  exercise(readonly_steps[6], false, "", R"json({})json");
#endif
  Check(!IsNonwarPrivateStep12002(std::string(readonly_steps[6]) + "-unregistered"),
        "readonly selector requires an exact match");
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1)
  exercise(readonly_steps[7], true, readonly_outputs[7], R"json({"expected_snapshot_revision":916})json");
#else
  exercise(readonly_steps[7], false, "", R"json({"expected_snapshot_revision":916})json");
#endif
  Check(!IsNonwarPrivateStep12002(std::string(readonly_steps[7]) + "-unregistered"),
        "readonly selector requires an exact match");
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  exercise(readonly_steps[8], true, readonly_outputs[8], R"json({"expected_revision":916})json");
#else
  exercise(readonly_steps[8], false, "", R"json({"expected_revision":916})json");
#endif
  Check(!IsNonwarPrivateStep12002(std::string(readonly_steps[8]) + "-unregistered"),
        "readonly selector requires an exact match");
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  exercise(readonly_steps[9], true, readonly_outputs[9], R"json({"target_rite_id":0,"expected_revision":916})json");
#else
  exercise(readonly_steps[9], false, "", R"json({"target_rite_id":0,"expected_revision":916})json");
#endif
  Check(!IsNonwarPrivateStep12002(std::string(readonly_steps[9]) + "-unregistered"),
        "readonly selector requires an exact match");
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  exercise(readonly_steps[10], true, readonly_outputs[10], R"json({"expected_revision":916,"actor_character_id":29829,"target_character_id":43699,"scheme_instance_id":0})json");
#else
  exercise(readonly_steps[10], false, "", R"json({"expected_revision":916,"actor_character_id":29829,"target_character_id":43699,"scheme_instance_id":0})json");
#endif
  Check(!IsNonwarPrivateStep12002(std::string(readonly_steps[10]) + "-unregistered"),
        "readonly selector requires an exact match");
#if defined(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_TREATMENT_PRIVATE_QUERY_V1)
  exercise(r4_steps[0], true, r4_outputs[0], R"json({"expected_revision":916})json");
#else
  exercise(r4_steps[0], false, "", R"json({"expected_revision":916})json");
#endif
  Check(!IsNonwarPrivateStep12002(std::string(r4_steps[0]) + "-unregistered"),
        "R4 readonly selector requires an exact match");
#if defined(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_RECOVERY_PRIVATE_QUERY_V1)
  exercise(r4_steps[1], true, r4_outputs[1], R"json({"expected_revision":916,"expected_event_instance_id":41})json");
#else
  exercise(r4_steps[1], false, "", R"json({"expected_revision":916,"expected_event_instance_id":41})json");
#endif
  Check(!IsNonwarPrivateStep12002(std::string(r4_steps[1]) + "-unregistered"),
        "R4 readonly selector requires an exact match");
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  exercise(r4_steps[2], true, r4_outputs[2], R"json({"target_rite_id":0,"expected_snapshot_revision":916,"expected_revision":916})json");
#else
  exercise(r4_steps[2], false, "", R"json({"target_rite_id":0,"expected_snapshot_revision":916,"expected_revision":916})json");
#endif
  Check(!IsNonwarPrivateStep12002(std::string(r4_steps[2]) + "-unregistered"),
        "R4 readonly selector requires an exact match");
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  exercise(r4_steps[3], true, r4_outputs[3], R"json({"expected_revision":916,"actor_character_id":29829,"target_character_id":43699,"scheme_instance_id":0,"after_sequence":7})json");
#else
  exercise(r4_steps[3], false, "", R"json({"expected_revision":916,"actor_character_id":29829,"target_character_id":43699,"scheme_instance_id":0,"after_sequence":7})json");
#endif
  Check(!IsNonwarPrivateStep12002(std::string(r4_steps[3]) + "-unregistered"),
        "R4 readonly selector requires an exact match");
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1)
  exercise(r4_steps[4], true, r4_outputs[4], R"json({"expected_snapshot_revision":916})json");
#else
  exercise(r4_steps[4], false, "", R"json({"expected_snapshot_revision":916})json");
#endif
  Check(!IsNonwarPrivateStep12002(std::string(r4_steps[4]) + "-unregistered"),
        "R4 readonly selector requires an exact match");
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_CATALOGUE_PRIVATE_QUERY_V1)
  exercise(r4_steps[5], true, r4_outputs[5], R"json({"expected_revision":916})json");
#else
  exercise(r4_steps[5], false, "", R"json({"expected_revision":916})json");
#endif
  Check(!IsNonwarPrivateStep12002(std::string(r4_steps[5]) + "-unregistered"),
        "R4 readonly selector requires an exact match");
#if defined(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_RECOVERY_PRIVATE_QUERY_V1)
  exercise(recovery_title_step, true, r4_outputs[1], R"json({"expected_revision":916})json");
#else
  exercise(recovery_title_step, false, "", R"json({"expected_revision":916})json");
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  state.sway_execution_recorder = nullptr;
  std::string missing_recorder_output = "stale-output", missing_recorder_failure = "stale-failure";
  Check(!HandleNonwarPrivate12002(adapter, mailbox, published, 916, r4_steps[3],
      R"json({"expected_revision":916})json", "missing-recorder", state,
      missing_recorder_output, missing_recorder_failure), "missing Sway recorder cannot invoke execution query");
  Check(missing_recorder_output.empty() && missing_recorder_failure == "sway_execution_observer_not_installed",
        "missing Sway recorder returns the actual central failure");
  Check(r4_calls[3] == 1, "missing recorder invokes no Sway execution handler");
  state.sway_execution_recorder = &owned_sway_execution_recorder;
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  exercise(r5_steps[0], true, r5_outputs[0], R"json({"target_rite_id":0,"expected_snapshot_revision":916,"expected_revision":916})json");
#else
  exercise(r5_steps[0], false, "", R"json({"target_rite_id":0,"expected_snapshot_revision":916,"expected_revision":916})json");
#endif
  Check(!IsNonwarPrivateStep12002(std::string(r5_steps[0]) + "-unregistered"),
        "R5 readonly selector requires an exact match");
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_NUMERIC_SPECIAL_PARAMETERS_PRIVATE_QUERY_V1)
  exercise(r5_steps[1], true, r5_outputs[1], R"json({"expected_snapshot_revision":916,"expected_revision":916})json");
#else
  exercise(r5_steps[1], false, "", R"json({"expected_snapshot_revision":916,"expected_revision":916})json");
#endif
  Check(!IsNonwarPrivateStep12002(std::string(r5_steps[1]) + "-unregistered"),
        "R5 readonly selector requires an exact match");
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  exercise(r5_steps[2], true, r5_outputs[2], R"json({"expected_revision":916,"actor_character_id":29829,"target_character_id":43699,"scheme_instance_id":0,"after_sequence":7})json");
#else
  exercise(r5_steps[2], false, "", R"json({"expected_revision":916,"actor_character_id":29829,"target_character_id":43699,"scheme_instance_id":0,"after_sequence":7})json");
#endif
  Check(!IsNonwarPrivateStep12002(std::string(r5_steps[2]) + "-unregistered"),
        "R5 readonly selector requires an exact match");
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
  Check(religion_calls ==
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1)
        1,
#else
        0,
#endif
        "religion selector obeys the selected build flag");
  Check(readonly_calls[0] ==
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1)
        1,
#else
        0,
#endif
        "rite_governance selector obeys the selected build flag");
  Check(readonly_calls[1] ==
#if defined(XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1)
        1,
#else
        0,
#endif
        "clergy selector obeys the selected build flag");
  Check(readonly_calls[2] ==
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
        1,
#else
        0,
#endif
        "religion_conversion selector obeys the selected build flag");
  Check(readonly_calls[3] ==
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1)
        1,
#else
        0,
#endif
        "religion_doctrines selector obeys the selected build flag");
  Check(readonly_calls[4] ==
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_HOSTILITY_PRIVATE_QUERY_V1)
        1,
#else
        0,
#endif
        "religion_hostility selector obeys the selected build flag");
  Check(readonly_calls[5] ==
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1)
        1,
#else
        0,
#endif
        "religion_doctrine_knowledge selector obeys the selected build flag");
  Check(readonly_calls[6] ==
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1)
        1,
#else
        0,
#endif
        "religion_tenets selector obeys the selected build flag");
  Check(readonly_calls[7] ==
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1)
        1,
#else
        0,
#endif
        "rite_members selector obeys the selected build flag");
  Check(readonly_calls[8] ==
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
        1,
#else
        0,
#endif
        "religion_conversion_choices selector obeys the selected build flag");
  Check(readonly_calls[9] ==
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
        1,
#else
        0,
#endif
        "religion_conversion_inputs selector obeys the selected build flag");
  Check(readonly_calls[10] ==
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
        1,
#else
        0,
#endif
        "sway_completion selector obeys the selected build flag");
  Check(r4_calls[0] ==
#if defined(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_TREATMENT_PRIVATE_QUERY_V1)
        1,
#else
        0,
#endif
        "epidemic_treatment R4 selector obeys the selected build flag");
  Check(r4_calls[1] ==
#if defined(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_RECOVERY_PRIVATE_QUERY_V1)
        2,
#else
        0,
#endif
        "epidemic_recovery R4 selector obeys the selected build flag");
  Check(r4_calls[2] ==
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
        1,
#else
        0,
#endif
        "religion_conversion_reasons R4 selector obeys the selected build flag");
  Check(r4_calls[3] ==
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
        1,
#else
        0,
#endif
        "sway_completion_execution R4 selector obeys the selected build flag");
  Check(r4_calls[4] ==
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1)
        1,
#else
        0,
#endif
        "religion_reform R4 selector obeys the selected build flag");
  Check(r4_calls[5] ==
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_CATALOGUE_PRIVATE_QUERY_V1)
        1,
#else
        0,
#endif
        "religion_doctrine_catalogue R4 selector obeys the selected build flag");
  std::size_t r4_total = 0;
  for (const auto value : r4_calls) r4_total += value;
  Check(r5_calls[0] ==
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
        1,
#else
        0,
#endif
        "religion_conversion_outcome R5 selector obeys the selected build flag");
  Check(r5_calls[1] ==
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_NUMERIC_SPECIAL_PARAMETERS_PRIVATE_QUERY_V1)
        1,
#else
        0,
#endif
        "religion_numeric_special_parameters R5 selector obeys the selected build flag");
  Check(r5_calls[2] ==
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
        1,
#else
        0,
#endif
        "sway_completion_termination R5 selector obeys the selected build flag");
  std::size_t r5_total = 0;
  for (const auto value : r5_calls) r5_total += value;
  std::size_t readonly_total = 0;
  for (const auto value : readonly_calls) readonly_total += value;
  std::cout << "{\"status\":\"GREEN\",\"checks\":" << checks
            << ",\"gift_selectors_forwarded\":" << gift_calls
            << ",\"sway_selectors_forwarded\":" << sway_calls
            << ",\"prisoner_selectors_forwarded\":" << prisoner_calls
            << ",\"religion_selectors_forwarded\":" << religion_calls
            << ",\"new_readonly_selectors_forwarded\":" << readonly_total
            << ",\"R4_readonly_selectors_forwarded\":" << r4_total
            << ",\"R5_readonly_selectors_forwarded\":" << r5_total
            << ",\"fallback_calls\":" << fallback_calls
            << ",\"live_verified\":false,\"ck3_touched\":false}\n";
}
