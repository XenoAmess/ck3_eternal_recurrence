#include "xar_bridge/ck3_121003_doctrine_select26785313_v1.hpp"
#include "xar_bridge/ck3_121003_doctrine_select26785313_pins_v1.hpp"
#include <cstring>
#include <limits>
#include <utility>
#include <windows.h>

namespace xar::ck3_121003::build26785313 { namespace {
[[maybe_unused]] bool Copy(std::uintptr_t from,void*to,std::size_t count) noexcept {
 if(!from||!to||!count)return false;
 __try {std::memcpy(to,reinterpret_cast<const void*>(from),count);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
template<class T>bool At(std::uintptr_t p,std::size_t offset,T&out) noexcept {
 constexpr auto max=(std::numeric_limits<std::uintptr_t>::max)();
 return p&&offset<=max-p&&sizeof(T)-1<=max-p-offset&&Copy(p+offset,&out,sizeof(out));
}
[[maybe_unused]] bool ExactTargets(const DoctrineSelectBindings267V1&b) noexcept {
 constexpr auto max=(std::numeric_limits<std::uintptr_t>::max)();
 return b.exact_image_verified&&b.image&&b.image<=max-kImageSize&&
   b.should_display==b.image+kShouldDisplayNativeRva267V1&&
   b.can_pick==b.image+kCanPickNativeRva267V1&&
   b.select_doctrine==b.image+kSelectDoctrineNativeRva267V1&&
   b.has_selected==b.image+kHasDoctrineSelectedNativeRva267V1;
}
[[maybe_unused]] bool ContextShape(std::uintptr_t controller) noexcept {
 constexpr auto max=(std::numeric_limits<std::uintptr_t>::max)();
 return controller&&controller<=max-0xB90;
}
[[maybe_unused]] bool Current(const ReadonlyBindings&core,const DoctrineSelectBindings267V1&b) noexcept {
 if(!core.exact_image_admitted||!core.core.enabled||core.module_base!=b.image||!ExactTargets(b))return false;
#if defined(XAR_CK3_26785313_OFFLINE_FIXTURE)
 if(core.offline_fixture)return false;
#endif
 return VerifyDoctrineSelectImage267V1(b.image);
}
struct Item {
 std::uintptr_t doctrine=0;
 std::array<std::byte,0x48> bytes{};
 DoctrineInternalKey267V1 key;
 friend bool operator==(const Item&,const Item&)=default;
};
[[maybe_unused]] bool ReadItem(const ReadonlyBindings&b,std::uintptr_t item,Item&out) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_DOCTRINE_SELECT_BINDINGS_V1) && XAR_CK3_ENABLE_121003_26785313_DOCTRINE_SELECT_BINDINGS_V1
 if(!item||!Copy(item,out.bytes.data(),out.bytes.size()))return false;
 std::memcpy(&out.doctrine,out.bytes.data()+0x28,sizeof(out.doctrine));
 std::string reason;
 return ReadSDoctrineInternalKey267V1(b,out.doctrine,out.key,reason);
#else
 (void)b;(void)item;(void)out;return false;
#endif
}
[[maybe_unused]] bool Predicates(const DoctrineSelectBindings267V1&b,std::uintptr_t controller,
    std::uintptr_t item,bool&shown,bool&pick) noexcept {
 using Native=bool(__fastcall*)(const void*,const void*);
 const auto *scope=reinterpret_cast<const void*>(controller+0xD0);
 __try {
  shown=reinterpret_cast<Native>(b.should_display)(reinterpret_cast<const void*>(item),scope);
  pick=reinterpret_cast<Native>(b.can_pick)(reinterpret_cast<const void*>(item),scope);
  return true;
 } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]] bool Has(const DoctrineSelectBindings267V1&b,std::uintptr_t controller,
    std::uintptr_t doctrine,bool&value) noexcept {
 using Native=bool(__fastcall*)(const void*,const void*);
 __try {value=reinterpret_cast<Native>(b.has_selected)(reinterpret_cast<const void*>(controller),
    reinterpret_cast<const void*>(doctrine));return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]] RawDoctrineSelectCall267V1 Select(const DoctrineSelectBindings267V1&b,
    std::uintptr_t controller,std::uintptr_t item) noexcept {
 using Native=void(__fastcall*)(void*,const void*);
 RawDoctrineSelectCall267V1 out;
 // All nontrivial C++ objects live outside this SEH boundary.
 out.effect_attempted=true;out.status=RawDoctrineSelectDispatch267V1::indeterminate;
 __try {
  reinterpret_cast<Native>(b.select_doctrine)(reinterpret_cast<void*>(controller),reinterpret_cast<const void*>(item));
  out.status=RawDoctrineSelectDispatch267V1::call_returned;return out;
 } __except(EXCEPTION_EXECUTE_HANDLER){return out;}
}
} // namespace

