#pragma once

#include "xar_bridge/ck3_12003.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12003::religion::vow_of_poverty_terms12003 {

inline constexpr std::string_view kDecisionId = "take_vow_of_poverty_decision";
inline constexpr std::string_view kSchema = "ck3_12003_vow_of_poverty_terms_v1";

using DecisionHash = std::uint32_t (*)(void *, const char *, std::uint32_t);
using DecisionLookup = const void *(*)(void *, std::uint32_t);
using RootConstruct = void *(*)(void *);
using RootDestroy = void (*)(void *);
using DecisionShown = bool (*)(const void *, void *);
using DecisionCanTake = bool (*)(const void *, void *, void *, const void *, void *);
using DecisionCost = const void *(*)(const void *);
using CostEvaluate = void (*)(const void *, void *, std::int64_t *);
using CostAffordable = bool (*)(const void *, void *, void *, void *);
using ReasonDestroy = void (*)(void *);

struct Bindings {
  bool enabled = false;
  void **decision_database = nullptr;
  const void **decision_fallback = nullptr;
  DecisionHash decision_hash = nullptr;
  DecisionLookup decision_lookup = nullptr;
  RootConstruct root_construct = nullptr;
  RootDestroy root_destroy = nullptr;
  DecisionShown decision_shown = nullptr;
  DecisionCanTake decision_can_take = nullptr;
  DecisionCost decision_cost = nullptr;
  CostEvaluate cost_evaluate = nullptr;
  CostAffordable cost_affordable = nullptr;
  ReasonDestroy reason_destroy = nullptr;
};

struct ResourceCost {
  std::int64_t gold = 0, treasury = 0, prestige = 0, piety = 0;
};

struct Terms {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0, played_character_id = -1;
  std::optional<bool> is_shown, can_take, affordable;
  std::optional<ResourceCost> costs_raw;
  bool reasons_available = false;
  std::optional<std::string> can_take_reasons;
  static constexpr std::int64_t raw_scale = 100'000;
};

Bindings BindVowOfPovertyTermsImage12003(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// The existing owner callback supplies the actual resolved player/frame. This
// fixed decision reader has no actor override, submission or resource effect.
bool ReadVowOfPovertyTerms12003(const Bindings &, void *actual_played_character,
    std::int32_t played_character_id, std::int32_t date_raw,
    std::uint64_t capture_epoch, Terms &) noexcept;
std::string SerializeVowOfPovertyTerms12003(const Terms &);

} // namespace xar::ck3_12003::religion::vow_of_poverty_terms12003
