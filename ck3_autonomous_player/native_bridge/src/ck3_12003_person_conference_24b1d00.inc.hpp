// Exact-build source packet conference-24b1d00-source precedes this reader.
template <typename T> void ConferenceFinish(T &out) {
  out.ready = out.reason.empty();
  out.status = out.ready ? "available" : "partial";
}
const void *ConferenceResolve(const ContextSourceBindingsV1 &b,
    const std::optional<const void *> &store, const void *fallback_slot,
    const void *key_address, std::optional<std::int32_t> explicit_key,
    std::size_t id_offset, game::ContextSourceConferenceObjectV1 &out,
    std::vector<const void *> &ids) {
  if (!store) { out.reason = "conference_registry_unavailable"; return nullptr; }
  if (*store) {
    out.requested_full_id_raw = explicit_key ? explicit_key : Read<std::int32_t>(b, key_address);
    if (!out.requested_full_id_raw) { out.reason = "conference_requested_id_unavailable"; return nullptr; }
    const auto capacity = Read<std::uint32_t>(b, *store, 0x2C);
    if (!capacity) { out.reason = "conference_registry_capacity_unavailable"; return nullptr; }
    const auto index = static_cast<std::uint32_t>(*out.requested_full_id_raw) & 0xFFFFFFU;
    if (index < *capacity) {
      const auto table = Read<const void *>(b, *store, 0x20);
      const auto candidate = table ? Read<const void *>(b, *table, static_cast<std::size_t>(index) * 16 + 8) : std::nullopt;
      if (!candidate) { out.reason = "conference_registry_slot_unavailable"; return nullptr; }
      if (*candidate) {
        const auto full_id = Read<std::int32_t>(b, *candidate, id_offset);
        if (!full_id) { out.reason = "conference_registry_full_id_unavailable"; return nullptr; }
        if (*full_id == *out.requested_full_id_raw) {
          out.selection = id_offset == 8 ? "registry_full_id_8" : "registry_full_id_10";
          out.identity = Identity(ids, *candidate, "conference");
          out.full_id_raw = *full_id;
          return *candidate;
        }
      }
    }
  } else if (explicit_key) out.requested_full_id_raw = explicit_key;
  const auto fallback = Read<const void *>(b, fallback_slot);
  if (!fallback) { out.reason = "conference_native_fallback_unavailable"; return nullptr; }
  out.selection = "native_fallback";
  out.identity = Identity(ids, *fallback, "conference");
  // Conf's full ID is demanded only after its magic gate. Relation IDs are
  // demanded unconditionally by the category comparison, including fallback.
  if (id_offset == 0x10) {
    out.full_id_raw = Read<std::int32_t>(b, *fallback, id_offset);
    if (!out.full_id_raw) out.reason = "conference_selected_full_id_unavailable";
  }
  return *fallback;
}
const void *ConferencePack(const ContextSourceBindingsV1 &b, const void *conf,
    game::ContextSourceConferencePackV1 &out, std::vector<const void *> &ids) {
  out.reason.clear();
  const auto config = Read<const void *>(b, conf, 0x38);
  out.target_q64 = Read<std::int64_t>(b, conf, 0x60);
  if (!config || !out.target_q64) {
    out.reason = "conference_pack_arguments_unavailable"; ConferenceFinish(out); return nullptr;
  }
  out.configuration_identity = Identity(ids, *config, "conference");
  out.enabled_u8 = Read<std::uint8_t>(b, *config, 0xAB08);
  if (!out.enabled_u8) {
    out.reason = "conference_pack_flag_unavailable"; ConferenceFinish(out); return nullptr;
  }
  const void *pack = nullptr;
  if (*out.enabled_u8 != 0) {
    const auto data = Read<const void *>(b, *config, 0x160);
    out.count_raw = Read<std::int32_t>(b, *config, 0x16C);
    if (data) out.array_present = *data != nullptr;
    out.probes.emplace();
    if (!data || !out.count_raw || *out.count_raw < 0) {
      out.reason = out.count_raw && *out.count_raw < 0
          ? "conference_pack_negative_count" : "conference_pack_header_unavailable";
      ConferenceFinish(out); return nullptr;
    }
    for (std::int32_t index = *out.count_raw; index > 0;) {
      --index;
      const auto *row = Offset(*data, static_cast<std::size_t>(index) * 0x1530);
      const auto timestamp = Read<std::int64_t>(b, row, 0x10);
      if (!timestamp) {
        out.reason = "conference_pack_timestamp_unavailable"; ConferenceFinish(out); return nullptr;
      }
      out.probes->push_back({index, *timestamp});
      if (*timestamp <= *out.target_q64) {
        pack = row;
        out.selected_native_index = index;
        out.selection = "last_native_row_at_or_before_target";
        break;
      }
    }
  }
  if (!pack) {
    pack = b.conference_24b1d00.inline_default_pack;
    out.selection = "inline_default_54ebab0";
    out.default_guard_raw = Read<std::int32_t>(b, b.conference_24b1d00.default_guard_slot);
    if (!out.default_guard_raw || *out.default_guard_raw == 0 || *out.default_guard_raw == -1)
      out.reason = out.default_guard_raw ? "conference_default_not_initialized" : "conference_default_guard_unavailable";
  }
  out.pack_identity = Identity(ids, pack, "conference");
  if (!pack) Reason(out.reason, "conference_selected_pack_null");
  ConferenceFinish(out);
  return pack;
}
game::ContextSourceConference24b1d00V1 Conference24b1d00(
    const ContextSourceBindingsV1 &b, const void *character, std::int32_t character_id) {
  game::ContextSourceConference24b1d00V1 out{};
  out.character_id = character_id;
  for (int i = 0; i < 4; ++i) {
    game::ContextSourceConferenceFamilyV1 family{};
    family.native_index = i;
    out.families.push_back(std::move(family));
  }
  const auto fail = [&](const char *reason) {
    out.reason = reason;
    for (auto &family : out.families) { family.reason = reason; ConferenceFinish(family); }
    ConferenceFinish(out); return out;
  };
  const auto skip = [&]() {
    out.admitted = false;
    for (auto &family : out.families) { family.admitted = false; ConferenceFinish(family); }
    ConferenceFinish(out); return out;
  };
  if (!b.conference_24b1d00.enabled) return fail("conference_bindings_unavailable");
  std::vector<const void *> ids;
  const auto carrier = Read<const void *>(b, character, 0x1C8);
  if (!carrier) return fail("conference_character_carrier_unavailable");
  out.carrier_present = *carrier != nullptr;
  const auto key = *carrier ? Read<std::int32_t>(b, *carrier, 0x80) : std::optional<std::int32_t>{-1};
  if (!key) return fail("conference_caller_key_unavailable");
  out.conference.requested_full_id_raw = key;
  const auto conf_store = Read<const void *>(b, b.conference_24b1d00.conf_registry_slot);
  const auto *conf = ConferenceResolve(b, conf_store, b.conference_24b1d00.conf_fallback_slot,
      nullptr, key, 8, out.conference, ids);
  if (!out.conference.reason.empty()) return fail(out.conference.reason.c_str());
  out.conference_magic_raw = Read<std::uint32_t>(b, conf, 0xC);
  if (!out.conference_magic_raw) return fail("conference_magic_unavailable");
  if (*out.conference_magic_raw != 0x436F6E66U) { out.conference_admitted = false; return skip(); }
  out.conference.full_id_raw = Read<std::int32_t>(b, conf, 8);
  if (!out.conference.full_id_raw) return fail("conference_full_id_unavailable");
  out.conference_admitted = *out.conference.full_id_raw != -1;
  if (!*out.conference_admitted) return skip();
  out.character_magic_raw = Read<std::uint32_t>(b, character, 0x1C);
  if (!out.character_magic_raw) return fail("conference_character_magic_unavailable");
  if (*out.character_magic_raw != 0x43686172U) { out.character_admitted = false; return skip(); }
  out.character_full_id_raw = Read<std::int32_t>(b, character, 0x18);
  if (!out.character_full_id_raw) return fail("conference_character_full_id_unavailable");
  out.character_admitted = *out.character_full_id_raw != -1;
  if (!*out.character_admitted) return skip();
  out.admitted = true;
  const auto *pack = ConferencePack(b, conf, out.pack, ids);
  const auto registry = Read<const void *>(b, b.conference_24b1d00.relation_registry_slot);
  if (registry) out.relation_registry_present = *registry != nullptr;
  const auto *first = ConferenceResolve(b, registry, b.conference_24b1d00.relation_fallback_slot,
      Offset(conf, 0x68), std::nullopt, 0x10, out.first, ids);
  const auto *second = ConferenceResolve(b, registry, b.conference_24b1d00.relation_fallback_slot,
      Offset(character, 0x158), std::nullopt, 0x10, out.second, ids);
  if (out.second.selection) {
    out.owner_full_id_raw = Read<std::int32_t>(b, second, 0x160);
    if (out.owner_full_id_raw) out.owner_matches = *out.owner_full_id_raw == *out.character_full_id_raw;
  }
  if (out.first.full_id_raw && out.second.full_id_raw) {
    if (*out.first.full_id_raw == *out.second.full_id_raw) out.category = "same_id";
    else {
      const auto first_group = Read<const void *>(b, first, 0x220);
      const auto second_group = Read<const void *>(b, second, 0x220);
      if (first_group) out.first_group_identity = Identity(ids, *first_group, "conference");
      if (second_group) out.second_group_identity = Identity(ids, *second_group, "conference");
      if (first_group && second_group) out.category = *first_group == *second_group ? "same_identity" : "different";
    }
  }
  const auto read_family = [&](int index, std::optional<std::uint32_t> offset) {
    auto &family = out.families[index];
    family.admitted = true;
    family.pc_offset = offset;
    if (!out.pack.ready) family.reason = out.pack.reason;
    if (!offset) Reason(family.reason, "conference_family_predicate_unavailable");
    if (pack && offset) {
      const auto *pc = Offset(pack, *offset);
      family.property_identity = Identity(ids, pc, "conference");
      family.property_block = Properties(b, pc);
      if (!PropertiesReady(*family.property_block) || !family.property_block->reason.empty())
        Reason(family.reason, "conference_family_properties_unavailable");
    } else Reason(family.reason, "conference_family_pack_unavailable");
    ConferenceFinish(family);
    if (!family.ready) Reason(out.reason, "conference_families_partial");
  };
  std::optional<std::uint32_t> specific, common;
  if (out.category) {
    const int index = *out.category == "same_id" ? 0 : *out.category == "same_identity" ? 1 : 2;
    constexpr std::uint32_t owners[] = {0x30U, 0xAB0U, 0xFF0U};
    constexpr std::uint32_t others[] = {0x1F0U, 0xC70U, 0x11B0U};
    constexpr std::uint32_t commons[] = {0x3B0U, 0xE30U, 0x1370U};
    common = commons[index];
    if (out.owner_matches) specific = *out.owner_matches ? owners[index] : others[index];
  }
  read_family(0, specific);
  read_family(1, common);
  read_family(2, out.owner_matches ? std::optional<std::uint32_t>{*out.owner_matches ? 0x570U : 0x730U} : std::nullopt);
  read_family(3, std::uint32_t{0x8F0U});
  ConferenceFinish(out);
  return out;
}
