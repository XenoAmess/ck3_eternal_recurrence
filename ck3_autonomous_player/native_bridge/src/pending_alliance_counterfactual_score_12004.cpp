#include "xar_bridge/pending_alliance_counterfactual_score_12004.hpp"

#include <limits>

namespace xar::ck3_12004 {
namespace {
bool ValidCharacter(std::int32_t value) noexcept {
  return value != -1 && value != 0;
}

bool ValidFrame(const PendingAllianceScoreFrame12004 &frame) noexcept {
  return frame.native_revision != 0 && frame.public_revision != 0 &&
      frame.query_sequence != 0 && frame.pump_epoch != 0 &&
      frame.connection_generation != 0 && frame.game_pid != 0 &&
      frame.pending_full_id != -1 && ValidCharacter(frame.actor_full_id) &&
      ValidCharacter(frame.recipient_full_id) &&
      frame.actor_full_id != frame.recipient_full_id &&
      frame.recipient_full_id == frame.played_full_id &&
      frame.intermediary_full_id == -1 && frame.pending_identity != 0 &&
      frame.definition_identity != 0 &&
      frame.definition_key == "negotiate_alliance_interaction" &&
      frame.definition_hash == 2566946210U && frame.owning_thread &&
      frame.paused && frame.map_ready && frame.human_recipient &&
      frame.normal_recipient_channel;
}

bool Add(std::uintptr_t base, std::size_t offset,
         std::uintptr_t &out) noexcept {
  if (offset > (std::numeric_limits<std::uintptr_t>::max)() - base)
    return false;
  out = base + offset;
  return true;
}

template <typename T>
bool Read(const PendingAllianceScoreAccess12004 &access, std::uintptr_t base,
          std::size_t offset, T &out) noexcept {
  std::uintptr_t address = 0;
  return Add(base, offset, address) &&
      access.read_memory(access.context, address, &out, sizeof(out));
}

bool ContextMatches(const PendingAllianceScoreAccess12004 &access,
                    const PendingAllianceScoreFrame12004 &frame) noexcept {
  std::uintptr_t definition = 0;
  std::int32_t actor = -1, recipient = -1;
  return Read(access, frame.pending_identity, 0x18, definition) &&
      Read(access, frame.pending_identity, 0x2F0, actor) &&
      Read(access, frame.pending_identity, 0x2F4, recipient) &&
      definition == frame.definition_identity && actor == frame.actor_full_id &&
      recipient == frame.recipient_full_id;
}
} // namespace

PendingAllianceCounterfactualScore12004
ReadPendingAllianceCounterfactualScore12004(
    const InteractionContextBindings12004 &bindings,
    std::string_view actual_executable_sha256,
    const PendingAllianceScoreAccess12004 &access,
    const PendingAllianceScoreFrame12004 &expected) noexcept {
  PendingAllianceCounterfactualScore12004 out{};
  const auto fail = [&](std::string_view reason) {
    out.available = false;
    out.raw_q64.reset();
    out.unavailable_reason = reason;
    return out;
  };
  if (!access.read_frame || !access.read_memory || !access.invoke_guarded)
    return fail("pending_alliance_score_access_unavailable");
  std::uintptr_t entry = 0;
  if (actual_executable_sha256 != kExecutableSha256 || !bindings.enabled ||
      !bindings.context.enabled || !bindings.context.core.enabled ||
      bindings.module_base == 0 ||
      !Add(bindings.module_base, kInteractionRecipientAnswerScoreRva12004, entry) ||
      reinterpret_cast<std::uintptr_t>(bindings.read_character_interaction_answer_score) != entry ||
      bindings.context.recipient_answer_score !=
          bindings.read_character_interaction_answer_score)
    return fail("pending_alliance_score_exact_build_binding_unavailable");
  PendingAllianceScoreFrame12004 before{};
  if (!ValidFrame(expected) || !access.read_frame(access.context, before) ||
      before != expected || !ContextMatches(access, before))
    return fail("pending_alliance_score_current_context_unbound");
  out.counterfactual_player_as_ai = true;
  out.actual_ai_final =
      PendingAllianceActualAiFinal12004::not_applicable_human_responder;
  std::uintptr_t borrowed = 0;
  if (!Add(before.pending_identity, 0x18, borrowed))
    return fail("pending_alliance_score_context_address_overflow");
  std::int64_t raw = 0;
  std::int64_t *returned = nullptr;
  out.getter_called = true;
  if (!access.invoke_guarded(access.context,
          bindings.read_character_interaction_answer_score,
          reinterpret_cast<void *>(borrowed), &raw, returned))
    return fail("pending_alliance_score_guarded_getter_unavailable");
  out.returned_original_output = returned == &raw;
  if (!out.returned_original_output)
    return fail("pending_alliance_score_returned_pointer_mismatch");
  PendingAllianceScoreFrame12004 after{};
  if (!access.read_frame(access.context, after) || after != before ||
      !ContextMatches(access, after))
    return fail("pending_alliance_score_frame_changed_after_getter");
  out.same_frame_confirmed = true;
  out.raw_q64 = raw;
  out.available = true;
  return out;
}

} // namespace xar::ck3_12004
