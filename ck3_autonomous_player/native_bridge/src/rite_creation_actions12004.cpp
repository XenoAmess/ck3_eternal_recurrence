#include "xar_bridge/rite_creation_actions12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_religion_bindings.hpp"
#include "xar_bridge/ck3_12004_religion_draft_bindings.hpp"
#include "xar_bridge/religion_ui12004.hpp"
#include "xar_bridge/religion_doctrine12002_tenet_rows.hpp"
#include <algorithm>
#include <array>
#include <cstring>
#include <limits>
#include <mutex>
#include <unordered_set>
#include <utility>
#if defined(_WIN32)
#include <windows.h>
#include <bcrypt.h>
#endif
#ifndef XAR_ENABLE_RITE_CREATION_ACTIONS12004
#define XAR_ENABLE_RITE_CREATION_ACTIONS12004 0
#endif

namespace xar::ck3_12004::religion::rite_creation_actions {
namespace {
namespace reform=ck3_12002::religion_reform;
namespace doctrine=ck3_12002::religion::doctrine12002;
const void*At(const void*p,std::size_t o) noexcept {
 auto v=reinterpret_cast<std::uintptr_t>(p);
 return v&&o<=std::numeric_limits<std::uintptr_t>::max()-v?reinterpret_cast<const void*>(v+o):nullptr;
}
template<class T>bool Read(const Bindings&b,const void*p,std::size_t o,T&v) noexcept {
 auto*q=At(p,o);return q&&b.read_memory&&b.read_memory(b.read_context,q,&v,sizeof(v));
}
bool ProcessRead(void*,const void*p,void*out,std::size_t n) noexcept {
#if defined(_WIN32)
 SIZE_T got=0;return p&&out&&n&&ReadProcessMemory(GetCurrentProcess(),p,out,n,&got)&&got==n;
#else
 (void)p;(void)out;(void)n;return false;
#endif
}
struct Header {const void*data=nullptr;std::int32_t capacity=0,count=0;std::uint64_t allocator=0;
 bool operator==(const Header&)const=default;};
static_assert(sizeof(Header)==24);
bool Array(const Bindings&b,const void*p,std::size_t o,Header&h,std::int32_t limit=8192) noexcept {
 return Read(b,p,o,h)&&h.count>=0&&h.capacity>=h.count&&h.count<=limit&&h.capacity<=limit*2&&(!h.count||h.data);
}
bool String(const Bindings&b,const void*p,std::string&out,std::size_t limit=16384) {
 std::array<unsigned char,32>h{},again{};
 if(!Read(b,p,0,h))return false;
 std::uint64_t size=0,capacity=0;std::memcpy(&size,h.data()+16,8);std::memcpy(&capacity,h.data()+24,8);
 if(size>limit||capacity<size||capacity>16*1024*1024||(capacity<16&&capacity!=15))return false;
 const void*data=p;if(capacity>=16)std::memcpy(&data,h.data(),sizeof(data));
 std::string value(static_cast<std::size_t>(size)+1,'\0');
 if(!data||!b.read_memory(b.read_context,data,value.data(),value.size())||value.back()!=0||
    std::find(value.begin(),value.end()-1,'\0')!=value.end()-1||!Read(b,p,0,again)||again!=h)return false;
 value.pop_back();out=std::move(value);return true;
}
bool Definition(const Bindings&b,const void*p,bool tenet,std::string&key,std::string&group) {
 std::uint32_t magic=0;const void*group_def=nullptr;
 if(!p||!Read(b,p,0x38,magic)||magic!=0x4744624FU||!String(b,At(p,0x18),key,128)||key.empty())return false;
 if(!tenet&&(!Read(b,p,0xB08,group_def)||!group_def||!String(b,At(group_def,0x18),group,128)||group.empty()))return false;
 return true;
}
bool AsciiKey(std::string_view s) noexcept {
 return !s.empty()&&s.size()<=128&&std::all_of(s.begin(),s.end(),[](unsigned char c){return
  (c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='_';});
}
bool Utf8Text(std::string_view s,std::size_t max_characters,bool multiline) noexcept {
 std::size_t i=0,count=0;
 while(i<s.size()){
  const auto c=static_cast<unsigned char>(s[i++]);std::uint32_t cp=c;unsigned continuation=0;
  if(c<0x80){}
  else if(c>=0xC2&&c<=0xDF){cp=c&31;continuation=1;}
  else if(c>=0xE0&&c<=0xEF){cp=c&15;continuation=2;}
  else if(c>=0xF0&&c<=0xF4){cp=c&7;continuation=3;}
  else return false;
  const unsigned length=continuation;
  if(continuation>s.size()-i)return false;
  while(continuation--){const auto d=static_cast<unsigned char>(s[i++]);if((d&0xC0)!=0x80)return false;cp=(cp<<6)|(d&63);}
  if((length==1&&cp<0x80)||(length==2&&cp<0x800)||(length==3&&cp<0x10000)||cp>0x10FFFF||
     (cp>=0xD800&&cp<=0xDFFF)||cp==0||cp==0x7F||(cp<32&&!(multiline&&(cp==10||cp==9))))return false;
  if(++count>max_characters)return false;
 }
 return true;
}
struct BorrowedUtf8 {
 std::array<unsigned char,16>storage{};std::uint64_t size=0,capacity=15;
 explicit BorrowedUtf8(const std::string&s):size(s.size()) {
  if(s.size()<16)std::memcpy(storage.data(),s.c_str(),s.size()+1);
  else {const char*p=s.c_str();std::memcpy(storage.data(),&p,sizeof(p));capacity=s.size();}
 }
 // The caller's std::string owns the long bytes throughout the original call.
 // This explicit native value is never passed to a native destructor.
};
static_assert(sizeof(BorrowedUtf8)==32);
struct Any {void*type=nullptr;std::array<unsigned char,32>data{};};
static_assert(sizeof(Any)==40);
struct Pin {std::uintptr_t rva;std::string_view bytes;};
#include "rite_creation_actions12004_pins.inc"
bool Pins(const Bindings&b) noexcept {
 for(const auto&p:kRiteCreationPins){
  std::array<unsigned char,32>actual{};
  if(p.bytes.size()%2||p.bytes.size()>64||!b.read_memory||
     !b.read_memory(b.read_context,reinterpret_cast<const void*>(b.image_base+p.rva),actual.data(),p.bytes.size()/2))return false;
  auto digit=[](char c)->int{return c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:-1;};
  for(std::size_t i=0;i<p.bytes.size()/2;++i){auto h=digit(p.bytes[2*i]),l=digit(p.bytes[2*i+1]);
   if(h<0||l<0||actual[i]!=static_cast<unsigned char>(h*16+l))return false;}
 }
 return true;
}
bool CallVoid(const Bindings&b,std::uintptr_t rva,const void*a,bool&attempted) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {attempted=true;reinterpret_cast<void(__fastcall*)(const void*)>(b.image_base+rva)(a);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)rva;(void)a;(void)attempted;return false;
#endif
}
bool CallPair(const Bindings&b,std::uintptr_t rva,const void*a,const void*v,bool&attempted) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {attempted=true;reinterpret_cast<void(__fastcall*)(const void*,const void*)>(b.image_base+rva)(a,v);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)rva;(void)a;(void)v;(void)attempted;return false;
#endif
}
bool CallBool(const Bindings&b,std::uintptr_t rva,const void*object,bool&value) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {value=reinterpret_cast<bool(__fastcall*)(const void*)>(b.image_base+rva)(object);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)rva;(void)object;(void)value;return false;
#endif
}
bool Materialize(const Bindings&b,const void*w,std::uint32_t slot,bool&attempted) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {attempted=true;reinterpret_cast<void(__fastcall*)(const void*,std::int32_t)>(b.image_base+0x14F1930)(At(w,0x888),static_cast<std::int32_t>(slot));return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)w;(void)slot;(void)attempted;return false;
#endif
}
bool Open(const Bindings&b,void*handler,std::uint32_t rite,bool&attempted) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {
  Any value{};value.type=reinterpret_cast<void*(__fastcall*)()>(b.image_base+0xB19A70)();
  std::uintptr_t vt=0,visitor=0,destroy=0,copy=0;
  if(reinterpret_cast<std::uintptr_t>(value.type)!=b.image_base+0x54D70E0||!Read(b,value.type,0,vt)||vt!=b.image_base+0x44B9360||
     !Read(b,reinterpret_cast<const void*>(vt),0x50,visitor)||visitor!=b.image_base+0xB1AAE0||
     !Read(b,reinterpret_cast<const void*>(vt),0x18,destroy)||destroy!=b.image_base+0x8522C0||
     !Read(b,reinterpret_cast<const void*>(vt),0x58,copy)||copy!=b.image_base+0x8771F0)return false;
  std::memcpy(value.data.data(),&rite,sizeof(rite));attempted=true;
  reinterpret_cast<void(__fastcall*)(void*,std::int32_t,const void*)>(b.image_base+0xAF39E0)(handler,0x3C,&value);return true;
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)handler;(void)rite;(void)attempted;return false;
#endif
}
bool PopupManager(const Bindings&b,const void*&out) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {out=reinterpret_cast<void*(__fastcall*)()>(b.image_base+0xC45DF0)();return out!=nullptr;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;out=nullptr;return false;
#endif
}
bool ModalCan(const Bindings&b,const void*p,bool editing,bool&value) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {value=reinterpret_cast<bool(__fastcall*)(const void*)>(b.image_base+(editing?0x14F1450:0x14F1170))(p);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)p;(void)editing;(void)value;return false;
#endif
}
bool NewCommand(const Bindings&b,bool edit,void*&command) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {command=reinterpret_cast<void*(__fastcall*)()>(b.image_base+(edit?0x29A9930:0x29A98D0))();return command!=nullptr;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)edit;command=nullptr;return false;
#endif
}
bool DeleteCommand(const Bindings&b,void*command) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {reinterpret_cast<void*(__fastcall*)(void*,std::uint32_t)>(b.image_base+0x29A1EA0)(command,1);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)command;return false;
#endif
}
bool ReplaceDraft(const Bindings&b,void*command,const void*actual_draft,bool&draft_live) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {
  draft_live=false;auto*destination=static_cast<unsigned char*>(command)+0x28;
  reinterpret_cast<void(__fastcall*)(void*)>(b.image_base+0x14F2FC0)(destination);
  if(reinterpret_cast<void*(__fastcall*)(void*,const void*)>(b.image_base+0x29A1EF0)(destination,actual_draft)!=destination)return false;
  draft_live=true;return true;
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)command;(void)actual_draft;(void)draft_live;return false;
#endif
}
struct NativeCString {std::array<unsigned char,32>bytes{};};
struct WriterInputs {
 std::array<std::uint8_t,2>flags{};
 std::vector<const void*>tenets,doctrines;
 std::vector<std::uint8_t>doctrine_skip_flags;
 bool operator==(const WriterInputs&)const=default;
};
bool CommandText(const Bindings&b,NativeCString&out,const void*command) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {return reinterpret_cast<void*(__fastcall*)(void*,const void*)>(b.image_base+0x37F2060)(out.bytes.data(),command)==out.bytes.data();}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)out;(void)command;return false;
#endif
}
bool DestroyString(const Bindings&b,NativeCString&out) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {reinterpret_cast<void(__fastcall*)(void*)>(b.image_base+0x856050)(out.bytes.data());return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)out;return false;
#endif
}
bool PrivateOne(const Bindings&b,std::uintptr_t rva,const void*p) noexcept {bool ignored=false;return CallVoid(b,rva,p,ignored);}
bool PrivatePair(const Bindings&b,std::uintptr_t rva,const void*p,const void*v) noexcept {bool ignored=false;return CallPair(b,rva,p,v,ignored);}
bool AssignBytes(const Bindings&b,void*destination,const char*bytes,std::uint64_t length) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {return reinterpret_cast<void*(__fastcall*)(void*,const void*,std::uint64_t)>(b.image_base+0x855DB0)(destination,bytes,length)==destination;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)destination;(void)bytes;(void)length;return false;
#endif
}
bool AssignText(const Bindings&b,void*destination,const void*source) {
 std::string bytes;return String(b,source,bytes,1024*1024)&&AssignBytes(b,destination,bytes.c_str(),bytes.size());
}
bool BorrowedSourceName(const Bindings&b,const void*faith,const void*&text) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {text=reinterpret_cast<const void*(__fastcall*)(const void*)>(b.image_base+0x24410A0)(faith);return text!=nullptr;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)faith;text=nullptr;return false;
#endif
}
const void*Resolve(const Bindings&b,std::uintptr_t global,std::uint32_t id) noexcept {
 const void*storage=nullptr,*rows=nullptr,*object=nullptr;std::uint32_t count=0,full=absent;
 if(id==absent||!Read(b,reinterpret_cast<const void*>(b.image_base+global),0,storage)||!storage||
    !Read(b,storage,0x20,rows)||!rows||!Read(b,storage,0x2C,count)||(id&0xFFFFFFU)>=count||
    !Read(b,rows,static_cast<std::size_t>(id&0xFFFFFFU)*16+8,object)||!object||
    !Read(b,object,8,full)||full!=id)return nullptr;
 return object;
}
bool Contains(const Bindings&b,const void*vector,const void*definition,bool&found) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {found=reinterpret_cast<bool(__fastcall*)(const void*,const void*)>(b.image_base+0xA11CC0)(vector,&definition);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)vector;(void)definition;(void)found;return false;
#endif
}
bool AddTenetStatus(const Bindings&b,const void*core,const void*definition) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {reinterpret_cast<void(__fastcall*)(const void*,const void*,std::uint8_t)>(b.image_base+0x2591A40)(core,definition,4);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)core;(void)definition;return false;
#endif
}
bool FinalizePrivateDraft(const Bindings&b,void*command,std::uint32_t source,bool edit,const WriterInputs&inputs,std::string&why) {
 auto fail=[&](const char*v){why=v;return false;};
 const void*rite=Resolve(b,0x5D1E2F8,source);std::uint32_t faith_id=absent,religion_id=absent,magic=0;
 if(!rite||!Read(b,rite,0xC,magic)||magic!=0x52697465U||!Read(b,rite,0x4B8,faith_id))return fail("rite_creation_finalize_source_rite_full_reference_unavailable");
 const void*faith=Resolve(b,0x5D1E300,faith_id);
 if(!faith||!Read(b,faith,0x8C,religion_id))return fail("rite_creation_finalize_source_faith_full_reference_unavailable");
 const void*religion=Resolve(b,0x5D1DE88,religion_id),*type=nullptr,*source_name=nullptr;
 if(!religion||!Read(b,religion,0x20,type)||!type)return fail("rite_creation_finalize_religion_type_unavailable");
 auto*p=static_cast<unsigned char*>(command)+0x28;auto*core=p+0x240;
 if(!edit&&!inputs.flags[0]&&(!AssignText(b,p+0x118,At(faith,0x1F0))||!AssignText(b,p+0x138,At(faith,0x210))))return fail("rite_creation_finalize_source_names_unavailable");
 if(!BorrowedSourceName(b,faith,source_name)||!AssignText(b,p+0x178,source_name)||
    !PrivatePair(b,0x14F0A90,p+0x198,At(faith,0x270)))return fail("rite_creation_finalize_source_faith_text_unavailable");
 alignas(16)std::array<unsigned char,0x4F8>temporary{};
 if(!PrivateOne(b,0x14F2670,temporary.data()))return fail("rite_creation_finalize_private_core_constructor_unavailable");
 const bool assigned=PrivatePair(b,0x14F4DC0,core,temporary.data());
 const bool destroyed=PrivateOne(b,0x14F2B50,temporary.data());
 if(!assigned||!destroyed)return fail("rite_creation_finalize_private_core_assignment_or_cleanup_unavailable");
 if(!edit){
  if(!PrivatePair(b,0x2592720,core,At(rite,0x788)))return fail("rite_creation_finalize_source_core_status_unavailable");
  Header borrowed{};borrowed.data=inputs.tenets.data();borrowed.count=borrowed.capacity=static_cast<std::int32_t>(inputs.tenets.size());
  if(!PrivatePair(b,0x2592500,core,&borrowed))return fail("rite_creation_finalize_original_tenet_replacement_unavailable");
 }else{
  for(const auto*definition:inputs.tenets){bool found=false;
   if(!Contains(b,core+8,definition,found)||(!found&&(!PrivatePair(b,0x880340,core+8,&definition)||
      !AddTenetStatus(b,core,definition))))return fail("rite_creation_finalize_original_edit_tenet_status_unavailable");}
 }
 for(std::size_t i=0;i<inputs.doctrines.size();++i){
  if(!edit&&inputs.flags[1]&&inputs.doctrine_skip_flags[i])continue;
  const void*definition=inputs.doctrines[i];bool found=false;
  if(!Contains(b,core+0x50,definition,found)||(!found&&!PrivatePair(b,0x880340,core+0x50,&definition)))return fail("rite_creation_finalize_original_doctrine_append_unavailable");
 }
 if(!PrivatePair(b,0x14F8EF0,core+0x228,At(type,0x648))||!PrivatePair(b,0x14F8EF0,core+0x390,At(type,0x7B0))||
    !PrivateOne(b,0x2591160,core))return fail("rite_creation_finalize_original_religion_vectors_or_recompute_unavailable");
 why.clear();return true;
}
bool NativeCommandText(const Bindings&b,const Frame&f,std::uint32_t source,bool edit,const void*window,const WriterInputs&inputs,std::string&text,std::string&why) {
 text.clear();void*command=nullptr;
 if(!NewCommand(b,edit,command)){why="rite_creation_original_temporary_factory_unavailable";return false;}
 bool draft_live=true;bool ok=false;NativeCString output{};bool output_live=false;
 try{
  std::uintptr_t vt=0,secondary=0,draft_vt=0;std::uint32_t actor=0,source_ref=0;
  if(Read(b,command,0,vt)&&vt==b.image_base+(edit?0x4770498:0x4770560)&&
     Read(b,command,0x18,secondary)&&secondary==b.image_base+(edit?0x4770530:0x4770418)&&
     Read(b,command,0x28,draft_vt)&&draft_vt==b.image_base+0x472FA20&&
     Read(b,command,edit?0x24:0x20,actor)&&actor==absent&&
     (!edit||(Read(b,command,0x20,source_ref)&&source_ref==absent))){
   // This is a newly allocated, provider-owned temporary command, not a game
   // world object or a request pointer. Its fields match original producers.
   actor=static_cast<std::uint32_t>(f.played_character_id);
   std::memcpy(static_cast<unsigned char*>(command)+(edit?0x24:0x20),&actor,sizeof(actor));
   if(edit)std::memcpy(static_cast<unsigned char*>(command)+0x20,&source,sizeof(source));
   if(ReplaceDraft(b,command,At(window,0x8E8),draft_live)&&FinalizePrivateDraft(b,command,source,edit,inputs,why)){
    output_live=CommandText(b,output,command);
    if(output_live)ok=String(b,output.bytes.data(),text,1024*1024);
   }
  }
 }catch(...){ok=false;}
 const bool string_destroyed=!output_live||DestroyString(b,output);
 // Never run a whole-object destructor on a failed placement construction.
 // Such a fault is unavailable with cleanup unknown, and never grants proof.
 const bool command_destroyed=draft_live&&DeleteCommand(b,command);
 if(!ok||!string_destroyed||!command_destroyed){text.clear();if(why.empty())why=!draft_live?"rite_creation_temporary_copy_failed_cleanup_unknown":"rite_creation_original_command_text_or_cleanup_unavailable";return false;}
 why.clear();return true;
}
bool Sha256(std::string_view bytes,std::string&out) {
 out.clear();
#if defined(_WIN32)
 BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;DWORD returned=0,size=0;
 std::array<unsigned char,32>digest{};bool ok=false;
 if(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0)return false;
 if(BCryptGetProperty(algorithm,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&size),sizeof(size),&returned,0)>=0){
  std::vector<unsigned char>storage(size);
  if(BCryptCreateHash(algorithm,&hash,storage.data(),size,nullptr,0,0)>=0){
   ok=bytes.size()<=std::numeric_limits<ULONG>::max()&&BCryptHashData(hash,reinterpret_cast<PUCHAR>(const_cast<char*>(bytes.data())),static_cast<ULONG>(bytes.size()),0)>=0&&
    BCryptFinishHash(hash,digest.data(),static_cast<ULONG>(digest.size()),0)>=0;
   (void)BCryptDestroyHash(hash);
  }
 }
 (void)BCryptCloseAlgorithmProvider(algorithm,0);if(!ok)return false;
 constexpr char hex[]="0123456789abcdef";for(auto byte:digest){out+=hex[byte>>4];out+=hex[byte&15];}return true;
