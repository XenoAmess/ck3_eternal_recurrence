#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <initializer_list>
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
using namespace xar;

void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

// Fake memory only. Read logs cover demands made by the new readonly collector;
// legacy Strength's direct reads continue to use the same allocated objects.
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  struct Denied { std::uintptr_t begin; std::size_t size; std::size_t attempts = 0; };
  struct Event { const void *address; std::size_t size; bool success; };
  std::vector<Region> regions;
  std::vector<Denied> denied;
  std::vector<Event> events;
  void *Allocate(std::size_t size) {
    auto bytes = std::make_unique<std::byte[]>(size);
    void *address = bytes.get();
    regions.push_back({std::move(bytes), size});
    return address;
  }
  template <typename T> void Put(void *address, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(address) + offset, &value, sizeof(value));
  }
  void Deny(const void *address, std::size_t offset, std::size_t size) {
    denied.push_back({reinterpret_cast<std::uintptr_t>(address) + offset, size});
  }
  std::size_t Attempts() const {
    std::size_t count = 0;
    for (const auto &range : denied) count += range.attempts;
    return count;
  }
  std::size_t Reads(const void *object, std::size_t offset, std::size_t size) const {
    const auto *address = static_cast<const std::byte *>(object) + offset;
    std::size_t count = 0;
    for (const auto &event : events)
      if (event.address == address && event.size == size) ++count;
    return count;
  }
  std::size_t First(const void *object, std::size_t offset, std::size_t size) const {
    const auto *address = static_cast<const std::byte *>(object) + offset;
    for (std::size_t i = 0; i < events.size(); ++i)
      if (events[i].address == address && events[i].size == size) return i;
    return std::numeric_limits<std::size_t>::max();
  }
  static bool Read(void *context, const void *address, void *output, std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    for (auto &range : memory.denied) {
      if (begin < range.begin + range.size && range.begin < begin + size) {
        ++range.attempts;
        memory.events.push_back({address, size, false});
        return false;
      }
    }
    for (const auto &region : memory.regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(region.bytes.get());
      if (begin >= base && begin - base <= region.size && size <= region.size - (begin - base)) {
        std::memcpy(output, address, size);
        memory.events.push_back({address, size, true});
        return true;
      }
    }
    memory.events.push_back({address, size, false});
    return false;
  }
};

struct Registry {
  Memory &memory;
  void *slot, *fallback_slot, *store, *table;
  Registry(Memory &m, std::uint32_t capacity)
      : memory(m), slot(m.Allocate(8)), fallback_slot(m.Allocate(8)),
        store(m.Allocate(0x30)), table(m.Allocate(capacity * 16)) {
    m.Put(slot, 0, store);
    m.Put(store, 0x20, table);
    m.Put(store, 0x2C, capacity);
  }
  void Add(std::uint32_t full, void *object, std::size_t full_offset) {
    memory.Put(table, (full & 0xFFFFFFU) * 16 + 8, object);
    memory.Put(object, full_offset, full);
  }
};

constexpr std::uint32_t kUnitA = 0x11000001U, kUnitB = 0x11000002U;
constexpr std::uint32_t kUnitAssociated = 0x11000003U, kUnitEarlyFalse = 0x11000004U;
constexpr std::uint32_t kScopeUnitA = 0x11000005U, kScopeUnitAssociated = 0x11000006U;
constexpr std::uint32_t kArmyA = 0x22000001U, kArmyB = 0x22000002U, kArmyAssociated = 0x22000003U;
constexpr std::uint32_t kCharacterAssociated = 0x10000001U, kCharacterProvince = 0xFE000002U;
constexpr std::uint32_t kSiege = 0xFE000002U, kWar = 0x55000001U;
constexpr std::uint32_t kRegA = 0x2B000001U, kRegB = 0x2B000002U, kRegC = 0x2B000003U;
constexpr std::uint32_t kInvalid = 0xFFFFFFFFU;

std::uint32_t Hash(std::uint32_t key) {
  std::uint32_t hash = 0x811C9DC5U;
  for (std::uint32_t shift = 0; shift != 32; shift += 8)
    hash = (hash ^ ((key >> shift) & 0xFFU)) * 0x1000193U;
  return hash;
}

