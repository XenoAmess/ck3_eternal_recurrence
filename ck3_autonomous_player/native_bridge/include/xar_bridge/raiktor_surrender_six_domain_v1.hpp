#pragma once

#include "xar_bridge/raiktor_surrender_truce_v1.hpp"
#include "xar_bridge/raiktor_war_bound_regiment_v1.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_11906 {

inline constexpr std::string_view kRaiktorSurrenderSixDomainV1GameVersion =
    "1.19.0.6";
inline constexpr std::string_view
    kRaiktorSurrenderSixDomainV1ExecutableSha256 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view kRaiktorSurrenderSixDomainV1BackendId =
    "ck3-1.19.0.6-native-raiktor-surrender-six-domain-v1";

enum class RaiktorSurrenderSixDomainStatusV1 : std::uint8_t {
  unavailable = 0,
  incomplete = 1,
  complete = 2,
};

enum class RaiktorSurrenderSixDomainFailureV1 : std::uint8_t {
  none = 0,
  invalid_frame,
  invalid_claims_base,
  invalid_gold_domain,
  invalid_prestige_domain,
  invalid_prisoner_domain,
  invalid_favor_domain,
  invalid_truce_domain,
  invalid_war_bound_domain,
};

enum class RaiktorSurrenderMissingDomainV1 : std::uint32_t {
  none = 0,
  claims_base = 1U << 0U,
  gold = 1U << 1U,
  prestige = 1U << 2U,
  prisoner_release = 1U << 3U,
  favor_hook = 1U << 4U,
  truce = 1U << 5U,
  generic_war_bound_current = 1U << 6U,
};

constexpr RaiktorSurrenderMissingDomainV1 operator|(
    RaiktorSurrenderMissingDomainV1 left,
    RaiktorSurrenderMissingDomainV1 right) noexcept {
  return static_cast<RaiktorSurrenderMissingDomainV1>(
      static_cast<std::uint32_t>(left) |
      static_cast<std::uint32_t>(right));
}

constexpr RaiktorSurrenderMissingDomainV1 &operator|=(
    RaiktorSurrenderMissingDomainV1 &left,
    RaiktorSurrenderMissingDomainV1 right) noexcept {
  left = left | right;
  return left;
}

struct RaiktorSurrenderSameFrameV1 {
  std::uint64_t snapshot_revision = 0;
  std::uint64_t native_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t war_id = -1;
  std::int32_t active_casus_belli_database_index = -1;
  bool exact_raiktor_claim_cb = false;
  std::int32_t primary_attacker_character_id = -1;
  std::int32_t primary_defender_character_id = -1;
  std::int32_t claimant_character_id = -1;

  friend bool operator==(const RaiktorSurrenderSameFrameV1 &,
                         const RaiktorSurrenderSameFrameV1 &) = default;
};

struct RaiktorSurrenderClaimsBaseV1 {
  std::vector<std::int32_t> target_title_ids;
  std::vector<game::WarClaimSnapshot> claims;
  std::string declared_title_disposition;
  std::string claim_disposition;
  bool target_order_stable = false;
  bool claim_rows_stable = false;

  friend bool operator==(const RaiktorSurrenderClaimsBaseV1 &,
                         const RaiktorSurrenderClaimsBaseV1 &) = default;
};

template <typename Observation> struct RaiktorSurrenderStampedDomainV1 {
  RaiktorSurrenderSameFrameV1 frame;
  Observation observation;

  friend bool operator==(const RaiktorSurrenderStampedDomainV1 &,
                         const RaiktorSurrenderStampedDomainV1 &) = default;
};

using RaiktorSurrenderClaimsDomainV1 =
    RaiktorSurrenderStampedDomainV1<RaiktorSurrenderClaimsBaseV1>;
using RaiktorSurrenderGoldDomainV1 =
    RaiktorSurrenderStampedDomainV1<RaiktorSurrenderGoldObservation>;
using RaiktorSurrenderPrestigeDomainV1 =
    RaiktorSurrenderStampedDomainV1<RaiktorSurrenderPrestigeObservation>;
using RaiktorSurrenderPrisonerDomainV1 = RaiktorSurrenderStampedDomainV1<
    RaiktorSurrenderPrisonerReleaseObservation>;
