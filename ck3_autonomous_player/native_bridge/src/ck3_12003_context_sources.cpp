#include "xar_bridge/ck3_12003_context_sources.hpp"
#include "xar_bridge/ck3_12003.hpp"

#include <algorithm>
#include <cstring>
#include <utility>

namespace xar::ck3_12002 {
namespace {

const void *Offset(const void *p, std::size_t offset) noexcept {
  return p ? static_cast<const std::byte *>(p) + offset : nullptr;
}
bool Copy(const ContextSourceBindingsV1 &b, const void *p, void *out,
          std::size_t bytes) noexcept {
  if (!p) return false;
  if (b.read_memory) return b.read_memory(b.read_context, p, out, bytes);
  std::memcpy(out, p, bytes);
  return true;
}
template <typename T>
std::optional<T> Read(const ContextSourceBindingsV1 &b, const void *p,
                      std::size_t offset = 0) noexcept {
  T out{};
  if (!Copy(b, Offset(p, offset), &out, sizeof(out))) return std::nullopt;
  return out;
}
void Reason(std::string &target, const char *reason) {
  if (target.empty()) target = reason;
}

template <typename T>
std::optional<std::vector<T>> Vector(const ContextSourceBindingsV1 &b,
                                    const void *data,
                                    const std::optional<std::int32_t> &count) {
  if (!count) return std::nullopt;
  if (*count <= 0) return std::vector<T>{};
  if (!data) return std::nullopt;
  std::vector<T> out(static_cast<std::size_t>(*count));
  if (!Copy(b, data, out.data(), out.size() * sizeof(T))) return std::nullopt;
  return out;
}
game::ContextSourcePropertiesV1 Properties(const ContextSourceBindingsV1 &b,
                                           const void *container) {
  game::ContextSourcePropertiesV1 out{};
  if (!container) {
    out.reason = "property_container_unavailable";
    return out;
  }
  out.keys_count = Read<std::int32_t>(b, container, 0xC);
  // Exact zero +C returns before any value header, pointer or element read.
  if (out.keys_count && *out.keys_count == 0) {
    out.keys_u16.emplace();
    out.values_q64.emplace();
    return out;
  }
  if (!out.keys_count || *out.keys_count < 0) {
    out.reason = out.keys_count ? "property_negative_key_count"
                                : "property_key_count_unavailable";
    return out;
  }
  // +74 is independent provenance; consumed values use the key count +C.
  out.values_count = Read<std::int32_t>(b, container, 0x74);
  const auto keys = Read<const void *>(b, container);
  const auto values = Read<const void *>(b, container, 0x68);
  out.keys_u16 = Vector<std::uint16_t>(b, keys.value_or(nullptr), out.keys_count);
  out.values_q64 = Vector<std::int64_t>(b, values.value_or(nullptr), out.keys_count);
  if (!out.keys_u16 || !out.values_q64)
    out.reason = "property_consumed_reads_unavailable";
  return out;
}
bool PropertiesReady(const game::ContextSourcePropertiesV1 &p) {
  if (!p.keys_count || *p.keys_count < 0) return false;
  if (*p.keys_count == 0) return true;
  return p.keys_u16.has_value() && p.values_q64.has_value() &&
      p.keys_u16->size() == static_cast<std::size_t>(*p.keys_count) &&
      p.values_q64->size() == static_cast<std::size_t>(*p.keys_count);
}

// Mirrors the caller's exact lookup demand order. Failed observations never
// take a native fallback; a readable native miss does. Raw IDs stay DWORDs.
const void *PreRegistry(const ContextSourceBindingsV1 &b,
                        const void *storage_slot, const void *fallback_slot,
                        const void *key_address,
                        std::optional<std::int32_t> &key_raw,
                        std::optional<std::string> &selection,
                        std::string &reason) {
  const auto store = Read<const void *>(b, storage_slot);
  if (!store) { reason = "registry_store_read_unavailable"; return nullptr; }
  if (*store) {
    key_raw = Read<std::int32_t>(b, key_address);
    if (!key_raw) { reason = "registry_key_read_unavailable"; return nullptr; }
    const auto index = static_cast<std::uint32_t>(*key_raw) & 0xFFFFFFU;
    const auto capacity = Read<std::uint32_t>(b, *store, 0x2C);
    if (!capacity) { reason = "registry_capacity_read_unavailable"; return nullptr; }
    if (index < *capacity) {
      const auto table = Read<const void *>(b, *store, 0x20);
      if (!table) { reason = "registry_table_read_unavailable"; return nullptr; }
      const auto object = Read<const void *>(b, *table,
          static_cast<std::size_t>(index) * 16 + 8);
      if (!object) { reason = "registry_slot_read_unavailable"; return nullptr; }
      if (*object) {
        const auto full_id = Read<std::int32_t>(b, *object, 0x10);
        if (!full_id) { reason = "registry_full_id_read_unavailable"; return nullptr; }
        if (*full_id == *key_raw) {
          selection = "registry_full_id";
          return *object;
        }
      }
    }
  }
  const auto fallback = Read<const void *>(b, fallback_slot);
  if (!fallback) { reason = "registry_fallback_read_unavailable"; return nullptr; }
  selection = "native_fallback";
  if (!*fallback) reason = "registry_native_fallback_null";
  return *fallback;
}

game::ContextSourcePre291e2101640V1 Pre291e2101640(
    const ContextSourceBindingsV1 &b, const void *character,
    std::int32_t character_id) {
  game::ContextSourcePre291e2101640V1 out{};
  out.character_id = character_id;
  out.status = "partial";
  const auto fail = [&](const char *reason) {
    out.unavailable_reason = reason;
    return out;
  };
  const auto link = Read<const void *>(b, character, 0x1B8);
  if (!link) return fail("character_carrier_1b8_read_unavailable");
  const void *army = nullptr;
  if (*link) {
    army = PreRegistry(b, b.army_internal_storage_slot,
                       b.army_internal_fallback_slot, Offset(*link, 0xF4),
                       out.army_key_f4_raw, out.army_selection,
                       out.unavailable_reason);
  } else {
    const auto fallback = Read<const void *>(b, b.army_internal_fallback_slot);
    if (!fallback) return fail("army_native_fallback_read_unavailable");
    out.army_selection = "native_fallback";
    army = *fallback;
    if (!army) return fail("army_native_fallback_null");
  }
  if (!army) return out;
  out.army_field_120_raw = Read<std::int32_t>(b, army, 0x120);
  if (!out.army_field_120_raw) return fail("army_field_120_read_unavailable");
  if (*out.army_field_120_raw == -1) {
    out.admitted = false;
  } else {
    const void *second = PreRegistry(
        b, b.pre_291e210_second_storage_slot,
        b.pre_291e210_second_fallback_slot, Offset(army, 0x124),
        out.army_field_124_raw, out.second_selection, out.unavailable_reason);
    if (!second) return out;
    out.second_field_174_raw = Read<std::int32_t>(b, second, 0x174);
    if (!out.second_field_174_raw) return fail("second_field_174_read_unavailable");
    out.admitted = *out.army_field_120_raw == *out.second_field_174_raw;
  }
  if (*out.admitted) {
    // The closed 8FD4E0 getter and actual provider+1640 Def+40 are demanded
    // only after AL=true; this never calls 24DFB70 or a context writer.
    const void *provider = b.provider ? b.provider() : nullptr;
    if (!provider) return fail("provider_unavailable");
    const auto definition = Read<const void *>(b, provider, 0x1640);
    if (!definition || !*definition) return fail("provider_1640_definition_unavailable");
    out.property_block = Properties(b, Offset(*definition, 0x40));
    if (!PropertiesReady(*out.property_block))
      return fail("provider_1640_consumed_properties_unavailable");
  }
  out.ready = true;
  out.status = "available";
  return out;
}

template <typename T> T PostReady(T out) {
  out.ready = true;
  out.status = "available";
  return out;
}
template <typename T> T PostPartial(T out, const char *reason) {
  out.status = "partial";
  out.unavailable_reason = reason;
  return out;
}

game::ContextSourcePostGuarded630V1 PostGuarded630(
    const ContextSourceBindingsV1 &b, const void *character) {
  game::ContextSourcePostGuarded630V1 out{};
  const auto carrier = Read<const void *>(b, character, 0x1B0);
  if (!carrier) return PostPartial(out, "carrier_1b0_read_unavailable");
  out.carrier_1b0_present = *carrier != nullptr;
  const void *selected = nullptr;
  if (*carrier) {
    const auto carrier280 = Read<const void *>(b, *carrier, 0x280);
    if (!carrier280) return PostPartial(out, "carrier280_read_unavailable");
    out.carrier280_present = *carrier280 != nullptr;
    if (*carrier280) {
      out.selection = "carrier280_qword8";
      const auto object = Read<const void *>(b, *carrier280, 8);
      if (!object) return PostPartial(out, "carrier280_selected_object_read_unavailable");
      selected = *object;
    }
  }
  if (!*carrier || out.carrier280_present == false) {
    out.selection = "native_fallback5D1E308";
    const auto fallback = Read<const void *>(b, b.post_ab_object_fallback_slot);
    if (!fallback) return PostPartial(out, "guarded630_fallback_read_unavailable");
    selected = *fallback;
  }
  // A null selected object is a demanded read failure, never a skipped guard.
  out.selected_field38_raw = Read<std::int32_t>(b, selected, 0x38);
  if (!out.selected_field38_raw)
    return PostPartial(out, "selected_field38_read_unavailable");
  if (*out.selected_field38_raw != 0x4744624F) {
    out.admitted = false;
    return PostReady(out);
  }
  out.character68_signed = Read<std::int16_t>(b, character, 0x68);
  if (!out.character68_signed) return PostPartial(out, "character68_read_unavailable");
  out.threshold_signed = Read<std::int32_t>(b, b.post_ab_signed_character_threshold_slot);
  if (!out.threshold_signed) return PostPartial(out, "threshold_read_unavailable");
  out.admitted = static_cast<std::int32_t>(*out.character68_signed) >= *out.threshold_signed;
  if (!*out.admitted) return PostReady(out);
  out.property_block = Properties(b, Offset(selected, 0x630));
  if (!PropertiesReady(*out.property_block))
    return PostPartial(out, "guarded630_consumed_properties_unavailable");
  return PostReady(out);
}

game::ContextSourcePostCarrier40V1 PostCarrier40(
    const ContextSourceBindingsV1 &b, const void *character) {
  game::ContextSourcePostCarrier40V1 out{};
  // This family has its own current carrier observation. No preceding writer
  // is executed, and no changed-stage identity is inferred from this query.
  const auto carrier = Read<const void *>(b, character, 0x1B0);
  if (!carrier) return PostPartial(out, "carrier_1b0_read_unavailable");
  out.carrier_1b0_present = *carrier != nullptr;
  if (!*carrier) {
    out.admitted = false;
    return PostReady(out);
  }
  const auto carrier288 = Read<const void *>(b, *carrier, 0x288);
  if (!carrier288) return PostPartial(out, "carrier288_read_unavailable");
  out.carrier288_present = *carrier288 != nullptr;
  out.admitted = *carrier288 != nullptr;
  if (!*out.admitted) return PostReady(out);
  const auto selected = Read<const void *>(b, *carrier288, 0x18);
  if (!selected) return PostPartial(out, "carrier288_selected_object_read_unavailable");
  out.property_block = Properties(b, Offset(*selected, 0x40));
  if (!PropertiesReady(*out.property_block))
    return PostPartial(out, "carrier40_consumed_properties_unavailable");
  return PostReady(out);
}

game::ContextSourcePostOrderedD8V1 PostOrderedD8(
    const ContextSourceBindingsV1 &b, const void *character) {
  game::ContextSourcePostOrderedD8V1 out{};
  const auto carrier = Read<const void *>(b, character, 0x1C0);
  if (!carrier) return PostPartial(out, "carrier_1c0_read_unavailable");
  out.carrier_1c0_present = *carrier != nullptr;
  out.header_selection = *carrier ? "carrier_1c0_plus200" : "inline_static54E7270";
  const void *header = *carrier ? Offset(*carrier, 0x200)
                               : b.post_ab_static_inline_source_list_header;
  // 28B6200 selects an INLINE header, not a pointer stored in the static slot.
  // Native caller reads pointer0 before countC, including on an empty list.
  const auto data = Read<const void *>(b, header);
  if (!data) return PostPartial(out, "ordered_d8_array_pointer_read_unavailable");
  out.source_array_present = *data != nullptr;
  out.source_count_raw = Read<std::int32_t>(b, header, 0xC);
  if (!out.source_count_raw) return PostPartial(out, "ordered_d8_count_read_unavailable");
  if (*out.source_count_raw < 0) return PostPartial(out, "ordered_d8_negative_count");
  if (*out.source_count_raw == 0) {
    out.occurrences.emplace();
    return PostReady(out);
  }
  if (!*data) return PostPartial(out, "ordered_d8_native_array_null");
  out.occurrences.emplace();
  std::vector<const void *> identities;
  bool complete = true;
  for (std::int32_t i = 0; i < *out.source_count_raw; ++i) {
    game::ContextSourcePostD8OccurrenceV1 row{};
    row.source_index = i;
    const auto source = Read<const void *>(b, *data, static_cast<std::size_t>(i) * 8);
    if (!source || !*source) {
      row.unavailable_reason = source ? "ordered_d8_native_source_null"
                                      : "ordered_d8_source_pointer_read_unavailable";
      complete = false;
    } else {
      auto found = std::find(identities.begin(), identities.end(), *source);
      if (found == identities.end()) {
        identities.push_back(*source);
        found = identities.end() - 1;
      }
      row.source_identity = "post" + std::to_string(found - identities.begin());
      row.property_block = Properties(b, Offset(*source, 0xD8));
      if (!PropertiesReady(*row.property_block)) {
        row.unavailable_reason = "ordered_d8_consumed_properties_unavailable";
        complete = false;
      }
    }
    out.occurrences->push_back(std::move(row));
  }
  return complete ? PostReady(out) : PostPartial(out, "ordered_d8_occurrences_partial");
}

game::ContextSourcePost291d7e0V1 Post291d7e0(
    const ContextSourceBindingsV1 &b, const void *character,
    std::int32_t character_id) {
  game::ContextSourcePost291d7e0V1 out{};
  out.character_id = character_id;
  out.guarded630 = PostGuarded630(b, character);
  out.carrier40 = PostCarrier40(b, character);
  out.ordered_d8 = PostOrderedD8(b, character);
  return out.guarded630.ready && out.carrier40.ready && out.ordered_d8.ready
      ? PostReady(out) : PostPartial(out, "post_291d7e0_sources_partial");
}

struct Resolved {
  game::ContextSourceResolutionV1 observation;
  const void *object = nullptr;
};
Resolved Resolve(const ContextSourceBindingsV1 &b, const void *storage_slot,
                 const void *fallback_slot, std::optional<std::uint32_t> id) {
  Resolved out{};
  out.observation.requested_full_id = id;
  if (!id) {
    out.observation.reason = "relation_id_unavailable";
    return out;
  }
  const auto store = Read<const void *>(b, storage_slot);
  if (!store) {
    out.observation.reason = "relation_store_read_unavailable";
    return out;
  }
  const char *fallback_reason = "store_null";
  if (*store) {
    const auto capacity = Read<std::uint32_t>(b, *store, 0x2C);
    const auto table = Read<const void *>(b, *store, 0x20);
    if (!capacity || !table) {
      out.observation.reason = "relation_storage_fields_unavailable";
      return out;
    }
    const auto index = *id & 0xFFFFFFU;
    fallback_reason = "index_outside_capacity";
    if (index < *capacity) {
      const auto object = Read<const void *>(b, *table,
                                           static_cast<std::size_t>(index) * 16 + 8);
      if (!object) {
        out.observation.reason = "relation_slot_read_unavailable";
        return out;
      }
      fallback_reason = "object_null";
      if (*object) {
        const auto full_id = Read<std::uint32_t>(b, *object, 0x10);
        if (!full_id) {
          out.observation.reason = "relation_generation_read_unavailable";
          return out;
        }
        fallback_reason = "full_id_mismatch";
        if (*full_id == *id) {
          out.object = *object;
          out.observation.status = "resolved";
          out.observation.selected_full_id = full_id;
          return out;
        }
      }
    }
  }
  out.observation.status = "native_fallback";
  out.observation.reason = fallback_reason;
  const auto fallback = Read<const void *>(b, fallback_slot);
  if (!fallback) {
    out.observation.status = "unavailable";
    out.observation.reason = "relation_fallback_read_unavailable";
    return out;
  }
  out.object = *fallback;
  if (out.object)
    out.observation.selected_full_id = Read<std::uint32_t>(b, out.object, 0x10);
  else
    out.observation.reason = "relation_native_fallback_null";
  return out;
}

struct Definitions {
  std::vector<const void *> pointers;
  std::vector<game::ContextSourceDefinitionBlockV1> blocks;
};
std::string Definition(const ContextSourceBindingsV1 &b, const void *pointer,
                       Definitions &definitions) {
  const auto found = std::find(definitions.pointers.begin(),
                               definitions.pointers.end(), pointer);
  if (found != definitions.pointers.end())
    return definitions.blocks[static_cast<std::size_t>(
        found - definitions.pointers.begin())].definition_identity;
  std::string identity = "d" + std::to_string(definitions.pointers.size());
  definitions.pointers.push_back(pointer);
  game::ContextSourceDefinitionBlockV1 block{};
  block.definition_identity = identity;
  block.properties = Properties(b, Offset(pointer, 0x40));
  definitions.blocks.push_back(std::move(block));
  return identity;
}
game::ContextSourceWeightedSpanV1 Span(const ContextSourceBindingsV1 &b,
                                      const void *header, const char *source,
                                      Definitions &definitions) {
  game::ContextSourceWeightedSpanV1 out{};
  out.selected_source = source;
  if (!header) {
    out.reason = "selected_source_header_unavailable";
    return out;
  }
  out.count = Read<std::int32_t>(b, header, 0xC);
  if (!out.count) {
    out.reason = "selected_source_count_unavailable";
    return out;
  }
  if (*out.count <= 0) {
    out.rows.emplace();
    return out;
  }
  const auto data = Read<const void *>(b, header);
  if (!data || !*data) {
    out.reason = "selected_source_rows_unavailable";
    return out;
  }
  out.rows.emplace();
  out.rows->reserve(static_cast<std::size_t>(*out.count));
  for (std::int32_t i = 0; i < *out.count; ++i) {
    const auto row = Offset(*data, static_cast<std::size_t>(i) * 0x48);
    game::ContextSourceWeightedRowV1 copied{};
    copied.native_index = i;
    const auto definition = Read<const void *>(b, row);
    if (definition && *definition)
      copied.definition_identity = Definition(b, *definition, definitions);
    else
      Reason(out.reason, "selected_source_definition_unavailable");
    copied.weight_q64 = Read<std::int64_t>(b, row, 0x30);
    if (!copied.weight_q64) Reason(out.reason, "selected_source_weight_unavailable");
    out.rows->push_back(std::move(copied));
  }
  return out;
}
bool SpanReady(const std::optional<game::ContextSourceWeightedSpanV1> &span) {
  if (!span || !span->count || !span->rows) return false;
  for (const auto &row : *span->rows)
    if (!row.definition_identity || !row.weight_q64) return false;
  return true;
}

game::ContextSource291e210V1 BranchA(const ContextSourceBindingsV1 &b,
                                    const void *character) {
  game::ContextSource291e210V1 out{};
  Definitions definitions{};
  const auto carrier = Read<const void *>(b, character, 0x1B0);
  if (carrier) {
    out.component_present = *carrier != nullptr;
    out.selected_lifestyle_span = Span(b,
        *carrier ? Offset(*carrier, 0x188) : b.lifestyle_fallback_header,
        *carrier ? "component+188" : "static+54E7288", definitions);
  } else Reason(out.reason, "component_pointer_unavailable");
  const auto first_id = Read<std::uint32_t>(b, character, 0x158);
  auto first = Resolve(b, b.first_storage_slot, b.first_fallback_slot, first_id);
  out.first_relation_resolution = first.observation;
  const auto second_id = Read<std::uint32_t>(b, first.object, 0x2C);
  auto second = Resolve(b, b.second_storage_slot, b.second_fallback_slot, second_id);
  out.second_relation_resolution = second.observation;
  out.selected_dynasty_span = Span(b, Offset(second.object, 0x140),
                                   "second_relation+140", definitions);
  // The native branch re-resolves the first full ID for its third/fourth calls.
  auto house = Resolve(b, b.first_storage_slot, b.first_fallback_slot,
                       Read<std::uint32_t>(b, character, 0x158));
  out.house_resolution = house.observation;
  out.selected_house_span = Span(b, Offset(house.object, 0x168),
                                 "first_relation+168", definitions);
  const auto extra_gate = Read<std::uint8_t>(b, house.object, 0x218);
  if (extra_gate) {
    out.house_extra_enabled = *extra_gate != 0;
    out.selected_house_extra_span = Span(b,
        *out.house_extra_enabled ? Offset(house.object, 0x200)
                                : b.house_extra_fallback_header,
        *out.house_extra_enabled ? "first_relation+200" : "static+54E56B0",
        definitions);
  } else Reason(out.reason, "house_extra_gate_unavailable");
  out.definition_blocks = std::move(definitions.blocks);
  out.ready = out.component_present.has_value() &&
      out.house_extra_enabled.has_value() &&
      SpanReady(out.selected_lifestyle_span) && SpanReady(out.selected_dynasty_span) &&
      SpanReady(out.selected_house_span) && SpanReady(out.selected_house_extra_span);
  for (const auto &block : out.definition_blocks)
    out.ready = out.ready && block.properties && PropertiesReady(*block.properties);
  out.status = out.ready ? "available" : "partial";
  if (!out.ready) Reason(out.reason, "branch_291e210_source_reads_unavailable");
  return out;
}

// Branch B copies two independent native arrays. The A append empty-block
// shortcut must not suppress a nonempty B value array when B keys are empty.
game::ContextSourcePropertiesV1 BaseProperties(const ContextSourceBindingsV1 &b,
                                               const void *source) {
  game::ContextSourcePropertiesV1 out{};
  out.keys_count = Read<std::int32_t>(b, source, 0x28C);
  out.values_count = Read<std::int32_t>(b, source, 0x2F4);
  if (out.keys_count && *out.keys_count >= 0) {
    const auto data = *out.keys_count == 0 ? std::optional<const void *>{nullptr}
                                         : Read<const void *>(b, source, 0x280);
    out.keys_u16 = Vector<std::uint16_t>(b, data.value_or(nullptr), out.keys_count);
  }
  if (out.values_count && *out.values_count >= 0) {
    const auto data = *out.values_count == 0 ? std::optional<const void *>{nullptr}
                                           : Read<const void *>(b, source, 0x2E8);
    out.values_q64 = Vector<std::int64_t>(b, data.value_or(nullptr), out.values_count);
  }
  if (!out.keys_u16 || !out.values_q64) out.reason = "base_copy_reads_unavailable";
  return out;
}
bool BasePropertiesReady(const game::ContextSourcePropertiesV1 &p) {
  return p.keys_count && *p.keys_count >= 0 && p.values_count &&
      *p.values_count >= 0 && p.keys_u16 && p.values_q64;
}
std::string Identity(std::vector<const void *> &pointers, const void *p,
                     const char *prefix) {
  const auto found = std::find(pointers.begin(), pointers.end(), p);
  const auto index = found == pointers.end() ? pointers.size()
      : static_cast<std::size_t>(found - pointers.begin());
  if (found == pointers.end()) pointers.push_back(p);
  return prefix + std::to_string(index);
}

template <typename Row, typename Copier>
std::optional<std::vector<Row>> ConditionalRows(
    const ContextSourceBindingsV1 &b, const void *source, std::size_t data_offset,
    std::size_t stride, const std::optional<std::int32_t> &count, Copier copy) {
  if (!count) return std::nullopt;
  if (*count <= 0) return std::vector<Row>{};
  const auto data = Read<const void *>(b, source, data_offset);
  if (!data || !*data) return std::nullopt;
  std::vector<Row> rows;
  rows.reserve(static_cast<std::size_t>(*count));
  for (std::int32_t i = 0; i < *count; ++i)
    rows.push_back(copy(Offset(*data, static_cast<std::size_t>(i) * stride), i));
  return rows;
}

struct ConditionState {
  bool registry_sampled = false;
  bool fallback_sampled = false;
  bool manager_sampled = false;
  bool government_sampled = false;
  std::optional<const void *> token_manager;
  std::vector<const void *> identities;
};
void Condition(const ContextSourceBindingsV1 &b, const void *character,
               game::ContextSource291d7e0V1 &branch, ConditionState &state,
               game::ContextSourceConditionalCV1 &row) {
  row.token_origin = "unavailable";
  if (!state.registry_sampled) {
    state.registry_sampled = true;
    branch.condition_registry_guard = Read<std::int32_t>(b, b.condition_registry_guard);
  }
  if (!row.source_key_u32) {
    row.reason = "condition_source_key_unavailable";
    return;
  }
  const auto index = *row.source_key_u32 & 0xFFFFFFU;
  row.masked_index_u32 = index;
  const auto count = Read<std::int32_t>(b, b.condition_registry, 0x3C);
  row.resolver_count_i32 = count;
  if (!count) {
    row.reason = "condition_registry_count_unavailable";
    return;
  }
  const bool from_registry = static_cast<std::int32_t>(index) < *count;
  row.selected_native_fallback = !from_registry;
  if (!from_registry && !state.fallback_sampled) {
    state.fallback_sampled = true;
    branch.condition_fallback_guard = Read<std::int32_t>(b, b.condition_fallback_guard);
  }
  const auto data = from_registry ? Read<const void *>(b, b.condition_registry, 0x30)
                                 : std::optional<const void *>{nullptr};
  const void *object = from_registry
      ? Offset(data.value_or(nullptr), static_cast<std::size_t>(index) * 0x20)
      : b.condition_fallback_object;
  row.condition_source = from_registry ? "registry+30/index" : "static+5DC1368";
  const auto guard = from_registry ? branch.condition_registry_guard
                                  : branch.condition_fallback_guard;
  const bool registry_prepared = branch.condition_registry_guard &&
      *branch.condition_registry_guard != 0 && *branch.condition_registry_guard != -1;
  const bool selected_prepared = guard && *guard != 0 && *guard != -1;
  if (object && registry_prepared && selected_prepared)
    row.resolved_condition_identity = Identity(state.identities, object, "c");
  row.condition_length = Read<std::int32_t>(b, object, 0x10);
  row.condition_capacity = Read<std::uint64_t>(b, object, 0x18);
  if (!row.condition_length || !row.condition_capacity || *row.condition_length < 0) {
    row.reason = "condition_string_shape_unavailable";
    return;
  }
  const auto bytes = *row.condition_capacity < 16
      ? std::optional<const void *>{object} : Read<const void *>(b, object);
  row.condition_bytes = Vector<std::uint8_t>(b, bytes.value_or(nullptr),
                                             row.condition_length);
  if (row.condition_bytes && !row.condition_bytes->empty())
    row.first_signed_byte = static_cast<std::int32_t>(
        static_cast<std::int8_t>(row.condition_bytes->front()));
  if (!registry_prepared || !selected_prepared) {
    row.reason = guard && branch.condition_registry_guard
        ? (*guard == -1 || *branch.condition_registry_guard == -1
            ? "condition_object_initialization_in_progress"
            : "condition_object_would_initialize")
        : "condition_object_guard_unavailable";
    return;
  }
  if (!row.condition_bytes) {
    row.reason = "condition_string_bytes_unavailable";
    return;
  }
  if (*row.condition_length != 0 && row.condition_bytes->front() == 0x2D) {
    row.condition_token_id = 0;
    row.token_origin = "native_early_zero_hyphen";
  } else {
    if (*row.condition_length != 0) {
      const auto locale = Read<std::int32_t>(b, b.prefix_classifier_locale_flag);
      row.classifier_mode_i32 = locale;
      if (!locale) {
        row.reason = "classifier_locale_flag_unavailable";
        return;
      }
      const auto first = *row.first_signed_byte;
      std::uint16_t classification = 0;
      if (*locale != 0) {
        auto locale_bindings = b.current_locale;
        locale_bindings.read_memory = b.read_memory;
        locale_bindings.read_context = b.read_context;
        row.locale_classification = ReadContextSourceLocaleClassification12003(
            locale_bindings, first);
        if (!row.locale_classification->ready ||
            !row.locale_classification->result_i32) {
          row.reason = row.locale_classification->reason;
          return;
        }
        classification = static_cast<std::uint16_t>(
            *row.locale_classification->result_i32);
      } else if (static_cast<std::uint32_t>(first + 1) <= 0x100U) {
        const auto table = Read<const void *>(b, b.prefix_classifier_table_slot);
        const void *element = table && *table
            ? static_cast<const std::byte *>(*table) + first * 2 : nullptr;
        const auto observed = Read<std::uint16_t>(b, element);
        if (!observed) {
          row.reason = "classifier_table_element_unavailable";
          return;
        }
        classification = static_cast<std::uint16_t>(*observed & 4U);
      }
      if (classification != 0) {
        row.condition_token_id = 0;
        row.token_origin = "native_early_zero_classifier";
      }
      row.classifier_result_i32 = classification;
    }
    if (!row.condition_token_id) {
      if (!state.manager_sampled) {
        state.manager_sampled = true;
        state.token_manager = Read<const void *>(b, b.token_manager_slot);
        if (state.token_manager)
          branch.token_manager_present = *state.token_manager != nullptr;
      }
      row.lookup_status = "unavailable";
      if (!state.token_manager || !*state.token_manager) {
        row.reason = "token_manager_absent";
        return;
      }
      if (!b.existing_token_lookup) {
        row.reason = "existing_token_lookup_unbound";
        return;
      }
      const ContextSourceTokenSliceV1 slice{
          reinterpret_cast<const char *>(row.condition_bytes->data()),
          *row.condition_length, 0, {}};
      ContextSourceTokenCursorV1 cursor{};
      b.existing_token_lookup(const_cast<void *>(Offset(*state.token_manager, 8)),
                              &cursor, &slice);
      row.token_origin = "existing_token_lookup";
      const auto marker = Read<std::uint8_t>(b, cursor.node, 4);
      if (!marker) {
        row.reason = "existing_token_lookup_node_unavailable";
        return;
      }
      if (*marker == 0xFF) {
        row.lookup_status = "miss";
        row.reason = "token_not_currently_interned_would_intern";
        return;
      }
      row.condition_token_id = Read<std::int32_t>(b, cursor.node, 0x28);
      if (!row.condition_token_id) {
        row.reason = "existing_token_lookup_value_unavailable";
        return;
      }
      row.token_origin = "existing_token_lookup";
      row.lookup_status = "found";
    }
  }
  if (!state.government_sampled) {
    state.government_sampled = true;
    if (b.government) {
      const auto *government = b.government(const_cast<void *>(character));
      branch.government_source = "28C2E10";
      if (government) {
        branch.government_token_count = Read<std::int32_t>(b, government, 0x5C);
        const auto government_data = Read<const void *>(b, government, 0x50);
        branch.government_token_ids_i32 = Vector<std::int32_t>(
            b, government_data.value_or(nullptr), branch.government_token_count);
      }
    }
  }
  if (!row.invert_u8 || !branch.government_token_count ||
      !branch.government_token_ids_i32) {
    row.reason = "conditional_c_membership_inputs_unavailable";
    return;
  }
  const auto &tokens = *branch.government_token_ids_i32;
  const bool member = std::binary_search(tokens.begin(), tokens.end(),
                                          *row.condition_token_id);
  row.admitted = member != (*row.invert_u8 != 0);
}

// V86: readonly selector resolution and conditional A/B consumers. Registry
// objects stay opaque; these field recipes come from the frozen caller/leaves.
Resolved SelectorResolve(const ContextSourceBindingsV1 &b,
                         const std::optional<const void *> &store,
                         const std::optional<std::uint32_t> &id,
                         const std::optional<const void *> &fallback,
                         std::size_t generation_offset) {
  Resolved out{};
  out.observation.requested_full_id = id;
  if (!store) {
    out.observation.reason = "selector_store_unavailable";
    return out;
  }
  const char *miss = "store_null";
  if (*store) {
    if (!id) {
      out.observation.reason = "selector_requested_id_unavailable";
      return out;
    }
    const auto capacity = Read<std::uint32_t>(b, *store, 0x2C);
    if (!capacity) {
      out.observation.reason = "selector_capacity_unavailable";
      return out;
    }
    const auto slot_index = *id & 0xFFFFFFU;
    miss = "index_outside_capacity";
    if (slot_index < *capacity) {
      const auto slots = Read<const void *>(b, *store, 0x20);
      if (!slots || !*slots) {
        out.observation.reason = "selector_slots_unavailable";
        return out;
      }
      const auto candidate = Read<const void *>(
          b, *slots, static_cast<std::size_t>(slot_index) * 16 + 8);
      if (!candidate) {
        out.observation.reason = "selector_slot_unavailable";
        return out;
      }
      miss = "object_null";
      if (*candidate) {
        const auto generation = Read<std::uint32_t>(
            b, *candidate, generation_offset);
        if (!generation) {
          out.observation.reason = "selector_generation_unavailable";
          return out;
        }
        miss = "full_id_mismatch";
        if (*generation == *id) {
          out.object = *candidate;
          out.observation.status = "resolved";
          out.observation.selected_full_id = generation;
          return out;
        }
      }
    }
  }
  if (!fallback) {
    out.observation.reason = "selector_fallback_slot_unavailable";
    return out;
  }
  out.object = *fallback;
  out.observation.status = "native_fallback";
  out.observation.reason = miss;
  if (out.object)
    out.observation.selected_full_id = Read<std::uint32_t>(
        b, out.object, generation_offset);
  else
    out.observation.reason = "selector_native_fallback_null";
  return out;
}

struct SelectorState {
  bool a_sampled = false;
  bool b_sampled = false;
  bool b_nested_sampled = false;
  std::optional<std::vector<const void *>> a_keys;
  const void *b_object = nullptr;
  std::optional<const void *> b_nested_data;
};

void SelectorA(const ContextSourceBindingsV1 &b, const void *character,
               game::ContextSource291d7e0V1 &branch, SelectorState &state,
               std::vector<const void *> &keys) {
  if (state.a_sampled) return;
  state.a_sampled = true;
  // R8 and R14 are loaded once and retained through all three stages.
  const auto first_store = Read<const void *>(b, b.selector_a_storage_slot);
  const auto initial_fallback = Read<const void *>(
      b, b.selector_a_initial_fallback_slot);
  const auto first_id = first_store && *first_store
      ? Read<std::uint32_t>(b, character, 0xB4) : std::nullopt;
  const auto first = SelectorResolve(b, first_store, first_id,
                                     initial_fallback, 8);
  branch.selector_a_stage1 = first.observation;
  if (!first.object) return;
  const auto second_id = Read<std::uint32_t>(b, first.object, 0x4B8);
  if (!second_id) return;
  const auto second_store = Read<const void *>(b, b.selector_a_second_storage_slot);
  const auto second = SelectorResolve(
      b, second_store, second_id,
      Read<const void *>(b, b.selector_a_second_fallback_slot), 8);
  branch.selector_a_stage2 = second.observation;
  // A null initial store bypasses the selected stage2+98 read altogether.
  if (!first_store) return;
  const auto third_id = *first_store
      ? Read<std::uint32_t>(b, second.object, 0x98) : std::nullopt;
  const auto third = SelectorResolve(b, first_store, third_id,
                                     initial_fallback, 8);
  branch.selector_a_stage3 = third.observation;
  if (third.observation.status == "resolved")
    branch.selector_a_selected_source = "stage3_resolved";
  else if (third.observation.status == "native_fallback")
    branch.selector_a_selected_source = "initial_fallback5C67670";
  if (!third.object) return;
  branch.selector_a_key_count = Read<std::int32_t>(b, third.object, 0x7AC);
  if (!branch.selector_a_key_count || *branch.selector_a_key_count < 0) return;
  if (*branch.selector_a_key_count == 0) state.a_keys.emplace();
  else {
    const auto key_data = Read<const void *>(b, third.object, 0x7A0);
    state.a_keys = Vector<const void *>(
        b, key_data.value_or(nullptr), branch.selector_a_key_count);
  }
  if (state.a_keys) {
    branch.selector_a_key_identities.emplace();
    for (const auto *key_pointer : *state.a_keys)
      branch.selector_a_key_identities->push_back(Identity(keys, key_pointer, "k"));
  }
}

game::ContextSourceSignedKeySetV1 SignedKeys(const ContextSourceBindingsV1 &b,
                                          const void *owner,
                                          std::size_t data_offset,
                                          std::size_t count_offset,
                                          std::int32_t native_index) {
  game::ContextSourceSignedKeySetV1 out{};
  out.native_index = native_index;
  out.count = Read<std::int32_t>(b, owner, count_offset);
  if (!out.count || *out.count < 0) {
    out.reason = out.count ? "selector_negative_key_count"
                          : "selector_key_count_unavailable";
    return out;
  }
  if (*out.count == 0) out.keys_i32.emplace();
  else {
    const auto key_data = Read<const void *>(b, owner, data_offset);
    out.keys_i32 = Vector<std::int32_t>(b, key_data.value_or(nullptr), out.count);
    if (!out.keys_i32) out.reason = "selector_key_data_unavailable";
  }
  return out;
}
std::optional<bool> SignedMember(const game::ContextSourceSignedKeySetV1 &set,
                                 std::int32_t key) {
  if (!set.count || *set.count < 0 || !set.keys_i32) return std::nullopt;
  const auto found = std::lower_bound(set.keys_i32->begin(), set.keys_i32->end(), key);
  // Exact native completion test; actual native arrays retain their signed order.
  return found != set.keys_i32->end() && key >= *found;
}
void SelectorB(const ContextSourceBindingsV1 &b, const void *character,
               game::ContextSource291d7e0V1 &branch, SelectorState &state) {
  if (state.b_sampled) return;
  state.b_sampled = true;
  const auto requested = Read<std::uint32_t>(b, character, 0xB0);
  if (!requested) return;
  const auto selected = SelectorResolve(
      b, Read<const void *>(b, b.selector_b_storage_slot), requested,
      Read<const void *>(b, b.selector_b_fallback_slot), 0x10);
  branch.selector_b_resolution = selected.observation;
  state.b_object = selected.object;
  const auto owner = Read<const void *>(b, selected.object, 0x20);
  const auto header = owner ? Read<const void *>(b, *owner, 0x128) : std::nullopt;
  if (header && *header)
    branch.selector_b_primary_keys = SignedKeys(b, *header, 8, 0x14, -1);
}
void ConditionalB(const ContextSourceBindingsV1 &b, const void *character,
                  game::ContextSource291d7e0V1 &branch, SelectorState &state,
                  game::ContextSourceConditionalBV1 &row) {
  SelectorB(b, character, branch, state);
  if (!row.key_i32 || !branch.selector_b_primary_keys) {
    row.reason = "conditional_b_primary_inputs_unavailable";
    return;
  }
  const auto primary = SignedMember(*branch.selector_b_primary_keys, *row.key_i32);
  if (!primary) {
    row.reason = "conditional_b_primary_inputs_unavailable";
    return;
  }
  if (*primary) {
    row.admitted = true;
    row.admission_source = "primary";
    return;
  }
  if (!state.b_nested_sampled) {
    state.b_nested_sampled = true;
    branch.selector_b_nested_count = Read<std::int32_t>(b, state.b_object, 0x524);
    if (branch.selector_b_nested_count && *branch.selector_b_nested_count >= 0) {
      branch.selector_b_nested_keys.emplace();
      if (*branch.selector_b_nested_count > 0)
        state.b_nested_data = Read<const void *>(b, state.b_object, 0x518);
    }
  }
  if (!branch.selector_b_nested_count || *branch.selector_b_nested_count < 0 ||
      !branch.selector_b_nested_keys) {
    row.reason = "conditional_b_nested_count_unavailable";
    return;
  }
  for (std::int32_t i = 0; i < *branch.selector_b_nested_count; ++i) {
    const auto ordinal = static_cast<std::size_t>(i);
    if (ordinal == branch.selector_b_nested_keys->size()) {
      const auto object = state.b_nested_data
          ? Read<const void *>(b, *state.b_nested_data, ordinal * 8) : std::nullopt;
      branch.selector_b_nested_keys->push_back(SignedKeys(
          b, object.value_or(nullptr), 0x1010, 0x101C, i));
    }
    const auto member = SignedMember((*branch.selector_b_nested_keys)[ordinal],
                                      *row.key_i32);
    if (!member) {
      row.reason = "conditional_b_nested_inputs_unavailable";
      return;
    }
    if (*member) {
      row.admitted = true;
      row.admission_source = "nested";
      row.admission_nested_native_index = i;
      return;
    }
  }
  row.admitted = false;
  row.admission_source = "absent";
}

void ConditionalA(const ContextSourceBindingsV1 &b, const void *character,
                  const void *source, const std::optional<std::int32_t> &count,
                  const std::optional<const void *> &key,
                  game::ContextSource291d7e0V1 &branch, SelectorState &state,
                  std::vector<const void *> &keys,
                  game::ContextSourceConditionalAV1 &row) {
  SelectorA(b, character, branch, state, keys);
  if (!state.a_keys) {
    row.reason = "conditional_a_selector_inputs_unavailable";
    return;
  }
  if (state.a_keys->empty()) {
    row.admitted = false;
    return;
  }
  if (!key) {
    row.reason = "conditional_a_key_unavailable";
    return;
  }
  row.admitted = std::find(state.a_keys->begin(), state.a_keys->end(), *key)
      != state.a_keys->end();
  if (!*row.admitted) return;
  row.key_object_magic = Read<std::uint32_t>(b, *key, 0x38);
  if (!row.key_object_magic) {
    row.reason = "conditional_a_magic_unavailable";
    return;
  }
  const void *selected_property = nullptr;
  if (*row.key_object_magic == 0x4744624FU) {
    row.key_object_id = Read<std::uint32_t>(b, *key, 0x10);
    if (!row.key_object_id || !count || *count < 0) {
      row.reason = "conditional_a_full_id_scan_inputs_unavailable";
      return;
    }
    const auto source_rows = *count > 0 ? Read<const void *>(b, source, 0x550)
                                       : std::optional<const void *>{nullptr};
    if (!source_rows || (*count > 0 && !*source_rows)) {
      row.reason = "conditional_a_full_id_scan_rows_unavailable";
      return;
    }
    for (std::int32_t i = 0; i < *count; ++i) {
      const auto candidate_row = Offset(*source_rows,
                                         static_cast<std::size_t>(i) * 0x30);
      const auto candidate_key = Read<const void *>(b, candidate_row, 0x20);
      const auto candidate_id = candidate_key
          ? Read<std::uint32_t>(b, *candidate_key, 0x10) : std::nullopt;
      if (!candidate_id) {
        row.reason = "conditional_a_scan_candidate_id_unavailable";
        return;
      }
      if (*candidate_id == *row.key_object_id) {
        const auto property = Read<const void *>(b, candidate_row, 0x28);
        if (!property || !*property) {
          row.reason = "conditional_a_first_id_property_unavailable";
          return;
        }
        selected_property = *property;
        row.property_source = "first_full_id_match";
        row.property_source_native_index = i;
        break;
      }
    }
  }
  if (!selected_property) {
    row.property_source = "static5DC21B0";
    if (!branch.conditional_a_fallback_properties && b.conditional_a_fallback_properties)
      branch.conditional_a_fallback_properties = Properties(
          b, b.conditional_a_fallback_properties);
    row.property_block = branch.conditional_a_fallback_properties;
    if (!row.property_block) row.reason = "conditional_a_fallback_property_unavailable";
    return;
  }
  row.property_block = Properties(b, selected_property);
}


game::ContextSource291d7e0V1 BranchB(const ContextSourceBindingsV1 &b,
                                    const void *character) {
  game::ContextSource291d7e0V1 out{};
  std::vector<const void *> sources, keys, retained;
  ConditionState conditions{};
  SelectorState selectors{};
  const auto carrier = Read<const void *>(b, character, 0x1B0);
  const void *header = nullptr;
  if (carrier) {
    out.component_present = *carrier != nullptr;
    header = *carrier ? Offset(*carrier, 0x220) : b.source_fallback_header;
    out.selected_source = *carrier ? "component+220" : "static+54E78B8";
  } else Reason(out.reason, "component_pointer_unavailable");
  out.source_count = Read<std::int32_t>(b, header, 0xC);
  if (out.source_count && *out.source_count <= 0) out.source_rows.emplace();
  else if (out.source_count) {
    const auto data = Read<const void *>(b, header);
    if (data && *data) {
      out.source_rows.emplace();
      out.source_rows->reserve(static_cast<std::size_t>(*out.source_count));
      for (std::int32_t i = 0; i < *out.source_count; ++i) {
        game::ContextSourceSourceRowV1 row{};
        row.native_index = i;
        const auto source = Read<const void *>(b, *data,
                                              static_cast<std::size_t>(i) * 8);
        if (!source || !*source) {
          row.reason = source ? "native_source_null" : "source_pointer_unavailable";
          out.source_rows->push_back(std::move(row));
          continue;
        }
        row.source_identity = Identity(sources, *source, "s");
        row.base_properties = BaseProperties(b, *source);
        // +410 has no sealed width/semantic copy recipe; do not fabricate it.
        const auto auxiliary = Read<const void *>(b, *source, 0x430);
        if (auxiliary) row.auxiliary_retained_present = *auxiliary != nullptr;
        if (auxiliary && *auxiliary)
          row.auxiliary_retained_identity = Identity(retained, *auxiliary, "r");
        row.auxiliary_tag_u32 = Read<std::uint32_t>(b, *source, 0x438);
        row.conditional_a_count = Read<std::int32_t>(b, *source, 0x55C);
        row.conditional_b_count = Read<std::int32_t>(b, *source, 0x574);
        row.conditional_c_count = Read<std::int32_t>(b, *source, 0x58C);
        row.conditional_a_rows = ConditionalRows<game::ContextSourceConditionalAV1>(
            b, *source, 0x550, 0x30, row.conditional_a_count,
            [&](const void *native, std::int32_t index) {
              game::ContextSourceConditionalAV1 copied{};
              copied.native_index = index;
              const auto key = Read<const void *>(b, native, 0x20);
              if (key) {
                copied.key_identity = Identity(keys, *key, "k");
              }
              ConditionalA(b, character, *source, row.conditional_a_count, key,
                           out, selectors, keys, copied);
              return copied;
            });
        row.conditional_b_rows = ConditionalRows<game::ContextSourceConditionalBV1>(
            b, *source, 0x568, 0x1C8, row.conditional_b_count,
            [&](const void *native, std::int32_t index) {
              game::ContextSourceConditionalBV1 copied{};
              copied.native_index = index;
              copied.key_i32 = Read<std::int32_t>(b, native);
              copied.property_block = Properties(b, Offset(native, 8));
              ConditionalB(b, character, out, selectors, copied);
              return copied;
            });
        row.conditional_c_rows = ConditionalRows<game::ContextSourceConditionalCV1>(
            b, *source, 0x580, 0x1D0, row.conditional_c_count,
            [&](const void *native, std::int32_t index) {
              game::ContextSourceConditionalCV1 copied{};
              copied.native_index = index;
              copied.source_key_u32 = Read<std::uint32_t>(b, native);
              copied.invert_u8 = Read<std::uint8_t>(b, native, 0x1C8);
              copied.property_block = Properties(b, Offset(native, 8));
              Condition(b, character, out, conditions, copied);
              return copied;
            });
        out.source_rows->push_back(std::move(row));
      }
    }
  }
  out.base_inputs_ready = out.component_present.has_value() &&
      out.source_count.has_value() && out.source_rows.has_value();
  bool conditionals_complete = out.base_inputs_ready;
  if (out.source_rows) {
    for (const auto &row : *out.source_rows) {
      out.base_inputs_ready = out.base_inputs_ready && row.base_properties &&
          BasePropertiesReady(*row.base_properties);
      conditionals_complete = conditionals_complete && row.conditional_a_rows &&
          row.conditional_b_rows && row.conditional_c_rows;
      const auto admitted_ready = [](const auto &conditional) {
        return conditional.admitted.has_value() &&
            (!*conditional.admitted || (conditional.property_block &&
             PropertiesReady(*conditional.property_block)));
      };
      if (row.conditional_a_rows)
        for (const auto &conditional : *row.conditional_a_rows)
          conditionals_complete = conditionals_complete && admitted_ready(conditional);
      if (row.conditional_b_rows)
        for (const auto &conditional : *row.conditional_b_rows)
          conditionals_complete = conditionals_complete && admitted_ready(conditional);
      if (row.conditional_c_rows)
        for (const auto &conditional : *row.conditional_c_rows)
          conditionals_complete = conditionals_complete && admitted_ready(conditional);
    }
  }
  out.ready = out.base_inputs_ready && conditionals_complete;
  out.status = out.ready ? "available" : "partial";
  if (!out.ready) Reason(out.reason, "branch_291d7e0_conditional_inputs_partial");
  return out;
}

#include "ck3_12003_person_helper_291f0a0.inc.hpp"

game::ContextSourceLaterDirectV1 LaterDirect(
    const ContextSourceBindingsV1 &b, const void *character,
    std::int32_t character_id) {
  game::ContextSourceLaterDirectV1 out{};
  out.character_id = character_id;
  out.status = "partial";
  bool ordered_ready = false;
  const auto carrier = Read<const void *>(b, character, 0x1B0);
  if (!carrier) {
    Reason(out.reason, "later_ordered_character_carrier_unavailable");
  } else {
    out.ordered_header_selection = *carrier ? "character_1b0_inline_98"
                                           : "inline_static_545a3e8";
    const void *header = *carrier ? Offset(*carrier, 0x98)
                                 : b.later_ordered_fallback_header;
    // Native caller reads pointer0 and signed countC even for an empty list.
    const auto data = Read<const void *>(b, header);
    if (data) out.ordered_array_present = *data != nullptr;
    out.ordered_count = Read<std::int32_t>(b, header, 0xC);
    if (!data || !out.ordered_count) {
      Reason(out.reason, "later_ordered_header_fields_unavailable");
    } else if (*out.ordered_count < 0) {
      Reason(out.reason, "later_ordered_negative_count_unrepresentable");
    } else if (*out.ordered_count == 0) {
      out.ordered_rows.emplace();
      ordered_ready = true;
    } else if (!*data) {
      Reason(out.reason, "later_ordered_positive_count_null_array");
    } else {
      // Both slots are loaded before the first key, even if all keys resolve.
      auto store = Read<const void *>(b, b.later_ordered_storage_slot);
      auto fallback = Read<const void *>(b, b.later_ordered_fallback_slot);
      std::vector<const void *> identities;
      out.ordered_rows.emplace();
      ordered_ready = true;
      for (std::int32_t i = 0; i < *out.ordered_count; ++i) {
        game::ContextSourceLaterOrderedRowV1 row{};
        row.native_index = i;
        row.requested_full_id_raw = Read<std::int32_t>(b, *data,
            static_cast<std::size_t>(i) * 4);
        const void *selected = nullptr;
        bool lookup_observed = store.has_value() && fallback.has_value() &&
                               row.requested_full_id_raw.has_value();
        if (!lookup_observed) {
          row.reason = "later_ordered_lookup_operands_unavailable";
        } else {
          if (*store) {
            const auto index = static_cast<std::uint32_t>(
                *row.requested_full_id_raw) & 0xFFFFFFU;
            const auto capacity = Read<std::uint32_t>(b, *store, 0x2C);
            if (!capacity) lookup_observed = false;
            else if (index < *capacity) {
              const auto table = Read<const void *>(b, *store, 0x20);
              if (!table) lookup_observed = false;
              else {
                const auto object = Read<const void *>(b, *table,
                    static_cast<std::size_t>(index) * 16 + 8);
                if (!object) lookup_observed = false;
                else if (*object) {
                  const auto full_id = Read<std::int32_t>(b, *object, 0x10);
                  if (!full_id) lookup_observed = false;
                  else if (*full_id == *row.requested_full_id_raw) {
                    selected = *object;
                    row.selection = "registry_full_id";
                  }
                }
              }
            }
          }
          if (!lookup_observed) {
            row.reason = "later_ordered_demanded_registry_read_unavailable";
          } else if (!selected) {
            selected = *fallback;
            row.selection = "native_fallback";
          }
        }
        if (lookup_observed) {
          if (!selected) {
            row.reason = "later_ordered_native_selected_null";
          } else {
            row.selected_identity = Identity(identities, selected, "later");
            row.selected_field_24c_raw = Read<std::int32_t>(b, selected, 0x24C);
            if (!row.selected_field_24c_raw) {
              row.reason = "later_ordered_selected_24c_unavailable";
            } else {
              row.admitted = *row.selected_field_24c_raw != 0;
              if (*row.admitted) {
                row.property_block = Properties(b, Offset(selected, 0x80));
                if (!PropertiesReady(*row.property_block))
                  row.reason = "later_ordered_consumed_properties_unavailable";
                // Native caller reloads these slots after each admitted merge.
                // The readonly observer performs the same reads, no merge.
                store = Read<const void *>(b, b.later_ordered_storage_slot);
                fallback = Read<const void *>(b, b.later_ordered_fallback_slot);
                if (!store || !fallback)
                  Reason(row.reason, "later_ordered_post_merge_slots_unavailable");
              }
            }
          }
        }
        if (!row.reason.empty()) {
          ordered_ready = false;
          Reason(out.reason, row.reason.c_str());
        }
        out.ordered_rows->push_back(std::move(row));
      }
    }
  }

  bool guarded_ready = false;
  const auto guarded_carrier = Read<const void *>(b, character, 0x1C0);
  if (!guarded_carrier) {
    Reason(out.reason, "later_guarded_character_carrier_unavailable");
  } else {
    out.guarded_selection = *guarded_carrier ? "character_1c0_pointer_388"
                                           : "native_fallback";
    const auto selected = *guarded_carrier
        ? Read<const void *>(b, *guarded_carrier, 0x388)
        : Read<const void *>(b, b.later_guarded_fallback_slot);
    if (!selected || !*selected) {
      Reason(out.reason, "later_guarded_selected_pointer_unavailable");
    } else {
      out.guarded_magic_raw = Read<std::uint32_t>(b, *selected, 0x38);
      if (!out.guarded_magic_raw) {
        Reason(out.reason, "later_guarded_magic_unavailable");
      } else {
        out.guarded_admitted = *out.guarded_magic_raw == 0x4744624FU;
        guarded_ready = true;
        if (*out.guarded_admitted) {
          out.guarded_property_block = Properties(b, Offset(*selected, 0xAA0));
          guarded_ready = PropertiesReady(*out.guarded_property_block);
          if (!guarded_ready)
            Reason(out.reason, "later_guarded_consumed_properties_unavailable");
        }
      }
    }
  }
  out.ready = ordered_ready && guarded_ready;
  out.status = out.ready ? "available" : "partial";
  if (!out.ready) Reason(out.reason, "later_direct_sources_partial");
  return out;
}

} // namespace

ContextSourceBindingsV1 BindContextSourceInputs12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  ContextSourceBindingsV1 b{};
  if (!base || sha != ck3_12003::kExecutableSha256) return b;
  b.enabled = true;
  b.pre_291e210_1640_enabled = true;
  b.army_internal_storage_slot = reinterpret_cast<const void *>(base + 0x5D1DE48);
  b.army_internal_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1DE50);
  b.pre_291e210_second_storage_slot = reinterpret_cast<const void *>(base + 0x5D1E380);
  b.pre_291e210_second_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1E378);
  b.later_direct_enabled = true;
  b.later_ordered_fallback_header = reinterpret_cast<const void *>(base + 0x545A3E8);
  b.later_ordered_storage_slot = reinterpret_cast<const void *>(base + 0x5D1FC58);
  b.later_ordered_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1FC48);
  b.later_guarded_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1DCB0);
  b.helper_291f0a0_enabled = true;
  b.helper_manager_slot = reinterpret_cast<const void *>(base + 0x5D1F6D0);
  b.helper_third_storage_slot = reinterpret_cast<const void *>(base + 0x5D1DE88);
  b.helper_third_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1DE00);
  b.helper_invalid_character_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1FBD8);
  b.helper_range_first_threshold_slot = reinterpret_cast<const void *>(base + 0x5C68E00);
  b.helper_range_last_threshold_slot = reinterpret_cast<const void *>(base + 0x5C68DF8);
  b.helper_default_pc = reinterpret_cast<const void *>(base + 0x5D70FC0);
  b.helper_default_pc_guard_slot = reinterpret_cast<const void *>(base + 0x5D70FBC);
  b.helper_source_pointer_fallback_header = reinterpret_cast<const void *>(base + 0x5D67E40);
  b.helper_source_pointer_fallback_guard_slot = reinterpret_cast<const void *>(base + 0x5D67E38);
  b.provider = reinterpret_cast<void *(*)()>(base + 0x8FD4E0);
  b.post_291d7e0_sources_enabled = true;
  b.post_ab_object_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1E308);
  b.post_ab_signed_character_threshold_slot = reinterpret_cast<const void *>(base + 0x5C6A19C);
  b.post_ab_static_inline_source_list_header = reinterpret_cast<const void *>(base + 0x54E7270);
  b.lifestyle_fallback_header = reinterpret_cast<const void *>(base + 0x54E7288);
  b.house_extra_fallback_header = reinterpret_cast<const void *>(base + 0x54E56B0);
  b.first_storage_slot = reinterpret_cast<const void *>(base + 0x5D1DAF0);
  b.first_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1DAE8);
  b.second_storage_slot = reinterpret_cast<const void *>(base + 0x5D1DE78);
  b.second_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1DE28);
  b.source_fallback_header = reinterpret_cast<const void *>(base + 0x54E78B8);
  b.conditional_a_fallback_properties = reinterpret_cast<const void *>(base + 0x5DC21B0);
  b.selector_a_storage_slot = reinterpret_cast<const void *>(base + 0x5D1E2F8);
  b.selector_a_initial_fallback_slot = reinterpret_cast<const void *>(base + 0x5C67670);
  b.selector_a_second_storage_slot = reinterpret_cast<const void *>(base + 0x5D1E300);
  b.selector_a_second_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1E2E0);
  b.selector_b_storage_slot = reinterpret_cast<const void *>(base + 0x5D1E2F0);
  b.selector_b_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1E2E8);
  b.government = reinterpret_cast<void *(*)(void *)>(base + 0x28C2E10);
  b.condition_registry = reinterpret_cast<const void *>(base + 0x5DC1390);
  b.condition_fallback_object = reinterpret_cast<const void *>(base + 0x5DC1368);
  b.condition_registry_guard = reinterpret_cast<const void *>(base + 0x5DC1388);
  b.condition_fallback_guard = reinterpret_cast<const void *>(base + 0x5DC1364);
  b.token_manager_slot = reinterpret_cast<const void *>(base + 0x5CBEDE8);
  b.prefix_classifier_locale_flag = reinterpret_cast<const void *>(base + 0x5C5D2D8);
  b.prefix_classifier_table_slot = reinterpret_cast<const void *>(base + 0x542F330);
  b.current_locale = BindContextSourceLocale12003(base, sha);
  b.existing_token_lookup = reinterpret_cast<ContextSourceExistingTokenLookupV1>(
      base + 0x3F51AB0);
  return b;
}