void *expected_army_a = nullptr, *expected_army_associated = nullptr;
std::int32_t Current(void *receiver, std::uint8_t flags) {
  Check(flags == 0, "roster fixture must retain flags-zero whole-army current getter");
  if (receiver == static_cast<std::byte *>(expected_army_a) + 0x38) return 230;
  if (receiver == static_cast<std::byte *>(expected_army_associated) + 0x38) return 40;
  throw std::runtime_error("roster fixture unexpected current receiver");
}
std::int32_t Maximum(void *receiver) {
  if (receiver == expected_army_a) return 360;
  if (receiver == expected_army_associated) return 80;
  throw std::runtime_error("roster fixture unexpected maximum receiver");
}

struct Fixture {
  Memory memory;
  Registry units{memory, 7}, armies{memory, 4}, characters{memory, 3};
  Registry wars{memory, 2}, sieges{memory, 3}, arrgs{memory, 4};
  ck3_12002::ArmyBindings bindings{};
  void *state_slot = memory.Allocate(8), *state = memory.Allocate(0xA8);
  void *data = memory.Allocate(0x2A540 + 0x150);
  void *manager = static_cast<std::byte *>(data) + 0x2A540;
  void *pending = memory.Allocate(18 * 0x28);
  void *unit_a = memory.Allocate(0x180), *unit_b = memory.Allocate(0x180);
  void *unit_associated = memory.Allocate(0x180), *unit_early = memory.Allocate(0x180);
  void *unit_fallback = memory.Allocate(0x180);
  void *scope_a = memory.Allocate(0x180), *scope_associated = memory.Allocate(0x180);
  void *army_a = memory.Allocate(0x210), *army_b = memory.Allocate(0x210);
  void *army_associated = memory.Allocate(0x210), *army_fallback = memory.Allocate(0x210);
  void *province = memory.Allocate(0x858), *siege = memory.Allocate(0x450);
  void *character_associated = memory.Allocate(0x1B8), *character_province = memory.Allocate(0x1B8);
  void *component = memory.Allocate(0x30), *relation_table = memory.Allocate(5 * 16);
  void *relationship = memory.Allocate(0x28), *relationship_fallback_slot = memory.Allocate(8);
  void *province_fallback_slot = memory.Allocate(8);
  void *war = memory.Allocate(0x360), *war_fallback = memory.Allocate(0x360);
  void *reg_a = memory.Allocate(0x48), *reg_b = memory.Allocate(0x48), *reg_c = memory.Allocate(0x48);

