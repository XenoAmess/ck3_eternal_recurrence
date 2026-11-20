#include "xar_bridge/ck3_26757580_council_progress_frame70.hpp"
#include "xar_bridge/council_progress_provenance70.hpp"
namespace xar::ck3_1210::council70 {namespace {
void Quote(std::string&s,std::string_view v) {
 constexpr char hex[]="0123456789abcdef";s+=char(0x22);
 for(const unsigned char c:v){
  if(c==0x22 || c==0x5c){s+=char(0x5c);s+=char(c);}
  else if(c<32){s+=char(0x5c);s+="u00";s+=hex[c>>4];s+=hex[c&15];}
  else s+=char(c);
 }
 s+=char(0x22);
}
void Key(std::string&s,std::string_view k){Quote(s,k);s+=':';}
void String(std::string&s,std::string_view k,std::string_view v){Key(s,k);Quote(s,v);}
void Bool(std::string&s,std::string_view k,bool v){Key(s,k);s+=v?"true":"false";}
void OptionalNumber(std::string&s,std::string_view k,std::uint64_t n){Key(s,k);s+=n?std::to_string(n):"null";}
bool ValidProgress(const xar::council_progress70::TaskRow&r)noexcept {
 const auto&p=r.progress;const bool current=r.current_type_source_verified && (p.kind_raw==0 || p.kind_raw==1);
 if(p.current_source_verified!=current || p.frozen.has_value()!=(p.frozen_raw<=1) ||
    (p.frozen && *p.frozen!=(p.frozen_raw==1)))return false;
 if(current)return p.current_raw && p.maximum_raw && *p.current_raw==p.backing_raw &&
    *p.maximum_raw==(p.kind_raw==0?0:10000000) && p.current_reason.empty();
 const auto reason=!r.current_type_source_verified?std::string_view("council70_current_holder_unverified"):
   p.kind_raw==2?std::string_view("council70_value_evaluator_unobserved"):std::string_view("council70_progress_kind_unrecognized");
 return !p.current_raw && !p.maximum_raw && p.current_reason==reason;
}
void SignedOptional(std::string&s,std::string_view key,const std::optional<std::int64_t>&n) {
 Key(s,key);s+=n?std::to_string(*n):"null";
}
void Progress(std::string&s,const xar::council_progress70::TaskRow&r) {
 const auto&p=r.progress;Key(s,"progress_observation");s+='{';Key(s,"kind_raw");s+=std::to_string(p.kind_raw);
 s+=',';String(s,"kind",p.kind_raw==0?"infinite":p.kind_raw==1?"percentage":p.kind_raw==2?"value":"unknown");
 s+=',';Key(s,"backing_raw");s+=std::to_string(p.backing_raw);s+=',';Key(s,"scale");s+=std::to_string(xar::council_progress70::kProgressScale);
 s+=',';Bool(s,"current_source_verified",p.current_source_verified);
 s+=',';SignedOptional(s,"current_raw",p.current_raw);s+=',';SignedOptional(s,"maximum_raw",p.maximum_raw);
 s+=',';Key(s,"current_reason");if(p.current_reason.empty())s+="null";else Quote(s,p.current_reason);
 s+=',';Bool(s,"native_float_observed",false);s+=',';Key(s,"frozen_raw");s+=std::to_string(p.frozen_raw);
 s+=',';Bool(s,"frozen_known",p.frozen.has_value());s+=',';Key(s,"frozen_value");s+=p.frozen?(*p.frozen?"true":"false"):"null";
 s+=',';Key(s,"frozen_reason");if(p.frozen)s+="null";else Quote(s,"council70_noncanonical_frozen_byte");s+='}';
}
bool Valid(const MailboxContext&q)noexcept {
 const auto&f=q.expected_full;
 if(!q.completed || !q.data_ready || !q.observation.reason.empty() ||
 !q.bindings.exact_build_admitted || !IsHotfix(q.bindings.core.image_build) ||
 !q.expected_native_revision || q.current_full_attempts!=2 || !q.ticket_sequence ||
 !q.pump_epoch || !q.thread_id || q.application_main_observed==q.offline_fixture ||
 !f.paused || !f.map_ready || !f.has_played_character || !f.played_character_alive ||
 f.played_character_id==-1 || q.observation.rows.size()>xar::council_progress70::kRowLimit)return false;
 for(const auto&r:q.observation.rows){
  if(r.task_id==-1 || r.position_key.empty() || r.stored_task_type_key.empty() ||
   r.position_key.size()>xar::council_progress70::kKeyLimit ||
   r.stored_task_type_key.size()>xar::council_progress70::kKeyLimit ||
   (r.holder_id && *r.holder_id==-1) || (!r.holder_id && r.holder_alive) ||
   r.current_type_source_verified!=(r.holder_id.has_value() && r.holder_alive) || !ValidProgress(r))return false;
 }
 return true;
}
}
std::string SerializeData(const MailboxContext&q) {
 const bool known=Valid(q);std::string s="{";
 String(s,"schema",kSchema);s+=',';String(s,"step",kStep);s+=',';
 String(s,"status",known?"partial":"unavailable");s+=',';Key(s,"reason");
 if(known)s+="null";else Quote(s,q.observation.reason.empty()?std::string_view("council70_result_unqualified"):q.observation.reason);
 s+=',';Bool(s,"private_build",true);s+=',';Bool(s,"advertised",false);s+=',';Bool(s,"read_only",true);
 s+=',';Bool(s,"data_ready",known);s+=',';Bool(s,"same_frame_ready",known);
 s+=',';Bool(s,"all_seats_enumerated",false);s+=',';Bool(s,"full_council_read_available",false);
 s+=',';Bool(s,"candidate_collection_complete",false);s+=',';Bool(s,"progress_ready",false);s+=',';Bool(s,"action_ready",false);
 s+=',';Key(s,"build");s+='{';String(s,"adapter_id",hotfix26757580::kAdapterId);s+=',';
 String(s,"game_version",kGameVersion);s+=',';String(s,"steam_build_id",hotfix26757580::kSteamBuildId);s+=',';
 String(s,"executable_sha256",hotfix26757580::kExecutableSha256);s+='}';
 s+=',';Key(s,"frame");if(!known)s+="null";else{
  const auto&f=q.expected_full;s+='{';String(s,"native_snapshot_id","native:"+std::to_string(q.expected_native_revision));
  s+=',';Key(s,"native_revision");s+=std::to_string(q.expected_native_revision);
  s+=',';Key(s,"date_raw");s+=std::to_string(f.date_raw);
  s+=',';Key(s,"player_character_id");s+=std::to_string(f.played_character_id);
  s+=',';Bool(s,"paused",f.paused);s+=',';Bool(s,"map_ready",f.map_ready);s+='}';
 }
 s+=',';Key(s,"owned_task_rows");if(!known)s+="null";else{
  s+='[';bool first=true;
  for(const auto&r:q.observation.rows){
   if(!first)s+=',';first=false;s+='{';Key(s,"task_id");s+=std::to_string(r.task_id);
   s+=',';Key(s,"holder_character_id");s+=r.holder_id?std::to_string(*r.holder_id):"null";
   s+=',';Bool(s,"holder_alive",r.holder_alive);
   s+=',';String(s,"position_key",r.position_key);s+=',';String(s,"stored_task_type_key",r.stored_task_type_key);
   s+=',';Bool(s,"current_type_source_verified",r.current_type_source_verified);
   s+=',';Key(s,"current_task_type_key");if(r.current_type_source_verified)Quote(s,r.stored_task_type_key);else s+="null";
   for(auto key:{"target","progress","max_progress","frozen"}){s+=',';Key(s,key);s+="null";}
   s+=',';Progress(s,r);
   s+='}';
  }
  s+=']';
 }
 for(auto key:{"candidates","final_gates","assignment_quote"}){s+=',';Key(s,key);s+="null";}
 s+=',';Key(s,"origin");s+='{';String(s,"source_kind",q.offline_fixture?"offline_fixture":q.application_main_observed?"application_main_ticket":"unavailable");
 s+=',';OptionalNumber(s,"ticket_sequence",q.ticket_sequence);s+=',';OptionalNumber(s,"pump_epoch",q.pump_epoch);
 s+=',';OptionalNumber(s,"thread_id",q.thread_id);s+=',';Bool(s,"main_owner_observed",q.application_main_observed && !q.offline_fixture);s+='}';
 s+=',';Key(s,"provenance");s+='{';String(s,"reader_sha256",provenance70::kReaderSha);s+=',';
 String(s,"abi_sha256",provenance70::kAbiSha);s+=',';String(s,"frame_sha256",provenance70::kFrameSha);s+="}}";return s;
}
std::string SerializeCommand(std::string_view id,const MailboxContext&q) {
 std::string s="{";String(s,"type","command_result");s+=',';Key(s,"protocol_version");s+='1';s+=',';
 String(s,"request_id",id);s+=',';Bool(s,"ok",q.completed);s+=',';
 if(q.completed){Key(s,"result");s+=SerializeData(q);}
 else String(s,"error",q.observation.reason.empty()?std::string_view("council70_query_unavailable"):q.observation.reason);
 s+='}';return s;
}
} // namespace xar::ck3_1210::council70
