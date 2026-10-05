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
      if (!locale || *locale != 0) {
        row.reason = locale ? "classifier_unavailable_locale_path"
                            : "classifier_locale_flag_unavailable";
        return;
      }
      const auto first = *row.first_signed_byte;
      std::uint16_t classification = 0;
      if (static_cast<std::uint32_t>(first + 1) <= 0x100U) {
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

game::ContextSource291d7e0V1 BranchB(const ContextSourceBindingsV1 &b,
                                    const void *character) {
  game::ContextSource291d7e0V1 out{};
  std::vector<const void *> sources, keys, retained;
  ConditionState conditions{};
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
                if (*key) {
                  copied.key_object_id = Read<std::uint32_t>(b, *key, 0x10);
                  copied.key_object_magic = Read<std::uint32_t>(b, *key, 0x38);
                }
              }
              const auto property = Read<const void *>(b, native, 0x28);
              if (property && *property) copied.property_block = Properties(b, *property);
              copied.reason = "conditional_a_selector_not_observed";
              return copied;
            });
        row.conditional_b_rows = ConditionalRows<game::ContextSourceConditionalBV1>(
            b, *source, 0x568, 0x1C8, row.conditional_b_count,
            [&](const void *native, std::int32_t index) {
              game::ContextSourceConditionalBV1 copied{};
              copied.native_index = index;
              copied.key_i32 = Read<std::int32_t>(b, native);
              copied.property_block = Properties(b, Offset(native, 8));
              copied.reason = "conditional_b_selector_not_observed";
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
  if (b.conditional_a_fallback_properties)
    out.conditional_a_fallback_properties = Properties(
        b, b.conditional_a_fallback_properties);
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

} // namespace

ContextSourceBindingsV1 BindContextSourceInputs12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  ContextSourceBindingsV1 b{};
  if (!base || sha != ck3_12003::kExecutableSha256) return b;
  b.enabled = true;
  b.lifestyle_fallback_header = reinterpret_cast<const void *>(base + 0x54E7288);
  b.house_extra_fallback_header = reinterpret_cast<const void *>(base + 0x54E56B0);
  b.first_storage_slot = reinterpret_cast<const void *>(base + 0x5D1DAF0);
  b.first_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1DAE8);
  b.second_storage_slot = reinterpret_cast<const void *>(base + 0x5D1DE78);
  b.second_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1DE28);
  b.source_fallback_header = reinterpret_cast<const void *>(base + 0x54E78B8);
  b.conditional_a_fallback_properties = reinterpret_cast<const void *>(base + 0x5DC21B0);
  b.government = reinterpret_cast<void *(*)(void *)>(base + 0x28C2E10);
  b.condition_registry = reinterpret_cast<const void *>(base + 0x5DC1390);
  b.condition_fallback_object = reinterpret_cast<const void *>(base + 0x5DC1368);
  b.condition_registry_guard = reinterpret_cast<const void *>(base + 0x5DC1388);
  b.condition_fallback_guard = reinterpret_cast<const void *>(base + 0x5DC1364);
  b.token_manager_slot = reinterpret_cast<const void *>(base + 0x5CBEDE8);
  b.prefix_classifier_locale_flag = reinterpret_cast<const void *>(base + 0x5C5D2D8);
  b.prefix_classifier_table_slot = reinterpret_cast<const void *>(base + 0x542F330);
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
  out.branch_291e210 = BranchA(b, character);
  out.branch_291d7e0 = BranchB(b, character);
  out.ready = out.branch_291e210->ready && out.branch_291d7e0->ready;
  out.status = out.ready ? "available" : "partial";
  if (!out.ready) out.reason = "context_source_reads_unavailable";
  return out;
}

} // namespace xar::ck3_12002