  explicit Fixture(bool deny_empty_removal_data = true) {
    bindings.enabled = true;
    bindings.game_state_slot = static_cast<void **>(state_slot);
    bindings.unit_storage_slot = static_cast<void **>(units.slot);
    bindings.internal_army_storage_slot = static_cast<void **>(armies.slot);
    bindings.regiment_storage_slot = static_cast<void **>(arrgs.slot);
    bindings.get_army_current_soldiers = Current;
    bindings.get_army_maximum_soldiers = Maximum;
    auto &b = bindings.current_daily_assault_roster_admission_bindings;
    b.enabled = true;
    b.game_state_slot = state_slot;
    b.army_registry_slot = armies.slot; b.army_fallback_slot = armies.fallback_slot;
    b.unit_registry_slot = units.slot; b.unit_fallback_slot = units.fallback_slot;
    b.character_registry_slot = characters.slot; b.character_fallback_slot = characters.fallback_slot;
    b.war_registry_slot = wars.slot; b.war_fallback_slot = wars.fallback_slot;
    b.siege_registry_slot = sieges.slot; b.siege_fallback_slot = sieges.fallback_slot;
    b.province_fallback_slot = province_fallback_slot;
    b.relationship_fallback_slot = relationship_fallback_slot;
    b.read_memory = Memory::Read; b.read_context = &memory;
    memory.Put(state_slot, 0, state); memory.Put(state, 0xA0, data);
    memory.Deny(manager, 0, 8); // The manager is inline, never a pointer at its prefix.
    Ids(static_cast<std::byte *>(manager) + 0x50, {kArmyA, kArmyA, kArmyB, kInvalid});
    Ids(static_cast<std::byte *>(manager) + 0x68, {});
    if (deny_empty_removal_data) memory.Deny(manager, 0x68, 8); // Zero count does not demand data.
    memory.Put(manager, 0x138, pending);
    memory.Put(manager, 0x144, std::int32_t{15});
    memory.Put(manager, 0x148, std::uint8_t{1});
    memory.Deny(manager, 0x148, 1); // Exact key hits do not demand a miss's end/tail.

    units.Add(kUnitA, unit_a, 0x10); units.Add(kUnitB, unit_b, 0x10);
    units.Add(kUnitAssociated, unit_associated, 0x10); units.Add(kUnitEarlyFalse, unit_early, 0x10);
    units.Add(kScopeUnitA, scope_a, 0x10); units.Add(kScopeUnitAssociated, scope_associated, 0x10);
    memory.Put(unit_fallback, 0x10, kInvalid); memory.Put(units.fallback_slot, 0, unit_fallback);
    armies.Add(kArmyA, army_a, 0x10); armies.Add(kArmyB, army_b, 0x10);
    armies.Add(kArmyAssociated, army_associated, 0x10);
    memory.Put(army_fallback, 0x10, kInvalid); memory.Put(armies.fallback_slot, 0, army_fallback);
    memory.Put(army_a, 0x124, kUnitA); memory.Put(army_b, 0x124, kUnitB);
    memory.Put(army_associated, 0x124, kUnitAssociated); memory.Put(army_fallback, 0x124, kUnitEarlyFalse);
    for (void *unit : {unit_a, unit_b}) {
      memory.Put(unit, 0x18, std::uint32_t{0});
      memory.Put(unit, 0x20, province);
      memory.Put(unit, 0x170, std::int32_t{0});
      memory.Put(unit, 0x178, kArmyAssociated);
    }
    memory.Put(unit_associated, 0x178, kArmyAssociated);
    memory.Put(unit_associated, 0x174, kCharacterAssociated);
    memory.Put(unit_early, 0x18, std::uint32_t{1});
    memory.Put(unit_fallback, 0x18, std::uint32_t{1});
    memory.Put(unit_fallback, 0x174, kCharacterAssociated);
    memory.Put(scope_a, 0x178, kArmyA); memory.Put(scope_associated, 0x178, kArmyAssociated);
    memory.Put(province, 0x10, std::uint32_t{101});
    memory.Put(province, 0x788, kSiege); memory.Put(province, 0x850, std::int32_t{1});
    memory.Put(province, 0x73C, kCharacterProvince);
    memory.Put(province_fallback_slot, 0, province);
    memory.Deny(province_fallback_slot, 0, 8);
    sieges.Add(kSiege, siege, 8); memory.Put(siege, 0x44C, std::uint8_t{1});
    memory.Put(sieges.fallback_slot, 0, siege);
    characters.Add(kCharacterAssociated, character_associated, 0x18);
    characters.Add(kCharacterProvince, character_province, 0x18);
    memory.Put(characters.fallback_slot, 0, character_associated);
    memory.Put(character_associated, 0x1B0, component);
    memory.Put(component, 0x20, relation_table); memory.Put(component, 0x2C, std::int32_t{5});
    const std::array<std::uint32_t, 5> keys{{0x01000001U, 0x7FFFFFFFU, 0x80000000U,
                                          kCharacterProvince, 0xFF000003U}};
    for (std::size_t i = 0; i < keys.size(); ++i) {
      memory.Put(relation_table, i * 16, keys[i]);
      if (i != 3) memory.Deny(relation_table, i * 16 + 8, 8);
    }
    memory.Put(relation_table, 3 * 16 + 8, relationship);
    memory.Put(relationship, 0x20, kWar);
    memory.Put(relationship_fallback_slot, 0, relationship);
    memory.Deny(relationship_fallback_slot, 0, 8);
    wars.Add(kWar, war, 8); memory.Put(war, 0x358, std::uint8_t{0});
    memory.Put(war_fallback, 8, kInvalid); memory.Put(war_fallback, 0x358, std::uint8_t{0});
    memory.Put(wars.fallback_slot, 0, war_fallback);

    arrgs.Add(kRegA, reg_a, 0x10); arrgs.Add(kRegB, reg_b, 0x10); arrgs.Add(kRegC, reg_c, 0x10);
    Regiment(reg_a, 100, 150, 100000); Regiment(reg_b, 30, 60, 400000);
    Regiment(reg_c, 40, 80, 200000);
    Ids(static_cast<std::byte *>(army_a) + 0x38, {kRegA, kRegA, kRegB});
    Ids(static_cast<std::byte *>(army_b) + 0x38, {kRegC});
    Ids(static_cast<std::byte *>(army_associated) + 0x38, {kRegC});
    Pending(kArmyA, {kRegB}); Pending(kArmyB, {});
    expected_army_a = army_a; expected_army_associated = army_associated;
  }
  void *Ids(void *header, std::initializer_list<std::uint32_t> ids) {
    memory.Put(header, 8, static_cast<std::int32_t>(ids.size()));
    memory.Put(header, 0xC, static_cast<std::int32_t>(ids.size()));
    if (ids.size() == 0) return nullptr;
    void *values = memory.Allocate(ids.size() * 4);
    std::size_t i = 0;
    for (auto id : ids) memory.Put(values, i++ * 4, id);
    memory.Put(header, 0, values);
    return values;
  }
  void Regiment(void *regiment, std::int32_t current, std::int32_t maximum, std::int64_t power) {
    memory.Put(regiment, 0x14, std::uint32_t{0x41725267U});
    memory.Put(regiment, 0x38, current); memory.Put(regiment, 0x3C, maximum);
    memory.Put(regiment, 0x40, power);
  }
  void *PendingRecord(std::uint32_t army) {
    return static_cast<std::byte *>(pending) + (Hash(army) & 15U) * 0x28;
  }
  void Pending(std::uint32_t army, std::initializer_list<std::uint32_t> suppression) {
    void *record = PendingRecord(army);
    memory.Put(record, 0, Hash(army)); memory.Put(record, 4, std::uint8_t{1});
    memory.Put(record, 8, army); Ids(static_cast<std::byte *>(record) + 0x10, suppression);
  }
  std::vector<game::ArmyStrengthSnapshot> Observe() {
    const std::array<ck3_12002::ArmyStrengthScope, 2> scope{{
        {static_cast<std::int32_t>(kScopeUnitA), game::ArmyStrengthScopeRole::player, {}},
        {static_cast<std::int32_t>(kScopeUnitAssociated), game::ArmyStrengthScopeRole::active_war_ally, {7}}}};
    std::vector<game::ArmyStrengthSnapshot> rows;
    const auto result = ck3_12002::ReadArmyStrengthsForScope(bindings, scope, rows);
    Check(result == game::ReadArmyStrengthsResult::available && rows.size() == 2 &&
              rows[0].available && rows[1].available && rows[0].current_soldiers == 230 &&
              rows[0].maximum_soldiers == 360 && rows[0].ai_base_power_raw == 600000 &&
              rows[1].current_soldiers == 40 && rows[1].maximum_soldiers == 80 &&
              rows[1].ai_base_power_raw == 200000 && rows[0].native_carmy_id == static_cast<std::int32_t>(kArmyA) &&
              rows[1].native_carmy_id == static_cast<std::int32_t>(kArmyAssociated),
          "roster optional leaf must preserve complete legacy whole-strength results");
    Check(rows[0].current_daily_assault_roster_admission_v1 && rows[1].current_daily_assault_roster_admission_v1 &&
              rows[0].current_daily_assault_roster_admission_v1 == rows[1].current_daily_assault_roster_admission_v1 &&
              !rows[0].current_daily_assault_table_v1 && !rows[1].current_daily_assault_table_v1 &&
              memory.Reads(state_slot, 0, 8) == 1 && memory.Reads(state, 0xA0, 8) == 1 &&
              memory.Reads(manager, 0x5C, 4) == 1 && memory.Reads(manager, 0x74, 4) == 1,
          "roster must sample once across requested rows without enabling an older optional leaf");
    return rows;
  }
};

