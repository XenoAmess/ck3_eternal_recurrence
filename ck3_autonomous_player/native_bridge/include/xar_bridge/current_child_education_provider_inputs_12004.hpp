#pragma once

#include "xar_bridge/ck3_12002_phase_culture.hpp"
#include "xar_bridge/current_first_heir_child_inputs_v1.hpp"
#include "xar_bridge/current_first_heir_descendants_v1.hpp"

#include <algorithm>
#include <bit>
#include <cstdint>
#include <map>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace xar::bridge {

// Independent owned query leaf. No change to the existing child-row stride.
struct CurrentChildEducationProviderRow12004 {
  std::uint32_t child_full_id{};
  std::vector<std::uint32_t> occurrence_indices;
  bool education_traits_available{};
  std::string education_traits_unavailable_reason{"education_traits_not_observed"};
  std::optional<std::vector<std::string>> education_trait_keys;
  bool culture_parameter_available{};
  std::optional<std::uint32_t> culture_full_id;
  std::optional<bool> better_ward_education;
  std::string culture_unavailable_reason{"child_culture_not_observed"};
};

struct CurrentChildEducationProviderInputs12004 {
  std::uint64_t native_revision{};
  std::int64_t date_raw{};
  std::uint32_t played_character_full_id{};
  std::uint32_t heir_character_full_id{};
  std::string request_id;
  std::string status{"unavailable"};
  std::string unavailable_reason{"education_provider_not_observed"};
  bool roster_complete{};
  bool collection_available{};
  bool child_observation_complete{};
  std::vector<CurrentChildEducationProviderRow12004> rows;
};

using CurrentChildEducationCultureReader12004 = bool (*)(void *, std::uint32_t,
    xar::ck3_12002::phase_culture::CharacterCultureParameterObservation &) noexcept;

