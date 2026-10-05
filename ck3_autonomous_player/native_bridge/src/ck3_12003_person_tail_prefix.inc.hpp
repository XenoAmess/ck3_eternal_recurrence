// Exact-build source tree is frozen in the Round4 tail-prefix-helper packet.
const void *TailPrefixRelationNext(const ContextSourceBindingsV1 &b,
    const void *current, const void *fallback, bool initial,
    std::optional<std::string> &selection,
    std::optional<std::int32_t> &key, std::string &reason) {
  const auto land = Read<const void *>(b, current, 0x1C0);
  const auto army = Read<const void *>(b, current, 0x1B8);
  if (!land || !army) { reason = "tail_prefix_relation_links_unavailable"; return nullptr; }
  if (*land) {
    const auto object = Read<const void *>(b, *land, 0x1C0);
    const auto candidate = object ? Read<const void *>(b, *object, 0x28) : std::nullopt;
    if (!candidate) { reason = "tail_prefix_relation_landed_candidate_unavailable"; return nullptr; }
    const auto magic = Read<std::uint32_t>(b, *candidate, 0x1C);
    if (!magic) { reason = "tail_prefix_relation_landed_magic_unavailable"; return nullptr; }
    bool valid = false;
    if (*magic == 0x43686172U) {
      const auto id = Read<std::int32_t>(b, *candidate, 0x18);
      if (!id) { reason = "tail_prefix_relation_landed_id_unavailable"; return nullptr; }
      valid = *id != -1;
    }
    selection = valid ? "land_1c0_1c0_28"
                      : initial ? "land_invalid_returns_current" : "land_invalid_stops";
    return valid ? *candidate : initial ? current : nullptr;
  }
  if (*army) {
    const auto store = Read<const void *>(b, b.remaining_character_storage_slot);
    if (!store) { reason = "tail_prefix_relation_character_store_unavailable"; return nullptr; }
    return RemainingLookup(b, *store, fallback, Offset(*army, 0xC8), 0x18,
                           key, selection, reason);
  }
  selection = "native_fallback";
  return fallback;
}

