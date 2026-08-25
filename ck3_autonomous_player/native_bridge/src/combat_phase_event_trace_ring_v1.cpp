#include "xar_bridge/combat_phase_event_trace_ring_v1.hpp"

#include <intrin.h>
#include <windows.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kCombatIdOffset = 0x08;
constexpr std::size_t kCombatSide0Offset = 0x20;
constexpr std::size_t kCombatSide1Offset = 0x368;
constexpr std::size_t kCombatPhaseOffset = 0x6B0;
constexpr std::size_t kCombatPhaseDayOffset = 0x6B4;
constexpr std::size_t kCombatBaseAdvantageOffset = 0x6C8;
constexpr std::size_t kCombatAdvantageRoll0Offset = 0x6D0;
constexpr std::size_t kCombatAdvantageRoll1Offset = 0x6D4;
constexpr std::size_t kCombatWinnerOffset = 0x6E0;
constexpr std::size_t kCombatBattleResultIdOffset = 0x708;
constexpr std::size_t kCombatResolvedAdvantageOffset = 0x710;

constexpr std::size_t kSideArmyHeaderOffset = 0x10;
constexpr std::size_t kSideKnightHeaderOffset = 0x40;
constexpr std::size_t kSideSelectedCommanderOffset = 0x74;
constexpr std::size_t kSideCurrentFightingTotalOffset = 0x98;
constexpr std::size_t kSideFirstFightingSubtotalOffset = 0xA0;
constexpr std::size_t kSideCombatBackPointerOffset = 0xB8;
constexpr std::size_t kSideScheduledKnightHeaderOffset = 0xD8;
constexpr std::size_t kSideScheduledCommanderOffset = 0xF0;
constexpr std::size_t kSideKnightStride = 0x60;
constexpr std::size_t kSideKnightRegimentIdOffset = 0x08;
constexpr std::size_t kSideScheduledKnightStride = 0x10;
constexpr std::size_t kSideScheduledKnightEventOffset = 0x00;
constexpr std::size_t kSideScheduledKnightRegimentIdOffset = 0x08;

constexpr std::size_t kArmyIdOffset = 0x10;
constexpr std::size_t kArmyCommanderOffset = 0x120;
constexpr std::size_t kArmyCombatIdOffset = 0x128;
constexpr std::size_t kRegimentIdOffset = 0x10;
constexpr std::size_t kRegimentArmyIdOffset = 0x140;
constexpr std::size_t kRegimentCharacterIdOffset = 0x148;
constexpr std::size_t kCharacterIdOffset = 0x18;
constexpr std::size_t kCharacterMartialOffset = 0xD8;
constexpr std::size_t kCharacterLearningOffset = 0xE4;
constexpr std::size_t kCharacterProwessOffset = 0xE8;
constexpr std::size_t kCharacterAccoladeLinkOffset = 0x1A8;
constexpr std::size_t kCharacterRegimentLinkOffset = 0x1B0;
constexpr std::size_t kCharacterDeathMarkerOffset = 0x1C8;
constexpr std::size_t kCharacterLinkRegimentIdOffset = 0xF8;
constexpr std::size_t kCharacterLinkAccoladeIdOffset = 0x568;

constexpr std::size_t kAccoladeIdOffset = 0x08;
constexpr std::size_t kAccoladeOwnerCharacterIdOffset = 0x70;
constexpr std::size_t kAccoladeGloryOffset = 0xB0;

constexpr std::size_t kBattleResultIdOffset = 0x08;
constexpr std::size_t kBattleEventHeaderOffset = 0x188;
constexpr std::size_t kBattleEventStride = 0x38;
constexpr std::size_t kBattleEventLeftCharacterOffset = 0x08;
constexpr std::size_t kBattleEventRightCharacterOffset = 0x0C;
constexpr std::size_t kBattleEventStableKeyOffset = 0x10;
constexpr std::size_t kBattleEventTypeOffset = 0x30;
constexpr std::size_t kBattleEventSide0Offset = 0x34;
constexpr std::size_t kBattleEventTargetRightOffset = 0x35;
constexpr std::size_t kMsvcStringSizeOffset = 0x10;
constexpr std::size_t kMsvcStringCapacityOffset = 0x18;
constexpr std::size_t kMsvcStringInlineCapacity = 15;

constexpr std::size_t kNativeVectorDataOffset = 0x00;
constexpr std::size_t kNativeVectorCapacityOffset = 0x08;
constexpr std::size_t kNativeVectorCountOffset = 0x0C;
constexpr std::size_t kCurrentDateRawOffset = 0x08;
constexpr std::size_t kGlobalRngStateOffset = 0x00;
constexpr std::size_t kGlobalRngCounterOffset = 0x08;
constexpr std::size_t kGlobalRngSaltOffset = 0x0C;
constexpr std::size_t kGlobalRngOwnerThreadOffset = 0x10;
constexpr std::int32_t kMaximumNativeContainerCapacity = 65'536;

std::atomic<CombatPhaseEventTraceRingV1 *> g_active_ring{nullptr};
std::atomic<CombatPhaseEventScheduleOriginalV1> g_original_schedule{nullptr};
std::atomic<CombatPhaseEventFireOriginalV1> g_original_fire{nullptr};

template <typename T>
T LoadAt(std::uintptr_t base, std::size_t offset) noexcept {
  T output{};
  std::memcpy(&output, reinterpret_cast<const void *>(base + offset),
              sizeof(output));
  return output;
}

template <typename T>
T LoadAt(const void *base, std::size_t offset) noexcept {
  return LoadAt<T>(reinterpret_cast<std::uintptr_t>(base), offset);
}

void MarkFailure(CombatPhaseEventTraceRingV1 &ring,
                 std::uint32_t flags) noexcept {
  ring.failure_flags.fetch_or(flags, std::memory_order_relaxed);
}

bool IsStrictlySortedAndValid(
    const CombatPhaseEventTraceObjectRefV1 *rows,
    std::uint32_t count) noexcept {
  std::int32_t previous = -1;
  for (std::uint32_t index = 0; index < count; ++index) {
    if (rows[index].full_id <= previous || rows[index].object == 0) {
      return false;
    }
    previous = rows[index].full_id;
  }
  return true;
}

