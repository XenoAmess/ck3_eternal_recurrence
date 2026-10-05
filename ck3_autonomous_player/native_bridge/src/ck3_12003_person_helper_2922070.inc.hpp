// Source-first packet: person-tail/helper-2922070/SOURCE-ONLY-RECEIPT.json.
const void *Helper2922070Lookup(const ContextSourceBindingsV1 &b,
    const void *storage_slot, const void *fallback_slot, const void *key_address,
    std::size_t id_offset, bool key_always, std::optional<std::int32_t> &key,
    std::optional<std::string> &selection, std::string &reason,
    const std::optional<std::int32_t> *known_key = nullptr) {
  const auto store = Read<const void *>(b, storage_slot);
  if (!store) { reason = "helper_2922070_registry_slot_unavailable"; return nullptr; }
  if (known_key) key = *known_key;
  else if (key_always || *store) key = Read<std::int32_t>(b, key_address);
  if ((known_key || key_always || *store) && !key) {
    reason = "helper_2922070_registry_key_unavailable";
    return nullptr;
  }
  if (*store) {
    const auto capacity = Read<std::uint32_t>(b, *store, 0x2C);
    if (!capacity) { reason = "helper_2922070_registry_capacity_unavailable"; return nullptr; }
    const auto index = static_cast<std::uint32_t>(*key) & 0xFFFFFFU;
    if (index < *capacity) {
      const auto table = Read<const void *>(b, *store, 0x20);
      const auto object = table ? Read<const void *>(b, *table, index * 16ULL + 8) : std::nullopt;
      if (!object) { reason = "helper_2922070_registry_entry_unavailable"; return nullptr; }
      if (*object) {
        const auto full_id = Read<std::int32_t>(b, *object, id_offset);
        if (!full_id) { reason = "helper_2922070_registry_full_id_unavailable"; return nullptr; }
        if (*full_id == *key) {
          selection = id_offset == 8 ? "registry_full_id_8"
              : id_offset == 0x10 ? "registry_full_id_10" : "registry_full_id_18";
          return *object;
        }
      }
    }
  }
  selection = "native_fallback";
  const auto fallback = Read<const void *>(b, fallback_slot);
  if (!fallback) { reason = "helper_2922070_registry_fallback_unavailable"; return nullptr; }
  return *fallback;
}

const void *Helper2922070TopCharacter(const ContextSourceBindingsV1 &b,
    const void *current, std::string &reason) {
  const auto fallback = Read<const void *>(b, b.remaining_character_fallback_slot);
  if (!fallback) { reason = "helper_2922070_top_fallback_unavailable"; return nullptr; }
  if (current == *fallback) return current;
  const auto store = Read<const void *>(b, b.remaining_character_storage_slot);
  if (!store) { reason = "helper_2922070_top_store_unavailable"; return nullptr; }
  for (;;) {
    const auto land = Read<const void *>(b, current, 0x1C0);
    if (!land) { reason = "helper_2922070_top_land_unavailable"; return nullptr; }
    const void *next = nullptr;
    if (*land) {
      const auto subject = Read<const void *>(b, *land, 0x1C0);
      const auto candidate = subject ? Read<const void *>(b, *subject, 0x28) : std::nullopt;
      if (!candidate) { reason = "helper_2922070_top_candidate_unavailable"; return nullptr; }
      const auto magic = Read<std::uint32_t>(b, *candidate, 0x1C);
      if (!magic) { reason = "helper_2922070_top_magic_unavailable"; return nullptr; }
      if (*magic != 0x43686172U) return current;
      const auto id = Read<std::int32_t>(b, *candidate, 0x18);
      if (!id) { reason = "helper_2922070_top_id_unavailable"; return nullptr; }
      if (*id == -1) return current;
      next = *candidate;
    } else {
      const auto army = Read<const void *>(b, current, 0x1B8);
      if (!army) { reason = "helper_2922070_top_army_unavailable"; return nullptr; }
      if (!*army) return current;
      std::optional<std::int32_t> key;
      std::optional<std::string> selection;
      next = RemainingLookup(b, *store, *fallback, Offset(*army, 0xC8),
                             0x18, key, selection, reason);
      if (!reason.empty()) return nullptr;
    }
    if (next == current) return current;
    current = next;
  }
}

