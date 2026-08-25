#include "xar_bridge/combat_phase_event_trace_managed_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <charconv>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <string>

namespace xar::ck3_11906 {
namespace {

constexpr std::uintptr_t kPhaseEventDatabaseSlotRva = 0x57C7930;
constexpr std::uintptr_t kCurrentDateSlotRva = 0x570E068;
constexpr std::uintptr_t kGlobalRngWrapperSlotRva = 0x4FEB1C8;
constexpr std::uintptr_t kBattleResultStorageSlotRva = 0x57C0328;
constexpr std::uintptr_t kBattleResultFallbackSlotRva = 0x57C0320;
constexpr std::uintptr_t kBattleEventVtableRva = 0x41461A0;
constexpr std::uintptr_t kAccoladeStorageSlotRva = 0x57BF1E0;
constexpr std::uintptr_t kAccoladeFallbackSlotRva = 0x57BF198;
constexpr std::uintptr_t kAccoladeRankThresholdDataSlotRva = 0x4F62B98;
constexpr std::uintptr_t kAccoladeRankThresholdCountSlotRva = 0x4F62BA4;

constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageObjectOffset = 0x08;
constexpr std::int32_t kMaximumComponents = 4'194'304;

constexpr std::size_t kCombatIdOffset = 0x08;
constexpr std::size_t kCombatSide0Offset = 0x20;
constexpr std::size_t kCombatSide1Offset = 0x368;
constexpr std::size_t kCombatBattleResultIdOffset = 0x708;
constexpr std::size_t kSideArmyHeaderOffset = 0x10;
constexpr std::size_t kSideKnightHeaderOffset = 0x40;
constexpr std::size_t kSideSelectedCommanderOffset = 0x74;
constexpr std::size_t kSideCombatBackPointerOffset = 0xB8;
constexpr std::size_t kSideKnightStride = 0x60;
constexpr std::size_t kSideKnightRegimentIdOffset = 0x08;
constexpr std::size_t kArmyIdOffset = 0x10;
constexpr std::size_t kArmyCommanderOffset = 0x120;
constexpr std::size_t kArmyCombatIdOffset = 0x128;
constexpr std::size_t kRegimentIdOffset = 0x10;
constexpr std::size_t kRegimentArmyIdOffset = 0x140;
constexpr std::size_t kRegimentCharacterIdOffset = 0x148;
constexpr std::size_t kCharacterIdOffset = 0x18;
constexpr std::size_t kCharacterAccoladeLinkOffset = 0x1A8;
constexpr std::size_t kCharacterLinkAccoladeIdOffset = 0x568;
constexpr std::size_t kAccoladeIdOffset = 0x08;
constexpr std::size_t kAccoladeOwnerCharacterIdOffset = 0x70;
constexpr std::size_t kBattleResultIdOffset = 0x08;
constexpr std::size_t kBattleEventHeaderOffset = 0x188;
constexpr std::size_t kBattleEventStride = 0x38;
constexpr std::size_t kBattleEventLeftCharacterOffset = 0x08;
constexpr std::size_t kBattleEventRightCharacterOffset = 0x0C;
constexpr std::size_t kCurrentDateRawOffset = 0x08;
constexpr std::size_t kGlobalRngStateOffset = 0x00;
constexpr std::int32_t kDateUnitsPerDay = 24;

template <typename T>
T LoadAt(std::uintptr_t base, std::size_t offset = 0) noexcept {
  T output{};
  std::memcpy(&output, reinterpret_cast<const void *>(base + offset),
              sizeof(output));
  return output;
}

template <typename T>
T LoadAt(const void *base, std::size_t offset = 0) noexcept {
  return LoadAt<T>(reinterpret_cast<std::uintptr_t>(base), offset);
}

std::uintptr_t ResolveAddress(std::uintptr_t override_address,
                              std::uintptr_t module_base,
                              std::uintptr_t rva) noexcept {
  return override_address != 0 ? override_address : module_base + rva;
}

void *ResolveStoredComponent(void **storage_slot, std::int32_t full_id,
                             std::size_t identity_offset) noexcept {
  if (storage_slot == nullptr || full_id <= 0) {
    return nullptr;
  }
  void *const storage = *storage_slot;
  if (storage == nullptr) {
    return nullptr;
  }
  void *const slots = LoadAt<void *>(storage, kStorageSlotsOffset);
  const auto capacity = LoadAt<std::int32_t>(storage,
                                             kStorageCapacityOffset);
  const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 || capacity > kMaximumComponents ||
      index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  void *const object = LoadAt<void *>(
      slots, static_cast<std::size_t>(index) * kStorageSlotStride +
                 kStorageObjectOffset);
  if (object == nullptr ||
      LoadAt<std::int32_t>(object, identity_offset) != full_id) {
    return nullptr;
  }
  return object;
}

bool ReadVector(std::uintptr_t owner, std::size_t offset,
                std::uint32_t maximum, std::uintptr_t &data,
                std::uint32_t &count) noexcept {
  const auto header = owner + offset;
  data = LoadAt<std::uintptr_t>(header);
  const auto capacity = LoadAt<std::int32_t>(header, 0x08);
  const auto signed_count = LoadAt<std::int32_t>(header, 0x0C);
  if (capacity < 0 || signed_count < 0 || signed_count > capacity ||
      static_cast<std::uint32_t>(signed_count) > maximum ||
      (signed_count > 0 && data == 0)) {
    return false;
  }
  count = static_cast<std::uint32_t>(signed_count);
  return true;
}

bool Int32VectorContains(std::uintptr_t data, std::uint32_t count,
                         std::int32_t value) noexcept {
  for (std::uint32_t index = 0; index < count; ++index) {
    if (LoadAt<std::int32_t>(data, index * sizeof(std::int32_t)) == value) {
      return true;
    }
  }
  return false;
}

template <std::size_t Size>
bool AddObjectRef(std::array<CombatPhaseEventTraceObjectRefV1, Size> &rows,
                  std::uint32_t &count, std::int32_t full_id,
                  void *object) noexcept {
  if (full_id <= 0 || object == nullptr) {
    return false;
  }
  for (std::uint32_t index = 0; index < count; ++index) {
    if (rows[index].full_id == full_id) {
      return rows[index].object == reinterpret_cast<std::uintptr_t>(object);
    }
  }
  if (count >= rows.size()) {
    return false;
  }
  rows[count++] = {full_id, reinterpret_cast<std::uintptr_t>(object)};
  return true;
}

template <std::size_t Size>
void SortObjectRefs(
    std::array<CombatPhaseEventTraceObjectRefV1, Size> &rows,
    std::uint32_t count) noexcept {
  std::sort(rows.begin(), rows.begin() + count,
            [](const auto &left, const auto &right) {
              return left.full_id < right.full_id;
            });
}

bool AddCharacter(const Bindings &bindings,
                  CombatPhaseEventTraceCapturePlanV1 &plan,
                  std::int32_t character_id) noexcept {
  if (character_id == -1) {
    return true;
  }
  void *const character = ResolveStoredComponent(
      bindings.character_storage_slot, character_id, kCharacterIdOffset);
  return AddObjectRef(plan.characters, plan.character_count, character_id,
                      character);
}

BuildCombatPhaseEventTraceCapturePlanV1Result BuildPlanUnsafe(
    const Bindings &bindings,
    const CombatPhaseEventTracePlanEnvironmentV1 &environment,
    std::int32_t combat_id, std::uint64_t managed_daily_sequence_token,
    CombatPhaseEventTraceCapturePlanV1 &output) noexcept {
  output = {};
  if (!environment.exact_build_admitted || !bindings.enabled ||
      environment.module_base == 0) {
    return BuildCombatPhaseEventTraceCapturePlanV1Result::
        exact_build_rejected;
  }
  if (combat_id <= 0 || managed_daily_sequence_token == 0 ||
      bindings.combat_storage_slot == nullptr ||
      bindings.army_internal_storage_slot == nullptr ||
      bindings.regiment_storage_slot == nullptr ||
      bindings.character_storage_slot == nullptr) {
    return BuildCombatPhaseEventTraceCapturePlanV1Result::invalid_request;
  }

  output.managed_daily_sequence_token = managed_daily_sequence_token;
  output.module_base = environment.module_base;
  output.combat_id = combat_id;
  void *const combat = ResolveStoredComponent(
      bindings.combat_storage_slot, combat_id, kCombatIdOffset);
  if (combat == nullptr) {
    return BuildCombatPhaseEventTraceCapturePlanV1Result::combat_unavailable;
  }
  output.combat = reinterpret_cast<std::uintptr_t>(combat);
  output.sides = {output.combat + kCombatSide0Offset,
                  output.combat + kCombatSide1Offset};
  if (LoadAt<std::uintptr_t>(output.sides[0],
                             kSideCombatBackPointerOffset) != output.combat ||
      LoadAt<std::uintptr_t>(output.sides[1],
                             kSideCombatBackPointerOffset) != output.combat) {
    return BuildCombatPhaseEventTraceCapturePlanV1Result::combat_unavailable;
  }

  output.phase_event_database_slot = ResolveAddress(
      environment.phase_event_database_slot_override,
      environment.module_base, kPhaseEventDatabaseSlotRva);
  output.current_date_slot = ResolveAddress(
      environment.current_date_slot_override, environment.module_base,
      kCurrentDateSlotRva);
  output.global_rng_wrapper_slot = ResolveAddress(
      environment.global_rng_wrapper_slot_override, environment.module_base,
      kGlobalRngWrapperSlotRva);
  output.expected_phase_event_database =
      LoadAt<std::uintptr_t>(output.phase_event_database_slot);
  output.expected_current_date_object =
      LoadAt<std::uintptr_t>(output.current_date_slot);
  output.expected_global_rng_wrapper =
      LoadAt<std::uintptr_t>(output.global_rng_wrapper_slot);
  output.expected_global_rng_state =
      output.expected_global_rng_wrapper == 0
          ? 0
          : LoadAt<std::uintptr_t>(output.expected_global_rng_wrapper,
                                   kGlobalRngStateOffset);
  if (output.expected_phase_event_database == 0 ||
      output.expected_current_date_object == 0 ||
      output.expected_global_rng_wrapper == 0 ||
      output.expected_global_rng_state == 0) {
    return BuildCombatPhaseEventTraceCapturePlanV1Result::
        native_slot_unavailable;
  }

  for (std::size_t side_index = 0; side_index < output.sides.size();
       ++side_index) {
    const auto side = output.sides[side_index];
    std::uintptr_t army_ids = 0;
    std::uint32_t army_count = 0;
    if (!ReadVector(side, kSideArmyHeaderOffset,
                    kCombatPhaseEventTraceRingV1MaximumArmiesPerSide,
                    army_ids, army_count)) {
      return BuildCombatPhaseEventTraceCapturePlanV1Result::roster_unavailable;
    }
    for (std::uint32_t index = 0; index < army_count; ++index) {
      const auto army_id = LoadAt<std::int32_t>(army_ids, index * 4U);
      void *const army = ResolveStoredComponent(
          bindings.army_internal_storage_slot, army_id, kArmyIdOffset);
      if (army == nullptr ||
          LoadAt<std::int32_t>(army, kArmyCombatIdOffset) != combat_id ||
          !AddObjectRef(output.armies, output.army_count, army_id, army) ||
          !AddCharacter(bindings, output,
                        LoadAt<std::int32_t>(army,
                                             kArmyCommanderOffset))) {
        return output.army_count >= output.armies.size() ||
                       output.character_count >= output.characters.size()
                   ? BuildCombatPhaseEventTraceCapturePlanV1Result::
                         capacity_exceeded
                   : BuildCombatPhaseEventTraceCapturePlanV1Result::
                         roster_unavailable;
      }
    }

    std::uintptr_t knight_rows = 0;
    std::uint32_t knight_count = 0;
    if (!ReadVector(side, kSideKnightHeaderOffset,
                    kCombatPhaseEventTraceRingV1MaximumRegimentsPerSide,
                    knight_rows, knight_count)) {
      return BuildCombatPhaseEventTraceCapturePlanV1Result::roster_unavailable;
    }
    for (std::uint32_t index = 0; index < knight_count; ++index) {
      const auto row = knight_rows + index * kSideKnightStride;
      const auto regiment_id =
          LoadAt<std::int32_t>(row, kSideKnightRegimentIdOffset);
      void *const regiment = ResolveStoredComponent(
          bindings.regiment_storage_slot, regiment_id, kRegimentIdOffset);
      const auto army_id = regiment == nullptr
                               ? -1
                               : LoadAt<std::int32_t>(regiment,
                                                      kRegimentArmyIdOffset);
      void *const army = ResolveStoredComponent(
          bindings.army_internal_storage_slot, army_id, kArmyIdOffset);
      if (regiment == nullptr || army == nullptr ||
          !Int32VectorContains(army_ids, army_count, army_id) ||
          LoadAt<std::int32_t>(army, kArmyCombatIdOffset) != combat_id ||
          !AddObjectRef(output.regiments, output.regiment_count, regiment_id,
                        regiment) ||
          !AddCharacter(bindings, output,
                        LoadAt<std::int32_t>(regiment,
                                             kRegimentCharacterIdOffset))) {
        return output.regiment_count >= output.regiments.size() ||
                       output.character_count >= output.characters.size()
                   ? BuildCombatPhaseEventTraceCapturePlanV1Result::
                         capacity_exceeded
                   : BuildCombatPhaseEventTraceCapturePlanV1Result::
                         roster_unavailable;
      }
    }
    if (!AddCharacter(bindings, output,
                      LoadAt<std::int32_t>(side,
                                           kSideSelectedCommanderOffset))) {
      return BuildCombatPhaseEventTraceCapturePlanV1Result::roster_unavailable;
    }
  }

  void **const battle_storage =
      environment.battle_result_storage_slot_override != nullptr
          ? environment.battle_result_storage_slot_override
          : reinterpret_cast<void **>(environment.module_base +
                                      kBattleResultStorageSlotRva);
  void *const battle_fallback =
      environment.offline_fixture
          ? environment.battle_result_fallback_override
          : LoadAt<void *>(environment.module_base +
                           kBattleResultFallbackSlotRva);
  output.battle_result_id =
      LoadAt<std::int32_t>(combat, kCombatBattleResultIdOffset);
  void *const battle_result = ResolveStoredComponent(
      battle_storage, output.battle_result_id, kBattleResultIdOffset);
  if (battle_result == nullptr || battle_result == battle_fallback) {
    return BuildCombatPhaseEventTraceCapturePlanV1Result::
        battle_result_unavailable;
  }
  output.battle_result = reinterpret_cast<std::uintptr_t>(battle_result);
  output.expected_battle_event_vtable = ResolveAddress(
      environment.battle_event_vtable_override, environment.module_base,
      kBattleEventVtableRva);
  std::uintptr_t battle_rows = 0;
  std::uint32_t battle_count = 0;
  if (!ReadVector(output.battle_result, kBattleEventHeaderOffset,
                  kCombatPhaseEventTraceRingV1MaximumBattleEvents,
                  battle_rows, battle_count)) {
    return BuildCombatPhaseEventTraceCapturePlanV1Result::
        battle_result_unavailable;
  }
  for (std::uint32_t index = 0; index < battle_count; ++index) {
    const auto row = battle_rows + index * kBattleEventStride;
    if (LoadAt<std::uintptr_t>(row) !=
        output.expected_battle_event_vtable) {
      return BuildCombatPhaseEventTraceCapturePlanV1Result::
          battle_result_unavailable;
    }
    if (!AddCharacter(bindings, output,
                      LoadAt<std::int32_t>(
                          row, kBattleEventLeftCharacterOffset)) ||
        !AddCharacter(bindings, output,
                      LoadAt<std::int32_t>(
                          row, kBattleEventRightCharacterOffset))) {
      return BuildCombatPhaseEventTraceCapturePlanV1Result::roster_unavailable;
    }
  }

  SortObjectRefs(output.armies, output.army_count);
  SortObjectRefs(output.regiments, output.regiment_count);
  SortObjectRefs(output.characters, output.character_count);

  output.accolade_rank_threshold_data_slot = ResolveAddress(
      environment.accolade_rank_threshold_data_slot_override,
      environment.module_base, kAccoladeRankThresholdDataSlotRva);
  output.accolade_rank_threshold_count_slot = ResolveAddress(
      environment.accolade_rank_threshold_count_slot_override,
      environment.module_base, kAccoladeRankThresholdCountSlotRva);
  output.expected_accolade_rank_threshold_data =
      LoadAt<std::uintptr_t>(output.accolade_rank_threshold_data_slot);
  const auto threshold_count = LoadAt<std::int32_t>(
      output.accolade_rank_threshold_count_slot);
  if (output.expected_accolade_rank_threshold_data == 0 ||
      threshold_count <= 0 ||
      static_cast<std::size_t>(threshold_count) >
          output.accolade_rank_thresholds_raw.size()) {
    return threshold_count > static_cast<std::int32_t>(
                                 output.accolade_rank_thresholds_raw.size())
               ? BuildCombatPhaseEventTraceCapturePlanV1Result::
                     capacity_exceeded
               : BuildCombatPhaseEventTraceCapturePlanV1Result::
                     accolade_unavailable;
  }
  output.accolade_rank_threshold_count =
      static_cast<std::uint32_t>(threshold_count);
  for (std::uint32_t index = 0;
       index < output.accolade_rank_threshold_count; ++index) {
    output.accolade_rank_thresholds_raw[index] = LoadAt<std::int64_t>(
        output.expected_accolade_rank_threshold_data,
        index * sizeof(std::int64_t));
  }

  void **const accolade_storage =
      environment.accolade_storage_slot_override != nullptr
          ? environment.accolade_storage_slot_override
          : reinterpret_cast<void **>(environment.module_base +
                                      kAccoladeStorageSlotRva);
  void *const accolade_fallback =
      environment.offline_fixture
          ? environment.accolade_fallback_override
          : LoadAt<void *>(environment.module_base +
                           kAccoladeFallbackSlotRva);
  for (std::uint32_t index = 0; index < output.character_count; ++index) {
    const auto &character_ref = output.characters[index];
    const auto link = LoadAt<std::uintptr_t>(
        character_ref.object, kCharacterAccoladeLinkOffset);
    if (link == 0) {
      continue;
    }
    const auto accolade_id = LoadAt<std::int32_t>(
        link, kCharacterLinkAccoladeIdOffset);
    if (accolade_id == -1) {
      continue;
    }
    void *const accolade = ResolveStoredComponent(
        accolade_storage, accolade_id, kAccoladeIdOffset);
    if (accolade == nullptr || accolade == accolade_fallback) {
      return BuildCombatPhaseEventTraceCapturePlanV1Result::
          accolade_unavailable;
    }
    const auto owner = LoadAt<std::int32_t>(
        accolade, kAccoladeOwnerCharacterIdOffset);
    bool duplicate = false;
    for (std::uint32_t row_index = 0;
         row_index < output.accolade_count; ++row_index) {
      auto &row = output.accolades[row_index];
      if (row.accolade_id == accolade_id) {
        duplicate = true;
        if (row.accolade != reinterpret_cast<std::uintptr_t>(accolade) ||
            row.acclaimed_knight_character_id != character_ref.full_id ||
            row.owner_character_id != owner) {
          return BuildCombatPhaseEventTraceCapturePlanV1Result::
              accolade_unavailable;
        }
      }
    }
    if (!duplicate) {
      if (owner <= 0 || output.accolade_count >= output.accolades.size()) {
        return output.accolade_count >= output.accolades.size()
                   ? BuildCombatPhaseEventTraceCapturePlanV1Result::
                         capacity_exceeded
                   : BuildCombatPhaseEventTraceCapturePlanV1Result::
                         accolade_unavailable;
      }
      output.accolades[output.accolade_count++] = {
          accolade_id, reinterpret_cast<std::uintptr_t>(accolade), owner,
          character_ref.full_id, character_ref.object};
    }
  }
  std::sort(output.accolades.begin(),
            output.accolades.begin() + output.accolade_count,
            [](const auto &left, const auto &right) {
              return left.accolade_id < right.accolade_id;
            });
  return BuildCombatPhaseEventTraceCapturePlanV1Result::built;
}

bool StampIsExact(const MainThreadQueryMailboxV1 &mailbox,
                  const MainThreadQueryTicketV1 &ticket,
                  MainThreadQueryExecutorV1 executor, void *context,
                  const MainThreadExecutionStampV1 &stamp) noexcept {
  return ticket.sequence != 0 && stamp.pump_epoch != 0 &&
         stamp.thread_id != 0 && stamp.paused &&
         stamp.tls_initialized_flag_address != 0 &&
         stamp.tls_initialized == 1 && stamp.tls_context != 0 &&
         stamp.tls_main_thread_marker == 1 && stamp.jomini_state != 0 &&
         stamp.game_state != 0 && GetCurrentThreadId() == stamp.thread_id &&
         mailbox.state.load(std::memory_order_acquire) ==
             MainThreadQueryMailboxStateV1::executing &&
         !mailbox.stop_requested.load(std::memory_order_acquire) &&
         mailbox.failure_flags.load(std::memory_order_acquire) == 0 &&
         mailbox.published_sequence.load(std::memory_order_acquire) ==
             ticket.sequence &&
         mailbox.owner_thread_id.load(std::memory_order_acquire) ==
             stamp.thread_id &&
         mailbox.paused_owner_verified_pump_epochs.load(
             std::memory_order_acquire) >=
             kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs &&
         mailbox.executor == executor && mailbox.executor_context == context;
}

CombatPhaseEventTraceManagedCheckpointV1 MakeCheckpoint(
    const MainThreadExecutionStampV1 &stamp, std::int32_t combat_id,
    std::uint64_t token) noexcept {
  return {token, stamp.pump_epoch, stamp.thread_id, stamp.date_raw,
          combat_id, stamp.paused};
}

bool CurrentDateMatchesPlan(
    const CombatPhaseEventTraceCapturePlanV1 &plan,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  return LoadAt<std::uintptr_t>(plan.current_date_slot) ==
             plan.expected_current_date_object &&
         LoadAt<std::int32_t>(plan.expected_current_date_object,
                              kCurrentDateRawOffset) == stamp.date_raw;
}

void MarkBeginRejected(CombatPhaseEventTraceBeginContextV1 &query) noexcept {
  query.completion =
      CombatPhaseEventTraceManagedCompletionV1::infrastructure_rejected;
  if (query.session != nullptr) {
    query.session->stage = CombatPhaseEventTraceManagedStageV1::failed;
  }
}

void MarkFinishRejected(CombatPhaseEventTraceFinishContextV1 &query) noexcept {
  query.completion =
      CombatPhaseEventTraceManagedCompletionV1::infrastructure_rejected;
  if (query.session != nullptr) {
    query.session->stage = CombatPhaseEventTraceManagedStageV1::failed;
  }
}

template <typename Value>
bool AppendNumber(std::string &output, Value value) {
  std::array<char, 32> buffer{};
  const auto encoded =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (encoded.ec != std::errc{}) {
    return false;
  }
  output.append(buffer.data(), encoded.ptr);
  return output.size() <= kCombatPhaseEventTraceWireMaximumBytesV1;
}

bool AppendCheckpoint(std::string &output,
                      const CombatPhaseEventTraceManagedCheckpointV1 &value) {
  output += "{\"managed_daily_sequence_token\":";
  if (!AppendNumber(output, value.managed_daily_sequence_token)) return false;
  output += ",\"pump_epoch\":";
  if (!AppendNumber(output, value.pump_epoch)) return false;
  output += ",\"thread_id\":";
  if (!AppendNumber(output, value.thread_id)) return false;
  output += ",\"date_raw\":";
  if (!AppendNumber(output, value.date_raw)) return false;
  output += ",\"combat_id\":";
  if (!AppendNumber(output, value.combat_id)) return false;
  output += ",\"paused\":";
  output += value.paused ? "true}" : "false}";
  return output.size() <= kCombatPhaseEventTraceWireMaximumBytesV1;
}

} // namespace

BuildCombatPhaseEventTraceCapturePlanV1Result
BuildCombatPhaseEventTraceCapturePlanV1(
    const Bindings &bindings,
    const CombatPhaseEventTracePlanEnvironmentV1 &environment,
    std::int32_t combat_id, std::uint64_t managed_daily_sequence_token,
    CombatPhaseEventTraceCapturePlanV1 &output) noexcept {
#if defined(_MSC_VER)
  __try {
    return BuildPlanUnsafe(bindings, environment, combat_id,
                           managed_daily_sequence_token, output);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = {};
    return BuildCombatPhaseEventTraceCapturePlanV1Result::memory_fault;
  }
#else
  return BuildPlanUnsafe(bindings, environment, combat_id,
                         managed_daily_sequence_token, output);
#endif
}

bool ExecuteCombatPhaseEventTraceBeginV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *const query =
      static_cast<CombatPhaseEventTraceBeginContextV1 *>(opaque_context);
  if (query == nullptr || query->mailbox == nullptr ||
      !StampIsExact(*query->mailbox, query->ticket,
                    &ExecuteCombatPhaseEventTraceBeginV1, query, stamp) ||
      query->session == nullptr || query->bindings == nullptr ||
      query->completion !=
          CombatPhaseEventTraceManagedCompletionV1::not_executed ||
      query->executor_invocations != 0 ||
      query->session->stage != CombatPhaseEventTraceManagedStageV1::idle) {
    if (query != nullptr) {
      MarkBeginRejected(*query);
    }
    return false;
  }