const CombatPhaseEventTraceObjectRefV1 *FindObject(
    const CombatPhaseEventTraceObjectRefV1 *rows, std::uint32_t count,
    std::int32_t full_id) noexcept;

bool ValidateAccoladePlanUnsafe(
    const CombatPhaseEventTraceCapturePlanV1 &plan) noexcept {
  if (plan.accolade_rank_threshold_data_slot == 0 ||
      plan.expected_accolade_rank_threshold_data == 0 ||
      plan.accolade_rank_threshold_count_slot == 0 ||
      plan.accolade_rank_threshold_count == 0 ||
      plan.accolade_rank_threshold_count >
          plan.accolade_rank_thresholds_raw.size() ||
      plan.accolade_count > plan.accolades.size() ||
      LoadAt<std::uintptr_t>(plan.accolade_rank_threshold_data_slot, 0) !=
          plan.expected_accolade_rank_threshold_data ||
      LoadAt<std::int32_t>(plan.accolade_rank_threshold_count_slot, 0) !=
          static_cast<std::int32_t>(plan.accolade_rank_threshold_count)) {
    return false;
  }
  for (std::uint32_t index = 0;
       index < plan.accolade_rank_threshold_count; ++index) {
    if (LoadAt<std::int64_t>(plan.expected_accolade_rank_threshold_data,
                             index * sizeof(std::int64_t)) !=
        plan.accolade_rank_thresholds_raw[index]) {
      return false;
    }
  }
  std::int32_t previous = -1;
  for (std::uint32_t index = 0; index < plan.accolade_count; ++index) {
    const auto &row = plan.accolades[index];
    if (row.accolade_id <= previous || row.accolade == 0 ||
        row.owner_character_id <= 0 ||
        row.acclaimed_knight_character_id <= 0 ||
        row.acclaimed_knight == 0 ||
        LoadAt<std::int32_t>(row.accolade, kAccoladeIdOffset) !=
            row.accolade_id ||
        LoadAt<std::int32_t>(row.accolade,
                             kAccoladeOwnerCharacterIdOffset) !=
            row.owner_character_id ||
        LoadAt<std::int32_t>(row.acclaimed_knight, kCharacterIdOffset) !=
            row.acclaimed_knight_character_id) {
      return false;
    }
    const auto *const character = FindObject(
        plan.characters.data(), plan.character_count,
        row.acclaimed_knight_character_id);
    if (character == nullptr ||
        character->object != row.acclaimed_knight) {
      return false;
    }
    const auto link = LoadAt<std::uintptr_t>(
        row.acclaimed_knight, kCharacterAccoladeLinkOffset);
    if (link == 0 ||
        LoadAt<std::int32_t>(link, kCharacterLinkAccoladeIdOffset) !=
            row.accolade_id) {
      return false;
    }
    previous = row.accolade_id;
  }
  return true;
}

const CombatPhaseEventTraceObjectRefV1 *FindObject(
    const CombatPhaseEventTraceObjectRefV1 *rows, std::uint32_t count,
    std::int32_t full_id) noexcept {
  std::uint32_t first = 0;
  std::uint32_t last = count;
  while (first < last) {
    const auto middle = first + (last - first) / 2;
    if (rows[middle].full_id < full_id) {
      first = middle + 1;
    } else {
      last = middle;
    }
  }
  if (first >= count || rows[first].full_id != full_id) {
    return nullptr;
  }
  return &rows[first];
}

bool ValidateCapturePlanUnsafe(
    const CombatPhaseEventTraceCapturePlanV1 &plan) noexcept {
  if (plan.abi_version != kCombatPhaseEventTraceRingV1AbiVersion ||
      plan.managed_daily_sequence_token == 0 || plan.module_base == 0 ||
      plan.combat_id <= 0 || plan.combat == 0 ||
      plan.sides[0] != plan.combat + kCombatSide0Offset ||
      plan.sides[1] != plan.combat + kCombatSide1Offset ||
      plan.phase_event_database_slot == 0 ||
      plan.expected_phase_event_database == 0 ||
      plan.current_date_slot == 0 ||
      plan.expected_current_date_object == 0 ||
      plan.global_rng_wrapper_slot == 0 ||
      plan.expected_global_rng_wrapper == 0 ||
      plan.expected_global_rng_state == 0 ||
      plan.battle_result_id <= 0 || plan.battle_result == 0 ||
      plan.expected_battle_event_vtable == 0 ||
      plan.army_count > plan.armies.size() ||
      plan.regiment_count > plan.regiments.size() ||
      plan.character_count == 0 ||
      plan.character_count > plan.characters.size() ||
      !IsStrictlySortedAndValid(plan.armies.data(), plan.army_count) ||
      !IsStrictlySortedAndValid(plan.regiments.data(),
                                plan.regiment_count) ||
      !IsStrictlySortedAndValid(plan.characters.data(),
                                plan.character_count) ||
      !ValidateAccoladePlanUnsafe(plan)) {
    return false;
  }
  if (LoadAt<std::int32_t>(plan.combat, kCombatIdOffset) != plan.combat_id ||
      LoadAt<std::uintptr_t>(plan.sides[0],
                             kSideCombatBackPointerOffset) != plan.combat ||
      LoadAt<std::uintptr_t>(plan.sides[1],
                             kSideCombatBackPointerOffset) != plan.combat ||
      LoadAt<std::int32_t>(plan.combat, kCombatBattleResultIdOffset) !=
          plan.battle_result_id ||
      LoadAt<std::int32_t>(plan.battle_result, kBattleResultIdOffset) !=
          plan.battle_result_id ||
      LoadAt<std::uintptr_t>(plan.phase_event_database_slot, 0) !=
          plan.expected_phase_event_database ||
      LoadAt<std::uintptr_t>(plan.current_date_slot, 0) !=
          plan.expected_current_date_object ||
      LoadAt<std::uintptr_t>(plan.global_rng_wrapper_slot, 0) !=
          plan.expected_global_rng_wrapper ||
      LoadAt<std::uintptr_t>(plan.expected_global_rng_wrapper,
                             kGlobalRngStateOffset) !=
          plan.expected_global_rng_state) {
    return false;
  }
  for (std::uint32_t index = 0; index < plan.army_count; ++index) {
    if (LoadAt<std::int32_t>(plan.armies[index].object, kArmyIdOffset) !=
        plan.armies[index].full_id) {
      return false;
    }
  }
  for (std::uint32_t index = 0; index < plan.regiment_count; ++index) {
    if (LoadAt<std::int32_t>(plan.regiments[index].object,
                             kRegimentIdOffset) !=
        plan.regiments[index].full_id) {
      return false;
    }
  }
  for (std::uint32_t index = 0; index < plan.character_count; ++index) {
    if (LoadAt<std::int32_t>(plan.characters[index].object,
                             kCharacterIdOffset) !=
        plan.characters[index].full_id) {
      return false;
    }
  }
  return true;
}

