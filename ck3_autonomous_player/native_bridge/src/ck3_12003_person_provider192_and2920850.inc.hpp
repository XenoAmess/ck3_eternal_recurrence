// Included after the qualified RemainingMapped/RemainingRite and AfterPc
// physical readers. The exact source and raw schema are sealed before code.
game::ContextSourceProvider192V1 Provider192Source(
    const ContextSourceBindingsV1 &b, const void *character) {
  game::ContextSourceProvider192V1 out{};
  const auto &raw = b.provider192_and2920850;
  const auto fail = [&](const char *reason) {
    out.reason = reason; AfterFinish(out); return out;
  };
  const auto provider = Read<const void *>(b, raw.provider_slot);
  if (provider) out.provider_loaded = *provider != nullptr;
  if (!provider || !*provider) return fail("provider192_loaded_provider_unavailable");
  out.provider_identity = TraitStageIdentity(*provider);
  out.character_192_i16 = Read<std::int16_t>(b, character, 0x192);
  out.upper_i32 = Read<std::int32_t>(b, raw.upper_slot);
  if (!out.character_192_i16 || !out.upper_i32)
    return fail("provider192_upper_comparison_unavailable");
  std::optional<const void *> selected;
  if (*out.character_192_i16 >= *out.upper_i32) {
    out.selection = "provider_16a0";
    selected = Read<const void *>(b, *provider, 0x16A0);
  } else {
    out.lower_i32 = Read<std::int32_t>(b, raw.lower_slot);
    if (!out.lower_i32) return fail("provider192_lower_comparison_unavailable");
    if (*out.character_192_i16 <= *out.lower_i32) {
      out.selection = "provider_16b0";
      selected = Read<const void *>(b, *provider, 0x16B0);
    } else {
      out.selection = "native_fallback_5d1e0b0";
      selected = Read<const void *>(b, raw.provider_fallback_slot);
    }
  }
  if (!selected || !*selected) return fail("provider192_selected_pointer_unavailable");
  out.selected_identity = TraitStageIdentity(*selected);
  out.magic_u32 = Read<std::uint32_t>(b, *selected, 0x38);
  if (!out.magic_u32) return fail("provider192_selected_magic_unavailable");
  out.admitted = *out.magic_u32 == 0x4744624FU;
  if (*out.admitted) {
    out.pc = AfterPc(b, Offset(*selected, 0x40));
    if (!out.pc.reason.empty()) out.reason = out.pc.reason;
  }
  AfterFinish(out);
  return out;
}
struct Provider2920850ReadState {
  ContextSourceBindingsV1 bindings;
  game::ContextSourceProvider192And2920850InputsV1 &out;
  RemainingRiteState rite{};
  std::vector<const void *> identities;
  Provider2920850ReadState(const ContextSourceBindingsV1 &b,
      game::ContextSourceProvider192And2920850InputsV1 &value) : bindings(b), out(value) {
    const auto &raw = b.provider192_and2920850;
    bindings.selector_a_storage_slot = raw.rite_storage_slot;
    bindings.selector_a_initial_fallback_slot = raw.rite_fallback_slot;
    bindings.selector_a_second_storage_slot = raw.faith_storage_slot;
    bindings.selector_a_second_fallback_slot = raw.faith_fallback_slot;
  }
};
game::ContextSourceProvider2920850OccurrenceV1 Provider2920850Occurrence(
    Provider2920850ReadState &s, const void *character, const void *id_address,
    std::int32_t native_index, bool first) {
  game::ContextSourceProvider2920850OccurrenceV1 out{};
  out.native_index = native_index;
  const auto &b = s.bindings;
  const auto &raw = b.provider192_and2920850;
  const void *object = AfterRegistry(b, raw.object_storage_slot, raw.object_fallback_slot,
      id_address, 8, "registry_full_id_8", out.requested_full_id_raw,
      out.resolution_selection, out.selected_full_id_raw, out.reason);
  if (!object) return out;
  out.object_identity = TraitStageIdentity(object);
  const auto table = Read<const void *>(b, object, 0x4C0);
  if (!table || !*table) { out.reason = "provider2920850_table_pointer_unavailable"; return out; }
  out.table_identity = TraitStageIdentity(*table);
  out.direct_rows.emplace();
  out.direct_ready = true;
  // All four direct occurrences precede all four mapped headers for this
  // physical list occurrence. This deliberately keeps the source order.
  for (std::int32_t i = 0; i < 4; ++i) {
    game::ContextSourceProvider2920850DirectV1 row{};
    row.native_index = i;
    row.pc = AfterPc(b, Offset(*table, (first ? 0x80U : 0x240U) +
        static_cast<std::size_t>(i) * 0xB30));
    if (!row.pc.reason.empty()) out.direct_ready = false;
    out.direct_rows->push_back(std::move(row));
  }
  out.nested_rows.emplace();
  out.mapped_ready = true;
  for (std::int32_t i = 0; i < 4; ++i) {
    game::ContextSourceProvider2920850NestedV1 row{};
    row.native_index = i;
    row.mapped_family = RemainingMapped(b, character,
        Offset(*table, (first ? 0x400U : 0x418U) + static_cast<std::size_t>(i) * 0xB30),
        false, s.out.rite, s.rite, raw.mapped_default_pc,
        raw.mapped_default_guard_slot, s.out.mapped_default_guard_raw, s.identities);
    if (!row.mapped_family.ready) out.mapped_ready = false;
    out.nested_rows->push_back(std::move(row));
  }
  out.ready = out.direct_ready && out.mapped_ready;
  if (!out.ready) out.reason = "provider2920850_occurrence_slots_partial";
  return out;
}
void Provider2920850EmptyList(game::ContextSourceProvider2920850ListV1 &out) {
  out.numeric_count = 0;
  out.rows.emplace();
  out.direct_ready = true;
  out.mapped_ready = true;
  AfterFinish(out);
}
game::ContextSourceProvider2920850ListV1 Provider2920850List(
    Provider2920850ReadState &s, const void *character,
    const std::optional<const void *> &land, const std::optional<const void *> &death,
    bool first) {
  game::ContextSourceProvider2920850ListV1 out{};
  const auto &b = s.bindings;
  const auto &raw = b.provider192_and2920850;
  const void *header = nullptr;
  if (!land || (*land && !death)) {
    out.reason = "provider2920850_current_header_selection_unavailable";
    AfterFinish(out); return out;
  }
  if (*land && !*death) {
    header = Offset(*land, first ? 0x168U : 0x180U);
    out.header_selection = first ? "current_1c0_168" : "current_1c0_180";
  } else {
    out.header_selection = "inline_default_5d67e60";
    out.default_init_guard_raw = Read<std::int32_t>(b, raw.list_default_guard_slot);
    if (!out.default_init_guard_raw) {
      out.reason = "provider2920850_default_list_init_guard_unavailable";
      AfterFinish(out); return out;
    }
    if (*out.default_init_guard_raw == 0 || *out.default_init_guard_raw == -1) {
      out.header_selection = "modeled_empty_default_5d67e60";
      Provider2920850EmptyList(out); return out;
    }
    header = raw.list_default_header;
  }
  out.count_raw = Read<std::int32_t>(b, header, 0xC);
  out.numeric_count = out.count_raw;
  if (!out.count_raw) out.reason = "provider2920850_list_count_unavailable";
  else if (*out.count_raw < 0) out.reason = "provider2920850_negative_list_count";
  else if (*out.count_raw == 0) {
    Provider2920850EmptyList(out); return out;
  } else {
    const auto data = Read<const void *>(b, header);
    if (data) out.array_present = *data != nullptr;
    if (!data || !*data) out.reason = "provider2920850_list_array_unavailable";
    else {
      out.rows.emplace();
      out.direct_ready = true;
      out.mapped_ready = true;
      for (std::int32_t i = 0; i < *out.count_raw; ++i) {
        auto row = Provider2920850Occurrence(s, character,
            Offset(*data, static_cast<std::size_t>(i) * 4), i, first);
        if (!row.direct_ready) out.direct_ready = false;
        if (!row.mapped_ready) out.mapped_ready = false;
        if (!row.ready) Reason(out.reason, "provider2920850_list_occurrences_partial");
        out.rows->push_back(std::move(row));
      }
    }
  }
  AfterFinish(out);
  return out;
}
game::ContextSourceProvider192And2920850InputsV1 Provider192And2920850Inputs(
    const ContextSourceBindingsV1 &b, const void *character, std::int32_t id) {
  game::ContextSourceProvider192And2920850InputsV1 out{};
  out.character_id = id;
  Provider2920850ReadState state(b, out);
  out.provider_192 = Provider192Source(b, character);
  const auto land = Read<const void *>(b, character, 0x1C0);
  std::optional<const void *> death;
  if (land) {
    out.current_land_present = *land != nullptr;
    if (*land) {
      death = Read<const void *>(b, character, 0x1D0);
      if (death) out.current_death_present = *death != nullptr;
    }
  }
  out.list_168 = Provider2920850List(state, character, land, death, true);
  out.list_180 = Provider2920850List(state, character, land, death, false);
  if (!out.provider_192.ready || !out.list_168.ready || !out.list_180.ready)
    out.reason = "provider192_and2920850_families_partial";
  AfterFinish(out);
  return out;
}
