// Included inside xar::game after the existing current-table JSON helpers.
namespace current_candidate_mapper_json_detail {
template <class Number, class JsonString>
inline void CountInput(std::string &out, const ArmyCandidateMapperCountInputV1 &p,
                       Number number, JsonString string) {
  using namespace daily_assault_table_json_detail;
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Integer("native_index", p.native_index); w.Text("regi_identity", p.regi_identity); w.Status(p);
  w.Integer("count_base_128_raw_i32", p.count_base_128_raw_i32);
  w.Key("chunks"); out += '[';
  for (std::size_t i = 0; i < p.chunks.size(); ++i) {
    if (i) out += ',';
    out += '{'; Writer<Number, JsonString> c{out, number, string};
    const auto &chunk = p.chunks[i]; c.Integer("physical_index", chunk.physical_index);
    c.Integer("maximum_00_raw_i32", chunk.maximum_00_raw_i32);
    c.Integer("current_04_raw_i32", chunk.current_04_raw_i32);
    c.Integer("state_18_raw_i32", chunk.state_18_raw_i32); out += '}';
  }
  out += "]}";
}
template <class Number, class JsonString>
inline void Mapper(std::string &out, const ArmyCandidateDetachmentMapperV1 &p,
                   Number number, JsonString string) {
  using namespace daily_assault_table_json_detail;
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Integer("native_index", p.native_index); w.Text("arrg_identity", p.arrg_identity); w.Status(p);
  w.Integer("kind_14c_raw_i32", p.kind_14c_raw_i32); w.Integer("data_count_raw_i32", p.data_count_raw_i32);
  w.Text("first_data_record_identity", p.first_data_record_identity);
  w.Integer("first_regi_full_id_u32", p.first_regi_full_id_u32);
  w.Key("selected_regi_resolution");
  if (p.selected_regi_resolution) Resolution(out, *p.selected_regi_resolution, number, string);
  else out += "null";
  w.Integer("selected_regi_magic_14_raw_u32", p.selected_regi_magic_14_raw_u32);
  w.Boolean("selected_regi_identity_valid", p.selected_regi_identity_valid);
  w.Integer("count_input_index", p.count_input_index); w.Text("fallback_regi_identity", p.fallback_regi_identity);
  w.Boolean("return_selection_ready", p.return_selection_ready); w.Text("return_selection", p.return_selection);
  w.Text("returned_regi_identity", p.returned_regi_identity);
  w.Integer("returned_regi_full_id_u32", p.returned_regi_full_id_u32);
  w.Integer("returned_regi_magic_14_raw_u32", p.returned_regi_magic_14_raw_u32);
  w.Integer("returned_state_138_raw_i32", p.returned_state_138_raw_i32);
  w.Text("return_basis", p.return_basis); out += '}';
}
} // namespace current_candidate_mapper_json_detail
template <class Number, class JsonString>
inline void AppendArmyCurrentCandidateDetachmentMapperInputsV1(std::string &out,
    const ArmyCurrentCandidateDetachmentMapperInputsV1 &p, Number number, JsonString string) {
  using namespace daily_assault_table_json_detail;
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Integer("schema_version", p.schema_version); w.Text("source", p.source); w.Text("stage", p.stage); w.Status(p);
  w.Boolean("selection_ready", p.selection_ready); w.Text("selection_branch", p.selection_branch);
  w.Integer("candidate_reference_native_index", p.candidate_reference_native_index);
  w.Integer("candidate_pending_native_index", p.candidate_pending_native_index);
  w.Integer("candidate_raw_full_id_u32", p.candidate_raw_full_id_u32);
  w.Integer("candidate_actual_full_id_u32", p.candidate_actual_full_id_u32);
  w.Text("candidate_army_identity", p.candidate_army_identity);
  w.Integer("roster_count_raw_i32", p.roster_count_raw_i32); w.Boolean("roster_data_present", p.roster_data_present);
  w.Text("roster_data_identity", p.roster_data_identity); w.Boolean("roster_ready", p.roster_ready);
  w.Key("occurrences"); out += '[';
  for (std::size_t i = 0; i < p.occurrences.size(); ++i) {
    if (i) out += ',';
    const auto &row = p.occurrences[i]; out += '{'; Writer<Number, JsonString> r{out, number, string};
    r.Integer("native_index", row.native_index); r.Integer("raw_full_id_u32", row.raw_full_id_u32); r.Status(row);
    r.Key("resolution"); Resolution(out, row.resolution, number, string);
    r.Integer("mapper_index", row.mapper_index); out += '}';
  }
  out += ']'; w.Key("mappers"); out += '[';
  for (std::size_t i = 0; i < p.mappers.size(); ++i) {
    if (i) out += ',';
    current_candidate_mapper_json_detail::Mapper(out, p.mappers[i], number, string);
  }
  out += ']'; w.Key("count_inputs"); out += '[';
  for (std::size_t i = 0; i < p.count_inputs.size(); ++i) {
    if (i) out += ',';
    current_candidate_mapper_json_detail::CountInput(out, p.count_inputs[i], number, string);
  }
  out += "]}";
}
