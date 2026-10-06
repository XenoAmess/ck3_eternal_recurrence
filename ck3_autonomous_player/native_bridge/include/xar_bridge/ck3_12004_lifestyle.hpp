#pragma once
#if !defined(NOMINMAX)
#define NOMINMAX
#endif
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/player_lifestyle_formal_wire_v1.hpp"
namespace xar::ck3_12004::lifestyle {
// The wire/state/receipt DTOs remain the master contracts. Every bound native
// address below belongs to the exact 1.20 image; old native binders are unused.
using namespace xar::ck3_11906;
inline constexpr std::string_view kPlayerLifestyleSnapshotGameVersionV1 = "1.20.0.4";
inline constexpr std::string_view kPlayerLifestyleSelectionActionGameVersionV1 = "1.20.0.4";
inline constexpr std::string_view kPlayerLifestyleSelectionNativeAdapterGameVersionV1 = "1.20.0.4";
inline constexpr std::string_view kPlayerLifestyleSnapshotExecutableSha256V1 =
    ck3_12004::kExecutableSha256;
inline constexpr std::string_view kStockFocusLegalityExeSha256V1 =
    ck3_12004::kExecutableSha256;
inline constexpr std::string_view kStockPerkLegalityExeSha256V1 =
    ck3_12004::kExecutableSha256;
inline constexpr std::string_view kPlayerLifestyleSelectionActionExecutableSha256V1 =
    ck3_12004::kExecutableSha256;
inline constexpr std::string_view kPlayerLifestyleSelectionNativeAdapterExecutableSha256V1 =
    ck3_12004::kExecutableSha256;
inline constexpr std::uintptr_t kPlayerLifestyleCurrentFocusGetterRvaV1 = 0x29194B0;
inline constexpr std::uintptr_t kPlayerLifestyleCurrentLifestyleGetterRvaV1 = 0x29193C0;
inline constexpr std::uintptr_t kPlayerLifestylePerkPointsGetterRvaV1 = 0x2918BB0;
inline constexpr std::uintptr_t kPlayerLifestylePerkPointsUsedGetterRvaV1 = 0x2918C30;
inline constexpr std::uintptr_t kPlayerLifestyleXpGetterRvaV1 = 0x2918D30;
inline constexpr std::uintptr_t kPlayerLifestyleOwnedPerksGetterRvaV1 = 0x2919340;
inline constexpr std::uintptr_t kPlayerLifestyleCharacterPerkDatabaseRvaV1 = 0x8FCD40;
inline constexpr std::uintptr_t kPlayerLifestyleFocusFallbackSlotRvaV1 = 0x5D1E308;
inline constexpr std::size_t kPlayerLifestyleXpPerLevelOffsetV1 = 0x130;
inline constexpr std::size_t kPlayerLifestyleFocusLifestyleOffsetV1 = 0x7F8;
inline constexpr std::size_t kPlayerLifestylePerkLifestyleOffsetV1 = 0x440;
inline constexpr std::uintptr_t kPlayerLifestyleSelectionCommandManagerRvaV1 = 0x5CC1240;
inline constexpr std::uintptr_t kPlayerLifestyleSelectionPerkPrimaryVtableRvaV1 = 0x4760A00;
inline constexpr std::uintptr_t kPlayerLifestyleSelectionPerkSecondaryVtableRvaV1 = 0x47609D0;
inline constexpr std::uintptr_t kPlayerLifestyleSelectionPerkValidatorRvaV1 = 0x288AE00;
inline constexpr std::uintptr_t kPlayerLifestyleSelectionFocusPrimaryVtableRvaV1 = 0x4760B90;
inline constexpr std::uintptr_t kPlayerLifestyleSelectionFocusSecondaryVtableRvaV1 = 0x4760B60;
inline constexpr std::uintptr_t kPlayerLifestyleSelectionFocusValidatorRvaV1 = 0x288A870;
bool AssignPlayerLifestyleStableKey12004V1(std::string_view,
    game::PlayerLifestyleStableKeyV1 &) noexcept;
std::string_view PlayerLifestyleStableKeyView12004V1(
    const game::PlayerLifestyleStableKeyV1 &) noexcept;
bool ReadPlayerLifestyleMsvcStableKey12004V1(void *, ReadPlayerLifestyleMemoryV1,
    std::uintptr_t, game::PlayerLifestyleStableKeyV1 &) noexcept;
PlayerLifestyleSnapshotEnvironmentV1 BindPlayerLifestyleSnapshotEnvironment12004V1(
    std::uintptr_t, bool, std::string_view) noexcept;
game::ReadPlayerLifestyleSnapshotResultV1 ReadPlayerLifestyleSnapshot12004V1(
    const PlayerLifestyleSnapshotEnvironmentV1 &, const PlayerLifestyleSnapshotAccessV1 &,
    const PlayerLifestyleSnapshotRequestV1 &, game::PlayerLifestyleSnapshotV1 &) noexcept;
std::string_view PlayerLifestyleSnapshotFailureKey12004V1(
    game::PlayerLifestyleSnapshotFailureV1) noexcept;
std::string_view PlayerLifestyleCandidateCollectionFailureKey12004V1(
    game::PlayerLifestyleCandidateCollectionFailureV1) noexcept;
std::string SerializePlayerLifestyleSnapshot12004V1(const game::PlayerLifestyleSnapshotV1 &);
StockFocusLegalityEnvironmentV1 BindStockFocusLegalityEnvironment12004V1(
    std::uintptr_t, bool, std::string_view) noexcept;
StockFocusLegalityResultV1 ReadStockFocusLegality12004V1(
    const StockFocusLegalityEnvironmentV1 &, const StockFocusLegalityAccessV1 &) noexcept;
StockFocusLegalityResultV1 ReadStockFocusLegality12004V1(
    const StockFocusLegalityEnvironmentV1 &, const StockFocusLegalityAccessV1 &,
    std::string_view, std::string_view) noexcept;
std::string_view StockFocusLegalityStatusKey12004V1(StockFocusLegalityStatusV1) noexcept;
StockPerkLegalityEnvironmentV1 BindStockPerkLegalityEnvironment12004V1(
    std::uintptr_t, bool, std::string_view) noexcept;
StockPerkLegalityResultV1 ReadStockPerkLegality12004V1(
    const StockPerkLegalityEnvironmentV1 &, const StockPerkLegalityAccessV1 &) noexcept;
StockPerkLegalityResultV1 ReadStockPerkLegality12004V1(
    const StockPerkLegalityEnvironmentV1 &, const StockPerkLegalityAccessV1 &,
    std::string_view) noexcept;
std::string_view StockPerkLegalityStatusKey12004V1(StockPerkLegalityStatusV1) noexcept;
PlayerLifestyleSelectionNativeAdapterEnvironmentV1
BindPlayerLifestyleSelectionNativeAdapterEnvironment12004V1(
    std::uintptr_t, bool, std::string_view) noexcept;
bool PlayerLifestyleSelectionNativeAdapterEnvironmentReady12004V1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &) noexcept;
PlayerLifestyleSelectionActionEnvironmentV1
BindPlayerLifestyleSelectionActionEnvironmentFromNativeAdapter12004V1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &) noexcept;
PlayerLifestyleSelectionNativeDispatchResultV1
DispatchResolvedPlayerLifestylePerkNativeAdapter12004V1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &,
    const PlayerLifestyleSelectionNativeAdapterAccessV1 &, std::uint32_t,
    std::uintptr_t) noexcept;
