#include "xar_bridge/ck3_12004_person_following_2922680.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_religion_profile.hpp"

#include <bit>
#include <algorithm>
#include <sstream>
#include <utility>

namespace xar::ck3_12004 {
namespace {

// Source before code: battle-person-next-ordered-helper-12004.md. Actual
// caller11B, helper314B, list getter164B, pointer getter112B, row consumer568B,
// participant getter282B (including its cold tail) and membership181B are
// retained Root evidence. Actual243EA10 returns selected Rite+750, not a PC.
// Only admitted42127E0 mappings remain an explicit numerical dependency;
// independently observed primary PCs retain their proved unit100000 calls.
constexpr std::uintptr_t kDefaultHeaderRva = 0x5D67DE0;
constexpr std::uintptr_t kRiteFallbackSlotRva = 0x5C67670;
constexpr std::uintptr_t kContextRegistryRva = 0x5D1E300;
constexpr std::uintptr_t kContextFallbackSlotRva = 0x5D1E2E0;
constexpr std::uintptr_t kRowRegistryRva = 0x5D1ED98;
constexpr std::uintptr_t kRowFallbackSlotRva = 0x5D1ED90;
constexpr std::uintptr_t kSourceRegistryRva = 0x5D1ED80;
constexpr std::uintptr_t kSourceFallbackSlotRva = 0x5D1ED78;
constexpr std::uintptr_t kCurrentGameDataSlotRva = 0x5C68C50;
constexpr std::uintptr_t kGetterValueRegistryRva = 0x5D1FF70;
constexpr std::uintptr_t kGetterFallbackSlotRva = 0x5D1FF78;

template <typename T>
std::optional<T> Copy(const PersonCarrierDirect12004Bindings &b,
                     std::uintptr_t address) {
  T value{};
  if (!b.read_memory || !b.read_memory(b.read_context,
      reinterpret_cast<const void *>(address), &value, sizeof(value)))
    return std::nullopt;
  return value;
}

PersonFollowing2922680DTO Initial() {
  PersonFollowing2922680DTO dto;
  dto.build_version = kGameVersion;
  dto.executable_sha256 = kExecutableSha256;
  return dto;
}

PersonFollowing2922680Resolution Resolve(
    const PersonCarrierDirect12004Bindings &b, std::uintptr_t registry_rva,
    std::uintptr_t fallback_rva, const std::optional<std::uintptr_t> &key_address) {
  PersonFollowing2922680Resolution result;
  result.registry_identity = Copy<std::uintptr_t>(b, b.module_base + registry_rva);
  if (!result.registry_identity) {
    result.reason = "registry_slot_unread";
    return result;
  }
  bool fallback = *result.registry_identity == 0;
  if (!fallback) {
    if (key_address) result.requested_full_id_u32 = Copy<std::uint32_t>(b, *key_address);
    if (!result.requested_full_id_u32) {
      result.reason = "requested_full_id_unread";
      return result;
    }
    const auto registry = *result.registry_identity;
    result.registry_count_u32 = Copy<std::uint32_t>(b, registry + 0x2C);
    if (!result.registry_count_u32) {
      result.reason = "registry_count_unread";
      return result;
    }
    const auto index = *result.requested_full_id_u32 & 0xFFFFFFU;
    fallback = index >= *result.registry_count_u32;
    if (!fallback) {
      result.registry_slots_identity = Copy<std::uintptr_t>(b, registry + 0x20);
      if (!result.registry_slots_identity || *result.registry_slots_identity == 0) {
        result.reason = "registry_slots_unread";
        return result;
      }
      result.candidate_identity = Copy<std::uintptr_t>(
          b, *result.registry_slots_identity + static_cast<std::uintptr_t>(index) * 16 + 8);
      if (!result.candidate_identity) {
        result.reason = "registry_candidate_unread";
        return result;
      }
      fallback = *result.candidate_identity == 0;
      if (!fallback) {
        result.candidate_full_id_u32 = Copy<std::uint32_t>(b, *result.candidate_identity + 8);
        if (!result.candidate_full_id_u32) {
          result.reason = "candidate_full_id_unread";
          return result;
        }
        fallback = *result.candidate_full_id_u32 != *result.requested_full_id_u32;
      }
    }
  }
  if (fallback) {
    result.selection = "fallback";
    result.selected_identity = Copy<std::uintptr_t>(b, b.module_base + fallback_rva);
  } else {
    result.selection = "mapped";
    result.selected_identity = result.candidate_identity;
  }
  if (!result.selected_identity || *result.selected_identity == 0) {
    result.reason = "selected_object_unread";
    return result;
  }
  result.ready = true;
  return result;
}

void ReadSourceOperand(const PersonCarrierDirect12004Bindings &b,
                       PersonFollowing2922680DTO &dto) {
  // Actual243EA10 tests the Rite registry before demanding context98. Its
  // null-registry fallback remains known even if the unused context is unread.
  const auto key_address = dto.context_resolution.ready
      ? std::optional<std::uintptr_t>(*dto.context_resolution.selected_identity + 0x98)
      : std::nullopt;
  dto.operand_rite_resolution = Resolve(b, religion::profile::kRiteStorageSlotRva,
      kRiteFallbackSlotRva, key_address);
  if (!dto.operand_rite_resolution.ready) {
    dto.source_operand_reason = dto.operand_rite_resolution.reason;
    return;
  }
  dto.source_operand_identity = *dto.operand_rite_resolution.selected_identity + 0x750;
  dto.source_operand_ready = true;
}

template <typename T>
std::optional<std::vector<T>> CopyArray(const PersonCarrierDirect12004Bindings &b,
    const std::optional<std::uintptr_t> &address, std::int32_t count) {
  if (!address || *address == 0) return std::nullopt;
  std::vector<T> values(static_cast<std::size_t>(count));
  if (!b.read_memory(b.read_context, reinterpret_cast<const void *>(*address),
                     values.data(), values.size() * sizeof(T))) return std::nullopt;
  return values;
}

void ReadPc(const PersonCarrierDirect12004Bindings &b, std::uintptr_t identity,
            PersonFollowing2922680Pc &pc) {
  pc.admitted = true;
  pc.identity = identity;
  pc.count_i32 = Copy<std::int32_t>(b, identity + 0xC);
  if (!pc.count_i32) { pc.reason = "pc_count_unread"; return; }
  if (*pc.count_i32 < 0) { pc.reason = "pc_count_negative"; return; }
  pc.properties.emplace();
  if (*pc.count_i32 == 0) {
    pc.properties->keys_u16.emplace();
    pc.properties->values_q64.emplace();
    pc.ready = true;
    return;
  }
  const auto keys = Copy<std::uintptr_t>(b, identity);
  const auto values = Copy<std::uintptr_t>(b, identity + 0x68);
  pc.properties->keys_u16 = CopyArray<std::uint16_t>(b, keys, *pc.count_i32);
  pc.properties->values_q64 = CopyArray<std::int64_t>(b, values, *pc.count_i32);
  if (!pc.properties->keys_u16 && !pc.properties->values_q64) pc.reason = "pc_keys_and_values_unread";
  else if (!pc.properties->keys_u16) pc.reason = "pc_keys_unread";
  else if (!pc.properties->values_q64) pc.reason = "pc_values_unread";
  else pc.ready = true;
}

void Append(PersonFollowing2922680DTO &dto, const PersonFollowing2922680Pc &pc,
    const char *kind, std::uint32_t outer, std::uint32_t source, std::uint32_t item,
    std::optional<std::uint32_t> nested = std::nullopt,
    std::optional<std::uint32_t> descriptor = std::nullopt) {
  PersonFollowing2922680Append append;
  static_cast<PersonFollowing2922680Pc &>(append) = pc;
  append.kind = kind;
  append.outer_index = outer;
  append.source_index = source;
  append.item_index = item;
  append.nested_index = nested;
  append.descriptor_index = descriptor;
  dto.append_occurrences.push_back(std::move(append));
}

void ReadGetter(const PersonCarrierDirect12004Bindings &b,
    const std::optional<std::uint32_t> &character_id,
    PersonFollowing2922680SourceRow &source) {
  auto &g = source.getter;
  const auto object = *source.resolution.selected_identity;
  g.input_magic_u32 = Copy<std::uint32_t>(b, object + 0xC);
  if (!g.input_magic_u32) { g.reason = "getter_input_magic_unread"; return; }
  bool fallback = *g.input_magic_u32 != 0x53695352U;
  if (!fallback) {
    g.input_full_id_u32 = Copy<std::uint32_t>(b, object + 8);
    if (!g.input_full_id_u32) { g.reason = "getter_input_full_id_unread"; return; }
    fallback = *g.input_full_id_u32 == 0xFFFFFFFFU;
  }
  if (!fallback) {
    if (!character_id) { g.reason = "getter_character_id_unread"; return; }
    std::uint32_t hash = 2166136261U;
    for (unsigned shift = 0; shift != 32; shift += 8)
      hash = (hash ^ ((*character_id >> shift) & 0xFFU)) * 16777619U;
    g.hash_u32 = hash;
    g.mask_i32 = Copy<std::int32_t>(b, object + 0xFC);
    g.table_identity = Copy<std::uintptr_t>(b, object + 0xF0);
    if (!g.mask_i32 || !g.table_identity || *g.table_identity == 0) {
      g.reason = "getter_hash_header_unread";
      return;
    }
    g.start_index_i64 = static_cast<std::int64_t>(
        std::bit_cast<std::int32_t>(hash & static_cast<std::uint32_t>(*g.mask_i32)));
    auto slot = *g.table_identity + static_cast<std::uintptr_t>(*g.start_index_i64) * 12;
    std::uint8_t distance = 1;
    bool found = false;
    for (std::uint32_t index = 0;; ++index) {
      PersonFollowing2922680Probe probe;
      probe.native_index = index;
      probe.slot_identity = slot;
      probe.control_u8 = Copy<std::uint8_t>(b, slot);
      if (!probe.control_u8) {
        g.probes.push_back(std::move(probe));
        g.reason = "getter_probe_control_unread";
        return;
      }
      if (*probe.control_u8 < distance) {
        g.probes.push_back(std::move(probe));
        break;
      }
      probe.key_u32 = Copy<std::uint32_t>(b, slot + 4);
      if (!probe.key_u32) {
        g.probes.push_back(std::move(probe));
        g.reason = "getter_probe_key_unread";
        return;
      }
      found = *probe.key_u32 == *character_id;
      g.probes.push_back(std::move(probe));
      if (found) break;
      slot += 12;
      distance = static_cast<std::uint8_t>(distance + 1U);
    }
    // The cold-tail BYTE100 load and branch back to84C are inside this same
    // source-closed getter, including a successful probe and an ordinary miss.
    g.overflow_u8 = Copy<std::uint8_t>(b, object + 0x100);
    if (!g.overflow_u8) { g.reason = "getter_overflow_unread"; return; }
    const auto end_bits = static_cast<std::uint32_t>(*g.mask_i32) +
                          static_cast<std::uint32_t>(*g.overflow_u8) + 1U;
    const auto end_index = static_cast<std::int64_t>(std::bit_cast<std::int32_t>(end_bits));
    g.end_slot_identity = *g.table_identity + static_cast<std::uintptr_t>(end_index) * 12;
    g.found_slot_identity = found ? slot : *g.end_slot_identity;
    fallback = *g.found_slot_identity == *g.end_slot_identity;
    if (!fallback) {
      g.value_resolution = Resolve(b, kGetterValueRegistryRva, kGetterFallbackSlotRva,
                                   *g.found_slot_identity + 8);
      g.selected_value_u32 = g.value_resolution.requested_full_id_u32;
      if (!g.value_resolution.ready) { g.reason = g.value_resolution.reason; return; }
      g.result_identity = g.value_resolution.selected_identity;
    }
  }
  if (fallback) g.result_identity = Copy<std::uintptr_t>(b, b.module_base + kGetterFallbackSlotRva);
  if (!g.result_identity || *g.result_identity == 0) { g.reason = "getter_result_unread"; return; }
  g.result_magic_u32 = Copy<std::uint32_t>(b, *g.result_identity + 0xC);
  if (!g.result_magic_u32) { g.reason = "getter_result_magic_unread"; return; }
  if (*g.result_magic_u32 != 0x53695047U) { g.admitted = false; g.ready = true; return; }
  g.result_full_id_u32 = Copy<std::uint32_t>(b, *g.result_identity + 8);
  if (!g.result_full_id_u32) { g.reason = "getter_result_full_id_unread"; return; }
  g.admitted = *g.result_full_id_u32 != 0xFFFFFFFFU;
  g.ready = true;
}

void ReadMembership(const PersonCarrierDirect12004Bindings &b,
    PersonFollowing2922680DTO &dto, PersonFollowing2922680Membership &m,
    std::uintptr_t header, std::uint32_t outer, std::uint32_t source,
    std::uint32_t item, std::optional<std::uint32_t> nested) {
  m.header_identity = header;
  m.count_i32 = Copy<std::int32_t>(b, header + 0xC);
  if (!m.count_i32) { m.reason = "descriptor_count_unread"; return; }
  if (*m.count_i32 < 0) { m.reason = "descriptor_count_negative"; return; }
  if (*m.count_i32 == 0) { m.ready = true; return; }
  m.array_identity = Copy<std::uintptr_t>(b, header);
  if (!m.array_identity || *m.array_identity == 0) { m.reason = "descriptor_array_unread"; return; }
  if (dto.source_operand_ready) {
    m.membership_count_i32 = Copy<std::int32_t>(b, *dto.source_operand_identity + 0x5C);
    if (m.membership_count_i32 && *m.membership_count_i32 >= 0) {
      if (*m.membership_count_i32 == 0) m.membership_identities.emplace();
      else {
        m.membership_array_identity = Copy<std::uintptr_t>(b, *dto.source_operand_identity + 0x50);
        m.membership_identities = CopyArray<std::uintptr_t>(b, m.membership_array_identity,
                                                          *m.membership_count_i32);
      }
    }
  }
  m.ready = true;
  for (std::uint32_t index = 0; index < static_cast<std::uint32_t>(*m.count_i32); ++index) {
    PersonFollowing2922680MembershipRow row;
    row.native_index = index;
    row.key_identity = Copy<std::uintptr_t>(b, *m.array_identity +
        static_cast<std::uintptr_t>(index) * 0x30 + 0x20);
    if (!row.key_identity) row.reason = "descriptor_key_unread";
    else if (!m.membership_identities) row.reason = "membership_inputs_unread";
    else {
      row.admitted = std::find(m.membership_identities->begin(), m.membership_identities->end(),
                               *row.key_identity) != m.membership_identities->end();
      if (!*row.admitted) row.ready = true;
      else {
        row.reason = "actual42127e0_input_unobserved";
        PersonFollowing2922680Pc mapped;
        mapped.admitted = true;
        mapped.reason = row.reason;
        Append(dto, mapped, nested ? "nested_mapped" : "item_mapped", outer, source,
               item, nested, index);
      }
    }
    m.ready = m.ready && row.ready;
    m.rows.push_back(std::move(row));
  }
  if (!m.ready) m.reason = "membership_rows_partial";
}

void ReadSourceItems(const PersonCarrierDirect12004Bindings &b,
    PersonFollowing2922680DTO &dto, PersonFollowing2922680SourceRow &source,
    std::uint32_t outer) {
  if (!source.resolution.ready) { source.reason = source.resolution.reason; return; }
  ReadGetter(b, dto.character_id, source);
  if (!source.getter.ready) { source.reason = source.getter.reason; return; }
  if (source.getter.admitted == false) { source.ready = true; source.direct_ready = true; return; }
  source.match_definition_identity = Copy<std::uintptr_t>(b, *source.getter.result_identity + 0x30);
  if (!source.match_definition_identity || *source.match_definition_identity == 0) {
    source.reason = "match_definition_unread"; return;
  }
  source.match_id_u32 = Copy<std::uint32_t>(b, *source.match_definition_identity + 8);
  if (!source.match_id_u32) { source.reason = "match_id_unread"; return; }
  source.item_container_identity = Copy<std::uintptr_t>(b, *source.resolution.selected_identity + 0x3F8);
  if (!source.item_container_identity || *source.item_container_identity == 0) {
    source.reason = "item_container_unread"; return;
  }
  source.item_count_i32 = Copy<std::int32_t>(b, *source.item_container_identity + 0xFC);
  if (!source.item_count_i32) { source.reason = "item_count_unread"; return; }
  if (*source.item_count_i32 < 0) { source.reason = "item_count_negative"; return; }
  if (*source.item_count_i32 == 0) { source.ready = true; source.direct_ready = true; return; }
  source.item_array_identity = Copy<std::uintptr_t>(b, *source.item_container_identity + 0xF0);
  if (!source.item_array_identity || *source.item_array_identity == 0) {
    source.reason = "item_array_unread"; return;
  }
  source.ready = true;
  source.direct_ready = true;
  for (std::uint32_t index = 0; index < static_cast<std::uint32_t>(*source.item_count_i32); ++index) {
    PersonFollowing2922680Item item;
    item.native_index = index;
    item.object_identity = Copy<std::uintptr_t>(b, *source.item_array_identity +
                                               static_cast<std::uintptr_t>(index) * 8);
    if (!item.object_identity || *item.object_identity == 0) {
      item.reason = "item_object_unread";
      source.ready = false;
      source.direct_ready = false;
      source.items.push_back(std::move(item));
      continue;
    }
    item.enabled_3f0_u8 = Copy<std::uint8_t>(b, *item.object_identity + 0x3F0);
    if (!item.enabled_3f0_u8) {
      item.primary_pc.reason = "item_enabled_unread";
      item.membership.reason = "item_enabled_unread";
    }
    else if (*item.enabled_3f0_u8 == 0) {
      item.primary_pc.admitted = false;
      item.primary_pc.ready = true;
      item.membership.ready = true;
    } else {
      ReadPc(b, *item.object_identity + 0x40, item.primary_pc);
      Append(dto, item.primary_pc, "item_primary", outer, source.native_index, index);
      ReadMembership(b, dto, item.membership, *item.object_identity + 0x3C0,
                     outer, source.native_index, index, std::nullopt);
    }
    bool item_direct_ready = item.primary_pc.ready;
    item.ready = item.primary_pc.ready && item.membership.ready;
    item.nested_count_i32 = Copy<std::int32_t>(b, *item.object_identity + 0x404);
    if (!item.nested_count_i32 || *item.nested_count_i32 < 0) {
      item.reason = item.nested_count_i32 ? "nested_count_negative" : "nested_count_unread";
      item.ready = false;
      item_direct_ready = false;
    } else if (*item.nested_count_i32 > 0) {
      item.nested_array_identity = Copy<std::uintptr_t>(b, *item.object_identity + 0x3F8);
      if (!item.nested_array_identity || *item.nested_array_identity == 0) {
        item.reason = "nested_array_unread";
        item.ready = false;
        item_direct_ready = false;
      } else for (std::uint32_t j = 0; j < static_cast<std::uint32_t>(*item.nested_count_i32); ++j) {
        PersonFollowing2922680Nested nested;
        nested.native_index = j;
        nested.object_identity = Copy<std::uintptr_t>(b, *item.nested_array_identity +
                                                     static_cast<std::uintptr_t>(j) * 8);
        if (!nested.object_identity || *nested.object_identity == 0) nested.reason = "nested_object_unread";
        else {
          nested.selector_id_u32 = Copy<std::uint32_t>(b, *nested.object_identity + 8);
          if (!nested.selector_id_u32) nested.reason = "nested_selector_unread";
          else {
            nested.matched = *nested.selector_id_u32 == *source.match_id_u32;
            if (!*nested.matched) {
              nested.primary_pc.admitted = false;
              nested.primary_pc.ready = true;
              nested.membership.ready = true;
              nested.ready = true;
            } else {
              ReadPc(b, *nested.object_identity + 0x10, nested.primary_pc);
              Append(dto, nested.primary_pc, "nested_primary", outer, source.native_index, index, j);
              ReadMembership(b, dto, nested.membership, *nested.object_identity + 0x390,
                             outer, source.native_index, index, j);
              nested.ready = nested.primary_pc.ready && nested.membership.ready;
              if (!nested.ready) nested.reason = "nested_inputs_partial";
            }
          }
        }
        item_direct_ready = item_direct_ready && nested.primary_pc.ready;
        item.ready = item.ready && nested.ready;
        item.nested.push_back(std::move(nested));
      }
    }
    if (!item.ready && item.reason.empty()) item.reason = "item_inputs_partial";
    source.direct_ready = source.direct_ready && item_direct_ready;
    source.ready = source.ready && item.ready;
    source.items.push_back(std::move(item));
  }
  if (!source.ready) source.reason = "source_items_partial";
}

void ReadRowPrefix(const PersonCarrierDirect12004Bindings &b,
                   PersonFollowing2922680DTO &dto, PersonFollowing2922680Row &row) {
  if (!row.resolution.ready) { row.reason = row.resolution.reason; return; }
  const auto object = *row.resolution.selected_identity;
  row.cached_date_c7ce_i16 = Copy<std::int16_t>(b, object + 0xC7CE);
  if (!row.cached_date_c7ce_i16) {
    row.reason = "row_cached_date_unread";
    return;
  }
  if (*row.cached_date_c7ce_i16 >= 0)
    row.derived_year_i32 = *row.cached_date_c7ce_i16;
  else {
    row.raw_date_c7c8_i32 = Copy<std::int32_t>(b, object + 0xC7C8);
    if (!row.raw_date_c7c8_i32) { row.reason = "row_raw_date_unread"; return; }
    // Native date conversion: wrapped signed32 subtraction, then truncation
    // toward zero. The cache's sign controls selection; no cache is written.
    const auto difference = static_cast<std::uint32_t>(*row.raw_date_c7c8_i32) - 43800000U;
    row.derived_year_i32 = std::bit_cast<std::int32_t>(difference) / 8760;
  }
  if (*row.derived_year_i32 > 1) {
    if (!row.raw_date_c7c8_i32)
      row.raw_date_c7c8_i32 = Copy<std::int32_t>(b, object + 0xC7C8);
    if (!row.raw_date_c7c8_i32) { row.reason = "row_raw_date_unread"; return; }
    row.current_game_data_identity = Copy<std::uintptr_t>(b, b.module_base + kCurrentGameDataSlotRva);
    if (!row.current_game_data_identity || *row.current_game_data_identity == 0) {
      row.reason = "current_game_data_unread";
      return;
    }
    row.current_date_i32 = Copy<std::int32_t>(b, *row.current_game_data_identity + 8);
    if (!row.current_date_i32) { row.reason = "current_date_unread"; return; }
    if (*row.raw_date_c7c8_i32 <= *row.current_date_i32) {
      row.date_branch = "expired";
      row.date_admitted = false;
      row.known_no_contribution = true;
      row.ready = true;
      row.primary_ready = true;
      row.reason.clear();
      return;
    }
    row.date_branch = "not_expired";
  } else row.date_branch = "no_current_date_required";
  row.date_admitted = true;
  row.source_list_count_i32 = Copy<std::int32_t>(b, object + 0x134);
  if (!row.source_list_count_i32) { row.reason = "source_list_count_unread"; return; }
  if (*row.source_list_count_i32 < 0) { row.reason = "source_list_count_negative"; return; }
  if (*row.source_list_count_i32 == 0) {
    row.known_no_contribution = true;
    row.ready = true;
    row.primary_ready = true;
    row.reason.clear();
    return;
  }
  row.source_list_array_identity = Copy<std::uintptr_t>(b, object + 0x128);
  if (!row.source_list_array_identity || *row.source_list_array_identity == 0) {
    row.reason = "source_list_array_unread";
    return;
  }
  row.ready = true;
  row.primary_ready = true;
  for (std::uint32_t index = 0;
       index < static_cast<std::uint32_t>(*row.source_list_count_i32); ++index) {
    PersonFollowing2922680SourceRow source;
    source.native_index = index;
    source.resolution = Resolve(b, kSourceRegistryRva, kSourceFallbackSlotRva,
        *row.source_list_array_identity + static_cast<std::uintptr_t>(index) * 4);
    if (source.resolution.registry_identity)
      source.list_id_demanded = *source.resolution.registry_identity != 0;
    source.list_full_id_u32 = source.resolution.requested_full_id_u32;
    ReadSourceItems(b, dto, source, row.native_index);
    row.ready = row.ready && source.ready;
    row.primary_ready = row.primary_ready && source.direct_ready;
    row.sources.push_back(std::move(source));
  }
  if (!row.ready) row.reason = "source_rows_partial";
}

void ReadSources(const PersonCarrierDirect12004Bindings &b,
                 PersonFollowing2922680DTO &dto, std::uintptr_t character) {
  dto.character_context_1c0_identity = Copy<std::uintptr_t>(b, character + 0x1C0);
  if (!dto.character_context_1c0_identity) {
    dto.reason = "character_context_1c0_unread";
    return;
  }
  bool default_header = *dto.character_context_1c0_identity == 0;
  if (!default_header) {
    dto.character_gate_1d0_identity = Copy<std::uintptr_t>(b, character + 0x1D0);
    if (!dto.character_gate_1d0_identity) {
      dto.reason = "character_gate_1d0_unread";
      return;
    }
    default_header = *dto.character_gate_1d0_identity != 0;
  }
  dto.header_selection = default_header ? "existing_default_5d67de0" : "context_1c0_198";
  dto.list_header_identity = default_header ? b.module_base + kDefaultHeaderRva
                                            : *dto.character_context_1c0_identity + 0x198;
  dto.list_count_i32 = Copy<std::int32_t>(b, *dto.list_header_identity + 0xC);
  if (!dto.list_count_i32) { dto.reason = "list_count_unread"; return; }
  if (*dto.list_count_i32 == 0) { dto.ready = true; dto.primary_ready = true; return; }
  if (*dto.list_count_i32 < 0) { dto.reason = "list_count_negative"; return; }

  dto.rite_resolution = Resolve(b, religion::profile::kRiteStorageSlotRva,
      kRiteFallbackSlotRva, character + 0xB4);
  if (dto.rite_resolution.ready) {
    dto.context_resolution = Resolve(b, kContextRegistryRva,
        kContextFallbackSlotRva, *dto.rite_resolution.selected_identity + 0x4B8);
  } else dto.context_resolution.reason = "rite_resolution_unavailable";
  ReadSourceOperand(b, dto);

  dto.list_array_identity = Copy<std::uintptr_t>(b, *dto.list_header_identity);
  if (!dto.list_array_identity || *dto.list_array_identity == 0) {
    dto.reason = "list_array_unread";
    return;
  }
  for (std::uint32_t index = 0; index < static_cast<std::uint32_t>(*dto.list_count_i32); ++index) {
    PersonFollowing2922680Row row;
    row.native_index = index;
    const auto key_address = *dto.list_array_identity + static_cast<std::uintptr_t>(index) * 4;
    row.resolution = Resolve(b, kRowRegistryRva, kRowFallbackSlotRva, key_address);
    // Actual292275C reads the DWORD only with a nonnull row registry.
    // Null registry goes straight to fallback; unread unused IDs stay null.
    if (row.resolution.registry_identity)
      row.list_id_demanded = *row.resolution.registry_identity != 0;
    row.list_full_id_u32 = row.resolution.requested_full_id_u32;
    ReadRowPrefix(b, dto, row);
    dto.rows.push_back(std::move(row));
  }
  dto.ready = true;
  dto.primary_ready = true;
  for (const auto &row : dto.rows) {
    dto.ready = dto.ready && row.ready;
    dto.primary_ready = dto.primary_ready && row.primary_ready;
  }
  if (!dto.ready) dto.reason = "rows_partial";
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
void Reason(std::ostream &out, std::string_view reason) {
  if (reason.empty()) out << "null";
  else String(out, reason);
}
template <typename T>
void Number(std::ostream &out, const std::optional<T> &value) {
  if (value) out << +*value;
  else out << "null";
}
void Pointer(std::ostream &out, const std::optional<std::uintptr_t> &value) {
  if (!value) { out << "null"; return; }
  out << "\"0x" << std::hex << *value << std::dec << '"';
}
void Resolution(std::ostream &out, const PersonFollowing2922680Resolution &r) {
  out << "{\"ready\":" << (r.ready ? "true" : "false") << ",\"reason\":";
  Reason(out, r.reason);
  out << ",\"selection\":"; String(out, r.selection);
  out << ",\"requested_full_id_u32\":"; Number(out, r.requested_full_id_u32);
  out << ",\"registry_identity\":"; Pointer(out, r.registry_identity);
  out << ",\"registry_count_u32\":"; Number(out, r.registry_count_u32);
  out << ",\"registry_slots_identity\":"; Pointer(out, r.registry_slots_identity);
  out << ",\"candidate_identity\":"; Pointer(out, r.candidate_identity);
  out << ",\"candidate_full_id_u32\":"; Number(out, r.candidate_full_id_u32);
  out << ",\"selected_identity\":"; Pointer(out, r.selected_identity);
  out << '}';
}

void Boolean(std::ostream &out, const std::optional<bool> &value) {
  if (value) out << (*value ? "true" : "false");
  else out << "null";
}
template <typename T>
void Array(std::ostream &out, const std::optional<std::vector<T>> &values, bool quoted) {
  if (!values) { out << "null"; return; }
  out << '[';
  bool first = true;
  for (const auto value : *values) {
    if (!first) out << ',';
    first = false;
    if (quoted) out << '"';
    out << +value;
    if (quoted) out << '"';
  }
  out << ']';
}
void PcFields(std::ostream &out, const PersonFollowing2922680Pc &pc) {
  out << "\"ready\":" << (pc.ready ? "true" : "false") << ",\"reason\":";
  Reason(out, pc.reason);
  out << ",\"admitted\":"; Boolean(out, pc.admitted);
  out << ",\"identity\":"; Pointer(out, pc.identity);
  out << ",\"count_i32\":"; Number(out, pc.count_i32);
  out << ",\"weight_q100000\":" << pc.weight_q100000 << ",\"properties\":";
  if (!pc.properties) out << "null";
  else {
    out << "{\"keys_u16\":"; Array(out, pc.properties->keys_u16, false);
    out << ",\"values_q64\":"; Array(out, pc.properties->values_q64, true);
    out << '}';
  }
}
void Pc(std::ostream &out, const PersonFollowing2922680Pc &pc) {
  out << '{'; PcFields(out, pc); out << '}';
}
void Getter(std::ostream &out, const PersonFollowing2922680Getter &g) {
  out << "{\"ready\":" << (g.ready ? "true" : "false") << ",\"reason\":";
  Reason(out, g.reason);
  out << ",\"input_magic_u32\":"; Number(out, g.input_magic_u32);
  out << ",\"input_full_id_u32\":"; Number(out, g.input_full_id_u32);
  out << ",\"hash_u32\":"; Number(out, g.hash_u32);
  out << ",\"mask_i32\":"; Number(out, g.mask_i32);
  out << ",\"table_identity\":"; Pointer(out, g.table_identity);
  out << ",\"start_index_i64\":"; Number(out, g.start_index_i64);
  out << ",\"overflow_u8\":"; Number(out, g.overflow_u8);
  out << ",\"end_slot_identity\":"; Pointer(out, g.end_slot_identity);
  out << ",\"found_slot_identity\":"; Pointer(out, g.found_slot_identity);
  out << ",\"probes\":[";
  bool first = true;
  for (const auto &p : g.probes) {
    if (!first) out << ',';
    first = false;
    out << "{\"native_index\":" << p.native_index << ",\"slot_identity\":";
    Pointer(out, p.slot_identity);
    out << ",\"control_u8\":"; Number(out, p.control_u8);
    out << ",\"key_u32\":"; Number(out, p.key_u32);
    out << '}';
  }
  out << "],\"selected_value_u32\":"; Number(out, g.selected_value_u32);
  out << ",\"value_resolution\":"; Resolution(out, g.value_resolution);
  out << ",\"result_identity\":"; Pointer(out, g.result_identity);
  out << ",\"result_magic_u32\":"; Number(out, g.result_magic_u32);
  out << ",\"result_full_id_u32\":"; Number(out, g.result_full_id_u32);
  out << ",\"admitted\":"; Boolean(out, g.admitted);
  out << '}';
}
void Membership(std::ostream &out, const PersonFollowing2922680Membership &m) {
  out << "{\"ready\":" << (m.ready ? "true" : "false") << ",\"reason\":";
  Reason(out, m.reason);
  out << ",\"header_identity\":"; Pointer(out, m.header_identity);
  out << ",\"count_i32\":"; Number(out, m.count_i32);
  out << ",\"array_identity\":"; Pointer(out, m.array_identity);
  out << ",\"membership_count_i32\":"; Number(out, m.membership_count_i32);
  out << ",\"membership_array_identity\":"; Pointer(out, m.membership_array_identity);
  out << ",\"membership_identities\":";
  if (!m.membership_identities) out << "null";
  else {
    out << '[';
    bool first = true;
    for (const auto identity : *m.membership_identities) {
      if (!first) out << ',';
      first = false;
      Pointer(out, identity);
    }
    out << ']';
  }
  out << ",\"rows\":[";
  bool first = true;
  for (const auto &row : m.rows) {
    if (!first) out << ',';
    first = false;
    out << "{\"native_index\":" << row.native_index << ",\"ready\":"
        << (row.ready ? "true" : "false") << ",\"reason\":";
    Reason(out, row.reason);
    out << ",\"key_identity\":"; Pointer(out, row.key_identity);
    out << ",\"admitted\":"; Boolean(out, row.admitted);
    out << '}';
  }
  out << "]}";
}
void Item(std::ostream &out, const PersonFollowing2922680Item &item) {
  out << "{\"native_index\":" << item.native_index << ",\"ready\":"
      << (item.ready ? "true" : "false") << ",\"reason\":";
  Reason(out, item.reason);
  out << ",\"object_identity\":"; Pointer(out, item.object_identity);
  out << ",\"enabled_3f0_u8\":"; Number(out, item.enabled_3f0_u8);
  out << ",\"primary_pc\":"; Pc(out, item.primary_pc);
  out << ",\"membership\":"; Membership(out, item.membership);
  out << ",\"nested_count_i32\":"; Number(out, item.nested_count_i32);
  out << ",\"nested_array_identity\":"; Pointer(out, item.nested_array_identity);
  out << ",\"nested\":[";
  bool first = true;
  for (const auto &n : item.nested) {
    if (!first) out << ',';
    first = false;
    out << "{\"native_index\":" << n.native_index << ",\"ready\":"
        << (n.ready ? "true" : "false") << ",\"reason\":";
    Reason(out, n.reason);
    out << ",\"object_identity\":"; Pointer(out, n.object_identity);
    out << ",\"selector_id_u32\":"; Number(out, n.selector_id_u32);
    out << ",\"matched\":"; Boolean(out, n.matched);
    out << ",\"primary_pc\":"; Pc(out, n.primary_pc);
    out << ",\"membership\":"; Membership(out, n.membership);
    out << '}';
  }
  out << "]}";
}
} // namespace

PersonFollowing2922680DTO ReadPersonFollowing2922680ForModel12004(
    const PersonCarrierDirect12004Bindings &b, std::uintptr_t actual_model) {
  auto dto = Initial();
  dto.selected_model_identity = actual_model;
  if (!b.enabled || !b.read_memory) { dto.reason = "exact_build_binding_unavailable"; return dto; }
  if (actual_model == 0) { dto.reason = "actual_model_unavailable"; return dto; }
  dto.destination_pc_identity = actual_model + 0x10;
  dto.character_identity = Copy<std::uintptr_t>(b, actual_model + 8);
  if (!dto.character_identity || *dto.character_identity == 0) {
    dto.reason = "model_character_unread";
    return dto;
  }
  dto.character_id = Copy<std::uint32_t>(b, *dto.character_identity + kCharacterFullIdOffset);
  ReadSources(b, dto, *dto.character_identity);
  return dto;
}

PersonFollowing2922680DTO ReadPersonFollowing2922680ForCharacter12004(
    const PersonCarrierDirect12004Bindings &b, std::uintptr_t actual_character) {
  auto dto = Initial();
  dto.character_identity = actual_character;
  if (!b.enabled || !b.read_memory || b.current_context_getter_identity !=
      b.module_base + kPersonCarrierContextGetterRva12004) {
    dto.reason = "exact_build_binding_unavailable";
    return dto;
  }
  if (actual_character == 0) { dto.reason = "requested_character_unavailable"; return dto; }
  dto.character_id = Copy<std::uint32_t>(b, actual_character + kCharacterFullIdOffset);
  const auto scratch = Copy<std::uintptr_t>(b, actual_character + 0x1B0);
  if (!scratch || *scratch == 0) {
    dto.reason = scratch ? "current_owned_model_absent_scratch" : "current_owned_model_scratch_unread";
    return dto;
  }
  dto.selected_model_identity = Copy<std::uintptr_t>(b, *scratch + 0x258);
  if (!dto.selected_model_identity || *dto.selected_model_identity == 0) {
    dto.reason = "current_owned_model_unread";
    return dto;
  }
  const auto owner = Copy<std::uintptr_t>(b, *dto.selected_model_identity + 8);
  if (!owner) { dto.reason = "current_owned_model_owner_unread"; return dto; }
  if (*owner != actual_character) { dto.reason = "current_owned_model_owner_mismatch"; return dto; }
  dto.destination_pc_identity = *dto.selected_model_identity + 0x10;
  ReadSources(b, dto, actual_character);
  return dto;
}

std::string SerializePersonFollowing2922680(const PersonFollowing2922680DTO &dto) {
  std::ostringstream out;
  out << "{\"schema\":"; String(out, kPersonFollowing2922680Schema);
  out << ",\"build_version\":"; String(out, dto.build_version);
  out << ",\"executable_sha256\":"; String(out, dto.executable_sha256);
  out << ",\"ready\":" << (dto.ready ? "true" : "false") << ",\"reason\":";
  Reason(out, dto.reason);
  out << ",\"character_id\":"; Number(out, dto.character_id);
  out << ",\"character_identity\":"; Pointer(out, dto.character_identity);
  out << ",\"selected_model_identity\":"; Pointer(out, dto.selected_model_identity);
  out << ",\"destination_pc_identity\":"; Pointer(out, dto.destination_pc_identity);
  out << ",\"character_context_1c0_identity\":"; Pointer(out, dto.character_context_1c0_identity);
  out << ",\"character_gate_1d0_identity\":"; Pointer(out, dto.character_gate_1d0_identity);
  out << ",\"header_selection\":"; String(out, dto.header_selection);
  out << ",\"list_header_identity\":"; Pointer(out, dto.list_header_identity);
  out << ",\"list_count_i32\":"; Number(out, dto.list_count_i32);
  out << ",\"list_array_identity\":"; Pointer(out, dto.list_array_identity);
  out << ",\"rite_resolution\":"; Resolution(out, dto.rite_resolution);
  out << ",\"context_resolution\":"; Resolution(out, dto.context_resolution);
  out << ",\"operand_rite_resolution\":"; Resolution(out, dto.operand_rite_resolution);
  out << ",\"source_operand_ready\":" << (dto.source_operand_ready ? "true" : "false");
  out << ",\"source_operand_reason\":"; Reason(out, dto.source_operand_reason);
  out << ",\"source_operand_identity\":"; Pointer(out, dto.source_operand_identity);
  out << ",\"rows\":[";
  bool first = true;
  for (const auto &row : dto.rows) {
    if (!first) out << ',';
    first = false;
    out << "{\"native_index\":" << row.native_index << ",\"ready\":"
        << (row.ready ? "true" : "false") << ",\"primary_ready\":"
        << (row.primary_ready ? "true" : "false") << ",\"reason\":";
    Reason(out, row.reason);
    out << ",\"list_id_demanded\":";
    if (row.list_id_demanded) out << (*row.list_id_demanded ? "true" : "false");
    else out << "null";
    out << ",\"list_full_id_u32\":"; Number(out, row.list_full_id_u32);
    out << ",\"resolution\":"; Resolution(out, row.resolution);
    out << ",\"cached_date_c7ce_i16\":"; Number(out, row.cached_date_c7ce_i16);
    out << ",\"raw_date_c7c8_i32\":"; Number(out, row.raw_date_c7c8_i32);
    out << ",\"derived_year_i32\":"; Number(out, row.derived_year_i32);
    out << ",\"current_game_data_identity\":"; Pointer(out, row.current_game_data_identity);
    out << ",\"current_date_i32\":"; Number(out, row.current_date_i32);
    out << ",\"date_branch\":"; String(out, row.date_branch);
    out << ",\"date_admitted\":";
    if (row.date_admitted) out << (*row.date_admitted ? "true" : "false");
    else out << "null";
    out << ",\"known_no_contribution\":" << (row.known_no_contribution ? "true" : "false");
    out << ",\"source_list_count_i32\":"; Number(out, row.source_list_count_i32);
    out << ",\"source_list_array_identity\":"; Pointer(out, row.source_list_array_identity);
    out << ",\"sources\":[";
    bool first_source = true;
    for (const auto &source : row.sources) {
      if (!first_source) out << ',';
      first_source = false;
      out << "{\"native_index\":" << source.native_index << ",\"ready\":"
          << (source.ready ? "true" : "false") << ",\"reason\":";
      Reason(out, source.reason);
      out << ",\"list_id_demanded\":";
      if (source.list_id_demanded) out << (*source.list_id_demanded ? "true" : "false");
      else out << "null";
      out << ",\"list_full_id_u32\":"; Number(out, source.list_full_id_u32);
      out << ",\"resolution\":"; Resolution(out, source.resolution);
      out << ",\"getter\":"; Getter(out, source.getter);
      out << ",\"direct_ready\":" << (source.direct_ready ? "true" : "false");
      out << ",\"match_definition_identity\":"; Pointer(out, source.match_definition_identity);
      out << ",\"match_id_u32\":"; Number(out, source.match_id_u32);
      out << ",\"item_container_identity\":"; Pointer(out, source.item_container_identity);
      out << ",\"item_count_i32\":"; Number(out, source.item_count_i32);
      out << ",\"item_array_identity\":"; Pointer(out, source.item_array_identity);
      out << ",\"items\":[";
      bool first_item = true;
      for (const auto &item : source.items) {
        if (!first_item) out << ',';
        first_item = false;
        Item(out, item);
      }
      out << ']';
      out << '}';
    }
    out << ']';
    out << '}';
  }
  out << "],\"primary_ready\":" << (dto.primary_ready ? "true" : "false");
  out << ",\"append_occurrences\":[";
  bool first_append = true;
  for (const auto &append : dto.append_occurrences) {
    if (!first_append) out << ',';
    first_append = false;
    out << '{'; PcFields(out, append);
    out << ",\"kind\":"; String(out, append.kind);
    out << ",\"outer_index\":" << append.outer_index;
    out << ",\"source_index\":" << append.source_index;
    out << ",\"item_index\":" << append.item_index;
    out << ",\"nested_index\":"; Number(out, append.nested_index);
    out << ",\"descriptor_index\":"; Number(out, append.descriptor_index);
    out << '}';
  }
  out << "]}";
  return out.str();
}

} // namespace xar::ck3_12004
