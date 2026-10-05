// Source30C4360/30C3C50: copy actual operands, never call their writer bodies.
game::CombatMaaSixStatsV1 MaaSixStats12003(const void *stats) noexcept {
  game::CombatMaaSixStatsV1 out{};
  out.max_size = LoadAt<std::int32_t>(stats, 8);
  for (std::size_t i = 0; i != 5; ++i)
    out.values[i] = LoadAt<std::int64_t>(stats, 0x10 + i * 8);
  return out;
}

bool MaaProperties12003(const void *properties,
    std::optional<game::CombatMaaPropertyBlockV1> &out) noexcept {
  if (!properties) return false;
  const auto count = LoadAt<std::int32_t>(properties, 0xC);
  if (count < 0) return false;
  const auto *keys = LoadAt<const std::uint16_t *>(properties, 0);
  const auto *values = LoadAt<const std::int64_t *>(properties, 0x68);
  if (count && (!keys || !values)) return false;
  out.emplace(); out->count = count;
  if (count) {
    out->keys_u16.assign(keys, keys + count);
    out->values_q64.assign(values, values + count);
  }
  return true;
}

bool MaaCultureRows12003(const void *definitions, std::int32_t definition_count,
    std::size_t rows_offset, void *selected_type, std::int32_t selected_class,
    std::optional<std::vector<game::CombatMaaCultureRowV1>> &out) noexcept {
  if (definition_count < 0 || (definition_count && !definitions)) return false;
  std::vector<game::CombatMaaCultureRowV1> rows;
  for (std::int32_t d = 0; d != definition_count; ++d) {
    const auto *definition = LoadAt<const void *>(definitions, static_cast<std::size_t>(d) * 8);
    if (!definition) return false;
    const auto count = LoadAt<std::int32_t>(definition, rows_offset + 0xC);
    const auto *data = LoadAt<const std::byte *>(definition, rows_offset);
    if (count < 0 || (count && !data)) return false;
    for (std::int32_t i = 0; i != count; ++i) {
      const auto *row = data + static_cast<std::size_t>(i) * 0x48;
      const auto *filter_definition = LoadAt<const void *>(row, 0x40);
      if (!filter_definition) return false;
      game::CombatMaaCultureRowV1 value{};
      value.definition_index = d; value.row_index = i;
      value.definition_is_gdbo = LoadAt<std::uint32_t>(filter_definition, 0x38) == 0x4744624F;
      value.definition_matches_selected_type = filter_definition == selected_type;
      value.class_filter = LoadAt<std::int32_t>(row, 0x38);
      if ((!value.definition_is_gdbo || value.definition_matches_selected_type) &&
          (value.class_filter == -1 || value.class_filter == selected_class))
        value.stats = MaaSixStats12003(row);
      rows.push_back(std::move(value));
    }
  }
  out = std::move(rows); return true;
}

