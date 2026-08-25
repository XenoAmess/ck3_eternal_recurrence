#include "xar_bridge/war_exit_terms_v2_test_only.hpp"
#include "xar_bridge/war_exit_terms_wire.hpp"

#include <array>
#include <cctype>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <utility>

namespace {

int Fail(const char *message) {
  std::cerr << "FAIL: " << message << '\n';
  return 1;
}

std::string MinifyJsonWhitespace(std::string_view source) {
  std::string result;
  result.reserve(source.size());
  bool in_string = false;
  bool escaped = false;
  for (const char character : source) {
    if (in_string) {
      result += character;
      if (escaped) {
        escaped = false;
      } else if (character == '\\') {
        escaped = true;
      } else if (character == '"') {
        in_string = false;
      }
    } else if (character == '"') {
      in_string = true;
      result += character;
    } else if (!std::isspace(static_cast<unsigned char>(character))) {
      result += character;
    }
  }
  return result;
}

template <std::size_t Size>
std::vector<xar::game::WarExitResourceV2TestOnly>
ResourceRows(std::int32_t attacker_id, std::int32_t defender_id,
             const std::array<std::string_view, Size> &kinds,
             const std::array<std::int64_t, Size * 2U> &raws) {
  std::vector<xar::game::WarExitResourceV2TestOnly> rows;
  std::size_t index = 0;
  for (const auto character_id : {attacker_id, defender_id}) {
    for (const auto kind : kinds) {
      rows.push_back(
          {character_id, std::string(kind), {raws[index++], 100'000}});
    }
  }
  return rows;
}

xar::game::WarTerminationExitTermsV2TestOnly Fixture() {
  using namespace xar::game;
  constexpr std::int32_t attacker_id = 16'777'218;
  constexpr std::int32_t defender_id = 16'777'219;
  constexpr std::array<std::string_view, 7> balance_kinds{
      "gold", "prestige", "prestige_experience", "piety",
      "piety_experience", "legitimacy", "stress"};
  constexpr std::array<std::int64_t, 14> balance_raws{
      35'000'000,  12'000'000, 100'000'000, 5'000'000, 30'000'000,
      8'000'000,   4'200'000,   80'000'000, 45'000'000, 200'000'000,
      9'000'000,   60'000'000,  7'000'000,   8'700'000};
  constexpr std::array<std::string_view, 6> delta_kinds{
      "prestige", "prestige_experience", "piety", "piety_experience",
      "legitimacy", "stress"};
  constexpr std::array<std::int64_t, 12> white_peace_raws{
      -3'500'000, 0, 0, 0, 0, 3'400'000,
      0,          0, 0, 0, 0, 0};
  constexpr std::array<std::int64_t, 12> defeat_raws{
      -7'000'000, 0, 0, 0, 0, 0,
      7'000'000,  0, 0, 0, 5'000'000, 0};

  WarTerminationExitTermsV2TestOnly terms{};
  terms.war_id = 16'777'300;
  terms.date_raw = 42'424'224;
  terms.casus_belli_database_index = 3;
  terms.casus_belli_key = "claim_cb";
  terms.primary_attacker_character_id = attacker_id;
  terms.primary_defender_character_id = defender_id;
  terms.claimant_character_id = attacker_id;
  terms.target_title_ids = {16'777'221};
  terms.claims = {
      {16'777'221, true, false, false, "weak_explicit"}};
  terms.primary_resource_balances =
      ResourceRows(attacker_id, defender_id, balance_kinds, balance_raws);
  terms.primary_monthly_gold_income = {
      {attacker_id, {500'000, 100'000}},
      {defender_id, {800'000, 100'000}},
  };

  terms.white_peace.declared_title_disposition = "unchanged";
  terms.white_peace.claim_disposition = "retain_and_strengthen_weak";
  terms.white_peace.native_validator_passed = true;
  terms.white_peace.acceptance = {1'100'000, 100'000};
  terms.white_peace.decision_status_raw = 0;
  terms.white_peace.would_accept_now = true;
  terms.white_peace.auto_accept = false;
  terms.white_peace.cb_prestige_factor = {700'000, 100'000};
  terms.white_peace.primary_resource_deltas = ResourceRows(
      attacker_id, defender_id, delta_kinds, white_peace_raws);
  terms.white_peace.truce =
      {attacker_id, defender_id, 1'825, 42'424'224, 42'468'024};
  terms.white_peace.complete = true;

  terms.attacker_defeat.declared_title_disposition = "unchanged";
  terms.attacker_defeat.claim_disposition =
      "remove_declared_target_claims";
  terms.attacker_defeat.native_validator_passed = true;
  terms.attacker_defeat.acceptance = {86'000'000, 100'000};
  terms.attacker_defeat.decision_status_raw = 1;
  terms.attacker_defeat.would_accept_now = true;
  terms.attacker_defeat.auto_accept = true;
  terms.attacker_defeat.cb_prestige_factor = {700'000, 100'000};
  terms.attacker_defeat.primary_gold_transfers = {
      {attacker_id, defender_id, {15'000'000, 100'000}}};
  terms.attacker_defeat.primary_resource_deltas =
      ResourceRows(attacker_id, defender_id, delta_kinds, defeat_raws);
  terms.attacker_defeat.truce =
      {attacker_id, defender_id, 1'825, 42'424'224, 42'468'024};
  terms.attacker_defeat.complete = true;
  terms.same_frame_stable = true;
  terms.claim_temporary_lifecycle_verified = true;
  terms.exit_terms_ready = true;
  return terms;
}

xar::game::WarTerminationExitTermsSnapshot ProductionFixture() {
  using namespace xar::game;
  const auto source = Fixture();
  WarTerminationExitTermsSnapshot terms{};
  terms.war_id = source.war_id;
  terms.date_raw = source.date_raw;
  terms.active_casus_belli_database_index =
      source.casus_belli_database_index;
  terms.active_casus_belli_key = source.casus_belli_key;
  terms.primary_attacker_character_id =
      source.primary_attacker_character_id;
  terms.primary_defender_character_id =
      source.primary_defender_character_id;
  terms.claimant_character_id = source.claimant_character_id;
  terms.target_title_ids = source.target_title_ids;
  for (const auto &claim : source.claims) {
    terms.claims.push_back({claim.title_id, claim.present, claim.strong,
                            claim.implicit, claim.state});
  }
  for (const auto &row : source.primary_resource_balances) {
    terms.primary_resource_balances.push_back(
        {row.character_id, row.resource_kind,
         {row.value.raw, row.value.scale}});
  }
  for (const auto &row : source.primary_monthly_gold_income) {
    terms.primary_monthly_gold_income.push_back(
        {row.character_id, {row.value.raw, row.value.scale}});
  }
  const auto convert_outcome = [](const WarExitOutcomeV2TestOnly &input) {
    WarExitOutcomeSnapshot output{};
    output.claim_disposition = {input.declared_title_disposition,
                                input.claim_disposition};
    output.recipient_response = {
        input.native_validator_passed,
        {input.acceptance.raw, input.acceptance.scale},
        input.decision_status_raw,
        input.would_accept_now,
        input.auto_accept,
    };
    output.cb_prestige_factor = {input.cb_prestige_factor.raw,
                                 input.cb_prestige_factor.scale};
    for (const auto &row : input.primary_gold_transfers) {
      output.primary_gold_transfers.push_back(
          {row.from_character_id, row.to_character_id,
           {row.value.raw, row.value.scale}});
    }
    for (const auto &row : input.primary_resource_deltas) {
      output.primary_resource_deltas.push_back(
          {row.character_id, row.resource_kind,
           {row.value.raw, row.value.scale}});
    }
    output.truce = {
        input.truce.owner_character_id,
        input.truce.toward_character_id,
        input.truce.evaluated_days,
        input.truce.current_date_raw,
        input.truce.expiry_date_raw,
    };
    for (const auto &row : input.prisoner_releases) {
      output.prisoner_releases.push_back(
          {row.jailer_character_id, row.prisoner_character_id, row.reason});
    }
    output.complete = input.complete;
    return output;
  };
  terms.white_peace = convert_outcome(source.white_peace);
  terms.attacker_defeat = convert_outcome(source.attacker_defeat);
  terms.same_frame_stable = source.same_frame_stable;
  terms.claim_temporary_lifecycle_verified =
      source.claim_temporary_lifecycle_verified;
  terms.exit_terms_ready = source.exit_terms_ready;
  return terms;
}

} // namespace

int main(int argc, char **argv) {
  const auto serialized =
      xar::game::SerializeWarTerminationExitTermsV2TestOnly(Fixture());
  if (!serialized.has_value()) {
    return Fail("complete v2 test-only fixture was rejected");
  }
  if (serialized->find("game.command.query-war-termination-exit-terms") !=
          std::string::npos ||
      serialized->find("query-war-termination-exit-terms-v2-") !=
          std::string::npos ||
      serialized->find("\"status\":\"partial\"") != std::string::npos ||
      serialized->find(":null") != std::string::npos) {
    return Fail("test-only serializer advertised dispatch or emitted partials");
  }
  const auto production_serialized =
      xar::game::SerializeWarTerminationExitTermsV2(ProductionFixture());
  if (!production_serialized.has_value() ||
      production_serialized.value() != serialized.value()) {
    return Fail("production serializer drifted from the independent v2 wire");
  }
  auto production_incomplete = ProductionFixture();
  production_incomplete.exit_terms_ready = false;
  if (xar::game::SerializeWarTerminationExitTermsV2(production_incomplete)
          .has_value()) {
    return Fail("production serializer emitted an incomplete v2 union");
  }

  auto incomplete = Fixture();
  incomplete.primary_resource_balances.pop_back();
  if (xar::game::SerializeWarTerminationExitTermsV2TestOnly(incomplete)
          .has_value()) {
    return Fail("incomplete current balance matrix was serialized");
  }
  incomplete = Fixture();
  incomplete.primary_monthly_gold_income.pop_back();
  if (xar::game::SerializeWarTerminationExitTermsV2TestOnly(incomplete)
          .has_value()) {
    return Fail("incomplete monthly income matrix was serialized");
  }
  incomplete = Fixture();
  incomplete.white_peace.would_accept_now = false;
  if (xar::game::SerializeWarTerminationExitTermsV2TestOnly(incomplete)
          .has_value()) {
    return Fail("inconsistent recipient response was serialized");
  }
  incomplete = Fixture();
  incomplete.white_peace.complete = false;
  if (xar::game::SerializeWarTerminationExitTermsV2TestOnly(incomplete)
          .has_value()) {
    return Fail("incomplete white-peace preview was serialized");
  }
  incomplete = Fixture();
  incomplete.claims.front().present = false;
  if (xar::game::SerializeWarTerminationExitTermsV2TestOnly(incomplete)
          .has_value()) {
    return Fail("missing declared target claim was serialized as ready");
  }

  if (argc == 1) {
    std::cout << serialized.value() << '\n';
    return 0;
  }
  if (argc != 2) {
    return Fail("expected zero args or one independent golden path");
  }
  std::ifstream stream(argv[1], std::ios::binary);
  if (!stream) {
    return Fail("could not open independent exit-terms golden");
  }
  std::string golden((std::istreambuf_iterator<char>(stream)),
                     std::istreambuf_iterator<char>());
  if (serialized.value() != MinifyJsonWhitespace(golden)) {
    return Fail("v2 test-only serializer drifted from independent golden");
  }
  std::cout << "PASS: exit_terms_v2_test_only_serializer=1 "
               "available_only=1 production_capability=0 dispatch=0\n";
  return 0;
}