bool Helper2922070Walk(const ContextSourceBindingsV1 &b, const void *character,
    game::ContextSourceHelper2922070V1 &out, std::vector<std::int32_t> &collected,
    std::vector<const void *> &identities) {
  const auto ordinal = out.walk_nodes->size();
  game::ContextSource2922070WalkV1 node{};
  node.native_index = static_cast<std::int32_t>(ordinal);
  node.character_identity = Identity(identities, character, "helper_2922070");
  out.walk_nodes->push_back(std::move(node));
  const auto fail = [&](const char *why) {
    out.walk_nodes->at(ordinal).reason = why;
    Reason(out.reason, why);
    return false;
  };
  const auto land = Read<const void *>(b, character, 0x1C0);
  if (!land) return fail("helper_2922070_walk_land_unavailable");
  const void *header = *land ? Offset(*land, 0x218)
      : b.helper_2922070_descendant_fallback_header;
  auto &raw = out.walk_nodes->at(ordinal);
  raw.header_selection = *land ? "land_218" : "native_inline_54596d8";
  const auto data = Read<const void *>(b, header);
  raw.count_c_raw = Read<std::int32_t>(b, header, 0xC);
  if (data) raw.array_present = *data != nullptr;
  if (!data || !raw.count_c_raw) return fail("helper_2922070_walk_header_unavailable");
  const auto count = *raw.count_c_raw;
  if (count < 0) return fail("helper_2922070_walk_negative_count");
  for (std::int32_t i = 0; i < count; ++i) {
    game::ContextSource2922070EdgeV1 edge{};
    edge.native_index = i;
    const void *object = Helper2922070Lookup(b,
        b.helper_2922070_descendant_storage_slot,
        b.helper_2922070_descendant_fallback_slot,
        Offset(*data, static_cast<std::size_t>(i) * 4), 8, false,
        edge.requested_id_raw, edge.selection, edge.reason);
    if (edge.reason.empty()) {
      edge.object_identity = Identity(identities, object, "helper_2922070");
      const auto holder = Read<const void *>(b, object, 0x20);
      if (!holder) edge.reason = "helper_2922070_walk_holder_unavailable";
      else {
        edge.holder_identity = Identity(identities, *holder, "helper_2922070");
        edge.holder_id_18_raw = Read<std::int32_t>(b, *holder, 0x18);
        if (!edge.holder_id_18_raw) edge.reason = "helper_2922070_walk_holder_id_unavailable";
        else {
          collected.push_back(*edge.holder_id_18_raw);
          // Commit the parent edge before recursion; vector growth may relocate nodes.
          out.walk_nodes->at(ordinal).edges.push_back(edge);
          if (!Helper2922070Walk(b, *holder, out, collected, identities)) return false;
          continue;
        }
      }
    }
    Reason(out.reason, edge.reason.c_str());
    out.walk_nodes->at(ordinal).edges.push_back(std::move(edge));
    return false;
  }
  return true;
}

bool Helper2922070Filter(const ContextSourceBindingsV1 &b, const void *character,
    game::ContextSource2922070CharacterV1 &row, std::vector<const void *> &identities) {
  const auto fail = [&](const char *why) { row.reason = why; return false; };
  row.first_key_158_raw = Read<std::int32_t>(b, character, 0x158);
  if (!row.first_key_158_raw) return fail("helper_2922070_filter_first_key_unavailable");
  if (*row.first_key_158_raw == -1) { row.admitted = false; return true; }
  const auto *first = Helper2922070Lookup(b, b.first_storage_slot, b.first_fallback_slot,
      Offset(character, 0x158), 0x10, true, row.first_key_158_raw,
      row.first_selection, row.reason);
  if (!row.reason.empty()) return false;
  row.first_identity = Identity(identities, first, "helper_2922070");
  row.character_id_18_raw = Read<std::int32_t>(b, character, 0x18);
  row.owner_id_160_raw = Read<std::int32_t>(b, first, 0x160);
  if (!row.character_id_18_raw || !row.owner_id_160_raw)
    return fail("helper_2922070_filter_owner_comparison_unavailable");
  if (*row.character_id_18_raw != *row.owner_id_160_raw) {
    row.admitted = false;
    return true;
  }
  std::optional<std::int32_t> owner_key;
  const auto *owner = Helper2922070Lookup(b, b.remaining_character_storage_slot,
      b.remaining_character_fallback_slot, Offset(first, 0x160), 0x18, false,
      owner_key, row.owner_selection, row.reason);
  if (!row.reason.empty()) return false;
  row.owner_identity = Identity(identities, owner, "helper_2922070");
  const auto *government = RemainingGovernment(b, owner, row.government_selection, row.reason);
  if (!row.reason.empty()) return false;
  row.government_identity = Identity(identities, government, "helper_2922070");
  const auto *top = Helper2922070TopCharacter(b, owner, row.reason);
  if (!row.reason.empty()) return false;
  row.top_character_identity = Identity(identities, top, "helper_2922070");
  const auto *top_government = RemainingGovernment(b, top,
      row.top_government_selection, row.reason);
  if (!row.reason.empty()) return false;
  row.top_government_identity = Identity(identities, top_government, "helper_2922070");
  row.government_mask_40_raw = Read<std::uint64_t>(b, government, 0x40);
  if (!row.government_mask_40_raw) return fail("helper_2922070_filter_government_mask_unavailable");
  constexpr std::uint64_t mask = 0x1000000400ULL;
  if ((*row.government_mask_40_raw & mask) != mask) {
    row.admitted = false;
    return true;
  }
  row.top_government_mask_40_raw = Read<std::uint64_t>(b, top_government, 0x40);
  if (!row.top_government_mask_40_raw) return fail("helper_2922070_filter_top_mask_unavailable");
  row.admitted = (*row.top_government_mask_40_raw & mask) == mask;
  return true;
}

