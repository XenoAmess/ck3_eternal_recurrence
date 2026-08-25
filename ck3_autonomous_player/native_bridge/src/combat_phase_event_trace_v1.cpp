#include "xar_bridge/combat_phase_event_trace_v1.hpp"

#include "xar_bridge/ck3_11906.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <exception>
#include <limits>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace xar::ck3_11906 {
namespace {

constexpr std::uintptr_t kPhaseEventDatabaseSlotRva = 0x57C7930;
constexpr std::uintptr_t kNullPhaseEventSlotRva = 0x57C7940;
constexpr std::uintptr_t kCombatSideScopeKeyIdRva = 0x57EB630;
constexpr std::uintptr_t kCurrentDateSlotRva = 0x570E068;
constexpr std::uintptr_t kCombatEventDaysRva = 0x570EF9C;
constexpr std::uintptr_t kGlobalRngWrapperSlotRva = 0x4FEB1C8;
constexpr std::uintptr_t kBattleResultStorageSlotRva = 0x57C0328;
constexpr std::uintptr_t kBattleResultFallbackSlotRva = 0x57C0320;
constexpr std::uintptr_t kBattleEventVtableRva = 0x41461A0;

constexpr std::uintptr_t kConstructEventTargetScopeRva = 0x81F190;
constexpr std::uintptr_t kInsertNamedEventTargetRva = 0x3358160;
constexpr std::uintptr_t kEvaluateTriggerRva = 0x334C510;
constexpr std::uintptr_t kEvaluateValueRva = 0x337B210;
constexpr std::uintptr_t kDestroyEventTargetTailRva = 0x81E900;
constexpr std::uintptr_t kDestroyEventTargetRows48Rva = 0x81E980;

constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageObjectOffset = 0x08;
constexpr std::int32_t kMaximumComponents = 4'194'304;
constexpr std::int32_t kMaximumRows = 65'536;
constexpr std::size_t kMaximumKeyBytes = 512;

constexpr std::size_t kCombatIdOffset = 0x08;
constexpr std::size_t kCombatSide0Offset = 0x20;
constexpr std::size_t kCombatSide1Offset = 0x368;
constexpr std::size_t kCombatPhaseOffset = 0x6B0;
constexpr std::size_t kCombatPhaseDayOffset = 0x6B4;
constexpr std::size_t kCombatTargetProvinceOffset = 0x6B8;
constexpr std::size_t kCombatWinnerOffset = 0x6E0;
constexpr std::size_t kCombatBattleResultIdOffset = 0x708;

constexpr std::size_t kSideArmyIdsOffset = 0x10;
constexpr std::size_t kSideArmyIdCountOffset = 0x1C;
constexpr std::size_t kSideKnightEntriesOffset = 0x40;
constexpr std::size_t kSideKnightEntryCountOffset = 0x4C;
constexpr std::size_t kSideSelectedCommanderOffset = 0x74;
constexpr std::size_t kSideCombatBackPointerOffset = 0xB8;
constexpr std::size_t kSideScheduledKnightRowsOffset = 0xD8;
constexpr std::size_t kSideScheduledKnightCountOffset = 0xE4;
constexpr std::size_t kSideScheduledCommanderOffset = 0xF0;
constexpr std::size_t kSideKnightEntryStride = 0x60;
constexpr std::size_t kSideScheduledKnightStride = 0x10;

constexpr std::size_t kInternalArmyIdOffset = 0x10;
constexpr std::size_t kInternalArmyCommanderOffset = 0x120;
constexpr std::size_t kInternalArmyCombatIdOffset = 0x128;
constexpr std::size_t kRegimentIdOffset = 0x10;
constexpr std::size_t kRegimentArmyIdOffset = 0x140;
constexpr std::size_t kRegimentKnightCharacterIdOffset = 0x148;
constexpr std::size_t kCharacterIdOffset = 0x18;
constexpr std::size_t kCharacterMartialOffset = 0xD8;
constexpr std::size_t kCharacterLearningOffset = 0xE4;
constexpr std::size_t kCharacterProwessOffset = 0xE8;
constexpr std::size_t kCharacterRegimentLinkOffset = 0x1B0;
constexpr std::size_t kCharacterDeathMarkerOffset = 0x1C8;
constexpr std::size_t kCharacterLinkRegimentIdOffset = 0xF8;

constexpr std::size_t kBattleResultIdOffset = 0x08;
constexpr std::size_t kBattleEventRowsOffset = 0x188;
constexpr std::size_t kBattleEventRowsDataOffset = 0x00;
constexpr std::size_t kBattleEventRowsCapacityOffset = 0x08;
constexpr std::size_t kBattleEventRowsCountOffset = 0x0C;
constexpr std::size_t kBattleEventRowStride = 0x38;
constexpr std::size_t kBattleEventLeftCharacterOffset = 0x08;
constexpr std::size_t kBattleEventRightCharacterOffset = 0x0C;
constexpr std::size_t kBattleEventStableKeyOffset = 0x10;
constexpr std::size_t kBattleEventTypeOffset = 0x30;
constexpr std::size_t kBattleEventSide0Offset = 0x34;
constexpr std::size_t kBattleEventTargetRightOffset = 0x35;

constexpr std::size_t kPhaseEventStableKeyOffset = 0x18;
constexpr std::size_t kPhaseEventTriggerOffset = 0x38;
constexpr std::size_t kPhaseEventChanceOffset = 0x118;
constexpr std::size_t kPhaseEventEmptyEffectOffset = 0x1C4;
constexpr std::size_t kPhaseEventTypeOffset = 0x1D8;
constexpr std::size_t kPhaseEventDatabaseRowsOffset = 0x68;
constexpr std::size_t kPhaseEventDatabaseRowCountOffset = 0x74;

constexpr std::size_t kEventTargetScopeSize = 0x168;
constexpr std::size_t kEventTargetNamedRowsOffset = 0x18;
constexpr std::size_t kEventTargetNamedRowsCapacityOffset = 0x20;
constexpr std::size_t kEventTargetNamedRowsCountOffset = 0x24;
constexpr std::size_t kEventTargetNamedRowsAllocatorOffset = 0x28;
constexpr std::size_t kEventTargetRows48Offset = 0x100;
constexpr std::size_t kEventTargetRows48CapacityOffset = 0x108;
constexpr std::size_t kEventTargetRows48CountOffset = 0x10C;
constexpr std::size_t kEventTargetRows48AllocatorOffset = 0x110;
constexpr std::size_t kEventTargetTailOffset = 0x118;

constexpr std::uint16_t kCharacterEventTargetKind = 4;
constexpr std::uint16_t kCombatSideEventTargetKind = 11;
constexpr std::int32_t kDateEpochRaw = 0x029C55A8;
constexpr std::int32_t kDateUnitsPerDay = 24;
constexpr std::uint32_t kExpectedCombatEventDays = 5;

constexpr std::array<bool, 13> kExpectedEmptyEffects{
    true,  false, false, false, true,  false, false,
    false, false, false, false, false, false,
};

template <typename T> T LoadAt(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset,
              sizeof(value));
  return value;
}

