// Self-owned parser/serializer DATA tests. Link the real wire TU; no Game/ABI P.
#ifndef XAR_RITE_TEXT_TEST_HEADER
#define XAR_RITE_TEXT_TEST_HEADER "xar_bridge/ck3_121003_rite_text26785313_v1.hpp"
#endif
#include XAR_RITE_TEXT_TEST_HEADER
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <Windows.h>
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string_view>
#include <utility>
#include <vector>
namespace g=xar::ck3_121003::build26785313;
namespace {
using A=g::RiteTextAction267V1;using S=g::RiteTextStatus267V1;
using Q=g::RiteTextRequest267V1;using R=g::RiteTextResult267V1;
constexpr auto MAX=(std::numeric_limits<std::uint64_t>::max)();
unsigned checks=0;
void Check(bool value,const char*why){++checks;if(!value)throw std::runtime_error(why);}
bool Has(std::string_view text,std::string_view part){return text.find(part)!=std::string_view::npos;}
std::string Replace(std::string text,std::string_view from,std::string_view to){auto p=text.find(from);Check(p!=std::string::npos,"mutation did not change actual input");text.replace(p,from.size(),to);return text;}
std::string Repeat(std::string_view part,unsigned count){std::string out;for(unsigned i=0;i<count;++i)out+=part;return out;}
std::string Quote(std::string_view text){
  constexpr char hex[]="0123456789abcdef";std::string out="\"";
  for(unsigned char c:text){if(c=='"')out+="\\\"";else if(c=='\\')out+="\\\\";else if(c<0x20){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}else out+=static_cast<char>(c);}return out+'"';
}
const char* Action(A a){switch(a){case A::query:return "query";case A::set_name:return "set_name";case A::set_description:return "set_description";}throw std::runtime_error("unknown fixture action");}
auto Core(std::int32_t actor=36423){xar::ck3_1210::CoreSnapshotPrefix p{};p.clock.date_raw=53144328;p.clock.speed=2;p.clock.paused=true;p.local_player_id=0;p.map_ready=p.has_played_character=p.played_character_alive=true;p.played_character_id=actor;return p;}
std::string Request(A action,std::string_view text={},std::string_view id="rite-text-request-01",std::int32_t actor=36423,std::uint32_t rite=47){
  auto lease=action==A::query?"0":"18446744073709551615";
  return std::string("{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":")+Quote(id)+",\"step\":"+Quote(g::kRiteTextStep267V1)+
    ",\"expected_revision\":0,\"arguments\":{},\"rite_text\":{\"schema\":"+Quote(g::kRiteTextRequestSchema267V1)+
    ",\"game_version\":"+Quote(g::kGameVersion)+",\"executable_sha256\":"+Quote(g::kExecutableSha256)+",\"adapter_id\":"+Quote(g::kAdapterId)+
    ",\"backend\":"+Quote(g::kRiteTextBackend267V1)+",\"action\":"+Quote(Action(action))+
    ",\"expected_core\":{\"date_raw\":53144328,\"speed\":2,\"paused\":true,\"local_player_id\":0,\"map_ready\":true,\"has_played_character\":true,\"played_character_id\":"+std::to_string(actor)+
    ",\"played_character_alive\":true},\"expected_source_rite_id\":"+std::to_string(rite)+",\"provider_generation\":\""+lease+"\",\"query_sequence\":\""+lease+
    "\",\"text\":"+Quote(text)+"},\"core_control_deadline_unix_ms\":18446744073709551615}";
}
R Available(std::int32_t actor=36423,std::uint32_t rite=47){
  R r{};r.action=A::query;r.status=S::available;r.source_available=r.cleanup_known=r.facts_available=true;
  r.provider_generation=r.query_sequence=r.connection_generation=r.ticket_sequence=r.pump_epoch=MAX;r.thread_id=(std::numeric_limits<std::uint32_t>::max)();r.facts=Core(actor);
  r.source.emplace();auto&s=*r.source;s.actor_id=actor;s.source_rite_id=rite;s.is_creating=true;s.name="Original name";s.description="Original description";s.window_visible=s.window_enabled=s.write_admissible=true;return r;
}
R Dispatched(A a){auto r=Available();r.action=a;r.status=S::text_dispatched;r.claim_sequence=MAX;r.effect_attempted=r.native_returned=true;r.native_handled=false;return r;}
R Refused(S status){R r{};r.action=A::set_name;r.status=status;r.provider_generation=r.query_sequence=MAX;r.cleanup_known=status!=S::indeterminate;r.reason="nogame_typed_refusal";return r;}
std::string Wire(const R&r,std::string_view id="rite-text-result-01"){return g::SerializeRiteTextResult267V1(id,r);}
void NoBusiness(const std::string&w){for(auto t:{"\"addresses_redacted\":true","\"native_handled\":false","\"text_applied\":false","\"new_date_observed\":false","\"physical_save_confirmed\":false"})Check(Has(w,t),"serializer invented handled/applied/date/Save credit");}
void Good(const std::string&w){NoBusiness(w);Check(Has(w,"\"ok\":true")&&Has(w,"\"source_available\":true")&&!Has(w,"\"source\":null")&&Has(w,"\"unavailable_reason\":null"),"complete legal Source rejected");}
void Bad(const std::string&w){NoBusiness(w);Check(Has(w,"\"ok\":false")&&Has(w,"\"source_available\":false")&&Has(w,"\"source\":null")&&!Has(w,"\"unavailable_reason\":null"),"partial/refused Source became usable");}
void ParseYes(A a,const std::string&text){Q q{};Check(g::ParseRiteTextRequest267V1(Request(a,text),q)&&q.text==text&&q.action==a&&g::RiteTextRequestShape267V1(q),"valid exact UTF8 text/action rejected or normalized");}
void ParseNo(A a,const std::string&text){Q q{};Check(!g::ParseRiteTextRequest267V1(Request(a,text),q),"invalid UTF8/scalar/control text accepted");}
const std::string EMOJI="\xF0\x9F\x98\x80", CJK="\xE4\xB8\xAD";

void ThreeActionsAndLeaseRoles(){
  for(auto a:{A::query,A::set_name,A::set_description}){Q q{};auto text=a==A::query?"":"new value";auto w=Request(a,text);Check(g::ParseRiteTextRequest267V1(w,q),"fixed action request rejected");Check(q.action==a&&q.deadline_unix_ms==MAX&&q.expected_source_rite_id==47,"request DATA changed");Check(q.provider_generation==(a==A::query?0:MAX)&&q.query_sequence==(a==A::query?0:MAX),"lease role changed");
    auto bad=a==A::query?Replace(w,"\"provider_generation\":\"0\"","\"provider_generation\":\"1\""):Replace(w,"\"query_sequence\":\"18446744073709551615\"","\"query_sequence\":\"0\"");Check(!g::ParseRiteTextRequest267V1(bad,q),"query/write lease roles mixed");}
  ParseNo(A::query," ");ParseNo(A::query,"name");ParseYes(A::query,"");
}
void FullSignedActorsAndUnsignedRites(){
  for(std::int32_t actor:{0,-2,(std::numeric_limits<std::int32_t>::min)(),(std::numeric_limits<std::int32_t>::max)()})for(std::uint32_t rite:{0U,4294967294U}){Q q{};Check(g::ParseRiteTextRequest267V1(Request(A::query,"","packed",actor,rite),q)&&q.expected.played_character_id==actor&&q.expected_source_rite_id==rite,"packed actor/uint32 Rite boundary lost");}
  Q q{};Check(!g::ParseRiteTextRequest267V1(Request(A::query,"","bad",-1),q),"actor-1 accepted");Check(!g::ParseRiteTextRequest267V1(Request(A::query,"","bad",0,0xFFFFFFFFU),q),"Rite FFFFFFFF accepted");
}
void NameScalarAndByteLimitsAndClear(){
  ParseYes(A::set_name,"");ParseYes(A::set_name,std::string(30,'a'));ParseNo(A::set_name,std::string(31,'a'));
  ParseYes(A::set_name,Repeat(EMOJI,30));ParseNo(A::set_name,Repeat(EMOJI,31));
  ParseYes(A::set_name,Repeat(CJK,30));ParseNo(A::set_name,Repeat(CJK,31));
  ParseYes(A::set_name,Repeat("e\xCC\x81",15));ParseNo(A::set_name,Repeat("e\xCC\x81",16));
  ParseYes(A::set_name,"literal \"quote\" \\ path"); // No normalization or trimmed empty substitutes.
}
void DescriptionScalarByteLimitsAndLfTab(){
  ParseYes(A::set_description,"");ParseYes(A::set_description,std::string(400,'a'));ParseNo(A::set_description,std::string(401,'a'));
  ParseYes(A::set_description,Repeat(EMOJI,400));ParseNo(A::set_description,Repeat(EMOJI,401));
  ParseYes(A::set_description,"line1\n\tline2 "+CJK+EMOJI);
  ParseNo(A::set_name,"line\nname");ParseNo(A::set_name,"tab\tname");
}
void NoncanonicalUtf8AndControlsFail(){
  for(const auto& bad:std::vector<std::string>{std::string("\xC0\xAF",2),std::string("\xE0\x80\x80",3),std::string("\xED\xA0\x80",3),std::string("\xF4\x90\x80\x80",4),std::string("\xF0\x9F",2),std::string("\x80",1)}){ParseNo(A::set_name,bad);ParseNo(A::set_description,bad);}
  for(unsigned byte:{0U,1U,8U,11U,12U,13U,31U,127U}){auto t=std::string("a")+static_cast<char>(byte)+"b";ParseNo(A::set_name,t);ParseNo(A::set_description,t);}
  Q q{};auto unicode_escape=Replace(Request(A::set_name,"PLACEHOLDER"),"PLACEHOLDER","\\ud83d\\ude00");
  Check(g::ParseRiteTextRequest267V1(unicode_escape,q)&&q.text==EMOJI,"valid JSON surrogate pair did not decode to canonical UTF8");
  Check(!g::ParseRiteTextRequest267V1(Replace(Request(A::set_name,"PLACEHOLDER"),"PLACEHOLDER","\\ud800"),q),"unpaired JSON surrogate accepted");
}
void StrictKeysTypesIdentityAndCore(){
  auto w=Request(A::set_name,"a");
  std::vector<std::string> bad{
    Replace(w,"\"protocol_version\":1","\"protocol_version\":1,\"protocol_version\":1"),
    Replace(w,"\"text\":\"a\"","\"text\":\"a\",\"text\":\"a\""),
    Replace(w,"\"paused\":true","\"paused\":true,\"paused\":true"),
    Replace(w,"\"type\":","\"caller_permission\":true,\"type\":"),
    Replace(w,"\"action\":","\"native_can_create\":true,\"action\":"),
    Replace(w,"\"expected_core\":","\"key\":\"arbitrary\",\"expected_core\":"),
    Replace(w,"\"arguments\":{}","\"arguments\":{\"ordinal\":0}"),
    Replace(w,"\"text\":\"a\"","\"text\":null"),Replace(w,",\"text\":\"a\"",""),
    Replace(w,"\"provider_generation\":\"18446744073709551615\"","\"provider_generation\":\"01\""),
    Replace(w,"\"query_sequence\":\"18446744073709551615\"","\"query_sequence\":18446744073709551615"),
    Replace(w,"\"expected_source_rite_id\":47","\"expected_source_rite_id\":-1"),
    Replace(w,"\"expected_source_rite_id\":47","\"expected_source_rite_id\":4294967296"),
    Replace(w,"\"speed\":2","\"speed\":0"),Replace(w,"\"paused\":true","\"paused\":false"),
    Replace(w,"\"local_player_id\":0","\"local_player_id\":-1"),Replace(w,"\"map_ready\":true","\"map_ready\":false"),
    Replace(w,"\"played_character_alive\":true","\"played_character_alive\":false"),
    Replace(w,g::kGameVersion,"1.20.0.4"),Replace(w,g::kRiteTextStep267V1,"current-rite-create-v1"),
    Replace(w,"\"core_control_deadline_unix_ms\":18446744073709551615","\"core_control_deadline_unix_ms\":18446744073709551616"),
    Request(A::query,"","bad/id"),Request(A::query,"",std::string(97,'a')),w+" trailing",std::string(16385,' ')};
  for(const auto&t:bad){Q q{};q.request_id_size=1;q.request_id[0]='x';Check(!g::ParseRiteTextRequest267V1(t,q),"unknown/duplicate/noncanonical request accepted");Check(q.id().empty()&&q.deadline_unix_ms==0&&q.expected_source_rite_id==0xFFFFFFFFU,"failed parse retained request authority");}
}
void EmptyAndFalseSourceDataRemainAvailable(){
  auto r=Available();r.source->name.clear();r.source->description.clear();r.source->is_creating=false;r.source->write_admissible=false;
  auto w=Wire(r);Good(w);Check(Has(w,"\"name\":\"\"")&&Has(w,"\"description\":\"\"")&&Has(w,"\"is_creating\":false"),"empty/false actual DATA fabricated unavailable");
  r=Available();r.source->window_enabled=false;r.source->blocked_by_unrelated_modal=true;r.source->write_admissible=false;Good(Wire(r));
  r=Available();r.source->write_admissible=false;Good(Wire(r)); // Gate implication is not reversible.
  for(std::int32_t actor:{0,-2}){auto q=Available(actor,0);Good(Wire(q));Check(Has(Wire(q),"\"actor_id\":"+std::to_string(actor)),"signed source actor lost");}
}
void SourceReadBoundIsIndependentOfWriteBound(){
  auto r=Available();r.source->name=Repeat(EMOJI,1024);r.source->description=std::string(4096,'x');Good(Wire(r));
  r.source->name+='x';Bad(Wire(r));r=Available();r.source->description=std::string(4097,'x');Bad(Wire(r));
  r=Available();r.source->name=std::string("\xC0\xAF",2);Bad(Wire(r));
  r=Available();r.source->description=CJK+" line\n\t"+EMOJI;auto w=Wire(r);Good(w);Check((Has(w,"\\n")||Has(w,"\\u000a")||Has(w,"\\u000A"))&&(Has(w,"\\t")||Has(w,"\\u0009")),"actual LF/TAB source not safely JSON-escaped");
}
void NameVoidDispatchPreservesBeforeSource(){
  auto r=Dispatched(A::set_name);r.source->name="old name";auto w=Wire(r);Good(w);
  for(auto t:{"\"action\":\"set_name\"","\"status\":\"text_dispatched\"","\"name\":\"old name\"","\"claim_sequence\":\"18446744073709551615\"","\"effect_attempted\":true","\"native_returned\":true"})Check(Has(w,t),"name void ACK lost original beforeSource/claim/return");
  r.claim_sequence=0;Bad(Wire(r));r=Dispatched(A::set_name);r.native_returned=false;Bad(Wire(r));
}
void DescriptionVoidDispatchAndSourceGate(){
  auto r=Dispatched(A::set_description);auto w=Wire(r);Good(w);Check(Has(w,"\"action\":\"set_description\"")&&Has(w,"\"description\":\"Original description\""),"description ACK invented after text");
  r.source->write_admissible=false;Bad(Wire(r));r=Available();r.source->window_enabled=false;Bad(Wire(r));
  r=Available();r.source->actor_id=37846;Bad(Wire(r));r=Available();r.source->source_rite_id=0xFFFFFFFFU;Bad(Wire(r));
}
void RefusalsPartialAndCleanupUnknownHaveNoSource(){
  for(auto s:{S::unavailable,S::expired,S::stale_source,S::claim_consumed,S::prerequisite_rejected}){auto r=Refused(s);if(s==S::claim_consumed)r.claim_sequence=17;auto w=Wire(r);Bad(w);Check(Has(w,"\"effect_attempted\":false")&&Has(w,"\"native_returned\":false"),"early refusal acquired effect");}
  auto r=Dispatched(A::set_name);r.cleanup_known=false;auto w=Wire(r);Bad(w);Check(Has(w,"\"status\":\"indeterminate\"")&&Has(w,"\"cleanup_known\":false"),"unknown cleanup hidden");
  for(unsigned field=0;field<6;++field){auto p=Available();if(field==0)p.source.reset();if(field==1)p.source_available=false;if(field==2)p.facts_available=false;if(field==3)p.connection_generation=0;if(field==4)p.ticket_sequence=0;if(field==5)p.thread_id=0;Bad(Wire(p));}
}
void QueryCannotBorrowWriteClaimOrOutcome(){
  auto r=Available();r.claim_sequence=1;Bad(Wire(r));r=Available();r.effect_attempted=true;Bad(Wire(r));
  r=Available();r.status=S::text_dispatched;Bad(Wire(r));r=Dispatched(A::set_name);r.action=A::query;Bad(Wire(r));
  auto w=Wire(Available());Check(Has(w,"\"claim_sequence\":\"0\"")&&Has(w,"\"effect_attempted\":false")&&Has(w,"\"native_returned\":false"),"query acquired write credit");
}
void WriteNew(const std::filesystem::path&path,const std::string&bytes){HANDLE h=CreateFileW(path.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);if(h==INVALID_HANDLE_VALUE)throw std::runtime_error("CREATE_NEW output refused");DWORD n=0;bool ok=bytes.size()<=(std::numeric_limits<DWORD>::max)()&&WriteFile(h,bytes.data(),static_cast<DWORD>(bytes.size()),&n,nullptr)&&n==bytes.size()&&FlushFileBuffers(h);CloseHandle(h);if(!ok)throw std::runtime_error("original bytes not fully written");}
void Emit(const std::filesystem::path&root){
  if(!CreateDirectoryW(root.c_str(),nullptr))throw std::runtime_error("emit root must be NEW");
  std::vector<std::pair<std::string,R>> rows;
  auto r=Available();r.source->name.clear();r.source->description.clear();rows.emplace_back("query-empty",r);
  r=Available(0,0);r.source->name=CJK+EMOJI;r.source->description="line\n\t"+CJK;rows.emplace_back("query-unicode",r);
  r=Available();r.source->name=Repeat(EMOJI,1024);r.source->description=std::string(4096,'x');rows.emplace_back("query-read4096",r);
  r=Available(-2);r.source->is_creating=false;r.source->write_admissible=false;rows.emplace_back("query-not-creating",r);
  r=Available();r.source->blocked_by_unrelated_modal=true;r.source->write_admissible=false;rows.emplace_back("query-blocked",r);
  rows.emplace_back("name-dispatched",Dispatched(A::set_name));rows.emplace_back("description-dispatched",Dispatched(A::set_description));
  rows.emplace_back("unavailable",Refused(S::unavailable));rows.emplace_back("expired",Refused(S::expired));rows.emplace_back("stale",Refused(S::stale_source));
  r=Refused(S::claim_consumed);r.claim_sequence=17;rows.emplace_back("claim-consumed",r);
  r=Dispatched(A::set_name);r.cleanup_known=false;rows.emplace_back("cleanup-unknown",r);
  for(auto&[name,value]:rows)WriteNew(root/(name+".json"),Wire(value,"rite-text-original-result-"+name)+"\n");
  for(auto a:{A::query,A::set_name,A::set_description})WriteNew(root/(std::string("request-")+Action(a)+".json"),Request(a,a==A::query?"":a==A::set_name?CJK+EMOJI:"line\n\t"+CJK,"rite-text-original-request-"+std::string(Action(a)))+"\n");
}
int Validate(const std::filesystem::path&path){std::ifstream f(path,std::ios::binary);if(!f)throw std::runtime_error("cannot open original request");std::string s;char c=0;while(s.size()<=16384&&f.get(c))s+=c;Q q{};bool good=s.size()<=16384&&g::ParseRiteTextRequest267V1(s,q);std::cout<<(good?"VALID\n":"INVALID\n");return good?0:2;}
}
int main(int argc,char**argv){try{
  if(argc==3&&std::string_view(argv[1])=="--validate-request")return Validate(argv[2]);
  if(argc!=1&&!(argc==3&&std::string_view(argv[1])=="--emit-json"))throw std::runtime_error("usage: test [--emit-json NEWDIR|--validate-request ORIGINAL_BODY]");
  unsigned groups=0;auto test=[&](const char*name,auto body){body();++groups;std::cout<<"PASS "<<name<<'\n';};
  test("three_actions_original_lease",ThreeActionsAndLeaseRoles);test("packed_actor_and_rite",FullSignedActorsAndUnsignedRites);
  test("name_scalar_byte_clear",NameScalarAndByteLimitsAndClear);test("description_scalar_byte_lftab",DescriptionScalarByteLimitsAndLfTab);
  test("utf8_controls_surrogates",NoncanonicalUtf8AndControlsFail);test("strict_keys_identity_core",StrictKeysTypesIdentityAndCore);
  test("empty_false_source_data",EmptyAndFalseSourceDataRemainAvailable);test("read4096_independent_write_bounds",SourceReadBoundIsIndependentOfWriteBound);
  test("name_void_before_source",NameVoidDispatchPreservesBeforeSource);test("description_void_gate",DescriptionVoidDispatchAndSourceGate);
  test("refusal_partial_unknown",RefusalsPartialAndCleanupUnknownHaveNoSource);test("query_no_effect_claim",QueryCannotBorrowWriteClaimOrOutcome);
  if(argc==3)Emit(argv[2]);std::cout<<"NoGame groups="<<groups<<" checks="<<checks<<"; Native ABI/runtime qualification=false\n";return 0;
}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}}
