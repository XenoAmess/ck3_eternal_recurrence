// Included once after the old Serialize body, whose contract stays unchanged.
namespace xar::ck3_12004::character_skill_effects {
std::string SerializeKnight(const Query &q){
  const auto &v=q.knight_observation;
  if(!q.knight_query||!q.completed||q.frame_changed||!q.failure.empty()||q.invocations!=1||
      !q.expected_revision||q.executable_sha256!=core::kExeSha||q.character_id==0xFFFFFFFFU||
      v.character_id!=q.character_id||v.frame.revision!=q.expected_revision||
      v.frame.date_raw!=q.expected_snapshot.date_raw||
      v.frame.played_character_id!=static_cast<std::uint32_t>(q.expected_snapshot.played_character_id)||
      !v.frame.owner_thread||!v.frame.paused||!v.frame.map_ready||q.expected_snapshot.played_character_id<=0||
      !v.read_only||v.gameplay_command_submitted||v.modifier_cache_refreshed||
      v.cache_generation_time_known||v.site_attribution_observed||v.selected_site_contribution_raw)return {};
  if(v.available){
    if(!v.two_pass_stable||!v.own_actor_context_verified||!v.unavailable_reason.empty()||
        v.callback_provenance!=core::CallbackProvenance::exact4_native||
        !v.rite_id||*v.rite_id==0xFFFFFFFFU||!v.faith_id||*v.faith_id==0xFFFFFFFFU||
        !v.knight_effectiveness_raw||!v.actual_knight_effectiveness_breakdown||
        v.actual_knight_effectiveness_breakdown->size()>core::kMaxBreakdownBytes)return {};
  }else if(v.two_pass_stable||v.own_actor_context_verified||v.unavailable_reason.empty()||
      v.callback_provenance!=core::CallbackProvenance::unavailable||v.rite_id||v.faith_id||
      v.knight_effectiveness_raw||v.actual_knight_effectiveness_breakdown)return {};
  std::string out="{\"schema\":\"ck3_12004_character_knight_effectiveness_v1\",\"available\":";
  out+=v.available?"true":"false";out+=",\"unavailable_reason\":";
  if(v.available)out+="null";else Quote(out,v.unavailable_reason);
  out+=",\"read_only\":true,\"snapshot_revision\":"+std::to_string(q.expected_revision);
  out+=",\"date_raw\":"+std::to_string(q.expected_snapshot.date_raw)+",\"played_character_id\":"+std::to_string(q.expected_snapshot.played_character_id);
  out+=",\"character_id\":"+std::to_string(q.character_id)+",\"rite_id\":";Number(out,v.rite_id);
  out+=",\"faith_id\":";Number(out,v.faith_id);out+=",\"knight_effectiveness_raw\":";Number(out,v.knight_effectiveness_raw);
  out+=",\"actual_knight_effectiveness_breakdown\":";
  if(v.actual_knight_effectiveness_breakdown)Quote(out,*v.actual_knight_effectiveness_breakdown);else out+="null";
  out+=",\"raw_scale\":100000,\"two_pass_stable\":";out+=v.two_pass_stable?"true":"false";
  out+=",\"own_actor_context_verified\":";out+=v.own_actor_context_verified?"true":"false";
  out+=",\"callback_provenance\":";Quote(out,v.available?"exact4_native":"unavailable");
  out+=",\"modifier_cache_refreshed\":false,\"cache_generation_time_known\":false,\"site_attribution_observed\":false,\"selected_site_contribution_raw\":null,";
  out+="\"gameplay_command_submitted\":false,\"raw_pointer_fields_persisted\":false,\"script_cache_rng_effects\":\"unknown\",\"game_version\":\"1.20.0.4\",\"executable_sha256\":";
  Quote(out,core::kExeSha);out+='}';return out;
}
} // namespace xar::ck3_12004::character_skill_effects
