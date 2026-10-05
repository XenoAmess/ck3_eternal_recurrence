// Included after the existing source-only selector and registry helpers.
// Source tree, raw schema and default/zero-count clarifications precede code.
template <typename T> void AfterFinish(T &out) {
  out.ready = out.reason.empty();
  out.status = out.ready ? "available" : "partial";
}
std::int32_t AfterWrap32(std::uint32_t bits) {
  std::int32_t value{};
  std::memcpy(&value, &bits, sizeof(value));
  return value;
}
game::ContextSourceAfterPcV1 AfterPc(const ContextSourceBindingsV1 &b, const void *pc) {
  game::ContextSourceAfterPcV1 out{};
  if (pc) {
    out.property_identity = TraitStageIdentity(pc);
    out.property_block = Properties(b, pc);
  }
  if (!out.property_block || !PropertiesReady(*out.property_block))
    out.reason = "after_requested_property_unavailable";
  return out;
}
struct AfterReadState {
  ContextSourceBindingsV1 bindings;
  game::ContextSourceAfterGatedTail326a8e0And2920310V1 &out;
  TraitStageReadState selectors;
  AfterReadState(const ContextSourceBindingsV1 &b,
                 game::ContextSourceAfterGatedTail326a8e0And2920310V1 &value)
      : bindings(b), out(value), selectors{value.selector_inputs} {
    const auto &raw = b.after_gated_tail;
    bindings.trait_stage.selector_a_storage_slot = raw.selector_a_storage_slot;
    bindings.trait_stage.selector_a_fallback_slot = raw.selector_a_fallback_slot;
    bindings.trait_stage.selector_b_storage_slot = raw.selector_b_storage_slot;
    bindings.trait_stage.selector_b_fallback_slot = raw.selector_b_fallback_slot;
    // Used only for the source-native28C00A0 candidate gates, never the
    // composition caller or the magic-free kind owner resolution.
    bindings.gated_temporary_tail.character_storage_slot = raw.character_storage_slot;
    bindings.gated_temporary_tail.character_fallback_slot = raw.character_fallback_slot;
  }
};

