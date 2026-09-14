#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string_view>

#include <windows.h>

namespace xar::bridge {

inline constexpr std::string_view
    kDomainConstructionCandidateObserverPrivateKeyV1 =
        "g2_domain_construction_candidate_observer_v1";
inline constexpr std::string_view
    kDomainConstructionCandidateObserverArtifactStemV1 =
        "g2-domain-construction-candidate-observer-v1";
inline constexpr std::string_view
    kDomainConstructionCandidateObserverCompileGateV1 =
        "XAR_CK3_ENABLE_G2_DOMAIN_CONSTRUCTION_CANDIDATE_OBSERVER_V1";
inline constexpr std::string_view
    kDomainConstructionCandidateObserverExecutableSha256V1 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view
    kDomainConstructionCandidateObserverNextReverseEngineeringEntryV1 =
        "ai_attempt_to_build_building_effect_0x2EBEE81_post_candidate_row_identity_decoder";

inline constexpr std::uintptr_t
    kDomainConstructionCandidateObserverPatchRvaV1 = 0x2EBEE81;
inline constexpr std::uintptr_t
    kDomainConstructionCandidateObserverCallRvaV1 = 0x2EBEE86;
inline constexpr std::uintptr_t
    kDomainConstructionCandidateObserverContinueRvaV1 = 0x2EBEE92;
inline constexpr std::uintptr_t
    kDomainConstructionCandidateProducerRvaV1 = 0x1921810;
inline constexpr std::uintptr_t
    kDomainConstructionCandidatePostCallGlobalSlotRvaV1 = 0x57BFBA8;
inline constexpr std::size_t
    kDomainConstructionCandidateObserverPatchBytesV1 = 17;
inline constexpr std::size_t
    kDomainConstructionCandidateObserverStubCapacityV1 = 192;
inline constexpr std::size_t kDomainConstructionCandidateRowBytesV1 = 0x28;
inline constexpr std::size_t
    kDomainConstructionCandidateObserverMaximumRowsV1 = 64;
inline constexpr bool
    kDomainConstructionCandidateObserverInstalledByDefaultV1 = false;

enum DomainConstructionCandidateObserverFailureV1 : std::uint32_t {
  domain_construction_candidate_observer_failure_none = 0,
  domain_construction_candidate_observer_failure_exact_build = 1U << 0,
  domain_construction_candidate_observer_failure_primary_thread_suspended =
      1U << 1,
  domain_construction_candidate_observer_failure_capture_admission = 1U << 2,
  domain_construction_candidate_observer_failure_unsupported_override = 1U << 3,
  domain_construction_candidate_observer_failure_already_installed = 1U << 4,
  domain_construction_candidate_observer_failure_anchor = 1U << 5,
  domain_construction_candidate_observer_failure_allocation = 1U << 6,
  domain_construction_candidate_observer_failure_stub_protection = 1U << 7,
  domain_construction_candidate_observer_failure_target_protection = 1U << 8,
  domain_construction_candidate_observer_failure_target_identity = 1U << 9,
  domain_construction_candidate_observer_failure_flush = 1U << 10,
  domain_construction_candidate_observer_failure_rollback = 1U << 11,
};

struct DomainConstructionCandidateCaptureAdmissionV1 {
  std::uint32_t application_main_thread_id = 0;
  bool paused = false;
  std::uint64_t proof_epoch = 0;
  std::int32_t date_raw = 0;
};

using DomainConstructionCandidateCaptureAdmissionProbeV1 = bool (*)(
    void *context,
    DomainConstructionCandidateCaptureAdmissionV1 &admission) noexcept;
using DomainConstructionCandidateMemoryReadV1 = bool (*)(
    void *context, std::uintptr_t address, void *output,
    std::size_t size) noexcept;
using DomainConstructionCandidateMemoryWriteV1 = bool (*)(
    void *context, std::uintptr_t address, const void *source,
    std::size_t size) noexcept;
using DomainConstructionCandidateVirtualAllocV1 = void *(*)(
    void *context, std::size_t size, DWORD allocation_type,
    DWORD protection) noexcept;
using DomainConstructionCandidateVirtualFreeV1 = bool (*)(
    void *context, void *address, std::size_t size, DWORD free_type) noexcept;
using DomainConstructionCandidateVirtualProtectV1 = bool (*)(
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using DomainConstructionCandidateFlushInstructionCacheV1 = bool (*)(
    void *context, const void *address, std::size_t size) noexcept;

struct DomainConstructionCandidateObserverEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target_override = 0;
  std::uintptr_t continue_target_override = 0;
  std::uintptr_t producer_target_override = 0;
  std::uintptr_t post_call_global_slot_target_override = 0;
  void *memory_context = nullptr;
  DomainConstructionCandidateMemoryReadV1 memory_read_override = nullptr;
  DomainConstructionCandidateMemoryWriteV1 memory_write_override = nullptr;
  DomainConstructionCandidateVirtualAllocV1 virtual_alloc_override = nullptr;
  DomainConstructionCandidateVirtualFreeV1 virtual_free_override = nullptr;
  DomainConstructionCandidateVirtualProtectV1 virtual_protect_override =
      nullptr;
  DomainConstructionCandidateFlushInstructionCacheV1
      flush_instruction_cache_override = nullptr;
  void *capture_admission_context = nullptr;
  DomainConstructionCandidateCaptureAdmissionProbeV1
      capture_admission_probe = nullptr;
};

struct DomainConstructionCandidateRawRowV1 {
  std::array<std::uint8_t, kDomainConstructionCandidateRowBytesV1> bytes{};
};

struct DomainConstructionCandidateCapturedRowV1 {
  std::int64_t score_raw = 0;
  std::array<std::uint8_t, kDomainConstructionCandidateRowBytesV1> row_bytes{};
  std::uint64_t row_bytes_fnv1a64 = 0;
};

struct DomainConstructionCandidateObservationV1 {
  std::atomic<std::uint64_t> producer_call_count{0};
  std::atomic<std::uint64_t> rejected_application_main_count{0};
  std::atomic<std::uint64_t> rejected_paused_count{0};
  std::atomic<std::uint64_t> capture_read_failure_count{0};
  std::atomic<std::uint64_t> accepted_capture_count{0};
  std::atomic<std::uint64_t> published_generation{0};
  std::atomic<std::uint64_t> last_proof_epoch{0};
  std::atomic<std::int32_t> last_date_raw{0};
  std::atomic<std::int32_t> last_vector_capacity{0};
  std::atomic<std::int32_t> last_vector_count{0};
  std::atomic<std::uint32_t> last_captured_row_count{0};
  std::atomic<std::uint32_t> last_rows_truncated{0};
  std::array<std::atomic<std::int64_t>,
             kDomainConstructionCandidateObserverMaximumRowsV1>
      last_scores_raw{};
  std::array<std::array<std::atomic<std::uint8_t>,
                        kDomainConstructionCandidateRowBytesV1>,
             kDomainConstructionCandidateObserverMaximumRowsV1>
      last_row_bytes{};
  std::array<std::atomic<std::uint64_t>,
             kDomainConstructionCandidateObserverMaximumRowsV1>
      last_row_bytes_fnv1a64{};
  std::atomic<std::uint32_t> last_thread_id{0};
  std::atomic<std::uint64_t> last_timestamp_qpc{0};
};

struct DomainConstructionCandidateObserverStateV1 {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{
      domain_construction_candidate_observer_failure_none};
  DomainConstructionCandidateObservationV1 observation{};

  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target = 0;
  std::uintptr_t continue_target = 0;
  std::uintptr_t producer_target = 0;
  std::uintptr_t post_call_global_slot_target = 0;
  void *stub = nullptr;
  std::array<std::uint8_t, kDomainConstructionCandidateObserverPatchBytesV1>
      original_patch_bytes{};
  std::array<std::uint8_t, kDomainConstructionCandidateObserverPatchBytesV1>
      installed_patch_bytes{};
  void *memory_context = nullptr;
  DomainConstructionCandidateMemoryReadV1 memory_read = nullptr;
  DomainConstructionCandidateMemoryWriteV1 memory_write = nullptr;
  DomainConstructionCandidateVirtualFreeV1 virtual_free = nullptr;
  DomainConstructionCandidateVirtualProtectV1 virtual_protect = nullptr;
  DomainConstructionCandidateFlushInstructionCacheV1
      flush_instruction_cache = nullptr;
  void *capture_admission_context = nullptr;
  DomainConstructionCandidateCaptureAdmissionProbeV1
      capture_admission_probe = nullptr;
};

struct DomainConstructionCandidateObservationDiagnosticsV1 {
  std::uint64_t producer_call_count = 0;
  std::uint64_t rejected_application_main_count = 0;
  std::uint64_t rejected_paused_count = 0;
  std::uint64_t capture_read_failure_count = 0;
  std::uint64_t accepted_capture_count = 0;
  std::uint64_t published_generation = 0;
  std::uint64_t last_proof_epoch = 0;
  std::int32_t last_date_raw = 0;
  std::int32_t last_vector_capacity = 0;
  std::int32_t last_vector_count = 0;
  std::uint32_t last_captured_row_count = 0;
  bool last_rows_truncated = false;
  std::array<DomainConstructionCandidateCapturedRowV1,
             kDomainConstructionCandidateObserverMaximumRowsV1>
      rows{};
  std::uint32_t last_thread_id = 0;
  std::uint64_t last_timestamp_qpc = 0;
};

struct DomainConstructionCandidateObserverDiagnosticsV1 {
  bool installed = false;
  bool offline_fixture = false;
  std::uint32_t failure_flags =
      domain_construction_candidate_observer_failure_none;
  DomainConstructionCandidateObservationDiagnosticsV1 observation{};
};

bool InstallDomainConstructionCandidateObserverV1(
    DomainConstructionCandidateObserverStateV1 &state,
    const DomainConstructionCandidateObserverEnvironmentV1
        &environment) noexcept;
bool UninstallDomainConstructionCandidateObserverV1(
    DomainConstructionCandidateObserverStateV1 &state) noexcept;
DomainConstructionCandidateObserverDiagnosticsV1
ReadDomainConstructionCandidateObserverDiagnosticsV1(
    const DomainConstructionCandidateObserverStateV1 &state) noexcept;

bool CaptureDomainConstructionCandidatePostCallV1(
    DomainConstructionCandidateObserverStateV1 &state,
    std::uintptr_t output_vector_address, std::uint32_t current_thread_id,
    std::uint64_t timestamp_qpc) noexcept;

} // namespace xar::bridge
