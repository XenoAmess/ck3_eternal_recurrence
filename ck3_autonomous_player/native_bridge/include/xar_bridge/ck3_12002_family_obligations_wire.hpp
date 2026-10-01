#pragma once

#include "xar_bridge/ck3_12002_family_obligations_lineage.hpp"
#include "xar_bridge/ck3_12002_family_obligations_break.hpp"
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
};

// Availability covers requested nonwar lanes only. The owner has deferred
// alliance-war research; an ally argument does not execute a native war read.
std::string_view FamilyObligationsQueryStatus12002(
    const FamilyObligationsObservation12002 &) noexcept;
std::string SerializeFamilyObligationsObservation12002(
    const FamilyObligationsObservation12002 &);
std::string SerializeFamilyObligationsResult12002(
    std::string_view request_id, const FamilyObligationsObservation12002 &);

#endif
} // namespace xar::ck3_12002
