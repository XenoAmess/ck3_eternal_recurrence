// Included inside the current source collector's anonymous namespace; reuses
// its readonly Read/Properties/Identity helpers without a new query or writer.
const void *HelperRegistry8(
    const ContextSourceBindingsV1 &b, const void *storage_slot,
    const void *fallback_slot, const void *key_address,
    std::optional<std::int32_t> &key_raw,
    std::optional<std::string> &selection, std::string &reason) {
  const auto store = Read<const void *>(b, storage_slot);
  if (!store) { reason = "helper_registry_store_unavailable"; return nullptr; }
  if (*store) {
    key_raw = Read<std::int32_t>(b, key_address);
    if (!key_raw) { reason = "helper_registry_key_unavailable"; return nullptr; }
    const auto index = static_cast<std::uint32_t>(*key_raw) & 0xFFFFFFU;
    const auto capacity = Read<std::uint32_t>(b, *store, 0x2C);
    if (!capacity) { reason = "helper_registry_capacity_unavailable"; return nullptr; }
    if (index < *capacity) {
      const auto table = Read<const void *>(b, *store, 0x20);
      if (!table) { reason = "helper_registry_table_unavailable"; return nullptr; }
      const auto object = Read<const void *>(b, *table,
          static_cast<std::size_t>(index) * 16 + 8);
      if (!object) { reason = "helper_registry_slot_unavailable"; return nullptr; }
      if (*object) {
        const auto id = Read<std::int32_t>(b, *object, 8);
        if (!id) { reason = "helper_registry_full_id_unavailable"; return nullptr; }
        if (*id == *key_raw) {
          selection = "registry_full_id_8";
          return *object;
        }
      }
    }
  }
  const auto fallback = Read<const void *>(b, fallback_slot);
  if (!fallback) { reason = "helper_registry_fallback_unavailable"; return nullptr; }
  selection = "native_fallback";
  if (!*fallback) reason = "helper_registry_native_fallback_null";
  return *fallback;
}

void HelperFinishFamily(game::ContextSourceHelperFamilyV1 &out) {
  out.ready = out.reason.empty();
  out.status = out.ready ? "available" : "partial";
}

game::ContextSourceHelperFamilyV1 HelperPointerFamily(
    const ContextSourceBindingsV1 &b, const void *header,
    const char *source, std::size_t property_offset,
    std::optional<std::size_t> gate_offset,
    std::vector<const void *> &identities) {
  game::ContextSourceHelperFamilyV1 out{};
  out.selected_source = source;
  out.admitted = true;
  const auto data = Read<const void *>(b, header);
  if (data) out.array_present = *data != nullptr;
  out.count = Read<std::int32_t>(b, header, 0xC);
  if (!data || !out.count) out.reason = "helper_source_header_unavailable";
  else if (*out.count < 0) out.reason = "helper_negative_count_unrepresentable";
  else if (*out.count == 0) out.rows.emplace();
  else if (!*data) out.reason = "helper_positive_count_null_array";
  else {
    out.rows.emplace();
    for (std::int32_t i = 0; i < *out.count; ++i) {
      game::ContextSourceHelperRowV1 row{};
      row.native_index = i;
      const auto pointer = Read<const void *>(b, *data,
          static_cast<std::size_t>(i) * 8);
      if (!pointer || !*pointer) row.reason = "helper_source_pointer_unavailable";
      else {
        row.source_identity = Identity(identities, *pointer, "h");
        if (gate_offset) {
          row.gate_raw = Read<std::int32_t>(b, *pointer, *gate_offset);
          if (row.gate_raw) row.admitted = *row.gate_raw != 0;
          else row.reason = "helper_source_gate_unavailable";
        } else row.admitted = true;
        if (row.admitted == true) {
          row.property_block = Properties(b, Offset(*pointer, property_offset));
          if (!PropertiesReady(*row.property_block))
            row.reason = "helper_source_properties_unavailable";
        }
      }
      if (!row.reason.empty()) Reason(out.reason, row.reason.c_str());
      out.rows->push_back(std::move(row));
    }
  }
  HelperFinishFamily(out);
  return out;
}

