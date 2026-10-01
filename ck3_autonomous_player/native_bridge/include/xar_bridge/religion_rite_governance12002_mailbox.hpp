#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/religion_rite_governance12002_context.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerRiteGovernancePrivateStep12002 =
    "query-player-rite-governance-v1";
inline constexpr std::string_view kPlayerRiteGovernanceDomainKey12002 =
    "player_rite_governance_v1";
inline constexpr std::string_view kPlayerRiteGovernanceBackend12002 =
    "ck3-1.20.0.2-native-player-rite-governance-v1";

struct PlayerRiteGovernanceMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  religion::governance::Bindings bindings{};
  religion::governance::Context observation{};
  bool completed = false;
  std::string failure;
};

bool IsPlayerRiteGovernancePrivateStep12002(std::string_view step) noexcept;
bool ParsePlayerRiteGovernanceRevision12002(std::string_view payload,
                                     std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerRiteGovernanceMailbox12002(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerRiteGovernanceResult12002(
    const PlayerRiteGovernanceMailboxContext12002 &, std::string_view request_id);

// Shared by the real handler and the fixture with owned native-memory bindings.
// The caller owns the context until the mailbox is terminal and reclaimed.
bool RunPlayerRiteGovernanceMailbox12002(PlayerRiteGovernanceMailboxContext12002 &,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;
bool HandlePlayerRiteGovernancePrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12002
