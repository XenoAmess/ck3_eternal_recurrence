#include "xar_bridge/ck3_121003_stock_bookmark107026785313_owner_v1.hpp"
#include <algorithm>
#include <chrono>
#include <windows.h>
#ifndef XAR_STOCK_BOOKMARK_CALL_ADDRESS
#define XAR_STOCK_BOOKMARK_CALL_ADDRESS(image,rva) ((image)+(rva))
#endif
namespace xar::ck3_121003::build26785313 {namespace {
[[maybe_unused]]bool Same(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&z)noexcept{return a.clock.date_raw==z.clock.date_raw&&a.clock.speed==z.clock.speed&&a.clock.paused==z.clock.paused&&a.local_player_id==z.local_player_id&&a.map_ready==z.map_ready&&a.has_played_character==z.has_played_character&&a.played_character_id==z.played_character_id&&a.played_character_alive==z.played_character_alive;}
[[maybe_unused]]bool Fresh(const ReadonlyBindings&b,const StockBookmarkFrame267V1&f,const StockBookmarkRequest267V1&q,std::uint64_t mono)noexcept{const auto wall=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();if(!mono||GetTickCount64()>=mono||wall<=0||static_cast<std::uint64_t>(wall)>=q.deadline_unix_ms||!f.facts_verified||!Same(f.core,q.expected)||!f.core.clock.paused||f.scene.kind!=LydKind267V1::events||f.scene.wall_deadline!=q.deadline_unix_ms)return false;__try{ck3_1210::CoreSnapshotPrefix actual;return ck3_1210::ReadCoreSnapshot(b.core,actual)&&Same(actual,f.core);}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]void Derive(const LydEventSource267V1&e,std::int32_t actor,StockBookmarkSource267V1&out){out={};out.event_census=e;out.sampled_twice=true;if(!e.census_complete||e.named_root_count!=1||e.events.size()!=1)return;const auto&r=e.events[0];if(r.definition_key!=kStockBookmarkDefinition267V1||r.recipient_character_id!=actor||r.authored_option_count!=3||r.options.size()!=3||!r.named_root_bound||!r.window_visible||!r.window_enabled)return;std::array<bool,3>seen{};const LydEventOption267V1*chosen=nullptr;for(const auto&o:r.options){if(o.authored_option_index<0||o.authored_option_index>=3||seen[static_cast<std::size_t>(o.authored_option_index)])return;seen[static_cast<std::size_t>(o.authored_option_index)]=true;if(o.authored_option_index==2)chosen=&o;}if(!chosen)return;out.fixed_instance_id=r.instance_id;out.select_c_admissible=chosen->native_can_select&&!chosen->text.empty();}
[[maybe_unused]]std::uintptr_t Chosen(const StockBookmarkRaw267V1&r)noexcept{if(!r.source.select_c_admissible||!r.source.fixed_instance_id||r.material.event_rows.size()!=1||r.source.event_census.events.size()!=1)return 0;const auto&pub=r.source.event_census.events[0];const auto&row=r.material.event_rows[0];if(row.instance_id!=*r.source.fixed_instance_id||!row.controller||!row.root||!row.data||!row.runtime||!row.definition||row.options.size()!=pub.options.size())return 0;std::uintptr_t p=0;for(std::size_t n=0;n<pub.options.size();++n)if(pub.options[n].authored_option_index==2){if(p)return 0;p=row.options[n];}return p;}
[[maybe_unused]]bool Can(std::uintptr_t image,std::uintptr_t p,bool&out)noexcept{__try{out=reinterpret_cast<bool(__fastcall*)(const void*)>(XAR_STOCK_BOOKMARK_CALL_ADDRESS(image,0x1B6CC30))(reinterpret_cast<const void*>(p));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Select(std::uintptr_t image,std::uintptr_t p)noexcept{__try{reinterpret_cast<void(__fastcall*)(void*)>(XAR_STOCK_BOOKMARK_CALL_ADDRESS(image,0x1B6CA10))(reinterpret_cast<void*>(p));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
}
bool VerifyStockBookmarkImage267V1([[maybe_unused]]std::uintptr_t image)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_STOCK_BOOKMARK1070_V1) && XAR_CK3_ENABLE_121003_26785313_STOCK_BOOKMARK1070_V1
 return image&&image==reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))&&VerifyLydImage267V1(image);
#else
 return false;
#endif
}
bool ReadStockBookmarkRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const StockBookmarkFrame267V1&f,[[maybe_unused]]const StockBookmarkRequest267V1&q,[[maybe_unused]]std::uint64_t mono,StockBookmarkRaw267V1&out,std::string&why)noexcept{out={};why="stock_bookmark1070_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_STOCK_BOOKMARK1070_V1) && XAR_CK3_ENABLE_121003_26785313_STOCK_BOOKMARK1070_V1
 try{if(!VerifyStockBookmarkImage267V1(b.module_base)||!Fresh(b,f,q,mono)){why="stock_bookmark1070_actual_image_core_or_deadline_unavailable";return false;}LydRequest267V1 read;read.action=LydAction267V1::query_events;read.expected=q.expected;read.deadline_unix_ms=q.deadline_unix_ms;read.request_id=q.request_id;read.request_id_size=q.request_id_size;if(!ReadLydRaw267V1(b,f.core,f.scene,mono,read,{},out.material,why))return false;if(!out.material.source.events||out.material.source.kind!=LydKind267V1::events||!out.material.cleanup_known){why="stock_bookmark1070_actual_complete_character_event_source_unavailable";return false;}Derive(*out.material.source.events,f.core.played_character_id,out.source);if(!StockBookmarkSourceShape267V1(out.source)||!Fresh(b,f,q,mono)){why="stock_bookmark1070_complete_source_or_final_core_changed";return false;}why.clear();return true;}catch(...){out.material.cleanup_known=!out.material.native_read_entered;why="stock_bookmark1070_actual_raw_exception";return false;}
#else
 return false;
#endif
}
StockBookmarkCall267V1 CallStockBookmarkRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const StockBookmarkFrame267V1&f,[[maybe_unused]]const StockBookmarkRequest267V1&q,[[maybe_unused]]std::uint64_t mono,[[maybe_unused]]const StockBookmarkRaw267V1&issued)noexcept{StockBookmarkCall267V1 call;
#if defined(XAR_CK3_ENABLE_121003_26785313_STOCK_BOOKMARK1070_V1) && XAR_CK3_ENABLE_121003_26785313_STOCK_BOOKMARK1070_V1
 try{if(q.action!=StockBookmarkAction267V1::select_c||!q.instance_id||q.instance_id!=issued.source.fixed_instance_id)return call;StockBookmarkRaw267V1 actual;std::string why;if(!ReadStockBookmarkRaw267V1(b,f,q,mono,actual,why)){call.cleanup_known=actual.material.cleanup_known;if(!call.cleanup_known)call.status=StockBookmarkCallStatus267V1::indeterminate;return call;}if(actual!=issued||!actual.source.select_c_admissible)return call;const auto p=Chosen(actual);if(!p||!Fresh(b,f,q,mono))return call;bool can=false;if(!Can(b.module_base,p,can)){call.cleanup_known=false;call.status=StockBookmarkCallStatus267V1::indeterminate;return call;}if(!can||!Fresh(b,f,q,mono))return call;call.entered=true;if(!Select(b.module_base,p)){call.cleanup_known=false;call.status=StockBookmarkCallStatus267V1::indeterminate;return call;}call.native_returned=true;call.status=Fresh(b,f,q,mono)?StockBookmarkCallStatus267V1::returned:StockBookmarkCallStatus267V1::indeterminate;return call;}catch(...){call.cleanup_known=false;call.status=StockBookmarkCallStatus267V1::indeterminate;return call;}
#endif
 return call;
}
}