bool Helper2922070Membership(const ContextSourceBindingsV1 &b, const void *character,
    game::ContextSource2922070MembershipV1 &row, std::vector<std::int32_t> &output_ids,
    std::vector<const void *> &identities) {
  const auto fail = [&](const char *why) { row.reason = why; return false; };
  const auto *first = Helper2922070Lookup(b, b.first_storage_slot, b.first_fallback_slot,
      Offset(character, 0x158), 0x10, true, row.first_key_158_raw,
      row.first_selection, row.reason);
  if (!row.reason.empty()) return false;
  row.first_identity = Identity(identities, first, "helper_2922070");
  const auto land = Read<const void *>(b, character, 0x1C0);
  if (!land) return fail("helper_2922070_membership_land_unavailable");
  row.header_selection = *land ? "land_1e0" : "native_inline_5459c88";
  const void *header = *land ? Offset(*land, 0x1E0)
      : b.helper_2922070_membership_fallback_header;
  const auto data = Read<const void *>(b, header);
  row.count_c_raw = Read<std::int32_t>(b, header, 0xC);
  if (data) row.array_present = *data != nullptr;
  if (!data || !row.count_c_raw) return fail("helper_2922070_membership_header_unavailable");
  if (*row.count_c_raw < 0) return fail("helper_2922070_membership_negative_count");
  row.admitted = false;
  for (std::int32_t i = 0; i < *row.count_c_raw; ++i) {
    game::ContextSource2922070KeyV1 key{};
    key.native_index = i;
    const auto *object = Helper2922070Lookup(b,
        b.helper_2922070_membership_storage_slot,
        b.helper_2922070_membership_fallback_slot,
        Offset(*data, static_cast<std::size_t>(i) * 4), 0x10, true,
        key.requested_id_raw, key.selection, key.reason);
    if (key.reason.empty()) {
      key.object_identity = Identity(identities, object, "helper_2922070");
      key.gate_32_raw = Read<std::uint8_t>(b, object, 0x32);
      if (!key.gate_32_raw) key.reason = "helper_2922070_membership_gate_unavailable";
    }
    const bool failed = !key.reason.empty();
    const bool admitted = key.gate_32_raw && *key.gate_32_raw != 0;
    if (failed) row.reason = key.reason;
    row.scans.push_back(std::move(key));
    if (failed) { row.admitted.reset(); return false; }
    if (admitted) { row.admitted = true; break; }
  }
  if (row.admitted == true) {
    row.first_id_10_raw = Read<std::int32_t>(b, first, 0x10);
    if (!row.first_id_10_raw) return fail("helper_2922070_membership_first_id_unavailable");
    row.appended = std::find(output_ids.begin(), output_ids.end(), *row.first_id_10_raw)
        == output_ids.end();
    if (*row.appended) output_ids.push_back(*row.first_id_10_raw);
  }
  return true;
}

