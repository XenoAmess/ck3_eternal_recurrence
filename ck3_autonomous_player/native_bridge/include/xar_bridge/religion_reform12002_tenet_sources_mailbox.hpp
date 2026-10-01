#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/religion_reform12002_tenet_sources.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerReligionDraftTenetChoicesPrivateStep12002 =
    "query-player-religion-draft-tenet-choices-v1";
inline constexpr std::string_view kPlayerReligionDraftTenetChoicesDomainKey12002 =
    "player_religion_draft_tenet_choices_v1";
inline constexpr std::string_view kPlayerReligionDraftTenetChoicesBackend12002 =
    "ck3-1.20.0.2-native-player-religion-draft-tenet-choices-v1";

struct PlayerReligionDraftTenetChoicesMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  religion_reform::TenetSourcesBindings bindings{};
  religion_reform::DraftTenetSources observation{};
  bool completed = false;
  std::string failure;
};

bool IsPlayerReligionDraftTenetChoicesPrivateStep12002(std::string_view step) noexcept;
bool ParsePlayerReligionDraftTenetChoicesRevision12002(std::string_view payload,
                                                     std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerReligionDraftTenetChoicesMailbox12002(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerReligionDraftTenetChoicesResult12002(
    const PlayerReligionDraftTenetChoicesMailboxContext12002 &, std::string_view request_id);

// Production and the new owned fixture share this actual owning-thread caller.
// No item, category window or draft is constructed; no religion action is sent.
bool RunPlayerReligionDraftTenetChoicesMailbox12002(PlayerReligionDraftTenetChoicesMailboxContext12002 &,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;
bool HandlePlayerReligionDraftTenetChoicesPrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12002
