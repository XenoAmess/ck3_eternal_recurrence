#include "xar_bridge/ck3_12004_family_ranked.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12004_family_abi.hpp"

namespace xar::ck3_12004 {
namespace {
// Actual finite callback and operand receipts: marriage-family/actual4-ranked.
constexpr std::uintptr_t kNativeCapTableSlotRva = 0x5449F10;
constexpr std::uintptr_t kEnumeratorRva = 0x1A3BD20;
constexpr std::uintptr_t kScoreFilterRva = 0x1A3C650;
constexpr std::uintptr_t kSortScoredRva = 0x1123AA0;
constexpr std::uintptr_t kInitializeScoredRva = 0x1121DA0;
// Shared Council/Army exact callback receipts; neither body is recaptured here.
constexpr std::uintptr_t kReleaseBufferRva = 0x855830;
constexpr std::uintptr_t kDestroyScoredRowRva = 0x8863D0;
// This frameless entry is rooted in actual candidate owner vtable slot+0x20.
constexpr std::uintptr_t kInitializeCandidatesRva = 0x9B4F80;
constexpr std::uintptr_t kCandidateOwnerVtableRva = 0x45284B8;
constexpr std::uintptr_t kScoredOwnerVtableRva = 0x4528470;
constexpr std::uintptr_t kScoredRowVtableRva = 0x4528110;
constexpr std::uintptr_t kCandidateBackingAllocatorRva = 0x54DEBB8;
constexpr std::uintptr_t kScoredBackingAllocatorRva = 0x54E1420;
} // namespace

ck3_12002::FamilyRankedBindings BindFamilyRankedImage(
    std::uintptr_t base, std::string_view sha) noexcept {
  ck3_12002::FamilyRankedBindings bindings{};
  bindings.family = BindFamilyImage(base, sha);
  if (!bindings.family.enabled) return bindings;
  bindings.enabled = true;
  bindings.read_native_tier =
      reinterpret_cast<ck3_12002::FamilyRankedReadTier>(base + kFamilyHighestTierRva);
  bindings.native_cap_table_slot =
      reinterpret_cast<const std::int32_t *const *>(base + kNativeCapTableSlotRva);
  bindings.enumerate_candidates =
      reinterpret_cast<ck3_12002::FamilyRankedEnumerate>(base + kEnumeratorRva);
  bindings.score_candidates =
      reinterpret_cast<ck3_12002::FamilyRankedScore>(base + kScoreFilterRva);
  bindings.sort_scored_candidates =
      reinterpret_cast<ck3_12002::FamilyRankedSortScored>(base + kSortScoredRva);
  bindings.destroy_scored_row =
      reinterpret_cast<ck3_12002::FamilyRankedDestroyScoredRow>(
          base + kDestroyScoredRowRva);
  bindings.initialize_scored_container =
      reinterpret_cast<ck3_12002::FamilyRankedInitializeScored>(
          base + kInitializeScoredRva);
  bindings.release_native_buffer =
      reinterpret_cast<ck3_12002::FamilyRankedReleaseBuffer>(base + kReleaseBufferRva);
  bindings.initialize_candidate_buffer =
      reinterpret_cast<ck3_12002::FamilyRankedInitializeCandidates>(
          base + kInitializeCandidatesRva);
  bindings.candidate_owner_vtable = base + kCandidateOwnerVtableRva;
  bindings.scored_owner_vtable = base + kScoredOwnerVtableRva;
  bindings.scored_row_vtable = base + kScoredRowVtableRva;
  bindings.candidate_backing_allocator = base + kCandidateBackingAllocatorRva;
  bindings.scored_backing_allocator = base + kScoredBackingAllocatorRva;
  return bindings;
}

} // namespace xar::ck3_12004
#endif
