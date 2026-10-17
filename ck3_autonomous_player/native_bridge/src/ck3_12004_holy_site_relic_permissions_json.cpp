#include "xar_bridge/ck3_12004_holy_site_relic_permissions.hpp"

namespace xar::ck3_12004::religion::relic_permissions {
namespace {
std::string Quote(std::string_view s){
 static constexpr char hex[]="0123456789abcdef";std::string out="\"";
 for(const unsigned char c:s){if(c=='"'||c=='\\'){out+='\\';out+=static_cast<char>(c);}
  else if(c<0x20){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}else out+=static_cast<char>(c);}
 return out+'"';
}
std::string Bool(bool v){return v?"true":"false";}
template<class T>std::string Number(const std::optional<T>&v){return v?std::to_string(*v):"null";}
std::string Boolean(const std::optional<bool>&v){return v?Bool(*v):"null";}
std::string Reason(const std::string&s){return s.empty()?"null":Quote(s);}
std::string Ids(const std::vector<std::uint32_t>&v){std::string out="[";for(const auto id:v){if(out.size()>1)out+=',';out+=std::to_string(id);}return out+']';}
std::string Observed(const ObservedBool&v){return "{\"available\":"+Bool(v.available)+",\"value\":"+Boolean(v.value)+
 ",\"unavailable_reason\":"+Reason(v.unavailable_reason)+'}';}
std::string Slots(const SiteSlots&s){
 std::string rows="[";for(const auto&row:s.slots){if(rows.size()>1)rows+=',';
  rows+="{\"slot_index\":"+std::to_string(row.slot_index)+",\"artifact_id\":"+Number(row.artifact_id)+'}';}
 rows+=']';return "{\"available\":"+Bool(s.available)+",\"slots\":"+(s.available?rows:"null")+
  ",\"unavailable_reason\":"+Reason(s.unavailable_reason)+'}';
}
std::string Cache(const CandidateCache&c){return "{\"available\":"+Bool(c.available)+",\"artifact_ids\":"+(c.available?Ids(c.artifact_ids):"null")+
 ",\"refresh_time_known\":false,\"producer_invoked\":false,\"unavailable_reason\":"+Reason(c.unavailable_reason)+'}';}
std::string Window(const WindowContext&w){return "{\"available\":"+Bool(w.available)+",\"root_present\":"+Boolean(w.root_present)+
 ",\"selected_holy_site_id\":"+Number(w.selected_holy_site_id)+",\"selected_artifact_id\":"+Number(w.selected_artifact_id)+
 ",\"slot_mode\":"+Quote(w.slot_mode)+",\"selected_slot_index\":"+Number(w.selected_slot_index)+
 ",\"selected_slot_artifact_id\":"+Number(w.selected_slot_artifact_id)+",\"cached_candidates\":"+Cache(w.cached_candidates)+
 ",\"unavailable_reason\":"+Reason(w.unavailable_reason)+'}';}
std::string Player(const PlayerInventory&p){return "{\"available\":"+Bool(p.available)+",\"artifact_ids\":"+(p.available?Ids(p.artifact_ids):"null")+
 ",\"native_character_owner_id\":"+Number(p.native_character_owner_id)+",\"native_holy_site_owner_id\":"+Number(p.native_holy_site_owner_id)+
 ",\"owner_matches_player\":"+Boolean(p.owner_matches_player)+",\"unavailable_reason\":"+Reason(p.unavailable_reason)+'}';}
std::string Candidates(const CurrentCandidates&c,bool inputs_available){
 std::string rows="[";for(const auto&r:c.evaluations){if(rows.size()>1)rows+=',';
  rows+="{\"artifact_id\":"+std::to_string(r.artifact_id)+",\"object_resolved\":"+Bool(r.object_resolved)+
   ",\"available\":"+Bool(r.available)+",\"predicate_called\":"+Bool(r.predicate_called)+
   ",\"can_be_candidate\":"+Boolean(r.can_be_candidate)+",\"unavailable_reason\":"+Reason(r.unavailable_reason)+'}';}
 rows+=']';return "{\"available\":"+Bool(c.available)+",\"artifact_ids\":"+(c.available?Ids(c.artifact_ids):"null")+
  ",\"evaluations\":"+(inputs_available?rows:"null")+
  ",\"method\":\"original_native_candidate_predicate_over_current_player_inventory\",\"producer_invoked\":false,\"unavailable_reason\":"+Reason(c.unavailable_reason)+'}';
}
std::string Permissions(const ArtifactPermissions&a){return "{\"available\":"+Bool(a.available)+",\"object_resolved\":"+Bool(a.object_resolved)+
 ",\"artifact_id\":"+Number(a.artifact_id)+",\"native_holy_site_owner_id\":"+Number(a.native_holy_site_owner_id)+
 ",\"rarity_level\":"+Number(a.rarity_level)+",\"player_inventory_contains_reference\":"+Boolean(a.player_inventory_contains_reference)+
 ",\"can_enshrine\":"+Observed(a.can_enshrine)+",\"can_remove\":"+Observed(a.can_remove)+
 ",\"slot_context\":\"current_holy_site_window\",\"unavailable_reason\":"+Reason(a.unavailable_reason)+'}';}
std::string Buttons(const CurrentButtons&b){return "{\"available\":"+Bool(b.available)+",\"selected_artifact_id\":"+Number(b.selected_artifact_id)+
 ",\"context_matches_requested_artifact\":"+Boolean(b.context_matches_requested_artifact)+
 ",\"can_enshrine\":"+Observed(b.can_enshrine)+",\"can_remove\":"+Observed(b.can_remove)+
 ",\"unavailable_reason\":"+Reason(b.unavailable_reason)+'}';}
}
std::string SerializeHolySiteRelicPermissions12004(const Snapshot&s){
 return "{\"schema\":\"ck3_12004_player_holy_site_relic_permissions_v1\",\"game_version\":\"1.20.0.4\",\"executable_sha256\":"+
  Quote(ck3_12004::kExecutableSha256)+",\"available\":"+Bool(s.available)+",\"unavailable_reason\":"+Reason(s.unavailable_reason)+
  ",\"capture_epoch\":"+std::to_string(s.capture_epoch)+",\"date_raw\":"+std::to_string(s.date_raw)+
  ",\"played_character_id\":"+std::to_string(s.played_character_id)+",\"player_faith_id\":"+Number(s.player_faith_id)+
  ",\"requested_holy_site_id\":"+std::to_string(s.requested_holy_site_id)+",\"holy_site_id\":"+Number(s.holy_site_id)+
  ",\"requested_artifact_id\":"+Number(s.requested_artifact_id)+",\"loaded_source_pins_verified\":"+Bool(s.loaded_source_pins_verified)+
  ",\"site_inventory_slots\":"+Slots(s.site_inventory_slots)+",\"window_context\":"+Window(s.window_context)+
  ",\"player_inventory\":"+Player(s.player_inventory)+",\"current_candidates\":"+Candidates(s.current_candidates,s.player_inventory.available)+
  ",\"artifact_permissions\":"+Permissions(s.artifact_permissions)+",\"current_buttons\":"+Buttons(s.current_buttons)+
  ",\"evaluation_context\":{\"native_getter_calls\":"+std::to_string(s.native_getter_calls)+",\"getter_backend\":"+Quote(s.getter_backend)+
  ",\"owner_thread_requirement\":\"existing_religion_owner_callback\",\"gameplay_command_submitted\":false,\"world_cache_written\":false,"
  "\"window_selection_written\":false,\"window_candidate_cache_written\":false,\"script_evaluation_allocates_and_uses_tls\":true,"
  "\"inventory_getter_may_initialize_static_context\":true,\"script_rng_effects_verified\":false,\"script_rng_effects\":\"unknown\"},"
  "\"action_ready\":false,\"beneficiaries_observed\":false,\"beneficiaries\":null,\"read_only\":true}";
}
std::string SerializeHolySiteRelicPermissionsCommand12004(const Snapshot&s,std::string_view request_id,
 std::uint64_t revision,std::int64_t date_raw){
 return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":"+Quote(request_id)+
  ",\"ok\":true,\"result\":{\"step\":"+Quote(kQueryStep)+",\"accepted\":true,\"status\":"+Quote(s.available?"observed":"unavailable")+
  ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":\"1.20.0.4\",\"executable_sha256\":"+
  Quote(ck3_12004::kExecutableSha256)+",\"domain_key\":"+Quote(kDomainKey)+
  ",\"backend_id\":\"ck3-1.20.0.4-native-player-holy-site-relic-permissions-v1\",\"snapshot_revision\":"+std::to_string(revision)+
  ",\"date_raw\":"+std::to_string(date_raw)+",\"player_holy_site_relic_permissions\":"+SerializeHolySiteRelicPermissions12004(s)+"}}";
}
}