std::span<const ImagePin> DoctrineSelectImagePins267V1() noexcept {return doctrine_select_pins::kPins;}
bool VerifyDoctrineSelectImage267V1([[maybe_unused]]std::uintptr_t image) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_DOCTRINE_SELECT_BINDINGS_V1) && XAR_CK3_ENABLE_121003_26785313_DOCTRINE_SELECT_BINDINGS_V1
 if(!image||image!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))||
    !VerifyReadonlyImage(image)||!VerifyDoctrineKeyImage267V1(image))return false;
 std::array<unsigned char,256> bytes{};
 for(const auto&pin:doctrine_select_pins::kPins) {
  if(pin.bytes.empty()||pin.bytes.size()>bytes.size()||pin.rva>kImageSize-pin.bytes.size()||
     !Copy(image+pin.rva,bytes.data(),pin.bytes.size())||std::memcmp(bytes.data(),pin.bytes.data(),pin.bytes.size())!=0)return false;
 }
 for(const auto&pin:doctrine_select_pins::kPointers) {
  std::uintptr_t value=0;if(!At(image,pin.slot,value)||value!=image+pin.target)return false;
 }
 return true;
#else
 return false;
#endif
}
DoctrineSelectBindings267V1 BindDoctrineSelectImage267V1([[maybe_unused]]std::uintptr_t image,
    [[maybe_unused]]std::string_view sha) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_DOCTRINE_SELECT_BINDINGS_V1) && XAR_CK3_ENABLE_121003_26785313_DOCTRINE_SELECT_BINDINGS_V1
 const auto core=BindReadonlyImage(image,sha);
 if(!core.exact_image_admitted||!VerifyDoctrineSelectImage267V1(image))return {};
 return {true,image,image+kShouldDisplayNativeRva267V1,image+kCanPickNativeRva267V1,
    image+kSelectDoctrineNativeRva267V1,image+kHasDoctrineSelectedNativeRva267V1};
#else
 return {};
