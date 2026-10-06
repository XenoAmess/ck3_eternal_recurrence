#pragma once

#include "xar_bridge/ck3_12002_religion_context.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/religion_reform12002_window.hpp"

#include <optional>
#include <string>

namespace xar::ck3_12002::religion_reform::creation_terms12003 {

inline constexpr std::uintptr_t kDraftDivergenceRva = 0x14F14B0;
inline constexpr std::uintptr_t kFaithCreationThresholdRva = 0x5C68C68;
inline constexpr std::uintptr_t kNativeCreateFaithOrReformRva = 0x2BDCA90;
inline constexpr std::uintptr_t kRiteStorageGlobalRva = 0x5D1E2F8;
inline constexpr std::uintptr_t kFaithStorageGlobalRva = 0x5D1E300;
inline constexpr std::size_t kWindowPriceDraftOffset = 0xB28;

// Cached complete native body: output first, actual CRiteCreationWindow second.
// The native getter uses a null tooltip for its numeric divergence sum.
using DraftDivergenceGetter = std::int64_t *(*)(std::int64_t *, const void *);
// Independent command-dispatch predicate: actor-current Faith, price subdraft.
// It neither validates the complete command nor creates/reforms a Faith.
using NativeCreateFaithOrReform = bool (*)(const void *, const void *);

struct Bindings {
  bool enabled = false;
  void *const *rite_storage_global = nullptr;
  void *const *faith_storage_global = nullptr;
  DraftDivergenceGetter draft_divergence = nullptr;
  // Direct address of the loaded signed Q100000 define, not pointer-to-pointer.
  const std::int64_t *creation_threshold_raw = nullptr;
  NativeCreateFaithOrReform native_create_faith_or_reform = nullptr;
};

struct DraftCreationTerms {
  bool available = false;
  std::string failure = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::uint32_t played_character_id = religion::kAbsentReference;
  // Window-source identities and actor-current Faith remain independent.
  std::optional<std::uint32_t> source_rite_id;
  std::optional<std::uint32_t> source_faith_id;
  std::optional<std::uint32_t> source_main_rite_id;
  std::optional<std::uint32_t> actor_faith_id;
  std::optional<std::int64_t> draft_divergence_raw;
  std::optional<std::int64_t> faith_creation_threshold_raw;
  // UI signed >= comparison and native command lane are separate observations.
  std::optional<bool> divergence_results_in_faith_creation;
  std::optional<bool> native_create_faith_or_reform;
  static constexpr std::int64_t raw_scale = 100'000;
};

// Pure address binding for the exact .3 SHA. The legacy .2 adapter is excluded.
Bindings BindDraftCreationTermsImage12003(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// The existing paused application-main owner supplies its actual current-window
// observation and independently resolved actor-current Faith/full identity.
// No process discovery, draft construction, selection, tooltip or command runs.
bool ReadCurrentDraftCreationTerms12003(const Bindings &bindings,
    const DraftWindowView &actual_window, const void *same_frame_actor_faith,
    std::uint32_t actual_actor_faith_id, std::uint64_t capture_epoch,
    DraftCreationTerms &output) noexcept;
std::string SerializeCurrentDraftCreationTerms12003(const DraftCreationTerms &);

} // namespace xar::ck3_12002::religion_reform::creation_terms12003
