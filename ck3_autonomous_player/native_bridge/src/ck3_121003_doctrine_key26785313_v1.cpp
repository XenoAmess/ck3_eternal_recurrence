#include "xar_bridge/ck3_121003_doctrine_key26785313_v1.hpp"
#include "xar_bridge/ck3_121003_doctrine_key26785313_pins_v1.hpp"
#include <array>
#include <cstring>
#include <limits>
#include <utility>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
[[maybe_unused]]bool DoctrineKeyCopy267V1(std::uintptr_t address,void *out,std::size_t bytes) noexcept {
 SIZE_T got=0;
 return address&&bytes&&bytes<=(std::numeric_limits<std::uintptr_t>::max)()-address&&
  ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void*>(address),out,bytes,&got)&&got==bytes;
}
template<class T>[[maybe_unused]]T DoctrineKeyField267V1(const std::array<std::byte,0x3C>&data,std::size_t offset) noexcept {
 T value{};std::memcpy(&value,data.data()+offset,sizeof(value));return value;
}
struct DoctrineKeySample267V1 {
 std::array<std::byte,0x3C> header{};
 DoctrineInternalKey267V1 value;
};
[[maybe_unused]]bool DoctrineKeyTake267V1(std::uintptr_t image,std::uintptr_t object,
 DoctrineKeySample267V1 &out) {
 out={};
 if(!DoctrineKeyCopy267V1(object,out.header.data(),out.header.size())||
  DoctrineKeyField267V1<std::uintptr_t>(out.header,0)!=image+0x5012530||
  DoctrineKeyField267V1<std::uintptr_t>(out.header,8)!=image+0x4FC61A0||
  DoctrineKeyField267V1<std::uint32_t>(out.header,0x38)!=0x4744624FU)return false;
 out.value.database_index=DoctrineKeyField267V1<std::uint32_t>(out.header,0x10);
 out.value.stored_identifier_hash=DoctrineKeyField267V1<std::uint32_t>(out.header,0x14);
 const auto length=DoctrineKeyField267V1<std::uint64_t>(out.header,0x28);
 const auto capacity=DoctrineKeyField267V1<std::uint64_t>(out.header,0x30);
 if(out.value.database_index==0xFFFFFFFFU||!length||length>kDoctrineKeyObservationMaxBytes267V1||
  length>capacity||capacity<15)return false;
 std::uintptr_t data=0;
 if(capacity==15) {
  if(object>(std::numeric_limits<std::uintptr_t>::max)()-0x18)return false;
  data=object+0x18;
 }else data=DoctrineKeyField267V1<std::uintptr_t>(out.header,0x18);
 std::array<char,kDoctrineKeyObservationMaxBytes267V1+1> bytes{};
 if(!DoctrineKeyCopy267V1(data,bytes.data(),static_cast<std::size_t>(length)+1)||
  bytes[static_cast<std::size_t>(length)]!=0||std::memchr(bytes.data(),0,static_cast<std::size_t>(length)))return false;
 out.value.exact_bytes.assign(bytes.data(),static_cast<std::size_t>(length));
 return true;
}
}
std::span<const ImagePin> DoctrineKeyImagePins267V1() noexcept {return doctrine_key_pins267_v1::kPins;}
bool VerifyDoctrineKeyImage267V1([[maybe_unused]]std::uintptr_t image) noexcept {
#if !defined(XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2) || !XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2
 return false;
#else
 if(!VerifyReadonlyImage(image))return false;
 std::array<unsigned char,64> bytes{};
 for(const auto&pin:doctrine_key_pins267_v1::kPins) {
  if(pin.bytes.empty()||pin.bytes.size()>bytes.size()||pin.rva>kImageSize-pin.bytes.size()||
   !DoctrineKeyCopy267V1(image+pin.rva,bytes.data(),pin.bytes.size())||std::memcmp(bytes.data(),pin.bytes.data(),pin.bytes.size()))return false;
 }
 for(const auto&pin:doctrine_key_pins267_v1::kPointers) {
  std::uintptr_t got=0;
  if(pin.slot>kImageSize-sizeof(got)||pin.target>=kImageSize||
   !DoctrineKeyCopy267V1(image+pin.slot,&got,sizeof(got))||got!=image+pin.target)return false;
 }
 return true;
#endif
}
bool ReadSDoctrineInternalKey267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]std::uintptr_t object,
 DoctrineInternalKey267V1&out,std::string&reason) noexcept {
 out={};
#if !defined(XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2) || !XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2
 reason="current_doctrine_key_opt_in_disabled";return false;
#else
 try {
  DoctrineKeySample267V1 a{},c{};
  if(!b.exact_image_admitted||!b.core.enabled||!VerifyDoctrineKeyImage267V1(b.module_base)||
   !DoctrineKeyTake267V1(b.module_base,object,a)||!DoctrineKeyTake267V1(b.module_base,object,c)||
   a.header!=c.header||a.value!=c.value||!VerifyDoctrineKeyImage267V1(b.module_base)) {
   reason="current_doctrine_identifier_source_unavailable";return false;
  }
  out=std::move(c.value);reason.clear();return true;
 }catch(...){out={};reason="current_doctrine_identifier_read_exception";return false;}
#endif
}

