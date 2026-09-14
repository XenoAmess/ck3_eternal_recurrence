#pragma once

#include "xar_bridge/major_decision_found_kingdom_source_adapter_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view
    kMajorDecisionFoundKingdomNativeBinderGameVersionV1 = "1.19.0.6";

inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomDecisionDatabaseSlotRvaV1 = 0x570C7B0;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomCharacterStorageSlotRvaV1 = 0x570C130;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomCharacterFallbackSlotRvaV1 = 0x570C138;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomNameHashRvaV1 = 0x3B8B000;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomDatabaseLookupRvaV1 = 0x0BFF6C0;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomRootScopeConstructorRvaV1 = 0x081F190;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomRootScopeNamedRowsDestructorRvaV1 = 0x081E860;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomRootScopeTailDestructorRvaV1 = 0x081E900;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomRootScopeRowsDestructorRvaV1 = 0x081E980;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomTriggerEvaluatorRvaV1 = 0x334C510;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomCostSelectorRvaV1 = 0x1354E00;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomCostEvaluatorRvaV1 = 0x2CDB740;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomAffordabilityEvaluatorRvaV1 = 0x2CD9C70;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomCanTakeEvaluatorRvaV1 = 0x2CD2260;

inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomDecisionDatabaseVtableRvaV1 = 0x43DC020;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomDecisionDefinitionVtableRvaV1 = 0x440B8E0;
inline constexpr std::size_t kMajorDecisionFoundKingdomIsShownOffsetV1 =
    0x690;
inline constexpr std::size_t kMajorDecisionFoundKingdomIsValidOffsetV1 =
    0x770;
inline constexpr std::size_t
    kMajorDecisionFoundKingdomIsValidShowingFailuresOnlyOffsetV1 = 0x850;

// The native cost evaluator writes the stock ten-resource vector. These are
// the exact positions selected by the resource-id dispatcher at RVA 0x2CDBA80.
inline constexpr std::size_t kMajorDecisionFoundKingdomGoldCostIndexV1 = 0;
inline constexpr std::size_t kMajorDecisionFoundKingdomPrestigeCostIndexV1 = 1;
inline constexpr std::size_t kMajorDecisionFoundKingdomPietyCostIndexV1 = 2;
inline constexpr std::size_t kMajorDecisionFoundKingdomTreasuryCostIndexV1 = 6;

struct MajorDecisionFoundKingdomNativeSignatureV1 {
  std::uintptr_t rva = 0;
  std::array<std::uint8_t, 16> bytes{};
  std::size_t size = 0;
};

struct MajorDecisionFoundKingdomNativeSlotV1 {
  std::uintptr_t slot_rva = 0;
  std::uintptr_t function_rva = 0;
};

inline constexpr std::array<MajorDecisionFoundKingdomNativeSignatureV1, 11>
    kMajorDecisionFoundKingdomNativeSignaturesV1{{
        {kMajorDecisionFoundKingdomNameHashRvaV1,
         {0x89, 0x4C, 0x24, 0x08, 0x53, 0x48, 0x83, 0xEC,
          0x20, 0x33, 0xC0, 0x48, 0x8D, 0x4C, 0x24, 0x30},
         16},
        {kMajorDecisionFoundKingdomDatabaseLookupRvaV1,
         {0x48, 0x89, 0x5C, 0x24, 0x08, 0x45, 0x33, 0xC0,
          0x48, 0x63, 0xDA, 0x44, 0x38, 0x81, 0xF8, 0x0E},
         16},
        {kMajorDecisionFoundKingdomRootScopeConstructorRvaV1,
         {0x48, 0x89, 0x5C, 0x24, 0x08, 0x57, 0x48, 0x83,
          0xEC, 0x20, 0x33, 0xFF, 0xC7, 0x41, 0x10, 0xFF},
         16},
        {kMajorDecisionFoundKingdomRootScopeNamedRowsDestructorRvaV1,
         {0x48, 0x89, 0x74, 0x24, 0x10, 0x57, 0x48, 0x83,
          0xEC, 0x20, 0x8B, 0x79, 0x0C, 0x48, 0x8B, 0xF1},
         16},
        {kMajorDecisionFoundKingdomRootScopeTailDestructorRvaV1,
         {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74,
          0x24, 0x10, 0x57, 0x48, 0x83, 0xEC, 0x20, 0x33},
         16},
        {kMajorDecisionFoundKingdomRootScopeRowsDestructorRvaV1,
         {0x48, 0x89, 0x74, 0x24, 0x10, 0x57, 0x48, 0x83,
          0xEC, 0x20, 0x8B, 0x79, 0x0C, 0x48, 0x8B, 0xF1},
         16},
        {kMajorDecisionFoundKingdomTriggerEvaluatorRvaV1,
         {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74,
          0x24, 0x10, 0x57, 0x48, 0x81, 0xEC, 0x30, 0x04},
         16},
        {kMajorDecisionFoundKingdomCostSelectorRvaV1,
         {0x48, 0x8D, 0x81, 0x78, 0x16, 0x00, 0x00, 0x4C,
          0x8B, 0xC1, 0x48, 0x8D, 0x91, 0xC8, 0x20, 0x00},
         16},
        {kMajorDecisionFoundKingdomCostEvaluatorRvaV1,
         {0x40, 0x53, 0x48, 0x83, 0xEC, 0x70, 0x49, 0x8B,
          0xD8, 0x0F, 0x57, 0xC0, 0x0F, 0x11, 0x44, 0x24},
         16},
        {kMajorDecisionFoundKingdomAffordabilityEvaluatorRvaV1,
         {0x48, 0x8B, 0xC4, 0x48, 0x89, 0x58, 0x08, 0x57,
          0x48, 0x81, 0xEC, 0xC0, 0x00, 0x00, 0x00, 0x49},
         16},
        {kMajorDecisionFoundKingdomCanTakeEvaluatorRvaV1,
         {0x48, 0x89, 0x5C, 0x24, 0x10, 0x4C, 0x89, 0x4C,
          0x24, 0x20, 0x4C, 0x89, 0x44, 0x24, 0x18, 0x55},
         16},
    }};

