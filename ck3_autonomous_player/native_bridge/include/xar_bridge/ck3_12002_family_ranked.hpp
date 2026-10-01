#pragma once

#include "xar_bridge/ck3_12002_family.hpp"
#include "xar_bridge/marriage_matchmaking_observer_v1.hpp"
#include "xar_bridge/marriage_matchmaking_source_adapter_v1.hpp"

namespace xar::ck3_12002 {
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)

// The legacy structs are wire values only. Native addresses, layout, producer
// ownership and admission are implemented exclusively for 1.20.0.2.
using FamilyRankedReadTier = std::int32_t (*)(void *);
using FamilyRankedEnumerate = void (*)(void *, std::int32_t, bool, std::int32_t, void *);
using FamilyRankedScore = void (*)(void *, const void *, void *, void *);
using FamilyRankedSortScored = void (*)(void *, void *);
using FamilyRankedDestroyScoredRow = void *(*)(void *, std::uint32_t);
using FamilyRankedInitializeScored = void *(*)(void *);
using FamilyRankedReleaseBuffer = void (*)(void *, void *, std::size_t);
using FamilyRankedInitializeCandidates = void (*)(void *, void **, std::int32_t *);

struct FamilyRankedBindings {
  bool enabled = false;
  FamilyBindings family{};
  FamilyRankedReadTier read_native_tier = nullptr;
  const std::int32_t *const *native_cap_table_slot = nullptr;
  FamilyRankedEnumerate enumerate_candidates = nullptr;
  FamilyRankedScore score_candidates = nullptr;
  FamilyRankedSortScored sort_scored_candidates = nullptr;
  FamilyRankedDestroyScoredRow destroy_scored_row = nullptr;
  FamilyRankedInitializeScored initialize_scored_container = nullptr;
  FamilyRankedReleaseBuffer release_native_buffer = nullptr;
  FamilyRankedInitializeCandidates initialize_candidate_buffer = nullptr;
  std::uintptr_t candidate_owner_vtable = 0;
  std::uintptr_t scored_owner_vtable = 0;
  std::uintptr_t scored_row_vtable = 0;
  std::uintptr_t candidate_backing_allocator = 0;
  std::uintptr_t scored_backing_allocator = 0;
};

struct FamilyRankedAccessV1 {
  void *context = nullptr;
  bridge::CaptureMarriageMatchmakingFrameV1 capture_frame = nullptr;
  bridge::IsMarriageMatchmakingMainThreadV1 is_main_thread = nullptr;
};

struct FamilyRankedDiagnosticsV1 {
  bridge::MarriageMatchmakingSourceAdapterFailureV1 source_failure =
      bridge::MarriageMatchmakingSourceAdapterFailureV1::none;
  std::int32_t native_cap = 0;
  std::int32_t native_pool_count = 0;
  std::int32_t native_scored_count = 0;
};

FamilyRankedBindings BindFamilyRankedImage(std::uintptr_t module_base,
    std::string_view executable_sha256) noexcept;

// Application-main, paused query. The subject must be the actual played
// character and its own matchmaker. Missing native Strategy is observable as
// ranked_source_unavailable; storage order never substitutes for native rank.
bool ReadMarriageMatchmakingObservationV1(const FamilyRankedBindings &,
    const FamilyRankedAccessV1 &,
    const bridge::MarriageMatchmakingObserverRequestV1 &,
    bridge::MarriageMatchmakingObservationV1 &,
    FamilyRankedDiagnosticsV1 *diagnostics = nullptr) noexcept;

#endif
} // namespace xar::ck3_12002
