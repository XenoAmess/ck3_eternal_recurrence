#pragma once

#include "xar_bridge/ck3_12004_clergy_appointment.hpp"
#include "xar_bridge/ck3_12004_religion_profile.hpp"

#include <cstddef>
#include <cstdint>

namespace xar::ck3_12004::religion::county_conversion::abi {

// Sole mapper: county-first01/{early3,remaining7,typed-inputs01}/FAMILY-MAP.json
// and selected-command-data/SELECTED-COMMAND-TABLE-MAP.json. Each concrete
// function/table is bound from its own actual .4 receipt, without RVA shifting.
inline constexpr std::uintptr_t kShownRva = 0x31AC790;
inline constexpr std::uintptr_t kValidRva = 0x31AC660;
inline constexpr std::uintptr_t kTargetValidRva = 0x2C48950;
inline constexpr std::uintptr_t kProduceTargetsRva = 0x2C48E60;
inline constexpr std::uintptr_t kMonthlyRateRva = 0x31ADC40;
inline constexpr std::uintptr_t kCountyRiteRva = 0x24D6330;
inline constexpr std::uintptr_t kLookupTypeRva = 0xCF1E80;
inline constexpr std::uintptr_t kTaskDispatchValidatorRva = 0x2996670;
inline constexpr std::uintptr_t kCommandPrimaryVtableRva = 0x476DC78;
inline constexpr std::uintptr_t kCommandSecondaryVtableRva = 0x476DC48;
// Actual typed DB getter+4 RIP pair. Lookup fallback is source-used in the
// complete actual CF1E80 body; no old-native lookup admission is used.
inline constexpr std::uintptr_t kTaskTypeDatabaseSlotRva = 0x5C671D8;
inline constexpr std::uintptr_t kTaskTypeFallbackSlotRva = 0x5D1F900;

// Shared exact .4 Hash/context, command, Epi/Faction/Province, Government and
// basic religion source proofs are indexed in ROOT-COUNTY-SOURCE-DELIVERY.json.
inline constexpr std::uintptr_t kHashKeyRva = 0x3F7E220;
inline constexpr std::uintptr_t kCommandManagerRva = 0x5CC1240;
inline constexpr std::uintptr_t kQueueOwnedCommandRva = 0x37F06D0;
inline constexpr std::uintptr_t kTitleStorageSlotRva = 0x5D1DAF8;
inline constexpr std::uintptr_t kTitleFallbackSlotRva = 0x5D1DAE0;
// A847A0 takes native CString*, obtains a fullID, then resolves that Title.
inline constexpr std::uintptr_t kTitleByKeyRva = 0xA847A0;
inline constexpr std::uintptr_t kGovernmentRva = 0x28C2DF0;
inline constexpr std::uintptr_t kGovernmentFallbackSlotRva = 0x5D1E2A8;
inline constexpr std::uintptr_t kIdentifierNameRva = 0x3F4F8E0;
inline constexpr std::uintptr_t kCountyOpinionRva = 0x24D4C90;
inline constexpr std::uintptr_t kCharacterRiteRva = religion::profile::kCharacterRiteRva;
inline constexpr std::uintptr_t kRiteFaithRva = religion::profile::kRiteFaithRva;

// Shared Council vector/allocator proof; only software DTOs are reused.
inline constexpr std::uintptr_t kAllocatorVtableRva = 0x452D0B8;
inline constexpr std::uintptr_t kFallbackAllocatorRva = 0x54DEDE0;
inline constexpr std::uintptr_t kInitializeVectorRva = 0x98B8C0;
inline constexpr std::uintptr_t kReleaseAllocationRva = 0x855830;
inline constexpr std::size_t kAllocatorSize = 0x210;
inline constexpr std::size_t kAllocatorFallbackOffset = 0x208;

// Typed Council key chain forms TaskType+18 from the same ActiveTask+18.
// It does not establish, and this implementation does not read, Position+18.
inline constexpr std::size_t kDefinitionKeyOffset = 0x18;
inline constexpr std::size_t kTaskTypeKindOffset = 0x48;
inline constexpr std::size_t kTaskTypeProgressKindOffset = 0x54;
inline constexpr std::size_t kTaskPercentageOffset = 0x20;
inline constexpr std::size_t kTaskFrozenOffset = 0x39;
inline constexpr std::size_t kTaskScopesOffset = 0x40;
inline constexpr std::size_t kTaskScopeTagOffset = 0x48;
inline constexpr std::size_t kTaskScopeProvinceOffset = 0x50;
inline constexpr std::size_t kCountyRiteOffset = 0x384;

// Shared Province/Title full-generation identity and storage source operands.
inline constexpr std::size_t kProvinceIdOffset = 0x10;
inline constexpr std::size_t kProvinceTagOffset = 0x85C;
inline constexpr std::size_t kProvinceCountyOffset = 0x848;
inline constexpr std::size_t kMapProvinceArrayOffset = 0x140;
inline constexpr std::size_t kMapProvinceCountOffset = 0x14C;
inline constexpr std::size_t kCountyTitleIdOffset = 0x18;
inline constexpr std::size_t kTitleFullIdOffset = 0x10;
inline constexpr std::size_t kTitleHolderOffset = 0x128;
inline constexpr std::size_t kStorageEntriesOffset = 0x20;
inline constexpr std::size_t kStorageCapacityOffset = 0x2C;
inline constexpr std::size_t kStorageStride = 0x10;
inline constexpr std::size_t kStorageObjectOffset = 0x08;

// Basic religion object identities and shared Government vector role proof.
inline constexpr std::size_t kReligionFullIdOffset = 0x08;
inline constexpr std::size_t kCharacterRiteOffset = clergy::kCharacterRiteOffset;
inline constexpr std::size_t kRiteFaithOffset = 0x4B8;
inline constexpr std::size_t kGovernmentFlagsOffset = 0x50;
inline constexpr std::size_t kGovernmentFlagCountOffset = 0x5C;

// Same actual .4 clergy task ownership and position-pointer proof. These
// aliases keep this lane from inventing or borrowing unrelated class offsets.
inline constexpr std::size_t kCharacterLandedOffset = clergy::kLandedOffset;
inline constexpr std::size_t kLandedTaskIdsOffset = clergy::kTaskIdsOffset;
inline constexpr std::size_t kLandedTaskCountOffset = clergy::kTaskCountOffset;
inline constexpr std::size_t kTaskFullIdOffset = clergy::kTaskIdentityOffset;
inline constexpr std::size_t kTaskTypeOffset = clergy::kTaskTypeOffset;
inline constexpr std::size_t kTaskOwnerOffset = clergy::kTaskOwnerOffset;
inline constexpr std::size_t kTaskIncumbentOffset = clergy::kTaskIncumbentOffset;
inline constexpr std::size_t kTaskTypePositionOffset = clergy::kTypePositionOffset;

} // namespace xar::ck3_12004::religion::county_conversion::abi
