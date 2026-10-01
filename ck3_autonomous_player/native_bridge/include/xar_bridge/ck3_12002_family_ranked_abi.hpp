#pragma once

#include <cstddef>
#include <cstdint>

namespace xar::ck3_12002 {
inline constexpr std::uintptr_t kFamilyRankedEnumeratorRva = 0x1A3BD40;
inline constexpr std::uintptr_t kFamilyRankedScoreFilterRva = 0x1A3C670;
inline constexpr std::uintptr_t kFamilyRankedGateAndScoreRva = 0x1A3C800;
inline constexpr std::uintptr_t kFamilyRankedNativeTierRva = 0x28AC6B0;
inline constexpr std::uintptr_t kFamilyRankedNativeCapTableSlotRva = 0x5449F10;
inline constexpr std::uintptr_t kFamilyRankedSortScoredRva = 0x1123AA0;
inline constexpr std::uintptr_t kFamilyRankedInitializeScoredRva = 0x1121DA0;
inline constexpr std::uintptr_t kFamilyRankedReleaseBufferRva = 0x855830;
inline constexpr std::uintptr_t kFamilyRankedInitializeCandidatesRva = 0x9B4F80;
inline constexpr std::uintptr_t kFamilyRankedDestroyScoredRowRva = 0x8863D0;
inline constexpr std::uintptr_t kFamilyRankedCandidateOwnerVtableRva = 0x45284A8;
inline constexpr std::uintptr_t kFamilyRankedScoredOwnerVtableRva = 0x4528460;
inline constexpr std::uintptr_t kFamilyRankedScoredRowVtableRva = 0x4528100;
inline constexpr std::uintptr_t kFamilyRankedCandidateBackingAllocatorRva = 0x54DEBB8;
inline constexpr std::uintptr_t kFamilyRankedScoredBackingAllocatorRva = 0x54E1420;
inline constexpr std::size_t kFamilyRankedCharacterLivingOffset = 0x1B0;
inline constexpr std::size_t kFamilyRankedLivingStrategyOffset = 0x278;
inline constexpr std::size_t kFamilyRankedStrategySourceCharacterOffset = 0x18;
inline constexpr std::size_t kFamilyRankedStrategyReadyOwnerOffset = 0x20;
inline constexpr std::size_t kFamilyRankedLivingAgeDataOffset = 0x310;
inline constexpr std::size_t kFamilyRankedAgeValueOffset = 0x2;
inline constexpr std::size_t kFamilyRankedSortScratchSize = 0x8;
} // namespace xar::ck3_12002
