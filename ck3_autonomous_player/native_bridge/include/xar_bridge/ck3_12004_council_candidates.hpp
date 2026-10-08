#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_council_task_owner_tax.hpp"
#include "xar_bridge/council_composition_candidates_public_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kCouncilCandidatesProducerRva12004 = 0x2C47EA0;
inline constexpr std::uintptr_t kCouncilCandidatesAllocatorVtableRva12004 = 0x452D0B8;
inline constexpr std::uintptr_t kCouncilCandidatesFallbackAllocatorRva12004 = 0x54DEDE0;
inline constexpr std::uintptr_t kCouncilCandidatesInitializeRva12004 = 0x98B8C0;
inline constexpr std::uintptr_t kCouncilCandidatesReleaseRva12004 = 0x855830;
inline constexpr std::uintptr_t kCouncilCandidatesPositionLookupRva12004 = 0x2684EE0;
// Actual .3/.4 finite source proof: council-government/native-candidates.
// GUI call +0x11A identifies the new producer; GUI RIP +0x48 identifies
// the new allocator vtable. The remaining bindings have actual body/slot
// operands, not an old-build hash alias.
inline constexpr std::size_t kCouncilCandidatesCharacterExtensionOffset12004 = 0x1C0;
inline constexpr std::size_t kCouncilCandidatesTaskIdsOffset12004 = 0x230;
inline constexpr std::size_t kCouncilCandidatesTaskCountOffset12004 = 0x23C;
inline constexpr std::size_t kCouncilCandidatesTaskIdentityOffset12004 = 0x10;
inline constexpr std::size_t kCouncilCandidatesTaskTypeOffset12004 = 0x18;
inline constexpr std::size_t kCouncilCandidatesTaskTypePositionOffset12004 = 0x40;
inline constexpr std::size_t kCouncilCandidatesTaskOwnerOffset12004 = 0x44;
inline constexpr std::uintptr_t kCouncilCandidatesCharacterFallbackSlotRva12004 = 0x5C67570;
inline constexpr std::uintptr_t kCouncilCandidatesTaskStorageSlotRva12004 = 0x5D1DEA0;
inline constexpr std::uintptr_t kCouncilCandidatesTaskFallbackSlotRva12004 = 0x5D1DDF8;
inline constexpr std::size_t kCouncilCandidatesAllocatorSize12004 = 0x210;
inline constexpr std::size_t kCouncilCandidatesAllocatorFallbackOffset12004 = 0x208;
inline constexpr std::size_t kCouncilCandidatesCharacterStewardshipOffset12004 = 0xE0;
inline constexpr std::size_t kCouncilCandidatesCharacterDiplomacyOffset12004 = 0xD8;
inline constexpr std::size_t kCouncilCandidatesCharacterIntrigueOffset12004 = 0xE4;
inline constexpr std::size_t kCouncilCandidatesCharacterLearningOffset12004 = 0xE8;
inline constexpr std::size_t kCouncilCandidatesTaskIncumbentOffset12004 = 0x40;
inline constexpr std::string_view kCouncilCandidatesStewardPosition12004 =
    "councillor_steward";
inline constexpr std::string_view kCouncilCandidatesChancellorPosition12004 =
    "councillor_chancellor";
inline constexpr std::string_view kCouncilCandidatesSpymasterPosition12004 =
    "councillor_spymaster";
inline constexpr std::string_view kCouncilCandidatesChaplainPosition12004 =
    "councillor_court_chaplain";

struct CouncilCandidatesPositionProfile12004 {
  std::string_view position_key{};
  std::string_view main_skill_key{};
  std::size_t main_skill_offset = 0;
};

inline constexpr CouncilCandidatesPositionProfile12004 CouncilCandidatesProfile12004(
    std::string_view position_key) noexcept {
  if (position_key == kCouncilCandidatesStewardPosition12004)
    return {position_key, "stewardship", kCouncilCandidatesCharacterStewardshipOffset12004};
  if (position_key == kCouncilCandidatesChancellorPosition12004)
    return {position_key, "diplomacy", kCouncilCandidatesCharacterDiplomacyOffset12004};
  if (position_key == kCouncilCandidatesSpymasterPosition12004)
    return {position_key, "intrigue", kCouncilCandidatesCharacterIntrigueOffset12004};
  return {};
}

// Composition-only observation. The original profile remains the final-gates
// coverage map; this learning read does not add a clergy appointment route.
inline constexpr CouncilCandidatesPositionProfile12004 CouncilCandidatesCompositionProfile12004(
    std::string_view position_key) noexcept {
  if (position_key == kCouncilCandidatesChaplainPosition12004)
    return {position_key, "learning", kCouncilCandidatesCharacterLearningOffset12004};
  return CouncilCandidatesProfile12004(position_key);
}

