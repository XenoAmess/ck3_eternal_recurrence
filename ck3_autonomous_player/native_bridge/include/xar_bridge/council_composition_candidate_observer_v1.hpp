#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string>

#include <windows.h>

namespace xar::bridge {

inline constexpr char kCouncilCompositionCandidateObserverExecutableSha256V1[] =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::uintptr_t
    kCouncilCompositionCandidateObserverPatchRvaV1 = 0x1058200;
inline constexpr std::uintptr_t
    kCouncilCompositionCandidateObserverCallRvaV1 = 0x105820A;
inline constexpr std::uintptr_t
    kCouncilCompositionCandidateObserverContinueRvaV1 = 0x105820F;
inline constexpr std::uintptr_t kCouncilCompositionCandidateProducerRvaV1 =
    0x293BD00;
inline constexpr std::size_t kCouncilCompositionCandidateObserverPatchBytesV1 =
    15;
inline constexpr std::size_t kCouncilCompositionCandidateObserverStubCapacityV1 =
    256;
inline constexpr std::size_t kCouncilCompositionCandidateObserverMaxRowsV1 =
    256;
inline constexpr std::int32_t
    kCouncilCompositionCandidateObserverMaxNativeCapacityV1 = 4096;
inline constexpr std::size_t
    kCouncilCompositionCandidateObserverPositionKeyCapacityV1 = 64;
inline constexpr bool
    kCouncilCompositionCandidateObserverInstalledByDefaultV1 = false;

enum CouncilCompositionCandidateObserverFailureV1 : std::uint32_t {
  council_composition_candidate_observer_failure_none = 0,
  council_composition_candidate_observer_failure_exact_build = 1U << 0,
  council_composition_candidate_observer_failure_primary_thread_suspended =
      1U << 1,
  council_composition_candidate_observer_failure_unsupported_override =
      1U << 2,
  council_composition_candidate_observer_failure_already_installed = 1U << 3,
  council_composition_candidate_observer_failure_anchor = 1U << 4,
  council_composition_candidate_observer_failure_allocation = 1U << 5,
  council_composition_candidate_observer_failure_stub_protection = 1U << 6,
  council_composition_candidate_observer_failure_target_protection = 1U << 7,
  council_composition_candidate_observer_failure_target_identity = 1U << 8,
  council_composition_candidate_observer_failure_flush = 1U << 9,
  council_composition_candidate_observer_failure_rollback = 1U << 10,
  council_composition_candidate_observer_failure_thread_source = 1U << 11,
  council_composition_candidate_observer_failure_paused_source = 1U << 12,
};

enum CouncilCompositionCandidateCaptureFailureV1 : std::uint32_t {
  council_composition_candidate_capture_failure_none = 0,
  council_composition_candidate_capture_failure_ui_thread_unavailable =
      1U << 0,
  council_composition_candidate_capture_failure_wrong_thread = 1U << 1,
  council_composition_candidate_capture_failure_not_paused = 1U << 2,
  council_composition_candidate_capture_failure_owner_id_unreadable = 1U << 3,
  council_composition_candidate_capture_failure_task_id_unreadable = 1U << 4,
  council_composition_candidate_capture_failure_position_key_unreadable =
      1U << 5,
  council_composition_candidate_capture_failure_header_unreadable = 1U << 6,
  council_composition_candidate_capture_failure_invalid_span = 1U << 7,
  council_composition_candidate_capture_failure_row_unreadable = 1U << 8,
  council_composition_candidate_capture_failure_character_id_unreadable =
      1U << 9,
  council_composition_candidate_capture_failure_already_captured = 1U << 10,
};

using CouncilCompositionCandidateObserverVirtualAllocV1 = void *(*) (
    void *context, std::size_t size, DWORD allocation_type,
    DWORD protection) noexcept;
using CouncilCompositionCandidateObserverVirtualFreeV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD free_type) noexcept;
using CouncilCompositionCandidateObserverVirtualProtectV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using CouncilCompositionCandidateObserverFlushInstructionCacheV1 = bool (*) (
    void *context, const void *address, std::size_t size) noexcept;

struct CouncilCompositionCandidateObserverEnvironmentV1 {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  const std::atomic<std::uint32_t> *ui_thread_id_source = nullptr;
  const std::atomic<bool> *paused_source = nullptr;
  std::uintptr_t patch_target_override = 0;
  std::uintptr_t continue_target_override = 0;
  std::uintptr_t producer_target_override = 0;
  void *memory_context = nullptr;
  CouncilCompositionCandidateObserverVirtualAllocV1 virtual_alloc_override =
      nullptr;
  CouncilCompositionCandidateObserverVirtualFreeV1 virtual_free_override =
      nullptr;
  CouncilCompositionCandidateObserverVirtualProtectV1
      virtual_protect_override = nullptr;
  CouncilCompositionCandidateObserverFlushInstructionCacheV1
      flush_instruction_cache_override = nullptr;
};

struct CouncilCompositionCandidateCapturedRowV1 {
  std::uint32_t character_id = 0;
  std::uint64_t raw_row_bytes = 0;
};

