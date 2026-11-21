#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <array>
#include <string>
#include <vector>

namespace xar::ck3_121003::build26785313 {
struct RiteEditConfirmationBindings267V1 {bool exact_image_verified=false;std::uintptr_t image=0;};
struct BoundRiteEditConfirmation267V1 {
 std::uintptr_t manager=0,data=0,modal=0,root=0,gui_context=0,controller=0;
 std::array<std::byte,16> exact_dialog_header{};
 std::vector<std::uintptr_t> dialog_pointers;
 std::uint32_t source_rite_id=0xFFFFFFFFU,actor_id=0xFFFFFFFFU;
 bool native_can_accept=false,no_active_dialog=false;
 friend bool operator==(const BoundRiteEditConfirmation267V1&,const BoundRiteEditConfirmation267V1&)=default;
};
enum class RawRiteEditConfirmStatus267V1 {unavailable,call_returned,indeterminate};
struct RawRiteEditConfirmCall267V1 {RawRiteEditConfirmStatus267V1 status=RawRiteEditConfirmStatus267V1::unavailable;bool effect_entered=false;};
std::span<const ImagePin> RiteEditConfirmationImagePins267V1() noexcept;
bool VerifyRiteEditConfirmationImage267V1(std::uintptr_t) noexcept;
RiteEditConfirmationBindings267V1 BindRiteEditConfirmation267V1(std::uintptr_t,std::string_view sha) noexcept;
// Raw source/read primitive; no owner/token/once/publiccap is created. Root's
// independent named-root observation must bind actual basic_confirmation_popup
// root and visible/enabled before formal owner consumes an effect claim.
bool ReadBoundRiteEditConfirmation267V1(const ReadonlyBindings&,
 const RiteEditConfirmationBindings267V1&,std::uintptr_t expected_controller,
 std::uintptr_t expected_gui_context,BoundRiteEditConfirmation267V1&,std::string&) noexcept;
// Never accepts a caller Sample/can boolean as authority. Fresh registered-modal
// read and original Can are repeated; full Core/source/deadline/once admission
// remains the fixed executor's responsibility. Return is NOT applied/physical.
RawRiteEditConfirmCall267V1 CallRawRiteEditConfirm267V1(const ReadonlyBindings&,
 const RiteEditConfirmationBindings267V1&,std::uintptr_t expected_controller,
 std::uintptr_t expected_gui_context,std::uintptr_t expected_modal,std::uintptr_t expected_root) noexcept;
} // namespace xar::ck3_121003::build26785313