#else
 (void)bytes;return false;
#endif
}
struct Pass {
 const void*window=nullptr,*root=nullptr,*modal=nullptr,*modal_root=nullptr,*modal_context=nullptr,*manager=nullptr;
 Header dialogs{};Result value{};
 WriterInputs writer_inputs{};
 bool modal_gui_enabled=false;
 bool same(const Pass&o)const {return window==o.window&&root==o.root&&modal==o.modal&&modal_root==o.modal_root&&
  modal_context==o.modal_context&&modal_gui_enabled==o.modal_gui_enabled&&manager==o.manager&&dialogs==o.dialogs&&writer_inputs==o.writer_inputs&&value.frame==o.value.frame&&
  value.draft==o.value.draft&&value.modal==o.value.modal&&value.full_can==o.value.full_can&&value.quote==o.value.quote;}
};
bool Owner(const Bindings&b,const Admission&a,const Frame&f) {
 const void*gfx=nullptr,*handler=nullptr;std::uint32_t actor=absent;
 return b.enabled&&b.source_bound&&a.exact_build_admitted&&a.owner_tls_paused_verified&&
  a.jomini_owner&&a.handler&&a.gui_root_state&&a.modal_scope_state&&f.connection_generation&&f.native_revision&&f.capture_epoch&&
  f.played_character_id>0&&Read(b,a.jomini_owner,0x10,gfx)&&gfx&&Read(b,gfx,0x88,handler)&&handler==a.handler&&
  Read(b,reinterpret_cast<const void*>(b.image_base+0x54DBC00),0,actor)&&actor==static_cast<std::uint32_t>(f.played_character_id);
}
bool Capture(const Bindings&b,const Admission&a,const Frame&f,const Request&r,Pass&p,std::string&why) {
 auto fail=[&](const char*v){why=v;return false;};
 if(!Owner(b,a,f))return fail("rite_creation_exact_owner_paused_frame_unverified");
 reform::query::Observation q{};
 if(!ReadPlayedReformQuery12004(BindReformQueryImage12004(b.image_base,ck3_12004::kExecutableSha256),f.capture_epoch,q)||
    !q.available||q.capture_epoch!=f.capture_epoch||q.date_raw!=f.date_raw||q.played_character_id!=f.played_character_id||
    !q.context.available||q.context.rite_id!=r.expected_source_rite_id)
  return fail("rite_creation_current_player_context_changed");
 p.value.operation=r.operation;p.value.frame=f;
 if(r.operation==Operation::confirm_once)p.value.action_id=r.action_id;
 if(!q.current_window.available||!q.current_window.present||!q.current_window.visible||!q.current_window.window||
    q.current_window.source_rite_id!=r.expected_source_rite_id||
    q.current_window.played_character_id!=static_cast<std::uint32_t>(f.played_character_id))
  return fail("rite_creation_original_visible_current_draft_unavailable");
 p.window=q.current_window.window;const void*back=nullptr,*gfx_owner=nullptr;
 if(!Read(b,p.window,0xA0,back)||back!=a.handler||!Read(b,p.window,0x98,gfx_owner)||gfx_owner!=a.jomini_owner||
    !Read(b,p.window,0x60,p.root)||!p.root)return fail("rite_creation_window_owner_or_root_changed");
 bool visible=false,enabled=false;
 if(!a.gui_root_state(a.gui_context,p.root,"rite_creation_window",visible,enabled)||!visible)
  return fail("rite_creation_actual_gui_root_unverified");
 auto&d=p.value.draft;d.observed=true;d.source_rite_id=q.current_window.source_rite_id;
 d.source_faith_id=q.draft_creation_terms.source_faith_id;d.actor_faith_id=q.context.faith_id;
 d.editing_owned_current_rite=q.draft_costs.editing_owned_current_rite;
 d.native_create_faith_or_reform=q.draft_creation_terms.native_create_faith_or_reform;
 if(d.editing_owned_current_rite&&*d.editing_owned_current_rite)d.actual_outcome_kind=Outcome::edit_rite;
 else if(d.editing_owned_current_rite&&d.native_create_faith_or_reform)
  d.actual_outcome_kind=*d.native_create_faith_or_reform?Outcome::create_faith:Outcome::create_rite;
 constexpr std::array<std::size_t,5>offsets{0x918,0x948,0x978,0x9A8,0x9D8};
 for(std::size_t i=0;i<offsets.size();++i){std::string s;if(!String(b,At(p.window,offsets[i]),s))return fail("rite_creation_name_field_unavailable");d.names[i]=std::move(s);}
 d.names_observed=true;Header tenets{},doctrines{};
 if(!Array(b,p.window,0x778,tenets,64)||!Array(b,p.window,0x790,doctrines,64))return fail("rite_creation_selected_rows_unavailable");
 for(std::int32_t i=0;i<tenets.count;++i){const void*def=nullptr;std::string key,group;
  if(!Read(b,tenets.data,static_cast<std::size_t>(i)*0x70+0x28,def)||!Definition(b,def,true,key,group))return fail("rite_creation_selected_tenet_definition_unavailable");
  d.selected_core_tenets.push_back({static_cast<std::uint32_t>(i),std::move(key)});p.writer_inputs.tenets.push_back(def);}
 for(std::int32_t i=0;i<doctrines.count;++i){const void*def=nullptr;std::string key,group;
  if(!Read(b,doctrines.data,static_cast<std::size_t>(i)*0x48+0x28,def)||!Definition(b,def,false,key,group))return fail("rite_creation_selected_doctrine_definition_unavailable");
  std::uint8_t skip=0;if(!Read(b,doctrines.data,static_cast<std::size_t>(i)*0x48+0x40,skip))return fail("rite_creation_original_doctrine_skip_flag_unavailable");
  d.selected_doctrines.push_back({std::move(group),std::move(key)});p.writer_inputs.doctrines.push_back(def);p.writer_inputs.doctrine_skip_flags.push_back(skip);}
 if(!Read(b,p.window,0x1039,p.writer_inputs.flags[0])||!Read(b,p.window,0x103A,p.writer_inputs.flags[1]))return fail("rite_creation_original_finalize_flags_unavailable");
 d.selected_core_tenets_observed=d.selected_doctrines_observed=true;
 p.value.full_can={q.draft_eligibility.available,q.draft_eligibility.can_create_rite,q.draft_eligibility.can_edit_rite,
  q.draft_eligibility.can_create_rite_native_text,q.draft_eligibility.can_edit_rite_native_text};
 p.value.quote={q.draft_costs.available,q.draft_costs.piety_cost_raw,q.draft_costs.piety_missing_signed_raw,q.draft_costs.has_enough_piety};
 if(!PopupManager(b,p.manager)||!Array(b,p.manager,0x18,p.dialogs,128))return fail("rite_creation_original_popup_manager_unavailable");
 std::size_t matching=0,visible_dialogs=0;
 for(std::int32_t i=0;i<p.dialogs.count;++i){const void*dialog=nullptr,*root=nullptr,*window=nullptr,*context=nullptr;std::uintptr_t vt=0;std::uint8_t closed=1;
  if(!Read(b,p.dialogs.data,static_cast<std::size_t>(i)*8,dialog))return fail("rite_creation_owned_dialog_list_unavailable");
  if(!dialog)continue;
  if(!Read(b,dialog,0,vt)||!Read(b,dialog,0xA8,closed)||!Read(b,dialog,0x70,root))return fail("rite_creation_owned_dialog_identity_unavailable");
  if(closed||!root)continue;
  bool shown=false,enabled_dialog=false;
  // Only the exact confirmation type is interpreted as this operation's modal.
  if(vt!=b.image_base+0x4565DB8&&vt!=b.image_base+0x4565D10){++visible_dialogs;continue;}
  const bool edit=vt==b.image_base+0x4565D10;
  std::uintptr_t secondary1=0,secondary2=0,can_target=0,accept_target=0;
  if(!Read(b,dialog,0x10,secondary1)||secondary1!=b.image_base+(edit?0x4565E40:0x4565D98)||
     !Read(b,dialog,0x20,secondary2)||secondary2!=b.image_base+(edit?0x4565E18:0x4565D70)||
     !Read(b,reinterpret_cast<const void*>(vt),0x38,can_target)||can_target!=b.image_base+(edit?0x14F1450:0x14F1170)||
     !Read(b,reinterpret_cast<const void*>(vt),0x48,accept_target)||accept_target!=b.image_base+(edit?0x14F1440:0x14F1160))
   return fail("rite_creation_original_modal_type_or_virtual_target_changed");
  if(!a.gui_root_state(a.gui_context,root,"basic_confirmation_popup",shown,enabled_dialog))return fail("rite_creation_confirmation_root_unverified");
  if(!shown)continue;++visible_dialogs;
  if(!Read(b,dialog,0x130,window)||window!=p.window||!Read(b,dialog,0x78,context))continue;
  ++matching;p.modal=dialog;p.modal_root=root;p.modal_context=context;p.modal_gui_enabled=enabled_dialog;
  bool can=false;
  if(!ModalCan(b,dialog,edit,can))return fail("rite_creation_original_modal_full_can_unavailable");
  p.value.modal={true,ModalStage::confirmation,edit?ModalKind::edit:ModalKind::create,true,true,can};
 }
 if(matching>1||visible_dialogs>1)return fail("rite_creation_original_modal_not_unique");
 if(!matching){if(visible_dialogs)return fail("rite_creation_unrelated_modal_blocks_draft");p.value.modal={true,ModalStage::none,{},{},{},{}};}
 if(!a.modal_scope_state(a.gui_context,p.modal_root))return fail("rite_creation_actual_modal_receiver_scope_unverified");
 Header t2{},d2{},dialogs2{};
 if(!Array(b,p.window,0x778,t2,64)||t2!=tenets||!Array(b,p.window,0x790,d2,64)||d2!=doctrines||
    !Array(b,p.manager,0x18,dialogs2,128)||dialogs2!=p.dialogs||!Owner(b,a,f))return fail("rite_creation_owned_draft_collections_changed");
 p.value.available=true;p.value.status="observed";p.value.unavailable_reason.clear();why.clear();return true;
}
bool Stable(const Bindings&b,const Admission&a,const Frame&f,const Request&r,const Pass&p) {
 Pass next{};std::string why;return Capture(b,a,f,r,next,why)&&next.same(p);
}
void Ack(Result&out,bool invoked,bool writer) {
 out.dispatch_invoked=invoked;out.available=invoked;out.verification_pending=out.native_dispatch_attempted;
 out.original_writer_may_have_been_queued=writer&&out.native_dispatch_attempted;
 out.status=invoked?"acknowledged_verification_pending":out.native_dispatch_attempted?"dispatch_result_unknown":"unavailable";
 out.unavailable_reason=invoked?"":out.native_dispatch_attempted?"original_callback_result_unknown_do_not_retry":"original_callback_unavailable";
}
void CanonicalUnsigned(std::string&out,std::uint64_t value) {
 // Explicit little-endian values, never raw C++ object bytes or pointers.
 for(unsigned i=0;i<8;++i)out.push_back(static_cast<char>((value>>(i*8))&255));
}
void CanonicalText(std::string&out,std::string_view value) {
 CanonicalUnsigned(out,value.size());out.append(value);
}
void CanonicalOptionalBool(std::string&out,const std::optional<bool>&v) {out.push_back(v?(*v?2:1):0);}
bool CompleteCommandPreview(const Bindings&b,const Admission&a,const Frame&f,const Request&r,const Pass&state,Result&out) {
 out.complete_command_payload_observed=false;out.original_writer_inputs_observed=false;
 out.preview_identity_available=false;out.preview_identity.reset();
 auto fail=[&](const char*v){out.unavailable_reason=v;return false;};
 if(!state.value.draft.observed||!state.value.draft.actual_outcome_kind||!state.value.draft.source_rite_id||
    !state.value.draft.source_faith_id||!state.value.draft.actor_faith_id||!state.value.draft.names_observed||
    !state.value.draft.selected_core_tenets_observed||!state.value.draft.selected_doctrines_observed||
    !state.value.full_can.observed||!state.value.full_can.can_create||!state.value.full_can.can_edit||
    !state.value.quote.observed||!state.value.quote.piety_cost_raw||!state.value.quote.piety_missing_signed_raw||
    !state.value.quote.has_enough_piety||!state.value.modal.observed||state.value.modal.stage==ModalStage::unknown)
  return fail("rite_creation_complete_native_preview_component_unavailable");
 const bool edit=*state.value.draft.actual_outcome_kind==Outcome::edit_rite;
 std::string first,second,why;
 if(!NativeCommandText(b,f,r.expected_source_rite_id,edit,state.window,state.writer_inputs,first,why)||
    !NativeCommandText(b,f,r.expected_source_rite_id,edit,state.window,state.writer_inputs,second,why)){
  out.unavailable_reason=why;return false;
 }
 if(first.empty()||first!=second)return fail("rite_creation_original_command_text_empty_or_changed_during_native_preview");
 if(!Stable(b,a,f,r,state))return fail("rite_creation_original_writer_inputs_or_frame_changed_during_preview");
 std::string native_hash;
 if(!Sha256(first,native_hash))return fail("rite_creation_native_command_sha256_unavailable");
 std::string canonical="ck3-1.20.0.4-original-rite-command-text-and-writer-inputs-v1";
 // capture_epoch is transient; admission rechecks the actual epoch on every
 // request. Connection and published revision are private runtime bindings.
 CanonicalUnsigned(canonical,f.connection_generation);CanonicalUnsigned(canonical,f.native_revision);
 CanonicalUnsigned(canonical,static_cast<std::uint32_t>(f.date_raw));CanonicalUnsigned(canonical,static_cast<std::uint32_t>(f.played_character_id));
 const auto&d=state.value.draft;
 CanonicalUnsigned(canonical,*d.source_rite_id);CanonicalUnsigned(canonical,*d.source_faith_id);CanonicalUnsigned(canonical,*d.actor_faith_id);
 CanonicalUnsigned(canonical,static_cast<unsigned>(*d.actual_outcome_kind));
 CanonicalOptionalBool(canonical,d.editing_owned_current_rite);CanonicalOptionalBool(canonical,d.native_create_faith_or_reform);
 CanonicalText(canonical,first);
 for(const auto&name:d.names){canonical.push_back(name?1:0);if(name)CanonicalText(canonical,*name);}
 CanonicalUnsigned(canonical,d.selected_core_tenets.size());
 for(const auto&v:d.selected_core_tenets){CanonicalUnsigned(canonical,v.slot_index);CanonicalText(canonical,v.tenet_key);}
 CanonicalUnsigned(canonical,d.selected_doctrines.size());
 for(std::size_t i=0;i<d.selected_doctrines.size();++i){const auto&v=d.selected_doctrines[i];CanonicalText(canonical,v.group_key);CanonicalText(canonical,v.doctrine_key);CanonicalUnsigned(canonical,state.writer_inputs.doctrine_skip_flags[i]);}
 CanonicalUnsigned(canonical,state.writer_inputs.flags[0]);CanonicalUnsigned(canonical,state.writer_inputs.flags[1]);
 CanonicalOptionalBool(canonical,state.value.full_can.can_create);CanonicalOptionalBool(canonical,state.value.full_can.can_edit);
 CanonicalUnsigned(canonical,static_cast<std::uint64_t>(*state.value.quote.piety_cost_raw));
 CanonicalUnsigned(canonical,static_cast<std::uint64_t>(*state.value.quote.piety_missing_signed_raw));CanonicalOptionalBool(canonical,state.value.quote.has_enough_piety);
 CanonicalUnsigned(canonical,static_cast<unsigned>(state.value.modal.stage));
 canonical.push_back(state.value.modal.kind?1:0);if(state.value.modal.kind)CanonicalUnsigned(canonical,static_cast<unsigned>(*state.value.modal.kind));
 CanonicalOptionalBool(canonical,state.value.modal.active);CanonicalOptionalBool(canonical,state.value.modal.same_draft_window_bound);CanonicalOptionalBool(canonical,state.value.modal.native_can_accept);
 canonical.push_back(state.modal_gui_enabled?1:0);
 std::string identity;if(!Sha256(canonical,identity))return fail("rite_creation_native_preview_sha256_unavailable");
 out.complete_command_payload_observed=true;out.original_writer_inputs_observed=true;
 out.native_command_text_bytes=first.size();out.native_command_text_sha256=std::move(native_hash);
 out.preview_identity_available=true;out.preview_identity=std::move(identity);return true;
}
bool ClaimOnce(const Request&r) {
 // Process-local additional guard. Python's fsynced episode+actor+source
 // intent claim is authoritative across reconnect/restart and new IDs.
 static std::mutex mutex;static std::unordered_set<std::string>actions,proofs;
 const std::lock_guard<std::mutex>lock(mutex);
 if(actions.size()>=4096||proofs.size()>=4096||actions.contains(r.action_id)||proofs.contains(r.expected_preview_identity))return false;
 actions.insert(r.action_id);proofs.insert(r.expected_preview_identity);return true;
}
} // namespace