const void *AfterRegistry(const ContextSourceBindingsV1 &b,
    const void *storage_slot, const void *fallback_slot, const void *key_address,
    std::size_t full_offset, const char *indexed_selection,
    std::optional<std::int32_t> &key, std::optional<std::string> &selection,
    std::optional<std::int32_t> &selected_full, std::string &reason,
    const std::optional<std::int32_t> *known_key = nullptr) {
  const auto store = Read<const void *>(b, storage_slot);
  if (!store) { Reason(reason, "after_registry_storage_unavailable"); return nullptr; }
  if (*store) {
    key = known_key ? *known_key : Read<std::int32_t>(b, key_address);
    if (!key) { Reason(reason, "after_registry_requested_id_unavailable"); return nullptr; }
    const auto capacity = Read<std::uint32_t>(b, *store, 0x2C);
    if (!capacity) { Reason(reason, "after_registry_capacity_unavailable"); return nullptr; }
    const auto index = static_cast<std::uint32_t>(*key) & 0xFFFFFFU;
    if (index < *capacity) {
      const auto table = Read<const void *>(b, *store, 0x20);
      const auto indexed = table ? Read<const void *>(b, *table,
          static_cast<std::size_t>(index) * 16 + 8) : std::nullopt;
      if (!indexed) { Reason(reason, "after_registry_indexed_pointer_unavailable"); return nullptr; }
      if (*indexed) {
        const auto full = Read<std::int32_t>(b, *indexed, full_offset);
        if (!full) { Reason(reason, "after_registry_indexed_id_unavailable"); return nullptr; }
        if (*full == *key) {
          selected_full = full;
          selection = indexed_selection;
          return *indexed;
        }
      }
    }
  }
  const auto fallback = Read<const void *>(b, fallback_slot);
  selection = "native_fallback";
  if (!fallback || !*fallback) {
    Reason(reason, "after_registry_native_fallback_unavailable");
    return nullptr;
  }
  return *fallback;
}
const void *AfterRelatedCharacter(AfterReadState &s, const void *character,
    const std::optional<bool> &current_land, bool composition,
    game::ContextSourceAfterRelatedSelectionV1 &out) {
  const auto &b = s.bindings;
  const auto &raw = b.after_gated_tail;
  const auto carrier = Read<const void *>(b, character, 0x1B8);
  if (!carrier) { out.reason = "after_related_carrier_unavailable"; return nullptr; }
  out.carrier_present = *carrier != nullptr;
  if (!*carrier) out.helper_return_full_id_raw = -1;
  else {
    const auto store = Read<const void *>(b, raw.character_storage_slot);
    if (!store) { out.reason = "after_related_helper_registry_unavailable"; return nullptr; }
    std::vector<const void *> identities;
    for (const auto offset : {0xCCU, 0xC8U}) {
      game::ContextSourceGatedResolutionV1 attempt{};
      attempt.native_index = static_cast<std::int32_t>(out.attempts.size());
      const auto key = Read<std::int32_t>(b, *carrier, offset);
      const void *candidate = nullptr;
      if (!key) attempt.reason = "after_related_helper_key_unavailable";
      else candidate = GatedResolveCharacter(b, store, *key, true, attempt, identities);
      if (candidate) attempt.object_identity = TraitStageIdentity(candidate);
      if (!attempt.reason.empty()) out.reason = attempt.reason;
      const bool accepted = attempt.admitted == true;
      out.attempts.push_back(std::move(attempt));
      if (!out.reason.empty()) return nullptr;
      if (accepted) { out.helper_return_full_id_raw = key; break; }
    }
    if (!out.helper_return_full_id_raw) {
      if (!current_land) { out.reason = "after_related_self_land_unavailable"; return nullptr; }
      if (*current_land) {
        out.self_full_id_raw = Read<std::int32_t>(b, character, 0x18);
        if (!out.self_full_id_raw) { out.reason = "after_related_self_id_unavailable"; return nullptr; }
        out.helper_return_full_id_raw = out.self_full_id_raw;
      } else out.helper_return_full_id_raw = -1;
    }
  }
  if (composition && out.helper_return_full_id_raw == -1) return nullptr;
  const void *related = AfterRegistry(b, raw.character_storage_slot,
      raw.character_fallback_slot, nullptr, 0x18, "indexed_full_id",
      out.caller_requested_full_id_raw, out.caller_selection,
      out.caller_full_id_raw, out.reason, &out.helper_return_full_id_raw);
  if (!related) return nullptr;
  out.caller_identity = TraitStageIdentity(related);
  if (composition) {
    out.caller_admitted = true;
  } else {
    out.caller_magic_raw = Read<std::uint32_t>(b, related, 0x1C);
    if (!out.caller_magic_raw) { out.reason = "after_related_caller_magic_unavailable"; return nullptr; }
    if (*out.caller_magic_raw != 0x43686172U) { out.caller_admitted = false; return nullptr; }
    out.caller_full_id_raw = Read<std::int32_t>(b, related, 0x18);
    if (!out.caller_full_id_raw) { out.reason = "after_related_caller_id_unavailable"; return nullptr; }
    out.caller_admitted = *out.caller_full_id_raw != -1;
    if (!*out.caller_admitted) return nullptr;
  }
  return related;
}

