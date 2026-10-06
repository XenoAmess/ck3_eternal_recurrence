#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>

namespace {
using namespace xar;
void Check(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  struct Request { const void *address; std::size_t size; };
  std::vector<Region> regions;
  std::vector<Request> requests;
  void *Allocate(std::size_t size) {
    auto data = std::make_unique<std::byte[]>(size); auto *pointer = data.get();
    regions.push_back({std::move(data), size}); return pointer;
  }
  template <class T> void Put(void *pointer, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(pointer) + offset, &value, sizeof(value));
  }
  static bool Read(void *context, const void *address, void *output, std::size_t size) noexcept {
    auto &m = *static_cast<Memory *>(context); m.requests.push_back({address, size});
    const auto requested = reinterpret_cast<std::uintptr_t>(address);
    for (const auto &region : m.regions) {
      const auto start = reinterpret_cast<std::uintptr_t>(region.bytes.get());
      if (requested >= start && requested - start <= region.size && size <= region.size - (requested - start)) {
        std::memcpy(output, address, size); return true;
      }
    }
    return false;
  }
};
struct Registry {
  Memory &m;
  void *slot, *fallback_slot, *store, *table;
  explicit Registry(Memory &memory) : m(memory), slot(m.Allocate(8)), fallback_slot(m.Allocate(8)),
      store(m.Allocate(0x30)), table(m.Allocate(32U * 16U)) {
    m.Put(slot, 0, store); m.Put(store, 0x20, table); m.Put(store, 0x2C, std::uint32_t{32});
  }
  void Add(std::uint32_t id, void *object, std::size_t id_offset = 0x10) {
    m.Put(table, static_cast<std::size_t>(id & 0xFFFFFFU) * 16U + 8U, object);
    m.Put(object, id_offset, id);
  }
};
constexpr std::uint32_t kUnit = 0x11000001U, kSubject = 0x22000001U, kCandidate = 0x22000002U;
constexpr std::uint32_t kLegacy = 0x2B000001U, kIncoming = 0x2B000002U;
constexpr std::uint32_t kCharacter = 0x1B000003U, kRegi = 0x4C000004U;
constexpr std::uint32_t kOwnerEqual = 0x4C000005U, kOwnerEarlier = 0x4C000006U;
constexpr std::uint32_t kInvalidRegi = 0xEF00001FU, kInvalidArmy = 0xEE00001EU;
constexpr std::int64_t kCurrentDate = 0x0000000200000064LL;
constexpr std::int64_t kLaterDate = 0x0000000900000080LL;
constexpr std::int64_t kEarlierDate = 0x0000000700000060LL;
void *expected_subject = nullptr, *expected_unit = nullptr, *expected_province = nullptr;
void *expected_capital = nullptr, *expected_earlier_origin = nullptr;
std::int32_t Current(void *receiver, std::uint8_t flags) {
  Check(receiver == static_cast<std::byte *>(expected_subject) + 0x38 && flags == 0,
        "new DATA fixture keeps production current helper receiver"); return 20;
}
std::int32_t Maximum(void *receiver) {
  Check(receiver == expected_subject, "new DATA fixture keeps production maximum helper receiver"); return 40;
}
const void *Capital(const void *) { return expected_capital; }
const void *Date(std::int64_t *output, const void *unit, const void *passed,
                 const void *origin, const std::int64_t *entry_date) {
  Check(unit == expected_unit && passed == expected_province && *entry_date == kCurrentDate,
        "computed DATA date uses actual Unit/ancestor Province and full existing current date");
  *output = origin == expected_earlier_origin ? kEarlierDate : kLaterDate;
  return output;
}

