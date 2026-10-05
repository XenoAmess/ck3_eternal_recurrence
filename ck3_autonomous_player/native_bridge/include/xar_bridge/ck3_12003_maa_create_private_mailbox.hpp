#pragma once

#include "xar_bridge/ck3_12003_maa_create.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kRegularMaaCreatePrivateStep12003 =
    "maa-regular-personal-create-private-v1";

bool IsRegularMaaCreatePrivateStep12003(std::string_view) noexcept;
std::string SerializeNativeMaaCreateCommandResult12003(
    const game::NativeMaaRegularPersonalCreateSubmissionV1 &,
    std::uint64_t native_revision, std::uint64_t public_revision,
    std::int32_t date_raw, std::uint64_t capture_epoch,
    std::string_view request_id, std::string_view action_id,
    const game::AdapterDescriptor &);
bool ExecuteRegularMaaCreateMailbox12003(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
bool HandleRegularMaaCreatePrivate12003(
    const game::GameAdapter &, ck3_11906::MainThreadQueryMailboxV1 &,
    const game::Snapshot &, std::uint64_t native_revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;

} // namespace xar::ck3_12002
