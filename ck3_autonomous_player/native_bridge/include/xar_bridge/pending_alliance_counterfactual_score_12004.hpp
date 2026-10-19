#pragma once

#include "xar_bridge/ck3_12004_interaction_context.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

// Internal same-query identities only. Do not serialize or retain pointers.
struct PendingAllianceScoreFrame12004 {
  std::uint64_t native_revision = 0, public_revision = 0;
  std::uint64_t query_sequence = 0, pump_epoch = 0, connection_generation = 0;
  std::uint32_t game_pid = 0;
  std::int32_t date_raw = 0, pending_full_id = -1;
  std::int32_t actor_full_id = -1, recipient_full_id = -1;
  std::int32_t played_full_id = -1, intermediary_full_id = -1;
  std::uintptr_t pending_identity = 0, definition_identity = 0;
  std::string_view definition_key;
  std::uint32_t definition_hash = 0;
  bool owning_thread = false, paused = false, map_ready = false;
  bool human_recipient = false, normal_recipient_channel = false;
  bool operator==(const PendingAllianceScoreFrame12004 &) const = default;
};

enum class PendingAllianceActualAiFinal12004 {
  unavailable,
  not_applicable_human_responder,
};

struct PendingAllianceCounterfactualScore12004 {
  bool available = false, getter_called = false;
  bool returned_original_output = false, same_frame_confirmed = false;
  bool counterfactual_player_as_ai = false;
  std::optional<std::int64_t> raw_q64;
  std::int64_t scale = 100000;
  PendingAllianceActualAiFinal12004 actual_ai_final =
      PendingAllianceActualAiFinal12004::unavailable;
  std::string_view unavailable_reason;
};

struct PendingAllianceScoreAccess12004 {
  void *context = nullptr;
  bool (*read_frame)(void *, PendingAllianceScoreFrame12004 &) noexcept = nullptr;
  bool (*read_memory)(void *, std::uintptr_t, void *, std::size_t) noexcept = nullptr;
  // The owner supplies its guarded native invocation path. There is no direct
  // native entry call, constructor, finalize, destroy, reply or retry here.
  bool (*invoke_guarded)(void *, ck3_12002::MarriageReadInteractionAnswerScore,
                        void *, std::int64_t *, std::int64_t *&) noexcept = nullptr;
};

// One getter invocation at most. A missing result remains null, including zero
// initialized local output when the invoker fails or returns another pointer.
// This is player-as-AI guidance, never alliance utility or an actual AI final.
PendingAllianceCounterfactualScore12004
ReadPendingAllianceCounterfactualScore12004(
    const InteractionContextBindings12004 &bindings,
    std::string_view actual_executable_sha256,
    const PendingAllianceScoreAccess12004 &access,
    const PendingAllianceScoreFrame12004 &expected) noexcept;

} // namespace xar::ck3_12004
