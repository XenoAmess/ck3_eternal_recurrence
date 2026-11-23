// NoGame source only. Actual candidate Raw, self-owned memory and explicit mocks.
// Native owner alone compiles/runs this. No live ABI or business credit follows.
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
#ifndef XAR_CK3_ENABLE_121003_26785313_RITE_CREATION_BLOCKERS_V1
#define XAR_CK3_ENABLE_121003_26785313_RITE_CREATION_BLOCKERS_V1 1
#endif
#include "xar_bridge/ck3_121003_rite_creation_blockers26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_rite_creation_blockers26785313_pins_v1.hpp"
namespace rite_blockers_test {
std::uintptr_t image=0;ULONGLONG tick=10;bool wrong_module=false;
HMODULE Module(LPCWSTR name)noexcept{return name==nullptr?reinterpret_cast<HMODULE>(image+(wrong_module?4096:0)):nullptr;}
ULONGLONG Tick()noexcept{return tick;}
std::uintptr_t Address(std::uintptr_t)noexcept;
}
#define GetModuleHandleW rite_blockers_test::Module
#define GetTickCount64 rite_blockers_test::Tick
#define XAR_RITE_BLOCKERS_CALL_ADDRESS(image,rva) (static_cast<void>(image), rite_blockers_test::Address(rva))
#ifndef XAR_RITE_BLOCKERS_TEST_RAW_SOURCE
#define XAR_RITE_BLOCKERS_TEST_RAW_SOURCE "ck3_121003_rite_creation_blockers26785313_raw_v1.cpp"
#endif
#include XAR_RITE_BLOCKERS_TEST_RAW_SOURCE
#undef XAR_RITE_BLOCKERS_CALL_ADDRESS
#undef GetTickCount64
#undef GetModuleHandleW