PlayerLifestyleSelectionNativeDispatchResultV1
DispatchResolvedPlayerLifestyleFocusNativeAdapter12004V1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &,
    const PlayerLifestyleSelectionNativeAdapterAccessV1 &, std::uint32_t,
    std::uintptr_t) noexcept;
PlayerLifestyleSelectionActionEnvironmentV1 BindPlayerLifestyleSelectionActionEnvironment12004V1(
    std::uintptr_t, bool, std::string_view) noexcept;
game::PlayerLifestyleSelectionActionAckStatusV1 ExecutePlayerLifestyleSelectionAction12004V1(
    const PlayerLifestyleSelectionActionEnvironmentV1 &,
    const PlayerLifestyleSelectionActionAccessV1 &,
    const game::PlayerLifestyleSelectionActionRequestV1 &,
    game::PlayerLifestyleSelectionActionAckV1 &) noexcept;
game::PlayerLifestyleSelectionActionReceiptStatusV1 VerifyPlayerLifestyleSelectionActionReceipt12004V1(
    const PlayerLifestyleSelectionActionAccessV1 &,
    const game::PlayerLifestyleSelectionActionAckV1 &,
    game::PlayerLifestyleSelectionActionReceiptV1 &) noexcept;
std::string_view PlayerLifestyleSelectionActionFailureClassKey12004V1(
    game::PlayerLifestyleSelectionActionFailureClassV1) noexcept;
struct PlayerLifestyleBindings12004 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  std::string_view admitted_executable_sha256{};
  CoreBindings core{};
  PlayerLifestyleSnapshotEnvironmentV1 snapshot{};
  StockFocusLegalityEnvironmentV1 focus{};
  StockPerkLegalityEnvironmentV1 perk{};
  PlayerLifestyleSelectionNativeAdapterEnvironmentV1 selection{};
};
PlayerLifestyleBindings12004 BindPlayerLifestyleImage12004(
    std::uintptr_t module_base, std::string_view actual_executable_sha256) noexcept;
struct PlayerLifestyleFormalWireContext12004V1 :
    ck3_11906::PlayerLifestyleFormalWireContextV1 {
  PlayerLifestyleBindings12004 bindings12004{};
  ck3_12002::QueryMailboxEnvelope envelope{};
};
bool InitializePlayerLifestyleFormalWireContext12004V1(
    PlayerLifestyleFormalWireContext12004V1 &, const PlayerLifestyleBindings12004 &,
    const game::Snapshot &, std::uint64_t, std::string_view,
    PlayerLifestyleFormalWireModeV1) noexcept;
bool ExecutePlayerLifestyleMailbox12004(
    void *, const MainThreadExecutionStampV1 &) noexcept;
} // namespace xar::ck3_12004::lifestyle
