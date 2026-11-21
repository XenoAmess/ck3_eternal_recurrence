#pragma once
#include <cstddef>
#include <cstdint>

namespace xar::current267_succession_source_v1 {
// SOURCE_ONLY for 1.21.0.3/build26785313/SHA859f. No compiled or live qualification.
inline constexpr char kExecutableSha256[] = "859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28";
inline constexpr std::uintptr_t kPrimaryVtable=0x4BA35F0, kSecondaryVtable=0x4BA36C0;
inline constexpr std::uintptr_t kPrimaryCol=0x5257180, kSecondaryCol=0x52571A8, kTypeDescriptor=0x615F200;
inline constexpr std::uintptr_t kTypedClose=0x1100FE0, kCloseDispatch=0x1107E98, kClose=0x1164E80;
inline constexpr std::uintptr_t kIsOpen=0x11650F0, kIsSuccession=0x11629D0;
inline constexpr std::uintptr_t kGetContinueAsCharacter=0x1165230, kGetPlayerHeir=0x11651D0, kGetDeadCharacter=0x1144620;
inline constexpr std::uintptr_t kCharacterDbSlot=0x68A8928, kNullCharacterSlot=0x68A8930;
inline constexpr std::uintptr_t kGameStateSlot=0x68B2090, kPlayerIdSlot=0x5D50448, kOpaqueCloseTokenSlot=0x69DAF8C;
inline constexpr std::uintptr_t kIsPausedBySuccession=0xBC4D80, kHasOpenSuccession=0xBC4DF0;
inline constexpr std::uintptr_t kCommandManager=0x69DABA0, kQueue=0x3E17C00, kCloseCommandExecutor=0x2D7B3E0;
inline constexpr std::size_t kHandlerController=0x260, kExcludedLineageController=0x268;
inline constexpr std::size_t kControllerBytes=0x350, kRoot=0x60, kGuiContext=0x68, kJomini=0x98, kHandler=0xA0;
inline constexpr std::size_t kDeadCharacterId=0xC8, kPlayerHeirId=0xD0, kSuccessionKind=0x1BC;
inline constexpr std::size_t kAlternateContinueId=0x2FC, kAlternateMode=0x300, kAnimationWidget=0x308;
inline constexpr std::size_t kOpenVslot=0x38, kCloseVslot=0x88;
inline constexpr std::size_t kDbRows=0x20, kDbCount=0x2C, kDbRowStride=0x10, kDbRowCharacter=8, kCharacterGenerationId=0x18;
inline constexpr std::size_t kGameData=0xA0, kPlayerRows=0x26FB0, kPlayerRowCount=0x26FBC;
inline constexpr std::size_t kRowCharacterId=0xB0, kRowOpaqueToken=0xD8, kRowActive=0x260;
using CharacterGetter = const void* (__fastcall*)(const void* controller);
using ControllerPredicate = bool (__fastcall*)(void* controller);
using ControllerClose = void (__fastcall*)(void* controller);
using PausedPredicate = bool (__fastcall*)();
using CharacterHasOpenPredicate = bool (__fastcall*)(const void* character);
// The native owner must acquire the exact resident handler/controller/root and current lifecycle.
// Never accept caller-supplied controller/boolean/character pointers as owner authorization.
// No living-only Core guard is relaxed by these declarations. A death-aware fixed executor is still absent.
// Close returns void; the typed AL=1 is merely handled, never inherited/APPLIED/SAVE proof.
struct ObservationInputsOnly {
  std::uintptr_t logical_owner=0, gfx=0, handler=0, controller=0, root=0, context=0;
  std::int32_t predecessor_id=-1, expected_heir_id=-1, observed_dead_id=-1, observed_continue_id=-1;
  std::int32_t actual_player_id=-1, opaque_close_token=-1, kind=-1;
  std::uint8_t alternate_mode=0, active_row=0;
};
} // namespace xar::current267_succession_source_v1
