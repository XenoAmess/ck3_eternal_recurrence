// Included inside the current-person source collector's anonymous namespace.
// Cached absent-1C8 receiver: raw reads and local integer arithmetic only.
using AbsentInputs = game::ContextSourceAbsentRecipientInputsV1;

std::int64_t AbsentSigned(std::uint64_t value) noexcept {
  std::int64_t out{};
  std::memcpy(&out, &value, sizeof(out));
  return out;
}
std::int64_t AbsentAdd(std::int64_t a, std::int64_t b) noexcept {
  return AbsentSigned(static_cast<std::uint64_t>(a) + static_cast<std::uint64_t>(b));
}
std::int64_t AbsentMul(std::int64_t a, std::int64_t b) noexcept {
  return AbsentSigned(static_cast<std::uint64_t>(a) * static_cast<std::uint64_t>(b));
}
std::int64_t AbsentFixedMul(std::int64_t a, std::int64_t b) noexcept {
  constexpr std::int64_t bound = 3037000499LL;
  constexpr std::int64_t q = 100000;
  if (a >= -bound && a <= bound && b >= -bound && b <= bound)
    return AbsentMul(a, b) / q;
  const auto lo = std::min(a, b);
  const auto hi = std::max(a, b);
  const auto quotient = lo / q;
  const auto remainder = AbsentAdd(lo, -AbsentMul(quotient, q));
  return AbsentAdd(AbsentMul(quotient, hi), AbsentMul(remainder, hi) / q);
}
const void *AbsentAssociated(const ContextSourceBindingsV1 &b,
                            const void *character, AbsentInputs &out) {
  const auto &bindings = b.absent_recipient;
  const auto store = Read<const void *>(b, bindings.associated_storage_slot);
  if (!store) { out.reason = "absent_associated_storage_slot_unavailable"; return nullptr; }
  if (*store) {
    out.associated_full_id = Read<std::uint32_t>(b, character, 0xB4);
    const auto capacity = Read<std::uint32_t>(b, *store, 0x2C);
    if (!out.associated_full_id || !capacity) {
      out.reason = "absent_associated_registry_operands_unavailable";
      return nullptr;
    }
    const auto index = *out.associated_full_id & 0xFFFFFFU;
    if (index < *capacity) {
      const auto table = Read<const void *>(b, *store, 0x20);
      if (!table) { out.reason = "absent_associated_table_unavailable"; return nullptr; }
      const auto candidate = Read<const void *>(b, *table,
          static_cast<std::size_t>(index) * 16 + 8);
      if (!candidate) { out.reason = "absent_associated_slot_unavailable"; return nullptr; }
      if (*candidate) {
        const auto full = Read<std::uint32_t>(b, *candidate, 8);
        if (!full) { out.reason = "absent_associated_candidate_id_unavailable"; return nullptr; }
        if (*full == *out.associated_full_id) {
          out.associated_resolved_full_id = full;
          out.associated_used_fallback = false;
          return *candidate;
        }
      }
    }
  }
  const auto fallback = Read<const void *>(b, bindings.associated_fallback_slot);
  out.associated_used_fallback = true;
  if (!fallback || !*fallback) {
    out.reason = "absent_associated_native_fallback_unavailable";
    return nullptr;
  }
  out.associated_resolved_full_id = Read<std::uint32_t>(b, *fallback, 8);
  return *fallback;
}

