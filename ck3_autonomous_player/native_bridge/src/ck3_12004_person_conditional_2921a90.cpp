#include "xar_bridge/ck3_12004_person_conditional_2921a90.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <cstring>
#include <sstream>
#include <utility>

namespace xar::ck3_12004 {
namespace {
template <typename T>
std::optional<T> Copy(const PersonCarrierDirect12004Bindings &b,
                      std::uintptr_t address) {
  T value{};
  if (!b.read_memory || !b.read_memory(b.read_context,
      reinterpret_cast<const void *>(address), &value, sizeof(value)))
    return std::nullopt;
  return value;
}
template <typename T>
std::optional<std::vector<T>> Array(const PersonCarrierDirect12004Bindings &b,
    const std::optional<std::uintptr_t> &address, std::int32_t count) {
  if (!address) return std::nullopt;
  if (count == 0) return std::vector<T>{};
  if (*address == 0) return std::nullopt;
  std::vector<T> values(static_cast<std::size_t>(count));
  if (!b.read_memory(b.read_context, reinterpret_cast<const void *>(*address),
                     values.data(), values.size() * sizeof(T))) return std::nullopt;
  return values;
}
float Float(std::uint32_t bits) {
  float value{};
  static_assert(sizeof(value) == sizeof(bits));
  std::memcpy(&value, &bits, sizeof(value));
  return value;
}

PersonConditional2921a90Vote Vote(const PersonCarrierDirect12004Bindings &b,
    std::uintptr_t character, std::uintptr_t ids, std::uint32_t index) {
  PersonConditional2921a90Vote row;
  row.native_index = index;
  row.registry_identity = Copy<std::uintptr_t>(b, b.module_base + 0x5C67568);
  if (!row.registry_identity) { row.reason = "classifier_registry_unread"; return row; }
  bool fallback = *row.registry_identity == 0;
  if (!fallback) {
    row.requested_full_id_u32 = Copy<std::uint32_t>(b, ids + index * 4ULL);
    row.registry_count_u32 = Copy<std::uint32_t>(b, *row.registry_identity + 0x2C);
    if (!row.requested_full_id_u32 || !row.registry_count_u32) {
      row.reason = "classifier_id_or_registry_count_unread"; return row;
    }
    const auto slot = *row.requested_full_id_u32 & 0xFFFFFFU;
    fallback = slot >= *row.registry_count_u32;
    if (!fallback) {
      row.registry_slots_identity = Copy<std::uintptr_t>(b, *row.registry_identity + 0x20);
      if (!row.registry_slots_identity || *row.registry_slots_identity == 0) {
        row.reason = "classifier_registry_table_unread"; return row;
      }
      row.candidate_character_identity = Copy<std::uintptr_t>(
          b, *row.registry_slots_identity + slot * 16ULL + 8);
      if (!row.candidate_character_identity) {
        row.reason = "classifier_candidate_unread"; return row;
      }
      fallback = *row.candidate_character_identity == 0;
      if (!fallback) {
        row.candidate_full_id_u32 = Copy<std::uint32_t>(
            b, *row.candidate_character_identity + kCharacterFullIdOffset);
        if (!row.candidate_full_id_u32) {
          row.reason = "classifier_candidate_id_unread"; return row;
        }
        fallback = *row.candidate_full_id_u32 != *row.requested_full_id_u32;
        if (!fallback) row.selected_character_identity = row.candidate_character_identity;
      }
    }
  }
  row.resolution_selection = fallback ? "fallback" : "mapped_id";
  if (fallback) row.selected_character_identity = Copy<std::uintptr_t>(b, b.module_base + 0x5C67570);
  if (!row.selected_character_identity || *row.selected_character_identity == 0) {
    row.reason = "classifier_selected_character_unread"; return row;
  }
  if (*row.selected_character_identity != character) {
    row.reason = "classifier_25a1220_directional_opinion_unobserved";
    return row;
  }
  // Actual 25A13BB with the caller's R8=0. The scratch read is still demanded;
  // same-pointer comparison bypasses the additional opinion calculation.
  row.base_opinion_i32 = 100;
  row.selected_scratch_identity = Copy<std::uintptr_t>(b, character + 0x1B0);
  if (!row.selected_scratch_identity) { row.reason = "classifier_selected_scratch_unread"; return row; }
  row.additional_opinion_i32 = 0;
  row.minimum_i32 = Copy<std::int32_t>(b, b.module_base + 0x5C6A1EC);
  if (!row.minimum_i32) { row.reason = "classifier_minimum_unread"; return row; }
  row.clamped_i32 = *row.minimum_i32;
  if (100 >= *row.minimum_i32) {
    row.maximum_i32 = Copy<std::int32_t>(b, b.module_base + 0x5C6A1E8);
    if (!row.maximum_i32) { row.reason = "classifier_maximum_unread"; return row; }
    row.clamped_i32 = 100 > *row.maximum_i32 ? *row.maximum_i32 : 100;
  }
  row.high_threshold_bits_u32 = Copy<std::uint32_t>(b, b.module_base + 0x5C68EE0);
  if (!row.high_threshold_bits_u32) { row.reason = "classifier_high_threshold_unread"; return row; }
  const float value = static_cast<float>(*row.clamped_i32);
  if (value >= Float(*row.high_threshold_bits_u32)) row.vote = "high";
  else {
    row.low_threshold_bits_u32 = Copy<std::uint32_t>(b, b.module_base + 0x5C68EF4);
    if (!row.low_threshold_bits_u32) { row.reason = "classifier_low_threshold_unread"; return row; }
    row.vote = Float(*row.low_threshold_bits_u32) >= value ? "low" : "middle";
  }
  row.ready = true;
  return row;
}

void Classifier(const PersonCarrierDirect12004Bindings &b, PersonConditional2921a90DTO &d) {
  const auto character = *d.character_identity;
  d.classifier_magic_u32 = Copy<std::uint32_t>(b, character + 0x1C);
  if (!d.classifier_magic_u32) { d.classifier_reason = "classifier_magic_unread"; return; }
  if (*d.classifier_magic_u32 != 0x43686172U) {
    d.classifier_ready = true; d.classifier_result_i32 = 1; return;
  }
  d.classifier_full_id_u32 = Copy<std::uint32_t>(b, character + 0x18);
  if (!d.classifier_full_id_u32) { d.classifier_reason = "classifier_full_id_unread"; return; }
  if (*d.classifier_full_id_u32 == 0xFFFFFFFFU) {
    d.classifier_ready = true; d.classifier_result_i32 = 1; return;
  }
  d.classifier_land_identity = Copy<std::uintptr_t>(b, character + 0x1C0);
  if (!d.classifier_land_identity) { d.classifier_reason = "classifier_land_unread"; return; }
  if (*d.classifier_land_identity != 0) {
    d.classifier_header_selection = "held_land_a8";
    d.classifier_header_identity = *d.classifier_land_identity + 0xA8;
  } else {
    d.classifier_header_selection = "static_default_5d21338";
    d.classifier_header_identity = b.module_base + 0x5D21338;
    d.classifier_default_guard_i32 = Copy<std::int32_t>(b, b.module_base + 0x5D21350);
    if (!d.classifier_default_guard_i32 || *d.classifier_default_guard_i32 == 0 ||
        *d.classifier_default_guard_i32 == -1) {
      d.classifier_reason = "classifier_default_uninitialized"; return;
    }
  }
  d.classifier_array_identity = Copy<std::uintptr_t>(b, *d.classifier_header_identity);
  d.classifier_count_i32 = Copy<std::int32_t>(b, *d.classifier_header_identity + 0xC);
  if (!d.classifier_array_identity || !d.classifier_count_i32) {
    d.classifier_reason = "classifier_header_unread"; return;
  }
  const auto count = *d.classifier_count_i32;
  if (count < 0) { d.classifier_reason = "classifier_count_negative"; return; }
  if (count == 0) { d.classifier_ready = true; d.classifier_result_i32 = 1; return; }
  if (*d.classifier_array_identity == 0) { d.classifier_reason = "classifier_array_unread"; return; }
  d.classifier_ready = true;
  std::uint32_t high = 0, low = 0, middle = 0;
  for (std::uint32_t index = 0; index < static_cast<std::uint32_t>(count); ++index) {
    auto row = Vote(b, character, *d.classifier_array_identity, index);
    if (!row.ready) {
      d.classifier_ready = false;
      if (d.classifier_reason.empty()) d.classifier_reason = row.reason;
    } else if (row.vote == "high") ++high;
    else if (row.vote == "low") ++low;
    else ++middle;
    d.classifier_rows.push_back(std::move(row));
  }
  if (d.classifier_ready) d.classifier_result_i32 = high > low && high > middle ? 0
      : low > high && low > middle ? 2 : 1;
}

void Weight(const PersonCarrierDirect12004Bindings &b, PersonConditional2921a90Row &r) {
  const auto object = *r.object_identity;
  r.expression_flag_280_i32 = Copy<std::int32_t>(b, object + 0x280);
  if (!r.expression_flag_280_i32) { r.reason = "weight_flag_280_unread"; return; }
  if (*r.expression_flag_280_i32 == 0) { r.weight_q64 = 100000; return; }
  r.expression_tree_278_identity = Copy<std::uintptr_t>(b, object + 0x278);
  if (!r.expression_tree_278_identity) { r.reason = "weight_tree_278_unread"; return; }
  if (*r.expression_tree_278_identity != 0) { r.reason = "weight_virtual_expression_9d7060_unobserved"; return; }
  r.expression_scoped_268_identity = Copy<std::uintptr_t>(b, object + 0x268);
  if (!r.expression_scoped_268_identity) { r.reason = "weight_scoped_268_unread"; return; }
  if (*r.expression_scoped_268_identity != 0) { r.reason = "weight_scoped_expression_37542d0_unobserved"; return; }
  r.expression_count_1d4_i32 = Copy<std::int32_t>(b, object + 0x1D4);
  if (!r.expression_count_1d4_i32) { r.reason = "weight_count_1d4_unread"; return; }
  if (*r.expression_count_1d4_i32 != 0) { r.reason = "weight_scripted_expression_3755500_unobserved"; return; }
  r.raw_value_258_q64 = Copy<std::int64_t>(b, object + 0x258);
  if (!r.raw_value_258_q64) { r.reason = "weight_literal_258_unread"; return; }
  r.weight_q64 = r.raw_value_258_q64;
}

void Property(const PersonCarrierDirect12004Bindings &b, PersonConditional2921a90Row &r) {
  const auto object = *r.object_identity;
  r.keys_count_i32 = Copy<std::int32_t>(b, object + 0xC);
  r.values_count_i32 = Copy<std::int32_t>(b, object + 0x74);
  if (!r.keys_count_i32 || !r.values_count_i32) { r.reason = "conditional_pc_counts_unread"; return; }
  if (*r.keys_count_i32 < 0 || *r.values_count_i32 < 0) { r.reason = "conditional_pc_count_negative"; return; }
  r.properties.emplace();
  const auto keys = Copy<std::uintptr_t>(b, object);
  const auto values = Copy<std::uintptr_t>(b, object + 0x68);
  r.properties->keys_u16 = Array<std::uint16_t>(b, keys, *r.keys_count_i32);
  r.properties->values_q64 = Array<std::int64_t>(b, values, *r.values_count_i32);
  // The postfold getter executes before the key loop; preserve its actual
  // current slot without invoking initialization. Empty/sentinel-only numeric
  // operands do not consume its registry table.
  r.metadata_registry_identity = Copy<std::uintptr_t>(b, b.module_base + 0x5D1F7B0);
  if (!r.properties->keys_u16 || !r.properties->values_q64) r.reason = "conditional_pc_arrays_unread";
  if (r.properties->keys_u16) {
    for (std::size_t index = 0; index < r.properties->keys_u16->size(); ++index) {
      PersonConditional2921a90Metadata m;
      m.native_index = static_cast<std::uint32_t>(index);
      m.key_u16 = (*r.properties->keys_u16)[index];
      if (*m.key_u16 == 0xFFFFU) m.definition_identity = b.module_base + 0x5461F40;
      else {
        if (r.metadata_registry_identity && *r.metadata_registry_identity != 0) {
          if (!r.metadata_table_identity)
            r.metadata_table_identity = Copy<std::uintptr_t>(b, *r.metadata_registry_identity + 0x50);
          if (r.metadata_table_identity && *r.metadata_table_identity != 0)
            m.definition_identity = *r.metadata_table_identity + *m.key_u16 * 0xC8ULL;
        }
        if (!m.definition_identity) m.reason = "property_metadata_registry_uninitialized_or_unread";
      }
      if (m.definition_identity) {
        m.flag_ba_u8 = Copy<std::uint8_t>(b, *m.definition_identity + 0xBA);
        if (!m.flag_ba_u8) m.reason = "property_metadata_ba_unread";
        else if (*m.flag_ba_u8 != 0) m.ready = true;
        else {
          m.flag_b8_u8 = Copy<std::uint8_t>(b, *m.definition_identity + 0xB8);
          if (!m.flag_b8_u8) m.reason = "property_metadata_b8_unread";
          else m.ready = true;
        }
      }
      if (!m.ready && r.reason.empty()) r.reason = m.reason;
      r.metadata.push_back(std::move(m));
    }
  }
  if (*r.values_count_i32 < *r.keys_count_i32 && r.reason.empty())
    r.reason = "conditional_pc_key_values_missing";
  r.ready = r.reason.empty();
}
} // namespace

PersonConditional2921a90DTO ReadPersonConditional2921a90Inputs12004(
    const PersonCarrierDirect12004Bindings &b, const PersonFollowing2921a90DTO &s) {
  PersonConditional2921a90DTO d;
  d.build_version = kGameVersion;
  d.executable_sha256 = kExecutableSha256;
  d.character_id = s.character_id;
  d.character_identity = s.character_identity;
  d.selected_model_identity = s.selected_model_identity;
  d.selected_object_identity = s.selected_object_identity;
  d.conditional_definition_identity = s.conditional_definition_identity;
  d.admitted = s.admitted;
  d.gate_b8c_count_i32 = s.conditional_b8c_count_i32;
  d.gate_bbc_count_i32 = s.conditional_bbc_count_i32;
  if (!b.enabled || !b.read_memory) { d.reason = "exact_build_binding_unavailable"; return d; }
  if (s.admitted == false || (s.admitted == true && d.gate_b8c_count_i32 == 0 &&
                            d.gate_bbc_count_i32 == 0)) {
    d.ready = true; d.selected_family = "not_demanded"; d.occurrence_count = 0U; return d;
  }
  if (s.admitted != true || !d.character_identity || *d.character_identity == 0 ||
      !d.conditional_definition_identity || *d.conditional_definition_identity == 0 ||
      !d.gate_b8c_count_i32 || (*d.gate_b8c_count_i32 == 0 && !d.gate_bbc_count_i32)) {
    d.reason = s.conditional_reason.empty() ? "conditional_admission_unread" : s.conditional_reason;
    return d;
  }
  Classifier(b, d);
  if (!d.classifier_ready) { d.reason = d.classifier_reason; return d; }
  if (*d.classifier_result_i32 == 1) {
    d.selected_family = "classifier_other_empty"; d.ready = true; d.occurrence_count = 0U; return d;
  }
  const bool high = *d.classifier_result_i32 == 0;
  d.selected_family = high ? "bb0_bbc" : "b80_b8c";
  const auto definition = *d.conditional_definition_identity;
  d.selected_array_identity = Copy<std::uintptr_t>(b, definition + (high ? 0xBB0 : 0xB80));
  d.selected_count_i32 = Copy<std::int32_t>(b, definition + (high ? 0xBBC : 0xB8C));
  if (!d.selected_array_identity || !d.selected_count_i32) { d.reason = "conditional_selected_header_unread"; return d; }
  const auto count = *d.selected_count_i32;
  if (count < 0) { d.reason = "conditional_selected_count_negative"; return d; }
  if (count > 0 && *d.selected_array_identity == 0) { d.reason = "conditional_selected_array_unread"; return d; }
  d.ready = true;
  std::uint32_t occurrences = 0;
  for (std::uint32_t index = 0; index < static_cast<std::uint32_t>(count); ++index) {
    PersonConditional2921a90Row row;
    row.native_index = index;
    row.object_identity = Copy<std::uintptr_t>(b, *d.selected_array_identity + index * 8ULL);
    if (!row.object_identity || *row.object_identity == 0) row.reason = "conditional_modifier_object_unread";
    else {
      Weight(b, row);
      if (row.weight_q64) {
        if (*row.weight_q64 == 0) row.ready = true;
        else { Property(b, row); if (row.ready) ++occurrences; }
      }
    }
    if (!row.ready) {
      d.ready = false;
      if (d.reason.empty()) d.reason = row.reason;
    }
    d.rows.push_back(std::move(row));
  }
  if (d.ready) d.occurrence_count = occurrences;
  return d;
}

namespace {
class Json {
public:
  std::ostringstream out;
  bool first = true;
  Json() { out << '{'; }
  void Key(std::string_view name) { if (!first) out << ','; first = false; Text(name); out << ':'; }
  void Text(std::string_view value) {
    constexpr char hex[] = "0123456789abcdef";
    out << '"';
    for (const unsigned char c : value) {
      if (c == '"' || c == '\\') out << '\\' << static_cast<char>(c);
      else if (c < 0x20) out << "\\u00" << hex[c >> 4] << hex[c & 0xF];
      else out << static_cast<char>(c);
    }
    out << '"';
  }
  void String(std::string_view name, std::string_view value, bool nullable = false) {
    Key(name); if (nullable && value.empty()) out << "null"; else Text(value);
  }
  void Bool(std::string_view name, bool value) { Key(name); out << (value ? "true" : "false"); }
  void Bool(std::string_view name, std::optional<bool> value) {
    Key(name); if (!value) out << "null"; else out << (*value ? "true" : "false");
  }
  template <typename T> void Number(std::string_view name, std::optional<T> value) {
    Key(name); if (value) out << +*value; else out << "null";
  }
  void Q64(std::string_view name, std::optional<std::int64_t> value) {
    Key(name); if (value) out << '"' << *value << '"'; else out << "null";
  }
  void Pointer(std::string_view name, std::optional<std::uintptr_t> value) {
    Key(name); if (value) out << "\"0x" << std::hex << *value << std::dec << '"'; else out << "null";
  }
  template <typename T> void Numbers(std::string_view name,
      const std::optional<std::vector<T>> &values, bool strings) {
    Key(name); if (!values) { out << "null"; return; }
    out << '['; bool comma = false;
    for (const auto value : *values) {
      if (comma) out << ','; comma = true;
      if (strings) out << '"'; out << +value; if (strings) out << '"';
    }
    out << ']';
  }
  std::string End() { out << '}'; return out.str(); }
};
} // namespace

std::string SerializePersonConditional2921a90(const PersonConditional2921a90DTO &d) {
  Json j;
  j.String("schema", kPersonConditional2921a90Schema);
  j.String("build_version", d.build_version); j.String("executable_sha256", d.executable_sha256);
  j.Bool("ready", d.ready); j.String("reason", d.reason, true); j.Bool("admitted", d.admitted);
#define NUMBER(name) j.Number(#name, d.name)
#define POINTER(name) j.Pointer(#name, d.name)
  NUMBER(character_id); POINTER(character_identity); POINTER(selected_model_identity);
  POINTER(selected_object_identity); POINTER(conditional_definition_identity);
  NUMBER(gate_b8c_count_i32); NUMBER(gate_bbc_count_i32);
  j.Bool("classifier_ready", d.classifier_ready); j.String("classifier_reason", d.classifier_reason, true);
  NUMBER(classifier_magic_u32); NUMBER(classifier_full_id_u32); POINTER(classifier_land_identity);
  j.String("classifier_header_selection", d.classifier_header_selection);
  POINTER(classifier_header_identity); NUMBER(classifier_default_guard_i32);
  POINTER(classifier_array_identity); NUMBER(classifier_count_i32); NUMBER(classifier_result_i32);
  j.String("selected_family", d.selected_family); POINTER(selected_array_identity);
  NUMBER(selected_count_i32); NUMBER(occurrence_count);
#undef NUMBER
#undef POINTER
  j.Key("classifier_rows"); j.out << '[';
  bool first = true;
  for (const auto &r : d.classifier_rows) {
    if (!first) j.out << ','; first = false;
    Json q;
    q.Number("native_index", std::optional<std::uint32_t>{r.native_index});
    q.Bool("ready", r.ready); q.String("reason", r.reason, true);
    q.String("resolution_selection", r.resolution_selection); q.String("vote", r.vote);
#define NUMBER(name) q.Number(#name, r.name)
#define POINTER(name) q.Pointer(#name, r.name)
    NUMBER(requested_full_id_u32); POINTER(registry_identity); NUMBER(registry_count_u32);
    POINTER(registry_slots_identity); POINTER(candidate_character_identity); NUMBER(candidate_full_id_u32);
    POINTER(selected_character_identity); POINTER(selected_scratch_identity); NUMBER(base_opinion_i32);
    NUMBER(additional_opinion_i32); NUMBER(minimum_i32); NUMBER(maximum_i32); NUMBER(clamped_i32);
    NUMBER(high_threshold_bits_u32); NUMBER(low_threshold_bits_u32);
#undef NUMBER
#undef POINTER
    j.out << q.End();
  }
  j.out << ']'; j.Key("rows"); j.out << '['; first = true;
  for (const auto &r : d.rows) {
    if (!first) j.out << ','; first = false;
    Json q;
    q.Number("native_index", std::optional<std::uint32_t>{r.native_index});
    q.Bool("ready", r.ready); q.String("reason", r.reason, true);
#define NUMBER(name) q.Number(#name, r.name)
#define POINTER(name) q.Pointer(#name, r.name)
    POINTER(object_identity); NUMBER(expression_flag_280_i32); POINTER(expression_tree_278_identity);
    POINTER(expression_scoped_268_identity); NUMBER(expression_count_1d4_i32);
    NUMBER(keys_count_i32); NUMBER(values_count_i32); POINTER(metadata_registry_identity); POINTER(metadata_table_identity);
#undef NUMBER
#undef POINTER
    q.Q64("raw_value_258_q64", r.raw_value_258_q64); q.Q64("weight_q64", r.weight_q64);
    q.Key("properties");
    if (!r.properties) q.out << "null";
    else {
      Json p; p.Numbers("keys_u16", r.properties->keys_u16, false);
      p.Numbers("values_q64", r.properties->values_q64, true); q.out << p.End();
    }
    q.Key("metadata"); q.out << '['; bool metadata_first = true;
    for (const auto &m : r.metadata) {
      if (!metadata_first) q.out << ','; metadata_first = false;
      Json p; p.Number("native_index", std::optional<std::uint32_t>{m.native_index});
      p.Bool("ready", m.ready); p.String("reason", m.reason, true);
      p.Number("key_u16", m.key_u16); p.Pointer("definition_identity", m.definition_identity);
      p.Number("flag_ba_u8", m.flag_ba_u8); p.Number("flag_b8_u8", m.flag_b8_u8);
      q.out << p.End();
    }
    q.out << ']'; j.out << q.End();
  }
  j.out << ']';
  return j.End();
}
// Added reuse seams only. The original reader and original JSON leaf above
// remain unchanged; the new pair-opinion sibling can demand a different list.
PersonConditional2921a90Row ReadPersonConditional2921a90RowInputs12004(
    const PersonCarrierDirect12004Bindings &b, std::uintptr_t physical_array,
    std::uint32_t native_index) {
  PersonConditional2921a90Row row;
  row.native_index = native_index;
  row.object_identity = Copy<std::uintptr_t>(b, physical_array + native_index * 8ULL);
  if (!row.object_identity || *row.object_identity == 0)
    row.reason = "conditional_modifier_object_unread";
  else {
    Weight(b, row);
    if (row.weight_q64) {
      if (*row.weight_q64 == 0) row.ready = true;
      else Property(b, row);
    }
  }
  return row;
}

std::string SerializePersonConditional2921a90RowInputs12004(
    const PersonConditional2921a90Row &r) {
  Json q;
  q.Number("native_index", std::optional<std::uint32_t>{r.native_index});
  q.Bool("ready", r.ready); q.String("reason", r.reason, true);
#define NUMBER(name) q.Number(#name, r.name)
#define POINTER(name) q.Pointer(#name, r.name)
  POINTER(object_identity); NUMBER(expression_flag_280_i32); POINTER(expression_tree_278_identity);
  POINTER(expression_scoped_268_identity); NUMBER(expression_count_1d4_i32);
  NUMBER(keys_count_i32); NUMBER(values_count_i32); POINTER(metadata_registry_identity); POINTER(metadata_table_identity);
#undef NUMBER
#undef POINTER
  q.Q64("raw_value_258_q64", r.raw_value_258_q64); q.Q64("weight_q64", r.weight_q64);
  q.Key("properties");
  if (!r.properties) q.out << "null";
  else {
    Json p; p.Numbers("keys_u16", r.properties->keys_u16, false);
    p.Numbers("values_q64", r.properties->values_q64, true); q.out << p.End();
  }
  q.Key("metadata"); q.out << '['; bool first = true;
  for (const auto &m : r.metadata) {
    if (!first) q.out << ',';
    first = false;
    Json p; p.Number("native_index", std::optional<std::uint32_t>{m.native_index});
    p.Bool("ready", m.ready); p.String("reason", m.reason, true);
    p.Number("key_u16", m.key_u16); p.Pointer("definition_identity", m.definition_identity);
    p.Number("flag_ba_u8", m.flag_ba_u8); p.Number("flag_b8_u8", m.flag_b8_u8);
    q.out << p.End();
  }
  q.out << ']';
  return q.End();
}
PersonConditional2921a90Row ReadPersonConditional2921a90RowWithWeightInputs12004(
    const PersonCarrierDirect12004Bindings &b, std::uintptr_t physical_array,
    std::uint32_t native_index, std::int64_t observed_weight) {
  PersonConditional2921a90Row row;
  row.native_index = native_index;
  row.object_identity = Copy<std::uintptr_t>(b, physical_array + native_index * 8ULL);
  if (!row.object_identity || *row.object_identity == 0) {
    row.reason = "conditional_modifier_object_unread";
    return row;
  }
  // Retain guarded physical expression operands independently of the newly
  // observed native numerical value. An evaluator gap no longer decides this
  // row's weight readiness, but it remains visible in the original DTO.
  Weight(b, row);
  row.weight_q64 = observed_weight;
  row.reason.clear();
  if (observed_weight == 0) row.ready = true;
  else Property(b, row);
  return row;
}
} // namespace xar::ck3_12004
