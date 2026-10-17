#include "xar_bridge/ck3_12004_holy_site_snapshot.hpp"

namespace xar::ck3_12004::religion::holy_site {
namespace {
std::string Quote(std::string_view text) {
  constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char c : text) {
    if (c == '"' || c == '\\') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 0x20) { out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; }
    else out += static_cast<char>(c);
  }
  return out + '"';
}
const char *Bool(bool value) noexcept { return value ? "true" : "false"; }
std::string Ref(std::uint32_t value) { return value == 0xFFFFFFFFU ? "null" : std::to_string(value); }
std::string Ref(std::optional<std::uint32_t> value) { return value ? Ref(*value) : "null"; }
std::string Reason(std::string_view value) { return value.empty() ? "null" : Quote(value); }
std::string Ids(const std::vector<std::uint32_t> &ids) {
  std::string out = "[";
  for (const auto id : ids) { if (out.size() > 1) out += ','; out += std::to_string(id); }
  return out + ']';
}
std::string SiteJson(const Site &site) {
  std::string faiths = "[";
  for (const auto &faith : site.associated_faiths) {
    if (faiths.size() > 1) faiths += ',';
    faiths += "{\"faith_id\":" + Ref(faith.faith_id) +
        ",\"available\":" + Bool(faith.available) +
        ",\"faith_lists_site\":" + (faith.available ? Bool(faith.faith_lists_site) : "null") +
        ",\"eminent\":" + (faith.available ? Bool(faith.eminent) : "null") +
        ",\"unavailable_reason\":" + Reason(faith.unavailable_reason) + '}';
  }
  faiths += ']';
  return "{\"available\":" + std::string(Bool(site.available)) +
      ",\"holy_site_id\":" + Ref(site.holy_site_id) +
      ",\"type_key\":" + (site.type_key.empty() ? "null" : Quote(site.type_key)) +
      ",\"barony_title_id\":" + Ref(site.barony_title_id) +
      ",\"associated_faiths\":" + faiths +
      ",\"inventory\":{\"available\":" + Bool(site.inventory.available) +
      ",\"identity_kind\":\"embedded_holy_site_inventory\",\"owner_kind\":\"holy_site\"" +
      ",\"owner_holy_site_id\":" + Ref(site.inventory.owner_holy_site_id) +
      ",\"native_holy_site_owner_id\":" + Ref(site.inventory.native_holy_site_owner_id) +
      ",\"native_character_owner_id\":" + Ref(site.inventory.native_character_owner_id) +
      ",\"artifact_ids\":" + (site.inventory.available ? Ids(site.inventory.artifact_ids) : "null") +
      ",\"artifact_objects_resolved\":false,\"unavailable_reason\":" +
      Reason(site.inventory.unavailable_reason) + '}' +
      ",\"unavailable_reason\":" + Reason(site.unavailable_reason) + '}';
}
} // namespace

std::string SerializeHolySiteSnapshot12004(const Snapshot &value) {
  std::string sites = "[";
  for (const auto &site : value.current_faith_sites) {
    if (sites.size() > 1) sites += ',';
    sites += SiteJson(site);
  }
  sites += ']';
  std::string roster = "[";
  for (const auto &entry : value.loaded_registry_roster) {
    if (roster.size() > 1) roster += ',';
    roster += "{\"holy_site_id\":" + Ref(entry.holy_site_id) +
        ",\"type_key\":" + Quote(entry.type_key) +
        ",\"barony_title_id\":" + Ref(entry.barony_title_id) + '}';
  }
  roster += ']';
  const auto &window = value.window_model;
  return "{\"schema\":\"ck3_12004_player_holy_site_v1\",\"game_version\":\"1.20.0.4\","
      "\"executable_sha256\":" + Quote(ck3_12004::kExecutableSha256) +
      ",\"available\":" + Bool(value.available) +
      ",\"unavailable_reason\":" + Reason(value.unavailable_reason) +
      ",\"capture_epoch\":" + std::to_string(value.capture_epoch) +
      ",\"date_raw\":" + std::to_string(value.date_raw) +
      ",\"played_character_id\":" + std::to_string(value.played_character_id) +
      ",\"player_rite_id\":" + Ref(value.player_rite_id) +
      ",\"player_faith_id\":" + Ref(value.player_faith_id) +
      ",\"requested_holy_site_id\":" + Ref(value.requested_holy_site_id) +
      ",\"current_faith_holy_site_ids\":" + Ids(value.current_faith_holy_site_ids) +
      ",\"current_faith_sites\":" + sites +
      ",\"loaded_registry_roster_available\":" + Bool(value.loaded_registry_roster_available) +
      ",\"loaded_registry_slot_count\":" + std::to_string(value.loaded_registry_slot_count) +
      ",\"loaded_registry_unreadable_slots\":" + std::to_string(value.loaded_registry_unreadable_slots) +
      ",\"loaded_registry_roster\":" + roster +
      ",\"registry_roster_is_native_adoption_candidates\":false" +
      ",\"window_model\":{\"available\":" + Bool(window.available) +
      ",\"present\":" + (window.available ? Bool(window.present) : "null") +
      ",\"root_present\":" + (window.available ? Bool(window.root_present) : "null") +
      ",\"holy_site_id\":" + Ref(window.holy_site_id) +
      ",\"holy_site_item_raw\":" + Ref(window.holy_site_item_raw) +
      ",\"rendered_visibility_observed\":false,\"unavailable_reason\":" + Reason(window.unavailable_reason) + '}' +
      ",\"selection_source\":" + Quote(value.selection_source) +
      ",\"selected_holy_site\":" + (value.selected_holy_site ? SiteJson(*value.selected_holy_site) : "null") +
      ",\"active_state_observed\":false,\"relic_recognition_observed\":false,\"beneficiaries_observed\":false," 
      "\"adoption_legality_observed\":false,\"read_only\":true}";
}
std::string SerializeHolySiteCommand12004(const Snapshot &value, std::string_view request_id,
    std::uint64_t revision, std::int64_t date_raw) {
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quote(request_id) +
      ",\"ok\":true,\"result\":{\"step\":\"query-player-holy-site-v1\",\"accepted\":true,"
      "\"status\":" + Quote(value.available ? "observed" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":\"1.20.0.4\","
      "\"executable_sha256\":" + Quote(ck3_12004::kExecutableSha256) +
      ",\"domain_key\":\"player_holy_site_v1\",\"backend_id\":\"ck3-1.20.0.4-native-player-holy-site-v1\","
      "\"snapshot_revision\":" + std::to_string(revision) +
      ",\"date_raw\":" + std::to_string(date_raw) + ",\"player_holy_site\":" +
      SerializeHolySiteSnapshot12004(value) + "}}";
}
} // namespace xar::ck3_12004::religion::holy_site