bool AfterDateCaches(const ContextSourceBindingsV1 &b, const void *address,
                     game::ContextSourceAfterDateV1 &out) {
  out.day_cache_i8 = Read<std::int8_t>(b, address, 4);
  out.month_cache_i8 = Read<std::int8_t>(b, address, 5);
  out.year_cache_i16 = Read<std::int16_t>(b, address, 6);
  if (!out.day_cache_i8 || !out.month_cache_i8 || !out.year_cache_i16) return false;
  if ((*out.day_cache_i8 < 0 || *out.month_cache_i8 < 0 || *out.year_cache_i16 < 0) &&
      !out.raw_i32) out.raw_i32 = Read<std::int32_t>(b, address);
  return (*out.day_cache_i8 >= 0 && *out.month_cache_i8 >= 0 && *out.year_cache_i16 >= 0) ||
      out.raw_i32.has_value();
}
struct AfterCalendarParts { std::int32_t year, month, day; };
AfterCalendarParts AfterCalendar(const game::ContextSourceAfterDateV1 &date) {
  std::int32_t year = *date.year_cache_i16;
  std::int32_t month = *date.month_cache_i8;
  std::int32_t day = *date.day_cache_i8;
  if (year < 0 || month < 0 || day < 0) {
    const auto hours = AfterWrap32(static_cast<std::uint32_t>(*date.raw_i32) - 43800000U);
    const auto days = hours / 24;
    const auto index = (days % 365 + 365) % 365;
    // Equivalent byte-for-byte calendar lookup to the reused365B tables:
    // month444C4B0 SHA218539a9..., day444C340 SHA49cfa773... (no leap day).
    constexpr std::int32_t starts[] = {0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365};
    std::int32_t decoded_month = 0;
    while (index >= starts[decoded_month + 1]) ++decoded_month;
    if (year < 0) year = hours / 8760;
    if (month < 0) month = decoded_month;
    if (day < 0) day = index - starts[decoded_month];
  }
  return {year, month, day};
}
void AfterEmptyRows(game::ContextSourceAfterRowsetV1 &rows) {
  rows.reason.clear();
  rows.rows.emplace();
  AfterFinish(rows);
}
void AfterThresholdRows(const ContextSourceBindingsV1 &b, const void *definition,
    std::size_t array_offset, const std::optional<std::int32_t> &selector, bool owner,
    game::ContextSourceAfterRowsetV1 &out) {
  out.reason.clear();
  if (!out.count_raw) Reason(out.reason, "after_composition_row_count_unavailable");
  else if (*out.count_raw < 0) Reason(out.reason, "after_composition_negative_row_count");
  else if (*out.count_raw == 0) out.rows.emplace();
  else if (!selector) Reason(out.reason, "after_composition_row_selector_unavailable");
  else {
    const auto data = Read<const void *>(b, definition, array_offset);
    if (data) out.array_present = *data != nullptr;
    if (!data || !*data) Reason(out.reason, "after_composition_row_array_unavailable");
    else {
      out.rows.emplace();
      for (std::int32_t i = 0; i < *out.count_raw; ++i) {
        game::ContextSourceAfterThresholdRowV1 row{};
        row.native_index = i;
        const void *source = Offset(*data, static_cast<std::size_t>(i) * 0x3D0);
        row.threshold_raw = Read<std::int32_t>(b, source, 8);
        if (!row.threshold_raw) row.reason = "after_composition_threshold_unavailable";
        else {
          row.admitted = *selector >= *row.threshold_raw;
          if (*row.admitted) {
            row.pc = AfterPc(b, Offset(source, owner ? 0x10U : 0x1D0U));
            row.reason = row.pc.reason;
          }
        }
        if (!row.reason.empty()) Reason(out.reason, row.reason.c_str());
        out.rows->push_back(std::move(row));
      }
    }
  }
  AfterFinish(out);
}
void AfterSkipComposition(game::ContextSourceAfterCompositionV1 &out) {
  out.receiver_selection = "skipped";
  out.admitted = false;
  AfterEmptyRows(out.level_rows);
  AfterEmptyRows(out.month_rows);
  AfterFinish(out);
}
game::ContextSourceAfterCompositionV1 AfterComposition(AfterReadState &s,
    const void *character, const std::optional<const void *> &current_land) {
  const auto &b = s.bindings;
  const auto &raw = b.after_gated_tail;
  game::ContextSourceAfterCompositionV1 out{};
  out.reason.clear();
  const auto finish = [&]() {
    if (!out.level_rows.ready || !out.month_rows.ready)
      Reason(out.reason, "after_composition_rowsets_partial");
    AfterFinish(out);
    return out;
  };
  const auto global = Read<const void *>(b, raw.global_flag_slot);
  if (global && *global) out.global_flag_u8 = Read<std::uint8_t>(b, *global, 0x2B0);
  if (!out.global_flag_u8) { out.reason = "after_composition_bit20_unavailable"; return finish(); }
  out.global_bit20 = (*out.global_flag_u8 & 0x20U) != 0U;
  if (!*out.global_bit20) { AfterSkipComposition(out); return out; }
  if (!current_land) { out.reason = "after_composition_current_land_unavailable"; return finish(); }
  out.current_land_present = *current_land != nullptr;
  const void *selected = nullptr;
  if (*current_land) {
    const auto link = Read<const void *>(b, *current_land, 0x458);
    if (!link) { out.reason = "after_composition_current_selected_unavailable"; return finish(); }
    selected = *link;
  }
  out.current_selected_present = selected != nullptr;
  if (selected) {
    out.owner_mode = true;
    out.receiver_selection = "current_458_178";
  } else {
    const void *related = AfterRelatedCharacter(s, character, out.current_land_present, true, out.related);
    if (!out.related.reason.empty()) { out.reason = out.related.reason; return finish(); }
    if (!related) { AfterSkipComposition(out); return out; }
    const auto land = Read<const void *>(b, related, 0x1C0);
    if (!land) { out.reason = "after_composition_related_land_unavailable"; return finish(); }
    out.related.land_present = *land != nullptr;
    if (*land) {
      const auto link = Read<const void *>(b, *land, 0x458);
      if (!link) { out.reason = "after_composition_related_selected_unavailable"; return finish(); }
      selected = *link;
    }
    out.related.selected_present = selected != nullptr;
    if (!selected) { AfterSkipComposition(out); return out; }
    out.owner_mode = false;
    out.receiver_selection = "related_458_178";
  }
  out.admitted = true;
  const void *handle = Offset(selected, 0x178);
  const auto definition = Read<const void *>(b, handle);
  if (!definition || !*definition) { out.reason = "after_composition_definition_unavailable"; return finish(); }
  out.definition_identity = TraitStageIdentity(*definition);
  out.level_rows.count_raw = Read<std::int32_t>(b, *definition, 0x64);
  out.month_rows.count_raw = Read<std::int32_t>(b, *definition, 0x4C);
  if (out.level_rows.count_raw && *out.level_rows.count_raw > 0)
    out.level_raw = Read<std::int32_t>(b, selected, 0xF8);
  if (out.month_rows.count_raw && *out.month_rows.count_raw > 0) {
    const auto carrier = Read<const void *>(b, character, 0x1B8);
    const void *fifth = carrier ? (*carrier ? Offset(*carrier, 0xE8) : raw.static_fifth_date) : nullptr;
    out.handle_date.raw_i32 = Read<std::int32_t>(b, handle, 8);
    out.fifth_date.raw_i32 = Read<std::int32_t>(b, fifth);
    if (!out.handle_date.raw_i32 || !out.fifth_date.raw_i32)
      Reason(out.reason, "after_composition_date_choice_unavailable");
    else {
      const bool use_fifth = *out.fifth_date.raw_i32 > *out.handle_date.raw_i32;
      out.chosen_date_selection = use_fifth ? "fifth" : "handle";
      auto &chosen = use_fifth ? out.fifth_date : out.handle_date;
      const auto clock = Read<const void *>(b, raw.clock_slot);
      const void *current_date = clock ? Offset(*clock, 8) : nullptr;
      const bool chosen_ready = AfterDateCaches(b, use_fifth ? fifth : Offset(handle, 8), chosen);
      const bool current_ready = AfterDateCaches(b, current_date, out.current_date);
      if (!chosen_ready || !current_ready) Reason(out.reason, "after_composition_date_fields_unavailable");
      else {
        const auto a = AfterCalendar(out.current_date);
        const auto c = AfterCalendar(chosen);
        auto months = 12U * (static_cast<std::uint32_t>(a.year) - static_cast<std::uint32_t>(c.year)) +
            static_cast<std::uint32_t>(a.month) - static_cast<std::uint32_t>(c.month);
        if (a.day < c.day) --months;
        out.completed_months_raw = AfterWrap32(months);
      }
    }
  }
  AfterThresholdRows(b, *definition, 0x58, out.level_raw, *out.owner_mode, out.level_rows);
  AfterThresholdRows(b, *definition, 0x40, out.completed_months_raw, *out.owner_mode, out.month_rows);
  return finish();
}

