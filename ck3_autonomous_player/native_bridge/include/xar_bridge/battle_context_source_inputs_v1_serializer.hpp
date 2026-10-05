#pragma once

#include "xar_bridge/battle_context_source_inputs_v1.hpp"

#include <cstddef>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::bridge {
namespace battle_context_source_inputs_v1_detail {

inline void String(std::string &out, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  out += '"';
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') {
      out += '\\';
      out += static_cast<char>(c);
    } else if (c < 0x20U) {
      out += "\\u00";
      out += hex[(c >> 4U) & 0x0FU];
      out += hex[c & 0x0FU];
    } else {
      out += static_cast<char>(c);
    }
  }
  out += '"';
}

inline void Reason(std::string &out, std::string_view value) {
  if (value.empty()) out += "null";
  else String(out, value);
}

template <typename T>
inline void Number(std::string &out, const std::optional<T> &value) {
  out += value ? std::to_string(*value) : "null";
}

inline void Boolean(std::string &out, const std::optional<bool> &value) {
  out += value ? (*value ? "true" : "false") : "null";
}

template <typename T>
inline void Numbers(std::string &out,
                    const std::optional<std::vector<T>> &values) {
  if (!values) { out += "null"; return; }
  out += '[';
  for (std::size_t i = 0; i < values->size(); ++i) {
    if (i) out += ',';
    out += std::to_string((*values)[i]);
  }
  out += ']';
}

inline void Properties(std::string &out,
                       const std::optional<game::ContextSourcePropertiesV1> &p) {
  if (!p) { out += "null"; return; }
  out += "{\"keys_count\":";
  Number(out, p->keys_count);
  out += ",\"values_count\":";
  Number(out, p->values_count);
  out += ",\"keys_u16\":";
  Numbers(out, p->keys_u16);
  out += ",\"values_q64\":";
  Numbers(out, p->values_q64);
  out += ",\"reason\":";
  Reason(out, p->reason);
  out += '}';
}

inline void Resolution(std::string &out,
                       const game::ContextSourceResolutionV1 &r) {
  out += "{\"status\":";
  String(out, r.status);
  out += ",\"requested_full_id\":";
  Number(out, r.requested_full_id);
  out += ",\"selected_full_id\":";
  Number(out, r.selected_full_id);
  out += ",\"reason\":";
  Reason(out, r.reason);
  out += '}';
}

inline void WeightedSpan(std::string &out,
                        const std::optional<game::ContextSourceWeightedSpanV1> &s) {
  if (!s) { out += "null"; return; }
  out += "{\"selected_source\":";
  String(out, s->selected_source);
  out += ",\"count\":";
  Number(out, s->count);
  out += ",\"rows\":";
  if (!s->rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < s->rows->size(); ++i) {
      if (i) out += ',';
      const auto &row = (*s->rows)[i];
      out += "{\"native_index\":" + std::to_string(row.native_index);
      out += ",\"definition_identity\":";
      if (row.definition_identity) String(out, *row.definition_identity);
      else out += "null";
      out += ",\"weight_q64\":";
      Number(out, row.weight_q64);
      out += '}';
    }
    out += ']';
  }
  out += ",\"reason\":";
  Reason(out, s->reason);
  out += '}';
}