template <typename T>
void StoreAt(void *base, std::size_t offset, T value) noexcept {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}

std::uintptr_t ModuleBase() noexcept {
  return reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
}

bool ValidSpan(const void *data, std::int32_t count,
               std::int32_t maximum = kMaximumRows) noexcept {
  return count >= 0 && count <= maximum && (count == 0 || data != nullptr);
}

void *ResolveStoredComponent(void **storage_slot, std::int32_t full_id,
                             std::size_t identity_offset) noexcept {
  if (storage_slot == nullptr || full_id == -1) {
    return nullptr;
  }
  void *const storage = *storage_slot;
  if (storage == nullptr) {
    return nullptr;
  }
  void *const slots = LoadAt<void *>(storage, kStorageSlotsOffset);
  const auto capacity = LoadAt<std::int32_t>(storage, kStorageCapacityOffset);
  const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 || capacity > kMaximumComponents ||
      index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  void *const object = LoadAt<void *>(slots, static_cast<std::size_t>(index) *
                                                     kStorageSlotStride +
                                                 kStorageObjectOffset);
  if (object == nullptr ||
      LoadAt<std::int32_t>(object, identity_offset) != full_id) {
    return nullptr;
  }
  return object;
}

bool ReadMsvcString(const void *storage, std::string &output) noexcept {
  if (storage == nullptr) {
    return false;
  }
  const auto size = LoadAt<std::size_t>(storage, 0x10);
  const auto capacity = LoadAt<std::size_t>(storage, 0x18);
  if (size > capacity || size > kMaximumKeyBytes) {
    return false;
  }
  const char *const data = capacity < 16 ? static_cast<const char *>(storage)
                                         : LoadAt<const char *>(storage, 0);
  if (size != 0 && data == nullptr) {
    return false;
  }
  output.assign(data == nullptr ? "" : data, size);
  return true;
}

using BoolPredicate = bool (*)(void *);

bool VcallBool(void *object, std::size_t slot_offset, bool &value) noexcept {
  if (object == nullptr) {
    return false;
  }
  void *const vtable = LoadAt<void *>(object, 0);
  const auto function = vtable == nullptr
                            ? std::uintptr_t{0}
                            : LoadAt<std::uintptr_t>(vtable, slot_offset);
  if (function == 0) {
    return false;
  }
  value = reinterpret_cast<BoolPredicate>(function)(object);
  return true;
}

struct NativePhaseEventRow {
  void *object = nullptr;
  std::string key;
  std::int32_t type = -1;
  bool empty_effect = false;
};

struct NativePhaseEventTable {
  void *database = nullptr;
  void *row_data = nullptr;
  std::array<NativePhaseEventRow, 13> rows;
};

bool ReadNativePhaseEventTable(std::uintptr_t module,
                               NativePhaseEventTable &output,
                               bool &table_mismatch) noexcept {
  output = {};
  table_mismatch = false;
  if (module == 0) {
    return false;
  }
  // Deliberately load the initialized singleton slot.  Calling 0x23CEB10
  // would lazily initialize it and would violate this query's read-only
  // boundary.
  output.database =
      *reinterpret_cast<void **>(module + kPhaseEventDatabaseSlotRva);
  if (output.database == nullptr) {
    return false;
  }
  output.row_data =
      LoadAt<void *>(output.database, kPhaseEventDatabaseRowsOffset);
  const auto count =
      LoadAt<std::int32_t>(output.database, kPhaseEventDatabaseRowCountOffset);
  if (!ValidSpan(output.row_data, count) ||
      count != kCombatPhaseEventTraceV1RowCount) {
    table_mismatch = true;
    return false;
  }
  for (std::size_t index = 0; index < output.rows.size(); ++index) {
    auto &row = output.rows[index];
    row.object = LoadAt<void *>(output.row_data, index * sizeof(void *));
    if (row.object == nullptr ||
        !ReadMsvcString(static_cast<std::byte *>(row.object) +
                            kPhaseEventStableKeyOffset,
                        row.key)) {
      table_mismatch = true;
      return false;
    }
    row.type = LoadAt<std::int32_t>(row.object, kPhaseEventTypeOffset);
    row.empty_effect =
        LoadAt<std::int32_t>(row.object, kPhaseEventEmptyEffectOffset) == 0;
    if (row.key != kCombatPhaseEventTraceV1StockKeys[index] ||
        row.type != kCombatPhaseEventTraceV1StockTypes[index] ||
        row.empty_effect != kExpectedEmptyEffects[index]) {
      table_mismatch = true;
      return false;
    }
    for (std::size_t previous = 0; previous < index; ++previous) {
      if (output.rows[previous].object == row.object ||
          output.rows[previous].key == row.key) {
        table_mismatch = true;
        return false;
      }
    }
  }
  return true;
}

bool RevalidateNativePhaseEventTable(
    std::uintptr_t module, const NativePhaseEventTable &expected) noexcept {
  NativePhaseEventTable current{};
  bool table_mismatch = false;
  if (!ReadNativePhaseEventTable(module, current, table_mismatch) ||
      current.database != expected.database ||
      current.row_data != expected.row_data) {
    return false;
  }
  for (std::size_t index = 0; index < current.rows.size(); ++index) {
    if (current.rows[index].object != expected.rows[index].object ||
        current.rows[index].key != expected.rows[index].key ||
        current.rows[index].type != expected.rows[index].type ||
        current.rows[index].empty_effect != expected.rows[index].empty_effect) {
      return false;
    }
  }
  return true;
}

struct NativeEventTargetToken {
  std::uint16_t kind = 0;
  std::uint16_t subtype = 0;
  std::uint32_t reserved = 0;
  std::int64_t payload = 0;
};
static_assert(sizeof(NativeEventTargetToken) == 0x10);

using ConstructEventTargetScope = void *(*)(void *);
using InsertNamedEventTarget = void *(*)(void *, std::int32_t,
                                         const NativeEventTargetToken *);
using DestroyEventTargetPart = void (*)(void *);
using DeallocateEventTargetRows = void (*)(void *, void *, std::size_t);

