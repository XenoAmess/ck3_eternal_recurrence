#pragma once

#include "xar_bridge/ck3_12004_sway.hpp"
#include "xar_bridge/ck3_12002_sway_completion_termination.hpp"
#include "xar_bridge/sway_common_termination_observation_12004.hpp"

#include <array>
#include <type_traits>

namespace xar::ck3_12004 {

// Actual .4 typed source: continuation-21/root-source01. Command source is
// the already qualified selected-Stop profile, not a historical address delta.
inline constexpr std::array<std::uintptr_t, 3> kSwayEndInvocationSlotRvas12004{
    0x476EB88, 0x4852280, 0x4852C38};
inline constexpr std::array<std::uintptr_t, 3> kSwayEndInvocationOriginalRvas12004{
    0x299C320, 0x2D11B30, 0x2D11AD0};
inline constexpr std::uintptr_t kSwayEndCommandPrimaryVptr12004 = 0x476ED40;
inline constexpr std::uintptr_t kSwayEndCommandSecondaryVptr12004 = 0x476EB80;
inline constexpr std::array<std::uintptr_t, 2> kSwayEndEffectVptrRvas12004{
    0x48521C0, 0x4852B78};

// Only software DTOs are shared with the old adapter; its native binder,
// capture functions, installer and address constants are never used here.
using SwayEndSourceClass12004 = ck3_12002::SwayTerminationSourceClass12002;
using SwayEndCaptureResult12004 = ck3_12002::SwayTerminationCaptureResult12002;
using SwayEndNativeCommand12004 = void (*)(const void *secondary_this);
using SwayEndNativeEffect12004 = void (*)(const void *effect,
                                        const void *effect_context);

struct SwayEndInvocationBindings12004 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  ck3_12002::SwayStateBindings12002 state{};
};
SwayEndInvocationBindings12004 BindSwayEndInvocationImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// Root obtains _ReturnAddress() in the typed entry itself, before calling a
// helper. A helper's return address identifies the wrapper, not its native
// caller. Root also owns session lifecycle and unique invocation allocation.
// SwayEndInvocationStamp12004 is shared unchanged in the neutral header.

// No receiver, context, root, storage or instance pointer persists here.
// Native state and source invocation are independent of specific end cause.
struct SwayEndInvocation12004 {
  SwayEndInvocationStamp12004 stamp{};
  ck3_12002::SwayTerminationSource12002 source{};
  std::uint32_t scheme_instance_generation = 0;
  bool pre_frame_observed = false;
  CoreSnapshotPrefix pre_frame{};
  bool original_forwarded_once = false;
  bool original_returned = false;
  bool post_frame_observed = false;
  CoreSnapshotPrefix post_frame{};
  // Deliberately unavailable until a separate source-proved parent contract
  // joins the actual dispatcher/intermediate entry to this invocation.
  bool causal_parent_observed = false;
  std::uint64_t causal_parent_invocation_id = 0;
};
static_assert(std::is_trivially_copyable_v<SwayEndInvocation12004>);

SwayEndCaptureResult12004 CaptureSwayEndBefore12004(
    const SwayEndInvocationBindings12004 &bindings,
    const SwayEndInvocationStamp12004 &stamp,
    SwayEndSourceClass12004 source_class, const void *native_self,
    const void *effect_context, SwayEndInvocation12004 &output) noexcept;
bool CaptureSwayEndAfter12004(const SwayEndInvocationBindings12004 &bindings,
                            SwayEndInvocation12004 &output) noexcept;

// Root supplies the already validated saved typed original. Observation
// ignored/unavailable still forwards it once with identical native operands.
// The original's exceptions and return behavior are not intercepted.
SwayEndCaptureResult12004 ForwardSwayEndCommand12004(
    const SwayEndInvocationBindings12004 &bindings,
    const SwayEndInvocationStamp12004 &stamp,
    SwayEndNativeCommand12004 original, const void *secondary_this,
    SwayEndInvocation12004 &output);
SwayEndCaptureResult12004 ForwardSwayEndEffect12004(
    const SwayEndInvocationBindings12004 &bindings,
    const SwayEndInvocationStamp12004 &stamp,
    SwayEndSourceClass12004 source_class, SwayEndNativeEffect12004 original,
    const void *effect, const void *effect_context,
    SwayEndInvocation12004 &output);

// Actual common call: RCX is the Scheme and only the raw DL byte is
// consumed. The fixed callsite forwards the same operands; no source class
// or specific terminal cause is assigned by this independent observation.
using SwayEndNativeCommonTermination12004 = void (*)(const void *scheme,
                                                    std::uint8_t raw_dl);
SwayEndCaptureResult12004 CaptureSwayCommonTerminationBefore12004(
    const SwayEndInvocationBindings12004 &bindings,
    const SwayEndInvocationStamp12004 &stamp, const void *actual_scheme,
    std::uint8_t raw_dl, const CoreSnapshotPrefix *previous_observer_frame,
    SwayCommonTerminationObservation12004 &output) noexcept;
bool CaptureSwayCommonTerminationAfter12004(
    const SwayEndInvocationBindings12004 &bindings, const void *actual_scheme,
    const CoreSnapshotPrefix *previous_observer_frame,
    SwayCommonTerminationObservation12004 &output) noexcept;
// The frame argument is an already copied observer frame. This path does
// not invoke ReadCoreSnapshot, a clock getter or another native query.
// Original exceptions propagate, with no fabricated returned observation.
SwayEndCaptureResult12004 ForwardSwayCommonTermination12004(
    const SwayEndInvocationBindings12004 &bindings,
    const SwayEndInvocationStamp12004 &stamp,
    SwayEndNativeCommonTermination12004 original, const void *actual_scheme,
    std::uint8_t raw_dl, const CoreSnapshotPrefix *previous_observer_frame,
    SwayCommonTerminationObservation12004 &output);

} // namespace xar::ck3_12004