template <typename Entry>
void AbsentMap(const ContextSourceBindingsV1 &b, const void *header,
               game::ContextSourceAbsentMapV1<Entry> &out, std::string &reason) {
  out.count = Read<std::int32_t>(b, header, 0x10);
  if (!out.count) { Reason(reason, "absent_map_count_unavailable"); return; }
  out.entries.emplace();
  // The cached copier consumes no buckets for a nonpositive occupied count.
  if (*out.count <= 0) return;
  out.mask = Read<std::int32_t>(b, header, 0x14);
  out.max_probe_u8 = Read<std::uint8_t>(b, header, 0x18);
  const auto data = Read<const void *>(b, header, 8);
  if (!data || !*data) { Reason(reason, "absent_map_bucket_pointer_unavailable"); return; }
  for (std::uint32_t index = 0;
       out.entries->size() < static_cast<std::size_t>(*out.count); ++index) {
    const auto *bucket = Offset(*data, static_cast<std::size_t>(index) * 24);
    const auto probe = Read<std::uint8_t>(b, bucket, 4);
    if (!probe) { Reason(reason, "absent_map_probe_unavailable"); return; }
    if (*probe == 0) continue;
    if (*probe == 0xFFU) { Reason(reason, "absent_map_end_before_occupied_count"); return; }
    Entry entry{};
    entry.bucket_index = index;
    entry.probe_u8 = probe;
    entry.hash_u32 = Read<std::uint32_t>(b, bucket);
    entry.key_object = Read<std::uint64_t>(b, bucket, 8);
    if constexpr (requires { entry.value_q64; }) {
      entry.value_q64 = Read<std::int64_t>(b, bucket, 0x10);
      if (entry.key_object)
        entry.trait_id_u32 = Read<std::uint32_t>(b,
            reinterpret_cast<const void *>(static_cast<std::uintptr_t>(*entry.key_object)), 0x10);
      if (!entry.key_object || !entry.trait_id_u32 || !entry.value_q64)
        Reason(reason, "absent_map430_entry_operands_unavailable");
    } else {
      entry.value_u64 = Read<std::uint64_t>(b, bucket, 0x10);
      if (!entry.key_object || !entry.value_u64)
        Reason(reason, "absent_map458_entry_operands_unavailable");
    }
    out.entries->push_back(std::move(entry));
  }
}

void AbsentTraits(const ContextSourceBindingsV1 &b, const void *character,
                  AbsentInputs &out) {
  auto &traits = out.trait_ids;
  traits.count = Read<std::int32_t>(b, character, 0x104);
  if (!traits.count) { Reason(out.reason, "absent_trait_count_unavailable"); return; }
  if (*traits.count < 0) { Reason(out.reason, "absent_trait_negative_count"); return; }
  if (*traits.count == 0) { traits.values_u32.emplace(); return; }
  const auto data = Read<const void *>(b, character, 0xF8);
  traits.values_u32 = Vector<std::uint32_t>(b, data.value_or(nullptr), traits.count);
  if (!traits.values_u32) Reason(out.reason, "absent_trait_values_unavailable");
}
void AbsentMembershipHeader(const ContextSourceBindingsV1 &b, AbsentInputs &out) {
  const auto &bindings = b.absent_recipient;
  out.membership_header_guard_raw = Read<std::int32_t>(b, bindings.membership_guard_slot);
  out.membership_ids.count = Read<std::int32_t>(b, bindings.membership_inline_header, 0xC);
  if (!out.membership_header_guard_raw)
    Reason(out.reason, "absent_membership_guard_unavailable");
  else if (*out.membership_header_guard_raw == 0 || *out.membership_header_guard_raw == -1)
    Reason(out.reason, "absent_membership_header_not_initialized");
  if (!out.membership_ids.count) Reason(out.reason, "absent_membership_count_unavailable");
  else if (*out.membership_ids.count < 0) Reason(out.reason, "absent_membership_negative_count");
  else if (*out.membership_ids.count == 0) out.membership_ids.values_u64.emplace();
}
void AbsentMembershipValues(const ContextSourceBindingsV1 &b, AbsentInputs &out) {
  if (out.membership_ids.values_u64) return;
  const auto data = Read<const void *>(b, b.absent_recipient.membership_inline_header);
  out.membership_ids.values_u64 = Vector<std::uint64_t>(
      b, data.value_or(nullptr), out.membership_ids.count);
  if (!out.membership_ids.values_u64) Reason(out.reason, "absent_membership_values_unavailable");
}

