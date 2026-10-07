#pragma once

#include "xar_bridge/ck3_12004_prisoner.hpp"
#include "xar_bridge/ck3_12004_prisoner_ransom_action.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"

#include <optional>

namespace xar::ck3_12004 {

struct PrisonerPrivateWorkerState12004 {
  std::uint64_t query_sequence = 0;
  std::uint64_t war_query_sequence = 0;
  std::optional<PlayerPrisonerRansomQuoteV1> current_quote;
  std::uint64_t quote_revision = 0;
  std::uint64_t quote_query_sequence = 0;
  bool may_have_submitted = false;
};

bool ExecutePlayerPrisonerCollection12004(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
bool ExecutePlayerPrisonerRansom12004(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

// The same whole wire is consumed by the production route and new offline
// producer. An accepted queue remains pending until custody and gold are read.
std::string SerializePlayerPrisonerRansomCommandResult12004(
    std::string_view request_id, PlayerPrisonerRansomSubmitV1 result);

ck3_11906::MainThreadQueryInstallEnvironmentV1
BindPrisonerCollectionMailboxEnvironment12004(std::uintptr_t module_base,
    std::string_view executable_sha256) noexcept;

bool HandlePlayerPrisonerCollection12004(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published_core, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    PrisonerPrivateWorkerState12004 &state, std::string &serialized,
    std::string &failure);

bool HandlePlayerPrisonerRansom12004(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published_core, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    PrisonerPrivateWorkerState12004 &state, std::string &serialized,
    std::string &failure);

} // namespace xar::ck3_12004
