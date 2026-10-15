#pragma once
#include <cstdint>
#include <optional>
#include <string>
namespace xar::game {
// Administrative source/switch observation. Never a permission result or ADD event.
struct ArmyRefillPermissionSwitchV1 {
  std::string status="unavailable", unavailable_reason, source_branch="unresolved";
  std::optional<std::int32_t> persistent_full_id;
  std::optional<std::uint32_t> definition_magic_38_raw;
  std::optional<std::int32_t> character_ref_12c_raw, title_ref_130_raw;
  std::optional<std::int32_t> resolved_title_full_id;
  std::optional<bool> title_used_fallback;
  std::optional<std::int32_t> selected_character_raw_full_id, resolved_character_full_id;
  std::optional<bool> character_used_fallback;
  std::optional<std::uint32_t> character_magic_raw;
  std::optional<bool> military_component_present;
  std::optional<std::int32_t> raw_byte_4a9;
  std::optional<bool> enabled;
  bool identity_consistent=false;
  friend bool operator==(const ArmyRefillPermissionSwitchV1 &,const ArmyRefillPermissionSwitchV1 &)=default;
};
} // namespace xar::game
