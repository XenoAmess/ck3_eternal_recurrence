#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string_view>

#include <windows.h>

namespace xar::bridge {

inline constexpr std::string_view kFactionTargetingRowObserverPrivateKeyV1 =
    "g2_faction_targeting_row_observer_v1";
inline constexpr std::string_view kFactionTargetingRowObserverArtifactStemV1 =
    "g2-faction-targeting-row-observer-v1";
inline constexpr std::string_view kFactionTargetingRowObserverCompileGateV1 =
    "XAR_CK3_ENABLE_G2_FACTION_TARGETING_ROW_OBSERVER_V1";
inline constexpr std::string_view
    kFactionTargetingRowObserverExecutableSha256V1 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view
    kFactionTargetingRowObserverNextReverseEngineeringEntryV1 =
        "faction_item_target_character_getter_and_campaign_root_count_equivalence";

inline constexpr std::uintptr_t kFactionTargetingRowObserverPatchRvaV1 =
    0x1395F0E;
inline constexpr std::uintptr_t kFactionTargetingRowObserverContinueRvaV1 =
    0x1395F1D;
inline constexpr std::uintptr_t kFactionTargetingRowGetterRvaV1 = 0xF6F790;
inline constexpr std::uintptr_t kFactionTargetingIdentityResolverRvaV1 =
    0xE6F440;
inline constexpr std::size_t kFactionTargetingRowObserverPatchBytesV1 = 15;
inline constexpr std::size_t kFactionTargetingRowObserverStubCapacityV1 = 192;
inline constexpr std::size_t kFactionTargetingRowStrideV1 = 0x18;
inline constexpr std::size_t kFactionTargetingRowObserverMaximumRowsV1 = 64;
inline constexpr bool kFactionTargetingRowObserverInstalledByDefaultV1 = false;

enum FactionTargetingRowObserverFailureV1 : std::uint32_t {
  faction_targeting_row_observer_failure_none = 0,
  faction_targeting_row_observer_failure_exact_build = 1U << 0,
  faction_targeting_row_observer_failure_primary_thread_suspended = 1U << 1,
  faction_targeting_row_observer_failure_capture_admission = 1U << 2,
  faction_targeting_row_observer_failure_unsupported_override = 1U << 3,
  faction_targeting_row_observer_failure_already_installed = 1U << 4,
  faction_targeting_row_observer_failure_anchor = 1U << 5,
  faction_targeting_row_observer_failure_allocation = 1U << 6,
  faction_targeting_row_observer_failure_stub_protection = 1U << 7,
  faction_targeting_row_observer_failure_target_protection = 1U << 8,
  faction_targeting_row_observer_failure_flush = 1U << 9,
  faction_targeting_row_observer_failure_rollback = 1U << 10,
  faction_targeting_row_observer_failure_identity_resolver = 1U << 11,
};

struct FactionTargetingRowCaptureAdmissionV1 {
  std::uint32_t application_main_thread_id = 0;
  bool paused = false;
  std::uint64_t proof_epoch = 0;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::uint32_t player_character_id = 0;
};

using FactionTargetingRowCaptureAdmissionProbeV1 = bool (*)(
    void *context,
    FactionTargetingRowCaptureAdmissionV1 &admission) noexcept;
using FactionTargetingRowMemoryReadV1 = bool (*)(
    void *context, std::uintptr_t address, void *output,
    std::size_t size) noexcept;
using FactionTargetingRowMemoryWriteV1 = bool (*)(
    void *context, std::uintptr_t address, const void *source,
    std::size_t size) noexcept;
using FactionTargetingRowIdentityResolverOverrideV1 = bool (*)(
    void *context, std::uint32_t faction_id,
    std::uintptr_t &resolved_faction) noexcept;
using FactionTargetingRowVirtualAllocV1 = void *(*)(
    void *context, std::size_t size, DWORD allocation_type,
    DWORD protection) noexcept;
using FactionTargetingRowVirtualFreeV1 = bool (*)(
    void *context, void *address, std::size_t size, DWORD free_type) noexcept;
using FactionTargetingRowVirtualProtectV1 = bool (*)(
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using FactionTargetingRowFlushInstructionCacheV1 = bool (*)(
    void *context, const void *address, std::size_t size) noexcept;

struct FactionTargetingRowObserverEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target_override = 0;
  std::uintptr_t continue_target_override = 0;
  std::uintptr_t original_getter_target_override = 0;
  std::uintptr_t identity_resolver_target_override = 0;
  void *memory_context = nullptr;
  FactionTargetingRowMemoryReadV1 memory_read_override = nullptr;
  FactionTargetingRowMemoryWriteV1 memory_write_override = nullptr;
  FactionTargetingRowVirtualAllocV1 virtual_alloc_override = nullptr;
  FactionTargetingRowVirtualFreeV1 virtual_free_override = nullptr;
  FactionTargetingRowVirtualProtectV1 virtual_protect_override = nullptr;
  FactionTargetingRowFlushInstructionCacheV1
      flush_instruction_cache_override = nullptr;
  void *capture_admission_context = nullptr;
  FactionTargetingRowCaptureAdmissionProbeV1 capture_admission_probe = nullptr;
  void *identity_resolver_context = nullptr;
  FactionTargetingRowIdentityResolverOverrideV1
      identity_resolver_override = nullptr;
};

struct FactionTargetingRowObservationV1 {
  std::atomic<std::uint64_t> callback_count{0};
  std::atomic<std::uint64_t> rejected_application_main_count{0};
  std::atomic<std::uint64_t> rejected_paused_count{0};
  std::atomic<std::uint64_t> rejected_state_change_count{0};
  std::atomic<std::uint64_t> span_read_failure_count{0};
  std::atomic<std::uint64_t> span_stability_failure_count{0};
  std::atomic<std::uint64_t> identity_failure_count{0};
  std::atomic<std::uint64_t> accepted_capture_count{0};
  std::atomic<std::uint64_t> published_generation{0};
  std::atomic<std::uint64_t> last_proof_epoch{0};
  std::atomic<std::uint64_t> last_snapshot_revision{0};
  std::atomic<std::int32_t> last_date_raw{0};
  std::atomic<std::uint32_t> last_player_character_id{0};
  std::atomic<std::uint32_t> last_faction_count{0};
  std::array<std::atomic<std::uint32_t>,
             kFactionTargetingRowObserverMaximumRowsV1>
      last_faction_ids{};
  std::atomic<std::uint32_t> last_thread_id{0};
  std::atomic<std::uint64_t> last_timestamp_qpc{0};
};

struct FactionTargetingRowObserverStateV1 {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{
      faction_targeting_row_observer_failure_none};
  FactionTargetingRowObservationV1 observation{};

  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target = 0;
  std::uintptr_t continue_target = 0;
  std::uintptr_t original_getter_target = 0;
  std::uintptr_t identity_resolver_target = 0;
  void *stub = nullptr;
  std::array<std::uint8_t, kFactionTargetingRowObserverPatchBytesV1>
      original_patch_bytes{};
  std::array<std::uint8_t, kFactionTargetingRowObserverPatchBytesV1>
      installed_patch_bytes{};
  void *memory_context = nullptr;
  FactionTargetingRowMemoryReadV1 memory_read = nullptr;
  FactionTargetingRowMemoryWriteV1 memory_write = nullptr;
  FactionTargetingRowVirtualFreeV1 virtual_free = nullptr;
  FactionTargetingRowVirtualProtectV1 virtual_protect = nullptr;
  FactionTargetingRowFlushInstructionCacheV1 flush_instruction_cache = nullptr;
  void *capture_admission_context = nullptr;
  FactionTargetingRowCaptureAdmissionProbeV1 capture_admission_probe = nullptr;
  void *identity_resolver_context = nullptr;
  FactionTargetingRowIdentityResolverOverrideV1
      identity_resolver_override = nullptr;
};

struct FactionTargetingRowObservationDiagnosticsV1 {
  std::uint64_t callback_count = 0;
  std::uint64_t rejected_application_main_count = 0;
  std::uint64_t rejected_paused_count = 0;
  std::uint64_t rejected_state_change_count = 0;
  std::uint64_t span_read_failure_count = 0;
  std::uint64_t span_stability_failure_count = 0;
  std::uint64_t identity_failure_count = 0;
  std::uint64_t accepted_capture_count = 0;
  std::uint64_t published_generation = 0;
  std::uint64_t last_proof_epoch = 0;
  std::uint64_t last_snapshot_revision = 0;
  std::int32_t last_date_raw = 0;
  std::uint32_t last_player_character_id = 0;
  std::uint32_t last_faction_count = 0;
  std::array<std::uint32_t, kFactionTargetingRowObserverMaximumRowsV1>
      last_faction_ids{};
  std::uint32_t last_thread_id = 0;
  std::uint64_t last_timestamp_qpc = 0;
};

struct FactionTargetingRowObserverDiagnosticsV1 {
  bool installed = false;
  bool offline_fixture = false;
  std::uint32_t failure_flags = faction_targeting_row_observer_failure_none;
  FactionTargetingRowObservationDiagnosticsV1 observation{};
};

bool InstallFactionTargetingRowObserverV1(
    FactionTargetingRowObserverStateV1 &state,
    const FactionTargetingRowObserverEnvironmentV1 &environment) noexcept;
bool UninstallFactionTargetingRowObserverV1(
    FactionTargetingRowObserverStateV1 &state) noexcept;
FactionTargetingRowObserverDiagnosticsV1
ReadFactionTargetingRowObserverDiagnosticsV1(
    const FactionTargetingRowObserverStateV1 &state) noexcept;

bool CaptureFactionTargetingRowsV1(
    FactionTargetingRowObserverStateV1 &state,
    std::uintptr_t targeting_container_address,
    std::uint32_t current_thread_id, std::uint64_t timestamp_qpc) noexcept;

} // namespace xar::bridge
