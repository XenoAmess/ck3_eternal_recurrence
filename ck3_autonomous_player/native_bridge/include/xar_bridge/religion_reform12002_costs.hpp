#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include <optional>
#include <string>

namespace xar::ck3_12002::religion_reform {

inline constexpr std::uintptr_t kRiteCreationPietyCostRva = 0x14F57C0;
inline constexpr std::uintptr_t kRiteCreationPietyMissingRva = 0x14F58E0;
inline constexpr std::uintptr_t kRiteCreationEditOwnedRiteRva = 0x14F4400;
inline constexpr std::size_t kRiteCreationActorOffset = 0xCC;
inline constexpr std::size_t kRiteCreationSourceRiteOffset = 0xC8;
inline constexpr std::size_t kRiteCreationPriceDraftOffset = 0xB28;

using WindowFixedGetter = std::int64_t *(*)(void *, std::int64_t *);
using WindowBoolGetter = bool (*)(void *);

struct CostBindings {
  bool enabled = false;
  WindowFixedGetter piety_cost = nullptr;
  WindowFixedGetter piety_missing = nullptr;
  WindowBoolGetter editing_owned_current_rite = nullptr;
};

// Supplied by the existing paused application-main owner after resolving the
// actual CRiteCreationWindow. This library neither creates nor opens a draft.
struct CurrentDraftView {
  void *window = nullptr;
  std::int32_t played_character_id = -1;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
};

enum class CostFailure {
  none, bindings_unavailable, draft_unavailable, draft_actor_mismatch,
  native_quote_unavailable, quote_changed,
};

struct CostQuote {
  bool available = false;
  CostFailure failure = CostFailure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::optional<std::uint32_t> source_rite_id;
  std::optional<bool> editing_owned_current_rite;
  std::optional<std::int64_t> piety_cost_raw;
  // Exact native cost minus current actor piety; negative is meaningful.
  std::optional<std::int64_t> piety_missing_signed_raw;
  std::optional<bool> has_enough_piety;
  static constexpr std::int64_t raw_scale = 100'000;
};

CostBindings BindRiteCreationCostsImage12002(std::uintptr_t image_base,
                                            std::string_view executable_sha256) noexcept;
bool ReadCurrentRiteCreationCosts12002(const CostBindings &bindings,
                                     const CurrentDraftView &view,
                                     CostQuote &output) noexcept;
const char *RiteCreationCostFailureKey(CostFailure failure) noexcept;
std::string SerializeCurrentRiteCreationCosts12002(const CostQuote &quote);

} // namespace xar::ck3_12002::religion_reform
