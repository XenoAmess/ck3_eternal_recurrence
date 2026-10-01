#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/religion_doctrine12002_choices.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerReligionDoctrineKnowledgePrivateStep12002 =
    "query-player-religion-doctrine-knowledge-v1";
inline constexpr std::string_view kPlayerReligionDoctrineKnowledgeDomainKey12002 =
    "player_religion_doctrine_knowledge_v1";
inline constexpr std::string_view kPlayerReligionDoctrineKnowledgeBackend12002 =
    "ck3-1.20.0.2-native-player-religion-doctrine-knowledge-v1";

struct PlayerReligionDoctrineKnowledgeMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  religion::doctrine12002::KnowledgeBindings bindings{};
  std::optional<std::string> doctrine_key;
  religion::doctrine12002::PlayedDoctrineKnowledge learned_observation{};
  religion::doctrine12002::PlayedDoctrineKnowledgeLookup lookup_observation{};
  bool completed = false;
  std::string failure;
};

bool IsPlayerReligionDoctrineKnowledgePrivateStep12002(std::string_view step) noexcept;
bool ParsePlayerReligionDoctrineKnowledgeRequest12002(std::string_view payload,
    std::uint64_t &expected_revision, std::optional<std::string> &doctrine_key) noexcept;
bool ExecutePlayerReligionDoctrineKnowledgeMailbox12002(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerReligionDoctrineKnowledgeResult12002(
    const PlayerReligionDoctrineKnowledgeMailboxContext12002 &, std::string_view request_id);
// Real worker and offline fixture call this same owned-context runtime.
bool RunPlayerReligionDoctrineKnowledgeMailbox12002(
    PlayerReligionDoctrineKnowledgeMailboxContext12002 &, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;
bool HandlePlayerReligionDoctrineKnowledgePrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept;

} // namespace xar::ck3_12002
