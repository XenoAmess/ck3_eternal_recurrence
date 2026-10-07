#pragma once

#include "xar_bridge/ck3_12002_realm_law_source_adapter.hpp"
#include "xar_bridge/realm_law_12004_native.hpp"

#include <array>

namespace xar::ck3_12004 {

// Shared durable storage and copied value contracts; actual image admission,
// native address selection and source callbacks belong to the .4 factories.
using RealmLawCrownSource12004 = ck3_12002::RealmLawCrownSource12002;

// CLOSED-SUBSET05.json: actual .4 formal source operands.
inline constexpr std::uintptr_t kCrownPrimaryTitleRva12004 = 0x289DA10;
inline constexpr std::uintptr_t kCrownCharacterFallbackSlotRva12004 = 0x5C67570;
inline constexpr std::uintptr_t kCrownActorScopeRva12004 = 0xB17C70;
inline constexpr std::uintptr_t kCrownCompiledTriggerRva12004 = 0x372DF10;
inline constexpr std::uintptr_t kCrownScopeTailDestroyRva12004 = 0x889700;
inline constexpr std::uintptr_t kCrownScopeRowsDestroyRva12004 = 0x889780;

// FIELD12-LEDGER.json: full-ID held titles and successor baselines.
inline constexpr std::uintptr_t kCrownTitleStorageSlotRva12004 = 0x5D1DAF8;
inline constexpr std::uintptr_t kCrownTitleFallbackSlotRva12004 = 0x5D1DAE0;
inline constexpr std::size_t kCrownTitleIdentityOffset12004 = 0x10;
inline constexpr std::size_t kCrownCharacterLandOffset12004 = 0x1C0;
inline constexpr std::size_t kCrownHeldTitleDataOffset12004 = 0x1E0;
inline constexpr std::size_t kCrownHeldTitleCapacityOffset12004 = 0x1E8;
inline constexpr std::size_t kCrownHeldTitleCountOffset12004 = 0x1EC;
inline constexpr std::size_t kCrownTitleHolderOffset12004 = 0x128;
inline constexpr std::size_t kCrownSuccessorDataOffset12004 = 0x150;
inline constexpr std::size_t kCrownSuccessorCapacityOffset12004 = 0x158;
inline constexpr std::size_t kCrownSuccessorCountOffset12004 = 0x15C;

// FIELD14-CLOSED-LEDGER.json and RESOURCE14-SOURCE-SEAL.json.
inline constexpr std::size_t kCrownActorResourceExtensionOffset12004 = 0x1B0;
inline constexpr std::array<std::size_t, 5> kCrownResourceCurrencySlots12004{
    0, 1, 2, 4, 8};
inline constexpr std::array<std::uintptr_t, 5> kCrownResourceBalanceOffsets12004{
    0x100, 0x130, 0x110, 0x150, 0x170};

bridge::RealmLawNativeBinderOperationsV1
MakeRealmLawCrownSourceOperations12004() noexcept;

bool ResolveRealmLawCrownTarget12004(
    void *context, const bridge::RealmLawEnactSubmissionV1 &submission,
    bridge::RealmLawNativeEnactTargetLeaseV1 &output) noexcept;

bool BindRealmLawCrownSource12004(
    RealmLawCrownSource12004 &source,
    std::string_view source_signature_manifest_sha256,
    bridge::RealmLawNativeBinderStateV1 &state,
    bool offline_fixture = false) noexcept;

ck3_12002::private_law::RealmLawComponentBindings12002
BindRealmLawComponentsImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004