bool DeallocateRows(void *scope, std::size_t data_offset,
                    std::size_t capacity_offset, std::size_t count_offset,
                    std::size_t allocator_offset,
                    bool destroy_rows48) noexcept {
  void *const data = LoadAt<void *>(scope, data_offset);
  const auto count = LoadAt<std::int32_t>(scope, count_offset);
  if (!ValidSpan(data, count)) {
    return false;
  }
  if (data == nullptr) {
    return count == 0;
  }
  if (destroy_rows48) {
    reinterpret_cast<DestroyEventTargetPart>(ModuleBase() +
                                             kDestroyEventTargetRows48Rva)(
        static_cast<std::byte *>(scope) + data_offset);
  }
  void *const allocator = LoadAt<void *>(scope, allocator_offset);
  void *const vtable =
      allocator == nullptr ? nullptr : LoadAt<void *>(allocator, 0);
  const auto deallocate = vtable == nullptr
                              ? std::uintptr_t{0}
                              : LoadAt<std::uintptr_t>(vtable, 0x10);
  if (deallocate == 0) {
    return false;
  }
  StoreAt<std::int32_t>(scope, count_offset, 0);
  reinterpret_cast<DeallocateEventTargetRows>(deallocate)(allocator, data, 8);
  StoreAt<void *>(scope, data_offset, nullptr);
  StoreAt<std::int32_t>(scope, capacity_offset, 0);
  return LoadAt<void *>(scope, data_offset) == nullptr &&
         LoadAt<std::int32_t>(scope, capacity_offset) == 0 &&
         LoadAt<std::int32_t>(scope, count_offset) == 0;
}

class NativeEventTargetScope final {
public:
  NativeEventTargetScope() = default;
  NativeEventTargetScope(const NativeEventTargetScope &) = delete;
  NativeEventTargetScope &operator=(const NativeEventTargetScope &) = delete;

  ~NativeEventTargetScope() {
    if (constructed_ && !cleaned_) {
      (void)CleanupChecked();
    }
  }

  bool Construct(std::uintptr_t module, std::int32_t character_id, void *side,
                 void *combat) noexcept {
    if (module == 0 || character_id <= 0 || side == nullptr ||
        combat == nullptr ||
        LoadAt<void *>(side, kSideCombatBackPointerOffset) != combat) {
      return false;
    }
    module_ = module;
    reinterpret_cast<ConstructEventTargetScope>(
        module + kConstructEventTargetScopeRva)(storage_.data());
    constructed_ = true;

    StoreAt<std::uint16_t>(storage_.data(), 0, kCharacterEventTargetKind);
    StoreAt<std::uint64_t>(
        storage_.data(), 0x08,
        static_cast<std::uint64_t>(static_cast<std::uint32_t>(character_id)));

    NativeEventTargetToken combat_side{};
    combat_side.kind = kCombatSideEventTargetKind;
    combat_side.subtype =
        side == static_cast<std::byte *>(combat) + kCombatSide0Offset ? 0 : 1;
    combat_side.payload = static_cast<std::int64_t>(
        LoadAt<std::int32_t>(combat, kCombatIdOffset));
    const auto key_id = *reinterpret_cast<const std::int32_t *>(
        module + kCombatSideScopeKeyIdRva);
    if (key_id < 0) {
      return false;
    }
    reinterpret_cast<InsertNamedEventTarget>(module +
                                             kInsertNamedEventTargetRva)(
        storage_.data() + kEventTargetNamedRowsOffset, key_id, &combat_side);
    return LoadAt<std::int32_t>(storage_.data(),
                                kEventTargetNamedRowsCountOffset) == 1;
  }

  void *data() noexcept { return storage_.data(); }

  bool CleanupChecked() noexcept {
    if (!constructed_) {
      return false;
    }
    if (cleaned_) {
      return cleanup_ok_;
    }
    cleaned_ = true;
    if (module_ == 0) {
      return false;
    }

    // Exact stock-selector teardown order: tail first, then the 0x48-stride
    // polymorphic rows, then the trivially destructible named-target rows.
    reinterpret_cast<DestroyEventTargetPart>(
        module_ + kDestroyEventTargetTailRva)(storage_.data() +
                                              kEventTargetTailOffset);
    const bool rows48_ok = DeallocateRows(
        storage_.data(), kEventTargetRows48Offset,
        kEventTargetRows48CapacityOffset, kEventTargetRows48CountOffset,
        kEventTargetRows48AllocatorOffset, true);
    const bool named_ok = DeallocateRows(
        storage_.data(), kEventTargetNamedRowsOffset,
        kEventTargetNamedRowsCapacityOffset, kEventTargetNamedRowsCountOffset,
        kEventTargetNamedRowsAllocatorOffset, false);
    cleanup_ok_ = rows48_ok && named_ok;
    return cleanup_ok_;
  }

private:
  alignas(16) std::array<std::byte, kEventTargetScopeSize> storage_{};
  std::uintptr_t module_ = 0;
  bool constructed_ = false;
  bool cleaned_ = false;
  bool cleanup_ok_ = false;
};

using EvaluateTrigger = bool (*)(const void *, const void *);
using EvaluateValue = std::int64_t *(*)(const void *, std::int64_t *,
                                        const void *);

bool EvaluateCharacterRows(
    std::uintptr_t module, const NativePhaseEventTable &table, void *combat,
    void *side, bool selected_commander_role, bool knight_role,
    std::int32_t character_id,
    std::array<game::CombatPhaseEventNativeRowV1, 13> &output,
    bool &teardown_complete) noexcept {
  teardown_complete = false;
  NativeEventTargetScope scope;
  if (!scope.Construct(module, character_id, side, combat)) {
    return false;
  }
  const auto evaluate_trigger =
      reinterpret_cast<EvaluateTrigger>(module + kEvaluateTriggerRva);
  const auto evaluate_value =
      reinterpret_cast<EvaluateValue>(module + kEvaluateValueRva);

  bool evaluated = true;
  for (std::size_t index = 0; index < table.rows.size(); ++index) {
    const auto &native = table.rows[index];
    auto &row = output[index];
    row.global_load_index = static_cast<std::int32_t>(index);
    row.type_load_index = kCombatPhaseEventTraceV1TypeLoadIndices[index];
    row.event_key = native.key;
    row.event_type = native.type == 0 ? "commander" : "knight";
    row.empty_effect = native.empty_effect;
    row.selector_role_applicable =
        native.type == 0 ? selected_commander_role : knight_role;
    row.trigger_valid = evaluate_trigger(
        static_cast<std::byte *>(native.object) + kPhaseEventTriggerOffset,
        scope.data());

    std::int64_t chance_raw = 0;
    std::int64_t *const returned = evaluate_value(
        static_cast<std::byte *>(native.object) + kPhaseEventChanceOffset,
        &chance_raw, scope.data());
    if (returned == nullptr) {
      evaluated = false;
      break;
    }
    chance_raw = *returned;
    const auto quotient = chance_raw / kCombatPhaseEventTraceV1FixedScale;
    if (quotient < std::numeric_limits<std::int32_t>::min() ||
        quotient > std::numeric_limits<std::int32_t>::max()) {
      evaluated = false;
      break;
    }
    row.chance_evaluated_for_differential = true;
    row.selector_would_evaluate_chance =
        row.selector_role_applicable && row.trigger_valid;
    row.chance_raw = chance_raw;
    row.int_weight = static_cast<std::int32_t>(quotient);
    row.positive_weight = row.int_weight > 0;
    row.selector_eligible =
        row.selector_would_evaluate_chance && row.positive_weight;
  }
  teardown_complete = scope.CleanupChecked();
  return evaluated && teardown_complete;
}