const void *HelperManagerDefinition(
    const ContextSourceBindingsV1 &b, const void *manager,
    const void *character, game::ContextSourceHelper291f0a0V1 &out,
    std::vector<const void *> &identities, std::string &reason) {
  const auto magic = Read<std::uint32_t>(b, character, 0x1C);
  if (!magic) { reason = "helper_character_magic_unavailable"; return nullptr; }
  bool valid = *magic == 0x43686172U;
  if (valid) {
    const auto id = Read<std::int32_t>(b, character, 0x18);
    if (!id) { reason = "helper_character_full_id_unavailable"; return nullptr; }
    valid = *id != -1;
  }
  if (!valid) {
    const auto fallback = Read<const void *>(b, b.helper_invalid_character_fallback_slot);
    if (!fallback) { reason = "helper_invalid_character_fallback_unavailable"; return nullptr; }
    out.manager_definition_selection = "invalid_character_native_fallback";
    if (*fallback) out.manager_definition_identity = Identity(identities, *fallback, "h");
    else reason = "helper_invalid_character_native_fallback_null";
    return *fallback;
  }
  std::optional<std::int32_t> first_key, second_key, third_key;
  std::optional<std::string> first_selection, second_selection, third_selection;
  const void *first = HelperRegistry8(b, b.selector_a_storage_slot,
      b.selector_a_initial_fallback_slot, Offset(character, 0xB4),
      first_key, first_selection, reason);
  if (!first) return nullptr;
  const void *second = HelperRegistry8(b, b.selector_a_second_storage_slot,
      b.selector_a_second_fallback_slot, Offset(first, 0x4B8),
      second_key, second_selection, reason);
  if (!second) return nullptr;
  const void *third = HelperRegistry8(b, b.helper_third_storage_slot,
      b.helper_third_fallback_slot, Offset(second, 0x8C),
      third_key, third_selection, reason);
  if (!third) return nullptr;
  const auto key = Read<const void *>(b, third, 0x20);
  const auto data = Read<const void *>(b, manager, 0x50);
  const auto count = Read<std::int32_t>(b, manager, 0x5C);
  if (!key || !data || !count) { reason = "helper_manager_selection_header_unavailable"; return nullptr; }
  if (*count < 0) { reason = "helper_manager_negative_count_unrepresentable"; return nullptr; }
  for (std::int32_t i = 0; i < *count; ++i) {
    const auto definition = Read<const void *>(b, *data,
        static_cast<std::size_t>(i) * 8);
    if (!definition || !*definition) { reason = "helper_manager_definition_unavailable"; return nullptr; }
    // A11CC0/3F90910 are exact full-QWORD membership. Empty membership headers
    // still demand pointer0/countC; lazy CPU dispatch does not change equality.
    const auto keys = Read<const void *>(b, *definition, 0x40);
    const auto keys_count = Read<std::int32_t>(b, *definition, 0x4C);
    if (!keys || !keys_count) { reason = "helper_manager_membership_header_unavailable"; return nullptr; }
    if (*keys_count < 0) { reason = "helper_manager_membership_negative_count"; return nullptr; }
    for (std::int32_t k = 0; k < *keys_count; ++k) {
      const auto candidate = Read<const void *>(b, *keys,
          static_cast<std::size_t>(k) * 8);
      if (!candidate) { reason = "helper_manager_membership_element_unavailable"; return nullptr; }
      if (*candidate == *key) {
        out.manager_definition_selection = "first_matching_stored_definition";
        out.manager_definition_identity = Identity(identities, *definition, "h");
        return *definition;
      }
    }
  }
  const auto fallback = Read<const void *>(b, manager, 0xEF0);
  if (!fallback) { reason = "helper_manager_ef0_unavailable"; return nullptr; }
  out.manager_definition_selection = "manager_ef0";
  if (*fallback) out.manager_definition_identity = Identity(identities, *fallback, "h");
  else reason = "helper_manager_ef0_null";
  return *fallback;
}

