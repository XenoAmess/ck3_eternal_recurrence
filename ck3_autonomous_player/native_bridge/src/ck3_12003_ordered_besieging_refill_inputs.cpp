#include "xar_bridge/ck3_12003_ordered_besieging_refill_inputs.hpp"
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12003_scoped_ordered_refill_core.hpp"
#include <algorithm>
#include <cstddef>
#include <cstring>
#include <utility>

namespace xar::ck3_12003 {
namespace {
template<class T> T Load(const void *object, std::size_t offset) noexcept {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof value); return value;
}
void *Resolve(void **slot, std::int32_t id) noexcept {
  if (!slot || !*slot) return nullptr;
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(Load<std::int32_t>(*slot, 0x2C))) return nullptr;
  void *objects = Load<void *>(*slot, 0x20);
  if (!objects) return nullptr;
  void *object = Load<void *>(objects, static_cast<std::size_t>(index) * 0x10 + 8);
  return object && Load<std::int32_t>(object, 0x10) == id ? object : nullptr;
}
void *Fallback(void **slot) noexcept { return slot ? *slot : nullptr; }
bool List(const void *object, std::size_t offset, const void *&ids, std::int32_t &count) noexcept {
  ids = Load<void *>(object, offset); count = Load<std::int32_t>(object, offset + 0xC);
  return count >= 0 && (count == 0 || ids != nullptr);
}
bool Contains(const std::vector<std::int32_t> &ids, std::int32_t id) {
  return std::find(ids.begin(), ids.end(), id) != ids.end();
}
} // namespace

OrderedBesiegingRefillBindings12003 BindOrderedBesiegingRefillInputs12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  OrderedBesiegingRefillBindings12003 result{};
  if (!BindScopedOrderedRefillInputs12003(base, sha).enabled) return result;
  result.enabled = true;
  // Held24E814A rip-relative fallback load; exact same ArRg registry as ArmyBindings.
  result.arrg_fallback_slot = reinterpret_cast<void **>(base + 0x5D1F338);
  return result;
}

