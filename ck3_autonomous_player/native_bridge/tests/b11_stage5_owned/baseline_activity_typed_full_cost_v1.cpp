#include "xar_bridge/activity_typed_full_cost_v1.hpp"
#include "xar_bridge/ck3_12002_activity_feast_costs.hpp"
#include "xar_bridge/ck3_12002_activity_feast_start.hpp"
#include "xar_bridge/ck3_12002_feast_planner.hpp"

#include <windows.h>

#include <array>
#include <cstring>
#include <limits>

namespace xar::bridge {
namespace {

template <class T>
bool ReadAt(const ActivityPlannerDiagEnvironmentV1 &environment,
            std::uintptr_t base, std::size_t offset, T &value) noexcept {
  return activity_typed_planner_detail_v1::ReadAt(
      environment, base, offset, value);
}

template <std::size_t N>
bool Match(const ActivityPlannerDiagEnvironmentV1 &environment,
           std::uintptr_t old_rva,
           const std::array<std::uint8_t, N> &bytes) noexcept {
  const auto rva = Activity12004RvaV1(
      environment.admitted_executable_sha256, old_rva);
  std::array<std::uint8_t, N> actual{};
  return rva != 0 && ReadAt(environment, environment.module_base, rva, actual) &&
         actual == bytes;
}

bool VerifyExistingAbi(const ActivityPlannerDiagEnvironmentV1 &d) noexcept {
  constexpr std::array<std::uint8_t, 13> named{
      0x48, 0x89, 0x5C, 0x24, 0x18, 0x56, 0x57,
      0x41, 0x56, 0x48, 0x83, 0xEC, 0x30};
  constexpr std::array<std::uint8_t, 4> indexed{0x49, 0x8B, 0x0C, 0xC6};
  return d.enabled && IsActivity12004BuildV1(d.admitted_executable_sha256) &&
         d.module_base != 0 && d.read_frame != nullptr &&
         d.read_memory != nullptr && d.rtti_cast != nullptr &&
         d.invoke_visibility != nullptr &&
         Match(d, kActivityGetCostByName12002RvaV1, named) &&
         Match(d, kActivityGetCostIndexed12002RvaV1, indexed) &&
         Match(d, ck3_12002::kFeastFinalCanStartRva,
               ck3_12002::kFeastFinalCanStartPrefix) &&
         Match(d, ck3_12002::kFeastFinalStage5BranchRva,
               ck3_12002::kFeastFinalStage5Prefix);
}

bool NativeNamed(void *opaque, std::uintptr_t base, std::uintptr_t breakdown,
                 std::string_view key, std::uint32_t &index,
                 std::int64_t &value) noexcept {
  if (opaque == nullptr || base == 0 || breakdown == 0 || key.empty() ||
      key.size() >= 16) return false;
  const auto sha = *static_cast<const std::string_view *>(opaque);
  if (!IsActivity12004BuildV1(sha)) return false;
  const auto getter_rva = Activity12004RvaV1(
      sha, kActivityGetCostByName12002RvaV1);
  if (getter_rva == 0 || getter_rva >
      (std::numeric_limits<std::uintptr_t>::max)() - base) return false;
  // Source-bound extraction of the existing 32-byte short string and
  // eleven-unique-sentinel native name/index chain. No old Feast TU is called.
  struct NativeShortString {
    char inline_bytes[16]{};
    std::uint64_t length = 0;
    std::uint64_t capacity = 15;
  } native_key{};
  static_assert(sizeof(NativeShortString) == 0x20);
  std::memcpy(native_key.inline_bytes, key.data(), key.size());
  native_key.length = key.size();
  using GetCost = std::int64_t *(__fastcall *)(
      std::int64_t *, const void *, const NativeShortString *);
  const auto getter = reinterpret_cast<GetCost>(base + getter_rva);
  constexpr std::int64_t marker_base = 0x4C41524300000000LL;
  std::array<std::int64_t, 11> markers{};
  for (std::size_t slot = 0; slot < markers.size(); ++slot)
    markers[slot] = marker_base + static_cast<std::int64_t>(slot);
  std::int64_t marker = 0, configured = 0;
  index = 10;
  __try {
    if (getter(&marker, markers.data(), &native_key) != &marker ||
        marker < marker_base || marker >= marker_base + 10)
      return false; // Native index10 means unknown name, never a valid value.
    index = static_cast<std::uint32_t>(marker - marker_base);
    if (getter(&configured, reinterpret_cast<const void *>(breakdown),
               &native_key) != &configured) return false;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
  value = configured;
  return true;
}

struct NativeCanStartContext {
  std::uintptr_t base = 0;
  std::string_view sha{};
};

bool NativeCanStart(void *opaque, std::uintptr_t planner,
                    bool &allowed) noexcept {
  if (opaque == nullptr || planner == 0) return false;
  const auto &context = *static_cast<const NativeCanStartContext *>(opaque);
  if (!IsActivity12004BuildV1(context.sha) || context.base == 0) return false;
  const auto evaluator_rva = Activity12004RvaV1(
      context.sha, ck3_12002::kFeastFinalCanStartRva);
  const auto destroy_rva = Activity12004RvaV1(
      context.sha, ck3_12002::kFeastNativeStringDestroyRva);
  if (evaluator_rva == 0 || destroy_rva == 0) return false;
  const auto evaluator =
      reinterpret_cast<ActivityTypedCanStartNativePredicateV1>(
          context.base + evaluator_rva);
  const auto destroy =
      reinterpret_cast<ActivityTypedCanStartNativeDestroyV1>(
          context.base + destroy_rva);
  return InvokeActivityTypedPlannerCanStartBoolOwnedV1(
      reinterpret_cast<void *>(planner), evaluator, destroy, allowed);
}

bool SameIdentity(const ActivityPlannerIdentityV1 &left,
                  const ActivityPlannerIdentityV1 &right) noexcept {
  return left.actor == right.actor && left.handler == right.handler &&
         left.planner == right.planner &&
         left.activity_type == right.activity_type && left.stage == right.stage;
}

bool ReadIdentity(const ActivityPlannerDiagEnvironmentV1 &d,
                  const ActivityPlannerDiagFrameV1 &expected,
                  const ActivityTypedPlannerContractV1 &contract,
                  ActivityPlannerDiagResultV1 &diagnostic,
                  ActivityPlannerIdentityV1 &identity) noexcept {
  diagnostic = ReadActivityPlannerDiagV1(d, expected);
  const auto *layout = ActivityFeastCostLayoutForBuildV1(
      d.admitted_executable_sha256);
  return layout != nullptr &&
         diagnostic.status == ActivityPlannerDiagStatusV1::observed &&
         diagnostic.frame == expected && diagnostic.value.planner_present &&
         diagnostic.value.widget_attached && diagnostic.value.widget_visible &&
         diagnostic.value.stage == 5 &&
         MatchesActivityTypedPlannerHostKeyV1(diagnostic.value, contract) &&
         ResolveActivityPlannerIdentityV1(d, expected, identity) &&
         identity.stage == 5 &&
         MatchesActivityTypedPlannerTypeV1(d, identity.activity_type,
             layout->type_vtable_rva, contract);
}

bool ReadTotals(const ActivityPlannerDiagEnvironmentV1 &d,
                std::uintptr_t breakdown,
                std::array<std::int64_t, 10> &totals) noexcept {
  // Existing GetCost(name) indexed instruction is [breakdown +index*8].
  // This is intentionally not the observer's diagnostic aggregate rows.
  for (std::size_t index = 0; index < totals.size(); ++index)
    if (!ReadAt(d, breakdown, index * sizeof(std::int64_t), totals[index]))
      return false;
  return true;
}

} // namespace

bool InvokeActivityTypedPlannerCanStartBoolOwnedV1(
    void *planner, ActivityTypedCanStartNativePredicateV1 predicate,
    ActivityTypedCanStartNativeDestroyV1 destroy, bool &allowed) noexcept {
  if (planner == nullptr || predicate == nullptr || destroy == nullptr)
    return false;
  // Same 32-byte owned string layout as the existing source-bound evaluator
  // helper, but no display pointer is read and no text is copied or published.
  struct OwnedNativeString {
    std::array<char, 16> storage{};
    std::uint64_t size = 0;
    std::uint64_t capacity = 15;
  } native{};
  static_assert(sizeof(OwnedNativeString) == 0x20);
  bool value = false;
  __try {
    value = predicate(planner, &native);
    destroy(&native);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
  allowed = value;
  return true;
}

ActivityTypedFullCostResultV1 ReadActivityTypedPlannerFullCostV1(
    const ActivityTypedFullCostEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected,
    const ActivityTypedPlannerContractV1 &contract) noexcept {
  ActivityTypedFullCostResultV1 result{};
  const auto &d = environment.diagnostic;
  if (!environment.enabled || !IsPilgrimageContractV1(contract) ||
      !VerifyExistingAbi(d)) return result;
  if (expected.revision == 0 || !expected.application_main_thread ||
      !expected.paused || !expected.map_ready || !expected.actor_alive ||
      expected.actor_character_id <= 0 ||
      expected.date_raw < (std::numeric_limits<std::int32_t>::min)() ||
      expected.date_raw > (std::numeric_limits<std::int32_t>::max)()) {
    result.status = ActivityTypedFullCostStatusV1::frame_unavailable;
    return result;
  }
  auto *observer = environment.passive_cost;
  if (observer == nullptr || !observer->installed ||
      !observer->environment.enabled ||
      observer->environment.module_base != d.module_base ||
      observer->environment.executable_sha256 != d.admitted_executable_sha256 ||
      observer->environment.typed_contract == nullptr ||
      !IsPilgrimageContractV1(
          *observer->environment.typed_contract)) {
    result.status = ActivityTypedFullCostStatusV1::passive_observer_contract_mismatch;
    return result;
  }
  ActivityPlannerDiagResultV1 diagnostic_before{};
  ActivityPlannerIdentityV1 identity_before{};
  if (!ReadIdentity(d, expected, contract, diagnostic_before, identity_before)) {
    result.status = ActivityTypedFullCostStatusV1::planner_or_type_mismatch;
    return result;
  }
  ActivityTypedPlannerSelectionV1 selection_before{};
  if (environment.read_selection == nullptr ||
      !environment.read_selection(environment.selection_context, expected, 5,
                                  selection_before) ||
      !MatchesActivityTypedPlannerSelectionV1(selection_before, expected,
          identity_before.planner, identity_before.activity_type, 5, contract)) {
    result.status = ActivityTypedFullCostStatusV1::selection_unavailable;
    return result;
  }
  const ActivityCostSlot12FrameV1 cost_frame{
      static_cast<std::int32_t>(expected.date_raw),
      expected.actor_character_id, GetCurrentThreadId(), true};
  ActivityCostSlot12CaptureV1 before{};
  const auto capture_status = ReadActivityCostSlot12PassiveV1(
      *observer, cost_frame, before);
  if (capture_status == ActivityCostSlot12ReadStatusV1::no_normal_refresh) {
    result.status = ActivityTypedFullCostStatusV1::no_normal_refresh;
    return result;
  }
  if (capture_status != ActivityCostSlot12ReadStatusV1::observed ||
      !before.typed_contract_bound || before.typed_kind != contract.kind ||
      before.planning_stage != 5 || before.planner != identity_before.planner ||
      before.owner != identity_before.handler ||
      before.activity_type != identity_before.activity_type) {
    result.status = ActivityTypedFullCostStatusV1::configuration_changed;
    return result;
  }
  const auto *layout = ActivityFeastCostLayoutForBuildV1(
      d.admitted_executable_sha256);
  std::uintptr_t breakdown = 0;
  if (layout == nullptr || layout->breakdown_offset >
          (std::numeric_limits<std::uintptr_t>::max)() - before.planner) {
    result.status = ActivityTypedFullCostStatusV1::configured_cost_unreadable;
    return result;
  }
  breakdown = before.planner + layout->breakdown_offset;
  auto &quote = result.quote;
  if (!ReadTotals(d, breakdown, quote.configured_cost_raw)) {
    result.status = ActivityTypedFullCostStatusV1::configured_cost_unreadable;
    return result;
  }
  const auto named = environment.invoke_named_cost != nullptr
                         ? environment.invoke_named_cost : &NativeNamed;
  auto sha = d.admitted_executable_sha256;
  void *named_context = environment.invoke_named_cost != nullptr
                            ? environment.named_context : &sha;
  for (std::size_t name = 0; name < kActivityTypedPlannerKnownCostNamesV1.size();
       ++name) {
    std::uint32_t index = 10;
    std::int64_t value = 0;
    if (!named(named_context, d.module_base, breakdown,
               kActivityTypedPlannerKnownCostNamesV1[name], index, value)) {
      result.status = ActivityTypedFullCostStatusV1::named_cost_failed;
      return result;
    }
    if (index >= quote.configured_cost_raw.size()) {
      result.status = ActivityTypedFullCostStatusV1::named_cost_unmapped;
      return result;
    }
    if (quote.named_cost_verified[index]) {
      result.status = ActivityTypedFullCostStatusV1::named_cost_duplicate_index;
      return result;
    }
    if (value != quote.configured_cost_raw[index]) {
      result.status = ActivityTypedFullCostStatusV1::named_cost_indexed_disagreement;
      return result;
    }
    quote.named_cost_verified[index] = true;
    quote.known_name_resource_indices[name] = index;
  }
  NativeCanStartContext native_context{d.module_base,
                                       d.admitted_executable_sha256};
  const auto evaluate = environment.evaluate_final_can_start != nullptr
                            ? environment.evaluate_final_can_start
                            : &NativeCanStart;
  void *can_start_context = environment.evaluate_final_can_start != nullptr
                               ? environment.can_start_context : &native_context;
  bool final_can_start = false;
  if (!evaluate(can_start_context, before.planner, final_can_start)) {
    result.status = ActivityTypedFullCostStatusV1::final_can_start_failed;
    return result;
  }
  ActivityPlannerDiagResultV1 diagnostic_after{};
  ActivityPlannerIdentityV1 identity_after{};
  ActivityTypedPlannerSelectionV1 selection_after{};
  ActivityCostSlot12CaptureV1 after{};
  std::array<std::int64_t, 10> totals_after{};
  if (!ReadIdentity(d, expected, contract, diagnostic_after, identity_after) ||
      !SameIdentity(identity_after, identity_before) ||
      diagnostic_after.value != diagnostic_before.value ||
      !environment.read_selection(environment.selection_context, expected, 5,
                                  selection_after) ||
      selection_after != selection_before ||
      ReadActivityCostSlot12PassiveV1(*observer, cost_frame, after) !=
          ActivityCostSlot12ReadStatusV1::observed ||
      !after.typed_contract_bound || after.typed_kind != contract.kind ||
      after.sequence != before.sequence || after.planner != before.planner ||
      after.owner != before.owner || after.activity_type != before.activity_type ||
      after.planning_stage != before.planning_stage ||
      after.configuration_fingerprint != before.configuration_fingerprint ||
      after.raw_aggregate != before.raw_aggregate ||
      !ReadTotals(d, breakdown, totals_after) ||
      totals_after != quote.configured_cost_raw) {
    result.status = ActivityTypedFullCostStatusV1::configuration_changed;
    return result;
  }
  quote.observed = true;
  quote.kind = contract.kind;
  quote.frame = expected;
  quote.planner = before.planner;
  quote.owner = before.owner;
  quote.activity_type = before.activity_type;
  quote.planning_stage = 5;
  quote.normal_refresh_sequence = before.sequence;
  quote.configuration_fingerprint = before.configuration_fingerprint;
  quote.selection = selection_before;
  quote.diagnostic_aggregate_raw = before.raw_aggregate;
  quote.final_can_start_observed = true;
  quote.final_can_start = final_can_start;
  quote.failure_display_known = false;
  for (std::size_t index = 0; index < quote.configured_cost_raw.size(); ++index)
    if (quote.configured_cost_raw[index] > 0 && !quote.named_cost_verified[index])
      result.unknown_positive_configured_cost = true;
  result.status = ActivityTypedFullCostStatusV1::observed;
  return result;
}

std::string_view ActivityTypedFullCostStatusKeyV1(
    ActivityTypedFullCostStatusV1 status) noexcept {
  switch (status) {
  case ActivityTypedFullCostStatusV1::observed: return "observed";
  case ActivityTypedFullCostStatusV1::disabled_or_exact_build_rejected:
    return "disabled_or_exact_build_rejected";
  case ActivityTypedFullCostStatusV1::frame_unavailable: return "frame_unavailable";
  case ActivityTypedFullCostStatusV1::planner_or_type_mismatch:
    return "planner_or_type_mismatch";
  case ActivityTypedFullCostStatusV1::selection_unavailable: return "selection_unavailable";
  case ActivityTypedFullCostStatusV1::passive_observer_contract_mismatch:
    return "passive_observer_contract_mismatch";
  case ActivityTypedFullCostStatusV1::no_normal_refresh: return "no_normal_refresh";
  case ActivityTypedFullCostStatusV1::configuration_changed: return "configuration_changed";
  case ActivityTypedFullCostStatusV1::configured_cost_unreadable:
    return "configured_cost_unreadable";
  case ActivityTypedFullCostStatusV1::named_cost_failed: return "named_cost_failed";
  case ActivityTypedFullCostStatusV1::named_cost_unmapped: return "named_cost_unmapped";
  case ActivityTypedFullCostStatusV1::named_cost_duplicate_index:
    return "named_cost_duplicate_index";
  case ActivityTypedFullCostStatusV1::named_cost_indexed_disagreement:
    return "named_cost_indexed_disagreement";
  case ActivityTypedFullCostStatusV1::final_can_start_failed:
    return "final_can_start_failed";
  }
  return "unknown";
}

} // namespace xar::bridge