  try {
    ++query->executor_invocations;
    auto &session = *query->session;
    session.recoverable_checkpoint_created =
        query->recoverable_checkpoint_created;
    if (!query->recoverable_checkpoint_created || query->combat_id <= 0 ||
        query->managed_daily_sequence_token == 0 ||
        query->plan_environment.module_base == 0 ||
        query->detour_environment.module_base !=
            query->plan_environment.module_base ||
        !query->detour_environment.exact_build_admitted) {
      session.stage = CombatPhaseEventTraceManagedStageV1::failed;
      query->completion =
          CombatPhaseEventTraceManagedCompletionV1::trace_unavailable;
      return true;
    }
    session.plan_result = BuildCombatPhaseEventTraceCapturePlanV1(
        *query->bindings, query->plan_environment, query->combat_id,
        query->managed_daily_sequence_token, session.plan);
    if (session.plan_result !=
            BuildCombatPhaseEventTraceCapturePlanV1Result::built ||
        !CurrentDateMatchesPlan(session.plan, stamp)) {
      session.stage = CombatPhaseEventTraceManagedStageV1::failed;
      query->completion =
          CombatPhaseEventTraceManagedCompletionV1::trace_unavailable;
      return true;
    }

    auto detour_environment = query->detour_environment;
    detour_environment.managed_paused_quiescence_proven = true;
    if (!InstallCombatPhaseEventTraceDetoursV1(session.detours,
                                               detour_environment)) {
      session.stage = CombatPhaseEventTraceManagedStageV1::failed;
      query->completion =
          CombatPhaseEventTraceManagedCompletionV1::trace_unavailable;
      return true;
    }
    if (!ArmCombatPhaseEventTraceRingV1(session.ring, session.plan)) {
      const bool uninstalled =
          UninstallCombatPhaseEventTraceDetoursV1(session.detours);
      session.detours_uninstalled = uninstalled;
      session.stage = CombatPhaseEventTraceManagedStageV1::failed;
      query->completion = uninstalled
                              ? CombatPhaseEventTraceManagedCompletionV1::
                                    trace_unavailable
                              : CombatPhaseEventTraceManagedCompletionV1::
                                    infrastructure_rejected;
      return uninstalled;
    }
    session.before = MakeCheckpoint(stamp, query->combat_id,
                                    query->managed_daily_sequence_token);
    session.stage =
        CombatPhaseEventTraceManagedStageV1::armed_waiting_for_one_day;
    query->completion = CombatPhaseEventTraceManagedCompletionV1::armed;
    return true;
  } catch (...) {
    MarkBeginRejected(*query);
    return false;
  }
}