inline CurrentChildEducationProviderInputs12004 ReadCurrentChildEducationProviderInputs12004(
    const xar::ck3_11906::CurrentFirstHeirDescendantsReadV1 &descendants,
    const xar::ck3_11906::CurrentFirstHeirChildInputsReadV1 &inputs,
    std::uint64_t native_revision, std::int64_t date_raw,
    std::int32_t played_id, std::int32_t heir_id, std::string_view request_id,
    void *reader_context, CurrentChildEducationCultureReader12004 read_culture) {
  CurrentChildEducationProviderInputs12004 out;
  out.native_revision = native_revision;
  out.date_raw = date_raw;
  out.played_character_full_id = std::bit_cast<std::uint32_t>(played_id);
  out.heir_character_full_id = std::bit_cast<std::uint32_t>(heir_id);
  if (request_id.size() > 256U) {
    out.unavailable_reason = "education_request_id_limit";
    return out;
  }
  out.request_id = request_id;
  if (native_revision == 0 || !descendants.date_raw || !inputs.date_raw ||
      *descendants.date_raw != date_raw || *inputs.date_raw != date_raw ||
      descendants.played_character_id != played_id || inputs.played_character_id != played_id ||
      descendants.heir_character_id != heir_id || inputs.heir_character_id != heir_id ||
      descendants.status == xar::ck3_11906::CurrentFirstHeirDescendantsStatusV1::unavailable ||
      inputs.status == "unavailable" || !descendants.roster_complete ||
      descendants.family_present != std::optional<bool>{true} ||
      !descendants.native_child_count_raw || *descendants.native_child_count_raw < 0 ||
      descendants.rows.size() != static_cast<std::size_t>(*descendants.native_child_count_raw)) {
    out.unavailable_reason = "education_roster_or_query_identity_unavailable";
    return out;
  }
  if (descendants.rows.size() > 4096U || inputs.rows.size() > 256U) {
    out.unavailable_reason = "education_roster_limit";
    return out;
  }
  std::map<std::uint32_t, std::vector<std::uint32_t>> expected;
  std::map<std::uint32_t, std::pair<bool, bool>> classifications;
  for (std::size_t index = 0; index < descendants.rows.size(); ++index) {
    const auto &source = descendants.rows[index];
    if (source.occurrence_index != static_cast<std::uint32_t>(index) ||
        !source.generation_valid || !source.alive ||
        (*source.alive && !source.child_of_heir)) {
      out.unavailable_reason = "education_unresolved_descendant_occurrence";
      return out;
    }
    const auto classification = std::pair{*source.alive,
        *source.alive && *source.child_of_heir};
    const auto inserted = classifications.emplace(source.raw_character_id, classification);
    if (!inserted.second && inserted.first->second != classification) {
      out.unavailable_reason = "education_descendant_classification_changed";
      return out;
    }
    if (classification.first && classification.second)
      expected[source.raw_character_id].push_back(source.occurrence_index);
  }
  if (expected.size() != inputs.rows.size()) {
    out.unavailable_reason = "education_child_row_join_incomplete";
    return out;
  }
  std::vector<std::uint32_t> seen;
  for (const auto &source : inputs.rows) {
    const auto full_id = std::bit_cast<std::uint32_t>(source.character_id);
    const auto occurrence = expected.find(full_id);
    if (occurrence == expected.end() || occurrence->second != source.occurrence_indices ||
        std::find(seen.begin(), seen.end(), full_id) != seen.end()) {
      out.unavailable_reason = "education_child_full_id_join_mismatch";
      return out;
    }
    seen.push_back(full_id);
  }
  out.roster_complete = true;
  out.collection_available = true;
  out.child_observation_complete = true;
  out.rows.reserve(inputs.rows.size());
  for (const auto &source : inputs.rows) {
    CurrentChildEducationProviderRow12004 row;
    row.child_full_id = std::bit_cast<std::uint32_t>(source.character_id);
    row.occurrence_indices = source.occurrence_indices;
    if (source.education_traits && source.education_traits->available &&
        source.education_traits->present_trait_keys &&
        source.education_traits->present_trait_keys->size() <= 25U) {
      bool valid = true;
      std::vector<std::string> keys;
      std::optional<std::size_t> previous_catalog_index;
      for (const auto key : *source.education_traits->present_trait_keys) {
        const auto found = std::find(xar::ck3_11906::kChildEducationTraitKeysV1.begin(),
            xar::ck3_11906::kChildEducationTraitKeysV1.end(), key);
        if (found == xar::ck3_11906::kChildEducationTraitKeysV1.end()) {
          valid = false;
          break;
        }
        const auto index = static_cast<std::size_t>(
            found - xar::ck3_11906::kChildEducationTraitKeysV1.begin());
        if (previous_catalog_index && index <= *previous_catalog_index) {
          valid = false;
          break;
        }
        previous_catalog_index = index;
        keys.emplace_back(key); // Preserve the observed order; never sort it.
      }
      if (valid) {
        row.education_traits_available = true;
        row.education_traits_unavailable_reason.clear();
        row.education_trait_keys = std::move(keys);
      } else {
        row.education_traits_unavailable_reason = "education_trait_key_projection_invalid";
      }
    } else if (source.education_traits &&
        !source.education_traits->unavailable_reason.empty() &&
        source.education_traits->unavailable_reason.size() <= 256U) {
      row.education_traits_unavailable_reason = source.education_traits->unavailable_reason;
    }
    xar::ck3_12002::phase_culture::CharacterCultureParameterObservation culture;
    if (read_culture != nullptr && read_culture(reader_context, row.child_full_id, culture) &&
        culture.available && culture.value && culture.culture_full_id) {
      row.culture_parameter_available = true;
      row.culture_full_id = culture.culture_full_id;
      row.better_ward_education = culture.value;
      row.culture_unavailable_reason.clear();
    } else {
      row.culture_full_id = culture.culture_full_id;
      if (culture.unavailable_reason != nullptr &&
          !std::string_view{culture.unavailable_reason}.empty() &&
          std::string_view{culture.unavailable_reason}.size() <= 256U)
        row.culture_unavailable_reason = culture.unavailable_reason;
    }
    out.child_observation_complete = out.child_observation_complete &&
        row.education_traits_available && row.culture_parameter_available;
    out.rows.push_back(std::move(row));
  }
  out.status = out.child_observation_complete ? "available" : "partial";
  out.unavailable_reason = out.child_observation_complete
      ? "" : "education_child_inputs_partially_observed";
  return out;
}

