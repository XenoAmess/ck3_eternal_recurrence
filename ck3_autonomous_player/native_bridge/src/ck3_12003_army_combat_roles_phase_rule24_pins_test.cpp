#include "xar_bridge/ck3_12003_army_combat_roles_phase_inputs.hpp"
#include "xar_bridge/ck3_12003_army_rule24_source_pins.hpp"
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
  struct Range { const void *address; std::size_t size; };
  std::vector<Region> regions;
  std::vector<Range> denied, pins;
  bool observer_reads = false;
  std::uint32_t pin_requested_bytes = 0, pin_captured_bytes = 0;
  std::size_t denied_attempts = 0;
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
  void Pin(const void *object, std::size_t offset, std::size_t size) {
    pins.push_back({static_cast<const std::byte *>(object) + offset, size});
  }
  std::vector<std::vector<std::byte>> Snapshot() const {
    std::vector<std::vector<std::byte>> out;
    for (const auto &region : regions) out.emplace_back(region.bytes.get(), region.bytes.get() + region.size);
    return out;
  }
  static bool Read(void *context, const void *address, void *out, std::size_t size) noexcept {
    auto &m = *static_cast<Memory *>(context); const auto begin = reinterpret_cast<std::uintptr_t>(address);
    bool pin = false;
    if (m.observer_reads) {
      for (const auto &range : m.pins) if (address == range.address && size == range.size) pin = true;
      if (pin) m.pin_requested_bytes += static_cast<std::uint32_t>(size);
      for (const auto &range : m.denied) {
        const auto denied_begin = reinterpret_cast<std::uintptr_t>(range.address);
        if (begin < denied_begin + range.size && denied_begin < begin + size) { ++m.denied_attempts; return false; }
      }
    }
    for (const auto &region : m.regions) {
      const auto region_begin = reinterpret_cast<std::uintptr_t>(region.bytes.get());
      if (begin >= region_begin && begin - region_begin <= region.size && size <= region.size - (begin - region_begin)) {
        std::memcpy(out, address, size);
        if (pin) m.pin_captured_bytes += static_cast<std::uint32_t>(size);
        return true;
      }
    }
    return false;
  }
  static bool ObserverRead(void *context, const void *address, void *out, std::size_t size) noexcept {
    auto &m = *static_cast<Memory *>(context); m.observer_reads = true;
    const bool copied = Read(context, address, out, size); m.observer_reads = false; return copied;
  }
};
struct Registry {
  Memory &memory; void *slot, *fallback_slot, *store, *rows;
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
  static constexpr std::uintptr_t kModule = 0x140000000ULL;
  static constexpr std::uint32_t kArmy = 0xAB000001U, kUnit = 0x88000001U;
  static constexpr std::uint32_t kCharacter = 0xFE000002U, kCombat = 0xD1000003U;
  static constexpr std::uint32_t kOtherArmy = 0xE7000004U, kFallbackArmy = 0xCD000006U;
  static constexpr std::uint32_t kSubjectUnit = 11, kSubjectArmy = 12, kSubjectArRg = 13;
  Memory memory;
  Registry armies{memory}, units{memory}, characters{memory}, combats{memory}, arrgs{memory}, subject_units{memory};
  void *army = memory.Allocate(0x200), *fallback_army = memory.Allocate(0x200);
  void *unit = memory.Allocate(0x180), *character = memory.Allocate(0x200), *fallback_character = memory.Allocate(0x200);
  void *combat = memory.Allocate(0x720), *fallback_combat = memory.Allocate(0x720);
  void *provider_slot = memory.Allocate(8), *provider = memory.Allocate(0xF00);
  void *rule_array = memory.Allocate(0x1380 + 0xD0), *rule_vtable = memory.Allocate(0xD0), *mode_slot = memory.Allocate(1);
  void *state_slot = memory.Allocate(8), *state = memory.Allocate(0xA8), *domain = memory.Allocate(0x2E9D0 + 0x190);
  void *army_manager = static_cast<std::byte *>(domain) + 0x2A540;
  void *combat_manager = static_cast<std::byte *>(domain) + 0x2E9D0;
  void *threshold_slot = memory.Allocate(4);
  void *subject_unit = memory.Allocate(0x180), *subject_army = memory.Allocate(0x200), *subject_arrg = memory.Allocate(0x150);
  ck3_12003::CurrentArmyFlag31Bindings12003 flag31{};
  ck3_12003::CurrentArmyCombatRolesPhaseBindings12003 roles{};
  ck3_12002::ArmyBindings query{};
  std::vector<game::ArmyStrengthSnapshot> whole_rows;
  bool rule_passed = false, expected_combat_ready = true, expect_rule = false;
  std::uint32_t expected_root = kCharacter, expected_pins_captured = 33;
  std::int32_t construct_calls = 0, evaluate_calls = 0, destroy_calls = 0;
  std::size_t expected_denied_attempts = 0;
  void *current_context = nullptr;
  Fixture() {
    armies.Add(kArmy, army); memory.Put(armies.fallback_slot, 0, fallback_army);
    memory.Put(fallback_army, 0x10, kFallbackArmy);
    units.Add(kUnit, unit); memory.Put(units.fallback_slot, 0, unit);
    characters.Add(kCharacter, character, 0x18); memory.Put(characters.fallback_slot, 0, fallback_character);
    memory.Put(fallback_character, 0x18, std::uint32_t{0x80000000U});
    combats.Add(kCombat, combat, 8); memory.Put(combats.fallback_slot, 0, fallback_combat);
    for (auto *selected : {army, fallback_army}) {
      memory.Put(selected, 0x124, kUnit); memory.Put(selected, 0x128, kCombat);
      memory.Put(selected, 0x31, std::uint8_t{187}); memory.Put(selected, 0x1D4, std::uint8_t{0});
      OrdinaryIds(static_cast<std::byte *>(selected) + 0x38, {});
    }
    memory.Put(unit, 0x18, std::uint32_t{1}); memory.Put(unit, 0x174, kCharacter);
    memory.Put(combat, 0xC, std::uint32_t{0x436F6D62});
    memory.Put(fallback_combat, 8, std::uint32_t{0xFFFFFFFFU});
    memory.Put(fallback_combat, 0xC, std::uint32_t{0x436F6D62});
    memory.Put(provider_slot, 0, provider); memory.Put(provider, 0xEF0, rule_array);
    memory.Put(rule_array, 0x1380, rule_vtable);
    memory.Put(rule_vtable, 0x58, reinterpret_cast<const void *>(kModule + 0x1110));
    memory.Put(rule_vtable, 0x60, static_cast<const void *>(nullptr));
    memory.Put(rule_vtable, 0xC8, reinterpret_cast<const void *>(kModule + 0x2220));
    memory.Put(mode_slot, 0, std::uint8_t{0});
    memory.Pin(mode_slot, 0, 1); memory.Pin(rule_array, 0x1380, 8);
    memory.Pin(rule_vtable, 0x58, 8); memory.Pin(rule_vtable, 0x60, 8); memory.Pin(rule_vtable, 0xC8, 8);
    memory.Put(state_slot, 0, state); memory.Put(state, 0xA0, domain);
    OrdinaryIds(static_cast<std::byte *>(army_manager) + 0x50, {kArmy, kArmy});
    OrdinaryIds(static_cast<std::byte *>(army_manager) + 0x68, {});
    memory.Put(combat_manager, 8, reinterpret_cast<const void *>(kModule + 0x477F178));
    CombatIds(combat_manager, 0x28, 0x30, 0x34, {kCombat}, 4);
    ConfigureSides({kArmy}, {});
    memory.Put(combat, 0x6B0, std::int32_t{1}); memory.Put(combat, 0x6B4, std::int32_t{4});
    memory.Put(combat, 0x700, std::int32_t{-1}); memory.Put(combat, 0x704, std::uint8_t{0});
    memory.Put(combat, 0x705, std::uint8_t{0}); memory.Put(threshold_slot, 0, std::int32_t{3});
    armies.Add(kSubjectArmy, subject_army); subject_units.Add(kSubjectUnit, subject_unit); arrgs.Add(kSubjectArRg, subject_arrg);
    memory.Put(subject_unit, 0x178, kSubjectArmy); memory.Put(subject_army, 0x124, kSubjectUnit);
    memory.Put(subject_arrg, 0x14, std::uint32_t{0x41725267});
    memory.Put(subject_arrg, 0x38, std::int32_t{20}); memory.Put(subject_arrg, 0x3C, std::int32_t{40});
    memory.Put(subject_arrg, 0x40, std::int64_t{4000000});
    OrdinaryIds(static_cast<std::byte *>(subject_army) + 0x38, {kSubjectArRg});
    auto &common = flag31.common; common.enabled = true; common.game_state_slot = state_slot;
    common.army_registry_slot = armies.slot; common.army_fallback_slot = armies.fallback_slot;
    common.unit_registry_slot = units.slot; common.unit_fallback_slot = units.fallback_slot;
    common.character_registry_slot = characters.slot; common.character_fallback_slot = characters.fallback_slot;
    common.read_memory = Memory::Read; common.read_context = &memory;
    flag31.combat_registry_slot = combats.slot; flag31.combat_fallback_slot = combats.fallback_slot;
    flag31.rule_provider_slot = provider_slot; flag31.construct_actor_scope = Construct;
    flag31.destroy_scope = Destroy; flag31.evaluate_condition = Evaluate;
    flag31.rule_source_mode_slot = mode_slot; flag31.rule_source_module_base = kModule;
    flag31.rule_source_image_size = 102518784;
    roles.common = common; roles.common.read_memory = Memory::ObserverRead;
    roles.combat_registry_slot = combats.slot; roles.combat_fallback_slot = combats.fallback_slot;
    roles.expected_secondary_vtable = reinterpret_cast<const void *>(kModule + 0x477F178);
    roles.maneuver_threshold_slot = threshold_slot;
    query.enabled = true; query.game_state_slot = static_cast<void **>(state_slot);
    query.unit_storage_slot = static_cast<void **>(subject_units.slot);
    query.internal_army_storage_slot = static_cast<void **>(armies.slot);
    query.regiment_storage_slot = static_cast<void **>(arrgs.slot);
    query.get_army_current_soldiers = Current; query.get_army_maximum_soldiers = Maximum;
    query.current_daily_assault_roster_admission_bindings = common;
    query.current_post_admission_refresh_bindings.common = common;
    query.current_post_admission_refresh_bindings.arrg_registry_slot = arrgs.slot;
    query.current_post_admission_refresh_bindings.arrg_fallback_slot = arrgs.fallback_slot;
    flag31.common.read_memory = Memory::ObserverRead;
  }
  void OrdinaryIds(void *header, std::initializer_list<std::uint32_t> ids) {
    memory.Put(header, 8, static_cast<std::int32_t>(ids.size())); memory.Put(header, 0xC, static_cast<std::int32_t>(ids.size()));
    void *raw = ids.size() ? memory.Allocate(ids.size() * 4) : nullptr;
    std::size_t i = 0; for (auto id : ids) memory.Put(raw, i++ * 4, id); memory.Put(header, 0, raw);
  }
  void CombatIds(void *object, std::size_t data_offset, std::size_t capacity_offset, std::size_t count_offset,
      std::initializer_list<std::uint32_t> ids, std::uint32_t capacity = 0) {
    void *raw = ids.size() ? memory.Allocate(ids.size() * 4) : nullptr;
    std::size_t i = 0; for (auto id : ids) memory.Put(raw, i++ * 4, id);
    memory.Put(object, data_offset, raw);
    memory.Put(object, capacity_offset, capacity ? capacity : static_cast<std::uint32_t>(ids.size()));
    memory.Put(object, count_offset, static_cast<std::int32_t>(ids.size()));
  }
  void ConfigureSides(std::initializer_list<std::uint32_t> attacker, std::initializer_list<std::uint32_t> defender) {
    const auto a = static_cast<std::byte *>(combat) + 0x20, d = static_cast<std::byte *>(combat) + 0x368;
    CombatIds(a, 0x10, 0x18, 0x1C, attacker); CombatIds(d, 0x10, 0x18, 0x1C, defender);
    memory.Put(a, 0xB8, combat); memory.Put(d, 0xB8, combat);
    memory.Put(a, 0x70, expected_root); memory.Put(d, 0x70, std::uint32_t{0xFFFFFFFFU});
    memory.Put(a, 0x74, std::uint32_t{0}); memory.Put(d, 0x74, std::uint32_t{0x99000005U});
  }
  void AbsentRule(bool passed, std::uint8_t mode) {
    expect_rule = true; rule_passed = passed;
    memory.Put(army, 0x1D4, std::uint8_t{1}); memory.Put(combat, 0xC, std::uint32_t{0xDEADBEEF});
    memory.Put(mode_slot, 0, mode);
    memory.Deny(combat, 0x6B0, 4); memory.Deny(combat_manager, 0x34, 4);
    memory.Deny(static_cast<std::byte *>(combat) + 0x20, 0x1C, 4);
  }
  const game::ArmyCurrentCombatRolesPhaseInputsV1 &Observe() {
    active = this; const auto before = memory.Snapshot();
    query.current_army_flag31_bindings = flag31;
    query.current_army_combat_roles_phase_bindings = roles;
    const std::array<ck3_12002::ArmyStrengthScope, 2> scopes{{
        {static_cast<std::int32_t>(kSubjectUnit), game::ArmyStrengthScopeRole::player, {}},
        {static_cast<std::int32_t>(kSubjectUnit), game::ArmyStrengthScopeRole::active_war_ally, {7}}}};
    Check(ck3_12002::ReadArmyStrengthsForScope(query, scopes, whole_rows) == game::ReadArmyStrengthsResult::available && whole_rows.size() == 2,
        "new observers require the genuine whole query route");
    for (const auto &row : whole_rows)
      Check(row.available && row.current_soldiers == 20 && row.maximum_soldiers == 40 && row.regiment_count == 1 &&
          row.ai_base_power_raw == std::int64_t{4000000} && row.current_post_admission_refresh_inputs_v1 &&
          row.current_army_flag31_inputs_v1 && row.current_army_combat_roles_phase_inputs_v1,
          "optional observer inputs must preserve genuine independent baseline strength");
    Check(whole_rows[0].current_army_combat_roles_phase_inputs_v1 == whole_rows[1].current_army_combat_roles_phase_inputs_v1 &&
        whole_rows[0].current_army_flag31_inputs_v1 == whole_rows[1].current_army_flag31_inputs_v1,
        "global observations must be copied once across both requested scopes");
    Check(before == memory.Snapshot(), "new read-only observers wrote fake world memory");
    Check(memory.denied_attempts == expected_denied_attempts, "new observer demanded an absent branch input");
    Check(memory.pin_requested_bytes == (expect_rule ? std::uint32_t{33} : std::uint32_t{0}) &&
        memory.pin_captured_bytes == (expect_rule ? expected_pins_captured : std::uint32_t{0}),
        "actual receiver capsule must capture at most33 bytes once per query including partial results");
    const auto &out = *whole_rows[0].current_army_combat_roles_phase_inputs_v1;
    Check(out.current_combat_roles_phase_inputs_ready == expected_combat_ready && out.occurrences.size() == 2 &&
        out.original_roster.occurrences.size() == 2 && out.original_army_selections_ready,
        "Combat family readiness or original duplicate occurrences changed");
    Check(!out.actual_manager_invocation_observed && !out.future_phase_transition_ready && !out.full_callback_ready &&
        !out.full_battle_ready && out.native_calls_executed == std::uint32_t{0} && out.native_writes_executed == std::uint32_t{0},
        "raw current observation cannot credit manager invocation or future phase execution");
    const auto &current31 = *whole_rows[0].current_army_flag31_inputs_v1;
    Check(current31.current_flag31_inputs_ready && current31.occurrences.size() == 2,
        "source pins partial must retain actual current31 verdict readiness");
    const std::int32_t calls = expect_rule ? 2 : 0;
    Check(construct_calls == calls && evaluate_calls == calls && destroy_calls == calls && !current_context,
        "actual ordinary scope/evaluator lifecycle demand changed");
    for (std::size_t i = 0; i < out.occurrences.size(); ++i) {
      const auto &role = out.occurrences[i]; const auto &rule = current31.occurrences[i];
      Check(role.raw_full_id_u32 == kArmy && role.same_query_army_selection_matched &&
          role.current_combat_roles_phase_inputs_ready == expected_combat_ready &&
          rule.derived_current_31_raw_u8 == static_cast<std::uint8_t>(expect_rule && !rule_passed ? 1 : 0),
          "fullDWORD/raw occurrence or actual current31 result was replaced");
      Check(rule.rule24_source_pins_v1.has_value() == expect_rule, "capsule must exist only after the actual receiver is reached");
      if (expect_rule) {
        const auto &pins = *rule.rule24_source_pins_v1;
        Check(pins.pin_requested_bytes_u32 == std::uint32_t{33} && pins.pin_captured_bytes_u32 == expected_pins_captured &&
            pins.pins_captured_ready == (expected_pins_captured == std::uint32_t{33}) &&
            pins.native_calls_executed == std::uint32_t{0} && pins.native_writes_executed == std::uint32_t{0},
            "pin inventory bytes/readiness cannot credit function calls");
        Check(role.source_active_combat == false && !role.actual_army_10_raw_u32 && !role.phase_6b0_raw_i32 &&
            !out.combat_manager.manager_identity, "inactive Combat must not demand current owner, manager or phase");
      } else Check(role.source_active_combat == true && role.active_combat_inputs_ready && rule.army_1d4_raw_u8 == std::uint8_t{0},
          "Combat collector must observe active inputs independently of source-zero current31");
    }
    if (expect_rule) Check(current31.occurrences[0].rule24_source_pins_v1 == current31.occurrences[1].rule24_source_pins_v1,
        "duplicate receiver must reuse the owned capsule including partial reads");
    return out;
  }
};
std::int32_t Current(void *receiver, std::uint8_t flags) {
  Check(active && flags == std::uint8_t{0} && receiver == static_cast<std::byte *>(active->subject_army) + 0x38,
      "whole current strength callback arguments changed"); return 20;
}
std::int32_t Maximum(void *receiver) {
  Check(active && receiver == active->subject_army, "whole maximum strength callback receiver changed"); return 40;
}
void *Construct(void *storage, const std::int32_t *id) {
  Check(active && storage && id && !active->current_context, "ordinary scope construction ownership changed");
  const auto bits = std::bit_cast<std::uint32_t>(*id);
  Check(bits == active->expected_root, "ordinary scope must use selectedCharacter18 fullDWORD");
  ++active->construct_calls; active->current_context = storage;
  const std::uint16_t kind = 4, subtype = 0; const auto payload = static_cast<std::uint64_t>(bits);
  std::memcpy(storage, &kind, sizeof(kind)); std::memcpy(static_cast<std::byte *>(storage) + 2, &subtype, sizeof(subtype));
  std::memcpy(static_cast<std::byte *>(storage) + 8, &payload, sizeof(payload)); return storage;
}
void Destroy(void *storage) {
  Check(active && storage == active->current_context, "ordinary scope destructor receiver changed");
  ++active->destroy_calls; active->current_context = nullptr;
}
bool Evaluate(const void *receiver, void *context) {
  Check(active && receiver == static_cast<std::byte *>(active->rule_array) + 0x1380 && context == active->current_context,
      "actual rule24 evaluator receiver/root changed");
  std::uint16_t kind = 0, subtype = 1; std::uint64_t payload = 0;
  std::memcpy(&kind, context, sizeof(kind)); std::memcpy(&subtype, static_cast<std::byte *>(context) + 2, sizeof(subtype));
  std::memcpy(&payload, static_cast<std::byte *>(context) + 8, sizeof(payload));
  Check(kind == 4 && subtype == 0 && payload == active->expected_root, "actual evaluator scope payload was guessed");
  ++active->evaluate_calls; return active->rule_passed;
}
std::string Serialize(const Fixture &f) {
  std::string out;
  game::AppendArmyStrengthV1(out, f.whole_rows[0], [](auto value) { return std::to_string(value); },
      [](std::string &text, const std::vector<std::int32_t> &values) {
        text += '['; for (std::size_t i = 0; i < values.size(); ++i) { if (i) text += ','; text += std::to_string(values[i]); } text += ']';
      }, [](std::string &text, std::string_view value) { text += '"'; text += value; text += '"'; });
  return out;
}
} // namespace
int main(int argc, char **argv) {
  try {
    const auto bound = ck3_12003::BindCurrentArmyCombatRolesPhaseInputs12003(Fixture::kModule,
        "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6");
    Check(bound.common.enabled && reinterpret_cast<std::uintptr_t>(bound.combat_registry_slot) == 0x145D1DE70ULL &&
        reinterpret_cast<std::uintptr_t>(bound.combat_fallback_slot) == 0x145D1DE18ULL &&
        reinterpret_cast<std::uintptr_t>(bound.expected_secondary_vtable) == 0x14477F178ULL &&
        reinterpret_cast<std::uintptr_t>(bound.maneuver_threshold_slot) == 0x145C69BB0ULL,
        "exact .3 current Combat raw binder offsets changed");
    const std::array<std::string_view, 14> names{{
      "absent-combat-rule24-pins-available-mode0", "absent-combat-rule24-pins-available-mode4-external-target",
      "absent-combat-rule24-missing-c8-pin", "absent-combat-rule24-missing-mode", "active-highbit-attacker-main",
      "active-fullid-zero-defender-pursuit", "active-selected-army-fallback-neither", "active-both-memberships-manager-duplicates-done",
      "phase0-below-threshold", "phase0-above-threshold", "phase0-forced-threshold-undemanded", "phase0-day-wrap",
      "missing-demanded-phase", "missing-demanded-side-roster"}};
    std::vector<std::pair<std::string, std::string>> samples;
    for (std::size_t scene = 0; scene < names.size(); ++scene) {
      Fixture f;
      if (scene < 4) {
        f.AbsentRule(scene == 1 || scene == 3, scene == 1 ? std::uint8_t{4} : std::uint8_t{0});
        if (scene == 1) f.memory.Put(f.rule_vtable, 0xC8, reinterpret_cast<const void *>(Fixture::kModule - 0x1000));
        if (scene == 2) { f.memory.Deny(f.rule_vtable, 0xC8, 8); f.expected_denied_attempts = 1; f.expected_pins_captured = 25; }
        if (scene == 3) { f.memory.Deny(f.mode_slot, 0, 1); f.expected_denied_attempts = 1; f.expected_pins_captured = 32; }
      }
      if (scene == 4) {
        f.memory.Put(f.character, 0x18, std::uint32_t{0xFE000042U});
        f.expected_root = 0x80000000U; f.ConfigureSides({Fixture::kArmy}, {});
      }
      if (scene == 5) {
        f.combats.Add(std::uint32_t{0}, f.combat, 8); f.memory.Put(f.army, 0x128, std::uint32_t{0});
        f.CombatIds(f.combat_manager, 0x28, 0x30, 0x34, {0}, 4);
        f.ConfigureSides({}, {Fixture::kArmy}); f.memory.Put(f.combat, 0x6B0, std::int32_t{2});
      }
      if (scene == 6) {
        f.memory.Put(f.army, 0x10, std::uint32_t{0xAB000099U});
        f.ConfigureSides({Fixture::kOtherArmy}, {Fixture::kOtherArmy});
      }
      if (scene == 7) {
        f.CombatIds(f.combat_manager, 0x28, 0x30, 0x34, {Fixture::kCombat, Fixture::kCombat}, 4);
        f.ConfigureSides({Fixture::kArmy, Fixture::kArmy, Fixture::kOtherArmy}, {Fixture::kArmy});
        f.memory.Put(f.combat, 0x6B0, std::int32_t{3}); f.memory.Put(f.combat, 0x704, std::uint8_t{1});
      }
      if (scene >= 8 && scene <= 11) {
        f.memory.Put(f.combat, 0x6B0, std::int32_t{0});
        f.memory.Put(f.combat, 0x6B4, scene == 8 ? std::int32_t{2} : scene == 11 ? std::int32_t{2147483647} : std::int32_t{3});
        if (scene == 10) { f.memory.Put(f.combat, 0x700, std::int32_t{0}); f.memory.Deny(f.threshold_slot, 0, 4); }
      }
      if (scene == 12) { f.memory.Deny(f.combat, 0x6B0, 4); f.expected_combat_ready = false; f.expected_denied_attempts = 2; }
      if (scene == 13) {
        f.memory.Deny(static_cast<std::byte *>(f.combat) + 0x368, 0x1C, 4);
        f.expected_combat_ready = false; f.expected_denied_attempts = 2;
      }
      const auto &out = f.Observe(); const auto &row = out.occurrences[0];
      if (scene >= 4) Check(out.combat_manager.roster.capacity_raw_u32 == std::uint32_t{4},
          "secondary receiver source offsets must preserve distinct capacity/count values");
      if (scene == 1) Check(f.whole_rows[0].current_army_flag31_inputs_v1->occurrences[0].rule24_source_pins_v1->
          rule_evaluator_function_identity.has_value() && !f.whole_rows[0].current_army_flag31_inputs_v1->occurrences[0].
          rule24_source_pins_v1->rule_evaluator_function_rva, "captured external evaluator target must retain identity and null RVA");
      if (scene == 4) Check(row.actual_army_10_raw_u32 == Fixture::kArmy && row.unit_owner_174_raw_u32 == Fixture::kCharacter &&
          row.character_resolution.used_fallback == true && row.selected_character_18_raw_u32 == std::uint32_t{0x80000000U} &&
          row.attacker_side.matching_army_indices == std::vector<std::int32_t>{0} && row.defender_side.matching_army_indices.empty(),
          "high-bit attacker owner raw174 vs selected18 fallback separation changed");
      if (scene == 5) Check(row.selected_combat_full_id_08_raw_u32 == std::uint32_t{0} && row.army_128_raw_u32 == std::uint32_t{0} &&
          row.attacker_side.matching_army_indices.empty() && row.defender_side.matching_army_indices == std::vector<std::int32_t>{0},
          "raw Combat fullID0 and genuine defender membership must remain legal");
      if (scene == 6) Check(row.original_army_resolution.used_fallback == true && row.actual_army_10_raw_u32 == Fixture::kFallbackArmy &&
          row.raw_full_id_u32 == Fixture::kArmy && row.attacker_side.matching_army_indices.empty() && row.defender_side.matching_army_indices.empty(),
          "fallback association must use actual selectedArmy10 and preserve neither membership");
      if (scene == 7) Check(row.manager_match_indices == std::vector<std::int32_t>({0, 1}) &&
          row.attacker_side.matching_army_indices == std::vector<std::int32_t>({0, 1}) &&
          row.defender_side.matching_army_indices == std::vector<std::int32_t>{0} && row.source_active_combat == true &&
          row.finalized_704_raw_u8 == std::uint8_t{1}, "both memberships/duplicate manager/done source-active distinction changed");
      if (scene >= 8 && scene <= 11) Check(row.threshold_required == (scene != 10) && row.threshold_inputs_ready &&
          row.maneuver_threshold_raw_i32.has_value() == (scene != 10), "phase0 forced winner must bypass loaded threshold");
      if (scene == 11) Check(row.day_6b4_raw_i32 == std::int32_t{2147483647}, "DWORD day wrap input must remain signed INTMAX");
      if (scene == 12) Check(!row.phase_inputs_ready && !row.phase_6b0_raw_i32, "missing demanded phase must remain unread partial");
      if (scene == 13) Check(!row.defender_side.armies.references_ready && !row.defender_side.armies.count_raw_i32,
          "missing demanded side roster must remain unread partial");
      samples.emplace_back(std::string(names[scene]), Serialize(f));
    }
    if (argc == 3 && std::string_view(argv[1]) == "--wire-dir") {
      const std::filesystem::path directory(argv[2]); std::filesystem::create_directories(directory);
      std::ofstream file(directory / "ck3_12003_army_combat_roles_phase_rule24_pins_wire.json", std::ios::binary);
      file << "{\"samples\":{";
      for (std::size_t i = 0; i < samples.size(); ++i) {
        if (i) file << ',';
        file << '"' << samples[i].first << "\":" << samples[i].second;
      }
      file << "},\"qualification\":\"genuine whole ReadArmyStrengthsForScope+AppendArmyStrengthV1; fourteen new scenes times two scopes and two repeated high-bit originalArmy occurrences; global capture once across scopes and receiver pins once/query; fake world/readmemory, ordinary scope/evaluator/getter callbacks and consumer Service frame synthetic; no whole row or leaf transplant; raw combat observer executes zero native calls/writes; no game execution\"}\n";
      Check(static_cast<bool>(file), "new combined whole wire write failed");
    }
    std::cout << "NEW current Combat roles/phase + Rule24 pins fourteen genuine wholequery scenes passed; synthetic callbacks, no game execution\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 1; }
}
