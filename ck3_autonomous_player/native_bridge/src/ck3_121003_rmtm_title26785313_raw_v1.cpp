#include "ck3_121003_rmtm_title26785313_raw_v1.hpp"
#include "ck3_121003_rmtm_title26785313_pins_v1.hpp"
#include <algorithm>
#include <bit>
#include <chrono>
#include <cstring>
#include <limits>
#include <windows.h>
#ifndef XAR_RMTM_TITLE_CALL_ADDRESS
#define XAR_RMTM_TITLE_CALL_ADDRESS(image,rva) ((image)+(rva))
#endif
namespace xar::ck3_121003::build26785313 {namespace rmtm_title_private {
constexpr std::uint32_t invalid=0xFFFFFFFFU;
constexpr std::uintptr_t title_storage_rva=0x6A66648,title_fallback_rva=0x6A66638;
constexpr std::uintptr_t char_fallback_rva=0x68A8930,current_heir_object_rva=0x69487B0;
bool Copy(std::uintptr_t p,void*out,std::size_t n)noexcept {
 if(!p||!out||!n||n-1>(std::numeric_limits<std::uintptr_t>::max)()-p)return false;
 __try{std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
template<class T>bool At(std::uintptr_t p,std::size_t offset,T&v)noexcept {
 return p&&offset<=(std::numeric_limits<std::uintptr_t>::max)()-p&&Copy(p+offset,&v,sizeof(v));
}
bool Time(std::uint64_t wall,std::uint64_t mono)noexcept {
 const auto n=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
 return n>0&&wall&&mono&&static_cast<std::uint64_t>(n)<wall&&GetTickCount64()<mono;
}
bool Same(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept {
 return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&
 a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&
 a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;
}
bool Fresh(const ReadonlyBindings&b,const RmtmTitleFrame267V1&f,const RmtmTitleRequest267V1&q,std::uint64_t mono)noexcept {
 if(!b.exact_image_admitted||!f.facts_verified||!Same(f.core,q.expected)||!f.core.clock.paused||!f.core.map_ready||
 !f.core.has_played_character||!f.core.played_character_alive||f.core.played_character_id==-1||!Time(q.deadline_unix_ms,mono))return false;
 __try{ck3_1210::CoreSnapshotPrefix c;std::uintptr_t d=0,p=0;std::uint32_t id=invalid,magic=0;
 return ck3_1210::ReadCoreSnapshot(b.core,c)&&Same(c,f.core)&&
 reinterpret_cast<std::uintptr_t>(*b.core.game_state_slot)==f.game&&reinterpret_cast<std::uintptr_t>(*b.core.jomini_state_slot)==f.jomini&&
 reinterpret_cast<std::uintptr_t>(*b.core.character_storage_slot)==f.storage&&At(f.game,0xA0,d)&&d==f.data&&
 At(f.jomini,0x18,p)&&p==f.players&&reinterpret_cast<std::uintptr_t>(b.core.get_local_player(reinterpret_cast<void*>(f.jomini)))==f.player&&
 reinterpret_cast<std::uintptr_t>(ck3_1210::ResolveCoreCharacter(b.core,c.played_character_id))==f.actor&&
 At(f.actor,0x18,id)&&id==static_cast<std::uint32_t>(c.played_character_id)&&At(f.actor,0x1C,magic)&&magic==0x43686172U&&Time(q.deadline_unix_ms,mono);
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool Resolve(std::uintptr_t storage,std::uintptr_t fallback,std::uint32_t id,std::size_t id_offset,std::uintptr_t&out)noexcept {
 out=0;if(!storage||id==invalid)return false;std::uint32_t cap=0,actual=invalid;std::uintptr_t rows=0,p=0;
 const auto index=id&0xFFFFFFU;
 if(!At(storage,0x2C,cap)||index>=cap||!At(storage,0x20,rows)||!rows||
 !At(rows,static_cast<std::size_t>(index)*16+8,p)||!p||p==fallback||!At(p,id_offset,actual)||actual!=id)return false;
 out=p;return true;
}
bool Character(const ReadonlyBindings&b,const RmtmTitleFrame267V1&f,std::uint32_t id,std::uintptr_t expected,RmtmTitleCharacter267V1&out)noexcept {
 std::uintptr_t fallback=0,p=0,dead=0;std::uint32_t magic=0;
 if(!At(b.module_base,char_fallback_rva,fallback)||!Resolve(f.storage,fallback,id,0x18,p)||
 (expected&&p!=expected)||!At(p,0x1C,magic)||magic!=0x43686172U||!At(p,0x1D0,dead))return false;
 __try{if(ck3_1210::ResolveCoreCharacter(b.core,std::bit_cast<std::int32_t>(id))!=reinterpret_cast<void*>(p))return false;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
 // Official current859 Character.IsAlive: valid Character, death pointer zero.
 out={id,dead==0};return true;
}
struct Array16 {std::uintptr_t data=0;std::int32_t capacity=0,count=0;friend bool operator==(const Array16&,const Array16&)=default;};
static_assert(sizeof(Array16)==16);
// Script CScopeObjectReference: the official current_heir leaf checks input
// kind WORD=5 and full DWORD at+8, then emits kind DWORD=4 and zero-extended ID.
struct Scope16 {std::uint32_t kind=0,reserved=0;std::uint64_t full_id=0;};
static_assert(sizeof(Scope16)==16);
bool PtrCall(std::uintptr_t image,std::uintptr_t rva,std::uintptr_t self,std::uintptr_t&out)noexcept {
 using Fn=const void*(__fastcall*)(const void*);
 __try{out=reinterpret_cast<std::uintptr_t>(reinterpret_cast<Fn>(XAR_RMTM_TITLE_CALL_ADDRESS(image,rva))(reinterpret_cast<const void*>(self)));return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){out=0;return false;}
}
bool HeirCall(std::uintptr_t image,std::uint32_t title_id,Scope16&out)noexcept {
 const Scope16 in{5,0,title_id};const Scope16*root=&in;
 using Fn=Scope16*(__fastcall*)(const void*,Scope16*,const Scope16*const*);
 __try{return reinterpret_cast<Fn>(XAR_RMTM_TITLE_CALL_ADDRESS(image,0x1F27FC0))(
 reinterpret_cast<void*>(image+current_heir_object_rva),&out,&root)==&out;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
struct LawSnapshot {std::uintptr_t object=0;std::uint32_t id=invalid;std::array<unsigned char,32>header{};std::string key;friend bool operator==(const LawSnapshot&,const LawSnapshot&)=default;};
bool Law(std::uintptr_t image,std::uintptr_t p,LawSnapshot&out) {
 std::uintptr_t vt=0;std::uint32_t magic=0;std::uint64_t n=0,cap=0;std::uintptr_t data=0;
 if(!At(p,0,vt)||vt!=image+0x4FFAF78||!At(p,0x10,out.id)||out.id==invalid||!At(p,0x38,magic)||magic!=0x4744624FU||
 !Copy(p+0x18,out.header.data(),out.header.size()))return false;
 std::memcpy(&n,out.header.data()+16,8);std::memcpy(&cap,out.header.data()+24,8);
 if(!n||n>256||cap<n||(cap<=15&&n>15))return false;
 if(cap>15)std::memcpy(&data,out.header.data(),8);else data=p+0x18;
 std::array<char,257>key{};if(!Copy(data,key.data(),static_cast<std::size_t>(n)+1)||key[static_cast<std::size_t>(n)]!=0)return false;
 // Script definition key, never localized text. No zero/truncation or fallback.
 for(std::size_t i=0;i<n;++i){const unsigned char c=key[i];if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'||c=='.'||c==':'||c=='-'))return false;}
 out.object=p;out.key.assign(key.data(),static_cast<std::size_t>(n));return true;
}
struct Snapshot {
 RmtmTitleSource267V1 source;std::uintptr_t title=0,title_storage=0,title_fallback=0,char_fallback=0,holder=0,heir=0;
 Array16 own{};std::array<unsigned char,16>engine_header{};std::vector<LawSnapshot>laws;
 friend bool operator==(const Snapshot&,const Snapshot&)=default;
};
bool Take(const ReadonlyBindings&b,const RmtmTitleFrame267V1&f,const RmtmTitleRequest267V1&q,std::uint64_t mono,Snapshot&out,RmtmTitleRaw267V1&state,std::string&why) {
 const auto image=b.module_base;const auto fail=[&](const char*s){why=s;return false;};
 if(!Fresh(b,f,q,mono))return fail("rmtm_title_actual_core_owner_source_unavailable");
 if(!At(image,title_storage_rva,out.title_storage)||!At(image,title_fallback_rva,out.title_fallback)||
 !At(image,char_fallback_rva,out.char_fallback)||!Resolve(out.title_storage,out.title_fallback,q.expected_full_title_id,0x10,out.title))return fail("rmtm_full_title_generation_unavailable");
 std::uintptr_t vt=0,returned=0;std::uint32_t id=invalid,magic=0,holder_id=invalid;
 if(!At(out.title,0,vt)||vt!=image+0x4E21980||!At(out.title,0x10,id)||id!=q.expected_full_title_id||
 !At(out.title,0x14,magic)||magic!=0x4C616E64U)return fail("rmtm_actual_landed_title_type_unavailable");
 state.entered=true;
 if(!PtrCall(image,0x2D83960,f.actor,returned)){state.cleanup_known=false;return fail("rmtm_primary_title_read_exception_unknown");}
 if(returned!=out.title||!Fresh(b,f,q,mono))return fail("rmtm_actual_primary_full_title_guard_changed");
 if(!At(out.title,0x168,holder_id)||!Time(q.deadline_unix_ms,mono))return fail("rmtm_holder_source_unavailable");
 if(!PtrCall(image,0x2704B40,out.title,out.holder)){state.cleanup_known=false;return fail("rmtm_holder_read_exception_unknown");}
 if(!Fresh(b,f,q,mono))return fail("rmtm_holder_post_read_source_changed");
 if(holder_id==invalid){if(out.holder!=out.char_fallback)return fail("rmtm_none_holder_pointer_mismatch");}
 else{RmtmTitleCharacter267V1 c;if(!Character(b,f,holder_id,out.holder,c))return fail("rmtm_holder_full_character_unavailable");out.source.holder=c;}
 if(!PtrCall(image,0xE18850,out.title,returned)){state.cleanup_known=false;return fail("rmtm_own_law_header_read_exception_unknown");}
 if(returned!=out.title+0x270||!Fresh(b,f,q,mono)||!Copy(returned,&out.own,sizeof(out.own))||out.own.capacity<0||out.own.count<0||
 out.own.count>out.own.capacity||out.own.count>64||(out.own.count&&!out.own.data))return fail("rmtm_own_law_complete_array_unavailable");
 for(std::int32_t i=0;i<out.own.count;++i){std::uintptr_t law=0;LawSnapshot row;
  if(!At(out.own.data,static_cast<std::size_t>(i)*8,law)||!Law(image,law,row))return fail("rmtm_own_law_definition_unavailable");
  if(std::any_of(out.laws.begin(),out.laws.end(),[&](const auto&x){return x.object==row.object||x.id==row.id||x.key==row.key;}))return fail("rmtm_own_law_duplicate_unavailable");
  out.source.physical_own_laws.push_back({row.id,row.key});out.laws.push_back(std::move(row));
 }
 // Full 16-byte engine header is compared, but its middle DWORD is deliberately
 // opaque. current_heir proves only data+0/count+C and its first DWORD item.
 if(!Copy(out.title+0x190,out.engine_header.data(),16))return fail("rmtm_engine_heir_header_unavailable");
 std::uintptr_t successors=0;std::int32_t count=0;std::memcpy(&successors,out.engine_header.data(),8);std::memcpy(&count,out.engine_header.data()+12,4);
 if(count<0||count>4096||(count&&!successors))return fail("rmtm_engine_heir_array_unavailable");
 std::uint32_t first=invalid;if(count&&(!At(successors,0,first)||first==invalid))return fail("rmtm_engine_heir_first_ref_unavailable");
 if(!At(image+current_heir_object_rva,0,vt)||vt!=image+0x4CDD140||!Time(q.deadline_unix_ms,mono))return fail("rmtm_current_heir_link_type_or_deadline_unavailable");
 Scope16 scoped{};if(!HeirCall(image,id,scoped)){state.cleanup_known=false;return fail("rmtm_current_heir_read_exception_unknown");}
 if(scoped.kind!=4||scoped.reserved!=0||scoped.full_id!=first||!Fresh(b,f,q,mono))return fail("rmtm_current_heir_full_scope_or_source_changed");
 if(count){RmtmTitleCharacter267V1 c;std::uintptr_t h=0;if(!Resolve(f.storage,out.char_fallback,first,0x18,h)||!Character(b,f,first,h,c))return fail("rmtm_engine_heir_full_character_unavailable");out.heir=h;out.source.engine_current_heir=c;}
 out.source.full_title_id=id;out.source.native_law_count=out.own.count;out.source.engine_successor_count=count;
 return Fresh(b,f,q,mono);
}
}
bool VerifyRmtmTitleImage267V1([[maybe_unused]]std::uintptr_t image)noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_V1
 using namespace rmtm_title_private;if(!image||image!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))||!VerifyReadonlyImage(image))return false;
 std::array<unsigned char,512>bytes{};for(const auto&p:rmtm_title_pins::kPins)if(p.bytes.empty()||p.bytes.size()>bytes.size()||p.rva>kImageSize-p.bytes.size()||!Copy(image+p.rva,bytes.data(),p.bytes.size())||std::memcmp(bytes.data(),p.bytes.data(),p.bytes.size()))return false;
 for(const auto&p:rmtm_title_pins::kPointers){std::uintptr_t value=0;if(!At(image,p.slot,value)||value!=image+p.target)return false;}return true;
#else
 return false;
#endif
}
bool ReadRmtmTitleRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const RmtmTitleFrame267V1&f,
 [[maybe_unused]]const RmtmTitleRequest267V1&q,[[maybe_unused]]std::uint64_t mono,RmtmTitleRaw267V1&out,std::string&why)noexcept {
 out={};why="rmtm_title_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_V1
 using namespace rmtm_title_private;try{if(q.expected_full_title_id==invalid||!VerifyRmtmTitleImage267V1(b.module_base)||!Fresh(b,f,q,mono))return false;
 Snapshot a,z;if(!Take(b,f,q,mono,a,out,why)||!Take(b,f,q,mono,z,out,why))return false;
 if(a!=z){why="rmtm_actual_title_laws_holder_heir_changed_between_samples";return false;}
 out.source=std::move(z.source);out.source.sampled_twice=true;why.clear();return true;
 }catch(...){out.source={};why="rmtm_title_local_copy_unavailable";return false;}
#endif
 return false;
}
}
