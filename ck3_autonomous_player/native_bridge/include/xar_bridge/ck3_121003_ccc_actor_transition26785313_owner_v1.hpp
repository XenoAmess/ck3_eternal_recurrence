#pragma once
#include "xar_bridge/ck3_121003_ccc_actor_transition26785313_wire_v1.hpp"
#include "xar_bridge/ck3_121003_ccc_date_proof26785313_v1.hpp"
#include "xar_bridge/ck3_121003_date_family_custody26785313_v1.hpp"
#include "xar_bridge/ck3_121003_date_advance26785313_v1.hpp"
#include <memory>
#include "xar_bridge/ck3_121003_ccc_owner26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
struct CccRoleFrame267V1 {bool facts_verified=false;ck3_1210::DateSentinelObservationV1 world{};};
struct CccRoleRaw267V1 {
 std::uintptr_t definition=0;std::array<std::byte,64>definition_header{};
 bool shown=false,entered=false,cleanup_known=true;
 friend bool operator==(const CccRoleRaw267V1&,const CccRoleRaw267V1&)=default;
};
struct CccTransitionContext267V1;
class CccTransitionSession267V1 {
 public:CccTransitionSession267V1();~CccTransitionSession267V1();
 CccTransitionSession267V1(const CccTransitionSession267V1&)=delete;CccTransitionSession267V1&operator=(const CccTransitionSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool BindCccTransitionSession267V1(CccTransitionSession267V1&,DateAdvanceSession267V1&,ck3_1210::DateSentinelStateV1&)noexcept;
 friend bool ExecuteCccTransitionInner267V1(CccTransitionContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
 friend CccTransitionResult267V1 QueryCccTransitionOperation267V1(CccTransitionSession267V1&,const CccTransitionRequest267V1&,std::uint64_t,bool*)noexcept;
 friend void BlockCccTransitionUnknown267V1(CccTransitionSession267V1&)noexcept;
 friend bool CccCaseAdmitted267V1(const ck3_1210::CoreSnapshotPrefix&,std::uint64_t,std::uintptr_t,std::uintptr_t)noexcept;
};
struct CccTransitionContext267V1 {
 CccOwnerInvocation267V1 invocation{0x4343433236375631ULL,CccInvocationKind267V1::transition,this};
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};
 CccTransitionRequest267V1 request{};CccTransitionResult267V1 result{};CccTransitionSession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool native_observation_entered=false,command_ownership_entered=false,deferred_observation_only=false;
};
CccTransitionSession267V1&RetainedCccTransitionSession267V1();
bool BindCccTransitionSession267V1(CccTransitionSession267V1&,DateAdvanceSession267V1&,ck3_1210::DateSentinelStateV1&)noexcept;
void ArmCccTransitionDeadline267V1(CccTransitionContext267V1&)noexcept;
void BlockCccTransitionUnknown267V1(CccTransitionSession267V1&)noexcept;
bool ExecuteCccTransitionInner267V1(CccTransitionContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ExecuteCccTransitionOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
CccTransitionResult267V1 QueryCccTransitionOperation267V1(CccTransitionSession267V1&,const CccTransitionRequest267V1&,std::uint64_t,bool*deferred_needed=nullptr)noexcept;
bool ReadCccRoleFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,
 const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,CccRoleFrame267V1&,std::string&)noexcept;
bool VerifyCccRoleImage267V1(std::uintptr_t)noexcept;
bool ReadCccRoleRaw267V1(const ReadonlyBindings&,const CccRoleFrame267V1&,bool,std::uint64_t,std::uint64_t,CccRoleRaw267V1&,std::string&)noexcept;
bool CccTransitionStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchCccTransitionRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
