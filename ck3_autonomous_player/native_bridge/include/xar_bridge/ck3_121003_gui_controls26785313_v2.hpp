#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include "xar_bridge/ck3_1210_gui_control_v1.hpp"
#include "xar_bridge/ck3_121003_doctrine_key26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
// Internal current ABI/capture leaf, not a capability or callable effect route.
// A later fixed owner executor must supply this frame through the real current
// Core/Window reader, then apply the existing one-use provider before dispatch.
struct GuiControlImage267V2 {std::uintptr_t module_base=0;bool exact_image_admitted=false;};
std::span<const ImagePin> GuiControlImagePins267V2() noexcept;
bool VerifyGuiControlImage267V2(std::uintptr_t) noexcept;
GuiControlImage267V2 BindGuiControlImage267V2(std::uintptr_t,std::string_view) noexcept;
bool CaptureGuiControlWindow267V2(const GuiControlImage267V2&,const GuiWindowV1&,
    ck3_1210::GuiControlCaptureV1&,std::string&) noexcept;
// Separate effect executor; none of the readonly modes executes an action.
inline constexpr char kGuiControlsQueryStep267V2[]="query-scripted-widget-controls-v2";
inline constexpr char kGuiControlsActivateStep267V2[]="activate-scripted-widget-control-v2";
inline constexpr char kGuiControlsQueryCapability267V2[]="game.query.scripted-widget-controls.v2";
inline constexpr char kGuiControlsActivateCapability267V2[]="game.command.activate-scripted-widget-control.v2";
struct GuiControlsRiteSource267V2 {
 std::uintptr_t gfx=0,handler=0,controller=0;
 std::uint32_t source_rite_id=0xFFFFFFFFU;
 std::int32_t actor=-1;
 RiteDoctrineItems267V1 doctrine_items;
 friend bool operator==(const GuiControlsRiteSource267V2&,const GuiControlsRiteSource267V2&)=default;
};
struct GuiControlsSession267V2 {
 ck3_1210::GuiControlProviderV1 provider;
 ck3_1210::CoreSnapshotPrefix issued_core{};
 GuiWindowV1 issued_window{};
 std::optional<GuiControlsRiteSource267V2> issued_rite;
 std::uint64_t connection_generation=0;
};
struct GuiControlsContext267V2 {
 GuiWindowRequestV1 request;
 std::uint32_t expected_source_rite_id=0xFFFFFFFFU,verified_source_rite_id=0xFFFFFFFFU;
 ck3_1210::GuiControlRequestV1 control;
 ReadonlyBindings bindings;
 const game::GameAdapter *game=nullptr;
 ck3_11906::MainThreadQueryMailboxV1 *mailbox=nullptr;
 ck3_11906::MainThreadQueryTicketV1 ticket;
 GuiControlsSession267V2 *session=nullptr;
 std::uint64_t monotonic_deadline_ms=0;
 ck3_1210::CoreSnapshotPrefix observed{};
 ck3_1210::GuiControlResultV1 result;
 bool core_before_verified=false;
 std::uint64_t witness_ticket_sequence=0,witness_pump_epoch=0;
 std::uint32_t witness_thread_id=0;
};
void ArmGuiControlsDeadline267V2(GuiControlsContext267V2&) noexcept;
bool ExecuteGuiControlsOnOwner267V2(void*,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
} // namespace
