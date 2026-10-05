// Included inside bridge::battle_context_source_inputs_v1_detail after Rows.
template <typename T>
inline void ListPredicate2530dd0NumberField(std::string &out, const char *name,
                                          const std::optional<T> &value) {
  out += ",\"";
  out += name;
  out += "\":";
  Number(out, value);
}
inline void ListPredicate2530dd0BoolField(std::string &out, const char *name,
                                        const std::optional<bool> &value) {
  out += ",\"";
  out += name;
  out += "\":";
  Boolean(out, value);
}
inline void ListPredicate2530dd0ScopeJson(std::string &out,
    const std::optional<game::ContextSourceListPredicate2530dd0ScopeV1> &scope) {
  if (!scope) { out += "null"; return; }
  out += "{\"root_scope_kind_u32\":";
  Number(out, scope->root_scope_kind_u32);
  ListPredicate2530dd0NumberField(out, "root_character_full_id_u32", scope->root_character_full_id_u32);
  ListPredicate2530dd0NumberField(out, "named_scope_kind_u32", scope->named_scope_kind_u32);
  ListPredicate2530dd0NumberField(out, "named_selected_full_id_u32", scope->named_selected_full_id_u32);
  ListPredicate2530dd0NumberField(out, "named_binding_key_i32", scope->named_binding_key_i32);
  ListPredicate2530dd0NumberField(out, "trigger_object", scope->trigger_object);
  ListPredicate2530dd0NumberField(out, "trigger_vtable", scope->trigger_vtable);
  ListPredicate2530dd0NumberField(out, "trigger_evaluator_function", scope->trigger_evaluator_function);
  out += '}';
}
inline void ListPredicate2530dd0RowJson(std::string &out,
    const game::ContextSourceListPredicate2530dd0RowV1 &row) {
  out += "{\"native_index\":" + std::to_string(row.native_index);
  ListPredicate2530dd0NumberField(out, "key_u32", row.key_u32);
  out += ",\"ready\":";
  out += row.ready ? "true" : "false";
  out += ",\"resolution_selection\":";
  Identity(out, row.resolution_selection);
  ListPredicate2530dd0NumberField(out, "selected_object", row.selected_object);
  ListPredicate2530dd0NumberField(out, "selected_full_id_u32", row.selected_full_id_u32);
  ListPredicate2530dd0BoolField(out, "used_fallback", row.used_fallback);
  ListPredicate2530dd0NumberField(out, "predicate_receiver", row.predicate_receiver);
  ListPredicate2530dd0NumberField(out, "magic_u32", row.magic_u32);
  ListPredicate2530dd0NumberField(out, "condition_count_raw_i32", row.condition_count_raw_i32);
  ListPredicate2530dd0BoolField(out, "predicate_result", row.predicate_result);
  out += ",\"pc_selection\":";
  Identity(out, row.pc_selection);
  out += ",\"scope_inputs\":";
  ListPredicate2530dd0ScopeJson(out, row.scope_inputs);
  out += ",\"properties\":";
  Properties(out, row.properties);
  out += ",\"reason\":";
  Reason(out, row.reason);
  out += '}';
}
inline void ListPredicate2530dd0Json(std::string &out,
    const game::ContextSourceListPredicate2530dd0InputsV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":" + std::to_string(p.character_id);
  ListPredicate2530dd0BoolField(out, "scratch_present", p.scratch_present);
  out += ",\"header_selection\":";
  Identity(out, p.header_selection);
  ListPredicate2530dd0NumberField(out, "default_header_guard_raw", p.default_header_guard_raw);
  ListPredicate2530dd0BoolField(out, "source_array_present", p.source_array_present);
  ListPredicate2530dd0NumberField(out, "source_count_raw", p.source_count_raw);
  out += ",\"rows\":";
  Rows(out, p.rows, ListPredicate2530dd0RowJson);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
