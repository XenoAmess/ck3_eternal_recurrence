package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * Software native packet/facts producer -> actual held sample/default interval -> production profile -> cold replay.
 * The controlled endpoint and ACK chronology are DATA fixtures, not a Root physical lease or a Game qualification.
 */
final class NativeDirectFixedWindowObservationTest {
    private static final Instant DEADLINE = Instant.parse("2030-01-01T00:00:00Z");
    private static final BigInteger NATIVE_GENERATION = BigInteger.valueOf(23);
    private static final String BUILD = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";

    @Test void actualHeldSampleKeepsNativeTimeAndColdRoundTripsEveryAvailableCloseOutcome() throws Exception {
        for (var kind : ArmyWindowCodec.Kind.values()) for (String status : List.of("closed_verified", "already_absent", "already_hidden")) {
            Fixture f = new Fixture(kind, status); var result = f.observer.observe(f.command, f.attempt, f.ack);
            var completed = assertInstanceOf(ActionPorts.DirectFixedWindowObserved.class, result.result());
            assertEquals(1, f.port.samples.get());
            ActionReceipt receipt = f.completed(completed.completion());
            var original = NativeDirectFixedWindowObservation.load(receipt, f.archive, f.loader);
            assertEquals(f.before.identity(), original.after().orElseThrow().identity());
            assertEquals(f.before.observedAt(), original.after().orElseThrow().observedAt(), "sampling never relabels a cached native packet time");
            assertTrue(original.sampling().startedAt().compareTo(f.ack.custody().orElseThrow().responseReceived().observedAt()) >= 0);
            assertEquals(BigInteger.ZERO, StrictJson.parse(original.normalized().bytes()).get("queried_connection_generation").bigIntegerValue());
            assertEquals(NATIVE_GENERATION, original.observation().leaf().get("connection_generation").bigIntegerValue());
            assertEquals(Optional.of(original.normalized()), result.compatibleResult());
            assertEquals(completed.completion(), NativeDirectFixedWindowObservation.Completion.decode(completed.completion().encode(f.archive), f.archive));
            assertDoesNotThrow(() -> f.observer.verifyArchived(receipt));
            assertEquals(ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT, receipt.outcome());
            assertFalse(receipt.visibleGameplay()); assertFalse(receipt.eligibleAdvance()); assertTrue(receipt.applied().isEmpty());
            assertThrows(IllegalArgumentException.class, () -> new NativeEffectSnapshots.Pair(f.before, original.after().orElseThrow()));
        }
    }

    @Test void unavailableAndVerificationPendingKeepActualAfterWithoutCompatibleSuccess() throws Exception {
        for (var kind : ArmyWindowCodec.Kind.values()) for (String status : List.of("verification_pending", "unavailable")) {
            Fixture f = new Fixture(kind, status); var projected = f.observer.observe(f.command, f.attempt, f.ack);
            var pending = assertInstanceOf(ActionPorts.Pending.class, projected.result());
            assertTrue(projected.compatibleResult().isEmpty()); assertEquals(1, pending.evidence().size());
            var receipt = f.pending(pending.evidence());
            var cold = NativeDirectFixedWindowObservation.load(receipt, f.archive, f.loader);
            assertEquals(status, cold.observation().status()); assertTrue(cold.completion().isEmpty());
            assertTrue(cold.after().isPresent()); assertEquals(f.before.identity(), cold.after().orElseThrow().identity());
            assertEquals(pending.evidence().getFirst(), cold.basis());
            assertDoesNotThrow(() -> f.observer.verifyArchived(receipt));
            assertFalse(receipt.settled()); assertFalse(receipt.visibleGameplay());
        }
    }

    @Test void onlyActualResultsCallbackScopeTransitionRetainsFullAfterWithoutInventingComplete() throws Exception {
        Fixture f = new Fixture(ArmyWindowCodec.Kind.RESULTS, "verification_pending");
        f.top.withObject("result").put("scope_unchanged", false).put("post_observed", false)
                .put("unavailable_reason", "war_results_ui_scope_transition; actual callback returned");
        f.replaceAck(); f.port.current = frame(10, 74, 53144352, false, false, 0);
        var projected = f.observer.observe(f.command, f.attempt, f.ack);
        var pending = assertInstanceOf(ActionPorts.Pending.class, projected.result());
        var cold = NativeDirectFixedWindowObservation.load(f.pending(pending.evidence()), f.archive, f.loader);
        assertTrue(cold.after().isEmpty()); assertTrue(cold.completion().isEmpty());
        assertEquals(BigInteger.TEN, cold.sampledAfter().actual().nativeRevision());
        assertEquals(BigInteger.valueOf(74), OpportunityJson.integer(OpportunityJson.object(
                cold.sampledAfter().semantic().get("played_character"), "player").get("character_id"), "player"));
        assertEquals(cold.sampledAfter().originalEvidence(), cold.sampledBasis().nativeFrame());
        Fixture overview = new Fixture(ArmyWindowCodec.Kind.OVERVIEW, "verification_pending");
        overview.port.current = f.port.current;
        assertThrows(IllegalArgumentException.class, () -> overview.observer.observe(overview.command, overview.attempt, overview.ack));
    }

    @Test void unchangedIdentifiersCannotHideDifferentOriginalsAndOrdinaryFrameDriftStillFails() throws Exception {
        Fixture changed = new Fixture(ArmyWindowCodec.Kind.OVERVIEW, "closed_verified");
        changed.port.current = frame(9, 73, 53144328, true, true, 1);
        assertThrows(IllegalArgumentException.class, () -> changed.observer.observe(changed.command, changed.attempt, changed.ack));
        Fixture advanced = new Fixture(ArmyWindowCodec.Kind.RESULTS, "closed_verified");
        advanced.port.current = frame(10, 73, 53144352, true, true, 0);
        assertThrows(IllegalArgumentException.class, () -> advanced.observer.observe(advanced.command, advanced.attempt, advanced.ack));
    }

