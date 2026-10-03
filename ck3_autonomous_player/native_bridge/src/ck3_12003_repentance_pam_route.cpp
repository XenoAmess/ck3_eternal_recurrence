#include "xar_bridge/ck3_12003_repentance_pam_route.hpp"

#include <algorithm>
#include <cstring>

namespace xar::ck3_12003::religion::repentance_pam_route {
namespace {
constexpr std::string_view kExactExeSha =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";

bool ShaMatches(std::string_view value) noexcept {
  if (value.size() != kExactExeSha.size()) return false;
  for (std::size_t i = 0; i < value.size(); ++i) {
    const char c = value[i] >= 'a' && value[i] <= 'f'
        ? static_cast<char>(value[i] - 'a' + 'A') : value[i];
    if (c != kExactExeSha[i]) return false;
  }
  return true;
}

bool CopyRaw(const void *source, void *destination, std::size_t bytes) noexcept {
  if (!source) return false;
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    std::memcpy(destination, source, bytes);
    return true;
  } __except (1) {
    return false;
  }
#else
  std::memcpy(destination, source, bytes);
  return true;
#endif
}

void Set(BoolObservation &value, bool observed) noexcept {
  value.available = true;
  value.reason = "none";
  value.value = observed;
}
void Missing(BoolObservation &value, const char *reason) noexcept {
  value.available = false;
  value.reason = reason;
  value.value.reset();
}

bool Frame(std::int32_t actor, std::int32_t date, std::uint64_t epoch,
    std::int32_t observed_actor, std::int32_t observed_date,
    std::uint64_t observed_epoch) noexcept {
  return actor == observed_actor && date == observed_date && epoch == observed_epoch;
}

void ReadPam(const Bindings &bindings, BoolObservation &out) noexcept {
  if (!bindings.enabled || !bindings.feature_root_slot || !bindings.feature_enum_table) {
    Missing(out, "bindings_unavailable");
    return;
  }
  std::uint32_t identifier = 0;
  std::uintptr_t root = 0, root_after = 0;
  std::uint64_t bits = 0;
  if (!CopyRaw(bindings.feature_enum_table + kPamFeatureIndex, &identifier, sizeof(identifier)) ||
      identifier != kPamFeatureIdentifier) {
    Missing(out, "pam_feature_enum_unavailable");
    return;
  }
  if (!CopyRaw(bindings.feature_root_slot, &root, sizeof(root)) || !root ||
      !CopyRaw(reinterpret_cast<const void *>(root + kEffectiveFeatureBitsOffset), &bits, sizeof(bits)) ||
      !CopyRaw(bindings.feature_root_slot, &root_after, sizeof(root_after)) || root_after != root) {
    Missing(out, "effective_feature_bits_unavailable");
    return;
  }
  Set(out, (bits & (std::uint64_t{1} << kPamFeatureIndex)) != 0);
}

bool ScalarOptionalEqual(std::int32_t left, std::int32_t right) noexcept {
  // Exact native ?= validates left Character scope before full payload equality.
  // Fresh role readers already resolve present full IDs; -1 is legal absence.
  return left != -1 && right != -1 && left == right;
}

void AppendQuoted(std::string &out, std::string_view value) {
  out += '"';
  for (const char c : value) {
    if (c == '"' || c == '\\') out += '\\';
    out += c;
  }
  out += '"';
}
void AppendBool(std::string &out, const char *key, const BoolObservation &value) {
  out += ',';
  AppendQuoted(out, key);
  out += ":{\"available\":";
  out += value.available ? "true" : "false";
  out += ",\"reason\":";
  AppendQuoted(out, value.reason);
  out += ",\"value\":";
  out += value.value ? (*value.value ? "true" : "false") : "null";
  out += '}';
}
} // namespace

Bindings BindRepentancePamRouteImage12003(std::uintptr_t module_base,
    std::string_view executable_sha256) noexcept {
  Bindings out;
  if (!module_base || !ShaMatches(executable_sha256)) return out;
  out.enabled = true;
  out.feature_root_slot = reinterpret_cast<const std::uintptr_t *>(module_base + kFeatureRootSlotRva);
  out.feature_enum_table = reinterpret_cast<const std::uint32_t *>(module_base + kFeatureEnumTableRva);
  return out;
}

