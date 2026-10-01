#include "xar_bridge/religion_reform12002_schedule.hpp"
#include <cstring>

namespace xar::ck3_12002::religion_reform {
namespace {
template <typename T> T ScheduleLoad(const void *p, std::size_t off) noexcept {
  T out{};
  std::memcpy(&out, static_cast<const std::byte *>(p) + off, sizeof(out));
  return out;
}
}
ScheduleBindings BindReformScheduleImage12002(
    std::uintptr_t base, std::string_view sha) noexcept {
  ScheduleBindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.highest_tier = reinterpret_cast<ScheduleHighestTierGetter>(
      base + kScheduleHighestTierRva);
  b.independent_ruler = reinterpret_cast<ScheduleIndependentRulerGetter>(
      base + kScheduleIndependentRulerRva);
  b.rare_periods = reinterpret_cast<const std::int32_t *const *>(
      base + kScheduleRarePeriodsRva);
  b.reformation_toggle = reinterpret_cast<const std::uint8_t *>(
      base + kScheduleReformationToggleRva);
  return b;
}
ScheduleInputs ReadReformScheduleInputs12002(
    const ScheduleBindings &b, void *actor, std::uint32_t expected_id,
    const void *ai) noexcept {
  ScheduleInputs out{};
  if (!b.enabled || !b.highest_tier || !b.independent_ruler ||
      !b.rare_periods || !b.reformation_toggle) return out;
  out.status = ScheduleStatus::actor_unavailable;
  if (!actor || expected_id == 0xFFFFFFFFU ||
      ScheduleLoad<std::uint32_t>(actor, kScheduleActorIdOffset) != expected_id ||
      ScheduleLoad<std::uint32_t>(actor, kScheduleActorTagOffset) != 0x43686172U)
    return out;
  out.actor_id = expected_id;
  out.highest_tier = b.highest_tier(actor);
  out.current_independent_ruler = b.independent_ruler(actor);
  out.reformation_enabled = *b.reformation_toggle != 0;
  out.status = ScheduleStatus::configuration_unavailable;
  if (out.highest_tier < 0 || out.highest_tier >= 7 || !*b.rare_periods)
    return out;
  out.rare_period = (*b.rare_periods)[out.highest_tier];
  if (out.rare_period <= 0) return out;
  out.status = ScheduleStatus::observed;
  if (!ai) return out;
  out.ai_status = ScheduleAIStatus::invalid_state;
  if (ScheduleLoad<std::uint32_t>(ai, 0x28) != 0x41495374U) return out;
  out.ai_status = ScheduleAIStatus::actor_mismatch;
  if (ScheduleLoad<void *>(ai, kScheduleAIActorOffset) != actor) return out;
  out.ai_government_flags = ScheduleLoad<std::uint16_t>(
      ai, kScheduleAIGovernmentFlagsOffset);
  out.ai_independent_flags = ScheduleLoad<std::uint8_t>(
      ai, kScheduleAIIndependentFlagsOffset);
  out.ai_active = ScheduleLoad<std::uint8_t>(ai, kScheduleAIActiveOffset);
  out.ai_special = ScheduleLoad<std::uint8_t>(ai, kScheduleAISpecialOffset);
  out.cached_independent_ruler = (out.ai_independent_flags & 1U) != 0;
  out.cached_government_bit6 = (out.ai_government_flags & 0x40U) != 0;
  out.handler_cache_gates_pass = out.cached_independent_ruler &&
      out.cached_government_bit6 && out.ai_special == 0;
  out.ai_status = ScheduleAIStatus::gates_only;
  const auto *extension = ScheduleLoad<const void *>(
      ai, kScheduleAIExtensionOffset);
  if (!extension) return out;
  out.rare_countdown_prepare_ticks = ScheduleLoad<std::int32_t>(
      extension, kScheduleRareCountdownOffset);
  out.rare_selected_raw = ScheduleLoad<std::uint8_t>(
      extension, kScheduleRareSelectedOffset);
  out.ai_status = ScheduleAIStatus::observed;
  return out;
}
} // namespace xar::ck3_12002::religion_reform
