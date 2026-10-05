// Included in the current-person collector anonymous namespace after the
// cached absent include. All operations read memory or calculate local values.
using UncachedInputs = game::ContextSourceUncachedRecipientInputsV1;
using UncachedFamily = game::ContextSourceUncachedIntrinsicFamilyV1;
struct UncachedRecord {
  std::uint64_t key{};
  std::int32_t id{};
  std::int64_t value{};
  std::uint8_t priority{};
  std::uint32_t kind{};
};
struct UncachedState {
  std::vector<UncachedRecord> kind2, kind1, seeds;
  std::uint8_t priority2 = 4, priority1 = 4;
  std::int64_t value2 = 0, value1 = 0;
};
std::int64_t UncachedFixedMul(std::int64_t a, std::int64_t b) noexcept {
  constexpr std::int64_t bound = 3037000499LL;
  constexpr std::int64_t q = 100000;
  if (a >= -bound && a <= bound && b >= -bound && b <= bound)
    return AbsentMul(a, b) / q;
  const auto lo = std::min(a, b);
  const auto hi = std::max(a, b);
  const auto quotient = hi / q;
  const auto remainder = AbsentAdd(hi, -AbsentMul(quotient, q));
  return AbsentAdd(AbsentMul(quotient, lo), AbsentMul(remainder, lo) / q);
}
std::vector<UncachedRecord> &UncachedGroup(UncachedState &s, std::uint32_t kind) {
  return kind == 2 ? s.kind2 : s.kind1;
}
void UncachedSort(std::vector<UncachedRecord> &rows) {
  std::stable_sort(rows.begin(), rows.end(), [](const auto &a, const auto &b) {
    if (a.priority != b.priority) return a.priority < b.priority;
    if (a.value != b.value) return a.value > b.value;
    return a.id > b.id;
  });
}
void UncachedRemove(UncachedState &s, std::uint32_t kind, std::uint64_t key) {
  auto &rows = UncachedGroup(s, kind);
  rows.erase(std::remove_if(rows.begin(), rows.end(), [key](const auto &r) {
    return r.key == key;
  }), rows.end());
  UncachedSort(rows);
}
void UncachedAppend(UncachedState &s, UncachedRecord r, UncachedInputs &out) {
  const auto seed = std::find_if(s.seeds.begin(), s.seeds.end(), [&](const auto &v) {
    return v.key == r.key;
  });
  if (seed != s.seeds.end() && seed->kind == r.kind) {
    if (!out.seed_boost_multiplier_q64)
      Reason(out.reason, "uncached_seed_boost_multiplier_unavailable");
    else r.value = AbsentAdd(r.value, UncachedFixedMul(seed->value, *out.seed_boost_multiplier_q64));
  }
  auto &rows = UncachedGroup(s, r.kind);
  rows.push_back(r);
  UncachedSort(rows);
}
bool UncachedOffer(UncachedState &s, UncachedRecord r, UncachedInputs &out) {
  if (r.kind == 0) return false;
  if (r.priority == 1) s.seeds.push_back(r);
  std::optional<UncachedRecord> existing;
  for (auto *rows : {&s.kind2, &s.kind1}) {
    const auto found = std::find_if(rows->begin(), rows->end(), [&](const auto &v) {
      return v.key == r.key;
    });
    if (found != rows->end()) { existing = *found; break; }
  }
  if (!out.cap_i32) { Reason(out.reason, "uncached_capacity_unavailable"); return false; }
  auto &rows = UncachedGroup(s, r.kind);
  const bool room = static_cast<std::int64_t>(rows.size()) < *out.cap_i32;
  if (existing && existing->priority == 1 && r.priority != 1 &&
      (room || existing->kind == r.kind)) {
    UncachedRemove(s, existing->kind, r.key);
    UncachedAppend(s, r, out);
    return true;
  }
  auto &threshold_priority = r.kind == 2 ? s.priority2 : s.priority1;
  auto &threshold_value = r.kind == 2 ? s.value2 : s.value1;
  if (threshold_priority < r.priority ||
      (threshold_priority == r.priority && threshold_value >= r.value)) return false;
  const auto worst = !room && !rows.empty() ? std::optional(rows.back()) : std::nullopt;
  if (worst && (worst->priority < r.priority ||
      (worst->priority == r.priority && worst->value >= r.value))) {
    if (worst->priority != r.priority || worst->value != r.value || worst->key == r.key)
      return false;
    std::size_t index = 0;
    while (index < rows.size()) {
      if (rows[index].priority == r.priority && rows[index].value == r.value) {
        rows[index] = rows.back();
        rows.pop_back();
      } else ++index;
    }
    UncachedSort(rows);
    threshold_priority = r.priority;
    threshold_value = r.value;
    return false;
  }
  if (existing) {
    if (existing->priority < r.priority ||
        (existing->priority == r.priority && existing->value >= r.value)) return false;
    if (existing->kind == r.kind) {
      const auto found = std::find_if(rows.begin(), rows.end(), [&](const auto &v) {
        return v.key == r.key;
      });
      found->value = r.value;
      found->priority = r.priority;
      UncachedSort(rows);
      return true;
    }
    UncachedRemove(s, existing->kind, r.key);
  }
  if (worst) UncachedRemove(s, r.kind, worst->key);
  UncachedAppend(s, r, out);
  return true;
}

