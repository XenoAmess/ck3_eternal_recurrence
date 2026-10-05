#pragma once

#include "xar_bridge/ck3_12002_army.hpp"
#include <algorithm>
#include <cstring>
#include <utility>

namespace xar::ck3_12002::current_helper_domain_detail {
template<class T> T Load(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof value);
  return value;
}

// Native generation selection including actual fallback. No new count cap or
// positive-ID gate: negative FullIDs retain their generation bits.
inline void *Resolve(void **slot, void **fallback, std::int32_t id,
                     std::size_t id_offset, std::optional<bool> &used_fallback) {
  if (slot == nullptr || fallback == nullptr) return nullptr;
  const auto *storage = *slot;
  if (storage != nullptr) {
    const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
    const auto capacity = Load<std::uint32_t>(storage, 0x2C);
    if (index < capacity) {
      const auto *objects = Load<const void *>(storage, 0x20);
      if (objects == nullptr) return nullptr;
      void *object = Load<void *>(objects, static_cast<std::size_t>(index) * 0x10 + 8);
      if (object != nullptr && Load<std::int32_t>(object, id_offset) == id) {
        used_fallback = false;
        return object;
      }
    }
  }
  used_fallback = true;
  return *fallback;
}

inline void ReadDomainRow(const ArmyBindings &bindings,
                         game::ArmyCurrentHelperDomainRowV1 &row,
                         std::vector<void *> &domain_aliases) {
  const auto &native = bindings.monthly_current_helper_domain_bindings;
  void *containing = Resolve(bindings.persistent_regiment_storage_slot,
      native.persistent_regiment_fallback_slot, row.record_regiment_reference_id,
      0x10, row.record_regiment_used_fallback);
  if (containing == nullptr) return;
  row.record_regiment_resolved_id = Load<std::int32_t>(containing, 0x10);
  row.record_regiment_magic_14_raw = Load<std::uint32_t>(containing, 0x14);
  if (*row.record_regiment_resolved_id == -1 ||
      *row.record_regiment_magic_14_raw != 0x52656769U) return;
  const auto displacement = static_cast<std::int64_t>(row.chunk_index) * 0x24;
  const auto address = reinterpret_cast<std::uintptr_t>(containing) + 0x18U +
      static_cast<std::uintptr_t>(displacement);
  const auto *data = reinterpret_cast<const void *>(address);
  row.data_record_present = data != nullptr;
  if (data == nullptr) return;
  row.data_state_18_raw = Load<std::int32_t>(data, 0x18);
  if (*row.data_state_18_raw != 4) return;
  row.data_owner_regiment_reference_id = Load<std::int32_t>(data, 8);
  void *receiver = Resolve(bindings.persistent_regiment_storage_slot,
      native.persistent_regiment_fallback_slot, *row.data_owner_regiment_reference_id,
      0x10, row.receiver_regiment_used_fallback);
  if (receiver == nullptr) return;
  row.receiver_regiment_resolved_id = Load<std::int32_t>(receiver, 0x10);
  row.receiver_state_138_raw = Load<std::int32_t>(receiver, 0x138);
  if (*row.receiver_state_138_raw != 4) return;
  row.receiver_title_reference_130_raw = Load<std::int32_t>(receiver, 0x130);
  row.receiver_character_reference_12c_raw = Load<std::int32_t>(receiver, 0x12C);
  auto character_id = std::int32_t{-1};
  if (*row.receiver_title_reference_130_raw != -1 &&
      *row.receiver_character_reference_12c_raw == -1) {
    void *title = Resolve(native.title_storage_slot, native.title_fallback_slot,
        *row.receiver_title_reference_130_raw, 0x10, row.owner_title_used_fallback);
    if (title == nullptr) return;
    row.owner_title_resolved_id = Load<std::int32_t>(title, 0x10);
    row.owner_title_holder_character_id_128_raw = Load<std::int32_t>(title, 0x128);
    character_id = *row.owner_title_holder_character_id_128_raw;
  } else if (*row.receiver_title_reference_130_raw == -1 &&
             *row.receiver_character_reference_12c_raw != -1) {
    character_id = *row.receiver_character_reference_12c_raw;
  }
  row.selected_character_reference_id = character_id;
  // 2C57020 preserves the initially loaded character registry/fallback across
  // its two readonly calls, then uses that same registry for Domain owner.
  void *character_storage = native.character_storage_slot == nullptr
      ? nullptr : *native.character_storage_slot;
  void *character_fallback = native.character_fallback_slot == nullptr
      ? nullptr : *native.character_fallback_slot;
  void **character_slot = native.character_storage_slot == nullptr ? nullptr : &character_storage;
  void **character_fallback_slot = native.character_fallback_slot == nullptr ? nullptr : &character_fallback;
  void *character = Resolve(character_slot, character_fallback_slot, character_id,
      0x18, row.selected_character_used_fallback);
  if (character == nullptr) return;
  row.selected_character_resolved_id = Load<std::int32_t>(character, 0x18);
  const auto *child = Load<const void *>(character, 0x1C8);
  row.character_domain_child_present = child != nullptr;
  row.domain_reference_id = child == nullptr ? -1 : Load<std::int32_t>(child, 0xB68);
  void *domain = Resolve(native.domain_storage_slot, native.domain_fallback_slot,
      *row.domain_reference_id, 8, row.domain_used_fallback);
  if (domain == nullptr) return;
  row.domain_resolved_id = Load<std::int32_t>(domain, 8);
  row.domain_magic_0c_raw = Load<std::uint32_t>(domain, 0xC);
  if (*row.domain_resolved_id == -1 || *row.domain_magic_0c_raw != 0x446F6D69U) return;
  const auto found = std::find(domain_aliases.begin(), domain_aliases.end(), domain);
  if (found == domain_aliases.end()) {
    row.domain_alias_ordinal = static_cast<std::int32_t>(domain_aliases.size());
    domain_aliases.push_back(domain);
  } else row.domain_alias_ordinal = static_cast<std::int32_t>(found - domain_aliases.begin());
  const auto *domain_data = Load<const void *>(domain, 0x30);
  row.domain_data_30_present = domain_data != nullptr;
  if (domain_data != nullptr) row.domain_flag_17e_raw = Load<std::uint8_t>(domain_data, 0x17E);
  row.count_base_128_raw = Load<std::int32_t>(receiver, 0x128);
  row.count_records.emplace();
  for (std::int32_t index = 0; index < 7; ++index) {
    const auto offset = 0x18 + static_cast<std::size_t>(index) * 0x24;
    row.count_records->push_back({index, Load<std::int32_t>(receiver, offset),
        Load<std::int32_t>(receiver, offset + 4), Load<std::int32_t>(receiver, offset + 0x18)});
  }
  row.domain_owner_character_reference_id = Load<std::int32_t>(domain, 0x20);
  void *owner = Resolve(character_slot, character_fallback_slot,
      *row.domain_owner_character_reference_id, 0x18, row.domain_owner_character_used_fallback);
  if (owner != nullptr) {
    row.domain_owner_character_resolved_id = Load<std::int32_t>(owner, 0x18);
    row.domain_owner_character_magic_1c_raw = Load<std::uint32_t>(owner, 0x1C);
  }
  row.domain_value_48_raw64 = Load<std::int64_t>(domain, 0x48);
}

