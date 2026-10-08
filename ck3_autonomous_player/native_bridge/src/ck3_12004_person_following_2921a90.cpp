#include "xar_bridge/ck3_12004_person_following_2921a90.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <sstream>
#include <utility>

namespace xar::ck3_12004 {
namespace {
// Source-first contract: battle-person-following-2921a90-12004.md and the
// sealed person-after-carrier41/QUERY-CONTRACT.json. Actual callsite11B and
// complete body1467B; current4 PC layout and owned Model association reused.
template <typename T>
std::optional<T> Copy(const PersonCarrierDirect12004Bindings &b,
                      std::uintptr_t address) {
  T value{};
  if (!b.read_memory || !b.read_memory(b.read_context,
      reinterpret_cast<const void *>(address), &value, sizeof(value)))
    return std::nullopt;
  return value;
}

PersonFollowing2921a90DTO Initial() {
  PersonFollowing2921a90DTO dto;
  dto.build_version = kGameVersion;
  dto.executable_sha256 = kExecutableSha256;
  return dto;
}
void Unavailable(PersonFollowing2921a90DTO &dto, const char *reason) {
  dto.reason = reason;
  dto.direct_reason = reason;
  dto.conditional_reason = reason;
}
void KnownGateFalse(PersonFollowing2921a90DTO &dto) {
  dto.admitted = false;
  dto.ready = true;
  dto.direct_ready = true;
  dto.conditional_ready = true;
  dto.conditional_occurrence_count = 0U;
}

template <typename T>
std::optional<std::vector<T>> CopyArray(
    const PersonCarrierDirect12004Bindings &b,
    const std::optional<std::uintptr_t> &address, std::int32_t count) {
  if (!address || *address == 0) return std::nullopt;
  std::vector<T> values(static_cast<std::size_t>(count));
  if (!b.read_memory(b.read_context, reinterpret_cast<const void *>(*address),
                     values.data(), values.size() * sizeof(T))) return std::nullopt;
  return values;
}

void CopyPc(const PersonCarrierDirect12004Bindings &b,
            PersonFollowing2921a90Row &row) {
  const auto pc = *row.source_pc_identity;
  row.pc_count_i32 = Copy<std::int32_t>(b, pc + 0xC);
  if (!row.pc_count_i32) { row.reason = "pc_count_unread"; return; }
  const auto count = *row.pc_count_i32;
  if (count < 0) { row.reason = "pc_count_negative"; return; }
  row.properties.emplace();
  if (count == 0) {
    row.properties->keys_u16.emplace();
    row.properties->values_q64.emplace();
    row.ready = true;
    return;
  }
  const auto keys = Copy<std::uintptr_t>(b, pc);
  const auto values = Copy<std::uintptr_t>(b, pc + 0x68);
  row.properties->keys_u16 = CopyArray<std::uint16_t>(b, keys, count);
  row.properties->values_q64 = CopyArray<std::int64_t>(b, values, count);
  if (!row.properties->keys_u16 && !row.properties->values_q64)
    row.reason = "pc_keys_and_values_unread";
  else if (!row.properties->keys_u16) row.reason = "pc_keys_unread";
  else if (!row.properties->values_q64) row.reason = "pc_values_unread";
  else row.ready = true;
}

void CopyDirect(const PersonCarrierDirect12004Bindings &b,
                PersonFollowing2921a90DTO &dto, std::uintptr_t object) {
  dto.direct_array_identity = Copy<std::uintptr_t>(b, object + 0x60);
  dto.direct_count_i32 = Copy<std::int32_t>(b, object + 0x6C);
  if (!dto.direct_count_i32) { dto.direct_reason = "direct_count_unread"; return; }
  const auto count = *dto.direct_count_i32;
  if (count < 0) { dto.direct_reason = "direct_count_negative"; return; }
  if (!dto.direct_array_identity) { dto.direct_reason = "direct_array_unread"; return; }
  if (count == 0) { dto.direct_ready = true; return; }
  if (*dto.direct_array_identity == 0) { dto.direct_reason = "direct_array_unread"; return; }
  dto.direct_ready = true;
  for (std::uint32_t index = 0; index < static_cast<std::uint32_t>(count); ++index) {
    PersonFollowing2921a90Row row;
    row.native_index = index;
    row.object_identity = Copy<std::uintptr_t>(
        b, *dto.direct_array_identity + static_cast<std::uintptr_t>(index) * 8);
    if (!row.object_identity || *row.object_identity == 0) row.reason = "pc_object_unread";
    else {
      row.source_pc_identity = *row.object_identity + 0x1778;
      CopyPc(b, row);
    }
    if (!row.ready) dto.direct_ready = false;
    dto.direct_rows.push_back(std::move(row));
  }
  if (!dto.direct_ready) dto.direct_reason = "direct_rows_partial";
}

void CopyConditional(const PersonCarrierDirect12004Bindings &b,
                     PersonFollowing2921a90DTO &dto, std::uintptr_t object) {
  dto.conditional_definition_identity = Copy<std::uintptr_t>(b, object + 0x30);
  if (!dto.conditional_definition_identity || *dto.conditional_definition_identity == 0) {
    dto.conditional_reason = "conditional_definition_unread";
    return;
  }
  const auto definition = *dto.conditional_definition_identity;
  dto.conditional_b8c_count_i32 = Copy<std::int32_t>(b, definition + 0xB8C);
  if (!dto.conditional_b8c_count_i32) {
    dto.conditional_reason = "conditional_b8c_count_unread";
    return;
  }
  if (*dto.conditional_b8c_count_i32 == 0) {
    dto.conditional_bbc_count_i32 = Copy<std::int32_t>(b, definition + 0xBBC);
    if (!dto.conditional_bbc_count_i32) {
      dto.conditional_reason = "conditional_bbc_count_unread";
      return;
    }
    if (*dto.conditional_bbc_count_i32 == 0) {
      dto.conditional_ready = true;
      dto.conditional_occurrence_count = 0U;
      return;
    }
  }
  dto.conditional_reason = "conditional_modifier_2a38030_2872300_unobserved";
}

void String(std::ostream &out, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  out << '"';
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') out << '\\' << static_cast<char>(c);
    else if (c < 0x20) out << "\\u00" << hex[c >> 4] << hex[c & 0xF];
    else out << static_cast<char>(c);
  }
  out << '"';
}
void Reason(std::ostream &out, std::string_view value) {
  if (value.empty()) out << "null";
  else String(out, value);
}
template <typename T> void Number(std::ostream &out, const std::optional<T> &value) {
  if (value) out << *value;
  else out << "null";
}
void Pointer(std::ostream &out, const std::optional<std::uintptr_t> &value) {
  if (!value) { out << "null"; return; }
  out << "\"0x" << std::hex << *value << std::dec << '"';
}
void Bool(std::ostream &out, const std::optional<bool> &value) {
  if (value) out << (*value ? "true" : "false");
  else out << "null";
}
template <typename T>
void Array(std::ostream &out, const std::optional<std::vector<T>> &values,
           bool decimal_strings) {
  if (!values) { out << "null"; return; }
  out << '[';
  bool first = true;
  for (const auto value : *values) {
    if (!first) out << ',';
    first = false;
    if (decimal_strings) out << '"';
    out << value;
    if (decimal_strings) out << '"';
  }
  out << ']';
}
void Properties(std::ostream &out,
                const std::optional<PersonCarrierDirect12004Properties> &properties) {
  if (!properties) { out << "null"; return; }
  out << "{\"keys_u16\":"; Array(out, properties->keys_u16, false);
  out << ",\"values_q64\":"; Array(out, properties->values_q64, true);
  out << '}';
}
} // namespace