const void *UncachedResolve(const ContextSourceBindingsV1 &b, const void *receiver,
    std::size_t id_offset, const void *storage_slot, const void *fallback_slot,
    std::optional<std::uint32_t> &full_id, std::optional<std::uint32_t> &resolved_id,
    std::optional<bool> &used_fallback, std::string &reason) {
  const auto store = Read<const void *>(b, storage_slot);
  if (!store) { Reason(reason, "uncached_registry_storage_unavailable"); return nullptr; }
  full_id = Read<std::uint32_t>(b, receiver, id_offset);
  if (*store) {
    const auto cap = Read<std::uint32_t>(b, *store, 0x2C);
    if (!full_id || !cap) { Reason(reason, "uncached_registry_operands_unavailable"); return nullptr; }
    const auto index = *full_id & 0xFFFFFFU;
    if (index < *cap) {
      const auto table = Read<const void *>(b, *store, 0x20);
      if (!table || !*table) { Reason(reason, "uncached_registry_table_unavailable"); return nullptr; }
      const auto row = Read<const void *>(b, *table, static_cast<std::size_t>(index) * 16 + 8);
      if (!row) { Reason(reason, "uncached_registry_row_unavailable"); return nullptr; }
      if (*row) {
        const auto id = Read<std::uint32_t>(b, *row, 8);
        if (!id) { Reason(reason, "uncached_registry_candidate_id_unavailable"); return nullptr; }
        if (*id == *full_id) { resolved_id = id; used_fallback = false; return *row; }
      }
    }
  }
  used_fallback = true;
  const auto fallback = Read<const void *>(b, fallback_slot);
  if (!fallback || !*fallback) { Reason(reason, "uncached_native_fallback_unavailable"); return nullptr; }
  resolved_id = Read<std::uint32_t>(b, *fallback, 8);
  return *fallback;
}
void UncachedFamilyRead(const ContextSourceBindingsV1 &b, const void *family,
                        UncachedFamily &out) {
  bool ready = true;
  std::size_t offset = 0;
  for (auto *vector : {&out.first, &out.second}) {
    vector->count = Read<std::int32_t>(b, family, offset + 0xC);
    if (!vector->count || *vector->count < 0) { ready = false; offset = 0x168; continue; }
    vector->records.emplace();
    if (*vector->count > 0) {
      const auto data = Read<const void *>(b, family, offset);
      if (!data || !*data) { ready = false; offset = 0x168; continue; }
      for (std::int32_t i = 0; i < *vector->count; ++i) {
        const auto *record = Offset(*data, static_cast<std::size_t>(i) * 40);
        game::ContextSourceUncachedIntrinsicRecordV1 r{};
        r.native_index = static_cast<std::uint32_t>(i);
        r.marker_u8 = Read<std::uint8_t>(b, record, 0x14);
        r.key_object = Read<std::uint64_t>(b, record, 8);
        r.value_q64 = Read<std::int64_t>(b, record, 0x20);
        if (r.marker_u8 && *r.marker_u8 == 2 && r.key_object)
          r.key_id_i32 = Read<std::int32_t>(b,
              reinterpret_cast<const void *>(static_cast<std::uintptr_t>(*r.key_object)), 0x10);
        if (!r.marker_u8 || !r.value_q64 ||
            (*r.marker_u8 == 2 && (!r.key_object || !r.key_id_i32))) ready = false;
        vector->records->push_back(r);
      }
    }
    offset = 0x168;
  }
  out.ready = ready;
}
std::vector<UncachedRecord> UncachedPairs(const UncachedFamily &family, UncachedInputs &out) {
  if (!family.ready) { Reason(out.reason, "uncached_intrinsic_family_unavailable"); return {}; }
  std::vector<UncachedRecord> raw;
  std::uint32_t kind = 1;
  for (const auto *vector : {&family.first, &family.second}) {
    if (vector->records) for (const auto &r : *vector->records) {
      const auto key = *r.marker_u8 == 2 ? r.key_object : out.fallback_key_object;
      const auto id = *r.marker_u8 == 2 ? r.key_id_i32 : out.fallback_key_id_i32;
      if (!key || !id) { Reason(out.reason, "uncached_effective_trait_key_unavailable"); continue; }
      raw.push_back({*key, *id, *r.value_q64, 0, kind});
    }
    ++kind;
  }
  auto keys = raw;
  std::stable_sort(keys.begin(), keys.end(), [](const auto &a, const auto &b) { return a.id < b.id; });
  keys.erase(std::unique(keys.begin(), keys.end(), [](const auto &a, const auto &b) {
    return a.key == b.key;
  }), keys.end());
  for (auto &key : keys) {
    key.kind = 0;
    key.value = 0;
    for (const auto &r : raw) if (r.key == key.key && r.value > key.value) {
      key.kind = r.kind;
      key.value = r.value;
    }
  }
  return keys;
}
void UncachedObjectsRead(const ContextSourceBindingsV1 &b, const void *associated,
    std::size_t offset, std::size_t family_offset,
    game::ContextSourceUncachedObjectVectorV1 &out) {
  out.count = Read<std::int32_t>(b, associated, offset + 0xC);
  if (!out.count || *out.count < 0) return;
  out.entries.emplace();
  if (*out.count == 0) return;
  const auto data = Read<const void *>(b, associated, offset);
  if (!data || !*data) return;
  for (std::int32_t i = 0; i < *out.count; ++i) {
    game::ContextSourceUncachedObjectV1 r{};
    r.native_index = static_cast<std::uint32_t>(i);
    r.object = Read<std::uint64_t>(b, *data, static_cast<std::size_t>(i) * 8);
    if (r.object && *r.object) {
      const auto *object = reinterpret_cast<const void *>(static_cast<std::uintptr_t>(*r.object));
      r.magic_u32 = Read<std::uint32_t>(b, object, 0x38);
      UncachedFamilyRead(b, Offset(object, family_offset), r.intrinsic_family);
    }
    out.entries->push_back(std::move(r));
  }
}
void UncachedContextRead(const ContextSourceBindingsV1 &b, const void *associated,
                         game::ContextSourceUncachedContextVectorV1 &out) {
  out.count = Read<std::int32_t>(b, associated, 0x794);
  if (!out.count || *out.count < 0) return;
  out.entries.emplace();
  if (*out.count == 0) return;
  const auto data = Read<const void *>(b, associated, 0x788);
  if (!data || !*data) return;
  for (std::int32_t i = 0; i < *out.count; ++i) {
    const auto *row = Offset(*data, static_cast<std::size_t>(i) * 16);
    out.entries->push_back({static_cast<std::uint32_t>(i),
                           Read<std::uint64_t>(b, row), Read<std::uint8_t>(b, row, 8)});
  }
}

