#include "xar_bridge/ck3_121003_djc_declaration_ui26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_djc_declarations26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_declarations26785313_abi_v1.hpp"
#include "xar_bridge/ck3_121003_djc_declaration_ui26785313_pins_v1.hpp"
#include "xar_bridge/ck3_121003_rite_edit_confirmation26785313_pins_v1.hpp"
#include "xar_bridge/ck3_121003_aub_private_console26785313_pins_v1.hpp"
#include "xar_bridge/ck3_12002_console_fixture.hpp"
#include <algorithm>
#include <chrono>
#include <cstring>
#include <limits>
#include <tuple>
#include <unordered_set>
#include <utility>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
namespace abi=declarations_abi_v1;
using NativeString=ck3_12002::ConsoleFixtureNativeString;
constexpr char interaction[]="declare_war_interaction";
[[maybe_unused]]bool Copy(std::uintptr_t p,void*out,std::size_t n)noexcept{
 if(!p||!out||!n||n-1>(std::numeric_limits<std::uintptr_t>::max)()-p)return false;
 __try{std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
template<class T>bool At(std::uintptr_t p,std::size_t off,T&out)noexcept{return p&&off<=(std::numeric_limits<std::uintptr_t>::max)()-p&&Copy(p+off,&out,sizeof(out));}
[[maybe_unused]]bool EqualCore(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool Fresh(const ReadonlyBindings&b,const ck3_1210::CoreSnapshotPrefix&e,std::uint64_t until,std::uint64_t deadline)noexcept{
 const auto wall=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
 if(!deadline||wall<=0||static_cast<std::uint64_t>(wall)>=deadline||!until||GetTickCount64()>=until||!e.clock.paused||!e.map_ready||!e.has_played_character||!e.played_character_alive||e.played_character_id==-1)return false;
 __try{ck3_1210::CoreSnapshotPrefix p;return ck3_1210::ReadCoreSnapshot(b.core,p)&&EqualCore(p,e);}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool Resolve(const ReadonlyBindings&b,std::int32_t id,std::uintptr_t&out)noexcept{
 if(id==-1)return false;__try{out=reinterpret_cast<std::uintptr_t>(ck3_1210::ResolveCoreCharacter(b.core,id));std::int32_t actual=-1;std::uint32_t type=0;std::uintptr_t death=0;return out&&At(out,0x18,actual)&&actual==id&&At(out,0x1C,type)&&type==0x43686172U&&At(out,0x1D0,death)&&!death;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool Bool1(std::uintptr_t image,std::uintptr_t fn,std::uintptr_t object,bool&out)noexcept{
 __try{out=reinterpret_cast<bool(__fastcall*)(void*)>(image+fn)(reinterpret_cast<void*>(object));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool Void1(std::uintptr_t image,std::uintptr_t fn,std::uintptr_t object)noexcept{
 __try{reinterpret_cast<void(__fastcall*)(void*)>(image+fn)(reinterpret_cast<void*>(object));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool Void2(std::uintptr_t image,std::uintptr_t fn,std::uintptr_t object,std::uintptr_t arg)noexcept{
 __try{reinterpret_cast<void(__fastcall*)(void*,const void*)>(image+fn)(reinterpret_cast<void*>(object),reinterpret_cast<const void*>(arg));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool Property(std::uintptr_t image,std::uintptr_t def,std::uintptr_t scope,bool&out)noexcept{
 __try{out=reinterpret_cast<bool(__fastcall*)(const void*,const void*)>(image+0x3D47320)(reinterpret_cast<const void*>(def+0xB48),reinterpret_cast<const void*>(scope));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]std::uintptr_t NativeGetter(std::uintptr_t image,std::uintptr_t rva)noexcept{
 __try{return reinterpret_cast<std::uintptr_t>(reinterpret_cast<void*(__fastcall*)()>(image+rva)());}__except(EXCEPTION_EXECUTE_HANDLER){return 0;}
}
[[maybe_unused]]bool Assign(std::uintptr_t image,NativeString&s)noexcept{
 __try{return reinterpret_cast<ck3_12002::ConsoleFixtureStringAssign>(image+0x896BB0)(&s,interaction,sizeof(interaction)-1)==&s;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool DestroyString(std::uintptr_t image,NativeString&s)noexcept{
 __try{reinterpret_cast<ck3_12002::ConsoleFixtureStringDestroy>(image+0x897460)(&s);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool NamedContext(std::uintptr_t image,void*out,const NativeString&s,std::uintptr_t actor,std::uintptr_t target)noexcept{
 __try{return reinterpret_cast<void*(__fastcall*)(void*,const NativeString*,const void*,const void*)>(image+0x3156120)(out,&s,reinterpret_cast<const void*>(actor),reinterpret_cast<const void*>(target))==out;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool Valid(std::uintptr_t image,std::uintptr_t target,const NativeString&s,bool&out)noexcept{
 __try{out=reinterpret_cast<bool(__fastcall*)(const void*,const NativeString*)>(image+0xBCA420)(reinterpret_cast<const void*>(target),&s);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
struct LocalSource {
 std::uintptr_t image=0;bool*known=nullptr;NativeString key{};alignas(8)std::array<std::byte,0x348>context{};
 bool key_entered=false,key_complete=false,context_entered=false,context_complete=false,closed=false;
 bool Close()noexcept{if(closed)return *known;closed=true;
  if(context_complete){if(!Void1(image,abi::k_destroy_context,reinterpret_cast<std::uintptr_t>(context.data()))) *known=false;}
  else if(context_entered)*known=false;
  if(key_complete){if(!DestroyString(image,key))*known=false;}else if(key_entered)*known=false;
  return *known;
 }
 ~LocalSource(){Close();}
};
[[maybe_unused]]bool WidgetType(std::uintptr_t image,std::uintptr_t p){
 const auto inside=[&](std::uintptr_t v,std::size_t n){return v>=image&&n<=kImageSize&&v-image<=kImageSize-n;};std::uintptr_t vt=0,col=0;std::uint32_t sig=0,off=0,self=0,chd=0,count=0,bases=0;
 if(!At(p,0,vt)||!inside(vt,8)||vt<image+8||!At(vt-8,0,col)||!inside(col,24)||!At(col,0,sig)||sig!=1||!At(col,4,off)||off||!At(col,8,self)||self||!At(col,20,self)||image+self!=col||!At(col,16,chd)||!inside(image+chd,16)||!At(image+chd,0,sig)||sig||!At(image+chd,8,count)||!count||count>64||!At(image+chd,12,bases)||!inside(image+bases,static_cast<std::size_t>(count)*4))return false;
 for(std::uint32_t i=0;i<count;++i){std::uint32_t desc=0,type=0;std::int32_t mdisp=0,pdisp=0;if(!At(image+bases,static_cast<std::size_t>(i)*4,desc)||!inside(image+desc,28)||!At(image+desc,0,type)||!At(image+desc,8,mdisp)||!At(image+desc,12,pdisp))return false;if(type==0x6082F78&&mdisp==0&&pdisp==-1)return true;}return false;
}
struct Node {std::uintptr_t pointer=0,children=0;std::int32_t count=0;std::string name;bool visible=false,enabled=false;};
[[maybe_unused]]bool Widget(std::uintptr_t image,std::uintptr_t p,std::uintptr_t context,std::uintptr_t parent,Node&out){
 std::uintptr_t actual=0,chars=0;std::uint32_t flags=0;std::int32_t cap=0;std::uint64_t size=0,ncap=0;
 if(!WidgetType(image,p)||!At(p,0xD8,actual)||actual!=context||!At(p,0xE8,actual)||actual!=parent||!At(p,0xD0,flags)||(flags&1)||!At(p,0xF0,out.children)||!At(p,0xF8,cap)||!At(p,0xFC,out.count)||out.count<0||out.count>4096||cap<out.count||(out.count&&!out.children)||!At(p,0x1C8,size)||size>256||!At(p,0x1D0,ncap)||size>ncap||ncap>0x1000000)return false;
 if(ncap==15){if(size>15)return false;chars=p+0x1B8;}else if(ncap<=15||!At(p,0x1B8,chars))return false;
 std::array<char,257>text{};if(!Copy(chars,text.data(),static_cast<std::size_t>(size)+1)||text[size]||std::memchr(text.data(),0,static_cast<std::size_t>(size))||(size&&MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,text.data(),static_cast<int>(size),nullptr,0)==0))return false;
 out.pointer=p;out.name.assign(text.data(),static_cast<std::size_t>(size));out.visible=(flags&0x18)==0;out.enabled=(flags&6)==0;return true;
}
[[maybe_unused]]bool FindWidget(std::uintptr_t image,const Node&parent,std::uintptr_t context,std::string_view name,Node&found){
 for(std::int32_t i=0;i<parent.count;++i){std::uintptr_t p=0;Node row;if(!At(parent.children,static_cast<std::size_t>(i)*8,p)||!p||!Widget(image,p,context,parent.pointer,row))return false;if(row.name==name){if(found.pointer)return false;row.visible=row.visible&&parent.visible;row.enabled=row.enabled&&parent.enabled;found=std::move(row);}}return true;
}
[[maybe_unused]]bool Scene(std::uintptr_t image,const DjcUiExpectedScene267V1&e,DjcUiRawObservation267V1&out){
 std::uintptr_t app=0,vt=0,first=0,context=0,root=0;if(!At(e.jomini,0x18,app)||!At(app,0,vt)||vt!=image+0x4AFA650||!At(app,0x1B8,first)||!At(first,0x58,context)||context!=e.gui_context||!At(context,0xD0,root)||root!=e.global_root)return false;
 Node global,middle,view;if(!Widget(image,root,context,0,global)||!FindWidget(image,global,context,"middle",middle)||!middle.pointer||middle.pointer!=e.middle||!FindWidget(image,middle,context,"declare_war_window",view))return false;
 if(e.view_named_bound!=static_cast<bool>(view.pointer)||(view.pointer&&e.view_root!=view.pointer))return false;
 out.view_material_visible=view.pointer&&view.visible;out.view_material_enabled=view.pointer&&view.enabled;
 if(e.view_visible!=out.view_material_visible||e.view_enabled!=out.view_material_enabled)return false;return true;
}
[[maybe_unused]]bool WarningWidget(std::uintptr_t image,const DjcUiExpectedScene267V1&e,std::uintptr_t actual){
 Node global,layer,popup;
 if(!Widget(image,e.global_root,e.gui_context,0,global)||!FindWidget(image,global,e.gui_context,"confirmation",layer)||!layer.pointer||!FindWidget(image,layer,e.gui_context,"basic_confirmation_popup",popup)||popup.pointer!=actual||!popup.visible||!popup.enabled)return false;
 std::vector<std::pair<Node,std::size_t>>todo{{popup,0}};std::unordered_set<std::uintptr_t>seen{popup.pointer};std::size_t buttons=0;
 while(!todo.empty()){auto[parent,depth]=std::move(todo.back());todo.pop_back();if(parent.name=="accept_button"&&parent.visible&&parent.enabled)++buttons;if(depth>=128&&parent.count)return false;
  for(std::int32_t i=0;i<parent.count;++i){std::uintptr_t p=0;Node child;if(seen.size()>=4096||!At(parent.children,static_cast<std::size_t>(i)*8,p)||!seen.insert(p).second||!Widget(image,p,e.gui_context,parent.pointer,child))return false;child.visible=child.visible&&parent.visible;child.enabled=child.enabled&&parent.enabled;todo.push_back({std::move(child),depth+1});}
 }return buttons==1;
}
[[maybe_unused]]bool Probe(const ReadonlyBindings&core,std::uintptr_t image,const ck3_1210::CoreSnapshotPrefix&e,std::int32_t target,DjcUiRawObservation267V1&out,LocalSource&scope){
 if(!Resolve(core,e.played_character_id,out.actor)||!Resolve(core,target,out.target))return false;
 std::int32_t actual_player=-1;std::uintptr_t actor=0;
 if(!At(image,0x5D50448,actual_player)||!Resolve(core,actual_player,actor)||actor!=out.actor)return false;
 const auto db=NativeGetter(image,abi::k_interaction_database_getter);
 if(!db||!At(db,abi::k_declare_interaction_offset,out.definition)||!out.definition)return false;
 scope.image=image;scope.known=&out.cleanup_known;scope.key_entered=true;if(!Assign(image,scope.key))return false;scope.key_complete=true;
 scope.context_entered=true;if(!NamedContext(image,scope.context.data(),scope.key,out.actor,out.target))return false;scope.context_complete=true;
 const auto context=reinterpret_cast<std::uintptr_t>(scope.context.data());std::uintptr_t definition=0;
 auto&s=out.source;if(!At(context,0,definition)||definition!=out.definition||!At(out.definition,0x1B61,s.loaded_interface)||!At(context,0x2E8,s.actor_id)||s.actor_id!=e.played_character_id||!At(context,0x2EC,s.recipient_id)||s.recipient_id!=target||!At(context,0x2FC,s.additional_role_id))return false;
 bool confirmation=false,valid=false;
 if(!Property(image,out.definition,context+8,confirmation)||!Valid(image,out.target,scope.key,valid)){out.cleanup_known=false;return false;}
 s.interaction_definition_verified=true;s.native_confirmation=confirmation;s.native_is_valid=valid;return true;
}
[[maybe_unused]]bool Array(std::uintptr_t p,std::vector<std::int32_t>&v,std::array<std::byte,16>*header=nullptr){
 std::uintptr_t data=0;std::int32_t cap=0,count=0;if(!At(p,0,data)||!At(p,8,cap)||!At(p,12,count)||cap<0||count<0||count>cap||count>10000||(count&&!data))return false;
 if(header&&!Copy(p,header->data(),header->size()))return false;v.resize(static_cast<std::size_t>(count));return !count||Copy(data,v.data(),v.size()*4);
}
[[maybe_unused]]bool Key(std::uintptr_t p,std::string&out){std::uint64_t n=0,cap=0;std::uintptr_t chars=p+0x18;if(!At(chars,16,n)||!At(chars,24,cap)||!n||n>256||n>cap||cap<15)return false;if(cap>15&&!At(chars,0,chars))return false;out.resize(static_cast<std::size_t>(n));if(!Copy(chars,out.data(),out.size()))return false;for(const auto c:out)if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'))return false;return true;}
[[maybe_unused]]bool CbDefinitions(std::uintptr_t image,std::array<std::uintptr_t,3>&out){
 const auto db=NativeGetter(image,abi::k_cb_database_getter);std::uintptr_t data=0;std::int32_t cap=0,count=0;
 if(!db||!At(db,0x50,data)||!At(db,0x58,cap)||!At(db,0x5C,count)||cap<count||count<0||count>10000||(count&&!data))return false;
 for(std::int32_t i=0;i<count;++i){std::uintptr_t type=0;if(!At(data,static_cast<std::size_t>(i)*8,type))return false;if(!type)continue;std::string key;if(!Key(type,key))return false;for(std::size_t j=0;j<3;++j)if(key==kDjcUiCbKeys267V1[j]){if(out[j])return false;out[j]=type;}}
 return std::all_of(out.begin(),out.end(),[](auto p){return p!=0;});
}
[[maybe_unused]]bool Tuple(std::uintptr_t p,const std::array<std::uintptr_t,3>&cb,DjcUiRawRow267V1&out){
 if(!At(p,0,out.definition))return false;const auto it=std::find(cb.begin(),cb.end(),out.definition);if(it==cb.end())return false;
 out.tuple.cb_key=kDjcUiCbKeys267V1[static_cast<std::size_t>(it-cb.begin())];
 if(!At(p,8,out.tuple.claimant_character_id)||!Array(p+0x10,out.tuple.target_title_ids,&out.primary_header)||!Array(p+0x58,out.tuple.extra_configuration_ids,&out.extra_header))return false;
 return std::none_of(out.tuple.target_title_ids.begin(),out.tuple.target_title_ids.end(),[](auto id){return id==-1;});
}
[[maybe_unused]]bool Special(std::uintptr_t context,const DjcUiRawRow267V1&expected,std::uintptr_t image){
 std::uintptr_t p=0,vt=0,cb=0;std::int32_t claimant=-1;std::vector<std::int32_t>titles;
 return At(context,0x340,p)&&p&&At(p,0,vt)&&vt==image+abi::k_war_vtable&&At(p,8,cb)&&cb==expected.definition&&At(p,0x28,claimant)&&claimant==expected.tuple.claimant_character_id&&Array(p+0x10,titles)&&titles==expected.tuple.target_title_ids;
}
[[maybe_unused]]bool Base(const ReadonlyBindings&core,const DjcUiExpectedScene267V1&e,std::uintptr_t image,DjcUiRawObservation267V1&out){
 std::uintptr_t vt=0,p=0;
 if(!At(image,kJominiStateSlotRva,p)||p!=e.jomini||!At(e.jomini,0,vt)||vt!=image+0x4B45FE0||!At(e.jomini,0x10,p)||p!=e.gfx||!At(e.gfx,0,vt)||vt!=image+0x4B24748||!At(e.gfx,0x20,p)||p!=e.jomini||!At(e.gfx,0x88,p)||p!=e.handler||!At(e.handler,0,vt)||vt!=image+0x4B22578||!At(e.handler,0x58,vt)||vt!=image+0x4B22558)return false;
 if(!At(e.handler,0x120,out.view)||!At(e.handler,0xF0,out.outer)||!out.view||!out.outer||!Scene(image,e,out))return false;
 for(const auto&entry:std::array<std::pair<std::uintptr_t,std::uintptr_t>,4>{{{out.view,0x4BB4E98},{out.view+0x10,0x4BB4F68},{out.outer,0x4BAC188},{out.outer+0x10,0x4BAC258}}})if(!At(entry.first,0,vt)||vt!=image+entry.second)return false;
 for(const auto object:{out.view,out.outer})if(!At(object,0x98,p)||p!=e.jomini||!At(object,0xA0,p)||p!=e.handler||!At(object,0x68,p)||p!=e.gui_context)return false;
 std::uintptr_t current_outer=0;if(!At(out.view,0xD0,current_outer))return false;
 // D0 may not yet refer to this interaction before the first official Open.
 if(current_outer!=out.outer)return true;
 std::uintptr_t def=0;auto&s=out.source;std::int32_t actor=-1,recipient=-1,additional=-1;
 if(!At(out.outer+0xC8,0,def)||def!=out.definition)return true;
 if(!At(out.outer+0xC8,0x2E8,actor)||!At(out.outer+0xC8,0x2EC,recipient)||!At(out.outer+0xC8,0x2FC,additional))return false;
 if(actor!=s.actor_id||recipient!=s.target_character_id)return true;
 if(!Resolve(core,additional,out.additional))return false;s.additional_role_id=additional;s.resident_available=true;
 std::uintptr_t root=0;if(!At(out.view,0x60,root)||!Copy(out.outer+0xC8,out.context.data(),out.context.size()))return false;
 s.named_root_bound=e.view_named_bound&&root==e.view_root;s.window_visible=s.named_root_bound&&out.view_material_visible;s.window_enabled=s.named_root_bound&&out.view_material_enabled;
 return true;
}
[[maybe_unused]]bool Resident(const ReadonlyBindings&core,const DjcUiExpectedScene267V1&e,std::uintptr_t image,std::uint8_t desired,DjcUiRawObservation267V1&out){
 auto&s=out.source;if(!Base(core,e,image,out))return false;if(!s.resident_available)return true;
 std::array<std::uintptr_t,3>cb{};if(!CbDefinitions(image,cb)||!Copy(out.view+0xD8,out.rows_header.data(),16))return false;
 std::int32_t cap=0,count=0;std::memcpy(&out.rows,out.rows_header.data(),8);std::memcpy(&cap,out.rows_header.data()+8,4);std::memcpy(&count,out.rows_header.data()+12,4);
 if(cap<count||count<0||count>4096||(count&&!out.rows))return false;std::size_t cells=0;
 for(std::int32_t i=0;i<count;++i){const auto p=out.rows+static_cast<std::uintptr_t>(i)*0xB0;std::uintptr_t type=0,owner=0;std::uint8_t enabled=0;
  if(!At(p,0,type)||!At(p,0xA0,owner)||owner!=out.view||!At(p,0xA8,enabled)||enabled>1)return false;
  if(type!=cb[desired])continue;DjcUiRawRow267V1 row;row.row=p;row.source_window=owner;row.tuple.source_row_enabled=enabled!=0;if(!Tuple(p,cb,row))return false;cells+=row.tuple.target_title_ids.size()+row.tuple.extra_configuration_ids.size();if(cells>10000)return false;out.choices.push_back(std::move(row));
 }
 std::uintptr_t selected=0;if(!At(out.view,0xF0,selected))return false;
 if(std::find(cb.begin(),cb.end(),selected)!=cb.end()){
  DjcUiRawRow267V1 row;std::uint8_t enabled=0;if(!Tuple(out.view+0xF0,cb,row)||!At(out.view,0x190,row.source_window)||row.source_window!=out.view||!At(out.view,0x198,enabled)||enabled>1)return false;row.tuple.source_row_enabled=enabled!=0;out.selected=row;s.selected=row.tuple;
  if(s.named_root_bound&&s.window_visible&&s.window_enabled){std::uint8_t cached=0;bool selected_gate=false;if(!Bool1(image,abi::k_selected_send_gate,out.view,selected_gate)){out.cleanup_known=false;return false;}if(!At(out.view,0x10DA,cached)||cached>1)return false;out.selected_native_gate=selected_gate;s.native_can_send=cached!=0&&selected_gate;
   if(s.native_can_send.value_or(false)&&!Special(out.outer+0xC8,row,image))return false;
  }
 }
 return true;
}
[[maybe_unused]]bool Modal(std::uintptr_t image,const DjcUiExpectedScene267V1&e,DjcUiRawObservation267V1&out){
 auto&s=out.source;out.manager=NativeGetter(image,0xCF2C50);if(!out.manager||!Copy(out.manager+0x18,out.dialog_header.data(),16))return false;std::int32_t cap=0,count=0;std::memcpy(&out.dialogs,out.dialog_header.data(),8);std::memcpy(&cap,out.dialog_header.data()+8,4);std::memcpy(&count,out.dialog_header.data()+12,4);
 if(cap<count||count<0||count>128||(count&&!out.dialogs))return false;std::size_t active=0;
 for(std::int32_t i=0;i<count;++i){std::uintptr_t p=0,vt=0,root=0,context=0;std::uint8_t closed=1;if(!At(out.dialogs,static_cast<std::size_t>(i)*8,p))return false;out.dialog_pointers.push_back(p);if(!p)continue;if(!At(p,0,vt)||!At(p,0x70,root)||!At(p,0x78,context)||!At(p,0xA8,closed)||closed>1)return false;if(closed||!root)continue;if(++active>1)return false;
  if(vt!=image+0x4BB4E38)continue;
  std::uintptr_t secondary=0,window=0;std::uint8_t eligible=0;
  if(!At(p,0x10,secondary)||secondary!=image+0x4BB4DF0||!At(p,0x20,secondary)||secondary!=image+0x4BB4E10||context!=e.gui_context||!At(p,0x1D0,window)||window!=out.view||!At(p,0x1D8,eligible)||eligible>1||!out.selected||eligible!=static_cast<std::uint8_t>(out.selected->tuple.source_row_enabled))return false;
  std::array<std::uintptr_t,3>cb{};DjcUiRawRow267V1 tuple;if(!CbDefinitions(image,cb)||!Tuple(p+0x130,cb,tuple)||tuple.definition!=out.selected->definition)return false;tuple.tuple.source_row_enabled=eligible!=0;if(tuple.tuple!=out.selected->tuple)return false;
  std::uintptr_t def=0;std::int32_t actor=-1,target=-1,additional=-1;
  if(!At(p+0x1E0,0,def)||def!=out.definition||!At(p+0x1E0,0x2E8,actor)||actor!=s.actor_id||!At(p+0x1E0,0x2EC,target)||target!=s.recipient_id||!At(p+0x1E0,0x2FC,additional)||additional!=s.additional_role_id||!Special(p+0x1E0,tuple,image)||!Copy(p+0x1E0,out.modal_context.data(),out.modal_context.size()))return false;
  if(!e.warning_named_bound||root!=e.warning_root||!e.warning_accept_admissible||!WarningWidget(image,e,root))continue;
  bool can=false;if(!Bool1(image,0x1230010,p,can)){out.cleanup_known=false;return false;}out.modal=p;out.modal_root=root;s.warning_source_available=true;s.native_can_accept=can;s.accept_admissible=can;
 }
 out.no_active_dialog=active==0;return true;
}
[[maybe_unused]]bool Capture(const ReadonlyBindings&core,const DjcUiRawBindings267V1&b,const ck3_1210::CoreSnapshotPrefix&expected,std::int32_t target,std::uint8_t cb,const DjcUiExpectedScene267V1&e,std::uint64_t until,DjcUiRawObservation267V1&out){
 out.source.target_character_id=target;out.source.cb_key=kDjcUiCbKeys267V1[cb];LocalSource scope;scope.known=&out.cleanup_known;scope.image=b.image;
 if(!Fresh(core,expected,until,e.deadline_unix_ms)||!Probe(core,b.image,expected,target,out,scope)||!scope.Close()||!Resident(core,e,b.image,cb,out)||!Modal(b.image,e,out)||!Fresh(core,expected,until,e.deadline_unix_ms))return false;
 auto&s=out.source;s.open_admissible=s.loaded_interface==4&&s.native_confirmation.value_or(false)&&s.native_is_valid.value_or(false)&&!out.view_material_visible&&out.no_active_dialog;
 s.send_admissible=s.resident_available&&s.named_root_bound&&s.window_visible&&s.window_enabled&&s.selected&&s.selected->cb_key==s.cb_key&&s.selected->source_row_enabled&&s.native_can_send.value_or(false)&&out.no_active_dialog;
 for(std::size_t i=0;i<out.choices.size();++i)s.choices.push_back({static_cast<std::uint64_t>(i+1),out.choices[i].tuple});
 return true;
}
}
bool VerifyDjcUiImage267V1([[maybe_unused]]std::uintptr_t image)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1
 if(image!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))||!VerifyCurrentDjcDeclarationsImage267V1(image)||!VerifyGuiWindowImageV1(image))return false;
 std::array<unsigned char,djc_ui_pins::kMaxBytes>buf{};
 const auto check=[&](const ImagePin&p){return !p.bytes.empty()&&p.bytes.size()<=buf.size()&&p.rva<=kImageSize-p.bytes.size()&&Copy(image+p.rva,buf.data(),p.bytes.size())&&!std::memcmp(buf.data(),p.bytes.data(),p.bytes.size());};
 for(const auto&p:djc_ui_pins::kPins)if(!check(p))return false;
 for(const auto&p:djc_ui_pins::kPointers){std::uintptr_t value=0;if(!At(image,p.slot,value)||value!=image+p.target)return false;}
 bool manager=false,assign=false,destroy=false;
 for(const auto&p:rite_edit_confirmation_pins::kPins)if(p.rva>=0xCF2C50&&p.rva<0xCF2CD0){manager=true;if(!check(p))return false;}
 for(const auto&p:aub_private_console_pins::kPins)if(p.rva==0x896BB0||p.rva==0x897460){if(!check(p))return false;assign=assign||p.rva==0x896BB0;destroy=destroy||p.rva==0x897460;}
 return manager&&assign&&destroy;
#else
 return false;
#endif
}
DjcUiRawBindings267V1 BindDjcUiImage267V1([[maybe_unused]]std::uintptr_t image,[[maybe_unused]]std::string_view sha)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1
 if(BindReadonlyImage(image,sha).exact_image_admitted&&VerifyDjcUiImage267V1(image))return {image,true};
#endif
 return {};
}
bool SameDjcUiRaw267V1(const DjcUiRawObservation267V1&a,const DjcUiRawObservation267V1&b)noexcept{
 const auto&s=a.source;const auto&t=b.source;
 return std::tie(s.target_character_id,s.cb_key,s.interaction_definition_verified,s.loaded_interface,s.native_confirmation,s.native_is_valid,s.open_admissible,s.resident_available,s.named_root_bound,s.window_visible,s.window_enabled,s.actor_id,s.recipient_id,s.additional_role_id,s.selected,s.choices,s.native_can_send,s.send_admissible,s.warning_source_available,s.native_can_accept,s.accept_admissible)==std::tie(t.target_character_id,t.cb_key,t.interaction_definition_verified,t.loaded_interface,t.native_confirmation,t.native_is_valid,t.open_admissible,t.resident_available,t.named_root_bound,t.window_visible,t.window_enabled,t.actor_id,t.recipient_id,t.additional_role_id,t.selected,t.choices,t.native_can_send,t.send_admissible,t.warning_source_available,t.native_can_accept,t.accept_admissible)&&
  std::tie(a.definition,a.actor,a.target,a.additional,a.view,a.outer,a.rows,a.rows_header,a.context,a.choices,a.selected,a.manager,a.dialogs,a.modal,a.modal_root,a.dialog_header,a.dialog_pointers,a.modal_context,a.selected_native_gate,a.cleanup_known,a.no_active_dialog,a.view_material_visible,a.view_material_enabled)==std::tie(b.definition,b.actor,b.target,b.additional,b.view,b.outer,b.rows,b.rows_header,b.context,b.choices,b.selected,b.manager,b.dialogs,b.modal,b.modal_root,b.dialog_header,b.dialog_pointers,b.modal_context,b.selected_native_gate,b.cleanup_known,b.no_active_dialog,b.view_material_visible,b.view_material_enabled);
}
static bool ReadDjcUiRawInner267V1([[maybe_unused]]bool refresh,[[maybe_unused]]const ReadonlyBindings&core,[[maybe_unused]]const DjcUiRawBindings267V1&b,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&expected,[[maybe_unused]]std::int32_t target,[[maybe_unused]]std::uint8_t cb,[[maybe_unused]]const DjcUiExpectedScene267V1&e,[[maybe_unused]]std::uint64_t until,DjcUiRawObservation267V1&out,std::string&reason)noexcept{
 out={};reason="current_djc_ui_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1
 try{if(!b.verified||core.module_base!=b.image||!core.exact_image_admitted||!core.core.enabled||cb>=3||target==-1||target==expected.played_character_id||!VerifyDjcUiImage267V1(b.image))return false;
  // Refresh only this already-visible resident view, never Open/Select/Send from query.
  DjcUiRawObservation267V1 pre;pre.source.target_character_id=target;pre.source.cb_key=kDjcUiCbKeys267V1[cb];LocalSource before;before.image=b.image;before.known=&pre.cleanup_known;
  if(!Fresh(core,expected,until,e.deadline_unix_ms)||!Probe(core,b.image,expected,target,pre,before)||!before.Close()||!Base(core,e,b.image,pre)){out.cleanup_known=pre.cleanup_known;reason="current_djc_ui_pre_refresh_source_unavailable";return false;}
  if(refresh&&pre.source.resident_available&&pre.source.named_root_bound&&pre.source.window_visible&&pre.source.window_enabled){
   std::uintptr_t selected=0;if(!At(pre.view,0xF0,selected))return false;if(selected&&!Void1(b.image,abi::k_refresh_can_send,pre.view)){out.cleanup_known=false;reason="current_djc_ui_native_can_refresh_unknown";return false;}}
  DjcUiRawObservation267V1 a,z;
  if(!Capture(core,b,expected,target,cb,e,until,a)){out.cleanup_known=a.cleanup_known;reason="current_djc_ui_actual_definition_or_resident_unavailable";return false;}
  if(!Capture(core,b,expected,target,cb,e,until,z)||!SameDjcUiRaw267V1(a,z)||!VerifyDjcUiImage267V1(b.image)){out.cleanup_known=a.cleanup_known&&z.cleanup_known;reason="current_djc_ui_source_changed_between_samples";return false;}
  out=std::move(z);reason.clear();return true;
 }catch(...){reason="current_djc_ui_read_exception";return false;}
#endif
 return false;
}
bool ReadDjcUiRaw267V1(const ReadonlyBindings&c,const DjcUiRawBindings267V1&b,const ck3_1210::CoreSnapshotPrefix&e,std::int32_t t,std::uint8_t cb,const DjcUiExpectedScene267V1&s,std::uint64_t d,DjcUiRawObservation267V1&o,std::string&r)noexcept{return ReadDjcUiRawInner267V1(true,c,b,e,t,cb,s,d,o,r);}
bool ReadDjcUiRawForClaim267V1(const ReadonlyBindings&c,const DjcUiRawBindings267V1&b,const ck3_1210::CoreSnapshotPrefix&e,std::int32_t t,std::uint8_t cb,const DjcUiExpectedScene267V1&s,std::uint64_t d,DjcUiRawObservation267V1&o,std::string&r)noexcept{return ReadDjcUiRawInner267V1(false,c,b,e,t,cb,s,d,o,r);}
DjcUiRawCall267V1 CallDjcUiRaw267V1([[maybe_unused]]DjcUiAction267V1 action,[[maybe_unused]]const ReadonlyBindings&core,[[maybe_unused]]const DjcUiRawBindings267V1&b,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&expected,[[maybe_unused]]std::int32_t target,[[maybe_unused]]std::uint8_t cb,[[maybe_unused]]const DjcUiExpectedScene267V1&e,[[maybe_unused]]std::uint64_t until,[[maybe_unused]]const DjcUiRawObservation267V1&prior,[[maybe_unused]]std::uintptr_t row)noexcept{
 DjcUiRawCall267V1 out;
#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1
 try{DjcUiRawObservation267V1 fresh;std::string reason;if(!ReadDjcUiRawForClaim267V1(core,b,expected,target,cb,e,until,fresh,reason)){out.cleanup_known=fresh.cleanup_known;return out;}if(!SameDjcUiRaw267V1(prior,fresh)||!Fresh(core,expected,until,e.deadline_unix_ms))return out;
  if(action==DjcUiAction267V1::open_ui){
   if(!fresh.source.open_admissible)return out;LocalSource scope;scope.image=b.image;scope.known=&out.cleanup_known;DjcUiRawObservation267V1 probe;
   if(!Probe(core,b.image,expected,target,probe,scope)||probe.definition!=fresh.definition||probe.actor!=fresh.actor||probe.target!=fresh.target||probe.source.loaded_interface!=4||!probe.source.native_confirmation.value_or(false)||!probe.source.native_is_valid.value_or(false)||!Fresh(core,expected,until,e.deadline_unix_ms))return out;
   out.effect_entered=true;const bool returned=Void2(b.image,0xBCA8E0,fresh.target,reinterpret_cast<std::uintptr_t>(&scope.key));out.cleanup_known=scope.Close();out.status=returned&&out.cleanup_known?DjcUiRawCallStatus267V1::returned:DjcUiRawCallStatus267V1::indeterminate;
  }else if(action==DjcUiAction267V1::select_choice){
   const auto it=std::find_if(fresh.choices.begin(),fresh.choices.end(),[&](const auto&c){return c.row==row;});if(it==fresh.choices.end()||!it->tuple.source_row_enabled||!fresh.source.named_root_bound||!fresh.source.window_visible||!fresh.source.window_enabled||!fresh.no_active_dialog)return out;
   out.effect_entered=true;out.status=Void2(b.image,0x1235CC0,fresh.view,row)?DjcUiRawCallStatus267V1::returned:DjcUiRawCallStatus267V1::indeterminate;
  }else if(action==DjcUiAction267V1::send_ui){
   if(!fresh.source.send_admissible||!fresh.selected_native_gate||!fresh.no_active_dialog)return out;
   out.effect_entered=true;out.status=Void1(b.image,abi::k_send_native_action,fresh.view)?DjcUiRawCallStatus267V1::returned:DjcUiRawCallStatus267V1::indeterminate;
  }else if(action==DjcUiAction267V1::accept_warning){
   if(!fresh.modal||!fresh.source.accept_admissible||!fresh.source.native_can_accept.value_or(false))return out;
   bool can=false;if(!Bool1(b.image,0x1230010,fresh.modal,can)){out.cleanup_known=false;return out;}if(!can||!Fresh(core,expected,until,e.deadline_unix_ms))return out;
   out.effect_entered=true;out.status=Void1(b.image,0xCF3200,fresh.modal)?DjcUiRawCallStatus267V1::returned:DjcUiRawCallStatus267V1::indeterminate;
  }
  if(out.status==DjcUiRawCallStatus267V1::returned&&!VerifyDjcUiImage267V1(b.image))out.status=DjcUiRawCallStatus267V1::indeterminate;
 }catch(...){if(out.effect_entered)out.status=DjcUiRawCallStatus267V1::indeterminate;}
#endif
 return out;
}
} // namespace