game::ArmyOrderedBesiegingRefillInputsV1 ReadOrderedBesiegingRefillInputs12003(
    const ck3_12002::ArmyBindings &b, void *army, void *unit,
    const game::ArmyCurrentProvinceBesiegingContributorsV1 &family) {
  game::ArmyOrderedBesiegingRefillInputsV1 r{};
  const auto unavailable = [&](const char *why) { r.unavailable_reason = why; return r; };
  if (!b.ordered_besieging_refill_bindings.enabled || !army || !unit)
    return unavailable("ordered_besieging_bindings_or_subject_unavailable");
  r.subject_army_id = Load<std::int32_t>(unit, 0x10);
  r.subject_carmy_id = Load<std::int32_t>(army, 0x10);
  r.province_id = family.province_id;
  std::vector<const game::ArmyProvinceBesiegingRegimentV1 *> targets;
  for (const auto &occurrence : family.occurrences) {
    if (occurrence.eligible != true) continue;
    for (const auto &regiment : occurrence.regiments) {
      if (regiment.available && regiment.army_regiment_id != -1 && !Contains(r.target_army_regiment_ids, regiment.army_regiment_id)) {
        r.target_army_regiment_ids.push_back(regiment.army_regiment_id); targets.push_back(&regiment);
      }
    }
  }
  if (!b.game_state_slot || !*b.game_state_slot) return unavailable("ordered_besieging_game_data_unavailable");
  void *game_data = Load<void *>(*b.game_state_slot, 0xA0);
  if (!game_data) return unavailable("ordered_besieging_game_data_unavailable");
  auto *manager = static_cast<std::byte *>(game_data) + 0x2A540;
  const void *army_ids = nullptr; std::int32_t count = 0;
  if (!List(manager, 0x50, army_ids, count)) return unavailable("ordered_besieging_refresh_roster_unavailable");
  r.native_army_refresh_occurrence_count = count;
  bool partial = !family.contributors_ready;
  r.refresh_membership_ready = true;
  std::vector<std::int32_t> refreshed;
  for (std::int32_t index = 0; index < count; ++index) {
    game::ArmyTargetRefreshOccurrenceV1 event{};
    event.manager_stored_index = index;
    event.raw_carmy_id = Load<std::int32_t>(army_ids, static_cast<std::size_t>(index) * 4);
    void *receiver = Resolve(b.internal_army_storage_slot, event.raw_carmy_id);
    event.army_used_fallback = receiver == nullptr;
    if (!receiver) receiver = Fallback(b.scoped_ordered_refill_bindings.army_fallback_slot);
    if (!receiver) { partial = true; r.refresh_membership_ready = false; continue; }
    event.resolved_carmy_id = Load<std::int32_t>(receiver, 0x10);
    const void *regiment_ids = nullptr; std::int32_t regiment_count = 0;
    if (!List(receiver, 0x38, regiment_ids, regiment_count)) {
      partial = true; r.refresh_membership_ready = false; continue;
    }
    event.native_regiment_occurrence_count = regiment_count;
    for (std::int32_t stored = 0; stored < regiment_count; ++stored) {
      const auto raw_id = Load<std::int32_t>(regiment_ids, static_cast<std::size_t>(stored) * 4);
      void *regiment = Resolve(b.regiment_storage_slot, raw_id);
      if (!regiment) regiment = Fallback(b.ordered_besieging_refill_bindings.arrg_fallback_slot);
      // Exact24E8180/89 guard before2633340. Invalid native fallback is skipped.
      if (!regiment) { partial = true; r.refresh_membership_ready = false; continue; }
      if (Load<std::uint32_t>(regiment, 0x14) != 0x41725267U || Load<std::int32_t>(regiment, 0x10) == -1) continue;
      const auto id = Load<std::int32_t>(regiment, 0x10);
      if (!Contains(r.target_army_regiment_ids, id)) continue;
      event.regiments.push_back({stored, raw_id, id});
      if (!Contains(refreshed, id)) refreshed.push_back(id);
    }
    if (!event.regiments.empty()) r.refresh_occurrences.push_back(std::move(event));
  }
  std::vector<std::int32_t> requested;
  for (const auto *target : targets) {
    if (!Contains(refreshed, target->army_regiment_id)) continue;
    if (!target->replenishment_records_v1) { partial = true; continue; }
    const auto &data = *target->replenishment_records_v1;
    if (data.native_loss_writer_skipped == true) continue; //2633340 special Character branch is1/1.
    partial = partial || data.status != game::ArmyRegimentReplenishmentRecordsStatusV1::available;
    for (const auto &record : data.records) {
      if (record.persistent_regiment_id == -1) { partial = true; continue; }
      if (!Contains(requested, record.persistent_regiment_id)) requested.push_back(record.persistent_regiment_id);
    }
  }
  const void *persistent_ids = nullptr;
  if (!List(manager, 0x30, persistent_ids, count)) return unavailable("ordered_besieging_persistent_roster_unavailable");
  r.native_persistent_occurrence_count = count;
  for (std::int32_t index = 0; index < count; ++index) {
    const auto id = Load<std::int32_t>(persistent_ids, static_cast<std::size_t>(index) * 4);
    if (Contains(requested, id)) r.persistent_occurrences.push_back({index, id});
  }
  for (auto id : requested) {
    auto persistent = ReadOrderedRefillPersistent12003(b, id);
    partial = partial || !persistent.unavailable_reason.empty();
    for (const auto &chunk : persistent.chunks) partial = partial || !chunk.context_unavailable_reason.empty();
    r.persistent_regiments.push_back(std::move(persistent));
  }
  r.status = partial ? "partial" : "available";
  if (partial) r.unavailable_reason = "ordered_besieging_refill_inputs_partial";
  return r;
}
} // namespace xar::ck3_12003