bool ReadRepentancePamRoute12003(const Bindings &bindings, void *actual_played_character,
    std::int32_t actor, std::int32_t date, std::uint64_t epoch,
    const ck3_12002::religion::Context &religion,
    const ck3_12002::religion::doctrine12002::TenetParameterContext &parameters,
    const ck3_12002::religion::doctrine12002::FaithMainRiteDoctrines &doctrines,
    const repentance_candidates::Context &current_candidates,
    const RawRouteInputs &raw, Context &output) noexcept {
  output = {};
  output.played_character_id = actor;
  output.date_raw = date;
  output.capture_epoch = epoch;
  if (!bindings.enabled) return false;
  if (!actual_played_character || actor == -1) {
    output.reason = "actual_player_unavailable";
    return false;
  }
  try {
    ReadPam(bindings, output.has_pam_dlc);
    const bool religion_ok = religion.available && religion.religion_key && religion.faith_id &&
        Frame(actor, date, epoch, religion.played_character_id, religion.date_raw, religion.capture_epoch);
    if (religion_ok) {
      output.current_rite_id = religion.rite_id;
      output.faith_id = religion.faith_id;
      output.faith_main_rite_id = religion.faith_main_rite_id;
      output.religion_key = religion.religion_key;
    }
    const bool parameter_ok = parameters.available && religion_ok &&
        Frame(actor, date, epoch, static_cast<std::int32_t>(parameters.played_character_id),
            parameters.date_raw, parameters.capture_epoch) && parameters.faith_id == religion.faith_id &&
        ((parameters.faith_main_rite && religion.faith_main_rite_id &&
          parameters.faith_main_rite->rite_id == *religion.faith_main_rite_id) ||
         (!parameters.faith_main_rite && !religion.faith_main_rite_id));
    if (parameter_ok) {
      const bool spiritual = parameters.faith_main_rite && std::any_of(
          parameters.faith_main_rite->parameters.begin(), parameters.faith_main_rite->parameters.end(),
          [](const auto &entry) { return entry.key == "spiritual_head_of_faith" && entry.value; });
      Set(output.faith_main_rite_spiritual_head_of_faith, spiritual);
      Set(output.faith_qualifies_for_pam_clergy_route,
          *religion.religion_key == "christianity_religion" && spiritual);
    } else {
      Missing(output.faith_main_rite_spiritual_head_of_faith, "fresh_faith_main_rite_parameters_unavailable");
      Missing(output.faith_qualifies_for_pam_clergy_route, "fresh_faith_main_rite_parameters_unavailable");
    }
    const bool doctrine_ok = doctrines.available && religion_ok &&
        Frame(actor, date, epoch, doctrines.played_character_id, doctrines.date_raw, doctrines.capture_epoch) &&
        doctrines.faith_id == religion.faith_id && doctrines.main_rite_id == religion.faith_main_rite_id;
    if (doctrine_ok) {
      Set(output.faith_has_central_sacraments, std::any_of(doctrines.rows.begin(), doctrines.rows.end(),
          [](const auto &entry) { return entry.doctrine_key == "doctrine_sacraments_central"; }));
    } else {
      Missing(output.faith_has_central_sacraments, "fresh_faith_main_rite_doctrines_unavailable");
    }
    const bool candidates_ok = current_candidates.available &&
        Frame(actor, date, epoch, current_candidates.played_character_id,
            current_candidates.date_raw, current_candidates.capture_epoch);
    const auto &capital = current_candidates.roles[1];
    const auto &authority = current_candidates.roles[3];
    const bool authority_ok = candidates_ok && authority.available && authority.character_id.has_value();
    const bool capital_ok = candidates_ok && capital.available && capital.character_id.has_value();
    if (authority_ok) Set(output.religious_authority_exists, *authority.character_id != -1);
    else Missing(output.religious_authority_exists, "fresh_religious_authority_unavailable");
    if (capital_ok) Set(output.capital_clerical_holder_is_actor, ScalarOptionalEqual(*capital.character_id, actor));
    else Missing(output.capital_clerical_holder_is_actor, "fresh_capital_clerical_holder_unavailable");
    if (capital_ok && authority_ok) {
      Set(output.capital_clerical_holder_is_religious_authority,
          ScalarOptionalEqual(*capital.character_id, *authority.character_id));
    } else {
      Missing(output.capital_clerical_holder_is_religious_authority, "fresh_capital_or_authority_unavailable");
    }
    const bool raw_ok = raw.available && raw.pope_excom.has_value() && raw.highest_held_title_tier.has_value() &&
        raw.any_held_title_has_clerical_region.has_value() &&
        Frame(actor, date, epoch, raw.played_character_id, raw.date_raw, raw.capture_epoch);
    if (raw_ok && output.has_pam_dlc.available) {
      Set(output.need_hof_for_clergy_interaction,
          *raw.highest_held_title_tier >= (*output.has_pam_dlc.value ? 4 : 5));
    } else Missing(output.need_hof_for_clergy_interaction, "fresh_rank_or_pam_feature_unavailable");
    if (raw_ok && authority_ok) {
      Set(output.is_archbishop_or_higher, *raw.any_held_title_has_clerical_region ||
          ScalarOptionalEqual(*authority.character_id, actor));
    } else Missing(output.is_archbishop_or_higher, "fresh_clerical_title_or_authority_unavailable");
    if (raw_ok && parameter_ok && authority_ok && capital_ok) {
      const bool bypass_rank = *raw.pope_excom ||
          *output.capital_clerical_holder_is_religious_authority.value ||
          *output.capital_clerical_holder_is_actor.value;
      Set(output.petition_head_of_faith_repentance_requires_petition,
          *output.faith_qualifies_for_pam_clergy_route.value && *output.religious_authority_exists.value &&
          (bypass_rank || *raw.highest_held_title_tier >= 4));
    } else Missing(output.petition_head_of_faith_repentance_requires_petition, "fresh_requires_petition_inputs_unavailable");
    const bool route_ok = output.has_pam_dlc.available && parameter_ok &&
        output.need_hof_for_clergy_interaction.available &&
        output.petition_head_of_faith_repentance_requires_petition.available &&
        output.is_archbishop_or_higher.available && authority_ok;
    if (candidates_ok) {
      for (const auto &candidate : current_candidates.candidates) {
        CandidateRoute row;
        row.requested_recipient_character_id = candidate.requested_recipient_character_id;
        if (authority_ok) Set(row.recipient_is_religious_authority,
            ScalarOptionalEqual(row.requested_recipient_character_id, *authority.character_id));
        else Missing(row.recipient_is_religious_authority, "fresh_religious_authority_unavailable");
        if (route_ok) {
          const bool pam_restricted = *output.has_pam_dlc.value &&
              *output.faith_qualifies_for_pam_clergy_route.value;
          Set(row.pam_ordinary_route_clause_passes, !pam_restricted ||
              (!*output.need_hof_for_clergy_interaction.value &&
               !*output.petition_head_of_faith_repentance_requires_petition.value &&
               !(*row.recipient_is_religious_authority.value && !*output.is_archbishop_or_higher.value)));
        } else Missing(row.pam_ordinary_route_clause_passes, "fresh_pam_route_inputs_unavailable");
        output.candidates.push_back(row);
      }
    }
    output.available = route_ok && doctrine_ok && candidates_ok;
    output.reason = output.available ? "none" : "one_or_more_route_inputs_unavailable";
    return output.available;
  } catch (...) {
    output.reason = "pam_route_copy_failed";
    return false;
  }
}

