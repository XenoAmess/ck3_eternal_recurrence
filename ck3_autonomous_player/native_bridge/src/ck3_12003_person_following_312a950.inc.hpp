// Included after accepted RemainingLookup/AfterRegistry source recipes.
// Government is death-first; current first Land is independently live-first.
game::ContextSourceFollowing312a950GovernmentV1 Following312a950Government(
    const ContextSourceBindingsV1 &b, const void *character) {
  game::ContextSourceFollowing312a950GovernmentV1 out{};
  const auto &raw = b.following_312a950;
  const auto finish = [&]() { AfterFinish(out); return out; };
  // Actual28C2E10 captures these two raw slots once before Character gates.
  const auto store = Read<const void *>(b, raw.character_storage_slot);
  const auto fallback = Read<const void *>(b, raw.character_fallback_slot);
  if (!store || !fallback) {
    out.reason = "following312a950_government_character_slots_unavailable"; return finish();
  }
  const void *current = character;
  const void *government = nullptr;
  std::int32_t ordinal = 0;
  while (current) {
    out.selected_character_identity = TraitStageIdentity(current);
    out.selection_native_index = ordinal;
    const auto magic = Read<std::uint32_t>(b, current, 0x1C);
    if (!magic) { out.reason = "following312a950_government_character_magic_unavailable"; return finish(); }
    if (*magic != 0x43686172U) break;
    const auto full = Read<std::int32_t>(b, current, 0x18);
    if (!full) { out.reason = "following312a950_government_character_id_unavailable"; return finish(); }
    if (*full == -1) break;
    const auto death = Read<const void *>(b, current, 0x1D0);
    if (!death) { out.reason = "following312a950_government_death_unavailable"; return finish(); }
    std::optional<const void *> selected;
    if (*death) {
      out.selection = "death_1d0_88";
      selected = Read<const void *>(b, *death, 0x88);
    } else {
      const auto living = Read<const void *>(b, current, 0x1C0);
      if (!living) { out.reason = "following312a950_government_living_unavailable"; return finish(); }
      if (*living) {
        out.selection = "living_1c0_3f8";
        selected = Read<const void *>(b, *living, 0x3F8);
      } else {
        const auto carrier = Read<const void *>(b, current, 0x1B8);
        if (!carrier) { out.reason = "following312a950_government_relay_unavailable"; return finish(); }
        const auto key = *carrier ? Read<std::int32_t>(b, *carrier, 0xC8)
                                  : std::optional<std::int32_t>{-1};
        if (!key) { out.reason = "following312a950_government_relay_id_unavailable"; return finish(); }
        std::optional<std::int32_t> requested;
        std::optional<std::string> selection;
        current = RemainingLookup(b, *store, *fallback, nullptr, 0x18,
            requested, selection, out.reason, &key);
        if (!current) {
          if (out.reason.empty()) out.reason = "following312a950_government_relay_character_unavailable";
          return finish();
        }
        ++ordinal;
        continue;
      }
    }
    if (!selected) { out.reason = "following312a950_government_pointer_unavailable"; return finish(); }
    government = *selected;
    break;
  }
  if (!government) {
    out.selection = "global_fallback_5d1e2a8";
    const auto selected = Read<const void *>(b, raw.government_fallback_slot);
    if (selected) government = *selected;
  }
  if (!government) { out.reason = "following312a950_government_fallback_unavailable"; return finish(); }
  out.government_identity = TraitStageIdentity(government);
  out.flags_raw_u32 = Read<std::uint32_t>(b, government, 0x40);
  if (!out.flags_raw_u32) out.reason = "following312a950_government_flags_unavailable";
  return finish();
}
game::ContextSourceFollowing312a950FirstLandV1 Following312a950FirstLand(
    const ContextSourceBindingsV1 &b, const void *character) {
  game::ContextSourceFollowing312a950FirstLandV1 out{};
  const auto finish = [&]() { AfterFinish(out); return out; };
  const auto living = Read<const void *>(b, character, 0x1C0);
  if (!living) { out.reason = "following312a950_first_land_living_unavailable"; return finish(); }
  out.living_present = *living != nullptr;
  const void *source = nullptr;
  std::size_t count_offset = 0;
  std::size_t array_offset = 0;
  if (*living) {
    out.selection = "living_1c0";
    source = *living;
    count_offset = 0x1EC;
    array_offset = 0x1E0;
  } else {
    const auto death = Read<const void *>(b, character, 0x1D0);
    if (!death) { out.reason = "following312a950_first_land_death_unavailable"; return finish(); }
    out.death_present = *death != nullptr;
    if (!*death) {
      out.selection = "none";
      out.full_id_raw = -1;
      return finish();
    }
    out.selection = "death_1d0";
    source = *death;
    count_offset = 0x74;
    array_offset = 0x68;
  }
  out.count_raw = Read<std::int32_t>(b, source, count_offset);
  if (!out.count_raw) { out.reason = "following312a950_first_land_count_unavailable"; return finish(); }
  if (*out.count_raw == 0) {
    out.full_id_raw = -1;
    return finish();
  }
  // This getter uses !=0, including negative counts, and reads only firstID.
  const auto data = Read<const void *>(b, source, array_offset);
  if (data) out.array_present = *data != nullptr;
  if (!data || !*data) { out.reason = "following312a950_first_land_array_unavailable"; return finish(); }
  out.full_id_raw = Read<std::int32_t>(b, *data);
  if (!out.full_id_raw) out.reason = "following312a950_first_land_id_unavailable";
  return finish();
}
game::ContextSourceFollowing312a950LandResolutionV1 Following312a950Land(
    const ContextSourceBindingsV1 &b, const std::optional<std::int32_t> &key) {
  game::ContextSourceFollowing312a950LandResolutionV1 out{};
  const auto &raw = b.following_312a950;
  const auto finish = [&]() { AfterFinish(out); return out; };
  const void *land = AfterRegistry(b, raw.land_storage_slot, raw.land_fallback_slot,
      nullptr, 0x10, "registry_full_id_10", out.requested_full_id_raw,
      out.selection, out.selected_full_id_raw, out.reason, &key);
  if (!land) return finish();
  out.object_identity = TraitStageIdentity(land);
  out.magic_u32 = Read<std::uint32_t>(b, land, 0x14);
  if (!out.magic_u32) { out.reason = "following312a950_land_magic_unavailable"; return finish(); }
  if (*out.magic_u32 != 0x4C616E64U) {
    out.admitted = false;
    return finish();
  }
  out.full_id_raw = Read<std::int32_t>(b, land, 0x10);
  if (!out.full_id_raw) { out.reason = "following312a950_land_id_unavailable"; return finish(); }
  out.admitted = *out.full_id_raw != -1;
  if (*out.admitted) {
    out.balance_raw_q64 = Read<std::int64_t>(b, land, 0x318);
    if (!out.balance_raw_q64) out.reason = "following312a950_land_balance_unavailable";
  }
  return finish();
}
game::ContextSourceFollowing312a950InputsV1 Following312a950Inputs(
    const ContextSourceBindingsV1 &b, const void *character, std::int32_t id) {
  game::ContextSourceFollowing312a950InputsV1 out{};
  out.character_id = id;
  const auto finish = [&]() { AfterFinish(out); return out; };
  out.government_source = Following312a950Government(b, character);
  if (!out.government_source.ready) { out.reason = out.government_source.reason; return finish(); }
  if ((*out.government_source.flags_raw_u32 & 0x20000000U) == 0U) {
    out.stage_selection = "government_bit29_false";
    return finish();
  }
  const auto state = Read<const void *>(b, character, 0x1B0);
  if (!state) { out.reason = "following312a950_character_state_unavailable"; return finish(); }
  out.character_state_present = *state != nullptr;
  if (!*state) {
    out.stage_selection = "character_1b0_absent";
    return finish();
  }
  out.first_land_source = Following312a950FirstLand(b, character);
  if (!out.first_land_source->ready) { out.reason = out.first_land_source->reason; return finish(); }
  out.land_resolution = Following312a950Land(b, out.first_land_source->full_id_raw);
  if (!out.land_resolution->ready) { out.reason = out.land_resolution->reason; return finish(); }
  if (out.land_resolution->admitted == false) {
    out.stage_selection = "first_land_invalid";
    return finish();
  }
  if (*out.land_resolution->balance_raw_q64 >= 0) {
    out.stage_selection = "first_land_nonnegative";
    return finish();
  }
  out.stage_selection = "negative_land_mode3_income_unobserved";
  out.mode3_classifier.emplace();
  out.mode3_classifier->reason = "mode3_income_2bca580";
  AfterFinish(*out.mode3_classifier);
  out.provider_selection.emplace();
  const auto provider = Read<const void *>(b, b.following_312a950.provider_slot);
  if (provider) out.provider_selection->provider_loaded = *provider != nullptr;
  out.provider_selection->reason = "mode3_income_2bca580";
  AfterFinish(*out.provider_selection);
  out.reason = "mode3_income_2bca580";
  return finish();
}
