#include "xar_bridge/ck3_12004_holy_site_relic_action_context.hpp"
namespace xar::ck3_12004::religion::relic_action_context {
namespace {
std::string Q(std::string_view s){static constexpr char hex[]="0123456789abcdef";std::string v="\"";for(const unsigned char c:s){if(c=='"'||c=='\\'){v+='\\';v+=static_cast<char>(c);}else if(c<32){v+="\\u00";v+=hex[c>>4];v+=hex[c&15];}else v+=static_cast<char>(c);}return v+'"';}
std::string B(bool b){return b?"true":"false";}
template<class T>std::string N(const std::optional<T>&v){return v?std::to_string(*v):"null";}
std::string O(const std::optional<bool>&v){return v?B(*v):"null";}
std::string Reason(std::string_view s){return s.empty()?"null":Q(s);}
std::string Observed(const relic_permissions::ObservedBool&v){return "{\"available\":"+B(v.available)+",\"value\":"+O(v.value)+",\"unavailable_reason\":"+Reason(v.unavailable_reason)+'}';}
std::string TextJson(const Text&v){return "{\"available\":"+B(v.available)+",\"text\":"+(v.available?Q(v.text):"null")+",\"unavailable_reason\":"+Reason(v.unavailable_reason)+'}';}
std::string Owner(const Ownership&v){return "{\"available\":"+B(v.available)+",\"object_resolved\":"+B(v.object_resolved)+
 ",\"artifact_id\":"+(v.artifact_id==0xFFFFFFFFU?"null":std::to_string(v.artifact_id))+
 ",\"character_owner_id\":"+N(v.character_owner_id)+",\"holy_site_owner_id\":"+N(v.holy_site_owner_id)+",\"rarity_level\":"+N(v.rarity_level)+
 ",\"character_owner_matches_player\":"+O(v.character_owner_matches_player)+",\"holy_site_owner_matches_requested\":"+O(v.holy_site_owner_matches_requested)+
 ",\"player_owned_reference_member\":"+O(v.player_owned_reference_member)+",\"player_equipped_slot_member\":"+Observed(v.player_equipped_slot_member)+
 ",\"site_equipped_slot_member\":"+Observed(v.site_equipped_slot_member)+",\"unavailable_reason\":"+Reason(v.unavailable_reason)+'}';}
std::string DestinationJson(const Destination&v){return "{\"available\":"+B(v.available)+",\"action_kind\":"+Q(v.action_kind)+
 ",\"selected_slot_index\":"+N(v.selected_slot_index)+",\"explicit_slot_type_compatible\":"+O(v.explicit_slot_type_compatible)+
 ",\"original_picker_called\":"+B(v.original_picker_called)+",\"effective_slot_index\":"+N(v.effective_slot_index)+
 ",\"replacing_artifact_id\":"+N(v.replacing_artifact_id)+",\"replacing_artifact\":"+Owner(v.replacing_artifact)+
 ",\"method\":\"source_bound_explicit_slot_branch_then_original_native_picker\",\"effective_slot_script_permission_independently_observed\":false,\"unavailable_reason\":"+Reason(v.unavailable_reason)+'}';}
}
std::string RelicActionPreviewCanonical12004(const Snapshot&s){
 // A read-only query does not freeze its transient capture epoch. Each action
 // separately admits the actual owner frame and re-evaluates this state twice.
 return "ck3-relic-action-preview-v1|"+std::to_string(s.date_raw)+'|'+std::to_string(s.played_character_id)+'|'+
  N(s.permissions.player_faith_id)+'|'+std::to_string(s.requested_holy_site_id)+'|'+std::to_string(s.requested_artifact_id)+'|'+
  Owner(s.artifact_ownership)+'|'+DestinationJson(s.destination)+'|'+TextJson(s.selected_action_effect_description)+'|'+
  TextJson(s.enshrine_disabled_tooltip)+'|'+TextJson(s.remove_disabled_tooltip)+'|'+
  Observed(s.permissions.artifact_permissions.can_enshrine)+'|'+Observed(s.permissions.artifact_permissions.can_remove)+'|'+
  Observed(s.permissions.current_buttons.can_enshrine)+'|'+Observed(s.permissions.current_buttons.can_remove);
}
std::string SerializeHolySiteRelicActionContext12004(const Snapshot&s){
 return "{\"schema\":\"ck3_12004_player_holy_site_relic_action_context_v1\",\"game_version\":\"1.20.0.4\",\"executable_sha256\":"+Q(ck3_12004::kExecutableSha256)+
 ",\"available\":"+B(s.available)+",\"unavailable_reason\":"+Reason(s.unavailable_reason)+",\"capture_epoch\":"+std::to_string(s.capture_epoch)+
 ",\"date_raw\":"+std::to_string(s.date_raw)+",\"played_character_id\":"+std::to_string(s.played_character_id)+
 ",\"requested_holy_site_id\":"+std::to_string(s.requested_holy_site_id)+",\"requested_artifact_id\":"+std::to_string(s.requested_artifact_id)+
 ",\"loaded_source_pins_verified\":"+B(s.loaded_source_pins_verified)+",\"permissions\":"+relic_permissions::SerializeHolySiteRelicPermissions12004(s.permissions)+
 ",\"artifact_ownership\":"+Owner(s.artifact_ownership)+",\"destination\":"+DestinationJson(s.destination)+
 ",\"selected_artifact_matches_request\":"+B(s.selected_artifact_matches_request)+
 ",\"selected_action_effect_description\":"+TextJson(s.selected_action_effect_description)+",\"enshrine_disabled_tooltip\":"+TextJson(s.enshrine_disabled_tooltip)+
 ",\"remove_disabled_tooltip\":"+TextJson(s.remove_disabled_tooltip)+",\"preview_identity_available\":"+B(s.preview_identity_available)+
 ",\"preview_identity_sha256\":"+(s.preview_identity_available?Q(s.preview_identity_sha256):"null")+
 ",\"evaluation_context\":{\"getter_backend\":"+Q(s.getter_backend)+",\"native_getter_calls\":"+std::to_string(s.native_getter_calls)+
 ",\"owner_thread_requirement\":\"existing_religion_owner_callback\",\"gameplay_command_submitted\":false,\"window_selection_written\":false,\"world_cache_written\":false,"
 "\"original_effect_description_evaluates_script_context\":true,\"script_rng_effects_verified\":false,\"script_rng_effects\":\"unknown\"},"
  "\"action_ready\":false,\"business_outcome_observed\":false,\"beneficiaries_observed\":false,\"beneficiaries\":null"+
  (s.recognition_matrix?",\"recognition_matrix\":"+holy_site_relic::SerializeHolySiteRelicRecognitionMatrix12004(*s.recognition_matrix):"")+",\"read_only\":true}";
}
std::string SerializeHolySiteRelicActionContextCommand12004(const Snapshot&s,std::string_view id,std::uint64_t revision,std::int64_t date){
 return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":"+Q(id)+",\"ok\":true,\"result\":{\"step\":"+Q(kQueryStep)+
 ",\"accepted\":true,\"status\":"+Q(s.available?"observed":"unavailable")+",\"private_build\":true,\"read_only\":true,\"advertised\":false,"
 "\"game_version\":\"1.20.0.4\",\"executable_sha256\":"+Q(ck3_12004::kExecutableSha256)+",\"domain_key\":"+Q(kDomainKey)+
 ",\"backend_id\":\"ck3-1.20.0.4-native-player-holy-site-relic-action-context-v1\",\"snapshot_revision\":"+std::to_string(revision)+
 ",\"date_raw\":"+std::to_string(date)+",\"player_holy_site_relic_action_context\":"+SerializeHolySiteRelicActionContext12004(s)+"}}";
}
}