PersonFollowing2921a90DTO ReadPersonFollowing2921a90ForModel12004(
    const PersonCarrierDirect12004Bindings &b, std::uintptr_t actual_model) {
  static_assert(sizeof(std::uintptr_t) == 8, "actual4 object pointers are QWORDs");
  auto dto = Initial();
  dto.selected_model_identity = actual_model;
  if (!b.enabled || !b.read_memory) { Unavailable(dto, "exact_build_binding_unavailable"); return dto; }
  if (actual_model == 0) { Unavailable(dto, "actual_model_unavailable"); return dto; }
  dto.destination_pc_identity = actual_model + 0x10;
  dto.character_identity = Copy<std::uintptr_t>(b, actual_model + 8);
  if (!dto.character_identity || *dto.character_identity == 0) {
    Unavailable(dto, "model_character_unread"); return dto;
  }
  const auto character = *dto.character_identity;
  dto.character_id = Copy<std::uint32_t>(b, character + kCharacterFullIdOffset);
  dto.carrier_identity = Copy<std::uintptr_t>(b, character + 0x1C8);
  if (!dto.carrier_identity) { Unavailable(dto, "character_carrier_unread"); return dto; }
  dto.carrier_present = *dto.carrier_identity != 0;
  if (*dto.carrier_present)
    dto.requested_full_id_u32 = Copy<std::uint32_t>(b, *dto.carrier_identity + 0xB68);
  else dto.requested_full_id_u32 = 0xFFFFFFFFU;
  if (!dto.requested_full_id_u32) { Unavailable(dto, "requested_full_id_unread"); return dto; }
  dto.registry_identity = Copy<std::uintptr_t>(b, b.module_base + kPersonFollowing2921a90RegistryRva);
  if (!dto.registry_identity) { Unavailable(dto, "registry_slot_unread"); return dto; }
  std::optional<std::uint32_t> mapped_full_id;
  bool fallback = *dto.registry_identity == 0;
  if (!fallback) {
    const auto registry = *dto.registry_identity;
    dto.registry_count_u32 = Copy<std::uint32_t>(b, registry + 0x2C);
    if (!dto.registry_count_u32) { Unavailable(dto, "registry_count_unread"); return dto; }
    const auto index = *dto.requested_full_id_u32 & 0xFFFFFFU;
    fallback = index >= *dto.registry_count_u32;
    if (!fallback) {
      dto.registry_slots_identity = Copy<std::uintptr_t>(b, registry + 0x20);
      if (!dto.registry_slots_identity || *dto.registry_slots_identity == 0) {
        Unavailable(dto, "registry_slots_unread"); return dto;
      }
      const auto candidate = Copy<std::uintptr_t>(
          b, *dto.registry_slots_identity + static_cast<std::uintptr_t>(index) * 16 + 8);
      if (!candidate) { Unavailable(dto, "registry_candidate_unread"); return dto; }
      fallback = *candidate == 0;
      if (!fallback) {
        mapped_full_id = Copy<std::uint32_t>(b, *candidate + 8);
        if (!mapped_full_id) { Unavailable(dto, "registry_candidate_id_unread"); return dto; }
        fallback = *mapped_full_id != *dto.requested_full_id_u32;
        if (!fallback) dto.selected_object_identity = *candidate;
      }
    }
  }
  if (fallback) {
    dto.resolution_selection = "fallback";
    dto.selected_object_identity = Copy<std::uintptr_t>(
        b, b.module_base + kPersonFollowing2921a90FallbackRva);
    if (!dto.selected_object_identity || *dto.selected_object_identity == 0) {
      Unavailable(dto, "fallback_object_unread"); return dto;
    }
  } else dto.resolution_selection = "mapped_id";
  const auto object = *dto.selected_object_identity;
  dto.selected_magic_u32 = Copy<std::uint32_t>(b, object + 0xC);
  if (!dto.selected_magic_u32) { Unavailable(dto, "selected_magic_unread"); return dto; }
  if (*dto.selected_magic_u32 != 0x446F6D69U) { KnownGateFalse(dto); return dto; }
  dto.selected_full_id_u32 = fallback ? Copy<std::uint32_t>(b, object + 8) : mapped_full_id;
  if (!dto.selected_full_id_u32) { Unavailable(dto, "selected_full_id_unread"); return dto; }
  if (*dto.selected_full_id_u32 == 0xFFFFFFFFU) { KnownGateFalse(dto); return dto; }
  dto.admitted = true;
  CopyDirect(b, dto, object);
  CopyConditional(b, dto, object);
  dto.ready = dto.direct_ready && dto.conditional_ready;
  dto.reason = !dto.direct_ready ? dto.direct_reason : dto.conditional_reason;
  return dto;
}

