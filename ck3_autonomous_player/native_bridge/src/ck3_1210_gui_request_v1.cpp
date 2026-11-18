#include "xar_bridge/ck3_1210_gui_control_v1.hpp"
#include "xar_bridge/ck3_1210_core_frame_v1.hpp"
#include <charconv>

namespace xar::ck3_1210 {
namespace {
struct Cursor {
  std::string_view text;std::size_t at=0;
  void space() {while(at<text.size() && (text[at]==' ' || text[at]=='\t' || text[at]=='\r' || text[at]=='\n'))++at;}
  bool take(char c) {space();if(at==text.size() || text[at]!=c)return false;++at;return true;}
  bool string(std::string_view &out) {
    if(!take('"'))return false;const auto begin=at;
    while(at<text.size() && text[at]!='"') {
      const auto ch=static_cast<unsigned char>(text[at]);
      if(ch<0x20 || ch>=0x7f || ch=='\\' || at-begin>=192)return false;++at;
    }
    if(at==text.size())return false;out=text.substr(begin,at++-begin);return true;
  }
  bool number(std::uint64_t &out) {
    space();const auto begin=at;
    while(at<text.size() && text[at]>='0' && text[at]<='9')++at;
    if(at==begin || (at-begin>1 && text[begin]=='0'))return false;
    const auto p=std::from_chars(text.data()+begin,text.data()+at,out);
    return p.ec==std::errc{} && p.ptr==text.data()+at;
  }
};
bool Decimal(std::string_view s,std::uint64_t &out) {
  if(s.empty() || (s.size()>1 && s.front()=='0'))return false;
  for(const char ch:s)if(ch<'0' || ch>'9')return false;
  const auto p=std::from_chars(s.data(),s.data()+s.size(),out);
  return p.ec==std::errc{} && p.ptr==s.data()+s.size();
}
bool Identity(Cursor &c,std::string_view expected) {std::string_view s;return c.string(s) && s==expected;}
bool Hash(Cursor &c) {
  std::string_view s;if(!c.string(s) || s.size()!=64)return false;
  for(std::size_t i=0;i<64;++i) {char ch=s[i];if(ch>='a' && ch<='f')ch=static_cast<char>(ch-'a'+'A');if(ch!=kExecutableSha256[i])return false;}
  return true;
}
bool Claim(Cursor &c,GuiControlRequestV1 &r) {
  if(!c.take('{'))return false;std::uint32_t seen=0;bool first=true;std::uint64_t snapshot=0;
  while(!c.take('}')) {
    if(!first && !c.take(','))return false;first=false;
    std::string_view k,v;if(!c.string(k) || !c.take(':'))return false;
    std::uint32_t bit=0;bool valid=false;
    if(k=="schema") {bit=1U;valid=Identity(c,kGuiControlClaimSchemaV1);}
    else if(k=="game_version") {bit=2U;valid=Identity(c,kGameVersion);}
    else if(k=="executable_sha256") {bit=4U;valid=Hash(c);}
    else if(k=="adapter_id") {bit=8U;valid=Identity(c,kAdapterId);}
    else if(k=="backend") {bit=16U;valid=Identity(c,kCoreBackendV1);}
    else if(k=="snapshot_id") {bit=32U;valid=c.string(v) && v.starts_with("native:") && Decimal(v.substr(7),snapshot) && snapshot>0;}
    else if(k=="native_revision") {bit=64U;valid=c.number(r.native_revision) && r.native_revision>0;}
    else if(k=="deadline_unix_ms") {bit=128U;valid=c.number(r.deadline_unix_ms) && r.deadline_unix_ms>0;}
    else if(k=="root_name") {bit=256U;valid=c.string(v) && GuiControlRootNameV1(v);if(valid)r.root_name.assign(v);}
    else if(k=="query_generation") {bit=512U;valid=c.string(v) && Decimal(v,r.query_generation);}
    else if(k=="widget_id") {bit=1024U;valid=c.string(v) && Decimal(v,r.widget_id);}
    if(!bit || !valid || (seen&bit))return false;seen|=bit;
  }
  return seen==2047U && snapshot==r.native_revision;
}
bool Id(std::string_view s) {
  if(s.empty() || s.size()>96)return false;
  for(const char ch:s)if(!((ch>='a' && ch<='z') || (ch>='A' && ch<='Z') || (ch>='0' && ch<='9') || ch=='_' || ch=='-' || ch=='.'))return false;
  return true;
}
const char *Status(GuiControlStatusV1 s) {
  switch(s) {
    case GuiControlStatusV1::available:return "available";
    case GuiControlStatusV1::submitted:return "submitted";
    case GuiControlStatusV1::expired:return "expired";
    case GuiControlStatusV1::stale_full_snapshot:return "stale_full_snapshot";
    case GuiControlStatusV1::stale_gui:return "stale_gui";
    case GuiControlStatusV1::disabled:return "disabled";
    case GuiControlStatusV1::indeterminate:return "indeterminate";
    default:return "unavailable";
  }
}
void String(std::string &out,std::string_view value) {
  constexpr char hex[]="0123456789abcdef";out+='"';
  for(const unsigned char ch:value) {
    if(ch=='"' || ch=='\\') {out+='\\';out+=static_cast<char>(ch);}
    else if(ch<0x20) {out+="\\u00";out+=hex[ch>>4];out+=hex[ch&15];}
    else out+=static_cast<char>(ch);
  }out+='"';
}
void Boolean(std::string &s,std::string_view key,bool value) {s+=",\"";s+=key;s+="\":";s+=value?"true":"false";}
} // namespace
bool ParseGuiControlRequestV1(std::string_view payload,GuiControlRequestV1 &out) noexcept {
  out={};try {
    if(payload.size()>16384)return false;Cursor c{payload};GuiControlRequestV1 r{};
    if(!c.take('{'))return false;std::uint32_t seen=0;std::uint64_t expected=0;bool first=true;
    while(!c.take('}')) {
      if(!first && !c.take(','))return false;first=false;
      std::string_view k,v;if(!c.string(k) || !c.take(':'))return false;
      std::uint32_t bit=0;bool valid=false;std::uint64_t n=0;
      if(k=="type") {bit=1U;valid=Identity(c,"execute_step");}
      else if(k=="protocol_version") {bit=2U;valid=c.number(n) && n==1;}
      else if(k=="request_id") {bit=4U;valid=c.string(v) && Id(v);}
      else if(k=="step") {bit=8U;valid=c.string(r.step);}
      else if(k=="expected_revision") {bit=16U;valid=c.number(expected) && expected>0;}
      else if(k=="gui_control_v1") {bit=32U;valid=Claim(c,r);}
      else if(k=="arguments") {bit=64U;valid=c.take('{') && c.take('}');}
      if(!bit || !valid || (seen&bit))return false;seen|=bit;
    }
    c.space();if(c.at!=payload.size() || (seen&63U)!=63U || expected!=r.native_revision)return false;
    if(r.step==kGuiControlQueryStepV1) {r.step=kGuiControlQueryStepV1;if(r.query_generation || r.widget_id)return false;}
    else if(r.step==kGuiControlActivateStepV1) {r.step=kGuiControlActivateStepV1;r.activate=true;if(!r.query_generation || !r.widget_id)return false;}
    else return false;
    out=std::move(r);return true;
  }catch(...) {out={};return false;}
}
std::string SerializeGuiControlCommandResultV1(std::string_view id,const GuiControlRequestV1 &r,const GuiControlResultV1 &v) {
  const bool accepted=v.status==GuiControlStatusV1::available || v.status==GuiControlStatusV1::submitted;
  std::string s="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";String(s,id);
  s+=",\"ok\":true,\"result\":{\"schema\":";String(s,kGuiControlResultSchemaV1);
  s+=",\"step\":";String(s,r.step);s+=",\"game_version\":";String(s,kGameVersion);
  s+=",\"executable_sha256\":";String(s,kExecutableSha256);s+=",\"adapter_id\":";String(s,kAdapterId);
  s+=",\"backend\":";String(s,kCoreBackendV1);s+=",\"status\":";String(s,Status(v.status));
  Boolean(s,"accepted",accepted);s+=",\"native_revision\":"+std::to_string(r.native_revision);
  s+=",\"root_name\":";String(s,r.root_name);s+=",\"query_generation\":";String(s,std::to_string(v.query_generation));
  s+=",\"widget_id\":";String(s,std::to_string(r.widget_id));
  Boolean(s,"application_main_observed",v.application_main_observed);
  Boolean(s,"full_snapshot_before_verified",v.full_snapshot_before_verified);
  Boolean(s,"source_abi_pins_verified",v.source_abi_pins_verified);
  Boolean(s,"effect_attempted",v.effect_attempted);Boolean(s,"native_handled",v.native_handled);
  Boolean(s,"verification_pending",v.verification_pending);Boolean(s,"complete",v.status==GuiControlStatusV1::available);
  s+=",\"widgets\":[";
  if(v.status==GuiControlStatusV1::available)for(std::size_t i=0;i<v.widgets.size();++i) {
    if(i)s+=',';const auto &w=v.widgets[i];s+="{\"widget_id\":";String(s,std::to_string(w.widget_id));
    s+=",\"runtime_name\":";String(s,w.runtime_name);s+=",\"child_path\":";String(s,w.child_path);
    s+=",\"vtable_rva\":"+std::to_string(w.vtable_rva);Boolean(s,"effective_visible",w.effective_visible);
    Boolean(s,"enabled",w.enabled);Boolean(s,"clickable",w.clickable);s+='}';
  }
  s+="],\"unavailable_reason\":";if(v.unavailable_reason.empty())s+="null";else String(s,v.unavailable_reason);
  s+="}}";return s;
}
} // namespace xar::ck3_1210
