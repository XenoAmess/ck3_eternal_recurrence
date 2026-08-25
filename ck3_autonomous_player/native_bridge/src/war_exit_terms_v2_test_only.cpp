#include "xar_bridge/war_exit_terms_v2_test_only.hpp"

#include <array>
#include <charconv>
#include <limits>
#include <string>
#include <unordered_set>

namespace xar::game {
namespace {

constexpr std::array<std::string_view, 7> kBalanceResourceKinds{
    "gold", "prestige", "prestige_experience", "piety",
    "piety_experience", "legitimacy", "stress"};
constexpr std::array<std::string_view, 6> kDeltaResourceKinds{
    "prestige", "prestige_experience", "piety", "piety_experience",
    "legitimacy", "stress"};

bool PositiveId(std::int32_t value) noexcept { return value > 0; }

bool ValidFixed(const WarExitFixedPointV2TestOnly &value) noexcept {
  return value.scale == kWarExitTermsFixedPointScale;
}

template <std::size_t Size>
bool ValidResourceMatrix(const std::vector<WarExitResourceV2TestOnly> &rows,
                         std::int32_t attacker_id,
                         std::int32_t defender_id,
                         const std::array<std::string_view, Size> &kinds) {
  if (rows.size() != kinds.size() * 2U) {
    return false;
  }
  std::size_t index = 0;
  for (const auto character_id : {attacker_id, defender_id}) {
    for (const auto kind : kinds) {
      const auto &row = rows[index++];
      if (row.character_id != character_id || row.resource_kind != kind ||
          !ValidFixed(row.value)) {
        return false;
      }
    }
  }
  return true;
}

bool ValidTruce(const WarExitTruceV2TestOnly &truce,
                const WarTerminationExitTermsV2TestOnly &terms) noexcept {
  const auto expiry = static_cast<std::int64_t>(truce.current_date_raw) +
                      24LL * truce.evaluated_days;
  return truce.owner_character_id == terms.primary_attacker_character_id &&
         truce.toward_character_id == terms.primary_defender_character_id &&
         truce.evaluated_days >= 0 &&
         truce.current_date_raw == terms.date_raw &&
         expiry >= std::numeric_limits<std::int32_t>::min() &&
         expiry <= std::numeric_limits<std::int32_t>::max() &&
         truce.expiry_date_raw == expiry;
}

bool ValidPrisoners(
    const std::vector<WarExitPrisonerReleaseV2TestOnly> &rows) {
  if (rows.size() > 64U) {
    return false;
  }
  std::unordered_set<std::string> seen;
  for (const auto &row : rows) {
    if (!PositiveId(row.jailer_character_id) ||
        !PositiveId(row.prisoner_character_id) ||
        row.jailer_character_id == row.prisoner_character_id ||
        row.reason.empty() || row.reason.size() > 80U) {
      return false;
    }
    for (const unsigned char character : row.reason) {
      if (!((character >= 'a' && character <= 'z') ||
            (character >= '0' && character <= '9') || character == '_')) {
        return false;
      }
    }
    const auto identity = std::to_string(row.jailer_character_id) + ':' +
                          std::to_string(row.prisoner_character_id) + ':' +
                          row.reason;
    if (!seen.insert(identity).second) {
      return false;
    }
  }
  return true;
}

bool ValidOutcome(const WarExitOutcomeV2TestOnly &outcome,
                  const WarTerminationExitTermsV2TestOnly &terms,
                  bool white_peace, bool any_weak_claim) {
  const bool would_accept = outcome.native_validator_passed &&
                            outcome.decision_status_raw != 2;
  if (!outcome.complete || !outcome.native_validator_passed ||
      !ValidFixed(outcome.acceptance) ||
      outcome.decision_status_raw < 0 || outcome.decision_status_raw >= 3 ||
      outcome.would_accept_now != would_accept ||
      outcome.declared_title_disposition != "unchanged" ||
      !ValidFixed(outcome.cb_prestige_factor) ||
      outcome.cb_prestige_factor.raw < 0 ||
      !ValidResourceMatrix(outcome.primary_resource_deltas,
                           terms.primary_attacker_character_id,
                           terms.primary_defender_character_id,
                           kDeltaResourceKinds) ||
      !ValidTruce(outcome.truce, terms) ||
      !ValidPrisoners(outcome.prisoner_releases)) {
    return false;
  }
  if (white_peace) {
    const auto expected = any_weak_claim
                              ? "retain_and_strengthen_weak"
                              : "retain_no_strength_change_already_strong";
    return outcome.claim_disposition == expected &&
           outcome.primary_gold_transfers.empty();
  }
  if (outcome.claim_disposition != "remove_declared_target_claims" ||
      outcome.primary_gold_transfers.size() != 1U) {
    return false;
  }
  const auto &gold = outcome.primary_gold_transfers.front();
  return gold.from_character_id == terms.primary_attacker_character_id &&
         gold.to_character_id == terms.primary_defender_character_id &&
         ValidFixed(gold.value) && gold.value.raw >= 0;
}

bool Valid(const WarTerminationExitTermsV2TestOnly &terms) {
  if (!PositiveId(terms.war_id) || terms.casus_belli_database_index < 0 ||
      terms.casus_belli_key != "claim_cb" ||
      !PositiveId(terms.primary_attacker_character_id) ||
      !PositiveId(terms.primary_defender_character_id) ||
      terms.primary_attacker_character_id ==
          terms.primary_defender_character_id ||
      !PositiveId(terms.claimant_character_id) ||
      terms.target_title_ids.empty() ||
      terms.target_title_ids.size() != terms.claims.size() ||
      terms.target_title_ids.size() > 4096U || !terms.same_frame_stable ||
      !terms.claim_temporary_lifecycle_verified || !terms.exit_terms_ready ||
      !ValidResourceMatrix(terms.primary_resource_balances,
                           terms.primary_attacker_character_id,
                           terms.primary_defender_character_id,
                           kBalanceResourceKinds) ||
      terms.primary_monthly_gold_income.size() != 2U) {
    return false;
  }
  for (std::size_t index = 0;
       index < terms.primary_monthly_gold_income.size(); ++index) {
    const auto expected_id = index == 0
                                 ? terms.primary_attacker_character_id
                                 : terms.primary_defender_character_id;
    const auto &row = terms.primary_monthly_gold_income[index];
    if (row.character_id != expected_id || !ValidFixed(row.value)) {
      return false;
    }
  }
  std::unordered_set<std::int32_t> title_ids;
  bool any_weak_claim = false;
  for (std::size_t index = 0; index < terms.claims.size(); ++index) {
    const auto &claim = terms.claims[index];
    if (!PositiveId(terms.target_title_ids[index]) ||
        !title_ids.insert(terms.target_title_ids[index]).second ||
        claim.title_id != terms.target_title_ids[index] || !claim.present) {
      return false;
    }
    const auto expected_state =
        std::string(claim.strong ? "strong_" : "weak_") +
        (claim.implicit ? "implicit" : "explicit");
    if (claim.state != expected_state) {
      return false;
    }
    any_weak_claim = any_weak_claim || !claim.strong;
  }
  return ValidOutcome(terms.white_peace, terms, true, any_weak_claim) &&
         ValidOutcome(terms.attacker_defeat, terms, false, any_weak_claim) &&
         terms.white_peace.cb_prestige_factor.raw ==
             terms.attacker_defeat.cb_prestige_factor.raw;
}

void AppendSigned(std::string &output, std::int64_t value) {
  std::array<char, 32> buffer{};
  const auto conversion =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (conversion.ec == std::errc{}) {
    output.append(buffer.data(), conversion.ptr);
  }
}

void AppendString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output += '"';
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      output += '\\';
      output += static_cast<char>(character);
    } else if (character < 0x20U) {
      output += "\\u00";
      output += hex[(character >> 4U) & 0x0FU];
      output += hex[character & 0x0FU];
    } else {
      output += static_cast<char>(character);
    }
  }
  output += '"';
}

