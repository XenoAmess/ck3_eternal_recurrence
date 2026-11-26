#include "xar_bridge/ck3_121003_lyd26785313_v1.hpp"
#include "xar_bridge/ck3_121003_full_profile111.hpp"
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <stdexcept>
using namespace xar::ck3_121003::build26785313;
namespace {
void Require(bool v,const char*why){if(!v)throw std::runtime_error(why);}
using A=LydAction267V1;using S=LydStatus267V1;
auto Core(){xar::ck3_1210::CoreSnapshotPrefix p;p.clock.date_raw=53144328;p.clock.speed=1;p.clock.paused=true;p.local_player_id=0;p.map_ready=true;p.has_played_character=true;p.played_character_id=-16777215;p.played_character_alive=true;return p;}
auto Request(A action){LydRequest267V1 q;q.action=action;q.expected=Core();q.deadline_unix_ms=1899999999999ULL;if(!LydQueryAction267V1(action))q.provider_generation=q.query_sequence=(std::numeric_limits<std::uint64_t>::max)();const std::string id="lyd-native-real-producer";std::copy(id.begin(),id.end(),q.request_id.begin());q.request_id_size=static_cast<std::uint8_t>(id.size());return q;}
std::string Q(std::string_view s){return '"'+std::string(s)+'"';}
template<class T,std::size_t N>std::string Enum(const std::optional<T>&v,const std::array<std::string_view,N>&names){return v?Q(names[static_cast<std::size_t>(*v)]):"null";}
std::string Encode(const LydRequest267V1&q,std::string_view adapter=kAdapterId){return "{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":"+Q(q.id())+",\"step\":"+Q(kLydSteps267V1[static_cast<std::size_t>(q.action)])+",\"expected_revision\":0,\"arguments\":{},\"lyd\":{\"schema\":"+Q(kLydRequestSchema267V1)+",\"game_version\":"+Q(kGameVersion)+",\"executable_sha256\":"+Q(kExecutableSha256)+",\"adapter_id\":"+Q(adapter)+",\"backend\":"+Q(kLydBackend267V1)+",\"action\":"+Q(kLydActionNames267V1[static_cast<std::size_t>(q.action)])+",\"expected_core\":{\"date_raw\":53144328,\"speed\":1,\"paused\":true,\"local_player_id\":0,\"map_ready\":true,\"has_played_character\":true,\"played_character_id\":-16777215,\"played_character_alive\":true},\"provider_generation\":"+Q(std::to_string(q.provider_generation))+",\"query_sequence\":"+Q(std::to_string(q.query_sequence))+",\"decision_key\":"+Enum(q.decision,kLydDecisionKeys267V1)+",\"personal_key\":"+Enum(q.personal,kLydPersonalKeys267V1)+",\"event_role\":"+Enum(q.event_role,kLydEventRoleNames267V1)+",\"instance_id\":"+(q.instance_id?std::to_string(*q.instance_id):"null")+",\"choice_token\":"+Q(q.choice_token)+"},\"core_control_deadline_unix_ms\":"+std::to_string(q.deadline_unix_ms)+"}";}
auto Decision(bool hidden=false,bool selected=false){LydSource267V1 v;v.kind=LydKind267V1::decisions;v.decisions.emplace();auto&s=*v.decisions;s.list_found=s.list_enabled=s.detail_found=true;s.list_visible=!hidden;s.open_list_admissible=hidden;
 if(!hidden){s.complete_model_census=true;s.groups_count=1;s.total_model_rows=5;for(unsigned n=0;n<5;++n)s.rows.push_back({static_cast<LydDecision267V1>(n),!(selected&&n==0),selected&&n==0});}
 if(selected){s.detail_visible=s.detail_enabled=true;s.selected_decision=LydDecision267V1::entry;s.native_can_confirm=true;s.confirm_admissible=true;s.widget_state=0;}return v;}
auto Events(){LydSource267V1 v;v.kind=LydKind267V1::events;v.events.emplace();v.events->census_complete=true;v.events->named_root_count=1;LydEventRow267V1 row;row.instance_id=7;row.recipient_character_id=Core().played_character_id;row.authored_option_count=2;row.definition_key="lyd.1002";row.opening="礼乐";row.description="\x15" "Y原样文本\x15!";row.named_root_bound=row.window_visible=row.window_enabled=true;row.options.push_back({0,true,"支付","",std::string("lyd_play_ritual_music_option_0"),LydEventRole267V1::ritual_music_pay});row.options.push_back({1,true,"取消","",std::string("lyd_play_cancel"),LydEventRole267V1::ritual_music_cancel});v.events->events.push_back(row);return v;}
auto Personal(bool modal=false){LydSource267V1 v;v.kind=LydKind267V1::personal;v.personal.emplace();auto&s=*v.personal;s.resident_available=s.named_root_bound=s.window_visible=s.window_enabled=s.actor_bound=s.is_adding=s.model_materialized=s.slots_complete=s.groups_complete=s.empty_slot_found=s.actual_personal_complete=true;s.native_window_visible=true;s.slot_count=1;s.group_count=1;s.slots.push_back({true,false,{}});s.rows.push_back({1,std::string(kLydPersonalKeys267V1[0]),"lyd.native.row.a",true,false,!modal,true});s.rows.push_back({1,std::string(kLydPersonalKeys267V1[1]),"lyd.native.row.b",true,false,!modal,true});if(modal){s.blocked_by_visible_modal=true;s.add_modal={true,true,true,false,LydPersonal267V1::reverent_heaven,true,true};}return v;}
auto Result(A a,const LydSource267V1&source,S status=S::available){LydResult267V1 r;r.action=a;r.status=status;r.facts_available=r.source_available=true;r.facts=Core();r.source=source;r.connection_generation=r.ticket_sequence=r.pump_epoch=r.provider_generation=r.query_sequence=(std::numeric_limits<std::uint64_t>::max)();r.thread_id=73;if(!LydQueryAction267V1(a)){r.effect_attempted=r.native_returned=true;r.claim_sequence=1;}return r;}
std::string RendererRequest(LydRequest267V1 q) {
 std::string request=Encode(q,xar::ck3_121003::full111::kAdapterId);
 const auto old_step=kLydSteps267V1[static_cast<std::size_t>(q.action)];
 request.replace(request.find(old_step),old_step.size(),kFull111EventRendererStep267V1);
 return request;
}
LydResult267V1 RendererResult() {
 auto r=Result(A::query_events,Events());
 r.instance_id=7;
 r.renderer=Full111EventRendererSource267V1{7,Core().played_character_id,6,"bookmark.1070",
  {{4,false,false,true,"Native hidden","Stock" " disabled reason"},
   {1,true,true,false,"Native visible",""}}};
 return r;
}
void RendererTests() {
 using xar::ck3_121003::full111::kAdapterId;
 auto q=Request(A::query_events);
 const auto old=Encode(q,kAdapterId);
 LydRequest267V1 parsed;
 Require(ParseFull111LydEventRequest267V1(old,parsed)&&!ParseFull111EventRendererRequest267V1(old,parsed),
     "old Full111 step was reinterpreted as a renderer read");
 Require(!ParseFull111EventRendererRequest267V1(RendererRequest(q),parsed),"renderer query skipped a target event");
 q.instance_id=7;
 const auto request=RendererRequest(q);
 Require(ParseFull111EventRendererRequest267V1(request,parsed)&&parsed.instance_id==7&&
     !ParseFull111LydEventRequest267V1(request,parsed)&&!ParseLydRequest267V1(request,parsed),
     "exact renderer target was accepted by the wrong profile or step");
 Require(!ParseFull111LydEventRequest267V1(Encode(q,kAdapterId),parsed),"old census accepted renderer target form");
 q.instance_id=0;
 Require(!ParseFull111EventRendererRequest267V1(RendererRequest(q),parsed),"zero renderer target accepted");
 q.instance_id=7;q.query_sequence=1;
 Require(!ParseFull111EventRendererRequest267V1(RendererRequest(q),parsed),"renderer read accepted a lease");
 q=Request(A::choose_known_event_option);q.event_role=LydEventRole267V1::ritual_music_pay;q.instance_id=7;
 Require(!ParseFull111EventRendererRequest267V1(RendererRequest(q),parsed),"renderer read accepted a choice action");
 auto r=RendererResult();
 const auto wire=SerializeFull111EventRendererResult267V1(q.id(),r);
 const auto hidden=wire.find(R"("authored_option_index":4,"native_can_select":false,"widget_visible":false,"widget_enabled":true)");
 const auto disabled=wire.find(R"("authored_option_index":1,"native_can_select":true,"widget_visible":true,"widget_enabled":false)");
 Require(wire.find(R"("ok":true)")!=std::string::npos&&hidden!=std::string::npos&&disabled!=std::string::npos&&hidden<disabled&&
     wire.find(R"("claim_sequence")")==std::string::npos,"renderer response lost stock order or emitted a claim");
 r.renderer->recipient_character_id+=1;
 Require(SerializeFull111EventRendererResult267V1(q.id(),r).find(R"("source":null)")!=std::string::npos,
     "renderer passed a different event recipient");
 r=RendererResult();r.renderer->options[1].authored_option_index=4;
 Require(SerializeFull111EventRendererResult267V1(q.id(),r).find(R"("source":null)")!=std::string::npos,
     "duplicate renderer option identity was accepted");
}
void Full111Tests(){
 namespace full111=xar::ck3_121003::full111;
 auto q=Request(A::query_events);
 LydRequest267V1 parsed;
 const auto wire=Encode(q,full111::kAdapterId);
 Require(ParseFull111LydEventRequest267V1(wire,parsed)&&parsed.action==A::query_events,"Full111 fixed read was rejected");
 Require(!ParseLydRequest267V1(wire,parsed),"old Core route accepted Full111 identity");
 Require(!ParseFull111LydEventRequest267V1(Encode(q),parsed)&&parsed.id().empty(),"Full111 accepted old identity");
 q=Request(A::choose_known_event_option);q.event_role=LydEventRole267V1::ritual_music_pay;q.instance_id=7;
 Require(!ParseFull111LydEventRequest267V1(Encode(q,full111::kAdapterId),parsed),"Full111 accepted event choice");
 auto r=Result(A::query_events,Events());
 const auto read=SerializeFull111LydEventResult267V1(q.id(),r);
 Require(read.find("\"ok\":true")!=std::string::npos&&read.find(full111::kAdapterId)!=std::string::npos&&
    read.find("\"permitted_role\":null")!=std::string::npos&&read.find("\"source_bound_option_key\":null")!=std::string::npos&&
    read.find("lyd_play_ritual_music_option_0")==std::string::npos,"Full111 query leaked writer metadata or wrong identity");
 r.status=S::expired;
 Require(SerializeFull111LydEventResult267V1(q.id(),r).find("\"source\":null")!=std::string::npos,"expired Full111 exposed event data");
 r=Result(A::choose_known_event_option,Events(),S::confirmation_dispatched);
 r.event_role=LydEventRole267V1::ritual_music_pay;r.instance_id=7;
 Require(SerializeFull111LydEventResult267V1(q.id(),r).find("\"ok\":false")!=std::string::npos,"Full111 serialized an accepted effect");
 auto empty=Events();empty.events->events.clear();empty.events->named_root_count=0;
 r=Result(A::query_events,empty);
 const auto unavailable=SerializeFull111LydEventResult267V1(q.id(),r);
 Require(unavailable.find("\"ok\":false")!=std::string::npos&&unavailable.find("\"source\":null")!=std::string::npos,
    "empty ordinary census got credit for proving an empty runtime queue");
}
void Tests(){
 Full111Tests();
 for(unsigned n=0;n<13;++n){auto q=Request(static_cast<A>(n));if(n==2||n==3)q.decision=LydDecision267V1::entry;if(n==5){q.event_role=LydEventRole267V1::ritual_music_pay;q.instance_id=7;}if(n>=6&&n<=11)q.personal=LydPersonal267V1::reverent_heaven;if(n==9)q.choice_token="lyd.native.row.a";LydRequest267V1 parsed;const auto text=Encode(q);Require(LydRequestShape267V1(q)&&ParseLydRequest267V1(text,parsed),"actual request roundtrip");auto bad=text;bad.insert(1,"\"arguments\":{},");Require(!ParseLydRequest267V1(bad,parsed),"duplicate outer accepted");bad=text;bad.insert(bad.find("\"schema\""),"\"action\":\"query_events\",");Require(!ParseLydRequest267V1(bad,parsed),"duplicate claim accepted");}
 auto q=Request(A::confirm_decision);q.decision=LydDecision267V1::begin_readonly;Require(!LydRequestShape267V1(q),"begin action allowed");auto d=Decision(false,true);d.decisions->selected_decision=LydDecision267V1::begin_readonly;for(auto&row:d.decisions->rows){row.is_selected=row.decision==LydDecision267V1::begin_readonly;row.can_open_detail=!row.is_selected;}Require(!LydPublicSourceShape267V1(d),"begin NativeCan made confirmation admissible");
 auto personal=Personal();q=Request(A::select_personal_candidate);q.personal=LydPersonal267V1::reverent_heaven;q.choice_token="lyd.native.row.a";Require(LydPublicAdmissible267V1(personal,q),"real bound personal unavailable");personal.personal->rows[0].native_can_pick=false;personal.personal->rows[0].select_admissible=false;Require(LydPublicSourceShape267V1(personal)&&!LydPublicAdmissible267V1(personal,q),"negative Can not retained or authorized");personal=Personal();personal.personal->empty_slot_found=false;Require(!LydPublicSourceShape267V1(personal),"invented free-slot mismatch accepted");personal=Personal();personal.personal->rows[1].choice_token=personal.personal->rows[0].choice_token;Require(!LydPublicSourceShape267V1(personal),"duplicate opaque rows accepted");personal=Personal();personal.personal->quoted_currency_costs.emplace();Require(!LydPublicSourceShape267V1(personal),"unknown quote synthesized as zero");
 personal=Personal();personal.personal->rows[0].definition_key="unreviewed_personal";personal.personal->rows[0].select_admissible=false;Require(!LydPublicSourceShape267V1(personal),"unqualified unrelated NativeCan supplied");LydSource267V1 unsupported;unsupported.kind=LydKind267V1::readback;unsupported.readback.emplace();unsupported.readback->resources.emplace();unsupported.readback->legitimacy_raw=0;Require(!LydPublicSourceShape267V1(unsupported),"unqualified legitimacy invented zero");
 auto events=Events();auto&row=events.events->events[0];row.definition_key="lyd.1032";row.authored_option_count=3;row.options[0].authored_option_index=1;row.options[0].source_bound_option_key="lyd_play_knowing_acting_support_option_1";row.options[0].permitted_role=LydEventRole267V1::knowing_acting_inquiry;Require(!LydPublicSourceShape267V1(events),"forbidden practice disguised as inquiry");
 auto r=Result(A::select_personal_candidate,Personal(),S::selection_dispatched);r.personal=LydPersonal267V1::reverent_heaven;Require(SerializeLydResult267V1("test",r).find("\"ok\":true")!=std::string::npos,"dispatch actual shape invalid");r.native_handled=true;Require(SerializeLydResult267V1("test",r).find("\"ok\":false")!=std::string::npos,"void action invented handled bool");r.native_handled=false;r.cleanup_known=false;const auto bad=SerializeLydResult267V1("test",r);Require(bad.find("\"ok\":false")!=std::string::npos&&bad.find("\"source\":null")!=std::string::npos,"cleanup unknown retained authority");
}
void Write(const std::filesystem::path&root,std::string_view name,std::string_view bytes){const auto p=root/std::string(name);Require(!std::filesystem::exists(p),"genuine file already exists");std::ofstream out(p,std::ios::binary);Require(bool(out),"output unavailable");out.write(bytes.data(),static_cast<std::streamsize>(bytes.size()));Require(bool(out),"output incomplete");}
void Emit(const std::filesystem::path&root){Require(std::filesystem::is_directory(root),"genuine output directory missing");const auto emit=[&](std::string_view name,const LydResult267V1&r){Write(root,name,SerializeLydResult267V1("lyd-native-real-producer",r));};
 emit("decisions-query.json",Result(A::query_decisions,Decision()));auto r=Result(A::open_detail,Decision(),S::selection_dispatched);r.decision=LydDecision267V1::entry;emit("decision-detail.json",r);r=Result(A::confirm_decision,Decision(false,true),S::confirmation_dispatched);r.decision=LydDecision267V1::entry;emit("decision-confirm.json",r);emit("decisions-hidden.json",Result(A::query_decisions,Decision(true)));r=Result(A::open_list,Decision(true),S::navigation_dispatched);r.native_handled=false;emit("decisions-open-list.json",r);
 auto renderer_query=Request(A::query_events);renderer_query.instance_id=7;
 Write(root,"full111-ordinary-event-renderer.request.json",RendererRequest(renderer_query));
 Write(root,"full111-ordinary-event-renderer.json",SerializeFull111EventRendererResult267V1(
     renderer_query.id(),RendererResult()));
 auto renderer_unavailable=RendererResult();
 renderer_unavailable.status=S::unavailable;
 renderer_unavailable.reason="current111_renderer_complete_widget_context_unavailable";
 renderer_unavailable.source_available=false;
 renderer_unavailable.renderer.reset();
 Write(root,"full111-ordinary-event-renderer-unavailable.json",SerializeFull111EventRendererResult267V1(
     renderer_query.id(),renderer_unavailable));
 Write(root,"full111-ordinary-event-query.request.json",Encode(Request(A::query_events),xar::ck3_121003::full111::kAdapterId));
 Write(root,"full111-ordinary-event-query.json",SerializeFull111LydEventResult267V1("lyd-native-real-producer",Result(A::query_events,Events())));
 auto queue_unavailable=Result(A::query_events,Events(),S::unavailable);
 queue_unavailable.source_available=false;queue_unavailable.source.reset();
 queue_unavailable.provider_generation=queue_unavailable.query_sequence=0;
 queue_unavailable.reason="current111_ordinary_events_do_not_cover_runtime_queue";
 Write(root,"full111-runtime-queue-unavailable.json",SerializeFull111LydEventResult267V1("lyd-native-real-producer",queue_unavailable));
 emit("events-query.json",Result(A::query_events,Events()));r=Result(A::choose_known_event_option,Events(),S::confirmation_dispatched);r.event_role=LydEventRole267V1::ritual_music_pay;r.instance_id=7;emit("event-choose-pay.json",r);LydSource267V1 empty;empty.kind=LydKind267V1::events;empty.events=LydEventSource267V1{true,0,{}};emit("events-empty.json",Result(A::query_events,empty));
 r=Result(A::query_personal,Personal());r.personal=LydPersonal267V1::reverent_heaven;emit("personal-query.json",r);r=Result(A::select_personal_candidate,Personal(),S::selection_dispatched);r.personal=LydPersonal267V1::reverent_heaven;emit("personal-select.json",r);r=Result(A::query_add_confirmation,Personal(true));r.personal=LydPersonal267V1::reverent_heaven;emit("add-modal-query.json",r);r=Result(A::confirm_personal_add,Personal(true),S::confirmation_dispatched);r.personal=LydPersonal267V1::reverent_heaven;emit("add-modal-confirm.json",r);
 LydSource267V1 resources;resources.kind=LydKind267V1::readback;resources.readback.emplace();resources.readback->resources=RawResources{-9223372036854775807LL,9223372036854775807LL,-20000000,12};emit("readback-resources.json",Result(A::query_readback,resources));auto negative=Personal();negative.personal->rows[0].native_can_pick=false;negative.personal->rows[0].select_admissible=false;r=Result(A::query_personal,negative);r.personal=LydPersonal267V1::reverent_heaven;emit("personal-can-false.json",r);
 r=Result(A::select_personal_candidate,Personal(),S::stale_source);r.personal=LydPersonal267V1::reverent_heaven;r.effect_attempted=r.native_returned=false;r.reason="lyd_original_source_changed";emit("select-refused-spent-claim.json",r);r.source_available=false;r.source.reset();r.status=S::expired;r.reason="lyd_original_deadline_expired";emit("select-expired.json",r);r.status=S::indeterminate;r.cleanup_known=false;r.reason="lyd_actual_native_completion_unknown";emit("select-indeterminate.json",r);
 for(const auto action:{A::query_personal,A::select_personal_candidate}){auto q=Request(action);q.personal=LydPersonal267V1::reverent_heaven;if(action==A::select_personal_candidate)q.choice_token="lyd.native.row.a";Write(root,action==A::query_personal?"query.request.json":"select.request.json",Encode(q));}
}
}
int main(int argc,char**argv){try{
 const std::string_view operation=argc==3?argv[1]:"";
 if(operation=="--validate-request"||operation=="--validate-full111-request"||
     operation=="--validate-full111-renderer-request"){
  std::ifstream in(argv[2],std::ios::binary);Require(bool(in),"request unavailable");
  const std::string bytes((std::istreambuf_iterator<char>(in)),{});LydRequest267V1 q;
  const bool accepted=operation=="--validate-full111-renderer-request"
    ?ParseFull111EventRendererRequest267V1(bytes,q):operation=="--validate-full111-request"
    ?ParseFull111LydEventRequest267V1(bytes,q):ParseLydRequest267V1(bytes,q);
  Require(accepted,"actual request parser refused");
  std::cout<<"PASS actual LYD request parser\n";return 0;
 }
 Tests();RendererTests();
 if(operation=="--emit")Emit(argv[2]);else Require(argc==1,"unsupported arguments");
 std::cout<<"PASS finite LYD actual parser/serializer and meaningful source/permission negatives; no Game\n";
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
