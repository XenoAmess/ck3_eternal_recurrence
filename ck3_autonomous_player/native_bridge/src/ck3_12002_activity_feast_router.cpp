#include "xar_bridge/ck3_12003_adapter.hpp"
#include "ck3_12002_activity_feast_router.hpp"

#include "ck3_12002_activity_feast_private_transport_v1.hpp"
#include "ck3_12002_activity_stage5_canstart_private_transport_v1.hpp"
#include "ck3_12002_activity_feast_cost_private_transport_v1.hpp"
#include "ck3_12002_activity_feast_guest_transport.hpp"
#include "ck3_12002_feast_planner_private_transport_v1.hpp"
#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12002_campaign.hpp"
#include "xar_bridge/ck3_12002_activity_feast_costs.hpp"
#include "xar_bridge/protocol.hpp"

#include <windows.h>

#include <array>
#include <limits>

namespace xar::ck3_12002 {
namespace {
using ck3_11906::MainThreadQuerySubmitResultV1;
using ck3_11906::MainThreadQueryWaitResultV1;
using ck3_11906::MainThreadQueryReclaimResultV1;

void AppendString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  output += '"';
  for (const unsigned char byte : value) {
    if (byte == '"' || byte == '\\') {
      output += '\\';
      output += static_cast<char>(byte);
    } else if (byte < 0x20) {
      output += "\\u00";
      output += hex[byte >> 4];
      output += hex[byte & 0x0f];
    } else {
      output += static_cast<char>(byte);
    }
  }
  output += '"';
}

[[maybe_unused]] std::string ResultFrame(std::string_view request_id, std::string_view step,
                        std::string_view key, std::string_view native,
                        bool ok, bool accepted, bool read_only,
                        std::string_view status,
                        std::string_view transport_failure = {}) {
  std::string response =
      "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  AppendString(response, request_id);
  response += ok ? ",\"ok\":true" : ",\"ok\":false";
  response += ",\"result\":{\"step\":";
  AppendString(response, step);
  response += accepted ? ",\"accepted\":true" : ",\"accepted\":false";
  response += ",\"status\":";
  AppendString(response, status);
  response += ",\"private_build\":true,\"advertised\":false,\"read_only\":";
  response += read_only ? "true" : "false";
  if (!transport_failure.empty()) {
    response += ",\"transport_failure\":";
    AppendString(response, transport_failure);
  }
  response += ',';
  AppendString(response, key);
  response += ':';
  response += native;
  response += ",\"backend_id\":\"native-headless\"}}";
  return response;
}

[[maybe_unused]] bool ReadAdapterSnapshot(void *context,
                                          game::Snapshot &output) noexcept {
  return context != nullptr &&
      static_cast<const game::GameAdapter *>(context)->read_snapshot(output);
}

// ScriptIdentifier::GetName is the same exact-build source already used by
// campaign, feature and pending-interaction readers. It returns interned names.
[[maybe_unused]] bool ResolveScriptIdentifier(
    void *context, std::int32_t identifier, std::string_view &output) noexcept {
  output = {};
  const auto *adapter = static_cast<const game::GameAdapter *>(context);
  if (adapter == nullptr || !adapter->enabled() || identifier < 0 ||
      xar::game::ReviewedCrozierAbiSha256(adapter->descriptor()) != kExecutableSha256)
    return false;
  const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  if (base == 0) return false;
  const auto getter = reinterpret_cast<NativeCampaignRootScriptIdentifierNameV1>(
      base + kCampaignRootScriptIdentifierNameRva);
  __try {
    const auto *name = getter(identifier);
    if (name == nullptr || name->empty() || name->size() > 96) return false;
    output = std::string_view(name->data(), name->size());
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

template <typename Query>
void BindQuery(Query &query, const game::GameAdapter &adapter,
               ck3_11906::MainThreadQueryMailboxV1 &mailbox,
               const game::Snapshot &current, std::uint64_t revision) noexcept {
  query.mailbox = &mailbox;
  query.enabled = adapter.enabled();
  query.module_base =
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  query.executable_sha256 = xar::game::ReviewedCrozierAbiSha256(adapter.descriptor());
  if constexpr (requires { query.native_context; })
    query.native_context = const_cast<game::GameAdapter *>(&adapter);
  else
    query.snapshot_context = const_cast<game::GameAdapter *>(&adapter);
  query.read_snapshot = &ReadAdapterSnapshot;
  query.expected_snapshot = current;
  query.expected_revision = revision;
  if constexpr (requires { query.resolve_script_identifier; })
    query.resolve_script_identifier = &ResolveScriptIdentifier;
}

template <typename Query>
bool RunQuery(Query &query, ck3_11906::MainThreadQueryExecutorV1 executor,
              std::string &failure) noexcept {
  if (ck3_11906::TrySubmitMainThreadQueryV1(
          *query.mailbox, executor, &query, query.ticket) !=
      MainThreadQuerySubmitResultV1::submitted) {
    failure = "activity feast application-main executor unavailable";
    return false;
  }
  auto wait = ck3_11906::WaitForMainThreadQueryV1(
      *query.mailbox, query.ticket, 8'000);
  while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
    wait = ck3_11906::WaitForMainThreadQueryV1(
        *query.mailbox, query.ticket, 2'000);
  if (wait != MainThreadQueryWaitResultV1::completed || !query.completed) {
    ck3_11906::ReclaimMainThreadQueryV1(*query.mailbox, query.ticket);
    failure = "activity feast application-main executor incomplete";
    return false;
  }
  return true;
}

template <typename Query>
bool Reclaim(Query &query, std::string &failure) noexcept {
  if (ck3_11906::ReclaimMainThreadQueryV1(*query.mailbox, query.ticket) ==
      MainThreadQueryReclaimResultV1::reclaimed)
    return true;
  failure = "activity feast application-main mailbox reclaim red";
  return false;
}

[[maybe_unused]] bool SameFrame(const game::GameAdapter &adapter,
                               const game::Snapshot &current) noexcept {
  game::Snapshot after{};
  return adapter.read_snapshot(after) && after == current;
}

[[maybe_unused]] bool ParseActorDate(std::string_view payload,
                                     const game::Snapshot &current) noexcept {
  std::uint64_t actor = 0, date = 0;
  return bridge::JsonUnsignedField(payload, "expected_date_raw", date) &&
      bridge::JsonUnsignedField(payload, "expected_actor_character_id", actor) &&
      actor == static_cast<std::uint64_t>(current.played_character_id) &&
      date == static_cast<std::uint64_t>(current.date_raw);
}

[[maybe_unused]] bool ParseFeastStage(std::string_view payload,
                                      std::uint64_t expected,
                                      bool option) noexcept {
  std::uint64_t stage = 0;
  std::string key, option_key;
  return bridge::JsonUnsignedField(payload, "expected_planning_stage", stage) &&
      stage == expected &&
      bridge::JsonStringField(payload, "expected_activity_key", key, 96) &&
      key == "activity_feast" &&
      (!option || (bridge::JsonStringField(
          payload, "expected_option_key", option_key, 96) &&
          option_key == "feast_type_generic"));
}

[[maybe_unused]] bool ParseFeastOption(std::string_view payload) noexcept {
  std::string key, option;
  return bridge::JsonStringField(payload, "expected_activity_key", key, 96) &&
      key == "activity_feast" &&
      bridge::JsonStringField(payload, "expected_option_key", option, 96) &&
      option == "feast_type_generic";
}

template <typename Query, typename Serializer>
bool FinishRead(Query &query, Serializer serializer,
                const game::GameAdapter &adapter,
                const game::Snapshot &current, std::string_view request_id,
                std::string_view step, std::string_view key,
                std::string &serialized, std::string &failure,
                bool permit_domain_red = false) {
  const bool stable = !query.frame_changed && SameFrame(adapter, current);
  const auto native = stable ? serializer(query) : std::string{};
  const bool reclaimed = Reclaim(query, failure);
  if (!stable || native.empty() || (!permit_domain_red && !query.failure.empty())) {
    if (failure.empty())
      failure = query.failure.empty() ? "activity feast paused read unavailable"
                                      : query.failure;
    return false;
  }
  if (!reclaimed) return false;
  serialized = ResultFrame(request_id, step, key, native,
                           true, true, true, "available");
  return true;
}
} // namespace

bool IsActivityFeastPrivateStep12002(std::string_view step) noexcept {
  static_cast<void>(step);
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_PLANNER_DIAG_PRIVATE_QUERY_V1)
  if (step == ck3_11906::kActivityPlannerDiagPrivateStepV1) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_PLANNER_OPEN_PRIVATE_V1)
  if (step == ck3_11906::kActivityFeastPlannerOpenPrivateStepV1) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_OPTION_READ_PRIVATE_V1)
  if (step == ck3_11906::kActivityStage1OptionReadPrivateStepV1) return true;
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_CONFIRM_PRIVATE_V1)
  if (step == ck3_11906::kActivityStage1ConfirmPrivateStepV1) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_OPTION_READ_PRIVATE_V1)
  if (step == ck3_11906::kActivityStage2OptionReadPrivateStepV1) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_GATE_READ_PRIVATE_V1)
  if (step == ck3_11906::kActivityStage2GateReadPrivateStepV1) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_LOCATION_READ_PRIVATE_V1)
  if (step == ck3_11906::kActivityStage2LocationReadPrivateStepV1) return true;
