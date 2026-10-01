#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/religion_reform12002_fullchoices.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerReligionDraftDoctrineChoicesPrivateStep12002 =
    "query-player-religion-draft-doctrine-choices-v1";
inline constexpr std::string_view kPlayerReligionDraftDoctrineChoicesDomainKey12002 =
    "player_religion_draft_doctrine_choices_v1";
inline constexpr std::string_view kPlayerReligionDraftDoctrineChoicesBackend12002 =
    "ck3-1.20.0.2-native-player-religion-draft-doctrine-choices-v1";

struct PlayerReligionDraftDoctrineChoicesMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  religion_reform::DraftChoiceBindings bindings{};
  religion_reform::DraftFullDoctrineChoices observation{};
  bool completed = false;
  std::string failure;
};

bool IsPlayerReligionDraftDoctrineChoicesPrivateStep12002(std::string_view step) noexcept;
bool ParsePlayerReligionDraftDoctrineChoicesRevision12002(std::string_view payload,
                                                        std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerReligionDraftDoctrineChoicesMailbox12002(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerReligionDraftDoctrineChoicesResult12002(
    const PlayerReligionDraftDoctrineChoicesMailboxContext12002 &, std::string_view request_id);

// Same actual owning-thread caller for production and the new owned fixture.
// Observes existing draft groups without constructing items or opening GUI.
bool RunPlayerReligionDraftDoctrineChoicesMailbox12002(PlayerReligionDraftDoctrineChoicesMailboxContext12002 &,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;
bool HandlePlayerReligionDraftDoctrineChoicesPrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12002
