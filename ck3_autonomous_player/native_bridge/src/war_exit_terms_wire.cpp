#include "xar_bridge/war_exit_terms_wire.hpp"

#include "xar_bridge/war_exit_terms_v2_test_only.hpp"

namespace xar::game {
namespace {

WarExitFixedPointV2TestOnly ConvertFixed(const FixedPointValue &value) {
  return {value.raw, value.scale};
}

WarExitResourceV2TestOnly ConvertResource(
    const WarExitResourceSnapshot &row) {
  return {row.character_id, row.resource_kind, ConvertFixed(row.value)};
}

WarExitOutcomeV2TestOnly ConvertOutcome(
    const WarExitOutcomeSnapshot &outcome) {
  WarExitOutcomeV2TestOnly converted{};
  converted.declared_title_disposition =
      outcome.claim_disposition.declared_title_disposition;
  converted.claim_disposition =
      outcome.claim_disposition.claim_disposition;
  converted.native_validator_passed =
      outcome.recipient_response.native_validator_passed;
  converted.acceptance = ConvertFixed(outcome.recipient_response.acceptance);
  converted.decision_status_raw =
      outcome.recipient_response.decision_status_raw;
  converted.would_accept_now =
      outcome.recipient_response.would_accept_now;
  converted.auto_accept = outcome.recipient_response.auto_accept;
  converted.cb_prestige_factor = ConvertFixed(outcome.cb_prestige_factor);
  converted.complete = outcome.complete;
  try {
    converted.primary_gold_transfers.reserve(
        outcome.primary_gold_transfers.size());
    for (const auto &row : outcome.primary_gold_transfers) {
      converted.primary_gold_transfers.push_back(
          {row.from_character_id, row.to_character_id,
           ConvertFixed(row.value)});
    }
    converted.primary_resource_deltas.reserve(
        outcome.primary_resource_deltas.size());
    for (const auto &row : outcome.primary_resource_deltas) {
      converted.primary_resource_deltas.push_back(ConvertResource(row));
    }
    converted.prisoner_releases.reserve(outcome.prisoner_releases.size());
    for (const auto &row : outcome.prisoner_releases) {
      converted.prisoner_releases.push_back(
          {row.jailer_character_id, row.prisoner_character_id, row.reason});
    }
  } catch (...) {
    return {};
  }
  converted.truce = {
      outcome.truce.owner_character_id,
      outcome.truce.toward_character_id,
      outcome.truce.evaluated_days,
      outcome.truce.current_date_raw,
      outcome.truce.expiry_date_raw,
  };
  return converted;
}

} // namespace

std::optional<std::string> SerializeWarTerminationExitTermsV2(
    const WarTerminationExitTermsSnapshot &terms) {
  WarTerminationExitTermsV2TestOnly converted{};
  converted.war_id = terms.war_id;
  converted.date_raw = terms.date_raw;
  converted.casus_belli_database_index =
      terms.active_casus_belli_database_index;
  converted.casus_belli_key = terms.active_casus_belli_key;
  converted.primary_attacker_character_id =
      terms.primary_attacker_character_id;
  converted.primary_defender_character_id =
      terms.primary_defender_character_id;
  converted.claimant_character_id = terms.claimant_character_id;
  converted.same_frame_stable = terms.same_frame_stable;
  converted.claim_temporary_lifecycle_verified =
      terms.claim_temporary_lifecycle_verified;
  converted.exit_terms_ready = terms.exit_terms_ready;
  try {
    converted.target_title_ids = terms.target_title_ids;
    converted.claims.reserve(terms.claims.size());
    for (const auto &claim : terms.claims) {
      converted.claims.push_back({claim.title_id, claim.present, claim.strong,
                                  claim.implicit, claim.state});
    }
    converted.primary_resource_balances.reserve(
        terms.primary_resource_balances.size());
    for (const auto &row : terms.primary_resource_balances) {
      converted.primary_resource_balances.push_back(ConvertResource(row));
    }
    converted.primary_monthly_gold_income.reserve(
        terms.primary_monthly_gold_income.size());
    for (const auto &row : terms.primary_monthly_gold_income) {
      converted.primary_monthly_gold_income.push_back(
          {row.character_id, ConvertFixed(row.value)});
    }
  } catch (...) {
    return std::nullopt;
  }
  converted.white_peace = ConvertOutcome(terms.white_peace);
  converted.attacker_defeat = ConvertOutcome(terms.attacker_defeat);
  return SerializeWarTerminationExitTermsV2TestOnly(converted);
}

} // namespace xar::game
