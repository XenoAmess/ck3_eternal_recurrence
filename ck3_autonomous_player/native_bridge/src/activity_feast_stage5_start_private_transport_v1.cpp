#include "activity_feast_stage5_start_private_transport_v1.hpp"

#include <windows.h>

#include <array>
#include <cstring>
#include <limits>

namespace xar::ck3_11906 {
namespace {

struct Context {
  ActivityFeastStage5PrivateQueryV1 *query = nullptr;
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
         ReadSnapshot(context.query->bindings, snapshot) &&
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
  const auto cast = reinterpret_cast<NativeCast>(context.base + 0x3E631F4);
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
    success = bridge::InvokeActivityStage5NativeNamedFeastCostV1(
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
  const auto predicate = reinterpret_cast<Predicate>(context.base + 0x10B0DA0);
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
    success = bridge::InvokeActivityFeastNativePlannerGuestJoinV1(
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
    activity = bridge::InvokeActivityFeastNativePlannerActivityV1(
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
    success = bridge::InvokeActivityFeastNativeTravelDaysV1(
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
  if (!ReadAt(type, 0, vtable) || vtable != base + 0x440E308 ||
      !ReadAt(type, 0x28, size) || !ReadAt(type, 0x30, capacity) ||
      size != sizeof(key) - 1 || size > capacity ||
      (capacity > 15 && !ReadAt(type, 0x18, data)))
    return false;
  std::array<char, sizeof(key) - 1> actual{};
  return ReadMemory(nullptr, data, actual.data(), actual.size()) &&
         std::memcmp(actual.data(), key, actual.size()) == 0;
}

bool GenericOption(Context &context, std::int32_t identifier) noexcept {
  const auto &bindings = context.query->bindings;
  if (identifier < 0 || bindings.get_script_identifier_table == nullptr ||
      bindings.resolve_script_identifier_name == nullptr ||
      bindings.script_identifier_name_fallback == nullptr)
    return false;
  bool match = false;
  __try {
    void *const table = bindings.get_script_identifier_table();
    if (table != nullptr) {
      const std::string *const name =
          bindings.resolve_script_identifier_name(table, identifier);
      match = name != nullptr &&
              name != bindings.script_identifier_name_fallback &&
              *name == "feast_type_generic";
    }
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    match = false;
  }
  return match;
}

bool ResolvePlannerAndOption(Context &context,
                             const bridge::ActivityHostedIdentityFrameV1 &frame,
                             std::uintptr_t &planner) noexcept {
  planner = 0;
  std::uintptr_t root = 0, idler = 0, gfx = 0, handler = 0;
  std::uintptr_t vtable = 0, owner = 0, type = 0, option = 0;
  std::uint32_t played_id = 0;
  std::int32_t stage = -1, option_id = -1;
  if (!ReadAt(context.base, 0x570F7B8, root) || root == 0 ||
      !ReadAt(root, 0x10, idler) || idler == 0)
    return false;
  gfx = CastIdler(&context, idler, context.base + 0x501EF28,
                  context.base + 0x501EF50);
  if (gfx == 0 || !ReadAt(gfx, 0, vtable) ||
      vtable != context.base + 0x40B1D30 ||
      !ReadAt(gfx, 0x88, handler) || handler == 0 ||
      !ReadAt(handler, 0, vtable) ||
      vtable != context.base + 0x40AF630 ||
      !ReadAt(handler, 0x3C0, planner) || planner == 0 ||
      !ReadAt(planner, 0, vtable) ||
      vtable != context.base + 0x41205F0 ||
      !ReadAt(planner, 0xD0, owner) || owner != handler ||
      !ReadAt(planner, 0x1AB0, stage) || stage != 5 ||
      !ReadAt(planner, 0x1530, type) || type == 0 ||
      !IsFeastType(context.base, type) ||
      !ReadAt(context.base, 0x4FE7EE0, played_id) ||
      played_id != static_cast<std::uint32_t>(frame.actor_character_id))
    return false;
  using SelectedOption = void *(*)(void *);
  const auto getter =
      reinterpret_cast<SelectedOption>(context.base + 0x10AEAE0);
  __try {
    option = reinterpret_cast<std::uintptr_t>(
        getter(reinterpret_cast<void *>(planner)));
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    option = 0;
  }
  if (option == 0 || !ReadAt(option, 0, vtable) ||
      vtable != context.base + 0x440E1D0 ||
      !ReadAt(option, 8, option_id) || !GenericOption(context, option_id))
    return false;
  return true;
}

bridge::ActivityPlannerDiagEnvironmentV1 Diagnostic(Context &context) noexcept {
  return {true, bridge::kActivityPlannerDiagExeSha256V1, context.base,
          &context, &ReadMemory, &ReadPlannerFrame, &CastIdler, &Visibility};
}

bridge::ActivityHostedIdentityEnvironmentV1 HostedEnvironment(
    Context &context) noexcept {
  return {true, bridge::kActivityHostedIdentityExeSha256V1, context.base,
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
  query.guest_route_qualified =
      bridge::IsActivityFeastSelectedGuestRouteQualifiedV1(output);
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
    returned = bridge::InvokeActivityFeastNativeCommitV1(
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
  return true;
}

void AppendIdentities(std::string &payload,
                      const std::array<bridge::ActivityHostedIdentityV1, 64> &ids,
                      std::uint32_t count) {
  payload += "[";
  for (std::uint32_t index = 0; index < count; ++index) {
    if (index != 0) payload += ",";
    payload += "{\"activity_id\":" + std::to_string(ids[index].activity_id) +
               ",\"host_character_id\":" +
               std::to_string(ids[index].host_character_id) +
               ",\"activity_type_key\":\"";
    payload.append(ids[index].type_key.data(), ids[index].type_key_size);
    payload += "\"}";
  }
  payload += "]";
}

void AppendBalances(std::string &payload,
                    const bridge::ActivityFeastResourceBalancesV1 &balances) {
  payload += "\"balances\":{";
  for (std::size_t index = 0; index < bridge::kActivityFeastCostKeysV1.size();
       ++index) {
    if (index != 0) payload += ",";
    payload += "\"" + std::string(bridge::kActivityFeastCostKeysV1[index]) +
               "\":{";
    payload += "\"available\":";
    payload += balances.available[index] ? "true" : "false";
    payload += ",\"raw\":";
    payload += balances.available[index]
                   ? std::to_string(balances.raw[index]) : "null";
    payload += "}";
  }
  payload += "}";
}

} // namespace

bool ExecuteActivityFeastStage5PrivateV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<ActivityFeastStage5PrivateQueryV1 *>(opaque);
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
      mailbox.executor != &ExecuteActivityFeastStage5PrivateV1 ||
      mailbox.executor_context != query)
    return false;
  try {
    ++query->invocations;
    game::Snapshot current{};
    if (!ReadSnapshot(query->bindings, current) ||
        current != query->expected_snapshot || !current.paused ||
        !current.map_ready || !current.has_played_character ||
        !current.played_character_alive || current.date_raw != stamp.date_raw) {
      query->frame_changed = true;
      query->failure = "published_frame_changed";
      query->completed = true;
      return true;
    }
    const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    if (!query->bindings.enabled || base == 0) {
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
          bridge::kActivityHostedIdentityExeSha256V1;
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

std::string SerializeActivityFeastStage5PrivateV1(
    const ActivityFeastStage5PrivateQueryV1 &query) {
  if (!query.completed || query.frame_changed) return {};
  if (query.mode == ActivityFeastStage5PrivateModeV1::hosted_post) {
    if (!query.post.hosted_identities_observed) return {};
    const auto &post = query.post;
    std::string payload =
        "{\"schema\":\"activity-feast-hosted-post-private-read-v1\",";
    payload += "\"snapshot_revision\":" +
               std::to_string(post.frame.revision) +
               ",\"date_raw\":" + std::to_string(post.frame.date_raw) +
               ",\"actor_character_id\":" +
               std::to_string(post.frame.actor_character_id) + ",";
    AppendBalances(payload, post.balances);
    payload += ",\"hosted_activities\":";
    AppendIdentities(payload, post.hosted, post.hosted_count);
    payload += ",\"read_only\":true,\"advertised\":false}";
    return payload;
  }
  if (!query.inputs.four_costs_observed ||
      !query.inputs.hosted_identities_observed)
    return {};
  const auto &input = query.inputs;
  std::string payload =
      "{\"schema\":\"activity-feast-stage5-start-inputs-private-v1\",";
  payload += "\"snapshot_revision\":" +
             std::to_string(input.frame.revision) +
             ",\"date_raw\":" + std::to_string(input.frame.date_raw) +
             ",\"actor_character_id\":" +
             std::to_string(input.frame.actor_character_id) +
             ",\"activity_key\":\"activity_feast\","
             "\"selected_option_key\":\"feast_type_generic\","
             "\"planning_stage\":5,\"scale\":100000,";
  payload += "\"normal_refresh_sequence\":" +
             std::to_string(input.normal_cost_refresh_sequence) +
             ",\"final_can_start\":" +
             std::string(input.final_can_start ? "true" : "false") +
             ",\"resources\":{";
  for (std::size_t index = 0; index < bridge::kActivityFeastCostKeysV1.size();
       ++index) {
    if (index != 0) payload += ",";
    payload += "\"" + std::string(bridge::kActivityFeastCostKeysV1[index]) +
               "\":{\"resource_index\":" +
               std::to_string(input.cost_resource_indices[index]) +
               ",\"configured_cost_raw\":" +
               std::to_string(input.cost_raw[index]) + "}";
  }
  payload += "},";
  AppendBalances(payload, input.balances);
  payload += ",\"hosted_activities\":";
  AppendIdentities(payload, input.hosted, input.hosted_count);
  payload += ",\"guest_join_status\":\"";
  payload += bridge::ActivityFeastGuestJoinStatusKeyV1(query.guest_status);
  payload += "\",\"selected_nonhost_count\":";
  payload += query.guest_status == bridge::ActivityFeastGuestJoinStatusV1::observed
                 ? std::to_string(query.selected_nonhost_count) : "null";
  payload += ",\"positive_join_count\":";
  payload += query.guest_status == bridge::ActivityFeastGuestJoinStatusV1::observed
                 ? std::to_string(query.positive_join_count) : "null";
  payload += ",\"timely_positive_join_count\":";
  payload += query.guest_status == bridge::ActivityFeastGuestJoinStatusV1::observed
                 ? std::to_string(query.timely_positive_join_count) : "null";
  payload += ",\"arrival_time_observed\":";
  payload += query.guest_status == bridge::ActivityFeastGuestJoinStatusV1::observed &&
                     query.arrival_time_observed ? "true" : "false";
  payload += ",\"native_guest_route_qualified\":";
  payload += query.guest_route_qualified ? "true" : "false";
  payload += ",\"read_only\":";
  payload += query.mode == ActivityFeastStage5PrivateModeV1::start_inputs
                 ? "true" : "false";
  payload += ",\"advertised\":false}";
  return payload;
}

} // namespace xar::ck3_11906
