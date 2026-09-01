#include "xar_bridge/raiktor_surrender_six_domain_v1.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <string_view>
#include <utility>
#include <vector>

namespace xar::ck3_11906 {
namespace {

constexpr std::int64_t kFixedPointScale = 100'000;
constexpr std::int64_t kPrestigeLossCapRaw = 1'000 * kFixedPointScale;

bool ValidFullId(std::int32_t value) noexcept { return value != -1; }

bool ValidFrame(const RaiktorSurrenderSameFrameV1 &frame) noexcept {
  return frame.snapshot_revision != 0 && frame.native_revision != 0 &&
         frame.paused && ValidFullId(frame.war_id) &&
         frame.active_casus_belli_database_index >= 0 &&
         frame.exact_raiktor_claim_cb &&
         ValidFullId(frame.primary_attacker_character_id) &&
         ValidFullId(frame.primary_defender_character_id) &&
         ValidFullId(frame.claimant_character_id) &&
         frame.primary_attacker_character_id !=
             frame.primary_defender_character_id;
}

bool ValidFixedPoint(const game::FixedPointValue &value) noexcept {
  return value.scale == kFixedPointScale;
}

bool UniqueFullIds(const std::vector<std::int32_t> &values,
                   bool require_nonempty) noexcept {
  if ((require_nonempty && values.empty()) ||
      values.size() >
          static_cast<std::size_t>((std::numeric_limits<std::int32_t>::max)())) {
    return false;
  }
  std::vector<std::int32_t> seen;
  seen.reserve(values.size());
  for (const auto value : values) {
    if (!ValidFullId(value) ||
        std::find(seen.begin(), seen.end(), value) != seen.end()) {
      return false;
    }
    seen.push_back(value);
  }
  return true;
}

bool Contains(const std::vector<std::int32_t> &values,
              std::int32_t value) noexcept {
  return std::find(values.begin(), values.end(), value) != values.end();
}

bool ValidClaims(const RaiktorSurrenderClaimsBaseV1 &claims) noexcept {
  if (!claims.target_order_stable || !claims.claim_rows_stable ||
      claims.declared_title_disposition != "unchanged" ||
      claims.claim_disposition != "remove_declared_target_claims" ||
      claims.target_title_ids.empty() ||
      claims.target_title_ids.size() != claims.claims.size()) {
    return false;
  }
  std::vector<std::int32_t> seen;
  seen.reserve(claims.target_title_ids.size());
  for (std::size_t index = 0; index < claims.claims.size(); ++index) {
    const auto title_id = claims.target_title_ids[index];
    const auto &claim = claims.claims[index];
    if (title_id <= 0 || claim.title_id != title_id ||
        std::find(seen.begin(), seen.end(), title_id) != seen.end()) {
      return false;
    }
    seen.push_back(title_id);
    if (!claim.present) {
      if (claim.strong || claim.implicit || claim.state != "absent") {
        return false;
      }
      continue;
    }
    const std::string_view expected_state =
        claim.strong
            ? (claim.implicit ? "strong_implicit" : "strong_explicit")
            : (claim.implicit ? "weak_implicit" : "weak_explicit");
    if (claim.state != expected_state) {
      return false;
    }
  }
  return true;
}

template <typename Observation>
bool CommonObservationIdentityMatches(
    const Observation &observation,
    const RaiktorSurrenderSameFrameV1 &frame) noexcept {
  return observation.war_id == frame.war_id &&
         observation.date_raw == frame.date_raw &&
         observation.active_casus_belli_database_index ==
             frame.active_casus_belli_database_index &&
         observation.active_casus_belli_key == "raiktor_claim_cb" &&
         observation.primary_attacker_character_id ==
             frame.primary_attacker_character_id &&
         observation.primary_defender_character_id ==
             frame.primary_defender_character_id &&
         observation.claimant_character_id == frame.claimant_character_id;
}

bool ValidGold(const RaiktorSurrenderGoldObservation &gold,
               const RaiktorSurrenderSameFrameV1 &frame) noexcept {
  return CommonObservationIdentityMatches(gold, frame) &&
         gold.exact_primary_transfer_observed && gold.same_frame_stable &&
         gold.attacker_current_gold.character_id ==
             frame.primary_attacker_character_id &&
         gold.defender_current_gold.character_id ==
             frame.primary_defender_character_id &&
         gold.attacker_authoritative_monthly_gold_income.character_id ==
             frame.primary_attacker_character_id &&
         gold.defender_authoritative_monthly_gold_income.character_id ==
             frame.primary_defender_character_id &&
         gold.actual_transfer.from_character_id ==
             frame.primary_attacker_character_id &&
         gold.actual_transfer.to_character_id ==
             frame.primary_defender_character_id &&
         ValidFixedPoint(gold.attacker_current_gold.value) &&
         ValidFixedPoint(gold.defender_current_gold.value) &&
         ValidFixedPoint(
             gold.attacker_authoritative_monthly_gold_income.value) &&
         ValidFixedPoint(
             gold.defender_authoritative_monthly_gold_income.value) &&
         ValidFixedPoint(gold.actual_transfer.value) &&
         gold.actual_transfer.value.raw >= 0;
}

bool ValidPrestige(const RaiktorSurrenderPrestigeObservation &prestige,
                   const RaiktorSurrenderSameFrameV1 &frame) noexcept {
  if (!CommonObservationIdentityMatches(prestige, frame) ||
      !prestige.exact_factor_and_attacker_delta_observed ||
      !prestige.same_frame_stable ||
      prestige.attacker_current_prestige.character_id !=
          frame.primary_attacker_character_id ||
      prestige.attacker_prestige_delta.character_id !=
          frame.primary_attacker_character_id ||
      !ValidFixedPoint(prestige.attacker_current_prestige.value) ||
      !ValidFixedPoint(prestige.cb_prestige_factor) ||
      !ValidFixedPoint(prestige.attacker_prestige_delta.value) ||
      prestige.cb_prestige_factor.raw < 0 ||
      prestige.cb_prestige_factor.raw >
          (std::numeric_limits<std::int64_t>::max)() / 10) {
    return false;
  }
  const auto uncapped_loss = prestige.cb_prestige_factor.raw * 10;
  const auto expected_delta =
      -std::min(uncapped_loss, kPrestigeLossCapRaw);
  return prestige.attacker_prestige_delta.value.raw == expected_delta;
}

bool ValidPrisoners(
    const RaiktorSurrenderPrisonerReleaseObservation &prisoners,
    const RaiktorSurrenderSameFrameV1 &frame) noexcept {
  if (!CommonObservationIdentityMatches(prisoners, frame) ||
      !prisoners.full_participant_scan ||
      !prisoners.primary_and_first_three_successors_scanned ||
      !prisoners.same_frame_stable ||
      !UniqueFullIds(prisoners.attacker_participant_ids, true) ||
      !UniqueFullIds(prisoners.defender_participant_ids, true) ||
      !UniqueFullIds(prisoners.attacker_release_candidate_ids, true) ||
      !UniqueFullIds(prisoners.defender_release_candidate_ids, true) ||
      prisoners.attacker_release_candidate_ids.front() !=
          frame.primary_attacker_character_id ||
      prisoners.defender_release_candidate_ids.front() !=
          frame.primary_defender_character_id ||
      !Contains(prisoners.attacker_participant_ids,
                frame.primary_attacker_character_id) ||
      !Contains(prisoners.defender_participant_ids,
                frame.primary_defender_character_id)) {
    return false;
  }
  for (const auto attacker : prisoners.attacker_participant_ids) {
    if (Contains(prisoners.defender_participant_ids, attacker)) {
      return false;
    }
  }
  for (const auto attacker : prisoners.attacker_release_candidate_ids) {
    if (Contains(prisoners.defender_release_candidate_ids, attacker)) {
      return false;
    }
  }

  std::vector<std::pair<std::int32_t, std::int32_t>> seen_pairs;
  seen_pairs.reserve(prisoners.release_pairs.size());
  for (const auto &pair : prisoners.release_pairs) {
    const bool attacker_jails_defender =
        Contains(prisoners.attacker_participant_ids,
                 pair.jailer_character_id) &&
        Contains(prisoners.defender_release_candidate_ids,
                 pair.prisoner_character_id);
    const bool defender_jails_attacker =
        Contains(prisoners.defender_participant_ids,
                 pair.jailer_character_id) &&
        Contains(prisoners.attacker_release_candidate_ids,
                 pair.prisoner_character_id);
    const auto identity =
        std::pair{pair.jailer_character_id, pair.prisoner_character_id};
    if (!ValidFullId(pair.jailer_character_id) ||
        !ValidFullId(pair.prisoner_character_id) ||
        pair.jailer_character_id == pair.prisoner_character_id ||
        pair.reason != "opposite_primary_or_first_three_successors" ||
        attacker_jails_defender == defender_jails_attacker ||
        std::find(seen_pairs.begin(), seen_pairs.end(), identity) !=
            seen_pairs.end()) {
      return false;
    }
    seen_pairs.push_back(identity);
  }
  return true;
}

bool ValidFavor(const RaiktorSurrenderFavorHookObservation &favor,
                const RaiktorSurrenderSameFrameV1 &frame) noexcept {
  if (!CommonObservationIdentityMatches(favor, frame) ||
      !favor.same_frame_stable ||
      favor.claimant_distinct_from_attacker !=
          (frame.claimant_character_id !=
           frame.primary_attacker_character_id)) {
    return false;
  }
  if (!favor.claimant_distinct_from_attacker) {
    return !favor.original_visible_root_traversed &&
           !favor.conditional_favor_hook_applies;
  }
  return favor.original_visible_root_traversed;
}

bool ValidTruce(const RaiktorSurrenderTruceObservationV1 &truce,
                const RaiktorSurrenderSameFrameV1 &frame) noexcept {
  const auto &native_frame = truce.frame;
  return truce.status == RaiktorSurrenderTruceStatusV1::available &&
         truce.failure == RaiktorSurrenderTruceFailureV1::none &&
         native_frame.snapshot_revision == frame.snapshot_revision &&
         native_frame.native_revision == frame.native_revision &&
         native_frame.date_raw == frame.date_raw && native_frame.paused &&
         native_frame.war_id == frame.war_id &&
         native_frame.active_casus_belli_database_index ==
             frame.active_casus_belli_database_index &&
         native_frame.exact_raiktor_claim_cb &&
         native_frame.primary_attacker_character_id ==
             frame.primary_attacker_character_id &&
         native_frame.primary_defender_character_id ==
             frame.primary_defender_character_id &&
         native_frame.claimant_character_id == frame.claimant_character_id &&
         native_frame.war != nullptr &&
         native_frame.active_casus_belli != nullptr &&
         native_frame.attacker_defeat_root != nullptr &&
         truce.owner_character_id == frame.primary_attacker_character_id &&
         truce.toward_character_id == frame.primary_defender_character_id &&
         truce.evaluated_days >= 0 && truce.pointer_shape_verified &&
         truce.evaluator_double_read_stable && truce.same_frame_stable &&
         !truce.expiry_observable;
}

bool CheckedAdd(std::int64_t value, std::int64_t &sum) noexcept {
  if (value < 0 ||
      sum > (std::numeric_limits<std::int64_t>::max)() - value) {
    return false;
  }
  sum += value;
  return true;
}

bool ValidWarBound(
    const RaiktorWarBoundRegimentObservationV1 &war_bound,
    const RaiktorSurrenderSameFrameV1 &frame) noexcept {
  const auto &active = war_bound.active_frame;
  const auto &readiness = war_bound.readiness;
  if (war_bound.status != RaiktorWarBoundRegimentStatusV1::
                              generic_war_bound_visible_source_unattributed ||
      war_bound.failure != RaiktorWarBoundRegimentFailureV1::none ||
      active.snapshot_revision != frame.snapshot_revision ||
      active.native_revision != frame.native_revision ||
      active.date_raw != frame.date_raw || !active.paused ||
      active.war_id != frame.war_id ||
      active.active_casus_belli_database_index !=
          frame.active_casus_belli_database_index ||
      !active.exact_raiktor_claim_cb ||
      active.primary_attacker_character_id !=
          frame.primary_attacker_character_id ||
      active.primary_defender_character_id !=
          frame.primary_defender_character_id ||
      war_bound.owner_character_id !=
          frame.primary_attacker_character_id ||
      war_bound.war_id != frame.war_id ||
      war_bound.authored_spawn_army_count !=
          kRaiktorAuthoredSpawnArmyCount ||
      war_bound.authored_soldiers_per_army !=
          kRaiktorAuthoredSoldiersPerArmy ||
      war_bound.authored_total_soldiers !=
          kRaiktorAuthoredTotalSoldiers ||
      war_bound.observed_current_soldiers < 0 ||
      war_bound.observed_pre_soldiers != -1 ||
      war_bound.proven_soldiers_lost != -1 ||
      war_bound.regiments.empty() ||
      !readiness.exact_raiktor_war_context_ready ||
      !readiness.generic_war_bound_identity_ready ||
      !readiness.current_soldiers_ready ||
      !readiness.independently_visible_value_ready ||
      readiness.source_specific_attribution_ready ||
      readiness.pre_soldiers_ready ||
      readiness.proven_soldier_loss_ready ||
      readiness.raiktor_source_specific_domain_ready) {
    return false;
  }

  const bool cleanup_ready = readiness.postwar_cleanup_ready;
  if (cleanup_ready) {
    const auto &postwar = war_bound.postwar_frame;
    if (postwar.snapshot_revision == 0 || postwar.native_revision == 0 ||
        !postwar.paused || postwar.frozen_war_id != frame.war_id ||
        !postwar.frozen_war_absent_from_active_wars ||
        (war_bound.cleanup_status !=
             WarBoundRegimentCleanupStatus::destroyed &&
         war_bound.cleanup_status !=
             WarBoundRegimentCleanupStatus::still_alive)) {
      return false;
    }
  } else if (war_bound.cleanup_status !=
                 WarBoundRegimentCleanupStatus::unavailable ||
             war_bound.postwar_frame != RaiktorWarBoundPostwarFrameV1{}) {
    return false;
  }

  std::vector<std::int32_t> persistent_ids;
  std::vector<std::int32_t> current_ids;
  persistent_ids.reserve(war_bound.regiments.size());
  current_ids.reserve(war_bound.regiments.size() *
                      kWarBoundRegimentCompositionRowCount);
  std::int64_t observed_total = 0;
  bool any_exact_regiment_still_alive = false;
  for (const auto &regiment : war_bound.regiments) {
    if (!ValidFullId(regiment.persistent_regiment_id) ||
        regiment.bound_war_id != frame.war_id ||
        regiment.war_keep_on_attacker_victory ||
        Contains(persistent_ids, regiment.persistent_regiment_id) ||
        regiment.current_soldiers < 0) {
      return false;
    }
    persistent_ids.push_back(regiment.persistent_regiment_id);
    if (cleanup_ready) {
      if (regiment.postwar_persistent_state !=
              FrozenWarBoundIdState::destroyed &&
          regiment.postwar_persistent_state !=
              FrozenWarBoundIdState::still_alive) {
        return false;
      }
      any_exact_regiment_still_alive |=
          regiment.postwar_persistent_state ==
          FrozenWarBoundIdState::still_alive;
    } else if (regiment.postwar_persistent_state !=
               FrozenWarBoundIdState::unavailable) {
      return false;
    }

    std::int64_t regiment_total = 0;
    for (std::size_t ordinal = 0;
         ordinal < kWarBoundRegimentCompositionRowCount; ++ordinal) {
      const auto &row = regiment.composition_rows[ordinal];
      if (row.composition_ordinal != static_cast<std::int32_t>(ordinal) ||
          (row.current_army_regiment_id == -1) !=
              (row.raised_carmy_id == -1)) {
        return false;
      }
      if (!cleanup_ready &&
          (row.current_army_regiment_state !=
               FrozenWarBoundIdState::not_present ||
           row.raised_carmy_state != FrozenWarBoundIdState::not_present ||
           row.frozen_carmy_roster_evidence !=
               FrozenWarBoundArmyRosterEvidence::not_present)) {
        return false;
      }
      if (row.current_army_regiment_id == -1) {
        if (row.current_soldiers != -1 ||
            (cleanup_ready &&
             (row.current_army_regiment_state !=
                  FrozenWarBoundIdState::not_present ||
              row.raised_carmy_state != FrozenWarBoundIdState::not_present ||
              row.frozen_carmy_roster_evidence !=
                  FrozenWarBoundArmyRosterEvidence::not_present))) {
          return false;
        }
        continue;
      }
      if (Contains(current_ids, row.current_army_regiment_id) ||
          row.current_soldiers < 0 ||
          !CheckedAdd(row.current_soldiers, regiment_total)) {
        return false;
      }
      current_ids.push_back(row.current_army_regiment_id);
      if (!cleanup_ready) {
        continue;
      }
      const auto current_state = row.current_army_regiment_state;
      const auto army_state = row.raised_carmy_state;
      const auto roster = row.frozen_carmy_roster_evidence;
      if ((current_state != FrozenWarBoundIdState::destroyed &&
           current_state != FrozenWarBoundIdState::still_alive) ||
          (army_state != FrozenWarBoundIdState::destroyed &&
           army_state != FrozenWarBoundIdState::still_alive) ||
          (army_state == FrozenWarBoundIdState::destroyed &&
           roster !=
               FrozenWarBoundArmyRosterEvidence::frozen_army_destroyed) ||
          (army_state == FrozenWarBoundIdState::still_alive &&
           roster != FrozenWarBoundArmyRosterEvidence::detached &&
           roster != FrozenWarBoundArmyRosterEvidence::still_attached) ||
          (current_state == FrozenWarBoundIdState::destroyed &&
           roster == FrozenWarBoundArmyRosterEvidence::still_attached)) {
        return false;
      }
      any_exact_regiment_still_alive |=
          current_state == FrozenWarBoundIdState::still_alive;
    }
    if (regiment_total != regiment.current_soldiers ||
        !CheckedAdd(regiment_total, observed_total)) {
      return false;
    }
  }
  if (observed_total != war_bound.observed_current_soldiers) {
    return false;
  }
  if (cleanup_ready) {
    const auto expected_status =
        any_exact_regiment_still_alive
            ? WarBoundRegimentCleanupStatus::still_alive
            : WarBoundRegimentCleanupStatus::destroyed;
    if (war_bound.cleanup_status != expected_status) {
      return false;
    }
  }
  return true;
}

bool Fail(RaiktorSurrenderSixDomainFailureV1 failure,
          RaiktorSurrenderSixDomainObservationV1 &output) noexcept {
  output = {};
  output.failure = failure;
  return false;
}

} // namespace

std::string_view RaiktorSurrenderSixDomainFailureReasonV1(
    RaiktorSurrenderSixDomainFailureV1 failure) noexcept {
  switch (failure) {
  case RaiktorSurrenderSixDomainFailureV1::none:
    return "none";
  case RaiktorSurrenderSixDomainFailureV1::invalid_frame:
    return "invalid_frame";
  case RaiktorSurrenderSixDomainFailureV1::invalid_claims_base:
    return "invalid_claims_base";
  case RaiktorSurrenderSixDomainFailureV1::invalid_gold_domain:
    return "invalid_gold_domain";
  case RaiktorSurrenderSixDomainFailureV1::invalid_prestige_domain:
    return "invalid_prestige_domain";
  case RaiktorSurrenderSixDomainFailureV1::invalid_prisoner_domain:
    return "invalid_prisoner_domain";
  case RaiktorSurrenderSixDomainFailureV1::invalid_favor_domain:
    return "invalid_favor_domain";
  case RaiktorSurrenderSixDomainFailureV1::invalid_truce_domain:
    return "invalid_truce_domain";
  case RaiktorSurrenderSixDomainFailureV1::invalid_war_bound_domain:
    return "invalid_war_bound_domain";
  }
  return "unknown";
}

bool BuildRaiktorSurrenderSixDomainObservationV1(
    const RaiktorSurrenderSixDomainInputV1 &input,
    RaiktorSurrenderSixDomainObservationV1 &output) noexcept {
  output = {};
  if (!ValidFrame(input.frame)) {
    return Fail(RaiktorSurrenderSixDomainFailureV1::invalid_frame, output);
  }

  RaiktorSurrenderSixDomainObservationV1 observed;
  observed.frame = input.frame;
  auto &readiness = observed.readiness;

  if (!input.claims_base.has_value()) {
    observed.missing_domains |=
        RaiktorSurrenderMissingDomainV1::claims_base;
  } else if (input.claims_base->frame != input.frame ||
             !ValidClaims(input.claims_base->observation)) {
    return Fail(RaiktorSurrenderSixDomainFailureV1::invalid_claims_base,
                output);
  } else {
    observed.claims_base = input.claims_base->observation;
    readiness.claims_base_ready = true;
  }

  if (!input.gold.has_value()) {
    observed.missing_domains |= RaiktorSurrenderMissingDomainV1::gold;
  } else if (input.gold->frame != input.frame ||
             !ValidGold(input.gold->observation, input.frame)) {
    return Fail(RaiktorSurrenderSixDomainFailureV1::invalid_gold_domain,
                output);
  } else {
    observed.gold = input.gold->observation;
    readiness.gold_ready = true;
  }

  if (!input.prestige.has_value()) {
    observed.missing_domains |= RaiktorSurrenderMissingDomainV1::prestige;
  } else if (input.prestige->frame != input.frame ||
             !ValidPrestige(input.prestige->observation, input.frame)) {
    return Fail(
        RaiktorSurrenderSixDomainFailureV1::invalid_prestige_domain,
        output);
  } else {
    observed.prestige = input.prestige->observation;
    readiness.prestige_ready = true;
  }

  if (!input.prisoner_release.has_value()) {
    observed.missing_domains |=
        RaiktorSurrenderMissingDomainV1::prisoner_release;
  } else if (input.prisoner_release->frame != input.frame ||
             !ValidPrisoners(input.prisoner_release->observation,
                             input.frame)) {
    return Fail(
        RaiktorSurrenderSixDomainFailureV1::invalid_prisoner_domain,
        output);
  } else {
    observed.prisoner_release = input.prisoner_release->observation;
    readiness.prisoner_release_ready = true;
  }

  if (!input.favor_hook.has_value()) {
    observed.missing_domains |= RaiktorSurrenderMissingDomainV1::favor_hook;
  } else if (input.favor_hook->frame != input.frame ||
             !ValidFavor(input.favor_hook->observation, input.frame)) {
    return Fail(RaiktorSurrenderSixDomainFailureV1::invalid_favor_domain,
                output);
  } else {
    observed.favor_hook = input.favor_hook->observation;
    readiness.favor_hook_ready = true;
  }

  if (!input.truce.has_value()) {
    observed.missing_domains |= RaiktorSurrenderMissingDomainV1::truce;
  } else if (input.truce->frame != input.frame ||
             !ValidTruce(input.truce->observation, input.frame)) {
    return Fail(RaiktorSurrenderSixDomainFailureV1::invalid_truce_domain,
                output);
  } else {
    observed.truce = input.truce->observation;
    readiness.truce_ready = true;
  }

  if (!input.generic_war_bound_current.has_value()) {
    observed.missing_domains |=
        RaiktorSurrenderMissingDomainV1::generic_war_bound_current;
  } else if (input.generic_war_bound_current->frame != input.frame ||
             !ValidWarBound(
                 input.generic_war_bound_current->observation,
                 input.frame)) {
    return Fail(
        RaiktorSurrenderSixDomainFailureV1::invalid_war_bound_domain,
        output);
  } else {
    observed.generic_war_bound_current =
        input.generic_war_bound_current->observation;
    readiness.generic_war_bound_current_ready = true;
    readiness.postwar_cleanup_ready =
        input.generic_war_bound_current->observation.readiness
            .postwar_cleanup_ready;
  }

  // "Six domains" counts gold, prestige, PoW, favor, truce and the honest
  // generic war-bound current observation. Claims are the base surrender
  // semantics. Postwar cleanup is a later frozen-ID proof, not a pre-action
  // same-frame prerequisite.
  readiness.six_dynamic_domains_ready =
      readiness.gold_ready && readiness.prestige_ready &&
      readiness.prisoner_release_ready && readiness.favor_hook_ready &&
      readiness.truce_ready &&
      readiness.generic_war_bound_current_ready;
  readiness.same_frame_stable =
      readiness.claims_base_ready && readiness.six_dynamic_domains_ready;
  readiness.action_terms_ready = readiness.same_frame_stable;

  // This aggregation deliberately never upgrades generic regiments to the
  // authored event source and never invents a pre-spawn baseline or loss.
  readiness.source_specific_war_bound_ready = false;
  readiness.pre_soldiers_ready = false;
  readiness.proven_soldier_loss_ready = false;

  // Exact options, native recipient validation and continue-vs-surrender
  // policy remain higher-level gates.
  readiness.automatic_surrender_ready = false;
  observed.failure = RaiktorSurrenderSixDomainFailureV1::none;
  observed.status = readiness.action_terms_ready
                        ? RaiktorSurrenderSixDomainStatusV1::complete
                        : RaiktorSurrenderSixDomainStatusV1::incomplete;
  output = std::move(observed);
  return true;
}

} // namespace xar::ck3_11906
