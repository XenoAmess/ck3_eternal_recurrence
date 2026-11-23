#include <windows.h>
#include <algorithm>
#include <chrono>
#include <iostream>
#include <stdexcept>
#include "xar_bridge/ck3_121003_ccc_event26785313_owner_v1.hpp"
namespace stock_raw_test {using namespace xar::ck3_121003::build26785313;
inline constexpr std::uintptr_t image=0x10700000;inline CccEventFrame267V1 frame;inline LydRaw267V1 material;inline bool case_ok=true,can=true,throw_select=false,change_core=false,read_good=true;inline int cans=0,selects=0,reads=0;inline std::uintptr_t expected=0x8881;
inline HMODULE FakeModule(LPCWSTR){return reinterpret_cast<HMODULE>(image);}
inline bool __fastcall FakeCan(const void*p){++cans;if(reinterpret_cast<std::uintptr_t>(p)!=expected)RaiseException(0xE0000107,0,0,nullptr);return can;}
inline void __fastcall FakeSelect(void*p){++selects;if(reinterpret_cast<std::uintptr_t>(p)!=expected||throw_select)RaiseException(0xE0000108,0,0,nullptr);if(change_core)frame.core.clock.date_raw+=24;}
inline std::uintptr_t Address(std::uintptr_t base,std::uintptr_t rva){if(base!=image)throw std::runtime_error("wrong actual wrapper image");if(rva==0x1B6CC30)return reinterpret_cast<std::uintptr_t>(&FakeCan);if(rva==0x1B6CA10)return reinterpret_cast<std::uintptr_t>(&FakeSelect);throw std::runtime_error("unapproved native call");}
inline void Check(bool c,const char*m){if(!c)throw std::runtime_error(m);}
inline CccEventRequest267V1 Query(std::int32_t actor=36423){frame={};material={};case_ok=can=read_good=true;throw_select=change_core=false;cans=selects=reads=0;frame.facts_verified=true;frame.connection_generation=9;frame.core.clock={53145600,3,true};frame.core.local_player_id=1;frame.core.map_ready=frame.core.has_played_character=frame.core.played_character_alive=true;frame.core.played_character_id=actor;frame.scene.kind=LydKind267V1::events;frame.scene.wall_deadline=18446744073709551615ULL;LydEventSource267V1 src;src.census_complete=true;src.named_root_count=1;LydEventRow267V1 row;row.instance_id=1;row.recipient_character_id=actor;row.definition_key=kCccEventDefinition267V1;row.authored_option_count=6;row.opening="Actual opening";row.description="Actual description";row.named_root_bound=row.window_visible=row.window_enabled=true;for(int index:{3,4,2,0,1,5}){LydEventOption267V1 o;o.authored_option_index=index;o.native_can_select=(index==3||index==4);o.text="Original actual option "+std::to_string(index);row.options.push_back(o);}src.events.push_back(row);material.source.kind=LydKind267V1::events;material.source.events=src;material.native_read_entered=true;LydEventRawRow267V1 r;r.instance_id=1;r.controller=0x100;r.root=0x200;r.data=0x300;r.runtime=0x400;r.definition=0x500;r.options={expected,0x8884,0x8882,0x8883,0x8885,0x8886};material.event_rows.push_back(r);CccEventRequest267V1 q;q.expected=frame.core;q.deadline_unix_ms=frame.scene.wall_deadline;const char id[]="raw-query";std::copy(id,id+sizeof(id),q.request_id.begin());q.request_id_size=sizeof(id)-1;return q;}
inline ReadonlyBindings Binding(){ReadonlyBindings b;b.module_base=image;b.exact_image_admitted=true;b.core.enabled=true;return b;}
}
namespace xar::ck3_1210 {bool ReadCoreSnapshot(const CoreBindings&,CoreSnapshotPrefix&out)noexcept{out=stock_raw_test::frame.core;return true;}}
namespace xar::ck3_121003::build26785313 {
bool CccCaseAdmitted267V1(const ck3_1210::CoreSnapshotPrefix&,std::uint64_t conn,std::uintptr_t,std::uintptr_t)noexcept{return stock_raw_test::case_ok&&conn==9;}
bool VerifyLydImage267V1(std::uintptr_t image)noexcept{return image==stock_raw_test::image;}
bool ReadLydRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const LydScene267V1&,std::uint64_t,const LydRequest267V1&q,const std::optional<LydSelectionAssociation267V1>&,LydRaw267V1&out,std::string&)noexcept{++stock_raw_test::reads;if(q.action!=LydAction267V1::query_events||q.decision||q.personal||q.event_role||q.instance_id)return false;out=stock_raw_test::material;return stock_raw_test::read_good;}
}
#define GetModuleHandleW stock_raw_test::FakeModule
#define XAR_STOCK_BOOKMARK_CALL_ADDRESS(image,rva) stock_raw_test::Address(image,rva)
#ifndef XAR_CCC_EVENT_RAW_SOURCE
#define XAR_CCC_EVENT_RAW_SOURCE "ck3_121003_ccc_event26785313_raw_v1.cpp"
#endif
#include XAR_CCC_EVENT_RAW_SOURCE
#undef GetModuleHandleW
using namespace stock_raw_test;using K=CccEventCallStatus267V1;
int main(){try{int groups=0;
 const auto capture=[](const CccEventRequest267V1&q){CccEventRaw267V1 r;std::string why;Check(ReadCccEventRaw267V1(Binding(),frame,q,18446744073709551615ULL,r,why),"new adapter actual read");return r;};
 const auto selection=[](CccEventRequest267V1 q){q.action=CccEventAction267V1::select_tier_four;q.provider_generation=q.query_sequence=1;q.instance_id=1;return q;};
 {auto q=Query();auto r=capture(q);Check(r.source.select_d_admissible&&r.source.fixed_instance_id==1,"actual D nativeCan is sufficient");auto call=CallCccEventRaw267V1(Binding(),frame,selection(q),18446744073709551615ULL,r);Check(call.status==K::returned&&call.entered&&call.native_returned&&call.cleanup_known&&selects==1&&cans==1,"shuffled actual authored3 resolves original option pointer");++groups;}
 {auto q=Query();material.source.events->events[0].options[0].native_can_select=false;auto r=capture(q);Check(!r.source.select_d_admissible,"actual C NativeCanfalse readable DATA");auto call=CallCccEventRaw267V1(Binding(),frame,selection(q),18446744073709551615ULL,r);Check(call.status==K::refused&&!call.entered&&!cans&&!selects,"no false-can dispatch");++groups;}
 {auto q=Query();auto r=capture(q);material.source.events->events[0].description+=" drift";auto call=CallCccEventRaw267V1(Binding(),frame,selection(q),18446744073709551615ULL,r);Check(!call.entered&&!selects&&!cans,"full real text fingerprint drift");++groups;}
 {auto q=Query();auto r=capture(q);material.semantic_model.push_back(std::byte{1});auto call=CallCccEventRaw267V1(Binding(),frame,selection(q),18446744073709551615ULL,r);Check(!call.entered&&!selects,"private material/header drift");++groups;}
 {auto q=Query();auto r=capture(q);can=false;auto call=CallCccEventRaw267V1(Binding(),frame,selection(q),18446744073709551615ULL,r);Check(cans==1&&!selects&&!call.entered&&call.status==K::refused,"fresh nativeCan immediately before select");++groups;}
 {auto q=Query();auto r=capture(q);auto select=selection(q);select.instance_id=2;auto call=CallCccEventRaw267V1(Binding(),frame,select,18446744073709551615ULL,r);Check(!call.entered&&!selects&&!cans,"wrong actual instance");++groups;}
 {auto q=Query();material.source.events->events[0].definition_key="other.event";auto r=capture(q);Check(!r.source.fixed_instance_id&&!r.source.select_d_admissible,"other real event query DATA only");++groups;}
 {auto q=Query();material.source.events->events[0].recipient_character_id++;auto r=capture(q);Check(!r.source.fixed_instance_id&&!r.source.select_d_admissible,"foreign recipient no fixed authorization");++groups;}
 {auto q=Query();material.source.events->events.push_back(material.source.events->events[0]);material.source.events->events[1].instance_id=2;material.source.events->named_root_count=2;auto r=capture(q);Check(!r.source.fixed_instance_id&&!r.source.select_d_admissible,"complete multiple-event DATA cannot select");++groups;}
 {auto q=Query();auto r=capture(q);throw_select=true;auto call=CallCccEventRaw267V1(Binding(),frame,selection(q),18446744073709551615ULL,r);Check(call.entered&&!call.native_returned&&!call.cleanup_known&&call.status==K::indeterminate,"native select SEH UNKNOWN, never no-effect");++groups;}
 {auto q=Query();auto r=capture(q);change_core=true;auto call=CallCccEventRaw267V1(Binding(),frame,selection(q),18446744073709551615ULL,r);Check(call.entered&&call.native_returned&&call.cleanup_known&&call.status==K::indeterminate,"callback return plus actual Core drift is indeterminate");++groups;}
 {auto q=Query();auto r=capture(q);auto call=CallCccEventRaw267V1(Binding(),frame,selection(q),0,r);Check(!call.entered&&!selects&&!cans,"expired mono pre-entry zero effects");++groups;}
 {for(auto actor:{0,-2}){auto q=Query(actor);auto r=capture(q);Check(r.source.select_d_admissible,"full signed packed actor0/-2 legal");}++groups;}
 {auto q=Query();auto r=capture(q);auto selected=selection(q);selected.action=CccEventAction267V1::select_temporary_cancel;expected=0x8884;auto call=CallCccEventRaw267V1(Binding(),frame,selected,18446744073709551615ULL,r);Check(call.status==K::returned&&selects==1&&cans==1,"fixed F resolves actual authored4 pointer independently");expected=0x8881;++groups;}
 {auto q=Query();auto&pub=material.source.events->events[0].options;pub.erase(pub.begin());material.event_rows[0].options.erase(material.event_rows[0].options.begin());auto r=capture(q);Check(!r.source.select_d_admissible&&r.source.select_f_admissible,"hidden d sparse rows retain exact f authored identity");auto selected=selection(q);selected.action=CccEventAction267V1::select_temporary_cancel;expected=0x8884;auto call=CallCccEventRaw267V1(Binding(),frame,selected,18446744073709551615ULL,r);Check(call.status==K::returned&&selects==1,"sparse F uses material row after removal");expected=0x8881;++groups;}
 {auto q=Query();case_ok=false;auto r=capture(q);Check(!r.source.case_bound&&!r.source.select_d_admissible&&!r.source.select_f_admissible,"foreign/missing CCC private case grants no selection");auto call=CallCccEventRaw267V1(Binding(),frame,selection(q),18446744073709551615ULL,r);Check(!call.entered&&!cans&&!selects,"no case no native call");++groups;}
 {auto q=Query();auto r=capture(q);q.action=static_cast<CccEventAction267V1>(3);q.instance_id=1;auto call=CallCccEventRaw267V1(Binding(),frame,q,18446744073709551615ULL,r);Check(!call.entered&&!cans&&!selects,"no arbitrary/extra e choice action");++groups;}
 {auto q=Query();auto r=capture(q);material.source.events->events[0].options[1].authored_option_index=3;CccEventRaw267V1 wrong;std::string why;Check(!ReadCccEventRaw267V1(Binding(),frame,q,18446744073709551615ULL,wrong,why),"duplicate authored definition rejected by actual shape");++groups;}
 {auto q=Query();auto r=capture(q);material.event_rows[0].options[0]++;auto call=CallCccEventRaw267V1(Binding(),frame,selection(q),18446744073709551615ULL,r);Check(!call.entered&&!cans&&!selects,"actual option pointer drift refuses original issued source");++groups;}
 std::cout<<"PASS fixed CCC d/f raw adapter "<<groups<<" groups, self-owned existing-Raw DATA and two fixed native stubs only\n";return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
