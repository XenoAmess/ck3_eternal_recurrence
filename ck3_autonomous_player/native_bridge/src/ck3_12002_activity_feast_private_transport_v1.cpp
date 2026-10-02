#include "ck3_12002_activity_feast_private_transport_v1.hpp"
#include "ck3_12002_activity_feast_guest_transport.hpp"
#include "activity_feast_ordinary_guest_selection_v1.hpp"
#include "xar_bridge/ck3_12002_feast_planner.hpp"
#include "xar_bridge/ck3_12002_feast_guests_abi.hpp"

#include <windows.h>

#include <array>
#include <cstring>
#include <limits>

namespace xar::ck3_12002 {
using ck3_11906::ActivityFeastStage5PrivateModeV1;
using ck3_11906::MainThreadExecutionStampV1;
using ck3_11906::MainThreadQueryMailboxStateV1;
using ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs;
namespace {

struct Context {
  ActivityFeastStage5Private12002QueryV1 *query = nullptr;
  std::uintptr_t base = 0;
  DWORD owner_thread_id = 0;
};

bool ReadMemory(void *, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  SIZE_T read = 0;
  return address != 0 && output != nullptr && size != 0 &&
         ReadProcessMemory(GetCurrentProcess(),
                           reinterpret_cast<const void *>(address), output,
                           size, &read) != 0 && read == size;
}

template <typename T>
bool ReadAt(std::uintptr_t base, std::size_t offset, T &value) noexcept {
  return base != 0 &&
         offset <= (std::numeric_limits<std::uintptr_t>::max)() - base &&
         ReadMemory(nullptr, base + offset, &value, sizeof(value));
}

bool ReadCurrent(Context &context, game::Snapshot &snapshot) noexcept {
  return GetCurrentThreadId() == context.owner_thread_id &&
         context.query->read_snapshot != nullptr &&
         context.query->read_snapshot(context.query->native_context, snapshot) &&
         snapshot == context.query->expected_snapshot;
}

bool ReadPlannerFrame(void *opaque,
                      bridge::ActivityPlannerDiagFrameV1 &output) noexcept {
  auto &context = *static_cast<Context *>(opaque);
  game::Snapshot snapshot{};
  if (!ReadCurrent(context, snapshot)) return false;
  output = {context.query->expected_revision, snapshot.date_raw,
            snapshot.played_character_id, true, snapshot.paused,
            snapshot.map_ready,
            snapshot.has_played_character && snapshot.played_character_alive};
  return true;
}

bool ReadHostedFrame(void *opaque,
                     bridge::ActivityHostedIdentityFrameV1 &output) noexcept {
  bridge::ActivityPlannerDiagFrameV1 frame{};
  if (!ReadPlannerFrame(opaque, frame)) return false;
  output = {frame.revision, frame.date_raw, frame.actor_character_id,
            frame.application_main_thread, frame.paused, frame.map_ready,
            frame.actor_alive};
  return true;
}

std::uintptr_t CastIdler(void *opaque, std::uintptr_t source,
                         std::uintptr_t source_type,
                         std::uintptr_t target_type) noexcept {
  auto &context = *static_cast<Context *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id || source == 0 ||
      context.base == 0)
    return 0;
  using NativeCast = void *(*)(void *, std::int32_t, void *, void *, std::int32_t);
  const auto cast = reinterpret_cast<NativeCast>(context.base + 0x4260E94);
  void *result = nullptr;
  __try {
    result = cast(reinterpret_cast<void *>(source), 0,
                  reinterpret_cast<void *>(source_type),
                  reinterpret_cast<void *>(target_type), 0);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    result = nullptr;
  }
  return reinterpret_cast<std::uintptr_t>(result);
}

bool Visibility(void *opaque, std::uintptr_t planner,
                std::uintptr_t entry, bool &visible) noexcept {
  auto &context = *static_cast<Context *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id || planner == 0 ||
      entry == 0)
    return false;
  const auto callback = reinterpret_cast<bool (*)(void *)>(entry);
  __try {
    visible = callback(reinterpret_cast<void *>(planner));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

bool NamedCost(void *opaque, std::uintptr_t module_base,
               std::uintptr_t breakdown, std::string_view key,
               std::uint32_t &index, std::int64_t &value) noexcept {
  auto &context = *static_cast<Context *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id ||
      module_base != context.base || breakdown == 0)
    return false;
  bool success = false;
  __try {
    success = bridge::InvokeActivityStage5NativeNamedFeastCost12002V1(
        nullptr, module_base, breakdown, key, index, value);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    success = false;
  }
  return success;
}

bool EvaluateCanStart(void *opaque, std::uintptr_t planner,
                      bool &value) noexcept {
  auto &context = *static_cast<Context *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id || planner == 0 ||
      context.base == 0)
    return false;
  using Predicate = bool (*)(void *, void *);
  const auto predicate = reinterpret_cast<Predicate>(context.base + kFeastFinalCanStartRva);
  __try {
    value = predicate(reinterpret_cast<void *>(planner), nullptr);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

bool EvaluateGuestJoin(void *opaque, std::uintptr_t base,
                       std::uintptr_t planner, std::uintptr_t character,
                       std::int64_t &value) noexcept {
  auto &context = *static_cast<Context *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id ||
      base != context.base) return false;
  bool success = false;
  __try {
    success = bridge::InvokeActivityFeastNativePlannerGuestJoin12002V1(
        nullptr, base, planner, character, value);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    success = false;
  }
  return success;
}

std::uintptr_t EvaluateGuestActivity(void *opaque, std::uintptr_t base,
                                     std::uintptr_t planner) noexcept {
  auto &context = *static_cast<Context *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id ||
      base != context.base) return 0;
  std::uintptr_t activity = 0;
  __try {
    activity = bridge::InvokeActivityFeastNativePlannerActivity12002V1(
        nullptr, base, planner);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    activity = 0;
  }
  return activity;
}

