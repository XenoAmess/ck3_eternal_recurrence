#include "xar_bridge/ck3_1210_opening_readonly56.hpp"
#include "xar_bridge/ck3_121003_opening_readonly26785313_pins.hpp"
#include <algorithm>
#include <cstring>
#include <limits>
#include <type_traits>
#include <utility>
#if defined(_MSC_VER)
#include <windows.h>
#endif
namespace xar::ck3_1210 {namespace {
using namespace opening_profile56;
const ImageProfile *Profile(ImageBuildV1 build) noexcept {
 switch(build){
 case ImageBuildV1::hotfix26757580:return &kHotfix26757580;
 case ImageBuildV1::full11126785313:return &kFull11126785313;
 default:return nullptr;
 }
}
bool BuildEnabled(ImageBuildV1 build) noexcept {
 switch(build){
#if defined(XAR_CK3_ENABLE_26757580_OPENING_READONLY56)
 case ImageBuildV1::hotfix26757580:return true;
#endif
#if defined(XAR_CK3_ENABLE_26785313_OPENING_READONLY56)
 case ImageBuildV1::full11126785313:return true;
#endif
 default:return false;
 }
}
bool LocalCopy(void*,const void *source,void *dest,std::size_t size) noexcept {
 if(!source || !dest)return false;
#if defined(_MSC_VER)
 __try {
#endif
 std::memcpy(dest,source,size);return true;
#if defined(_MSC_VER)
 } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
bool Core(const CoreBindings &b,CoreSnapshotPrefix &p) noexcept {
#if defined(_MSC_VER)
 __try {
#endif
 return ReadCoreSnapshot(b,p);
#if defined(_MSC_VER)
 } __except(GetExceptionCode()==0xE06D7363UL?EXCEPTION_CONTINUE_SEARCH:EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
const void *Actor(const CoreBindings &b,std::int32_t id) noexcept {
#if defined(_MSC_VER)
 __try {
#endif
 return ResolveCoreCharacter(b,id);
#if defined(_MSC_VER)
 } __except(EXCEPTION_EXECUTE_HANDLER){return nullptr;}
#endif
}
bool Object(OpeningObjectGetter56 f,const void *actor,const void *&out) {
#if defined(_MSC_VER)
 __try {
#endif
 out=f(actor);return true;
#if defined(_MSC_VER)
 } __except(GetExceptionCode()==0xE06D7363UL?EXCEPTION_CONTINUE_SEARCH:EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
bool Name(OpeningNameGetter56 f,std::int32_t id,const void *&out) {
#if defined(_MSC_VER)
 __try {
#endif
 out=f(id);return true;
#if defined(_MSC_VER)
 } __except(GetExceptionCode()==0xE06D7363UL?EXCEPTION_CONTINUE_SEARCH:EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
bool Xp(OpeningXpGetter56 f,const void *actor,const void *style,bool within,std::int64_t &out) {
#if defined(_MSC_VER)
 __try {
#endif
 std::int64_t value=0;const auto result=f(actor,&value,style,within);
 if(result!=&value)return false;out=value;return true;
#if defined(_MSC_VER)
 } __except(GetExceptionCode()==0xE06D7363UL?EXCEPTION_CONTINUE_SEARCH:EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
bool Points(OpeningPointsGetter56 f,const void *actor,const void *style,std::int32_t &out) {
#if defined(_MSC_VER)
 __try {
#endif
 out=f(actor,style);return true;
#if defined(_MSC_VER)
 } __except(GetExceptionCode()==0xE06D7363UL?EXCEPTION_CONTINUE_SEARCH:EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
bool SameCore(const CoreSnapshotPrefix&a,const CoreSnapshotPrefix&b) noexcept {
 return a.clock.date_raw==b.clock.date_raw && a.clock.speed==b.clock.speed && a.clock.paused==b.clock.paused &&
 a.local_player_id==b.local_player_id && a.map_ready==b.map_ready && a.has_played_character==b.has_played_character &&
 a.played_character_id==b.played_character_id && a.played_character_alive==b.played_character_alive;
}
bool Utf8(std::string_view v) noexcept {
 for(std::size_t i=0;i<v.size();){const auto c=static_cast<unsigned char>(v[i++]);
  if(c<0x20 || c==0x7f)return false;if(c<0x80)continue;
  unsigned n=0;std::uint32_t code=0,minimum=0;
  if(c>=0xc2 && c<=0xdf){n=1;code=c&31;minimum=0x80;}
  else if(c>=0xe0 && c<=0xef){n=2;code=c&15;minimum=0x800;}
  else if(c>=0xf0 && c<=0xf4){n=3;code=c&7;minimum=0x10000;}else return false;
  if(n>v.size()-i)return false;
  while(n--){const auto d=static_cast<unsigned char>(v[i++]);if((d&0xc0)!=0x80)return false;code=(code<<6)|(d&63);}
  if(code<minimum || code>0x10ffff || (code>=0xd800 && code<=0xdfff))return false;
 }return true;
}
struct Cell {std::uintptr_t address=0;std::vector<std::byte> bytes;friend bool operator==(const Cell&,const Cell&)=default;};
struct Sample {
 const OpeningReadBindings56 &b;const ImageProfile &profile;const CoreSnapshotPrefix &expected;OpeningReadAccess56 access;
 std::size_t &calls;std::vector<Cell> cells;std::size_t string_bytes=0;
 std::string_view reason="opening_source_unavailable";
 OpeningGovernment56 government;OpeningLifestyle56 life;
 const void *actor=nullptr,*living=nullptr,*selected=nullptr,*style=nullptr;
 bool Raw(const void *src,void *dest,std::size_t size) noexcept {
  return (access.copy?access.copy:LocalCopy)(access.context,src,dest,size);
 }
 bool Copy(const void *base,std::size_t offset,void *dest,std::size_t size){
  const auto p=reinterpret_cast<std::uintptr_t>(base);const auto max=(std::numeric_limits<std::uintptr_t>::max)();
  if(!p || offset>max-p || size==0 || size-1>max-(p+offset) || cells.size()>=32768){reason="opening_copy_scope_invalid";return false;}
  Cell c{p+offset,{}};c.bytes.resize(size);
  if(!Raw(reinterpret_cast<const void*>(c.address),c.bytes.data(),size)){reason="opening_memory_read_failed";return false;}
  std::memcpy(dest,c.bytes.data(),size);cells.push_back(std::move(c));return true;
 }
 template<class T> bool Read(const void *base,std::size_t offset,T &out){static_assert(std::is_trivially_copyable_v<T>);return Copy(base,offset,&out,sizeof(T));}
 bool Stable() noexcept {
  std::array<std::byte,512> temp{};
  for(const auto &cell:cells){if(cell.bytes.size()>temp.size() || !Raw(reinterpret_cast<const void*>(cell.address),temp.data(),cell.bytes.size()) ||
    std::memcmp(temp.data(),cell.bytes.data(),cell.bytes.size())!=0){reason="opening_source_changed";return false;}}
  return true;
 }
 bool Admit() noexcept {
  if(!b.integration_native_calls_permitted || !b.native_call_admission || !b.native_call_admission(b.native_call_admission_context)){
   reason="opening_actor_owner_unqualified";return false;}return true;
 }
 template<class Fn> bool Before(Fn fn,const std::array<std::uint8_t,32>&pin){
  std::array<std::uint8_t,32> bytes{};
  if(!fn || !Copy(reinterpret_cast<const void*>(fn),0,bytes.data(),bytes.size()) || bytes!=pin){reason="opening_native_entry_mismatch";return false;}
  if(!Stable() || !Admit())return false;++calls;return true;
 }
 bool After(){if(!Admit() || !Stable())return false;CoreSnapshotPrefix p{};if(!Core(b.core,p) || !SameCore(p,expected)){reason="opening_core_changed";return false;}return true;}
 bool String(const void *base,std::size_t offset,std::string &out){
  struct Native {std::array<std::byte,16> data;std::uint64_t size,capacity;};Native h{};
  if(!Read(base,offset,h) || h.size==0 || h.size>256 || h.size>h.capacity || h.capacity>1048576 || h.size>65536-string_bytes){reason="opening_native_string_invalid";return false;}
  const void *ptr=nullptr;
  if(h.capacity<=15)ptr=static_cast<const std::byte*>(base)+offset;else std::memcpy(&ptr,h.data.data(),sizeof(ptr));
  std::array<char,257> bytes{};
  if(!Copy(ptr,0,bytes.data(),static_cast<std::size_t>(h.size)+1) || bytes[h.size]!=0 ||
    std::memchr(bytes.data(),0,static_cast<std::size_t>(h.size))){reason="opening_native_string_unterminated";return false;}
  out.assign(bytes.data(),static_cast<std::size_t>(h.size));string_bytes+=out.size();
  if(!Utf8(out)){reason="opening_native_string_utf8_invalid";return false;}return true;
 }
 bool Frame(){
  if(!Admit())return false;CoreSnapshotPrefix p{};
  if(!Core(b.core,p) || !SameCore(p,expected) || !p.clock.paused || !p.map_ready || !p.has_played_character || !p.played_character_alive || p.played_character_id==-1){reason="opening_expected_frame_unavailable";return false;}
  void *state=nullptr,*jomini=nullptr,*storage=nullptr,*data=nullptr;
  if(!Read(b.core.game_state_slot,0,state) || !Read(b.core.jomini_state_slot,0,jomini) || !Read(b.core.character_storage_slot,0,storage) ||
    !Read(state,kGameStateDataOffset,data) || !state || !jomini || !storage || !data)return false;
  actor=Actor(b.core,p.played_character_id);
  std::int32_t id=-1;std::uint32_t tag=0;const void *death=nullptr;
  if(!Read(actor,0x18,id) || !Read(actor,0x1c,tag) || !Read(actor,kCharacterDeathDataOffset,death) ||
    !Read(actor,0x1b0,living) || id!=p.played_character_id || tag!=0x43686172U || death){reason="opening_actor_generation_unavailable";return false;}
  return true;
 }
 bool Government(){
  if(!Frame())return false;const void *fallback=nullptr,*manager=nullptr;
  if(!Read(b.government_fallback_slot,0,fallback) || !fallback || !Read(b.identifier_manager_slot,0,manager) || !manager){reason="opening_government_globals_unavailable";return false;}
  // First profile uses the proven live-owned fast path. Do not enter the
  // getter's logger/fallback/ancestor branches when that source is missing.
  const void *owned=nullptr,*owned_government=nullptr;
  if(!Read(actor,0x1c0,owned) || !owned || !Read(owned,0x428,owned_government) || !owned_government || owned_government==fallback){
   reason="opening_owned_government_required";return false;}
  if(!Before(b.government,profile.government.pin) || !Object(b.government,actor,selected) || !After())return false;
  if(!selected || selected==fallback || selected!=owned_government){reason="opening_government_not_observed";return false;}
  std::uintptr_t vt=0;std::uint32_t tag=0;const void *ids=nullptr;
  if(!Read(selected,0,vt) || !Read(selected,0x38,tag) || vt!=b.government_vtable || tag!=0x4744624fU ||
    !String(selected,0x18,government.key) || !Read(selected,0x50,ids) || !Read(selected,0x5c,government.native_flag_count))return false;
  if(government.native_flag_count<0 || government.native_flag_count>4096 || (government.native_flag_count && !ids)){reason="opening_government_flags_incomplete";return false;}
  const void *table=nullptr;std::int32_t bound=-1;
  if(!Read(manager,0x48,table) || !Read(manager,0x54,bound) || bound<0 || bound>1048576 || (government.native_flag_count && !table))return false;
  government.flags.reserve(static_cast<std::size_t>(government.native_flag_count));std::int32_t prior=-1;
  for(std::int32_t i=0;i<government.native_flag_count;++i){
   std::int32_t id=-1;const void *name=nullptr,*table_name=nullptr;
   if(!Read(ids,static_cast<std::size_t>(i)*4,id) || id<0 || id<prior || id>bound ||
     !Read(table,static_cast<std::size_t>(id)*sizeof(void*),table_name) || !table_name){reason="opening_government_identifier_invalid";return false;}
   prior=id;
   if(!Before(b.identifier_name,profile.identifier_name.pin) || !Name(b.identifier_name,id,name) || !After())return false;
   if(!name || name==b.identifier_missing_string || name!=table_name){reason="opening_government_name_unavailable";return false;}
   std::string text;if(!String(name,0,text))return false;government.flags.push_back(std::move(text));
  }
  return After();
 }
 bool Lifestyle(){
  if(!Frame())return false;if(!living){reason="opening_living_required_for_current_progress";return false;}
  const void *fallback=nullptr;
  if(!Read(b.focus_fallback_slot,0,fallback) || !fallback){reason="opening_focus_default_uninitialized";return false;}
  const void *focus_owner=nullptr,*source_focus=nullptr;
  if(!Read(living,0x280,focus_owner) || !focus_owner || !Read(focus_owner,8,source_focus) || !source_focus || source_focus==fallback){
   reason="opening_focus_absence_progress_unverified";return false;}
  if(!Before(b.focus,profile.focus.pin) || !Object(b.focus,actor,selected) || !After())return false;
  if(!selected || selected==fallback || selected!=source_focus){reason="opening_focus_absence_progress_unverified";return false;}
  std::uintptr_t focus_type=0,style_type=0;const void *associated=nullptr;
  if(!Read(selected,0,focus_type) || focus_type!=b.focus_vtable || !String(selected,0x18,life.focus_key) || !Read(selected,0x5c8,associated))return false;
  if(!Before(b.lifestyle,profile.lifestyle.pin) || !Object(b.lifestyle,actor,style) || !After())return false;
  if(!style || style!=associated || !Read(style,0,style_type) || style_type!=b.lifestyle_vtable ||
    !String(style,0x18,life.lifestyle_key) || !Read(style,0xc8,life.xp_per_level) || life.xp_per_level<1){reason="opening_current_lifestyle_unavailable";return false;}
  const void *rows=nullptr;std::int32_t count=0,capacity=0;
  if(!Read(living,0x208,rows) || !Read(living,0x210,capacity) || !Read(living,0x214,count) || capacity<0 ||
    count<0 || count>capacity || capacity>65536 || (capacity && !rows)){reason="opening_xp_header_invalid";return false;}
  bool found=false;std::int64_t expected_raw=0;
  for(std::int32_t i=0;i<count;++i){const void *row_style=nullptr;std::int64_t raw=0;
   if(!Read(rows,static_cast<std::size_t>(i)*16,row_style) || !Read(rows,static_cast<std::size_t>(i)*16+8,raw) || !row_style)return false;
   if(row_style==style){if(found){reason="opening_xp_duplicate_style";return false;}found=true;expected_raw=raw;}
  }
  if(expected_raw<0 || expected_raw/100000>(std::numeric_limits<std::int32_t>::max)()){reason="opening_xp_native_narrowing_unqualified";return false;}
  if(!Before(b.xp,profile.xp.pin) || !Xp(b.xp,actor,style,false,life.xp_total_raw) || !After() ||
    life.xp_total_raw!=expected_raw){reason="opening_xp_total_abi_or_source_mismatch";return false;}
  if(!Before(b.xp,profile.xp.pin) || !Xp(b.xp,actor,style,true,life.xp_within_level_raw) || !After() ||
    life.xp_within_level_raw!=expected_raw%(static_cast<std::int64_t>(life.xp_per_level)*100000)){reason="opening_xp_within_abi_or_source_mismatch";return false;}
  if(!Before(b.points,profile.points.pin) || !Points(b.points,actor,style,life.unspent_perk_points) || !After() ||
    life.unspent_perk_points<0 || life.unspent_perk_points!=expected_raw/100000/life.xp_per_level){reason="opening_points_abi_or_source_mismatch";return false;}
  const void *owned=nullptr;std::int32_t owned_count=0;
  if(!Read(living,0x220,owned) || !Read(living,0x22c,owned_count) || owned_count<0 || owned_count>512 || (owned_count && !owned)){
   reason="opening_used_counter_scope_unavailable";return false;}
  std::int32_t used=0;
  for(std::int32_t i=0;i<owned_count;++i){const void *perk=nullptr,*perk_style=nullptr;
   if(!Read(owned,static_cast<std::size_t>(i)*sizeof(void*),perk) || !perk || !Read(perk,0x390,perk_style))return false;
   if(perk_style==style)++used;
  }
  if(!Before(b.used,profile.used.pin) || !Points(b.used,actor,style,life.used_perk_points) || !After() ||
    life.used_perk_points<0 || life.used_perk_points!=used){reason="opening_used_counter_abi_or_source_mismatch";return false;}
  // No owned-perk keys, membership completeness or action permission is emitted.
  return After();
 }
};
}
OpeningReadBindings56 BindOpeningReadImage56(std::uintptr_t base,std::string_view sha) noexcept {
 OpeningReadBindings56 b{};b.core=BindCoreImage(base,sha);
 const auto *profile=Profile(b.core.image_build);
 if(!b.core.enabled || !profile || !BuildEnabled(b.core.image_build))return b;
 b.government=reinterpret_cast<OpeningObjectGetter56>(base+profile->government.rva);
 b.identifier_name=reinterpret_cast<OpeningNameGetter56>(base+profile->identifier_name.rva);
 b.focus=reinterpret_cast<OpeningObjectGetter56>(base+profile->focus.rva);
 b.lifestyle=reinterpret_cast<OpeningObjectGetter56>(base+profile->lifestyle.rva);
 b.xp=reinterpret_cast<OpeningXpGetter56>(base+profile->xp.rva);
 b.points=reinterpret_cast<OpeningPointsGetter56>(base+profile->points.rva);
 b.used=reinterpret_cast<OpeningPointsGetter56>(base+profile->used.rva);
 b.government_fallback_slot=reinterpret_cast<void**>(base+profile->government_fallback);
 b.identifier_manager_slot=reinterpret_cast<void**>(base+profile->identifier_manager);
 b.focus_fallback_slot=reinterpret_cast<void**>(base+profile->focus_fallback);
 b.identifier_missing_string=reinterpret_cast<const void*>(base+profile->missing_identifier);
 b.government_vtable=base+profile->government_vtable;
 b.focus_vtable=base+profile->focus_vtable;
 b.lifestyle_vtable=base+profile->lifestyle_vtable;
 b.exact_build_admitted=true;return b;
}
bool ReadOpeningReadonly56(const OpeningReadBindings56 &b,const CoreSnapshotPrefix &expected,OpeningReadKind56 kind,
 OpeningReadObservation56 &out,OpeningReadAccess56 access) noexcept {
 out={};out.kind=kind;std::size_t calls=0;std::string_view reason="opening_exact_binding_unavailable";
 try {
  const auto *profile=Profile(b.core.image_build);
  if(!b.exact_build_admitted || !b.core.enabled || !profile ||
    !b.integration_native_calls_permitted || !b.native_call_admission){out.unavailable_reason=reason;return false;}
  Sample first{b,*profile,expected,access,calls},second{b,*profile,expected,access,calls};
  const auto read=[&](Sample &s){return kind==OpeningReadKind56::government_scope?s.Government():s.Lifestyle();};
  if(!read(first)){reason=first.reason;}else if(!read(second)){reason=second.reason;}
  else if(first.cells!=second.cells || first.selected!=second.selected || first.style!=second.style ||
    first.government!=second.government || first.life!=second.life || !first.Stable() || !second.Stable() || !first.Admit() || !second.Admit())reason="opening_two_samples_changed";
  else {
   out.available=true;out.frame=expected;out.native_call_attempts=calls;out.unavailable_reason={};
   if(kind==OpeningReadKind56::government_scope)out.government=std::move(second.government);else out.lifestyle=std::move(second.life);
   return true;
  }
 }catch(...){reason="opening_reader_cpp_exception";}
 out={};out.kind=kind;out.native_call_attempts=calls;out.unavailable_reason=reason;return false;
}
}