void Helper2922070PropertyRow(const ContextSourceBindingsV1 &b, const void *source,
    game::ContextSource2922070RowV1 &row, std::vector<const void *> &identities) {
  row.type_280_raw = Read<std::uint8_t>(b, source, 0x280);
  if (!row.type_280_raw) { row.reason = "helper_2922070_type_unavailable"; return; }
  if (*row.type_280_raw != 2) { row.admitted = false; return; }
  const auto definition = Read<const void *>(b, source, 0x220);
  if (!definition) { row.reason = "helper_2922070_definition_unavailable"; return; }
  row.definition_identity = Identity(identities, *definition, "helper_2922070");
  row.definition_magic_38_raw = Read<std::uint32_t>(b, *definition, 0x38);
  if (!row.definition_magic_38_raw) { row.reason = "helper_2922070_definition_magic_unavailable"; return; }
  row.admitted = *row.definition_magic_38_raw == 0x4744624FU;
  if (row.admitted == false) return;
  row.requested_index_228_raw = Read<std::int32_t>(b, source, 0x228);
  row.count_214_raw = Read<std::int32_t>(b, *definition, 0x214);
  if (!row.requested_index_228_raw || !row.count_214_raw) {
    row.reason = "helper_2922070_index_operands_unavailable";
    return;
  }
  const auto last = static_cast<std::int32_t>(
      static_cast<std::uint32_t>(*row.count_214_raw) - 1U);
  row.selected_index_raw = *row.requested_index_228_raw < 0
      ? 0 : std::min(*row.requested_index_228_raw, last);
  const auto table = Read<const void *>(b, *definition, 0x208);
  if (!table) { row.reason = "helper_2922070_table_unavailable"; return; }
  row.table_identity = Identity(identities, *table, "helper_2922070");
  const auto delta = static_cast<std::int64_t>(*row.selected_index_raw) * 0x12D0;
  const auto *pc = reinterpret_cast<const void *>(reinterpret_cast<std::uintptr_t>(*table)
      + static_cast<std::uintptr_t>(delta) + 0xBA0);
  row.property_identity = Identity(identities, pc, "helper_2922070");
  row.property_block = Properties(b, pc);
  if (!PropertiesReady(*row.property_block)) row.reason = "helper_2922070_properties_unavailable";
}