bool ValidateCapturePlan(
    const CombatPhaseEventTraceCapturePlanV1 &plan) noexcept {
#if defined(_MSC_VER)
  __try {
    return ValidateCapturePlanUnsafe(plan);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  return ValidateCapturePlanUnsafe(plan);
#endif
}

struct NativeVectorView {
  std::uintptr_t data = 0;
  std::uint32_t count = 0;
};

bool ReadVector(std::uintptr_t owner, std::size_t header_offset,
                std::uint32_t maximum_count, NativeVectorView &output,
                std::uint32_t &failure_flags) noexcept {
  const auto header = owner + header_offset;
  const auto data = LoadAt<std::uintptr_t>(header, kNativeVectorDataOffset);
  const auto capacity =
      LoadAt<std::int32_t>(header, kNativeVectorCapacityOffset);
  const auto count = LoadAt<std::int32_t>(header, kNativeVectorCountOffset);
  if (capacity < 0 || count < 0 || count > capacity ||
      capacity > kMaximumNativeContainerCapacity ||
      static_cast<std::uint32_t>(count) > maximum_count ||
      (count > 0 && data == 0)) {
    failure_flags |= count > static_cast<std::int32_t>(maximum_count)
                         ? trace_capture_failure_capacity
                         : trace_capture_failure_container;
    return false;
  }
  output.data = data;
  output.count = static_cast<std::uint32_t>(count);
  return true;
}

bool ReadSide(const CombatPhaseEventTraceCapturePlanV1 &plan,
              std::size_t side_index,
              CombatPhaseEventTraceSideRecordV1 &output,
              std::uint32_t &failure_flags) noexcept {
  const auto side = plan.sides[side_index];
  if (side == 0 ||
      LoadAt<std::uintptr_t>(side, kSideCombatBackPointerOffset) !=
          plan.combat) {
    failure_flags |= trace_capture_failure_identity;
    return false;
  }
  output.side = side;
  output.side_index = static_cast<std::int32_t>(side_index);
  output.selected_commander_character_id =
      LoadAt<std::int32_t>(side, kSideSelectedCommanderOffset);
  output.current_fighting_total_raw =
      LoadAt<std::int64_t>(side, kSideCurrentFightingTotalOffset);
  output.first_fighting_subtotal_raw =
      LoadAt<std::int64_t>(side, kSideFirstFightingSubtotalOffset);
  output.scheduled_commander_event_identity =
      LoadAt<std::uintptr_t>(side, kSideScheduledCommanderOffset);

  NativeVectorView armies{};
  if (!ReadVector(side, kSideArmyHeaderOffset,
                  static_cast<std::uint32_t>(output.armies.size()), armies,
                  failure_flags)) {
    return false;
  }
  output.army_count = armies.count;
  for (std::uint32_t index = 0; index < armies.count; ++index) {
    const auto army_id =
        LoadAt<std::int32_t>(armies.data, index * sizeof(std::int32_t));
    const auto *const resolved =
        FindObject(plan.armies.data(), plan.army_count, army_id);
    if (resolved == nullptr ||
        LoadAt<std::int32_t>(resolved->object, kArmyIdOffset) != army_id) {
      failure_flags |= trace_capture_failure_identity;
      return false;
    }
    auto &row = output.armies[index];
    row.army_id = army_id;
    row.commander_character_id =
        LoadAt<std::int32_t>(resolved->object, kArmyCommanderOffset);
    row.combat_id =
        LoadAt<std::int32_t>(resolved->object, kArmyCombatIdOffset);
    if (row.combat_id != plan.combat_id) {
      failure_flags |= trace_capture_failure_identity;
      return false;
    }
  }

  NativeVectorView knights{};
  if (!ReadVector(side, kSideKnightHeaderOffset,
                  static_cast<std::uint32_t>(output.knights.size()), knights,
                  failure_flags)) {
    return false;
  }
  output.knight_count = knights.count;
  for (std::uint32_t index = 0; index < knights.count; ++index) {
    const auto native_row =
        knights.data + index * kSideKnightStride;
    const auto regiment_id =
        LoadAt<std::int32_t>(native_row, kSideKnightRegimentIdOffset);
    const auto *const resolved = FindObject(
        plan.regiments.data(), plan.regiment_count, regiment_id);
    if (resolved == nullptr ||
        LoadAt<std::int32_t>(resolved->object, kRegimentIdOffset) !=
            regiment_id) {
      failure_flags |= trace_capture_failure_identity;
      return false;
    }
    auto &row = output.knights[index];
    row.regiment_id = regiment_id;
    row.army_id =
        LoadAt<std::int32_t>(resolved->object, kRegimentArmyIdOffset);
    row.character_id =
        LoadAt<std::int32_t>(resolved->object, kRegimentCharacterIdOffset);
  }

  NativeVectorView schedules{};
  if (!ReadVector(side, kSideScheduledKnightHeaderOffset,
                  static_cast<std::uint32_t>(output.scheduled_knights.size()),
                  schedules, failure_flags)) {
    return false;
  }
  output.scheduled_knight_count = schedules.count;
  for (std::uint32_t index = 0; index < schedules.count; ++index) {
    const auto native_row =
        schedules.data + index * kSideScheduledKnightStride;
    auto &row = output.scheduled_knights[index];
    row.event_identity = LoadAt<std::uintptr_t>(
        native_row, kSideScheduledKnightEventOffset);
    row.regiment_id = LoadAt<std::int32_t>(
        native_row, kSideScheduledKnightRegimentIdOffset);
    const auto *const resolved = FindObject(
        plan.regiments.data(), plan.regiment_count, row.regiment_id);
    if (resolved == nullptr ||
        LoadAt<std::int32_t>(resolved->object, kRegimentIdOffset) !=
            row.regiment_id) {
      failure_flags |= trace_capture_failure_identity;
      return false;
    }
    row.current_character_id =
        LoadAt<std::int32_t>(resolved->object, kRegimentCharacterIdOffset);
  }
  return true;
}

bool ReadCharacters(const CombatPhaseEventTraceCapturePlanV1 &plan,
                    CombatPhaseEventTraceRingRecordV1 &output,
                    std::uint32_t &failure_flags) noexcept {
  output.character_count = plan.character_count;
  for (std::uint32_t index = 0; index < plan.character_count; ++index) {
    const auto &source = plan.characters[index];
    if (LoadAt<std::int32_t>(source.object, kCharacterIdOffset) !=
        source.full_id) {
      failure_flags |= trace_capture_failure_identity;
      return false;
    }
    auto &row = output.characters[index];
    row.character_id = source.full_id;
    row.character = source.object;
    row.death_marker_present =
        LoadAt<std::uintptr_t>(source.object, kCharacterDeathMarkerOffset) != 0;
    row.martial =
        LoadAt<std::int32_t>(source.object, kCharacterMartialOffset);
    row.learning =
        LoadAt<std::int32_t>(source.object, kCharacterLearningOffset);
    row.prowess =
        LoadAt<std::int32_t>(source.object, kCharacterProwessOffset);
    const auto link =
        LoadAt<std::uintptr_t>(source.object, kCharacterRegimentLinkOffset);
    if (link == 0) {
      row.current_regiment_back_reference_matches = true;
      continue;
    }
    const auto regiment_id =
        LoadAt<std::int32_t>(link, kCharacterLinkRegimentIdOffset);
    if (regiment_id == -1) {
      row.current_regiment_back_reference_matches = true;
      continue;
    }
    row.current_regiment_id = regiment_id;
    const auto *const resolved = FindObject(
        plan.regiments.data(), plan.regiment_count, regiment_id);
    if (resolved == nullptr ||
        LoadAt<std::int32_t>(resolved->object, kRegimentIdOffset) !=
            regiment_id) {
      failure_flags |= trace_capture_failure_identity;
      return false;
    }
    row.current_regiment_back_reference_matches =
        LoadAt<std::int32_t>(resolved->object,
                             kRegimentCharacterIdOffset) == source.full_id;
  }
  return true;
}

std::int32_t MirrorAccoladeRank(
    const CombatPhaseEventTraceCapturePlanV1 &plan,
    std::int64_t glory_raw) noexcept {
  for (std::int32_t index =
           static_cast<std::int32_t>(
               plan.accolade_rank_threshold_count) -
           1;
       index >= 0; --index) {
    if (glory_raw >= plan.accolade_rank_thresholds_raw[
                         static_cast<std::size_t>(index)]) {
      return index + 1;
    }
  }
  return 1;
}

bool ReadAccolades(const CombatPhaseEventTraceCapturePlanV1 &plan,
                   CombatPhaseEventTraceRingRecordV1 &output,
                   std::uint32_t &failure_flags) noexcept {
  if (LoadAt<std::uintptr_t>(plan.accolade_rank_threshold_data_slot, 0) !=
          plan.expected_accolade_rank_threshold_data ||
      LoadAt<std::int32_t>(plan.accolade_rank_threshold_count_slot, 0) !=
          static_cast<std::int32_t>(plan.accolade_rank_threshold_count)) {
    failure_flags |= trace_capture_failure_identity;
    return false;
  }
  for (std::uint32_t index = 0;
       index < plan.accolade_rank_threshold_count; ++index) {
    if (LoadAt<std::int64_t>(plan.expected_accolade_rank_threshold_data,
                             index * sizeof(std::int64_t)) !=
        plan.accolade_rank_thresholds_raw[index]) {
      failure_flags |= trace_capture_failure_identity;
      return false;
    }
  }

  output.accolade_count = plan.accolade_count;
  for (std::uint32_t index = 0; index < plan.accolade_count; ++index) {
    const auto &source = plan.accolades[index];
    auto &row = output.accolades[index];
    row.accolade_id = source.accolade_id;
    row.accolade = source.accolade;
    row.owner_character_id = LoadAt<std::int32_t>(
        source.accolade, kAccoladeOwnerCharacterIdOffset);
    row.acclaimed_knight_character_id =
        source.acclaimed_knight_character_id;
    row.glory_raw =
        LoadAt<std::int64_t>(source.accolade, kAccoladeGloryOffset);
    row.rank_native_mirror = MirrorAccoladeRank(plan, row.glory_raw);
    const auto link = LoadAt<std::uintptr_t>(
        source.acclaimed_knight, kCharacterAccoladeLinkOffset);
    row.participant_link_identity_matches =
        LoadAt<std::int32_t>(source.accolade, kAccoladeIdOffset) ==
            source.accolade_id &&
        row.owner_character_id == source.owner_character_id &&
        LoadAt<std::int32_t>(source.acclaimed_knight,
                             kCharacterIdOffset) ==
            source.acclaimed_knight_character_id &&
        link != 0 &&
        LoadAt<std::int32_t>(link, kCharacterLinkAccoladeIdOffset) ==
            source.accolade_id;
    if (!row.participant_link_identity_matches) {
      failure_flags |= trace_capture_failure_identity;
      return false;
    }
  }
  return true;
}

bool ReadBoundedMsvcString(
    std::uintptr_t storage,
    CombatPhaseEventTraceBattleEventRecordV1 &output,
    std::uint32_t &failure_flags) noexcept {
  const auto size = LoadAt<std::size_t>(storage, kMsvcStringSizeOffset);
  const auto capacity =
      LoadAt<std::size_t>(storage, kMsvcStringCapacityOffset);
  if (capacity < size ||
      size > kCombatPhaseEventTraceRingV1BattleEventKeyBytes ||
      capacity > static_cast<std::size_t>(kMaximumNativeContainerCapacity) *
                     kCombatPhaseEventTraceRingV1BattleEventKeyBytes) {
    failure_flags |= size >
                             kCombatPhaseEventTraceRingV1BattleEventKeyBytes
                         ? trace_capture_failure_capacity
                         : trace_capture_failure_string;
    return false;
  }
  const auto data = capacity <= kMsvcStringInlineCapacity
                        ? storage
                        : LoadAt<std::uintptr_t>(storage, 0);
  if (size > 0 && data == 0) {
    failure_flags |= trace_capture_failure_string;
    return false;
  }
  output.stable_key_size = static_cast<std::uint16_t>(size);
  if (size > 0) {
    std::memcpy(output.stable_key.data(),
                reinterpret_cast<const void *>(data), size);
  }
  return true;
}

bool ReadBattleEvents(const CombatPhaseEventTraceCapturePlanV1 &plan,
                      CombatPhaseEventTraceRingRecordV1 &output,
                      std::uint32_t &failure_flags) noexcept {
  if (LoadAt<std::int32_t>(plan.combat, kCombatBattleResultIdOffset) !=
          plan.battle_result_id ||
      LoadAt<std::int32_t>(plan.battle_result, kBattleResultIdOffset) !=
          plan.battle_result_id) {
    failure_flags |= trace_capture_failure_identity;
    return false;
  }
  NativeVectorView rows{};
  if (!ReadVector(
          plan.battle_result, kBattleEventHeaderOffset,
          static_cast<std::uint32_t>(output.battle_events.size()), rows,
          failure_flags)) {
    return false;
  }
  output.battle_event_count = rows.count;
  for (std::uint32_t index = 0; index < rows.count; ++index) {
    const auto native = rows.data + index * kBattleEventStride;
    if (LoadAt<std::uintptr_t>(native, 0) !=
        plan.expected_battle_event_vtable) {
      failure_flags |= trace_capture_failure_identity;
      return false;
    }
    auto &row = output.battle_events[index];
    row.left_character_id =
        LoadAt<std::int32_t>(native, kBattleEventLeftCharacterOffset);
    row.right_character_id =
        LoadAt<std::int32_t>(native, kBattleEventRightCharacterOffset);
    row.type_raw = LoadAt<std::int32_t>(native, kBattleEventTypeOffset);
    row.side_index =
        LoadAt<std::uint8_t>(native, kBattleEventSide0Offset) != 0 ? 0 : 1;
    row.target_right =
        LoadAt<std::uint8_t>(native, kBattleEventTargetRightOffset) != 0;
    if (!ReadBoundedMsvcString(native + kBattleEventStableKeyOffset, row,
                               failure_flags)) {
      return false;
    }
  }
  return true;
}

bool IsScheduleBoundary(CombatPhaseEventTraceBoundaryV1 boundary) noexcept {
  return boundary ==
             CombatPhaseEventTraceBoundaryV1::before_side0_schedule ||
         boundary ==
             CombatPhaseEventTraceBoundaryV1::after_side1_schedule;
}

std::uintptr_t ExpectedTriggerSide(
    const CombatPhaseEventTraceCapturePlanV1 &plan,
    CombatPhaseEventTraceBoundaryV1 boundary) noexcept {
  switch (boundary) {
  case CombatPhaseEventTraceBoundaryV1::before_side0_schedule:
  case CombatPhaseEventTraceBoundaryV1::before_side0_phase_fire:
  case CombatPhaseEventTraceBoundaryV1::after_side0_phase_fire:
    return plan.sides[0];
  case CombatPhaseEventTraceBoundaryV1::after_side1_schedule:
  case CombatPhaseEventTraceBoundaryV1::before_side1_phase_fire:
  case CombatPhaseEventTraceBoundaryV1::after_side1_phase_fire:
    return plan.sides[1];
  case CombatPhaseEventTraceBoundaryV1::paused_next_day_stable_query:
    return 0;
  }
  return 0;
}

std::uintptr_t ExpectedReturnAddress(
    const CombatPhaseEventTraceCapturePlanV1 &plan,
    CombatPhaseEventTraceBoundaryV1 boundary) noexcept {
  switch (boundary) {
  case CombatPhaseEventTraceBoundaryV1::before_side0_schedule:
    return plan.module_base + kCombatPhaseEventScheduleSide0ReturnRva;
  case CombatPhaseEventTraceBoundaryV1::after_side1_schedule:
    return plan.module_base + kCombatPhaseEventScheduleSide1ReturnRva;
  case CombatPhaseEventTraceBoundaryV1::before_side0_phase_fire:
  case CombatPhaseEventTraceBoundaryV1::after_side0_phase_fire:
    return plan.module_base + kCombatPhaseEventFireSide0ReturnRva;
  case CombatPhaseEventTraceBoundaryV1::before_side1_phase_fire:
  case CombatPhaseEventTraceBoundaryV1::after_side1_phase_fire:
    return plan.module_base + kCombatPhaseEventFireSide1ReturnRva;
  case CombatPhaseEventTraceBoundaryV1::paused_next_day_stable_query:
    return 0;
  }
  return 0;
}

bool CaptureUnsafe(CombatPhaseEventTraceRingV1 &ring,
                   CombatPhaseEventTraceRingRecordV1 &output,
                   CombatPhaseEventTraceBoundaryV1 boundary, void *combat,
                   void *trigger_side,
                   const std::uint32_t *schedule_local_rng,
                   std::uintptr_t caller_return_address) noexcept {
  const auto &plan = ring.plan;
  std::uint32_t failure_flags = trace_capture_failure_none;
  output.abi_version = kCombatPhaseEventTraceRingV1AbiVersion;
  output.boundary = boundary;
  output.managed_daily_sequence_token = plan.managed_daily_sequence_token;
  output.caller_return_address = caller_return_address;
  output.combat = reinterpret_cast<std::uintptr_t>(combat);
  output.trigger_side = reinterpret_cast<std::uintptr_t>(trigger_side);

  if (output.combat != plan.combat ||
      output.trigger_side != ExpectedTriggerSide(plan, boundary) ||
      caller_return_address != ExpectedReturnAddress(plan, boundary) ||
      LoadAt<std::int32_t>(plan.combat, kCombatIdOffset) != plan.combat_id) {
    failure_flags |= trace_capture_failure_identity;
  }
  if (IsScheduleBoundary(boundary)) {
    if (schedule_local_rng == nullptr) {
      failure_flags |= trace_capture_failure_identity;
    } else {
      output.schedule_local_rng_present = true;
      output.schedule_local_rng_word0 = schedule_local_rng[0];
      output.schedule_local_rng_word1 = schedule_local_rng[1];
    }
  } else if (schedule_local_rng != nullptr) {
    failure_flags |= trace_capture_failure_identity;
  }

  output.phase_event_database =
      LoadAt<std::uintptr_t>(plan.phase_event_database_slot, 0);
  output.current_date_object =
      LoadAt<std::uintptr_t>(plan.current_date_slot, 0);
  output.global_rng_wrapper =
      LoadAt<std::uintptr_t>(plan.global_rng_wrapper_slot, 0);
  if (output.phase_event_database != plan.expected_phase_event_database ||
      output.current_date_object != plan.expected_current_date_object ||
      output.global_rng_wrapper != plan.expected_global_rng_wrapper) {
    failure_flags |= trace_capture_failure_identity;
  }
  if (output.current_date_object != 0) {
    output.native_date_raw =
        LoadAt<std::int32_t>(output.current_date_object,
                             kCurrentDateRawOffset);
  }
  if (output.global_rng_wrapper != 0) {
    output.global_rng_state = LoadAt<std::uintptr_t>(
        output.global_rng_wrapper, kGlobalRngStateOffset);
  }
  if (output.global_rng_state != plan.expected_global_rng_state) {
    failure_flags |= trace_capture_failure_identity;
  } else {
    output.global_rng_counter = LoadAt<std::uint32_t>(
        output.global_rng_state, kGlobalRngCounterOffset);
    output.global_rng_salt =
        LoadAt<std::uint32_t>(output.global_rng_state,
                              kGlobalRngSaltOffset);
    output.global_rng_owner_thread_token = LoadAt<std::uint32_t>(
        output.global_rng_state, kGlobalRngOwnerThreadOffset);
  }

  output.combat_id = LoadAt<std::int32_t>(plan.combat, kCombatIdOffset);
  output.phase_raw = LoadAt<std::int32_t>(plan.combat, kCombatPhaseOffset);
  output.phase_day =
      LoadAt<std::int32_t>(plan.combat, kCombatPhaseDayOffset);
  output.winner_side_raw =
      LoadAt<std::int32_t>(plan.combat, kCombatWinnerOffset);
  output.battle_result_id =
      LoadAt<std::int32_t>(plan.combat, kCombatBattleResultIdOffset);
  output.battle_result = plan.battle_result;
  output.base_advantage_raw =
      LoadAt<std::int64_t>(plan.combat, kCombatBaseAdvantageOffset);
  output.resolved_advantage_raw =
      LoadAt<std::int64_t>(plan.combat, kCombatResolvedAdvantageOffset);
  output.advantage_rolls_raw[0] =
      LoadAt<std::int32_t>(plan.combat, kCombatAdvantageRoll0Offset);
  output.advantage_rolls_raw[1] =
      LoadAt<std::int32_t>(plan.combat, kCombatAdvantageRoll1Offset);
  if (output.combat_id != plan.combat_id ||
      output.battle_result_id != plan.battle_result_id) {
    failure_flags |= trace_capture_failure_identity;
  }

  if (!ReadSide(plan, 0, output.sides[0], failure_flags) ||
      !ReadSide(plan, 1, output.sides[1], failure_flags) ||
      !ReadCharacters(plan, output, failure_flags) ||
      !ReadAccolades(plan, output, failure_flags) ||
      !ReadBattleEvents(plan, output, failure_flags)) {
    output.capture_failure_flags = failure_flags;
    return false;
  }
  output.full_mutable_transition_bundle_complete = false;
  output.capture_failure_flags = failure_flags;
  return failure_flags == trace_capture_failure_none;
}

bool CaptureWithFaultBoundary(
    CombatPhaseEventTraceRingV1 &ring,
    CombatPhaseEventTraceRingRecordV1 &output,
    CombatPhaseEventTraceBoundaryV1 boundary, void *combat,
    void *trigger_side, const std::uint32_t *schedule_local_rng,
    std::uintptr_t caller_return_address) noexcept {
#if defined(_MSC_VER)
  __try {
    return CaptureUnsafe(ring, output, boundary, combat, trigger_side,
                         schedule_local_rng, caller_return_address);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output.capture_failure_flags |= trace_capture_failure_memory_fault;
    return false;
  }
#else
  return CaptureUnsafe(ring, output, boundary, combat, trigger_side,
                       schedule_local_rng, caller_return_address);
#endif
}

bool AllRecordsMatch(
    const CombatPhaseEventTraceRingDrainV1 &output,
    bool (*predicate)(const CombatPhaseEventTraceRingRecordV1 &,
                      const CombatPhaseEventTraceRingRecordV1 &)) noexcept {
  for (std::size_t index = 1; index < output.record_count; ++index) {
    if (!predicate(output.records[0], output.records[index])) {
      return false;
    }
  }
  return output.record_count == kCombatPhaseEventTraceRingV1RecordCount;
}

bool SameCombat(const CombatPhaseEventTraceRingRecordV1 &left,
                const CombatPhaseEventTraceRingRecordV1 &right) noexcept {
  return left.managed_daily_sequence_token ==
             right.managed_daily_sequence_token &&
         left.combat_id == right.combat_id && left.combat == right.combat &&
         left.battle_result_id == right.battle_result_id &&
         left.battle_result == right.battle_result;
}

bool SameDate(const CombatPhaseEventTraceRingRecordV1 &left,
              const CombatPhaseEventTraceRingRecordV1 &right) noexcept {
  return left.current_date_object == right.current_date_object &&
         left.native_date_raw == right.native_date_raw;
}

bool SameTable(const CombatPhaseEventTraceRingRecordV1 &left,
               const CombatPhaseEventTraceRingRecordV1 &right) noexcept {
  return left.phase_event_database == right.phase_event_database;
}

bool ValidateSideAndReturnIdentity(
    const CombatPhaseEventTraceCapturePlanV1 &plan,
    const CombatPhaseEventTraceRingDrainV1 &output) noexcept {
  if (output.record_count != kCombatPhaseEventTraceRingV1RecordCount) {
    return false;
  }
  for (std::size_t index = 0; index < output.record_count; ++index) {
    const auto boundary =
        static_cast<CombatPhaseEventTraceBoundaryV1>(index);
    if (output.records[index].trigger_side !=
            ExpectedTriggerSide(plan, boundary) ||
        output.records[index].caller_return_address !=
            ExpectedReturnAddress(plan, boundary) ||
        output.records[index].sides[0].side != plan.sides[0] ||
        output.records[index].sides[1].side != plan.sides[1]) {
      return false;
    }
  }
  return true;
}

} // namespace

