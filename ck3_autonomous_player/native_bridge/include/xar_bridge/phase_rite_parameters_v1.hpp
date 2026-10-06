#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {
enum class PhaseRiteParameterStatusV1 { available, absent, unavailable };

// Current adopted Rite of one already observed Character occurrence. The
// surrounding commander/knight row supplies Army, Regiment and role identity.
struct PhaseRiteParametersV1 {
  PhaseRiteParameterStatusV1 status = PhaseRiteParameterStatusV1::unavailable;
  std::uint32_t source_character_id = 0;
  std::uint32_t raw_adopted_rite_id = 0xFFFFFFFFU;
  std::optional<std::uint32_t> rite_id;
  std::optional<std::uint32_t> faith_id;
  bool boolean_parameters_complete = false;
  std::vector<std::string> boolean_parameter_keys;
  std::string unavailable_reason;
  friend bool operator==(const PhaseRiteParametersV1 &,
                         const PhaseRiteParametersV1 &) = default;
};
} // namespace xar::game
