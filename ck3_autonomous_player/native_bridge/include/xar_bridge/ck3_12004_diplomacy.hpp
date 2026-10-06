#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_diplomacy.hpp"

namespace xar::ck3_12004 {

// Caller-owned software bindings and algorithms are retained. These actual .4
// addresses come from complete paired native spans and source-use operands in
// actual4-domain/diplomacy-map; no prior-image binder is invoked.
using DiplomacyBindings = ck3_12002::DiplomacyBindings;

inline constexpr std::uintptr_t kWarResolutionContextRva = 0xCF57D0;
inline constexpr std::uintptr_t kInteractionDatabaseRva = 0x89DA60;
inline constexpr std::uintptr_t kDefaultInteractionContextRva = 0x3077300;
inline constexpr std::uintptr_t kConstructInteractionContextRva = 0x3076C70;
inline constexpr std::uintptr_t kDestroyInteractionContextRva = 0x3077380;
inline constexpr std::uintptr_t kValidateInteractionContextRva = 0x307C020;
inline constexpr std::uintptr_t kInteractionAnswerScoreRva = 0x307C440;
inline constexpr std::uintptr_t kEvaluateInteractionTriggerRva = 0x372DF10;
inline constexpr std::uintptr_t kSendInteractionCommandRva = 0x2968150;
inline constexpr std::uintptr_t kSendInteractionSecondaryValidateRva = 0x2968200;
inline constexpr std::uintptr_t kPlayedCharacterIdRva = 0x54DBC00;
inline constexpr std::uintptr_t kContainsWarParticipantRva = 0x2494B40;
inline constexpr std::uintptr_t kWarScoreRva = 0x249AC20;
inline constexpr std::uintptr_t kWarImprisonmentScoreRva = 0x2C0C2F0;
inline constexpr std::uintptr_t kWarBattleBaseScoreRva = 0x2C0C390;
inline constexpr std::uintptr_t kWarBattleSideScoreRva = 0x2C0CFE0;
inline constexpr std::uintptr_t kWarOccupationScoreRva = 0x2C0DD90;
inline constexpr std::uintptr_t kWarTickingScoreRva = 0x2C0EE50;
inline constexpr std::uintptr_t kSendPrimaryVtableRva = 0x448BCF0;
inline constexpr std::uintptr_t kSendSecondaryVtableRva = 0x448BCC0;
inline constexpr std::size_t kDiplomacyAutoAcceptTriggerOffset = 0x2290;
inline constexpr std::size_t kDiplomacyAutoAcceptScalarOffset = 0x2718;

// Core and command bundles must be supplied by the actual .4 profile owner.
// Read-only options remain usable when that owner has not enabled commands.
DiplomacyBindings BindDiplomacyImage(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const CoreBindings &actual_core,
    const ck3_12002::CommandBindings &actual_commands) noexcept;

// Actual .4 Core/World layout proofs preserve the pure-memory paths used by
// these established algorithms. Native callbacks come only from the binder
// above. Recipient-response unavailability and the existing full wire DTO are
// retained; AI scores are not substituted for a recipient decision.
using ck3_12002::ReadWarTerminationOptions;
using ck3_12002::SubmitEnforceDemands;
using ck3_12002::SubmitSurrenderWar;
using ck3_12002::SubmitOfferWhitePeace;

} // namespace xar::ck3_12004
