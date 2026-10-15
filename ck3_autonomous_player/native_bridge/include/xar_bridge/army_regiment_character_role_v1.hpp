#pragma once
#include <cstdint>
#include <optional>
#include <string_view>
namespace xar::game {
struct ArmyRegimentCharacterRoleV1 {
  std::string_view source = "native_selected_ArRg_character_role_raw";
  std::string_view status = "unavailable";
  std::int32_t army_regiment_id = -1, native_carmy_id = -1;
  std::optional<std::int32_t> arrg_army_id_140, character_raw_id_148;
  std::optional<std::int32_t> resolved_character_id;
  std::optional<std::uint32_t> character_magic_1c;
  std::optional<bool> resolution_used_fallback, native_character_predicate;
  std::optional<bool> character_extension_present;
  std::optional<std::int32_t> extension_army_id_f4, extension_arrg_id_f8;
  bool same_ArRg_instance_after = false;
  std::string_view unavailable_reason = "character_role_inputs_unavailable";
  friend bool operator==(const ArmyRegimentCharacterRoleV1 &, const ArmyRegimentCharacterRoleV1 &) = default;
};
}
