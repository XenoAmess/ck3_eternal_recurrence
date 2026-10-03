#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002_religion_context.hpp"
#include "xar_bridge/ck3_12003_spiritual_fulfillment_progress.hpp"
#include "xar_bridge/ck3_12003_spiritual_fulfillment_type.hpp"
#include "xar_bridge/ck3_12003_mystical_communion_decision_terms.hpp"
#include "xar_bridge/ck3_12003_pilgrimage_activity_type_terms.hpp"
#include "xar_bridge/ck3_12003_pilgrimage_activity_terms.hpp"
#include "xar_bridge/ck3_12003_pilgrimage_candidate_route.hpp"
#include "xar_bridge/ck3_12003_confession_decision_terms.hpp"
#include "xar_bridge/ck3_12003_confession_rite_permission.hpp"
#include "xar_bridge/ck3_12003_church_income_profile.hpp"
#include "xar_bridge/ck3_12003_church_tax_inputs.hpp"
#include "xar_bridge/ck3_12003_player_devotion_profile.hpp"
#include "xar_bridge/ck3_12003_player_rite_virtue_sin_profile.hpp"
#include "xar_bridge/ck3_12003_vow_of_poverty_terms.hpp"

#include <vector>

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
  religion::fulfillment_progress12003::Bindings progress_bindings{};
  religion::fulfillment_progress12003::Progress progress{};
  ck3_12003::religion::fulfillment_type::Type spiritual_fulfillment_type{};
  ck3_12003::religion::mystical_communion::Bindings mystical_communion_bindings{};
  ck3_12003::religion::mystical_communion::Terms mystical_communion_terms{};
  ck3_12003::religion::pilgrimage::Bindings pilgrimage_bindings{};
  ck3_12003::religion::pilgrimage::Terms pilgrimage_terms{};
  ck3_12003::religion::pilgrimage_activity_terms::Bindings pilgrimage_activity_bindings{};
  ck3_12003::religion::pilgrimage_activity_terms::Terms pilgrimage_activity_terms{};
  ck3_12003::religion::pilgrimage_route::Bindings pilgrimage_route_bindings{};
  std::vector<ck3_12003::religion::pilgrimage_route::Terms> pilgrimage_candidate_routes;
  ck3_12003::religion::confession::Bindings confession_bindings{};
  ck3_12003::religion::confession::Terms confession_terms{};
  ck3_12003::religion::confession_permission::Bindings confession_permission_bindings{};
  ck3_12003::religion::confession_permission::Terms confession_rite_permission{};
  ck3_12003::religion::church_income::Bindings church_income_bindings{};
  ck3_12003::religion::church_income::Terms church_income_terms{};
  ck3_12003::religion::church_tax_inputs::Bindings church_tax_bindings{};
  ck3_12003::religion::church_tax_inputs::Terms church_tax_inputs{};
  religion::devotion_profile12003::Bindings devotion_bindings{};
  religion::devotion_profile12003::Profile devotion_profile{};
  religion::rite_virtue_sin_profile12003::Bindings rite_virtue_sin_bindings{};
  religion::rite_virtue_sin_profile12003::Profile rite_virtue_sin_profile{};
  ck3_12003::religion::vow_of_poverty_terms12003::Bindings vow_of_poverty_bindings{};
  ck3_12003::religion::vow_of_poverty_terms12003::Terms vow_of_poverty_terms{};
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
