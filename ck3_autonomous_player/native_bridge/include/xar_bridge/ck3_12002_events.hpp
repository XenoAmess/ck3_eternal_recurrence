#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/game_contract.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12002 {

inline constexpr std::size_t kEventManagerOffset = 0x34480;
inline constexpr std::size_t kEventDataOptionCountOffset = 0x1AC;
inline constexpr std::uintptr_t kGetCurrentEventRva = 0x29C57A0;
inline constexpr std::uintptr_t kSelectEventOptionPrimaryVtableRva = 0x47733D0;
inline constexpr std::uintptr_t kSelectEventOptionSecondaryVtableRva = 0x4773530;
inline constexpr std::uintptr_t kPendingInteractionStorageSlotRva = 0x5D1EC80;
inline constexpr std::uintptr_t kIsPendingInteractionForCharacterRva = 0x136D1B0;
inline constexpr std::uintptr_t kValidateReplyInteractionRva = 0x2968490;
inline constexpr std::uintptr_t kReplyInteractionPrimaryVtableRva = 0x448BC18;
inline constexpr std::uintptr_t kReplyInteractionSecondaryVtableRva = 0x448BBE8;

using GetCurrentEvent = void *(*)(void *event_manager);
using IsPendingInteractionForCharacter = bool (*)(void *pending, void *character);
using ValidateReplyInteraction = bool (*)(void *command);
using SubmitEventCommand = bool (*)(void *context, void *command,
                                   std::uint32_t channel_flags) noexcept;

// The queue callback owns cloning/transfer; the event reader owns no commands
// after the callback returns. Bind it to SubmitCommandCopyCompat at integration.
struct EventsBindings {
  CoreBindings core;
  std::uintptr_t image_base = 0;
  GetCurrentEvent get_current_event = nullptr;
  void **pending_interaction_storage_slot = nullptr;
  IsPendingInteractionForCharacter is_pending_for_character = nullptr;
  ValidateReplyInteraction validate_reply = nullptr;
  SubmitEventCommand submit_command = nullptr;
  void *submit_context = nullptr;
};

EventsBindings BindEventsImage(std::uintptr_t image_base,
                              std::string_view executable_sha256) noexcept;

struct alignas(8) EventCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 15> reserved{};
  std::uintptr_t secondary_vtable = 0;
  std::int32_t instance_id = -1;
  std::int32_t choice = -1;
};
static_assert(sizeof(EventCommand) == 0x28);
static_assert(offsetof(EventCommand, secondary_vtable) == 0x18);
static_assert(offsetof(EventCommand, instance_id) == 0x20);
static_assert(offsetof(EventCommand, choice) == 0x24);

// On false, neither absence flag may be treated as an observed absence.
// The complete snapshot's core/world fields are left to the owning adapter.
bool ReadEventsSnapshot(const EventsBindings &bindings,
                        game::Snapshot &output) noexcept;
void *ResolveEventsCharacter(const CoreBindings &bindings,
                             std::int32_t character_id) noexcept;
void *ResolveEventsPending(const EventsBindings &bindings,
                           std::int32_t pending_id) noexcept;
void *CurrentEvent(const EventsBindings &bindings) noexcept;

game::SelectEventOptionResult SubmitSelectEventOption(
    const EventsBindings &bindings, std::int32_t option_index) noexcept;
game::ReplyPendingInteractionResult SubmitReplyToPendingInteraction(
    const EventsBindings &bindings, game::PendingInteractionReply reply) noexcept;
game::AcknowledgePendingInteractionResult SubmitAcknowledgePendingInteraction(
    const EventsBindings &bindings, std::int32_t pending_id) noexcept;

} // namespace xar::ck3_12002
