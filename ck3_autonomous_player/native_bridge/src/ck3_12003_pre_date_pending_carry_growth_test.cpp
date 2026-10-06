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
    void *address = bytes.get(); regions.push_back({std::move(bytes), size}); return address;
  }
  template <class T> void Put(void *address, std::size_t offset, T value) {
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
    for (const auto &r : regions) out.emplace_back(r.bytes.get(), r.bytes.get() + r.size);
    return out;
  }
  static bool Read(void *context, const void *address, void *output, std::size_t size) noexcept {
    auto &m = *static_cast<Memory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    for (auto &r : m.denied) {
      if (begin < r.begin + r.size && r.begin < begin + size) {
        ++r.attempts; m.events.push_back({address, size, false}); return false;
      }
    }
    for (const auto &r : m.regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(r.bytes.get());
      if (begin >= base && begin - base <= r.size && size <= r.size - (begin - base)) {
        std::memcpy(output, address, size); m.events.push_back({address, size, true}); return true;
      }
    }
    m.events.push_back({address, size, false}); return false;
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
  void Add(std::uint32_t full_id, void *object, std::size_t full_offset) {
    memory.Put(table, static_cast<std::size_t>(full_id & 0xFFFFFFU) * 16 + 8, object);
    memory.Put(object, full_offset, full_id);
  }
};

constexpr std::uint32_t kInvalid = 0xFFFFFFFFU, kArmyA = 12U, kArmyEarlier = 4U;
constexpr std::uint32_t kUnitA = 0x11000001U, kUnitScope = 0x11000002U, kArmyScope = 0x22000002U;
constexpr std::uint32_t kRegA = 0x2B000001U, kRegSkip = 0x2B000002U, kRegScope = 0x2B000003U;
constexpr std::uint32_t kContract = 0x66000001U;
constexpr std::uint32_t kThresholdNineTenths = 0x3F666666U, kThresholdOneHalf = 0x3F000000U;

std::uint32_t Hash(std::uint32_t key) {
  std::uint32_t value = 0x811C9DC5U;
  for (std::uint32_t shift = 0; shift != 32; shift += 8)
    value = (value ^ ((key >> shift) & 0xFFU)) * 0x1000193U;
  return value;
}
void *expected_scope_army = nullptr;
std::int32_t Current(void *receiver, std::uint8_t flags) {
  Check(flags == 0 && receiver == static_cast<std::byte *>(expected_scope_army) + 0x38,
        "carry/growth fixture flags-zero current receiver must be independent scope Army");
  return 160;
}
std::int32_t Maximum(void *receiver) {
  Check(receiver == expected_scope_army, "carry/growth fixture maximum receiver must be independent scope Army");
  return 240;
}

struct Fixture {
  Memory memory;
  Registry units{memory, 3U}, armies{memory, 13U}, arrgs{memory, 4U};
  Registry combats{memory, 1U}, contracts{memory, 2U};
  ck3_12002::ArmyBindings bindings{};
  void *state_slot = memory.Allocate(8), *state = memory.Allocate(0xA8);
  void *data = memory.Allocate(0x2A540 + 0x190);
  void *manager = static_cast<std::byte *>(data) + 0x2A540;
  void *pending = memory.Allocate(14 * 0x28);
  void *native_empty = memory.Allocate(2 * 0x28), *vector_allocator = memory.Allocate(8);
  void *unit_a = memory.Allocate(0x180), *unit_scope = memory.Allocate(0x180);
  void *army_a = memory.Allocate(0x210), *army_earlier = memory.Allocate(0x210);
  void *army_scope = memory.Allocate(0x210), *combat_fallback = memory.Allocate(0x10);
  void *reg_a = memory.Allocate(0x150), *reg_skip = memory.Allocate(0x150);
  void *reg_scope = memory.Allocate(0x150), *contract = memory.Allocate(0xC0);

