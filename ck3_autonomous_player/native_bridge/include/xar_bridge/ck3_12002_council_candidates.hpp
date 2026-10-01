#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/council_composition_candidates_public_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kCouncilCandidatesProducerRva12002 = 0x2C47EC0;
inline constexpr std::uintptr_t kCouncilCandidatesAllocatorVtableRva12002 = 0x452D0A8;
inline constexpr std::uintptr_t kCouncilCandidatesFallbackAllocatorRva12002 = 0x54DEDE0;
inline constexpr std::uintptr_t kCouncilCandidatesInitializeRva12002 = 0x98B8C0;
inline constexpr std::uintptr_t kCouncilCandidatesReleaseRva12002 = 0x855830;
inline constexpr std::uintptr_t kCouncilCandidatesCharacterFallbackSlotRva12002 = 0x5C67570;
inline constexpr std::uintptr_t kCouncilCandidatesTaskStorageSlotRva12002 = 0x5D1DEA0;
inline constexpr std::uintptr_t kCouncilCandidatesTaskFallbackSlotRva12002 = 0x5D1DDF8;
inline constexpr std::size_t kCouncilCandidatesAllocatorSize12002 = 0x210;
inline constexpr std::size_t kCouncilCandidatesAllocatorFallbackOffset12002 = 0x208;
inline constexpr std::size_t kCouncilCandidatesCharacterStewardshipOffset12002 = 0xE0;
inline constexpr std::size_t kCouncilCandidatesTaskIncumbentOffset12002 = 0x40;

using CouncilCandidatesFrameV1 =
    ck3_11906::CouncilCompositionStewardCandidatesFrameV1;
using CouncilCandidatesRequestV1 =
    ck3_11906::CouncilCompositionStewardCandidatesRequestV1;

// The GUI producer owns no rows after this temporary vector is released.
// A row is an eight-byte CCharacter pointer, never a public identity.
struct CouncilCandidatesNativeVectorV1 {
  std::uintptr_t data_address = 0;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
  void *allocator = nullptr;
};
static_assert(sizeof(CouncilCandidatesNativeVectorV1) == 0x18);
static_assert(offsetof(CouncilCandidatesNativeVectorV1, allocator) == 0x10);

using NativeCouncilCandidatesInitialize12002 =
    void (*)(void *, std::uintptr_t *, std::int32_t *);
using NativeCouncilCandidatesProducer12002 =
    void (*)(const void *, const void *, bool, CouncilCandidatesNativeVectorV1 *);
using NativeCouncilCandidatesRelease12002 =
    void (*)(void *, void *, std::size_t);

struct CouncilCandidatesEnvironmentV1 {
  bool exact_build_admitted = false;
  // Fixture-owned globals/functions only; production Bind leaves this false.
  bool offline_fixture_function_overrides = false;
  std::uintptr_t module_base = 0;
  std::string_view admitted_executable_sha256{};
  void **character_storage_slot = nullptr;
  void **character_fallback_slot = nullptr;
  void **active_task_storage_slot = nullptr;
  void **active_task_fallback_slot = nullptr;
  std::uintptr_t allocator_vtable = 0;
  std::uintptr_t fallback_allocator = 0;
  NativeCouncilCandidatesInitialize12002 initialize_vector = nullptr;
  NativeCouncilCandidatesProducer12002 produce_candidates = nullptr;
  NativeCouncilCandidatesRelease12002 release_allocation = nullptr;
};

using CouncilCandidatesReadMemoryV1 =
    bool (*)(void *, const void *, void *, std::size_t) noexcept;
using CouncilCandidatesInitializeOverrideV1 = bool (*)(
    void *, const CouncilCandidatesEnvironmentV1 &, void *, std::size_t,
    CouncilCandidatesNativeVectorV1 &) noexcept;
using CouncilCandidatesProduceOverrideV1 = bool (*)(
    void *, const CouncilCandidatesEnvironmentV1 &, const void *, const void *,
    bool, CouncilCandidatesNativeVectorV1 &) noexcept;
using CouncilCandidatesReleaseOverrideV1 = bool (*)(
    void *, const CouncilCandidatesEnvironmentV1 &,
    CouncilCandidatesNativeVectorV1 &) noexcept;

struct CouncilCandidatesAccessV1 {
  void *context = nullptr;
  // Source frame supplies snapshot/date/revisions/player. This reader resolves
  // the steward task from the same frame, and does not trust a cached task.
  ck3_11906::CaptureCouncilCompositionStewardCandidatesFrameV1 capture_frame = nullptr;
  ck3_11906::IsCouncilCompositionStewardCandidatesMainThreadV1 is_main_thread = nullptr;
  CouncilCandidatesReadMemoryV1 read_memory = nullptr; // null = in-process read
  // Optional fixture callbacks. Accepted only when the environment explicitly
  // declares offline_fixture_function_overrides.
  CouncilCandidatesInitializeOverrideV1 initialize_vector = nullptr;
  CouncilCandidatesProduceOverrideV1 invoke_producer = nullptr;
  CouncilCandidatesReleaseOverrideV1 release_allocation = nullptr;
};

// Address calculation only. No process discovery, memory reads or native calls.
CouncilCandidatesEnvironmentV1 BindCouncilCandidates12002(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

bool ReadCouncilMemory12002(const CouncilCandidatesAccessV1 &access,
    const void *address, void *output, std::size_t size) noexcept;
bool ResolveCouncilCharacter12002(const CouncilCandidatesEnvironmentV1 &environment,
    const CouncilCandidatesAccessV1 &access, std::int32_t full_id,
    const void *&pointer) noexcept;
bool CaptureCouncilCandidatesFrame12002(
    const CouncilCandidatesEnvironmentV1 &environment,
    const CouncilCandidatesAccessV1 &access,
    CouncilCandidatesFrameV1 &output) noexcept;

// One application-main paused transaction: resolve -> GUI-mode native producer
// -> copy/round-trip IDs and native skill -> release -> recapture -> v1 projector.
// The private source output is optional and also zero-row on failure.
ck3_11906::ProjectCouncilCompositionCandidatesPublicResultV1
ReadCouncilCandidates12002(const CouncilCandidatesEnvironmentV1 &environment,
    const CouncilCandidatesAccessV1 &access,
    const CouncilCandidatesRequestV1 &request,
    game::CouncilCompositionCandidatesPublicV1 &output,
    game::CouncilCompositionStewardCandidatesV1 *private_source = nullptr) noexcept;

// Existing v1 wire shape with the actual 1.20.0.2 exact-build provenance.
std::string SerializeCouncilCandidates12002(
    const game::CouncilCompositionCandidatesPublicV1 &value);

} // namespace xar::ck3_12002
