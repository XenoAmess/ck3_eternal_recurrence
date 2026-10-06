#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12003_pre_date_pending_update.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <initializer_list>
#include <iostream>
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
  std::vector<std::vector<std::byte>> Snapshot() const {
    std::vector<std::vector<std::byte>> out;
    for (const auto &region : regions)
      out.emplace_back(region.bytes.get(), region.bytes.get() + region.size);
    return out;
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
        store(m.Allocate(0x30)), table(m.Allocate(static_cast<std::size_t>(capacity) * 16)) {
    m.Put(slot, 0, store); m.Put(store, 0x20, table); m.Put(store, 0x2C, capacity);
  }
  void Add(std::uint32_t full, void *object, std::size_t full_offset) {
    memory.Put(table, static_cast<std::size_t>(full & 0xFFFFFFU) * 16 + 8, object);
    memory.Put(object, full_offset, full);
  }
};

constexpr std::uint32_t kInvalid = 0xFFFFFFFFU;
constexpr std::uint32_t kUnitA = 0x11000001U, kUnitScope = 0x11000002U;
constexpr std::uint32_t kArmyA = 0x22000001U, kArmyScope = 0x22000002U, kArmyFallback = 0x22000003U;
constexpr std::uint32_t kArmyWrongGeneration = 0x33000001U;
constexpr std::uint32_t kRegA = 0x2B000001U, kRegB = 0x2B000002U, kRegC = 0x2B000003U;
constexpr std::uint32_t kRegD = 0x2B000004U, kRegE = 0x2B000005U, kRegF = 0x2B000006U;
constexpr std::uint32_t kRegG = 0x2B000007U, kRegScope = 0x2B000008U, kRegFallback = 0x2B000009U;
constexpr std::uint32_t kRegWrongGeneration = 0x3C000001U, kCombat = 0x44000001U;
constexpr std::uint32_t kWarValid = 0x55000001U, kWarWrongMagic = 0x55000002U;
constexpr std::uint32_t kWarIndexed = 0x55000003U, kWarWrongGeneration = 0x99000003U;
constexpr std::uint32_t kContractFlag = 0x66000001U, kContractNormal = 0x66000002U;
constexpr std::uint32_t kPersistentD = 0x77000001U, kPersistentE = 0x77000002U;
constexpr std::uint32_t kPersistentF = 0x77000003U, kPersistentG = 0x77000004U;

std::uint32_t Hash(std::uint32_t key) {
  std::uint32_t hash = 0x811C9DC5U;
  for (std::uint32_t shift = 0; shift != 32; shift += 8)
    hash = (hash ^ ((key >> shift) & 0xFFU)) * 0x1000193U;
  return hash;
}

void *expected_scope_army = nullptr;
std::int32_t Current(void *receiver, std::uint8_t flags) {
  Check(flags == 0 && receiver == static_cast<std::byte *>(expected_scope_army) + 0x38,
        "pre-date fixture expected flags-zero whole-army current receiver");
  return 160;
}
std::int32_t Maximum(void *receiver) {
  Check(receiver == expected_scope_army, "pre-date fixture expected whole-army maximum receiver");
  return 240;
}

struct Fixture {
  Memory memory;
  Registry units{memory, 3}, armies{memory, 4}, arrgs{memory, 10};
  Registry combats{memory, 2}, contracts{memory, 3}, persistent{memory, 5}, wars{memory, 4};
  ck3_12002::ArmyBindings bindings{};
  void *state_slot = memory.Allocate(8), *state = memory.Allocate(0xA8);
  void *data = memory.Allocate(0x2A540 + 0x190);
  void *manager = static_cast<std::byte *>(data) + 0x2A540;
  void *pending = memory.Allocate(19 * 0x28);
  void *unit_a = memory.Allocate(0x180), *unit_scope = memory.Allocate(0x180);
  void *army_a = memory.Allocate(0x210), *army_scope = memory.Allocate(0x210);
  void *army_fallback = memory.Allocate(0x210);
  void *combat = memory.Allocate(0x10), *combat_fallback = memory.Allocate(0x10);
  void *contract_flag = memory.Allocate(0xC0), *contract_normal = memory.Allocate(0xC0);
  std::array<void *, 7> regs{};
  void *reg_scope = memory.Allocate(0x150), *reg_fallback = memory.Allocate(0x150);
  std::array<void *, 4> persistents{};
  void *war_valid = memory.Allocate(0x360), *war_wrong_magic = memory.Allocate(0x360);
  void *war_indexed = memory.Allocate(0x360), *war_fallback = memory.Allocate(0x360);