void Emit(const std::filesystem::path &directory, const char *name,
          const std::vector<game::ArmyStrengthSnapshot> &rows) {
  std::string wire;
  game::AppendArmyStrengthV1(wire, rows[0],
      [](auto value) { return std::to_string(value); },
      [](std::string &out, const std::vector<std::int32_t> &values) {
        out += '[';
        for (std::size_t i = 0; i < values.size(); ++i) {
          if (i) out += ',';
          out += std::to_string(values[i]);
        }
        out += ']';
      },
      [](std::string &out, std::string_view value) { out += '"'; out += value; out += '"'; });
  std::ofstream output(directory / (std::string("daily-assault-roster-") + name + ".json"), std::ios::binary);
  output << wire << '\n';
  Check(static_cast<bool>(output), "roster production whole-strength wire write failed");
}

void ExactBinding() {
  constexpr std::uintptr_t base = 0x140000000;
  const auto b = ck3_12003::BindCurrentDailyAssaultRosterAdmission12003(base, ck3_12003::kExecutableSha256);
  const auto at = [base](std::uintptr_t rva) { return reinterpret_cast<const void *>(base + rva); };
  Check(b.enabled && b.game_state_slot == at(0x5C68C50) &&
            b.army_registry_slot == at(0x5D1DE48) && b.army_fallback_slot == at(0x5D1DE50) &&
            b.unit_registry_slot == at(0x5D1E380) && b.unit_fallback_slot == at(0x5D1E378) &&
            b.character_registry_slot == at(0x5C67568) && b.character_fallback_slot == at(0x5C67570) &&
            b.war_registry_slot == at(0x5D1DE58) && b.war_fallback_slot == at(0x5D1DE40) &&
            b.siege_registry_slot == at(0x5D1EC88) && b.siege_fallback_slot == at(0x5D1EC60) &&
            b.province_fallback_slot == at(0x5D1E390) && b.relationship_fallback_slot == at(0x5D27B70),
        "roster exact frozen slots must match the source contract");
  Check(!ck3_12003::BindCurrentDailyAssaultRosterAdmission12003(base, "wrong-build").enabled &&
            !ck3_12002::BindArmyImage(base, ck3_12002::kExecutableSha256).current_daily_assault_roster_admission_bindings.enabled,
        "roster exact .3 capability must remain absent on wrong-build and .2 binders");
}

