#pragma once

#if !defined(NOMINMAX)
#define NOMINMAX
#endif

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/player_lifestyle_formal_wire_v1.hpp"

namespace xar::ck3_12002::lifestyle {

// The wire/state/receipt DTOs remain the master contracts. Every bound native
// address below belongs to the exact 1.20 image; old native binders are unused.
using namespace xar::ck3_11906;

inline constexpr std::string_view kPlayerLifestyleSnapshotGameVersionV1 = "1.20.0.2";
inline constexpr std::string_view kPlayerLifestyleSelectionActionGameVersionV1 = "1.20.0.2";
inline constexpr std::string_view kPlayerLifestyleSelectionNativeAdapterGameVersionV1 = "1.20.0.2";

inline constexpr std::string_view kPlayerLifestyleSnapshotExecutableSha256V1 =
    ck3_12002::kExecutableSha256;
inline constexpr std::string_view kStockFocusLegalityExeSha256V1 =
    ck3_12002::kExecutableSha256;
inline constexpr std::string_view kStockPerkLegalityExeSha256V1 =
    ck3_12002::kExecutableSha256;
inline constexpr std::string_view kPlayerLifestyleSelectionActionExecutableSha256V1 =
    ck3_12002::kExecutableSha256;
inline constexpr std::string_view kPlayerLifestyleSelectionNativeAdapterExecutableSha256V1 =
    ck3_12002::kExecutableSha256;
inline constexpr std::uintptr_t kPlayerLifestyleCurrentFocusGetterRvaV1 = 0x29194D0;
inline constexpr std::uintptr_t kPlayerLifestyleCurrentLifestyleGetterRvaV1 = 0x29193E0;
inline constexpr std::uintptr_t kPlayerLifestylePerkPointsGetterRvaV1 = 0x2918BD0;
inline constexpr std::uintptr_t kPlayerLifestylePerkPointsUsedGetterRvaV1 = 0x2918C50;
inline constexpr std::uintptr_t kPlayerLifestyleXpGetterRvaV1 = 0x2918D50;
inline constexpr std::uintptr_t kPlayerLifestyleOwnedPerksGetterRvaV1 = 0x2919360;
inline constexpr std::uintptr_t kPlayerLifestyleHasPerkGetterRvaV1 = 0x2919070;
inline constexpr std::uintptr_t kPlayerLifestyleCharacterPerkDatabaseRvaV1 = 0x8FCD40;
inline constexpr std::uintptr_t kPlayerLifestyleFocusFallbackSlotRvaV1 = 0x5D1E308;
inline constexpr std::size_t kPlayerLifestyleXpPerLevelOffsetV1 = 0x130;
inline constexpr std::size_t kPlayerLifestyleFocusLifestyleOffsetV1 = 0x7F8;
inline constexpr std::size_t kPlayerLifestylePerkLifestyleOffsetV1 = 0x440;
inline constexpr std::uintptr_t kPlayerLifestyleSelectionCommandManagerRvaV1 = 0x5CC1240;
inline constexpr std::uintptr_t kPlayerLifestyleSelectionPerkPrimaryVtableRvaV1 = 0x47609F0;
inline constexpr std::uintptr_t kPlayerLifestyleSelectionPerkSecondaryVtableRvaV1 = 0x47609C0;
inline constexpr std::uintptr_t kPlayerLifestyleSelectionPerkValidatorRvaV1 = 0x288AE20;
inline constexpr std::uintptr_t kPlayerLifestyleSelectionFocusPrimaryVtableRvaV1 = 0x4760B80;
inline constexpr std::uintptr_t kPlayerLifestyleSelectionFocusSecondaryVtableRvaV1 = 0x4760B50;
inline constexpr std::uintptr_t kPlayerLifestyleSelectionFocusValidatorRvaV1 = 0x288A890;

bool AssignPlayerLifestyleStableKey12002V1(std::string_view,
    game::PlayerLifestyleStableKeyV1 &) noexcept;
std::string_view PlayerLifestyleStableKeyView12002V1(
    const game::PlayerLifestyleStableKeyV1 &) noexcept;
bool ReadPlayerLifestyleMsvcStableKey12002V1(void *, ReadPlayerLifestyleMemoryV1,
    std::uintptr_t, game::PlayerLifestyleStableKeyV1 &) noexcept;
PlayerLifestyleSnapshotEnvironmentV1 BindPlayerLifestyleSnapshotEnvironment12002V1(
    std::uintptr_t, bool, std::string_view) noexcept;
game::ReadPlayerLifestyleSnapshotResultV1 ReadPlayerLifestyleSnapshot12002V1(
    const PlayerLifestyleSnapshotEnvironmentV1 &, const PlayerLifestyleSnapshotAccessV1 &,
    const PlayerLifestyleSnapshotRequestV1 &, game::PlayerLifestyleSnapshotV1 &) noexcept;
std::string_view PlayerLifestyleSnapshotFailureKey12002V1(
    game::PlayerLifestyleSnapshotFailureV1) noexcept;
std::string_view PlayerLifestyleCandidateCollectionFailureKey12002V1(
    game::PlayerLifestyleCandidateCollectionFailureV1) noexcept;
std::string SerializePlayerLifestyleSnapshot12002V1(const game::PlayerLifestyleSnapshotV1 &);

StockFocusLegalityEnvironmentV1 BindStockFocusLegalityEnvironment12002V1(
    std::uintptr_t, bool, std::string_view) noexcept;
StockFocusLegalityResultV1 ReadStockFocusLegality12002V1(
    const StockFocusLegalityEnvironmentV1 &, const StockFocusLegalityAccessV1 &) noexcept;
StockFocusLegalityResultV1 ReadStockFocusLegality12002V1(
    const StockFocusLegalityEnvironmentV1 &, const StockFocusLegalityAccessV1 &,
    std::string_view, std::string_view) noexcept;
std::string_view StockFocusLegalityStatusKey12002V1(StockFocusLegalityStatusV1) noexcept;
StockPerkLegalityEnvironmentV1 BindStockPerkLegalityEnvironment12002V1(
    std::uintptr_t, bool, std::string_view) noexcept;
StockPerkLegalityResultV1 ReadStockPerkLegality12002V1(
    const StockPerkLegalityEnvironmentV1 &, const StockPerkLegalityAccessV1 &) noexcept;
StockPerkLegalityResultV1 ReadStockPerkLegality12002V1(
    const StockPerkLegalityEnvironmentV1 &, const StockPerkLegalityAccessV1 &,
    std::string_view) noexcept;
std::string_view StockPerkLegalityStatusKey12002V1(StockPerkLegalityStatusV1) noexcept;

PlayerLifestyleSelectionNativeAdapterEnvironmentV1
BindPlayerLifestyleSelectionNativeAdapterEnvironment12002V1(
    std::uintptr_t, bool, std::string_view) noexcept;
bool PlayerLifestyleSelectionNativeAdapterEnvironmentReady12002V1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &) noexcept;
PlayerLifestyleSelectionActionEnvironmentV1
BindPlayerLifestyleSelectionActionEnvironmentFromNativeAdapter12002V1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &) noexcept;
PlayerLifestyleSelectionNativeDispatchResultV1
DispatchResolvedPlayerLifestylePerkNativeAdapter12002V1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &,
    const PlayerLifestyleSelectionNativeAdapterAccessV1 &, std::uint32_t,
    std::uintptr_t) noexcept;
