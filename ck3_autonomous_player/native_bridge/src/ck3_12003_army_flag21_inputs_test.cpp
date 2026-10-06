#include "xar_bridge/ck3_12003_army_flag21_inputs.hpp"
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <initializer_list>
#include <memory>
#include <stdexcept>

namespace {
using namespace xar;
void Check(bool value, const char *message) { if (!value) throw std::runtime_error(message); }
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  struct Denied { const void *address; std::size_t size; };
  std::vector<Region> regions;
  std::vector<Denied> denied;
  std::size_t denied_attempts = 0;
  bool flag21_reads = false;
  void *Allocate(std::size_t size) {
    auto bytes = std::make_unique<std::byte[]>(size); auto *object = bytes.get();
    regions.push_back({std::move(bytes), size}); return object;
  }
  template <class T> void Put(void *object, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
  }
  void Deny(const void *object, std::size_t offset, std::size_t size) {
    denied.push_back({static_cast<const std::byte *>(object) + offset, size});
  }
  std::vector<std::vector<std::byte>> Snapshot() const {
    std::vector<std::vector<std::byte>> out;
    for (const auto &region : regions) out.emplace_back(region.bytes.get(), region.bytes.get() + region.size);
    return out;
  }
  static bool Read(void *context, const void *address, void *out, std::size_t size) noexcept {
    auto &m = *static_cast<Memory *>(context); const auto begin = reinterpret_cast<std::uintptr_t>(address);
    for (const auto &range : m.denied) {
      const auto denied = reinterpret_cast<std::uintptr_t>(range.address);
      if (m.flag21_reads && begin < denied + range.size && denied < begin + size) {
        ++m.denied_attempts; return false;
      }
    }
    for (const auto &region : m.regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(region.bytes.get());
      if (begin >= base && begin - base <= region.size && size <= region.size - (begin - base)) {
        std::memcpy(out, address, size); return true;
      }
    }
    return false;
  }
  static bool Flag21Read(void *context, const void *address, void *out, std::size_t size) noexcept {
    auto &m = *static_cast<Memory *>(context); m.flag21_reads = true;
    const bool copied = Read(context, address, out, size); m.flag21_reads = false; return copied;
  }
};
struct Registry {
  Memory &memory;
  void *slot, *fallback_slot, *store, *rows;
  Registry(Memory &m) : memory(m), slot(m.Allocate(8)), fallback_slot(m.Allocate(8)),
      store(m.Allocate(0x30)), rows(m.Allocate(16 * 16)) {
    m.Put(slot, 0, store); m.Put(store, 0x20, rows); m.Put(store, 0x2C, std::uint32_t{16});
  }
  void Add(std::uint32_t id, void *object, std::size_t full_offset = 0x10) {
    memory.Put(rows, (id & 0xFFFFFFU) * 16 + 8, object); memory.Put(object, full_offset, id);
  }
};
struct Fixture;
Fixture *active = nullptr;
std::uint8_t SharedTail(const void *);
std::int32_t Current(void *, std::uint8_t);
std::int32_t Maximum(void *);
struct Fixture {
  static constexpr std::uint32_t kArmy = 0xAB000001U, kUnit = 0x88000001U, kCharacter = 0xFE000002U;
  static constexpr std::uint32_t kSubjectUnit = 11, kSubjectArmy = 12, kSubjectArRg = 13;
  Memory memory;
  Registry armies{memory}, units{memory}, characters{memory}, arrgs{memory}, subject_units{memory};
  void *army = memory.Allocate(0x200), *unit = memory.Allocate(0x180), *fallback_unit = memory.Allocate(0x180);
  void *character = memory.Allocate(0x200), *fallback_character = memory.Allocate(0x200);
  void *carrier = memory.Allocate(0x400), *default_header = memory.Allocate(0x10);
  void *state_slot = memory.Allocate(8), *state = memory.Allocate(0xA8);
  void *data = memory.Allocate(0x2A540 + 0x190), *manager = static_cast<std::byte *>(data) + 0x2A540;
  void *subject_unit = memory.Allocate(0x180), *subject_army = memory.Allocate(0x200);
  void *subject_arrg = memory.Allocate(0x150);
  ck3_12003::CurrentArmyFlag21Bindings12003 bindings{};
  ck3_12002::ArmyBindings query_bindings{};
  std::vector<game::ArmyStrengthSnapshot> whole_rows;
  std::uint8_t tail_value = std::uint8_t{1};
  std::int32_t tail_calls = 0;
  std::size_t expected_denied_attempts = 0;
  bool missing_materialization = false;
  Fixture() {
    armies.Add(kArmy, army); memory.Put(armies.fallback_slot, 0, army);
    units.Add(kUnit, unit); memory.Put(units.fallback_slot, 0, fallback_unit);
    characters.Add(kCharacter, character, 0x18); memory.Put(characters.fallback_slot, 0, fallback_character);
    memory.Put(army, 0x124, kUnit); memory.Put(army, 0x1EC, std::uint8_t{1});
    memory.Put(army, 0x1F0, std::int64_t{0}); memory.Put(army, 0x21, std::uint8_t{187});
    memory.Put(unit, 0x18, std::uint32_t{1}); memory.Put(unit, 0x174, kCharacter);
    memory.Put(character, 0x1C0, carrier); memory.Put(carrier, 0x324, std::int32_t{1});
    armies.Add(kSubjectArmy, subject_army); subject_units.Add(kSubjectUnit, subject_unit); arrgs.Add(kSubjectArRg, subject_arrg);
    memory.Put(subject_unit, 0x178, kSubjectArmy); memory.Put(subject_army, 0x124, kSubjectUnit);
    memory.Put(subject_arrg, 0x14, std::uint32_t{0x41725267});
    memory.Put(subject_arrg, 0x38, std::int32_t{20}); memory.Put(subject_arrg, 0x3C, std::int32_t{40});
    memory.Put(subject_arrg, 0x40, std::int64_t{4000000});
    memory.Put(state_slot, 0, state); memory.Put(state, 0xA0, data);
    Ids(static_cast<std::byte *>(manager) + 0x50, {kArmy, kArmy});
    Ids(static_cast<std::byte *>(manager) + 0x68, {}); Ids(static_cast<std::byte *>(army) + 0x38, {});
    Ids(static_cast<std::byte *>(subject_army) + 0x38, {kSubjectArRg});
    auto &common = bindings.common; common.enabled = true; common.game_state_slot = state_slot;
    common.army_registry_slot = armies.slot; common.army_fallback_slot = armies.fallback_slot;
    common.unit_registry_slot = units.slot; common.unit_fallback_slot = units.fallback_slot;
    common.character_registry_slot = characters.slot; common.character_fallback_slot = characters.fallback_slot;
    common.read_memory = Memory::Read; common.read_context = &memory;
    bindings.default_header = default_header; bindings.get_current_shared_tail = SharedTail;
    query_bindings.enabled = true; query_bindings.game_state_slot = static_cast<void **>(state_slot);
    query_bindings.unit_storage_slot = static_cast<void **>(subject_units.slot);
    query_bindings.internal_army_storage_slot = static_cast<void **>(armies.slot);
    query_bindings.regiment_storage_slot = static_cast<void **>(arrgs.slot);
    query_bindings.get_army_current_soldiers = Current; query_bindings.get_army_maximum_soldiers = Maximum;
    query_bindings.current_daily_assault_roster_admission_bindings = common;
    auto &refresh = query_bindings.current_post_admission_refresh_bindings;
    refresh.common = common; refresh.arrg_registry_slot = arrgs.slot; refresh.arrg_fallback_slot = arrgs.fallback_slot;
    // Only the new family sees demand denials; the borrowed postadmission capture remains genuine.
    bindings.common.read_memory = Memory::Flag21Read;
  }
  void Ids(void *header, std::initializer_list<std::uint32_t> ids) {
    memory.Put(header, 8, static_cast<std::int32_t>(ids.size()));
    memory.Put(header, 0xC, static_cast<std::int32_t>(ids.size()));
    void *raw = ids.size() ? memory.Allocate(ids.size() * 4) : nullptr;
    std::size_t index = 0; for (auto id : ids) memory.Put(raw, index++ * 4, id);
    memory.Put(header, 0, raw);
  }
  void PositiveQword() {
    memory.Put(army, 0x1F0, std::int64_t{1} << 40);
    memory.Deny(army, 0x124, 4); memory.Deny(unit, 0x174, 4); memory.Deny(character, 0x1C0, 8);
  }
  game::ArmyCurrentFlag21InputsV1 Observe() {
    active = this; const auto before = memory.Snapshot();
    query_bindings.current_army_flag21_bindings = bindings;
    const std::array<ck3_12002::ArmyStrengthScope, 2> scopes{{
        {static_cast<std::int32_t>(kSubjectUnit), game::ArmyStrengthScopeRole::player, {}},
        {static_cast<std::int32_t>(kSubjectUnit), game::ArmyStrengthScopeRole::active_war_ally, {7}}}};
    Check(ck3_12002::ReadArmyStrengthsForScope(query_bindings, scopes, whole_rows) ==
              game::ReadArmyStrengthsResult::available && whole_rows.size() == 2,
          "flag21 requires genuine whole query source route");
    for (const auto &row : whole_rows) {
      Check(row.available && row.current_soldiers == 20 && row.maximum_soldiers == 40 &&
                row.regiment_count == 1 && row.ai_base_power_raw == std::int64_t{4000000},
            "flag21 optional partial must retain independent current strength");
      Check(row.current_post_admission_refresh_inputs_v1 && row.current_army_flag21_inputs_v1,
            "flag21 must borrow genuine postadmission capture through actual Root hook");
    }
    Check(whole_rows[0].current_army_flag21_inputs_v1 == whole_rows[1].current_army_flag21_inputs_v1,
          "flag21 global collector should capture once for both requested scope rows");
    auto out = *whole_rows[0].current_army_flag21_inputs_v1;
    Check(before == memory.Snapshot(), "flag21 query wrote Army/world inputs");
    Check(memory.denied_attempts == expected_denied_attempts, "flag21 reads disagree with actual branch demand");
    Check(out.occurrences.size() == 2 && out.original_roster.occurrences.size() == 2,
          "flag21 filtered original duplicate roster occurrences");
    for (const auto &row : out.occurrences) {
      Check(row.raw_full_id_u32 == kArmy, "flag21 lost original fullDWORD bits");
      if (missing_materialization)
        Check(!row.same_query_army_selection_matched && !row.actual_army_21_raw_u8,
              "flag21 materialization failure fabricated physicalArmy/cache value");
      else Check(row.same_query_army_selection_matched && row.actual_army_21_raw_u8 == std::uint8_t{187},
                 "flag21 lost physical selection/cached21 separation");
    }
    Check(!out.actual_refresh_execution_ready && !out.actual_next_occurrence_ready && !out.full_callback_ready &&
              !out.full_daily_assault_ready && !out.full_monthly_ready,
          "flag21 may not raise future refresh or callback readiness");
    return out;
  }
};
std::int32_t Current(void *receiver, std::uint8_t flags) {
  Check(active && flags == std::uint8_t{0} && receiver == static_cast<std::byte *>(active->subject_army) + 0x38,
        "flag21 whole current strength getter arguments changed"); return 20;
}
std::int32_t Maximum(void *receiver) {
  Check(active && receiver == active->subject_army, "flag21 whole maximum strength getter receiver changed"); return 40;
}
std::uint8_t SharedTail(const void *army) {
  Check(active && army == active->army, "flag21 tail must use actual borrowed physicalArmy, not parsed identity");
  ++active->tail_calls;
  // Synthetic return validates real collector plumbing; it does not execute the EXE's shared-tail branches.
  return active->tail_value;
}
void Ready(const Fixture &f, const game::ArmyCurrentFlag21InputsV1 &out, std::uint8_t value, bool tail_demanded) {
  Check(out.ready && out.current_flag21_inputs_ready && out.original_army_selections_ready,
        "flag21 independently observable current value did not become available");
  Check(f.tail_calls == (tail_demanded ? 2 : 0), "flag21 tail invocation demand/once-global count disagrees");
  for (const auto &row : out.occurrences) {
    Check(row.ready && row.derived_current_21_raw_u8 == value, "flag21 source/native current value changed");
    Check(row.native_shared_tail_returned == tail_demanded, "flag21 sourcezero/native return distinction lost");
    if (tail_demanded) Check(row.native_shared_tail_21_raw_u8 == value, "flag21 actual returned AL changed");
    else Check(!row.native_shared_tail_21_raw_u8, "flag21 sourcezero fabricated shared-tail return");
  }
}
std::string Serialize(const Fixture &fixture) {
  std::string wire;
  game::AppendArmyStrengthV1(wire, fixture.whole_rows[0], [](auto value) { return std::to_string(value); },
      [](std::string &text, const std::vector<std::int32_t> &values) {
        text += '[';
        for (std::size_t i = 0; i < values.size(); ++i) { if (i) text += ','; text += std::to_string(values[i]); }
        text += ']';
      },
      [](std::string &text, std::string_view value) { text += '"'; text += value; text += '"'; });
  return wire;
}
}
int main(int argc, char **argv) {
  try {
    const auto bound = xar::ck3_12003::BindCurrentArmyFlag21Inputs12003(0x140000000ULL,
        "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6");
    Check(bound.common.enabled && reinterpret_cast<std::uintptr_t>(bound.get_current_shared_tail) == 0x1424E3FE0ULL &&
              reinterpret_cast<std::uintptr_t>(bound.default_header) == 0x145459D38ULL,
          "flag21 exact .3 binder must select actual shared-tail and inline static header");
    std::vector<std::pair<std::string, std::string>> samples;
    { Fixture f; f.memory.Put(f.army, 0x1EC, std::uint8_t{0}); f.bindings.get_current_shared_tail = nullptr;
      f.memory.Deny(f.army, 0x1F0, 8); f.memory.Deny(f.army, 0x124, 4); f.memory.Deny(f.default_header, 0xC, 4);
      auto out = f.Observe(); Ready(f, out, std::uint8_t{0}, false);
      Check(!out.occurrences[0].army_1f0_raw_i64 && !out.occurrences[0].header_selection,
            "flag21 zero1EC may not demand QWORD or owner header");
      samples.emplace_back("source-zero-1ec-undemanded", Serialize(f)); }
    { Fixture f; f.PositiveQword(); f.tail_value = std::uint8_t{0}; auto out = f.Observe(); Ready(f, out, std::uint8_t{0}, true);
      Check(out.occurrences[0].army_1f0_raw_i64 == (std::int64_t{1} << 40) && !out.occurrences[0].header_selection,
            "flag21 positive signed QWORD must not truncate to DWORD or demand header");
      samples.emplace_back("positive-qword-native-false", Serialize(f)); }
    { Fixture f; f.PositiveQword(); auto out = f.Observe(); Ready(f, out, std::uint8_t{1}, true);
      Check(out.occurrences[0].raw_full_id_u32 == Fixture::kArmy &&
                out.occurrences[0].original_army_resolution.used_fallback == false,
            "flag21 highbit fullArmy generation route changed");
      samples.emplace_back("positive-qword-native-true", Serialize(f)); }
    { Fixture f; f.units.Add(std::uint32_t{0}, f.unit); f.characters.Add(std::uint32_t{0}, f.character, 0x18);
      f.memory.Put(f.army, 0x124, std::uint32_t{0}); f.memory.Put(f.unit, 0x174, std::uint32_t{0});
      f.memory.Put(f.character, 0x1C0, static_cast<void *>(nullptr)); f.bindings.get_current_shared_tail = nullptr;
      auto out = f.Observe(); Ready(f, out, std::uint8_t{0}, false); const auto &row = out.occurrences[0];
      Check(row.army_124_raw_u32 == std::uint32_t{0} && row.unit_owner_174_raw_u32 == std::uint32_t{0} &&
                row.character_resolution.indexed_full_id_u32 == std::uint32_t{0} &&
                row.header_selection == "native_static" && row.header_0c_raw_i32 == std::int32_t{0},
            "flag21 fullgen0/native-static countzero source boundary changed");
      samples.emplace_back("native-static-header-zero-fullgen0", Serialize(f)); }
    { Fixture f; f.memory.Put(f.army, 0x1F0, -(std::int64_t{1} << 40)); f.memory.Put(f.carrier, 0x324, std::int32_t{-1});
      auto out = f.Observe(); Ready(f, out, std::uint8_t{1}, true); const auto &row = out.occurrences[0];
      Check(row.army_1f0_raw_i64 == -(std::int64_t{1} << 40) && row.unit_owner_174_raw_u32 == Fixture::kCharacter &&
                row.header_selection == "carrier_inline" && row.header_0c_raw_i32 == std::int32_t{-1},
            "flag21 negative signed QWORD/count and whole ownerDWORD route changed");
      samples.emplace_back("carrier-negative-header-native-true", Serialize(f)); }
    { Fixture f; f.memory.Put(f.units.slot, 0, static_cast<void *>(nullptr));
      f.memory.Put(f.characters.slot, 0, static_cast<void *>(nullptr)); f.memory.Put(f.default_header, 0xC, std::int32_t{5});
      f.memory.Deny(f.army, 0x124, 4); f.memory.Deny(f.fallback_unit, 0x10, 4);
      f.memory.Deny(f.fallback_unit, 0x174, 4); f.memory.Deny(f.fallback_character, 0x18, 4);
      f.tail_value = std::uint8_t{0}; auto out = f.Observe(); Ready(f, out, std::uint8_t{0}, true);
      const auto &row = out.occurrences[0];
      Check(row.unit_resolution.registry_loaded == false && row.unit_resolution.used_fallback == true &&
                row.character_resolution.registry_loaded == false && row.character_resolution.used_fallback == true &&
                !row.army_124_raw_u32 && !row.unit_owner_174_raw_u32 && row.header_0c_raw_i32 == std::int32_t{5},
            "flag21 actual null-store fallback may not demand Unit174 or fallback fullID metadata");
      samples.emplace_back("null-stores-fallback-header-native-false", Serialize(f)); }
    { Fixture f; f.PositiveQword(); f.bindings.get_current_shared_tail = nullptr; auto out = f.Observe();
      Check(!out.ready && f.tail_calls == 0 && !out.occurrences[0].native_shared_tail_21_raw_u8 &&
                !out.occurrences[0].derived_current_21_raw_u8,
            "flag21 missing demanded callable must remain independently unknown");
      samples.emplace_back("missing-shared-tail-callable", Serialize(f)); }
    { Fixture f; f.memory.Put(f.character, 0x1C0, static_cast<void *>(nullptr));
      f.memory.Deny(f.default_header, 0xC, 4); f.expected_denied_attempts = 2; auto out = f.Observe();
      Check(!out.ready && f.tail_calls == 0 && !out.occurrences[0].owner_header_inputs_ready &&
                !out.occurrences[0].header_0c_raw_i32 && !out.occurrences[0].derived_current_21_raw_u8,
            "flag21 missing demanded actual header count must remain independently unknown");
      samples.emplace_back("missing-demanded-header-count", Serialize(f)); }
    { Fixture f; f.missing_materialization = true; f.memory.Deny(f.armies.slot, 0, 8);
      f.expected_denied_attempts = 1; auto out = f.Observe();
      Check(!out.ready && f.tail_calls == 0 && !out.occurrences[0].same_query_army_selection_matched &&
                !out.occurrences[0].derived_current_21_raw_u8,
            "flag21 missing materialization must remain independently unknown");
      samples.emplace_back("missing-army-materialization", Serialize(f)); }
    if (argc == 3 && std::string_view(argv[1]) == "--wire-dir") {
      const std::filesystem::path directory(argv[2]); std::filesystem::create_directories(directory);
      std::ofstream file(directory / "ck3_12003_army_flag21_inputs_wire.json", std::ios::binary);
      file << "{\"samples\":{";
      for (std::size_t i = 0; i < samples.size(); ++i) {
        if (i) file << ',';
        file << '"' << samples[i].first << "\":" << samples[i].second;
      }
      file << "},\"qualification\":\"genuine whole ReadArmyStrengthsForScope +AppendArmyStrengthV1; nine scenes times two scopes and two repeated occurrences; world/tailcallbacks synthetic; no baseline or field transplant; newcurrent21 only\"}\n";
      Check(static_cast<bool>(file), "flag21 fixture whole wire write failed");
    }
    std::cout << "NEW current21 nine wholequery samples passed; synthetic tailcallbacks, no game execution\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 1; }
}
