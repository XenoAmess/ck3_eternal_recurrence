#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/battle_terminal_journal_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdio>
#include <cstring>
#include <limits>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace xar::ck3_11906 {
namespace {

thread_local std::string_view
    g_last_war_termination_exit_terms_unavailable_reason{};
thread_local std::string_view g_last_war_exit_preview_unavailable_reason{};
thread_local std::array<char, 4096> g_war_exit_preview_diagnostic_buffer{};
thread_local std::uintptr_t g_war_exit_loaded_root_vtable_rva = 0;
thread_local std::int32_t g_war_exit_loaded_root_selector_count = -1;
thread_local std::uintptr_t g_war_exit_loaded_default_child_vtable_rva = 0;
thread_local std::int32_t g_war_exit_loaded_root_capacity = -1;
thread_local std::int32_t g_war_exit_loaded_root_count = -1;
thread_local std::int32_t g_war_exit_loaded_hidden_count = -1;
thread_local std::int32_t g_war_exit_loaded_hidden_index = -1;
thread_local std::int32_t g_war_exit_loaded_hidden_capacity = -1;
thread_local std::int32_t g_war_exit_loaded_hidden_child_count = -1;
thread_local std::uintptr_t
    g_war_exit_loaded_hidden_child0_vtable_rva = 0;
constexpr std::size_t kMaximumWarExitDiagnosticRootChildren = 16;
thread_local std::array<std::uintptr_t,
                        kMaximumWarExitDiagnosticRootChildren>
    g_war_exit_loaded_root_child_pointers{};
thread_local std::array<std::uintptr_t,
                        kMaximumWarExitDiagnosticRootChildren>
    g_war_exit_loaded_root_child_vtable_rvas{};

void SetWarExitPreviewUnavailableReason(std::string_view reason) noexcept {
  if (g_last_war_exit_preview_unavailable_reason.empty()) {
    g_last_war_exit_preview_unavailable_reason = reason;
  }
}

constexpr std::uintptr_t kGameStateSlotRva = 0x570E068;
constexpr std::uintptr_t kJominiStateSlotRva = 0x570F7B8;
constexpr std::uintptr_t kCommandManagerRva = 0x57621F0;
constexpr std::uintptr_t kPausePrimaryVtableRva = 0x432F1C8;
constexpr std::uintptr_t kPauseSecondaryVtableRva = 0x432F198;
constexpr std::uintptr_t kSetSpeedPrimaryVtableRva = 0x432F3F0;
constexpr std::uintptr_t kSetSpeedSecondaryVtableRva = 0x432F260;
constexpr std::uintptr_t kSelectEventOptionPrimaryVtableRva = 0x4335240;
constexpr std::uintptr_t kSelectEventOptionSecondaryVtableRva = 0x4335210;
constexpr std::uintptr_t kIngameInterfaceIdlerVtableRva = 0x40B1D30;
constexpr std::uintptr_t kEventWindowPrimaryVtableRva = 0x417F758;
constexpr std::uintptr_t kSchemeTypePrimaryVtableRva = 0x44081E8;
constexpr std::uintptr_t kAutoSavePrimaryVtableRva = 0x40AABE8;
constexpr std::uintptr_t kAutoSaveSecondaryVtableRva = 0x40AAC80;
constexpr std::uintptr_t kReplyCharacterInteractionPrimaryVtableRva =
    0x4082930;
constexpr std::uintptr_t kReplyCharacterInteractionSecondaryVtableRva =
    0x4082900;
constexpr std::uintptr_t kPendingCharacterInteractionStorageSlotRva =
    0x57BF1C8;
constexpr std::uintptr_t kCharacterStorageSlotRva = 0x570C130;
constexpr std::uintptr_t kArmyStorageSlotRva = 0x570CC80;
constexpr std::uintptr_t kArmyInternalStorageSlotRva = 0x570C730;
constexpr std::uintptr_t kRegimentStorageSlotRva = 0x57BF4C8;
constexpr std::uintptr_t kCombatStorageSlotRva = 0x570C758;
constexpr std::uintptr_t kBattleResultFallbackSlotRva = 0x57C0320;
constexpr std::uintptr_t kBattleResultStorageSlotRva = 0x57C0328;
constexpr std::uintptr_t kAiWarCoordinatorFallbackSlotRva = 0x57C0798;
constexpr std::uintptr_t kAiWarCoordinatorStorageSlotRva = 0x57C07A8;
constexpr std::uintptr_t kSiegeStorageSlotRva = 0x57BF1B8;
constexpr std::uintptr_t kContactGameModeSlotRva = 0x576CC68;
constexpr std::uintptr_t kTraitDatabaseSlotRva = 0x570C0F8;
constexpr std::uintptr_t kSchemeTypeDatabaseSlotRva = 0x570BD98;
constexpr std::uintptr_t kSchemeTypeFallbackSlotRva = 0x570CB58;
constexpr std::uintptr_t kGlobalVariableContainerAccessorSlotRva =
    0x570F750;
constexpr std::uintptr_t kRaiseTroopsPrimaryVtableRva = 0x41226D8;
constexpr std::uintptr_t kRaiseTroopsSecondaryVtableRva = 0x41226A8;
constexpr std::uintptr_t kMoveArmyPrimaryVtableRva = 0x432BF18;
constexpr std::uintptr_t kMoveArmySecondaryVtableRva = 0x432BFB0;
constexpr std::uintptr_t kDisbandArmyPrimaryVtableRva = 0x432BFE0;
constexpr std::uintptr_t kDisbandArmySecondaryVtableRva = 0x432C078;
constexpr std::uintptr_t kSplitArmyHalfPrimaryVtableRva = 0x432D5C0;
constexpr std::uintptr_t kSplitArmyHalfSecondaryVtableRva = 0x432D658;
constexpr std::uintptr_t kMergeArmiesPrimaryVtableRva = 0x432D3C8;
constexpr std::uintptr_t kMergeArmiesSecondaryVtableRva = 0x432D398;
constexpr std::uintptr_t kStartAssaultPrimaryVtableRva = 0x432CB30;
constexpr std::uintptr_t kStartAssaultSecondaryVtableRva = 0x432CB00;
constexpr std::uintptr_t kStopAssaultPrimaryVtableRva = 0x432CBC8;
constexpr std::uintptr_t kStopAssaultSecondaryVtableRva = 0x432CA08;
constexpr std::uintptr_t kSendCharacterInteractionPrimaryVtableRva =
    0x40829F8;
constexpr std::uintptr_t kSendCharacterInteractionSecondaryVtableRva =
    0x40829C8;
constexpr std::uintptr_t kWarDeclarationVtableRva = 0x411DAA0;
constexpr std::uintptr_t kCharacterClaimVtableRva = 0x40E3060;
constexpr std::uintptr_t kEffectPreviewCollectorVtableRva = 0x411CBA8;
constexpr std::uintptr_t kJominiEffectVtableRva = 0x44CF030;
constexpr std::uintptr_t kJominiScriptedEffectVtableRva = 0x44CF0F8;
constexpr std::uintptr_t kJominiScriptedEffectTemplateVtableRva = 0x44DCD38;
constexpr std::uintptr_t kHiddenEffectVtableRva = 0x44D1C88;
constexpr std::uintptr_t kJominiContextEffectVtableRva = 0x44D27B8;
constexpr std::uintptr_t kPrestigeEffectVtableRva = 0x446C7B0;
constexpr std::uintptr_t kPrestigeExperienceEffectVtableRva = 0x446D368;
constexpr std::uintptr_t kPietyEffectVtableRva = 0x446CAD0;
constexpr std::uintptr_t kPietyExperienceEffectVtableRva = 0x446CA08;
constexpr std::uintptr_t kLegitimacyEffectVtableRva = 0x446E3D8;
constexpr std::uintptr_t kStressImpactEffectVtableRva = 0x446FE58;
constexpr std::uintptr_t
    kAddFromContributionAttackersEffectVtableRva = 0x444AE10;
constexpr std::uintptr_t
    kAddFromContributionDefendersEffectVtableRva = 0x444AED8;
constexpr std::uintptr_t kGoldTransferEffectVtableRva = 0x446E950;
constexpr std::uintptr_t kTruceEffectVtableRva = 0x4461CA8;
constexpr std::uintptr_t kAiUnitStackVtableRva = 0x4191870;
constexpr std::uintptr_t kAiSubunitStackVtableRva = 0x4192778;
constexpr std::uintptr_t kAiWarCoordinatorVtableRva = 0x41923B0;
constexpr std::uintptr_t kValidCasusBelliConfigurationScratchRva =
    0x4FED598;
constexpr std::uintptr_t kSubmitCommandRva = 0x0973E00;
constexpr std::uintptr_t kGetLocalPlayerRva = 0x346B7C0;
constexpr std::uintptr_t kGetCurrentEventRva = 0x2706AD0;
constexpr std::uintptr_t kIsPendingInteractionForCharacterRva = 0x1266BA0;
constexpr std::uintptr_t kValidateReplyCharacterInteractionCommandRva =
    0x26B3540;
constexpr std::uintptr_t kContainsWarParticipantRva = 0x2224870;
constexpr std::uintptr_t kGetWarScoreRva = 0x222A8A0;
constexpr std::uintptr_t kGetImprisonmentWarScoreRva = 0x29030B0;
constexpr std::uintptr_t kGetBattleWarScoreBaseRva = 0x2903150;
constexpr std::uintptr_t kGetBattleWarScoreSideRva = 0x2903DA0;
constexpr std::uintptr_t kGetOccupationWarScoreSideRva = 0x2904B00;
constexpr std::uintptr_t kGetTickingWarScoreSideRva = 0x2905BC0;
constexpr std::uintptr_t kIsNativeComponentAliveRva = 0x10495A0;
constexpr std::uintptr_t kGetSiegeProgressRva = 0x229B960;
constexpr std::uintptr_t kGetSiegeTotalWorkRva = 0x229CCA0;
constexpr std::uintptr_t kGetSiegeDaysLeftRva = 0x229BAA0;
constexpr std::uintptr_t kReadAssaultDailyProgressRva = 0x229F610;
constexpr std::uintptr_t kGetAssaultDailyCasualtiesRva = 0x229F410;
constexpr std::uintptr_t kValidateStartAssaultCommandRva = 0x26BE8C0;
constexpr std::uintptr_t kValidateStopAssaultCommandRva = 0x26BEA90;
constexpr std::uintptr_t kDestroyAssaultCommandRva = 0x0963C60;
constexpr std::uintptr_t kIsProvinceOccupiedRva = 0x220C4A0;
constexpr std::uintptr_t kGetProvinceFortLevelRva = 0x2209D20;
constexpr std::uintptr_t kGetProvinceGarrisonSizeRva = 0x220E710;
constexpr std::uintptr_t kGetProvinceBesiegingStrengthRva = 0x220E580;
constexpr std::uintptr_t kResolveDefaultRaiseProvinceRva = 0x224CC80;
constexpr std::uintptr_t kGetUnitStateRva = 0x0C7AAB0;
constexpr std::uintptr_t kGetArmyCurrentSoldiersRva = 0x27BD9E0;
constexpr std::uintptr_t kGetArmyMaximumSoldiersRva = 0x226F350;
constexpr std::uintptr_t kGetArmyCommanderRva = 0x2278F70;
constexpr std::uintptr_t kGetCommanderAdvantageRva = 0x0BC5410;
constexpr std::uintptr_t kGetProvinceTerrainRva = 0x220D940;
constexpr std::uintptr_t kEvaluateRegimentStatsAtProvinceRva = 0x239CAE0;
constexpr std::uintptr_t kIsSpecialCombatRegimentRva = 0x239CEB0;
constexpr std::uintptr_t kGetCharacterModifierAggregatorRva = 0x26172C0;
constexpr std::uintptr_t kReadCharacterModifierRva = 0x20AB950;
constexpr std::uintptr_t kGetCombatRulesRva = 0x82DC40;
constexpr std::uintptr_t kGetCombatSideStrengthRva = 0x23CC340;
constexpr std::uintptr_t kGetCombatRegimentStrengthRva = 0x23D2D70;
constexpr std::uintptr_t kReadCounterCurrentChunkRva = 0x23D2B90;
constexpr std::uintptr_t kResolveCounterClassesRva = 0x23CF1B0;
constexpr std::uintptr_t kGetCounterContextScaleRva = 0x2946B50;
constexpr std::uintptr_t kGetKnightEffectivenessContextRva = 0x2613480;
constexpr std::uintptr_t kReadKnightEffectivenessRva = 0x28FD990;
constexpr std::uintptr_t kIsHoldingDefenderRva = 0x2900BB0;
constexpr std::uintptr_t kCommanderMinRollRva = 0x570ED7C;
constexpr std::uintptr_t kCommanderMaxRollRva = 0x570ED80;
constexpr std::uintptr_t kKnightDamagePerProwessRva = 0x570EDF8;
constexpr std::uintptr_t kKnightToughnessPerProwessRva = 0x570EDFC;
constexpr std::uintptr_t kMinimumCombatWidthRva = 0x570ED84;
constexpr std::uintptr_t kBaseCombatWidthRatioRva = 0x570EDB8;
constexpr std::uintptr_t kConstructRaiseTroopsCommandRva = 0x26D6FC0;
constexpr std::uintptr_t kValidateRaiseTroopsCommandRva = 0x26D7150;
constexpr std::uintptr_t kDestroyRaiseTroopsCommandRva = 0x10E7950;
constexpr std::uintptr_t kGetArmyMoveModeRva = 0x26B51B0;
constexpr std::uintptr_t kCanCharacterUseCommandKindRva = 0x26B26A0;
constexpr std::uintptr_t kCanArmyUseMoveModeRva = 0x2248860;
constexpr std::uintptr_t kCanMoveArmyRva = 0x26B4610;
constexpr std::uintptr_t kCanOrderCombatRetreatRva = 0x2308250;
constexpr std::uintptr_t kGetCombatRetreatRuleStateRva = 0x26165B0;
constexpr std::uintptr_t kMinimumDaysBeforeManualRetreatRva = 0x570EE04;
constexpr std::uintptr_t kResolveMoveOriginRva = 0x2248260;
constexpr std::uintptr_t kConstructMovePathContextRva = 0x23C32F0;
constexpr std::uintptr_t kConstructArmyMovePathRva = 0x0C7BA70;
constexpr std::uintptr_t kBuildArmyMoveRouteRva = 0x23C33D0;
constexpr std::uintptr_t kReadUnitLandRouteSpeedRva = 0x2246EC0;
constexpr std::uintptr_t kReadUnitNavalRouteSpeedRva = 0x2247180;
constexpr std::uintptr_t kReadRouteTravelDurationRva = 0x2247320;
constexpr std::uintptr_t kReadRouteEdgeDurationRva = 0x22475E0;
constexpr std::uintptr_t kReadUnitCurrentEdgeSpeedRva = 0x2247B40;
constexpr std::uintptr_t kDestroyMoveArmyCommandRva = 0x26B46D0;
constexpr std::uintptr_t kValidateDisbandArmyCommandRva = 0x26B5710;
constexpr std::uintptr_t kValidateSplitArmyHalfCommandRva = 0x26B8030;
constexpr std::uintptr_t kDestroySplitArmyHalfCommandRva = 0x0963C60;
constexpr std::uintptr_t kCreateMergeArmiesCommandRva = 0x26C6CE0;
constexpr std::uintptr_t kValidateMergeArmiesCommandRva = 0x26BA050;
constexpr std::uintptr_t kDestroyMergeArmiesCommandRva = 0x26B5330;
constexpr std::uintptr_t kGetCasusBelliTypeDatabaseRva = 0x088E260;
constexpr std::uintptr_t kGetCharacterInteractionDatabaseRva = 0x0831890;
constexpr std::uintptr_t kHashStableKeyRva = 0x3B8B000;
constexpr std::uintptr_t kLookupSchemeTypeRva = 0x0A48C70;
constexpr std::uintptr_t kEvaluateCasusBelliRva = 0x2D95D00;
constexpr std::uintptr_t kDestroyValidCasusBelliConfigurationRva =
    0x101B3C0;
constexpr std::uintptr_t kConstructCharacterInteractionContextRva =
    0x2C3EE50;
constexpr std::uintptr_t kRedirectCharacterInteractionRolesRva =
    0x2C3C4C0;
constexpr std::uintptr_t kConstructCharacterInteractionContextAllRolesRva =
    0x2C3F000;
constexpr std::uintptr_t kCopyNativeIntArrayRva = 0x0BDBC10;
constexpr std::uintptr_t kAppendNativeIntArrayRangeRva = 0x0975ED0;
constexpr std::uintptr_t kRefreshCharacterInteractionContextRva =
    0x2C40950;
constexpr std::uintptr_t kFinalizeCharacterInteractionContextRva =
    0x2C40B20;
constexpr std::uintptr_t kValidateCharacterInteractionContextRva =
    0x2C43F00;
constexpr std::uintptr_t kReadCharacterInteractionAnswerScoreRva =
    0x2C44320;
constexpr std::uintptr_t kEvaluateCharacterInteractionTriggerRva =
    0x334C510;
constexpr std::uintptr_t kConstructSendCharacterInteractionCommandRva =
    0x26B3220;
constexpr std::uintptr_t kDestroyCharacterInteractionContextRva =
    0x2C3F380;
constexpr std::uintptr_t kDefaultConstructCharacterInteractionContextRva =
    0x2C3F300;
constexpr std::uintptr_t kConstructWarResolutionInteractionContextRva =
    0x0C569F0;
constexpr std::uintptr_t kConstructSpecialCharacterInteractionContextRva =
    0x2225D40;
constexpr std::uintptr_t kReadCharacterClaimRva = 0x28B1AA0;
constexpr std::uintptr_t kConstructWarEffectContextRva = 0x081F190;
constexpr std::uintptr_t kPopulateWarEffectContextRva = 0x27A46F0;
constexpr std::uintptr_t kConstructEffectPreviewCollectorRva = 0x10803E0;
constexpr std::uintptr_t kDestroyEffectPreviewCollectorRva = 0x10804E0;
constexpr std::uintptr_t kTraverseLoadedEffectRva = 0x3380170;
constexpr std::uintptr_t kDestroyEffectContext118Rva = 0x081E900;
constexpr std::uintptr_t kDestroyEffectContextArrayRowRva = 0x081E980;
constexpr std::uintptr_t kEvaluateTruceDurationDaysRva = 0x3373000;
constexpr std::uintptr_t kGetCharacterPrimaryTitleRva = 0x25F3350;
constexpr std::uintptr_t kReadMonthlyGoldIncomeRva = 0x28DBE90;
constexpr std::uintptr_t kEvaluateCharacterInteractionAnswerRva = 0x2C43B40;
constexpr std::uintptr_t kCbPrestigeFactorIdentifierIdRva = 0x57EB754;
constexpr std::uintptr_t kGetScriptIdentifierTableRva = 0x3B971A0;
// Locks the script-identifier table, calls lookup-only RVA 0x3B96D40, then
// unlocks. Unlike RVA 0x3B96E50 it never inserts a missing name.
constexpr std::uintptr_t kLookupScriptIdentifierIdRva = 0x3B97020;
constexpr std::uintptr_t kGetGenericValueTypeRegistryRva = 0x33C52B0;
constexpr std::uintptr_t kGenericValueTypeRegistryRva = 0x4FFE290;
constexpr std::uintptr_t kResolveGenericValueTypeNameRva = 0x3B58970;
constexpr std::uintptr_t kGenericValueTypeNameFallbackRva = 0x585F058;
constexpr std::uintptr_t kResolveScriptIdentifierNameRva = 0x3B97090;
constexpr std::uintptr_t kScriptIdentifierNameFallbackRva = 0x585F218;
constexpr std::uintptr_t kIsEventTargetValidRva = 0x3329B00;
constexpr std::uintptr_t kResolveEventTargetObjectRva = 0x33299E0;
constexpr std::uintptr_t kIsCharacterHostileRva = 0x2900470;
constexpr std::uintptr_t kIsArmyEmptyForContactRva = 0x2277290;
constexpr std::uintptr_t kIsArmyInCombatRva = 0x22771F0;
constexpr std::uintptr_t kReadProvinceHolderCharacterIdRva = 0x220C3F0;
constexpr std::uintptr_t kClassifyContactDefenderByHolderRva = 0x2900710;
constexpr std::uintptr_t kClassifyContactDefenderFallbackRva = 0x290CD60;

constexpr std::size_t kGameStateDateOffset = 0x08;
constexpr std::size_t kGameStateSpeedOffset = 0x70;
constexpr std::size_t kGameStateGameDataOffset = 0xA0;
constexpr std::size_t kJominiPlayersOffset = 0x18;
constexpr std::size_t kJominiPausedOffset = 0x20;
constexpr std::size_t kPlayersLocalIdOffset = 0x1F0;
constexpr std::size_t kPlayerIdOffset = 0x70;
constexpr std::size_t kEventManagerOffset = 0x2F4C0;
constexpr std::size_t kPlayerCharacterManagerOffset = 0x1D4F0;
constexpr std::size_t kWarManagerOffset = 0x29C20;
constexpr std::size_t kLandedTitleManagerOffset = 0x2FC8;
constexpr std::size_t kActiveEventDataOffset = 0x1B0;
constexpr std::size_t kActiveEventInstanceIdOffset = 0x1BC;
constexpr std::size_t kEventDataOptionCountOffset = 0x1BC;
constexpr std::size_t kComponentStorageSlotsOffset = 0x20;
constexpr std::size_t kComponentStorageCapacityOffset = 0x2C;
constexpr std::size_t kComponentStorageSlotSize = 0x10;
constexpr std::size_t kComponentStorageSlotObjectOffset = 0x08;
constexpr std::size_t kPendingInteractionIdOffset = 0x10;
constexpr std::size_t kPendingInteractionSenderIdOffset = 0x2F0;
constexpr std::size_t kPendingInteractionRecipientIdOffset = 0x2F4;
constexpr std::size_t kPendingInteractionAlternateRecipientIdOffset = 0x300;
constexpr std::size_t kPendingInteractionRoutingKindOffset = 0x5C0;
constexpr std::size_t kPendingInteractionAutoAcceptOffset = 0x5C6;
constexpr std::size_t kPlayerCharacterEntriesOffset = 0x58;
constexpr std::size_t kPlayerCharacterEntryCountOffset = 0x64;
constexpr std::size_t kPlayerCharacterIdOffset = 0xB0;
constexpr std::size_t kPlayerCharacterPlayerIdOffset = 0xD8;
constexpr std::size_t kCharacterIdOffset = 0x18;
constexpr std::size_t kCharacterValiditySubobjectOffset = 0x10;
constexpr std::size_t kCharacterEffectiveProwessOffset = 0xE8;
constexpr std::size_t kCharacterKnightLinkOffset = 0x1B0;
constexpr std::size_t kCharacterExtensionOffset = 0x1A8;
constexpr std::size_t kCharacterLegitimacyDataOffset = 0x1C0;
constexpr std::size_t kCharacterKnightLinkRegimentIdOffset = 0xF8;
constexpr std::size_t kCharacterFamilyDataOffset = 0x1A0;
constexpr std::size_t kCharacterLandStatusObjectOffset = 0x1B8;
constexpr std::size_t kCharacterDeathDataOffset = 0x1C8;
constexpr std::size_t kFamilyBetrothedCharacterIdOffset = 0x10;
constexpr std::size_t kFamilyPrimarySpouseCharacterIdOffset = 0x14;
constexpr std::size_t kFamilySpouseCharacterIdsOffset = 0x20;
constexpr std::size_t kWarStorageOffset = 0x20;
constexpr std::size_t kWarIdOffset = 0x08;
constexpr std::size_t kWarAttackersOffset = 0x20;
constexpr std::size_t kWarDefendersOffset = 0x80;
constexpr std::size_t kWarActiveCasusBelliTypeOffset = 0x100;
constexpr std::size_t kWarStartDateRawOffset = 0xE0;
constexpr std::size_t kWarPrimaryAttackerCharacterIdOffset = 0x288;
constexpr std::size_t kWarPrimaryDefenderCharacterIdOffset = 0x28C;
constexpr std::size_t kWarTargetedTitleIdsOffset = 0x270;
constexpr std::size_t kWarClaimantCharacterIdOffset = 0x290;
constexpr std::size_t kWarEndedDataOffset = 0x358;
constexpr std::size_t kWarParticipantPointersOffset = 0x08;
constexpr std::size_t kWarParticipantPointerCapacityOffset = 0x10;
constexpr std::size_t kWarParticipantPointerCountOffset = 0x14;
constexpr std::size_t kWarParticipantCharacterIdOffset = 0x08;
constexpr std::size_t kLandedTitleStorageOffset = 0x20;
constexpr std::size_t kLandedTitleIdOffset = 0x10;
constexpr std::size_t kLandedTitleTemplateOffset = 0x160;
constexpr std::size_t kLandedTitleDeJureVassalIdsOffset = 0x240;
constexpr std::size_t kLandedTitleTemplateTierOffset = 0x5C;
constexpr std::size_t kLandedTitleTemplateProvinceIdOffset = 0x80;
constexpr std::size_t kLandedTitleSuccessionIdsOffset = 0x278;
constexpr std::int32_t kBaronyTitleTier = 1;
constexpr std::int32_t kCountyTitleTier = 2;
constexpr std::size_t kArmyIdOffset = 0x10;
constexpr std::size_t kArmyCurrentProvinceOffset = 0x20;
constexpr std::size_t kArmyTargetProvinceOffset = 0x30;
constexpr std::size_t kUnitPathProvinceInfosOffset = 0x38;
constexpr std::size_t kUnitPathProvinceInfoCapacityOffset = 0x40;
constexpr std::size_t kUnitPathProvinceInfoCountOffset = 0x44;
constexpr std::size_t kUnitPathProvinceIdOffset = 0x00;
constexpr std::size_t kUnitRetreatStateOffset = 0x170;
constexpr std::size_t kUnitCachedCurrentEdgeSpeedOffset = 0x190;
constexpr std::size_t kArmyOwnerCharacterIdOffset = 0x174;
constexpr std::size_t kUnitArmyIdOffset = 0x178;
constexpr std::size_t kUnitAiWarCoordinatorIdOffset = 0x1C4;
constexpr std::size_t kUnitAiSubunitStackOffset = 0x1D0;
constexpr std::size_t kAiWarCoordinatorIdOffset = 0x10;
constexpr std::size_t kAiWarCoordinatorUnitStacksOffset = 0x50;
constexpr std::size_t kAiWarCoordinatorUnitStacksCapacityOffset = 0x58;
constexpr std::size_t kAiWarCoordinatorUnitStacksCountOffset = 0x5C;
constexpr std::size_t kAiUnitStackSupportProvincesOffset = 0x08;
constexpr std::size_t kAiUnitStackSupportProvincesCapacityOffset = 0x10;
constexpr std::size_t kAiUnitStackSupportProvincesCountOffset = 0x14;
constexpr std::size_t kAiUnitStackPublicCunitIdsOffset = 0x28;
constexpr std::size_t kAiUnitStackPublicCunitIdsCapacityOffset = 0x30;
constexpr std::size_t kAiUnitStackPublicCunitIdsCountOffset = 0x34;
constexpr std::size_t kAiUnitStackSubunitsOffset = 0x40;
constexpr std::size_t kAiUnitStackSubunitsCapacityOffset = 0x48;
constexpr std::size_t kAiUnitStackSubunitsCountOffset = 0x4C;
constexpr std::size_t kAiUnitStackCoordinatorOffset = 0x58;
constexpr std::size_t kAiSubunitPublicCunitIdsOffset = 0x10;
constexpr std::size_t kAiSubunitPublicCunitIdsCapacityOffset = 0x18;
constexpr std::size_t kAiSubunitPublicCunitIdsCountOffset = 0x1C;
constexpr std::size_t kAiSubunitRequestPowerBasisOffset = 0x28;
constexpr std::size_t kAiSubunitCrossCoordinatorValidOffset = 0x34;
constexpr std::size_t kAiSubunitCrossCoordinatorPowerOffset = 0x38;
constexpr std::size_t kAiSubunitParentOffset = 0x40;
constexpr std::size_t kAiSubunitAssignmentTargetOffset = 0x48;
constexpr std::size_t kAiSubunitFlagsOffset = 0x50;
constexpr std::size_t kInternalArmyIdOffset = 0x10;
constexpr std::size_t kInternalArmyRegimentIdsOffset = 0x38;
constexpr std::size_t kInternalArmyRegimentCapacityOffset = 0x40;
constexpr std::size_t kInternalArmyRegimentCountOffset = 0x44;
constexpr std::size_t kInternalArmyCommanderCharacterIdOffset = 0x120;
constexpr std::size_t kInternalArmyUnitIdOffset = 0x124;
constexpr std::size_t kInternalArmyCombatIdOffset = 0x128;
constexpr std::size_t kInternalArmyGatheringCountOffset = 0x5C;
constexpr std::size_t kRegimentIdentitySubobjectOffset = 0x08;
constexpr std::size_t kRegimentIdOffset = 0x10;
constexpr std::size_t kRegimentCurrentSoldiersOffset = 0x38;
constexpr std::size_t kRegimentMaximumSoldiersOffset = 0x3C;
constexpr std::size_t kRegimentAiBasePowerOffset = 0x40;
constexpr std::size_t kRegimentMaaTypeOffset = 0x118;
constexpr std::size_t kRegimentInnerTypeOffset = 0x18;
constexpr std::size_t kRegimentCounterStackSizeOffset = 0x68;
constexpr std::size_t kRegimentCounterClassOffset = 0x270;
constexpr std::size_t kRegimentCounterTargetsDataOffset = 0x2B8;
constexpr std::size_t kRegimentCounterTargetsCountOffset = 0x2C4;
constexpr std::size_t kRegimentMainPhaseEligibilityOffset = 0xA0A;
constexpr std::size_t kRegimentCounterTargetStride = 0x10;
constexpr std::size_t kRegimentCounterTargetClassOffset = 0x00;
constexpr std::size_t kRegimentCounterTargetEffectivenessOffset = 0x08;
constexpr std::size_t kRegimentKnightCharacterIdOffset = 0x148;
constexpr std::size_t kRegimentArmyIdOffset = 0x140;
constexpr std::size_t kDatabaseObjectKeyOffset = 0x18;
constexpr std::size_t kTerrainCombatWidthMultiplierOffset = 0x58;
constexpr std::size_t kTerrainCommanderMinRollModifierIndexOffset = 0x76E;
constexpr std::size_t kTerrainCommanderMaxRollModifierIndexOffset = 0x770;
constexpr std::int32_t kCommanderMinRollModifierIndex = 0x108;
constexpr std::int32_t kCommanderMaxRollModifierIndex = 0x109;
constexpr std::int32_t kCounterEfficiencyModifierIndex = 0x106;
constexpr std::int32_t kCounterResistanceModifierIndex = 0x107;
constexpr std::size_t kCombatRulesCounterClassCountOffset = 0xF14;
constexpr std::int32_t kMaximumCounterClasses = 4'096;
constexpr std::int32_t kMaximumCounterTargets = 4'096;
constexpr std::int32_t kMaximumProvinceAdjacencies = 4'096;
constexpr std::size_t kCombatIdOffset = 0x08;
constexpr std::size_t kCombatPhaseOffset = 0x6B0;
constexpr std::size_t kCombatPhaseDayOffset = 0x6B4;
constexpr std::size_t kCombatProvinceOffset = 0x6B8;
constexpr std::size_t kCombatBaseWidthOffset = 0x6C0;
constexpr std::size_t kCombatFinalWidthOffset = 0x6C4;
constexpr std::size_t kCombatBaseAdvantageOffset = 0x6C8;
constexpr std::size_t kCombatSide0RollOffset = 0x6D0;
constexpr std::size_t kCombatSide1RollOffset = 0x6D4;
constexpr std::size_t kCombatResolvedAdvantageOffset = 0x710;
constexpr std::size_t kCombatAttackerSideOffset = 0x20;
constexpr std::size_t kCombatDefenderSideOffset = 0x368;
constexpr std::size_t kCombatWinnerOffset = 0x6E0;
constexpr std::size_t kCombatRollCadenceCounterOffset = 0x6E4;
constexpr std::size_t kCombatForcedWinnerOffset = 0x700;
constexpr std::size_t kCombatFinalizedOffset = 0x704;
constexpr std::size_t kCombatDailyDispatchInProgressOffset = 0x705;
constexpr std::size_t kCombatBattleResultIdOffset = 0x708;
constexpr std::size_t kCombatSideArmyIdsOffset = 0x10;
constexpr std::size_t kCombatSideArmyCapacityOffset = 0x18;
constexpr std::size_t kCombatSideArmyCountOffset = 0x1C;
constexpr std::size_t kCombatSideLevyEntriesOffset = 0x28;
constexpr std::size_t kCombatSideLevyEntryCapacityOffset = 0x30;
constexpr std::size_t kCombatSideLevyEntryCountOffset = 0x34;
constexpr std::size_t kCombatSideMaaEntriesOffset = 0x40;
constexpr std::size_t kCombatSideMaaEntryCapacityOffset = 0x48;
constexpr std::size_t kCombatSideMaaEntryCountOffset = 0x4C;
constexpr std::size_t kCombatSideParticipantHardRowsOffset = 0x58;
constexpr std::size_t kCombatSideParticipantHardCapacityOffset = 0x60;
constexpr std::size_t kCombatSideParticipantHardCountOffset = 0x64;
constexpr std::size_t kCombatSidePrimaryCharacterIdOffset = 0x70;
constexpr std::size_t kCombatSideSelectedCommanderCharacterIdOffset = 0x74;
constexpr std::size_t kCombatSideStoredCurrentFightingOffset = 0x98;
constexpr std::size_t kCombatSideStoredLevyCurrentFightingOffset = 0xA0;
constexpr std::size_t kCombatSideCombatBackPointerOffset = 0xB8;
constexpr std::size_t kCombatSideDisallowRetreatOffset = 0xC0;
constexpr std::size_t kCombatSideAllowEarlyRetreatOffset = 0xC1;
constexpr std::size_t kCombatSideSkipPursuitOffset = 0xC2;
constexpr std::size_t kCombatRegimentEntryStride = 0x60;
constexpr std::size_t kCombatRegimentIdOffset = 0x08;
constexpr std::size_t kCombatRegimentStartingOffset = 0x10;
constexpr std::size_t kCombatRegimentCurrentFightingOffset = 0x18;
constexpr std::size_t kCombatRegimentSoftCasualtiesOffset = 0x20;
constexpr std::size_t kCombatRegimentEffectiveMaxSizeOffset = 0x30;
constexpr std::size_t kCombatRegimentEffectiveSiegeOffset = 0x38;
constexpr std::size_t kCombatRegimentEffectiveDamageOffset = 0x40;
constexpr std::size_t kCombatRegimentEffectiveToughnessOffset = 0x48;
constexpr std::size_t kCombatRegimentEffectivePursuitOffset = 0x50;
constexpr std::size_t kCombatRegimentEffectiveScreenOffset = 0x58;
constexpr std::size_t kCombatParticipantHardRowStride = 0x18;
constexpr std::size_t kCombatParticipantHardCharacterIdOffset = 0x08;
constexpr std::size_t kCombatParticipantHardCasualtiesOffset = 0x10;
constexpr std::size_t kBattleResultIdOffset = 0x08;
constexpr std::size_t kBattleResultReadyOffset = 0x28;
constexpr std::size_t kBattleResultRetreatElapsedBaselineDateOffset = 0x2C;
constexpr std::size_t kCharacterLandStatusSentinelOffset = 0x1F8;
constexpr std::size_t kCombatRetreatRuleFlagsOffset = 0x38;
constexpr std::uint32_t kCombatRetreatLandlessOverrideBit = 1U << 10U;
constexpr std::int64_t kCk3DateEpochRaw = 0x029C55C0;
constexpr std::int64_t kCk3DateRawPerWholeDay = 24;
constexpr std::size_t kEncounterMaaStatsMaximumOffset = 0x08;
constexpr std::size_t kEncounterMaaStatsSiegeOffset = 0x10;
constexpr std::size_t kEncounterMaaStatsDamageOffset = 0x18;
constexpr std::size_t kEncounterMaaStatsToughnessOffset = 0x20;
constexpr std::size_t kEncounterMaaStatsPursuitOffset = 0x28;
constexpr std::size_t kEncounterMaaStatsScreenOffset = 0x30;
constexpr std::size_t kProvinceIdOffset = 0x10;
constexpr std::size_t kProvinceMapNodeOffset = 0x08;
constexpr std::size_t kMapNodeAdjacencyDataOffset = 0x50;
constexpr std::size_t kMapNodeAdjacencyCountOffset = 0x5C;
constexpr std::size_t kMapNodePathProvinceInfoOffset = 0xB0;
constexpr std::size_t kMapAdjacencyStride = 0x30;
constexpr std::size_t kMapAdjacencyKindOffset = 0x00;
constexpr std::size_t kMapAdjacencyTargetProvinceIdOffset = 0x04;
constexpr std::size_t kPathProvinceInfoLandOffset = 0x09;
constexpr std::size_t kPathProvinceInfoWaterOffset = 0x0B;
constexpr std::size_t kProvinceOccupyingCharacterIdOffset = 0x744;
constexpr std::size_t kProvinceContactGatePointerOffset = 0x20;
constexpr std::size_t kProvinceUnitIdsOffset = 0x748;
constexpr std::size_t kProvinceUnitIdCountOffset = 0x754;
constexpr std::size_t kProvinceCombatIdsOffset = 0x760;
constexpr std::size_t kProvinceCombatIdCountOffset = 0x76C;
constexpr std::size_t kProvinceActiveSiegeIdOffset = 0x790;
constexpr std::size_t kProvinceFortLevelOffset = 0x858;
constexpr std::size_t kSiegeIdOffset = 0x08;
constexpr std::size_t kSiegeProvinceOffset = 0x200;
constexpr std::size_t kSiegeBesiegingArmyIdOffset = 0x208;
constexpr std::size_t kSiegeCurrentWorkOffset = 0x3D0;
constexpr std::size_t kSiegeBreachLevelOffset = 0x3D8;
constexpr std::size_t kSiegeAssaultInProgressOffset = 0x44C;
constexpr std::size_t kGameDataProvinceArrayOffset = 0x140;
constexpr std::size_t kGameDataProvinceCountOffset = 0x14C;
constexpr std::size_t kArrangeMarriageInteractionOffset = 0xF48;
constexpr std::size_t kDeclareWarInteractionOffset = 0xF78;
constexpr std::size_t kCasusBelliTypeArrayOffset = 0x68;
constexpr std::size_t kCasusBelliTypeCountOffset = 0x74;
constexpr std::size_t kCasusBelliTypeDatabaseIndexOffset = 0x10;
constexpr std::size_t kCasusBelliTypeKeyOffset = 0x18;
constexpr std::size_t kCasusBelliTypeRuleOffset = 0x38;
constexpr std::size_t kCasusBelliRuleDisabledOffset = 0x211;
constexpr std::size_t kCasusBelliTypeFlagsOffset = 0x1718;
constexpr std::uint32_t kCasusBelliWhitePeacePossibleFlag = 1U << 7U;
constexpr std::uint32_t kCasusBelliCombinedConfigurationsFlag = 1U << 20U;
constexpr std::size_t kValidCasusBelliConfigurationSize = 0x98;
constexpr std::size_t kValidCasusBelliClaimantOffset = 0x00;
constexpr std::size_t kValidCasusBelliTargetTitlesOffset = 0x08;
constexpr std::size_t kNativeArrayDataOffset = 0x00;
constexpr std::size_t kNativeArrayCapacityOffset = 0x08;
constexpr std::size_t kNativeArrayCountOffset = 0x0C;
constexpr std::size_t kCharacterInteractionSpecialDataOffset = 0x330;
constexpr std::size_t kCharacterInteractionContextScopeOffset = 0x08;
constexpr std::size_t kCharacterInteractionAutoAcceptTriggerOffset = 0x2580;
constexpr std::size_t kCharacterInteractionAutoAcceptScalarOffset = 0x2A48;
constexpr std::size_t kCharacterGoldOffset = 0x100;
constexpr std::size_t kCharacterPietyOffset = 0x110;
constexpr std::size_t kCharacterPietyExperienceOffset = 0x118;
constexpr std::size_t kCharacterPrestigeOffset = 0x130;
constexpr std::size_t kCharacterPrestigeExperienceOffset = 0x138;
constexpr std::size_t kCharacterMonthlyGoldIncomeOffset = 0x2B0;
constexpr std::size_t kCharacterStressPointsOffset = 0x2F8;
constexpr std::size_t kCharacterLegitimacyOffset = 0x28;
constexpr std::size_t kCharacterPrisonRelationOffset = 0x288;
constexpr std::size_t kPrisonRelationJailerCharacterIdOffset = 0x00;
constexpr std::size_t kWarEffectWhitePeaceOffset = 0x9C8;
constexpr std::size_t kWarEffectAttackerDefeatOffset = 0xA28;
constexpr std::size_t kTruceEffectDurationScriptValueOffset = 0x108;
constexpr std::size_t kGlobalVariableEntriesOffset = 0x10;
constexpr std::size_t kGlobalVariableEntryCountOffset = 0x1C;
constexpr std::size_t kGlobalVariableEntrySize = 0x20;
constexpr std::size_t kGlobalVariableEntryKeyOffset = 0x08;
constexpr std::size_t kGlobalVariableEntryValueOffset = 0x10;
constexpr std::uint16_t kNumericEventTargetKind = 1;
constexpr std::uint16_t kCharacterEventTargetKind = 4;
constexpr std::size_t kEventTargetPayloadOffset = 0x08;
constexpr std::int64_t kFixedPointScale = 100'000;
constexpr std::size_t kWarDeclarationCasusBelliOffset = 0x08;
constexpr std::size_t kWarDeclarationTargetTitlesOffset = 0x10;
constexpr std::size_t kWarDeclarationClaimantOffset = 0x28;
constexpr std::size_t kSendCharacterInteractionContextOffset = 0x20;
constexpr std::int32_t kMaximumPlayerCharacterEntries = 1024;
constexpr std::int32_t kMaximumComponentCapacity = 1'000'000;
constexpr std::int32_t kMaximumGlobalVariableEntries = 1'000'000;
constexpr std::int32_t kMaximumCasusBelliTypes = 10'000;
constexpr std::int32_t kMaximumCasusBelliConfigurations = 10'000;
constexpr std::int32_t kMaximumNativeTitleIds = 1'000'000;
constexpr std::int32_t kMaximumArmyRegiments = 65'536;
constexpr std::int32_t kMaximumWarObjectiveTitleIds = 4'096;
constexpr std::int32_t kMaximumUnitRouteProvinceInfos = 4'096;
constexpr std::int32_t kMaximumActualContactProvinceUnits = 4'096;
constexpr std::int32_t kMaximumActualContactProvinceCombats = 1'024;
constexpr std::int32_t kMaximumActualContactSideArmies = 4'096;
constexpr std::int32_t kMaximumActualContactRegiments = 4'096;
constexpr std::int32_t kMaximumBattleControlEntriesPerBucket = 16'384;
constexpr std::int32_t kMaximumBattleControlParticipantHardRows = 4'096;
constexpr std::int32_t kMaximumAiCoordinatorUnitStacks = 4'096;
constexpr std::int32_t kMaximumAiUnitStackSubunits = 4'096;
constexpr std::int32_t kMaximumAiSubunitPublicCunitIds = 4'096;
constexpr std::int32_t kMaximumAiSupportSearchProvinces = 4'096;
constexpr std::size_t kMaximumLandedTitleHierarchyDepth = 8;
constexpr std::size_t kMaximumWarObjectiveProvinceIds = 4'096;
constexpr std::size_t kMaximumWarObjectiveProvinceStateCount = 256;
constexpr std::size_t kMaximumDatabaseObjectKeyBytes = 4'096;
constexpr std::size_t kMsvcStringInlineCapacity = 15;
constexpr std::size_t kMaximumMarriageValidationSamples = 8;

constexpr std::string_view kSettlementReadyName = "xa_settlement_ready";
constexpr std::string_view kSettlementCommitSerialName =
    "xa_settlement_commit_serial";
constexpr std::string_view kSettlementSourceCharacterName =
    "xa_settlement_source_character";
constexpr std::string_view kSettlementFinalScoreName =
    "xa_settlement_final_score";
constexpr std::string_view kSettlementScoreBeforeRejectName =
    "xa_settlement_score_before_reject";
constexpr std::string_view kSettlementRecordCandidateName =
    "xa_settlement_record_candidate";
constexpr std::string_view kSettlementOldRecordName =
    "xa_settlement_old_record";
constexpr std::string_view kSettlementRecordDeltaName =
    "xa_settlement_record_delta";
constexpr std::string_view kSettlementBlessingCountName =
    "xa_settlement_blessing_count";
constexpr std::string_view kSettlementRefusalCountName =
    "xa_settlement_refusal_count";
constexpr std::string_view kSettlementContractProgressName =
    "xa_settlement_contract_progress";
constexpr std::string_view kSettlementRecordWrittenName =
    "xa_settlement_record_written";

struct NativeStringView {
  const char *data = nullptr;
  std::int32_t size = 0;
  std::uint8_t owned = 0;
  std::array<std::byte, 3> padding{};
};

static_assert(sizeof(NativeStringView) == 0x10);

struct PauseCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> flags_padding{};
  std::uint32_t metadata_0c = 0;
  std::uint32_t metadata_10 = 0;
  std::uint32_t metadata_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::int32_t player_id = -1;
  std::uint8_t paused = 0;
  std::array<std::byte, 3> payload_padding{};
};

struct SetSpeedCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> flags_padding{};
  std::uint32_t metadata_0c = 0;
  std::uint32_t metadata_10 = 0;
  std::uint32_t metadata_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::int32_t speed = 0;
  std::array<std::byte, 4> payload_padding{};
};

struct SelectEventOptionCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> flags_padding{};
  std::uint32_t metadata_0c = 0;
  std::uint32_t metadata_10 = 0;
  std::uint32_t metadata_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::int32_t event_instance_id = -1;
  std::int32_t option_index = -1;
};

struct InlineCk3String {
  std::array<char, 16> buffer{};
  std::uint64_t size = 0;
  std::uint64_t capacity = 15;
};

struct AutoSaveCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> flags_padding{};
  std::uint32_t metadata_0c = 0;
  std::uint32_t metadata_10 = 0;
  std::uint32_t metadata_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  InlineCk3String save_name{};
};

struct ReplyCharacterInteractionCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> flags_padding{};
  std::uint32_t metadata_0c = 0;
  std::uint32_t metadata_10 = 0;
  std::uint32_t metadata_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::int32_t pending_interaction_id = -1;
  std::int32_t reply = 0;
};

struct alignas(16) RaiseTroopsCommandStorage {
  std::array<std::byte, 0x50> bytes{};
};

struct RaiseEntry {
  std::int32_t province_id = -1;
  std::int32_t regiment_id = -1;
};

struct MoveArmyCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> flags_padding{};
  std::uint32_t metadata_0c = 0;
  std::uint32_t metadata_10 = 0;
  std::uint32_t metadata_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::int32_t command_kind = 1;
  std::int32_t army_id = -1;
  std::int32_t destination_province_id = -1;
  std::int32_t move_mode = 0;
  std::int32_t route_kind = 2;
  std::int32_t direct_target = 1;
  std::array<std::byte, 0x130> path_storage{};
};

struct MoveOriginContext {
  const std::uint8_t *mode_is_one = nullptr;
  void *army = nullptr;
  void *destination_province = nullptr;
};

struct alignas(8) MovePathContextStorage {
  std::array<std::byte, 0x70> bytes{};
};

struct MoveArmyCommandCleanup {
  DestroyNativeCommand destroy = nullptr;
  MoveArmyCommand *command = nullptr;

  ~MoveArmyCommandCleanup() {
    if (destroy != nullptr && command != nullptr) {
      destroy(command, 0);
    }
  }
};

struct DisbandArmyCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> flags_padding{};
  std::uint32_t metadata_0c = 0;
  std::uint32_t metadata_10 = 0;
  std::uint32_t metadata_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::int32_t command_kind = 1;
  std::int32_t command_target_id = -1;
};

struct SplitArmyHalfCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> flags_padding{};
  std::uint32_t metadata_0c = 0;
  std::uint32_t metadata_10 = 0;
  std::uint32_t metadata_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::int32_t command_kind = 1;
  std::int32_t played_character_id = -1;
  std::int32_t source_army_id = -1;
  std::array<std::byte, 4> payload_padding{};
};

struct NativeIntArrayHeader {
  std::int32_t *data = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
  void *allocator = nullptr;
};

struct MergeArmiesCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> flags_padding{};
  std::uint32_t metadata_0c = 0;
  std::uint32_t metadata_10 = 0;
  std::uint32_t metadata_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::int32_t command_kind = 0;
  std::int32_t destination_army_id = -1;
  NativeIntArrayHeader source_army_ids{};
};

struct MergeArmiesCommandCleanup {
  DestroyNativeCommand destroy = nullptr;
  MergeArmiesCommand *command = nullptr;

  ~MergeArmiesCommandCleanup() {
    if (destroy != nullptr && command != nullptr) {
      // The canonical factory allocated both the 0x40-byte object and, after
      // range insertion, its source array. Bit 1 frees both in native order.
      destroy(command, 1);
    }
  }
};

struct AssaultCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> flags_padding{};
  std::uint32_t metadata_0c = 0;
  std::uint32_t metadata_10 = 0;
  std::uint32_t metadata_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::int32_t command_kind = 1;
  std::int32_t played_character_id = -1;
  std::int32_t siege_id = -1;
  std::array<std::byte, 4> payload_padding{};
};

struct alignas(8) CharacterInteractionContextStorage {
  std::array<std::byte, 0x338> bytes{};
};

struct alignas(8) CharacterClaimStorage {
  std::array<std::byte, 0x18> bytes{};
};

struct alignas(16) WarEffectContextStorage {
  std::array<std::byte, 0x170> bytes{};
};

struct alignas(8) EffectPreviewCollectorStorage {
  std::array<std::byte, 0xD8> bytes{};
};

struct PreviewFixedPayload {
  std::uint32_t tag = 0;
  std::uint32_t padding = 0;
  std::int64_t raw = 0;
};

enum class WarExitPreviewRowKind {
  prestige,
  prestige_experience,
  piety,
  piety_experience,
  legitimacy,
  stress,
  gold_transfer,
  truce,
};

enum class WarExitPreviewOutcome : std::uint8_t {
  white_peace,
  attacker_defeat,
};

struct WarExitPreviewRow {
  WarExitPreviewRowKind kind = WarExitPreviewRowKind::prestige;
  std::int32_t first_character_id = -1;
  std::int32_t second_character_id = -1;
  std::int64_t raw = 0;
  void *effect_node = nullptr;
};

using EffectPreviewCollectorSlot8 = void (*)(
    void *collector, const void *first_scope, const void *second_scope,
    const PreviewFixedPayload *payload, void *effect_node,
    void *forwarded_argument);
using LoadedEffectSlot58 = void (*)(void *loaded_effect, void *wrapper,
                                    std::uint32_t mode, void *collector);

struct WarExitPreviewCapture {
  const Bindings *bindings = nullptr;
  EffectPreviewCollectorSlot8 original_slot8 = nullptr;
  std::int32_t primary_attacker_character_id = -1;
  std::int32_t primary_defender_character_id = -1;
  WarExitPreviewOutcome outcome = WarExitPreviewOutcome::white_peace;
  void *proxy_loaded_effect = nullptr;
  void *original_loaded_effect = nullptr;
  LoadedEffectSlot58 original_slot58 = nullptr;
  std::int32_t factor_identifier_id = -1;
  std::int64_t factor_raw = 0;
  bool factor_found = false;
  std::size_t callback_ordinal = 0;
  std::vector<WarExitPreviewRow> rows;
  bool failed = false;
};

struct WarExitHiddenTrucePath {
  void *root_effect = nullptr;
  void *root_children = nullptr;
  void *scripted_effect = nullptr;
  void *scripted_template = nullptr;
  void *default_effect = nullptr;
  void *default_children = nullptr;
  void *hidden_effect = nullptr;
  void *hidden_children = nullptr;
  void *context_effect = nullptr;
};

struct alignas(16) WarExitHiddenTruceProjection {
  std::array<std::byte, 0x50> root_effect{};
  std::array<void *, 13> root_children{};
  std::array<std::byte, 0xA0> scripted_effect{};
  std::array<std::byte, 0x128> scripted_template{};
  std::array<std::byte, 0x50> default_effect{};
  std::array<void *, 6> default_children{};
};

thread_local WarExitPreviewCapture *g_war_exit_preview_capture = nullptr;

struct alignas(8) SendCharacterInteractionCommandStorage {
  std::array<std::byte, 0x368> bytes{};
};

static_assert(sizeof(PauseCommand) == 0x28);
static_assert(offsetof(PauseCommand, secondary_vtable) == 0x18);
static_assert(offsetof(PauseCommand, player_id) == 0x20);
static_assert(offsetof(PauseCommand, paused) == 0x24);
static_assert(sizeof(SetSpeedCommand) == 0x28);
static_assert(offsetof(SetSpeedCommand, secondary_vtable) == 0x18);
static_assert(offsetof(SetSpeedCommand, speed) == 0x20);
static_assert(sizeof(SelectEventOptionCommand) == 0x28);
static_assert(offsetof(SelectEventOptionCommand, secondary_vtable) == 0x18);
static_assert(offsetof(SelectEventOptionCommand, event_instance_id) == 0x20);
static_assert(offsetof(SelectEventOptionCommand, option_index) == 0x24);
static_assert(sizeof(InlineCk3String) == 0x20);
static_assert(offsetof(InlineCk3String, size) == 0x10);
static_assert(offsetof(InlineCk3String, capacity) == 0x18);
static_assert(sizeof(AutoSaveCommand) == 0x40);
static_assert(offsetof(AutoSaveCommand, secondary_vtable) == 0x18);
static_assert(offsetof(AutoSaveCommand, save_name) == 0x20);
static_assert(sizeof(ReplyCharacterInteractionCommand) == 0x28);
static_assert(offsetof(ReplyCharacterInteractionCommand, secondary_vtable) ==
              0x18);
static_assert(
    offsetof(ReplyCharacterInteractionCommand, pending_interaction_id) ==
    0x20);
static_assert(offsetof(ReplyCharacterInteractionCommand, reply) == 0x24);
static_assert(sizeof(RaiseTroopsCommandStorage) == 0x50);
static_assert(sizeof(RaiseEntry) == 0x08);
static_assert(sizeof(MoveArmyCommand) == 0x168);
static_assert(offsetof(MoveArmyCommand, secondary_vtable) == 0x18);
static_assert(offsetof(MoveArmyCommand, command_kind) == 0x20);
static_assert(offsetof(MoveArmyCommand, army_id) == 0x24);
static_assert(offsetof(MoveArmyCommand, destination_province_id) == 0x28);
static_assert(offsetof(MoveArmyCommand, move_mode) == 0x2C);
static_assert(offsetof(MoveArmyCommand, route_kind) == 0x30);
static_assert(offsetof(MoveArmyCommand, direct_target) == 0x34);
static_assert(offsetof(MoveArmyCommand, path_storage) == 0x38);
static_assert(sizeof(MoveOriginContext) == 0x18);
static_assert(offsetof(MoveOriginContext, mode_is_one) == 0x00);
static_assert(offsetof(MoveOriginContext, army) == 0x08);
static_assert(offsetof(MoveOriginContext, destination_province) == 0x10);
static_assert(sizeof(MovePathContextStorage) == 0x70);
static_assert(sizeof(DisbandArmyCommand) == 0x28);
static_assert(offsetof(DisbandArmyCommand, secondary_vtable) == 0x18);
static_assert(offsetof(DisbandArmyCommand, command_kind) == 0x20);
static_assert(offsetof(DisbandArmyCommand, command_target_id) == 0x24);
static_assert(sizeof(SplitArmyHalfCommand) == 0x30);
static_assert(offsetof(SplitArmyHalfCommand, secondary_vtable) == 0x18);
static_assert(offsetof(SplitArmyHalfCommand, command_kind) == 0x20);
static_assert(offsetof(SplitArmyHalfCommand, played_character_id) == 0x24);
static_assert(offsetof(SplitArmyHalfCommand, source_army_id) == 0x28);
static_assert(sizeof(NativeIntArrayHeader) == 0x18);
static_assert(offsetof(NativeIntArrayHeader, allocator) == 0x10);
static_assert(sizeof(MergeArmiesCommand) == 0x40);
static_assert(offsetof(MergeArmiesCommand, secondary_vtable) == 0x18);
static_assert(offsetof(MergeArmiesCommand, command_kind) == 0x20);
static_assert(offsetof(MergeArmiesCommand, destination_army_id) == 0x24);
static_assert(offsetof(MergeArmiesCommand, source_army_ids) == 0x28);
static_assert(sizeof(AssaultCommand) == 0x30);
static_assert(offsetof(AssaultCommand, secondary_vtable) == 0x18);
static_assert(offsetof(AssaultCommand, command_kind) == 0x20);
static_assert(offsetof(AssaultCommand, played_character_id) == 0x24);
static_assert(offsetof(AssaultCommand, siege_id) == 0x28);
static_assert(sizeof(CharacterInteractionContextStorage) == 0x338);
static_assert(sizeof(CharacterClaimStorage) == 0x18);
static_assert(sizeof(WarEffectContextStorage) == 0x170);
static_assert(sizeof(EffectPreviewCollectorStorage) == 0xD8);
static_assert(sizeof(PreviewFixedPayload) == 0x10);
static_assert(sizeof(SendCharacterInteractionCommandStorage) == 0x368);

template <typename Value>
Value LoadAt(const void *base, std::size_t offset) noexcept {
  Value result{};
  std::memcpy(&result, static_cast<const std::byte *>(base) + offset,
              sizeof(result));
  return result;
}

template <typename Value>
void StoreAt(void *base, std::size_t offset, Value value) noexcept {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value,
              sizeof(value));
}

void SetUnknownWarExitPreviewRowReason(
    const void *effect_node, const void *first_scope,
    const void *second_scope, const PreviewFixedPayload *payload,
    const void *forwarded_argument, std::size_t callback_ordinal) noexcept {
  if (!g_last_war_exit_preview_unavailable_reason.empty()) {
    return;
  }
  const auto module =
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  const auto effect_vtable =
      effect_node == nullptr ? std::uintptr_t{0}
                             : LoadAt<std::uintptr_t>(effect_node, 0x00);
  const auto effect_vtable_rva =
      module != 0 && effect_vtable >= module ? effect_vtable - module
                                             : effect_vtable;
  const auto first_kind = first_scope == nullptr
                              ? std::uint16_t{0xFFFF}
                              : LoadAt<std::uint16_t>(first_scope, 0x00);
  const auto first_id = first_scope == nullptr
                            ? std::int32_t{-1}
                            : LoadAt<std::int32_t>(first_scope, 0x08);
  const auto second_kind = second_scope == nullptr
                               ? std::uint16_t{0xFFFF}
                               : LoadAt<std::uint16_t>(second_scope, 0x00);
  const auto second_id = second_scope == nullptr
                             ? std::int32_t{-1}
                             : LoadAt<std::int32_t>(second_scope, 0x08);
  const auto payload_tag =
      payload == nullptr ? std::uint32_t{0xFFFFFFFF} : payload->tag;
  const auto payload_raw =
      payload == nullptr ? std::int64_t{0} : payload->raw;
  const int written = std::snprintf(
      g_war_exit_preview_diagnostic_buffer.data(),
      g_war_exit_preview_diagnostic_buffer.size(),
      "dry_preview.capture_row_unknown:effect_vtable_rva=0x%llX,"
      "first_kind=%u,first_id=%d,second_kind=%u,second_id=%d,"
      "payload_tag=%u,payload_raw=%lld,forwarded_ptr=0x%llX,"
      "callback_ordinal=%llu",
      static_cast<unsigned long long>(effect_vtable_rva),
      static_cast<unsigned int>(first_kind), first_id,
      static_cast<unsigned int>(second_kind), second_id, payload_tag,
      static_cast<long long>(payload_raw),
      static_cast<unsigned long long>(
          reinterpret_cast<std::uintptr_t>(forwarded_argument)),
      static_cast<unsigned long long>(callback_ordinal));
  if (written <= 0 ||
      static_cast<std::size_t>(written) >=
          g_war_exit_preview_diagnostic_buffer.size()) {
    SetWarExitPreviewUnavailableReason("dry_preview.capture_row_unknown");
    return;
  }
  g_last_war_exit_preview_unavailable_reason = std::string_view(
      g_war_exit_preview_diagnostic_buffer.data(),
      static_cast<std::size_t>(written));
}

void *CurrentEvent(const Bindings &bindings, void *game_state) noexcept {
  if (bindings.get_current_event == nullptr || game_state == nullptr) {
    return nullptr;
  }
  void *const game_data =
      LoadAt<void *>(game_state, kGameStateGameDataOffset);
  if (game_data == nullptr) {
    return nullptr;
  }
  void *const event_manager =
      static_cast<std::byte *>(game_data) + bindings.event_manager_offset;
  return bindings.get_current_event(event_manager);
}

bool ReadCurrentEvent(const Bindings &bindings, void *game_state,
                      std::int32_t &instance_id,
                      std::int32_t &option_count) noexcept {
  void *const active_event = CurrentEvent(bindings, game_state);
  if (active_event == nullptr) {
    return false;
  }
  void *const event_data =
      LoadAt<void *>(active_event, kActiveEventDataOffset);
  if (event_data == nullptr) {
    return false;
  }
  instance_id =
      LoadAt<std::int32_t>(active_event, kActiveEventInstanceIdOffset);
  option_count =
      LoadAt<std::int32_t>(event_data, kEventDataOptionCountOffset);
  return instance_id > 0 && option_count >= 0;
}

bool ReadPendingCharacterInteraction(const Bindings &bindings,
                                     void *played_character,
                                     std::int32_t played_character_id,
                                     std::int32_t &instance_id,
                                     std::int32_t &sender_character_id,
                                     bool &auto_accept_notification) noexcept {
  if (played_character == nullptr || played_character_id == -1 ||
      bindings.pending_character_interaction_storage_slot == nullptr ||
      bindings.is_pending_character_interaction_for_character == nullptr ||
      bindings.validate_reply_character_interaction_command == nullptr ||
      bindings.reply_character_interaction_primary_vtable == 0 ||
      bindings.reply_character_interaction_secondary_vtable == 0) {
    return false;
  }
  void *const storage =
      *bindings.pending_character_interaction_storage_slot;
  if (storage == nullptr) {
    return false;
  }
  void *const slots = LoadAt<void *>(storage, kComponentStorageSlotsOffset);
  const std::int32_t capacity =
      LoadAt<std::int32_t>(storage, kComponentStorageCapacityOffset);
  if (slots == nullptr || capacity <= 0) {
    return false;
  }

  for (std::int32_t index = 0; index < capacity; ++index) {
    const auto slot_offset = static_cast<std::size_t>(index) *
                                 kComponentStorageSlotSize +
                             kComponentStorageSlotObjectOffset;
    void *const pending = LoadAt<void *>(slots, slot_offset);
    if (pending == nullptr) {
      continue;
    }
    const std::int32_t candidate_id =
        LoadAt<std::int32_t>(pending, kPendingInteractionIdOffset);
    if ((static_cast<std::uint32_t>(candidate_id) & 0x00FFFFFFU) !=
        static_cast<std::uint32_t>(index)) {
      continue;
    }

    // CK3's notification enumeration calls RVA 0x1266BA0 with the pending
    // object and the currently played Character.  Cheaply reproduce its
    // routing switch first so the exact engine predicate is called only for
    // requests addressed to this player, not every global pending component.
    const std::int32_t routing_kind = LoadAt<std::int32_t>(
        pending, kPendingInteractionRoutingKindOffset);
    std::size_t recipient_offset = kPendingInteractionRecipientIdOffset;
    if (routing_kind == 1) {
      recipient_offset = kPendingInteractionAlternateRecipientIdOffset;
    } else if (routing_kind != 0 && routing_kind != 2) {
      continue;
    }
    if (LoadAt<std::int32_t>(pending, recipient_offset) !=
        played_character_id) {
      continue;
    }

    if (!bindings.is_pending_character_interaction_for_character(
            pending, played_character)) {
      continue;
    }

    const bool notification =
        LoadAt<std::uint8_t>(pending,
                             kPendingInteractionAutoAcceptOffset) != 0;
    if (!notification) {
      ReplyCharacterInteractionCommand accept_command{};
      accept_command.primary_vtable =
          bindings.reply_character_interaction_primary_vtable;
      accept_command.secondary_vtable =
          bindings.reply_character_interaction_secondary_vtable;
      accept_command.pending_interaction_id = candidate_id;
      accept_command.reply =
          static_cast<std::int32_t>(PendingInteractionReply::accept);
      if (!bindings.validate_reply_character_interaction_command(
              &accept_command)) {
        continue;
      }
    }
    instance_id = candidate_id;
    sender_character_id = LoadAt<std::int32_t>(
        pending, kPendingInteractionSenderIdOffset);
    auto_accept_notification = notification;
    return true;
  }
  return false;
}

void *ResolveCharacter(const Bindings &bindings,
                       std::int32_t character_id) noexcept {
  if (character_id == -1 || bindings.character_storage_slot == nullptr) {
    return nullptr;
  }
  void *const storage = *bindings.character_storage_slot;
  if (storage == nullptr) {
    return nullptr;
  }
  void *const slots = LoadAt<void *>(storage, kComponentStorageSlotsOffset);
  const std::int32_t capacity =
      LoadAt<std::int32_t>(storage, kComponentStorageCapacityOffset);
  const std::uint32_t index =
      static_cast<std::uint32_t>(character_id) & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 ||
      index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  const auto slot_offset = static_cast<std::size_t>(index) *
                               kComponentStorageSlotSize +
                           kComponentStorageSlotObjectOffset;
  void *const character = LoadAt<void *>(slots, slot_offset);
  if (character == nullptr ||
      LoadAt<std::int32_t>(character, kCharacterIdOffset) != character_id) {
    return nullptr;
  }
  return character;
}

const void *FindGlobalVariableValue(const Bindings &bindings,
                                    void *container,
                                    std::string_view name) noexcept {
  if (container == nullptr ||
      bindings.get_script_identifier_table == nullptr ||
      bindings.lookup_script_identifier_id == nullptr || name.empty() ||
      name.size() >
          static_cast<std::size_t>(std::numeric_limits<std::int32_t>::max())) {
    return nullptr;
  }
  void *const identifier_table = bindings.get_script_identifier_table();
  if (identifier_table == nullptr) {
    return nullptr;
  }
  const NativeStringView view{name.data(),
                              static_cast<std::int32_t>(name.size())};
  std::int32_t key = -1;
  if (bindings.lookup_script_identifier_id(identifier_table, &key, &view) ==
          nullptr ||
      key < 0) {
    return nullptr;
  }
  void *const entries =
      LoadAt<void *>(container, kGlobalVariableEntriesOffset);
  const std::int32_t count = LoadAt<std::int32_t>(
      container, kGlobalVariableEntryCountOffset);
  if (entries == nullptr || count < 0 ||
      count > kMaximumGlobalVariableEntries) {
    return nullptr;
  }
  const auto *entry = static_cast<const std::byte *>(entries);
  for (std::int32_t index = 0; index < count;
       ++index, entry += kGlobalVariableEntrySize) {
    if (LoadAt<std::int32_t>(entry, kGlobalVariableEntryKeyOffset) == key) {
      return entry + kGlobalVariableEntryValueOffset;
    }
  }
  return nullptr;
}

bool ReadFixedPoint(const void *event_target,
                    FixedPointValue &output) noexcept {
  if (event_target == nullptr ||
      LoadAt<std::uint16_t>(event_target, 0) != kNumericEventTargetKind) {
    return false;
  }
  output.raw = LoadAt<std::int64_t>(event_target, 0x08);
  output.scale = kFixedPointScale;
  return true;
}

bool ReadSemanticInteger(const void *event_target,
                         std::int64_t &output) noexcept {
  FixedPointValue fixed{};
  if (!ReadFixedPoint(event_target, fixed) ||
      fixed.raw % fixed.scale != 0) {
    return false;
  }
  output = fixed.raw / fixed.scale;
  return true;
}

bool ReadSemanticBoolean(const void *event_target, bool &output) noexcept {
  std::int64_t value = 0;
  if (!ReadSemanticInteger(event_target, value) ||
      (value != 0 && value != 1)) {
    return false;
  }
  output = value == 1;
  return true;
}

bool ReadSettlementSourceCharacter(const Bindings &bindings,
                                    const void *event_target,
                                    std::int32_t &character_id) noexcept {
  if (event_target == nullptr ||
      LoadAt<std::uint16_t>(event_target, 0) != kCharacterEventTargetKind) {
    return false;
  }
  // CK3 1.19.0.6's character EventTarget stores its complete CharacterID at
  // +0x08. Its generic object resolver adds gameplay-liveness checks,
  // including CCharacter+0x1A8, and therefore returns null for the retained
  // scope:xar_dead. Settlement needs stable identity, not a live gameplay
  // object, so decode the proven variant and require a generation-safe storage
  // lookup to return that exact ID.
  const std::int32_t candidate_id =
      LoadAt<std::int32_t>(event_target, kEventTargetPayloadOffset);
  void *const object = ResolveCharacter(bindings, candidate_id);
  if (object == nullptr) {
    return false;
  }
  if (LoadAt<std::int32_t>(object, kCharacterIdOffset) != candidate_id) {
    return false;
  }
  character_id = candidate_id;
  return true;
}

void ReadOneLifeSettlement(const Bindings &bindings,
                           Snapshot &output) noexcept {
  output.has_one_life_settlement = false;
  output.one_life_settlement = {};
  if (bindings.global_variable_container_accessor_slot == nullptr) {
    return;
  }
  const GetGlobalVariableContainer accessor =
      *bindings.global_variable_container_accessor_slot;
  if (accessor == nullptr) {
    return;
  }
  void *const container = accessor();
  if (container == nullptr) {
    return;
  }

  const void *const ready_value =
      FindGlobalVariableValue(bindings, container, kSettlementReadyName);
  bool ready = false;
  if (!ReadSemanticBoolean(ready_value, ready) || !ready) {
    return;
  }

  OneLifeSettlementSnapshot settlement{};
  settlement.ready = true;
  bool record_written = false;
  if (!ReadSemanticInteger(
          FindGlobalVariableValue(bindings, container,
                                  kSettlementCommitSerialName),
          settlement.commit_serial) ||
      !ReadSettlementSourceCharacter(
          bindings,
          FindGlobalVariableValue(bindings, container,
                                  kSettlementSourceCharacterName),
          settlement.source_character_id) ||
      !ReadFixedPoint(
          FindGlobalVariableValue(bindings, container,
                                  kSettlementFinalScoreName),
          settlement.final_score) ||
      !ReadFixedPoint(
          FindGlobalVariableValue(bindings, container,
                                  kSettlementScoreBeforeRejectName),
          settlement.score_before_reject) ||
      !ReadSemanticInteger(
          FindGlobalVariableValue(bindings, container,
                                  kSettlementRecordCandidateName),
          settlement.record_candidate) ||
      !ReadSemanticInteger(
          FindGlobalVariableValue(bindings, container,
                                  kSettlementOldRecordName),
          settlement.old_record) ||
      !ReadSemanticInteger(
          FindGlobalVariableValue(bindings, container,
                                  kSettlementRecordDeltaName),
          settlement.record_delta) ||
      !ReadSemanticInteger(
          FindGlobalVariableValue(bindings, container,
                                  kSettlementBlessingCountName),
          settlement.blessing_count) ||
      !ReadSemanticInteger(
          FindGlobalVariableValue(bindings, container,
                                  kSettlementRefusalCountName),
          settlement.refusal_count) ||
      !ReadSemanticInteger(
          FindGlobalVariableValue(bindings, container,
                                  kSettlementContractProgressName),
          settlement.contract_progress) ||
      !ReadSemanticBoolean(
          FindGlobalVariableValue(bindings, container,
                                  kSettlementRecordWrittenName),
          record_written)) {
    return;
  }
  settlement.record_written = record_written;

  // A new episode invalidates the old payload by writing ready=0 first. Read
  // the publication gate again so a transition cannot expose a mixed object.
  ready = false;
  if (!ReadSemanticBoolean(
          FindGlobalVariableValue(bindings, container,
                                  kSettlementReadyName),
          ready) ||
      !ready) {
    return;
  }
  output.one_life_settlement = settlement;
  output.has_one_life_settlement = true;
}

bool ReadPlayedCharacter(const Bindings &bindings, void *game_state,
                         std::int32_t local_player_id,
                         std::int32_t &character_id, bool &alive) noexcept {
  if (game_state == nullptr || local_player_id < 0 ||
      bindings.character_storage_slot == nullptr) {
    return false;
  }
  void *const game_data =
      LoadAt<void *>(game_state, kGameStateGameDataOffset);
  if (game_data == nullptr) {
    return false;
  }
  const auto *const manager = static_cast<const std::byte *>(game_data) +
                              bindings.player_character_manager_offset;
  void *const entries =
      LoadAt<void *>(manager, kPlayerCharacterEntriesOffset);
  const std::int32_t count =
      LoadAt<std::int32_t>(manager, kPlayerCharacterEntryCountOffset);
  if (entries == nullptr || count <= 0 ||
      count > kMaximumPlayerCharacterEntries) {
    return false;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    void *const entry = LoadAt<void *>(
        entries, static_cast<std::size_t>(index) * sizeof(void *));
    if (entry == nullptr ||
        LoadAt<std::int32_t>(entry, kPlayerCharacterPlayerIdOffset) !=
            local_player_id) {
      continue;
    }
    const std::int32_t candidate_id =
        LoadAt<std::int32_t>(entry, kPlayerCharacterIdOffset);
    void *const character = ResolveCharacter(bindings, candidate_id);
    if (character == nullptr) {
      continue;
    }
    character_id = candidate_id;
    alive =
        LoadAt<void *>(character, kCharacterDeathDataOffset) == nullptr;
    return true;
  }
  return false;
}

bool HasDeclarableWarReadBindings(const Bindings &bindings) noexcept {
  return bindings.enabled && bindings.game_state_slot != nullptr &&
         bindings.character_storage_slot != nullptr &&
         bindings.valid_casus_belli_configuration_scratch != nullptr &&
         bindings.get_casus_belli_type_database != nullptr &&
         bindings.get_character_interaction_database != nullptr &&
         bindings.evaluate_casus_belli != nullptr &&
         bindings.destroy_valid_casus_belli_configuration != nullptr;
}

bool HasArrangeMarriageReadBindings(const Bindings &bindings) noexcept {
  return bindings.enabled && bindings.game_state_slot != nullptr &&
         bindings.character_storage_slot != nullptr &&
         bindings.get_character_interaction_database != nullptr &&
         bindings.arrange_marriage_interaction_offset != 0 &&
         bindings.redirect_character_interaction_roles != nullptr &&
         bindings.construct_character_interaction_context_all_roles !=
             nullptr &&
         bindings.refresh_character_interaction_context != nullptr &&
         bindings.finalize_character_interaction_context != nullptr &&
         bindings.validate_character_interaction_context != nullptr &&
         bindings.destroy_character_interaction_context != nullptr;
}

void *ResolveCharacterInteraction(const Bindings &bindings,
                                  std::size_t interaction_offset) noexcept {
  if (bindings.get_character_interaction_database == nullptr ||
      interaction_offset == 0) {
    return nullptr;
  }
  void *const interaction_database =
      bindings.get_character_interaction_database();
  return interaction_database == nullptr
             ? nullptr
             : LoadAt<void *>(
                   interaction_database, interaction_offset);
}

bool PrepareArrangeMarriageContext(
    const Bindings &bindings, std::int32_t played_character_id,
    std::int32_t candidate_character_id,
    CharacterInteractionContextStorage &storage,
    ArrangeMarriageValidationSample *diagnostic_sample = nullptr) noexcept {
  void *const interaction =
      ResolveCharacterInteraction(
          bindings, bindings.arrange_marriage_interaction_offset);
  if (interaction == nullptr) {
    return false;
  }
  std::int32_t actor_character_id = played_character_id;
  std::int32_t recipient_character_id = candidate_character_id;
  std::int32_t secondary_actor_character_id = played_character_id;
  std::int32_t secondary_recipient_character_id = candidate_character_id;
  std::int32_t intermediary_character_id = -1;
  bindings.redirect_character_interaction_roles(
      interaction, &actor_character_id, &recipient_character_id,
      &secondary_actor_character_id, &secondary_recipient_character_id,
      &intermediary_character_id);
  if (diagnostic_sample != nullptr) {
    diagnostic_sample->candidate_character_id = candidate_character_id;
    diagnostic_sample->actor_character_id = actor_character_id;
    diagnostic_sample->recipient_character_id = recipient_character_id;
    diagnostic_sample->secondary_actor_character_id =
        secondary_actor_character_id;
    diagnostic_sample->secondary_recipient_character_id =
        secondary_recipient_character_id;
    diagnostic_sample->intermediary_character_id =
        intermediary_character_id;
  }
  void *const context = storage.bytes.data();
  if (bindings.construct_character_interaction_context_all_roles(
          context, interaction, actor_character_id,
          recipient_character_id, secondary_actor_character_id,
          secondary_recipient_character_id, intermediary_character_id,
          nullptr) != context) {
    return false;
  }
  bindings.refresh_character_interaction_context(context, true);
  bindings.finalize_character_interaction_context(context);
  return true;
}

bool ReadNativeIntArray(
    const void *native_array, std::vector<std::int32_t> &output,
    std::int32_t maximum_count = kMaximumNativeTitleIds) noexcept {
  const auto capacity =
      LoadAt<std::int32_t>(native_array, kNativeArrayCapacityOffset);
  const auto count =
      LoadAt<std::int32_t>(native_array, kNativeArrayCountOffset);
  const auto *const data =
      LoadAt<const std::int32_t *>(native_array, kNativeArrayDataOffset);
  if (maximum_count < 0 || capacity < 0 || count < 0 || count > capacity ||
      count > maximum_count || (count > 0 && data == nullptr)) {
    return false;
  }
  output.clear();
  output.reserve(static_cast<std::size_t>(count));
  for (std::int32_t index = 0; index < count; ++index) {
    output.push_back(data[index]);
  }
  return true;
}

bool ReadPlayedCharacterRelationships(
    const Bindings &bindings, const void *played_character,
    std::int32_t &betrothed_character_id,
    std::int32_t &primary_spouse_character_id,
    std::vector<std::int32_t> &spouse_character_ids) noexcept {
  betrothed_character_id = -1;
  primary_spouse_character_id = -1;
  spouse_character_ids.clear();
  if (played_character == nullptr) {
    return true;
  }
  const void *const family_data =
      LoadAt<const void *>(played_character, kCharacterFamilyDataOffset);
  if (family_data == nullptr) {
    return true;
  }

  const auto raw_betrothed_character_id = LoadAt<std::int32_t>(
      family_data, kFamilyBetrothedCharacterIdOffset);
  if (ResolveCharacter(bindings, raw_betrothed_character_id) != nullptr) {
    betrothed_character_id = raw_betrothed_character_id;
  }
  const auto raw_primary_spouse_character_id = LoadAt<std::int32_t>(
      family_data, kFamilyPrimarySpouseCharacterIdOffset);
  if (ResolveCharacter(bindings, raw_primary_spouse_character_id) != nullptr) {
    primary_spouse_character_id = raw_primary_spouse_character_id;
  }

  std::vector<std::int32_t> raw_spouse_character_ids;
  if (!ReadNativeIntArray(
          static_cast<const std::byte *>(family_data) +
              kFamilySpouseCharacterIdsOffset,
          raw_spouse_character_ids)) {
    return false;
  }
  spouse_character_ids.reserve(raw_spouse_character_ids.size());
  for (const auto spouse_character_id : raw_spouse_character_ids) {
    if (ResolveCharacter(bindings, spouse_character_id) != nullptr) {
      spouse_character_ids.push_back(spouse_character_id);
    }
  }
  return true;
}

bool ReadValidCasusBelliConfigurationArray(
    const Bindings &bindings, void *&data, std::int32_t &count) noexcept {
  void *const scratch =
      bindings.valid_casus_belli_configuration_scratch;
  const auto capacity =
      LoadAt<std::int32_t>(scratch, kNativeArrayCapacityOffset);
  count = LoadAt<std::int32_t>(scratch, kNativeArrayCountOffset);
  data = LoadAt<void *>(scratch, kNativeArrayDataOffset);
  return capacity >= 0 && count >= 0 && count <= capacity &&
         count <= kMaximumCasusBelliConfigurations &&
         (count == 0 || data != nullptr);
}

bool ClearValidCasusBelliConfigurations(
    const Bindings &bindings) noexcept {
  void *data = nullptr;
  std::int32_t count = 0;
  if (!ReadValidCasusBelliConfigurationArray(bindings, data, count)) {
    return false;
  }
  auto *configuration = static_cast<std::byte *>(data);
  for (std::int32_t index = 0; index < count; ++index) {
    bindings.destroy_valid_casus_belli_configuration(configuration);
    configuration += kValidCasusBelliConfigurationSize;
  }
  StoreAt(bindings.valid_casus_belli_configuration_scratch,
          kNativeArrayCountOffset, std::int32_t{0});
  return true;
}

bool ReadCasusBelliDatabase(void *database, void *&types,
                            std::int32_t &count) noexcept {
  if (database == nullptr) {
    return false;
  }
  types = LoadAt<void *>(database, kCasusBelliTypeArrayOffset);
  count = LoadAt<std::int32_t>(database, kCasusBelliTypeCountOffset);
  return count >= 0 && count <= kMaximumCasusBelliTypes &&
         (count == 0 || types != nullptr);
}

bool IsEnabledCasusBelliType(const void *casus_belli_type) noexcept {
  if (casus_belli_type == nullptr) {
    return false;
  }
  void *const rule =
      LoadAt<void *>(casus_belli_type, kCasusBelliTypeRuleOffset);
  return rule != nullptr &&
         LoadAt<std::uint8_t>(rule, kCasusBelliRuleDisabledOffset) == 0;
}

bool ReadDatabaseObjectKey(const void *database_object,
                           std::size_t key_offset,
                           std::string &output) noexcept {
  if (database_object == nullptr) {
    return false;
  }
  const auto *const string_storage =
      static_cast<const std::byte *>(database_object) + key_offset;
  const auto size = LoadAt<std::size_t>(string_storage, 0x10);
  const auto capacity = LoadAt<std::size_t>(string_storage, 0x18);
  if (size > capacity || size > kMaximumDatabaseObjectKeyBytes) {
    return false;
  }
  const char *data = nullptr;
  if (capacity <= kMsvcStringInlineCapacity) {
    data = reinterpret_cast<const char *>(string_storage);
  } else {
    data = LoadAt<const char *>(string_storage, 0x00);
  }
  if (size > 0 && data == nullptr) {
    return false;
  }
  output.assign(data == nullptr ? "" : data, size);
  return true;
}

bool ReadCasusBelliTypeKey(const void *casus_belli_type,
                           std::string &output) noexcept {
  return ReadDatabaseObjectKey(casus_belli_type,
                               kCasusBelliTypeKeyOffset, output);
}

bool MaterializeCasusBelliChoices(
    const Bindings &bindings, const void *casus_belli_type,
    std::int32_t target_character_id, std::int32_t casus_belli_index,
    std::vector<DeclarableWarSnapshot> &output) noexcept {
  std::string casus_belli_key;
  if (!ReadCasusBelliTypeKey(casus_belli_type, casus_belli_key)) {
    return false;
  }
  void *configuration_data = nullptr;
  std::int32_t configuration_count = 0;
  if (!ReadValidCasusBelliConfigurationArray(
          bindings, configuration_data, configuration_count)) {
    return false;
  }
  const bool combined =
      configuration_count == 0 ||
      (LoadAt<std::uint32_t>(casus_belli_type,
                             kCasusBelliTypeFlagsOffset) &
       kCasusBelliCombinedConfigurationsFlag) != 0;
  if (combined) {
    DeclarableWarSnapshot choice{};
    choice.target_character_id = target_character_id;
    choice.casus_belli_index = casus_belli_index;
    choice.casus_belli_key = casus_belli_key;
    choice.configuration_index = -1;
    choice.claimant_character_id = -1;
    for (std::int32_t index = 0; index < configuration_count; ++index) {
      const auto *const configuration =
          static_cast<const std::byte *>(configuration_data) +
          static_cast<std::size_t>(index) *
              kValidCasusBelliConfigurationSize;
      std::vector<std::int32_t> target_title_ids;
      if (!ReadNativeIntArray(
              configuration + kValidCasusBelliTargetTitlesOffset,
              target_title_ids)) {
        return false;
      }
      choice.target_title_ids.insert(choice.target_title_ids.end(),
                                     target_title_ids.begin(),
                                     target_title_ids.end());
    }
    output.push_back(std::move(choice));
    return true;
  }

  for (std::int32_t index = 0; index < configuration_count; ++index) {
    const auto *const configuration =
        static_cast<const std::byte *>(configuration_data) +
        static_cast<std::size_t>(index) *
            kValidCasusBelliConfigurationSize;
    DeclarableWarSnapshot choice{};
    choice.target_character_id = target_character_id;
    choice.casus_belli_index = casus_belli_index;
    choice.casus_belli_key = casus_belli_key;
    choice.configuration_index = index;
    choice.claimant_character_id = LoadAt<std::int32_t>(
        configuration, kValidCasusBelliClaimantOffset);
    if (!ReadNativeIntArray(
            configuration + kValidCasusBelliTargetTitlesOffset,
            choice.target_title_ids)) {
      return false;
    }
    // CDeclareWarInteractionWindow creates no selectable item for an empty
    // per-configuration target-title vector (RVA 0x10865E5).
    if (!choice.target_title_ids.empty()) {
      output.push_back(std::move(choice));
    }
  }
  return true;
}

bool ReadDeclarableWarsForTargetInternal(
    const Bindings &bindings, void *casus_belli_database,
    void *attacker_character, void *target_character,
    std::int32_t target_character_id,
    std::vector<DeclarableWarSnapshot> &output) noexcept {
  void *casus_belli_types = nullptr;
  std::int32_t casus_belli_type_count = 0;
  if (!ReadCasusBelliDatabase(casus_belli_database, casus_belli_types,
                              casus_belli_type_count)) {
    return false;
  }
  for (std::int32_t index = 0; index < casus_belli_type_count; ++index) {
    void *const casus_belli_type = LoadAt<void *>(
        casus_belli_types,
        static_cast<std::size_t>(index) * sizeof(void *));
    if (!IsEnabledCasusBelliType(casus_belli_type)) {
      continue;
    }
    if (!ClearValidCasusBelliConfigurations(bindings)) {
      return false;
    }
    const bool available = bindings.evaluate_casus_belli(
        casus_belli_type, attacker_character, target_character,
        bindings.valid_casus_belli_configuration_scratch, false, false,
        nullptr);
    if (available && !MaterializeCasusBelliChoices(
                         bindings, casus_belli_type, target_character_id,
                         index, output)) {
      ClearValidCasusBelliConfigurations(bindings);
      return false;
    }
    if (!ClearValidCasusBelliConfigurations(bindings)) {
      return false;
    }
  }
  return true;
}

void *ResolveArmy(const Bindings &bindings, std::int32_t army_id) noexcept {
  if (army_id == -1 || bindings.army_storage_slot == nullptr) {
    return nullptr;
  }
  void *const storage = *bindings.army_storage_slot;
  if (storage == nullptr) {
    return nullptr;
  }
  void *const slots = LoadAt<void *>(storage, kComponentStorageSlotsOffset);
  const std::int32_t capacity =
      LoadAt<std::int32_t>(storage, kComponentStorageCapacityOffset);
  const std::uint32_t index =
      static_cast<std::uint32_t>(army_id) & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentCapacity ||
      index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  const auto slot_offset = static_cast<std::size_t>(index) *
                               kComponentStorageSlotSize +
                           kComponentStorageSlotObjectOffset;
  void *const army = LoadAt<void *>(slots, slot_offset);
  if (army == nullptr || LoadAt<std::int32_t>(army, kArmyIdOffset) != army_id) {
    return nullptr;
  }
  return army;
}

void *ResolveProvince(void *game_state, std::int32_t province_id) noexcept {
  if (game_state == nullptr || province_id < 1) {
    return nullptr;
  }
  void *const game_data =
      LoadAt<void *>(game_state, kGameStateGameDataOffset);
  if (game_data == nullptr) {
    return nullptr;
  }
  void *const provinces =
      LoadAt<void *>(game_data, kGameDataProvinceArrayOffset);
  const std::int32_t province_count =
      LoadAt<std::int32_t>(game_data, kGameDataProvinceCountOffset);
  if (provinces == nullptr || province_count <= 1 ||
      province_id >= province_count) {
    return nullptr;
  }
  void *const province = LoadAt<void *>(
      provinces, static_cast<std::size_t>(province_id) * sizeof(void *));
  if (province == nullptr ||
      LoadAt<std::int32_t>(province, kProvinceIdOffset) != province_id) {
    return nullptr;
  }
  return province;
}

void *ResolveSiege(const Bindings &bindings,
                   std::int32_t siege_id) noexcept {
  if (siege_id == -1 || bindings.siege_storage_slot == nullptr ||
      bindings.is_native_component_alive == nullptr) {
    return nullptr;
  }
  void *const storage = *bindings.siege_storage_slot;
  if (storage == nullptr) {
    return nullptr;
  }
  void *const slots = LoadAt<void *>(storage, kComponentStorageSlotsOffset);
  const auto capacity =
      LoadAt<std::int32_t>(storage, kComponentStorageCapacityOffset);
  const auto index =
      static_cast<std::uint32_t>(siege_id) & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentCapacity ||
      index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  void *const siege = LoadAt<void *>(
      slots, static_cast<std::size_t>(index) * kComponentStorageSlotSize +
                 kComponentStorageSlotObjectOffset);
  if (siege == nullptr ||
      LoadAt<std::int32_t>(siege, kSiegeIdOffset) != siege_id ||
      !bindings.is_native_component_alive(siege)) {
    return nullptr;
  }
  return siege;
}

void *ResolveLandedTitle(const Bindings &bindings, void *game_state,
                         std::int32_t title_id) noexcept {
  if (game_state == nullptr || title_id == -1) {
    return nullptr;
  }
  void *const game_data =
      LoadAt<void *>(game_state, kGameStateGameDataOffset);
  if (game_data == nullptr) {
    return nullptr;
  }
  auto *const title_manager = static_cast<std::byte *>(game_data) +
                              bindings.landed_title_manager_offset;
  void *const storage =
      LoadAt<void *>(title_manager, kLandedTitleStorageOffset);
  if (storage == nullptr) {
    return nullptr;
  }
  void *const slots = LoadAt<void *>(storage, kComponentStorageSlotsOffset);
  const auto capacity =
      LoadAt<std::int32_t>(storage, kComponentStorageCapacityOffset);
  const auto index = static_cast<std::uint32_t>(title_id) & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentCapacity ||
      index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  void *const title = LoadAt<void *>(
      slots, static_cast<std::size_t>(index) * kComponentStorageSlotSize +
                 kComponentStorageSlotObjectOffset);
  if (title == nullptr ||
      LoadAt<std::int32_t>(title, kLandedTitleIdOffset) != title_id) {
    return nullptr;
  }
  return title;
}

bool AppendUniqueWarObjectiveProvinceId(
    std::vector<std::int32_t> &province_ids,
    std::int32_t province_id) noexcept {
  if (std::find(province_ids.begin(), province_ids.end(), province_id) !=
      province_ids.end()) {
    return true;
  }
  if (province_ids.size() >= kMaximumWarObjectiveProvinceIds) {
    return false;
  }
  province_ids.push_back(province_id);
  return true;
}

bool CollectWarObjectiveProvinceIds(
    const Bindings &bindings, void *game_state, std::int32_t title_id,
    bool is_target_root, std::size_t depth,
    std::size_t &remaining_title_budget,
    std::vector<std::int32_t> &visited_title_ids,
    std::vector<std::int32_t> &province_ids) noexcept {
  if (depth > kMaximumLandedTitleHierarchyDepth) {
    return false;
  }
  if (std::find(visited_title_ids.begin(), visited_title_ids.end(),
                title_id) != visited_title_ids.end()) {
    return false;
  }
  if (remaining_title_budget == 0) {
    return false;
  }
  void *const title = ResolveLandedTitle(bindings, game_state, title_id);
  if (title == nullptr) {
    return false;
  }
  --remaining_title_budget;
  visited_title_ids.push_back(title_id);

  void *const title_template =
      LoadAt<void *>(title, kLandedTitleTemplateOffset);
  if (title_template == nullptr) {
    return false;
  }
  const auto title_tier = LoadAt<std::int32_t>(
      title_template, kLandedTitleTemplateTierOffset);
  if (title_tier == kBaronyTitleTier) {
    if (!is_target_root) {
      return false;
    }
    const auto province_id = LoadAt<std::int32_t>(
        title_template, kLandedTitleTemplateProvinceIdOffset);
    return ResolveProvince(game_state, province_id) != nullptr &&
           AppendUniqueWarObjectiveProvinceId(province_ids, province_id);
  }

  std::vector<std::int32_t> de_jure_vassal_ids;
  if (!ReadNativeIntArray(
          static_cast<std::byte *>(title) +
              kLandedTitleDeJureVassalIdsOffset,
          de_jure_vassal_ids, kMaximumWarObjectiveTitleIds)) {
    return false;
  }
  if (title_tier == kCountyTitleTier) {
    if (de_jure_vassal_ids.empty()) {
      return false;
    }
    const auto capital_barony_title_id = de_jure_vassal_ids.front();
    if (remaining_title_budget == 0 ||
        std::find(visited_title_ids.begin(), visited_title_ids.end(),
                  capital_barony_title_id) != visited_title_ids.end()) {
      return false;
    }
    void *const capital_barony = ResolveLandedTitle(
        bindings, game_state, capital_barony_title_id);
    if (capital_barony == nullptr) {
      return false;
    }
    --remaining_title_budget;
    visited_title_ids.push_back(capital_barony_title_id);
    void *const barony_template =
        LoadAt<void *>(capital_barony, kLandedTitleTemplateOffset);
    if (barony_template == nullptr ||
        LoadAt<std::int32_t>(barony_template,
                             kLandedTitleTemplateTierOffset) !=
            kBaronyTitleTier) {
      return false;
    }
    const auto province_id = LoadAt<std::int32_t>(
        barony_template, kLandedTitleTemplateProvinceIdOffset);
    return ResolveProvince(game_state, province_id) != nullptr &&
           AppendUniqueWarObjectiveProvinceId(province_ids, province_id);
  }
  if (title_tier <= kBaronyTitleTier) {
    return false;
  }

  for (const auto child_title_id : de_jure_vassal_ids) {
    if (!CollectWarObjectiveProvinceIds(
            bindings, game_state, child_title_id, false, depth + 1,
            remaining_title_budget, visited_title_ids, province_ids)) {
      return false;
    }
  }
  return true;
}

void *ResolveWar(const Bindings &bindings, void *game_state,
                 std::int32_t war_id) noexcept {
  if (game_state == nullptr || war_id == -1) {
    return nullptr;
  }
  void *const game_data =
      LoadAt<void *>(game_state, kGameStateGameDataOffset);
  if (game_data == nullptr) {
    return nullptr;
  }
  auto *const war_manager =
      static_cast<std::byte *>(game_data) + bindings.war_manager_offset;
  void *const storage = LoadAt<void *>(war_manager, kWarStorageOffset);
  if (storage == nullptr) {
    return nullptr;
  }
  void *const slots = LoadAt<void *>(storage, kComponentStorageSlotsOffset);
  const auto capacity =
      LoadAt<std::int32_t>(storage, kComponentStorageCapacityOffset);
  const auto index = static_cast<std::uint32_t>(war_id) & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentCapacity ||
      index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  void *const war = LoadAt<void *>(
      slots, static_cast<std::size_t>(index) * kComponentStorageSlotSize +
                 kComponentStorageSlotObjectOffset);
  if (war == nullptr || LoadAt<std::int32_t>(war, kWarIdOffset) != war_id ||
      LoadAt<void *>(war, kWarEndedDataOffset) != nullptr) {
    return nullptr;
  }
  return war;
}

bool HasWarTerminationQueryBindings(const Bindings &bindings) noexcept {
  return bindings.enabled && bindings.game_state_slot != nullptr &&
         bindings.jomini_state_slot != nullptr &&
         bindings.contains_war_participant != nullptr &&
         bindings.default_construct_character_interaction_context != nullptr &&
         bindings.construct_war_resolution_interaction_context != nullptr &&
         bindings.construct_special_character_interaction_context != nullptr &&
         bindings.validate_character_interaction_context != nullptr &&
         bindings.destroy_character_interaction_context != nullptr;
}

bool HasWarTerminationTermsBindings(const Bindings &bindings) noexcept {
  return bindings.enabled && bindings.game_state_slot != nullptr &&
         bindings.jomini_state_slot != nullptr &&
         bindings.character_storage_slot != nullptr &&
         bindings.contains_war_participant != nullptr &&
         bindings.read_character_claim != nullptr &&
         bindings.character_claim_vtable != 0;
}

bool HasWarTerminationExitTermsBindings(const Bindings &bindings) noexcept {
  return HasWarTerminationQueryBindings(bindings) &&
         HasWarTerminationTermsBindings(bindings) &&
         bindings.construct_war_effect_context != nullptr &&
         bindings.populate_war_effect_context != nullptr &&
         bindings.construct_effect_preview_collector != nullptr &&
         bindings.destroy_effect_preview_collector != nullptr &&
         bindings.traverse_loaded_effect != nullptr &&
         bindings.destroy_effect_context_118 != nullptr &&
         bindings.destroy_effect_context_array_row != nullptr &&
         bindings.evaluate_truce_duration_days != nullptr &&
         bindings.get_character_primary_title != nullptr &&
         bindings.read_monthly_gold_income != nullptr &&
         bindings.evaluate_character_interaction_answer != nullptr &&
         bindings.cb_prestige_factor_identifier_id != nullptr &&
         bindings.effect_preview_collector_vtable != 0 &&
         bindings.prestige_effect_vtable != 0 &&
         bindings.prestige_experience_effect_vtable != 0 &&
         bindings.piety_effect_vtable != 0 &&
         bindings.piety_experience_effect_vtable != 0 &&
         bindings.legitimacy_effect_vtable != 0 &&
         bindings.stress_impact_effect_vtable != 0 &&
         bindings.add_from_contribution_attackers_effect_vtable != 0 &&
         bindings.add_from_contribution_defenders_effect_vtable != 0 &&
         bindings.gold_transfer_effect_vtable != 0 &&
         bindings.truce_effect_vtable != 0;
}

void *ResolveTermsCharacter(const Bindings &bindings,
                            std::int32_t character_id) noexcept {
  if (character_id == -1 || bindings.character_storage_slot == nullptr) {
    return nullptr;
  }
  void *const storage = *bindings.character_storage_slot;
  if (storage == nullptr) {
    return nullptr;
  }
  const auto capacity =
      LoadAt<std::int32_t>(storage, kComponentStorageCapacityOffset);
  if (capacity <= 0 || capacity > kMaximumComponentCapacity) {
    return nullptr;
  }
  return ResolveCharacter(bindings, character_id);
}

bool ReadWarClaimRow(const Bindings &bindings, void *claimant, void *title,
                     std::int32_t title_id,
                     game::WarClaimSnapshot &output) noexcept {
  output = {};
  CharacterClaimStorage storage{};
  void *const claim = storage.bytes.data();
  void *const returned =
      bindings.read_character_claim(claim, claimant, title);
  const auto present_raw = LoadAt<std::uint8_t>(claim, 0x10);
  if (returned != claim || present_raw > 1) {
    return false;
  }

  output.title_id = title_id;
  output.present = present_raw != 0;
  if (!output.present) {
    output.state = "absent";
    return true;
  }

  const auto strong_raw = LoadAt<std::uint8_t>(claim, 0x0C);
  const auto implicit_raw = LoadAt<std::uint8_t>(claim, 0x0D);
  auto **const vtable = LoadAt<void **>(claim, 0x00);
  if (reinterpret_cast<std::uintptr_t>(vtable) !=
          bindings.character_claim_vtable ||
      vtable == nullptr || vtable[0] == nullptr) {
    return false;
  }
  const bool fields_valid =
      strong_raw <= 1 && implicit_raw <= 1 &&
      LoadAt<std::int32_t>(claim, 0x08) == title_id;
  if (fields_valid) {
    output.strong = strong_raw != 0;
    output.implicit = implicit_raw != 0;
    if (output.strong) {
      output.state =
          output.implicit ? "strong_implicit" : "strong_explicit";
    } else {
      output.state =
          output.implicit ? "weak_implicit" : "weak_explicit";
    }
  }
  using DestroyCharacterClaim = void *(*)(void *, std::int32_t);
  reinterpret_cast<DestroyCharacterClaim>(vtable[0])(claim, 0);
  return fields_valid;
}

bool ReadPreviewCharacterScope(const Bindings &bindings, const void *scope,
                               std::int32_t &character_id) noexcept {
  if (scope == nullptr || LoadAt<std::uint16_t>(scope, 0x00) != 4) {
    return false;
  }
  const auto candidate = LoadAt<std::int32_t>(scope, 0x08);
  if (candidate <= 0 || ResolveTermsCharacter(bindings, candidate) == nullptr) {
    return false;
  }
  character_id = candidate;
  return true;
}

bool ClassifyWarExitPreviewNode(const Bindings &bindings,
                                const void *effect_node,
                                WarExitPreviewRowKind &kind) noexcept {
  if (effect_node == nullptr) {
    return false;
  }
  const auto vtable = LoadAt<std::uintptr_t>(effect_node, 0x00);
  if (vtable == bindings.prestige_effect_vtable) {
    kind = WarExitPreviewRowKind::prestige;
  } else if (vtable == bindings.prestige_experience_effect_vtable) {
    kind = WarExitPreviewRowKind::prestige_experience;
  } else if (vtable == bindings.piety_effect_vtable) {
    kind = WarExitPreviewRowKind::piety;
  } else if (vtable == bindings.piety_experience_effect_vtable) {
    kind = WarExitPreviewRowKind::piety_experience;
  } else if (vtable == bindings.legitimacy_effect_vtable) {
    kind = WarExitPreviewRowKind::legitimacy;
  } else if (vtable == bindings.stress_impact_effect_vtable) {
    kind = WarExitPreviewRowKind::stress;
  } else if (vtable == bindings.gold_transfer_effect_vtable) {
    kind = WarExitPreviewRowKind::gold_transfer;
  } else if (vtable == bindings.truce_effect_vtable) {
    kind = WarExitPreviewRowKind::truce;
  } else {
    return false;
  }
  return true;
}

bool CaptureWarExitPrestigeFactor(WarExitPreviewCapture &capture,
                                  const void *wrapper) noexcept {
  if (wrapper == nullptr || capture.factor_identifier_id < 0 ||
      capture.factor_found) {
    SetWarExitPreviewUnavailableReason("dry_preview.factor_preconditions");
    return false;
  }
  void *const variables = LoadAt<void *>(wrapper, 0x18);
  if (variables == nullptr) {
    SetWarExitPreviewUnavailableReason("dry_preview.factor_container");
    return false;
  }
  void *const data = LoadAt<void *>(variables, 0x00);
  const auto capacity = LoadAt<std::int32_t>(variables, 0x08);
  const auto count = LoadAt<std::int32_t>(variables, 0x0C);
  if (capacity < 0 || count < 0 || count > capacity ||
      count > kMaximumComponentCapacity || (count > 0 && data == nullptr)) {
    SetWarExitPreviewUnavailableReason("dry_preview.factor_span");
    return false;
  }
  bool found = false;
  std::int64_t raw = 0;
  for (std::int32_t index = 0; index < count; ++index) {
    const auto *const row = static_cast<const std::byte *>(data) +
                            static_cast<std::size_t>(index) * 0x20;
    if (LoadAt<std::int32_t>(row, 0x00) !=
        capture.factor_identifier_id) {
      continue;
    }
    if (found || LoadAt<std::uint16_t>(row, 0x08) != 1 ||
        LoadAt<std::uint16_t>(row, 0x0A) != 0 ||
        LoadAt<std::uint8_t>(row, 0x18) != 0) {
      SetWarExitPreviewUnavailableReason("dry_preview.factor_row");
      return false;
    }
    raw = LoadAt<std::int64_t>(row, 0x10);
    found = true;
  }
  if (!found) {
    SetWarExitPreviewUnavailableReason("dry_preview.factor_missing");
    return false;
  }
  capture.factor_raw = raw;
  capture.factor_found = true;
  return true;
}

bool ReadExactWarExitEffectChildren(
    void *effect, std::int32_t expected_count,
    std::int32_t expected_capacity, void *&children,
    std::string_view reason) noexcept {
  children = nullptr;
  if (effect == nullptr) {
    SetWarExitPreviewUnavailableReason(reason);
    return false;
  }
  void *const data = LoadAt<void *>(effect, 0x40);
  const auto capacity = LoadAt<std::int32_t>(effect, 0x48);
  const auto count = LoadAt<std::int32_t>(effect, 0x4C);
  if (count != expected_count || capacity != expected_capacity ||
      (expected_count > 0 && data == nullptr)) {
    SetWarExitPreviewUnavailableReason(reason);
    return false;
  }
  children = data;
  return true;
}

bool ResolveWarExitHiddenTrucePath(
    const Bindings &bindings, void *root_effect,
    WarExitHiddenTrucePath &path) noexcept {
  path = {};
  auto **const root_vtable =
      root_effect == nullptr ? nullptr : LoadAt<void **>(root_effect, 0x00);
  if (reinterpret_cast<std::uintptr_t>(root_vtable) !=
      bindings.jomini_effect_vtable) {
    SetWarExitPreviewUnavailableReason(
        "dry_preview.hidden_truce.root_vtable");
    return false;
  }
  void *root_children = nullptr;
  if (!ReadExactWarExitEffectChildren(
          root_effect, 10, 13, root_children,
          "dry_preview.hidden_truce.root_span")) {
    return false;
  }

  void *const scripted_effect =
      LoadAt<void *>(root_children, 8 * sizeof(void *));
  if (scripted_effect == nullptr ||
      LoadAt<std::uintptr_t>(scripted_effect, 0x00) !=
          bindings.jomini_scripted_effect_vtable) {
    SetWarExitPreviewUnavailableReason(
        "dry_preview.hidden_truce.root_child8");
    return false;
  }
  if (LoadAt<std::int32_t>(scripted_effect, 0x94) != 0) {
    SetWarExitPreviewUnavailableReason(
        "dry_preview.hidden_truce.selector_count");
    return false;
  }
  void *const scripted_template = LoadAt<void *>(scripted_effect, 0x60);
  if (scripted_template == nullptr ||
      LoadAt<std::uintptr_t>(scripted_template, 0x00) !=
          bindings.jomini_scripted_effect_template_vtable) {
    SetWarExitPreviewUnavailableReason(
        "dry_preview.hidden_truce.template_vtable");
    return false;
  }
  void *const default_effect = LoadAt<void *>(scripted_template, 0x120);
  if (default_effect == nullptr ||
      LoadAt<std::uintptr_t>(default_effect, 0x00) !=
          bindings.jomini_effect_vtable) {
    SetWarExitPreviewUnavailableReason(
        "dry_preview.hidden_truce.default_vtable");
    return false;
  }
  void *default_children = nullptr;
  if (!ReadExactWarExitEffectChildren(
          default_effect, 5, 6, default_children,
          "dry_preview.hidden_truce.default_span")) {
    return false;
  }

  void *const hidden_effect =
      LoadAt<void *>(default_children, 2 * sizeof(void *));
  if (hidden_effect == nullptr ||
      LoadAt<std::uintptr_t>(hidden_effect, 0x00) !=
          bindings.hidden_effect_vtable) {
    SetWarExitPreviewUnavailableReason(
        "dry_preview.hidden_truce.hidden_vtable");
    return false;
  }
  void *hidden_children = nullptr;
  if (!ReadExactWarExitEffectChildren(
          hidden_effect, 1, 1, hidden_children,
          "dry_preview.hidden_truce.hidden_span")) {
    return false;
  }

  void *const context_effect = LoadAt<void *>(hidden_children, 0x00);
  if (context_effect == nullptr ||
      LoadAt<std::uintptr_t>(context_effect, 0x00) !=
          bindings.jomini_context_effect_vtable) {
    SetWarExitPreviewUnavailableReason(
        "dry_preview.hidden_truce.context_vtable");
    return false;
  }
  void *context_children = nullptr;
  if (!ReadExactWarExitEffectChildren(
          context_effect, 1, 1, context_children,
          "dry_preview.hidden_truce.context_span")) {
    return false;
  }
  if (LoadAt<void *>(context_effect, 0x60) == nullptr ||
      LoadAt<std::int32_t>(context_effect, 0x6C) != 1) {
    SetWarExitPreviewUnavailableReason(
        "dry_preview.hidden_truce.context_scope");
    return false;
  }

  void *const truce_effect = LoadAt<void *>(context_children, 0x00);
  if (truce_effect == nullptr ||
      LoadAt<std::uintptr_t>(truce_effect, 0x00) !=
          bindings.truce_effect_vtable) {
    SetWarExitPreviewUnavailableReason(
        "dry_preview.hidden_truce.truce_vtable");
    return false;
  }
  auto **const context_vtable = LoadAt<void **>(context_effect, 0x00);
  if (context_vtable[11] == nullptr || root_vtable[11] == nullptr ||
      context_vtable[11] != root_vtable[11]) {
    SetWarExitPreviewUnavailableReason(
        "dry_preview.hidden_truce.preview_slot");
    return false;
  }
  path.root_effect = root_effect;
  path.root_children = root_children;
  path.scripted_effect = scripted_effect;
  path.scripted_template = scripted_template;
  path.default_effect = default_effect;
  path.default_children = default_children;
  path.hidden_effect = hidden_effect;
  path.hidden_children = hidden_children;
  path.context_effect = context_effect;
  return true;
}

bool BuildWarExitHiddenTruceProjection(
    const Bindings &bindings, const WarExitHiddenTrucePath &path,
    WarExitHiddenTruceProjection &projection,
    void *&projected_root_effect) noexcept {
  projected_root_effect = nullptr;
  if (path.root_effect == nullptr || path.root_children == nullptr ||
      path.scripted_effect == nullptr || path.scripted_template == nullptr ||
      path.default_effect == nullptr || path.default_children == nullptr ||
      path.hidden_effect == nullptr || path.hidden_children == nullptr ||
      path.context_effect == nullptr) {
    SetWarExitPreviewUnavailableReason(
        "dry_preview.hidden_truce.projection_preconditions");
    return false;
  }

  std::memcpy(projection.root_effect.data(), path.root_effect,
              projection.root_effect.size());
  std::memcpy(projection.scripted_effect.data(), path.scripted_effect,
              projection.scripted_effect.size());
  std::memcpy(projection.scripted_template.data(), path.scripted_template,
              projection.scripted_template.size());
  std::memcpy(projection.default_effect.data(), path.default_effect,
              projection.default_effect.size());

  for (std::size_t index = 0; index < 10; ++index) {
    void *const child =
        LoadAt<void *>(path.root_children, index * sizeof(void *));
    if (child == nullptr) {
      SetWarExitPreviewUnavailableReason(
          "dry_preview.hidden_truce.projection_root_child");
      return false;
    }
    projection.root_children[index] = child;
  }
  for (std::size_t index = 0; index < 5; ++index) {
    void *const child =
        LoadAt<void *>(path.default_children, index * sizeof(void *));
    if (child == nullptr) {
      SetWarExitPreviewUnavailableReason(
          "dry_preview.hidden_truce.projection_default_child");
      return false;
    }
    projection.default_children[index] = child;
  }

  projection.root_children[8] = projection.scripted_effect.data();
  projection.default_children[2] = path.context_effect;
  StoreAt(projection.root_effect.data(), 0x40,
          static_cast<void *>(projection.root_children.data()));
  StoreAt(projection.scripted_effect.data(), 0x60,
          static_cast<void *>(projection.scripted_template.data()));
  StoreAt(projection.scripted_template.data(), 0x120,
          static_cast<void *>(projection.default_effect.data()));
  StoreAt(projection.default_effect.data(), 0x40,
          static_cast<void *>(projection.default_children.data()));

  if (LoadAt<std::uintptr_t>(projection.root_effect.data(), 0x00) !=
          bindings.jomini_effect_vtable ||
      LoadAt<std::int32_t>(projection.root_effect.data(), 0x48) != 13 ||
      LoadAt<std::int32_t>(projection.root_effect.data(), 0x4C) != 10 ||
      LoadAt<void *>(projection.root_effect.data(), 0x40) !=
          projection.root_children.data() ||
      projection.root_children[8] != projection.scripted_effect.data() ||
      LoadAt<std::uintptr_t>(projection.scripted_effect.data(), 0x00) !=
          bindings.jomini_scripted_effect_vtable ||
      LoadAt<void *>(projection.scripted_effect.data(), 0x60) !=
          projection.scripted_template.data() ||
      LoadAt<std::int32_t>(projection.scripted_effect.data(), 0x94) != 0 ||
      LoadAt<std::uintptr_t>(projection.scripted_template.data(), 0x00) !=
          bindings.jomini_scripted_effect_template_vtable ||
      LoadAt<void *>(projection.scripted_template.data(), 0x120) !=
          projection.default_effect.data() ||
      LoadAt<std::uintptr_t>(projection.default_effect.data(), 0x00) !=
          bindings.jomini_effect_vtable ||
      LoadAt<std::int32_t>(projection.default_effect.data(), 0x48) != 6 ||
      LoadAt<std::int32_t>(projection.default_effect.data(), 0x4C) != 5 ||
      LoadAt<void *>(projection.default_effect.data(), 0x40) !=
          projection.default_children.data() ||
      projection.default_children[2] != path.context_effect ||
      LoadAt<std::uintptr_t>(projection.default_children[2], 0x00) !=
          bindings.jomini_context_effect_vtable) {
    SetWarExitPreviewUnavailableReason(
        "dry_preview.hidden_truce.projection_readback");
    return false;
  }
  for (std::size_t index = 0; index < 10; ++index) {
    if (index != 8 && projection.root_children[index] !=
                          LoadAt<void *>(path.root_children,
                                         index * sizeof(void *))) {
      SetWarExitPreviewUnavailableReason(
          "dry_preview.hidden_truce.projection_root_identity");
      return false;
    }
  }
  for (std::size_t index = 0; index < 5; ++index) {
    if (index != 2 && projection.default_children[index] !=
                          LoadAt<void *>(path.default_children,
                                         index * sizeof(void *))) {
      SetWarExitPreviewUnavailableReason(
          "dry_preview.hidden_truce.projection_default_identity");
      return false;
    }
  }
  projected_root_effect = projection.root_effect.data();
  return true;
}

void SetWarExitAttackerDefeatShapeReason(
    const Bindings &bindings, void *root_effect) noexcept {
  if (!g_last_war_exit_preview_unavailable_reason.empty()) {
    return;
  }

  const auto module = bindings.truce_effect_vtable - kTruceEffectVtableRva;
  const auto effect_vtable =
      root_effect == nullptr
          ? std::uintptr_t{0}
          : LoadAt<std::uintptr_t>(root_effect, 0x00);
  bool diagnostic_complete = true;
  std::size_t used = 0;
  const auto append = [&](const char *format, const auto... values) noexcept {
    if (!diagnostic_complete) {
      return;
    }
    const int written = std::snprintf(
        g_war_exit_preview_diagnostic_buffer.data() + used,
        g_war_exit_preview_diagnostic_buffer.size() - used, format,
        values...);
    if (written <= 0 ||
        static_cast<std::size_t>(written) >=
            g_war_exit_preview_diagnostic_buffer.size() - used) {
      diagnostic_complete = false;
      return;
    }
    used += static_cast<std::size_t>(written);
  };
  const auto vtable_rva = [module](const void *effect) noexcept {
    if (effect == nullptr) {
      return std::uintptr_t{0};
    }
    const auto vtable = LoadAt<std::uintptr_t>(effect, 0x00);
    return vtable >= module ? vtable - module : std::uintptr_t{0};
  };

  append("dry_preview.hidden_truce.attacker_defeat_shape:"
         "root=0x%llX,root_span=%d/%d,root_children=",
         static_cast<unsigned long long>(
             g_war_exit_loaded_root_vtable_rva),
         g_war_exit_loaded_root_count, g_war_exit_loaded_root_capacity);
  const auto root_child_count =
      g_war_exit_loaded_root_count > 0
          ? std::min<std::size_t>(
                static_cast<std::size_t>(g_war_exit_loaded_root_count),
                kMaximumWarExitDiagnosticRootChildren)
          : std::size_t{0};
  for (std::size_t index = 0; index < root_child_count; ++index) {
    append("%s%llu=0x%llX@0x%llX", index == 0 ? "" : "/",
           static_cast<unsigned long long>(index),
           static_cast<unsigned long long>(
               g_war_exit_loaded_root_child_pointers[index]),
           static_cast<unsigned long long>(
               g_war_exit_loaded_root_child_vtable_rvas[index]));
  }

  std::int32_t selector_count = -1;
  void *scripted_template = nullptr;
  std::uintptr_t scripted_template_vtable_rva = 0;
  void *default_effect = nullptr;
  std::uintptr_t default_vtable_rva = 0;
  void *default_children = nullptr;
  std::int32_t default_capacity = -1;
  std::int32_t default_count = -1;
  std::array<std::uintptr_t, kMaximumWarExitDiagnosticRootChildren>
      default_child_pointers{};
  std::array<std::uintptr_t, kMaximumWarExitDiagnosticRootChildren>
      default_child_vtable_rvas{};
  std::int32_t hidden_count = -1;
  std::int32_t hidden_index = -1;
  std::int32_t hidden_capacity = -1;
  std::int32_t hidden_child_count = -1;
  void *hidden_child0 = nullptr;
  std::uintptr_t hidden_child0_vtable_rva = 0;
  std::int32_t context_capacity = -1;
  std::int32_t context_child_count = -1;
  std::int32_t context_scope_count = -1;
  void *context_child0 = nullptr;
  std::uintptr_t context_child0_vtable_rva = 0;

  constexpr std::size_t kAttackerDefeatTruceRootIndex = 9;
  void *const scripted_effect =
      root_child_count > kAttackerDefeatTruceRootIndex
          ? reinterpret_cast<void *>(
                g_war_exit_loaded_root_child_pointers[
                    kAttackerDefeatTruceRootIndex])
          : nullptr;
  const auto scripted_effect_vtable_rva =
      root_child_count > kAttackerDefeatTruceRootIndex
          ? g_war_exit_loaded_root_child_vtable_rvas[
                kAttackerDefeatTruceRootIndex]
          : std::uintptr_t{0};
  if (effect_vtable == bindings.jomini_effect_vtable &&
      scripted_effect != nullptr &&
      LoadAt<std::uintptr_t>(scripted_effect, 0x00) ==
          bindings.jomini_scripted_effect_vtable) {
    selector_count = LoadAt<std::int32_t>(scripted_effect, 0x94);
    scripted_template = LoadAt<void *>(scripted_effect, 0x60);
    scripted_template_vtable_rva = vtable_rva(scripted_template);
    if (selector_count == 0 && scripted_template != nullptr &&
        LoadAt<std::uintptr_t>(scripted_template, 0x00) ==
            bindings.jomini_scripted_effect_template_vtable) {
      default_effect = LoadAt<void *>(scripted_template, 0x120);
      default_vtable_rva = vtable_rva(default_effect);
      if (default_effect != nullptr &&
          LoadAt<std::uintptr_t>(default_effect, 0x00) ==
              bindings.jomini_effect_vtable) {
        default_children = LoadAt<void *>(default_effect, 0x40);
        default_capacity = LoadAt<std::int32_t>(default_effect, 0x48);
        default_count = LoadAt<std::int32_t>(default_effect, 0x4C);
        constexpr std::int32_t kMaximumDiagnosticEffectChildren = 512;
        if (default_capacity < 0 || default_count < 0 ||
            default_count > default_capacity ||
            default_capacity > kMaximumDiagnosticEffectChildren ||
            (default_count > 0 && default_children == nullptr)) {
          default_capacity = -2;
          default_count = -2;
        } else {
          hidden_count = 0;
          const auto captured_default_count = std::min<std::size_t>(
              static_cast<std::size_t>(default_count),
              kMaximumWarExitDiagnosticRootChildren);
          for (std::size_t index = 0; index < captured_default_count;
               ++index) {
            void *const child = LoadAt<void *>(
                default_children, index * sizeof(void *));
            default_child_pointers[index] =
                reinterpret_cast<std::uintptr_t>(child);
            default_child_vtable_rvas[index] = vtable_rva(child);
            if (child != nullptr &&
                LoadAt<std::uintptr_t>(child, 0x00) ==
                    bindings.hidden_effect_vtable) {
              ++hidden_count;
              hidden_index = static_cast<std::int32_t>(index);
            }
          }
          if (hidden_count == 1 && hidden_index >= 0) {
            void *const hidden_effect = LoadAt<void *>(
                default_children,
                static_cast<std::size_t>(hidden_index) * sizeof(void *));
            void *const hidden_children =
                LoadAt<void *>(hidden_effect, 0x40);
            hidden_capacity = LoadAt<std::int32_t>(hidden_effect, 0x48);
            hidden_child_count =
                LoadAt<std::int32_t>(hidden_effect, 0x4C);
            if (hidden_capacity == 1 && hidden_child_count == 1 &&
                hidden_children != nullptr) {
              hidden_child0 = LoadAt<void *>(hidden_children, 0x00);
              hidden_child0_vtable_rva = vtable_rva(hidden_child0);
              if (hidden_child0 != nullptr &&
                  LoadAt<std::uintptr_t>(hidden_child0, 0x00) ==
                      bindings.jomini_context_effect_vtable) {
                void *const context_children =
                    LoadAt<void *>(hidden_child0, 0x40);
                context_capacity =
                    LoadAt<std::int32_t>(hidden_child0, 0x48);
                context_child_count =
                    LoadAt<std::int32_t>(hidden_child0, 0x4C);
                context_scope_count =
                    LoadAt<std::int32_t>(hidden_child0, 0x6C);
                if (context_capacity == 1 && context_child_count == 1 &&
                    context_children != nullptr) {
                  context_child0 =
                      LoadAt<void *>(context_children, 0x00);
                  context_child0_vtable_rva = vtable_rva(context_child0);
                }
              }
            }
          }
        }
      }
    }
  }

  append(",child9=0x%llX@0x%llX,selector_count=%d,template=0x%llX@0x%llX,"
         "default=0x%llX@0x%llX,default_span=%d/%d,default_children=",
         static_cast<unsigned long long>(
             reinterpret_cast<std::uintptr_t>(scripted_effect)),
         static_cast<unsigned long long>(scripted_effect_vtable_rva),
         selector_count,
         static_cast<unsigned long long>(
             reinterpret_cast<std::uintptr_t>(scripted_template)),
         static_cast<unsigned long long>(scripted_template_vtable_rva),
         static_cast<unsigned long long>(
             reinterpret_cast<std::uintptr_t>(default_effect)),
         static_cast<unsigned long long>(default_vtable_rva), default_count,
         default_capacity);
  if (default_count > 0 && default_count <=
                               static_cast<std::int32_t>(
                                   kMaximumWarExitDiagnosticRootChildren)) {
    for (std::int32_t index = 0; index < default_count; ++index) {
      append("%s%d=0x%llX@0x%llX", index == 0 ? "" : "/", index,
             static_cast<unsigned long long>(
                 default_child_pointers[static_cast<std::size_t>(index)]),
             static_cast<unsigned long long>(
                 default_child_vtable_rvas[
                     static_cast<std::size_t>(index)]));
    }
  }
  append(",hidden=%d@index%d,hidden_span=%d/%d,hidden_child0=0x%llX@0x%llX,"
         "context_span=%d/%d,context_scope_count=%d,"
         "context_child0=0x%llX@0x%llX",
         hidden_count, hidden_index, hidden_child_count, hidden_capacity,
         static_cast<unsigned long long>(
             reinterpret_cast<std::uintptr_t>(hidden_child0)),
         static_cast<unsigned long long>(hidden_child0_vtable_rva),
         context_child_count, context_capacity, context_scope_count,
         static_cast<unsigned long long>(
             reinterpret_cast<std::uintptr_t>(context_child0)),
         static_cast<unsigned long long>(context_child0_vtable_rva));

  if (!diagnostic_complete || used == 0) {
    constexpr std::string_view fallback =
        "dry_preview.hidden_truce.attacker_defeat_shape";
    std::memcpy(g_war_exit_preview_diagnostic_buffer.data(),
                fallback.data(), fallback.size());
    used = fallback.size();
  }
  g_last_war_exit_preview_unavailable_reason = std::string_view(
      g_war_exit_preview_diagnostic_buffer.data(), used);
}

void CaptureWarExitLoadedEffect(
    void *proxy_loaded_effect, void *wrapper, std::uint32_t mode,
    void *collector) noexcept {
  WarExitPreviewCapture *const capture = g_war_exit_preview_capture;
  if (capture == nullptr || capture->original_slot58 == nullptr ||
      proxy_loaded_effect != capture->proxy_loaded_effect ||
      capture->original_loaded_effect == nullptr || wrapper == nullptr ||
      collector == nullptr) {
    if (capture != nullptr) {
      SetWarExitPreviewUnavailableReason("dry_preview.trampoline_context");
      capture->failed = true;
    }
    return;
  }
  if (mode != 0) {
    SetWarExitPreviewUnavailableReason("dry_preview.trampoline_mode");
    capture->failed = true;
    return;
  }
  const auto module = capture->bindings->truce_effect_vtable -
                      kTruceEffectVtableRva;
  const auto root_vtable =
      LoadAt<std::uintptr_t>(capture->original_loaded_effect, 0x00);
  g_war_exit_loaded_root_vtable_rva =
      root_vtable >= module ? root_vtable - module : 0;
  g_war_exit_loaded_root_selector_count = -1;
  g_war_exit_loaded_default_child_vtable_rva = 0;
  g_war_exit_loaded_root_capacity = -1;
  g_war_exit_loaded_root_count = -1;
  g_war_exit_loaded_hidden_count = -1;
  g_war_exit_loaded_hidden_index = -1;
  g_war_exit_loaded_hidden_capacity = -1;
  g_war_exit_loaded_hidden_child_count = -1;
  g_war_exit_loaded_hidden_child0_vtable_rva = 0;
  g_war_exit_loaded_root_child_pointers.fill(0);
  g_war_exit_loaded_root_child_vtable_rvas.fill(0);
  if (root_vtable == capture->bindings->jomini_effect_vtable) {
    const auto root_capacity =
        LoadAt<std::int32_t>(capture->original_loaded_effect, 0x48);
    const auto root_count =
        LoadAt<std::int32_t>(capture->original_loaded_effect, 0x4C);
    void *const root_data =
        LoadAt<void *>(capture->original_loaded_effect, 0x40);
    constexpr std::int32_t kMaximumDiagnosticEffectChildren = 512;
    if (root_capacity < 0 || root_count < 0 ||
        root_count > root_capacity ||
        root_capacity > kMaximumDiagnosticEffectChildren ||
        (root_count > 0 && root_data == nullptr)) {
      g_war_exit_loaded_root_capacity = -2;
      g_war_exit_loaded_root_count = -2;
    } else {
      g_war_exit_loaded_root_capacity = root_capacity;
      g_war_exit_loaded_root_count = root_count;
      g_war_exit_loaded_hidden_count = 0;
      for (std::int32_t index = 0; index < root_count; ++index) {
        void *const child = LoadAt<void *>(
            root_data, static_cast<std::size_t>(index) * sizeof(void *));
        if (child == nullptr) {
          g_war_exit_loaded_hidden_count = -2;
          break;
        }
        const auto child_vtable = LoadAt<std::uintptr_t>(child, 0x00);
        if (static_cast<std::size_t>(index) <
            kMaximumWarExitDiagnosticRootChildren) {
          g_war_exit_loaded_root_child_pointers[static_cast<std::size_t>(
              index)] = reinterpret_cast<std::uintptr_t>(child);
          g_war_exit_loaded_root_child_vtable_rvas[static_cast<std::size_t>(
              index)] = child_vtable >= module ? child_vtable - module : 0;
        }
        if (child_vtable != module + kHiddenEffectVtableRva) {
          continue;
        }
        ++g_war_exit_loaded_hidden_count;
        g_war_exit_loaded_hidden_index = index;
        const auto hidden_capacity = LoadAt<std::int32_t>(child, 0x48);
        const auto hidden_count = LoadAt<std::int32_t>(child, 0x4C);
        void *const hidden_data = LoadAt<void *>(child, 0x40);
        if (hidden_capacity < 0 || hidden_count < 0 ||
            hidden_count > hidden_capacity ||
            hidden_capacity > kMaximumDiagnosticEffectChildren ||
            (hidden_count > 0 && hidden_data == nullptr)) {
          g_war_exit_loaded_hidden_capacity = -2;
          g_war_exit_loaded_hidden_child_count = -2;
          continue;
        }
        g_war_exit_loaded_hidden_capacity = hidden_capacity;
        g_war_exit_loaded_hidden_child_count = hidden_count;
        if (hidden_count > 0) {
          void *const hidden_child0 = LoadAt<void *>(hidden_data, 0x00);
          if (hidden_child0 != nullptr) {
            const auto hidden_child0_vtable =
                LoadAt<std::uintptr_t>(hidden_child0, 0x00);
            g_war_exit_loaded_hidden_child0_vtable_rva =
                hidden_child0_vtable >= module
                    ? hidden_child0_vtable - module
                    : 0;
          }
        }
      }
    }
  }
  if (root_vtable == capture->bindings->jomini_scripted_effect_vtable) {
    g_war_exit_loaded_root_selector_count =
        LoadAt<std::int32_t>(capture->original_loaded_effect, 0x94);
    void *const selector_owner =
        LoadAt<void *>(capture->original_loaded_effect, 0x60);
    if (g_war_exit_loaded_root_selector_count == 0 &&
        selector_owner != nullptr) {
      void *const default_child = LoadAt<void *>(selector_owner, 0x120);
      if (default_child != nullptr) {
        const auto child_vtable =
            LoadAt<std::uintptr_t>(default_child, 0x00);
        g_war_exit_loaded_default_child_vtable_rva =
            child_vtable >= module ? child_vtable - module : 0;
      }
    }
  }
  if (capture->outcome == WarExitPreviewOutcome::attacker_defeat) {
    // final19 is deliberately diagnostic-only for this outcome.  The exact
    // loaded root span is known, but its child array was not present in the
    // final18 crash dump.  Capture the complete direct list and expand only
    // statically identified container vtables; do not invoke any effect until
    // that outcome-specific path has been proven from a paused live object.
    SetWarExitAttackerDefeatShapeReason(
        *capture->bindings, capture->original_loaded_effect);
    capture->failed = true;
    return;
  }
  WarExitHiddenTrucePath hidden_truce_path{};
  if (!ResolveWarExitHiddenTrucePath(
          *capture->bindings, capture->original_loaded_effect,
          hidden_truce_path)) {
    capture->failed = true;
    return;
  }
  WarExitHiddenTruceProjection projection{};
  void *projected_root_effect = nullptr;
  if (!BuildWarExitHiddenTruceProjection(
          *capture->bindings, hidden_truce_path, projection,
          projected_root_effect)) {
    capture->failed = true;
    return;
  }
  capture->original_slot58(projected_root_effect, wrapper, mode, collector);
  if (capture->failed) {
    return;
  }
  const auto truce_rows = static_cast<std::size_t>(std::count_if(
      capture->rows.begin(), capture->rows.end(),
      [](const WarExitPreviewRow &row) {
        return row.kind == WarExitPreviewRowKind::truce;
      }));
  if (truce_rows != 1) {
    SetWarExitPreviewUnavailableReason(
        "dry_preview.hidden_truce.projected_preview_count");
    capture->failed = true;
    return;
  }
  if (!CaptureWarExitPrestigeFactor(*capture, wrapper)) {
    capture->failed = true;
  }
}

void CaptureWarExitPreviewRow(
    void *collector, const void *first_scope, const void *second_scope,
    const PreviewFixedPayload *payload, void *effect_node,
    void *forwarded_argument) noexcept {
  WarExitPreviewCapture *const capture = g_war_exit_preview_capture;
  if (capture == nullptr || capture->bindings == nullptr ||
      capture->original_slot8 == nullptr) {
    SetWarExitPreviewUnavailableReason("dry_preview.capture_context");
    return;
  }

  const auto &bindings = *capture->bindings;
  const auto callback_ordinal = ++capture->callback_ordinal;
  std::int32_t first_character_id = -1;
  const bool first_scope_valid = ReadPreviewCharacterScope(
      bindings, first_scope, first_character_id);
  const auto effect_vtable =
      effect_node == nullptr ? std::uintptr_t{0}
                             : LoadAt<std::uintptr_t>(effect_node, 0x00);
  const bool attacker_contribution =
      effect_vtable ==
      bindings.add_from_contribution_attackers_effect_vtable;
  const bool defender_contribution =
      effect_vtable ==
      bindings.add_from_contribution_defenders_effect_vtable;
  if (attacker_contribution || defender_contribution) {
    // Exact-build registration xrefs bind these two loaded classes to
    // add_from_contribution_attackers/defenders.  In stock claim_cb both are
    // reached exclusively through modify_allies_of_participants_fame_values,
    // whose script contract excludes the primary attacker and defender.  The
    // collector nevertheless anchors its presentation row on that side's
    // primary character, so these rows are forwarded but deliberately stay
    // outside the v2 primary-character resource grid.
    const auto expected_character_id =
        attacker_contribution ? capture->primary_attacker_character_id
                              : capture->primary_defender_character_id;
    if (!first_scope_valid || first_character_id != expected_character_id ||
        second_scope != nullptr || payload == nullptr || payload->tag != 1 ||
        forwarded_argument == nullptr) {
      SetWarExitPreviewUnavailableReason(
          attacker_contribution
              ? "dry_preview.attacker_contribution_row"
              : "dry_preview.defender_contribution_row");
      capture->failed = true;
    }
    capture->original_slot8(collector, first_scope, second_scope, payload,
                            effect_node, forwarded_argument);
    return;
  }
  if (first_scope_valid &&
      first_character_id != capture->primary_attacker_character_id &&
      first_character_id != capture->primary_defender_character_id) {
    // Stock claim_cb previews also visit allies/contingents.  Their rows are
    // outside this deliberately narrow primary-character slice.  Validate
    // the typed full-generation scope, then forward and ignore the row even
    // when it uses a contribution-specific node vtable that this slice does
    // not otherwise consume.  Primary-character unknown nodes still fail
    // closed below.
    capture->original_slot8(collector, first_scope, second_scope, payload,
                            effect_node, forwarded_argument);
    return;
  }

  WarExitPreviewRow row{};
  row.first_character_id = first_character_id;
  const bool node_known =
      ClassifyWarExitPreviewNode(bindings, effect_node, row.kind);
  bool valid = first_scope_valid && node_known;
  switch (row.kind) {
  case WarExitPreviewRowKind::prestige:
  case WarExitPreviewRowKind::prestige_experience:
  case WarExitPreviewRowKind::piety:
  case WarExitPreviewRowKind::piety_experience:
  case WarExitPreviewRowKind::legitimacy:
  case WarExitPreviewRowKind::stress:
    valid = valid && second_scope == nullptr && payload != nullptr &&
            payload->tag == 1;
    if (valid) {
      row.raw = payload->raw;
    }
    break;
  case WarExitPreviewRowKind::gold_transfer:
    valid = valid && payload != nullptr && payload->tag == 1 &&
            ReadPreviewCharacterScope(bindings, second_scope,
                                      row.second_character_id) &&
            forwarded_argument == nullptr;
    if (valid) {
      row.raw = payload->raw;
    }
    break;
  case WarExitPreviewRowKind::truce:
    valid = valid && payload == nullptr &&
            ReadPreviewCharacterScope(bindings, second_scope,
                                      row.second_character_id) &&
            forwarded_argument == nullptr;
    break;
  }
  row.effect_node = effect_node;
  if (valid) {
    try {
      capture->rows.push_back(row);
    } catch (...) {
      SetWarExitPreviewUnavailableReason("dry_preview.capture_allocation");
      capture->failed = true;
    }
  } else {
    if (node_known) {
      SetWarExitPreviewUnavailableReason("dry_preview.capture_row");
    } else {
      SetUnknownWarExitPreviewRowReason(
          effect_node, first_scope, second_scope, payload,
          forwarded_argument, callback_ordinal);
    }
    capture->failed = true;
  }

  capture->original_slot8(collector, first_scope, second_scope, payload,
                          effect_node, forwarded_argument);
}

using NativeAllocatorFree = void (*)(void *allocator, void *data,
                                     std::uint64_t alignment);

bool FreeEffectContextArray(void *context, std::size_t data_offset,
                            std::size_t count_offset,
                            std::size_t allocator_offset) noexcept {
  void *const data = LoadAt<void *>(context, data_offset);
  if (data == nullptr) {
    return true;
  }
  void *const allocator = LoadAt<void *>(context, allocator_offset);
  auto **const allocator_vtable =
      allocator == nullptr ? nullptr : LoadAt<void **>(allocator, 0x00);
  if (allocator_vtable == nullptr || allocator_vtable[2] == nullptr) {
    return false;
  }
  StoreAt(context, count_offset, std::int32_t{0});
  reinterpret_cast<NativeAllocatorFree>(allocator_vtable[2])(
      allocator, data, 8);
  StoreAt(context, data_offset, static_cast<void *>(nullptr));
  return true;
}

bool DestroyWarEffectContext(const Bindings &bindings,
                             void *context) noexcept {
  if (context == nullptr || bindings.destroy_effect_context_118 == nullptr ||
      bindings.destroy_effect_context_array_row == nullptr) {
    return false;
  }
  // Mirrors WarOverview 0xF5973E..0xF59793. The +0x118 destructor owns the
  // +0x128/+0x148 headers; +0x100 and +0x18 are then released in order.
  bindings.destroy_effect_context_118(
      static_cast<std::byte *>(context) + 0x118);
  bool valid = true;
  if (LoadAt<void *>(context, 0x100) != nullptr) {
    bindings.destroy_effect_context_array_row(
        static_cast<std::byte *>(context) + 0x100);
    valid = FreeEffectContextArray(context, 0x100, 0x108, 0x110) && valid;
  }
  valid = FreeEffectContextArray(context, 0x18, 0x24, 0x28) && valid;
  return valid;
}

bool DryPreviewWarExitEffect(const Bindings &bindings, void *loaded_effect,
                             void *effect_context,
                             WarExitPreviewOutcome outcome,
                             std::int32_t factor_identifier_id,
                             std::int32_t primary_attacker_character_id,
                             std::int32_t primary_defender_character_id,
                             std::vector<WarExitPreviewRow> &rows,
                             std::int64_t &factor_raw) noexcept {
  g_last_war_exit_preview_unavailable_reason = {};
  g_war_exit_loaded_root_vtable_rva = 0;
  g_war_exit_loaded_root_selector_count = -1;
  g_war_exit_loaded_default_child_vtable_rva = 0;
  g_war_exit_loaded_root_capacity = -1;
  g_war_exit_loaded_root_count = -1;
  g_war_exit_loaded_hidden_count = -1;
  g_war_exit_loaded_hidden_index = -1;
  g_war_exit_loaded_hidden_capacity = -1;
  g_war_exit_loaded_hidden_child_count = -1;
  g_war_exit_loaded_hidden_child0_vtable_rva = 0;
  rows.clear();
  factor_raw = 0;
  if (loaded_effect == nullptr || effect_context == nullptr ||
      factor_identifier_id < 0 ||
      primary_attacker_character_id <= 0 ||
      primary_defender_character_id <= 0 ||
      primary_attacker_character_id == primary_defender_character_id ||
      bindings.construct_effect_preview_collector == nullptr ||
      bindings.destroy_effect_preview_collector == nullptr ||
      bindings.traverse_loaded_effect == nullptr ||
      bindings.effect_preview_collector_vtable == 0 ||
      bindings.jomini_effect_vtable == 0 ||
      bindings.jomini_scripted_effect_vtable == 0 ||
      bindings.jomini_scripted_effect_template_vtable == 0 ||
      bindings.hidden_effect_vtable == 0 ||
      bindings.jomini_context_effect_vtable == 0 ||
      bindings.truce_effect_vtable == 0 ||
      g_war_exit_preview_capture != nullptr) {
    SetWarExitPreviewUnavailableReason("dry_preview.preconditions");
    return false;
  }

  EffectPreviewCollectorStorage collector_storage{};
  void *const collector = collector_storage.bytes.data();
  if (bindings.construct_effect_preview_collector(collector) != collector) {
    SetWarExitPreviewUnavailableReason("dry_preview.collector_construct");
    return false;
  }
  auto **const original_vtable = LoadAt<void **>(collector, 0x00);
  if (reinterpret_cast<std::uintptr_t>(original_vtable) !=
      bindings.effect_preview_collector_vtable ||
      original_vtable == nullptr || original_vtable[1] == nullptr) {
    SetWarExitPreviewUnavailableReason("dry_preview.collector_vtable");
    bindings.destroy_effect_preview_collector(collector);
    return false;
  }

  // The preview interface is a large shared visitor. Clone a conservative
  // prefix so every callback used by the loaded traversal remains native;
  // only slot +0x08 is replaced and the hook forwards to its exact original.
  constexpr std::size_t kPreviewVtableCloneSlots = 128;
  std::array<void *, kPreviewVtableCloneSlots> cloned_vtable{};
  std::copy_n(original_vtable, cloned_vtable.size(), cloned_vtable.begin());
  auto *const original_slot8 =
      reinterpret_cast<EffectPreviewCollectorSlot8>(original_vtable[1]);
  cloned_vtable[1] = reinterpret_cast<void *>(&CaptureWarExitPreviewRow);

  auto **const original_effect_vtable =
      LoadAt<void **>(loaded_effect, 0x00);
  if (original_effect_vtable == nullptr ||
      original_effect_vtable[11] == nullptr) {
    SetWarExitPreviewUnavailableReason("dry_preview.loaded_effect_slot");
    bindings.destroy_effect_preview_collector(collector);
    return false;
  }
  constexpr std::size_t kLoadedEffectProxyVtableSlots = 12;
  std::array<void *, kLoadedEffectProxyVtableSlots>
      cloned_effect_vtable{};
  std::copy_n(original_effect_vtable, cloned_effect_vtable.size(),
              cloned_effect_vtable.begin());
  auto *const original_slot58 =
      reinterpret_cast<LoadedEffectSlot58>(original_effect_vtable[11]);
  cloned_effect_vtable[11] =
      reinterpret_cast<void *>(&CaptureWarExitLoadedEffect);
  std::array<std::byte, sizeof(void *)> proxy_loaded_effect{};
  StoreAt(proxy_loaded_effect.data(), 0x00,
          cloned_effect_vtable.data());

  WarExitPreviewCapture capture{};
  capture.bindings = &bindings;
  capture.original_slot8 = original_slot8;
  capture.primary_attacker_character_id =
      primary_attacker_character_id;
  capture.primary_defender_character_id =
      primary_defender_character_id;
  capture.outcome = outcome;
  capture.proxy_loaded_effect = proxy_loaded_effect.data();
  capture.original_loaded_effect = loaded_effect;
  capture.original_slot58 = original_slot58;
  capture.factor_identifier_id = factor_identifier_id;
  StoreAt(collector, 0x00, cloned_vtable.data());
  g_war_exit_preview_capture = &capture;
  // 0x3380170 owns the exact seed/TLS/variable-container lifecycle.  Its
  // only loaded-root operation is vtable+0x58, so a stack proxy lets the
  // trampoline inspect identifier82 after the original root returns but
  // before that helper destroys its temporary variable container.  Neither
  // the loaded effect nor any game object is modified.
  bindings.traverse_loaded_effect(proxy_loaded_effect.data(), effect_context,
                                  collector);
  g_war_exit_preview_capture = nullptr;
  StoreAt(collector, 0x00, original_vtable);
  bindings.destroy_effect_preview_collector(collector);
  if (LoadAt<void **>(loaded_effect, 0x00) != original_effect_vtable) {
    SetWarExitPreviewUnavailableReason(
        "dry_preview.loaded_effect_vtable_changed");
    return false;
  }
  if (capture.failed) {
    SetWarExitPreviewUnavailableReason("dry_preview.capture_failed");
    return false;
  }
  if (!capture.factor_found) {
    SetWarExitPreviewUnavailableReason("dry_preview.factor_not_captured");
    return false;
  }
  rows = std::move(capture.rows);
  factor_raw = capture.factor_raw;
  return true;
}

bool ReadCharacterExitResources(
    const Bindings &bindings, void *character, std::int32_t character_id,
    bool attacker_role,
    std::vector<game::WarExitResourceSnapshot> &balances,
    game::WarExitCharacterFixedPointSnapshot &monthly_income) noexcept {
  if (character == nullptr || character_id <= 0 ||
      bindings.read_monthly_gold_income == nullptr ||
      ResolveTermsCharacter(bindings, character_id) != character) {
    g_last_war_termination_exit_terms_unavailable_reason =
        attacker_role ? "primary_resources.attacker_identity"
                      : "primary_resources.defender_identity";
    return false;
  }
  void *const extension =
      LoadAt<void *>(character, kCharacterExtensionOffset);
  const auto read_extension_fixed = [extension](std::size_t offset) {
    return extension == nullptr ? std::int64_t{0}
                                : LoadAt<std::int64_t>(extension, offset);
  };
  const auto append = [&balances, character_id](
                          std::string_view kind, std::int64_t raw) {
    balances.push_back(
        {character_id, std::string(kind), {raw, kFixedPointScale}});
  };
  try {
    append("gold", read_extension_fixed(kCharacterGoldOffset));
    append("prestige", read_extension_fixed(kCharacterPrestigeOffset));
    append("prestige_experience",
           read_extension_fixed(kCharacterPrestigeExperienceOffset));
    append("piety", read_extension_fixed(kCharacterPietyOffset));
    append("piety_experience",
           read_extension_fixed(kCharacterPietyExperienceOffset));
    void *const legitimacy_data =
        LoadAt<void *>(character, kCharacterLegitimacyDataOffset);
    const auto legitimacy = legitimacy_data == nullptr
                                ? std::int64_t{0}
                                : std::max(
                                      LoadAt<std::int64_t>(
                                          legitimacy_data,
                                          kCharacterLegitimacyOffset),
                                      std::int64_t{0});
    append("legitimacy", legitimacy);
    const auto stress_points =
        extension == nullptr
            ? std::int32_t{0}
            : LoadAt<std::int32_t>(extension, kCharacterStressPointsOffset);
    if (stress_points < 0) {
      g_last_war_termination_exit_terms_unavailable_reason =
          attacker_role ? "primary_resources.attacker_stress"
                        : "primary_resources.defender_stress";
      return false;
    }
    append("stress", static_cast<std::int64_t>(stress_points) *
                         kFixedPointScale);
  } catch (...) {
    g_last_war_termination_exit_terms_unavailable_reason =
        attacker_role ? "primary_resources.attacker_balance_append"
                      : "primary_resources.defender_balance_append";
    return false;
  }

  std::int64_t income_raw = 0;
  if (bindings.read_monthly_gold_income(&income_raw, character, nullptr,
                                        nullptr) != &income_raw) {
    g_last_war_termination_exit_terms_unavailable_reason =
        attacker_role ? "primary_resources.attacker_income_call"
                      : "primary_resources.defender_income_call";
    return false;
  }
  // extension+0x2B0 is the direct cached monthly-income leaf, never current
  // gold.  Live paused evidence proves it can lag the complete 0x28DBE90
  // evaluator (551588 vs 570772), so it is diagnostic evidence only and not
  // an equality/readiness gate.  The callable result is authoritative.
  [[maybe_unused]] const auto cached_income =
      extension == nullptr
          ? std::int64_t{0}
          : LoadAt<std::int64_t>(extension,
                                 kCharacterMonthlyGoldIncomeOffset);
  if (ResolveTermsCharacter(bindings, character_id) != character) {
    g_last_war_termination_exit_terms_unavailable_reason =
        attacker_role ? "primary_resources.attacker_generation_changed"
                      : "primary_resources.defender_generation_changed";
    return false;
  }
  monthly_income = {character_id, {income_raw, kFixedPointScale}};
  return true;
}

bool ReadPrimaryExitResources(
    const Bindings &bindings, void *attacker, std::int32_t attacker_id,
    void *defender, std::int32_t defender_id,
    std::vector<game::WarExitResourceSnapshot> &balances,
    std::vector<game::WarExitCharacterFixedPointSnapshot> &monthly_income)
    noexcept {
  balances.clear();
  monthly_income.clear();
  try {
    balances.reserve(14);
    monthly_income.resize(2);
  } catch (...) {
    return false;
  }
  if (!ReadCharacterExitResources(bindings, attacker, attacker_id, true,
                                  balances, monthly_income[0]) ||
      !ReadCharacterExitResources(bindings, defender, defender_id, false,
                                  balances, monthly_income[1])) {
    balances.clear();
    monthly_income.clear();
    return false;
  }
  if (balances.size() != 14) {
    g_last_war_termination_exit_terms_unavailable_reason =
        "primary_resources.balance_count";
    balances.clear();
    monthly_income.clear();
    return false;
  }
  return true;
}

bool ReadWarParticipantIds(const Bindings &bindings, const void *side,
                           std::vector<std::int32_t> &ids) noexcept {
  ids.clear();
  if (side == nullptr) {
    return false;
  }
  void *const data =
      LoadAt<void *>(side, kWarParticipantPointersOffset);
  const auto capacity = LoadAt<std::int32_t>(
      side, kWarParticipantPointerCapacityOffset);
  const auto count =
      LoadAt<std::int32_t>(side, kWarParticipantPointerCountOffset);
  if (capacity < 0 || count < 0 || count > capacity || count > 4'096 ||
      (count > 0 && data == nullptr)) {
    return false;
  }
  try {
    ids.reserve(static_cast<std::size_t>(count));
  } catch (...) {
    return false;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    void *const participant = LoadAt<void *>(
        data, static_cast<std::size_t>(index) * sizeof(void *));
    if (participant == nullptr) {
      return false;
    }
    const auto character_id = LoadAt<std::int32_t>(
        participant, kWarParticipantCharacterIdOffset);
    if (character_id <= 0 ||
        ResolveTermsCharacter(bindings, character_id) == nullptr ||
        std::find(ids.begin(), ids.end(), character_id) != ids.end()) {
      return false;
    }
    ids.push_back(character_id);
  }
  return true;
}

bool ReadPrimaryAndSuccessors(const Bindings &bindings, void *game_state,
                              void *character,
                              std::int32_t character_id,
                              std::vector<std::int32_t> &ids) noexcept {
  ids.clear();
  if (bindings.get_character_primary_title == nullptr || character == nullptr ||
      ResolveTermsCharacter(bindings, character_id) != character) {
    return false;
  }
  void *const title = bindings.get_character_primary_title(character);
  if (title == nullptr) {
    return false;
  }
  const auto title_id = LoadAt<std::int32_t>(title, kLandedTitleIdOffset);
  if (title_id <= 0 ||
      ResolveLandedTitle(bindings, game_state, title_id) != title) {
    return false;
  }
  std::vector<std::int32_t> succession;
  if (!ReadNativeIntArray(
          static_cast<std::byte *>(title) +
              kLandedTitleSuccessionIdsOffset,
          succession, 4'096)) {
    return false;
  }
  try {
    ids.push_back(character_id);
    for (std::size_t index = 0;
         index < succession.size() && index < 3U; ++index) {
      const auto successor_id = succession[index];
      if (successor_id <= 0 ||
          ResolveTermsCharacter(bindings, successor_id) == nullptr ||
          std::find(ids.begin(), ids.end(), successor_id) != ids.end()) {
        return false;
      }
      ids.push_back(successor_id);
    }
  } catch (...) {
    return false;
  }
  return ResolveTermsCharacter(bindings, character_id) == character &&
         ResolveLandedTitle(bindings, game_state, title_id) == title;
}

bool AppendPrisonerReleases(
    const Bindings &bindings, const std::vector<std::int32_t> &candidates,
    const std::vector<std::int32_t> &opposite_participants,
    std::vector<game::WarExitPrisonerReleaseSnapshot> &output) noexcept {
  for (const auto candidate_id : candidates) {
    void *const candidate = ResolveTermsCharacter(bindings, candidate_id);
    if (candidate == nullptr) {
      return false;
    }
    void *const extension =
        LoadAt<void *>(candidate, kCharacterExtensionOffset);
    void *const prison_relation =
        extension == nullptr
            ? nullptr
            : LoadAt<void *>(extension, kCharacterPrisonRelationOffset);
    if (prison_relation == nullptr) {
      continue;
    }
    const auto jailer_id = LoadAt<std::int32_t>(
        prison_relation, kPrisonRelationJailerCharacterIdOffset);
    if (jailer_id <= 0 ||
        ResolveTermsCharacter(bindings, jailer_id) == nullptr) {
      return false;
    }
    if (std::find(opposite_participants.begin(),
                  opposite_participants.end(), jailer_id) ==
        opposite_participants.end()) {
      continue;
    }
    try {
      output.push_back({jailer_id, candidate_id,
                        "opposite_primary_or_first_three_successors"});
    } catch (...) {
      return false;
    }
  }
  return true;
}

bool ReadWarExitPrisonerReleases(
    const Bindings &bindings, void *game_state, void *war,
    void *attacker_character, std::int32_t attacker_id,
    void *defender_character, std::int32_t defender_id,
    std::vector<game::WarExitPrisonerReleaseSnapshot> &output) noexcept {
  output.clear();
  std::vector<std::int32_t> attackers;
  std::vector<std::int32_t> defenders;
  std::vector<std::int32_t> attacker_candidates;
  std::vector<std::int32_t> defender_candidates;
  if (!ReadWarParticipantIds(
          bindings,
          static_cast<std::byte *>(war) + kWarAttackersOffset,
          attackers) ||
      !ReadWarParticipantIds(
          bindings,
          static_cast<std::byte *>(war) + kWarDefendersOffset,
          defenders) ||
      std::find(attackers.begin(), attackers.end(), attacker_id) ==
          attackers.end() ||
      std::find(defenders.begin(), defenders.end(), defender_id) ==
          defenders.end() ||
      !ReadPrimaryAndSuccessors(bindings, game_state, attacker_character,
                                attacker_id, attacker_candidates) ||
      !ReadPrimaryAndSuccessors(bindings, game_state, defender_character,
                                defender_id, defender_candidates) ||
      !AppendPrisonerReleases(bindings, attacker_candidates, defenders,
                              output) ||
      !AppendPrisonerReleases(bindings, defender_candidates, attackers,
                              output) ||
      output.size() > 64U) {
    output.clear();
    return false;
  }
  return true;
}

void ReadWarTerminationAcceptance(
    const Bindings &bindings, void *context,
    game::WarTerminationOptionSnapshot &option) noexcept {
  if (bindings.read_character_interaction_answer_score != nullptr) {
    std::int64_t raw = 0;
    if (bindings.read_character_interaction_answer_score(context, &raw) ==
        &raw) {
      option.ai_acceptance_observable = true;
      option.ai_acceptance.raw = raw;
      option.ai_acceptance.scale = kFixedPointScale;
    }
  }
  void *const interaction = LoadAt<void *>(context, 0);
  if (interaction == nullptr) {
    return;
  }
  void *const auto_accept_trigger = LoadAt<void *>(
      interaction, kCharacterInteractionAutoAcceptTriggerOffset);
  if (auto_accept_trigger != nullptr) {
    if (bindings.evaluate_character_interaction_trigger != nullptr) {
      option.auto_accept_observable = true;
      option.auto_accept = bindings.evaluate_character_interaction_trigger(
          auto_accept_trigger,
          static_cast<const std::byte *>(context) +
              kCharacterInteractionContextScopeOffset);
    }
    return;
  }
  const auto scalar = LoadAt<std::uint8_t>(
      interaction, kCharacterInteractionAutoAcceptScalarOffset);
  if (scalar <= 1) {
    option.auto_accept_observable = true;
    option.auto_accept = scalar != 0;
  }
}

bool ReadWarExitRecipientResponse(
    const Bindings &bindings, void *context,
    game::WarExitRecipientResponseSnapshot &response) noexcept;

bool EvaluateWarResolutionContext(
    const Bindings &bindings, void *war, bool attacker_victory,
    game::WarTerminationOptionSnapshot &option) noexcept {
  CharacterInteractionContextStorage context_storage{};
  void *const context = context_storage.bytes.data();
  if (bindings.default_construct_character_interaction_context(context) !=
      context) {
    return false;
  }
  bindings.construct_war_resolution_interaction_context(
      context, war, attacker_victory);
  option.context_constructed =
      LoadAt<void *>(context, kCharacterInteractionSpecialDataOffset) !=
      nullptr;
  if (option.context_constructed) {
    option.native_validator_observable = true;
    option.native_validator_passed =
        bindings.validate_character_interaction_context(context, nullptr);
    ReadWarTerminationAcceptance(bindings, context, option);
    game::WarExitRecipientResponseSnapshot response{};
    if (ReadWarExitRecipientResponse(bindings, context, response)) {
      option.recipient_response.observable = true;
      option.recipient_response.decision_status_raw =
          response.decision_status_raw;
      option.recipient_response.would_accept_now =
          response.would_accept_now;
    }
  }
  bindings.destroy_character_interaction_context(context);
  return true;
}

bool EvaluateWhitePeaceContext(
    const Bindings &bindings, std::int32_t actor_character_id,
    std::int32_t recipient_character_id,
    game::WarTerminationOptionSnapshot &option) noexcept {
  CharacterInteractionContextStorage context_storage{};
  void *const context = context_storage.bytes.data();
  constexpr std::uint8_t kWhitePeaceSpecialInteractionIndex = 3;
  if (bindings.construct_special_character_interaction_context(
          context, kWhitePeaceSpecialInteractionIndex, actor_character_id,
          recipient_character_id) != context) {
    return false;
  }
  option.context_constructed =
      LoadAt<void *>(context, kCharacterInteractionSpecialDataOffset) !=
      nullptr;
  if (option.context_constructed) {
    option.native_validator_observable = true;
    option.native_validator_passed =
        bindings.validate_character_interaction_context(context, nullptr);
    ReadWarTerminationAcceptance(bindings, context, option);
    game::WarExitRecipientResponseSnapshot response{};
    if (ReadWarExitRecipientResponse(bindings, context, response)) {
      option.recipient_response.observable = true;
      option.recipient_response.decision_status_raw =
          response.decision_status_raw;
      option.recipient_response.would_accept_now =
          response.would_accept_now;
    }
  }
  bindings.destroy_character_interaction_context(context);
  return true;
}

bool ReadWarExitRecipientResponse(
    const Bindings &bindings, void *context,
    game::WarExitRecipientResponseSnapshot &response) noexcept {
  response = {};
  if (context == nullptr ||
      bindings.evaluate_character_interaction_answer == nullptr ||
      LoadAt<void *>(context, kCharacterInteractionSpecialDataOffset) ==
          nullptr) {
    return false;
  }
  response.native_validator_passed =
      bindings.validate_character_interaction_context(context, nullptr);
  if (!response.native_validator_passed) {
    return false;
  }
  game::WarTerminationOptionSnapshot diagnostic{};
  ReadWarTerminationAcceptance(bindings, context, diagnostic);
  if (!diagnostic.ai_acceptance_observable ||
      !diagnostic.auto_accept_observable) {
    return false;
  }
  const auto status = bindings.evaluate_character_interaction_answer(
      context, 1, 0, nullptr, nullptr);
  if (status >= 3) {
    return false;
  }
  response.acceptance = diagnostic.ai_acceptance;
  response.decision_status_raw = status;
  response.would_accept_now = status != 2;
  response.auto_accept = diagnostic.auto_accept;
  return true;
}

bool EvaluateWarExitDefeatRecipient(
    const Bindings &bindings, void *war,
    game::WarExitRecipientResponseSnapshot &response) noexcept {
  CharacterInteractionContextStorage storage{};
  void *const context = storage.bytes.data();
  if (bindings.default_construct_character_interaction_context(context) !=
      context) {
    return false;
  }
  // `false` is the absolute attacker-defeat result in 1.19.0.6.
  bindings.construct_war_resolution_interaction_context(context, war, false);
  const bool result =
      ReadWarExitRecipientResponse(bindings, context, response);
  bindings.destroy_character_interaction_context(context);
  return result;
}

bool EvaluateWarExitWhitePeaceRecipient(
    const Bindings &bindings, std::int32_t attacker_id,
    std::int32_t defender_id,
    game::WarExitRecipientResponseSnapshot &response) noexcept {
  CharacterInteractionContextStorage storage{};
  void *const context = storage.bytes.data();
  constexpr std::uint8_t kWhitePeaceSpecialInteractionIndex = 3;
  if (bindings.construct_special_character_interaction_context(
          context, kWhitePeaceSpecialInteractionIndex, attacker_id,
          defender_id) != context) {
    return false;
  }
  const bool result =
      ReadWarExitRecipientResponse(bindings, context, response);
  bindings.destroy_character_interaction_context(context);
  return result;
}

bool NarrowWarScore(std::int64_t value, std::int32_t &output) noexcept {
  if (value < std::numeric_limits<std::int32_t>::min() ||
      value > std::numeric_limits<std::int32_t>::max()) {
    return false;
  }
  output = static_cast<std::int32_t>(value);
  return true;
}

std::int32_t PackedWarScore(std::uint64_t packed) noexcept {
  const auto raw = static_cast<std::uint32_t>(packed & 0xFFFFFFFFULL);
  std::int32_t score = 0;
  std::memcpy(&score, &raw, sizeof(score));
  return score;
}

bool ReadWarScoreBreakdown(
    const Bindings &bindings, void *war,
    game::WarScoreBreakdownSnapshot &output) noexcept {
  output = {};
  if (bindings.get_imprisonment_war_score == nullptr ||
      bindings.get_battle_war_score_base == nullptr ||
      bindings.get_battle_war_score_side == nullptr ||
      bindings.get_occupation_war_score_side == nullptr ||
      bindings.get_ticking_war_score_side == nullptr) {
    return false;
  }

  std::int32_t battles = 0;
  if (!NarrowWarScore(
          static_cast<std::int64_t>(
              bindings.get_battle_war_score_base(war, nullptr)) +
              bindings.get_battle_war_score_side(war, false, nullptr) -
              bindings.get_battle_war_score_side(war, true, nullptr),
          battles)) {
    return false;
  }

  const auto first_occupation =
      bindings.get_occupation_war_score_side(war, false, nullptr);
  const auto first_score = PackedWarScore(first_occupation);
  const bool first_authoritative =
      ((first_occupation >> 32U) & 0xFFU) != 0;
  std::int32_t occupation = first_score;
  if (!first_authoritative) {
    const auto second_occupation =
        bindings.get_occupation_war_score_side(war, true, nullptr);
    const auto second_score = PackedWarScore(second_occupation);
    const bool second_authoritative =
        ((second_occupation >> 32U) & 0xFFU) != 0;
    const std::int64_t combined = second_authoritative
                                      ? -static_cast<std::int64_t>(second_score)
                                      : static_cast<std::int64_t>(first_score) -
                                            second_score;
    if (!NarrowWarScore(combined, occupation)) {
      return false;
    }
  }

  std::int32_t ticking = 0;
  if (!NarrowWarScore(
          static_cast<std::int64_t>(
              bindings.get_ticking_war_score_side(
                  war, false, nullptr, true)) -
              bindings.get_ticking_war_score_side(
                  war, true, nullptr, false),
          ticking)) {
    return false;
  }

  output.observable = true;
  output.imprisonment =
      bindings.get_imprisonment_war_score(war, nullptr);
  output.battles = battles;
  output.occupation = occupation;
  output.ticking = ticking;
  return true;
}

std::string_view UnitStateName(std::int32_t state_code) noexcept {
  switch (state_code) {
  case 1:
    return "regular";
  case 2:
    return "combat";
  case 3:
    return "sieging";
  case 4:
    return "embarked";
  case 5:
    return "gathering";
  case 6:
    return "retreating";
  case 7:
    return "moving";
  case 8:
    return "raiding";
  case 9:
    return "bartering";
  default:
    return "unknown";
  }
}

void ReadUnitRoute(void *game_state, void *unit, bool include_full_route,
                   ArmySnapshot &snapshot) noexcept {
  snapshot.route_province_ids.clear();
  snapshot.move_target_observable = false;
  snapshot.move_target_province_id = -1;
  void *const province_infos =
      LoadAt<void *>(unit, kUnitPathProvinceInfosOffset);
  const auto capacity = LoadAt<std::int32_t>(
      unit, kUnitPathProvinceInfoCapacityOffset);
  const auto count =
      LoadAt<std::int32_t>(unit, kUnitPathProvinceInfoCountOffset);
  if (capacity < 0 || count < 0 || count > capacity ||
      count > kMaximumUnitRouteProvinceInfos) {
    return;
  }
  if (count == 0) {
    return;
  }
  if (province_infos == nullptr) {
    return;
  }

  if (!include_full_route) {
    void *const last_province_info = LoadAt<void *>(
        province_infos,
        static_cast<std::size_t>(count - 1) * sizeof(void *));
    if (last_province_info == nullptr) {
      return;
    }
    const auto province_id = LoadAt<std::int32_t>(
        last_province_info, kUnitPathProvinceIdOffset);
    if (ResolveProvince(game_state, province_id) == nullptr) {
      return;
    }
    snapshot.move_target_observable = true;
    snapshot.move_target_province_id = province_id;
    return;
  }

  std::vector<std::int32_t> route_province_ids;
  route_province_ids.reserve(static_cast<std::size_t>(count));
  for (std::int32_t index = 0; index < count; ++index) {
    void *const province_info = LoadAt<void *>(
        province_infos, static_cast<std::size_t>(index) * sizeof(void *));
    if (province_info == nullptr) {
      return;
    }
    const auto province_id =
        LoadAt<std::int32_t>(province_info, kUnitPathProvinceIdOffset);
    if (ResolveProvince(game_state, province_id) == nullptr) {
      return;
    }
    route_province_ids.push_back(province_id);
  }

  snapshot.route_province_ids = std::move(route_province_ids);
  snapshot.move_target_observable = true;
  snapshot.move_target_province_id = snapshot.route_province_ids.back();
}

struct ResolvedArmySnapshot {
  void *army = nullptr;
  ArmySnapshot snapshot{};
};

std::vector<ResolvedArmySnapshot>
ReadArmies(const Bindings &bindings, void *game_state,
           std::int32_t played_character_id,
           bool include_full_routes) noexcept {
  std::vector<ResolvedArmySnapshot> result;
  if (bindings.army_storage_slot == nullptr) {
    return result;
  }
  void *const storage = *bindings.army_storage_slot;
  if (storage == nullptr) {
    return result;
  }
  void *const slots = LoadAt<void *>(storage, kComponentStorageSlotsOffset);
  const std::int32_t capacity =
      LoadAt<std::int32_t>(storage, kComponentStorageCapacityOffset);
  if (slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentCapacity) {
    return result;
  }
  for (std::int32_t index = 0; index < capacity; ++index) {
    const auto slot_offset = static_cast<std::size_t>(index) *
                                 kComponentStorageSlotSize +
                             kComponentStorageSlotObjectOffset;
    void *const army = LoadAt<void *>(slots, slot_offset);
    if (army == nullptr) {
      continue;
    }
    const std::int32_t army_id =
        LoadAt<std::int32_t>(army, kArmyIdOffset);
    if ((static_cast<std::uint32_t>(army_id) & 0x00FFFFFFU) !=
        static_cast<std::uint32_t>(index)) {
      continue;
    }

    ArmySnapshot snapshot{};
    snapshot.army_id = army_id;
    snapshot.owner_character_id =
        LoadAt<std::int32_t>(army, kArmyOwnerCharacterIdOffset);
    snapshot.controllable =
        snapshot.owner_character_id == played_character_id;
    void *const current_province =
        LoadAt<void *>(army, kArmyCurrentProvinceOffset);
    if (current_province != nullptr) {
      const std::int32_t province_id =
          LoadAt<std::int32_t>(current_province, kProvinceIdOffset);
      if (province_id > 0) {
        snapshot.has_current_province = true;
        snapshot.current_province_id = province_id;
      }
    }
    if (bindings.get_unit_state != nullptr) {
      const auto state_code = bindings.get_unit_state(army);
      if (state_code >= 1 && state_code <= 9) {
        snapshot.army_state_code = state_code;
      }
    }
    snapshot.army_state = UnitStateName(snapshot.army_state_code);
    snapshot.in_combat = snapshot.army_state_code == 2;
    snapshot.retreating =
        LoadAt<std::int32_t>(army, kUnitRetreatStateOffset) > 0;
    ReadUnitRoute(game_state, army, include_full_routes, snapshot);
    result.push_back({army, snapshot});
  }
  return result;
}

WarObjectiveProvinceState ReadWarObjectiveProvinceState(
    const Bindings &bindings, void *game_state, std::int32_t province_id,
    std::int32_t played_character_id,
    const std::vector<ResolvedArmySnapshot> &armies,
    bool include_paused_details) noexcept {
  WarObjectiveProvinceState state{};
  state.province_id = province_id;
  void *const province = ResolveProvince(game_state, province_id);
  if (province == nullptr) {
    return state;
  }

  if (bindings.is_province_occupied != nullptr) {
    const bool occupied = bindings.is_province_occupied(province);
    if (!occupied) {
      state.occupation_observable = true;
    } else {
      const auto occupying_character_id = LoadAt<std::int32_t>(
          province, kProvinceOccupyingCharacterIdOffset);
      if (ResolveCharacter(bindings, occupying_character_id) != nullptr) {
        state.occupation_observable = true;
        state.is_occupied = true;
        state.occupying_character_id = occupying_character_id;
      }
    }
  }

  if (bindings.get_province_fort_level != nullptr) {
    const auto fort_level = bindings.get_province_fort_level(province);
    if (fort_level >= 0) {
      state.fort_level_observable = true;
      state.fort_level = fort_level;
    }
  }
  // The remaining getters traverse mutable Holding/CUnit/CSiege subgraphs.
  // No engine read lock has been identified, so the worker calls them only
  // while CK3 is paused. Occupation and fort level above are direct Province
  // scalar getters and remain useful in running snapshots.
  if (!include_paused_details) {
    return state;
  }
  if (bindings.get_province_garrison_size != nullptr) {
    const auto garrison_size =
        bindings.get_province_garrison_size(province);
    if (garrison_size >= 0) {
      state.garrison_size_observable = true;
      state.garrison_size = garrison_size;
    }
  }
  if (bindings.get_province_besieging_strength != nullptr) {
    const auto besieging_strength =
        bindings.get_province_besieging_strength(province);
    if (besieging_strength >= 0) {
      state.besieging_strength_observable = true;
      state.besieging_strength = besieging_strength;
    }
  }

  const bool has_siege_reader =
      bindings.siege_storage_slot != nullptr &&
      bindings.is_native_component_alive != nullptr &&
      bindings.get_siege_progress != nullptr &&
      bindings.get_siege_total_work != nullptr &&
      bindings.get_siege_days_left != nullptr;
  if (!has_siege_reader) {
    return state;
  }
  const auto siege_id =
      LoadAt<std::int32_t>(province, kProvinceActiveSiegeIdOffset);
  if (siege_id == -1) {
    state.siege_observable = true;
    return state;
  }
  void *const siege = ResolveSiege(bindings, siege_id);
  if (siege == nullptr ||
      LoadAt<void *>(siege, kSiegeProvinceOffset) != province) {
    return state;
  }

  std::int64_t progress_raw = 0;
  std::int64_t total_work_raw = 0;
  if (bindings.get_siege_progress(siege, &progress_raw) != &progress_raw ||
      bindings.get_siege_total_work(siege, &total_work_raw) !=
          &total_work_raw) {
    return state;
  }
  const auto current_work_raw =
      LoadAt<std::int64_t>(siege, kSiegeCurrentWorkOffset);
  if (progress_raw < 0 || progress_raw > kFixedPointScale ||
      current_work_raw < 0 || total_work_raw < 0) {
    return state;
  }

  state.siege_observable = true;
  state.has_active_siege = true;
  state.siege_id = siege_id;
  state.siege_progress_fraction.raw = progress_raw;
  state.siege_current_work.raw = current_work_raw;
  state.siege_total_work.raw = total_work_raw;

  const auto besieging_carmy_id =
      LoadAt<std::int32_t>(siege, kSiegeBesiegingArmyIdOffset);
  std::int32_t unique_besieging_unit_id = -1;
  std::size_t besieging_unit_matches = 0;
  if (besieging_carmy_id != -1) {
    for (const auto &army : armies) {
      if (LoadAt<std::int32_t>(army.army, kUnitArmyIdOffset) !=
          besieging_carmy_id) {
        continue;
      }
      ++besieging_unit_matches;
      unique_besieging_unit_id = army.snapshot.army_id;
      state.player_army_besieging =
          state.player_army_besieging || army.snapshot.controllable;
    }
  }
  if (besieging_unit_matches == 1) {
    state.besieging_army_id = unique_besieging_unit_id;
  }

  // Assault is an all-or-none paused subdomain. Never expose +0x3D8/+0x44C
  // directly: only the exact adapter maps their validated representation to
  // version-neutral breach/active semantics. An intact wall has no legal
  // daily assault projection, so its exact public projection is zero without
  // calling the casualty routine that indexes breach_level - 1.
  const bool has_assault_reader =
      bindings.read_assault_daily_progress != nullptr &&
      bindings.get_assault_daily_casualties != nullptr &&
      bindings.validate_start_assault_command != nullptr &&
      bindings.validate_stop_assault_command != nullptr &&
      state.besieging_strength_observable;
  if (has_assault_reader) {
    const auto breach_level =
        LoadAt<std::int32_t>(siege, kSiegeBreachLevelOffset);
    const auto active_raw =
        LoadAt<std::uint8_t>(siege, kSiegeAssaultInProgressOffset);
    if (breach_level >= 0 && breach_level <= 2 && active_raw <= 1) {
      constexpr std::int32_t command_kind = 1;
      const bool can_start = bindings.validate_start_assault_command(
          command_kind, played_character_id, siege_id, nullptr);
      const bool can_stop = bindings.validate_stop_assault_command(
          command_kind, played_character_id, siege_id, nullptr);
      std::int64_t daily_progress_raw = 0;
      std::int32_t daily_casualties = 0;
      bool projection_valid = true;
      if (breach_level > 0) {
        projection_valid =
            bindings.read_assault_daily_progress(
                siege, &daily_progress_raw, state.besieging_strength) ==
                &daily_progress_raw &&
            daily_progress_raw >= 0;
        if (projection_valid) {
          daily_casualties =
              bindings.get_assault_daily_casualties(siege);
          projection_valid = daily_casualties >= 0;
        }
      }
      if (projection_valid) {
        state.assault_observable = true;
        state.breach_level = breach_level;
        state.assault_in_progress = active_raw != 0;
        state.can_start_assault = can_start;
        state.can_stop_assault = can_stop;
        state.assault_daily_progress.raw = daily_progress_raw;
        state.assault_daily_casualties = daily_casualties;
      }
    }
  }

  const auto days_left = bindings.get_siege_days_left(siege);
  if (days_left >= 0 && days_left != std::numeric_limits<std::int32_t>::max()) {
    state.siege_days_left_observable = true;
    state.siege_days_left = days_left;
  }
  return state;
}

void ReadWarObjectiveProvinceStates(
    const Bindings &bindings, void *game_state,
    std::int32_t played_character_id,
    const std::vector<ResolvedArmySnapshot> &armies,
    bool include_paused_details, std::size_t &remaining_state_budget,
    ActiveWarSnapshot &war) noexcept {
  war.objective_province_states.clear();
  // Publish a war atomically or not at all. The shared snapshot budget is
  // deliberately smaller than the 4096-ID hierarchy ceiling because paused
  // heartbeats still run every 250 ms and each rich row calls engine getters.
  // Multiple concurrent wars share this budget.
  if (war.war_objective_province_ids.size() > remaining_state_budget) {
    return;
  }
  war.objective_province_states.reserve(
      war.war_objective_province_ids.size());
  for (const auto province_id : war.war_objective_province_ids) {
    war.objective_province_states.push_back(
        ReadWarObjectiveProvinceState(bindings, game_state, province_id,
                                      played_character_id, armies,
                                      include_paused_details));
  }
  remaining_state_budget -= war.objective_province_states.size();
}

void ReadWarsAndArmies(const Bindings &bindings, void *game_state,
                       std::int32_t played_character_id,
                       bool include_full_routes,
                       Snapshot &output) noexcept {
  output.active_wars.clear();
  output.player_armies.clear();
  const auto armies = ReadArmies(bindings, game_state,
                                 played_character_id,
                                 include_full_routes);
  for (const auto &army : armies) {
    if (army.snapshot.controllable) {
      output.player_armies.push_back(army.snapshot);
    }
  }
  if (game_state == nullptr || bindings.contains_war_participant == nullptr ||
      bindings.get_war_score == nullptr) {
    return;
  }
  void *const game_data =
      LoadAt<void *>(game_state, kGameStateGameDataOffset);
  if (game_data == nullptr) {
    return;
  }
  auto *const war_manager =
      static_cast<std::byte *>(game_data) + bindings.war_manager_offset;
  void *const war_storage =
      LoadAt<void *>(war_manager, kWarStorageOffset);
  if (war_storage == nullptr) {
    return;
  }
  void *const slots =
      LoadAt<void *>(war_storage, kComponentStorageSlotsOffset);
  const std::int32_t capacity =
      LoadAt<std::int32_t>(war_storage, kComponentStorageCapacityOffset);
  if (slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentCapacity) {
    return;
  }
  std::size_t remaining_objective_state_budget =
      kMaximumWarObjectiveProvinceStateCount;

  for (std::int32_t index = 0; index < capacity; ++index) {
    const auto slot_offset = static_cast<std::size_t>(index) *
                                 kComponentStorageSlotSize +
                             kComponentStorageSlotObjectOffset;
    void *const war = LoadAt<void *>(slots, slot_offset);
    if (war == nullptr || LoadAt<void *>(war, kWarEndedDataOffset) != nullptr) {
      continue;
    }
    const std::int32_t war_id = LoadAt<std::int32_t>(war, kWarIdOffset);
    if ((static_cast<std::uint32_t>(war_id) & 0x00FFFFFFU) !=
        static_cast<std::uint32_t>(index)) {
      continue;
    }
    void *const attackers =
        static_cast<std::byte *>(war) + kWarAttackersOffset;
    void *const defenders =
        static_cast<std::byte *>(war) + kWarDefendersOffset;
    const bool player_is_attacker =
        bindings.contains_war_participant(attackers, played_character_id);
    const bool player_is_defender =
        bindings.contains_war_participant(defenders, played_character_id);
    if (player_is_attacker == player_is_defender) {
      continue;
    }

    ActiveWarSnapshot snapshot{};
    snapshot.war_id = war_id;
    snapshot.player_side = player_is_attacker ? PlayerWarSide::attacker
                                              : PlayerWarSide::defender;
    const std::int32_t player_primary_character_id =
        LoadAt<std::int32_t>(
            war, player_is_attacker
                     ? kWarPrimaryAttackerCharacterIdOffset
                     : kWarPrimaryDefenderCharacterIdOffset);
    snapshot.player_is_primary_war_leader =
        player_primary_character_id == played_character_id;
    if (ReadNativeIntArray(
            static_cast<std::byte *>(war) + kWarTargetedTitleIdsOffset,
            snapshot.targeted_title_ids, kMaximumWarObjectiveTitleIds)) {
      std::size_t remaining_title_budget =
          static_cast<std::size_t>(kMaximumWarObjectiveTitleIds);
      for (const auto targeted_title_id : snapshot.targeted_title_ids) {
        std::vector<std::int32_t> visited_title_ids;
        std::vector<std::int32_t> target_province_ids;
        if (!CollectWarObjectiveProvinceIds(
                bindings, game_state, targeted_title_id, true, 0,
                remaining_title_budget, visited_title_ids,
                target_province_ids)) {
          continue;
        }
        for (const auto province_id : target_province_ids) {
          AppendUniqueWarObjectiveProvinceId(
              snapshot.war_objective_province_ids, province_id);
        }
      }
    }
    ReadWarObjectiveProvinceStates(
        bindings, game_state, played_character_id, armies,
        include_full_routes,
        remaining_objective_state_budget, snapshot);
    const std::int32_t primary_opponent_character_id =
        LoadAt<std::int32_t>(
            war, player_is_attacker
                     ? kWarPrimaryDefenderCharacterIdOffset
                     : kWarPrimaryAttackerCharacterIdOffset);
    void *const primary_opponent =
        ResolveCharacter(bindings, primary_opponent_character_id);
    if (primary_opponent != nullptr) {
      snapshot.primary_opponent_character_id =
          primary_opponent_character_id;
      if (bindings.resolve_default_raise_province != nullptr) {
        void *const default_raise_province =
            bindings.resolve_default_raise_province(primary_opponent);
        if (default_raise_province != nullptr) {
          const std::int32_t default_raise_province_id =
              LoadAt<std::int32_t>(default_raise_province,
                                   kProvinceIdOffset);
          if (ResolveProvince(game_state, default_raise_province_id) ==
              default_raise_province) {
            snapshot.enemy_primary_default_raise_province_id =
                default_raise_province_id;
          }
        }
      }
    }
    const std::int32_t attacker_score = bindings.get_war_score(war, nullptr);
    snapshot.player_relative_war_score =
        player_is_attacker ? attacker_score : -attacker_score;
    void *const allied_participants =
        player_is_attacker ? attackers : defenders;
    void *const enemy_participants =
        player_is_attacker ? defenders : attackers;
    for (const auto &army : armies) {
      if (bindings.contains_war_participant(
              allied_participants, army.snapshot.owner_character_id)) {
        snapshot.allied_armies.push_back(army.snapshot);
      } else if (bindings.contains_war_participant(
                     enemy_participants,
                     army.snapshot.owner_character_id)) {
        snapshot.enemy_armies.push_back(army.snapshot);
      }
    }
    output.active_wars.push_back(std::move(snapshot));
  }
}

struct ArmyStrengthScopeEntry {
  std::int32_t army_id = -1;
  ArmyStrengthScopeRole role = ArmyStrengthScopeRole::active_war_enemy;
  std::vector<std::int32_t> war_ids;
};

int ArmyStrengthRolePriority(ArmyStrengthScopeRole role) noexcept {
  switch (role) {
  case ArmyStrengthScopeRole::player:
    return 3;
  case ArmyStrengthScopeRole::active_war_ally:
    return 2;
  case ArmyStrengthScopeRole::active_war_enemy:
    return 1;
  }
  return 0;
}

void AppendArmyStrengthScope(
    std::vector<ArmyStrengthScopeEntry> &scope, std::int32_t army_id,
    ArmyStrengthScopeRole role, std::int32_t war_id) {
  auto existing = std::find_if(
      scope.begin(), scope.end(), [army_id](const auto &candidate) {
        return candidate.army_id == army_id;
      });
  if (existing == scope.end()) {
    scope.push_back({army_id, role, {}});
    existing = scope.end() - 1;
  } else if (ArmyStrengthRolePriority(role) >
             ArmyStrengthRolePriority(existing->role)) {
    // Upgrade the semantic role without moving the row. This preserves the
    // first-seen order while keeping player > ally > enemy classification.
    existing->role = role;
  }
  if (war_id != -1 &&
      std::find(existing->war_ids.begin(), existing->war_ids.end(), war_id) ==
          existing->war_ids.end()) {
    existing->war_ids.push_back(war_id);
  }
}

std::vector<ArmyStrengthScopeEntry>
BuildArmyStrengthScope(const Snapshot &snapshot) {
  std::vector<ArmyStrengthScopeEntry> result;
  for (const auto &army : snapshot.player_armies) {
    AppendArmyStrengthScope(result, army.army_id,
                            ArmyStrengthScopeRole::player, -1);
  }
  for (const auto &war : snapshot.active_wars) {
    for (const auto &army : war.allied_armies) {
      AppendArmyStrengthScope(result, army.army_id,
                              ArmyStrengthScopeRole::active_war_ally,
                              war.war_id);
    }
    for (const auto &army : war.enemy_armies) {
      AppendArmyStrengthScope(result, army.army_id,
                              ArmyStrengthScopeRole::active_war_enemy,
                              war.war_id);
    }
  }
  return result;
}

void *ResolveStoredComponent(void **storage_slot, std::int32_t component_id,
                             std::size_t component_id_offset) noexcept {
  if (storage_slot == nullptr || component_id == -1) {
    return nullptr;
  }
  void *const storage = *storage_slot;
  if (storage == nullptr) {
    return nullptr;
  }
  void *const slots = LoadAt<void *>(storage, kComponentStorageSlotsOffset);
  const auto capacity =
      LoadAt<std::int32_t>(storage, kComponentStorageCapacityOffset);
  const auto index =
      static_cast<std::uint32_t>(component_id) & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentCapacity ||
      index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  const auto slot_offset = static_cast<std::size_t>(index) *
                               kComponentStorageSlotSize +
                           kComponentStorageSlotObjectOffset;
  void *const component = LoadAt<void *>(slots, slot_offset);
  if (component == nullptr ||
      LoadAt<std::int32_t>(component, component_id_offset) != component_id) {
    return nullptr;
  }
  return component;
}

bool CheckedAddNonnegative(std::int64_t &sum,
                           std::int32_t value) noexcept {
  if (value < 0 ||
      sum > static_cast<std::int64_t>(
                std::numeric_limits<std::int32_t>::max()) -
                value) {
    return false;
  }
  sum += value;
  return true;
}

bool CheckedAddSigned(std::int64_t &sum, std::int64_t value) noexcept {
  if ((value > 0 &&
       sum > std::numeric_limits<std::int64_t>::max() - value) ||
      (value < 0 &&
       sum < std::numeric_limits<std::int64_t>::min() - value)) {
    return false;
  }
  sum += value;
  return true;
}

bool CheckedMultiplySigned(std::int64_t left, std::int64_t right,
                           std::int64_t &output) noexcept {
  if (left == 0 || right == 0) {
    output = 0;
    return true;
  }
  if ((left == -1 && right == std::numeric_limits<std::int64_t>::min()) ||
      (right == -1 && left == std::numeric_limits<std::int64_t>::min())) {
    return false;
  }
  if (left > 0) {
    if ((right > 0 &&
         left > std::numeric_limits<std::int64_t>::max() / right) ||
        (right < 0 &&
         right < std::numeric_limits<std::int64_t>::min() / left)) {
      return false;
    }
  } else if ((right > 0 &&
              left < std::numeric_limits<std::int64_t>::min() / right) ||
             (right < 0 &&
              left < std::numeric_limits<std::int64_t>::max() / right)) {
    return false;
  }
  output = left * right;
  return true;
}

using RegimentIdentityPredicate = bool (*)(void *regiment_subobject);

bool ReadSubobjectPredicate(void *object, std::size_t subobject_offset,
                             bool &value) noexcept {
  void *const subobject =
      static_cast<std::byte *>(object) + subobject_offset;
  void *const vtable = LoadAt<void *>(subobject, 0);
  if (vtable == nullptr) {
    return false;
  }
  const auto predicate_address =
      LoadAt<std::uintptr_t>(vtable, sizeof(void *));
  if (predicate_address == 0) {
    return false;
  }
  const auto predicate =
      reinterpret_cast<RegimentIdentityPredicate>(predicate_address);
  value = predicate(subobject);
  return true;
}

bool ReadObjectPredicateAtSlot(void *object, std::size_t vtable_slot_offset,
                               bool &value) noexcept {
  void *const vtable = LoadAt<void *>(object, 0);
  if (vtable == nullptr) {
    return false;
  }
  const auto predicate_address =
      LoadAt<std::uintptr_t>(vtable, vtable_slot_offset);
  if (predicate_address == 0) {
    return false;
  }
  const auto predicate =
      reinterpret_cast<RegimentIdentityPredicate>(predicate_address);
  value = predicate(object);
  return true;
}

bool ReadRegimentIdentity(void *regiment, bool &identity_valid) noexcept {
  return ReadSubobjectPredicate(regiment, kRegimentIdentitySubobjectOffset,
                                identity_valid);
}

ArmyStrengthSnapshot ReadArmyStrengthRow(
    const Bindings &bindings,
    const ArmyStrengthScopeEntry &scope_entry) noexcept {
  ArmyStrengthSnapshot result{};
  result.army_id = scope_entry.army_id;
  result.scope_role = scope_entry.role;
  result.war_ids = scope_entry.war_ids;

  void *const unit = ResolveStoredComponent(
      bindings.army_storage_slot, scope_entry.army_id, kArmyIdOffset);
  if (unit == nullptr) {
    result.unavailable_reason = "public_cunit_not_found";
    return result;
  }
  const auto internal_army_id =
      LoadAt<std::int32_t>(unit, kUnitArmyIdOffset);
  void *const internal_army = ResolveStoredComponent(
      bindings.army_internal_storage_slot, internal_army_id,
      kInternalArmyIdOffset);
  if (internal_army == nullptr) {
    result.unavailable_reason = "native_carmy_not_found";
    return result;
  }
  result.native_carmy_id_observable = true;
  result.native_carmy_id = internal_army_id;

  void *const regiment_ids = LoadAt<void *>(
      internal_army, kInternalArmyRegimentIdsOffset);
  const auto regiment_capacity = LoadAt<std::int32_t>(
      internal_army, kInternalArmyRegimentCapacityOffset);
  const auto regiment_count = LoadAt<std::int32_t>(
      internal_army, kInternalArmyRegimentCountOffset);
  if (regiment_capacity < 0 ||
      regiment_capacity > kMaximumArmyRegiments || regiment_count < 0 ||
      regiment_count > regiment_capacity ||
      (regiment_count > 0 && regiment_ids == nullptr)) {
    result.unavailable_reason = "regiment_array_invalid";
    return result;
  }

  std::int64_t current_soldiers = 0;
  std::int64_t maximum_soldiers = 0;
  std::int64_t ai_base_power_raw = 0;
  for (std::int32_t index = 0; index < regiment_count; ++index) {
    const auto regiment_id = LoadAt<std::int32_t>(
        regiment_ids, static_cast<std::size_t>(index) * sizeof(std::int32_t));
    void *const regiment = ResolveStoredComponent(
        bindings.regiment_storage_slot, regiment_id, kRegimentIdOffset);
    if (regiment == nullptr) {
      result.unavailable_reason = "regiment_not_found";
      return result;
    }

    bool identity_valid = false;
    if (!ReadRegimentIdentity(regiment, identity_valid)) {
      result.unavailable_reason = "identity_predicate_unavailable";
      return result;
    }
    if (!identity_valid) {
      result.unavailable_reason = "regiment_identity_invalid";
      return result;
    }
    const auto maximum = LoadAt<std::int32_t>(
        regiment, kRegimentMaximumSoldiersOffset);
    if (!CheckedAddNonnegative(maximum_soldiers, maximum)) {
      result.unavailable_reason = maximum < 0 ? "soldier_value_invalid"
                                              : "aggregate_overflow";
      return result;
    }
    const auto current = LoadAt<std::int32_t>(
        regiment, kRegimentCurrentSoldiersOffset);
    if (!CheckedAddNonnegative(current_soldiers, current)) {
      result.unavailable_reason = current < 0 ? "soldier_value_invalid"
                                              : "aggregate_overflow";
      return result;
    }
    const auto base_power = LoadAt<std::int64_t>(
        regiment, kRegimentAiBasePowerOffset);
    if (!CheckedAddSigned(ai_base_power_raw, base_power)) {
      result.unavailable_reason = "aggregate_overflow";
      return result;
    }
  }

  // The instruction mirror above owns generation/fallback/predicate safety.
  // Require it to match the same original helpers used by CK3 before
  // publishing, so an offset or predicate drift cannot silently become data.
  const auto native_current = bindings.get_army_current_soldiers(
      static_cast<std::byte *>(internal_army) +
          kInternalArmyRegimentIdsOffset,
      0);
  const auto native_maximum =
      bindings.get_army_maximum_soldiers(internal_army);
  if (native_current < 0 || native_maximum < 0 ||
      native_current != current_soldiers ||
      native_maximum != maximum_soldiers) {
    result.unavailable_reason = "native_helper_mismatch";
    return result;
  }

  result.available = true;
  result.regiment_count = regiment_count;
  result.current_soldiers = native_current;
  result.maximum_soldiers = native_maximum;
  result.ai_base_power_raw = ai_base_power_raw;
  return result;
}

using DatabaseObjectValidity = bool (*)(void *object);

bool ReadDatabaseObjectValidity(void *object, bool &valid) noexcept {
  if (object == nullptr) {
    valid = false;
    return true;
  }
  void *const vtable = LoadAt<void *>(object, 0);
  if (vtable == nullptr) {
    return false;
  }
  const auto function_address = LoadAt<std::uintptr_t>(vtable, 0);
  if (function_address == 0) {
    return false;
  }
  valid = reinterpret_cast<DatabaseObjectValidity>(function_address)(object);
  return true;
}

bool ReadCombatMaaType(void *regiment,
                       game::CombatMaaTypeSnapshot &output) noexcept {
  output = {};
  void *const maa_type = LoadAt<void *>(regiment, kRegimentMaaTypeOffset);
  if (maa_type == nullptr) {
    output.status = CombatObservationStatus::absent;
    return true;
  }
  bool valid = false;
  if (!ReadDatabaseObjectValidity(maa_type, valid)) {
    output.unavailable_reason = "maa_type_validity_unavailable";
    return false;
  }
  if (!valid) {
    output.status = CombatObservationStatus::absent;
    return true;
  }
  if (!ReadDatabaseObjectKey(maa_type, kDatabaseObjectKeyOffset,
                             output.key) ||
      output.key.empty()) {
    output.key.clear();
    output.unavailable_reason = "maa_type_key_unavailable";
    return false;
  }
  output.status = CombatObservationStatus::available;
  return true;
}

bool ReadCombatRegimentKind(
    const Bindings &bindings, void *regiment, std::int32_t regiment_id,
    game::CombatRegimentKindSnapshot &output) noexcept {
  output = {};
  output.unavailable_reason = "combat_type_unavailable";
  void *const combat_type =
      LoadAt<void *>(regiment, kRegimentInnerTypeOffset);
  if (combat_type == nullptr) {
    return false;
  }
  bool type_valid = false;
  if (!ReadDatabaseObjectValidity(combat_type, type_valid)) {
    output.unavailable_reason = "combat_type_validity_unavailable";
    return false;
  }
  const bool special = bindings.is_special_combat_regiment(regiment);
  if (ResolveStoredComponent(bindings.regiment_storage_slot, regiment_id,
                             kRegimentIdOffset) != regiment ||
      LoadAt<void *>(regiment, kRegimentInnerTypeOffset) != combat_type) {
    output.unavailable_reason = "regiment_generation_changed";
    return false;
  }
  output.status = CombatObservationStatus::available;
  output.value = !type_valid && !special ? "levy" : "men_at_arms";
  output.fights_in_main_phase =
      LoadAt<std::uint8_t>(combat_type,
                           kRegimentMainPhaseEligibilityOffset) != 0;
  if (ResolveStoredComponent(bindings.regiment_storage_slot, regiment_id,
                             kRegimentIdOffset) != regiment ||
      LoadAt<void *>(regiment, kRegimentInnerTypeOffset) != combat_type) {
    output = {};
    output.unavailable_reason = "regiment_generation_changed";
    return false;
  }
  output.unavailable_reason.clear();
  return true;
}

CombatCommanderSnapshot ReadCombatCommander(
    const Bindings &bindings, void *internal_army) noexcept {
  CombatCommanderSnapshot output{};
  const auto commander_id = LoadAt<std::int32_t>(
      internal_army, kInternalArmyCommanderCharacterIdOffset);
  if (commander_id == -1) {
    output.status = CombatObservationStatus::absent;
    return output;
  }
  if (commander_id < 0) {
    output.unavailable_reason = "commander_id_invalid";
    return output;
  }
  void *const commander = ResolveStoredComponent(
      bindings.character_storage_slot, commander_id, kCharacterIdOffset);
  if (commander == nullptr) {
    output.unavailable_reason = "commander_not_found";
    return output;
  }
  bool commander_valid = false;
  if (!ReadSubobjectPredicate(commander,
                              kCharacterValiditySubobjectOffset,
                              commander_valid) ||
      !commander_valid) {
    output.unavailable_reason = "commander_not_valid";
    return output;
  }
  if (bindings.get_army_commander(internal_army) != commander) {
    output.unavailable_reason = "native_commander_helper_mismatch";
    return output;
  }
  output.character_id = commander_id;
  output.generic_advantage_points =
      bindings.get_commander_advantage(commander, -1, false);
  output.generic_advantage_observable = true;
  output.status = CombatObservationStatus::available;
  return output;
}

bool ResolveCombatModifierOwner(const Bindings &bindings,
                                void *expected_unit,
                                void *internal_army,
                                void *&owner) noexcept {
  owner = nullptr;
  const auto unit_id =
      LoadAt<std::int32_t>(internal_army, kInternalArmyUnitIdOffset);
  void *const linked_unit = ResolveStoredComponent(
      bindings.army_storage_slot, unit_id, kArmyIdOffset);
  if (linked_unit == nullptr || linked_unit != expected_unit) {
    return false;
  }
  const auto owner_id =
      LoadAt<std::int32_t>(linked_unit, kArmyOwnerCharacterIdOffset);
  owner = ResolveStoredComponent(bindings.character_storage_slot, owner_id,
                                 kCharacterIdOffset);
  return owner != nullptr;
}

bool ReadEncounterEffectiveStats(
    const Bindings &bindings, void *regiment, void *target_province,
    std::int32_t regiment_id, std::int32_t target_province_id,
    game::CombatEffectiveStatsSnapshot &output) noexcept {
  output = {};
  if (target_province == nullptr ||
      ResolveStoredComponent(bindings.regiment_storage_slot, regiment_id,
                             kRegimentIdOffset) != regiment ||
      LoadAt<std::int32_t>(target_province, kProvinceIdOffset) !=
          target_province_id) {
    output.unavailable_reason = "encounter_province_unavailable";
    return false;
  }

  alignas(8) std::array<std::byte, 0x38> native_stats{};
  if (bindings.evaluate_regiment_stats_at_province(
          regiment, native_stats.data(), target_province) !=
          native_stats.data() ||
      ResolveStoredComponent(bindings.regiment_storage_slot, regiment_id,
                             kRegimentIdOffset) != regiment ||
      LoadAt<std::int32_t>(regiment, kRegimentIdOffset) != regiment_id ||
      LoadAt<std::int32_t>(target_province, kProvinceIdOffset) !=
          target_province_id) {
    output.unavailable_reason = "effective_stats_helper_failed";
    return false;
  }
  output.source_target_province_id = target_province_id;
  output.max_size = LoadAt<std::int32_t>(
      native_stats.data(), kEncounterMaaStatsMaximumOffset);
  output.siege_value_raw = LoadAt<std::int64_t>(
      native_stats.data(), kEncounterMaaStatsSiegeOffset);
  output.damage_raw = LoadAt<std::int64_t>(
      native_stats.data(), kEncounterMaaStatsDamageOffset);
  output.toughness_raw = LoadAt<std::int64_t>(
      native_stats.data(), kEncounterMaaStatsToughnessOffset);
  output.pursuit_raw = LoadAt<std::int64_t>(
      native_stats.data(), kEncounterMaaStatsPursuitOffset);
  output.screen_raw = LoadAt<std::int64_t>(
      native_stats.data(), kEncounterMaaStatsScreenOffset);
  if (output.max_size < 0) {
    output = {};
    output.unavailable_reason = "effective_stats_invalid";
    return false;
  }
  output.available = true;
  output.unavailable_reason.clear();
  return true;
}

struct NativeArrayHeader {
  void *data = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
};
static_assert(sizeof(NativeArrayHeader) == 0x10);

bool ReadCharacterModifierRaw(const Bindings &bindings, void *aggregator,
                              std::int32_t modifier_index,
                              std::int64_t &output) noexcept;

bool ReadCounterClassCount(const Bindings &bindings,
                           std::int32_t &class_count) noexcept {
  class_count = 0;
  void *const rules = bindings.get_combat_rules();
  if (rules == nullptr) {
    return false;
  }
  class_count = LoadAt<std::int32_t>(
      rules, kCombatRulesCounterClassCountOffset);
  return class_count > 0 && class_count <= kMaximumCounterClasses;
}

bool ReadCombatOwner(const Bindings &bindings, void *owner_character,
                     std::int32_t owner_character_id,
                     game::CombatOwnerSnapshot &output) noexcept {
  output = {};
  output.character_id = owner_character_id;
  if (owner_character == nullptr || owner_character_id < 0) {
    output.unavailable_reason = "counter_modifier_owner_unavailable";
    return false;
  }
  void *const aggregator =
      bindings.get_character_modifier_aggregator(owner_character);
  if (aggregator == nullptr ||
      !ReadCharacterModifierRaw(bindings, aggregator,
                                kCounterEfficiencyModifierIndex,
                                output.counter_efficiency_raw) ||
      !ReadCharacterModifierRaw(bindings, aggregator,
                                kCounterResistanceModifierIndex,
                                output.counter_resistance_raw)) {
    output.unavailable_reason = "counter_modifiers_unavailable";
    return false;
  }
  if (ResolveStoredComponent(bindings.character_storage_slot,
                             owner_character_id,
                             kCharacterIdOffset) != owner_character) {
    output = {};
    output.unavailable_reason = "counter_modifier_owner_generation_changed";
    return false;
  }
  output.status = CombatObservationStatus::available;
  output.unavailable_reason.clear();
  return true;
}

bool ReadCombatCounter(const Bindings &bindings, void *regiment,
                       std::int32_t regiment_id,
                       std::int32_t current_soldiers,
                       std::int32_t class_count,
                       game::CombatCounterSnapshot &output) noexcept {
  output = {};
  void *const inner_type =
      LoadAt<void *>(regiment, kRegimentInnerTypeOffset);
  if (inner_type == nullptr) {
    output.unavailable_reason = "regiment_inner_type_unavailable";
    return false;
  }
  const auto class_index = LoadAt<std::int32_t>(
      inner_type, kRegimentCounterClassOffset);
  if (class_index < 0) {
    output.status = CombatObservationStatus::absent;
    output.unavailable_reason.clear();
    return true;
  }
  if (class_index >= class_count) {
    output.unavailable_reason = "counter_class_out_of_range";
    return false;
  }

  void *const targets = LoadAt<void *>(
      inner_type, kRegimentCounterTargetsDataOffset);
  const auto target_count = LoadAt<std::int32_t>(
      inner_type, kRegimentCounterTargetsCountOffset);
  if (target_count < 0 || target_count > kMaximumCounterTargets ||
      (target_count > 0 && targets == nullptr)) {
    output.unavailable_reason = "counter_targets_invalid";
    return false;
  }
  output.targets.reserve(static_cast<std::size_t>(target_count));
  for (std::int32_t index = 0; index < target_count; ++index) {
    const auto *const target =
        static_cast<const std::byte *>(targets) +
        static_cast<std::size_t>(index) * kRegimentCounterTargetStride;
    game::CombatCounterTargetSnapshot row{};
    row.class_index = LoadAt<std::int32_t>(
        target, kRegimentCounterTargetClassOffset);
    row.effectiveness_raw = LoadAt<std::int64_t>(
        target, kRegimentCounterTargetEffectivenessOffset);
    if (row.class_index < 0 || row.class_index >= class_count) {
      output.targets.clear();
      output.unavailable_reason = "counter_target_class_out_of_range";
      return false;
    }
    output.targets.push_back(row);
  }

  alignas(8) std::array<std::byte, 0x60> synthetic_entry{};
  StoreAt(synthetic_entry.data(), 0x08, regiment_id);
  StoreAt(synthetic_entry.data(), 0x18,
          static_cast<std::int64_t>(current_soldiers) * kFixedPointScale);
  std::int64_t current_chunk_raw = -1;
  if (bindings.read_counter_current_chunk(
          synthetic_entry.data(), &current_chunk_raw) !=
          &current_chunk_raw ||
      current_chunk_raw < 0 ||
      ResolveStoredComponent(bindings.regiment_storage_slot, regiment_id,
                             kRegimentIdOffset) != regiment ||
      LoadAt<std::int32_t>(regiment, kRegimentIdOffset) != regiment_id) {
    output.targets.clear();
    output.unavailable_reason = "counter_current_chunk_unavailable";
    return false;
  }
  output.class_index = class_index;
  output.current_chunk_raw = current_chunk_raw;
  output.status = CombatObservationStatus::available;
  output.unavailable_reason.clear();
  return true;
}

bool ReadCombatRegiments(const Bindings &bindings, void *internal_army,
                         void *target_province,
                         std::int32_t target_province_id,
                         std::int32_t counter_class_count,
                         std::vector<CombatRegimentSnapshot> &output,
                         bool &has_unavailable_subdomain,
                         std::string &unavailable_reason) noexcept {
  output.clear();
  void *const regiment_ids = LoadAt<void *>(
      internal_army, kInternalArmyRegimentIdsOffset);
  const auto regiment_capacity = LoadAt<std::int32_t>(
      internal_army, kInternalArmyRegimentCapacityOffset);
  const auto regiment_count = LoadAt<std::int32_t>(
      internal_army, kInternalArmyRegimentCountOffset);
  if (regiment_capacity < 0 ||
      regiment_capacity > kMaximumArmyRegiments || regiment_count < 0 ||
      regiment_count > regiment_capacity ||
      (regiment_count > 0 && regiment_ids == nullptr)) {
    unavailable_reason = "regiment_array_invalid";
    return false;
  }

  std::vector<CombatRegimentSnapshot> rows;
  rows.reserve(static_cast<std::size_t>(regiment_count));
  for (std::int32_t index = 0; index < regiment_count; ++index) {
    CombatRegimentSnapshot row{};
    row.regiment_id = LoadAt<std::int32_t>(
        regiment_ids, static_cast<std::size_t>(index) * sizeof(std::int32_t));
    void *const regiment = ResolveStoredComponent(
        bindings.regiment_storage_slot, row.regiment_id, kRegimentIdOffset);
    if (regiment == nullptr) {
      unavailable_reason = "regiment_not_found";
      return false;
    }
    if (!ReadRegimentIdentity(regiment, row.identity_valid)) {
      unavailable_reason = "identity_predicate_unavailable";
      return false;
    }
    if (!row.identity_valid) {
      unavailable_reason = "regiment_identity_invalid";
      return false;
    }
    row.current_soldiers = LoadAt<std::int32_t>(
        regiment, kRegimentCurrentSoldiersOffset);
    row.maximum_soldiers = LoadAt<std::int32_t>(
        regiment, kRegimentMaximumSoldiersOffset);
    if (row.current_soldiers < 0 || row.maximum_soldiers < 0) {
      unavailable_reason = "soldier_value_invalid";
      return false;
    }
    if (!ReadCombatMaaType(regiment, row.maa_type)) {
      row.unavailable_reason = row.maa_type.unavailable_reason;
      has_unavailable_subdomain = true;
    } else {
      row.available = true;
    }
    if (!ReadCombatRegimentKind(bindings, regiment, row.regiment_id,
                                row.kind)) {
      has_unavailable_subdomain = true;
      row.available = false;
      row.unavailable_reason = row.kind.unavailable_reason;
    }
    if (!ReadEncounterEffectiveStats(bindings, regiment, target_province,
                                     row.regiment_id, target_province_id,
                                     row.effective_stats)) {
      has_unavailable_subdomain = true;
      row.available = false;
      row.unavailable_reason = row.effective_stats.unavailable_reason;
    }
    if (!ReadCombatCounter(bindings, regiment, row.regiment_id,
                           row.current_soldiers, counter_class_count,
                           row.counter)) {
      has_unavailable_subdomain = true;
    }
    rows.push_back(std::move(row));
  }
  output = std::move(rows);
  return true;
}

bool ReadCombatKnights(
    const Bindings &bindings, std::int32_t internal_army_id,
    const std::vector<CombatRegimentSnapshot> &regiments,
    std::vector<std::int32_t> &seen_knight_character_ids,
    std::vector<std::int32_t> &seen_knight_regiment_ids,
    game::CombatKnightsSnapshot &output) noexcept {
  output = {};
  for (const auto &regiment_row : regiments) {
    void *const regiment = ResolveStoredComponent(
        bindings.regiment_storage_slot, regiment_row.regiment_id,
        kRegimentIdOffset);
    if (regiment == nullptr) {
      output.unavailable_reason = "knight_source_regiment_unavailable";
      return false;
    }
    const auto knight_character_id = LoadAt<std::int32_t>(
        regiment, kRegimentKnightCharacterIdOffset);
    if (knight_character_id == -1) {
      continue;
    }
    if (!regiment_row.effective_stats.available) {
      output.unavailable_reason = "knight_effective_stats_unavailable";
      return false;
    }
    if (knight_character_id < 0 ||
        LoadAt<std::int32_t>(regiment, kRegimentArmyIdOffset) !=
            internal_army_id ||
        std::find(seen_knight_character_ids.begin(),
                  seen_knight_character_ids.end(),
                  knight_character_id) !=
            seen_knight_character_ids.end() ||
        std::find(seen_knight_regiment_ids.begin(),
                  seen_knight_regiment_ids.end(),
                  regiment_row.regiment_id) !=
            seen_knight_regiment_ids.end()) {
      output.unavailable_reason = "knight_identity_or_membership_invalid";
      return false;
    }
    void *const character = ResolveStoredComponent(
        bindings.character_storage_slot, knight_character_id,
        kCharacterIdOffset);
    bool character_valid = false;
    if (character == nullptr ||
        !ReadSubobjectPredicate(character,
                                kCharacterValiditySubobjectOffset,
                                character_valid) ||
        !character_valid) {
      output.unavailable_reason = "knight_character_unavailable";
      return false;
    }
    void *const knight_link =
        LoadAt<void *>(character, kCharacterKnightLinkOffset);
    if (knight_link == nullptr ||
        LoadAt<std::int32_t>(
            knight_link, kCharacterKnightLinkRegimentIdOffset) !=
            regiment_row.regiment_id) {
      output.unavailable_reason = "knight_character_regiment_backlink_invalid";
      return false;
    }

    game::CombatKnightSnapshot knight{};
    knight.character_id = knight_character_id;
    knight.source_regiment_id = regiment_row.regiment_id;
    knight.army_id = internal_army_id;
    knight.prowess = LoadAt<std::int32_t>(
        character, kCharacterEffectiveProwessOffset);
    const auto effective_prowess =
        std::max<std::int64_t>(1, knight.prowess);
    void *const effectiveness_context =
        bindings.get_knight_effectiveness_context(character);
    if (effectiveness_context == nullptr ||
        bindings.read_knight_effectiveness(
            &knight.knight_effectiveness_raw, effectiveness_context, 0) !=
            &knight.knight_effectiveness_raw ||
        knight.knight_effectiveness_raw < 0) {
      output.unavailable_reason = "knight_effectiveness_unavailable";
      return false;
    }
    if (ResolveStoredComponent(bindings.regiment_storage_slot,
                               regiment_row.regiment_id,
                               kRegimentIdOffset) != regiment ||
        ResolveStoredComponent(bindings.character_storage_slot,
                               knight_character_id,
                               kCharacterIdOffset) != character ||
        LoadAt<std::int32_t>(regiment,
                             kRegimentKnightCharacterIdOffset) !=
            knight_character_id ||
        LoadAt<std::int32_t>(regiment, kRegimentArmyIdOffset) !=
            internal_army_id ||
        LoadAt<void *>(character, kCharacterKnightLinkOffset) != knight_link ||
        LoadAt<std::int32_t>(
            knight_link, kCharacterKnightLinkRegimentIdOffset) !=
            regiment_row.regiment_id) {
      output.unavailable_reason = "knight_generation_changed";
      return false;
    }
    const auto damage_raw = regiment_row.effective_stats.damage_raw;
    const auto toughness_raw = regiment_row.effective_stats.toughness_raw;
    std::int64_t per_prowess_raw = 0;
    std::int64_t expected_damage_raw = 0;
    std::int64_t expected_toughness_raw = 0;
    if (!CheckedMultiplySigned(knight.knight_effectiveness_raw,
                               effective_prowess, per_prowess_raw) ||
        !CheckedMultiplySigned(per_prowess_raw,
                               *bindings.knight_damage_per_prowess,
                               expected_damage_raw) ||
        !CheckedMultiplySigned(per_prowess_raw,
                               *bindings.knight_toughness_per_prowess,
                               expected_toughness_raw)) {
      output.unavailable_reason = "knight_effectiveness_overflow";
      return false;
    }
    if (damage_raw != expected_damage_raw ||
        toughness_raw != expected_toughness_raw) {
      output.unavailable_reason = "knight_effectiveness_crosscheck_failed";
      return false;
    }
    knight.effective_damage_raw = damage_raw;
    knight.effective_toughness_raw = toughness_raw;
    knight.eligible = true;
    knight.participant_army_membership_verified = true;
    seen_knight_character_ids.push_back(knight_character_id);
    seen_knight_regiment_ids.push_back(regiment_row.regiment_id);
    output.members.push_back(knight);
  }
  std::sort(output.members.begin(), output.members.end(),
            [](const auto &left, const auto &right) {
              if (left.army_id != right.army_id) {
                return left.army_id < right.army_id;
              }
              if (left.source_regiment_id != right.source_regiment_id) {
                return left.source_regiment_id < right.source_regiment_id;
              }
              return left.character_id < right.character_id;
            });
  output.available = true;
  output.unavailable_reason.clear();
  return true;
}

game::CombatPrecontactWidthSnapshot ReadPrecontactCombatWidth(
    const Bindings &bindings,
    const std::vector<CombatArmyInputsSnapshot> &armies,
    const game::CombatTerrainSnapshot &terrain) noexcept {
  game::CombatPrecontactWidthSnapshot output{};
  if (!terrain.available) {
    output.unavailable_reason = "target_terrain_unavailable";
    return output;
  }
  std::int64_t friendly_total_raw = 0;
  std::int64_t enemy_total_raw = 0;
  for (const auto &army : armies) {
    if (!army.available || !army.regiments_observable) {
      output.unavailable_reason = "contact_participants_unavailable";
      return output;
    }
    auto &side_total =
        army.scope_role == ArmyStrengthScopeRole::active_war_enemy
            ? enemy_total_raw
            : friendly_total_raw;
    for (const auto &regiment : army.regiments) {
      if (!regiment.identity_valid) {
        output.unavailable_reason = "contact_regiment_identity_invalid";
        return output;
      }
      std::int64_t regiment_current_raw = 0;
      if (!CheckedMultiplySigned(regiment.current_soldiers,
                                 kFixedPointScale,
                                 regiment_current_raw) ||
          !CheckedAddSigned(side_total, regiment_current_raw)) {
        output.unavailable_reason = "contact_participant_total_overflow";
        return output;
      }
    }
  }
  std::int64_t combined_total_raw = friendly_total_raw;
  if (!CheckedAddSigned(combined_total_raw, enemy_total_raw)) {
    output.unavailable_reason = "contact_participant_total_overflow";
    return output;
  }
  const auto average_total_raw = combined_total_raw / 2;
  std::int64_t ratio_product = 0;
  if (!CheckedMultiplySigned(average_total_raw,
                             *bindings.base_combat_width_ratio,
                             ratio_product)) {
    output.unavailable_reason = "base_combat_width_overflow";
    return output;
  }
  const auto candidate_raw = ratio_product / kFixedPointScale;
  const auto candidate_width = candidate_raw / kFixedPointScale;
  const auto base_width = std::max<std::int64_t>(1, candidate_width);
  std::int64_t final_product = 0;
  if (!CheckedMultiplySigned(
          base_width, terrain.combat_width_multiplier_raw,
          final_product)) {
    output.unavailable_reason = "final_combat_width_overflow";
    return output;
  }
  const auto terrain_width = final_product / kFixedPointScale;
  const auto final_width = std::max<std::int64_t>(
      *bindings.minimum_combat_width, terrain_width);
  if (base_width > std::numeric_limits<std::int32_t>::max() ||
      final_width < std::numeric_limits<std::int32_t>::min() ||
      final_width > std::numeric_limits<std::int32_t>::max()) {
    output.unavailable_reason = "combat_width_out_of_range";
    return output;
  }
  output.base = static_cast<std::int32_t>(base_width);
  output.final = static_cast<std::int32_t>(final_width);
  output.available = true;
  output.unavailable_reason.clear();
  return output;
}

enum class ReadContactGeographyResult {
  available,
  invalid_encounter,
  unavailable,
};

enum class ReadAdjacencyKindResult {
  available,
  invalid_encounter,
  unavailable,
};

ReadAdjacencyKindResult ReadProvinceAdjacencyKind(
    void *origin_province, std::int32_t target_province_id,
    std::int32_t &kind) noexcept {
  kind = -1;
  if (origin_province == nullptr) {
    return ReadAdjacencyKindResult::unavailable;
  }
  void *const map_node =
      LoadAt<void *>(origin_province, kProvinceMapNodeOffset);
  if (map_node == nullptr) {
    return ReadAdjacencyKindResult::unavailable;
  }
  void *const adjacency_data =
      LoadAt<void *>(map_node, kMapNodeAdjacencyDataOffset);
  const auto adjacency_count = LoadAt<std::int32_t>(
      map_node, kMapNodeAdjacencyCountOffset);
  if (adjacency_count < 0 ||
      adjacency_count > kMaximumProvinceAdjacencies ||
      (adjacency_count > 0 && adjacency_data == nullptr)) {
    return ReadAdjacencyKindResult::unavailable;
  }
  bool found = false;
  for (std::int32_t index = 0; index < adjacency_count; ++index) {
    const auto *const edge =
        static_cast<const std::byte *>(adjacency_data) +
        static_cast<std::size_t>(index) * kMapAdjacencyStride;
    if (LoadAt<std::int32_t>(
            edge, kMapAdjacencyTargetProvinceIdOffset) !=
        target_province_id) {
      continue;
    }
    if (found) {
      return ReadAdjacencyKindResult::unavailable;
    }
    found = true;
    kind = LoadAt<std::int32_t>(edge, kMapAdjacencyKindOffset);
  }
  if (!found) {
    return ReadAdjacencyKindResult::invalid_encounter;
  }
  return ReadAdjacencyKindResult::available;
}

ReadContactGeographyResult ReadContactGeography(
    const Bindings &bindings, void *game_state, void *target_province,
    std::int32_t target_province_id, std::int32_t attacker_entry_province_id,
    bool attacker_enemy_side,
    const std::vector<CombatArmyInputsSnapshot> &armies,
    game::CombatCrossingSnapshot &crossing,
    game::CombatDefenderContextSnapshot &defender_context) noexcept {
  crossing = {};
  defender_context = {};
  void *const attacker_entry_province =
      ResolveProvince(game_state, attacker_entry_province_id);
  if (attacker_entry_province == nullptr) {
    crossing.unavailable_reason = "attacker_entry_province_unavailable";
    defender_context.unavailable_reason = crossing.unavailable_reason;
    return ReadContactGeographyResult::unavailable;
  }
  std::int32_t edge_kind = -1;
  const auto edge_result = ReadProvinceAdjacencyKind(
      attacker_entry_province, target_province_id, edge_kind);
  if (edge_result != ReadAdjacencyKindResult::available) {
    crossing.unavailable_reason =
        edge_result == ReadAdjacencyKindResult::invalid_encounter
            ? "entry_target_edge_missing"
            : "entry_target_adjacency_unavailable";
    defender_context.unavailable_reason = crossing.unavailable_reason;
    return edge_result == ReadAdjacencyKindResult::invalid_encounter
               ? ReadContactGeographyResult::invalid_encounter
               : ReadContactGeographyResult::unavailable;
  }

  switch (edge_kind) {
  case 0:
    crossing.kind = "none";
    break;
  case 1:
    crossing.kind = "strait";
    break;
  case 2:
    crossing.kind = "river";
    break;
  case 3:
    crossing.kind = "large_river";
    break;
  case 4:
    crossing.unavailable_reason = "impassable_entry_target_edge";
    defender_context.unavailable_reason = crossing.unavailable_reason;
    return ReadContactGeographyResult::invalid_encounter;
  case 5:
  case 6:
    crossing.unavailable_reason = "non_contact_adjacency_encoding";
    defender_context.unavailable_reason = crossing.unavailable_reason;
    return ReadContactGeographyResult::invalid_encounter;
  default:
    crossing.unavailable_reason = "adjacency_kind_out_of_range";
    defender_context.unavailable_reason = crossing.unavailable_reason;
    return ReadContactGeographyResult::unavailable;
  }

  if (ResolveProvince(game_state, attacker_entry_province_id) !=
          attacker_entry_province ||
      ResolveProvince(game_state, target_province_id) != target_province) {
    crossing = {};
    defender_context = {};
    crossing.unavailable_reason = "hypothetical_contact_identity_changed";
    defender_context.unavailable_reason = crossing.unavailable_reason;
    return ReadContactGeographyResult::unavailable;
  }
  crossing.available = true;
  crossing.unavailable_reason.clear();
  defender_context.available = true;
  defender_context.defender_side =
      attacker_enemy_side ? "player_or_allied" : "enemy";
  defender_context.unavailable_reason.clear();

  std::int32_t defender_owner_character_id = -1;
  for (const auto &army : armies) {
    if (army.encounter_role != "defender") {
      continue;
    }
    if (army.owner.status != CombatObservationStatus::available) {
      defender_context.holding_unavailable_reason =
          "defender_owner_unavailable";
      return ReadContactGeographyResult::available;
    }
    // CCombat side population establishes the primary participant from the
    // first inserted army. A hypothetical side uses explicit request order as
    // that insertion order; current Province participant order is irrelevant.
    defender_owner_character_id = army.owner.character_id;
    break;
  }
  if (defender_owner_character_id == -1) {
    defender_context.holding_unavailable_reason = "defender_side_missing";
    return ReadContactGeographyResult::available;
  }
  void *const defender_owner = ResolveStoredComponent(
      bindings.character_storage_slot, defender_owner_character_id,
      kCharacterIdOffset);
  if (defender_owner == nullptr) {
    defender_context.holding_unavailable_reason =
        "defender_owner_generation_changed";
    return ReadContactGeographyResult::available;
  }
  const bool holding_defender =
      bindings.is_holding_defender(defender_owner, target_province);
  if (ResolveProvince(game_state, attacker_entry_province_id) !=
          attacker_entry_province ||
      ResolveProvince(game_state, target_province_id) != target_province) {
    crossing = {};
    defender_context = {};
    crossing.unavailable_reason = "hypothetical_contact_identity_changed";
    defender_context.unavailable_reason = crossing.unavailable_reason;
    return ReadContactGeographyResult::unavailable;
  }
  if (ResolveStoredComponent(bindings.character_storage_slot,
                             defender_owner_character_id,
                             kCharacterIdOffset) != defender_owner) {
    defender_context.holding_unavailable_reason =
        "holding_context_identity_changed";
    return ReadContactGeographyResult::available;
  }
  defender_context.holding_defender_status =
      CombatObservationStatus::available;
  defender_context.holding_defender = holding_defender;
  defender_context.holding_unavailable_reason.clear();
  return ReadContactGeographyResult::available;
}

bool AppendOngoingCombat(const Bindings &bindings, void *game_state,
                         void *internal_army,
                         std::vector<OngoingCombatInputsSnapshot> &output,
                         bool &has_unavailable_subdomain) noexcept {
  const auto combat_id = LoadAt<std::int32_t>(
      internal_army, kInternalArmyCombatIdOffset);
  if (combat_id == -1) {
    return true;
  }
  OngoingCombatInputsSnapshot row{};
  if (combat_id < 0) {
    row.unavailable_reason = "combat_id_invalid";
    has_unavailable_subdomain = true;
    output.push_back(std::move(row));
    return true;
  }
  const auto existing = std::find_if(
      output.begin(), output.end(), [combat_id](const auto &candidate) {
        return candidate.combat_id_observable &&
               candidate.combat_id == combat_id;
      });
  if (existing != output.end()) {
    return true;
  }
  row.combat_id_observable = true;
  row.combat_id = combat_id;
  void *const combat = ResolveStoredComponent(
      bindings.combat_storage_slot, combat_id, kCombatIdOffset);
  if (combat == nullptr) {
    row.unavailable_reason = "combat_not_found";
    has_unavailable_subdomain = true;
    output.push_back(std::move(row));
    return true;
  }
  void *const province = LoadAt<void *>(combat, kCombatProvinceOffset);
  if (province == nullptr) {
    row.unavailable_reason = "combat_province_unavailable";
    has_unavailable_subdomain = true;
    output.push_back(std::move(row));
    return true;
  }
  row.province_id = LoadAt<std::int32_t>(province, kProvinceIdOffset);
  if (ResolveProvince(game_state, row.province_id) != province) {
    row.province_id = -1;
    row.unavailable_reason = "combat_province_unavailable";
    has_unavailable_subdomain = true;
    output.push_back(std::move(row));
    return true;
  }
  row.phase = LoadAt<std::int32_t>(combat, kCombatPhaseOffset);
  row.phase_day = LoadAt<std::int32_t>(combat, kCombatPhaseDayOffset);
  row.base_combat_width =
      LoadAt<std::int32_t>(combat, kCombatBaseWidthOffset);
  row.final_combat_width =
      LoadAt<std::int32_t>(combat, kCombatFinalWidthOffset);
  row.side_0_roll = LoadAt<std::int32_t>(combat, kCombatSide0RollOffset);
  row.side_1_roll = LoadAt<std::int32_t>(combat, kCombatSide1RollOffset);
  row.base_advantage =
      LoadAt<std::int64_t>(combat, kCombatBaseAdvantageOffset);
  row.resolved_advantage =
      LoadAt<std::int64_t>(combat, kCombatResolvedAdvantageOffset);
  if (row.phase < 0 || row.phase > 3 || row.phase_day < 0 ||
      row.base_combat_width < 0 || row.final_combat_width < 0) {
    row.province_id = -1;
    row.unavailable_reason = "combat_state_invalid";
    has_unavailable_subdomain = true;
    output.push_back(std::move(row));
    return true;
  }
  if (ResolveStoredComponent(bindings.combat_storage_slot, combat_id,
                             kCombatIdOffset) != combat) {
    row.province_id = -1;
    row.unavailable_reason = "combat_generation_changed";
    has_unavailable_subdomain = true;
    output.push_back(std::move(row));
    return true;
  }
  row.available = true;
  output.push_back(std::move(row));
  return true;
}

CombatCandidateProvinceSnapshot ReadCombatCandidateProvince(
    const Bindings &bindings, void *game_state,
    std::int32_t province_id) noexcept {
  CombatCandidateProvinceSnapshot output{};
  output.province_id = province_id;
  void *const province = ResolveProvince(game_state, province_id);
  if (province == nullptr) {
    output.unavailable_reason = "province_not_found";
    output.terrain.unavailable_reason = output.unavailable_reason;
    return output;
  }
  void *const terrain = bindings.get_province_terrain(province);
  if (terrain == nullptr ||
      !ReadDatabaseObjectKey(terrain, kDatabaseObjectKeyOffset,
                             output.terrain.key) ||
      output.terrain.key.empty()) {
    output.terrain.key.clear();
    output.unavailable_reason = "terrain_unavailable";
    output.terrain.unavailable_reason = output.unavailable_reason;
    return output;
  }
  output.terrain.combat_width_multiplier_raw = LoadAt<std::int64_t>(
      terrain, kTerrainCombatWidthMultiplierOffset);
  if (ResolveProvince(game_state, province_id) != province ||
      bindings.get_province_terrain(province) != terrain) {
    output.terrain = {};
    output.unavailable_reason = "terrain_generation_changed";
    output.terrain.unavailable_reason = output.unavailable_reason;
    return output;
  }
  output.terrain.available = true;
  output.available = true;
  return output;
}

bool ReadCharacterModifierRaw(const Bindings &bindings, void *aggregator,
                              std::int32_t modifier_index,
                              std::int64_t &output) noexcept {
  output = 0;
  return bindings.read_character_modifier(aggregator, &output,
                                          modifier_index) == &output;
}

CombatCommanderContextSnapshot ReadCommanderRollContext(
    const Bindings &bindings, std::int32_t province_id, void *terrain,
    const CombatCommanderSnapshot &commander) noexcept {
  CombatCommanderContextSnapshot output{};
  output.province_id = province_id;
  if (commander.status == CombatObservationStatus::absent) {
    output.available = true;
    output.unavailable_reason.clear();
    return output;
  }
  if (commander.status != CombatObservationStatus::available) {
    output.unavailable_reason = "commander_unavailable";
    return output;
  }
  void *const character = ResolveStoredComponent(
      bindings.character_storage_slot, commander.character_id,
      kCharacterIdOffset);
  if (character == nullptr || terrain == nullptr) {
    output.unavailable_reason = "commander_context_object_unavailable";
    return output;
  }
  void *const aggregator =
      bindings.get_character_modifier_aggregator(character);
  if (aggregator == nullptr) {
    output.unavailable_reason = "commander_modifier_aggregator_unavailable";
    return output;
  }

  const auto terrain_min_index = static_cast<std::int32_t>(
      LoadAt<std::uint16_t>(
          terrain, kTerrainCommanderMinRollModifierIndexOffset));
  const auto terrain_max_index = static_cast<std::int32_t>(
      LoadAt<std::uint16_t>(
          terrain, kTerrainCommanderMaxRollModifierIndexOffset));
  std::int64_t character_min_raw = 0;
  std::int64_t character_max_raw = 0;
  std::int64_t terrain_min_raw = 0;
  std::int64_t terrain_max_raw = 0;
  if (!ReadCharacterModifierRaw(bindings, aggregator,
                                kCommanderMinRollModifierIndex,
                                character_min_raw) ||
      !ReadCharacterModifierRaw(bindings, aggregator,
                                kCommanderMaxRollModifierIndex,
                                character_max_raw) ||
      !ReadCharacterModifierRaw(bindings, aggregator, terrain_min_index,
                                terrain_min_raw) ||
      !ReadCharacterModifierRaw(bindings, aggregator, terrain_max_index,
                                terrain_max_raw)) {
    output.unavailable_reason = "commander_modifier_unavailable";
    return output;
  }
  if (ResolveStoredComponent(bindings.character_storage_slot,
                             commander.character_id,
                             kCharacterIdOffset) != character) {
    output.unavailable_reason = "commander_generation_changed";
    return output;
  }

  const auto minimum =
      static_cast<std::int64_t>(*bindings.commander_min_roll) +
      character_min_raw / kFixedPointScale +
      terrain_min_raw / kFixedPointScale;
  const auto maximum =
      static_cast<std::int64_t>(*bindings.commander_max_roll) +
      character_max_raw / kFixedPointScale +
      terrain_max_raw / kFixedPointScale;
  if (minimum < std::numeric_limits<std::int32_t>::min() ||
      minimum > std::numeric_limits<std::int32_t>::max() ||
      maximum < std::numeric_limits<std::int32_t>::min() ||
      maximum > std::numeric_limits<std::int32_t>::max()) {
    output.unavailable_reason = "commander_roll_bounds_overflow";
    return output;
  }
  output.effective_min_roll = static_cast<std::int32_t>(minimum);
  output.effective_max_roll = static_cast<std::int32_t>(maximum);
  output.available = true;
  output.unavailable_reason.clear();
  return output;
}

CombatArmyInputsSnapshot ReadCombatArmyInputsRow(
    const Bindings &bindings, void *game_state, void *target_province,
    void *target_terrain, std::int32_t target_province_id,
    std::int32_t counter_class_count,
    const ArmyStrengthScopeEntry &scope_entry,
    std::vector<OngoingCombatInputsSnapshot> &ongoing_combats,
    bool &has_unavailable_subdomain) noexcept {
  CombatArmyInputsSnapshot output{};
  output.army_id = scope_entry.army_id;
  output.scope_role = scope_entry.role;
  output.war_ids = scope_entry.war_ids;

  void *const unit = ResolveStoredComponent(
      bindings.army_storage_slot, scope_entry.army_id, kArmyIdOffset);
  if (unit == nullptr) {
    output.unavailable_reason = "public_cunit_not_found";
    return output;
  }
  void *const current_province =
      LoadAt<void *>(unit, kArmyCurrentProvinceOffset);
  if (current_province != nullptr) {
    const auto current_province_id =
        LoadAt<std::int32_t>(current_province, kProvinceIdOffset);
    if (ResolveProvince(game_state, current_province_id) == current_province) {
      output.current_province_observable = true;
      output.current_province_id = current_province_id;
    }
  }

  const auto internal_army_id =
      LoadAt<std::int32_t>(unit, kUnitArmyIdOffset);
  void *const internal_army = ResolveStoredComponent(
      bindings.army_internal_storage_slot, internal_army_id,
      kInternalArmyIdOffset);
  if (internal_army == nullptr) {
    output.unavailable_reason = "native_carmy_not_found";
    return output;
  }
  output.native_carmy_id_observable = true;
  output.native_carmy_id = internal_army_id;
  void *modifier_owner = nullptr;
  if (!ResolveCombatModifierOwner(bindings, unit, internal_army,
                                  modifier_owner)) {
    output.unavailable_reason = "modifier_owner_not_found";
    return output;
  }
  const auto owner_character_id =
      LoadAt<std::int32_t>(unit, kArmyOwnerCharacterIdOffset);
  if (!ReadCombatOwner(bindings, modifier_owner, owner_character_id,
                       output.owner)) {
    has_unavailable_subdomain = true;
  }
  output.commander = ReadCombatCommander(bindings, internal_army);
  if (output.commander.status == CombatObservationStatus::unavailable) {
    has_unavailable_subdomain = true;
  }
  output.commander.battle_context = ReadCommanderRollContext(
      bindings, target_province_id, target_terrain, output.commander);
  if (!output.commander.battle_context.available) {
    has_unavailable_subdomain = true;
  }

  std::string regiment_failure;
  if (!ReadCombatRegiments(bindings, internal_army, target_province,
                           target_province_id, counter_class_count,
                           output.regiments,
                           has_unavailable_subdomain, regiment_failure)) {
    output.regiments.clear();
    output.unavailable_reason = std::move(regiment_failure);
    return output;
  }
  output.regiments_observable = true;
  if (!AppendOngoingCombat(bindings, game_state, internal_army,
                           ongoing_combats,
                           has_unavailable_subdomain)) {
    output.unavailable_reason = "combat_observation_failed";
    return output;
  }
  output.available = true;
  return output;
}

bool BuildCounterSideEntries(
    const Bindings &bindings,
    const std::vector<CombatArmyInputsSnapshot> &armies, bool enemy_side,
    std::vector<std::array<std::byte, 0x60>> &entries,
    std::int32_t &modifier_owner_character_id,
    std::string &unavailable_reason) noexcept {
  entries.clear();
  modifier_owner_character_id = -1;
  bool found_side_army = false;
  for (const auto &army : armies) {
    const bool is_enemy =
        army.scope_role == ArmyStrengthScopeRole::active_war_enemy;
    if (is_enemy != enemy_side) {
      continue;
    }
    found_side_army = true;
    if (!army.available || !army.regiments_observable ||
        army.owner.status != CombatObservationStatus::available) {
      unavailable_reason = "counter_side_army_unavailable";
      return false;
    }
    if (modifier_owner_character_id == -1) {
      modifier_owner_character_id = army.owner.character_id;
    }
    for (const auto &regiment : army.regiments) {
      if (!regiment.identity_valid) {
        unavailable_reason = "counter_regiment_identity_invalid";
        return false;
      }
      if (regiment.counter.status == CombatObservationStatus::unavailable) {
        unavailable_reason = "counter_operand_unavailable";
        return false;
      }
      void *const native_regiment = ResolveStoredComponent(
          bindings.regiment_storage_slot, regiment.regiment_id,
          kRegimentIdOffset);
      if (native_regiment == nullptr) {
        unavailable_reason = "counter_regiment_generation_mismatch";
        return false;
      }
      entries.emplace_back();
      auto &entry = entries.back();
      StoreAt(entry.data(), 0x08, regiment.regiment_id);
      StoreAt(entry.data(), 0x18,
              static_cast<std::int64_t>(regiment.current_soldiers) *
                  kFixedPointScale);
    }
  }
  if (!found_side_army || modifier_owner_character_id < 0) {
    unavailable_reason = "counter_side_missing";
    return false;
  }
  return true;
}

game::CombatCounterResolutionSnapshot ReadCounterResolution(
    const Bindings &bindings,
    const std::vector<CombatArmyInputsSnapshot> &armies,
    std::int32_t class_count, bool countered_enemy_side) noexcept {
  game::CombatCounterResolutionSnapshot output{};
  output.countered_side =
      countered_enemy_side ? "enemy" : "player_or_allied";
  output.countering_side =
      countered_enemy_side ? "player_or_allied" : "enemy";
  output.class_count = class_count;

  std::vector<std::array<std::byte, 0x60>> countered_entries;
  std::vector<std::array<std::byte, 0x60>> countering_entries;
  if (!BuildCounterSideEntries(
          bindings, armies, countered_enemy_side, countered_entries,
          output.countered_modifier_owner_character_id,
          output.unavailable_reason) ||
      !BuildCounterSideEntries(
          bindings, armies, !countered_enemy_side, countering_entries,
          output.countering_modifier_owner_character_id,
          output.unavailable_reason)) {
    return output;
  }

  void *const countered_owner = ResolveStoredComponent(
      bindings.character_storage_slot,
      output.countered_modifier_owner_character_id, kCharacterIdOffset);
  void *const countering_owner = ResolveStoredComponent(
      bindings.character_storage_slot,
      output.countering_modifier_owner_character_id, kCharacterIdOffset);
  void *const countered_aggregator =
      countered_owner == nullptr
          ? nullptr
          : bindings.get_character_modifier_aggregator(countered_owner);
  void *const countering_aggregator =
      countering_owner == nullptr
          ? nullptr
          : bindings.get_character_modifier_aggregator(countering_owner);
  if (countered_aggregator == nullptr || countering_aggregator == nullptr ||
      bindings.get_counter_context_scale(
          &output.context_scale_raw, countered_aggregator,
          countering_aggregator) != &output.context_scale_raw ||
      output.context_scale_raw < 0) {
    output.unavailable_reason = "counter_context_scale_unavailable";
    return output;
  }

  NativeArrayHeader countered_header{
      countered_entries.empty() ? nullptr : countered_entries.data(),
      static_cast<std::int32_t>(countered_entries.size()),
      static_cast<std::int32_t>(countered_entries.size())};
  NativeArrayHeader countering_header{
      countering_entries.empty() ? nullptr : countering_entries.data(),
      static_cast<std::int32_t>(countering_entries.size()),
      static_cast<std::int32_t>(countering_entries.size())};
  output.damage_retention_by_class_raw.assign(
      static_cast<std::size_t>(class_count), kFixedPointScale);
  NativeArrayHeader output_header{
      output.damage_retention_by_class_raw.data(), class_count, class_count};
  bindings.resolve_counter_classes(
      &countered_header, &countering_header, &output_header,
      output.context_scale_raw);
  if (output_header.data != output.damage_retention_by_class_raw.data() ||
      output_header.capacity != class_count ||
      output_header.count != class_count) {
    output.damage_retention_by_class_raw.clear();
    output.unavailable_reason = "counter_resolution_output_reallocated";
    return output;
  }
  const auto validate_entries = [&bindings](const auto &entries) {
    for (const auto &entry : entries) {
      const auto regiment_id =
          LoadAt<std::int32_t>(entry.data(), 0x08);
      if (ResolveStoredComponent(bindings.regiment_storage_slot,
                                 regiment_id,
                                 kRegimentIdOffset) == nullptr) {
        return false;
      }
    }
    return true;
  };
  if (!validate_entries(countered_entries) ||
      !validate_entries(countering_entries)) {
    output.damage_retention_by_class_raw.clear();
    output.unavailable_reason = "counter_regiment_generation_changed";
    return output;
  }
  if (ResolveStoredComponent(bindings.character_storage_slot,
                             output.countered_modifier_owner_character_id,
                             kCharacterIdOffset) != countered_owner ||
      ResolveStoredComponent(bindings.character_storage_slot,
                             output.countering_modifier_owner_character_id,
                             kCharacterIdOffset) != countering_owner) {
    output.damage_retention_by_class_raw.clear();
    output.unavailable_reason = "counter_owner_generation_changed";
    return output;
  }
  output.available = true;
  output.unavailable_reason.clear();
  return output;
}

constexpr std::array<std::string_view, 6> kWarExitDeltaKinds{
    "prestige", "prestige_experience", "piety", "piety_experience",
    "legitimacy", "stress"};

std::optional<std::size_t>
WarExitDeltaKindIndex(WarExitPreviewRowKind kind) noexcept {
  switch (kind) {
  case WarExitPreviewRowKind::prestige:
    return 0;
  case WarExitPreviewRowKind::prestige_experience:
    return 1;
  case WarExitPreviewRowKind::piety:
    return 2;
  case WarExitPreviewRowKind::piety_experience:
    return 3;
  case WarExitPreviewRowKind::legitimacy:
    return 4;
  case WarExitPreviewRowKind::stress:
    return 5;
  default:
    return std::nullopt;
  }
}

void SetWarExitMaterializeReason(
    std::string_view stage, const WarExitPreviewRow *row,
    std::size_t row_index, std::size_t row_count,
    std::int32_t truce_count, std::size_t gold_count) noexcept {
  if (!g_last_war_exit_preview_unavailable_reason.empty()) {
    return;
  }
  const auto kind = row == nullptr
                        ? std::uint32_t{0xFFFFFFFF}
                        : static_cast<std::uint32_t>(row->kind);
  const auto first_id =
      row == nullptr ? std::int32_t{-1} : row->first_character_id;
  const auto second_id =
      row == nullptr ? std::int32_t{-1} : row->second_character_id;
  const auto raw = row == nullptr ? std::int64_t{0} : row->raw;
  const int written = std::snprintf(
      g_war_exit_preview_diagnostic_buffer.data(),
      g_war_exit_preview_diagnostic_buffer.size(),
      "dry_preview.materialize_%.*s:row_index=%llu,row_count=%llu,"
      "kind=%u,first_id=%d,second_id=%d,raw=%lld,truce_count=%d,"
      "gold_count=%llu,root_vtable_rva=0x%llX,selector_count=%d,"
      "default_child_vtable_rva=0x%llX,root_span=%d/%d,hidden_count=%d,"
      "hidden_index=%d,hidden_span=%d/%d,"
      "hidden_child0_vtable_rva=0x%llX",
      static_cast<int>(stage.size()), stage.data(),
      static_cast<unsigned long long>(row_index),
      static_cast<unsigned long long>(row_count), kind, first_id, second_id,
      static_cast<long long>(raw), truce_count,
      static_cast<unsigned long long>(gold_count),
      static_cast<unsigned long long>(g_war_exit_loaded_root_vtable_rva),
      g_war_exit_loaded_root_selector_count,
      static_cast<unsigned long long>(
          g_war_exit_loaded_default_child_vtable_rva),
      g_war_exit_loaded_root_count, g_war_exit_loaded_root_capacity,
      g_war_exit_loaded_hidden_count, g_war_exit_loaded_hidden_index,
      g_war_exit_loaded_hidden_child_count,
      g_war_exit_loaded_hidden_capacity,
      static_cast<unsigned long long>(
          g_war_exit_loaded_hidden_child0_vtable_rva));
  if (written <= 0 ||
      static_cast<std::size_t>(written) >=
          g_war_exit_preview_diagnostic_buffer.size()) {
    SetWarExitPreviewUnavailableReason("dry_preview.materialize_unknown");
    return;
  }
  std::size_t used = static_cast<std::size_t>(written);
  if (g_war_exit_loaded_root_count > 0) {
    const auto child_count = std::min<std::size_t>(
        static_cast<std::size_t>(g_war_exit_loaded_root_count),
        kMaximumWarExitDiagnosticRootChildren);
    int appended = std::snprintf(
        g_war_exit_preview_diagnostic_buffer.data() + used,
        g_war_exit_preview_diagnostic_buffer.size() - used,
        ",root_children=");
    if (appended <= 0 || static_cast<std::size_t>(appended) >=
                             g_war_exit_preview_diagnostic_buffer.size() -
                                 used) {
      SetWarExitPreviewUnavailableReason("dry_preview.materialize_unknown");
      return;
    }
    used += static_cast<std::size_t>(appended);
    for (std::size_t index = 0; index < child_count; ++index) {
      appended = std::snprintf(
          g_war_exit_preview_diagnostic_buffer.data() + used,
          g_war_exit_preview_diagnostic_buffer.size() - used,
          "%s0x%llX@0x%llX", index == 0 ? "" : "/",
          static_cast<unsigned long long>(
              g_war_exit_loaded_root_child_pointers[index]),
          static_cast<unsigned long long>(
              g_war_exit_loaded_root_child_vtable_rvas[index]));
      if (appended <= 0 || static_cast<std::size_t>(appended) >=
                               g_war_exit_preview_diagnostic_buffer.size() -
                                   used) {
        SetWarExitPreviewUnavailableReason("dry_preview.materialize_unknown");
        return;
      }
      used += static_cast<std::size_t>(appended);
    }
  }
  g_last_war_exit_preview_unavailable_reason = std::string_view(
      g_war_exit_preview_diagnostic_buffer.data(), used);
}

bool MaterializeWarExitPreview(
    const Bindings &bindings, const std::vector<WarExitPreviewRow> &rows,
    void *effect_context, std::int32_t attacker_id,
    std::int32_t defender_id, std::int32_t date_raw, bool white_peace,
    game::WarExitOutcomeSnapshot &outcome,
    std::array<std::int32_t, 12> &resource_callback_counts) noexcept {
  outcome.primary_gold_transfers.clear();
  outcome.primary_resource_deltas.clear();
  outcome.prisoner_releases.clear();
  resource_callback_counts.fill(0);
  try {
    outcome.primary_resource_deltas.reserve(12);
    for (const auto character_id : {attacker_id, defender_id}) {
      for (const auto kind : kWarExitDeltaKinds) {
        outcome.primary_resource_deltas.push_back(
            {character_id, std::string(kind), {0, kFixedPointScale}});
      }
    }
  } catch (...) {
    SetWarExitMaterializeReason("allocation", nullptr, 0, rows.size(), 0,
                                0);
    return false;
  }

  std::int32_t truce_count = 0;
  for (std::size_t row_index = 0; row_index < rows.size(); ++row_index) {
    const auto &row = rows[row_index];
    const auto resource_kind = WarExitDeltaKindIndex(row.kind);
    if (resource_kind.has_value()) {
      const std::size_t character_offset =
          row.first_character_id == attacker_id
              ? 0U
              : (row.first_character_id == defender_id ? 6U : 12U);
      if (character_offset == 12U) {
        SetWarExitMaterializeReason(
            "resource_character", &row, row_index, rows.size(), truce_count,
            outcome.primary_gold_transfers.size());
        return false;
      }
      const auto index = character_offset + resource_kind.value();
      if (!CheckedAddSigned(
              outcome.primary_resource_deltas[index].value.raw, row.raw) ||
          resource_callback_counts[index] ==
              std::numeric_limits<std::int32_t>::max()) {
        SetWarExitMaterializeReason(
            "resource_accumulate", &row, row_index, rows.size(), truce_count,
            outcome.primary_gold_transfers.size());
        return false;
      }
      ++resource_callback_counts[index];
      continue;
    }
    if (row.kind == WarExitPreviewRowKind::gold_transfer) {
      if (white_peace || row.first_character_id != attacker_id ||
          row.second_character_id != defender_id || row.raw < 0 ||
          !outcome.primary_gold_transfers.empty()) {
        SetWarExitMaterializeReason(
            "gold_row", &row, row_index, rows.size(), truce_count,
            outcome.primary_gold_transfers.size());
        return false;
      }
      try {
        outcome.primary_gold_transfers.push_back(
            {attacker_id, defender_id, {row.raw, kFixedPointScale}});
      } catch (...) {
        SetWarExitMaterializeReason(
            "gold_allocation", &row, row_index, rows.size(), truce_count,
            outcome.primary_gold_transfers.size());
        return false;
      }
      continue;
    }
    if (row.kind != WarExitPreviewRowKind::truce ||
        row.first_character_id != attacker_id ||
        row.second_character_id != defender_id || row.effect_node == nullptr ||
        ++truce_count != 1) {
      SetWarExitMaterializeReason(
          "truce_row", &row, row_index, rows.size(), truce_count,
          outcome.primary_gold_transfers.size());
      return false;
    }
    const auto days = bindings.evaluate_truce_duration_days(
        static_cast<std::byte *>(row.effect_node) +
            kTruceEffectDurationScriptValueOffset,
        effect_context, static_cast<std::byte *>(effect_context) + 0x28);
    const auto expiry = static_cast<std::int64_t>(date_raw) +
                        24LL * static_cast<std::int64_t>(days);
    if (days < 0 || expiry < std::numeric_limits<std::int32_t>::min() ||
        expiry > std::numeric_limits<std::int32_t>::max()) {
      SetWarExitMaterializeReason(
          "truce_duration", &row, row_index, rows.size(), truce_count,
          outcome.primary_gold_transfers.size());
      return false;
    }
    outcome.truce = {attacker_id, defender_id, days, date_raw,
                     static_cast<std::int32_t>(expiry)};
  }
  if (truce_count != 1 ||
      (white_peace && !outcome.primary_gold_transfers.empty()) ||
      (!white_peace && outcome.primary_gold_transfers.size() != 1U)) {
    SetWarExitMaterializeReason(
        "final_shape", nullptr, rows.size(), rows.size(), truce_count,
        outcome.primary_gold_transfers.size());
    return false;
  }
  outcome.complete = true;
  return true;
}

bool FinalizeWarExitPrestigeFactor(
    game::WarExitOutcomeSnapshot &white_peace,
    const std::array<std::int32_t, 12> &white_peace_counts,
    game::WarExitOutcomeSnapshot &attacker_defeat,
    const std::array<std::int32_t, 12> &attacker_defeat_counts,
    std::int64_t white_peace_factor_raw,
    std::int64_t attacker_defeat_factor_raw) noexcept {
  if (white_peace.primary_resource_deltas.size() != 12U ||
      attacker_defeat.primary_resource_deltas.size() != 12U ||
      white_peace_counts[0] != 1 || white_peace_counts[6] != 0 ||
      attacker_defeat_counts[0] != 1 || attacker_defeat_counts[6] != 1 ||
      white_peace_factor_raw < 0 ||
      white_peace_factor_raw != attacker_defeat_factor_raw) {
    return false;
  }
  const auto white_peace_attacker_prestige =
      white_peace.primary_resource_deltas[0].value.raw;
  std::int64_t expected_white_peace = 0;
  if (!CheckedMultiplySigned(white_peace_factor_raw, std::int64_t{-5},
                             expected_white_peace) ||
      white_peace_attacker_prestige != expected_white_peace) {
    return false;
  }
  std::int64_t ten_factor = 0;
  if (!CheckedMultiplySigned(white_peace_factor_raw, std::int64_t{10},
                             ten_factor)) {
    return false;
  }
  const auto maximum_raw = 1'000LL * kFixedPointScale;
  const auto expected_attacker = std::max(-ten_factor, -maximum_raw);
  const auto expected_defender = std::min(ten_factor, maximum_raw);
  if (attacker_defeat.primary_resource_deltas[0].value.raw !=
          expected_attacker ||
      attacker_defeat.primary_resource_deltas[6].value.raw !=
          expected_defender) {
    return false;
  }
  white_peace.cb_prestige_factor = {white_peace_factor_raw,
                                    kFixedPointScale};
  attacker_defeat.cb_prestige_factor = {attacker_defeat_factor_raw,
                                        kFixedPointScale};
  return true;
}

} // namespace

bool ResolvePendingCharacterInteractionActiveWarV1(
    const Bindings &bindings, void *game_state, std::int32_t war_id,
    void *&output) noexcept {
  output = nullptr;
  if (!bindings.enabled || game_state == nullptr || war_id <= 0) {
    return false;
  }
  output = ResolveWar(bindings, game_state, war_id);
  return output != nullptr;
}

std::string_view LastWarTerminationExitTermsUnavailableReason() noexcept {
  return g_last_war_termination_exit_terms_unavailable_reason;
}

Bindings BindCurrentProcess(bool executable_matches) noexcept {
  Bindings result{};
  if (!executable_matches) {
    return result;
  }
  const auto module =
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  if (module == 0) {
    return result;
  }
  result.enabled = true;
  result.game_state_slot =
      reinterpret_cast<void **>(module + kGameStateSlotRva);
  result.jomini_state_slot =
      reinterpret_cast<void **>(module + kJominiStateSlotRva);
  result.command_manager =
      reinterpret_cast<void *>(module + kCommandManagerRva);
  result.pause_primary_vtable = module + kPausePrimaryVtableRva;
  result.pause_secondary_vtable = module + kPauseSecondaryVtableRva;
  result.set_speed_primary_vtable = module + kSetSpeedPrimaryVtableRva;
  result.set_speed_secondary_vtable = module + kSetSpeedSecondaryVtableRva;
  result.select_event_option_primary_vtable =
      module + kSelectEventOptionPrimaryVtableRva;
  result.select_event_option_secondary_vtable =
      module + kSelectEventOptionSecondaryVtableRva;
  result.ingame_interface_idler_vtable =
      module + kIngameInterfaceIdlerVtableRva;
  result.event_window_primary_vtable =
      module + kEventWindowPrimaryVtableRva;
  result.scheme_type_primary_vtable =
      module + kSchemeTypePrimaryVtableRva;
  result.auto_save_primary_vtable = module + kAutoSavePrimaryVtableRva;
  result.auto_save_secondary_vtable = module + kAutoSaveSecondaryVtableRva;
  result.reply_character_interaction_primary_vtable =
      module + kReplyCharacterInteractionPrimaryVtableRva;
  result.reply_character_interaction_secondary_vtable =
      module + kReplyCharacterInteractionSecondaryVtableRva;
  result.raise_troops_primary_vtable =
      module + kRaiseTroopsPrimaryVtableRva;
  result.raise_troops_secondary_vtable =
      module + kRaiseTroopsSecondaryVtableRva;
  result.move_army_primary_vtable = module + kMoveArmyPrimaryVtableRva;
  result.move_army_secondary_vtable = module + kMoveArmySecondaryVtableRva;
  result.disband_army_primary_vtable =
      module + kDisbandArmyPrimaryVtableRva;
  result.disband_army_secondary_vtable =
      module + kDisbandArmySecondaryVtableRva;
  result.split_army_half_primary_vtable =
      module + kSplitArmyHalfPrimaryVtableRva;
  result.split_army_half_secondary_vtable =
      module + kSplitArmyHalfSecondaryVtableRva;
  result.merge_armies_primary_vtable =
      module + kMergeArmiesPrimaryVtableRva;
  result.merge_armies_secondary_vtable =
      module + kMergeArmiesSecondaryVtableRva;
  result.start_assault_primary_vtable =
      module + kStartAssaultPrimaryVtableRva;
  result.start_assault_secondary_vtable =
      module + kStartAssaultSecondaryVtableRva;
  result.stop_assault_primary_vtable =
      module + kStopAssaultPrimaryVtableRva;
  result.stop_assault_secondary_vtable =
      module + kStopAssaultSecondaryVtableRva;
  result.send_character_interaction_primary_vtable =
      module + kSendCharacterInteractionPrimaryVtableRva;
  result.send_character_interaction_secondary_vtable =
      module + kSendCharacterInteractionSecondaryVtableRva;
  result.war_declaration_vtable = module + kWarDeclarationVtableRva;
  result.character_claim_vtable = module + kCharacterClaimVtableRva;
  result.effect_preview_collector_vtable =
      module + kEffectPreviewCollectorVtableRva;
  result.jomini_effect_vtable = module + kJominiEffectVtableRva;
  result.jomini_scripted_effect_vtable =
      module + kJominiScriptedEffectVtableRva;
  result.jomini_scripted_effect_template_vtable =
      module + kJominiScriptedEffectTemplateVtableRva;
  result.hidden_effect_vtable = module + kHiddenEffectVtableRva;
  result.jomini_context_effect_vtable =
      module + kJominiContextEffectVtableRva;
  result.prestige_effect_vtable = module + kPrestigeEffectVtableRva;
  result.prestige_experience_effect_vtable =
      module + kPrestigeExperienceEffectVtableRva;
  result.piety_effect_vtable = module + kPietyEffectVtableRva;
  result.piety_experience_effect_vtable =
      module + kPietyExperienceEffectVtableRva;
  result.legitimacy_effect_vtable = module + kLegitimacyEffectVtableRva;
  result.stress_impact_effect_vtable =
      module + kStressImpactEffectVtableRva;
  result.add_from_contribution_attackers_effect_vtable =
      module + kAddFromContributionAttackersEffectVtableRva;
  result.add_from_contribution_defenders_effect_vtable =
      module + kAddFromContributionDefendersEffectVtableRva;
  result.gold_transfer_effect_vtable =
      module + kGoldTransferEffectVtableRva;
  result.truce_effect_vtable = module + kTruceEffectVtableRva;
  result.ai_unit_stack_vtable = module + kAiUnitStackVtableRva;
  result.ai_subunit_stack_vtable = module + kAiSubunitStackVtableRva;
  result.ai_war_coordinator_vtable =
      module + kAiWarCoordinatorVtableRva;
  result.cb_prestige_factor_identifier_id =
      reinterpret_cast<const std::int32_t *>(
          module + kCbPrestigeFactorIdentifierIdRva);
  result.pending_character_interaction_storage_slot =
      reinterpret_cast<void **>(
          module + kPendingCharacterInteractionStorageSlotRva);
  result.character_storage_slot =
      reinterpret_cast<void **>(module + kCharacterStorageSlotRva);
  result.army_storage_slot =
      reinterpret_cast<void **>(module + kArmyStorageSlotRva);
  result.army_internal_storage_slot =
      reinterpret_cast<void **>(module + kArmyInternalStorageSlotRva);
  result.regiment_storage_slot =
      reinterpret_cast<void **>(module + kRegimentStorageSlotRva);
  result.combat_storage_slot =
      reinterpret_cast<void **>(module + kCombatStorageSlotRva);
  result.battle_result_fallback_slot =
      reinterpret_cast<void **>(module + kBattleResultFallbackSlotRva);
  result.battle_result_storage_slot =
      reinterpret_cast<void **>(module + kBattleResultStorageSlotRva);
  result.ai_war_coordinator_fallback_slot = reinterpret_cast<void **>(
      module + kAiWarCoordinatorFallbackSlotRva);
  result.ai_war_coordinator_storage_slot = reinterpret_cast<void **>(
      module + kAiWarCoordinatorStorageSlotRva);
  result.siege_storage_slot =
      reinterpret_cast<void **>(module + kSiegeStorageSlotRva);
  result.contact_game_mode_slot =
      reinterpret_cast<void **>(module + kContactGameModeSlotRva);
  result.trait_database_slot =
      reinterpret_cast<void **>(module + kTraitDatabaseSlotRva);
  result.scheme_type_database_slot =
      reinterpret_cast<void **>(module + kSchemeTypeDatabaseSlotRva);
  result.scheme_type_fallback_slot =
      reinterpret_cast<void **>(module + kSchemeTypeFallbackSlotRva);
  result.expected_generic_value_type_registry =
      reinterpret_cast<void *>(module + kGenericValueTypeRegistryRva);
  result.generic_value_type_name_fallback =
      reinterpret_cast<const std::string *>(
          module + kGenericValueTypeNameFallbackRva);
  result.script_identifier_name_fallback =
      reinterpret_cast<const std::string *>(
          module + kScriptIdentifierNameFallbackRva);
  result.global_variable_container_accessor_slot =
      reinterpret_cast<GetGlobalVariableContainer *>(
          module + kGlobalVariableContainerAccessorSlotRva);
  result.valid_casus_belli_configuration_scratch =
      reinterpret_cast<void *>(
          module + kValidCasusBelliConfigurationScratchRva);
  result.event_manager_offset = kEventManagerOffset;
  result.player_character_manager_offset =
      kPlayerCharacterManagerOffset;
  result.war_manager_offset = kWarManagerOffset;
  result.landed_title_manager_offset = kLandedTitleManagerOffset;
  result.arrange_marriage_interaction_offset =
      kArrangeMarriageInteractionOffset;
  result.declare_war_interaction_offset = kDeclareWarInteractionOffset;
  result.submit_command =
      reinterpret_cast<SubmitCommand>(module + kSubmitCommandRva);
  result.get_local_player =
      reinterpret_cast<GetLocalPlayer>(module + kGetLocalPlayerRva);
  result.get_current_event =
      reinterpret_cast<GetCurrentEvent>(module + kGetCurrentEventRva);
  result.is_pending_character_interaction_for_character =
      reinterpret_cast<IsPendingCharacterInteractionForCharacter>(
          module + kIsPendingInteractionForCharacterRva);
  result.validate_reply_character_interaction_command =
      reinterpret_cast<ValidateReplyCharacterInteractionCommand>(
          module + kValidateReplyCharacterInteractionCommandRva);
  result.contains_war_participant = reinterpret_cast<ContainsWarParticipant>(
      module + kContainsWarParticipantRva);
  result.get_war_score =
      reinterpret_cast<GetWarScore>(module + kGetWarScoreRva);
  result.get_imprisonment_war_score =
      reinterpret_cast<GetWarScoreComponent>(
          module + kGetImprisonmentWarScoreRva);
  result.get_battle_war_score_base =
      reinterpret_cast<GetWarScoreComponent>(
          module + kGetBattleWarScoreBaseRva);
  result.get_battle_war_score_side =
      reinterpret_cast<GetWarScoreSideComponent>(
          module + kGetBattleWarScoreSideRva);
  result.get_occupation_war_score_side =
      reinterpret_cast<GetWarScoreOccupationComponent>(
          module + kGetOccupationWarScoreSideRva);
  result.get_ticking_war_score_side =
      reinterpret_cast<GetWarScoreTickingComponent>(
          module + kGetTickingWarScoreSideRva);
  result.is_native_component_alive =
      reinterpret_cast<IsNativeComponentAlive>(
          module + kIsNativeComponentAliveRva);
  result.get_siege_progress = reinterpret_cast<ReadSiegeFixedPoint>(
      module + kGetSiegeProgressRva);
  result.get_siege_total_work = reinterpret_cast<ReadSiegeFixedPoint>(
      module + kGetSiegeTotalWorkRva);
  result.get_siege_days_left = reinterpret_cast<GetSiegeDaysLeft>(
      module + kGetSiegeDaysLeftRva);
  result.read_assault_daily_progress =
      reinterpret_cast<ReadAssaultDailyProgress>(
          module + kReadAssaultDailyProgressRva);
  result.get_assault_daily_casualties =
      reinterpret_cast<GetAssaultDailyCasualties>(
          module + kGetAssaultDailyCasualtiesRva);
  result.validate_start_assault_command =
      reinterpret_cast<ValidateAssaultCommand>(
          module + kValidateStartAssaultCommandRva);
  result.validate_stop_assault_command =
      reinterpret_cast<ValidateAssaultCommand>(
          module + kValidateStopAssaultCommandRva);
  result.destroy_assault_command =
      reinterpret_cast<DestroyNativeCommand>(
          module + kDestroyAssaultCommandRva);
  result.is_province_occupied = reinterpret_cast<IsProvinceOccupied>(
      module + kIsProvinceOccupiedRva);
  result.get_province_fort_level = reinterpret_cast<GetProvinceInt32>(
      module + kGetProvinceFortLevelRva);
  result.get_province_garrison_size = reinterpret_cast<GetProvinceInt32>(
      module + kGetProvinceGarrisonSizeRva);
  result.get_province_besieging_strength =
      reinterpret_cast<GetProvinceInt32>(
          module + kGetProvinceBesiegingStrengthRva);
  result.resolve_default_raise_province =
      reinterpret_cast<ResolveDefaultRaiseProvince>(
          module + kResolveDefaultRaiseProvinceRva);
  result.get_unit_state =
      reinterpret_cast<GetUnitState>(module + kGetUnitStateRva);
  result.get_army_current_soldiers =
      reinterpret_cast<GetArmyCurrentSoldiers>(
          module + kGetArmyCurrentSoldiersRva);
  result.get_army_maximum_soldiers =
      reinterpret_cast<GetArmyMaximumSoldiers>(
          module + kGetArmyMaximumSoldiersRva);
  result.get_army_commander =
      reinterpret_cast<GetArmyCommander>(module + kGetArmyCommanderRva);
  result.get_commander_advantage = reinterpret_cast<GetCommanderAdvantage>(
      module + kGetCommanderAdvantageRva);
  result.get_province_terrain = reinterpret_cast<GetProvinceTerrain>(
      module + kGetProvinceTerrainRva);
  result.evaluate_regiment_stats_at_province =
      reinterpret_cast<EvaluateRegimentStatsAtProvince>(
          module + kEvaluateRegimentStatsAtProvinceRva);
  result.is_special_combat_regiment =
      reinterpret_cast<IsSpecialCombatRegiment>(
          module + kIsSpecialCombatRegimentRva);
  result.get_character_modifier_aggregator =
      reinterpret_cast<GetCharacterModifierAggregator>(
          module + kGetCharacterModifierAggregatorRva);
  result.read_character_modifier =
      reinterpret_cast<ReadCharacterModifier>(
          module + kReadCharacterModifierRva);
  result.get_combat_rules =
      reinterpret_cast<GetCombatRules>(module + kGetCombatRulesRva);
  result.get_combat_side_strength =
      reinterpret_cast<GetCombatSideStrength>(
          module + kGetCombatSideStrengthRva);
  result.get_combat_regiment_strength =
      reinterpret_cast<GetCombatRegimentStrength>(
          module + kGetCombatRegimentStrengthRva);
  result.read_counter_current_chunk =
      reinterpret_cast<ReadCounterCurrentChunk>(
          module + kReadCounterCurrentChunkRva);
  result.resolve_counter_classes =
      reinterpret_cast<ResolveCounterClasses>(
          module + kResolveCounterClassesRva);
  result.get_counter_context_scale =
      reinterpret_cast<GetCounterContextScale>(
          module + kGetCounterContextScaleRva);
  result.get_knight_effectiveness_context =
      reinterpret_cast<GetKnightEffectivenessContext>(
          module + kGetKnightEffectivenessContextRva);
  result.read_knight_effectiveness =
      reinterpret_cast<ReadKnightEffectiveness>(
          module + kReadKnightEffectivenessRva);
  result.is_holding_defender = reinterpret_cast<IsHoldingDefender>(
      module + kIsHoldingDefenderRva);
  result.commander_min_roll = reinterpret_cast<const std::int32_t *>(
      module + kCommanderMinRollRva);
  result.commander_max_roll = reinterpret_cast<const std::int32_t *>(
      module + kCommanderMaxRollRva);
  result.knight_damage_per_prowess =
      reinterpret_cast<const std::int32_t *>(
          module + kKnightDamagePerProwessRva);
  result.knight_toughness_per_prowess =
      reinterpret_cast<const std::int32_t *>(
          module + kKnightToughnessPerProwessRva);
  result.minimum_combat_width = reinterpret_cast<const std::int32_t *>(
      module + kMinimumCombatWidthRva);
  result.base_combat_width_ratio = reinterpret_cast<const std::int64_t *>(
      module + kBaseCombatWidthRatioRva);
  result.construct_raise_troops_command =
      reinterpret_cast<ConstructRaiseTroopsCommand>(
          module + kConstructRaiseTroopsCommandRva);
  result.validate_raise_troops_command =
      reinterpret_cast<ValidateRaiseTroopsCommand>(
          module + kValidateRaiseTroopsCommandRva);
  result.destroy_raise_troops_command =
      reinterpret_cast<DestroyNativeCommand>(
          module + kDestroyRaiseTroopsCommandRva);
  result.get_army_move_mode =
      reinterpret_cast<GetArmyMoveMode>(module + kGetArmyMoveModeRva);
  result.can_character_use_command_kind =
      reinterpret_cast<CanCharacterUseCommandKind>(
          module + kCanCharacterUseCommandKindRva);
  result.can_army_use_move_mode = reinterpret_cast<CanArmyUseMoveMode>(
      module + kCanArmyUseMoveModeRva);
  result.can_move_army =
      reinterpret_cast<CanMoveArmy>(module + kCanMoveArmyRva);
  result.can_order_combat_retreat =
      reinterpret_cast<CanOrderCombatRetreat>(
          module + kCanOrderCombatRetreatRva);
  result.get_combat_retreat_rule_state =
      reinterpret_cast<GetCombatRetreatRuleState>(
          module + kGetCombatRetreatRuleStateRva);
  result.minimum_days_before_manual_retreat =
      reinterpret_cast<const std::int32_t *>(
          module + kMinimumDaysBeforeManualRetreatRva);
  result.resolve_move_origin = reinterpret_cast<ResolveMoveOrigin>(
      module + kResolveMoveOriginRva);
  result.construct_move_path_context =
      reinterpret_cast<ConstructMovePathContext>(
          module + kConstructMovePathContextRva);
  result.construct_army_move_path =
      reinterpret_cast<ConstructArmyMovePath>(
          module + kConstructArmyMovePathRva);
  result.build_army_move_route = reinterpret_cast<BuildArmyMoveRoute>(
      module + kBuildArmyMoveRouteRva);
  result.destroy_move_army_command =
      reinterpret_cast<DestroyNativeCommand>(
          module + kDestroyMoveArmyCommandRva);
  result.validate_disband_army_command =
      reinterpret_cast<ValidateDisbandArmyCommand>(
          module + kValidateDisbandArmyCommandRva);
  result.validate_split_army_half_command =
      reinterpret_cast<ValidateSplitArmyHalfCommand>(
          module + kValidateSplitArmyHalfCommandRva);
  result.destroy_split_army_half_command =
      reinterpret_cast<DestroyNativeCommand>(
          module + kDestroySplitArmyHalfCommandRva);
  result.create_merge_armies_command =
      reinterpret_cast<CreateMergeArmiesCommand>(
          module + kCreateMergeArmiesCommandRva);
  result.validate_merge_armies_command =
      reinterpret_cast<ValidateMergeArmiesCommand>(
          module + kValidateMergeArmiesCommandRva);
  result.destroy_merge_armies_command =
      reinterpret_cast<DestroyNativeCommand>(
          module + kDestroyMergeArmiesCommandRva);
  result.get_casus_belli_type_database =
      reinterpret_cast<GetCasusBelliTypeDatabase>(
          module + kGetCasusBelliTypeDatabaseRva);
  result.get_character_interaction_database =
      reinterpret_cast<GetCharacterInteractionDatabase>(
          module + kGetCharacterInteractionDatabaseRva);
  result.hash_stable_key =
      reinterpret_cast<HashStableKey>(module + kHashStableKeyRva);
  result.lookup_scheme_type =
      reinterpret_cast<LookupSchemeType>(module + kLookupSchemeTypeRva);
  result.evaluate_casus_belli = reinterpret_cast<EvaluateCasusBelli>(
      module + kEvaluateCasusBelliRva);
  result.destroy_valid_casus_belli_configuration =
      reinterpret_cast<DestroyValidCasusBelliConfiguration>(
          module + kDestroyValidCasusBelliConfigurationRva);
  result.construct_character_interaction_context =
      reinterpret_cast<ConstructCharacterInteractionContext>(
          module + kConstructCharacterInteractionContextRva);
  result.redirect_character_interaction_roles =
      reinterpret_cast<RedirectCharacterInteractionRoles>(
          module + kRedirectCharacterInteractionRolesRva);
  result.construct_character_interaction_context_all_roles =
      reinterpret_cast<ConstructCharacterInteractionContextAllRoles>(
          module + kConstructCharacterInteractionContextAllRolesRva);
  result.copy_native_int_array = reinterpret_cast<CopyNativeIntArray>(
      module + kCopyNativeIntArrayRva);
  result.append_native_int_array_range =
      reinterpret_cast<AppendNativeIntArrayRange>(
          module + kAppendNativeIntArrayRangeRva);
  result.refresh_character_interaction_context =
      reinterpret_cast<RefreshCharacterInteractionContext>(
          module + kRefreshCharacterInteractionContextRva);
  result.finalize_character_interaction_context =
      reinterpret_cast<FinalizeCharacterInteractionContext>(
          module + kFinalizeCharacterInteractionContextRva);
  result.validate_character_interaction_context =
      reinterpret_cast<ValidateCharacterInteractionContext>(
          module + kValidateCharacterInteractionContextRva);
  result.read_character_interaction_answer_score =
      reinterpret_cast<ReadCharacterInteractionAnswerScore>(
          module + kReadCharacterInteractionAnswerScoreRva);
  result.evaluate_character_interaction_trigger =
      reinterpret_cast<EvaluateCharacterInteractionTrigger>(
          module + kEvaluateCharacterInteractionTriggerRva);
  result.construct_send_character_interaction_command =
      reinterpret_cast<ConstructSendCharacterInteractionCommand>(
          module + kConstructSendCharacterInteractionCommandRva);
  result.destroy_character_interaction_context =
      reinterpret_cast<DestroyCharacterInteractionContext>(
          module + kDestroyCharacterInteractionContextRva);
  result.default_construct_character_interaction_context =
      reinterpret_cast<DefaultConstructCharacterInteractionContext>(
          module + kDefaultConstructCharacterInteractionContextRva);
  result.construct_war_resolution_interaction_context =
      reinterpret_cast<ConstructWarResolutionInteractionContext>(
          module + kConstructWarResolutionInteractionContextRva);
  result.construct_special_character_interaction_context =
      reinterpret_cast<ConstructSpecialCharacterInteractionContext>(
          module + kConstructSpecialCharacterInteractionContextRva);
  result.read_character_claim = reinterpret_cast<ReadCharacterClaim>(
      module + kReadCharacterClaimRva);
  result.construct_war_effect_context =
      reinterpret_cast<ConstructWarEffectContext>(
          module + kConstructWarEffectContextRva);
  result.populate_war_effect_context =
      reinterpret_cast<PopulateWarEffectContext>(
          module + kPopulateWarEffectContextRva);
  result.construct_effect_preview_collector =
      reinterpret_cast<ConstructEffectPreviewCollector>(
          module + kConstructEffectPreviewCollectorRva);
  result.destroy_effect_preview_collector =
      reinterpret_cast<DestroyEffectPreviewCollector>(
          module + kDestroyEffectPreviewCollectorRva);
  result.traverse_loaded_effect = reinterpret_cast<TraverseLoadedEffect>(
      module + kTraverseLoadedEffectRva);
  result.destroy_effect_context_118 =
      reinterpret_cast<DestroyEffectContextSubobject>(
          module + kDestroyEffectContext118Rva);
  result.destroy_effect_context_array_row =
      reinterpret_cast<DestroyEffectContextSubobject>(
          module + kDestroyEffectContextArrayRowRva);
  result.evaluate_truce_duration_days =
      reinterpret_cast<EvaluateTruceDurationDays>(
          module + kEvaluateTruceDurationDaysRva);
  result.get_character_primary_title =
      reinterpret_cast<GetCharacterPrimaryTitle>(
          module + kGetCharacterPrimaryTitleRva);
  result.read_monthly_gold_income =
      reinterpret_cast<ReadMonthlyGoldIncome>(
          module + kReadMonthlyGoldIncomeRva);
  result.evaluate_character_interaction_answer =
      reinterpret_cast<EvaluateCharacterInteractionAnswer>(
          module + kEvaluateCharacterInteractionAnswerRva);
  result.get_script_identifier_table =
      reinterpret_cast<GetScriptIdentifierTable>(
          module + kGetScriptIdentifierTableRva);
  result.lookup_script_identifier_id =
      reinterpret_cast<LookupScriptIdentifierId>(
          module + kLookupScriptIdentifierIdRva);
  result.get_generic_value_type_registry =
      reinterpret_cast<GetGenericValueTypeRegistry>(
          module + kGetGenericValueTypeRegistryRva);
  result.resolve_generic_value_type_name =
      reinterpret_cast<ResolveGenericValueTypeName>(
          module + kResolveGenericValueTypeNameRva);
  result.resolve_script_identifier_name =
      reinterpret_cast<ResolveScriptIdentifierName>(
          module + kResolveScriptIdentifierNameRva);
  result.is_event_target_valid = reinterpret_cast<IsEventTargetValid>(
      module + kIsEventTargetValidRva);
  result.resolve_event_target_object =
      reinterpret_cast<ResolveEventTargetObject>(
          module + kResolveEventTargetObjectRva);
  result.is_character_hostile = reinterpret_cast<IsCharacterHostile>(
      module + kIsCharacterHostileRva);
  result.is_army_empty_for_contact =
      reinterpret_cast<ArmyContactPredicate>(
          module + kIsArmyEmptyForContactRva);
  result.is_army_in_combat = reinterpret_cast<ArmyContactPredicate>(
      module + kIsArmyInCombatRva);
  result.read_province_holder_character_id =
      reinterpret_cast<ReadProvinceHolderCharacterId>(
          module + kReadProvinceHolderCharacterIdRva);
  result.classify_contact_defender_by_holder =
      reinterpret_cast<CharacterRelationPredicate>(
          module + kClassifyContactDefenderByHolderRva);
  result.classify_contact_defender_fallback =
      reinterpret_cast<CharacterProvincePredicate>(
          module + kClassifyContactDefenderFallbackRva);
  result.read_unit_land_route_speed =
      reinterpret_cast<ReadUnitRouteSpeed>(
          module + kReadUnitLandRouteSpeedRva);
  result.read_unit_naval_route_speed =
      reinterpret_cast<ReadUnitRouteSpeed>(
          module + kReadUnitNavalRouteSpeedRva);
  result.read_unit_current_edge_speed =
      reinterpret_cast<ReadUnitRouteSpeed>(
          module + kReadUnitCurrentEdgeSpeedRva);
  result.read_route_travel_duration =
      reinterpret_cast<ReadRouteTravelDuration>(
          module + kReadRouteTravelDurationRva);
  result.read_route_edge_duration =
      reinterpret_cast<ReadRouteEdgeDuration>(
          module + kReadRouteEdgeDurationRva);
  return result;
}

bool ReadSnapshot(const Bindings &bindings, Snapshot &output) noexcept {
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.jomini_state_slot == nullptr) {
    return false;
  }
  void *const game_state = *bindings.game_state_slot;
  void *const jomini_state = *bindings.jomini_state_slot;
  if (game_state == nullptr || jomini_state == nullptr) {
    return false;
  }
  void *const players = LoadAt<void *>(jomini_state, kJominiPlayersOffset);
  if (players == nullptr) {
    return false;
  }

  output.date_raw = LoadAt<std::int32_t>(game_state, kGameStateDateOffset);
  const std::int32_t native_speed =
      LoadAt<std::int32_t>(game_state, kGameStateSpeedOffset);
  if (native_speed < 0 || native_speed > 4) {
    return false;
  }
  output.speed = native_speed + 1;
  output.paused = LoadAt<std::uint8_t>(jomini_state, kJominiPausedOffset) != 0;
  output.player_id = LoadAt<std::int32_t>(players, kPlayersLocalIdOffset);
  void *const local_player = bindings.get_local_player != nullptr
                                 ? bindings.get_local_player(jomini_state)
                                 : nullptr;
  output.map_ready =
      local_player != nullptr &&
      LoadAt<std::int32_t>(local_player, kPlayerIdOffset) >= 0;
  if (!output.map_ready) {
    // During CK3's application-main startup the category registries used by
    // events, wars, and scripted globals are not yet populated.  Publish the
    // stable process/game-state prefix only; in particular, do not traverse
    // any of those registries until the local-player sentinel proves the map
    // has finished loading.
    const std::int32_t date_raw = output.date_raw;
    const std::int32_t speed = output.speed;
    const bool paused = output.paused;
    const std::int32_t player_id = output.player_id;
    output = {};
    output.date_raw = date_raw;
    output.speed = speed;
    output.paused = paused;
    output.player_id = player_id;
    output.map_ready = false;
    return true;
  }
  output.has_played_character =
      ReadPlayedCharacter(bindings, game_state, output.player_id,
                          output.played_character_id,
                          output.played_character_alive);
  if (!output.has_played_character) {
    output.played_character_id = -1;
    output.played_character_alive = false;
    output.played_character_betrothed_id = -1;
    output.played_character_primary_spouse_id = -1;
    output.played_character_spouse_ids.clear();
  }
  output.has_active_event = ReadCurrentEvent(
      bindings, game_state, output.active_event_instance_id,
      output.active_event_option_count);
  if (!output.has_active_event) {
    output.active_event_instance_id = -1;
    output.active_event_option_count = 0;
  }
  void *const played_character = output.has_played_character
                                     ? ResolveCharacter(
                                           bindings,
                                           output.played_character_id)
                                     : nullptr;
  if (output.has_played_character &&
      !ReadPlayedCharacterRelationships(
          bindings, played_character,
          output.played_character_betrothed_id,
          output.played_character_primary_spouse_id,
          output.played_character_spouse_ids)) {
    return false;
  }
  output.has_pending_character_interaction = ReadPendingCharacterInteraction(
      bindings, played_character, output.played_character_id,
      output.pending_character_interaction_id,
      output.pending_sender_character_id,
      output.pending_auto_accept_notification);
  if (!output.has_pending_character_interaction) {
    output.pending_character_interaction_id = -1;
    output.pending_sender_character_id = -1;
    output.pending_auto_accept_notification = false;
  }
  if (output.has_played_character) {
    ReadWarsAndArmies(bindings, game_state, output.played_character_id,
                      output.paused, output);
  } else {
    output.active_wars.clear();
    output.player_armies.clear();
  }
  ReadOneLifeSettlement(bindings, output);
  return true;
}

ReadArmyStrengthsResult ReadArmyStrengths(
    const Bindings &bindings,
    std::vector<ArmyStrengthSnapshot> &output) noexcept {
  output.clear();
  if (!bindings.enabled || bindings.army_storage_slot == nullptr ||
      bindings.army_internal_storage_slot == nullptr ||
      bindings.regiment_storage_slot == nullptr ||
      bindings.get_army_current_soldiers == nullptr ||
      bindings.get_army_maximum_soldiers == nullptr) {
    return ReadArmyStrengthsResult::unavailable;
  }

  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return ReadArmyStrengthsResult::unavailable;
  }
  if (!current.paused) {
    return ReadArmyStrengthsResult::requires_paused;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return ReadArmyStrengthsResult::no_played_character;
  }

  const auto scope = BuildArmyStrengthScope(current);
  output.reserve(scope.size());
  bool partial = false;
  for (const auto &entry : scope) {
    output.push_back(ReadArmyStrengthRow(bindings, entry));
    partial = partial || !output.back().available;
  }
  return partial ? ReadArmyStrengthsResult::partial
                 : ReadArmyStrengthsResult::available;
}

ReadCombatSimulationInputsResult ReadCombatSimulationInputs(
    const Bindings &bindings, const CombatSimulationInputsRequest &request,
    CombatSimulationInputsSnapshot &output) noexcept {
  output = {};
  const auto total_army_count = request.attacker_army_ids.size() +
                                request.defender_army_ids.size();
  if (request.target_province_id <= 0 ||
      request.attacker_entry_province_id <= 0 ||
      request.target_province_id == request.attacker_entry_province_id ||
      request.attacker_army_ids.empty() ||
      request.defender_army_ids.empty() ||
      request.attacker_army_ids.size() > 63 ||
      request.defender_army_ids.size() > 63 || total_army_count > 64) {
    return ReadCombatSimulationInputsResult::invalid_arguments;
  }
  std::vector<std::int32_t> army_ids;
  army_ids.reserve(total_army_count);
  army_ids.insert(army_ids.end(), request.attacker_army_ids.begin(),
                  request.attacker_army_ids.end());
  army_ids.insert(army_ids.end(), request.defender_army_ids.begin(),
                  request.defender_army_ids.end());
  for (std::size_t index = 0; index < army_ids.size(); ++index) {
    if (army_ids[index] <= 0 ||
        std::find(army_ids.begin(), army_ids.begin() + index,
                  army_ids[index]) != army_ids.begin() + index) {
      return ReadCombatSimulationInputsResult::invalid_arguments;
    }
  }
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.army_storage_slot == nullptr ||
      bindings.army_internal_storage_slot == nullptr ||
      bindings.regiment_storage_slot == nullptr ||
      bindings.character_storage_slot == nullptr ||
      bindings.combat_storage_slot == nullptr ||
      bindings.get_army_commander == nullptr ||
      bindings.get_commander_advantage == nullptr ||
      bindings.get_province_terrain == nullptr ||
      bindings.evaluate_regiment_stats_at_province == nullptr ||
      bindings.is_special_combat_regiment == nullptr ||
      bindings.get_character_modifier_aggregator == nullptr ||
      bindings.read_character_modifier == nullptr ||
      bindings.get_combat_rules == nullptr ||
      bindings.read_counter_current_chunk == nullptr ||
      bindings.resolve_counter_classes == nullptr ||
      bindings.get_counter_context_scale == nullptr ||
      bindings.get_knight_effectiveness_context == nullptr ||
      bindings.read_knight_effectiveness == nullptr ||
      bindings.is_holding_defender == nullptr ||
      bindings.commander_min_roll == nullptr ||
      bindings.commander_max_roll == nullptr ||
      bindings.knight_damage_per_prowess == nullptr ||
      bindings.knight_toughness_per_prowess == nullptr ||
      bindings.minimum_combat_width == nullptr ||
      bindings.base_combat_width_ratio == nullptr) {
    return ReadCombatSimulationInputsResult::unavailable;
  }

  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return ReadCombatSimulationInputsResult::unavailable;
  }
  if (!current.paused) {
    return ReadCombatSimulationInputsResult::requires_paused;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return ReadCombatSimulationInputsResult::no_played_character;
  }
  void *const game_state = *bindings.game_state_slot;
  if (game_state == nullptr) {
    return ReadCombatSimulationInputsResult::unavailable;
  }
  void *const target_province =
      ResolveProvince(game_state, request.target_province_id);
  if (target_province == nullptr) {
    return ReadCombatSimulationInputsResult::target_province_not_found;
  }
  if (ResolveProvince(game_state, request.attacker_entry_province_id) ==
      nullptr) {
    return ReadCombatSimulationInputsResult::invalid_encounter;
  }
  std::int32_t counter_class_count = 0;
  if (!ReadCounterClassCount(bindings, counter_class_count)) {
    return ReadCombatSimulationInputsResult::unavailable;
  }

  output.target_province_id = request.target_province_id;
  output.scenario.attacker_entry_province_id =
      request.attacker_entry_province_id;
  output.scenario.attacker_army_ids = request.attacker_army_ids;
  output.scenario.defender_army_ids = request.defender_army_ids;
  output.input_observation_ready = false;
  output.monte_carlo_ready = false;
  output.missing_required_domains.clear();

  const auto scope = BuildArmyStrengthScope(current);
  std::vector<const ArmyStrengthScopeEntry *> selected_scope;
  selected_scope.reserve(army_ids.size());
  for (const auto army_id : army_ids) {
    const auto entry = std::find_if(
        scope.begin(), scope.end(), [army_id](const auto &candidate) {
          return candidate.army_id == army_id;
        });
    if (entry == scope.end()) {
      output = {};
      return ReadCombatSimulationInputsResult::army_not_in_scope;
    }
    selected_scope.push_back(&*entry);
  }

  std::vector<std::int32_t> common_wars;
  if (!selected_scope.empty()) {
    common_wars = selected_scope.front()->war_ids;
  }
  for (const auto *entry : selected_scope) {
    std::erase_if(common_wars, [entry](std::int32_t war_id) {
      return std::find(entry->war_ids.begin(), entry->war_ids.end(), war_id) ==
             entry->war_ids.end();
    });
  }
  const auto is_enemy_scope = [](const ArmyStrengthScopeEntry *entry) {
    return entry->role == ArmyStrengthScopeRole::active_war_enemy;
  };
  const bool attacker_enemy_side = is_enemy_scope(selected_scope.front());
  const auto attacker_count = request.attacker_army_ids.size();
  for (std::size_t index = 0; index < selected_scope.size(); ++index) {
    const bool expected_enemy =
        index < attacker_count ? attacker_enemy_side : !attacker_enemy_side;
    if (is_enemy_scope(selected_scope[index]) != expected_enemy) {
      output = {};
      return ReadCombatSimulationInputsResult::invalid_encounter;
    }
  }
  if (common_wars.empty()) {
    output = {};
    return ReadCombatSimulationInputsResult::invalid_encounter;
  }
  output.scenario.attacker_side =
      attacker_enemy_side ? "enemy" : "player_or_allied";
  output.scenario.defender_side =
      attacker_enemy_side ? "player_or_allied" : "enemy";

  output.target_province = ReadCombatCandidateProvince(
      bindings, game_state, request.target_province_id);
  void *const target_terrain = bindings.get_province_terrain(target_province);
  output.armies.reserve(selected_scope.size());
  bool has_unavailable_subdomain = false;
  bool partial = !output.target_province.available;
  for (std::size_t index = 0; index < selected_scope.size(); ++index) {
    const auto *entry = selected_scope[index];
    output.armies.push_back(ReadCombatArmyInputsRow(
        bindings, game_state, target_province, target_terrain,
        request.target_province_id, counter_class_count, *entry,
        output.ongoing_combats,
        has_unavailable_subdomain));
    output.armies.back().encounter_role =
        index < attacker_count ? "attacker" : "defender";
    partial = partial || !output.armies.back().available;
  }
  std::vector<std::int32_t> seen_knight_character_ids;
  std::vector<std::int32_t> seen_knight_regiment_ids;
  for (auto &army : output.armies) {
    if (!army.native_carmy_id_observable || !army.regiments_observable) {
      army.knights = {};
      army.knights.unavailable_reason =
          "knight_source_composition_unavailable";
      has_unavailable_subdomain = true;
      continue;
    }
    void *const internal_army = ResolveStoredComponent(
        bindings.army_internal_storage_slot, army.native_carmy_id,
        kInternalArmyIdOffset);
    if (internal_army == nullptr ||
        !ReadCombatKnights(bindings, army.native_carmy_id,
                           army.regiments, seen_knight_character_ids,
                           seen_knight_regiment_ids, army.knights)) {
      output = {};
      return ReadCombatSimulationInputsResult::unavailable;
    }
  }
  const auto geography_result = ReadContactGeography(
      bindings, game_state, target_province, request.target_province_id,
      request.attacker_entry_province_id, attacker_enemy_side,
      output.armies, output.target_province.crossing,
      output.target_province.defender_context);
  if (geography_result != ReadContactGeographyResult::available) {
    if (geography_result == ReadContactGeographyResult::invalid_encounter) {
      output = {};
      return ReadCombatSimulationInputsResult::invalid_encounter;
    }
    has_unavailable_subdomain = true;
  }
  output.target_province.precontact_width = ReadPrecontactCombatWidth(
      bindings, output.armies, output.target_province.terrain);
  if (!output.target_province.precontact_width.available) {
    has_unavailable_subdomain = true;
  }
  output.counter_resolutions.push_back(ReadCounterResolution(
      bindings, output.armies, counter_class_count, false));
  output.counter_resolutions.push_back(ReadCounterResolution(
      bindings, output.armies, counter_class_count, true));
  for (const auto &resolution : output.counter_resolutions) {
    has_unavailable_subdomain =
        has_unavailable_subdomain || !resolution.available;
  }
  const auto append_missing_domain = [&output](std::string_view domain) {
    if (std::find(output.missing_required_domains.begin(),
                  output.missing_required_domains.end(), domain) ==
        output.missing_required_domains.end()) {
      output.missing_required_domains.emplace_back(domain);
    }
  };
  if (!output.target_province.available ||
      !output.target_province.terrain.available) {
    append_missing_domain("target_terrain");
  }
  if (!output.target_province.crossing.available) {
    append_missing_domain("crossing");
  }
  if (!output.target_province.defender_context.available ||
      output.target_province.defender_context.holding_defender_status !=
          CombatObservationStatus::available) {
    append_missing_domain("attacker_defender_holding");
  }
  if (!output.target_province.precontact_width.available) {
    append_missing_domain("contact_combat_width");
  }
  for (const auto &army : output.armies) {
    if (!army.available || !army.native_carmy_id_observable ||
        army.owner.status != CombatObservationStatus::available) {
      append_missing_domain("army_identity_and_owner");
    }
    if (army.commander.status == CombatObservationStatus::unavailable ||
        !army.commander.battle_context.available) {
      append_missing_domain("commander_and_roll_bounds");
    }
    if (!army.regiments_observable) {
      append_missing_domain("regiment_composition");
    }
    for (const auto &regiment : army.regiments) {
      if (!regiment.identity_valid) {
        append_missing_domain("regiment_identity");
      }
      if (regiment.maa_type.status == CombatObservationStatus::unavailable) {
        append_missing_domain("regiment_maa_type");
      }
      if (regiment.kind.status != CombatObservationStatus::available) {
        append_missing_domain("regiment_kind_and_main_phase_eligibility");
      }
      if (!regiment.effective_stats.available) {
        append_missing_domain("effective_regiment_stats");
      }
      if (regiment.counter.status == CombatObservationStatus::unavailable) {
        append_missing_domain("counter_operands");
      }
    }
    if (!army.knights.available) {
      append_missing_domain("knights");
    }
  }
  for (const auto &combat : output.ongoing_combats) {
    if (!combat.available) {
      append_missing_domain("ongoing_combat_context");
    }
  }
  for (const auto &resolution : output.counter_resolutions) {
    if (!resolution.available) {
      append_missing_domain("counter_resolutions");
    }
  }
  output.input_observation_ready = output.missing_required_domains.empty();
  append_missing_domain("damage_to_casualty_allocation");
  append_missing_domain("pursuit_transition");
  append_missing_domain("battle_end_and_retreat_transition");
  append_missing_domain("phase_event_rng_and_effects");
  partial = partial || has_unavailable_subdomain ||
            !output.input_observation_ready;
  return partial ? ReadCombatSimulationInputsResult::partial
                 : ReadCombatSimulationInputsResult::available;
}

PauseSubmitResult SubmitPauseMap(const Bindings &bindings) noexcept {
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return PauseSubmitResult::unavailable;
  }
  if (current.paused) {
    return PauseSubmitResult::already_paused;
  }
  if (bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.get_local_player == nullptr ||
      bindings.pause_primary_vtable == 0 ||
      bindings.pause_secondary_vtable == 0) {
    return PauseSubmitResult::unavailable;
  }

  void *const jomini_state = *bindings.jomini_state_slot;
  void *const player = bindings.get_local_player(jomini_state);
  if (player == nullptr) {
    return PauseSubmitResult::unavailable;
  }
  const std::int32_t player_id = LoadAt<std::int32_t>(player, kPlayerIdOffset);
  if (player_id < 0) {
    return PauseSubmitResult::unavailable;
  }

  PauseCommand command{};
  command.primary_vtable = bindings.pause_primary_vtable;
  command.flags = 0x08;
  command.secondary_vtable = bindings.pause_secondary_vtable;
  command.player_id = player_id;
  command.paused = 1;
  bindings.submit_command(bindings.command_manager, &command, 7);
  return PauseSubmitResult::submitted;
}

ResumeSubmitResult SubmitResumeMap(const Bindings &bindings) noexcept {
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return ResumeSubmitResult::unavailable;
  }
  if (!current.paused) {
    return ResumeSubmitResult::already_running;
  }
  if (bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.get_local_player == nullptr ||
      bindings.pause_primary_vtable == 0 ||
      bindings.pause_secondary_vtable == 0) {
    return ResumeSubmitResult::unavailable;
  }

  void *const jomini_state = *bindings.jomini_state_slot;
  void *const player = bindings.get_local_player(jomini_state);
  if (player == nullptr) {
    return ResumeSubmitResult::unavailable;
  }
  const std::int32_t player_id = LoadAt<std::int32_t>(player, kPlayerIdOffset);
  if (player_id < 0) {
    return ResumeSubmitResult::unavailable;
  }

  PauseCommand command{};
  command.primary_vtable = bindings.pause_primary_vtable;
  command.flags = 0x08;
  command.secondary_vtable = bindings.pause_secondary_vtable;
  command.player_id = player_id;
  command.paused = 0;
  bindings.submit_command(bindings.command_manager, &command, 7);
  return ResumeSubmitResult::submitted;
}

bool SubmitSetSpeed(const Bindings &bindings, std::int32_t speed) noexcept {
  if (!bindings.enabled || speed < 1 || speed > 5 ||
      bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.set_speed_primary_vtable == 0 ||
      bindings.set_speed_secondary_vtable == 0) {
    return false;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return false;
  }

  SetSpeedCommand command{};
  command.primary_vtable = bindings.set_speed_primary_vtable;
  command.secondary_vtable = bindings.set_speed_secondary_vtable;
  command.speed = speed - 1;
  bindings.submit_command(bindings.command_manager, &command, 7);
  return true;
}

SelectEventOptionResult
SubmitSelectEventOption(const Bindings &bindings,
                        std::int32_t option_index) noexcept {
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.select_event_option_primary_vtable == 0 ||
      bindings.select_event_option_secondary_vtable == 0 ||
      bindings.get_current_event == nullptr) {
    return SelectEventOptionResult::unavailable;
  }
  void *const game_state = *bindings.game_state_slot;
  if (game_state == nullptr) {
    return SelectEventOptionResult::unavailable;
  }

  std::int32_t event_instance_id = -1;
  std::int32_t option_count = 0;
  if (!ReadCurrentEvent(bindings, game_state, event_instance_id,
                        option_count)) {
    return SelectEventOptionResult::no_active_event;
  }
  if (option_index < 0 || option_index >= option_count) {
    return SelectEventOptionResult::option_out_of_range;
  }

  SelectEventOptionCommand command{};
  command.primary_vtable = bindings.select_event_option_primary_vtable;
  command.secondary_vtable = bindings.select_event_option_secondary_vtable;
  command.event_instance_id = event_instance_id;
  command.option_index = option_index;
  bindings.submit_command(bindings.command_manager, &command, 7);
  return SelectEventOptionResult::submitted;
}

SaveCheckpointResult SubmitSaveCheckpoint(const Bindings &bindings) noexcept {
  if (!bindings.enabled || bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.auto_save_primary_vtable == 0 ||
      bindings.auto_save_secondary_vtable == 0) {
    return {};
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return {};
  }
  if (!current.map_ready) {
    return {SaveCheckpointStatus::map_not_ready, current.date_raw};
  }

  AutoSaveCommand command{};
  command.primary_vtable = bindings.auto_save_primary_vtable;
  command.flags = 0x20;
  command.secondary_vtable = bindings.auto_save_secondary_vtable;
  constexpr std::size_t save_name_length = sizeof(kCheckpointSaveName) - 1U;
  static_assert(save_name_length < 16U);
  std::memcpy(command.save_name.buffer.data(), kCheckpointSaveName,
              save_name_length);
  command.save_name.size = save_name_length;
  bindings.submit_command(bindings.command_manager, &command, 7);
  return {SaveCheckpointStatus::submitted, current.date_raw};
}

ReplyPendingInteractionResult SubmitReplyToPendingInteraction(
    const Bindings &bindings, PendingInteractionReply reply) noexcept {
  if (!bindings.enabled || bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.reply_character_interaction_primary_vtable == 0 ||
      bindings.reply_character_interaction_secondary_vtable == 0) {
    return ReplyPendingInteractionResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return ReplyPendingInteractionResult::unavailable;
  }
  if (!current.has_pending_character_interaction) {
    return ReplyPendingInteractionResult::no_pending_interaction;
  }
  if (current.pending_auto_accept_notification) {
    return ReplyPendingInteractionResult::acknowledgement_required;
  }

  ReplyCharacterInteractionCommand command{};
  command.primary_vtable =
      bindings.reply_character_interaction_primary_vtable;
  command.secondary_vtable =
      bindings.reply_character_interaction_secondary_vtable;
  command.pending_interaction_id =
      current.pending_character_interaction_id;
  command.reply = static_cast<std::int32_t>(reply);
  bindings.submit_command(bindings.command_manager, &command, 0x0E);
  return ReplyPendingInteractionResult::submitted;
}

AcknowledgePendingInteractionResult SubmitAcknowledgePendingInteraction(
    const Bindings &bindings,
    std::int32_t pending_interaction_id) noexcept {
  if (!bindings.enabled || pending_interaction_id == -1 ||
      bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.pending_character_interaction_storage_slot == nullptr ||
      bindings.character_storage_slot == nullptr ||
      bindings.is_pending_character_interaction_for_character == nullptr ||
      bindings.reply_character_interaction_primary_vtable == 0 ||
      bindings.reply_character_interaction_secondary_vtable == 0) {
    return AcknowledgePendingInteractionResult::unavailable;
  }

  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return AcknowledgePendingInteractionResult::unavailable;
  }
  if (!current.paused) {
    return AcknowledgePendingInteractionResult::requires_paused;
  }
  if (!current.has_pending_character_interaction) {
    return AcknowledgePendingInteractionResult::no_pending_interaction;
  }
  if (current.pending_character_interaction_id != pending_interaction_id) {
    return AcknowledgePendingInteractionResult::pending_interaction_mismatch;
  }
  if (!current.pending_auto_accept_notification) {
    return AcknowledgePendingInteractionResult::acknowledgement_not_required;
  }

  void *const played_character =
      ResolveCharacter(bindings, current.played_character_id);
  if (played_character == nullptr) {
    return AcknowledgePendingInteractionResult::not_for_played_character;
  }
  void *const pending = ResolveStoredComponent(
      bindings.pending_character_interaction_storage_slot,
      pending_interaction_id, kPendingInteractionIdOffset);
  if (pending == nullptr) {
    return AcknowledgePendingInteractionResult::state_changed;
  }
  if (LoadAt<std::uint8_t>(pending,
                           kPendingInteractionAutoAcceptOffset) == 0) {
    return AcknowledgePendingInteractionResult::acknowledgement_not_required;
  }
  if (!bindings.is_pending_character_interaction_for_character(
          pending, played_character)) {
    return AcknowledgePendingInteractionResult::not_for_played_character;
  }
  if (LoadAt<std::int32_t>(pending, kPendingInteractionIdOffset) !=
          pending_interaction_id ||
      LoadAt<std::uint8_t>(pending,
                           kPendingInteractionAutoAcceptOffset) == 0) {
    return AcknowledgePendingInteractionResult::state_changed;
  }

  ReplyCharacterInteractionCommand command{};
  command.primary_vtable =
      bindings.reply_character_interaction_primary_vtable;
  command.secondary_vtable =
      bindings.reply_character_interaction_secondary_vtable;
  command.pending_interaction_id = pending_interaction_id;
  command.reply = 4;
  if (!bindings.submit_command(bindings.command_manager, &command, 0x0E)) {
    return AcknowledgePendingInteractionResult::queue_rejected;
  }
  return AcknowledgePendingInteractionResult::submitted;
}

RaiseTroopsResult SubmitRaiseTroopsDefault(
    const Bindings &bindings) noexcept {
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.resolve_default_raise_province == nullptr ||
      bindings.construct_raise_troops_command == nullptr ||
      bindings.validate_raise_troops_command == nullptr ||
      bindings.destroy_raise_troops_command == nullptr ||
      bindings.raise_troops_primary_vtable == 0 ||
      bindings.raise_troops_secondary_vtable == 0) {
    return RaiseTroopsResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return RaiseTroopsResult::unavailable;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return RaiseTroopsResult::no_played_character;
  }
  void *const character =
      ResolveCharacter(bindings, current.played_character_id);
  if (character == nullptr) {
    return RaiseTroopsResult::no_played_character;
  }
  void *const default_province =
      bindings.resolve_default_raise_province(character);
  if (default_province == nullptr) {
    return RaiseTroopsResult::no_default_province;
  }
  const std::int32_t province_id =
      LoadAt<std::int32_t>(default_province, kProvinceIdOffset);
  void *const game_state = *bindings.game_state_slot;
  if (province_id < 1 || ResolveProvince(game_state, province_id) == nullptr) {
    return RaiseTroopsResult::no_default_province;
  }

  RaiseTroopsCommandStorage storage{};
  RaiseEntry entry{province_id, -1};
  void *const command = storage.bytes.data();
  if (bindings.construct_raise_troops_command(
          command, current.played_character_id, &entry) != command) {
    return RaiseTroopsResult::unavailable;
  }
  const bool layout_matches =
      LoadAt<std::uintptr_t>(command, 0x00) ==
          bindings.raise_troops_primary_vtable &&
      LoadAt<std::uintptr_t>(command, 0x18) ==
          bindings.raise_troops_secondary_vtable;
  if (!layout_matches) {
    bindings.destroy_raise_troops_command(command, 0);
    return RaiseTroopsResult::unavailable;
  }
  if (!bindings.validate_raise_troops_command(command, nullptr)) {
    bindings.destroy_raise_troops_command(command, 0);
    return RaiseTroopsResult::validation_failed;
  }
  bindings.submit_command(bindings.command_manager, command, 7);
  bindings.destroy_raise_troops_command(command, 0);
  return RaiseTroopsResult::submitted;
}

MoveArmyResult SubmitMoveArmy(const Bindings &bindings,
                              std::int32_t army_id,
                              std::int32_t province_id) noexcept {
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.get_army_move_mode == nullptr ||
      bindings.can_character_use_command_kind == nullptr ||
      bindings.can_army_use_move_mode == nullptr ||
      bindings.can_move_army == nullptr ||
      bindings.construct_army_move_path == nullptr ||
      bindings.destroy_move_army_command == nullptr ||
      bindings.move_army_primary_vtable == 0 ||
      bindings.move_army_secondary_vtable == 0) {
    return MoveArmyResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return MoveArmyResult::unavailable;
  }
  void *const army = ResolveArmy(bindings, army_id);
  if (army == nullptr) {
    return MoveArmyResult::army_not_found;
  }
  bool controllable = false;
  for (const auto &candidate : current.player_armies) {
    if (candidate.army_id == army_id && candidate.controllable) {
      controllable = true;
      break;
    }
  }
  if (!controllable) {
    return MoveArmyResult::army_not_controllable;
  }
  void *const game_state = *bindings.game_state_slot;
  void *const province = ResolveProvince(game_state, province_id);
  if (province == nullptr) {
    return MoveArmyResult::province_not_found;
  }
  // The map UI submits the local-player command kind. Kind 2 is the
  // AI/controller path and fails its controller gate for a player army.
  constexpr std::int32_t command_kind = 1;
  constexpr std::int32_t direct_target = 1;
  const std::int32_t move_mode =
      bindings.get_army_move_mode(army, province, direct_target);
  if (move_mode == 2) {
    return MoveArmyResult::move_mode_unavailable;
  }
  void *const owner_character =
      ResolveCharacter(bindings, current.played_character_id);
  if (owner_character == nullptr ||
      !bindings.can_character_use_command_kind(owner_character,
                                                command_kind)) {
    return MoveArmyResult::character_state_rejected;
  }
  if (!bindings.can_army_use_move_mode(army, move_mode)) {
    return MoveArmyResult::army_state_rejected;
  }
  if (!bindings.can_move_army(command_kind, army, move_mode)) {
    return MoveArmyResult::validation_failed;
  }

  MoveArmyCommand command{};
  command.primary_vtable = bindings.move_army_primary_vtable;
  command.secondary_vtable = bindings.move_army_secondary_vtable;
  command.command_kind = command_kind;
  command.army_id = army_id;
  command.destination_province_id = province_id;
  command.move_mode = move_mode;
  bindings.construct_army_move_path(command.path_storage.data());
  bindings.submit_command(bindings.command_manager, &command, 0x0E);
  bindings.destroy_move_army_command(&command, 0);
  return MoveArmyResult::submitted;
}

PreviewMoveArmyResult PreviewMoveArmy(const Bindings &bindings,
                                      std::int32_t army_id,
                                      std::int32_t province_id) noexcept {
  PreviewMoveArmyResult result{};
  result.army_id = army_id;
  result.target_province_id = province_id;
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.get_army_move_mode == nullptr ||
      bindings.can_character_use_command_kind == nullptr ||
      bindings.can_army_use_move_mode == nullptr ||
      bindings.can_move_army == nullptr ||
      bindings.resolve_move_origin == nullptr ||
      bindings.construct_move_path_context == nullptr ||
      bindings.construct_army_move_path == nullptr ||
      bindings.build_army_move_route == nullptr ||
      bindings.destroy_move_army_command == nullptr ||
      bindings.move_army_primary_vtable == 0 ||
      bindings.move_army_secondary_vtable == 0) {
    return result;
  }

  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return result;
  }
  if (!current.paused) {
    result.status = PreviewMoveArmyStatus::requires_paused;
    return result;
  }
  void *const army = ResolveArmy(bindings, army_id);
  if (army == nullptr) {
    result.status = PreviewMoveArmyStatus::army_not_found;
    return result;
  }
  const ArmySnapshot *selected_army = nullptr;
  for (const auto &candidate : current.player_armies) {
    if (candidate.army_id == army_id && candidate.controllable) {
      selected_army = &candidate;
      break;
    }
  }
  if (selected_army == nullptr) {
    result.status = PreviewMoveArmyStatus::army_not_controllable;
    return result;
  }

  void *const game_state = *bindings.game_state_slot;
  if (!selected_army->has_current_province) {
    result.status = PreviewMoveArmyStatus::origin_unavailable;
    return result;
  }
  const auto observed_current_province_id =
      selected_army->current_province_id;
  void *const observed_current_province =
      ResolveProvince(game_state, observed_current_province_id);
  if (observed_current_province == nullptr ||
      LoadAt<void *>(army, kArmyCurrentProvinceOffset) !=
          observed_current_province) {
    result.status = PreviewMoveArmyStatus::origin_unavailable;
    return result;
  }
  void *const target_province = ResolveProvince(game_state, province_id);
  if (target_province == nullptr) {
    result.status = PreviewMoveArmyStatus::province_not_found;
    return result;
  }

  constexpr std::int32_t command_kind = 1;
  constexpr std::int32_t direct_target = 1;
  constexpr std::int32_t route_kind = 2;
  const std::int32_t move_mode =
      bindings.get_army_move_mode(army, target_province, direct_target);
  if (move_mode == 2) {
    result.status = PreviewMoveArmyStatus::move_mode_unavailable;
    return result;
  }
  void *const owner_character =
      ResolveCharacter(bindings, current.played_character_id);
  if (owner_character == nullptr ||
      !bindings.can_character_use_command_kind(owner_character,
                                                command_kind)) {
    result.status = PreviewMoveArmyStatus::character_state_rejected;
    return result;
  }
  if (!bindings.can_army_use_move_mode(army, move_mode)) {
    result.status = PreviewMoveArmyStatus::army_state_rejected;
    return result;
  }
  if (!bindings.can_move_army(command_kind, army, move_mode)) {
    result.status = PreviewMoveArmyStatus::validation_failed;
    return result;
  }

  const std::uint8_t mode_is_one = move_mode == 1 ? 1U : 0U;
  MoveOriginContext origin_context{
      &mode_is_one,
      army,
      target_province,
  };
  void *const effective_origin_province =
      bindings.resolve_move_origin(&origin_context);
  if (effective_origin_province == nullptr) {
    result.status = PreviewMoveArmyStatus::origin_unavailable;
    return result;
  }
  const auto effective_origin_province_id =
      LoadAt<std::int32_t>(effective_origin_province, kProvinceIdOffset);
  if (ResolveProvince(game_state, effective_origin_province_id) !=
      effective_origin_province) {
    result.status = PreviewMoveArmyStatus::origin_unavailable;
    return result;
  }
  const bool effective_origin_is_observed_current =
      effective_origin_province_id == observed_current_province_id;
  const bool effective_origin_is_paused_route_front =
      !selected_army->route_province_ids.empty() &&
      effective_origin_province_id ==
          selected_army->route_province_ids.front();
  if (!effective_origin_is_observed_current &&
      !effective_origin_is_paused_route_front) {
    result.status = PreviewMoveArmyStatus::origin_unavailable;
    return result;
  }
  // ResolveMoveOrigin advances to the next Province while a CUnit is already
  // travelling along an edge. Keep the public origin stable at the Province
  // observed in the same paused snapshot and expose that effective origin as
  // the first remaining route entry instead. Do not simplify the native A*
  // tail: revisiting the observed Province is a real mid-edge route shape.
  result.origin_province_id = observed_current_province_id;

  MoveArmyCommand command{};
  command.primary_vtable = bindings.move_army_primary_vtable;
  command.secondary_vtable = bindings.move_army_secondary_vtable;
  command.command_kind = command_kind;
  command.army_id = army_id;
  command.destination_province_id = province_id;
  command.move_mode = move_mode;
  command.route_kind = route_kind;
  command.direct_target = direct_target;
  void *const constructed_path =
      bindings.construct_army_move_path(command.path_storage.data());
  MoveArmyCommandCleanup cleanup{
      bindings.destroy_move_army_command,
      &command,
  };
  if (constructed_path != command.path_storage.data()) {
    return result;
  }

  if (observed_current_province_id == province_id &&
      effective_origin_is_observed_current) {
    result.status = PreviewMoveArmyStatus::available;
    return result;
  }
  if (effective_origin_province_id == province_id) {
    result.route_province_ids.push_back(effective_origin_province_id);
    result.status = PreviewMoveArmyStatus::available;
    return result;
  }

  MovePathContextStorage path_context{};
  if (bindings.construct_move_path_context(path_context.bytes.data(), army) !=
      path_context.bytes.data()) {
    result.status = PreviewMoveArmyStatus::route_unavailable;
    return result;
  }
  if (!bindings.build_army_move_route(
          path_context.bytes.data(), effective_origin_province,
          target_province,
          route_kind, command.path_storage.data())) {
    result.status = PreviewMoveArmyStatus::route_unavailable;
    return result;
  }

  void *const province_infos =
      LoadAt<void *>(command.path_storage.data(), 0x00);
  const auto capacity =
      LoadAt<std::int32_t>(command.path_storage.data(), 0x08);
  const auto count =
      LoadAt<std::int32_t>(command.path_storage.data(), 0x0C);
  if (capacity < 0 || count <= 0 || count > capacity ||
      count > kMaximumUnitRouteProvinceInfos || province_infos == nullptr) {
    result.status = PreviewMoveArmyStatus::route_unavailable;
    return result;
  }

  std::vector<std::int32_t> route_province_ids;
  route_province_ids.reserve(
      static_cast<std::size_t>(count) +
      (effective_origin_is_observed_current ? 0U : 1U));
  if (!effective_origin_is_observed_current) {
    route_province_ids.push_back(effective_origin_province_id);
  }
  for (std::int32_t index = 0; index < count; ++index) {
    void *const province_info = LoadAt<void *>(
        province_infos, static_cast<std::size_t>(index) * sizeof(void *));
    if (province_info == nullptr) {
      result.status = PreviewMoveArmyStatus::route_unavailable;
      return result;
    }
    const auto route_province_id =
        LoadAt<std::int32_t>(province_info, kUnitPathProvinceIdOffset);
    if (ResolveProvince(game_state, route_province_id) == nullptr) {
      result.status = PreviewMoveArmyStatus::route_unavailable;
      return result;
    }
    route_province_ids.push_back(route_province_id);
  }
  if (route_province_ids.back() != province_id) {
    result.status = PreviewMoveArmyStatus::route_unavailable;
    return result;
  }

  result.route_province_ids = std::move(route_province_ids);
  result.status = PreviewMoveArmyStatus::available;
  return result;
}

namespace {

constexpr std::int64_t kRouteDurationScale = 100'000;
constexpr std::int64_t kRouteDurationFailureSentinel = 0xFFFF'FFFFLL;
constexpr std::int64_t kMaximumProjectedRouteDurationRaw =
    365'000LL * kRouteDurationScale;

struct NativeMovePathPrefix {
  void *province_infos = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
};

static_assert(offsetof(NativeMovePathPrefix, province_infos) == 0x00);
static_assert(offsetof(NativeMovePathPrefix, capacity) == 0x08);
static_assert(offsetof(NativeMovePathPrefix, count) == 0x0C);
static_assert(sizeof(NativeMovePathPrefix) == 0x10);

bool AddRouteDuration(std::int64_t left, std::int64_t right,
                      std::int64_t &output) noexcept {
  if (left < 0 || right < 0 ||
      left > (std::numeric_limits<std::int64_t>::max)() - right) {
    return false;
  }
  output = left + right;
  return true;
}

bool RouteDurationToDate(std::int32_t date_raw, std::int64_t duration_raw,
                         std::int32_t &output) noexcept {
  if (duration_raw < 0 ||
      duration_raw >
          (std::numeric_limits<std::int64_t>::max)() -
              (kRouteDurationScale / 2)) {
    return false;
  }
  const auto rounded_days =
      (duration_raw + (kRouteDurationScale / 2)) / kRouteDurationScale;
  if (rounded_days >
      ((std::numeric_limits<std::int64_t>::max)() / 24)) {
    return false;
  }
  const auto delta = rounded_days * 24;
  const auto projected = static_cast<std::int64_t>(date_raw) + delta;
  if (projected < (std::numeric_limits<std::int32_t>::min)() ||
      projected > (std::numeric_limits<std::int32_t>::max)()) {
    return false;
  }
  output = static_cast<std::int32_t>(projected);
  return true;
}

bool ReadPathHeader(const void *path_storage,
                    NativeMovePathPrefix &output) noexcept {
  if (path_storage == nullptr) {
    return false;
  }
  output.province_infos = LoadAt<void *>(path_storage, 0x00);
  output.capacity = LoadAt<std::int32_t>(path_storage, 0x08);
  output.count = LoadAt<std::int32_t>(path_storage, 0x0C);
  return output.capacity >= 0 && output.count >= 0 &&
         output.count <= output.capacity &&
         output.count <= kMaximumUnitRouteProvinceInfos &&
         (output.count == 0 || output.province_infos != nullptr);
}

bool PathSharesActiveRouteFront(void *unit, const void *path_storage,
                                bool &output) noexcept {
  output = false;
  if (unit == nullptr) {
    return false;
  }
  NativeMovePathPrefix proposed{};
  NativeMovePathPrefix active{};
  const auto *const active_path =
      static_cast<const std::byte *>(unit) + kUnitPathProvinceInfosOffset;
  if (!ReadPathHeader(path_storage, proposed) || proposed.count <= 0 ||
      !ReadPathHeader(active_path, active)) {
    return false;
  }
  if (active.count == 0) {
    return true;
  }
  void *const proposed_front = LoadAt<void *>(proposed.province_infos, 0);
  void *const active_front = LoadAt<void *>(active.province_infos, 0);
  if (proposed_front == nullptr || active_front == nullptr) {
    return false;
  }
  output = LoadAt<std::int32_t>(proposed_front,
                                kUnitPathProvinceIdOffset) ==
           LoadAt<std::int32_t>(active_front,
                                kUnitPathProvinceIdOffset);
  return true;
}

bool ReadRouteTravelSpeeds(const Bindings &bindings, void *unit,
                           std::int64_t &land_speed,
                           std::int64_t &naval_speed) noexcept {
  land_speed = 0;
  naval_speed = 0;
  if (bindings.read_unit_land_route_speed == nullptr ||
      bindings.read_unit_naval_route_speed == nullptr || unit == nullptr) {
    return false;
  }
  return bindings.read_unit_land_route_speed(unit, &land_speed) ==
             &land_speed &&
         bindings.read_unit_naval_route_speed(unit, &naval_speed) ==
             &naval_speed;
}

bool CurrentEdgeSpeedIsPositive(const Bindings &bindings, void *unit,
                                const void *path_storage) noexcept {
  bool shares_active_front = false;
  if (!PathSharesActiveRouteFront(unit, path_storage,
                                  shares_active_front)) {
    return false;
  }
  if (!shares_active_front) {
    return true;
  }
  auto current_edge_speed = LoadAt<std::int64_t>(
      unit, kUnitCachedCurrentEdgeSpeedOffset);
  if (current_edge_speed > 0) {
    return true;
  }
  if (bindings.read_unit_current_edge_speed == nullptr) {
    return false;
  }
  current_edge_speed = 0;
  return bindings.read_unit_current_edge_speed(
             unit, &current_edge_speed) == &current_edge_speed &&
         current_edge_speed > 0;
}

bool ValidateRouteTimingInputs(const Bindings &bindings, void *game_state,
                               void *unit, const void *path_storage,
                               void *origin_province) noexcept {
  NativeMovePathPrefix path{};
  std::int64_t land_speed = 0;
  std::int64_t naval_speed = 0;
  if (game_state == nullptr || unit == nullptr || origin_province == nullptr ||
      !ReadPathHeader(path_storage, path) || path.count <= 0 ||
      !ReadRouteTravelSpeeds(bindings, unit, land_speed, naval_speed) ||
      !CurrentEdgeSpeedIsPositive(bindings, unit, path_storage)) {
    return false;
  }

  void *edge_origin = origin_province;
  void *const origin_map_node =
      LoadAt<void *>(edge_origin, kProvinceMapNodeOffset);
  if (origin_map_node == nullptr) {
    return false;
  }
  void *source_info =
      LoadAt<void *>(origin_map_node, kMapNodePathProvinceInfoOffset);
  if (source_info == nullptr) {
    return false;
  }

  for (std::int32_t index = 0; index < path.count; ++index) {
    void *const destination_info = LoadAt<void *>(
        path.province_infos,
        static_cast<std::size_t>(index) * sizeof(void *));
    if (destination_info == nullptr) {
      return false;
    }
    const auto destination_id = LoadAt<std::int32_t>(
        destination_info, kUnitPathProvinceIdOffset);
    void *const destination = ResolveProvince(game_state, destination_id);
    std::int32_t adjacency_kind = -1;
    if (destination == nullptr ||
        ReadProvinceAdjacencyKind(edge_origin, destination_id,
                                  adjacency_kind) !=
            ReadAdjacencyKindResult::available) {
      return false;
    }

    const bool source_is_land =
        LoadAt<std::uint8_t>(source_info, kPathProvinceInfoLandOffset) != 0;
    const bool source_is_water =
        LoadAt<std::uint8_t>(source_info, kPathProvinceInfoWaterOffset) != 0;
    const bool destination_is_land = LoadAt<std::uint8_t>(
                                               destination_info,
                                               kPathProvinceInfoLandOffset) !=
                                           0;
    const bool destination_is_water = LoadAt<std::uint8_t>(
                                                destination_info,
                                                kPathProvinceInfoWaterOffset) !=
                                            0;
    // Exact 0x23C45B0 branch order: embark/disembark use their fixed costs;
    // same-medium travel divides by the corresponding unit speed.  A zero
    // divisor is reported only as the additive uint32 0xffffffff value, so it
    // must be rejected before the duration ABI can silently accumulate it.
    if (source_is_land) {
      if (!destination_is_water && land_speed <= 0) {
        return false;
      }
    } else if (source_is_water) {
      if (!destination_is_land && naval_speed <= 0) {
        return false;
      }
    }

    edge_origin = destination;
    source_info = destination_info;
  }
  return true;
}

bool ProjectPathTimeline(
    const Bindings &bindings, void *game_state, void *unit,
    const void *path_storage, void *origin_province,
    std::int32_t date_raw, std::int64_t base_duration_raw,
    std::vector<std::int32_t> &province_ids,
    std::vector<std::int32_t> &arrival_date_raws) noexcept {
  province_ids.clear();
  arrival_date_raws.clear();
  if (bindings.read_route_travel_duration == nullptr || game_state == nullptr ||
      unit == nullptr || origin_province == nullptr || base_duration_raw < 0) {
    return false;
  }

  NativeMovePathPrefix full{};
  if (!ReadPathHeader(path_storage, full)) {
    return false;
  }
  if (full.count > 0 &&
      !ValidateRouteTimingInputs(bindings, game_state, unit, path_storage,
                                 origin_province)) {
    return false;
  }
  province_ids.reserve(static_cast<std::size_t>(full.count));
  arrival_date_raws.reserve(static_cast<std::size_t>(full.count));
  std::int32_t prior_arrival = date_raw;
  std::int64_t prior_path_duration_raw = 0;
  void *edge_origin = origin_province;
  for (std::int32_t index = 0; index < full.count; ++index) {
    void *const province_info = LoadAt<void *>(
        full.province_infos, static_cast<std::size_t>(index) * sizeof(void *));
    if (province_info == nullptr) {
      return false;
    }
    const auto province_id =
        LoadAt<std::int32_t>(province_info, kUnitPathProvinceIdOffset);
    void *const next_province = ResolveProvince(game_state, province_id);
    std::int32_t adjacency_kind = -1;
    if (next_province == nullptr ||
        ReadProvinceAdjacencyKind(edge_origin, province_id,
                                  adjacency_kind) !=
            ReadAdjacencyKindResult::available) {
      return false;
    }
    edge_origin = next_province;

    // The original helper reads only MovePath+0/+0x0C.  Give every prefix its
    // own zeroed full-size view so no owned allocator/cost tail can be
    // mistaken for shallow storage or destroyed by this reader.
    std::array<std::byte, 0x130> prefix{};
    StoreAt(prefix.data(), 0x00, full.province_infos);
    StoreAt(prefix.data(), 0x0C, index + 1);
    std::int64_t path_duration_raw = -1;
    if (bindings.read_route_travel_duration(
            unit, &path_duration_raw, prefix.data(), origin_province) !=
            &path_duration_raw ||
        path_duration_raw < 0) {
      return false;
    }
    if (path_duration_raw == kRouteDurationFailureSentinel ||
        path_duration_raw > kMaximumProjectedRouteDurationRaw ||
        path_duration_raw < prior_path_duration_raw) {
      return false;
    }
    std::int64_t total_duration_raw = 0;
    std::int32_t arrival_date_raw = 0;
    if (!AddRouteDuration(base_duration_raw, path_duration_raw,
                          total_duration_raw) ||
        !RouteDurationToDate(date_raw, total_duration_raw,
                             arrival_date_raw) ||
        arrival_date_raw < prior_arrival) {
      return false;
    }
    province_ids.push_back(province_id);
    arrival_date_raws.push_back(arrival_date_raw);
    prior_arrival = arrival_date_raw;
    prior_path_duration_raw = path_duration_raw;
  }
  return province_ids.size() == arrival_date_raws.size();
}

bool ReadFirstActiveEdgeDuration(const Bindings &bindings, void *game_state,
                                 void *unit, void *current_province,
                                 std::int32_t expected_front_province_id,
                                 std::int64_t &duration_raw) noexcept {
  duration_raw = -1;
  NativeMovePathPrefix active{};
  const auto *const path_storage =
      static_cast<const std::byte *>(unit) + kUnitPathProvinceInfosOffset;
  if (!ReadPathHeader(path_storage, active) || active.count <= 0) {
    return false;
  }
  void *const first_info = LoadAt<void *>(active.province_infos, 0);
  if (first_info == nullptr ||
      LoadAt<std::int32_t>(first_info, kUnitPathProvinceIdOffset) !=
          expected_front_province_id ||
      ResolveProvince(game_state, expected_front_province_id) == nullptr) {
    return false;
  }
  std::array<std::byte, 0x130> prefix{};
  StoreAt(prefix.data(), 0x00, active.province_infos);
  StoreAt(prefix.data(), 0x0C, std::int32_t{1});
  const bool read = ValidateRouteTimingInputs(
                        bindings, game_state, unit, path_storage,
                        current_province) &&
                    bindings.read_route_travel_duration(
             unit, &duration_raw, prefix.data(), current_province) ==
             &duration_raw &&
         duration_raw >= 0 &&
         duration_raw != kRouteDurationFailureSentinel &&
         duration_raw <= kMaximumProjectedRouteDurationRaw;
  return read;
}

const ArmySnapshot *FindArmySnapshot(const Snapshot &snapshot,
                                     std::int32_t army_id) noexcept {
  for (const auto &army : snapshot.player_armies) {
    if (army.army_id == army_id) {
      return &army;
    }
  }
  for (const auto &war : snapshot.active_wars) {
    for (const auto &army : war.allied_armies) {
      if (army.army_id == army_id) {
        return &army;
      }
    }
    for (const auto &army : war.enemy_armies) {
      if (army.army_id == army_id) {
        return &army;
      }
    }
  }
  return nullptr;
}

bool CollectCompleteHostileScope(const Snapshot &snapshot,
                                 std::int32_t subject_army_id,
                                 std::vector<std::int32_t> &output) {
  (void)subject_army_id;
  output.clear();
  bool found_active_war = false;
  for (const auto &war : snapshot.active_wars) {
    found_active_war = true;
    for (const auto &enemy : war.enemy_armies) {
      if (!enemy.retreating && enemy.army_id > 0 &&
          std::find(output.begin(), output.end(), enemy.army_id) ==
              output.end()) {
        output.push_back(enemy.army_id);
      }
    }
  }
  std::sort(output.begin(), output.end());
  return found_active_war && !output.empty();
}

bool SameCanonicalIdSet(std::vector<std::int32_t> left,
                        std::vector<std::int32_t> right) {
  std::sort(left.begin(), left.end());
  std::sort(right.begin(), right.end());
  return left == right &&
         std::adjacent_find(left.begin(), left.end()) == left.end() &&
         std::adjacent_find(right.begin(), right.end()) == right.end();
}

bool BuildActiveRouteTimeline(const Bindings &bindings, void *game_state,
                              std::int32_t date_raw,
                              const ArmySnapshot &snapshot,
                              game::RouteTimelineSnapshot &output) noexcept {
  output = {};
  output.army_id = snapshot.army_id;
  if (!snapshot.has_current_province) {
    return false;
  }
  output.current_province_id = snapshot.current_province_id;
  output.effective_origin_province_id = snapshot.current_province_id;
  void *const unit = ResolveArmy(bindings, snapshot.army_id);
  void *const current_province =
      ResolveProvince(game_state, snapshot.current_province_id);
  if (unit == nullptr || current_province == nullptr ||
      LoadAt<void *>(unit, kArmyCurrentProvinceOffset) != current_province) {
    return false;
  }
  if (snapshot.route_province_ids.empty()) {
    NativeMovePathPrefix active{};
    const auto *const path_storage =
        static_cast<const std::byte *>(unit) + kUnitPathProvinceInfosOffset;
    output.timeline_observable =
        ReadPathHeader(path_storage, active) && active.count == 0;
    return output.timeline_observable;
  }
  output.effective_origin_province_id = snapshot.route_province_ids.front();
  const auto *const path_storage =
      static_cast<const std::byte *>(unit) + kUnitPathProvinceInfosOffset;
  if (!ProjectPathTimeline(bindings, game_state, unit, path_storage,
                           current_province, date_raw, 0,
                           output.route_province_ids,
                           output.arrival_date_raws) ||
      output.route_province_ids != snapshot.route_province_ids) {
    output.route_province_ids.clear();
    output.arrival_date_raws.clear();
    return false;
  }
  output.timeline_observable = true;
  return true;
}

RouteContactHorizonStatus BuildSubjectRouteTimeline(
    const Bindings &bindings, void *game_state, const Snapshot &snapshot,
    const game::RouteContactHorizonRequest &request,
    game::RouteTimelineSnapshot &output) noexcept {
  output = {};
  output.army_id = request.subject_army_id;
  const ArmySnapshot *selected = nullptr;
  for (const auto &candidate : snapshot.player_armies) {
    if (candidate.army_id == request.subject_army_id) {
      selected = &candidate;
      break;
    }
  }
  if (selected == nullptr) {
    return RouteContactHorizonStatus::subject_army_not_found;
  }
  if (!selected->controllable) {
    return RouteContactHorizonStatus::subject_army_not_controllable;
  }
  if (!selected->has_current_province) {
    return RouteContactHorizonStatus::route_unavailable;
  }

  void *const unit = ResolveArmy(bindings, request.subject_army_id);
  void *const current_province =
      ResolveProvince(game_state, selected->current_province_id);
  void *const target_province =
      ResolveProvince(game_state, request.target_province_id);
  if (unit == nullptr || current_province == nullptr ||
      LoadAt<void *>(unit, kArmyCurrentProvinceOffset) != current_province) {
    return RouteContactHorizonStatus::state_changed;
  }
  if (target_province == nullptr) {
    return RouteContactHorizonStatus::target_province_not_found;
  }

  // Re-querying the already committed target must project the exact stored
  // active MovePath.  Re-running A* could produce a different equal-cost tail
  // and would no longer prove the route the simulation is actually following.
  if (!selected->route_province_ids.empty() &&
      selected->route_province_ids.back() == request.target_province_id) {
    return BuildActiveRouteTimeline(bindings, game_state, snapshot.date_raw,
                                    *selected, output)
               ? RouteContactHorizonStatus::available
               : RouteContactHorizonStatus::timeline_unavailable;
  }

  constexpr std::int32_t direct_target = 1;
  constexpr std::int32_t route_kind = 2;
  const auto move_mode =
      bindings.get_army_move_mode(unit, target_province, direct_target);
  if (move_mode == 2) {
    return RouteContactHorizonStatus::route_unavailable;
  }
  const std::uint8_t mode_is_one = move_mode == 1 ? 1U : 0U;
  MoveOriginContext origin_context{&mode_is_one, unit, target_province};
  void *const effective_origin = bindings.resolve_move_origin(&origin_context);
  if (effective_origin == nullptr) {
    return RouteContactHorizonStatus::route_unavailable;
  }
  const auto effective_origin_id =
      LoadAt<std::int32_t>(effective_origin, kProvinceIdOffset);
  if (ResolveProvince(game_state, effective_origin_id) != effective_origin ||
      (effective_origin_id != selected->current_province_id &&
       (selected->route_province_ids.empty() ||
        effective_origin_id != selected->route_province_ids.front()))) {
    return RouteContactHorizonStatus::route_unavailable;
  }

  output.current_province_id = selected->current_province_id;
  output.effective_origin_province_id = effective_origin_id;
  std::int64_t first_edge_duration_raw = 0;
  if (effective_origin_id != selected->current_province_id) {
    if (!ReadFirstActiveEdgeDuration(
            bindings, game_state, unit, current_province,
            effective_origin_id, first_edge_duration_raw)) {
      return RouteContactHorizonStatus::timeline_unavailable;
    }
    std::int32_t first_arrival = 0;
    if (!RouteDurationToDate(snapshot.date_raw, first_edge_duration_raw,
                             first_arrival)) {
      return RouteContactHorizonStatus::timeline_unavailable;
    }
    output.route_province_ids.push_back(effective_origin_id);
    output.arrival_date_raws.push_back(first_arrival);
  }

  if (effective_origin_id == request.target_province_id) {
    output.timeline_observable = true;
    return RouteContactHorizonStatus::available;
  }
  if (effective_origin_id == selected->current_province_id &&
      selected->current_province_id == request.target_province_id) {
    output.timeline_observable = true;
    return RouteContactHorizonStatus::available;
  }

  MoveArmyCommand command{};
  command.primary_vtable = bindings.move_army_primary_vtable;
  command.secondary_vtable = bindings.move_army_secondary_vtable;
  command.command_kind = 1;
  command.army_id = request.subject_army_id;
  command.destination_province_id = request.target_province_id;
  command.move_mode = move_mode;
  command.route_kind = route_kind;
  command.direct_target = direct_target;
  if (bindings.construct_army_move_path(command.path_storage.data()) !=
      command.path_storage.data()) {
    return RouteContactHorizonStatus::route_unavailable;
  }
  MoveArmyCommandCleanup cleanup{bindings.destroy_move_army_command,
                                 &command};
  MovePathContextStorage path_context{};
  if (bindings.construct_move_path_context(path_context.bytes.data(), unit) !=
          path_context.bytes.data() ||
      !bindings.build_army_move_route(
          path_context.bytes.data(), effective_origin, target_province,
          route_kind, command.path_storage.data())) {
    return RouteContactHorizonStatus::route_unavailable;
  }

  std::vector<std::int32_t> tail_ids;
  std::vector<std::int32_t> tail_arrivals;
  if (!ProjectPathTimeline(
          bindings, game_state, unit, command.path_storage.data(),
          effective_origin, snapshot.date_raw, first_edge_duration_raw,
          tail_ids, tail_arrivals) || tail_ids.empty() ||
      tail_ids.back() != request.target_province_id) {
    return RouteContactHorizonStatus::timeline_unavailable;
  }
  output.route_province_ids.insert(output.route_province_ids.end(),
                                   tail_ids.begin(), tail_ids.end());
  output.arrival_date_raws.insert(output.arrival_date_raws.end(),
                                  tail_arrivals.begin(), tail_arrivals.end());
  if (output.route_province_ids.size() != output.arrival_date_raws.size()) {
    return RouteContactHorizonStatus::timeline_unavailable;
  }
  output.timeline_observable = true;
  return RouteContactHorizonStatus::available;
}

struct ProvinceOccupancyInterval {
  std::int32_t province_id = -1;
  std::int32_t enter = 0;
  std::int32_t leave = 0;
};

struct RouteEdgeInterval {
  std::int32_t from = -1;
  std::int32_t to = -1;
  std::int32_t depart = 0;
  std::int32_t arrive = 0;
};

void BuildTimelineIntervals(const game::RouteTimelineSnapshot &route,
                            std::int32_t horizon_start,
                            std::int32_t horizon_end,
                            std::vector<ProvinceOccupancyInterval> &occupancy,
                            std::vector<RouteEdgeInterval> &edges) {
  occupancy.clear();
  edges.clear();
  if (route.route_province_ids.size() != route.arrival_date_raws.size()) {
    return;
  }
  const auto first_leave = route.arrival_date_raws.empty()
                               ? horizon_end
                               : route.arrival_date_raws.front();
  occupancy.push_back(
      {route.current_province_id, horizon_start, first_leave});
  std::int32_t from = route.current_province_id;
  std::int32_t depart = horizon_start;
  for (std::size_t index = 0; index < route.route_province_ids.size();
       ++index) {
    const auto to = route.route_province_ids[index];
    const auto arrive = route.arrival_date_raws[index];
    edges.push_back({from, to, depart, arrive});
    const auto leave = index + 1U < route.arrival_date_raws.size()
                           ? route.arrival_date_raws[index + 1U]
                           : horizon_end;
    occupancy.push_back({to, arrive, leave});
    from = to;
    depart = arrive;
  }
}

bool ClosedIntervalsOverlap(std::int32_t left_start,
                            std::int32_t left_end,
                            std::int32_t right_start,
                            std::int32_t right_end,
                            std::int32_t horizon_start,
                            std::int32_t horizon_end,
                            std::int32_t &overlap_start,
                            std::int32_t &overlap_end) noexcept {
  overlap_start = (std::max)({left_start, right_start, horizon_start});
  overlap_end = (std::min)({left_end, right_end, horizon_end});
  return overlap_start <= overlap_end;
}

void AppendContactConflicts(
    const game::RouteTimelineSnapshot &subject,
    const game::RouteTimelineSnapshot &hostile, std::int32_t horizon_start,
    std::int32_t horizon_end,
    std::vector<game::RouteContactConflictSnapshot> &output) {
  std::vector<ProvinceOccupancyInterval> subject_occupancy;
  std::vector<ProvinceOccupancyInterval> hostile_occupancy;
  std::vector<RouteEdgeInterval> subject_edges;
  std::vector<RouteEdgeInterval> hostile_edges;
  BuildTimelineIntervals(subject, horizon_start, horizon_end,
                         subject_occupancy, subject_edges);
  BuildTimelineIntervals(hostile, horizon_start, horizon_end,
                         hostile_occupancy, hostile_edges);
  for (const auto &left : subject_occupancy) {
    for (const auto &right : hostile_occupancy) {
      std::int32_t overlap_start = 0;
      std::int32_t overlap_end = 0;
      if (left.province_id == right.province_id &&
          ClosedIntervalsOverlap(left.enter, left.leave, right.enter,
                                 right.leave, horizon_start, horizon_end,
                                 overlap_start, overlap_end)) {
        game::RouteContactConflictSnapshot conflict{};
        conflict.kind = "same_province";
        conflict.hostile_army_id = hostile.army_id;
        conflict.province_id = left.province_id;
        conflict.overlap_start_date_raw = overlap_start;
        conflict.overlap_end_date_raw = overlap_end;
        if (std::find(output.begin(), output.end(), conflict) == output.end()) {
          output.push_back(std::move(conflict));
        }
      }
    }
  }
  for (const auto &left : subject_edges) {
    for (const auto &right : hostile_edges) {
      std::int32_t overlap_start = 0;
      std::int32_t overlap_end = 0;
      if (left.from == right.to && left.to == right.from &&
          ClosedIntervalsOverlap(left.depart, left.arrive, right.depart,
                                 right.arrive, horizon_start, horizon_end,
                                 overlap_start, overlap_end)) {
        game::RouteContactConflictSnapshot conflict{};
        conflict.kind = "opposing_edge";
        conflict.hostile_army_id = hostile.army_id;
        conflict.subject_from_province_id = left.from;
        conflict.subject_to_province_id = left.to;
        conflict.hostile_from_province_id = right.from;
        conflict.hostile_to_province_id = right.to;
        conflict.overlap_start_date_raw = overlap_start;
        conflict.overlap_end_date_raw = overlap_end;
        if (std::find(output.begin(), output.end(), conflict) == output.end()) {
          output.push_back(std::move(conflict));
        }
      }
    }
  }
}

bool RelevantRouteStateMatches(const Snapshot &before, const Snapshot &after,
                               const game::RouteContactHorizonRequest &request) {
  if (!after.paused || before.date_raw != after.date_raw) {
    return false;
  }
  const auto *const before_subject =
      FindArmySnapshot(before, request.subject_army_id);
  const auto *const after_subject =
      FindArmySnapshot(after, request.subject_army_id);
  if (before_subject == nullptr || after_subject == nullptr ||
      *before_subject != *after_subject) {
    return false;
  }
  for (const auto hostile_id : request.hostile_army_ids) {
    const auto *const before_hostile = FindArmySnapshot(before, hostile_id);
    const auto *const after_hostile = FindArmySnapshot(after, hostile_id);
    if (before_hostile == nullptr || after_hostile == nullptr ||
        *before_hostile != *after_hostile) {
      return false;
    }
  }
  std::vector<std::int32_t> after_scope;
  return CollectCompleteHostileScope(after, request.subject_army_id,
                                     after_scope) &&
         SameCanonicalIdSet(after_scope, request.hostile_army_ids);
}

} // namespace

RouteContactHorizonStatus ReadRouteContactHorizon(
    const Bindings &bindings, const RouteContactHorizonRequest &request,
    RouteContactHorizonSnapshot &output) noexcept {
  output = {};
  output.subject_army_id = request.subject_army_id;
  output.target_province_id = request.target_province_id;
  output.hostile_army_ids = request.hostile_army_ids;
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.jomini_state_slot == nullptr ||
      bindings.get_army_move_mode == nullptr ||
      bindings.resolve_move_origin == nullptr ||
      bindings.construct_move_path_context == nullptr ||
      bindings.construct_army_move_path == nullptr ||
      bindings.build_army_move_route == nullptr ||
      bindings.destroy_move_army_command == nullptr ||
      bindings.read_unit_land_route_speed == nullptr ||
      bindings.read_unit_naval_route_speed == nullptr ||
      bindings.read_unit_current_edge_speed == nullptr ||
      bindings.read_route_travel_duration == nullptr ||
      request.subject_army_id <= 0 || request.target_province_id <= 0 ||
      request.hostile_army_ids.empty() ||
      request.hostile_army_ids.size() > 64 ||
      std::find(request.hostile_army_ids.begin(),
                request.hostile_army_ids.end(),
                request.subject_army_id) != request.hostile_army_ids.end()) {
    output.status = RouteContactHorizonStatus::unavailable;
    return output.status;
  }
  for (const auto hostile_id : request.hostile_army_ids) {
    if (hostile_id <= 0 ||
        std::count(request.hostile_army_ids.begin(),
                   request.hostile_army_ids.end(), hostile_id) != 1) {
      output.status = RouteContactHorizonStatus::unavailable;
      return output.status;
    }
  }

  Snapshot before{};
  if (!ReadSnapshot(bindings, before)) {
    output.status = RouteContactHorizonStatus::unavailable;
    return output.status;
  }
  if (!before.paused) {
    output.status = RouteContactHorizonStatus::requires_paused;
    return output.status;
  }
  if (before.date_raw >
      (std::numeric_limits<std::int32_t>::max)() - 24) {
    output.status = RouteContactHorizonStatus::timeline_unavailable;
    return output.status;
  }
  output.date_raw = before.date_raw;
  output.horizon_start_date_raw = before.date_raw;
  output.horizon_end_date_raw = before.date_raw + 24;

  std::vector<std::int32_t> exact_hostile_scope;
  if (!CollectCompleteHostileScope(before, request.subject_army_id,
                                   exact_hostile_scope) ||
      !SameCanonicalIdSet(exact_hostile_scope,
                          request.hostile_army_ids)) {
    output.status = RouteContactHorizonStatus::hostile_scope_mismatch;
    return output.status;
  }

  void *const game_state = *bindings.game_state_slot;
  const auto subject_status = BuildSubjectRouteTimeline(
      bindings, game_state, before, request, output.subject_route);
  if (subject_status != RouteContactHorizonStatus::available) {
    output.status = subject_status;
    return output.status;
  }
  output.hostile_routes.clear();
  output.hostile_routes.reserve(request.hostile_army_ids.size());
  for (const auto hostile_id : request.hostile_army_ids) {
    const auto *const hostile = FindArmySnapshot(before, hostile_id);
    if (hostile == nullptr || hostile->retreating) {
      output.hostile_routes.clear();
      output.status = RouteContactHorizonStatus::state_changed;
      return output.status;
    }
    output.hostile_routes.emplace_back();
    if (!BuildActiveRouteTimeline(bindings, game_state, before.date_raw,
                                  *hostile,
                                  output.hostile_routes.back())) {
      output.hostile_routes.clear();
      output.status = RouteContactHorizonStatus::timeline_unavailable;
      return output.status;
    }
  }

  Snapshot after{};
  if (!ReadSnapshot(bindings, after) ||
      !RelevantRouteStateMatches(before, after, request) ||
      ResolveProvince(game_state, request.target_province_id) == nullptr) {
    output.subject_route = {};
    output.hostile_routes.clear();
    output.status = RouteContactHorizonStatus::state_changed;
    return output.status;
  }

  output.conflicts.clear();
  for (const auto &hostile : output.hostile_routes) {
    AppendContactConflicts(output.subject_route, hostile,
                           output.horizon_start_date_raw,
                           output.horizon_end_date_raw, output.conflicts);
  }
  output.one_day_contact_free = output.conflicts.empty();
  output.status = RouteContactHorizonStatus::available;
  return output.status;
}

namespace {

bool ReadContactIdArray(const void *owner, std::size_t data_offset,
                        std::size_t count_offset, std::int32_t maximum,
                        std::vector<std::int32_t> &output,
                        bool require_strictly_sorted) {
  output.clear();
  void *const data = LoadAt<void *>(owner, data_offset);
  const auto count = LoadAt<std::int32_t>(owner, count_offset);
  if (count < 0 || count > maximum || (count > 0 && data == nullptr)) {
    return false;
  }
  output.reserve(static_cast<std::size_t>(count));
  for (std::int32_t index = 0; index < count; ++index) {
    const auto id = LoadAt<std::int32_t>(
        data, static_cast<std::size_t>(index) * sizeof(std::int32_t));
    if (id <= 0 ||
        (require_strictly_sorted && !output.empty() &&
         output.back() >= id)) {
      output.clear();
      return false;
    }
    output.push_back(id);
  }
  return true;
}

bool ResolveContactCharacter(const Bindings &bindings,
                             std::int32_t character_id,
                             void *&character) noexcept {
  character = ResolveCharacter(bindings, character_id);
  if (character == nullptr) {
    return false;
  }
  bool identity_valid = false;
  return ReadSubobjectPredicate(character, kCharacterValiditySubobjectOffset,
                                identity_valid) &&
         identity_valid;
}

bool NativeArmyIdsToPublicUnitIds(
    const Bindings &bindings,
    const std::vector<std::int32_t> &native_army_ids,
    std::vector<std::int32_t> &public_unit_ids) noexcept {
  public_unit_ids.clear();
  public_unit_ids.reserve(native_army_ids.size());
  for (const auto native_id : native_army_ids) {
    void *const army = ResolveStoredComponent(
        bindings.army_internal_storage_slot, native_id,
        kInternalArmyIdOffset);
    if (army == nullptr) {
      public_unit_ids.clear();
      return false;
    }
    const auto unit_id =
        LoadAt<std::int32_t>(army, kInternalArmyUnitIdOffset);
    void *const unit = ResolveStoredComponent(
        bindings.army_storage_slot, unit_id, kArmyIdOffset);
    if (unit == nullptr ||
        LoadAt<std::int32_t>(unit, kUnitArmyIdOffset) != native_id) {
      public_unit_ids.clear();
      return false;
    }
    public_unit_ids.push_back(unit_id);
  }
  return true;
}

bool ReadCombatSidePublicUnitIds(
    const Bindings &bindings, const void *combat,
    std::size_t side_offset,
    std::vector<std::int32_t> &output) noexcept {
  std::vector<std::int32_t> native_ids;
  const auto *const side = static_cast<const std::byte *>(combat) + side_offset;
  return ReadContactIdArray(
             side, kCombatSideArmyIdsOffset, kCombatSideArmyCountOffset,
             kMaximumActualContactSideArmies, native_ids, false) &&
         NativeArmyIdsToPublicUnitIds(bindings, native_ids, output);
}

bool ReadActiveCombatSideIds(
    const Bindings &bindings, const void *combat,
    std::size_t side_offset, std::int32_t expected_combat_id,
    std::vector<std::int32_t> &native_ids,
    std::vector<std::int32_t> &public_unit_ids) noexcept {
  native_ids.clear();
  public_unit_ids.clear();
  const auto *const side = static_cast<const std::byte *>(combat) + side_offset;
  if (LoadAt<const void *>(side, kCombatSideCombatBackPointerOffset) != combat ||
      !ReadContactIdArray(
          side, kCombatSideArmyIdsOffset, kCombatSideArmyCountOffset,
          kMaximumActualContactSideArmies, native_ids, false) ||
      native_ids.empty()) {
    return false;
  }
  public_unit_ids.reserve(native_ids.size());
  for (const auto native_id : native_ids) {
    void *const army = ResolveStoredComponent(
        bindings.army_internal_storage_slot, native_id,
        kInternalArmyIdOffset);
    if (army == nullptr ||
        LoadAt<std::int32_t>(army, kInternalArmyCombatIdOffset) !=
            expected_combat_id) {
      native_ids.clear();
      public_unit_ids.clear();
      return false;
    }
    const auto unit_id =
        LoadAt<std::int32_t>(army, kInternalArmyUnitIdOffset);
    void *const unit = ResolveStoredComponent(
        bindings.army_storage_slot, unit_id, kArmyIdOffset);
    if (unit == nullptr ||
        LoadAt<std::int32_t>(unit, kUnitArmyIdOffset) != native_id ||
        std::find(public_unit_ids.begin(), public_unit_ids.end(), unit_id) !=
            public_unit_ids.end()) {
      native_ids.clear();
      public_unit_ids.clear();
      return false;
    }
    public_unit_ids.push_back(unit_id);
  }
  return true;
}

struct ActiveCombatIdentityV1 {
  std::int32_t combat_id = -1;
  std::int32_t province_id = -1;
  std::int32_t selected_combat_array_index = -1;
  bool finalized = false;
  std::vector<std::int32_t> province_public_cunit_ids;
  std::vector<std::int32_t> province_combat_ids;
  std::vector<std::int32_t> attacker_native_carmy_ids;
  std::vector<std::int32_t> attacker_public_cunit_ids;
  std::vector<std::int32_t> defender_native_carmy_ids;
  std::vector<std::int32_t> defender_public_cunit_ids;

  friend bool operator==(const ActiveCombatIdentityV1 &,
                         const ActiveCombatIdentityV1 &) = default;
};

bool ReadActiveCombatIdentityV1(
    const Bindings &bindings, void *game_state, void *subject_unit,
    void *subject_native_army, void *expected_province,
    std::int32_t expected_subject_public_cunit_id, bool require_not_finalized,
    ActiveCombatIdentityV1 &output) noexcept {
  output = {};
  const auto combat_id = LoadAt<std::int32_t>(
      subject_native_army, kInternalArmyCombatIdOffset);
  if (combat_id <= 0) {
    return false;
  }
  void *const combat = ResolveStoredComponent(
      bindings.combat_storage_slot, combat_id, kCombatIdOffset);
  if (combat == nullptr) {
    return false;
  }
  const bool finalized =
      LoadAt<std::uint8_t>(combat, kCombatFinalizedOffset) != 0;
  if (require_not_finalized && finalized) {
    return false;
  }
  void *const actual_province =
      LoadAt<void *>(combat, kCombatProvinceOffset);
  if (actual_province == nullptr || actual_province != expected_province ||
      LoadAt<void *>(subject_unit, kArmyCurrentProvinceOffset) !=
          actual_province) {
    return false;
  }
  const auto province_id =
      LoadAt<std::int32_t>(actual_province, kProvinceIdOffset);
  if (province_id <= 0 ||
      ResolveProvince(game_state, province_id) != actual_province) {
    return false;
  }
  if (!ReadContactIdArray(
          actual_province, kProvinceUnitIdsOffset,
          kProvinceUnitIdCountOffset, kMaximumActualContactProvinceUnits,
          output.province_public_cunit_ids, true) ||
      !ReadContactIdArray(
          actual_province, kProvinceCombatIdsOffset,
          kProvinceCombatIdCountOffset,
          kMaximumActualContactProvinceCombats,
          output.province_combat_ids, true) ||
      !std::binary_search(output.province_public_cunit_ids.begin(),
                          output.province_public_cunit_ids.end(),
                          expected_subject_public_cunit_id)) {
    return false;
  }
  const auto selected = std::lower_bound(output.province_combat_ids.begin(),
                                         output.province_combat_ids.end(),
                                         combat_id);
  if (selected == output.province_combat_ids.end() ||
      *selected != combat_id ||
      !ReadActiveCombatSideIds(
          bindings, combat, kCombatAttackerSideOffset, combat_id,
          output.attacker_native_carmy_ids,
          output.attacker_public_cunit_ids) ||
      !ReadActiveCombatSideIds(
          bindings, combat, kCombatDefenderSideOffset, combat_id,
          output.defender_native_carmy_ids,
          output.defender_public_cunit_ids)) {
    return false;
  }
  const auto attacker_subject_count = static_cast<std::size_t>(std::count(
      output.attacker_public_cunit_ids.begin(),
      output.attacker_public_cunit_ids.end(),
      expected_subject_public_cunit_id));
  const auto defender_subject_count = static_cast<std::size_t>(std::count(
      output.defender_public_cunit_ids.begin(),
      output.defender_public_cunit_ids.end(),
      expected_subject_public_cunit_id));
  if (attacker_subject_count + defender_subject_count != 1) {
    return false;
  }
  for (const auto attacker_id : output.attacker_public_cunit_ids) {
    if (std::find(output.defender_public_cunit_ids.begin(),
                  output.defender_public_cunit_ids.end(), attacker_id) !=
        output.defender_public_cunit_ids.end()) {
      return false;
    }
  }
  if (ResolveStoredComponent(bindings.combat_storage_slot, combat_id,
                             kCombatIdOffset) != combat ||
      LoadAt<std::int32_t>(subject_native_army,
                           kInternalArmyCombatIdOffset) != combat_id) {
    return false;
  }
  output.combat_id = combat_id;
  output.province_id = province_id;
  output.selected_combat_array_index = static_cast<std::int32_t>(
      std::distance(output.province_combat_ids.begin(), selected));
  output.finalized = finalized;
  return true;
}

ActualContactScopeStatus ReadExistingActualContact(
    const Bindings &bindings, void *game_state, void *unit,
    void *native_army, void *requested_province,
    const game::ActualContactScopeRequest &request,
    game::ActualContactScopeSnapshot &output) noexcept {
  ActiveCombatIdentityV1 identity{};
  if (!ReadActiveCombatIdentityV1(
          bindings, game_state, unit, native_army, requested_province,
          request.subject_army_id, true, identity) ||
      identity.province_id != request.target_province_id) {
    return ActualContactScopeStatus::state_changed;
  }
  output.target_province_id = identity.province_id;
  output.province_unit_army_ids =
      std::move(identity.province_public_cunit_ids);
  output.province_combat_ids = std::move(identity.province_combat_ids);
  output.attacker_army_ids =
      std::move(identity.attacker_public_cunit_ids);
  output.defender_army_ids =
      std::move(identity.defender_public_cunit_ids);
  output.scope_kind = "post_contact_observation";
  output.transition_kind = "in_combat";
  output.selected_combat_id = identity.combat_id;
  output.selected_combat_array_index =
      identity.selected_combat_array_index;
  output.actual_contact_scope_ready = true;
  output.combat_v3_participant_scope_ready = true;
  return ActualContactScopeStatus::available;
}

bool HasPositiveContactSoldiers(const Bindings &bindings, void *army,
                                bool &positive) noexcept {
  positive = false;
  std::vector<std::int32_t> regiment_ids;
  if (!ReadContactIdArray(army, kInternalArmyRegimentIdsOffset,
                          kInternalArmyRegimentCountOffset,
                          kMaximumActualContactRegiments, regiment_ids,
                          false)) {
    return false;
  }
  std::int64_t total = 0;
  for (const auto regiment_id : regiment_ids) {
    void *const regiment = ResolveStoredComponent(
        bindings.regiment_storage_slot, regiment_id, kRegimentIdOffset);
    if (regiment == nullptr) {
      return false;
    }
    bool identity_valid = false;
    if (!ReadRegimentIdentity(regiment, identity_valid)) {
      return false;
    }
    if (!identity_valid) {
      continue;
    }
    const auto soldiers =
        LoadAt<std::int32_t>(regiment, kRegimentCurrentSoldiersOffset);
    if (soldiers < 0 ||
        total > std::numeric_limits<std::int32_t>::max() - soldiers) {
      return false;
    }
    total += soldiers;
  }
  positive = total > 0;
  return true;
}

bool AppendLoserExclusions(const Bindings &bindings, void *combat,
                           std::vector<std::int32_t> &output) noexcept {
  const auto battle_result_id =
      LoadAt<std::int32_t>(combat, kCombatBattleResultIdOffset);
  void *const battle_result = ResolveStoredComponent(
      bindings.battle_result_storage_slot, battle_result_id,
      kBattleResultIdOffset);
  if (battle_result == nullptr) {
    return true;
  }
  bool identity_valid = false;
  if (!ReadSubobjectPredicate(battle_result, 0, identity_valid)) {
    return false;
  }
  if (!identity_valid) {
    return true;
  }
  const auto winner = LoadAt<std::int32_t>(combat, kCombatWinnerOffset);
  if (LoadAt<std::uint8_t>(battle_result, kBattleResultReadyOffset) == 0 ||
      winner == -1) {
    return true;
  }
  const auto loser_side = winner == 0 ? kCombatDefenderSideOffset
                                      : kCombatAttackerSideOffset;
  std::vector<std::int32_t> loser_ids;
  const auto *const side = static_cast<const std::byte *>(combat) + loser_side;
  if (!ReadContactIdArray(side, kCombatSideArmyIdsOffset,
                          kCombatSideArmyCountOffset,
                          kMaximumActualContactSideArmies, loser_ids,
                          false)) {
    return false;
  }
  output.insert(output.end(), loser_ids.begin(), loser_ids.end());
  return true;
}

bool ReadContactAdjacencyKind(void *unit, std::int32_t &kind) noexcept {
  kind = 0;
  void *const current = LoadAt<void *>(unit, kArmyCurrentProvinceOffset);
  void *const prior = LoadAt<void *>(unit, kArmyTargetProvinceOffset);
  if (current == nullptr || prior == nullptr) {
    return true;
  }
  bool current_valid = false;
  bool prior_valid = false;
  if (!ReadObjectPredicateAtSlot(current, 0x30, current_valid) ||
      !ReadObjectPredicateAtSlot(prior, 0x30, prior_valid)) {
    return false;
  }
  if (!current_valid || !prior_valid) {
    return true;
  }
  void *const map_node = LoadAt<void *>(current, kProvinceMapNodeOffset);
  if (map_node == nullptr) {
    return false;
  }
  void *const rows = LoadAt<void *>(map_node, kMapNodeAdjacencyDataOffset);
  const auto count =
      LoadAt<std::int32_t>(map_node, kMapNodeAdjacencyCountOffset);
  if (count < 0 || count > kMaximumProvinceAdjacencies ||
      (count > 0 && rows == nullptr)) {
    return false;
  }
  const auto prior_id = LoadAt<std::int32_t>(prior, kProvinceIdOffset);
  for (std::int32_t index = 0; index < count; ++index) {
    const auto *const row = static_cast<const std::byte *>(rows) +
                            static_cast<std::size_t>(index) *
                                kMapAdjacencyStride;
    if (LoadAt<std::int32_t>(row,
                             kMapAdjacencyTargetProvinceIdOffset) == prior_id) {
      kind = LoadAt<std::int32_t>(row, kMapAdjacencyKindOffset);
      return true;
    }
  }
  return true;
}

ActualContactScopeStatus ReadActualContactScopeSample(
    const Bindings &bindings, const game::ActualContactScopeRequest &request,
    game::ActualContactScopeSnapshot &output) noexcept {
  output = {};
  output.subject_army_id = request.subject_army_id;
  output.target_province_id = request.target_province_id;
  void *const game_state = *bindings.game_state_slot;
  void *const unit = ResolveStoredComponent(
      bindings.army_storage_slot, request.subject_army_id, kArmyIdOffset);
  if (unit == nullptr) {
    return ActualContactScopeStatus::subject_army_not_found;
  }
  void *const province =
      ResolveProvince(game_state, request.target_province_id);
  if (province == nullptr) {
    return ActualContactScopeStatus::target_province_not_found;
  }
  if (LoadAt<void *>(unit, kArmyCurrentProvinceOffset) != province) {
    return ActualContactScopeStatus::subject_not_at_target;
  }
  const auto native_army_id =
      LoadAt<std::int32_t>(unit, kUnitArmyIdOffset);
  void *const native_army = ResolveStoredComponent(
      bindings.army_internal_storage_slot, native_army_id,
      kInternalArmyIdOffset);
  if (native_army == nullptr ||
      LoadAt<std::int32_t>(native_army, kInternalArmyUnitIdOffset) !=
          request.subject_army_id) {
    return ActualContactScopeStatus::state_changed;
  }
  const auto owner_id =
      LoadAt<std::int32_t>(unit, kArmyOwnerCharacterIdOffset);
  void *owner = nullptr;
  if (!ResolveContactCharacter(bindings, owner_id, owner)) {
    return ActualContactScopeStatus::entry_rejected;
  }
  output.subject_native_carmy_id = native_army_id;
  output.subject_owner_character_id = owner_id;

  const bool subject_in_combat = bindings.is_army_in_combat(native_army);
  if (subject_in_combat) {
    return ReadExistingActualContact(
        bindings, game_state, unit, native_army, province, request, output);
  }

  void *const province_gate =
      LoadAt<void *>(province, kProvinceContactGatePointerOffset);
  void *const mode_root = *bindings.contact_game_mode_slot;
  void *const mode = mode_root == nullptr
                         ? nullptr
                         : LoadAt<void *>(mode_root, 0x1C0);
  if (province_gate == nullptr ||
      LoadAt<std::uint8_t>(province_gate, 0x1B) == 0 || mode == nullptr ||
      LoadAt<std::uint8_t>(mode, 0x28) != 0 ||
      LoadAt<std::int32_t>(unit, 0x18) != 0 ||
      LoadAt<std::int32_t>(unit, kUnitRetreatStateOffset) > 0 ||
      bindings.is_army_empty_for_contact(native_army)) {
    return ActualContactScopeStatus::entry_rejected;
  }

  if (!ReadContactIdArray(
          province, kProvinceUnitIdsOffset, kProvinceUnitIdCountOffset,
          kMaximumActualContactProvinceUnits,
          output.province_unit_army_ids, true) ||
      !ReadContactIdArray(
          province, kProvinceCombatIdsOffset, kProvinceCombatIdCountOffset,
          kMaximumActualContactProvinceCombats,
          output.province_combat_ids, true) ||
      !std::binary_search(output.province_unit_army_ids.begin(),
                          output.province_unit_army_ids.end(),
                          request.subject_army_id)) {
    return ActualContactScopeStatus::state_changed;
  }

  void *selected_combat = nullptr;
  for (std::size_t index = 0; index < output.province_combat_ids.size();
       ++index) {
    const auto combat_id = output.province_combat_ids[index];
    void *const combat = ResolveStoredComponent(
        bindings.combat_storage_slot, combat_id, kCombatIdOffset);
    if (combat == nullptr ||
        LoadAt<void *>(combat, kCombatProvinceOffset) != province) {
      return ActualContactScopeStatus::state_changed;
    }
    bool compatible = false;
    if (LoadAt<std::uint8_t>(combat, kCombatFinalizedOffset) == 0) {
      const auto attacker_primary_id = LoadAt<std::int32_t>(
          combat, kCombatAttackerSideOffset +
                      kCombatSidePrimaryCharacterIdOffset);
      const auto defender_primary_id = LoadAt<std::int32_t>(
          combat, kCombatDefenderSideOffset +
                      kCombatSidePrimaryCharacterIdOffset);
      void *attacker_primary = nullptr;
      void *defender_primary = nullptr;
      if (!ResolveContactCharacter(bindings, attacker_primary_id,
                                   attacker_primary) ||
          !ResolveContactCharacter(bindings, defender_primary_id,
                                   defender_primary)) {
        return ActualContactScopeStatus::relation_unavailable;
      }
      const bool hostile_to_attacker =
          bindings.is_character_hostile(owner, attacker_primary, false);
      const bool hostile_to_defender =
          bindings.is_character_hostile(owner, defender_primary, false);
      compatible = hostile_to_attacker != hostile_to_defender;
    }
    if (compatible) {
      selected_combat = combat;
      output.selected_combat_id = combat_id;
      output.selected_combat_array_index =
          static_cast<std::int32_t>(index);
      continue;
    }
    if (selected_combat == nullptr &&
        !AppendLoserExclusions(
            bindings, combat,
            output.loser_excluded_native_carmy_ids)) {
      return ActualContactScopeStatus::state_changed;
    }
  }

  if (selected_combat != nullptr) {
    const auto attacker_primary_id = LoadAt<std::int32_t>(
        selected_combat, kCombatAttackerSideOffset +
                             kCombatSidePrimaryCharacterIdOffset);
    const auto defender_primary_id = LoadAt<std::int32_t>(
        selected_combat, kCombatDefenderSideOffset +
                             kCombatSidePrimaryCharacterIdOffset);
    void *attacker_primary = nullptr;
    void *defender_primary = nullptr;
    if (!ResolveContactCharacter(bindings, attacker_primary_id,
                                 attacker_primary) ||
        !ResolveContactCharacter(bindings, defender_primary_id,
                                 defender_primary)) {
      return ActualContactScopeStatus::relation_unavailable;
    }
    const bool joins_defender =
        bindings.is_character_hostile(attacker_primary, owner, false);
    const bool joins_attacker =
        bindings.is_character_hostile(defender_primary, owner, false);
    if (joins_defender == joins_attacker ||
        !ReadCombatSidePublicUnitIds(bindings, selected_combat,
                                     kCombatAttackerSideOffset,
                                     output.attacker_army_ids) ||
        !ReadCombatSidePublicUnitIds(bindings, selected_combat,
                                     kCombatDefenderSideOffset,
                                     output.defender_army_ids)) {
      return ActualContactScopeStatus::relation_unavailable;
    }
    auto &joined_side = joins_defender ? output.defender_army_ids
                                       : output.attacker_army_ids;
    if (std::find(joined_side.begin(), joined_side.end(),
                  request.subject_army_id) == joined_side.end()) {
      joined_side.push_back(request.subject_army_id);
    }
    output.transition_kind = "join_existing";
    output.join_side = joins_defender ? "defender" : "attacker";
    output.actual_contact_scope_ready = true;
    output.combat_v3_participant_scope_ready = true;
    return ActualContactScopeStatus::available;
  }

  std::vector<std::int32_t> opponent_native_army_ids;
  for (const auto candidate_unit_id : output.province_unit_army_ids) {
    void *const candidate_unit = ResolveStoredComponent(
        bindings.army_storage_slot, candidate_unit_id, kArmyIdOffset);
    if (candidate_unit == nullptr) {
      return ActualContactScopeStatus::state_changed;
    }
    const auto candidate_owner_id = LoadAt<std::int32_t>(
        candidate_unit, kArmyOwnerCharacterIdOffset);
    if (candidate_owner_id == owner_id ||
        LoadAt<std::int32_t>(candidate_unit, 0x18) != 0 ||
        LoadAt<std::int32_t>(candidate_unit, kUnitRetreatStateOffset) > 0) {
      continue;
    }
    const auto candidate_native_id = LoadAt<std::int32_t>(
        candidate_unit, kUnitArmyIdOffset);
    void *const candidate_army = ResolveStoredComponent(
        bindings.army_internal_storage_slot, candidate_native_id,
        kInternalArmyIdOffset);
    if (candidate_army == nullptr) {
      return ActualContactScopeStatus::state_changed;
    }
    if (bindings.is_army_empty_for_contact(candidate_army) ||
        bindings.is_army_in_combat(candidate_army) ||
        std::find(output.loser_excluded_native_carmy_ids.begin(),
                  output.loser_excluded_native_carmy_ids.end(),
                  candidate_native_id) !=
            output.loser_excluded_native_carmy_ids.end()) {
      continue;
    }
    void *candidate_owner = nullptr;
    if (!ResolveContactCharacter(bindings, candidate_owner_id,
                                 candidate_owner)) {
      return ActualContactScopeStatus::relation_unavailable;
    }
    if (bindings.is_character_hostile(owner, candidate_owner, false)) {
      output.defender_seed_character_id = candidate_owner_id;
      break;
    }
  }
  if (output.defender_seed_character_id == -1) {
    output.actual_contact_scope_ready = true;
    return ActualContactScopeStatus::available;
  }
  bool positive_soldiers = false;
  if (!HasPositiveContactSoldiers(bindings, native_army,
                                  positive_soldiers)) {
    return ActualContactScopeStatus::state_changed;
  }
  if (!positive_soldiers) {
    // The hostile seed is only part of a create-new projection.  Native stops
    // before construction when the initiator has no positive regiment
    // strength, so do not expose the intermediate scan candidate as a
    // transition participant.
    output.defender_seed_character_id = -1;
    output.actual_contact_scope_ready = true;
    return ActualContactScopeStatus::available;
  }

  for (const auto candidate_unit_id : output.province_unit_army_ids) {
    void *const candidate_unit = ResolveStoredComponent(
        bindings.army_storage_slot, candidate_unit_id, kArmyIdOffset);
    if (candidate_unit == nullptr) {
      return ActualContactScopeStatus::state_changed;
    }
    if (LoadAt<std::int32_t>(candidate_unit, 0x18) != 0 ||
        LoadAt<std::int32_t>(candidate_unit, kUnitRetreatStateOffset) > 0) {
      continue;
    }
    const auto candidate_native_id = LoadAt<std::int32_t>(
        candidate_unit, kUnitArmyIdOffset);
    void *const candidate_army = ResolveStoredComponent(
        bindings.army_internal_storage_slot, candidate_native_id,
        kInternalArmyIdOffset);
    if (candidate_army == nullptr) {
      return ActualContactScopeStatus::state_changed;
    }
    if (bindings.is_army_empty_for_contact(candidate_army) ||
        bindings.is_army_in_combat(candidate_army)) {
      continue;
    }
    const auto candidate_owner_id = LoadAt<std::int32_t>(
        candidate_unit, kArmyOwnerCharacterIdOffset);
    void *candidate_owner = nullptr;
    if (!ResolveContactCharacter(bindings, candidate_owner_id,
                                 candidate_owner)) {
      return ActualContactScopeStatus::relation_unavailable;
    }
    if (candidate_owner_id == output.defender_seed_character_id ||
        bindings.is_character_hostile(candidate_owner, owner, false)) {
      if (LoadAt<std::int32_t>(candidate_army,
                               kInternalArmyUnitIdOffset) !=
          candidate_unit_id) {
        return ActualContactScopeStatus::state_changed;
      }
      opponent_native_army_ids.push_back(candidate_native_id);
      output.opponent_army_ids.push_back(candidate_unit_id);
    }
  }
  if (output.opponent_army_ids.empty()) {
    return ActualContactScopeStatus::state_changed;
  }

  bool initiator_is_defender = false;
  if (LoadAt<std::int32_t>(province, kProvinceFortLevelOffset) > 0) {
    std::int32_t holder_id = -1;
    if (bindings.read_province_holder_character_id(province, &holder_id) !=
        &holder_id) {
      return ActualContactScopeStatus::relation_unavailable;
    }
    if (holder_id != -1) {
      void *holder = nullptr;
      if (!ResolveContactCharacter(bindings, holder_id, holder)) {
        return ActualContactScopeStatus::relation_unavailable;
      }
      initiator_is_defender =
          bindings.classify_contact_defender_by_holder(owner, holder);
    }
  }
  if (!initiator_is_defender) {
    initiator_is_defender =
        bindings.classify_contact_defender_fallback(owner, province);
  }
  output.initiator_is_defender = initiator_is_defender;
  if (!ReadContactAdjacencyKind(unit, output.adjacency_kind_raw)) {
    return ActualContactScopeStatus::state_changed;
  }
  std::vector<std::int32_t> unique_opponent_native_army_ids;
  unique_opponent_native_army_ids.reserve(opponent_native_army_ids.size());
  for (const auto opponent_native_id : opponent_native_army_ids) {
    if (std::find(unique_opponent_native_army_ids.begin(),
                  unique_opponent_native_army_ids.end(),
                  opponent_native_id) ==
        unique_opponent_native_army_ids.end()) {
      unique_opponent_native_army_ids.push_back(opponent_native_id);
    }
  }
  std::vector<std::int32_t> unique_opponent_army_ids;
  if (!NativeArmyIdsToPublicUnitIds(bindings,
                                    unique_opponent_native_army_ids,
                                    unique_opponent_army_ids)) {
    return ActualContactScopeStatus::state_changed;
  }
  if (initiator_is_defender) {
    output.attacker_army_ids = std::move(unique_opponent_army_ids);
    output.defender_army_ids = {request.subject_army_id};
  } else {
    output.attacker_army_ids = {request.subject_army_id};
    output.defender_army_ids = std::move(unique_opponent_army_ids);
  }
  output.transition_kind = "create_new";
  output.actual_contact_scope_ready = true;
  output.combat_v3_participant_scope_ready = true;
  return ActualContactScopeStatus::available;
}

struct BattleControlArrayHeaderV1 {
  void *data = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
};

bool ReadBattleControlArrayHeader(
    const void *owner, std::size_t data_offset, std::size_t capacity_offset,
    std::size_t count_offset, std::int32_t maximum,
    BattleControlArrayHeaderV1 &output) noexcept {
  output.data = LoadAt<void *>(owner, data_offset);
  output.capacity = LoadAt<std::int32_t>(owner, capacity_offset);
  output.count = LoadAt<std::int32_t>(owner, count_offset);
  return output.capacity >= 0 && output.capacity <= maximum &&
         output.count >= 0 && output.count <= output.capacity &&
         (output.count == 0 || output.data != nullptr);
}

bool BattleControlArrayHeaderUnchanged(
    const void *owner, std::size_t data_offset, std::size_t capacity_offset,
    std::size_t count_offset,
    const BattleControlArrayHeaderV1 &expected) noexcept {
  return LoadAt<void *>(owner, data_offset) == expected.data &&
         LoadAt<std::int32_t>(owner, capacity_offset) == expected.capacity &&
         LoadAt<std::int32_t>(owner, count_offset) == expected.count;
}

struct BattleReinforcementAssignmentSampleV1 {
  game::BattleReinforcementAssignmentSnapshot value;
  std::vector<std::uintptr_t> structural_proof;

  friend bool operator==(
      const BattleReinforcementAssignmentSampleV1 &,
      const BattleReinforcementAssignmentSampleV1 &) = default;
};

void AppendBattleReinforcementProof(
    BattleReinforcementAssignmentSampleV1 &sample,
    const void *pointer) {
  sample.structural_proof.push_back(
      reinterpret_cast<std::uintptr_t>(pointer));
}

void AppendBattleReinforcementProof(
    BattleReinforcementAssignmentSampleV1 &sample,
    const BattleControlArrayHeaderV1 &header) {
  AppendBattleReinforcementProof(sample, header.data);
  sample.structural_proof.push_back(
      static_cast<std::uintptr_t>(
          static_cast<std::uint32_t>(header.capacity)));
  sample.structural_proof.push_back(
      static_cast<std::uintptr_t>(
          static_cast<std::uint32_t>(header.count)));
}

bool ReadBattleReinforcementPublicIds(
    const Bindings &bindings, const void *subunit,
    BattleReinforcementAssignmentSampleV1 &sample,
    std::vector<std::int32_t> &output) noexcept {
  output.clear();
  BattleControlArrayHeaderV1 header{};
  if (!ReadBattleControlArrayHeader(
          subunit, kAiSubunitPublicCunitIdsOffset,
          kAiSubunitPublicCunitIdsCapacityOffset,
          kAiSubunitPublicCunitIdsCountOffset,
          kMaximumAiSubunitPublicCunitIds, header)) {
    return false;
  }
  AppendBattleReinforcementProof(sample, header);
  output.reserve(static_cast<std::size_t>(header.count));
  for (std::int32_t index = 0; index < header.count; ++index) {
    const auto public_cunit_id = LoadAt<std::int32_t>(
        header.data,
        static_cast<std::size_t>(index) * sizeof(std::int32_t));
    void *const unit = ResolveStoredComponent(
        bindings.army_storage_slot, public_cunit_id, kArmyIdOffset);
    if (public_cunit_id <= 0 || unit == nullptr ||
        LoadAt<void *>(unit, kUnitAiSubunitStackOffset) != subunit ||
        std::find(output.begin(), output.end(), public_cunit_id) !=
            output.end()) {
      output.clear();
      return false;
    }
    output.push_back(public_cunit_id);
  }
  return BattleControlArrayHeaderUnchanged(
      subunit, kAiSubunitPublicCunitIdsOffset,
      kAiSubunitPublicCunitIdsCapacityOffset,
      kAiSubunitPublicCunitIdsCountOffset, header);
}

bool ReadBattleReinforcementAssignmentTarget(
    void *game_state, const void *subunit, bool assigned,
    std::optional<std::int32_t> &output,
    BattleReinforcementAssignmentSampleV1 &sample) noexcept {
  output.reset();
  void *const target =
      LoadAt<void *>(subunit, kAiSubunitAssignmentTargetOffset);
  AppendBattleReinforcementProof(sample, target);
  if (!assigned) {
    return true;
  }
  if (target == nullptr) {
    return false;
  }
  const auto target_id =
      LoadAt<std::int32_t>(target, kProvinceIdOffset);
  if (target_id <= 0 || ResolveProvince(game_state, target_id) != target) {
    return false;
  }
  output = target_id;
  return true;
}

bool ReadBattleReinforcementParentOrder(
    const Bindings &bindings, void *game_state, void *parent,
    void *selected_subunit,
    BattleReinforcementAssignmentSampleV1 &sample,
    std::int32_t &selected_subunit_index) noexcept {
  auto &native_order = *sample.value.native_order;
  selected_subunit_index = -1;

  BattleControlArrayHeaderV1 support_header{};
  if (!ReadBattleControlArrayHeader(
          parent, kAiUnitStackSupportProvincesOffset,
          kAiUnitStackSupportProvincesCapacityOffset,
          kAiUnitStackSupportProvincesCountOffset,
          kMaximumAiSupportSearchProvinces, support_header)) {
    return false;
  }
  AppendBattleReinforcementProof(sample, support_header);
  native_order.support_search_province_ids_in_stored_order.reserve(
      static_cast<std::size_t>(support_header.count));
  for (std::int32_t index = 0; index < support_header.count; ++index) {
    void *const province = LoadAt<void *>(
        support_header.data,
        static_cast<std::size_t>(index) * sizeof(void *));
    if (province == nullptr) {
      return false;
    }
    const auto province_id =
        LoadAt<std::int32_t>(province, kProvinceIdOffset);
    if (province_id <= 0 ||
        ResolveProvince(game_state, province_id) != province) {
      return false;
    }
    AppendBattleReinforcementProof(sample, province);
    native_order.support_search_province_ids_in_stored_order.push_back(
        province_id);
  }
  if (!BattleControlArrayHeaderUnchanged(
          parent, kAiUnitStackSupportProvincesOffset,
          kAiUnitStackSupportProvincesCapacityOffset,
          kAiUnitStackSupportProvincesCountOffset, support_header)) {
    return false;
  }

  BattleControlArrayHeaderV1 parent_cunit_header{};
  if (!ReadBattleControlArrayHeader(
          parent, kAiUnitStackPublicCunitIdsOffset,
          kAiUnitStackPublicCunitIdsCapacityOffset,
          kAiUnitStackPublicCunitIdsCountOffset,
          kMaximumAiSubunitPublicCunitIds, parent_cunit_header)) {
    return false;
  }
  AppendBattleReinforcementProof(sample, parent_cunit_header);
  for (std::int32_t index = 0; index < parent_cunit_header.count; ++index) {
    const auto public_cunit_id = LoadAt<std::int32_t>(
        parent_cunit_header.data,
        static_cast<std::size_t>(index) * sizeof(std::int32_t));
    if (public_cunit_id <= 0 ||
        ResolveStoredComponent(bindings.army_storage_slot,
                               public_cunit_id,
                               kArmyIdOffset) == nullptr) {
      return false;
    }
    sample.structural_proof.push_back(
        static_cast<std::uintptr_t>(
            static_cast<std::uint32_t>(public_cunit_id)));
  }
  if (!BattleControlArrayHeaderUnchanged(
          parent, kAiUnitStackPublicCunitIdsOffset,
          kAiUnitStackPublicCunitIdsCapacityOffset,
          kAiUnitStackPublicCunitIdsCountOffset, parent_cunit_header)) {
    return false;
  }

  BattleControlArrayHeaderV1 subunit_header{};
  if (!ReadBattleControlArrayHeader(
          parent, kAiUnitStackSubunitsOffset,
          kAiUnitStackSubunitsCapacityOffset,
          kAiUnitStackSubunitsCountOffset,
          kMaximumAiUnitStackSubunits, subunit_header)) {
    return false;
  }
  AppendBattleReinforcementProof(sample, subunit_header);
  native_order.parent_subunits_in_stored_order.reserve(
      static_cast<std::size_t>(subunit_header.count));
  for (std::int32_t index = 0; index < subunit_header.count; ++index) {
    void *const subunit = LoadAt<void *>(
        subunit_header.data,
        static_cast<std::size_t>(index) * sizeof(void *));
    if (subunit == nullptr ||
        LoadAt<std::uintptr_t>(subunit, 0) !=
            bindings.ai_subunit_stack_vtable ||
        LoadAt<void *>(subunit, kAiSubunitParentOffset) != parent) {
      return false;
    }
    AppendBattleReinforcementProof(sample, subunit);
    if (subunit == selected_subunit) {
      if (selected_subunit_index != -1) {
        return false;
      }
      selected_subunit_index = index;
    }
    game::BattleReinforcementParentSubunitSnapshot row{};
    if (!ReadBattleReinforcementPublicIds(bindings, subunit, sample,
                                           row.public_cunit_ids_in_stored_order)) {
      return false;
    }
    const auto flags =
        LoadAt<std::uint8_t>(subunit, kAiSubunitFlagsOffset);
    sample.structural_proof.push_back(flags);
    row.asking_for_help = (flags & 0x01U) != 0;
    row.assigned_to_help = (flags & 0x02U) != 0;
    if (!ReadBattleReinforcementAssignmentTarget(
            game_state, subunit, row.assigned_to_help,
            row.assignment_target_province_id, sample)) {
      return false;
    }
    native_order.parent_subunits_in_stored_order.push_back(
        std::move(row));
  }
  return selected_subunit_index >= 0 &&
         BattleControlArrayHeaderUnchanged(
             parent, kAiUnitStackSubunitsOffset,
             kAiUnitStackSubunitsCapacityOffset,
             kAiUnitStackSubunitsCountOffset, subunit_header);
}

bool ReadBattleReinforcementRoute(
    const Bindings &bindings, void *game_state, void *unit,
    std::int32_t observed_date_raw,
    const std::optional<std::int32_t> &assignment_target,
    game::BattleReinforcementSignalSnapshot &signal,
    game::BattleReinforcementRouteSnapshot &route,
    BattleReinforcementAssignmentSampleV1 &sample) noexcept {
  void *const current_province =
      LoadAt<void *>(unit, kArmyCurrentProvinceOffset);
  if (current_province == nullptr) {
    return false;
  }
  route.current_province_id =
      LoadAt<std::int32_t>(current_province, kProvinceIdOffset);
  if (route.current_province_id <= 0 ||
      ResolveProvince(game_state, route.current_province_id) !=
          current_province) {
    return false;
  }
  AppendBattleReinforcementProof(sample, current_province);

  void *const move_target =
      LoadAt<void *>(unit, kArmyTargetProvinceOffset);
  AppendBattleReinforcementProof(sample, move_target);
  if (move_target != nullptr) {
    const auto move_target_id =
        LoadAt<std::int32_t>(move_target, kProvinceIdOffset);
    if (move_target_id <= 0 ||
        ResolveProvince(game_state, move_target_id) != move_target) {
      return false;
    }
    route.move_target_province_id = move_target_id;
  }

  const auto *const path_storage =
      static_cast<const std::byte *>(unit) +
      kUnitPathProvinceInfosOffset;
  NativeMovePathPrefix path{};
  if (!ReadPathHeader(path_storage, path)) {
    return false;
  }
  BattleControlArrayHeaderV1 proof_header{
      path.province_infos, path.capacity, path.count};
  AppendBattleReinforcementProof(sample, proof_header);
  route.route_province_ids.reserve(static_cast<std::size_t>(path.count));
  for (std::int32_t index = 0; index < path.count; ++index) {
    void *const province_info = LoadAt<void *>(
        path.province_infos,
        static_cast<std::size_t>(index) * sizeof(void *));
    if (province_info == nullptr) {
      return false;
    }
    AppendBattleReinforcementProof(sample, province_info);
    const auto province_id = LoadAt<std::int32_t>(
        province_info, kUnitPathProvinceIdOffset);
    if (province_id <= 0 ||
        ResolveProvince(game_state, province_id) == nullptr) {
      return false;
    }
    route.route_province_ids.push_back(province_id);
  }

  std::vector<std::int32_t> projected_ids;
  std::vector<std::int32_t> arrivals;
  const bool timeline_available = ProjectPathTimeline(
      bindings, game_state, unit, path_storage, current_province,
      observed_date_raw, 0, projected_ids, arrivals) &&
      projected_ids == route.route_province_ids;
  if (timeline_available) {
    route.arrival_date_raws = arrivals;
  }

  const auto movement_state =
      LoadAt<std::int32_t>(unit, kUnitRetreatStateOffset);
  sample.structural_proof.push_back(
      static_cast<std::uintptr_t>(
          static_cast<std::uint32_t>(movement_state)));
  if (path.count > 0 && movement_state != 1 &&
      bindings.read_route_edge_duration != nullptr &&
      ValidateRouteTimingInputs(bindings, game_state, unit, path_storage,
                                current_province)) {
    std::int64_t first_edge_duration = -1;
    if (bindings.read_route_edge_duration(
            unit, &first_edge_duration, 0) == &first_edge_duration &&
        first_edge_duration >= 0 &&
        first_edge_duration != kRouteDurationFailureSentinel &&
        first_edge_duration <= kMaximumProjectedRouteDurationRaw) {
      signal.first_route_edge_remaining_duration_q100000 =
          first_edge_duration;
    }
  }

  if (!assignment_target.has_value()) {
    route.route_alignment = "no_assignment";
  } else {
    const bool aligned =
        route.move_target_province_id == assignment_target &&
        ((!route.route_province_ids.empty() &&
          route.route_province_ids.back() == *assignment_target) ||
         (route.route_province_ids.empty() &&
          route.current_province_id == *assignment_target));
    if (!aligned) {
      route.route_alignment = "not_aligned";
    } else if (!timeline_available) {
      route.route_alignment = "timeline_unavailable";
    } else {
      route.route_alignment = "aligned_to_assignment";
      route.assignment_eta_date_raw =
          arrivals.empty() ? observed_date_raw : arrivals.back();
    }
  }
  return ReadPathHeader(path_storage, path) &&
         path.province_infos == proof_header.data &&
         path.capacity == proof_header.capacity &&
         path.count == proof_header.count;
}

void ReadBattleReinforcementContactProjection(
    const Bindings &bindings, void *game_state, void *unit,
    const std::optional<std::int32_t> &assignment_target,
    game::BattleReinforcementContactProjectionSnapshot &output,
    BattleReinforcementAssignmentSampleV1 &sample) noexcept {
  output = {};
  if (!assignment_target.has_value()) {
    output.status = "not_applicable";
    return;
  }
  if (bindings.is_character_hostile == nullptr ||
      bindings.character_storage_slot == nullptr ||
      bindings.combat_storage_slot == nullptr) {
    output.status = "unavailable";
    return;
  }
  void *const province =
      ResolveProvince(game_state, *assignment_target);
  const auto owner_id =
      LoadAt<std::int32_t>(unit, kArmyOwnerCharacterIdOffset);
  void *owner = nullptr;
  if (province == nullptr ||
      !ResolveContactCharacter(bindings, owner_id, owner)) {
    output.status = "unavailable";
    return;
  }
  void *const combat_ids_data =
      LoadAt<void *>(province, kProvinceCombatIdsOffset);
  const auto combat_id_count =
      LoadAt<std::int32_t>(province, kProvinceCombatIdCountOffset);
  AppendBattleReinforcementProof(sample, combat_ids_data);
  sample.structural_proof.push_back(
      static_cast<std::uintptr_t>(
          static_cast<std::uint32_t>(combat_id_count)));
  std::vector<std::int32_t> combat_ids;
  if (!ReadContactIdArray(
          province, kProvinceCombatIdsOffset,
          kProvinceCombatIdCountOffset,
          kMaximumActualContactProvinceCombats, combat_ids, false)) {
    output.status = "unavailable";
    return;
  }
  for (const auto combat_id : combat_ids) {
    void *const combat = ResolveStoredComponent(
        bindings.combat_storage_slot, combat_id, kCombatIdOffset);
    if (combat == nullptr ||
        LoadAt<void *>(combat, kCombatProvinceOffset) != province) {
      output.status = "unavailable";
      output.current_target_compatible_combat_ids_in_stored_order.clear();
      output.contact_if_now_selected_combat_id.reset();
      return;
    }
    AppendBattleReinforcementProof(sample, combat);
    if (LoadAt<std::uint8_t>(combat,
                             kCombatFinalizedOffset) != 0) {
      continue;
    }
    const auto attacker_primary_id = LoadAt<std::int32_t>(
        combat, kCombatAttackerSideOffset +
                    kCombatSidePrimaryCharacterIdOffset);
    const auto defender_primary_id = LoadAt<std::int32_t>(
        combat, kCombatDefenderSideOffset +
                    kCombatSidePrimaryCharacterIdOffset);
    void *attacker_primary = nullptr;
    void *defender_primary = nullptr;
    if (!ResolveContactCharacter(bindings, attacker_primary_id,
                                 attacker_primary) ||
        !ResolveContactCharacter(bindings, defender_primary_id,
                                 defender_primary)) {
      output.status = "unavailable";
      output.current_target_compatible_combat_ids_in_stored_order.clear();
      output.contact_if_now_selected_combat_id.reset();
      return;
    }
    const bool hostile_to_attacker =
        bindings.is_character_hostile(owner, attacker_primary, false);
    const bool hostile_to_defender =
        bindings.is_character_hostile(owner, defender_primary, false);
    if (hostile_to_attacker != hostile_to_defender) {
      output.current_target_compatible_combat_ids_in_stored_order.push_back(
          combat_id);
    }
  }
  if (!output.current_target_compatible_combat_ids_in_stored_order.empty()) {
    output.contact_if_now_selected_combat_id =
        output.current_target_compatible_combat_ids_in_stored_order.back();
  }
  output.status = "available";
}

bool ReadBattleReinforcementAssignmentSampleV1(
    const Bindings &bindings, const game::Snapshot &same_frame_world,
    const game::BattleReinforcementAssignmentRequest &request,
    BattleReinforcementAssignmentSampleV1 &sample,
    std::string_view &failure_reason) noexcept {
  sample = {};
  failure_reason = "state_changed";
  auto &output = sample.value;
  output.selected_public_cunit_id = request.selected_public_cunit_id;
  output.observed_date_raw = same_frame_world.date_raw;
  void *const game_state = *bindings.game_state_slot;
  void *const unit = ResolveStoredComponent(
      bindings.army_storage_slot, request.selected_public_cunit_id,
      kArmyIdOffset);
  if (unit == nullptr) {
    failure_reason = "subject_cunit_not_found";
    return false;
  }
  AppendBattleReinforcementProof(sample, unit);

  void *const selected_subunit =
      LoadAt<void *>(unit, kUnitAiSubunitStackOffset);
  if (selected_subunit == nullptr) {
    failure_reason = "subject_not_ai_managed";
    return false;
  }
  if (LoadAt<std::uintptr_t>(selected_subunit, 0) !=
      bindings.ai_subunit_stack_vtable) {
    failure_reason = "subunit_backlink_mismatch";
    return false;
  }
  AppendBattleReinforcementProof(sample, selected_subunit);

  const auto coordinator_id =
      LoadAt<std::int32_t>(unit, kUnitAiWarCoordinatorIdOffset);
  void *const coordinator = ResolveStoredComponent(
      bindings.ai_war_coordinator_storage_slot, coordinator_id,
      kAiWarCoordinatorIdOffset);
  void *const fallback =
      *bindings.ai_war_coordinator_fallback_slot;
  if (coordinator_id <= 0 || coordinator == nullptr ||
      coordinator == fallback ||
      LoadAt<std::uintptr_t>(coordinator, 0) !=
          bindings.ai_war_coordinator_vtable) {
    failure_reason = "coordinator_generation_mismatch";
    return false;
  }
  AppendBattleReinforcementProof(sample, coordinator);
  output.coordinator_id = coordinator_id;

  void *const parent =
      LoadAt<void *>(selected_subunit, kAiSubunitParentOffset);
  if (parent == nullptr ||
      LoadAt<std::uintptr_t>(parent, 0) !=
          bindings.ai_unit_stack_vtable ||
      LoadAt<void *>(parent, kAiUnitStackCoordinatorOffset) !=
          coordinator) {
    failure_reason = "parent_membership_mismatch";
    return false;
  }
  AppendBattleReinforcementProof(sample, parent);

  BattleControlArrayHeaderV1 unit_stack_header{};
  if (!ReadBattleControlArrayHeader(
          coordinator, kAiWarCoordinatorUnitStacksOffset,
          kAiWarCoordinatorUnitStacksCapacityOffset,
          kAiWarCoordinatorUnitStacksCountOffset,
          kMaximumAiCoordinatorUnitStacks, unit_stack_header)) {
    failure_reason = "parent_membership_mismatch";
    return false;
  }
  AppendBattleReinforcementProof(sample, unit_stack_header);
  std::int32_t unit_stack_index = -1;
  for (std::int32_t index = 0; index < unit_stack_header.count; ++index) {
    void *const candidate = LoadAt<void *>(
        unit_stack_header.data,
        static_cast<std::size_t>(index) * sizeof(void *));
    if (candidate == parent) {
      if (unit_stack_index != -1) {
        failure_reason = "parent_membership_mismatch";
        return false;
      }
      unit_stack_index = index;
    }
  }
  if (unit_stack_index < 0 ||
      !BattleControlArrayHeaderUnchanged(
          coordinator, kAiWarCoordinatorUnitStacksOffset,
          kAiWarCoordinatorUnitStacksCapacityOffset,
          kAiWarCoordinatorUnitStacksCountOffset, unit_stack_header)) {
    failure_reason = "parent_membership_mismatch";
    return false;
  }
  output.unit_stack_stored_index = unit_stack_index;
  output.native_order.emplace();
  std::int32_t selected_subunit_index = -1;
  if (!ReadBattleReinforcementParentOrder(
          bindings, game_state, parent, selected_subunit, sample,
          selected_subunit_index)) {
    failure_reason = "parent_membership_mismatch";
    return false;
  }
  output.subunit_stored_index = selected_subunit_index;
  const auto &selected_ids =
      output.native_order
          ->parent_subunits_in_stored_order[
              static_cast<std::size_t>(selected_subunit_index)]
          .public_cunit_ids_in_stored_order;
  if (std::count(selected_ids.begin(), selected_ids.end(),
                 request.selected_public_cunit_id) != 1) {
    failure_reason = "subunit_backlink_mismatch";
    return false;
  }

  output.signal.emplace();
  auto &signal = *output.signal;
  const auto flags =
      LoadAt<std::uint8_t>(selected_subunit, kAiSubunitFlagsOffset);
  sample.structural_proof.push_back(flags);
  signal.asking_for_help = (flags & 0x01U) != 0;
  signal.assigned_to_help = (flags & 0x02U) != 0;
  signal.asking_changed_last_evaluation = (flags & 0x10U) != 0;
  if (signal.asking_for_help) {
    signal.request_power_basis_raw = LoadAt<std::int64_t>(
        selected_subunit, kAiSubunitRequestPowerBasisOffset);
  }
  signal.cross_coordinator_request_valid_raw = LoadAt<std::uint8_t>(
      selected_subunit, kAiSubunitCrossCoordinatorValidOffset);
  if (signal.cross_coordinator_request_valid_raw != 0) {
    signal.cross_coordinator_request_power_raw = LoadAt<std::int64_t>(
        selected_subunit, kAiSubunitCrossCoordinatorPowerOffset);
  }

  output.assignment.emplace();
  auto &assignment = *output.assignment;
  if (!ReadBattleReinforcementAssignmentTarget(
          game_state, selected_subunit, signal.assigned_to_help,
          assignment.assignment_target_province_id, sample)) {
    failure_reason = "subunit_backlink_mismatch";
    return false;
  }
  assignment.target_provenance =
      assignment.assignment_target_province_id.has_value()
          ? "native_help_override"
          : "none";

  const auto native_carmy_id =
      LoadAt<std::int32_t>(unit, kUnitArmyIdOffset);
  void *native_army = nullptr;
  if (native_carmy_id > 0) {
    native_army = ResolveStoredComponent(
        bindings.army_internal_storage_slot, native_carmy_id,
        kInternalArmyIdOffset);
    if (native_army == nullptr ||
        LoadAt<std::int32_t>(native_army,
                             kInternalArmyUnitIdOffset) !=
            request.selected_public_cunit_id) {
      return false;
    }
    output.selected_native_carmy_id = native_carmy_id;
    AppendBattleReinforcementProof(sample, native_army);
    const auto active_combat_id = LoadAt<std::int32_t>(
        native_army, kInternalArmyCombatIdOffset);
    if (active_combat_id > 0) {
      void *const active_combat = ResolveStoredComponent(
          bindings.combat_storage_slot, active_combat_id,
          kCombatIdOffset);
      if (active_combat == nullptr ||
          LoadAt<std::uint8_t>(active_combat,
                               kCombatFinalizedOffset) != 0) {
        return false;
      }
      assignment.active_combat_id = active_combat_id;
      assignment.combat_binding_status = "already_in_active_combat";
      AppendBattleReinforcementProof(sample, active_combat);
    } else if (active_combat_id != -1) {
      return false;
    }
  } else if (native_carmy_id != -1) {
    return false;
  }

  output.route.emplace();
  if (!ReadBattleReinforcementRoute(
          bindings, game_state, unit, same_frame_world.date_raw,
          assignment.assignment_target_province_id, signal,
          *output.route, sample)) {
    failure_reason = "route_timeline_unavailable";
    return false;
  }

  output.contact_projection.emplace();
  ReadBattleReinforcementContactProjection(
      bindings, game_state, unit,
      assignment.assignment_target_province_id,
      *output.contact_projection, sample);
  output.status =
      game::BattleReinforcementAssignmentStatus::available;
  output.battle_reinforcement_assignment_ready = true;
  failure_reason = {};
  return true;
}

bool BattleControlArmyContainsRegiment(void *army,
                                       std::int32_t regiment_id) noexcept {
  BattleControlArrayHeaderV1 header{};
  if (!ReadBattleControlArrayHeader(
          army, kInternalArmyRegimentIdsOffset,
          kInternalArmyRegimentCapacityOffset,
          kInternalArmyRegimentCountOffset,
          kMaximumActualContactRegiments, header)) {
    return false;
  }
  std::int32_t matches = 0;
  std::vector<std::int32_t> observed;
  observed.reserve(static_cast<std::size_t>(header.count));
  for (std::int32_t index = 0; index < header.count; ++index) {
    const auto candidate = LoadAt<std::int32_t>(
        header.data, static_cast<std::size_t>(index) * sizeof(std::int32_t));
    if (candidate <= 0 ||
        std::find(observed.begin(), observed.end(), candidate) !=
            observed.end()) {
      return false;
    }
    observed.push_back(candidate);
    if (candidate == regiment_id) {
      ++matches;
    }
  }
  return matches == 1 &&
         BattleControlArrayHeaderUnchanged(
             army, kInternalArmyRegimentIdsOffset,
             kInternalArmyRegimentCapacityOffset,
             kInternalArmyRegimentCountOffset, header);
}

const game::BattleControlArmyIdentitySnapshot *FindBattleControlArmy(
    const std::vector<game::BattleControlArmyIdentitySnapshot> &armies,
    std::int32_t native_carmy_id) noexcept {
  const auto found = std::find_if(
      armies.begin(), armies.end(), [native_carmy_id](const auto &row) {
        return row.native_carmy_id == native_carmy_id;
      });
  return found == armies.end() ? nullptr : &*found;
}

bool ReadBattleControlArmyIdentities(
    const Bindings &bindings, const void *combat, const void *side,
    std::int32_t expected_combat_id,
    const std::vector<std::int32_t> &native_carmy_ids,
    const std::vector<std::int32_t> &public_cunit_ids,
    std::vector<game::BattleControlArmyIdentitySnapshot> &output) noexcept {
  output.clear();
  BattleControlArrayHeaderV1 header{};
  if (!ReadBattleControlArrayHeader(
          side, kCombatSideArmyIdsOffset, kCombatSideArmyCapacityOffset,
          kCombatSideArmyCountOffset, kMaximumActualContactSideArmies,
          header) ||
      header.count != static_cast<std::int32_t>(native_carmy_ids.size()) ||
      native_carmy_ids.size() != public_cunit_ids.size() ||
      LoadAt<const void *>(side, kCombatSideCombatBackPointerOffset) != combat) {
    return false;
  }
  output.reserve(native_carmy_ids.size());
  for (std::size_t index = 0; index < native_carmy_ids.size(); ++index) {
    if (LoadAt<std::int32_t>(
            header.data, index * sizeof(std::int32_t)) !=
        native_carmy_ids[index]) {
      output.clear();
      return false;
    }
    void *const army = ResolveStoredComponent(
        bindings.army_internal_storage_slot, native_carmy_ids[index],
        kInternalArmyIdOffset);
    void *const unit = ResolveStoredComponent(
        bindings.army_storage_slot, public_cunit_ids[index], kArmyIdOffset);
    if (army == nullptr || unit == nullptr ||
        LoadAt<std::int32_t>(army, kInternalArmyUnitIdOffset) !=
            public_cunit_ids[index] ||
        LoadAt<std::int32_t>(army, kInternalArmyCombatIdOffset) !=
            expected_combat_id ||
        LoadAt<std::int32_t>(unit, kUnitArmyIdOffset) !=
            native_carmy_ids[index]) {
      output.clear();
      return false;
    }
    const auto owner_id =
        LoadAt<std::int32_t>(unit, kArmyOwnerCharacterIdOffset);
    void *owner = nullptr;
    if (!ResolveContactCharacter(bindings, owner_id, owner)) {
      output.clear();
      return false;
    }
    game::BattleControlArmyIdentitySnapshot row{};
    row.native_carmy_id = native_carmy_ids[index];
    row.public_cunit_id = public_cunit_ids[index];
    row.owner_character_id = owner_id;
    row.combat_backlink_id = expected_combat_id;
    output.push_back(row);
  }
  return BattleControlArrayHeaderUnchanged(
             side, kCombatSideArmyIdsOffset, kCombatSideArmyCapacityOffset,
             kCombatSideArmyCountOffset, header) &&
         LoadAt<const void *>(side, kCombatSideCombatBackPointerOffset) ==
             combat;
}

bool ReadBattleControlEntryBucket(
    const Bindings &bindings, const void *side, std::string_view bucket,
    std::size_t data_offset, std::size_t capacity_offset,
    std::size_t count_offset,
    const std::vector<game::BattleControlArmyIdentitySnapshot> &armies,
    std::vector<game::BattleControlRegimentEntrySnapshot> &output,
    game::BattleControlSideSnapshot &side_output,
    std::int64_t &bucket_current_fighting_raw) noexcept {
  output.clear();
  bucket_current_fighting_raw = 0;
  BattleControlArrayHeaderV1 header{};
  if (!ReadBattleControlArrayHeader(
          side, data_offset, capacity_offset, count_offset,
          kMaximumBattleControlEntriesPerBucket, header)) {
    return false;
  }
  output.reserve(static_cast<std::size_t>(header.count));
  for (std::int32_t index = 0; index < header.count; ++index) {
    auto *const entry = static_cast<std::byte *>(header.data) +
                        static_cast<std::size_t>(index) *
                            kCombatRegimentEntryStride;
    game::BattleControlRegimentEntrySnapshot row{};
    row.bucket = std::string(bucket);
    row.bucket_index = index;
    row.regiment_id =
        LoadAt<std::int32_t>(entry, kCombatRegimentIdOffset);
    void *const regiment = ResolveStoredComponent(
        bindings.regiment_storage_slot, row.regiment_id, kRegimentIdOffset);
    bool identity_valid = false;
    if (regiment == nullptr ||
        !ReadRegimentIdentity(regiment, identity_valid) || !identity_valid) {
      output.clear();
      return false;
    }
    row.native_carmy_id =
        LoadAt<std::int32_t>(regiment, kRegimentArmyIdOffset);
    const auto *const army_identity =
        FindBattleControlArmy(armies, row.native_carmy_id);
    void *const army = ResolveStoredComponent(
        bindings.army_internal_storage_slot, row.native_carmy_id,
        kInternalArmyIdOffset);
    if (army_identity == nullptr || army == nullptr ||
        !BattleControlArmyContainsRegiment(army, row.regiment_id)) {
      output.clear();
      return false;
    }
    row.public_cunit_id = army_identity->public_cunit_id;
    row.owner_character_id = army_identity->owner_character_id;
    void *const combat_type =
        LoadAt<void *>(regiment, kRegimentInnerTypeOffset);
    if (combat_type == nullptr) {
      output.clear();
      return false;
    }
    row.starting_raw =
        LoadAt<std::int64_t>(entry, kCombatRegimentStartingOffset);
    row.current_fighting_raw =
        LoadAt<std::int64_t>(entry, kCombatRegimentCurrentFightingOffset);
    row.soft_casualties_raw =
        LoadAt<std::int64_t>(entry, kCombatRegimentSoftCasualtiesOffset);
    row.effective_max_size =
        LoadAt<std::int32_t>(entry, kCombatRegimentEffectiveMaxSizeOffset);
    row.effective_siege_raw =
        LoadAt<std::int64_t>(entry, kCombatRegimentEffectiveSiegeOffset);
    row.effective_damage_raw =
        LoadAt<std::int64_t>(entry, kCombatRegimentEffectiveDamageOffset);
    row.effective_toughness_raw =
        LoadAt<std::int64_t>(entry, kCombatRegimentEffectiveToughnessOffset);
    row.effective_pursuit_raw =
        LoadAt<std::int64_t>(entry, kCombatRegimentEffectivePursuitOffset);
    row.effective_screen_raw =
        LoadAt<std::int64_t>(entry, kCombatRegimentEffectiveScreenOffset);
    if (row.starting_raw < 0 || row.current_fighting_raw < 0 ||
        row.soft_casualties_raw < 0 || row.effective_max_size < 0) {
      output.clear();
      return false;
    }
    row.fights_in_main_phase =
        LoadAt<std::uint8_t>(combat_type,
                             kRegimentMainPhaseEligibilityOffset) != 0;
    std::int64_t accounted_raw = row.current_fighting_raw;
    if (!CheckedAddSigned(accounted_raw, row.soft_casualties_raw) ||
        accounted_raw > row.starting_raw) {
      output.clear();
      return false;
    }
    const auto starting_minus_current_minus_soft =
        row.starting_raw - accounted_raw;
    if (row.fights_in_main_phase) {
      row.hard_casualties_available = true;
      row.hard_casualties_raw = starting_minus_current_minus_soft;
      if (!CheckedAddSigned(
              side_output.derived_main_fighting_entry_hard_casualties_raw,
              row.hard_casualties_raw)) {
        output.clear();
        return false;
      }
    } else if (!CheckedAddSigned(
                   side_output.non_main_start_minus_current_minus_soft_raw,
                   starting_minus_current_minus_soft)) {
      output.clear();
      return false;
    }
    if (!CheckedAddSigned(side_output.derived_current_fighting_raw,
                          row.current_fighting_raw) ||
        !CheckedAddSigned(side_output.derived_soft_casualties_raw,
                          row.soft_casualties_raw) ||
        !CheckedAddSigned(bucket_current_fighting_raw,
                          row.current_fighting_raw)) {
      output.clear();
      return false;
    }
    row.entry_strength_raw =
        bindings.get_combat_regiment_strength(entry);
    if (ResolveStoredComponent(bindings.regiment_storage_slot,
                               row.regiment_id,
                               kRegimentIdOffset) != regiment ||
        LoadAt<std::int32_t>(regiment, kRegimentArmyIdOffset) !=
            row.native_carmy_id ||
        LoadAt<void *>(regiment, kRegimentInnerTypeOffset) != combat_type) {
      output.clear();
      return false;
    }
    output.push_back(std::move(row));
  }
  return BattleControlArrayHeaderUnchanged(
      side, data_offset, capacity_offset, count_offset, header);
}

bool ReadBattleControlParticipantHardLedger(
    const Bindings &bindings, const void *side,
    game::BattleControlSideSnapshot &output) noexcept {
  output.participant_hard_ledger.clear();
  output.participant_hard_total_raw = 0;
  BattleControlArrayHeaderV1 header{};
  if (!ReadBattleControlArrayHeader(
          side, kCombatSideParticipantHardRowsOffset,
          kCombatSideParticipantHardCapacityOffset,
          kCombatSideParticipantHardCountOffset,
          kMaximumBattleControlParticipantHardRows, header)) {
    return false;
  }
  output.participant_hard_ledger.reserve(
      static_cast<std::size_t>(header.count));
  for (std::int32_t index = 0; index < header.count; ++index) {
    const auto *const row_data =
        static_cast<const std::byte *>(header.data) +
        static_cast<std::size_t>(index) *
            kCombatParticipantHardRowStride;
    game::BattleControlParticipantHardSnapshot row{};
    row.row_index = index;
    row.participant_character_id = LoadAt<std::int32_t>(
        row_data, kCombatParticipantHardCharacterIdOffset);
    row.hard_casualties_raw = LoadAt<std::int64_t>(
        row_data, kCombatParticipantHardCasualtiesOffset);
    void *participant = nullptr;
    if (row.hard_casualties_raw < 0 ||
        !ResolveContactCharacter(bindings, row.participant_character_id,
                                 participant) ||
        !CheckedAddSigned(output.participant_hard_total_raw,
                          row.hard_casualties_raw)) {
      output.participant_hard_ledger.clear();
      output.participant_hard_total_raw = 0;
      return false;
    }
    output.participant_hard_ledger.push_back(row);
  }
  return BattleControlArrayHeaderUnchanged(
      side, kCombatSideParticipantHardRowsOffset,
      kCombatSideParticipantHardCapacityOffset,
      kCombatSideParticipantHardCountOffset, header);
}

bool ReadBattleControlSide(
    const Bindings &bindings, void *combat, std::size_t side_offset,
    std::int32_t side_index, std::string_view role,
    std::int32_t expected_combat_id,
    const std::vector<std::int32_t> &native_carmy_ids,
    const std::vector<std::int32_t> &public_cunit_ids,
    std::int32_t current_roll_points,
    game::BattleControlSideSnapshot &output) noexcept {
  output = {};
  output.side_index = side_index;
  output.role = std::string(role);
  output.current_roll_points = current_roll_points;
  const auto *const side = static_cast<const std::byte *>(combat) + side_offset;
  if (LoadAt<const void *>(side, kCombatSideCombatBackPointerOffset) != combat ||
      !ReadBattleControlArmyIdentities(
          bindings, combat, side, expected_combat_id, native_carmy_ids,
          public_cunit_ids, output.ordered_armies)) {
    return false;
  }
  output.primary_participant_character_id = LoadAt<std::int32_t>(
      side, kCombatSidePrimaryCharacterIdOffset);
  void *primary = nullptr;
  if (!ResolveContactCharacter(
          bindings, output.primary_participant_character_id, primary)) {
    return false;
  }
  output.selected_commander_character_id = LoadAt<std::int32_t>(
      side, kCombatSideSelectedCommanderCharacterIdOffset);
  if (output.selected_commander_character_id != -1) {
    void *commander = nullptr;
    if (!ResolveContactCharacter(
            bindings, output.selected_commander_character_id, commander)) {
      return false;
    }
  }
  std::int64_t levy_current_fighting_raw = 0;
  std::int64_t maa_current_fighting_raw = 0;
  if (!ReadBattleControlEntryBucket(
          bindings, side, "levy", kCombatSideLevyEntriesOffset,
          kCombatSideLevyEntryCapacityOffset,
          kCombatSideLevyEntryCountOffset, output.ordered_armies,
          output.levy_entries, output, levy_current_fighting_raw) ||
      !ReadBattleControlEntryBucket(
          bindings, side, "men_at_arms", kCombatSideMaaEntriesOffset,
          kCombatSideMaaEntryCapacityOffset,
          kCombatSideMaaEntryCountOffset, output.ordered_armies,
          output.men_at_arms_entries, output, maa_current_fighting_raw) ||
      !ReadBattleControlParticipantHardLedger(bindings, side, output)) {
    return false;
  }
  output.stored_current_fighting_raw = LoadAt<std::int64_t>(
      side, kCombatSideStoredCurrentFightingOffset);
  output.stored_levy_current_fighting_raw = LoadAt<std::int64_t>(
      side, kCombatSideStoredLevyCurrentFightingOffset);
  std::int64_t bucket_total_raw = levy_current_fighting_raw;
  if (!CheckedAddSigned(bucket_total_raw, maa_current_fighting_raw) ||
      bucket_total_raw != output.derived_current_fighting_raw) {
    return false;
  }
  // +0x98/+0xA0 are tick-start caches. A stable paused main-phase frame can
  // legitimately retain the prior totals after entry rows have advanced.
  // Publish both raw observations and their equality discriminants; never
  // invoke the mutating 0x23CB840 refresh helper from this read-only query.
  output.stored_current_matches_derived =
      output.stored_current_fighting_raw ==
      output.derived_current_fighting_raw;
  output.stored_levy_current_matches_derived =
      output.stored_levy_current_fighting_raw == levy_current_fighting_raw;
  output.side_strength_raw =
      bindings.get_combat_side_strength(const_cast<std::byte *>(side));
  return LoadAt<const void *>(side, kCombatSideCombatBackPointerOffset) ==
             combat &&
         LoadAt<std::int32_t>(side, kCombatSidePrimaryCharacterIdOffset) ==
             output.primary_participant_character_id &&
         LoadAt<std::int32_t>(
             side, kCombatSideSelectedCommanderCharacterIdOffset) ==
             output.selected_commander_character_id &&
         LoadAt<std::int64_t>(side,
                              kCombatSideStoredCurrentFightingOffset) ==
             output.stored_current_fighting_raw &&
         LoadAt<std::int64_t>(
             side, kCombatSideStoredLevyCurrentFightingOffset) ==
             output.stored_levy_current_fighting_raw;
}

std::string_view BattleControlPhaseName(std::int32_t phase) noexcept {
  constexpr std::array<std::string_view, 4> names{
      "maneuver", "main", "pursuit", "done"};
  return phase >= 0 && phase < static_cast<std::int32_t>(names.size())
             ? names[static_cast<std::size_t>(phase)]
             : std::string_view{};
}

std::string_view BattleControlWinnerName(std::int32_t winner) noexcept {
  switch (winner) {
  case -1:
    return "none";
  case 0:
    return "attacker";
  case 1:
    return "defender";
  default:
    return {};
  }
}

std::int64_t CombatRetreatDayIndex(std::int32_t date_raw) noexcept {
  return (static_cast<std::int64_t>(date_raw) - kCk3DateEpochRaw) /
         kCk3DateRawPerWholeDay;
}

void AppendCombatRetreatReason(
    game::ActiveCombatRetreatLegalitySnapshot &output,
    std::string_view reason_code, std::string_view native_reason_key) {
  output.reason_codes_in_native_order.emplace_back(reason_code);
  output.native_reason_keys_in_native_order.emplace_back(native_reason_key);
}

bool ReadActiveCombatRetreatProjection(
    const Bindings &bindings, void *game_state, void *combat,
    void *subject_unit, void *subject_native_army,
    const game::BattleControlSnapshot &battle,
    game::BattleControlSnapshot &output) noexcept {
  const auto *const attacker_selected = FindBattleControlArmy(
      battle.attacker.ordered_armies, battle.subject_native_carmy_id);
  const auto *const defender_selected = FindBattleControlArmy(
      battle.defender.ordered_armies, battle.subject_native_carmy_id);
  if ((attacker_selected == nullptr) == (defender_selected == nullptr)) {
    return false;
  }
  const bool selected_is_attacker = attacker_selected != nullptr;
  const auto &selected_identity =
      selected_is_attacker ? *attacker_selected : *defender_selected;
  const auto &selected_side =
      selected_is_attacker ? battle.attacker : battle.defender;
  const auto selected_side_offset = selected_is_attacker
                                        ? kCombatAttackerSideOffset
                                        : kCombatDefenderSideOffset;
  const auto *const selected_side_native =
      static_cast<const std::byte *>(combat) + selected_side_offset;
  if (selected_identity.public_cunit_id != battle.subject_public_cunit_id ||
      LoadAt<std::int32_t>(subject_unit, kArmyOwnerCharacterIdOffset) !=
          selected_identity.owner_character_id) {
    return false;
  }

  output.selected_public_cunit_id = battle.subject_public_cunit_id;
  output.selected_native_carmy_id = battle.subject_native_carmy_id;
  output.selected_owner_character_id = selected_identity.owner_character_id;
  output.combat_province_id = battle.province_id;
  output.side_index = selected_is_attacker ? 0 : 1;
  output.affected_public_cunit_ids_in_stored_order.clear();
  output.unaffected_same_side_public_cunit_ids_in_stored_order.clear();
  for (const auto &army : selected_side.ordered_armies) {
    auto &destination = army.owner_character_id ==
                                output.selected_owner_character_id
                            ? output.affected_public_cunit_ids_in_stored_order
                            : output
                                  .unaffected_same_side_public_cunit_ids_in_stored_order;
    destination.push_back(army.public_cunit_id);
  }
  if (output.affected_public_cunit_ids_in_stored_order.empty() ||
      std::find(output.affected_public_cunit_ids_in_stored_order.begin(),
                output.affected_public_cunit_ids_in_stored_order.end(),
                output.selected_public_cunit_id) ==
          output.affected_public_cunit_ids_in_stored_order.end()) {
    return false;
  }
  output.side_scope =
      output.unaffected_same_side_public_cunit_ids_in_stored_order.empty()
          ? "full_side"
          : "owner_subset";

  output.side_flags.disallow_retreat =
      LoadAt<std::uint8_t>(selected_side_native,
                           kCombatSideDisallowRetreatOffset) != 0;
  output.side_flags.allow_early_retreat =
      LoadAt<std::uint8_t>(selected_side_native,
                           kCombatSideAllowEarlyRetreatOffset) != 0;
  output.side_flags.skip_pursuit =
      LoadAt<std::uint8_t>(selected_side_native,
                           kCombatSideSkipPursuitOffset) != 0;

  // The exact native helper falls back for any BattleResult resolution
  // failure.  BattleControl deliberately keeps its stronger full-generation
  // identity gate for a positive ID; only the native legal missing sentinel
  // (-1) reaches the fallback object in this same-frame projection.
  void *baseline_battle_result = nullptr;
  if (battle.battle_result_id > 0) {
    baseline_battle_result = ResolveStoredComponent(
        bindings.battle_result_storage_slot, battle.battle_result_id,
        kBattleResultIdOffset);
  } else if (battle.battle_result_id == -1 &&
             bindings.battle_result_fallback_slot != nullptr) {
    baseline_battle_result = *bindings.battle_result_fallback_slot;
  }
  if (baseline_battle_result == nullptr ||
      bindings.minimum_days_before_manual_retreat == nullptr) {
    return false;
  }

  auto &legality = output.legality;
  legality.status = "available";
  legality.phase_raw = battle.phase_raw;
  legality.phase = battle.phase;
  legality.retreat_elapsed_baseline_date_raw = LoadAt<std::int32_t>(
      baseline_battle_result,
      kBattleResultRetreatElapsedBaselineDateOffset);
  legality.minimum_elapsed_whole_days_exclusive =
      *bindings.minimum_days_before_manual_retreat;
  const auto observed_date_raw =
      LoadAt<std::int32_t>(game_state, kGameStateDateOffset);
  legality.elapsed_whole_days =
      CombatRetreatDayIndex(observed_date_raw) -
      CombatRetreatDayIndex(legality.retreat_elapsed_baseline_date_raw);
  const auto earliest_day_index =
      CombatRetreatDayIndex(legality.retreat_elapsed_baseline_date_raw) +
      static_cast<std::int64_t>(
          legality.minimum_elapsed_whole_days_exclusive) +
      1;
  legality.earliest_day_gate_date_raw =
      kCk3DateEpochRaw + earliest_day_index * kCk3DateRawPerWholeDay;

  void *owner_character = nullptr;
  if (!ResolveContactCharacter(bindings,
                               output.selected_owner_character_id,
                               owner_character)) {
    return false;
  }
  void *const land_status =
      LoadAt<void *>(owner_character, kCharacterLandStatusObjectOffset);
  const auto land_status_sentinel =
      land_status == nullptr
          ? 0
          : LoadAt<std::int32_t>(
                land_status, kCharacterLandStatusSentinelOffset);
  void *retreat_rule_state = nullptr;
  std::uint32_t retreat_rule_flags = 0;
  bool landless_rejected = false;
  if (land_status != nullptr && land_status_sentinel == -1) {
    retreat_rule_state = bindings.get_combat_retreat_rule_state();
    if (retreat_rule_state == nullptr) {
      return false;
    }
    retreat_rule_flags = LoadAt<std::uint32_t>(
        retreat_rule_state, kCombatRetreatRuleFlagsOffset);
    landless_rejected =
        (retreat_rule_flags & kCombatRetreatLandlessOverrideBit) == 0;
  }
  legality.landless_gate_allows_retreat = !landless_rejected;

  const bool disallowed = output.side_flags.disallow_retreat;
  const bool too_early =
      !output.side_flags.allow_early_retreat &&
      legality.elapsed_whole_days <=
          legality.minimum_elapsed_whole_days_exclusive;
  const bool pursuit_or_done = legality.phase_raw >= 2;
  if (disallowed) {
    AppendCombatRetreatReason(legality, "disallowed",
                              "COMBAT_NO_RETREAT_DISALLOWED");
  }
  if (too_early) {
    AppendCombatRetreatReason(legality, "too_early",
                              "COMBAT_NO_RETREAT_TOO_EARLY");
  }
  if (pursuit_or_done) {
    AppendCombatRetreatReason(legality, "pursuit_or_done",
                              "COMBAT_NO_RETREAT_PURSUIT");
  }
  if (landless_rejected) {
    AppendCombatRetreatReason(legality, "landless",
                              "COMBAT_NO_RETREAT_LANDLESS");
  }
  legality.legal_now =
      !disallowed && !too_early && !pursuit_or_done && !landless_rejected;
  legality.native_boolean =
      bindings.can_order_combat_retreat(combat, subject_native_army, nullptr);
  if (legality.native_boolean != legality.legal_now) {
    return false;
  }

  return LoadAt<std::int32_t>(game_state, kGameStateDateOffset) ==
             observed_date_raw &&
         LoadAt<std::int32_t>(
             baseline_battle_result,
             kBattleResultRetreatElapsedBaselineDateOffset) ==
             legality.retreat_elapsed_baseline_date_raw &&
         *bindings.minimum_days_before_manual_retreat ==
             legality.minimum_elapsed_whole_days_exclusive &&
         (LoadAt<std::uint8_t>(selected_side_native,
                               kCombatSideDisallowRetreatOffset) != 0) ==
             output.side_flags.disallow_retreat &&
         (LoadAt<std::uint8_t>(selected_side_native,
                               kCombatSideAllowEarlyRetreatOffset) != 0) ==
             output.side_flags.allow_early_retreat &&
         (LoadAt<std::uint8_t>(selected_side_native,
                               kCombatSideSkipPursuitOffset) != 0) ==
             output.side_flags.skip_pursuit &&
         LoadAt<void *>(owner_character, kCharacterLandStatusObjectOffset) ==
             land_status &&
         (land_status == nullptr ||
          LoadAt<std::int32_t>(
              land_status, kCharacterLandStatusSentinelOffset) ==
              land_status_sentinel) &&
         (retreat_rule_state == nullptr ||
          LoadAt<std::uint32_t>(
              retreat_rule_state, kCombatRetreatRuleFlagsOffset) ==
              retreat_rule_flags);
}

bool ReadBattleControlSnapshotSample(
    const Bindings &bindings, const game::BattleControlRequest &request,
    game::BattleControlSnapshot &output) noexcept {
  output = {};
  output.subject_public_cunit_id = request.subject_public_cunit_id;
  void *const game_state = *bindings.game_state_slot;
  output.observed_date_raw =
      LoadAt<std::int32_t>(game_state, kGameStateDateOffset);
  void *const subject_unit = ResolveStoredComponent(
      bindings.army_storage_slot, request.subject_public_cunit_id,
      kArmyIdOffset);
  if (subject_unit == nullptr) {
    return false;
  }
  output.subject_native_carmy_id =
      LoadAt<std::int32_t>(subject_unit, kUnitArmyIdOffset);
  void *const subject_native_army = ResolveStoredComponent(
      bindings.army_internal_storage_slot,
      output.subject_native_carmy_id, kInternalArmyIdOffset);
  void *const province =
      LoadAt<void *>(subject_unit, kArmyCurrentProvinceOffset);
  if (subject_native_army == nullptr || province == nullptr ||
      LoadAt<std::int32_t>(subject_native_army,
                           kInternalArmyUnitIdOffset) !=
          request.subject_public_cunit_id ||
      !bindings.is_army_in_combat(subject_native_army)) {
    return false;
  }
  ActiveCombatIdentityV1 identity{};
  if (!ReadActiveCombatIdentityV1(
          bindings, game_state, subject_unit, subject_native_army, province,
          request.subject_public_cunit_id, false, identity)) {
    return false;
  }
  output.combat_id = identity.combat_id;
  output.province_id = identity.province_id;
  output.finalized = identity.finalized;
  void *const combat = ResolveStoredComponent(
      bindings.combat_storage_slot, output.combat_id, kCombatIdOffset);
  if (combat == nullptr ||
      LoadAt<std::uint8_t>(combat,
                           kCombatDailyDispatchInProgressOffset) != 0) {
    return false;
  }
  output.phase_raw =
      LoadAt<std::int32_t>(combat, kCombatPhaseOffset);
  output.phase_day =
      LoadAt<std::int32_t>(combat, kCombatPhaseDayOffset);
  output.winner_raw =
      LoadAt<std::int32_t>(combat, kCombatWinnerOffset);
  output.forced_winner_raw =
      LoadAt<std::int32_t>(combat, kCombatForcedWinnerOffset);
  const auto phase = BattleControlPhaseName(output.phase_raw);
  const auto winner = BattleControlWinnerName(output.winner_raw);
  const auto forced_winner =
      BattleControlWinnerName(output.forced_winner_raw);
  const auto finalized_raw =
      LoadAt<std::uint8_t>(combat, kCombatFinalizedOffset);
  if (phase.empty() || winner.empty() || forced_winner.empty() ||
      output.phase_day < 0 || finalized_raw > 1 ||
      (finalized_raw != 0) != output.finalized) {
    return false;
  }
  output.phase = std::string(phase);
  output.winner_side = std::string(winner);
  output.forced_winner_side = std::string(forced_winner);
  output.battle_result_id =
      LoadAt<std::int32_t>(combat, kCombatBattleResultIdOffset);
  if (output.battle_result_id != -1 &&
      (output.battle_result_id <= 0 ||
       ResolveStoredComponent(bindings.battle_result_storage_slot,
                              output.battle_result_id,
                              kBattleResultIdOffset) == nullptr)) {
    return false;
  }
  output.base_combat_width =
      LoadAt<std::int32_t>(combat, kCombatBaseWidthOffset);
  output.final_combat_width =
      LoadAt<std::int32_t>(combat, kCombatFinalWidthOffset);
  output.roll_cadence_counter = LoadAt<std::int32_t>(
      combat, kCombatRollCadenceCounterOffset);
  output.base_advantage_raw =
      LoadAt<std::int64_t>(combat, kCombatBaseAdvantageOffset);
  output.resolved_advantage_raw =
      LoadAt<std::int64_t>(combat, kCombatResolvedAdvantageOffset);
  if (output.base_combat_width < 0 || output.final_combat_width < 0 ||
      !ReadBattleControlSide(
          bindings, combat, kCombatAttackerSideOffset, 0, "attacker",
          output.combat_id, identity.attacker_native_carmy_ids,
          identity.attacker_public_cunit_ids,
          LoadAt<std::int32_t>(combat, kCombatSide0RollOffset),
          output.attacker) ||
      !ReadBattleControlSide(
          bindings, combat, kCombatDefenderSideOffset, 1, "defender",
          output.combat_id, identity.defender_native_carmy_ids,
          identity.defender_public_cunit_ids,
          LoadAt<std::int32_t>(combat, kCombatSide1RollOffset),
          output.defender) ||
      !ReadActiveCombatRetreatProjection(
          bindings, game_state, combat, subject_unit, subject_native_army,
          output, output)) {
    return false;
  }
  ActiveCombatIdentityV1 identity_after{};
  if (LoadAt<std::uint8_t>(combat,
                           kCombatDailyDispatchInProgressOffset) != 0 ||
      ResolveStoredComponent(bindings.combat_storage_slot,
                             output.combat_id, kCombatIdOffset) != combat ||
      !ReadActiveCombatIdentityV1(
          bindings, game_state, subject_unit, subject_native_army, province,
          request.subject_public_cunit_id, false, identity_after) ||
      identity_after != identity) {
    return false;
  }
  output.status = game::BattleControlSnapshotStatus::available;
  output.battle_control_ready = true;
  return true;
}

bool ReadBattleTransitionSidePublicIds(
    const Bindings &bindings, const void *combat, std::size_t side_offset,
    std::int32_t expected_combat_id,
    std::vector<std::int32_t> &output) noexcept {
  output.clear();
  const auto *const side =
      static_cast<const std::byte *>(combat) + side_offset;
  BattleControlArrayHeaderV1 header{};
  if (LoadAt<const void *>(side, kCombatSideCombatBackPointerOffset) !=
          combat ||
      !ReadBattleControlArrayHeader(
          side, kCombatSideArmyIdsOffset, kCombatSideArmyCapacityOffset,
          kCombatSideArmyCountOffset, kMaximumActualContactSideArmies,
          header)) {
    return false;
  }
  output.reserve(static_cast<std::size_t>(header.count));
  for (std::int32_t index = 0; index < header.count; ++index) {
    const auto native_carmy_id = LoadAt<std::int32_t>(
        header.data,
        static_cast<std::size_t>(index) * sizeof(std::int32_t));
    if (native_carmy_id <= 0) {
      output.clear();
      return false;
    }
    void *const native_army = ResolveStoredComponent(
        bindings.army_internal_storage_slot, native_carmy_id,
        kInternalArmyIdOffset);
    if (native_army == nullptr ||
        LoadAt<std::int32_t>(native_army,
                             kInternalArmyCombatIdOffset) !=
            expected_combat_id) {
      output.clear();
      return false;
    }
    const auto public_cunit_id = LoadAt<std::int32_t>(
        native_army, kInternalArmyUnitIdOffset);
    void *const public_unit = ResolveStoredComponent(
        bindings.army_storage_slot, public_cunit_id, kArmyIdOffset);
    if (public_cunit_id <= 0 || public_unit == nullptr ||
        LoadAt<std::int32_t>(public_unit, kUnitArmyIdOffset) !=
            native_carmy_id ||
        std::find(output.begin(), output.end(), public_cunit_id) !=
            output.end()) {
      output.clear();
      return false;
    }
    output.push_back(public_cunit_id);
  }
  return BattleControlArrayHeaderUnchanged(
             side, kCombatSideArmyIdsOffset,
             kCombatSideArmyCapacityOffset, kCombatSideArmyCountOffset,
             header) &&
         LoadAt<const void *>(side, kCombatSideCombatBackPointerOffset) ==
             combat;
}

game::BattleTransitionSnapshotStatus ReadBattleTransitionSnapshotSample(
    const Bindings &bindings,
    const game::BattleTransitionRequest &request,
    game::BattleTransitionSnapshot &output) noexcept {
  output = {};
  output.combat_id = request.combat_id;
  void *const game_state = *bindings.game_state_slot;
  if (game_state == nullptr) {
    output.status = game::BattleTransitionSnapshotStatus::state_changed;
    return output.status;
  }
  output.observed_date_raw =
      LoadAt<std::int32_t>(game_state, kGameStateDateOffset);
  void *const combat = ResolveStoredComponent(
      bindings.combat_storage_slot, request.combat_id, kCombatIdOffset);
  if (combat == nullptr) {
    output.status =
        game::BattleTransitionSnapshotStatus::combat_not_found;
    output.battle_transition_ready = true;
    return output.status;
  }
  if (LoadAt<std::uint8_t>(combat,
                           kCombatDailyDispatchInProgressOffset) != 0) {
    output.status = game::BattleTransitionSnapshotStatus::state_changed;
    return output.status;
  }

  void *const province = LoadAt<void *>(combat, kCombatProvinceOffset);
  output.province_id =
      province == nullptr ? -1
                          : LoadAt<std::int32_t>(province,
                                                 kProvinceIdOffset);
  output.phase_raw = LoadAt<std::int32_t>(combat, kCombatPhaseOffset);
  output.phase_day = LoadAt<std::int32_t>(combat, kCombatPhaseDayOffset);
  output.winner_raw = LoadAt<std::int32_t>(combat, kCombatWinnerOffset);
  output.forced_winner_raw =
      LoadAt<std::int32_t>(combat, kCombatForcedWinnerOffset);
  const auto finalized_raw =
      LoadAt<std::uint8_t>(combat, kCombatFinalizedOffset);
  output.finalized = finalized_raw != 0;
  output.battle_result_id =
      LoadAt<std::int32_t>(combat, kCombatBattleResultIdOffset);
  const auto phase = BattleControlPhaseName(output.phase_raw);
  const auto winner = BattleControlWinnerName(output.winner_raw);
  const auto forced_winner =
      BattleControlWinnerName(output.forced_winner_raw);
  if (province == nullptr || output.province_id <= 0 ||
      ResolveProvince(game_state, output.province_id) != province ||
      phase.empty() || winner.empty() || forced_winner.empty() ||
      output.phase_day < 0 || finalized_raw > 1 ||
      (output.battle_result_id != -1 &&
       (output.battle_result_id <= 0 ||
        ResolveStoredComponent(bindings.battle_result_storage_slot,
                               output.battle_result_id,
                               kBattleResultIdOffset) == nullptr)) ||
      !ReadBattleTransitionSidePublicIds(
          bindings, combat, kCombatAttackerSideOffset,
          request.combat_id,
          output.attacker_public_cunit_ids_in_stored_order) ||
      !ReadBattleTransitionSidePublicIds(
          bindings, combat, kCombatDefenderSideOffset,
          request.combat_id,
          output.defender_public_cunit_ids_in_stored_order)) {
    output = {};
    output.combat_id = request.combat_id;
    output.observed_date_raw =
        LoadAt<std::int32_t>(game_state, kGameStateDateOffset);
    output.status = game::BattleTransitionSnapshotStatus::state_changed;
    return output.status;
  }
  for (const auto attacker_id :
       output.attacker_public_cunit_ids_in_stored_order) {
    if (std::find(
            output.defender_public_cunit_ids_in_stored_order.begin(),
            output.defender_public_cunit_ids_in_stored_order.end(),
            attacker_id) !=
        output.defender_public_cunit_ids_in_stored_order.end()) {
      output = {};
      output.combat_id = request.combat_id;
      output.observed_date_raw =
          LoadAt<std::int32_t>(game_state, kGameStateDateOffset);
      output.status = game::BattleTransitionSnapshotStatus::state_changed;
      return output.status;
    }
  }
  if (ResolveStoredComponent(bindings.combat_storage_slot,
                             request.combat_id,
                             kCombatIdOffset) != combat ||
      LoadAt<std::uint8_t>(combat,
                           kCombatDailyDispatchInProgressOffset) != 0) {
    output = {};
    output.combat_id = request.combat_id;
    output.observed_date_raw =
        LoadAt<std::int32_t>(game_state, kGameStateDateOffset);
    output.status = game::BattleTransitionSnapshotStatus::state_changed;
    return output.status;
  }
  output.phase = std::string(phase);
  output.winner_side = std::string(winner);
  output.forced_winner_side = std::string(forced_winner);
  output.status = game::BattleTransitionSnapshotStatus::available;
  output.battle_transition_ready = true;
  return output.status;
}

void PopulateTerminalJournalWireV1(
    const BattleTerminalJournalLookupV1 &lookup,
    const game::BattleTerminalTransitionRequestV1 &request,
    game::BattleTerminalJournalSnapshotV1 &output) noexcept {
  output = {};
  output.requested_after_sequence = request.after_terminal_sequence;
  output.oldest_available_sequence = lookup.oldest_available_sequence;
  output.latest_sequence = lookup.latest_sequence;
  if (lookup.status ==
      BattleTerminalJournalLookupStatusV1::observed) {
    output.event_status =
        game::BattleTerminalJournalEventStatusV1::observed;
    output.event_sequence = lookup.event.sequence;
  }
}

void PopulateTerminalPriorFromEventV1(
    const BattleTerminalJournalEventV1 &event,
    game::BattleTerminalPriorSnapshotV1 &output) {
  output = {};
  output.combat_id = event.combat_id;
  output.terminal_kind =
      event.suppress_normal_result_envelopes
          ? game::BattleTerminalKindV1::no_normal_result
          : game::BattleTerminalKindV1::normal_result;
  output.suppress_normal_result_envelopes =
      event.suppress_normal_result_envelopes;
  output.phase_raw = event.phase_raw;
  output.winner_raw = event.winner_raw;
  output.finalized_before = event.finalized_before;
  output.daily_guard_raw = event.daily_guard_raw;
  output.province_id = event.province_id;
  if (event.battle_result_id > 0) {
    output.battle_result_id = event.battle_result_id;
  }
  if (event.wipe_raw_observable) {
    output.wipe_raw = event.wipe_raw;
  }
  output.attacker_primary_participant_character_id =
      event.attacker_primary_participant_character_id;
  output.defender_primary_participant_character_id =
      event.defender_primary_participant_character_id;
  output.attacker_public_cunit_ids_in_stored_order.emplace(
      event.attacker_public_cunit_ids_in_stored_order.begin(),
      event.attacker_public_cunit_ids_in_stored_order.begin() +
          event.attacker_public_cunit_count);
  output.defender_public_cunit_ids_in_stored_order.emplace(
      event.defender_public_cunit_ids_in_stored_order.begin(),
      event.defender_public_cunit_ids_in_stored_order.begin() +
          event.defender_public_cunit_count);
}

bool PopulateTerminalPriorFromActiveCombatV1(
    const Bindings &bindings, void *combat, std::int32_t combat_id,
    game::BattleTerminalPriorSnapshotV1 &output) noexcept {
  output = {};
  output.combat_id = combat_id;
  if (combat == nullptr ||
      LoadAt<std::int32_t>(combat, kCombatIdOffset) != combat_id ||
      LoadAt<std::uint8_t>(combat, kCombatFinalizedOffset) != 0 ||
      LoadAt<std::uint8_t>(combat,
                           kCombatDailyDispatchInProgressOffset) != 0) {
    return false;
  }
  void *const province = LoadAt<void *>(combat, kCombatProvinceOffset);
  const auto province_id = province == nullptr
                               ? -1
                               : LoadAt<std::int32_t>(province,
                                                      kProvinceIdOffset);
  if (province_id <= 0) {
    return false;
  }
  output.terminal_kind = game::BattleTerminalKindV1::active_not_terminal;
  output.phase_raw = LoadAt<std::int32_t>(combat, kCombatPhaseOffset);
  output.winner_raw = LoadAt<std::int32_t>(combat, kCombatWinnerOffset);
  output.finalized_before = false;
  output.daily_guard_raw = LoadAt<std::uint8_t>(
      combat, kCombatDailyDispatchInProgressOffset);
  output.province_id = province_id;
  const auto result_id =
      LoadAt<std::int32_t>(combat, kCombatBattleResultIdOffset);
  if (result_id > 0) {
    void *const result = ResolveStoredComponent(
        bindings.battle_result_storage_slot, result_id,
        kBattleResultIdOffset);
    if (result == nullptr) {
      return false;
    }
    output.battle_result_id = result_id;
    output.wipe_raw =
        LoadAt<std::uint8_t>(result, kBattleResultReadyOffset) != 0;
  } else if (result_id != -1) {
    return false;
  }
  output.attacker_primary_participant_character_id =
      LoadAt<std::int32_t>(
          combat, kCombatAttackerSideOffset +
                      kCombatSidePrimaryCharacterIdOffset);
  output.defender_primary_participant_character_id =
      LoadAt<std::int32_t>(
          combat, kCombatDefenderSideOffset +
                      kCombatSidePrimaryCharacterIdOffset);
  output.attacker_public_cunit_ids_in_stored_order.emplace();
  output.defender_public_cunit_ids_in_stored_order.emplace();
  return output.attacker_primary_participant_character_id.value_or(-1) > 0 &&
         output.defender_primary_participant_character_id.value_or(-1) > 0 &&
         ReadBattleTransitionSidePublicIds(
             bindings, combat, kCombatAttackerSideOffset, combat_id,
             *output.attacker_public_cunit_ids_in_stored_order) &&
         ReadBattleTransitionSidePublicIds(
             bindings, combat, kCombatDefenderSideOffset, combat_id,
             *output.defender_public_cunit_ids_in_stored_order);
}

void PopulateTerminalWarscoreV1(
    const BattleWarscoreJournalLookupV1 &lookup,
    bool suppress_normal_result_envelopes,
    game::BattleTerminalWarscoreSnapshotV1 &output) noexcept {
  output = {};
  if (suppress_normal_result_envelopes) {
    output.status =
        game::BattleTerminalWarscoreStatusV1::not_recorded_by_native;
    return;
  }
  if (lookup.status ==
      BattleWarscoreJournalLookupStatusV1::observed) {
    const auto &event = lookup.event;
    if (event.capture_failure_flags !=
            battle_terminal_capture_failure_none ||
        event.war_id <= 0 || event.war_battle_row_index < 0 ||
        event.battle_warscore_value_raw < 0) {
      return;
    }
    output.status = game::BattleTerminalWarscoreStatusV1::recorded;
    output.war_id = event.war_id;
    output.war_battle_row_index = event.war_battle_row_index;
    output.value_raw_q100000 = event.battle_warscore_value_raw;
    output.winner_is_war_attacker = event.winner_is_war_attacker;
    output.combat_side0_is_war_attacker =
        event.combat_side0_is_war_attacker;
    output.attacker_relative_delta_raw_q100000 =
        event.winner_is_war_attacker
            ? event.battle_warscore_value_raw
            : -event.battle_warscore_value_raw;
  } else if (lookup.status ==
             BattleWarscoreJournalLookupStatusV1::not_observed) {
    output.status =
        game::BattleTerminalWarscoreStatusV1::not_recorded_by_native;
  }
}

bool ReadTerminalRouteV1(
    void *game_state, void *unit,
    std::vector<std::int32_t> &output) noexcept {
  output.clear();
  void *const data = LoadAt<void *>(unit, kUnitPathProvinceInfosOffset);
  const auto capacity = LoadAt<std::int32_t>(
      unit, kUnitPathProvinceInfoCapacityOffset);
  const auto count = LoadAt<std::int32_t>(
      unit, kUnitPathProvinceInfoCountOffset);
  if (capacity < 0 || count < 0 || count > capacity ||
      count > kMaximumUnitRouteProvinceInfos ||
      (count > 0 && data == nullptr)) {
    return false;
  }
  output.reserve(static_cast<std::size_t>(count));
  for (std::int32_t index = 0; index < count; ++index) {
    void *const info = LoadAt<void *>(
        data, static_cast<std::size_t>(index) * sizeof(void *));
    const auto province_id = info == nullptr
                                 ? -1
                                 : LoadAt<std::int32_t>(
                                       info, kUnitPathProvinceIdOffset);
    if (ResolveProvince(game_state, province_id) == nullptr) {
      output.clear();
      return false;
    }
    output.push_back(province_id);
  }
  return LoadAt<void *>(unit, kUnitPathProvinceInfosOffset) == data &&
         LoadAt<std::int32_t>(unit,
                              kUnitPathProvinceInfoCapacityOffset) ==
             capacity &&
         LoadAt<std::int32_t>(unit, kUnitPathProvinceInfoCountOffset) ==
             count;
}

void ReadTerminalAiMembershipV1(
    const Bindings &bindings, void *unit,
    game::BattleTerminalSubjectSnapshotV1 &output) noexcept {
  output.ai_membership_status =
      game::BattleTerminalAiMembershipStatusV1::unavailable;
  output.coordinator_id.reset();
  output.unit_stack_stored_index.reset();
  output.subunit_stored_index.reset();
  const auto coordinator_id =
      LoadAt<std::int32_t>(unit, kUnitAiWarCoordinatorIdOffset);
  void *const subunit =
      LoadAt<void *>(unit, kUnitAiSubunitStackOffset);
  if (coordinator_id == -1 && subunit == nullptr) {
    output.ai_membership_status =
        game::BattleTerminalAiMembershipStatusV1::none;
    return;
  }
  if (coordinator_id <= 0 || subunit == nullptr ||
      bindings.ai_war_coordinator_storage_slot == nullptr ||
      bindings.ai_war_coordinator_fallback_slot == nullptr ||
      bindings.ai_war_coordinator_vtable == 0 ||
      bindings.ai_unit_stack_vtable == 0 ||
      bindings.ai_subunit_stack_vtable == 0) {
    return;
  }
  void *const coordinator = ResolveStoredComponent(
      bindings.ai_war_coordinator_storage_slot, coordinator_id,
      kAiWarCoordinatorIdOffset);
  if (coordinator == nullptr ||
      coordinator == *bindings.ai_war_coordinator_fallback_slot ||
      LoadAt<std::uintptr_t>(coordinator, 0) !=
          bindings.ai_war_coordinator_vtable ||
      LoadAt<std::uintptr_t>(subunit, 0) !=
          bindings.ai_subunit_stack_vtable) {
    return;
  }
  void *const parent = LoadAt<void *>(subunit, kAiSubunitParentOffset);
  if (parent == nullptr ||
      LoadAt<std::uintptr_t>(parent, 0) !=
          bindings.ai_unit_stack_vtable ||
      LoadAt<void *>(parent, kAiUnitStackCoordinatorOffset) !=
          coordinator) {
    return;
  }
  BattleControlArrayHeaderV1 unit_stacks{};
  BattleControlArrayHeaderV1 subunits{};
  if (!ReadBattleControlArrayHeader(
          coordinator, kAiWarCoordinatorUnitStacksOffset,
          kAiWarCoordinatorUnitStacksCapacityOffset,
          kAiWarCoordinatorUnitStacksCountOffset,
          kMaximumAiCoordinatorUnitStacks, unit_stacks) ||
      !ReadBattleControlArrayHeader(
          parent, kAiUnitStackSubunitsOffset,
          kAiUnitStackSubunitsCapacityOffset,
          kAiUnitStackSubunitsCountOffset,
          kMaximumAiUnitStackSubunits, subunits)) {
    return;
  }
  std::int32_t parent_index = -1;
  std::int32_t subunit_index = -1;
  for (std::int32_t index = 0; index < unit_stacks.count; ++index) {
    if (LoadAt<void *>(unit_stacks.data,
                       static_cast<std::size_t>(index) *
                           sizeof(void *)) == parent) {
      if (parent_index != -1) {
        return;
      }
      parent_index = index;
    }
  }
  for (std::int32_t index = 0; index < subunits.count; ++index) {
    if (LoadAt<void *>(subunits.data,
                       static_cast<std::size_t>(index) *
                           sizeof(void *)) == subunit) {
      if (subunit_index != -1) {
        return;
      }
      subunit_index = index;
    }
  }
  if (parent_index < 0 || subunit_index < 0 ||
      !BattleControlArrayHeaderUnchanged(
          coordinator, kAiWarCoordinatorUnitStacksOffset,
          kAiWarCoordinatorUnitStacksCapacityOffset,
          kAiWarCoordinatorUnitStacksCountOffset, unit_stacks) ||
      !BattleControlArrayHeaderUnchanged(
          parent, kAiUnitStackSubunitsOffset,
          kAiUnitStackSubunitsCapacityOffset,
          kAiUnitStackSubunitsCountOffset, subunits)) {
    return;
  }
  output.coordinator_id = coordinator_id;
  output.unit_stack_stored_index = parent_index;
  output.subunit_stored_index = subunit_index;
  output.ai_membership_status =
      game::BattleTerminalAiMembershipStatusV1::observed;
}

bool ReadTerminalSubjectV1(
    const Bindings &bindings, void *game_state,
    std::int32_t subject_public_cunit_id,
    game::BattleTerminalSubjectSnapshotV1 &output) noexcept {
  output = {};
  output.ai_membership_status =
      game::BattleTerminalAiMembershipStatusV1::none;
  void *const unit = ResolveStoredComponent(
      bindings.army_storage_slot, subject_public_cunit_id,
      kArmyIdOffset);
  if (unit == nullptr) {
    return true;
  }
  output.exists = true;
  output.ai_membership_status =
      game::BattleTerminalAiMembershipStatusV1::unavailable;
  void *const province = LoadAt<void *>(unit, kArmyCurrentProvinceOffset);
  if (province != nullptr) {
    const auto province_id =
        LoadAt<std::int32_t>(province, kProvinceIdOffset);
    if (province_id <= 0 ||
        ResolveProvince(game_state, province_id) != province) {
      return false;
    }
    output.current_province_id = province_id;
  }
  const auto native_carmy_id =
      LoadAt<std::int32_t>(unit, kUnitArmyIdOffset);
  bool blocked = false;
  if (native_carmy_id > 0) {
    void *const native_army = ResolveStoredComponent(
        bindings.army_internal_storage_slot, native_carmy_id,
        kInternalArmyIdOffset);
    if (native_army == nullptr ||
        LoadAt<std::int32_t>(native_army,
                             kInternalArmyUnitIdOffset) !=
            subject_public_cunit_id) {
      return false;
    }
    output.native_carmy_id = native_carmy_id;
    const auto combat_id = LoadAt<std::int32_t>(
        native_army, kInternalArmyCombatIdOffset);
    if (combat_id != -1 && combat_id <= 0) {
      return false;
    }
    if (combat_id > 0) {
      output.combat_backlink_id = combat_id;
    }
    if (combat_id > 0) {
      void *const combat = ResolveStoredComponent(
          bindings.combat_storage_slot, combat_id, kCombatIdOffset);
      if (combat != nullptr &&
          LoadAt<std::uint8_t>(combat, kCombatFinalizedOffset) == 0) {
        output.active_combat_id = combat_id;
        blocked = true;
      }
    }
  } else if (native_carmy_id != -1) {
    return false;
  }
  output.blocked_by_active_combat = blocked;
  output.movement_or_retreat_state_raw =
      LoadAt<std::int32_t>(unit, kUnitRetreatStateOffset);
  void *const target = LoadAt<void *>(unit, kArmyTargetProvinceOffset);
  if (target != nullptr) {
    const auto target_id =
        LoadAt<std::int32_t>(target, kProvinceIdOffset);
    if (target_id <= 0 || ResolveProvince(game_state, target_id) != target) {
      return false;
    }
    output.move_target_province_id = target_id;
  }
  output.route_province_ids_in_stored_order.emplace();
  if (!ReadTerminalRouteV1(
          game_state, unit,
          *output.route_province_ids_in_stored_order)) {
    return false;
  }
  ReadTerminalAiMembershipV1(bindings, unit, output);
  return ResolveStoredComponent(bindings.army_storage_slot,
                                subject_public_cunit_id,
                                kArmyIdOffset) == unit;
}

bool ReadTerminalProvinceMembershipV1(
    const Bindings &bindings, void *game_state,
    const game::BattleTerminalPriorSnapshotV1 &prior,
    game::BattleTerminalRemovalSnapshotV1 &output,
    void *&prior_province) noexcept {
  prior_province = nullptr;
  if (!prior.province_id.has_value()) {
    return true;
  }
  prior_province = ResolveProvince(game_state, *prior.province_id);
  output.prior_province_strictly_resolves = prior_province != nullptr;
  if (prior_province != nullptr) {
    std::vector<std::int32_t> combat_ids;
    if (!ReadContactIdArray(
            prior_province, kProvinceCombatIdsOffset,
            kProvinceCombatIdCountOffset,
            kMaximumActualContactProvinceCombats, combat_ids, false)) {
      return false;
    }
    output.prior_province_contains_prior_combat_id =
        std::find(combat_ids.begin(), combat_ids.end(), prior.combat_id) !=
        combat_ids.end();
  }
  if (prior.battle_result_id.has_value()) {
    void *const result = ResolveStoredComponent(
        bindings.battle_result_storage_slot, *prior.battle_result_id,
        kBattleResultIdOffset);
    output.result_strictly_resolves = result != nullptr;
    if (result != nullptr) {
      constexpr std::size_t kRelevantPlayerCountOffset = 0xC4;
      const auto count = LoadAt<std::int32_t>(
          result, kRelevantPlayerCountOffset);
      if (count < 0 || count > kMaximumComponentCapacity) {
        return false;
      }
      output.result_relevant_player_count = count;
    }
  }
  return true;
}

bool ReadTerminalSuccessorV1(
    const Bindings &bindings, void *prior_province,
    const game::BattleTerminalPriorSnapshotV1 &prior,
    const game::BattleTerminalSubjectSnapshotV1 &subject,
    game::BattleTerminalSuccessorSnapshotV1 &output) noexcept {
  output = {};
  if (!subject.exists) {
    output.state =
        game::BattleTerminalSuccessorStateV1::subject_missing;
    return true;
  }
  if (prior.terminal_kind ==
      game::BattleTerminalKindV1::active_not_terminal) {
    output.state = game::BattleTerminalSuccessorStateV1::unavailable;
    return true;
  }
  const bool successor_scan_observable =
      prior.attacker_public_cunit_ids_in_stored_order.has_value() &&
      prior.defender_public_cunit_ids_in_stored_order.has_value() &&
      prior_province != nullptr;
  if (successor_scan_observable) {
    std::vector<std::int32_t> province_combat_ids;
    if (!ReadContactIdArray(
            prior_province, kProvinceCombatIdsOffset,
            kProvinceCombatIdCountOffset,
            kMaximumActualContactProvinceCombats, province_combat_ids,
            false)) {
      return false;
    }
    for (const auto combat_id : province_combat_ids) {
      if (combat_id == prior.combat_id) {
        continue;
      }
      void *const combat = ResolveStoredComponent(
          bindings.combat_storage_slot, combat_id, kCombatIdOffset);
      if (combat == nullptr ||
          LoadAt<void *>(combat, kCombatProvinceOffset) != prior_province) {
        return false;
      }
      if (LoadAt<std::uint8_t>(combat, kCombatFinalizedOffset) != 0) {
        continue;
      }
      std::vector<std::int32_t> attacker;
      std::vector<std::int32_t> defender;
      if (!ReadBattleTransitionSidePublicIds(
              bindings, combat, kCombatAttackerSideOffset, combat_id,
              attacker) ||
          !ReadBattleTransitionSidePublicIds(
              bindings, combat, kCombatDefenderSideOffset, combat_id,
              defender)) {
        return false;
      }
      const auto candidate_contains_prior = [&](std::int32_t id) noexcept {
        return std::find(attacker.begin(), attacker.end(), id) !=
                   attacker.end() ||
               std::find(defender.begin(), defender.end(), id) !=
                   defender.end();
      };
      const bool overlaps = std::any_of(
          prior.attacker_public_cunit_ids_in_stored_order->begin(),
          prior.attacker_public_cunit_ids_in_stored_order->end(),
          candidate_contains_prior) ||
          std::any_of(
              prior.defender_public_cunit_ids_in_stored_order->begin(),
              prior.defender_public_cunit_ids_in_stored_order->end(),
              candidate_contains_prior);
      if (overlaps) {
        output.matching_combat_ids_in_native_order.push_back(combat_id);
      }
    }
  }
  if (subject.active_combat_id.has_value() &&
      std::find(output.matching_combat_ids_in_native_order.begin(),
                output.matching_combat_ids_in_native_order.end(),
                *subject.active_combat_id) !=
          output.matching_combat_ids_in_native_order.end()) {
    output.selected_successor_combat_id = *subject.active_combat_id;
  }
  if (output.selected_successor_combat_id.has_value()) {
    void *const selected = ResolveStoredComponent(
        bindings.combat_storage_slot,
        *output.selected_successor_combat_id, kCombatIdOffset);
    std::vector<std::int32_t> attacker;
    std::vector<std::int32_t> defender;
    if (selected == nullptr ||
        !ReadBattleTransitionSidePublicIds(
            bindings, selected, kCombatAttackerSideOffset,
            *output.selected_successor_combat_id, attacker) ||
        !ReadBattleTransitionSidePublicIds(
            bindings, selected, kCombatDefenderSideOffset,
            *output.selected_successor_combat_id, defender)) {
      return false;
    }
    const auto append_prior_overlap = [&](const auto &prior_ids) {
      for (const auto id : prior_ids) {
        if (std::find(attacker.begin(), attacker.end(), id) !=
                attacker.end() ||
            std::find(defender.begin(), defender.end(), id) !=
                defender.end()) {
          output.participant_overlap_public_cunit_ids_in_prior_order
              .push_back(id);
        }
      }
    };
    append_prior_overlap(
        *prior.attacker_public_cunit_ids_in_stored_order);
    append_prior_overlap(
        *prior.defender_public_cunit_ids_in_stored_order);
    output.state =
        game::BattleTerminalSuccessorStateV1::residual_new_combat;
  } else if (subject.active_combat_id.has_value()) {
    output.state = game::BattleTerminalSuccessorStateV1::unavailable;
  } else if (subject.movement_or_retreat_state_raw.value_or(0) > 0) {
    output.state =
        game::BattleTerminalSuccessorStateV1::subject_retreating;
  } else if (!output.matching_combat_ids_in_native_order.empty() ||
             !successor_scan_observable) {
    output.state = game::BattleTerminalSuccessorStateV1::unavailable;
  } else if (subject.ai_membership_status ==
                 game::BattleTerminalAiMembershipStatusV1::observed &&
             subject.blocked_by_active_combat.value_or(true) == false) {
    output.state = game::BattleTerminalSuccessorStateV1::
        subject_assignment_reopened;
  } else if (subject.ai_membership_status ==
             game::BattleTerminalAiMembershipStatusV1::none) {
    output.state = game::BattleTerminalSuccessorStateV1::no_successor;
  } else {
    output.state = game::BattleTerminalSuccessorStateV1::unavailable;
  }
  return true;
}

bool ReadBattleTerminalTransitionSampleV1(
    const Bindings &bindings, const game::Snapshot &same_frame_world,
    const game::BattleTerminalTransitionRequestV1 &request,
    game::BattleTerminalTransitionSnapshotV1 &output) noexcept {
  output = {};
  output.observed_date_raw = same_frame_world.date_raw;
  output.prior_combat_id = request.prior_combat_id;
  output.subject_public_cunit_id = request.subject_public_cunit_id;
  output.prior.combat_id = request.prior_combat_id;
  const auto cursor = request.after_terminal_sequence.value_or(0);
  const auto journal = LookupBattleTerminalJournalV1(
      request.prior_combat_id, cursor);
  PopulateTerminalJournalWireV1(journal, request,
                               output.terminal_journal);
  const auto unavailable = [&](std::string_view reason) noexcept {
    output.status = game::BattleTerminalTransitionStatusV1::unavailable;
    output.unavailable_reason = reason;
    output.battle_terminal_transition_ready = false;
    output.terminal_journal.event_sequence.reset();
    output.terminal_journal.event_status =
        game::BattleTerminalJournalEventStatusV1::not_observed;
    return true;
  };
  if (journal.status ==
      BattleTerminalJournalLookupStatusV1::invalid_cursor) {
    return unavailable("invalid_request");
  }
  if (journal.status ==
      BattleTerminalJournalLookupStatusV1::journal_gap) {
    return unavailable("journal_gap");
  }
  if (journal.status ==
      BattleTerminalJournalLookupStatusV1::unavailable) {
    return unavailable("identity_unavailable");
  }
  if (journal.status ==
      BattleTerminalJournalLookupStatusV1::observed) {
    if ((journal.event.capture_failure_flags &
         battle_terminal_capture_failure_bounds) != 0) {
      return unavailable("bounds_exceeded");
    }
    if (journal.event.capture_failure_flags !=
        battle_terminal_capture_failure_none) {
      return unavailable("identity_unavailable");
    }
    PopulateTerminalPriorFromEventV1(journal.event, output.prior);
    const auto warscore = LookupBattleWarscoreJournalV1(
        request.prior_combat_id);
    PopulateTerminalWarscoreV1(
        warscore, journal.event.suppress_normal_result_envelopes,
        output.prior.battle_warscore);
  }
  void *const game_state = *bindings.game_state_slot;
  void *const prior_combat = ResolveStoredComponent(
      bindings.combat_storage_slot, request.prior_combat_id,
      kCombatIdOffset);
  output.removal.prior_combat_strictly_resolves = prior_combat != nullptr;
  if (journal.status ==
      BattleTerminalJournalLookupStatusV1::not_observed) {
    if (prior_combat != nullptr) {
      if (!PopulateTerminalPriorFromActiveCombatV1(
              bindings, prior_combat, request.prior_combat_id,
              output.prior)) {
        return unavailable("identity_unavailable");
      }
    } else {
      output.prior = {};
      output.prior.combat_id = request.prior_combat_id;
      output.prior.terminal_kind =
          game::BattleTerminalKindV1::unavailable_after_removal;
    }
  }
  void *prior_province = nullptr;
  if (!ReadTerminalProvinceMembershipV1(
          bindings, game_state, output.prior, output.removal,
          prior_province) ||
      !ReadTerminalSubjectV1(
          bindings, game_state, request.subject_public_cunit_id,
          output.subject) ||
      !ReadTerminalSuccessorV1(
          bindings, prior_province, output.prior, output.subject,
          output.successor)) {
    return unavailable("state_changed");
  }
  if (prior_combat != nullptr &&
      ResolveStoredComponent(bindings.combat_storage_slot,
                             request.prior_combat_id,
                             kCombatIdOffset) != prior_combat) {
    return unavailable("state_changed");
  }
  output.status = game::BattleTerminalTransitionStatusV1::available;
  output.unavailable_reason.clear();
  output.battle_terminal_transition_ready = true;
  return true;
}

} // namespace

ActualContactScopeStatus ReadActualContactScope(
    const Bindings &bindings, const ActualContactScopeRequest &request,
    ActualContactScopeSnapshot &output) noexcept {
  output = {};
  output.subject_army_id = request.subject_army_id;
  output.target_province_id = request.target_province_id;
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.jomini_state_slot == nullptr ||
      bindings.army_storage_slot == nullptr ||
      bindings.army_internal_storage_slot == nullptr ||
      bindings.regiment_storage_slot == nullptr ||
      bindings.character_storage_slot == nullptr ||
      bindings.combat_storage_slot == nullptr ||
      bindings.battle_result_storage_slot == nullptr ||
      bindings.contact_game_mode_slot == nullptr ||
      bindings.is_character_hostile == nullptr ||
      bindings.is_army_empty_for_contact == nullptr ||
      bindings.is_army_in_combat == nullptr ||
      bindings.read_province_holder_character_id == nullptr ||
      bindings.classify_contact_defender_by_holder == nullptr ||
      bindings.classify_contact_defender_fallback == nullptr ||
      request.subject_army_id <= 0 || request.target_province_id <= 0) {
    output.status = ActualContactScopeStatus::unavailable;
    return output.status;
  }
  Snapshot before{};
  if (!ReadSnapshot(bindings, before)) {
    output.status = ActualContactScopeStatus::unavailable;
    return output.status;
  }
  if (!before.paused) {
    output.status = ActualContactScopeStatus::requires_paused;
    return output.status;
  }
  const auto *const subject =
      FindArmySnapshot(before, request.subject_army_id);
  if (subject == nullptr) {
    output.status = ActualContactScopeStatus::subject_army_not_found;
    return output.status;
  }
  if (!subject->controllable) {
    output.status = ActualContactScopeStatus::subject_army_not_controllable;
    return output.status;
  }
  if (!subject->has_current_province ||
      subject->current_province_id != request.target_province_id) {
    output.status = ActualContactScopeStatus::subject_not_at_target;
    return output.status;
  }

  ActualContactScopeSnapshot first{};
  ActualContactScopeSnapshot second{};
  const auto first_status =
      ReadActualContactScopeSample(bindings, request, first);
  const auto second_status =
      ReadActualContactScopeSample(bindings, request, second);
  Snapshot after{};
  if (first_status != second_status || first != second ||
      !ReadSnapshot(bindings, after) || before != after) {
    output.status = ActualContactScopeStatus::state_changed;
    return output.status;
  }
  output = std::move(second);
  output.date_raw = before.date_raw;
  output.status = second_status;
  return output.status;
}

BattleControlSnapshotStatus ReadBattleControlSnapshot(
    const Bindings &bindings, const BattleControlRequest &request,
    BattleControlSnapshot &output) noexcept {
  output = {};
  output.subject_public_cunit_id = request.subject_public_cunit_id;
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.jomini_state_slot == nullptr ||
      bindings.army_storage_slot == nullptr ||
      bindings.army_internal_storage_slot == nullptr ||
      bindings.regiment_storage_slot == nullptr ||
      bindings.character_storage_slot == nullptr ||
      bindings.combat_storage_slot == nullptr ||
      bindings.battle_result_storage_slot == nullptr ||
      bindings.battle_result_fallback_slot == nullptr ||
      bindings.is_army_in_combat == nullptr ||
      bindings.get_combat_side_strength == nullptr ||
      bindings.get_combat_regiment_strength == nullptr ||
      bindings.can_order_combat_retreat == nullptr ||
      bindings.get_combat_retreat_rule_state == nullptr ||
      bindings.minimum_days_before_manual_retreat == nullptr ||
      request.subject_public_cunit_id <= 0) {
    output.status = BattleControlSnapshotStatus::unavailable;
    return output.status;
  }
  Snapshot before{};
  if (!ReadSnapshot(bindings, before)) {
    output.status = BattleControlSnapshotStatus::unavailable;
    return output.status;
  }
  if (!before.paused) {
    output.status = BattleControlSnapshotStatus::requires_paused;
    return output.status;
  }
  const auto *const subject =
      FindArmySnapshot(before, request.subject_public_cunit_id);
  if (subject == nullptr) {
    output.status = BattleControlSnapshotStatus::subject_cunit_not_found;
    return output.status;
  }
  if (!subject->controllable) {
    output.status = BattleControlSnapshotStatus::subject_not_controllable;
    return output.status;
  }
  if (subject->retreating) {
    output.status = BattleControlSnapshotStatus::subject_retreating;
    return output.status;
  }
  if (!subject->in_combat) {
    output.status = BattleControlSnapshotStatus::subject_not_in_combat;
    return output.status;
  }
  game::BattleControlSnapshot first{};
  game::BattleControlSnapshot second{};
  Snapshot after{};
  if (!ReadBattleControlSnapshotSample(bindings, request, first) ||
      !ReadBattleControlSnapshotSample(bindings, request, second) ||
      first != second || !ReadSnapshot(bindings, after) || before != after) {
    output.status = BattleControlSnapshotStatus::state_changed;
    return output.status;
  }
  output = std::move(second);
  output.observed_date_raw = before.date_raw;
  output.status = BattleControlSnapshotStatus::available;
  output.battle_control_ready = true;
  return output.status;
}

BattleTransitionSnapshotStatus ReadBattleTransitionSnapshot(
    const Bindings &bindings, const BattleTransitionRequest &request,
    BattleTransitionSnapshot &output) noexcept {
  output = {};
  output.combat_id = request.combat_id;
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.jomini_state_slot == nullptr ||
      bindings.combat_storage_slot == nullptr ||
      bindings.army_storage_slot == nullptr ||
      bindings.army_internal_storage_slot == nullptr ||
      bindings.battle_result_storage_slot == nullptr ||
      request.combat_id <= 0) {
    output.status = BattleTransitionSnapshotStatus::unavailable;
    return output.status;
  }
  Snapshot before{};
  if (!ReadSnapshot(bindings, before)) {
    output.status = BattleTransitionSnapshotStatus::unavailable;
    return output.status;
  }
  output.observed_date_raw = before.date_raw;
  if (!before.paused) {
    output.status = BattleTransitionSnapshotStatus::unavailable;
    return output.status;
  }

  BattleTransitionSnapshot first{};
  BattleTransitionSnapshot second{};
  const auto first_status =
      ReadBattleTransitionSnapshotSample(bindings, request, first);
  const auto second_status =
      ReadBattleTransitionSnapshotSample(bindings, request, second);
  Snapshot after{};
  if (first_status != second_status || first != second ||
      !ReadSnapshot(bindings, after) || before != after) {
    output = {};
    output.combat_id = request.combat_id;
    output.observed_date_raw = before.date_raw;
    output.status = BattleTransitionSnapshotStatus::state_changed;
    return output.status;
  }
  output = std::move(second);
  output.observed_date_raw = before.date_raw;
  output.status = second_status;
  output.battle_transition_ready =
      second_status == BattleTransitionSnapshotStatus::available ||
      second_status == BattleTransitionSnapshotStatus::combat_not_found;
  return output.status;
}

BattleTerminalTransitionStatusV1 ReadBattleTerminalTransitionV1(
    const Bindings &bindings, const Snapshot &same_frame_world,
    const BattleTerminalTransitionRequestV1 &request,
    BattleTerminalTransitionSnapshotV1 &output) noexcept {
  const auto unavailable = [&](std::string_view reason) noexcept {
    const auto journal = LookupBattleTerminalJournalV1(
        request.prior_combat_id,
        request.after_terminal_sequence.value_or(0));
    output = {};
    output.status = BattleTerminalTransitionStatusV1::unavailable;
    output.unavailable_reason = reason;
    output.observed_date_raw = same_frame_world.date_raw;
    output.prior_combat_id = request.prior_combat_id;
    output.subject_public_cunit_id = request.subject_public_cunit_id;
    PopulateTerminalJournalWireV1(journal, request,
                                 output.terminal_journal);
    output.terminal_journal.event_sequence.reset();
    output.terminal_journal.event_status =
        game::BattleTerminalJournalEventStatusV1::not_observed;
    return output.status;
  };

  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.jomini_state_slot == nullptr ||
      bindings.combat_storage_slot == nullptr ||
      bindings.army_storage_slot == nullptr ||
      bindings.army_internal_storage_slot == nullptr ||
      bindings.battle_result_storage_slot == nullptr ||
      request.prior_combat_id <= 0 ||
      request.subject_public_cunit_id <= 0) {
    return unavailable(request.prior_combat_id <= 0 ||
                               request.subject_public_cunit_id <= 0
                           ? "invalid_request"
                           : "unsupported_build");
  }
  if (!same_frame_world.paused) {
    return unavailable("requires_paused");
  }
  Snapshot before{};
  if (!ReadSnapshot(bindings, before) || before != same_frame_world) {
    return unavailable("state_changed");
  }

  BattleTerminalTransitionSnapshotV1 first{};
  BattleTerminalTransitionSnapshotV1 second{};
  if (!ReadBattleTerminalTransitionSampleV1(bindings, same_frame_world,
                                            request, first) ||
      !ReadBattleTerminalTransitionSampleV1(bindings, same_frame_world,
                                            request, second)) {
    return unavailable("state_changed");
  }
  Snapshot after{};
  if (first != second || !ReadSnapshot(bindings, after) ||
      after != same_frame_world) {
    return unavailable("state_changed");
  }
  output = std::move(second);
  output.observed_date_raw = same_frame_world.date_raw;
  output.prior_combat_id = request.prior_combat_id;
  output.subject_public_cunit_id = request.subject_public_cunit_id;
  return output.status;
}

BattleReinforcementAssignmentStatus ReadBattleReinforcementAssignmentV1(
    const Bindings &bindings, const Snapshot &same_frame_world,
    const BattleReinforcementAssignmentRequest &request,
    BattleReinforcementAssignmentSnapshot &output) noexcept {
  const auto unavailable =
      [&](std::string_view reason) noexcept {
        output = {};
        output.status = BattleReinforcementAssignmentStatus::unavailable;
        output.unavailable_reason = reason;
        output.observed_date_raw = same_frame_world.date_raw;
        output.selected_public_cunit_id =
            request.selected_public_cunit_id;
        return output.status;
      };

  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.army_storage_slot == nullptr ||
      bindings.army_internal_storage_slot == nullptr ||
      bindings.combat_storage_slot == nullptr ||
      bindings.character_storage_slot == nullptr ||
      bindings.ai_war_coordinator_storage_slot == nullptr ||
      bindings.ai_war_coordinator_fallback_slot == nullptr ||
      bindings.ai_unit_stack_vtable == 0 ||
      bindings.ai_subunit_stack_vtable == 0 ||
      bindings.ai_war_coordinator_vtable == 0 ||
      bindings.read_unit_land_route_speed == nullptr ||
      bindings.read_unit_naval_route_speed == nullptr ||
      bindings.read_unit_current_edge_speed == nullptr ||
      bindings.read_route_travel_duration == nullptr ||
      bindings.read_route_edge_duration == nullptr ||
      bindings.is_character_hostile == nullptr ||
      request.selected_public_cunit_id <= 0) {
    return unavailable("unsupported_build");
  }
  if (!same_frame_world.paused) {
    return unavailable("requires_paused");
  }
  void *const game_state = *bindings.game_state_slot;
  if (game_state == nullptr ||
      LoadAt<std::int32_t>(game_state, kGameStateDateOffset) !=
          same_frame_world.date_raw) {
    return unavailable("state_changed");
  }

  BattleReinforcementAssignmentSampleV1 first{};
  BattleReinforcementAssignmentSampleV1 second{};
  std::string_view first_failure;
  std::string_view second_failure;
  const bool first_available =
      ReadBattleReinforcementAssignmentSampleV1(
          bindings, same_frame_world, request, first, first_failure);
  const bool second_available =
      ReadBattleReinforcementAssignmentSampleV1(
          bindings, same_frame_world, request, second, second_failure);
  if (first_available != second_available || first_failure != second_failure ||
      first != second ||
      LoadAt<std::int32_t>(game_state, kGameStateDateOffset) !=
          same_frame_world.date_raw) {
    return unavailable("state_changed");
  }
  if (!second_available) {
    return unavailable(second_failure.empty() ? "state_changed"
                                               : second_failure);
  }
  output = std::move(second.value);
  output.unavailable_reason.clear();
  output.observed_date_raw = same_frame_world.date_raw;
  output.selected_public_cunit_id = request.selected_public_cunit_id;
  output.status = BattleReinforcementAssignmentStatus::available;
  output.battle_reinforcement_assignment_ready = true;
  return output.status;
}

DisbandArmyResult SubmitDisbandArmy(const Bindings &bindings,
                                    std::int32_t army_id) noexcept {
  if (!bindings.enabled || bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.validate_disband_army_command == nullptr ||
      bindings.disband_army_primary_vtable == 0 ||
      bindings.disband_army_secondary_vtable == 0) {
    return DisbandArmyResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return DisbandArmyResult::unavailable;
  }
  void *const army = ResolveArmy(bindings, army_id);
  if (army == nullptr) {
    return DisbandArmyResult::army_not_found;
  }
  bool controllable = false;
  for (const auto &candidate : current.player_armies) {
    if (candidate.army_id == army_id && candidate.controllable) {
      controllable = true;
      break;
    }
  }
  if (!controllable) {
    return DisbandArmyResult::army_not_controllable;
  }

  constexpr std::int32_t command_kind = 1;
  const std::int32_t command_target_id =
      LoadAt<std::int32_t>(army, kUnitArmyIdOffset);
  if (!bindings.validate_disband_army_command(
          command_kind, command_target_id, nullptr)) {
    return DisbandArmyResult::army_not_controllable;
  }

  DisbandArmyCommand command{};
  command.primary_vtable = bindings.disband_army_primary_vtable;
  command.secondary_vtable = bindings.disband_army_secondary_vtable;
  command.command_kind = command_kind;
  command.command_target_id = command_target_id;
  bindings.submit_command(bindings.command_manager, &command, 0x0E);
  return DisbandArmyResult::submitted;
}

SplitArmyHalfResult SubmitSplitArmyHalf(const Bindings &bindings,
                                        std::int32_t army_id) noexcept {
  if (!bindings.enabled || bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.validate_split_army_half_command == nullptr ||
      bindings.destroy_split_army_half_command == nullptr ||
      bindings.split_army_half_primary_vtable == 0 ||
      bindings.split_army_half_secondary_vtable == 0) {
    return SplitArmyHalfResult::unavailable;
  }

  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return SplitArmyHalfResult::unavailable;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return SplitArmyHalfResult::no_played_character;
  }

  // The public ArmySnapshot ID is CUnit+0x10. Split Half instead consumes the
  // generation-bearing CArmyID linked from CUnit+0x178.
  void *const unit = ResolveArmy(bindings, army_id);
  if (unit == nullptr) {
    return SplitArmyHalfResult::army_not_found;
  }
  const auto selected = std::find_if(
      current.player_armies.begin(), current.player_armies.end(),
      [army_id](const ArmySnapshot &candidate) {
        return candidate.army_id == army_id && candidate.controllable;
      });
  if (selected == current.player_armies.end()) {
    return SplitArmyHalfResult::army_not_controllable;
  }

  constexpr std::int32_t command_kind = 1;
  const auto source_army_id =
      LoadAt<std::int32_t>(unit, kUnitArmyIdOffset);
  if (!bindings.validate_split_army_half_command(
          command_kind, source_army_id, current.played_character_id,
          nullptr)) {
    return SplitArmyHalfResult::validator_rejected;
  }

  SplitArmyHalfCommand command{};
  command.primary_vtable = bindings.split_army_half_primary_vtable;
  command.secondary_vtable = bindings.split_army_half_secondary_vtable;
  command.command_kind = command_kind;
  command.played_character_id = current.played_character_id;
  command.source_army_id = source_army_id;
  // SubmitCommand invokes the primary-vtable +0x40 heap clone synchronously
  // and returns whether the queue accepted that clone with player flags 0x0E.
  const bool submitted =
      bindings.submit_command(bindings.command_manager, &command, 0x0E);
  bindings.destroy_split_army_half_command(&command, 0);
  return submitted ? SplitArmyHalfResult::split_submitted
                   : SplitArmyHalfResult::submission_failed;
}

MergeArmiesResult SubmitMergeArmies(const Bindings &bindings,
                                    std::int32_t destination_army_id,
                                    std::int32_t source_army_id) noexcept {
  if (!bindings.enabled || bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.create_merge_armies_command == nullptr ||
      bindings.validate_merge_armies_command == nullptr ||
      bindings.destroy_merge_armies_command == nullptr ||
      bindings.append_native_int_array_range == nullptr ||
      bindings.merge_armies_primary_vtable == 0 ||
      bindings.merge_armies_secondary_vtable == 0) {
    return MergeArmiesResult::unavailable;
  }

  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return MergeArmiesResult::unavailable;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return MergeArmiesResult::no_played_character;
  }
  if (destination_army_id == source_army_id) {
    return MergeArmiesResult::same_army;
  }
  if (ResolveArmy(bindings, destination_army_id) == nullptr) {
    return MergeArmiesResult::destination_not_found;
  }
  if (ResolveArmy(bindings, source_army_id) == nullptr) {
    return MergeArmiesResult::source_not_found;
  }

  const auto is_controllable = [&current](std::int32_t army_id) {
    return std::any_of(
        current.player_armies.begin(), current.player_armies.end(),
        [army_id](const ArmySnapshot &candidate) {
          return candidate.army_id == army_id && candidate.controllable;
        });
  };
  if (!is_controllable(destination_army_id)) {
    return MergeArmiesResult::destination_not_controllable;
  }
  if (!is_controllable(source_army_id)) {
    return MergeArmiesResult::source_not_controllable;
  }

  auto *const command = static_cast<MergeArmiesCommand *>(
      bindings.create_merge_armies_command());
  if (command == nullptr) {
    return MergeArmiesResult::unavailable;
  }
  MergeArmiesCommandCleanup cleanup{
      bindings.destroy_merge_armies_command, command};
  if (command->primary_vtable != bindings.merge_armies_primary_vtable ||
      command->secondary_vtable != bindings.merge_armies_secondary_vtable ||
      command->source_army_ids.data != nullptr ||
      command->source_army_ids.capacity != 0 ||
      command->source_army_ids.count != 0 ||
      command->source_army_ids.allocator == nullptr) {
    return MergeArmiesResult::unavailable;
  }

  constexpr std::int32_t command_kind = 1;
  command->command_kind = command_kind;
  command->destination_army_id = destination_army_id;
  bindings.append_native_int_array_range(
      &command->source_army_ids, 0, &source_army_id, &source_army_id + 1);
  if (command->source_army_ids.data == nullptr ||
      command->source_army_ids.capacity < 1 ||
      command->source_army_ids.count != 1 ||
      command->source_army_ids.data[0] != source_army_id) {
    return MergeArmiesResult::unavailable;
  }
  if (!bindings.validate_merge_armies_command(command, nullptr)) {
    return MergeArmiesResult::validator_rejected;
  }

  // SubmitCommand synchronously calls primary-vtable +0x40, whose exact-build
  // clone repeats the same canonical range copy. The RAII cleanup then frees
  // only the original engine-owned array/object; the wrapper's clone is
  // distinct whether the queue accepts or rejects it.
  const bool submitted =
      bindings.submit_command(bindings.command_manager, command, 0x0E);
  return submitted ? MergeArmiesResult::merge_submitted
                   : MergeArmiesResult::submission_failed;
}

StartAssaultResult SubmitStartAssault(const Bindings &bindings,
                                      std::int32_t siege_id) noexcept {
  if (!bindings.enabled || bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.validate_start_assault_command == nullptr ||
      bindings.destroy_assault_command == nullptr ||
      bindings.start_assault_primary_vtable == 0 ||
      bindings.start_assault_secondary_vtable == 0) {
    return StartAssaultResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return StartAssaultResult::unavailable;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return StartAssaultResult::no_played_character;
  }
  void *const siege = ResolveSiege(bindings, siege_id);
  if (siege == nullptr) {
    return StartAssaultResult::siege_not_found;
  }
  void *const siege_province =
      LoadAt<void *>(siege, kSiegeProvinceOffset);
  const auto siege_province_id = siege_province != nullptr
                                     ? LoadAt<std::int32_t>(
                                           siege_province, kProvinceIdOffset)
                                     : -1;
  void *const game_state = bindings.game_state_slot != nullptr
                               ? *bindings.game_state_slot
                               : nullptr;
  if (siege_province == nullptr ||
      ResolveProvince(game_state, siege_province_id) != siege_province ||
      LoadAt<std::int32_t>(siege_province,
                           kProvinceActiveSiegeIdOffset) != siege_id) {
    return StartAssaultResult::siege_not_found;
  }
  const auto active_raw =
      LoadAt<std::uint8_t>(siege, kSiegeAssaultInProgressOffset);
  if (active_raw > 1) {
    return StartAssaultResult::unavailable;
  }
  if (active_raw != 0) {
    return StartAssaultResult::assault_already_active;
  }

  constexpr std::int32_t command_kind = 1;
  if (!bindings.validate_start_assault_command(
          command_kind, current.played_character_id, siege_id, nullptr)) {
    return StartAssaultResult::validator_rejected;
  }
  AssaultCommand command{};
  command.primary_vtable = bindings.start_assault_primary_vtable;
  command.secondary_vtable = bindings.start_assault_secondary_vtable;
  command.command_kind = command_kind;
  command.played_character_id = current.played_character_id;
  command.siege_id = siege_id;
  const bool submitted =
      bindings.submit_command(bindings.command_manager, &command, 0x0E);
  bindings.destroy_assault_command(&command, 0);
  return submitted ? StartAssaultResult::start_submitted
                   : StartAssaultResult::submission_failed;
}

StopAssaultResult SubmitStopAssault(const Bindings &bindings,
                                    std::int32_t siege_id) noexcept {
  if (!bindings.enabled || bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.validate_stop_assault_command == nullptr ||
      bindings.destroy_assault_command == nullptr ||
      bindings.stop_assault_primary_vtable == 0 ||
      bindings.stop_assault_secondary_vtable == 0) {
    return StopAssaultResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return StopAssaultResult::unavailable;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return StopAssaultResult::no_played_character;
  }
  void *const siege = ResolveSiege(bindings, siege_id);
  if (siege == nullptr) {
    return StopAssaultResult::siege_not_found;
  }
  void *const siege_province =
      LoadAt<void *>(siege, kSiegeProvinceOffset);
  const auto siege_province_id = siege_province != nullptr
                                     ? LoadAt<std::int32_t>(
                                           siege_province, kProvinceIdOffset)
                                     : -1;
  void *const game_state = bindings.game_state_slot != nullptr
                               ? *bindings.game_state_slot
                               : nullptr;
  if (siege_province == nullptr ||
      ResolveProvince(game_state, siege_province_id) != siege_province ||
      LoadAt<std::int32_t>(siege_province,
                           kProvinceActiveSiegeIdOffset) != siege_id) {
    return StopAssaultResult::siege_not_found;
  }
  const auto active_raw =
      LoadAt<std::uint8_t>(siege, kSiegeAssaultInProgressOffset);
  if (active_raw > 1) {
    return StopAssaultResult::unavailable;
  }
  if (active_raw == 0) {
    return StopAssaultResult::assault_not_active;
  }

  constexpr std::int32_t command_kind = 1;
  if (!bindings.validate_stop_assault_command(
          command_kind, current.played_character_id, siege_id, nullptr)) {
    return StopAssaultResult::validator_rejected;
  }
  AssaultCommand command{};
  command.primary_vtable = bindings.stop_assault_primary_vtable;
  command.secondary_vtable = bindings.stop_assault_secondary_vtable;
  command.command_kind = command_kind;
  command.played_character_id = current.played_character_id;
  command.siege_id = siege_id;
  const bool submitted =
      bindings.submit_command(bindings.command_manager, &command, 0x0E);
  bindings.destroy_assault_command(&command, 0);
  return submitted ? StopAssaultResult::stop_submitted
                   : StopAssaultResult::submission_failed;
}

ReadDeclarableWarsResult ReadDeclarableWarsForTarget(
    const Bindings &bindings, std::int32_t target_character_id,
    std::vector<DeclarableWarSnapshot> &output) noexcept {
  output.clear();
  if (!HasDeclarableWarReadBindings(bindings)) {
    return ReadDeclarableWarsResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return ReadDeclarableWarsResult::unavailable;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return ReadDeclarableWarsResult::no_played_character;
  }
  void *const attacker_character =
      ResolveCharacter(bindings, current.played_character_id);
  void *const target_character =
      ResolveCharacter(bindings, target_character_id);
  if (target_character == nullptr ||
      LoadAt<void *>(target_character, kCharacterDeathDataOffset) != nullptr) {
    return ReadDeclarableWarsResult::target_not_found;
  }
  void *const casus_belli_database =
      bindings.get_casus_belli_type_database();
  std::vector<DeclarableWarSnapshot> choices;
  if (attacker_character == nullptr ||
      !ReadDeclarableWarsForTargetInternal(
          bindings, casus_belli_database, attacker_character,
          target_character, target_character_id, choices)) {
    return ReadDeclarableWarsResult::unavailable;
  }
  output = std::move(choices);
  return ReadDeclarableWarsResult::available;
}

bool ReadDeclarableWars(
    const Bindings &bindings,
    std::vector<DeclarableWarSnapshot> &output) noexcept {
  output.clear();
  if (!HasDeclarableWarReadBindings(bindings)) {
    return false;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current) || !current.has_played_character ||
      !current.played_character_alive) {
    return false;
  }
  void *const attacker_character =
      ResolveCharacter(bindings, current.played_character_id);
  void *const storage = *bindings.character_storage_slot;
  if (attacker_character == nullptr || storage == nullptr) {
    return false;
  }
  void *const slots = LoadAt<void *>(storage, kComponentStorageSlotsOffset);
  const auto capacity =
      LoadAt<std::int32_t>(storage, kComponentStorageCapacityOffset);
  if (slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentCapacity) {
    return false;
  }
  void *const casus_belli_database =
      bindings.get_casus_belli_type_database();
  void *casus_belli_types = nullptr;
  std::int32_t casus_belli_type_count = 0;
  if (!ReadCasusBelliDatabase(casus_belli_database, casus_belli_types,
                              casus_belli_type_count)) {
    return false;
  }

  std::vector<DeclarableWarSnapshot> choices;
  for (std::int32_t index = 0; index < capacity; ++index) {
    void *const target_character = LoadAt<void *>(
        slots, static_cast<std::size_t>(index) *
                       kComponentStorageSlotSize +
                   kComponentStorageSlotObjectOffset);
    if (target_character == nullptr ||
        target_character == attacker_character ||
        LoadAt<void *>(target_character, kCharacterDeathDataOffset) !=
            nullptr) {
      continue;
    }
    const auto target_character_id =
        LoadAt<std::int32_t>(target_character, kCharacterIdOffset);
    if ((static_cast<std::uint32_t>(target_character_id) & 0x00FFFFFFU) !=
        static_cast<std::uint32_t>(index)) {
      continue;
    }
    if (!ReadDeclarableWarsForTargetInternal(
            bindings, casus_belli_database, attacker_character,
            target_character, target_character_id, choices)) {
      return false;
    }
  }
  output = std::move(choices);
  return true;
}

DeclareWarResult SubmitDeclareWar(
    const Bindings &bindings,
    const DeclarableWarSnapshot &declaration) noexcept {
  if (!HasDeclarableWarReadBindings(bindings) ||
      bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.copy_native_int_array == nullptr ||
      bindings.append_native_int_array_range == nullptr ||
      bindings.construct_character_interaction_context == nullptr ||
      bindings.refresh_character_interaction_context == nullptr ||
      bindings.finalize_character_interaction_context == nullptr ||
      bindings.validate_character_interaction_context == nullptr ||
      bindings.construct_send_character_interaction_command == nullptr ||
      bindings.destroy_character_interaction_context == nullptr ||
      bindings.send_character_interaction_primary_vtable == 0 ||
      bindings.send_character_interaction_secondary_vtable == 0 ||
      bindings.war_declaration_vtable == 0) {
    return DeclareWarResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return DeclareWarResult::unavailable;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return DeclareWarResult::no_played_character;
  }
  void *const attacker_character =
      ResolveCharacter(bindings, current.played_character_id);
  void *const target_character =
      ResolveCharacter(bindings, declaration.target_character_id);
  if (target_character == nullptr ||
      LoadAt<void *>(target_character, kCharacterDeathDataOffset) != nullptr) {
    return DeclareWarResult::target_not_found;
  }
  void *const casus_belli_database =
      bindings.get_casus_belli_type_database();
  void *casus_belli_types = nullptr;
  std::int32_t casus_belli_type_count = 0;
  if (attacker_character == nullptr ||
      !ReadCasusBelliDatabase(casus_belli_database, casus_belli_types,
                              casus_belli_type_count)) {
    return DeclareWarResult::unavailable;
  }
  if (declaration.casus_belli_index < 0 ||
      declaration.casus_belli_index >= casus_belli_type_count) {
    return DeclareWarResult::declaration_unavailable;
  }
  void *const casus_belli_type = LoadAt<void *>(
      casus_belli_types,
      static_cast<std::size_t>(declaration.casus_belli_index) *
          sizeof(void *));
  if (!IsEnabledCasusBelliType(casus_belli_type) ||
      !ClearValidCasusBelliConfigurations(bindings)) {
    return DeclareWarResult::declaration_unavailable;
  }
  const bool available = bindings.evaluate_casus_belli(
      casus_belli_type, attacker_character, target_character,
      bindings.valid_casus_belli_configuration_scratch, false, false,
      nullptr);
  std::vector<DeclarableWarSnapshot> current_choices;
  if (!available ||
      !MaterializeCasusBelliChoices(
          bindings, casus_belli_type, declaration.target_character_id,
          declaration.casus_belli_index, current_choices)) {
    ClearValidCasusBelliConfigurations(bindings);
    return DeclareWarResult::declaration_unavailable;
  }
  bool exact_choice = false;
  for (const auto &candidate : current_choices) {
    if (candidate == declaration) {
      exact_choice = true;
      break;
    }
  }
  if (!exact_choice) {
    ClearValidCasusBelliConfigurations(bindings);
    return DeclareWarResult::declaration_unavailable;
  }

  void *const interaction = ResolveCharacterInteraction(
      bindings, bindings.declare_war_interaction_offset);
  if (interaction == nullptr) {
    ClearValidCasusBelliConfigurations(bindings);
    return DeclareWarResult::unavailable;
  }

  CharacterInteractionContextStorage context_storage{};
  void *const context = context_storage.bytes.data();
  if (bindings.construct_character_interaction_context(
          context, interaction, current.played_character_id,
          declaration.target_character_id, nullptr, true) != context) {
    ClearValidCasusBelliConfigurations(bindings);
    return DeclareWarResult::unavailable;
  }
  void *const war_declaration = LoadAt<void *>(
      context, kCharacterInteractionSpecialDataOffset);
  if (war_declaration == nullptr ||
      LoadAt<std::uintptr_t>(war_declaration, 0) !=
          bindings.war_declaration_vtable) {
    ClearValidCasusBelliConfigurations(bindings);
    bindings.destroy_character_interaction_context(context);
    return DeclareWarResult::unavailable;
  }

  StoreAt(war_declaration, kWarDeclarationCasusBelliOffset,
          casus_belli_type);
  void *const native_target_titles =
      static_cast<std::byte *>(war_declaration) +
      kWarDeclarationTargetTitlesOffset;
  void *configuration_data = nullptr;
  std::int32_t configuration_count = 0;
  if (!ReadValidCasusBelliConfigurationArray(
          bindings, configuration_data, configuration_count)) {
    bindings.destroy_character_interaction_context(context);
    return DeclareWarResult::unavailable;
  }
  if (declaration.configuration_index >= 0) {
    if (declaration.configuration_index >= configuration_count) {
      ClearValidCasusBelliConfigurations(bindings);
      bindings.destroy_character_interaction_context(context);
      return DeclareWarResult::declaration_unavailable;
    }
    const auto *const configuration =
        static_cast<const std::byte *>(configuration_data) +
        static_cast<std::size_t>(declaration.configuration_index) *
            kValidCasusBelliConfigurationSize;
    bindings.copy_native_int_array(
        native_target_titles,
        configuration + kValidCasusBelliTargetTitlesOffset);
  } else {
    for (std::int32_t index = 0; index < configuration_count; ++index) {
      const auto *const configuration =
          static_cast<const std::byte *>(configuration_data) +
          static_cast<std::size_t>(index) *
              kValidCasusBelliConfigurationSize;
      const void *const source =
          configuration + kValidCasusBelliTargetTitlesOffset;
      const auto source_count =
          LoadAt<std::int32_t>(source, kNativeArrayCountOffset);
      const auto *const source_data =
          LoadAt<const std::int32_t *>(source, kNativeArrayDataOffset);
      if (source_count <= 0) {
        continue;
      }
      const auto destination_count = LoadAt<std::int32_t>(
          native_target_titles, kNativeArrayCountOffset);
      bindings.append_native_int_array_range(
          native_target_titles, destination_count, source_data,
          source_data + source_count);
    }
  }
  StoreAt(war_declaration, kWarDeclarationClaimantOffset,
          declaration.claimant_character_id);
  if (!ClearValidCasusBelliConfigurations(bindings)) {
    bindings.destroy_character_interaction_context(context);
    return DeclareWarResult::unavailable;
  }

  bindings.refresh_character_interaction_context(context, true);
  bindings.finalize_character_interaction_context(context);
  if (!bindings.validate_character_interaction_context(context, nullptr)) {
    bindings.destroy_character_interaction_context(context);
    return DeclareWarResult::validation_failed;
  }

  SendCharacterInteractionCommandStorage command_storage{};
  void *const command = command_storage.bytes.data();
  if (bindings.construct_send_character_interaction_command(command,
                                                             context) !=
          command ||
      LoadAt<std::uintptr_t>(command, 0) !=
          bindings.send_character_interaction_primary_vtable ||
      LoadAt<std::uintptr_t>(command, 0x18) !=
          bindings.send_character_interaction_secondary_vtable) {
    if (LoadAt<void *>(command,
                       kSendCharacterInteractionContextOffset) != nullptr) {
      bindings.destroy_character_interaction_context(
          static_cast<std::byte *>(command) +
          kSendCharacterInteractionContextOffset);
    }
    bindings.destroy_character_interaction_context(context);
    return DeclareWarResult::unavailable;
  }
  bindings.submit_command(bindings.command_manager, command, 0x0E);
  bindings.destroy_character_interaction_context(
      static_cast<std::byte *>(command) +
      kSendCharacterInteractionContextOffset);
  bindings.destroy_character_interaction_context(context);
  return DeclareWarResult::submitted;
}

ReadArrangeMarriageChoicesResult ReadArrangeMarriageChoices(
    const Bindings &bindings,
    std::vector<ArrangeMarriageChoice> &output,
    ArrangeMarriageQueryDiagnostics &diagnostics) noexcept {
  output.clear();
  diagnostics = {};
  if (!HasArrangeMarriageReadBindings(bindings)) {
    return ReadArrangeMarriageChoicesResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return ReadArrangeMarriageChoicesResult::unavailable;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return ReadArrangeMarriageChoicesResult::no_played_character;
  }
  if (ResolveCharacterInteraction(
          bindings, bindings.arrange_marriage_interaction_offset) ==
      nullptr) {
    return ReadArrangeMarriageChoicesResult::unavailable;
  }
  void *const played_character =
      ResolveCharacter(bindings, current.played_character_id);
  void *const storage = *bindings.character_storage_slot;
  if (played_character == nullptr || storage == nullptr) {
    return ReadArrangeMarriageChoicesResult::unavailable;
  }
  void *const slots = LoadAt<void *>(storage, kComponentStorageSlotsOffset);
  const auto capacity =
      LoadAt<std::int32_t>(storage, kComponentStorageCapacityOffset);
  diagnostics.storage_capacity = capacity;
  if (slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentCapacity) {
    return ReadArrangeMarriageChoicesResult::unavailable;
  }

  std::vector<ArrangeMarriageChoice> choices;
  for (std::int32_t index = 0; index < capacity; ++index) {
    ++diagnostics.slots_scanned;
    void *const candidate_character = LoadAt<void *>(
        slots, static_cast<std::size_t>(index) *
                       kComponentStorageSlotSize +
                   kComponentStorageSlotObjectOffset);
    if (candidate_character == nullptr) {
      ++diagnostics.empty_slots;
      continue;
    }
    if (candidate_character == played_character) {
      ++diagnostics.self_candidates;
      continue;
    }
    if (LoadAt<void *>(candidate_character, kCharacterDeathDataOffset) !=
        nullptr) {
      ++diagnostics.dead_candidates;
      continue;
    }
    const auto candidate_character_id =
        LoadAt<std::int32_t>(candidate_character, kCharacterIdOffset);
    if ((static_cast<std::uint32_t>(candidate_character_id) &
         0x00FFFFFFU) != static_cast<std::uint32_t>(index)) {
      ++diagnostics.generation_mismatch_candidates;
      continue;
    }
    ++diagnostics.live_candidates;

    CharacterInteractionContextStorage context_storage{};
    void *const context = context_storage.bytes.data();
    ArrangeMarriageValidationSample sample{};
    sample.slot_index = index;
    sample.candidate_character_id = candidate_character_id;
    if (!PrepareArrangeMarriageContext(
            bindings, current.played_character_id,
            candidate_character_id, context_storage, &sample)) {
      ++diagnostics.context_construct_failures;
      return ReadArrangeMarriageChoicesResult::unavailable;
    }
    ++diagnostics.contexts_constructed;
    const bool available =
        bindings.validate_character_interaction_context(context, nullptr);
    bindings.destroy_character_interaction_context(context);
    if (!available) {
      ++diagnostics.native_validate_false;
      if (diagnostics.validation_false_samples.size() <
          kMaximumMarriageValidationSamples) {
        diagnostics.validation_false_samples.push_back(sample);
      }
      continue;
    }
    ++diagnostics.native_validate_true;
    choices.push_back(
        {current.played_character_id, candidate_character_id});
  }
  output = std::move(choices);
  return ReadArrangeMarriageChoicesResult::available;
}

ArrangeMarriageResult SubmitArrangeMarriage(
    const Bindings &bindings,
    const ArrangeMarriageChoice &choice) noexcept {
  if (!HasArrangeMarriageReadBindings(bindings) ||
      bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.construct_send_character_interaction_command == nullptr ||
      bindings.send_character_interaction_primary_vtable == 0 ||
      bindings.send_character_interaction_secondary_vtable == 0) {
    return ArrangeMarriageResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return ArrangeMarriageResult::unavailable;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return ArrangeMarriageResult::no_played_character;
  }
  if (choice.played_character_id != current.played_character_id ||
      choice.candidate_character_id == current.played_character_id) {
    return ArrangeMarriageResult::choice_unavailable;
  }
  void *const candidate_character =
      ResolveCharacter(bindings, choice.candidate_character_id);
  if (candidate_character == nullptr ||
      LoadAt<void *>(candidate_character, kCharacterDeathDataOffset) !=
          nullptr) {
    return ArrangeMarriageResult::candidate_not_found;
  }

  CharacterInteractionContextStorage context_storage{};
  void *const context = context_storage.bytes.data();
  if (!PrepareArrangeMarriageContext(
          bindings, choice.played_character_id,
          choice.candidate_character_id, context_storage)) {
    return ArrangeMarriageResult::unavailable;
  }
  if (!bindings.validate_character_interaction_context(context, nullptr)) {
    bindings.destroy_character_interaction_context(context);
    return ArrangeMarriageResult::choice_unavailable;
  }

  SendCharacterInteractionCommandStorage command_storage{};
  void *const command = command_storage.bytes.data();
  if (bindings.construct_send_character_interaction_command(command,
                                                             context) !=
          command ||
      LoadAt<std::uintptr_t>(command, 0) !=
          bindings.send_character_interaction_primary_vtable ||
      LoadAt<std::uintptr_t>(command, 0x18) !=
          bindings.send_character_interaction_secondary_vtable) {
    if (LoadAt<void *>(command,
                       kSendCharacterInteractionContextOffset) != nullptr) {
      bindings.destroy_character_interaction_context(
          static_cast<std::byte *>(command) +
          kSendCharacterInteractionContextOffset);
    }
    bindings.destroy_character_interaction_context(context);
    return ArrangeMarriageResult::unavailable;
  }
  bindings.submit_command(bindings.command_manager, command, 0x0E);
  bindings.destroy_character_interaction_context(
      static_cast<std::byte *>(command) +
      kSendCharacterInteractionContextOffset);
  bindings.destroy_character_interaction_context(context);
  return ArrangeMarriageResult::submitted;
}

ReadWarTerminationOptionsResult ReadWarTerminationOptions(
    const Bindings &bindings, std::int32_t war_id,
    WarTerminationOptionsSnapshot &output) noexcept {
  output = {};
  if (!HasWarTerminationQueryBindings(bindings)) {
    return ReadWarTerminationOptionsResult::unavailable;
  }

  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return ReadWarTerminationOptionsResult::unavailable;
  }
  if (!current.paused) {
    return ReadWarTerminationOptionsResult::requires_paused;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return ReadWarTerminationOptionsResult::no_played_character;
  }

  void *const game_state = *bindings.game_state_slot;
  void *const war = ResolveWar(bindings, game_state, war_id);
  if (war == nullptr) {
    return ReadWarTerminationOptionsResult::war_not_found;
  }
  void *const attackers =
      static_cast<std::byte *>(war) + kWarAttackersOffset;
  void *const defenders =
      static_cast<std::byte *>(war) + kWarDefendersOffset;
  const bool player_is_attacker = bindings.contains_war_participant(
      attackers, current.played_character_id);
  const bool player_is_defender = bindings.contains_war_participant(
      defenders, current.played_character_id);
  if (!player_is_attacker && !player_is_defender) {
    return ReadWarTerminationOptionsResult::player_not_participant;
  }
  if (player_is_attacker && player_is_defender) {
    return ReadWarTerminationOptionsResult::unavailable;
  }

  const auto published_war = std::find_if(
      current.active_wars.begin(), current.active_wars.end(),
      [war_id](const ActiveWarSnapshot &candidate) {
        return candidate.war_id == war_id;
      });
  if (published_war == current.active_wars.end() ||
      (published_war->player_side == PlayerWarSide::attacker) !=
          player_is_attacker) {
    return ReadWarTerminationOptionsResult::unavailable;
  }

  output.war_id = war_id;
  output.player_side = published_war->player_side;
  output.player_is_primary_war_leader =
      published_war->player_is_primary_war_leader;
  output.player_relative_war_score =
      published_war->player_relative_war_score;
  const std::int64_t duration_raw =
      static_cast<std::int64_t>(current.date_raw) -
      LoadAt<std::int32_t>(war, kWarStartDateRawOffset);
  const std::int64_t duration_days = duration_raw / 24;
  if (duration_raw >= 0 &&
      duration_days <= std::numeric_limits<std::int32_t>::max()) {
    output.war_duration_days_observable = true;
    output.war_duration_days = static_cast<std::int32_t>(duration_days);
  }
  const auto attacker_war_score = bindings.get_war_score(war, nullptr);
  if (attacker_war_score != std::numeric_limits<std::int32_t>::min()) {
    output.absolute_war_scores_observable = true;
    output.attacker_war_score = attacker_war_score;
    output.defender_war_score = -attacker_war_score;
  }
  if (!output.absolute_war_scores_observable ||
      output.player_relative_war_score !=
          (player_is_attacker ? output.attacker_war_score
                              : output.defender_war_score)) {
    output = {};
    return ReadWarTerminationOptionsResult::unavailable;
  }
  ReadWarScoreBreakdown(bindings, war, output.war_score_breakdown);
  output.surrender.outcome = player_is_attacker ? "attacker_defeat"
                                                : "attacker_victory";
  output.white_peace.outcome = "white_peace";
  output.victory.outcome = player_is_attacker ? "attacker_victory"
                                              : "attacker_defeat";

  void *const active_casus_belli_type =
      LoadAt<void *>(war, kWarActiveCasusBelliTypeOffset);
  output.active_casus_belli_observable = true;
  output.active_casus_belli_present = active_casus_belli_type != nullptr;
  if (active_casus_belli_type != nullptr) {
    const auto database_index = LoadAt<std::int32_t>(
        active_casus_belli_type, kCasusBelliTypeDatabaseIndexOffset);
    std::string casus_belli_key;
    if (database_index >= 0 && database_index < kMaximumCasusBelliTypes &&
        ReadCasusBelliTypeKey(active_casus_belli_type, casus_belli_key)) {
      output.active_casus_belli_identity_observable = true;
      output.active_casus_belli_database_index = database_index;
      output.active_casus_belli_key = std::move(casus_belli_key);
    }
    output.white_peace_permission_observable = true;
    const auto flags = LoadAt<std::uint32_t>(
        active_casus_belli_type, kCasusBelliTypeFlagsOffset);
    output.cb_allows_white_peace =
        (flags & kCasusBelliWhitePeacePossibleFlag) != 0;
  }

  if (!output.player_is_primary_war_leader) {
    return ReadWarTerminationOptionsResult::available;
  }
  // 0xC569F0's boolean is an absolute outcome, not "concede own side":
  // true = attacker victory, false = attacker defeat.
  if (!EvaluateWarResolutionContext(bindings, war, !player_is_attacker,
                                    output.surrender) ||
      !EvaluateWarResolutionContext(bindings, war, player_is_attacker,
                                    output.victory)) {
    output = {};
    return ReadWarTerminationOptionsResult::unavailable;
  }
  if (output.white_peace_permission_observable &&
      output.cb_allows_white_peace &&
      published_war->primary_opponent_character_id != -1 &&
      !EvaluateWhitePeaceContext(
          bindings, current.played_character_id,
          published_war->primary_opponent_character_id,
          output.white_peace)) {
    output = {};
    return ReadWarTerminationOptionsResult::unavailable;
  }
  return ReadWarTerminationOptionsResult::available;
}

ReadWarTerminationTermsResult ReadWarTerminationTerms(
    const Bindings &bindings, std::int32_t war_id,
    WarTerminationTermsSnapshot &output) noexcept {
  output = {};
  if (!HasWarTerminationTermsBindings(bindings)) {
    return ReadWarTerminationTermsResult::unavailable;
  }

  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return ReadWarTerminationTermsResult::unavailable;
  }
  if (!current.paused) {
    return ReadWarTerminationTermsResult::requires_paused;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return ReadWarTerminationTermsResult::no_played_character;
  }

  void *const game_state = *bindings.game_state_slot;
  void *const war = ResolveWar(bindings, game_state, war_id);
  if (war == nullptr) {
    return ReadWarTerminationTermsResult::war_not_found;
  }
  void *const attackers =
      static_cast<std::byte *>(war) + kWarAttackersOffset;
  void *const defenders =
      static_cast<std::byte *>(war) + kWarDefendersOffset;
  const bool player_is_attacker = bindings.contains_war_participant(
      attackers, current.played_character_id);
  const bool player_is_defender = bindings.contains_war_participant(
      defenders, current.played_character_id);
  if (!player_is_attacker && !player_is_defender) {
    return ReadWarTerminationTermsResult::player_not_participant;
  }
  if (player_is_attacker && player_is_defender) {
    return ReadWarTerminationTermsResult::unavailable;
  }
  const auto published_war = std::find_if(
      current.active_wars.begin(), current.active_wars.end(),
      [war_id](const ActiveWarSnapshot &candidate) {
        return candidate.war_id == war_id;
      });
  if (published_war == current.active_wars.end()) {
    return ReadWarTerminationTermsResult::unavailable;
  }

  void *const casus_belli_type =
      LoadAt<void *>(war, kWarActiveCasusBelliTypeOffset);
  if (casus_belli_type == nullptr) {
    return ReadWarTerminationTermsResult::unavailable;
  }
  const auto casus_belli_database_index = LoadAt<std::int32_t>(
      casus_belli_type, kCasusBelliTypeDatabaseIndexOffset);
  std::string casus_belli_key;
  if (casus_belli_database_index < 0 ||
      casus_belli_database_index >= kMaximumCasusBelliTypes ||
      !ReadCasusBelliTypeKey(casus_belli_type, casus_belli_key) ||
      casus_belli_key.empty()) {
    return ReadWarTerminationTermsResult::unavailable;
  }
  output.war_id = war_id;
  output.active_casus_belli_database_index = casus_belli_database_index;
  output.active_casus_belli_key = casus_belli_key;
  if (casus_belli_key != "claim_cb") {
    if (ResolveWar(bindings, game_state, war_id) != war ||
        LoadAt<void *>(war, kWarActiveCasusBelliTypeOffset) !=
            casus_belli_type) {
      output = {};
      return ReadWarTerminationTermsResult::unavailable;
    }
    return ReadWarTerminationTermsResult::unsupported_casus_belli;
  }

  const auto claimant_character_id =
      LoadAt<std::int32_t>(war, kWarClaimantCharacterIdOffset);
  void *const claimant =
      ResolveTermsCharacter(bindings, claimant_character_id);
  if (claimant == nullptr) {
    output = {};
    return ReadWarTerminationTermsResult::unavailable;
  }
  std::vector<std::int32_t> target_title_ids;
  if (!ReadNativeIntArray(
          static_cast<std::byte *>(war) + kWarTargetedTitleIdsOffset,
          target_title_ids, kMaximumWarObjectiveTitleIds) ||
      target_title_ids.empty()) {
    output = {};
    return ReadWarTerminationTermsResult::unavailable;
  }

  std::vector<void *> titles;
  titles.reserve(target_title_ids.size());
  for (const auto title_id : target_title_ids) {
    if (std::find(output.target_title_ids.begin(),
                  output.target_title_ids.end(), title_id) !=
        output.target_title_ids.end()) {
      output = {};
      return ReadWarTerminationTermsResult::unavailable;
    }
    void *const title = ResolveLandedTitle(bindings, game_state, title_id);
    if (title == nullptr) {
      output = {};
      return ReadWarTerminationTermsResult::unavailable;
    }
    output.target_title_ids.push_back(title_id);
    titles.push_back(title);
  }

  output.claimant_character_id = claimant_character_id;
  output.claims.reserve(output.target_title_ids.size());
  for (std::size_t index = 0; index < output.target_title_ids.size();
       ++index) {
    game::WarClaimSnapshot claim{};
    if (!ReadWarClaimRow(bindings, claimant, titles[index],
                         output.target_title_ids[index], claim) ||
        ResolveTermsCharacter(bindings, claimant_character_id) != claimant ||
        ResolveLandedTitle(bindings, game_state,
                           output.target_title_ids[index]) != titles[index]) {
      output = {};
      return ReadWarTerminationTermsResult::unavailable;
    }
    output.claims.push_back(std::move(claim));
  }

  std::vector<std::int32_t> target_title_ids_after;
  std::string casus_belli_key_after;
  Snapshot after{};
  if (ResolveWar(bindings, game_state, war_id) != war ||
      LoadAt<void *>(war, kWarActiveCasusBelliTypeOffset) !=
          casus_belli_type ||
      LoadAt<std::int32_t>(
          casus_belli_type, kCasusBelliTypeDatabaseIndexOffset) !=
          casus_belli_database_index ||
      !ReadCasusBelliTypeKey(casus_belli_type, casus_belli_key_after) ||
      casus_belli_key_after != casus_belli_key ||
      LoadAt<std::int32_t>(war, kWarClaimantCharacterIdOffset) !=
          claimant_character_id ||
      ResolveTermsCharacter(bindings, claimant_character_id) != claimant ||
      !ReadNativeIntArray(
          static_cast<std::byte *>(war) + kWarTargetedTitleIdsOffset,
          target_title_ids_after, kMaximumWarObjectiveTitleIds) ||
      target_title_ids_after != output.target_title_ids ||
      !ReadSnapshot(bindings, after) || !after.paused ||
      after.date_raw != current.date_raw ||
      after.played_character_id != current.played_character_id ||
      std::none_of(after.active_wars.begin(), after.active_wars.end(),
                   [war_id](const ActiveWarSnapshot &candidate) {
                     return candidate.war_id == war_id;
                   })) {
    output = {};
    return ReadWarTerminationTermsResult::unavailable;
  }

  output.attacker_victory.declared_title_disposition =
      "transfer_to_claimant_via_conquest_claim";
  output.attacker_victory.claim_disposition =
      "resolve_with_add_claim_on_loss";
  output.white_peace.declared_title_disposition = "unchanged";
  output.white_peace.claim_disposition = "retain_and_strengthen_weak";
  output.attacker_defeat.declared_title_disposition = "unchanged";
  output.attacker_defeat.claim_disposition =
      "remove_declared_target_claims";
  return ReadWarTerminationTermsResult::available;
}

ReadWarTerminationExitTermsResult ReadWarTerminationExitTerms(
    const Bindings &, std::int32_t,
    WarTerminationExitTermsSnapshot &output) noexcept {
  output = {};
  g_last_war_termination_exit_terms_unavailable_reason =
      "loaded_effect_preview_disabled_after_live_crash_rva_0x334C668";
  return ReadWarTerminationExitTermsResult::unavailable;
}

#if defined(XAR_CK3_WAR_EXIT_TERMS_OFFLINE_RE_TEST)
ReadWarTerminationExitTermsResult
ReadWarTerminationExitTermsForOfflineReFixture(
    const Bindings &bindings, std::int32_t war_id,
    WarTerminationExitTermsSnapshot &output) noexcept {
  output = {};
  g_last_war_termination_exit_terms_unavailable_reason = {};
  const auto unavailable = [&output](std::string_view reason) noexcept {
    output = {};
    g_last_war_termination_exit_terms_unavailable_reason = reason;
    return ReadWarTerminationExitTermsResult::unavailable;
  };
  if (!HasWarTerminationExitTermsBindings(bindings)) {
    return unavailable("bindings");
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return unavailable("initial_snapshot");
  }
  if (!current.paused) {
    return ReadWarTerminationExitTermsResult::requires_paused;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return ReadWarTerminationExitTermsResult::no_played_character;
  }

  void *const game_state = *bindings.game_state_slot;
  void *const war = ResolveWar(bindings, game_state, war_id);
  if (war == nullptr) {
    return ReadWarTerminationExitTermsResult::war_not_found;
  }
  void *const attackers =
      static_cast<std::byte *>(war) + kWarAttackersOffset;
  void *const defenders =
      static_cast<std::byte *>(war) + kWarDefendersOffset;
  const bool player_is_attacker = bindings.contains_war_participant(
      attackers, current.played_character_id);
  const bool player_is_defender = bindings.contains_war_participant(
      defenders, current.played_character_id);
  if (!player_is_attacker && !player_is_defender) {
    return ReadWarTerminationExitTermsResult::player_not_participant;
  }
  if (!player_is_attacker || player_is_defender ||
      LoadAt<std::int32_t>(war, kWarPrimaryAttackerCharacterIdOffset) !=
          current.played_character_id) {
    return ReadWarTerminationExitTermsResult::player_not_primary_attacker;
  }

  const auto attacker_id = LoadAt<std::int32_t>(
      war, kWarPrimaryAttackerCharacterIdOffset);
  const auto defender_id = LoadAt<std::int32_t>(
      war, kWarPrimaryDefenderCharacterIdOffset);
  void *const attacker = ResolveTermsCharacter(bindings, attacker_id);
  void *const defender = ResolveTermsCharacter(bindings, defender_id);
  if (attacker == nullptr || defender == nullptr || attacker == defender) {
    return unavailable("primary_character_resolution");
  }

  WarTerminationTermsSnapshot claims_before{};
  const auto claim_result =
      ReadWarTerminationTerms(bindings, war_id, claims_before);
  if (claim_result == ReadWarTerminationTermsResult::unsupported_casus_belli) {
    return ReadWarTerminationExitTermsResult::unsupported_casus_belli;
  }
  if (claim_result != ReadWarTerminationTermsResult::available ||
      claims_before.active_casus_belli_key != "claim_cb" ||
      claims_before.claims.empty() ||
      std::any_of(claims_before.claims.begin(), claims_before.claims.end(),
                  [](const game::WarClaimSnapshot &claim) {
                    return !claim.present;
                  })) {
    return unavailable("claim_disposition_slice");
  }
  void *const casus_belli =
      LoadAt<void *>(war, kWarActiveCasusBelliTypeOffset);
  const auto factor_identifier_id =
      *bindings.cb_prestige_factor_identifier_id;
  if (casus_belli == nullptr || factor_identifier_id < 0) {
    return unavailable("casus_belli_or_factor_identifier");
  }

  output.war_id = war_id;
  output.date_raw = current.date_raw;
  output.active_casus_belli_database_index =
      claims_before.active_casus_belli_database_index;
  output.active_casus_belli_key = claims_before.active_casus_belli_key;
  output.primary_attacker_character_id = attacker_id;
  output.primary_defender_character_id = defender_id;
  output.claimant_character_id = claims_before.claimant_character_id;
  output.target_title_ids = claims_before.target_title_ids;
  output.claims = claims_before.claims;

  if (!ReadPrimaryExitResources(
          bindings, attacker, attacker_id, defender, defender_id,
          output.primary_resource_balances,
          output.primary_monthly_gold_income)) {
    const auto reason =
        g_last_war_termination_exit_terms_unavailable_reason.empty()
            ? std::string_view{"primary_resources"}
            : g_last_war_termination_exit_terms_unavailable_reason;
    return unavailable(reason);
  }
  std::vector<game::WarExitPrisonerReleaseSnapshot> prisoners_before;
  if (!ReadWarExitPrisonerReleases(
          bindings, game_state, war, attacker, attacker_id, defender,
          defender_id, prisoners_before)) {
    return unavailable("prisoner_releases");
  }

  WarEffectContextStorage effect_context_storage{};
  void *const effect_context = effect_context_storage.bytes.data();
  if (bindings.construct_war_effect_context(effect_context) != effect_context) {
    return unavailable("effect_context_construct");
  }
  bindings.populate_war_effect_context(effect_context, war, false);
  std::vector<WarExitPreviewRow> white_peace_rows;
  std::vector<WarExitPreviewRow> attacker_defeat_rows;
  std::int64_t white_peace_factor_raw = 0;
  std::int64_t attacker_defeat_factor_raw = 0;
  std::array<std::int32_t, 12> white_peace_counts{};
  std::array<std::int32_t, 12> attacker_defeat_counts{};
  std::string_view preview_failure{};
  if (!DryPreviewWarExitEffect(
          bindings,
          static_cast<std::byte *>(casus_belli) +
              kWarEffectWhitePeaceOffset,
          effect_context, WarExitPreviewOutcome::white_peace,
          factor_identifier_id, attacker_id, defender_id,
          white_peace_rows, white_peace_factor_raw)) {
    preview_failure = g_last_war_exit_preview_unavailable_reason.empty()
                          ? std::string_view{"white_peace_effect_preview"}
                          : g_last_war_exit_preview_unavailable_reason;
  } else if (!MaterializeWarExitPreview(
                 bindings, white_peace_rows, effect_context, attacker_id,
                 defender_id, current.date_raw, true, output.white_peace,
                 white_peace_counts)) {
    preview_failure = g_last_war_exit_preview_unavailable_reason.empty()
                          ? std::string_view{"white_peace_effect_materialize"}
                          : g_last_war_exit_preview_unavailable_reason;
  } else if (!DryPreviewWarExitEffect(
                 bindings,
                 static_cast<std::byte *>(casus_belli) +
                     kWarEffectAttackerDefeatOffset,
                 effect_context, WarExitPreviewOutcome::attacker_defeat,
                 factor_identifier_id, attacker_id,
                 defender_id, attacker_defeat_rows,
                 attacker_defeat_factor_raw)) {
    preview_failure = g_last_war_exit_preview_unavailable_reason.empty()
                          ? std::string_view{"attacker_defeat_effect_preview"}
                          : g_last_war_exit_preview_unavailable_reason;
  } else if (!MaterializeWarExitPreview(
                 bindings, attacker_defeat_rows, effect_context, attacker_id,
                 defender_id, current.date_raw, false,
                 output.attacker_defeat, attacker_defeat_counts)) {
    preview_failure = g_last_war_exit_preview_unavailable_reason.empty()
                          ? std::string_view{"attacker_defeat_effect_materialize"}
                          : g_last_war_exit_preview_unavailable_reason;
  }
  const bool context_destroyed =
      DestroyWarEffectContext(bindings, effect_context);
  if (!context_destroyed) {
    return unavailable("effect_context_destroy");
  }
  if (!preview_failure.empty()) {
    return unavailable(preview_failure);
  }
  if (!FinalizeWarExitPrestigeFactor(
          output.white_peace, white_peace_counts, output.attacker_defeat,
          attacker_defeat_counts, white_peace_factor_raw,
          attacker_defeat_factor_raw)) {
    return unavailable("prestige_factor_crosscheck");
  }

  const bool any_weak_claim = std::any_of(
      output.claims.begin(), output.claims.end(),
      [](const game::WarClaimSnapshot &claim) { return !claim.strong; });
  output.white_peace.claim_disposition.declared_title_disposition =
      "unchanged";
  output.white_peace.claim_disposition.claim_disposition =
      any_weak_claim ? "retain_and_strengthen_weak"
                     : "retain_no_strength_change_already_strong";
  output.attacker_defeat.claim_disposition.declared_title_disposition =
      "unchanged";
  output.attacker_defeat.claim_disposition.claim_disposition =
      "remove_declared_target_claims";
  output.white_peace.prisoner_releases = prisoners_before;
  output.attacker_defeat.prisoner_releases = prisoners_before;

  if (!EvaluateWarExitWhitePeaceRecipient(
          bindings, attacker_id, defender_id,
          output.white_peace.recipient_response)) {
    return unavailable("white_peace_recipient_response");
  }
  if (!EvaluateWarExitDefeatRecipient(
          bindings, war, output.attacker_defeat.recipient_response)) {
    return unavailable("attacker_defeat_recipient_response");
  }

  std::vector<game::WarExitResourceSnapshot> balances_after;
  std::vector<game::WarExitCharacterFixedPointSnapshot> income_after;
  std::vector<game::WarExitPrisonerReleaseSnapshot> prisoners_after;
  WarTerminationTermsSnapshot claims_after{};
  Snapshot after{};
  if (!ReadPrimaryExitResources(bindings, attacker, attacker_id, defender,
                                defender_id, balances_after, income_after) ||
      balances_after != output.primary_resource_balances ||
      income_after != output.primary_monthly_gold_income ||
      !ReadWarExitPrisonerReleases(
          bindings, game_state, war, attacker, attacker_id, defender,
          defender_id, prisoners_after) ||
      prisoners_after != prisoners_before ||
      ReadWarTerminationTerms(bindings, war_id, claims_after) !=
          ReadWarTerminationTermsResult::available ||
      claims_after != claims_before || !ReadSnapshot(bindings, after) ||
      !after.paused || after.date_raw != current.date_raw ||
      after.played_character_id != current.played_character_id ||
      ResolveWar(bindings, game_state, war_id) != war ||
      LoadAt<void *>(war, kWarActiveCasusBelliTypeOffset) != casus_belli ||
      *bindings.cb_prestige_factor_identifier_id != factor_identifier_id ||
      LoadAt<std::int32_t>(war, kWarPrimaryAttackerCharacterIdOffset) !=
          attacker_id ||
      LoadAt<std::int32_t>(war, kWarPrimaryDefenderCharacterIdOffset) !=
          defender_id ||
      ResolveTermsCharacter(bindings, attacker_id) != attacker ||
      ResolveTermsCharacter(bindings, defender_id) != defender) {
    return unavailable("same_frame_stability");
  }

  output.same_frame_stable = true;
  output.claim_temporary_lifecycle_verified = true;
  output.exit_terms_ready = true;
  return ReadWarTerminationExitTermsResult::available;
}
#endif

SurrenderWarResult SubmitSurrenderWar(const Bindings &bindings,
                                      std::int32_t war_id) noexcept {
  if (!HasWarTerminationQueryBindings(bindings) ||
      bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.construct_send_character_interaction_command == nullptr ||
      bindings.send_character_interaction_primary_vtable == 0 ||
      bindings.send_character_interaction_secondary_vtable == 0) {
    return SurrenderWarResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return SurrenderWarResult::unavailable;
  }
  if (!current.paused) {
    return SurrenderWarResult::requires_paused;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return SurrenderWarResult::no_played_character;
  }
  void *const game_state = *bindings.game_state_slot;
  void *const war = ResolveWar(bindings, game_state, war_id);
  if (war == nullptr) {
    return SurrenderWarResult::war_not_found;
  }
  void *const attackers =
      static_cast<std::byte *>(war) + kWarAttackersOffset;
  void *const defenders =
      static_cast<std::byte *>(war) + kWarDefendersOffset;
  if (!bindings.contains_war_participant(
          attackers, current.played_character_id) &&
      !bindings.contains_war_participant(
          defenders, current.played_character_id)) {
    return SurrenderWarResult::player_not_participant;
  }
  const bool player_is_primary_attacker =
      LoadAt<std::int32_t>(war, kWarPrimaryAttackerCharacterIdOffset) ==
      current.played_character_id;
  const bool player_is_primary_defender =
      LoadAt<std::int32_t>(war, kWarPrimaryDefenderCharacterIdOffset) ==
      current.played_character_id;
  if (!player_is_primary_attacker && !player_is_primary_defender) {
    return SurrenderWarResult::player_not_war_leader;
  }
  if (player_is_primary_attacker && player_is_primary_defender) {
    return SurrenderWarResult::unavailable;
  }

  CharacterInteractionContextStorage context_storage{};
  void *const context = context_storage.bytes.data();
  if (bindings.default_construct_character_interaction_context(context) !=
      context) {
    return SurrenderWarResult::unavailable;
  }
  bindings.construct_war_resolution_interaction_context(
      context, war, player_is_primary_defender);
  if (LoadAt<void *>(context, kCharacterInteractionSpecialDataOffset) ==
      nullptr) {
    bindings.destroy_character_interaction_context(context);
    return SurrenderWarResult::context_unavailable;
  }
  if (!bindings.validate_character_interaction_context(context, nullptr)) {
    bindings.destroy_character_interaction_context(context);
    return SurrenderWarResult::validation_failed;
  }

  SendCharacterInteractionCommandStorage command_storage{};
  void *const command = command_storage.bytes.data();
  if (bindings.construct_send_character_interaction_command(command,
                                                             context) !=
          command ||
      LoadAt<std::uintptr_t>(command, 0) !=
          bindings.send_character_interaction_primary_vtable ||
      LoadAt<std::uintptr_t>(command, 0x18) !=
          bindings.send_character_interaction_secondary_vtable) {
    if (LoadAt<void *>(command,
                       kSendCharacterInteractionContextOffset) != nullptr) {
      bindings.destroy_character_interaction_context(
          static_cast<std::byte *>(command) +
          kSendCharacterInteractionContextOffset);
    }
    bindings.destroy_character_interaction_context(context);
    return SurrenderWarResult::unavailable;
  }
  const bool submitted =
      bindings.submit_command(bindings.command_manager, command, 0x0E);
  bindings.destroy_character_interaction_context(
      static_cast<std::byte *>(command) +
      kSendCharacterInteractionContextOffset);
  bindings.destroy_character_interaction_context(context);
  return submitted ? SurrenderWarResult::submitted
                   : SurrenderWarResult::submission_failed;
}

OfferWhitePeaceResult SubmitOfferWhitePeace(const Bindings &bindings,
                                            std::int32_t war_id) noexcept {
  if (!HasWarTerminationQueryBindings(bindings) ||
      bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.construct_send_character_interaction_command == nullptr ||
      bindings.send_character_interaction_primary_vtable == 0 ||
      bindings.send_character_interaction_secondary_vtable == 0) {
    return OfferWhitePeaceResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return OfferWhitePeaceResult::unavailable;
  }
  if (!current.paused) {
    return OfferWhitePeaceResult::requires_paused;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return OfferWhitePeaceResult::no_played_character;
  }
  void *const game_state = *bindings.game_state_slot;
  void *const war = ResolveWar(bindings, game_state, war_id);
  if (war == nullptr) {
    return OfferWhitePeaceResult::war_not_found;
  }
  void *const attackers =
      static_cast<std::byte *>(war) + kWarAttackersOffset;
  void *const defenders =
      static_cast<std::byte *>(war) + kWarDefendersOffset;
  const bool player_is_attacker = bindings.contains_war_participant(
      attackers, current.played_character_id);
  const bool player_is_defender = bindings.contains_war_participant(
      defenders, current.played_character_id);
  if (!player_is_attacker && !player_is_defender) {
    return OfferWhitePeaceResult::player_not_participant;
  }
  if (player_is_attacker && player_is_defender) {
    return OfferWhitePeaceResult::unavailable;
  }
  const auto primary_attacker_character_id = LoadAt<std::int32_t>(
      war, kWarPrimaryAttackerCharacterIdOffset);
  const auto primary_defender_character_id = LoadAt<std::int32_t>(
      war, kWarPrimaryDefenderCharacterIdOffset);
  const bool player_is_primary_attacker =
      primary_attacker_character_id == current.played_character_id;
  const bool player_is_primary_defender =
      primary_defender_character_id == current.played_character_id;
  if (!player_is_primary_attacker && !player_is_primary_defender) {
    return OfferWhitePeaceResult::player_not_war_leader;
  }
  if (player_is_primary_attacker && player_is_primary_defender) {
    return OfferWhitePeaceResult::unavailable;
  }
  const auto recipient_character_id = player_is_primary_attacker
                                          ? primary_defender_character_id
                                          : primary_attacker_character_id;
  if (ResolveTermsCharacter(bindings, recipient_character_id) == nullptr) {
    return OfferWhitePeaceResult::unavailable;
  }

  void *const casus_belli_type =
      LoadAt<void *>(war, kWarActiveCasusBelliTypeOffset);
  if (casus_belli_type == nullptr) {
    return OfferWhitePeaceResult::casus_belli_unavailable;
  }
  const auto casus_belli_flags = LoadAt<std::uint32_t>(
      casus_belli_type, kCasusBelliTypeFlagsOffset);
  if ((casus_belli_flags & kCasusBelliWhitePeacePossibleFlag) == 0) {
    return OfferWhitePeaceResult::white_peace_not_allowed;
  }

  CharacterInteractionContextStorage context_storage{};
  void *const context = context_storage.bytes.data();
  constexpr std::uint8_t kWhitePeaceSpecialInteractionIndex = 3;
  if (bindings.construct_special_character_interaction_context(
          context, kWhitePeaceSpecialInteractionIndex,
          current.played_character_id, recipient_character_id) != context) {
    return OfferWhitePeaceResult::unavailable;
  }
  if (LoadAt<void *>(context, kCharacterInteractionSpecialDataOffset) ==
      nullptr) {
    bindings.destroy_character_interaction_context(context);
    return OfferWhitePeaceResult::context_unavailable;
  }
  if (!bindings.validate_character_interaction_context(context, nullptr)) {
    bindings.destroy_character_interaction_context(context);
    return OfferWhitePeaceResult::validation_failed;
  }
  if (ResolveWar(bindings, game_state, war_id) != war ||
      LoadAt<std::int32_t>(war, kWarPrimaryAttackerCharacterIdOffset) !=
          primary_attacker_character_id ||
      LoadAt<std::int32_t>(war, kWarPrimaryDefenderCharacterIdOffset) !=
          primary_defender_character_id ||
      ResolveTermsCharacter(bindings, recipient_character_id) == nullptr ||
      LoadAt<void *>(war, kWarActiveCasusBelliTypeOffset) !=
          casus_belli_type ||
      LoadAt<std::uint32_t>(casus_belli_type,
                            kCasusBelliTypeFlagsOffset) !=
          casus_belli_flags) {
    bindings.destroy_character_interaction_context(context);
    return OfferWhitePeaceResult::unavailable;
  }

  SendCharacterInteractionCommandStorage command_storage{};
  void *const command = command_storage.bytes.data();
  if (bindings.construct_send_character_interaction_command(command,
                                                             context) !=
          command ||
      LoadAt<std::uintptr_t>(command, 0) !=
          bindings.send_character_interaction_primary_vtable ||
      LoadAt<std::uintptr_t>(command, 0x18) !=
          bindings.send_character_interaction_secondary_vtable) {
    if (LoadAt<void *>(command,
                       kSendCharacterInteractionContextOffset) != nullptr) {
      bindings.destroy_character_interaction_context(
          static_cast<std::byte *>(command) +
          kSendCharacterInteractionContextOffset);
    }
    bindings.destroy_character_interaction_context(context);
    return OfferWhitePeaceResult::unavailable;
  }
  const bool submitted =
      bindings.submit_command(bindings.command_manager, command, 0x0E);
  bindings.destroy_character_interaction_context(
      static_cast<std::byte *>(command) +
      kSendCharacterInteractionContextOffset);
  bindings.destroy_character_interaction_context(context);
  return submitted ? OfferWhitePeaceResult::submitted
                   : OfferWhitePeaceResult::submission_failed;
}

EnforceDemandsResult SubmitEnforceDemands(const Bindings &bindings,
                                          std::int32_t war_id) noexcept {
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.contains_war_participant == nullptr ||
      bindings.default_construct_character_interaction_context == nullptr ||
      bindings.construct_war_resolution_interaction_context == nullptr ||
      bindings.validate_character_interaction_context == nullptr ||
      bindings.construct_send_character_interaction_command == nullptr ||
      bindings.destroy_character_interaction_context == nullptr ||
      bindings.send_character_interaction_primary_vtable == 0 ||
      bindings.send_character_interaction_secondary_vtable == 0) {
    return EnforceDemandsResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return EnforceDemandsResult::unavailable;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return EnforceDemandsResult::no_played_character;
  }
  void *const game_state = *bindings.game_state_slot;
  void *const war = ResolveWar(bindings, game_state, war_id);
  if (war == nullptr) {
    return EnforceDemandsResult::war_not_found;
  }
  void *const attackers =
      static_cast<std::byte *>(war) + kWarAttackersOffset;
  void *const defenders =
      static_cast<std::byte *>(war) + kWarDefendersOffset;
  if (!bindings.contains_war_participant(
          attackers, current.played_character_id) &&
      !bindings.contains_war_participant(
          defenders, current.played_character_id)) {
    return EnforceDemandsResult::player_not_participant;
  }
  const bool player_is_primary_attacker =
      LoadAt<std::int32_t>(war, kWarPrimaryAttackerCharacterIdOffset) ==
      current.played_character_id;
  const bool player_is_primary_defender =
      LoadAt<std::int32_t>(war, kWarPrimaryDefenderCharacterIdOffset) ==
      current.played_character_id;
  if (!player_is_primary_attacker && !player_is_primary_defender) {
    return EnforceDemandsResult::player_not_war_leader;
  }
  if (player_is_primary_attacker && player_is_primary_defender) {
    return EnforceDemandsResult::unavailable;
  }

  CharacterInteractionContextStorage context_storage{};
  void *const context = context_storage.bytes.data();
  if (bindings.default_construct_character_interaction_context(context) !=
      context) {
    return EnforceDemandsResult::unavailable;
  }
  bindings.construct_war_resolution_interaction_context(context, war,
                                                        player_is_primary_attacker);
  if (!bindings.validate_character_interaction_context(context, nullptr)) {
    bindings.destroy_character_interaction_context(context);
    return EnforceDemandsResult::validation_failed;
  }

  SendCharacterInteractionCommandStorage command_storage{};
  void *const command = command_storage.bytes.data();
  if (bindings.construct_send_character_interaction_command(command,
                                                             context) !=
          command ||
      LoadAt<std::uintptr_t>(command, 0) !=
          bindings.send_character_interaction_primary_vtable ||
      LoadAt<std::uintptr_t>(command, 0x18) !=
          bindings.send_character_interaction_secondary_vtable) {
    if (LoadAt<void *>(command,
                       kSendCharacterInteractionContextOffset) != nullptr) {
      bindings.destroy_character_interaction_context(
          static_cast<std::byte *>(command) +
          kSendCharacterInteractionContextOffset);
    }
    bindings.destroy_character_interaction_context(context);
    return EnforceDemandsResult::unavailable;
  }
  bindings.submit_command(bindings.command_manager, command, 0x0E);
  bindings.destroy_character_interaction_context(
      static_cast<std::byte *>(command) +
      kSendCharacterInteractionContextOffset);
  bindings.destroy_character_interaction_context(context);
  return EnforceDemandsResult::submitted;
}

} // namespace xar::ck3_11906