void CheckRosterOrder(const game::ArmyCurrentDailyAssaultRosterAdmissionV1 &roster) {
  Check(roster.raw_roster_references_ready && roster.original_roster.count_raw_i32 == 4 &&
            roster.original_roster.occurrences.size() == 4 && roster.occurrences.size() == 4 &&
            roster.occurrences[0].native_index == 0 && roster.occurrences[1].native_index == 1 &&
            roster.occurrences[2].native_index == 2 && roster.occurrences[3].native_index == 3 &&
            roster.occurrences[0].raw_full_id_u32 == kArmyA && roster.occurrences[1].raw_full_id_u32 == kArmyA &&
            roster.occurrences[2].raw_full_id_u32 == kArmyB && roster.occurrences[3].raw_full_id_u32 == kInvalid &&
            !roster.actual_next_callback_ready && !roster.actual_tomorrow_roster_ready &&
            !roster.full_future_table_placement_ready && !roster.full_daily_assault_ready,
        "roster must preserve all original duplicates/out-of-scope/invalid occurrences and honest stage boundaries");
}
void CheckTruePrefix(const game::ArmyCurrentDailyAssaultRosterAdmissionV1 &roster) {
  CheckRosterOrder(roster);
  for (std::size_t i = 0; i < 3; ++i) {
    const auto &occurrence = roster.occurrences[i];
    Check(occurrence.gate.ready && occurrence.gate.verdict == true && occurrence.gate.unavailable_reason.empty() &&
              occurrence.army_append_ready && occurrence.army_append == true &&
              occurrence.army_append_siege_full_id_u32 == kSiege &&
              occurrence.army_append_full_id_u32 == (i < 2 ? kArmyA : kArmyB),
          "roster nonempty true must derive actual gate and caller operands before pending selection");
  }
  const auto &invalid = roster.occurrences[3];
  Check(invalid.original_army_resolution.used_fallback == true &&
            invalid.original_army_resolution.selected_object_ready &&
            invalid.gate.original_unit_kind_raw_u32 == 1U && invalid.gate.ready && invalid.gate.verdict == false &&
            invalid.army_append_ready && invalid.army_append == false && invalid.arrg_append_ready &&
            invalid.arrg_append_full_ids_u32 && invalid.arrg_append_full_ids_u32->empty(),
        "invalid original raw Army must read the actual fallback gate and retain its decisive false result");
}

