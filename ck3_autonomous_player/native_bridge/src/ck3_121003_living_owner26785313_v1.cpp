#include "xar_bridge/ck3_121003_living_owner26785313_v1.hpp"
#include "xar_bridge/ck3_121003_living_inventory26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_living_ui26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_living_entry26785313_owner_v1.hpp"
#include <atomic>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {
namespace {std::atomic_bool family_unknown{false};}
bool LivingFamilyUnknown267V1()noexcept{return family_unknown.load(std::memory_order_acquire);}
void BlockLivingFamilyUnknown267V1()noexcept{family_unknown.store(true,std::memory_order_release);}
std::uint64_t LivingOwnerConnection267V1(const LivingOwnerInvocation267V1*i)noexcept {
 if(!i)return 0;
 __try {
  if(i->magic!=0x4C49564932363731ULL||!i->context)return 0;
  if(i->kind==LivingInvocationKind267V1::inventory_query){
   const auto&q=*static_cast<const LivingInventoryQueryContext267V1*>(i->context);
   return &q.invocation==i&&q.invocation.context==&q?q.connection_generation:0;
  }
  if(i->kind==LivingInvocationKind267V1::ui){
   const auto&q=*static_cast<const LivingUiContext267V1*>(i->context);
   return &q.invocation==i&&q.invocation.context==&q?q.connection_generation:0;
  }
  if(i->kind==LivingInvocationKind267V1::entry){
   const auto&q=*static_cast<const LivingEntryContext267V1*>(i->context);
   return &q.invocation==i&&q.invocation.context==&q?q.connection_generation:0;
  }
  return 0;
 }__except(EXCEPTION_EXECUTE_HANDLER){return 0;}
}
bool ExecuteLivingOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept {
 if(!p)return false;
 __try {
  const auto&i=*static_cast<const LivingOwnerInvocation267V1*>(p);
  if(i.magic!=0x4C49564932363731ULL||!i.context)return false;
  if(i.kind==LivingInvocationKind267V1::inventory_query){
   auto&q=*static_cast<LivingInventoryQueryContext267V1*>(i.context);
   return &q.invocation==p&&q.invocation.context==&q&&ExecuteLivingInventoryQueryOnOwner267V1(&q,s);
  }
  if(i.kind==LivingInvocationKind267V1::ui){
   auto&q=*static_cast<LivingUiContext267V1*>(i.context);
   return &q.invocation==p&&q.invocation.context==&q&&ExecuteLivingUiOnOwner267V1(&q,s);
  }
  if(i.kind==LivingInvocationKind267V1::entry){
   auto&q=*static_cast<LivingEntryContext267V1*>(i.context);
   return &q.invocation==p&&q.invocation.context==&q&&ExecuteLivingEntryOnOwner267V1(&q,s);
  }
  return false;
 }__except(EXCEPTION_EXECUTE_HANDLER){BlockLivingFamilyUnknown267V1();return false;}
}
}