bool EvaluateGuestTravelDays(void *opaque, std::uintptr_t base,
                             std::uintptr_t character,
                             std::uintptr_t destination,
                             std::int32_t &days) noexcept {
  auto &context = *static_cast<Context *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id ||
      base != context.base) return false;
  bool success = false;
  __try {
    success = bridge::InvokeActivityFeastNativeTravelDays12002V1(
        nullptr, base, character, destination, days);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    success = false;
  }
  return success;
}

bool IsFeastType(std::uintptr_t base, std::uintptr_t type) noexcept {
  constexpr char key[] = "activity_feast";
  std::uintptr_t vtable = 0, data = type + 0x18;
  std::uint64_t size = 0, capacity = 0;
  if (!ReadAt(type, 0, vtable) || vtable != base + 0x48BFE50 ||
      !ReadAt(type, 0x28, size) || !ReadAt(type, 0x30, capacity) ||
      size != sizeof(key) - 1 || size > capacity ||
      (capacity > 15 && !ReadAt(type, 0x18, data)))
    return false;
  std::array<char, sizeof(key) - 1> actual{};
  return ReadMemory(nullptr, data, actual.data(), actual.size()) &&
         std::memcmp(actual.data(), key, actual.size()) == 0;
}

bool GenericOption(Context &context, std::int32_t identifier) noexcept {
  if (identifier < 0 || context.query->resolve_script_identifier == nullptr)
    return false;
  std::string_view copied{};
  return context.query->resolve_script_identifier(
             context.query->native_context, identifier, copied) &&
         copied == "feast_type_generic";
}

