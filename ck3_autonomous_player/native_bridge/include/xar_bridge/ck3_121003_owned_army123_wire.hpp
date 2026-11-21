#pragma once
#include "xar_bridge/ck3_121003_full_profile111.hpp"
#include "xar_bridge/game_contract.hpp"
#include <string>
#include <string_view>

namespace xar::ck3_121003::owned_army123 {
// This is producer provenance already carried by the state frame, not a new
// wire flag or a deduction from default ArmySnapshot member values.
inline bool IdentityFieldsOnly(bool enabled, std::string_view version,
    std::string_view executable_sha256, std::string_view adapter_id) noexcept {
  return enabled && version == full111::kGameVersion &&
      executable_sha256 == full111::kExecutableSha256 &&
      adapter_id == full111::kAdapterId;
}
inline void AppendIdentity(std::string &json, const game::ArmySnapshot &army) {
  // Preserve every signed full-ID bit; never substitute a low24 index.
  json += "{\"army_id\":";
  json += std::to_string(army.army_id);
  json += ",\"owner_character_id\":";
  json += std::to_string(army.owner_character_id);
  json += ",\"controllable\":";
  json += army.controllable ? "true" : "false";
  json += '}';
}
} // namespace xar::ck3_121003::owned_army123
