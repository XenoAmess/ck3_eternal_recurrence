#pragma once

#include "xar_bridge/ck3_12004_snapshot_foundation.hpp"

namespace xar::ck3_12004 {

// The adapter owns the same callback/context bundle; its .4 binder and submit
// methods select actual .4 code and command tables explicitly.
using EventsBindings = ck3_12002::EventsBindings;
using EventCommand = ck3_12002::EventCommand;

inline constexpr std::uintptr_t kSelectEventOptionPrimaryVtableRva12004 = 0x47733E0;
inline constexpr std::uintptr_t kSelectEventOptionSecondaryVtableRva12004 = 0x4773540;

EventsBindings BindEventsImage(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;

game::SelectEventOptionResult SubmitSelectEventOption(
    const EventsBindings &bindings, std::int32_t option_index) noexcept;
game::ReplyPendingInteractionResult SubmitReplyToPendingInteraction(
    const EventsBindings &bindings, game::PendingInteractionReply reply) noexcept;
game::AcknowledgePendingInteractionResult SubmitAcknowledgePendingInteraction(
    const EventsBindings &bindings, std::int32_t pending_id) noexcept;

} // namespace xar::ck3_12004