bool ResolvePlannerAndOption(Context &context,
                             const bridge::ActivityHostedIdentityFrameV1 &frame,
                             std::uintptr_t &planner) noexcept {
  bridge::ActivityPlannerDiagEnvironmentV1 environment{
      true, kFeastExecutableSha256, context.base, &context,
      &ReadMemory, &ReadPlannerFrame, &CastIdler, &Visibility};
  const bridge::ActivityPlannerDiagFrameV1 expected{
      frame.revision, frame.date_raw, frame.actor_character_id,
      frame.application_main_thread, frame.paused, frame.map_ready,
      frame.actor_alive};
  bridge::ActivityPlannerIdentityV1 identity{};
  if (!bridge::ResolveActivityPlannerIdentityV1(environment, expected, identity) ||
      identity.stage != 5 || !IsFeastType(context.base, identity.activity_type))
    return false;
  planner = identity.planner;
  using SelectedOption = void *(*)(void *);
  const auto getter = reinterpret_cast<SelectedOption>(context.base + 0x11B64C0);
  std::uintptr_t option = 0, vtable = 0;
  std::int32_t option_id = -1;
  __try {
    option = reinterpret_cast<std::uintptr_t>(
        getter(reinterpret_cast<void *>(planner)));
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    option = 0;
  }
  return option != 0 && ReadAt(option, 0, vtable) &&
         vtable == context.base + 0x48BFD18 &&
         ReadAt(option, 8, option_id) && GenericOption(context, option_id);
}

bridge::ActivityPlannerDiagEnvironmentV1 Diagnostic(Context &context) noexcept {
  return {true, kFeastExecutableSha256, context.base,
          &context, &ReadMemory, &ReadPlannerFrame, &CastIdler, &Visibility};
}

bridge::ActivityHostedIdentityEnvironmentV1 HostedEnvironment(
    Context &context) noexcept {
  return {true, kFeastExecutableSha256, context.base,
          &context, &ReadMemory, &ReadHostedFrame};
}

