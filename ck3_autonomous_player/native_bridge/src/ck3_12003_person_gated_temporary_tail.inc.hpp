// Included in the existing source collector's anonymous namespace.
// Frozen source tree + FINAL raw schema precede this numeric-only observer.
template <typename T> void GatedFinish(T &out) {
  out.ready = out.reason.empty();
  out.status = out.ready ? "available" : "partial";
}
std::int32_t GatedSigned32(std::uint32_t raw) {
  std::int32_t result{};
  std::memcpy(&result, &raw, sizeof(result));
  return result;
}
std::int32_t GatedPlusOne(std::int32_t value) {
  return GatedSigned32(static_cast<std::uint32_t>(value) + 1U);
}
game::ContextSourceGatedNamedLiteralV1 GatedNamedLiteral(
    const ContextSourceBindingsV1 &b, std::int32_t slot,
    std::vector<const void *> &identities) {
  game::ContextSourceGatedNamedLiteralV1 out(slot);
  out.kind = "missing";
  out.reason.clear();
  const auto fail = [&](const char *reason) {
    out.reason = reason; GatedFinish(out); return out;
  };
  const auto db = Read<const void *>(b, b.gated_temporary_tail.named_db_slot);
  if (!db || !*db) return fail("gated_named_db_unavailable");
  const auto entries = Read<const void *>(b, *db, 0xEF0);
  if (!entries || !*entries) return fail("gated_named_entries_unavailable");
  const auto entry = Read<const void *>(b, *entries, static_cast<std::size_t>(slot));
  if (!entry || !*entry) return fail("gated_named_entry_unavailable");
  out.entry_identity = Identity(identities, *entry, "gated");
  // The evaluator tests tree70 before any fixed flag/raw operand.
  const auto tree = Read<const void *>(b, *entry, 0x70);
  if (!tree) return fail("gated_named_tree_unavailable");
  out.tree_present = *tree != nullptr;
  if (*tree) {
    out.tree_identity = Identity(identities, *tree, "gated");
    out.kind = "dynamic_tree_requires_current_result";
    return fail("dynamic_tree_requires_current_result");
  }
  out.fixed_flag_u8 = Read<std::uint8_t>(b, *entry, 0x7B);
  if (!out.fixed_flag_u8) return fail("gated_named_fixed_flag_unavailable");
  if (*out.fixed_flag_u8 == 0U) {
    out.kind = "known_zero";
    out.value_q64 = 0;
  } else {
    out.raw_fixed_q64 = Read<std::int64_t>(b, *entry, 0x68);
    if (!out.raw_fixed_q64) return fail("gated_named_raw_fixed_unavailable");
    out.kind = "literal";
    out.value_q64 = out.raw_fixed_q64;
  }
  GatedFinish(out);
  return out;
}
game::ContextSourceGatedRefreshV1 GatedRefresh168(
    const ContextSourceBindingsV1 &b, std::vector<const void *> &identities) {
  game::ContextSourceGatedRefreshV1 out{};
  out.reason.clear();
  const auto fail = [&](const char *reason) {
    out.reason = reason; GatedFinish(out); return out;
  };
  out.source = GatedNamedLiteral(b, 0x168, identities);
  if (!out.source.ready) return fail("gated_refresh_168_source_unavailable");
  out.minimum_q64 = Read<std::int64_t>(b, b.gated_temporary_tail.minimum_slot);
  if (!out.minimum_q64) return fail("gated_refresh_minimum_unavailable");
  if (*out.source.value_q64 < *out.minimum_q64) {
    out.clamped_q64 = out.minimum_q64;
  } else {
    out.maximum_q64 = Read<std::int64_t>(b, b.gated_temporary_tail.maximum_slot);
    if (!out.maximum_q64) return fail("gated_refresh_maximum_unavailable");
    out.clamped_q64 = *out.source.value_q64 > *out.maximum_q64
        ? out.maximum_q64 : out.source.value_q64;
  }
  out.threshold_count = Read<std::int32_t>(b, b.gated_temporary_tail.threshold_count_slot);
  if (!out.threshold_count) return fail("gated_refresh_threshold_count_unavailable");
  out.thresholds_consumed_q64.emplace();
  if (*out.threshold_count <= 0) {
    out.fresh_rank_raw = out.threshold_count;
  } else {
    const auto data = Read<const void *>(b, b.gated_temporary_tail.threshold_pointer_slot);
    if (!data) return fail("gated_refresh_threshold_pointer_unavailable");
    out.threshold_array_present = *data != nullptr;
    out.fresh_rank_raw = out.threshold_count;
    for (std::int32_t i = 0; i < *out.threshold_count; ++i) {
      const auto threshold = Read<std::int64_t>(b, *data, static_cast<std::size_t>(i) * 8);
      if (!threshold) {
        out.fresh_rank_raw.reset();
        return fail("gated_refresh_threshold_value_unavailable");
      }
      out.thresholds_consumed_q64->push_back(*threshold);
      if (*out.clamped_q64 <= *threshold) { out.fresh_rank_raw = i; break; }
    }
  }
  GatedFinish(out);
  return out;
}
game::ContextSourceGatedPrefixV1 GatedPrefix(
    const ContextSourceBindingsV1 &b, std::int32_t selector, std::size_t offset,
    std::vector<const void *> &identities) {
  game::ContextSourceGatedPrefixV1 out{};
  out.reason.clear();
  out.selector_raw = selector;
  out.native_prefix_count = GatedPlusOne(selector);
  const auto fail = [&](const char *reason) {
    Reason(out.reason, reason); GatedFinish(out); return out;
  };
  // FE20 tests wrapped N before its first header read at291FFB4.
  if (*out.native_prefix_count <= 0) {
    out.rows.emplace();
    GatedFinish(out);
    return out;
  }
  const auto provider = Read<const void *>(b, b.gated_temporary_tail.provider_slot);
  if (!provider || !*provider) return fail("gated_prefix_provider_unavailable");
  const void *header = Offset(*provider, offset);
  out.header_count = Read<std::int32_t>(b, header, 0xC);
  if (!out.header_count) return fail("gated_prefix_header_count_unavailable");
  if (*out.native_prefix_count > *out.header_count) {
    out.rows.emplace();
    GatedFinish(out);
    return out;
  }
  const auto data = Read<const void *>(b, header);
  if (!data) return fail("gated_prefix_array_unavailable");
  out.array_present = *data != nullptr;
  if (!*data) return fail("gated_prefix_array_null");
  out.rows.emplace();
  for (std::int32_t i = 0; i < *out.native_prefix_count; ++i) {
    game::ContextSourceGatedPrefixRowV1 row{};
    row.native_index = i;
    const auto definition = Read<const void *>(b, *data, static_cast<std::size_t>(i) * 8);
    if (!definition || !*definition) row.reason = "gated_prefix_definition_unavailable";
    else {
      row.definition_identity = Identity(identities, *definition, "gated");
      row.magic_raw = Read<std::uint32_t>(b, *definition, 0x38);
      if (!row.magic_raw) row.reason = "gated_prefix_magic_unavailable";
      else {
        row.admitted = *row.magic_raw == 0x4744624FU;
        if (*row.admitted) {
          const void *pc = Offset(*definition, 0x40);
          row.property_identity = Identity(identities, pc, "gated");
          row.property_block = Properties(b, pc);
          if (!PropertiesReady(*row.property_block))
            row.reason = "gated_prefix_properties_unavailable";
        }
      }
    }
    if (!row.reason.empty()) Reason(out.reason, row.reason.c_str());
    out.rows->push_back(std::move(row));
  }
  GatedFinish(out);
  return out;
}
void GatedEmptyPrefix(game::ContextSourceGatedPrefixV1 &out) {
  out.reason.clear();
  out.rows.emplace();
  GatedFinish(out);
}
game::ContextSourceGatedDeltaV1 GatedDelta(
    const ContextSourceBindingsV1 &b, const std::optional<std::int32_t> &selected,
    const game::ContextSourceGatedRefreshV1 &refresh,
    std::vector<const void *> &identities) {
  game::ContextSourceGatedDeltaV1 out{};
  out.reason.clear();
  const auto fail = [&](const char *reason) {
    out.reason = reason; GatedFinish(out); return out;
  };
  if (!selected) return fail("gated_delta_selected_operand_unavailable");
  if (!refresh.ready || !refresh.fresh_rank_raw)
    return fail("gated_delta_fresh_rank_unavailable");
  out.delta_raw = GatedSigned32(static_cast<std::uint32_t>(*selected) -
                              static_cast<std::uint32_t>(*refresh.fresh_rank_raw));
  if (*out.delta_raw == 0) {
    out.header_selection = "zero_delta";
    GatedEmptyPrefix(out.prefix);
    GatedFinish(out);
    return out;
  }
  const auto raw = static_cast<std::uint32_t>(*out.delta_raw);
  out.absolute_delta_raw = GatedSigned32(*out.delta_raw < 0 ? 0U - raw : raw);
  out.header_selection = *out.delta_raw > 0 ? "provider_1420" : "provider_14a8";
  out.prefix = GatedPrefix(b, *out.absolute_delta_raw,
                          *out.delta_raw > 0 ? 0x1420U : 0x14A8U, identities);
  if (!out.prefix.ready) return fail("gated_delta_prefix_unavailable");
  bool needs_weight = false;
  for (const auto &row : *out.prefix.rows)
    if (row.admitted == true && row.property_block &&
        row.property_block->keys_count && *row.property_block->keys_count > 0)
      needs_weight = true;
  // Source executes its evaluator before bounds. Numeric empty contribution
  // readiness does not claim that evaluation activity or fabricate a weight.
  if (needs_weight) {
    out.weight_source = GatedNamedLiteral(b, 0x170, identities);
    if (!out.weight_source.ready) return fail("gated_delta_weight_source_unavailable");
  }
  GatedFinish(out);
  return out;
}

