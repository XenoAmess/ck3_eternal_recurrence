package org.xar.ck3.control.application.routecontact;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.routecontact.RouteContactModel.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.AdvanceClock;
import org.xar.ck3.control.application.advance.AdvancePlan;
import org.xar.ck3.control.application.advance.AdvanceResult;
import org.xar.ck3.control.application.advance.AdvanceObservationPort;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.DriverSurvivingHistory;
import org.xar.ck3.control.application.history.RouteContactHistoryAdapter;
import org.xar.ck3.control.application.routecontact.RouteContactComposite.*;
import org.xar.ck3.control.contracts.ExactRef;

/** The domain's real archive producer/reader/result consumer, with only physical IO replaced. */
final class RouteContactEvidenceTest {
    static final class Archive implements ActionPorts.OutcomeArchive {
        private final Map<ExactRef, RawJson> materials = new LinkedHashMap<>();
        private final Map<ExactRef, ActionReceipt> receipts = new LinkedHashMap<>();
        @Override public ExactRef preserveMaterial(RawJson raw) { ExactRef ref = new ExactRef("D:/fixture/material/" + ActionCodec.sha256(raw.bytes()), raw.bytes().length, ActionCodec.sha256(raw.bytes())); materials.put(ref, raw); return ref; }
        @Override public RawJson loadMaterial(ExactRef ref) { return new RawJson(Optional.ofNullable(materials.get(ref)).orElseThrow().bytes()); }
        @Override public RawJson loadFullMaterial(ExactRef ref) { return RawJson.fullMaterial(Optional.ofNullable(materials.get(ref)).orElseThrow().bytes()); }
        @Override public ExactRef materialReferenceOf(RawJson raw) { return materials.entrySet().stream().filter(item -> item.getValue().equals(raw)).map(Map.Entry::getKey).findFirst().orElseThrow(); }
        @Override public ExactRef preserveReceipt(ActionReceipt receipt) { byte[] body = (receipt.command().actionId() + receipt.sequence() + receipt.bodySha256()).getBytes(StandardCharsets.UTF_8); ExactRef ref = new ExactRef("D:/fixture/receipt/" + ActionCodec.sha256(body), body.length, ActionCodec.sha256(body)); receipts.put(ref, receipt); return ref; }
        @Override public ActionReceipt loadReceipt(ExactRef ref) { return Optional.ofNullable(receipts.get(ref)).orElseThrow(); }
        @Override public ExactRef receiptReferenceOf(ActionReceipt receipt) { return receipts.entrySet().stream().filter(item -> item.getValue().equals(receipt)).map(Map.Entry::getKey).findFirst().orElseThrow(); }
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value) { throw new UnsupportedOperationException(); }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef value) { throw new UnsupportedOperationException(); }
        @Override public ExactRef preserveRequest(NativeRequest value) { throw new UnsupportedOperationException(); }
        @Override public NativeRequest loadRequest(ExactRef value) { throw new UnsupportedOperationException(); }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value) { throw new UnsupportedOperationException(); }
        @Override public ExactRef requestReferenceOf(NativeRequest value) { throw new UnsupportedOperationException(); }
        @Override public ExactRef preserveRead(PlanningReadReceipt value) { throw new UnsupportedOperationException(); }
        @Override public PlanningReadReceipt loadRead(ExactRef value) { throw new UnsupportedOperationException(); }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt value) { throw new UnsupportedOperationException(); }
        @Override public ExactRef preserveRecord(ActionRecord value) { throw new UnsupportedOperationException(); }
        @Override public ActionRecord loadRecord(ExactRef value) { throw new UnsupportedOperationException(); }
        @Override public ExactRef recordReferenceOf(ActionRecord value) { throw new UnsupportedOperationException(); }
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value) { throw new UnsupportedOperationException(); }
        @Override public byte[] loadNativeFrame(ExactRef value) { throw new UnsupportedOperationException(); }
    }
    private static Proof proof(boolean strict) { return RouteContactPostconditionsTest.proof(strict); }
    /** Actual report codec over explicit controller-test DATA; no Native clock or managed Root qualification. */
    static ClockResult reportedExact(ActionCommand parent, AdvanceObservationPort.Frame start, AdvanceObservationPort.Frame end, int speed) {
        var from = start.identity().frame().identity().dateRaw(); var to = end.identity().frame().identity().dateRaw();
        String policy = speed == 1 ? "exact_one_day_unavoidable_contact" : "exact_one_day_contact_free_speed_" + speed;
        var plan = new AdvancePlan(from, from.add(AdvancePlan.DAY), 1, speed, policy, true, AdvancePlan.ClockMode.POLLED, Optional.empty());
        var diagnostic = new AdvanceClock.Diagnostics(from, to, to.subtract(from).divide(AdvancePlan.DAY).intValueExact(), 1, speed, policy,
                AdvanceClock.ProgressStatus.POSTCONDITION, Optional.empty(), Optional.empty(), false, List.of(), 17, Optional.empty());
        var original = new AdvanceResult(parent, plan, start, new AdvanceClock.Outcome(end, diagnostic), List.of()).encode(new Archive());
        return new ClockResult(end, true, false, "fixture original clock", ClockProgress.POSTCONDITION, speed, policy, true, Optional.empty(), List.of(), Optional.of(original));
    }
    private static RouteContactEvidenceCodec.Completed completed() {
        var start = RouteContactCompositeTest.raw(RouteContactCompositeTest.START);
        var ending = RouteContactCompositeTest.raw(RouteContactProofsTest.frame(2, 124, RouteContactCompositeTest.START.ownArmies(), RouteContactCompositeTest.START.hostileArmies()));
        Proof proof = proof(false); var transition = RouteContactPostconditions.predictedEndpoint(RouteContactCodec.frame(start), RouteContactCodec.frame(ending), proof);
        assertTrue(transition.isPresent());
        return new RouteContactEvidenceCodec.Completed(RouteContactCompositeTest.command(false), new Completion(start, ending, proof, transition,
                reportedExact(RouteContactCompositeTest.command(false), start, ending, 1), List.of()));
    }
    @Test void completeProducerRoundtripFeedsTheActualHistoryMarkerConsumer() {
        Archive archive = new Archive(); var input = completed();
        ExactRef ref = new RouteContactEvidenceArchive(archive).completed(input.parent(), input.completion());
        var decoded = assertInstanceOf(RouteContactEvidenceCodec.Completed.class, RouteContactEvidenceCodec.decode(archive.loadMaterial(ref), archive));
        assertEquals(input, decoded); Obj result = RouteContactEvidenceCodec.result(decoded);
        var row = DriverSurvivingHistory.row(new Obj(Map.of("index", n(1), "command", new Text(input.parent().operation().value()), "ok", new Bool(true), "result", result)));
        var timeline = RouteContactHistoryAdapter.timeline(List.of(row));
        AdvanceHistory marker = assertInstanceOf(AdvanceHistory.class, timeline.getFirst());
        assertEquals(TransitionKind.PREDICTED_CONTACT_BOUNDARY_REACHED, marker.transition().orElseThrow().kind());
        assertFalse(marker.transition().orElseThrow().contactObserved());
    }
    @Test void strictFailureSurvivesArchiveHistoryAndCannotAuthorizeThirdExactDay() {
        Archive archive = new Archive(); var completed = completed(); Proof strict = proof(true);
        ContactFailure failure = new ContactFailure(completed.starting(), completed.ending(), strict, "exhausted_without_strong_transition", true, List.of());
        ExactRef ref = new RouteContactEvidenceArchive(archive).failed(completed.parent(), failure);
        var decoded = assertInstanceOf(RouteContactEvidenceCodec.Failed.class, RouteContactEvidenceCodec.decode(archive.loadMaterial(ref), archive));
        assertEquals(failure, decoded.failure());
        ActionCommand parent = completed.parent();
        var guard = new GuardEvidence(completed.starting().identity(), parent.source(), parent.sessionId(), java.math.BigInteger.ONE,
                parent.operation(), RouteContactCompositeTest.EVIDENCE, RouteContactCompositeTest.EVIDENCE, "route-fixture-authority", RouteContactCompositeTest.NOW, parent.deadline());
        var execution = new CompositeExecution(RouteContactComposite.HANDLER, RouteContactCompositeTest.NOW, guard, List.of());
        var actual = new ActionReceipt(1, 1, parent, ActionCodec.bodySha256(parent), new ActionState.CompositeUnknown(execution,
                "exhausted_without_strong_transition", List.of(ref, completed.ending().originalEvidence())));
        Obj result = RouteContactEvidenceArchive.compatibleResult(actual, archive);
        assertEquals(RouteContactEvidenceCodec.result(decoded), result);
        var row = DriverSurvivingHistory.row(new Obj(Map.of("index", n(1), "command", new Text(decoded.parent().operation().value()), "ok", new Bool(false), "result", result)));
        var timeline = RouteContactHistoryAdapter.timeline(List.of(row)); Frame current = RouteContactCodec.frame(completed.ending());
        var scope = new RouteContactProofs.Scope(0, 20, List.of(8));
        assertTrue(RouteContactProofs.oneDayEntries(current, List.of(new RouteContactProofs.QueryEntry(scope, Optional.of(RouteContactProofsTest.endpointQuery(current)))), timeline).isEmpty());
        assertTrue(RouteContactCapabilities.steps(current, List.of(new RouteContactProofs.QueryEntry(scope, Optional.of(RouteContactProofsTest.endpointQuery(current)))), timeline).isEmpty());
    }
    @Test void v4FailureOriginalsRoundtripAndRemainInTheActualParentUnknownEvidence() {
        Archive archive = new Archive(); var completed = completed();
        ExactRef basis = archive.preserveMaterial(new RawJson("{\"schema\":\"fixture-original-clock-basis\"}".getBytes(StandardCharsets.UTF_8)));
        ContactFailure failure = new ContactFailure(completed.starting(), completed.starting(), completed.proof(), "actual clock unavailable", false, List.of(), List.of(basis));
        ExactRef ref = new RouteContactEvidenceArchive(archive).failed(completed.parent(), failure);
        var decoded = assertInstanceOf(RouteContactEvidenceCodec.Failed.class, RouteContactEvidenceCodec.decode(archive.loadMaterial(ref), archive));
        assertEquals(failure, decoded.failure()); assertEquals(List.of(basis), decoded.failure().failureEvidence());
        var parent = completed.parent(); var guard = new GuardEvidence(completed.starting().identity(), parent.source(), parent.sessionId(), java.math.BigInteger.ONE,
                parent.operation(), RouteContactCompositeTest.EVIDENCE, RouteContactCompositeTest.EVIDENCE, "route-fixture-authority", RouteContactCompositeTest.NOW, parent.deadline());
        var execution = new CompositeExecution(RouteContactComposite.HANDLER, RouteContactCompositeTest.NOW, guard, List.of());
        var actual = new ActionReceipt(1, 1, parent, ActionCodec.bodySha256(parent), new ActionState.CompositeUnknown(execution, failure.status(), List.of(ref, completed.starting().originalEvidence(), basis)));
        assertEquals(RouteContactEvidenceCodec.result(decoded), RouteContactEvidenceArchive.compatibleResult(actual, archive));
        assertEquals(List.of(ref, completed.starting().originalEvidence(), basis), ((ActionState.CompositeUnknown) actual.state()).evidence());
        Obj root = DriverJson.object(archive.loadMaterial(ref).bytes(), RawJson.MAXIMUM_BYTES); assertEquals(new Text(RouteContactEvidenceCodec.SCHEMA), root.get("schema"));
        assertThrows(IllegalArgumentException.class, () -> decode(root.with("clock_failure_evidence", Nil.INSTANCE), archive));
        var missing = new LinkedHashMap<>(root.members()); missing.remove("clock_failure_evidence"); assertThrows(IllegalArgumentException.class, () -> decode(new Obj(missing), archive));
    }
    @Test void explicitLegacyV2FailureHasNoInventedClockBasisAndRejectsExtraOriginalRefs() {
        Archive archive = new Archive(); var completed = completed(); ContactFailure failure = new ContactFailure(completed.starting(), completed.ending(), completed.proof(), "historical unavailable", false, List.of());
        Obj fresh = DriverJson.object(RouteContactEvidenceCodec.encode(new RouteContactEvidenceCodec.Failed(completed.parent(), failure), archive).bytes(), RawJson.MAXIMUM_BYTES);
        var fields = new LinkedHashMap<>(fresh.members()); fields.put("schema", new Text("xar.java-route-contact-evidence/v2")); fields.remove("clock_failure_evidence");
        fields.remove("clock"); fields.remove("contact_refresh"); fields.remove("original_error_message");
        var legacy = assertInstanceOf(RouteContactEvidenceCodec.Failed.class, RouteContactEvidenceCodec.decode(new RawJson(DriverJson.encode(new Obj(fields))), archive));
        assertTrue(legacy.failure().failureEvidence().isEmpty());
        assertThrows(IllegalArgumentException.class, () -> decode(new Obj(fields).with("clock_failure_evidence", new Arr(List.of())), archive));
    }
    @Test void explicitLegacyV3CompletedReaderCannotManufactureAFullCurrentClockReport() {
        Archive archive = new Archive(); var original = completed();
        Obj current = DriverJson.object(RouteContactEvidenceCodec.encode(original, archive).bytes(), RawJson.MAXIMUM_BYTES);
        var fields = new LinkedHashMap<>(current.members()); fields.put("schema", new Text("xar.java-route-contact-evidence/v3")); fields.remove("contact_refresh");
        var clock = original.completion().clockResult();
        var legacyClock = new ClockResult(clock.ending(), clock.nativeClockVerified(), clock.unknown(), clock.reason(), clock.progressStatus(), clock.timelineSpeed(), clock.timelinePolicy(), clock.checkpointEligible(), clock.nativeStopRead());
        var legacy = new RouteContactEvidenceCodec.Completed(original.parent(), new Completion(original.starting(), original.ending(), original.proof(), original.completion().transition(), legacyClock, original.children()));
        var retained = new LinkedHashMap<>(object(current.get("clock"), "clock").members()); retained.remove("original_clock_report"); fields.put("clock", new Obj(retained));
        fields.put("result", RouteContactEvidenceCodec.result(legacy));
        var decoded = assertInstanceOf(RouteContactEvidenceCodec.Completed.class, RouteContactEvidenceCodec.decode(new RawJson(DriverJson.encode(new Obj(fields))), archive));
        assertEquals(legacy, decoded); assertTrue(decoded.completion().clockResult().originalReport().isEmpty());
        assertThrows(IllegalArgumentException.class, () -> RouteContactEvidenceCodec.encode(decoded, archive), "new v4 producer cannot silently emit a legacy simplified success");
        assertThrows(IllegalArgumentException.class, () -> decode(new Obj(fields).with("contact_refresh", Nil.INSTANCE), archive));
        assertThrows(IllegalArgumentException.class, () -> decode(new Obj(fields).with("clock", new Obj(retained).with("original_clock_report", object(current.get("clock"), "clock").get("original_clock_report"))), archive));
    }
    @Test void historicalControllerRefreshTokenCannotMasqueradeAsTheCurrentCompletePrimitiveResult() {
        Archive archive = new Archive(); var fixture = new RouteContactCompositeTest.Fixture(); var children = new RouteContactCompositeTest.TestChildren();
        var parent = RouteContactCompositeTest.command(false); var proof = fixture.handler().project(parent);
        var originalClock = reportedExact(parent, fixture.start, fixture.end, 1);
        var child = RouteContactCompositeTest.pauseReceipt(parent, fixture.end, false); children.rows.add(child);
        var refresh = new ContactRefresh(fixture.end, Optional.of(child), Optional.of(fixture.refreshed), Optional.of("already_paused"));
        var transition = RouteContactPostconditions.predictedEndpoint(RouteContactCodec.frame(fixture.start), RouteContactCodec.frame(fixture.refreshed), proof);
        var completion = new Completion(fixture.start, fixture.refreshed, proof, transition, originalClock, children.completed(), Optional.of(refresh));
        var document = new RouteContactEvidenceCodec.Completed(parent, completion);
        assertThrows(IllegalArgumentException.class, () -> RouteContactEvidenceCodec.encode(document, archive), "typed controller DATA has no actual complete primitive producer result");
        Obj result = RouteContactEvidenceCodec.result(document); // Historical v4 DATA projection remains readable.
        Obj base = DriverJson.object(originalClock.originalReport().orElseThrow().bytes(), RawJson.MAXIMUM_BYTES);
        assertEquals(base.get("schema"), result.get("schema")); assertEquals(base.get("starting_revision"), result.get("starting_revision"));
        assertEquals(base.get("native_stop_read_ref"), result.get("native_stop_read_ref")); assertEquals(base.get("full_wall_nanos"), result.get("full_wall_nanos"));
        assertEquals(fixture.refreshed.identity().frame().revision(), integer(result.get("revision"), "revision"));
        assertEquals(fixture.refreshed.identity().frame().snapshotId(), text(result.get("snapshot_id"), "snapshot_id"));
        Obj metadata = object(result.get("contact_refresh"), "contact_refresh");
        assertEquals(fixture.end.identity().frame().revision(), integer(metadata.get("from_revision"), "from_revision"));
        assertEquals(fixture.refreshed.identity().frame().identity().nativeRevision(), integer(metadata.get("to_native_revision"), "to_native_revision"));
        assertEquals(array(base.get("actions"), "actions").size() + 1, array(result.get("actions"), "actions").size());
        assertEquals(ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT, child.outcome()); assertFalse(child.visibleGameplay()); assertFalse(child.eligibleAdvance());
        var tokenOnly = new ContactRefresh(fixture.end, Optional.of(child), Optional.of(fixture.refreshed), Optional.of("already_paused"), child.ack().orElseThrow().originalResultToken());
        var wrong = new RouteContactEvidenceCodec.Completed(parent, new Completion(fixture.start, fixture.refreshed, proof, transition, originalClock, children.completed(), Optional.of(tokenOnly)));
        assertThrows(IllegalArgumentException.class, () -> RouteContactEvidenceCodec.encode(wrong, archive), "raw ACK cannot pass full original Driver boundary");
    }
    @Test void partialFailureKeepsOriginalCompletedClockAndNullUnpublishedRefreshFields() {
        Archive archive = new Archive(); var fixture = new RouteContactCompositeTest.Fixture(); var parent = RouteContactCompositeTest.command(false);
        var proof = fixture.handler().project(parent); var clock = reportedExact(parent, fixture.start, fixture.end, 1);
        var refresh = new ContactRefresh(fixture.end, Optional.empty(), Optional.empty(), Optional.empty());
        var failure = new ContactFailure(fixture.start, fixture.end, proof, "contact refresh deadline", false, List.of(), List.of(), Optional.of(clock), Optional.of(refresh),
                Optional.of("same-date unavoidable-contact refresh timed out before pause-map submission"));
        var document = new RouteContactEvidenceCodec.Failed(parent, failure);
        var decoded = assertInstanceOf(RouteContactEvidenceCodec.Failed.class, RouteContactEvidenceCodec.decode(RouteContactEvidenceCodec.encode(document, archive), archive));
        assertEquals(document, decoded); Obj result = RouteContactEvidenceCodec.result(decoded);
        assertEquals(DriverJson.object(clock.originalReport().orElseThrow().bytes(), RawJson.MAXIMUM_BYTES).get("actions"), result.get("actions"));
        assertEquals(Nil.INSTANCE, object(result.get("contact_refresh"), "contact_refresh").get("to_revision"));
        assertEquals(Nil.INSTANCE, object(result.get("contact_refresh"), "contact_refresh").get("ack_status"));
        assertEquals(failure.originalErrorMessage(), decoded.failure().originalErrorMessage());
        Obj current = DriverJson.object(RouteContactEvidenceCodec.encode(document, archive).bytes(), RawJson.MAXIMUM_BYTES);
        Obj retainedRefresh = object(current.get("contact_refresh"), "contact_refresh");
        var legacyFields = new LinkedHashMap<>(retainedRefresh.members()); legacyFields.remove("original_driver_result");
        Obj legacy = current.with("schema", new Text("xar.java-route-contact-evidence/v4")).with("contact_refresh", new Obj(legacyFields));
        assertEquals(document, RouteContactEvidenceCodec.decode(new RawJson(DriverJson.encode(legacy)), archive), "explicit v4 reader preserves its original absence");
        assertThrows(IllegalArgumentException.class, () -> decode(legacy.with("contact_refresh", retainedRefresh), archive), "v4 does not silently adopt the new field");
        assertThrows(IllegalArgumentException.class, () -> decode(current.with("contact_refresh", new Obj(legacyFields)), archive), "v5 requires its declared nullable field");
        assertThrows(IllegalArgumentException.class, () -> decode(current.with("contact_refresh", retainedRefresh.with("original_driver_result", new Bool(true))), archive));
    }
    @Test void currentClockOriginalRefStillRejectsMissingNullBooleanAndNonReferenceValues() {
        Archive archive = new Archive(); Obj root = DriverJson.object(RouteContactEvidenceCodec.encode(completed(), archive).bytes(), RawJson.MAXIMUM_BYTES);
        Obj clock = object(root.get("clock"), "clock");
        for (Value wrong : List.of(Nil.INSTANCE, new Bool(true), new IntegerValue(java.math.BigInteger.ONE)))
            assertThrows(IllegalArgumentException.class, () -> decode(root.with("clock", clock.with("original_clock_report", wrong)), archive));
        var missing = new LinkedHashMap<>(clock.members()); missing.remove("original_clock_report");
        assertThrows(IllegalArgumentException.class, () -> decode(root.with("clock", new Obj(missing)), archive));
    }
    @Test void fullSemanticMaterialWithSeventyThousandDigitAuxiliaryUsesOnlyTheDeclaredFullLane() {
        Archive archive = new Archive(); var original = completed();
        var extra = new IntegerValue(new java.math.BigInteger("1".repeat(70000)));
        var start = original.starting(); var end = original.ending();
        var wideStart = new AdvanceObservationPort.Frame(start.identity(), start.source(), start.sessionId(), start.semantic().with("retained_auxiliary", extra), start.provenance(), start.observedAt(), start.originalEvidence());
        var wideEnd = new AdvanceObservationPort.Frame(end.identity(), end.source(), end.sessionId(), end.semantic().with("retained_auxiliary", extra), end.provenance(), end.observedAt(), end.originalEvidence());
        var document = new RouteContactEvidenceCodec.Completed(original.parent(), new Completion(wideStart, wideEnd, original.proof(), original.completion().transition(), reportedExact(original.parent(), wideStart, wideEnd, 1), List.of()));
        RawJson encoded = RouteContactEvidenceCodec.encode(document, archive);
        assertEquals(document, RouteContactEvidenceCodec.decode(encoded, archive));
        Obj root = DriverJson.object(encoded.bytes(), RawJson.MAXIMUM_BYTES); Obj semanticRef = object(object(root.get("starting"), "starting").get("semantic"), "semantic ref");
        var reference = new ExactRef(text(semanticRef.get("path"), "path"), integer(semanticRef.get("bytes"), "bytes").longValueExact(), text(semanticRef.get("sha256"), "sha256"));
        assertThrows(IllegalArgumentException.class, () -> archive.loadMaterial(reference), "full material does not expand the ordinary Native4300 lane");
        assertEquals(extra, DriverJson.object(archive.loadFullMaterial(reference).bytes(), RawJson.MAXIMUM_BYTES).get("retained_auxiliary"));
    }
    @Test void strictEvidenceRejectsExtraMissingNullBooleanAndDifferentBody() {
        Archive archive = new Archive(); RawJson raw = RouteContactEvidenceCodec.encode(completed(), archive); Obj root = DriverJson.object(raw.bytes(), RawJson.MAXIMUM_BYTES);
        assertThrows(IllegalArgumentException.class, () -> decode(root.with("extra", new Bool(true)), archive));
        assertThrows(IllegalArgumentException.class, () -> decode(root.with("parent_body_sha256", new Text("b".repeat(64))), archive));
        assertThrows(IllegalArgumentException.class, () -> decode(root.with("clock", Nil.INSTANCE), archive));
        Map<String, Value> missing = new LinkedHashMap<>(root.members()); missing.remove("transition");
        assertThrows(IllegalArgumentException.class, () -> decode(new Obj(missing), archive));
        Obj proof = object(root.get("proof"), "proof");
        assertThrows(IllegalArgumentException.class, () -> decode(root.with("proof", proof.with("horizon_days", new Bool(true))), archive));
    }
    @Test void capabilityWindowIsTheSameBoundedProofAndNeverAddsShorterUncappedPrefix() {
        Frame start = RouteContactCompositeTest.START;
        var query = RouteContactProofsTest.query(start); var entry = new RouteContactProofs.QueryEntry(new RouteContactProofs.Scope(0, 20, List.of(8)), Optional.of(query));
        List<String> operations = RouteContactCapabilities.steps(start, List.of(entry), List.of()).stream().map(OperationKey::value).toList();
        assertTrue(operations.contains("advance-route-contact-horizon-v1-0-to-20-h-1-8"));
        assertTrue(operations.contains("advance-route-contact-window-v1-0-to-20-days-3-h-1-8"));
        assertFalse(operations.contains("advance-route-contact-window-v1-0-to-20-days-2-h-1-8"));
        assertFalse(RouteContactSteps.supports("advance-route-contact-window-v1-0-to-20-days-1-h-1-8"));
        assertFalse(RouteContactSteps.supports("advance-route-contact-horizon-v1-00-to-20-h-1-8"));
        assertFalse(RouteContactSteps.supports(null));
    }
    @Test void sameRevisionWithoutIndependentStatusNeverRefreshesOrClaimsACompletedDay() throws InterruptedException {
        var fixture = new RouteContactCompositeTest.Fixture(); fixture.endpoint = false; fixture.end = fixture.start;
        assertInstanceOf(ActionPorts.Pending.class, fixture.handler().run(RouteContactCompositeTest.command(false), new RouteContactCompositeTest.TestChildren()));
        assertEquals(0, fixture.refreshCalls); assertEquals(0, fixture.completions);
    }
    private static void decode(Obj value, Archive archive) { RouteContactEvidenceCodec.decode(new RawJson(DriverJson.encode(value)), archive); }
    private static IntegerValue n(int value) { return RouteContactCompositeTest.n(value); }
}