bool Capture(void *opaque,
             const bridge::ActivityHostedIdentityFrameV1 &expected,
             bridge::ActivityFeastStage5StartSnapshotV1 &output) noexcept {
  auto &context = *static_cast<Context *>(opaque);
  auto &query = *context.query;
  if (query.passive_cost == nullptr || !query.passive_cost->installed)
    return false;
  const auto diagnostic = Diagnostic(context);
  const bridge::ActivityPlannerDiagFrameV1 planner_expected{
      expected.revision, expected.date_raw, expected.actor_character_id,
      expected.application_main_thread, expected.paused, expected.map_ready,
      expected.actor_alive};
  bridge::ActivityStage5FeastFullCostEnvironmentV1 cost_environment{};
  cost_environment.enabled = true;
  cost_environment.gold.enabled = true;
  cost_environment.gold.diagnostic = diagnostic;
  cost_environment.gold.passive_cost = query.passive_cost;
  cost_environment.invoke_named_cost = &NamedCost;
  cost_environment.named_context = &context;
  const auto cost = bridge::ReadActivityStage5FeastFullCostV1(
      cost_environment, planner_expected);
  query.cost_status = cost.status;
  if (cost.status != bridge::ActivityStage5FeastFullCostStatusV1::observed)
    return false;
  bridge::ActivityStage5CanStartEnvironmentV1 start_environment{};
  start_environment.diagnostic = diagnostic;
  start_environment.evaluate = &EvaluateCanStart;
  const auto can_start = bridge::ReadActivityStage5CanStartV1(
      start_environment, planner_expected);
  query.can_start_status = can_start.status;
  if (can_start.status != bridge::ActivityStage5CanStartStatusV1::observed ||
      can_start.frame != cost.frame)
    return false;
  bridge::ActivityFeastGuestJoinEnvironmentV1 guest_environment{};
  guest_environment.enabled = true;
  guest_environment.diagnostic = diagnostic;
  guest_environment.passive_cost = query.passive_cost;
  guest_environment.invoke_join = &EvaluateGuestJoin;
  guest_environment.join_context = &context;
  guest_environment.invoke_activity = &EvaluateGuestActivity;
  guest_environment.invoke_travel_days = &EvaluateGuestTravelDays;
  guest_environment.arrival_context = &context;
  const auto guests = bridge::ReadActivityFeastGuestJoinV1(
      guest_environment, planner_expected);
  query.guest_status = guests.status;
  if (guests.status == bridge::ActivityFeastGuestJoinStatusV1::observed &&
      guests.frame == cost.frame &&
      guests.normal_refresh_sequence == cost.normal_refresh_sequence) {
    query.selected_nonhost_count = guests.selected_nonhost_count;
    query.positive_join_count = guests.positive_join_count;
    query.timely_positive_join_count = guests.timely_positive_join_count;
    query.arrival_time_observed = guests.arrival_time_observed;
  } else if (guests.status ==
             bridge::ActivityFeastGuestJoinStatusV1::observed) {
    query.guest_status =
        bridge::ActivityFeastGuestJoinStatusV1::configuration_changed;
  }
  bridge::ActivityFeastOrdinaryGuestRouteV1 ordinary{};
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1)
  ordinary.candidate = bridge::ReadActivityFeastGuestCandidateV1(
      guest_environment, planner_expected);
  if (ordinary.candidate.status ==
      bridge::ActivityFeastGuestCandidateStatusV1::observed) {
    ActivityFeastGuestRulePrivateQueryV1 rule_query{};
    rule_query.enabled = true;
    rule_query.module_base = context.base;
    rule_query.executable_sha256 = kFeastExecutableSha256;
    rule_query.snapshot_context = query.native_context;
    rule_query.read_snapshot = query.read_snapshot;
    rule_query.expected_snapshot = query.expected_snapshot;
    rule_query.expected_revision = query.expected_revision;
    rule_query.passive_cost = query.passive_cost;
    rule_query.authored_rule_key = ordinary.authored_rule_key;
    rule_query.query_provenance = true;
    rule_query.provenance_observer = query.provenance_observer;
    rule_query.candidate_character_id =
        static_cast<std::uint32_t>(ordinary.candidate.character_id);
    bool rule_observed = ReadActivityFeastGuestRuleSources12002V1(
        rule_query, context.owner_thread_id);
    if (rule_observed &&
        rule_query.rule.status == bridge::ActivityFeastGuestRuleStatusV1::observed_active &&
        rule_query.provenance.status == bridge::ActivityGuestRuleProvenanceStatusV1::observed) {
      const auto candidate = SelectFeastOrdinaryCloseFamilyCandidateV1(
          guest_environment, planner_expected, rule_query.provenance,
          ordinary.candidate);
      if (candidate != ordinary.candidate) {
        ordinary.candidate = candidate;
        if (candidate.status == bridge::ActivityFeastGuestCandidateStatusV1::observed) {
          rule_query.candidate_character_id = static_cast<std::uint32_t>(candidate.character_id);
          rule_observed = ReadActivityFeastGuestRuleSources12002V1(
              rule_query, context.owner_thread_id);
        }
      }
    }
    if (rule_observed) {
      ordinary.rule_status = rule_query.rule.status;
      ordinary.rule_active = rule_query.rule.active;
      ordinary.native_key_hash = rule_query.rule.native_key_hash;
      ordinary.provenance_status = rule_query.provenance.status;
      ordinary.provenance_key_hash = rule_query.provenance.native_key_hash;
      ordinary.provenance_refresh_sequence = rule_query.provenance.normal_refresh_sequence;
      ordinary.candidate_membership = rule_query.provenance.candidate_membership;
      ordinary.raw_rule_character_count = rule_query.provenance.raw_rule_character_count;
      ordinary.filtered_rule_character_count = rule_query.provenance.filtered_rule_character_count;
    } else {
      ordinary.rule_status = bridge::ActivityFeastGuestRuleStatusV1::frame_changed;
      ordinary.provenance_status = bridge::ActivityGuestRuleProvenanceStatusV1::frame_changed;
    }
    const auto candidate_after = bridge::ReadActivityFeastGuestCandidateV1(
        guest_environment, planner_expected,
        ordinary.candidate.status == bridge::ActivityFeastGuestCandidateStatusV1::observed
            ? ordinary.candidate.character_id : 0);
    if (candidate_after != ordinary.candidate)
      ordinary.candidate.status = bridge::ActivityFeastGuestCandidateStatusV1::configuration_changed;
  }
