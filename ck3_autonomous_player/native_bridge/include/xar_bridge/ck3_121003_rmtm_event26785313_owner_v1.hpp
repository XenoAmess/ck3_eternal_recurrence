#pragma once
#include "xar_bridge/ck3_121003_rmtm_event26785313_v1.hpp"
#include "xar_bridge/ck3_121003_lyd26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_fullscreen_event26785313_raw_v1.hpp"
#include <memory>
#include "xar_bridge/ck3_121003_rmtm_owner26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
struct RmtmEventFrame267V1:LydFrame267V1{std::uint64_t connection_generation=0;FullscreenEventScene267V1 fullscreen_scene{};FullscreenEventBindings267V1 fullscreen_bindings{};std::vector<GuiWindowNodeV1>fullscreen_witness;};
struct RmtmEventRaw267V1{LydRaw267V1 material{};FullscreenEventRaw267V1 fullscreen{};bool fullscreen_channel=false;RmtmEventSource267V1 source{};std::vector<std::byte>empty_chaos_proof;friend bool operator==(const RmtmEventRaw267V1&,const RmtmEventRaw267V1&)=default;};
enum class RmtmEventCallStatus267V1{refused,returned,indeterminate};
struct RmtmEventCall267V1{RmtmEventCallStatus267V1 status=RmtmEventCallStatus267V1::refused;bool entered=false,native_returned=false,cleanup_known=true;};
struct RmtmEventContext267V1;
class RmtmEventSession267V1{public:RmtmEventSession267V1();~RmtmEventSession267V1();RmtmEventSession267V1(const RmtmEventSession267V1&)=delete;RmtmEventSession267V1&operator=(const RmtmEventSession267V1&)=delete;private:struct State;std::unique_ptr<State>state_;friend bool ExecuteRmtmEventInner267V1(RmtmEventContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;friend void BlockRmtmEventUnknown267V1(RmtmEventSession267V1&)noexcept;};
struct RmtmEventContext267V1{RmtmOwnerInvocation267V1 invocation{0x524D544D32363731ULL,RmtmInvocationKind267V1::event,this};ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};RmtmEventRequest267V1 request{};RmtmEventResult267V1 result{};RmtmEventSession267V1*session=nullptr;std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool observation_entered=false;};
RmtmEventSession267V1&RetainedRmtmEventSession267V1();void BlockRmtmEventUnknown267V1(RmtmEventSession267V1&)noexcept;void ArmRmtmEventDeadline267V1(RmtmEventContext267V1&)noexcept;
bool ExecuteRmtmEventInner267V1(RmtmEventContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;bool ExecuteRmtmEventOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadRmtmEventFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,RmtmEventFrame267V1&,std::string&)noexcept;
bool VerifyRmtmEventImage267V1(std::uintptr_t)noexcept;
bool ReadRmtmEventRaw267V1(const ReadonlyBindings&,const RmtmEventFrame267V1&,const RmtmEventRequest267V1&,std::uint64_t,RmtmEventRaw267V1&,std::string&)noexcept;
RmtmEventCall267V1 CallRmtmEventRaw267V1(const ReadonlyBindings&,const RmtmEventFrame267V1&,const RmtmEventRequest267V1&,std::uint64_t,const RmtmEventRaw267V1&)noexcept;
bool RmtmEventStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchRmtmEventRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
