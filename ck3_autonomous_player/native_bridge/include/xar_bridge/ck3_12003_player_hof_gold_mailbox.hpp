#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12003_player_hof_gold_context.hpp"

namespace xar::ck3_12003 {

inline constexpr std::string_view kPlayerHeadOfFaithGoldPrivateStep12003 =
    "query-player-head-of-faith-gold-context-v1";
inline constexpr std::string_view kPlayerHeadOfFaithGoldDomainKey12003 =
    "player_head_of_faith_gold_context_v1";
inline constexpr std::string_view kPlayerHeadOfFaithGoldBackend12003 =
    "ck3-1.20.0.3-native-player-head-of-faith-gold-context-v1";

struct PlayerHeadOfFaithGoldMailboxContext12003 {
  ck3_12002::QueryMailboxEnvelope envelope{};
  religion::hof_gold::Bindings bindings{};
  religion::hof_gold::Context observation{};
  bool completed = false;
  std::string failure;
};

bool IsPlayerHeadOfFaithGoldPrivateStep12003(std::string_view step) noexcept;
bool ParsePlayerHeadOfFaithGoldRevision12003(
    std::string_view payload, std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerHeadOfFaithGoldMailbox12003(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerHeadOfFaithGoldResult12003(
    const PlayerHeadOfFaithGoldMailboxContext12003 &, std::string_view request_id);
bool RunPlayerHeadOfFaithGoldMailbox12003(PlayerHeadOfFaithGoldMailboxContext12003 &,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;
bool HandlePlayerHeadOfFaithGoldPrivate12003(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12003
