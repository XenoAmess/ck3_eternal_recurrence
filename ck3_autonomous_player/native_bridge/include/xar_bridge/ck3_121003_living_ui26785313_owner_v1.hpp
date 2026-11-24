#pragma once
#include "xar_bridge/ck3_121003_living_ui26785313_v1.hpp"
#include "xar_bridge/ck3_121003_living_owner26785313_v1.hpp"
#include "xar_bridge/ck3_121003_living_weapon26785313_private_v1.hpp"
#include "xar_bridge/ck3_121003_living_detail26785313_private_v1.hpp"
#include "xar_bridge/ck3_121003_lyd26785313_owner_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
namespace xar::ck3_121003::build26785313 {
struct LivingUiFrame267V1 {
 LivingInventoryFrame267V1 inventory;
 std::optional<LivingWeaponFrame267V1>weapon;
 std::optional<LydFrame267V1>events;
 std::optional<LivingDetailFrame267V1>detail;
};
namespace living_inventory_private {struct LivingFiniteCase267V1;}
class LivingUiRaw267V1 {
 public:LivingUiSource267V1 source;LivingInventorySource267V1 inventory;
 bool entered=false,cleanup_known=true;
 private:struct State;std::shared_ptr<const State>state_;
 friend bool ReadLivingUiRaw267V1(const ReadonlyBindings&,const LivingUiFrame267V1&,
  const LivingUiRequest267V1&,std::uint64_t,living_inventory_private::LivingFiniteCase267V1&,
  LivingUiRaw267V1&,std::string&)noexcept;
 friend bool SameLivingUiRaw267V1(const LivingUiRaw267V1&,const LivingUiRaw267V1&)noexcept;
 friend struct LivingUiCallAccess267V1;
};
struct LivingUiCall267V1 {bool entered=false,native_returned=false,cleanup_known=true;};
bool ReadLivingUiRaw267V1(const ReadonlyBindings&,const LivingUiFrame267V1&,
 const LivingUiRequest267V1&,std::uint64_t,living_inventory_private::LivingFiniteCase267V1&,
 LivingUiRaw267V1&,std::string&)noexcept;
bool SameLivingUiRaw267V1(const LivingUiRaw267V1&,const LivingUiRaw267V1&)noexcept;
LivingUiCall267V1 CallLivingUiRaw267V1(const ReadonlyBindings&,const LivingUiFrame267V1&,
 const LivingUiRequest267V1&,std::uint64_t,const LivingUiRaw267V1&,
 living_inventory_private::LivingFiniteCase267V1&,LivingWeaponPrivateSession267V1&)noexcept;
class LivingUiSession267V1;
struct LivingUiContext267V1 {
 LivingOwnerInvocation267V1 invocation{0x4C49564932363731ULL,LivingInvocationKind267V1::ui,this};
 ReadonlyBindings bindings;ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;
 ck3_11906::MainThreadQueryTicketV1 ticket;
 LivingUiRequest267V1 request;LivingUiResult267V1 result;LivingUiSession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;
 bool observation_entered=false;
};
class LivingUiSession267V1 {
 public:LivingUiSession267V1();~LivingUiSession267V1();
 LivingUiSession267V1(const LivingUiSession267V1&)=delete;
 LivingUiSession267V1&operator=(const LivingUiSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool ExecuteLivingUiInner267V1(LivingUiContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
};
LivingUiSession267V1&RetainedLivingUiSession267V1();
void ArmLivingUiDeadline267V1(LivingUiContext267V1&)noexcept;
bool ExecuteLivingUiInner267V1(LivingUiContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ExecuteLivingUiOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadLivingUiFrameOnOwner267V1(const ReadonlyBindings&,
 ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,
 const ck3_11906::MainThreadExecutionStampV1&,void*,const LivingUiRequest267V1&,
 std::uint64_t,LivingUiFrame267V1&,std::string&)noexcept;
const game::AdapterDescriptor&LivingUiDescriptor267V1(const game::AdapterDescriptor&)noexcept;
bool LivingUiStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchLivingUiRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
