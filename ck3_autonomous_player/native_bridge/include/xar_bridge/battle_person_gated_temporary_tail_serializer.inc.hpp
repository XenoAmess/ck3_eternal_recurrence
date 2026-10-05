// Included inside the existing context-source serializer detail namespace.
inline void GatedNamedLiteralJson(std::string &out, const game::ContextSourceGatedNamedLiteralV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"slot_offset\":";
  out += std::to_string(p.slot_offset);
  out += ",\"entry_identity\":";
  HelperString(out, p.entry_identity);
  out += ",\"tree_present\":";
  Boolean(out, p.tree_present);
  out += ",\"tree_identity\":";
  HelperString(out, p.tree_identity);
  out += ",\"fixed_flag_u8\":";
  Number(out, p.fixed_flag_u8);
  out += ",\"raw_fixed_q64\":";
  Number(out, p.raw_fixed_q64);
  out += ",\"value_q64\":";
  Number(out, p.value_q64);
  out += ",\"kind\":";
  String(out, p.kind);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void GatedRefreshJson(std::string &out, const game::ContextSourceGatedRefreshV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"source\":";
  GatedNamedLiteralJson(out, p.source);
  out += ",\"minimum_q64\":";
  Number(out, p.minimum_q64);
  out += ",\"maximum_q64\":";
  Number(out, p.maximum_q64);
  out += ",\"clamped_q64\":";
  Number(out, p.clamped_q64);
  out += ",\"threshold_count\":";
  Number(out, p.threshold_count);
  out += ",\"threshold_array_present\":";
  Boolean(out, p.threshold_array_present);
  out += ",\"thresholds_consumed_q64\":";
  if (!p.thresholds_consumed_q64) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.thresholds_consumed_q64->size(); ++i) {
      if (i) out += ',';
      out += std::to_string(p.thresholds_consumed_q64->at(i));
    }
    out += ']';
  }
  out += ",\"fresh_rank_raw\":";
  Number(out, p.fresh_rank_raw);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void GatedPrefixRowJson(std::string &out, const game::ContextSourceGatedPrefixRowV1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"definition_identity\":";
  HelperString(out, p.definition_identity);
  out += ",\"magic_raw\":";
  Number(out, p.magic_raw);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"property_identity\":";
  HelperString(out, p.property_identity);
  out += ",\"property_block\":";
  Properties(out, p.property_block);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void GatedPrefixJson(std::string &out, const game::ContextSourceGatedPrefixV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"selector_raw\":";
  Number(out, p.selector_raw);
  out += ",\"native_prefix_count\":";
  Number(out, p.native_prefix_count);
  out += ",\"header_count\":";
  Number(out, p.header_count);
  out += ",\"array_present\":";
  Boolean(out, p.array_present);
  out += ",\"rows\":";
  if (!p.rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.rows->size(); ++i) {
      if (i) out += ',';
      GatedPrefixRowJson(out, p.rows->at(i));
    }
    out += ']';
  }
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void GatedDeltaJson(std::string &out, const game::ContextSourceGatedDeltaV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"delta_raw\":";
  Number(out, p.delta_raw);
  out += ",\"absolute_delta_raw\":";
  Number(out, p.absolute_delta_raw);
  out += ",\"header_selection\":";
  HelperString(out, p.header_selection);
  out += ",\"weight_source\":";
  GatedNamedLiteralJson(out, p.weight_source);
  out += ",\"prefix\":";
  GatedPrefixJson(out, p.prefix);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void GatedResolutionJson(std::string &out, const game::ContextSourceGatedResolutionV1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"requested_full_id_raw\":";
  Number(out, p.requested_full_id_raw);
  out += ",\"registry_present\":";
  Boolean(out, p.registry_present);
  out += ",\"capacity_u32\":";
  Number(out, p.capacity_u32);
  out += ",\"indexed_pointer_present\":";
  Boolean(out, p.indexed_pointer_present);
  out += ",\"indexed_full_id_raw\":";
  Number(out, p.indexed_full_id_raw);
  out += ",\"selection\":";
  HelperString(out, p.selection);
  out += ",\"object_identity\":";
  HelperString(out, p.object_identity);
  out += ",\"magic_raw\":";
  Number(out, p.magic_raw);
  out += ",\"full_id_raw\":";
  Number(out, p.full_id_raw);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void GatedRelatedJson(std::string &out, const game::ContextSourceGatedRelatedV1 &p) {
  out += "{\"carrier_present\":";
  Boolean(out, p.carrier_present);
  out += ",\"attempts\":";
  out += '[';
  for (std::size_t i = 0; i < p.attempts.size(); ++i) {
    if (i) out += ',';
    GatedResolutionJson(out, p.attempts.at(i));
  }
  out += ']';
  out += ",\"self_full_id_raw\":";
  Number(out, p.self_full_id_raw);
  out += ",\"helper_return_full_id_raw\":";
  Number(out, p.helper_return_full_id_raw);
  out += ",\"caller\":";
  GatedResolutionJson(out, p.caller);
  out += ",\"land_present\":";
  Boolean(out, p.land_present);
  out += ",\"selected_present\":";
  Boolean(out, p.selected_present);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void GatedListRowJson(std::string &out, const game::ContextSourceGatedListRowV1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"property_identity\":";
  HelperString(out, p.property_identity);
  out += ",\"property_block\":";
  Properties(out, p.property_block);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void GatedListJson(std::string &out, const game::ContextSourceGatedListV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"selection\":";
  HelperString(out, p.selection);
  out += ",\"related\":";
  GatedRelatedJson(out, p.related);
  out += ",\"count_raw\":";
  Number(out, p.count_raw);
  out += ",\"array_present\":";
  Boolean(out, p.array_present);
  out += ",\"rows\":";
  if (!p.rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.rows->size(); ++i) {
      if (i) out += ',';
      GatedListRowJson(out, p.rows->at(i));
    }
    out += ']';
  }
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void GatedTemporaryTail291c7a7Json(std::string &out, const game::ContextSourceGatedTemporaryTail291c7a7V1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":";
  out += std::to_string(p.character_id);
  out += ",\"global_flag_u8\":";
  Number(out, p.global_flag_u8);
  out += ",\"global_bit20\":";
  Boolean(out, p.global_bit20);
  out += ",\"current_land_present\":";
  Boolean(out, p.current_land_present);
  out += ",\"current_selected_present\":";
  Boolean(out, p.current_selected_present);
  out += ",\"temporary_admitted\":";
  Boolean(out, p.temporary_admitted);
  out += ",\"selected_ec_raw\":";
  Number(out, p.selected_ec_raw);
  out += ",\"selector_global_raw\":";
  Number(out, p.selector_global_raw);
  out += ",\"selected_e8_raw\":";
  Number(out, p.selected_e8_raw);
  out += ",\"selected_f8_raw\":";
  Number(out, p.selected_f8_raw);
  out += ",\"refresh_168\":";
  GatedRefreshJson(out, p.refresh_168);
  out += ",\"prefix_1398\":";
  GatedPrefixJson(out, p.prefix_1398);
  out += ",\"delta_prefix_1420_14a8\":";
  GatedDeltaJson(out, p.delta_prefix_1420_14a8);
  out += ",\"list\":";
  GatedListJson(out, p.list);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
