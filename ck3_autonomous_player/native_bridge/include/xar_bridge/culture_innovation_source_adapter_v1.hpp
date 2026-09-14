#pragma once

#include "xar_bridge/culture_innovation_snapshot_v1.hpp"

#include <cstddef>
#include <cstdint>

namespace xar::ck3_11906 {

enum class CultureInnovationSourceAdapterFailureV1 : std::uint32_t {
  none = 0,
  invalid_context,
  native_read_failed,
  player_identity_invalid,
  player_identity_round_trip_failed,
  culture_handle_invalid,
  culture_store_invalid,
  culture_identity_round_trip_failed,
  culture_head_handle_invalid,
  culture_head_identity_round_trip_failed,
  era_collection_invalid,
  era_definition_invalid,
  era_progress_invalid,
  innovation_collection_invalid,
  innovation_definition_invalid,
  innovation_definition_round_trip_failed,
  innovation_metadata_unavailable,
  innovation_progress_invalid,
  native_predicate_unavailable,
};

using ReadCultureInnovationMemoryV1 = bool (*)(
    void *context, std::uintptr_t address, void *output,
    std::size_t size) noexcept;
using CanCultureInnovationGainProgressV1 = bool (*)(
    void *context, std::uintptr_t module_base,
    std::uintptr_t innovation_state, bool &output) noexcept;
using CanSetCultureInnovationFascinationV1 = bool (*)(
    void *context, std::uintptr_t module_base,
    std::uintptr_t innovation_definition, std::uintptr_t culture,
    bool &output) noexcept;

struct CultureInnovationSourceNativeAccessV1 {
  void *context = nullptr;
  ReadCultureInnovationMemoryV1 read_memory = nullptr;
  CanCultureInnovationGainProgressV1 can_gain_progress = nullptr;
  CanSetCultureInnovationFascinationV1 can_be_fascination = nullptr;
};

struct CultureInnovationSourceAdapterContextV1 {
  std::uintptr_t module_base = 0;
  CultureInnovationSourceNativeAccessV1 native{};
  CultureInnovationSourceAdapterFailureV1 last_failure =
      CultureInnovationSourceAdapterFailureV1::none;
};

// These offsets are private exact-build implementation details. The adapter
// copies all observed values into the pointer-free CULTURE2 sample.
inline constexpr std::uintptr_t kCultureSourceCharacterStoreSlotV1 =
    0x570C130;
inline constexpr std::uintptr_t kCultureSourceCharacterFallbackSlotV1 =
    0x570C138;
inline constexpr std::uintptr_t kCultureSourceCultureStoreSlotV1 = 0x570CB80;
inline constexpr std::uintptr_t kCultureSourceCultureFallbackSlotV1 =
    0x570CB78;
inline constexpr std::uintptr_t kCultureSourceInnovationFallbackSlotV1 =
    0x57C04E0;
inline constexpr std::size_t kCultureSourceCharacterIdentityOffsetV1 = 0x18;
inline constexpr std::size_t kCultureSourceCharacterCultureIdOffsetV1 = 0xB0;
inline constexpr std::size_t kCultureSourceCultureIdentityOffsetV1 = 0x10;
inline constexpr std::size_t kCultureSourceEraDefinitionOffsetV1 = 0x08;
inline constexpr std::size_t kCultureSourceEraCultureOffsetV1 = 0x20;
inline constexpr std::size_t kCultureSourceEraProgressOffsetV1 = 0x28;
inline constexpr std::size_t kCultureSourceDefinitionIndexOffsetV1 = 0x10;
inline constexpr std::size_t kCultureSourceDefinitionStableKeyOffsetV1 = 0x18;
inline constexpr std::size_t kCultureSourceInnovationEraDefinitionOffsetV1 =
    0x200;
inline constexpr std::size_t kCultureSourceActiveInnovationVectorOffsetV1 =
    0x758;
inline constexpr std::size_t kCultureSourceActiveInnovationCountOffsetV1 =
    0x764;
inline constexpr std::uintptr_t kCultureSourceCanGainProgressRvaV1 =
    0x2D4DD80;
inline constexpr std::uintptr_t kCultureSourceCanBeFascinationRvaV1 =
    0x2926310;

CultureInnovationSourceNativeAccessV1
DirectCultureInnovationSourceNativeAccessV1() noexcept;

CultureInnovationSourceAdapterFailureV1
ReadExactBuildCultureInnovationSourceV1(
    CultureInnovationSourceAdapterContextV1 &context,
    std::uintptr_t played_character,
    CultureInnovationSourceSampleV1 &output) noexcept;

// Signature-compatible adapter for CultureInnovationSnapshotAccessV1.
bool ReadExactBuildCultureInnovationNativeSourceV1(
    void *context, std::uintptr_t played_character,
    CultureInnovationSourceSampleV1 &output) noexcept;

std::string_view CultureInnovationSourceAdapterFailureKeyV1(
    CultureInnovationSourceAdapterFailureV1 failure) noexcept;

} // namespace xar::ck3_11906
