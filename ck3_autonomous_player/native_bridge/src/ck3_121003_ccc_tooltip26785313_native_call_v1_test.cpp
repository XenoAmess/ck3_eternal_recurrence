// External Source-only NoGame test. Native owner alone compiles/runs it.
// Includes the ACTUAL private Raw helper; does not replace that implementation.
// Synthetic module pages contain only the actual three code pins. Never calls
// executable image bytes, Confirm, NativeCan, GUI traversal or another SDK API.
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
#include "xar_bridge/ck3_121003_ccc_tooltip26785313_pins_v1.hpp"

namespace ccc_tooltip_test {
std::uintptr_t image=0;ULONGLONG tick=10;
ULONGLONG Tick()noexcept{return tick;}
std::uintptr_t Address(std::uintptr_t image_arg,std::uintptr_t rva)noexcept;
unsigned unused_raw_traps=0;
}
// The public complete-GUI paths are deliberately OFF. The private helper being
// tested is unconditional and its real three-span pin verifier is never stubbed.
#if defined(XAR_CK3_ENABLE_121003_26785313_CCC_DECISION_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_DECISION_V1
#error This private-tooltip test must not enable the public complete-GUI path
#endif
#define GetTickCount64 ccc_tooltip_test::Tick
#define XAR_CCC_TOOLTIP_CALL_ADDRESS(image,rva) ccc_tooltip_test::Address(image,rva)
#ifndef XAR_CCC_TOOLTIP_RAW_SOURCE
#define XAR_CCC_TOOLTIP_RAW_SOURCE "ck3_121003_ccc_decision26785313_raw_v1.cpp"
#endif
#include XAR_CCC_TOOLTIP_RAW_SOURCE
#undef XAR_CCC_TOOLTIP_CALL_ADDRESS
#undef GetTickCount64

namespace ccc_tooltip_test {
namespace current=xar::ck3_121003::build26785313;
unsigned cases=0,bad_abi=0,unexpected_calls=0;
void Need(bool yes,const char*label){if(!yes)throw std::runtime_error(label);}
void Guard(bool yes){if(!yes){++bad_abi;RaiseException(0xE0431001,0,0,nullptr);}}
struct Header32{std::array<std::byte,16>storage{};std::uint64_t length=0,capacity=15;};
static_assert(sizeof(Header32)==32&&offsetof(Header32,length)==16&&offsetof(Header32,capacity)==24);
struct Fixture;Fixture*active=nullptr;
struct Fixture {
 alignas(16)std::array<std::byte,0x320>detail{};
 std::string input="blocked",output="prior output must clear";
 std::vector<char>heap;
 std::uint64_t wall=0,mono=1000;
 void*owned_output=nullptr;
 unsigned getters=0,cleanups=0;
 bool clean=false,entered=true,force_heap=false,wrong_return=false,throw_getter=false,throw_cleanup=false;
 bool expire_getter=false,expire_cleanup=false;
 int malformed=0;
 Fixture(){Reset();}
 std::uintptr_t Detail()const{return reinterpret_cast<std::uintptr_t>(detail.data());}
 void Reset(){
  active=this;tick=10;bad_abi=unexpected_calls=unused_raw_traps=0;detail={};
  const auto vt=image+current::aub_decision_abi::kDecisionDetailVtable;
  std::memcpy(detail.data(),&vt,sizeof(vt));
  const auto secondary=image+current::aub_decision_abi::kDecisionDetailSecondary10;
  std::memcpy(detail.data()+16,&secondary,sizeof(secondary));
  input="blocked";output="prior output must clear";heap.clear();owned_output=nullptr;
  const auto now=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
  wall=static_cast<std::uint64_t>(now)+60000;mono=1000;
  getters=cleanups=0;clean=false;entered=true;
  force_heap=wrong_return=throw_getter=throw_cleanup=expire_getter=expire_cleanup=false;malformed=0;
 }
 bool Read(){return current::ReadCccConfirmTooltip267V1(image,Detail(),wall,mono,output,clean,entered);}
};
void* __fastcall Get(const void*self,void*out){
 auto&f=*active;Guard(self==f.detail.data()&&out&&(reinterpret_cast<std::uintptr_t>(out)&7)==0);
 Header32 initial;std::memcpy(&initial,out,sizeof(initial));
 Guard(initial.length==0&&initial.capacity==15&&initial.storage.front()==std::byte{});
 f.owned_output=out;++f.getters;
 Header32 h;h.length=f.input.size();
 if(f.input.size()<=15&&!f.force_heap){
  std::memcpy(h.storage.data(),f.input.data(),f.input.size());h.storage[f.input.size()]=std::byte{};
 }else{
  f.heap.assign(f.input.begin(),f.input.end());f.heap.push_back(0);
  const auto ptr=reinterpret_cast<std::uintptr_t>(f.heap.data());std::memcpy(h.storage.data(),&ptr,sizeof(ptr));
  h.capacity=(std::max)(std::uint64_t{16},h.length);
 }
 switch(f.malformed){
  case 1:h.length=16385;h.capacity=16385;break;
  case 2:h.length=5;h.capacity=4;break;
  case 3:h.length=16;h.capacity=15;break;
  case 4:h.capacity=14;break;
  case 5:h.capacity=0x10000001ULL;break;
  case 6:if(h.capacity==15)h.storage[static_cast<std::size_t>(h.length)]=std::byte{'!'};else f.heap.back()='!';break;
  case 7:{const std::uintptr_t p=0;std::memcpy(h.storage.data(),&p,8);h.length=1;h.capacity=16;break;}
  case 8:{const std::uintptr_t p=1;std::memcpy(h.storage.data(),&p,8);h.length=1;h.capacity=16;break;}
  case 9:h.capacity=(std::numeric_limits<std::uint64_t>::max)();break;
 }
 std::memcpy(out,&h,sizeof(h));
 if(f.expire_getter)tick=f.mono;
 if(f.throw_getter)RaiseException(0xE0431002,0,0,nullptr); // Own output already partially initialized.
 return f.wrong_return?static_cast<std::byte*>(out)+8:out;
}
void __fastcall Destroy(void*object){
 auto&f=*active;Guard(object&&object==f.owned_output);++f.cleanups;
 if(f.throw_cleanup)RaiseException(0xE0431003,0,0,nullptr);
 // Mock owns this vector, never a native allocator. Poisoning proves the helper
 // copied the bytes before releasing scratch, including short forced-heap text.
 std::fill(f.heap.begin(),f.heap.end(),'!');f.heap.clear();
 Header32 empty;std::memcpy(object,&empty,sizeof(empty));
 if(f.expire_cleanup)tick=f.mono;
}
std::uintptr_t Address(std::uintptr_t image_arg,std::uintptr_t rva)noexcept{
 Guard(image_arg==image);
 switch(rva){
  case 0x1603C90:return reinterpret_cast<std::uintptr_t>(&Get);
  case 0x897460:return reinterpret_cast<std::uintptr_t>(&Destroy);
  default:++unexpected_calls;RaiseException(0xE0431004,0,0,nullptr);return 0;
 }
}
}

