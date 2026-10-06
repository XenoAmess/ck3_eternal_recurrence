#pragma once

#include "xar_bridge/ck3_12004.hpp"

namespace xar::ck3_12004::religion::profile {

// Actual .4 paired instruction/data operands. The ledger is external at
// faith-tenet/implementation-caa4/{actor-map,basic-map,doctrine-map,tenet-map}.
// These constants are independent of the legacy .2/.3 image factories.
inline constexpr std::uintptr_t kCharacterRiteRva = 0x28D2F70;
inline constexpr std::uintptr_t kCharacterFaithRva = 0x289E730;
inline constexpr std::uintptr_t kRiteFaithRva = 0x24FC540;
inline constexpr std::uintptr_t kFaithReligionRva = 0x2443D20;
inline constexpr std::uintptr_t kFaithMainRiteRva = 0x2444340;
inline constexpr std::uintptr_t kFaithFervorRva = 0x243EA70;
inline constexpr std::uintptr_t kCharacterSpiritualFulfillmentRva = 0x28BCE20;
inline constexpr std::uintptr_t kFaithTagRva = 0xB801A0;
inline constexpr std::uintptr_t kRiteIsMainRva = 0x24F7E20;
inline constexpr std::uintptr_t kRiteDivergenceToMainRva = 0x2BDFB80;
inline constexpr std::uintptr_t kFaithHeresyThresholdRva = 0x2440900;
inline constexpr std::uintptr_t kFaithIsUnreformedRva = 0x2BD8940;
inline constexpr std::uintptr_t kDraftWindowVisibilityRva = 0x2160380;
inline constexpr std::uintptr_t kDraftIdlerVtableRva = 0x44BC418;
inline constexpr std::uintptr_t kDraftHandlerVtableRva = 0x44BA8A0;
inline constexpr std::uintptr_t kDraftWindowPrimaryVtableRva = 0x4565C40;
inline constexpr std::uintptr_t kDraftWindowSecondaryVtableRva = 0x4565C18;

inline constexpr std::uintptr_t kCharacterKnowsDoctrineRva = 0x28B0BE0;
inline constexpr std::uintptr_t kBooleanParameterMembershipRva = 0xB9DE80;
inline constexpr std::uintptr_t kParameterTokenKeyRva = 0x3F4F8E0;
inline constexpr std::uintptr_t kDoctrineDatabaseSlotRva = 0x5C67198;

inline constexpr std::uintptr_t kNativeTenetStateRva = 0x24F8880;
inline constexpr std::uintptr_t kCharacterExtraTenetsRva = 0x28B0B40;
inline constexpr std::uintptr_t kCharacterActualPerksRva = 0x2919340;
inline constexpr std::uintptr_t kActualDefinitionPointerContainsRva = 0xA11CC0;
inline constexpr std::uintptr_t kRiteStorageSlotRva = 0x5D1E2F8;
inline constexpr std::uintptr_t kTenetDatabaseSlotRva = 0x5D1DEB8;
inline constexpr std::uintptr_t kPerkDatabaseSlotRva = 0x5C67128;

// Shared software layouts retained in actual .4 source operands. Religion
// key18 is closed by the actual SReligionType virtual consumer, not RTTI.
inline constexpr std::size_t kReligionDefinitionPointerOffset = 0x20;
inline constexpr std::size_t kReligionDefinitionKeyOffset = 0x18;
inline constexpr std::size_t kRiteFounderOffset = 0x4BC;
inline constexpr std::size_t kRiteHeadOffset = 0x4C0;
inline constexpr std::size_t kRiteUnreformedOffset = 0x8B0;
inline constexpr std::size_t kRiteCoreTenetsOffset = 0x758;
inline constexpr std::size_t kRiteTenetStatesOffset = 0x788;
inline constexpr std::size_t kRiteDoctrinesOffset = 0x7A0;
inline constexpr std::size_t kRiteBooleanParametersOffset = 0x7B8;
inline constexpr std::size_t kCharacterKnowledgeExtensionOffset = 0x1C8;
inline constexpr std::size_t kPersonalTenetsOffset = 0x88;
inline constexpr std::size_t kExtraTenetsOffset = 0xC8;
inline constexpr std::size_t kLearnedDoctrinesOffset = 0xE0;
inline constexpr std::size_t kTenetDatabaseDefinitionsOffset = 0xEF0;
inline constexpr std::size_t kTenetDatabaseCountOffset = 0xEFC;
inline constexpr std::size_t kProphetDefinitionOffset = 0xEF0;
inline constexpr std::size_t kCharacterPerkExtensionOffset = 0x1B0;
inline constexpr std::size_t kActualPerksOffset = 0x220;

} // namespace xar::ck3_12004::religion::profile
