// Real owner/wire with explicit self-owned DATA dependencies. No Native/live P.
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_CREATE_V1) && !XAR_CK3_ENABLE_121003_26785313_RITE_CREATE_V1
#error Enabled owner test must not be compiled with feature OFF.
#endif
#ifndef XAR_CK3_ENABLE_121003_26785313_RITE_CREATE_V1
#define XAR_CK3_ENABLE_121003_26785313_RITE_CREATE_V1 1
#endif
#include "rite_create_owner_nogame_fixture.hpp"

namespace {
using namespace rite_owner_fixture;

void CompleteOriginalCreatePendingConfirmationAndAccept() {
  state.Reset(); Session session; auto mailbox = NewMailbox();
  auto draft = QueryDraft(session, mailbox.get());
  const auto first_source = draft.result.source;
  auto create = Create(session, mailbox.get(), draft);
  Require(create.result.source == first_source && state.calls == 1 && state.entered_calls == 1,
      "Create changed immutable beforeSource or dispatched twice");
  const auto create_claim = create.result.claim_sequence;
  state.modal_pending = true;
  auto waiting = QueryConfirmation(session, mailbox.get(), draft);
  Require(waiting.result.status == Status::confirmation_pending && waiting.result.cleanup_known &&
      !waiting.result.effect_attempted && !waiting.result.native_returned && !waiting.result.claim_sequence &&
      waiting.result.provider_generation == draft.result.provider_generation &&
      waiting.result.query_sequence == draft.result.query_sequence && state.calls == 1,
      "clean correlated pending minted a lease or another callback");
  NoSource(waiting);
  state.modal_pending = false;
  auto ready = QueryConfirmation(session, mailbox.get(), draft);
  Require(ready.result.status == Status::available && ready.result.source &&
      ready.result.source->phase == Phase::confirmation &&
      ready.result.source->confirmation->original_create_bound &&
      ready.result.query_sequence > draft.result.query_sequence &&
      ready.result.provider_generation == draft.result.provider_generation &&
      ready.request.deadline_unix_ms == draft.request.deadline_unix_ms &&
      state.window_reads == 1 && state.window_binds == 1 && state.calls == 1,
      "fresh final query did not retain original Create association/deadline");
  const auto final_source = ready.result.source;
  auto accept = FromQuery(session, mailbox.get(), Action::accept_confirmation, ready); Run(accept);
  Require(accept.result.status == Status::confirmation_dispatched && accept.result.source == final_source &&
      accept.result.effect_attempted && accept.result.native_returned && !accept.result.native_handled &&
      accept.result.cleanup_known && accept.result.claim_sequence > create_claim && state.calls == 2 && state.entered_calls == 2,
      "Accept did not return its own immutable confirmation Source/void result");
  Require(Has(Wire(create), "\"status\":\"create_dispatched\"") &&
      Has(Wire(accept), "\"status\":\"confirmation_dispatched\""), "actual dispatch serializer lost status");
  const auto observations = state.observations;
  Run(create); Run(accept);
  Require(create.result.status == Status::claim_consumed && create.result.claim_sequence == create_claim &&
      accept.result.status == Status::claim_consumed && state.calls == 2 && state.observations == observations,
      "same original effect ID replayed an observation or callback");
  auto post = QueryDraft(session, mailbox.get());
  Require(post.result.query_sequence > ready.result.query_sequence && state.calls == 2,
      "known final dispatch did not clear pending without repeating an effect");
}

void ConnectionRiteCoreAndOriginalDeadlineMustMatch() {
  state.Reset(); Session session; auto mailbox = NewMailbox();
  auto draft = QueryDraft(session, mailbox.get());
  for (unsigned mismatch = 0; mismatch != 7; ++mismatch) {
    auto create = FromQuery(session, mailbox.get(), Action::create, draft);
    switch (mismatch) {
      case 0: ++create.connection_generation; break;
      case 1: ++create.request.expected_source_rite_id; break;
      case 2: create.request.expected.clock.date_raw += 24; break;
      case 3: ++create.request.deadline_unix_ms; break;
      case 4: --create.request.deadline_unix_ms; break;
      case 5: ++create.request.provider_generation; break;
      case 6: ++create.request.query_sequence; break;
    }
    const auto observations = state.observations; Run(create);
    Require(create.result.status == Status::stale_source && !create.result.claim_sequence &&
      !create.result.effect_attempted && state.observations == observations && !state.calls,
      "mismatched connection/Rite/Core/original lease/deadline reached Raw or claim");
    NoSource(create);
  }
  auto create = Create(session, mailbox.get(), draft);
  for (unsigned mismatch = 0; mismatch != 5; ++mismatch) {
    auto query = FromQuery(session, mailbox.get(), Action::query_confirmation, draft);
    if (mismatch == 0) ++query.connection_generation;
    if (mismatch == 1) ++query.request.expected_source_rite_id;
    if (mismatch == 2) query.request.expected.clock.date_raw += 24;
    if (mismatch == 3) ++query.request.deadline_unix_ms;
    if (mismatch == 4) --query.request.deadline_unix_ms;
    const auto observations = state.observations; Run(query);
    Require(query.result.status == Status::stale_source && state.observations == observations && state.calls == 1,
      "original pending was rebound to another connection/Rite/Core/deadline");
    NoSource(query);
  }
  Require(create.request.deadline_unix_ms == draft.request.deadline_unix_ms,
      "test itself extended the original deadline");
}

void OldEditOrNewSessionCannotBorrowOriginalCreateProof() {
  state.Reset(); Session session; Session foreign; auto mailbox = NewMailbox();
  // Caller-positive leases or an unrelated edit workflow are not a Create occurrence.
  for (auto action : {Action::query_confirmation, Action::accept_confirmation}) {
    auto forged = Request(foreign, mailbox.get(), action); Run(forged);
    Require(forged.result.status == (action == Action::query_confirmation ? Status::prerequisite_rejected : Status::stale_source)
      && !state.observations && !state.calls, "an unbound/old-edit lease created pending authority");
    NoSource(forged);
  }
  auto draft = QueryDraft(session, mailbox.get());
  auto create = Create(session, mailbox.get(), draft);
  const auto observations = state.observations;
  auto stolen = FromQuery(foreign, mailbox.get(), Action::query_confirmation, draft); Run(stolen);
  Require(stolen.result.status == Status::prerequisite_rejected && state.observations == observations && state.calls == 1,
      "new receiver/session imported original pending solely from matching DATA");
  auto wrong_connection = FromQuery(session, mailbox.get(), Action::query_confirmation, draft);
  ++wrong_connection.connection_generation; Run(wrong_connection);
  Require(wrong_connection.result.status == Status::stale_source && state.calls == 1,
      "same process with different connection borrowed pending");
  (void)create;
}

void RawStalenessBeforeClaimDoesNotSpendOrRewriteLease() {
  state.Reset(); Session session; auto mailbox = NewMailbox();
  auto draft = QueryDraft(session, mailbox.get());
  state.change_raw = true;
  auto stale = FromQuery(session, mailbox.get(), Action::create, draft); Run(stale);
  Require(stale.result.status == Status::stale_source && !stale.result.claim_sequence &&
      !stale.result.effect_attempted && !state.calls, "changed complete Raw was called or spent claim before admission");
  NoSource(stale);
  state.change_raw = false;
  // A different explicit request against the still-identical private lease can
  // proceed after known preclaim rejection. This is NoGame state coverage, not
  // permission to retry any actual UNKNOWN/runtime command.
  auto fresh_id = Create(session, mailbox.get(), draft);
  Require(fresh_id.result.claim_sequence == 1 && fresh_id.result.source == draft.result.source,
      "known preclaim failure consumed/rewrote the original private source");
}

void CalleeBeforeEffectRefusalRetainsSpentClaimWithZeroEffect() {
  state.Reset(); Session session; auto mailbox = NewMailbox();
  auto draft = QueryDraft(session, mailbox.get());
  state.call_status = RiteCreateCallStatus267V1::unavailable; state.call_entered = false;
  auto refused = FromQuery(session, mailbox.get(), Action::create, draft); Run(refused);
  Require(refused.result.status == Status::stale_source && refused.result.claim_sequence == 1 &&
      !refused.result.effect_attempted && !refused.result.native_returned && refused.result.cleanup_known &&
      state.calls == 1 && !state.entered_calls, "pre-effect callee refusal lost already-spent claim or invented effect");
  NoSource(refused);
  const auto observations = state.observations;
  Run(refused);
  Require(refused.result.status == Status::claim_consumed && refused.result.claim_sequence == 1 &&
      state.calls == 1 && state.observations == observations, "spent original ID retried callee");
  auto another_id = FromQuery(session, mailbox.get(), Action::create, draft); Run(another_id);
  Require(another_id.result.status == Status::claim_consumed && state.calls == 1,
      "new ID bypassed consumed private query");
  Require(Has(Wire(refused), "\"effect_attempted\":false"), "spent claim became effect credit");
}

void UnknownCompletionIsStickyAndNeverCallsAgain() {
  state.Reset(); Session session; auto mailbox = NewMailbox();
  auto draft = QueryDraft(session, mailbox.get());
  state.call_status = RiteCreateCallStatus267V1::indeterminate;
  state.call_cleanup_known = false;
  auto unknown = FromQuery(session, mailbox.get(), Action::create, draft); Run(unknown);
  Require(unknown.result.status == Status::indeterminate && !unknown.result.cleanup_known &&
      unknown.result.claim_sequence == 1 && unknown.result.effect_attempted &&
      !unknown.result.native_returned && state.calls == 1 && state.entered_calls == 1,
      "unknown callback completion was recast as known no-dispatch or dropped claim");
  NoSource(unknown);
  const auto observations = state.observations;
  const auto bindings = state.bindings;
  auto later = Request(session, mailbox.get(), Action::query); Run(later);
  Require(later.result.status == Status::indeterminate && !later.result.cleanup_known &&
      state.calls == 1 && state.observations == observations && state.bindings == bindings,
      "unknown session reminted permission or sampled new Raw");
  NoSource(later);
  Require(Has(Wire(unknown), "\"status\":\"indeterminate\""), "unknown wire status lost");
}

void UnknownObservationStopsBeforeAnyEffect() {
  state.Reset(); state.raw_cleanup_known = false;
  Session session; auto mailbox = NewMailbox();
  auto query = Request(session, mailbox.get(), Action::query); Run(query);
  Require(query.result.status == Status::indeterminate && !query.result.cleanup_known && !state.calls,
      "unknown Raw cleanup acquired an available query");
  NoSource(query);
  const auto observations = state.observations;
  state.raw_cleanup_known = true;
  auto next = Request(session, mailbox.get(), Action::query); Run(next);
  Require(next.result.status == Status::indeterminate && state.observations == observations && !state.calls,
      "unknown observation lock was cleared by later request DATA");
}

void SourceFalseCanDataNeverGrantsCreateOrAccept() {
  state.Reset(); state.draft_can = false;
  Session session; auto mailbox = NewMailbox();
  auto query = QueryDraft(session, mailbox.get());
  Require(query.result.source && !query.result.source->draft->native_can_create &&
      Has(Wire(query), "\"native_can_create\":false"), "actual false CanCreate was fabricated unavailable");
  auto refused = FromQuery(session, mailbox.get(), Action::create, query); Run(refused);
  Require(refused.result.status == Status::prerequisite_rejected && !refused.result.claim_sequence && !state.calls,
      "false actual CanCreate dispatched a callback");
  state.draft_can = true;
  auto ready_draft = QueryDraft(session, mailbox.get()); Create(session, mailbox.get(), ready_draft);
  state.accept_can = false;
  auto modal = QueryConfirmation(session, mailbox.get(), ready_draft);
  Require(modal.result.status == Status::available && modal.result.source &&
      !modal.result.source->confirmation->native_can_accept, "actual false CanAccept was fabricated missing");
  auto accept = FromQuery(session, mailbox.get(), Action::accept_confirmation, modal); Run(accept);
  Require(accept.result.status == Status::prerequisite_rejected && !accept.result.claim_sequence && state.calls == 1,
      "false actual CanAccept dispatched or spent an effect claim");
}

void OriginalExpiryAndWorldDriftNeverAuthorizeEffect() {
  state.Reset(); Session session; auto mailbox = NewMailbox();
  auto query = QueryDraft(session, mailbox.get());
  auto expired = FromQuery(session, mailbox.get(), Action::create, query);
  expired.monotonic_deadline_ms = 0;
  const auto observations = state.observations; Run(expired);
  Require(expired.result.status == Status::expired && state.observations == observations && !state.calls,
      "expired/unarmed original operation reached Raw");
  for (bool world : {false, true}) {
    state.drift_after_core = !world; state.drift_after_world = world;
    auto drift = FromQuery(session, mailbox.get(), Action::create, query); Run(drift);
    Require(drift.result.status != Status::available && drift.result.status != Status::create_dispatched &&
      !drift.result.claim_sequence && !state.calls,
      "post-sampling Core/world identity drift granted an effect");
    NoSource(drift);
  }
}

void ExactSourceActorZeroAndNegativeGenerationRemainValid() {
  for (const std::int32_t actor : {0, -2}) {
    state.Reset(); state.actual = CoreFor(actor); state.rite = 0;
    Session session; auto mailbox = NewMailbox();
    auto query = QueryDraft(session, mailbox.get());
    auto create = Create(session, mailbox.get(), query);
    auto modal = QueryConfirmation(session, mailbox.get(), query);
    Require(modal.result.status == Status::available, "valid packed actor lost final query");
    auto accept = FromQuery(session, mailbox.get(), Action::accept_confirmation, modal); Run(accept);
    Require(accept.result.status == Status::confirmation_dispatched && accept.result.source &&
      accept.result.source->actor_id == actor && accept.result.source->source_rite_id == 0 &&
      state.calls == 2, "packed actor0/-2 or Rite0 was changed/rejected");
    (void)create;
  }
}

void MissingRawOrNamedWindowCannotFabricateFalseSource() {
  state.Reset(); state.missing_raw = true;
  Session session; auto mailbox = NewMailbox();
  auto missing = Request(session, mailbox.get(), Action::query); Run(missing);
  Require(missing.result.status == Status::unavailable && missing.result.cleanup_known && !state.calls,
      "missing Raw was fabricated as complete false-can Source");
  NoSource(missing);
  state.missing_raw = false;
  auto draft = QueryDraft(session, mailbox.get()); Create(session, mailbox.get(), draft);
  state.bind_ok = false;
  auto modal = QueryConfirmation(session, mailbox.get(), draft);
  Require(modal.result.status == Status::unavailable && state.calls == 1 && state.window_binds == 1,
      "missing named final window supplied acceptance source");
  NoSource(modal);
}

void OwnerCustodyNeedsOfflineFalseAndFixedSlot28() {
  for (unsigned failure = 0; failure != 5; ++failure) {
    state.Reset(); Session session; auto mailbox = NewMailbox();
    auto query = Request(session, mailbox.get(), Action::query);
    if (failure == 0) mailbox->offline_fixture = true;
    if (failure == 1) mailbox->permitted_executor_octovigintary = nullptr;
    if (failure == 2) {mailbox->permitted_executor_octovigintary = nullptr; mailbox->permitted_executor_septemvigintary = &ExecuteRiteCreateOnOwner267V1;}
    if (failure == 3) query.connection_generation = 0;
    if (failure == 4) query.mailbox = nullptr;
    Run(query);
    Require(query.result.status == Status::unavailable && !state.bindings && !state.observations && !state.calls,
      "wrong/offline/absent owner custody reached observation/effect");
    NoSource(query);
  }
  Require(!ExecuteRiteCreateOnOwner267V1(nullptr, NewStamp()), "null owner context accepted");
}
}

