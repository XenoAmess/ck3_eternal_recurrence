#include "xar_bridge/ck3_121003_rite_edit_confirmation26785313_v1.hpp"
#include "xar_bridge/ck3_121003_rite_edit_confirmation26785313_pins_v1.hpp"
#include <cstring>
#include <limits>
#include <utility>
#include <windows.h>

namespace xar::ck3_121003::build26785313 { namespace {
[[maybe_unused]] bool Copy(std::uintptr_t from,void*to,std::size_t n) noexcept {
 if(!from||!to||!n)return false;
 __try {std::memcpy(to,reinterpret_cast<const void*>(from),n);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
template<class T>bool At(std::uintptr_t p,std::size_t offset,T&out) noexcept {
 constexpr auto max=(std::numeric_limits<std::uintptr_t>::max)();
 return p&&offset<=max-p&&sizeof(T)-1<=max-p-offset&&Copy(p+offset,&out,sizeof(out));
}
[[maybe_unused]] std::uintptr_t Manager(std::uintptr_t image) noexcept {
 using Native=void*(__fastcall*)();
 __try {return reinterpret_cast<std::uintptr_t>(reinterpret_cast<Native>(image+0xCF2C50)());}
 __except(EXCEPTION_EXECUTE_HANDLER){return 0;}
}
[[maybe_unused]] bool Can(std::uintptr_t image,std::uintptr_t modal,bool&value) noexcept {
 using Native=bool(__fastcall*)(const void*);
 __try {value=reinterpret_cast<Native>(image+0x16B61E0)(reinterpret_cast<const void*>(modal));return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]] RawRiteEditConfirmCall267V1 Confirm(std::uintptr_t image,std::uintptr_t modal) noexcept {
 using Native=void(__fastcall*)(void*);RawRiteEditConfirmCall267V1 out;
 out.effect_entered=true;out.status=RawRiteEditConfirmStatus267V1::indeterminate;
 __try {reinterpret_cast<Native>(image+0xCF3200)(reinterpret_cast<void*>(modal));out.status=RawRiteEditConfirmStatus267V1::call_returned;return out;}
 __except(EXCEPTION_EXECUTE_HANDLER){return out;}
}
[[maybe_unused]] bool Capture(const ReadonlyBindings&core,const RiteEditConfirmationBindings267V1&b,
 std::uintptr_t controller,std::uintptr_t context,BoundRiteEditConfirmation267V1&out) {
 constexpr auto max=(std::numeric_limits<std::uintptr_t>::max)();
 if(!b.exact_image_verified||!core.exact_image_admitted||!core.core.enabled||b.image!=core.module_base||
    !controller||controller>max-0x134||!context||!VerifyRiteEditConfirmationImage267V1(b.image))return false;
 std::uintptr_t cvt=0,jomini=0,application=0,first=0,current_context=0;
 if(!At(controller,0,cvt)||cvt!=b.image+0x4C09438||!At(b.image,kJominiStateSlotRva,jomini)||
    !At(jomini,0x18,application)||!At(application,0x1B8,first)||!At(first,0x58,current_context)||
    current_context!=context||!At(controller,0xC8,out.source_rite_id)||out.source_rite_id==0xFFFFFFFFU||
    !At(controller,0xCC,out.actor_id)||out.actor_id==0xFFFFFFFFU)return false;
 out.controller=controller;out.gui_context=context;out.manager=Manager(b.image);
 if(!out.manager||out.manager>max-0x27||!Copy(out.manager+0x18,out.exact_dialog_header.data(),16))return false;
 std::int32_t count=0,capacity=0;std::memcpy(&out.data,out.exact_dialog_header.data(),8);
 std::memcpy(&capacity,out.exact_dialog_header.data()+8,4);std::memcpy(&count,out.exact_dialog_header.data()+12,4);
 if(count<0||count>128||capacity<count||(!out.data&&count)||(count&&out.data>max-static_cast<std::size_t>(count)*8))return false;
 unsigned active=0;
 for(std::int32_t i=0;i<count;++i) {
  std::uintptr_t dialog=0,vt=0,root=0,cx=0,owner=0,s1=0,s2=0;std::uint8_t closed=1;
  if(!At(out.data,static_cast<std::size_t>(i)*8,dialog))return false;
  out.dialog_pointers.push_back(dialog);if(!dialog)continue;
  if(!At(dialog,0,vt)||!At(dialog,0x70,root)||!At(dialog,0x78,cx)||!At(dialog,0xA8,closed)||closed>1)return false;
  if(closed||!root)continue;
  if(++active!=1||vt!=b.image+0x4C09588||!At(dialog,0x10,s1)||s1!=b.image+0x4C09638||
     !At(dialog,0x20,s2)||s2!=b.image+0x4C09610||!At(dialog,0x130,owner)||owner!=controller||cx!=context)return false;
  out.modal=dialog;out.root=root;
 }
 if(!active){out.no_active_dialog=true;return true;}
 return active==1&&Can(b.image,out.modal,out.native_can_accept);
}
} // namespace
std::span<const ImagePin> RiteEditConfirmationImagePins267V1() noexcept {return rite_edit_confirmation_pins::kPins;}
bool VerifyRiteEditConfirmationImage267V1([[maybe_unused]]std::uintptr_t image) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1
 if(!image||image!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))||!VerifyReadonlyImage(image))return false;
 std::array<unsigned char,256> data{};
 for(const auto&p:rite_edit_confirmation_pins::kPins) {
  if(p.bytes.empty()||p.bytes.size()>data.size()||p.rva>kImageSize-p.bytes.size()||
     !Copy(image+p.rva,data.data(),p.bytes.size())||std::memcmp(data.data(),p.bytes.data(),p.bytes.size())!=0)return false;
 }
 for(const auto&p:rite_edit_confirmation_pins::kPointers) {std::uintptr_t value=0;if(!At(image,p.slot,value)||value!=image+p.target)return false;}
 return true;
#else
 return false;
#endif
}
RiteEditConfirmationBindings267V1 BindRiteEditConfirmation267V1([[maybe_unused]]std::uintptr_t image,[[maybe_unused]]std::string_view sha) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1
 const auto core=BindReadonlyImage(image,sha);return core.exact_image_admitted&&VerifyRiteEditConfirmationImage267V1(image)?RiteEditConfirmationBindings267V1{true,image}:RiteEditConfirmationBindings267V1{};