bool MaaLinkedSources12003(const CombatBindings &b, void *selected_regiment,
    game::CombatMaaStatInputsSnapshotV1 &out) noexcept {
  auto *army = b.maa_get_actual_army ? b.maa_get_actual_army(selected_regiment) : nullptr;
  if (!army) return false;
  const auto count = LoadAt<std::int32_t>(army, 0x44);
  const auto *ids = LoadAt<const std::int32_t *>(army, 0x38);
  if (count < 0 || (count && !ids)) return false;
  out.linked_character_full_ids.emplace(); out.accolade_blocks.emplace();
  for (std::int32_t i = 0; i != count; ++i) {
    auto *regiment = OrdinaryResolvedOrFallback12003(b.regiment_storage_slot,
        b.maa_army_regiment_fallback_slot, ids[i], 0x10);
    if (!regiment) return false;
    const auto id = LoadAt<std::int32_t>(regiment, 0x148);
    if (id == -1) continue;
    auto *character = OrdinaryResolvedOrFallback12003(b.character_storage_slot,
        b.ordinary_character_fallback_slot, id, 0x18);
    if (!character) return false;
    if (LoadAt<std::uint32_t>(character, 0x1C) != 0x43686172 ||
        LoadAt<std::int32_t>(character, 0x18) == -1) continue;
    const auto linked_index = static_cast<std::int32_t>(out.linked_character_full_ids->size());
    out.linked_character_full_ids->push_back(id);
    const auto *carrier = LoadAt<const void *>(character, 0x1B0);
    auto *accolade = carrier ? ResolveStoredComponent(b.maa_accolade_storage_slot,
        LoadAt<std::int32_t>(carrier, 0x570), 8) : nullptr;
    if (!accolade && b.maa_accolade_fallback_slot) accolade = *b.maa_accolade_fallback_slot;
    if (!accolade) return false;
    if (LoadAt<std::uint32_t>(accolade, 0xC) != 0x4163636F ||
        LoadAt<std::int32_t>(accolade, 8) == -1) continue;
    const auto row_count = LoadAt<std::int32_t>(accolade, 0x64);
    const auto *rows = LoadAt<const std::byte *>(accolade, 0x58);
    if (row_count < 0 || (row_count && !rows)) return false;
    bool eligible = true;
    for (std::int32_t j = 0; j != row_count; ++j) {
      const auto *definition = LoadAt<const void *>(rows + static_cast<std::size_t>(j) * 0x18, 0x10);
      if (!definition || LoadAt<std::uint32_t>(definition, 0x38) != 0x4744624F) {
        eligible = false; break;
      }
    }
    if (!eligible) continue; // Native skips the complete group, not just its invalid row.
    for (std::int32_t j = 0; j != row_count; ++j) {
      const auto *row = rows + static_cast<std::size_t>(j) * 0x18;
      auto *definition = LoadAt<std::byte *>(row, 0x10);
      const auto level = LoadAt<std::int32_t>(row, 8);
      auto *tier = b.maa_get_tier ? b.maa_get_tier(level, definition + 0x3C0) : nullptr;
      std::optional<game::CombatMaaPropertyBlockV1> properties;
      if (!tier || !MaaProperties12003(static_cast<const std::byte *>(tier) + 0x390, properties)) return false;
      game::CombatMaaAccoladeBlockV1 block{};
      block.linked_index = linked_index; block.character_full_id = id;
      block.accolade_full_id = LoadAt<std::int32_t>(accolade, 8);
      block.row_index = j; block.level = level; block.properties = std::move(*properties);
      out.accolade_blocks->push_back(std::move(block));
    }
  }
  return true;
}

