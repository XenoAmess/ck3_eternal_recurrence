#pragma once

#include "xar_bridge/ck3_12002_epidemic_recovery.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"

#include <string>
#include <string_view>

namespace xar::ck3_12002 {

struct EpidemicRecoveryMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  epidemic_recovery::Bindings source{};
  std::int32_t requested_title_id = 0;
  ck3_11906::PlayerEpidemicRecoveryV1 result{};
  bool completed = false;
  std::string failure{};
};

bool IsEpidemicRecoveryPrivate12002(std::string_view step) noexcept;
bool ExecutePlayerEpidemicRecoveryMailbox12002(
    void *context, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

// The production worker supplies its published snapshot. All actual game
// captures and county reads execute through the registered application owner.
bool HandleEpidemicRecoveryPrivate12002(
    const game::GameAdapter &adapter, ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;

// The same controller with an explicit source binding. The standard worker
// caller binds the exact current image before delegating; offline fixtures
// provide their own objects/callbacks without replacing provider or payload.
bool HandleEpidemicRecoveryPrivateBound12002(
    const game::GameAdapter &adapter, ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    const epidemic_recovery::Bindings &source,
    std::string &serialized, std::string &failure) noexcept;

std::string SerializeEpidemicRecoveryPacket12002(
    const EpidemicRecoveryMailboxContext12002 &query,
    std::string_view step, std::string_view request_id);

} // namespace xar::ck3_12002
