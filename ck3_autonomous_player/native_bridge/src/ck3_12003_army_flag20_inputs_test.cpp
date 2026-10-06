#include "xar_bridge/ck3_12003_army_flag20_inputs.hpp"
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
  bool flag20_reads = false;
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
      if (m.flag20_reads && begin < denied + range.size && denied < begin + size) {
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
  static bool Flag20Read(void *context, const void *address, void *out, std::size_t size) noexcept {
    auto &m = *static_cast<Memory *>(context); m.flag20_reads = true;
    const bool copied = Read(context, address, out, size); m.flag20_reads = false; return copied;
  }
};
struct Registry {
  Memory &memory;
  void *slot, *fallback_slot, *store, *rows;
  Registry(Memory &m) : memory(m), slot(m.Allocate(8)), fallback_slot(m.Allocate(8)),
      store(m.Allocate(0x30)), rows(m.Allocate(16 * 16)) {
    m.Put(slot, 0, store); m.Put(store, 0x20, rows); m.Put(store, 0x2C, std::uint32_t{16});
  }
  void Add(std::uint32_t id, void *object) {
    memory.Put(rows, (id & 0xFFFFFFU) * 16 + 8, object); memory.Put(object, 0x10, id);
  }
};
struct Fixture;
Fixture *active = nullptr;
std::uint8_t GetCurrent20(const void *);
std::int32_t Current(void *, std::uint8_t);
std::int32_t Maximum(void *);
struct Fixture {
  static constexpr std::uint32_t kArmy = 0xAB000001U, kUnit = 0x88000001U;
  static constexpr std::uint32_t kSubjectUnit = 11, kSubjectArmy = 12, kSubjectArRg = 13;
  Memory memory;
  Registry armies{memory}, units{memory}, arrgs{memory}, subject_units{memory};
  void *army = memory.Allocate(0x200), *unit = memory.Allocate(0x180);
  void *state_slot = memory.Allocate(8), *state = memory.Allocate(0xA8);
  void *data = memory.Allocate(0x2A540 + 0x190), *manager = static_cast<std::byte *>(data) + 0x2A540;
  void *subject_unit = memory.Allocate(0x180), *subject_army = memory.Allocate(0x200);
  void *subject_arrg = memory.Allocate(0x150);
  ck3_12003::CurrentArmyFlag20Bindings12003 bindings{};
  ck3_12002::ArmyBindings query_bindings{};
  std::vector<game::ArmyStrengthSnapshot> whole_rows;
  std::uint32_t requested = kArmy, expected_selected_id = kArmy;
  std::uint8_t current_value = 1;
  std::int32_t getter_calls = 0;
  bool missing_materialization = false;
  Fixture() {
    armies.Add(kArmy, army); memory.Put(armies.fallback_slot, 0, army);
    units.Add(kUnit, unit); memory.Put(units.fallback_slot, 0, unit);
    memory.Put(army, 0x124, kUnit); memory.Put(army, 0x1D4, std::uint8_t{1});
    memory.Put(army, 0x20, std::uint8_t{187}); memory.Put(unit, 0x18, std::uint32_t{1});
    armies.Add(kSubjectArmy, subject_army); subject_units.Add(kSubjectUnit, subject_unit); arrgs.Add(kSubjectArRg, subject_arrg);
    memory.Put(subject_unit, 0x178, kSubjectArmy); memory.Put(subject_army, 0x124, kSubjectUnit);
    memory.Put(subject_arrg, 0x14, std::uint32_t{0x41725267});
    memory.Put(subject_arrg, 0x38, std::int32_t{20}); memory.Put(subject_arrg, 0x3C, std::int32_t{40});
    memory.Put(subject_arrg, 0x40, std::int64_t{4000000});
    memory.Put(state_slot, 0, state); memory.Put(state, 0xA0, data);
    Roster(requested); Ids(static_cast<std::byte *>(manager) + 0x68, {});
    Ids(static_cast<std::byte *>(army) + 0x38, {});
    Ids(static_cast<std::byte *>(subject_army) + 0x38, {kSubjectArRg});
    auto &common = bindings.common; common.enabled = true; common.game_state_slot = state_slot;
    common.army_registry_slot = armies.slot; common.army_fallback_slot = armies.fallback_slot;
    common.unit_registry_slot = units.slot; common.unit_fallback_slot = units.fallback_slot;
    common.read_memory = Memory::Read; common.read_context = &memory;
    bindings.get_current_flag20 = GetCurrent20;
    query_bindings.enabled = true; query_bindings.game_state_slot = static_cast<void **>(state_slot);
    query_bindings.unit_storage_slot = static_cast<void **>(subject_units.slot);
    query_bindings.internal_army_storage_slot = static_cast<void **>(armies.slot);
    query_bindings.regiment_storage_slot = static_cast<void **>(arrgs.slot);
    query_bindings.get_army_current_soldiers = Current; query_bindings.get_army_maximum_soldiers = Maximum;
    query_bindings.current_daily_assault_roster_admission_bindings = common;
    auto &refresh = query_bindings.current_post_admission_refresh_bindings;
    refresh.common = common; refresh.arrg_registry_slot = arrgs.slot; refresh.arrg_fallback_slot = arrgs.fallback_slot;
    // Read-demand denials apply only to the new family. Old same-query source capture stays genuine.
    bindings.common.read_memory = Memory::Flag20Read;
  }
  void Ids(void *header, std::initializer_list<std::uint32_t> ids) {
    memory.Put(header, 8, static_cast<std::int32_t>(ids.size()));
    memory.Put(header, 0xC, static_cast<std::int32_t>(ids.size()));
    void *raw = ids.size() ? memory.Allocate(ids.size() * 4) : nullptr;
    std::size_t index = 0; for (auto id : ids) memory.Put(raw, index++ * 4, id);
    memory.Put(header, 0, raw);
  }
  void Roster(std::uint32_t id) {
    requested = id; Ids(static_cast<std::byte *>(manager) + 0x50, {id, id});
  }
  game::ArmyCurrentFlag20InputsV1 Observe() {
    active = this; const auto before = memory.Snapshot();
    query_bindings.current_army_flag20_bindings = bindings;
    const std::array<ck3_12002::ArmyStrengthScope, 2> scopes{{
        {static_cast<std::int32_t>(kSubjectUnit), game::ArmyStrengthScopeRole::player, {}},
        {static_cast<std::int32_t>(kSubjectUnit), game::ArmyStrengthScopeRole::active_war_ally, {7}}}};
    Check(ck3_12002::ReadArmyStrengthsForScope(query_bindings, scopes, whole_rows) ==
              game::ReadArmyStrengthsResult::available && whole_rows.size() == 2,
          "flag20 requires genuine whole query source route");
    for (const auto &row : whole_rows) {
      Check(row.available && row.current_soldiers == 20 && row.maximum_soldiers == 40 &&
                row.regiment_count == 1 && row.ai_base_power_raw == 4000000,
            "flag20 optional partial must retain independent current strength");
      Check(row.current_post_admission_refresh_inputs_v1 && row.current_army_flag20_inputs_v1,
            "flag20 must borrow genuine postadmission capture with actual Root hook");
    }
    Check(whole_rows[0].current_army_flag20_inputs_v1 == whole_rows[1].current_army_flag20_inputs_v1,
          "flag20 global collector should capture once for both requested scope rows");
    auto out = *whole_rows[0].current_army_flag20_inputs_v1;
    Check(before == memory.Snapshot(), "flag20 query wrote Army/world inputs");
    Check(memory.denied_attempts == (missing_materialization ? std::size_t{1} : std::size_t{0}),
          "flag20 denied reads disagree with actual branch demand");
    Check(out.occurrences.size() == 2 && out.original_roster.occurrences.size() == 2,
          "flag20 filtered original repeated roster occurrences");
    for (const auto &row : out.occurrences) {
      Check(row.raw_full_id_u32 == requested, "flag20 lost original fullDWORD bits");
      if (missing_materialization)
        Check(!row.same_query_army_selection_matched && !row.actual_army_20_raw_u8,
              "flag20 materialization failure fabricated selectedArmy/cache value");
      else Check(row.same_query_army_selection_matched && row.actual_army_20_raw_u8 == 187,
                 "flag20 lost physical selection/cached20 separation");
    }
    Check(!out.actual_refresh_execution_ready && !out.actual_next_occurrence_ready && !out.full_callback_ready &&
              !out.full_daily_assault_ready && !out.full_monthly_ready,
          "flag20 may not raise future refresh or callback readiness");
    return out;
  }
};
std::int32_t Current(void *receiver, std::uint8_t flags) {
  Check(active && flags == 0 && receiver == static_cast<std::byte *>(active->subject_army) + 0x38,
        "flag20 whole current strength getter arguments changed"); return 20;
}
std::int32_t Maximum(void *receiver) {
  Check(active && receiver == active->subject_army, "flag20 whole maximum strength getter receiver changed"); return 40;
}
std::uint8_t GetCurrent20(const void *army) {
  Check(active && army == active->army, "flag20 callback must use actual borrowed physicalArmy, not parsed identity");
  std::uint32_t full_id = 0;
  std::memcpy(&full_id, static_cast<const std::byte *>(army) + 0x10, sizeof(full_id));
  Check(full_id == active->expected_selected_id, "flag20 callback selected fullDWORD identity changed");
  ++active->getter_calls;
  // Synthetic callable return tests collector plumbing, not execution of the EXE branch tree.
  return active->current_value;
}
void Ready(const Fixture &f, const game::ArmyCurrentFlag20InputsV1 &out, std::uint8_t value, bool demanded) {
  Check(out.ready && out.current_flag20_inputs_ready && out.original_army_selections_ready,
        "flag20 independently available getter did not unlock current value");
  Check(f.getter_calls == (demanded ? 2 : 0), "flag20 getter invocation demand/once-global count disagrees");
  for (const auto &row : out.occurrences) {
    Check(row.ready && row.derived_current_20_raw_u8 == value, "flag20 source/native current value changed");
    Check(row.native_getter_returned == demanded, "flag20 direct sourcezero/native return distinction lost");
    if (demanded) Check(row.native_getter_20_raw_u8 == value, "flag20 actual returned AL changed");
    else Check(!row.native_getter_20_raw_u8, "flag20 zero1D4 branch fabricated native getter return");
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
    const auto bound = xar::ck3_12003::BindCurrentArmyFlag20Inputs12003(0x140000000ULL,
        "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6");
    Check(bound.common.enabled && reinterpret_cast<std::uintptr_t>(bound.get_current_flag20) == 0x142C4B840ULL,
          "flag20 exact .3 binder does not select actual getter");
    std::vector<std::pair<std::string, std::string>> samples;
    { Fixture f; f.memory.Put(f.army, 0x1D4, std::uint8_t{0}); f.bindings.get_current_flag20 = nullptr;
      f.memory.Deny(f.army, 0x124, 4); f.memory.Deny(f.army, 0x1E0, 4);
      auto out = f.Observe(); Ready(f, out, std::uint8_t{0}, false);
      samples.emplace_back("zero-1d4-undemanded", Serialize(f)); }
    { Fixture f; f.current_value = std::uint8_t{0}; f.armies.Add(0, f.army); f.Roster(0); f.expected_selected_id = 0;
      auto out = f.Observe(); Ready(f, out, std::uint8_t{0}, true);
      Check(out.occurrences[0].original_army_resolution.selected_full_id_u32 == std::uint32_t{0},
            "flag20 must preserve fullgen0 without an added ID gate");
      samples.emplace_back("native-false-fullgen", Serialize(f)); }
    { Fixture f; f.memory.Put(f.army, 0x1D4, std::uint8_t{255}); auto out = f.Observe(); Ready(f, out, std::uint8_t{1}, true);
      Check(out.occurrences[0].raw_full_id_u32 == Fixture::kArmy &&
                out.occurrences[0].original_army_resolution.used_fallback == false,
            "flag20 highbit original fullID must stay whole generation route");
      samples.emplace_back("native-true-highbit-fullgen", Serialize(f)); }
    { Fixture f; f.Roster(0xCD000001U); auto out = f.Observe(); Ready(f, out, std::uint8_t{1}, true);
      Check(out.occurrences[0].original_army_resolution.used_fallback == true &&
                out.occurrences[0].original_army_resolution.selected_full_id_u32 == Fixture::kArmy,
            "flag20 wrong requested generation must retain actual fallback physicalArmy");
      samples.emplace_back("native-true-generation-fallback", Serialize(f)); }
    { Fixture f; f.bindings.get_current_flag20 = nullptr; auto out = f.Observe();
      Check(!out.ready && f.getter_calls == 0 && !out.occurrences[0].native_getter_20_raw_u8 &&
                !out.occurrences[0].derived_current_20_raw_u8,
            "flag20 missing callable must stay independently unknown, not false");
      samples.emplace_back("missing-getter", Serialize(f)); }
    { Fixture f; f.missing_materialization = true; f.memory.Deny(f.armies.slot, 0, 8); auto out = f.Observe();
      Check(!out.ready && f.getter_calls == 0 && !out.occurrences[0].same_query_army_selection_matched &&
                !out.occurrences[0].derived_current_20_raw_u8,
            "flag20 missing actual materialization must remain independently unknown");
      samples.emplace_back("missing-army-materialization", Serialize(f)); }
    if (argc == 3 && std::string_view(argv[1]) == "--wire-dir") {
      const std::filesystem::path directory(argv[2]); std::filesystem::create_directories(directory);
      std::ofstream file(directory / "ck3_12003_army_flag20_inputs_wire.json", std::ios::binary);
      file << "{\"samples\":{";
      for (std::size_t i = 0; i < samples.size(); ++i) {
        if (i) file << ',';
        file << '"' << samples[i].first << "\":" << samples[i].second;
      }
      file << "},\"qualification\":\"genuine whole ReadArmyStrengthsForScope +AppendArmyStrengthV1; fixture world/gettercallbacks synthetic; no baseline or field transplant; newcurrent20 only\"}\n";
      Check(static_cast<bool>(file), "flag20 fixture wire write failed");
    }
    std::cout << "NEW current20 six wholequery samples passed; synthetic callbacks, no game execution\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 1; }
}
