#pragma once

#include "xar_bridge/projected_contact_scope_v1.hpp"

#include <string_view>

namespace xar::game {

inline constexpr std::string_view kProjectedContactScopeV1StepPrefix =
    "query-projected-contact-scope-v1-";
inline constexpr std::string_view kProjectedContactScopeV1Capability =
    "game.command.query-projected-contact-scope-v1-N";

bool ParseProjectedContactScopeV1Step(
    std::string_view step, ProjectedContactScopeRequest &output) noexcept;

std::string SerializeProjectedContactScopeV1Snapshot(
    const ProjectedContactScopeSnapshot &scope);

} // namespace xar::game
