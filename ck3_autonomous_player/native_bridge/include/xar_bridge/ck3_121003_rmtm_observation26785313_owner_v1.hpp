#pragma once
#include "xar_bridge/ck3_121003_rmtm_observation26785313_v1.hpp"
#include "xar_bridge/ck3_121003_rmtm_decision26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_rmtm_actor_transition26785313_owner_v1.hpp"
namespace xar::ck3_121003::build26785313 {
struct RmtmObservationFrame267V1 {
 bool facts_verified=false;ck3_1210::CoreSnapshotPrefix core{};RmtmRoleFrame267V1 role{};
 RmtmDecisionScene267V1 scene{};std::vector<GuiWindowNodeV1>witness;std::uint64_t connection_generation=0;
};
struct RmtmObservationRaw267V1 {
 RmtmObservationSource267V1 source{};std::vector<std::byte>fingerprint;
 std::uintptr_t window=0,root=0,menu=0,item=0,definition=0,origin_widget=0;
 bool entered=false,cleanup_known=true;
 friend bool operator==(const RmtmObservationRaw267V1&,const RmtmObservationRaw267V1&)=default;
};
enum class RmtmObservationCallStatus267V1 {refused,returned,indeterminate};
struct RmtmObservationCall267V1 {RmtmObservationCallStatus267V1 status=RmtmObservationCallStatus267V1::refused;bool entered=false,native_returned=false,native_handled=false,cleanup_known=true;};
struct RmtmObservationContext267V1;
class RmtmObservationSession267V1 {
 public:RmtmObservationSession267V1();~RmtmObservationSession267V1();RmtmObservationSession267V1(const RmtmObservationSession267V1&)=delete;RmtmObservationSession267V1&operator=(const RmtmObservationSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;friend bool ExecuteRmtmObservationInner267V1(RmtmObservationContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;friend void BlockRmtmObservationUnknown267V1(RmtmObservationSession267V1&)noexcept;
};
struct RmtmObservationContext267V1 {
 RmtmOwnerInvocation267V1 invocation{0x524D544D32363731ULL,RmtmInvocationKind267V1::observation,this};
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};
 RmtmObservationRequest267V1 request{};RmtmObservationResult267V1 result{};RmtmObservationSession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool observation_entered=false;
};
RmtmObservationSession267V1&RetainedRmtmObservationSession267V1();
void ArmRmtmObservationDeadline267V1(RmtmObservationContext267V1&)noexcept;
void BlockRmtmObservationUnknown267V1(RmtmObservationSession267V1&)noexcept;
bool ExecuteRmtmObservationInner267V1(RmtmObservationContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ExecuteRmtmObservationOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadRmtmObservationFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,RmtmObservationFrame267V1&,std::string&)noexcept;
bool VerifyRmtmObservationImage267V1(std::uintptr_t)noexcept;
bool ReadRmtmObservationRaw267V1(const ReadonlyBindings&,const RmtmObservationFrame267V1&,const RmtmObservationRequest267V1&,std::uint64_t,RmtmObservationRaw267V1&,std::string&)noexcept;
RmtmObservationCall267V1 CallRmtmObservationRaw267V1(const ReadonlyBindings&,const RmtmObservationFrame267V1&,const RmtmObservationRequest267V1&,std::uint64_t,const RmtmObservationRaw267V1&)noexcept;
bool RmtmObservationStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchRmtmObservationRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