game::ContextSourceGatedNamedLiteralV1 AfterNestedNamed(
    const ContextSourceBindingsV1 &b, const void *entry) {
  game::ContextSourceGatedNamedLiteralV1 out(0);
  out.reason.clear();
  out.kind = "missing";
  const auto fail = [&](const char *reason) {
    out.reason = reason; AfterFinish(out); return out;
  };
  out.entry_identity = TraitStageIdentity(entry);
  const auto tree = Read<const void *>(b, entry, 0x70);
  if (!tree) return fail("after_nested_named_tree_unavailable");
  out.tree_present = *tree != nullptr;
  if (*tree) {
    out.tree_identity = TraitStageIdentity(*tree);
    out.kind = "dynamic_tree_requires_current_result";
    return fail("dynamic_tree_requires_current_result");
  }
  out.fixed_flag_u8 = Read<std::uint8_t>(b, entry, 0x7B);
  if (!out.fixed_flag_u8) return fail("after_nested_named_flag_unavailable");
  if (*out.fixed_flag_u8 == 0U) {
    out.kind = "known_zero";
    out.value_q64 = 0;
  } else {
    out.raw_fixed_q64 = Read<std::int64_t>(b, entry, 0x68);
    if (!out.raw_fixed_q64) return fail("after_nested_named_raw_unavailable");
    out.kind = "literal";
    out.value_q64 = out.raw_fixed_q64;
  }
  AfterFinish(out);
  return out;
}
game::ContextSourceAfterRuleV1 AfterRule(const ContextSourceBindingsV1 &b,
                                       const void *definition) {
  game::ContextSourceAfterRuleV1 out{};
  out.reason.clear();
  const auto fail = [&](const char *reason) {
    out.reason = reason; AfterFinish(out); return out;
  };
  const void *rule = Offset(definition, 0x600);
  out.mode_raw = Read<std::int32_t>(b, rule, 0xC0);
  if (!out.mode_raw) return fail("after_definition_600_mode_unavailable");
  if (*out.mode_raw == 0) {
    out.selection = "mode_zero_raw98";
    out.raw_98_q64 = Read<std::int64_t>(b, rule, 0x98);
    if (!out.raw_98_q64) return fail("after_definition_600_literal_unavailable");
    out.value_q64 = out.raw_98_q64;
    AfterFinish(out);
    return out;
  }
  const auto tree = Read<const void *>(b, rule, 0xB8);
  if (!tree) return fail("after_definition_600_tree_unavailable");
  out.tree_present = *tree != nullptr;
  if (*tree) {
    out.tree_identity = TraitStageIdentity(*tree);
    out.selection = "dynamic_tree";
    return fail("definition_600_dynamic_fixed_result");
  }
  const auto named = Read<const void *>(b, rule, 0xA8);
  if (!named) return fail("after_definition_600_named_pointer_unavailable");
  out.named_present = *named != nullptr;
  if (*named) {
    out.selection = "nested_named";
    out.named = AfterNestedNamed(b, *named);
    if (!out.named.ready) return fail(out.named.kind == "dynamic_tree_requires_current_result"
        ? "definition_600_dynamic_fixed_result" : "after_definition_600_nested_named_unavailable");
    out.value_q64 = out.named.value_q64;
  } else {
    out.target_count_raw = Read<std::int32_t>(b, rule, 0x14);
    if (!out.target_count_raw) return fail("after_definition_600_target_count_unavailable");
    if (*out.target_count_raw != 0) {
      out.selection = "dynamic_targets";
      return fail("definition_600_dynamic_fixed_result");
    }
    out.selection = "zero_targets_raw98";
    out.raw_98_q64 = Read<std::int64_t>(b, rule, 0x98);
    if (!out.raw_98_q64) return fail("after_definition_600_fallback_raw_unavailable");
    out.value_q64 = out.raw_98_q64;
  }
  AfterFinish(out);
  return out;
}
game::ContextSourceAfterKindV1 AfterKind(const ContextSourceBindingsV1 &b,
    const void *position, const void *definition) {
  const auto &raw = b.after_gated_tail;
  game::ContextSourceAfterKindV1 out{};
  out.reason.clear();
  const auto fail = [&](const char *reason) {
    Reason(out.reason, reason); AfterFinish(out); return out;
  };
  std::optional<std::int32_t> indexed_full;
  const void *owner = AfterRegistry(b, raw.character_storage_slot, raw.character_fallback_slot,
      Offset(position, 0x120), 0x18, "indexed_full_id", out.position_120_raw,
      out.owner_selection, indexed_full, out.reason);
  if (!owner) return fail("after_kind_owner_unavailable");
  out.owner_identity = TraitStageIdentity(owner);
  // Actual2423700 reads ID18 for played membership, never Character magic.
  out.owner_full_id_raw = Read<std::int32_t>(b, owner, 0x18);
  if (!out.owner_full_id_raw) return fail("after_kind_owner_id_unavailable");
  const auto clock = Read<const void *>(b, raw.clock_slot);
  const auto manager = clock ? Read<const void *>(b, *clock, 0xA0) : std::nullopt;
  if (!manager || !*manager) return fail("after_kind_played_manager_unavailable");
  out.played_count_raw = Read<std::int32_t>(b, *manager, 0x22364);
  if (!out.played_count_raw) return fail("after_kind_played_count_unavailable");
  if (*out.played_count_raw < 0) return fail("after_kind_played_negative_count");
  if (*out.played_count_raw == 0) out.played_full_ids.emplace();
  else {
    const auto data = Read<const void *>(b, *manager, 0x22358);
    out.played_full_ids = Vector<std::int32_t>(b, data.value_or(nullptr), out.played_count_raw);
    if (!out.played_full_ids) return fail("after_kind_played_ids_unavailable");
  }
  out.owner_played = std::find(out.played_full_ids->begin(), out.played_full_ids->end(),
                             *out.owner_full_id_raw) != out.played_full_ids->end();
  if (!*out.owner_played) {
    out.raw_a0_u8 = Read<std::uint8_t>(b, position, 0xA0);
    if (!out.raw_a0_u8) return fail("after_kind_raw_a0_unavailable");
    if (*out.raw_a0_u8 != 5U) {
      out.kind_raw = *out.raw_a0_u8;
      AfterFinish(out);
      return out;
    }
  }
  out.threshold_count_raw = Read<std::int32_t>(b, definition, 0x40E4);
  if (!out.threshold_count_raw) return fail("after_kind_threshold_count_unavailable");
  if (*out.threshold_count_raw < 4) {
    out.kind_raw = 4;
    AfterFinish(out);
    return out;
  }
  out.rule = AfterRule(b, definition);
  if (!out.rule.ready) return fail(out.rule.reason.c_str());
  const auto data = Read<const void *>(b, definition, 0x40D8);
  if (!data) return fail("after_kind_threshold_pointer_unavailable");
  const std::optional<std::int32_t> four{4};
  out.thresholds_i32 = Vector<std::int32_t>(b, *data, four);
  if (!out.thresholds_i32) return fail("after_kind_threshold_values_unavailable");
  out.kind_raw = 4;
  for (std::int32_t i = 0; i < 4; ++i) {
    const auto threshold = static_cast<std::int64_t>(out.thresholds_i32->at(static_cast<std::size_t>(i))) * 100000;
    if (*out.rule.value_q64 < threshold) { out.kind_raw = i; break; }
  }
  AfterFinish(out);
  return out;
}