game::ContextSourceTailPrefix275V1 TailPrefix275(
    const ContextSourceBindingsV1 &b, const void *character,
    std::vector<const void *> &identities) {
  game::ContextSourceTailPrefix275V1 out{};
  out.status = "partial";
  const auto finish = [&]() {
    out.ready = out.reason.empty();
    out.status = out.ready ? "available" : "partial";
    return out;
  };
  // This caller loads the Character key before testing the storage slot.
  out.first_key_158_raw = Read<std::int32_t>(b, character, 0x158);
  if (!out.first_key_158_raw) { out.reason = "tail_prefix_caller_key_unavailable"; return finish(); }
  const auto *first = PreRegistry(b, b.first_storage_slot, b.first_fallback_slot,
      Offset(character, 0x158), out.first_key_158_raw, out.first_selection, out.reason);
  if (!first) return finish();
  out.first_identity = Identity(identities, first, "tail_prefix");
  out.caller_gate_218_raw = Read<std::uint8_t>(b, first, 0x218);
  if (!out.caller_gate_218_raw) { out.reason = "tail_prefix_caller_gate_unavailable"; return finish(); }
  out.caller_admitted = *out.caller_gate_218_raw != 0;
  if (out.caller_admitted == false) return finish();
  out.caller_gate_218_recheck_raw = Read<std::uint8_t>(b, first, 0x218);
  if (!out.caller_gate_218_recheck_raw || *out.caller_gate_218_recheck_raw == 0) {
    out.reason = "tail_prefix_caller_recheck_not_admitted";
    return finish();
  }
  const auto definition = Read<const void *>(b, first, 0x1D8);
  if (!definition) { out.reason = "tail_prefix_original_definition_unavailable"; return finish(); }
  out.definition_identity = Identity(identities, *definition, "tail_prefix");
  const auto definition_pointer = Read<const void *>(b, *definition, 0x260);
  if (!definition_pointer) { out.reason = "tail_prefix_definition_pointer_unavailable"; return finish(); }
  out.definition_pointer_260_identity = Identity(identities, *definition_pointer, "tail_prefix");
  const auto land = Read<const void *>(b, character, 0x1C0);
  if (!land) { out.reason = "tail_prefix_predicate_land_unavailable"; return finish(); }
  out.character_land_present = *land != nullptr;
  if (!*land) { out.predicate_admitted = false; return finish(); }
  out.land_field_1f8_raw = Read<std::int32_t>(b, *land, 0x1F8);
  if (!out.land_field_1f8_raw) { out.reason = "tail_prefix_predicate_land_field_unavailable"; return finish(); }
  if (*out.land_field_1f8_raw == -1) { out.predicate_admitted = false; return finish(); }
  const auto *government = RemainingGovernment(b, character, out.government_selection,
                                               out.reason);
  if (!government) return finish();
  out.government_identity = Identity(identities, government, "tail_prefix");
  out.government_mode_80c_raw = Read<std::uint8_t>(b, government, 0x80C);
  if (!out.government_mode_80c_raw) { out.reason = "tail_prefix_government_mode_unavailable"; return finish(); }
  out.predicate_pointer_selection = *out.government_mode_80c_raw == 2
      ? "government_800" : "native_default_5d26d50";
  const auto pointer = *out.government_mode_80c_raw == 2
      ? Read<const void *>(b, government, 0x800)
      : Read<const void *>(b, b.tail_prefix_default_relation_slot);
  if (!pointer) { out.reason = "tail_prefix_predicate_pointer_unavailable"; return finish(); }
  out.predicate_pointer_identity = Identity(identities, *pointer, "tail_prefix");
  out.predicate_admitted = *pointer == *definition_pointer;
  if (out.predicate_admitted == false) return finish();
  const auto *owner = PreRegistry(b, b.first_storage_slot, b.first_fallback_slot,
      Offset(first, 0x1E0), out.owner_key_1e0_raw, out.owner_selection, out.reason);
  if (!owner) return finish();
  out.owner_identity = Identity(identities, owner, "tail_prefix");
  out.owner_id_160_raw = Read<std::int32_t>(b, owner, 0x160);
  out.character_id_18_raw = Read<std::int32_t>(b, character, 0x18);
  if (!out.owner_id_160_raw || !out.character_id_18_raw) {
    out.reason = "tail_prefix_owner_comparison_unavailable";
    return finish();
  }
  out.owner_admitted = *out.owner_id_160_raw == *out.character_id_18_raw;
  if (out.owner_admitted == false) {
    out.owner_admitted.reset();
    const auto fallback = Read<const void *>(b, b.remaining_character_fallback_slot);
    if (!fallback) { out.reason = "tail_prefix_relation_fallback_unavailable"; return finish(); }
    const void *last = *fallback;
    const void *current = TailPrefixRelationNext(b, character, *fallback, true,
        out.initial_relation_selection, out.initial_relation_key_c8_raw, out.reason);
    if (!out.reason.empty()) return finish();
    out.initial_relation_identity = Identity(identities, current, "tail_prefix");
    out.relation_rows.emplace();
    if (current != *fallback) {
      // Native reads this captured storage once before the repeated walker.
      const auto store = Read<const void *>(b, b.remaining_character_storage_slot);
      if (!store) { out.reason = "tail_prefix_relation_store_unavailable"; return finish(); }
      while (current) {
        game::ContextSourceTailPrefixRelationV1 row{};
        row.native_index = static_cast<std::int32_t>(out.relation_rows->size());
        row.character_identity = Identity(identities, current, "tail_prefix");
        row.magic_1c_raw = Read<std::uint32_t>(b, current, 0x1C);
        if (!row.magic_1c_raw) row.reason = "tail_prefix_relation_magic_unavailable";
        else if (*row.magic_1c_raw != 0x43686172U) row.accepted = false;
        else {
          row.character_id_18_raw = Read<std::int32_t>(b, current, 0x18);
          if (!row.character_id_18_raw) row.reason = "tail_prefix_relation_id_unavailable";
          else row.accepted = *row.character_id_18_raw != -1;
        }
        bool stop = row.accepted != true;
        const void *next = nullptr;
        if (row.accepted == true) {
          last = current;
          if (*out.owner_id_160_raw == *row.character_id_18_raw) {
            out.owner_admitted = true;
            stop = true;
          } else {
            // Reproduce the direct repeated walker with its captured store.
            const auto army = Read<const void *>(b, current, 0x1B8);
            const auto link = Read<const void *>(b, current, 0x1C0);
            if (!army || !link) row.reason = "tail_prefix_relation_links_unavailable";
            else if (*link) {
              const auto object = Read<const void *>(b, *link, 0x1C0);
              const auto candidate = object ? Read<const void *>(b, *object, 0x28) : std::nullopt;
              if (!candidate) row.reason = "tail_prefix_relation_next_candidate_unavailable";
              else {
                const auto magic = Read<std::uint32_t>(b, *candidate, 0x1C);
                if (!magic) row.reason = "tail_prefix_relation_next_magic_unavailable";
                else if (*magic != 0x43686172U) stop = true;
                else {
                  const auto id = Read<std::int32_t>(b, *candidate, 0x18);
                  if (!id) row.reason = "tail_prefix_relation_next_id_unavailable";
                  else if (*id == -1) stop = true;
                  else next = *candidate;
                }
                row.next_selection = stop ? "land_invalid_stops" : "land_1c0_1c0_28";
              }
            } else if (*army && *store) {
              next = RemainingLookup(b, *store, *fallback, Offset(*army, 0xC8), 0x18,
                  row.next_key_c8_raw, row.next_selection, row.reason);
            } else {
              next = *fallback;
              row.next_selection = "native_fallback";
            }
            if (next) row.next_identity = Identity(identities, next, "tail_prefix");
            if (next == current) stop = true;
          }
        }
        if (!row.reason.empty()) Reason(out.reason, row.reason.c_str());
        out.relation_rows->push_back(std::move(row));
        if (!out.reason.empty()) return finish();
        if (stop) break;
        current = next;
      }
    }
    out.last_character_id_18_raw = out.owner_admitted == true
        ? out.owner_id_160_raw : Read<std::int32_t>(b, last, 0x18);
    if (!out.last_character_id_18_raw) { out.reason = "tail_prefix_final_owner_id_unavailable"; return finish(); }
    out.owner_admitted = *out.owner_id_160_raw == *out.last_character_id_18_raw;
  }
  if (out.owner_admitted == true) {
    const auto *pc = Offset(*definition, 0x40);
    out.property_identity = Identity(identities, pc, "tail_prefix");
    out.property_block = Properties(b, pc);
    if (!PropertiesReady(*out.property_block)) out.reason = "tail_prefix_275_properties_unavailable";
  }
  return finish();
}

