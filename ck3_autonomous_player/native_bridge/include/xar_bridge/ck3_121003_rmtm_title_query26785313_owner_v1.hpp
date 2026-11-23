#pragma once
#include "xar_bridge/ck3_121003_rmtm_title_query26785313_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
struct RmtmTitleQueryContext267V1;
class RmtmTitleQuerySession267V1 {
 public:RmtmTitleQuerySession267V1();~RmtmTitleQuerySession267V1();
 RmtmTitleQuerySession267V1(const RmtmTitleQuerySession267V1&)=delete;
 RmtmTitleQuerySession267V1&operator=(const RmtmTitleQuerySession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool ExecuteRmtmTitleQueryInner267V1(RmtmTitleQueryContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
 friend void BlockRmtmTitleQueryUnknown267V1(RmtmTitleQuerySession267V1&)noexcept;
};
struct RmtmTitleQueryContext267V1 {
 ReadonlyBindings bindings{};
 ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;
 ck3_11906::MainThreadQueryTicketV1 ticket{};
 RmtmTitleQueryRequest267V1 request{};RmtmTitleQueryResult267V1 result{};
 RmtmTitleQuerySession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;
 bool native_observation_entered=false;
 // Written only by the actual owner capture, never parsed or caller-set.
 std::uint32_t captured_full_title_id=0xFFFFFFFFU;
};
RmtmTitleQuerySession267V1&RetainedRmtmTitleQuerySession267V1();
void ArmRmtmTitleQueryDeadline267V1(RmtmTitleQueryContext267V1&)noexcept;
void BlockRmtmTitleQueryUnknown267V1(RmtmTitleQuerySession267V1&)noexcept;
bool ExecuteRmtmTitleQueryInner267V1(RmtmTitleQueryContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ExecuteRmtmTitleQueryOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadRmtmTitleQueryFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,const RmtmTitleQueryRequest267V1&,std::uint64_t,RmtmTitleFrame267V1&,std::string&)noexcept;
bool CaptureRmtmTitleQueryPrimary267V1(const ReadonlyBindings&,const RmtmTitleFrame267V1&,const RmtmTitleQueryRequest267V1&,std::uint64_t,std::uint32_t&,bool&entered,bool&cleanup_known,std::string&)noexcept;
bool RmtmTitleQueryStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchRmtmTitleQueryRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
