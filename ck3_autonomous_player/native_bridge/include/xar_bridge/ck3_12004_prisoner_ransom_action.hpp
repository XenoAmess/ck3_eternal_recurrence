#pragma once

#include "xar_bridge/ck3_12004_prisoner_ransom.hpp"
#include "xar_bridge/ck3_12002_commands.hpp"

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kPrisonerRansomSendConstructorRva12004 =
    0x2968150;
inline constexpr std::uintptr_t kPrisonerRansomSendPrimaryVtableRva12004 =
    0x448BCF0;
inline constexpr std::uintptr_t kPrisonerRansomSendSecondaryVtableRva12004 =
    0x448BCC0;

using PlayerPrisonerRansomSubmitV1 = ck3_11906::PlayerPrisonerRansomSubmitV1;

// The command ownership algorithm is software-only. Actual .4 admission
// comes from the quote, central command and typed Send command proofs.
struct PrisonerRansomActionBindings12004 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  PrisonerRansomBindings12004 quote{};
  ck3_12002::CommandBindings commands{};
  ck3_12002::MarriageConstructSendInteractionCommand
      construct_send_character_interaction_command = nullptr;
  std::uintptr_t send_character_interaction_primary_vtable = 0;
  std::uintptr_t send_character_interaction_secondary_vtable = 0;
};

PrisonerRansomActionBindings12004 BindPrisonerRansomActionImage12004(
    std::uintptr_t module_base,
    std::string_view actual_executable_sha256) noexcept;

// Rereads the ordinary native quote at the application-main submit point.
// A submitted result is a queue ACK awaiting custody and gold observations.
PlayerPrisonerRansomSubmitV1 SubmitPlayerPrisonerRansomPrivateV1(
    const PrisonerRansomActionBindings12004 &bindings,
    std::uintptr_t module_base,
    const PlayerPrisonerRansomQuoteV1 &observed_quote,
    std::uint64_t expected_native_revision,
    std::int64_t expected_date_raw) noexcept;

} // namespace xar::ck3_12004
