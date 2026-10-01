#pragma once

#include <cstddef>
#include <cstdint>

namespace xar::ck3_12002 {
inline constexpr std::size_t kFamilySubjectCharacterHouseIdOffset = 0x158;
inline constexpr std::size_t kFamilySubjectHouseDynastyIdOffset = 0x2C;
inline constexpr std::size_t kFamilySubjectCharacterCourtRelationOffset = 0x1B8;
inline constexpr std::size_t kFamilySubjectCourtEmployerIdOffset = 0xC8;
inline constexpr std::uintptr_t kFamilySubjectHouseStorageSlotRva = 0x5D1DAF0;
inline constexpr std::uintptr_t kFamilySubjectHouseFallbackSlotRva = 0x5D1DAE8;
inline constexpr std::uintptr_t kFamilySubjectDynastyStorageSlotRva = 0x5D1DE78;
inline constexpr std::uintptr_t kFamilySubjectDynastyFallbackSlotRva = 0x5D1DE28;
inline constexpr std::size_t kFamilySubjectFirstParentIdOffset = 0x0;
inline constexpr std::size_t kFamilySubjectSecondParentIdOffset = 0x4;
inline constexpr std::size_t kFamilySubjectSpouseArrayOffset = 0x20;
inline constexpr std::size_t kFamilySubjectChildrenArrayOffset = 0x38;
inline constexpr std::uintptr_t kFamilySubjectNativeChildPredicateWrapperRva = 0x2B6EDC0;
inline constexpr std::uintptr_t kFamilySubjectNativeChildCollectorRva = 0x1C11B50;
} // namespace xar::ck3_12002
