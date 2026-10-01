#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/religion_doctrine12002_query.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerReligionDoctrinesPrivateStep12002 =
    "query-player-religion-doctrines-v1";
inline constexpr std::string_view kPlayerReligionDoctrinesDomainKey12002 =
    "player_religion_doctrines_v1";
inline constexpr std::string_view kPlayerReligionDoctrinesBackend12002 =
    "ck3-1.20.0.2-native-player-religion-doctrines-v1";

struct PlayerReligionDoctrinesMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  religion::doctrine12002::CurrentDoctrineBindings bindings{};
  religion::doctrine12002::CurrentDoctrineContext observation{};
  bool completed = false;
  std::string failure;
};

bool IsPlayerReligionDoctrinesPrivateStep12002(std::string_view step) noexcept;
bool ParsePlayerReligionDoctrinesRevision12002(std::string_view payload,
                                     std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerReligionDoctrinesMailbox12002(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerReligionDoctrinesResult12002(
    const PlayerReligionDoctrinesMailboxContext12002 &, std::string_view request_id);

// Shared by the real handler and the fixture with owned native-memory bindings.
// The caller owns the context until the mailbox is terminal and reclaimed.
bool RunPlayerReligionDoctrinesMailbox12002(PlayerReligionDoctrinesMailboxContext12002 &,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;
bool HandlePlayerReligionDoctrinesPrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12002