PersonFollowing2921a90DTO ReadPersonFollowing2921a90ForCharacter12004(
    const PersonCarrierDirect12004Bindings &b, std::uintptr_t actual_character) {
  auto dto = Initial();
  dto.character_identity = actual_character;
  if (!b.enabled || !b.read_memory) { Unavailable(dto, "exact_build_binding_unavailable"); return dto; }
  if (actual_character == 0) { Unavailable(dto, "actual_character_unavailable"); return dto; }
  dto.character_id = Copy<std::uint32_t>(b, actual_character + kCharacterFullIdOffset);
  const auto scratch = Copy<std::uintptr_t>(b, actual_character + 0x1B0);
  if (!scratch || *scratch == 0) { Unavailable(dto, "owned_scratch_unread"); return dto; }
  const auto model = Copy<std::uintptr_t>(b, *scratch + 0x258);
  if (!model || *model == 0) { Unavailable(dto, "owned_model_unread"); return dto; }
  dto.selected_model_identity = *model;
  dto.destination_pc_identity = *model + 0x10;
  const auto owner = Copy<std::uintptr_t>(b, *model + 8);
  if (!owner) { Unavailable(dto, "owned_model_character_unread"); return dto; }
  if (*owner != actual_character) { Unavailable(dto, "owned_model_character_mismatch"); return dto; }
  return ReadPersonFollowing2921a90ForModel12004(b, *model);
}

