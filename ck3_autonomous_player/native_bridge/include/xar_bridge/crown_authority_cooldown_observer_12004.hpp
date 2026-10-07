#pragma once

#include "xar_bridge/ck3_12002_phase_definitions.hpp"

#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004::crown_cooldown {

struct Bindings {
  ck3_12002::PhaseDefinitionBindings identifiers{};
};

// Raw scalar timing is source-closed. Calendar meaning still requires the
// same-context daily caller or the native date converter; it is not 24 CDate
// ticks merely because the current frame publishes a CDate.
struct Observation {
  bool read_available = false;
  std::optional<bool> present;
  std::optional<bool> timed;
  std::optional<std::int32_t> expiry_raw;
  std::optional<std::int32_t> current_clock_raw;
  std::optional<std::int32_t> remaining_raw;
  std::optional<std::int32_t> retry_date_raw;
  std::string_view expiry_type = "signed32_scalar_clock_counter";
  std::string_view remaining_unit = "scalar_clock_step_calendar_unqualified";
};

Bindings BindImage(std::uintptr_t image_base,
                   std::string_view executable_sha256) noexcept;

// Existing owning paused capture supplies the played full CharacterID and
// frame date. This leaf uses the shared identifier/context route, never a law
// action. An absent row can request fresh terms now; a positive calendar retry
// date remains unqualified until its actual source unit is closed.
bool Read(const Bindings &, std::int32_t played_character_id,
          std::int32_t frame_date_raw, Observation &) noexcept;

} // namespace xar::ck3_12004::crown_cooldown
