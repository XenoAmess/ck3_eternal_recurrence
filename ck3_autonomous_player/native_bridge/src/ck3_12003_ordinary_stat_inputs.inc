// 26344C0 non-special/non-GDbo ->30C3BA0: actual selected Character sources.
void *OrdinaryResolvedOrFallback12003(
    void **storage, void **fallback, std::int32_t id,
    std::size_t id_offset, bool *used_fallback = nullptr) noexcept {
  void *const resolved = ResolveStoredComponent(storage, id, id_offset);
  if (used_fallback) *used_fallback = resolved == nullptr;
  return resolved != nullptr ? resolved : (fallback ? *fallback : nullptr);
}

void ReadOrdinaryRegimentStatInputs12003(
    const CombatBindings &bindings, void *regiment,
    CombatRegimentSnapshot &row) noexcept {
  if (!bindings.ordinary_stat_inputs_enabled ||
      row.kind.status != CombatObservationStatus::available ||
      row.kind.value != "levy") return;
  auto &out = row.ordinary_stat_inputs_v1.emplace();
  for (std::size_t i = 0; i != out.loaded_bases.size(); ++i)
    if (bindings.ordinary_stat_loaded_bases[i])
      out.loaded_bases[i] = *bindings.ordinary_stat_loaded_bases[i];

  auto first_id = std::int32_t{-1};
  if (LoadAt<std::int32_t>(regiment, 0x2C) != 0) {
    const auto *first_row = LoadAt<const void *>(regiment, 0x20);
    if (!first_row) { out.unavailable_reason = "ordinary_first_row_unavailable"; return; }
    first_id = LoadAt<std::int32_t>(first_row, 8);
  }
  const auto *selected = OrdinaryResolvedOrFallback12003(
      bindings.ordinary_regiment_storage_slot, bindings.ordinary_regiment_fallback_slot,
      first_id, 0x10);
  if (!selected) { out.unavailable_reason = "ordinary_selected_regiment_unavailable"; return; }
  const auto selector_id = LoadAt<std::int32_t>(selected, 0x130);
  const auto direct_id = LoadAt<std::int32_t>(selected, 0x12C);
  auto character_id = std::int32_t{-1};
  if (selector_id == -1) character_id = direct_id;
  else if (direct_id == -1) {
    const auto *nested = OrdinaryResolvedOrFallback12003(
        bindings.ordinary_selector_storage_slot, bindings.ordinary_selector_fallback_slot,
        selector_id, 0x10);
    if (!nested) { out.unavailable_reason = "ordinary_nested_selector_unavailable"; return; }
    character_id = LoadAt<std::int32_t>(nested, 0x128);
  }
  bool used_fallback = false;
  auto *character = OrdinaryResolvedOrFallback12003(
      bindings.character_storage_slot, bindings.ordinary_character_fallback_slot,
      character_id, 0x18, &used_fallback);
  if (!character) { out.unavailable_reason = "ordinary_selected_character_unavailable"; return; }
  out.selected_character_full_id = LoadAt<std::int32_t>(character, 0x18);
  out.character_resolution = used_fallback ? "native_fallback" : "generation_resolved";
  const auto *context = bindings.get_character_modifier_aggregator
      ? bindings.get_character_modifier_aggregator(character) : nullptr;
  if (!context) { out.unavailable_reason = "ordinary_selected_context_unavailable"; return; }
  const auto count = LoadAt<std::int32_t>(context, 0x74);
  out.aggregate_count = count;
  if (count == 0) {
    out.aggregate_keys_u16.emplace();
    out.aggregate_values_q64.emplace();
  } else if (count > 0) {
    const auto *keys = LoadAt<const std::uint16_t *>(context, 0x68);
    const auto *values = LoadAt<const std::int64_t *>(context, 0xD0);
    if (keys) out.aggregate_keys_u16.emplace(keys, keys + count);
    if (values) out.aggregate_values_q64.emplace(values, values + count);
  }
  out.available = out.aggregate_keys_u16.has_value() &&
      out.aggregate_values_q64.has_value() &&
      std::all_of(out.loaded_bases.begin(), out.loaded_bases.end(),
                  [](const auto &value) { return value.has_value(); });
  out.unavailable_reason = out.available ? "" : "ordinary_loaded_or_aggregate_operand_unavailable";
}
