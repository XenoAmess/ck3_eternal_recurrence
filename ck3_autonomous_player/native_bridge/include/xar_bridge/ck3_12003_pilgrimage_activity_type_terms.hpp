#pragma once

#include "xar_bridge/ck3_12003.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12003::religion::pilgrimage {

inline constexpr std::string_view kActivityId = "activity_pilgrimage";
inline constexpr std::string_view kSchema = "ck3_12003_pilgrimage_activity_type_terms_v1";

using ActivityCanPlan = bool (*)(const void *, void *);
using ActivityCanPlanTooltip = void *(*)(void *, const void *, void *);
using ReasonDestroy = void (*)(void *);

struct Bindings {
  bool enabled = false;
  void **activity_type_database = nullptr;
  std::uintptr_t activity_type_vtable = 0;
  ActivityCanPlan can_plan = nullptr;
  ActivityCanPlanTooltip can_plan_tooltip = nullptr;
  ReasonDestroy reason_destroy = nullptr;
};

struct Terms {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0, played_character_id = -1;
  std::optional<bool> can_plan;
  bool reasons_available = false;
  std::optional<std::string> can_plan_reasons;
};

Bindings BindPlayerPilgrimageActivityTypeTermsImage12003(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// Fixed ActivityType and the actual resolved player supplied by the existing
// owner callback. CanPlan does not open a planner or imply final CanStart.
bool ReadPlayerPilgrimageActivityTypeTerms12003(const Bindings &, void *actual_played_character,
    std::int32_t played_character_id, std::int32_t date_raw,
    std::uint64_t capture_epoch, Terms &) noexcept;
std::string SerializePlayerPilgrimageActivityTypeTerms12003(const Terms &);

} // namespace xar::ck3_12003::religion::pilgrimage
