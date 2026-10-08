#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/player_prisoner_collection_query_v1_private.hpp"

#include <optional>
#include <string>

namespace xar::ck3_12004 {

struct RetainedTargetStateBindings12004 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  CoreBindings core{};
};

struct RetainedTargetState12004 {
  bool available = false;
  std::string unavailable_reason = "not_evaluated";
  bridge::PlayerPrisonerFrameV1 frame{};
  std::uint32_t target_character_id = 0;
  std::optional<bool> target_alive;
  std::optional<bool> is_imprisoned;
  std::optional<std::uint32_t> jailer_character_id;
  std::string custody_state = "unavailable";
};

RetainedTargetStateBindings12004 BindRetainedTargetStateImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// Same-frame raw observation for an independently retained full target ID.
// Missing custody relation is free only for a resolved, alive target.
bool ReadRetainedTargetState12004(
    const RetainedTargetStateBindings12004 &bindings,
    const bridge::PlayerPrisonerCollectionAccessV1 &access,
    const bridge::PlayerPrisonerFrameV1 &expected_frame,
    std::uint32_t target_character_id,
    RetainedTargetState12004 &output) noexcept;

std::string SerializeRetainedTargetState12004(
    const RetainedTargetState12004 &output);

} // namespace xar::ck3_12004