#endif
  const auto hosted_environment = HostedEnvironment(context);
  const auto balances = bridge::ReadActivityFeastResourceBalancesV1(
      hosted_environment, expected);
  query.balance_status = balances.status;
  if (balances.status != bridge::ActivityFeastBalanceStatusV1::observed_partial)
    return false;
  const auto identities = bridge::ReadActivityHostedIdentityV1(
      hosted_environment, expected);
  query.hosted_status = identities.status;
  if (identities.status != bridge::ActivityHostedIdentityStatusV1::observed)
    return false;
  std::uintptr_t planner = 0, planner_after = 0;
  if (!ResolvePlannerAndOption(context, expected, planner) ||
      !ResolvePlannerAndOption(context, expected, planner_after) ||
      planner_after != planner)
    return false;
  game::Snapshot final{};
  if (!ReadCurrent(context, final)) return false;
  output = {};
  output.frame = expected;
  output.planner = planner;
  output.normal_cost_refresh_sequence = cost.normal_refresh_sequence;
  output.feast_type_verified = true;
  output.generic_option_verified = true;
  output.final_can_start_observed = true;
  output.final_can_start = can_start.final_can_start;
  output.four_costs_observed = true;
  output.cost_resource_indices = cost.resource_indices;
  output.cost_raw = cost.configured_cost_raw;
  output.balances = balances.value;
  output.hosted_identities_observed = true;
  output.hosted_count = identities.hosted_count;
  output.hosted = identities.hosted;
  output.selected_guests = guests;
  output.ordinary_guest = ordinary;
  bridge::FeastOutcomeEnvironmentV1 outcome_environment{};
  outcome_environment.identity = hosted_environment;
  const auto outcomes = bridge::ReadFeastOutcomeValues12002(
      outcome_environment, expected);
  if (outcomes.status == bridge::FeastOutcomeStatusV1::observed ||
      outcomes.status == bridge::FeastOutcomeStatusV1::observed_partial)
    output.outcome_values = outcomes.value;
  query.guest_route_qualified =
      bridge::IsActivityFeastGuestRouteQualifiedV1(output);
  return true;
}

bool InvokeCommit(void *opaque, std::uintptr_t base,
                  std::uintptr_t planner) noexcept {
  auto &context = *static_cast<Context *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id ||
      base != context.base || planner == 0)
    return false;
  bool returned = false;
  __try {
    returned = bridge::InvokeActivityFeastNativeCommit12002V1(
        nullptr, base, planner);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    returned = false;
  }
  return returned;
}

bool CapturePost(Context &context,
                 const bridge::ActivityHostedIdentityFrameV1 &expected,
                 bridge::ActivityFeastStage5PostV1 &output) noexcept {
  const auto environment = HostedEnvironment(context);
  const auto balances = bridge::ReadActivityFeastResourceBalancesV1(
      environment, expected);
  context.query->balance_status = balances.status;
  if (balances.status != bridge::ActivityFeastBalanceStatusV1::observed_partial)
    return false;
  const auto identities = bridge::ReadActivityHostedIdentityV1(
      environment, expected);
  context.query->hosted_status = identities.status;
  if (identities.status != bridge::ActivityHostedIdentityStatusV1::observed)
    return false;
  game::Snapshot final{};
  if (!ReadCurrent(context, final)) return false;
  output.frame = expected;
  output.balances = balances.value;
  output.hosted_identities_observed = true;
  output.hosted_count = identities.hosted_count;
  output.hosted = identities.hosted;
  bridge::FeastOutcomeEnvironmentV1 outcome_environment{};
  outcome_environment.identity = environment;
  const auto outcomes = bridge::ReadFeastOutcomeValues12002(
      outcome_environment, expected);
  if (outcomes.status == bridge::FeastOutcomeStatusV1::observed ||
      outcomes.status == bridge::FeastOutcomeStatusV1::observed_partial)
    output.outcome_values = outcomes.value;
  return true;
}

} // namespace

