package org.xar.ck3.control.application.planning.governance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceFixtures.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldown;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldownCodec;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryCodec;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryPolicy;

/** Reproduces the first-publication/cold-proof deadlock through the actual ordinary Crown policy. */
final class CrownRetryOrdinaryPolicyTest {
    @Test void noRetainedProofStillRunsFreshNativeClockAndProducesOnlyAnOriginalWriterIntent() {
        var request = request(); var supplier = new RetrySupplier(request);
        var decision = assertInstanceOf(OrdinaryPolicy.Replace.class,
                new GovernancePolicies.Crown(supplier, REF).evaluate(request, advance(request)));
        assertEquals(1, supplier.retryReads); assertEquals(1, supplier.cooldownReads);
        Obj detail = decision.draft().detail(); assertEquals(new Text("current_query"), detail.get("crown_calendar_retry_source"));
        assertEquals(new Text("exact Game import proof absent"), detail.get("crown_retry_cache_unavailable_reason"));
        Obj intent = object(detail.get("crown_required_retry_intent"), "required source-bound publication");
        Obj hint = object(intent.get("after"), "current native retry");
        assertEquals(new Text("sole_continuity_writer"), intent.get("publication_authority"));
        assertEquals(new IntegerValue(BigInteger.valueOf(request.before().game().pid())), object(hint.get("source_context"), "context").get("bridge_pid"));
        assertEquals(new Text(request.before().frame().episodeRunId()), object(hint.get("source_context"), "context").get("episode_run_id"));
        assertEquals(new IntegerValue(request.before().frame().identity().player()), hint.get("actor_character_id"));
        assertEquals(n(364), hint.get("retry_date_raw"));
        assertEquals("life-advance", decision.draft().command().orElseThrow().operation().value());
    }

    @Test void aProvenCurrentFutureHintAvoidsAnotherClockReadAndDoesNotRepublish() {
        var request = request(); var supplier = new RetrySupplier(request); supplier.cached = true;
        var decision = assertInstanceOf(OrdinaryPolicy.Replace.class,
                new GovernancePolicies.Crown(supplier, REF).evaluate(request, advance(request)));
        assertEquals(1, supplier.retryReads); assertEquals(0, supplier.cooldownReads);
        assertEquals(new Text("reused_hint"), decision.draft().detail().get("crown_calendar_retry_source"));
        assertNull(decision.draft().detail().get("crown_required_retry_intent"));
        assertEquals("life-advance", decision.draft().command().orElseThrow().operation().value());
    }

    @Test void clockDateDriftIsRejectedBeforeCreatingAnyHint() {
        var request = request(); var supplier = new RetrySupplier(request); supplier.clockDateDrift = true;
        assertThrows(IllegalArgumentException.class,
                () -> new GovernancePolicies.Crown(supplier, REF).evaluate(request, advance(request)));
        assertEquals(1, supplier.cooldownReads);
    }

    @Test void originalPendingAndUnknownStillTakePrecedenceOverAllNativeRetryReads() {
        for (DomainStatus status : List.of(DomainStatus.PENDING, DomainStatus.UNKNOWN)) {
            var request = request(); var supplier = new RetrySupplier(request); var old = supplier.durable;
            var retained = new Obj(java.util.Map.of()).with("stage", new Text("submission_unresolved")).with("action_id", new Text("original-crown-action"));
            supplier.durable = new Durable(old.observed(), old.sessionId(), old.cadence(), old.opening(), old.council(),
                    Optional.of(new DomainState(status, Optional.empty(), Optional.of(retained), retained)));
            new GovernancePolicies.Crown(supplier, REF).evaluate(request, advance(request));
            assertEquals(0, supplier.crownReads); assertEquals(0, supplier.retryReads); assertEquals(0, supplier.cooldownReads);
            assertEquals(Optional.of(retained), supplier.durable.crown().orElseThrow().legacyPending());
        }
    }

