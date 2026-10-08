#include "xar_bridge/ck3_12004_person_carrier_direct.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <sstream>
#include <utility>

namespace xar::ck3_12004 {
namespace {

// Source-before-code: battle-person-next-direct-carrier-12004.md, including
// its October 9 closure. Actual caller291CD93..291CDEB, fallback31937A0,
// pc-decoder-source03's six concrete field/argument windows; total328B.
// This observes their raw source inputs, not merger arithmetic or full Entry.
template <typename T>
std::optional<T> Copy(const PersonCarrierDirect12004Bindings &bindings,
                      std::uintptr_t address) {
  T value{};
  if (bindings.read_memory == nullptr ||
      !bindings.read_memory(bindings.read_context,
                            reinterpret_cast<const void *>(address),
                            &value, sizeof(value))) {
    return std::nullopt;
  }
  return value;
}

void KnownZero(PersonCarrierDirect12004DTO &dto) {
  dto.ready = true;
  dto.reason.clear();
  dto.source_occurrence_count = 0;
}

template <typename T>
std::optional<std::vector<T>> CopyArray(
    const PersonCarrierDirect12004Bindings &bindings,
    const std::optional<std::uintptr_t> &address, std::int32_t count) {
  if (!address || *address == 0) return std::nullopt;
  std::vector<T> values(static_cast<std::size_t>(count));
  if (!bindings.read_memory(bindings.read_context,
                            reinterpret_cast<const void *>(*address),
                            values.data(), values.size() * sizeof(T))) {
    return std::nullopt;
  }
  return values;
}

// Returns the demanded numerical-copy gap, while retaining independent copies.
std::string CopySelectedPc(const PersonCarrierDirect12004Bindings &bindings,
                           PersonCarrierDirect12004DTO &dto) {
  const auto pc = *dto.selected_pc_identity;
  dto.selected_pc_count_i32 = Copy<std::int32_t>(bindings, pc + 0xC);
  if (!dto.selected_pc_count_i32) return "selected_pc_count_unread";
  const auto count = *dto.selected_pc_count_i32;
  if (count < 0) return "selected_pc_count_negative";
  dto.properties.emplace();
  if (count == 0) {
    dto.properties->keys_u16.emplace();
    dto.properties->values_q64.emplace();
    return {};
  }
  const auto keys = Copy<std::uintptr_t>(bindings, pc + 0);
  const auto values = Copy<std::uintptr_t>(bindings, pc + 0x68);
  dto.properties->keys_u16 = CopyArray<std::uint16_t>(bindings, keys, count);
  dto.properties->values_q64 = CopyArray<std::int64_t>(bindings, values, count);
  if (!dto.properties->keys_u16 && !dto.properties->values_q64)
    return "selected_pc_keys_and_values_unread";
  if (!dto.properties->keys_u16) return "selected_pc_keys_unread";
  if (!dto.properties->values_q64) return "selected_pc_values_unread";
  return {};
}

void String(std::ostream &out, std::string_view value) {
  static constexpr char hex[] = "0123456789abcdef";
  out << '"';
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') out << '\\' << static_cast<char>(c);
    else if (c < 0x20) out << "\\u00" << hex[c >> 4] << hex[c & 0xF];
    else out << static_cast<char>(c);
  }
  out << '"';
}

template <typename T>
void Number(std::ostream &out, const std::optional<T> &value) {
  if (value) out << *value;
  else out << "null";
}

void Pointer(std::ostream &out,
             const std::optional<std::uintptr_t> &value) {
  if (!value) { out << "null"; return; }
  out << "\"0x" << std::hex << *value << std::dec << '"';
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
} // namespace

PersonCarrierDirect12004Bindings BindPersonCarrierDirect12004(
    std::uintptr_t module_base, std::string_view build_version,
    std::string_view executable_sha256,
    PersonCarrierDirect12004ReadMemory read_memory,
    void *read_context) noexcept {
  PersonCarrierDirect12004Bindings bindings;
  if (module_base == 0 || build_version != kGameVersion ||
      executable_sha256 != kExecutableSha256 || read_memory == nullptr) {
    return bindings;
  }
  bindings.enabled = true;
  bindings.module_base = module_base;
  bindings.read_memory = read_memory;
  bindings.read_context = read_context;
  return bindings;
}

PersonCarrierDirect12004DTO ReadPersonCarrierDirect12004(
    const PersonCarrierDirect12004Bindings &bindings,
    std::uintptr_t actual_model) {
  static_assert(sizeof(std::uintptr_t) == 8, "actual4 PC pointers are QWORDs");
  PersonCarrierDirect12004DTO dto;
  dto.build_version = kGameVersion;
  dto.executable_sha256 = kExecutableSha256;
  dto.selected_model_identity = actual_model;
  if (!bindings.enabled || bindings.read_memory == nullptr) {
    dto.reason = "exact_build_binding_unavailable";
    return dto;
  }
  if (actual_model == 0) {
    dto.reason = "actual_model_unavailable";
    return dto;
  }
  dto.destination_pc_identity = actual_model + 0x10;
  dto.character_identity = Copy<std::uintptr_t>(bindings, actual_model + 8);
  if (!dto.character_identity || *dto.character_identity == 0) {
    dto.reason = "model_character_unread";
    return dto;
  }
  const auto character = *dto.character_identity;
  dto.character_id = Copy<std::uint32_t>(
      bindings, character + kCharacterFullIdOffset);
  dto.carrier_identity = Copy<std::uintptr_t>(bindings, character + 0x1C8);
  if (!dto.carrier_identity) {
    dto.reason = "character_carrier_unread";
    return dto;
  }
  dto.carrier_present = *dto.carrier_identity != 0;
  if (!*dto.carrier_present) {
    dto.selection = "none";
    KnownZero(dto);
    return dto;
  }
  const auto carrier = *dto.carrier_identity;
  dto.definition_identity = Copy<std::uintptr_t>(bindings, carrier + 0x20);
  if (!dto.definition_identity || *dto.definition_identity == 0) {
    dto.reason = "definition_magic_unread";
    return dto;
  }
  const auto definition = *dto.definition_identity;
  dto.definition_magic_u32 = Copy<std::uint32_t>(bindings, definition + 0x38);
  if (!dto.definition_magic_u32) {
    dto.reason = "definition_magic_unread";
    return dto;
  }
  if (*dto.definition_magic_u32 != 0x4744624FU) {
    dto.selection = "none";
    KnownZero(dto);
    return dto;
  }
  dto.rank_i32 = Copy<std::int32_t>(bindings, carrier + 0xB70);
  if (!dto.rank_i32) {
    dto.reason = "carrier_rank_unread";
    return dto;
  }
  bool fallback = *dto.rank_i32 < 0;
  if (!fallback) {
    dto.row_count_i32 = Copy<std::int32_t>(bindings, definition + 0x3E4);
    if (!dto.row_count_i32) {
      dto.reason = "definition_row_count_unread";
      return dto;
    }
    fallback = *dto.rank_i32 >= *dto.row_count_i32;
  }
  std::string initialization_gap;
  if (fallback) {
    dto.selection = "static_default_5d71200";
    dto.selected_pc_identity = bindings.module_base + kPersonCarrierDefaultPcRva12004;
    dto.default_guard_raw = Copy<std::int32_t>(
        bindings, bindings.module_base + kPersonCarrierDefaultGuardRva12004);
    if (!dto.default_guard_raw) initialization_gap = "fallback_default_guard_unread";
    else if (*dto.default_guard_raw == 0 || *dto.default_guard_raw == -1)
      initialization_gap = "fallback_31937a0_default_initialization_unobserved";
  } else {
    dto.table_identity = Copy<std::uintptr_t>(bindings, definition + 0x3D8);
    if (!dto.table_identity || *dto.table_identity == 0) {
      dto.reason = "definition_table_unread";
      return dto;
    }
    dto.selection = "mapped_row";
    dto.selected_pc_identity = *dto.table_identity +
        static_cast<std::uintptr_t>(*dto.rank_i32) * 0x340;
  }
  const auto numerical_gap = CopySelectedPc(bindings, dto);
  dto.reason = initialization_gap.empty() ? numerical_gap : initialization_gap;
  if (!dto.reason.empty()) return dto;
  dto.ready = true;
  dto.source_occurrence_count = *dto.selected_pc_count_i32 == 0 ? 0U : 1U;
  return dto;
}

std::string SerializePersonCarrierDirect12004(
    const PersonCarrierDirect12004DTO &dto) {
  std::ostringstream out;
  out << "{\"schema\":"; String(out, kPersonCarrierDirect12004Schema);
  out << ",\"build_version\":"; String(out, dto.build_version);
  out << ",\"executable_sha256\":"; String(out, dto.executable_sha256);
  out << ",\"ready\":" << (dto.ready ? "true" : "false");
  out << ",\"reason\":";
  if (dto.reason.empty()) out << "null";
  else String(out, dto.reason);
  out << ",\"character_id\":"; Number(out, dto.character_id);
  out << ",\"selected_model_identity\":"; Pointer(out, dto.selected_model_identity);
  out << ",\"character_identity\":"; Pointer(out, dto.character_identity);
  out << ",\"destination_pc_identity\":"; Pointer(out, dto.destination_pc_identity);
  out << ",\"carrier_present\":";
  if (dto.carrier_present) out << (*dto.carrier_present ? "true" : "false");
  else out << "null";
  out << ",\"carrier_identity\":"; Pointer(out, dto.carrier_identity);
  out << ",\"definition_identity\":"; Pointer(out, dto.definition_identity);
  out << ",\"definition_magic_u32\":"; Number(out, dto.definition_magic_u32);
  out << ",\"rank_i32\":"; Number(out, dto.rank_i32);
  out << ",\"row_count_i32\":"; Number(out, dto.row_count_i32);
  out << ",\"table_identity\":"; Pointer(out, dto.table_identity);
  out << ",\"selection\":"; String(out, dto.selection);
  out << ",\"default_guard_raw\":"; Number(out, dto.default_guard_raw);
  out << ",\"selected_pc_identity\":"; Pointer(out, dto.selected_pc_identity);
  out << ",\"selected_pc_count_i32\":"; Number(out, dto.selected_pc_count_i32);
  out << ",\"properties\":";
  if (dto.properties) {
    out << "{\"keys_u16\":"; Array(out, dto.properties->keys_u16, false);
    out << ",\"values_q64\":"; Array(out, dto.properties->values_q64, true);
    out << '}';
  } else out << "null";
  out << ",\"source_occurrence_count\":"; Number(out, dto.source_occurrence_count);
  out << ",\"weight_q100000\":" << dto.weight_q100000 << '}';
  return out.str();
}
} // namespace xar::ck3_12004
