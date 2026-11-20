// Finite body inclusion matches the existing exact readonly static fixture.
#include "ck3_1210_core.cpp"
#include "ck3_1210_core_frame_v1.cpp"
#include "ck3_121003_gui_window26785313_wire_v1.cpp"
#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace f=xar::ck3_121003::build26785313;
namespace {
void Check(bool good,const char *why){if(!good)throw std::runtime_error(why);}
std::string Request() {
  return std::string(R"({"type":"execute_step","protocol_version":1,"request_id":"root-qa-1","step":")")+
      f::kGuiWindowStepV1+R"(","expected_revision":0,"arguments":{},"gui_window":{"schema":")"+
      f::kGuiWindowRequestSchemaV1+R"(","game_version":")"+f::kGameVersion+R"(","executable_sha256":")"+
      f::kExecutableSha256+R"(","adapter_id":")"+f::kAdapterId+R"(","backend":")"+f::kGuiWindowBackendV1+
      R"(","window_name":"rite_creation_window","deadline_unix_ms":4102444800000,"expected_core":{"date_raw":53176992,"speed":3,"paused":true,"local_player_id":1,"map_ready":true,"has_played_character":true,"played_character_id":-16777215,"played_character_alive":true}}})";
}
std::string Replace(std::string text,std::string_view a,std::string_view b) {
  const auto pos=text.find(a);Check(pos!=std::string::npos,"fixture replacement missing");text.replace(pos,a.size(),b);return text;
}
f::ReadonlyObservation Data() {
  f::ReadonlyObservation in;in.available=true;in.main_owner_observed=true;in.unavailable_reason={};
  in.core.clock={53176992,3,true};in.core.local_player_id=1;in.core.map_ready=true;in.core.has_played_character=true;
  in.core.played_character_id=-16777215;in.core.played_character_alive=true;
  f::GuiWindowV1 roots;roots.logical_owner=0x1111;roots.application=0x2222;roots.first=0x3333;roots.context=0x4444;
  roots.global_root=0x5555;roots.root.widget=roots.global_root;roots.root.context=roots.context;roots.root.child_count=1;roots.root.visible=true;roots.root.enabled=true;
  roots.connection_generation=7;roots.ticket_sequence=13;roots.pump_epoch=23;roots.owner_thread_id=42;roots.requested_name="rite_creation_window";
  f::GuiWindowNodeV1 node;node.widget=0x6666;node.parent=roots.global_root;node.context=roots.context;node.name=roots.requested_name;node.visible=true;node.enabled=true;
  roots.top_level.push_back(node);roots.tree.push_back(node);roots.window_found=true;in.gui_window=std::move(roots);return in;
}
void Write(const std::filesystem::path &p,const std::string &s) {std::ofstream out(p,std::ios::binary);Check(bool(out),"golden open");out<<s<<'\n';Check(bool(out),"golden write");}
}
int main(int argc,char **argv) {
  try {
    const auto request=Request();f::GuiWindowWireRequestV1 parsed;
    Check(f::ParseGuiWindowRequestV1(request,parsed)&&parsed.request_id=="root-qa-1"&&
        parsed.owner_request.expected_core.played_character_id==-16777215&&
        parsed.owner_request.deadline_unix_ms==4102444800000ULL&&
        parsed.owner_request.connection_generation==0,"strict signed Core request, no consumer-owned connection generation");
    for(const auto &pair:std::array<std::pair<std::string_view,std::string_view>,23>{{
      {"\"protocol_version\":1","\"protocol_version\":2"},
      {"\"expected_revision\":0","\"expected_revision\":1"},
      {"\"arguments\":{}","\"arguments\":{\"address\":1}"},
      {"\"request_id\":\"root-qa-1\"","\"request_id\":\"bad/path\""},
      {"\"deadline_unix_ms\":4102444800000","\"deadline_unix_ms\":0"},
      {"\"deadline_unix_ms\":4102444800000","\"deadline_unix_ms\":18446744073709551616"},
      {"\"played_character_id\":-16777215","\"played_character_id\":-1"},
      {"\"played_character_id\":-16777215","\"played_character_id\":2147483648"},
      {"\"played_character_id\":-16777215","\"played_character_id\":\"-16777215\""},
      {"\"played_character_id\":-16777215","\"played_character_id\":-16777215.0"},
      {"\"played_character_id\":-16777215","\"played_character_id\":+1"},
      {"\"played_character_id\":-16777215","\"played_character_id\":01"},
      {"\"played_character_id\":-16777215","\"played_character_id\":-0"},
      {"\"paused\":true","\"paused\":false"},
      {"\"map_ready\":true","\"map_ready\":false"},
      {"\"played_character_alive\":true","\"played_character_alive\":false"},
      {"\"speed\":3","\"speed\":6"},
      {"\"local_player_id\":1","\"local_player_id\":-1"},
      {"\"game_version\":\"1.21.0.3\"","\"game_version\":\"1.21.0\""},
      {"\"expected_core\":{","\"connection_generation\":7,\"expected_core\":{"},
      {"\"expected_core\":{","\"expected_core\":{\"address\":1,"},
      {"\"protocol_version\":1","\"protocol_version\":1,\"protocol_version\":1"},
      {"\"paused\":true","\"paused\":true,\"paused\":true"}
    }})Check(!f::ParseGuiWindowRequestV1(Replace(request,pair.first,pair.second),parsed),"malformed/extra/duplicate/wrong identity request refused");
    for(const auto &pair:std::array<std::pair<std::string_view,std::string_view>,6>{{
      {"\"window_name\":\"rite_creation_window\"","\"window_name\":\"\""},
      {"\"window_name\":\"rite_creation_window\"","\"window_name\":null"},
      {"\"window_name\":\"rite_creation_window\"","\"window_name\":\"bad/path\""},
      {"\"window_name\":\"rite_creation_window\"","\"window_name\":\"rite_creation_window\",\"window_name\":\"rite_creation_window\""},
      {"\"window_name\":\"rite_creation_window\",",""},
      {"\"schema\":\"ck3.scripted_gui_window_request.v1\"","\"schema\":\"ck3.scripted_gui_root_index_request.v1\""}
    }})Check(!f::ParseGuiWindowRequestV1(Replace(request,pair.first,pair.second),parsed),"new claim name/variant/duplicate/refusal boundaries");
    Check(!f::ParseGuiWindowRequestV1(request+" trailing",parsed),"trailing request refused");
    Check(!f::ParseGuiWindowRequestV1(Replace(request,f::kExecutableSha256,std::string(64,'0')),parsed),"old or mixed EXE refused");
    constexpr std::array<std::string_view,1> caps{xar::ck3_1210::kCoreFrameCapabilityV1};
    const xar::game::AdapterDescriptor d{f::kAdapterId,f::kGameVersion,f::kExecutableSha256,"xar_checkpoint",caps};
    const xar::game::AdapterDescriptor wrong{f::kAdapterId,f::kGameVersion,"BB3FEF106240E95ECDB6F1532982E89E9432C92A99D33DB623521572F06E6F79","xar_checkpoint",caps};
    const auto data=Data();const auto partial=f::SerializeGuiWindowCommandResultV1("root-qa-1",data,d);
    auto offline=data;offline.offline_fixture=true;offline.main_owner_observed=false;
    const auto unavailable=f::SerializeGuiWindowCommandResultV1("root-qa-1",offline,d);
    Check(unavailable.find("\"top_level\":null,\"window\":null,\"owner_witness\":null")!=std::string::npos&&
        unavailable.find("\"core_available\":false")!=std::string::npos&&
        unavailable.find("\"played_character_id\":null")!=std::string::npos,"NoGame cannot emit live root/core/owner witness");
#if defined(XAR_CK3_ENABLE_121003_26785313_GUI_WINDOW_V1)
    Check(f::GuiWindowRouteEnabledV1(d)&&!f::GuiWindowRouteEnabledV1(wrong),"current exact Corecap root QA route only");
    Check(partial.find("\"status\":\"partial\"")!=std::string::npos&&partial.find("\"played_character_id\":-16777215")!=std::string::npos&&
        partial.find("\"window_available\":true")!=std::string::npos,"actual C++ synthetic DATA producer preserves signed Core/counts");
    for(const auto literal:{"0x1111","0x2222","0x4444","0x7777","0x8888","\"widget\":","\"object\":"})
      Check(partial.find(literal)==std::string::npos,"all addresses remain redacted");
    for(const auto field:{"\"addresses_redacted\":true","\"complete_snapshot\":false","\"complete_gui_tree\":false","\"control_actions_available\":false"})
      Check(partial.find(field)!=std::string::npos,"partial scope is explicit");
    auto drift=data;drift.gui_window->tree[0].context=1;
    Check(f::SerializeGuiWindowCommandResultV1("root-qa-1",drift,d).find("\"tree_source_available\":false")!=std::string::npos,"foreign context cannot obtain positive witness");
    drift=data;drift.gui_window->window_found=false;drift.gui_window->tree.clear();
    Check(f::SerializeGuiWindowCommandResultV1("root-qa-1",drift,d).find("\"tree_source_available\":false")!=std::string::npos,"false missing-window shape with exact named match refused");
    drift=data;drift.gui_window->owner_thread_id=0;
    Check(f::SerializeGuiWindowCommandResultV1("root-qa-1",drift,d).find("\"tree_source_available\":false")!=std::string::npos,"owner thread0 cannot obtain positive witness");
#else
    Check(!f::GuiWindowRouteEnabledV1(d)&&partial.find("\"tree_source_available\":false")!=std::string::npos,"defaultOFF root route stays closed");
#endif
    if(argc==3&&std::string_view(argv[1])=="--emit-qa-fixtures") {
      const std::filesystem::path out=argv[2];std::filesystem::create_directories(out);
      Write(out/"request-v1.json",request);Write(out/"partial-SYNTHETIC-DATA.json",partial);
      Write(out/"unavailable-NoGame.json",unavailable);
      Write(out/"wrong-tuple-unavailable.json",f::SerializeGuiWindowCommandResultV1("root-qa-1",data,wrong));
      auto missing=data;missing.main_owner_observed=false;
      Write(out/"missing-owner-unavailable.json",f::SerializeGuiWindowCommandResultV1("root-qa-1",missing,d));
      Write(out/"missing-window-SYNTHETIC-DATA.json",[&](){auto missing=data;missing.gui_window->window_found=false;missing.gui_window->tree.clear();missing.gui_window->top_level[0].name="other_window";return f::SerializeGuiWindowCommandResultV1("root-qa-1",missing,d);}());
      Write(out/"qualifier.json",R"({"scope":"C++ named-window producer SYNTHETIC DATA / NoGame boundary only","actual_Game_MainOwner_root_or_context":"NOT_RUN","addresses":"redacted","no_GUI_actions_or_Full":true})");
    } else Check(argc==1,"expected no args or --emit-qa-fixtures outputdir");
    std::cout<<"PASS current root-index strict request/redacted C++ producer/ON-OFF tuple boundaries; DATA ONLY, LIVE NOT_RUN\n";return 0;
  }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
