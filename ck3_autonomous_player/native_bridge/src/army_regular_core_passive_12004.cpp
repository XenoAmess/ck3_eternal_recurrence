#include "xar_bridge/army_regular_core_passive_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/army_position_same_war_side_12004.hpp"
#include "xar_bridge/army_position_2c09280_12004.hpp"
#include "xar_bridge/army_position_2c09410_12004.hpp"
#include "xar_bridge/army_position_war_membership_12004.hpp"
#include "xar_bridge/army_position_relation_28b2800_12004.hpp"
#include "xar_bridge/army_position_2c3a0e0_readonly_12004.hpp"
#include <algorithm>
#include <cstring>
#include <limits>
#include <mutex>
#include <utility>
#if defined(_MSC_VER)
#include <intrin.h>
#endif

namespace xar::ck3_12004 {
namespace {
constexpr std::array<std::uint8_t, kArmyRegularCorePatchBytes12004> kPrologue{
  0x40,0x53,0x57,0x48,0x83,0xEC,0x48,0x48,0x8B,0x59,0x30,0x48,0x63,0x41,0x3C};
constexpr std::uintptr_t kPersistent = 0x5D1EB68, kPersistentFallback = 0x5D1EB58;
constexpr std::uintptr_t kArmy = 0x5D1DE48, kArmyFallback = 0x5D1DE50;
constexpr std::uintptr_t kArRg = 0x5D1F340, kArRgFallback = 0x5D1F338;
constexpr std::uintptr_t kUnit = 0x5D1E380, kUnitFallback = 0x5D1E378;
constexpr std::uintptr_t kCharacter = 0x5C67568, kCharacterFallback = 0x5C67570;
constexpr std::uintptr_t kCombat = 0x5D1DE70, kCombatFallback = 0x5D1DE18;
constexpr std::uintptr_t kTitle = 0x5D1DAF8, kTitleFallback = 0x5D1DAE0;
constexpr std::uintptr_t kWar = 0x5D1DE58, kWarFallback = 0x5D1DE40;
std::mutex g_mutex;
std::array<ArmyRegularCoreObservation12004, kArmyRegularCoreJournalCapacity12004> g_records;
std::uint64_t g_latest = 0, g_publication_failures = 0;
ArmyRegularCoreBindings12004 g_bindings;
std::atomic<bool> g_initialized{false};
std::atomic<ArmyRegularCoreOriginal12004> g_original{nullptr};
std::atomic<ArmyRegularCoreDetourState12004 *> g_state{nullptr};

template<class Function> bool FaultBoundary(Function function) noexcept {
#if defined(_MSC_VER)
  __try { return function(); }
  __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  return function();
#endif
}
bool DefaultRead(void *, std::uintptr_t address, void *out, std::size_t size) noexcept {
  if (!address) return false;
  return FaultBoundary([&]() noexcept { std::memcpy(out, reinterpret_cast<const void *>(address), size); return true; });
}
ArmyNaturalPhaseScope12004 DefaultScope(void *) noexcept { return CopyActiveArmyNaturalPhaseScope12004(); }

struct Resolution {
  std::uintptr_t object = 0;
  std::optional<std::int32_t> full_id;
  std::optional<bool> fallback;
  std::string reason;
};
class Reader {
 public:
  Reader(const ArmyRegularCoreBindings12004 &bindings, ArmyRegularCoreFrame12004 &frame)
      : b(bindings), f(frame) {}
  bool Read(std::uintptr_t address, void *out, std::size_t size) noexcept {
    if (!address || size > b.maximum_read_bytes - (std::min)(used, b.maximum_read_bytes)) return false;
    used += size;
    const auto read = b.read ? b.read : &DefaultRead;
    return FaultBoundary([&]() noexcept { return read(b.read_context, address, out, size); });
  }
  template<class T> bool At(std::uintptr_t address, std::size_t offset, T &out) noexcept {
    if (!address || offset > (std::numeric_limits<std::uintptr_t>::max)() - address) return false;
    return Read(address + offset, &out, sizeof out);
  }
  template<class T> std::optional<T> Field(std::uintptr_t address, std::size_t offset) noexcept {
    T out{}; return At(address, offset, out) ? std::optional<T>(out) : std::nullopt;
  }
  std::uintptr_t Slot(std::uintptr_t rva, bool &ok) noexcept {
    std::uintptr_t out = 0;
    ok = b.image_base && rva <= (std::numeric_limits<std::uintptr_t>::max)() - b.image_base &&
        At(b.image_base, rva, out);
    return out;
  }
  Resolution Resolve(std::uintptr_t slot, std::uintptr_t fallback_slot,
                     std::int32_t raw, std::size_t id_offset = 0x10) {
    Resolution r;
    bool ok = false; const auto registry = Slot(slot, ok);
    if (!ok) { r.reason = "native_registry_slot_unreadable"; return r; }
    bool fallback = !registry;
    if (registry) {
      std::int32_t count = 0;
      if (!At(registry, 0x2C, count) || count < 0 || count > 1'000'000) {
        r.reason = "native_registry_count_unreadable_or_capture_bound"; return r;
      }
      const auto index = static_cast<std::uint32_t>(raw) & 0xFFFFFFU;
      fallback = index >= static_cast<std::uint32_t>(count);
      if (!fallback) {
        std::uintptr_t table = 0, object = 0;
        if (!At(registry, 0x20, table) || !At(table, std::size_t(index) * 16 + 8, object)) {
          r.reason = "native_registry_record_unreadable"; return r;
        }
        fallback = !object;
        if (object) {
          std::int32_t identity = 0;
          if (!At(object, id_offset, identity)) { r.reason = "native_generation_identity_unreadable"; return r; }
          fallback = identity != raw;
          if (!fallback) { r.object = object; r.full_id = identity; }
        }
      }
    }
    r.fallback = fallback;
    if (fallback) {
      r.object = Slot(fallback_slot, ok);
      if (!ok || !r.object) { r.reason = "native_fallback_slot_or_object_unreadable"; return r; }
      r.full_id = Field<std::int32_t>(r.object, id_offset);
      if (!r.full_id) r.reason = "native_fallback_identity_unreadable";
    }
    return r;
  }
  void Missing(std::string reason) {
    if (std::find(f.missing_inputs.begin(), f.missing_inputs.end(), reason) == f.missing_inputs.end())
      f.missing_inputs.push_back(std::move(reason));
  }
  bool Roster(std::uintptr_t object, std::size_t offset,
              std::optional<std::int32_t> &count, std::vector<std::optional<std::int32_t>> &ids,
              const char *name) {
    count = Field<std::int32_t>(object, offset + 12);
    std::uintptr_t array = 0;
    if (!count || *count < 0 || static_cast<std::size_t>(*count) > b.maximum_occurrences ||
        !At(object, offset, array) || (*count && !array)) { Missing(name); return false; }
    ids.reserve(static_cast<std::size_t>(*count));
    for (std::int32_t i = 0; i < *count; ++i) {
      auto id = Field<std::int32_t>(array, static_cast<std::size_t>(i) * 4);
      if (!id) Missing(name);
      ids.push_back(id);
    }
    return true;
  }
  ArmyRegularCoreOccurrence12004 Occurrence(std::int32_t index, std::optional<std::int32_t> raw,
                                           std::uintptr_t slot, std::uintptr_t fallback,
                                           std::size_t identity_offset = 0x10) {
    ArmyRegularCoreOccurrence12004 out; out.stored_index = index; out.raw_full_id = raw;
    if (!raw) { out.unavailable_reason = "original_occurrence_FullID_unreadable"; return out; }
    auto r = Resolve(slot, fallback, *raw, identity_offset);
    out.resolved_full_id = r.full_id; out.physical_token = r.object;
    out.used_fallback = r.fallback; out.unavailable_reason = std::move(r.reason);
    if (!out.unavailable_reason.empty()) Missing(out.unavailable_reason);
    return out;
  }
  ArmyRegularCoreReadonlyAccess12004 Access() noexcept {
    return {b.image_base, this, &BudgetRead, b.maximum_occurrences};
  }
  static bool BudgetRead(void *context, std::uintptr_t address, void *out, std::size_t size) noexcept {
    return static_cast<Reader *>(context)->Read(address, out, size);
  }
  std::optional<bool> CharacterPredicate(std::uintptr_t arrg) {
    auto raw = Field<std::int32_t>(arrg, 0x148);
    if (!raw) return std::nullopt;
    if (*raw == -1) return false;
    auto character = Resolve(kCharacter, kCharacterFallback, *raw, 0x18);
    if (!character.full_id) return std::nullopt;
    auto magic = Field<std::uint32_t>(character.object, 0x1C);
    if (!magic) return std::nullopt;
    return *magic == 0x43686172U && *character.full_id != -1;
  }
  std::optional<bool> CombatPredicate(std::uintptr_t army) {
    auto raw = Field<std::int32_t>(army, 0x128);
    if (!raw) return std::nullopt;
    auto combat = Resolve(kCombat, kCombatFallback, *raw, 8);
    if (!combat.full_id) return std::nullopt;
    auto magic = Field<std::uint32_t>(combat.object, 0xC);
    if (!magic) return std::nullopt;
    return *magic == 0x436F6D62U && *combat.full_id != -1;
  }
  std::optional<std::int32_t> ProvinceHolder(std::uintptr_t province) {
    auto explicit_holder = Field<std::int32_t>(province, 0x73C);
    if (!explicit_holder) return std::nullopt;
    if (*explicit_holder != -1) return explicit_holder;
    auto title_id = Field<std::int32_t>(province, 0x738);
    if (!title_id) return std::nullopt;
    auto title = Resolve(kTitle, kTitleFallback, *title_id);
    if (!title.full_id) return std::nullopt;
    auto definition = Field<std::uintptr_t>(title.object, 0x48);
    if (!definition || !*definition) return std::nullopt;
    auto kind = Field<std::int32_t>(*definition, 0x64);
    if (!kind) return std::nullopt;
    if (*kind != 1) return -1;
    auto liege_id = Field<std::int32_t>(title.object, 0xE8);
    if (!liege_id) return std::nullopt;
    auto liege = Resolve(kTitle, kTitleFallback, *liege_id);
    if (!liege.full_id) return std::nullopt;
    return Field<std::int32_t>(liege.object, 0x128);
  }
  std::optional<bool> PositionPolitical(std::uintptr_t actor, std::uintptr_t holder,
                                       std::int32_t actor_id, std::int32_t holder_id) {
    // Actual2C09817 tests complete DWORD IDs before all six subordinate calls.
    if (actor_id == holder_id) return true;
    const auto access = Access(); const auto &p = b.position_predicates;
    const auto pair = [&](ArmyRegularCorePairPredicate12004 fn, std::uintptr_t left, std::uintptr_t right) {
      return fn ? fn(access, left, right, 0).value : std::optional<bool>{};
    };
    auto common = pair(p.common_war_side_2C090D0, actor, holder);
    if (!common) return std::nullopt;
    if (!*common) {
      for (const auto fn : {p.relation_2C09280, p.relation_2C09410}) {
        auto value = pair(fn, actor, holder); if (!value) return std::nullopt; if (*value) return false;
        value = pair(fn, holder, actor); if (!value) return std::nullopt; if (*value) return false;
      }
    }
    common = pair(p.common_war_side_2C090D0, actor, holder);
    if (!common) return std::nullopt;
    if (*common) return true;
    auto state = Field<std::uintptr_t>(actor, 0x1C0);
    if (!state) return std::nullopt;
    const auto descriptor = *state ? *state + 0x318 : b.image_base + 0x5459D38;
    std::optional<std::int32_t> war_count;
    std::vector<std::optional<std::int32_t>> ids;
    if (!Roster(descriptor, 0, war_count, ids, "position_actor_war_roster_unavailable")) return std::nullopt;
    for (const auto id : ids) {
      if (!id) return std::nullopt;
      auto war = Resolve(kWar, kWarFallback, *id, 8);
      if (!war.full_id) return std::nullopt;
      if (!p.membership_2494B40) return std::nullopt;
      auto side = war.object + 0x20;
      auto contains = p.membership_2494B40(access, side, actor_id).value;
      if (!contains) return std::nullopt;
      if (!*contains) {
        side = war.object + 0x80;
        contains = p.membership_2494B40(access, side, actor_id).value;
        if (!contains) return std::nullopt;
        if (!*contains) continue;
      }
      auto begin = Field<std::uintptr_t>(side, 8);
      auto count = Field<std::int32_t>(side, 0x14);
      if (!begin || !count || *count < 0 || static_cast<std::size_t>(*count) > b.maximum_occurrences ||
          (*count && !*begin)) return std::nullopt;
      for (std::int32_t i = 0; i < *count; ++i) {
        auto record = Field<std::uintptr_t>(*begin, static_cast<std::size_t>(i) * 8);
        if (!record || !*record) return std::nullopt;
        auto identity = Field<std::int32_t>(*record, 8);
        if (!identity) return std::nullopt;
        if (*identity == actor_id) continue;
        if (!p.holder_relation_28B2800) return std::nullopt;
        auto relation = p.holder_relation_28B2800(access, holder, *identity).value;
        if (!relation) return std::nullopt;
        if (*relation) return true;
      }
    }
    if (!p.holder_relation_28B2800) return std::nullopt;
    auto relation = p.holder_relation_28B2800(access, holder, actor_id).value;
    if (!relation) return std::nullopt;
    if (*relation) return true;
    return p.final_relation_2C3A0E0 ? p.final_relation_2C3A0E0(access, holder, actor).value : std::nullopt;
  }
  void Context(game::ArmyOrderedRefillChunkV1 &chunk) {
    auto owner = Resolve(kPersistent, kPersistentFallback, chunk.owner_persistent_regiment_id);
    const auto missing = [&](const char *why) { if (chunk.context_unavailable_reason.empty()) chunk.context_unavailable_reason = why; };
    chunk.owner_resolved_full_id = owner.full_id;
    chunk.owner_guard_138_raw = Field<std::int32_t>(owner.object, 0x138);
    auto definition = Field<std::uintptr_t>(owner.object, 0x118);
    if (definition && *definition) chunk.owner_definition_magic_38_raw = Field<std::uint32_t>(*definition, 0x38);
    if (!chunk.owner_guard_138_raw || !chunk.owner_definition_magic_38_raw) missing("entry_raw_owner_cleanup_context_unreadable");
    auto province = Field<std::uintptr_t>(owner.object, 0x120);
    if (province && *province) {
      chunk.origin_province_id = Field<std::int32_t>(*province, 0x10);
      chunk.origin_province_788_raw = Field<std::int32_t>(*province, 0x788);
      chunk.origin_province_73c_raw = Field<std::int32_t>(*province, 0x73C);
    }
    if (!chunk.origin_province_788_raw || !chunk.origin_province_73c_raw) missing("entry_raw_origin_province_unreadable");
    auto arrg = Resolve(kArRg, kArRgFallback, chunk.army_regiment_id_raw);
    chunk.associated_arrg_resolved_full_id = arrg.full_id;
    chunk.associated_arrg_magic_raw = Field<std::uint32_t>(arrg.object, 0x14);
    if (!arrg.full_id || !chunk.associated_arrg_magic_raw) { missing("entry_associated_ArRg_unreadable"); return; }
    if (*arrg.full_id == -1 || *chunk.associated_arrg_magic_raw != 0x41725267U) return;
    chunk.associated_army_raw_full_id = Field<std::int32_t>(arrg.object, 0x140);
    if (!chunk.associated_army_raw_full_id) { missing("entry_associated_Army_FullID_unreadable"); return; }
    auto army = Resolve(kArmy, kArmyFallback, *chunk.associated_army_raw_full_id);
    chunk.associated_army_resolved_full_id = army.full_id;
    chunk.army_byte_1d4_raw = Field<std::uint8_t>(army.object, 0x1D4);
    chunk.army_byte_1ec_raw = Field<std::uint8_t>(army.object, 0x1EC);
    chunk.native_army_in_combat = CombatPredicate(army.object);
    chunk.associated_unit_raw_full_id = Field<std::int32_t>(army.object, 0x124);
    if (!chunk.associated_unit_raw_full_id) { missing("entry_associated_Unit_FullID_unreadable"); return; }
    auto unit = Resolve(kUnit, kUnitFallback, *chunk.associated_unit_raw_full_id);
    chunk.associated_unit_resolved_full_id = unit.full_id;
    chunk.unit_170_raw = Field<std::int32_t>(unit.object, 0x170);
    auto position = Field<std::uintptr_t>(unit.object, 0x20);
    if (!position) { missing("entry_Unit_position_pointer_unreadable"); return; }
    if (!*position) { bool ok = false; position = Slot(0x5D1E390, ok); if (!ok) position = std::nullopt; }
    if (!position || !*position) { missing("entry_Unit_position_fallback_unreadable"); return; }
    chunk.unit_position_province_magic_raw = Field<std::uint32_t>(*position, 0x85C);
    if (!chunk.unit_position_province_magic_raw) { missing("entry_position_Province_magic_unreadable"); return; }
    if (*chunk.unit_position_province_magic_raw != 0x50726F76U) { chunk.native_unit_position_eligible = false; return; }
    auto actor_raw = Field<std::int32_t>(unit.object, 0x174);
    auto holder_raw = ProvinceHolder(*position);
    if (!actor_raw || !holder_raw) { missing("entry_position_actor_or_holder_raw_unreadable"); return; }
    auto actor = Resolve(kCharacter, kCharacterFallback, *actor_raw, 0x18);
    auto holder = Resolve(kCharacter, kCharacterFallback, *holder_raw, 0x18);
    chunk.unit_position_owner_resolved_full_id = actor.full_id;
    chunk.unit_position_holder_resolved_full_id = holder.full_id;
    if (!actor.full_id || !holder.full_id) { missing("entry_position_actor_or_holder_resolution_unreadable"); return; }
    chunk.native_unit_position_eligible = PositionPolitical(actor.object, holder.object, *actor.full_id, *holder.full_id);
    if (!chunk.native_unit_position_eligible) missing("entry_position_native_political_raw_dependency_unavailable");
  }
  bool Persistent(std::uintptr_t object, bool manager_receiver) {
    auto found = std::find_if(f.persistent_objects.begin(), f.persistent_objects.end(),
        [&](const auto &item) { return item.physical_token == object; });
    if (found != f.persistent_objects.end()) {
      if (manager_receiver && !found->prepared_fraction_raw) Missing("entry_manager_receiver_prepared148_unreadable");
      return found->chunks.size() == 7 && found->resolved_full_id.has_value();
    }
    if (!object || f.persistent_objects.size() + f.army_objects.size() >= b.maximum_physical_objects) {
      Missing("entry_physical_object_materialization_bound"); return false;
    }
    ArmyRegularCorePersistent12004 p; p.physical_token = object;
    p.resolved_full_id = Field<std::int32_t>(object, 0x10);
    p.prepared_fraction_raw = Field<std::int64_t>(object, 0x148);
    std::array<std::byte, 7 * 0x24> bytes{};
    if (!p.resolved_full_id || !At(object, 0x18, bytes)) {
      p.unavailable_reason = "entry_complete_physical_seven_unreadable"; Missing(p.unavailable_reason);
    } else {
      for (std::int32_t i = 0; i < 7; ++i) {
        const auto *raw = bytes.data() + std::size_t(i) * 0x24;
        game::ArmyOrderedRefillChunkV1 chunk; chunk.physical_index = i;
        const auto integer = [&](std::size_t offset) { std::int32_t value; std::memcpy(&value, raw + offset, sizeof value); return value; };
        chunk.maximum_soldiers = integer(0); chunk.current_soldiers = integer(4);
        chunk.owner_persistent_regiment_id = integer(8); chunk.q_ordinal_raw = integer(0xC);
        chunk.army_regiment_id_raw = integer(0x10); chunk.state_raw = integer(0x18);
        chunk.exclusion_byte_14_raw = std::to_integer<std::uint8_t>(raw[0x14]);
        Context(chunk); p.chunks.push_back(std::move(chunk));
      }
      const auto identity_after = Field<std::int32_t>(object, 0x10);
      if (!identity_after || identity_after != p.resolved_full_id) {
        p.unavailable_reason = "entry_physical_generation_changed_during_capture"; Missing(p.unavailable_reason);
      }
    }
    if (manager_receiver && !p.prepared_fraction_raw) Missing("entry_manager_receiver_prepared148_unreadable");
    const bool complete = p.chunks.size() == 7 && p.resolved_full_id.has_value() && p.unavailable_reason.empty();
    f.persistent_objects.push_back(std::move(p)); return complete;
  }
  ArmyRegularCoreArRg12004 ArRg(std::int32_t index, std::optional<std::int32_t> id) {
    ArmyRegularCoreArRg12004 a; a.occurrence = Occurrence(index, id, kArRg, kArRgFallback);
    const auto object = a.occurrence.physical_token;
    a.resolved_magic_14_raw = Field<std::uint32_t>(object, 0x14);
    if (!a.occurrence.resolved_full_id || !a.resolved_magic_14_raw) {
      a.unavailable_reason = "entry_ArRg_dispatch_admission_unreadable"; Missing(a.unavailable_reason); return a;
    }
    a.native_refresh_admitted = *a.resolved_magic_14_raw == 0x41725267U && *a.occurrence.resolved_full_id != -1;
    if (!*a.native_refresh_admitted) { a.records_complete = true; return a; }
    a.native_loss_writer_skipped = CharacterPredicate(object);
    a.native_record_count = Field<std::int32_t>(object, 0x2C);
    if (!a.native_loss_writer_skipped) {
      a.unavailable_reason = "entry_native_character_predicate_unreadable"; Missing(a.unavailable_reason); return a;
    }
    // Qualified current/max override needs no DATA traversal. Other statistics/lifecycle remain excluded.
    if (*a.native_loss_writer_skipped) { a.records_complete = true; return a; }
    auto data = Field<std::uintptr_t>(object, 0x20);
    if (!a.native_record_count || *a.native_record_count < 0 ||
        static_cast<std::size_t>(*a.native_record_count) > b.maximum_occurrences ||
        static_cast<std::size_t>(*a.native_record_count) > b.maximum_total_data_records - (std::min)(total_data, b.maximum_total_data_records) ||
        !data || (*a.native_record_count && !*data)) {
      a.unavailable_reason = "entry_complete_DATA_roster_unavailable_or_bound"; Missing(a.unavailable_reason); return a;
    }
    total_data += static_cast<std::size_t>(*a.native_record_count);
    a.records_complete = true;
    for (std::int32_t i = 0; i < *a.native_record_count; ++i) {
      ArmyRegularCoreDataRecord12004 row; row.record_index = i;
      const auto record = *data + static_cast<std::size_t>(i) * 16;
      row.persistent_regiment_id = Field<std::int32_t>(record, 8);
      row.chunk_index = Field<std::int32_t>(record, 0xC);
      if (row.persistent_regiment_id && row.chunk_index) {
        auto persistent = Resolve(kPersistent, kPersistentFallback, *row.persistent_regiment_id);
        row.persistent_physical_token = persistent.object;
        auto magic = Field<std::uint32_t>(persistent.object, 0x14);
        if (persistent.full_id && magic && *magic == 0x52656769U && *persistent.full_id != -1 &&
            *row.chunk_index >= 0 && *row.chunk_index < 7 && Persistent(persistent.object, false)) {
          const auto captured = std::find_if(f.persistent_objects.begin(), f.persistent_objects.end(),
              [&](const auto &item) { return item.physical_token == persistent.object; });
          if (captured != f.persistent_objects.end() && captured->chunks.size() == 7)
            row.state_raw = captured->chunks[static_cast<std::size_t>(*row.chunk_index)].state_raw;
          row.native_record_admitted = row.state_raw.has_value();
        }
      }
      if (!row.native_record_admitted) {
        row.unavailable_reason = "entry_DATA_invalid_or_unbounded_lifecycle_branch";
        a.records_complete = false; Missing(row.unavailable_reason);
      }
      a.records.push_back(std::move(row));
    }
    if (!a.records_complete) a.unavailable_reason = "entry_complete_admitted_DATA_unavailable";
    return a;
  }
  void ArmyObject(std::uintptr_t object) {
    if (std::any_of(f.army_objects.begin(), f.army_objects.end(), [&](const auto &a) { return a.physical_token == object; })) return;
    if (!object || f.persistent_objects.size() + f.army_objects.size() >= b.maximum_physical_objects) {
      Missing("entry_physical_Army_materialization_bound"); return;
    }
    ArmyRegularCoreArmy12004 a; a.physical_token = object; a.resolved_full_id = Field<std::int32_t>(object, 0x10);
    std::vector<std::optional<std::int32_t>> ids;
    if (!Roster(object, 0x38, a.native_arrg_occurrence_count, ids, "entry_complete_Army_ArRg_roster_unavailable"))
      a.unavailable_reason = "entry_complete_Army_ArRg_roster_unavailable";
    for (std::size_t i = 0; i < ids.size(); ++i) a.arrg_occurrences.push_back(ArRg(static_cast<std::int32_t>(i), ids[i]));
    if (!a.resolved_full_id) Missing("entry_Army_resolved_identity_unreadable");
    f.army_objects.push_back(std::move(a));
  }
  const ArmyRegularCoreBindings12004 &b;
  ArmyRegularCoreFrame12004 &f;
  std::size_t used = 0, total_data = 0;
};

bool SameEvent(const ArmyNaturalPhaseEvent12004 &a, const ArmyNaturalPhaseEvent12004 &b) noexcept {
  return a.clock_identity && a.clock_identity == b.clock_identity && a.thread_id && a.thread_id == b.thread_id;
}
bool ParentValid(const ArmyNaturalPhaseScope12004 &scope, const ArmyNaturalPhaseEvent12004 &event,
                 std::uintptr_t manager, std::uintptr_t caller) noexcept {
  return scope.observed && scope.phase == ArmyNaturalPhaseKind12004::post_date &&
      scope.actual_entry_rva == kArmyNaturalPostDateRva12004 && scope.primary_manager_identity == manager &&
      scope.secondary_manager_identity == manager + 8 && caller == kArmyRegularCoreCallerReturnRva12004 &&
      scope.game_state_identity && scope.date_raw && SameEvent(scope.entry_event, event) &&
      scope.entry_event.sequence < event.sequence;
}
std::optional<std::uint64_t> CaptureDate(const ArmyRegularCoreBindings12004 &b,
                                       const ArmyNaturalPhaseScope12004 &scope) noexcept {
  std::uint64_t date = 0; const auto read = b.read ? b.read : &DefaultRead;
  const bool ok = scope.game_state_identity && FaultBoundary([&]() noexcept {
    return read(b.read_context, scope.game_state_identity + 8, &date, sizeof date);
  });
  return ok ? std::optional<std::uint64_t>(date) : std::nullopt;
}
void Publish(ArmyRegularCoreObservation12004 &event) noexcept {
  try {
    const std::lock_guard lock(g_mutex);
    const auto next = g_latest + 1;
    event.journal_sequence = next;
    g_records[(next - 1) % g_records.size()] = event;
    g_latest = next;
  } catch (...) {
    const std::lock_guard lock(g_mutex); ++g_publication_failures;
  }
}
} // namespace

ArmyRegularCoreBindings12004 BindArmyRegularCoreImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  ArmyRegularCoreBindings12004 b;
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true; b.image_base = base; b.read = &DefaultRead;
  b.next_event = &NextArmyNaturalPhaseEvent12004; b.read_scope = &DefaultScope;
  b.position_predicates = {&ReadArmyPosition2C090D012004, &ReadArmyPosition2C0928012004,
      &ReadArmyPosition2C0941012004, &ReadArmyPosition2494B4012004,
      &ReadArmyPosition28B280012004, &ReadArmyPosition2C3A0E012004};
  return b;
}
ArmyRegularCoreFrame12004 CaptureArmyRegularCoreFrame12004(
    const ArmyRegularCoreBindings12004 &b, const void *manager) noexcept {
  ArmyRegularCoreFrame12004 f;
  try {
    if (!b.enabled || !b.image_base || !manager) { f.missing_inputs.push_back("exact_regular_core_binding_or_receiver_unavailable"); return f; }
    Reader r(b, f); const auto object = reinterpret_cast<std::uintptr_t>(manager);
    std::vector<std::optional<std::int32_t>> persist, armies;
    r.Roster(object, 0x30, f.native_persistent_occurrence_count, persist, "complete_original_manager_persistent_roster_unavailable");
    r.Roster(object, 0x50, f.native_army_refresh_occurrence_count, armies, "complete_original_manager_Army_roster_unavailable");
    for (std::size_t i = 0; i < persist.size(); ++i) {
      auto row = r.Occurrence(static_cast<std::int32_t>(i), persist[i], kPersistent, kPersistentFallback);
      if (row.physical_token) r.Persistent(row.physical_token, true);
      f.persistent_occurrences.push_back(std::move(row));
    }
    for (std::size_t i = 0; i < armies.size(); ++i) {
      auto row = r.Occurrence(static_cast<std::int32_t>(i), armies[i], kArmy, kArmyFallback);
      if (row.physical_token) r.ArmyObject(row.physical_token);
      f.army_refresh_occurrences.push_back(std::move(row));
    }
    f.capture_complete = f.missing_inputs.empty();
  } catch (...) {
    f.capture_complete = false;
    try { f.missing_inputs.push_back("regular_core_owned_capture_exception"); } catch (...) {}
  }
  return f;
}
ArmyRegularCoreObservation12004 InvokeArmyRegularCorePassive12004(
    const ArmyRegularCoreBindings12004 &b, ArmyRegularCoreOriginal12004 original,
    void *manager, std::uintptr_t caller) noexcept {
  ArmyRegularCoreObservation12004 event;
  event.manager_identity = reinterpret_cast<std::uintptr_t>(manager); event.caller_return_rva = caller;
  try {
    if (b.enabled && b.next_event && b.read_scope) {
      event.entry_event = b.next_event(b.event_context);
      auto scope = b.read_scope(b.scope_context);
      bool mask_proved = false;
      if (ParentValid(scope, event.entry_event, event.manager_identity, caller)) {
        // Literal source branch proves mask2 at this reached return PC, not the entire saved C0 byte.
        mask_proved = ObserveArmyNaturalPhaseSavedMask12004(scope.secondary_manager_identity, caller, 2);
        scope = b.read_scope(b.scope_context);
      }
      event.parent_scope = std::move(scope);
      event.entry_date_raw = CaptureDate(b, event.parent_scope);
      event.entry_provenance_complete = ParentValid(event.parent_scope, event.entry_event,
          event.manager_identity, caller) && mask_proved && event.parent_scope.saved_mask02_admitted == true &&
          event.parent_scope.saved_c0_observed_rva == caller && event.entry_date_raw == event.parent_scope.date_raw;
      if (event.entry_provenance_complete) {
        event.observed = true; event.entry = CaptureArmyRegularCoreFrame12004(b, manager);
        if (CaptureDate(b, event.parent_scope) != event.entry_date_raw) {
          event.entry_provenance_complete = false; event.entry.capture_complete = false;
          event.entry.missing_inputs.push_back("entry_date_changed_during_owned_capture");
        }
      } else event.provenance_failures.push_back("genuine_same_thread_postdate_core_entry_provenance_unavailable");
    } else event.provenance_failures.push_back("regular_core_scope_or_shared_event_clock_unavailable");
  } catch (...) {
    event.entry_provenance_complete = false;
  }
  if (!original) return event;
  // Exactly once, outside observer read/capture fault boundaries. Save the full opaque native RAX bits immediately.
  event.original_called = true;
  event.raw_return_bits = original(manager);
  event.original_returned = true;
  try {
    if (b.next_event && b.read_scope) {
      event.returned_event = b.next_event(b.event_context);
      const auto after_scope = b.read_scope(b.scope_context);
      event.returned_date_raw = CaptureDate(b, after_scope);
      event.return_provenance_complete = event.entry_provenance_complete &&
          ParentValid(after_scope, event.returned_event, event.manager_identity, caller) &&
          after_scope.entry_event.sequence == event.parent_scope.entry_event.sequence &&
          SameEvent(event.entry_event, event.returned_event) && event.entry_event.sequence < event.returned_event.sequence &&
          event.returned_date_raw == event.entry_date_raw;
      if (event.return_provenance_complete) {
        event.returned = CaptureArmyRegularCoreFrame12004(b, manager);
        if (CaptureDate(b, after_scope) != event.returned_date_raw) {
          event.return_provenance_complete = false; event.returned.capture_complete = false;
          event.returned.missing_inputs.push_back("return_date_changed_during_owned_capture");
        }
      }
      else event.provenance_failures.push_back("regular_core_return_clock_parent_thread_or_date_changed");
    }
  } catch (...) { event.return_provenance_complete = false; }
  Publish(event);
  return event;
}
ArmyRegularCoreJournal12004 ReadArmyRegularCoreJournal12004() noexcept {
  ArmyRegularCoreJournal12004 out;
  try {
    out.observer_initialized = g_initialized.load(std::memory_order_acquire);
    const auto state = g_state.load(std::memory_order_acquire);
    out.observer_installed = state && state->installed.load(std::memory_order_acquire);
    const std::lock_guard lock(g_mutex);
    out.latest_journal_sequence = g_latest; out.publication_failures = g_publication_failures;
    out.overwritten_events = g_latest > g_records.size() ? g_latest - g_records.size() : 0;
    const auto first = g_latest > g_records.size() ? g_latest - g_records.size() + 1 : 1;
    for (auto i = first; i <= g_latest; ++i) {
      const auto &event = g_records[(i - 1) % g_records.size()];
      if (event.journal_sequence == i) out.events.push_back(event);
    }
  } catch (...) { out.events.clear(); out.observer_initialized = false; }
  return out;
}
void ClearArmyRegularCoreJournal12004() noexcept {
  try { const std::lock_guard lock(g_mutex); g_latest = 0; g_publication_failures = 0; for (auto &event : g_records) event = {}; } catch (...) {}
}
bool InitializeArmyRegularCoreFixture12004(const ArmyRegularCoreBindings12004 &b,
                                         ArmyRegularCoreOriginal12004 original) noexcept {
  if (!b.enabled || !original || g_state.load(std::memory_order_acquire)) return false;
  try {
    g_initialized.store(false, std::memory_order_release); ClearArmyRegularCoreJournal12004();
    g_bindings = b; g_original.store(original, std::memory_order_release);
    g_initialized.store(true, std::memory_order_release); return true;
  } catch (...) { return false; }
}
extern "C" std::uintptr_t __fastcall XarArmyRegularCoreHook12004(void *manager) noexcept {
  const auto original = g_original.load(std::memory_order_acquire);
#if defined(_MSC_VER)
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
#else
  const auto caller = reinterpret_cast<std::uintptr_t>(__builtin_return_address(0));
#endif
  const auto rva = caller >= g_bindings.image_base ? caller - g_bindings.image_base : 0;
  auto event = InvokeArmyRegularCorePassive12004(g_bindings, original, manager, rva);
  return event.raw_return_bits;
}