void AppendFixed(std::string &output,
                 const WarExitFixedPointV2TestOnly &value) {
  output += "{\"raw\":";
  AppendSigned(output, value.raw);
  output += ",\"scale\":";
  AppendSigned(output, value.scale);
  output += '}';
}

void AppendResources(std::string &output,
                     const std::vector<WarExitResourceV2TestOnly> &rows) {
  output += "{\"values\":[";
  for (std::size_t index = 0; index < rows.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &row = rows[index];
    output += "{\"character_id\":";
    AppendSigned(output, row.character_id);
    output += ",\"resource_kind\":";
    AppendString(output, row.resource_kind);
    output += ",\"raw\":";
    AppendSigned(output, row.value.raw);
    output += ",\"scale\":";
    AppendSigned(output, row.value.scale);
    output += '}';
  }
  output += "]}";
}

void AppendCharacterFixed(
    std::string &output,
    const std::vector<WarExitCharacterFixedPointV2TestOnly> &rows) {
  output += "{\"values\":[";
  for (std::size_t index = 0; index < rows.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &row = rows[index];
    output += "{\"character_id\":";
    AppendSigned(output, row.character_id);
    output += ",\"raw\":";
    AppendSigned(output, row.value.raw);
    output += ",\"scale\":";
    AppendSigned(output, row.value.scale);
    output += '}';
  }
  output += "]}";
}

