#include "xar_bridge/battle_terminal_journal_v1.hpp"

#include <intrin.h>

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>

namespace xar::ck3_11906 {
namespace {

constexpr std::array<std::uint8_t,
                     kBattleTerminalFinalizerPatchBytesV1>
    kTerminalPrologue{
        0x48, 0x8B, 0xC4, 0x88, 0x50, 0x10, 0x48, 0x89, 0x48, 0x08,
        0x53, 0x55, 0x48, 0x81, 0xEC, 0xC8, 0x00, 0x00, 0x00};
constexpr std::array<std::uint8_t,
                     kBattleWarscoreWriterPatchBytesV1>
    kWarscorePrologue{
        0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C,
        0x24, 0x18, 0x56, 0x57, 0x41, 0x54, 0x41, 0x56};

constexpr std::size_t kComponentStorageSlotsOffset = 0x20;
constexpr std::size_t kComponentStorageCapacityOffset = 0x2C;
constexpr std::size_t kComponentStorageSlotSize = 0x10;
constexpr std::size_t kComponentStorageSlotObjectOffset = 0x08;
constexpr std::int32_t kMaximumComponentCapacity = 1'000'000;
constexpr std::size_t kGameStateDateRawOffset = 0x08;
constexpr std::size_t kCombatIdOffset = 0x08;
constexpr std::size_t kCombatAttackerSideOffset = 0x20;
constexpr std::size_t kCombatDefenderSideOffset = 0x368;
constexpr std::size_t kCombatPhaseOffset = 0x6B0;
constexpr std::size_t kCombatProvinceOffset = 0x6B8;
constexpr std::size_t kCombatWinnerOffset = 0x6E0;
constexpr std::size_t kCombatFinalizedOffset = 0x704;
constexpr std::size_t kCombatDailyGuardOffset = 0x705;
constexpr std::size_t kCombatResultIdOffset = 0x708;
constexpr std::size_t kCombatSideArmyIdsOffset = 0x10;
constexpr std::size_t kCombatSideArmyCapacityOffset = 0x18;
constexpr std::size_t kCombatSideArmyCountOffset = 0x1C;
constexpr std::size_t kCombatSidePrimaryCharacterIdOffset = 0x70;
constexpr std::size_t kCombatSideBackPointerOffset = 0xB8;
constexpr std::size_t kProvinceIdOffset = 0x10;
constexpr std::size_t kInternalArmyIdOffset = 0x10;
constexpr std::size_t kInternalArmyUnitIdOffset = 0x124;
constexpr std::size_t kInternalArmyCombatIdOffset = 0x128;
constexpr std::size_t kPublicCunitIdOffset = 0x10;
constexpr std::size_t kPublicCunitInternalArmyIdOffset = 0x178;
constexpr std::size_t kBattleResultIdOffset = 0x08;
constexpr std::size_t kBattleResultWipeOffset = 0x28;
constexpr std::size_t kBattleResultWarscoreOffset = 0x40;
constexpr std::size_t kWarIdOffset = 0x08;
constexpr std::size_t kWarBattleRowsOffset = 0x298;
constexpr std::size_t kWarBattleRowCapacityOffset = 0x2A0;
constexpr std::size_t kWarBattleRowCountOffset = 0x2A4;
constexpr std::size_t kWarBattleRowWarscoreOffset = 0x40;
constexpr std::size_t kWarBattleRowWinnerIsAttackerOffset = 0x50;
constexpr std::size_t kWarBattleRowSide0IsAttackerOffset = 0x51;

template <typename Record>
struct JournalSlotV1 {
  std::atomic<std::uint64_t> published_sequence{0};
  Record record{};
};

template <typename Record>
struct JournalRingV1 {
  std::atomic<std::uint64_t> next_sequence{0};
  std::atomic<std::uint64_t> latest_sequence{0};
  std::atomic<std::uint32_t> capture_in_progress{0};
  std::array<JournalSlotV1<Record>, kBattleTerminalJournalCapacityV1> slots{};
};

JournalRingV1<BattleTerminalJournalEventV1> g_terminal_ring{};
JournalRingV1<BattleWarscoreJournalEventV1> g_warscore_ring{};
Bindings g_bindings{};
std::atomic<bool> g_storage_initialized{false};
std::atomic<std::uint32_t> g_warscore_unattributed_failures{0};
std::atomic<BattleTerminalJournalDetourStateV1 *> g_active_state{nullptr};
std::atomic<BattleTerminalOriginalV1> g_original_terminal{nullptr};
std::atomic<BattleWarscoreWriterOriginalV1> g_original_warscore{nullptr};

template <typename Value>
Value LoadAt(const void *base, std::size_t offset) noexcept {
  Value value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset,
              sizeof(value));
  return value;
}

void *ResolveStoredComponent(void **storage_slot, std::int32_t component_id,
                             std::size_t id_offset) noexcept {
  if (storage_slot == nullptr || component_id <= 0) {
    return nullptr;
  }
  void *const storage = *storage_slot;
  if (storage == nullptr) {
    return nullptr;
  }
  void *const slots =
      LoadAt<void *>(storage, kComponentStorageSlotsOffset);
  const auto capacity =
      LoadAt<std::int32_t>(storage, kComponentStorageCapacityOffset);
  const auto index =
      static_cast<std::uint32_t>(component_id) & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentCapacity ||
      index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  void *const object = LoadAt<void *>(
      slots, static_cast<std::size_t>(index) * kComponentStorageSlotSize +
                 kComponentStorageSlotObjectOffset);
  return object != nullptr &&
                 LoadAt<std::int32_t>(object, id_offset) == component_id
             ? object
             : nullptr;
}

std::int32_t ReadDateRaw() noexcept {
  if (g_bindings.game_state_slot == nullptr) {
    return 0;
  }
  void *const game_state = *g_bindings.game_state_slot;
  return game_state == nullptr
             ? 0
             : LoadAt<std::int32_t>(game_state, kGameStateDateRawOffset);
}

template <typename Record>
void Publish(JournalRingV1<Record> &ring, Record &record) noexcept {
  const auto sequence =
      ring.next_sequence.fetch_add(1, std::memory_order_acq_rel) + 1;
  record.sequence = sequence;
  auto &slot = ring.slots[(sequence - 1) % ring.slots.size()];
  slot.published_sequence.store(0, std::memory_order_relaxed);
  slot.record = record;
  slot.published_sequence.store(sequence, std::memory_order_release);
  ring.latest_sequence.store(sequence, std::memory_order_release);
}

template <typename Record>
bool ReadPublished(const JournalRingV1<Record> &ring, std::uint64_t sequence,
                   Record &output) noexcept {
  if (sequence == 0) {
    return false;
  }
  const auto &slot = ring.slots[(sequence - 1) % ring.slots.size()];
  if (slot.published_sequence.load(std::memory_order_acquire) != sequence) {
    return false;
  }
  output = slot.record;
  return slot.published_sequence.load(std::memory_order_acquire) == sequence &&
         output.sequence == sequence;
}

bool ReadTerminalSide(
    const void *combat, std::size_t side_offset, std::int32_t combat_id,
    std::array<std::int32_t, kBattleTerminalMaximumSideCunitsV1> &output,
    std::uint32_t &output_count, std::uint32_t &failure_flags) noexcept {
  output_count = 0;
  const auto *const side =
      static_cast<const std::byte *>(combat) + side_offset;
  if (LoadAt<const void *>(side, kCombatSideBackPointerOffset) != combat) {
    failure_flags |= battle_terminal_capture_failure_identity;
    return false;
  }
  void *const data = LoadAt<void *>(side, kCombatSideArmyIdsOffset);
  const auto capacity =
      LoadAt<std::int32_t>(side, kCombatSideArmyCapacityOffset);
  const auto count = LoadAt<std::int32_t>(side, kCombatSideArmyCountOffset);
  if (capacity < 0 || count < 0 || count > capacity ||
      capacity > kMaximumComponentCapacity ||
      count > static_cast<std::int32_t>(output.size()) ||
      (count > 0 && data == nullptr)) {
    failure_flags |= count > static_cast<std::int32_t>(output.size())
                         ? battle_terminal_capture_failure_bounds
                         : battle_terminal_capture_failure_identity;
    return false;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    const auto native_carmy_id = LoadAt<std::int32_t>(
        data, static_cast<std::size_t>(index) * sizeof(std::int32_t));
    void *const native_army = ResolveStoredComponent(
        g_bindings.army_internal_storage_slot, native_carmy_id,
        kInternalArmyIdOffset);
    if (native_army == nullptr ||
        LoadAt<std::int32_t>(native_army, kInternalArmyCombatIdOffset) !=
            combat_id) {
      failure_flags |= battle_terminal_capture_failure_identity;
      return false;
    }
    const auto public_cunit_id =
        LoadAt<std::int32_t>(native_army, kInternalArmyUnitIdOffset);
    void *const public_cunit = ResolveStoredComponent(
        g_bindings.army_storage_slot, public_cunit_id,
        kPublicCunitIdOffset);
    if (public_cunit == nullptr ||
        LoadAt<std::int32_t>(public_cunit,
                             kPublicCunitInternalArmyIdOffset) !=
            native_carmy_id ||
        std::find(output.begin(), output.begin() + index, public_cunit_id) !=
            output.begin() + index) {
      failure_flags |= battle_terminal_capture_failure_identity;
      return false;
    }
    output[static_cast<std::size_t>(index)] = public_cunit_id;
  }
  output_count = static_cast<std::uint32_t>(count);
  return LoadAt<void *>(side, kCombatSideArmyIdsOffset) == data &&
         LoadAt<std::int32_t>(side, kCombatSideArmyCapacityOffset) ==
             capacity &&
         LoadAt<std::int32_t>(side, kCombatSideArmyCountOffset) == count &&
         LoadAt<const void *>(side, kCombatSideBackPointerOffset) == combat;
}

bool CaptureTerminalUnsafe(void *combat,
                           bool suppress_normal_result_envelopes,
                           BattleTerminalJournalEventV1 &event) noexcept {
  if (combat == nullptr || !g_storage_initialized.load(
                               std::memory_order_acquire)) {
    event.capture_failure_flags |= battle_terminal_capture_failure_identity;
    return false;
  }
  event.observed_date_raw = ReadDateRaw();
  event.combat_id = LoadAt<std::int32_t>(combat, kCombatIdOffset);
  event.battle_result_id =
      LoadAt<std::int32_t>(combat, kCombatResultIdOffset);
  event.suppress_normal_result_envelopes =
      suppress_normal_result_envelopes;
  event.phase_raw = LoadAt<std::int32_t>(combat, kCombatPhaseOffset);
  event.winner_raw = LoadAt<std::int32_t>(combat, kCombatWinnerOffset);
  const auto finalized_raw =
      LoadAt<std::uint8_t>(combat, kCombatFinalizedOffset);
  event.finalized_before = finalized_raw != 0;
  event.daily_guard_raw =
      LoadAt<std::uint8_t>(combat, kCombatDailyGuardOffset);
  const auto *const attacker =
      static_cast<const std::byte *>(combat) + kCombatAttackerSideOffset;
  const auto *const defender =
      static_cast<const std::byte *>(combat) + kCombatDefenderSideOffset;
  event.attacker_primary_participant_character_id = LoadAt<std::int32_t>(
      attacker, kCombatSidePrimaryCharacterIdOffset);
  event.defender_primary_participant_character_id = LoadAt<std::int32_t>(
      defender, kCombatSidePrimaryCharacterIdOffset);
  void *const province = LoadAt<void *>(combat, kCombatProvinceOffset);
  event.province_id = province == nullptr
                          ? -1
                          : LoadAt<std::int32_t>(province, kProvinceIdOffset);
  if (event.combat_id <= 0 || event.province_id <= 0 ||
      event.winner_raw < -1 || event.winner_raw > 1 || finalized_raw > 1 ||
      event.attacker_primary_participant_character_id <= 0 ||
      event.defender_primary_participant_character_id <= 0) {
    event.capture_failure_flags |= battle_terminal_capture_failure_identity;
  }
  if (event.battle_result_id > 0) {
    void *const result = ResolveStoredComponent(
        g_bindings.battle_result_storage_slot, event.battle_result_id,
        kBattleResultIdOffset);
    if (result == nullptr) {
      event.capture_failure_flags |= battle_terminal_capture_failure_identity;
    } else {
      event.wipe_raw_observable = true;
      event.wipe_raw =
          LoadAt<std::uint8_t>(result, kBattleResultWipeOffset) != 0;
    }
  } else if (event.battle_result_id != -1) {
    event.capture_failure_flags |= battle_terminal_capture_failure_identity;
  }
  (void)ReadTerminalSide(
      combat, kCombatAttackerSideOffset, event.combat_id,
      event.attacker_public_cunit_ids_in_stored_order,
      event.attacker_public_cunit_count, event.capture_failure_flags);
  (void)ReadTerminalSide(
      combat, kCombatDefenderSideOffset, event.combat_id,
      event.defender_public_cunit_ids_in_stored_order,
      event.defender_public_cunit_count, event.capture_failure_flags);
  for (std::uint32_t left = 0;
       left < event.attacker_public_cunit_count; ++left) {
    if (std::find(
            event.defender_public_cunit_ids_in_stored_order.begin(),
            event.defender_public_cunit_ids_in_stored_order.begin() +
                event.defender_public_cunit_count,
            event.attacker_public_cunit_ids_in_stored_order[left]) !=
        event.defender_public_cunit_ids_in_stored_order.begin() +
            event.defender_public_cunit_count) {
      event.capture_failure_flags |= battle_terminal_capture_failure_identity;
    }
  }
  return event.capture_failure_flags == battle_terminal_capture_failure_none;
}

struct WarscorePreObservationV1 {
  std::int32_t combat_id = -1;
  std::int32_t war_id = -1;
  std::int32_t row_count = -1;
};

bool ReadWarscorePreUnsafe(void *war, void *combat,
                           WarscorePreObservationV1 &output) noexcept {
  if (war == nullptr || combat == nullptr) {
    return false;
  }
  output.combat_id = LoadAt<std::int32_t>(combat, kCombatIdOffset);
  output.war_id = LoadAt<std::int32_t>(war, kWarIdOffset);
  output.row_count =
      LoadAt<std::int32_t>(war, kWarBattleRowCountOffset);
  const auto capacity =
      LoadAt<std::int32_t>(war, kWarBattleRowCapacityOffset);
  return output.combat_id > 0 && output.war_id > 0 &&
         output.row_count >= 0 && output.row_count <= capacity &&
         capacity <= kMaximumComponentCapacity;
}

bool CaptureWarscorePostUnsafe(
    void *war, void *combat, const WarscorePreObservationV1 &before,
    BattleWarscoreJournalEventV1 &event, bool &row_appended) noexcept {
  row_appended = false;
  if (war == nullptr || combat == nullptr || before.combat_id <= 0 ||
      before.war_id <= 0) {
    return false;
  }
  const auto combat_id = LoadAt<std::int32_t>(combat, kCombatIdOffset);
  const auto war_id = LoadAt<std::int32_t>(war, kWarIdOffset);
  const auto count =
      LoadAt<std::int32_t>(war, kWarBattleRowCountOffset);
  const auto capacity =
      LoadAt<std::int32_t>(war, kWarBattleRowCapacityOffset);
  if (combat_id != before.combat_id || war_id != before.war_id ||
      count < before.row_count || count > capacity ||
      capacity > kMaximumComponentCapacity) {
    return false;
  }
  if (count == before.row_count) {
    return true;
  }
  event.observed_date_raw = ReadDateRaw();
  event.combat_id = combat_id;
  event.war_id = war_id;
  if (count != before.row_count + 1 || count <= 0) {
    event.capture_failure_flags |= battle_terminal_capture_failure_identity;
    row_appended = true;
    return false;
  }
  void *const rows = LoadAt<void *>(war, kWarBattleRowsOffset);
  void *const row = rows == nullptr
                        ? nullptr
                        : LoadAt<void *>(
                              rows, static_cast<std::size_t>(count - 1) *
                                        sizeof(void *));
  event.war_battle_row_index = count - 1;
  if (row == nullptr) {
    event.capture_failure_flags |= battle_terminal_capture_failure_identity;
    row_appended = true;
    return false;
  }
  event.battle_warscore_value_raw =
      LoadAt<std::int64_t>(row, kWarBattleRowWarscoreOffset);
  event.winner_is_war_attacker =
      LoadAt<std::uint8_t>(row,
                           kWarBattleRowWinnerIsAttackerOffset) != 0;
  event.combat_side0_is_war_attacker =
      LoadAt<std::uint8_t>(row,
                           kWarBattleRowSide0IsAttackerOffset) != 0;
  const auto result_id =
      LoadAt<std::int32_t>(combat, kCombatResultIdOffset);
  void *const result = ResolveStoredComponent(
      g_bindings.battle_result_storage_slot, result_id,
      kBattleResultIdOffset);
  if (event.battle_warscore_value_raw < 0 || result == nullptr ||
      LoadAt<std::int64_t>(result, kBattleResultWarscoreOffset) !=
          event.battle_warscore_value_raw) {
    event.capture_failure_flags |= battle_terminal_capture_failure_identity;
  }
  row_appended = true;
  return event.capture_failure_flags == battle_terminal_capture_failure_none;
}

template <typename Callback>
bool FaultBoundary(Callback callback) noexcept {
#if defined(_MSC_VER)
  __try {
    return callback();
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  return callback();
#endif
}

void WriteAbsoluteJump(std::uint8_t *destination,
                       std::uintptr_t target) noexcept {
  constexpr std::array<std::uint8_t, 6> prefix{
      0xFF, 0x25, 0x00, 0x00, 0x00, 0x00};
  std::memcpy(destination, prefix.data(), prefix.size());
  std::memcpy(destination + prefix.size(), &target, sizeof(target));
}

void *DefaultVirtualAlloc(void *, std::size_t size, DWORD allocation_type,
                          DWORD protection) noexcept {
  return VirtualAlloc(nullptr, size, allocation_type, protection);
}

bool DefaultVirtualFree(void *, void *address, std::size_t size,
                        DWORD free_type) noexcept {
  return VirtualFree(address, size, free_type) != FALSE;
}

bool DefaultVirtualProtect(void *, void *address, std::size_t size,
                           DWORD protection, DWORD &old) noexcept {
  return VirtualProtect(address, size, protection, &old) != FALSE;
}

bool DefaultFlush(void *, const void *address, std::size_t size) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}

template <std::size_t Size>
bool FillTrampoline(void *storage,
                    const std::array<std::uint8_t, Size> &original,
                    std::uintptr_t resume) noexcept {
  if (storage == nullptr || resume == 0) {
    return false;
  }
  auto *const bytes = static_cast<std::uint8_t *>(storage);
  std::memcpy(bytes, original.data(), original.size());
  WriteAbsoluteJump(bytes + original.size(), resume);
  return true;
}

void AddInstallFailure(BattleTerminalJournalDetourStateV1 &state,
                       BattleTerminalJournalInstallFailureV1 failure) {
  state.failure_flags.fetch_or(static_cast<std::uint32_t>(failure),
                               std::memory_order_acq_rel);
}

bool Flush(BattleTerminalJournalDetourStateV1 &state, const void *address,
           std::size_t size) noexcept {
  if (state.flush_instruction_cache == nullptr ||
      !state.flush_instruction_cache(state.memory_context, address, size)) {
    AddInstallFailure(state, battle_terminal_install_failure_flush);
    return false;
  }
  return true;
}

template <std::size_t Size>
bool MakeExecutable(BattleTerminalJournalDetourStateV1 &state,
                    void *storage) noexcept {
  DWORD old = 0;
  if (state.virtual_protect == nullptr ||
      !state.virtual_protect(state.memory_context, storage,
                             Size + kBattleTerminalAbsoluteJumpBytesV1,
                             PAGE_EXECUTE_READ, old) ||
      old != PAGE_READWRITE ||
      !Flush(state, storage,
             Size + kBattleTerminalAbsoluteJumpBytesV1)) {
    AddInstallFailure(state, battle_terminal_install_failure_protection);
    return false;
  }
  return true;
}

template <std::size_t Size>
bool WritePatch(BattleTerminalJournalDetourStateV1 &state,
                std::uintptr_t target,
                const std::array<std::uint8_t, Size> &expected,
                const std::array<std::uint8_t, Size> &desired) noexcept {
  if (target == 0 ||
      std::memcmp(reinterpret_cast<const void *>(target), expected.data(),
                  Size) != 0) {
    AddInstallFailure(state, battle_terminal_install_failure_anchor);
    return false;
  }
  DWORD old = 0;
  if (state.virtual_protect == nullptr ||
      !state.virtual_protect(state.memory_context,
                             reinterpret_cast<void *>(target), Size,
                             PAGE_EXECUTE_READWRITE, old)) {
    AddInstallFailure(state, battle_terminal_install_failure_protection);
    return false;
  }
  std::memcpy(reinterpret_cast<void *>(target), desired.data(), Size);
  const bool identity =
      std::memcmp(reinterpret_cast<const void *>(target), desired.data(),
                  Size) == 0;
  const bool flushed = Flush(state, reinterpret_cast<void *>(target), Size);
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(target), Size, old,
      ignored);
  if (identity && flushed && restored) {
    return true;
  }
  if (!identity || !restored) {
    AddInstallFailure(state, battle_terminal_install_failure_protection);
  }
  DWORD rollback_old = 0;
  const bool rollback_writable = state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(target), Size,
      PAGE_EXECUTE_READWRITE, rollback_old);
  if (rollback_writable) {
    std::memcpy(reinterpret_cast<void *>(target), expected.data(), Size);
  }
  const bool rollback_identity =
      rollback_writable &&
      std::memcmp(reinterpret_cast<const void *>(target), expected.data(),
                  Size) == 0;
  const bool rollback_flushed =
      rollback_identity &&
      Flush(state, reinterpret_cast<void *>(target), Size);
  DWORD rollback_ignored = 0;
  const bool rollback_restored =
      rollback_writable && state.virtual_protect(
                               state.memory_context,
                               reinterpret_cast<void *>(target), Size, old,
                               rollback_ignored);
  if (!rollback_identity || !rollback_flushed || !rollback_restored) {
    AddInstallFailure(state, battle_terminal_install_failure_rollback);
  }
  return false;
}

