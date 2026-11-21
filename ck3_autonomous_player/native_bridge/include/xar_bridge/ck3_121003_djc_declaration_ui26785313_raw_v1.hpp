#pragma once
#include "xar_bridge/ck3_121003_djc_declaration_ui26785313_v1.hpp"
#include <array>
#include <vector>
namespace xar::ck3_121003::build26785313 {
struct DjcUiRawBindings267V1{std::uintptr_t image=0;bool verified=false;};
struct DjcUiExpectedScene267V1{
 std::uint64_t deadline_unix_ms=0;
 std::uintptr_t jomini=0,gfx=0,handler=0,gui_context=0,global_root=0,middle=0,view_root=0;
 bool view_named_bound=false,view_visible=false,view_enabled=false;
 std::uintptr_t warning_root=0;bool warning_named_bound=false,warning_accept_admissible=false;
 friend bool operator==(const DjcUiExpectedScene267V1&,const DjcUiExpectedScene267V1&)=default;
};
struct DjcUiRawRow267V1{std::uintptr_t row=0,definition=0,source_window=0;DjcUiTuple267V1 tuple;
 std::array<std::byte,16>primary_header{},extra_header{};
 friend bool operator==(const DjcUiRawRow267V1&,const DjcUiRawRow267V1&)=default;};
struct DjcUiRawObservation267V1{
 DjcUiSource267V1 source;std::uintptr_t definition=0,actor=0,target=0,additional=0,view=0,outer=0,rows=0;
 std::array<std::byte,16>rows_header{};std::array<std::byte,0x348>context{};
 std::vector<DjcUiRawRow267V1>choices;std::optional<DjcUiRawRow267V1>selected;
 std::uintptr_t manager=0,dialogs=0,modal=0,modal_root=0;std::array<std::byte,16>dialog_header{};
 std::vector<std::uintptr_t>dialog_pointers;std::array<std::byte,0x348>modal_context{};
 bool selected_native_gate=false,cleanup_known=true,no_active_dialog=false,view_material_visible=false,view_material_enabled=false;
};
enum class DjcUiRawCallStatus267V1{unavailable,returned,indeterminate};
struct DjcUiRawCall267V1{DjcUiRawCallStatus267V1 status=DjcUiRawCallStatus267V1::unavailable;bool effect_entered=false,cleanup_known=true;};
bool VerifyDjcUiImage267V1(std::uintptr_t)noexcept;
DjcUiRawBindings267V1 BindDjcUiImage267V1(std::uintptr_t,std::string_view)noexcept;
// These raw source/call primitives are not an owner, private lease or public capability.
// Scene comes only from the formal fixed current owner/widget reader; addresses never cross wire.
bool ReadDjcUiRaw267V1(const ReadonlyBindings&,const DjcUiRawBindings267V1&,const ck3_1210::CoreSnapshotPrefix&,
 std::int32_t target,std::uint8_t cb,const DjcUiExpectedScene267V1&,std::uint64_t monotonic_deadline,
 DjcUiRawObservation267V1&,std::string&)noexcept;
// Claim/warning observation does not re-run the UI updater. The genuine initial UI query
// refreshes once; its exact actual snapshot is then compared without manufacturing a new
// special-payload allocation. Original Send itself refreshes Can/selected gates again.
bool ReadDjcUiRawForClaim267V1(const ReadonlyBindings&,const DjcUiRawBindings267V1&,const ck3_1210::CoreSnapshotPrefix&,
 std::int32_t,std::uint8_t,const DjcUiExpectedScene267V1&,std::uint64_t,DjcUiRawObservation267V1&,std::string&)noexcept;
bool SameDjcUiRaw267V1(const DjcUiRawObservation267V1&,const DjcUiRawObservation267V1&)noexcept;
// CallOpen independently rebuilds the fixed native named context, actual confirmation predicate,
// interface4 and original IsValid; it never accepts caller permission booleans.
DjcUiRawCall267V1 CallDjcUiRaw267V1(DjcUiAction267V1,const ReadonlyBindings&,const DjcUiRawBindings267V1&,
 const ck3_1210::CoreSnapshotPrefix&,std::int32_t target,std::uint8_t cb,const DjcUiExpectedScene267V1&,
 std::uint64_t monotonic_deadline,const DjcUiRawObservation267V1&,std::uintptr_t actual_choice_row=0)noexcept;
} // namespace