PlayerLifestyleSelectionNativeDispatchResultV1
DispatchResolvedPlayerLifestyleFocusNativeAdapter12002V1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &,
    const PlayerLifestyleSelectionNativeAdapterAccessV1 &, std::uint32_t,
    std::uintptr_t) noexcept;
PlayerLifestyleSelectionActionEnvironmentV1 BindPlayerLifestyleSelectionActionEnvironment12002V1(
    std::uintptr_t, bool, std::string_view) noexcept;
game::PlayerLifestyleSelectionActionAckStatusV1 ExecutePlayerLifestyleSelectionAction12002V1(
    const PlayerLifestyleSelectionActionEnvironmentV1 &,
    const PlayerLifestyleSelectionActionAccessV1 &,
    const game::PlayerLifestyleSelectionActionRequestV1 &,
    game::PlayerLifestyleSelectionActionAckV1 &) noexcept;
game::PlayerLifestyleSelectionActionReceiptStatusV1 VerifyPlayerLifestyleSelectionActionReceipt12002V1(
    const PlayerLifestyleSelectionActionAccessV1 &,
    const game::PlayerLifestyleSelectionActionAckV1 &,
    game::PlayerLifestyleSelectionActionReceiptV1 &) noexcept;
std::string_view PlayerLifestyleSelectionActionFailureClassKey12002V1(
    game::PlayerLifestyleSelectionActionFailureClassV1) noexcept;

struct PlayerLifestyleFormalWireContext12002V1 :
    ck3_11906::PlayerLifestyleFormalWireContextV1 {
  CoreBindings core_bindings12002{};
};

bool InitializePlayerLifestyleFormalWireContext12002V1(
    PlayerLifestyleFormalWireContext12002V1 &, const CoreBindings &,
    const game::Snapshot &, std::uint64_t, std::string_view,
    PlayerLifestyleFormalWireModeV1) noexcept;
bool ExecutePlayerLifestyleFormalWireMailbox12002V1(
    void *, const MainThreadExecutionStampV1 &) noexcept;

} // namespace xar::ck3_12002::lifestyle