namespace {
[[maybe_unused]]bool RiteDoctrineItemsTake267V1(const ReadonlyBindings&b,std::uintptr_t controller,
 RiteDoctrineItems267V1 &out) {
 out={};out.controller=controller;
 std::uintptr_t vtable=0,secondary=0;
 if(!DoctrineKeyCopy267V1(controller,&vtable,8)||vtable!=b.module_base+0x4C09438||
  controller>(std::numeric_limits<std::uintptr_t>::max)()-0x8C0||
  !DoctrineKeyCopy267V1(controller+0x10,&secondary,8)||secondary!=b.module_base+0x4C09410||
  !DoctrineKeyCopy267V1(controller+0x8B0,out.exact_array_header.data(),out.exact_array_header.size()))return false;
 std::int32_t count=0;
 std::memcpy(&out.data,out.exact_array_header.data(),8);std::memcpy(&count,out.exact_array_header.data()+12,4);
 if(count<0||count>static_cast<std::int32_t>(kRiteDoctrineItemsObservationMax267V1))return false;
 const auto bytes=static_cast<std::size_t>(count)*0x48;
 if(count&&(!out.data||bytes>(std::numeric_limits<std::uintptr_t>::max)()-out.data))return false;
 out.values.reserve(static_cast<std::size_t>(count));
 for(std::int32_t index=0;index<count;++index) {
  RiteDoctrineItemKey267V1 item;item.item=out.data+static_cast<std::size_t>(index)*0x48;
  if(!DoctrineKeyCopy267V1(item.item,item.exact_item_bytes.data(),item.exact_item_bytes.size()))return false;
  std::memcpy(&item.doctrine,item.exact_item_bytes.data()+0x28,8);std::string reason;
  if(!ReadSDoctrineInternalKey267V1(b,item.doctrine,item.key,reason))return false;
  out.values.push_back(std::move(item));
 }
 return true;
}
}
std::span<const ImagePin> RiteDoctrineItemsImagePins267V1() noexcept {return rite_doctrine_items_pins267_v1::kPins;}
bool VerifyRiteDoctrineItemsImage267V1([[maybe_unused]]std::uintptr_t image) noexcept {
#if !defined(XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2) || !XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2
 return false;
#else
 if(!VerifyRiteDraftImageV2(image)||!VerifyDoctrineKeyImage267V1(image))return false;
 std::array<unsigned char,64> bytes{};
 for(const auto&pin:rite_doctrine_items_pins267_v1::kPins) {
  if(pin.bytes.empty()||pin.bytes.size()>bytes.size()||pin.rva>kImageSize-pin.bytes.size()||
   !DoctrineKeyCopy267V1(image+pin.rva,bytes.data(),pin.bytes.size())||std::memcmp(bytes.data(),pin.bytes.data(),pin.bytes.size()))return false;
 }
 for(const auto&pin:rite_doctrine_items_pins267_v1::kPointers) {
  std::uintptr_t value=0;if(pin.slot>kImageSize-8||pin.target>=kImageSize||
   !DoctrineKeyCopy267V1(image+pin.slot,&value,8)||value!=image+pin.target)return false;
 }
 return true;
#endif
}
bool ReadRiteDoctrineItems267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]std::uintptr_t controller,
 RiteDoctrineItems267V1&out,std::string&reason) noexcept {
 out={};
#if !defined(XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2) || !XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2
 reason="current_rite_doctrine_items_opt_in_disabled";return false;
#else
 try {
  RiteDoctrineItems267V1 a,c;
  if(!b.exact_image_admitted||!b.core.enabled||!VerifyRiteDoctrineItemsImage267V1(b.module_base)||
   !RiteDoctrineItemsTake267V1(b,controller,a)||!RiteDoctrineItemsTake267V1(b,controller,c)||a!=c||
   !VerifyRiteDoctrineItemsImage267V1(b.module_base)) {
   reason="current_rite_doctrine_items_source_unavailable";return false;
  }
  out=std::move(c);reason.clear();return true;
 }catch(...){out={};reason="current_rite_doctrine_items_read_exception";return false;}
#endif
}
const RiteDoctrineItemKey267V1 *FindUniqueRiteDoctrineKey267V1(const RiteDoctrineItems267V1 &items,
 std::string_view key) noexcept {
 const RiteDoctrineItemKey267V1 *found=nullptr;
 for(const auto&item:items.values)if(item.key.exact_bytes==key){if(found)return nullptr;found=&item;}
 return found;
}
}
