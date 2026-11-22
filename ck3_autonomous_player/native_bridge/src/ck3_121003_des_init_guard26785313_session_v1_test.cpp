// Source-only owner/session regression. Frame/Raw are explicit self-owned NoGame
// dependencies; a successful test would not qualify the native ABI or a live game.
#if defined(XAR_CK3_ENABLE_121003_26785313_DES_INIT_GUARD_V1) && !XAR_CK3_ENABLE_121003_26785313_DES_INIT_GUARD_V1
#error This source tests the enabled owner; build the independent default-off leaf separately.
#endif
#ifndef XAR_CK3_ENABLE_121003_26785313_DES_INIT_GUARD_V1
#define XAR_CK3_ENABLE_121003_26785313_DES_INIT_GUARD_V1 1
#endif
#include "des_init_guard_owner_nogame_fixture.hpp"

namespace {
using namespace des_owner_fixture;

void IndependentQueriesRetainShownFalseAndTrue() {
  state.Reset();
  DesInitGuardSession267V1 session;
  auto mailbox = NewMailbox();
  auto stamp = NewStamp();
  auto first = Query(session, mailbox.get());
  Run(first, stamp);
  Require(first.result.status == Status::available && first.result.cleanup_known &&
    first.result.source && !first.result.source->native_shown &&
    first.result.query_sequence == 1 && first.result.provider_generation > 0,
    "Shown=false was turned into unavailability or initialization credit");
  Require(first.result.facts_available && Same(first.result.facts, first.request.expected) &&
    first.result.connection_generation == 21 &&
    first.result.ticket_sequence == first.ticket.sequence &&
    first.result.thread_id == stamp.thread_id && first.result.pump_epoch == stamp.pump_epoch,
    "actual query did not retain complete Core and this callback's custody");
  Has(ReadonlyWire(first), "\"native_shown\":false", "actual false Shown was not serialized");
  const auto generation = first.result.provider_generation;
  state.shown = true;
  // Each query gets independent actual custody; session, connection and world remain stable.
  state.frames = 0;
  ++stamp.pump_epoch;
  auto second = Query(session, mailbox.get());
  Run(second, stamp);
  Require(second.request.id() != first.request.id() &&
    second.ticket.sequence != first.ticket.sequence &&
    second.result.status == Status::available && second.result.source &&
    second.result.source->native_shown && second.result.provider_generation == generation &&
    second.result.query_sequence == 2 &&
    second.result.ticket_sequence == second.ticket.sequence &&
    second.result.pump_epoch == stamp.pump_epoch &&
    state.observations == 2 && state.bindings == 4,
    "same session did not perform two independent queries with increasing sequence");
  Has(ReadonlyWire(second), "\"native_shown\":true", "actual true Shown was not serialized");
  Require(state.seen_context == &second &&
    state.seen_wall == second.request.deadline_unix_ms &&
    state.seen_monotonic == second.monotonic_deadline_ms,
    "owner did not forward this context and original deadline to its Frame dependency");
}

void SignedPackedActorsZeroAndNegativeGeneration() {
  DesInitGuardSession267V1 session;
  auto mailbox = NewMailbox();
  const auto stamp = NewStamp();
  std::uint64_t sequence = 0;
  for (const std::int32_t actor : {0, -2}) {
    state.Reset(); state.actual = CoreFor(actor);
    auto query = Query(session, mailbox.get(), actor);
    Run(query, stamp);
    Require(query.result.status == Status::available && query.result.source &&
      query.result.source->character_id == actor && query.result.query_sequence == ++sequence,
      "valid full signed32 packed actor was rejected or changed");
    Has(ReadonlyWire(query), "\"character_id\":" + std::to_string(actor),
        "serializer lost actual signed packed actor");
  }
  state.Reset(); state.actual = CoreFor(-1);
  auto invalid = Query(session, mailbox.get(), -1);
  Run(invalid, stamp);
  Require(invalid.result.status == Status::unavailable && !state.observations && !state.frames,
      "invalid -1 actor reached Frame/Raw");
  NoSource(invalid);
}

void EveryCoreFieldIsCheckedBeforeRaw() {
  for (unsigned field = 0; field != 8; ++field) {
    state.Reset(); MutateCore(state.actual, field);
    DesInitGuardSession267V1 session;
    auto mailbox = NewMailbox();
    auto query = Query(session, mailbox.get());
    Run(query, NewStamp());
    Require(query.result.status == Status::stale_source && state.frames == 1 &&
      state.observations == 0 && query.result.reason == "des_init_guard_actual_core_changed",
      "a changed expected Core field reached Raw");
    NoSource(query);
    Has(ReadonlyWire(query), "\"source\":null", "changed Core acquired source");
  }
}

void EveryCoreFieldIsCheckedAfterRaw() {
  for (unsigned field = 0; field != 8; ++field) {
    state.Reset(); state.post_core_field = field;
    DesInitGuardSession267V1 session;
    auto mailbox = NewMailbox();
    auto query = Query(session, mailbox.get());
    Run(query, NewStamp());
    Require(query.result.status == Status::stale_source && state.frames == 2 &&
      state.observations == 1 && query.result.cleanup_known,
      "post-predicate Core drift was granted an available source");
    NoSource(query);
  }
}

void AllSevenWorldIdentitiesAreCheckedAfterRaw() {
  for (unsigned pointer = 0; pointer != 7; ++pointer) {
    state.Reset(); state.post_world_pointer = pointer;
    DesInitGuardSession267V1 session;
    auto mailbox = NewMailbox();
    auto query = Query(session, mailbox.get());
    Run(query, NewStamp());
    Require(query.result.status == Status::stale_source && state.frames == 2 &&
      state.observations == 1 &&
      query.result.reason == "des_init_guard_actual_world_changed_after_predicate",
      "post-predicate game/world/storage/player/actor identity drift was accepted");
    NoSource(query);
  }
}

void ExpiredWallAndMonotonicDeadlineNeverReachRaw() {
  DesInitGuardSession267V1 session;
  auto mailbox = NewMailbox();
  state.Reset();
  auto expired = Query(session, mailbox.get());
  expired.request.deadline_unix_ms = Wall() - 1;
  Run(expired, NewStamp());
  Require(expired.result.status == Status::expired && !state.frames && !state.observations,
      "expired original wall deadline reached Raw");
  NoSource(expired);
  state.Reset();
  auto unarmed = Query(session, mailbox.get());
  unarmed.monotonic_deadline_ms = 0;
  Run(unarmed, NewStamp());
  Require(unarmed.result.status == Status::expired && !state.frames && !state.observations,
      "unarmed monotonic deadline reached Raw");
  NoSource(unarmed);
  state.Reset();
  auto elapsed = Query(session, mailbox.get());
  elapsed.monotonic_deadline_ms = GetTickCount64();
  Run(elapsed, NewStamp());
  Require(elapsed.result.status == Status::expired && !state.frames && !state.observations,
      "elapsed monotonic deadline reached Raw");
  NoSource(elapsed);
}

void MissingRawDefinitionIsUnavailableNotShownFalse() {
  state.Reset(); state.raw_missing = true;
  DesInitGuardSession267V1 session;
  auto mailbox = NewMailbox();
  auto missing = Query(session, mailbox.get());
  Run(missing, NewStamp());
  Require(missing.result.status == Status::unavailable && missing.result.cleanup_known &&
    missing.native_observation_entered && state.frames == 1 && state.observations == 1 &&
    missing.result.reason == "nogame_actual_definition_unavailable",
    "missing definition was mistaken for available Shown=false");
  NoSource(missing);
  Has(ReadonlyWire(missing), "\"source\":null", "missing Raw produced public source");
  // A known unavailable observation does not consume a successful query sequence.
  state.Reset();
  auto next = Query(session, mailbox.get());
  Run(next, NewStamp());
  Require(next.result.status == Status::available && next.result.query_sequence == 1,
    "known unavailable observation poisoned or advanced the session sequence");
}

void CleanupUnknownSticksAndStopsFurtherFrameAndRaw() {
  state.Reset(); state.cleanup_known = false;
  DesInitGuardSession267V1 session;
  auto mailbox = NewMailbox();
  auto unknown = Query(session, mailbox.get());
  Run(unknown, NewStamp());
  Require(unknown.result.status == Status::indeterminate && !unknown.result.cleanup_known &&
    state.frames == 1 && state.observations == 1 &&
    unknown.result.reason == "des_init_guard_owned_scope_cleanup_unknown",
    "cleanup unknown retained source or a known terminal state");
  NoSource(unknown);
  Has(ReadonlyWire(unknown), "\"cleanup_known\":false", "unknown cleanup was hidden");
  state.Reset(); state.shown = true;
  auto later = Query(session, mailbox.get());
  Run(later, NewStamp());
  Require(later.result.status == Status::indeterminate && !later.result.cleanup_known &&
    later.result.reason == "des_init_guard_prior_cleanup_unknown_no_permission" &&
    !state.bindings && !state.frames && !state.observations,
    "unknown session made another Frame/Raw call or reminted a source");
  NoSource(later);
}

void ExplicitUnknownLatchStopsWithoutRaw() {
  state.Reset();
  DesInitGuardSession267V1 session;
  BlockDesInitGuardUnknown267V1(session);
  auto mailbox = NewMailbox();
  auto query = Query(session, mailbox.get());
  Run(query, NewStamp());
  Require(query.result.status == Status::indeterminate && !query.result.cleanup_known &&
    !state.bindings && !state.frames && !state.observations,
    "explicit unknown latch admitted another observation");
  NoSource(query);
}

void MailboxMustUseRealSlot27WithOfflineFixtureFalse() {
  for (unsigned failure = 0; failure != 5; ++failure) {
    state.Reset();
    DesInitGuardSession267V1 session;
    auto mailbox = NewMailbox();
    auto query = Query(session, mailbox.get());
    switch (failure) {
      case 0: mailbox->offline_fixture = true; break;
      case 1: mailbox->permitted_executor_septemvigintary = nullptr; break;
      case 2:
        mailbox->permitted_executor_septemvigintary = nullptr;
        mailbox->permitted_executor_quinquevigintary = &ExecuteDesInitGuardOnOwner267V1;
        break;
      case 3: query.connection_generation = 0; break;
      case 4: query.mailbox = nullptr; break;
    }
    Run(query, NewStamp());
    Require(query.result.status == Status::unavailable &&
      !state.bindings && !state.frames && !state.observations,
      "offline fixture/wrong slot/absent mailbox or connection reached Frame/Raw");
    NoSource(query);
  }
}

void MissingSessionAndMalformedRequestNeverReachRaw() {
  DesInitGuardSession267V1 session;
  auto mailbox = NewMailbox();
  for (unsigned failure = 0; failure != 3; ++failure) {
    state.Reset();
    auto query = Query(session, mailbox.get());
    if (failure == 0) query.session = nullptr;
    if (failure == 1) query.request.request_id_size = 0;
    if (failure == 2) query.request.deadline_unix_ms = 0;
    Run(query, NewStamp());
    Require(query.result.status == Status::unavailable &&
      !state.bindings && !state.frames && !state.observations,
      "missing session or malformed request reached Frame/Raw");
    NoSource(query);
  }
  Require(!ExecuteDesInitGuardOnOwner267V1(nullptr, NewStamp()),
      "null callback context was accepted");
}

void FrameUnavailableOrUnverifiedNeverGrantsSource() {
  for (unsigned failure = 0; failure != 2; ++failure) {
    state.Reset();
    if (failure == 0) state.frame_missing = true;
    else state.facts_verified = false;
    DesInitGuardSession267V1 session;
    auto mailbox = NewMailbox();
    auto query = Query(session, mailbox.get());
    Run(query, NewStamp());
    if (failure == 0) {
      Require(query.result.status == Status::unavailable && state.observations == 0 &&
        query.result.reason == "nogame_frame_dependency_unavailable",
        "missing Frame dependency reached Raw");
    } else {
      // SameFrame explicitly checks both verified flags after Raw. This is not a
      // claim that a real Frame reader would return success for unverified facts.
      Require(query.result.status == Status::stale_source && state.observations == 1,
        "unverified before/after frames acquired source");
    }
    NoSource(query);
    Has(ReadonlyWire(query), "\"source\":null", "invalid Frame serialized source");
  }
}
}