void AfterPairGate(const ContextSourceBindingsV1 &b, const void *definition,
    std::size_t base_offset, std::size_t tier_offset,
    std::vector<game::ContextSourceAfterPairProbeV1> &probes,
    std::optional<bool> &admitted, std::string &reason) {
  for (std::int32_t i = 0; i < 6; ++i) {
    const auto offset = i == 0 ? base_offset : tier_offset +
        static_cast<std::size_t>(i - 1) * 0x1C0;
    game::ContextSourceAfterPairProbeV1 probe{};
    probe.native_index = i;
    probe.count_raw = Read<std::int32_t>(b, definition, offset + 0xC);
    const auto count = probe.count_raw;
    probes.push_back(std::move(probe));
    if (!count) { Reason(reason, "after_pair_count_unavailable"); return; }
    if (*count != 0) { admitted = true; return; }
  }
  admitted = false;
}
game::ContextSourceAfterPositionV1 AfterPosition(AfterReadState &s,
    const void *character, const void *key_address, std::int32_t index,
    std::int32_t family) {
  const auto &b = s.bindings;
  const auto &raw = b.after_gated_tail;
  game::ContextSourceAfterPositionV1 out{};
  out.native_index = index;
  const void *position = AfterRegistry(b, raw.position_storage_slot,
      raw.position_fallback_slot, key_address, 8, "registry_full_id_8",
      out.requested_full_id_raw, out.position_selection,
      out.position_full_id_raw, out.reason);
  if (!position) return out;
  out.position_identity = TraitStageIdentity(position);
  const auto definition = Read<const void *>(b, position, 0x110);
  const auto other = Read<const void *>(b, position, 0x118);
  const auto take_pc = [&](const void *source, game::ContextSourceAfterPcV1 &pc) {
    pc = AfterPc(b, source);
    if (!pc.reason.empty()) Reason(out.reason, pc.reason.c_str());
  };
  const auto take_kind = [&](game::ContextSourceAfterKindV1 &kind) {
    kind = AfterKind(b, position, definition.value_or(nullptr));
    if (!kind.ready) Reason(out.reason, kind.reason.c_str());
  };
  if (!definition || !*definition) Reason(out.reason, "after_position_definition_unavailable");
  else {
    out.definition_identity = TraitStageIdentity(*definition);
    if (family == 3) {
      AfterPairGate(b, *definition, 0x3658, 0x3818,
          out.definition_pair_probes, out.definition_pair_admitted, out.reason);
      if (out.definition_pair_admitted == true) {
        take_pc(Offset(*definition, 0x3658), out.base_pc);
        take_kind(out.kind);
        if (out.kind.kind_raw)
          take_pc(Offset(*definition, 0x3818 + static_cast<std::size_t>(*out.kind.kind_raw) * 0x1C0), out.tier_pc);
      }
    } else {
      take_pc(Offset(*definition, family == 1 ? 0x2748U : 0x2908U), out.base_pc);
      if (family == 2) {
        take_kind(out.kind);
        if (out.kind.kind_raw)
          take_pc(Offset(*definition, 0x2CB8 + static_cast<std::size_t>(*out.kind.kind_raw) * 0x1C0), out.tier_pc);
      }
      out.composite_group = TraitStageGroup(b, character, Offset(*definition, 0x2AC8), s.selectors, "base");
      // B8D0 traverses begin/end for its conditional rows. A negative raw
      // count cannot be relabeled the reused reader's known-empty branch.
      if ((out.composite_group->conditional_a_count && *out.composite_group->conditional_a_count < 0) ||
          (out.composite_group->conditional_b_count && *out.composite_group->conditional_b_count < 0)) {
        out.composite_group->ready = false;
        Reason(out.composite_group->reason, "after_composite_negative_count");
      }
      if (!out.composite_group->ready) Reason(out.reason, "after_position_composite_partial");
    }
  }
  if (!other || !*other) Reason(out.reason, "after_position_other_definition_unavailable");
  else {
    out.other_definition_identity = TraitStageIdentity(*other);
    out.other_magic_raw = Read<std::uint32_t>(b, *other, 0x38);
    if (!out.other_magic_raw) Reason(out.reason, "after_position_other_magic_unavailable");
    else {
      out.other_admitted = *out.other_magic_raw == 0x4744624FU;
      if (*out.other_admitted) {
        if (family == 3) {
          AfterPairGate(b, *other, 0x2580, 0x2740,
              out.other_pair_probes, out.other_pair_admitted, out.reason);
          if (out.other_pair_admitted == true) {
            take_pc(Offset(*other, 0x2580), out.other_base_pc);
            if (definition && *definition) take_kind(out.other_kind);
            if (out.other_kind.kind_raw)
              take_pc(Offset(*other, 0x2740 + static_cast<std::size_t>(*out.other_kind.kind_raw) * 0x1C0), out.other_tier_pc);
          }
        } else {
          take_pc(Offset(*other, family == 1 ? 0x1940U : 0x1B00U), out.other_base_pc);
          if (family == 2) {
            // Each actual getter occurrence consumes Position.Def110 again,
            // while its selected PC resides in OtherDef118.
            if (definition && *definition) take_kind(out.other_kind);
            if (out.other_kind.kind_raw)
              take_pc(Offset(*other, 0x1CC0 + static_cast<std::size_t>(*out.other_kind.kind_raw) * 0x1C0), out.other_tier_pc);
          }
        }
      }
    }
  }
  out.ready = out.reason.empty();
  return out;
}
void AfterEmptyCourtList(game::ContextSourceAfterCourtListV1 &out,
                         const char *selection) {
  out.reason.clear();
  out.header_selection = selection;
  out.numeric_count = 0;
  out.rows.emplace();
  AfterFinish(out);
}
void AfterCourtRows(AfterReadState &s, const void *character, const void *header,
    std::int32_t family, game::ContextSourceAfterCourtListV1 &out) {
  out.reason.clear();
  out.count_raw = Read<std::int32_t>(s.bindings, header, 0xC);
  out.numeric_count = out.count_raw;
  if (!out.count_raw) Reason(out.reason, "after_court_list_count_unavailable");
  else if (*out.count_raw < 0) Reason(out.reason, "after_court_list_negative_count");
  else if (*out.count_raw == 0) out.rows.emplace();
  else {
    const auto data = Read<const void *>(s.bindings, header);
    if (data) out.array_present = *data != nullptr;
    if (!data || !*data) Reason(out.reason, "after_court_list_array_unavailable");
    else {
      out.rows.emplace();
      for (std::int32_t i = 0; i < *out.count_raw; ++i) {
        auto row = AfterPosition(s, character, Offset(*data, static_cast<std::size_t>(i) * 4), i, family);
        if (!row.ready) Reason(out.reason, "after_court_position_partial");
        out.rows->push_back(std::move(row));
      }
    }
  }
  AfterFinish(out);
}
game::ContextSourceAfterCourtListV1 AfterCurrentCourtList(AfterReadState &s,
    const void *character, const std::optional<const void *> &owner,
    std::int32_t family) {
  game::ContextSourceAfterCourtListV1 out{};
  out.reason.clear();
  if (!owner) { out.reason = "after_court_list_owner_unavailable"; AfterFinish(out); return out; }
  out.owner_present = *owner != nullptr;
  if (!*owner) { AfterEmptyCourtList(out, "absent_owner"); return out; }
  out.header_selection = family == 1 ? "current_1b8_d0" : "current_1c0_3b8";
  AfterCourtRows(s, character, Offset(*owner, family == 1 ? 0xD0U : 0x3B8U), family, out);
  return out;
}
game::ContextSourceAfterCourtListV1 AfterRelatedCourtList(AfterReadState &s,
    const void *character, const std::optional<bool> &current_land) {
  game::ContextSourceAfterCourtListV1 out{};
  out.reason.clear();
  const void *related = AfterRelatedCharacter(s, character, current_land, false, out.related);
  if (!out.related.reason.empty()) {
    out.reason = out.related.reason; AfterFinish(out); return out;
  }
  if (!related) { AfterEmptyCourtList(out, "related_invalid_skip"); return out; }
  const auto land = Read<const void *>(s.bindings, related, 0x1C0);
  if (!land) { out.reason = "after_related_court_owner_unavailable"; AfterFinish(out); return out; }
  out.related.land_present = *land != nullptr;
  out.owner_present = *land != nullptr;
  if (*land) {
    out.header_selection = "related_1c0_3b8";
    AfterCourtRows(s, character, Offset(*land, 0x3B8), 3, out);
  } else {
    out.header_selection = "inline_default_54e7220";
    out.default_init_guard_raw = Read<std::int32_t>(s.bindings, s.bindings.after_gated_tail.default_list_guard_slot);
    if (!out.default_init_guard_raw) {
      out.reason = "after_default_list_init_guard_unavailable"; AfterFinish(out);
    } else if (*out.default_init_guard_raw == 0 || *out.default_init_guard_raw == -1) {
      AfterEmptyCourtList(out, "modeled_empty_default_54e7220");
    } else AfterCourtRows(s, character, s.bindings.after_gated_tail.default_list_header, 3, out);
  }
  return out;
}
game::ContextSourceAfterGatedTail326a8e0And2920310V1 AfterGatedTail326a8e0And2920310(
    const ContextSourceBindingsV1 &b, const void *character, std::int32_t id) {
  game::ContextSourceAfterGatedTail326a8e0And2920310V1 out{};
  out.character_id = id;
  out.reason.clear();
  AfterReadState state(b, out);
  const auto land = Read<const void *>(b, character, 0x1C0);
  if (land) out.current_land_present = *land != nullptr;
  out.composition_326a8e0 = AfterComposition(state, character, land);
  const auto carrier = Read<const void *>(b, character, 0x1B8);
  out.current_1b8_court_positions = AfterCurrentCourtList(state, character, carrier, 1);
  out.current_1c0_court_positions = AfterCurrentCourtList(state, character, land, 2);
  out.related_court_positions = AfterRelatedCourtList(state, character, out.current_land_present);
  if (!out.composition_326a8e0.ready || !out.current_1b8_court_positions.ready ||
      !out.current_1c0_court_positions.ready || !out.related_court_positions.ready)
    out.reason = "after_gated_tail_families_partial";
  AfterFinish(out);
  return out;
}
