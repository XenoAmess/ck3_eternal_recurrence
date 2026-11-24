#pragma once
#include "xar_bridge/ck3_121003_living_entry26785313_v1.hpp"
#include "xar_bridge/ck3_121003_living_owner26785313_v1.hpp"
#include "xar_bridge/ck3_121003_living_weapon26785313_private_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
namespace xar::ck3_121003::build26785313 {
struct LivingEntryFrame267V1 {
 LivingInventoryFrame267V1 inventory;
 std::optional<LivingManageFrame267V1>manage;
 std::optional<LivingWeaponFrame267V1>view;
};
class LivingEntryRaw267V1 {
 public:LivingEntrySource267V1 source;LivingInventorySource267V1 inventory;
 bool entered=false,cleanup_known=true;
 private:struct State;std::shared_ptr<const State>state_;
 friend bool ReadLivingEntryRaw267V1(const ReadonlyBindings&,const LivingEntryFrame267V1&,
  const LivingEntryRequest267V1&,std::uint64_t,LivingEntryRaw267V1&,std::string&)noexcept;
 friend bool SameLivingEntryRaw267V1(const LivingEntryRaw267V1&,const LivingEntryRaw267V1&)noexcept;
 friend struct LivingEntryCallAccess267V1;
};
struct LivingEntryCall267V1 {bool entered=false,native_returned=false,cleanup_known=true;};
bool ReadLivingEntryRaw267V1(const ReadonlyBindings&,const LivingEntryFrame267V1&,
 const LivingEntryRequest267V1&,std::uint64_t,LivingEntryRaw267V1&,std::string&)noexcept;
bool SameLivingEntryRaw267V1(const LivingEntryRaw267V1&,const LivingEntryRaw267V1&)noexcept;
LivingEntryCall267V1 CallLivingEntryRaw267V1(const ReadonlyBindings&,const LivingEntryFrame267V1&,
 const LivingEntryRequest267V1&,std::uint64_t,const LivingEntryRaw267V1&)noexcept;
bool VerifyLivingEntryImage267V1(std::uintptr_t)noexcept;
class LivingEntrySession267V1;
struct LivingEntryContext267V1 {
 LivingOwnerInvocation267V1 invocation{0x4C49564932363731ULL,LivingInvocationKind267V1::entry,this};
 ReadonlyBindings bindings;ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;
 ck3_11906::MainThreadQueryTicketV1 ticket;
 LivingEntryRequest267V1 request;LivingEntryResult267V1 result;LivingEntrySession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;
 bool observation_entered=false;
};
class LivingEntrySession267V1 {
 public:LivingEntrySession267V1();~LivingEntrySession267V1();
 LivingEntrySession267V1(const LivingEntrySession267V1&)=delete;
 LivingEntrySession267V1&operator=(const LivingEntrySession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool ExecuteLivingEntryInner267V1(LivingEntryContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
};
LivingEntrySession267V1&RetainedLivingEntrySession267V1();
void ArmLivingEntryDeadline267V1(LivingEntryContext267V1&)noexcept;
bool ExecuteLivingEntryInner267V1(LivingEntryContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ExecuteLivingEntryOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadLivingEntryFrameOnOwner267V1(const ReadonlyBindings&,
 ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,
 const ck3_11906::MainThreadExecutionStampV1&,void*,const LivingEntryRequest267V1&,
 std::uint64_t,LivingEntryFrame267V1&,std::string&)noexcept;
const game::AdapterDescriptor&LivingEntryDescriptor267V1(const game::AdapterDescriptor&)noexcept;
bool LivingEntryStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchLivingEntryRequest267V1(const game::GameAdapter&,std::uint64_t,
 std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
