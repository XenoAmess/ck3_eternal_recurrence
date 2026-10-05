#pragma once

#include "xar_bridge/battle_context_source_inputs_v1.hpp"
#include "xar_bridge/battle_context_admissions_v86_serializer.hpp"

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

inline void Pre291e2101640(
    std::string &out,
    const std::optional<game::ContextSourcePre291e2101640V1> &p) {
  if (!p) { out += "null"; return; }
  out += "{\"status\":";
  String(out, p->status);
  out += ",\"ready\":";
  out += p->ready ? "true" : "false";
  out += ",\"character_id\":" + std::to_string(p->character_id);
  out += ",\"army_selection\":";
  if (p->army_selection) String(out, *p->army_selection);
  else out += "null";
  out += ",\"army_key_f4_raw\":";
  Number(out, p->army_key_f4_raw);
  out += ",\"army_field_120_raw\":";
  Number(out, p->army_field_120_raw);
  out += ",\"army_field_124_raw\":";
  Number(out, p->army_field_124_raw);
  out += ",\"second_selection\":";
  if (p->second_selection) String(out, *p->second_selection);
  else out += "null";
  out += ",\"second_field_174_raw\":";
  Number(out, p->second_field_174_raw);
  out += ",\"admitted\":";
  Boolean(out, p->admitted);
  out += ",\"property_block\":";
  Properties(out, p->property_block);
  out += ",\"unavailable_reason\":";
  Reason(out, p->unavailable_reason);
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

inline void LaterDirect(
    std::string &out, const game::ContextSourceLaterDirectV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":" + std::to_string(p.character_id);
  out += ",\"ordered_header_selection\":";
  if (p.ordered_header_selection) String(out, *p.ordered_header_selection);
  else out += "null";
  out += ",\"ordered_count\":";
  Number(out, p.ordered_count);
  out += ",\"ordered_array_present\":";
  Boolean(out, p.ordered_array_present);
  out += ",\"ordered_rows\":";
  if (!p.ordered_rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.ordered_rows->size(); ++i) {
      if (i) out += ',';
      const auto &r = (*p.ordered_rows)[i];
      out += "{\"native_index\":" + std::to_string(r.native_index);
      out += ",\"requested_full_id_raw\":";
      Number(out, r.requested_full_id_raw);
      out += ",\"selection\":";
      if (r.selection) String(out, *r.selection);
      else out += "null";
      out += ",\"selected_identity\":";
      if (r.selected_identity) String(out, *r.selected_identity);
      else out += "null";
      out += ",\"selected_field_24c_raw\":";
      Number(out, r.selected_field_24c_raw);
      out += ",\"admitted\":";
      Boolean(out, r.admitted);
      out += ",\"property_block\":";
      Properties(out, r.property_block);
      out += ",\"reason\":";
      Reason(out, r.reason);
      out += '}';
    }
    out += ']';
  }
  out += ",\"guarded_selection\":";
  if (p.guarded_selection) String(out, *p.guarded_selection);
  else out += "null";
  out += ",\"guarded_magic_raw\":";
  Number(out, p.guarded_magic_raw);
  out += ",\"guarded_admitted\":";
  Boolean(out, p.guarded_admitted);
  out += ",\"guarded_property_block\":";
  Properties(out, p.guarded_property_block);
  out += ",\"reason\":";
  Reason(out, p.reason);
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
  out += ",\"property_source\":";
  String(out, row.property_source);
  out += ",\"property_source_native_index\":";
  Number(out, row.property_source_native_index);
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
  out += ",\"admission_source\":";
  String(out, row.admission_source);
  out += ",\"admission_nested_native_index\":";
  Number(out, row.admission_nested_native_index);
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
  out += ",\"locale_classification\":";
  out += SerializeContextSourceLocaleClassificationV86(row.locale_classification);
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
  out += SerializeContextSourceSelectorFieldsV86(*b);
  out += ",\"reason\":";
  Reason(out, b->reason);
  out += '}';
}