struct NativeCombatCore {
  void *combat = nullptr;
  void *target_province = nullptr;
  std::int32_t combat_id = -1;
  std::int32_t target_province_id = -1;
  std::int32_t phase = -1;
  std::int32_t phase_day = -1;
  std::int32_t winner = -2;

  friend bool operator==(const NativeCombatCore &,
                         const NativeCombatCore &) = default;
};

bool ReadCombatCore(const Bindings &bindings, std::int32_t combat_id,
                    NativeCombatCore &output) noexcept {
  output = {};
  output.combat_id = combat_id;
  output.combat = ResolveStoredComponent(bindings.combat_storage_slot,
                                         combat_id, kCombatIdOffset);
  if (output.combat == nullptr) {
    return false;
  }
  output.target_province =
      LoadAt<void *>(output.combat, kCombatTargetProvinceOffset);
  if (output.target_province == nullptr) {
    return false;
  }
  output.target_province_id =
      LoadAt<std::int32_t>(output.target_province, 0x10);
  output.phase = LoadAt<std::int32_t>(output.combat, kCombatPhaseOffset);
  output.phase_day = LoadAt<std::int32_t>(output.combat, kCombatPhaseDayOffset);
  output.winner = LoadAt<std::int32_t>(output.combat, kCombatWinnerOffset);
  return output.target_province_id >= 0 && output.phase >= 0 &&
         output.phase <= 3 && output.phase_day >= 0 &&
         (output.winner == -1 || output.winner == 0 || output.winner == 1);
}

std::string PhaseName(std::int32_t phase) {
  switch (phase) {
  case 0:
    return "maneuver";
  case 1:
    return "main";
  case 2:
    return "pursuit";
  case 3:
    return "done";
  default:
    return "invalid";
  }
}

bool ContainsArmyObject(
    const std::vector<std::pair<std::int32_t, void *>> &rows, std::int32_t id,
    const void *object) noexcept {
  return std::any_of(rows.begin(), rows.end(), [id, object](const auto &row) {
    return row.first == id && row.second == object;
  });
}

std::int32_t EventIndexForObject(const NativePhaseEventTable &table,
                                 const void *event) noexcept {
  for (std::size_t index = 0; index < table.rows.size(); ++index) {
    if (table.rows[index].object == event) {
      return static_cast<std::int32_t>(index);
    }
  }
  return -1;
}

struct NativeSideRead {
  void *side = nullptr;
  std::vector<std::pair<std::int32_t, void *>> armies;
  game::CombatPhaseEventSideTraceV1 wire;
};

