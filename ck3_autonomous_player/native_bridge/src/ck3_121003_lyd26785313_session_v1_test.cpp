// Actual owner and wire translation units, with only owner-frame/Raw native dependencies supplied as explicit NoGame DATA fixtures.
// This exercises process-private query/claim/connection state; it grants no Raw/Native/live qualification.
#include "ck3_121003_lyd26785313_wire_v1.cpp"
#include "ck3_121003_lyd26785313_owner_v1.cpp"
#include "ck3_121003_full111_event_read_v1.hpp"
#include <stdexcept>
#include <cstring>
#include <filesystem>
#include <fstream>
using namespace xar::ck3_121003::build26785313;
namespace fixture {
unsigned observations=0,effects=0;bool uncertain=false,full_read_available=true;
#if defined(XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_OPTION_V2) && XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_OPTION_V2
bool option_visible=true, option_enabled=true, option_native=true, option_changed=false, queue_available=true, still_pending=false;
int foreground=7;
#endif
auto core(){xar::ck3_1210::CoreSnapshotPrefix p;p.clock.date_raw=53144328;p.clock.speed=1;p.clock.paused=true;p.local_player_id=0;p.map_ready=p.has_played_character=p.played_character_alive=true;p.played_character_id=-16777215;return p;}
auto source(bool modal){LydSource267V1 v;v.kind=LydKind267V1::personal;v.personal.emplace();auto&s=*v.personal;s.resident_available=s.named_root_bound=s.window_visible=s.window_enabled=s.actor_bound=s.is_adding=s.model_materialized=s.slots_complete=s.groups_complete=s.empty_slot_found=s.actual_personal_complete=true;s.native_window_visible=true;s.slot_count=1;s.group_count=1;s.slots.push_back({true,false,{}});s.rows.push_back({1,std::string(kLydPersonalKeys267V1[0]),"lyd.private.fixture",true,false,!modal,true});if(modal){s.blocked_by_visible_modal=true;s.add_modal={true,true,true,false,LydPersonal267V1::reverent_heaven,true,true};}return v;}
auto ordinary(){
 LydSource267V1 value;value.kind=LydKind267V1::events;
 value.events=LydEventSource267V1{true,1,{}};
 LydEventRow267V1 row;row.instance_id=1;row.recipient_character_id=core().played_character_id;
 row.definition_key="bookmark.1070";row.named_root_bound=row.window_visible=row.window_enabled=true;
 value.events->events.push_back(std::move(row));return value;
}
void require(bool value,const char*why){if(!value)throw std::runtime_error(why);}
}
namespace xar::ck3_121003::build26785313 {
namespace lyd_common {
template<class T>bool At(std::uintptr_t address,std::size_t offset,T&value)noexcept{
 if(!address)return false;
 std::memcpy(&value,reinterpret_cast<const void*>(address+offset),sizeof(value));return true;
}
}
#include "ck3_121003_lyd26785313_full111_queue_v1.inc"
ReadonlyBindings BindReadonlyImage(std::uintptr_t,std::string_view)noexcept{return{};}
bool ReadLydFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,LydKind267V1 kind,std::uint64_t wall,std::uint64_t,LydFrame267V1&out,std::string&)noexcept{out.facts_verified=true;out.core=fixture::core();out.scene.kind=kind;out.scene.wall_deadline=wall;out.scene.global=0x1000;out.scene.jomini=0x2000;out.scene.context=0x3000;return true;}
bool ReadLydRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const LydScene267V1&,std::uint64_t,const LydRequest267V1&q,const std::optional<LydSelectionAssociation267V1>&,LydRaw267V1&out,std::string&)noexcept{++fixture::observations;out.source=fixture::source(q.action==LydAction267V1::query_add_confirmation||q.action==LydAction267V1::confirm_personal_add);out.actor=0x4000;out.resident=0x5000;out.root=0x6000;out.choices.push_back({std::string(kLydPersonalKeys267V1[0]),"lyd.private.fixture",0x7000,true});return true;}
bool ReadFull111LydEventRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&expected,
 const LydScene267V1&,std::uint64_t,const LydRequest267V1&request,std::uintptr_t owner_game,
 LydRaw267V1&out,std::string&reason)noexcept{
 ++fixture::observations;
 if(!fixture::full_read_available||!owner_game||!expected.clock.paused||
     request.action!=LydAction267V1::query_events){
  reason="current111_ordinary_events_do_not_cover_runtime_queue";return false;
 }
 out.source=fixture::ordinary();return true;
}
bool ReadFull111EventRendererOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,
 const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,
 const LydFrame267V1&,const LydRequest267V1&request,std::uint64_t,Full111EventRendererSource267V1&out,
 bool &entered,bool &cleanup,std::string&reason,[[maybe_unused]] Full111EventRendererMaterial267V2 *material)noexcept{
 ++fixture::observations;entered=false;cleanup=true;
#if defined(XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_OPTION_V2) && XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_OPTION_V2
 if(material&&request.instance_id==fixture::foreground){
  out={fixture::foreground,fixture::core().played_character_id,6,"bookmark.1070",{{4,fixture::option_native,fixture::option_visible,fixture::option_enabled,"Bound",""}}};
  material->root=0x44;material->runtime=0x45;material->definition=0x46;
  material->options={{0x50,fixture::option_changed?std::uintptr_t{0x60}:std::uintptr_t{0x51},0x52,4}};
  return true;
 }
#endif
 if(request.instance_id!=1){reason="current111_renderer_expected_foreground_changed";return false;}
 out={1,fixture::core().played_character_id,6,"bookmark.1070",{{4,true,true,false,"Visible",""}}};
 return true;
}
#if defined(XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_OPTION_V2) && XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_OPTION_V2
namespace lyd_common {
bool Text(std::uintptr_t address, std::size_t, std::string &out, bool) {
 out.assign(reinterpret_cast<const char *>(address));return true;
}
}
namespace lyd_raw {
bool NativeSelect(std::uintptr_t, std::uintptr_t, bool &entered, bool &clean) noexcept {
 entered=true;clean=!fixture::uncertain;++fixture::effects;return clean;
}
}
#include "ck3_121003_full111_event_option_raw_v2.inc"
bool ReadFull111EventQueueOnOwner267V2(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,
 const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,
 const Full111EventOptionRequest267V2 &request,std::uint64_t,ck3_1210::CoreSnapshotPrefix &actual,Full111EventQueue267V2 &queue) noexcept {
 if(!fixture::queue_available) return false;
 actual=fixture::core();queue=fixture::still_pending?Full111EventQueue267V2{{8,request.target.instance_id},true}:Full111EventQueue267V2{{},false};return true;
}
LydRawCall267V1 SelectFull111RenderedOptionOnOwner267V2(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,
 const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,const LydFrame267V1&,
 const Full111EventOptionRequest267V2&,std::uint64_t,const Full111EventRendererMaterial267V2::Option &option,
 const Full111EventRendererMaterial267V2&) noexcept {
 ReadonlyBindings bindings;bindings.exact_image_admitted=true;
 return option.model==0x51?CallFull111StockOption267V2(bindings,option.model):LydRawCall267V1{};
}
#endif
void TokenizeLydRaw267V1(LydRaw267V1&,std::uint64_t,std::uint64_t){}
bool SameLydRawForLease267V1(const LydRaw267V1&a,const LydRaw267V1&b)noexcept{return a==b;}
bool LydRawAdmissible267V1(const LydRaw267V1&r,const LydRequest267V1&q)noexcept{return LydPublicAdmissible267V1(r.source,q);}
LydRawCall267V1 CallLydRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const LydScene267V1&,std::uint64_t,const LydRequest267V1&,const std::optional<LydSelectionAssociation267V1>&,const LydRaw267V1&)noexcept{++fixture::effects;return{fixture::uncertain?LydRawCallStatus267V1::indeterminate:LydRawCallStatus267V1::returned,true,false,!fixture::uncertain};}
}
namespace {
void VerifyQueueWitness(){
 using namespace fixture;
 constexpr std::size_t queue=0x44BC0+0x1F18;
 std::array<std::byte,0xA8> game{};
 std::vector<std::byte> data(queue+16);
 std::array<std::uintptr_t,2> queued{0x1000,0x2000};
 void* game_slot=game.data();
 const auto game_address=reinterpret_cast<std::uintptr_t>(game_slot);
 const auto put=[](auto&buffer,std::size_t offset,auto value){
  std::memcpy(buffer.data()+offset,&value,sizeof(value));
 };
 put(game,0xA0,data.data());put(data,queue,queued.data());put(data,queue+8,std::int32_t{2});
 put(data,queue+12,std::int32_t{1});
 ReadonlyBindings bindings;bindings.exact_image_admitted=true;bindings.core.game_state_slot=&game_slot;
 LydRaw267V1 raw;raw.source=ordinary();raw.manager_census.game=game_address;
 raw.event_rows.emplace_back();raw.event_rows.front().material.game=game_address;
 raw.event_rows.front().runtime=queued.front();raw.event_rows.front().instance_id=1;
 full111_event_queue::Sample first{},later{};
 require(full111_event_queue::Capture(bindings,game_address,first)&&
    full111_event_queue::Matches(first,game_address,core().played_character_id,raw),
    "same living ordinary event covers the complete runtime queue");
 require(!full111_event_queue::Capture(bindings,game_address+1,later),"different stamped world accepted");
 put(data,queue+12,std::int32_t{2});
 require(full111_event_queue::Capture(bindings,game_address,later)&&later!=first&&
    !full111_event_queue::Matches(later,game_address,core().played_character_id,raw),
    "unidentified letter/fullscreen runtime row was dropped");
 put(data,queue+12,std::int32_t{1});
 queued.front()=0x3000;
 require(full111_event_queue::Capture(bindings,game_address,later)&&later!=first&&
    !full111_event_queue::Matches(later,game_address,core().played_character_id,raw),
    "unchanged count accepted wrong runtime event");
 raw.event_rows.front().runtime=queued.front();
 require(!full111_event_queue::Matches(later,game_address,core().played_character_id+1,raw),
    "another recipient became the current player");
 put(data,queue+12,std::int32_t{0});
 require(!full111_event_queue::Capture(bindings,game_address,later),"empty queue became an event proof");
}
}
#if defined(XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_OPTION_V2) && XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_OPTION_V2
#include "ck3_121003_full111_event_option_test_v2.inc"
#endif
int main([[maybe_unused]] int argc,[[maybe_unused]] char **argv){using namespace fixture;
#if defined(XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_OPTION_V2) && XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_OPTION_V2
 if(argc==3&&std::string_view(argv[1])=="--emit-option-wire") { EmitOptionWire(argv[2]);return 0; }
 if(argc==3&&std::string_view(argv[1])=="--validate-option-request") return ValidateOptionWire(argv[2]);
 VerifyStockOptionOwner();VerifyStockOptionRefusals();VerifyStockRuntimeQueue();effects=0;uncertain=false;
#endif
 VerifyQueueWitness();LydSession267V1 session;auto mailbox=std::make_unique<xar::ck3_11906::MainThreadQueryMailboxV1>();mailbox->offline_fixture=false;mailbox->permitted_executor_quinquevigintary=&ExecuteLydOnOwner267V1;xar::ck3_11906::MainThreadExecutionStampV1 stamp;stamp.thread_id=7;stamp.pump_epoch=11;stamp.paused=true;unsigned ids=0;const auto deadline=Wall()+60000;
 const auto request=[&](LydAction267V1 action,std::uint64_t connection){LydContext267V1 q;q.session=&session;q.mailbox=mailbox.get();q.connection_generation=connection;q.ticket.sequence=17;q.request.action=action;q.request.expected=core();q.request.personal=LydPersonal267V1::reverent_heaven;q.request.deadline_unix_ms=deadline;const auto id="fixture-"+std::to_string(++ids);std::copy(id.begin(),id.end(),q.request.request_id.begin());q.request.request_id_size=static_cast<std::uint8_t>(id.size());ArmLydDeadline267V1(q);return q;};
 stamp.game_state=0x4000;
 auto observed_event=request(LydAction267V1::query_events,21);
 observed_event.request.personal.reset();observed_event.full111_ordinary_events_only=true;
 require(ExecuteLydInner267V1(observed_event,stamp)&&observed_event.result.status==LydStatus267V1::available&&
    observed_event.result.source_available&&effects==0&&!observed_event.result.claim_sequence,
    "Full111 ordinary read produced no identity or entered effects");
 auto forbidden=request(LydAction267V1::choose_known_event_option,21);
 forbidden.request.personal.reset();forbidden.full111_ordinary_events_only=true;
 forbidden.request.provider_generation=observed_event.result.provider_generation;
 forbidden.request.query_sequence=observed_event.result.query_sequence;
 forbidden.request.event_role=LydEventRole267V1::welcome_continue;forbidden.request.instance_id=1;
 require(ExecuteLydInner267V1(forbidden,stamp)&&forbidden.result.status==LydStatus267V1::unavailable&&
    !forbidden.result.source_available&&effects==0,"Full111 owner accepted an event choice");
 forbidden.full111_ordinary_events_only=false;
 require(ExecuteLydInner267V1(forbidden,stamp)&&forbidden.result.status==LydStatus267V1::stale_source&&effects==0,
    "Full111 read unexpectedly retained a writable LYD lease");
 full_read_available=false;
 require(ExecuteLydInner267V1(observed_event,stamp)&&observed_event.result.status==LydStatus267V1::unavailable&&
    !observed_event.result.source_available&&effects==0,"unsupported queue emitted Full111 source DATA");
 full_read_available=true;
 auto renderer=request(LydAction267V1::query_events,21);
 renderer.request.personal.reset();renderer.request.instance_id=1;
 renderer.full111_ordinary_events_only=renderer.full111_event_renderer=true;
 require(ExecuteLydInner267V1(renderer,stamp)&&renderer.result.status==LydStatus267V1::available&&
    renderer.result.renderer&&renderer.result.renderer->options.front().authored_option_index==4&&
    !renderer.result.claim_sequence&&effects==0,"exact owner renderer did not publish independent read-only data");
 renderer.request.instance_id=2;
 require(ExecuteLydInner267V1(renderer,stamp)&&renderer.result.status==LydStatus267V1::unavailable&&
    !renderer.result.renderer&&effects==0,"renderer query acquired different standing instance");
 renderer.request.instance_id=1;renderer.full111_ordinary_events_only=false;
 require(ExecuteLydInner267V1(renderer,stamp)&&renderer.result.status==LydStatus267V1::unavailable&&
    !renderer.result.renderer&&effects==0,"core owner accepted Full111 renderer");
 auto query=request(LydAction267V1::query_personal,21);require(ExecuteLydInner267V1(query,stamp)&&query.result.status==LydStatus267V1::available,"actual owner query fixture failed");
 auto select=request(LydAction267V1::select_personal_candidate,21);select.request.provider_generation=query.result.provider_generation;select.request.query_sequence=query.result.query_sequence;select.request.choice_token="lyd.private.fixture";require(ExecuteLydInner267V1(select,stamp)&&select.result.status==LydStatus267V1::selection_dispatched&&effects==1,"actual owner select custody failed");
 auto wrong=request(LydAction267V1::query_add_confirmation,22);const auto before=observations;require(ExecuteLydInner267V1(wrong,stamp)&&wrong.result.status==LydStatus267V1::stale_source&&!wrong.result.source_available&&!wrong.result.effect_attempted&&!wrong.result.claim_sequence&&observations==before&&effects==1,"new connection acquired pending selection");
 auto add=request(LydAction267V1::query_add_confirmation,21);require(ExecuteLydInner267V1(add,stamp)&&add.result.status==LydStatus267V1::available&&effects==1,"original connection lost valid pending source");
 auto confirm=request(LydAction267V1::confirm_personal_add,21);confirm.request.provider_generation=add.result.provider_generation;confirm.request.query_sequence=add.result.query_sequence;require(ExecuteLydInner267V1(confirm,stamp)&&confirm.result.status==LydStatus267V1::confirmation_dispatched&&effects==2,"actual owner pending confirm failed");const auto claim=confirm.result.claim_sequence;require(ExecuteLydInner267V1(confirm,stamp)&&confirm.result.status==LydStatus267V1::claim_consumed&&confirm.result.claim_sequence==claim&&!confirm.result.effect_attempted&&effects==2,"actual owner replayed original claim");
 auto fresh=request(LydAction267V1::query_personal,21);require(ExecuteLydInner267V1(fresh,stamp)&&fresh.result.status==LydStatus267V1::available,"fresh query failed");auto unknown=request(LydAction267V1::select_personal_candidate,21);unknown.request.provider_generation=fresh.result.provider_generation;unknown.request.query_sequence=fresh.result.query_sequence;unknown.request.choice_token="lyd.private.fixture";uncertain=true;require(ExecuteLydInner267V1(unknown,stamp)&&unknown.result.status==LydStatus267V1::indeterminate&&!unknown.result.source_available,"uncertain completion retained source");auto later=request(LydAction267V1::query_personal,21);require(ExecuteLydInner267V1(later,stamp)&&later.result.status==LydStatus267V1::indeterminate&&!later.result.cleanup_known&&effects==3,"unknown session reminted permission");return 0;}