int main() {
  try {
    unsigned passed = 0;
    const auto test = [&](const char* name, auto body) {
      body(); ++passed; std::cout << "PASS " << name << '\n';
    };
    test("independent_false_true_queries", IndependentQueriesRetainShownFalseAndTrue);
    test("signed_packed_actor_ids", SignedPackedActorsZeroAndNegativeGeneration);
    test("pre_raw_all_core_fields", EveryCoreFieldIsCheckedBeforeRaw);
    test("post_raw_all_core_fields", EveryCoreFieldIsCheckedAfterRaw);
    test("post_raw_all_world_identities", AllSevenWorldIdentitiesAreCheckedAfterRaw);
    test("original_expired_deadlines", ExpiredWallAndMonotonicDeadlineNeverReachRaw);
    test("missing_raw_is_not_false_shown", MissingRawDefinitionIsUnavailableNotShownFalse);
    test("cleanup_unknown_is_sticky", CleanupUnknownSticksAndStopsFurtherFrameAndRaw);
    test("explicit_unknown_latch", ExplicitUnknownLatchStopsWithoutRaw);
    test("offline_false_and_exact_slot27", MailboxMustUseRealSlot27WithOfflineFixtureFalse);
    test("request_session_and_null_context", MissingSessionAndMalformedRequestNeverReachRaw);
    test("frame_unavailable_or_unverified", FrameUnavailableOrUnverifiedNeverGrantsSource);
    std::cout << "NoGame owner/session cases=" << passed << "; live ABI qualification=false\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