  explicit Fixture(bool deny_empty_removal_data = true) {
    bindings.enabled = true;
    bindings.game_state_slot = static_cast<void **>(state_slot);
    bindings.unit_storage_slot = static_cast<void **>(units.slot);
    bindings.internal_army_storage_slot = static_cast<void **>(armies.slot);
    bindings.regiment_storage_slot = static_cast<void **>(arrgs.slot);
    bindings.get_army_current_soldiers = Current;
    bindings.get_army_maximum_soldiers = Maximum;
    auto &b = bindings.current_pre_date_pending_update_bindings;
    b.common.enabled = true; b.common.game_state_slot = state_slot;
    b.common.army_registry_slot = armies.slot; b.common.army_fallback_slot = armies.fallback_slot;
    b.common.unit_registry_slot = units.slot; b.common.unit_fallback_slot = units.fallback_slot;
    b.common.war_registry_slot = wars.slot; b.common.war_fallback_slot = wars.fallback_slot;
    b.common.read_memory = Memory::Read; b.common.read_context = &memory;
    b.combat_registry_slot = combats.slot; b.combat_fallback_slot = combats.fallback_slot;
    b.arrg_registry_slot = arrgs.slot; b.arrg_fallback_slot = arrgs.fallback_slot;
    b.contract_registry_slot = contracts.slot; b.contract_fallback_slot = contracts.fallback_slot;
    b.persistent_registry_slot = persistent.slot; b.persistent_fallback_slot = persistent.fallback_slot;
    bindings.current_daily_assault_roster_admission_bindings = b.common;

    memory.Put(state_slot, 0, state); memory.Put(state, 0xA0, data);
    Ids(static_cast<std::byte *>(manager) + 0x50, {kArmyA, kArmyA});
    Ids(static_cast<std::byte *>(manager) + 0x68, {});
    memory.Deny(manager, 0, 8);
    if (deny_empty_removal_data) memory.Deny(manager, 0x68, 8);
    memory.Put(manager, 0x138, pending); memory.Put(manager, 0x140, std::int32_t{1});
    memory.Put(manager, 0x144, std::int32_t{15}); memory.Put(manager, 0x148, std::uint8_t{2});
    memory.Put(manager, 0x14C, std::uint32_t{0x3F400000U});

    units.Add(kUnitA, unit_a, 0x10); units.Add(kUnitScope, unit_scope, 0x10);
    armies.Add(kArmyA, army_a, 0x10); armies.Add(kArmyScope, army_scope, 0x10);
    memory.Put(army_fallback, 0x10, kArmyFallback); memory.Put(armies.fallback_slot, 0, army_fallback);
    // A decisive real standalone-admission false allows the separate pre-date mutator to be tested independently.
    memory.Put(unit_a, 0x18, std::uint32_t{1}); memory.Put(unit_scope, 0x178, kArmyScope);
    memory.Put(army_a, 0x124, kUnitA); memory.Put(army_scope, 0x124, kUnitScope);
    memory.Put(army_fallback, 0x124, kUnitA);
    memory.Put(army_a, 0x128, kInvalid); memory.Put(army_fallback, 0x128, kInvalid);
    combats.Add(kCombat, combat, 8); memory.Put(combat, 0xC, std::uint32_t{0x436F6D62U});
    memory.Put(combat_fallback, 8, kInvalid); memory.Put(combat_fallback, 0xC, std::uint32_t{0});
    memory.Put(combats.fallback_slot, 0, combat_fallback);
    contracts.Add(kContractFlag, contract_flag, 8); contracts.Add(kContractNormal, contract_normal, 8);
    memory.Put(contract_flag, 0xB9, std::uint8_t{1}); memory.Put(contract_normal, 0xB9, std::uint8_t{0});
    memory.Put(contracts.fallback_slot, 0, contract_normal);
    for (std::size_t i = 0; i < regs.size(); ++i) {
      regs[i] = memory.Allocate(0x150);
      arrgs.Add(kRegA + static_cast<std::uint32_t>(i), regs[i], 0x10);
      memory.Put(regs[i], 0x14, std::uint32_t{0x41725267U});
      memory.Put(regs[i], 0x144, kContractNormal);
    }
    arrgs.Add(kRegScope, reg_scope, 0x10);
    memory.Put(reg_scope, 0x14, std::uint32_t{0x41725267U});
    memory.Put(reg_scope, 0x38, std::int32_t{160}); memory.Put(reg_scope, 0x3C, std::int32_t{240});
    memory.Put(reg_scope, 0x40, std::int64_t{300000});
    memory.Put(reg_fallback, 0x10, kRegFallback); memory.Put(arrgs.fallback_slot, 0, reg_fallback);
    Ids(static_cast<std::byte *>(army_scope) + 0x38, {kRegScope});
    Ids(static_cast<std::byte *>(army_a) + 0x38, {kRegA});
    Ids(static_cast<std::byte *>(army_fallback) + 0x38, {kRegWrongGeneration});
    Pending(kArmyA, {});

    const std::array<std::uint32_t, 4> ids{{kPersistentD, kPersistentE, kPersistentF, kPersistentG}};
    for (std::size_t i = 0; i < persistents.size(); ++i) {
      persistents[i] = memory.Allocate(0x140); persistent.Add(ids[i], persistents[i], 0x10);
    }
    wars.Add(kWarValid, war_valid, 8); wars.Add(kWarWrongMagic, war_wrong_magic, 8);
    wars.Add(kWarIndexed, war_indexed, 8);
    memory.Put(war_valid, 0xC, std::uint32_t{0x5761725FU});
    memory.Put(war_wrong_magic, 0xC, std::uint32_t{0});
    memory.Put(war_indexed, 0xC, std::uint32_t{0x5761725FU});
    memory.Put(war_fallback, 8, kInvalid); memory.Put(war_fallback, 0xC, std::uint32_t{0x5761725FU});
    memory.Put(wars.fallback_slot, 0, war_fallback);
    expected_scope_army = army_scope;
  }

