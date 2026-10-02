#pragma once

#include "xar_bridge/ck3_12002_campaign.hpp"
#include "xar_bridge/county_faction_final_12003.hpp"
#include "xar_bridge/player_faction_alerts_v1.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerFactionAlertsV1GameVersion = "1.20.0.2";
inline constexpr std::string_view kPlayerFactionAlertsV1ExecutableSha256 =
    "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
inline constexpr std::string_view kPlayerFactionAlertsV1BackendId =
    "ck3-1.20.0.2-native-player-faction-alerts-v1";
inline constexpr std::uintptr_t kFactionAlertsStorageSlotRva12002 = 0x5D1DE90;
inline constexpr std::uintptr_t kFactionAlertsFallbackSlotRva12002 = 0x5D1DE10;
inline constexpr std::uintptr_t kFactionAlertsVtableRva12002 = 0x4743520;

#if defined(_MSC_VER)
#define XAR_FACTION_12002_CALL __fastcall
#else
#define XAR_FACTION_12002_CALL
#endif

struct FactionItemIdentity12002 {
  std::int32_t faction_id = -1;
};
using NativeFactionItemFixedPoint12002 = std::int64_t *(XAR_FACTION_12002_CALL *)(
    FactionItemIdentity12002 *item, std::int64_t *output);
using NativeFactionItemInt32_12002 = std::int32_t(XAR_FACTION_12002_CALL *)(
    FactionItemIdentity12002 *item);
using NativeFactionItemBool12002 = bool(XAR_FACTION_12002_CALL *)(
    FactionItemIdentity12002 *item);
using NativeFactionCharacterBool12002 = bool(XAR_FACTION_12002_CALL *)(
    std::uint32_t character_id);
using NativeFactionFixedPoint12002 = std::int64_t *(XAR_FACTION_12002_CALL *)(
    void *faction, std::int64_t *output);
using NativeFactionInt32_12002 = std::int32_t(XAR_FACTION_12002_CALL *)(void *faction);
using NativeCountyOpinionInt32_12003 = std::int32_t(XAR_FACTION_12002_CALL *)(
    void *county_data);
using NativeFactionBool12002 = bool(XAR_FACTION_12002_CALL *)(void *faction);
using NativeFactionDanger12002 = bool(XAR_FACTION_12002_CALL *)(
    void *ignored, void *faction);

#undef XAR_FACTION_12002_CALL

struct PlayerFactionAlertsNativeEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  bool offline_fixture_function_overrides = false;
  void **character_storage_slot = nullptr;
  void **character_fallback_slot = nullptr;
  void **faction_storage_slot = nullptr;
  void **faction_fallback_slot = nullptr;
  void **landed_title_storage_slot = nullptr;
  void **landed_title_fallback_slot = nullptr;
  void **war_storage_slot = nullptr;
  void **war_fallback_slot = nullptr;
  void **vassal_contract_storage_slot = nullptr;
  void **vassal_contract_fallback_slot = nullptr;
  std::uintptr_t expected_faction_vtable = 0;
  NativeCampaignRootCharacterResolverV1 immediate_liege = nullptr;
  NativeCampaignRootCharacterResolverV1 title_province = nullptr;
  NativeFactionCharacterBool12002 character_is_human = nullptr;
  NativeFactionFixedPoint12002 power = nullptr;
  NativeFactionFixedPoint12002 power_threshold = nullptr;
  NativeFactionFixedPoint12002 discontent_per_month = nullptr;
  NativeFactionInt32_12002 months_until_max_discontent = nullptr;
  NativeFactionBool12002 at_war = nullptr;
  NativeFactionDanger12002 dangerous = nullptr;
  bool county_observations_12003 = false;
  NativeCountyOpinionInt32_12003 county_opinion = nullptr;
  CountyFactionFinalBindings12003 county_faction_finals;
};

struct PlayerFactionAlertsAccessV1 {
  void *context = nullptr;
  ck3_11906::CapturePlayerFactionAlertsFrameV1 capture_frame = nullptr;
  ck3_11906::IsPlayerFactionAlertsMainThreadV1 is_main_thread = nullptr;
  ReadCampaignRootMemoryV1 read_memory = nullptr;
  ReadCampaignRootStringV1 read_string = nullptr;
};

using PlayerFactionAlertsRequestV1 = ck3_11906::PlayerFactionAlertsRequestV1;

enum class ReadFactionEntityResult12002 {
  unavailable,
  known_absent,
  available,
};

PlayerFactionAlertsNativeEnvironmentV1 BindPlayerFactionAlertsNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

struct FactionCountyOpinionMaterial12003 {
  std::int32_t county_title_id = -1;
  std::int32_t capital_province_id = -1;
  std::int32_t holder_character_id = -1;
  std::int32_t county_opinion = 0;
};

// Enabled only by the exact .3 descriptor at the existing query entry.
// The shared .2 binder retains its original reader behavior.
void BindCountyMemberObservations12003(
    PlayerFactionAlertsNativeEnvironmentV1 &environment) noexcept;

bool ReadCountyMemberOpinion12003(
    const PlayerFactionAlertsNativeEnvironmentV1 &environment,
    const PlayerFactionAlertsAccessV1 &access, std::int32_t county_title_id,
    FactionCountyOpinionMaterial12003 &output) noexcept;

// Independent full-generation lookup for gift receipts. Absence in the
// player's targeting vector is not evidence that a faction was destroyed.
ReadFactionEntityResult12002 ReadFactionEntityV1(
    const PlayerFactionAlertsNativeEnvironmentV1 &environment,
    const PlayerFactionAlertsAccessV1 &access, std::int32_t faction_id,
    game::PlayerTargetingFactionV1 &output) noexcept;

game::ReadPlayerFactionAlertsResultV1 ReadPlayerFactionAlertsV1(
    const PlayerFactionAlertsNativeEnvironmentV1 &environment,
    const PlayerFactionAlertsAccessV1 &access,
    const PlayerFactionAlertsRequestV1 &request,
    game::PlayerFactionAlertsV1 &output) noexcept;

std::string SerializePlayerFactionAlertsV1(
    const game::PlayerFactionAlertsV1 &snapshot);

} // namespace xar::ck3_12002