std::string SerializeRepentancePamRoute12003(const Context &value) {
  std::string out = "{\"schema\":";
  AppendQuoted(out, kSchema);
  out += ",\"available\":";
  out += value.available ? "true" : "false";
  out += ",\"reason\":";
  AppendQuoted(out, value.reason);
  out += ",\"evaluator\":";
  AppendQuoted(out, value.evaluator);
  out += ",\"compiled_named_trigger_invoked\":false,\"played_character_id\":";
  out += std::to_string(value.played_character_id);
  out += ",\"date_raw\":" + std::to_string(value.date_raw);
  out += ",\"capture_epoch\":" + std::to_string(value.capture_epoch);
  out += ",\"current_rite_id\":" + (value.current_rite_id ? std::to_string(*value.current_rite_id) : "null");
  out += ",\"faith_id\":" + (value.faith_id ? std::to_string(*value.faith_id) : "null");
  out += ",\"faith_main_rite_id\":" + (value.faith_main_rite_id ? std::to_string(*value.faith_main_rite_id) : "null");
  out += ",\"religion_key\":";
  if (value.religion_key) AppendQuoted(out, *value.religion_key);
  else out += "null";
  out += ",\"faith_central_sacraments_source\":";
  AppendQuoted(out, value.faith_central_sacraments_source);
  AppendBool(out, "faith_main_rite_spiritual_head_of_faith", value.faith_main_rite_spiritual_head_of_faith);
  AppendBool(out, "has_pam_dlc", value.has_pam_dlc);
  AppendBool(out, "faith_qualifies_for_pam_clergy_route", value.faith_qualifies_for_pam_clergy_route);
  AppendBool(out, "religious_authority_exists", value.religious_authority_exists);
  AppendBool(out, "capital_clerical_holder_is_religious_authority", value.capital_clerical_holder_is_religious_authority);
  AppendBool(out, "capital_clerical_holder_is_actor", value.capital_clerical_holder_is_actor);
  AppendBool(out, "petition_head_of_faith_repentance_requires_petition", value.petition_head_of_faith_repentance_requires_petition);
  AppendBool(out, "need_hof_for_clergy_interaction", value.need_hof_for_clergy_interaction);
  AppendBool(out, "is_archbishop_or_higher", value.is_archbishop_or_higher);
  AppendBool(out, "faith_has_central_sacraments", value.faith_has_central_sacraments);
  out += ",\"candidates\":[";
  bool first = true;
  for (const auto &row : value.candidates) {
    if (!first) out += ',';
    first = false;
    out += "{\"requested_recipient_character_id\":" + std::to_string(row.requested_recipient_character_id);
    AppendBool(out, "recipient_is_religious_authority", row.recipient_is_religious_authority);
    AppendBool(out, "pam_ordinary_route_clause_passes", row.pam_ordinary_route_clause_passes);
    out += '}';
  }
  out += "]}";
  return out;
}

} // namespace xar::ck3_12003::religion::repentance_pam_route
