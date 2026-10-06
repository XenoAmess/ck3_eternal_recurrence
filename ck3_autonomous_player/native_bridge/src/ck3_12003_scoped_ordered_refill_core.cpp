#include "xar_bridge/ck3_12003_scoped_ordered_refill_core.hpp"
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include <algorithm>
#include <cstring>
#include <utility>

namespace xar::ck3_12003 {
namespace {
template<class T> T Load(const void *object, std::size_t offset) noexcept {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof value); return value;
}
void *Resolve(void **slot, std::int32_t id, std::size_t id_offset = 0x10) noexcept {
  if (!slot || !*slot) return nullptr;
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  const auto count = Load<std::int32_t>(*slot, 0x2C);
  const auto *objects = Load<const void *>(*slot, 0x20);
  if (count < 0 || index >= static_cast<std::uint32_t>(count) || !objects) return nullptr;
  void *object = Load<void *>(objects, static_cast<std::size_t>(index) * 16 + 8);
  return object && Load<std::int32_t>(object, id_offset) == id ? object : nullptr;
}
void *Fallback(void **slot) noexcept { return slot ? *slot : nullptr; }
bool List(const void *manager, std::size_t offset, const void *&ids, std::int32_t &count) noexcept {
  ids = Load<const void *>(manager, offset);
  const auto capacity = Load<std::int32_t>(manager, offset + 8);
  count = Load<std::int32_t>(manager, offset + 12);
  return capacity >= 0 && capacity <= 1'000'000 && count >= 0 && count <= capacity && (!count || ids);
}
game::ArmyOrderedRefillChunkV1 Chunk(const ck3_12002::ArmyBindings &b, const void *chunk, std::int32_t index) {
  const auto &n = b.scoped_ordered_refill_bindings;
  game::ArmyOrderedRefillChunkV1 r{};
  r.physical_index = index;
  r.maximum_soldiers = Load<std::int32_t>(chunk, 0);
  r.current_soldiers = Load<std::int32_t>(chunk, 4);
  r.owner_persistent_regiment_id = Load<std::int32_t>(chunk, 8);
  r.q_ordinal_raw = Load<std::int32_t>(chunk, 0xC);
  r.army_regiment_id_raw = Load<std::int32_t>(chunk, 0x10);
  r.exclusion_byte_14_raw = Load<std::uint8_t>(chunk, 0x14);
  r.state_raw = Load<std::int32_t>(chunk, 0x18);
  const auto missing = [&](const char *reason) { if (r.context_unavailable_reason.empty()) r.context_unavailable_reason = reason; };
  void *owner = Resolve(b.persistent_regiment_storage_slot, r.owner_persistent_regiment_id);
  if (!owner) owner = Fallback(n.persistent_fallback_slot);
  if (owner) {
    r.owner_resolved_full_id = Load<std::int32_t>(owner, 0x10);
    r.owner_guard_138_raw = Load<std::int32_t>(owner, 0x138);
    void *definition = Load<void *>(owner, 0x118);
    if (definition) r.owner_definition_magic_38_raw = Load<std::uint32_t>(definition, 0x38);
    else missing("raw_owner_definition_unavailable");
    void *province = Load<void *>(owner, 0x120);
    if (province) {
      r.origin_province_id = Load<std::int32_t>(province, 0x10);
      r.origin_province_788_raw = Load<std::int32_t>(province, 0x788);
      r.origin_province_73c_raw = Load<std::int32_t>(province, 0x73C);
    } else missing("raw_owner_origin_province_unavailable");
  } else missing("raw_chunk_owner_and_fallback_unavailable");
  void *arrg = n.resolve_arrg_reference ? n.resolve_arrg_reference(static_cast<const std::byte *>(chunk) + 0x10) : nullptr;
  if (!arrg) { missing("native_arrg_reference_resolver_unavailable"); return r; }
  r.associated_arrg_resolved_full_id = Load<std::int32_t>(arrg, 0x10);
  r.associated_arrg_magic_raw = Load<std::uint32_t>(arrg, 0x14);
  if (*r.associated_arrg_resolved_full_id == -1 || *r.associated_arrg_magic_raw != 0x41725267U) return r;
  r.associated_army_raw_full_id = Load<std::int32_t>(arrg, 0x140);
  void *army = Resolve(b.internal_army_storage_slot, *r.associated_army_raw_full_id);
  if (!army) army = Fallback(n.army_fallback_slot);
  if (!army) { missing("native_associated_army_and_fallback_unavailable"); return r; }
  r.associated_army_resolved_full_id = Load<std::int32_t>(army, 0x10);
  r.army_byte_1d4_raw = Load<std::uint8_t>(army, 0x1D4);
  r.army_byte_1ec_raw = Load<std::uint8_t>(army, 0x1EC);
  if (n.is_army_in_combat) r.native_army_in_combat = n.is_army_in_combat(army);
  else missing("native_army_combat_predicate_unavailable");
  r.associated_unit_raw_full_id = Load<std::int32_t>(army, 0x124);
  void *unit = n.resolve_unit_reference ? n.resolve_unit_reference(static_cast<std::byte *>(army) + 0x124) : nullptr;
  if (!unit) { missing("native_unit_reference_resolver_unavailable"); return r; }
  r.associated_unit_resolved_full_id = Load<std::int32_t>(unit, 0x10);
  r.unit_170_raw = Load<std::int32_t>(unit, 0x170);
  if (n.is_unit_position_eligible) r.native_unit_position_eligible = n.is_unit_position_eligible(unit);
  else missing("native_unit_position_predicate_unavailable");
  void *position = Load<void *>(unit, 0x20);
  if (!position) position = Fallback(n.unit_position_province_fallback_slot);
  if (!position) { missing("native_unit_position_province_unavailable"); return r; }
  r.unit_position_province_magic_raw = Load<std::uint32_t>(position, 0x85C);
  if (*r.unit_position_province_magic_raw != 0x50726F76U) return r;
  void *actor = Resolve(n.character_storage_slot, Load<std::int32_t>(unit, 0x174), 0x18);
  if (!actor) actor = Fallback(n.character_fallback_slot);
  std::int32_t holder_id = -1;
  const auto *holder_out = n.read_province_holder ? n.read_province_holder(position, &holder_id) : nullptr;
  if (!actor || !holder_out) { missing("native_position_owner_or_holder_unavailable"); return r; }
  void *holder = Resolve(n.character_storage_slot, *holder_out, 0x18);
  if (!holder) holder = Fallback(n.character_fallback_slot);
  r.unit_position_owner_resolved_full_id = Load<std::int32_t>(actor, 0x18);
  if (holder) r.unit_position_holder_resolved_full_id = Load<std::int32_t>(holder, 0x18);
  else missing("native_position_holder_fallback_unavailable");
  return r;
}
} // namespace

