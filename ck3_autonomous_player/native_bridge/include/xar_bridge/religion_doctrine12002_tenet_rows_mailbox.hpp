#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/religion_doctrine12002_tenet_rows.hpp"
#include "xar_bridge/ck3_12003_target_rite_tenet_comparison.hpp"
#include "xar_bridge/ck3_12003_player_tenet_knowledge_catalogue.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerReligionTenetsPrivateStep12002 =
    "query-player-religion-tenets-v1";
inline constexpr std::string_view kPlayerReligionTenetsDomainKey12002 =
    "player_religion_tenets_v1";
inline constexpr std::string_view kPlayerReligionTenetsBackend12002 =
    "ck3-1.20.0.2-native-player-religion-tenets-v1";

struct PlayerReligionTenetsMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  religion::Bindings bindings{};
  religion::doctrine12002::TenetRowsBindings tenet_bindings{};
  religion::doctrine12002::TenetRowsContext observation{};
  // Absent pair keeps the original Tenet DTO byte-for-byte unchanged.
  std::optional<std::uint32_t> target_rite_id;
  std::string tenet_key;
  ck3_12003::religion::target_tenet::Bindings comparison_bindings{};
  ck3_12003::religion::target_tenet::Comparison comparison{};
  // False preserves the original result and does not read actor knowledge.
  bool include_knowledge_catalogue = false;
  ck3_12003::religion::tenet_knowledge::Bindings knowledge_bindings{};
  ck3_12003::religion::tenet_knowledge::Catalogue knowledge_catalogue{};
  bool completed = false;
  std::string failure;
};

bool IsPlayerReligionTenetsPrivateStep12002(std::string_view step) noexcept;
bool ParsePlayerReligionTenetsRevision12002(std::string_view payload,
                                     std::uint64_t &expected_revision) noexcept;
bool ParsePlayerReligionTenetsComparisonRequest12003(std::string_view payload,
    std::optional<std::uint32_t> &target_rite_id, std::string &tenet_key) noexcept;
bool ParsePlayerReligionTenetsKnowledgeRequest12003(std::string_view payload,
    bool &include_knowledge_catalogue) noexcept;
bool ExecutePlayerReligionTenetsMailbox12002(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerReligionTenetsResult12002(
    const PlayerReligionTenetsMailboxContext12002 &, std::string_view request_id);

// Shared by the real handler and the fixture with owned native-memory bindings.
// The caller owns the context until the mailbox is terminal and reclaimed.
bool RunPlayerReligionTenetsMailbox12002(PlayerReligionTenetsMailboxContext12002 &,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;
bool HandlePlayerReligionTenetsPrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12002
