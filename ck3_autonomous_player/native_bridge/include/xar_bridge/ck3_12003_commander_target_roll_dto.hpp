#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12003 {

// A requested target context for one native candidate, including candidates
// which the separate player/manual CanAssign predicate currently rejects.
// The endpoints are independent signed native integers; no ordering is imposed.
struct CommanderCandidateTargetRollBoundsSnapshot {
  std::string_view status = "unavailable";
  std::string_view source = "native_current_candidate_target_roll_context";
  std::int32_t source_target_province_id = -1;
  std::optional<std::int32_t> effective_min_roll;
  std::optional<std::int32_t> effective_max_roll;
  std::string unavailable_reason = "candidate_target_roll_not_read";
};

} // namespace xar::ck3_12003