const void *HelperRangePc(
    const ContextSourceBindingsV1 &b, const void *definition,
    game::ContextSourceHelper291f0a0V1 &out, std::string &reason) {
  out.range_count_raw = Read<std::int32_t>(b, definition, 0x64);
  if (!out.range_count_raw) { reason = "helper_range_count_unavailable"; return nullptr; }
  if (*out.range_count_raw < 0) { reason = "helper_range_negative_count_unrepresentable"; return nullptr; }
  if (*out.range_count_raw == 0) {
    out.range_selection = "inline_default_5d70fc0";
    out.default_pc_guard_raw = Read<std::int32_t>(b, b.helper_default_pc_guard_slot);
    if (!out.default_pc_guard_raw) reason = "helper_default_pc_guard_unavailable";
    else if (*out.default_pc_guard_raw == 0 || *out.default_pc_guard_raw == -1)
      reason = "helper_default_pc_not_initialized";
    return b.helper_default_pc;
  }
  const auto first_threshold = Read<std::int64_t>(b, b.helper_range_first_threshold_slot);
  if (!first_threshold) { reason = "helper_range_first_threshold_unavailable"; return nullptr; }
  if (*out.recipient_q64 <= *first_threshold) {
    const auto data = Read<const void *>(b, definition, 0x58);
    if (!data || !*data) { reason = "helper_range_data_unavailable"; return nullptr; }
    out.range_selection = "first_threshold";
    out.range_native_index = 0;
    return *data;
  }
  const auto last_threshold = Read<std::int64_t>(b, b.helper_range_last_threshold_slot);
  if (!last_threshold) { reason = "helper_range_last_threshold_unavailable"; return nullptr; }
  const auto data = Read<const void *>(b, definition, 0x58);
  if (!data || !*data) { reason = "helper_range_data_unavailable"; return nullptr; }
  if (*out.recipient_q64 >= *last_threshold) {
    out.range_selection = "last_threshold";
    out.range_native_index = *out.range_count_raw - 1;
    return Offset(*data, static_cast<std::size_t>(*out.range_native_index) * 0x218);
  }
  for (std::int32_t i = 0; i < *out.range_count_raw; ++i) {
    const void *row = Offset(*data, static_cast<std::size_t>(i) * 0x218);
    const auto upper = Read<std::int64_t>(b, row, 0x1E8);
    const auto lower = Read<std::int64_t>(b, row, 0x1E0);
    if (!upper || !lower) { reason = "helper_range_interval_unavailable"; return nullptr; }
    const auto recipient = *out.recipient_q64;
    const bool admitted = *upper < 0
        ? (*lower < recipient && recipient <= *upper)
        : ((*lower > 0 ? *lower <= recipient : *lower < recipient) && recipient < *upper);
    if (admitted) {
      out.range_selection = "first_matching_stored_interval";
      out.range_native_index = i;
      out.range_lower_q64 = lower;
      out.range_upper_q64 = upper;
      return row;
    }
  }
  const auto fallback = Read<const void *>(b, definition, 0x70);
  if (!fallback) { reason = "helper_range_fallback_70_unavailable"; return nullptr; }
  out.range_selection = "native_fallback_70";
  if (!*fallback) reason = "helper_range_native_fallback_null";
  return *fallback;
}

