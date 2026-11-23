#pragma once
#include "xar_bridge/ck3_121003_ccc_event26785313_v1.hpp"
#include "xar_bridge/ck3_121003_lyd26785313_owner_v1.hpp"
#include <memory>
#include "xar_bridge/ck3_121003_ccc_owner26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
struct CccEventFrame267V1:LydFrame267V1{std::uint64_t connection_generation=0;};
struct CccEventRaw267V1{LydRaw267V1 material{};CccEventSource267V1 source{};friend bool operator==(const CccEventRaw267V1&,const CccEventRaw267V1&)=default;};
enum class CccEventCallStatus267V1{refused,returned,indeterminate};
struct CccEventCall267V1{CccEventCallStatus267V1 status=CccEventCallStatus267V1::refused;bool entered=false,native_returned=false,cleanup_known=true;};
struct CccEventContext267V1;
class CccEventSession267V1{public:CccEventSession267V1();~CccEventSession267V1();CccEventSession267V1(const CccEventSession267V1&)=delete;CccEventSession267V1&operator=(const CccEventSession267V1&)=delete;private:struct State;std::unique_ptr<State>state_;friend bool ExecuteCccEventInner267V1(CccEventContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;friend void BlockCccEventUnknown267V1(CccEventSession267V1&)noexcept;};
struct CccEventContext267V1{CccOwnerInvocation267V1 invocation{0x4343433236375631ULL,CccInvocationKind267V1::event,this};ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};CccEventRequest267V1 request{};CccEventResult267V1 result{};CccEventSession267V1*session=nullptr;std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool observation_entered=false;};
CccEventSession267V1&RetainedCccEventSession267V1();void BlockCccEventUnknown267V1(CccEventSession267V1&)noexcept;void ArmCccEventDeadline267V1(CccEventContext267V1&)noexcept;
bool ExecuteCccEventInner267V1(CccEventContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;bool ExecuteCccEventOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadCccEventFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,CccEventFrame267V1&,std::string&)noexcept;
bool VerifyCccEventImage267V1(std::uintptr_t)noexcept;
bool ReadCccEventRaw267V1(const ReadonlyBindings&,const CccEventFrame267V1&,const CccEventRequest267V1&,std::uint64_t,CccEventRaw267V1&,std::string&)noexcept;
CccEventCall267V1 CallCccEventRaw267V1(const ReadonlyBindings&,const CccEventFrame267V1&,const CccEventRequest267V1&,std::uint64_t,const CccEventRaw267V1&)noexcept;
bool CccEventStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchCccEventRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
