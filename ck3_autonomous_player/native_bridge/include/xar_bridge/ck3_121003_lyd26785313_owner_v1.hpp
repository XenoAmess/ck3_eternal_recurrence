#pragma once
#include "xar_bridge/ck3_121003_lyd26785313_raw_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/ck3_121003_full111_event_option_v2.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
struct LydFrame267V1{
 bool facts_verified=false;ck3_1210::CoreSnapshotPrefix core{};LydScene267V1 scene{};
 std::vector<GuiWindowNodeV1>witness;std::vector<std::byte>name_witness;
};
enum class Full111OptionContextStorage267V2 : std::uint8_t { unavailable, direct = 1, typed_thunk = 3 };
struct Full111EventRendererMaterial267V2 {
 struct Option {
  std::uintptr_t widget=0, model=0, cell_context_identity=0;
  std::int32_t authored_index=-1;
  Full111OptionContextStorage267V2 cell_context_storage=Full111OptionContextStorage267V2::unavailable;
  friend bool operator==(const Option &, const Option &) = default;
 };
 std::uintptr_t game_data=0, queue_items=0, controller=0, root=0, data=0, runtime=0, definition=0, grid=0;
 std::vector<std::uintptr_t> queue_rows;
 std::vector<Option> options;
 friend bool operator==(const Full111EventRendererMaterial267V2 &, const Full111EventRendererMaterial267V2 &) = default;
};
struct LydContext267V1;
class LydSession267V1{
 public:LydSession267V1();~LydSession267V1();LydSession267V1(const LydSession267V1&)=delete;LydSession267V1&operator=(const LydSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool ExecuteLydInner267V1(LydContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
 friend void BlockLydUnknown267V1(LydSession267V1&)noexcept;
};
struct LydContext267V1{
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};
 LydRequest267V1 request{};LydResult267V1 result{};LydSession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0,published_revision=0;
 std::optional<Full111EventOptionRequest267V2> event_option_request;
 Full111EventOptionResult267V2 event_option_result;
 Full111EventRendererMaterial267V2 renderer_material;
 bool native_observation_entered=false,full111_ordinary_events_only=false,full111_event_renderer=false;
};
LydSession267V1&RetainedLydSession267V1();
void ArmLydDeadline267V1(LydContext267V1&)noexcept;
void BlockLydUnknown267V1(LydSession267V1&)noexcept;
bool ExecuteLydInner267V1(LydContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ExecuteLydOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadLydFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,
 const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,
 LydKind267V1,std::uint64_t,std::uint64_t,LydFrame267V1&,std::string&)noexcept;
bool ReadFull111EventRendererOnOwner267V1(const ReadonlyBindings&, ck3_11906::MainThreadQueryMailboxV1*,
 const ck3_11906::MainThreadQueryTicketV1&, const ck3_11906::MainThreadExecutionStampV1&, void*,
 const LydFrame267V1&, const LydRequest267V1&, std::uint64_t, Full111EventRendererSource267V1&,
 bool &native_read_entered, bool &cleanup_known, std::string&, Full111EventRendererMaterial267V2 *material=nullptr) noexcept;
bool ReadFull111EventQueueOnOwner267V2(const ReadonlyBindings&, ck3_11906::MainThreadQueryMailboxV1*,
 const ck3_11906::MainThreadQueryTicketV1&, const ck3_11906::MainThreadExecutionStampV1&, void*,
 const Full111EventOptionRequest267V2&, std::uint64_t, ck3_1210::CoreSnapshotPrefix&, Full111EventQueue267V2&) noexcept;
bool SampleFull111EventQueue267V2(const ReadonlyBindings&, std::uintptr_t, const Full111EventOptionTarget267V2&,
 Full111EventQueue267V2&);
LydRawCall267V1 CallFull111StockOption267V2(const ReadonlyBindings&, std::uintptr_t) noexcept;
LydRawCall267V1 SelectFull111RenderedOptionOnOwner267V2(const ReadonlyBindings&, ck3_11906::MainThreadQueryMailboxV1*,
 const ck3_11906::MainThreadQueryTicketV1&, const ck3_11906::MainThreadExecutionStampV1&, void*,
 const LydFrame267V1&, const Full111EventOptionRequest267V2&, std::uint64_t,
 const Full111EventRendererMaterial267V2::Option&, const Full111EventRendererMaterial267V2&) noexcept;
bool LydStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchLydRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&,std::uint64_t published_revision=0);
}
