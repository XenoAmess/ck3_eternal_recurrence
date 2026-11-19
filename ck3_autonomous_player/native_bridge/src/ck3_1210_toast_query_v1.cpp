#include "xar_bridge/ck3_1210_toast_query_v1.hpp"
#include "xar_bridge/ck3_1210_core_frame_v1.hpp"
namespace xar::ck3_1210 {
namespace {
void Text(std::string &s,std::string_view value) {
  constexpr char hex[]="0123456789abcdef";s+='"';
  for(const unsigned char ch:value) {
    if(ch=='"' || ch=='\\') {s+='\\';s+=static_cast<char>(ch);}
    else if(ch<0x20) {s+="\\u00";s+=hex[ch>>4];s+=hex[ch&15];}
    else s+=static_cast<char>(ch);
  }s+='"';
}
void Field(std::string &s,std::string_view key,std::string_view value) {s+=",\"";s+=key;s+="\":";Text(s,value);}
void Flag(std::string &s,std::string_view key,bool value) {s+=",\"";s+=key;s+="\":";s+=value?"true":"false";}
const char *Kind(ToastScopeKindV1 kind) {
  switch(kind) {case ToastScopeKindV1::character:return "character";case ToastScopeKindV1::story:return "story";
    default:return "unsupported";}
}
void Scopes(std::string &s,std::string_view key,const std::vector<ToastObjectScopeIdentityV1> &scopes) {
  s+=",\"";s+=key;s+="\":[";
  for(std::size_t i=0;i<scopes.size();++i) {
    if(i)s+=',';const auto &scope=scopes[i];s+="{\"name\":";Text(s,scope.name);
    Field(s,"kind",Kind(scope.kind));s+=",\"observed_tag\":"+std::to_string(scope.observed_tag);
    Flag(s,"identity_available",scope.identity_available);s+=",\"identity\":";
    if(scope.identity)Text(s,*scope.identity);else s+="null";
    s+=",\"unavailable_reason\":";if(scope.unavailable_reason.empty())s+="null";else Text(s,scope.unavailable_reason);s+='}';
  }s+=']';
}
const char *Stage(ToastObjectStageV1 stage) {
  switch(stage) {
    case ToastObjectStageV1::empty:return "empty";
    case ToastObjectStageV1::hidden:return "hidden";
    case ToastObjectStageV1::visible_pending_frame:return "visible_pending_frame";
    case ToastObjectStageV1::visible:return "visible";
    default:return "unavailable";
  }
}
} // namespace
std::string SerializeToastQueryResultV1(std::string_view id,const GuiControlRequestV1 &r,const ToastQueryResultV1 &v) {
  std::string s="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";Text(s,id);
  s+=",\"ok\":true,\"result\":{\"schema\":";Text(s,kToastQueryResultSchemaV1);
  Field(s,"step",kToastQueryStepV1);Field(s,"game_version",kGameVersion);Field(s,"executable_sha256",kExecutableSha256);
  Field(s,"adapter_id",kAdapterId);Field(s,"backend",kCoreBackendV1);Field(s,"status",v.available?"available":"unavailable");
  Flag(s,"accepted",v.available);Field(s,"snapshot_id","native:"+std::to_string(r.native_revision));
  Field(s,"native_revision",std::to_string(r.native_revision));Field(s,"connection_generation",std::to_string(v.connection_generation));
  Field(s,"query_sequence",std::to_string(v.query_sequence));s+=",\"owner_thread_id\":"+std::to_string(v.owner_thread_id);
  Flag(s,"application_main_observed",v.application_main_observed);Flag(s,"full_snapshot_before_verified",v.full_snapshot_before_verified);
  Flag(s,"full_snapshot_after_verified",v.full_snapshot_after_verified);Flag(s,"source_abi_pins_verified",v.source_abi_pins_verified);
  Flag(s,"read_only",true);Flag(s,"effect_attempted",false);
  const auto &o=v.observation;Field(s,"stage",Stage(o.stage));
  Field(s,"completed_application_frame",std::to_string(o.completed_application_frame));
  s+=",\"queue_count\":"+std::to_string(o.queue_count);Field(s,"title",o.title);Field(s,"description",o.description);
  Scopes(s,"saved_gui_scopes",o.saved_gui_scopes);Scopes(s,"saved_script_scopes",o.saved_script_scopes);
  Flag(s,"recipient_identity_available",false);Flag(s,"news_origin_available",false);Flag(s,"delivery_confirmed",false);
  s+=",\"unavailable_reason\":";if(v.unavailable_reason.empty())s+="null";else Text(s,v.unavailable_reason);
  s+="}}";return s;
}
} // namespace xar::ck3_1210
