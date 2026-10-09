#include "xar_bridge/ck3_12004_person_government_gate.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <sstream>

namespace xar::ck3_12004 {
namespace {

// Source first: battle-person-next-returned-flags-12004.md. Reused complete
// actual237B getter28C2DF0 and actual20B caller gate291CE01; no delta binder.
constexpr std::uintptr_t kCharacterRegistry = 0x5C67568;
constexpr std::uintptr_t kCharacterFallback = 0x5C67570;
constexpr std::uintptr_t kGovernmentFallback = 0x5D1E2A8;
constexpr std::uint32_t kCharacterMagic = 0x43686172;

template <typename T>
std::optional<T> Copy(const PersonCarrierDirect12004Bindings &b,
                     std::uintptr_t address) {
  T value{};
  if (!b.read_memory || !b.read_memory(b.read_context,
      reinterpret_cast<const void *>(address), &value, sizeof(value)))
    return std::nullopt;
  return value;
}

void String(std::ostringstream &out, std::string_view text) {
  constexpr char hex[] = "0123456789abcdef";
  out << '"';
  for (const unsigned char ch : text) {
    if (ch == '"' || ch == '\\') out << '\\' << static_cast<char>(ch);
    else if (ch < 0x20) out << "\\u00" << hex[ch >> 4] << hex[ch & 15];
    else out << static_cast<char>(ch);
  }
  out << '"';
}

template <typename T>
void Number(std::ostringstream &out, const std::optional<T> &value) {
  if (value) out << *value;
  else out << "null";
}
void Pointer(std::ostringstream &out,
             const std::optional<std::uintptr_t> &value) {
  if (value) out << '"' << "0x" << std::hex << *value << std::dec << '"';
  else out << "null";
}
void Boolean(std::ostringstream &out, const std::optional<bool> &value) {
  if (value) out << (*value ? "true" : "false");
  else out << "null";
}

} // namespace

PersonGovernmentGate12004DTO ReadPersonGovernmentGateForCharacter12004(
    const PersonCarrierDirect12004Bindings &b, std::uintptr_t character) {
  PersonGovernmentGate12004DTO dto;
  dto.build_version = kGameVersion;
  dto.executable_sha256 = kExecutableSha256;
  dto.character_identity = character;
  if (!b.enabled || !b.read_memory || b.current_context_getter_identity !=
          b.module_base + kPersonCarrierContextGetterRva12004) {
    dto.reason = "exact_build_binding_unavailable";
    return dto;
  }
  if (character == 0) {
    dto.reason = "requested_character_unavailable";
    return dto;
  }
  dto.character_id = Copy<std::uint32_t>(b, character + 0x18);
  // This independent Character gate does not demand the preceding PC leaf.
  const auto scratch = Copy<std::uintptr_t>(b, character + 0x1B0);
  if (scratch && *scratch != 0) {
    dto.selected_model_identity = Copy<std::uintptr_t>(b, *scratch + 0x258);
    if (dto.selected_model_identity && *dto.selected_model_identity != 0) {
      const auto owner = Copy<std::uintptr_t>(b, *dto.selected_model_identity + 8);
      if (owner) dto.model_owner_matches = *owner == character;
    }
  }
  dto.registry_identity = Copy<std::uintptr_t>(b, b.module_base + kCharacterRegistry);
  dto.character_fallback_identity = Copy<std::uintptr_t>(b, b.module_base + kCharacterFallback);

  auto current = character;
  for (;;) {
    dto.steps.emplace_back();
    auto &step = dto.steps.back();
    step.native_index = static_cast<std::uint32_t>(dto.steps.size() - 1);
    step.character_identity = current;
    if (current == 0) {
      dto.reason = "selected_character_unavailable";
      return dto;
    }
    step.magic_u32 = Copy<std::uint32_t>(b, current + 0x1C);
    if (!step.magic_u32) {
      dto.reason = "character_magic_unread";
      return dto;
    }
    bool invalid = *step.magic_u32 != kCharacterMagic;
    if (!invalid) {
      step.full_id_u32 = Copy<std::uint32_t>(b, current + 0x18);
      if (!step.full_id_u32) {
        dto.reason = "character_full_id_unread";
        return dto;
      }
      invalid = *step.full_id_u32 == 0xFFFFFFFFU;
    }
    if (invalid) {
      dto.selection = "invalid_character_fallback";
      dto.government_identity = Copy<std::uintptr_t>(b, b.module_base + kGovernmentFallback);
      break;
    }
    step.death_context_identity = Copy<std::uintptr_t>(b, current + 0x1D0);
    if (!step.death_context_identity) {
      dto.reason = "death_context_unread";
      return dto;
    }
    if (*step.death_context_identity != 0) {
      dto.selection = "death_context";
      dto.government_identity = Copy<std::uintptr_t>(b, *step.death_context_identity + 0x88);
      break;
    }
    step.living_context_identity = Copy<std::uintptr_t>(b, current + 0x1C0);
    if (!step.living_context_identity) {
      dto.reason = "living_context_unread";
      return dto;
    }
    if (*step.living_context_identity != 0) {
      dto.selection = "living_context";
      dto.government_identity = Copy<std::uintptr_t>(b, *step.living_context_identity + 0x3F8);
      break;
    }
    step.related_context_identity = Copy<std::uintptr_t>(b, current + 0x1B8);
    if (!step.related_context_identity) {
      dto.reason = "related_context_unread";
      return dto;
    }
    step.related_full_id_u32 = *step.related_context_identity == 0
        ? std::optional<std::uint32_t>(0xFFFFFFFFU)
        : Copy<std::uint32_t>(b, *step.related_context_identity + 0xC8);
    if (!step.related_full_id_u32) {
      dto.reason = "related_full_id_unread";
      return dto;
    }
    if (!dto.registry_identity) {
      dto.reason = "character_registry_unread";
      return dto;
    }
    bool fallback = *dto.registry_identity == 0;
    if (!fallback) {
      step.registry_count_u32 = Copy<std::uint32_t>(b, *dto.registry_identity + 0x2C);
      if (!step.registry_count_u32) {
        dto.reason = "character_registry_count_unread";
        return dto;
      }
      const auto index = *step.related_full_id_u32 & 0xFFFFFFU;
      fallback = index >= *step.registry_count_u32;
      if (!fallback) {
        step.registry_slots_identity = Copy<std::uintptr_t>(b, *dto.registry_identity + 0x20);
        if (!step.registry_slots_identity) {
          dto.reason = "character_registry_slots_unread";
          return dto;
        }
        step.candidate_identity = Copy<std::uintptr_t>(b,
            *step.registry_slots_identity + static_cast<std::uintptr_t>(index) * 16 + 8);
        if (!step.candidate_identity) {
          dto.reason = "character_registry_candidate_unread";
          return dto;
        }
        fallback = *step.candidate_identity == 0;
        if (!fallback) {
          step.candidate_full_id_u32 = Copy<std::uint32_t>(b, *step.candidate_identity + 0x18);
          if (!step.candidate_full_id_u32) {
            dto.reason = "candidate_full_id_unread";
            return dto;
          }
          fallback = *step.candidate_full_id_u32 != *step.related_full_id_u32;
        }
      }
    }
    if (fallback) {
      step.resolution_selection = "fallback";
      if (!dto.character_fallback_identity) {
        dto.reason = "character_fallback_unread";
        return dto;
      }
      step.selected_character_identity = dto.character_fallback_identity;
    } else {
      step.resolution_selection = "mapped";
      step.selected_character_identity = step.candidate_identity;
    }
    current = *step.selected_character_identity;
  }
  if (!dto.government_identity) {
    dto.reason = "government_pointer_unread";
    return dto;
  }
  if (*dto.government_identity == 0 && dto.selection != "invalid_character_fallback") {
    dto.selection = "selected_null_fallback";
    dto.government_identity = Copy<std::uintptr_t>(b, b.module_base + kGovernmentFallback);
    if (!dto.government_identity) {
      dto.reason = "government_fallback_unread";
      return dto;
    }
  }
  if (*dto.government_identity == 0) {
    dto.reason = "government_return_null";
    return dto;
  }
  dto.flags_40_u32 = Copy<std::uint32_t>(b, *dto.government_identity + 0x40);
  if (!dto.flags_40_u32) {
    dto.reason = "government_flags_unread";
    return dto;
  }
  dto.bit19_set = ((*dto.flags_40_u32 >> 19) & 1U) != 0;
  dto.branch_admitted = dto.bit19_set;
  dto.known_no_contribution = !*dto.bit19_set;
  dto.ready = true;
  return dto;
}

std::string SerializePersonGovernmentGate12004(const PersonGovernmentGate12004DTO &dto) {
  std::ostringstream out;
  out << "{\"schema\":"; String(out, kPersonGovernmentGate12004Schema);
  out << ",\"build_version\":"; String(out, dto.build_version);
  out << ",\"executable_sha256\":"; String(out, dto.executable_sha256);
  out << ",\"ready\":" << (dto.ready ? "true" : "false") << ",\"reason\":";
  if (dto.reason.empty()) out << "null"; else String(out, dto.reason);
  out << ",\"character_id\":"; Number(out, dto.character_id);
  out << ",\"character_identity\":"; Pointer(out, dto.character_identity);
  out << ",\"selected_model_identity\":"; Pointer(out, dto.selected_model_identity);
  out << ",\"model_owner_matches\":"; Boolean(out, dto.model_owner_matches);
  out << ",\"registry_identity\":"; Pointer(out, dto.registry_identity);
  out << ",\"character_fallback_identity\":"; Pointer(out, dto.character_fallback_identity);
  out << ",\"government_identity\":"; Pointer(out, dto.government_identity);
  out << ",\"selection\":"; String(out, dto.selection);
  out << ",\"flags_40_u32\":"; Number(out, dto.flags_40_u32);
  out << ",\"bit19_set\":"; Boolean(out, dto.bit19_set);
  out << ",\"branch_admitted\":"; Boolean(out, dto.branch_admitted);
  out << ",\"known_no_contribution\":"; Boolean(out, dto.known_no_contribution);
  out << ",\"steps\":[";
  bool first = true;
  for (const auto &s : dto.steps) {
    if (!first) out << ',';
    first = false;
    out << "{\"native_index\":" << s.native_index << ",\"character_identity\":";
    Pointer(out, s.character_identity);
    out << ",\"magic_u32\":"; Number(out, s.magic_u32);
    out << ",\"full_id_u32\":"; Number(out, s.full_id_u32);
    out << ",\"death_context_identity\":"; Pointer(out, s.death_context_identity);
    out << ",\"living_context_identity\":"; Pointer(out, s.living_context_identity);
    out << ",\"related_context_identity\":"; Pointer(out, s.related_context_identity);
    out << ",\"related_full_id_u32\":"; Number(out, s.related_full_id_u32);
    out << ",\"registry_count_u32\":"; Number(out, s.registry_count_u32);
    out << ",\"registry_slots_identity\":"; Pointer(out, s.registry_slots_identity);
    out << ",\"candidate_identity\":"; Pointer(out, s.candidate_identity);
    out << ",\"candidate_full_id_u32\":"; Number(out, s.candidate_full_id_u32);
    out << ",\"selected_character_identity\":"; Pointer(out, s.selected_character_identity);
    out << ",\"resolution_selection\":"; String(out, s.resolution_selection);
    out << '}';
  }
  out << "]}";
  return out.str();
}

} // namespace xar::ck3_12004
