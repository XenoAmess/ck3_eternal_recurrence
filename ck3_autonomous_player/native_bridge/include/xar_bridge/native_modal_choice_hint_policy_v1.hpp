#pragma once

#include "main_thread_query_mailbox_v1.hpp"

#include <cstdint>

namespace xar::mandatory_choice_v1 {

// A visible modal can block progress while CK3's pause flag remains false.
// Only the verified application GUI owner may sample the receiver.
inline bool OwnerModalHintObservationAllowedV1(
    const ck3_11906::MainThreadExecutionStampV1 &stamp,
    std::uint32_t current_thread_id) noexcept {
  return stamp.thread_id == current_thread_id &&
      stamp.tls_initialized == 1 && stamp.tls_main_thread_marker == 1 &&
      stamp.tls_context && stamp.game_state && stamp.jomini_state;
}

// An exclusive GUI receiver can be actionable while the simulation pause bit
// is false. This is deliberately limited to the mandatory-choice executor;
// all unrelated native commands retain their paused-owner requirement.
inline bool OwnerModalChoiceCommandAllowedV1(
    const ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const ck3_11906::MainThreadExecutionStampV1 &stamp,
    std::uint32_t executing_thread_id) noexcept {
  return stamp.pump_epoch != 0 && stamp.thread_id != 0 &&
      executing_thread_id == stamp.thread_id &&
      mailbox.owner_thread_id.load(std::memory_order_acquire) == stamp.thread_id &&
      stamp.tls_initialized_flag_address != 0 && stamp.tls_initialized == 1 &&
      stamp.tls_context != 0 && stamp.tls_main_thread_marker == 1 &&
      stamp.jomini_state != 0 && stamp.game_state != 0 &&
      mailbox.owner_verified_pump_epochs.load(std::memory_order_acquire) >=
          ck3_11906::kMainThreadQueryMinimumOwnerVerifiedPumpEpochs;
}

inline bool SemanticModalHintPublicationAllowedV1(
    bool map_ready, bool exact_12004_build) noexcept {
  return map_ready && exact_12004_build;
}
} // namespace xar::mandatory_choice_v1
