#pragma once
#include "xar_bridge/ck3_121003_djc_target_query26785313_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
struct DjcTargetQueryContext267V1;
class DjcTargetQuerySession267V1 {
 public:DjcTargetQuerySession267V1();~DjcTargetQuerySession267V1();
 DjcTargetQuerySession267V1(const DjcTargetQuerySession267V1&)=delete;
 DjcTargetQuerySession267V1&operator=(const DjcTargetQuerySession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool ExecuteDjcTargetQueryInner267V1(DjcTargetQueryContext267V1&,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
 friend void BlockDjcTargetQueryUnknown267V1(DjcTargetQuerySession267V1&) noexcept;
};
struct DjcTargetQueryContext267V1 {
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;
 ck3_11906::MainThreadQueryTicketV1 ticket{};DjcTargetQueryRequest267V1 request{};
 DjcTargetQueryResult267V1 result{};DjcTargetQuerySession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool native_query_entered=false;
};
void ArmDjcTargetQueryDeadline267V1(DjcTargetQueryContext267V1&) noexcept;
void BlockDjcTargetQueryUnknown267V1(DjcTargetQuerySession267V1&) noexcept;
bool ExecuteDjcTargetQueryOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
bool ReadDjcTargetQueryCoreOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,
 const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,ReadonlyObservation&) noexcept;
bool DjcTargetQueryRouteEnabled267V1(const game::AdapterDescriptor&) noexcept;
std::string DispatchDjcTargetQueryRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,
 std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