game::ContextSourceHelper291f0a0V1 Helper291f0a0(
    const ContextSourceBindingsV1 &b, const void *character,
    std::int32_t character_id,
    std::optional<std::int64_t> absent_recipient_q64 = std::nullopt,
    std::string_view absent_recipient_source = "absent_1c8_2bfac30_cached") {
  game::ContextSourceHelper291f0a0V1 out{};
  out.character_id = character_id;
  std::vector<const void *> identities;
  std::string first_reason;
  const void *first = HelperRegistry8(b, b.selector_a_storage_slot,
      b.selector_a_initial_fallback_slot, Offset(character, 0xB4),
      out.first_key_b4_raw, out.first_selection, first_reason);
  out.primary_direct = HelperPointerFamily(b, Offset(first, 0x20),
      "selected_first_inline_20", 0, std::nullopt, identities);
  if (!first_reason.empty()) {
    out.primary_direct.reason = first_reason;
    HelperFinishFamily(out.primary_direct);
  }

  auto &range = out.manager_range;
  range.selected_source = "3181bf0_definition_then_3181370_recipient";
  range.admitted = true;
  const auto manager = Read<const void *>(b, b.helper_manager_slot);
  if (!manager) range.reason = "helper_manager_slot_unavailable";
  else {
    out.manager_present = *manager != nullptr;
    if (!*manager) range.reason = "helper_native_manager_not_initialized";
    else {
      const void *definition = HelperManagerDefinition(b, *manager, character,
          out, identities, range.reason);
      if (definition) {
        const auto carrier = Read<const void *>(b, character, 0x1C8);
        if (!carrier) range.reason = "helper_recipient_carrier_unavailable";
        else if (!*carrier) {
          if (absent_recipient_q64) {
            out.recipient_source = std::string(absent_recipient_source);
            out.recipient_q64 = absent_recipient_q64;
          } else {
            out.recipient_source = "absent_1c8_2bfac30_unobserved";
            range.reason = "helper_absent_1c8_recipient_contribution_inputs_unobserved";
          }
        } else {
          out.recipient_source = "character_1c8_a0";
          out.recipient_q64 = Read<std::int64_t>(b, *carrier, 0xA0);
          if (!out.recipient_q64) range.reason = "helper_recipient_a0_unavailable";
        }
        if (out.recipient_q64) {
          const void *pc = HelperRangePc(b, definition, out, range.reason);
          if (pc) {
            game::ContextSourceHelperRowV1 row{};
            row.source_identity = Identity(identities, pc, "h");
            row.gate_raw = Read<std::int32_t>(b, pc, 0xC);
            range.count = row.gate_raw;
            if (!row.gate_raw) row.reason = "helper_manager_pc_count_unavailable";
            else {
              row.admitted = *row.gate_raw != 0;
              if (*row.admitted) {
                row.property_block = Properties(b, pc);
                if (!PropertiesReady(*row.property_block))
                  row.reason = "helper_manager_pc_properties_unavailable";
              }
            }
            if (!row.reason.empty()) Reason(range.reason, row.reason.c_str());
            if (!range.reason.empty()) Reason(row.reason, range.reason.c_str());
            range.rows.emplace();
            range.rows->push_back(std::move(row));
          }
        }
      }
    }
  }
  HelperFinishFamily(range);

  const auto pointer_carrier = Read<const void *>(b, character, 0x1C8);
  if (!pointer_carrier) {
    out.source_a18.selected_source = "28bd090_header_unavailable";
    out.source_a18.reason = "helper_source_1c8_carrier_unavailable";
    HelperFinishFamily(out.source_a18);
  } else {
    const void *header = *pointer_carrier ? Offset(*pointer_carrier, 0x88)
                                         : b.helper_source_pointer_fallback_header;
    out.source_a18 = HelperPointerFamily(b, header,
        *pointer_carrier ? "character_1c8_inline_88" : "inline_static_5d67e40",
        0xA18, 0xA24, identities);
    if (!*pointer_carrier) {
      out.pointer_list_guard_raw = Read<std::int32_t>(b, b.helper_source_pointer_fallback_guard_slot);
      if (!out.pointer_list_guard_raw) out.source_a18.reason = "helper_pointer_list_guard_unavailable";
      else if (*out.pointer_list_guard_raw == 0 || *out.pointer_list_guard_raw == -1)
        out.source_a18.reason = "helper_pointer_list_not_initialized";
      HelperFinishFamily(out.source_a18);
    }
  }

  auto &conditional = out.conditional_direct;
  conditional.selected_source = "selected_first_inline_938";
  out.predicate_character_15c_raw = Read<std::int32_t>(b, character, 0x15C);
  if (!out.predicate_character_15c_raw) conditional.reason = "helper_predicate_character_15c_unavailable";
  else if (*out.predicate_character_15c_raw == -1) out.predicate_admitted = false;
  else {
    std::optional<std::string> predicate_first_selection, predicate_second_selection;
    const void *predicate_first = HelperRegistry8(b, b.selector_a_storage_slot,
        b.selector_a_initial_fallback_slot, Offset(character, 0xB4),
        out.predicate_first_key_b4_raw, predicate_first_selection, conditional.reason);
    if (predicate_first) {
      const void *second = HelperRegistry8(b, b.selector_a_second_storage_slot,
          b.selector_a_second_fallback_slot, Offset(predicate_first, 0x4B8),
          out.predicate_second_key_4b8_raw, predicate_second_selection, conditional.reason);
      if (second) {
        out.predicate_second_a0_raw = Read<std::int32_t>(b, second, 0xA0);
        if (!out.predicate_second_a0_raw) conditional.reason = "helper_predicate_second_a0_unavailable";
        else out.predicate_admitted = *out.predicate_character_15c_raw == *out.predicate_second_a0_raw;
      }
    }
  }
  if (out.predicate_admitted == false) {
    conditional.admitted = false;
    conditional.rows.emplace();
    HelperFinishFamily(conditional);
  } else if (out.predicate_admitted == true) {
    conditional = HelperPointerFamily(b, Offset(first, 0x938),
        "selected_first_inline_938", 0, std::nullopt, identities);
    if (!first) {
      Reason(conditional.reason, first_reason.c_str());
      HelperFinishFamily(conditional);
    }
  } else HelperFinishFamily(conditional);

  out.ready = out.primary_direct.ready && out.manager_range.ready &&
              out.source_a18.ready && out.conditional_direct.ready;
  out.status = out.ready ? "available" : "partial";
  if (!out.ready) out.reason = "helper_291f0a0_current_families_partial";
  return out;
}
