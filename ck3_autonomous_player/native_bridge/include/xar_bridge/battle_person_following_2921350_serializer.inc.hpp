// Included inside the existing context-source serializer detail namespace.

inline void Following2921350TitleSourceJson(std::string &out, const game::ContextSourceFollowing2921350TitleSourceV1 &p) {
  out += '{';
  out += "\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"carrier_present\":";
  Boolean(out, p.carrier_present);
  out += ",\"selection\":";
  HelperString(out, p.selection);
  out += ",\"header_identity\":";
  HelperString(out, p.header_identity);
  out += ",\"count_raw\":";
  Number(out, p.count_raw);
  out += ",\"array_present\":";
  Boolean(out, p.array_present);
  out += ",\"full_ids_u32\":";
  Numbers(out, p.full_ids_u32);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Following2921350TitleWalkJson(std::string &out, const game::ContextSourceFollowing2921350TitleWalkV1 &p) {
  out += '{';
  out += "\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"root_index\":";
  out += std::to_string(p.root_index);
  out += ",\"parent_index\":";
  Number(out, p.parent_index);
  out += ",\"requested_full_id_u32\":";
  Number(out, p.requested_full_id_u32);
  out += ",\"selection\":";
  HelperString(out, p.selection);
  out += ",\"selected_full_id_u32\":";
  Number(out, p.selected_full_id_u32);
  out += ",\"title_identity\":";
  HelperString(out, p.title_identity);
  out += ",\"definition_identity\":";
  HelperString(out, p.definition_identity);
  out += ",\"tier_raw_i32\":";
  Number(out, p.tier_raw_i32);
  out += ",\"children_count_raw\":";
  Number(out, p.children_count_raw);
  out += ",\"children_array_present\":";
  Boolean(out, p.children_array_present);
  out += ",\"child_ids_u32\":";
  Numbers(out, p.child_ids_u32);
  out += ",\"collected\":";
  Boolean(out, p.collected);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Following2921350MapProbeJson(std::string &out, const game::ContextSourceFollowing2921350MapProbeV1 &p) {
  out += '{';
  out += "\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"bucket_index_i64\":";
  Number(out, p.bucket_index_i64);
  out += ",\"distance_raw_u8\":";
  Number(out, p.distance_raw_u8);
  out += ",\"key_raw_u32\":";
  Number(out, p.key_raw_u32);
  out += ",\"operand_q64\":";
  Number(out, p.operand_q64);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Following2921350MapJson(std::string &out, const game::ContextSourceFollowing2921350MapV1 &p) {
  out += '{';
  out += "\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"data_identity\":";
  HelperString(out, p.data_identity);
  out += ",\"mask_raw_i32\":";
  Number(out, p.mask_raw_i32);
  out += ",\"overflow_raw_u8\":";
  Number(out, p.overflow_raw_u8);
  out += ",\"probes\":";
  out += '[';
  for (std::size_t i = 0; i < p.probes.size(); ++i) {
    if (i) out += ',';
    Following2921350MapProbeJson(out, p.probes[i]);
  }
  out += ']';
  out += ",\"found\":";
  Boolean(out, p.found);
  out += ",\"operand_q64\":";
  Number(out, p.operand_q64);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Following2921350TierJson(std::string &out, const game::ContextSourceFollowing2921350TierV1 &p) {
  out += '{';
  out += "\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"count_raw_i32\":";
  Number(out, p.count_raw_i32);
  out += ",\"data_identity\":";
  HelperString(out, p.data_identity);
  out += ",\"thresholds_q64\":";
  Numbers(out, p.thresholds_q64);
  out += ",\"selected_index_raw_i32\":";
  Number(out, p.selected_index_raw_i32);
  out += ",\"selection\":";
  HelperString(out, p.selection);
  out += ",\"default_guard_raw_i32\":";
  Number(out, p.default_guard_raw_i32);
  out += ",\"pc\":";
  AfterPcJson(out, p.pc);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Following2921350SourceJson(std::string &out, const game::ContextSourceFollowing2921350SourceV1 &p) {
  out += '{';
  out += "\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"requested_full_id_u32\":";
  Number(out, p.requested_full_id_u32);
  out += ",\"selection\":";
  HelperString(out, p.selection);
  out += ",\"selected_full_id_u32\":";
  Number(out, p.selected_full_id_u32);
  out += ",\"object_identity\":";
  HelperString(out, p.object_identity);
  out += ",\"definition_identity\":";
  HelperString(out, p.definition_identity);
  out += ",\"group_index_raw_i32\":";
  Number(out, p.group_index_raw_i32);
  out += ",\"map\":";
  Following2921350MapJson(out, p.map);
  out += ",\"tiers\":";
  Following2921350TierJson(out, p.tiers);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Following2921350ProvinceStepJson(std::string &out, const game::ContextSourceFollowing2921350ProvinceStepV1 &p) {
  out += '{';
  out += "\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"title_identity\":";
  HelperString(out, p.title_identity);
  out += ",\"definition_identity\":";
  HelperString(out, p.definition_identity);
  out += ",\"tier_raw_i32\":";
  Number(out, p.tier_raw_i32);
  out += ",\"requested_full_id_u32\":";
  Number(out, p.requested_full_id_u32);
  out += ",\"selection\":";
  HelperString(out, p.selection);
  out += ",\"selected_full_id_u32\":";
  Number(out, p.selected_full_id_u32);
  out += ",\"first_child_count_raw\":";
  Number(out, p.first_child_count_raw);
  out += ",\"first_child_array_present\":";
  Boolean(out, p.first_child_array_present);
  out += ",\"first_child_full_id_u32\":";
  Number(out, p.first_child_full_id_u32);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Following2921350ProvinceJson(std::string &out, const game::ContextSourceFollowing2921350ProvinceV1 &p) {
  out += '{';
  out += "\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"title_walk_index\":";
  out += std::to_string(p.title_walk_index);
  out += ",\"steps\":";
  out += '[';
  for (std::size_t i = 0; i < p.steps.size(); ++i) {
    if (i) out += ',';
    Following2921350ProvinceStepJson(out, p.steps[i]);
  }
  out += ']';
  out += ",\"province_identity\":";
  HelperString(out, p.province_identity);
  out += ",\"magic_u32\":";
  Number(out, p.magic_u32);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"full_id_u32\":";
  Number(out, p.full_id_u32);
  out += ",\"source_count_raw\":";
  Number(out, p.source_count_raw);
  out += ",\"source_array_present\":";
  Boolean(out, p.source_array_present);
  out += ",\"source_ids_u32\":";
  Numbers(out, p.source_ids_u32);
  out += ",\"sources\":";
  out += '[';
  for (std::size_t i = 0; i < p.sources.size(); ++i) {
    if (i) out += ',';
    Following2921350SourceJson(out, p.sources[i]);
  }
  out += ']';
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Following2921350ManagerJson(std::string &out, const game::ContextSourceFollowing2921350ManagerV1 &p) {
  out += '{';
  out += "\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"loaded\":";
  Boolean(out, p.loaded);
  out += ",\"identity\":";
  HelperString(out, p.identity);
  out += ",\"group_count_raw_i32\":";
  Number(out, p.group_count_raw_i32);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Following2921350Json(std::string &out, const game::ContextSourceFollowing2921350InputsV1 &p) {
  out += '{';
  out += "\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":";
  out += std::to_string(p.character_id);
  out += ",\"character_identity\":";
  HelperString(out, p.character_identity);
  out += ",\"source_scope\":";
  String(out, p.source_scope);
  out += ",\"title_source\":";
  Following2921350TitleSourceJson(out, p.title_source);
  out += ",\"title_walk\":";
  out += '[';
  for (std::size_t i = 0; i < p.title_walk.size(); ++i) {
    if (i) out += ',';
    Following2921350TitleWalkJson(out, p.title_walk[i]);
  }
  out += ']';
  out += ",\"provinces\":";
  out += '[';
  for (std::size_t i = 0; i < p.provinces.size(); ++i) {
    if (i) out += ',';
    Following2921350ProvinceJson(out, p.provinces[i]);
  }
  out += ']';
  out += ",\"manager\":";
  Following2921350ManagerJson(out, p.manager);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
