#pragma once

#include "xar_bridge/ck3_12004_interaction_context.hpp"
#include "xar_bridge/ck3_12004_prisoner_named.hpp"
#include "xar_bridge/player_prisoner_ransom_private_v1.hpp"

namespace xar::ck3_12004 {

using PlayerPrisonerRansomQuoteV1 = ck3_11906::PlayerPrisonerRansomQuoteV1;
using PlayerPrisonerRansomQuoteFailureV1 =
    ck3_11906::PlayerPrisonerRansomQuoteFailureV1;

// Software DTOs and the quote algorithm are reused. Every image callback is
// supplied by the actual .4 interaction/named binders; no send command exists.
struct PrisonerRansomBindings12004 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  InteractionContextBindings12004 interaction{};
  PrisonerNamedBindings12004 named{};
};

PrisonerRansomBindings12004 BindPrisonerRansomImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// Ordinary gold/current_gold only. Actual redirected payer, final option,
// native CanSend, Q100000 score and native answer decide this readonly quote.
PlayerPrisonerRansomQuoteV1 ReadPlayerPrisonerRansomQuotePrivateV1(
    const PrisonerRansomBindings12004 &bindings, std::uintptr_t module_base,
    std::int32_t jailer_character_id,
    std::int32_t prisoner_character_id) noexcept;

} // namespace xar::ck3_12004