const void *AbsentAggregateContext(const ContextSourceBindingsV1 &b,
                                  const void *character, AbsentInputs &out) {
  const auto scratch = Read<const void *>(b, character, 0x1B0);
  if (!scratch) { Reason(out.reason, "absent_aggregate_scratch_pointer_unavailable"); return nullptr; }
  if (*scratch) {
    const auto model = Read<const void *>(b, *scratch, 0x258);
    if (!model) { Reason(out.reason, "absent_aggregate_model_pointer_unavailable"); return nullptr; }
    if (*model) {
      const auto owner = Read<const void *>(b, *model, 8);
      if (!owner) { Reason(out.reason, "absent_aggregate_model_owner_unavailable"); return nullptr; }
      if (*owner == character) {
        out.aggregate_context_selection = "owned_model_10";
        return Offset(*model, 0x10);
      }
    }
  }
  out.aggregate_context_selection = "inline_context_5d67b90";
  out.aggregate_context_guard_raw = Read<std::int32_t>(b, b.absent_recipient.aggregate_guard_slot);
  if (!out.aggregate_context_guard_raw)
    Reason(out.reason, "absent_aggregate_context_guard_unavailable");
  else if (*out.aggregate_context_guard_raw == 0 || *out.aggregate_context_guard_raw == -1)
    Reason(out.reason, "absent_aggregate_context_not_initialized");
  return b.absent_recipient.aggregate_inline_context;
}
std::optional<std::int64_t> AbsentAggregate(const ContextSourceBindingsV1 &b,
                                          const void *character, AbsentInputs &out) {
  const auto *context = AbsentAggregateContext(b, character, out);
  if (!context) return std::nullopt;
  auto &aggregate = out.aggregate_properties;
  aggregate.count = Read<std::int32_t>(b, context, 0x74);
  if (!aggregate.count) { Reason(out.reason, "absent_aggregate_count_unavailable"); return std::nullopt; }
  if (*aggregate.count < 0) { Reason(out.reason, "absent_aggregate_negative_count"); return std::nullopt; }
  if (*aggregate.count == 0) {
    aggregate.keys_u16.emplace();
    aggregate.values_q64.emplace();
    return 0;
  }
  const auto keys = Read<const void *>(b, context, 0x68);
  aggregate.keys_u16 = Vector<std::uint16_t>(b, keys.value_or(nullptr), aggregate.count);
  if (!aggregate.keys_u16) { Reason(out.reason, "absent_aggregate_keys_unavailable"); return std::nullopt; }
  // The native lower_bound uses the actual array order, without sorting.
  std::int32_t offset = 0;
  std::int32_t remaining = *aggregate.count;
  while (remaining > 0) {
    const auto half = remaining >> 1;
    const auto index = offset + half;
    if (aggregate.keys_u16->at(static_cast<std::size_t>(index)) < 0x25D)
      offset += remaining - half;
    remaining = half;
  }
  if (offset == *aggregate.count ||
      aggregate.keys_u16->at(static_cast<std::size_t>(offset)) > 0x25D) return 0;
  const auto values = Read<const void *>(b, context, 0xD0);
  aggregate.values_q64 = Vector<std::int64_t>(b, values.value_or(nullptr), aggregate.count);
  if (!aggregate.values_q64) { Reason(out.reason, "absent_aggregate_values_unavailable"); return std::nullopt; }
  return aggregate.values_q64->at(static_cast<std::size_t>(offset));
}

