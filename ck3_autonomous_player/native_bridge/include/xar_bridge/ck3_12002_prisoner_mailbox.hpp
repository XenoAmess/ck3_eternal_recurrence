#pragma once
#include "xar_bridge/ck3_12002_prisoner.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include <optional>

namespace xar::ck3_12002 {
struct PrisonerPrivateWorkerState12002 {
  std::uint64_t query_sequence = 0;
  std::optional<PlayerPrisonerRansomQuoteV1> current_quote;
  std::uint64_t quote_revision = 0;
  std::uint64_t quote_query_sequence = 0;
  bool may_have_submitted = false;
};
bool ExecutePlayerPrisonerCollection12002(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
bool ExecutePlayerPrisonerRansom12002(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
bool HandlePlayerPrisonerPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    PrisonerPrivateWorkerState12002 &state, std::string &serialized,
    std::string &failure);
} // namespace xar::ck3_12002