bool ArmCombatPhaseEventTraceRingV1(
    CombatPhaseEventTraceRingV1 &ring,
    const CombatPhaseEventTraceCapturePlanV1 &plan) noexcept {
  if (!ValidateCapturePlan(plan)) {
    return false;
  }
  if (ring.armed.load(std::memory_order_acquire) != 0 ||
      ring.capture_in_progress.load(std::memory_order_acquire) != 0) {
    return false;
  }
  ring.armed.store(0, std::memory_order_relaxed);
  ring.capture_in_progress.store(0, std::memory_order_relaxed);
  ring.committed_count.store(0, std::memory_order_relaxed);
  ring.failure_flags.store(trace_capture_failure_none,
                           std::memory_order_relaxed);
  ring.plan = plan;
  std::memset(ring.records.data(), 0,
              sizeof(CombatPhaseEventTraceRingRecordV1) *
                  ring.records.size());
  CombatPhaseEventTraceRingV1 *expected = nullptr;
  if (!g_active_ring.compare_exchange_strong(
          expected, &ring, std::memory_order_acq_rel,
          std::memory_order_acquire)) {
    return false;
  }
  ring.armed.store(1, std::memory_order_release);
  return true;
}

void CancelCombatPhaseEventTraceRingV1(
    CombatPhaseEventTraceRingV1 &ring) noexcept {
  ring.armed.store(0, std::memory_order_release);
  CombatPhaseEventTraceRingV1 *expected = &ring;
  (void)g_active_ring.compare_exchange_strong(
      expected, nullptr, std::memory_order_acq_rel,
      std::memory_order_acquire);
}