inline void Branch291e210(std::string &out,
                         const std::optional<game::ContextSource291e210V1> &a) {
  if (!a) { out += "null"; return; }
  out += "{\"status\":";
  String(out, a->status);
  out += ",\"ready\":";
  out += a->ready ? "true" : "false";
  out += ",\"component_present\":";
  Boolean(out, a->component_present);
  out += ",\"first_relation_resolution\":";
  Resolution(out, a->first_relation_resolution);
  out += ",\"second_relation_resolution\":";
  Resolution(out, a->second_relation_resolution);
  out += ",\"house_resolution\":";
  Resolution(out, a->house_resolution);
  out += ",\"house_extra_enabled\":";
  Boolean(out, a->house_extra_enabled);
  out += ",\"selected_lifestyle_span\":";
  WeightedSpan(out, a->selected_lifestyle_span);
  out += ",\"selected_dynasty_span\":";
  WeightedSpan(out, a->selected_dynasty_span);
  out += ",\"selected_house_span\":";
  WeightedSpan(out, a->selected_house_span);
  out += ",\"selected_house_extra_span\":";
  WeightedSpan(out, a->selected_house_extra_span);
  out += ",\"definition_blocks\":[";
  for (std::size_t i = 0; i < a->definition_blocks.size(); ++i) {
    if (i) out += ',';
    const auto &block = a->definition_blocks[i];
    out += "{\"definition_identity\":";
    String(out, block.definition_identity);
    out += ",\"properties\":";
    Properties(out, block.properties);
    out += '}';
  }
  out += "],\"reason\":";
  Reason(out, a->reason);
  out += '}';
}

inline void Identity(std::string &out, const std::optional<std::string> &value) {
  if (value) String(out, *value);
  else out += "null";
}

template <typename Row, typename Append>
inline void Rows(std::string &out,
                 const std::optional<std::vector<Row>> &rows, Append append) {
  if (!rows) { out += "null"; return; }
  out += '[';
  for (std::size_t i = 0; i < rows->size(); ++i) {
    if (i) out += ',';
    append(out, (*rows)[i]);
  }
  out += ']';
}

inline void ConditionalA(std::string &out,
                         const game::ContextSourceConditionalAV1 &row) {
  out += "{\"native_index\":" + std::to_string(row.native_index);
  out += ",\"key_identity\":";
  Identity(out, row.key_identity);
  out += ",\"key_object_id\":";
  Number(out, row.key_object_id);
  out += ",\"key_object_magic\":";
  Number(out, row.key_object_magic);
  out += ",\"property_block\":";
  Properties(out, row.property_block);
  out += ",\"admitted\":";
  Boolean(out, row.admitted);
  out += ",\"reason\":";
  Reason(out, row.reason);
  out += '}';
}

inline void ConditionalB(std::string &out,
                         const game::ContextSourceConditionalBV1 &row) {
  out += "{\"native_index\":" + std::to_string(row.native_index);
  out += ",\"key_i32\":";
  Number(out, row.key_i32);
  out += ",\"property_block\":";
  Properties(out, row.property_block);
  out += ",\"admitted\":";
  Boolean(out, row.admitted);
  out += ",\"reason\":";
  Reason(out, row.reason);
  out += '}';
}

inline void ConditionalC(std::string &out,
                         const game::ContextSourceConditionalCV1 &row) {
  out += "{\"native_index\":" + std::to_string(row.native_index);
  out += ",\"source_key_u32\":";
  Number(out, row.source_key_u32);
  out += ",\"masked_index_u32\":";
  Number(out, row.masked_index_u32);
  out += ",\"resolver_count_i32\":";
  Number(out, row.resolver_count_i32);
  out += ",\"selected_native_fallback\":";
  Boolean(out, row.selected_native_fallback);
  out += ",\"invert_u8\":";
  Number(out, row.invert_u8);
  out += ",\"property_block\":";
  Properties(out, row.property_block);
  out += ",\"resolved_condition_identity\":";
  Identity(out, row.resolved_condition_identity);
  out += ",\"condition_source\":";
  String(out, row.condition_source);
  out += ",\"condition_length\":";
  Number(out, row.condition_length);
  out += ",\"condition_capacity\":";
  Number(out, row.condition_capacity);
  out += ",\"condition_bytes\":";
  Numbers(out, row.condition_bytes);
  out += ",\"first_signed_byte\":";
  Number(out, row.first_signed_byte);
  out += ",\"classifier_mode_i32\":";
  Number(out, row.classifier_mode_i32);
  out += ",\"classifier_result_i32\":";
  Number(out, row.classifier_result_i32);
  out += ",\"condition_token_id\":";
  Number(out, row.condition_token_id);
  out += ",\"admitted\":";
  Boolean(out, row.admitted);
  out += ",\"token_origin\":";
  String(out, row.token_origin);
  out += ",\"lookup_status\":";
  String(out, row.lookup_status);
  out += ",\"reason\":";
  Reason(out, row.reason);
  out += '}';
}