void FreeTrampolines(BattleTerminalJournalDetourStateV1 &state) noexcept {
  if (state.virtual_free != nullptr) {
    if (state.terminal_trampoline != nullptr) {
      (void)state.virtual_free(state.memory_context,
                               state.terminal_trampoline, 0, MEM_RELEASE);
    }
    if (state.warscore_trampoline != nullptr) {
      (void)state.virtual_free(state.memory_context,
                               state.warscore_trampoline, 0, MEM_RELEASE);
    }
  }
  state.terminal_trampoline = nullptr;
  state.warscore_trampoline = nullptr;
}

template <typename Record>
void ResetRing(JournalRingV1<Record> &ring) noexcept {
  ring.next_sequence.store(0, std::memory_order_relaxed);
  ring.latest_sequence.store(0, std::memory_order_relaxed);
  ring.capture_in_progress.store(0, std::memory_order_relaxed);
  for (auto &slot : ring.slots) {
    slot.published_sequence.store(0, std::memory_order_relaxed);
    slot.record = {};
  }
}

} // namespace

bool InitializeBattleTerminalJournalStorageV1(
    const Bindings &bindings) noexcept {
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.army_storage_slot == nullptr ||
      bindings.army_internal_storage_slot == nullptr ||
      bindings.battle_result_storage_slot == nullptr) {
    return false;
  }
  g_storage_initialized.store(false, std::memory_order_release);
  g_bindings = bindings;
  ResetRing(g_terminal_ring);
  ResetRing(g_warscore_ring);
  g_warscore_unattributed_failures.store(0, std::memory_order_relaxed);
  g_storage_initialized.store(true, std::memory_order_release);
  return true;
}