game::BattleCurrentPersonContextSourceInputsSnapshotV1
ReadCurrentContextSourceInputs12003(const ContextSourceBindingsV1 &b,
                                   const void *character,
                                   std::int32_t character_id) noexcept {
  game::BattleCurrentPersonContextSourceInputsSnapshotV1 out{};
  out.character_id = character_id;
  if (!b.enabled || !character) {
    out.reason = character ? "context_source_reader_unbound" : "character_unresolved";
    return out;
  }
  if (b.pre_291e210_1640_enabled)
    out.pre_291e210_1640 = Pre291e2101640(b, character, character_id);
  if (b.later_direct_enabled)
    out.later_direct_291c3fb_44c = LaterDirect(b, character, character_id);
  if (b.helper_291f0a0_enabled)
    out.helper_291f0a0 = Helper291f0a0(b, character, character_id);
  out.branch_291e210 = BranchA(b, character);
  out.branch_291d7e0 = BranchB(b, character);
  if (b.post_291d7e0_sources_enabled)
    out.post_291d7e0_sources = Post291d7e0(b, character, character_id);
  out.ready = out.branch_291e210->ready && out.branch_291d7e0->ready;
  if (out.pre_291e210_1640)
    out.ready = out.ready && out.pre_291e210_1640->ready;
  if (out.post_291d7e0_sources)
    out.ready = out.ready && out.post_291d7e0_sources->ready;
  if (out.later_direct_291c3fb_44c)
    out.ready = out.ready && out.later_direct_291c3fb_44c->ready;
  if (out.helper_291f0a0)
    out.ready = out.ready && out.helper_291f0a0->ready;
  out.status = out.ready ? "available" : "partial";
  if (!out.ready) out.reason = "context_source_reads_unavailable";
  return out;
}

} // namespace xar::ck3_12002