inline game::ArmyCurrentHelperDomainInputsV1 Sample(const ArmyBindings &bindings,
                                                   void *army) {
  game::ArmyCurrentHelperDomainInputsV1 result{};
  result.entry_army_id = Load<std::int32_t>(army, 0x10);
  result.group_count_5c_raw = Load<std::int32_t>(army, 0x5C);
  result.rows.emplace();
  const auto count = *result.group_count_5c_raw;
  if (count > 0) {
    auto *const groups = Load<void *const *>(army, 0x50);
    if (groups == nullptr) {
      result.rows.reset(); result.unavailable_reason = "current_helper_groups_unavailable";
      return result;
    }
    std::vector<void *> domain_aliases;
    for (std::int32_t group_index = 0; group_index < count; ++group_index) {
      const auto *group = groups[group_index];
      if (group == nullptr) {
        result.rows.reset(); result.unavailable_reason = "current_helper_group_unavailable";
        return result;
      }
      const auto record_count = Load<std::int32_t>(group, 0x14);
      const auto *records = Load<const void *>(group, 8);
      if (record_count > 0 && records == nullptr) {
        result.rows.reset(); result.unavailable_reason = "current_helper_group_records_unavailable";
        return result;
      }
      for (std::int32_t index = 0; index < record_count; ++index) {
        game::ArmyCurrentHelperDomainRowV1 row{};
        row.group_index = group_index; row.stored_index = index;
        const auto offset = static_cast<std::size_t>(index) * 0x10;
        row.record_regiment_reference_id = Load<std::int32_t>(records, offset + 8);
        row.chunk_index = Load<std::int32_t>(records, offset + 0xC);
        ReadDomainRow(bindings, row, domain_aliases);
        result.rows->push_back(std::move(row));
      }
    }
  }
  result.available = true;
  return result;
}
} // namespace xar::ck3_12002::current_helper_domain_detail

namespace xar::ck3_12002 {
inline game::ArmyCurrentHelperDomainInputsV1 ReadCurrentHelperDomainInputs12003(
    const ArmyBindings &bindings, void *current_army) {
  const auto first = current_helper_domain_detail::Sample(bindings, current_army);
  const auto second = current_helper_domain_detail::Sample(bindings, current_army);
  if (first == second) return second;
  game::ArmyCurrentHelperDomainInputsV1 result{};
  result.entry_army_id = current_helper_domain_detail::Load<std::int32_t>(current_army, 0x10);
  result.unavailable_reason = "current_helper_domain_inputs_changed_during_read";
  return result;
}
} // namespace xar::ck3_12002