bool CaptureBattleTerminalJournalEntryV1(
    void *combat, bool suppress_normal_result_envelopes) noexcept {
  if (g_terminal_ring.capture_in_progress.exchange(
          1, std::memory_order_acq_rel) != 0) {
    return false;
  }
  BattleTerminalJournalEventV1 event{};
  const bool captured = FaultBoundary([&]() noexcept {
    return CaptureTerminalUnsafe(combat,
                                 suppress_normal_result_envelopes, event);
  });
  if (!captured && event.capture_failure_flags ==
                       battle_terminal_capture_failure_none) {
    event.capture_failure_flags |= battle_terminal_capture_failure_memory;
  }
  Publish(g_terminal_ring, event);
  g_terminal_ring.capture_in_progress.store(0, std::memory_order_release);
  return captured;
}

BattleTerminalJournalLookupV1 LookupBattleTerminalJournalV1(
    std::int32_t prior_combat_id,
    std::uint64_t after_terminal_sequence) noexcept {
  BattleTerminalJournalLookupV1 output{};
  output.requested_after_sequence = after_terminal_sequence;
  if (prior_combat_id <= 0 ||
      !g_storage_initialized.load(std::memory_order_acquire)) {
    return output;
  }
  output.latest_sequence =
      g_terminal_ring.latest_sequence.load(std::memory_order_acquire);
  output.oldest_available_sequence =
      output.latest_sequence == 0
          ? 0
          : output.latest_sequence <= kBattleTerminalJournalCapacityV1
                ? 1
                : output.latest_sequence -
                      kBattleTerminalJournalCapacityV1 + 1;
  if (after_terminal_sequence > output.latest_sequence) {
    output.status = BattleTerminalJournalLookupStatusV1::invalid_cursor;
    return output;
  }
  if (output.oldest_available_sequence > 1 &&
      after_terminal_sequence < output.oldest_available_sequence - 1) {
    output.status = BattleTerminalJournalLookupStatusV1::journal_gap;
    return output;
  }
  const auto begin = std::max<std::uint64_t>(
      after_terminal_sequence + 1, output.oldest_available_sequence);
  bool found = false;
  for (std::uint64_t sequence = begin;
       sequence != 0 && sequence <= output.latest_sequence; ++sequence) {
    BattleTerminalJournalEventV1 candidate{};
    if (!ReadPublished(g_terminal_ring, sequence, candidate)) {
      output.status = BattleTerminalJournalLookupStatusV1::journal_gap;
      return output;
    }
    if (candidate.combat_id == prior_combat_id) {
      output.event = candidate;
      found = true;
    }
  }
  output.status = found ? BattleTerminalJournalLookupStatusV1::observed
                        : BattleTerminalJournalLookupStatusV1::not_observed;
  return output;
}

