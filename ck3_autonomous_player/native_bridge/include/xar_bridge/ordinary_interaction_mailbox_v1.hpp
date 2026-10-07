#pragma once

#include "xar_bridge/ordinary_character_interaction_v1.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"

namespace xar::ck3_12003 {

struct OrdinaryInteractionMailboxProofV1 {
  bool source_code_pins_verified = false;
  bool owner_thread_verified = false;
  bool tls_verified = false;
  bool frame_verified = false;
  std::uint32_t owner_thread_id = 0;
  std::uint64_t owner_pump_epoch = 0;
};

struct OrdinaryInteractionMailboxContextV1 {
  ck3_12002::QueryMailboxEnvelope envelope{};
  std::uintptr_t image_base = 0;
  OrdinaryInteractionRequestV1 request{};
  bool initiate = false;
  ordinary_interaction::Observation observation{};
  ordinary_interaction::SendObservation initiation{};
  OrdinaryInteractionMailboxProofV1 proof{};
  bool completed = false;
};

bool OrdinaryInteractionCodePinsMatchV1(std::uintptr_t image_base) noexcept;
bool OrdinaryInteractionCodePinsMatchV1(std::uintptr_t image_base,
                                      std::string_view executable_sha256) noexcept;
bool OrdinaryInteractionControlFrameMatchesV1(
    const game::Snapshot &before, const game::Snapshot &after) noexcept;
bool OrdinaryInteractionReadyV1(
    const ordinary_interaction::Observation &observation,
    const OrdinaryInteractionMailboxProofV1 &proof,
    const game::Snapshot &frame) noexcept;
bool ExecuteOrdinaryInteractionMailboxV1(
    void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
std::string SerializeOrdinaryInteractionV1(
    const OrdinaryInteractionMailboxContextV1 &query,
    std::uint64_t query_sequence);

} // namespace xar::ck3_12003