AbsentInputs AbsentRecipientInputs(const ContextSourceBindingsV1 &b,
                                  const void *character, std::int32_t id) {
  AbsentInputs out{};
  out.character_id = id;
  const auto carrier = Read<const void *>(b, character, 0x1C8);
  if (!carrier) { out.reason = "absent_carrier_pointer_unavailable"; return out; }
  out.carrier_present = *carrier != nullptr;
  if (*carrier) {
    out.ready = true;
    out.status = "not_applicable";
    return out;
  }
  const auto *associated = AbsentAssociated(b, character, out);
  if (!associated) return out;
  out.associated_cache_440 = Read<std::uint32_t>(b, associated, 0x440);
  if (!out.associated_cache_440) { out.reason = "absent_associated_cache_440_unavailable"; return out; }
  if (*out.associated_cache_440 == 0) {
    out.reason = "absent_uncached_2bfa420_derived_input_families_unavailable";
    return out;
  }
  AbsentMap(b, Offset(associated, 0x430), out.cached_map_430, out.reason);
  if (out.cached_map_430.count && *out.cached_map_430.count > 0)
    AbsentTraits(b, character, out);
  bool map458_attempted = false;
  bool membership_attempted = false;
  std::vector<std::pair<std::uint64_t, std::int64_t>> assigned;
  if (out.cached_map_430.entries && out.trait_ids.values_u32) {
    for (const auto &entry : *out.cached_map_430.entries) {
      if (!entry.key_object || !entry.trait_id_u32 || !entry.value_q64) continue;
      if (std::find(out.trait_ids.values_u32->begin(), out.trait_ids.values_u32->end(),
                    *entry.trait_id_u32) == out.trait_ids.values_u32->end()) continue;
      auto value = *entry.value_q64;
      if (!membership_attempted) {
        AbsentMembershipHeader(b, out);
        membership_attempted = true;
      }
      if (out.membership_ids.count && *out.membership_ids.count > 0 &&
          out.membership_header_guard_raw && *out.membership_header_guard_raw != 0 &&
          *out.membership_header_guard_raw != -1) {
        if (!map458_attempted) {
          AbsentMap(b, Offset(associated, 0x458), out.cached_map_458, out.reason);
          map458_attempted = true;
        }
        if (out.cached_map_458.entries) {
          const auto linked = std::find_if(out.cached_map_458.entries->begin(),
              out.cached_map_458.entries->end(), [&](const auto &row) {
                return row.key_object == entry.key_object;
              });
          if (linked != out.cached_map_458.entries->end() && linked->value_u64 &&
              *linked->value_u64 != 0) {
            AbsentMembershipValues(b, out);
            if (out.membership_ids.values_u64 &&
                std::find(out.membership_ids.values_u64->begin(), out.membership_ids.values_u64->end(),
                          *linked->value_u64) != out.membership_ids.values_u64->end()) {
              if (!out.member_multiplier_q64)
                out.member_multiplier_q64 = Read<std::int64_t>(b, b.absent_recipient.member_multiplier_slot);
              if (!out.member_multiplier_q64) Reason(out.reason, "absent_member_multiplier_unavailable");
              else value = AbsentFixedMul(value, *out.member_multiplier_q64);
            }
          }
        }
      }
      const auto prior = std::find_if(assigned.begin(), assigned.end(), [&](const auto &row) {
        return row.first == *entry.key_object;
      });
      if (prior == assigned.end()) assigned.emplace_back(*entry.key_object, value);
      else prior->second = value; // Native 2BFFE10 replaces, rather than adds.
    }
  }
  const auto aggregate = AbsentAggregate(b, character, out);
  out.clamp_lower_q64 = Read<std::int64_t>(b, b.absent_recipient.clamp_lower_slot);
  out.clamp_upper_q64 = Read<std::int64_t>(b, b.absent_recipient.clamp_upper_slot);
  if (!out.clamp_lower_q64 || !out.clamp_upper_q64)
    Reason(out.reason, "absent_clamp_slots_unavailable");
  if (out.reason.empty() && aggregate && out.clamp_lower_q64 && out.clamp_upper_q64) {
    auto total = *aggregate;
    for (const auto &row : assigned) total = AbsentAdd(total, row.second);
    out.calculated_recipient_q64 = total < *out.clamp_lower_q64 ? *out.clamp_lower_q64
        : std::min(total, *out.clamp_upper_q64);
    out.ready = true;
    out.status = "available";
  }
  return out;
}