bool ExecuteCombatPhaseEventTraceFinishV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *const query =
      static_cast<CombatPhaseEventTraceFinishContextV1 *>(opaque_context);
  if (query == nullptr || query->mailbox == nullptr ||
      !StampIsExact(*query->mailbox, query->ticket,
                    &ExecuteCombatPhaseEventTraceFinishV1, query, stamp) ||
      query->session == nullptr ||
      query->completion !=
          CombatPhaseEventTraceManagedCompletionV1::not_executed ||
      query->executor_invocations != 0 ||
      query->session->stage != CombatPhaseEventTraceManagedStageV1::
                                   armed_waiting_for_one_day ||
      query->managed_daily_sequence_token == 0 ||
      query->session->before.managed_daily_sequence_token !=
          query->managed_daily_sequence_token) {
    if (query != nullptr) {
      MarkFinishRejected(*query);
    }
    return false;
  }

  try {
    ++query->executor_invocations;
    auto &session = *query->session;
    session.after = MakeCheckpoint(
        stamp, session.plan.combat_id, query->managed_daily_sequence_token);
    session.exact_one_day_observed =
        session.before.paused && session.after.paused &&
        session.before.thread_id == session.after.thread_id &&
        session.before.date_raw <=
            std::numeric_limits<std::int32_t>::max() - kDateUnitsPerDay &&
        session.after.date_raw ==
            session.before.date_raw + kDateUnitsPerDay &&
        CurrentDateMatchesPlan(session.plan, stamp);

    (void)CompleteAndDrainCombatPhaseEventTraceRingV1(session.ring,
                                                       session.drain);
    session.detours_uninstalled =
        UninstallCombatPhaseEventTraceDetoursV1(session.detours);
    if (!session.detours_uninstalled) {
      MarkFinishRejected(*query);
      return false;
    }
    session.serialized_drain =
        SerializeCombatPhaseEventTraceRingDrainV1(session.drain);
    session.stage = CombatPhaseEventTraceManagedStageV1::drained;
    if (session.exact_one_day_observed &&
        session.drain.bounded_capture_complete &&
        !session.serialized_drain.empty()) {
      query->completion = CombatPhaseEventTraceManagedCompletionV1::
          bounded_trace_available;
    } else {
      query->completion =
          CombatPhaseEventTraceManagedCompletionV1::trace_unavailable;
    }
    return true;
  } catch (...) {
    MarkFinishRejected(*query);
    return false;
  }
}

std::string SerializeCombatPhaseEventTraceManagedResultV1(
    const CombatPhaseEventTraceManagedSessionV1 &session) {
  if (session.stage != CombatPhaseEventTraceManagedStageV1::drained ||
      session.serialized_drain.empty()) {
    return {};
  }
  std::string output;
  output.reserve(session.serialized_drain.size() + 512U);
  output += "{\"schema_version\":1,\"managed_checkpoint\":{";
  output += "\"recoverable_checkpoint_created\":";
  output += session.recoverable_checkpoint_created ? "true" : "false";
  output += ",\"exact_one_day_observed\":";
  output += session.exact_one_day_observed ? "true" : "false";
  output += ",\"detours_uninstalled\":";
  output += session.detours_uninstalled ? "true" : "false";
  output += ",\"before\":";
  if (!AppendCheckpoint(output, session.before)) return {};
  output += ",\"after\":";
  if (!AppendCheckpoint(output, session.after)) return {};
  output += "},\"trace\":";
  output += session.serialized_drain;
  output.push_back('}');
  return output.size() <= kCombatPhaseEventTraceWireMaximumBytesV1
             ? output
             : std::string{};
}

} // namespace xar::ck3_11906