using RaiktorSurrenderFavorDomainV1 =
    RaiktorSurrenderStampedDomainV1<RaiktorSurrenderFavorHookObservation>;
using RaiktorSurrenderTruceDomainV1 =
    RaiktorSurrenderStampedDomainV1<RaiktorSurrenderTruceObservationV1>;
using RaiktorSurrenderWarBoundDomainV1 = RaiktorSurrenderStampedDomainV1<
    RaiktorWarBoundRegimentObservationV1>;

struct RaiktorSurrenderSixDomainInputV1 {
  RaiktorSurrenderSameFrameV1 frame;
  std::optional<RaiktorSurrenderClaimsDomainV1> claims_base;
  std::optional<RaiktorSurrenderGoldDomainV1> gold;
  std::optional<RaiktorSurrenderPrestigeDomainV1> prestige;
  std::optional<RaiktorSurrenderPrisonerDomainV1> prisoner_release;
  std::optional<RaiktorSurrenderFavorDomainV1> favor_hook;
  std::optional<RaiktorSurrenderTruceDomainV1> truce;
  std::optional<RaiktorSurrenderWarBoundDomainV1>
      generic_war_bound_current;

  friend bool operator==(const RaiktorSurrenderSixDomainInputV1 &,
                         const RaiktorSurrenderSixDomainInputV1 &) = default;
};

struct RaiktorSurrenderSixDomainReadinessV1 {
  bool claims_base_ready = false;
  bool gold_ready = false;
  bool prestige_ready = false;
  bool prisoner_release_ready = false;
  bool favor_hook_ready = false;
  bool truce_ready = false;
  bool generic_war_bound_current_ready = false;
  bool postwar_cleanup_ready = false;
  bool source_specific_war_bound_ready = false;
  bool pre_soldiers_ready = false;
  bool proven_soldier_loss_ready = false;
  bool six_dynamic_domains_ready = false;
  bool same_frame_stable = false;
  bool action_terms_ready = false;
  bool automatic_surrender_ready = false;

  friend bool operator==(const RaiktorSurrenderSixDomainReadinessV1 &,
                         const RaiktorSurrenderSixDomainReadinessV1 &) =
      default;
};

struct RaiktorSurrenderSixDomainObservationV1 {
  RaiktorSurrenderSixDomainStatusV1 status =
      RaiktorSurrenderSixDomainStatusV1::unavailable;
  RaiktorSurrenderSixDomainFailureV1 failure =
      RaiktorSurrenderSixDomainFailureV1::invalid_frame;
  RaiktorSurrenderSameFrameV1 frame;
  RaiktorSurrenderMissingDomainV1 missing_domains =
      RaiktorSurrenderMissingDomainV1::none;
  std::optional<RaiktorSurrenderClaimsBaseV1> claims_base;
  std::optional<RaiktorSurrenderGoldObservation> gold;
  std::optional<RaiktorSurrenderPrestigeObservation> prestige;
  std::optional<RaiktorSurrenderPrisonerReleaseObservation>
      prisoner_release;
  std::optional<RaiktorSurrenderFavorHookObservation> favor_hook;
  std::optional<RaiktorSurrenderTruceObservationV1> truce;
  std::optional<RaiktorWarBoundRegimentObservationV1>
      generic_war_bound_current;
  RaiktorSurrenderSixDomainReadinessV1 readiness;

  friend bool operator==(const RaiktorSurrenderSixDomainObservationV1 &,
                         const RaiktorSurrenderSixDomainObservationV1 &) =
      default;
};

std::string_view RaiktorSurrenderSixDomainFailureReasonV1(
    RaiktorSurrenderSixDomainFailureV1 failure) noexcept;

// Returns true for both complete and structurally valid incomplete
// aggregations. Missing optionals are an observed readiness state, not a
// malformed contract. A present but malformed or cross-frame domain returns
// false and leaves an unavailable observation with the typed failure.
bool BuildRaiktorSurrenderSixDomainObservationV1(
    const RaiktorSurrenderSixDomainInputV1 &input,
    RaiktorSurrenderSixDomainObservationV1 &output) noexcept;

} // namespace xar::ck3_11906
