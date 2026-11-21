#include "ck3_121003_frontend_menu26785313_wire_v1.cpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
namespace f=xar::ck3_121003::build26785313;
namespace {
void Check(bool v,const char*why){if(!v)throw std::runtime_error(why);}
std::string Replace(std::string s,std::string_view from,std::string_view to){const auto p=s.find(from);Check(p!=std::string::npos,"fixture token");s.replace(p,from.size(),to);return s;}
std::string Request(f::FrontendMenuAction267V1 action) {
 const bool query=action==f::FrontendMenuAction267V1::query_menu;
 const auto lease=query?"0":"18446744073709551615";
 return std::string(R"({"type":"execute_step","protocol_version":1,"request_id":"frontend-menu-qa-1","step":")")+std::string(f::FrontendMenuStep267V1(action))+
 R"(","expected_revision":0,"arguments":{},"frontend_menu":{"schema":")"+f::kFrontendMenuRequestSchema267V1+
 R"(","game_version":")"+f::kGameVersion+R"(","executable_sha256":")"+f::kExecutableSha256+
 R"(","adapter_id":")"+f::kAdapterId+R"(","backend":")"+f::kFrontendMenuBackend267V1+
 R"(","action":")"+f::Name(action)+R"(","deadline_unix_ms":4102444800000,"provider_generation":")"+lease+R"(","query_sequence":")"+lease+R"("}})";
}
f::FrontendMenuResult267V1 Facts(){f::FrontendMenuResult267V1 r;r.status=f::FrontendMenuStatus267V1::available;
 r.provider_generation=r.query_sequence=18446744073709551615ULL;auto&s=r.facts;s.route=f::FrontendMenuRoute267V1::main_menu;
 s.application_verified=s.gui_context_verified=s.global_root_verified=s.route_root_visible=s.no_world=true;
 s.connection_generation=7;s.ticket_sequence=13;s.pump_epoch=23;s.thread_id=42;return r;}
