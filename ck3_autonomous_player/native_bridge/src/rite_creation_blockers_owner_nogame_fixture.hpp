#pragma once
#ifndef XAR_RITE_BLOCKERS_OWNER_TEST_OWNER_SOURCE
#define XAR_RITE_BLOCKERS_OWNER_TEST_OWNER_SOURCE "ck3_121003_rite_creation_blockers26785313_owner_v1.cpp"
#endif
#ifndef XAR_RITE_BLOCKERS_OWNER_TEST_WIRE_SOURCE
#define XAR_RITE_BLOCKERS_OWNER_TEST_WIRE_SOURCE "ck3_121003_rite_creation_blockers26785313_wire_v1.cpp"
#endif
#include XAR_RITE_BLOCKERS_OWNER_TEST_OWNER_SOURCE
#include XAR_RITE_BLOCKERS_OWNER_TEST_WIRE_SOURCE
#include <iostream>
#include <stdexcept>
namespace blockers_owner_test {
using namespace xar::ck3_121003::build26785313;
using Core=xar::ck3_1210::CoreSnapshotPrefix;using Stamp=xar::ck3_11906::MainThreadExecutionStampV1;using Mailbox=xar::ck3_11906::MainThreadQueryMailboxV1;using Status=RiteBlockersStatus267V1;
inline void Need(bool v,const char*s){if(!v)throw std::runtime_error(s);}
inline Core CoreFor(std::int32_t id=36423){Core c;c.clock.date_raw=53144328;c.clock.speed=3;c.clock.paused=true;c.local_player_id=1;c.map_ready=c.has_played_character=c.played_character_alive=true;c.played_character_id=id;return c;}
inline void Change(Core&c,unsigned n){switch(n){case 0:c.clock.date_raw+=24;break;case 1:c.clock.speed=2;break;case 2:c.clock.paused=false;break;case 3:c.local_player_id=2;break;case 4:c.map_ready=false;break;case 5:c.has_played_character=false;break;case 6:c.played_character_id=50;break;case 7:c.played_character_alive=false;break;default:break;}}
struct State {std::array<std::uint64_t,5>world{};Core core=CoreFor();std::uint32_t rite=0;unsigned frames=0,rawcalls=0,binds=0,driftCore=8,driftPointer=4;bool can=false,creating=true,visible=true,enabled=true,missing=false,clean=true,sampled=true,expireAfter=false;std::string text;void*context=nullptr;void Reset(){core=CoreFor();rite=0;frames=rawcalls=binds=0;driftCore=8;driftPointer=4;can=false;creating=visible=enabled=clean=sampled=true;missing=expireAfter=false;text.clear();context=nullptr;}};
inline State state;inline unsigned ids=0;
inline std::unique_ptr<Mailbox> Box(){auto m=std::make_unique<Mailbox>();m->offline_fixture=false;m->permitted_executor_trigintary=&ExecuteRiteBlockersOnOwner267V1;return m;}
inline Stamp StampFor(){Stamp s;s.thread_id=GetCurrentThreadId();s.pump_epoch=17;s.paused=true;return s;}
inline RiteBlockersContext267V1 Query(RiteBlockersSession267V1&session,Mailbox*m){RiteBlockersContext267V1 q;q.session=&session;q.mailbox=m;q.connection_generation=9;q.ticket.sequence=++ids;q.request.expected=state.core;q.request.expected_source_rite_id=state.rite;q.request.deadline_unix_ms=Wall()+60000;const auto id="blockers-owner-"+std::to_string(ids);std::copy(id.begin(),id.end(),q.request.request_id.begin());q.request.request_id_size=static_cast<std::uint8_t>(id.size());ArmRiteBlockersDeadline267V1(q);return q;}
inline void Run(RiteBlockersContext267V1&q){Need(ExecuteRiteBlockersOnOwner267V1(&q,StampFor()),"actual owner refused");}
inline void NoSource(const RiteBlockersContext267V1&q){Need(!q.result.source_available&&!q.result.source&&!q.result.provider_generation&&!q.result.query_sequence,"unexpected source or informational sequence");}
inline void Wire(const RiteBlockersContext267V1&q,bool available){const auto w=SerializeRiteBlockersResult267V1(q.request.id(),q.result);for(const auto s:{"\"claim_sequence\":\"0\"","\"effect_attempted\":false","\"native_returned\":false","\"native_handled\":false","\"new_date_observed\":false","\"physical_save_confirmed\":false"})Need(w.find(s)!=std::string::npos,"effect/claim was fabricated");Need(w.find(available?"\"ok\":true":"\"ok\":false")!=std::string::npos,"unexpected wire status");}
}
namespace xar::ck3_121003::build26785313 {
ReadonlyBindings BindReadonlyImage(std::uintptr_t,std::string_view)noexcept{++blockers_owner_test::state.binds;return{};}
bool ReadRiteBlockersFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*context,const RiteBlockersRequest267V1&r,std::uint64_t,RiteBlockersFrame267V1&out,std::string&why)noexcept{auto&s=blockers_owner_test::state;++s.frames;s.context=context;out={};out.facts_verified=true;out.core=s.core;if(s.frames>1)blockers_owner_test::Change(out.core,s.driftCore);std::array<std::uintptr_t*,4>p{&out.game,&out.jomini,&out.storage,&out.actor};for(unsigned i=0;i<4;++i)*p[i]=reinterpret_cast<std::uintptr_t>(&s.world[s.frames>1&&s.driftPointer==i?4:i]);if(r.expected_source_rite_id!=s.rite){why="self_owned_source_rite_guard_mismatch";return false;}return true;}
bool ReadRiteBlockersRaw267V1(const ReadonlyBindings&,const RiteBlockersFrame267V1&f,const RiteBlockersRequest267V1&,std::uint64_t,RiteBlockersRaw267V1&out,std::string&why)noexcept{auto&s=blockers_owner_test::state;++s.rawcalls;out={};out.entered=true;out.cleanup_known=s.clean;if(s.expireAfter)static_cast<RiteBlockersContext267V1*>(s.context)->monotonic_deadline_ms=1;if(s.missing){why="self_owned_raw_missing_not_false";return false;}out.source.source_rite_id=s.rite;out.source.actor_id=f.core.played_character_id;out.source.is_creating=s.creating;out.source.native_can_create=s.can;out.source.blockers_text=s.text;out.source.window_visible=s.visible;out.source.window_enabled=s.enabled;out.source.sampled_twice=s.sampled;return true;}
}
