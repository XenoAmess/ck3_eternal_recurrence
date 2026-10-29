package org.xar.ck3.control.g2.m5;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.g2.planning.ProposalLifecycleFixtures;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real producer, selector, caller-owned lock and persisted consumer, without Game/ledger access. */
final class M5ReservationTest {
    private static final String CORPUS_SHA = "7dd54e752495c5a1f7cacd19e7651758689e3052120d335e273b36650268177c";
    private record Actual(G2Request request, G2Response response, M5Research.Result result, Obj selector) {
        M5FrameDispatcher owner() { return new M5FrameDispatcher(request.source(), object(selector.get("snapshot"), "snapshot"), object(selector.get("commitments"), "commitments")); }
    }

    @Test void allOriginalAcceptedCollectorCasesReachActualReservationAndSavedTypedConsumer() throws Exception {
        int accepted = 0, waiting = 0, reserved = 0;
        for (Value raw : cases()) {
            Obj entry = object(raw, "original case");
            if (!new Bool(true).equals(entry.get("accepted"))) continue;
            accepted++;
            Actual actual = actual(entry);
            Obj original = object(entry.get("expected"), "original expected");
            assertEquals(original.get("analysis"), actual.result().intakeAnalysis().get("analysis"), text(entry.get("name"), "case name"));
            M5FrameDispatcher owner = actual.owner();
            var dispatch = M5ReservationConsumer.reserve(actual.request(), actual.response(), owner);
            assertEquals(actual.result().intakeAnalysis().get("analysis"), dispatch.analysis().orElseThrow());
            assertEquals(dispatch, M5ReservationCodec.decode(M5ReservationCodec.encode(dispatch)));
            assertFalse(dispatch.formalActionReady()); assertFalse(dispatch.intentDurable());
            Obj analysis = object(original.get("analysis"), "original analysis");
            if (analysis.get("selected_candidate_id") == Nil.INSTANCE) {
                waiting++; assertEquals(M5FrameDispatcher.Status.wait, dispatch.status()); assertTrue(dispatch.reservation().isEmpty());
                assertEquals(M5FrameDispatcher.Status.wait, M5ReservationConsumer.reserve(actual.request(), actual.response(), owner).status());
            } else {
                reserved++; assertEquals(M5FrameDispatcher.Status.reserved_observed_analytic, dispatch.status());
                String candidate = text(analysis.get("selected_candidate_id"), "original selected identity");
                assertEquals(candidate, dispatch.selectedCandidateId().orElseThrow());
                Obj chosen = array(analysis.get("evaluated"), "original evaluated").stream().map(value -> object(value, "original candidate"))
                        .filter(value -> new Text(candidate).equals(value.get("candidate_id"))).findFirst().orElseThrow();
                Obj before = object(actual.selector().get("commitments"), "original commitments");
                var reservation = dispatch.reservation().orElseThrow();
                assertEquals(integer(before.get("gold_raw"), "old gold").add(integer(chosen.get("gold_cost_raw"), "selected gold")), reservation.commitmentsAfter().goldRaw());
                assertEquals(integer(before.get("pending_war_slots"), "old slots").add(integer(chosen.get("war_slot_claim"), "selected slots")), reservation.commitmentsAfter().pendingWarSlots());
                assertTrue(reservation.commitmentsAfter().claims().characterIds().containsAll(M5FrameDispatcher.claims(chosen).characterIds()));
                var repeated = M5ReservationConsumer.reserve(actual.request(), actual.response(), owner);
                assertEquals(M5FrameDispatcher.Status.already_reserved_this_frame, repeated.status());
                assertEquals(dispatch.reservation(), repeated.reservation());
                assertEquals(actual.request().source(), owner.resourceSnapshot().source());
                assertEquals(reservation.frame(), owner.resourceSnapshot().frame());
                assertEquals(reservation.commitmentsAfter(), owner.resourceSnapshot().commitments());
                assertEquals(dispatch.reservation(), owner.resourceSnapshot().reservation());
                assertEquals(repeated, M5ReservationCodec.decode(M5ReservationCodec.encode(repeated)));
            }
            assertEquals(new Bool(false), actual.result().intakeAnalysis().get("resource_reservation_performed"));
        }
        assertEquals(18, accepted, "original accepted corpus must stay complete");
        assertTrue(waiting > 0 && reserved > 0, "both actual reservation transitions must execute");
    }