bool ExecuteActivityFeastStage5Private12002V1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<ActivityFeastStage5Private12002QueryV1 *>(opaque);
  if (query == nullptr || query->mailbox == nullptr ||
      query->ticket.sequence == 0 || query->expected_revision == 0 ||
      query->invocations != 0 || stamp.pump_epoch == 0 ||
      stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 ||
      stamp.tls_initialized != 1 || stamp.tls_context == 0 ||
      stamp.tls_main_thread_marker != 1 || stamp.jomini_state == 0 ||
      stamp.game_state == 0 || GetCurrentThreadId() != stamp.thread_id)
    return false;
  auto &mailbox = *query->mailbox;
  if (mailbox.state.load(std::memory_order_acquire) !=
          MainThreadQueryMailboxStateV1::executing ||
      mailbox.stop_requested.load(std::memory_order_acquire) ||
      mailbox.failure_flags.load(std::memory_order_acquire) != 0 ||
      mailbox.published_sequence.load(std::memory_order_acquire) !=
          query->ticket.sequence ||
      mailbox.owner_thread_id.load(std::memory_order_acquire) != stamp.thread_id ||
      mailbox.paused_owner_verified_pump_epochs.load(std::memory_order_acquire) <
          kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
      mailbox.executor != &ExecuteActivityFeastStage5Private12002V1 ||
      mailbox.executor_context != query)
    return false;
  try {
    ++query->invocations;
    game::Snapshot current{};
    if (query->read_snapshot == nullptr ||
        !query->read_snapshot(query->native_context, current) ||
        current != query->expected_snapshot || !current.paused ||
        !current.map_ready || !current.has_played_character ||
        !current.played_character_alive || current.date_raw != stamp.date_raw) {
      query->frame_changed = true;
      query->failure = "published_frame_changed";
      query->completed = true;
      return true;
    }
    const auto base = query->module_base;
    if (!query->enabled || base == 0 ||
        query->executable_sha256 != kFeastExecutableSha256) {
      query->failure = "exact_activity_feast_stage5_build_unavailable";
      query->completed = true;
      return true;
    }
    Context context{query, base, stamp.thread_id};
    const bridge::ActivityHostedIdentityFrameV1 frame{
        query->expected_revision, current.date_raw,
        current.played_character_id, true, true, true, true};
    if (query->mode == ActivityFeastStage5PrivateModeV1::hosted_post) {
      if (!CapturePost(context, frame, query->post))
        query->failure = "native_activity_feast_post_read_unavailable";
    } else if (!Capture(&context, frame, query->inputs)) {
      query->failure = "native_activity_feast_stage5_inputs_unavailable";
    } else if (query->mode == ActivityFeastStage5PrivateModeV1::start_attempt) {
      bridge::ActivityFeastStage5StartEnvironmentV1 environment{};
      environment.enabled = true;
      environment.admitted_executable_sha256 =
          kFeastExecutableSha256;
      environment.module_base = base;
      environment.context = &context;
      environment.read_memory = &ReadMemory;
      environment.capture = &Capture;
      environment.invoke_commit = &InvokeCommit;
      bridge::ActivityFeastStage5StartRequestV1 request{};
      request.expected = frame;
      request.policy_approved = query->policy_positive &&
                                query->guest_route_qualified;
      request.previous_submit_pending = query->previous_submit_pending;
      request.reserve_raw = query->reserve_raw;
      query->start = bridge::StartActivityFeastStage5V1(environment, request);
      if (!query->guest_route_qualified)
        query->failure = "native_guest_route_unqualified";
      else if (query->start.status !=
               bridge::ActivityFeastStage5StartStatusV1::submitted_pending)
        query->failure = "native_activity_feast_start_pending_or_red";
    }
    query->completed = true;
    return true;
  } catch (...) {
    query->failure = "native_activity_feast_stage5_exception";
    query->completed = true;
    return true;
  }
}

std::string SerializeActivityFeastStage5Private12002V1(
    const ActivityFeastStage5Private12002QueryV1 &query) {
  return ck3_11906::SerializeActivityFeastStage5PrivateV1(query);
}

} // namespace xar::ck3_12002
