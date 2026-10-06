#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12003_pre_date_character_prefix.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <algorithm>
#include <array>
#include <bit>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <vector>

namespace {
using namespace xar;
void Check(bool value, const char *reason) { if (!value) throw std::runtime_error(reason); }
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  struct Event { const void *address; std::size_t size; };
  std::vector<Region> regions;
  std::vector<Event> events, denied;
  void *Allocate(std::size_t size) {
    auto bytes = std::make_unique<std::byte[]>(size);
    auto *address = bytes.get(); regions.push_back({std::move(bytes), size}); return address;
  }
  template <class T> void Put(void *object, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
  }
  void Deny(const void *object, std::size_t offset, std::size_t size) {
    denied.push_back({static_cast<const std::byte *>(object) + offset, size});
  }
  void Allow(const void *object, std::size_t offset) {
    const auto *address = static_cast<const std::byte *>(object) + offset;
    std::erase_if(denied, [address](const auto &event) { return event.address == address; });
  }
  std::size_t Reads(const void *object, std::size_t offset, std::size_t size) const {
    const auto *address = static_cast<const std::byte *>(object) + offset;
    return static_cast<std::size_t>(std::count_if(events.begin(), events.end(),
        [address, size](const auto &event) { return event.address == address && event.size == size; }));
  }
  std::size_t First(const void *object, std::size_t offset) const {
    const auto *address = static_cast<const std::byte *>(object) + offset;
    for (std::size_t i = 0; i < events.size(); ++i) if (events[i].address == address) return i;
    return events.size();
  }
  std::vector<std::vector<std::byte>> Snapshot() const {
    std::vector<std::vector<std::byte>> result;
    for (const auto &region : regions) result.emplace_back(region.bytes.get(), region.bytes.get() + region.size);
    return result;
  }
  static bool Read(void *context, const void *address, void *out, std::size_t size) noexcept {
    auto &m = *static_cast<Memory *>(context); m.events.push_back({address, size});
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    for (const auto &denied : m.denied) {
      const auto blocked = reinterpret_cast<std::uintptr_t>(denied.address);
      if (begin < blocked + denied.size && blocked < begin + size) return false;
    }
    for (const auto &region : m.regions) {
      const auto start = reinterpret_cast<std::uintptr_t>(region.bytes.get());
      if (begin >= start && size <= region.size && begin - start <= region.size - size) {
        std::memcpy(out, address, size); return true;
      }
    }
    return false;
  }
};
struct Registry {
  Memory &m; void *slot, *fallback_slot, *store, *table;
  Registry(Memory &memory, std::uint32_t capacity) : m(memory), slot(m.Allocate(8)),
      fallback_slot(m.Allocate(8)), store(m.Allocate(0x30)), table(m.Allocate(capacity * 16U)) {
    m.Put(slot, 0, store); m.Put(store, 0x20, table); m.Put(store, 0x2C, capacity);
  }
  void Add(std::uint32_t id, void *object, std::size_t full_offset) {
    m.Put(table, (id & 0xFFFFFFU) * 16U + 8U, object); m.Put(object, full_offset, id);
  }
};
constexpr std::uint32_t kOwner = 0xFE000041U, kStaleArmy = 0xFD000003U;
std::array<std::size_t, 3> calls{};
std::vector<std::uint32_t> basic_candidates;
std::uint32_t Full(void *object) { std::uint32_t value{}; std::memcpy(&value, static_cast<std::byte *>(object) + 0x18, 4); return value; }
bool Membership(void *character, std::int32_t owner, bool allow_guests) {
  Check(!allow_guests && std::bit_cast<std::uint32_t>(owner) == kOwner, "membership false/raw owner bits");
  ++calls[0]; return Full(character) != 0xFE000005U;
}
bool Basic(bool basic, std::int32_t candidate, std::int32_t owner, void *reason) {
  Check(basic && reason == nullptr && std::bit_cast<std::uint32_t>(owner) == kOwner, "basic true/null/raw owner bits");
  ++calls[1]; basic_candidates.push_back(std::bit_cast<std::uint32_t>(candidate));
  return std::bit_cast<std::uint32_t>(candidate) != 0xFE000006U;
}
bool Availability(void *character, std::int32_t owner, bool assignment, void *reason) {
  Check(!assignment && reason == nullptr && std::bit_cast<std::uint32_t>(owner) == kOwner,
        "availability false/null/raw owner bits");
  ++calls[2]; return Full(character) != 0xFE000007U;
}
std::int32_t Current(void *, std::uint8_t flags) { Check(flags == 0, "whole strength flag zero"); return 0; }
std::int32_t Maximum(void *) { return 0; }
struct Fixture {
  Memory m;
  Registry units{m, 2}, armies{m, 12}, characters{m, 12}, combats{m, 2}, arrgs{m, 2};
  void *state_slot = m.Allocate(8), *state = m.Allocate(0xB0), *data = m.Allocate(0x2AA00);
  void *manager = static_cast<std::byte *>(data) + 0x2A540;
  void *unit = m.Allocate(0x180), *unit_fallback = m.Allocate(0x180);
  void *character_fallback = m.Allocate(0x1D8), *combat_fallback = m.Allocate(0x10);
  void *source_ids = m.Allocate(12 * 4), *initial_ids = m.Allocate(2 * 4);
  void *pending_entries = m.Allocate(9 * 0x28), *arrg_ids = m.Allocate(4), *arrg = m.Allocate(0x150);
  std::array<void *, 10> army{}, character{};
  ck3_12002::ArmyBindings bindings{};
  Fixture() {
    m.Put(state_slot, 0, state); m.Put(state, 0xA0, data);
    units.Add(0x01000001U, unit, 0x10); m.Put(unit, 0x178, 0x02000000U);
    m.Put(unit, 0x174, kOwner); m.Put(unit, 0x18, 1U);
    m.Put(unit_fallback, 0x10, 0x01000001U); m.Put(unit_fallback, 0x174, kOwner); m.Put(unit_fallback, 0x18, 1U);
    m.Put(units.fallback_slot, 0, unit_fallback);
    m.Put(character_fallback, 0x18, 0xFFFFFFFFU); m.Put(character_fallback, 0x1C, 0U);
    m.Put(characters.fallback_slot, 0, character_fallback);
    m.Put(combat_fallback, 8, 0xFFFFFFFFU); m.Put(combat_fallback, 0xC, 0x436F6D62U);
    m.Put(combats.fallback_slot, 0, combat_fallback);
    for (std::uint32_t i = 0; i < army.size(); ++i) {
      army[i] = m.Allocate(0x210); character[i] = m.Allocate(0x1D8);
      armies.Add(0x02000000U + i, army[i], 0x10);
      characters.Add(0xFE000000U + i, character[i], 0x18);
      m.Put(army[i], 0x14, 0x41726D79U); m.Put(army[i], 0x120, 0xFE000000U + i);
      m.Put(army[i], 0x124, 0x01000001U); m.Put(army[i], 0x128, 0xFFFFFFFFU);
      m.Put(army[i], 0x5C, i == 0 ? 0 : 1);
      m.Put(character[i], 0x1C, 0x43686172U); m.Put(character[i], 0x1C8, character[i]);
    }
    m.Put(armies.fallback_slot, 0, army[2]);
    m.Put(army[1], 0x120, 0xFFFFFFFFU);
    m.Put(army[2], 0x120, 0xFD000001U); m.Put(army[2], 0x124, 0xFD000001U);
    m.Put(character[3], 0x1D0, character[3]);
    m.Put(character[4], 0x1C8, static_cast<void *>(nullptr));
    m.Put(character[9], 0x1C8, static_cast<void *>(nullptr)); m.Put(character[9], 0x1C0, character[9]);
    const std::array<std::uint32_t, 11> ids{0x02000000U, 0x02000001U, kStaleArmy,
        0x02000003U, 0x02000004U, 0x02000005U, 0x02000006U, 0x02000007U, 0x02000008U, 0x02000009U, 0x02000007U};
    for (std::size_t i = 0; i < ids.size(); ++i) m.Put(source_ids, i * 4, ids[i]);
    m.Put(manager, 0x50, source_ids); m.Put(manager, 0x5C, 11);
    m.Put(initial_ids, 0, 7U); m.Put(initial_ids, 4, 7U);
    m.Put(manager, 0x80, initial_ids); m.Put(manager, 0x8C, 2);
    m.Put(manager, 0x138, pending_entries); m.Put(manager, 0x144, 7);
    const auto home = ck3_12003::daily_assault_roster_detail::Hash(0x02000000U) & 7U;
    m.Put(pending_entries, home * 0x28 + 4, static_cast<std::uint8_t>(1));
    m.Put(pending_entries, home * 0x28 + 8, 0x02000000U);
    arrgs.Add(0x07000001U, arrg, 0x10); m.Put(arrg, 0x14, 0x41725267U); m.Put(arrg_ids, 0, 0x07000001U);
    m.Deny(army[0], 0x120, 4); m.Deny(army[1], 0x124, 4);
    m.Deny(character_fallback, 0x1D0, 8); m.Deny(character[8], 0x1C0, 8); m.Deny(character[8], 0x1B8, 8);
    bindings.enabled = true; bindings.game_state_slot = static_cast<void **>(state_slot);
    bindings.unit_storage_slot = static_cast<void **>(units.slot);
    bindings.internal_army_storage_slot = static_cast<void **>(armies.slot);
    bindings.regiment_storage_slot = static_cast<void **>(arrgs.slot);
    bindings.get_army_current_soldiers = Current; bindings.get_army_maximum_soldiers = Maximum;
    bindings.monthly_first_removal_cleanup_inputs_enabled = true;
    auto &common = bindings.current_daily_assault_roster_admission_bindings;
    common.enabled = true; common.game_state_slot = state_slot; common.read_memory = Memory::Read; common.read_context = &m;
    common.army_registry_slot = armies.slot; common.army_fallback_slot = armies.fallback_slot;
    common.unit_registry_slot = units.slot; common.unit_fallback_slot = units.fallback_slot;
    common.character_registry_slot = characters.slot; common.character_fallback_slot = characters.fallback_slot;
    auto &pending = bindings.current_pre_date_pending_update_bindings;
    pending.common = common; pending.combat_registry_slot = combats.slot; pending.combat_fallback_slot = combats.fallback_slot;
    pending.arrg_registry_slot = arrgs.slot; pending.arrg_fallback_slot = arrgs.fallback_slot;
    auto &prefix = bindings.current_pre_date_character_prefix_bindings;
    prefix.common = common; prefix.membership = Membership; prefix.basic_rule = Basic; prefix.availability = Availability;
  }
  game::ArmyStrengthSnapshot Read() {
    m.events.clear(); calls.fill(0); basic_candidates.clear(); const auto before = m.Snapshot();
    const std::array<ck3_12002::ArmyStrengthScope, 2> scope{{
        {0x01000001, game::ArmyStrengthScopeRole::player, {}}, {0x01000001, game::ArmyStrengthScopeRole::player, {}}}};
    std::vector<game::ArmyStrengthSnapshot> rows;
    Check(ck3_12002::ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available,
          "prefix partial keeps available parent strength");
    Check(m.Snapshot() == before, "readonly prefix observer wrote source memory");
    Check(rows.size() == 2 && rows[0].current_pre_date_character_prefix_inputs_v1 == rows[1].current_pre_date_character_prefix_inputs_v1,
          "same query prefix value reused across scope rows");
    return rows[0];
  }
};
void Emit(const std::filesystem::path &directory, const char *label, const game::ArmyStrengthSnapshot &row) {
  std::string wire;
  game::AppendArmyStrengthV1(wire, row, [](auto value) { return std::to_string(value); },
      [](std::string &out, const std::vector<std::int32_t> &values) {
        out += '['; for (std::size_t i = 0; i < values.size(); ++i) { if (i) out += ','; out += std::to_string(values[i]); } out += ']';
      }, [](std::string &out, std::string_view value) { out += '"'; out += value; out += '"'; });
  std::filesystem::create_directories(directory);
  std::ofstream file(directory / (std::string(label) + ".json"), std::ios::binary);
  Check(static_cast<bool>(file), "fixture wire output"); file << wire << '\n';
}
void Cases(const std::filesystem::path &directory) {
  Fixture f; auto row = f.Read(); const auto &p = *row.current_pre_date_character_prefix_inputs_v1;
  Check(p.ready && p.occurrences.size() == 11 && p.initial_80.ready &&
        p.initial_80.source == "same_query_first_removal_id_list", "nonempty complete prefix/initial80 reuse");
  Check(p.occurrences[0].earlier_skip == true && !p.occurrences[0].army_character_120_raw_u32 &&
        !p.occurrences[0].membership.demanded && f.m.Reads(f.army[0], 0x120, 4) == 0,
        "existing-key known skip makes zero prefix reads/predicate calls");
  Check(p.occurrences[1].army_character_120_raw_u32 == 0xFFFFFFFFU &&
        !p.occurrences[1].army_unit_124_raw_u32 && !p.occurrences[1].membership.demanded,
        "sentinel does not demand Unit/Character/predicates");
  Check(p.occurrences[2].army_resolution.used_fallback == true &&
        p.occurrences[2].failure_append_army_10_raw_u32 == 0x02000002U &&
        p.occurrences[2].unit_resolution.used_fallback == true &&
        f.m.First(f.unit_fallback, 0x174) < f.m.First(f.character_fallback, 0x1C),
        "native fallback and actual Army10; owner load before Character tag");
  Check(p.occurrences[3].character_death_1d0_present == true && !p.occurrences[3].character_state_1c8_present &&
        p.occurrences[4].character_state_1b8_present == false && !p.occurrences[4].membership.demanded,
        "death/state failures short circuit real callbacks");
  Check(p.occurrences[5].membership.verdict == false && !p.occurrences[5].basic_rule.demanded &&
        p.occurrences[6].basic_rule.verdict == false && !p.occurrences[6].availability.demanded &&
        p.occurrences[7].availability.verdict == false && p.occurrences[8].availability.verdict == true &&
        p.occurrences[9].character_state_1c0_present == true && !p.occurrences[9].character_state_1b8_present,
        "independent native verdicts and ordered state stop");
  Check(calls == std::array<std::size_t, 3>{6, 5, 4} && f.m.Reads(f.character[8], 0x1C0, 8) == 0 &&
        f.m.Reads(f.initial_ids, 0, 4) == 0 && f.m.Reads(f.source_ids, 0, 4) == 1,
        "F/T/F callback demand counts and no second original/initial vector scans");
  Emit(directory, "nonempty-all-source-branches", row);
  f.m.Put(f.manager, 0x80, static_cast<void *>(nullptr)); row = f.Read();
  Check(row.current_pre_date_character_prefix_inputs_v1->ready && !row.current_pre_date_character_prefix_inputs_v1->initial_80.ready,
        "append requests independent of unavailable initial80");
  Emit(directory, "initial80-unavailable", row); f.m.Put(f.manager, 0x80, f.initial_ids);
  f.bindings.current_pre_date_character_prefix_bindings.availability = nullptr; row = f.Read();
  Check(!row.current_pre_date_character_prefix_inputs_v1->ready &&
        row.current_pre_date_character_prefix_inputs_v1->occurrences[5].ready &&
        row.current_pre_date_character_prefix_inputs_v1->occurrences[7].availability.demanded &&
        !row.current_pre_date_character_prefix_inputs_v1->occurrences[7].availability.observable && calls[2] == 0,
        "unresolved demanded native callback stays precise partial; early verdicts independent");
  Emit(directory, "availability-callback-unavailable", row);
  f.bindings.current_pre_date_character_prefix_bindings.availability = Availability;
  f.m.Deny(f.unit_fallback, 0x174, 4); row = f.Read();
  Check(!row.current_pre_date_character_prefix_inputs_v1->occurrences[2].ready &&
        !row.current_pre_date_character_prefix_inputs_v1->occurrences[2].character_magic_1c_raw_u32 &&
        f.m.Reads(f.character_fallback, 0x1C, 4) == 0, "owner load failure cannot be replaced by later invalid Character tag");
  Emit(directory, "unit174-required-load-unavailable", row); f.m.Allow(f.unit_fallback, 0x174);
  f.m.Put(f.character_fallback, 0x1C, 0x43686172U); row = f.Read();
  Check(row.current_pre_date_character_prefix_inputs_v1->occurrences[2].character_full_id_18_raw_u32 == 0xFFFFFFFFU &&
        row.current_pre_date_character_prefix_inputs_v1->occurrences[2].failure_append_army_10_raw_u32 == 0x02000002U,
        "Character fallback selected sentinel ownID is a true failure");
  Emit(directory, "fallback-character-fullid-failure", row);
  f.m.Allow(f.character_fallback, 0x1D0); f.m.Put(f.character_fallback, 0x18, 0xFE00000AU);
  f.m.Put(f.character_fallback, 0x1C8, f.character_fallback); row = f.Read();
  Check(row.current_pre_date_character_prefix_inputs_v1->occurrences[2].character_resolution.used_fallback == true &&
        row.current_pre_date_character_prefix_inputs_v1->occurrences[2].character_full_id_18_raw_u32 == 0xFE00000AU &&
        row.current_pre_date_character_prefix_inputs_v1->occurrences[2].availability.verdict == true &&
        std::find(basic_candidates.begin(), basic_candidates.end(), 0xFE00000AU) != basic_candidates.end() &&
        std::find(basic_candidates.begin(), basic_candidates.end(), 0xFD000001U) == basic_candidates.end(),
        "basic native argument uses valid fallback Character18 instead of Army120 request; fullDWORD preserved");
  Emit(directory, "valid-fallback-character-selected-basic-argument", row);
  f.m.Put(f.character_fallback, 0x1C, 0U); f.m.Put(f.character_fallback, 0x18, 0xFFFFFFFFU);
  f.m.Put(f.character_fallback, 0x1C8, static_cast<void *>(nullptr)); f.m.Deny(f.character_fallback, 0x1D0, 8);
  f.m.Allow(f.army[0], 0x120); f.m.Put(f.army[0], 0x120, 0xFFFFFFFFU);
  f.m.Put(f.manager, 0x138, static_cast<void *>(nullptr)); row = f.Read();
  Check(row.current_pre_date_character_prefix_inputs_v1->ready &&
        !row.current_pre_date_character_prefix_inputs_v1->occurrences[0].earlier_skip &&
        row.current_pre_date_character_prefix_inputs_v1->occurrences[0].army_character_120_raw_u32 == 0xFFFFFFFFU,
        "unknown pending setup keeps independent explicit current sentinel entrance");
  Emit(directory, "earlier-setup-unknown-independent-prefix", row);
  f.m.Put(f.manager, 0x138, f.pending_entries); f.m.Put(f.army[0], 0x38, f.arrg_ids);
  f.m.Put(f.army[0], 0x40, 1); f.m.Put(f.army[0], 0x44, 1);
  f.m.Put(f.source_ids, 11 * 4, 0x02000000U); f.m.Put(f.manager, 0x5C, 12); row = f.Read();
  const auto &repeated = *row.current_pre_date_character_prefix_inputs_v1;
  Check(repeated.ready && repeated.occurrences[0].earlier_skip == true && repeated.occurrences[11].earlier_skip == false &&
        repeated.occurrences[11].army_character_120_raw_u32 == 0xFFFFFFFFU && f.m.Reads(f.army[0], 0x120, 4) == 1,
        "actual repeated Army existing-key count carried; second occurrence enters prefix");
  Emit(directory, "repeated-existing-key-count-changes-skip", row);
  Check(ck3_12003::BindCurrentPreDateCharacterPrefix12003(0x140000000ULL, ck3_12003::kExecutableSha256).common.enabled &&
        !ck3_12003::BindCurrentPreDateCharacterPrefix12003(0x140000000ULL, ck3_12002::kExecutableSha256).common.enabled,
        "exact .3 only binder");
}
} // namespace
int main(int argc, char **argv) {
  try {
    const auto directory = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::current_path() / "pre-date-character-prefix-new-cases";
    Cases(directory); std::cout << "pre-date character prefix new fixture GREEN\n"; return 0;
  } catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 1; }
}
