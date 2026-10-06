#include "xar_bridge/ck3_12003_army_flag31_inputs.hpp"
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"
#include <array>
#include <bit>
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
  bool flag31_reads = false;
  void *Allocate(std::size_t size) {
    auto bytes = std::make_unique<std::byte[]>(size);
    auto *object = bytes.get(); regions.push_back({std::move(bytes), size}); return object;
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
      const auto denied_begin = reinterpret_cast<std::uintptr_t>(range.address);
      if (m.flag31_reads && begin < denied_begin + range.size && denied_begin < begin + size) {
        ++m.denied_attempts; return false;
      }
    }
    for (const auto &region : m.regions) {
      const auto region_begin = reinterpret_cast<std::uintptr_t>(region.bytes.get());
      if (begin >= region_begin && begin - region_begin <= region.size && size <= region.size - (begin - region_begin)) {
        std::memcpy(out, address, size); return true;
      }
    }
    return false;
  }
  static bool Flag31Read(void *context, const void *address, void *out, std::size_t size) noexcept {
    auto &m = *static_cast<Memory *>(context); m.flag31_reads = true;
    const bool copied = Read(context, address, out, size); m.flag31_reads = false; return copied;
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
void *Construct(void *, const std::int32_t *);
void Destroy(void *);
bool Evaluate(const void *, void *);
std::int32_t Current(void *, std::uint8_t);
std::int32_t Maximum(void *);
struct Fixture {
  static constexpr std::uint32_t kArmy = 0xAB000001U, kUnit = 0x88000001U;
  static constexpr std::uint32_t kCharacter = 0xFE000002U, kCombat = 0xD1000003U;
  static constexpr std::uint32_t kSubjectUnit = 11, kSubjectArmy = 12, kSubjectArRg = 13;
  Memory memory;
  Registry armies{memory}, units{memory}, characters{memory}, combats{memory}, arrgs{memory}, subject_units{memory};
  void *army = memory.Allocate(0x200), *unit = memory.Allocate(0x180), *fallback_unit = memory.Allocate(0x180);
  void *character = memory.Allocate(0x200), *fallback_character = memory.Allocate(0x200);
  void *combat = memory.Allocate(0x10), *fallback_combat = memory.Allocate(0x10);
  void *provider_slot = memory.Allocate(8), *provider = memory.Allocate(0xF00);
  void *rule_array = memory.Allocate(0x1380 + 0xD0);
  void *state_slot = memory.Allocate(8), *state = memory.Allocate(0xA8);
  void *data = memory.Allocate(0x2A540 + 0x190), *manager = static_cast<std::byte *>(data) + 0x2A540;
  void *subject_unit = memory.Allocate(0x180), *subject_army = memory.Allocate(0x200);
  void *subject_arrg = memory.Allocate(0x150);
  ck3_12003::CurrentArmyFlag31Bindings12003 bindings{};
  ck3_12002::ArmyBindings query_bindings{};
  std::vector<game::ArmyStrengthSnapshot> whole_rows;
  bool rule_passed = true;
  std::uint32_t expected_root = kCharacter;
  std::int32_t construct_calls = 0, evaluate_calls = 0, destroy_calls = 0;
  void *current_context = nullptr;
  std::size_t expected_denied_attempts = 0;
  Fixture() {
    armies.Add(kArmy, army); memory.Put(armies.fallback_slot, 0, army);
    units.Add(kUnit, unit); memory.Put(units.fallback_slot, 0, fallback_unit);
    characters.Add(kCharacter, character, 0x18); memory.Put(characters.fallback_slot, 0, fallback_character);
    combats.Add(kCombat, combat, 8); memory.Put(combats.fallback_slot, 0, fallback_combat);
    memory.Put(army, 0x124, kUnit); memory.Put(army, 0x128, kCombat);
    memory.Put(army, 0x1D4, std::uint8_t{1}); memory.Put(army, 0x31, std::uint8_t{187});
    memory.Put(unit, 0x18, std::uint32_t{1}); memory.Put(unit, 0x174, kCharacter);
    memory.Put(combat, 0xC, std::uint32_t{0x436F6D62});
    memory.Put(fallback_combat, 8, std::uint32_t{0xFFFFFFFFU});
    memory.Put(fallback_combat, 0xC, std::uint32_t{0x436F6D62});
    memory.Put(provider_slot, 0, provider); memory.Put(provider, 0xEF0, rule_array);
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
    bindings.combat_registry_slot = combats.slot; bindings.combat_fallback_slot = combats.fallback_slot;
    bindings.rule_provider_slot = provider_slot;
    bindings.construct_actor_scope = Construct; bindings.destroy_scope = Destroy; bindings.evaluate_condition = Evaluate;
    query_bindings.enabled = true; query_bindings.game_state_slot = static_cast<void **>(state_slot);
    query_bindings.unit_storage_slot = static_cast<void **>(subject_units.slot);
    query_bindings.internal_army_storage_slot = static_cast<void **>(armies.slot);
    query_bindings.regiment_storage_slot = static_cast<void **>(arrgs.slot);
    query_bindings.get_army_current_soldiers = Current; query_bindings.get_army_maximum_soldiers = Maximum;
    query_bindings.current_daily_assault_roster_admission_bindings = common;
    auto &refresh = query_bindings.current_post_admission_refresh_bindings;
    refresh.common = common; refresh.arrg_registry_slot = arrgs.slot; refresh.arrg_fallback_slot = arrgs.fallback_slot;
    bindings.common.read_memory = Memory::Flag31Read;
  }
  void Ids(void *header, std::initializer_list<std::uint32_t> ids) {
    memory.Put(header, 8, static_cast<std::int32_t>(ids.size()));
    memory.Put(header, 0xC, static_cast<std::int32_t>(ids.size()));
    void *raw = ids.size() ? memory.Allocate(ids.size() * 4) : nullptr;
    std::size_t index = 0; for (auto id : ids) memory.Put(raw, index++ * 4, id);
    memory.Put(header, 0, raw);
  }
  void InactiveWrongMagic() { memory.Put(combat, 0xC, std::uint32_t{0xDEADBEEFU}); }
  game::ArmyCurrentFlag31InputsV1 Observe() {
    active = this; const auto before = memory.Snapshot();
    query_bindings.current_army_flag31_bindings = bindings;
    const std::array<ck3_12002::ArmyStrengthScope, 2> scopes{{
        {static_cast<std::int32_t>(kSubjectUnit), game::ArmyStrengthScopeRole::player, {}},
        {static_cast<std::int32_t>(kSubjectUnit), game::ArmyStrengthScopeRole::active_war_ally, {7}}}};
    Check(ck3_12002::ReadArmyStrengthsForScope(query_bindings, scopes, whole_rows) ==
              game::ReadArmyStrengthsResult::available && whole_rows.size() == 2,
          "flag31 requires genuine whole query source route");
    for (const auto &row : whole_rows) {
      Check(row.available && row.current_soldiers == 20 && row.maximum_soldiers == 40 &&
                row.regiment_count == 1 && row.ai_base_power_raw == std::int64_t{4000000},
            "flag31 optional partial must retain genuine independent current strength");
      Check(row.current_post_admission_refresh_inputs_v1 && row.current_army_flag31_inputs_v1,
            "flag31 must borrow genuine postadmission capture through actual Root hook");
    }
    Check(whole_rows[0].current_army_flag31_inputs_v1 == whole_rows[1].current_army_flag31_inputs_v1,
          "flag31 global collector should capture once for both requested scope rows");
    auto out = *whole_rows[0].current_army_flag31_inputs_v1;
    Check(before == memory.Snapshot(), "flag31 query wrote Army/world inputs");
    Check(memory.denied_attempts == expected_denied_attempts, "flag31 reads disagree with actual branch demand");
    Check(out.occurrences.size() == 2 && out.original_roster.occurrences.size() == 2,
          "flag31 filtered original duplicate roster occurrences");
    for (const auto &row : out.occurrences)
      Check(row.raw_full_id_u32 == kArmy && row.same_query_army_selection_matched &&
                row.actual_army_31_raw_u8 == std::uint8_t{187},
            "flag31 lost physical selection/fullDWORD or cached31 separation");
    Check(!out.actual_refresh_execution_ready && !out.actual_next_occurrence_ready && !out.full_callback_ready &&
              !out.full_daily_assault_ready && !out.full_monthly_ready,
          "flag31 may not raise future refresh or callback readiness");
    return out;
  }
};
std::int32_t Current(void *receiver, std::uint8_t flags) {
  Check(active && flags == std::uint8_t{0} &&
            receiver == static_cast<std::byte *>(active->subject_army) + 0x38,
        "flag31 whole current strength getter arguments changed"); return 20;
}
std::int32_t Maximum(void *receiver) {
  Check(active && receiver == active->subject_army, "flag31 whole maximum strength getter receiver changed"); return 40;
}
void *Construct(void *storage, const std::int32_t *id) {
  Check(active && storage && id && !active->current_context, "flag31 context construction receiver/ownership changed");
  const auto bits = std::bit_cast<std::uint32_t>(*id);
  Check(bits == active->expected_root, "flag31 constructor must receive selectedCharacter18 fullDWORD");
  ++active->construct_calls; active->current_context = storage;
  const std::uint16_t kind = 4, subtype = 0; const auto payload = static_cast<std::uint64_t>(bits);
  std::memcpy(storage, &kind, sizeof(kind));
  std::memcpy(static_cast<std::byte *>(storage) + 2, &subtype, sizeof(subtype));
  std::memcpy(static_cast<std::byte *>(storage) + 8, &payload, sizeof(payload));
  return storage;
}
void Destroy(void *storage) {
  Check(active && storage == active->current_context, "flag31 destructor must release its own ordinary context");
  ++active->destroy_calls; active->current_context = nullptr;
}
bool Evaluate(const void *receiver, void *context) {
  Check(active && receiver == static_cast<std::byte *>(active->rule_array) + 0x1380 &&
            context == active->current_context, "flag31 evaluator must use actual inline slot24 and constructed context");
  std::uint16_t kind = 0, subtype = 1; std::uint64_t payload = 0;
  std::memcpy(&kind, context, sizeof(kind));
  std::memcpy(&subtype, static_cast<std::byte *>(context) + 2, sizeof(subtype));
  std::memcpy(&payload, static_cast<std::byte *>(context) + 8, sizeof(payload));
  Check(kind == 4 && subtype == 0 && payload == active->expected_root,
        "flag31 actual ordinary context root fields/fullDWORD changed");
  ++active->evaluate_calls; return active->rule_passed;
}
void Ready(const Fixture &f, const game::ArmyCurrentFlag31InputsV1 &out, std::uint8_t value, bool evaluated) {
  Check(out.ready && out.current_flag31_inputs_ready && out.original_army_selections_ready,
        "flag31 independently observable current value did not become available");
  const std::int32_t expected_calls = evaluated ? 2 : 0;
  Check(f.construct_calls == expected_calls && f.evaluate_calls == expected_calls &&
            f.destroy_calls == expected_calls && !f.current_context,
        "flag31 context/evaluator demand or once-global lifecycle count changed");
  for (const auto &row : out.occurrences) {
    Check(row.ready && row.derived_current_31_raw_u8 == value &&
              row.native_rule_evaluation_returned == evaluated,
          "flag31 source/current verdict result changed");
    if (evaluated)
      Check(row.native_current_rule24_passed == f.rule_passed &&
                row.selected_character_18_raw_u32 == f.expected_root && row.root_kind == 4 &&
                row.root_subtype == 0 && row.root_payload_u64 == f.expected_root &&
                row.root_construction == "9F9E20_normal_return",
            "flag31 actual returned rule/context/root association lost");
    else Check(!row.native_current_rule24_passed && row.root_construction == "not_demanded",
               "flag31 source-zero fabricated native rule or context");
  }
}
void Partial(const Fixture &f, const game::ArmyCurrentFlag31InputsV1 &out) {
  Check(!out.ready && !out.current_flag31_inputs_ready && f.construct_calls == 0 &&
            f.evaluate_calls == 0 && f.destroy_calls == 0,
        "flag31 missing demanded input must not evaluate or become ready");
  for (const auto &row : out.occurrences)
    Check(!row.ready && !row.derived_current_31_raw_u8 && !row.native_current_rule24_passed &&
              !row.native_rule_evaluation_returned && !row.unavailable_reason.empty(),
          "flag31 missing demanded input became guessed nativefalse/currentzero");
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
} // namespace
int main(int argc, char **argv) {
  try {
    const auto bound = xar::ck3_12003::BindCurrentArmyFlag31Inputs12003(0x140000000ULL,
        "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6");
    Check(bound.common.enabled &&
              reinterpret_cast<std::uintptr_t>(bound.combat_registry_slot) == 0x145D1DE70ULL &&
              reinterpret_cast<std::uintptr_t>(bound.combat_fallback_slot) == 0x145D1DE18ULL &&
              reinterpret_cast<std::uintptr_t>(bound.rule_provider_slot) == 0x145D21DC8ULL &&
              reinterpret_cast<std::uintptr_t>(bound.construct_actor_scope) == 0x1409F9E20ULL &&
              reinterpret_cast<std::uintptr_t>(bound.destroy_scope) == 0x14087E0E0ULL &&
              reinterpret_cast<std::uintptr_t>(bound.evaluate_condition) == 0x14372DF30ULL,
          "flag31 exact .3 binder must select actual combat/slot24/context/evaluator");
    std::vector<std::pair<std::string, std::string>> samples;
    { Fixture f; f.memory.Put(f.army, 0x1D4, std::uint8_t{0});
      f.bindings.combat_registry_slot = nullptr; f.bindings.rule_provider_slot = nullptr;
      f.bindings.construct_actor_scope = nullptr; f.bindings.destroy_scope = nullptr; f.bindings.evaluate_condition = nullptr;
      f.memory.Deny(f.army, 0x128, 4); f.memory.Deny(f.army, 0x124, 4); f.memory.Deny(f.unit, 0x174, 4);
      const auto out = f.Observe(); Ready(f, out, std::uint8_t{0}, false);
      Check(!out.occurrences[0].source_active_combat && !out.occurrences[0].army_128_raw_u32 &&
                !out.occurrences[0].selected_character_18_raw_u32 && !out.occurrences[0].inline_rule_identity,
            "flag31 zero1D4 demanded combat/owner/slot24");
      samples.emplace_back("source-zero-1d4-undemanded", Serialize(f)); }
    { Fixture f; f.combats.Add(std::uint32_t{0}, f.combat, 8); f.memory.Put(f.army, 0x128, std::uint32_t{0});
      f.memory.Deny(f.army, 0x124, 4); f.memory.Deny(f.unit, 0x174, 4);
      f.bindings.construct_actor_scope = nullptr; f.bindings.destroy_scope = nullptr; f.bindings.evaluate_condition = nullptr;
      const auto out = f.Observe(); Ready(f, out, std::uint8_t{0}, false); const auto &row = out.occurrences[0];
      Check(row.army_128_raw_u32 == std::uint32_t{0} && row.source_active_combat == true &&
                row.selected_combat_full_id_08_raw_u32 == std::uint32_t{0} && !row.army_124_raw_u32,
            "flag31 actualCombat fullgen0 or owner bypass lost");
      samples.emplace_back("active-combat-fullgen0-undemanded", Serialize(f)); }
    { Fixture f; f.InactiveWrongMagic(); const auto out = f.Observe(); Ready(f, out, std::uint8_t{0}, true);
      const auto &row = out.occurrences[0];
      Check(row.source_active_combat == false && !row.selected_combat_full_id_08_raw_u32 &&
                row.unit_owner_174_raw_u32 == Fixture::kCharacter && row.rule_selector_i32 == 24 &&
                row.rule_inline_offset_u32 == std::uint32_t{0x1380},
            "flag31 wrongCombatmagic demands or slot24 changed");
      samples.emplace_back("inactive-combat-wrong-magic-rule24-true", Serialize(f)); }
    { Fixture f; f.memory.Put(f.combats.slot, 0, static_cast<void *>(nullptr)); f.memory.Deny(f.army, 0x128, 4);
      f.units.Add(std::uint32_t{0}, f.unit); f.characters.Add(std::uint32_t{0}, f.character, 0x18);
      f.memory.Put(f.army, 0x124, std::uint32_t{0}); f.memory.Put(f.unit, 0x174, std::uint32_t{0});
      f.rule_passed = false; f.expected_root = 0; const auto out = f.Observe(); Ready(f, out, std::uint8_t{1}, true);
      const auto &row = out.occurrences[0];
      Check(row.combat_resolution.registry_loaded == false && row.combat_resolution.used_fallback == true &&
                row.selected_combat_full_id_08_raw_u32 == std::uint32_t{0xFFFFFFFFU} &&
                !row.army_128_raw_u32 && row.army_124_raw_u32 == std::uint32_t{0} &&
                row.unit_owner_174_raw_u32 == std::uint32_t{0},
            "flag31 Combat sentinel/rawfullgen0 distinction changed");
      samples.emplace_back("inactive-combat-sentinel-rule24-false", Serialize(f)); }
    { Fixture f; f.memory.Put(f.combats.slot, 0, static_cast<void *>(nullptr));
      f.memory.Put(f.fallback_combat, 0xC, std::uint32_t{0xDEADBEEFU});
      f.memory.Put(f.units.slot, 0, static_cast<void *>(nullptr));
      f.memory.Put(f.characters.slot, 0, static_cast<void *>(nullptr));
      f.memory.Put(f.fallback_unit, 0x174, std::uint32_t{42});
      f.memory.Put(f.fallback_character, 0x18, std::uint32_t{0xFFFFFFFFU});
      f.memory.Deny(f.army, 0x128, 4); f.memory.Deny(f.army, 0x124, 4); f.memory.Deny(f.fallback_unit, 0x174, 4);
      f.rule_passed = false; f.expected_root = 0xFFFFFFFFU;
      const auto out = f.Observe(); Ready(f, out, std::uint8_t{1}, true); const auto &row = out.occurrences[0];
      Check(row.unit_resolution.registry_loaded == false && row.unit_resolution.used_fallback == true &&
                row.character_resolution.registry_loaded == false && row.character_resolution.used_fallback == true &&
                !row.army_124_raw_u32 && !row.unit_owner_174_raw_u32 && !row.army_128_raw_u32 &&
                row.selected_character_18_raw_u32 == std::uint32_t{0xFFFFFFFFU},
            "flag31 actual null-store fallback selectedCharacter18/rawsentinel root lost");
      samples.emplace_back("null-stores-character-fallback-sentinel-rule24-false", Serialize(f)); }
    { Fixture f; f.InactiveWrongMagic();
      f.memory.Put(f.character, 0x18, std::uint32_t{0xFE000042U});
      f.memory.Put(f.fallback_character, 0x18, std::uint32_t{0x80000000U});
      f.bindings.evaluate_condition = nullptr;
      const auto out = f.Observe(); Partial(f, out); const auto &row = out.occurrences[0];
      Check(row.character_resolution.used_fallback == true && row.selected_character_18_raw_u32 ==
                std::uint32_t{0x80000000U} && row.unit_owner_174_raw_u32 == Fixture::kCharacter &&
                !row.root_payload_u64 && row.root_construction == "not_demanded",
            "flag31 generation mismatch/root prefix or missing evaluator distinction changed");
      samples.emplace_back("missing-rule-evaluator-callable", Serialize(f)); }
    { Fixture f; f.memory.Deny(f.combat, 0xC, 4); f.expected_denied_attempts = 2;
      const auto out = f.Observe(); Partial(f, out); const auto &row = out.occurrences[0];
      Check(!row.selected_combat_magic_0c_raw_u32 && !row.source_active_combat &&
                !row.army_124_raw_u32 && !row.selected_character_18_raw_u32,
            "flag31 unknown Combat tag fabricated false or demanded owner");
      samples.emplace_back("missing-demanded-combat-magic", Serialize(f)); }
    if (argc == 3 && std::string_view(argv[1]) == "--wire-dir") {
      const std::filesystem::path directory(argv[2]); std::filesystem::create_directories(directory);
      std::ofstream file(directory / "ck3_12003_army_flag31_inputs_wire.json", std::ios::binary);
      file << "{\"samples\":{";
      for (std::size_t i = 0; i < samples.size(); ++i) {
        if (i) file << ',';
        file << '"' << samples[i].first << "\":" << samples[i].second;
      }
      file << "},\"qualification\":\"genuine whole ReadArmyStrengthsForScope+AppendArmyStrengthV1; seven scenes times two scopes and two repeated originalArmy occurrences; world and ordinary scope/evaluator callbacks synthetic; no baseline or field transplant; newcurrent31 only\"}\n";
      Check(static_cast<bool>(file), "flag31 fixture whole wire write failed");
    }
    std::cout << "NEW current31 seven wholequery samples passed; synthetic evaluator callbacks, no game execution\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 1; }
}
