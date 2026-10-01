#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/religion_reform12002_group_model.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerReligionDraftGroupsPrivateStep12002 =
    "query-player-religion-draft-groups-v1";
inline constexpr std::string_view kPlayerReligionDraftGroupsDomainKey12002 =
    "player_religion_draft_groups_v1";
inline constexpr std::string_view kPlayerReligionDraftGroupsBackend12002 =
    "ck3-1.20.0.2-native-player-religion-draft-groups-v1";

struct PlayerReligionDraftGroupsMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  religion_reform::DraftChoiceBindings bindings{};
  religion_reform::DraftGroupModel observation{};
  bool completed = false;
  std::string failure;
};

bool IsPlayerReligionDraftGroupsPrivateStep12002(std::string_view step) noexcept;
bool ParsePlayerReligionDraftGroupsRevision12002(std::string_view payload,
                                               std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerReligionDraftGroupsMailbox12002(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerReligionDraftGroupsResult12002(
    const PlayerReligionDraftGroupsMailboxContext12002 &, std::string_view request_id);

// Production and owned-memory fixtures use the same owning-thread caller.
// This only reads an already-existing creation window and its current caches.
bool RunPlayerReligionDraftGroupsMailbox12002(PlayerReligionDraftGroupsMailboxContext12002 &,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;
bool HandlePlayerReligionDraftGroupsPrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12002
