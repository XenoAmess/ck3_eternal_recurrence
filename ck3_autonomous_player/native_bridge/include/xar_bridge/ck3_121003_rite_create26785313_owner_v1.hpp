#pragma once
#include "xar_bridge/ck3_121003_rite_create26785313_v1.hpp"
#include "xar_bridge/ck3_121003_rite_draft26785313_v2.hpp"
#include "xar_bridge/ck3_121003_gui_controls26785313_v2.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <memory>
#include <vector>
namespace xar::ck3_121003::build26785313 {
struct RiteCreateFrame267V1{bool facts_verified=false;ck3_1210::CoreSnapshotPrefix core{};std::uintptr_t game=0,jomini=0,storage=0,actor=0;std::optional<RiteDraftV2>draft;};
struct RiteCreateAssociation267V1{std::uintptr_t controller=0,context=0,window_root=0;std::uint32_t source_rite_id=0xFFFFFFFFU;std::int32_t actor_id=-1;std::uint64_t connection=0,original_deadline=0;std::array<std::byte,16>selected_draft_header{};std::vector<std::array<std::byte,0x48>>selected_draft_rows;friend bool operator==(const RiteCreateAssociation267V1&,const RiteCreateAssociation267V1&)=default;};
struct RiteCreateRaw267V1{RiteCreateSource267V1 source{};std::uintptr_t controller=0,context=0,root=0,create_button=0,modal=0,manager=0;bool pending=false,entered=false,cleanup_known=true;std::optional<RiteDraftV2>draft_witness;std::optional<ck3_1210::GuiControlCaptureV1>controls_witness;RiteDoctrineItems267V1 doctrine_items;std::array<std::byte,16>selected_draft_header{},dialog_header{};std::vector<std::array<std::byte,0x48>>selected_draft_rows;std::vector<std::uintptr_t>dialog_pointers;friend bool operator==(const RiteCreateRaw267V1&,const RiteCreateRaw267V1&)=default;};
enum class RiteCreateCallStatus267V1{unavailable,returned,indeterminate};
struct RiteCreateCall267V1{RiteCreateCallStatus267V1 status=RiteCreateCallStatus267V1::unavailable;bool entered=false,cleanup_known=true;};
struct RiteCreateContext267V1;
class RiteCreateSession267V1{public:RiteCreateSession267V1();~RiteCreateSession267V1();RiteCreateSession267V1(const RiteCreateSession267V1&)=delete;RiteCreateSession267V1&operator=(const RiteCreateSession267V1&)=delete;private:struct State;std::unique_ptr<State>state_;friend bool ExecuteRiteCreateInner267V1(RiteCreateContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;friend void BlockRiteCreateUnknown267V1(RiteCreateSession267V1&)noexcept;};
struct RiteCreateContext267V1{ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};RiteCreateRequest267V1 request{};RiteCreateResult267V1 result{};RiteCreateSession267V1*session=nullptr;std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool observation_entered=false;};
RiteCreateSession267V1&RetainedRiteCreateSession267V1();void ArmRiteCreateDeadline267V1(RiteCreateContext267V1&)noexcept;void BlockRiteCreateUnknown267V1(RiteCreateSession267V1&)noexcept;
bool ExecuteRiteCreateInner267V1(RiteCreateContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;bool ExecuteRiteCreateOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadRiteCreateFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,const RiteCreateRequest267V1&,std::uint64_t,RiteCreateFrame267V1&,std::string&)noexcept;
bool ReadRiteCreateConfirmationWindowOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,const RiteCreateRequest267V1&,std::uint64_t,GuiWindowV1&,std::string&)noexcept;
bool VerifyRiteCreateImage267V1(std::uintptr_t)noexcept;
bool ReadRiteCreateRaw267V1(const ReadonlyBindings&,const RiteCreateFrame267V1&,const RiteCreateRequest267V1&,const std::optional<RiteCreateAssociation267V1>&,std::uint64_t,RiteCreateRaw267V1&,std::string&)noexcept;
bool BindRiteCreateConfirmationWindow267V1(const ReadonlyBindings&,const GuiWindowV1&,RiteCreateRaw267V1&,std::string&)noexcept;
RiteCreateCall267V1 CallRiteCreateRaw267V1(const ReadonlyBindings&,const RiteCreateFrame267V1&,const RiteCreateRequest267V1&,const std::optional<RiteCreateAssociation267V1>&,std::uint64_t,const RiteCreateRaw267V1&)noexcept;
bool RiteCreateStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchRiteCreateRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