namespace {
constexpr std::size_t kJumpBytes = 14;
constexpr std::size_t kTrampolineBytes = kArmyRegularCorePatchBytes12004 + kJumpBytes;
enum : std::uint32_t { kBindingFailure = 1, kAnchorFailure = 2, kAllocationFailure = 4,
  kProtectionFailure = 8, kPublicationFailure = 16, kRollbackFailure = 32, kFreeFailure = 64 };
void *DefaultAllocate(void *, std::size_t size, DWORD type, DWORD protection) noexcept {
  return ::VirtualAlloc(nullptr, size, type, protection);
}
bool DefaultFree(void *, void *address, std::size_t size, DWORD type) noexcept {
  return ::VirtualFree(address, size, type) != FALSE;
}
bool DefaultProtect(void *, void *address, std::size_t size, DWORD protection, DWORD &old) noexcept {
  return ::VirtualProtect(address, size, protection, &old) != FALSE;
}
bool DefaultFlush(void *, const void *address, std::size_t size) noexcept {
  return ::FlushInstructionCache(::GetCurrentProcess(), address, size) != FALSE;
}
void AbsoluteJump(std::uint8_t *bytes, std::uintptr_t destination) noexcept {
  bytes[0] = 0xFF; bytes[1] = 0x25;
  std::memset(bytes + 2, 0, 4);
  std::memcpy(bytes + 6, &destination, sizeof destination);
}
bool CopyBytes(void *destination, const void *source, std::size_t size) noexcept {
  return FaultBoundary([&]() noexcept { std::memcpy(destination, source, size); return true; });
}
std::array<std::uint8_t, kArmyRegularCorePatchBytes12004> HookPatch() noexcept {
  std::array<std::uint8_t, kArmyRegularCorePatchBytes12004> bytes{};
  AbsoluteJump(bytes.data(), reinterpret_cast<std::uintptr_t>(&XarArmyRegularCoreHook12004));
  bytes[kJumpBytes] = 0x90; return bytes;
}
} // namespace