#endif
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_COST_SLOT12_PASSIVE_PRIVATE_V1)
  if (step == "query-activity-cost-slot12-raw-v1-private") return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_DESTINATION_PRIVATE_V1)
  if (step == ck3_11906::kActivityStage2DestinationSelectPrivateStepV1 ||
      step == kActivityStage2ConfirmPrivate12002StepV1) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_CANSTART_PRIVATE_V1)
  if (step == ck3_11906::kActivityStage5CanStartPrivateStepV1) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_GOLD_COST_PRIVATE_V1)
  if (step == kActivityStage5GoldCostPrivateStepV1) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_FEAST_FULL_COST_PRIVATE_V1)
  if (step == kActivityStage5FeastFullCostPrivateStepV1) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_STAGE5_START_PRIVATE_V1)
  if (step == ck3_11906::kActivityFeastStage5InputsPrivateStepV1 ||
      step == ck3_11906::kActivityFeastStage5StartPrivateStepV1 ||
      step == ck3_11906::kActivityFeastHostedPostPrivateStepV1) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_CANDIDATE_PRIVATE_V1)
  if (step == kActivityFeastGuestCandidatePrivateStepV1 ||
      step == kActivityFeastGuestRouteProofPrivateStepV1 ||
      step == kActivityFeastGuestTargetPrivateStepV1) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_OPINION_PRIVATE_V1)
  if (step == kActivityFeastGuestOpinionPrivateStepV1) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_TOGGLE_PRIVATE_V1)
  if (step == kActivityFeastGuestRuleReadPrivateStepV1 ||
      step == kActivityFeastGuestRuleActivatePrivateStepV1) return true;
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1)
  if (step == kActivityFeastGuestRuleProvenancePrivateStepV1) return true;
