#include "xar_bridge/ck3_12004_holy_site_relic_context.hpp"

namespace xar::ck3_12004::religion::holy_site_relic {
namespace {
std::string Quote(std::string_view s) {
  constexpr char hex[]="0123456789abcdef";
  std::string out="\"";
  for (const unsigned char c:s) {
    if (c=='"'||c=='\\') {out+='\\';out+=static_cast<char>(c);}
    else if (c<0x20) {out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}
    else out+=static_cast<char>(c);
  }
  return out+'"';
}
std::string Bool(bool v) {return v?"true":"false";}
std::string Value(std::optional<bool> v) {return v?Bool(*v):"null";}
template<class T> std::string Number(std::optional<T> v) {return v?std::to_string(*v):"null";}
std::string Ref(std::uint32_t v) {return v==0xFFFFFFFFU?"null":std::to_string(v);}
std::string Ref(std::optional<std::uint32_t> v) {return v?Ref(*v):"null";}
std::string Reason(std::string_view s) {return s.empty()?"null":Quote(s);}
std::string Ids(const std::vector<std::uint32_t> &ids) {
  std::string out="[";
    for (const auto id:ids) {if(out.size()>1)out+=',';out+=std::to_string(id);}
  return out+']';
}
std::string RecognitionJson(const Recognition &r) {
  return "{\"available\":"+Bool(r.available)+",\"faith_id\":"+Ref(r.faith_id)+
      ",\"value\":"+Value(r.value)+",\"unavailable_reason\":"+Reason(r.unavailable_reason)+'}';
}
std::string ArtifactJson(const Artifact &a) {
  return "{\"artifact_id\":"+Ref(a.artifact_id)+",\"available\":"+Bool(a.available)+
      ",\"rarity_level\":"+Number(a.rarity_level)+",\"native_holy_site_owner_id\":"+Ref(a.native_holy_site_owner_id)+
      ",\"sanctified_faith_ids_available\":"+Bool(a.sanctified_faith_ids_available)+
      ",\"sanctified_faith_ids\":"+(a.sanctified_faith_ids_available?Ids(a.sanctified_faith_ids):"null")+
      ",\"template_trigger_evaluated_separately\":false,\"recognition_semantics\":\"native_dynamic_sanctification_or_template_trigger\""+
      ",\"recognition_for_player_faith\":"+RecognitionJson(a.recognition_for_player_faith)+
      ",\"recognition_for_county_holder_faith\":"+RecognitionJson(a.recognition_for_county_holder_faith)+
      ",\"unavailable_reason\":"+Reason(a.unavailable_reason)+'}';
}
} // namespace
std::string SerializeHolySiteRelicContext12004(const Snapshot &s) {
  const auto &c=s.cached_world_state;
  const auto &h=s.county_context;
  const auto &i=s.inventory;
  const auto &e=s.current_relic_evaluation;
  std::string slots="[",artifacts="[";
  for (const auto &slot:i.slots) {
    if(slots.size()>1)slots+=',';
    slots+="{\"slot_index\":"+std::to_string(slot.slot_index)+",\"artifact_id\":"+Ref(slot.artifact_id)+'}';
  }
  slots+=']';
  for (const auto &artifact:i.artifact_objects) {
    if(artifacts.size()>1)artifacts+=',';
    artifacts+=ArtifactJson(artifact);
  }
  artifacts+=']';
  return "{\"schema\":\"ck3_12004_player_holy_site_relic_context_v1\",\"game_version\":\"1.20.0.4\","
      "\"executable_sha256\":"+Quote(ck3_12004::kExecutableSha256)+
      ",\"available\":"+Bool(s.available)+",\"unavailable_reason\":"+Reason(s.unavailable_reason)+
      ",\"capture_epoch\":"+std::to_string(s.capture_epoch)+",\"date_raw\":"+std::to_string(s.date_raw)+
      ",\"played_character_id\":"+std::to_string(s.played_character_id)+
      ",\"player_rite_id\":"+Ref(s.player_rite_id)+",\"player_faith_id\":"+Ref(s.player_faith_id)+
      ",\"requested_holy_site_id\":"+Ref(s.requested_holy_site_id)+",\"holy_site_id\":"+Ref(s.holy_site_id)+
      ",\"associated_faith_ids_available\":"+Bool(s.associated_faith_ids_available)+
      ",\"associated_faith_ids\":"+(s.associated_faith_ids_available?Ids(s.associated_faith_ids):"null")+
      ",\"cached_world_state\":{\"available\":"+Bool(c.available)+",\"is_active\":"+Value(c.is_active)+
      ",\"total_active_artifact_rarity\":"+Number(c.total_active_artifact_rarity)+
      ",\"refresh_time_known\":false,\"world_effects_applied_observed\":false,\"unavailable_reason\":"+Reason(c.unavailable_reason)+'}'+
      ",\"county_context\":{\"available\":"+Bool(h.available)+",\"barony_title_id\":"+Ref(h.barony_title_id)+
      ",\"county_title_id\":"+Ref(h.county_title_id)+",\"county_holder_id\":"+Ref(h.county_holder_id)+
      ",\"county_holder_rite_id\":"+Ref(h.county_holder_rite_id)+",\"county_holder_faith_id\":"+Ref(h.county_holder_faith_id)+
      ",\"unavailable_reason\":"+Reason(h.unavailable_reason)+'}'+
      ",\"inventory\":{\"available\":"+Bool(i.available)+",\"artifact_ids\":"+(i.available?Ids(i.artifact_ids):"null")+
      ",\"slots\":"+(i.available?slots:"null")+",\"artifact_objects\":"+(i.available?artifacts:"null")+
      ",\"unavailable_reason\":"+Reason(i.unavailable_reason)+'}'+
      ",\"current_relic_evaluation\":{\"available\":"+Bool(e.available)+
      ",\"inventory_artifact_count_raw\":"+Number(e.inventory_artifact_count_raw)+
      ",\"county_holder_faith_associated\":"+Value(e.county_holder_faith_associated)+
      ",\"active_artifact_rarity_sum\":"+Number(e.active_artifact_rarity_sum)+",\"is_active\":"+Value(e.is_active)+
      ",\"cache_evaluation_disagreement\":"+Value(e.cache_evaluation_disagreement)+
      ",\"method\":\"original_native_rarity_producer\",\"unavailable_reason\":"+Reason(e.unavailable_reason)+'}'+
      ",\"evaluation_context\":{\"native_getter_calls\":"+std::to_string(s.native_getter_calls)+
      ",\"getter_backend\":"+Quote(s.getter_backend)+
      ",\"owner_thread_requirement\":\"existing_religion_owner_callback\",\"gameplay_command_submitted\":false,"
      "\"world_cache_written\":false,\"script_evaluation_allocates_and_uses_tls\":true,"
      "\"script_rng_effects_verified\":false,\"script_rng_effects\":\"unknown\"},"
      "\"beneficiaries_observed\":false,\"beneficiaries\":null,\"can_enshrine_observed\":false,\"can_enshrine\":null,"
      "\"window_candidates_observed\":false,\"read_only\":true}";
}
std::string SerializeHolySiteRelicContextCommand12004(const Snapshot &s,
    std::string_view request,std::uint64_t revision,std::int64_t date) {
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":"+Quote(request)+
      ",\"ok\":true,\"result\":{\"step\":\"query-player-holy-site-relic-context-v1\",\"accepted\":true,"
      "\"status\":"+Quote(s.available?"observed":"unavailable")+
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":\"1.20.0.4\","
      "\"executable_sha256\":"+Quote(ck3_12004::kExecutableSha256)+
      ",\"domain_key\":\"player_holy_site_relic_context_v1\","
      "\"backend_id\":\"ck3-1.20.0.4-native-player-holy-site-relic-context-v1\",\"snapshot_revision\":"+
      std::to_string(revision)+",\"date_raw\":"+std::to_string(date)+",\"player_holy_site_relic_context\":"+
      SerializeHolySiteRelicContext12004(s)+"}}";
}
} // namespace xar::ck3_12004::religion::holy_site_relic
