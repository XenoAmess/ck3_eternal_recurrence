#pragma once

#include "xar_bridge/ck3_12002_family_obligations_lineage.hpp"
#include "xar_bridge/ck3_12002_family_obligations_break.hpp"
#include "xar_bridge/ck3_12002_family_obligations_alliance.hpp"
#include "xar_bridge/game_adapter.hpp"

#include <string>
#include <string_view>

namespace xar::ck3_12002 {
#if defined(XAR_CK3_ENABLE_G2_M5_FAMILY_OBLIGATIONS_PRIVATE_QUERY_V1) && \
    defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)

inline constexpr std::string_view kFamilyObligationsPrivateStep12002 =
    "read-family-obligations-private-12002";

struct FamilyObligationsRequest12002 {
  std::int32_t subject_character_id = -1;
  std::int32_t candidate_character_id = -1;
  std::int32_t ally_character_id = -1;
  std::int32_t break_recipient_character_id = -1;
  bool request_matrilineal_option = false;
  bool enumerate_current_allies = false;
  std::uint64_t expected_snapshot_revision = 0;
};

struct FamilyObligationsObservation12002 {
  game::Snapshot frame{};
  std::uint64_t snapshot_revision = 0;
  FamilyObligationsRequest12002 request{};
  family_obligations_lineage::Snapshot lineage{};
  FamilyObligationsBreakTermsV1 break_terms{};
  std::string lineage_reason;
  bool lineage_available = false;
  family_obligations_alliance::Snapshot alliance{};
  std::string alliance_reason;
  bool alliance_available = false;
  family_obligations_alliance::CurrentAlliesSnapshot current_allies{};
  std::string current_allies_reason;
  bool current_allies_available = false;
};

// Availability covers each explicitly requested native lane. An ally-only
// request needs no unrelated marriage pair and never sends an interaction.
std::string_view FamilyObligationsQueryStatus12002(
    const FamilyObligationsObservation12002 &) noexcept;
std::string SerializeFamilyObligationsObservation12002(
    const FamilyObligationsObservation12002 &);
std::string SerializeFamilyObligationsResult12002(
    std::string_view request_id, const FamilyObligationsObservation12002 &);

#endif
} // namespace xar::ck3_12002