#endif
}
RawDoctrinePredicateObservation267V1 ReadRawDoctrinePredicates267V1(
    [[maybe_unused]]const ReadonlyBindings&core,[[maybe_unused]]const DoctrineSelectBindings267V1&bound,
    [[maybe_unused]]std::uintptr_t controller,[[maybe_unused]]std::uintptr_t item) noexcept {
 RawDoctrinePredicateObservation267V1 out;
#if defined(XAR_CK3_ENABLE_121003_26785313_DOCTRINE_SELECT_BINDINGS_V1) && XAR_CK3_ENABLE_121003_26785313_DOCTRINE_SELECT_BINDINGS_V1
 try {
  if(!ContextShape(controller)||!Current(core,bound))return out;
  Item first,second;bool shown1=false,pick1=false,shown2=false,pick2=false;
  if(!ReadItem(core,item,first)||!Predicates(bound,controller,item,shown1,pick1)||
     !Predicates(bound,controller,item,shown2,pick2)||!ReadItem(core,item,second)||first!=second||
     shown1!=shown2||pick1!=pick2||(pick1&&!shown1)||!Current(core,bound))return out;
  out.status=RawDoctrineObservationStatus267V1::observed;out.should_display=shown1;out.can_pick=pick1;
  out.controller=controller;out.item=item;out.doctrine=first.doctrine;out.exact_item=first.bytes;out.exact_doctrine=std::move(first.key);
 } catch(...) {return {};}
#endif
 return out;
}
RawHasDoctrineSelected267V1 ReadRawHasDoctrineSelected267V1(
    [[maybe_unused]]const ReadonlyBindings&core,[[maybe_unused]]const DoctrineSelectBindings267V1&bound,
    [[maybe_unused]]std::uintptr_t controller,[[maybe_unused]]std::uintptr_t doctrine) noexcept {
 RawHasDoctrineSelected267V1 out;
#if defined(XAR_CK3_ENABLE_121003_26785313_DOCTRINE_SELECT_BINDINGS_V1) && XAR_CK3_ENABLE_121003_26785313_DOCTRINE_SELECT_BINDINGS_V1
 try {
  if(!ContextShape(controller)||!Current(core,bound))return out;
  DoctrineInternalKey267V1 first,second;std::string reason;bool a=false,b=false;
  std::array<std::byte,16> before{},after{};std::uintptr_t data=0;std::int32_t count=0;
  constexpr auto max=(std::numeric_limits<std::uintptr_t>::max)();
  if(!Copy(controller+0xB80,before.data(),before.size()))return out;
  std::memcpy(&data,before.data(),8);std::memcpy(&count,before.data()+12,4);
  if(count<0||static_cast<std::size_t>(count)>kRiteDoctrineItemsObservationMax267V1||
     (!data&&count)||(count&&data>max-static_cast<std::size_t>(count)*8))return out;
  if(!ReadSDoctrineInternalKey267V1(core,doctrine,first,reason)||!Has(bound,controller,doctrine,a)||
     !Has(bound,controller,doctrine,b)||a!=b||!ReadSDoctrineInternalKey267V1(core,doctrine,second,reason)||
     first!=second||!Copy(controller+0xB80,after.data(),after.size())||before!=after||!Current(core,bound))return out;
  out.status=RawDoctrineObservationStatus267V1::observed;out.has_selected=a;out.exact_doctrine=std::move(first);
 } catch(...) {return {};}
#endif
 return out;
}
RawDoctrineSelectCall267V1 CallRawSelectDoctrine267V1(
    [[maybe_unused]]const ReadonlyBindings&core,[[maybe_unused]]const DoctrineSelectBindings267V1&bound,
    [[maybe_unused]]std::uintptr_t controller,[[maybe_unused]]std::uintptr_t item) noexcept {
 RawDoctrineSelectCall267V1 out;
#if defined(XAR_CK3_ENABLE_121003_26785313_DOCTRINE_SELECT_BINDINGS_V1) && XAR_CK3_ENABLE_121003_26785313_DOCTRINE_SELECT_BINDINGS_V1
 try {
  if(!ContextShape(controller)||!Current(core,bound))return out;
  Item first,second;
  if(!ReadItem(core,item,first)||!ReadItem(core,item,second)||first!=second||!Current(core,bound))return out;
  // Raw dispatch only. No booleans can be supplied to pretend predicates or
  // knowledge passed; the formal fixed owner consumes its own one claim here.
  out=Select(bound,controller,item);
  if(out.status==RawDoctrineSelectDispatch267V1::call_returned&&!Current(core,bound))
    out.status=RawDoctrineSelectDispatch267V1::indeterminate;
 } catch(...) {if(out.effect_attempted)out.status=RawDoctrineSelectDispatch267V1::indeterminate;}
#endif
 return out;
}
} // namespace xar::ck3_121003::build26785313