bool ReadSideRosterAndSchedule(const Bindings &bindings, std::uintptr_t module,
                               const NativeCombatCore &core,
                               const NativePhaseEventTable &table,
                               std::int32_t side_index, NativeSideRead &output,
                               bool &roster_failed,
                               bool &schedule_failed) noexcept {
  output = {};
  roster_failed = false;
  schedule_failed = false;
  output.side = static_cast<std::byte *>(core.combat) +
                (side_index == 0 ? kCombatSide0Offset : kCombatSide1Offset);
  output.wire.side_index = side_index;
  output.wire.is_attacker = side_index == 0;
  if (LoadAt<void *>(output.side, kSideCombatBackPointerOffset) !=
      core.combat) {
    roster_failed = true;
    return false;
  }

  void *const army_ids = LoadAt<void *>(output.side, kSideArmyIdsOffset);
  const auto army_count =
      LoadAt<std::int32_t>(output.side, kSideArmyIdCountOffset);
  if (!ValidSpan(army_ids, army_count, 4'096)) {
    roster_failed = true;
    return false;
  }
  output.armies.reserve(static_cast<std::size_t>(army_count));
  output.wire.ordered_army_ids.reserve(static_cast<std::size_t>(army_count));
  output.wire.ordered_commander_slots.reserve(
      static_cast<std::size_t>(army_count));
  for (std::int32_t index = 0; index < army_count; ++index) {
    const auto army_id =
        LoadAt<std::int32_t>(army_ids, static_cast<std::size_t>(index) * 4);
    void *const army = ResolveStoredComponent(
        bindings.army_internal_storage_slot, army_id, kInternalArmyIdOffset);
    if (army == nullptr ||
        LoadAt<std::int32_t>(army, kInternalArmyCombatIdOffset) !=
            core.combat_id ||
        std::any_of(
            output.armies.begin(), output.armies.end(),
            [army_id](const auto &row) { return row.first == army_id; })) {
      roster_failed = true;
      return false;
    }
    output.armies.emplace_back(army_id, army);
    output.wire.ordered_army_ids.push_back(army_id);
    game::CombatPhaseEventCommanderSlotV1 commander{};
    commander.source_army_id = army_id;
    const auto character_id =
        LoadAt<std::int32_t>(army, kInternalArmyCommanderOffset);
    if (character_id != -1) {
      if (character_id <= 0 ||
          ResolveStoredComponent(bindings.character_storage_slot, character_id,
                                 kCharacterIdOffset) == nullptr) {
        roster_failed = true;
        return false;
      }
      commander.character = {true, character_id};
      output.wire.ordered_commander_character_ids.push_back(character_id);
    }
    output.wire.ordered_commander_slots.push_back(commander);
  }

  void *const knight_entries =
      LoadAt<void *>(output.side, kSideKnightEntriesOffset);
  const auto knight_count =
      LoadAt<std::int32_t>(output.side, kSideKnightEntryCountOffset);
  if (!ValidSpan(knight_entries, knight_count, 4'096)) {
    roster_failed = true;
    return false;
  }
  output.wire.ordered_knight_slots.reserve(
      static_cast<std::size_t>(knight_count));
  for (std::int32_t index = 0; index < knight_count; ++index) {
    const auto *const entry =
        static_cast<const std::byte *>(knight_entries) +
        static_cast<std::size_t>(index) * kSideKnightEntryStride;
    const auto regiment_id = LoadAt<std::int32_t>(entry, 0x08);
    void *const regiment = ResolveStoredComponent(
        bindings.regiment_storage_slot, regiment_id, kRegimentIdOffset);
    if (regiment == nullptr) {
      roster_failed = true;
      return false;
    }
    const auto army_id = LoadAt<std::int32_t>(regiment, kRegimentArmyIdOffset);
    void *const army = ResolveStoredComponent(
        bindings.army_internal_storage_slot, army_id, kInternalArmyIdOffset);
    if (army == nullptr || !ContainsArmyObject(output.armies, army_id, army) ||
        LoadAt<std::int32_t>(army, kInternalArmyCombatIdOffset) !=
            core.combat_id) {
      roster_failed = true;
      return false;
    }
    game::CombatPhaseEventKnightSlotV1 slot{};
    slot.source_regiment_id = regiment_id;
    slot.source_army_id = army_id;
    const auto character_id =
        LoadAt<std::int32_t>(regiment, kRegimentKnightCharacterIdOffset);
    if (character_id != -1) {
      if (character_id <= 0 ||
          ResolveStoredComponent(bindings.character_storage_slot, character_id,
                                 kCharacterIdOffset) == nullptr) {
        roster_failed = true;
        return false;
      }
      slot.character = {true, character_id};
      output.wire.ordered_knight_character_ids.push_back(character_id);
    }
    output.wire.ordered_knight_slots.push_back(slot);
  }

  const auto selected_commander =
      LoadAt<std::int32_t>(output.side, kSideSelectedCommanderOffset);
  if (selected_commander != -1) {
    if (selected_commander <= 0 ||
        ResolveStoredComponent(bindings.character_storage_slot,
                               selected_commander,
                               kCharacterIdOffset) == nullptr ||
        std::find(output.wire.ordered_commander_character_ids.begin(),
                  output.wire.ordered_commander_character_ids.end(),
                  selected_commander) ==
            output.wire.ordered_commander_character_ids.end()) {
      roster_failed = true;
      return false;
    }
    output.wire.selected_commander = {true, selected_commander};
  }

  void *const null_event =
      *reinterpret_cast<void **>(module + kNullPhaseEventSlotRva);
  if (null_event == nullptr) {
    schedule_failed = true;
    return false;
  }
  void *const scheduled_knights =
      LoadAt<void *>(output.side, kSideScheduledKnightRowsOffset);
  const auto scheduled_knight_count =
      LoadAt<std::int32_t>(output.side, kSideScheduledKnightCountOffset);
  if (!ValidSpan(scheduled_knights, scheduled_knight_count, 4'096)) {
    schedule_failed = true;
    return false;
  }
  output.wire.retained_nonempty_schedule_rows.reserve(
      static_cast<std::size_t>(scheduled_knight_count) + 1);
  for (std::int32_t index = 0; index < scheduled_knight_count; ++index) {
    const auto *const row =
        static_cast<const std::byte *>(scheduled_knights) +
        static_cast<std::size_t>(index) * kSideScheduledKnightStride;
    void *const event = LoadAt<void *>(row, 0);
    const auto event_index = EventIndexForObject(table, event);
    const auto regiment_id = LoadAt<std::int32_t>(row, 0x08);
    if (event == null_event || event_index < 0 ||
        table.rows[static_cast<std::size_t>(event_index)].type != 1 ||
        table.rows[static_cast<std::size_t>(event_index)].empty_effect) {
      schedule_failed = true;
      return false;
    }
    void *const regiment = ResolveStoredComponent(
        bindings.regiment_storage_slot, regiment_id, kRegimentIdOffset);
    if (regiment == nullptr) {
      schedule_failed = true;
      return false;
    }
    const auto army_id = LoadAt<std::int32_t>(regiment, kRegimentArmyIdOffset);
    void *const army = ResolveStoredComponent(
        bindings.army_internal_storage_slot, army_id, kInternalArmyIdOffset);
    if (army == nullptr || !ContainsArmyObject(output.armies, army_id, army)) {
      schedule_failed = true;
      return false;
    }
    game::CombatPhaseEventRetainedScheduleRowV1 schedule{};
    schedule.side_index = side_index;
    schedule.retained_order = index;
    schedule.dispatch_role = "knight";
    schedule.event_key = table.rows[static_cast<std::size_t>(event_index)].key;
    schedule.source_regiment = {true, regiment_id};
    const auto character_id =
        LoadAt<std::int32_t>(regiment, kRegimentKnightCharacterIdOffset);
    if (character_id != -1) {
      if (character_id <= 0 ||
          ResolveStoredComponent(bindings.character_storage_slot, character_id,
                                 kCharacterIdOffset) == nullptr) {
        schedule_failed = true;
        return false;
      }
      schedule.current_character = {true, character_id};
    }
    schedule.current_combat_association_matches =
        LoadAt<std::int32_t>(army, kInternalArmyCombatIdOffset) ==
        core.combat_id;
    output.wire.retained_nonempty_schedule_rows.push_back(std::move(schedule));
  }

  void *const commander_event =
      LoadAt<void *>(output.side, kSideScheduledCommanderOffset);
  if (commander_event == null_event) {
    output.wire.retained_commander_schedule_state =
        "sentinel_no_nonempty_commander_row";
  } else {
    const auto event_index = EventIndexForObject(table, commander_event);
    if (event_index < 0 ||
        table.rows[static_cast<std::size_t>(event_index)].type != 0 ||
        table.rows[static_cast<std::size_t>(event_index)].empty_effect) {
      schedule_failed = true;
      return false;
    }
    game::CombatPhaseEventRetainedScheduleRowV1 schedule{};
    schedule.side_index = side_index;
    schedule.retained_order = scheduled_knight_count;
    schedule.dispatch_role = "commander";
    schedule.event_key = table.rows[static_cast<std::size_t>(event_index)].key;
    schedule.current_character = output.wire.selected_commander;
    schedule.current_combat_association_matches =
        output.wire.selected_commander.present;
    output.wire.retained_nonempty_schedule_rows.push_back(std::move(schedule));
    output.wire.retained_commander_schedule_state =
        "retained_nonempty_commander_row";
  }
  return true;
}

bool ReadRetainedBattleEvents(
    const Bindings &bindings, std::uintptr_t module,
    const NativeCombatCore &core,
    game::CombatPhaseBattleEventLedgerV1 &output) noexcept {
  output = {};
  if (module == 0 || core.combat == nullptr) {
    return false;
  }
  const auto battle_result_id =
      LoadAt<std::int32_t>(core.combat, kCombatBattleResultIdOffset);
  if (battle_result_id == -1) {
    return false;
  }
  void *const battle_result = ResolveStoredComponent(
      reinterpret_cast<void **>(module + kBattleResultStorageSlotRva),
      battle_result_id, kBattleResultIdOffset);
  void *const fallback =
      *reinterpret_cast<void **>(module + kBattleResultFallbackSlotRva);
  if (battle_result == nullptr || battle_result == fallback) {
    return false;
  }

  const auto *const container =
      static_cast<const std::byte *>(battle_result) + kBattleEventRowsOffset;
  void *const rows = LoadAt<void *>(container, kBattleEventRowsDataOffset);
  const auto capacity =
      LoadAt<std::int32_t>(container, kBattleEventRowsCapacityOffset);
  const auto count =
      LoadAt<std::int32_t>(container, kBattleEventRowsCountOffset);
  if (!ValidSpan(rows, count) || capacity < 0 || capacity > kMaximumRows ||
      count > capacity) {
    return false;
  }

  output.battle_result = {true, battle_result_id};
  output.storage_identity_matches = true;
  output.retained_rows.reserve(static_cast<std::size_t>(count));
  const auto expected_vtable = module + kBattleEventVtableRva;
  for (std::int32_t index = 0; index < count; ++index) {
    const auto *const native =
        static_cast<const std::byte *>(rows) +
        static_cast<std::size_t>(index) * kBattleEventRowStride;
    if (LoadAt<std::uintptr_t>(native, 0) != expected_vtable) {
      return false;
    }
    game::CombatPhaseRetainedBattleEventV1 row{};
    row.retained_order = index;
    const auto left =
        LoadAt<std::int32_t>(native, kBattleEventLeftCharacterOffset);
    const auto right =
        LoadAt<std::int32_t>(native, kBattleEventRightCharacterOffset);
    if (!ReadMsvcString(native + kBattleEventStableKeyOffset, row.stable_key) ||
        row.stable_key.empty()) {
      return false;
    }
    if (left != -1) {
      if (ResolveStoredComponent(bindings.character_storage_slot, left,
                                 kCharacterIdOffset) == nullptr) {
        return false;
      }
      row.left_character = {true, left};
    }
    if (right != -1) {
      if (ResolveStoredComponent(bindings.character_storage_slot, right,
                                 kCharacterIdOffset) == nullptr) {
        return false;
      }
      row.right_character = {true, right};
    }
    row.type_raw = LoadAt<std::int32_t>(native, kBattleEventTypeOffset);
    const bool side0 =
        LoadAt<std::uint8_t>(native, kBattleEventSide0Offset) != 0;
    row.side_index = side0 ? 0 : 1;
    row.is_attacker_side = side0;
    row.target_right =
        LoadAt<std::uint8_t>(native, kBattleEventTargetRightOffset) != 0;
    row.character_identities_resolve = true;
    output.retained_rows.push_back(std::move(row));
  }
  output.retained_storage_reader_ready =
      ResolveStoredComponent(
          reinterpret_cast<void **>(module + kBattleResultStorageSlotRva),
          battle_result_id, kBattleResultIdOffset) == battle_result;
  return output.retained_storage_reader_ready;
}

bool AppendUnique(std::vector<std::int32_t> &values, std::int32_t value) {
  if (std::find(values.begin(), values.end(), value) == values.end()) {
    values.push_back(value);
  }
  return true;
}

game::CombatPhaseEventCharacterTraceV1 *FindOrAppendCharacter(
    std::vector<game::CombatPhaseEventCharacterTraceV1> &characters,
    std::int32_t side_index, std::int32_t character_id) noexcept {
  const auto existing = std::find_if(characters.begin(), characters.end(),
                                     [character_id](const auto &row) {
                                       return row.character_id == character_id;
                                     });
  if (existing != characters.end()) {
    return existing->side_index == side_index ? &*existing : nullptr;
  }
  characters.emplace_back();
  auto &row = characters.back();
  row.character_id = character_id;
  row.side_index = side_index;
  return &row;
}

bool BuildCharacterRoster(
    const std::array<NativeSideRead, 2> &sides,
    std::vector<game::CombatPhaseEventCharacterTraceV1> &characters) noexcept {
  characters.clear();
  for (const auto &side : sides) {
    for (const auto &slot : side.wire.ordered_commander_slots) {
      if (!slot.character.present) {
        continue;
      }
      auto *const row = FindOrAppendCharacter(characters, side.wire.side_index,
                                              slot.character.value);
      if (row == nullptr) {
        return false;
      }
      row->ordered_army_commander = true;
      (void)AppendUnique(row->source_army_ids, slot.source_army_id);
    }
    for (const auto &slot : side.wire.ordered_knight_slots) {
      if (!slot.character.present) {
        continue;
      }
      auto *const row = FindOrAppendCharacter(characters, side.wire.side_index,
                                              slot.character.value);
      if (row == nullptr) {
        return false;
      }
      row->ordered_knight = true;
      (void)AppendUnique(row->source_army_ids, slot.source_army_id);
      (void)AppendUnique(row->source_regiment_ids, slot.source_regiment_id);
    }
    if (side.wire.selected_commander.present) {
      auto *const row = FindOrAppendCharacter(
          characters, side.wire.side_index, side.wire.selected_commander.value);
      if (row == nullptr) {
        return false;
      }
      row->selected_side_commander = true;
    }
    for (const auto &schedule : side.wire.retained_nonempty_schedule_rows) {
      if (!schedule.current_character.present) {
        continue;
      }
      if (FindOrAppendCharacter(characters, side.wire.side_index,
                                schedule.current_character.value) == nullptr) {
        return false;
      }
    }
  }
  return !characters.empty();
}

bool ReadCharacterCoreState(
    const Bindings &bindings, std::int32_t character_id,
    game::CombatPhaseEventCharacterCoreStateV1 &output) noexcept {
  output = {};
  output.character_id = character_id;
  void *const character = ResolveStoredComponent(
      bindings.character_storage_slot, character_id, kCharacterIdOffset);
  if (character == nullptr) {
    return false;
  }
  bool native_valid = false;
  if (!VcallBool(static_cast<std::byte *>(character) + 0x10, 0x08,
                 native_valid)) {
    return false;
  }
  output.native_valid = native_valid;
  output.death_marker_present =
      LoadAt<void *>(character, kCharacterDeathMarkerOffset) != nullptr;
  output.alive = output.native_valid && !output.death_marker_present;
  output.martial = LoadAt<std::int32_t>(character, kCharacterMartialOffset);
  output.learning = LoadAt<std::int32_t>(character, kCharacterLearningOffset);
  output.prowess = LoadAt<std::int32_t>(character, kCharacterProwessOffset);

  void *const link = LoadAt<void *>(character, kCharacterRegimentLinkOffset);
  if (link == nullptr) {
    output.current_regiment_back_reference_matches = true;
    return ResolveStoredComponent(bindings.character_storage_slot, character_id,
                                  kCharacterIdOffset) == character;
  }
  const auto regiment_id =
      LoadAt<std::int32_t>(link, kCharacterLinkRegimentIdOffset);
  if (regiment_id == -1) {
    output.current_regiment_back_reference_matches = true;
    return ResolveStoredComponent(bindings.character_storage_slot, character_id,
                                  kCharacterIdOffset) == character;
  }
  void *const regiment = ResolveStoredComponent(bindings.regiment_storage_slot,
                                                regiment_id, kRegimentIdOffset);
  if (regiment == nullptr) {
    return false;
  }
  output.current_regiment = {true, regiment_id};
  output.current_regiment_back_reference_matches =
      LoadAt<std::int32_t>(regiment, kRegimentKnightCharacterIdOffset) ==
      character_id;
  return ResolveStoredComponent(bindings.character_storage_slot, character_id,
                                kCharacterIdOffset) == character;
}

bool PopulateCharacterStatesAndRows(
    const Bindings &bindings, std::uintptr_t module,
    const NativeCombatCore &core, const NativePhaseEventTable &table,
    const std::array<NativeSideRead, 2> &sides,
    std::vector<game::CombatPhaseEventCharacterTraceV1> &characters,
    bool &all_teardowns_complete) noexcept {
  all_teardowns_complete = true;
  for (auto &character : characters) {
    if (!ReadCharacterCoreState(bindings, character.character_id,
                                character.core_state)) {
      return false;
    }
    bool teardown_complete = false;
    if (!EvaluateCharacterRows(
            module, table, core.combat,
            sides[static_cast<std::size_t>(character.side_index)].side,
            character.selected_side_commander, character.ordered_knight,
            character.character_id, character.event_rows, teardown_complete)) {
      all_teardowns_complete = all_teardowns_complete && teardown_complete;
      return false;
    }
    all_teardowns_complete = all_teardowns_complete && teardown_complete;
  }
  return true;
}

std::uint32_t Avalanche32(std::uint32_t value) noexcept {
  value ^= value >> 8;
  value += 0x68E31DA4U;
  value ^= value << 8;
  value *= 0x1B56C4E9U;
  value ^= value >> 8;
  value *= 0x92D68CA2U;
  value ^= value >> 8;
  return value;
}

struct NativeRngRead {
  void *wrapper = nullptr;
  void *state = nullptr;
  std::uint32_t counter = 0;
  std::uint32_t salt = 0;
  std::uint32_t owner_thread_token = 0;
  std::uint32_t next_draw31 = 0;

  friend bool operator==(const NativeRngRead &,
                         const NativeRngRead &) = default;
};

bool ReadGlobalRng(std::uintptr_t module, NativeRngRead &output) noexcept {
  output = {};
  if (module == 0) {
    return false;
  }
  output.wrapper =
      *reinterpret_cast<void **>(module + kGlobalRngWrapperSlotRva);
  output.state =
      output.wrapper == nullptr ? nullptr : LoadAt<void *>(output.wrapper, 0);
  if (output.state == nullptr) {
    return false;
  }
  output.counter = LoadAt<std::uint32_t>(output.state, 0x08);
  output.salt = LoadAt<std::uint32_t>(output.state, 0x0C);
  output.owner_thread_token = LoadAt<std::uint32_t>(output.state, 0x10);
  const std::uint32_t input = output.salt - output.counter * 0x4AD685B3U;
  output.next_draw31 = Avalanche32(input) & 0x7FFFFFFFU;
  return true;
}

bool ReadCadence(
    std::uintptr_t module, std::int32_t snapshot_date_raw, std::int32_t phase,
    const std::vector<game::CombatPhaseEventCharacterTraceV1> &characters,
    game::CombatPhaseEventCadenceV1 &output) noexcept {
  output = {};
  if (module == 0) {
    return false;
  }
  void *const date = *reinterpret_cast<void **>(module + kCurrentDateSlotRva);
  if (date == nullptr) {
    return false;
  }
  output.native_date_raw = LoadAt<std::int32_t>(date, 0x08);
  output.period_days =
      *reinterpret_cast<const std::uint32_t *>(module + kCombatEventDaysRva);
  if (output.native_date_raw != snapshot_date_raw ||
      output.period_days != kExpectedCombatEventDays) {
    return false;
  }
  const auto delta = static_cast<std::int64_t>(output.native_date_raw) -
                     static_cast<std::int64_t>(kDateEpochRaw);
  if (delta < std::numeric_limits<std::int32_t>::min() ||
      delta > std::numeric_limits<std::int32_t>::max()) {
    return false;
  }
  output.day_index = static_cast<std::int32_t>(delta) / kDateUnitsPerDay;
  output.current_phase_fires_events = phase == 1;
  output.characters.reserve(characters.size());
  for (const auto &character : characters) {
    game::CombatPhaseEventCadenceCharacterV1 row{};
    row.character_id = character.character_id;
    row.side_index = character.side_index;
    row.selected_commander_role = character.selected_side_commander;
    row.knight_role = character.ordered_knight;
    row.unsigned_sum = static_cast<std::uint32_t>(character.character_id) +
                       static_cast<std::uint32_t>(output.day_index);
    row.residue = row.unsigned_sum % output.period_days;
    row.schedule_due =
        row.residue == 0 && (row.selected_commander_role || row.knight_role);
    output.characters.push_back(row);
  }
  return true;
}

bool SamePausedSnapshot(const game::Snapshot &before,
                        const game::Snapshot &after) noexcept {
  return before.paused && after.paused && before == after;
}

game::ReadCombatPhaseEventTraceV1Result
Fail(game::CombatPhaseEventTraceV1 &output,
     game::ReadCombatPhaseEventTraceV1Result result, std::string reason) {
  output.evaluator_probe_ready = false;
  output.production_trace_ready = false;
  output.same_paused_frame_stable = false;
  output.unavailable_reason = std::move(reason);
  return result;
}

} // namespace

game::ReadCombatPhaseEventTraceV1Result ReadCombatPhaseEventTraceV1Probe(
    const Bindings &bindings, std::int32_t combat_id,
    game::CombatPhaseEventTraceV1 &output) noexcept {
  output = {};
  output.combat_id = combat_id;
  try {
    if (!bindings.enabled) {
      return Fail(output, game::ReadCombatPhaseEventTraceV1Result::unavailable,
                  "exact_build_bindings_disabled");
    }
    if (combat_id < 0) {
      return Fail(output,
                  game::ReadCombatPhaseEventTraceV1Result::invalid_combat_id,
                  "combat_id_must_be_a_real_full_generation_id");
    }

    game::Snapshot before{};
    if (!ReadSnapshot(bindings, before)) {
      return Fail(output, game::ReadCombatPhaseEventTraceV1Result::unavailable,
                  "snapshot_before_unavailable");
    }
    if (!before.paused) {
      return Fail(output,
                  game::ReadCombatPhaseEventTraceV1Result::requires_paused,
                  "paused_snapshot_required");
    }
    const auto module = ModuleBase();
    if (module == 0) {
      return Fail(output, game::ReadCombatPhaseEventTraceV1Result::unavailable,
                  "main_module_unavailable");
    }

    NativeCombatCore core{};
    if (!ReadCombatCore(bindings, combat_id, core)) {
      void *const candidate = ResolveStoredComponent(
          bindings.combat_storage_slot, combat_id, kCombatIdOffset);
      return Fail(
          output,
          candidate == nullptr
              ? game::ReadCombatPhaseEventTraceV1Result::combat_not_found
              : game::ReadCombatPhaseEventTraceV1Result::combat_state_invalid,
          candidate == nullptr ? "combat_not_found"
                               : "combat_core_state_invalid");
    }

    NativePhaseEventTable table{};
    bool table_mismatch = false;
    if (!ReadNativePhaseEventTable(module, table, table_mismatch)) {
      return Fail(
          output,
          table_mismatch
              ? game::ReadCombatPhaseEventTraceV1Result::event_table_mismatch
              : game::ReadCombatPhaseEventTraceV1Result::
                    event_database_unavailable,
          table_mismatch ? "loaded_phase_event_table_is_not_exact_stock_13"
                         : "initialized_phase_event_database_unavailable");
    }

    NativeRngRead rng_before{};
    if (!ReadGlobalRng(module, rng_before)) {
      return Fail(output,
                  game::ReadCombatPhaseEventTraceV1Result::rng_unavailable,
                  "global_rng_state_unavailable");
    }

    std::array<NativeSideRead, 2> sides{};
    for (std::int32_t side_index = 0; side_index < 2; ++side_index) {
      bool roster_failed = false;
      bool schedule_failed = false;
      if (!ReadSideRosterAndSchedule(
              bindings, module, core, table, side_index,
              sides[static_cast<std::size_t>(side_index)], roster_failed,
              schedule_failed)) {
        return Fail(
            output,
            schedule_failed
                ? game::ReadCombatPhaseEventTraceV1Result::schedule_unavailable
                : game::ReadCombatPhaseEventTraceV1Result::roster_unavailable,
            schedule_failed ? "retained_phase_event_schedule_unavailable"
                            : "combat_side_roster_unavailable");
      }
    }

    game::CombatPhaseBattleEventLedgerV1 battle_events;
    if (!ReadRetainedBattleEvents(bindings, module, core, battle_events)) {
      return Fail(output,
                  game::ReadCombatPhaseEventTraceV1Result::
                      battle_event_storage_unavailable,
                  "combat_battle_result_retained_event_storage_unavailable");
    }

    std::vector<game::CombatPhaseEventCharacterTraceV1> characters;
    if (!BuildCharacterRoster(sides, characters)) {
      return Fail(output,
                  game::ReadCombatPhaseEventTraceV1Result::roster_unavailable,
                  "combat_side_character_roster_empty_or_ambiguous");
    }
    bool all_teardowns_complete = false;
    if (!PopulateCharacterStatesAndRows(bindings, module, core, table, sides,
                                        characters, all_teardowns_complete)) {
      return Fail(
          output,
          all_teardowns_complete
              ? game::ReadCombatPhaseEventTraceV1Result::
                    native_evaluator_unavailable
              : game::ReadCombatPhaseEventTraceV1Result::scope_teardown_failed,
          all_teardowns_complete
              ? "native_trigger_or_chance_evaluator_unavailable"
              : "event_target_scope_evaluation_or_teardown_failed");
    }

    game::CombatPhaseEventCadenceV1 cadence{};
    if (!ReadCadence(module, before.date_raw, core.phase, characters,
                     cadence)) {
      return Fail(output,
                  game::ReadCombatPhaseEventTraceV1Result::atomicity_failed,
                  "phase_event_cadence_or_date_identity_changed");
    }

    // A second full differential pass is intentional.  Equality proves that
    // trigger/value output itself was stable, rather than merely proving that
    // the small subset of fields explicitly serialized below did not change.
    NativeCombatCore core_after{};
    NativePhaseEventTable table_after{};
    bool table_after_mismatch = false;
    std::array<NativeSideRead, 2> sides_after{};
    game::CombatPhaseBattleEventLedgerV1 battle_events_after;
    std::vector<game::CombatPhaseEventCharacterTraceV1> characters_after;
    bool all_teardowns_after = false;
    bool second_pass_ok =
        ReadCombatCore(bindings, combat_id, core_after) && core_after == core &&
        ReadNativePhaseEventTable(module, table_after, table_after_mismatch) &&
        !table_after_mismatch && RevalidateNativePhaseEventTable(module, table);
    for (std::int32_t side_index = 0; second_pass_ok && side_index < 2;
         ++side_index) {
      bool roster_failed = false;
      bool schedule_failed = false;
      second_pass_ok = ReadSideRosterAndSchedule(
          bindings, module, core_after, table_after, side_index,
          sides_after[static_cast<std::size_t>(side_index)], roster_failed,
          schedule_failed);
    }
    second_pass_ok = second_pass_ok && sides_after[0].wire == sides[0].wire &&
                     sides_after[1].wire == sides[1].wire &&
                     ReadRetainedBattleEvents(bindings, module, core_after,
                                              battle_events_after) &&
                     battle_events_after == battle_events &&
                     BuildCharacterRoster(sides_after, characters_after) &&
                     PopulateCharacterStatesAndRows(
                         bindings, module, core_after, table_after, sides_after,
                         characters_after, all_teardowns_after) &&
                     all_teardowns_after && characters_after == characters;

    NativeRngRead rng_after{};
    game::Snapshot after{};
    if (!second_pass_ok || !ReadGlobalRng(module, rng_after) ||
        rng_after != rng_before || !ReadSnapshot(bindings, after) ||
        !SamePausedSnapshot(before, after)) {
      return Fail(output,
                  game::ReadCombatPhaseEventTraceV1Result::atomicity_failed,
                  "same_paused_frame_identity_or_evaluator_output_changed");
    }

    output.date_raw = before.date_raw;
    output.target_province_id = core.target_province_id;
    output.phase_raw = core.phase;
    output.phase = PhaseName(core.phase);
    output.phase_day = core.phase_day;
    if (core.winner != -1) {
      output.winner_side = {true, core.winner};
    }
    output.sides[0] = std::move(sides[0].wire);
    output.sides[1] = std::move(sides[1].wire);
    output.characters = std::move(characters);
    output.cadence = std::move(cadence);
    output.global_rng.counter = rng_before.counter;
    output.global_rng.salt = rng_before.salt;
    output.global_rng.owner_thread_token = rng_before.owner_thread_token;
    output.global_rng.next_draw31 = rng_before.next_draw31;
    output.global_rng.wrapper_and_state_identity_stable = true;
    output.global_rng.unchanged_by_probe = true;
    output.random_side_knight_order.source_vector_runtime_reader_ready = true;
    output.battle_events = std::move(battle_events);
    output.occurrence_boundary.battle_event_storage_reader_ready = true;
    output.real_combat_side_scope = true;
    output.all_scope_teardowns_complete =
        all_teardowns_complete && all_teardowns_after;
    output.same_paused_frame_stable = true;
    output.evaluator_probe_ready = true;

    // No nullable placeholders: each missing semantic domain names the next
    // concrete reader/managed trace required before the capability can be
    // advertised.
    output.missing_production_readers = {
        "full_mutable_state_traits_tracks_variables_and_participant_membership",
        "phase_event_origin_association_for_retained_battle_event_delta",
        "managed_daily_before_after_transition_driver",
        "effect_transition_same_day_recompute_trace",
    };
    output.production_trace_ready = false;
    output.unavailable_reason = "production_trace_gates_not_closed";
    return game::ReadCombatPhaseEventTraceV1Result::evaluator_probe_available;
  } catch (const std::exception &) {
    output = {};
    output.combat_id = combat_id;
    return Fail(output, game::ReadCombatPhaseEventTraceV1Result::unavailable,
                "phase_event_trace_probe_exception");
  } catch (...) {
    output = {};
    output.combat_id = combat_id;
    return Fail(output, game::ReadCombatPhaseEventTraceV1Result::unavailable,
                "phase_event_trace_probe_exception");
  }
}

} // namespace xar::ck3_11906
