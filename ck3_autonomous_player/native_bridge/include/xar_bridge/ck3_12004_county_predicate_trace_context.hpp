#pragma once
#include "xar_bridge/army_county_predicate_trace_v1.hpp"
#include <cstddef>
#include <cstdint>
#include <optional>

namespace xar::ck3_12004 {
#if defined(_MSC_VER)
using CountyPredicateOriginal12004 = bool(__fastcall *)(void *, void *, std::uintptr_t, std::uintptr_t);
#else
using CountyPredicateOriginal12004 = bool (*)(void *, void *, std::uintptr_t, std::uintptr_t);
#endif
inline constexpr std::array<std::uint64_t, 3> kCountyPredicateReturns12004{
    0x24E22B3, 0x24E22F1, 0x24E2348};

struct CountyPredicateTraceFrame12004 {
  CountyPredicateTraceFrame12004 *previous = nullptr;
  const void *actor = nullptr, *source_county = nullptr, *target_county = nullptr;
  std::uint32_t thread_id = 0, callback_depth = 0;
  std::size_t next_stage = 0;
  std::optional<std::size_t> active_relation_stage;
  std::uint32_t relation_callback_depth = 0;
  bool stopped = false;
  game::ArmyCountyPredicateTraceV1 trace{};
};
inline thread_local CountyPredicateTraceFrame12004 *g_county_predicate_trace12004 = nullptr;

class CountyPredicateTraceScope12004 {
  CountyPredicateTraceFrame12004 frame_{};
 public:
  CountyPredicateTraceScope12004(bool installed, std::int32_t mode,
      std::uint32_t thread, const void *actor, const void *source_county,
      const void *target_county) noexcept {
    frame_.trace.hook_installed = installed;
    frame_.trace.unavailable_reason = !installed ? "county_P_hook_not_installed"
                                              : "county_P_trace_requires_mode1";
    frame_.previous = g_county_predicate_trace12004;
    frame_.thread_id = thread;
    frame_.actor = actor;
    frame_.source_county = source_county;
    frame_.target_county = target_county;
    frame_.trace.scope_entered = installed && mode == 1;
    // Even a disabled nested scope masks an older preview frame.
    g_county_predicate_trace12004 = &frame_;
  }
  ~CountyPredicateTraceScope12004() { g_county_predicate_trace12004 = frame_.previous; }
  CountyPredicateTraceScope12004(const CountyPredicateTraceScope12004 &) = delete;
  CountyPredicateTraceScope12004 &operator=(const CountyPredicateTraceScope12004 &) = delete;

  game::ArmyCountyPredicateTraceV1 Finish(bool returned, bool passes,
      bool outer_identity_stable, std::uint32_t thread,
      bool source_P_expected, bool target_present, bool target_magic_CoDa) const {
    auto out = frame_.trace;
    out.same_thread = thread == frame_.thread_id;
    out.native_predicate_returned = returned;
    // Preserve the independently valid parent bool only when its outer sample
    // is stable. A failed trace never changes the parent's available result.
    if (returned && outer_identity_stable) out.final_condition_passes = passes;
    if (!out.scope_entered) return out;
    if (!returned || !outer_identity_stable || !out.same_thread ||
        !out.order_valid || frame_.callback_depth != 0) {
      out.unavailable_reason = "county_P_trace_incomplete_or_identity_changed";
      return out;
    }
    for (const auto &stage : out.stages) {
      if (stage.call_count > 1 || (stage.call_count == 1 &&
          (!stage.returned.has_value() || stage.argument_identity_matched != true))) {
        out.unavailable_reason = "county_P_trace_incomplete_or_identity_changed";
        return out;
      }
    }
    const bool target_first_expected = out.stages[0].returned == true && target_present;
    const bool target_second_expected = out.stages[1].returned == true && target_magic_CoDa;
    if ((out.stages[0].call_count == 1) != source_P_expected ||
        (out.stages[1].call_count == 1) != target_first_expected ||
        (out.stages[2].call_count == 1) != target_second_expected ||
        (passes && !(out.stages[0].returned == true &&
                     out.stages[1].returned == true && out.stages[2].returned == true))) {
      out.unavailable_reason = "county_P_trace_does_not_cover_source_CFG";
      return out;
    }
    out.available = true;
    out.unavailable_reason.clear();
    return out;
  }
};

inline bool InvokeCountyPredicateTrace12004(CountyPredicateOriginal12004 original,
    void *actor, void *county, std::optional<std::uint64_t> caller,
    std::uint32_t thread, std::uintptr_t opaque_r8 = 0,
    std::uintptr_t opaque_r9 = 0) {
  // Installation requires nonnull original before the patch becomes reachable.
  if (!original) return false;
  auto *const frame = g_county_predicate_trace12004;
  if (!frame || !frame->trace.scope_entered)
    return original(actor, county, opaque_r8, opaque_r9);
  const bool nested = frame->callback_depth != 0;
  ++frame->callback_depth;
  struct DepthExit {
    CountyPredicateTraceFrame12004 *frame;
    ~DepthExit() { --frame->callback_depth; }
  } depth_exit{frame};
  if (nested) {
    ++frame->trace.ignored_nested_calls;
    return original(actor, county, opaque_r8, opaque_r9);
  }
  std::size_t stage_index = 3;
  for (std::size_t i = 0; i != 3; ++i)
    if (caller == kCountyPredicateReturns12004[i]) stage_index = i;
  if (stage_index == 3) {
    ++frame->trace.ignored_foreign_calls;
    return original(actor, county, opaque_r8, opaque_r9);
  }
  auto &stage = frame->trace.stages[stage_index];
  ++stage.call_count;
  stage.actual_caller_return_rva = caller;
  const void *const expected_county = stage_index == 0
      ? frame->source_county : frame->target_county;
  stage.argument_identity_matched = thread == frame->thread_id &&
      actor == frame->actor && county == expected_county;
  if (stage_index != frame->next_stage || frame->stopped ||
      stage.argument_identity_matched != true || stage.call_count != 1)
    frame->trace.order_valid = false;
  // P tail-jumps to 2C09620. Its actual return is this bridge call site,
  // not the original 24E22xx caller. Carry the known P stage through it.
  const auto previous_relation_stage = frame->active_relation_stage;
  frame->active_relation_stage = stage_index;
  struct StageExit {
    CountyPredicateTraceFrame12004 *frame;
    std::optional<std::size_t> previous;
    ~StageExit() { frame->active_relation_stage = previous; }
  } stage_exit{frame, previous_relation_stage};
  const bool result = original(actor, county, opaque_r8, opaque_r9); // exactly one native call
  stage.returned = result;
  frame->next_stage = stage_index + 1;
  frame->stopped = !result;
  return result;
}
}