BattleWarscoreJournalLookupV1 LookupBattleWarscoreJournalV1(
    std::int32_t combat_id) noexcept {
  BattleWarscoreJournalLookupV1 output{};
  if (combat_id <= 0 ||
      !g_storage_initialized.load(std::memory_order_acquire)) {
    return output;
  }
  output.latest_sequence =
      g_warscore_ring.latest_sequence.load(std::memory_order_acquire);
  output.oldest_available_sequence =
      output.latest_sequence == 0
          ? 0
          : output.latest_sequence <= kBattleTerminalJournalCapacityV1
                ? 1
                : output.latest_sequence -
                      kBattleTerminalJournalCapacityV1 + 1;
  bool found = false;
  for (std::uint64_t sequence = output.oldest_available_sequence;
       sequence != 0 && sequence <= output.latest_sequence; ++sequence) {
    BattleWarscoreJournalEventV1 candidate{};
    if (!ReadPublished(g_warscore_ring, sequence, candidate)) {
      output.status = BattleWarscoreJournalLookupStatusV1::journal_gap;
      return output;
    }
    if (candidate.combat_id == combat_id) {
      output.event = candidate;
      found = true;
    }
  }
  if (found) {
    output.status = BattleWarscoreJournalLookupStatusV1::observed;
  } else if (g_warscore_unattributed_failures.load(
                 std::memory_order_acquire) != 0 ||
             output.latest_sequence > kBattleTerminalJournalCapacityV1) {
    output.status = BattleWarscoreJournalLookupStatusV1::journal_gap;
  } else {
    output.status = BattleWarscoreJournalLookupStatusV1::not_observed;
  }
  return output;
}

