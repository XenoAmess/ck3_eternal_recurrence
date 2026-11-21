#include "xar_bridge/ck3_121003_djc_selected_cost26785313_v1.hpp"
#include "ck3_121003_djc_declaration_ui26785313_wire_v1.cpp"
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
using namespace xar::ck3_121003::build26785313;
namespace {
void Require(bool ok,const char*why){if(!ok)throw std::runtime_error(why);}
std::string Request(){
 return std::string(R"({"type":"execute_step","protocol_version":1,"request_id":"djc-cost-synthetic-query","step":")")+kDjcSelectedCostStep267V1+
 R"(","expected_revision":0,"arguments":{},"djc_selected_cost":{"schema":")"+kDjcSelectedCostRequestSchema267V1+
 R"(","game_version":")"+kGameVersion+R"(","executable_sha256":")"+kExecutableSha256+R"(","adapter_id":")"+kAdapterId+
 R"(","backend":")"+kDjcSelectedCostBackend267V1+R"(","action":"query_selected_cost","expected_core":{"date_raw":53144328,"speed":3,"paused":true,"local_player_id":1,"map_ready":true,"has_played_character":true,"played_character_id":-16777215,"played_character_alive":true},"target_character_id":39957,"cb_key":"duchy_de_jure_greatwar","provider_generation":"18446744073709551615","query_sequence":"18446744073709551615"},"core_control_deadline_unix_ms":4102444800000})";
}
std::string Change(std::string text,std::string_view from,std::string_view to){const auto n=text.find(from);Require(n!=std::string::npos,"negative fixture source missing");text.replace(n,from.size(),to);return text;}
DjcSelectedCostResult267V1 Available(){
 DjcSelectedCostRequest267V1 q;Require(ParseDjcSelectedCostRequest267V1(Request(),q),"actual request parse");DjcSelectedCostResult267V1 r;auto&w=r.witness;
 w.action=DjcUiAction267V1::query_ui;w.status=DjcUiStatus267V1::available;w.source_available=w.facts_available=true;w.facts=q.expected;w.provider_generation=q.provider_generation;w.query_sequence=q.query_sequence;w.connection_generation=7;w.ticket_sequence=11;w.pump_epoch=13;w.thread_id=17;
 DjcUiSource267V1 s;s.target_character_id=39957;s.cb_key="duchy_de_jure_greatwar";s.actor_id=-16777215;s.recipient_id=39957;s.additional_role_id=-1;s.interaction_definition_verified=true;s.loaded_interface=4;s.native_confirmation=true;s.native_is_valid=true;s.resident_available=s.named_root_bound=s.window_visible=s.window_enabled=true;
 DjcUiTuple267V1 tuple;tuple.cb_key=s.cb_key;tuple.claimant_character_id=-1;tuple.target_title_ids={2264,7};tuple.extra_configuration_ids={-1,(std::numeric_limits<std::int32_t>::min)(),-1};tuple.source_row_enabled=true;s.selected=tuple;w.source=s;
 r.values.available=true;r.values.native_getter_calls=10;r.values.raw={(std::numeric_limits<std::int64_t>::min)(),-1,0,1,(std::numeric_limits<std::int64_t>::max)()};return r;
}
void Write(const std::filesystem::path&p,std::string_view text){Require(!std::filesystem::exists(p),"immutable fixture exists");std::ofstream f(p,std::ios::binary);f.write(text.data(),static_cast<std::streamsize>(text.size()));Require(static_cast<bool>(f),"fixture write");}
void Emit(const std::filesystem::path&root){
 Require(!std::filesystem::exists(root),"new fixture directory required");Require(std::filesystem::create_directories(root),"create fixture directory");Write(root/"request.json",Request());
 auto r=Available();Write(root/"available-fullrange.json",SerializeDjcSelectedCostResult267V1("djc-cost-synthetic-query",r));
 Write(root/"source-v23-query.json",SerializeDjcUiResult267V1("djc-ui-synthetic-query",r.witness));
 r.witness.source->window_enabled=false;r.witness.source->selected->source_row_enabled=false;Write(root/"available-disabled.json",SerializeDjcSelectedCostResult267V1("djc-cost-synthetic-query",r));
 for(auto status:{DjcUiStatus267V1::unavailable,DjcUiStatus267V1::expired,DjcUiStatus267V1::stale_source,DjcUiStatus267V1::claim_consumed}){
  r=Available();r.witness.status=status;r.witness.source_available=false;r.witness.source.reset();r.values={};r.witness.reason="SYNTHETIC_NoGame_known_refusal";
  const char*name=status==DjcUiStatus267V1::unavailable?"unavailable.json":status==DjcUiStatus267V1::expired?"expired.json":status==DjcUiStatus267V1::stale_source?"stale-source.json":"claim-consumed.json";Write(root/name,SerializeDjcSelectedCostResult267V1("djc-cost-synthetic-query",r));
 }
 r=Available();r.witness.status=DjcUiStatus267V1::indeterminate;r.witness.cleanup_known=false;r.values.cleanup_known=false;r.witness.reason="SYNTHETIC_NoGame_cleanup_unknown";Write(root/"indeterminate-cleanup.json",SerializeDjcSelectedCostResult267V1("djc-cost-synthetic-query",r));
 r=Available();r.values.raw[2].reset();Write(root/"indeterminate-incomplete.json",SerializeDjcSelectedCostResult267V1("djc-cost-synthetic-query",r));
 Write(root/"scope.json",R"({"qualification":"SYNTHETIC_NoGame_DATA_actual_Cpp_serializer","native_owner_executed":false,"native_getters_executed":false,"price_preview_observed":false,"payment_confirmed":false})");
}
void Tests(){
 DjcSelectedCostRequest267V1 q;const auto valid=Request();Require(ParseDjcSelectedCostRequest267V1(valid,q),"strict query accepted");Require(q.provider_generation==(std::numeric_limits<std::uint64_t>::max)()&&q.expected.played_character_id==-16777215,"full signed/uint64 identity");
 for(const auto&bad:{Change(valid,"\"query_sequence\":\"18446744073709551615\"","\"query_sequence\":\"0\""),Change(valid,"\"arguments\":{}","\"arguments\":{\"currency\":\"gold\"}"),Change(valid,"\"action\":\"query_selected_cost\"","\"action\":\"send_ui\""),Change(valid,"\"target_character_id\":39957","\"target_character_id\":-16777215"),Change(valid,"\"query_sequence\":\"18446744073709551615\"","\"query_sequence\":\"18446744073709551615\",\"currency\":\"gold\""),Change(valid,"\"paused\":true","\"paused\":false"),Change(valid,"\"expected_revision\":0","\"expected_revision\":1")})Require(!ParseDjcSelectedCostRequest267V1(bad,q),"unsafe/foreign request refused");
 auto r=Available();auto wire=SerializeDjcSelectedCostResult267V1("test",r);Require(wire.find("\"ok\":true")!=std::string::npos&&wire.find("-9223372036854775808")!=std::string::npos&&wire.find("9223372036854775807")!=std::string::npos,"raw64 no rounding");
 r.witness.source->window_enabled=false;r.witness.source->selected->source_row_enabled=false;Require(SerializeDjcSelectedCostResult267V1("test",r).find("\"ok\":true")!=std::string::npos,"negative permission does not erase readonly price");
 r=Available();r.values.raw[0].reset();wire=SerializeDjcSelectedCostResult267V1("test",r);Require(wire.find("\"status\":\"indeterminate\"")!=std::string::npos&&wire.find("\"costs\":null")!=std::string::npos,"missing price never zero-filled");
 r=Available();r.witness.source->native_confirmation=false;Require(SerializeDjcSelectedCostResult267V1("test",r).find("\"ok\":false")!=std::string::npos,"fixed current declaration source required");
 r=Available();r.witness.ticket_sequence=0;Require(SerializeDjcSelectedCostResult267V1("test",r).find("\"source\":null")!=std::string::npos,"owner witness required");
 r=Available();r.values.native_getter_calls=9;Require(SerializeDjcSelectedCostResult267V1("test",r).find("\"costs\":null")!=std::string::npos,"both full passes required");
 r=Available();r.witness.status=DjcUiStatus267V1::stale_source;r.witness.source_available=false;r.witness.reason="stale";wire=SerializeDjcSelectedCostResult267V1("test",r);Require(wire.find("\"provider_generation\":\"18446744073709551615\"")!=std::string::npos&&wire.find("\"query_sequence\":\"18446744073709551615\"")!=std::string::npos,"early legal refusal preserves original lease");
}
}
int main(int argc,char**argv){try{
 if(argc==3&&std::string_view(argv[1])=="--validate-request"){std::ifstream f(argv[2],std::ios::binary);Require(static_cast<bool>(f),"request input");std::string text((std::istreambuf_iterator<char>(f)),{});DjcSelectedCostRequest267V1 q;const bool good=ParseDjcSelectedCostRequest267V1(text,q);std::cout<<(good?"VALID\n":"INVALID\n");return good?0:2;}
 Tests();if(argc==3&&std::string_view(argv[1])=="--emit-selected-cost-fixtures")Emit(argv[2]);else Require(argc==1,"unknown test mode");std::cout<<"SelectedCost strict readonly wire PASS; SYNTHETIC_NoGame only\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