game::ContextSourceHelper2922070V1 Helper2922070(const ContextSourceBindingsV1 &b,
    const void *character, std::int32_t character_id) {
  game::ContextSourceHelper2922070V1 out{};
  out.character_id = character_id;
  out.status = "partial";
  std::vector<const void *> identities;
  const auto finish = [&]() {
    out.ready = out.gate_ready && (out.admitted == false
        || (out.admitted == true && out.collection_ready && out.rows_ready))
        && out.reason.empty();
    out.status = out.ready ? "available" : "partial";
    return out;
  };
  const auto *government = RemainingGovernment(b, character,
      out.government_selection, out.reason);
  if (!out.reason.empty()) return finish();
  out.government_identity = Identity(identities, government, "helper_2922070");
  out.government_mode_4d6_raw = Read<std::uint8_t>(b, government, 0x4D6);
  if (!out.government_mode_4d6_raw) {
    out.reason = "helper_2922070_government_gate_unavailable";
    return finish();
  }
  if (*out.government_mode_4d6_raw != 5) {
    out.admitted = false; out.gate_ready = true; return finish();
  }
  const auto land = Read<const void *>(b, character, 0x1C0);
  if (!land) { out.reason = "helper_2922070_gate_land_unavailable"; return finish(); }
  out.character_land_present = *land != nullptr;
  if (!*land) { out.admitted = false; out.gate_ready = true; return finish(); }
  const auto subject = Read<const void *>(b, *land, 0x1C0);
  if (!subject) { out.reason = "helper_2922070_gate_subject_unavailable"; return finish(); }
  out.subject_identity = Identity(identities, *subject, "helper_2922070");
  out.subject_magic_c_raw = Read<std::uint32_t>(b, *subject, 0xC);
  if (!out.subject_magic_c_raw) { out.reason = "helper_2922070_subject_magic_unavailable"; return finish(); }
  if (*out.subject_magic_c_raw == 0x5362436FU) {
    out.subject_id_8_raw = Read<std::int32_t>(b, *subject, 8);
    if (!out.subject_id_8_raw) { out.reason = "helper_2922070_subject_id_unavailable"; return finish(); }
    if (*out.subject_id_8_raw != -1) {
      out.admitted = false; out.gate_ready = true; return finish();
    }
  }
  out.admitted = true;
  out.gate_ready = true;
  out.walk_nodes.emplace();
  std::vector<std::int32_t> collected;
  if (!Helper2922070Walk(b, character, out, collected, identities)) return finish();
  out.characters.emplace();
  std::vector<const void *> characters;
  for (const auto id : collected) {
    game::ContextSource2922070CharacterV1 row{};
    row.native_index = static_cast<std::int32_t>(out.characters->size());
    const std::optional<std::int32_t> known{id};
    const auto *selected = Helper2922070Lookup(b, b.remaining_character_storage_slot,
        b.remaining_character_fallback_slot, nullptr, 0x18, true,
        row.input_id_raw, row.selection, row.reason, &known);
    row.character_identity = Identity(identities, selected, "helper_2922070");
    characters.push_back(selected);
    if (row.reason.empty()) Helper2922070Filter(b, selected, row, identities);
    if (!row.reason.empty()) Reason(out.reason, row.reason.c_str());
    out.characters->push_back(std::move(row));
    if (!out.reason.empty()) return finish();
  }
  game::ContextSource2922070CharacterV1 self{};
  self.native_index = static_cast<std::int32_t>(out.characters->size());
  self.include_self = true;
  self.character_identity = Identity(identities, character, "helper_2922070");
  self.admitted = true;
  characters.push_back(character);
  out.characters->push_back(std::move(self));
  out.character_order.emplace();
  for (std::size_t i = 0; i < out.characters->size(); ++i)
    if (out.characters->at(i).admitted == true)
      out.character_order->push_back(static_cast<std::int32_t>(i));
  if (out.character_order->size() > 1) {
    for (const auto index : *out.character_order) {
      auto &row = out.characters->at(index);
      row.character_id_18_raw = Read<std::int32_t>(b, characters.at(index), 0x18);
      if (!row.character_id_18_raw) {
        row.reason = "helper_2922070_character_sort_id_unavailable";
        Reason(out.reason, row.reason.c_str());
      }
    }
    if (!out.reason.empty()) return finish();
    std::stable_sort(out.character_order->begin(), out.character_order->end(),
        [&](std::int32_t a, std::int32_t c) {
          return static_cast<std::uint32_t>(*out.characters->at(a).character_id_18_raw)
              < static_cast<std::uint32_t>(*out.characters->at(c).character_id_18_raw);
        });
    out.character_order->erase(std::unique(out.character_order->begin(),
        out.character_order->end(), [&](std::int32_t a, std::int32_t c) {
          return characters.at(a) == characters.at(c);
        }), out.character_order->end());
  }
  out.membership_rows.emplace();
  out.output_ids.emplace();
  for (const auto index : *out.character_order) {
    game::ContextSource2922070MembershipV1 row{};
    row.native_index = static_cast<std::int32_t>(out.membership_rows->size());
    row.character_index = index;
    Helper2922070Membership(b, characters.at(index), row, *out.output_ids, identities);
    if (!row.reason.empty()) Reason(out.reason, row.reason.c_str());
    out.membership_rows->push_back(std::move(row));
    if (!out.reason.empty()) return finish();
  }
  out.rows.emplace();
  std::vector<const void *> sources;
  for (const auto id : *out.output_ids) {
    game::ContextSource2922070RowV1 row{};
    row.input_index = static_cast<std::int32_t>(out.rows->size());
    row.native_index = row.input_index;
    row.requested_id_raw = id;
    const std::optional<std::int32_t> known{id};
    std::optional<std::int32_t> key;
    const auto *source = Helper2922070Lookup(b, b.first_storage_slot, b.first_fallback_slot,
        nullptr, 0x10, true, key, row.selection, row.reason, &known);
    row.source_identity = Identity(identities, source, "helper_2922070");
    sources.push_back(source);
    if (!row.reason.empty()) Reason(out.reason, row.reason.c_str());
    out.rows->push_back(std::move(row));
    if (!out.reason.empty()) return finish();
  }
  if (out.rows->size() > 1) {
    for (std::size_t i = 0; i < out.rows->size(); ++i) {
      auto &row = out.rows->at(i);
      row.selected_id_10_raw = Read<std::int32_t>(b, sources.at(i), 0x10);
      if (!row.selected_id_10_raw) {
        row.reason = "helper_2922070_source_sort_id_unavailable";
        Reason(out.reason, row.reason.c_str());
      }
    }
    if (!out.reason.empty()) return finish();
    std::stable_sort(out.rows->begin(), out.rows->end(), [](const auto &a, const auto &c) {
      return static_cast<std::uint32_t>(*a.selected_id_10_raw)
          < static_cast<std::uint32_t>(*c.selected_id_10_raw);
    });
  }
  out.collection_ready = true;
  for (std::size_t i = 0; i < out.rows->size(); ++i) {
    auto &row = out.rows->at(i);
    row.native_index = static_cast<std::int32_t>(i);
    Helper2922070PropertyRow(b, sources.at(row.input_index), row, identities);
    if (!row.reason.empty()) Reason(out.reason, row.reason.c_str());
  }
  out.rows_ready = out.reason.empty();
  return finish();
}
