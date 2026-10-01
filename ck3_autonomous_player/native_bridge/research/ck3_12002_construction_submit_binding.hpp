#pragma once

#include "../src/domain_construction_application_main_runtime_v1.hpp"

#include <cstddef>
#include <cstdint>

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kConstructionBuildingPrimaryVtableRva =
    0x476C540U;
inline constexpr std::uintptr_t kConstructionBuildingSecondaryVtableRva =
    0x476C5D8U;
inline constexpr std::uintptr_t kConstructionBuildingValidatorRva =
    0x2982440U;
inline constexpr std::uintptr_t kConstructionBuildingFinalLegalityRva =
    0x2C77D50U;
inline constexpr std::uintptr_t kConstructionBuildingMaterializeRva =
    0x2985DC0U;
inline constexpr std::uintptr_t kConstructionReceiverRva = 0x37F06F0U;
inline constexpr std::uintptr_t kConstructionReceiverSingletonRva =
    0x5CC1240U;
inline constexpr std::uintptr_t kConstructionCommandPhaseFlagsRva =
    0x5CC14D0U;
inline constexpr std::uint32_t kConstructionReceiverFlags = 7U;
inline constexpr std::size_t kConstructionNativeCommandBytes = 0x30U;

// Reuse the pointer-free application-main DTOs. Their namespace records their
// introduction version, not the executable selected by this binding.
using ConstructionNativeCallsV1 =
    ck3::shared::DomainConstructionExactNativeCallsV1;
using ConstructionActionStateV1 =
    ck3::shared::PlayerWorldBuildingDirectActionStateV1;
using ConstructionActionRequestV1 =
    ck3::shared::PlayerWorldBuildingDirectActionRequestV1;

// Only CAddConstructionCommand is mapped here. validate_holding is null:
// the old adapter's "new_holding" branch actually builds a domicile building.
[[nodiscard]] ConstructionNativeCallsV1
BindCurrentProcessDomainConstructionExactNativeCallsV1(
    std::uintptr_t module_base) noexcept;

[[nodiscard]] bool SubmitPlayerWorldBuildingDirectActionV1(
    ConstructionActionStateV1& state,
    const ConstructionActionRequestV1& request,
    const ck3_11906::MainThreadExecutionStampV1& stamp) noexcept;

[[nodiscard]] bool ObservePlayerWorldBuildingDirectActionReceiptV1(
    ConstructionActionStateV1& state,
    const ck3_11906::PlayerWorldBuildingSourceResultV1& fresh,
    std::uint64_t fresh_proof_epoch) noexcept;

}  // namespace xar::ck3_12002
