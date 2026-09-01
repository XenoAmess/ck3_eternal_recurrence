#include "xar_bridge/raiktor_surrender_six_domain_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <iostream>
#include <string_view>
#include <vector>

namespace {

using namespace xar::ck3_11906;

constexpr std::int32_t kWarId = 50'331'699;
constexpr std::int32_t kAttackerId = 29'829;
constexpr std::int32_t kDefenderId = 17'116;
constexpr std::int32_t kClaimantId = 41'001;
int g_war_identity = 0;
int g_cb_identity = 0;
int g_root_identity = 0;

RaiktorSurrenderSameFrameV1 Frame() {
  return {
      91,
      7,
      53'175'816,
      true,
      kWarId,
      411,
      true,
      kAttackerId,
      kDefenderId,
      kClaimantId,
  };
}

RaiktorSurrenderClaimsBaseV1 Claims() {
  RaiktorSurrenderClaimsBaseV1 value;
  value.target_title_ids = {1'800};
  value.claims = {{1'800, true, true, false, "strong_explicit"}};
  value.declared_title_disposition = "unchanged";
  value.claim_disposition = "remove_declared_target_claims";
  value.target_order_stable = true;
  value.claim_rows_stable = true;
  return value;
}

template <typename Observation>
void BindCommon(Observation &value) {
  value.war_id = kWarId;
  value.date_raw = 53'175'816;
  value.active_casus_belli_database_index = 411;
  value.active_casus_belli_key = "raiktor_claim_cb";
  value.primary_attacker_character_id = kAttackerId;
  value.primary_defender_character_id = kDefenderId;
  value.claimant_character_id = kClaimantId;
}

RaiktorSurrenderGoldObservation Gold() {
  RaiktorSurrenderGoldObservation value;
  BindCommon(value);
  value.attacker_current_gold = {kAttackerId, {35'000'000, 100'000}};
  value.defender_current_gold = {kDefenderId, {80'000'000, 100'000}};
  value.attacker_authoritative_monthly_gold_income = {
      kAttackerId, {500'001, 100'000}};
  value.defender_authoritative_monthly_gold_income = {
      kDefenderId, {800'000, 100'000}};
  value.actual_transfer = {
      kAttackerId, kDefenderId, {15'000'000, 100'000}};
  value.exact_primary_transfer_observed = true;
  value.same_frame_stable = true;
  return value;
}

RaiktorSurrenderPrestigeObservation Prestige() {
  RaiktorSurrenderPrestigeObservation value;
  BindCommon(value);
  value.attacker_current_prestige = {
      kAttackerId, {12'345'678, 100'000}};
  value.cb_prestige_factor = {700'000, 100'000};
  value.attacker_prestige_delta = {
      kAttackerId, {-7'000'000, 100'000}};
  value.exact_factor_and_attacker_delta_observed = true;
  value.same_frame_stable = true;
  return value;
}

RaiktorSurrenderPrisonerReleaseObservation Prisoners() {
  RaiktorSurrenderPrisonerReleaseObservation value;
  BindCommon(value);
  value.attacker_participant_ids = {kAttackerId, 30'001};
  value.defender_participant_ids = {kDefenderId};
  value.attacker_release_candidate_ids = {kAttackerId, 30'003};
  value.defender_release_candidate_ids = {kDefenderId};
  value.release_pairs = {
      {kDefenderId, 30'003,
       "opposite_primary_or_first_three_successors"}};
  value.full_participant_scan = true;
  value.primary_and_first_three_successors_scanned = true;
  value.same_frame_stable = true;
  return value;
}

RaiktorSurrenderFavorHookObservation Favor() {
  RaiktorSurrenderFavorHookObservation value;
  BindCommon(value);
  value.claimant_distinct_from_attacker = true;
  value.original_visible_root_traversed = true;
  value.conditional_favor_hook_applies = true;
  value.same_frame_stable = true;
  return value;
}

RaiktorSurrenderTruceObservationV1 Truce() {
  RaiktorSurrenderTruceObservationV1 value;
  value.status = RaiktorSurrenderTruceStatusV1::available;
  value.failure = RaiktorSurrenderTruceFailureV1::none;
  value.frame.snapshot_revision = 91;
  value.frame.native_revision = 7;
  value.frame.date_raw = 53'175'816;
  value.frame.paused = true;
  value.frame.war_id = kWarId;
  value.frame.active_casus_belli_database_index = 411;
  value.frame.exact_raiktor_claim_cb = true;
  value.frame.primary_attacker_character_id = kAttackerId;
  value.frame.primary_defender_character_id = kDefenderId;
  value.frame.claimant_character_id = kClaimantId;
  value.frame.war = &g_war_identity;
  value.frame.active_casus_belli = &g_cb_identity;
  value.frame.attacker_defeat_root = &g_root_identity;
  value.owner_character_id = kAttackerId;
  value.toward_character_id = kDefenderId;
  value.evaluated_days = 1'825;
  value.pointer_shape_verified = true;
  value.evaluator_double_read_stable = true;
  value.same_frame_stable = true;
  value.expiry_observable = false;
  return value;
}

RaiktorWarBoundRegimentObservationV1 WarBound() {
  RaiktorWarBoundRegimentObservationV1 value;
  value.status = RaiktorWarBoundRegimentStatusV1::
      generic_war_bound_visible_source_unattributed;
  value.failure = RaiktorWarBoundRegimentFailureV1::none;
  value.active_frame = {
      91,
      7,
      53'175'816,
      true,
      kWarId,
      411,
      true,
      kAttackerId,
      kDefenderId,
  };
  value.owner_character_id = kAttackerId;
  value.war_id = kWarId;
  value.observed_current_soldiers = 180;
  value.readiness.exact_raiktor_war_context_ready = true;
  value.readiness.generic_war_bound_identity_ready = true;
  value.readiness.current_soldiers_ready = true;
  value.readiness.independently_visible_value_ready = true;

  RaiktorWarBoundPersistentRegimentV1 first;
  first.persistent_regiment_id = 0x01000010;
  first.bound_war_id = kWarId;
  first.current_soldiers = 140;
  RaiktorWarBoundPersistentRegimentV1 second;
  second.persistent_regiment_id = 0x01000011;
  second.bound_war_id = kWarId;
  second.current_soldiers = 40;
  for (std::size_t ordinal = 0;
       ordinal < kWarBoundRegimentCompositionRowCount; ++ordinal) {
    first.composition_rows[ordinal].composition_ordinal =
        static_cast<std::int32_t>(ordinal);
    second.composition_rows[ordinal].composition_ordinal =
        static_cast<std::int32_t>(ordinal);
  }
  first.composition_rows[0].current_army_regiment_id = 0x02000020;
  first.composition_rows[0].raised_carmy_id = 0x03000030;
  first.composition_rows[0].current_soldiers = 80;
  first.composition_rows[3].current_army_regiment_id = 0x02000021;
  first.composition_rows[3].raised_carmy_id = 0x03000030;
  first.composition_rows[3].current_soldiers = 60;
  second.composition_rows[6].current_army_regiment_id = 0x02000022;
  second.composition_rows[6].raised_carmy_id = 0x03000031;
  second.composition_rows[6].current_soldiers = 40;
  value.regiments = {first, second};
  return value;
}

RaiktorWarBoundRegimentObservationV1 DestroyedWarBound() {
  auto value = WarBound();
  value.postwar_frame = {96, 8, 53'175'816, true, kWarId, true};
  value.cleanup_status = WarBoundRegimentCleanupStatus::destroyed;
  value.readiness.postwar_cleanup_ready = true;
  for (auto &regiment : value.regiments) {
    regiment.postwar_persistent_state = FrozenWarBoundIdState::destroyed;
    for (auto &row : regiment.composition_rows) {
      if (row.current_army_regiment_id == -1) {
        continue;
      }
      row.current_army_regiment_state = FrozenWarBoundIdState::destroyed;
      row.raised_carmy_state = FrozenWarBoundIdState::destroyed;
      row.frozen_carmy_roster_evidence =
          FrozenWarBoundArmyRosterEvidence::frozen_army_destroyed;
    }
  }
  return value;
}

RaiktorSurrenderSixDomainInputV1 CompleteInput() {
  const auto frame = Frame();
  RaiktorSurrenderSixDomainInputV1 value;
  value.frame = frame;
  value.claims_base = RaiktorSurrenderClaimsDomainV1{frame, Claims()};
  value.gold = RaiktorSurrenderGoldDomainV1{frame, Gold()};
  value.prestige = RaiktorSurrenderPrestigeDomainV1{frame, Prestige()};
  value.prisoner_release =
      RaiktorSurrenderPrisonerDomainV1{frame, Prisoners()};
  value.favor_hook = RaiktorSurrenderFavorDomainV1{frame, Favor()};
  value.truce = RaiktorSurrenderTruceDomainV1{frame, Truce()};
  value.generic_war_bound_current =
      RaiktorSurrenderWarBoundDomainV1{frame, WarBound()};
  return value;
}

bool ExpectFailure(bool returned,
                   const RaiktorSurrenderSixDomainObservationV1 &value,
                   RaiktorSurrenderSixDomainFailureV1 expected,
                   std::string_view label) {
  if (returned ||
      value.status != RaiktorSurrenderSixDomainStatusV1::unavailable ||
      value.failure != expected) {
    std::cerr << label << ": expected "
              << RaiktorSurrenderSixDomainFailureReasonV1(expected)
              << ", got "
              << RaiktorSurrenderSixDomainFailureReasonV1(value.failure)
              << '\n';
    return false;
  }
  return true;
}

template <typename Mutate>
bool ExpectMissing(Mutate mutate, RaiktorSurrenderMissingDomainV1 missing,
                   bool six_dynamic_ready, std::string_view label) {
  auto input = CompleteInput();
  mutate(input);
  RaiktorSurrenderSixDomainObservationV1 value;
  if (!BuildRaiktorSurrenderSixDomainObservationV1(input, value) ||
      value.status != RaiktorSurrenderSixDomainStatusV1::incomplete ||
      value.failure != RaiktorSurrenderSixDomainFailureV1::none ||
      value.missing_domains != missing ||
      value.readiness.six_dynamic_domains_ready != six_dynamic_ready ||
      value.readiness.same_frame_stable ||
      value.readiness.action_terms_ready ||
      value.readiness.automatic_surrender_ready) {
    std::cerr << label << ": incomplete fail-closed contract failed\n";
    return false;
  }
  return true;
}

} // namespace

int main() {
  {
    RaiktorSurrenderSixDomainObservationV1 value;
    if (!BuildRaiktorSurrenderSixDomainObservationV1(CompleteInput(), value) ||
        value.status != RaiktorSurrenderSixDomainStatusV1::complete ||
        value.failure != RaiktorSurrenderSixDomainFailureV1::none ||
        value.missing_domains != RaiktorSurrenderMissingDomainV1::none ||
        !value.readiness.claims_base_ready ||
        !value.readiness.six_dynamic_domains_ready ||
        !value.readiness.same_frame_stable ||
        !value.readiness.action_terms_ready ||
        value.readiness.automatic_surrender_ready ||
        value.readiness.source_specific_war_bound_ready ||
        value.readiness.pre_soldiers_ready ||
        value.readiness.proven_soldier_loss_ready ||
        value.readiness.postwar_cleanup_ready ||
        !value.truce.has_value() || value.truce->expiry_observable ||
        !value.generic_war_bound_current.has_value() ||
        value.generic_war_bound_current->observed_pre_soldiers != -1 ||
        value.generic_war_bound_current->proven_soldiers_lost != -1) {
      std::cerr << "complete same-frame aggregation failed\n";
      return 1;
    }
  }

  if (!ExpectMissing(
          [](auto &value) { value.claims_base.reset(); },
          RaiktorSurrenderMissingDomainV1::claims_base, true,
          "missing claims base") ||
      !ExpectMissing(
          [](auto &value) { value.gold.reset(); },
          RaiktorSurrenderMissingDomainV1::gold, false, "missing gold") ||
      !ExpectMissing(
          [](auto &value) { value.prestige.reset(); },
          RaiktorSurrenderMissingDomainV1::prestige, false,
          "missing prestige") ||
      !ExpectMissing(
          [](auto &value) { value.prisoner_release.reset(); },
          RaiktorSurrenderMissingDomainV1::prisoner_release, false,
          "missing prisoners") ||
      !ExpectMissing(
          [](auto &value) { value.favor_hook.reset(); },
          RaiktorSurrenderMissingDomainV1::favor_hook, false,
          "missing favor") ||
      !ExpectMissing(
          [](auto &value) { value.truce.reset(); },
          RaiktorSurrenderMissingDomainV1::truce, false, "missing truce") ||
      !ExpectMissing(
          [](auto &value) { value.generic_war_bound_current.reset(); },
          RaiktorSurrenderMissingDomainV1::generic_war_bound_current, false,
          "missing generic war-bound")) {
    return 1;
  }

  {
    auto input = CompleteInput();
    ++input.gold->frame.snapshot_revision;
    RaiktorSurrenderSixDomainObservationV1 value;
    if (!ExpectFailure(
            BuildRaiktorSurrenderSixDomainObservationV1(input, value), value,
            RaiktorSurrenderSixDomainFailureV1::invalid_gold_domain,
            "gold cross-frame drift")) {
      return 1;
    }
  }
  {
    auto input = CompleteInput();
    input.claims_base->observation.claims[0].state = "weak_explicit";
    RaiktorSurrenderSixDomainObservationV1 value;
    if (!ExpectFailure(
            BuildRaiktorSurrenderSixDomainObservationV1(input, value), value,
            RaiktorSurrenderSixDomainFailureV1::invalid_claims_base,
            "claim state drift")) {
      return 1;
    }
  }
  {
    auto input = CompleteInput();
    input.prestige->observation.attacker_prestige_delta.value.raw =
        -6'999'999;
    RaiktorSurrenderSixDomainObservationV1 value;
    if (!ExpectFailure(
            BuildRaiktorSurrenderSixDomainObservationV1(input, value), value,
            RaiktorSurrenderSixDomainFailureV1::invalid_prestige_domain,
            "prestige formula drift")) {
      return 1;
    }
  }
  {
    auto input = CompleteInput();
    input.prisoner_release->observation.release_pairs[0]
        .jailer_character_id = kAttackerId;
    RaiktorSurrenderSixDomainObservationV1 value;
    if (!ExpectFailure(
            BuildRaiktorSurrenderSixDomainObservationV1(input, value), value,
            RaiktorSurrenderSixDomainFailureV1::invalid_prisoner_domain,
            "prisoner side drift")) {
      return 1;
    }
  }
  {
    auto input = CompleteInput();
    input.truce->observation.expiry_observable = true;
    RaiktorSurrenderSixDomainObservationV1 value;
    if (!ExpectFailure(
            BuildRaiktorSurrenderSixDomainObservationV1(input, value), value,
            RaiktorSurrenderSixDomainFailureV1::invalid_truce_domain,
            "invented truce expiry")) {
      return 1;
    }
  }
  {
    auto input = CompleteInput();
    auto &war_bound = input.generic_war_bound_current->observation;
    war_bound.readiness.source_specific_attribution_ready = true;
    war_bound.readiness.raiktor_source_specific_domain_ready = true;
    war_bound.observed_pre_soldiers = 3'000;
    war_bound.proven_soldiers_lost = 2'820;
    RaiktorSurrenderSixDomainObservationV1 value;
    if (!ExpectFailure(
            BuildRaiktorSurrenderSixDomainObservationV1(input, value), value,
            RaiktorSurrenderSixDomainFailureV1::invalid_war_bound_domain,
            "source and loss overclaim")) {
      return 1;
    }
  }
  {
    auto input = CompleteInput();
    input.generic_war_bound_current->observation = DestroyedWarBound();
    RaiktorSurrenderSixDomainObservationV1 value;
    if (!BuildRaiktorSurrenderSixDomainObservationV1(input, value) ||
        value.status != RaiktorSurrenderSixDomainStatusV1::complete ||
        !value.readiness.action_terms_ready ||
        !value.readiness.postwar_cleanup_ready ||
        value.readiness.source_specific_war_bound_ready ||
        value.readiness.proven_soldier_loss_ready ||
        !value.generic_war_bound_current.has_value() ||
        value.generic_war_bound_current->cleanup_status !=
            WarBoundRegimentCleanupStatus::destroyed) {
      std::cerr << "postwar frozen-ID cleanup attachment failed\n";
      return 1;
    }
  }
  return 0;
}