// Both runtime objects must still expose the frozen exact-build virtual
// surface. The binder never invokes these slots; they are identity gates.
inline constexpr std::array<MajorDecisionFoundKingdomNativeSlotV1, 6>
    kMajorDecisionFoundKingdomNativeSlotsV1{{
        {kMajorDecisionFoundKingdomDecisionDatabaseVtableRvaV1 + 0x00,
         0x2A63150},
        {kMajorDecisionFoundKingdomDecisionDatabaseVtableRvaV1 + 0x08,
         0x29F3480},
        {kMajorDecisionFoundKingdomDecisionDatabaseVtableRvaV1 + 0x10,
         0x2CD3200},
        {kMajorDecisionFoundKingdomDecisionDefinitionVtableRvaV1 + 0x00,
         0x07E9220},
        {kMajorDecisionFoundKingdomDecisionDefinitionVtableRvaV1 + 0x08,
         0x07E6490},
        {kMajorDecisionFoundKingdomDecisionDefinitionVtableRvaV1 + 0x10,
         0x07E6490},
    }};

using MajorDecisionFoundKingdomNativeReadMemoryV1 = bool (*)(
    void *context, const void *address, void *output,
    std::size_t size) noexcept;
using MajorDecisionFoundKingdomNativeResolvePlayerV1 = std::uintptr_t (*)(
    void *context, std::uintptr_t module_base,
    std::int32_t character_id) noexcept;
using MajorDecisionFoundKingdomNativeHashNameV1 = bool (*)(
    void *context, std::uintptr_t module_base, std::string_view name,
    std::uint32_t &output) noexcept;
using MajorDecisionFoundKingdomNativeLookupDefinitionV1 = std::uintptr_t (*)(
    void *context, std::uintptr_t module_base, std::uintptr_t database,
    std::uint32_t name_hash) noexcept;
using MajorDecisionFoundKingdomNativeEvaluateTriggerV1 = bool (*)(
    void *context, std::uintptr_t module_base, std::uintptr_t definition,
    std::size_t trigger_offset, std::int32_t character_id,
    bool &output) noexcept;
using MajorDecisionFoundKingdomNativeEvaluateCostV1 = bool (*)(
    void *context, std::uintptr_t module_base, std::uintptr_t definition,
    std::int32_t character_id,
    MajorDecisionFoundKingdomSourceCostV1 &output) noexcept;
using MajorDecisionFoundKingdomNativeEvaluateBoolV1 = bool (*)(
    void *context, std::uintptr_t module_base, std::uintptr_t definition,
    std::uintptr_t player, std::int32_t character_id,
    bool &output) noexcept;

struct MajorDecisionFoundKingdomNativeOperationsV1 {
  MajorDecisionFoundKingdomNativeReadMemoryV1 read_memory = nullptr;
  MajorDecisionFoundKingdomNativeResolvePlayerV1 resolve_player = nullptr;
  MajorDecisionFoundKingdomNativeHashNameV1 hash_name = nullptr;
  MajorDecisionFoundKingdomNativeLookupDefinitionV1 lookup_definition =
      nullptr;
  MajorDecisionFoundKingdomNativeEvaluateTriggerV1 evaluate_trigger = nullptr;
  MajorDecisionFoundKingdomNativeEvaluateCostV1 evaluate_cost = nullptr;
  MajorDecisionFoundKingdomNativeEvaluateBoolV1 evaluate_affordability =
      nullptr;
  MajorDecisionFoundKingdomNativeEvaluateBoolV1 evaluate_can_take = nullptr;
};

struct MajorDecisionFoundKingdomNativeEnvironmentV1 {
  bool binding_enabled = false;
  bool exact_build_admitted = false;
  std::string_view admitted_game_version{};
  std::string_view admitted_executable_sha256{};
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  void *operation_context = nullptr;
  MajorDecisionFoundKingdomNativeOperationsV1 operations{};
};

struct MajorDecisionFoundKingdomNativeBindingStateV1 {
  std::uintptr_t module_base = 0;
  void *operation_context = nullptr;
  MajorDecisionFoundKingdomNativeOperationsV1 operations{};
  void *upstream_context = nullptr;
  CaptureMajorDecisionFoundKingdomSourceFrameV1 upstream_capture_frame =
      nullptr;
  bool attached = false;
};

// Installs private read-only callbacks into DECISION3. It publishes no effect
// preview and exposes no command or decision-execution callback.
bool BindMajorDecisionFoundKingdomNativeV1(
    const MajorDecisionFoundKingdomNativeEnvironmentV1 &environment,
    MajorDecisionFoundKingdomNativeBindingStateV1 &state,
    MajorDecisionFoundKingdomSourceAccessV1 &access) noexcept;

} // namespace xar::bridge