bool InstallArmyRegularCorePassive12004(ArmyRegularCoreDetourState12004 &state,
    const ArmyRegularCoreInstallEnvironment12004 &environment, std::string_view sha) noexcept {
  // The literal 15B prefix consists of five complete non-relative instructions.
  // Every patch/rollback runs only under the caller's fresh cold/quiescent proof.
  if (sha != kExecutableSha256 || !environment.primary_thread_suspended_proven ||
      !environment.bindings.enabled || !environment.bindings.image_base ||
      !environment.bindings.next_event || !environment.bindings.read_scope ||
      state.installed.load(std::memory_order_acquire) || state.trampoline ||
      g_state.load(std::memory_order_acquire)) {
    state.failure_flags.fetch_or(kBindingFailure); return false;
  }
  const auto base = environment.bindings.image_base;
  if (!environment.target_override && kArmyRegularCoreRva12004 > (std::numeric_limits<std::uintptr_t>::max)() - base) {
    state.failure_flags.fetch_or(kBindingFailure); return false;
  }
  const auto target = environment.target_override ? environment.target_override : base + kArmyRegularCoreRva12004;
  std::array<std::uint8_t, kArmyRegularCorePatchBytes12004> anchor{};
  if (!CopyBytes(anchor.data(), reinterpret_cast<const void *>(target), anchor.size()) || anchor != kPrologue) {
    state.failure_flags.fetch_or(kAnchorFailure); return false;
  }
  const auto allocate = environment.allocate ? environment.allocate : &DefaultAllocate;
  state.memory_context = environment.memory_context;
  state.free = environment.free ? environment.free : &DefaultFree;
  state.protect = environment.protect ? environment.protect : &DefaultProtect;
  state.flush = environment.flush ? environment.flush : &DefaultFlush;
  state.target = target; state.original_bytes = anchor;
  state.trampoline = allocate(state.memory_context, kTrampolineBytes, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (!state.trampoline) { state.failure_flags.fetch_or(kAllocationFailure); return false; }
  const auto discard = [&]() noexcept {
    if (state.free(state.memory_context, state.trampoline, 0, MEM_RELEASE)) state.trampoline = nullptr;
    else state.failure_flags.fetch_or(kFreeFailure);
  };
  std::array<std::uint8_t, kTrampolineBytes> trampoline{};
  std::copy(anchor.begin(), anchor.end(), trampoline.begin());
  AbsoluteJump(trampoline.data() + anchor.size(), target + anchor.size());
  DWORD old_trampoline = 0;
  if (!CopyBytes(state.trampoline, trampoline.data(), trampoline.size()) ||
      !state.protect(state.memory_context, state.trampoline, trampoline.size(), PAGE_EXECUTE_READ, old_trampoline) ||
      !state.flush(state.memory_context, state.trampoline, trampoline.size())) {
    state.failure_flags.fetch_or(kProtectionFailure); discard(); return false;
  }
  try { g_bindings = environment.bindings; }
  catch (...) { state.failure_flags.fetch_or(kBindingFailure); discard(); return false; }
  ClearArmyRegularCoreJournal12004();
  g_original.store(reinterpret_cast<ArmyRegularCoreOriginal12004>(state.trampoline), std::memory_order_release);
  g_state.store(&state, std::memory_order_release); g_initialized.store(true, std::memory_order_release);
  DWORD old_target = 0;
  if (!state.protect(state.memory_context, reinterpret_cast<void *>(target), anchor.size(), PAGE_EXECUTE_READWRITE, old_target)) {
    g_initialized.store(false); g_state.store(nullptr); g_original.store(nullptr);
    state.failure_flags.fetch_or(kProtectionFailure); discard(); return false;
  }
  const auto patch = HookPatch();
  DWORD ignored = 0;
  const bool published = CopyBytes(reinterpret_cast<void *>(target), patch.data(), patch.size()) &&
      state.flush(state.memory_context, reinterpret_cast<const void *>(target), patch.size()) &&
      state.protect(state.memory_context, reinterpret_cast<void *>(target), patch.size(), old_target, ignored);
  if (!published) {
    state.failure_flags.fetch_or(kPublicationFailure);
    DWORD rollback_old = 0, rollback_ignored = 0;
    const bool writable = state.protect(state.memory_context, reinterpret_cast<void *>(target), anchor.size(),
        PAGE_EXECUTE_READWRITE, rollback_old);
    const bool restored = writable && CopyBytes(reinterpret_cast<void *>(target), anchor.data(), anchor.size()) &&
        state.flush(state.memory_context, reinterpret_cast<const void *>(target), anchor.size()) &&
        state.protect(state.memory_context, reinterpret_cast<void *>(target), anchor.size(), old_target, rollback_ignored);
    if (!restored) {
      // A target may still reference the thunk. Retain state/trampoline/original.
      state.failure_flags.fetch_or(kRollbackFailure); state.installed.store(true, std::memory_order_release); return false;
    }
    g_initialized.store(false); g_state.store(nullptr); g_original.store(nullptr); discard(); return false;
  }
  state.installed.store(true, std::memory_order_release); return true;
}

bool UninstallArmyRegularCorePassive12004(ArmyRegularCoreDetourState12004 &state,
    bool primary_thread_suspended_proven) noexcept {
  if (!primary_thread_suspended_proven || !state.installed.load(std::memory_order_acquire) ||
      g_state.load(std::memory_order_acquire) != &state || !state.target || !state.trampoline ||
      !state.protect || !state.flush || !state.free) return false;
  std::array<std::uint8_t, kArmyRegularCorePatchBytes12004> current{};
  if (!CopyBytes(current.data(), reinterpret_cast<const void *>(state.target), current.size()) || current != HookPatch()) {
    state.failure_flags.fetch_or(kAnchorFailure); return false;
  }
  DWORD old = 0, ignored = 0;
  if (!state.protect(state.memory_context, reinterpret_cast<void *>(state.target), current.size(), PAGE_EXECUTE_READWRITE, old)) {
    state.failure_flags.fetch_or(kProtectionFailure); return false;
  }
  if (!CopyBytes(reinterpret_cast<void *>(state.target), state.original_bytes.data(), current.size()) ||
      !state.flush(state.memory_context, reinterpret_cast<const void *>(state.target), current.size()) ||
      !state.protect(state.memory_context, reinterpret_cast<void *>(state.target), current.size(), old, ignored)) {
    state.failure_flags.fetch_or(kRollbackFailure); return false;
  }
  state.installed.store(false, std::memory_order_release);
  g_initialized.store(false); g_state.store(nullptr); g_original.store(nullptr);
  if (!state.free(state.memory_context, state.trampoline, 0, MEM_RELEASE)) {
    state.failure_flags.fetch_or(kFreeFailure); return false;
  }
  state.trampoline = nullptr; return true;
}
} // namespace xar::ck3_12004
