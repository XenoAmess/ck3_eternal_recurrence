// Included after source-closed AfterRegistry/AfterPc helpers. This raw
// projection preserves all-attribute preflight before any numeric rank/PC.
void FollowingRankedAttribute(const ContextSourceBindingsV1 &b,
    const void *attribute, const void *definition, bool own,
    game::ContextSourceFollowing2920b50AttributeV1 &out) {
  const auto &raw = b.following_2920b50;
  out.rank_raw_i32 = Read<std::int32_t>(b, attribute, 8);
  if (!out.rank_raw_i32) { out.reason = "following_attribute_rank_unavailable"; return; }
  out.index_raw_i32 = AfterWrap32(static_cast<std::uint32_t>(*out.rank_raw_i32) - 1U);
  const void *header = Offset(definition, 0x3C0);
  out.ranked_header_identity = TraitStageIdentity(header);
  const void *selected = nullptr;
  bool fallback = *out.index_raw_i32 < 0;
  if (!fallback) {
    out.ranked_count_raw = Read<std::int32_t>(b, header, 0xC);
    if (!out.ranked_count_raw) { out.reason = "following_ranked_count_unavailable"; return; }
    fallback = *out.index_raw_i32 >= *out.ranked_count_raw;
    if (!fallback) {
      out.selection = "indexed_ranked_row";
      const auto data = Read<const void *>(b, header);
      if (data) out.ranked_array_present = *data != nullptr;
      if (!data || !*data) { out.reason = "following_ranked_array_unavailable"; return; }
      selected = Offset(*data, static_cast<std::size_t>(*out.index_raw_i32) * 0x5F8);
    }
  }
  if (fallback) {
    selected = raw.ranked_default_row;
    out.selected_row_identity = TraitStageIdentity(selected);
    out.ranked_default_init_guard_raw = Read<std::int32_t>(b, raw.ranked_default_guard_slot);
    if (!out.ranked_default_init_guard_raw) {
      out.reason = "following_ranked_default_guard_unavailable"; return;
    }
    if (*out.ranked_default_init_guard_raw == 0 || *out.ranked_default_init_guard_raw == -1) {
      out.selection = "uninitialized_default_5d68fb0";
      out.reason = "ranked_default_initialization_result";
      return;
    }
    out.selection = "initialized_default_5d68fb0";
  }
  out.selected_row_identity = TraitStageIdentity(selected);
  out.pc = AfterPc(b, Offset(selected, own ? 0x1D0U : 0x10U));
  out.reason = out.pc.reason;
  out.ready = out.reason.empty();
}
void FollowingAttributeVector(const ContextSourceBindingsV1 &b,
    const void *object, bool own,
    game::ContextSourceFollowing2920b50OccurrenceV1 &out) {
  out.attribute_count_raw = Read<std::int32_t>(b, object, 0x64);
  if (!out.attribute_count_raw) {
    out.reason = "following_attribute_count_unavailable"; AfterFinish(out); return;
  }
  if (*out.attribute_count_raw < 0) {
    out.reason = "following_attribute_negative_count"; AfterFinish(out); return;
  }
  if (*out.attribute_count_raw == 0) {
    out.attributes.emplace();
    out.preflight_ready = true;
    out.preflight_all_valid = true;
    AfterFinish(out); return;
  }
  const auto data = Read<const void *>(b, object, 0x58);
  if (data) out.attribute_array_present = *data != nullptr;
  if (!data || !*data) {
    out.reason = "following_attribute_array_unavailable"; AfterFinish(out); return;
  }
  out.attributes.emplace();
  std::vector<const void *> definitions;
  for (std::int32_t i = 0; i < *out.attribute_count_raw; ++i) {
    game::ContextSourceFollowing2920b50AttributeV1 row{};
    row.native_index = i;
    const auto definition = Read<const void *>(b, *data, static_cast<std::size_t>(i) * 0x18 + 0x10);
    if (!definition) row.reason = "following_attribute_definition_pointer_unavailable";
    else {
      row.definition_present = *definition != nullptr;
      if (!*definition) row.preflight_valid = false;
      else {
        row.definition_identity = TraitStageIdentity(*definition);
        row.definition_magic_u32 = Read<std::uint32_t>(b, *definition, 0x38);
        if (!row.definition_magic_u32) row.reason = "following_attribute_definition_magic_unavailable";
        else row.preflight_valid = *row.definition_magic_u32 == 0x4744624FU;
      }
    }
    const auto valid = row.preflight_valid;
    if (!row.reason.empty()) out.reason = row.reason;
    out.attributes->push_back(std::move(row));
    if (valid == false) {
      // The entire occurrence is known zero before ANY rank or PC demand.
      out.preflight_ready = true;
      out.preflight_all_valid = false;
      AfterFinish(out); return;
    }
    if (valid != true) { AfterFinish(out); return; }
    definitions.push_back(*definition);
  }
  out.preflight_ready = true;
  out.preflight_all_valid = true;
  for (std::int32_t i = 0; i < *out.attribute_count_raw; ++i) {
    auto &row = out.attributes->at(static_cast<std::size_t>(i));
    FollowingRankedAttribute(b, Offset(*data, static_cast<std::size_t>(i) * 0x18),
        definitions.at(static_cast<std::size_t>(i)), own, row);
    if (!row.ready) Reason(out.reason, row.reason.c_str());
  }
  AfterFinish(out);
}
void FollowingKnownOwnSkip(game::ContextSourceFollowing2920b50OccurrenceV1 &out) {
  out.admitted = false;
  out.attributes.emplace();
  out.preflight_ready = true;
  out.preflight_all_valid = false;
  AfterFinish(out);
}
game::ContextSourceFollowing2920b50OccurrenceV1 FollowingListOccurrence(
    const ContextSourceBindingsV1 &b, const void *id_address, std::int32_t index) {
  game::ContextSourceFollowing2920b50OccurrenceV1 out{};
  out.native_index = index;
  const auto &raw = b.following_2920b50;
  const void *object = AfterRegistry(b, raw.accolade_storage_slot,
      raw.accolade_fallback_slot, id_address, 8, "registry_full_id_8",
      out.requested_full_id_raw, out.resolution_selection,
      out.selected_full_id_raw, out.reason);
  if (!object) { AfterFinish(out); return out; }
  out.object_identity = TraitStageIdentity(object);
  out.admitted = true; // This list has no Acco magic/sentinel admission gate.
  FollowingAttributeVector(b, object, false, out);
  return out;
}
game::ContextSourceFollowing2920b50ListV1 FollowingList(
    const ContextSourceBindingsV1 &b, const void *character) {
  game::ContextSourceFollowing2920b50ListV1 out{};
  const auto &raw = b.following_2920b50;
  const auto component = Read<const void *>(b, character, 0x1C8);
  if (!component) { out.reason = "following_list_component_unavailable"; AfterFinish(out); return out; }
  out.component_present = *component != nullptr;
  const void *header = nullptr;
  if (*component) {
    out.header_selection = "current_1c8_50";
    header = Offset(*component, 0x50);
  } else {
    out.header_selection = "inline_default_5d67e80";
    out.default_init_guard_raw = Read<std::int32_t>(b, raw.list_default_guard_slot);
    if (!out.default_init_guard_raw) {
      out.reason = "following_default_list_guard_unavailable"; AfterFinish(out); return out;
    }
    if (*out.default_init_guard_raw == 0 || *out.default_init_guard_raw == -1) {
      out.header_selection = "modeled_empty_default_5d67e80";
      out.numeric_count = 0;
      out.rows.emplace();
      AfterFinish(out); return out;
    }
    header = raw.list_default_header;
  }
  out.count_raw = Read<std::int32_t>(b, header, 0xC);
  out.numeric_count = out.count_raw;
  if (!out.count_raw) out.reason = "following_list_count_unavailable";
  else if (*out.count_raw < 0) out.reason = "following_list_negative_count";
  else if (*out.count_raw == 0) out.rows.emplace();
  else {
    const auto data = Read<const void *>(b, header);
    if (data) out.array_present = *data != nullptr;
    if (!data || !*data) out.reason = "following_list_array_unavailable";
    else {
      out.rows.emplace();
      for (std::int32_t i = 0; i < *out.count_raw; ++i) {
        auto row = FollowingListOccurrence(b, Offset(*data, static_cast<std::size_t>(i) * 4), i);
        if (!row.ready) Reason(out.reason, "following_list_occurrence_partial");
        out.rows->push_back(std::move(row));
      }
    }
  }
  AfterFinish(out);
  return out;
}
game::ContextSourceFollowing2920b50OwnV1 FollowingOwn(
    const ContextSourceBindingsV1 &b, const void *character) {
  game::ContextSourceFollowing2920b50OwnV1 out{};
  auto &occurrence = out.occurrence;
  const auto &raw = b.following_2920b50;
  const auto finish = [&]() {
    if (!occurrence.ready) out.reason = occurrence.reason;
    AfterFinish(out); return out;
  };
  const auto component = Read<const void *>(b, character, 0x1B0);
  if (!component) {
    occurrence.reason = "following_own_component_unavailable"; AfterFinish(occurrence); return finish();
  }
  out.component_present = *component != nullptr;
  const void *object = nullptr;
  if (*component) {
    object = AfterRegistry(b, raw.accolade_storage_slot, raw.accolade_fallback_slot,
        Offset(*component, 0x570), 8, "registry_full_id_8", occurrence.requested_full_id_raw,
        occurrence.resolution_selection, occurrence.selected_full_id_raw, occurrence.reason);
  } else {
    occurrence.resolution_selection = "native_fallback";
    const auto fallback = Read<const void *>(b, raw.accolade_fallback_slot);
    if (fallback) object = *fallback;
    if (!object) occurrence.reason = "following_own_fallback_unavailable";
  }
  if (!object) { AfterFinish(occurrence); return finish(); }
  occurrence.object_identity = TraitStageIdentity(object);
  occurrence.accolade_magic_u32 = Read<std::uint32_t>(b, object, 0xC);
  if (!occurrence.accolade_magic_u32) {
    occurrence.reason = "following_own_accolade_magic_unavailable"; AfterFinish(occurrence); return finish();
  }
  if (*occurrence.accolade_magic_u32 != 0x4163636FU) {
    FollowingKnownOwnSkip(occurrence); return finish();
  }
  occurrence.accolade_full_id_raw = Read<std::int32_t>(b, object, 8);
  if (!occurrence.accolade_full_id_raw) {
    occurrence.reason = "following_own_accolade_id_unavailable"; AfterFinish(occurrence); return finish();
  }
  if (*occurrence.accolade_full_id_raw == -1) {
    FollowingKnownOwnSkip(occurrence); return finish();
  }
  occurrence.admitted = true;
  FollowingAttributeVector(b, object, true, occurrence);
  return finish();
}
game::ContextSourceFollowing2920b50InputsV1 Following2920b50Inputs(
    const ContextSourceBindingsV1 &b, const void *character, std::int32_t id) {
  game::ContextSourceFollowing2920b50InputsV1 out{};
  out.character_id = id;
  out.list_1c8_50 = FollowingList(b, character);
  out.own_1b0_570 = FollowingOwn(b, character);
  if (!out.list_1c8_50.ready || !out.own_1b0_570.ready)
    out.reason = "following_2920b50_families_partial";
  AfterFinish(out);
  return out;
}
