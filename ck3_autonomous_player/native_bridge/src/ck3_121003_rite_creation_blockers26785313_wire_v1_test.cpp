// Self-owned NoGame DATA only. Link the actual candidate wire TU, never a copy.
// No compilation/execution by this Source author; no native getter/ABI credit.
#ifndef XAR_RITE_CREATION_BLOCKERS_TEST_HEADER
#define XAR_RITE_CREATION_BLOCKERS_TEST_HEADER "xar_bridge/ck3_121003_rite_creation_blockers26785313_v1.hpp"
#endif
#include XAR_RITE_CREATION_BLOCKERS_TEST_HEADER
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <Windows.h>
#include <algorithm>
#include <array>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace g=xar::ck3_121003::build26785313;
namespace {
using Request=g::RiteBlockersRequest267V1;
using Result=g::RiteBlockersResult267V1;
using Source=g::RiteBlockersSource267V1;
using Status=g::RiteBlockersStatus267V1;
std::size_t checks=0;
void Check(bool value,const char*label){++checks;if(!value)throw std::runtime_error(label);}
bool Has(std::string_view s,std::string_view v){return s.find(v)!=std::string_view::npos;}
std::string Replace(std::string s,std::string_view from,std::string_view to){auto p=s.find(from);Check(p!=std::string::npos,"mutation must affect actual input");s.replace(p,from.size(),to);return s;}
xar::ck3_1210::CoreSnapshotPrefix Core(std::int32_t actor=36423){
 xar::ck3_1210::CoreSnapshotPrefix c{};c.clock={53144328,2,true};c.local_player_id=0;c.map_ready=c.has_played_character=c.played_character_alive=true;c.played_character_id=actor;return c;
}
std::string CoreJson(std::int32_t actor=36423){return "{\"date_raw\":53144328,\"speed\":2,\"paused\":true,\"local_player_id\":0,\"map_ready\":true,\"has_played_character\":true,\"played_character_id\":"+std::to_string(actor)+",\"played_character_alive\":true}";}
std::string Query(std::string_view id="blockers-original-query-01",std::int32_t actor=36423,std::uint32_t rite=47){
 return std::string("{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"")+std::string(id)+"\",\"step\":\""+g::kRiteBlockersStep267V1+"\",\"expected_revision\":0,\"arguments\":{},\"rite_creation_blockers\":{\"schema\":\""+g::kRiteBlockersRequestSchema267V1+"\",\"game_version\":\""+g::kGameVersion+"\",\"executable_sha256\":\""+g::kExecutableSha256+"\",\"adapter_id\":\""+g::kAdapterId+"\",\"backend\":\""+g::kRiteBlockersBackend267V1+"\",\"action\":\"query_blockers\",\"expected_core\":"+CoreJson(actor)+",\"expected_source_rite_id\":"+std::to_string(rite)+"},\"core_control_deadline_unix_ms\":18446744073709551615}";
}
Result Available(std::int32_t actor=36423,std::uint32_t rite=47){
 Result r{};r.status=Status::available;r.source_available=r.cleanup_known=r.facts_available=true;
 r.provider_generation=r.query_sequence=r.connection_generation=r.ticket_sequence=r.pump_epoch=(std::numeric_limits<std::uint64_t>::max)();r.thread_id=(std::numeric_limits<std::uint32_t>::max)();r.facts=Core(actor);
 Source s{};s.source_rite_id=rite;s.actor_id=actor;s.is_creating=true;s.native_can_create=false;s.window_visible=s.window_enabled=s.sampled_twice=true;r.source=s;return r;
}
std::string Wire(const Result&r,std::string_view id="blockers-self-owned-result"){return g::SerializeRiteBlockersResult267V1(id,r);}
void Readonly(const std::string&w){
 for(const auto v:{"\"action\":\"query_blockers\"","\"claim_sequence\":\"0\"","\"effect_attempted\":false","\"native_returned\":false","\"native_handled\":false","\"new_date_observed\":false","\"physical_save_confirmed\":false","\"addresses_redacted\":true"})Check(Has(w,v),"readonly result must retain every zero-effect field");
}
void Valid(const std::string&w){Readonly(w);Check(Has(w,"\"ok\":true")&&Has(w,"\"status\":\"available\"")&&Has(w,"\"source_available\":true")&&Has(w,"\"sampled_twice\":true")&&Has(w,"\"unavailable_reason\":null"),"complete actual DATA must serialize available");}
void Refused(const std::string&w,std::string_view status){Readonly(w);Check(Has(w,"\"ok\":false")&&Has(w,"\"status\":\""+std::string(status)+"\""),"typed refusal status retained");Check(Has(w,"\"source_available\":false")&&Has(w,"\"source\":null"),"refusal must not expose partial source");Check(Has(w,"\"provider_generation\":\"0\"")&&Has(w,"\"query_sequence\":\"0\""),"all refusal informational sequences zero");Check(!Has(w,"\"unavailable_reason\":null"),"refusal reason is nonempty");}

void ValidRequestPackedActorsAndRiteGuard(){
 for(auto actor:{std::int32_t{36423},std::int32_t{0},std::int32_t{-2},(std::numeric_limits<std::int32_t>::min)(),(std::numeric_limits<std::int32_t>::max)()})for(auto rite:{std::uint32_t{0},std::uint32_t{47},std::uint32_t{0xFFFFFFFEU}}){Request q{};Check(g::ParseRiteBlockersRequest267V1(Query("blockers-signed-id",actor,rite),q),"packed actor and mandatory uint32 Rite DATA retained");Check(q.id()=="blockers-signed-id"&&q.expected.played_character_id==actor&&q.expected_source_rite_id==rite,"full request DATA retained");Check(q.deadline_unix_ms==(std::numeric_limits<std::uint64_t>::max)()&&g::RiteBlockersRequestShape267V1(q),"full uint64 deadline and shape");}
 std::string digest=g::kExecutableSha256;std::transform(digest.begin(),digest.end(),digest.begin(),[](char c){return c>='A'&&c<='F'?static_cast<char>(c-'A'+'a'):c;});Request q{};Check(g::ParseRiteBlockersRequest267V1(Replace(Query(),g::kExecutableSha256,digest),q),"only SHA case normalization allowed");
}
void DuplicateUnknownOrCallerPermissionRejected(){
 const auto q=Query();std::vector<std::string> bad{
 Replace(q,"\"protocol_version\":1","\"protocol_version\":1,\"protocol_version\":1"),Replace(q,"\"action\":\"query_blockers\"","\"action\":\"query_blockers\",\"action\":\"query_blockers\""),Replace(q,"\"paused\":true","\"paused\":true,\"paused\":true"),Replace(q,"\"type\":","\"can_create\":true,\"type\":"),Replace(q,"\"action\":","\"text\":\"caller reason\",\"action\":"),Replace(q,"\"action\":","\"provider_generation\":\"1\",\"action\":"),Replace(q,"\"expected_core\":","\"actor\":36423,\"expected_core\":"),Replace(q,"\"arguments\":{}","\"arguments\":{\"key\":\"arbitrary\"}"),Replace(q,"\"paused\":true","\"key\":\"create\",\"paused\":true"),Replace(q,"\"query_blockers\"","\"create\""),Replace(q,",\"expected_source_rite_id\":47",""),Replace(q,",\"played_character_alive\":true","")};
 for(const auto&w:bad){Request out{};out.request_id_size=1;out.request_id[0]='x';Check(!g::ParseRiteBlockersRequest267V1(w,out),"strict outer8/claim8/Core8 rejects unknown/duplicate/missing");Check(out.id().empty()&&out.deadline_unix_ms==0,"failed parse clears stale prior authority");}
}
void NumericIdentityJsonAndSizeBoundaries(){
 const auto q=Query();std::vector<std::string> bad{Query(""),Query("bad/id"),Query(std::string(97,'a')),Query("bad-\xc3\xa9"),Query("reserved",-1),Query("reserved-rite",36423,0xFFFFFFFFU),Replace(q,"53144328","053144328"),Replace(q,"\"speed\":2","\"speed\":2.0"),Replace(q,"\"paused\":true","\"paused\":1"),Replace(q,"\"local_player_id\":0","\"local_player_id\":-0"),Replace(q,"\"played_character_id\":36423","\"played_character_id\":2147483648"),Replace(q,"\"played_character_id\":36423","\"played_character_id\":-2147483649"),Replace(q,"\"expected_source_rite_id\":47","\"expected_source_rite_id\":true"),Replace(q,"\"expected_source_rite_id\":47","\"expected_source_rite_id\":-1"),Replace(q,"\"expected_source_rite_id\":47","\"expected_source_rite_id\":4294967296"),Replace(q,"18446744073709551615","18446744073709551616"),Replace(q,"18446744073709551615","\"18446744073709551615\""),Replace(q,"18446744073709551615","0"),Replace(q,g::kGameVersion,"1.20.0.4"),Replace(q,g::kRiteBlockersBackend267V1,"arbitrary"),Replace(q,"\"expected_revision\":0","\"expected_revision\":1"),q+"{}",q.substr(0,q.size()-1),std::string(16385,' ')};
 for(const auto&w:bad){Request out{};Check(!g::ParseRiteBlockersRequest267V1(w,out),"wrong type/overflow/identity/JSON/size refused");}
 Request out{};Check(g::ParseRiteBlockersRequest267V1(" \n\t"+Query(std::string(96,'a'))+"\r\n",out),"ASCII96 ID and JSON whitespace valid");
}
void DirectCoreShapeCannotAuthorizeInvalidScope(){
 Request q{};Check(g::ParseRiteBlockersRequest267V1(Query(),q),"real parser baseline");
 for(int i=0;i<11;++i){auto v=q;switch(i){case 0:v.expected.played_character_id=-1;break;case 1:v.expected.local_player_id=-1;break;case 2:v.expected.clock.paused=false;break;case 3:v.expected.clock.speed=0;break;case 4:v.expected.clock.speed=6;break;case 5:v.expected.map_ready=false;break;case 6:v.expected.has_played_character=false;break;case 7:v.expected.played_character_alive=false;break;case 8:v.expected_source_rite_id=0xFFFFFFFFU;break;case 9:v.deadline_unix_ms=0;break;default:v.request_id_size=97;break;}Check(!g::RiteBlockersRequestShape267V1(v),"direct shape rejects invalid scope/deadline/id before read");}
 for(std::uint32_t speed:{1U,5U}){auto v=q;v.expected.clock.speed=speed;Check(g::RiteBlockersRequestShape267V1(v),"both valid speed bounds");}
}
void FalseCanEmptyReasonAndHiddenSourceAreAvailableData(){
 for(int i=0;i<4;++i){auto r=Available();if(i==1)r.source->is_creating=false;if(i==2)r.source->window_visible=false;if(i==3)r.source->window_enabled=false;const auto w=Wire(r);Valid(w);Check(Has(w,"\"native_can_create\":false")&&Has(w,"\"blockers_text\":\"\""),"false Can with empty text is DATA not inferred permission or reason");}
 auto r=Available();r.source->native_can_create=true;r.source->blockers_text="self-owned explanatory DATA";Valid(Wire(r));
}
void FullLengthUnicodeRichtextAndEmbeddedNulPreserved(){
 auto r=Available();r.source->blockers_text=std::string("a\0b",3)+"\x15"+"#P rich#!\n\t"+"\xe4\xb8\xad";auto w=Wire(r);Valid(w);Check(Has(w,"a\\u0000b")&&Has(w,"\\u0015")&&Has(w,"\xe4\xb8\xad"),"length-based NUL/richtext/UTF8 preserved rather than strlen/truncation");Check(!Has(w,std::string("a\0b",3)),"raw JSON must not contain literal control bytes");
 r.source->blockers_text=std::string(16384,'x');w=Wire(r);Valid(w);Check(Has(w,r.source->blockers_text),"full16384 ASCII bytes preserved");
 r.source->blockers_text.clear();for(int i=0;i<4096;++i)r.source->blockers_text+="\xf0\x9f\x98\x80";Valid(Wire(r));Check(r.source->blockers_text.size()==16384,"read limit counts bytes not4096 glyphs");
}
void InvalidUtf8AndOverlengthNeverBecomeTruncatedAvailable(){
 std::vector<std::string> invalid{std::string(16385,'x'),std::string("\x80",1),std::string("\xc0\xaf",2),std::string("\xed\xa0\x80",3),std::string("\xf4\x90\x80\x80",4),std::string("\xe2\x82",2)};
 for(const auto&t:invalid){auto r=Available();r.source->blockers_text=t;Refused(Wire(r),"indeterminate");}
}
void IncompleteSourceActorMismatchAndReservedRiteRejected(){
 for(int i=0;i<5;++i){auto r=Available();switch(i){case 0:r.source.reset();break;case 1:r.source->sampled_twice=false;break;case 2:r.source->actor_id=40180;break;case 3:r.source->actor_id=-1;break;default:r.source->source_rite_id=0xFFFFFFFFU;break;}Refused(Wire(r),"indeterminate");}
 for(auto actor:{std::int32_t{0},std::int32_t{-2}}){auto r=Available(actor,0);auto w=Wire(r);Valid(w);Check(Has(w,"\"actor_id\":"+std::to_string(actor))&&Has(w,"\"source_rite_id\":0"),"actual packed actor0/-2 and Rite0 retained");}
}
void FactsAndPositiveOwnerWitnessesAreRequiredTogether(){
 auto w=Wire(Available());Valid(w);Check(Has(w,"\"provider_generation\":\"18446744073709551615\"")&&Has(w,"\"thread_id\":4294967295"),"full unsigned informational fields retained");
 for(int i=0;i<8;++i){auto r=Available();switch(i){case 0:r.facts_available=false;break;case 1:r.connection_generation=0;break;case 2:r.ticket_sequence=0;break;case 3:r.pump_epoch=0;break;case 4:r.thread_id=0;break;case 5:r.provider_generation=0;break;case 6:r.query_sequence=0;break;default:r.facts.clock.paused=false;break;}Refused(Wire(r),"indeterminate");}
}
void CleanupUnknownAndChangedCoreNeverExposeCachedFalse(){
 auto r=Available();r.cleanup_known=false;auto w=Wire(r);Refused(w,"indeterminate");Check(Has(w,"\"cleanup_known\":false"),"unknown cleanup remains unknown");
 r=Available();r.status=Status::stale_source;r.facts.played_character_id=40180;r.reason="actual_source_core_changed";w=Wire(r);Refused(w,"stale_source");Check(Has(w,"\"played_character_id\":40180")&&!Has(w,"\"actor_id\":36423"),"changed facts never retain old actual Source");
}
void TypedRefusalsZeroInformationalSequencesAndEscapeReasons(){
 const std::array<std::pair<Status,const char*>,4> statuses{{{Status::unavailable,"unavailable"},{Status::expired,"expired"},{Status::stale_source,"stale_source"},{Status::indeterminate,"indeterminate"}}};
 for(const auto&[s,name]:statuses){auto r=Available();r.status=s;r.reason="self-owned \"why\"\\path\nline";auto w=Wire(r);Refused(w,name);Check(Has(w,"\\\"why\\\"\\\\path"),"official serializer escapes raw refusal data");}
 Result r{};r.reason="actual_missing_definition";auto w=Wire(r);Refused(w,"unavailable");Check(Has(w,"\"facts_before\":null")&&Has(w,"\"owner\":null"),"no synthetic facts or owner");
}
void ReadonlyReasonTextDoesNotMintActionAuthority(){
 auto r=Available();r.source->blockers_text="CanCreate=true; execute arbitrary -- this is only source DATA";auto w=Wire(r);Valid(w);Readonly(w);Check(Has(w,"\"native_can_create\":false"),"reason text cannot overwrite actual boolean or readonly flags");
 r.source->blockers_text="";r.source->native_can_create=true;w=Wire(r);Valid(w);Readonly(w);
}

void WriteNew(const std::filesystem::path&p,const std::string&data){auto h=CreateFileW(p.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);if(h==INVALID_HANDLE_VALUE)throw std::runtime_error("CREATE_NEW emission refused");DWORD n=0;bool ok=data.size()<=(std::numeric_limits<DWORD>::max)()&&WriteFile(h,data.data(),static_cast<DWORD>(data.size()),&n,nullptr)&&n==data.size()&&FlushFileBuffers(h);bool closed=CloseHandle(h)!=0;Check(ok&&closed,"complete immutable output");}
struct Frame{const char*name;const char*id;Result result;};
void Emit(const std::filesystem::path&dir){
 if(!std::filesystem::create_directory(dir))throw std::runtime_error("emission directory must be new");
 std::vector<Frame> frames;frames.push_back({"available-false-can-empty.json","blockers-original-query-01",Available()});auto r=Available();r.source->is_creating=r.source->window_visible=r.source->window_enabled=false;frames.push_back({"available-hidden-notcreating.json","blockers-hidden-02",r});r=Available();r.source->blockers_text=std::string("a\0b",3)+"\x15"+"#P detail#!\n\t";frames.push_back({"available-richtext-nul.json","blockers-richtext-03",r});frames.push_back({"available-actor-zero-rite-zero.json","blockers-actor-zero-04",Available(0,0)});frames.push_back({"available-actor-negative-rite-max.json","blockers-actor-negative-05",Available(-2,0xFFFFFFFEU)});
 r=Available();r.status=Status::unavailable;r.reason="actual_definition_unavailable";frames.push_back({"unavailable-definition.json","blockers-unavailable-06",r});r=Result{};r.status=Status::expired;r.reason="actual_deadline_expired";frames.push_back({"expired-before-source.json","blockers-expired-07",r});r=Available();r.status=Status::stale_source;r.facts.played_character_id=40180;r.reason="actual_core_changed";frames.push_back({"stale-core.json","blockers-stale-08",r});r=Available();r.cleanup_known=false;r.reason="cleanup_unknown";frames.push_back({"indeterminate-cleanup.json","blockers-cleanup-09",r});r=Available();r.source->sampled_twice=false;frames.push_back({"indeterminate-partial-samples.json","blockers-partial-10",r});
 WriteNew(dir/"request-query-blockers.json",Query());std::vector<std::string> ids;
 for(const auto&f:frames){Check(std::find(ids.begin(),ids.end(),f.id)==ids.end(),"distinct genuine serializer IDs");ids.push_back(f.id);auto w=Wire(f.result,f.id);Readonly(w);WriteNew(dir/f.name,w);}Check(frames.size()==10,"ten actual serializer outputs");
}
int ValidateRequest(const std::filesystem::path&p){std::ifstream in(p,std::ios::binary);if(!in)throw std::runtime_error("request input unavailable");std::array<char,16385> b{};in.read(b.data(),static_cast<std::streamsize>(b.size()));auto n=static_cast<std::size_t>(in.gcount());if(n>16384)return 2;Request q{};return g::ParseRiteBlockersRequest267V1(std::string_view(b.data(),n),q)?0:2;}
}
int main(int argc,char**argv){try{
 if(argc==3&&std::string_view(argv[1])=="--validate-request")return ValidateRequest(std::filesystem::path(argv[2]));
 ValidRequestPackedActorsAndRiteGuard();DuplicateUnknownOrCallerPermissionRejected();NumericIdentityJsonAndSizeBoundaries();DirectCoreShapeCannotAuthorizeInvalidScope();FalseCanEmptyReasonAndHiddenSourceAreAvailableData();FullLengthUnicodeRichtextAndEmbeddedNulPreserved();InvalidUtf8AndOverlengthNeverBecomeTruncatedAvailable();IncompleteSourceActorMismatchAndReservedRiteRejected();FactsAndPositiveOwnerWitnessesAreRequiredTogether();CleanupUnknownAndChangedCoreNeverExposeCachedFalse();TypedRefusalsZeroInformationalSequencesAndEscapeReasons();ReadonlyReasonTextDoesNotMintActionAuthority();
 if(argc==3&&std::string_view(argv[1])=="--emit-json")Emit(std::filesystem::path(argv[2]));else if(argc!=1)throw std::runtime_error("usage: test [--emit-json NEWDIR | --validate-request FILE]");std::printf("Rite blockers:12 NoGame wire groups/%zu checks; no runtime or ABI credit\n",checks);return 0;
 }catch(const std::exception&e){std::fprintf(stderr,"blockers wire test after %zu checks: %s\n",checks,e.what());return 1;}}
