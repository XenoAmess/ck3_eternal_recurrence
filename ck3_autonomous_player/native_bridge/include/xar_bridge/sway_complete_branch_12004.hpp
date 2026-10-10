#pragma once

#include "xar_bridge/ck3_12004_sway_execution.hpp"

namespace xar::ck3_12004 {

inline constexpr std::string_view kSwayCompleteBranchKey12004 =
    "authored_sway_complete_100_source";

// Copied at the existing toast Execute entry. This source is distinct from
// hidden .0001/.0002 phase inputs and does not prove an enqueue or actual end.
// Observer session, sequence and query-frame attachment belong to the shared
// recorder; no native pointer or inferred end-invocation key survives here.
struct SwayCompleteBranchSource12004 {
  std::string unavailable_reason;
  std::int32_t date_raw = 0;
  std::uint32_t actor_character_id = 0xFFFFFFFFu;
  std::uint32_t target_character_id = 0xFFFFFFFFu;
  std::uint32_t scheme_id = 0xFFFFFFFFu;
  ck3_12002::SwayExecutionScopeToken12002 root;
  ck3_12002::SwayExecutionScopeToken12002 owner;
  ck3_12002::SwayExecutionScopeToken12002 target;
  ck3_12002::SwayExecutionScopeToken12002 scheme;
  bool executing_input_observed = false;
  bool message_enqueue_observed = false;
  bool material_effect_observed = false;
  bool native_terminal_state_observed = false;
  friend bool operator==(const SwayCompleteBranchSource12004 &,
                         const SwayCompleteBranchSource12004 &) = default;
};

// Reuses the admitted actual4 profile, inherited native scope lookup and
// named identifier callbacks. No new native address or installer is added.
ck3_12002::SwayExecutionBindings12002 BindSwayCompleteBranchImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// RCX=effect, RDX=EffectContext on the original owning thread, before forwarding
// Execute once. Matches send_interface_toast/title=sway_complete with the exact
// full actor/target/scheme context. A captured input is not terminal attribution.
ck3_12002::SwayExecutionCaptureResult12002 CaptureSwayCompleteBranch12004(
    const ck3_12002::SwayExecutionBindings12002 &bindings,
    const void *effect, const void *effect_context,
    SwayCompleteBranchSource12004 &output) noexcept;

} // namespace xar::ck3_12004
