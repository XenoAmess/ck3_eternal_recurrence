#pragma once
#include "xar_bridge/character_skill_effect12004.hpp"

namespace xar::bridge::character_skill_effect12004 {
using ReadKnight = bool (*)(void *,std::uintptr_t actual_actor,std::int64_t &,
                           std::string &) noexcept;
struct KnightEnvironment { Environment actor{}; ReadKnight read_knight=nullptr; };
struct KnightRequest { Frame expected{}; std::uint32_t character_id=0xFFFFFFFFU; };
struct KnightResult {
  bool available=false,two_pass_stable=false,own_actor_context_verified=false;
  std::string unavailable_reason="not_read";
  Frame frame{};
  std::uint32_t character_id=0xFFFFFFFFU;
  std::optional<std::uint32_t> rite_id,faith_id;
  std::optional<std::int64_t> knight_effectiveness_raw;
  std::optional<std::string> actual_knight_effectiveness_breakdown;
  CallbackProvenance callback_provenance=CallbackProvenance::unavailable;
  bool read_only=true,gameplay_command_submitted=false;
  bool modifier_cache_refreshed=false,cache_generation_time_known=false;
  bool site_attribution_observed=false;
  std::optional<std::int64_t> selected_site_contribution_raw;
};
// Fixed actual-Character query. No arbitrary modifier index, pointer, callback,
// army, selector, native address, stat enum or site attribution is public input.
bool ReadKnightEffectiveness(const KnightEnvironment &,const KnightRequest &,
                            KnightResult &) noexcept;
struct NativeContext;
KnightEnvironment BindKnightNative(NativeContext &) noexcept;
} // namespace xar::bridge::character_skill_effect12004