bool IsCombatPhaseEventTraceRingV1Armed() noexcept {
  const auto *const ring = g_active_ring.load(std::memory_order_acquire);
  return ring != nullptr &&
         ring->armed.load(std::memory_order_acquire) != 0;
}

bool CaptureCombatPhaseEventTraceBoundaryV1(
    CombatPhaseEventTraceBoundaryV1 boundary, void *combat,
    void *trigger_side, const std::uint32_t *schedule_local_rng,
    std::uintptr_t caller_return_address) noexcept {
  auto *const ring = g_active_ring.load(std::memory_order_acquire);
  if (ring == nullptr ||
      ring->armed.load(std::memory_order_acquire) == 0) {
    return false;
  }
  if (ring->capture_in_progress.exchange(1, std::memory_order_acq_rel) != 0) {
    MarkFailure(*ring, trace_capture_failure_reentry);
    return false;
  }
  const auto index = ring->committed_count.load(std::memory_order_acquire);
  if (index >= ring->records.size()) {
    MarkFailure(*ring, trace_capture_failure_ring_full);
    ring->capture_in_progress.store(0, std::memory_order_release);
    return false;
  }
  if (static_cast<std::uint32_t>(boundary) != index) {
    MarkFailure(*ring, trace_capture_failure_sequence);
    ring->capture_in_progress.store(0, std::memory_order_release);
    return false;
  }
  auto &record = ring->records[index];
  const bool captured = CaptureWithFaultBoundary(
      *ring, record, boundary, combat, trigger_side, schedule_local_rng,
      caller_return_address);
  if (!captured) {
    if (record.capture_failure_flags == trace_capture_failure_none) {
      record.capture_failure_flags = trace_capture_failure_identity;
    }
    MarkFailure(*ring, record.capture_failure_flags);
  }
  ring->committed_count.store(index + 1, std::memory_order_release);
  ring->capture_in_progress.store(0, std::memory_order_release);
  return captured;
}