using CouncilCandidatesFrameV1 =
    ck3_11906::CouncilCompositionStewardCandidatesFrameV1;
struct CouncilCandidatesRequestV1 {
  std::string_view expected_snapshot_id{};
  std::uint64_t expected_public_revision = 0;
  std::uint64_t expected_native_revision = 0;
  std::int32_t expected_date_raw = 0;
  std::int32_t expected_owner_character_id = -1;
  std::string_view position_key = kCouncilCandidatesStewardPosition12004;
};

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

using NativeCouncilCandidatesInitialize12004 =
    void (*)(void *, std::uintptr_t *, std::int32_t *);
using NativeCouncilCandidatesProducer12004 =
    void (*)(const void *, const void *, bool, CouncilCandidatesNativeVectorV1 *);
using NativeCouncilCandidatesRelease12004 =
    void (*)(void *, void *, std::size_t);

using NativeCouncilPositionLookup12004 =
    const void *(*)(const void *, const std::string *);

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
  NativeCouncilCandidatesInitialize12004 initialize_vector = nullptr;
  NativeCouncilCandidatesProducer12004 produce_candidates = nullptr;
  NativeCouncilCandidatesRelease12004 release_allocation = nullptr;
  NativeCouncilPositionLookup12004 position_lookup = nullptr;
  CouncilTaskOwnerTaxBindings12004 task_owner_tax{};
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

using LookupCouncilPositionFixture12004 = bool (*)(
    void *, const CouncilCandidatesEnvironmentV1 &, const void *,
    std::string_view, const void *&) noexcept;

struct CouncilCandidatesAccessV1 {
  void *context = nullptr;
  // Source frame supplies snapshot/date/revisions/player. This reader resolves
  // the requested task from the same frame, and does not trust a cached task.
  ck3_11906::CaptureCouncilCompositionStewardCandidatesFrameV1 capture_frame = nullptr;
  ck3_11906::IsCouncilCompositionStewardCandidatesMainThreadV1 is_main_thread = nullptr;
  CouncilCandidatesReadMemoryV1 read_memory = nullptr; // null = in-process read
  // Optional fixture callbacks. Accepted only when the environment explicitly
  // declares offline_fixture_function_overrides.
  CouncilCandidatesInitializeOverrideV1 initialize_vector = nullptr;
  CouncilCandidatesProduceOverrideV1 invoke_producer = nullptr;
  CouncilCandidatesReleaseOverrideV1 release_allocation = nullptr;
  // Only accepted with offline_fixture_function_overrides, like the vector callbacks.
  LookupCouncilPositionFixture12004 lookup_position = nullptr;
};

// Address calculation only. No process discovery, memory reads or native calls.
CouncilCandidatesEnvironmentV1 BindCouncilCandidates12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

bool ReadCouncilMemory12004(const CouncilCandidatesAccessV1 &access,
    const void *address, void *output, std::size_t size) noexcept;
bool ResolveCouncilCharacter12004(const CouncilCandidatesEnvironmentV1 &environment,
    const CouncilCandidatesAccessV1 &access, std::int32_t full_id,
    const void *&pointer) noexcept;
bool CaptureCouncilCandidatesFrame12004(
    const CouncilCandidatesEnvironmentV1 &environment,
    const CouncilCandidatesAccessV1 &access,
    CouncilCandidatesFrameV1 &output,
    std::string_view position_key = kCouncilCandidatesStewardPosition12004) noexcept;

// One application-main paused transaction: resolve -> GUI-mode native producer
// -> copy/round-trip IDs and native skill -> release -> recapture -> v1 projector.
// The private source output is optional and also zero-row on failure.
ck3_11906::ProjectCouncilCompositionCandidatesPublicResultV1
ReadCouncilCandidates12004(const CouncilCandidatesEnvironmentV1 &environment,
    const CouncilCandidatesAccessV1 &access,
    const CouncilCandidatesRequestV1 &request,
    game::CouncilCompositionCandidatesPublicV1 &output,
    game::CouncilCompositionStewardCandidatesV1 *private_source = nullptr) noexcept;

// Existing v1 wire shape with the actual 1.20.0.4 exact-build provenance.
std::string SerializeCouncilCandidates12004(
    const game::CouncilCompositionCandidatesPublicV1 &value);

} // namespace xar::ck3_12004
