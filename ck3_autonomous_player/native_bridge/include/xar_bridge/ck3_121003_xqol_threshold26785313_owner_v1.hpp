#pragma once
#include "xar_bridge/ck3_121003_xqol_threshold26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_xqol_threshold26785313_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
struct XqolThresholdFrame267V1{bool facts_verified=false,native_read_entered=false,cleanup_known=true;ck3_1210::CoreSnapshotPrefix core{};XqolThresholdScene267V1 scene{};std::vector<GuiWindowNodeV1>witness;};
struct XqolThresholdContext267V1;
class XqolThresholdSession267V1{
 public:XqolThresholdSession267V1();~XqolThresholdSession267V1();XqolThresholdSession267V1(const XqolThresholdSession267V1&)=delete;XqolThresholdSession267V1&operator=(const XqolThresholdSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool ExecuteXqolThresholdInner267V1(XqolThresholdContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
 friend void BlockXqolThresholdUnknown267V1(XqolThresholdSession267V1&)noexcept;
};
struct XqolThresholdContext267V1{
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};
 XqolThresholdRequest267V1 request{};XqolThresholdResult267V1 result{};XqolThresholdSession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool native_observation_entered=false;
};
XqolThresholdSession267V1& RetainedXqolThresholdSession267V1();
void ArmXqolThresholdDeadline267V1(XqolThresholdContext267V1&)noexcept;
void BlockXqolThresholdUnknown267V1(XqolThresholdSession267V1&)noexcept;
bool ExecuteXqolThresholdOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadXqolThresholdFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,
 const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,XqolThresholdFrame267V1&,std::string&)noexcept;
bool XqolThresholdStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchXqolThresholdRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
} // namespace
