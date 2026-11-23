#include "xar_bridge/ck3_121003_rmtm_observation26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_rmtm_observation26785313_pins_v1.hpp"
#include "xar_bridge/ck3_121003_rmtm_title_query26785313_owner_v1.hpp"
#include <algorithm>
#include <bit>
#include <chrono>
#include <cstring>
#include <limits>
#include <unordered_set>
#include <windows.h>
#include <cstdio>
#include <intrin.h>
#ifndef XAR_RMTM_OBSERVATION_CALL_ADDRESS
#define XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,rva) ((image)+(rva))
#endif
namespace xar::ck3_121003::build26785313 {namespace rmtm_observation_native {
constexpr std::uint32_t invalid=0xFFFFFFFFU;
[[maybe_unused]]bool Copy(std::uintptr_t p,void*out,std::size_t n)noexcept{
 if(!p||!out||!n||n-1>(std::numeric_limits<std::uintptr_t>::max)()-p)return false;
 __try{std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
template<class T>bool At(std::uintptr_t p,std::size_t off,T&v)noexcept{return p&&off<=(std::numeric_limits<std::uintptr_t>::max)()-p&&Copy(p+off,&v,sizeof(v));}
[[maybe_unused]]bool Add(std::vector<std::byte>&out,std::uintptr_t p,std::size_t n){if(n>256*1024||out.size()>256*1024-n)return false;const auto pos=out.size();out.resize(pos+n);return !n||Copy(p,out.data()+pos,n);}
[[maybe_unused]]bool Core(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool Time(std::uint64_t wall,std::uint64_t mono)noexcept{const auto n=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return wall&&mono&&n>0&&static_cast<std::uint64_t>(n)<wall&&GetTickCount64()<mono;}
[[maybe_unused]]bool Fresh(const ReadonlyBindings&b,const RmtmObservationFrame267V1&f,const RmtmObservationRequest267V1&q,std::uint64_t mono)noexcept{
 if(!b.exact_image_admitted||!f.facts_verified||!f.role.facts_verified||!Core(f.core,q.expected)||!f.core.clock.paused||!Time(q.deadline_unix_ms,mono))return false;
#if defined(XAR_CK3_26785313_OFFLINE_FIXTURE)
 if(b.offline_fixture)return false;
#endif
 __try{const auto&w=f.role.world;ck3_1210::CoreSnapshotPrefix now;std::uintptr_t data=0,players=0;
  return ck3_1210::ReadCoreSnapshot(b.core,now)&&Core(now,f.core)&&*b.core.game_state_slot==w.game&&*b.core.jomini_state_slot==w.jomini&&*b.core.character_storage_slot==w.storage&&At(reinterpret_cast<std::uintptr_t>(w.game),0xA0,data)&&data==reinterpret_cast<std::uintptr_t>(w.data)&&At(reinterpret_cast<std::uintptr_t>(w.jomini),0x18,players)&&players==reinterpret_cast<std::uintptr_t>(w.players)&&b.core.get_local_player(w.jomini)==w.player&&ck3_1210::ResolveCoreCharacter(b.core,f.core.played_character_id)==w.actor&&Time(q.deadline_unix_ms,mono);
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool Typed(std::uintptr_t object,[[maybe_unused]]std::uintptr_t image,std::uintptr_t vt){std::uintptr_t value=0;return At(object,0,value)&&value==image+vt;}
[[maybe_unused]]bool Resolve(std::uintptr_t db,std::uintptr_t fallback,std::uint32_t id,std::size_t idOff,std::uintptr_t&out){
 out=0;std::uintptr_t rows=0,p=0;std::uint32_t count=0,actual=invalid;const auto index=id&0xFFFFFFU;
 if(id==invalid||!At(db,0x2C,count)||index>=count||!At(db,0x20,rows)||!At(rows,static_cast<std::size_t>(index)*16+8,p)||!p||p==fallback||!At(p,idOff,actual)||actual!=id)return false;out=p;return true;
}
[[maybe_unused]]bool Character(const ReadonlyBindings&b,const RmtmObservationFrame267V1&f,std::uint32_t id,std::uintptr_t&out,bool&alive){
 std::uintptr_t fallback=0,dead=0;std::uint32_t magic=0;
 if(!At(b.module_base,0x68A8930,fallback)||!Resolve(reinterpret_cast<std::uintptr_t>(f.role.world.storage),fallback,id,0x18,out)||!At(out,0x1C,magic)||magic!=0x43686172U||!At(out,0x1D0,dead))return false;
 __try{if(ck3_1210::ResolveCoreCharacter(b.core,std::bit_cast<std::int32_t>(id))!=reinterpret_cast<void*>(out))return false;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
 // Official current859 Character.IsAlive does not require optional +1C0.
 alive=dead==0;return true;
}
[[maybe_unused]]bool String(std::uintptr_t p,std::size_t max,std::string&out,std::vector<std::byte>&proof,bool key=false){
 std::array<std::byte,32>a{},z{};std::uint64_t len=0,cap=0;std::uintptr_t data=p;
 if(!Copy(p,a.data(),32))return false;std::memcpy(&len,a.data()+16,8);std::memcpy(&cap,a.data()+24,8);
 if(len>max||cap<len||(cap<=15&&cap!=15)||cap>0x10000000)return false;if(cap>15)std::memcpy(&data,a.data(),8);
 std::string text(static_cast<std::size_t>(len)+1,'\0');if(!Copy(data,text.data(),text.size())||text.back()||!Copy(p,z.data(),32)||a!=z)return false;text.pop_back();
 if(key){if(text.empty())return false;for(const auto c:text)if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'||c=='.'||c=='-'))return false;}
 else if(!text.empty()&&MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,text.data(),static_cast<int>(text.size()),nullptr,0)==0)return false;
 if(!Add(proof,p,32)||!Add(proof,data,static_cast<std::size_t>(len)+1))return false;out=std::move(text);return true;
}
[[maybe_unused]]bool Array(std::uintptr_t p,std::size_t max,std::uintptr_t&data,std::int32_t&count,std::vector<std::byte>&proof){std::int32_t cap=0;return At(p,0,data)&&At(p,8,cap)&&At(p,12,count)&&cap>=0&&count>=0&&count<=cap&&static_cast<std::size_t>(count)<=max&&(!count||data)&&Add(proof,p,16);}
[[maybe_unused]]bool Root(const RmtmObservationFrame267V1&f,std::string_view name,std::uintptr_t expected,GuiWindowNodeV1&out,std::vector<std::byte>&proof){
 for(const auto&n:f.witness)if(n.name==name){if(out.widget)return false;out=n;}
 if(!out.widget)return !expected;if(out.widget!=expected)return false;
 std::uint8_t flags=0;std::uintptr_t context=0,parent=0,vt=0;
 if(!At(out.widget,0,vt)||vt!=out.vtable||!At(out.widget,0xD0,flags)||(flags&1)||!At(out.widget,0xD8,context)||context!=f.scene.context||!At(out.widget,0xE8,parent)||parent!=out.parent||!Add(proof,out.widget+0xD0,0x38))return false;
 out.flags=flags;out.visible=(flags&0x18)==0;out.enabled=(flags&0x06)==0;return true;
}
[[maybe_unused]]bool Window(const ReadonlyBindings&b,const RmtmObservationFrame267V1&f,std::uintptr_t object,std::uintptr_t vt,std::uintptr_t secondary,std::uintptr_t root,std::vector<std::byte>&proof){
 std::uintptr_t v=0,owner=0;if(!Typed(object,b.module_base,vt)||(secondary&&(!At(object,0x10,v)||v!=b.module_base+secondary))||!At(f.scene.handler,0x40,owner)||owner!=f.scene.jomini||!At(object,0x98,v)||v!=owner||!At(object,0xA0,v)||v!=f.scene.handler||!At(object,0x68,v)||v!=f.scene.context||!At(object,0x60,v)||v!=root)return false;return Add(proof,object,0x18)&&Add(proof,object+0x60,0x68);
}
[[maybe_unused]]bool Modal(const RmtmObservationFrame267V1&f,std::vector<std::byte>&proof,bool&blocked){
 std::uintptr_t rows=0;std::int32_t count=0;blocked=false;if(!Array(f.scene.context+0x298,64,rows,count,proof))return false;
 for(std::int32_t n=0;n<count;++n){std::uintptr_t p=0;std::uint8_t flags=0;if(!At(rows,static_cast<std::size_t>(n)*8,p)||!At(p,0xD0,flags)||!Add(proof,rows+static_cast<std::size_t>(n)*8,8)||!Add(proof,p+0xD0,1))return false;if(!(flags&8))blocked=true;}return true;
}
[[maybe_unused]]RmtmTitleFrame267V1 TitleFrame(const RmtmObservationFrame267V1&f){const auto&w=f.role.world;return {f.core,reinterpret_cast<std::uintptr_t>(w.game),reinterpret_cast<std::uintptr_t>(w.jomini),reinterpret_cast<std::uintptr_t>(w.storage),reinterpret_cast<std::uintptr_t>(w.data),reinterpret_cast<std::uintptr_t>(w.players),reinterpret_cast<std::uintptr_t>(w.player),reinterpret_cast<std::uintptr_t>(w.actor),true};}
[[maybe_unused]]bool TitlePhase(const ReadonlyBindings&b,const RmtmObservationFrame267V1&f,const RmtmObservationRequest267V1&q,std::uint64_t mono,RmtmObservationRaw267V1&out,std::string&why){
 RmtmPrivateCaseAnchor267V1 anchor;
 if(!q.phase||!ReadRmtmPrivateCaseAnchor267V1(f.core,f.connection_generation,reinterpret_cast<std::uintptr_t>(f.role.world.game),reinterpret_cast<std::uintptr_t>(f.role.world.jomini),anchor)){why="rmtm_actual_private_Later_title_anchor_unavailable";return false;}
 RmtmTitleRaw267V1 physical;const RmtmTitleRequest267V1 guard{f.core,anchor.full_title_id,q.deadline_unix_ms};const bool read=ReadRmtmTitleRaw267V1(b,TitleFrame(f),guard,mono,physical,why);out.entered|=physical.entered;out.cleanup_known&=physical.cleanup_known;if(!read)return false;
 RmtmRoleRaw267V1 witness;const bool isSuccessor=anchor.successor==f.core.played_character_id;const bool shown=ReadRmtmRoleRaw267V1(b,f.role,isSuccessor,q.deadline_unix_ms,mono,witness,why);out.entered|=witness.entered;out.cleanup_known&=witness.cleanup_known;
 if(!shown||!witness.shown||!witness.predicates[2])return false;
 RmtmTitlePhaseData267V1 value;value.phase=*q.phase;value.physical={f.core.played_character_id,std::move(physical.source)};value.script_own_single_heir=witness.predicates[3];value.holder_realm_single_heir=witness.predicates[4];value.witness_guard_bound=value.witness_sampled_twice=true;
 out.fingerprint.insert(out.fingerprint.end(),witness.all_definition_fingerprint.begin(),witness.all_definition_fingerprint.end());out.source.title_phase=std::move(value);return true;
}
[[maybe_unused]]bool Council(const ReadonlyBindings&b,const RmtmObservationFrame267V1&f,RmtmObservationRaw267V1&out){
 const auto image=b.module_base;auto&proof=out.fingerprint;std::uintptr_t living=0,db=0,fallback=0,rows=0;std::int32_t count=0;
 if(!At(reinterpret_cast<std::uintptr_t>(f.role.world.actor),0x1C0,living)||!living||!Array(living+0x248,4096,rows,count,proof)||!At(image,0x6A669F0,db)||!At(image,0x6A669A0,fallback))return false;
 RmtmCouncilData267V1 value;value.owner_id=f.core.played_character_id;value.native_task_count=count;std::array<bool,9>found{};std::unordered_set<std::uint32_t>taskIDs;
 for(std::int32_t n=0;n<count;++n){
  std::uint32_t id=invalid,owner=invalid,incumbent=invalid,magic=0;std::uintptr_t task=0,type=0,definition=0;
  if(!At(rows,static_cast<std::size_t>(n)*4,id)||!taskIDs.insert(id).second||!Resolve(db,fallback,id,0x10,task)||!Typed(task,image,0x4BB1860)||!At(task,0x18,type)||!At(type,0x40,definition)||!Typed(definition,image,0x5011840)||!At(definition,0x38,magic)||magic!=0x4744624FU||!At(task,0x44,owner)||owner!=static_cast<std::uint32_t>(f.core.played_character_id)||!At(task,0x40,incumbent)||!Add(proof,rows+static_cast<std::size_t>(n)*4,4)||!Add(proof,task,0x48))return false;
  std::string key;if(!String(definition+0x18,256,key,proof,true))return false;
  const auto it=std::find(kRmtmCouncilKeys267V1.begin(),kRmtmCouncilKeys267V1.end(),key);if(it==kRmtmCouncilKeys267V1.end())continue;const auto index=static_cast<std::size_t>(it-kRmtmCouncilKeys267V1.begin());if(found[index])return false;found[index]=true;
  auto&seat=value.seats[index];seat.position_key=key;seat.full_task_id=id;
  if(incumbent!=invalid){std::uintptr_t actor=0;bool alive=false;if(!Character(b,f,incumbent,actor,alive)||!Add(proof,actor+0x18,8)||!Add(proof,actor+0x1C0,0x18))return false;seat.incumbent_id=incumbent;seat.incumbent_alive=alive;}
 }
 if(!std::all_of(found.begin(),found.end(),[](bool x){return x;}))return false;value.complete_model_census=value.sampled_twice=true;out.source.council=std::move(value);return true;
}
[[maybe_unused]]bool BudgetTitle([[maybe_unused]]std::uintptr_t image,std::uintptr_t object,std::uint32_t&out)noexcept{
 __try{return reinterpret_cast<std::uint32_t*(__fastcall*)(const void*,std::uint32_t*)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x19AC480))(reinterpret_cast<const void*>(object),&out)==&out;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool Budget(const ReadonlyBindings&b,const RmtmObservationFrame267V1&f,RmtmObservationRaw267V1&out){
 auto&proof=out.fingerprint;std::uintptr_t window=0,root=0;bool blocked=false;
 if(!At(f.scene.handler,0x5A8,window)||!Add(proof,f.scene.handler+0x5A8,8)||!Modal(f,proof,blocked))return false;
 RmtmBudgetData267V1 value;value.blocked_by_visible_modal=blocked;value.sampled_twice=true;
 if(!window){GuiWindowNodeV1 none;if(!Root(f,"window_treasury_budget_change",0,none,proof))return false;value.open_admissible=!blocked;out.source.budget=value;return true;}
 GuiWindowNodeV1 node;if(!At(window,0x60,root)||!root||!Root(f,"window_treasury_budget_change",root,node,proof)||!Window(b,f,window,0x4C417D8,0x4C417B0,root,proof))return false;
 value.found=true;value.visible=node.visible;value.enabled=node.enabled;out.window=window;out.root=root;std::uint32_t owner=invalid;
 if(!At(window,0xC8,owner)||!Add(proof,window+0xC8,4))return false;
 if(value.visible){
  if(owner!=static_cast<std::uint32_t>(f.core.played_character_id))return false;std::uintptr_t actor=0;bool alive=false;if(!Character(b,f,owner,actor,alive)||!alive)return false;value.owner_id=std::bit_cast<std::int32_t>(owner);
  std::uint32_t title=invalid;out.entered=true;if(!BudgetTitle(b.module_base,window,title)){out.cleanup_known=false;return false;}if(title==invalid)return false;
  std::uintptr_t db=0,fallback=0,p=0;std::uint32_t holder=invalid;
  if(!At(b.module_base,0x6A66648,db)||!At(b.module_base,0x6A66638,fallback)||!Resolve(db,fallback,title,0x10,p)||!Typed(p,b.module_base,0x4E21980)||!At(p,0x168,holder)||holder!=owner||!Add(proof,p+0x10,8)||!Add(proof,p+0x168,4))return false;
  value.full_title_id=title;value.holder_id=holder;
 }
 value.open_admissible=!value.visible&&!blocked;value.cancel_admissible=value.visible&&value.enabled&&!blocked&&value.owner_id==f.core.played_character_id;out.source.budget=std::move(value);return true;
}
#include "ck3_121003_rmtm_offer_diagnostic26785313_v1.inc"
#include "ck3_121003_rmtm_offer_origin26785313_v1.inc"
#include "ck3_121003_rmtm_observation26785313_native_v1.inc"
[[maybe_unused]]bool EmptyConfirmationTrigger([[maybe_unused]]std::uintptr_t image,std::uintptr_t definition,std::vector<std::byte>&proof){
 std::uint8_t subtype=255;std::int32_t count=-1;std::uintptr_t alternate=1;
 return Typed(definition,image,0x5006388)&&Typed(definition+0xB48,image,0x4AFA8E8)&&At(definition,0x1B61,subtype)&&subtype==0&&At(definition,0xB6C,count)&&count==0&&At(definition,0xBA8,alternate)&&!alternate&&Add(proof,definition+0xB48,0x68)&&Add(proof,definition+0x1B61,1);
}
struct OfferItemAny267V1 {std::uintptr_t type=0;std::array<std::byte,32>storage{};};
static_assert(sizeof(OfferItemAny267V1)==40);
[[maybe_unused]]bool ItemCan([[maybe_unused]]std::uintptr_t image,std::uintptr_t item,bool&can,bool&cleanup)noexcept{
 // D3E460 is typed IsValid(item RCX, owned Any40* RDX); AL is handled,
 // not the Boolean payload. Missing RDX is an ABI violation, not false DATA.
 can=false;cleanup=true;
 struct Guarded {std::array<std::uint64_t,2>before{0x9315ABCDEF267001ULL,0xF010203040506070ULL};
  OfferItemAny267V1 any{};std::array<std::uint64_t,2>after{0xAB35133726785001ULL,0xABCDEF9876543210ULL};}owned;
 const auto front=owned.before,back=owned.after;
 std::uintptr_t empty=0,boolean=0;bool initialized=false,valid=false;
 std::array<std::byte,0x28>before{},after{};
 __try{
  using Factory=std::uintptr_t(__fastcall*)();
  empty=reinterpret_cast<Factory>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x8B2EF0))();
  boolean=reinterpret_cast<Factory>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x8C2930))();
  owned.any.type=empty;initialized=true;
  if(empty&&boolean&&item&&Copy(item,before.data(),before.size())){
   OfferTraceMark267(OfferStage267V1::item_can_enter);
   const bool handled=reinterpret_cast<bool(__fastcall*)(const void*,OfferItemAny267V1*)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0xD3E460))(
      reinterpret_cast<const void*>(item),&owned.any);
   OfferTraceMark267(OfferStage267V1::item_can_returned,true);
   const auto value=std::to_integer<unsigned char>(owned.any.storage[0]);
   const auto physical=std::to_integer<unsigned char>(before[0x1C]);
   OfferTraceCan267(handled,owned.any.type==boolean,value,handled&&owned.any.type==boolean);
   valid=handled&&owned.any.type==boolean&&value<=1&&physical<=1&&value==physical&&
    Copy(item,after.data(),after.size())&&before==after&&owned.before==front&&owned.after==back;
   OfferTraceMark267(valid?OfferStage267V1::item_can_payload_valid:OfferStage267V1::item_can_payload_rejected,true);
   if(valid)can=value!=0;
  }
 }__except(OfferTraceException267(GetExceptionInformation())){cleanup=false;}
 if(owned.before!=front||owned.after!=back)cleanup=false;
 if(initialized){
  __try{
   if(!owned.any.type||(owned.any.type!=empty&&owned.any.type!=boolean))cleanup=false;
   else{
    const auto vt=*reinterpret_cast<const std::uintptr_t*>(owned.any.type);
    const auto dtor=*reinterpret_cast<const std::uintptr_t*>(vt+0x18);
    if(dtor<image||dtor-image>=kImageSize)cleanup=false;
    else {OfferTraceMark267(OfferStage267V1::item_any_destroy_enter);reinterpret_cast<void(__fastcall*)(void*,void*)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,dtor-image))(
      reinterpret_cast<void*>(owned.any.type),owned.any.storage.data());OfferTraceMark267(OfferStage267V1::item_any_destroy_returned,true);}
   }
  }__except(OfferTraceException267(GetExceptionInformation())){cleanup=false;}
 }
 if(offer_trace267.active)offer_trace267.item_cleanup=cleanup?1:0;
 if(!valid||!cleanup)can=false;return valid&&cleanup;
}
[[maybe_unused]]bool OfferRows(const ReadonlyBindings&b,const RmtmObservationFrame267V1&f,std::uintptr_t menu,RmtmObservationRaw267V1&out){
 auto&proof=out.fingerprint;std::uintptr_t categories=0,more=0,matched=0;std::int32_t categoryCount=0,moreCount=0;std::size_t total=0;std::unordered_set<std::uintptr_t>visited;
 const auto items=[&](std::uintptr_t header){
  std::uintptr_t rows=0;std::int32_t count=0;OfferTraceSub267("offer_rows_array_header");if(!Array(header,4096,rows,count,proof)||total+static_cast<std::size_t>(count)>4096)return false;total+=static_cast<std::size_t>(count);
  for(std::int32_t n=0;n<count;++n){std::uintptr_t item=0,owner=0,definition=0;std::uint32_t tag=99;
   OfferTraceSub267("offer_row_owner_tag");if(!At(rows,static_cast<std::size_t>(n)*8,item)||!item||!At(item,0,owner)||owner!=menu||!At(item,0x20,tag)||tag>1||!Add(proof,rows+static_cast<std::size_t>(n)*8,8)||!Add(proof,item,0x28))return false;
   // Repeated membership of the same physical item is not a second item. Every
   // occurrence is still captured; two distinct fixed Offer rows are refused.
   if(!visited.insert(item).second||tag!=0)continue;
   OfferTraceSub267("offer_row_definition");if(!At(item,8,definition)||!Typed(definition,b.module_base,0x5006388))return false;std::string key;std::uint32_t magic=0;
   OfferTraceSub267("offer_definition_canonical_key");if(!At(definition,0x38,magic)||magic!=0x4744624FU||!String(definition+0x18,256,key,proof,true))return false;
   if(key!="offer_vassalization_interaction")continue;OfferTraceSub267("fixed_offer_uniqueness");if(matched)return false;matched=item;
   OfferTraceSub267("fixed_offer_empty_confirmation_trigger");if(!EmptyConfirmationTrigger(b.module_base,definition,proof))return false;bool can=false,clean=true;out.entered=true;
   OfferTraceSub267("fixed_offer_typed_ItemCan");const bool read=ItemCan(b.module_base,item,can,clean);out.cleanup_known&=clean;if(!read)return false;
   const auto value=static_cast<unsigned char>(can);proof.push_back(static_cast<std::byte>(value));
   std::uint8_t admitted=0;if(!At(item,0x1C,admitted)||admitted>1)return false;
   // A known false Boolean is readable DATA, not a malformed source. It never
   // supplies an actionable fixed item or permission to populate the dialog.
   if(!can||!admitted)continue;out.item=item;out.definition=definition;
  }return true;
 };
 OfferTraceSub267("offer_categories_header");if(!Array(menu+0x118,256,categories,categoryCount,proof))return false;
 for(std::int32_t n=0;n<categoryCount;++n){const auto category=categories+static_cast<std::size_t>(n)*0x78;std::uintptr_t owner=0,definition=0;std::int32_t ordinal=-1;
  OfferTraceSub267("offer_category_owner_ordinal");if(!At(category,0x60,owner)||owner!=menu||!At(category,0x68,definition)||!definition||!At(definition,0x60,ordinal)||ordinal!=n||!Add(proof,category,0x78)||!items(category+0x20))return false;
 }
 OfferTraceSub267("offer_more_rows");if(!Array(menu+0xE0,4096,more,moreCount,proof)||!items(menu+0xE0))return false;
 (void)f;return true;
}
[[maybe_unused]]bool Offer(const ReadonlyBindings&b,const RmtmObservationFrame267V1&f,const RmtmObservationRequest267V1&q,RmtmObservationRaw267V1&out){
 if(!q.offer_target)return false;auto&proof=out.fingerprint;std::uint32_t full=invalid;std::uintptr_t target=0;std::array<std::byte,16>ref{};bool clean=true;
 OfferTraceSub267("offer_target_scope_ref");out.entered=true;if(!OfferTarget(b.module_base,reinterpret_cast<std::uintptr_t>(f.role.world.actor),static_cast<std::uint32_t>(f.core.played_character_id),*q.offer_target,full,target,ref,clean)){out.cleanup_known&=clean;return false;}
 bool alive=false;std::uintptr_t resolved=0;OfferTraceSub267("offer_target_character_fullID_alive");if(!Character(b,f,full,resolved,alive)||resolved!=target||!alive)return false;proof.insert(proof.end(),ref.begin(),ref.end());
 std::uintptr_t menu=0,confirmation=0,menuRoot=0,confirmRoot=0;bool blocked=false;
 OfferTraceSub267("offer_manager_windows_and_modal");if(!At(f.scene.handler,0xE8,menu)||!At(f.scene.handler,0xF0,confirmation)||!menu||!confirmation||!At(menu,0x60,menuRoot)||!At(confirmation,0x60,confirmRoot)||!menuRoot||!confirmRoot||!Add(proof,f.scene.handler+0xE8,16)||!Modal(f,proof,blocked))return false;
 GuiWindowNodeV1 menuNode,confirmNode;
 OfferTraceSub267("offer_root_context_backrefs");if(!Root(f,"character_interaction_menu_window",menuRoot,menuNode,proof)||!Root(f,"character_interaction_confirmation_window",confirmRoot,confirmNode,proof)||!Window(b,f,menu,0x4BDB6B8,0,menuRoot,proof)||!Window(b,f,confirmation,0x4BAC188,0,confirmRoot,proof))return false;
 RmtmOfferData267V1 value;value.target=*q.offer_target;value.actor_id=f.core.played_character_id;value.recipient_id=std::bit_cast<std::int32_t>(full);value.found=true;value.visible=confirmNode.visible;value.enabled=confirmNode.enabled;value.blocked_by_visible_modal=blocked;value.sampled_twice=true;
 out.window=confirmation;out.root=confirmRoot;out.menu=menu;
 // The official opener toggles/no-ops when its origin equals the cached
 // pointer even if the menu is hidden. Choose only an existing fixed owned
 // anchor which differs; never clear the cache or pass a null fallback.
 bool openerCan=false;
 if(!menuNode.visible&&!confirmNode.visible){
  OfferTraceSub267("offer_fixed_owned_origin");
  if(!SelectOfferOrigin267V1(f,proof,menuRoot,out.origin_widget))return false;
  bool scalar=false,collection=false;
  OfferTraceSub267("offer_official_opener_guards");
  if(!ReadOfferOpenerScalarGuards267V1(f,target,proof,scalar)||
   !ReadOfferOpenerCollectionGate267V1(f,proof,collection))return false;
  openerCan=out.origin_widget&&scalar&&collection;
 }
 if(menuNode.visible){std::uint32_t selected=invalid;OfferTraceSub267("offer_menu_recipient_and_rows");if(!At(menu,0xD0,selected)||selected!=full||!Add(proof,menu+0xD0,4)||!OfferRows(b,f,menu,out))return false;}
 if(confirmNode.visible){
  std::uint32_t actor=invalid,recipient=invalid;std::uintptr_t definition=0;std::string key;
  OfferTraceSub267("offer_confirmation_actor_recipient_definition");if(!At(confirmation,0x3B4,recipient)||recipient!=full||!At(confirmation,0x3C4,actor)||actor!=static_cast<std::uint32_t>(f.core.played_character_id)||!At(confirmation,0xC8,definition)||!Typed(definition,b.module_base,0x5006388)||!String(definition+0x18,256,key,proof,true)||key!="offer_vassalization_interaction"||!Add(proof,confirmation+0xC8,0x310))return false;
  out.definition=definition;out.entered=true;bool cleanup=true;OfferTraceSub267("offer_confirmation_description");if(!Description(b.module_base,confirmation,value.description,proof,cleanup)){out.cleanup_known&=cleanup;return false;}
 }
 value.open_admissible=!menuNode.visible&&!confirmNode.visible&&!blocked&&openerCan;value.cancel_admissible=confirmNode.visible&&confirmNode.enabled&&!blocked;out.source.offer=std::move(value);return true;
}
[[maybe_unused]]bool Take(const ReadonlyBindings&b,const RmtmObservationFrame267V1&f,const RmtmObservationRequest267V1&q,std::uint64_t mono,RmtmObservationRaw267V1&out,std::string&why){
 if(!Fresh(b,f,q,mono)){why="rmtm_observation_actual_Core_world_or_deadline_changed";return false;}
 out.source.kind=RmtmObservationKindFor267V1(q.action);out.source.case_bound=RmtmCaseAdmitted267V1(f.core,f.connection_generation,reinterpret_cast<std::uintptr_t>(f.role.world.game),reinterpret_cast<std::uintptr_t>(f.role.world.jomini));out.source.sampled_twice=true;
 if(!out.source.case_bound){why="rmtm_observation_actual_private_case_unavailable";return false;}
 bool good=false;switch(out.source.kind){case RmtmObservationKind267V1::title_phase:good=TitlePhase(b,f,q,mono,out,why);break;case RmtmObservationKind267V1::council:good=Council(b,f,out);break;case RmtmObservationKind267V1::budget:good=Budget(b,f,out);break;case RmtmObservationKind267V1::offer:good=Offer(b,f,q,out);break;}
 if(!good){if(why.empty())why="rmtm_observation_actual_complete_fixed_model_unavailable";return false;}
 return Fresh(b,f,q,mono)&&RmtmObservationSourceShape267V1(out.source,f.core);
}
}
bool VerifyRmtmObservationImage267V1([[maybe_unused]]std::uintptr_t image)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_OBSERVATION_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_OBSERVATION_V1
 using namespace rmtm_observation_native;
 if(!image||image!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))||!VerifyRmtmRoleImage267V1(image)||!VerifyRmtmDecisionImage267V1(image)||!VerifyRmtmTitleImage267V1(image))return false;
 for(const auto&p:rmtm_observation_pins::kPins){if(p.hex.empty()||p.hex.size()%2||p.hex.size()/2>kImageSize||p.rva>kImageSize-p.hex.size()/2)return false;for(std::size_t n=0;n<p.hex.size()/2;++n){const auto digit=[](char c){return static_cast<unsigned char>(c<='9'?c-'0':c-'a'+10);};const auto expected=static_cast<unsigned char>((digit(p.hex[n*2])<<4)|digit(p.hex[n*2+1]));unsigned char actual=0;if(!At(image+p.rva,n,actual)||actual!=expected)return false;}}
 for(const auto&p:kOfferOriginPins267V1){if(p.hex.empty()||p.hex.size()%2||p.hex.size()/2>kImageSize||p.rva>kImageSize-p.hex.size()/2)return false;for(std::size_t n=0;n<p.hex.size()/2;++n){const auto digit=[](char c){return static_cast<unsigned char>(c<='9'?c-'0':c-'a'+10);};const auto expected=static_cast<unsigned char>((digit(p.hex[n*2])<<4)|digit(p.hex[n*2+1]));unsigned char actual=0;if(!At(image+p.rva,n,actual)||actual!=expected)return false;}}
 return true;
