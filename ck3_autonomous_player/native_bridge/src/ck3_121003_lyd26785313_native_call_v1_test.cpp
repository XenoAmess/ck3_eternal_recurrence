#include "xar_bridge/ck3_121003_lyd26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_lyd_personal26785313_pins_v1.hpp"
#include <array>
#include <cstring>
#include <stdexcept>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace lyd_common {
bool fresh_test=true;bool Fresh(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const LydScene267V1&,std::uint64_t)noexcept{return fresh_test;}
}
#include "ck3_121003_lyd26785313_personal_native_v1.inc"
}
using namespace xar::ck3_121003::build26785313;
namespace {
std::uintptr_t image=0;std::array<std::byte,64>actor{},fallback{};bool wrong_actor=false,wrong_type=false,copy_bad=false,callback_false=false,toggle_value=false;unsigned toggles=0,destroys=0,copies=0;
void Require(bool v,const char*why){if(!v)throw std::runtime_error(why);}
std::uintptr_t Empty(){return image+0x5D25000;}std::uintptr_t Character(){return image+lyd_personal_pins::kCharacterAnyInstanceRva;}std::uintptr_t TextType(){return image+lyd_personal_pins::kStringAnyInstanceRva;}
void Destroy(void*,void*){++destroys;}
void*Assign(void*out,const char*bytes,std::size_t length){Require(std::string_view(bytes,length)=="personal_beliefs_window","wrong literal view key");const auto ptr=reinterpret_cast<std::uintptr_t>(bytes);const auto n=static_cast<std::uint64_t>(length);std::memcpy(out,&ptr,8);std::memcpy(static_cast<std::byte*>(out)+16,&n,8);std::memcpy(static_cast<std::byte*>(out)+24,&n,8);return out;}
void TextDestroy(void*){++destroys;}
void Copy(lyd_personal_native::Any*out,const void*storage,void*type){++copies;Require(reinterpret_cast<std::uintptr_t>(type)==TextType(),"8B4960 wrong R8 type");std::uint64_t length=0;std::memcpy(&length,static_cast<const std::byte*>(storage)+16,8);Require(length==std::string_view("personal_beliefs_window").size(),"8B4960 source is not CString STORAGE");out->type=copy_bad?Empty():TextType();std::memcpy(out->storage.data(),storage,32);}
bool Player(void*,lyd_personal_native::Any*out){out->type=wrong_type?TextType():Character();const auto ptr=reinterpret_cast<std::uintptr_t>(wrong_actor?fallback.data():actor.data());std::memcpy(out->storage.data(),&ptr,8);return !callback_false;}
bool Toggle(void*,void*,const lyd_personal_native::ArgCursor*cursor){++toggles;Require(cursor&&cursor->index==0&&cursor->table&&cursor->table->data,"actual cursor ABI");const auto*args=cursor->table->data;Require(args[0].type==TextType()&&args[1].type==Character(),"actual two Any40 argument types");std::uintptr_t value=0;std::memcpy(&value,args[1].storage.data(),8);Require(value==reinterpret_cast<std::uintptr_t>(actor.data()),"fallback payload reached navigation");return toggle_value;}
void Write(std::uintptr_t at,const void*data,std::size_t n){const auto page=at&~std::uintptr_t{4095};Require(VirtualAlloc(reinterpret_cast<void*>(page),((at-page+n+4095)/4096)*4096,MEM_COMMIT,PAGE_READWRITE)!=nullptr,"own fake image commit");std::memcpy(reinterpret_cast<void*>(at),data,n);}
template<class F>void Code(std::uintptr_t rva,F function){std::array<unsigned char,12>bytes{0x48,0xB8};const auto fn=reinterpret_cast<std::uintptr_t>(function);std::memcpy(bytes.data()+2,&fn,8);bytes[10]=0xFF;bytes[11]=0xE0;Write(image+rva,bytes.data(),bytes.size());DWORD old=0;Require(VirtualProtect(reinterpret_cast<void*>(image+rva),bytes.size(),PAGE_EXECUTE_READ,&old)!=0,"own fake code protect");Require(FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(image+rva),bytes.size())!=0,"own instruction cache");}
void Type(std::uintptr_t singleton,std::uintptr_t vt){const auto v=image+vt;Write(image+singleton,&v,8);const auto destroy=reinterpret_cast<std::uintptr_t>(&Destroy);Write(v+0x18,&destroy,8);}
}
int main(){try{image=reinterpret_cast<std::uintptr_t>(VirtualAlloc(nullptr,kImageSize,MEM_RESERVE,PAGE_NOACCESS));Require(image!=0,"own fake image reserve");Type(0x5D25000,0x4AF0000);Type(lyd_personal_pins::kCharacterAnyInstanceRva,lyd_personal_pins::kCharacterAnyVtableRva);Type(lyd_personal_pins::kStringAnyInstanceRva,lyd_personal_pins::kStringAnyVtableRva);Code(0x8B2EF0,&Empty);Code(0xA3F530,&Character);Code(0x8C21D0,&TextType);Code(0x896BB0,&Assign);Code(0x897460,&TextDestroy);Code(0x8B4960,&Copy);Code(0x2B48940,&Player);Code(0xBC1460,&Toggle);
 const std::int32_t id=-16777215;const std::uint32_t magic=0x43686172;std::memcpy(actor.data()+0x18,&id,4);std::memcpy(actor.data()+0x1C,&magic,4);const std::int32_t invalid=-1;std::memcpy(fallback.data()+0x18,&invalid,4);std::memcpy(fallback.data()+0x1C,&magic,4);ReadonlyBindings b;b.module_base=image;xar::ck3_1210::CoreSnapshotPrefix core;core.played_character_id=id;LydScene267V1 scene;
 auto invoke=[&]{return lyd_personal_native::Open(b,core,scene,1,actor.data());};auto result=invoke();Require(result.status==LydRawCallStatus267V1::returned&&result.effect_entered&&result.cleanup_known&&!result.native_handled&&toggles==1&&copies==1&&destroys==3,"actual typed navigation false-bool dispatch/cleanup");toggle_value=true;result=invoke();Require(result.native_handled&&toggles==2,"actual handled bool lost");
 wrong_actor=true;result=invoke();Require(result.status==LydRawCallStatus267V1::refused&&!result.effect_entered&&result.cleanup_known&&toggles==2,"true-returning fallback accepted");wrong_actor=false;wrong_type=true;result=invoke();Require(!result.effect_entered&&result.cleanup_known&&toggles==2,"wrong Character Any accepted");wrong_type=false;callback_false=true;result=invoke();Require(!result.effect_entered&&result.cleanup_known&&toggles==2,"false producer accepted");callback_false=false;lyd_common::fresh_test=false;result=invoke();Require(!result.effect_entered&&toggles==2,"expired/mismatched owner entered");lyd_common::fresh_test=true;copy_bad=true;result=invoke();Require(!result.effect_entered&&!result.cleanup_known&&result.status==LydRawCallStatus267V1::indeterminate,"uncertain Any copy cleanup normalized");Require(VirtualFree(reinterpret_cast<void*>(image),0,MEM_RELEASE)!=0,"own fake image release");return 0;
 }catch(...){if(image)VirtualFree(reinterpret_cast<void*>(image),0,MEM_RELEASE);return 1;}}
