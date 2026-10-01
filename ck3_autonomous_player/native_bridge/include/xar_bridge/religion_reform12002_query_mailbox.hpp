#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/religion_reform12002_query_runtime.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerReligionReformPrivateStep12002 =
    "query-player-religion-reform-context-v1";
inline constexpr std::string_view kPlayerReligionReformDomainKey12002 =
    "player_religion_reform_context_v1";
inline constexpr std::string_view kPlayerReligionReformBackend12002 =
    "ck3-1.20.0.2-native-player-religion-reform-context-v1";

struct PlayerReligionReformMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  religion_reform::query::Bindings bindings{};
  religion_reform::query::Observation observation{};
  bool completed = false;
  std::string failure;
};

bool IsPlayerReligionReformPrivateStep12002(std::string_view step) noexcept;
bool ParsePlayerReligionReformRevision12002(std::string_view payload,
                                          std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerReligionReformMailbox12002(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerReligionReformResult12002(
    const PlayerReligionReformMailboxContext12002 &, std::string_view request_id);

// The real handler and the owned-memory fixture share this exact caller. The
// context remains alive until its submitted owner-thread query is reclaimed.
bool RunPlayerReligionReformMailbox12002(PlayerReligionReformMailboxContext12002 &,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;
bool HandlePlayerReligionReformPrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12002
