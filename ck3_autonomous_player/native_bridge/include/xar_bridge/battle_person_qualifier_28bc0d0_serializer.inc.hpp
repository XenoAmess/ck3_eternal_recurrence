// Included inside bridge::battle_context_source_inputs_v1_detail after Rows.
template <typename T>
inline void Qualifier28bc0d0NumberField(std::string &out, const char *name,
                                      const std::optional<T> &value) {
  out += ",\"";
  out += name;
  out += "\":";
  Number(out, value);
}
inline void Qualifier28bc0d0BoolField(std::string &out, const char *name,
                                    const std::optional<bool> &value) {
  out += ",\"";
  out += name;
  out += "\":";
  Boolean(out, value);
}
inline void Qualifier28bc0d0RelationshipJson(std::string &out,
    const game::ContextSourceQualifier28bc0d0RelationshipV1 &row) {
  out += "{\"native_index\":" + std::to_string(row.native_index);
  Qualifier28bc0d0NumberField(out, "marker_u8", row.marker_u8);
  Qualifier28bc0d0NumberField(out, "definition_object", row.definition_object);
  out += '}';
}
inline void Qualifier28bc0d0CandidateJson(std::string &out,
    const game::ContextSourceQualifier28bc0d0CandidateV1 &row) {
  out += "{\"native_index\":" + std::to_string(row.native_index);
  Qualifier28bc0d0NumberField(out, "definition_object", row.definition_object);
  Qualifier28bc0d0BoolField(out, "relationship_array_present", row.relationship_array_present);
  Qualifier28bc0d0NumberField(out, "relationship_count_raw_i32", row.relationship_count_raw_i32);
  out += ",\"relationships\":";
  Rows(out, row.relationships, Qualifier28bc0d0RelationshipJson);
  out += '}';
}
inline void Qualifier28bc0d0EvaluationJson(std::string &out,
    const game::ContextSourceQualifier28bc0d0EvaluationV1 &row) {
  out += "{\"native_index\":" + std::to_string(row.native_index);
  Qualifier28bc0d0NumberField(out, "object", row.object);
  Qualifier28bc0d0BoolField(out, "candidate_array_present", row.candidate_array_present);
  Qualifier28bc0d0NumberField(out, "candidate_count_raw_i32", row.candidate_count_raw_i32);
  out += ",\"candidates\":";
  Rows(out, row.candidates, Qualifier28bc0d0CandidateJson);
  Qualifier28bc0d0NumberField(out, "id_u32", row.id_u32);
  out += '}';
}
inline void Qualifier28bc0d0DefinitionJson(std::string &out,
    const game::ContextSourceQualifier28bc0d0DefinitionV1 &row) {
  out += "{\"native_index\":" + std::to_string(row.native_index);
  Qualifier28bc0d0NumberField(out, "definition_object", row.definition_object);
  out += ",\"ready\":";
  out += row.ready ? "true" : "false";
  out += ",\"scratch_evaluations\":";
  Rows(out, row.scratch_evaluations, Qualifier28bc0d0EvaluationJson);
  out += ",\"accepted_ids_u32\":";
  Numbers(out, row.accepted_ids_u32);
  Qualifier28bc0d0NumberField(out, "repeat_count", row.repeat_count);
  out += ",\"properties\":";
  Properties(out, row.properties);
  out += ",\"reason\":";
  Reason(out, row.reason);
  out += '}';
}
inline void Qualifier28bc0d0Json(std::string &out,
    const game::ContextSourceQualifier28bc0d0InputsV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":" + std::to_string(p.character_id);
  Qualifier28bc0d0NumberField(out, "manager_object", p.manager_object);
  Qualifier28bc0d0BoolField(out, "definition_array_present", p.definition_array_present);
  Qualifier28bc0d0NumberField(out, "definition_count_raw_i32", p.definition_count_raw_i32);
  Qualifier28bc0d0BoolField(out, "scratch_present", p.scratch_present);
  Qualifier28bc0d0NumberField(out, "scratch_count_raw_i32", p.scratch_count_raw_i32);
  Qualifier28bc0d0NumberField(out, "fallback_definition_object", p.fallback_definition_object);
  out += ",\"definitions\":";
  Rows(out, p.definitions, Qualifier28bc0d0DefinitionJson);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
