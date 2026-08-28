#include "xar_bridge/tactical_daily_sentinel_v1.hpp"

#include <algorithm>
#include <array>
#include <charconv>
#include <cstring>
#include <limits>

namespace xar::ck3_11906 {
namespace {

constexpr std::array<std::uint8_t, kDailyTickFinalStagePatchBytesV1>
    kDailyTickFinalStagePrologue{0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74,
                                 0x24, 0x10, 0x57, 0x48, 0x83, 0xEC, 0x20};

constexpr std::size_t kGameStateDateRawOffset = 0x08;
constexpr std::size_t kJominiPausedOffset = 0x20;
constexpr std::size_t kPlayerIdOffset = 0x70;
constexpr std::size_t kComponentStorageSlotsOffset = 0x20;
constexpr std::size_t kComponentStorageCapacityOffset = 0x2C;
constexpr std::size_t kComponentStorageSlotSize = 0x10;
constexpr std::size_t kComponentStorageSlotObjectOffset = 0x08;
constexpr std::int32_t kMaximumComponentCapacity = 1'000'000;

constexpr std::size_t kProvinceIdOffset = 0x10;
constexpr std::size_t kPublicCunitIdOffset = 0x10;
constexpr std::size_t kPublicCunitKindOffset = 0x18;
constexpr std::size_t kPublicCunitMoveTargetOffset = 0x30;
constexpr std::size_t kPublicCunitRetreatStateOffset = 0x170;
constexpr std::size_t kPublicCunitInternalArmyIdOffset = 0x178;
constexpr std::size_t kInternalArmyIdOffset = 0x10;
constexpr std::size_t kInternalArmyPublicCunitIdOffset = 0x124;
constexpr std::size_t kInternalArmyCombatIdOffset = 0x128;

constexpr std::size_t kCombatIdOffset = 0x08;
constexpr std::size_t kCombatAttackerSideOffset = 0x20;
constexpr std::size_t kCombatDefenderSideOffset = 0x368;
constexpr std::size_t kCombatPhaseOffset = 0x6B0;
constexpr std::size_t kCombatPhaseDayOffset = 0x6B4;
constexpr std::size_t kCombatWinnerOffset = 0x6E0;
constexpr std::size_t kCombatFinalizedOffset = 0x704;
constexpr std::size_t kCombatDailyDispatchInProgressOffset = 0x705;
constexpr std::size_t kCombatSideArmyIdsOffset = 0x10;
constexpr std::size_t kCombatSideArmyCapacityOffset = 0x18;
constexpr std::size_t kCombatSideArmyCountOffset = 0x1C;
constexpr std::size_t kCombatSideBackPointerOffset = 0xB8;
constexpr std::int32_t kMaximumCombatSideArmies = 128;
constexpr std::int32_t kDateRawPerDay = 24;

struct ArmyFingerprintV1 {
  std::int32_t public_cunit_id = -1;
  std::int32_t internal_army_id = -1;
  std::int32_t move_target_province_id = -1;
  std::int32_t combat_id = -1;
  bool retreating = false;
};

struct CombatFingerprintV1 {
  std::int32_t combat_id = -1;
  std::int32_t phase = -1;
  std::int32_t phase_day = -1;
  std::int32_t winner = -1;
  bool finalized = false;
  std::uint32_t attacker_count = 0;
  std::uint32_t defender_count = 0;
  std::uint64_t ordered_roster_hash = 0;
};

struct ArmedPayloadV1 {
  void *game_state = nullptr;
  void *jomini_state = nullptr;
  std::int32_t player_id = -1;
  TacticalDailySentinelArmRequestV1 request{};
  std::array<ArmyFingerprintV1, kTacticalDailySentinelMaximumArmiesV1> armies{};
  std::uint32_t combat_count = 0;
  std::array<CombatFingerprintV1, kTacticalDailySentinelMaximumCombatsV1>
      combats{};
};

struct RuntimeStatusV1 {
  std::atomic<TacticalDailySentinelStateV1> state{
      TacticalDailySentinelStateV1::unavailable};
  std::atomic<std::uint64_t> generation{0};
  std::atomic<std::int32_t> starting_date_raw{0};
  std::atomic<std::int32_t> target_date_raw{0};
  std::atomic<std::int32_t> last_observed_date_raw{0};
  std::atomic<std::int32_t> trigger_date_raw{0};
  std::atomic<std::int32_t> speed{0};
  std::atomic<TacticalDailySentinelModeV1> mode{
      TacticalDailySentinelModeV1::decision_epoch};
  std::atomic<std::uint32_t> army_count{0};
  std::atomic<std::uint32_t> combat_count{0};
  std::atomic<std::uint32_t> completed_daily_ticks{0};
  std::atomic<std::uint32_t> intermediate_pause_count{0};
  std::atomic<std::uint32_t> trigger_flags{tactical_daily_trigger_none};
  std::atomic<bool> pause_wrapper_called{false};
  std::atomic<bool> pause_observed{false};
};

Bindings g_bindings{};
ArmedPayloadV1 g_payload{};
RuntimeStatusV1 g_status{};
std::atomic<bool> g_runtime_available{false};
std::atomic<TacticalSetPausedV1> g_set_paused{nullptr};
std::atomic<TacticalDailyOriginalV1> g_original{nullptr};
std::atomic<TacticalDailySentinelDetourStateV1 *> g_active_state{nullptr};

template <typename Value>
Value LoadAt(const void *base, std::size_t offset) noexcept {
  Value value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset,
              sizeof(value));
  return value;
}

template <typename Callback> bool FaultBoundary(Callback &&callback) noexcept {
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

void *ResolveStoredComponent(void **storage_slot, std::int32_t component_id,
                             std::size_t id_offset) noexcept {
  if (storage_slot == nullptr || component_id <= 0) {
    return nullptr;
  }
  void *const storage = *storage_slot;
  if (storage == nullptr) {
    return nullptr;
  }
  void *const slots = LoadAt<void *>(storage, kComponentStorageSlotsOffset);
  const auto capacity =
      LoadAt<std::int32_t>(storage, kComponentStorageCapacityOffset);
  const auto index = static_cast<std::uint32_t>(component_id) & 0x00FFFFFFU;
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

bool ReadArmyFingerprint(const Bindings &bindings, std::int32_t army_id,
                         ArmyFingerprintV1 &output) noexcept {
  output = {};
  output.public_cunit_id = army_id;
  void *const unit = ResolveStoredComponent(bindings.army_storage_slot, army_id,
                                            kPublicCunitIdOffset);
  if (unit == nullptr ||
      LoadAt<std::int32_t>(unit, kPublicCunitKindOffset) != 0) {
    return false;
  }
  output.internal_army_id =
      LoadAt<std::int32_t>(unit, kPublicCunitInternalArmyIdOffset);
  void *const internal_army =
      ResolveStoredComponent(bindings.army_internal_storage_slot,
                             output.internal_army_id, kInternalArmyIdOffset);
  if (internal_army == nullptr ||
      LoadAt<std::int32_t>(internal_army, kInternalArmyPublicCunitIdOffset) !=
          army_id) {
    return false;
  }
  void *const move_target = LoadAt<void *>(unit, kPublicCunitMoveTargetOffset);
  if (move_target != nullptr) {
    output.move_target_province_id =
        LoadAt<std::int32_t>(move_target, kProvinceIdOffset);
    if (output.move_target_province_id <= 0) {
      // A regular idle CUnit can retain a non-null direct-target slot whose
      // pointed row has no positive ProvinceID.  The authoritative paused
      // route projection is empty in that state, so fingerprint it as no
      // direct target instead of rejecting the complete watched army set.
      output.move_target_province_id = -1;
    }
  } else {
    output.move_target_province_id = -1;
  }
  output.combat_id =
      LoadAt<std::int32_t>(internal_army, kInternalArmyCombatIdOffset);
  if (output.combat_id == 0 || output.combat_id < -1) {
    return false;
  }
  output.retreating =
      LoadAt<std::int32_t>(unit, kPublicCunitRetreatStateOffset) > 0;
  return true;
}

void HashRosterValue(std::uint64_t &hash, std::uint32_t value) noexcept {
  constexpr std::uint64_t kFnvPrime = 1099511628211ULL;
  for (std::size_t index = 0; index < sizeof(value); ++index) {
    hash ^= static_cast<std::uint8_t>(value >> (index * 8U));
    hash *= kFnvPrime;
  }
}

bool HashCombatSide(const void *combat, std::size_t side_offset,
                    std::uint32_t tag, std::uint64_t &hash,
                    std::uint32_t &output_count) noexcept {
  const auto *const side = static_cast<const std::byte *>(combat) + side_offset;
  if (LoadAt<const void *>(side, kCombatSideBackPointerOffset) != combat) {
    return false;
  }
  void *const data = LoadAt<void *>(side, kCombatSideArmyIdsOffset);
  const auto capacity =
      LoadAt<std::int32_t>(side, kCombatSideArmyCapacityOffset);
  const auto count = LoadAt<std::int32_t>(side, kCombatSideArmyCountOffset);
  if (capacity < 0 || count < 0 || count > capacity ||
      count > kMaximumCombatSideArmies || (count > 0 && data == nullptr)) {
    return false;
  }
  HashRosterValue(hash, tag);
  HashRosterValue(hash, static_cast<std::uint32_t>(count));
  for (std::int32_t index = 0; index < count; ++index) {
    const auto army_id = LoadAt<std::int32_t>(
        data, static_cast<std::size_t>(index) * sizeof(std::int32_t));
    if (army_id <= 0) {
      return false;
    }
    HashRosterValue(hash, static_cast<std::uint32_t>(army_id));
  }
  if (LoadAt<void *>(side, kCombatSideArmyIdsOffset) != data ||
      LoadAt<std::int32_t>(side, kCombatSideArmyCapacityOffset) != capacity ||
      LoadAt<std::int32_t>(side, kCombatSideArmyCountOffset) != count ||
      LoadAt<const void *>(side, kCombatSideBackPointerOffset) != combat) {
    return false;
  }
  output_count = static_cast<std::uint32_t>(count);
  return true;
}

bool ReadCombatFingerprint(const Bindings &bindings, std::int32_t combat_id,
                           CombatFingerprintV1 &output) noexcept {
  output = {};
  output.combat_id = combat_id;
  void *const combat = ResolveStoredComponent(bindings.combat_storage_slot,
                                              combat_id, kCombatIdOffset);
  if (combat == nullptr) {
    return false;
  }
  output.phase = LoadAt<std::int32_t>(combat, kCombatPhaseOffset);
  output.phase_day = LoadAt<std::int32_t>(combat, kCombatPhaseDayOffset);
  output.winner = LoadAt<std::int32_t>(combat, kCombatWinnerOffset);
  const auto finalized = LoadAt<std::uint8_t>(combat, kCombatFinalizedOffset);
  const auto daily_in_progress =
      LoadAt<std::uint8_t>(combat, kCombatDailyDispatchInProgressOffset);
  if (output.phase < 0 || output.phase_day < 0 || output.winner < -1 ||
      output.winner > 1 || finalized > 1 || daily_in_progress != 0) {
    return false;
  }
  output.finalized = finalized != 0;
  output.ordered_roster_hash = 1469598103934665603ULL;
  return HashCombatSide(combat, kCombatAttackerSideOffset, 0,
                        output.ordered_roster_hash, output.attacker_count) &&
         HashCombatSide(combat, kCombatDefenderSideOffset, 1,
                        output.ordered_roster_hash, output.defender_count) &&
         LoadAt<std::int32_t>(combat, kCombatIdOffset) == combat_id;
}

bool ParseCanonicalPositive(std::string_view token,
                            std::int32_t &output) noexcept {
  output = 0;
  if (token.empty() || token.front() < '1' || token.front() > '9') {
    return false;
  }
  const auto parsed =
      std::from_chars(token.data(), token.data() + token.size(), output);
  return parsed.ec == std::errc{} &&
         parsed.ptr == token.data() + token.size() && output > 0;
}

bool ParseCanonicalPositive(std::string_view token,
                            std::uint64_t &output) noexcept {
  output = 0;
  if (token.empty() || token.front() < '1' || token.front() > '9') {
    return false;
  }
  const auto parsed =
      std::from_chars(token.data(), token.data() + token.size(), output);
  return parsed.ec == std::errc{} &&
         parsed.ptr == token.data() + token.size() && output > 0;
}

bool InitializeRuntime(const Bindings &bindings, TacticalSetPausedV1 set_paused,
                       TacticalDailyOriginalV1 original) noexcept {
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.jomini_state_slot == nullptr ||
      bindings.army_storage_slot == nullptr ||
      bindings.army_internal_storage_slot == nullptr ||
      bindings.combat_storage_slot == nullptr ||
      bindings.get_local_player == nullptr || set_paused == nullptr) {
    return false;
  }
  g_runtime_available.store(false, std::memory_order_release);
  g_bindings = bindings;
  g_payload = {};
  g_set_paused.store(set_paused, std::memory_order_release);
  g_original.store(original, std::memory_order_release);
  g_status.generation.store(0, std::memory_order_relaxed);
  g_status.starting_date_raw.store(0, std::memory_order_relaxed);
  g_status.target_date_raw.store(0, std::memory_order_relaxed);
  g_status.last_observed_date_raw.store(0, std::memory_order_relaxed);
  g_status.trigger_date_raw.store(0, std::memory_order_relaxed);
  g_status.speed.store(0, std::memory_order_relaxed);
  g_status.mode.store(TacticalDailySentinelModeV1::decision_epoch,
                      std::memory_order_relaxed);
  g_status.army_count.store(0, std::memory_order_relaxed);
  g_status.combat_count.store(0, std::memory_order_relaxed);
  g_status.completed_daily_ticks.store(0, std::memory_order_relaxed);
  g_status.intermediate_pause_count.store(0, std::memory_order_relaxed);
  g_status.trigger_flags.store(tactical_daily_trigger_none,
                               std::memory_order_relaxed);
  g_status.pause_wrapper_called.store(false, std::memory_order_relaxed);
  g_status.pause_observed.store(false, std::memory_order_relaxed);
  g_status.state.store(TacticalDailySentinelStateV1::idle,
                       std::memory_order_release);
  g_runtime_available.store(true, std::memory_order_release);
  return true;
}

bool PauseAtStableBoundary(const ArmedPayloadV1 &payload,
                           std::uint32_t &trigger_flags) noexcept {
  if (g_bindings.jomini_state_slot == nullptr ||
      *g_bindings.jomini_state_slot != payload.jomini_state ||
      payload.jomini_state == nullptr) {
    trigger_flags |= tactical_daily_trigger_world_identity_changed;
    return false;
  }
  if (LoadAt<std::uint8_t>(payload.jomini_state, kJominiPausedOffset) == 0) {
    const auto set_paused = g_set_paused.load(std::memory_order_acquire);
    if (set_paused == nullptr) {
      trigger_flags |= tactical_daily_trigger_pause_not_observed;
      return false;
    }
    g_status.pause_wrapper_called.store(true, std::memory_order_release);
    const bool called = FaultBoundary([&]() noexcept {
      set_paused(payload.jomini_state, true, payload.player_id);
      return true;
    });
    if (!called) {
      trigger_flags |= tactical_daily_trigger_pause_not_observed;
      return false;
    }
  }
  const bool paused =
      LoadAt<std::uint8_t>(payload.jomini_state, kJominiPausedOffset) != 0;
  g_status.pause_observed.store(paused, std::memory_order_release);
  if (!paused) {
    trigger_flags |= tactical_daily_trigger_pause_not_observed;
  }
  return paused;
}

void PublishTerminalState(std::int32_t date_raw,
                          std::uint32_t trigger_flags) noexcept {
  const bool paused = PauseAtStableBoundary(g_payload, trigger_flags);
  g_status.trigger_date_raw.store(date_raw, std::memory_order_release);
  g_status.trigger_flags.store(trigger_flags, std::memory_order_release);
  constexpr std::uint32_t infrastructure_failures =
      tactical_daily_trigger_date_sequence_failure |
      tactical_daily_trigger_world_identity_changed |
      tactical_daily_trigger_pause_not_observed |
      tactical_daily_trigger_original_unavailable |
      tactical_daily_trigger_evaluation_failure;
  g_status.state.store(!paused || (trigger_flags & infrastructure_failures) != 0
                           ? TacticalDailySentinelStateV1::failed
                           : TacticalDailySentinelStateV1::triggered,
                       std::memory_order_release);
}

void AddInstallFailure(TacticalDailySentinelDetourStateV1 &state,
                       TacticalDailySentinelInstallFailureV1 failure) {
  state.failure_flags.fetch_or(static_cast<std::uint32_t>(failure),
                               std::memory_order_acq_rel);
}

void WriteAbsoluteJump(std::uint8_t *destination,
                       std::uintptr_t target) noexcept {
  constexpr std::array<std::uint8_t, 6> prefix{0xFF, 0x25, 0x00,
                                               0x00, 0x00, 0x00};
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

bool Flush(TacticalDailySentinelDetourStateV1 &state, const void *address,
           std::size_t size) noexcept {
  if (state.flush_instruction_cache == nullptr ||
      !state.flush_instruction_cache(state.memory_context, address, size)) {
    AddInstallFailure(state, tactical_daily_install_failure_flush);
    return false;
  }
  return true;
}

bool WritePatch(
    TacticalDailySentinelDetourStateV1 &state, std::uintptr_t target,
    const std::array<std::uint8_t, kDailyTickFinalStagePatchBytesV1> &expected,
    const std::array<std::uint8_t, kDailyTickFinalStagePatchBytesV1>
        &desired) noexcept {
  if (target == 0 || std::memcmp(reinterpret_cast<const void *>(target),
                                 expected.data(), expected.size()) != 0) {
    AddInstallFailure(state, tactical_daily_install_failure_anchor);
    return false;
  }
  DWORD old = 0;
  if (state.virtual_protect == nullptr ||
      !state.virtual_protect(state.memory_context,
                             reinterpret_cast<void *>(target), expected.size(),
                             PAGE_EXECUTE_READWRITE, old)) {
    AddInstallFailure(state, tactical_daily_install_failure_protection);
    return false;
  }
  std::memcpy(reinterpret_cast<void *>(target), desired.data(), desired.size());
  const bool identity = std::memcmp(reinterpret_cast<const void *>(target),
                                    desired.data(), desired.size()) == 0;
  const bool flushed =
      Flush(state, reinterpret_cast<void *>(target), desired.size());
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(state.memory_context,
                                              reinterpret_cast<void *>(target),
                                              desired.size(), old, ignored);
  if (identity && flushed && restored) {
    return true;
  }
  if (!identity || !restored) {
    AddInstallFailure(state, tactical_daily_install_failure_protection);
  }
  DWORD rollback_old = 0;
  const bool rollback_writable = state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(target), desired.size(),
      PAGE_EXECUTE_READWRITE, rollback_old);
  if (rollback_writable) {
    std::memcpy(reinterpret_cast<void *>(target), expected.data(),
                expected.size());
  }
  const bool rollback_identity =
      rollback_writable && std::memcmp(reinterpret_cast<const void *>(target),
                                       expected.data(), expected.size()) == 0;
  const bool rollback_flushed =
      rollback_identity &&
      Flush(state, reinterpret_cast<void *>(target), expected.size());
  DWORD rollback_ignored = 0;
  const bool rollback_restored =
      rollback_writable &&
      state.virtual_protect(state.memory_context,
                            reinterpret_cast<void *>(target), expected.size(),
                            old, rollback_ignored);
  if (!rollback_identity || !rollback_flushed || !rollback_restored) {
    AddInstallFailure(state, tactical_daily_install_failure_rollback);
  }
  return false;
}

} // namespace

bool ParseTacticalDailySentinelArmStepV1(
    std::string_view step,
    TacticalDailySentinelArmRequestV1 &request) noexcept {
  request = {};
  if (!step.starts_with(kTacticalDailySentinelArmPrefixV1)) {
    return false;
  }
  auto suffix = step.substr(kTacticalDailySentinelArmPrefixV1.size());
  std::array<std::string_view, kTacticalDailySentinelMaximumArmiesV1 + 9>
      tokens{};
  std::size_t count = 0;
  while (!suffix.empty()) {
    if (count >= tokens.size()) {
      return false;
    }
    const auto delimiter = suffix.find('-');
    tokens[count++] = suffix.substr(0, delimiter);
    if (tokens[count - 1].empty()) {
      return false;
    }
    if (delimiter == std::string_view::npos) {
      suffix = {};
    } else {
      suffix.remove_prefix(delimiter + 1);
      if (suffix.empty()) {
        return false;
      }
    }
  }
  std::size_t army_marker_index = 5;
  request.mode = TacticalDailySentinelModeV1::decision_epoch;
  if (count >= 10 && tokens[5] == "mode") {
    if (tokens[6] == "decision") {
      request.mode = TacticalDailySentinelModeV1::decision_epoch;
    } else if (tokens[6] == "terminal") {
      request.mode = TacticalDailySentinelModeV1::terminal_or_sentinel;
    } else {
      request = {};
      return false;
    }
    army_marker_index = 7;
  }
  const auto army_count_index = army_marker_index + 1;
  const auto first_army_index = army_marker_index + 2;
  std::int32_t army_count = 0;
  if (count < first_army_index + 1 || tokens[1] != "to" ||
      tokens[3] != "speed" || tokens[army_marker_index] != "a" ||
      !ParseCanonicalPositive(tokens[0], request.starting_date_raw) ||
      !ParseCanonicalPositive(tokens[2], request.target_date_raw) ||
      !ParseCanonicalPositive(tokens[4], request.speed) ||
      !ParseCanonicalPositive(tokens[army_count_index], army_count) ||
      request.speed > 5 || army_count <= 0 ||
      army_count >
          static_cast<std::int32_t>(kTacticalDailySentinelMaximumArmiesV1) ||
      count != first_army_index + static_cast<std::size_t>(army_count) ||
      request.target_date_raw <= request.starting_date_raw ||
      (request.target_date_raw - request.starting_date_raw) % kDateRawPerDay !=
          0) {
    request = {};
    return false;
  }
  request.army_count = static_cast<std::uint32_t>(army_count);
  for (std::uint32_t index = 0; index < request.army_count; ++index) {
    if (!ParseCanonicalPositive(tokens[first_army_index + index],
                                request.army_ids[index]) ||
        std::find(request.army_ids.begin(), request.army_ids.begin() + index,
                  request.army_ids[index]) !=
            request.army_ids.begin() + index) {
      request = {};
      return false;
    }
  }
  return true;
}

bool ParseTacticalDailySentinelCancelStepV1(
    std::string_view step, std::uint64_t &generation) noexcept {
  generation = 0;
  return step.starts_with(kTacticalDailySentinelCancelPrefixV1) &&
         ParseCanonicalPositive(
             step.substr(kTacticalDailySentinelCancelPrefixV1.size()),
             generation);
}

TacticalDailySentinelArmStatusV1 ArmTacticalDailySentinelV1(
    const TacticalDailySentinelArmRequestV1 &request) noexcept {
  if (!g_runtime_available.load(std::memory_order_acquire)) {
    return TacticalDailySentinelArmStatusV1::unavailable;
  }
  if (request.speed < 1 || request.speed > 5 || request.army_count == 0 ||
      request.army_count > kTacticalDailySentinelMaximumArmiesV1 ||
      request.starting_date_raw <= 0 ||
      request.target_date_raw <= request.starting_date_raw ||
      (request.mode != TacticalDailySentinelModeV1::decision_epoch &&
       request.mode != TacticalDailySentinelModeV1::terminal_or_sentinel) ||
      (request.target_date_raw - request.starting_date_raw) % kDateRawPerDay !=
          0) {
    return TacticalDailySentinelArmStatusV1::invalid_request;
  }
  ArmedPayloadV1 payload{};
  payload.request = request;
  auto graph_failure = TacticalDailySentinelArmStatusV1::army_unavailable;
  bool graph_ready = FaultBoundary([&]() noexcept {
    if (g_bindings.game_state_slot == nullptr ||
        g_bindings.jomini_state_slot == nullptr) {
      return false;
    }
    payload.game_state = *g_bindings.game_state_slot;
    payload.jomini_state = *g_bindings.jomini_state_slot;
    if (payload.game_state == nullptr || payload.jomini_state == nullptr ||
        LoadAt<std::uint8_t>(payload.jomini_state, kJominiPausedOffset) == 0) {
      return false;
    }
    void *const player = g_bindings.get_local_player(payload.jomini_state);
    if (player == nullptr) {
      return false;
    }
    payload.player_id = LoadAt<std::int32_t>(player, kPlayerIdOffset);
    if (payload.player_id < 0) {
      return false;
    }
    for (std::uint32_t index = 0; index < request.army_count; ++index) {
      if (request.army_ids[index] <= 0 ||
          std::find(request.army_ids.begin(), request.army_ids.begin() + index,
                    request.army_ids[index]) !=
              request.army_ids.begin() + index ||
          !ReadArmyFingerprint(g_bindings, request.army_ids[index],
                               payload.armies[index])) {
        return false;
      }
      const auto combat_id = payload.armies[index].combat_id;
      if (combat_id <= 0) {
        continue;
      }
      const auto existing =
          std::find_if(payload.combats.begin(),
                       payload.combats.begin() + payload.combat_count,
                       [&](const CombatFingerprintV1 &candidate) noexcept {
                         return candidate.combat_id == combat_id;
                       });
      if (existing != payload.combats.begin() + payload.combat_count) {
        continue;
      }
      if (payload.combat_count >= payload.combats.size() ||
          !ReadCombatFingerprint(g_bindings, combat_id,
                                 payload.combats[payload.combat_count])) {
        graph_failure =
            TacticalDailySentinelArmStatusV1::combat_unavailable;
        return false;
      }
      ++payload.combat_count;
    }
    return true;
  });
  if (!graph_ready) {
    const bool paused =
        payload.jomini_state != nullptr && FaultBoundary([&]() noexcept {
          return LoadAt<std::uint8_t>(payload.jomini_state,
                                      kJominiPausedOffset) != 0;
        });
    return paused ? graph_failure
                  : TacticalDailySentinelArmStatusV1::requires_paused;
  }
  const auto observed_date =
      LoadAt<std::int32_t>(payload.game_state, kGameStateDateRawOffset);
  if (observed_date != request.starting_date_raw) {
    return TacticalDailySentinelArmStatusV1::starting_date_mismatch;
  }

  auto current_state = g_status.state.load(std::memory_order_acquire);
  if (current_state == TacticalDailySentinelStateV1::armed &&
      !g_status.state.compare_exchange_strong(
          current_state, TacticalDailySentinelStateV1::idle,
          std::memory_order_acq_rel, std::memory_order_acquire)) {
    return TacticalDailySentinelArmStatusV1::already_armed;
  }
  g_payload = payload;
  const auto generation =
      g_status.generation.fetch_add(1, std::memory_order_acq_rel) + 1;
  g_status.starting_date_raw.store(request.starting_date_raw,
                                   std::memory_order_relaxed);
  g_status.target_date_raw.store(request.target_date_raw,
                                 std::memory_order_relaxed);
  g_status.last_observed_date_raw.store(request.starting_date_raw,
                                        std::memory_order_relaxed);
  g_status.trigger_date_raw.store(0, std::memory_order_relaxed);
  g_status.speed.store(request.speed, std::memory_order_relaxed);
  g_status.mode.store(request.mode, std::memory_order_relaxed);
  g_status.army_count.store(request.army_count, std::memory_order_relaxed);
  g_status.combat_count.store(payload.combat_count, std::memory_order_relaxed);
  g_status.completed_daily_ticks.store(0, std::memory_order_relaxed);
  g_status.intermediate_pause_count.store(0, std::memory_order_relaxed);
  g_status.trigger_flags.store(tactical_daily_trigger_none,
                               std::memory_order_relaxed);
  g_status.pause_wrapper_called.store(false, std::memory_order_relaxed);
  g_status.pause_observed.store(false, std::memory_order_relaxed);
  g_status.generation.store(generation, std::memory_order_relaxed);
  g_status.state.store(TacticalDailySentinelStateV1::armed,
                       std::memory_order_release);
  return TacticalDailySentinelArmStatusV1::armed;
}

TacticalDailySentinelCancelStatusV1 CancelTacticalDailySentinelV1(
    std::uint64_t expected_generation) noexcept {
  using Result = TacticalDailySentinelCancelStatusV1;
  if (!g_runtime_available.load(std::memory_order_acquire)) {
    return Result::unavailable;
  }
  if (expected_generation == 0) {
    return Result::invalid_request;
  }
  if (g_status.generation.load(std::memory_order_acquire) !=
      expected_generation) {
    return Result::generation_mismatch;
  }
  if (g_status.state.load(std::memory_order_acquire) !=
      TacticalDailySentinelStateV1::armed) {
    return Result::not_armed;
  }
  const bool paused = g_payload.jomini_state != nullptr &&
                      FaultBoundary([&]() noexcept {
                        return LoadAt<std::uint8_t>(
                                   g_payload.jomini_state,
                                   kJominiPausedOffset) != 0;
                      });
  if (!paused) {
    return Result::requires_paused;
  }
  auto expected_state = TacticalDailySentinelStateV1::armed;
  if (!g_status.state.compare_exchange_strong(
          expected_state, TacticalDailySentinelStateV1::idle,
          std::memory_order_acq_rel, std::memory_order_acquire)) {
    return Result::not_armed;
  }
  return Result::canceled;
}

TacticalDailySentinelStatusV1 ReadTacticalDailySentinelStatusV1() noexcept {
  TacticalDailySentinelStatusV1 output{};
  output.state = g_status.state.load(std::memory_order_acquire);
  output.generation = g_status.generation.load(std::memory_order_acquire);
  output.starting_date_raw =
      g_status.starting_date_raw.load(std::memory_order_acquire);
  output.target_date_raw =
      g_status.target_date_raw.load(std::memory_order_acquire);
  output.last_observed_date_raw =
      g_status.last_observed_date_raw.load(std::memory_order_acquire);
  output.trigger_date_raw =
      g_status.trigger_date_raw.load(std::memory_order_acquire);
  output.speed = g_status.speed.load(std::memory_order_acquire);
  output.mode = g_status.mode.load(std::memory_order_acquire);
  output.army_count = g_status.army_count.load(std::memory_order_acquire);
  output.combat_count = g_status.combat_count.load(std::memory_order_acquire);
  output.completed_daily_ticks =
      g_status.completed_daily_ticks.load(std::memory_order_acquire);
  output.intermediate_pause_count =
      g_status.intermediate_pause_count.load(std::memory_order_acquire);
  output.trigger_flags = g_status.trigger_flags.load(std::memory_order_acquire);
  if ((output.state == TacticalDailySentinelStateV1::triggered ||
       output.state == TacticalDailySentinelStateV1::failed) &&
      output.trigger_date_raw > 0 && output.target_date_raw > 0) {
    const auto delta = static_cast<std::int64_t>(output.trigger_date_raw) -
                       output.target_date_raw;
    if (delta >= std::numeric_limits<std::int32_t>::min() &&
        delta <= std::numeric_limits<std::int32_t>::max()) {
      output.signed_date_delta_from_target_raw =
          static_cast<std::int32_t>(delta);
      output.overshoot_days =
          delta <= 0 ? 0
                     : static_cast<std::int32_t>((delta + kDateRawPerDay - 1) /
                                                 kDateRawPerDay);
    }
  }
  output.pause_wrapper_called =
      g_status.pause_wrapper_called.load(std::memory_order_acquire);
  output.pause_observed =
      g_status.pause_observed.load(std::memory_order_acquire);
  output.terminal_observed =
      (output.trigger_flags & tactical_daily_trigger_combat_terminal) != 0;
  output.abnormal = output.state == TacticalDailySentinelStateV1::failed;
  return output;
}

void ProcessTacticalDailySentinelAfterTickV1() noexcept {
  if (g_status.state.load(std::memory_order_acquire) !=
      TacticalDailySentinelStateV1::armed) {
    return;
  }
  std::uint32_t trigger_flags = tactical_daily_trigger_none;
  std::int32_t observed_date = 0;
  const bool evaluated = FaultBoundary([&]() noexcept {
    if (g_bindings.game_state_slot == nullptr ||
        g_bindings.jomini_state_slot == nullptr ||
        *g_bindings.game_state_slot != g_payload.game_state ||
        *g_bindings.jomini_state_slot != g_payload.jomini_state) {
      trigger_flags |= tactical_daily_trigger_world_identity_changed;
      return false;
    }
    observed_date =
        LoadAt<std::int32_t>(g_payload.game_state, kGameStateDateRawOffset);
    const auto previous_date =
        g_status.last_observed_date_raw.load(std::memory_order_relaxed);
    if (observed_date != previous_date + kDateRawPerDay) {
      trigger_flags |= tactical_daily_trigger_date_sequence_failure;
    }
    g_status.last_observed_date_raw.store(observed_date,
                                          std::memory_order_relaxed);
    g_status.completed_daily_ticks.fetch_add(1, std::memory_order_acq_rel);

    if (LoadAt<std::uint8_t>(g_payload.jomini_state, kJominiPausedOffset) !=
        0) {
      g_status.intermediate_pause_count.fetch_add(1, std::memory_order_acq_rel);
      trigger_flags |= tactical_daily_trigger_native_pause;
    }

    for (std::uint32_t index = 0; index < g_payload.request.army_count;
         ++index) {
      ArmyFingerprintV1 current{};
      if (!ReadArmyFingerprint(
              g_bindings, g_payload.armies[index].public_cunit_id, current) ||
          current.internal_army_id !=
              g_payload.armies[index].internal_army_id) {
        trigger_flags |= tactical_daily_trigger_army_unavailable;
        continue;
      }
      if (current.move_target_province_id !=
          g_payload.armies[index].move_target_province_id) {
        trigger_flags |= tactical_daily_trigger_route_target_changed;
      }
      if (current.combat_id != g_payload.armies[index].combat_id) {
        trigger_flags |= tactical_daily_trigger_combat_transition;
      }
      if (current.retreating != g_payload.armies[index].retreating) {
        trigger_flags |= tactical_daily_trigger_retreat_transition;
      }
    }

    for (std::uint32_t index = 0; index < g_payload.combat_count; ++index) {
      CombatFingerprintV1 current{};
      if (!ReadCombatFingerprint(g_bindings, g_payload.combats[index].combat_id,
                                 current)) {
        trigger_flags |= tactical_daily_trigger_combat_unavailable |
                         tactical_daily_trigger_combat_terminal;
        continue;
      }
      if (current.attacker_count != g_payload.combats[index].attacker_count ||
          current.defender_count != g_payload.combats[index].defender_count ||
          current.ordered_roster_hash !=
              g_payload.combats[index].ordered_roster_hash) {
        trigger_flags |= tactical_daily_trigger_combat_roster_changed;
      }
      const bool terminal_changed =
          current.finalized != g_payload.combats[index].finalized;
      if (terminal_changed) {
        trigger_flags |= tactical_daily_trigger_combat_terminal;
      }
    }
    if (observed_date >= g_payload.request.target_date_raw) {
      trigger_flags |= tactical_daily_trigger_date_deadline;
    }
    return true;
  });
  if (!evaluated) {
    trigger_flags |= tactical_daily_trigger_evaluation_failure;
  }
  if (trigger_flags != tactical_daily_trigger_none) {
    PublishTerminalState(observed_date, trigger_flags);
  }
}

bool InitializeTacticalDailySentinelFixtureV1(
    const Bindings &bindings, TacticalSetPausedV1 set_paused,
    TacticalDailyOriginalV1 original) noexcept {
  return InitializeRuntime(bindings, set_paused, original);
}

bool InstallTacticalDailySentinelV1(
    TacticalDailySentinelDetourStateV1 &state,
    const TacticalDailySentinelInstallEnvironmentV1 &environment) noexcept {
  state.failure_flags.store(tactical_daily_install_failure_none,
                            std::memory_order_relaxed);
  if (!environment.exact_build_admitted || environment.module_base == 0) {
    AddInstallFailure(state, tactical_daily_install_failure_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    AddInstallFailure(state, tactical_daily_install_failure_quiescence);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0) {
    return true;
  }
  TacticalDailySentinelDetourStateV1 *expected = nullptr;
  if (!g_active_state.compare_exchange_strong(expected, &state,
                                              std::memory_order_acq_rel,
                                              std::memory_order_acquire)) {
    AddInstallFailure(state, tactical_daily_install_failure_already_installed);
    return false;
  }
  state.final_stage_target =
      environment.final_stage_target_override != 0
          ? environment.final_stage_target_override
          : environment.module_base + kDailyTickFinalStageRvaV1;
  if (std::memcmp(reinterpret_cast<const void *>(state.final_stage_target),
                  kDailyTickFinalStagePrologue.data(),
                  kDailyTickFinalStagePrologue.size()) != 0) {
    AddInstallFailure(state, tactical_daily_install_failure_anchor);
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
  state.trampoline = allocate(state.memory_context,
                              kDailyTickFinalStagePatchBytesV1 +
                                  kTacticalDailySentinelAbsoluteJumpBytesV1,
                              MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.trampoline == nullptr) {
    AddInstallFailure(state, tactical_daily_install_failure_allocation);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  auto *const trampoline = static_cast<std::uint8_t *>(state.trampoline);
  std::memcpy(trampoline, kDailyTickFinalStagePrologue.data(),
              kDailyTickFinalStagePrologue.size());
  WriteAbsoluteJump(trampoline + kDailyTickFinalStagePrologue.size(),
                    state.final_stage_target +
                        kDailyTickFinalStagePatchBytesV1);
  DWORD old = 0;
  if (state.virtual_protect == nullptr ||
      !state.virtual_protect(state.memory_context, state.trampoline,
                             kDailyTickFinalStagePatchBytesV1 +
                                 kTacticalDailySentinelAbsoluteJumpBytesV1,
                             PAGE_EXECUTE_READ, old) ||
      old != PAGE_READWRITE ||
      !Flush(state, state.trampoline,
             kDailyTickFinalStagePatchBytesV1 +
                 kTacticalDailySentinelAbsoluteJumpBytesV1)) {
    AddInstallFailure(state, tactical_daily_install_failure_protection);
    (void)state.virtual_free(state.memory_context, state.trampoline, 0,
                             MEM_RELEASE);
    state.trampoline = nullptr;
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  const auto set_paused =
      environment.set_paused_override != nullptr
          ? environment.set_paused_override
          : reinterpret_cast<TacticalSetPausedV1>(environment.module_base +
                                                  kSetPausedWrapperRvaV1);
  if (!InitializeRuntime(
          environment.bindings, set_paused,
          reinterpret_cast<TacticalDailyOriginalV1>(state.trampoline))) {
    AddInstallFailure(state, tactical_daily_install_failure_exact_build);
    (void)state.virtual_free(state.memory_context, state.trampoline, 0,
                             MEM_RELEASE);
    state.trampoline = nullptr;
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  std::array<std::uint8_t, kDailyTickFinalStagePatchBytesV1> patch{};
  patch.fill(0x90);
  WriteAbsoluteJump(patch.data(), reinterpret_cast<std::uintptr_t>(
                                      &XarTacticalDailySentinelHookV1));
  if (!WritePatch(state, state.final_stage_target, kDailyTickFinalStagePrologue,
                  patch)) {
    g_runtime_available.store(false, std::memory_order_release);
    g_original.store(nullptr, std::memory_order_release);
    (void)state.virtual_free(state.memory_context, state.trampoline, 0,
                             MEM_RELEASE);
    state.trampoline = nullptr;
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  std::memcpy(state.original.data(), kDailyTickFinalStagePrologue.data(),
              kDailyTickFinalStagePrologue.size());
  state.installed.store(1, std::memory_order_release);
  return true;
}

bool TacticalDailySentinelInstalledV1() noexcept {
  const auto *const state = g_active_state.load(std::memory_order_acquire);
  return state != nullptr &&
         state->installed.load(std::memory_order_acquire) != 0;
}

extern "C" void __fastcall XarTacticalDailySentinelHookV1() noexcept {
  const auto original = g_original.load(std::memory_order_acquire);
  if (original == nullptr) {
    if (g_status.state.load(std::memory_order_acquire) ==
        TacticalDailySentinelStateV1::armed) {
      std::int32_t date_raw = 0;
      (void)FaultBoundary([&]() noexcept {
        date_raw =
            LoadAt<std::int32_t>(g_payload.game_state, kGameStateDateRawOffset);
        return true;
      });
      PublishTerminalState(date_raw,
                           tactical_daily_trigger_original_unavailable);
    }
    return;
  }
  original();
  ProcessTacticalDailySentinelAfterTickV1();
}

} // namespace xar::ck3_11906