    @Test void cooperatingCallersShareOneActualLockAndOnlyOneReservation() throws Exception {
        Actual actual = named("five-family-proposals-original-rank"); M5FrameDispatcher owner = actual.owner();
        CountDownLatch start = new CountDownLatch(1);
        try (var pool = Executors.newFixedThreadPool(2)) {
            var first = pool.submit(() -> { assertTrue(start.await(5, TimeUnit.SECONDS)); return M5ReservationConsumer.reserve(actual.request(), actual.response(), owner); });
            var second = pool.submit(() -> { assertTrue(start.await(5, TimeUnit.SECONDS)); return M5ReservationConsumer.reserve(actual.request(), actual.response(), owner); });
            start.countDown();
            var values = List.of(first.get(10, TimeUnit.SECONDS), second.get(10, TimeUnit.SECONDS));
            assertEquals(1, values.stream().filter(value -> value.status() == M5FrameDispatcher.Status.reserved_observed_analytic).count());
            assertEquals(1, values.stream().filter(value -> value.status() == M5FrameDispatcher.Status.already_reserved_this_frame).count());
            assertEquals(values.get(0).reservation(), values.get(1).reservation());
        }
    }

    @Test void ownerRejectsChangedSameFrameTreasuryAndCommitmentsWithoutReserving() throws Exception {
        Actual actual = named("five-family-proposals-original-rank"); M5FrameDispatcher owner = actual.owner();
        Obj snapshot = object(actual.selector().get("snapshot"), "snapshot");
        Obj gold = object(snapshot.get("played_character_gold"), "gold");
        assertThrows(IllegalArgumentException.class, () -> owner.chooseObserved(actual.request().source(), actual.selector().with("snapshot", snapshot.with("played_character_gold", gold.with("raw", new IntegerValue(BigInteger.ONE))))));
        Obj commitments = object(actual.selector().get("commitments"), "commitments");
        assertThrows(IllegalArgumentException.class, () -> owner.chooseObserved(actual.request().source(), actual.selector().with("commitments", commitments.with("gold_raw", new IntegerValue(BigInteger.ONE)))));
        G2Source other = new G2Source(actual.request().source().machineId(), actual.request().source().observedAtUtc(), "different-original-source", actual.request().source().sourceRef());
        assertThrows(IllegalArgumentException.class, () -> owner.chooseObserved(other, actual.selector()));
        assertTrue(owner.resourceSnapshot().reservation().isEmpty());
        assertEquals(M5FrameDispatcher.Status.reserved_observed_analytic, owner.chooseObserved(actual.request().source(), actual.selector()).status());
    }

    @Test void envelopeAndOriginalRequestConflictsCannotConsumeTheOwner() throws Exception {
        Actual actual = named("five-family-proposals-original-rank"); M5FrameDispatcher owner = actual.owner();
        G2Response wrongId = new G2Response("different-request", Milestone.M5, actual.response().source(), actual.response().result());
        assertThrows(IllegalArgumentException.class, () -> M5ReservationConsumer.reserve(actual.request(), wrongId, owner));
        Obj sourceIntake = ((M5PayloadCodec.ContextRequest) M5PayloadCodec.decodeOperation(actual.request().payload().bytes())).context().intakeRequest();
        Obj sources = object(sourceIntake.get("sources"), "sources");
        M5PayloadCodec.Request changed = new M5PayloadCodec.Request(sourceIntake.with("sources", sources.with("gold_reserve_raw", new IntegerValue(BigInteger.ZERO))), new M5Research.MissingPlan());
        G2Request changedRequest = new G2Request(actual.request().requestId(), Milestone.M5, actual.request().source(), ProjectionJson.object(M5PayloadCodec.encodeContextOperation(changed), M5PayloadCodec.MAXIMUM_BYTES));
        assertThrows(IllegalArgumentException.class, () -> M5ReservationConsumer.reserve(changedRequest, actual.response(), owner));
        assertEquals(M5FrameDispatcher.Status.reserved_observed_analytic, M5ReservationConsumer.reserve(actual.request(), actual.response(), owner).status());
    }

    @Test void pureLifecycleProposalNeverEntersObservedReservationApi() throws Exception {
        Actual actual = named("five-family-proposals-original-rank");
        Obj operation = new Obj(Map.of("schema", new Text(M5PayloadCodec.OPERATION_SCHEMA), "operation", new Text("proposal_lifecycle"),
                "request", M5PayloadCodec.parseObject(ProposalLifecycleCodec.encodePayload(ProposalLifecycleFixtures.request()), "actual lifecycle request")));
        G2Request request = new G2Request("lifecycle-no-observed-reservation", Milestone.M5, actual.request().source(), ProjectionJson.object(OpportunityJson.encode(operation), M5PayloadCodec.MAXIMUM_BYTES));
        G2Response response = new M5Research().evaluate(request); M5FrameDispatcher owner = actual.owner();
        assertThrows(IllegalArgumentException.class, () -> M5ReservationConsumer.reserve(request, response, owner));
        assertEquals(M5FrameDispatcher.Status.reserved_observed_analytic, M5ReservationConsumer.reserve(actual.request(), actual.response(), owner).status());
    }

