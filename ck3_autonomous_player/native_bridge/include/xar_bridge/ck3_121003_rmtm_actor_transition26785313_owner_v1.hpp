#pragma once
#include "xar_bridge/ck3_121003_rmtm_actor_transition26785313_wire_v1.hpp"
#include "xar_bridge/ck3_121003_rmtm_day_port26785313_v1.hpp"
#include "xar_bridge/ck3_121003_date_family_custody26785313_v1.hpp"
#include "xar_bridge/ck3_121003_date_advance26785313_v1.hpp"
#include <memory>
#include <vector>
#include "xar_bridge/ck3_121003_rmtm_owner26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
struct RmtmRoleFrame267V1 {bool facts_verified=false;ck3_1210::DateSentinelObservationV1 world{};};
struct RmtmRoleRaw267V1 {
 std::uintptr_t definition=0;std::array<std::byte,64>definition_header{};std::vector<std::byte>all_definition_fingerprint;
 bool shown=false,entered=false,cleanup_known=true;std::array<bool,7> predicates{};
 friend bool operator==(const RmtmRoleRaw267V1&,const RmtmRoleRaw267V1&)=default;
};
struct RmtmTransitionContext267V1;
class RmtmTransitionSession267V1 {
 public:RmtmTransitionSession267V1();~RmtmTransitionSession267V1();
 RmtmTransitionSession267V1(const RmtmTransitionSession267V1&)=delete;RmtmTransitionSession267V1&operator=(const RmtmTransitionSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool BindRmtmTransitionSession267V1(RmtmTransitionSession267V1&,DateAdvanceSession267V1&,ck3_1210::DateSentinelStateV1&)noexcept;
 friend bool ExecuteRmtmTransitionInner267V1(RmtmTransitionContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
 friend RmtmTransitionResult267V1 QueryRmtmTransitionOperation267V1(RmtmTransitionSession267V1&,const RmtmTransitionRequest267V1&,std::uint64_t,bool*)noexcept;
 friend void BlockRmtmTransitionUnknown267V1(RmtmTransitionSession267V1&)noexcept;
 friend bool ReadRmtmPrivateCaseAnchor267V1(const ck3_1210::CoreSnapshotPrefix&,std::uint64_t,std::uintptr_t,std::uintptr_t,RmtmPrivateCaseAnchor267V1&)noexcept;
 friend bool RmtmCaseAdmitted267V1(const ck3_1210::CoreSnapshotPrefix&,std::uint64_t,std::uintptr_t,std::uintptr_t)noexcept;
};
struct RmtmTransitionContext267V1 {
 RmtmOwnerInvocation267V1 invocation{0x524D544D32363731ULL,RmtmInvocationKind267V1::transition,this};
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};
 RmtmTransitionRequest267V1 request{};RmtmTransitionResult267V1 result{};RmtmTransitionSession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool native_observation_entered=false,command_ownership_entered=false,deferred_observation_only=false;
};
RmtmTransitionSession267V1&RetainedRmtmTransitionSession267V1();
bool BindRmtmTransitionSession267V1(RmtmTransitionSession267V1&,DateAdvanceSession267V1&,ck3_1210::DateSentinelStateV1&)noexcept;
void ArmRmtmTransitionDeadline267V1(RmtmTransitionContext267V1&)noexcept;
void BlockRmtmTransitionUnknown267V1(RmtmTransitionSession267V1&)noexcept;
bool ExecuteRmtmTransitionInner267V1(RmtmTransitionContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ExecuteRmtmTransitionOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
RmtmTransitionResult267V1 QueryRmtmTransitionOperation267V1(RmtmTransitionSession267V1&,const RmtmTransitionRequest267V1&,std::uint64_t,bool*deferred_needed=nullptr)noexcept;
bool ReadRmtmRoleFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,
 const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,RmtmRoleFrame267V1&,std::string&)noexcept;
bool VerifyRmtmRoleImage267V1(std::uintptr_t)noexcept;
bool ReadRmtmRoleRaw267V1(const ReadonlyBindings&,const RmtmRoleFrame267V1&,bool,std::uint64_t,std::uint64_t,RmtmRoleRaw267V1&,std::string&)noexcept;
bool RmtmTransitionStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchRmtmTransitionRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
