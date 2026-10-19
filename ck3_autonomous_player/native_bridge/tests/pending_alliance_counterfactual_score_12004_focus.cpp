// No main. Parent may add this focus to its existing bounded offline runner.
#include "../src/pending_alliance_counterfactual_score_12004.cpp"

#include <cstring>
#include <stdexcept>

namespace {
using namespace xar::ck3_12004;
struct Scene {
  PendingAllianceScoreFrame12004 frame{};
  std::int64_t value = 125000, foreign_output = 0;
  int calls = 0, frame_reads = 0;
  bool memory_fail = false, invoke_fail = false;
  bool foreign_return = false, change_after = false;
};
void Require(bool value) {
  if (!value) throw std::runtime_error("pending alliance score focus failed");
}
bool Frame(void *opaque, PendingAllianceScoreFrame12004 &out) noexcept {
  auto &scene = *static_cast<Scene *>(opaque);
  out = scene.frame;
  ++scene.frame_reads;
  if (scene.change_after && scene.frame_reads > 1) ++out.native_revision;
  return true;
}
bool Memory(void *opaque, std::uintptr_t address, void *out,
            std::size_t count) noexcept {
  const auto &s = *static_cast<Scene *>(opaque);
  if (s.memory_fail) return false;
  if (address == s.frame.pending_identity + 0x18 && count == sizeof(std::uintptr_t)) {
    std::memcpy(out, &s.frame.definition_identity, count); return true;
  }
  if (address == s.frame.pending_identity + 0x2F0 && count == sizeof(std::int32_t)) {
    std::memcpy(out, &s.frame.actor_full_id, count); return true;
  }
  if (address == s.frame.pending_identity + 0x2F4 && count == sizeof(std::int32_t)) {
    std::memcpy(out, &s.frame.recipient_full_id, count); return true;
  }
  return false;
}
bool Invoke(void *opaque, xar::ck3_12002::MarriageReadInteractionAnswerScore,
            void *borrowed, std::int64_t *out,
            std::int64_t *&returned) noexcept {
  auto &s = *static_cast<Scene *>(opaque);
  ++s.calls;
  if (reinterpret_cast<std::uintptr_t>(borrowed) != s.frame.pending_identity + 0x18)
    return false;
  *out = s.value;
  returned = s.foreign_return ? &s.foreign_output : out;
  return !s.invoke_fail;
}
Scene NewScene() {
  Scene s{};
  auto &f = s.frame;
  f.native_revision = 49; f.public_revision = 50;
  f.query_sequence = 77; f.pump_epoch = 3; f.connection_generation = 1;
  f.game_pid = 100; f.date_raw = 53146704; f.pending_full_id = 150995095;
  f.actor_full_id = 36445; f.recipient_full_id = 31254; f.played_full_id = 31254;
  f.pending_identity = 0x1000; f.definition_identity = 0x4000;
  f.definition_key = "negotiate_alliance_interaction";
  f.definition_hash = 2566946210U; f.owning_thread = true;
  f.paused = true; f.map_ready = true; f.human_recipient = true;
  f.normal_recipient_channel = true;
  return s;
}
InteractionContextBindings12004 Bindings() {
  InteractionContextBindings12004 b{};
  b.module_base = 0x10000000;
  b.enabled = true; b.context.enabled = true; b.context.core.enabled = true;
  b.read_character_interaction_answer_score =
      reinterpret_cast<xar::ck3_12002::MarriageReadInteractionAnswerScore>(
          b.module_base + kInteractionRecipientAnswerScoreRva12004);
  b.context.recipient_answer_score = b.read_character_interaction_answer_score;
  return b;
}
auto ReadScore(Scene &s, const InteractionContextBindings12004 &b,
               std::string_view sha = kExecutableSha256) {
  PendingAllianceScoreAccess12004 a{};
  a.context = &s; a.read_frame = Frame; a.read_memory = Memory; a.invoke_guarded = Invoke;
  return ReadPendingAllianceCounterfactualScore12004(b, sha, a, s.frame);
}
} // namespace

void RunPendingAllianceCounterfactualScoreFocus12004() {
  const auto b = Bindings();
  for (const std::int64_t raw : {125000LL, -500000LL, 0LL, 3600000000LL}) {
    auto s = NewScene(); s.value = raw;
    const auto out = ReadScore(s, b);
    Require(out.available && out.raw_q64 == raw && out.scale == 100000);
    Require(out.counterfactual_player_as_ai && out.same_frame_confirmed &&
        out.returned_original_output && s.calls == 1 && s.frame_reads == 2);
    Require(out.actual_ai_final == PendingAllianceActualAiFinal12004::not_applicable_human_responder);
  }
  auto signed_id = NewScene(); signed_id.frame.pending_full_id = -721420283;
  Require(ReadScore(signed_id, b).available);
  auto wrong_sha = NewScene();
  Require(!ReadScore(wrong_sha, b, "other-build").raw_q64 && wrong_sha.calls == 0);
  auto wrong_entry = NewScene(); auto bad = b; bad.module_base += 1;
  Require(!ReadScore(wrong_entry, bad).raw_q64 && wrong_entry.calls == 0);
  auto wrong_human = NewScene(); wrong_human.frame.human_recipient = false;
  const auto not_human = ReadScore(wrong_human, b);
  Require(!not_human.raw_q64 && wrong_human.calls == 0 &&
      not_human.actual_ai_final == PendingAllianceActualAiFinal12004::unavailable);
  auto memory_fail = NewScene(); memory_fail.memory_fail = true;
  Require(!ReadScore(memory_fail, b).raw_q64 && memory_fail.calls == 0);
  auto call_fail = NewScene(); call_fail.invoke_fail = true;
  Require(!ReadScore(call_fail, b).raw_q64 && call_fail.calls == 1);
  auto foreign = NewScene(); foreign.foreign_return = true;
  Require(!ReadScore(foreign, b).raw_q64 && foreign.calls == 1);
  auto moved = NewScene(); moved.change_after = true;
  const auto stale = ReadScore(moved, b);
  Require(!stale.raw_q64 && stale.getter_called && !stale.same_frame_confirmed && moved.calls == 1);
}