namespace rite_blockers_test {
using namespace xar::ck3_121003::build26785313;
using Core=xar::ck3_1210::CoreSnapshotPrefix;
struct Fixture;Fixture*active=nullptr;
unsigned cases=0,bad_receiver=0,unexpected_calls=0;
bool readonly_ok=true,create_image_ok=true;
void Need(bool value,const char*label){if(!value)throw std::runtime_error(label);}
void Guard(bool value){if(!value){++bad_receiver;RaiseException(0xE0421001,0,0,nullptr);}}
template<std::size_t N>std::uintptr_t Ptr(std::array<std::byte,N>&a){return reinterpret_cast<std::uintptr_t>(a.data());}
template<std::size_t N,class T>void Put(std::array<std::byte,N>&a,std::size_t offset,T value){Need(offset+sizeof(value)<=N,"self-owned fixture write bounds");std::memcpy(a.data()+offset,&value,sizeof(value));}
struct Header32{std::array<std::byte,16>data{};std::uint64_t length=0,capacity=15;};
static_assert(sizeof(Header32)==32);
struct Fixture{
 alignas(16)std::array<std::byte,0x200>jomini{},actor{},app{};
 alignas(16)std::array<std::byte,0x100>gfx{},first{},root{},context{},controller{},other_actor{};
 alignas(16)std::array<std::byte,0x300>handler{};
 Core core{};ReadonlyBindings bindings{};RiteBlockersFrame267V1 frame{};RiteBlockersRequest267V1 request{};
 void*game=reinterpret_cast<void*>(0x1000),*storage=reinterpret_cast<void*>(0x2000),*jo=nullptr,*last_owned=nullptr;
 std::string text="blocked";std::vector<char>heap;
 unsigned predicates=0,getters=0,cleanups=0,core_reads=0;
 bool creating=true,can_create=false,core_ok=true,resolve_other=false;
 bool force_heap=false,wrong_return=false,throw_getter=false,throw_cleanup=false,throw_predicate=false;
 bool expire_predicate=false,expire_getter=false,core_drift_after_getter=false,scope_drift_after_getter=false;
 bool text_drift=false,bool_drift=false,draft_drift=false;
 int malformed=0;
 Fixture(){Reset();}
 void Actor(std::int32_t id){core.played_character_id=frame.core.played_character_id=request.expected.played_character_id=id;Put(actor,0x18,id);Put(controller,0xCC,id);}
 void Reset(){
  active=this;tick=10;wrong_module=false;readonly_ok=create_image_ok=true;bad_receiver=unexpected_calls=0;
  jomini={};actor={};app={};gfx={};first={};root={};context={};handler={};controller={};other_actor={};heap.clear();last_owned=nullptr;
  core={};core.clock={53144328,3,true};core.local_player_id=1;core.map_ready=core.has_played_character=core.played_character_alive=true;core.played_character_id=0;
  game=reinterpret_cast<void*>(0x1000);storage=reinterpret_cast<void*>(0x2000);jo=jomini.data();
  bindings={};bindings.module_base=image;bindings.exact_image_admitted=true;bindings.core.enabled=true;bindings.core.image_build=xar::ck3_1210::ImageBuildV1::full11126785313;
  bindings.core.game_state_slot=&game;bindings.core.jomini_state_slot=&jo;bindings.core.character_storage_slot=&storage;
  frame={};frame.facts_verified=true;frame.core=core;frame.game=reinterpret_cast<std::uintptr_t>(game);frame.storage=reinterpret_cast<std::uintptr_t>(storage);frame.jomini=Ptr(jomini);frame.actor=Ptr(actor);
  request={};request.expected=core;request.expected_source_rite_id=0;const std::string id="blockers-native-nogame";std::copy(id.begin(),id.end(),request.request_id.begin());request.request_id_size=static_cast<std::uint8_t>(id.size());
  request.deadline_unix_ms=static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count())+60000;
  Put(actor,0x18,std::int32_t{0});Put(actor,0x1C,std::uint32_t{0x43686172});Put(actor,0x1D0,std::uintptr_t{0});
  Put(jomini,0,image+0x4B45FE0);Put(jomini,0x10,Ptr(gfx));Put(jomini,0x18,Ptr(app));
  Put(gfx,0,image+0x4B24748);Put(gfx,0x20,Ptr(jomini));Put(gfx,0x88,Ptr(handler));
  Put(handler,0,image+0x4B22578);Put(handler,0x58,image+0x4B22558);Put(handler,0x278,Ptr(controller));
  Put(controller,0,image+0x4C09438);Put(controller,0x10,image+0x4C09410);Put(controller,0x98,Ptr(jomini));Put(controller,0xA0,Ptr(handler));
  Put(controller,0x60,Ptr(root));Put(controller,0x68,Ptr(context));Put(controller,0xC8,std::uint32_t{0});Put(controller,0xCC,std::int32_t{0});
  Put(app,0x1B8,Ptr(first));Put(first,0x58,Ptr(context));
  RiteDraftV2 draft;draft.controller=Ptr(controller);draft.source_rite_id=0;draft.piety_cost_raw=100000;draft.piety_missing_raw=0;
  draft.window.window_found=true;draft.window.context=Ptr(context);draft.window.requested_name="rite_creation_window";
  GuiWindowNodeV1 node;node.widget=Ptr(root);node.context=Ptr(context);node.name="rite_creation_window";node.visible=node.enabled=true;draft.window.tree.push_back(node);frame.draft=draft;
  text="blocked";creating=true;can_create=false;core_ok=true;resolve_other=false;
  force_heap=wrong_return=throw_getter=throw_cleanup=throw_predicate=false;
  expire_predicate=expire_getter=core_drift_after_getter=scope_drift_after_getter=false;text_drift=bool_drift=draft_drift=false;
  predicates=getters=cleanups=core_reads=0;malformed=0;
 }
 bool Read(RiteBlockersRaw267V1&out,std::string&why){return ReadRiteBlockersRaw267V1(bindings,frame,request,1000,out,why);}
};
bool __fastcall IsCreating(const void*self){
 Guard(active&&self==reinterpret_cast<void*>(Ptr(active->controller)));++active->predicates;
 if(active->throw_predicate)RaiseException(0xE0421002,0,0,nullptr);
 if(active->expire_predicate)tick=1000;
 return active->bool_drift&&active->getters>0?!active->creating:active->creating;
}
bool __fastcall CanCreate(const void*self,void*blocker){
 Guard(active&&self==reinterpret_cast<void*>(Ptr(active->controller))&&blocker==nullptr);++active->predicates;return active->can_create;
}
void*__fastcall GetBlockers(const void*self,void*out){
 Guard(active&&self==reinterpret_cast<void*>(Ptr(active->controller))&&out&&(reinterpret_cast<std::uintptr_t>(out)&7)==0);
 Header32 empty;std::memcpy(&empty,out,32);Guard(empty.length==0&&empty.capacity==15&&empty.data[0]==std::byte{});
 auto&f=*active;f.last_owned=out;++f.getters;
 const std::string value=f.text_drift&&f.getters==2?f.text+" changed":f.text;
 Header32 h;h.length=value.size();
 if(value.size()<=15&&!f.force_heap){std::memcpy(h.data.data(),value.data(),value.size());h.data[value.size()]=std::byte{};}
 else{f.heap.assign(value.begin(),value.end());f.heap.push_back(0);const auto p=reinterpret_cast<std::uintptr_t>(f.heap.data());std::memcpy(h.data.data(),&p,8);h.capacity=(std::max)(std::uint64_t{16},h.length);}
 switch(f.malformed){
  case 1:h.length=16385;h.capacity=16385;break;
  case 2:h.length=5;h.capacity=4;break;
  case 3:h.length=16;h.capacity=15;break;
  case 4:if(h.capacity<=15)h.data[static_cast<std::size_t>(h.length)]=std::byte{'!'};else f.heap.back()='!';break;
  case 5:{const std::uintptr_t bad=1;std::memcpy(h.data.data(),&bad,8);h.length=1;h.capacity=16;break;}
  case 6:{const std::uintptr_t null=0;std::memcpy(h.data.data(),&null,8);h.length=1;h.capacity=16;break;}
 }
 std::memcpy(out,&h,32);
 if(f.throw_getter)RaiseException(0xE0421003,0,0,nullptr); // Owned output already partially initialized.
 if(f.expire_getter)tick=1000;
 if(f.core_drift_after_getter)f.core.clock.date_raw+=24;
 if(f.scope_drift_after_getter)Put(f.controller,0x68,std::uintptr_t{0});
 if(f.draft_drift)f.frame.draft->piety_cost_raw+=1;
 return f.wrong_return?reinterpret_cast<void*>(std::uintptr_t{1}):out;
}
void __fastcall Cleanup(void*object){
 Guard(active&&object==active->last_owned);++active->cleanups;
 if(active->throw_cleanup)RaiseException(0xE0421004,0,0,nullptr);
 // Explicit mock: lifetime/poisoning is our own. Does not emulate native allocator ABI.
 std::fill(active->heap.begin(),active->heap.end(),'!');active->heap.clear();Header32 empty;std::memcpy(object,&empty,32);
}
std::uintptr_t Address(std::uintptr_t rva)noexcept{
 switch(rva){case 0x16B9260:return reinterpret_cast<std::uintptr_t>(&IsCreating);case 0x16BA410:return reinterpret_cast<std::uintptr_t>(&CanCreate);case 0x16BA4C0:return reinterpret_cast<std::uintptr_t>(&GetBlockers);case 0x897460:return reinterpret_cast<std::uintptr_t>(&Cleanup);default:++unexpected_calls;Guard(false);return 0;}
}
}
namespace xar::ck3_1210 {
bool ReadCoreSnapshot(const CoreBindings&b,CoreSnapshotPrefix&out)noexcept{auto*f=rite_blockers_test::active;if(!b.enabled||!f||!f->core_ok)return false;++f->core_reads;out=f->core;return true;}
void*ResolveCoreCharacter(const CoreBindings&b,std::int32_t id)noexcept{auto*f=rite_blockers_test::active;return b.enabled&&f&&id!=-1&&id==f->core.played_character_id?(f->resolve_other?f->other_actor.data():f->actor.data()):nullptr;}
}
namespace xar::ck3_121003::build26785313 {
bool VerifyReadonlyImage(std::uintptr_t i)noexcept{return i==rite_blockers_test::image&&rite_blockers_test::readonly_ok;}
bool VerifyRiteCreateImage267V1(std::uintptr_t i)noexcept{return i==rite_blockers_test::image&&rite_blockers_test::create_image_ok;}
}

