#include "xar_bridge/ck3_121003_doctrine_category26785313_v1.hpp"
#include "xar_bridge/ck3_121003_doctrine_category26785313_pins_v1.hpp"
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
[[maybe_unused]] bool GroupKey(std::uintptr_t image,std::uintptr_t group,DoctrineInternalKey267V1&out) {
 std::uintptr_t vptr=0,vbptr=0;std::uint32_t marker=0,index=0,hash=0;
 std::array<unsigned char,32> before{},after{};
 if(!At(group,0,vptr)||vptr!=image+0x4FC7050||!At(group,8,vbptr)||vbptr!=image+category_pins::kGroupVbtable||
    !At(group,0x38,marker)||marker!=0x4744624FU||!At(group,0x10,index)||index==0xFFFFFFFFU||
    !At(group,0x14,hash)||!Copy(group+0x18,before.data(),before.size()))return false;
 std::uint64_t size=0,capacity=0;std::memcpy(&size,before.data()+16,8);std::memcpy(&capacity,before.data()+24,8);
 if(!size||size>kDoctrineKeyObservationMaxBytes267V1||size>capacity||(capacity!=15&&capacity<=15))return false;
 std::uintptr_t data=group+0x18;
 if(capacity>15)std::memcpy(&data,before.data(),8);
 constexpr auto max=(std::numeric_limits<std::uintptr_t>::max)();
 if(!data||size>max-data)return false;
 std::string first(static_cast<std::size_t>(size)+1,'\0'),second(first.size(),'\0');
 if(!Copy(data,first.data(),first.size())||first.back()!=0||first.find('\0')!=size||
    !Copy(data,second.data(),second.size())||first!=second||!Copy(group+0x18,after.data(),after.size())||before!=after)return false;
 std::uintptr_t vptr2=0;std::uint32_t marker2=0,index2=0,hash2=0;
 if(!At(group,0,vptr2)||vptr2!=vptr||!At(group,0x38,marker2)||marker2!=marker||
    !At(group,0x10,index2)||index2!=index||!At(group,0x14,hash2)||hash2!=hash)return false;
 first.pop_back();out={index,hash,std::move(first)};return true;
}
[[maybe_unused]] bool Lookup(const DoctrineCategoryBindings267V1&bound,std::uintptr_t controller,
    std::uintptr_t&helper,std::uintptr_t&header) noexcept {
 CategoryLookupString267V1 name;constexpr char value[]="main_group";
 std::memcpy(name.data.data(),value,sizeof(value));name.size=sizeof(value)-1;
 __try {
  helper=reinterpret_cast<std::uintptr_t>(bound.get_helper(reinterpret_cast<void*>(controller),&name));
  if(!helper)return false;
  header=reinterpret_cast<std::uintptr_t>(bound.get_category_array(reinterpret_cast<void*>(controller+0x7F8),reinterpret_cast<const void*>(helper)));
  return header!=0;
 } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]] bool Capture(const ReadonlyBindings&b,const DoctrineCategoryBindings267V1&bound,
    std::uintptr_t controller,DynasticCategoryTarget267V1&out) {
 constexpr auto max=(std::numeric_limits<std::uintptr_t>::max)();
 if(!controller||controller>max-0x8E8)return false;
 out.controller=controller;
 if(!Lookup(bound,controller,out.helper,out.array_header))return false;
 std::uintptr_t parent=0;std::int32_t count=0,draft_count=0;
 if(!At(out.helper,0x20,parent)||parent!=controller||
    !Copy(out.array_header,out.exact_pointer_array_header.data(),16)||
    !At(out.array_header,0,out.data)||!At(out.array_header,12,count)||count<0||
    static_cast<std::size_t>(count)>kRiteDoctrineItemsObservationMax267V1||(!out.data&&count)||
    !Copy(controller+0x798,out.exact_draft_array_header.data(),16)||
    !At(controller,0x798,out.draft_data)||!At(controller,0x7A4,draft_count)||draft_count<0||
    static_cast<std::size_t>(draft_count)>kRiteDoctrineItemsObservationMax267V1||(!out.draft_data&&draft_count))return false;
 if((count&&out.data>max-static_cast<std::size_t>(count)*8)||
    (draft_count&&out.draft_data>max-static_cast<std::size_t>(draft_count)*0x48))return false;
 unsigned matches=0;
 for(std::int32_t i=0;i<count;++i) {
  std::uintptr_t item=0,doctrine=0,group=0;std::int32_t slot=-1;std::array<std::byte,0x48> exact{};
  if(!At(out.data,static_cast<std::size_t>(i)*8,item)||!item||!Copy(item,exact.data(),exact.size())||
     !At(item,0x20,slot)||!At(item,0x28,doctrine))return false;
  out.category_item_pointers.push_back(item);
  DoctrineInternalKey267V1 doctrine_key,group_key;std::string reason;
  if(!ReadSDoctrineInternalKey267V1(b,doctrine,doctrine_key,reason)||!At(doctrine,0xA20,group)||
     !GroupKey(b.module_base,group,group_key))return false;
  if(group_key.exact_bytes!=kDynasticMembershipGroupKey267V1)continue;
  // This is the native slot read from the key-qualified typed item, not its
  // ordinal in the UI/pointer array. Match the exact current selected draft.
  if(slot<0||slot>=draft_count)return false;
  const auto selected=out.draft_data+static_cast<std::size_t>(slot)*0x48;
  std::array<std::byte,0x48> selected_bytes{};
  if(!Copy(selected,selected_bytes.data(),selected_bytes.size())||selected_bytes!=exact)return false;
  if(++matches!=1)return false;
  out.item=item;out.doctrine=doctrine;out.group=group;out.slot=slot;out.exact_item=exact;
  out.doctrine_key=std::move(doctrine_key);out.group_key=std::move(group_key);
 }
 return matches==1;
}
// The selected-draft value array is an independent source from GetCategory's
// pointer array. Retain all actual object bytes and both keys in each sample.
struct DraftItemProof {
 std::uintptr_t item=0,doctrine=0,group=0;
 std::array<std::byte,0x48> exact{};
 std::int32_t slot=-1;
 DoctrineInternalKey267V1 doctrine_key,group_key;
 friend bool operator==(const DraftItemProof&,const DraftItemProof&)=default;
};
struct DraftSample {
 DynasticCategoryTarget267V1 target;
 std::vector<DraftItemProof> all;
 friend bool operator==(const DraftSample&,const DraftSample&)=default;
};
[[maybe_unused]] bool CaptureDraft(const ReadonlyBindings&b,std::uintptr_t controller,DraftSample&out) {
 constexpr auto max=(std::numeric_limits<std::uintptr_t>::max)();
 if(!controller||controller>max-0x7A8)return false;
 auto&target=out.target;target.controller=controller;
 if(!Copy(controller+0x798,target.exact_draft_array_header.data(),16))return false;
 std::int32_t count=0;
 std::memcpy(&target.draft_data,target.exact_draft_array_header.data(),8);
 std::memcpy(&count,target.exact_draft_array_header.data()+12,4);
 if(count<0||static_cast<std::size_t>(count)>kRiteDoctrineItemsObservationMax267V1||
    (!target.draft_data&&count)||(count&&target.draft_data>max-static_cast<std::size_t>(count)*0x48))return false;
 unsigned matches=0;
 for(std::int32_t i=0;i<count;++i) {
  DraftItemProof value;value.item=target.draft_data+static_cast<std::size_t>(i)*0x48;
  if(!Copy(value.item,value.exact.data(),value.exact.size()))return false;
  std::memcpy(&value.slot,value.exact.data()+0x20,4);
  std::memcpy(&value.doctrine,value.exact.data()+0x28,8);
  std::string reason;
  if(!ReadSDoctrineInternalKey267V1(b,value.doctrine,value.doctrine_key,reason)||
     !At(value.doctrine,0xA20,value.group)||!GroupKey(b.module_base,value.group,value.group_key))return false;
  if(value.group_key.exact_bytes==kDynasticMembershipGroupKey267V1) {
   // The loop index never becomes a selector. Use the key-qualified item's
   // own typed slot, then independently prove its same native draft object.
   if(value.slot<0||value.slot>=count)return false;
   const auto selected=target.draft_data+static_cast<std::size_t>(value.slot)*0x48;
   if(selected!=value.item)return false;
   std::array<std::byte,0x48> selected_bytes{};
   if(!Copy(selected,selected_bytes.data(),selected_bytes.size())||selected_bytes!=value.exact||++matches!=1)return false;
   target.item=value.item;target.doctrine=value.doctrine;target.group=value.group;target.slot=value.slot;
   target.exact_item=value.exact;target.doctrine_key=value.doctrine_key;target.group_key=value.group_key;
  }
  out.all.push_back(std::move(value));
 }
 return matches==1;
}
} // namespace
std::span<const ImagePin> DoctrineCategoryImagePins267V1() noexcept {return category_pins::kPins;}
bool VerifyDoctrineCategoryImage267V1([[maybe_unused]]std::uintptr_t image) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_DOCTRINE_CATEGORY_OPEN_V1) && XAR_CK3_ENABLE_121003_26785313_DOCTRINE_CATEGORY_OPEN_V1
 if(!image||image!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))||
    !VerifyReadonlyImage(image)||!VerifyDoctrineKeyImage267V1(image))return false;
 std::array<unsigned char,256> bytes{};
 for(const auto&p:category_pins::kPins) {
  if(p.bytes.empty()||p.bytes.size()>bytes.size()||p.rva>kImageSize-p.bytes.size()||
     !Copy(image+p.rva,bytes.data(),p.bytes.size())||std::memcmp(bytes.data(),p.bytes.data(),p.bytes.size())!=0)return false;
 }
 for(const auto&p:category_pins::kPointers) {std::uintptr_t value=0;if(!At(image,p.slot,value)||value!=image+p.target)return false;}
 return true;
