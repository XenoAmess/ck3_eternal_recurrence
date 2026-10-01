#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/religion_rite_governance12002_organization_members.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerRiteMembersPrivateStep12002 =
    "query-player-rite-members-v1";
inline constexpr std::string_view kPlayerRiteMembersDomainKey12002 =
    "player_rite_members_v1";
inline constexpr std::string_view kPlayerRiteMembersBackend12002 =
    "ck3-1.20.0.2-native-player-rite-members-v1";

struct PlayerRiteMembersMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  religion::organization::members::Bindings bindings{};
  religion::organization::members::Snapshot observation{};
  bool completed = false;
  std::string failure;
};

bool IsPlayerRiteMembersPrivateStep12002(std::string_view step) noexcept;
bool ParsePlayerRiteMembersRevision12002(std::string_view payload,
                                       std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerRiteMembersMailbox12002(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerRiteMembersResult12002(
    const PlayerRiteMembersMailboxContext12002 &, std::string_view request_id);

// The worker owns the context through terminal Wait/Reclaim. Owned native
// bindings let the offline fixture exercise the same reader and serializer.
bool RunPlayerRiteMembersMailbox12002(PlayerRiteMembersMailboxContext12002 &,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;
bool HandlePlayerRiteMembersPrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12002
