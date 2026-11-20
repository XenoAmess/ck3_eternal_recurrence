#include "ck3_1210_core.cpp"
#include "ck3_1210_core_frame_v1.cpp"
#include "ck3_121003_rite_draft26785313_wire_v2.cpp"
#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
namespace f=xar::ck3_121003::build26785313;
namespace {
void Check(bool b,const char*why){if(!b)throw std::runtime_error(why);}
std::string Request(){return std::string(R"({"type":"execute_step","protocol_version":1,"request_id":"rite-qa-1","step":")")+f::kRiteDraftStepV2+R"(","expected_revision":0,"arguments":{},"rite_draft":{"schema":")"+f::kRiteDraftRequestSchemaV2+R"(","game_version":")"+f::kGameVersion+R"(","executable_sha256":")"+f::kExecutableSha256+R"(","adapter_id":")"+f::kAdapterId+R"(","backend":")"+f::kRiteDraftBackendV2+R"(","deadline_unix_ms":4102444800000,"expected_source_rite_id":152,"expected_core":{"date_raw":53176992,"speed":3,"paused":true,"local_player_id":1,"map_ready":true,"has_played_character":true,"played_character_id":-16777215,"played_character_alive":true}}})";}
std::string Replace(std::string s,std::string_view a,std::string_view b){auto p=s.find(a);Check(p!=std::string::npos,"fixture replacement");s.replace(p,a.size(),b);return s;}
f::ReadonlyObservation Data(){f::ReadonlyObservation o;o.available=true;o.main_owner_observed=true;o.unavailable_reason={};o.core.clock={53176992,3,true};o.core.local_player_id=1;o.core.map_ready=true;o.core.has_played_character=true;o.core.played_character_id=-16777215;o.core.played_character_alive=true;
 f::RiteDraftV2 r;r.gfx=0x1111;r.handler=0x2222;r.controller=0x3333;r.source_rite_id=152;r.can_edit_rite_native=false;r.piety_cost_raw=(std::numeric_limits<std::int64_t>::max)();r.piety_missing_raw=(std::numeric_limits<std::int64_t>::min)();
 auto&w=r.window;w.application=0x4444;w.context=0x5555;w.global_root=0x6666;w.connection_generation=7;w.ticket_sequence=13;w.pump_epoch=23;w.owner_thread_id=42;w.window_found=true;w.requested_name="rite_creation_window";f::GuiWindowNodeV1 n;n.name=w.requested_name;n.visible=true;w.tree.push_back(n);o.rite_draft=std::move(r);return o;}
void Write(const std::filesystem::path&p,const std::string&s){std::ofstream o(p,std::ios::binary);Check(bool(o),"golden open");o<<s<<'\n';Check(bool(o),"golden write");}
}
int main(int argc,char**argv){try{
 const auto request=Request();f::RiteDraftWireRequestV2 parsed;Check(f::ParseRiteDraftRequestV2(request,parsed)&&parsed.owner_request.expected_source_rite_id==152&&parsed.owner_request.window.connection_generation==0&&parsed.owner_request.window.window_name=="rite_creation_window"&&parsed.owner_request.window.expected_core.played_character_id==-16777215,"actual strict request/source rite/signed Core, worker-owned generation, fixed native root");
 for(const auto &pair:std::array<std::pair<std::string_view,std::string_view>,15>{{
 {"\"expected_source_rite_id\":152","\"expected_source_rite_id\":4294967295"},{"\"expected_source_rite_id\":152","\"expected_source_rite_id\":4294967296"},{"\"expected_source_rite_id\":152","\"expected_source_rite_id\":-1"},{"\"expected_source_rite_id\":152","\"expected_source_rite_id\":\"152\""},{"\"expected_source_rite_id\":152","\"expected_source_rite_id\":152.0"},
 {"\"expected_source_rite_id\":152","\"expected_source_rite_id\":152,\"expected_source_rite_id\":152"},{"\"paused\":true","\"paused\":false"},{"\"played_character_id\":-16777215","\"played_character_id\":-1"},
 {"\"deadline_unix_ms\":4102444800000","\"deadline_unix_ms\":0"},{"\"expected_core\":{","\"connection_generation\":7,\"expected_core\":{"},{"\"expected_core\":{","\"window_name\":\"faith_window\",\"expected_core\":{"},
 {"\"arguments\":{}","\"arguments\":{\"address\":1}"},{"\"protocol_version\":1","\"protocol_version\":2"},{"\"schema\":\"ck3.rite_draft_costs_request.v2\"","\"schema\":\"ck3_12002_rite_draft_costs_v1\""},{"\"game_version\":\"1.21.0.3\"","\"game_version\":\"1.21.0\""}
 }})Check(!f::ParseRiteDraftRequestV2(Replace(request,pair.first,pair.second),parsed),"mixedtuple/unknown/duplicate/wrongsource/falsepaused refused");
 Check(!f::ParseRiteDraftRequestV2(request+" trailing",parsed),"trailing refused");
 constexpr std::array<std::string_view,1> caps{xar::ck3_1210::kCoreFrameCapabilityV1};const xar::game::AdapterDescriptor d{f::kAdapterId,f::kGameVersion,f::kExecutableSha256,"xar_checkpoint",caps};const xar::game::AdapterDescriptor wrong{f::kAdapterId,f::kGameVersion,std::string_view{"0000000000000000000000000000000000000000000000000000000000000000"},"xar_checkpoint",caps};
 const auto data=Data();auto unavailable=data;unavailable.offline_fixture=true;unavailable.main_owner_observed=false;
 const auto frame=f::SerializeRiteDraftCommandResultV2("rite-qa-1",data,d);const auto noGame=f::SerializeRiteDraftCommandResultV2("rite-qa-1",unavailable,d);
 Check(noGame.find("\"draft\":null,\"owner_witness\":null")!=std::string::npos&&noGame.find("\"core_available\":false")!=std::string::npos,"NoGame cannot become actual MainOwner quote");
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_DRAFT_V2)
 Check(f::RiteDraftRouteEnabledV2(d)&&!f::RiteDraftRouteEnabledV2(wrong),"only current exact Core-cap query route");
 Check(frame.find("\"draft_available\":true")!=std::string::npos&&frame.find("\"can_edit_rite_native\":false")!=std::string::npos&&frame.find("\"piety_cost_raw\":\"9223372036854775807\"")!=std::string::npos&&frame.find("\"piety_missing_signed_raw\":\"-9223372036854775808\"")!=std::string::npos,"Nativefalse not unavailable; canonical signed64 strings no float/JS precision loss");
 for(const auto marker:{"\"control_actions_available\":false","\"observer_guard_evaluated\":false","\"physical_save_confirmed\":false","\"complete_snapshot\":false","\"addresses_redacted\":true"})Check(frame.find(marker)!=std::string::npos,"finite readonly scope");
 for(const auto marker:{"0x1111","0x2222","0x3333","\"controller\":","\"gfx\":"})Check(frame.find(marker)==std::string::npos,"internal controller identities redacted");
#else
 Check(!f::RiteDraftRouteEnabledV2(d)&&frame.find("\"draft_available\":false")!=std::string::npos,"defaultOFF rejects current query");
#endif
 if(argc==3&&std::string_view(argv[1])=="--emit-rite-fixtures") {std::filesystem::path dir=argv[2];std::filesystem::create_directories(dir);Write(dir/"request-v2.json",request);Write(dir/"partial-native-false-SYNTHETIC-DATA.json",frame);Write(dir/"unavailable-NoGame.json",noGame);Write(dir/"wrong-tuple-unavailable.json",f::SerializeRiteDraftCommandResultV2("rite-qa-1",data,wrong));auto allowed=data;allowed.rite_draft->can_edit_rite_native=true;allowed.rite_draft->piety_cost_raw=0;allowed.rite_draft->piety_missing_raw=1;Write(dir/"partial-native-true-missing-piety-SYNTHETIC-DATA.json",f::SerializeRiteDraftCommandResultV2("rite-qa-1",allowed,d));Write(dir/"qualifier.json",R"({"scope":"actual C++ producer SYNTHETIC DATA / NoGame boundary only","current_native_getter_execution":"NOT_RUN","Game_MainOwner_Rite_Dynastic_confirm_Save":"NOT_RUN","Observer_and_actions":false})");}
 else Check(argc==1,"expected no args or --emit-rite-fixtures outputdir");
 std::cout<<"PASS current RiteCanCost V2 strict request and exact signed64 C++ producer; DATA/NoGame only, live NOT_RUN\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