    private static final class RetrySupplier implements GovernanceObservationSupplier {
        private Durable durable;
        private boolean cached;
        private boolean clockDateDrift;
        private int crownReads;
        private int retryReads;
        private int cooldownReads;
        private RetrySupplier(PlanningRequest request) { durable = GovernanceFixtures.durable(request); }
        @Override public Read<Durable> durable(PlanningRequest request) { return new Known<>(durable, List.of(REF)); }
        @Override public Read<Crown> crown(PlanningRequest request) {
            crownReads++; var value = GovernanceFixtures.crown(request).readback();
            var blocked = value.candidates().stream().map(candidate -> candidate.active() ? candidate
                    : new CrownAuthorityPolicy.Candidate(candidate.lawKey(), false, candidate.engineFinalOnly(), false,
                            "actual native cooldown block", candidate.costs())).toList();
            var observed = new CrownAuthorityPolicy.Readback(value.schema(), value.available(), value.paused(), value.groupKey(), value.activeLawKey(),
                    blocked, value.resources(), value.titleSuccessors(), value.sourceFrame(), value.readOnly(), value.advertised());
            return new Known<>(new Crown(observed, object(parse(CrownAuthorityCodec.encodeReadback(observed)), "full original Crown readback")), List.of(REF));
        }
        @Override public Read<CrownRetryCodec.MatchRequest> crownRetry(PlanningRequest request, String lawKey) {
            retryReads++;
            if (!cached) return new Unavailable<>("exact Game import proof absent");
            var frame = request.before().frame();
            Obj hint = new Obj(java.util.Map.of()).with("source_context", new Obj(java.util.Map.of()).with("bridge_pid", new IntegerValue(BigInteger.valueOf(request.before().game().pid()))).with("episode_run_id", new Text(frame.episodeRunId()))).with("actor_character_id", new IntegerValue(frame.identity().player())).with("law_key", new Text(lawKey)).with("observed_date_raw", new IntegerValue(frame.identity().dateRaw())).with("retry_date_raw", n(364));
            Obj body = new Obj(java.util.Map.of()).with("pending", Nil.INSTANCE).with("resolved", Nil.INSTANCE).with("retry", hint);
            Obj input = new Obj(java.util.Map.of()).with("schema", new Text(CrownRetryCodec.MATCH_SCHEMA)).with("bridge_pid", new IntegerValue(BigInteger.valueOf(request.before().game().pid()))).with("snapshot", request.observations().snapshot()).with("state", body).with("law_key", new Text(lawKey));
            return new Known<>(CrownRetryCodec.decodeMatch(encode(input)), List.of(REF));
        }
        @Override public Read<CrownCooldownCodec.ClockRequest> crownCooldown(PlanningRequest request) {
            cooldownReads++; BigInteger date = request.before().frame().identity().dateRaw().add(clockDateDrift ? BigInteger.ONE : BigInteger.ZERO);
            var clock = new CrownCooldown.RawObservation(true, true, true, 28, 7, 21, date.add(BigInteger.valueOf(264)), CrownCooldown.EXPIRY_TYPE, CrownCooldown.PROJECTED_UNIT);
            var tick = new CrownCooldown.TurnTick(true, BigInteger.TWO, true, true, true, null, CrownCooldown.TICK_SOURCE);
            return new Known<>(new CrownCooldownCodec.ClockRequest(clock, date, tick), List.of(REF));
        }
        @Override public Read<Life> lifestyle(PlanningRequest request, String preferred, boolean opening) { return new Unavailable<>("unused by Crown regression"); }
        @Override public Read<OpeningComparison> openingComparison(PlanningRequest request) { return new Unavailable<>("unused by Crown regression"); }
        @Override public Read<CouncilSelection.Query> council(PlanningRequest request, CouncilSelection.Position position) { return new Unavailable<>("unused by Crown regression"); }
        @Override public Read<CouncilSelection.Query> coreCouncil(PlanningRequest request) { return new Unavailable<>("unused by Crown regression"); }
        @Override public Read<CouncilRoot> councilRoot(PlanningRequest request) { return new Unavailable<>("unused by Crown regression"); }
    }
}