#endif
#endif
  return false;
}

bool HandleActivityFeastPrivate12002(
    const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure,
    bridge::ActivityCostSlot12ObserverV1 *passive_cost,
    bridge::ActivityGuestRuleProvenanceObserverV1 *provenance_observer) noexcept {
  serialized.clear();
  failure.clear();
  if (!IsActivityFeastPrivateStep12002(step)) return false;
  try {
    std::uint64_t requested_revision = 0;
    game::Snapshot current{};
    if (!adapter.enabled() ||
        xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()) != kExecutableSha256 ||
        !bridge::JsonUnsignedField(payload, "expected_revision", requested_revision) ||
        revision == 0 || requested_revision != revision ||
        !adapter.read_snapshot(current) || current != published ||
        !current.paused || !current.map_ready ||
        !current.has_played_character || !current.played_character_alive ||
        current.played_character_id <= 0) {
      failure = "activity feast exact-build frame or request invalid";
      return false;
    }
    static_cast<void>(mailbox);
    static_cast<void>(request_id);
    static_cast<void>(passive_cost);
    static_cast<void>(provenance_observer);

#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_COST_SLOT12_PASSIVE_PRIVATE_V1)
    if (step == "query-activity-cost-slot12-raw-v1-private") {
      if (passive_cost == nullptr) {
        failure = "activity cost normal slot12 refresh observer unavailable";
        return false;
      }
      bridge::ActivityCostSlot12CaptureV1 capture{};
      const bridge::ActivityCostSlot12FrameV1 expected{
          current.date_raw, current.played_character_id,
          mailbox.owner_thread_id.load(std::memory_order_acquire), true};
      const auto status = bridge::ReadActivityCostSlot12PassiveV1(
          *passive_cost, expected, capture);
      if (status != bridge::ActivityCostSlot12ReadStatusV1::observed ||
          !SameFrame(adapter, current)) {
        switch (status) {
        case bridge::ActivityCostSlot12ReadStatusV1::no_normal_refresh:
          failure = "activity cost normal slot12 refresh not observed"; break;
        case bridge::ActivityCostSlot12ReadStatusV1::configuration_changed:
          failure = "activity cost planner configuration changed"; break;
        case bridge::ActivityCostSlot12ReadStatusV1::exact_build_rejected:
          failure = "activity cost exact build unavailable"; break;
        default: failure = "activity cost frame changed"; break;
        }
        return false;
      }
      std::string native =
          "{\"schema\":\"activity-cost-slot12-raw-private-v1\",\"snapshot_revision\":" +
          std::to_string(revision) + ",\"date_raw\":" + std::to_string(current.date_raw) +
          ",\"actor_character_id\":" + std::to_string(current.played_character_id) +
          ",\"activity_key\":\"activity_feast\",\"planning_stage\":" +
          std::to_string(capture.planning_stage) + ",\"capture_sequence\":" +
          std::to_string(capture.sequence) +
          ",\"source\":\"normal_slot12_return_0x11B5B5F\","
          "\"resource_mapping\":null,\"configured_cost\":null,\"raw_aggregate_i64\":[";
      for (std::size_t index = 0; index < capture.raw_aggregate.size(); ++index) {
        if (index != 0) native += ',';
        native += std::to_string(capture.raw_aggregate[index]);
      }
      native += "]}";
      serialized = ResultFrame(request_id, step, "activity_cost_slot12_raw", native,
          true, true, true, "available");
      return true;
    }
#endif

#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_PLANNER_DIAG_PRIVATE_QUERY_V1)
    if (step == ck3_11906::kActivityPlannerDiagPrivateStepV1) {
      ActivityPlannerDiagPrivate12002QueryV1 query{};
      BindQuery(query, adapter, mailbox, current, revision);
      if (!RunQuery(query, &ExecuteActivityPlannerDiagPrivate12002QueryV1, failure))
        return false;
      return FinishRead(query, &ck3_11906::SerializeActivityPlannerDiagPrivateQueryV1,
          adapter, current, request_id, step, "activity_planner_diag",
          serialized, failure, true);
    }
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_PLANNER_OPEN_PRIVATE_V1)
    if (step == ck3_11906::kActivityFeastPlannerOpenPrivateStepV1) {
      ActivityFeastPlannerOpenPrivate12002QueryV1 query{};
      BindQuery(query, adapter, mailbox, current, revision);
      if (!RunQuery(query, &ExecuteActivityFeastPlannerOpenPrivate12002V1, failure))
        return false;
      const bool stable = !query.frame_changed && SameFrame(adapter, current);
      const auto native = ck3_11906::SerializeActivityFeastPlannerOpenPrivateV1(query);
      const bool reclaimed = Reclaim(query, failure);
      if (native.empty() || !reclaimed) return false;
      const bool opened = stable && query.failure.empty() &&
          (query.result.status == bridge::ActivityFeastPlannerOpenStatusV1::opened ||
           query.result.status == bridge::ActivityFeastPlannerOpenStatusV1::already_open);
      serialized = ResultFrame(request_id, step, "activity_feast_planner_open",
          native, opened, opened, false, opened ? "available" : "red");
      return true;
    }
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_CANDIDATE_PRIVATE_V1)
    if (step == kActivityFeastGuestCandidatePrivateStepV1 ||
        step == kActivityFeastGuestRouteProofPrivateStepV1 ||
        step == kActivityFeastGuestTargetPrivateStepV1) {
      const bool target = step == kActivityFeastGuestTargetPrivateStepV1;
      std::uint64_t target_id = 0;
      if (!ParseActorDate(payload, current) || !ParseFeastStage(payload, 5, false) ||
          (target && (!bridge::JsonUnsignedField(payload, "target_character_id", target_id) ||
                      target_id == 0 || target_id > 0x7fffffffULL ||
                      target_id == static_cast<std::uint64_t>(current.played_character_id)))) {
        failure = "activity feast guest candidate request invalid";
        return false;
      }
      ActivityFeastGuestCandidatePrivateQueryV1 query{};
      BindQuery(query, adapter, mailbox, current, revision);
      query.passive_cost = passive_cost;
      query.route_proof = target || step == kActivityFeastGuestRouteProofPrivateStepV1;
      query.target_character_id = target ? static_cast<std::int32_t>(target_id) : 0;
      if (!RunQuery(query, &ExecuteActivityFeastGuestCandidatePrivateV1, failure))
        return false;
      const bool stable = !query.frame_changed && SameFrame(adapter, current);
      const auto native = stable
          ? (target ? SerializeActivityFeastGuestTargetPrivateV1(query)
                    : query.route_proof ? SerializeActivityFeastGuestRouteProofPrivateV1(query)
                                        : SerializeActivityFeastGuestCandidatePrivateV1(query))
          : std::string{};
      const bool reclaimed = Reclaim(query, failure);
      if (native.empty() || !reclaimed) {
        if (failure.empty()) failure = query.failure.empty()
            ? "activity feast guest candidate paused read unavailable" : query.failure;
        return false;
      }
      const bool available = query.route_proof ? query.route_proof_consistent
          : (query.candidate.status == bridge::ActivityFeastGuestCandidateStatusV1::observed ||
             query.candidate.status == bridge::ActivityFeastGuestCandidateStatusV1::no_qualified_candidate);
      serialized = ResultFrame(request_id, step,
          target ? "activity_feast_guest_target"
                 : query.route_proof ? "activity_feast_guest_route_proof"
                                     : "activity_feast_guest_candidate",
          native, true, true, true, available ? "available" : "unavailable");
      return true;
    }
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_OPINION_PRIVATE_V1)
    if (step == kActivityFeastGuestOpinionPrivateStepV1) {
      std::uint64_t guest = 0;
      if (!ParseActorDate(payload, current) ||
          !bridge::JsonUnsignedField(payload, "guest_character_id", guest) ||
          guest == 0 || guest > 0x7fffffffULL ||
          guest == static_cast<std::uint64_t>(current.played_character_id)) {
        failure = "activity feast guest opinion request invalid";
        return false;
      }
      ActivityFeastGuestOpinionPrivateQueryV1 query{};
      BindQuery(query, adapter, mailbox, current, revision);
      query.guest_character_id = static_cast<std::int32_t>(guest);
      if (!RunQuery(query, &ExecuteActivityFeastGuestOpinionPrivateV1, failure))
        return false;
      const bool stable = !query.frame_changed && SameFrame(adapter, current);
      const auto native = stable ? SerializeActivityFeastGuestOpinionPrivateV1(query)
                                 : std::string{};
      const bool reclaimed = Reclaim(query, failure);
      if (native.empty() || !reclaimed) {
        if (failure.empty()) failure = query.failure.empty()
            ? "activity feast guest opinion paused read unavailable" : query.failure;
        return false;
      }
      const bool available = query.opinion.status ==
          bridge::ActivityFeastGuestOpinionStatusV1::observed;
      serialized = ResultFrame(request_id, step, "activity_feast_guest_opinion",
          native, true, true, true, available ? "available" : "unavailable");
      return true;
    }
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_TOGGLE_PRIVATE_V1)
    if (step == kActivityFeastGuestRuleReadPrivateStepV1 ||
        step == kActivityFeastGuestRuleActivatePrivateStepV1
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1)
        || step == kActivityFeastGuestRuleProvenancePrivateStepV1
