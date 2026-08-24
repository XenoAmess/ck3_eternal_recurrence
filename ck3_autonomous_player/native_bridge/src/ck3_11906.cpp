#include "xar_bridge/ck3_11906.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstring>
#include <limits>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace xar::ck3_11906 {
namespace {

constexpr std::uintptr_t kGameStateSlotRva = 0x570E068;
constexpr std::uintptr_t kJominiStateSlotRva = 0x570F7B8;
constexpr std::uintptr_t kCommandManagerRva = 0x57621F0;
constexpr std::uintptr_t kPausePrimaryVtableRva = 0x432F1C8;
constexpr std::uintptr_t kPauseSecondaryVtableRva = 0x432F198;
constexpr std::uintptr_t kSetSpeedPrimaryVtableRva = 0x432F3F0;
constexpr std::uintptr_t kSetSpeedSecondaryVtableRva = 0x432F260;
constexpr std::uintptr_t kSelectEventOptionPrimaryVtableRva = 0x4335240;
constexpr std::uintptr_t kSelectEventOptionSecondaryVtableRva = 0x4335210;
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
constexpr std::uintptr_t kSiegeStorageSlotRva = 0x57BF1B8;
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
constexpr std::uintptr_t kConstructRaiseTroopsCommandRva = 0x26D6FC0;
constexpr std::uintptr_t kValidateRaiseTroopsCommandRva = 0x26D7150;
constexpr std::uintptr_t kDestroyRaiseTroopsCommandRva = 0x10E7950;
constexpr std::uintptr_t kGetArmyMoveModeRva = 0x26B51B0;
constexpr std::uintptr_t kCanCharacterUseCommandKindRva = 0x26B26A0;
constexpr std::uintptr_t kCanArmyUseMoveModeRva = 0x2248860;
constexpr std::uintptr_t kCanMoveArmyRva = 0x26B4610;
constexpr std::uintptr_t kResolveMoveOriginRva = 0x2248260;
constexpr std::uintptr_t kConstructMovePathContextRva = 0x23C32F0;
constexpr std::uintptr_t kConstructArmyMovePathRva = 0x0C7BA70;
constexpr std::uintptr_t kBuildArmyMoveRouteRva = 0x23C33D0;
constexpr std::uintptr_t kDestroyMoveArmyCommandRva = 0x26B46D0;
constexpr std::uintptr_t kValidateDisbandArmyCommandRva = 0x26B5710;
constexpr std::uintptr_t kValidateSplitArmyHalfCommandRva = 0x26B8030;
constexpr std::uintptr_t kDestroySplitArmyHalfCommandRva = 0x0963C60;
constexpr std::uintptr_t kCreateMergeArmiesCommandRva = 0x26C6CE0;
constexpr std::uintptr_t kValidateMergeArmiesCommandRva = 0x26BA050;
constexpr std::uintptr_t kDestroyMergeArmiesCommandRva = 0x26B5330;
constexpr std::uintptr_t kGetCasusBelliTypeDatabaseRva = 0x088E260;
constexpr std::uintptr_t kGetCharacterInteractionDatabaseRva = 0x0831890;
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
constexpr std::uintptr_t kConstructSendCharacterInteractionCommandRva =
    0x26B3220;
constexpr std::uintptr_t kDestroyCharacterInteractionContextRva =
    0x2C3F380;
constexpr std::uintptr_t kDefaultConstructCharacterInteractionContextRva =
    0x2C3F300;
constexpr std::uintptr_t kConstructWarResolutionInteractionContextRva =
    0x0C569F0;
constexpr std::uintptr_t kGetScriptIdentifierTableRva = 0x3B971A0;
// Locks the script-identifier table, calls lookup-only RVA 0x3B96D40, then
// unlocks. Unlike RVA 0x3B96E50 it never inserts a missing name.
constexpr std::uintptr_t kLookupScriptIdentifierIdRva = 0x3B97020;
constexpr std::uintptr_t kIsEventTargetValidRva = 0x3329B00;
constexpr std::uintptr_t kResolveEventTargetObjectRva = 0x33299E0;

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
constexpr std::size_t kCharacterFamilyDataOffset = 0x1A0;
constexpr std::size_t kCharacterDeathDataOffset = 0x1C8;
constexpr std::size_t kFamilyBetrothedCharacterIdOffset = 0x10;
constexpr std::size_t kFamilyPrimarySpouseCharacterIdOffset = 0x14;
constexpr std::size_t kFamilySpouseCharacterIdsOffset = 0x20;
constexpr std::size_t kWarStorageOffset = 0x20;
constexpr std::size_t kWarIdOffset = 0x08;
constexpr std::size_t kWarAttackersOffset = 0x20;
constexpr std::size_t kWarDefendersOffset = 0x80;
constexpr std::size_t kWarPrimaryAttackerCharacterIdOffset = 0x288;
constexpr std::size_t kWarPrimaryDefenderCharacterIdOffset = 0x28C;
constexpr std::size_t kWarTargetedTitleIdsOffset = 0x270;
constexpr std::size_t kWarEndedDataOffset = 0x358;
constexpr std::size_t kLandedTitleStorageOffset = 0x20;
constexpr std::size_t kLandedTitleIdOffset = 0x10;
constexpr std::size_t kLandedTitleTemplateOffset = 0x160;
constexpr std::size_t kLandedTitleDeJureVassalIdsOffset = 0x240;
constexpr std::size_t kLandedTitleTemplateTierOffset = 0x5C;
constexpr std::size_t kLandedTitleTemplateProvinceIdOffset = 0x80;
constexpr std::int32_t kBaronyTitleTier = 1;
constexpr std::int32_t kCountyTitleTier = 2;
constexpr std::size_t kArmyIdOffset = 0x10;
constexpr std::size_t kArmyCurrentProvinceOffset = 0x20;
constexpr std::size_t kUnitPathProvinceInfosOffset = 0x38;
constexpr std::size_t kUnitPathProvinceInfoCapacityOffset = 0x40;
constexpr std::size_t kUnitPathProvinceInfoCountOffset = 0x44;
constexpr std::size_t kUnitPathProvinceIdOffset = 0x00;
constexpr std::size_t kUnitRetreatStateOffset = 0x170;
constexpr std::size_t kArmyOwnerCharacterIdOffset = 0x174;
constexpr std::size_t kUnitArmyIdOffset = 0x178;
constexpr std::size_t kProvinceIdOffset = 0x10;
constexpr std::size_t kProvinceOccupyingCharacterIdOffset = 0x744;
constexpr std::size_t kProvinceActiveSiegeIdOffset = 0x790;
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
constexpr std::size_t kCasusBelliTypeKeyOffset = 0x18;
constexpr std::size_t kCasusBelliTypeRuleOffset = 0x38;
constexpr std::size_t kCasusBelliRuleDisabledOffset = 0x211;
constexpr std::size_t kCasusBelliTypeFlagsOffset = 0x1718;
constexpr std::uint32_t kCasusBelliCombinedConfigurationsFlag = 1U << 20U;
constexpr std::size_t kValidCasusBelliConfigurationSize = 0x98;
constexpr std::size_t kValidCasusBelliClaimantOffset = 0x00;
constexpr std::size_t kValidCasusBelliTargetTitlesOffset = 0x08;
constexpr std::size_t kNativeArrayDataOffset = 0x00;
constexpr std::size_t kNativeArrayCapacityOffset = 0x08;
constexpr std::size_t kNativeArrayCountOffset = 0x0C;
constexpr std::size_t kCharacterInteractionSpecialDataOffset = 0x330;
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
constexpr std::int32_t kMaximumWarObjectiveTitleIds = 4'096;
constexpr std::int32_t kMaximumUnitRouteProvinceInfos = 4'096;
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

