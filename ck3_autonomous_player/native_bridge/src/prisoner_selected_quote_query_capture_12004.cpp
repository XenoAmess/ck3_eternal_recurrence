#include "xar_bridge/prisoner_selected_quote_query_capture_12004.hpp"

namespace xar::ck3_12004 {
namespace {
using ExistingAnswer = ck3_11906::EvaluateCharacterInteractionAnswer;
using ExistingCost = ck3_12002::MarriageEvaluateInteractionCost;
using ExistingTrigger = ck3_12002::MarriageEvaluateInteractionTrigger;
struct Capture {
  PrisonerQuoteSourceFrame12004 seed;
  PrisonerQuoteReadOnlyAccess12004 access;
  PrisonerSelectedQuoteSource12004 *source = nullptr;
  PrisonerExistingScoreQuery12004 score = nullptr;
  ExistingAnswer answer = nullptr;
  ExistingCost cost = nullptr;
  ExistingTrigger trigger = nullptr;
  bool ordinary = false;
  bool copy_failed = false;
};
thread_local Capture *active = nullptr;
struct Scope {
  Capture *previous;
  explicit Scope(Capture &c) noexcept : previous(active) { active = &c; }
  ~Scope() { active = previous; }
};
PrisonerQuoteSourceSample12004 *Sample(Capture &c, std::uintptr_t context, bool new_sample) noexcept {
  try {
    if (!c.source) return nullptr;
    if (!new_sample && !c.source->samples.empty() &&
        c.source->samples.back().frame.interaction_context_identity == context)
      return &c.source->samples.back();
    if (c.source->samples.size() >= 4) {
      c.source->unavailable_reason = "selected_quote_source_sample_bound_exceeded"; return nullptr;
    }
    c.source->samples.push_back(CopyPrisonerQuoteSourceSample12004(c.access, c.seed, context, c.ordinary));
    c.source->samples.back().copied_at_existing_query_call = true;
    return &c.source->samples.back();
  } catch (...) { c.copy_failed = true; return nullptr; }
}
std::int64_t *Score(void *context, std::int64_t *output) {
  auto *const c = active;
  if (!c || !c->score) return nullptr;
  auto *const s = Sample(*c, reinterpret_cast<std::uintptr_t>(context), false);
  if (!s) return c->score(context, output);
  return ObservePrisonerExistingScoreQuery12004(c->access, *s, c->score, context, output);
}
std::uint8_t Answer(void *context, std::uint8_t a2, std::uint8_t a3, void *a4, void *a5) {
  auto *const c = active;
  if (!c || !c->answer) return 3;
  const auto result = c->answer(context, a2, a3, a4, a5);
  if (auto *const s = Sample(*c, reinterpret_cast<std::uintptr_t>(context), false);
      s && a2 == 1 && a3 == 1 && !a4 && !a5) s->native_answer_raw_u8 = result;
  return result;
}
void Costs(const void *block, const void *scope, std::int64_t *output) {
  auto *const c = active;
  if (!c || !c->cost) return;
  const auto scope_identity = reinterpret_cast<std::uintptr_t>(scope);
  auto *const s = scope_identity >= 8 ? Sample(*c, scope_identity - 8, true) : nullptr;
  if (s) ObservePrisonerExistingCostQuery12004(c->access, *s, c->cost, block, scope, output);
  else c->cost(block, scope, output);
}
bool Trigger(void *trigger, const void *scope) {
  auto *const c = active;
  if (!c || !c->trigger) return false;
  const auto result = c->trigger(trigger, scope);
  const auto scope_identity = reinterpret_cast<std::uintptr_t>(scope);
  auto *const s = scope_identity >= 8 ? Sample(*c, scope_identity - 8, false) : nullptr;
  if (s && s->auto_accept_trigger_identity == std::optional<std::uintptr_t>{reinterpret_cast<std::uintptr_t>(trigger)})
    s->native_auto_accept = result;
  return result;
}
void Finish(Capture &c, bool complete) noexcept {
  try {
    c.source->selected_query_completed = complete;
    if (c.copy_failed) c.source->unavailable_reason = "selected_quote_source_copy_failed";
    if (complete && c.source->unavailable_reason == "not_evaluated") c.source->unavailable_reason.clear();
    else if (c.source->unavailable_reason == "not_evaluated") c.source->unavailable_reason = "selected_quote_unavailable";
    for (auto &s : c.source->samples) FinishPrisonerQuoteSourceSample12004(s, complete);
  } catch (...) { c.source->selected_query_completed = false;
    c.source->unavailable_reason = "selected_quote_source_finalize_failed"; }
}
}
std::int64_t *ObservePrisonerExistingScoreQuery12004(
    const PrisonerQuoteReadOnlyAccess12004 &access, PrisonerQuoteSourceSample12004 &sample,
    PrisonerExistingScoreQuery12004 original, void *context, std::int64_t *output) noexcept {
  if (!original) return nullptr;
  sample.copied_at_existing_query_call = true;
  try { CopyPrisonerQuoteRecipientScoreSource12004(access, sample); } catch (...) { sample.recipient_score.reset(); }
  // Copying failed inputs never suppresses or repeats the original query.
  auto *const returned = original(context, output);
  if (sample.recipient_score) {
    auto &score = *sample.recipient_score; score.native_getter_called = true;
    score.native_getter_returned_output_pointer = returned == output && output != nullptr;
    if (score.native_getter_returned_output_pointer) {
      std::int64_t copied = 0;
      if (access.read_memory && access.read_memory(access.context, output, &copied, sizeof(copied)))
        score.native_final_output_q64 = copied;
    }
  }
  return returned;
}
void ObservePrisonerExistingCostQuery12004(const PrisonerQuoteReadOnlyAccess12004 &access,
    PrisonerQuoteSourceSample12004 &sample, PrisonerExistingCostQuery12004 original,
    const void *block, const void *scope, std::int64_t *output) noexcept {
  if (!original) return;
  sample.copied_at_existing_query_call = true;
  try {
    if (sample.frame.original_scope_identity == reinterpret_cast<std::uintptr_t>(scope)) {
      CopyPrisonerQuoteCostSource12004(access, sample, reinterpret_cast<std::uintptr_t>(block), output);
      CopyPrisonerQuoteAutoAcceptSource12004(access, sample);
    }
  } catch (...) { sample.actor_on_send_costs.reset(); }
  original(block, scope, output);
  if (sample.actor_on_send_costs) {
    auto &out = *sample.actor_on_send_costs; out.native_getter_called = true;
    std::array<std::int64_t, 10> copied{};
    if (output && access.read_memory && access.read_memory(access.context, output, copied.data(), sizeof(copied)))
      out.native_final_q64 = copied;
  }
}
PlayerPrisonerRansomQuoteV1 ReadPlayerPrisonerRansomQuoteSourcePrivateV1(
    const PrisonerRansomBindings12004 &bindings, std::uintptr_t module, std::int32_t jailer,
    std::int32_t prisoner, std::uint32_t ordinal, const PrisonerQuoteSourceFrame12004 &seed,
    const PrisonerQuoteReadOnlyAccess12004 &access, PrisonerSelectedQuoteSource12004 &source) noexcept {
  source = {}; source.source_ordinal = ordinal; source.quote_kind = "ordinary_ransom";
  Capture c{seed, access, &source, bindings.interaction.read_character_interaction_answer_score,
      bindings.interaction.evaluate_answer, nullptr, nullptr, true};
  auto copied = bindings;
  if (c.score) copied.interaction.read_character_interaction_answer_score = &Score;
  if (c.answer) copied.interaction.evaluate_answer = &Answer;
  Scope scope(c);
  const auto quote = ReadPlayerPrisonerRansomQuotePrivateV1(copied, module, jailer, prisoner);
  Finish(c, quote.available); return quote;
}
bool ReadPrisonerNegotiatedCollectionRowSource12004(
    const PrisonerNegotiatedBindings12004 &bindings, const PrisonerReleasePreviewAccess12004 &query_access,
    const bridge::PlayerPrisonerCollectionSnapshotV1 &collection, std::uint32_t ordinal, std::uint32_t mask,
    std::array<PrisonerNegotiatedPreview12004, bridge::kPlayerPrisonerMaximumRowsV1> &previews,
    const PrisonerQuoteSourceFrame12004 &seed, const PrisonerQuoteReadOnlyAccess12004 &access,
    PrisonerSelectedQuoteSource12004 &source) noexcept {
  source = {}; source.source_ordinal = ordinal; source.quote_kind = "negotiated_preview";
  const auto &original = bindings.release.gift.interaction;
  Capture c{seed, access, &source, original.recipient_answer_score, bindings.evaluate_answer,
      original.evaluate_cost, original.evaluate_trigger, false};
  auto copied = bindings;
  auto &callbacks = copied.release.gift.interaction;
  if (c.score) callbacks.recipient_answer_score = &Score;
  if (c.answer) copied.evaluate_answer = &Answer;
  if (c.cost) callbacks.evaluate_cost = &Costs;
  if (c.trigger) callbacks.evaluate_trigger = &Trigger;
  Scope scope(c);
  const bool ok = ReadPrisonerNegotiatedCollectionRow12004(copied, query_access, collection, ordinal, mask, previews);
  Finish(c, ok && ordinal < previews.size() && previews[ordinal].observation.available); return ok;
}
} // namespace xar::ck3_12004