#endif
        ) {
      ActivityFeastGuestRulePrivateQueryV1 query{};
      BindQuery(query, adapter, mailbox, current, revision);
      query.passive_cost = passive_cost;
      query.activate = step == kActivityFeastGuestRuleActivatePrivateStepV1;
      bool valid = ParseActorDate(payload, current) && ParseFeastStage(payload, 5, false) &&
          bridge::JsonStringField(payload, "authored_rule_key", query.authored_rule_key, 96) &&
          query.authored_rule_key.starts_with("activity_invite_rule_") &&
          query.authored_rule_key.size() > sizeof("activity_invite_rule_") - 1 &&
          query.authored_rule_key.find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789_") ==
              std::string::npos;
      if (query.activate)
        valid = valid && bridge::JsonBooleanField(payload, "policy_approved", query.policy_approved) &&
            query.policy_approved;
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1)
      query.query_provenance = step == kActivityFeastGuestRuleProvenancePrivateStepV1;
      query.provenance_observer = provenance_observer;
      if (query.query_provenance) {
        std::uint64_t candidate = 0;
        valid = valid && bridge::JsonUnsignedField(payload, "candidate_character_id", candidate) &&
            candidate != 0 && candidate <= UINT32_MAX;
        query.candidate_character_id = static_cast<std::uint32_t>(candidate);
      }
