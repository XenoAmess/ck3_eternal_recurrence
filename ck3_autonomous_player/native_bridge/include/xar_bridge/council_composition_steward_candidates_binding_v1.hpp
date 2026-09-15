#pragma once

#include "xar_bridge/council_composition_steward_candidates_reader_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_11906 {

struct CouncilCompositionCandidatesEnrichmentAccessV1;

inline constexpr std::string_view
    kCouncilCompositionStewardCandidatesBindingPrivateKeyV1 =
        "g2_council_composition_steward_candidates_binding_v1";
inline constexpr std::uintptr_t
    kCouncilCompositionStewardInlineAllocatorVtableRvaV1 = 0x4098A20;
inline constexpr std::uintptr_t
    kCouncilCompositionStewardInlineAllocatorFallbackRvaV1 = 0x4FEBE00;
inline constexpr std::uintptr_t
    kCouncilCompositionStewardInlineAllocatorInitializeRvaV1 = 0x91E320;
inline constexpr std::uintptr_t
    kCouncilCompositionStewardInlineAllocatorReleaseRvaV1 = 0x7E8FB0;
inline constexpr std::size_t kCouncilCompositionStewardInlineAllocatorSizeV1 =
    0x210;
inline constexpr std::size_t
    kCouncilCompositionStewardInlineAllocatorFallbackOffsetV1 = 0x208;
inline constexpr std::int32_t
    kCouncilCompositionStewardInlineCandidateCapacityV1 = 64;

struct CouncilCompositionStewardCandidatesBindingNativeVectorV1 {
  std::uintptr_t data_address = 0;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
  void *allocator = nullptr;
};

using CouncilCompositionStewardBindingReadMemoryV1 =
    bool (*)(void *context, const void *address, void *output,
             std::size_t size) noexcept;
using CouncilCompositionStewardBindingReadStableKeyV1 =
    bool (*)(void *context, const void *native_string, char *output,
             std::size_t output_capacity) noexcept;
using CouncilCompositionStewardBindingResolveCharacterV1 = bool (*)(
    void *context, std::uintptr_t module_base, std::int32_t full_character_id,
    std::uintptr_t &character) noexcept;
using CouncilCompositionStewardBindingInitializeVectorV1 = bool (*)(
    void *context, std::uintptr_t module_base, void *allocator_storage,
    std::size_t allocator_storage_size,
    CouncilCompositionStewardCandidatesBindingNativeVectorV1 &vector) noexcept;
using CouncilCompositionStewardBindingInvokeProducerV1 = bool (*)(
    void *context, std::uintptr_t module_base, std::uintptr_t owner_character,
    std::uintptr_t active_task, bool gui_eligibility_mode,
    CouncilCompositionStewardCandidatesBindingNativeVectorV1 &vector) noexcept;
using CouncilCompositionStewardBindingReleaseAllocationV1 =
    bool (*)(void *context, std::uintptr_t module_base, void *allocator,
             std::uintptr_t data_address, std::size_t element_size) noexcept;

struct CouncilCompositionStewardCandidatesBindingOperationsV1 {
  CouncilCompositionStewardBindingReadMemoryV1 read_memory = nullptr;
  CouncilCompositionStewardBindingReadStableKeyV1 read_stable_key = nullptr;
  CouncilCompositionStewardBindingResolveCharacterV1 resolve_character =
      nullptr;
  CouncilCompositionStewardBindingInitializeVectorV1 initialize_vector =
      nullptr;
  CouncilCompositionStewardBindingInvokeProducerV1 invoke_producer = nullptr;
  CouncilCompositionStewardBindingReleaseAllocationV1 release_allocation =
      nullptr;
};

struct CouncilCompositionStewardCandidatesBindingEnvironmentV1 {
  bool binding_enabled = false;
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  void *operation_context = nullptr;
  CouncilCompositionStewardCandidatesBindingOperationsV1 operations{};
};

struct CouncilCompositionStewardCandidatesBindingStateV1 {
  std::uintptr_t module_base = 0;
  void *operation_context = nullptr;
  CouncilCompositionStewardCandidatesBindingOperationsV1 operations{};

  void *upstream_context = nullptr;
  CaptureCouncilCompositionStewardCandidatesFrameV1 upstream_capture_frame =
      nullptr;
  IsCouncilCompositionStewardCandidatesMainThreadV1 upstream_is_main_thread =
      nullptr;

  std::array<std::byte, kCouncilCompositionStewardInlineAllocatorSizeV1 + 15>
      allocator_storage{};
  CouncilCompositionStewardCandidatesBindingNativeVectorV1 native_vector{};
  CouncilCompositionStewardCandidatesFrameV1 bound_frame{};
  bool attached = false;
  bool frame_bound = false;
  bool transaction_active = false;
  bool vector_initialized = false;
  bool producer_invoked = false;
};

// Completes the Council6 private reader dependencies without registering a
// bridge command or public capability.  The caller supplies the existing
// application-main frame/main-thread callbacks; this binding resolves the
// active steward task and owns one exact native vector transaction.
bool BindCouncilCompositionStewardCandidatesV1(
    const CouncilCompositionStewardCandidatesBindingEnvironmentV1 &binding,
    CouncilCompositionStewardCandidatesBindingStateV1 &state,
    CouncilCompositionStewardCandidatesEnvironmentV1 &core_environment,
    CouncilCompositionStewardCandidatesAccessV1 &core_access) noexcept;

// Reuses the exact native memory and Character resolver operations from an
// attached steward binding after its private read has released the temporary
// candidate vector. The returned access remains application-main/frame-bound.
bool BindCouncilCompositionCandidatesEnrichmentAccessV1(
    CouncilCompositionStewardCandidatesBindingStateV1 &state,
    CouncilCompositionCandidatesEnrichmentAccessV1 &access) noexcept;

} // namespace xar::ck3_11906