#include "xar_bridge/battle_person_helper_291f0a0_serializer.inc.hpp"
#include "xar_bridge/battle_person_remaining_helpers_serializer.inc.hpp"
#include "xar_bridge/battle_person_tail_direct_serializer.inc.hpp"
#include "xar_bridge/battle_person_middle_helpers_serializer.inc.hpp"
#include "xar_bridge/battle_person_tail_prefix_serializer.inc.hpp"
#include "xar_bridge/battle_person_trait_stage_291d460_serializer.inc.hpp"
#include "xar_bridge/battle_person_absent_recipient_serializer.inc.hpp"
#include "xar_bridge/battle_person_uncached_recipient_serializer.inc.hpp"
#include "xar_bridge/battle_person_helper_2922070_serializer.inc.hpp"
#include "xar_bridge/battle_person_conference_24b1d00_serializer.inc.hpp"
#include "xar_bridge/battle_person_provider_bucket_serializer.inc.hpp"
#include "xar_bridge/battle_person_qualifier_28bc0d0_serializer.inc.hpp"
#include "xar_bridge/battle_person_list_predicate_2530dd0_serializer.inc.hpp"
#include "xar_bridge/battle_person_gated_temporary_tail_serializer.inc.hpp"
#include "xar_bridge/battle_person_after_gated_tail_serializer.inc.hpp"

}  // namespace battle_context_source_inputs_v1_detail

namespace battle_context_source_inputs_v1_detail {
template <typename T>
inline void PostAvailability(std::string &out, const T &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
}
inline void PostGuarded630(std::string &out, const game::ContextSourcePostGuarded630V1 &p) {
  PostAvailability(out, p);
  out += ",\"carrier_1b0_present\":";
  Boolean(out, p.carrier_1b0_present);
  out += ",\"carrier280_present\":";
  Boolean(out, p.carrier280_present);
  out += ",\"selection\":";
  Identity(out, p.selection);
  out += ",\"selected_field38_raw\":";
  Number(out, p.selected_field38_raw);
  out += ",\"character68_signed\":";
  Number(out, p.character68_signed);
  out += ",\"threshold_signed\":";
  Number(out, p.threshold_signed);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"property_block\":";
  Properties(out, p.property_block);
  out += ",\"unavailable_reason\":";
  Reason(out, p.unavailable_reason);
  out += '}';
}
inline void PostCarrier40(std::string &out, const game::ContextSourcePostCarrier40V1 &p) {
  PostAvailability(out, p);
  out += ",\"carrier_1b0_present\":";
  Boolean(out, p.carrier_1b0_present);
  out += ",\"carrier288_present\":";
  Boolean(out, p.carrier288_present);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"property_block\":";
  Properties(out, p.property_block);
  out += ",\"unavailable_reason\":";
  Reason(out, p.unavailable_reason);
  out += '}';
}
inline void PostOrderedD8(std::string &out, const game::ContextSourcePostOrderedD8V1 &p) {
  PostAvailability(out, p);
  out += ",\"carrier_1c0_present\":";
  Boolean(out, p.carrier_1c0_present);
  out += ",\"header_selection\":";
  Identity(out, p.header_selection);
  out += ",\"source_array_present\":";
  Boolean(out, p.source_array_present);
  out += ",\"source_count_raw\":";
  Number(out, p.source_count_raw);
  out += ",\"occurrences\":";
  Rows(out, p.occurrences, [](std::string &wire, const game::ContextSourcePostD8OccurrenceV1 &row) {
    wire += "{\"source_index\":" + std::to_string(row.source_index);
    wire += ",\"source_identity\":";
    Identity(wire, row.source_identity);
    wire += ",\"property_block\":";
    Properties(wire, row.property_block);
    wire += ",\"unavailable_reason\":";
    Reason(wire, row.unavailable_reason);
    wire += '}';
  });
  out += ",\"unavailable_reason\":";
  Reason(out, p.unavailable_reason);
  out += '}';
}
inline void Post291d7e0(std::string &out, const game::ContextSourcePost291d7e0V1 &p) {
  PostAvailability(out, p);
  out += ",\"character_id\":" + std::to_string(p.character_id);
  out += ",\"guarded630\":";
  PostGuarded630(out, p.guarded630);
  out += ",\"carrier40\":";
  PostCarrier40(out, p.carrier40);
  out += ",\"ordered_d8\":";
  PostOrderedD8(out, p.ordered_d8);
  out += ",\"unavailable_reason\":";
  Reason(out, p.unavailable_reason);
  out += '}';
}
} // namespace battle_context_source_inputs_v1_detail