bool CompleteAndDrainCombatPhaseEventTraceRingV1(
    CombatPhaseEventTraceRingV1 &ring,
    CombatPhaseEventTraceRingDrainV1 &output) noexcept {
  const auto final_captured = CaptureCombatPhaseEventTraceBoundaryV1(
      CombatPhaseEventTraceBoundaryV1::paused_next_day_stable_query,
      reinterpret_cast<void *>(ring.plan.combat), nullptr, nullptr, 0);
  if (!final_captured) {
    MarkFailure(ring, trace_capture_failure_final_query);
  }
  CancelCombatPhaseEventTraceRingV1(ring);

  std::memset(&output, 0, sizeof(output));
  output.failure_flags =
      ring.failure_flags.load(std::memory_order_acquire);
  output.record_count = std::min<std::uint32_t>(
      ring.committed_count.load(std::memory_order_acquire),
      static_cast<std::uint32_t>(output.records.size()));
  if (output.record_count > 0) {
    std::memcpy(output.records.data(), ring.records.data(),
                sizeof(CombatPhaseEventTraceRingRecordV1) *
                    output.record_count);
  }

  output.exact_boundary_sequence =
      output.record_count == output.records.size();
  for (std::size_t index = 0;
       output.exact_boundary_sequence && index < output.record_count;
       ++index) {
    output.exact_boundary_sequence =
        output.records[index].boundary ==
            static_cast<CombatPhaseEventTraceBoundaryV1>(index) &&
        output.records[index].capture_failure_flags ==
            trace_capture_failure_none;
  }
  output.same_full_generation_combat =
      AllRecordsMatch(output, &SameCombat);
  output.same_native_date = AllRecordsMatch(output, &SameDate);
  output.same_loaded_event_table = AllRecordsMatch(output, &SameTable);
  output.side_and_return_site_identity =
      ValidateSideAndReturnIdentity(ring.plan, output);
  output.schedule_phase_day_then_single_increment =
      output.record_count == output.records.size() &&
      output.records[0].phase_day == output.records[1].phase_day &&
      output.records[0].phase_day != std::numeric_limits<std::int32_t>::max() &&
      output.records[2].phase_day == output.records[0].phase_day + 1;
  for (std::size_t index = 3;
       output.schedule_phase_day_then_single_increment &&
       index < output.record_count;
       ++index) {
    output.schedule_phase_day_then_single_increment =
        output.records[index].phase_day == output.records[2].phase_day &&
        output.records[index].phase_raw == output.records[2].phase_raw;
  }
  output.full_mutable_transition_bundle_complete = true;
  for (std::size_t index = 0; index < output.record_count; ++index) {
    output.full_mutable_transition_bundle_complete =
        output.full_mutable_transition_bundle_complete &&
        output.records[index].full_mutable_transition_bundle_complete;
  }
  output.bounded_capture_complete =
      output.failure_flags == trace_capture_failure_none &&
      output.exact_boundary_sequence && output.same_full_generation_combat &&
      output.same_native_date && output.same_loaded_event_table &&
      output.side_and_return_site_identity &&
      output.schedule_phase_day_then_single_increment;
  // Deliberately independent gates: bounded native capture is useful ABI
  // progress, but it cannot claim transition parity while the mutable bundle
  // is incomplete and no paused live seven-record fixture exists.
  output.production_trace_ready =
      output.bounded_capture_complete &&
      output.full_mutable_transition_bundle_complete && false;
  return output.bounded_capture_complete;
}

