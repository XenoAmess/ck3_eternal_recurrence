#pragma once

#include "xar_bridge/ck3_12004_phase_character.hpp"
#include "xar_bridge/ck3_12002_religion_context.hpp"

#include <array>
#include <optional>
#include <string>

namespace xar::ck3_12004::religion::pilgrimage_traits {

inline constexpr std::array<std::string_view, 4> kTraitKeys{
    "pilgrim", "hajjaj", "lifestyle_scholar", "lifestyle_mystic"};
inline constexpr std::int64_t kExperienceScale = 100000;

struct Row {
  std::optional<bool> present;
  std::optional<std::int64_t> experience_raw;
};

struct Snapshot {
  bool available = false;
  std::string unavailable_reason = "not_captured";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::array<Row, 4> traits{};
};

// Only the four fixed definitions are read. No effect or trait write is bound.
// The enclosing religion mailbox owns the paused actor/frame and later recheck.
bool ReadPlayerPilgrimageTraits12004(
    const phase_character::Bindings &bindings, void *character,
    const ck3_12002::religion::Context &context, Snapshot &output) noexcept;
std::string SerializePlayerPilgrimageTraits12004(const Snapshot &snapshot);

} // namespace xar::ck3_12004::religion::pilgrimage_traits