    @Test void originalAckPacketOutboundRevisionAndCustodyRemainMandatory() throws Exception {
        Fixture badPacket = new Fixture(ArmyWindowCodec.Kind.OVERVIEW, "closed_verified");
        byte[] corrupted = badPacket.ack.originalPacket(); corrupted[0] ^= 1;
        var old = badPacket.ack;
        var bad = new NativeActionPort.AckReceived(old.requestId(), old.nativeOk(), old.originalResultToken(), old.originalFrame(), corrupted,
                old.outbound(), old.custody());
        assertThrows(IllegalArgumentException.class, () -> badPacket.observer.observe(badPacket.command, badPacket.attempt, bad));
        for (Object value : List.of(true, 9.0, 10)) {
            Fixture f = new Fixture(ArmyWindowCodec.Kind.RESULTS, "closed_verified");
            ObjectNode outgoing = request(f.kind.step(ArmyWindowCodec.Operation.CLOSE), f.attempt.requestId(), BigInteger.valueOf(9));
            if (value instanceof Boolean b) outgoing.put("expected_revision", b);
            else if (value instanceof Double d) outgoing.put("expected_revision", d);
            else outgoing.put("expected_revision", (Integer)value);
            f.ack = ack(f.top, f.attempt, packet(StrictJson.canonical(outgoing)), f.before);
            f.archive.preserve(f.ack);
            assertThrows(IllegalArgumentException.class, () -> f.observer.observe(f.command, f.attempt, f.ack));
        }
        Fixture absent = new Fixture(ArmyWindowCodec.Kind.RESULTS, "closed_verified"); old = absent.ack;
        var historical = new NativeActionPort.AckReceived(old.requestId(), true, old.originalResultToken(), old.originalFrame(), old.originalPacket(), old.outbound());
        assertThrows(IllegalArgumentException.class, () -> absent.observer.observe(absent.command, absent.attempt, historical));
    }

    @Test void nativeFalseOrMissingAckNeverInventsAnAfterOrAnExecutedCompletion() throws Exception {
        Fixture f = new Fixture(ArmyWindowCodec.Kind.RESULTS, "closed_verified");
        ObjectNode error = StrictJson.object().put("type", "command_result").put("protocol_version", 1)
                .put("request_id", f.attempt.requestId()).put("ok", false).put("error", "state_changed");
        var refused = ack(error, f.attempt, f.ack.outbound().orElseThrow().originalPacket(), f.before);
        var pending = f.observer.observe(f.command, f.attempt, refused);
        assertInstanceOf(ActionPorts.Pending.class, pending.result()); assertTrue(pending.compatibleResult().isEmpty());
        assertEquals(0, f.port.samples.get());
        var unknown = new NativeActionPort.Unknown(f.attempt.requestId(), "lost original ACK", f.ack.outbound().orElseThrow().originalPacket(), Optional.empty());
        assertInstanceOf(ActionPorts.Pending.class, f.observer.observe(f.command, f.attempt, unknown).result());
        var query = ownerQuery(f, "visible", 2);
        for (NativeActionPort.DispatchOutcome dispatch : List.of(refused, unknown)) {
            var retained = new ActionReceipt(1, 1, f.command, ActionCodec.bodySha256(f.command),
                    new ActionState.Unknown(Optional.of(f.attempt), Optional.of(dispatch), "retained original uncertainty", List.of(f.before.originalEvidence())));
            assertFalse(f.observer.publicQueryCanObserveOriginal(retained, query, f.before, f.archive),
                    "a complete independent public QUERY does not manufacture a positive original CLOSE ACK or after basis");
        }
        assertEquals(0, f.port.samples.get());
    }

    @Test void coldOriginalRejectsWrongSchemaFieldsRequestAndSamplingClock() throws Exception {
        Fixture f = new Fixture(ArmyWindowCodec.Kind.OVERVIEW, "verification_pending");
        var pending = assertInstanceOf(ActionPorts.Pending.class, f.observer.observe(f.command, f.attempt, f.ack).result());
        ObjectNode original = (ObjectNode)StrictJson.parse(f.archive.loadMaterial(pending.evidence().getFirst()).bytes());
        for (int mutation = 0; mutation < 5; mutation++) {
            ObjectNode row = original.deepCopy();
            switch (mutation) {
                case 0 -> row.put("schema", "ordinary-pair-is-not-direct");
                case 1 -> row.put("request_id", "another-original-request");
                case 2 -> row.remove("sampling");
                case 3 -> row.withObject("sampling").put("started_at", true);
                case 4 -> row.withObject("sampling").put("completed_at", "2000-01-01T00:00:00Z");
                default -> throw new AssertionError();
            }
            var forged = f.pending(List.of(f.archive.preserveMaterial(new RawJson(StrictJson.canonical(row)))));
            assertThrows(RuntimeException.class, () -> NativeDirectFixedWindowObservation.load(forged, f.archive, f.loader));
        }
        var cold = NativeDirectFixedWindowObservation.load(f.pending(pending.evidence()), f.archive, f.loader);
        f.archive.nativeFrames.get(cold.sampledBasis().nativeFrame())[4] ^= 1;
        assertThrows(IllegalArgumentException.class, () -> NativeDirectFixedWindowObservation.load(f.pending(pending.evidence()), f.archive, f.loader));
    }

    @Test void laterActualReadonlyReceiptCanResolveExecutionWithZeroClosedOrGameplayCredit() throws Exception {
        for (var kind : ArmyWindowCodec.Kind.values()) {
            Fixture f = new Fixture(kind, "verification_pending");
            var initial = assertInstanceOf(ActionPorts.Pending.class, f.observer.observe(f.command, f.attempt, f.ack).result());
            var pending = f.pending(initial.evidence());
            PlanningReadReceipt query = ownerQuery(f, "visible", 2);
            var resolved = NativeDirectFixedWindowObservation.resolvePending(pending, query, f.before, f.archive, f.loader);
            assertTrue(resolved.ownerResolution().isPresent());
            assertTrue(resolved.ownerResolution().orElseThrow().retryDeferredForNativeFrame());
            var data = StrictJson.parse(resolved.ownerResolution().orElseThrow().normalizedQuery().bytes());
            assertEquals("query", data.get("operation").textValue());
            assertFalse(data.get("prior_close_execution_observation").get("close_action_credit").booleanValue());
            assertFalse(data.get("prior_close_execution_observation").get("original_action_replayed").booleanValue());
            assertTrue(data.get("close_retry_deferred_for_native_frame").booleanValue());
            assertFalse(StrictJson.parse(resolved.normalized().bytes()).get("available").booleanValue(), "the original close ACK is never rewritten");
            var completion = resolved.completion().orElseThrow();
            assertEquals(NativeDirectFixedWindowObservation.Resolution.LATER_OWNER_QUERY_RESOLVED, completion.resolution());
            completion.validate(f.command, f.attempt, f.ack, f.archive);
            assertEquals(completion, NativeDirectFixedWindowObservation.Completion.decode(completion.encode(f.archive), f.archive));
            var cold = NativeDirectFixedWindowObservation.load(f.completed(completion), f.archive, f.loader);
            assertEquals(resolved.ownerResolution().orElseThrow().normalizedQuery(), cold.ownerResolution().orElseThrow().normalizedQuery());
            assertFalse(f.completed(completion).visibleGameplay()); assertFalse(f.completed(completion).eligibleAdvance());
            assertEquals(1, f.port.samples.get(), "cold query interpretation never re-observes or resends a close");
        }
    }

