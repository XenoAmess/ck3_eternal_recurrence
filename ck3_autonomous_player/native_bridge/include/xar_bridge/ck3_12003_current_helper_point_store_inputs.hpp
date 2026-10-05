#pragma once
#include "xar_bridge/ck3_12003_current_helper_domain_inputs.hpp"

namespace xar::ck3_12002::current_helper_point_store_detail {
using current_helper_domain_detail::Load;
using current_helper_domain_detail::Resolve;

inline std::int32_t Alias(std::vector<const void *> &aliases, const void *pointer) {
  const auto found = std::find(aliases.begin(), aliases.end(), pointer);
  if (found != aliases.end()) return static_cast<std::int32_t>(found - aliases.begin());
  const auto ordinal = static_cast<std::int32_t>(aliases.size());
  aliases.push_back(pointer);
  return ordinal;
}

inline void ReadRecord(const ArmyBindings &bindings, game::ArmyCurrentHelperPointRecordV1 &row,
                       std::vector<const void *> &data_aliases,
                       std::vector<const void *> &membership_aliases) {
  const auto &native = bindings.monthly_current_helper_domain_bindings;
  void *containing = Resolve(bindings.persistent_regiment_storage_slot,
      native.persistent_regiment_fallback_slot, row.record_regiment_reference_id,
      0x10, row.record_regiment_used_fallback);
  if (containing == nullptr) return;
  row.record_regiment_resolved_id = Load<std::int32_t>(containing, 0x10);
  row.record_regiment_magic_14_raw = Load<std::uint32_t>(containing, 0x14);
  if (*row.record_regiment_resolved_id == -1 || *row.record_regiment_magic_14_raw != 0x52656769U) return;
  const auto displacement = static_cast<std::int64_t>(row.chunk_index) * 0x24;
  const auto address = reinterpret_cast<std::uintptr_t>(containing) + 0x18U +
      static_cast<std::uintptr_t>(displacement);
  const auto *data = reinterpret_cast<const void *>(address);
  row.data_record_present = data != nullptr;
  if (data == nullptr) return;
  row.data_alias_ordinal = Alias(data_aliases, data);
  row.data_byte_14_raw = Load<std::uint8_t>(data, 0x14);
  row.data_state_18_raw = Load<std::int32_t>(data, 0x18);
  // DATA14 is cleared before the state4 branch in source. Observation performs
  // no write. Only membership's post2C continuation requires state4.
  if (*row.data_state_18_raw != 4) return;
  row.data_owner_regiment_reference_id = Load<std::int32_t>(data, 8);
  void *receiver = Resolve(bindings.persistent_regiment_storage_slot,
      native.persistent_regiment_fallback_slot, *row.data_owner_regiment_reference_id,
      0x10, row.receiver_regiment_used_fallback);
  if (receiver == nullptr) return;
  row.receiver_regiment_resolved_id = Load<std::int32_t>(receiver, 0x10);
  // Membership uses the source owner route after the ordinary2C return even
  // when receiver138!=4. Do not reuse the Domain reader's earlier return gate.
  row.receiver_title_reference_130_raw = Load<std::int32_t>(receiver, 0x130);
  row.receiver_character_reference_12c_raw = Load<std::int32_t>(receiver, 0x12C);
  auto character_id = std::int32_t{-1};
  if (*row.receiver_title_reference_130_raw != -1 && *row.receiver_character_reference_12c_raw == -1) {
    void *title = Resolve(native.title_storage_slot, native.title_fallback_slot,
        *row.receiver_title_reference_130_raw, 0x10, row.owner_title_used_fallback);
    if (title == nullptr) return;
    row.owner_title_resolved_id = Load<std::int32_t>(title, 0x10);
    row.owner_title_holder_character_id_128_raw = Load<std::int32_t>(title, 0x128);
    character_id = *row.owner_title_holder_character_id_128_raw;
  } else if (*row.receiver_title_reference_130_raw == -1 && *row.receiver_character_reference_12c_raw != -1) {
    character_id = *row.receiver_character_reference_12c_raw;
  }
  row.selected_character_reference_id = character_id;
  void *character = Resolve(native.character_storage_slot, native.character_fallback_slot,
      character_id, 0x18, row.selected_character_used_fallback);
  if (character == nullptr) return;
  row.selected_character_resolved_id = Load<std::int32_t>(character, 0x18);
  const auto *child = Load<const std::byte *>(character, 0x1C0);
  row.character_child_1c0_present = child != nullptr;
  if (child == nullptr) return;
  const auto *header = child + 0x2A8;
  row.membership_alias_ordinal = Alias(membership_aliases, header);
  row.membership_count_2b4_raw = Load<std::int32_t>(header, 0xC);
  const auto count = *row.membership_count_2b4_raw;
  const auto *ids = Load<const std::int32_t *>(header, 0);
  if (count <= 0 || ids != nullptr) {
    row.ordered_persistent_regiment_ids_2a8.emplace();
    for (std::int32_t index = 0; index < count; ++index)
      row.ordered_persistent_regiment_ids_2a8->push_back(ids[index]);
  }
}

inline game::ArmyCurrentHelperPointCharacterV1 ReadCharacter(
    const ArmyBindings &bindings, std::int32_t index, std::int32_t id,
    std::vector<const void *> &child_aliases) {
  game::ArmyCurrentHelperPointCharacterV1 row{};
  row.stored_index = index; row.character_reference_id = id;
  const auto &native = bindings.monthly_current_helper_domain_bindings;
  void *character = Resolve(native.character_storage_slot, native.character_fallback_slot,
      id, 0x18, row.character_used_fallback);
  if (character == nullptr) return row;
  row.character_resolved_id = Load<std::int32_t>(character, 0x18);
  row.character_child_1c8_present = Load<const void *>(character, 0x1C8) != nullptr;
  row.character_child_1c0_present = Load<const void *>(character, 0x1C0) != nullptr;
  const auto *child = Load<const void *>(character, 0x1B8);
  row.character_child_1b8_present = child != nullptr;
  if (child != nullptr) {
    row.child_1b8_alias_ordinal = Alias(child_aliases, child);
    row.child_byte_108_raw = Load<std::uint8_t>(child, 0x108);
    row.child_character_reference_fc_raw = Load<std::int32_t>(child, 0xFC);
  }
  return row;
}

inline game::ArmyCurrentHelperPointStoreInputsV1 Sample(const ArmyBindings &bindings, void *current_army) {
  game::ArmyCurrentHelperPointStoreInputsV1 result{};
  result.entry_army_id = Load<std::int32_t>(current_army, 0x10);
  void *army = Resolve(bindings.internal_army_storage_slot,
      bindings.monthly_daily_queue_bindings.army_fallback_slot, result.entry_army_id,
      0x10, result.helper_used_fallback);
  if (army == nullptr) {
    result.unavailable_reason = "point_store_helper_army_unavailable";
    return result;
  }
  result.helper_resolved_army_id = Load<std::int32_t>(army, 0x10);
  result.helper_same_current_army_pointer = army == current_army;
  result.group_count_5c_raw = Load<std::int32_t>(army, 0x5C);
  result.groups.emplace();
  result.available = true;
  const auto count = *result.group_count_5c_raw;
  if (count <= 0) return result;
  auto *const groups = Load<void *const *>(army, 0x50);
  if (groups == nullptr) {
    result.groups.reset(); result.available = false;
    result.unavailable_reason = "point_store_groups_unavailable";
    return result;
  }
  std::vector<const void *> data_aliases, membership_aliases, child_aliases;
  for (std::int32_t group_index = 0; group_index < count; ++group_index) {
    const auto *group = groups[group_index];
    if (group == nullptr) {
      result.groups.reset(); result.available = false;
      result.unavailable_reason = "point_store_group_unavailable";
      return result;
    }
    game::ArmyCurrentHelperPointGroupV1 observed{};
    observed.group_index = group_index;
    observed.record_count_14_raw = Load<std::int32_t>(group, 0x14);
    const auto *records = Load<const void *>(group, 8);
    if (observed.record_count_14_raw <= 0 || records != nullptr) {
      observed.record_rows.emplace();
      for (std::int32_t index = 0; index < observed.record_count_14_raw; ++index) {
        game::ArmyCurrentHelperPointRecordV1 row{};
        row.stored_index = index;
        const auto offset = static_cast<std::size_t>(index) * 0x10;
        row.record_regiment_reference_id = Load<std::int32_t>(records, offset + 8);
        row.chunk_index = Load<std::int32_t>(records, offset + 0xC);
        ReadRecord(bindings, row, data_aliases, membership_aliases);
        observed.record_rows->push_back(std::move(row));
      }
    }
    observed.character_count_2c_raw = Load<std::int32_t>(group, 0x2C);
    const auto *characters = Load<const std::int32_t *>(group, 0x20);
    // Native character loop compares begin/end, unlike the record JLE branch.
    // A negative signed count cannot be reported as a known empty traversal.
    if (observed.character_count_2c_raw == 0 ||
        (observed.character_count_2c_raw > 0 && characters != nullptr)) {
      observed.character_rows.emplace();
      for (std::int32_t index = 0; index < observed.character_count_2c_raw; ++index)
        observed.character_rows->push_back(ReadCharacter(bindings, index, characters[index], child_aliases));
    }
    result.available &= observed.record_rows.has_value() && observed.character_rows.has_value();
    result.groups->push_back(std::move(observed));
  }
  if (!result.available) result.unavailable_reason = "point_store_traversal_unavailable";
  return result;
}
} // namespace xar::ck3_12002::current_helper_point_store_detail

namespace xar::ck3_12002 {
inline game::ArmyCurrentHelperPointStoreInputsV1 ReadCurrentHelperPointStoreInputs12003(
    const ArmyBindings &bindings, void *current_army) {
  const auto first = current_helper_point_store_detail::Sample(bindings, current_army);
  const auto second = current_helper_point_store_detail::Sample(bindings, current_army);
  if (first == second) return second;
  game::ArmyCurrentHelperPointStoreInputsV1 result{};
  result.entry_army_id = current_helper_domain_detail::Load<std::int32_t>(current_army, 0x10);
  result.unavailable_reason = "point_store_inputs_changed_during_read";
  return result;
}
} // namespace xar::ck3_12002
