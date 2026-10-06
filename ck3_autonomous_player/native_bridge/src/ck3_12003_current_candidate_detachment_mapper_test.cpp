#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12003_current_candidate_detachment_mapper.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>

namespace {
using namespace xar;
void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  struct Range { const void *address; std::size_t size; };
  std::vector<Region> regions;
  std::vector<Range> requests, denied;
  void *Allocate(std::size_t size) {
    auto bytes = std::make_unique<std::byte[]>(size); auto *pointer = bytes.get();
    regions.push_back({std::move(bytes), size}); return pointer;
  }
  template <class T> void Put(void *pointer, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(pointer) + offset, &value, sizeof(value));
  }
  void Deny(const void *pointer, std::size_t offset, std::size_t size) {
    denied.push_back({static_cast<const std::byte *>(pointer) + offset, size});
  }
  std::size_t Reads(const void *pointer, std::size_t offset, std::size_t size) const {
    const auto *address = static_cast<const std::byte *>(pointer) + offset;
    return static_cast<std::size_t>(std::count_if(requests.begin(), requests.end(),
        [&](const auto &row) { return row.address == address && row.size == size; }));
  }
  static bool Read(void *context, const void *address, void *output, std::size_t size) noexcept {
    auto &m = *static_cast<Memory *>(context); m.requests.push_back({address, size});
    for (const auto &row : m.denied) if (row.address == address && row.size == size) return false;
    const auto start = reinterpret_cast<std::uintptr_t>(address);
    for (const auto &region : m.regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(region.bytes.get());
      if (start >= base && start - base <= region.size && size <= region.size - (start - base)) {
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
      store(m.Allocate(0x30)), table(m.Allocate(32 * 16)) {
    m.Put(slot, 0, store); m.Put(store, 0x20, table); m.Put(store, 0x2C, std::uint32_t{32});
  }
  void Add(std::uint32_t id, void *object) {
    m.Put(table, static_cast<std::size_t>(id & 0xFFFFFFU) * 16 + 8, object); m.Put(object, 0x10, id);
  }
};
constexpr std::uint32_t kUnit = 0x11000001U, kSubject = 0x22000001U, kCandidate = 0x22000002U;
constexpr std::uint32_t kLegacy = 0x2B000001U, kWrongArmy = 0xAB00000CU, kWrongArRg = 0xEE00000FU;
void *expected_subject = nullptr;
std::int32_t Current(void *receiver, std::uint8_t flags) {
  Check(receiver == static_cast<std::byte *>(expected_subject) + 0x38 && flags == 0,
        "mapper fixture actual subject current helper receiver"); return 20;
}
std::int32_t Maximum(void *receiver) {
  Check(receiver == expected_subject, "mapper fixture actual subject maximum receiver"); return 40;
}
struct Fixture {
  Memory m;
  Registry units{m}, armies{m}, arrgs{m}, regis{m};
  ck3_12002::ArmyBindings bindings{};
  void *state_slot = m.Allocate(8), *state = m.Allocate(0xA8);
  void *data = m.Allocate(0x2A540 + 0x500), *manager = static_cast<std::byte *>(data) + 0x2A540;
  void *unit = m.Allocate(0x180), *subject = m.Allocate(0x208), *candidate = m.Allocate(0x208);
  void *legacy = m.Allocate(0x150), *arrg_fallback = m.Allocate(0x150), *regi_fallback = m.Allocate(0x150);
  std::array<void *, 6> raised{}, persistent{};
  Fixture() {
    bindings.enabled = true; bindings.game_state_slot = static_cast<void **>(state_slot);
    bindings.unit_storage_slot = static_cast<void **>(units.slot);
    bindings.internal_army_storage_slot = static_cast<void **>(armies.slot);
    bindings.regiment_storage_slot = static_cast<void **>(arrgs.slot);
    bindings.get_army_current_soldiers = Current; bindings.get_army_maximum_soldiers = Maximum;
    bindings.monthly_daily_queue_bindings.enabled = true;
    bindings.monthly_daily_queue_bindings.army_fallback_slot = static_cast<void **>(armies.fallback_slot);
    bindings.monthly_first_removal_cleanup_inputs_enabled = true;
    auto &lookup = bindings.current_assault_removal_reference_bindings.lookup;
    bindings.current_assault_removal_reference_bindings.enabled = true;
    lookup.enabled = true; lookup.game_state_slot = state_slot;
    lookup.army_registry_slot = armies.slot; lookup.army_fallback_slot = armies.fallback_slot;
    lookup.arrg_registry_slot = arrgs.slot; lookup.arrg_fallback_slot = arrgs.fallback_slot;
    lookup.read_memory = Memory::Read; lookup.read_context = &m;
    auto &mapper = bindings.current_candidate_detachment_mapper_bindings;
    mapper.enabled = true; mapper.lookup = lookup;
    mapper.regi_registry_slot = regis.slot; mapper.regi_fallback_slot = regis.fallback_slot;
    m.Put(state_slot, 0, state); m.Put(state, 0xA0, data);
    units.Add(kUnit, unit); armies.Add(kSubject, subject); armies.Add(kCandidate, candidate);
    m.Put(subject, 0x14, std::uint32_t{0x41726D79}); m.Put(candidate, 0x14, std::uint32_t{0x41726D79});
    m.Put(armies.fallback_slot, 0, candidate);
    m.Put(unit, 0x178, kSubject); m.Put(subject, 0x124, kUnit); m.Put(candidate, 0x124, kUnit);
    arrgs.Add(kLegacy, legacy); m.Put(legacy, 0x14, std::uint32_t{0x41725267});
    m.Put(legacy, 0x38, std::int32_t{20}); m.Put(legacy, 0x3C, std::int32_t{40});
    m.Put(legacy, 0x40, std::int64_t{100000});
    auto *subject_ids = m.Allocate(4); m.Put(subject_ids, 0, kLegacy);
    m.Put(subject, 0x38, subject_ids); m.Put(subject, 0x40, std::int32_t{1}); m.Put(subject, 0x44, std::int32_t{1});
    m.Put(arrgs.fallback_slot, 0, arrg_fallback); m.Put(arrg_fallback, 0x10, std::uint32_t{0xFFFFFFFF});
    m.Put(arrg_fallback, 0x14, std::uint32_t{0x446C7464}); m.Put(arrg_fallback, 0x14C, std::int32_t{0});
    m.Put(regis.fallback_slot, 0, regi_fallback); m.Put(regi_fallback, 0x10, std::uint32_t{0xFFFFFFFF});
    m.Put(regi_fallback, 0x14, std::uint32_t{0x446C7464}); m.Put(regi_fallback, 0x138, std::int32_t{4});
    for (std::size_t i = 0; i < raised.size(); ++i) {
      raised[i] = m.Allocate(0x150); persistent[i] = m.Allocate(0x150);
      const auto offset = static_cast<std::uint32_t>(i) + 2U;
      arrgs.Add(0xAB000000U + offset, raised[i]); regis.Add(0xCC000000U + offset, persistent[i]);
      m.Put(raised[i], 0x14, std::uint32_t{0x41725267});
      m.Put(raised[i], 0x14C, std::int32_t{i == 0U ? 4 : i == 5U ? 9 : 1});
      m.Put(raised[i], 0x2C, std::int32_t{1});
      auto *record = m.Allocate(16); m.Put(record, 8, 0xCC000000U + offset); m.Put(raised[i], 0x20, record);
      m.Put(persistent[i], 0x14, std::uint32_t{0x52656769}); m.Put(persistent[i], 0x138, std::int32_t{4});
    }
    m.Put(persistent[1], 0x128, std::int32_t{8}); Chunk(persistent[1], 0, 10, 2, 0);
    m.Put(persistent[2], 0x128, std::int32_t{7});
    m.Put(persistent[3], 0x128, std::int32_t{1}); Chunk(persistent[3], 0, 5, 1, 0);
    m.Put(persistent[4], 0x128, std::numeric_limits<std::int32_t>::max());
    Chunk(persistent[4], 0, 1, 3, 0); Chunk(persistent[4], 1, 20, 0, 3);
    Pending({static_cast<std::int32_t>(kWrongArmy), static_cast<std::int32_t>(kCandidate), static_cast<std::int32_t>(kWrongArmy)});
    Roster({0xAB000002U, 0xAB000002U, 0xAB000003U, 0xAB000004U, 0xAB000005U,
            0xAB000006U, 0xAB000007U, kWrongArRg, kWrongArRg});
    expected_subject = subject;
  }
  void Chunk(void *regi, std::size_t index, std::int32_t maximum, std::int32_t current, std::int32_t state_value) {
    const auto offset = 0x18 + index * 0x24;
    m.Put(regi, offset, maximum); m.Put(regi, offset + 4, current); m.Put(regi, offset + 0x18, state_value);
  }
  void Pending(const std::vector<std::int32_t> &ids) {
    auto *buffer = ids.empty() ? nullptr : m.Allocate(ids.size() * 4);
    for (std::size_t i = 0; i < ids.size(); ++i) m.Put(buffer, i * 4, ids[i]);
    m.Put(manager, 0x68, buffer); m.Put(manager, 0x74, static_cast<std::int32_t>(ids.size()));
  }
  void Roster(const std::vector<std::uint32_t> &ids) {
    auto *buffer = ids.empty() ? nullptr : m.Allocate(ids.size() * 4);
    for (std::size_t i = 0; i < ids.size(); ++i) m.Put(buffer, i * 4, ids[i]);
    m.Put(candidate, 0x38, buffer); m.Put(candidate, 0x44, static_cast<std::int32_t>(ids.size()));
  }
  game::ArmyStrengthSnapshot Observe() {
    const std::array<ck3_12002::ArmyStrengthScope, 1> scope{{
        {static_cast<std::int32_t>(kUnit), game::ArmyStrengthScopeRole::player, {}}}};
    std::vector<game::ArmyStrengthSnapshot> rows;
    Check(ck3_12002::ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available &&
              rows.size() == 1U && rows[0].available && rows[0].current_soldiers == 20 &&
              rows[0].maximum_soldiers == 40 && rows[0].current_candidate_detachment_mapper_inputs_v1,
          "new mapper family must preserve actual whole ArmyStrength reader");
    Check(m.Reads(manager, 0x68, 8) == 0U && m.Reads(manager, 0x74, 4) == 0U,
          "new mapper borrows captured current pending without another queue read");
    return std::move(rows[0]);
  }
};
const game::ArmyCurrentCandidateDetachmentMapperInputsV1 &Leaf(const game::ArmyStrengthSnapshot &row) {
  return *row.current_candidate_detachment_mapper_inputs_v1;
}
void Emit(const std::filesystem::path &directory, const char *name, const game::ArmyStrengthSnapshot &row) {
  std::string wire;
  game::AppendArmyStrengthV1(wire, row, [](auto value) { return std::to_string(value); },
      [](std::string &out, const std::vector<std::int32_t> &values) {
        out += '[';
        for (std::size_t i = 0; i < values.size(); ++i) { if (i) out += ','; out += std::to_string(values[i]); }
        out += ']';
      }, [](std::string &out, std::string_view value) { out += '"'; out += value; out += '"'; });
  std::ofstream file(directory / (std::string("candidate-detachment-mapper-") + name + ".json"), std::ios::binary);
  file << wire << '\n'; Check(static_cast<bool>(file), "new mapper whole-strength wire output");
}
void Cases(const std::filesystem::path &directory) {
  {
    Fixture f; f.m.Deny(f.persistent[0], 0x128, 4); f.m.Deny(f.raised[5], 0x2C, 4);
    const auto row = f.Observe(); const auto &p = Leaf(row);
    Check(p.ready && p.occurrences.size() == 9U && p.mappers.size() == 7U && p.count_inputs.size() == 4U,
          "whole ordered raw roster, invalid fallback and physical alias reuse");
    Check(p.occurrences[0].mapper_index == p.occurrences[1].mapper_index &&
              p.occurrences[7].mapper_index == p.occurrences[8].mapper_index &&
              p.occurrences[7].resolution.used_fallback == true,
          "duplicate/fallback occurrences remain separate with shared mapper snapshot");
    Check(f.m.Reads(f.raised[0], 0x14C, 4) == 1U && f.m.Reads(f.persistent[0], 0x128, 4) == 0U &&
              f.m.Reads(f.raised[5], 0x2C, 4) == 0U,
          "aliases sampled once and kind4/unrelatedkind skip unused operands");
    Check(ck3_12003::candidate_mapper_detail::CountValue(p.count_inputs[0]) == 0 &&
              ck3_12003::candidate_mapper_detail::CountValue(p.count_inputs[1]) == 7 &&
              ck3_12003::candidate_mapper_detail::CountValue(p.count_inputs[2]) == -3 &&
              ck3_12003::candidate_mapper_detail::CountValue(p.count_inputs[3]) == -2147483647,
          "source seven-chunk signed zero/positive/negative/overflow counts");
    Check(p.mappers[2].return_selection == "native_fallback" &&
              p.mappers[6].returned_regi_full_id_u32 == 0xFFFFFFFFU && p.mappers[6].returned_state_138_raw_i32 == 4,
          "positive count and invalid fallback still publish actual returned state");
    Emit(directory, "ordered-branches-and-aliases", row);
  }
  {
    Fixture f; f.Roster({0xAB000002U}); f.m.Put(f.raised[0], 0x2C, std::int32_t{-5});
    f.m.Deny(f.persistent[0], 0x128, 4); const auto row = f.Observe(); const auto &p = Leaf(row);
    Check(p.ready && p.mappers[0].data_count_raw_i32 == -5 &&
              p.mappers[0].first_regi_full_id_u32 == 0xCC000002U && p.count_inputs.empty(),
          "negative DATA count is nonzero firstrecord source branch");
    Emit(directory, "negative-data-count-first-record", row);
  }
  {
    Fixture f; f.Roster({0xAB000002U}); f.m.Put(f.raised[0], 0x2C, std::int32_t{0});
    f.m.Deny(f.raised[0], 0x20, 8); const auto row = f.Observe(); const auto &p = Leaf(row);
    Check(p.ready && p.mappers[0].first_regi_full_id_u32 == 0xFFFFFFFFU &&
              p.mappers[0].returned_state_138_raw_i32 == 4 && f.m.Reads(f.raised[0], 0x20, 8) == 0U,
          "exact zero count skips unused data and retains invalid fallback state");
    Emit(directory, "zero-data-count-invalid-fallback", row);
  }
  {
    Fixture f; f.Roster({0xAB000007U}); f.m.Deny(f.raised[5], 0x2C, 4); f.m.Deny(f.raised[5], 0x20, 8);
    const auto row = f.Observe(); const auto &p = Leaf(row);
    Check(p.ready && p.count_inputs.empty() && !p.mappers[0].selected_regi_resolution &&
              f.m.Reads(f.raised[5], 0x2C, 4) == 0U && f.m.Reads(f.raised[5], 0x20, 8) == 0U,
          "unrelated kind independently ready with unused DATA absent");
    Emit(directory, "unrelated-kind-unused-data", row);
  }
  {
    Fixture f; f.Roster({0xAB000003U, 0xAB000002U}); f.m.Deny(f.persistent[1], 0x128, 4);
    const auto row = f.Observe(); const auto &p = Leaf(row);
    Check(!p.ready && !p.mappers[0].return_selection_ready && p.mappers[1].ready && p.occurrences[1].ready,
          "required kind1 count partial preserves independent kind4 result");
    Emit(directory, "required-kind1-count-partial", row);
  }
  {
    Fixture f; f.Roster({0xAB000007U, 0xAB000002U}); f.m.Deny(f.regi_fallback, 0x138, 4);
    const auto row = f.Observe(); const auto &p = Leaf(row);
    Check(!p.ready && p.mappers[0].return_selection_ready && !p.mappers[0].returned_state_138_raw_i32 && p.mappers[1].ready,
          "return branch independently ready while demanded caller state is partial");
    Emit(directory, "returned-state-partial", row);
  }
  {
    Fixture f; f.bindings.monthly_daily_queue_bindings.enabled = false;
    const auto row = f.Observe(); const auto &p = Leaf(row);
    Check(!p.ready && !p.selection_ready && p.occurrences.empty(), "absent captured initial pending is not invented empty");
    Emit(directory, "current-pending-unavailable", row);
  }
  {
    Fixture f; f.Pending({}); const auto row = f.Observe(); const auto &p = Leaf(row);
    Check(p.ready && p.selection_ready && p.selection_branch == "not_called" && p.occurrences.empty(),
          "observed empty pending is independently ready and does not demand candidate DATA");
    Emit(directory, "observed-empty-pending", row);
  }
}
} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "new mapper fixture requires output directory");
    const std::filesystem::path directory(argv[1]); std::filesystem::create_directories(directory);
    Cases(directory); std::cout << "FIRST eight new current mapper production wires GREEN\n"; return 0;
  } catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 1; }
}
