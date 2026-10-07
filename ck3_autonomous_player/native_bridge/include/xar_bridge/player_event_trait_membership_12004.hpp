#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_phase_character.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12004::person_events {

struct Bindings {
  bool enabled = false;
  CoreBindings core;
  phase_character::Bindings traits;
};

struct PlayerEventTraitMembershipV1 {
  bool available = false;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  bool lifestyle_poet = false;
  bool journaller = false;
  std::string unavailable_reason = "not_observed";
};

Bindings BindImage(std::uintptr_t image_base,
                   std::string_view executable_sha256) noexcept;

// Caller uses its existing ordinary owning-thread read-only frame. The revision
// is that frame's native revision, not the independently published public one.
bool ReadPlayerEventTraitMembershipV1(
    const Bindings &bindings, std::uint64_t expected_native_revision,
    std::int32_t expected_date_raw, std::int32_t expected_played_character_id,
    PlayerEventTraitMembershipV1 &output) noexcept;

std::string SerializePlayerEventTraitMembershipV1(
    const PlayerEventTraitMembershipV1 &value);

} // namespace xar::ck3_12004::person_events
