#pragma once

#include "xar_bridge/ck3_12002_family_projection.hpp"
#include "xar_bridge/ck3_12002_family_value.hpp"

#include <optional>

namespace xar::ck3_12002::family_value {

// One loaded signed DWORD sample is shared by the owning rich frame.
// Missing binding/read leaves the independent observer unavailable.
inline std::optional<std::int32_t> ReadCandidateScorerAgeUpperRawV1(
    const Bindings &bindings,
    const FamilyProjectionBindings &projection) noexcept {
  if (!bindings.enabled || bindings.candidate_scorer_age_upper == nullptr ||
      projection.read_memory == nullptr)
    return std::nullopt;
  std::int32_t raw = 0;
  if (!projection.read_memory(
          projection.memory_context,
          reinterpret_cast<std::uintptr_t>(bindings.candidate_scorer_age_upper),
          &raw, sizeof(raw)))
    return std::nullopt;
  return raw;
}

} // namespace xar::ck3_12002::family_value
