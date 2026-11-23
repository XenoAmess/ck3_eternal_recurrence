#pragma once
#include "ccc_owner_nogame_common.hpp"
#include "xar_bridge/ck3_121003_ccc_decision26785313_owner_v1.hpp"
namespace ccc_decision_nogame {
using namespace ccc_nogame;using namespace c;
inline CccDecisionFrame267V1 frame;inline CccDecisionRaw267V1 raw;
inline bool frame_good=true,read_good=true,drift_after_read=false;
inline int frames=0,reads=0,calls=0;inline CccDecisionRawCall267V1 response;
inline void Seed(std::int32_t actor=36423){
 frame={};raw={};frame_good=read_good=true;drift_after_read=false;frames=reads=calls=0;
 response={CccDecisionRawCallStatus267V1::returned,true,true,false};frame.facts_verified=true;frame.core=Core(actor);
 frame.scene.global=0x1100;frame.scene.jomini=0x2200;frame.scene.context=0x3300;frame.scene.gfx=0x4400;frame.scene.handler=0x5500;frame.scene.list_root=0x6600;frame.scene.list_enabled=true;
 raw.source.list_found=raw.source.list_enabled=raw.source.complete_model_census=raw.source.open_list_admissible=raw.source.case_bound=true;
 raw.source.groups_count=1;raw.source.total_model_rows=1;raw.source.corruption_traits=std::array<bool,4>{false,false,false,true};
 raw.source.fixture_tax_variable_present=true;raw.source.fixture_tax_exact_half=true;raw.source.rows.push_back({CccDecision267V1::corruption_policy,false,false});
 raw.list=0x6600;raw.controller=0x7700;raw.rows[0]=0x8800;raw.exact_model.push_back(std::byte{1});raw.native_read_entered=true;
}
inline void ListOpened(){frame.scene.list_visible=true;raw.source.list_visible=true;raw.source.open_list_admissible=false;raw.source.rows[0].can_open_detail=true;}
inline void DetailOpened(bool can=true){ListOpened();frame.scene.detail_root=0x9900;frame.scene.detail_visible=frame.scene.detail_enabled=true;
 raw.detail=0x9900;raw.definition=0xAA00;raw.source.detail_found=raw.source.detail_visible=raw.source.detail_enabled=true;
 raw.source.selected_decision=CccDecision267V1::corruption_policy;raw.source.native_can_confirm=can;raw.source.confirm_admissible=can;
 raw.source.widget_state=1;raw.source.rows[0].can_open_detail=false;raw.source.rows[0].is_selected=true;
 raw.source.confirm_tooltip_observed=true;raw.source.confirm_tooltip="";
}
struct Fixture {
 CccDecisionSession267V1 session;mt::MainThreadQueryMailboxV1 mailbox{};mt::MainThreadExecutionStampV1 stamp{};std::uint64_t seq=0;
 explicit Fixture(std::int32_t actor=36423){Seed(actor);mailbox.offline_fixture=false;mailbox.permitted_executor_duotrigintary=&ExecuteCccOnOwner267V1;stamp.thread_id=7;stamp.pump_epoch=9;}
 CccDecisionContext267V1 Context(std::string_view id,CccDecisionAction267V1 action=CccDecisionAction267V1::query){CccDecisionContext267V1 q;q.session=&session;q.mailbox=&mailbox;q.ticket.sequence=++seq;q.connection_generation=1;q.request.action=action;q.request.expected=frame.core;q.request.deadline_unix_ms=WallNow()+60000;SetId(q.request,id);ArmCccDecisionDeadline267V1(q);return q;}
 void Run(CccDecisionContext267V1&q){q.invocation.context=&q;Check(ExecuteCccDecisionInner267V1(q,stamp),"actual CCC decision Inner returned");}
 CccDecisionContext267V1 Query(std::string_view id="query"){auto q=Context(id);Run(q);Check(q.result.status==CccDecisionStatus267V1::available&&q.result.source_available&&q.result.source,"actual owner readonly Source");return q;}
 CccDecisionContext267V1 Action(const CccDecisionContext267V1&original,CccDecisionAction267V1 action,std::string_view id="effect"){auto q=Context(id,action);q.request.expected=original.request.expected;q.request.deadline_unix_ms=original.request.deadline_unix_ms;q.request.provider_generation=original.result.provider_generation;q.request.query_sequence=original.result.query_sequence;if(action!=CccDecisionAction267V1::open_list)q.request.decision=CccDecision267V1::corruption_policy;ArmCccDecisionDeadline267V1(q);return q;}
};
}
namespace xar::ck3_121003::build26785313 {
bool ReadCccDecisionFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,CccDecisionFrame267V1&out,std::string&why)noexcept{++ccc_decision_nogame::frames;out=ccc_decision_nogame::frame;if(ccc_decision_nogame::drift_after_read&&ccc_decision_nogame::reads)++out.core.clock.date_raw;why="explicit self-owned NoGame Frame DATA";return ccc_decision_nogame::frame_good;}
bool ReadCccDecisionRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const CccDecisionScene267V1&,std::uint64_t,CccDecisionRaw267V1&out,std::string&why)noexcept{++ccc_decision_nogame::reads;out=ccc_decision_nogame::raw;why="explicit self-owned NoGame Raw DATA";return ccc_decision_nogame::read_good;}
CccDecisionRawCall267V1 CallCccDecisionRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const CccDecisionScene267V1&,std::uint64_t,const CccDecisionRaw267V1&,CccDecisionAction267V1,std::optional<CccDecision267V1>)noexcept{++ccc_decision_nogame::calls;return ccc_decision_nogame::response;}
}
#ifndef XAR_CCC_DECISION_OWNER_SOURCE
#define XAR_CCC_DECISION_OWNER_SOURCE "ck3_121003_ccc_decision26785313_owner_v1.cpp"
#endif
#ifndef XAR_CCC_DECISION_WIRE_SOURCE
#define XAR_CCC_DECISION_WIRE_SOURCE "ck3_121003_ccc_decision26785313_wire_v1.cpp"
#endif
#include XAR_CCC_DECISION_OWNER_SOURCE
#include XAR_CCC_DECISION_WIRE_SOURCE