bool BindCombatPhaseEventTraceOriginalTrampolinesV1(
    CombatPhaseEventScheduleOriginalV1 schedule,
    CombatPhaseEventFireOriginalV1 fire) noexcept {
  if (schedule == nullptr || fire == nullptr) {
    return false;
  }
  g_original_schedule.store(schedule, std::memory_order_release);
  g_original_fire.store(fire, std::memory_order_release);
  return true;
}

extern "C" std::uintptr_t __fastcall
XarCombatPhaseEventScheduleHookV1(void *side,
                                  std::uint32_t *schedule_local_rng,
                                  void *target_province) noexcept {
  const auto return_address =
      reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  auto *const ring = g_active_ring.load(std::memory_order_acquire);
  if (ring != nullptr &&
      ring->armed.load(std::memory_order_acquire) != 0 &&
      reinterpret_cast<std::uintptr_t>(side) == ring->plan.sides[0] &&
      return_address ==
          ring->plan.module_base +
              kCombatPhaseEventScheduleSide0ReturnRva) {
    (void)CaptureCombatPhaseEventTraceBoundaryV1(
        CombatPhaseEventTraceBoundaryV1::before_side0_schedule,
        reinterpret_cast<void *>(ring->plan.combat), side,
        schedule_local_rng, return_address);
  }

  const auto original = g_original_schedule.load(std::memory_order_acquire);
  if (original == nullptr) {
    if (ring != nullptr) {
      MarkFailure(*ring, trace_capture_failure_original_trampoline);
    }
    return 0;
  }
  const auto result = original(side, schedule_local_rng, target_province);

  if (ring != nullptr &&
      ring->armed.load(std::memory_order_acquire) != 0 &&
      reinterpret_cast<std::uintptr_t>(side) == ring->plan.sides[1] &&
      return_address ==
          ring->plan.module_base +
              kCombatPhaseEventScheduleSide1ReturnRva) {
    (void)CaptureCombatPhaseEventTraceBoundaryV1(
        CombatPhaseEventTraceBoundaryV1::after_side1_schedule,
        reinterpret_cast<void *>(ring->plan.combat), side,
        schedule_local_rng, return_address);
  }
  return result;
}