struct Fixture {
  Memory m;
  Registry units{m}, armies{m}, arrgs{m}, regis{m}, characters{m};
  ck3_12002::ArmyBindings bindings{};
  void *state_slot = m.Allocate(8), *state = m.Allocate(0xA8);
  void *data = m.Allocate(0x2A540U + 0x500U), *manager = static_cast<std::byte *>(data) + 0x2A540;
  void *unit = m.Allocate(0x180), *unit_fallback = m.Allocate(0x180);
  void *subject = m.Allocate(0x208), *candidate = m.Allocate(0x208), *army_fallback = m.Allocate(0x208);
  void *legacy = m.Allocate(0x150), *incoming = m.Allocate(0x150), *arrg_fallback = m.Allocate(0x150);
  void *regi = m.Allocate(0x150), *owner_equal = m.Allocate(0x150), *owner_earlier = m.Allocate(0x150);
  void *regi_fallback = m.Allocate(0x150), *character = m.Allocate(0x1D0), *character_fallback = m.Allocate(0x1D0);
  void *context = m.Allocate(0x340), *static_context = m.Allocate(0x20), *definition = m.Allocate(0x50);
  void *passed = m.Allocate(0x880), *origin = m.Allocate(0x880), *capital = m.Allocate(0x880), *earlier_origin = m.Allocate(0x880);
  void *province_slot = m.Allocate(8), *canonical_vtable = m.Allocate(8), *other_vtable = m.Allocate(8);
  Fixture() {
    bindings.enabled = true; bindings.game_state_slot = static_cast<void **>(state_slot);
    bindings.unit_storage_slot = static_cast<void **>(units.slot);
    bindings.internal_army_storage_slot = static_cast<void **>(armies.slot);
    bindings.regiment_storage_slot = static_cast<void **>(arrgs.slot);
    bindings.get_army_current_soldiers = Current; bindings.get_army_maximum_soldiers = Maximum;
    bindings.monthly_daily_queue_bindings.enabled = true;
    bindings.monthly_daily_queue_bindings.army_fallback_slot = static_cast<void **>(armies.fallback_slot);
    bindings.monthly_first_removal_cleanup_inputs_enabled = true;
    bindings.monthly_caller_effect_bindings.enabled = true;
    auto &lookup = bindings.current_assault_removal_reference_bindings.lookup;
    bindings.current_assault_removal_reference_bindings.enabled = true;
    lookup.enabled = true; lookup.game_state_slot = state_slot;
    lookup.army_registry_slot = armies.slot; lookup.army_fallback_slot = armies.fallback_slot;
    lookup.arrg_registry_slot = arrgs.slot; lookup.arrg_fallback_slot = arrgs.fallback_slot;
    lookup.read_memory = Memory::Read; lookup.read_context = &m;
    auto &mapper = bindings.current_candidate_detachment_mapper_bindings;
    mapper.enabled = true; mapper.lookup = lookup; mapper.regi_registry_slot = regis.slot;
    mapper.regi_fallback_slot = regis.fallback_slot;
    auto &leaf = bindings.current_detachment_data_bindings;
    leaf.common = lookup; leaf.regi_registry_slot = regis.slot; leaf.regi_fallback_slot = regis.fallback_slot;
    leaf.unit_registry_slot = units.slot; leaf.unit_fallback_slot = units.fallback_slot;
    leaf.character_registry_slot = characters.slot; leaf.character_fallback_slot = characters.fallback_slot;
    leaf.province_fallback_slot = province_slot; leaf.static_context = static_context;
    leaf.canonical_pending_vtable = canonical_vtable;
    leaf.ready_pending_callback = reinterpret_cast<const void *>(std::uintptr_t{0x1408863D0ULL});
    leaf.get_capital = Capital; leaf.compute_date = Date;
    m.Put(canonical_vtable, 0, leaf.ready_pending_callback);
    m.Put(other_vtable, 0, reinterpret_cast<const void *>(std::uintptr_t{0x1408863E8ULL}));
    m.Put(state_slot, 0, state); m.Put(state, 0xA0, data); m.Put(state, 8, kCurrentDate);
    units.Add(kUnit, unit); armies.Add(kSubject, subject); armies.Add(kCandidate, candidate);
    m.Put(subject, 0x14, std::uint32_t{0x41726D79}); m.Put(candidate, 0x14, std::uint32_t{0x41726D79});
    m.Put(armies.fallback_slot, 0, army_fallback); m.Put(army_fallback, 0x10, std::uint32_t{0xFFFFFFFFU});
    m.Put(army_fallback, 0x14, std::uint32_t{0x446C7464}); m.Put(army_fallback, 0x124, std::uint32_t{0xFFFFFFFFU});
    m.Put(units.fallback_slot, 0, unit_fallback); m.Put(unit_fallback, 0x10, std::uint32_t{0xFFFFFFFFU});
    m.Put(unit_fallback, 0x174, std::uint32_t{0xFFFFFFFFU}); m.Put(unit_fallback, 0x20, passed);
    m.Put(unit, 0x178, kSubject); m.Put(subject, 0x124, kUnit); m.Put(candidate, 0x124, kUnit);
    m.Put(unit, 0x174, kCharacter); m.Put(unit, 0x20, passed); m.Put(province_slot, 0, passed);
    arrgs.Add(kLegacy, legacy); m.Put(legacy, 0x14, std::uint32_t{0x41725267});
    m.Put(legacy, 0x38, std::int32_t{20}); m.Put(legacy, 0x3C, std::int32_t{40}); m.Put(legacy, 0x40, std::int64_t{100000});
    auto *subject_roster = m.Allocate(4); m.Put(subject_roster, 0, kLegacy);
    m.Put(subject, 0x38, subject_roster); m.Put(subject, 0x40, std::int32_t{1}); m.Put(subject, 0x44, std::int32_t{1});
    arrgs.Add(kIncoming, incoming); m.Put(incoming, 0x14, std::uint32_t{0x41725267});
    m.Put(incoming, 0x14C, std::int32_t{4}); m.Put(incoming, 0x140, kCandidate);
    m.Put(incoming, 0x148, std::uint32_t{0xFFFFFFFFU});
    m.Put(arrgs.fallback_slot, 0, arrg_fallback); m.Put(arrg_fallback, 0x10, std::uint32_t{0xFFFFFFFFU});
    m.Put(arrg_fallback, 0x14, std::uint32_t{0x446C7464}); m.Put(arrg_fallback, 0x140, std::uint32_t{0xFFFFFFFFU});
    regis.Add(kRegi, regi); regis.Add(kOwnerEqual, owner_equal); regis.Add(kOwnerEarlier, owner_earlier);
    for (auto *p : {regi, owner_equal, owner_earlier}) {
      m.Put(p, 0x14, std::uint32_t{0x52656769}); m.Put(p, 0x118, definition);
      m.Put(p, 0x138, std::int32_t{0});
    }
    m.Put(definition, 0x38, std::uint32_t{0x12345678});
    m.Put(regi, 0x120, origin); m.Put(owner_equal, 0x120, capital); m.Put(owner_earlier, 0x120, earlier_origin);
    m.Put(passed, 0x85C, std::uint32_t{0x50726F76}); m.Put(origin, 0x85C, std::uint32_t{0x50726F76});
    m.Put(earlier_origin, 0x85C, std::uint32_t{0x50726F76}); m.Put(capital, 0x85C, std::uint32_t{0});
    m.Put(regis.fallback_slot, 0, regi_fallback); m.Put(regi_fallback, 0x10, std::uint32_t{0xFFFFFFFFU});
    m.Put(regi_fallback, 0x14, std::uint32_t{0x446C7464}); m.Put(regi_fallback, 0x138, std::int32_t{4});
    characters.Add(kCharacter, character, 0x18); m.Put(character, 0x1C0, context);
    m.Put(context, 0x318 + 0xC, std::uint32_t{0xFFFFFFFEU});
    m.Put(characters.fallback_slot, 0, character_fallback); m.Put(character_fallback, 0x18, std::uint32_t{0xFFFFFFFFU});
    Chunk(0, 10, 20, kRegi, -5); Chunk(1, 40, 7, kOwnerEqual, 99); Chunk(2, -10, -7, kOwnerEarlier, -13);
    Queue({kInvalidArmy, kCandidate}); Roster({kIncoming, kIncoming});
    Records({{kRegi, 0}}); Pending(0, 8, false);
    expected_subject = subject; expected_unit = unit; expected_province = passed;
    expected_capital = capital; expected_earlier_origin = earlier_origin;
  }
  void Chunk(std::size_t index, std::int32_t maximum, std::int32_t current,
             std::uint32_t owner, std::int32_t raw_ordinal) {
    const auto offset = 0x18U + index * 0x24U;
    m.Put(regi, offset, maximum); m.Put(regi, offset + 4U, current);
    m.Put(regi, offset + 8U, owner); m.Put(regi, offset + 0xCU, raw_ordinal);
    m.Put(regi, offset + 0x10U, kIncoming); m.Put(regi, offset + 0x14U, std::uint8_t{1});
    m.Put(regi, offset + 0x1CU, std::int64_t{111});
  }
  void Queue(const std::vector<std::uint32_t> &ids) {
    auto *buffer = ids.empty() ? nullptr : m.Allocate(ids.size() * 4U);
    for (std::size_t i = 0; i < ids.size(); ++i) m.Put(buffer, i * 4U, ids[i]);
    m.Put(manager, 0x68, buffer); m.Put(manager, 0x74, static_cast<std::int32_t>(ids.size()));
  }
  void Roster(const std::vector<std::uint32_t> &ids) {
    auto *buffer = ids.empty() ? nullptr : m.Allocate(ids.size() * 4U);
    for (std::size_t i = 0; i < ids.size(); ++i) m.Put(buffer, i * 4U, ids[i]);
    m.Put(candidate, 0x38, buffer); m.Put(candidate, 0x44, static_cast<std::int32_t>(ids.size()));
  }
  void Records(const std::vector<std::pair<std::uint32_t, std::int32_t>> &rows) {
    auto *buffer = rows.empty() ? nullptr : m.Allocate(rows.size() * 16U);
    for (std::size_t i = 0; i < rows.size(); ++i) {
      m.Put(buffer, i * 16U + 8U, rows[i].first); m.Put(buffer, i * 16U + 0xCU, rows[i].second);
    }
    m.Put(incoming, 0x20, buffer); m.Put(incoming, 0x2C, static_cast<std::int32_t>(rows.size()));
  }
  void Pending(std::int32_t count, std::int32_t capacity, bool other_callback) {
    auto *buffer = m.Allocate(static_cast<std::size_t>(std::max(count, std::int32_t{0}) + 8) * 16U);
    for (std::int32_t i = 0; i < count; ++i) {
      const auto offset = static_cast<std::size_t>(i) * 16U;
      m.Put(buffer, offset, other_callback ? other_vtable : canonical_vtable);
      m.Put(buffer, offset + 8U, std::uint32_t{0xF1000007U}); m.Put(buffer, offset + 0xCU, std::int32_t{-91});
    }
    auto *header = static_cast<std::byte *>(manager) + 0x468;
    m.Put(header, 0, buffer); m.Put(header, 8, capacity); m.Put(header, 0xC, count);
    m.Put(header, 0x10, m.Allocate(8));
  }
  game::ArmyStrengthSnapshot Observe() {
    const std::array<ck3_12002::ArmyStrengthScope, 1> scope{{
        {static_cast<std::int32_t>(kUnit), game::ArmyStrengthScopeRole::player, {}}}};
    std::vector<game::ArmyStrengthSnapshot> rows;
    Check(ck3_12002::ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available &&
              rows.size() == 1U && rows[0].available && rows[0].current_soldiers == 20 && rows[0].maximum_soldiers == 40 &&
              rows[0].current_detachment_data_inputs_v1,
          "new whole DATA leaf must preserve actual complete ArmyStrength reader");
    return std::move(rows[0]);
  }
};
const game::ArmyCurrentDetachmentDataInputsV1 &Leaf(const game::ArmyStrengthSnapshot &row) {
  return *row.current_detachment_data_inputs_v1;
}
void Emit(const std::filesystem::path &directory, const char *name, const game::ArmyStrengthSnapshot &row) {
  std::string wire;
  game::AppendArmyStrengthV1(wire, row, [](auto value) { return std::to_string(value); },
      [](std::string &out, const std::vector<std::int32_t> &values) {
        out += '['; for (std::size_t i = 0; i < values.size(); ++i) { if (i) out += ','; out += std::to_string(values[i]); } out += ']';
      }, [](std::string &out, std::string_view value) { out += '"'; out += value; out += '"'; });
  std::ofstream file(directory / (std::string("detachment-data-") + name + ".json"), std::ios::binary);
  file << wire << '\n'; Check(static_cast<bool>(file), "new whole DATA wire emitted");
}
void Cases(const std::filesystem::path &directory) {
  {
    Fixture f; f.Records({{kInvalidRegi, 0}, {kRegi, 0}, {kRegi, 0}, {kRegi, 1}, {kRegi, 2}, {kInvalidRegi, 5}});
    const auto row = f.Observe(); const auto &p = Leaf(row);
    Check(p.candidate_occurrences.size() == 2U && p.incoming.size() == 1U &&
              p.candidate_occurrences[0].incoming_index == p.candidate_occurrences[1].incoming_index,
          "actual candidate duplicate occurrences share one independent incoming baseline");
    const auto &incoming_row = p.incoming[0];
    Check(incoming_row.data_ready && incoming_row.data_occurrences.size() == 6U && incoming_row.physical_chunks.size() == 3U,
          "new producer captures whole raw DATA including invalid records and repeated physical aliases");
    Check(incoming_row.data_occurrences[1].physical_chunk_index == incoming_row.data_occurrences[2].physical_chunk_index &&
              incoming_row.physical_chunks[0].ordinal_0c_raw_i32 == -5 &&
              incoming_row.data_occurrences[1].data_ordinal_raw_i32 == 0 &&
              p.current_date_storage_raw64 == kCurrentDate,
          "DATA ordinal, physical raw ordinal and existing fullQWORDdate remain distinct");
    Emit(directory, "whole-six-record-aliases", row);
  }
  {
    Fixture f; f.Pending(1, 1, false); const auto row = f.Observe(); const auto &p = Leaf(row);
    Check(p.incoming.size() == 1U && p.incoming[0].pending.count_0c_raw_i32 == 1 &&
              p.incoming[0].pending.records.size() == 1U &&
              p.incoming[0].pending.records[0].slot0_target_identity == p.ready_pending_callback_identity,
          "positive growth captures actual canonical record callback target");
    Emit(directory, "canonical-positive-growth", row);
  }
  {
    Fixture f; f.Pending(0, 0, false); const auto row = f.Observe(); const auto &p = Leaf(row);
    Check(p.incoming[0].pending.count_0c_raw_i32 == 0 && p.incoming[0].pending.records.empty(),
          "zero oldcount growth has no demanded record callbacks");
    Emit(directory, "zero-oldcount-growth", row);
  }
  {
    Fixture f; f.Pending(1, 1, true); const auto row = f.Observe(); const auto &p = Leaf(row);
    Check(p.incoming[0].pending.records[0].slot0_target_identity != p.ready_pending_callback_identity,
          "a different selected callback is observed rather than executed or invented canonical");
    Emit(directory, "different-callback-partial", row);
  }
  {
    Fixture f; f.m.Put(f.incoming, 0x2C, std::int32_t{-1}); const auto row = f.Observe(); const auto &p = Leaf(row);
    Check(p.incoming[0].data_count_raw_i32 == -1 && !p.incoming[0].data_ready,
          "negative signed DATA count preserves nonempty source cursor distinction");
    Emit(directory, "negative-data-prefix", row);
  }
  {
    Fixture f; f.bindings.current_detachment_data_bindings.compute_date = nullptr;
    const auto row = f.Observe(); const auto &p = Leaf(row);
    Check(p.incoming[0].data_ready && !p.incoming[0].date_inputs.empty(),
          "missing selected readonly date computation preserves captured wholeDATA and other physical operands");
    Emit(directory, "required-computed-date-partial", row);
  }
  {
    Fixture f; f.Records({{kInvalidRegi, 0}, {kInvalidRegi, 6}});
    f.bindings.current_detachment_data_bindings.compute_date = nullptr;
    const auto row = f.Observe(); const auto &p = Leaf(row);
    Check(p.incoming[0].data_ready && p.incoming[0].data_occurrences.size() == 2U && p.incoming[0].physical_chunks.empty(),
          "invalid raw records are a complete independent source skip with unused date absent");
    Emit(directory, "all-invalid-records", row);
  }
  {
    Fixture f; f.Queue({}); const auto row = f.Observe(); const auto &p = Leaf(row);
    Check(p.selection_ready && p.roster_ready && p.incoming.empty() && p.candidate_occurrences.empty(),
          "observed empty current pending selection is a ready not-called family");
    Emit(directory, "no-current-candidate", row);
  }
}
} // namespace
int main(int argc, char **argv) {
  try {
    const auto directory = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path("current-detachment-data-wire");
    std::filesystem::create_directories(directory); Cases(directory);
    std::cout << "new current incoming whole DATA inputs: 8 scenes GREEN\n"; return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n'; return 1;
  }
}