const void *GatedResolveCharacter(const ContextSourceBindingsV1 &b,
    const std::optional<const void *> &store, std::int32_t key, bool helper,
    game::ContextSourceGatedResolutionV1 &out,
    std::vector<const void *> &identities) {
  out.requested_full_id_raw = key;
  if (!store) { out.reason = "gated_character_registry_unavailable"; return nullptr; }
  out.registry_present = *store != nullptr;
  bool use_fallback = !helper;
  const void *object = nullptr;
  if (!*store) {
    out.selection = "registry_absent";
    if (helper) { out.admitted = false; return nullptr; }
  } else {
    out.capacity_u32 = Read<std::uint32_t>(b, *store, 0x2C);
    if (!out.capacity_u32) { out.reason = "gated_character_capacity_unavailable"; return nullptr; }
    const auto index = static_cast<std::uint32_t>(key) & 0xFFFFFFU;
    if (index >= *out.capacity_u32) {
      out.selection = "out_of_capacity";
      if (helper) { out.admitted = false; return nullptr; }
    } else {
      const auto table = Read<const void *>(b, *store, 0x20);
      const auto indexed = table ? Read<const void *>(b, *table,
          static_cast<std::size_t>(index) * 16 + 8) : std::nullopt;
      if (!indexed) { out.reason = "gated_character_indexed_pointer_unavailable"; return nullptr; }
      out.indexed_pointer_present = *indexed != nullptr;
      if (*indexed) {
        out.indexed_full_id_raw = Read<std::int32_t>(b, *indexed, 0x18);
        if (!out.indexed_full_id_raw) { out.reason = "gated_character_indexed_id_unavailable"; return nullptr; }
        if (*out.indexed_full_id_raw == key) {
          object = *indexed;
          out.selection = "indexed_full_id";
          use_fallback = false;
        } else use_fallback = true;
      } else use_fallback = true;
    }
  }
  if (use_fallback) {
    const auto fallback = Read<const void *>(b, b.gated_temporary_tail.character_fallback_slot);
    if (!fallback) { out.reason = "gated_character_fallback_unavailable"; return nullptr; }
    object = *fallback;
    out.selection = "native_fallback";
  }
  if (!object) { out.reason = "gated_character_selected_null"; return nullptr; }
  out.object_identity = Identity(identities, object, "gated");
  out.magic_raw = Read<std::uint32_t>(b, object, 0x1C);
  if (!out.magic_raw) { out.reason = "gated_character_magic_unavailable"; return nullptr; }
  if (*out.magic_raw != 0x43686172U) { out.admitted = false; return object; }
  out.full_id_raw = Read<std::int32_t>(b, object, 0x18);
  if (!out.full_id_raw) { out.reason = "gated_character_id_unavailable"; return nullptr; }
  out.admitted = *out.full_id_raw != -1;
  return object;
}
const void *GatedRelatedSelection(const ContextSourceBindingsV1 &b,
    const void *character, const std::optional<bool> &current_land,
    game::ContextSourceGatedRelatedV1 &out,
    std::vector<const void *> &identities) {
  const auto carrier = Read<const void *>(b, character, 0x1B8);
  if (!carrier) { out.reason = "gated_related_carrier_unavailable"; return nullptr; }
  out.carrier_present = *carrier != nullptr;
  if (!*carrier) {
    out.helper_return_full_id_raw = -1;
  } else {
    const auto store = Read<const void *>(b, b.gated_temporary_tail.character_storage_slot);
    if (!store) { out.reason = "gated_related_helper_registry_unavailable"; return nullptr; }
    for (const auto offset : {0xCCU, 0xC8U}) {
      game::ContextSourceGatedResolutionV1 row{};
      row.native_index = static_cast<std::int32_t>(out.attempts.size());
      const auto key = Read<std::int32_t>(b, *carrier, offset);
      if (!key) row.reason = "gated_related_helper_key_unavailable";
      else GatedResolveCharacter(b, store, *key, true, row, identities);
      if (!row.reason.empty()) out.reason = row.reason;
      const bool accepted = row.admitted == true;
      out.attempts.push_back(std::move(row));
      if (!out.reason.empty()) return nullptr;
      if (accepted) { out.helper_return_full_id_raw = key; break; }
    }
    if (!out.helper_return_full_id_raw) {
      if (!current_land) { out.reason = "gated_related_self_land_unavailable"; return nullptr; }
      if (*current_land) {
        out.self_full_id_raw = Read<std::int32_t>(b, character, 0x18);
        if (!out.self_full_id_raw) { out.reason = "gated_related_self_id_unavailable"; return nullptr; }
        out.helper_return_full_id_raw = out.self_full_id_raw;
      } else out.helper_return_full_id_raw = -1;
    }
  }
  // Caller performs its own resolution even for helper-return FFFFFFFF.
  const auto store = Read<const void *>(b, b.gated_temporary_tail.character_storage_slot);
  const auto *related = GatedResolveCharacter(b, store, *out.helper_return_full_id_raw,
                                            false, out.caller, identities);
  if (!out.caller.reason.empty()) { out.reason = out.caller.reason; return nullptr; }
  if (out.caller.admitted != true) return nullptr;
  const auto land = Read<const void *>(b, related, 0x1C0);
  if (!land) { out.reason = "gated_related_land_unavailable"; return nullptr; }
  out.land_present = *land != nullptr;
  if (!*land) { out.selected_present = false; return nullptr; }
  const auto selected = Read<const void *>(b, *land, 0x458);
  if (!selected) { out.reason = "gated_related_selected_unavailable"; return nullptr; }
  out.selected_present = *selected != nullptr;
  return *selected;
}
game::ContextSourceGatedListV1 GatedList(const ContextSourceBindingsV1 &b,
    const void *character, const void *current_selected,
    const std::optional<bool> &current_land, const std::optional<bool> &selected_present,
    std::vector<const void *> &identities) {
  game::ContextSourceGatedListV1 out{};
  out.reason.clear();
  const auto fail = [&](const char *reason) {
    Reason(out.reason, reason); GatedFinish(out); return out;
  };
  if (!selected_present) return fail("gated_list_current_selection_unavailable");
  const void *selected = current_selected;
  const bool related = !*selected_present;
  if (related) {
    selected = GatedRelatedSelection(b, character, current_land, out.related, identities);
    if (!out.related.reason.empty()) return fail(out.related.reason.c_str());
    if (!selected) {
      out.selection = "related_skip";
      out.rows.emplace();
      GatedFinish(out);
      return out;
    }
  }
  out.selection = related ? "related_BE0" : "current_A20";
  out.count_raw = Read<std::int32_t>(b, selected, 0x114);
  if (!out.count_raw) return fail("gated_list_count_unavailable");
  if (*out.count_raw < 0 && !related) return fail("gated_list_current_negative_count");
  if (*out.count_raw <= 0) {
    out.rows.emplace();
    GatedFinish(out);
    return out;
  }
  const auto data = Read<const void *>(b, selected, 0x108);
  if (!data) return fail("gated_list_array_unavailable");
  out.array_present = *data != nullptr;
  if (!*data) return fail("gated_list_array_null");
  out.rows.emplace();
  for (std::int32_t i = 0; i < *out.count_raw; ++i) {
    game::ContextSourceGatedListRowV1 row{};
    row.native_index = i;
    const auto object = Read<const void *>(b, *data, static_cast<std::size_t>(i) * 8);
    if (!object || !*object) row.reason = "gated_list_object_unavailable";
    else {
      const void *pc = Offset(*object, related ? 0xBE0U : 0xA20U);
      row.property_identity = Identity(identities, pc, "gated");
      row.property_block = Properties(b, pc);
      if (!PropertiesReady(*row.property_block)) row.reason = "gated_list_properties_unavailable";
    }
    if (!row.reason.empty()) Reason(out.reason, row.reason.c_str());
    out.rows->push_back(std::move(row));
  }
  GatedFinish(out);
  return out;
}
void GatedSkipTemporaries(game::ContextSourceGatedTemporaryTail291c7a7V1 &out) {
  out.refresh_168.reason.clear();
  GatedFinish(out.refresh_168);
  GatedEmptyPrefix(out.prefix_1398);
  out.delta_prefix_1420_14a8.reason.clear();
  GatedEmptyPrefix(out.delta_prefix_1420_14a8.prefix);
  GatedFinish(out.delta_prefix_1420_14a8);
}
game::ContextSourceGatedTemporaryTail291c7a7V1 GatedTemporaryTail291c7a7Inputs(
    const ContextSourceBindingsV1 &b, const void *character, std::int32_t character_id) {
  game::ContextSourceGatedTemporaryTail291c7a7V1 out{};
  out.character_id = character_id;
  out.reason.clear();
  std::vector<const void *> identities;
  const auto finish = [&]() {
    if (!out.prefix_1398.ready || !out.delta_prefix_1420_14a8.ready || !out.list.ready)
      Reason(out.reason, "gated_temporary_tail_families_partial");
    GatedFinish(out);
    return out;
  };
  const auto global = Read<const void *>(b, b.gated_temporary_tail.global_flag_slot);
  if (global && *global) out.global_flag_u8 = Read<std::uint8_t>(b, *global, 0x2B0);
  if (!out.global_flag_u8) {
    out.reason = "gated_temporary_tail_bit20_unavailable";
    return finish();
  }
  out.global_bit20 = (*out.global_flag_u8 & 0x20U) != 0U;
  if (!*out.global_bit20) {
    out.temporary_admitted = false;
    GatedSkipTemporaries(out);
    out.list.selection = "skipped_bit20";
    out.list.reason.clear();
    out.list.rows.emplace();
    GatedFinish(out.list);
    return finish();
  }
  const auto land = Read<const void *>(b, character, 0x1C0);
  const void *selected = nullptr;
  if (land) {
    out.current_land_present = *land != nullptr;
    if (!*land) out.current_selected_present = false;
    else {
      const auto link = Read<const void *>(b, *land, 0x458);
      if (link) { selected = *link; out.current_selected_present = selected != nullptr; }
    }
  }
  out.temporary_admitted = out.current_selected_present;
  if (out.temporary_admitted == false) GatedSkipTemporaries(out);
  else if (out.temporary_admitted == true) {
    out.selected_ec_raw = Read<std::int32_t>(b, selected, 0xEC);
    out.selector_global_raw = Read<std::int32_t>(b, b.gated_temporary_tail.selector_global_slot);
    std::optional<std::int32_t> chosen;
    if (out.selected_ec_raw && out.selector_global_raw) {
      if (*out.selected_ec_raw == *out.selector_global_raw) {
        out.selected_f8_raw = Read<std::int32_t>(b, selected, 0xF8);
        chosen = out.selected_f8_raw;
      } else {
        out.selected_e8_raw = Read<std::int32_t>(b, selected, 0xE8);
        chosen = out.selected_e8_raw;
      }
    }
    out.refresh_168 = GatedRefresh168(b, identities);
    if (chosen) out.prefix_1398 = GatedPrefix(b, *chosen, 0x1398, identities);
    else out.prefix_1398.reason = "gated_prefix_selected_operand_unavailable";
    out.delta_prefix_1420_14a8 = GatedDelta(b, chosen, out.refresh_168, identities);
  }
  out.list = GatedList(b, character, selected, out.current_land_present,
                       out.current_selected_present, identities);
  return finish();
}
