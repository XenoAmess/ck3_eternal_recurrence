#pragma once

#include "xar_bridge/ck3_12002_family_projection.hpp"
#include "xar_bridge/ck3_12002_family_value.hpp"

#include <optional>

namespace xar::ck3_12002::family_value {

// The owning rich query samples this optional loaded operand once for its
// whole paused frame. Missing binding/read is independent of legacy row status.
inline std::optional<std::int64_t> ReadCandidateFertilityFloorRawV1(
    const Bindings &bindings,
    const FamilyProjectionBindings &projection) noexcept {
  if (!bindings.enabled || bindings.candidate_fertility_floor == nullptr ||
      projection.read_memory == nullptr)
    return std::nullopt;
  std::int64_t raw = 0;
  if (!projection.read_memory(
          projection.memory_context,
          reinterpret_cast<std::uintptr_t>(bindings.candidate_fertility_floor),
          &raw, sizeof(raw)))
    return std::nullopt;
  return raw;
}

} // namespace xar::ck3_12002::family_value
