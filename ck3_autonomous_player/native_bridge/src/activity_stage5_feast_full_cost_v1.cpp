#include "xar_bridge/activity_stage5_feast_full_cost_v1.hpp"
#include "xar_bridge/ck3_12002_activity_feast_costs.hpp"

#include <array>
#include <cstring>

namespace xar::bridge {
namespace {

struct NativeShortString {
  char inline_bytes[16]{};
  std::uint64_t length = 0;
  std::uint64_t capacity = 15;
};
static_assert(sizeof(NativeShortString) == 0x20);

struct Invocation {
  const ActivityStage5FeastFullCostEnvironmentV1 *environment = nullptr;
  std::array<std::uint32_t, 4> indices{};
  std::array<std::int64_t, 4> values{};
  ActivityStage5FeastFullCostStatusV1 failure =
      ActivityStage5FeastFullCostStatusV1::named_query_failed;
  bool complete = false;
};

bool ForwardReadMemory(void *opaque, std::uintptr_t address, void *output,
                       std::size_t size) noexcept {
  const auto &source = static_cast<Invocation *>(opaque)->environment->gold
                           .diagnostic;
  return source.read_memory != nullptr &&
         source.read_memory(source.context, address, output, size);
}

bool ForwardReadFrame(void *opaque,
                      ActivityPlannerDiagFrameV1 &output) noexcept {
  const auto &source = static_cast<Invocation *>(opaque)->environment->gold
                           .diagnostic;
  return source.read_frame != nullptr &&
         source.read_frame(source.context, output);
}

std::uintptr_t ForwardCast(void *opaque, std::uintptr_t source_pointer,
                           std::uintptr_t source_type,
                           std::uintptr_t target_type) noexcept {
  const auto &source = static_cast<Invocation *>(opaque)->environment->gold
                           .diagnostic;
  return source.rtti_cast != nullptr
             ? source.rtti_cast(source.context, source_pointer, source_type,
                                target_type)
             : 0;
}

bool ForwardVisibility(void *opaque, std::uintptr_t planner,
                       std::uintptr_t entry, bool &visible) noexcept {
  const auto &source = static_cast<Invocation *>(opaque)->environment->gold
                           .diagnostic;
  return source.invoke_visibility != nullptr &&
         source.invoke_visibility(source.context, planner, entry, visible);
}

bool InvokeFourNames(void *opaque, std::uintptr_t module_base,
                     std::uintptr_t breakdown,
                     std::int64_t &gold_raw) noexcept {
  auto &invocation = *static_cast<Invocation *>(opaque);
  const auto &environment = *invocation.environment;
  const auto invoke = environment.invoke_named_cost != nullptr
                          ? environment.invoke_named_cost
                          : IsActivityFeastCostsModernBuildV1(
                                    environment.gold.diagnostic.admitted_executable_sha256)
                              ? &InvokeActivityStage5NativeNamedFeastCost12002V1
                              : &InvokeActivityStage5NativeNamedFeastCostV1;
  for (std::size_t index = 0; index < kActivityFeastCostKeysV1.size(); ++index) {
    std::uint32_t resource_index = 10;
    std::int64_t value = 0;
    if (!invoke(environment.invoke_named_cost != nullptr ? environment.named_context
        : const_cast<std::string_view *>(&environment.gold.diagnostic.admitted_executable_sha256), module_base, breakdown,
                kActivityFeastCostKeysV1[index], resource_index, value)) {
      invocation.failure = ActivityStage5FeastFullCostStatusV1::named_query_failed;
      return false;
    }
    if (resource_index >= 10) {
      invocation.failure = ActivityStage5FeastFullCostStatusV1::resource_unmapped;
      return false;
    }
    invocation.indices[index] = resource_index;
    invocation.values[index] = value;
  }
  invocation.complete = true;
  gold_raw = invocation.values[0];
  return true;
}

} // namespace

static bool InvokeNativeNamedFeastCost(
    std::uintptr_t getter_rva, std::uintptr_t module_base, std::uintptr_t cost_breakdown,
    std::string_view resource_key, std::uint32_t &resource_index,
    std::int64_t &cost_raw) noexcept {
  if (module_base == 0 || cost_breakdown == 0 || resource_key.empty() ||
      resource_key.size() >= 16)
    return false;
  NativeShortString key{};
  std::memcpy(key.inline_bytes, resource_key.data(), resource_key.size());
  key.length = resource_key.size();
  using GetCost = std::int64_t *(__fastcall *)(
      std::int64_t *, const void *, const NativeShortString *);
  const auto getter = reinterpret_cast<GetCost>(
      module_base + getter_rva);
  constexpr std::int64_t kMarkerBase = 0x4C41524300000000LL;
  std::array<std::int64_t, 11> markers{};
  for (std::size_t index = 0; index < markers.size(); ++index)
    markers[index] = kMarkerBase + static_cast<std::int64_t>(index);
  std::int64_t marker = 0;
  if (getter(&marker, markers.data(), &key) != &marker ||
      marker < kMarkerBase || marker >= kMarkerBase + 11)
    return false;
  resource_index = static_cast<std::uint32_t>(marker - kMarkerBase);
  if (resource_index >= 10) return true;
  std::int64_t value = 0;
  if (getter(&value, reinterpret_cast<const void *>(cost_breakdown), &key) !=
      &value)
    return false;
  cost_raw = value;
  return true;
}

bool InvokeActivityStage5NativeNamedFeastCostV1(
    void *, std::uintptr_t module_base, std::uintptr_t cost_breakdown,
    std::string_view resource_key, std::uint32_t &resource_index,
    std::int64_t &cost_raw) noexcept {
  return InvokeNativeNamedFeastCost(kActivityGetCostByNameRvaV1, module_base,
      cost_breakdown, resource_key, resource_index, cost_raw);
}

bool InvokeActivityStage5NativeNamedFeastCost12002V1(
    void *opaque, std::uintptr_t module_base, std::uintptr_t cost_breakdown,
    std::string_view resource_key, std::uint32_t &resource_index,
    std::int64_t &cost_raw) noexcept {
  return InvokeNativeNamedFeastCost(Activity12004RvaV1(
      ActivityFeastCostNativeCallbackShaV1(opaque), kActivityGetCostByName12002RvaV1), module_base,
      cost_breakdown, resource_key, resource_index, cost_raw);
}

ActivityStage5FeastFullCostResultV1 ReadActivityStage5FeastFullCostV1(
    const ActivityStage5FeastFullCostEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept {
  ActivityStage5FeastFullCostResultV1 result{};
  result.frame = expected;
  if (!environment.enabled) return result;

  Invocation invocation{&environment};
  auto gold = environment.gold;
  gold.diagnostic.context = &invocation;
  gold.diagnostic.read_memory = &ForwardReadMemory;
  gold.diagnostic.read_frame = &ForwardReadFrame;
  gold.diagnostic.rtti_cast = &ForwardCast;
  gold.diagnostic.invoke_visibility = &ForwardVisibility;
  gold.invoke_gold_cost = &InvokeFourNames;
  const auto gold_result = ReadActivityStage5GoldCostV1(gold, expected);
  result.gold_gate_status = gold_result.status;
  if (gold_result.status != ActivityStage5GoldCostStatusV1::observed) {
    if (gold_result.status == ActivityStage5GoldCostStatusV1::native_query_failed)
      result.status = invocation.failure;
    return result;
  }
  if (!invocation.complete ||
      gold_result.gold_cost_raw != invocation.values[0]) {
    result.status = ActivityStage5FeastFullCostStatusV1::named_query_failed;
    return result;
  }
  result.normal_refresh_sequence = gold_result.normal_refresh_sequence;
  result.resource_indices = invocation.indices;
  result.configured_cost_raw = invocation.values;
  result.actor_gold_raw = gold_result.actor_gold_raw;
  result.status = ActivityStage5FeastFullCostStatusV1::observed;
  return result;
}

std::string_view ActivityStage5FeastFullCostStatusKeyV1(
    ActivityStage5FeastFullCostStatusV1 status) noexcept {
  switch (status) {
  case ActivityStage5FeastFullCostStatusV1::observed:
    return "observed";
  case ActivityStage5FeastFullCostStatusV1::gold_gate_red:
    return "gold_gate_red";
  case ActivityStage5FeastFullCostStatusV1::named_query_failed:
    return "named_query_failed";
  case ActivityStage5FeastFullCostStatusV1::resource_unmapped:
    return "resource_unmapped";
  }
  return "unknown";
}

} // namespace xar::bridge