#else
 return {};
#endif
}
bool ReadBoundRiteEditConfirmation267V1([[maybe_unused]]const ReadonlyBindings&core,
 [[maybe_unused]]const RiteEditConfirmationBindings267V1&b,[[maybe_unused]]std::uintptr_t controller,
 [[maybe_unused]]std::uintptr_t context,BoundRiteEditConfirmation267V1&out,std::string&reason) noexcept {
 out={};reason="exact_rite_edit_confirmation_unavailable";
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1
#if defined(XAR_CK3_26785313_OFFLINE_FIXTURE)
 if(core.offline_fixture)return false;
#endif
 try {
  BoundRiteEditConfirmation267V1 a,z;
  if(!Capture(core,b,controller,context,a)||!Capture(core,b,controller,context,z)||a!=z||!VerifyRiteEditConfirmationImage267V1(b.image))return false;
  out=std::move(a);reason="raw_modal_owner_and_named_root_not_granted";return true;
 } catch(...) {out={};return false;}
#else
 return false;
#endif
}
RawRiteEditConfirmCall267V1 CallRawRiteEditConfirm267V1([[maybe_unused]]const ReadonlyBindings&core,
 [[maybe_unused]]const RiteEditConfirmationBindings267V1&b,[[maybe_unused]]std::uintptr_t controller,
 [[maybe_unused]]std::uintptr_t context,[[maybe_unused]]std::uintptr_t modal,[[maybe_unused]]std::uintptr_t root) noexcept {
 RawRiteEditConfirmCall267V1 out;
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1
 try {
  BoundRiteEditConfirmation267V1 actual;std::string reason;
  if(!modal||!root||!ReadBoundRiteEditConfirmation267V1(core,b,controller,context,actual,reason)||
     actual.modal!=modal||actual.root!=root||!actual.native_can_accept)return out;
  out=Confirm(b.image,actual.modal);
  if(out.status==RawRiteEditConfirmStatus267V1::call_returned&&!VerifyRiteEditConfirmationImage267V1(b.image))out.status=RawRiteEditConfirmStatus267V1::indeterminate;
 } catch(...) {if(out.effect_entered)out.status=RawRiteEditConfirmStatus267V1::indeterminate;}
#endif
 return out;
}
} // namespace xar::ck3_121003::build26785313