void RosterScenes(const std::filesystem::path &directory) {
  ExactBinding();
  {
    Fixture f;
    const auto rows = f.Observe();
    const auto &roster = *rows[0].current_daily_assault_roster_admission_v1;
    CheckTruePrefix(roster);
    Check(roster.ready && roster.conditional_admission_ready && roster.army_appends_ready &&
              roster.arrg_appends_ready && roster.original_army_selections_ready && roster.unavailable_reason.empty() &&
              roster.occurrences[0].arrg_append_full_ids_u32 == std::vector<std::uint32_t>{kRegA, kRegA} &&
              roster.occurrences[1].arrg_append_full_ids_u32 == std::vector<std::uint32_t>{kRegA, kRegA} &&
              roster.occurrences[2].arrg_append_full_ids_u32 == std::vector<std::uint32_t>{kRegC} &&
              f.memory.Attempts() == 0,
          "roster compound stream must preserve duplicate source armies and surviving duplicate ArRg requests");
    const auto &gate = roster.occurrences[0].gate;
    const auto &lookup = gate.relation_lookup;
    Check(gate.original_army_unit_id_raw_u32 == kUnitA && gate.associated_army_unit_id_raw_u32 == kUnitAssociated &&
              gate.associated_character_full_id_raw_u32 == kCharacterAssociated &&
              gate.province_character_full_id_raw_u32 == kCharacterProvince && lookup.ready &&
              lookup.selection == "pair_map" && lookup.table_count_raw_i32 == 5 && lookup.probes.size() == 4 &&
              lookup.probes[0].kind == "pivot" && lookup.probes[0].slot_index_i64 == 2 &&
              lookup.probes[0].key_character_id_raw_u32 == 0x80000000U &&
              lookup.probes[1].kind == "pivot" && lookup.probes[1].slot_index_i64 == 4 &&
              lookup.probes[2].kind == "pivot" && lookup.probes[2].slot_index_i64 == 3 &&
              lookup.probes[3].kind == "candidate" && lookup.probes[3].slot_index_i64 == 3 &&
              lookup.selected_relationship_war_id_raw_u32 == kWar && gate.selected_war_ended_358_raw_u8 == 0 &&
              !roster.occurrences[0].pending_selection.tail_distance_raw_u8 &&
              !roster.occurrences[0].pending_selection.end_slot_raw_i32,
          "roster must expose exact unsigned Character map probes and keep hit-only pending tail undemanded");
    Check(f.memory.First(f.unit_a, 0x18, 4) < f.memory.First(f.province, 0x850, 4) &&
              f.memory.First(f.unit_associated, 0x174, 4) < f.memory.First(f.character_associated, 0x1B0, 8) &&
              f.memory.First(f.relationship, 0x20, 4) < f.memory.First(f.war, 0x358, 1) &&
              f.memory.First(f.siege, 0x44C, 1) < f.memory.First(f.PendingRecord(kArmyA), 4, 1) &&
              f.memory.Reads(f.unit_early, 0x18, 4) != 0 && f.memory.Reads(f.manager, 0x74, 4) == 1,
          "roster source-order demand log must read genuine gate fields and sample removal once");
    Emit(directory, "compound-nonempty", rows);
  }
  {
    Fixture f;
    f.memory.Put(f.province, 0x73C, kCharacterAssociated);
    f.memory.Deny(f.character_associated, 0x1B0, 8);
    f.memory.Deny(f.wars.slot, 0, 8);
    f.memory.Put(f.manager, 0x74, std::int32_t{1}); // The always sampled but unused queue data remains denied.
    const auto rows = f.Observe();
    const auto &roster = *rows[0].current_daily_assault_roster_admission_v1;
    CheckRosterOrder(roster);
    Check(roster.ready && roster.army_appends_ready && roster.arrg_appends_ready &&
              roster.removal_queue.count_raw_i32 == 1 && !roster.removal_queue.references_ready &&
              !roster.removal_queue.ready && !roster.removal_queue.unavailable_reason.empty() &&
              f.memory.Reads(f.manager, 0x68, 8) == 1 && f.memory.Attempts() == 1,
          "same actual Character false must close admission despite independently observed partial removal queue");
    for (const auto &occurrence : roster.occurrences) {
      Check(occurrence.ready && occurrence.gate.ready && occurrence.gate.verdict == false &&
                occurrence.army_append == false && occurrence.arrg_append_full_ids_u32 &&
                occurrence.arrg_append_full_ids_u32->empty() && !occurrence.gate.relation_lookup.ready &&
                !occurrence.gate.relation_lookup.component_present &&
                occurrence.gate.relation_lookup.unavailable_reason == "not_demanded",
            "decisive false must retain undemanded relation fields and completed empty append results");
    }
    Emit(directory, "same-character-false", rows);
  }
  {
    Fixture f;
    for (auto army : {kArmyA, kArmyB}) f.memory.Put(f.PendingRecord(army), 4, std::uint8_t{0xFF});
    f.memory.Deny(f.army_a, 0x44, 4); f.memory.Deny(f.army_b, 0x44, 4);
    const auto rows = f.Observe();
    const auto &roster = *rows[0].current_daily_assault_roster_admission_v1;
    CheckTruePrefix(roster);
    Check(roster.ready && roster.arrg_appends_ready && f.memory.Attempts() == 0,
          "pending control FF must preserve Army append and skip original ArRg demands");
    for (std::size_t i = 0; i < 3; ++i)
      Check(roster.occurrences[i].pending_selection.selected_control_raw_u8 == 0xFF &&
                roster.occurrences[i].arrg_append_ready && roster.occurrences[i].arrg_append_full_ids_u32 &&
                roster.occurrences[i].arrg_append_full_ids_u32->empty() &&
                !roster.occurrences[i].original_arrg_references.count_raw_i32,
            "pending FF must publish known empty ArRg output without fabricating captured original references");
    Emit(directory, "pending-control-ff", rows);
  }
  {
    Fixture f;
    f.memory.Deny(f.PendingRecord(kArmyA), 4, 1);
    const auto rows = f.Observe();
    const auto &roster = *rows[0].current_daily_assault_roster_admission_v1;
    CheckTruePrefix(roster);
    Check(!roster.ready && !roster.conditional_admission_ready && roster.army_appends_ready &&
              !roster.arrg_appends_ready && !roster.unavailable_reason.empty() &&
              !roster.occurrences[0].arrg_append_ready && !roster.occurrences[0].arrg_append_full_ids_u32 &&
              !roster.occurrences[1].arrg_append_ready && !roster.occurrences[1].arrg_append_full_ids_u32 &&
              roster.occurrences[2].ready && roster.occurrences[2].arrg_append_full_ids_u32 ==
                  std::vector<std::uint32_t>{kRegC} && f.memory.Attempts() != 0,
          "missing pending control must retain independent Army-only knowledge, null ArRg list and complete later occurrence");
    Emit(directory, "partial-pending-control", rows);
  }
  {
    Fixture f;
    f.memory.Put(f.wars.table, 16 + 8, static_cast<void *>(nullptr));
    const auto rows = f.Observe();
    const auto &roster = *rows[0].current_daily_assault_roster_admission_v1;
    CheckTruePrefix(roster);
    const auto &resolution = roster.occurrences[0].gate.selected_war_resolution;
    Check(roster.ready && resolution.requested_full_id_u32 == kWar && resolution.used_fallback == true &&
              resolution.selected_object_ready && resolution.selected_full_id_u32 == kInvalid &&
              roster.occurrences[0].gate.selected_war_ended_358_raw_u8 == 0 && f.memory.Attempts() == 0,
          "nonsentinel requested War must admit actual fallback FFFFFFFF with byte358 zero");
    Emit(directory, "war-registry-miss-fallback-sentinel", rows);
  }
  {
    Fixture f;
    for (void *unit : {f.unit_a, f.unit_b}) f.memory.Put(unit, 0x178, std::uint32_t{0x99000003U});
    f.memory.Put(f.army_fallback, 0x124, std::uint32_t{0x99000007U});
    f.memory.Put(f.wars.table, 16 + 8, static_cast<void *>(nullptr));
    f.memory.Deny(f.unit_fallback, 0x10, 4);
    f.memory.Deny(f.army_fallback, 0x10, 4);
    f.memory.Deny(f.war_fallback, 8, 4);
    const auto rows = f.Observe();
    const auto &roster = *rows[0].current_daily_assault_roster_admission_v1;
    CheckTruePrefix(roster);
    const auto &gate = roster.occurrences[0].gate;
    Check(roster.ready && roster.original_army_selections_ready &&
              !gate.associated_army_resolution.ready && gate.associated_army_resolution.selected_object_ready &&
              gate.associated_army_resolution.selected_full_id_read_ready == false &&
              !gate.associated_unit_resolution.ready && gate.associated_unit_resolution.selected_object_ready &&
              gate.associated_unit_resolution.selected_full_id_read_ready == false &&
              !gate.selected_war_resolution.ready && gate.selected_war_resolution.selected_object_ready &&
              gate.selected_war_resolution.selected_full_id_read_ready == false &&
              roster.occurrences[3].gate.original_unit_resolution.selected_object_ready &&
              roster.occurrences[3].gate.original_unit_resolution.selected_full_id_read_ready == false &&
              !gate.associated_army_resolution.unavailable_reason.empty() &&
              f.memory.Reads(f.unit_fallback, 0x18, 4) != 0 &&
              f.memory.Reads(f.unit_fallback, 0x174, 4) != 0 && f.memory.Reads(f.war_fallback, 0x358, 1) != 0 &&
              f.memory.Attempts() != 0,
          "optional fallback Unit/associatedArmy/War ID metadata must not block demanded actual operands or decisive gates");
    Emit(directory, "optional-fallback-id-metadata-unreadable", rows);
  }
  {
    Fixture f;
    f.memory.Put(f.relationship, 0x20, kInvalid);
    f.memory.Deny(f.wars.slot, 0, 8); f.memory.Deny(f.wars.fallback_slot, 0, 8);
    const auto rows = f.Observe();
    const auto &roster = *rows[0].current_daily_assault_roster_admission_v1;
    CheckRosterOrder(roster);
    const auto &gate = roster.occurrences[0].gate;
    Check(!roster.ready && !roster.army_appends_ready && !roster.arrg_appends_ready &&
              !gate.ready && !gate.verdict && gate.relation_lookup.ready &&
              gate.relation_lookup.selected_relationship_war_id_raw_u32 == kInvalid &&
              gate.unavailable_reason == "2c09640_remaining_relation_predicates_unclosed" &&
              !gate.selected_war_resolution.selected_object_ready &&
              !gate.selected_war_ended_358_raw_u8 && !roster.occurrences[0].army_append &&
              !roster.occurrences[0].arrg_append_full_ids_u32 && roster.occurrences[3].ready &&
              f.memory.Attempts() == 0,
          "requested War sentinel must preserve unsupported branch rather than reuse fallback true or invent false");
    Emit(directory, "requested-war-sentinel-unclosed", rows);
  }
  {
    Fixture f;
    f.memory.Put(f.manager, 0x5C, std::int32_t{0});
    f.memory.Deny(f.manager, 0x50, 8);
    f.memory.Deny(f.armies.slot, 0, 8); f.memory.Deny(f.units.slot, 0, 8);
    const auto rows = f.Observe();
    const auto &roster = *rows[0].current_daily_assault_roster_admission_v1;
    Check(roster.ready && roster.raw_roster_references_ready && roster.original_army_selections_ready &&
              roster.army_appends_ready && roster.arrg_appends_ready && roster.conditional_admission_ready &&
              roster.original_roster.count_raw_i32 == 0 && roster.original_roster.occurrences.empty() &&
              roster.occurrences.empty() && !roster.original_roster.data_present &&
              roster.removal_queue.count_raw_i32 == 0 && roster.removal_queue.references_ready &&
              !roster.removal_queue.data_present && roster.unavailable_reason.empty() && f.memory.Attempts() == 0 &&
              !roster.actual_next_callback_ready && !roster.actual_tomorrow_roster_ready &&
              !roster.full_future_table_placement_ready && !roster.full_daily_assault_ready,
          "known empty roster must retain independently sampled zero removal count without unused data pointers or registries");
    Emit(directory, "current-empty", rows);
  }
  {
    Fixture f{false};
    // The first real Strength row must satisfy its existing Army+124 guard to
    // publish monthly_daily_queue_inputs_v1. Only this reuse scene changes it.
    f.memory.Put(f.army_a, 0x124, kScopeUnitA);
    f.memory.Put(f.scope_a, 0x20, f.province);
    f.memory.Put(f.scope_a, 0x174, kCharacterAssociated);
    f.bindings.monthly_daily_queue_bindings.enabled = true;
    f.bindings.monthly_daily_queue_bindings.army_fallback_slot = static_cast<void **>(f.armies.fallback_slot);
    void *queue_values = f.Ids(static_cast<std::byte *>(f.manager) + 0x68, {kArmyAssociated, kInvalid});
    f.memory.Deny(queue_values, 0, 8);
    const auto rows = f.Observe();
    const auto &roster = *rows[0].current_daily_assault_roster_admission_v1;
    CheckTruePrefix(roster);
    Check(rows[0].monthly_daily_queue_inputs_v1 &&
              rows[0].monthly_daily_queue_inputs_v1->manager_army_id_list_2a5a8 ==
                  std::vector<std::int32_t>{static_cast<std::int32_t>(kArmyAssociated), -1} &&
              roster.ready && roster.removal_queue.ready && roster.removal_queue.references_ready &&
              roster.removal_queue.count_raw_i32 == 2 && roster.removal_queue.data_present == true &&
              roster.removal_queue.data_identity && roster.removal_queue.occurrences.size() == 2 &&
              roster.removal_queue.occurrences[0].native_index == 0 &&
              roster.removal_queue.occurrences[0].raw_full_id_u32 == kArmyAssociated &&
              roster.removal_queue.occurrences[1].native_index == 1 &&
              roster.removal_queue.occurrences[1].raw_full_id_u32 == kInvalid &&
              roster.occurrences[0].removal_contains_selected_army == false &&
              roster.occurrences[2].removal_contains_selected_army == false &&
              f.memory.Reads(f.manager, 0x68, 8) == 1 &&
              f.memory.Reads(queue_values, 0, 4) == 0 && f.memory.Reads(queue_values, 4, 4) == 0 &&
              f.memory.Attempts() == 0,
          "actual whole-query shared queue must retain unsigned source order and data provenance without new raw element reads");
    Emit(directory, "shared-queue-reuse", rows);
  }
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path directory(argv[1]);
  std::filesystem::create_directories(directory);
  RosterScenes(directory);
  std::cout << "current daily assault roster admission fixture GREEN\n";
  return 0;
}