#endif
      if (!valid) {
        failure = "activity feast guest rule request invalid";
        return false;
      }
      if (!RunQuery(query, &ExecuteActivityFeastGuestRulePrivateV1, failure)) return false;
      const bool stable = !query.frame_changed && SameFrame(adapter, current);
      std::string native;
      std::string_view key = "activity_feast_guest_rule";
      std::string_view outcome = "unavailable";
      if (stable) {
        native = SerializeActivityFeastGuestRulePrivateV1(query);
        if (query.rule.status == bridge::ActivityFeastGuestRuleStatusV1::activated)
          outcome = "activated";
        else if (query.rule.status == bridge::ActivityFeastGuestRuleStatusV1::observed_active)
          outcome = "already_active";
        else if (query.rule.status == bridge::ActivityFeastGuestRuleStatusV1::observed_inactive)
          outcome = "available";
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1)
        if (query.query_provenance) {
          native = SerializeActivityFeastGuestRuleProvenancePrivateV1(query);
          key = "activity_feast_guest_rule_provenance";
          outcome = query.provenance.status == bridge::ActivityGuestRuleProvenanceStatusV1::observed
              ? "available" : "unavailable";
        }
#endif
      }
      const bool reclaimed = Reclaim(query, failure);
      if (native.empty() || !reclaimed) {
        if (failure.empty()) failure = query.failure.empty()
            ? "activity feast guest rule paused read unavailable" : query.failure;
        return false;
      }
      serialized = ResultFrame(request_id, step, key, native, true, true,
          !query.activate, outcome);
      return true;
    }
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_OPTION_READ_PRIVATE_V1)
    if (step == ck3_11906::kActivityStage1OptionReadPrivateStepV1 ||
        step == ck3_11906::kActivityStage1ConfirmPrivateStepV1 ||
        step == ck3_11906::kActivityStage2OptionReadPrivateStepV1 ||
        step == ck3_11906::kActivityStage2GateReadPrivateStepV1 ||
        step == ck3_11906::kActivityStage2LocationReadPrivateStepV1) {
      ActivityStage1OptionReadPrivate12002QueryV1 query{};
      BindQuery(query, adapter, mailbox, current, revision);
      query.confirm_stage_one = step == ck3_11906::kActivityStage1ConfirmPrivateStepV1;
      query.stage_two_read = step == ck3_11906::kActivityStage2OptionReadPrivateStepV1;
      query.stage_two_gate_read = step == ck3_11906::kActivityStage2GateReadPrivateStepV1;
      query.stage_two_location_read = step == ck3_11906::kActivityStage2LocationReadPrivateStepV1;
      const bool typed = query.confirm_stage_one || query.stage_two_read ||
          query.stage_two_gate_read || query.stage_two_location_read;
      if ((typed && (!ParseActorDate(payload, current) || !ParseFeastOption(payload))) ||
          (query.stage_two_location_read &&
           !ck3_11906::ParseActivityStage2CandidateIdsV1(payload,
               query.candidate_province_ids, query.candidate_province_count))) {
        failure = "activity stage-1 or stage-2 option request invalid";
        return false;
      }
      if (!RunQuery(query, &ExecuteActivityStage1OptionReadPrivate12002V1, failure))
        return false;
      game::Snapshot after{};
      const bool stable = adapter.read_snapshot(after) &&
          (query.confirm_stage_one || (!query.frame_changed && after == current));
      std::string native;
      std::string_view key = "activity_stage1_option";
      if (stable) {
        if (query.confirm_stage_one) {
          key = "activity_stage1_confirm";
          native = ck3_11906::SerializeActivityStage1ConfirmPrivateV1(query);
        } else if (query.stage_two_location_read) {
          key = "activity_stage2_location";
          native = ck3_11906::SerializeActivityStage2LocationReadPrivateV1(query);
        } else if (query.stage_two_gate_read) {
          key = "activity_stage2_gate";
          native = ck3_11906::SerializeActivityStage2GateReadPrivateV1(query);
        } else if (query.stage_two_read) {
          key = "activity_stage2_option";
          native = ck3_11906::SerializeActivityStage2OptionReadPrivateV1(query);
        } else native = ck3_11906::SerializeActivityStage1OptionReadPrivateV1(query);
      }
      const bool reclaimed = Reclaim(query, failure);
      if (native.empty() || !reclaimed) return false;
      const bool green = !query.confirm_stage_one ||
          (query.failure.empty() && query.post_snapshot_read &&
           after == query.post_snapshot && query.confirm_result.status ==
               bridge::ActivityStage1ConfirmStatusV1::stage_two_verified);
      serialized = ResultFrame(request_id, step, key, native, green,
          query.confirm_stage_one ? query.confirm_result.submitted : true,
          !query.confirm_stage_one, green ? "available" : "red");
      return true;
    }
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_DESTINATION_PRIVATE_V1)
    if (step == ck3_11906::kActivityStage2DestinationSelectPrivateStepV1) {
      std::uint64_t province = 0;
      if (!ParseActorDate(payload, current) || !ParseFeastOption(payload) ||
          !bridge::JsonUnsignedField(payload, "province_id", province) ||
          province == 0 || province > 0x7fffffffULL) {
        failure = "activity stage-2 destination request invalid";
        return false;
      }
      ActivityStage2DestinationSelectPrivate12002QueryV1 query{};
      BindQuery(query, adapter, mailbox, current, revision);
      query.province_id = static_cast<std::int32_t>(province);
      if (!RunQuery(query, &ExecuteActivityStage2DestinationSelectPrivate12002V1, failure))
        return false;
      const auto native = ck3_11906::SerializeActivityStage2DestinationSelectPrivateV1(query);
      const bool reclaimed = Reclaim(query, failure);
      const bool green = query.failure.empty() && query.result.status ==
          bridge::ActivityStage2DestinationStatusV1::verified_stage_five;
      serialized = ResultFrame(request_id, step, "activity_stage2_destination_select",
          native, reclaimed && green, query.result.submitted, false,
          reclaimed && green ? "available" : "red",
          reclaimed ? std::string_view{} : "reclaim_red");
      return true;
    }
    if (step == kActivityStage2ConfirmPrivate12002StepV1) {
      if (!ParseActorDate(payload, current) || !ParseFeastOption(payload)) {
        failure = "activity stage-2 confirm request invalid";
        return false;
      }
      ActivityStage2ConfirmPrivate12002QueryV1 query{};
      BindQuery(query, adapter, mailbox, current, revision);
      if (!RunQuery(query, &ExecuteActivityStage2ConfirmPrivate12002V1, failure))
        return false;
      const auto native = SerializeActivityStage2ConfirmPrivate12002V1(query);
      const bool reclaimed = Reclaim(query, failure);
      const bool green = query.failure.empty() &&
          query.stage_two_confirm_result.status ==
              bridge::ActivityStage2ConfirmStatusV1::stage_five_verified;
      serialized = ResultFrame(request_id, step, "activity_stage2_confirm",
          native, reclaimed && green, query.stage_two_confirm_result.submitted,
          false, reclaimed && green ? "available" : "red",
          reclaimed ? std::string_view{} : "reclaim_red");
      return true;
    }
