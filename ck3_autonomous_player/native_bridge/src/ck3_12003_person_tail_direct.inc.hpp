// Source-closed sparse tail families. No intervening helper is reconstructed.
game::ContextSourceTailGovernmentV1 TailGovernment(
    const ContextSourceBindingsV1 &b, const void *character,
    std::vector<const void *> &ids) {
  game::ContextSourceTailGovernmentV1 out{};
  const auto fail = [&](const char *reason) { out.reason = reason; return out; };
  const auto land = Read<const void *>(b, character, 0x1C0);
  if (!land) return fail("tail_government_land_unavailable");
  out.land_present = *land != nullptr;
  if (!*land) {
    out.admitted = false;
    return PostReady(std::move(out));
  }
  const void *government = RemainingGovernment(
      b, character, out.government_selection, out.reason);
  if (!government) return out;
  out.government_identity = Identity(ids, government, "tail");
  out.government_magic_raw = Read<std::uint32_t>(b, government, 0x38);
  if (!out.government_magic_raw) return fail("tail_government_magic_unavailable");
  out.admitted = *out.government_magic_raw == 0x4744624FU;
  if (!*out.admitted) return PostReady(std::move(out));
  const void *pc870 = Offset(government, 0x870);
  out.property_870_identity = Identity(ids, pc870, "tail");
  out.property_870 = Properties(b, pc870);
  // Independent +870 is retained even if later admission bytes are unavailable.
  const auto second_land = Read<const void *>(b, character, 0x1C0);
  if (!second_land) return fail("tail_government_second_land_unavailable");
  out.second_land_present = *second_land != nullptr;
  if (!*second_land) {
    out.additional_a30_admitted = false;
  } else {
    const auto subcarrier = Read<const void *>(b, *second_land, 0x1C0);
    if (!subcarrier || !*subcarrier) return fail("tail_government_subcarrier_unavailable");
    out.subcarrier_magic_raw = Read<std::uint32_t>(b, *subcarrier, 0xC);
    if (!out.subcarrier_magic_raw) return fail("tail_government_subcarrier_magic_unavailable");
    if (*out.subcarrier_magic_raw == 0x5362436FU) {
      out.subcarrier_full_id_raw = Read<std::int32_t>(b, *subcarrier, 8);
      if (!out.subcarrier_full_id_raw) return fail("tail_government_subcarrier_id_unavailable");
      out.additional_a30_admitted = *out.subcarrier_full_id_raw == -1;
    } else {
      out.additional_a30_admitted = true;
    }
  }
  if (*out.additional_a30_admitted) {
    const void *pca30 = Offset(government, 0xA30);
    out.property_a30_identity = Identity(ids, pca30, "tail");
    out.property_a30 = Properties(b, pca30);
  }
  if (!PropertiesReady(*out.property_870) ||
      (out.property_a30 && !PropertiesReady(*out.property_a30)))
    return fail("tail_government_consumed_properties_unavailable");
  return PostReady(std::move(out));
}

const void *TailWeightedSelection(const ContextSourceBindingsV1 &b,
    std::int32_t key, std::optional<std::string> &selection, std::string &reason) {
  const auto store = Read<const void *>(b, b.tail_weighted_storage_slot);
  if (!store) { reason = "tail_weighted_store_unavailable"; return nullptr; }
  if (*store) {
    const auto capacity = Read<std::uint32_t>(b, *store, 0x2C);
    if (!capacity) { reason = "tail_weighted_capacity_unavailable"; return nullptr; }
    const auto index = static_cast<std::uint32_t>(key) & 0xFFFFFFU;
    if (index < *capacity) {
      const auto table = Read<const void *>(b, *store, 0x20);
      if (!table) { reason = "tail_weighted_table_unavailable"; return nullptr; }
      const auto object = Read<const void *>(b, *table,
          static_cast<std::size_t>(index) * 16 + 8);
      if (!object) { reason = "tail_weighted_slot_unavailable"; return nullptr; }
      if (*object) {
        const auto full_id = Read<std::int32_t>(b, *object, 8);
        if (!full_id) { reason = "tail_weighted_full_id_unavailable"; return nullptr; }
        if (*full_id == key) { selection = "registry_full_id_8"; return *object; }
      }
    }
  }
  const auto fallback = Read<const void *>(b, b.tail_weighted_fallback_slot);
  if (!fallback) { reason = "tail_weighted_fallback_unavailable"; return nullptr; }
  selection = "native_fallback";
  if (!*fallback) reason = "tail_weighted_native_fallback_null";
  return *fallback;
}

game::ContextSourceTailWeightedV1 TailWeighted(
    const ContextSourceBindingsV1 &b, const void *character,
    std::vector<const void *> &ids) {
  game::ContextSourceTailWeightedV1 out{};
  const auto fail = [&](const char *reason) { out.reason = reason; return out; };
  const auto carrier = Read<const void *>(b, character, 0x1B0);
  if (!carrier) return fail("tail_weighted_carrier_unavailable");
  out.carrier_present = *carrier != nullptr;
  if (!*carrier) {
    out.rows.emplace();
    return PostReady(std::move(out));
  }
  out.key_274_raw = Read<std::int32_t>(b, *carrier, 0x274);
  if (!out.key_274_raw) return fail("tail_weighted_key_unavailable");
  if (*out.key_274_raw == -1) {
    out.rows.emplace();
    return PostReady(std::move(out));
  }
  const void *selected = TailWeightedSelection(
      b, *out.key_274_raw, out.selection, out.reason);
  if (!selected) return out;
  out.selected_identity = Identity(ids, selected, "tail");
  out.count_63c = Read<std::int32_t>(b, selected, 0x63C);
  if (!out.count_63c) return fail("tail_weighted_count_unavailable");
  if (*out.count_63c == 0) {
    out.rows.emplace();
    return PostReady(std::move(out));
  }
  if (*out.count_63c < 0) return fail("tail_weighted_negative_count");
  const auto array = Read<const void *>(b, selected, 0x630);
  if (!array) return fail("tail_weighted_array_unavailable");
  out.array_present = *array != nullptr;
  if (!*array) return fail("tail_weighted_array_null");
  out.rows.emplace();
  bool ready = true;
  for (std::int32_t index = 0; index < *out.count_63c; ++index) {
    game::ContextSourceTailWeightedRowV1 row{};
    row.native_index = index;
    const void *source = Offset(*array, static_cast<std::size_t>(index) * 16);
    const auto pc = Read<const void *>(b, source);
    row.weight_q64 = Read<std::int64_t>(b, source, 8);
    if (pc && *pc) {
      row.property_identity = Identity(ids, *pc, "tail");
      row.property_block = Properties(b, *pc);
    }
    if (!row.weight_q64 || !row.property_block || !PropertiesReady(*row.property_block)) {
      row.reason = "tail_weighted_row_operands_unavailable";
      ready = false;
    }
    out.rows->push_back(std::move(row));
  }
  if (!ready) return fail("tail_weighted_rows_partial");
  return PostReady(std::move(out));
}

game::ContextSourceTailDirectV1 TailDirect(const ContextSourceBindingsV1 &b,
    const void *character, std::int32_t character_id) {
  game::ContextSourceTailDirectV1 out{};
  out.character_id = character_id;
  std::vector<const void *> ids;
  out.government_870_a30 = TailGovernment(b, character, ids);
  out.carrier_weighted630 = TailWeighted(b, character, ids);
  if (out.government_870_a30.ready && out.carrier_weighted630.ready)
    return PostReady(std::move(out));
  out.reason = "tail_direct_families_partial";
  return out;
}
