#pragma once
#include "xar_bridge/ck3_121003_rite_creation_blockers26785313_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/ck3_121003_rite_create26785313_owner_v1.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
using RiteBlockersFrame267V1=RiteCreateFrame267V1;
struct RiteBlockersRaw267V1 {RiteBlockersSource267V1 source{};RiteDraftV2 draft{};std::uintptr_t controller=0,context=0,root=0;bool entered=false,cleanup_known=true;friend bool operator==(const RiteBlockersRaw267V1&,const RiteBlockersRaw267V1&)=default;};
struct RiteBlockersContext267V1;
class RiteBlockersSession267V1 {
 public:RiteBlockersSession267V1();~RiteBlockersSession267V1();RiteBlockersSession267V1(const RiteBlockersSession267V1&)=delete;RiteBlockersSession267V1&operator=(const RiteBlockersSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;friend bool ExecuteRiteBlockersInner267V1(RiteBlockersContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;friend void BlockRiteBlockersUnknown267V1(RiteBlockersSession267V1&)noexcept;
};
struct RiteBlockersContext267V1 {ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};RiteBlockersRequest267V1 request{};RiteBlockersResult267V1 result{};RiteBlockersSession267V1*session=nullptr;std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool native_observation_entered=false;};
RiteBlockersSession267V1&RetainedRiteBlockersSession267V1();
void ArmRiteBlockersDeadline267V1(RiteBlockersContext267V1&)noexcept;
void BlockRiteBlockersUnknown267V1(RiteBlockersSession267V1&)noexcept;
bool ExecuteRiteBlockersInner267V1(RiteBlockersContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ExecuteRiteBlockersOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadRiteBlockersFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,const RiteBlockersRequest267V1&,std::uint64_t,RiteBlockersFrame267V1&,std::string&)noexcept;
bool VerifyRiteBlockersImage267V1(std::uintptr_t)noexcept;
bool ReadRiteBlockersRaw267V1(const ReadonlyBindings&,const RiteBlockersFrame267V1&,const RiteBlockersRequest267V1&,std::uint64_t,RiteBlockersRaw267V1&,std::string&)noexcept;
bool RiteBlockersStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchRiteBlockersRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
