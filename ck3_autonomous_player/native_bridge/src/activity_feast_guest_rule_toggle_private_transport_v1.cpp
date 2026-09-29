#include "activity_feast_guest_rule_toggle_private_transport_v1.hpp"

#include <windows.h>

namespace xar::ck3_11906 {
namespace {

struct Context {
  ActivityFeastGuestRulePrivateQueryV1 *query = nullptr;
  std::uintptr_t module_base = 0;
  DWORD owner_thread_id = 0;
};

#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1)
std::string_view PassiveCostStatusKey(
    bridge::ActivityCostSlot12ReadStatusV1 status) noexcept {
  switch (status) {
  case bridge::ActivityCostSlot12ReadStatusV1::observed: return "observed";
  case bridge::ActivityCostSlot12ReadStatusV1::exact_build_rejected:
    return "exact_build_rejected";
  case bridge::ActivityCostSlot12ReadStatusV1::no_normal_refresh:
    return "no_normal_refresh";
  case bridge::ActivityCostSlot12ReadStatusV1::frame_changed:
    return "frame_changed";
  case bridge::ActivityCostSlot12ReadStatusV1::configuration_changed:
    return "configuration_changed";
  }
  return "unknown";
}
#endif

bool ReadMemory(void *, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  SIZE_T read = 0;
  return address != 0 && output != nullptr && size != 0 &&
         ReadProcessMemory(GetCurrentProcess(),
                           reinterpret_cast<const void *>(address), output,
                           size, &read) != 0 && read == size;
}

bool ReadFrame(void *opaque,
               bridge::ActivityPlannerDiagFrameV1 &output) noexcept {
  auto &context = *static_cast<Context *>(opaque);
  game::Snapshot snapshot{};
  if (GetCurrentThreadId() != context.owner_thread_id ||
      !ReadSnapshot(context.query->bindings, snapshot))
    return false;
  output = {context.query->expected_revision,
            snapshot.date_raw,
            snapshot.played_character_id,
            true,
            snapshot.paused,
            snapshot.map_ready,
            snapshot.has_played_character && snapshot.played_character_alive};
  return true;
}

std::uintptr_t CastIdler(void *opaque, std::uintptr_t source,
                         std::uintptr_t source_type,
                         std::uintptr_t target_type) noexcept {
  auto &context = *static_cast<Context *>(opaque);
  if (context.module_base == 0 || source == 0 ||
      GetCurrentThreadId() != context.owner_thread_id)
    return 0;
  using NativeCast = void *(*)(void *, std::int32_t, void *, void *, std::int32_t);
  const auto cast = reinterpret_cast<NativeCast>(context.module_base +
                                                 0x3E631F4);
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

bool InvokeVisibility(void *opaque, std::uintptr_t planner,
                      std::uintptr_t entry, bool &output) noexcept {
  auto &context = *static_cast<Context *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id || planner == 0 ||
      entry == 0)
    return false;
  const auto visible = reinterpret_cast<bool (*)(void *)>(entry);
  __try {
    output = visible(reinterpret_cast<void *>(planner));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

std::uint32_t Hash(void *opaque, std::uintptr_t base,
                   std::string_view key) noexcept {
  auto &context = *static_cast<Context *>(opaque);
  if (base != context.module_base ||
      GetCurrentThreadId() != context.owner_thread_id)
    return 0;
  using NativeHash = std::uint32_t(__fastcall *)(void *, const char *,
                                                  std::uint32_t);
  std::uint32_t hash = 0;
  __try {
    hash = reinterpret_cast<NativeHash>(base + 0x3B8B000)(
        nullptr, key.data(), static_cast<std::uint32_t>(key.size()));
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    hash = 0;
  }
  return hash;
}

std::uintptr_t Lookup(void *opaque, std::uintptr_t base,
                      std::uint32_t hash) noexcept {
  auto &context = *static_cast<Context *>(opaque);
  if (base != context.module_base ||
      GetCurrentThreadId() != context.owner_thread_id)
    return 0;
  using GetDatabase = void *(__fastcall *)();
  using NativeLookup = void *(__fastcall *)(void *, std::uint32_t);
  void *definition = nullptr;
  __try {
    auto *database = reinterpret_cast<GetDatabase>(base + 0x2C19210)();
    if (database != nullptr)
      definition = reinterpret_cast<NativeLookup>(base + 0x2C1B800)(
          database, hash);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    definition = nullptr;
  }
  return reinterpret_cast<std::uintptr_t>(definition);
}

bool Active(void *opaque, std::uintptr_t base, std::uintptr_t window,
            std::uintptr_t row, bool &output) noexcept {
  auto &context = *static_cast<Context *>(opaque);
  if (base != context.module_base || window == 0 || row == 0 ||
      GetCurrentThreadId() != context.owner_thread_id)
    return false;
  using NativeActive = bool(__fastcall *)(void *, void *);
  __try {
    output = reinterpret_cast<NativeActive>(base + 0x151C2B0)(
        reinterpret_cast<void *>(window), reinterpret_cast<void *>(row));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

bool Toggle(void *opaque, std::uintptr_t base, std::uintptr_t window,
            std::uintptr_t row) noexcept {
  auto &context = *static_cast<Context *>(opaque);
  if (base != context.module_base || window == 0 || row == 0 ||
      GetCurrentThreadId() != context.owner_thread_id)
    return false;
  using NativeToggle = void(__fastcall *)(void *, void *);
  __try {
    reinterpret_cast<NativeToggle>(base + 0x151C110)(
        reinterpret_cast<void *>(window), reinterpret_cast<void *>(row));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

} // namespace

bool ExecuteActivityFeastGuestRulePrivateV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<ActivityFeastGuestRulePrivateQueryV1 *>(opaque);
  if (query == nullptr || query->mailbox == nullptr ||
      query->passive_cost == nullptr || query->ticket.sequence == 0 ||
      query->expected_revision == 0 || query->invocations != 0 ||
      stamp.pump_epoch == 0 || stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      stamp.jomini_state == 0 || stamp.game_state == 0 ||
      GetCurrentThreadId() != stamp.thread_id)
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
      mailbox.executor != &ExecuteActivityFeastGuestRulePrivateV1 ||
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
    if (!query->bindings.enabled || base == 0 ||
        !query->passive_cost->installed) {
      query->failure = "exact_activity_feast_guest_rule_build_unavailable";
      query->completed = true;
      return true;
    }
    Context context{query, base, stamp.thread_id};
    bridge::ActivityPlannerDiagEnvironmentV1 diagnostic{
        true, bridge::kActivityPlannerDiagExeSha256V1, base, &context,
        &ReadMemory, &ReadFrame, &CastIdler, &InvokeVisibility};
    bridge::ActivityFeastGuestRuleEnvironmentV1 environment{};
    environment.enabled = true;
    environment.diagnostic = diagnostic;
    environment.passive_cost = query->passive_cost;
    environment.context = &context;
    environment.hash_key = &Hash;
    environment.lookup_rule = &Lookup;
    environment.read_active = &Active;
    environment.toggle = &Toggle;
    const bridge::ActivityPlannerDiagFrameV1 expected{
        query->expected_revision, current.date_raw,
        current.played_character_id, true, true, true, true};
    query->rule = query->activate
                      ? bridge::ActivateActivityFeastGuestRuleV1(
                            environment, expected, query->authored_rule_key,
                            query->policy_approved)
                      : bridge::ReadActivityFeastGuestRuleV1(
                            environment, expected, query->authored_rule_key);
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1)
    if (query->query_provenance && query->provenance_observer != nullptr &&
        (query->rule.status ==
             bridge::ActivityFeastGuestRuleStatusV1::observed_active ||
         query->rule.status ==
             bridge::ActivityFeastGuestRuleStatusV1::observed_inactive)) {
      bridge::ActivityCostSlot12CaptureV1 cost{};
      const bridge::ActivityCostSlot12FrameV1 frame{
          static_cast<std::int32_t>(current.date_raw),
          current.played_character_id, stamp.thread_id, true};
      const auto cost_status = bridge::ReadActivityCostSlot12PassiveV1(
          *query->passive_cost, frame, cost);
      if (cost_status == bridge::ActivityCostSlot12ReadStatusV1::observed) {
        query->provenance = bridge::ReadActivityGuestRuleProvenanceV1(
            *query->provenance_observer, frame, cost.planner,
            query->rule.native_key_hash, query->candidate_character_id);
        if (query->provenance.status ==
            bridge::ActivityGuestRuleProvenanceStatusV1::no_normal_refresh)
          query->failure = "activity feast guest provenance: " +
              bridge::DescribeActivityGuestRuleRefreshDiagnosticsV1(
                  *query->provenance_observer);
      } else {
        query->provenance.status =
            bridge::ActivityGuestRuleProvenanceStatusV1::no_normal_refresh;
        query->failure = "activity feast guest provenance passive slot12: " +
            std::string(PassiveCostStatusKey(cost_status));
      }
    }
#endif
    query->completed = true;
    return true;
  } catch (...) {
    query->failure = "native_activity_feast_guest_rule_exception";
    query->completed = true;
    return true;
  }
}

std::string SerializeActivityFeastGuestRulePrivateV1(
    const ActivityFeastGuestRulePrivateQueryV1 &query) {
  if (!query.completed || !query.failure.empty() || query.frame_changed)
    return {};
  const auto &rule = query.rule;
  const bool observed =
      rule.status == bridge::ActivityFeastGuestRuleStatusV1::observed_inactive ||
      rule.status == bridge::ActivityFeastGuestRuleStatusV1::observed_active ||
      rule.status == bridge::ActivityFeastGuestRuleStatusV1::activated;
  std::string payload =
      "{\"schema\":\"activity-feast-guest-rule-private-v1\",";
  payload += "\"snapshot_revision\":" +
             std::to_string(query.expected_revision) +
             ",\"date_raw\":" +
             std::to_string(query.expected_snapshot.date_raw) +
             ",\"actor_character_id\":" +
             std::to_string(query.expected_snapshot.played_character_id) +
             ",\"activity_key\":\"activity_feast\",\"planning_stage\":5,";
  payload += "\"status\":\"" +
             std::string(bridge::ActivityFeastGuestRuleStatusKeyV1(rule.status)) +
             "\",\"invoked\":" + (rule.invoked ? "true" : "false") +
             ",\"active\":" +
             (observed ? (rule.active ? "true" : "false") : "null") +
             ",\"native_key_hash\":" +
             (observed ? std::to_string(rule.native_key_hash) : "null") +
             ",\"ordered_rule_count\":" +
             (observed ? std::to_string(rule.ordered_rule_count) : "null") +
             ",\"active_rule_count\":" +
             (observed ? std::to_string(rule.active_rule_count) : "null") +
             ",\"filtered_group_count\":" +
             (observed ? std::to_string(rule.filtered_group_count) : "null") +
             ",\"filtered_character_count\":" +
             (observed ? std::to_string(rule.filtered_character_count) : "null") +
             "}";
  return payload;
}

#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1)
std::string SerializeActivityFeastGuestRuleProvenancePrivateV1(
    const ActivityFeastGuestRulePrivateQueryV1 &query) {
  if (!query.completed || !query.failure.empty() || query.frame_changed ||
      !query.query_provenance || query.candidate_character_id == 0)
    return {};
  const auto &capture = query.provenance;
  const bool observed =
      capture.status == bridge::ActivityGuestRuleProvenanceStatusV1::observed;
  std::string payload =
      "{\"schema\":\"activity-feast-guest-rule-provenance-private-v1\","
      "\"snapshot_revision\":" + std::to_string(query.expected_revision) +
      ",\"date_raw\":" +
      std::to_string(query.expected_snapshot.date_raw) +
      ",\"actor_character_id\":" +
      std::to_string(query.expected_snapshot.played_character_id) +
      ",\"activity_key\":\"activity_feast\",\"planning_stage\":5,"
      "\"authored_rule_key\":\"" + query.authored_rule_key + "\","
      "\"rule_status\":\"" +
      std::string(bridge::ActivityFeastGuestRuleStatusKeyV1(
          query.rule.status)) + "\","
      "\"status\":\"" +
      std::string(bridge::ActivityGuestRuleProvenanceStatusKeyV1(
          capture.status)) +
      "\",\"candidate_character_id\":" +
      std::to_string(query.candidate_character_id) +
      ",\"rule_active\":";
  if (query.rule.status ==
          bridge::ActivityFeastGuestRuleStatusV1::observed_active)
    payload += "true";
  else if (query.rule.status ==
               bridge::ActivityFeastGuestRuleStatusV1::observed_inactive)
    payload += "false";
  else
    payload += "null";
  payload += ",\"native_key_hash\":" +
             (observed ? std::to_string(capture.native_key_hash) : "null") +
             ",\"normal_refresh_sequence\":" +
             (observed ? std::to_string(capture.normal_refresh_sequence)
                       : "null") +
             ",\"raw_rule_character_count\":" +
             (observed ? std::to_string(capture.raw_rule_character_count)
                       : "null") +
             ",\"filtered_rule_character_count\":" +
             (observed ? std::to_string(capture.filtered_rule_character_count)
                       : "null") +
             ",\"candidate_membership\":" +
             (observed ? (capture.candidate_membership ? "true" : "false")
                       : "null") +
             ",\"filtered_rule_character_ids\":";
  if (!observed) {
    payload += "null";
  } else {
    payload += "[";
    for (std::uint32_t i = 0;
         i < capture.filtered_rule_character_count; ++i) {
      if (i != 0) payload += ",";
      payload += std::to_string(capture.filtered_ids[i]);
    }
    payload += "]";
  }
  payload += "}";
  return payload;
}
#endif

} // namespace xar::ck3_11906