game::ContextSourceTailPrefix2530V1 TailPrefix2530(
    const ContextSourceBindingsV1 &b, const void *character,
    std::vector<const void *> &identities) {
  game::ContextSourceTailPrefix2530V1 out{};
  out.status = "partial";
  const auto finish = [&]() {
    out.ready = out.reason.empty();
    out.status = out.ready ? "available" : "partial";
    return out;
  };
  const auto *first = PreRegistry(b, b.first_storage_slot, b.first_fallback_slot,
      Offset(character, 0x158), out.first_key_158_raw, out.first_selection, out.reason);
  if (!first) return finish();
  out.first_identity = Identity(identities, first, "tail_prefix");
  const auto definition = Read<const void *>(b, first, 0x220);
  if (!definition) { out.reason = "tail_prefix_2530_definition_unavailable"; return finish(); }
  out.definition_identity = Identity(identities, *definition, "tail_prefix");
  out.definition_magic_38_raw = Read<std::uint32_t>(b, *definition, 0x38);
  if (!out.definition_magic_38_raw) { out.reason = "tail_prefix_2530_definition_magic_unavailable"; return finish(); }
  out.admitted = *out.definition_magic_38_raw == 0x4744624FU;
  out.rows.emplace();
  if (out.admitted == false) return finish();
  out.type_280_raw = Read<std::uint8_t>(b, first, 0x280);
  if (!out.type_280_raw) Reason(out.reason, "tail_prefix_2530_type_unavailable");
  const auto append = [&](std::int32_t ordinal, std::optional<bool> admission,
                          const void *selected, std::size_t offset) {
    game::ContextSourceTailPrefix2530RowV1 row{};
    row.native_index = ordinal;
    row.admitted = admission;
    if (!admission) row.reason = "tail_prefix_2530_row_admission_unavailable";
    else if (*admission) {
      row.definition_identity = Identity(identities, selected, "tail_prefix");
      row.count_214_raw = Read<std::int32_t>(b, selected, 0x214);
      row.requested_index_228_raw = Read<std::int32_t>(b, first, 0x228);
      const auto table = Read<const void *>(b, selected, 0x208);
      if (table) row.table_identity = Identity(identities, *table, "tail_prefix");
      if (!row.count_214_raw || !row.requested_index_228_raw || !table)
        row.reason = "tail_prefix_2530_index_operands_unavailable";
      else {
        const auto last = static_cast<std::int32_t>(static_cast<std::uint32_t>(*row.count_214_raw) - 1U);
        row.selected_index_raw = *row.requested_index_228_raw < 0
            ? 0 : std::min(*row.requested_index_228_raw, last);
        const auto delta = static_cast<std::int64_t>(*row.selected_index_raw) * 0x12D0;
        const auto *pc = reinterpret_cast<const void *>(reinterpret_cast<std::uintptr_t>(*table)
            + static_cast<std::uintptr_t>(delta) + offset);
        row.property_identity = Identity(identities, pc, "tail_prefix");
        row.property_block = Properties(b, pc);
        if (!PropertiesReady(*row.property_block)) row.reason = "tail_prefix_2530_properties_unavailable";
      }
    }
    if (!row.reason.empty()) Reason(out.reason, row.reason.c_str());
    out.rows->push_back(std::move(row));
  };
  append(0, out.type_280_raw ? std::optional<bool>{*out.type_280_raw < 3} : std::nullopt,
         *definition, 0xD60);
  const auto second_definition = Read<const void *>(b, first, 0x220);
  append(1, true, second_definition.value_or(nullptr), 0xF20);
  out.character_id_18_raw = Read<std::int32_t>(b, character, 0x18);
  out.owner_id_160_raw = Read<std::int32_t>(b, first, 0x160);
  std::optional<bool> owner_admitted;
  if (out.character_id_18_raw && out.owner_id_160_raw)
    owner_admitted = *out.character_id_18_raw == *out.owner_id_160_raw;
  else Reason(out.reason, "tail_prefix_2530_owner_comparison_unavailable");
  const auto third_definition = owner_admitted == true
      ? Read<const void *>(b, first, 0x220) : std::optional<const void *>{nullptr};
  append(2, owner_admitted, third_definition.value_or(nullptr), 0x10E0);
  return finish();
}

game::ContextSourceTailPrefixV1 TailPrefix(const ContextSourceBindingsV1 &b,
    const void *character, std::int32_t character_id) {
  game::ContextSourceTailPrefixV1 out{};
  out.character_id = character_id;
  std::vector<const void *> identities;
  out.helper_2753860 = TailPrefix275(b, character, identities);
  out.helper_2922530 = TailPrefix2530(b, character, identities);
  out.ready = out.helper_2753860.ready && out.helper_2922530.ready;
  out.status = out.ready ? "available" : "partial";
  if (!out.ready) out.reason = "tail_prefix_current_helpers_partial";
  return out;
}