extern "C" std::uintptr_t __fastcall
XarCombatPhaseEventFireHookV1(void *side) noexcept {
  const auto return_address =
      reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  auto *const ring = g_active_ring.load(std::memory_order_acquire);
  CombatPhaseEventTraceBoundaryV1 before =
      CombatPhaseEventTraceBoundaryV1::before_side0_phase_fire;
  CombatPhaseEventTraceBoundaryV1 after =
      CombatPhaseEventTraceBoundaryV1::after_side0_phase_fire;
  bool capture = false;
  if (ring != nullptr &&
      ring->armed.load(std::memory_order_acquire) != 0) {
    if (reinterpret_cast<std::uintptr_t>(side) == ring->plan.sides[0] &&
        return_address ==
            ring->plan.module_base + kCombatPhaseEventFireSide0ReturnRva) {
      capture = true;
    } else if (
        reinterpret_cast<std::uintptr_t>(side) == ring->plan.sides[1] &&
        return_address ==
            ring->plan.module_base + kCombatPhaseEventFireSide1ReturnRva) {
      capture = true;
      before = CombatPhaseEventTraceBoundaryV1::before_side1_phase_fire;
      after = CombatPhaseEventTraceBoundaryV1::after_side1_phase_fire;
    }
  }
  if (capture) {
    (void)CaptureCombatPhaseEventTraceBoundaryV1(
        before, reinterpret_cast<void *>(ring->plan.combat), side, nullptr,
        return_address);
  }

  const auto original = g_original_fire.load(std::memory_order_acquire);
  if (original == nullptr) {
    if (ring != nullptr) {
      MarkFailure(*ring, trace_capture_failure_original_trampoline);
    }
    return 0;
  }
  const auto result = original(side);

  if (capture && ring->armed.load(std::memory_order_acquire) != 0) {
    (void)CaptureCombatPhaseEventTraceBoundaryV1(
        after, reinterpret_cast<void *>(ring->plan.combat), side, nullptr,
        return_address);
  }
  return result;
}

} // namespace xar::ck3_11906