void Write(const std::filesystem::path&p,const std::string&s){std::ofstream out(p,std::ios::binary);Check(bool(out),"fixture open");out<<s<<'\n';Check(bool(out),"fixture write");}
}
int main(int argc,char**argv){try{using A=f::FrontendMenuAction267V1;using S=f::FrontendMenuStatus267V1;using Route=f::FrontendMenuRoute267V1;
 if(argc==3&&std::string_view(argv[1])=="--validate-request"){std::ifstream in(argv[2],std::ios::binary);Check(bool(in),"external request open");std::string s(16385,'\0');in.read(s.data(),static_cast<std::streamsize>(s.size()));s.resize(static_cast<std::size_t>(in.gcount()));f::FrontendMenuRequest267V1 r;return f::ParseFrontendMenuRequest267V1(s,r)?0:1;}
 constexpr std::array actions{A::query_menu,A::quit_menu,A::open_bookmarks,A::select_1066_bookmark,A::select_robert_1066,A::start_robert_1066};
 f::FrontendMenuRequest267V1 parsed;
 for(auto a:actions)Check(f::ParseFrontendMenuRequest267V1(Request(a),parsed)&&parsed.action==a,"six fixed exact requests and canonical uint64 leases");
 const auto effect=Request(A::quit_menu);
 for(auto v:{"\"00\"","\"+1\"","\"-0\"","\"18446744073709551616\"","1","1.0"})
  Check(!f::ParseFrontendMenuRequest267V1(Replace(effect,"\"provider_generation\":\"18446744073709551615\"",std::string("\"provider_generation\":")+v),parsed),"numeric/signed/overflow/noncanonical leases refused");
 for(auto mutation:{std::pair{"\"arguments\":{}","\"arguments\":{\"actor\":1128}"},std::pair{"\"deadline_unix_ms\":4102444800000","\"deadline_unix_ms\":0"},
  std::pair{"\"schema\":","\"no_world\":true,\"schema\":"},std::pair{"\"action\":","\"expected_core\":{},\"action\":"},
  std::pair{"\"game_version\":\"1.21.0.3\"","\"game_version\":\"1.20.0.4\""}})
  Check(!f::ParseFrontendMenuRequest267V1(Replace(effect,mutation.first,mutation.second),parsed),"caller owner/core/actor/oldtuple/invalid deadline refused");
 Check(!f::ParseFrontendMenuRequest267V1(Replace(effect,f::kFrontendMenuQuitStep267V1,f::kFrontendMenuQueryStep267V1),parsed),"action cannot hide behind a readonly step");
 Check(!f::ParseFrontendMenuRequest267V1(effect+" junk",parsed),"trailing bytes refused");
 std::filesystem::path dir;const bool emit=argc==3&&std::string_view(argv[1])=="--emit-frontend-menu-fixtures";
 if(emit){dir=argv[2];std::filesystem::create_directories(dir);}else Check(argc==1,"only actual fixture/validation options accepted");
 for(auto a:actions){auto r=Facts();r.action=a;
  if(a!=A::query_menu){r.effect_attempted=r.native_returned=true;r.claim_sequence=1;}
  switch(a){case A::query_menu:break;case A::quit_menu:r.status=S::exit_requested;break;
  case A::open_bookmarks:r.status=S::bookmarks_opened;r.facts.route=Route::bookmarks;break;
  case A::select_1066_bookmark:r.status=S::bookmark_selected;r.facts.route=Route::bookmarks;r.facts.selected_bookmark_key=f::kFrontendRobertBookmark267V1;break;
  case A::select_robert_1066:r.status=S::selection_dispatched;r.post_selection_verified=true;[[fallthrough]];
  case A::start_robert_1066:if(a==A::start_robert_1066)r.status=S::start_dispatched;r.facts.route=Route::bookmarks;r.facts.selected_bookmark_key=f::kFrontendRobertBookmark267V1;r.facts.selected_character_key=f::kFrontendRobertCharacter267V1;r.facts.robert_source_verified=r.facts.start_admissible=true;break;}
  const auto s=f::SerializeFrontendMenuResult267V1("frontend-menu-qa-1",r);
  Check(s.find("\"ok\":true")!=std::string::npos&&s.find("\"world_core_fabricated\":false")!=std::string::npos&&s.find("\"application_exit_confirmed\":false")!=std::string::npos,"actual serializer keeps software dispatch separate from natural exit/new world/save");
  if(emit){Write(dir/(std::string(f::Name(a))+"-request.json"),Request(a));Write(dir/(std::string(f::Name(a))+"-SYNTHETIC-DATA.json"),s);}
 }
 auto unavailable=Facts();unavailable.action=A::quit_menu;unavailable.status=S::unavailable;unavailable.facts={};unavailable.reason="current_frontend_application_source_unavailable";
 const auto no=f::SerializeFrontendMenuResult267V1("frontend-menu-qa-1",unavailable);
 Check(no.find("\"source\":null,\"owner_witness\":null")!=std::string::npos&&no.find("\"provider_generation\":\"18446744073709551615\"")!=std::string::npos,"early refusal retains lease and fabricates neither source nor Core");
 auto unknown=unavailable;unknown.status=S::indeterminate;unknown.effect_attempted=true;unknown.claim_sequence=1;unknown.reason="current_frontend_native_unknown_no_replay";
 auto bad=Facts();bad.action=A::quit_menu;bad.status=S::exit_requested;bad.effect_attempted=true;bad.claim_sequence=1;
 Check(f::SerializeFrontendMenuResult267V1("frontend-menu-qa-1",bad).find("\"status\":\"indeterminate\"")!=std::string::npos,"a missing native return cannot look like a successful quit");
 if(emit){Write(dir/"unavailable-NoGame.json",no);Write(dir/"indeterminate-SYNTHETIC-DATA.json",f::SerializeFrontendMenuResult267V1("frontend-menu-qa-1",unknown));Write(dir/"incoherent-SYNTHETIC-DATA.json",f::SerializeFrontendMenuResult267V1("frontend-menu-qa-1",bad));Write(dir/"qualifier.json",R"({"scope":"Actual C++ parser/serializer with explicitly SYNTHETIC DATA and NoGame only","native_owner":false,"ABI_calls":false,"menu_observed":false,"natural_exit":false,"new_world":false,"physical_save":false})");}
 std::cout<<"PASS exact current frontend wire/no-fake-Core/lease/dispatch distinctions; native/menu/live NOT_RUN\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
