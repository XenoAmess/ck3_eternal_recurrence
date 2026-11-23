#pragma once
#include "ccc_owner_nogame_common.hpp"
#include "xar_bridge/ck3_121003_ccc_event26785313_owner_v1.hpp"
namespace ccc_event_nogame {
using namespace ccc_nogame;using namespace c;
inline CccEventFrame267V1 frame;inline CccEventRaw267V1 raw;
inline bool frame_good=true,read_good=true,drift_after_read=false;
inline int frames=0,reads=0,calls=0;inline CccEventCall267V1 response;
inline void Seed(std::int32_t actor=36423){
 frame={};raw={};frame_good=read_good=true;drift_after_read=false;frames=reads=calls=0;
 response={CccEventCallStatus267V1::returned,true,true,true};
 frame.facts_verified=true;frame.core=Core(actor);frame.scene.kind=LydKind267V1::events;
 frame.scene.global=0x1100;frame.scene.jomini=0x2200;frame.scene.context=0x3300;
 frame.scene.gfx=0x4400;frame.scene.handler=0x5500;frame.scene.application=0x6600;frame.scene.events_layer=0x7700;
 raw.source.case_bound=raw.source.sampled_twice=raw.source.event_census.census_complete=true;
 raw.source.event_census.named_root_count=1;raw.source.fixed_instance_id=1;raw.source.select_d_admissible=true;
 LydEventRow267V1 row;row.instance_id=1;row.recipient_character_id=actor;row.authored_option_count=6;
 row.definition_key=kCccEventDefinition267V1;row.opening="Original opening\x15\n";row.description="Original description";
 row.named_root_bound=row.window_visible=row.window_enabled=true;
 for(int index:{5,3,0,4,2,1}){LydEventOption267V1 o;o.authored_option_index=index;o.native_can_select=index==3||index==4;o.text="Actual option "+std::to_string(index);row.options.push_back(o);}
 raw.source.event_census.events.push_back(row);raw.material.native_read_entered=true;
 raw.material.manager_census.game=0x8800;raw.material.manager_census.jomini=frame.scene.jomini;
 raw.material.source.kind=LydKind267V1::events;raw.material.source.events=raw.source.event_census;
 raw.material.semantic_model.push_back(std::byte{1});
}
inline void NewTemporaryInstance(){raw.source.fixed_instance_id=2;raw.source.event_census.events[0].instance_id=2;raw.source.select_d_admissible=false;raw.source.select_f_admissible=true;raw.material.source.events=raw.source.event_census;raw.material.semantic_model.push_back(std::byte{2});}
struct Fixture {
 CccEventSession267V1 session;mt::MainThreadQueryMailboxV1 mailbox{};mt::MainThreadExecutionStampV1 stamp{};std::uint64_t seq=0;
 explicit Fixture(std::int32_t actor=36423){Seed(actor);mailbox.offline_fixture=false;mailbox.permitted_executor_duotrigintary=&ExecuteCccOnOwner267V1;stamp.thread_id=7;stamp.pump_epoch=9;}
 CccEventContext267V1 Context(std::string_view id,CccEventAction267V1 action=CccEventAction267V1::query){CccEventContext267V1 q;q.session=&session;q.mailbox=&mailbox;q.ticket.sequence=++seq;q.connection_generation=1;q.request.action=action;q.request.expected=frame.core;q.request.deadline_unix_ms=WallNow()+60000;SetId(q.request,id);ArmCccEventDeadline267V1(q);return q;}
 void Run(CccEventContext267V1&q){q.invocation.context=&q;Check(ExecuteCccEventInner267V1(q,stamp),"actual CCC event Inner returned");}
 CccEventContext267V1 Query(std::string_view id="query"){auto q=Context(id);Run(q);Check(q.result.status==CccEventStatus267V1::available&&q.result.source_available&&q.result.source,"actual owner readonly Source");return q;}
 CccEventContext267V1 Select(const CccEventContext267V1&original,std::string_view id="select",CccEventAction267V1 action=CccEventAction267V1::select_tier_four){auto q=Context(id,action);q.request.expected=original.request.expected;q.request.deadline_unix_ms=original.request.deadline_unix_ms;q.request.provider_generation=original.result.provider_generation;q.request.query_sequence=original.result.query_sequence;q.request.instance_id=original.result.source->fixed_instance_id;ArmCccEventDeadline267V1(q);return q;}
};
}
namespace xar::ck3_121003::build26785313 {
bool ReadCccEventFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t wall,std::uint64_t,CccEventFrame267V1&out,std::string&why)noexcept{++ccc_event_nogame::frames;out=ccc_event_nogame::frame;out.scene.wall_deadline=wall;if(ccc_event_nogame::drift_after_read&&ccc_event_nogame::reads)++out.core.clock.date_raw;why="explicit self-owned NoGame Frame DATA";return ccc_event_nogame::frame_good;}
bool ReadCccEventRaw267V1(const ReadonlyBindings&,const CccEventFrame267V1&,const CccEventRequest267V1&,std::uint64_t,CccEventRaw267V1&out,std::string&why)noexcept{++ccc_event_nogame::reads;out=ccc_event_nogame::raw;why="explicit self-owned NoGame Raw DATA";return ccc_event_nogame::read_good;}
CccEventCall267V1 CallCccEventRaw267V1(const ReadonlyBindings&,const CccEventFrame267V1&,const CccEventRequest267V1&,std::uint64_t,const CccEventRaw267V1&)noexcept{++ccc_event_nogame::calls;return ccc_event_nogame::response;}
}
#ifndef XAR_CCC_EVENT_OWNER_SOURCE
#define XAR_CCC_EVENT_OWNER_SOURCE "ck3_121003_ccc_event26785313_owner_v1.cpp"
#endif
#ifndef XAR_CCC_EVENT_WIRE_SOURCE
#define XAR_CCC_EVENT_WIRE_SOURCE "ck3_121003_ccc_event26785313_wire_v1.cpp"
#endif
#include XAR_CCC_EVENT_OWNER_SOURCE
#include XAR_CCC_EVENT_WIRE_SOURCE
