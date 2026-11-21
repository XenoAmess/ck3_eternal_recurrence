#include "ck3_121003_djc_target_query26785313_wire_v1.cpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
using namespace xar::ck3_121003::build26785313;
void Check(bool b){if(!b)throw std::runtime_error("current DJC target wire invariant");}
std::string Read(const std::filesystem::path&p){std::ifstream f(p,std::ios::binary);if(!f)throw std::runtime_error("read failed");return {std::istreambuf_iterator<char>(f),{}};}
void Write(const std::filesystem::path&p,const std::string&s){Check(!std::filesystem::exists(p));std::ofstream f(p,std::ios::binary);f<<s;f.close();Check(!f.fail());}
std::string Request(){return std::string(R"({"type":"execute_step","protocol_version":1,"request_id":"djc-query-SYNTHETIC","step":")")+kDjcTargetQueryStep267V1+R"(","expected_revision":0,"arguments":{},"djc_war_query":{"schema":")"+kDjcTargetQuerySchema267V1+R"(","game_version":")"+kGameVersion+R"(","executable_sha256":")"+kExecutableSha256+R"(","adapter_id":")"+kAdapterId+R"(","backend":")"+kDjcTargetQueryBackend267V1+R"(","date_raw":53144328,"speed":1,"paused":true,"local_player_id":0,"map_ready":true,"has_played_character":true,"played_character_id":36423,"played_character_alive":true,"target_character_id":39957},"core_control_deadline_unix_ms":4102444800000})";}
DjcTargetQueryResult267V1 Sample(){DjcTargetQueryRequest267V1 q;Check(ParseDjcTargetQueryRequest267V1(Request(),q));DjcTargetQueryResult267V1 r;r.status=DjcTargetQueryStatus267V1::available;r.raw.available=true;r.raw.target_character_id=q.target_character_id;r.core_available=true;r.observed=q.expected;r.connection_generation=7;r.ticket_sequence=11;r.pump_epoch=13;r.thread_id=17;r.provider_generation=UINT64_MAX;r.query_sequence=UINT64_MAX;
 for(std::size_t i=0;i<3;++i){auto&c=r.raw.casus_belli[i];c.key=kDjcCbKeys267V1[i];c.definition_present=c.enabled=c.evaluation_returned=true;c.native_available=false;}return r;}
int main(int argc,char**argv){try{
 if(argc==3&&std::string_view(argv[1])=="--validate-request"){DjcTargetQueryRequest267V1 q;Check(ParseDjcTargetQueryRequest267V1(Read(argv[2]),q));std::cout<<"PASS actual current target parser; no Game/owner calls\n";return 0;}
 DjcTargetQueryRequest267V1 q;const auto request=Request();Check(ParseDjcTargetQueryRequest267V1(request,q));
 for(const auto&change:std::array<std::pair<std::string,std::string>,4>{{{"\"arguments\":{}","\"arguments\":{\"command\":\"x\"}"},{"\"target_character_id\":39957","\"target_character_id\":36423"},{"\"target_character_id\":39957","\"target_character_id\":-1"},{"\"paused\":true","\"paused\":false"}}}){auto s=request;const auto p=s.find(change.first);Check(p!=std::string::npos);s.replace(p,change.first.size(),change.second);Check(!ParseDjcTargetQueryRequest267V1(s,q));}
 auto r=Sample();const auto blocked=SerializeDjcTargetQueryResult267V1("djc-query-SYNTHETIC",r);Check(blocked.find("\"ok\":true")!=std::string::npos&&blocked.find("\"ordinary_can_declare_war\":null")!=std::string::npos);
 r.raw.casus_belli[0].native_available=true;r.raw.casus_belli[0].choices.push_back({42,0,-1,{123,456,123},{7,9,7}});const auto choice=SerializeDjcTargetQueryResult267V1("djc-choice-SYNTHETIC",r);Check(choice.find("[123,456,123]")!=std::string::npos);
 r.raw.cleanup_known=false;const auto unknown=SerializeDjcTargetQueryResult267V1("djc-cleanup-SYNTHETIC",r);Check(unknown.find("\"status\":\"indeterminate\"")!=std::string::npos&&unknown.find("\"ok\":false")!=std::string::npos);
 DjcTargetQueryResult267V1 unavailable;unavailable.raw.target_character_id=39957;unavailable.reason="NoGame_not_owner_qualified";const auto no=SerializeDjcTargetQueryResult267V1("djc-unavailable-NoGame",unavailable);Check(no.find("\"core_before\":null")!=std::string::npos&&no.find("\"casus_belli\":null")!=std::string::npos);
 auto malformed=Sample();malformed.raw.casus_belli[1].key="not_a_fixed_cb";const auto bad=SerializeDjcTargetQueryResult267V1("djc-incoherent-SYNTHETIC",malformed);Check(bad.find("\"ok\":false")!=std::string::npos);
 if(argc==3&&std::string_view(argv[1])=="--emit"){const std::filesystem::path dir=argv[2];Check(!std::filesystem::exists(dir));std::filesystem::create_directories(dir);Write(dir/"request-SYNTHETIC-DATA.json",request);Write(dir/"available-native-blocked-SYNTHETIC-DATA.json",blocked);Write(dir/"available-choice-SYNTHETIC-DATA.json",choice);Write(dir/"indeterminate-cleanup-SYNTHETIC-DATA.json",unknown);Write(dir/"unavailable-NoGame.json",no);Write(dir/"incoherent-SYNTHETIC-DATA.json",bad);}
 std::cout<<"PASS fixed three-CB/target strict parser, actual result serializer, ordered tuple and null ordinary-gate/debit; DATA only\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
