#include "xar_bridge/ck3_12002_marriage_probe.hpp"

#include <string>
#include <utility>
#include <vector>

namespace xar::ck3_12002 {
namespace {

void Number(std::string &out, std::string_view name, std::int64_t value) {
  out += '"'; out += name; out += "\":"; out += std::to_string(value);
}
void Boolean(std::string &out, std::string_view name, bool value) {
  out += '"'; out += name; out += value ? "\":true" : "\":false";
}
void Roles(std::string &out, const game::ArrangeMarriageValidationSample &roles) {
  out += '{'; Number(out, "slot_index", roles.slot_index);
  out += ','; Number(out, "candidate_character_id", roles.candidate_character_id);
  out += ','; Number(out, "actor_character_id", roles.actor_character_id);
  out += ','; Number(out, "recipient_character_id", roles.recipient_character_id);
  out += ','; Number(out, "secondary_actor_character_id", roles.secondary_actor_character_id);
  out += ','; Number(out, "secondary_recipient_character_id", roles.secondary_recipient_character_id);
  out += ','; Number(out, "intermediary_character_id", roles.intermediary_character_id);
  out += '}';
}
const char *Status(game::ReadArrangeMarriageChoicesResult status) noexcept {
  switch (status) {
    case game::ReadArrangeMarriageChoicesResult::available: return "available";
    case game::ReadArrangeMarriageChoicesResult::no_played_character: return "no_played_character";
    case game::ReadArrangeMarriageChoicesResult::unavailable: return "unavailable";
  }
  return "unavailable";
}

} // namespace

bool CollectMarriageProbe12002(const ContextBindings &bindings,
                              std::string &artifact_json) noexcept {
  CoreSnapshotPrefix prefix{};
  const bool core_observable = ReadCoreSnapshot(bindings.core, prefix);
  game::PlayedCharacterRelationships12002 relationships{};
  const bool relationships_observable = core_observable &&
      prefix.has_played_character && ReadPlayedCharacterRelationships(
          bindings.core, prefix.played_character_id, relationships);
  std::vector<game::ArrangeMarriageChoice> choices;
  std::vector<game::MarriageCandidateEvaluation12002> evaluations;
  game::ArrangeMarriageQueryDiagnostics diagnostics{};
  const auto status = ReadArrangeMarriageChoices(
      bindings, choices, diagnostics, &evaluations);

  std::string out = "{\"schema\":1,\"kind\":\"ck3_12002_marriage_native_probe\","
      "\"game_version\":\"1.20.0.2\",\"executable_sha256\":\"";
  out += kExecutableSha256;
  out += "\",\"query_status\":\""; out += Status(status); out += "\",";
  Boolean(out, "core_observable", core_observable);
  out += ','; Number(out, "date_raw", prefix.clock.date_raw);
  out += ','; Boolean(out, "paused", prefix.clock.paused);
  out += ','; Number(out, "played_character_id", prefix.played_character_id);
  out += ','; Boolean(out, "relationships_observable", relationships_observable);
  out += ",\"relationships\":{";
  Number(out, "betrothed_id", relationships.betrothed_character_id);
  out += ','; Number(out, "primary_spouse_id", relationships.primary_spouse_character_id);
  out += ",\"spouse_ids\":[";
  for (std::size_t index = 0; index < relationships.spouse_character_ids.size(); ++index) {
    if (index != 0) out += ',';
    out += std::to_string(relationships.spouse_character_ids[index]);
  }
  out += "]},\"diagnostics\":{";
  Number(out, "storage_capacity", diagnostics.storage_capacity);
  out += ','; Number(out, "slots_scanned", diagnostics.slots_scanned);
  out += ','; Number(out, "empty_slots", diagnostics.empty_slots);
  out += ','; Number(out, "live_candidates", diagnostics.live_candidates);
  out += ','; Number(out, "dead_candidates", diagnostics.dead_candidates);
  out += ','; Number(out, "self_candidates", diagnostics.self_candidates);
  out += ','; Number(out, "generation_mismatch_candidates", diagnostics.generation_mismatch_candidates);
  out += ','; Number(out, "contexts_constructed", diagnostics.contexts_constructed);
  out += ','; Number(out, "context_construct_failures", diagnostics.context_construct_failures);
  out += ','; Number(out, "native_validate_true", diagnostics.native_validate_true);
  out += ','; Number(out, "native_validate_false", diagnostics.native_validate_false);
  out += ",\"validation_false_samples\":[";
  for (std::size_t index = 0; index < diagnostics.validation_false_samples.size(); ++index) {
    if (index != 0) out += ',';
    Roles(out, diagnostics.validation_false_samples[index]);
  }
  out += "]},\"cost_order\":[\"gold\",\"prestige\",\"piety\",\"renown\","
      "\"influence\",\"herd\",\"treasury\",\"treasury_or_gold\",\"merit\",\"barter_goods\"],"
      "\"marriage_candidate_evaluations\":[";
  for (std::size_t index = 0; index < evaluations.size(); ++index) {
    const auto &row = evaluations[index];
    if (index != 0) out += ',';
    out += '{'; Number(out, "played_character_id", row.choice.played_character_id);
    out += ','; Number(out, "candidate_character_id", row.choice.candidate_character_id);
    out += ','; Boolean(out, "native_legal", row.native_legal);
    out += ','; Boolean(out, "native_auto_accept", row.native_auto_accept);
    out += ','; Number(out, "recipient_acceptance_score_raw", row.recipient_acceptance_score_raw);
    out += ','; Number(out, "intermediary_acceptance_score_raw", row.intermediary_acceptance_score_raw);
    out += ','; Number(out, "raw_scale", row.raw_scale);
    out += ",\"roles\":"; Roles(out, row.roles);
    out += ",\"send_costs_raw\":[";
    for (std::size_t cost = 0; cost < row.send_costs_raw.size(); ++cost) {
      if (cost != 0) out += ',';
      out += std::to_string(row.send_costs_raw[cost]);
    }
    out += "]}";
  }
  out += "]}\n";
  artifact_json = std::move(out);
  return core_observable && relationships_observable &&
      status == game::ReadArrangeMarriageChoicesResult::available;
}

} // namespace xar::ck3_12002
