#pragma once
// Actual owner/wire, explicit self-owned DATA dependencies only. No native ABI.
#ifndef XAR_RITE_TEXT_OWNER_TEST_WIRE_SOURCE
#define XAR_RITE_TEXT_OWNER_TEST_WIRE_SOURCE "ck3_121003_rite_text26785313_wire_v1.cpp"
#endif
#ifndef XAR_RITE_TEXT_OWNER_TEST_OWNER_SOURCE
#define XAR_RITE_TEXT_OWNER_TEST_OWNER_SOURCE "ck3_121003_rite_text26785313_owner_v1.cpp"
#endif
#include XAR_RITE_TEXT_OWNER_TEST_WIRE_SOURCE
#include XAR_RITE_TEXT_OWNER_TEST_OWNER_SOURCE
#include <array>
#include <iostream>
#include <stdexcept>
namespace text_owner_fixture {
using namespace xar::ck3_121003::build26785313;
using A=RiteTextAction267V1;using S=RiteTextStatus267V1;
using Session=RiteTextSession267V1;using Context=RiteTextContext267V1;
using Core=xar::ck3_1210::CoreSnapshotPrefix;
using Mailbox=xar::ck3_11906::MainThreadQueryMailboxV1;
using Stamp=xar::ck3_11906::MainThreadExecutionStampV1;
inline void Require(bool value,const char*why){if(!value)throw std::runtime_error(why);}
inline auto CoreFor(std::int32_t actor=36423){Core c{};c.clock.date_raw=53144328;c.clock.speed=1;c.clock.paused=true;c.local_player_id=0;c.map_ready=c.has_played_character=c.played_character_alive=true;c.played_character_id=actor;return c;}
struct State {
  std::array<std::uint64_t,12> memory{};Core core=CoreFor();std::uint32_t rite=47;
  std::string name="Old name",description="Old description";
  bool creating=true,visible=true,enabled=true,blocked=false,admissible=true;
  bool raw_missing=false,raw_cleanup=true,world_drift=false,core_drift=false;
  unsigned raw_mutation=0,bindings=0,frames=0,observations=0,calls=0,entered_calls=0;
  RiteTextCallStatus267V1 call_status=RiteTextCallStatus267V1::returned;
  bool call_entered=true,call_cleanup=true,apply=true;
  std::uintptr_t Address(std::size_t i){return reinterpret_cast<std::uintptr_t>(&memory[i]);}
  void Reset(){core=CoreFor();rite=47;name="Old name";description="Old description";
    creating=visible=enabled=admissible=raw_cleanup=call_entered=call_cleanup=apply=true;
    blocked=raw_missing=world_drift=core_drift=false;raw_mutation=bindings=frames=observations=calls=entered_calls=0;call_status=RiteTextCallStatus267V1::returned;}
};
inline State state;inline std::uint64_t ids=0;
inline auto Mail(){auto m=std::make_unique<Mailbox>();m->offline_fixture=false;m->permitted_executor_novemvigintary=&ExecuteRiteTextOnOwner267V1;return m;}
inline auto StampNow(){Stamp s{};s.thread_id=GetCurrentThreadId();s.pump_epoch=11;s.paused=true;return s;}
inline Context Request(Session&s,Mailbox*m,A action){Context q{};q.session=&s;q.mailbox=m;q.connection_generation=21;q.ticket.sequence=++ids;
  q.request.action=action;q.request.expected=state.core;q.request.expected_source_rite_id=state.rite;q.request.deadline_unix_ms=Wall()+60000;
  auto id="text-owner-nogame-"+std::to_string(ids);std::copy(id.begin(),id.end(),q.request.request_id.begin());q.request.request_id_size=static_cast<std::uint8_t>(id.size());
  if(action!=A::query)q.request.provider_generation=q.request.query_sequence=1;ArmRiteTextDeadline267V1(q);return q;}
inline Context FromQuery(Session&s,Mailbox*m,A action,const Context&query,std::string text){auto q=Request(s,m,action);q.request.expected=query.request.expected;q.request.expected_source_rite_id=query.request.expected_source_rite_id;q.request.deadline_unix_ms=query.request.deadline_unix_ms;q.request.provider_generation=query.result.provider_generation;q.request.query_sequence=query.result.query_sequence;q.request.text=std::move(text);ArmRiteTextDeadline267V1(q);return q;}
inline void Run(Context&q){state.frames=0;Require(ExecuteRiteTextOnOwner267V1(&q,StampNow()),"actual text owner refused context");}
inline void NoSource(const Context&q){Require(!q.result.source_available&&!q.result.source,"refusal retained Source");}
inline std::string Wire(const Context&q){auto w=SerializeRiteTextResult267V1(q.request.id(),q.result);for(auto t:{"\"native_handled\":false","\"text_applied\":false","\"new_date_observed\":false","\"physical_save_confirmed\":false"})Require(w.find(t)!=std::string::npos,"wire fabricated handled/applied/date/SAVE credit");return w;}
inline Context Query(Session&s,Mailbox*m){auto q=Request(s,m,A::query);Run(q);Require(q.result.status==S::available&&q.result.source&&q.result.provider_generation&&q.result.query_sequence,"actual complete text query failed");return q;}
inline Context Write(Session&s,Mailbox*m,A a,const Context&query,std::string text){auto q=FromQuery(s,m,a,query,std::move(text));Run(q);Require(q.result.status==S::text_dispatched&&q.result.effect_attempted&&q.result.native_returned&&!q.result.native_handled&&q.result.cleanup_known&&q.result.claim_sequence&&q.result.source==query.result.source,"void setter lost immutable actual beforeSource/lease/claim");return q;}
}
namespace xar::ck3_121003::build26785313 {
ReadonlyBindings BindReadonlyImage(std::uintptr_t,std::string_view)noexcept{++text_owner_fixture::state.bindings;return{};}
bool ReadRiteTextFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,const RiteTextRequest267V1&,std::uint64_t,RiteTextFrame267V1&out,std::string&)noexcept{
  auto&f=text_owner_fixture::state;++f.frames;out={};out.facts_verified=true;out.core=f.core;if(f.frames>1&&f.core_drift)out.core.clock.date_raw+=24;
  out.game=f.Address(f.frames>1&&f.world_drift?11:0);out.jomini=f.Address(1);out.storage=f.Address(2);out.actor=f.Address(3);return true;
}
bool ReadRiteTextRaw267V1(const ReadonlyBindings&,const RiteTextFrame267V1&frame,const RiteTextRequest267V1&,std::uint64_t,RiteTextRaw267V1&out,std::string&why)noexcept{
  auto&f=text_owner_fixture::state;++f.observations;out={};out.entered=true;out.cleanup_known=f.raw_cleanup;
  if(f.raw_missing){why="nogame_actual_text_source_unavailable";return false;}
  out.source={f.rite,frame.core.played_character_id,f.creating,f.name,f.description,f.visible,f.enabled,f.blocked,f.admissible};
  out.values.name=f.name;out.values.description=f.description;
  out.controller=f.Address(4);out.context=f.Address(5);out.root=f.Address(6);
  // These are public DATA records only; no RiteDraft/GUI ABI or pointer dereference is simulated.
  out.draft.source_rite_id=f.rite;out.draft.controller=f.Address(4);out.draft.gfx=f.Address(7);out.draft.handler=f.Address(8);out.draft.piety_cost_raw=123456;out.draft.piety_missing_raw=-7;
  if(f.raw_mutation==1)out.values.name_header[0]=std::byte{1};
  if(f.raw_mutation==2)out.draft.gfx=f.Address(9);
  if(f.raw_mutation==3)out.selected_header[0]=std::byte{1};
  return true;
}
RiteTextCall267V1 CallRiteTextRaw267V1(const ReadonlyBindings&,const RiteTextFrame267V1&,const RiteTextRequest267V1&q,std::uint64_t,const RiteTextRaw267V1&)noexcept{
  auto&f=text_owner_fixture::state;++f.calls;if(f.call_entered)++f.entered_calls;
  if(f.call_status==RiteTextCallStatus267V1::returned&&f.call_entered&&f.apply){if(q.action==RiteTextAction267V1::set_name)f.name=q.text;else if(q.action==RiteTextAction267V1::set_description)f.description=q.text;}
  return{f.call_status,f.call_entered,f.call_cleanup};
}
}
