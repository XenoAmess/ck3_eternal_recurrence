#pragma once
#include "xar_bridge/ck3_121003_xqol_conversion_prompt26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_xqol_conversion_prompt26785313_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
struct XqolPromptFrame267V1{bool facts_verified=false;ck3_1210::CoreSnapshotPrefix core{};XqolConversionScene267V1 scene{};std::vector<GuiWindowNodeV1>witness;};
struct XqolPromptContext267V1;
class XqolPromptSession267V1{
 public:XqolPromptSession267V1();~XqolPromptSession267V1();XqolPromptSession267V1(const XqolPromptSession267V1&)=delete;XqolPromptSession267V1&operator=(const XqolPromptSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool ExecuteXqolPromptInner267V1(XqolPromptContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
 friend void BlockXqolPromptUnknown267V1(XqolPromptSession267V1&)noexcept;
};
struct XqolPromptContext267V1{
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};
 XqolPromptRequest267V1 request{};XqolPromptResult267V1 result{};XqolPromptSession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool native_observation_entered=false;
};
XqolPromptSession267V1& RetainedXqolPromptSession267V1();
void ArmXqolPromptDeadline267V1(XqolPromptContext267V1&)noexcept;
void BlockXqolPromptUnknown267V1(XqolPromptSession267V1&)noexcept;
bool ExecuteXqolPromptOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadXqolPromptFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,
 const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,XqolPromptFrame267V1&,std::string&)noexcept;
bool XqolPromptStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchXqolPromptRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
} // namespace
