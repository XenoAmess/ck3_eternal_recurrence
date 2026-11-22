// NoGame only. Self-owned synthetic image/objects, explicit fixed-call stubs.
// Includes actual candidate Raw + Wire: no mock request-shape permission.
// This does not compile or query a game when written; Native owner runs it later.
#include <windows.h>
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#ifndef XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1
#define XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1 1
#endif
#include "xar_bridge/ck3_121003_rite_text26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_rite_text26785313_pins_v1.hpp"
namespace rite_text_test {
std::uintptr_t image=0; ULONGLONG tick=10;
HMODULE Module(LPCWSTR name) noexcept {return name==nullptr?reinterpret_cast<HMODULE>(image):nullptr;}
ULONGLONG Tick() noexcept {return tick;}
std::uintptr_t Address(std::uintptr_t) noexcept;
}
#define GetModuleHandleW rite_text_test::Module
#define GetTickCount64 rite_text_test::Tick
#define XAR_RITE_TEXT_CALL_ADDRESS(image,rva) ((void)(image),rite_text_test::Address(rva))
#include "ck3_121003_rite_text26785313_raw_v1.cpp"
#undef XAR_RITE_TEXT_CALL_ADDRESS
#undef GetTickCount64
#undef GetModuleHandleW
#include "ck3_121003_rite_text26785313_wire_v1.cpp"
namespace rite_text_test {
using namespace xar::ck3_121003::build26785313;
using Core=xar::ck3_1210::CoreSnapshotPrefix;
struct Fixture;Fixture* active=nullptr;
unsigned total_cases=0,bad_receiver=0;bool readonly_ok=true,create_image_ok=true;
void Need(bool ok,const char*label){if(!ok)throw std::runtime_error(label);}
void Guard(bool ok){if(!ok){++bad_receiver;RaiseException(0xE0410001,0,0,nullptr);}}
template<std::size_t N>std::uintptr_t Ptr(std::array<std::byte,N>&a){return reinterpret_cast<std::uintptr_t>(a.data());}
template<std::size_t N,class T>void Put(std::array<std::byte,N>&a,std::size_t at,T v){Need(at+sizeof(v)<=N,"owned fixture write bound");std::memcpy(a.data()+at,&v,sizeof(v));}
struct Header32 {std::array<std::byte,16>data{};std::uint64_t length=0,capacity=15;};
static_assert(sizeof(Header32)==32);
struct Fixture {
 alignas(16)std::array<std::byte,0x200>jomini{},actor{},app{};
 alignas(16)std::array<std::byte,0x100>gfx{},first{},root{},context{};
 alignas(16)std::array<std::byte,0x300>handler{};
 alignas(16)std::array<std::byte,0xA20>controller{};
 std::array<std::array<std::byte,0x48>,1>selected_rows{};
 std::vector<char>name_heap,description_heap;
 Core core{};ReadonlyBindings bindings{};RiteTextFrame267V1 frame{};RiteTextRequest267V1 request{};
 void*game=reinterpret_cast<void*>(0x1000),*storage=reinterpret_cast<void*>(0x2000),*jo=nullptr;
 bool creating=true,core_ok=true,core_drift=false,wrong_name_getter=false,throw_predicate=false,throw_setter=false;
 bool expire_setter=false,description_noop=true,foreign_modal=false,control_drift=false;
 unsigned getters=0,predicates=0,set_name=0,set_description=0,captures=0,drift_name_at=0,drift_desc_at=0,drift_dirty_at=0;
 std::string copied_name_input,copied_description_input;
 Fixture(){Reset();}
 void Field(std::size_t offset,const std::string&text,bool force_heap=false){
  Header32 h;h.length=text.size();auto&heap=offset==0x920?name_heap:description_heap;
  if(text.size()<=15&&!force_heap){std::memcpy(h.data.data(),text.data(),text.size());h.data[text.size()]=std::byte{};}
  else {heap.assign(text.begin(),text.end());heap.push_back(0);const auto address=reinterpret_cast<std::uintptr_t>(heap.data());std::memcpy(h.data.data(),&address,8);h.capacity=(std::max)(std::uint64_t{16},h.length);}
  std::memcpy(controller.data()+offset,&h,sizeof(h));
 }
 void Name(const std::string&s,bool heap=false){Field(0x920,s,heap);}
 void Description(const std::string&s,bool heap=false){Field(0x9E0,s,heap);}
 void Dirty(std::uint8_t name,std::uint8_t description){Put(controller,0x940,name);Put(controller,0xA00,description);}
 void Query(){request.action=RiteTextAction267V1::query;request.provider_generation=0;request.query_sequence=0;request.text.clear();}
 void Write(RiteTextAction267V1 kind,const std::string&text){request.action=kind;request.provider_generation=7;request.query_sequence=11;request.text=text;Need(RiteTextRequestShape267V1(request),"actual Wire request-shape positive");}
 void Reset(){
  active=this;tick=10;readonly_ok=create_image_ok=true;bad_receiver=0;
  jomini={};actor={};app={};gfx={};first={};root={};context={};handler={};controller={};selected_rows={};
  core={};core.clock={53144328,3,true};core.local_player_id=1;core.map_ready=core.has_played_character=core.played_character_alive=true;core.played_character_id=0;
  jo=jomini.data();bindings={};bindings.module_base=image;bindings.exact_image_admitted=true;bindings.core.enabled=true;bindings.core.image_build=xar::ck3_1210::ImageBuildV1::full11126785313;
  bindings.core.game_state_slot=&game;bindings.core.jomini_state_slot=&jo;bindings.core.character_storage_slot=&storage;
  frame={};frame.facts_verified=true;frame.core=core;frame.game=reinterpret_cast<std::uintptr_t>(game);frame.jomini=Ptr(jomini);frame.storage=reinterpret_cast<std::uintptr_t>(storage);frame.actor=Ptr(actor);
  request={};request.expected=core;request.expected_source_rite_id=17;const std::string id="rite-text-native-test";std::copy(id.begin(),id.end(),request.request_id.begin());request.request_id_size=static_cast<std::uint8_t>(id.size());
  request.deadline_unix_ms=static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count())+60000;
  Put(actor,0x18,std::int32_t{0});Put(actor,0x1C,std::uint32_t{0x43686172});
  Put(jomini,0,image+0x4B45FE0);Put(jomini,0x10,Ptr(gfx));Put(jomini,0x18,Ptr(app));
  Put(gfx,0,image+0x4B24748);Put(gfx,0x20,Ptr(jomini));Put(gfx,0x88,Ptr(handler));
  Put(handler,0,image+0x4B22578);Put(handler,0x58,image+0x4B22558);Put(handler,0x278,Ptr(controller));
  Put(controller,0,image+0x4C09438);Put(controller,0x10,image+0x4C09410);Put(controller,0x98,Ptr(jomini));Put(controller,0xA0,Ptr(handler));Put(controller,0x60,Ptr(root));Put(controller,0xC8,std::uint32_t{17});Put(controller,0xCC,std::int32_t{0});
  Put(app,0x1B8,Ptr(first));Put(first,0x58,Ptr(context));
  Put(controller,0x798,reinterpret_cast<std::uintptr_t>(selected_rows.data()));Put(controller,0x7A0,std::int32_t{1});Put(controller,0x7A4,std::int32_t{1});
  RiteDraftV2 draft;draft.controller=Ptr(controller);draft.source_rite_id=17;draft.piety_cost_raw=100000;draft.piety_missing_raw=0;draft.window.window_found=true;draft.window.context=Ptr(context);draft.window.requested_name="rite_creation_window";
  GuiWindowNodeV1 n;n.widget=Ptr(root);n.context=Ptr(context);n.visible=n.enabled=true;n.name="rite_creation_window";draft.window.tree.push_back(n);frame.draft=draft;
  creating=core_ok=description_noop=true;core_drift=wrong_name_getter=throw_predicate=throw_setter=expire_setter=foreign_modal=control_drift=false;
  getters=predicates=set_name=set_description=captures=drift_name_at=drift_desc_at=drift_dirty_at=0;copied_name_input.clear();copied_description_input.clear();Name("Initial");Description("Original description");Dirty(0,0);Query();
 }
 bool Read(RiteTextRaw267V1&out,std::string&why){return ReadRiteTextRaw267V1(bindings,frame,request,1000,out,why);}
 bool Values(RiteTextValues267V1&out,std::string&why){return ReadRiteTextValues267V1(bindings,Ptr(controller),request.deadline_unix_ms,1000,out,why);}
 RiteTextCall267V1 Call(const RiteTextRaw267V1&out){return CallRiteTextRaw267V1(bindings,frame,request,1000,out);}
 unsigned SetterCalls()const{return set_name+set_description;}
};
bool __fastcall IsCreating(const void*self){Guard(active&&self==reinterpret_cast<void*>(Ptr(active->controller)));++active->predicates;if(active->throw_predicate)RaiseException(0xE0410002,0,0,nullptr);return active->creating;}
const void*__fastcall GetName(const void*self){Guard(active&&self==reinterpret_cast<void*>(Ptr(active->controller)));const auto call=++active->getters;
 if(call==active->drift_name_at)active->Name("Changed");if(call==active->drift_desc_at)active->Description("Changed description");if(call==active->drift_dirty_at)active->Dirty(1,0);
 return reinterpret_cast<void*>(Ptr(active->controller)+(active->wrong_name_getter?0x940:0x920));}