UncachedInputs UncachedRecipientInputs(const ContextSourceBindingsV1 &b,
                                      const void *character, std::int32_t id) {
  UncachedInputs out{};
  out.character_id = id;
  const auto carrier = Read<const void *>(b, character, 0x1C8);
  if (!carrier) { out.reason = "uncached_carrier_pointer_unavailable"; return out; }
  out.carrier_present = *carrier != nullptr;
  if (*carrier) { out.status = "not_applicable"; out.ready = true; return out; }
  auto &down = out.downstream_inputs;
  const auto *associated = AbsentAssociated(b, character, down);
  out.associated_full_id = down.associated_full_id;
  out.associated_resolved_full_id = down.associated_resolved_full_id;
  out.associated_used_fallback = down.associated_used_fallback;
  if (!associated) { out.reason = down.reason; return out; }
  out.associated_cache_440 = Read<std::uint32_t>(b, associated, 0x440);
  if (!out.associated_cache_440) { out.reason = "uncached_cache_440_unavailable"; return out; }
  if (*out.associated_cache_440 != 0) { out.status = "not_applicable"; out.ready = true; return out; }
  const auto &bind = b.uncached_recipient;
  auto &seed = out.seed_receiver;
  const auto *first = UncachedResolve(b, associated, 0x4B8, bind.first_registry_slot,
      bind.first_fallback_slot, seed.first_full_id, seed.first_resolved_full_id,
      seed.first_used_fallback, out.reason);
  if (!first) return out;
  const auto *second = UncachedResolve(b, first, 0x8C, bind.second_registry_slot,
      bind.second_fallback_slot, seed.second_full_id, seed.second_resolved_full_id,
      seed.second_used_fallback, out.reason);
  if (!second) return out;
  seed.definition_object = Read<std::uint64_t>(b, second, 0x20);
  if (!seed.definition_object || !*seed.definition_object) {
    out.reason = "uncached_seed_definition_pointer_unavailable";
    return out;
  }
  UncachedFamilyRead(b, Offset(reinterpret_cast<const void *>(
      static_cast<std::uintptr_t>(*seed.definition_object)), 0x648), out.seed_family);
  out.fallback_key_object = Read<std::uint64_t>(b, bind.fallback_key_slot);
  if (out.fallback_key_object && *out.fallback_key_object)
    out.fallback_key_id_i32 = Read<std::int32_t>(b, reinterpret_cast<const void *>(
        static_cast<std::uintptr_t>(*out.fallback_key_object)), 0x10);
  UncachedObjectsRead(b, associated, 0x770, 0xF70, out.active_objects);
  UncachedObjectsRead(b, associated, 0x7A0, 0x728, out.removed_objects);
  UncachedContextRead(b, associated, out.active_context);
  out.cap_i32 = Read<std::int32_t>(b, bind.cap_slot);
  out.active_flag4_multiplier_q64 = Read<std::int64_t>(b, bind.active_flag4_multiplier_slot);
  out.active_other_multiplier_q64 = Read<std::int64_t>(b, bind.active_other_multiplier_slot);
  out.seed_boost_multiplier_q64 = Read<std::int64_t>(b, bind.seed_boost_multiplier_slot);
  out.positive_fallback_object = Read<std::uint64_t>(b, bind.positive_fallback_slot);
  out.negative_fallback_object = Read<std::uint64_t>(b, bind.negative_fallback_slot);
  if (out.positive_fallback_object && *out.positive_fallback_object)
    out.positive_fallback_magic_u32 = Read<std::uint32_t>(b, reinterpret_cast<const void *>(
        static_cast<std::uintptr_t>(*out.positive_fallback_object)), 0x38);
  if (out.negative_fallback_object && *out.negative_fallback_object)
    out.negative_fallback_magic_u32 = Read<std::uint32_t>(b, reinterpret_cast<const void *>(
        static_cast<std::uintptr_t>(*out.negative_fallback_object)), 0x38);

  UncachedState state{};
  std::vector<std::pair<std::uint64_t, std::uint64_t>> positive, negative;
  const auto assign = [](auto &values, std::uint64_t key, std::uint64_t value) {
    const auto found = std::find_if(values.begin(), values.end(), [key](const auto &v) {
      return v.first == key;
    });
    if (found == values.end()) values.emplace_back(key, value);
    else found->second = value;
  };
  for (auto r : UncachedPairs(out.seed_family, out)) {
    r.priority = 1;
    UncachedOffer(state, r, out);
  }
  for (const auto *vector : {&out.active_objects, &out.removed_objects}) {
    const bool active = vector == &out.active_objects;
    if (!vector->count || *vector->count < 0 || !vector->entries ||
        vector->entries->size() != static_cast<std::size_t>(*vector->count)) {
      Reason(out.reason, "uncached_object_vector_unavailable");
      continue;
    }
    for (const auto &object : *vector->entries) {
      if (!object.object) { Reason(out.reason, "uncached_object_pointer_unavailable"); continue; }
      auto pairs = UncachedPairs(object.intrinsic_family, out);
      if (pairs.empty()) continue;
      std::uint8_t priority = 2;
      std::optional<std::int64_t> multiplier;
      if (active) {
        const auto &context = out.active_context;
        if (!context.count || *context.count < 0 || !context.entries ||
            context.entries->size() != static_cast<std::size_t>(*context.count)) {
          Reason(out.reason, "uncached_active_context_unavailable");
          continue;
        }
        const game::ContextSourceUncachedContextRecordV1 *selected = nullptr;
        for (const auto &r : *context.entries) {
          if (!r.object) { Reason(out.reason, "uncached_context_object_unavailable"); break; }
          if (r.object == object.object) { selected = &r; break; }
        }
        if (!selected) continue;
        if (!selected->flag_u8) { Reason(out.reason, "uncached_context_flag_unavailable"); continue; }
        priority = *selected->flag_u8 == 4 ? 0 : 3;
        multiplier = *selected->flag_u8 == 4 ? out.active_flag4_multiplier_q64
                                            : out.active_other_multiplier_q64;
        if (!multiplier) { Reason(out.reason, "uncached_active_multiplier_unavailable"); continue; }
      }
      for (auto r : pairs) {
        r.priority = priority;
        if (active) r.value = UncachedFixedMul(r.value, *multiplier);
        if (UncachedOffer(state, r, out)) assign(active ? positive : negative, r.key, *object.object);
      }
    }
  }
  std::vector<UncachedRecord> materialized;
  for (const auto *rows : {&state.kind2, &state.kind1}) for (const auto &r : *rows) {
    const auto prior = std::find_if(materialized.begin(), materialized.end(), [&](const auto &v) {
      return v.key == r.key;
    });
    if (prior == materialized.end()) materialized.push_back(r);
    else *prior = r;
  }
  const auto link = [&](const auto &table, std::uint64_t key, bool positive_link) {
    std::pair<std::optional<std::uint64_t>, std::optional<std::uint32_t>> result;
    const auto found = std::find_if(table.begin(), table.end(), [key](const auto &v) { return v.first == key; });
    if (found == table.end()) {
      result.first = positive_link ? out.positive_fallback_object : out.negative_fallback_object;
      result.second = positive_link ? out.positive_fallback_magic_u32 : out.negative_fallback_magic_u32;
    } else {
      result.first = found->second;
      for (const auto *vector : {&out.active_objects, &out.removed_objects})
        if (vector->entries) for (const auto &r : *vector->entries)
          if (r.object == result.first) result.second = r.magic_u32;
    }
    return result;
  };
  if (!materialized.empty()) AbsentTraits(b, character, down);
  bool membership_attempted = false;
  std::int64_t total = 0;
  for (const auto &r : materialized) {
    auto p = link(positive, r.key, true);
    if (!p.first || !p.second) Reason(out.reason, "uncached_positive_link_operands_unavailable");
    bool positive_valid = p.second && *p.second == 0x4744624FU;
    if (positive_valid) {
      const auto n = link(negative, r.key, false);
      if (!n.first || !n.second) Reason(out.reason, "uncached_negative_link_operands_unavailable");
      if (n.second && *n.second == 0x4744624FU && r.priority == 2) {
        p = {out.positive_fallback_object, out.positive_fallback_magic_u32};
        if (!p.first || !p.second) Reason(out.reason, "uncached_conflict_fallback_unavailable");
        positive_valid = p.second && *p.second == 0x4744624FU;
      }
    }
    if (!down.trait_ids.values_u32) continue;
    if (std::find(down.trait_ids.values_u32->begin(), down.trait_ids.values_u32->end(),
                  static_cast<std::uint32_t>(r.id)) == down.trait_ids.values_u32->end()) continue;
    auto value = r.kind == 2 ? AbsentSigned(0ULL - static_cast<std::uint64_t>(r.value)) : r.value;
    if (!membership_attempted) { AbsentMembershipHeader(b, down); membership_attempted = true; }
    if (down.membership_ids.count && *down.membership_ids.count > 0 &&
        down.membership_header_guard_raw && *down.membership_header_guard_raw != 0 &&
        *down.membership_header_guard_raw != -1 && positive_valid && p.first && *p.first != 0) {
      AbsentMembershipValues(b, down);
      if (down.membership_ids.values_u64 && std::find(down.membership_ids.values_u64->begin(),
          down.membership_ids.values_u64->end(), *p.first) != down.membership_ids.values_u64->end()) {
        if (!down.member_multiplier_q64)
          down.member_multiplier_q64 = Read<std::int64_t>(b, b.absent_recipient.member_multiplier_slot);
        if (!down.member_multiplier_q64) Reason(down.reason, "uncached_member_multiplier_unavailable");
        else value = AbsentFixedMul(value, *down.member_multiplier_q64);
      }
    }
    total = AbsentAdd(total, value);
  }
  const auto aggregate = AbsentAggregate(b, character, down);
  down.clamp_lower_q64 = Read<std::int64_t>(b, b.absent_recipient.clamp_lower_slot);
  down.clamp_upper_q64 = Read<std::int64_t>(b, b.absent_recipient.clamp_upper_slot);
  if (!down.clamp_lower_q64 || !down.clamp_upper_q64)
    Reason(down.reason, "uncached_clamp_operands_unavailable");
  if (!down.reason.empty()) Reason(out.reason, down.reason.c_str());
  if (out.reason.empty() && aggregate && down.clamp_lower_q64 && down.clamp_upper_q64) {
    total = AbsentAdd(total, *aggregate);
    out.calculated_recipient_q64 = total < *down.clamp_lower_q64 ? *down.clamp_lower_q64
        : std::min(total, *down.clamp_upper_q64);
    out.ready = true;
    out.status = "available";
  }
  return out;
}