    @Test void unavailableOrOldOwnerQueryRemainsPendingAndKeepsThatQueryCompleteData() throws Exception {
        for (String status : List.of("unavailable", "visible")) {
            Fixture f = new Fixture(ArmyWindowCodec.Kind.RESULTS, "verification_pending");
            var first = assertInstanceOf(ActionPorts.Pending.class, f.observer.observe(f.command, f.attempt, f.ack).result());
            var original = f.pending(first.evidence());
            var query = ownerQuery(f, status, 1);
            var observed = NativeDirectFixedWindowObservation.resolvePending(original, query, f.before, f.archive, f.loader);
            assertTrue(observed.completion().isEmpty()); assertTrue(observed.ownerResolution().isEmpty());
            var captured = observed.ownerQuery().orElseThrow(); assertFalse(captured.executionResolved());
            assertEquals(status, StrictJson.parse(captured.normalizedQuery().bytes()).get("status").textValue());
            var cold = NativeDirectFixedWindowObservation.load(f.pending(List.of(observed.basis())), f.archive, f.loader);
            assertEquals(captured.normalizedQuery(), cold.ownerQuery().orElseThrow().normalizedQuery());
            assertTrue(cold.completion().isEmpty());
        }
    }

    @Test void producedPriorOwnerMetadataUsesTheSolePublicUint64CodecWithoutPrecisionLoss() throws Exception {
        Fixture f = new Fixture(ArmyWindowCodec.Kind.RESULTS, "verification_pending");
        BigInteger maximum = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE), previous = maximum.subtract(BigInteger.ONE);
        for (ObjectNode row : List.of((ObjectNode)f.top.get("result"), (ObjectNode)f.top.get(f.kind.ownerKey()))) {
            row.put("ticket_sequence", previous).put("pump_epoch", previous);
            if (row.has("completed_sequence")) row.put("executor_started_sequence", previous).put("completed_sequence", previous);
        }
        f.replaceAck();
        var initial = assertInstanceOf(ActionPorts.Pending.class, f.observer.observe(f.command, f.attempt, f.ack).result());
        var resolved = NativeDirectFixedWindowObservation.resolvePending(f.pending(initial.evidence()), ownerQuery(f, "visible", maximum),
                f.before, f.archive, f.loader);
        var numeric = DriverJson.object(resolved.ownerResolution().orElseThrow().normalizedQuery().bytes(), DriverJson.MAX_NATIVE_BYTES);
        var context = new ArmyTypes.Context(f.before.identity(), f.before.source(), f.before.sessionId(), DEADLINE);
        RawJson encoded = ArmyPublicWire.encodeExactSourceBound(numeric, context);
        assertEquals(previous.toString(), StrictJson.parse(encoded.bytes()).get("prior_close_execution_observation")
                .get("original_owner_receipt").get("ticket_sequence").textValue());
        assertEquals(maximum.toString(), StrictJson.parse(encoded.bytes()).get("ticket_sequence").textValue());
        assertEquals(numeric, ArmyPublicWire.decodeExactSourceBound(encoded, context));
    }

    @Test void dataContinuationAndKnownReceiptCannotReplaceTheInstalledPrivateRootAuthority() throws Exception {
        Fixture f = new Fixture(ArmyWindowCodec.Kind.RESULTS, "verification_pending");
        var first = assertInstanceOf(ActionPorts.Pending.class, f.observer.observe(f.command, f.attempt, f.ack).result());
        var pending = f.pending(first.evidence()); var query = ownerQuery(f, "visible", 2);
        DirectFixedWindowQueryContinuation decodedDataOnly = new DirectFixedWindowQueryContinuation() {
            @Override public String actionId() { return f.command.actionId(); }
            @Override public PlanningReadReceipt queryReceipt() { return query; }
            @Override public ExactRef queryRef() { return f.archive.readReferenceOf(query); }
            @Override public Instant deadline() { return DEADLINE; }
        };
        assertThrows(java.io.IOException.class, () -> f.observer.withCapturedOwnerQuery(decodedDataOnly, pending,
                f.before, new RootReadContractCatalog(List.of(), List.of()), f.archive,
                () -> { throw new AssertionError("a decoded DATA token cannot enter the central reducer"); }));
        assertEquals(1, f.port.samples.get(), "denied captured-query ingress neither observes again nor sends another query");
    }

    @Test void publicOwnerQueryRequiresTheSameGameplayRequestAndRejectsReconSubstitution() throws Exception {
        Fixture f = new Fixture(ArmyWindowCodec.Kind.RESULTS, "verification_pending");
        PlanningReadRequest actual = ownerQuery(f, "visible", 2).request();
        assertDoesNotThrow(() -> NativeDirectFixedWindowObservation.requirePublicOwnerQuery(actual, f.before));
        var foreign = new PlanningReadRequest(f.before.identity(), f.before.source(), "other-session", actual.operation(), actual.arguments(), DEADLINE);
        assertThrows(IllegalArgumentException.class, () -> NativeDirectFixedWindowObservation.requirePublicOwnerQuery(foreign, f.before));
        var close = new PlanningReadRequest(f.before.identity(), f.before.source(), f.before.sessionId(), f.command.operation(), actual.arguments(), DEADLINE);
        assertThrows(IllegalArgumentException.class, () -> NativeDirectFixedWindowObservation.requirePublicOwnerQuery(close, f.before));
        // These are explicit identity DATA only, never a writer/physical qualification or a positive callback.
        ExactRef driver = softwareRole("driver");
        var identity = new ReconciliationIdentity(f.before.identity(), f.before.source(), f.before.sessionId(), f.before.connectionGeneration(),
                new ReconciliationIdentity.Pending(f.command.actionId(), ActionCodec.bodySha256(f.command), f.attempt.requestId(),
                        f.before.identity(), softwareRole("receipt"), driver),
                new ReconciliationIdentity.Evidence(softwareRole("native"), softwareRole("hello"), softwareRole("heartbeat"),
                        softwareRole("manifest"), driver, softwareRole("qualification")), f.before.observedAt());
        var recon = PlanningReadRequest.newReconciliation(identity, actual.operation(), actual.arguments(), DEADLINE);
        assertInstanceOf(CommandOrigin.Reconciliation.class, recon.origin());
        assertThrows(IllegalArgumentException.class, () -> NativeDirectFixedWindowObservation.requirePublicOwnerQuery(recon, f.before));
        assertEquals(0, f.port.samples.get(), "request-role validation sends no query and obtains no after snapshot");
    }

    @Test void bothOriginalPublicPublishResolversMatchTheRetainedQueryAndColdPublicSerde() throws Exception {
        var cases = new java.util.ArrayList<OracleCase>();
        for (var kind : ArmyWindowCodec.Kind.values()) for (String status : List.of("absent", "hidden", "visible", "unavailable"))
            for (int ticket : List.of(1, 2)) {
                Fixture f = new Fixture(kind, "verification_pending");
                var initial = assertInstanceOf(ActionPorts.Pending.class, f.observer.observe(f.command, f.attempt, f.ack).result());
                var pending = f.pending(initial.evidence()); PlanningReadReceipt query = ownerQuery(f, status, ticket);
                NativeDirectFixedWindowObservation.requirePublicOwnerQuery(query.request(), f.before);
                assertTrue(f.observer.publicQueryCanObserveOriginal(pending, query, f.before, f.archive),
                        "unavailable or unchanged owner counters retain the original unresolved owner-query archive path");
                var resolved = NativeDirectFixedWindowObservation.resolvePending(pending, query, f.before, f.archive, f.loader);
                var context = new ArmyTypes.Context(f.before.identity(), f.before.source(), f.before.sessionId(), DEADLINE);
                var decoded = ArmyWindowCodec.decode(kind, ArmyWindowCodec.Operation.QUERY, query.original().originalFrame().bytes(),
                        query.requestId(), context, f.before.connectionGeneration(), ArmyWindowCodec.driverGeneration(f.before));
                var prior = NativeDirectFixedWindowObservation.load(pending, f.archive, f.loader);
                cases.add(new OracleCase(kind, prior.normalized(), new RawJson(StrictJson.canonical(decoded.normalized())), resolved.ownerQuery().orElseThrow().normalizedQuery(),
                        resolved.ownerQuery().orElseThrow().executionResolved()));
                ActionReceipt retained = resolved.completion().isPresent() ? f.completed(resolved.completion().orElseThrow()) : f.pending(List.of(resolved.basis()));
                var cold = NativeDirectFixedWindowObservation.load(retained, f.archive, f.loader).ownerQuery().orElseThrow();
                assertEquals(resolved.ownerQuery().orElseThrow(), cold);
                var numeric = DriverJson.object(cold.normalizedQuery().bytes(), DriverJson.MAX_NATIVE_BYTES);
                assertEquals(numeric, ArmyPublicWire.decodeExactSourceBound(ArmyPublicWire.encodeExactSourceBound(numeric, context), context));
                assertEquals(1, f.port.samples.get(), "consuming the retained public QUERY never resends CLOSE or observes again");
                assertFalse(retained.visibleGameplay()); assertFalse(retained.eligibleAdvance());
            }
        assertOriginalPublishCases(cases);
    }

    @Test void incompatibleCurrentQueriesRemainIndependentAndMalformedOriginalsStillFail() throws Exception {
        var cases = new java.util.ArrayList<OracleCase>();
        for (var kind : ArmyWindowCodec.Kind.values()) for (int drift = 0; drift < 6; drift++) {
            Fixture f = new Fixture(kind, "verification_pending");
            var first = assertInstanceOf(ActionPorts.Pending.class, f.observer.observe(f.command, f.attempt, f.ack).result());
            var pending = f.pending(first.evidence());
            f.port.current = switch (drift) {
                case 0 -> frame(9, 73, 53144328, true, true, 1);
                case 1 -> frame(9, 73, 53144328, true, true, 0, NATIVE_GENERATION.add(BigInteger.ONE), "held-session");
                case 2 -> frame(8, 73, 53144328, true, true, 0);
                case 3 -> frame(9, 73, 53144304, true, true, 0);
                case 4 -> frame(9, 73, 53144328, true, true, 0, NATIVE_GENERATION, "new-held-session");
                case 5 -> f.port.current;
                default -> throw new AssertionError();
            };
            var current = f.held.observe(DEADLINE);
            var query = ownerQuery(f, current, "visible", BigInteger.TWO, drift == 5 ? UUID.randomUUID() : f.ack.custody().orElseThrow().custodyEpoch());
            int materials = f.archive.materials.size(), reads = f.archive.reads.size(), nativeFrames = f.archive.nativeFrames.size();
            assertFalse(f.observer.publicQueryCanObserveOriginal(pending, query, current, f.archive));
            assertEquals(materials, f.archive.materials.size()); assertEquals(reads, f.archive.reads.size());
            assertEquals(nativeFrames, f.archive.nativeFrames.size()); assertInstanceOf(ActionState.Unknown.class, pending.state());
            assertEquals(1, f.port.samples.get(), "eligibility must not sample after, resend or preserve new evidence");
            var context = new ArmyTypes.Context(current.identity(), current.source(), current.sessionId(), DEADLINE);
            var decoded = ArmyWindowCodec.decode(kind, ArmyWindowCodec.Operation.QUERY, query.original().originalFrame().bytes(),
                    query.requestId(), context, current.connectionGeneration(), ArmyWindowCodec.driverGeneration(current));
            RawJson raw = new RawJson(StrictJson.canonical(decoded.normalized()));
            // Session and receiver-epoch provenance are additional Java transport identities;
            // the original Python business result has no corresponding fields to compare.
            if (drift < 4) cases.add(new OracleCase(kind, NativeDirectFixedWindowObservation.load(pending, f.archive, f.loader).normalized(), raw, raw, false));
            var numeric = DriverJson.object(raw.bytes(), DriverJson.MAX_NATIVE_BYTES);
            assertEquals(numeric, ArmyPublicWire.decodeExactSourceBound(ArmyPublicWire.encodeExactSourceBound(numeric, context), context));
            var original = query.original(); byte[] corrupt = original.originalPacket(); corrupt[0] ^= 1;
            var altered = new NativeActionPort.AckReceived(original.requestId(), original.nativeOk(), original.originalResultToken(), original.originalFrame(),
                    corrupt, original.outbound(), original.custody());
            var forged = new PlanningReadReceipt(query.request(), query.contractId(), query.requestId(), query.before(), query.after(), altered);
            f.archive.preserve(altered); f.archive.preserveRead(forged);
            assertThrows(RuntimeException.class, () -> f.observer.publicQueryCanObserveOriginal(pending, forged, current, f.archive),
                    "an incompatible current binding cannot hide altered original packet bytes");
        }
        assertOriginalPublishCases(cases);
        Fixture f = new Fixture(ArmyWindowCodec.Kind.RESULTS, "verification_pending");
        var first = assertInstanceOf(ActionPorts.Pending.class, f.observer.observe(f.command, f.attempt, f.ack).result());
        var pending = f.pending(first.evidence()); var query = ownerQuery(f, "visible", 2); var original = query.original();
        var custody = original.custody().orElseThrow();
        var early = new NativeRequestChronology(custody.session(), custody.custodyEpoch(), custody.requestId(), custody.originalRequest(), custody.originalResponse(),
                new NativeRequestChronology.Event(BigInteger.ONE, custody.writeEntered().observedAt()),
                new NativeRequestChronology.Event(BigInteger.TWO, custody.writeCompleted().observedAt()),
                new NativeRequestChronology.Event(BigInteger.valueOf(3), custody.responseReceived().observedAt()));
        var reordered = new NativeActionPort.AckReceived(original.requestId(), original.nativeOk(), original.originalResultToken(), original.originalFrame(),
                original.originalPacket(), original.outbound(), Optional.of(early));
        var invalidOrder = new PlanningReadReceipt(query.request(), query.contractId(), query.requestId(), query.before(), query.after(), reordered);
        f.archive.preserve(reordered); f.archive.preserveRead(invalidOrder);
        assertThrows(IllegalArgumentException.class, () -> f.observer.publicQueryCanObserveOriginal(pending, invalidOrder, f.before, f.archive),
                "the same held connection still requires the original strict after-ACK event order");
    }

    private static void assertOriginalPublishCases(List<OracleCase> cases) throws Exception {
        var rows = originalPublishOracle(cases);
        assertEquals(cases.size(), rows.size());
        for (int index = 0; index < cases.size(); index++) {
            OracleCase expected = cases.get(index); var actual = rows.get(index);
            assertEquals(expected.resolved(), actual.get("pending_cleared").booleanValue(), expected.kind() + " pending latch");
            assertEquals(DriverJson.object(expected.normalized().bytes(), DriverJson.MAX_NATIVE_BYTES),
                    DriverJson.object(StrictJson.canonical(actual.get("result")), DriverJson.MAX_NATIVE_BYTES), expected.kind() + " full original QUERY result");
            assertEquals(actual.get("result"), actual.get("published"), "same original public call publishes its full result");
            if (expected.resolved()) {
                assertFalse(actual.get("result").get("prior_close_execution_observation").get("original_action_replayed").booleanValue());
                assertFalse(actual.get("result").get("prior_close_execution_observation").get("close_action_credit").booleanValue());
            }
        }
    }

    private record OracleCase(ArmyWindowCodec.Kind kind, RawJson close, RawJson query, RawJson normalized, boolean resolved) { }
    private static ExactRef softwareRole(String role) {
        byte[] body = role.getBytes(java.nio.charset.StandardCharsets.UTF_8);
        return new ExactRef("controlled-query-role/" + role, body.length, ActionCodec.sha256(body));
    }
    private static com.fasterxml.jackson.databind.JsonNode originalPublishOracle(List<OracleCase> cases) throws Exception {
        java.nio.file.Path root = requiredOriginalPath("xar.repository.root"), python = requiredOriginalPath("xar.python");
        String[][] pins = {
                {"war_declared_overview_transport.py", "52183d4339e407bdbc29f9b222d28a7b80c5691a5b67e6ef158e9313a6f77b4c"},
                {"war_results_window_transport.py", "e1a3d7d5ae36ccf2a17055d166742f3fd49b11529bdbd383c7b2b9d5640fd86e"}};
        for (String[] pin : pins) assertEquals(pin[1], ActionCodec.sha256(java.nio.file.Files.readAllBytes(root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge").resolve(pin[0]))));
        var input = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode();
        for (OracleCase item : cases) {
            var row = StrictJson.object().put("kind", item.kind().name());
            row.set("close", StrictJson.parse(item.close().bytes())); row.set("query", StrictJson.parse(item.query().bytes())); input.add(row);
        }
        java.nio.file.Path output = java.nio.file.Files.createTempFile("original-window-publish-", ".json");
        String program = """
            import copy,json,sys,threading
            from pathlib import Path
            from types import SimpleNamespace
            root=Path(sys.argv[1]);sys.dont_write_bytecode=True
            sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            from xar_autoplayer.bridge import war_declared_overview_transport as O,war_results_window_transport as R
            rows=[]
            for row in json.load(sys.stdin):
                module,prefix=(O,'_war_declared_overview') if row['kind']=='OVERVIEW' else (R,'_war_results_window')
                previous=row['close'];answer=copy.deepcopy(row['query'])
                pending=dict(status='verification_pending',step=previous['step'],collectable=False,
                    completed_response=previous,native_request_id=previous['native_request_id'],
                    native_generation=previous['connection_generation'],
                    binding=dict(native_revision=previous['queried_native_revision'],date_raw=previous['queried_date_raw']))
                driver=SimpleNamespace(_driver_state_lock=threading.RLock())
                setattr(driver,prefix+'_close_pending',pending);setattr(driver,prefix+'_attempt',1)
                assert module._publish(driver,answer,1) is True
                rows.append(dict(result=answer,pending_cleared=getattr(driver,prefix+'_close_pending') is None,
                    published=getattr(driver,prefix+'_observation')['result']))
            print(json.dumps(rows,allow_nan=False,separators=(',',':')))
            """;
        try {
            var builder = new ProcessBuilder(python.toString(), "-I", "-B", "-X", "utf8", "-c", program, root.toString()).directory(root.toFile());
            builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
            var process = builder.redirectErrorStream(true).redirectOutput(output.toFile()).start();
            try (var stream = process.getOutputStream()) { stream.write(StrictJson.canonical(input, 1024 * 1024)); }
            boolean ended = process.waitFor(45, java.util.concurrent.TimeUnit.SECONDS);
            if (!ended) { process.destroyForcibly(); process.waitFor(5, java.util.concurrent.TimeUnit.SECONDS); }
            assertTrue(ended, "original two window publish oracle timed out");
            byte[] result = java.nio.file.Files.readAllBytes(output);
            assertTrue(result.length <= 1024 * 1024, "bounded original QUERY oracle output required");
            assertEquals(0, process.exitValue(), new String(result, java.nio.charset.StandardCharsets.UTF_8));
            return StrictJson.parse(result, StrictJson.EXPLICIT_MAX_BYTES);
        } finally { java.nio.file.Files.deleteIfExists(output); }
    }
    private static java.nio.file.Path requiredOriginalPath(String property) throws java.io.IOException {
        String configured = System.getProperty(property);
        if (configured == null || configured.isBlank()) throw new IllegalStateException("NOT_RUN_REQUIRED_ORIGINAL_INPUT: " + property);
        var path = java.nio.file.Path.of(configured); assertTrue(path.isAbsolute()); return path.toRealPath();
    }

    /** Real strict public window decoder and receipt DATA; no Root/Known/private writer token is constructed. */
    private static PlanningReadReceipt ownerQuery(Fixture f, String status, int ticket) {
        return ownerQuery(f, status, BigInteger.valueOf(ticket));
    }
    private static PlanningReadReceipt ownerQuery(Fixture f, String status, BigInteger ticket) {
        return ownerQuery(f, f.before, status, ticket, f.ack.custody().orElseThrow().custodyEpoch());
    }
    private static PlanningReadReceipt ownerQuery(Fixture f, DriverObservationAssembler.Complete current, String status, BigInteger ticket, UUID custodyEpoch) {
        String id = "actual-followup-query-" + ticket + "-" + status;
        ObjectNode top = top(f.kind, status.equals("unavailable") ? "unavailable" : "already_hidden", id, 1);
        ((ObjectNode)top.get("result")).put("played_character_id", current.identity().frame().identity().player())
                .put("native_revision", current.identity().frame().identity().nativeRevision()).put("date_raw", current.identity().frame().identity().dateRaw())
                .put("connection_generation", current.connectionGeneration());
        ((ObjectNode)top.get(f.kind.ownerKey())).put("date_raw", current.identity().frame().identity().dateRaw())
                .put("connection_generation", current.connectionGeneration());
        ((ObjectNode)top.get("result")).put("ticket_sequence", ticket).put("pump_epoch", ticket);
        ((ObjectNode)top.get(f.kind.ownerKey())).put("ticket_sequence", ticket).put("pump_epoch", ticket)
                .put("executor_started_sequence", ticket).put("completed_sequence", ticket);
        ObjectNode leaf = (ObjectNode)top.get("result"); boolean available = !status.equals("unavailable"), visible = status.equals("visible"),
                present = available && !status.equals("absent");
        leaf.put("operation", "query").put("status", status).put("available", available).put("accepted", available)
                .put("window_present", present).put("effective_visible", visible).put("post_window_present", present)
                .put("post_effective_visible", visible).put("dispatch_attempted", false).put("dispatch_invoked", false).put("native_handled", false)
                .put("closure_verified", false).put("button_name", "");
        var operation = new OperationKey(f.kind.step(ArmyWindowCodec.Operation.QUERY));
        var planning = new PlanningReadRequest(current.identity(), current.source(), current.sessionId(), operation,
                new OpportunityJson.Obj(Map.of()), DEADLINE);
        var guard = new GuardEvidence(current.identity(), current.source(), current.sessionId(), current.connectionGeneration(), operation,
                current.originalEvidence(), current.originalEvidence(), "software-query-data-no-Root", current.observedAt(), DEADLINE);
        var bound = new PlanningReadGuard(guard, true, true, true, current.fullBindingSha256());
        byte[] outbound = packet(StrictJson.canonical(request(operation.value(), id, current.identity().frame().identity().nativeRevision())));
        byte[] response = packet(StrictJson.canonical(top)); Instant time = f.attempt.submittedAt().plusSeconds(1);
        var original = new NativeActionPort.AckReceived(id, true, Optional.of(new RawJson(StrictJson.canonical(leaf))),
                new RawJson(StrictJson.canonical(top)), response, Optional.of(new NativeActionPort.OutboundPacket(id, outbound)),
                Optional.of(new NativeRequestChronology(new NativeObservationPort.TransportSession(current.identity().machineId(), current.identity().game(),
                        current.connectionGeneration(), current.sessionId()), custodyEpoch, id,
                        NativeRequestChronology.PacketIdentity.of(outbound), NativeRequestChronology.PacketIdentity.of(response),
                        new NativeRequestChronology.Event(BigInteger.valueOf(4), time),
                        new NativeRequestChronology.Event(BigInteger.valueOf(5), time.plusMillis(10)),
                        new NativeRequestChronology.Event(BigInteger.valueOf(6), time.plusMillis(20)))));
        var receipt = new PlanningReadReceipt(planning, "controlled-real-window-decoder", id, bound, bound, original);
        // Exercise the same strict production decoder before the original enters the explicit cold DATA archive.
        ArmyWindowCodec.decode(f.kind, ArmyWindowCodec.Operation.QUERY, original.originalFrame().bytes(), id,
                new ArmyTypes.Context(current.identity(), current.source(), current.sessionId(), DEADLINE),
                current.connectionGeneration(), ArmyWindowCodec.driverGeneration(current));
        f.archive.preserve(original); f.archive.preserveRead(receipt); return receipt;
    }

    private static final class Fixture {
        final ArmyWindowCodec.Kind kind; final Archive archive = new Archive(); final Endpoint port = new Endpoint();
        final HeldDriverObservationPort held; final DriverObservationAssembler.Complete before;
        final DriverFrameEvidenceLoader loader = new DriverFrameEvidenceLoader(new DriverObservationAssembler());
        final NativeDirectFixedWindowObservation observer; final ActionCommand command; final ActionState.Attempt attempt;
        ObjectNode top; NativeActionPort.AckReceived ack;
        Fixture(ArmyWindowCodec.Kind kind, String status) throws Exception {
            this.kind = kind;
            held = new HeldDriverObservationPort(port, actual -> new DriverObservationFacts.Known(facts(actual, archive)),
                    archive::preserveNativeFrame, new DriverObservationAssembler(), 8);
            before = held.observe(DEADLINE);
            var operation = new OperationKey(kind.step(ArmyWindowCodec.Operation.CLOSE));
            var args = new ArmyOrdinaryActionArguments(kind == ArmyWindowCodec.Kind.OVERVIEW
                    ? ArmyOrdinaryActionArguments.Kind.CLOSE_WAR_DECLARED_OVERVIEW_V1 : ArmyOrdinaryActionArguments.Kind.CLOSE_WAR_RESULTS_WINDOW_V1,
                    new RawJson(StrictJson.canonical(StrictJson.object().put("expected_revision", before.identity().frame().revision()))), List.of(),
                    ArmyOrdinaryActionArguments.ExecutionProfile.DIRECT_FIXED_WINDOW, Optional.empty());
            command = new ActionCommand("controlled-direct-" + kind, before.identity(), before.source(), before.sessionId(), operation, args.encode(),
                    NativeDirectFixedWindowObservation.expected(before.identity(), before.source(), operation, args.raw()),
                    new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), DEADLINE);
            var guard = new GuardEvidence(before.identity(), before.source(), before.sessionId(), before.connectionGeneration(), operation,
                    before.originalEvidence(), before.originalEvidence(), "controlled-software-no-Root-authority", before.observedAt(), DEADLINE);
            attempt = new ActionState.Attempt("original-close-" + kind, Instant.now().minusSeconds(2), guard,
                    new NativeRequest(operation.value(), Optional.of("game.command." + operation.value()), new RawJson(new byte[]{'{','}'})));
            archive.preserveRequest(attempt.preparedRequest()); top = top(kind, status, attempt.requestId(), 1);
            replaceAck(); observer = new NativeDirectFixedWindowObservation(new NativeEffectSnapshots(held, archive, loader));
        }
        void replaceAck() {
            ack = ack(top, attempt, packet(StrictJson.canonical(request(command.operation().value(), attempt.requestId(), before.identity().frame().identity().nativeRevision()))), before);
            archive.preserve(ack);
        }
        ActionReceipt completed(NativeDirectFixedWindowObservation.Completion completion) {
            return new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command),
                    new ActionState.Settled(attempt, ack, new ActionState.DirectFixedWindowCompleted(completion)));
        }
        ActionReceipt pending(List<ExactRef> evidence) {
            return new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command),
                    new ActionState.Unknown(Optional.of(attempt), Optional.of(ack), "actual unavailable close", evidence));
        }
    }
    private static final class Endpoint implements NativeSnapshotWaitPort {
        NativeObservationPort.ObservedFrame current = frame(9, 73, 53144328, true, true, 0);
        final AtomicInteger samples = new AtomicInteger();
        @Override public NativeObservationPort.ObservedFrame observe(Instant deadline) { return current; }
        @Override public NativeObservationPort.ObservedFrame currentSnapshot(Instant deadline) { samples.incrementAndGet(); return current; }
        @Override public WaitResult waitForSnapshot(Instant until, Instant capture) { throw new AssertionError("direct sample must not pump or issue a native query"); }
    }
    private static DriverObservationFacts facts(NativeObservationPort.ObservedFrame actual, Archive archive) {
        var driver = DriverStateAssemblerTest.known(); RawJson full = new RawJson(driver.driver().encode());
        var fullRef = archive.preserveMaterial(full);
        RawJson manifest = DriverObservationEvidenceReader.encode(driver, actual, actual.nativeRevision(), 1,
                DriverStateAssemblerTest.source(), new OpportunityJson.Obj(Map.of()), fullRef);
        return DriverObservationEvidenceReader.decode(archive.preserveMaterial(manifest), manifest, full, actual);
    }
    private static NativeObservationPort.ObservedFrame frame(int revision, int actor, int date, boolean paused, boolean ready, int driverGeneration) {
        return frame(revision, actor, date, paused, ready, driverGeneration, NATIVE_GENERATION, "held-session");
    }
    private static NativeObservationPort.ObservedFrame frame(int revision, int actor, int date, boolean paused, boolean ready, int driverGeneration,
            BigInteger nativeGeneration, String sessionId) {
        ObjectNode state = StrictJson.object().put("paused", paused).put("map_ready", ready).put("speed", 3).put("date_raw", date);
        state.putObject("played_character").put("character_id", actor).put("alive", true);
        state.putNull("active_event").putNull("pending_character_interaction").putNull("one_life_terminal_reason");
        state.putArray("active_wars"); state.putArray("player_armies");
        var diagnostics = state.putObject("diagnostics").put("connection_generation", driverGeneration);
        diagnostics.putObject("hello").put("expected_ck3_version", "1.20.0.4").put("expected_ck3_sha256", BUILD)
                .put("connection_generation", nativeGeneration);
        ObjectNode row = StrictJson.object().put("protocol_version", 1).put("type", "state_snapshot")
                .put("snapshot_id", "snapshot-" + revision).put("revision", revision); row.set("state", state);
        return new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("test-machine", DriverStateAssemblerTest.game(),
                nativeGeneration, sessionId), "snapshot-" + revision, BigInteger.valueOf(revision),
                new RawJson(StrictJson.canonical(state)), packet(StrictJson.canonical(row)), Instant.parse("2026-10-23T16:00:00Z"));
    }
    private static ObjectNode request(String operation, String id, BigInteger revision) {
        return StrictJson.object().put("type", "execute_step").put("protocol_version", 1).put("request_id", id).put("step", operation).put("expected_revision", revision);
    }
    private static NativeActionPort.AckReceived ack(ObjectNode top, ActionState.Attempt attempt, byte[] outbound, DriverObservationAssembler.Complete before) {
        byte[] body = StrictJson.canonical(top), response = packet(body);
        var session = new NativeObservationPort.TransportSession(before.identity().machineId(), before.identity().game(), before.connectionGeneration(), before.sessionId());
        var start = attempt.submittedAt();
        var custody = new NativeRequestChronology(session, UUID.fromString("b3ba5af6-6b14-4d50-ad24-30213979b501"), attempt.requestId(),
                NativeRequestChronology.PacketIdentity.of(outbound), NativeRequestChronology.PacketIdentity.of(response),
                new NativeRequestChronology.Event(BigInteger.ONE, start.plusMillis(10)),
                new NativeRequestChronology.Event(BigInteger.TWO, start.plusMillis(20)),
                new NativeRequestChronology.Event(BigInteger.valueOf(3), start.plusMillis(30)));
        return new NativeActionPort.AckReceived(attempt.requestId(), top.get("ok").booleanValue(),
                top.has("result") ? Optional.of(new RawJson(StrictJson.canonical(top.get("result")))) : Optional.empty(),
                new RawJson(body), response, Optional.of(new NativeActionPort.OutboundPacket(attempt.requestId(), outbound)), Optional.of(custody));
    }
    private static ObjectNode top(ArmyWindowCodec.Kind kind, String status, String id, int ticket) {
        boolean available = !Set.of("verification_pending", "unavailable").contains(status), attempted = status.equals("closed_verified") || status.equals("verification_pending");
        boolean absent = status.equals("already_absent"), visible = !Set.of("already_absent", "already_hidden", "unavailable").contains(status);
        String suffix = kind == ArmyWindowCodec.Kind.OVERVIEW ? "war-declared-overview" : "war-results-window";
        ObjectNode leaf = StrictJson.object().put("schema", "ck3-" + suffix + "-v1").put("operation", "close")
                .put("window_name", kind == ArmyWindowCodec.Kind.OVERVIEW ? "war_declared_overview" : "war_results")
                .put("status", status).put("available", available).put("accepted", status.equals("closed_verified"))
                .put("root_observed", !status.equals("unavailable")).put("window_present", !absent && !status.equals("unavailable"))
                .put("effective_visible", visible).put("dispatch_attempted", attempted).put("dispatch_invoked", attempted).put("native_handled", attempted)
                .put("post_observed", !status.equals("unavailable")).put("post_window_present", status.equals("verification_pending") || status.equals("already_hidden"))
                .put("post_effective_visible", status.equals("verification_pending")).put("scope_unchanged", !status.equals("unavailable"))
                .put("closure_verified", status.equals("closed_verified")).put("application_owner_thread_verified", true).put("paused", true)
                .put("unavailable_reason", available ? "" : "controlled actual window uncertainty").put("button_name", attempted ? (kind == ArmyWindowCodec.Kind.OVERVIEW ? "dismiss" : "close_button") : "")
                .put("request_id", id).put("root_observation_source", status.equals("unavailable") ? "" : "guarded_top_level_and_complete_owner_tree")
                .put("post_observation_source", status.equals("unavailable") ? "" : "guarded_top_level_and_complete_owner_tree")
                .put("played_character_id", 73).put("date_raw", 53144328).put("native_revision", 9).put("connection_generation", NATIVE_GENERATION)
                .put("pump_epoch", ticket).put("thread_id", 81).put("ticket_sequence", ticket).put("game_version", "1.20.0.4").put("executable_sha256", BUILD);
        String trace = kind == ArmyWindowCodec.Kind.OVERVIEW ? "close" : "dismiss";
        leaf.put(trace + "_stage", attempted ? "callback_returned" : "not_attempted").put(trace + "_exception_code", 0);
        ObjectNode owner = StrictJson.object().put("request_id", id).put("ticket_sequence", ticket).put("executor_started_sequence", ticket)
                .put("completed_sequence", ticket).put("pump_epoch", ticket).put("thread_id", 81).put("date_raw", 53144328).put("connection_generation", NATIVE_GENERATION);
        ObjectNode result = StrictJson.object().put("type", "command_result").put("protocol_version", 1).put("request_id", id).put("ok", true);
        result.set("result", leaf); result.set(kind.ownerKey(), owner); return result;
    }
    private static byte[] packet(byte[] body) { return ByteBuffer.allocate(body.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array(); }
    private static final class Archive implements ActionPorts.OutcomeArchive {
        final Map<ExactRef, RawJson> materials = new HashMap<>(); final Map<ExactRef, byte[]> nativeFrames = new HashMap<>();
        final Map<ExactRef, NativeActionPort.DispatchOutcome> outcomes = new HashMap<>(); final Map<ExactRef, NativeRequest> requests = new HashMap<>();
        final Map<ExactRef, PlanningReadReceipt> reads = new HashMap<>();
        private static ExactRef ref(String role, byte[] body) { return new ExactRef("controlled/" + role + "/" + ActionCodec.sha256(body), body.length, ActionCodec.sha256(body)); }
        @Override public ExactRef preserveMaterial(RawJson raw) { var r = ref("material", raw.bytes()); materials.putIfAbsent(r, raw); return r; }
        @Override public RawJson loadMaterial(ExactRef r) { return java.util.Objects.requireNonNull(materials.get(r)); }
        @Override public RawJson loadFullMaterial(ExactRef r) { return loadMaterial(r); }
        @Override public ExactRef materialReferenceOf(RawJson raw) { var r = ref("material", raw.bytes()); assertEquals(raw, materials.get(r)); return r; }
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame raw) { var r = ref("native", raw.originalPacket()); nativeFrames.putIfAbsent(r, raw.originalPacket()); return r; }
        @Override public byte[] loadNativeFrame(ExactRef r) { return java.util.Objects.requireNonNull(nativeFrames.get(r)).clone(); }
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome raw) { byte[] bytes = DriverStateAssemblerTest.bytes(raw.toString()); var r = ref("outcome", bytes); outcomes.put(r, raw); return r; }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef r) { return java.util.Objects.requireNonNull(outcomes.get(r)); }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome raw) { return outcomes.entrySet().stream().filter(e -> e.getValue().equals(raw)).map(Map.Entry::getKey).findFirst().orElseThrow(); }
        @Override public ExactRef preserveRequest(NativeRequest raw) { var r = ref("request", DriverStateAssemblerTest.bytes(raw.toString())); requests.put(r, raw); return r; }
        @Override public NativeRequest loadRequest(ExactRef r) { return java.util.Objects.requireNonNull(requests.get(r)); }
        @Override public ExactRef requestReferenceOf(NativeRequest raw) { return requests.entrySet().stream().filter(e -> e.getValue().equals(raw)).map(Map.Entry::getKey).findFirst().orElseThrow(); }
        @Override public ExactRef preserveRead(PlanningReadReceipt raw) { var r = ref("read", DriverStateAssemblerTest.bytes(raw.toString())); reads.put(r, raw); return r; }
        @Override public PlanningReadReceipt loadRead(ExactRef r) { return java.util.Objects.requireNonNull(reads.get(r)); }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt raw) { return reads.entrySet().stream().filter(e -> e.getValue().equals(raw)).map(Map.Entry::getKey).findFirst().orElseThrow(); }
        @Override public ExactRef preserveRecord(ActionRecord raw) { throw new UnsupportedOperationException("no writer authority in controlled DATA fixture"); }
        @Override public ActionRecord loadRecord(ExactRef r) { throw new UnsupportedOperationException(); }
        @Override public ExactRef recordReferenceOf(ActionRecord raw) { throw new UnsupportedOperationException(); }
        @Override public ExactRef preserveReceipt(ActionReceipt raw) { throw new UnsupportedOperationException(); }
        @Override public ActionReceipt loadReceipt(ExactRef r) { throw new UnsupportedOperationException(); }
        @Override public ExactRef receiptReferenceOf(ActionReceipt raw) { throw new UnsupportedOperationException(); }
    }
}
