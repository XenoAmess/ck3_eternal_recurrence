#include "xar_bridge/ck3_12003_army_condition30_inputs.hpp"
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"
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
  bool condition_reads = false;
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
    auto &m = *static_cast<Memory *>(context); auto begin = reinterpret_cast<std::uintptr_t>(address);
    for (const auto &range : m.denied) {
      const auto denied = reinterpret_cast<std::uintptr_t>(range.address);
      if (m.condition_reads && begin < denied + range.size && denied < begin + size) {
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
  static bool ConditionRead(void *context, const void *address, void *out, std::size_t size) noexcept {
    auto &m = *static_cast<Memory *>(context); m.condition_reads = true;
    const bool copied = Read(context, address, out, size); m.condition_reads = false; return copied;
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
void *Construct(void *, const std::int32_t *);
void Destroy(void *);
bool Evaluate(const void *, void *);
std::int32_t Current(void *, std::uint8_t);
std::int32_t Maximum(void *);
struct Fixture {
  static constexpr std::uint32_t kArmy = 0xAB000001U, kUnit = 0x88000001U;
  static constexpr std::uint32_t kSubjectUnit = 11, kSubjectArmy = 12, kSubjectArRg = 13;
  Memory memory;
  Registry armies{memory}, units{memory}, arrgs{memory}, subject_units{memory};
  void *army = memory.Allocate(0x200), *unit = memory.Allocate(0x180), *fallback_unit = memory.Allocate(0x180);
  void *condition_owner = memory.Allocate(0x180);
  void *state_slot = memory.Allocate(8), *state = memory.Allocate(0xA8);
  void *data = memory.Allocate(0x2A540 + 0x190), *manager = static_cast<std::byte *>(data) + 0x2A540;
  void *subject_unit = memory.Allocate(0x180), *subject_army = memory.Allocate(0x200);
  void *subject_arrg = memory.Allocate(0x150);
  ck3_12003::CurrentArmyCondition30Bindings12003 bindings{};
  ck3_12002::ArmyBindings query_bindings{};
  std::vector<game::ArmyStrengthSnapshot> whole_rows;
  std::uint32_t expected_owner = 29829;
  bool passed = true, null_context = false;
  std::int32_t constructed = 0, evaluated = 0, destroyed = 0;
  void *last_storage = nullptr, *last_context = nullptr;
  Fixture() {
    armies.Add(kArmy, army); memory.Put(armies.fallback_slot, 0, army);
    units.Add(kUnit, unit); memory.Put(units.fallback_slot, 0, fallback_unit);
    memory.Put(army, 0x124, kUnit); memory.Put(army, 0x1D4, std::uint8_t{1});
    memory.Put(army, 0x30, std::uint8_t{187}); memory.Put(army, 0x1D8, condition_owner);
    memory.Put(unit, 0x174, expected_owner); memory.Put(fallback_unit, 0x174, expected_owner);
    memory.Put(unit, 0x18, std::uint32_t{1}); // Existing roster admission exits before unrelated ArRg demand.
    armies.Add(kSubjectArmy, subject_army); subject_units.Add(kSubjectUnit, subject_unit); arrgs.Add(kSubjectArRg, subject_arrg);
    memory.Put(subject_unit, 0x178, kSubjectArmy); memory.Put(subject_army, 0x124, kSubjectUnit);
    memory.Put(subject_arrg, 0x14, std::uint32_t{0x41725267});
    memory.Put(subject_arrg, 0x38, std::int32_t{20}); memory.Put(subject_arrg, 0x3C, std::int32_t{40});
    memory.Put(subject_arrg, 0x40, std::int64_t{4000000});
    memory.Put(state_slot, 0, state); memory.Put(state, 0xA0, data);
    Ids(static_cast<std::byte *>(manager) + 0x50, {kArmy, kArmy});
    Ids(static_cast<std::byte *>(manager) + 0x68, {});
    Ids(static_cast<std::byte *>(army) + 0x38, {});
    Ids(static_cast<std::byte *>(subject_army) + 0x38, {kSubjectArRg});
    auto &common = bindings.common; common.enabled = true; common.game_state_slot = state_slot;
    common.army_registry_slot = armies.slot; common.army_fallback_slot = armies.fallback_slot;
    common.unit_registry_slot = units.slot; common.unit_fallback_slot = units.fallback_slot;
    common.read_memory = Memory::Read; common.read_context = &memory;
    bindings.construct_actor_scope = Construct; bindings.destroy_scope = Destroy; bindings.evaluate_condition = Evaluate;
    query_bindings.enabled = true; query_bindings.game_state_slot = static_cast<void **>(state_slot);
    // The fixture's independent subject storage keeps whole-strength available
    // while a global-roster condition scene exercises Unit-store-null fallback.
    query_bindings.unit_storage_slot = static_cast<void **>(subject_units.slot);
    query_bindings.internal_army_storage_slot = static_cast<void **>(armies.slot);
    query_bindings.regiment_storage_slot = static_cast<void **>(arrgs.slot);
    query_bindings.get_army_current_soldiers = Current; query_bindings.get_army_maximum_soldiers = Maximum;
    query_bindings.current_daily_assault_roster_admission_bindings = common;
    auto &refresh = query_bindings.current_post_admission_refresh_bindings;
    refresh.common = common; refresh.arrg_registry_slot = arrgs.slot; refresh.arrg_fallback_slot = arrgs.fallback_slot;
    // Only this new collector's callback enforces its branch-demand checks.
    // Other genuine query families may legitimately read the same fields.
    bindings.common.read_memory = Memory::ConditionRead;
  }
  void Ids(void *header, std::initializer_list<std::uint32_t> ids) {
    memory.Put(header, 8, static_cast<std::int32_t>(ids.size()));
    memory.Put(header, 0xC, static_cast<std::int32_t>(ids.size()));
    void *raw = ids.size() ? memory.Allocate(ids.size() * 4) : nullptr;
    std::size_t index = 0; for (auto id : ids) memory.Put(raw, index++ * 4, id);
    memory.Put(header, 0, raw);
  }
  void Owner(std::uint32_t id) {
    expected_owner = id; memory.Put(unit, 0x174, id); memory.Put(fallback_unit, 0x174, id);
  }
  game::ArmyCurrentCondition30InputsV1 Observe() {
    active = this; const auto before = memory.Snapshot();
    query_bindings.current_army_condition30_bindings = bindings;
    const std::array<ck3_12002::ArmyStrengthScope, 2> scopes{{
        {static_cast<std::int32_t>(kSubjectUnit), game::ArmyStrengthScopeRole::player, {}},
        {static_cast<std::int32_t>(kSubjectUnit), game::ArmyStrengthScopeRole::active_war_ally, {7}}}};
    Check(ck3_12002::ReadArmyStrengthsForScope(query_bindings, scopes, whole_rows) ==
              game::ReadArmyStrengthsResult::available && whole_rows.size() == 2,
          "condition30 requires genuine whole ReadArmyStrengthsForScope path");
    for (const auto &row : whole_rows) {
      Check(row.available && row.current_soldiers == 20 && row.maximum_soldiers == 40 &&
                row.regiment_count == 1 && row.ai_base_power_raw == 4000000,
            "condition30 optional family changed independent whole subject strength");
      Check(row.current_post_admission_refresh_inputs_v1 && row.current_army_condition30_inputs_v1,
            "condition30 wholequery must capture genuine postadmission source and new family hooks");
    }
    Check(whole_rows[0].current_army_condition30_inputs_v1 == whole_rows[1].current_army_condition30_inputs_v1,
          "condition30 global collector must run once and reuse on both query scope rows");
    auto out = *whole_rows[0].current_army_condition30_inputs_v1;
    Check(before == memory.Snapshot(), "condition30 must not write Army/Unit/world inputs");
    Check(memory.denied_attempts == 0, "condition30 read an undemanded source operand");
    Check(out.occurrences.size() == 2 && out.original_roster.occurrences.size() == 2,
          "condition30 must preserve both original repeated occurrences");
    Check(out.occurrences[0].raw_full_id_u32 == kArmy && out.occurrences[1].raw_full_id_u32 == kArmy &&
              out.occurrences[0].original_army_resolution.object_identity == out.occurrences[1].original_army_resolution.object_identity,
          "condition30 duplicate physical Army association changed");
    for (const auto &row : out.occurrences) {
      Check(row.same_query_army_selection_matched && row.actual_army_30_raw_u8 == 187,
            "condition30 lost recorded selectedArmy/cache separation");
    }
    Check(!out.actual_refresh_execution_ready && !out.actual_next_occurrence_ready && !out.full_callback_ready &&
              !out.full_daily_assault_ready && !out.full_monthly_ready,
          "condition30 may not raise refresh/fullcallback readiness");
    Check(constructed == destroyed, "condition30 context construction/destruction are unpaired");
    return out;
  }
};
std::int32_t Current(void *receiver, std::uint8_t flags) {
  Check(active && flags == 0 && receiver == static_cast<std::byte *>(active->subject_army) + 0x38,
        "condition30 whole current getter subject/flags changed"); return 20;
}
std::int32_t Maximum(void *receiver) {
  Check(active && receiver == active->subject_army, "condition30 whole maximum getter subject changed"); return 40;
}
void *Construct(void *storage, const std::int32_t *id) {
  Check(active && std::bit_cast<std::uint32_t>(*id) == active->expected_owner,
        "condition30 constructor argument changed complete ownerDWORD bits");
  ++active->constructed; active->last_storage = storage;
  // Offset returned context intentionally differs from allocation base.
  auto *context = static_cast<std::byte *>(storage) + 0x20; active->last_context = context;
  const std::uint16_t kind = 4, subtype = 0; const std::uint64_t payload = active->expected_owner;
  std::memcpy(context, &kind, 2); std::memcpy(context + 2, &subtype, 2); std::memcpy(context + 8, &payload, 8);
  return active->null_context ? nullptr : context;
}
void Destroy(void *storage) {
  Check(active && storage == active->last_storage, "condition30 destroy must receive owning storage, not returned context");
  ++active->destroyed;
}
bool Evaluate(const void *condition, void *context) {
  Check(active && condition == static_cast<std::byte *>(active->condition_owner) + 0x160 &&
            context == active->last_context,
        "condition30 evaluator receiver/actual returned context changed");
  std::uint16_t kind = 0, subtype = 1; std::uint64_t payload = 0;
  std::memcpy(&kind, context, 2); std::memcpy(&subtype, static_cast<std::byte *>(context) + 2, 2);
  std::memcpy(&payload, static_cast<std::byte *>(context) + 8, 8);
  Check(kind == 4 && subtype == 0 && payload == active->expected_owner,
        "condition30 kind4 root must zeroextend complete ownerDWORD");
  ++active->evaluated; return active->passed;
}
void Ready(const Fixture &f, const game::ArmyCurrentCondition30InputsV1 &out, std::uint8_t value, bool demanded) {
  Check(out.ready && out.current_condition_30_inputs_ready && out.original_army_selections_ready,
        "condition30 available demanded branch did not become ready");
  Check(f.evaluated == (demanded ? 2 : 0), "condition30 evaluate demand/count disagrees");
  for (const auto &row : out.occurrences) {
    Check(row.ready && row.derived_current_30_raw_u8 == value, "condition30 actual bool inverse changed");
    if (demanded) Check(row.root_payload_u64 == f.expected_owner && row.native_current_condition_passed == f.passed,
                       "condition30 root/verdict provenance changed");
    else Check(!row.native_current_condition_passed && !row.root_payload_u64 && !row.unit_owner_174_raw_u32,
               "condition30 zero branch demanded root/evaluation");
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
    const auto bound = xar::ck3_12003::BindCurrentArmyCondition30Inputs12003(0x140000000ULL,
        "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6");
    Check(bound.common.enabled && reinterpret_cast<std::uintptr_t>(bound.construct_actor_scope) == 0x1409F9E20ULL &&
              reinterpret_cast<std::uintptr_t>(bound.destroy_scope) == 0x14087E0E0ULL &&
              reinterpret_cast<std::uintptr_t>(bound.evaluate_condition) == 0x14372DF30ULL,
          "condition30 exact .3 bindings changed");
    std::vector<std::pair<std::string, std::string>> samples;
    { Fixture f; f.memory.Put(f.army, 0x1D4, std::uint8_t{0});
      f.memory.Deny(f.army, 0x124, 4); f.memory.Deny(f.army, 0x1D8, 8);
      f.bindings.construct_actor_scope = nullptr; f.bindings.destroy_scope = nullptr; f.bindings.evaluate_condition = nullptr;
      auto out = f.Observe(); Ready(f, out, 0, false); samples.emplace_back("zero-1d4-undemanded", Serialize(f)); }
    { Fixture f; auto out = f.Observe(); Ready(f, out, 0, true); samples.emplace_back("native-true-returned-context-repeats", Serialize(f)); }
    { Fixture f; f.passed = false; f.Owner(0xFFFFFFFFU); auto out = f.Observe(); Ready(f, out, 1, true);
      samples.emplace_back("native-false-invalid-root-is-verdict", Serialize(f)); }
    { Fixture f; f.Owner(0xFE000022U); auto out = f.Observe(); Ready(f, out, 0, true); samples.emplace_back("high-bit-owner-zeroextends", Serialize(f)); }
    { Fixture f; f.Owner(0); f.units.Add(0, f.unit); f.memory.Put(f.army, 0x124, std::uint32_t{0});
      auto out = f.Observe(); Ready(f, out, 0, true); samples.emplace_back("zero-full-unit-and-owner", Serialize(f)); }
    { Fixture f; f.passed = false; f.Owner(424242); f.memory.Put(f.army, 0x124, std::uint32_t{0xA9000001U});
      f.memory.Deny(f.fallback_unit, 0x10, 4); auto out = f.Observe(); Ready(f, out, 1, true);
      Check(out.occurrences[0].unit_resolution.used_fallback == true, "condition30 wrong Unit generation must use nativefallback");
      samples.emplace_back("unit-generation-fallback", Serialize(f)); }
    { Fixture f; f.memory.Put(f.units.slot, 0, static_cast<void *>(nullptr)); f.memory.Deny(f.army, 0x124, 4);
      f.memory.Deny(f.fallback_unit, 0x10, 4); auto out = f.Observe(); Ready(f, out, 0, true);
      Check(!out.occurrences[0].army_124_raw_u32 && out.occurrences[0].unit_resolution.registry_loaded == false,
            "condition30 store-null must not request Army124"); samples.emplace_back("unit-store-null-fallback", Serialize(f)); }
    { Fixture f; f.memory.Put(f.army, 0x1D8, static_cast<void *>(nullptr)); auto out = f.Observe();
      Check(!out.ready && f.constructed == 0 && f.evaluated == 0 && !out.occurrences[0].native_current_condition_passed &&
                !out.occurrences[0].derived_current_30_raw_u8,
            "condition30 missing receiver cannot be a false predicate"); samples.emplace_back("missing-condition-receiver", Serialize(f)); }
    { Fixture f; f.null_context = true; auto out = f.Observe();
      Check(!out.ready && f.constructed == 2 && f.destroyed == 2 && f.evaluated == 0 &&
                !out.occurrences[0].derived_current_30_raw_u8,
            "condition30 null returned context must release owned scope and preserve unknown");
      samples.emplace_back("constructor-null-return-paired-destroy", Serialize(f)); }
    if (argc == 3 && std::string_view(argv[1]) == "--wire-dir") {
      const std::filesystem::path directory(argv[2]); std::filesystem::create_directories(directory);
      std::ofstream file(directory / "ck3_12003_army_condition30_inputs_wire.json", std::ios::binary);
      file << "{\"samples\":{";
      for (std::size_t i = 0; i < samples.size(); ++i) {
        if (i) file << ',';
        file << '"' << samples[i].first << "\":" << samples[i].second;
      }
      file << "},\"qualification\":\"genuine whole ReadArmyStrengthsForScope plus AppendArmyStrengthV1 outputs; fixture world/context/predicate callbacks synthetic; no field transplant\"}\n";
      Check(static_cast<bool>(file), "condition30 fixture wire write failed");
    }
    std::cout << "NEW condition30 nine samples passed; no native/game action executed\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 1; }
}
