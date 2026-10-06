#pragma once

#include "xar_bridge/ck3_12002_context.hpp"
#include "xar_bridge/ck3_12004_faction_alerts.hpp"
#include "xar_bridge/ck3_12004_gift_opinion.hpp"
#include "xar_bridge/faction_gift_mitigation_action_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kFactionGiftDatabaseGetterRvaV1 = 0x89DA60;
inline constexpr std::uintptr_t kFactionGiftStableHashRvaV1 = 0x3F7E220;
inline constexpr std::uintptr_t kFactionGiftDefinitionLookupRvaV1 = 0xA055E0;
inline constexpr std::uintptr_t kFactionGiftConstructTwoRoleContextRvaV1 = 0x3076C70;
inline constexpr std::uint32_t kFactionGiftDefinitionStableHashV1 = 0x776D7835;
inline constexpr std::size_t kFactionGiftContextSizeV1 = 0x338;
inline constexpr std::size_t kFactionGiftCommandSizeV1 = 0x368;
inline constexpr std::size_t kFactionGiftDefinitionCostOffsetV1 = 0x40;
inline constexpr std::size_t kFactionGiftAutoAcceptTriggerOffsetV1 = 0x2290;
inline constexpr std::size_t kFactionGiftAutoAcceptScalarOffsetV1 = 0x2718;
inline constexpr std::size_t kFactionGiftContextActorOffsetV1 = 0x2D8;
inline constexpr std::size_t kFactionGiftContextRecipientOffsetV1 = 0x2DC;
inline constexpr std::size_t kFactionGiftContextPayerOffsetV1 = 0x2EC;
inline constexpr std::size_t kFactionGiftDefinitionHashOffsetV1 = 0x14;
inline constexpr std::size_t kFactionGiftDefinitionKeyOffsetV1 = 0x18;
inline constexpr std::size_t kFactionGiftCharacterExtensionOffsetV1 = 0x1B0;
inline constexpr std::size_t kFactionGiftCharacterGoldOffsetV1 = 0x100;

inline constexpr std::string_view kFactionGiftBackendIdV1 =
    "ck3-1.20.0.4-private-faction-gift-mitigation-action-v1";
inline constexpr std::string_view kFactionGiftContractStageV1 =
    "exact_build_private_action_source_static_ready_live_pending";

using FactionGiftGetDatabaseV1 = void *(*)();
using FactionGiftStableHashV1 = std::int32_t (*)(void *, const char *, std::uint32_t);
using FactionGiftLookupDefinitionV1 = void *(*)(void *, std::int32_t);
using FactionGiftConstructTwoRoleContextV1 = void *(*)(
    void *, void *, std::int32_t, std::int32_t, void *, bool);
using FactionGiftReadOpinionDeltaV1 = bool (*)(
    void *, std::uintptr_t, const void *, std::uint32_t, std::uint32_t,
    std::int32_t &) noexcept;
using FactionGiftReadOpinionV1 = bool (*)(
    void *, std::uintptr_t, const CoreBindings &, std::uint32_t,
    std::uint32_t, GiftOpinionResult &) noexcept;
using FactionGiftReadValueV1 = bool (*)(
    void *, std::uintptr_t, const void *, std::uint32_t, std::uint32_t,
    std::int64_t &) noexcept;

// The generic lifecycle/cost/queue bindings are the same 1.20 provider used
// by marriage. Gift owns a separate definition and its two-role constructor.
struct FactionGiftBindings12004 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  ck3_12002::ContextBindings interaction{};
  FactionGiftGetDatabaseV1 get_database = nullptr;
  FactionGiftStableHashV1 stable_hash = nullptr;
  FactionGiftLookupDefinitionV1 lookup_definition = nullptr;
  FactionGiftConstructTwoRoleContextV1 construct_two_role = nullptr;
  void *opinion_delta_context = nullptr;
  FactionGiftReadOpinionDeltaV1 read_opinion_delta = nullptr;
  void *opinion_context = nullptr;
  FactionGiftReadOpinionV1 read_opinion = nullptr;
  void *gift_value_context = nullptr;
  FactionGiftReadValueV1 read_gift_value = nullptr;
};

// Pure address binding; no process discovery or access occurs here.
FactionGiftBindings12004 BindFactionGiftImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// Negative native CanSend is a complete observable preview. Gifts whose
// native on-send cost vector charges any currency are outside this receipt.
// Actual gift gold is the named gift_value paid by the on-accept effect.
bool ReadFactionGiftPreview12004(
    const FactionGiftBindings12004 &, std::uint32_t player_character_id,
    std::uint32_t recipient_character_id,
    game::FactionGiftPreviewV1 &output) noexcept;
bool ValidateFactionGift12004(
    const FactionGiftBindings12004 &, std::uint32_t player_character_id,
    std::uint32_t recipient_character_id, std::string_view definition_key,
    std::uint64_t expected_definition_stable_hash, bool &valid,
    std::string &reason) noexcept;
// Returns queue ACK only. Existing receipt verification reads independent
// gold, recipient opinion/modifier, and the persisted faction entity.
bool SubmitFactionGift12004(
    const FactionGiftBindings12004 &, std::uint32_t player_character_id,
    std::uint32_t recipient_character_id, std::string_view definition_key,
    std::uint64_t expected_definition_stable_hash) noexcept;

// The caller supplies a freshly captured campaign-root row from this paused
// frame. Its existing direct-vassal reader supplies eligibility; this reader
// independently resolves the persisted faction entity, gold and opinion.
bool CaptureFactionGiftObservation12004(
    const FactionGiftBindings12004 &,
    const PlayerFactionAlertsNativeEnvironmentV1 &,
    const PlayerFactionAlertsAccessV1 &,
    const game::CampaignRootContextV1 &campaign_root,
    std::uint64_t native_revision, std::uint32_t source_faction_id,
    std::uint32_t recipient_character_id, bool require_preview,
    game::FactionGiftMitigationObservationV1 &output) noexcept;

// The stable action/receipt algorithms retain their original DTOs. Only the
// native source and image binding change; no second pending ledger is added.
game::FactionGiftMitigationAckStatusV1 ExecuteFactionGiftAction12004(
    const ck3_11906::FactionGiftMitigationNativeEnvironmentV1 &,
    const ck3_11906::FactionGiftMitigationActionAccessV1 &,
    const game::FactionGiftMitigationRequestV1 &,
    game::FactionGiftMitigationAckV1 &) noexcept;
std::string SerializeFactionGiftAck12004(const game::FactionGiftMitigationAckV1 &);

} // namespace xar::ck3_12004