#else
 return false;
#endif
}
bool ReadRmtmObservationRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const RmtmObservationFrame267V1&f,[[maybe_unused]]const RmtmObservationRequest267V1&q,[[maybe_unused]]std::uint64_t mono,RmtmObservationRaw267V1&out,std::string&why)noexcept{
 out={};why="rmtm_observation_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_OBSERVATION_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_OBSERVATION_V1
 try{using namespace rmtm_observation_native;if(!VerifyRmtmObservationImage267V1(b.module_base)||!Fresh(b,f,q,mono))return false;RmtmObservationRaw267V1 a,z;
  if(!Take(b,f,q,mono,a,why)){out=std::move(a);return false;}if(!Take(b,f,q,mono,z,why)){out=std::move(z);return false;}if(a!=z){out.entered=a.entered||z.entered;out.cleanup_known=a.cleanup_known&&z.cleanup_known;why="rmtm_observation_actual_model_changed_between_samples";return false;}out=std::move(z);why.clear();return true;
 }catch(...){out.source={};why="rmtm_observation_local_copy_unavailable";return false;}
#endif
 return false;
}
RmtmObservationCall267V1 CallRmtmObservationRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const RmtmObservationFrame267V1&f,[[maybe_unused]]const RmtmObservationRequest267V1&q,[[maybe_unused]]std::uint64_t mono,[[maybe_unused]]const RmtmObservationRaw267V1&issued)noexcept{
 RmtmObservationCall267V1 call;
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_OBSERVATION_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_OBSERVATION_V1
 using namespace rmtm_observation_native;using A=RmtmObservationAction267V1;
 OfferTraceScope267 diagnostic(b.module_base,q.action==A::open_offer);
 try{
  if(RmtmObservationQuery267V1(q.action))return call;RmtmObservationRaw267V1 now;std::string why;
  OfferTraceMark267(OfferStage267V1::issued_read_enter);
  if(!ReadRmtmObservationRaw267V1(b,f,q,mono,now,why)){OfferTraceTakeReason267(why);call.cleanup_known=now.cleanup_known;if(!call.cleanup_known)call.status=RmtmObservationCallStatus267V1::indeterminate;return call;}
  OfferTraceMark267(OfferStage267V1::issued_read_returned,true);
  if(now!=issued||!Fresh(b,f,q,mono)){OfferTraceMark267(OfferStage267V1::issued_source_changed);return call;}
  if(q.action==A::open_budget){if(!now.source.budget||!now.source.budget->open_admissible)return call;call=OpenBudget(b,f,q,mono);}
  else if(q.action==A::cancel_budget||q.action==A::cancel_offer){
   if(q.action==A::cancel_budget?(!now.source.budget||!now.source.budget->cancel_admissible):(!now.source.offer||!now.source.offer->cancel_admissible))return call;
   call.entered=true;call.cleanup_known=false;call.status=RmtmObservationCallStatus267V1::indeterminate;
   if(Close(b.module_base,q.action==A::cancel_budget?0x1173C40:0x11BB090,now.window)){call.native_returned=true;call.cleanup_known=true;call.status=RmtmObservationCallStatus267V1::returned;}
  }else if(q.action==A::open_offer){
   if(!now.source.offer||!now.source.offer->open_admissible||!q.offer_target||!now.origin_widget)return call;
   call.entered=true;call.cleanup_known=false;call.status=RmtmObservationCallStatus267V1::indeterminate;
   if(!RightClick(b.module_base,static_cast<std::uint32_t>(now.source.offer->recipient_id),now.origin_widget))return call;
   // Re-read the real complete menu produced by the official opener. A lazy
   // or unavailable model is not replaced by a synthetic item or success.
   RmtmObservationRaw267V1 opened;
   if(!Fresh(b,f,q,mono)){OfferTraceMark267(OfferStage267V1::post_click_fresh_rejected);return call;}
   OfferTraceMark267(OfferStage267V1::opened_take_enter);
   if(!Take(b,f,q,mono,opened,why)){OfferTraceTakeReason267(why);return call;}
   OfferTraceMark267(OfferStage267V1::opened_take_returned,true);
   if(!opened.item){OfferTraceMark267(OfferStage267V1::opened_item_missing);return call;}
   if(!opened.definition){OfferTraceMark267(OfferStage267V1::opened_definition_missing);return call;}
   if(!opened.source.offer||opened.source.offer->recipient_id!=now.source.offer->recipient_id){OfferTraceMark267(OfferStage267V1::opened_recipient_mismatch);return call;}
   std::vector<std::byte>gateProof;OfferTraceMark267(OfferStage267V1::fixed_trigger_guard_enter);
   if(!EmptyConfirmationTrigger(b.module_base,opened.definition,gateProof)||!Fresh(b,f,q,mono)){OfferTraceMark267(OfferStage267V1::fixed_trigger_guard_rejected);return call;}
   OfferTraceMark267(OfferStage267V1::fixed_trigger_guard_returned,true);
   bool clean=true,entered=false;
   if(!PopulateOffer(b.module_base,f.scene.handler,opened.item,opened.definition,now.window,clean,entered)){OfferTraceMark267(OfferStage267V1::populate_returned_false);call.cleanup_known=clean;if(clean&&!entered){call.native_returned=true;call.status=RmtmObservationCallStatus267V1::returned;}return call;}
   OfferTraceMark267(OfferStage267V1::populate_returned_true,true);call.native_returned=true;call.cleanup_known=clean;call.status=RmtmObservationCallStatus267V1::returned;
  }
  if(call.status==RmtmObservationCallStatus267V1::returned&&!Fresh(b,f,q,mono)){OfferTraceMark267(OfferStage267V1::final_fresh_rejected);call.status=RmtmObservationCallStatus267V1::indeterminate;call.cleanup_known=false;}
  OfferTraceMark267(call.status==RmtmObservationCallStatus267V1::returned?OfferStage267V1::call_returned:OfferStage267V1::call_refused,true);return call;
 }catch(...){OfferTraceMark267(OfferStage267V1::call_cpp_exception);if(call.entered){call.status=RmtmObservationCallStatus267V1::indeterminate;call.cleanup_known=false;}return call;}
#else
 return call;
#endif
}
std::string RmtmOfferDiagnostic267V1(){
 using namespace rmtm_observation_native;const auto&d=offer_trace267;
 if(!d.event_count)return {};char tail[97]{};std::size_t used=0;
 const unsigned count=d.event_count;const unsigned first=count>16?count-16:0;
 for(unsigned n=first;n<count&&used+4<sizeof(tail);++n){
  const int written=std::snprintf(tail+used,sizeof(tail)-used,"%s%u",n==first?"":",",static_cast<unsigned>(d.events[n%d.events.size()]));
  if(written<0||static_cast<std::size_t>(written)>=sizeof(tail)-used)break;used+=static_cast<std::size_t>(written);
 }
 char out[768]{};
 const int written=std::snprintf(out,sizeof(out),";offer_diag_v1 stage=%u completed=%u milestones=%llx seh=%u code=%08x module_rva_known=%u module_rva=%08x exception_stage=%u exception_count=%u item_handled=%d item_bool_type=%u item_payload=%d item_cleanup=%d events=%u tail=%s sub=%s take=%s",
  static_cast<unsigned>(d.stage),static_cast<unsigned>(d.last_completed),static_cast<unsigned long long>(d.milestones),
  d.exception_observed?1U:0U,static_cast<unsigned>(d.exception_code),d.exception_in_module?1U:0U,
  static_cast<unsigned>(d.exception_module_rva),static_cast<unsigned>(d.exception_stage),static_cast<unsigned>(d.exception_count),
  static_cast<int>(d.item_handled),d.item_type_expected?1U:0U,static_cast<int>(d.item_payload),static_cast<int>(d.item_cleanup),
  count,tail,d.subreason.data(),d.take_reason.data());
 return written>0&&static_cast<std::size_t>(written)<sizeof(out)?std::string(out,static_cast<std::size_t>(written)):std::string{};
}

}