#endif

#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_CANSTART_PRIVATE_V1)
    if (step == ck3_11906::kActivityStage5CanStartPrivateStepV1) {
      if (!ParseActorDate(payload, current) || !ParseFeastStage(payload, 5, false)) {
        failure = "activity stage-5 CanStart request invalid";
        return false;
      }
      ActivityStage5CanStartPrivate12002QueryV1 query{};
      BindQuery(query, adapter, mailbox, current, revision);
      if (!RunQuery(query, &ExecuteActivityStage5CanStartPrivate12002V1, failure))
        return false;
      return FinishRead(query, &SerializeActivityStage5CanStartPrivate12002V1,
          adapter, current, request_id, step, "activity_stage5_canstart",
          serialized, failure, true);
    }
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_GOLD_COST_PRIVATE_V1)
    if (step == kActivityStage5GoldCostPrivateStepV1) {
      if (!ParseActorDate(payload, current) || !ParseFeastStage(payload, 5, false)) {
        failure = "activity stage-5 Gold request invalid";
        return false;
      }
      ActivityStage5GoldCostPrivateQueryV1 query{};
      BindQuery(query, adapter, mailbox, current, revision);
      query.passive_cost = passive_cost;
      if (!RunQuery(query, &ExecuteActivityStage5GoldCostPrivateV1, failure))
        return false;
      return FinishRead(query, &SerializeActivityStage5GoldCostPrivateV1,
          adapter, current, request_id, step, "activity_stage5_gold_cost",
          serialized, failure, true);
    }
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_FEAST_FULL_COST_PRIVATE_V1)
    if (step == kActivityStage5FeastFullCostPrivateStepV1) {
      if (!ParseActorDate(payload, current) || !ParseFeastStage(payload, 5, false)) {
        failure = "activity stage-5 full-cost request invalid";
        return false;
      }
      ActivityStage5FeastFullCostPrivateQueryV1 query{};
      BindQuery(query, adapter, mailbox, current, revision);
      query.passive_cost = passive_cost;
      if (!RunQuery(query, &ExecuteActivityStage5FeastFullCostPrivateV1, failure))
        return false;
      return FinishRead(query, &SerializeActivityStage5FeastFullCostPrivateV1,
          adapter, current, request_id, step, "activity_stage5_feast_full_cost",
          serialized, failure, true);
    }
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_STAGE5_START_PRIVATE_V1)
    if (step == ck3_11906::kActivityFeastStage5InputsPrivateStepV1 ||
        step == ck3_11906::kActivityFeastStage5StartPrivateStepV1 ||
        step == ck3_11906::kActivityFeastHostedPostPrivateStepV1) {
      const bool start = step == ck3_11906::kActivityFeastStage5StartPrivateStepV1;
      const bool post = step == ck3_11906::kActivityFeastHostedPostPrivateStepV1;
      ActivityFeastStage5Private12002QueryV1 query{};
      BindQuery(query, adapter, mailbox, current, revision);
      query.resolve_script_identifier = &ResolveScriptIdentifier;
      query.passive_cost = passive_cost;
      query.mode = post ? ck3_11906::ActivityFeastStage5PrivateModeV1::hosted_post
          : start ? ck3_11906::ActivityFeastStage5PrivateModeV1::start_attempt
                  : ck3_11906::ActivityFeastStage5PrivateModeV1::start_inputs;
      if (!ParseActorDate(payload, current) ||
          (!post && !ParseFeastStage(payload, 5, true))) {
        failure = "activity feast Stage-5 request invalid";
        return false;
      }
      if (start) {
        constexpr std::array<std::string_view, 4> keys{
            "reserve_gold_raw", "reserve_treasury_raw",
            "reserve_piety_raw", "reserve_barter_goods_raw"};
        if (!bridge::JsonBooleanField(payload, "policy_positive", query.policy_positive) ||
            !bridge::JsonBooleanField(payload, "previous_submit_pending",
                                       query.previous_submit_pending)) {
          failure = "activity feast Start policy request invalid";
          return false;
        }
        for (std::size_t index = 0; index < keys.size(); ++index) {
          std::uint64_t reserve = 0;
          if (!bridge::JsonUnsignedField(payload, keys[index], reserve) ||
              reserve > static_cast<std::uint64_t>(
                  (std::numeric_limits<std::int64_t>::max)())) {
            failure = "activity feast Start reserve request invalid";
            return false;
          }
          query.reserve_raw[index] = static_cast<std::int64_t>(reserve);
        }
      }
      if (!RunQuery(query, &ExecuteActivityFeastStage5Private12002V1, failure))
        return false;
      const bool stable = !query.frame_changed &&
          (query.start.invoked || SameFrame(adapter, current));
      const auto native = stable
          ? SerializeActivityFeastStage5Private12002V1(query) : std::string{};
      const bool reclaimed = Reclaim(query, failure);
      if (native.empty() || (!query.failure.empty() && !start)) {
        if (failure.empty()) failure = query.failure.empty()
            ? "activity feast Stage-5 paused read unavailable" : query.failure;
        return false;
      }
      if (!reclaimed && !query.start.invoked) return false;
      const bool pending = start && query.start.status ==
          bridge::ActivityFeastStage5StartStatusV1::submitted_pending;
      std::string value = native;
      if (start) {
        value = "{\"schema\":\"activity-feast-stage5-start-private-action-v1\",\"submitted\":";
        value += query.start.invoked ? "true" : "false";
        value += ",\"native_status\":";
        AppendString(value, pending && reclaimed ? "submitted_pending"
            : query.start.invoked ? "submission_outcome_unknown" : "rejected");
        value += ",\"failure\":";
        AppendString(value, query.failure);
        value += ",\"precondition\":" + native + '}';
      }
      serialized = ResultFrame(request_id, step,
          post ? "activity_feast_hosted_post"
               : start ? "activity_feast_stage5_start"
                       : "activity_feast_stage5_start_inputs",
          value, reclaimed && (!start || pending),
          !start || query.start.invoked, !start,
          start ? (pending && reclaimed ? "pending" : "red") : "available",
          reclaimed ? std::string_view{} : "reclaim_red");
      return true;
    }
#endif
    failure = "activity feast private route unavailable";
    return false;
  } catch (...) {
    serialized.clear();
    failure = "activity feast private router exception";
    return false;
  }
}
} // namespace xar::ck3_12002
