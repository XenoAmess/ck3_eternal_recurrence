// Included in the source reader anonymous namespace after PropertiesReady.
std::string TraitStageIdentity(const void *p) {
  return "trait_stage_pointer_" + std::to_string(reinterpret_cast<std::uintptr_t>(p));
}
const void *TraitStageSignedOffset(const void *p, std::int64_t delta) {
  return p ? reinterpret_cast<const void *>(reinterpret_cast<std::uintptr_t>(p) +
      static_cast<std::uint64_t>(delta)) : nullptr;
}
std::int32_t TraitStageWrap32(std::uint32_t value) {
  std::int32_t out{};
  std::memcpy(&out, &value, sizeof(out));
  return out;
}
struct TraitStageReadState {
  game::ContextSourceTraitStage291d460V1 &out;
  const void *a = nullptr;
  const void *b_selector = nullptr;
  bool a_tried = false;
  bool b_tried = false;
  bool a_keys_tried = false;
  bool b_keys_tried = false;
  bool b_nested_tried = false;
};
const void *TraitStageSelector(const ContextSourceBindingsV1 &b,
                              const void *character, TraitStageReadState &s,
                              bool first) {
  auto &tried = first ? s.a_tried : s.b_tried;
  auto &selected = first ? s.a : s.b_selector;
  if (tried) return selected;
  tried = true;
  const auto &raw = b.trait_stage;
  auto &key = first ? s.out.selector_a_key_raw : s.out.selector_b_key_raw;
  auto &selection = first ? s.out.selector_a_selection : s.out.selector_b_selection;
  auto &identity = first ? s.out.selector_a_identity : s.out.selector_b_identity;
  key = Read<std::int32_t>(b, character, first ? 0xB4 : 0xB0);
  const auto store = Read<const void *>(b, first ? raw.selector_a_storage_slot
                                                : raw.selector_b_storage_slot);
  if (!key || !store) return nullptr;
  if (*store) {
    const auto capacity = Read<std::uint32_t>(b, *store, 0x2C);
    if (!capacity) return nullptr;
    const auto index = static_cast<std::uint32_t>(*key) & 0xFFFFFFU;
    if (index < *capacity) {
      const auto data = Read<const void *>(b, *store, 0x20);
      if (!data || !*data) return nullptr;
      const auto candidate = Read<const void *>(b, *data,
          static_cast<std::size_t>(index) * 0x10 + 8);
      if (!candidate) return nullptr;
      if (*candidate) {
        const auto full = Read<std::int32_t>(b, *candidate, first ? 8 : 0x10);
        if (!full) return nullptr;
        if (*full == *key) {
          selected = *candidate;
          selection = first ? "registry_full_id_8" : "registry_full_id_10";
        }
      }
    }
  }
  if (!selected) {
    const auto fallback = Read<const void *>(b, first ? raw.selector_a_fallback_slot
                                                     : raw.selector_b_fallback_slot);
    if (!fallback || !*fallback) return nullptr;
    selected = *fallback;
    selection = "native_fallback";
  }
  identity = TraitStageIdentity(selected);
  return selected;
}
const void *TraitStageDefinition(const ContextSourceBindingsV1 &b,
                                 const void *database, std::int32_t id,
                                 std::optional<std::string> &selection) {
  if (id >= 0) {
    const auto count = Read<std::int32_t>(b, database, 0x5C);
    if (!count) return nullptr;
    if (id < *count) {
      const auto data = Read<const void *>(b, database, 0x50);
      if (!data || !*data) return nullptr;
      const auto pointer = Read<const void *>(b, *data, static_cast<std::size_t>(id) * 8);
      if (!pointer) return nullptr;
      selection = "indexed_trait_database";
      return *pointer;
    }
  }
  const auto pointer = Read<const void *>(b, b.trait_stage.trait_definition_fallback_slot);
  if (!pointer) return nullptr;
  selection = "native_trait_definition_fallback";
  return *pointer;
}
bool TraitStageContains(const std::vector<std::int32_t> &keys, std::int32_t key) {
  const auto i = std::lower_bound(keys.begin(), keys.end(), key);
  return i != keys.end() && *i == key;
}
std::optional<bool> TraitStageMembershipA(const ContextSourceBindingsV1 &b,
    const void *character, TraitStageReadState &s, std::int32_t key) {
  const auto selected = TraitStageSelector(b, character, s, true);
  if (!selected) return std::nullopt;
  if (!s.a_keys_tried) {
    s.a_keys_tried = true;
    s.out.selector_a_membership_count = Read<std::int32_t>(b, selected, 0x7C4);
    if (s.out.selector_a_membership_count) {
      if (*s.out.selector_a_membership_count <= 0) s.out.selector_a_keys_i32.emplace();
      else {
        const auto data = Read<const void *>(b, selected, 0x7B8);
        s.out.selector_a_keys_i32 = Vector<std::int32_t>(b, data.value_or(nullptr),
                                                       s.out.selector_a_membership_count);
      }
    }
  }
  if (!s.out.selector_a_keys_i32) return std::nullopt;
  return TraitStageContains(*s.out.selector_a_keys_i32, key);
}
std::optional<bool> TraitStageMembershipB(const ContextSourceBindingsV1 &b,
    const void *character, TraitStageReadState &s, std::int32_t key) {
  const auto selected = TraitStageSelector(b, character, s, false);
  if (!selected) return std::nullopt;
  if (!s.b_keys_tried) {
    s.b_keys_tried = true;
    const auto owner = Read<const void *>(b, selected, 0x20);
    const auto header = owner && *owner ? Read<const void *>(b, *owner, 0x128)
                                       : std::optional<const void *>{};
    if (header && *header) {
      s.out.selector_b_primary_count = Read<std::int32_t>(b, *header, 0x14);
      if (s.out.selector_b_primary_count) {
        if (*s.out.selector_b_primary_count <= 0) s.out.selector_b_primary_keys_i32.emplace();
        else {
          const auto data = Read<const void *>(b, *header, 8);
          s.out.selector_b_primary_keys_i32 = Vector<std::int32_t>(b, data.value_or(nullptr),
                                                          s.out.selector_b_primary_count);
        }
      }
    }
  }
  if (!s.out.selector_b_primary_keys_i32) return std::nullopt;
  if (TraitStageContains(*s.out.selector_b_primary_keys_i32, key)) return true;
  if (!s.b_nested_tried) {
    s.b_nested_tried = true;
    s.out.selector_b_nested_count = Read<std::int32_t>(b, selected, 0x524);
    if (s.out.selector_b_nested_count) s.out.selector_b_nested_keys.emplace();
  }
  if (!s.out.selector_b_nested_count || !s.out.selector_b_nested_keys) return std::nullopt;
  auto &sets = *s.out.selector_b_nested_keys;
  const auto count = *s.out.selector_b_nested_count;
  for (std::int32_t i = 0; i < count; ++i) {
    const auto index = static_cast<std::size_t>(i);
    if (index == sets.size()) {
      game::ContextSourceSignedKeySetV1 row{};
      row.native_index = i;
      const auto data = Read<const void *>(b, selected, 0x518);
      const auto object = data && *data ? Read<const void *>(b, *data, index * 8)
                                       : std::optional<const void *>{};
      if (object && *object) {
        row.count = Read<std::int32_t>(b, *object, 0x101C);
        if (row.count) {
          if (*row.count <= 0) row.keys_i32.emplace();
          else {
            const auto keys = Read<const void *>(b, *object, 0x1010);
            row.keys_i32 = Vector<std::int32_t>(b, keys.value_or(nullptr), row.count);
          }
        }
      }
      if (!row.keys_i32) row.reason = "trait_selector_b_nested_keys_unavailable";
      sets.push_back(std::move(row));
    }
    if (!sets[index].keys_i32) return std::nullopt;
    if (TraitStageContains(*sets[index].keys_i32, key)) return true;
  }
  return false;
}
game::ContextSourceTraitGroup291d460V1 TraitStageGroup(
    const ContextSourceBindingsV1 &b, const void *character,
    const void *container, TraitStageReadState &s, std::string role,
    std::optional<std::int32_t> track = {}, std::optional<std::int32_t> level = {}) {
  game::ContextSourceTraitGroup291d460V1 out{};
  out.role = std::move(role); out.track_index = track; out.level_index = level;
  out.property_identity = TraitStageIdentity(container);
  out.base_property_block = Properties(b, container);
  if (!PropertiesReady(*out.base_property_block)) Reason(out.reason, "trait_group_base_unavailable");
  out.conditional_b_count = Read<std::int32_t>(b, container, 0x1CC);
  out.conditional_a_count = Read<std::int32_t>(b, container, 0x1E4);
  auto family = [&](bool first) {
    auto &count = first ? out.conditional_a_count : out.conditional_b_count;
    auto &rows = first ? out.conditional_a_rows : out.conditional_b_rows;
    if (!count) { Reason(out.reason, "trait_group_conditional_count_unavailable"); return; }
    rows.emplace();
    if (*count <= 0) return;
    const auto data = Read<const void *>(b, container, first ? 0x1D8 : 0x1C0);
    if (!data || !*data) { Reason(out.reason, "trait_group_conditional_data_unavailable"); return; }
    for (std::int32_t i = 0; i < *count; ++i) {
      game::ContextSourceTraitCondition291d460V1 row{};
      row.native_index = i;
      const auto entry = Offset(*data, static_cast<std::size_t>(i) * 0x1C8);
      row.key_i32 = Read<std::int32_t>(b, entry);
      if (row.key_i32) row.admitted = first ? TraitStageMembershipA(b, character, s, *row.key_i32)
                                          : TraitStageMembershipB(b, character, s, *row.key_i32);
      if (!row.admitted) row.reason = "trait_conditional_admission_unavailable";
      else if (*row.admitted) {
        const auto pc = Offset(entry, 8);
        row.property_identity = TraitStageIdentity(pc);
        row.property_block = Properties(b, pc);
        if (!PropertiesReady(*row.property_block)) row.reason = "trait_conditional_pc_unavailable";
      }
      if (!row.reason.empty()) Reason(out.reason, "trait_group_conditional_unavailable");
      rows->push_back(std::move(row));
    }
  };
  family(false); family(true);
  out.ready = out.reason.empty();
  return out;
}
game::ContextSourceTraitSide291d460V1 TraitStageSide(
    const ContextSourceBindingsV1 &b, const void *character,
    const void *definition, TraitStageReadState &s) {
  game::ContextSourceTraitSide291d460V1 out{};
  auto finish = [&]() {
    out.ready = out.reason.empty() && out.kind_raw.has_value();
    out.status = out.ready ? "available" : "partial";
    return out;
  };
  const auto selected = TraitStageSelector(b, character, s, true);
  if (!selected) { out.reason = "trait_side_selector_a_unavailable"; return finish(); }
  const auto map = Offset(selected, 0x950);
  const auto data = Read<const void *>(b, map, 8);
  out.map_mask_raw = Read<std::int32_t>(b, map, 0x14);
  out.map_overflow_raw = Read<std::uint8_t>(b, map, 0x18);
  if (!data || !*data || !out.map_mask_raw || !out.map_overflow_raw) {
    out.reason = "trait_side_map_header_unavailable"; return finish();
  }
  const auto key = static_cast<std::uint64_t>(reinterpret_cast<std::uintptr_t>(definition));
  std::uint32_t hash = 0x811C9DC5U;
  for (unsigned i = 0; i < 8; ++i) hash = (hash ^ static_cast<std::uint8_t>(key >> (i * 8))) * 0x1000193U;
  out.hash_u32 = hash;
  std::int64_t row_index = static_cast<std::int64_t>(TraitStageWrap32(hash)) &
                           static_cast<std::int64_t>(*out.map_mask_raw);
  out.first_row_index = row_index;
  std::uint8_t distance = 1;
  const void *matched = nullptr;
  for (;;) {
    game::ContextSourceTraitProbe291d460V1 probe{};
    probe.row_index = row_index; probe.distance_u8 = distance;
    const auto row = TraitStageSignedOffset(*data, row_index * 0x38);
    probe.control_u8 = Read<std::uint8_t>(b, row, 4);
    if (!probe.control_u8) {
      probe.reason = "trait_side_probe_control_unavailable";
      out.reason = probe.reason; out.probes.push_back(std::move(probe)); return finish();
    }
    probe.admitted = *probe.control_u8 >= distance;
    if (!*probe.admitted) { out.probes.push_back(std::move(probe)); break; }
    probe.key_pointer_raw = Read<std::uint64_t>(b, row, 8);
    if (!probe.key_pointer_raw) {
      probe.reason = "trait_side_probe_key_unavailable";
      out.reason = probe.reason; out.probes.push_back(std::move(probe)); return finish();
    }
    const bool hit = *probe.key_pointer_raw == key;
    out.probes.push_back(std::move(probe));
    if (hit) { matched = row; break; }
    ++row_index;
    distance = static_cast<std::uint8_t>(distance + 1U);
  }
  const auto end_index = static_cast<std::int64_t>(TraitStageWrap32(
      static_cast<std::uint32_t>(*out.map_mask_raw) +
      static_cast<std::uint32_t>(*out.map_overflow_raw) + 1U));
  if (!matched || row_index == end_index) out.kind_raw = 0;
  else out.kind_raw = Read<std::int32_t>(b, matched, 0x10);
  if (!out.kind_raw) { out.reason = "trait_side_kind_unavailable"; return finish(); }
  if (*out.kind_raw == 0) return finish();
  const auto provider = Read<const void *>(b, b.trait_stage.definition_provider_slot);
  const auto offset = *out.kind_raw == 1 ? 0x1620U : 0x1630U;
  out.owner_selection = *out.kind_raw == 1 ? "provider_1620" : "provider_1630";
  const auto owner = provider && *provider ? Read<const void *>(b, *provider, offset)
                                          : std::optional<const void *>{};
  if (!owner || !*owner) { out.reason = "trait_side_owner_definition_unavailable"; return finish(); }
  const auto pc = Offset(*owner, 0x40);
  out.property_identity = TraitStageIdentity(pc);
  out.property_block = Properties(b, pc);
  if (!PropertiesReady(*out.property_block)) out.reason = "trait_side_owner_pc_unavailable";
  return finish();
}
void TraitStageGrowth(const ContextSourceBindingsV1 &b, const void *character,
    const void *database, const void *definition, const std::vector<std::int32_t> &ids,
    TraitStageReadState &s, game::ContextSourceTraitRow291d460V1 &out) {
  auto fail = [&](const char *reason) { Reason(out.composite_reason, reason); };
  out.growth_flag_raw = Read<std::uint8_t>(b, character, 0x1A5);
  if (!out.growth_flag_raw) { fail("trait_growth_flag_unavailable"); return; }
  if (*out.growth_flag_raw != 0) {
    out.growth_selection = "empty_character_flag"; out.growth_output_count_raw = 0; return;
  }
  out.track_count_raw = Read<std::int32_t>(b, definition, 0x29C);
  if (!out.track_count_raw) { fail("trait_track_count_unavailable"); return; }
  if (*out.track_count_raw <= 0) {
    out.growth_selection = "empty_track_count"; out.growth_output_count_raw = 0; return;
  }
  out.definition_id_raw = Read<std::int32_t>(b, definition, 0x10);
  if (!out.definition_id_raw) { fail("trait_definition_id_unavailable"); return; }
  const auto match = std::find(ids.begin(), ids.end(), *out.definition_id_raw);
  if (match == ids.end()) {
    out.growth_selection = "empty_trait_search"; out.growth_output_count_raw = 0; return;
  }
  out.growth_trait_match_index = static_cast<std::int32_t>(match - ids.begin());
  out.growth_prefix_track_counts.emplace();
  std::uint32_t prefix = 0;
  for (std::int32_t i = 0; i < *out.growth_trait_match_index; ++i) {
    std::optional<std::string> selection;
    const auto prior = TraitStageDefinition(b, database, ids[static_cast<std::size_t>(i)], selection);
    const auto count = prior ? Read<std::int32_t>(b, prior, 0x29C) : std::optional<std::int32_t>{};
    if (!count) { fail("trait_growth_prefix_count_unavailable"); return; }
    out.growth_prefix_track_counts->push_back(*count);
    prefix += static_cast<std::uint32_t>(*count);
  }
  out.growth_prefix_offset_raw = TraitStageWrap32(prefix);
  out.growth_aux_count_raw = Read<std::int32_t>(b, character, 0x14C);
  if (!out.growth_aux_count_raw) { fail("trait_growth_aux_count_unavailable"); return; }
  if (*out.growth_prefix_offset_raw >= *out.growth_aux_count_raw) {
    out.growth_selection = "empty_aux_range"; out.growth_output_count_raw = 0; return;
  }
  const auto remaining = TraitStageWrap32(static_cast<std::uint32_t>(*out.growth_aux_count_raw) - prefix);
  out.growth_output_count_raw = std::min(*out.track_count_raw, remaining);
  if (*out.growth_output_count_raw == 0) { out.growth_selection = "empty_header_count"; return; }
  out.growth_selection = "current_consumed_growth";
  const auto aux = Read<const void *>(b, character, 0x140);
  if (!aux || !*aux) { fail("trait_growth_aux_data_unavailable"); return; }
  const auto current_data = TraitStageSignedOffset(*aux,
      static_cast<std::int64_t>(*out.growth_prefix_offset_raw) * 8);
  // Positive header count admits all Def tracks; diagnostic out-of-header
  // indices still consume actual successive QWORDs in 30E49F0.
  for (std::int32_t i = 0; i < *out.track_count_raw; ++i) {
    game::ContextSourceTraitTrack291d460V1 track{};
    track.native_index = i;
    track.current_value_raw = Read<std::int64_t>(b, current_data, static_cast<std::size_t>(i) * 8);
    if (!track.current_value_raw) track.reason = "trait_growth_value_unavailable";
    else if (*track.current_value_raw > 0) {
      const auto definitions = Read<const void *>(b, definition, 0x290);
      const auto row = definitions && *definitions ? Offset(*definitions, static_cast<std::size_t>(i) * 0x650) : nullptr;
      track.level_count = Read<std::int32_t>(b, row, 0x2C);
      if (!track.level_count || *track.level_count < 0) track.reason = "trait_growth_level_count_unavailable";
      else {
        track.thresholds_read.emplace(); track.admitted_prefix_count = 0;
        if (*track.level_count > 0) {
          const auto levels = Read<const void *>(b, row, 0x20);
          if (!levels || !*levels) track.reason = "trait_growth_levels_unavailable";
          else for (std::int32_t j = 0; j < *track.level_count; ++j) {
            const auto level = Offset(*levels, static_cast<std::size_t>(j) * 0x200);
            const auto threshold = Read<std::int64_t>(b, level, 0x1F0);
            if (!threshold) { track.reason = "trait_growth_threshold_unavailable"; break; }
            track.thresholds_read->push_back(*threshold);
            if (*track.current_value_raw < *threshold) break;
            ++*track.admitted_prefix_count;
            out.composite_groups.push_back(TraitStageGroup(b, character, level, s, "growth_level", i, j));
          }
        }
      }
    }
    if (!track.reason.empty()) fail("trait_growth_track_unavailable");
    out.growth_tracks.push_back(std::move(track));
  }
}
game::ContextSourceTraitStage291d460V1 TraitStage291d460(
    const ContextSourceBindingsV1 &b, const void *character, std::int32_t id) {
  game::ContextSourceTraitStage291d460V1 out{};
  out.character_id = id;
  out.trait_count = Read<std::int32_t>(b, character, 0x104);
  auto finish = [&]() {
    out.ready = out.reason.empty() && out.rows.has_value();
    out.status = out.ready ? "available" : out.rows ? "partial" : "unavailable";
    return out;
  };
  if (!out.trait_count || *out.trait_count < 0) {
    out.reason = "trait_stage_trait_count_unavailable"; return finish();
  }
  out.rows.emplace();
  if (*out.trait_count == 0) return finish();
  const auto data = Read<const void *>(b, character, 0xF8);
  if (data) out.trait_array_present = *data != nullptr;
  const auto ids = Vector<std::int32_t>(b, data.value_or(nullptr), out.trait_count);
  const auto database = Read<const void *>(b, b.trait_stage.trait_database_slot);
  if (!ids || !database || !*database) {
    out.reason = "trait_stage_current_ids_or_database_unavailable"; return finish();
  }
  TraitStageReadState state{out};
  for (std::int32_t i = 0; i < *out.trait_count; ++i) {
    game::ContextSourceTraitRow291d460V1 row{};
    row.native_index = i; row.trait_id_raw = ids->at(static_cast<std::size_t>(i));
    const auto definition = TraitStageDefinition(b, *database, row.trait_id_raw, row.definition_selection);
    if (!definition) {
      row.reason = "trait_stage_definition_unavailable";
      row.composite_reason = row.reason; row.side.reason = row.reason;
    } else {
      row.definition_identity = TraitStageIdentity(definition);
      row.definition_pointer_raw = static_cast<std::uint64_t>(reinterpret_cast<std::uintptr_t>(definition));
      row.composite_groups.push_back(TraitStageGroup(b, character, Offset(definition, 0xA0), state, "base"));
      TraitStageGrowth(b, character, *database, definition, *ids, state, row);
      for (const auto &group : row.composite_groups)
        if (!group.ready) Reason(row.composite_reason, "trait_stage_composite_group_unavailable");
      row.composite_ready = row.composite_reason.empty();
      row.side = TraitStageSide(b, character, definition, state);
      if (!row.composite_ready || !row.side.ready) row.reason = "trait_stage_trait_inputs_partial";
    }
    if (!row.reason.empty()) Reason(out.reason, "trait_stage_some_trait_inputs_partial");
    out.rows->push_back(std::move(row));
  }
  return finish();
}
