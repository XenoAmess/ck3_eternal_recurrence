#include "ck3_1210_core.cpp"
#include "ck3_1210_core_frame_v1.cpp"
#include "ck3_121003_rite_doctrine26785313_wire_v1.cpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
namespace f=xar::ck3_121003::build26785313;
namespace {
void Check(bool value,const char*why){if(!value)throw std::runtime_error(why);}
std::string Request() {
 return std::string(R"({"type":"execute_step","protocol_version":1,"request_id":"rite-doctrine-qa-1","step":")")+f::kRiteDoctrineStep267V1+
 R"(","expected_revision":0,"arguments":{},"rite_doctrine":{"schema":")"+f::kRiteDoctrineSchema267V1+
 R"(","game_version":")"+f::kGameVersion+R"(","executable_sha256":")"+f::kExecutableSha256+
 R"(","adapter_id":")"+f::kAdapterId+R"(","backend":")"+f::kGuiWindowBackendV1+
 R"(","action":"query","deadline_unix_ms":4102444800000,"expected_core":{"date_raw":53144376,"speed":1,"paused":true,"local_player_id":1,"map_ready":true,"has_played_character":true,"played_character_id":-16777215,"played_character_alive":true},"expected_source_rite_id":152,"provider_generation":"0","query_sequence":"0"}})";
}
std::string Replace(std::string value,std::string_view from,std::string_view to) {
 const auto at=value.find(from);Check(at!=std::string::npos,"fixture substring");value.replace(at,from.size(),to);return value;
}
std::string Action(std::string_view action) {
 auto value=Replace(Request(),"\"action\":\"query\"",std::string("\"action\":\"")+std::string(action)+'"');
 value=Replace(value,"\"provider_generation\":\"0\"","\"provider_generation\":\"18446744073709551615\"");
 return Replace(value,"\"query_sequence\":\"0\"","\"query_sequence\":\"18446744073709551615\"");
}
f::RiteDoctrineResult267V1 Facts() {
 f::RiteDoctrineResult267V1 r;r.status=f::RiteDoctrineStatus267V1::available;
 r.provider_generation=18446744073709551615ULL;r.query_sequence=18446744073709551615ULL;
 auto&d=r.facts;d.core_before_verified=true;d.source_rite_verified=true;d.source_rite_id=152;
 d.core.clock={53144376,1,true};d.core.local_player_id=1;d.core.map_ready=true;d.core.has_played_character=true;d.core.played_character_id=-16777215;d.core.played_character_alive=true;
 d.connection_generation=7;d.ticket_sequence=13;d.pump_epoch=23;d.thread_id=42;
 d.category_available=true;d.target_available=true;d.should_display_evaluated=true;d.should_display=true;
 d.can_pick_evaluated=true;d.can_pick=true;d.knowledge_evaluated=true;d.known_doctrine=true;
 d.selected_evaluated=true;d.selected=false;d.can_edit_evaluated=true;d.can_edit=true;
 d.piety_cost_raw=17500000;d.piety_missing_raw=-82500000;return r;
}
void Write(const std::filesystem::path&p,const std::string&value) {
 std::ofstream out(p,std::ios::binary);Check(bool(out),"output open");out<<value<<'\n';Check(bool(out),"output write");
}
}
int main(int argc,char**argv){try {
 if(argc==3&&std::string_view(argv[1])=="--validate-request") {
  std::ifstream in(argv[2],std::ios::binary);Check(bool(in),"external request open");std::string body(16385,'\0');in.read(body.data(),static_cast<std::streamsize>(body.size()));body.resize(static_cast<std::size_t>(in.gcount()));
  f::RiteDoctrineRequest267V1 parsed;return f::ParseRiteDoctrineRequest267V1(body,parsed)?0:1;
 }
 f::RiteDoctrineRequest267V1 parsed;
 Check(f::ParseRiteDoctrineRequest267V1(Request(),parsed)&&parsed.action==f::RiteDoctrineAction267V1::query&&parsed.window.connection_generation==0&&parsed.window.expected_core.played_character_id==-16777215,"strict current query, signed actor and actual connection kept outside caller");
 for(const auto action:{"open_dynastic_category","select_dynastic","confirm_edit"})
  Check(f::ParseRiteDoctrineRequest267V1(Action(action),parsed)&&parsed.provider_generation==18446744073709551615ULL&&parsed.query_sequence==18446744073709551615ULL,"three fixed actions preserve uint64 lease strings");
 const auto select=Action("select_dynastic");
 for(const auto value:{"\"00\"","\"+1\"","\"-0\"","\"18446744073709551616\"","1","1.0","\"1.0\""})
  Check(!f::ParseRiteDoctrineRequest267V1(Replace(select,"\"provider_generation\":\"18446744073709551615\"",std::string("\"provider_generation\":")+value),parsed),"noncanonical/number/float/overflow lease refused");
 for(const auto actor:{"0","-1"})Check(!f::ParseRiteDoctrineRequest267V1(Replace(Request(),"-16777215",actor),parsed),"sentinel actor refused without rejecting legitimate negative full IDs");
 for(const auto mutation:{std::pair{"\"paused\":true","\"paused\":false"},std::pair{"\"action\":\"query\"","\"action\":\"activate_arbitrary\""},
  std::pair{"\"expected_core\":{","\"raw_address\":1,\"expected_core\":{"},std::pair{"\"arguments\":{}","\"arguments\":{\"key\":\"des_doctrine_dynastic\"}"},
  std::pair{"\"deadline_unix_ms\":4102444800000","\"deadline_unix_ms\":0"},std::pair{"\"paused\":true","\"paused\":true,\"paused\":true"},
  std::pair{"\"game_version\":\"1.21.0.3\"","\"game_version\":\"1.21.0\""}})
  Check(!f::ParseRiteDoctrineRequest267V1(Replace(Request(),mutation.first,mutation.second),parsed),"wrongtuple/unpaused/unknown fields/duplicate/deadline rejected");
 Check(!f::ParseRiteDoctrineRequest267V1(Replace(select,"\"provider_generation\":\"18446744073709551615\"","\"provider_generation\":\"0\""),parsed),"effect requires original private query lease");
 Check(!f::ParseRiteDoctrineRequest267V1(Request()+" garbage",parsed),"trailing payload refused");
 auto query=Facts();const auto query_json=f::SerializeRiteDoctrineResult267V1("rite-doctrine-qa-1",query);
 Check(query_json.find("\"status\":\"available\"")!=std::string::npos&&query_json.find("\"provider_generation\":\"18446744073709551615\"")!=std::string::npos,"actual serializer preserves explicit query lease");
 auto selected=query;selected.action=f::RiteDoctrineAction267V1::select_dynastic;selected.status=f::RiteDoctrineStatus267V1::draft_selected;
 selected.effect_attempted=true;selected.native_returned=true;selected.claim_sequence=1;selected.post_selected_evaluated=true;selected.post_selected=true;
 const auto selected_json=f::SerializeRiteDoctrineResult267V1("rite-doctrine-qa-1",selected);
 Check(selected_json.find("\"status\":\"draft_selected\"")!=std::string::npos&&selected_json.find("\"selected\":false")!=std::string::npos&&selected_json.find("\"post_selected\":true")!=std::string::npos,"before facts and actual post-selection observation stay distinct");
 auto incomplete=selected;incomplete.claim_sequence=0;
 Check(f::SerializeRiteDoctrineResult267V1("rite-doctrine-qa-1",incomplete).find("\"status\":\"indeterminate\"")!=std::string::npos,"incoherent claimed success normalizes to unknown");
 auto pam=query;pam.facts.known_doctrine=false;
 Check(f::SerializeRiteDoctrineResult267V1("rite-doctrine-qa-1",pam).find("\"pam_gate_available\":false")!=std::string::npos,"false known branch does not assert the whole knowledge/perk OR is false");
 auto unavailable=query;unavailable.status=f::RiteDoctrineStatus267V1::unavailable;unavailable.facts={};unavailable.reason="current_rite_owner_source_unavailable";
 Check(f::SerializeRiteDoctrineResult267V1("rite-doctrine-qa-1",unavailable).find("\"facts\":null,\"owner_witness\":null")!=std::string::npos,"unavailable emits no guessed source/witness");
 if(argc==3&&std::string_view(argv[1])=="--emit-rite-doctrine-fixtures") {
  const std::filesystem::path dir=argv[2];std::filesystem::create_directories(dir);
  Write(dir/"query-request.json",Request());Write(dir/"query-SYNTHETIC-DATA.json",query_json);
  for(const auto action:{"open_dynastic_category","select_dynastic","confirm_edit"})Write(dir/(std::string(action)+"-request.json"),Action(action));
  Write(dir/"selected-SYNTHETIC-DATA.json",selected_json);
  auto opened=query;opened.action=f::RiteDoctrineAction267V1::open_dynastic_category;opened.status=f::RiteDoctrineStatus267V1::category_opened;opened.effect_attempted=true;opened.native_returned=true;opened.claim_sequence=1;
  Write(dir/"category-opened-SYNTHETIC-DATA.json",f::SerializeRiteDoctrineResult267V1("rite-doctrine-qa-1",opened));
  auto confirm=selected;confirm.action=f::RiteDoctrineAction267V1::confirm_edit;confirm.status=f::RiteDoctrineStatus267V1::confirmation_dispatched;confirm.facts.selected=true;confirm.native_handled=true;confirm.post_selected_evaluated=false;confirm.post_selected=false;confirm.claim_sequence=2;
  Write(dir/"confirmation-dispatched-SYNTHETIC-DATA.json",f::SerializeRiteDoctrineResult267V1("rite-doctrine-qa-1",confirm));
  Write(dir/"indeterminate-SYNTHETIC-DATA.json",f::SerializeRiteDoctrineResult267V1("rite-doctrine-qa-1",incomplete));
  Write(dir/"pam-unresolved-SYNTHETIC-DATA.json",f::SerializeRiteDoctrineResult267V1("rite-doctrine-qa-1",pam));
  Write(dir/"unavailable-NoGame.json",f::SerializeRiteDoctrineResult267V1("rite-doctrine-qa-1",unavailable));
  Write(dir/"qualifier.json",R"({"scope":"Actual C++ DTO serializer with explicit SYNTHETIC DATA/NoGame only","native_owner_or_ABI_call":false,"GuiAction":false,"RiteBusinessConfirm":false,"physicalSave":false})");
 }else Check(argc==1,"no arguments or existing validation/fixture mode required");
 std::cout<<"PASS Rite exact request and redacted before/after contract; synthetic DATA only, owner/native/GUI/business NOT_RUN\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
