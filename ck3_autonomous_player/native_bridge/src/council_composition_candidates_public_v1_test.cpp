#include "xar_bridge/council_composition_candidates_public_v1.hpp"

#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <string>
#include <string_view>

namespace {

using namespace xar;
using Failure = game::CouncilCompositionCandidatesPublicFailureV1;
using Result = ck3_11906::ProjectCouncilCompositionCandidatesPublicResultV1;

template <std::size_t Size>
void SetFixed(std::array<char, Size> &output, std::string_view value) {
  assert(value.size() < output.size());
  output.fill('\0');
  std::copy(value.begin(), value.end(), output.begin());
}

game::CouncilCompositionStewardCandidatesV1 PrivateResult() {
  game::CouncilCompositionStewardCandidatesV1 output{};
  output.status =
      game::CouncilCompositionStewardCandidatesStatusV1::available;
  output.unavailable_reason =
      game::CouncilCompositionStewardCandidatesFailureV1::none;
  SetFixed(output.snapshot_id, "native:17");
  output.public_revision = 19;
  output.native_revision = 17;
  output.date_raw = 53'178'264;
  output.paused = true;
  output.owner_character_id = 29'829;
  SetFixed(output.position_key, "councillor_steward");
  output.candidate_collection_complete = true;
  output.candidate_count = 2;
  output.candidates[0] = {30'784, 4};
  output.candidates[1] = {57'582, 1};
  output.temporary_vector_released = true;
  output.readiness.identity_ready = true;
  output.readiness.candidate_collection_ready = true;
  return output;
}

ck3_11906::CouncilCompositionCandidatesPublicEnrichmentV1 Enrichment() {
  ck3_11906::CouncilCompositionCandidatesPublicEnrichmentV1 output{};
  SetFixed(output.snapshot_id, "native:17");
  output.public_revision = 19;
  output.native_revision = 17;
  output.date_raw = 53'178'264;
  output.owner_character_id = 29'829;
  SetFixed(output.position_key, "councillor_steward");
  output.incumbent_character_id = -1;
  output.incumbent_ready = true;
  output.incumbent_main_skill = -1;
  output.incumbent_main_skill_ready = true;
  output.same_frame_stable = true;
  output.candidate_count = 2;
  output.candidates[0] = {30'784, 4, true,
      game::CouncilCompositionCandidateEligibilityReasonV1::
          native_candidate_provider_accepted,
      18};
  output.candidates[1] = {57'582, 1, true,
      game::CouncilCompositionCandidateEligibilityReasonV1::
          native_candidate_provider_accepted,
      27};
  return output;
}

game::CouncilCompositionCandidatesPublicV1 Project(
    const game::CouncilCompositionStewardCandidatesV1 &private_result,
    const ck3_11906::CouncilCompositionCandidatesPublicEnrichmentV1
        &enrichment,
    Result expected) {
  game::CouncilCompositionCandidatesPublicV1 output{};
  assert(ck3_11906::ProjectCouncilCompositionCandidatesPublicV1(
             private_result, enrichment, output) == expected);
  return output;
}

void ExpectUnavailable(
    const game::CouncilCompositionCandidatesPublicV1 &output,
    Failure reason) {
  assert(output.status ==
         game::CouncilCompositionCandidatesPublicStatusV1::unavailable);
  assert(output.unavailable_reason == reason);
  assert(!output.readiness.ready);
  assert(output.candidate_count == 0);
}

void TestVacancyProjectionAndWire() {
  const auto output =
      Project(PrivateResult(), Enrichment(), Result::available);
  assert(output.status ==
         game::CouncilCompositionCandidatesPublicStatusV1::available);
  assert(output.vacant);
  assert(output.incumbent_character_id == -1);
  assert(output.readiness.incumbent_main_skill_ready);
  assert(output.action_route ==
         game::CouncilCompositionCandidateActionRouteV1::assign);
  assert(output.candidate_count == 2);
  assert(output.candidates[0].character_id == 30'784);
  assert(output.candidates[0].native_collection_ordinal == 4);
  assert(output.candidates[0].eligible);
  assert(output.candidates[0].main_skill.value == 18);
  assert(output.candidates[0].action_route == output.action_route);
  assert(output.candidates[1].character_id == 57'582);
  assert(output.candidates[1].main_skill.value == 27);
  assert(output.readiness.ready);

  const std::string wire =
      ck3_11906::SerializeCouncilCompositionCandidatesPublicV1(output);
  assert(wire.find(
             "\"schema\":\"xar.ck3.council-composition-candidates/v1\"") !=
         std::string::npos);
  assert(wire.find(
             "\"capability\":\"game.query.council-composition-candidates-v1\"") !=
         std::string::npos);
  assert(wire.find("\"incumbent_character_id\":null,\"incumbent_main_skill\":null,\"vacant\":true,") !=
         std::string::npos);
  assert(wire.find("\"action_route\":\"assign\"") != std::string::npos);
  assert(wire.find(
             "\"eligible\":true,\"eligibility_reason\":\"native_candidate_provider_accepted\"") !=
         std::string::npos);
  assert(wire.find("\"main_skill\":{\"key\":\"stewardship\",\"value\":27}") !=
         std::string::npos);
  assert(wire.find("\"same_frame_ready\":true,\"ready\":true") !=
         std::string::npos);
}

void TestReplacementProjection() {
  auto enrichment = Enrichment();
  enrichment.incumbent_character_id = 33'433;
  enrichment.incumbent_main_skill = 12;
  const auto output =
      Project(PrivateResult(), enrichment, Result::available);
  assert(!output.vacant);
  assert(output.incumbent_character_id == 33'433);
  assert(output.incumbent_main_skill.value == 12);
  assert(output.action_route ==
         game::CouncilCompositionCandidateActionRouteV1::replace);
  assert(output.candidates[0].action_route == output.action_route);
  const auto wire =
      ck3_11906::SerializeCouncilCompositionCandidatesPublicV1(output);
  assert(wire.find(
             "\"incumbent_character_id\":33433,\"incumbent_main_skill\":{\"key\":\"stewardship\",\"value\":12},\"vacant\":false,\"action_route\":\"replace\"") !=
         std::string::npos);
}

void TestPrivateFailureIsPreserved() {
  auto private_result = PrivateResult();
  private_result.status =
      game::CouncilCompositionStewardCandidatesStatusV1::unavailable;
  private_result.unavailable_reason =
      game::CouncilCompositionStewardCandidatesFailureV1::date_drift;
  const auto output =
      Project(private_result, Enrichment(), Result::unavailable);
  ExpectUnavailable(output, Failure::private_reader_unavailable);
  assert(output.source_unavailable_reason ==
         game::CouncilCompositionStewardCandidatesFailureV1::date_drift);
  const auto wire =
      ck3_11906::SerializeCouncilCompositionCandidatesPublicV1(output);
  assert(wire.find("\"unavailable_reason\":\"private_reader_unavailable\"") !=
         std::string::npos);
  assert(wire.find("\"source_unavailable_reason\":\"date_drift\"") !=
         std::string::npos);
}

void TestEnrichmentAndBindingFailures() {
  {
    auto enrichment = Enrichment();
    enrichment.incumbent_ready = false;
    ExpectUnavailable(Project(PrivateResult(), enrichment, Result::unavailable),
                      Failure::enrichment_unavailable);
  }
  {
    auto enrichment = Enrichment();
    ++enrichment.native_revision;
    ExpectUnavailable(Project(PrivateResult(), enrichment, Result::unavailable),
                      Failure::same_frame_binding_mismatch);
  }
  {
    auto enrichment = Enrichment();
    enrichment.incumbent_character_id = 0;
    ExpectUnavailable(Project(PrivateResult(), enrichment, Result::unavailable),
                      Failure::incumbent_invalid);
  }
  {
    auto enrichment = Enrichment();
    enrichment.incumbent_main_skill_ready = false;
    ExpectUnavailable(Project(PrivateResult(), enrichment, Result::unavailable),
                      Failure::incumbent_main_skill_unready);
  }
  {
    auto enrichment = Enrichment();
    enrichment.incumbent_character_id = 33'433;
    enrichment.incumbent_main_skill = -1;
    ExpectUnavailable(Project(PrivateResult(), enrichment, Result::unavailable),
                      Failure::incumbent_main_skill_unready);
  }
  {
    auto enrichment = Enrichment();
    enrichment.candidates[1].character_id = 57'583;
    ExpectUnavailable(Project(PrivateResult(), enrichment, Result::unavailable),
                      Failure::candidate_set_mismatch);
  }
  {
    auto enrichment = Enrichment();
    enrichment.candidates[0].final_eligible = false;
    ExpectUnavailable(Project(PrivateResult(), enrichment, Result::unavailable),
                      Failure::candidate_eligibility_unready);
  }
  {
    auto enrichment = Enrichment();
    enrichment.candidates[0].main_skill = -1;
    ExpectUnavailable(Project(PrivateResult(), enrichment, Result::unavailable),
                      Failure::candidate_main_skill_unready);
  }
}

void TestPrivateSchemaInvariantFailure() {
  auto private_result = PrivateResult();
  private_result.temporary_vector_released = false;
  ExpectUnavailable(Project(private_result, Enrichment(), Result::unavailable),
                    Failure::schema_invariant_failed);
}

} // namespace

int main() {
  TestVacancyProjectionAndWire();
  TestReplacementProjection();
  TestPrivateFailureIsPreserved();
  TestEnrichmentAndBindingFailures();
  TestPrivateSchemaInvariantFailure();
  return 0;
}
