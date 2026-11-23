#include "xar_bridge/ck3_121003_rmtm_title_query26785313_owner_v1.hpp"
#include <chrono>
#include <cstring>
#include <limits>
#include <windows.h>
#ifndef XAR_RMTM_TITLE_QUERY_CALL_ADDRESS
#define XAR_RMTM_TITLE_QUERY_CALL_ADDRESS(image,rva) ((image)+(rva))
#endif
namespace xar::ck3_121003::build26785313 {namespace {
[[maybe_unused]]bool TitleQueryCopy(std::uintptr_t p,void*out,std::size_t n)noexcept{if(!p||!out||!n||n-1>(std::numeric_limits<std::uintptr_t>::max)()-p)return false;__try{std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
template<class T>bool TitleQueryAt(std::uintptr_t p,std::size_t n,T&out)noexcept{return p&&n<=(std::numeric_limits<std::uintptr_t>::max)()-p&&TitleQueryCopy(p+n,&out,sizeof(out));}
[[maybe_unused]]bool TitleQuerySame(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool TitleQueryTime(std::uint64_t wall,std::uint64_t mono)noexcept{const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return t>0&&wall&&mono&&static_cast<std::uint64_t>(t)<wall&&GetTickCount64()<mono;}
[[maybe_unused]]bool TitleQueryFresh(const ReadonlyBindings&b,const RmtmTitleFrame267V1&f,const RmtmTitleQueryRequest267V1&q,std::uint64_t mono)noexcept{
 if(!b.exact_image_admitted||!f.facts_verified||!TitleQuerySame(f.core,q.expected)||!TitleQueryTime(q.deadline_unix_ms,mono))return false;
 __try{ck3_1210::CoreSnapshotPrefix c;std::uint32_t id=0xFFFFFFFFU,magic=0;return ck3_1210::ReadCoreSnapshot(b.core,c)&&TitleQuerySame(c,f.core)&&reinterpret_cast<std::uintptr_t>(*b.core.game_state_slot)==f.game&&reinterpret_cast<std::uintptr_t>(*b.core.jomini_state_slot)==f.jomini&&reinterpret_cast<std::uintptr_t>(*b.core.character_storage_slot)==f.storage&&reinterpret_cast<std::uintptr_t>(ck3_1210::ResolveCoreCharacter(b.core,c.played_character_id))==f.actor&&TitleQueryAt(f.actor,0x18,id)&&id==static_cast<std::uint32_t>(c.played_character_id)&&TitleQueryAt(f.actor,0x1C,magic)&&magic==0x43686172U&&TitleQueryTime(q.deadline_unix_ms,mono);}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool TitleQueryPrimaryCall(std::uintptr_t image,std::uintptr_t actor,std::uintptr_t&out)noexcept{using Fn=const void*(__fastcall*)(const void*);__try{out=reinterpret_cast<std::uintptr_t>(reinterpret_cast<Fn>(XAR_RMTM_TITLE_QUERY_CALL_ADDRESS(image,0x2D83960))(reinterpret_cast<const void*>(actor)));return true;}__except(EXCEPTION_EXECUTE_HANDLER){out=0;return false;}}
}
bool CaptureRmtmTitleQueryPrimary267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const RmtmTitleFrame267V1&f,[[maybe_unused]]const RmtmTitleQueryRequest267V1&q,[[maybe_unused]]std::uint64_t mono,std::uint32_t&out,bool&entered,bool&cleanup,std::string&why)noexcept{
 out=0xFFFFFFFFU;why="rmtm_title_query_capture_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_QUERY_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_QUERY_V1 && defined(XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_V1
 if(!VerifyRmtmTitleImage267V1(b.module_base)||!TitleQueryFresh(b,f,q,mono)){why="rmtm_title_query_actual_capture_source_unavailable";return false;}
 entered=true;std::uintptr_t title=0;
 if(!TitleQueryPrimaryCall(b.module_base,f.actor,title)){cleanup=false;why="rmtm_title_query_actual_primary_capture_exception_unknown";return false;}
 std::uintptr_t vt=0,storage=0,fallback=0,rows=0,resolved=0;std::uint32_t id=0xFFFFFFFFU,magic=0,cap=0,actual=0xFFFFFFFFU;
 if(!TitleQueryFresh(b,f,q,mono)||!TitleQueryAt(b.module_base,0x6A66648,storage)||!storage||!TitleQueryAt(b.module_base,0x6A66638,fallback)||!title||title==fallback||!TitleQueryAt(title,0,vt)||vt!=b.module_base+0x4E21980||!TitleQueryAt(title,0x10,id)||id==0xFFFFFFFFU||!TitleQueryAt(title,0x14,magic)||magic!=0x4C616E64U||!TitleQueryAt(storage,0x2C,cap)||(id&0xFFFFFFU)>=cap||!TitleQueryAt(storage,0x20,rows)||!TitleQueryAt(rows,static_cast<std::size_t>(id&0xFFFFFFU)*16+8,resolved)||resolved!=title||!TitleQueryAt(resolved,0x10,actual)||actual!=id||!TitleQueryFresh(b,f,q,mono)){why="rmtm_title_query_actual_primary_full_generation_unavailable";return false;}
 out=id;why.clear();return true;
#else
 (void)entered;(void)cleanup;return false;
#endif
}
}