  void *Ids(void *header, std::initializer_list<std::uint32_t> ids) {
    memory.Put(header, 8, static_cast<std::int32_t>(ids.size()));
    memory.Put(header, 0xC, static_cast<std::int32_t>(ids.size()));
    memory.Put(header, 0, static_cast<const void *>(nullptr));
    if (ids.size() == 0) return nullptr;
    void *values = memory.Allocate(ids.size() * 4);
    std::size_t i = 0; for (auto id : ids) memory.Put(values, i++ * 4, id);
    memory.Put(header, 0, values); return values;
  }
  void *PendingRecord(std::uint32_t army) {
    return static_cast<std::byte *>(pending) + (Hash(army) & 15U) * 0x28;
  }
  void Pending(std::uint32_t army, std::initializer_list<std::uint32_t> ids) {
    void *record = PendingRecord(army);
    memory.Put(record, 0, Hash(army)); memory.Put(record, 4, std::uint8_t{1});
    memory.Put(record, 8, army); Ids(static_cast<std::byte *>(record) + 0x10, ids);
  }
  void OriginalPersistent(void *regiment, std::uint32_t full_id) {
    void *original_data = memory.Allocate(12);
    memory.Put(original_data, 8, full_id); memory.Put(regiment, 0x20, original_data);
    memory.Put(regiment, 0x2C, std::int32_t{0});
    memory.Deny(regiment, 0x2C, 4); // Actual helper reads data+8 without consulting this count.
  }
  std::vector<game::ArmyStrengthSnapshot> Observe(bool context_available = true) {
    const auto before = memory.Snapshot();
    const std::array<ck3_12002::ArmyStrengthScope, 2> scope{{
        {static_cast<std::int32_t>(kUnitScope), game::ArmyStrengthScopeRole::player, {}},
        {static_cast<std::int32_t>(kUnitScope), game::ArmyStrengthScopeRole::active_war_ally, {7}}}};
    std::vector<game::ArmyStrengthSnapshot> rows;
    const auto result = ck3_12002::ReadArmyStrengthsForScope(bindings, scope, rows);
    Check(result == game::ReadArmyStrengthsResult::available && rows.size() == 2,
          "pre-date optional source leaf must preserve available scoped ArmyStrength query");
    for (const auto &row : rows) {
      Check(row.available && row.current_soldiers == 160 && row.maximum_soldiers == 240 &&
                row.ai_base_power_raw == 300000 && row.regiment_count == 1 &&
                row.native_carmy_id == static_cast<std::int32_t>(kArmyScope),
            "pre-date source partial must preserve original whole-strength numeric values");
      Check(row.current_daily_assault_roster_admission_v1 && row.current_pre_date_pending_update_inputs_v1 &&
                !row.current_daily_assault_table_v1 && !row.current_daily_assault_loss_inputs_v1,
            "pre-date fixture must sample production new leaf and actual roster without enabling older optional table/loss");
      const auto &leaf = *row.current_pre_date_pending_update_inputs_v1;
      Check(!leaf.actual_pre_date_callback_ready && !leaf.actual_tomorrow_roster_ready &&
                !leaf.full_daily_assault_ready && !leaf.full_monthly_ready,
            "source operands must not claim actual callback/tomorrow/daily/monthly execution");
    }
    Check(rows[0].current_daily_assault_roster_admission_v1 == rows[1].current_daily_assault_roster_admission_v1 &&
              rows[0].current_pre_date_pending_update_inputs_v1 == rows[1].current_pre_date_pending_update_inputs_v1,
          "two scope rows must reuse one same-query source leaf");
    if (context_available)
      Check(memory.Reads(manager, 0x5C, 4) == 1 && memory.Reads(manager, 0x74, 4) == 1,
            "new pending collector must reuse actual primary roster and ready removal queue");
    Check(before == memory.Snapshot(), "new readonly collector must leave source roster/map/vector memory unchanged");
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
  std::ofstream output(directory / (std::string("pre-date-pending-") + name + ".json"), std::ios::binary);
  output << wire << '\n';
  Check(static_cast<bool>(output), "pre-date pending production whole-strength wire write failed");
}

const game::ArmyCurrentPreDatePendingUpdateInputsV1 &Leaf(const std::vector<game::ArmyStrengthSnapshot> &rows) {
  return *rows[0].current_pre_date_pending_update_inputs_v1;
}
void CheckReady(const game::ArmyCurrentPreDatePendingUpdateInputsV1 &leaf, std::size_t count,
                std::int32_t removal_count = 0) {
  Check(leaf.ready && leaf.status == "available" && leaf.unavailable_reason.empty() &&
            leaf.raw_roster_references_ready && leaf.source_operands_ready &&
            leaf.original_roster.count_raw_i32 == static_cast<std::int32_t>(count) &&
            leaf.occurrences.size() == count && leaf.removal_queue.references_ready &&
            leaf.removal_queue.count_raw_i32 == removal_count,
        "new pre-date source input readiness must follow actual complete roster/occurrence memory reads");
}
void CheckExisting(const game::ArmyPreDatePendingOccurrenceV1 &row, std::uint32_t target) {
  Check(row.ready && row.pending_mutator_selected == true && row.army_counter_5c_raw_i32 == 0 &&
            row.pending_setup.ready && row.pending_setup.existing_key == true &&
            row.pending_setup.target_army_full_id_u32 == target && row.pending_setup.hash_raw_u32 == Hash(target) &&
            row.pending_setup.home_slot_i64 == static_cast<std::int64_t>(Hash(target) & 15U) &&
            row.pending_setup.terminal_physical_slot_i64 == row.pending_setup.home_slot_i64 &&
            row.pending_setup.probes.size() == 1 && row.pending_setup.probes[0].control_raw_u8 == 1 &&
            row.pending_setup.probes[0].key_raw_full_id_u32 == target &&
            row.pending_setup.existing_references.references_ready &&
            row.pending_setup.existing_references.count_raw_i32 == 0 &&
            !row.pending_setup.map_count_raw_i32 && !row.pending_setup.insertion_tail_raw_u8 &&
            !row.pending_setup.insertion_threshold_bits_u32,
        "existing-key setup must use real hash/control/key/list and omit unconsumed insertion header");
}

void ExactBinding() {
  constexpr std::uintptr_t base = 0x140000000;
  const auto b = ck3_12003::BindCurrentPreDatePendingUpdate12003(base, ck3_12003::kExecutableSha256);
  const auto at = [base](std::uintptr_t rva) { return reinterpret_cast<const void *>(base + rva); };
  Check(b.common.enabled && b.common.game_state_slot == at(0x5C68C50) &&
            b.combat_registry_slot == at(0x5D1DE70) && b.combat_fallback_slot == at(0x5D1DE18) &&
            b.arrg_registry_slot == at(0x5D1F340) && b.arrg_fallback_slot == at(0x5D1F338) &&
            b.contract_registry_slot == at(0x5D1EB88) && b.contract_fallback_slot == at(0x5D1EB40) &&
            b.persistent_registry_slot == at(0x5D1EB68) && b.persistent_fallback_slot == at(0x5D1EB58),
        "new exact-build pending operand binding must retain source-closed current registry slots");
  Check(!ck3_12003::BindCurrentPreDatePendingUpdate12003(base, "wrong-build").common.enabled &&
            !ck3_12003::BindCurrentPreDatePendingUpdate12003(0, ck3_12003::kExecutableSha256).common.enabled,
        "new pending inputs must remain unbound on unavailable/different exact build");
}

void Scenes(const std::filesystem::path &directory) {
  ExactBinding();
  {
    Fixture f;
    f.Ids(static_cast<std::byte *>(f.army_a) + 0x38, {kRegA, kRegC});
    f.memory.Put(f.regs[2], 0x38, std::int32_t{10});
    f.memory.Deny(f.manager, 0x140, 4); f.memory.Deny(f.manager, 0x148, 1); f.memory.Deny(f.manager, 0x14C, 4);
    f.memory.Deny(f.regs[0], 0x144, 4);
    const auto rows = f.Observe(); const auto &leaf = Leaf(rows); CheckReady(leaf, 2);
    for (std::size_t i = 0; i < leaf.occurrences.size(); ++i) {
      const auto &row = leaf.occurrences[i]; CheckExisting(row, kArmyA);
      Check(row.native_index == static_cast<std::int32_t>(i) && row.raw_full_id_u32 == kArmyA &&
                row.original_arrg_references.count_raw_i32 == 2 && row.arrg_occurrences.size() == 2 &&
                row.arrg_occurrences[0].raw_full_id_u32 == kRegA && row.arrg_occurrences[0].current_38_raw_i32 == 0 &&
                row.arrg_occurrences[0].append_to_pending == true && row.arrg_occurrences[0].append_full_id_u32 == kRegA &&
                !row.arrg_occurrences[0].contract_id_144_raw_u32 &&
                row.arrg_occurrences[1].raw_full_id_u32 == kRegC && row.arrg_occurrences[1].current_38_raw_i32 == 10 &&
                row.arrg_occurrences[1].contract_flag_b9_raw_u8 == 0 && row.arrg_occurrences[1].state_14c_raw_i32 == 0 &&
                row.arrg_occurrences[1].append_to_pending == false,
            "repeated original Army occurrences must preserve two separate zero-current pending appends");
    }
    Check(f.memory.Attempts() == 0, "existing-key and zero-current branches must skip their undemanded headers/contract");
    Emit(directory, "existing-key-repeated-army", rows);
  }
  {
    Fixture f(false);
    f.Ids(static_cast<std::byte *>(f.manager) + 0x50, {kArmyA});
    f.Ids(static_cast<std::byte *>(f.manager) + 0x68, {99, 99});
    f.Ids(static_cast<std::byte *>(f.army_a) + 0x38, {kRegA, kRegB, kRegC, kRegD, kRegE, kRegF, kRegG});
    for (std::size_t i = 1; i < f.regs.size(); ++i) f.memory.Put(f.regs[i], 0x38, std::int32_t{10});
    f.memory.Put(f.regs[1], 0x144, kContractFlag);
    for (std::size_t i = 3; i < f.regs.size(); ++i) f.memory.Put(f.regs[i], 0x14C, std::int32_t{1});
    f.OriginalPersistent(f.regs[3], kPersistentD); f.OriginalPersistent(f.regs[4], kPersistentE);
    f.OriginalPersistent(f.regs[5], kPersistentF); f.OriginalPersistent(f.regs[6], kPersistentG);
    f.memory.Put(f.persistents[0], 0x13C, kInvalid); f.memory.Put(f.persistents[1], 0x13C, kWarWrongMagic);
    f.memory.Put(f.persistents[2], 0x13C, kWarWrongGeneration); f.memory.Put(f.persistents[3], 0x13C, kWarValid);
    f.memory.Deny(f.regs[0], 0x144, 4); f.memory.Deny(f.regs[1], 0x14C, 4); f.memory.Deny(f.regs[2], 0x20, 8);
    const auto rows = f.Observe(); const auto &leaf = Leaf(rows); CheckReady(leaf, 1, 2);
    const auto &row = leaf.occurrences[0]; CheckExisting(row, kArmyA);
    const auto &r = row.arrg_occurrences;
    Check(r.size() == 7 && r[0].append_to_pending == true && r[1].append_to_pending == true &&
              r[2].append_to_pending == false && r[3].append_to_pending == false &&
              r[4].append_to_pending == true && r[5].append_to_pending == true && r[6].append_to_pending == false,
          "mixed real predicate operands must select appends [A,B,E,F] in original order");
    Check(r[0].current_38_raw_i32 == 0 && !r[0].contract_id_144_raw_u32 &&
              r[1].contract_flag_b9_raw_u8 == 1 && !r[1].state_14c_raw_i32 &&
              r[2].state_14c_raw_i32 == 0 && !r[2].first_persistent_id_raw_u32 &&
              r[3].persistent_war_id_13c_raw_u32 == kInvalid && !r[3].war_magic_0c_raw_u32 &&
              r[4].war_magic_0c_raw_u32 == 0U && r[5].war_resolution.used_fallback == true &&
              r[5].war_resolution.selected_full_id_u32 == kInvalid && r[5].war_magic_0c_raw_u32 == 0x5761725FU &&
              r[6].war_resolution.selected_full_id_u32 == kWarValid && r[6].war_magic_0c_raw_u32 == 0x5761725FU,
          "mixed contract/persistent/War operands and sentinel choices must come from demanded source reads");
    Check(f.memory.Attempts() == 0, "mixed predicates must skip all source-unused contract/state/vector-count fields");
    Check(leaf.removal_queue.occurrences.size() == 2 && leaf.removal_queue.occurrences[0].raw_full_id_u32 == 99U &&
              leaf.removal_queue.occurrences[1].raw_full_id_u32 == 99U,
          "mixed current source must preserve real nonmatching old removal duplicates without normalization");
    Emit(directory, "mixed-arrg-predicates", rows);
  }
  {
    Fixture f; f.Ids(static_cast<std::byte *>(f.manager) + 0x50, {kArmyA});
    f.memory.Put(f.PendingRecord(kArmyA), 4, std::uint8_t{0});
    f.memory.Put(f.manager, 0x140, std::int32_t{0});
    f.memory.Deny(f.pending, 18 * 0x28 + 4, 1); // Standalone end marker is not a mutator insertion input.
    const auto rows = f.Observe(); const auto &leaf = Leaf(rows); CheckReady(leaf, 1);
    const auto &setup = leaf.occurrences[0].pending_setup;
    Check(setup.ready && setup.existing_key == false && setup.target_army_full_id_u32 == kArmyA &&
              setup.probes.size() == 1 && setup.probes[0].control_raw_u8 == 0 && !setup.probes[0].key_raw_full_id_u32 &&
              setup.terminal_physical_slot_i64 == setup.home_slot_i64 && setup.map_count_raw_i32 == 0 &&
              setup.mask_raw_i32 == 15 && setup.insertion_tail_raw_u8 == 2 &&
              setup.insertion_threshold_bits_u32 == 0x3F400000U &&
              leaf.occurrences[0].arrg_occurrences[0].append_to_pending == true,
          "direct-empty mutator miss must read actual insertion header and empty control without standalone end-marker demands");
    Check(f.memory.Attempts() == 0, "direct empty pending setup must use only reachable map source operands");
    Emit(directory, "direct-empty-insertion", rows);
  }
  {
    Fixture f; f.Ids(static_cast<std::byte *>(f.manager) + 0x50, {});
    f.memory.Deny(f.manager, 0x50, 8); f.memory.Deny(f.manager, 0x138, 8);
    const auto rows = f.Observe(); const auto &leaf = Leaf(rows); CheckReady(leaf, 0);
    Check(leaf.original_roster.occurrences.empty() && leaf.occurrences.empty() && !leaf.original_roster.data_present &&
              f.memory.Attempts() == 0,
          "known-zero source roster/removal must be complete without data pointers or pending map");
    Emit(directory, "known-zero-roster", rows);
  }
  {
    Fixture f; f.memory.Deny(f.state, 0xA0, 8);
    const auto rows = f.Observe(false); const auto &leaf = Leaf(rows);
    Check(!leaf.ready && !leaf.source_operands_ready && !leaf.raw_roster_references_ready &&
              leaf.unavailable_reason == "pre_date_pending_game_data_unavailable" && leaf.occurrences.empty() &&
              f.memory.Reads(f.manager, 0x5C, 4) == 0,
          "missing actual game-data context must preserve unavailable source distinction and independent whole strength");
    Emit(directory, "missing-game-data-context", rows);
  }
  {
    Fixture f; f.Ids(static_cast<std::byte *>(f.manager) + 0x50, {kArmyA});
    f.memory.Put(f.army_a, 0x128, kCombat);
    f.memory.Deny(f.army_a, 0x5C, 4); f.memory.Deny(f.army_a, 0x44, 4); f.memory.Deny(f.manager, 0x138, 8);
    const auto rows = f.Observe(); const auto &leaf = Leaf(rows); CheckReady(leaf, 1);
    const auto &row = leaf.occurrences[0];
    Check(row.pending_mutator_selected == false && row.combat_magic_0c_raw_u32 == 0x436F6D62U &&
              row.combat_resolution.selected_full_id_u32 == kCombat && !row.army_counter_5c_raw_i32 &&
              !row.pending_setup.ready && row.arrg_occurrences.empty() && f.memory.Attempts() == 0,
          "real valid Combat must bypass counter/pending/ArRg work before any such read");
    Emit(directory, "valid-combat-bypass", rows);
  }
  {
    Fixture f; f.Ids(static_cast<std::byte *>(f.manager) + 0x50, {kArmyA});
    f.memory.Put(f.army_a, 0x5C, std::int32_t{1});
    f.memory.Deny(f.army_a, 0x44, 4); f.memory.Deny(f.manager, 0x138, 8);
    const auto rows = f.Observe(); const auto &leaf = Leaf(rows); CheckReady(leaf, 1);
    const auto &row = leaf.occurrences[0];
    Check(row.pending_mutator_selected == false && row.combat_magic_0c_raw_u32 == 0U &&
              row.army_counter_5c_raw_i32 == 1 && !row.pending_setup.ready && row.arrg_occurrences.empty() &&
              f.memory.Attempts() == 0,
          "real nonzero Army5C must bypass pending/ArRg work after invalid Combat branch");
    Emit(directory, "nonzero-army-counter-bypass", rows);
  }
  {
    Fixture f; f.Ids(static_cast<std::byte *>(f.manager) + 0x50, {kArmyWrongGeneration});
    f.Pending(kArmyFallback, {});
    const auto rows = f.Observe(); const auto &leaf = Leaf(rows); CheckReady(leaf, 1);
    const auto &row = leaf.occurrences[0]; CheckExisting(row, kArmyFallback);
    Check(row.raw_full_id_u32 == kArmyWrongGeneration && row.original_army_resolution.used_fallback == true &&
              row.original_army_resolution.indexed_full_id_u32 == kArmyA &&
              row.original_army_resolution.selected_full_id_u32 == kArmyFallback && row.arrg_occurrences.size() == 1 &&
              row.arrg_occurrences[0].raw_full_id_u32 == kRegWrongGeneration &&
              row.arrg_occurrences[0].arrg_resolution.indexed_full_id_u32 == kRegA &&
              row.arrg_occurrences[0].arrg_resolution.used_fallback == true &&
              row.arrg_occurrences[0].arrg_resolution.selected_full_id_u32 == kRegFallback &&
              row.arrg_occurrences[0].append_to_pending == true &&
              row.arrg_occurrences[0].append_full_id_u32 == kRegFallback && f.memory.Attempts() == 0,
          "unresolved raw references must retain actual indexed mismatch and use read native fallback IDs for pending work");
    Emit(directory, "wrong-generation-fallback", rows);
  }
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 3 || std::string_view(argv[1]) != "--wire-dir") {
    std::cerr << "usage: xar_bridge_ck3_12003_current_pre_date_pending_update_test --wire-dir DIRECTORY\n";
    return 2;
  }
  try {
    const std::filesystem::path directory(argv[2]);
    std::filesystem::create_directories(directory);
    Scenes(directory);
    std::cout << "current pre-date pending update production memory fixture GREEN: 8 new whole-strength wires\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "current pre-date pending update fixture RED: " << error.what() << '\n';
    return 1;
  }
}
