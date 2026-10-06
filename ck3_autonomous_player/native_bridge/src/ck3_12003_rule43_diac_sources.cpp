#include "xar_bridge/ck3_12003_rule43_diac_sources.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include <algorithm>
#include <utility>

namespace xar::ck3_12003 {
namespace {
const void *At(const void *p, std::size_t n) {
  return p ? static_cast<const std::byte *>(p) + n : nullptr;
}
template<class T> std::optional<T> Read(const Rule43DiacBindingsV1 &b,
    const void *p, std::size_t n = 0) {
  T value{};
  if (!p || !b.read_memory || !b.read_memory(b.read_context, At(p, n), &value, sizeof value))
    return std::nullopt;
  return value;
}
std::string Identity(const void *p) { return "ptr:" + std::to_string(reinterpret_cast<std::uintptr_t>(p)); }
std::optional<std::uint64_t> Rva(const Rule43DiacBindingsV1 &b, const void *p) {
  const auto value = reinterpret_cast<std::uintptr_t>(p);
  return value >= b.image_base ? std::optional<std::uint64_t>{value - b.image_base} : std::nullopt;
}
// Readable native miss alone takes fallback. A read failure never becomes miss.
const void *Lookup(const Rule43DiacBindingsV1 &b, const void *storage,
    const void *fallback, std::int32_t id, std::size_t id_offset,
    std::optional<std::string> &selection, std::string &reason) {
  const auto store = Read<const void *>(b, storage);
  if (!store) { reason = "registry_store_read_unavailable"; return nullptr; }
  if (*store) {
    const auto capacity = Read<std::uint32_t>(b, *store, 0x2C);
    if (!capacity) { reason = "registry_capacity_read_unavailable"; return nullptr; }
    const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
    if (index < *capacity) {
      const auto table = Read<const void *>(b, *store, 0x20);
      if (!table) { reason = "registry_table_read_unavailable"; return nullptr; }
      const auto object = Read<const void *>(b, *table, static_cast<std::size_t>(index) * 16 + 8);
      if (!object) { reason = "registry_row_read_unavailable"; return nullptr; }
      if (*object) {
        const auto actual_id = Read<std::int32_t>(b, *object, id_offset);
        if (!actual_id) { reason = "registry_generation_read_unavailable"; return nullptr; }
        if (*actual_id == id) { selection = "registry_full_generation"; return *object; }
      }
    }
  }
  const auto selected = Read<const void *>(b, fallback);
  if (!selected || !*selected) { reason = "registry_fallback_read_unavailable"; return nullptr; }
  selection = "native_fallback";
  return *selected;
}

game::Rule43NodeV1 Node(const Rule43DiacBindingsV1 &b, const void *object,
    std::uint8_t mode, std::string path, std::vector<const void *> ancestors) {
  game::Rule43NodeV1 out{};
  out.path = std::move(path);
  if (!object) { out.reason = "node_receiver_null"; return out; }
  out.identity = Identity(object);
  if (std::find(ancestors.begin(), ancestors.end(), object) != ancestors.end()) {
    out.reason = "recursive_node_result_not_bounded"; return out;
  }
  ancestors.push_back(object);
  const auto table = Read<const void *>(b, object);
  if (!table || !*table) { out.reason = "node_vtable_read_unavailable"; return out; }
  const auto slot58 = Read<const void *>(b, *table, 0x58);
  if (slot58) out.slot58_rva = Rva(b, *slot58);
  if (!out.slot58_rva || *out.slot58_rva != 0x855AB0) {
    out.reason = "applicability_slot58_source"; return out;
  }
  const auto slot60 = Read<const void *>(b, *table, 0x60);
  if (slot60) out.slot60_rva = Rva(b, *slot60);
  if (!out.slot60_rva || (*out.slot60_rva != 0x9CFEC0 && *out.slot60_rva != 0x9CFEE0)) {
    out.reason = "applicability_slot60_source"; return out;
  }
  // Closed actual58 returns0; both recognized actual60 bodies produce zero mask.
  const auto slotc8 = Read<const void *>(b, *table, 0xC8);
  if (slotc8) out.slotc8_rva = Rva(b, *slotc8);
  if (!out.slotc8_rva) { out.reason = "evaluator_slotc8_read_unavailable"; return out; }
  if (*out.slotc8_rva == 0x372F780) {
    if (mode == 2 || mode == 4) {
      out.reason = mode == 2 ? "mode2_372f880_source" : "mode4_37354a0_source";
      return out;
    }
    const auto header = At(object, mode == 1 || mode == 3 ? 0x88U : 0x40U);
    // Native reads pointer before signed count, even count0.
    const auto data = Read<const void *>(b, header);
    if (data) out.children_array_present = *data != nullptr;
    out.children_count_raw = Read<std::int32_t>(b, header, 0xC);
    if (!data || !out.children_count_raw) { out.reason = "conjunction_header_read_unavailable"; return out; }
    if (*out.children_count_raw == 0) { out.result = true; return out; }
    if (*out.children_count_raw < 0) { out.reason = "negative_conjunction_count_not_empty"; return out; }
    for (std::int32_t i = 0; i < *out.children_count_raw; ++i) {
      const auto child = Read<const void *>(b, *data, static_cast<std::size_t>(i) * 8);
      const auto child_path = out.path + "/child" + std::to_string(i);
      auto next = child ? Node(b, *child, mode, child_path, ancestors) : game::Rule43NodeV1{};
      if (!child) { next.path = child_path; next.reason = "conjunction_child_pointer_read_unavailable"; }
      out.children.push_back(std::move(next));
      const auto &last = out.children.back();
      if (!last.result) { out.reason = last.reason; return out; }
      if (!*last.result) { out.result = false; return out; }
    }
    out.result = true;
    return out;
  }
  if (*out.slotc8_rva == 0x3730940) {
    // Referent precedes arguments; compare follows known nested result.
    const auto referent = Read<const void *>(b, object, 0x40);
    out.reference_arguments_count_raw = Read<std::int32_t>(b, object, 0x74);
    if (!referent || !out.reference_arguments_count_raw) { out.reason = "reference_inputs_read_unavailable"; return out; }
    if (*out.reference_arguments_count_raw != 0) { out.reason = "reference_arguments_37b6c50_source"; return out; }
    const auto nested = Read<const void *>(b, *referent, 0x110);
    if (!nested) { out.reason = "reference_nested_pointer_read_unavailable"; return out; }
    out.nested_present = *nested != nullptr;
    bool result = false;
    if (*nested) {
      out.children.push_back(Node(b, *nested, mode, out.path + "/reference", ancestors));
      if (!out.children.back().result) { out.reason = out.children.back().reason; return out; }
      result = *out.children.back().result;
    }
    out.reference_compare_raw = Read<std::uint8_t>(b, object, 0x80);
    if (!out.reference_compare_raw) { out.reason = "reference_compare_read_unavailable"; return out; }
    out.result = *out.reference_compare_raw == static_cast<std::uint8_t>(result);
    return out;
  }
  out.reason = "evaluator_slotc8_source";
  return out;
}

game::Rule43AdmissionV1 Rule(const Rule43DiacBindingsV1 &b, std::int32_t id) {
  game::Rule43AdmissionV1 out{};
  out.input_character_full_id = id;
  const auto provider = Read<const void *>(b, b.rule_provider_slot);
  if (!provider || !*provider) { out.reason = "rule_provider_1d65660_unavailable"; return out; }
  out.provider_identity = Identity(*provider);
  const auto array = Read<const void *>(b, *provider, 0xEF0);
  if (!array || !*array) { out.reason = "rule_array_ef0_read_unavailable"; return out; }
  const void *receiver = At(*array, 0x22F0);
  out.rule_identity = Identity(receiver);
  out.mode_raw = Read<std::uint8_t>(b, b.rule_mode_slot);
  if (!out.mode_raw) { out.reason = "rule_mode_5d1dadc_read_unavailable"; return out; }
  out.registry_count_raw = Read<std::int32_t>(b, b.root_registry_header, 0xC);
  if (!out.registry_count_raw) { out.reason = "root_registry_count_read_unavailable"; return out; }
  const void *descriptor = b.root_fallback_descriptor;
  if (*out.registry_count_raw > 4) {
    const auto data = Read<const void *>(b, b.root_registry_header);
    if (!data || !*data) { out.reason = "root_registry_data_read_unavailable"; return out; }
    descriptor = At(*data, 4 * 0x50);
    out.descriptor_selection = "registry_kind4";
  } else out.descriptor_selection = "native_descriptor_fallback";
  const auto validator = Read<const void *>(b, descriptor, 0x10);
  if (validator) out.loaded_validator_rva = Rva(b, *validator);
  if (!out.loaded_validator_rva || *out.loaded_validator_rva != out.expected_validator_rva) {
    out.reason = "root_validator_loaded_source"; return out;
  }
  const auto character = Lookup(b, b.character_storage_slot, b.character_fallback_slot,
      id, 0x18, out.root_lookup_selection, out.reason);
  if (!character) return out;
  out.root_object_identity = Identity(character);
  out.root_tag_raw = Read<std::uint32_t>(b, character, 0x1C);
  if (!out.root_tag_raw) { out.reason = "root_selected_tag_read_unavailable"; return out; }
  if (*out.root_tag_raw != 0x43686172U) out.root_valid = false;
  else {
    out.root_full_id_raw = Read<std::int32_t>(b, character, 0x18);
    if (!out.root_full_id_raw) { out.reason = "root_selected_full_id_read_unavailable"; return out; }
    out.root_valid = *out.root_full_id_raw != -1;
  }
  if (!*out.root_valid) { out.result = false; return out; }
  out.nodes.push_back(Node(b, receiver, *out.mode_raw, "rule43", {}));
  out.result = out.nodes.front().result;
  out.reason = out.nodes.front().reason;
  return out;
}

const void *SelectedCharacter(const Rule43DiacBindingsV1 &b, const void *character, std::string &reason) {
  const auto landed = Read<const void *>(b, character, 0x1C0);
  const auto related = Read<const void *>(b, character, 0x1B8);
  if (!landed || !related) { reason = "secondary_28bfc70_carriers_read_unavailable"; return nullptr; }
  if (*landed) {
    const auto owner = Read<const void *>(b, *landed, 0x1C0);
    const auto candidate = owner ? Read<const void *>(b, *owner, 0x28) : std::nullopt;
    if (!candidate || !*candidate) { reason = "secondary_28bfc70_candidate_read_unavailable"; return nullptr; }
    const auto tag = Read<std::uint32_t>(b, *candidate, 0x1C);
    if (!tag) { reason = "secondary_28bfc70_candidate_tag_unavailable"; return nullptr; }
    if (*tag != 0x43686172U) return character;
    const auto id = Read<std::int32_t>(b, *candidate, 0x18);
    if (!id) { reason = "secondary_28bfc70_candidate_id_unavailable"; return nullptr; }
    return *id != -1 ? *candidate : character;
  }
  if (!*related) {
    const auto fallback = Read<const void *>(b, b.character_fallback_slot);
    if (!fallback || !*fallback) { reason = "secondary_28bfc70_fallback_read_unavailable"; return nullptr; }
    return *fallback;
  }
  const auto id = Read<std::int32_t>(b, *related, 0xC8);
  if (!id) { reason = "secondary_28bfc70_related_id_unavailable"; return nullptr; }
  std::optional<std::string> selection;
  return Lookup(b, b.character_storage_slot, b.character_fallback_slot, *id, 0x18, selection, reason);
}
const void *Diac(const Rule43DiacBindingsV1 &b, const void *character, game::DiacSelectionV1 &out) {
  out.source_character_identity = Identity(character);
  const auto component = Read<const void *>(b, character, 0x1C8);
  if (!component) { out.reason = "diac_source_carrier_read_unavailable"; return nullptr; }
  out.requested_diac_id_raw = *component ? Read<std::int32_t>(b, *component, 0x30) : std::optional<std::int32_t>{-1};
  if (!out.requested_diac_id_raw) { out.reason = "diac_requested_id_read_unavailable"; return nullptr; }
  const auto selected = Lookup(b, b.diac_storage_slot, b.diac_fallback_slot,
      *out.requested_diac_id_raw, 8, out.lookup_selection, out.reason);
  if (selected) out.diac_identity = Identity(selected);
  return selected;
}
void ValidateDiac(const Rule43DiacBindingsV1 &b, const void *object, game::DiacSelectionV1 &out) {
  out.diac_tag_raw = Read<std::uint32_t>(b, object, 0xC);
  if (!out.diac_tag_raw) { out.reason = "diac_tag_read_unavailable"; return; }
  if (*out.diac_tag_raw != 0x44696163U) { out.diac_valid = false; return; }
  out.diac_full_id_raw = Read<std::int32_t>(b, object, 8);
  if (!out.diac_full_id_raw) { out.reason = "diac_full_id_read_unavailable"; return; }
  out.diac_valid = *out.diac_full_id_raw != -1;
}
} // namespace

Rule43DiacBindingsV1 BindRule43DiacSources12003(std::uintptr_t base, std::string_view sha) {
  Rule43DiacBindingsV1 b{};
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.image_base = base;
  b.diac_storage_slot = reinterpret_cast<const void *>(base + 0x5D20318);
  b.diac_fallback_slot = reinterpret_cast<const void *>(base + 0x5D20310);
  b.character_storage_slot = reinterpret_cast<const void *>(base + 0x5C67568);
  b.character_fallback_slot = reinterpret_cast<const void *>(base + 0x5C67570);
  b.rule_provider_slot = reinterpret_cast<const void *>(base + 0x5D21DC8);
  b.rule_mode_slot = reinterpret_cast<const void *>(base + 0x5D1DADC);
  b.root_registry_header = reinterpret_cast<const void *>(base + 0x54F2AF0);
  b.root_fallback_descriptor = reinterpret_cast<const void *>(base + 0x54F5310);
  b.numeric = BindDiacLiteralNumericInputs12003(base, sha);
  return b;
}

game::FollowingDiac2920d60V1 ReadRule43DiacSources12003(
    const Rule43DiacBindingsV1 &b, const void *character, std::int32_t id) {
  game::FollowingDiac2920d60V1 out{};
  out.character_id = id;
  const auto fail = [&](const std::string &reason) { out.reason = reason; return out; };
  const auto finish = [&]() {
    out.ready = out.selected_family && (*out.selected_family == "none" ||
        (out.numeric_inputs && out.numeric_inputs->ready));
    out.status = out.ready ? "available" : "partial";
    if (!out.ready && out.reason.empty()) out.reason = "selected_diac_numeric_inputs_partial";
    return out;
  };
  if (!b.enabled || !b.read_memory || !character) return fail("rule43_diac_reader_unbound");
  const auto primary = Diac(b, character, out.primary);
  if (!primary) return fail(out.primary.reason);
  // Native resolves the owner's Character before validating primary Diac.
  out.primary.diac_owner_full_id_raw = Read<std::int32_t>(b, primary, 0x24);
  if (!out.primary.diac_owner_full_id_raw) return fail("primary_diac_owner_read_unavailable");
  const auto resolved = Lookup(b, b.character_storage_slot, b.character_fallback_slot,
      *out.primary.diac_owner_full_id_raw, 0x18, out.primary.early_character_lookup_selection, out.primary.reason);
  if (!resolved) return fail(out.primary.reason);
  ValidateDiac(b, primary, out.primary);
  if (!out.primary.diac_valid) return fail(out.primary.reason);
  const auto selected_numeric = [&](const void *diac, const void *scope, std::size_t offset) {
    const auto definition = Read<const void *>(b, diac, 0x28);
    if (!definition || !*definition) { out.reason = "selected_diac_definition_read_unavailable"; return; }
    auto numeric = b.numeric;
    numeric.read_memory = b.read_memory;
    numeric.read_context = b.read_context;
    out.numeric_inputs = ReadDiacLiteralNumericInputs12003(numeric, scope, At(*definition, offset));
    out.reason = out.numeric_inputs->reason;
  };
  if (*out.primary.diac_valid) {
    out.primary.rule_character_full_id_raw = Read<std::int32_t>(b, resolved, 0x18);
    if (!out.primary.rule_character_full_id_raw) return fail("primary_rule_character_id_read_unavailable");
    out.primary.rule = Rule(b, *out.primary.rule_character_full_id_raw);
    if (!out.primary.rule->result) return fail(out.primary.rule->reason);
    if (*out.primary.rule->result) {
      out.selected_family = "primary_620";
      selected_numeric(primary, At(primary, 0x24), 0x620);
      return finish();
    }
  }
  out.secondary.emplace();
  auto &secondary = *out.secondary;
  const auto source = SelectedCharacter(b, character, secondary.reason);
  if (!source) return fail(secondary.reason);
  const auto diac = Diac(b, source, secondary);
  if (!diac) return fail(secondary.reason);
  ValidateDiac(b, diac, secondary);
  if (!secondary.diac_valid) return fail(secondary.reason);
  if (!*secondary.diac_valid) { out.selected_family = "none"; return finish(); }
  out.current_character_full_id_raw = Read<std::int32_t>(b, character, 0x18);
  secondary.diac_owner_full_id_raw = Read<std::int32_t>(b, diac, 0x24);
  if (!out.current_character_full_id_raw || !secondary.diac_owner_full_id_raw)
    return fail("secondary_owner_comparison_read_unavailable");
  secondary.owner_matches = *out.current_character_full_id_raw == *secondary.diac_owner_full_id_raw;
  if (!*secondary.owner_matches) { out.selected_family = "none"; return finish(); }
  secondary.rule_character_full_id_raw = out.current_character_full_id_raw;
  secondary.rule = Rule(b, *out.current_character_full_id_raw);
  if (!secondary.rule->result) return fail(secondary.rule->reason);
  if (!*secondary.rule->result) { out.selected_family = "none"; return finish(); }
  out.selected_family = "secondary_658";
  selected_numeric(diac, At(character, 0x18), 0x658);
  return finish();
}
} // namespace xar::ck3_12003
