// Included after the existing B/DATA serializer definitions inside xar::game.
template<class Number, class JsonString>
inline void AppendArmyCurrentDailyAssaultLossInputsV1(std::string &out,
    const ArmyCurrentDailyAssaultLossInputsV1 &leaf, Number number, JsonString string) {
  const auto n = [&](std::string_view key, const auto &value) {
    out += ','; string(out,key); out += ':'; out += value ? number(*value) : "null";
  };
  const auto boolean = [&](std::string_view key, const auto &value) {
    out += ','; string(out,key); out += ':'; out += value ? (*value ? "true" : "false") : "null";
  };
  const auto state = [&](const auto &row) {
    out += ",\"status\":"; string(out,row.status); out += ",\"ready\":"; out += row.ready ? "true" : "false";
    out += ",\"unavailable_reason\":";
    if (row.unavailable_reason.empty()) out += "null"; else string(out,row.unavailable_reason);
  };
  const auto resolution = [&](const auto &row) {
    out += "\"resolution\":";
    daily_assault_table_json_detail::Resolution(out,row.resolution,number,string);
  };
  out += "{\"schema_version\":" + number(leaf.schema_version);
  out += ",\"source\":"; string(out,leaf.source); out += ",\"stage\":"; string(out,leaf.stage); state(leaf);
  out += ",\"groups\":["; bool first = true;
  for (const auto &group : leaf.groups) {
    if (!first) out += ','; first = false;
    out += "{\"native_index\":" + number(group.native_index) + ",\"physical_slot_i64\":" + number(group.physical_slot_i64);
    state(group); n("native_current_expected_loss",group.native_current_expected_loss); n("province_magic_raw_u32",group.province_magic_raw_u32);
    out += ",\"besieging_inputs_v1\":";
    if (group.besieging_inputs_v1) AppendArmyCurrentProvinceBesiegingContributorsV1(out,*group.besieging_inputs_v1,number,string); else out += "null";
    out += ",\"ordered_besieging_refill_inputs_v1\":";
    if (group.ordered_besieging_refill_inputs_v1)
      AppendArmyOrderedBesiegingRefillInputsV1(out,*group.ordered_besieging_refill_inputs_v1,number,string);
    else out += "null";
    out += ",\"army_counts\":["; bool first_army = true;
    for (const auto &army : group.army_counts) {
      if (!first_army) out += ','; first_army = false;
      out += "{\"native_index\":" + number(army.native_index); n("raw_full_id_u32",army.raw_full_id_u32); out += ','; resolution(army);
      state(army); n("native_whole_current_soldiers",army.native_whole_current_soldiers);
      out += ",\"regiments\":["; bool first_regiment = true;
      for (const auto &row : army.regiments) {
        if (!first_regiment) out += ','; first_regiment = false;
        out += "{\"native_index\":" + number(row.native_index); n("raw_full_id_u32",row.raw_full_id_u32); out += ','; resolution(row);
        boolean("identity_valid",row.identity_valid); n("current_soldiers",row.current_soldiers); n("maximum_soldiers",row.maximum_soldiers); out += '}';
      }
      out += "]}";
    }
    out += "]}";
  }
  out += "],\"target_regiments\":["; first = true;
  for (const auto &row : leaf.target_regiments) {
    if (!first) out += ','; first = false;
    out += '{'; resolution(row); boolean("identity_valid",row.identity_valid); state(row);
    n("current_soldiers",row.current_soldiers); n("maximum_soldiers",row.maximum_soldiers); boolean("native_loss_writer_skipped",row.native_loss_writer_skipped);
    out += ",\"replenishment_records_v1\":";
    if (row.replenishment_records_v1) AppendArmyRegimentReplenishmentRecordsSnapshotV1(out,*row.replenishment_records_v1,number,string); else out += "null";
    out += '}';
  }
  out += "]}";
}
