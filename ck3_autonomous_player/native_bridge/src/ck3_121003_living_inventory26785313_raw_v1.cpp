#include "xar_bridge/ck3_121003_living_inventory26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_living_fixture_bindings26785313_v1.hpp"
#include <algorithm>
#include <bit>
#include <chrono>
#include <cstring>
#include <limits>
#include <windows.h>
#ifndef XAR_LIVING_INVENTORY_CALL_ADDRESS
#define XAR_LIVING_INVENTORY_CALL_ADDRESS(image,rva) ((image)+(rva))
#endif
namespace xar::ck3_121003::build26785313 { namespace living_inventory_private {
constexpr std::uint32_t invalid=0xFFFFFFFFU;
constexpr std::size_t artifact_limit=128,slot_limit=64,string_limit=4096;
bool Copy(std::uintptr_t p,void*out,std::size_t n)noexcept {
 if(!p||!out||!n||n-1>(std::numeric_limits<std::uintptr_t>::max)()-p)return false;
 __try{std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
template<class T>bool At(std::uintptr_t p,std::size_t off,T&v)noexcept {
 return p&&off<=(std::numeric_limits<std::uintptr_t>::max)()-p&&Copy(p+off,&v,sizeof(v));
}
bool Time(std::uint64_t wall,std::uint64_t mono)noexcept {
 const auto n=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
 return n>0&&wall&&mono&&static_cast<std::uint64_t>(n)<wall&&GetTickCount64()<mono;
}
bool Same(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&z)noexcept {
 return a.clock.date_raw==z.clock.date_raw&&a.clock.speed==z.clock.speed&&a.clock.paused==z.clock.paused&&
 a.local_player_id==z.local_player_id&&a.map_ready==z.map_ready&&a.has_played_character==z.has_played_character&&
 a.played_character_id==z.played_character_id&&a.played_character_alive==z.played_character_alive;
}
bool Fresh(const ReadonlyBindings&b,const LivingInventoryFrame267V1&f,
 const LivingInventoryRequest267V1&q,std::uint64_t mono)noexcept {
 if(!b.exact_image_admitted||!b.module_base||!f.facts_verified||!f.connection_generation||
 !Same(f.core,q.expected)||!f.core.clock.paused||!f.core.map_ready||!f.core.has_played_character||
 !f.core.played_character_alive||f.core.played_character_id==-1||!Time(q.deadline_unix_ms,mono))return false;
#if defined(XAR_CK3_26785313_OFFLINE_FIXTURE)
 if(b.offline_fixture)return false;
#endif
 __try{ck3_1210::CoreSnapshotPrefix actual;std::uintptr_t data=0,players=0;std::uint32_t id=invalid,magic=0;
 return ck3_1210::ReadCoreSnapshot(b.core,actual)&&Same(actual,f.core)&&
 reinterpret_cast<std::uintptr_t>(*b.core.game_state_slot)==f.game&&
 reinterpret_cast<std::uintptr_t>(*b.core.jomini_state_slot)==f.jomini&&
 reinterpret_cast<std::uintptr_t>(*b.core.character_storage_slot)==f.character_storage&&
 At(f.game,0xA0,data)&&data==f.data&&At(f.jomini,0x18,players)&&players==f.players&&
 reinterpret_cast<std::uintptr_t>(b.core.get_local_player(reinterpret_cast<void*>(f.jomini)))==f.player&&
 reinterpret_cast<std::uintptr_t>(ck3_1210::ResolveCoreCharacter(b.core,actual.played_character_id))==f.actor&&
 At(f.actor,0x18,id)&&id==std::bit_cast<std::uint32_t>(actual.played_character_id)&&
 At(f.actor,0x1C,magic)&&magic==0x43686172U&&Time(q.deadline_unix_ms,mono);
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
struct Array16 {std::uintptr_t data=0;std::int32_t capacity=0,count=0;friend bool operator==(const Array16&,const Array16&)=default;};
static_assert(sizeof(Array16)==16);
bool Array(const Array16&a,std::size_t bound,std::size_t stride)noexcept {
 return a.count>=0&&a.capacity>=a.count&&static_cast<std::size_t>(a.count)<=bound&&
 (!a.count||(a.data&&static_cast<std::size_t>(a.count)<=(std::numeric_limits<std::uintptr_t>::max)()/stride&&
 static_cast<std::size_t>(a.count)*stride-1<=(std::numeric_limits<std::uintptr_t>::max)()-a.data));
}
// Diagnostics only: Array remains the sole unchanged acceptance predicate.
// Never serialize the data address or dereference rejected array elements.
const char* ArrayIssue(const Array16&a,std::size_t bound,std::size_t stride)noexcept {
 if(a.count<0)return "negative_count";
 if(a.capacity<a.count)return "capacity_below_count";
 if(static_cast<std::size_t>(a.count)>bound)return "count_exceeds_bound";
 if(a.count&&!a.data)return "nonnull_data_required";
 if(a.count&&(static_cast<std::size_t>(a.count)>(std::numeric_limits<std::uintptr_t>::max)()/stride||
 static_cast<std::size_t>(a.count)*stride-1>(std::numeric_limits<std::uintptr_t>::max)()-a.data))return "span_overflow";
 return "predicate_inconsistent";
}
void AppendArrayDiagnostic(std::string&why,const char*name,const Array16&a,bool read,
 std::size_t bound,std::size_t stride) {
 const auto field=[&](const char*key,const std::string&value){why+=';';why+=name;why+=key;why+=value;};
 field("_read=",read?"1":"0");
 if(!read)return; // Partial Copy bytes are not diagnostic DATA.
 field("_count=",std::to_string(a.count));field("_capacity=",std::to_string(a.capacity));
 field("_data_nonnull=",a.data?"1":"0");
 field("_count_oob=",a.count>=0&&static_cast<std::size_t>(a.count)>bound?"1":"0");
 const bool overflow=a.count>0&&(static_cast<std::size_t>(a.count)>(std::numeric_limits<std::uintptr_t>::max)()/stride||
 static_cast<std::size_t>(a.count)*stride-1>(std::numeric_limits<std::uintptr_t>::max)()-a.data);
 field("_span_oob=",overflow?"1":"0");
}
bool ReadInventoryArrays(std::uintptr_t inventory,Array16&artifacts,Array16&slots,std::string&why) {
 bool artifacts_read=false,slots_read=false;
 const auto fail=[&](const char*field,const char*issue){
  why="living_inventory_complete_arrays_unavailable;field=";why+=field;why+=";issue=";why+=issue;
  AppendArrayDiagnostic(why,"artifacts",artifacts,artifacts_read,artifact_limit,4);
  AppendArrayDiagnostic(why,"slots",slots,slots_read,slot_limit,24);return false;
 };
 // Preserve the old OR expression's read and validation order exactly.
 artifacts_read=At(inventory,0x58,artifacts);
 if(!artifacts_read)return fail("artifacts_header","unreadable");
 slots_read=At(inventory,0x40,slots);
 if(!slots_read)return fail("slots_header","unreadable");
 if(!Array(artifacts,artifact_limit,4))return fail("artifacts",ArrayIssue(artifacts,artifact_limit,4));
 if(!Array(slots,slot_limit,24))return fail("slots",ArrayIssue(slots,slot_limit,24));
 return true;
}
struct String32 {std::array<std::byte,32>header{};std::string value;friend bool operator==(const String32&,const String32&)=default;};
bool String(std::uintptr_t p,String32&out) {
 std::uint64_t n=0,cap=0;std::uintptr_t data=p;
 if(!Copy(p,out.header.data(),32))return false;
 std::memcpy(&n,out.header.data()+16,8);std::memcpy(&cap,out.header.data()+24,8);
 if(n>string_limit||cap<n||(cap<=15&&n>15))return false;
 if(cap>15)std::memcpy(&data,out.header.data(),8);
 std::vector<char>bytes(static_cast<std::size_t>(n)+1);
 if(!Copy(data,bytes.data(),bytes.size())||bytes.back()!=0)return false;
 // Read DATA is length-delimited. Preserve controls/NUL; never apply write rules.
 if(n&&MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,bytes.data(),static_cast<int>(n),nullptr,0)<=0)return false;
 std::array<std::byte,32>after{};if(!Copy(p,after.data(),32)||after!=out.header)return false;
 out.value.assign(bytes.data(),static_cast<std::size_t>(n));return true;
}
struct Definition {std::uintptr_t pointer=0;std::uint32_t id=invalid;String32 key;friend bool operator==(const Definition&,const Definition&)=default;};
bool Def(std::uintptr_t image,std::uintptr_t p,std::uintptr_t vt,Definition&out) {
 std::uintptr_t actual=0;std::uint32_t magic=0;
 if(!p||!At(p,0,actual)||actual!=image+vt||!At(p,0x10,out.id)||out.id==invalid||
 !At(p,0x38,magic)||magic!=0x4744624FU||!String(p+0x18,out.key))return false;
 out.pointer=p;return true;
}
struct Any40 {std::uintptr_t type=0;std::array<std::byte,32>storage{};};
struct ArgTable24 {Any40*data=nullptr;std::uint32_t capacity=1,count=1;std::uintptr_t allocator=0;};
struct Cursor16 {ArgTable24*table=nullptr;std::uint32_t index=0,reserved=0;};
static_assert(sizeof(Any40)==40&&sizeof(ArgTable24)==24&&sizeof(Cursor16)==16);
bool ReadonlyVariableOwner(std::uintptr_t image,const void*ref,std::uint16_t kind,
 std::uintptr_t expected,std::uintptr_t&descriptor,std::uintptr_t&owner)noexcept{
 std::uintptr_t table=0,callback=0;std::uint16_t count=0;owner=descriptor=0;
 if(!At(image,0x68B2484,count)||kind>=count||!At(image,0x68B3AC0,table)||!table||
  static_cast<std::size_t>(kind)*80>(std::numeric_limits<std::uintptr_t>::max)()-table)return false;
 descriptor=table+static_cast<std::size_t>(kind)*80;
 if(!At(descriptor,0x30,callback)||callback!=image+expected)return false;
 __try{owner=reinterpret_cast<std::uintptr_t(__fastcall*)(const void*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,expected))(ref);return owner!=0;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
struct NumericSnapshot {
 std::array<LivingNumeric267V1,4>values;
 std::uintptr_t variable_owner=0,official_descriptor=0;
 std::array<std::uintptr_t,4>borrowed{};
 std::array<std::array<std::byte,16>,4>refs{};
 friend bool operator==(const NumericSnapshot&,const NumericSnapshot&)=default;
};
bool Destroy(std::uintptr_t image,Any40&any,std::uintptr_t empty,std::uintptr_t allowed)noexcept {
 if(!any.type)return false;
 __try{
 if(any.type!=empty&&any.type!=allowed)return false;
 const auto vt=*reinterpret_cast<const std::uintptr_t*>(any.type);
 const auto dtor=*reinterpret_cast<const std::uintptr_t*>(vt+0x18);
 if(dtor<image||dtor>=image+kImageSize)return false;
 reinterpret_cast<void(__fastcall*)(void*,void*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,dtor-image))(reinterpret_cast<void*>(any.type),any.storage.data());
 any={};any.type=empty;return true;
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
// Fixed Artifact kind36 -> official descriptor+30 READONLY owner2636DB0.
// Var itself resolves that descriptor; never call mutable +38/2636E20.
// Borrowed ScopeRef16 is copied but never destroyed. Any40 and String are owned.
bool Numeric(std::uintptr_t image,std::uintptr_t artifact,std::uint32_t full,
 std::uint64_t wall,std::uint64_t mono,NumericSnapshot&out,bool&cleanup)noexcept {
 using Factory=std::uintptr_t(__fastcall*)();Any40 root{},text{},value{};
 std::uintptr_t empty=0,reference=0,string=0,fixed=0;bool initialized=false,good=false;
 volatile bool string_entered=false,string_complete=false;
 cleanup=true;
 __try{
  empty=reinterpret_cast<Factory>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x8B2EF0))();
  reference=reinterpret_cast<Factory>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x8B5030))();
  string=reinterpret_cast<Factory>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x8C21D0))();
  fixed=reinterpret_cast<Factory>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0xA3FDD0))();
  root.type=text.type=value.type=empty;initialized=true;
  do{
   if(!empty||!reference||!string||fixed!=image+0x5D251D8||!Time(wall,mono))break;
   if(!reinterpret_cast<bool(__fastcall*)(const void*,Any40*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x2BA4BD0))(
      reinterpret_cast<const void*>(artifact),&root)||root.type!=reference)break;
   std::uint32_t kind=0;std::uint64_t id=0;std::memcpy(&kind,root.storage.data(),4);std::memcpy(&id,root.storage.data()+8,8);
   if(kind!=36||id!=full)break;
   if(!ReadonlyVariableOwner(image,root.storage.data(),36,0x2636DB0,out.official_descriptor,out.variable_owner))break;
   bool all=true;
   for(std::size_t i=0;i<kLivingNumericKeys267V1.size();++i){
    if(!Time(wall,mono)){all=false;break;}
    const auto key=kLivingNumericKeys267V1[i];text={};text.type=string;
    const std::uint64_t cap=15;std::memcpy(text.storage.data()+24,&cap,8);
    string_entered=true;string_complete=false;
    reinterpret_cast<void*(__fastcall*)(void*,const char*,std::size_t)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x896BB0))(
       text.storage.data(),key,std::strlen(key));string_complete=true;
    ArgTable24 table{&text,1,1,0};Cursor16 args{&table,0,0};
    const auto ref=reinterpret_cast<std::uintptr_t(__fastcall*)(const void*,const Cursor16*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x3D26A70))(root.storage.data(),&args);
    std::array<std::byte,16>before{},after{};
    if(!ref||!Copy(ref,before.data(),16)){all=false;break;}
    auto&v=out.values[i];std::memcpy(&v.scope_kind,before.data(),2);
    if(ref==image+0x4AE2008){
     if(before!=std::array<std::byte,16>{}){all=false;break;}
     v.state=LivingNumericState267V1::absent;
    }else if(!v.scope_kind)v.state=LivingNumericState267V1::present_empty;
    else if(v.scope_kind!=1)v.state=LivingNumericState267V1::other_kind;
    else{
     // GetValue(true,0) for wrong kind is NOT used as a numeric proof.
     if(!reinterpret_cast<bool(__fastcall*)(const void*,Any40*,const Cursor16*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x3D5CCE0))(
        reinterpret_cast<const void*>(ref),&value,&args)||value.type!=fixed){all=false;break;}
     std::int64_t raw=0,payload=0;std::memcpy(&raw,value.storage.data(),8);std::memcpy(&payload,before.data()+8,8);
     if(raw!=payload){all=false;break;}v.state=LivingNumericState267V1::numeric;v.raw=raw;
    }
    if(!Copy(ref,after.data(),16)||before!=after){all=false;break;}
    out.borrowed[i]=ref;out.refs[i]=before;
    reinterpret_cast<void(__fastcall*)(void*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x897460))(text.storage.data());
    string_entered=string_complete=false;text={};text.type=empty;
    if(!Destroy(image,value,empty,fixed)){cleanup=false;all=false;break;}
   }
   std::uintptr_t owner_after=0,descriptor_after=0;
   good=all&&ReadonlyVariableOwner(image,root.storage.data(),36,0x2636DB0,descriptor_after,owner_after)&&owner_after==out.variable_owner&&descriptor_after==out.official_descriptor;
  }while(false);
 }__except(EXCEPTION_EXECUTE_HANDLER){good=false;cleanup=false;}
 if(string_entered){
  if(!string_complete)cleanup=false;
  else{__try{reinterpret_cast<void(__fastcall*)(void*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x897460))(text.storage.data());}
       __except(EXCEPTION_EXECUTE_HANDLER){cleanup=false;}}
 }
 if(initialized){const bool a=Destroy(image,value,empty,fixed),z=Destroy(image,root,empty,reference);cleanup=cleanup&&a&&z;}
 return good&&cleanup&&Time(wall,mono);
}
struct ArtifactSnapshot {
 std::uintptr_t pointer=0;std::array<std::byte,12>identity{};
 Definition type;std::uint32_t storage_reference=0;NumericSnapshot numeric;
 LivingArtifact267V1 value;
 friend bool operator==(const ArtifactSnapshot&,const ArtifactSnapshot&)=default;
};
struct SlotSnapshot {
 std::uintptr_t pointer=0;std::array<std::byte,24>bytes{};Definition type;
 LivingInventorySlot267V1 value;
 friend bool operator==(const SlotSnapshot&,const SlotSnapshot&)=default;
};
bool ArtifactRefs(std::uintptr_t,std::uintptr_t,std::uint32_t,std::uint64_t,std::uint64_t,LivingFixtureBindings267V1&,bool&)noexcept;
struct Snapshot {
 LivingInventorySource267V1 source;
 LivingFixtureBindings267V1 actor_references;
 std::uintptr_t property=0,inventory=0,storage=0,fallback=0,storage_rows=0;
 std::uint32_t storage_count=0;Array16 artifacts{},slots{};
 std::vector<std::uint32_t>ids;
 std::vector<ArtifactSnapshot>artifact_rows;std::vector<SlotSnapshot>slot_rows;
 friend bool operator==(const Snapshot&,const Snapshot&)=default;
};
bool Resolve(const Snapshot&s,std::uint32_t full,std::uintptr_t&out)noexcept {
 if(full==invalid)return false;const auto index=full&0xFFFFFFU;std::uint32_t actual=invalid;
 return index<s.storage_count&&At(s.storage_rows,static_cast<std::size_t>(index)*16+8,out)&&out&&out!=s.fallback&&
 At(out,0x10,actual)&&actual==full;
}
bool IsEquipped(std::uintptr_t image,std::uintptr_t inventory,std::uintptr_t artifact,bool&out)noexcept {
 __try{
  out=reinterpret_cast<bool(__fastcall*)(const void*,const void*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x26C92D0))(
    reinterpret_cast<const void*>(inventory),reinterpret_cast<const void*>(artifact));return true;
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool Take(const ReadonlyBindings&b,const LivingInventoryFrame267V1&f,const LivingInventoryRequest267V1&q,
 std::uint64_t mono,Snapshot&out,LivingInventoryRaw267V1&state,std::string&why) {
 const auto fail=[&](const char*reason){why=reason;return false;};const auto image=b.module_base;
 if(!Fresh(b,f,q,mono))return fail("living_inventory_actual_owner_Core_unavailable");
 std::uintptr_t vt=0;
 if(!At(f.actor,0x1B0,out.property)||!out.property)return fail("living_inventory_property_missing_not_empty");
 if(0x458>(std::numeric_limits<std::uintptr_t>::max)()-out.property)return false;
 out.inventory=out.property+0x458;
 if(out.inventory==image+0x5D5E9D0||!At(out.inventory,0,vt)||vt!=image+0x4E1E908)return fail("living_inventory_actual_type_unavailable");
 if(!ReadInventoryArrays(out.inventory,out.artifacts,out.slots,why))return false;
 if(!At(image,0x6A669D8,out.storage)||!out.storage||!At(image,0x6A669C0,out.fallback)||
 !At(out.storage,0x20,out.storage_rows)||!At(out.storage,0x2C,out.storage_count))return fail("living_artifact_storage_unavailable");
 out.ids.resize(static_cast<std::size_t>(out.artifacts.count));
 if(!out.ids.empty()&&!Copy(out.artifacts.data,out.ids.data(),out.ids.size()*4))return fail("living_inventory_ID_array_unreadable");
 out.source.actor_full_id=std::bit_cast<std::uint32_t>(f.core.played_character_id);
 for(const auto id:out.ids){
  if(id==invalid||std::count(out.ids.begin(),out.ids.end(),id)!=1)return fail("living_inventory_duplicate_or_invalid_fullID");
  ArtifactSnapshot row;std::uintptr_t definition=0;std::uint32_t magic=0;
  if(!Resolve(out,id,row.pointer)||!At(row.pointer,0,vt)||vt!=image+0x4E4DA80||
   !Copy(row.pointer+0x10,row.identity.data(),row.identity.size())||!At(row.pointer,0x14,magic)||magic!=0x41727469U||
   !At(row.pointer,0x18,row.storage_reference)||!At(row.pointer,0x78,row.value.owner_full_id)||
   row.value.owner_full_id!=out.source.actor_full_id||!At(row.pointer,0xB8,definition)||
   !Def(image,definition,0x4FF0528,row.type)||!At(row.pointer,0xB0,row.value.rarity_raw))return fail("living_owned_artifact_type_owner_unavailable");
  row.value.full_id=id;row.value.type_key=row.type.key.value;state.entered=true;bool cleanup=true;
  if(!Numeric(image,row.pointer,id,q.deadline_unix_ms,mono,row.numeric,cleanup)){
   state.cleanup_known=state.cleanup_known&&cleanup;return fail(cleanup?"living_fixed_numeric_unavailable":"living_fixed_numeric_cleanup_unknown");}
  row.value.numeric=row.numeric.values;out.artifact_rows.push_back(std::move(row));
 }
 for(std::int32_t i=0;i<out.slots.count;++i){
  SlotSnapshot row;row.pointer=out.slots.data+static_cast<std::size_t>(i)*24;
  std::uintptr_t definition=0;std::uint32_t id=invalid;
  if(row.pointer==image+0x5D5CBF8||!Copy(row.pointer,row.bytes.data(),row.bytes.size())||
   !At(row.pointer,0,vt)||vt!=image+0x4C4D4C0||!At(row.pointer,8,definition)||
   !Def(image,definition,0x4FF0840,row.type)||!At(row.pointer,16,id))return fail("living_complete_slot_model_unavailable");
  row.value.key=row.type.key.value;
  if(std::any_of(out.slot_rows.begin(),out.slot_rows.end(),[&](const auto&v){return v.type.pointer==row.type.pointer||v.value.key==row.value.key;}))return fail("living_duplicate_slot_definition");
  if(id!=invalid){
   std::uintptr_t actual=0;if(!Resolve(out,id,actual))return fail("living_equipped_slot_generation_unavailable");
   auto artifact=std::find_if(out.artifact_rows.begin(),out.artifact_rows.end(),[&](const auto&v){return v.value.full_id==id&&v.pointer==actual;});
   if(artifact==out.artifact_rows.end())return fail("living_equipped_slot_outside_owned_census");
   artifact->value.equipped=true;row.value.artifact_full_id=id;
  }
  if(row.value.key=="weapon")out.source.weapon_slot=static_cast<std::size_t>(i);
  out.source.slots.push_back(row.value);out.slot_rows.push_back(std::move(row));
 }
 for(const auto&row:out.artifact_rows){
  bool actual=false;if(!Fresh(b,f,q,mono))return fail("living_inventory_Core_changed_before_equipped_read");
  state.entered=true;
  if(!IsEquipped(image,out.inventory,row.pointer,actual)){state.cleanup_known=false;return fail("living_native_equipped_read_unknown");}
  if(actual!=row.value.equipped)return fail("living_native_equipped_physical_slot_disagreement");
  out.source.artifacts.push_back(row.value);
 }
 bool reference_cleanup=true;state.entered=true;
 if(!ArtifactRefs(image,f.actor,out.source.actor_full_id,q.deadline_unix_ms,mono,out.actor_references,reference_cleanup)){
  state.cleanup_known&=reference_cleanup;return fail(reference_cleanup?"living_fixed_Artifact_refs_unavailable":"living_fixed_Artifact_refs_cleanup_unknown");}
 out.source.fixed_references=out.actor_references.refs;
 if(!Fresh(b,f,q,mono))return fail("living_inventory_Core_changed_after_sample");
 return true;
}
} // namespace living_inventory_private
bool ReadLivingInventoryRaw267V1(const ReadonlyBindings&b,const LivingInventoryFrame267V1&f,
 const LivingInventoryRequest267V1&q,std::uint64_t mono,LivingInventoryRaw267V1&out,std::string&why)noexcept {
 out={};why="living_inventory_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1
 using namespace living_inventory_private;
 if(!Fresh(b,f,q,mono)||!VerifyReadonlyImage(b.module_base)||!VerifyLivingInventoryImage267V1(b.module_base)){
  why="living_inventory_exact_owned_binding_unavailable";return false;}
 try{
  Snapshot a,z;
  if(!Take(b,f,q,mono,a,out,why)||!Take(b,f,q,mono,z,out,why))return false;
  if(a!=z){why="living_inventory_complete_owned_model_drift";return false;}
  if(!Fresh(b,f,q,mono)){why="living_inventory_final_Core_drift";return false;}
  out.source=std::move(z.source);out.source.complete_inventory=out.source.sampled_twice=true;why.clear();return true;
 }catch(...){out.source={};why="living_inventory_bounded_cpp_observation_exception";return false;}
#else
 (void)b;(void)f;(void)q;(void)mono;return false;
#endif
}
}

#include "ck3_121003_living_fixture_bindings26785313_v1.inc"
#include "ck3_121003_living_weapon26785313_private_v1.inc"

#include "ck3_121003_living_event_scopes26785313_private_v1.inc"

#include "ck3_121003_living_detail26785313_private_v1.inc"

#include "ck3_121003_living_finite_case26785313_private_v1.inc"

#include "ck3_121003_living_ui26785313_raw_v1.inc"

#include "ck3_121003_living_entry26785313_raw_v1.inc"