  Fixture() {
    bindings.enabled = true; bindings.game_state_slot = static_cast<void **>(state_slot);
    bindings.unit_storage_slot = static_cast<void **>(units.slot);
    bindings.internal_army_storage_slot = static_cast<void **>(armies.slot);
    bindings.regiment_storage_slot = static_cast<void **>(arrgs.slot);
    bindings.get_army_current_soldiers = Current; bindings.get_army_maximum_soldiers = Maximum;
    auto &b = bindings.current_pre_date_pending_update_bindings;
    b.common.enabled = true; b.common.game_state_slot = state_slot;
    b.common.army_registry_slot = armies.slot; b.common.army_fallback_slot = armies.fallback_slot;
    b.common.unit_registry_slot = units.slot; b.common.unit_fallback_slot = units.fallback_slot;
    b.common.read_memory = Memory::Read; b.common.read_context = &memory;
    b.combat_registry_slot = combats.slot; b.combat_fallback_slot = combats.fallback_slot;
    b.arrg_registry_slot = arrgs.slot; b.arrg_fallback_slot = arrgs.fallback_slot;
    b.contract_registry_slot = contracts.slot; b.contract_fallback_slot = contracts.fallback_slot;
    b.native_empty_pending_buffer = native_empty; b.expected_pending_vector_allocator = vector_allocator;
    bindings.current_daily_assault_roster_admission_bindings = b.common;
    memory.Put(state_slot, 0, state); memory.Put(state, 0xA0, data);
    Ids(static_cast<std::byte *>(manager) + 0x50, {kArmyA});
    Ids(static_cast<std::byte *>(manager) + 0x68, {});
    memory.Deny(manager, 0, 8); memory.Deny(manager, 0x68, 8); memory.Deny(vector_allocator, 0, 8);
    Header(pending, 4, 7, 5, kThresholdNineTenths);
    memory.Put(pending, 13 * 0x28 + 4, std::uint8_t{0xFF});
    memory.Deny(pending, 13 * 0x28, 4); memory.Deny(pending, 13 * 0x28 + 8, 0x20);
    memory.Put(native_empty, 4, std::uint8_t{0}); memory.Put(native_empty, 0x28 + 4, std::uint8_t{0xFF});
    memory.Deny(native_empty, 0, 4); memory.Deny(native_empty, 8, 0x20);
    memory.Deny(native_empty, 0x28, 4); memory.Deny(native_empty, 0x28 + 8, 0x20);

    units.Add(kUnitA, unit_a, 0x10); units.Add(kUnitScope, unit_scope, 0x10);
    memory.Put(unit_a, 0x18, std::uint32_t{1U}); memory.Put(unit_scope, 0x178, kArmyScope);
    armies.Add(kArmyA, army_a, 0x10); armies.Add(kArmyEarlier, army_earlier, 0x10);
    armies.Add(kArmyScope, army_scope, 0x10);
    for (void *army : {army_a, army_earlier}) {
      memory.Put(army, 0x124, kUnitA); memory.Put(army, 0x128, kInvalid);
      Ids(static_cast<std::byte *>(army) + 0x38, {kRegA, kRegSkip});
    }
    memory.Put(army_scope, 0x124, kUnitScope);
    memory.Put(combat_fallback, 8, kInvalid); memory.Put(combat_fallback, 0xC, std::uint32_t{0U});
    memory.Put(combats.fallback_slot, 0, combat_fallback);
    contracts.Add(kContract, contract, 8); memory.Put(contract, 0xB9, std::uint8_t{0});
    arrgs.Add(kRegA, reg_a, 0x10); arrgs.Add(kRegSkip, reg_skip, 0x10); arrgs.Add(kRegScope, reg_scope, 0x10);
    memory.Put(reg_skip, 0x38, std::int32_t{10}); memory.Put(reg_skip, 0x144, kContract);
    memory.Put(reg_skip, 0x14C, std::int32_t{0});
    memory.Put(reg_scope, 0x14, std::uint32_t{0x41725267U});
    memory.Put(reg_scope, 0x38, std::int32_t{160}); memory.Put(reg_scope, 0x3C, std::int32_t{240});
    memory.Put(reg_scope, 0x40, std::int64_t{300000});
    Ids(static_cast<std::byte *>(army_scope) + 0x38, {kRegScope});
    GeneralRecords(); expected_scope_army = army_scope;
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
  void Header(void *entries, std::int32_t count, std::int32_t mask, std::uint8_t tail, std::uint32_t threshold) {
    memory.Put(manager, 0x138, entries); memory.Put(manager, 0x140, count);
    memory.Put(manager, 0x144, mask); memory.Put(manager, 0x148, tail); memory.Put(manager, 0x14C, threshold);
  }
  void *Record(std::size_t slot) { return static_cast<std::byte *>(pending) + slot * 0x28; }
  void PutRecord(std::size_t slot, std::uint32_t key, std::uint8_t control,
                 std::initializer_list<std::uint32_t> values) {
    void *record = Record(slot);
    memory.Put(record, 0, Hash(key)); memory.Put(record, 4, control); memory.Put(record, 8, key);
    Ids(static_cast<std::byte *>(record) + 0x10, values); memory.Put(record, 0x20, vector_allocator);
  }
  void GeneralRecords() {
    PutRecord(1, 4U, 1, {601U}); PutRecord(2, 7U, 1, {701U, 701U, 702U});
    PutRecord(3, 6U, 1, {801U, 801U}); PutRecord(4, 1U, 1, {901U, 902U, 901U});
  }
  void EmptyRecords() {
    for (std::size_t slot = 1; slot <= 4; ++slot) memory.Put(Record(slot), 4, std::uint8_t{0});
  }
  std::vector<game::ArmyStrengthSnapshot> Observe(bool framed = true) {
    const auto before = memory.Snapshot();
    const std::array<ck3_12002::ArmyStrengthScope, 2> scope{{
        {static_cast<std::int32_t>(kUnitScope), game::ArmyStrengthScopeRole::player, {}},
        {static_cast<std::int32_t>(kUnitScope), game::ArmyStrengthScopeRole::active_war_ally, {7}}}};
    std::vector<game::ArmyStrengthSnapshot> rows;
    const auto result = ck3_12002::ReadArmyStrengthsForScope(bindings, scope, rows);
    Check(result == game::ReadArmyStrengthsResult::available && rows.size() == 2,
          "new carry/growth source optional must preserve available whole-strength query");
    for (const auto &row : rows) {
      Check(row.available && row.current_soldiers == 160 && row.maximum_soldiers == 240 &&
                row.ai_base_power_raw == 300000 && row.regiment_count == 1 &&
                row.native_carmy_id == static_cast<std::int32_t>(kArmyScope),
            "new carry/growth frame must preserve complete legacy scoped strength values");
      Check(row.current_pre_date_pending_update_inputs_v1 && row.current_daily_assault_roster_admission_v1 &&
                !row.current_daily_assault_table_v1 && !row.current_daily_assault_loss_inputs_v1,
            "new frame fixture must use actual pending/roster producer without enabling older optional table/loss leaves");
      const auto &p = *row.current_pre_date_pending_update_inputs_v1;
      Check(p.pending_table_frame_v1.has_value() == framed && !p.actual_pre_date_callback_ready &&
                !p.actual_tomorrow_roster_ready && !p.full_daily_assault_ready && !p.full_monthly_ready,
            "current raw frame must not claim actual callbacks/tomorrow/daily/monthly");
    }
    Check(rows[0].current_pre_date_pending_update_inputs_v1 == rows[1].current_pre_date_pending_update_inputs_v1 &&
              memory.Reads(manager, 0x5C, 4) == 1 && memory.Reads(manager, 0x74, 4) == 1,
          "new source frame and primary/removal roster must be sampled once and reused across scope rows");
    if (framed)
      Check(memory.Reads(manager, 0x138, 8) == 1 && memory.Reads(manager, 0x140, 4) == 1 &&
                memory.Reads(manager, 0x144, 4) == 1 && memory.Reads(manager, 0x148, 1) == 1 &&
                memory.Reads(manager, 0x14C, 4) == 1,
            "actual same-query frame header must be reused by repeated current lookup setups");
    Check(before == memory.Snapshot(), "new frame sampler must leave native-shaped source memory unchanged");
    return rows;
  }
};

const game::ArmyCurrentPreDatePendingUpdateInputsV1 &Leaf(const std::vector<game::ArmyStrengthSnapshot> &rows) {
  return *rows[0].current_pre_date_pending_update_inputs_v1;
}
const game::ArmyPreDatePendingTableFrameV1 &Frame(const std::vector<game::ArmyStrengthSnapshot> &rows) {
  return *Leaf(rows).pending_table_frame_v1;
}
const game::ArmyPreDatePendingPhysicalRecordV1 &Physical(const game::ArmyPreDatePendingTableFrameV1 &frame,
                                                       std::int64_t slot) {
  for (const auto &record : frame.records)
    if (record.physical_slot_i64 == slot) return record;
  throw std::runtime_error("fixture expected captured physical record");
}
void CheckFrame(const game::ArmyPreDatePendingTableFrameV1 &frame, std::int32_t count,
                std::int32_t mask, std::uint8_t tail, std::uint32_t threshold) {
  Check(frame.ready && frame.status == "available" && frame.entries_present == true &&
            frame.map_count_raw_i32 == count && frame.mask_raw_i32 == mask && frame.tail_raw_u8 == tail &&
            frame.threshold_bits_u32 == threshold && frame.physical_controls_complete && frame.rehash_prefix_complete &&
            frame.physical_control_extent_last_slot_i64 == static_cast<std::int64_t>(mask) + tail + 1,
        "raw current pending frame header/controls/count-driven prefix must come from complete actual memory reads");
  const auto &terminal = Physical(frame, static_cast<std::int64_t>(mask) + tail + 1);
  Check(terminal.control_raw_u8 == 0xFF && !terminal.stored_hash_raw_u32 &&
            !terminal.key_raw_full_id_u32 && !terminal.vector_capacity_raw_i32,
        "current extent terminal must stay control-only when old count prefix does not consume it");
}
void CheckValues(const game::ArmyPreDatePendingPhysicalRecordV1 &record, std::uint32_t key,
                 std::uint8_t control, std::initializer_list<std::uint32_t> expected) {
  Check(record.ready && record.control_raw_u8 == control && record.stored_hash_raw_u32 == Hash(key) &&
            record.key_raw_full_id_u32 == key && record.vector_capacity_raw_i32 == static_cast<std::int32_t>(expected.size()) &&
            record.vector_allocator_matches_expected == true && record.vector_allocator_identity &&
            record.references.references_ready && record.references.count_raw_i32 == static_cast<std::int32_t>(expected.size()) &&
            record.references.occurrences.size() == expected.size(),
        "occupied record scalar/vector/allocator witness must retain demanded actual values");
  std::size_t i = 0;
  for (auto value : expected) {
    Check(record.references.occurrences[i].native_index == static_cast<std::int32_t>(i) &&
              record.references.occurrences[i].raw_full_id_u32 == value,
          "pending frame must preserve physical list order and duplicated DWORD references");
    ++i;
  }
}
void CheckArmyOperands(const game::ArmyPreDatePendingOccurrenceV1 &occurrence, std::uint32_t key,
                       bool existing) {
  Check(occurrence.ready && occurrence.raw_full_id_u32 == key && occurrence.pending_mutator_selected == true &&
            occurrence.pending_setup.target_army_full_id_u32 == key && occurrence.pending_setup.existing_key == existing &&
            occurrence.original_arrg_references.count_raw_i32 == 2 && occurrence.arrg_occurrences.size() == 2 &&
            occurrence.arrg_occurrences[0].append_to_pending == true && occurrence.arrg_occurrences[0].append_full_id_u32 == kRegA &&
            occurrence.arrg_occurrences[1].append_to_pending == false,
        "actual Army44=2 and m1 must come from production pending/current ArRg reads");
}
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
  std::ofstream output(directory / (std::string("pending-carry-growth-") + name + ".json"), std::ios::binary);
  output << wire << '\n'; Check(static_cast<bool>(output), "new carry/growth whole-strength wire write failed");
}
void ExactBinding() {
  constexpr std::uintptr_t base = 0x140000000;
  const auto b = ck3_12003::BindCurrentPreDatePendingUpdate12003(base, ck3_12003::kExecutableSha256);
  Check(b.common.enabled && b.native_empty_pending_buffer == reinterpret_cast<const void *>(base + 0x5D68BA0) &&
            b.expected_pending_vector_allocator == reinterpret_cast<const void *>(base + 0x54DEB68),
        "new pending constants must bind exact source-closed empty-buffer and vector allocator RVAs");
  Check(!ck3_12003::BindCurrentPreDatePendingUpdate12003(base, "wrong-build").common.enabled,
        "new pending frame must preserve existing exact-build binding boundary");
  Check((Hash(12U) & 7U) == 1U && (Hash(4U) & 7U) == 1U && (Hash(7U) & 7U) == 2U &&
            (Hash(6U) & 7U) == 3U && (Hash(1U) & 7U) == 4U && (Hash(15U) & 7U) == 2U,
        "new fixture keys must match frozen actual FNV physical homes");
}
void Scenes(const std::filesystem::path &directory) {
  ExactBinding();
  {
    Fixture f; f.Header(f.pending, 2, 7, 5, kThresholdNineTenths);
    f.memory.Put(f.Record(3), 4, std::uint8_t{0}); f.memory.Put(f.Record(4), 4, std::uint8_t{0});
    const auto rows = f.Observe(); const auto &frame = Frame(rows); CheckFrame(frame, 2, 7, 5, kThresholdNineTenths);
    CheckArmyOperands(Leaf(rows).occurrences[0], kArmyA, false);
    CheckValues(Physical(frame, 2), 7U, 1, {701U, 701U, 702U});
    Check(Physical(frame, 3).control_raw_u8 == 0 && frame.rehash_nonzero_records_observed_i32 == 2 &&
              f.memory.Attempts() == 0, "fastshift frame must expose actual resident value and immediate empty successor");
    Emit(directory, "fastshift", rows);
  }
  {
    Fixture f; const auto rows = f.Observe(); const auto &frame = Frame(rows);
    CheckFrame(frame, 4, 7, 5, kThresholdNineTenths); CheckArmyOperands(Leaf(rows).occurrences[0], kArmyA, false);
    CheckValues(Physical(frame, 1), 4U, 1, {601U}); CheckValues(Physical(frame, 2), 7U, 1, {701U, 701U, 702U});
    CheckValues(Physical(frame, 3), 6U, 1, {801U, 801U}); CheckValues(Physical(frame, 4), 1U, 1, {901U, 902U, 901U});
    Check(Physical(frame, 5).control_raw_u8 == 0 && frame.rehash_nonzero_records_observed_i32 == 4 &&
              f.memory.Attempts() == 0, "general two-swap frame must retain complete ordered duplicate resident values");
    Emit(directory, "general-two-swaps", rows);
  }
  {
    Fixture f; f.Header(f.pending, 4, 7, 5, kThresholdOneHalf);
    const auto rows = f.Observe(); const auto &frame = Frame(rows); CheckFrame(frame, 4, 7, 5, kThresholdOneHalf);
    CheckArmyOperands(Leaf(rows).occurrences[0], kArmyA, false);
    Check(frame.data_is_native_empty_buffer == false && frame.rehash_nonzero_records_observed_i32 == 4 &&
              Physical(frame, 0).control_raw_u8 == 0 && f.memory.Attempts() == 0,
          "initial density growth must expose actual count-driven physical old prefix and binary32 threshold");
    Emit(directory, "initial-density-growth", rows);
  }
  {
    Fixture f; f.Header(f.pending, 3, 7, 2, kThresholdNineTenths);
    f.PutRecord(3, 15U, 2, {801U, 801U}); f.memory.Put(f.Record(4), 4, std::uint8_t{0});
    f.memory.Put(f.pending, 10 * 0x28 + 4, std::uint8_t{0xFF});
    f.memory.Deny(f.pending, 10 * 0x28, 4); f.memory.Deny(f.pending, 10 * 0x28 + 8, 0x20);
    const auto rows = f.Observe(); const auto &frame = Frame(rows); CheckFrame(frame, 3, 7, 2, kThresholdNineTenths);
    CheckArmyOperands(Leaf(rows).occurrences[0], kArmyA, false);
    CheckValues(Physical(frame, 2), 7U, 1, {701U, 701U, 702U}); CheckValues(Physical(frame, 3), 15U, 2, {801U, 801U});
    Check(frame.rehash_nonzero_records_observed_i32 == 3 && f.memory.Attempts() == 0,
          "carried-overflow frame must expose real equal-distance resident and table tail2 for actual growth arm");
    Emit(directory, "carried-overflow-growth", rows);
  }
  {
    Fixture f; f.EmptyRecords(); f.Header(f.pending, 0, 7, 5, kThresholdNineTenths);
    f.Ids(static_cast<std::byte *>(f.manager) + 0x50, {kArmyA, kArmyA});
    const auto rows = f.Observe(); const auto &frame = Frame(rows); CheckFrame(frame, 0, 7, 5, kThresholdNineTenths);
    Check(Leaf(rows).occurrences.size() == 2 && frame.rehash_nonzero_records_observed_i32 == 0,
          "repeated new Army source must preserve both original occurrences and actual empty current map");
    for (const auto &occurrence : Leaf(rows).occurrences) CheckArmyOperands(occurrence, kArmyA, false);
    Check(f.memory.Attempts() == 0, "repeated current lookups must reuse frame without physical mutation");
    Emit(directory, "repeated-new-army", rows);
  }
  {
    Fixture f; f.Header(f.native_empty, 0, 0, 0, kThresholdNineTenths);
    const auto rows = f.Observe(); const auto &frame = Frame(rows); CheckFrame(frame, 0, 0, 0, kThresholdNineTenths);
    CheckArmyOperands(Leaf(rows).occurrences[0], kArmyA, false);
    Check(frame.data_is_native_empty_buffer == true && frame.rehash_nonzero_records_observed_i32 == 0 &&
              f.memory.Attempts() == 0,
          "actual current data equality must publish native empty-buffer fact without pointer helper/init or old value reads");
    Emit(directory, "native-empty-buffer", rows);
  }
  {
    Fixture f; f.Ids(static_cast<std::byte *>(f.manager) + 0x50, {kArmyEarlier, kArmyA});
    f.memory.Deny(f.Record(2), 0x20, 8);
    const auto rows = f.Observe(); const auto &leaf = Leaf(rows); const auto &frame = Frame(rows);
    Check(leaf.occurrences.size() == 2 && frame.physical_controls_complete && !frame.ready,
          "missing demanded resident vector must remain local readable partial frame while original source rows survive");
    CheckArmyOperands(leaf.occurrences[0], kArmyEarlier, true); CheckArmyOperands(leaf.occurrences[1], kArmyA, false);
    Check(leaf.occurrences[0].pending_setup.existing_references.references_ready &&
              leaf.occurrences[0].pending_setup.existing_references.count_raw_i32 == 1 &&
              leaf.occurrences[0].pending_setup.existing_references.occurrences[0].raw_full_id_u32 == 601U,
          "earlier existing Army must retain available source list before the later transfer failure");
    const auto &missing = Physical(frame, 2);
    Check(!missing.ready && missing.key_raw_full_id_u32 == 7U && missing.stored_hash_raw_u32 == Hash(7U) &&
              !missing.vector_allocator_matches_expected && !missing.vector_allocator_identity &&
              missing.vector_capacity_raw_i32 == 3 && missing.references.count_raw_i32 == 3 &&
              missing.references.references_ready && missing.references.occurrences.size() == 3 &&
              missing.references.occurrences[0].raw_full_id_u32 == 701U &&
              missing.references.occurrences[1].raw_full_id_u32 == 701U &&
              missing.references.occurrences[2].raw_full_id_u32 == 702U && f.memory.Attempts() == 1,
          "actual failed vector allocator read must preserve known raw count/ordered values while required transfer witness stays unknown");
    Emit(directory, "missing-vector-transfer", rows);
  }
  {
    Fixture f; f.EmptyRecords(); f.PutRecord(1, kArmyA, 1, {}); f.Header(f.pending, 1, 7, 5, kThresholdNineTenths);
    f.bindings.current_pre_date_pending_update_bindings.native_empty_pending_buffer = nullptr;
    f.bindings.current_pre_date_pending_update_bindings.expected_pending_vector_allocator = nullptr;
    const auto rows = f.Observe(false); const auto &leaf = Leaf(rows);
    CheckArmyOperands(leaf.occurrences[0], kArmyA, true);
    Check(!leaf.pending_table_frame_v1 && leaf.occurrences[0].pending_setup.existing_references.count_raw_i32 == 0 &&
              leaf.occurrences[0].pending_setup.existing_references.references_ready && f.memory.Attempts() == 0,
          "new fixture frame-free source must preserve original qualified existing-key family path");
    Emit(directory, "legacy-frame-free", rows);
  }
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 3 || std::string_view(argv[1]) != "--wire-dir") {
    std::cerr << "usage: xar_bridge_ck3_12003_pre_date_pending_carry_growth_test --wire-dir DIRECTORY\n";
    return 2;
  }
  try {
    const std::filesystem::path directory(argv[2]); std::filesystem::create_directories(directory);
    Scenes(directory);
    std::cout << "pre-date pending carry/growth production memory fixture GREEN: 8 new whole-strength wires\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "pre-date pending carry/growth fixture RED: " << error.what() << '\n'; return 1;
  }
}