ScopedOrderedRefillBindings12003 BindScopedOrderedRefillInputs12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  ScopedOrderedRefillBindings12003 b{};
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.persistent_fallback_slot = reinterpret_cast<void **>(base + 0x5D1EB58);
  b.army_fallback_slot = reinterpret_cast<void **>(base + 0x5D1DE50);
  b.character_storage_slot = reinterpret_cast<void **>(base + 0x5C67568);
  b.character_fallback_slot = reinterpret_cast<void **>(base + 0x5C67570);
  b.unit_position_province_fallback_slot = reinterpret_cast<void **>(base + 0x5D1E390);
  b.resolve_arrg_reference = reinterpret_cast<decltype(b.resolve_arrg_reference)>(base + 0xC171A0);
  b.resolve_unit_reference = reinterpret_cast<decltype(b.resolve_unit_reference)>(base + 0xAEAA20);
  b.is_army_in_combat = reinterpret_cast<decltype(b.is_army_in_combat)>(base + 0x24E8360);
  b.is_unit_position_eligible = reinterpret_cast<decltype(b.is_unit_position_eligible)>(base + 0x24ACAC0);
  b.read_province_holder = reinterpret_cast<decltype(b.read_province_holder)>(base + 0x247D030);
  return b;
}

game::ArmyScopedOrderedRefillInputsV1 ReadScopedOrderedRefillInputs12003(
    const ck3_12002::ArmyBindings &b, void *army, void *unit,
    std::span<const game::ArmyRegimentReplenishmentRecordsSnapshotV1> data) {
  game::ArmyScopedOrderedRefillInputsV1 r{};
  const auto unavailable = [&](const char *why) { r.unavailable_reason = why; return r; };
  if (!b.scoped_ordered_refill_bindings.enabled || !army || !unit)
    return unavailable("scoped_ordered_refill_bindings_or_subject_unavailable");
  r.subject_army_id = Load<std::int32_t>(unit, 0x10);
  r.subject_carmy_id = Load<std::int32_t>(army, 0x10);
  if (!b.game_state_slot || !*b.game_state_slot) return unavailable("ordered_refill_game_data_unavailable");
  void *game_data = Load<void *>(*b.game_state_slot, 0xA0);
  if (!game_data) return unavailable("ordered_refill_game_data_unavailable");
  auto *manager = static_cast<std::byte *>(game_data) + 0x2A540;
  const void *ids = nullptr; std::int32_t count = 0;
  if (!List(manager, 0x30, ids, count)) return unavailable("ordered_persistent_roster_unavailable");
  r.native_persistent_occurrence_count = count;
  std::vector<std::int32_t> requested;
  bool partial = data.size() != static_cast<std::size_t>(Load<std::int32_t>(army, 0x44));
  for (const auto &snapshot : data) {
    partial = partial || snapshot.status != game::ArmyRegimentReplenishmentRecordsStatusV1::available;
    for (const auto &record : snapshot.records) {
      if (record.persistent_regiment_id == -1) { partial = true; continue; }
      if (std::find(requested.begin(), requested.end(), record.persistent_regiment_id) == requested.end())
        requested.push_back(record.persistent_regiment_id);
    }
  }
  for (std::int32_t index = 0; index < count; ++index) {
    const auto id = Load<std::int32_t>(ids, static_cast<std::size_t>(index) * 4);
    if (std::find(requested.begin(), requested.end(), id) != requested.end())
      r.persistent_occurrences.push_back({index, id});
  }
  if (!List(manager, 0x50, ids, count)) return unavailable("ordered_army_refresh_roster_unavailable");
  r.native_army_refresh_occurrence_count = count;
  for (std::int32_t index = 0; index < count; ++index)
    if (Load<std::int32_t>(ids, static_cast<std::size_t>(index) * 4) == r.subject_carmy_id)
      r.army_refresh_occurrence_indices.push_back(index);
  for (const auto id : requested) {
    game::ArmyOrderedRefillPersistentV1 persistent{}; persistent.persistent_regiment_id = id;
    void *object = Resolve(b.persistent_regiment_storage_slot, id);
    if (!object || Load<std::uint32_t>(object, 0x14) != 0x52656769U) {
      persistent.unavailable_reason = "requested_persistent_regiment_unresolved"; partial = true;
    } else {
      persistent.prepared_fraction_raw = Load<std::int64_t>(object, 0x148);
      for (std::int32_t index = 0; index < 7; ++index) {
        persistent.chunks.push_back(Chunk(b, static_cast<std::byte *>(object) + 0x18 + index * 0x24, index));
        partial = partial || !persistent.chunks.back().context_unavailable_reason.empty();
      }
    }
    r.persistent_regiments.push_back(std::move(persistent));
  }
  r.status = partial ? "partial" : "available";
  if (partial) r.unavailable_reason = "scoped_ordered_refill_inputs_partial";
  return r;
}
} // namespace xar::ck3_12003