namespace current_child_education_json_detail12004 {
inline void String(std::string &out, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  out += '"';
  for (const char character : value) {
    const auto byte = static_cast<unsigned char>(character);
    if (character == '"' || character == '\\') { out += '\\'; out += character; }
    else if (byte < 0x20U) { out += "\\u00"; out += hex[byte >> 4U]; out += hex[byte & 15U]; }
    else out += character;
  }
  out += '"';
}
inline void Reason(std::string &out, std::string_view reason) {
  if (reason.empty()) out += "null"; else String(out, reason);
}
inline std::string Serialize(const CurrentChildEducationProviderInputs12004 &value) {
  std::string out = "{\"schema_version\":1,\"read_only\":true,"
      "\"source\":\"same_query_actual4_child_education_inputs\",\"request_id\":";
  String(out, value.request_id);
  out += ",\"native_revision\":" + std::to_string(value.native_revision);
  out += ",\"date_raw\":" + std::to_string(value.date_raw);
  out += ",\"played_character_full_id\":" + std::to_string(value.played_character_full_id);
  out += ",\"heir_character_full_id\":" + std::to_string(value.heir_character_full_id);
  out += ",\"status\":"; String(out, value.status);
  out += ",\"unavailable_reason\":"; Reason(out, value.unavailable_reason);
  out += ",\"roster_complete\":"; out += value.roster_complete ? "true" : "false";
  out += ",\"collection_available\":"; out += value.collection_available ? "true" : "false";
  out += ",\"child_observation_complete\":"; out += value.child_observation_complete ? "true" : "false";
  out += ",\"m6_inputs_complete\":false,\"guardian_role_equivalence_qualified\":false,"
      "\"queried_education_trait_keys\":[";
  bool first = true;
  for (const auto key : xar::ck3_11906::kChildEducationTraitKeysV1) {
    if (!first) out += ','; first = false; String(out, key);
  }
  out += "],\"rows\":[";
  first = true;
  for (const auto &row : value.rows) {
    if (!first) out += ','; first = false;
    out += "{\"child_full_id\":" + std::to_string(row.child_full_id);
    out += ",\"role_source\":\"current_living_actual_child_of_first_heir\",\"occurrence_indices\":[";
    bool first_occurrence = true;
    for (const auto occurrence : row.occurrence_indices) {
      if (!first_occurrence) out += ','; first_occurrence = false; out += std::to_string(occurrence);
    }
    out += "],\"education_traits\":{\"available\":";
    out += row.education_traits_available ? "true" : "false";
    out += ",\"unavailable_reason\":"; Reason(out, row.education_traits_unavailable_reason);
    out += ",\"present_trait_keys\":";
    if (!row.education_trait_keys) out += "null";
    else {
      out += '['; bool first_key = true;
      for (const auto &key : *row.education_trait_keys) {
        if (!first_key) out += ','; first_key = false; String(out, key);
      }
      out += ']';
    }
    out += "},\"culture_parameter\":{\"key\":\"better_ward_education\",\"available\":";
    out += row.culture_parameter_available ? "true" : "false";
    out += ",\"culture_full_id\":";
    out += row.culture_full_id ? std::to_string(*row.culture_full_id) : "null";
    out += ",\"value\":";
    out += row.better_ward_education ? (*row.better_ward_education ? "true" : "false") : "null";
    out += ",\"unavailable_reason\":"; Reason(out, row.culture_unavailable_reason);
    out += "},\"guardian_full_id\":null,\"guardian_culture_parameter\":null,"
        "\"guardian_unavailable_reason\":\"authoritative_educator_identity_not_observed\","
        "\"rite_parameters\":null,\"rite_unavailable_reason\":\"target_rite_education_parameters_not_observed\","
        "\"education_type\":null,\"education_progress\":null,"
        "\"education_variables_unavailable_reason\":\"typed_target_variable_value_access_not_wired\"}";
  }
  out += "]}";
  return out;
}
} // namespace current_child_education_json_detail12004

inline std::string SerializeCurrentChildEducationProviderInputs12004(
    const CurrentChildEducationProviderInputs12004 &value) {
  // Guard the serializer independently of the producer's request-id bound.
  if (value.request_id.size() > 256U) return "null";
  auto out = current_child_education_json_detail12004::Serialize(value);
  if (out.size() <= 65536U) return out;
  auto unavailable = CurrentChildEducationProviderInputs12004{};
  unavailable.native_revision = value.native_revision;
  unavailable.date_raw = value.date_raw;
  unavailable.played_character_full_id = value.played_character_full_id;
  unavailable.heir_character_full_id = value.heir_character_full_id;
  unavailable.request_id = value.request_id;
  unavailable.unavailable_reason = "education_leaf_serialized_size_limit";
  out = current_child_education_json_detail12004::Serialize(unavailable);
  return out.size() <= 65536U ? out : "null";
}

} // namespace xar::bridge