struct CouncilCompositionCandidateObservationV1 {
  std::atomic<std::uint64_t> call_count{0};
  std::atomic<std::uint64_t> accepted_count{0};
  std::atomic<std::uint64_t> rejected_count{0};
  std::atomic<std::uint64_t> ignored_after_capture_count{0};
  std::atomic<std::uint32_t> last_capture_failure_flags{
      council_composition_candidate_capture_failure_none};
  std::atomic<std::uint64_t> capture_sequence{0};
  std::atomic<std::uint32_t> capture_complete{0};
  std::atomic<std::uint32_t> last_ui_thread_id{0};
  std::atomic<std::uint32_t> last_thread_id{0};
  std::atomic<std::uint64_t> last_timestamp_qpc{0};
  std::atomic<std::uint32_t> last_owner_character_id{0};
  std::atomic<std::uint32_t> last_active_task_id{0};
  std::atomic<std::int32_t> last_vector_capacity{0};
  std::atomic<std::int32_t> last_vector_count{0};
  std::atomic<std::uint32_t> last_captured_row_count{0};
  std::atomic<std::uint32_t> last_duplicate_character_id_count{0};
  std::atomic<std::uint32_t> last_position_key_size{0};
  std::array<std::atomic<std::uint8_t>,
             kCouncilCompositionCandidateObserverPositionKeyCapacityV1>
      last_position_key{};
  std::array<std::atomic<std::uint32_t>,
             kCouncilCompositionCandidateObserverMaxRowsV1>
      last_character_ids{};
  std::array<std::atomic<std::uint64_t>,
             kCouncilCompositionCandidateObserverMaxRowsV1>
      last_raw_row_bytes{};
};

struct CouncilCompositionCandidateObserverStateV1 {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{
      council_composition_candidate_observer_failure_none};
  CouncilCompositionCandidateObservationV1 observation{};

  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target = 0;
  std::uintptr_t continue_target = 0;
  std::uintptr_t producer_target = 0;
  void *stub = nullptr;
  std::array<std::uint8_t,
             kCouncilCompositionCandidateObserverPatchBytesV1>
      original_patch_bytes{};
  std::array<std::uint8_t,
             kCouncilCompositionCandidateObserverPatchBytesV1>
      installed_patch_bytes{};
  const std::atomic<std::uint32_t> *ui_thread_id_source = nullptr;
  const std::atomic<bool> *paused_source = nullptr;
  void *memory_context = nullptr;
  CouncilCompositionCandidateObserverVirtualFreeV1 virtual_free = nullptr;
  CouncilCompositionCandidateObserverVirtualProtectV1 virtual_protect =
      nullptr;
  CouncilCompositionCandidateObserverFlushInstructionCacheV1
      flush_instruction_cache = nullptr;
};

struct CouncilCompositionCandidateObservationDiagnosticsV1 {
  std::uint64_t call_count = 0;
  std::uint64_t accepted_count = 0;
  std::uint64_t rejected_count = 0;
  std::uint64_t ignored_after_capture_count = 0;
  std::uint32_t last_capture_failure_flags =
      council_composition_candidate_capture_failure_none;
  bool capture_consistent = false;
  bool capture_complete = false;
  std::uint32_t last_ui_thread_id = 0;
  std::uint32_t last_thread_id = 0;
  std::uint64_t last_timestamp_qpc = 0;
  std::uint32_t last_owner_character_id = 0;
  std::uint32_t last_active_task_id = 0;
  std::int32_t last_vector_capacity = 0;
  std::int32_t last_vector_count = 0;
  std::uint32_t last_captured_row_count = 0;
  std::uint32_t last_duplicate_character_id_count = 0;
  std::array<char,
             kCouncilCompositionCandidateObserverPositionKeyCapacityV1>
      last_position_key{};
  std::array<CouncilCompositionCandidateCapturedRowV1,
             kCouncilCompositionCandidateObserverMaxRowsV1>
      rows{};
};

struct CouncilCompositionCandidateObserverDiagnosticsV1 {
  bool installed = false;
  std::uint32_t failure_flags =
      council_composition_candidate_observer_failure_none;
  CouncilCompositionCandidateObservationDiagnosticsV1 observation{};
};

bool InstallCouncilCompositionCandidateObserverV1(
    CouncilCompositionCandidateObserverStateV1 &state,
    const CouncilCompositionCandidateObserverEnvironmentV1
        &environment) noexcept;
bool UninstallCouncilCompositionCandidateObserverV1(
    CouncilCompositionCandidateObserverStateV1 &state) noexcept;

bool CaptureCouncilCompositionCandidatePostCallV1(
    CouncilCompositionCandidateObserverStateV1 &state,
    std::uintptr_t owner_character, std::uintptr_t active_task,
    std::uintptr_t vector_header, std::uint32_t thread_id,
    std::uint64_t timestamp_qpc) noexcept;

CouncilCompositionCandidateObserverDiagnosticsV1
ReadCouncilCompositionCandidateObserverDiagnosticsV1(
    const CouncilCompositionCandidateObserverStateV1 &state) noexcept;

std::string SerializeCouncilCompositionCandidateObserverDiagnosticsV1(
    const CouncilCompositionCandidateObserverDiagnosticsV1 &diagnostics);

} // namespace xar::bridge
