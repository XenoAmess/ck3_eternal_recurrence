#pragma once

#include <cstdint>
#include <optional>
#include <string>

namespace xar::game {
struct PhaseWarmongerCoreV1 {
  bool available = false;
  std::uint32_t source_character_id = 0;
  std::uint32_t raw_adopted_rite_id = 0xFFFFFFFFU;
  std::optional<std::uint32_t> rite_id;
  std::string rite_resolution = "unresolved";
  std::optional<std::string> target_tenet_key;
  std::optional<bool> warmonger_core_membership;
  std::string unavailable_reason = "bindings_unavailable";
  friend bool operator==(const PhaseWarmongerCoreV1 &, const PhaseWarmongerCoreV1 &) = default;
};
} // namespace xar::game
