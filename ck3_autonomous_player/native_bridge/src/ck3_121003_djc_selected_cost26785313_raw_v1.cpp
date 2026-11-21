#include "xar_bridge/ck3_121003_djc_selected_cost26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_djc_declarations26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_declarations26785313_abi_v1.hpp"
#include <cstring>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
struct NativeCString32 {char data[16];std::uint64_t size,capacity;};
static_assert(sizeof(NativeCString32)==32);
[[maybe_unused]]bool CostCall(std::uintptr_t image,std::uintptr_t view,const NativeCString32&name,std::int64_t&out)noexcept{
 __try{
  auto*returned=reinterpret_cast<declarations_abi_v1::GetSpecificCbCost>(image+declarations_abi_v1::k_get_specific_cb_cost)(&out,reinterpret_cast<void*>(view),&name);
  return returned==&out;
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool Selected(const DjcUiRawObservation267V1&r,std::uint8_t cb)noexcept{
 return cb<kDjcUiCbKeys267V1.size()&&r.cleanup_known&&r.no_active_dialog&&r.view&&r.outer&&r.selected&&
  r.source.resident_available&&r.source.named_root_bound&&r.source.window_visible&&r.source.interaction_definition_verified&&
  r.source.loaded_interface==4&&r.source.native_confirmation.value_or(false)&&r.source.selected&&
  r.selected->definition&&r.selected->tuple.cb_key==kDjcUiCbKeys267V1[cb]&&r.source.selected->cb_key==kDjcUiCbKeys267V1[cb];
}
}
bool ReadDjcSelectedCostRaw267V1([[maybe_unused]]const ReadonlyBindings&core,[[maybe_unused]]const DjcUiRawBindings267V1&b,
 [[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&expected,[[maybe_unused]]std::int32_t target,[[maybe_unused]]std::uint8_t cb,
 [[maybe_unused]]const DjcUiExpectedScene267V1&scene,[[maybe_unused]]std::uint64_t until,
 [[maybe_unused]]const DjcUiRawObservation267V1&prior,DjcSelectedCostValues267V1&out,std::string&reason)noexcept{
 out={};reason="current_djc_selected_cost_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_COST_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_COST_V1
 try{
  if(!b.verified||!Selected(prior,cb)||!BindCurrentDjcDeclarations267V1(b.image,kExecutableSha256).verified){reason="djc_cost_exact_binding_or_selected_source_unavailable";return false;}
  DjcUiRawObservation267V1 first,last;
  if(!ReadDjcUiRawForClaim267V1(core,b,expected,target,cb,scene,until,first,reason)){out.cleanup_known=first.cleanup_known;return false;}
  if(!Selected(first,cb)||!SameDjcUiRaw267V1(prior,first)){reason="djc_cost_original_private_selected_source_changed";return false;}
  std::array<std::int64_t,5>values{};
  for(unsigned pass=0;pass<2;++pass){
   for(std::size_t i=0;i<kDjcSelectedCostCurrencies267V1.size();++i){
    if(!until||GetTickCount64()>=until||!VerifyDjcUiImage267V1(b.image)){reason="djc_cost_original_deadline_or_image_changed";return false;}
    NativeCString32 name{};const auto key=kDjcSelectedCostCurrencies267V1[i];
    std::memcpy(name.data,key.data(),key.size());name.size=key.size();name.capacity=15;
    std::int64_t value=0;++out.native_getter_calls;
    // The official getter resolves this fixed name through the actual registry.
    // No vector index, data-only supplied value or native permission bool exists.
    if(!CostCall(b.image,first.view,name,value)){out.cleanup_known=false;reason="djc_cost_native_getter_or_internal_cleanup_unknown";return false;}
    if(!pass)values[i]=value;else if(values[i]!=value){reason="djc_cost_values_changed_between_native_passes";return false;}
   }
  }
  if(!ReadDjcUiRawForClaim267V1(core,b,expected,target,cb,scene,until,last,reason)){out.cleanup_known=last.cleanup_known;return false;}
  if(!Selected(last,cb)||!SameDjcUiRaw267V1(first,last)||!SameDjcUiRaw267V1(prior,last)){reason="djc_cost_post_getter_resident_or_full_tuple_changed";return false;}
  for(std::size_t i=0;i<values.size();++i)out.raw[i]=values[i];
  out.available=true;reason.clear();return true;
 }catch(...){out.available=false;out.raw={};out.cleanup_known=false;reason="djc_cost_native_observation_exception_unknown";return false;}
#else
 return false;
#endif
}
} // namespace