Bindings BindRiteCreationActionsImage12004(std::uintptr_t base,std::string_view sha) noexcept {
 Bindings b{};if(!XAR_ENABLE_RITE_CREATION_ACTIONS12004||!base||sha!=ck3_12004::kExecutableSha256)return b;
 b.enabled=b.source_bound=true;b.image_base=base;b.read_memory=&ProcessRead;return b;
}
bool ValidateRequest(const Request&r) noexcept {
 if(r.expected_source_rite_id==absent)return false;
 const auto no_selection=[&]{return !r.core_slot_index&&r.tenet_key.empty()&&r.group_key.empty()&&r.doctrine_key.empty()&&!r.name_field&&r.text.empty();};
 switch(r.operation){
  case Operation::open_create_draft:case Operation::open_edit_current_rite_draft:case Operation::preview:
   return no_selection()&&r.expected_preview_identity.empty()&&r.action_id.empty();
  case Operation::select_core_tenet:return r.core_slot_index&&*r.core_slot_index<64&&AsciiKey(r.tenet_key)&&r.group_key.empty()&&r.doctrine_key.empty()&&!r.name_field&&r.text.empty()&&r.expected_preview_identity.empty()&&r.action_id.empty();
  case Operation::select_doctrine:return !r.core_slot_index&&r.tenet_key.empty()&&AsciiKey(r.group_key)&&AsciiKey(r.doctrine_key)&&!r.name_field&&r.text.empty()&&r.expected_preview_identity.empty()&&r.action_id.empty();
  case Operation::set_name_field:return r.name_field&&!r.core_slot_index&&r.tenet_key.empty()&&r.group_key.empty()&&r.doctrine_key.empty()&&r.expected_preview_identity.empty()&&r.action_id.empty()&&
   static_cast<unsigned>(*r.name_field)<=4&&r.text.size()<=(*r.name_field==NameField::description?4096U:256U)&&Utf8Text(r.text,*r.name_field==NameField::description?240:30,*r.name_field==NameField::description);
  case Operation::prepare_confirmation:case Operation::confirm_once:
   return no_selection()&&r.expected_outcome_kind&&r.expected_preview_identity.size()==64&&
    std::all_of(r.expected_preview_identity.begin(),r.expected_preview_identity.end(),[](char c){return(c>='0'&&c<='9')||(c>='a'&&c<='f');})&&
    (r.operation==Operation::prepare_confirmation?r.action_id.empty():!r.action_id.empty()&&r.action_id.size()<=128);
 }
 return false;
}
bool ReadRiteCreationController12004(const Bindings&b,const Admission&a,const Frame&f,const Request&r,Result&out) noexcept {
 out={};out.operation=r.operation;out.frame=f;
 if(r.operation==Operation::confirm_once)out.action_id=r.action_id;
 try{
  if(!ValidateRequest(r)){out.unavailable_reason="rite_creation_request_invalid";return false;}
  if(!Pins(b)){out.unavailable_reason="rite_creation_loaded_source_pins_changed";return false;}
  Pass first{},last{};std::string why;
  if(!Capture(b,a,f,r,first,why)||!Capture(b,a,f,r,last,why)||!first.same(last)){
   out.unavailable_reason=why.empty()?"rite_creation_draft_changed_during_read":why;return false;}
  if(r.expected_outcome_kind&&r.expected_outcome_kind!=first.value.draft.actual_outcome_kind){
   out.unavailable_reason="rite_creation_native_outcome_differs_from_expectation";return false;}
  out=first.value;
  if(!CompleteCommandPreview(b,a,f,r,first,out)){out.available=false;out.status="unavailable";}
  return true;
 }catch(...){out.unavailable_reason="rite_creation_capture_exception";return false;}
}
bool ExecuteRiteCreationAction12004(const Bindings&b,const Admission&a,const Frame&f,const Request&r,Result&out) noexcept {
 out={};out.operation=r.operation;out.frame=f;
 if(r.operation==Operation::confirm_once)out.action_id=r.action_id;
 try{
  auto fail=[&](const char*why){out.available=false;out.verification_pending=out.native_dispatch_attempted;
   out.status=out.native_dispatch_attempted?"unavailable_after_draft_callback":"unavailable";out.unavailable_reason=why;return false;};
  if(!ValidateRequest(r))return fail("rite_creation_request_invalid");
  if(!Pins(b))return fail("rite_creation_loaded_source_pins_changed");
  if(r.operation==Operation::preview)return ReadRiteCreationController12004(b,a,f,r,out);
  if(!a.draft_action_opt_in||!Owner(b,a,f))return fail("rite_creation_explicit_draft_optin_owner_required");
  if(r.operation==Operation::open_create_draft||r.operation==Operation::open_edit_current_rite_draft){
   Result existing{};
   if(ReadRiteCreationController12004(b,a,f,r,existing)){
    const bool edit_requested=r.operation==Operation::open_edit_current_rite_draft;
    if(!existing.draft.actual_outcome_kind||
       ((*existing.draft.actual_outcome_kind==Outcome::edit_rite)!=edit_requested)||
       (r.expected_outcome_kind&&r.expected_outcome_kind!=existing.draft.actual_outcome_kind))
     return fail("rite_creation_existing_native_draft_mode_differs_do_not_reinitialize");
    out=std::move(existing);out.available=true;out.unavailable_reason.clear();out.already_in_requested_state=true;
    out.draft_open_postcondition_observed=true;out.status="already_in_requested_state";return true;
   }
   if(!a.modal_scope_state(a.gui_context,nullptr))return fail("rite_creation_open_blocked_by_effective_visible_modal");
   ck3_12002::religion::Context context{};
   if(!ReadPlayedReligionContext12004(BindReligionContextImage12004(b.image_base,ck3_12004::kExecutableSha256),f.capture_epoch,context)||
      !context.available||context.date_raw!=f.date_raw||context.played_character_id!=f.played_character_id||context.rite_id!=r.expected_source_rite_id)
    return fail("rite_creation_open_current_player_full_source_mismatch");
   religion_ui::Selection faith{};const auto ub=religion_ui::BindImage12004(b.image_base,ck3_12004::kExecutableSha256);
   if(!religion_ui::ReadSelection12004(ub,a.handler,religion_ui::Window::faith,faith)||
      !faith.available||faith.selected_rite_id!=r.expected_source_rite_id||!context.faith_id||faith.subject_id!=*context.faith_id||!a.named_button_state)
    return fail("rite_creation_open_original_faith_window_selection_unverified");
   bool root_visible=false,root_enabled=false;
   if(!a.gui_root_state(a.gui_context,faith.root,"faith_window",root_visible,root_enabled)||!root_visible||!root_enabled)
    return fail("rite_creation_open_original_faith_root_not_enabled");
   const bool edit=r.operation==Operation::open_edit_current_rite_draft;
   std::size_t enabled_count=0;
   for(auto name:edit?std::array<std::string_view,2>{"edit_rite",""}:std::array<std::string_view,2>{"create_rite","create_rite_puppet"}){
    if(name.empty())continue;bool visible=false,enabled=false;
    if(!a.named_button_state(a.gui_context,faith.root,name,visible,enabled))return fail("rite_creation_original_open_button_unverified");
    if(visible&&enabled)++enabled_count;
   }
   bool original_can_open=false;
   if(enabled_count!=1||!CallBool(b,edit?0x14C5B40:0x14C5B90,faith.window,original_can_open)||
      !original_can_open||!Owner(b,a,f))return fail("rite_creation_original_open_button_or_full_source_predicate_false");
   const bool invoked=Open(b,a.handler,r.expected_source_rite_id,out.native_dispatch_attempted);Ack(out,invoked,false);
   Result after{};
   if(ReadRiteCreationController12004(b,a,f,r,after)){
    const bool actual_edit=after.draft.actual_outcome_kind==Outcome::edit_rite;
    out.draft_open_postcondition_observed=actual_edit==edit&&(!r.expected_outcome_kind||after.draft.actual_outcome_kind==r.expected_outcome_kind);
    out.draft=std::move(after.draft);out.modal=std::move(after.modal);out.full_can=std::move(after.full_can);out.quote=std::move(after.quote);
   }
   if(out.native_dispatch_attempted&&!out.draft_open_postcondition_observed){out.available=false;out.unavailable_reason="rite_creation_open_postcondition_unverified_do_not_retry";}
   return invoked;
  }
  Pass state{};std::string why;
  if(!Capture(b,a,f,r,state,why)){out.unavailable_reason=why;return false;}out=state.value;
  if(r.expected_outcome_kind&&r.expected_outcome_kind!=out.draft.actual_outcome_kind)return fail("rite_creation_native_outcome_differs_from_expectation");
  if(r.operation==Operation::prepare_confirmation||r.operation==Operation::confirm_once){
   if(!CompleteCommandPreview(b,a,f,r,state,out)){out.available=false;out.status="unavailable";return false;}
   if(!out.preview_identity||*out.preview_identity!=r.expected_preview_identity)return fail("rite_creation_preview_identity_changed");
   const bool edit=out.draft.actual_outcome_kind==Outcome::edit_rite;
   if(!out.full_can.observed||!(edit?out.full_can.can_edit:out.full_can.can_create).value_or(false))return fail("rite_creation_original_full_can_false_or_unavailable");
   if(r.operation==Operation::prepare_confirmation){
    if(out.modal.stage!=ModalStage::none||!Stable(b,a,f,r,state))return fail("rite_creation_prepare_requires_same_unobstructed_current_draft");
    const bool invoked=CallVoid(b,edit?0x14F49C0:0x14F5130,state.window,out.native_dispatch_attempted);Ack(out,invoked,false);return invoked;
   }
   if(!a.gameplay_commit_opt_in||r.action_id.empty()||out.modal.stage!=ModalStage::confirmation||
      out.modal.kind!=(edit?ModalKind::edit:ModalKind::create)||!out.modal.active.value_or(false)||
      !state.modal_gui_enabled||!out.modal.same_draft_window_bound.value_or(false)||!out.modal.native_can_accept.value_or(false)||!Stable(b,a,f,r,state))
    return fail("rite_creation_confirm_requires_original_active_bound_modal_and_full_can");
   out.action_id=r.action_id;
   if(!ClaimOnce(r))return fail("rite_creation_native_once_claim_exists_or_capacity_reached_do_not_retry");
   out.native_once_claimed=true;
   // Original generic Confirm performs Accept48 AND closes+A8. Never call
   // writer/queue directly and never emulate only the Accept virtual.
   const bool invoked=CallVoid(b,0xC46380,state.modal,out.native_dispatch_attempted);Ack(out,invoked,true);return invoked;
  }
  if(out.modal.stage!=ModalStage::none)return fail("rite_creation_active_modal_blocks_draft_mutation");
  if(r.operation==Operation::set_name_field){
   const auto index=static_cast<std::size_t>(*r.name_field);
   if(out.draft.names[index]==r.text){out.already_in_requested_state=true;out.selection_or_name_postcondition_observed=true;out.status="already_in_requested_state";return true;}
   if(!Stable(b,a,f,r,state))return fail("rite_creation_draft_changed_before_name_callback");
   constexpr std::array<std::uintptr_t,5>rvas{0x14F38F0,0x14F39C0,0x14F3AE0,0x14F3C00,0x14F3D20};
   const BorrowedUtf8 input(r.text);const bool invoked=CallPair(b,rvas[index],state.window,&input,out.native_dispatch_attempted);Ack(out,invoked,false);
   Result after{};if(ReadRiteCreationController12004(b,a,f,r,after))out.selection_or_name_postcondition_observed=after.draft.names[index]==r.text;
   if(out.native_dispatch_attempted&&!out.selection_or_name_postcondition_observed){out.available=false;out.unavailable_reason="rite_creation_name_postcondition_unverified_do_not_retry";}
   return invoked;
  }
  const bool tenet=r.operation==Operation::select_core_tenet;std::uint32_t slot=absent;
  if(tenet)slot=*r.core_slot_index;
  else for(std::size_t i=0;i<out.draft.selected_doctrines.size();++i)if(out.draft.selected_doctrines[i].group_key==r.group_key){if(slot!=absent)return fail("rite_creation_doctrine_group_not_unique");slot=static_cast<std::uint32_t>(i);}
  if(slot==absent||slot>=out.draft.selected_doctrines.size()||(tenet&&slot>=out.draft.selected_core_tenets.size()))return fail("rite_creation_actual_slot_out_of_range");
  if((tenet&&out.draft.selected_core_tenets[slot].tenet_key==r.tenet_key)||(!tenet&&out.draft.selected_doctrines[slot].doctrine_key==r.doctrine_key)){
   out.already_in_requested_state=true;out.selection_or_name_postcondition_observed=true;out.status="already_in_requested_state";return true;}
  if(!Stable(b,a,f,r,state))return fail("rite_creation_draft_changed_before_native_materializer");
  if(!Materialize(b,state.window,slot,out.native_dispatch_attempted)){Ack(out,false,false);return false;}
  reform::DraftChoices choices{};const auto cb=BindCurrentDraftChoices12004(b.image_base,ck3_12004::kExecutableSha256);
  if(!reform::ReadCurrentDraftChoices12002(cb,f.capture_epoch,choices)||!choices.available||!choices.draft_observed||choices.source_rite_id!=r.expected_source_rite_id)
   return fail("rite_creation_materialized_original_gates_unavailable");
  const void*item=nullptr;std::size_t matches=0;Header category{},groups{};
  if(tenet){
   if(!Array(b,state.window,0x7A8,groups))return fail("rite_creation_owned_tenet_groups_unavailable");
   for(const auto&choice:choices.tenets)if(choice.tenet_key==r.tenet_key&&choice.native_can_pick){
    if(choice.popup_group_index>=static_cast<std::uint32_t>(groups.count))return fail("rite_creation_tenet_group_changed");
    Header rows{};if(!Array(b,groups.data,static_cast<std::size_t>(choice.popup_group_index)*0x20+8,rows)||choice.popup_item_index>=static_cast<std::uint32_t>(rows.count))return fail("rite_creation_tenet_rows_changed");
    item=At(rows.data,static_cast<std::size_t>(choice.popup_item_index)*0x70);++matches;}
  }else{
   if(!Array(b,state.window,0x8A8,category))return fail("rite_creation_owned_doctrine_rows_unavailable");
   for(const auto&choice:choices.doctrines)if(choice.group_key==r.group_key&&choice.doctrine_key==r.doctrine_key&&choice.button_enabled){
    if(choice.popup_index>=static_cast<std::uint32_t>(category.count))return fail("rite_creation_doctrine_rows_changed");
    item=At(category.data,static_cast<std::size_t>(choice.popup_index)*0x48);++matches;}
  }
  const void*def=nullptr;std::uint32_t row_slot=absent,faith=absent,rite=absent;std::string key,group;
  if(matches!=1||!Read(b,item,0x20,row_slot)||row_slot!=slot||!Read(b,item,0x28,def)||!Definition(b,def,tenet,key,group)||
     key!=(tenet?r.tenet_key:r.doctrine_key)||(!tenet&&group!=r.group_key)||!Read(b,item,0x30,faith)||
     !Read(b,item,0x34,rite)||rite!=r.expected_source_rite_id||out.draft.source_faith_id!=faith)
   return fail("rite_creation_candidate_not_unique_owned_typed_full_source_row");
  // Re-evaluate the complete original gates after candidate identity checks.
  reform::DraftChoices gates_again{};
  if(!reform::ReadCurrentDraftChoices12002(cb,f.capture_epoch,gates_again)||gates_again.source_rite_id!=choices.source_rite_id||
     !Owner(b,a,f))return fail("rite_creation_original_choice_gates_changed");
  const bool allowed=tenet?std::any_of(gates_again.tenets.begin(),gates_again.tenets.end(),[&](const auto&v){return v.tenet_key==r.tenet_key&&v.native_can_pick;}):
   std::any_of(gates_again.doctrines.begin(),gates_again.doctrines.end(),[&](const auto&v){return v.group_key==r.group_key&&v.doctrine_key==r.doctrine_key&&v.button_enabled;});
  if(!allowed)return fail("rite_creation_original_choice_gate_false");
  const void*last_def=nullptr;std::uint32_t last_slot=absent,last_faith=absent,last_rite=absent;Header last_owned{};
  if(!Read(b,item,0x20,last_slot)||last_slot!=slot||!Read(b,item,0x28,last_def)||last_def!=def||
     !Read(b,item,0x30,last_faith)||last_faith!=faith||!Read(b,item,0x34,last_rite)||last_rite!=rite||
     !Array(b,state.window,tenet?0x7A8:0x8A8,last_owned)||last_owned!=(tenet?groups:category))
   return fail("rite_creation_owned_candidate_changed_before_original_mutator");
  const bool invoked=CallPair(b,tenet?0x14F4580:0x14F46F0,state.window,item,out.native_dispatch_attempted);Ack(out,invoked,false);
  Result after{};if(ReadRiteCreationController12004(b,a,f,r,after))out.selection_or_name_postcondition_observed=tenet?
   slot<after.draft.selected_core_tenets.size()&&after.draft.selected_core_tenets[slot].tenet_key==r.tenet_key:
   slot<after.draft.selected_doctrines.size()&&after.draft.selected_doctrines[slot].group_key==r.group_key&&after.draft.selected_doctrines[slot].doctrine_key==r.doctrine_key;
  if(out.native_dispatch_attempted&&!out.selection_or_name_postcondition_observed){out.available=false;out.unavailable_reason="rite_creation_selection_postcondition_unverified_do_not_retry";}
  return invoked;
 }catch(...){out.verification_pending=out.native_dispatch_attempted;out.status=out.native_dispatch_attempted?"dispatch_result_unknown":"unavailable";
  out.original_writer_may_have_been_queued=r.operation==Operation::confirm_once&&out.native_dispatch_attempted;
  out.unavailable_reason="rite_creation_action_exception_do_not_retry_if_attempted";return false;}
}
} // namespace xar::ck3_12004::religion::rite_creation_actions
