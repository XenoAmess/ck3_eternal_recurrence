#include "ck3_1210_core.cpp"
#include "ck3_1210_core_frame_v1.cpp"
#include "ck3_1210_gui_control_v1.cpp"
#include "ck3_121003_gui_controls26785313_wire_v2.cpp"
#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
namespace f=xar::ck3_121003::build26785313;
namespace {
void Check(bool b,const char*why){if(!b)throw std::runtime_error(why);}
std::string Request(){return std::string(R"({"type":"execute_step","protocol_version":1,"request_id":"controls-qa-1","step":")")+f::kGuiControlsQueryStep267V2+R"(","expected_revision":0,"arguments":{},"gui_control":{"schema":")"+f::kGuiControlsRequestSchema267V2+R"(","game_version":")"+f::kGameVersion+R"(","executable_sha256":")"+f::kExecutableSha256+R"(","adapter_id":")"+f::kAdapterId+R"(","backend":")"+f::kGuiControlsBackend267V2+R"(","deadline_unix_ms":4102444800000,"window_name":"rite_creation_window","expected_source_rite_id":152,"expected_core":{"date_raw":53176992,"speed":3,"paused":true,"local_player_id":1,"map_ready":true,"has_played_character":true,"played_character_id":-16777215,"played_character_alive":true}}})";}
std::string Replace(std::string s,std::string_view a,std::string_view b){auto p=s.find(a);Check(p!=std::string::npos,"fixture replacement");s.replace(p,a.size(),b);return s;}
std::string Activate(){return Replace(Replace(Request(),f::kGuiControlsQueryStep267V2,f::kGuiControlsActivateStep267V2),"\"window_name\":","\"query_generation\":\"18446744073709551615\",\"widget_id\":\"2\",\"window_name\":");}
f::GuiControlsContext267V2 Data(){f::GuiControlsContext267V2 q;q.request.window_name="rite_creation_window";q.request.connection_generation=7;
 q.observed.clock={53176992,3,true};q.observed.local_player_id=1;q.observed.map_ready=true;q.observed.has_played_character=true;q.observed.played_character_id=-16777215;q.observed.played_character_alive=true;
 q.expected_source_rite_id=152;q.verified_source_rite_id=152;q.request.expected_core=q.observed;q.control.root_name=q.request.window_name;q.control.step=f::kGuiControlsQueryStep267V2;
 q.core_before_verified=true;q.witness_ticket_sequence=13;q.witness_pump_epoch=23;q.witness_thread_id=42;
 q.result.status=xar::ck3_1210::GuiControlStatusV1::available;q.result.application_main_observed=true;q.result.source_abi_pins_verified=true;q.result.query_generation=(std::numeric_limits<std::uint64_t>::max)();
 q.result.widgets={{1,"rite_creation_window","",0,true,true,false},{2,"edit_faith","0",0,true,true,true}};return q;}
void Write(const std::filesystem::path&p,const std::string&s){std::ofstream out(p,std::ios::binary);Check(bool(out),"golden open");out<<s<<'\n';Check(bool(out),"golden write");}
}
int main(int argc,char**argv){try{
 const auto request=Request(),activate=Activate();f::GuiControlsWireRequest267V2 parsed;
 Check(f::ParseGuiControlsRequest267V2(request,parsed)&&!parsed.control.activate&&parsed.owner_request.connection_generation==0&&parsed.owner_request.expected_core.played_character_id==-16777215,"strict current query Core; generation only supplied by actual WorkerState");
 Check(f::ParseGuiControlsRequest267V2(activate,parsed)&&parsed.control.activate&&parsed.control.query_generation==(std::numeric_limits<std::uint64_t>::max)()&&parsed.control.widget_id==2,"positive canonical uint64 string query handles preserve all64bits");
 for(const auto &token:{"\"0\"","\"00\"","\"+1\"","\"-1\"","\"1.0\"","\"18446744073709551616\"","1","1.0"})
  Check(!f::ParseGuiControlsRequest267V2(Replace(activate,"\"18446744073709551615\"",token),parsed),"noncanonical/overflow/number/float query lease refused");
 for(const auto &pair:std::array<std::pair<std::string_view,std::string_view>,13>{{
 {"\"window_name\":\"rite_creation_window\"","\"window_name\":\"main_menu\""},{"\"paused\":true","\"paused\":false"},{"\"played_character_id\":-16777215","\"played_character_id\":-1"},{"\"played_character_id\":-16777215","\"played_character_id\":0"},
 {"\"expected_core\":{","\"connection_generation\":7,\"expected_core\":{"},{"\"expected_core\":{","\"address\":1,\"expected_core\":{"},{"\"arguments\":{}","\"arguments\":{\"expression\":\"x\"}"},
 {"\"deadline_unix_ms\":4102444800000","\"deadline_unix_ms\":0"},{"\"window_name\":","\"widget_id\":\"2\",\"window_name\":"},{"\"protocol_version\":1","\"protocol_version\":2"},
 {"\"game_version\":\"1.21.0.3\"","\"game_version\":\"1.21.0\""},{"\"schema\":\"ck3.scripted_widget_controls_request.v2\"","\"schema\":\"ck3_1210_gui_control_v1\""},
 {"\"paused\":true","\"paused\":true,\"paused\":true"}
 }})Check(!f::ParseGuiControlsRequest267V2(Replace(request,pair.first,pair.second),parsed),"wrongtuple/unsafe scope/unknown/duplicate field refused");
 Check(!f::ParseGuiControlsRequest267V2(request+" trailing",parsed),"trailing refused");
 constexpr std::array<std::string_view,3> caps{xar::ck3_1210::kCoreFrameCapabilityV1,f::kGuiControlsQueryCapability267V2,f::kGuiControlsActivateCapability267V2};
 const xar::game::AdapterDescriptor descriptor{f::kAdapterId,f::kGameVersion,f::kExecutableSha256,"xar_checkpoint",caps};
 const xar::game::AdapterDescriptor wrong{f::kAdapterId,f::kGameVersion,"0000000000000000000000000000000000000000000000000000000000000000","xar_checkpoint",caps};
 const auto data=Data();auto noGame=data;noGame.core_before_verified=false;noGame.result.application_main_observed=false;noGame.result.status=xar::ck3_1210::GuiControlStatusV1::unavailable;
 const auto available=f::SerializeGuiControlsCommandResult267V2("controls-qa-1",data,descriptor),unavailable=f::SerializeGuiControlsCommandResult267V2("controls-qa-1",noGame,descriptor);
 Check(unavailable.find("\"query_available\":false")!=std::string::npos&&unavailable.find("\"widgets\":null")!=std::string::npos&&unavailable.find("\"owner_witness\":null")!=std::string::npos,"NoGame cannot claim owner/query");
#if defined(XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2) && XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2
 Check(f::GuiControlsRouteEnabled267V2(descriptor,true)&&!f::GuiControlsRouteEnabled267V2(wrong,true),"only current narrow explicit cap route");
 Check(available.find("\"query_available\":true")!=std::string::npos&&available.find("\"query_generation\":\"18446744073709551615\"")!=std::string::npos,"actual producer canonical handles");
#else
 Check(!f::GuiControlsRouteEnabled267V2(descriptor,true)&&available.find("\"query_available\":false")!=std::string::npos,"defaultOFF closed");
#endif
 for(const auto marker:{"\"full_snapshot_before_verified\":false","\"complete_snapshot\":false","\"complete_gui_tree\":false","\"effect_confirmed\":false","\"physical_save_confirmed\":false","\"addresses_redacted\":true"})Check(available.find(marker)!=std::string::npos,"current Core is not Full/action/save confirmation");
 auto submitted=data;submitted.control.activate=true;submitted.control.step=f::kGuiControlsActivateStep267V2;submitted.result.status=xar::ck3_1210::GuiControlStatusV1::submitted;submitted.result.effect_attempted=true;submitted.result.native_handled=true;submitted.result.verification_pending=true;
 auto unknown=submitted;unknown.result.status=xar::ck3_1210::GuiControlStatusV1::indeterminate;unknown.result.native_handled=false;unknown.result.unavailable_reason="gui_dispatch_indeterminate_no_retry";
 auto disabled=data;disabled.control.activate=true;disabled.result.status=xar::ck3_1210::GuiControlStatusV1::disabled;disabled.result.unavailable_reason="gui_button_not_currently_clickable";
 if(argc==3&&std::string_view(argv[1])=="--emit-controls-fixtures"){std::filesystem::path dir=argv[2];std::filesystem::create_directories(dir);
  Write(dir/"query-request-v2.json",request);Write(dir/"activate-request-v2.json",activate);Write(dir/"available-query-SYNTHETIC-DATA.json",available);Write(dir/"unavailable-NoGame.json",unavailable);
  Write(dir/"submitted-SYNTHETIC-DATA.json",f::SerializeGuiControlsCommandResult267V2("controls-qa-1",submitted,descriptor));
  Write(dir/"indeterminate-SYNTHETIC-DATA.json",f::SerializeGuiControlsCommandResult267V2("controls-qa-1",unknown,descriptor));
  Write(dir/"disabled-SYNTHETIC-DATA.json",f::SerializeGuiControlsCommandResult267V2("controls-qa-1",disabled,descriptor));
  Write(dir/"wrong-tuple-unavailable.json",f::SerializeGuiControlsCommandResult267V2("controls-qa-1",data,wrong));
  Write(dir/"qualifier.json",R"({"scope":"actual C++ serializer with synthetic DATA / NoGame boundary; not a Runtime receipt","MainOwner_NativeDispatch_Dynastic_confirm_Save":"NOT_RUN","semantic_doctrine_row_key":"NOT_RESOLVED","full_snapshot":false,"effect_confirmed":false})");
 }else Check(argc==1,"expected no args or --emit-controls-fixtures directory");
 std::cout<<"PASS current controls V2 strict query/one-use handle wire schema; DATA/NoGame only, live NOT_RUN\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
