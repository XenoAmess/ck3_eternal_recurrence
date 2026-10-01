#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002_religion_context.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerReligionPrivateStep12002 =
    "query-player-religion-context-v1";
inline constexpr std::string_view kPlayerReligionDomainKey12002 =
    "player_religion_context_v1";
inline constexpr std::string_view kPlayerReligionBackend12002 =
    "ck3-1.20.0.2-native-player-religion-context-v1";

struct PlayerReligionMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  religion::Bindings bindings{};
  religion::Context observation{};
  bool completed = false;
  std::string failure;
};

bool IsPlayerReligionPrivateStep12002(std::string_view step) noexcept;
bool ParsePlayerReligionRevision12002(std::string_view payload,
                                     std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerReligionMailbox12002(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerReligionResult12002(
    const PlayerReligionMailboxContext12002 &, std::string_view request_id);

// Shared by the real handler and the fixture with owned native-memory bindings.
// The caller owns the context until the mailbox is terminal and reclaimed.
bool RunPlayerReligionMailbox12002(PlayerReligionMailboxContext12002 &,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;
bool HandlePlayerReligionPrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12002
