// Same-query readonly later helpers. Source tree/plan were frozen before code.
using RemainingRow = game::ContextSourceRemainingRowV1;
using RemainingFamily = game::ContextSourceRemainingFamilyV1;

void RemainingFinish(RemainingFamily &out) {
  out.ready = out.reason.empty();
  out.status = out.ready ? "available" : "partial";
}
void RemainingSkip(RemainingFamily &out) {
  out.admitted = false;
  out.rows.emplace();
  RemainingFinish(out);
}
void RemainingProperty(const ContextSourceBindingsV1 &b, const void *pc,
                       const char *selection, RemainingRow &row,
                       std::vector<const void *> &ids) {
  row.property_selection = selection;
  row.property_identity = Identity(ids, pc, "remaining");
  row.property_block = Properties(b, pc);
  if (!PropertiesReady(*row.property_block))
    Reason(row.reason, "remaining_property_consumed_reads_unavailable");
}
const void *RemainingLookup(const ContextSourceBindingsV1 &b,
    const void *store, const void *fallback, const void *key_address,
    std::size_t id_offset, std::optional<std::int32_t> &key_raw,
    std::optional<std::string> &selection, std::string &reason,
    const std::optional<std::int32_t> *known_key = nullptr) {
  if (store) {
    key_raw = known_key ? *known_key : Read<std::int32_t>(b, key_address);
    if (!key_raw) { reason = "remaining_registry_key_unavailable"; return nullptr; }
    const auto index = static_cast<std::uint32_t>(*key_raw) & 0xFFFFFFU;
    const auto capacity = Read<std::uint32_t>(b, store, 0x2C);
    if (!capacity) { reason = "remaining_registry_capacity_unavailable"; return nullptr; }
    if (index < *capacity) {
      const auto table = Read<const void *>(b, store, 0x20);
      if (!table) { reason = "remaining_registry_table_unavailable"; return nullptr; }
      const auto object = Read<const void *>(b, *table, static_cast<std::size_t>(index) * 16 + 8);
      if (!object) { reason = "remaining_registry_slot_unavailable"; return nullptr; }
      if (*object) {
        const auto full = Read<std::int32_t>(b, *object, id_offset);
        if (!full) { reason = "remaining_registry_full_id_unavailable"; return nullptr; }
        if (*full == *key_raw) {
          selection = id_offset == 8 ? "registry_full_id_8" : "registry_full_id_18";
          return *object;
        }
      }
    }
  }
  selection = "native_fallback";
  if (!fallback) reason = "remaining_registry_native_fallback_null";
  return fallback;
}
struct RemainingRiteState {
  bool attempted = false;
  const void *selected = nullptr;
  std::optional<std::vector<const void *>> members;
};
bool RemainingRite(const ContextSourceBindingsV1 &b, const void *character,
    game::ContextSourceRemainingRiteV1 &out, RemainingRiteState &state,
    std::vector<const void *> &ids) {
  if (state.attempted) return state.members.has_value();
  state.attempted = true;
  // The initial fallback and first storage are kept for third-stage failure.
  const auto store = Read<const void *>(b, b.selector_a_storage_slot);
  const auto fallback = Read<const void *>(b, b.selector_a_initial_fallback_slot);
  if (!store || !fallback) { out.reason = "remaining_rite_initial_slots_unavailable"; return false; }
  const auto *first = RemainingLookup(b, *store, *fallback, Offset(character, 0xB4),
      8, out.first_key_b4_raw, out.first_selection, out.reason);
  if (!first) return false;
  const auto *second = HelperRegistry8(b, b.selector_a_second_storage_slot,
      b.selector_a_second_fallback_slot, Offset(first, 0x4B8),
      out.second_key_4b8_raw, out.second_selection, out.reason);
  if (!second) return false;
  state.selected = RemainingLookup(b, *store, *fallback, Offset(second, 0x98),
      8, out.third_key_98_raw, out.third_selection, out.reason);
  if (!state.selected) return false;
  out.selected_identity = Identity(ids, state.selected, "remaining");
  const auto data = Read<const void *>(b, state.selected, 0x7A0);
  if (data) out.membership_array_present = *data != nullptr;
  out.membership_count = Read<std::int32_t>(b, state.selected, 0x7AC);
  if (!data || !out.membership_count) { out.reason = "remaining_membership_header_unavailable"; return false; }
  if (*out.membership_count < 0) { out.reason = "remaining_membership_negative_count"; return false; }
  state.members = Vector<const void *>(b, *data, out.membership_count);
  if (!state.members) { out.reason = "remaining_membership_values_unavailable"; return false; }
  out.membership_identities.emplace();
  for (const auto *key : *state.members)
    out.membership_identities->push_back(Identity(ids, key, "remaining"));
  return true;
}
const void *RemainingGovernment(const ContextSourceBindingsV1 &b,
    const void *character, std::optional<std::string> &selection, std::string &reason) {
  const auto store = Read<const void *>(b, b.remaining_character_storage_slot);
  const auto fallback = Read<const void *>(b, b.remaining_character_fallback_slot);
  if (!store || !fallback) { reason = "remaining_government_character_slots_unavailable"; return nullptr; }
  const void *current = character;
  while (current) {
    const auto magic = Read<std::uint32_t>(b, current, 0x1C);
    if (!magic) { reason = "remaining_government_character_magic_unavailable"; return nullptr; }
    if (*magic != 0x43686172U) break;
    const auto full = Read<std::int32_t>(b, current, 0x18);
    if (!full) { reason = "remaining_government_character_id_unavailable"; return nullptr; }
    if (*full == -1) break;
    const auto death = Read<const void *>(b, current, 0x1D0);
    if (!death) { reason = "remaining_government_death_link_unavailable"; return nullptr; }
    std::optional<const void *> government;
    if (*death) {
      government = Read<const void *>(b, *death, 0x88);
      selection = "character_death_1d0_88";
    } else {
      const auto land = Read<const void *>(b, current, 0x1C0);
      if (!land) { reason = "remaining_government_land_link_unavailable"; return nullptr; }
      if (*land) {
        government = Read<const void *>(b, *land, 0x3F8);
        selection = "character_land_1c0_3f8";
      } else {
        const auto army = Read<const void *>(b, current, 0x1B8);
        if (!army) { reason = "remaining_government_army_link_unavailable"; return nullptr; }
        const auto key = *army ? Read<std::int32_t>(b, *army, 0xC8)
                              : std::optional<std::int32_t>{-1};
        if (!key) { reason = "remaining_government_relay_key_unavailable"; return nullptr; }
        std::optional<std::int32_t> requested;
        std::optional<std::string> resolution;
        // key is already consumed even when the captured store is native null.
        current = RemainingLookup(b, *store, *fallback, nullptr, 0x18,
                                  requested, resolution, reason, &key);
        if (!current) return nullptr;
        continue;
      }
    }
    if (!government) { reason = "remaining_government_pointer_unavailable"; return nullptr; }
    if (*government) return *government;
    break;
  }
  const auto government = Read<const void *>(b, b.remaining_government_fallback_slot);
  selection = "native_government_fallback";
  if (!government || !*government) {
    reason = "remaining_government_native_fallback_unavailable";
    return nullptr;
  }
  return *government;
}
void RemainingMap(const ContextSourceBindingsV1 &b, const void *key,
    const void *data, std::int32_t count, bool pointer_descriptors,
    const void *default_pc, const std::optional<std::int32_t> &guard,
    RemainingRow &row, std::vector<const void *> &ids) {
  row.key_magic_raw = Read<std::uint32_t>(b, key, 0x38);
  if (!row.key_magic_raw) { Reason(row.reason, "remaining_map_key_magic_unavailable"); return; }
  const void *pc = nullptr;
  bool use_default = *row.key_magic_raw != 0x4744624FU;
  if (!use_default) {
    row.key_full_id_raw = Read<std::int32_t>(b, key, 0x10);
    if (!row.key_full_id_raw) { Reason(row.reason, "remaining_map_key_id_unavailable"); return; }
    bool found = false;
    for (std::int32_t i = 0; i < count; ++i) {
      const void *descriptor = Offset(data, static_cast<std::size_t>(i) * 0x30);
      if (pointer_descriptors) {
        const auto pointer = Read<const void *>(b, data, static_cast<std::size_t>(i) * 8);
        if (!pointer) { Reason(row.reason, "remaining_map_descriptor_unavailable"); return; }
        descriptor = *pointer;
      }
      const auto candidate = Read<const void *>(b, descriptor, 0x20);
      if (!candidate) { Reason(row.reason, "remaining_map_candidate_key_unavailable"); return; }
      const auto id = Read<std::int32_t>(b, *candidate, 0x10);
      if (!id) { Reason(row.reason, "remaining_map_candidate_id_unavailable"); return; }
      if (*id != *row.key_full_id_raw) continue;
      found = true;
      row.mapping_native_index = i;
      if (pointer_descriptors) {
        const auto selected = Read<const void *>(b, data, static_cast<std::size_t>(i) * 8);
        if (!selected) { Reason(row.reason, "remaining_map_selected_descriptor_unavailable"); return; }
        descriptor = *selected;
        if (!descriptor) { use_default = true; break; }
      }
      const auto property = Read<const void *>(b, descriptor, 0x28);
      if (!property) { Reason(row.reason, "remaining_map_pc_pointer_unavailable"); return; }
      pc = *property;
      break;
    }
    if (!found) {
      if (pointer_descriptors) {
        Reason(row.reason, "remaining_culture_map_no_match_native_dereference_unobserved");
        return;
      }
      use_default = true;
    }
  }
  if (use_default) {
    pc = default_pc;
    RemainingProperty(b, pc, pointer_descriptors
        ? "inline_culture_mapped_default_5dc2380"
        : "inline_nested_mapped_default_5dc21b0", row, ids);
    if (!guard || *guard == 0 || *guard == -1)
      Reason(row.reason, guard ? "remaining_mapped_default_not_initialized"
                               : "remaining_mapped_default_guard_unavailable");
  } else {
    RemainingProperty(b, pc, "first_full_id_10_mapping", row, ids);
  }
}
RemainingFamily RemainingMapped(const ContextSourceBindingsV1 &b,
    const void *character, const void *header, bool pointer_descriptors,
    game::ContextSourceRemainingRiteV1 &rite, RemainingRiteState &rite_state,
    const void *default_pc, const void *guard_slot,
    std::optional<std::int32_t> &guard_raw, std::vector<const void *> &ids) {
  RemainingFamily out{};
  out.admitted = true;
  const auto data = Read<const void *>(b, header);
  if (data) out.array_present = *data != nullptr;
  out.count = Read<std::int32_t>(b, header, 0xC);
  if (!data || !out.count) out.reason = "remaining_mapped_header_unavailable";
  else if (*out.count < 0) out.reason = "remaining_mapped_negative_count";
  else if (*out.count == 0) out.rows.emplace();
  else if (!*data) out.reason = "remaining_mapped_positive_count_null_array";
  else {
    const bool members_ready = RemainingRite(b, character, rite, rite_state, ids);
    out.rows.emplace();
    for (std::int32_t i = 0; i < *out.count; ++i) {
      RemainingRow row{};
      row.native_index = i;
      const void *descriptor = Offset(*data, static_cast<std::size_t>(i) * 0x30);
      if (pointer_descriptors) {
        const auto pointer = Read<const void *>(b, *data, static_cast<std::size_t>(i) * 8);
        if (pointer) descriptor = *pointer;
        else descriptor = nullptr;
      }
      row.source_identity = Identity(ids, descriptor, "remaining");
      const auto key = Read<const void *>(b, descriptor, 0x20);
      if (!key) row.reason = "remaining_mapped_key_pointer_unavailable";
      else {
        row.key_identity = Identity(ids, *key, "remaining");
        if (!members_ready) row.reason = "remaining_mapped_membership_unavailable";
        else {
          row.admitted = std::find(rite_state.members->begin(), rite_state.members->end(), *key)
              != rite_state.members->end();
          if (row.admitted == true) {
            // The native marker is read before mapping, including valid maps.
            guard_raw = Read<std::int32_t>(b, guard_slot);
            if (!guard_raw) row.reason = "remaining_mapped_default_guard_unavailable";
            RemainingMap(b, *key, *data, *out.count, pointer_descriptors,
                         default_pc, guard_raw, row, ids);
          }
        }
      }
      if (!row.reason.empty()) Reason(out.reason, row.reason.c_str());
      out.rows->push_back(std::move(row));
    }
  }
  RemainingFinish(out);
  return out;
}
game::ContextSourceRemaining550V1 Remaining550(const ContextSourceBindingsV1 &b,
    const void *character, std::vector<const void *> &ids) {
  game::ContextSourceRemaining550V1 out{};
  out.status = "partial";
  const auto *culture = PreRegistry(b, b.selector_b_storage_slot,
      b.selector_b_fallback_slot, Offset(character, 0xB0),
      out.culture_key_b0_raw, out.culture_selection, out.reason);
  if (culture) {
    out.culture_identity = Identity(ids, culture, "remaining");
    out.culture_magic_raw = Read<std::uint32_t>(b, culture, 0x14);
    if (!out.culture_magic_raw) out.reason = "remaining_culture_magic_unavailable";
    else if (*out.culture_magic_raw != 0x43756C74U) out.admitted = false;
    else {
      out.culture_full_id_raw = Read<std::int32_t>(b, culture, 0x10);
      if (!out.culture_full_id_raw) out.reason = "remaining_culture_id_unavailable";
      else out.admitted = *out.culture_full_id_raw != -1;
    }
  }
  if (out.admitted == false) {
    RemainingSkip(out.government_indexed);
    RemainingSkip(out.culture_direct);
    RemainingSkip(out.culture_mapped);
    out.ready = true;
    out.status = "available";
    return out;
  }
  if (out.admitted != true) {
    if (out.reason.empty()) out.reason = "remaining_culture_selection_unavailable";
    for (auto *family : {&out.government_indexed, &out.culture_direct, &out.culture_mapped}) {
      family->reason = out.reason;
      RemainingFinish(*family);
    }
    return out;
  }
  auto &government_family = out.government_indexed;
  government_family.admitted = true;
  government_family.count = 1; // One native candidate, not a PC key count.
  government_family.rows.emplace();
  RemainingRow government_row{};
  const auto *government = RemainingGovernment(b, character, out.government_selection,
                                                government_row.reason);
  if (government) {
    out.government_identity = Identity(ids, government, "remaining");
    government_row.source_identity = out.government_identity;
    out.government_magic_raw = Read<std::uint32_t>(b, government, 0x38);
    if (!out.government_magic_raw) government_row.reason = "remaining_government_magic_unavailable";
    else {
      government_row.admitted = true;
      if (*out.government_magic_raw == 0x4744624FU) {
        out.government_full_id_raw = Read<std::int32_t>(b, government, 0x10);
        const auto table = Read<const void *>(b, culture, 0x670);
        if (!out.government_full_id_raw || !table)
          government_row.reason = "remaining_government_index_operands_unavailable";
        else {
          const auto delta = static_cast<std::int64_t>(*out.government_full_id_raw) * 0x1C0;
          const auto *pc = reinterpret_cast<const void *>(reinterpret_cast<std::uintptr_t>(*table)
              + static_cast<std::uintptr_t>(delta));
          RemainingProperty(b, pc, "government_indexed_1c0", government_row, ids);
        }
      } else {
        out.government_default_guard_raw = Read<std::int32_t>(b, b.remaining_government_default_guard_slot);
        RemainingProperty(b, b.remaining_government_default_pc,
                          "inline_government_default_5d65890", government_row, ids);
        if (!out.government_default_guard_raw || *out.government_default_guard_raw == 0 ||
            *out.government_default_guard_raw == -1)
          Reason(government_row.reason, out.government_default_guard_raw
              ? "remaining_government_default_not_initialized"
              : "remaining_government_default_guard_unavailable");
      }
    }
  }
  government_family.reason = government_row.reason;
  government_family.rows->push_back(std::move(government_row));
  RemainingFinish(government_family);
  auto &direct = out.culture_direct;
  direct.admitted = true;
  const auto direct_data = Read<const void *>(b, culture, 0x90);
  if (direct_data) direct.array_present = *direct_data != nullptr;
  direct.count = Read<std::int32_t>(b, culture, 0x9C);
  if (!direct_data || !direct.count) direct.reason = "remaining_culture_direct_header_unavailable";
  else if (*direct.count < 0) direct.reason = "remaining_culture_direct_negative_count";
  else if (*direct.count == 0) direct.rows.emplace();
  else if (!*direct_data) direct.reason = "remaining_culture_direct_positive_count_null_array";
  else {
    direct.rows.emplace();
    for (std::int32_t i = 0; i < *direct.count; ++i) {
      RemainingRow row{};
      row.native_index = i;
      const auto pc = Read<const void *>(b, *direct_data, static_cast<std::size_t>(i) * 8);
      if (!pc) row.reason = "remaining_culture_direct_pointer_unavailable";
      else {
        row.source_identity = Identity(ids, *pc, "remaining");
        row.admitted = true;
        RemainingProperty(b, *pc, "direct_pc_pointer", row, ids);
      }
      if (!row.reason.empty()) Reason(direct.reason, row.reason.c_str());
      direct.rows->push_back(std::move(row));
    }
  }
  RemainingFinish(direct);
  RemainingRiteState rite_state{};
  out.culture_mapped = RemainingMapped(b, character, Offset(culture, 0x230), true,
      out.rite, rite_state, b.remaining_culture_mapped_default_pc,
      b.remaining_culture_mapped_default_guard_slot, out.mapped_default_guard_raw, ids);
  out.ready = government_family.ready && direct.ready && out.culture_mapped.ready;
  out.status = out.ready ? "available" : "partial";
  if (!out.ready) out.reason = "remaining_550_current_families_partial";
  return out;
}
game::ContextSourceRemaining940V1 Remaining940(const ContextSourceBindingsV1 &b,
    const void *character, std::vector<const void *> &ids) {
  game::ContextSourceRemaining940V1 out{};
  out.status = "partial";
  const auto *first = PreRegistry(b, b.first_storage_slot, b.first_fallback_slot,
      Offset(character, 0x158), out.first_key_158_raw, out.first_selection, out.reason);
  const auto *second = first ? PreRegistry(b, b.second_storage_slot, b.second_fallback_slot,
      Offset(first, 0x2C), out.second_key_2c_raw, out.second_selection, out.reason) : nullptr;
  if (!second) return out;
  out.selected_identity = Identity(ids, second, "remaining");
  const auto data = Read<const void *>(b, second, 0x178);
  if (data) out.outer_array_present = *data != nullptr;
  out.outer_count = Read<std::int32_t>(b, second, 0x184);
  if (!data || !out.outer_count) out.reason = "remaining_940_outer_header_unavailable";
  else if (*out.outer_count < 0) out.reason = "remaining_940_negative_outer_count";
  else if (*out.outer_count > 0 && !*data) out.reason = "remaining_940_positive_count_null_array";
  if (!out.reason.empty()) return out;
  out.outer_rows.emplace();
  out.direct_ready = true;
  out.mapped_ready = true;
  RemainingRiteState rite_state{};
  for (std::int32_t i = 0; i < *out.outer_count; ++i) {
    game::ContextSourceRemainingOuterV1 row{};
    row.native_index = i;
    const auto source = Read<const void *>(b, *data, static_cast<std::size_t>(i) * 8);
    if (!source || !*source) {
      row.direct_reason = "remaining_940_source_pointer_unavailable";
      row.inner_mapped.reason = row.direct_reason;
      RemainingFinish(row.inner_mapped);
    } else {
      row.source_identity = Identity(ids, *source, "remaining");
      row.direct_gate_raw = Read<std::int32_t>(b, *source, 0x16C);
      if (!row.direct_gate_raw) row.direct_reason = "remaining_940_direct_gate_unavailable";
      else {
        row.direct_admitted = *row.direct_gate_raw != 0;
        if (row.direct_admitted == true) {
          const auto *pc = Offset(*source, 0x160);
          row.direct_property_identity = Identity(ids, pc, "remaining");
          row.direct_property_block = Properties(b, pc);
          if (!PropertiesReady(*row.direct_property_block))
            row.direct_reason = "remaining_940_direct_properties_unavailable";
        }
      }
      row.inner_mapped = RemainingMapped(b, character, Offset(*source, 0x450), false,
          out.rite, rite_state, b.conditional_a_fallback_properties,
          b.remaining_nested_mapped_default_guard_slot, out.mapped_default_guard_raw, ids);
    }
    out.direct_ready = out.direct_ready && row.direct_reason.empty();
    out.mapped_ready = out.mapped_ready && row.inner_mapped.ready;
    out.outer_rows->push_back(std::move(row));
  }
  out.ready = out.direct_ready && out.mapped_ready;
  out.status = out.ready ? "available" : "partial";
  if (!out.ready) out.reason = "remaining_940_current_families_partial";
  return out;
}
game::ContextSourceRemainingHelpersV1 RemainingHelpers(
    const ContextSourceBindingsV1 &b, const void *character, std::int32_t character_id) {
  game::ContextSourceRemainingHelpersV1 out{};
  out.character_id = character_id;
  std::vector<const void *> ids;
  out.helper_291f550 = Remaining550(b, character, ids);
  out.helper_291f940 = Remaining940(b, character, ids);
  out.ready = out.helper_291f550.ready && out.helper_291f940.ready;
  out.status = out.ready ? "available" : "partial";
  if (!out.ready) out.reason = "remaining_person_helper_families_partial";
  return out;
}