std::string InputCopy(const void*value){
 Guard(value!=nullptr&&(reinterpret_cast<std::uintptr_t>(value)&7)==0);Header32 h;std::memcpy(&h,value,sizeof(h));Guard(h.length==active->request.text.size()&&h.length<=1600&&h.capacity>=h.length);
 const char*bytes=nullptr;if(h.capacity<=15){Guard(h.length<=15);bytes=reinterpret_cast<const char*>(h.data.data());}else{std::uintptr_t p=0;std::memcpy(&p,h.data.data(),8);Guard(p==reinterpret_cast<std::uintptr_t>(active->request.text.c_str()));bytes=reinterpret_cast<const char*>(p);}
 Guard(bytes&&bytes[h.length]==0);std::string copied(bytes,static_cast<std::size_t>(h.length));Guard(copied==active->request.text);return copied;
}
void __fastcall SetName(void*self,const void*value){Guard(active&&self==reinterpret_cast<void*>(Ptr(active->controller)));++active->set_name;if(active->throw_setter)RaiseException(0xE0410003,0,0,nullptr);active->copied_name_input=InputCopy(value);active->Name(active->copied_name_input);active->Dirty(1,0);if(active->expire_setter)tick=1000;}
void __fastcall SetDescription(void*self,const void*value){Guard(active&&self==reinterpret_cast<void*>(Ptr(active->controller)));++active->set_description;if(active->throw_setter)RaiseException(0xE0410004,0,0,nullptr);active->copied_description_input=InputCopy(value);if(!active->description_noop){active->Description(active->copied_description_input);active->Dirty(0,1);}if(active->expire_setter)tick=1000;}
std::uintptr_t Address(std::uintptr_t rva)noexcept{switch(rva){case 0x16B9260:return reinterpret_cast<std::uintptr_t>(&IsCreating);case 0x16BB5A0:return reinterpret_cast<std::uintptr_t>(&GetName);case 0x16B8720:return reinterpret_cast<std::uintptr_t>(&SetName);case 0x16B8B90:return reinterpret_cast<std::uintptr_t>(&SetDescription);default:Guard(false);return 0;}}
}
namespace xar::ck3_1210 {
bool ReadCoreSnapshot(const CoreBindings&b,CoreSnapshotPrefix&out)noexcept{if(!b.enabled||!rite_text_test::active)return false;out=rite_text_test::active->core;if(rite_text_test::active->core_drift)out.clock.date_raw+=24;return rite_text_test::active->core_ok;}
void*ResolveCoreCharacter(const CoreBindings&b,std::int32_t id)noexcept{return b.enabled&&rite_text_test::active&&id==rite_text_test::active->core.played_character_id?rite_text_test::active->actor.data():nullptr;}
}
namespace xar::ck3_121003::build26785313 {
bool VerifyReadonlyImage(std::uintptr_t i)noexcept{return i==rite_text_test::image&&rite_text_test::readonly_ok;}
bool VerifyRiteCreateImage267V1(std::uintptr_t i)noexcept{return i==rite_text_test::image&&rite_text_test::create_image_ok;}
GuiControlImage267V2 BindGuiControlImage267V2(std::uintptr_t i,std::string_view)noexcept{return{i,i==rite_text_test::image};}
bool CaptureGuiControlWindow267V2(const GuiControlImage267V2&i,const GuiWindowV1&w,ck3_1210::GuiControlCaptureV1&out,std::string&)noexcept{
 auto*f=rite_text_test::active;rite_text_test::Guard(f&&i.module_base==rite_text_test::image&&!w.tree.empty()&&w.tree.front().widget==rite_text_test::Ptr(f->root));out.complete=true;out.context=rite_text_test::Ptr(f->context);out.root=rite_text_test::Ptr(f->root);
 ck3_1210::GuiControlIdentityV1 row;row.widget=0x3333;row.context=out.context;row.row.runtime_name="name_input";row.row.effective_visible=row.row.enabled=true;row.row.widget_id=++f->captures>=2&&f->control_drift?2:1;out.widgets.push_back(row);
 if(f->foreign_modal){out.modal_receivers.push_back(0x5555);out.modal_flags.push_back(0);}return true;
}
bool ReadRiteDoctrineItems267V1(const ReadonlyBindings&,std::uintptr_t self,RiteDoctrineItems267V1&out,std::string&)noexcept{
 auto*f=rite_text_test::active;rite_text_test::Guard(f&&self==rite_text_test::Ptr(f->controller));out.controller=self;RiteDoctrineItemKey267V1 row;row.item=reinterpret_cast<std::uintptr_t>(f->selected_rows.data());row.key.exact_bytes="des_doctrine_dynastic";out.values.push_back(row);return true;
}
}
int main(){using namespace rite_text_test;try{
 auto*allocation=VirtualAlloc(nullptr,kImageSize,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);Need(allocation!=nullptr,"owned synthetic image allocation");image=reinterpret_cast<std::uintptr_t>(allocation);
 for(const auto&p:rite_text_pins::kPins)std::memcpy(reinterpret_cast<void*>(image+p.rva),p.bytes.data(),p.bytes.size());for(const auto&p:rite_text_pins::kPointers){const auto value=image+p.target;std::memcpy(reinterpret_cast<void*>(image+p.slot),&value,sizeof(value));}
 Fixture f;std::string why;RiteTextRaw267V1 raw;RiteTextValues267V1 values;
 auto done=[&](bool ok,const char*label){Need(ok,label);++total_cases;};
 done(VerifyRiteTextImage267V1(image),"actual text pin checker on self-owned synthetic module");
 done(f.Read(raw,why)&&raw.source.name=="Initial"&&raw.source.description=="Original description"&&raw.source.write_admissible,"actual field reads/name getter receiver");
 for(const std::string&text:std::vector<std::string>{"",std::string(15,'x'),std::string(16,'h'),std::string("A\0B",3),"#P literal text#!","\xE5\xAE\x97\xE6\x97\x8F"}){
  f.Reset();f.Name(text);done(f.Values(values,why)&&values.name==text,"SSO/heap/embeddedNUL/richtext/UTF8 exact read");
 }
 f.Reset();f.Name("forced heap",true);done(f.Values(values,why)&&values.name=="forced heap","small heap CString32 follows pointer only when capacity>15");
 f.Reset();f.Description(std::string(4096,'z'));done(f.Values(values,why)&&values.description.size()==4096,"4096-byte read boundary");
 for(int kind=0;kind<7;++kind){f.Reset();
  if(kind==0)Put(f.controller,0x930,std::uint64_t{4097});
  if(kind==1){Put(f.controller,0x930,std::uint64_t{5});Put(f.controller,0x938,std::uint64_t{4});}
  if(kind==2){Put(f.controller,0x930,std::uint64_t{16});Put(f.controller,0x938,std::uint64_t{15});}
  if(kind==3)Put(f.controller,0x920+7,std::uint8_t{'x'}); // Original length7 terminator corrupted.
  if(kind==4){Put(f.controller,0x920,std::uintptr_t{1});Put(f.controller,0x930,std::uint64_t{1});Put(f.controller,0x938,std::uint64_t{16});}
  if(kind==5)f.Name(std::string("\xC0\xAF",2));
  if(kind==6)f.wrong_name_getter=true;
  done(!f.Values(values,why),"invalid length/cap/terminator/heap/UTF8/exactGetter rejected");
 }
 f.Reset();f.Dirty(1,1);done(f.Read(raw,why)&&raw.values.name_dirty==1&&raw.values.description_dirty==1,"dirty1 is actual valid DATA");
 for(int which=0;which<2;++which){f.Reset();f.Dirty(which==0?2:0,which==1?2:0);done(!f.Values(values,why),"dirty>1 unavailable, not coerced true");}
 for(int kind=0;kind<3;++kind){f.Reset();if(kind==0)f.drift_name_at=2;if(kind==1)f.drift_desc_at=2;if(kind==2)f.drift_dirty_at=2;done(!f.Values(values,why),"two value/header/dirty samples must match");}
 f.Reset();f.control_drift=true;done(!f.Read(raw,why),"whole control capture drift rejected");
 for(const std::string&text:std::vector<std::string>{"plain",std::string(15,'s'),std::string(16,'h'),std::string(30,'q')}){
  f.Reset();Need(f.Read(raw,why),"setter baseline read");f.Write(RiteTextAction267V1::set_name,text);const auto call=f.Call(raw);
  done(call.entered&&call.status==RiteTextCallStatus267V1::returned&&call.cleanup_known&&f.set_name==1&&f.copied_name_input==text&&bad_receiver==0,"actual CUTF8String32 typed name setter");
  f.request.text.assign(200,'!');f.Query();RiteTextRaw267V1 after;done(f.Read(after,why)&&after.source.name==text&&after.values.name_dirty==1,"fresh post-call name/header/dirty owns copied input, not caller alias");
 }
 f.Reset();Need(f.Read(raw,why),"description noop baseline");const auto old_description=raw.source.description;f.Write(RiteTextAction267V1::set_description,"new description heap input");auto call=f.Call(raw);done(call.entered&&call.status==RiteTextCallStatus267V1::returned&&f.set_description==1&&f.copied_description_input=="new description heap input","actual desc CUTF8String32 input/void return");f.Query();done(f.Read(raw,why)&&raw.source.description==old_description&&raw.values.description_dirty==0,"description no-op requires fresh query, not applied credit");
 f.Reset();f.description_noop=false;Need(f.Read(raw,why),"description-copy baseline");f.Write(RiteTextAction267V1::set_description,"short");call=f.Call(raw);f.request.text="poison";f.Query();done(call.entered&&f.Read(raw,why)&&raw.source.description=="short"&&raw.values.description_dirty==1,"mock apply mode proves synchronous temporary copy, not live setter behavior");
 for(int kind=0;kind<9;++kind){f.Reset();Need(f.Read(raw,why),"preentry baseline");f.Write(RiteTextAction267V1::set_name,"new");
  if(kind==0)f.creating=false;if(kind==1)Put(f.controller,0xC8,std::uint32_t{18});if(kind==2)Put(f.controller,0xCC,std::int32_t{1});if(kind==3)f.frame.draft->piety_cost_raw+=1;
  if(kind==4)f.selected_rows[0][0]=std::byte{1};if(kind==5)f.Name("different");if(kind==6)f.Description("different");if(kind==7)f.Dirty(1,0);if(kind==8)tick=1000;
  call=f.Call(raw);done(!call.entered&&f.SetterCalls()==0,"pre-entry creating/source/actor/draft/selected/name/desc/dirty/deadline drift causes0 setter calls");
 }
 f.Reset();f.creating=false;done(f.Read(raw,why)&&!raw.source.is_creating&&!raw.source.write_admissible,"creatingfalse read is DATA");
 f.Reset();f.foreign_modal=true;done(f.Read(raw,why)&&raw.source.blocked_by_unrelated_modal&&!raw.source.write_admissible,"unrelated modal read DATA blocks write");
 f.Reset();Need(f.Read(raw,why),"realshape negative baseline");f.request.action=RiteTextAction267V1::set_name;f.request.provider_generation=7;f.request.query_sequence=11;f.request.text=std::string("a\0b",3);call=f.Call(raw);done(!call.entered&&!f.SetterCalls(),"real Wire rejects write NUL before setter");
 f.Reset();Need(f.Read(raw,why),"post expiry baseline");f.Write(RiteTextAction267V1::set_name,"new");f.expire_setter=true;call=f.Call(raw);done(call.entered&&call.status==RiteTextCallStatus267V1::indeterminate&&f.set_name==1,"post-entry expiry not returned/applied");
 f.Reset();Need(f.Read(raw,why),"SEH baseline");f.Write(RiteTextAction267V1::set_name,"new");f.throw_setter=true;call=f.Call(raw);done(call.entered&&!call.cleanup_known&&call.status==RiteTextCallStatus267V1::indeterminate,"setter SEH remains unknown after entry");
 f.Reset();f.throw_predicate=true;done(!f.Read(raw,why)&&!raw.cleanup_known&&f.SetterCalls()==0,"creating predicate SEH cleanup unknown and no effect");
 f.Reset();f.core_drift=true;done(!f.Read(raw,why)&&!f.SetterCalls(),"Core drift rejects before text call");
 f.Reset();Put(f.actor,0x18,std::int32_t{-2});Put(f.controller,0xCC,std::int32_t{-2});f.core.played_character_id=f.frame.core.played_character_id=f.request.expected.played_character_id=-2;done(f.Read(raw,why),"full signed actor -2 retained; baseline0 already exercised");
 RiteTextResult267V1 result;result.effect_attempted=result.native_returned=result.native_handled=true;result.reason="NoGame owner authority not supplied";const auto json=SerializeRiteTextResult267V1("test",result);done(json.find("\"native_handled\":false")!=std::string::npos&&json.find("\"text_applied\":false")!=std::string::npos,"actual Wire never upgrades void return to handled/applied");
 Need(bad_receiver==0,"strict controller receivers maintained");VirtualFree(allocation,0,MEM_RELEASE);std::cout<<"NoGame text native-call cases="<<total_cases<<" passed; Source model only, no ABI/live credit\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
