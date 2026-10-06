// Included inside xar::game after the current-table JSON helpers.
namespace current_assault_removal_json_detail {
template <class Number, typename T>
inline void Values(std::string &out, const std::optional<std::vector<T>> &values, Number number) {
  if (!values) { out += "null"; return; }
  out += '[';
  for (std::size_t i = 0; i < values->size(); ++i) {
    if (i) out += ',';
    out += number((*values)[i]);
  }
  out += ']';
}
template <class Number, class JsonString>
inline void Reference(std::string &out, const ArmyCurrentAssaultRemovalReferenceV1 &p,
                      Number number, JsonString string) {
  using namespace daily_assault_table_json_detail;
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Integer("native_index", p.native_index); w.Status(p); w.Text("reference_scope", p.reference_scope);
  w.Integer("pending_native_index", p.pending_native_index);
  w.Integer("group_native_index", p.group_native_index);
  w.Integer("group_physical_slot_i64", p.group_physical_slot_i64);
  w.Integer("group_army_native_index", p.group_army_native_index);
  w.Integer("raw_full_id_u32", p.raw_full_id_u32);
  w.Key("resolution"); Resolution(out, p.resolution, number, string);
  w.Integer("army_magic_14_raw_u32", p.army_magic_14_raw_u32);
  w.Boolean("native_army_identity_valid", p.native_army_identity_valid);
  w.Text("identity_scalar_basis", p.identity_scalar_basis);
  w.Integer("cleanup_target_index", p.cleanup_target_index); out += '}';
}
template <class Number, class JsonString>
inline void Target(std::string &out, const ArmyCurrentAssaultRemovalTargetV1 &p,
                   Number number, JsonString string) {
  using namespace daily_assault_table_json_detail;
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Integer("native_index", p.native_index); w.Integer("argument_full_id_u32", p.argument_full_id_u32); w.Status(p);
  w.Key("helper_resolution"); Resolution(out, p.helper_resolution, number, string);
  w.Integer("selected_bucket_index_u32", p.selected_bucket_index_u32);
  w.Integer("bucket_count_raw_i32", p.bucket_count_raw_i32);
  w.Boolean("bucket_data_present", p.bucket_data_present);
  w.Key("bucket_rows");
  if (!p.bucket_rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.bucket_rows->size(); ++i) {
      if (i) out += ',';
      out += '{'; Writer<Number, JsonString> r{out, number, string};
      const auto &row = (*p.bucket_rows)[i];
      r.Integer("native_index", row.native_index); r.Text("pointer_identity", row.pointer_identity);
      r.Boolean("native_same_helper_pointer", row.native_same_helper_pointer); out += '}';
    }
    out += ']';
  }
  out += '}';
}
} // namespace current_assault_removal_json_detail
template <class Number, class JsonString>
inline void AppendArmyCurrentAssaultRemovalReferenceInputsV1(std::string &out,
    const ArmyCurrentAssaultRemovalReferenceInputsV1 &p, Number number, JsonString string) {
  using namespace daily_assault_table_json_detail;
  using namespace current_assault_removal_json_detail;
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Integer("schema_version", p.schema_version); w.Text("source", p.source); w.Text("stage", p.stage);
  w.Status(p); w.Text("manager_identity", p.manager_identity);
  w.Key("observed_pending_ids_i32"); Values(out, p.observed_pending_ids_i32, number);
  w.Key("manager_id_lists"); out += '[';
  for (std::size_t i = 0; i < p.manager_id_lists.size(); ++i) {
    if (i) out += ',';
    out += '{'; Writer<Number, JsonString> c{out, number, string};
    const auto &list = p.manager_id_lists[i]; c.Text("manager_offset", list.manager_offset);
    c.Key("ordered_army_ids"); Values(out, list.ordered_army_ids, number); out += '}';
  }
  out += ']';
  w.Key("records_b0");
  if (!p.records_b0) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.records_b0->size(); ++i) {
      if (i) out += ',';
      out += '[';
      for (std::size_t j = 0; j < 4; ++j) {
        if (j) out += ',';
        out += number((*p.records_b0)[i][j]);
      }
      out += ']';
    }
    out += ']';
  }
  w.Key("reference_occurrences"); out += '[';
  for (std::size_t i = 0; i < p.reference_occurrences.size(); ++i) {
    if (i) out += ',';
    Reference(out, p.reference_occurrences[i], number, string);
  }
  out += ']'; w.Key("cleanup_targets"); out += '[';
  for (std::size_t i = 0; i < p.cleanup_targets.size(); ++i) {
    if (i) out += ',';
    current_assault_removal_json_detail::Target(out, p.cleanup_targets[i], number, string);
  }
  out += "]}";
}
