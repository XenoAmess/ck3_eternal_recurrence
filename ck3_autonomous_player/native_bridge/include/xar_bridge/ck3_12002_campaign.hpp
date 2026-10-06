#pragma once

#include "xar_bridge/campaign_root_context_v1.hpp"
#include "xar_bridge/loaded_feature_manifest_v1.hpp"

// Stable DTO/access contracts are shared; all executable addresses and native
// layouts below belong only to the frozen 1.20.0.2 build.
namespace xar::ck3_12002 {


inline constexpr std::string_view kCampaignRootContextV1Capability =
    "game.command.query-campaign-root-context-v1";
inline constexpr std::string_view kCampaignRootContextV1Step =
    "query-campaign-root-context-v1";
inline constexpr std::string_view kCampaignRootContextV1GameVersion =
    "1.20.0.2";
inline constexpr std::string_view kCampaignRootContextV1ExecutableSha256 =
    "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
inline constexpr std::string_view kCampaignRootContextV1BackendId =
    "ck3-1.20.0.2-native-campaign-root-context-v1";

inline constexpr std::uintptr_t kCampaignRootGameStateSlotRva = 0x5C68C50;
inline constexpr std::uintptr_t kCampaignRootJominiStateSlotRva = 0x5C6A520;
inline constexpr std::uintptr_t kCampaignRootCharacterStorageSlotRva =
    0x5C67568;
inline constexpr std::uintptr_t kCampaignRootCharacterFallbackSlotRva =
    0x5C67570;
inline constexpr std::uintptr_t kCampaignRootLandedTitleStorageSlotRva =
    0x5D1DAF8;
inline constexpr std::uintptr_t kCampaignRootLandedTitleFallbackSlotRva =
    0x5D1DAE0;
inline constexpr std::uintptr_t kCampaignRootGovernmentFallbackSlotRva =
    0x5D1E2A8;
inline constexpr std::uintptr_t kCampaignRootGameRuleSelectionServiceSlotRva =
    0x5CB3D78;
inline constexpr std::uintptr_t kCampaignRootGameRuleTokenFallbackSlotRva =
    0x5D37A70;

inline constexpr std::uintptr_t kCampaignRootPrimaryTitleRva = 0x289DA30;
inline constexpr std::uintptr_t kCampaignRootCapitalProvinceRva = 0x28B1CD0;
inline constexpr std::uintptr_t kCampaignRootImmediateLiegeRva = 0x28BFC70;
inline constexpr std::uintptr_t kCampaignRootTopLiegeRva = 0x28BFDA0;
inline constexpr std::uintptr_t kCampaignRootGovernmentRva = 0x28C2E10;
inline constexpr std::uintptr_t kCampaignRootScriptIdentifierNameRva =
    0x3F4F900;



inline constexpr std::string_view kLoadedFeatureManifestV1Capability =
    "game.command.query-loaded-feature-manifest-v1";
inline constexpr std::string_view kLoadedFeatureManifestV1Step =
    "query-loaded-feature-manifest-v1";
inline constexpr std::string_view kLoadedFeatureManifestV1GameVersion =
    "1.20.0.2";
inline constexpr std::string_view kLoadedFeatureManifestV1ExecutableSha256 =
    "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
inline constexpr std::string_view kLoadedFeatureManifestV1BackendId =
    "ck3-1.20.0.2-native-loaded-feature-manifest-v1";

inline constexpr std::uintptr_t kLoadedFeatureRootSlotRva = 0x5CB87F8;
inline constexpr std::uintptr_t kLoadedFeatureScriptDlcSetRva = 0x5CC15E0;
inline constexpr std::uintptr_t kLoadedFeatureEnumTableRva = 0x47334C0;
inline constexpr std::uintptr_t kLoadedFeatureEnumTableEndRva = 0x4733570;
inline constexpr std::uintptr_t kLoadedFeatureScriptIdentifierNameRva =
    0x3F4F900;
inline constexpr std::size_t kLoadedFeatureNativeCount = 44;

using NativeCampaignRootCharacterResolverV1 = ck3_11906::NativeCampaignRootCharacterResolverV1;
using NativeCampaignRootMonthlyGoldIncomeV1 = ck3_11906::NativeCampaignRootMonthlyGoldIncomeV1;
using NativeCampaignRootCharacterFixedPointV1 = ck3_11906::NativeCampaignRootCharacterFixedPointV1;
using NativeCampaignRootCharacterInt32V1 = ck3_11906::NativeCampaignRootCharacterInt32V1;
using NativeCampaignRootProvinceHolderCharacterIdV1 = ck3_11906::NativeCampaignRootProvinceHolderCharacterIdV1;
using NativeCampaignRootCouncilValueProgressV1 = ck3_11906::NativeCampaignRootCouncilValueProgressV1;
using NativeCampaignRootScriptIdentifierNameV1 = ck3_11906::NativeCampaignRootScriptIdentifierNameV1;
using CampaignRootNativeEnvironmentV1 = ck3_11906::CampaignRootNativeEnvironmentV1;
using CaptureCampaignRootFrameV1 = ck3_11906::CaptureCampaignRootFrameV1;
using IsCampaignRootMainThreadV1 = ck3_11906::IsCampaignRootMainThreadV1;
using ReadCampaignRootMemoryV1 = ck3_11906::ReadCampaignRootMemoryV1;
using ReadCampaignRootStringV1 = ck3_11906::ReadCampaignRootStringV1;
using CampaignRootAccessV1 = ck3_11906::CampaignRootAccessV1;
using CampaignRootContextRequestV1 = ck3_11906::CampaignRootContextRequestV1;
using NativeLoadedFeatureScriptIdentifierNameV1 = ck3_11906::NativeLoadedFeatureScriptIdentifierNameV1;
using LoadedFeatureManifestNativeEnvironmentV1 = ck3_11906::LoadedFeatureManifestNativeEnvironmentV1;
using CaptureLoadedFeatureManifestFrameV1 = ck3_11906::CaptureLoadedFeatureManifestFrameV1;
using IsLoadedFeatureManifestMainThreadV1 = ck3_11906::IsLoadedFeatureManifestMainThreadV1;
using ReadLoadedFeatureManifestMemoryV1 = ck3_11906::ReadLoadedFeatureManifestMemoryV1;
using ReadLoadedFeatureManifestStringV1 = ck3_11906::ReadLoadedFeatureManifestStringV1;
using LoadedFeatureManifestAccessV1 = ck3_11906::LoadedFeatureManifestAccessV1;
using LoadedFeatureManifestRequestV1 = ck3_11906::LoadedFeatureManifestRequestV1;

struct HeldTitlePartitionFailure12002;

CampaignRootNativeEnvironmentV1 BindCampaignRootNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;
game::ReadCampaignRootContextResultV1 ReadCampaignRootContextV1(
    const CampaignRootNativeEnvironmentV1 &environment,
    const CampaignRootAccessV1 &access,
    const CampaignRootContextRequestV1 &request,
    game::CampaignRootContextV1 &output,
    HeldTitlePartitionFailure12002 *failure_diagnostic = nullptr) noexcept;
bool ReadCampaignRootTargetingFactionCountV1(
    const CampaignRootNativeEnvironmentV1 &environment,
    const CampaignRootAccessV1 &access,
    std::int32_t expected_player_character_id,
    std::int32_t &output) noexcept;
LoadedFeatureManifestNativeEnvironmentV1 BindLoadedFeatureManifestNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;
game::ReadLoadedFeatureManifestResultV1 ReadLoadedFeatureManifestV1(
    const LoadedFeatureManifestNativeEnvironmentV1 &environment,
    const LoadedFeatureManifestAccessV1 &access,
    const LoadedFeatureManifestRequestV1 &request,
    game::LoadedFeatureManifestV1 &output) noexcept;
std::string SerializeCampaignRootContextV1(const game::CampaignRootContextV1 &context);
std::string SerializeLoadedFeatureManifestV1(const game::LoadedFeatureManifestV1 &manifest);
} // namespace xar::ck3_12002
