#include "xar_bridge/activity_pilgrimage_stage5_start_v1.hpp"
#include "xar_bridge/ck3_12002_activity_feast_start.hpp"

namespace xar::bridge {
namespace {

bool Usable(const ActivityPlannerDiagFrameV1 &f) noexcept {
  return f.revision != 0 && f.actor_character_id > 0 &&
         f.application_main_thread && f.paused && f.map_ready && f.actor_alive;
}

ActivityHostedIdentityFrameV1 HostedFrame(
    const ActivityPlannerDiagFrameV1 &f) noexcept {
  return {f.revision, f.date_raw, f.actor_character_id,
          f.application_main_thread, f.paused, f.map_ready, f.actor_alive};
}

bool IsPilgrimage(const ActivityHostedIdentityV1 &id) noexcept {
  const auto key = kOrdinaryPilgrimagePiousContractV1.activity_key;
  return id.type_key_size < id.type_key.size() &&
         std::string_view(id.type_key.data(), id.type_key_size) == key;
}

bool HostedValid(const ActivityHostedIdentityResultV1 &hosted,
                 const ActivityPlannerDiagFrameV1 &frame) noexcept {
  if (hosted.status != ActivityHostedIdentityStatusV1::observed ||
      hosted.frame != HostedFrame(frame) || hosted.hosted_count > hosted.hosted.size())
    return false;
  for (std::size_t i = 0; i < hosted.hosted_count; ++i) {
    const auto &row = hosted.hosted[i];
    if (row.host_character_id != frame.actor_character_id ||
        row.type_key_size == 0 || row.type_key_size >= row.type_key.size() ||
        !row.terminal_flags_observed)
      return false;
    for (std::size_t j = 0; j < i; ++j)
      if (row.activity_id == hosted.hosted[j].activity_id) return false;
  }
  return true;
}

bool SameIdentity(const ActivityHostedIdentityV1 &a,
                  const ActivityHostedIdentityV1 &b) noexcept {
  return a.activity_id == b.activity_id && a.host_character_id == b.host_character_id &&
         a.type_key == b.type_key && a.type_key_size == b.type_key_size &&
         a.terminal_flags_observed == b.terminal_flags_observed &&
         a.native_completed == b.native_completed &&
         a.native_invalidated == b.native_invalidated &&
         a.native_completion_stamp_observed == b.native_completion_stamp_observed &&
         a.native_completion_stamp_raw == b.native_completion_stamp_raw;
}

bool Same(const ActivityPilgrimageStage5SnapshotV1 &a,
          const ActivityPilgrimageStage5SnapshotV1 &b) noexcept {
  if (a.quote != b.quote || a.destination != b.destination ||
      a.balance_frame != b.balance_frame ||
      a.balance_available != b.balance_available || a.balance_raw != b.balance_raw ||
      a.hosted.frame != b.hosted.frame || a.hosted.status != b.hosted.status ||
      a.hosted.manager_active_count != b.hosted.manager_active_count ||
      a.hosted.hosted_count != b.hosted.hosted_count)
    return false;
  for (std::size_t i = 0; i < a.hosted.hosted_count; ++i)
    if (!SameIdentity(a.hosted.hosted[i], b.hosted.hosted[i])) return false;
  return true;
}

bool Valid(const ActivityPilgrimageStage5SnapshotV1 &s,
           const ActivityPilgrimageStage5StartRequestV1 &request) noexcept {
  const auto &q = s.quote;
  if (q.selection.option_key_size >= q.selection.option_key.size()) return false;
  const auto *contract = PilgrimageContractForKeyV1(std::string_view(
      q.selection.option_key.data(), q.selection.option_key_size));
  if (contract == nullptr) return false;
  const auto &c = *contract;
  if (!q.observed || q.kind != c.kind || q.frame != request.expected ||
      q.planner == 0 || q.owner == 0 || q.activity_type == 0 || q.planning_stage != 5 ||
      q.normal_refresh_sequence == 0 || !q.final_can_start_observed ||
      !q.final_can_start ||
      !MatchesActivityTypedPlannerSelectionV1(q.selection, request.expected,
          q.planner, q.activity_type, 5, c) ||
      !s.destination.observed || s.destination.kind != c.kind ||
      s.destination.frame != request.expected || s.destination.planner != q.planner ||
      s.destination.activity_type != q.activity_type ||
      s.destination.planning_stage != 5 || s.destination.predefined_phase_count != 1 ||
      request.destination_province_id == 0 ||
      s.destination.province_id != request.destination_province_id ||
      s.balance_frame != request.expected || !HostedValid(s.hosted, request.expected))
    return false;
  for (std::size_t i = 0; i < q.known_name_resource_indices.size(); ++i) {
    const auto index = q.known_name_resource_indices[i];
    if (index >= 10 || !q.named_cost_verified[index]) return false;
    for (std::size_t j = 0; j < i; ++j)
      if (index == q.known_name_resource_indices[j]) return false;
  }
  for (std::size_t index = 0; index < 10; ++index) {
    const auto cost = q.configured_cost_raw[index];
    const auto reserve = request.reserve_raw[index];
    if (cost < 0 || reserve < 0) return false;
    if (cost == 0) continue;
    bool admitted_name_index = false;
    for (const auto mapped : q.known_name_resource_indices)
      if (mapped == index) admitted_name_index = true;
    if (!admitted_name_index || !q.named_cost_verified[index] ||
        !s.balance_available[index] ||
        cost > (std::numeric_limits<std::int64_t>::max)() - reserve ||
        s.balance_raw[index] < cost + reserve)
      return false;
  }
  // No new booking while another nonterminal pilgrimage is observed.
  for (std::size_t i = 0; i < s.hosted.hosted_count; ++i) {
    const auto &id = s.hosted.hosted[i];
    if (IsPilgrimage(id) && !id.native_completed && !id.native_invalidated)
      return false;
  }
  return true;
}

template <std::size_t N>
bool Match(const ActivityPilgrimageStage5StartEnvironmentV1 &e,
           std::uintptr_t rva, const std::array<std::uint8_t, N> &prefix) noexcept {
  if (e.read_memory == nullptr || rva >
      (std::numeric_limits<std::uintptr_t>::max)() - e.module_base) return false;
  std::array<std::uint8_t, N> actual{};
  return e.read_memory(e.context, e.module_base + rva, actual.data(), actual.size()) &&
         actual == prefix;
}

bool Abi(const ActivityPilgrimageStage5StartEnvironmentV1 &e) noexcept {
  return e.enabled && IsActivity12004BuildV1(e.admitted_executable_sha256) &&
         e.module_base != 0 && e.capture != nullptr &&
         Match(e, Activity12004RvaV1(e.admitted_executable_sha256,
                  ck3_12002::kFeastCommitRva), ck3_12002::kFeastCommitPrefix) &&
         Match(e, Activity12004RvaV1(e.admitted_executable_sha256,
                  ck3_12002::kFeastFinalCanStartRva), ck3_12002::kFeastFinalCanStartPrefix) &&
         Match(e, Activity12004RvaV1(e.admitted_executable_sha256,
                  ck3_12002::kFeastFinalStage5BranchRva), ck3_12002::kFeastFinalStage5Prefix);
}

} // namespace

ActivityPilgrimageStage5StartResultV1 StartActivityPilgrimageStage5V1(
    const ActivityPilgrimageStage5StartEnvironmentV1 &environment,
    const ActivityPilgrimageStage5StartRequestV1 &request,
    ActivityPilgrimageStartLedgerV1 &ledger) noexcept {
  ActivityPilgrimageStage5StartResultV1 out{};
  out.state = ledger.state;
  if (ledger.state != ActivityPilgrimageStartStateV1::idle ||
      !request.policy_approved || !Usable(request.expected) || !Abi(environment))
    return out;
  ActivityPilgrimageStage5SnapshotV1 first{}, final{};
  if (!environment.capture(environment.context, request.expected, first) ||
      !Valid(first, request) ||
      !environment.capture(environment.context, request.expected, final) ||
      !Valid(final, request) || !Same(first, final)) return out;
  ledger.before = final;
  // Set before invocation: a false/SEH/timeout outcome must never be retried.
  ledger.state = ActivityPilgrimageStartStateV1::submission_outcome_unknown;
  out.accepted = true;
  out.invoked = true;
  const auto invoke = environment.invoke_commit != nullptr
      ? environment.invoke_commit : &InvokeActivityPilgrimageNativeCommit12004V1;
  if (invoke(environment.context, environment.module_base, final.quote.planner))
    ledger.state = ActivityPilgrimageStartStateV1::submitted_pending;
  out.state = ledger.state;
  return out;
}

ActivityPilgrimageReconcileResultV1 ReconcileActivityPilgrimageStartV1(
    ActivityPilgrimageStartLedgerV1 &ledger,
    const ActivityHostedIdentityResultV1 &after) noexcept {
  ActivityPilgrimageReconcileResultV1 out{};
  const auto &before_frame = ledger.before.quote.frame;
  const auto &hf = after.frame;
  const ActivityPlannerDiagFrameV1 frame{hf.revision, hf.date_raw,
      hf.actor_character_id, hf.application_main_thread, hf.paused,
      hf.map_ready, hf.actor_alive};
  if (ledger.state == ActivityPilgrimageStartStateV1::idle ||
      !Usable(frame) || !HostedValid(after, frame) ||
      frame.actor_character_id != before_frame.actor_character_id ||
      frame.revision <= before_frame.revision || frame.date_raw < before_frame.date_raw)
    return out;
  std::uint32_t matches = 0;
  for (std::size_t i = 0; i < after.hosted_count; ++i) {
    const auto &row = after.hosted[i];
    if (!IsPilgrimage(row)) continue;
    bool existed = false;
    for (std::size_t j = 0; j < ledger.before.hosted.hosted_count; ++j)
      if (ledger.before.hosted.hosted[j].activity_id == row.activity_id)
        existed = true; // Full generation bits are preserved and compared.
    if (existed) continue;
    ++matches;
    out.identity = row;
  }
  if (matches == 0) out.status = ActivityPilgrimageReconcileStatusV1::pending;
  else if (matches > 1)
    out.status = ActivityPilgrimageReconcileStatusV1::ambiguous_new_identities;
  else if (ledger.state == ActivityPilgrimageStartStateV1::identity_observed &&
           ledger.observed_activity_id != out.identity.activity_id)
    out.status = ActivityPilgrimageReconcileStatusV1::ambiguous_new_identities;
  else {
    out.status = ActivityPilgrimageReconcileStatusV1::identity_observed;
    ledger.observed_activity_id = out.identity.activity_id;
    ledger.state = ActivityPilgrimageStartStateV1::identity_observed;
  }
  return out;
}

bool InvokeActivityPilgrimageNativeCommit12004V1(
    void *, std::uintptr_t module_base, std::uintptr_t planner) noexcept {
#if defined(_WIN32)
  const auto rva = Activity12004RvaV1(ck3_12004::kExecutableSha256,
                                    ck3_12002::kFeastCommitRva);
  if (module_base == 0 || planner == 0 ||
      rva > (std::numeric_limits<std::uintptr_t>::max)() - module_base) return false;
  using Commit = void(__fastcall *)(void *);
#if defined(_MSC_VER)
  __try {
    reinterpret_cast<Commit>(module_base + rva)(reinterpret_cast<void *>(planner));
  } __except (1) {
    return false; // Ledger was already set to outcome-unknown by the caller.
  }
#else
  reinterpret_cast<Commit>(module_base + rva)(reinterpret_cast<void *>(planner));
#endif
  return true;
#else
  (void)module_base;
  (void)planner;
  return false;
#endif
}

} // namespace xar::bridge
