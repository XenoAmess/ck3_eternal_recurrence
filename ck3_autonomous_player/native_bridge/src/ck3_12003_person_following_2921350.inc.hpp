// Source-closed read-only2921350 inputs. No native getter, merger or initializer.
const void *Following2921350At(const void *data, std::int64_t offset) {
  if (!data) return nullptr;
  return reinterpret_cast<const void *>(reinterpret_cast<std::uintptr_t>(data) +
                                       static_cast<std::uintptr_t>(offset));
}
bool Following2921350Ids(const ContextSourceBindingsV1 &b, const void *header,
    std::optional<std::int32_t> &count, std::optional<bool> &array_present,
    std::optional<std::vector<std::uint32_t>> &ids, std::string &reason) {
  count = Read<std::int32_t>(b, header, 0xC);
  if (!count) { reason = "following2921350_id_count_unavailable"; return false; }
  if (*count < 0) { reason = "following2921350_negative_id_count"; return false; }
  if (*count == 0) { ids.emplace(); return true; }
  const auto data = Read<const void *>(b, header);
  if (data) array_present = *data != nullptr;
  if (!data || !*data) { reason = "following2921350_id_array_unavailable"; return false; }
  ids = Vector<std::uint32_t>(b, *data, count);
  if (!ids) { reason = "following2921350_id_elements_unavailable"; return false; }
  return true;
}
const void *Following2921350Resolve(const ContextSourceBindingsV1 &b,
    const void *store_slot, const void *fallback_slot, std::uint32_t full_id,
    std::size_t full_offset, std::optional<std::string> &selection,
    std::optional<std::uint32_t> &selected_full, std::string &reason) {
  const std::optional<std::int32_t> known{AfterWrap32(full_id)};
  std::optional<std::int32_t> requested, selected;
  const auto object = AfterRegistry(b, store_slot, fallback_slot, nullptr,
      full_offset, "registry_full_id", requested, selection, selected, reason, &known);
  if (selected) selected_full = static_cast<std::uint32_t>(*selected);
  return object;
}
game::ContextSourceFollowing2921350TitleSourceV1 Following2921350TitleSource(
    const ContextSourceBindingsV1 &b, const void *character) {
  game::ContextSourceFollowing2921350TitleSourceV1 out{};
  const auto finish = [&]() { AfterFinish(out); return out; };
  const auto living = Read<const void *>(b, character, 0x1C0);
  if (!living) { out.reason = "following2921350_character_1c0_unavailable"; return finish(); }
  out.carrier_present = *living != nullptr;
  out.selection = *living ? "current_1c0_1e0" : "actual_default_5459c88";
  const auto header = *living ? Offset(*living, 0x1E0) : b.following_2921350.title_default_header;
  if (!header) { out.reason = "following2921350_title_header_unavailable"; return finish(); }
  out.header_identity = TraitStageIdentity(header);
  Following2921350Ids(b, header, out.count_raw, out.array_present, out.full_ids_u32, out.reason);
  return finish();
}
struct Following2921350CollectedTitle {
  const void *title = nullptr;
  std::int32_t walk_index = 0;
};
bool Following2921350Titles(const ContextSourceBindingsV1 &b,
    game::ContextSourceFollowing2921350InputsV1 &out,
    std::vector<Following2921350CollectedTitle> &collected) {
  struct Pending {
    std::int32_t root;
    std::optional<std::int32_t> parent;
    std::uint32_t key;
  };
  std::vector<Pending> pending;
  const auto &ids = *out.title_source.full_ids_u32;
  for (std::size_t i = ids.size(); i > 0; --i)
    pending.push_back({static_cast<std::int32_t>(i - 1), std::nullopt, ids[i - 1]});
  const auto &raw = b.following_2921350;
  while (!pending.empty()) {
    const auto item = pending.back();
    pending.pop_back();
    game::ContextSourceFollowing2921350TitleWalkV1 row{};
    row.native_index = static_cast<std::int32_t>(out.title_walk.size());
    row.root_index = item.root; row.parent_index = item.parent;
    row.requested_full_id_u32 = item.key;
    const auto finish = [&]() {
      if (!row.reason.empty() && out.reason.empty()) out.reason = row.reason;
      const bool complete = row.reason.empty();
      out.title_walk.push_back(std::move(row));
      return complete;
    };
    const auto title = Following2921350Resolve(b, raw.title_storage_slot, raw.title_fallback_slot,
        item.key, 0x10, row.selection, row.selected_full_id_u32, row.reason);
    if (!title) { if (row.reason.empty()) row.reason = "following2921350_title_unavailable"; finish(); return false; }
    row.title_identity = TraitStageIdentity(title);
    const auto definition = Read<const void *>(b, title, 0x48);
    if (!definition || !*definition) { row.reason = "following2921350_title_definition_unavailable"; finish(); return false; }
    row.definition_identity = TraitStageIdentity(*definition);
    row.tier_raw_i32 = Read<std::int32_t>(b, *definition, 0x64);
    if (!row.tier_raw_i32) { row.reason = "following2921350_title_tier_unavailable"; finish(); return false; }
    if (*row.tier_raw_i32 > 1) {
      row.collected = false;
      if (!Following2921350Ids(b, Offset(title, 0xF0), row.children_count_raw,
            row.children_array_present, row.child_ids_u32, row.reason)) { finish(); return false; }
      for (std::size_t i = row.child_ids_u32->size(); i > 0; --i)
        pending.push_back({item.root, row.native_index, (*row.child_ids_u32)[i - 1]});
    } else {
      const bool first = *row.tier_raw_i32 == 1 && std::none_of(collected.begin(), collected.end(),
          [title](const auto &entry) { return entry.title == title; });
      row.collected = first;
      if (first) collected.push_back({title, row.native_index});
    }
    finish();
  }
  return true;
}
const void *Following2921350Province(const ContextSourceBindingsV1 &b,
    const Following2921350CollectedTitle &collected,
    game::ContextSourceFollowing2921350ProvinceV1 &out) {
  const auto &raw = b.following_2921350;
  const void *title = collected.title;
  std::optional<std::uint32_t> next_id;
  std::optional<std::string> next_selection;
  std::optional<std::uint32_t> next_selected_full;
  for (;;) {
    game::ContextSourceFollowing2921350ProvinceStepV1 step{};
    step.native_index = static_cast<std::int32_t>(out.steps.size());
    step.title_identity = TraitStageIdentity(title);
    step.requested_full_id_u32 = next_id; step.selection = next_selection;
    step.selected_full_id_u32 = next_selected_full;
    const auto fail = [&](const char *reason) {
      step.reason = reason; out.reason = reason;
      out.steps.push_back(std::move(step));
      return static_cast<const void *>(nullptr);
    };
    const auto definition = Read<const void *>(b, title, 0x48);
    if (!definition || !*definition) return fail("following2921350_province_title_definition_unavailable");
    step.definition_identity = TraitStageIdentity(*definition);
    step.tier_raw_i32 = Read<std::int32_t>(b, *definition, 0x64);
    if (!step.tier_raw_i32) return fail("following2921350_province_title_tier_unavailable");
    if (*step.tier_raw_i32 != 2) {
      out.steps.push_back(std::move(step));
      const auto province = Read<const void *>(b, title, 0x338);
      if (!province || !*province) { out.reason = "following2921350_province_pointer_unavailable"; return nullptr; }
      out.province_identity = TraitStageIdentity(*province);
      out.magic_u32 = Read<std::uint32_t>(b, *province, 0x85C);
      if (!out.magic_u32) { out.reason = "following2921350_province_magic_unavailable"; return nullptr; }
      out.admitted = *out.magic_u32 == 0x50726F76U;
      return *province;
    }
    step.first_child_count_raw = Read<std::int32_t>(b, title, 0x11C);
    if (!step.first_child_count_raw) return fail("following2921350_province_first_child_count_unavailable");
    if (*step.first_child_count_raw == 0) {
      step.first_child_full_id_u32 = 0xFFFFFFFFU;
    } else {
      const auto data = Read<const void *>(b, title, 0x110);
      if (data) step.first_child_array_present = *data != nullptr;
      if (!data || !*data) return fail("following2921350_province_first_child_array_unavailable");
      step.first_child_full_id_u32 = Read<std::uint32_t>(b, *data);
      if (!step.first_child_full_id_u32) return fail("following2921350_province_first_child_id_unavailable");
    }
    next_id = step.first_child_full_id_u32;
    next_selection.reset(); next_selected_full.reset();
    std::string reason;
    const auto child = Following2921350Resolve(b, raw.title_storage_slot, raw.title_fallback_slot,
        *next_id, 0x10, next_selection, next_selected_full, reason);
    out.steps.push_back(std::move(step));
    if (!child) {
      game::ContextSourceFollowing2921350ProvinceStepV1 missing{};
      missing.native_index = static_cast<std::int32_t>(out.steps.size());
      missing.requested_full_id_u32 = next_id; missing.selection = next_selection;
      missing.selected_full_id_u32 = next_selected_full;
      missing.reason = reason.empty() ? "following2921350_province_child_unavailable" : reason;
      out.reason = missing.reason; out.steps.push_back(std::move(missing)); return nullptr;
    }
    title = child;
  }
}
game::ContextSourceFollowing2921350MapV1 Following2921350Map(
    const ContextSourceBindingsV1 &b, const void *object, std::uint32_t province_id) {
  game::ContextSourceFollowing2921350MapV1 out{};
  const auto finish = [&]() { AfterFinish(out); return out; };
  const auto data = Read<const void *>(b, object, 0xC8);
  if (!data || !*data) { out.reason = "following2921350_map_data_unavailable"; return finish(); }
  out.data_identity = TraitStageIdentity(*data);
  out.mask_raw_i32 = Read<std::int32_t>(b, object, 0xD4);
  if (!out.mask_raw_i32) { out.reason = "following2921350_map_mask_unavailable"; return finish(); }
  out.overflow_raw_u8 = Read<std::uint8_t>(b, object, 0xD8);
  if (!out.overflow_raw_u8) { out.reason = "following2921350_map_overflow_unavailable"; return finish(); }
  std::uint32_t hash = 0x811C9DC5U;
  for (std::uint32_t shift = 0; shift != 32; shift += 8)
    hash = (hash ^ ((province_id >> shift) & 0xFFU)) * 0x1000193U;
  std::int64_t index = static_cast<std::int64_t>(AfterWrap32(hash)) &
                       static_cast<std::int64_t>(*out.mask_raw_i32);
  const std::int64_t end = static_cast<std::int64_t>(*out.mask_raw_i32) + 1 + *out.overflow_raw_u8;
  std::uint8_t probe = 1;
  for (;;) {
    game::ContextSourceFollowing2921350MapProbeV1 row{};
    row.native_index = static_cast<std::int32_t>(out.probes.size());
    row.bucket_index_i64 = index;
    const auto bucket = Following2921350At(*data, index * 0x38);
    row.distance_raw_u8 = Read<std::uint8_t>(b, bucket, 4);
    if (!row.distance_raw_u8) row.reason = "following2921350_map_distance_unavailable";
    else if (*row.distance_raw_u8 < probe) { out.found = false; out.operand_q64 = 0; }
    else {
      row.key_raw_u32 = Read<std::uint32_t>(b, bucket, 8);
      if (!row.key_raw_u32) row.reason = "following2921350_map_key_unavailable";
      else if (*row.key_raw_u32 == province_id) {
        out.found = index != end;
        if (*out.found) {
          row.operand_q64 = Read<std::int64_t>(b, bucket, 0x30);
          out.operand_q64 = row.operand_q64;
          if (!row.operand_q64) row.reason = "following2921350_map_operand_unavailable";
        } else out.operand_q64 = 0;
      }
    }
    const bool done = out.found.has_value();
    if (!row.reason.empty()) out.reason = row.reason;
    out.probes.push_back(std::move(row));
    if (done || !out.reason.empty()) return finish();
    ++index; probe = static_cast<std::uint8_t>(probe + 1U);
  }
}
game::ContextSourceFollowing2921350TierV1 Following2921350Tier(
    const ContextSourceBindingsV1 &b, const void *definition, std::int64_t operand) {
  game::ContextSourceFollowing2921350TierV1 out{};
  const auto finish = [&]() { AfterFinish(out); return out; };
  out.count_raw_i32 = Read<std::int32_t>(b, definition, 0xEDC);
  if (!out.count_raw_i32) { out.reason = "following2921350_tier_count_unavailable"; return finish(); }
  out.thresholds_q64.emplace();
  const void *data = nullptr;
  std::int32_t ordinal = *out.count_raw_i32;
  if (*out.count_raw_i32 > 0) {
    const auto rows = Read<const void *>(b, definition, 0xED0);
    if (!rows || !*rows) { out.reason = "following2921350_tier_data_unavailable"; return finish(); }
    data = *rows; out.data_identity = TraitStageIdentity(data);
    for (std::int32_t i = 0; i < *out.count_raw_i32; ++i) {
      const auto threshold = Read<std::int64_t>(b, data, static_cast<std::size_t>(i) * 0x548 + 0x540);
      if (!threshold) { out.reason = "following2921350_tier_threshold_unavailable"; return finish(); }
      out.thresholds_q64->push_back(*threshold);
      if (operand < *threshold) { ordinal = i; break; }
    }
  }
  out.selected_index_raw_i32 = AfterWrap32(static_cast<std::uint32_t>(ordinal) - 1U);
  const void *row = nullptr;
  if (*out.selected_index_raw_i32 >= 0 && *out.selected_index_raw_i32 < *out.count_raw_i32) {
    out.selection = "indexed_tier";
    row = Offset(data, static_cast<std::size_t>(*out.selected_index_raw_i32) * 0x548);
  } else {
    out.default_guard_raw_i32 = Read<std::int32_t>(b, b.following_2921350.tier_default_guard);
    if (!out.default_guard_raw_i32) { out.reason = "following2921350_tier_default_guard_unavailable"; return finish(); }
    if (*out.default_guard_raw_i32 == 0 || *out.default_guard_raw_i32 == -1) {
      out.selection = "cold_default_5d65b00";
      out.reason = out.pc.reason = "tier_default_2560620_result";
      return finish();
    }
    out.selection = "initialized_default_5d65b00";
    row = b.following_2921350.tier_default_row;
  }
  out.pc = AfterPc(b, Offset(row, 0x380));
  if (!out.pc.reason.empty()) out.reason = out.pc.reason;
  return finish();
}
game::ContextSourceFollowing2921350SourceV1 Following2921350Source(
    const ContextSourceBindingsV1 &b, std::int32_t native_index,
    std::uint32_t requested, std::uint32_t province_id, std::int32_t group_count) {
  game::ContextSourceFollowing2921350SourceV1 out{};
  out.native_index = native_index; out.requested_full_id_u32 = requested;
  const auto &raw = b.following_2921350;
  const auto incomplete = [&]() {
    if (out.map.reason.empty()) out.map.reason = out.reason;
    if (out.tiers.reason.empty()) out.tiers.reason = out.reason;
    return out;
  };
  const auto object = Following2921350Resolve(b, raw.source_storage_slot, raw.source_fallback_slot,
      requested, 8, out.selection, out.selected_full_id_u32, out.reason);
  if (!object) { if (out.reason.empty()) out.reason = "following2921350_source_unavailable"; return incomplete(); }
  out.object_identity = TraitStageIdentity(object);
  const auto definition = Read<const void *>(b, object, 0x88);
  if (!definition || !*definition) { out.reason = "following2921350_source_definition_unavailable"; return incomplete(); }
  out.definition_identity = TraitStageIdentity(*definition);
  out.group_index_raw_i32 = Read<std::int32_t>(b, *definition, 0x10);
  if (!out.group_index_raw_i32) { out.reason = "following2921350_group_index_unavailable"; return incomplete(); }
  if (*out.group_index_raw_i32 < 0 || *out.group_index_raw_i32 >= group_count) {
    out.reason = "following2921350_group_index_outside_manager"; return incomplete();
  }
  out.map = Following2921350Map(b, object, province_id);
  if (!out.map.ready) { out.reason = out.map.reason; return incomplete(); }
  out.tiers = Following2921350Tier(b, *definition, *out.map.operand_q64);
  if (!out.tiers.ready) out.reason = out.tiers.reason;
  return out;
}
game::ContextSourceFollowing2921350InputsV1 Following2921350Inputs(
    const ContextSourceBindingsV1 &b, const void *character, std::int32_t id) {
  game::ContextSourceFollowing2921350InputsV1 out{};
  out.character_id = id;
  out.character_identity = TraitStageIdentity(character);
  out.manager.reason = "following2921350_title_stream_unavailable";
  const auto finish = [&]() { AfterFinish(out); return out; };
  const auto actual_id = Read<std::int32_t>(b, character, 0x18);
  if (!actual_id) {
    out.reason = out.title_source.reason = "following2921350_character_full_id_unavailable";
    return finish();
  }
  out.character_id = *actual_id;
  if (*actual_id != id) {
    out.reason = out.title_source.reason = "following2921350_character_full_id_mismatch";
    return finish();
  }
  out.title_source = Following2921350TitleSource(b, character);
  if (!out.title_source.ready) { out.reason = out.title_source.reason; return finish(); }
  std::vector<Following2921350CollectedTitle> collected;
  if (!Following2921350Titles(b, out, collected)) return finish();
  std::vector<const void *> provinces;
  for (const auto &title : collected) {
    game::ContextSourceFollowing2921350ProvinceV1 province{};
    province.native_index = static_cast<std::int32_t>(out.provinces.size());
    province.title_walk_index = title.walk_index;
    const auto object = Following2921350Province(b, title, province);
    if (!object || !province.reason.empty()) {
      out.reason = province.reason;
      out.provinces.push_back(std::move(province));
      return finish();
    }
    // Distinct collected Titles retain duplicate Province pointer occurrences.
    provinces.push_back(object); out.provinces.push_back(std::move(province));
  }
  out.manager.reason.clear();
  const auto manager = Read<const void *>(b, b.following_2921350.manager_slot);
  if (manager) out.manager.loaded = *manager != nullptr;
  if (!manager || !*manager) out.manager.reason = "following2921350_manager_unloaded";
  else {
    out.manager.identity = TraitStageIdentity(*manager);
    out.manager.group_count_raw_i32 = Read<std::int32_t>(b, *manager, 0x5C);
    if (!out.manager.group_count_raw_i32) out.manager.reason = "following2921350_manager_count_unavailable";
    else if (*out.manager.group_count_raw_i32 < 0) out.manager.reason = "following2921350_negative_manager_count";
  }
  AfterFinish(out.manager);
  if (!out.manager.ready) { out.reason = out.manager.reason; return finish(); }
  for (std::size_t i = 0; i < out.provinces.size(); ++i) {
    auto &province = out.provinces[i];
    if (province.admitted != true) continue;
    const auto object = provinces[i];
    province.full_id_u32 = Read<std::uint32_t>(b, object, 0x10);
    if (!province.full_id_u32) province.reason = "following2921350_province_id_unavailable";
    else if (Following2921350Ids(b, Offset(object, 0x7A8), province.source_count_raw,
                 province.source_array_present, province.source_ids_u32, province.reason)) {
      for (std::size_t j = 0; j < province.source_ids_u32->size(); ++j) {
        auto source = Following2921350Source(b, static_cast<std::int32_t>(j),
            (*province.source_ids_u32)[j], *province.full_id_u32, *out.manager.group_count_raw_i32);
        // Continue the known occurrence census even if one selected PC is cold.
        if (!source.reason.empty() && province.reason.empty()) province.reason = source.reason;
        province.sources.push_back(std::move(source));
      }
    }
    if (!province.reason.empty() && out.reason.empty()) out.reason = province.reason;
  }
  return finish();
}