std::string SerializePersonFollowing2921a90(const PersonFollowing2921a90DTO &dto) {
  std::ostringstream out;
  out << "{\"schema\":"; String(out, kPersonFollowing2921a90Schema);
  out << ",\"build_version\":"; String(out, dto.build_version);
  out << ",\"executable_sha256\":"; String(out, dto.executable_sha256);
  out << ",\"ready\":" << (dto.ready ? "true" : "false");
  out << ",\"reason\":"; Reason(out, dto.reason);
  out << ",\"character_id\":"; Number(out, dto.character_id);
  out << ",\"selected_model_identity\":"; Pointer(out, dto.selected_model_identity);
  out << ",\"character_identity\":"; Pointer(out, dto.character_identity);
  out << ",\"destination_pc_identity\":"; Pointer(out, dto.destination_pc_identity);
  out << ",\"carrier_present\":"; Bool(out, dto.carrier_present);
  out << ",\"carrier_identity\":"; Pointer(out, dto.carrier_identity);
  out << ",\"requested_full_id_u32\":"; Number(out, dto.requested_full_id_u32);
  out << ",\"registry_identity\":"; Pointer(out, dto.registry_identity);
  out << ",\"registry_count_u32\":"; Number(out, dto.registry_count_u32);
  out << ",\"registry_slots_identity\":"; Pointer(out, dto.registry_slots_identity);
  out << ",\"resolution_selection\":"; String(out, dto.resolution_selection);
  out << ",\"selected_object_identity\":"; Pointer(out, dto.selected_object_identity);
  out << ",\"selected_full_id_u32\":"; Number(out, dto.selected_full_id_u32);
  out << ",\"selected_magic_u32\":"; Number(out, dto.selected_magic_u32);
  out << ",\"admitted\":"; Bool(out, dto.admitted);
  out << ",\"direct_ready\":" << (dto.direct_ready ? "true" : "false");
  out << ",\"direct_reason\":"; Reason(out, dto.direct_reason);
  out << ",\"direct_array_identity\":"; Pointer(out, dto.direct_array_identity);
  out << ",\"direct_count_i32\":"; Number(out, dto.direct_count_i32);
  out << ",\"direct_rows\":[";
  bool first = true;
  for (const auto &row : dto.direct_rows) {
    if (!first) out << ',';
    first = false;
    out << "{\"native_index\":" << row.native_index;
    out << ",\"ready\":" << (row.ready ? "true" : "false");
    out << ",\"reason\":"; Reason(out, row.reason);
    out << ",\"object_identity\":"; Pointer(out, row.object_identity);
    out << ",\"source_pc_identity\":"; Pointer(out, row.source_pc_identity);
    out << ",\"pc_count_i32\":"; Number(out, row.pc_count_i32);
    out << ",\"properties\":"; Properties(out, row.properties);
    out << ",\"weight_q100000\":" << row.weight_q100000 << '}';
  }
  out << ']';
  out << ",\"conditional_ready\":" << (dto.conditional_ready ? "true" : "false");
  out << ",\"conditional_reason\":"; Reason(out, dto.conditional_reason);
  out << ",\"conditional_definition_identity\":"; Pointer(out, dto.conditional_definition_identity);
  out << ",\"conditional_b8c_count_i32\":"; Number(out, dto.conditional_b8c_count_i32);
  out << ",\"conditional_bbc_count_i32\":"; Number(out, dto.conditional_bbc_count_i32);
  out << ",\"conditional_occurrence_count\":"; Number(out, dto.conditional_occurrence_count);
  out << '}';
  return out.str();
}
} // namespace xar::ck3_12004
