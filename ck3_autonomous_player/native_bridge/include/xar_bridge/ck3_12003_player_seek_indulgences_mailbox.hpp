#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12003_player_seek_indulgences_terms.hpp"

namespace xar::ck3_12003 {

inline constexpr std::string_view kPlayerSeekIndulgencesTermsPrivateStep12003 =
    "query-player-seek-indulgences-terms-v1";
inline constexpr std::string_view kPlayerSeekIndulgencesTermsDomainKey12003 =
    "player_seek_indulgences_terms_v1";
inline constexpr std::string_view kPlayerSeekIndulgencesTermsBackend12003 =
    "ck3-1.20.0.3-native-player-seek-indulgences-terms-v1";

struct PlayerSeekIndulgencesMailboxContext12003 {
  ck3_12002::QueryMailboxEnvelope envelope{};
  religion::seek_indulgences::Bindings bindings{};
  religion::seek_indulgences::Context observation{};
  std::uint32_t requested_recipient_character_id = UINT32_MAX;
  bool completed = false;
  std::string failure;
};

bool IsPlayerSeekIndulgencesTermsPrivateStep12003(std::string_view step) noexcept;
bool ParsePlayerSeekIndulgencesTermsRevision12003(
    std::string_view payload, std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerSeekIndulgencesTermsMailbox12003(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerSeekIndulgencesTermsResult12003(
    const PlayerSeekIndulgencesMailboxContext12003 &, std::string_view request_id);
bool RunPlayerSeekIndulgencesTermsMailbox12003(PlayerSeekIndulgencesMailboxContext12003 &,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;
bool HandlePlayerSeekIndulgencesTermsPrivate12003(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12003