#else
 return false;
#endif
}
DoctrineCategoryBindings267V1 BindDoctrineCategoryImage267V1(std::uintptr_t image,std::string_view sha) noexcept {
 const auto core=BindReadonlyImage(image,sha);
 if(!core.exact_image_admitted||!VerifyDoctrineCategoryImage267V1(image))return {};
 return {true,image,reinterpret_cast<DoctrineCategoryBindings267V1::Helper>(image+0x16B90F0),
   reinterpret_cast<DoctrineCategoryBindings267V1::Array>(image+0x16C1050),
   reinterpret_cast<DoctrineCategoryBindings267V1::Show>(image+0x16B66B0)};
}
bool ReadRawDynasticCategoryTarget267V1([[maybe_unused]]const ReadonlyBindings&b,
    [[maybe_unused]]std::uintptr_t controller,DynasticCategoryTarget267V1&out,std::string&reason) noexcept {
 out={};reason="category_source_unavailable";
#if defined(XAR_CK3_ENABLE_121003_26785313_DOCTRINE_CATEGORY_OPEN_V1) && XAR_CK3_ENABLE_121003_26785313_DOCTRINE_CATEGORY_OPEN_V1
#if defined(XAR_CK3_26785313_OFFLINE_FIXTURE)
 if(b.offline_fixture)return false;
#endif
 try {
  const auto bound=BindDoctrineCategoryImage267V1(b.module_base,kExecutableSha256);
  if(!b.exact_image_admitted||!b.core.enabled||!bound.verified)return false;
  DynasticCategoryTarget267V1 first,second;
  if(!Capture(b,bound,controller,first)||!Capture(b,bound,controller,second)||first!=second||
     !VerifyDoctrineCategoryImage267V1(b.module_base))return false;
  out=std::move(first);reason="source_only_owner_not_granted";return true;
 } catch(...) {out={};return false;}
#else
 return false;
#endif
}
bool ReadRawDynasticDraftTarget267V1([[maybe_unused]]const ReadonlyBindings&b,
    [[maybe_unused]]std::uintptr_t controller,DynasticCategoryTarget267V1&out,std::string&reason) noexcept {
 out={};reason="draft_category_source_unavailable";
#if defined(XAR_CK3_ENABLE_121003_26785313_DOCTRINE_CATEGORY_OPEN_V1) && XAR_CK3_ENABLE_121003_26785313_DOCTRINE_CATEGORY_OPEN_V1
#if defined(XAR_CK3_26785313_OFFLINE_FIXTURE)
 if(b.offline_fixture)return false;
#endif
 try {
  if(!b.exact_image_admitted||!b.core.enabled||!VerifyDoctrineCategoryImage267V1(b.module_base))return false;
  DraftSample first,second;
  if(!CaptureDraft(b,controller,first)||!CaptureDraft(b,controller,second)||first!=second||
     !VerifyDoctrineCategoryImage267V1(b.module_base))return false;
  out=std::move(first.target);reason="draft_source_only_owner_not_granted";return true;
 } catch(...) {out={};return false;}
#else
 return false;
#endif
}
} // namespace xar::ck3_121003::build26785313
