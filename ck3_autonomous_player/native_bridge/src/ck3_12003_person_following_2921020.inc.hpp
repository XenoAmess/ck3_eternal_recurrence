// Included after AfterRegistry/AfterPc helpers. Readonly numeric operands only;
// no native256EA10/2491D80/2303120/291B3D0/effect/diagnostic is invoked.
void Following2921020OwnerHeader(const ContextSourceBindingsV1 &b,
    const void *header, game::ContextSourceFollowing2921020InputsV1 &out) {
  out.owner_weighted_header.emplace();
  auto &span = *out.owner_weighted_header;
  span.selected_source = "selected_28";
  span.count = Read<std::int32_t>(b, header, 0xC);
  out.owner_header_ready = false;
  if (!span.count) span.reason = "selected_source_count_unavailable";
  else if (*span.count <= 0) {
    span.rows.emplace();
    out.owner_header_ready = true;
    return;
  } else {
    const auto data = Read<const void *>(b, header);
    if (!data || !*data) span.reason = "selected_source_rows_unavailable";
    else {
      span.rows.emplace();
      std::vector<const void *> definitions;
      for (std::int32_t i = 0; i < *span.count; ++i) {
        const void *address = Offset(*data, static_cast<std::size_t>(i) * 0x48);
        game::ContextSourceWeightedRowV1 row{};
        row.native_index = i;
        const auto definition = Read<const void *>(b, address);
        if (!definition || !*definition) Reason(span.reason, "selected_source_definition_unavailable");
        else {
          row.definition_identity = TraitStageIdentity(*definition);
          if (std::find(definitions.begin(), definitions.end(), *definition) == definitions.end()) {
            definitions.push_back(*definition);
            game::ContextSourceDefinitionBlockV1 block{};
            block.definition_identity = *row.definition_identity;
            block.properties = Properties(b, Offset(*definition, 0x40));
            if (!block.properties || !PropertiesReady(*block.properties) || !block.properties->reason.empty())
              Reason(out.reason, "following2921020_owner_property_unavailable");
            out.owner_definition_blocks.push_back(std::move(block));
          }
        }
        row.weight_q64 = Read<std::int64_t>(b, address, 0x30);
        if (!row.weight_q64) Reason(span.reason, "selected_source_weight_unavailable");
        span.rows->push_back(std::move(row));
      }
      out.owner_header_ready = span.reason.empty() &&
          std::all_of(out.owner_definition_blocks.begin(), out.owner_definition_blocks.end(),
              [](const auto &block) { return block.properties && PropertiesReady(*block.properties) && block.properties->reason.empty(); });
    }
  }
  if (!span.reason.empty()) Reason(out.reason, span.reason.c_str());
}

game::ContextSourceFollowing2921020InputsV1 Following2921020Inputs(
    const ContextSourceBindingsV1 &b, const void *character, std::int32_t id) {
  game::ContextSourceFollowing2921020InputsV1 out{};
  out.character_id = id;
  const auto finish = [&]() { AfterFinish(out); return out; };
  const auto &raw = b.following_2921020;
  const auto component = Read<const void *>(b, character, 0x1C0);
  if (!component) { out.reason = "following2921020_component_unavailable"; return finish(); }
  out.component_present = *component != nullptr;
  const std::optional<std::int32_t> requested = *component
      ? Read<std::int32_t>(b, *component, 0x1B0) : std::optional<std::int32_t>{-1};
  out.requested_full_id_raw = requested;
  if (!requested) { out.reason = "following2921020_requested_id_unavailable"; return finish(); }
  const void *object = AfterRegistry(b, raw.lege_storage_slot, raw.lege_fallback_slot,
      nullptr, 8, "registry_full_id_8", out.requested_full_id_raw,
      out.resolution_selection, out.selected_full_id_raw, out.reason, &requested);
  if (!object) return finish();
  out.object_identity = TraitStageIdentity(object);
  out.magic_u32 = Read<std::uint32_t>(b, object, 0xC);
  if (!out.magic_u32) { out.reason = "following2921020_magic_unavailable"; return finish(); }
  if (*out.magic_u32 != 0x4C656765U) { out.admitted = false; return finish(); }
  out.full_id_raw = Read<std::int32_t>(b, object, 8);
  if (!out.full_id_raw) { out.reason = "following2921020_full_id_unavailable"; return finish(); }
  if (*out.full_id_raw == -1) { out.admitted = false; return finish(); }
  out.admitted = true;
  out.character_full_id_raw = Read<std::int32_t>(b, character, 0x18);
  out.owner_full_id_raw = Read<std::int32_t>(b, object, 0x288);
  if (out.character_full_id_raw && out.owner_full_id_raw)
    out.owner_matches = *out.character_full_id_raw == *out.owner_full_id_raw;
  else Reason(out.reason, "following2921020_owner_comparison_unavailable");
  const auto definition = Read<const void *>(b, object, 0x78);
  if (definition && *definition) out.definition_identity = TraitStageIdentity(*definition);
  else Reason(out.reason, "following2921020_definition_unavailable");
  out.rank_raw_i8 = Read<std::int8_t>(b, object, 0x250);
  const auto table = Read<const void *>(b, object, 0x70);
  if (table && *table) out.table_identity = TraitStageIdentity(*table);
  if (!out.rank_raw_i8) {
    Reason(out.reason, "following2921020_rank_unavailable"); return finish();
  }
  if (*out.rank_raw_i8 < 0 || *out.rank_raw_i8 >= 3) {
    out.tier_selection = "diagnostic_3f7ab90_outcome_unobserved";
    out.reason = "rank_diagnostic_3f7ab90_result";
    return finish();
  }
  out.tier_selection = "direct_rank_0_2";
  if (!table || !*table) {
    Reason(out.reason, "following2921020_table_unavailable"); return finish();
  }
  const void *selected = Offset(*table, 0x438 + static_cast<std::size_t>(*out.rank_raw_i8) * 0x3478);
  out.selected_row_identity = TraitStageIdentity(selected);
  if (!out.owner_matches) return finish();
  const bool owner = *out.owner_matches;
  if (owner) Following2921020OwnerHeader(b, Offset(object, 0x28), out);
  if (!definition || !*definition) return finish();
  out.base_pc = AfterPc(b, Offset(*definition, owner ? 0x420U : 0x5E0U));
  out.tier_pc = AfterPc(b, Offset(selected, owner ? 0x2BF8U : 0x2DB8U));
  out.composite_ready = out.base_pc.reason.empty() && out.tier_pc.reason.empty();
  if (!out.base_pc.reason.empty()) Reason(out.reason, out.base_pc.reason.c_str());
  if (!out.tier_pc.reason.empty()) Reason(out.reason, out.tier_pc.reason.c_str());
  return finish();
}