int main(){using namespace rite_blockers_test;try{
 // Only three known code-pin pages committed. Never executes these bytes or reads a game.
 void*allocation=VirtualAlloc(nullptr,kImageSize,MEM_RESERVE,PAGE_NOACCESS);Need(allocation!=nullptr,"reserve self-owned synthetic image");image=reinterpret_cast<std::uintptr_t>(allocation);
 for(const auto&p:rite_creation_blockers_pins::kPins){const auto begin=p.rva&~std::uintptr_t{4095};const auto end=(p.rva+p.bytes.size()+4095)&~std::uintptr_t{4095};Need(VirtualAlloc(reinterpret_cast<void*>(image+begin),end-begin,MEM_COMMIT,PAGE_READWRITE)!=nullptr,"commit actual pin pages");std::memcpy(reinterpret_cast<void*>(image+p.rva),p.bytes.data(),p.bytes.size());}
 Fixture f;RiteBlockersRaw267V1 out;std::string why;
 auto done=[&](bool ok,const char*label){Need(ok,label);Need(unexpected_calls==0&&bad_receiver==0,"no Create/Accept/unbound or wrong typed-self call");++cases;};
 done(VerifyRiteBlockersImage267V1(image),"actual3pin verifier on explicitly owned image");
 done(f.Read(out,why)&&why.empty()&&out.source.sampled_twice&&out.source.blockers_text=="blocked"&&!out.source.native_can_create&&out.source.is_creating&&out.entered&&out.cleanup_known&&f.getters==2&&f.cleanups==2,"two actual Raw samples and typed self/output/cleanup");
 const std::vector<std::string>valid={"",std::string(15,'s'),std::string(16,'h'),std::string("A\0B",3),"#N blocker#!\n\t",std::string("\xE5\xAE\x97\xE6\x97\x8F",6),std::string(16384,'z')};
 for(const auto&value:valid){f.Reset();f.text=value;done(f.Read(out,why)&&out.source.blockers_text==value&&out.source.sampled_twice&&f.cleanups==2,"SSO heap NUL richtext UTF8 and16KiB exact bounded DATA");}
 f.Reset();f.text="small";f.force_heap=true;done(f.Read(out,why)&&out.source.blockers_text=="small"&&f.cleanups==2,"short heap CString32 follows capacity, output copied before mock poison");
 f.Reset();f.text.clear();f.creating=false;f.can_create=false;done(f.Read(out,why)&&!out.source.is_creating&&!out.source.native_can_create&&out.source.blockers_text.empty(),"false creating false Can and empty text remain DATA");
 f.Reset();f.can_create=true;done(f.Read(out,why)&&out.source.native_can_create,"true Can remains readonly DATA, no Create");
 f.Reset();f.frame.draft->window.tree.front().visible=false;f.frame.draft->window.tree.front().enabled=false;done(f.Read(out,why)&&!out.source.window_visible&&!out.source.window_enabled,"hidden disabled DATA does not mint action permission");
 for(int kind=1;kind<=6;++kind){f.Reset();f.malformed=kind;done(!f.Read(out,why)&&f.getters==1&&f.cleanups==1&&out.cleanup_known,"bad length cap SSO terminator inaccessible/null heap rejected with best-effort cleanup");}
 for(const auto&value:std::vector<std::string>{std::string("\xC0\xAF",2),std::string("\xED\xA0\x80",3),std::string("\xF4\x90\x80\x80",4),std::string("\x80",1),std::string("\xE2\x82",2)}){f.Reset();f.text=value;done(!f.Read(out,why)&&f.cleanups==1,"invalid overlong surrogate range/truncated UTF8 never coerced/truncated");}
 f.Reset();f.wrong_return=true;done(!f.Read(out,why)&&!out.cleanup_known&&f.getters==1&&f.cleanups==1,"wrong returned pointer never dereferenced and owned output cleanup attempted");
 f.Reset();f.text=std::string(40,'p');f.throw_getter=true;done(!f.Read(out,why)&&!out.cleanup_known&&f.getters==1&&f.cleanups==1,"partially initialized getter SEH still best-effort owned cleanup");
 f.Reset();f.throw_cleanup=true;done(!f.Read(out,why)&&!out.cleanup_known&&f.getters==1&&f.cleanups==1,"destructor SEH remains cleanup unknown");
 f.Reset();f.throw_predicate=true;done(!f.Read(out,why)&&!out.cleanup_known&&f.getters==0&&f.cleanups==0,"predicate SEH never calls getter or mutation");
 f.Reset();tick=1000;done(!f.Read(out,why)&&f.predicates==0&&f.getters==0,"expired original monotonic deadline before native entry");
 f.Reset();f.request.deadline_unix_ms=1;done(!f.Read(out,why)&&f.getters==0,"expired original wall deadline no getter");
 f.Reset();f.expire_predicate=true;done(!f.Read(out,why)&&f.getters==0,"post predicate expiry does not start owned getter");
 f.Reset();f.expire_getter=true;done(!f.Read(out,why)&&f.getters==1&&f.cleanups==1,"post getter expiry still cleans owned CString before rejection");
 for(int kind=0;kind<3;++kind){f.Reset();f.text_drift=kind==0;f.bool_drift=kind==1;f.draft_drift=kind==2;done(!f.Read(out,why)&&f.getters==2&&f.cleanups==2&&why=="rite_creation_blockers_actual_source_changed_between_samples","two text predicate or full-draft sample drift fails closed");}
 f.Reset();f.core_drift_after_getter=true;done(!f.Read(out,why)&&f.getters==1&&f.cleanups==1,"post-call Core date drift rejects complete source");
 f.Reset();f.scope_drift_after_getter=true;done(!f.Read(out,why)&&f.getters==1&&f.cleanups==1,"post-call actual context drift rejects complete source");
 for(int kind=0;kind<14;++kind){f.Reset();
  if(kind==0)Put(f.controller,0,std::uintptr_t{0});if(kind==1)Put(f.controller,0x10,image+0x4C09588);if(kind==2)Put(f.controller,0x98,std::uintptr_t{0});
  if(kind==3)Put(f.controller,0xA0,std::uintptr_t{0});if(kind==4)Put(f.controller,0x60,std::uintptr_t{0});if(kind==5)Put(f.controller,0x68,std::uintptr_t{0});
  if(kind==6)Put(f.controller,0xC8,std::uint32_t{1});if(kind==7)Put(f.controller,0xCC,std::int32_t{1});if(kind==8)Put(f.handler,0x278,std::uintptr_t{0});
  if(kind==9)Put(f.first,0x58,std::uintptr_t{0});if(kind==10)f.frame.draft->window.requested_name="wrong_window";if(kind==11)f.frame.draft->window.tree.front().name="wrong_root";
  if(kind==12)f.frame.draft.reset();if(kind==13)Put(f.gfx,0x20,std::uintptr_t{0});
  done(!f.Read(out,why)&&f.getters==0,"exact complete controller VT root context owner actor sourceRite scope required");
 }
 for(int kind=0;kind<13;++kind){f.Reset();
  if(kind==0)f.core.clock.date_raw+=24;if(kind==1)f.core.clock.speed+=1;if(kind==2)f.core.clock.paused=false;if(kind==3)f.core.local_player_id=2;
  if(kind==4)f.core.map_ready=false;if(kind==5)f.core.has_played_character=false;if(kind==6)f.core.played_character_alive=false;if(kind==7)f.core.played_character_id=1;
  if(kind==8)f.game=reinterpret_cast<void*>(0x3000);if(kind==9)f.storage=reinterpret_cast<void*>(0x4000);if(kind==10)f.jo=nullptr;if(kind==11)f.resolve_other=true;if(kind==12)f.core_ok=false;
  done(!f.Read(out,why)&&f.getters==0,"dual original Core world/role identity enforced before getter");
 }
 f.Reset();f.Actor(-2);done(f.Read(out,why)&&out.source.actor_id==-2,"full signed actor-2 is valid; baseline0 already proved");
 f.Reset();f.Actor(-1);done(!f.Read(out,why)&&f.getters==0,"invalid actor sentinel does not resolve to fake character");
 f.Reset();Put(f.actor,0x1C,std::uint32_t{0});done(!f.Read(out,why)&&f.getters==0,"Char magic/high-half pollution rejected");
 f.Reset();Put(f.actor,0x1D0,std::uintptr_t{1});done(!f.Read(out,why)&&f.getters==0,"actual dead actor rejected");
 f.Reset();f.bindings.exact_image_admitted=false;done(!f.Read(out,why)&&f.getters==0,"explicit exact image admission still required");
 f.Reset();f.frame.facts_verified=false;done(!f.Read(out,why)&&f.getters==0,"owner facts not bypassed by CString mock");
 f.Reset();wrong_module=true;done(!f.Read(out,why)&&f.getters==0,"GetModuleHandle mismatch rejects synthetic native read");
 f.Reset();readonly_ok=false;done(!f.Read(out,why)&&f.getters==0,"Readonly image seam remains explicit gate");
 f.Reset();create_image_ok=false;done(!f.Read(out,why)&&f.getters==0,"existing Create image gate retained, not asserted by this test");
 f.Reset();const auto&p=rite_creation_blockers_pins::kPins[0];auto*byte=reinterpret_cast<std::byte*>(image+p.rva);const auto saved=*byte;*byte^=std::byte{1};done(!f.Read(out,why)&&f.getters==0,"actual pin-byte drift rejects");*byte=saved;
 Need(VirtualFree(allocation,0,MEM_RELEASE)!=0,"release own synthetic pages");
 std::cout<<"NoGame Raw blockers cases="<<cases<<"; 0 Create/Accept/unbound calls; mock-only, not live ABI qualification\n";return 0;
 }catch(const std::exception&e){std::cerr<<"NoGame blockers failure: "<<e.what()<<"\n";return 1;}}
