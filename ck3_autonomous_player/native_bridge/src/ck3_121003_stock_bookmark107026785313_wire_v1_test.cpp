// Self-owned NoGame DATA. Link actual new wire and its real LYD dependencies.
// No compilation/emission/runtime/ABI credit by this Source author.
#ifndef XAR_STOCK_BOOKMARK1070_TEST_HEADER
#define XAR_STOCK_BOOKMARK1070_TEST_HEADER "xar_bridge/ck3_121003_stock_bookmark107026785313_v1.hpp"
#endif
#include XAR_STOCK_BOOKMARK1070_TEST_HEADER
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
using Request=g::StockBookmarkRequest267V1;
using Source=g::StockBookmarkSource267V1;
using Result=g::StockBookmarkResult267V1;
using Action=g::StockBookmarkAction267V1;
using Status=g::StockBookmarkStatus267V1;
std::size_t checks=0;
void Check(bool x,const char*m){++checks;if(!x)throw std::runtime_error(m);}
bool Has(std::string_view a,std::string_view b){return a.find(b)!=std::string_view::npos;}
std::string Replace(std::string s,std::string_view a,std::string_view b){auto p=s.find(a);Check(p!=std::string::npos,"mutation must alter an original input");s.replace(p,a.size(),b);return s;}
xar::ck3_1210::CoreSnapshotPrefix Core(std::int32_t actor=36423){xar::ck3_1210::CoreSnapshotPrefix c{};c.clock={53144328,2,true};c.local_player_id=0;c.map_ready=c.has_played_character=c.played_character_alive=true;c.played_character_id=actor;return c;}
std::string CoreJson(std::int32_t actor){return "{\"date_raw\":53144328,\"speed\":2,\"paused\":true,\"local_player_id\":0,\"map_ready\":true,\"has_played_character\":true,\"played_character_id\":"+std::to_string(actor)+",\"played_character_alive\":true}";}
std::string RequestJson(Action action=Action::query,std::string_view id="bookmark-original-query-01",std::int32_t actor=36423,std::int32_t instance=1){
 bool select=action==Action::select_c;return std::string("{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"")+std::string(id)+"\",\"step\":\""+std::string(g::kStockBookmarkSteps267V1[select?1:0])+"\",\"expected_revision\":0,\"arguments\":{},\"stock_bookmark1070\":{\"schema\":\""+g::kStockBookmarkRequestSchema267V1+"\",\"game_version\":\""+g::kGameVersion+"\",\"executable_sha256\":\""+g::kExecutableSha256+"\",\"adapter_id\":\""+g::kAdapterId+"\",\"backend\":\""+g::kStockBookmarkBackend267V1+"\",\"action\":\""+(select?"select_c":"query")+"\",\"expected_core\":"+CoreJson(actor)+",\"provider_generation\":"+(select?"18446744073709551615":"0")+",\"query_sequence\":"+(select?"18446744073709551615":"0")+",\"instance_id\":"+(select?std::to_string(instance):"null")+"},\"core_control_deadline_unix_ms\":18446744073709551615}";
}
g::LydEventRow267V1 Event(std::int32_t instance=1,std::int32_t actor=36423){
 g::LydEventRow267V1 e{};e.instance_id=instance;e.recipient_character_id=actor;e.authored_option_count=3;e.definition_key="bookmark.1070";e.opening="self-owned original opening\n#P raw#!";e.description="self-owned complete description";e.named_root_bound=e.window_visible=e.window_enabled=true;
 // Deliberately not array order0,1,2: only actual authored index2 denotes fixed.c.
 for(int index:{2,0,1}){g::LydEventOption267V1 o{};o.authored_option_index=index;o.native_can_select=true;o.text=std::string("self-owned option ")+char('a'+index);e.options.push_back(o);}return e;
}
Source Bound(std::int32_t actor=36423){Source s{};s.event_census.census_complete=true;s.event_census.named_root_count=1;s.event_census.events.push_back(Event(1,actor));s.fixed_instance_id=1;s.select_c_admissible=s.sampled_twice=true;return s;}
Source Empty(){Source s{};s.event_census.census_complete=true;s.sampled_twice=true;return s;}
Result QueryResult(Source s=Bound(),std::int32_t actor=36423){Result r{};r.action=Action::query;r.status=Status::available;r.source_available=r.cleanup_known=r.facts_available=true;r.provider_generation=r.query_sequence=r.connection_generation=r.ticket_sequence=r.pump_epoch=(std::numeric_limits<std::uint64_t>::max)();r.thread_id=(std::numeric_limits<std::uint32_t>::max)();r.facts=Core(actor);r.source=std::move(s);return r;}
Result Chosen(){auto r=QueryResult();r.action=Action::select_c;r.status=Status::selection_dispatched;r.instance_id=1;r.claim_sequence=7;r.effect_attempted=r.native_returned=true;return r;}
std::string Wire(const Result&r,std::string_view id="bookmark-self-owned-result"){return g::SerializeStockBookmarkResult267V1(id,r);}
void AlwaysFalse(const std::string&w){for(auto t:{"\"native_handled\":false","\"event_closed\":false","\"new_date_observed\":false","\"physical_save_confirmed\":false","\"addresses_redacted\":true"})Check(Has(w,t),"dispatch/query cannot grant closure/date/save/handled");}
void Available(const std::string&w){AlwaysFalse(w);Check(Has(w,"\"ok\":true")&&Has(w,"\"status\":\"available\"")&&Has(w,"\"source_available\":true")&&Has(w,"\"claim_sequence\":\"0\"")&&Has(w,"\"instance_id\":null")&&Has(w,"\"effect_attempted\":false")&&Has(w,"\"native_returned\":false"),"complete query is readonly known DATA");}
void Refused(const std::string&w,std::string_view status,bool source=false){AlwaysFalse(w);Check(Has(w,"\"ok\":false")&&Has(w,"\"status\":\""+std::string(status)+"\""),"exact typed refusal");Check(Has(w,source?"\"source_available\":true":"\"source_available\":false"),"actual refusal Source presence retained coherently");if(!source)Check(Has(w,"\"source\":null"),"partial/unknown source must not be invented");Check(!Has(w,"\"unavailable_reason\":null"),"actual refusal reason retained");}

void StrictTwoActionsAndPackedExpectedCore(){
 for(auto actor:{std::int32_t{36423},std::int32_t{0},std::int32_t{-2},(std::numeric_limits<std::int32_t>::min)()})for(auto action:{Action::query,Action::select_c}){Request r{};Check(g::ParseStockBookmarkRequest267V1(RequestJson(action,"bookmark-packed",actor),r),"actual signed packed actor and two strict actions");Check(r.action==action&&r.expected.played_character_id==actor&&r.deadline_unix_ms==(std::numeric_limits<std::uint64_t>::max)()&&g::StockBookmarkRequestShape267V1(r),"real parsed fields retained");if(action==Action::select_c)Check(r.instance_id==1&&r.provider_generation==(std::numeric_limits<std::uint64_t>::max)(),"positive uint64 integer claim and actual instance");else Check(!r.instance_id&&r.provider_generation==0&&r.query_sequence==0,"query has no caller lease/instance");}
}
void DuplicateUnknownAndCallerOrdinalRejected(){
 const auto q=RequestJson();std::vector<std::string> bad{Replace(q,"\"protocol_version\":1","\"protocol_version\":1,\"protocol_version\":1"),Replace(q,"\"action\":\"query\"","\"action\":\"query\",\"action\":\"query\""),Replace(q,"\"paused\":true","\"paused\":true,\"paused\":true"),Replace(q,"\"type\":","\"permission\":true,\"type\":"),Replace(q,"\"action\":","\"event_key\":\"bookmark.1070\",\"action\":"),Replace(q,"\"action\":","\"option_index\":2,\"action\":"),Replace(q,"\"action\":","\"option_key\":\"bookmark.1070.c\",\"action\":"),Replace(q,"\"arguments\":{}","\"arguments\":{\"role\":\"lyd_begin\"}"),Replace(q,"\"expected_core\":","\"actor\":36423,\"expected_core\":"),Replace(q,",\"instance_id\":null",""),Replace(q,",\"played_character_alive\":true","")};
 for(const auto&w:bad){Request r{};r.request_id_size=1;r.request_id[0]='x';Check(!g::ParseStockBookmarkRequest267V1(w,r),"strict outer8/claim10/Core8 no duplicate/unknown/caller selector");Check(r.id().empty()&&r.deadline_unix_ms==0,"failed parse clears stale request");}
}
void TypedNumbersActionStepAndInstanceLimits(){
 const auto q=RequestJson(),s=RequestJson(Action::select_c,"bookmark-original-select-02");std::vector<std::string> bad{RequestJson(Action::query,""),RequestJson(Action::query,"bad/id"),RequestJson(Action::query,std::string(97,'a')),RequestJson(Action::query,"nonascii-\xc3\xa9"),RequestJson(Action::query,"reserved",-1),Replace(q,"\"provider_generation\":0","\"provider_generation\":1"),Replace(q,"\"query_sequence\":0","\"query_sequence\":1"),Replace(q,"\"instance_id\":null","\"instance_id\":1"),Replace(s,"\"instance_id\":1","\"instance_id\":0"),Replace(s,"\"instance_id\":1","\"instance_id\":-2"),Replace(s,"\"instance_id\":1","\"instance_id\":2147483648"),Replace(s,"\"provider_generation\":18446744073709551615","\"provider_generation\":\"18446744073709551615\""),Replace(s,"\"query_sequence\":18446744073709551615","\"query_sequence\":0"),Replace(s,"\"action\":\"select_c\"","\"action\":\"query\""),Replace(q,"\"action\":\"query\"","\"action\":\"select_any\""),Replace(q,"\"paused\":true","\"paused\":1"),Replace(q,"\"speed\":2","\"speed\":2.0"),Replace(q,"18446744073709551615","18446744073709551616"),Replace(q,g::kGameVersion,"1.20.0.4"),q+"{}",q.substr(0,q.size()-1),std::string(16385,' ')};
 for(const auto&w:bad){Request r{};Check(!g::ParseStockBookmarkRequest267V1(w,r),"typed identities/step/action/uint64 and signed32 guards");}
 Request r{};Check(g::ParseStockBookmarkRequest267V1(" \t"+RequestJson(Action::query,std::string(96,'a'))+"\r\n",r),"ASCII96 and JSON whitespace valid");Check(g::ParseStockBookmarkRequest267V1(RequestJson(Action::select_c,"max-instance",36423,(std::numeric_limits<std::int32_t>::max)()),r),"positive signed32 instance maximum");
}
void DirectShapeRequiresOriginalCoreAndQueryLeaseRoles(){
 Request q{},s{};Check(g::ParseStockBookmarkRequest267V1(RequestJson(),q)&&g::ParseStockBookmarkRequest267V1(RequestJson(Action::select_c,"shape-select"),s),"two original baselines");
 for(int i=0;i<11;++i){auto r=q;switch(i){case 0:r.expected.played_character_id=-1;break;case 1:r.expected.local_player_id=-1;break;case 2:r.expected.clock.paused=false;break;case 3:r.expected.clock.speed=0;break;case 4:r.expected.clock.speed=6;break;case 5:r.expected.map_ready=false;break;case 6:r.expected.has_played_character=false;break;case 7:r.expected.played_character_alive=false;break;case 8:r.deadline_unix_ms=0;break;case 9:r.provider_generation=1;break;default:r.instance_id=1;break;}Check(!g::StockBookmarkRequestShape267V1(r),"query direct shape must not acquire action role");}
 for(int i=0;i<3;++i){auto r=s;if(i==0)r.provider_generation=0;if(i==1)r.query_sequence=0;if(i==2)r.instance_id.reset();Check(!g::StockBookmarkRequestShape267V1(r),"selection requires original positive query and instance");}
}
void CompleteSourceResolvesAuthoredCNotArrayOrdinal(){
 auto s=Bound();Check(s.event_census.events[0].options[0].authored_option_index==2&&g::StockBookmarkSourceShape267V1(s),"original authoredC row may be first in memory");Available(Wire(QueryResult(s)));
 for(auto&o:s.event_census.events[0].options)if(o.authored_option_index!=2)o.native_can_select=false;
 Check(g::StockBookmarkSourceShape267V1(s),"other options Canfalse must not reject actual admissible C");Available(Wire(QueryResult(s)));Check(Has(Wire(QueryResult(s)),"\"authored_option_index\":2"),"original authored index kept, not caller index");
}
void AbsentForeignAndNativeCanFalseRemainQueryData(){
 auto e=Empty();Check(g::StockBookmarkSourceShape267V1(e),"complete empty census is available negative DATA");Available(Wire(QueryResult(e)));
 auto wrong=Bound();wrong.event_census.events[0].definition_key="other_actual.event";wrong.fixed_instance_id.reset();wrong.select_c_admissible=false;Check(g::StockBookmarkSourceShape267V1(wrong),"unrelated actual definition remains readable");Available(Wire(QueryResult(wrong)));
 auto no=Bound();for(auto&o:no.event_census.events[0].options)if(o.authored_option_index==2)o.native_can_select=false;no.select_c_admissible=false;Check(g::StockBookmarkSourceShape267V1(no),"actual Canfalse does not become unavailable");Available(Wire(QueryResult(no)));
 auto multiple=Bound();multiple.event_census.events.push_back(Event(2));multiple.event_census.named_root_count=2;multiple.fixed_instance_id.reset();multiple.select_c_admissible=false;Check(g::StockBookmarkSourceShape267V1(multiple),"multiple actual roots are complete observable DATA");Available(Wire(QueryResult(multiple)));
}
void PartialDuplicateAndMisassociatedModelsRejected(){
 for(int i=0;i<8;++i){auto s=Bound();switch(i){case 0:s.sampled_twice=false;break;case 1:s.event_census.census_complete=false;break;case 2:s.event_census.named_root_count=2;break;case 3:s.event_census.events[0].options[1].authored_option_index=2;break;case 4:s.fixed_instance_id=9;break;case 5:s.event_census.events[0].definition_key="wrong.event";break;case 6:s.event_census.events.push_back(Event(2));s.event_census.named_root_count=2;break;default:for(auto&o:s.event_census.events[0].options)if(o.authored_option_index==2)o.native_can_select=false;break;}Check(!g::StockBookmarkSourceShape267V1(s),"partial/duplicate/foreign fixed model or falseCan must not claim admissible");}
}
void RawUtf8RichtextLengthAndNulBoundaries(){
 auto s=Bound();s.event_census.events[0].opening="#P rich#!\n\t\x15";s.event_census.events[0].description=std::string(16384,'x');Check(g::StockBookmarkSourceShape267V1(s),"real controls and full16384 cached text retained");auto w=Wire(QueryResult(s));Available(w);Check(Has(w,"#P rich#!")&&Has(w,"\\u0015")&&Has(w,std::string(16384,'x')),"serializer full raw text, no localization replacement");
 for(const auto&t:std::vector<std::string>{std::string(16385,'x'),std::string("a\0b",3),std::string("\xc0\xaf",2),std::string("\xed\xa0\x80",3)}){auto bad=Bound();bad.event_census.events[0].description=t;Check(!g::StockBookmarkSourceShape267V1(bad),"existing Letter/LYD text forbids NUL/invalidUTF8/oversize; not Text-family rules");}
}
void OnceVoidDispatchKeepsImmutableBeforeSourceAndNoPoststate(){
 const auto r=Chosen();const auto w=Wire(r);AlwaysFalse(w);Check(Has(w,"\"ok\":true")&&Has(w,"\"status\":\"selection_dispatched\"")&&Has(w,"\"effect_attempted\":true")&&Has(w,"\"native_returned\":true")&&Has(w,"\"claim_sequence\":\"7\""),"known fixed.c void dispatch with positive spentclaim");Check(Has(w,"\"instance_id\":1")&&Has(w,"self-owned original opening")&&Has(w,"self-owned option c"),"ACK retains original complete beforeSource, not fictional absence");
 auto bad=r;bad.instance_id=2;Refused(Wire(bad),"indeterminate");bad=r;bad.claim_sequence=0;Refused(Wire(bad),"indeterminate");bad=r;bad.native_returned=false;Refused(Wire(bad),"indeterminate");
}
void RefusalMayPreserveActualSourceButUnknownCannot(){
 auto stale=QueryResult();stale.action=Action::select_c;stale.status=Status::stale_source;stale.instance_id=1;stale.reason="actual original source stale before effect";Refused(Wire(stale),"stale_source",true);
 auto expired=Result{};expired.status=Status::expired;expired.reason="original deadline expired";Refused(Wire(expired),"expired");
 auto unknown=Chosen();unknown.status=Status::indeterminate;unknown.cleanup_known=false;unknown.native_returned=false;unknown.source_available=false;unknown.source.reset();unknown.reason="actual cleanup uncertain after write";auto w=Wire(unknown);Refused(w,"indeterminate");Check(Has(w,"\"cleanup_known\":false")&&Has(w,"\"effect_attempted\":true")&&Has(w,"\"claim_sequence\":\"7\""),"original unknown/spentclaim not rewritten as no dispatch");
}
void PositiveOwnerFactsAndFullUnsignedResults(){
 auto r=QueryResult();auto w=Wire(r);Available(w);Check(Has(w,"\"provider_generation\":\"18446744073709551615\"")&&Has(w,"\"thread_id\":4294967295"),"result witnesses use full unsigned typed strings/number");
 for(int i=0;i<7;++i){auto bad=r;switch(i){case 0:bad.facts_available=false;break;case 1:bad.connection_generation=0;break;case 2:bad.ticket_sequence=0;break;case 3:bad.pump_epoch=0;break;case 4:bad.thread_id=0;break;case 5:bad.provider_generation=0;break;default:bad.query_sequence=0;break;}Refused(Wire(bad),"indeterminate");}
 for(auto actor:{std::int32_t{0},std::int32_t{-2}})Available(Wire(QueryResult(Bound(actor),actor)));
}
void CompleteAfterCensusIsSeparateFromDispatchCredit(){
 auto absent=QueryResult(Empty());Available(Wire(absent));auto foreign=Bound();foreign.event_census.events[0].definition_key="other_actual.event";foreign.fixed_instance_id.reset();foreign.select_c_admissible=false;auto still=Wire(QueryResult(foreign));Available(still);Check(Has(still,"\"instance_id\":1"),"fixed_instance null does not mean original instance absent from complete census");AlwaysFalse(still);AlwaysFalse(Wire(Chosen()));
}
void WriteNew(const std::filesystem::path&p,const std::string&data){auto h=CreateFileW(p.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);if(h==INVALID_HANDLE_VALUE)throw std::runtime_error("CREATE_NEW emission refused");DWORD n=0;bool ok=data.size()<=(std::numeric_limits<DWORD>::max)()&&WriteFile(h,data.data(),static_cast<DWORD>(data.size()),&n,nullptr)&&n==data.size()&&FlushFileBuffers(h);bool close=CloseHandle(h)!=0;Check(ok&&close,"complete producer write");}
struct Frame{const char*name;const char*id;Result result;};
void Emit(const std::filesystem::path&dir){
 if(!std::filesystem::create_directory(dir))throw std::runtime_error("output directory must be new");std::vector<Frame> f;
 f.push_back({"available-original.json","bookmark-original-query-01",QueryResult()});f.push_back({"selection-c-dispatched.json","bookmark-original-select-02",Chosen()});f.push_back({"available-empty.json","bookmark-empty-03",QueryResult(Empty())});auto s=Bound();s.event_census.events[0].definition_key="other_actual.event";s.fixed_instance_id.reset();s.select_c_admissible=false;f.push_back({"available-wrong-definition.json","bookmark-wrong-04",QueryResult(s)});s=Bound();for(auto&o:s.event_census.events[0].options)if(o.authored_option_index==2)o.native_can_select=false;s.select_c_admissible=false;f.push_back({"available-native-can-false.json","bookmark-can-false-05",QueryResult(s)});s=Bound();s.event_census.events.push_back(Event(2));s.event_census.named_root_count=2;s.fixed_instance_id.reset();s.select_c_admissible=false;f.push_back({"available-multiple.json","bookmark-multiple-06",QueryResult(s)});
 Result r{};r.status=Status::expired;r.reason="original_deadline_expired";f.push_back({"expired.json","bookmark-expired-07",r});r=Chosen();r.status=Status::indeterminate;r.cleanup_known=false;r.native_returned=false;r.source_available=false;r.source.reset();r.reason="cleanup_unknown";f.push_back({"indeterminate-cleanup.json","bookmark-cleanup-08",r});r=QueryResult();r.action=Action::select_c;r.status=Status::stale_source;r.instance_id=1;r.reason="actual_source_stale";f.push_back({"stale-with-original-source.json","bookmark-stale-09",r});r=QueryResult();r.source->sampled_twice=false;f.push_back({"indeterminate-incomplete.json","bookmark-partial-10",r});
 WriteNew(dir/"request-query.json",RequestJson());WriteNew(dir/"request-select-c.json",RequestJson(Action::select_c,"bookmark-original-select-02"));std::vector<std::string>ids;for(const auto&v:f){Check(std::find(ids.begin(),ids.end(),v.id)==ids.end(),"distinct original IDs");ids.push_back(v.id);auto w=Wire(v.result,v.id);AlwaysFalse(w);WriteNew(dir/v.name,w);}Check(f.size()==10,"ten actual serializer replies");
}
int Validate(const std::filesystem::path&p){std::ifstream f(p,std::ios::binary);if(!f)throw std::runtime_error("input unavailable");std::array<char,16385>b{};f.read(b.data(),static_cast<std::streamsize>(b.size()));auto n=static_cast<std::size_t>(f.gcount());if(n>16384)return 2;Request q{};return g::ParseStockBookmarkRequest267V1(std::string_view(b.data(),n),q)?0:2;}
}
int main(int argc,char**argv){try{
 if(argc==3&&std::string_view(argv[1])=="--validate-request")return Validate(std::filesystem::path(argv[2]));
 StrictTwoActionsAndPackedExpectedCore();DuplicateUnknownAndCallerOrdinalRejected();TypedNumbersActionStepAndInstanceLimits();DirectShapeRequiresOriginalCoreAndQueryLeaseRoles();CompleteSourceResolvesAuthoredCNotArrayOrdinal();AbsentForeignAndNativeCanFalseRemainQueryData();PartialDuplicateAndMisassociatedModelsRejected();RawUtf8RichtextLengthAndNulBoundaries();OnceVoidDispatchKeepsImmutableBeforeSourceAndNoPoststate();RefusalMayPreserveActualSourceButUnknownCannot();PositiveOwnerFactsAndFullUnsignedResults();CompleteAfterCensusIsSeparateFromDispatchCredit();
 if(argc==3&&std::string_view(argv[1])=="--emit-json")Emit(std::filesystem::path(argv[2]));else if(argc!=1)throw std::runtime_error("usage: test [--emit-json NEWDIR | --validate-request FILE]");std::printf("stock bookmark1070:12 self-owned NoGame wire groups/%zu checks\n",checks);return 0;
 }catch(const std::exception&e){std::fprintf(stderr,"bookmark wire after %zu checks: %s\n",checks,e.what());return 1;}}
