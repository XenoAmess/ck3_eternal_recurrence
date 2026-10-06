#pragma once

#include "xar_bridge/ck3_12004_prisoner.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"

namespace xar::ck3_12004 {

struct PrisonerPrivateWorkerState12004 {
  std::uint64_t query_sequence = 0;
};

bool ExecutePlayerPrisonerCollection12004(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

ck3_11906::MainThreadQueryInstallEnvironmentV1
BindPrisonerCollectionMailboxEnvironment12004(std::uintptr_t module_base,
    std::string_view executable_sha256) noexcept;

bool HandlePlayerPrisonerCollection12004(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published_core, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    PrisonerPrivateWorkerState12004 &state, std::string &serialized,
    std::string &failure);

} // namespace xar::ck3_12004
