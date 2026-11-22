#pragma once
#include "xar_bridge/ck3_121003_ted_actor_transition26785313_wire_v1.hpp"
#include "xar_bridge/ck3_121003_ted_date_proof26785313_v1.hpp"
#include "xar_bridge/ck3_121003_date_family_custody26785313_v1.hpp"
#include "xar_bridge/ck3_121003_date_advance26785313_v1.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
struct TedRoleFrame267V1 {bool facts_verified=false;ck3_1210::DateSentinelObservationV1 world{};};
struct TedRoleRaw267V1 {
 std::uintptr_t definition=0;std::array<std::byte,64>definition_header{};
 bool shown=false,entered=false,cleanup_known=true;
 friend bool operator==(const TedRoleRaw267V1&,const TedRoleRaw267V1&)=default;
};
struct TedTransitionContext267V1;
class TedTransitionSession267V1 {
 public:TedTransitionSession267V1();~TedTransitionSession267V1();
 TedTransitionSession267V1(const TedTransitionSession267V1&)=delete;TedTransitionSession267V1&operator=(const TedTransitionSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool BindTedTransitionSession267V1(TedTransitionSession267V1&,DateAdvanceSession267V1&,ck3_1210::DateSentinelStateV1&)noexcept;
 friend bool ExecuteTedTransitionInner267V1(TedTransitionContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
 friend TedTransitionResult267V1 QueryTedTransitionOperation267V1(TedTransitionSession267V1&,const TedTransitionRequest267V1&,std::uint64_t)noexcept;
 friend void BlockTedTransitionUnknown267V1(TedTransitionSession267V1&)noexcept;
};
struct TedTransitionContext267V1 {
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};
 TedTransitionRequest267V1 request{};TedTransitionResult267V1 result{};TedTransitionSession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool native_observation_entered=false,command_ownership_entered=false;
};
TedTransitionSession267V1&RetainedTedTransitionSession267V1();
bool BindTedTransitionSession267V1(TedTransitionSession267V1&,DateAdvanceSession267V1&,ck3_1210::DateSentinelStateV1&)noexcept;
void ArmTedTransitionDeadline267V1(TedTransitionContext267V1&)noexcept;
void BlockTedTransitionUnknown267V1(TedTransitionSession267V1&)noexcept;
bool ExecuteTedTransitionInner267V1(TedTransitionContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ExecuteTedTransitionOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
TedTransitionResult267V1 QueryTedTransitionOperation267V1(TedTransitionSession267V1&,const TedTransitionRequest267V1&,std::uint64_t)noexcept;
bool ReadTedRoleFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,
 const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,TedRoleFrame267V1&,std::string&)noexcept;
bool VerifyTedRoleImage267V1(std::uintptr_t)noexcept;
bool ReadTedRoleRaw267V1(const ReadonlyBindings&,const TedRoleFrame267V1&,bool,std::uint64_t,std::uint64_t,TedRoleRaw267V1&,std::string&)noexcept;
bool TedTransitionStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchTedTransitionRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
