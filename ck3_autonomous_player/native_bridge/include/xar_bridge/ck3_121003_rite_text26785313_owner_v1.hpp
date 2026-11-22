#pragma once
#include "xar_bridge/ck3_121003_rite_text26785313_v1.hpp"
#include "xar_bridge/ck3_121003_rite_text_values26785313_v1.hpp"
#include "xar_bridge/ck3_121003_rite_create26785313_owner_v1.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
using RiteTextFrame267V1=RiteCreateFrame267V1;
struct RiteTextRaw267V1{RiteTextSource267V1 source{};RiteTextValues267V1 values{};RiteDraftV2 draft{};ck3_1210::GuiControlCaptureV1 controls{};RiteDoctrineItems267V1 doctrine_items{};std::uintptr_t controller=0,context=0,root=0;std::array<std::byte,16>selected_header{};std::vector<std::array<std::byte,0x48>>selected_rows;bool entered=false,cleanup_known=true;friend bool operator==(const RiteTextRaw267V1&,const RiteTextRaw267V1&)=default;};
enum class RiteTextCallStatus267V1{unavailable,returned,indeterminate};struct RiteTextCall267V1{RiteTextCallStatus267V1 status=RiteTextCallStatus267V1::unavailable;bool entered=false,cleanup_known=true;};
struct RiteTextContext267V1;
class RiteTextSession267V1{public:RiteTextSession267V1();~RiteTextSession267V1();RiteTextSession267V1(const RiteTextSession267V1&)=delete;RiteTextSession267V1&operator=(const RiteTextSession267V1&)=delete;private:struct State;std::unique_ptr<State>state_;friend bool ExecuteRiteTextInner267V1(RiteTextContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;friend void BlockRiteTextUnknown267V1(RiteTextSession267V1&)noexcept;};
struct RiteTextContext267V1{ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};RiteTextRequest267V1 request{};RiteTextResult267V1 result{};RiteTextSession267V1*session=nullptr;std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool observation_entered=false;};
RiteTextSession267V1&RetainedRiteTextSession267V1();void ArmRiteTextDeadline267V1(RiteTextContext267V1&)noexcept;void BlockRiteTextUnknown267V1(RiteTextSession267V1&)noexcept;
bool ExecuteRiteTextInner267V1(RiteTextContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;bool ExecuteRiteTextOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadRiteTextFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,const RiteTextRequest267V1&,std::uint64_t,RiteTextFrame267V1&,std::string&)noexcept;
bool VerifyRiteTextImage267V1(std::uintptr_t)noexcept;
bool ReadRiteTextRaw267V1(const ReadonlyBindings&,const RiteTextFrame267V1&,const RiteTextRequest267V1&,std::uint64_t,RiteTextRaw267V1&,std::string&)noexcept;
RiteTextCall267V1 CallRiteTextRaw267V1(const ReadonlyBindings&,const RiteTextFrame267V1&,const RiteTextRequest267V1&,std::uint64_t,const RiteTextRaw267V1&)noexcept;
bool RiteTextStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchRiteTextRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