bool InstallBattleTerminalJournalV1(
    BattleTerminalJournalDetourStateV1 &state,
    const BattleTerminalJournalInstallEnvironmentV1 &environment) noexcept {
  state.failure_flags.store(battle_terminal_install_failure_none,
                            std::memory_order_relaxed);
  if (!environment.exact_build_admitted || environment.module_base == 0) {
    AddInstallFailure(state, battle_terminal_install_failure_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    AddInstallFailure(state, battle_terminal_install_failure_quiescence);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0) {
    return true;
  }
  BattleTerminalJournalDetourStateV1 *expected = nullptr;
  if (!g_active_state.compare_exchange_strong(
          expected, &state, std::memory_order_acq_rel,
          std::memory_order_acquire)) {
    AddInstallFailure(state,
                      battle_terminal_install_failure_already_installed);
    return false;
  }
  if (!InitializeBattleTerminalJournalStorageV1(environment.bindings)) {
    AddInstallFailure(state, battle_terminal_install_failure_exact_build);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  state.terminal_target =
      environment.terminal_target_override != 0
          ? environment.terminal_target_override
          : environment.module_base + kBattleTerminalFinalizerRvaV1;
  state.warscore_target =
      environment.warscore_target_override != 0
          ? environment.warscore_target_override
          : environment.module_base + kBattleWarscoreWriterRvaV1;
  if (std::memcmp(reinterpret_cast<const void *>(state.terminal_target),
                  kTerminalPrologue.data(), kTerminalPrologue.size()) != 0 ||
      std::memcmp(reinterpret_cast<const void *>(state.warscore_target),
                  kWarscorePrologue.data(), kWarscorePrologue.size()) != 0) {
    AddInstallFailure(state, battle_terminal_install_failure_anchor);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  state.memory_context = environment.memory_context;
  state.virtual_free = environment.virtual_free_override != nullptr
                           ? environment.virtual_free_override
                           : &DefaultVirtualFree;
  state.virtual_protect = environment.virtual_protect_override != nullptr
                              ? environment.virtual_protect_override
                              : &DefaultVirtualProtect;
  state.flush_instruction_cache =
      environment.flush_instruction_cache_override != nullptr
          ? environment.flush_instruction_cache_override
          : &DefaultFlush;
  const auto allocate = environment.virtual_alloc_override != nullptr
                            ? environment.virtual_alloc_override
                            : &DefaultVirtualAlloc;
  state.terminal_trampoline = allocate(
      state.memory_context,
      kBattleTerminalFinalizerPatchBytesV1 +
          kBattleTerminalAbsoluteJumpBytesV1,
      MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  state.warscore_trampoline = allocate(
      state.memory_context,
      kBattleWarscoreWriterPatchBytesV1 +
          kBattleTerminalAbsoluteJumpBytesV1,
      MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.terminal_trampoline == nullptr ||
      state.warscore_trampoline == nullptr ||
      !FillTrampoline(state.terminal_trampoline, kTerminalPrologue,
                      state.terminal_target +
                          kBattleTerminalFinalizerPatchBytesV1) ||
      !FillTrampoline(state.warscore_trampoline, kWarscorePrologue,
                      state.warscore_target +
                          kBattleWarscoreWriterPatchBytesV1) ||
      !MakeExecutable<kBattleTerminalFinalizerPatchBytesV1>(
          state, state.terminal_trampoline) ||
      !MakeExecutable<kBattleWarscoreWriterPatchBytesV1>(
          state, state.warscore_trampoline)) {
    AddInstallFailure(state, battle_terminal_install_failure_allocation);
    FreeTrampolines(state);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  g_original_terminal.store(
      reinterpret_cast<BattleTerminalOriginalV1>(
          state.terminal_trampoline),
      std::memory_order_release);
  g_original_warscore.store(
      reinterpret_cast<BattleWarscoreWriterOriginalV1>(
          state.warscore_trampoline),
      std::memory_order_release);

  std::array<std::uint8_t, kBattleTerminalFinalizerPatchBytesV1>
      terminal_patch{};
  std::array<std::uint8_t, kBattleWarscoreWriterPatchBytesV1>
      warscore_patch{};
  terminal_patch.fill(0x90);
  warscore_patch.fill(0x90);
  WriteAbsoluteJump(terminal_patch.data(),
                    reinterpret_cast<std::uintptr_t>(
                        &XarBattleTerminalHookV1));
  WriteAbsoluteJump(warscore_patch.data(),
                    reinterpret_cast<std::uintptr_t>(
                        &XarBattleWarscoreWriterHookV1));
  const bool terminal_installed = WritePatch(
      state, state.terminal_target, kTerminalPrologue, terminal_patch);
  const bool warscore_installed = terminal_installed && WritePatch(
      state, state.warscore_target, kWarscorePrologue, warscore_patch);
  if (!terminal_installed || !warscore_installed) {
    if (terminal_installed &&
        !WritePatch(state, state.terminal_target, terminal_patch,
                    kTerminalPrologue)) {
      AddInstallFailure(state, battle_terminal_install_failure_rollback);
    }
    g_original_terminal.store(nullptr, std::memory_order_release);
    g_original_warscore.store(nullptr, std::memory_order_release);
    FreeTrampolines(state);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  std::memcpy(state.terminal_original.data(), kTerminalPrologue.data(),
              kTerminalPrologue.size());
  std::memcpy(state.warscore_original.data(), kWarscorePrologue.data(),
              kWarscorePrologue.size());
  state.installed.store(1, std::memory_order_release);
  return true;
}

bool BattleTerminalJournalInstalledV1() noexcept {
  const auto *const state =
      g_active_state.load(std::memory_order_acquire);
  return state != nullptr &&
         state->installed.load(std::memory_order_acquire) != 0;
}

extern "C" void __fastcall XarBattleTerminalHookV1(
    void *combat, bool suppress_normal_result_envelopes) noexcept {
  (void)CaptureBattleTerminalJournalEntryV1(
      combat, suppress_normal_result_envelopes);
  const auto original =
      g_original_terminal.load(std::memory_order_acquire);
  if (original != nullptr) {
    original(combat, suppress_normal_result_envelopes);
  }
}

extern "C" void __fastcall XarBattleWarscoreWriterHookV1(
    void *war, void *combat) noexcept {
  WarscorePreObservationV1 before{};
  const bool before_ready = FaultBoundary(
      [&]() noexcept { return ReadWarscorePreUnsafe(war, combat, before); });
  const auto original =
      g_original_warscore.load(std::memory_order_acquire);
  if (original == nullptr) {
    g_warscore_unattributed_failures.fetch_add(
        1, std::memory_order_acq_rel);
    return;
  }
  original(war, combat);
  if (!before_ready) {
    g_warscore_unattributed_failures.fetch_add(
        1, std::memory_order_acq_rel);
    return;
  }
  if (g_warscore_ring.capture_in_progress.exchange(
          1, std::memory_order_acq_rel) != 0) {
    g_warscore_unattributed_failures.fetch_add(
        1, std::memory_order_acq_rel);
    return;
  }
  BattleWarscoreJournalEventV1 event{};
  bool row_appended = false;
  const bool captured = FaultBoundary([&]() noexcept {
    return CaptureWarscorePostUnsafe(war, combat, before, event,
                                     row_appended);
  });
  if (row_appended) {
    if (!captured && event.capture_failure_flags ==
                         battle_terminal_capture_failure_none) {
      event.capture_failure_flags |= battle_terminal_capture_failure_memory;
    }
    Publish(g_warscore_ring, event);
  } else if (!captured) {
    g_warscore_unattributed_failures.fetch_add(
        1, std::memory_order_acq_rel);
  }
  g_warscore_ring.capture_in_progress.store(0, std::memory_order_release);
}

} // namespace xar::ck3_11906
