#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string_view>

#include <windows.h>

namespace xar::bridge {

inline constexpr std::string_view
    kDomainConstructionRuntimeObserverPrivateKeyV1 =
        "g2_domain_construction_native_runtime_callsite_observer_v1";
inline constexpr std::string_view
    kDomainConstructionRuntimeObserverArtifactStemV1 =
        "g2-domain-construction-native-runtime-callsite-observer-v1";
inline constexpr std::string_view
    kDomainConstructionRuntimeObserverCompileGateV1 =
        "XAR_CK3_ENABLE_G2_DOMAIN_CONSTRUCTION_RUNTIME_OBSERVER_V1";
inline constexpr std::string_view
    kDomainConstructionRuntimeObserverExecutableSha256V1 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view
    kDomainConstructionRuntimeObserverNextReverseEngineeringEntryV1 =
        "native_runtime_0x18D2954_candidate_row_identity_decoder";

inline constexpr std::uintptr_t
    kDomainConstructionRuntimeObserverPatchRvaV1 = 0x18D2948;
inline constexpr std::uintptr_t
    kDomainConstructionRuntimeObserverCallRvaV1 = 0x18D294F;
inline constexpr std::uintptr_t
    kDomainConstructionRuntimeObserverContinueRvaV1 = 0x18D2958;
inline constexpr std::uintptr_t
    kDomainConstructionRuntimeProducerRvaV1 = 0x1921810;
inline constexpr std::size_t
    kDomainConstructionRuntimeObserverPatchBytesV1 = 16;
inline constexpr std::size_t
    kDomainConstructionRuntimeObserverStubCapacityV1 = 192;
inline constexpr std::size_t kDomainConstructionRuntimeRowBytesV1 = 0x28;
inline constexpr std::size_t
    kDomainConstructionRuntimeObserverMaximumRowsV1 = 64;
inline constexpr bool
    kDomainConstructionRuntimeObserverInstalledByDefaultV1 = false;

enum DomainConstructionRuntimeObserverFailureV1 : std::uint32_t {
  domain_construction_runtime_observer_failure_none = 0,
  domain_construction_runtime_observer_failure_exact_build = 1U << 0,
  domain_construction_runtime_observer_failure_primary_thread_suspended =
      1U << 1,
  domain_construction_runtime_observer_failure_capture_admission = 1U << 2,
  domain_construction_runtime_observer_failure_unsupported_override = 1U << 3,
  domain_construction_runtime_observer_failure_already_installed = 1U << 4,
  domain_construction_runtime_observer_failure_anchor = 1U << 5,
  domain_construction_runtime_observer_failure_allocation = 1U << 6,
  domain_construction_runtime_observer_failure_stub_protection = 1U << 7,
  domain_construction_runtime_observer_failure_target_protection = 1U << 8,
  domain_construction_runtime_observer_failure_target_identity = 1U << 9,
  domain_construction_runtime_observer_failure_flush = 1U << 10,
  domain_construction_runtime_observer_failure_rollback = 1U << 11,
};

struct DomainConstructionRuntimeCaptureAdmissionV1 {
  std::uint32_t application_main_thread_id = 0;
  bool session_live = false;
  bool paused = false;
  std::uint64_t proof_epoch = 0;
  std::int32_t date_raw = 0;
};

using DomainConstructionRuntimeCaptureAdmissionProbeV1 = bool (*)(
    void *context,
    DomainConstructionRuntimeCaptureAdmissionV1 &admission) noexcept;
using DomainConstructionRuntimeMemoryReadV1 = bool (*)(
    void *context, std::uintptr_t address, void *output,
    std::size_t size) noexcept;
using DomainConstructionRuntimeMemoryWriteV1 = bool (*)(
    void *context, std::uintptr_t address, const void *source,
    std::size_t size) noexcept;
using DomainConstructionRuntimeVirtualAllocV1 = void *(*)(
    void *context, std::size_t size, DWORD allocation_type,
    DWORD protection) noexcept;
using DomainConstructionRuntimeVirtualFreeV1 = bool (*)(
    void *context, void *address, std::size_t size, DWORD free_type) noexcept;
using DomainConstructionRuntimeVirtualProtectV1 = bool (*)(
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using DomainConstructionRuntimeFlushInstructionCacheV1 = bool (*)(
    void *context, const void *address, std::size_t size) noexcept;

struct DomainConstructionRuntimeObserverEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target_override = 0;
  std::uintptr_t continue_target_override = 0;
  std::uintptr_t producer_target_override = 0;
  void *memory_context = nullptr;
  DomainConstructionRuntimeMemoryReadV1 memory_read_override = nullptr;
  DomainConstructionRuntimeMemoryWriteV1 memory_write_override = nullptr;
  DomainConstructionRuntimeVirtualAllocV1 virtual_alloc_override = nullptr;
  DomainConstructionRuntimeVirtualFreeV1 virtual_free_override = nullptr;
  DomainConstructionRuntimeVirtualProtectV1 virtual_protect_override = nullptr;
  DomainConstructionRuntimeFlushInstructionCacheV1
      flush_instruction_cache_override = nullptr;
  void *capture_admission_context = nullptr;
  DomainConstructionRuntimeCaptureAdmissionProbeV1
      capture_admission_probe = nullptr;
};

struct DomainConstructionRuntimeRawRowV1 {
  std::array<std::uint8_t, kDomainConstructionRuntimeRowBytesV1> bytes{};
};

struct DomainConstructionRuntimeCapturedRowV1 {
  std::int64_t score_raw = 0;
  std::array<std::uint8_t, kDomainConstructionRuntimeRowBytesV1> row_bytes{};
  std::uint64_t row_bytes_fnv1a64 = 0;
};

struct DomainConstructionRuntimeObservationV1 {
  std::atomic<std::uint64_t> producer_call_count{0};
  std::atomic<std::uint64_t> rejected_application_main_count{0};
  std::atomic<std::uint64_t> rejected_session_count{0};
  std::atomic<std::uint64_t> capture_read_failure_count{0};
  std::atomic<std::uint64_t> accepted_capture_count{0};
  std::atomic<std::uint64_t> published_generation{0};
  std::atomic<std::uint64_t> last_proof_epoch{0};
  std::atomic<std::int32_t> last_date_raw{0};
  std::atomic<std::uint32_t> last_paused{0};
  std::atomic<std::int32_t> last_vector_capacity{0};
  std::atomic<std::int32_t> last_vector_count{0};
  std::atomic<std::uint32_t> last_captured_row_count{0};
  std::atomic<std::uint32_t> last_rows_truncated{0};
  std::array<std::atomic<std::int64_t>,
             kDomainConstructionRuntimeObserverMaximumRowsV1>
      last_scores_raw{};
  std::array<std::array<std::atomic<std::uint8_t>,
                        kDomainConstructionRuntimeRowBytesV1>,
             kDomainConstructionRuntimeObserverMaximumRowsV1>
      last_row_bytes{};
  std::array<std::atomic<std::uint64_t>,
             kDomainConstructionRuntimeObserverMaximumRowsV1>
      last_row_bytes_fnv1a64{};
  std::atomic<std::uint32_t> last_thread_id{0};
  std::atomic<std::uint64_t> last_timestamp_qpc{0};
};

struct DomainConstructionRuntimeObserverStateV1 {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{
      domain_construction_runtime_observer_failure_none};
  DomainConstructionRuntimeObservationV1 observation{};

  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target = 0;
  std::uintptr_t continue_target = 0;
  std::uintptr_t producer_target = 0;
  void *stub = nullptr;
  std::array<std::uint8_t, kDomainConstructionRuntimeObserverPatchBytesV1>
      original_patch_bytes{};
  std::array<std::uint8_t, kDomainConstructionRuntimeObserverPatchBytesV1>
      installed_patch_bytes{};
  void *memory_context = nullptr;
  DomainConstructionRuntimeMemoryReadV1 memory_read = nullptr;
  DomainConstructionRuntimeMemoryWriteV1 memory_write = nullptr;
  DomainConstructionRuntimeVirtualFreeV1 virtual_free = nullptr;
  DomainConstructionRuntimeVirtualProtectV1 virtual_protect = nullptr;
  DomainConstructionRuntimeFlushInstructionCacheV1
      flush_instruction_cache = nullptr;
  void *capture_admission_context = nullptr;
  DomainConstructionRuntimeCaptureAdmissionProbeV1
      capture_admission_probe = nullptr;
};

struct DomainConstructionRuntimeObservationDiagnosticsV1 {
  std::uint64_t producer_call_count = 0;
  std::uint64_t rejected_application_main_count = 0;
  std::uint64_t rejected_session_count = 0;
  std::uint64_t capture_read_failure_count = 0;
  std::uint64_t accepted_capture_count = 0;
  std::uint64_t published_generation = 0;
  std::uint64_t last_proof_epoch = 0;
  std::int32_t last_date_raw = 0;
  bool last_paused = false;
  std::int32_t last_vector_capacity = 0;
  std::int32_t last_vector_count = 0;
  std::uint32_t last_captured_row_count = 0;
  bool last_rows_truncated = false;
  std::array<DomainConstructionRuntimeCapturedRowV1,
             kDomainConstructionRuntimeObserverMaximumRowsV1>
      rows{};
  std::uint32_t last_thread_id = 0;
  std::uint64_t last_timestamp_qpc = 0;
};

struct DomainConstructionRuntimeObserverDiagnosticsV1 {
  bool installed = false;
  bool offline_fixture = false;
  std::uint32_t failure_flags =
      domain_construction_runtime_observer_failure_none;
  DomainConstructionRuntimeObservationDiagnosticsV1 observation{};
};

bool InstallDomainConstructionRuntimeObserverV1(
    DomainConstructionRuntimeObserverStateV1 &state,
    const DomainConstructionRuntimeObserverEnvironmentV1
        &environment) noexcept;
bool UninstallDomainConstructionRuntimeObserverV1(
    DomainConstructionRuntimeObserverStateV1 &state) noexcept;
DomainConstructionRuntimeObserverDiagnosticsV1
ReadDomainConstructionRuntimeObserverDiagnosticsV1(
    const DomainConstructionRuntimeObserverStateV1 &state) noexcept;
bool CaptureDomainConstructionRuntimePostCallV1(
    DomainConstructionRuntimeObserverStateV1 &state,
    std::uintptr_t output_vector_address, std::uint32_t current_thread_id,
    std::uint64_t timestamp_qpc) noexcept;

} // namespace xar::bridge
