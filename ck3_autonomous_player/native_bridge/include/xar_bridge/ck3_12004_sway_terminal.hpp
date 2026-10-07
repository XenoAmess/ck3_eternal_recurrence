#pragma once

#include "xar_bridge/ck3_12004_sway.hpp"
#include "xar_bridge/ck3_12002_sway_completion_mailbox.hpp"

namespace xar::ck3_12004 {

// Reuse caller-owned completion software types. No old image binder/getter is
// reached; the actual4 retained-row route leaves Chance/CanContinue unobserved.
ck3_12002::SwayCompletionBindings12002 BindSwayTerminalImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
bool ReadSwayTerminal12004(
    const ck3_12002::SwayCompletionBindings12002 &bindings,
    const ck3_12002::SwayCompletionRequestV1 &request,
    ck3_12002::SwayCompletionStateV1 &output) noexcept;
bool ExecuteSwayTerminalMailbox12004(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
std::string SerializeSwayTerminalCommandResult12004(
    const ck3_12002::SwayCompletionStateV1 &output,
    std::uint64_t revision, std::int32_t date_raw,
    std::string_view request_id, const game::AdapterDescriptor &descriptor);
bool HandleSwayTerminal12004(
    const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12004