    @Test void rawWrongMissingAndNullReservationFieldsUseActualDecodeFailures() throws Exception {
        Actual actual = named("five-family-proposals-original-rank");
        Obj saved = M5PayloadCodec.parseObject(M5ReservationCodec.encode(M5ReservationConsumer.reserve(actual.request(), actual.response(), actual.owner())), "saved dispatch");
        assertThrows(IllegalArgumentException.class, () -> M5ReservationCodec.decode(OpportunityJson.encode(saved.with("formal_action_ready", new Bool(true)))));
        assertThrows(IllegalArgumentException.class, () -> M5ReservationCodec.decode(OpportunityJson.encode(saved.with("unexpected", Nil.INSTANCE))));
        assertThrows(IllegalArgumentException.class, () -> M5ReservationCodec.decode(OpportunityJson.encode(saved.with("reservation", Nil.INSTANCE))));
        Obj analysis = object(saved.get("analysis"), "analysis");
        assertThrows(IllegalArgumentException.class, () -> M5ReservationCodec.decode(OpportunityJson.encode(saved.with("analysis", analysis.with("formal_action_ready", new Bool(true))))));
        Obj reservation = object(saved.get("reservation"), "reservation"), costs = object(reservation.get("observed_opportunity_cost"), "costs");
        assertThrows(IllegalArgumentException.class, () -> M5ReservationCodec.decode(OpportunityJson.encode(saved.with("reservation", reservation.with("observed_opportunity_cost", costs.with("gold_cost_raw", new Bool(true)))))));
        var missing = new java.util.LinkedHashMap<>(saved.members()); missing.remove("analysis");
        assertThrows(IllegalArgumentException.class, () -> M5ReservationCodec.decode(OpportunityJson.encode(new Obj(missing))));
        assertThrows(IllegalArgumentException.class, () -> M5ReservationCodec.decode(new byte[] {(byte) 0xc3, 0x28}));
    }

    private static Actual named(String name) throws Exception {
        for (Value value : cases()) { Obj row = object(value, "case"); if (new Text(name).equals(row.get("name"))) return actual(row); }
        throw new IllegalArgumentException("original named producer case missing: " + name);
    }
    private static Actual actual(Obj row) {
        Obj intake = object(row.get("input"), "original producer input");
        M5PayloadCodec.Request context = new M5PayloadCodec.Request(intake, new M5Research.MissingPlan());
        String machine = System.getenv("XAR_MACHINE_ID"); assertNotNull(machine, "actual machine fixture environment required");
        G2Source source = new G2Source(machine, Instant.parse("2026-10-22T22:54:34Z").toString(), "original-producer-corpus-software-only-no-native-qualification", new ExactRef("resource:/jointintake/producer-golden-v1.json.gz", 15627, CORPUS_SHA));
        G2Request request = new G2Request("m5-actual-reservation-" + text(row.get("name"), "original name"), Milestone.M5, source, ProjectionJson.object(M5PayloadCodec.encodeContextOperation(context), M5PayloadCodec.MAXIMUM_BYTES));
        G2Response response = G2Wire.decodeResponse(G2Wire.encodeResponse(new M5Research().evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(request)))));
        M5Research.Result result = M5PayloadCodec.decodeResult(response.result().bytes());
        return new Actual(request, response, result, object(result.intakeAnalysis().get("selector_request"), "actual selector request"));
    }
    private static List<Value> cases() throws Exception {
        try (var stream = M5ReservationTest.class.getResourceAsStream("/jointintake/producer-golden-v1.json.gz")) {
            assertNotNull(stream, "unchanged complete original corpus required");
            byte[] bytes = stream.readAllBytes();
            assertEquals(CORPUS_SHA, java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes)));
            try (var gzip = new GZIPInputStream(new java.io.ByteArrayInputStream(bytes))) {
                return array(M5PayloadCodec.parseObject(gzip.readAllBytes(), "original producer corpus").get("cases"), "original cases");
            }
        }
    }
}