inline void SourceRow(std::string &out, const game::ContextSourceSourceRowV1 &row) {
  out += "{\"native_index\":" + std::to_string(row.native_index);
  out += ",\"source_identity\":";
  Identity(out, row.source_identity);
  out += ",\"base_properties\":";
  Properties(out, row.base_properties);
  out += ",\"auxiliary_410_provenance\":";
  String(out, row.auxiliary_410_provenance);
  out += ",\"auxiliary_retained_identity\":";
  Identity(out, row.auxiliary_retained_identity);
  out += ",\"auxiliary_retained_present\":";
  Boolean(out, row.auxiliary_retained_present);
  out += ",\"auxiliary_tag_u32\":";
  Number(out, row.auxiliary_tag_u32);
  out += ",\"conditional_a_count\":";
  Number(out, row.conditional_a_count);
  out += ",\"conditional_b_count\":";
  Number(out, row.conditional_b_count);
  out += ",\"conditional_c_count\":";
  Number(out, row.conditional_c_count);
  out += ",\"conditional_a_rows\":";
  Rows(out, row.conditional_a_rows, ConditionalA);
  out += ",\"conditional_b_rows\":";
  Rows(out, row.conditional_b_rows, ConditionalB);
  out += ",\"conditional_c_rows\":";
  Rows(out, row.conditional_c_rows, ConditionalC);
  out += ",\"reason\":";
  Reason(out, row.reason);
  out += '}';
}

inline void Branch291d7e0(std::string &out,
                         const std::optional<game::ContextSource291d7e0V1> &b) {
  if (!b) { out += "null"; return; }
  out += "{\"status\":";
  String(out, b->status);
  out += ",\"ready\":";
  out += b->ready ? "true" : "false";
  out += ",\"base_inputs_ready\":";
  out += b->base_inputs_ready ? "true" : "false";
  out += ",\"component_present\":";
  Boolean(out, b->component_present);
  out += ",\"selected_source\":";
  String(out, b->selected_source);
  out += ",\"source_count\":";
  Number(out, b->source_count);
  out += ",\"source_rows\":";
  Rows(out, b->source_rows, SourceRow);
  out += ",\"conditional_a_fallback_properties\":";
  Properties(out, b->conditional_a_fallback_properties);
  out += ",\"government_token_count\":";
  Number(out, b->government_token_count);
  out += ",\"government_token_ids_i32\":";
  Numbers(out, b->government_token_ids_i32);
  out += ",\"government_source\":";
  String(out, b->government_source);
  out += ",\"condition_registry_guard\":";
  Number(out, b->condition_registry_guard);
  out += ",\"condition_fallback_guard\":";
  Number(out, b->condition_fallback_guard);
  out += ",\"token_manager_present\":";
  Boolean(out, b->token_manager_present);
  out += ",\"reason\":";
  Reason(out, b->reason);
  out += '}';
}

}  // namespace battle_context_source_inputs_v1_detail

// Same-frame current source operands; this is not a prepared context postimage.
inline std::string SerializeBattleCurrentPersonContextSourceInputsV1(
    const game::BattleCurrentPersonContextSourceInputsSnapshotV1 &p) {
  using namespace battle_context_source_inputs_v1_detail;
  std::string out = "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":" + std::to_string(p.character_id);
  out += ",\"branch_291e210\":";
  Branch291e210(out, p.branch_291e210);
  out += ",\"branch_291d7e0\":";
  Branch291d7e0(out, p.branch_291d7e0);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
  return out;
}

}  // namespace xar::bridge