void ReadMaaRegimentStatInputs12003(const CombatBindings &b, void *regiment,
    void *province, std::int32_t province_id, CombatRegimentSnapshot &row) noexcept {
  if (!b.maa_stat_inputs_enabled || row.kind.status != CombatObservationStatus::available ||
      row.kind.value != "men_at_arms" ||
      (b.is_special_combat_regiment && b.is_special_combat_regiment(regiment))) return;
  auto &out = row.maa_stat_inputs_v1.emplace(); out.source_target_province_id = province_id;
  const auto fail = [&out](const char *reason) { out.unavailable_reason = reason; };
  auto first_id = std::int32_t{-1};
  if (LoadAt<std::int32_t>(regiment, 0x2C) != 0) {
    const auto *first = LoadAt<const void *>(regiment, 0x20);
    if (!first) { fail("maa_first_row_unavailable"); return; }
    first_id = LoadAt<std::int32_t>(first, 8);
  }
  auto *selected = OrdinaryResolvedOrFallback12003(b.ordinary_regiment_storage_slot,
      b.ordinary_regiment_fallback_slot, first_id, 0x10);
  if (!selected) { fail("maa_selected_regiment_unavailable"); return; }
  out.source_regiment_full_id = LoadAt<std::int32_t>(selected, 0x10);
  const auto selector = LoadAt<std::int32_t>(selected, 0x130);
  const auto direct = LoadAt<std::int32_t>(selected, 0x12C);
  out.selector_mode = !(selector == -1 && direct != -1);
  auto character_id = std::int32_t{-1};
  if (selector == -1) character_id = direct;
  else if (direct == -1) {
    auto *nested = OrdinaryResolvedOrFallback12003(b.ordinary_selector_storage_slot,
        b.ordinary_selector_fallback_slot, selector, 0x10);
    if (!nested) { fail("maa_nested_selector_unavailable"); return; }
    character_id = LoadAt<std::int32_t>(nested, 0x128);
  }
  bool fallback = false;
  auto *character = OrdinaryResolvedOrFallback12003(b.character_storage_slot,
      b.ordinary_character_fallback_slot, character_id, 0x18, &fallback);
  if (!character) { fail("maa_selected_character_unavailable"); return; }
  out.selected_character_full_id = LoadAt<std::int32_t>(character, 0x18);
  out.character_resolution = fallback ? "native_fallback" : "generation_resolved";
  auto *context = b.get_character_modifier_aggregator ? b.get_character_modifier_aggregator(character) : nullptr;
  if (!context || !MaaProperties12003(static_cast<std::byte *>(context) + 0x68, out.selected_properties)) {
    fail("maa_selected_context_unavailable"); return;
  }
  auto *type = LoadAt<void *>(selected, 0x118);
  if (!type) { fail("maa_inner_type_unavailable"); return; }
  out.inner_type_is_gdbo = LoadAt<std::uint32_t>(type, 0x38) == 0x4744624F;
  if (!*out.inner_type_is_gdbo) {
    for (std::size_t i = 0; i != 5; ++i)
      if (b.ordinary_stat_loaded_bases[i]) out.fallback_ordinary_bases[i] = *b.ordinary_stat_loaded_bases[i];
    out.available = std::all_of(out.fallback_ordinary_bases.begin(), out.fallback_ordinary_bases.end(),
        [](const auto &value) { return value.has_value(); });
    out.unavailable_reason = out.available ? "" : "maa_ordinary_fallback_bases_unavailable"; return;
  }
  const auto cls = LoadAt<std::int32_t>(type, 0x260); out.selected_type_class = cls;
  out.type_bases.emplace(); out.type_bases->max_size = LoadAt<std::int32_t>(type, 0x270);
  for (std::size_t i = 0; i != 5; ++i) out.type_bases->values[i] = LoadAt<std::int64_t>(type, 0x278 + i * 8);
  auto *rules = b.get_combat_rules ? b.get_combat_rules() : nullptr;
  if (!rules) { fail("maa_rules_unavailable"); return; }
  out.class_row_present = cls >= 0 && cls < LoadAt<std::int32_t>(rules, 0xEFC);
  if (*out.class_row_present) {
    const auto *classes = LoadAt<const std::byte *>(rules, 0xEF0);
    if (!classes) { fail("maa_class_row_unavailable"); return; }
    const auto *class_row = classes + static_cast<std::size_t>(cls) * 0x58;
    out.class_add_keys_u16.emplace(); out.class_mult_keys_u16.emplace();
    out.extra_add_keys_u16.emplace(); out.extra_mult_keys_u16.emplace();
    for (std::size_t i = 0; i != 6; ++i) {
      (*out.class_add_keys_u16)[i] = LoadAt<std::uint16_t>(class_row, 0x28 + i * 2);
      (*out.class_mult_keys_u16)[i] = LoadAt<std::uint16_t>(class_row, 0x34 + i * 2);
    }
    for (std::size_t i = 0; i != 5; ++i) {
      (*out.extra_add_keys_u16)[i] = LoadAt<std::uint16_t>(class_row, 0x40 + i * 2);
      (*out.extra_mult_keys_u16)[i] = LoadAt<std::uint16_t>(class_row, 0x4A + i * 2);
    }
    auto *extra = LoadAt<std::byte *>(selected, 0x120);
    if (!extra || !MaaProperties12003(extra + 0x30 + 0x68, out.extra_properties)) {
      fail("maa_extra_context_unavailable"); return;
    }
    out.extra_title_full_id = LoadAt<std::int32_t>(extra, 0x738);
    auto *title = OrdinaryResolvedOrFallback12003(b.ordinary_selector_storage_slot,
        b.ordinary_selector_fallback_slot, *out.extra_title_full_id, 0x10);
    auto *holder = title && b.maa_get_title_holder ? b.maa_get_title_holder(title) : nullptr;
    if (!holder || !b.maa_get_piety_rank) { fail("maa_extra_holder_unavailable"); return; }
    out.extra_holder_full_id = LoadAt<std::int32_t>(holder, 0x18);
    out.holder_piety_rank = b.maa_get_piety_rank(holder);
  }
  const auto culture_id = LoadAt<std::int32_t>(character, 0xB0);
  auto *culture = OrdinaryResolvedOrFallback12003(b.maa_culture_storage_slot,
      b.maa_culture_fallback_slot, culture_id, 0x10);
  auto *government = b.maa_get_government ? b.maa_get_government(character) : nullptr;
  if (!culture || !government) { fail("maa_culture_or_government_unavailable"); return; }
  out.culture_full_id = LoadAt<std::int32_t>(culture, 0x10);
  const auto gov_index = LoadAt<std::int32_t>(government, 0x10); out.government_index = gov_index;
  out.selected_government_byte_4d6 = LoadAt<std::uint8_t>(government, 0x4D6);
  if (gov_index < 0 || gov_index >= LoadAt<std::int32_t>(culture, 0x694)) {
    out.government_rows.emplace(); out.global_rows.emplace();
  } else {
    const auto *gov_rows = LoadAt<const std::byte *>(culture, 0x688);
    if (!gov_rows) { fail("maa_culture_government_rows_unavailable"); return; }
    const auto *gov_row = gov_rows + static_cast<std::size_t>(gov_index) * 0x18;
    if (!MaaCultureRows12003(LoadAt<const void *>(gov_row, 0), LoadAt<std::int32_t>(gov_row, 0xC),
          0x7C8, type, cls, out.government_rows) ||
        !MaaCultureRows12003(LoadAt<const void *>(culture, 0x6A0), LoadAt<std::int32_t>(culture, 0x6AC),
          0xFE0, type, cls, out.global_rows)) {
      fail("maa_culture_callback_rows_unavailable"); return;
    }
  }
  if (*out.selector_mode) {
    std::int64_t factor = 0;
    if (!b.maa_get_selector_factor || b.maa_get_selector_factor(&factor, character, nullptr) != &factor) {
      fail("maa_selector_factor_unavailable"); return;
    }
    out.selector_factor_q64 = factor;
  }
  if (!MaaLinkedSources12003(b, selected, out)) { fail("maa_linked_or_accolade_sources_unavailable"); return; }
  if (!province) { fail("maa_environment_province_unavailable"); return; }
  auto *map = LoadAt<void *>(province, 0x20);
  auto *terrain = map ? LoadAt<void *>(map, 0xB8) : nullptr;
  auto *definition = LoadAt<void *>(province, 0x620);
  out.definition620_present = definition && LoadAt<std::uint32_t>(definition, 0x38) == 0x4744624F;
  if (!terrain) { fail("maa_environment_terrain_unavailable"); return; }
  struct Ids { const std::int32_t *data; std::int32_t capacity, count; };
  const auto n = static_cast<std::int32_t>(out.linked_character_full_ids->size());
  const Ids ids{out.linked_character_full_ids->data(), n, n};
  const std::array<void *, 3> environments{terrain, definition, province};
  for (std::size_t i = 0; i != 3; ++i) {
    if (i == 1 && !*out.definition620_present) continue;
    if (!b.maa_get_type_environment[i] || !b.maa_get_linked_environment[i]) {
      fail("maa_environment_getter_unbound"); return;
    }
    const auto *type_stats = b.maa_get_type_environment[i](type, environments[i]);
    alignas(8) std::array<std::byte, 0x38> linked_stats{};
    if (!type_stats || b.maa_get_linked_environment[i](linked_stats.data(), type, environments[i], &ids) != linked_stats.data()) {
      fail("maa_environment_vector_unavailable"); return;
    }
    out.environment_components[i] = MaaSixStats12003(type_stats);
    out.environment_components[i + 3] = MaaSixStats12003(linked_stats.data());
  }
  out.available = true; out.unavailable_reason.clear();
}
