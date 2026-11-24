#pragma once
#include "xar_bridge/ck3_121003_living_inventory26785313_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <memory>
#include "xar_bridge/ck3_121003_living_owner26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
struct LivingInventoryQueryContext267V1;
class LivingInventoryQuerySession267V1 {
 public:LivingInventoryQuerySession267V1();~LivingInventoryQuerySession267V1();
 LivingInventoryQuerySession267V1(const LivingInventoryQuerySession267V1&)=delete;
 LivingInventoryQuerySession267V1&operator=(const LivingInventoryQuerySession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool ExecuteLivingInventoryQueryInner267V1(LivingInventoryQueryContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
 friend void BlockLivingInventoryQueryUnknown267V1(LivingInventoryQuerySession267V1&)noexcept;
};
struct LivingInventoryQueryContext267V1 {
 LivingOwnerInvocation267V1 invocation{0x4C49564932363731ULL,LivingInvocationKind267V1::inventory_query,this};
 ReadonlyBindings bindings{};
 ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;
 ck3_11906::MainThreadQueryTicketV1 ticket{};
 LivingInventoryQueryRequest267V1 request{};LivingInventoryQueryResult267V1 result{};
 LivingInventoryQuerySession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;
 bool native_observation_entered=false;
};
LivingInventoryQuerySession267V1&RetainedLivingInventoryQuerySession267V1();
void ArmLivingInventoryQueryDeadline267V1(LivingInventoryQueryContext267V1&)noexcept;
void BlockLivingInventoryQueryUnknown267V1(LivingInventoryQuerySession267V1&)noexcept;
bool ExecuteLivingInventoryQueryInner267V1(LivingInventoryQueryContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ExecuteLivingInventoryQueryOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadLivingInventoryQueryFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,const LivingInventoryQueryRequest267V1&,std::uint64_t,LivingInventoryFrame267V1&,std::string&)noexcept;
const game::AdapterDescriptor&LivingInventoryQueryDescriptor267V1(const game::AdapterDescriptor&)noexcept;
bool LivingInventoryQueryStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchLivingInventoryQueryRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
