// Included in the context-source collector's anonymous namespace.
// Frozen source tree precedes this readonly reconstruction. No native calls.
template <typename T> void MiddleFinish(T &out) {
  out.ready = out.reason.empty();
  out.status = out.ready ? "available" : "partial";
}
std::int64_t MiddleWeight(std::int64_t value) {
  const std::uint64_t raw = static_cast<std::uint64_t>(value) + 100000U;
  std::int64_t result{};
  std::memcpy(&result, &raw, sizeof(result));
  return result;
}
void MiddleWeightSource(const ContextSourceBindingsV1 &b, const void *character,
    const void *component, game::ContextSourceMiddleRankFamilyV1 &out,
    std::vector<const void *> &ids) {
  const auto &m = b.middle_helpers;
  const void *pc = nullptr;
  if (component) {
    const auto carrier = Read<const void *>(b, component, 0x258);
    if (!carrier) { Reason(out.reason, "middle_weight_carrier_unavailable"); return; }
    out.weight_carrier_present = *carrier != nullptr;
    if (*carrier) {
      const auto owner = Read<const void *>(b, *carrier, 8);
      if (!owner) { Reason(out.reason, "middle_weight_owner_unavailable"); return; }
      out.weight_owner_matches = *owner == character;
      if (*out.weight_owner_matches) {
        pc = Offset(*carrier, 0x10);
        out.weight_source_selection = "exact_owner_carrier_10";
      }
    }
  }
  if (!pc) {
    pc = m.weight_default_pc;
    out.weight_source_selection = "inline_weight_default_5d67b90";
    out.weight_default_guard_raw = Read<std::int32_t>(b, m.weight_default_guard_slot);
    if (!out.weight_default_guard_raw || *out.weight_default_guard_raw == 0 ||
        *out.weight_default_guard_raw == -1)
      Reason(out.reason, out.weight_default_guard_raw
          ? "middle_weight_default_not_initialized" : "middle_weight_default_guard_unavailable");
  }
  out.weight_source_identity = Identity(ids, pc, "middle");
  out.weight_keys_count_raw = Read<std::int32_t>(b, pc, 0x74);
  const auto keys = Read<const void *>(b, pc, 0x68);
  if (!out.weight_keys_count_raw || !keys) {
    Reason(out.reason, "middle_weight_key_header_unavailable"); return;
  }
  if (*out.weight_keys_count_raw < 0) {
    Reason(out.reason, "middle_weight_negative_key_count"); return;
  }
  out.weight_key_probes.emplace();
  std::int32_t lower = 0, remaining = *out.weight_keys_count_raw;
  const auto probe = [&](std::int32_t index) -> std::optional<std::uint16_t> {
    const auto key = Read<std::uint16_t>(b, *keys, static_cast<std::size_t>(index) * 2);
    if (key) out.weight_key_probes->push_back({index, *key});
    else Reason(out.reason, "middle_weight_key_probe_unavailable");
    return key;
  };
  while (remaining > 0) {
    const auto half = remaining / 2;
    const auto key = probe(lower + half);
    if (!key) return;
    if (*key < out.weight_key_u16) { lower += remaining - half; remaining = half; }
    else remaining = half;
  }
  out.weight_found = false;
  if (lower != *out.weight_keys_count_raw) {
    const auto key = probe(lower);
    if (!key) { out.weight_found.reset(); return; }
    out.weight_found = *key == out.weight_key_u16;
  }
  if (*out.weight_found) {
    out.weight_native_index = lower;
    const auto values = Read<const void *>(b, pc, 0xD0);
    if (values) out.weight_value_q64 = Read<std::int64_t>(
        b, *values, static_cast<std::size_t>(lower) * 8);
    if (!out.weight_value_q64) {
      Reason(out.reason, "middle_weight_value_unavailable"); return;
    }
  }
  out.weight_q64 = MiddleWeight(out.weight_value_q64.value_or(0));
}
game::ContextSourceMiddleRankFamilyV1 MiddleRank(const ContextSourceBindingsV1 &b,
    const void *character, const std::optional<const void *> &component, int index,
    std::vector<const void *> &ids) {
  game::ContextSourceMiddleRankFamilyV1 out{};
  out.native_index = index;
  constexpr std::size_t scores[] = {0x138, 0x118, 0x158, 0x178};
  constexpr std::size_t overrides[] = {0x140, 0x120, 0x160, 0x180};
  constexpr std::size_t arrays[] = {0x10C0, 0x1058, 0x1128, 0x1190};
  constexpr std::size_t counts[] = {0x10CC, 0x1064, 0x1134, 0x119C};
  constexpr std::uint16_t keys[] = {45, 44, 46, 47};
  out.weight_key_u16 = keys[index];
  const auto fail = [&](const char *reason) {
    Reason(out.reason, reason); MiddleFinish(out); return out;
  };
  if (!component) return fail("middle_rank_component_unavailable");
  std::int32_t rank = 0;
  if (*component) {
    out.score_q64 = Read<std::int64_t>(b, *component, scores[index]);
    out.override_raw = Read<std::int32_t>(b, *component, overrides[index]);
    out.threshold_count = Read<std::int32_t>(b, b.middle_helpers.threshold_count_slots[index]);
    if (!out.score_q64 || !out.override_raw || !out.threshold_count)
      return fail("middle_rank_operands_unavailable");
    out.thresholds_consumed_q64.emplace();
    if (*out.threshold_count > 0) {
      const auto data = Read<const void *>(b, b.middle_helpers.threshold_pointer_slots[index]);
      if (!data) return fail("middle_rank_threshold_pointer_unavailable");
      out.threshold_array_present = *data != nullptr;
      for (std::int32_t i = 0; i < *out.threshold_count; ++i) {
        const auto threshold = Read<std::int64_t>(b, *data, static_cast<std::size_t>(i) * 8);
        if (!threshold) return fail("middle_rank_threshold_unavailable");
        out.thresholds_consumed_q64->push_back(*threshold);
        if (*out.score_q64 < *threshold) break;
        ++rank;
      }
    }
    if (*out.override_raw >= 0 && rank > *out.override_raw) rank = *out.override_raw;
  }
  out.rank_raw = rank;
  const auto manager = Read<const void *>(b, b.middle_helpers.manager_slot);
  if (!manager || !*manager) return fail("middle_rank_manager_unavailable");
  const void *definition = nullptr;
  if (rank >= 0) {
    out.manager_count_raw = Read<std::int32_t>(b, *manager, counts[index]);
    if (!out.manager_count_raw) return fail("middle_rank_manager_count_unavailable");
    if (rank < *out.manager_count_raw) {
      const auto data = Read<const void *>(b, *manager, arrays[index]);
      const auto selected = data ? Read<const void *>(b, *data, static_cast<std::size_t>(rank) * 8)
                                 : std::nullopt;
      if (!selected) return fail("middle_rank_definition_unavailable");
      definition = *selected;
      out.definition_selection = "manager_rank_index";
    }
  }
  if (!out.definition_selection) {
    const auto fallback = Read<const void *>(b, b.middle_helpers.rank_fallback_slot);
    if (!fallback) return fail("middle_rank_fallback_unavailable");
    definition = *fallback;
    out.definition_selection = "native_rank_fallback";
  }
  out.definition_identity = Identity(ids, definition, "middle");
  out.definition_gate_raw = Read<std::int32_t>(b, definition, 0x4C);
  if (!out.definition_gate_raw) return fail("middle_rank_definition_gate_unavailable");
  out.admitted = *out.definition_gate_raw != 0;
  if (*out.admitted) {
    MiddleWeightSource(b, character, *component, out, ids);
    const auto *pc = Offset(definition, 0x40);
    out.property_identity = Identity(ids, pc, "middle");
    out.property_block = Properties(b, pc);
    if (!PropertiesReady(*out.property_block))
      Reason(out.reason, "middle_rank_definition_properties_unavailable");
  }
  MiddleFinish(out);
  return out;
}
game::ContextSourceMiddle260V1 Middle260(const ContextSourceBindingsV1 &b,
    const void *character, std::vector<const void *> &ids) {
  game::ContextSourceMiddle260V1 out{};
  const auto component = Read<const void *>(b, character, 0x1B0);
  if (component) out.component_present = *component != nullptr;
  for (int i = 0; i < 4; ++i) {
    out.families.push_back(MiddleRank(b, character, component, i, ids));
    if (!out.families.back().ready) Reason(out.reason, "middle_rank_families_partial");
  }
  MiddleFinish(out);
  return out;
}
bool MiddleSubcGate(const ContextSourceBindingsV1 &b, const void *context,
    std::optional<std::uint32_t> &magic, std::optional<std::int32_t> &full_id,
    std::optional<bool> &admitted, std::string &reason) {
  magic = Read<std::uint32_t>(b, context, 0xC);
  if (!magic) { Reason(reason, "middle_subc_magic_unavailable"); return false; }
  if (*magic != 0x5362436FU) { admitted = false; return true; }
  full_id = Read<std::int32_t>(b, context, 8);
  if (!full_id) { Reason(reason, "middle_subc_full_id_unavailable"); return false; }
  admitted = *full_id != -1;
  return true;
}
void MiddleGather(const ContextSourceBindingsV1 &b, const void *character,
    const void *context, game::ContextSourceMiddleContextV1 &out,
    std::vector<const void *> &ids) {
  out.context_identity = Identity(ids, context, "middle");
  if (!MiddleSubcGate(b, context, out.magic_raw, out.full_id_raw, out.admitted, out.reason)) return;
  if (out.admitted != true) { out.modifier_rows.emplace(); return; }
  const auto owner = Read<const void *>(b, context, 0x20);
  if (owner) out.owner_full_id_raw = Read<std::int32_t>(b, *owner, 0x18);
  out.character_full_id_raw = Read<std::int32_t>(b, character, 0x18);
  if (!out.owner_full_id_raw || !out.character_full_id_raw) {
    Reason(out.reason, "middle_subc_owner_ids_unavailable"); return;
  }
  out.owner_matches = *out.owner_full_id_raw == *out.character_full_id_raw;
  out.modifier_count = Read<std::int32_t>(b, context, 0x44);
  if (!out.modifier_count) Reason(out.reason, "middle_subc_modifier_count_unavailable");
  else if (*out.modifier_count <= 0) out.modifier_rows.emplace();
  else {
    const auto modifiers = Read<const void *>(b, context, 0x38);
    const auto tokens = Read<const void *>(b, context, 0x68);
    if (modifiers) out.modifier_array_present = *modifiers != nullptr;
    if (tokens) out.token_array_present = *tokens != nullptr;
    if (!modifiers || !tokens) Reason(out.reason, "middle_subc_modifier_headers_unavailable");
    else {
      out.modifier_rows.emplace();
      for (std::int32_t i = 0; i < *out.modifier_count; ++i) {
        game::ContextSourceMiddleModifierV1 row{};
        row.native_index = i;
        const auto object = Read<const void *>(b, *modifiers, static_cast<std::size_t>(i) * 8);
        row.token_u8 = Read<std::uint8_t>(b, *tokens, i);
        if (object) {
          row.modifier_identity = Identity(ids, *object, "middle");
          row.modifier_count_u8 = Read<std::uint8_t>(b, *object, 0x1EC);
        }
        if (!object || !row.token_u8 || !row.modifier_count_u8)
          row.reason = "middle_subc_modifier_operands_unavailable";
        else {
          const void *base = nullptr;
          if (*row.modifier_count_u8 > *row.token_u8) {
            const auto data = Read<const void *>(b, *object, 0x1E0);
            if (data) base = Offset(*data, static_cast<std::size_t>(*row.token_u8) * 0x1A30);
            row.base_selection = "token_indexed";
          } else {
            const auto fallback = Read<const void *>(b, b.middle_helpers.modifier_default_base_slot);
            if (fallback) base = *fallback;
            row.base_selection = "native_modifier_fallback";
          }
          const auto *pc = Offset(base, *out.owner_matches ? 0x13C8 : 0x1208);
          row.property_identity = Identity(ids, pc, "middle");
          row.gate_raw = Read<std::int32_t>(b, pc, 0xC);
          if (!row.gate_raw) row.reason = "middle_subc_modifier_pc_gate_unavailable";
          else {
            row.admitted = *row.gate_raw != 0;
            if (*row.admitted) {
              row.property_block = Properties(b, pc);
              if (!PropertiesReady(*row.property_block)) row.reason = "middle_subc_modifier_properties_unavailable";
            }
          }
        }
        if (!row.reason.empty()) Reason(out.reason, row.reason.c_str());
        out.modifier_rows->push_back(std::move(row));
      }
    }
  }
  // This unconditional terminal remains observable even if modifier rows fail.
  const auto terminal_link = Read<const void *>(b, context, 0x30);
  const auto terminal_base = terminal_link ? Read<const void *>(b, *terminal_link, 0x50) : std::nullopt;
  const auto *pc = terminal_base ? Offset(*terminal_base, *out.owner_matches ? 0x1400 : 0x1240) : nullptr;
  if (!terminal_base || !pc) Reason(out.reason, "middle_subc_terminal_pointer_unavailable");
  else {
    out.terminal_property_identity = Identity(ids, pc, "middle");
    out.terminal_property_block = Properties(b, pc);
    if (!PropertiesReady(*out.terminal_property_block)) Reason(out.reason, "middle_subc_terminal_properties_unavailable");
  }
}
const void *MiddleSubcResolve(const ContextSourceBindingsV1 &b, const void *key_address,
    game::ContextSourceMiddleContextV1 &out) {
  const auto store = Read<const void *>(b, b.middle_helpers.subc_registry_slot);
  if (!store) { out.reason = "middle_subc_registry_unavailable"; return nullptr; }
  if (*store) {
    out.requested_full_id_raw = Read<std::int32_t>(b, key_address);
    if (!out.requested_full_id_raw) { out.reason = "middle_subc_requested_id_unavailable"; return nullptr; }
    const auto index = static_cast<std::uint32_t>(*out.requested_full_id_raw) & 0xFFFFFFU;
    const auto capacity = Read<std::uint32_t>(b, *store, 0x2C);
    if (!capacity) { out.reason = "middle_subc_registry_capacity_unavailable"; return nullptr; }
    if (index < *capacity) {
      const auto table = Read<const void *>(b, *store, 0x20);
      const auto selected = table ? Read<const void *>(b, *table, static_cast<std::size_t>(index) * 16 + 8) : std::nullopt;
      if (!selected) { out.reason = "middle_subc_registry_slot_unavailable"; return nullptr; }
      if (*selected) {
        const auto full = Read<std::int32_t>(b, *selected, 8);
        if (!full) { out.reason = "middle_subc_registry_id_unavailable"; return nullptr; }
        if (*full == *out.requested_full_id_raw) {
          out.selection = "registry_full_id_8"; return *selected;
        }
      }
    }
  }
  const auto fallback = Read<const void *>(b, b.middle_helpers.subc_fallback_slot);
  if (!fallback) { out.reason = "middle_subc_fallback_unavailable"; return nullptr; }
  out.selection = "native_subc_fallback";
  return *fallback;
}
game::ContextSourceMiddleContextFamilyV1 MiddlePreferred(const ContextSourceBindingsV1 &b,
    const void *character, const std::optional<const void *> &land,
    std::vector<const void *> &ids) {
  game::ContextSourceMiddleContextFamilyV1 out{};
  out.header_selection = "preferred_context";
  out.count = 1;
  out.rows.emplace();
  game::ContextSourceMiddleContextV1 row{};
  const void *context = nullptr;
  if (!land) row.reason = "middle_subc_land_unavailable";
  else if (*land) {
    for (const auto offset : {0x1C0U, 0x1C8U}) {
      const auto candidate = Read<const void *>(b, *land, offset);
      if (!candidate) { row.reason = "middle_subc_preferred_pointer_unavailable"; break; }
      std::optional<std::uint32_t> magic;
      std::optional<std::int32_t> full_id;
      std::optional<bool> admitted;
      if (!MiddleSubcGate(b, *candidate, magic, full_id, admitted, row.reason)) break;
      if (admitted == true) {
        context = *candidate;
        row.selection = offset == 0x1C0U ? "land_1c0" : "land_1c8";
        break;
      }
    }
  }
  if (land && !context && row.reason.empty()) {
    const auto fallback = Read<const void *>(b, b.middle_helpers.subc_fallback_slot);
    if (!fallback) row.reason = "middle_subc_fallback_unavailable";
    else { context = *fallback; row.selection = "native_subc_fallback"; }
  }
  if (row.reason.empty()) MiddleGather(b, character, context, row, ids);
  MiddleFinish(row);
  if (!row.ready) out.reason = row.reason;
  out.rows->push_back(std::move(row));
  MiddleFinish(out);
  return out;
}
game::ContextSourceMiddleContextFamilyV1 MiddleContextList(const ContextSourceBindingsV1 &b,
    const void *character, const std::optional<const void *> &land, std::size_t offset,
    std::vector<const void *> &ids) {
  game::ContextSourceMiddleContextFamilyV1 out{};
  if (!land) { out.reason = "middle_subc_land_unavailable"; MiddleFinish(out); return out; }
  const void *header = *land ? Offset(*land, offset) : b.middle_helpers.null_land_list_header;
  out.header_selection = *land ? (offset == 0x218 ? "land_218" : "land_248") : "inline_null_land_54596d8";
  const auto data = Read<const void *>(b, header);
  if (data) out.array_present = *data != nullptr;
  out.count = Read<std::int32_t>(b, header, 0xC);
  if (!data || !out.count) out.reason = "middle_subc_list_header_unavailable";
  else if (*out.count < 0) out.reason = "middle_subc_list_negative_count";
  else {
    out.rows.emplace();
    for (std::int32_t i = 0; i < *out.count; ++i) {
      game::ContextSourceMiddleContextV1 row{};
      row.native_index = i;
      const auto *context = MiddleSubcResolve(b, Offset(*data, static_cast<std::size_t>(i) * 4), row);
      if (row.reason.empty()) MiddleGather(b, character, context, row, ids);
      MiddleFinish(row);
      if (!row.ready) Reason(out.reason, row.reason.c_str());
      out.rows->push_back(std::move(row));
    }
  }
  MiddleFinish(out);
  return out;
}
game::ContextSourceMiddleFb10V1 MiddleFb10(const ContextSourceBindingsV1 &b,
    const void *character, std::vector<const void *> &ids) {
  game::ContextSourceMiddleFb10V1 out{};
  const auto land = Read<const void *>(b, character, 0x1C0);
  if (land) out.land_present = *land != nullptr;
  out.preferred = MiddlePreferred(b, character, land, ids);
  out.list_218 = MiddleContextList(b, character, land, 0x218, ids);
  out.list_248 = MiddleContextList(b, character, land, 0x248, ids);
  if (!out.preferred.ready || !out.list_218.ready || !out.list_248.ready)
    out.reason = "middle_subc_families_partial";
  MiddleFinish(out);
  return out;
}
game::ContextSourceMiddleHelpersV1 MiddleHelpers(const ContextSourceBindingsV1 &b,
    const void *character, std::int32_t character_id) {
  game::ContextSourceMiddleHelpersV1 out{};
  out.character_id = character_id;
  std::vector<const void *> ids;
  out.helper_291f260 = Middle260(b, character, ids);
  out.helper_291fb10 = MiddleFb10(b, character, ids);
  if (!out.helper_291f260.ready || !out.helper_291fb10.ready)
    out.reason = "middle_helper_families_partial";
  MiddleFinish(out);
  return out;
}
