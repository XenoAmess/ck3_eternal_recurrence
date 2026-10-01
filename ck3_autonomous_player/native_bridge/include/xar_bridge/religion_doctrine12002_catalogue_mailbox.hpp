#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/religion_doctrine12002_catalogue.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerReligionDoctrineCataloguePrivateStep12002 =
    "query-player-religion-doctrine-catalogue-v1";
inline constexpr std::string_view kPlayerReligionDoctrineCatalogueDomainKey12002 =
    "player_religion_doctrine_catalogue_v1";
inline constexpr std::string_view kPlayerReligionDoctrineCatalogueBackend12002 =
    "ck3-1.20.0.2-native-player-religion-doctrine-catalogue-v1";

struct PlayerReligionDoctrineCatalogueMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  religion::doctrine12002::CatalogueBindings bindings{};
  religion::doctrine12002::DoctrineCatalogue observation{};
  bool completed = false;
  std::string failure;
};

bool IsPlayerReligionDoctrineCataloguePrivateStep12002(std::string_view step) noexcept;
bool ParsePlayerReligionDoctrineCatalogueRevision12002(std::string_view payload,
                                     std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerReligionDoctrineCatalogueMailbox12002(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerReligionDoctrineCatalogueResult12002(
    const PlayerReligionDoctrineCatalogueMailboxContext12002 &, std::string_view request_id);

// Shared by the real handler and the fixture with owned native-memory bindings.
// The caller owns the context until the mailbox is terminal and reclaimed.
bool RunPlayerReligionDoctrineCatalogueMailbox12002(PlayerReligionDoctrineCatalogueMailboxContext12002 &,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;
bool HandlePlayerReligionDoctrineCataloguePrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12002