void AppendGold(std::string &output,
                const std::vector<WarExitGoldTransferV2TestOnly> &rows) {
  output += "{\"values\":[";
  for (std::size_t index = 0; index < rows.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &row = rows[index];
    output += "{\"from_character_id\":";
    AppendSigned(output, row.from_character_id);
    output += ",\"to_character_id\":";
    AppendSigned(output, row.to_character_id);
    output += ",\"raw\":";
    AppendSigned(output, row.value.raw);
    output += ",\"scale\":";
    AppendSigned(output, row.value.scale);
    output += '}';
  }
  output += "]}";
}

void AppendTruce(std::string &output, const WarExitTruceV2TestOnly &truce) {
  output += "{\"owner_character_id\":";
  AppendSigned(output, truce.owner_character_id);
  output += ",\"toward_character_id\":";
  AppendSigned(output, truce.toward_character_id);
  output += ",\"evaluated_days\":";
  AppendSigned(output, truce.evaluated_days);
  output += ",\"current_date_raw\":";
  AppendSigned(output, truce.current_date_raw);
  output += ",\"expiry_date_raw\":";
  AppendSigned(output, truce.expiry_date_raw);
  output += '}';
}

void AppendPrisoners(
    std::string &output,
    const std::vector<WarExitPrisonerReleaseV2TestOnly> &rows) {
  output += "{\"values\":[";
  for (std::size_t index = 0; index < rows.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &row = rows[index];
    output += "{\"jailer_character_id\":";
    AppendSigned(output, row.jailer_character_id);
    output += ",\"prisoner_character_id\":";
    AppendSigned(output, row.prisoner_character_id);
    output += ",\"reason\":";
    AppendString(output, row.reason);
    output += '}';
  }
  output += "]}";
}

void AppendOutcome(std::string &output,
                   const WarExitOutcomeV2TestOnly &outcome) {
  output += "{\"claim_disposition\":{\"declared_title_disposition\":";
  AppendString(output, outcome.declared_title_disposition);
  output += ",\"claim_disposition\":";
  AppendString(output, outcome.claim_disposition);
  output += "},\"recipient_response\":{\"native_validator_passed\":";
  output += outcome.native_validator_passed ? "true" : "false";
  output += ",\"acceptance_raw\":";
  AppendSigned(output, outcome.acceptance.raw);
  output += ",\"acceptance_scale\":";
  AppendSigned(output, outcome.acceptance.scale);
  output += ",\"decision_status_raw\":";
  AppendSigned(output, outcome.decision_status_raw);
  output += ",\"would_accept_now\":";
  output += outcome.would_accept_now ? "true" : "false";
  output += ",\"auto_accept\":";
  output += outcome.auto_accept ? "true" : "false";
  output += "},\"cb_prestige_factor\":";
  AppendFixed(output, outcome.cb_prestige_factor);
  output += ",\"primary_gold_transfers\":";
  AppendGold(output, outcome.primary_gold_transfers);
  output += ",\"primary_resource_deltas\":";
  AppendResources(output, outcome.primary_resource_deltas);
  output += ",\"truce\":";
  AppendTruce(output, outcome.truce);
  output += ",\"prisoner_releases\":";
  AppendPrisoners(output, outcome.prisoner_releases);
  output += ",\"complete\":true}";
}

} // namespace