int main() {
  try {
    unsigned passed = 0;
    const auto test = [&](const char* name, auto body) {body(); ++passed; std::cout << "PASS " << name << '\n';};
    test("original_create_pending_query_accept_once", CompleteOriginalCreatePendingConfirmationAndAccept);
    test("connection_rite_core_original_deadline", ConnectionRiteCoreAndOriginalDeadlineMustMatch);
    test("no_old_edit_or_new_session_pending", OldEditOrNewSessionCannotBorrowOriginalCreateProof);
    test("raw_stale_before_claim_keeps_lease", RawStalenessBeforeClaimDoesNotSpendOrRewriteLease);
    test("known_callee_refusal_spent_zero_effect", CalleeBeforeEffectRefusalRetainsSpentClaimWithZeroEffect);
    test("unknown_completion_sticky", UnknownCompletionIsStickyAndNeverCallsAgain);
    test("unknown_observation_sticky", UnknownObservationStopsBeforeAnyEffect);
    test("false_can_data_no_effect", SourceFalseCanDataNeverGrantsCreateOrAccept);
    test("expiry_world_core_drift_no_effect", OriginalExpiryAndWorldDriftNeverAuthorizeEffect);
    test("packed_zero_negative_actor_rite_zero", ExactSourceActorZeroAndNegativeGenerationRemainValid);
    test("missing_raw_named_modal_no_source", MissingRawOrNamedWindowCannotFabricateFalseSource);
    test("actual_slot28_offline_false", OwnerCustodyNeedsOfflineFalseAndFixedSlot28);
    std::cout << "NoGame owner/session groups=" << passed << "; native ABI/runtime qualification=false\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "FAIL " << error.what() << '\n'; return 1;
  }
}