    // Auto-accept notifications need reply enum 4 (acknowledge).  The public
    // agent action is deliberately accept/reject, so exposing one would leave
    // the planner parked on a request that neither public action can advance.
    if (LoadAt<std::uint8_t>(pending,
                             kPendingInteractionAutoAcceptOffset) != 0) {
      continue;
    }
    if (!bindings.is_pending_character_interaction_for_character(
            pending, played_character)) {
      continue;
    }

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
    instance_id = candidate_id;
    sender_character_id = LoadAt<std::int32_t>(
        pending, kPendingInteractionSenderIdOffset);
    auto_accept_notification = false;
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

bool ReadCasusBelliTypeKey(const void *casus_belli_type,
                           std::string &output) noexcept {
  const auto *const string_storage =
      static_cast<const std::byte *>(casus_belli_type) +
      kCasusBelliTypeKeyOffset;
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

} // namespace

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
  result.pending_character_interaction_storage_slot =
      reinterpret_cast<void **>(
          module + kPendingCharacterInteractionStorageSlotRva);
  result.character_storage_slot =
      reinterpret_cast<void **>(module + kCharacterStorageSlotRva);
  result.army_storage_slot =
      reinterpret_cast<void **>(module + kArmyStorageSlotRva);
  result.siege_storage_slot =
      reinterpret_cast<void **>(module + kSiegeStorageSlotRva);
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
  result.get_script_identifier_table =
      reinterpret_cast<GetScriptIdentifierTable>(
          module + kGetScriptIdentifierTableRva);
  result.lookup_script_identifier_id =
      reinterpret_cast<LookupScriptIdentifierId>(
          module + kLookupScriptIdentifierIdRva);
  result.is_event_target_valid = reinterpret_cast<IsEventTargetValid>(
      module + kIsEventTargetValidRva);
  result.resolve_event_target_object =
      reinterpret_cast<ResolveEventTargetObject>(
          module + kResolveEventTargetObjectRva);
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
  output.has_played_character =
      output.map_ready &&
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
  if (LoadAt<std::int32_t>(war, kWarPrimaryAttackerCharacterIdOffset) !=
          current.played_character_id &&
      LoadAt<std::int32_t>(war, kWarPrimaryDefenderCharacterIdOffset) !=
          current.played_character_id) {
    return EnforceDemandsResult::player_not_war_leader;
  }

  CharacterInteractionContextStorage context_storage{};
  void *const context = context_storage.bytes.data();
  if (bindings.default_construct_character_interaction_context(context) !=
      context) {
    return EnforceDemandsResult::unavailable;
  }
  bindings.construct_war_resolution_interaction_context(context, war,
                                                        false);
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
