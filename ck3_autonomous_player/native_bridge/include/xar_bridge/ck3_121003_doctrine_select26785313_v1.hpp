#pragma once
#include "xar_bridge/ck3_121003_doctrine_key26785313_v1.hpp"
#include <array>

namespace xar::ck3_121003::build26785313 {
inline constexpr std::uintptr_t kShouldDisplayNativeRva267V1=0xF78F00;
inline constexpr std::uintptr_t kCanPickNativeRva267V1=0xF78F10;
inline constexpr std::uintptr_t kSelectDoctrineNativeRva267V1=0x16B94E0;
inline constexpr std::uintptr_t kHasDoctrineSelectedNativeRva267V1=0x16BB5D0;
struct DoctrineSelectBindings267V1 {
 bool exact_image_verified=false;
 std::uintptr_t image=0;
 // Literal current targets, never caller-supplied callback functions.
 std::uintptr_t should_display=0,can_pick=0,select_doctrine=0,has_selected=0;
};
enum class RawDoctrineObservationStatus267V1 { unavailable,observed };
struct RawDoctrinePredicateObservation267V1 {
 RawDoctrineObservationStatus267V1 status=RawDoctrineObservationStatus267V1::unavailable;
 bool should_display=false,can_pick=false;
 std::uintptr_t controller=0,item=0,doctrine=0;
 std::array<std::byte,0x48> exact_item{};
 DoctrineInternalKey267V1 exact_doctrine;
};
struct RawHasDoctrineSelected267V1 {
 RawDoctrineObservationStatus267V1 status=RawDoctrineObservationStatus267V1::unavailable;
 bool has_selected=false;
 DoctrineInternalKey267V1 exact_doctrine;
};
enum class RawDoctrineSelectDispatch267V1 { unavailable,call_returned,indeterminate };
struct RawDoctrineSelectCall267V1 {
 RawDoctrineSelectDispatch267V1 status=RawDoctrineSelectDispatch267V1::unavailable;
 bool effect_attempted=false;
};
std::span<const ImagePin> DoctrineSelectImagePins267V1() noexcept;
bool VerifyDoctrineSelectImage267V1(std::uintptr_t) noexcept;
DoctrineSelectBindings267V1 BindDoctrineSelectImage267V1(std::uintptr_t,std::string_view sha) noexcept;
// RAW/PRIVATE ABI primitives only: no public capability, owner proof, query
// token, SourceRite admission, knowledge/perk input, or action claim is created.
// Future fixed Native owner must compose current Core/TLS/paused living/source,
// typed category/item/key and TopScope, real knownTRUE, dual deadlines, stable
// double reads, and its retained once/UNKNOWN claim BEFORE the call primitive.
RawDoctrinePredicateObservation267V1 ReadRawDoctrinePredicates267V1(
    const ReadonlyBindings&,const DoctrineSelectBindings267V1&,
    std::uintptr_t actual_controller,std::uintptr_t actual_typed_item) noexcept;
RawHasDoctrineSelected267V1 ReadRawHasDoctrineSelected267V1(
    const ReadonlyBindings&,const DoctrineSelectBindings267V1&,
    std::uintptr_t actual_controller,std::uintptr_t typed_doctrine) noexcept;
// void native effect: call_returned is not proof of selection/application.
// No eligibility booleans are accepted or synthesized by this interface.
RawDoctrineSelectCall267V1 CallRawSelectDoctrine267V1(
    const ReadonlyBindings&,const DoctrineSelectBindings267V1&,
    std::uintptr_t actual_controller,std::uintptr_t actual_typed_item) noexcept;
} // namespace xar::ck3_121003::build26785313
