#pragma once

#include "xar_bridge/marriage_proposal_native_binder_v1.hpp"

#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kMarriageRankedContainerAdapterPrivateKeyV1 =
    "marriage_ranked_container_adapter_v1";
inline constexpr std::uintptr_t kMarriageNativeTierRvaV1 = 0x2601F90;
inline constexpr std::uintptr_t kMarriageNativeCapTableSlotRvaV1 = 0x4F56B00;
inline constexpr std::uintptr_t kMarriageInitializeScoredContainerRvaV1 =
    0x101E070;
inline constexpr std::uintptr_t kMarriageReleaseNativeBufferRvaV1 = 0x7E8FB0;
inline constexpr std::uintptr_t kMarriageInitializeCandidateBufferRvaV1 =
    0x947C00;
inline constexpr std::uintptr_t kMarriageDestroyScoredRowRvaV1 = 0x81B620;
inline constexpr std::uintptr_t kMarriageCandidateOwnerVtableRvaV1 = 0x4117388;
inline constexpr std::uintptr_t kMarriageScoredOwnerVtableRvaV1 = 0x4117340;
inline constexpr std::uintptr_t kMarriageScoredRowVtableRvaV1 = 0x4116F08;
inline constexpr std::uintptr_t kMarriageCandidateBackingAllocatorRvaV1 =
    0x4FEAE00;
inline constexpr std::uintptr_t kMarriageScoredBackingAllocatorRvaV1 =
    0x4FED500;

inline constexpr std::size_t kMarriageRankedHeaderSizeV1 = 0x18;
inline constexpr std::size_t kMarriageCandidateOwnerSizeV1 = 0x410;
inline constexpr std::size_t kMarriageScoredOwnerSizeV1 = 0x210;
inline constexpr std::size_t kMarriageCandidateStorageSizeV1 = 0x428;
inline constexpr std::size_t kMarriageScoredStorageSizeV1 = 0x228;
inline constexpr std::size_t kMarriageCandidateInlineCapacityV1 = 0x80;
inline constexpr std::size_t kMarriageScoredInlineCapacityV1 = 0x20;

using ReadMarriageNativeTierV1 = std::int32_t (*)(void *character);
using EnumerateMarriageNativeCandidatesV1 = void (*)(
    void *strategy, std::int32_t opaque_selector, bool mode,
    std::int32_t native_cap, void *candidate_header);
using ScoreMarriageNativeCandidatesV1 = void (*)(
    void *strategy, const void *parameters, void *candidate_header,
    void *scored_header);
using InitializeMarriageScoredContainerV1 = void *(*)(void *scored_header);
using ReleaseMarriageNativeBufferV1 = void (*)(void *owner, void *data,
                                                std::size_t alignment);
using InitializeMarriageCandidateBufferV1 = void (*)(
    void *owner, void **data, std::int32_t *capacity);

enum class MarriageRankedContainerAdapterFailureV1 : std::uint32_t {
  none = 0,
  exact_build_not_admitted,
  binding_mismatch,
  signature_mismatch,
  memory_reader_unavailable,
  invalid_invocation,
  native_cap_unavailable,
  parameter_source_unavailable,
  candidate_container_invalid,
  scored_container_invalid,
  scored_row_identity_mismatch,
};

struct MarriageRankedContainerAdapterEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  bool offline_fixture = false;
  void *memory_context = nullptr;
  MarriageSourceAdapterMemoryReadV1 read_memory = nullptr;
  ReadMarriageNativeTierV1 read_native_tier = nullptr;
  std::uintptr_t native_cap_table_slot = 0;
  EnumerateMarriageNativeCandidatesV1 enumerate_candidates = nullptr;
  ScoreMarriageNativeCandidatesV1 score_candidates = nullptr;
  InitializeMarriageScoredContainerV1 initialize_scored_container = nullptr;
  ReleaseMarriageNativeBufferV1 release_native_buffer = nullptr;
  InitializeMarriageCandidateBufferV1 initialize_candidate_buffer = nullptr;
  std::uintptr_t candidate_owner_vtable = 0;
  std::uintptr_t scored_owner_vtable = 0;
  std::uintptr_t scored_row_vtable = 0;
  std::uintptr_t candidate_backing_allocator = 0;
  std::uintptr_t scored_backing_allocator = 0;
};

struct MarriageRankedContainerAdapterStateV1 {
  MarriageRankedContainerAdapterEnvironmentV1 environment{};
  std::atomic<std::uint32_t> last_failure{static_cast<std::uint32_t>(
      MarriageRankedContainerAdapterFailureV1::none)};
};

MarriageRankedContainerAdapterEnvironmentV1
BindMarriageRankedContainerAdapterEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept;

bool ConfigureMarriageRankedContainerAdapterV1(
    MarriageRankedContainerAdapterStateV1 &adapter,
    MarriageProposalNativeBinderStateV1 &binder) noexcept;

bool InvokeMarriageRankedContainerExactV1(
    void *context, const MarriageNativeRankedInvocationV1 &request,
    std::uintptr_t &container_token) noexcept;
bool ReadMarriageRankedContainerViewExactV1(
    void *context, std::uintptr_t container_token,
    MarriageNativeRankedContainerViewV1 &output) noexcept;
void ReleaseMarriageRankedContainerExactV1(
    void *context, std::uintptr_t container_token) noexcept;

MarriageRankedContainerAdapterFailureV1
ReadMarriageRankedContainerAdapterFailureV1(
    const MarriageRankedContainerAdapterStateV1 &adapter) noexcept;

} // namespace xar::bridge
