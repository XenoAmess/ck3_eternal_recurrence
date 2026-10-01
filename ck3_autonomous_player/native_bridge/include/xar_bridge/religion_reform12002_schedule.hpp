#pragma once
#include "xar_bridge/ck3_12002.hpp"
#include <cstddef>
#include <cstdint>

namespace xar::ck3_12002::religion_reform {
inline constexpr std::uintptr_t kScheduleHighestTierRva = 0x28AC6B0;
inline constexpr std::uintptr_t kScheduleIndependentRulerRva = 0x28C0000;
inline constexpr std::uintptr_t kScheduleRarePeriodsRva = 0x5449D90;
inline constexpr std::uintptr_t kScheduleReformationToggleRva = 0x5448579;
inline constexpr std::size_t kScheduleActorIdOffset = 0x18;
inline constexpr std::size_t kScheduleActorTagOffset = 0x1C;
inline constexpr std::size_t kScheduleAIActorOffset = 0x18;
inline constexpr std::size_t kScheduleAIExtensionOffset = 0x20;
inline constexpr std::size_t kScheduleAIGovernmentFlagsOffset = 0x14;
inline constexpr std::size_t kScheduleAIIndependentFlagsOffset = 0x16;
inline constexpr std::size_t kScheduleAIActiveOffset = 0x2C;
inline constexpr std::size_t kScheduleAISpecialOffset = 0x2E;
inline constexpr std::size_t kScheduleRareCountdownOffset = 0x284;
inline constexpr std::size_t kScheduleRareSelectedOffset = 0x29B;

using ScheduleHighestTierGetter = std::int32_t (*)(void *actor);
using ScheduleIndependentRulerGetter = bool (*)(void *actor);
struct ScheduleBindings {
  bool enabled = false;
  ScheduleHighestTierGetter highest_tier = nullptr;
  ScheduleIndependentRulerGetter independent_ruler = nullptr;
  const std::int32_t *const *rare_periods = nullptr;
  const std::uint8_t *reformation_toggle = nullptr;
};
enum class ScheduleStatus { bindings_unavailable, actor_unavailable,
                            configuration_unavailable, observed };
enum class ScheduleAIStatus { not_supplied, actor_mismatch, invalid_state,
                              gates_only, observed };
struct ScheduleInputs {
  ScheduleStatus status = ScheduleStatus::bindings_unavailable;
  ScheduleAIStatus ai_status = ScheduleAIStatus::not_supplied;
  std::uint32_t actor_id = 0xFFFFFFFFU;
  std::int32_t highest_tier = -1;
  std::int32_t rare_period = 0;
  bool reformation_enabled = false;
  bool current_independent_ruler = false;
  std::uint16_t ai_government_flags = 0;
  std::uint8_t ai_independent_flags = 0;
  std::uint8_t ai_active = 0;
  std::uint8_t ai_special = 0;
  bool cached_independent_ruler = false;
  bool cached_government_bit6 = false;
  bool handler_cache_gates_pass = false;
  // Units are prepare invocations until the outer game-day caller is proved.
  std::int32_t rare_countdown_prepare_ticks = 0;
  std::uint8_t rare_selected_raw = 0;
};
ScheduleBindings BindReformScheduleImage12002(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;
// Existing paused owner supplies actor identity and, optionally, its actual AI
// state. This API does not discover controllers or call any scheduler/action.
ScheduleInputs ReadReformScheduleInputs12002(
    const ScheduleBindings &bindings, void *actor,
    std::uint32_t expected_actor_id, const void *optional_actual_ai) noexcept;
} // namespace xar::ck3_12002::religion_reform
