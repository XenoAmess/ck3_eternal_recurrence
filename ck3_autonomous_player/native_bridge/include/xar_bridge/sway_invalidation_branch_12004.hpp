#pragma once

#include "xar_bridge/sway_complete_branch_12004.hpp"

namespace xar::ck3_12004 {

inline constexpr std::string_view kSwayInvalidationBranchKey12004 =
    "authored_sway_invalidated_title_source";
inline constexpr std::string_view kSwayInvalidationTitleKey12004 =
    "sway_invalidated_title";

// Reuse only the copied identity layout. The caller records the distinct
// invalidation source kind. This alias does not establish a completion source
// or permit arming the complete branch's child-end causal parent guard.
using SwayInvalidationBranchSource12004 = SwayCompleteBranchSource12004;

// The existing admitted actual.4 binder and identifier/native scope callbacks
// remain the binding source; no legacy reason-child coordinates are admitted.
ck3_12002::SwayExecutionBindings12002 BindSwayInvalidationBranchImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// At actual Toast Execute entry, before unchanged original forwarding once:
// send_interface_toast + literal sway_invalidated_title + exact owner/root,
// target and full SchemeID inherited tokens. A copied executing title supplies
// no specific Tooltip reason, enqueue, material, typed end or terminal cause.
// The original Toast remains an unmatched nearest-parent causal barrier.
ck3_12002::SwayExecutionCaptureResult12002 CaptureSwayInvalidationBranch12004(
    const ck3_12002::SwayExecutionBindings12002 &bindings,
    const void *effect, const void *effect_context,
    SwayInvalidationBranchSource12004 &output) noexcept;

} // namespace xar::ck3_12004
