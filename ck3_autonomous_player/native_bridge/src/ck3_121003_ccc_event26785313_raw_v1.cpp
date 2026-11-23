#include "xar_bridge/ck3_121003_ccc_event26785313_owner_v1.hpp"
#include <algorithm>
#include <chrono>
#include <windows.h>
#ifndef XAR_STOCK_BOOKMARK_CALL_ADDRESS
#define XAR_STOCK_BOOKMARK_CALL_ADDRESS(image,rva) ((image)+(rva))
#endif
namespace xar::ck3_121003::build26785313 {namespace {
[[maybe_unused]]bool Same(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&z)noexcept{return a.clock.date_raw==z.clock.date_raw&&a.clock.speed==z.clock.speed&&a.clock.paused==z.clock.paused&&a.local_player_id==z.local_player_id&&a.map_ready==z.map_ready&&a.has_played_character==z.has_played_character&&a.played_character_id==z.played_character_id&&a.played_character_alive==z.played_character_alive;}
[[maybe_unused]]bool Fresh(const ReadonlyBindings&b,const CccEventFrame267V1&f,const CccEventRequest267V1&q,std::uint64_t mono)noexcept{const auto wall=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();if(!mono||GetTickCount64()>=mono||wall<=0||static_cast<std::uint64_t>(wall)>=q.deadline_unix_ms||!f.facts_verified||!Same(f.core,q.expected)||!f.core.clock.paused||f.scene.kind!=LydKind267V1::events||f.scene.wall_deadline!=q.deadline_unix_ms)return false;__try{ck3_1210::CoreSnapshotPrefix actual;return ck3_1210::ReadCoreSnapshot(b.core,actual)&&Same(actual,f.core);}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]void Derive(const LydEventSource267V1&e,std::int32_t actor,CccEventSource267V1&out){
 out={};out.event_census=e;out.sampled_twice=true;if(!e.census_complete||e.named_root_count!=1||e.events.size()!=1)return;
 const auto&r=e.events[0];if(r.definition_key!=kCccEventDefinition267V1||r.recipient_character_id!=actor||r.authored_option_count!=6||!r.named_root_bound||!r.window_visible||!r.window_enabled)return;
 std::array<bool,6>seen{};const LydEventOption267V1*d=nullptr,*f=nullptr;
 for(const auto&o:r.options){if(o.authored_option_index<0||o.authored_option_index>=6||seen[static_cast<std::size_t>(o.authored_option_index)])return;seen[static_cast<std::size_t>(o.authored_option_index)]=true;if(o.authored_option_index==3)d=&o;if(o.authored_option_index==4)f=&o;}
 // Complete authored definitions are separate from conditionally visible material rows.
 out.fixed_instance_id=r.instance_id;out.select_d_admissible=d&&d->native_can_select&&!d->text.empty();out.select_f_admissible=f&&f->native_can_select&&!f->text.empty();
}
[[maybe_unused]]std::uintptr_t Chosen(const CccEventRaw267V1&r,CccEventAction267V1 action)noexcept{
 const int index=action==CccEventAction267V1::select_tier_four?3:action==CccEventAction267V1::select_temporary_cancel?4:-1;
 if(index<0||!(index==3?r.source.select_d_admissible:r.source.select_f_admissible)||!r.source.fixed_instance_id||r.material.event_rows.size()!=1||r.source.event_census.events.size()!=1)return 0;
 const auto&pub=r.source.event_census.events[0];const auto&row=r.material.event_rows[0];if(row.instance_id!=*r.source.fixed_instance_id||!row.controller||!row.root||!row.data||!row.runtime||!row.definition||row.options.size()!=pub.options.size())return 0;
 std::uintptr_t pointer=0;for(std::size_t n=0;n<pub.options.size();++n)if(pub.options[n].authored_option_index==index){if(pointer)return 0;pointer=row.options[n];}return pointer;
}
[[maybe_unused]]bool Can(std::uintptr_t image,std::uintptr_t p,bool&out)noexcept{__try{out=reinterpret_cast<bool(__fastcall*)(const void*)>(XAR_STOCK_BOOKMARK_CALL_ADDRESS(image,0x1B6CC30))(reinterpret_cast<const void*>(p));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Select(std::uintptr_t image,std::uintptr_t p)noexcept{__try{reinterpret_cast<void(__fastcall*)(void*)>(XAR_STOCK_BOOKMARK_CALL_ADDRESS(image,0x1B6CA10))(reinterpret_cast<void*>(p));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
}
bool VerifyCccEventImage267V1([[maybe_unused]]std::uintptr_t image)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_CCC_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_EVENT_V1
 return image&&image==reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))&&VerifyLydImage267V1(image);
#else
 return false;
#endif
}
bool ReadCccEventRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const CccEventFrame267V1&f,[[maybe_unused]]const CccEventRequest267V1&q,[[maybe_unused]]std::uint64_t mono,CccEventRaw267V1&out,std::string&why)noexcept{out={};why="ccc_event_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_CCC_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_EVENT_V1
 try{if(!VerifyCccEventImage267V1(b.module_base)||!Fresh(b,f,q,mono)){why="ccc_event_actual_image_core_or_deadline_unavailable";return false;}LydRequest267V1 read;read.action=LydAction267V1::query_events;read.expected=q.expected;read.deadline_unix_ms=q.deadline_unix_ms;read.request_id=q.request_id;read.request_id_size=q.request_id_size;if(!ReadLydRaw267V1(b,f.core,f.scene,mono,read,{},out.material,why))return false;if(!out.material.source.events||out.material.source.kind!=LydKind267V1::events||!out.material.cleanup_known){why="ccc_event_actual_complete_character_event_source_unavailable";return false;}Derive(*out.material.source.events,f.core.played_character_id,out.source);out.source.case_bound=CccCaseAdmitted267V1(f.core,f.connection_generation,out.material.manager_census.game,out.material.manager_census.jomini);if(!out.source.case_bound)out.source.select_d_admissible=out.source.select_f_admissible=false;if(!CccEventSourceShape267V1(out.source)||!Fresh(b,f,q,mono)){why="ccc_event_complete_source_or_final_core_changed";return false;}why.clear();return true;}catch(...){out.material.cleanup_known=!out.material.native_read_entered;why="ccc_event_actual_raw_exception";return false;}
#else
 return false;
#endif
}
CccEventCall267V1 CallCccEventRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const CccEventFrame267V1&f,[[maybe_unused]]const CccEventRequest267V1&q,[[maybe_unused]]std::uint64_t mono,[[maybe_unused]]const CccEventRaw267V1&issued)noexcept{CccEventCall267V1 call;
#if defined(XAR_CK3_ENABLE_121003_26785313_CCC_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_EVENT_V1
 try{if((q.action!=CccEventAction267V1::select_tier_four&&q.action!=CccEventAction267V1::select_temporary_cancel)||!q.instance_id||q.instance_id!=issued.source.fixed_instance_id)return call;CccEventRaw267V1 actual;std::string why;if(!ReadCccEventRaw267V1(b,f,q,mono,actual,why)){call.cleanup_known=actual.material.cleanup_known;if(!call.cleanup_known)call.status=CccEventCallStatus267V1::indeterminate;return call;}if(actual!=issued||!(q.action==CccEventAction267V1::select_tier_four?actual.source.select_d_admissible:actual.source.select_f_admissible))return call;const auto p=Chosen(actual,q.action);if(!p||!Fresh(b,f,q,mono))return call;bool can=false;if(!Can(b.module_base,p,can)){call.cleanup_known=false;call.status=CccEventCallStatus267V1::indeterminate;return call;}if(!can||!Fresh(b,f,q,mono))return call;call.entered=true;if(!Select(b.module_base,p)){call.cleanup_known=false;call.status=CccEventCallStatus267V1::indeterminate;return call;}call.native_returned=true;call.status=Fresh(b,f,q,mono)?CccEventCallStatus267V1::returned:CccEventCallStatus267V1::indeterminate;return call;}catch(...){call.cleanup_known=false;call.status=CccEventCallStatus267V1::indeterminate;return call;}
#endif
 return call;
}
}