std::optional<std::string> SerializeWarTerminationExitTermsV2TestOnly(
    const WarTerminationExitTermsV2TestOnly &terms) {
  if (!Valid(terms)) {
    return std::nullopt;
  }
  std::string output =
      "{\"schema_version\":2,\"status\":\"available\",\"war_id\":";
  AppendSigned(output, terms.war_id);
  output += ",\"date_raw\":";
  AppendSigned(output, terms.date_raw);
  output += ",\"casus_belli\":{\"database_index\":";
  AppendSigned(output, terms.casus_belli_database_index);
  output += ",\"canonical_key\":";
  AppendString(output, terms.casus_belli_key);
  output +=
      "},\"supported_slice\":\"claim_cb_exit_terms_v2\","
      "\"player_side\":\"attacker\",\"primary_attacker_character_id\":";
  AppendSigned(output, terms.primary_attacker_character_id);
  output += ",\"primary_defender_character_id\":";
  AppendSigned(output, terms.primary_defender_character_id);
  output += ",\"claimant_character_id\":";
  AppendSigned(output, terms.claimant_character_id);
  output += ",\"target_title_ids\":[";
  for (std::size_t index = 0; index < terms.target_title_ids.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    AppendSigned(output, terms.target_title_ids[index]);
  }
  output += "],\"claims\":[";
  for (std::size_t index = 0; index < terms.claims.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &claim = terms.claims[index];
    output += "{\"title_id\":";
    AppendSigned(output, claim.title_id);
    output += ",\"present\":true,\"strong\":";
    output += claim.strong ? "true" : "false";
    output += ",\"implicit\":";
    output += claim.implicit ? "true" : "false";
    output += ",\"state\":";
    AppendString(output, claim.state);
    output += '}';
  }
  output += "],\"primary_resource_balances\":";
  AppendResources(output, terms.primary_resource_balances);
  output += ",\"primary_monthly_gold_income\":";
  AppendCharacterFixed(output, terms.primary_monthly_gold_income);
  output += ",\"outcomes\":{\"white_peace\":";
  AppendOutcome(output, terms.white_peace);
  output += ",\"attacker_defeat\":";
  AppendOutcome(output, terms.attacker_defeat);
  output +=
      "},\"readiness\":{\"same_frame_stable\":true,"
      "\"claim_temporary_lifecycle_verified\":true,"
      "\"white_peace_complete\":true,"
      "\"attacker_defeat_complete\":true,\"exit_terms_ready\":true},"
      "\"provenance\":{\"game_version\":\"1.19.0.6\","
      "\"executable_sha256\":"
      "\"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86\","
      "\"claim_script_sha256\":"
      "\"D9AA37BDC45F81B4F6185B2697A3EBD09404084EA0D3CF77BBE3C1D2C962E8B1\","
      "\"war_effects_sha256\":"
      "\"A936E09F448EF715580A918165EAB89A9368AD2D3014E425C998CD9D4F0E8D7D\","
      "\"war_values_sha256\":"
      "\"ED1CDB6E8BC887CF1FFFE010F1E9CA642DFD6DAF241E81F23E6B4736F7AFDF3B\","
      "\"ep3_effects_sha256\":"
      "\"D2F5FE80E7BC000A749642CD26BDE1626DBEA7409C39314B8583547AE43DB43D\","
      "\"native_contract_sha256\":\"";
  output += kWarExitTermsV2ContractSha256;
  output += "\"}}";
  return output;
}

} // namespace xar::game