// Same-frame current source operands; this is not a prepared context postimage.
inline std::string SerializeBattleCurrentPersonContextSourceInputsV1(
    const game::BattleCurrentPersonContextSourceInputsSnapshotV1 &p) {
  using namespace battle_context_source_inputs_v1_detail;
  std::string out = "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":" + std::to_string(p.character_id);
  if (p.pre_291e210_1640) {
    out += ",\"pre_291e210_1640\":";
    Pre291e2101640(out, p.pre_291e210_1640);
  }
  if (p.later_direct_291c3fb_44c) {
    out += ",\"later_direct_291c3fb_44c\":";
    LaterDirect(out, *p.later_direct_291c3fb_44c);
  }
  if (p.helper_291f0a0) {
    out += ",\"helper_291f0a0\":";
    Helper291f0a0(out, *p.helper_291f0a0);
  }
  if (p.later_helpers_291f550_291f940) {
    out += ",\"later_helpers_291f550_291f940\":";
    RemainingHelpersV1Json(out, *p.later_helpers_291f550_291f940);
  }
  if (p.tail_direct_291c5b7_291cc49) {
    out += ",\"tail_direct_291c5b7_291cc49\":";
    TailDirectV1Json(out, *p.tail_direct_291c5b7_291cc49);
  }
  if (p.middle_helpers_291f260_291fb10) {
    out += ",\"middle_helpers_291f260_291fb10\":";
    MiddleHelpersV1Json(out, *p.middle_helpers_291f260_291fb10);
  }
  if (p.tail_prefix_2753860_2922530) {
    out += ",\"tail_prefix_2753860_2922530\":";
    TailPrefixV1Json(out, *p.tail_prefix_2753860_2922530);
  }
  if (p.trait_stage_291d460) {
    out += ",\"trait_stage_291d460\":";
    TraitStage291d460V1Json(out, *p.trait_stage_291d460);
  }
  if (p.absent_recipient_inputs) {
    out += ",\"absent_recipient_inputs\":";
    AbsentRecipientV1Json(out, *p.absent_recipient_inputs);
  }
  if (p.uncached_recipient_inputs) {
    out += ",\"uncached_recipient_inputs\":";
    UncachedRecipientV1Json(out, *p.uncached_recipient_inputs);
  }
  if (p.helper_2922070) {
    out += ",\"helper_2922070\":";
    Helper2922070V1Json(out, *p.helper_2922070);
  }
  if (p.conference_24b1d00) {
    out += ",\"conference_24b1d00\":";
    Conference24b1d00V1Json(out, *p.conference_24b1d00);
  }
  if (p.provider_bucket_291c5b2) {
    out += ",\"provider_bucket_291c5b2\":";
    ProviderBucket291c5b2(out, *p.provider_bucket_291c5b2);
  }
  if (p.qualifier_28bc0d0) {
    out += ",\"qualifier_28bc0d0\":";
    Qualifier28bc0d0Json(out, *p.qualifier_28bc0d0);
  }
  if (p.list_predicate_2530dd0) {
    out += ",\"list_predicate_2530dd0\":";
    ListPredicate2530dd0Json(out, *p.list_predicate_2530dd0);
  }
  if (p.gated_temporary_tail_291c7a7) {
    out += ",\"gated_temporary_tail_291c7a7\":";
    GatedTemporaryTail291c7a7Json(out, *p.gated_temporary_tail_291c7a7);
  }
  if (p.after_gated_tail_326a8e0_2920310) {
    out += ",\"after_gated_tail_326a8e0_2920310\":";
    AfterGatedTail326a8e0And2920310Json(out, *p.after_gated_tail_326a8e0_2920310);
  }
  out += ",\"branch_291e210\":";
  Branch291e210(out, p.branch_291e210);
  out += ",\"branch_291d7e0\":";
  Branch291d7e0(out, p.branch_291d7e0);
  if (p.post_291d7e0_sources) {
    out += ",\"post_291d7e0_sources\":";
    Post291d7e0(out, *p.post_291d7e0_sources);
  }
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
  return out;
}

}  // namespace xar::bridge