// Explicit traps satisfy unused full-Raw dependencies without granting a GUI,
// actor, role or decision source. None may be reached by this helper test.
namespace xar::ck3_1210 {
void*ResolveCoreCharacter(const CoreBindings&,std::int32_t)noexcept{++ccc_tooltip_test::unused_raw_traps;return nullptr;}
}
namespace xar::ck3_121003::build26785313 {
bool CccCaseAdmitted267V1(const ck3_1210::CoreSnapshotPrefix&,std::uint64_t,std::uintptr_t,std::uintptr_t)noexcept{++ccc_tooltip_test::unused_raw_traps;return false;}
bool VerifyCccRoleImage267V1(std::uintptr_t)noexcept{++ccc_tooltip_test::unused_raw_traps;return false;}
std::optional<CccDecision267V1>ParseCccDecisionKey267V1(std::string_view)noexcept{++ccc_tooltip_test::unused_raw_traps;return std::nullopt;}
}

int main(){using namespace ccc_tooltip_test;try{
 void*allocation=VirtualAlloc(nullptr,current::kImageSize,MEM_RESERVE,PAGE_NOACCESS);
 Need(allocation!=nullptr,"reserve own synthetic module");image=reinterpret_cast<std::uintptr_t>(allocation);
 for(const auto&p:current::ccc_tooltip_pins::kPins){
  const auto begin=p.rva&~std::uintptr_t{4095};const auto end=(p.rva+p.bytes.size()+4095)&~std::uintptr_t{4095};
  Need(VirtualAlloc(reinterpret_cast<void*>(image+begin),end-begin,MEM_COMMIT,PAGE_READWRITE)!=nullptr,"commit own actual pin pages");
  std::memcpy(reinterpret_cast<void*>(image+p.rva),p.bytes.data(),p.bytes.size());
 }
 Fixture f;
 const auto done=[&](bool yes,const char*label){Need(yes,label);Need(bad_abi==0&&unexpected_calls==0&&unused_raw_traps==0,"no wrong receiver, Confirm, NativeCan, GUI, role, or other ABI call");++cases;};
 done(current::CccTooltipPins267V1(image),"actual3span verifier succeeds only on filled owned module");
 done(f.Read()&&f.output=="blocked"&&f.clean&&f.entered&&f.getters==1&&f.cleanups==1,"real private Raw helper calls typed owned receiver/output and official-cleanup seam");
 const std::vector<std::string>valid={"",std::string(15,'s'),std::string(16,'h'),std::string("A\0B",3),
  "#N Cooldown#!\n\t",std::string("\xE5\x86\xB7\xE5\x8D\xB4",6),std::string("\0\1\2\7\10\13\14\33\177",9),std::string(16384,'z')};
 for(const auto&text:valid){f.Reset();f.input=text;
  done(f.Read()&&f.output==text&&f.output.size()==text.size()&&f.clean&&f.entered&&f.getters==1&&f.cleanups==1,
   "empty/SSO/heap/embeddedNUL/controls/richtext/UTF8/16KiB exact DATA, not C-string truncation");}
 for(const auto&text:std::vector<std::string>{"", "short"}){f.Reset();f.input=text;f.force_heap=true;
  done(f.Read()&&f.output==text&&f.clean&&f.cleanups==1,"capacity selects even short/empty heap, copy survives scratch poisoning");}
 for(int malformed=1;malformed<=9;++malformed){f.Reset();f.malformed=malformed;
  done(!f.Read()&&f.output.empty()&&f.clean&&f.entered&&f.getters==1&&f.cleanups==1,
   "overlength/badcap/SSO overflow/unboundedcap/unterminated/null or unreadable heap reject after owned cleanup");}
 for(const auto&text:std::vector<std::string>{std::string("\xC0\xAF",2),std::string("\xED\xA0\x80",3),
  std::string("\xF4\x90\x80\x80",4),std::string("\x80",1),std::string("\xE2\x82",2),std::string("\xF5\x80\x80\x80",4)}){
  f.Reset();f.input=text;done(!f.Read()&&f.output.empty()&&f.clean&&f.entered&&f.cleanups==1,"invalid UTF8 is refused without coercion/truncation and still cleaned");}
 f.Reset();f.input=std::string(16385,'z');done(!f.Read()&&f.output.empty()&&f.clean&&f.cleanups==1,"actual over16KiB payload refused, not truncated");
 f.Reset();f.wrong_return=true;done(!f.Read()&&f.output.empty()&&!f.clean&&f.entered&&f.getters==1&&f.cleanups==1,"return pointer must equal owned out; still destroy owned scratch once");
 f.Reset();f.input=std::string(40,'p');f.throw_getter=true;
 done(!f.Read()&&f.output.empty()&&!f.clean&&f.entered&&f.getters==1&&f.cleanups==1,"getter SEH after partial owned output triggers best-effort cleanup, remains unknown");
 f.Reset();f.throw_cleanup=true;done(!f.Read()&&f.output.empty()&&!f.clean&&f.entered&&f.getters==1&&f.cleanups==1,"cleanup SEH keeps unknown, no text or automatic retry");
 f.Reset();f.expire_getter=true;done(!f.Read()&&f.output.empty()&&f.clean&&f.entered&&f.getters==1&&f.cleanups==1,"postgetter deadline expiry still destroys owned scratch and rejects result");
 f.Reset();f.expire_cleanup=true;done(!f.Read()&&f.output.empty()&&f.clean&&f.entered&&f.getters==1&&f.cleanups==1,"expiry during cleanup preserves known cleanup but rejects returned text");
 for(int kind=0;kind<4;++kind){f.Reset();if(kind==0)f.wall=0;if(kind==1)f.wall=1;if(kind==2)f.mono=0;if(kind==3)tick=f.mono;
  done(!f.Read()&&f.output.empty()&&f.clean&&!f.entered&&f.getters==0&&f.cleanups==0,"preentry wall or monotonic deadline failure causes zero native calls");}
 f.Reset();done(!current::ReadCccConfirmTooltip267V1(0,f.Detail(),f.wall,f.mono,f.output,f.clean,f.entered)&&f.output.empty()&&f.clean&&!f.entered&&f.getters==0&&f.cleanups==0,"zero image no entry");
 f.Reset();done(!current::ReadCccConfirmTooltip267V1(image,0,f.wall,f.mono,f.output,f.clean,f.entered)&&f.output.empty()&&f.clean&&!f.entered&&f.getters==0&&f.cleanups==0,"zero detail no entry");
 for(const auto&p:current::ccc_tooltip_pins::kPins){f.Reset();auto*byte=reinterpret_cast<std::byte*>(image+p.rva);const auto saved=*byte;*byte^=std::byte{1};
  const bool accepted=f.Read();*byte=saved;
  done(!accepted&&f.output.empty()&&f.clean&&!f.entered&&f.getters==0&&f.cleanups==0,"any actual pin span drift refuses before getter/dtor");}
 Need(VirtualFree(allocation,0,MEM_RELEASE)!=0,"release self-owned synthetic pin pages");
 std::cout<<"PASS NoGame CCC private Raw tooltip cases="<<cases<<"; getter/dtor only, no Confirm; mocks do not grant live ABI, fullGUI or cooldown expiry\n";return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL NoGame CCC tooltip: "<<e.what()<<'\n';return 1;}}
