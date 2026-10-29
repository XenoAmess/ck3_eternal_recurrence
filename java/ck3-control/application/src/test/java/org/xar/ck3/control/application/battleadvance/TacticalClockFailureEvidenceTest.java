package org.xar.ck3.control.application.battleadvance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.battleadvance.BattleAdvanceFixture.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Duration;
import java.time.ZoneOffset;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.application.advance.AdvanceObservationPort.Frame;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.session.AutoFailureDiagnostic;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Mode;
import org.xar.ck3.control.reconciliation.LateOutcome.State;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;

/** Offline transport/archive fixture. Exercises actual failure producer, runtime installer and public typed port. */
final class TacticalClockFailureEvidenceTest {
    @Test void actualUnknownResumePublishesBoundFailureWithUnobservedStopAndNeverReplays() throws Exception {
        var run = failedWindow();
        int priorSteps = run.nativeFixture.steps.size(), priorReads = run.nativeFixture.frameReads;
        AutoFailureDiagnostic diagnostic = run.runtime.diagnostics().project(run.parent, run.archive).orElseThrow();
        diagnostic.require(run.parent);
        var originalFailureRef = ((ActionState.CompositeUnknown)run.parent.state()).evidence().getFirst();
        var existingConsumer = new BattleAdvanceArchive(run.archive).load(originalFailureRef, BattleAdvanceResultCodec.Profile.JAVA_V1);
        assertTrue(existingConsumer.sentinel().isEmpty()); assertEquals(run.parent.command().operation().value(), existingConsumer.plan().orElseThrow().step());
        var body = StrictJson.parse(diagnostic.diagnostic().bytes());
        assertEquals("xar.tactical-clock-failure.v1", body.path("schema").textValue());
        assertTrue(body.path("is_error").booleanValue()); assertTrue(body.path("never_replay").booleanValue()); assertEquals(0, body.path("credit").intValue());
        assertTrue(body.path("step_result").path("tactical_daily_sentinel").isNull());
        assertTrue(body.path("step_result").path("completed_daily_ticks").isNull());
        assertEquals("1", body.path("step_result").path("armed_tactical_daily_sentinel").path("generation").textValue());
        assertTrue(body.path("wait_progress").isNull());
        assertEquals(run.parent.command().operation().value(), body.path("selected_step").textValue());
        assertEquals(diagnostic, run.runtime.diagnostics().project(run.parent, run.archive).orElseThrow());
        assertEquals(priorSteps, run.nativeFixture.steps.size()); assertEquals(priorReads, run.nativeFixture.frameReads);
        assertInstanceOf(ActionState.CompositeUnknown.class, run.parent.state());
        assertFalse(run.nativeFixture.children.getLast().settled()); assertFalse(run.nativeFixture.steps.contains("pause-map"));
    }
    @Test void exactFailureBasisHashParentAndPlanTypesCannotBeSubstituted() throws Exception {
        var run = failedWindow(); var unknown = (ActionState.CompositeUnknown)run.parent.state();
        ExactRef basis = ExactRef.fromJson(StrictJson.parse(run.archive.loadMaterial(unknown.evidence().getFirst()).bytes()).get(TacticalClockFailureEvidence.BASIS_FIELD));
        RawJson saved = run.archive.loadMaterial(basis);
        var changed = (com.fasterxml.jackson.databind.node.ObjectNode) StrictJson.parse(saved.bytes()); changed.put("parent_body_sha256", "0".repeat(64));
        var wrongParentBasis = run.archive.preserveMaterial(new RawJson(StrictJson.canonical(changed)));
        assertThrows(IllegalArgumentException.class, () -> run.runtime.diagnostics().project(withOriginals(run, wrongParentBasis), run.archive));
        changed = (com.fasterxml.jackson.databind.node.ObjectNode) StrictJson.parse(saved.bytes()); ((com.fasterxml.jackson.databind.node.ObjectNode) changed.get("plan")).put("speed", true);
        var wrongType = run.archive.preserveMaterial(new RawJson(StrictJson.canonical(changed)));
        assertThrows(IllegalArgumentException.class, () -> run.runtime.diagnostics().project(withOriginals(run, wrongType), run.archive));
        run.archive.materials.put(basis, new RawJson("{}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> run.runtime.diagnostics().project(run.parent, run.archive));
        run.archive.materials.put(basis, saved);
        assertTrue(run.runtime.diagnostics().project(run.parent, run.archive).isPresent());
    }
    @Test void noFailureStateOrMissingOriginalFrameCannotBecomeATacticalDiagnostic() throws Exception {
        var run = failedWindow();
        ActionReceipt child = run.nativeFixture.children.getFirst();
        assertTrue(run.runtime.diagnostics().project(child, run.archive).isEmpty());
        var unknown = (ActionState.CompositeUnknown)run.parent.state();
        var foreign = new CompositeExecution("unregistered.fixture.handler", unknown.execution().startedAt(), unknown.execution().guard(), unknown.execution().children());
        var wrongHandler = new ActionReceipt(run.parent.version(), run.parent.sequence(), run.parent.command(), run.parent.bodySha256(), new ActionState.CompositeUnknown(foreign, unknown.reason(), unknown.evidence()));
        assertThrows(IllegalArgumentException.class, () -> run.runtime.diagnostics().project(wrongHandler, run.archive));
        run.archive.nativeFrames.clear();
        assertThrows(IllegalArgumentException.class, () -> run.runtime.diagnostics().project(run.parent, run.archive));
    }
    private static ActionReceipt withBasis(ActionReceipt parent, ExactRef basis) {
        var original = (ActionState.CompositeUnknown)parent.state();
        return new ActionReceipt(parent.version(), parent.sequence(), parent.command(), parent.bodySha256(),
                new ActionState.CompositeUnknown(original.execution(), original.reason(), List.of(basis)));
    }
    private static ActionReceipt withOriginals(Run run, ExactRef originals) {
        var unknown = (ActionState.CompositeUnknown)run.parent.state();
        var compatible = (com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(run.archive.loadMaterial(unknown.evidence().getFirst()).bytes());
        compatible.set(TacticalClockFailureEvidence.BASIS_FIELD, originals.toJson());
        return withBasis(run.parent, run.archive.preserveMaterial(new RawJson(StrictJson.canonical(compatible))));
    }
    private record Run(BattleAdvanceFixture nativeFixture, MemoryArchive archive, TacticalClockFailureRuntime.Installed runtime, ActionReceipt parent) { }
    private static Run failedWindow() throws Exception {
        var archive = new MemoryArchive(); var nativeFixture = new BattleAdvanceFixture(); nativeFixture.unknownStep = "resume-map";
        Frame starting = archive.frame(nonCombat(frame(1, 100, true, false)));
        Frame afterSpeed = archive.frame(nonCombat(frame(2, 100, true, false))), beforeResume = archive.frame(nonCombat(frame(3, 100, true, false)));
        String step = "advance-route-contact-window-v1-0-to-7-days-2-h-1-5";
        var original = BattleAdvanceFixture.parent();
        var command = new ActionCommand("route-window-failure-parent", starting.identity(), starting.source(), starting.sessionId(), new OperationKey(step), new OpportunityJson.Obj(Map.of()),
                new ProposalLifecycle.ExpectedPostcondition(1, starting.identity(), starting.source(), "fixture.route.window", List.of()), original.claims(), original.deadline());
        var runtime = TacticalClockFailureRuntime.install(archive::complete, archive);
        var status = new ClockStatusRead(nativeFixture, REF, archive);
        var clock = Clock.fixed(NOW, ZoneOffset.UTC);
        var composite = new BattleAdvanceComposite(nativeFixture, new AdvanceWait(nativeFixture, clock, 4), status,
                BattleAdvancePlan.Configuration.production(Optional.empty()),
                (parent, actual) -> new AdvanceReadiness.Facts(actual.identity(), AVAILABLE,
                        java.util.Set.of(ClockStatusRead.ARM_CAP, ClockStatusRead.STATUS_CAP, ClockStatusRead.CANCEL_CAP), false, false, false, 45, REF),
                new ActionSnapshotReader(new NoWriterJournal()), runtime.failureArchive(), Duration.ofSeconds(30), Duration.ofSeconds(120), clock,
                (parent, retained) -> { throw new AssertionError("failure projection must not reconcile/read Native"); });
        nativeFixture.frames.addAll(List.of(afterSpeed, beforeResume));
        Status arm = new Status(State.ARMED, new org.xar.ck3.control.contracts.CrossJsDecimalUInt64("1"), 100, 148, 100, 0, 3, Mode.TERMINAL_OR_SENTINEL,
                1, 1, 0, 0, 0, List.of(), 0, -1, false, false, false, false);
        nativeFixture.statusReads.add(arm);
        var failure = assertThrows(BattleAdvanceComposite.Unresolved.class, () -> composite.executeWindow(command, nativeFixture, starting, new BattleAdvanceComposite.WindowRequest(List.of(0), 148, 3)));
        var guard = new GuardEvidence(command.before(), command.source(), command.sessionId(), BigInteger.ONE, command.operation(), starting.originalEvidence(), REF, "fixture.authority", NOW, command.deadline());
        var execution = new CompositeExecution(org.xar.ck3.control.application.routecontact.RouteContactComposite.HANDLER, NOW, guard, nativeFixture.children.stream().map(child -> new CompositeExecution.Child(child.command().actionId(), child.bodySha256())).toList());
        var parent = new ActionReceipt(1, 8, command, ActionCodec.bodySha256(command), new ActionState.CompositeUnknown(execution, failure.getMessage(), failure.evidence()));
        return new Run(nativeFixture, archive, runtime, parent);
    }
    private static Frame nonCombat(Frame frame) {
        String json = new String(OpportunityJson.encode(frame.semantic()), StandardCharsets.UTF_8).replace("\"army_state\":\"combat\"", "\"army_state\":\"regular\"")
                .replace("\"army_state_code\":2", "\"army_state_code\":1").replace("\"in_combat\":true", "\"in_combat\":false").replace("\"combat_id\":281474976710657", "\"combat_id\":-1");
        return new Frame(frame.identity(), frame.source(), frame.sessionId(), OpportunityJson.object(OpportunityJson.parse(json.getBytes(StandardCharsets.UTF_8)), "fixture"), frame.provenance(), frame.observedAt(), frame.originalEvidence());
    }
    private static final class NoWriterJournal implements ActionJournal {
        @Override public <T> T locked(java.util.function.Function<ActionJournal.LockedJournal,T> work) { throw new AssertionError("diagnostic fixture must not open another writer"); }
    }
    private static final class MemoryArchive implements ActionPorts.OutcomeArchive {
        final Map<ExactRef,RawJson> materials = new HashMap<>(); final Map<ExactRef,byte[]> nativeFrames = new HashMap<>();
        final Map<ExactRef,NativeActionPort.DispatchOutcome> dispatches = new HashMap<>(); final Map<ExactRef,ActionReceipt> receipts = new HashMap<>();
        final Map<ExactRef,Frame> frames = new HashMap<>();
        private static ExactRef ref(String domain, byte[] bytes) { String sha = ActionCodec.sha256(bytes); return new ExactRef("D:/offline-tactical-fixture/" + domain + "-" + sha + ".json", bytes.length, sha); }
        Frame frame(Frame original) {
            RawJson facts = new RawJson(("{\"actual_fixture_snapshot\":\"" + original.identity().frame().snapshotId() + "\"}").getBytes(StandardCharsets.UTF_8));
            ExactRef factRef = preserveMaterial(facts); byte[] packet = OpportunityJson.encode(original.semantic()); ExactRef nativeRef = ref("native", packet); nativeFrames.put(nativeRef, packet);
            var semantic = original.semantic().with("java_driver_facts_evidence", OpportunityJson.parse(StrictJson.canonical(factRef.toJson())));
            var push = new ObservationProvenance.Push(original.identity().frame().snapshotId(), original.identity().frame().identity().nativeRevision(), nativeRef);
            Frame result = new Frame(original.identity(), original.source(), original.sessionId(), semantic, push, original.observedAt(), nativeRef); frames.put(nativeRef, result); return result;
        }
        DriverObservationAssembler.Complete complete(NativeEffectEvidence.FrameBasis basis, ActionPorts.OutcomeArchive ignored) {
            loadNativeFrame(basis.nativeFrame()); loadMaterial(basis.driverFacts()); Frame actual = frames.get(basis.nativeFrame());
            if (actual == null || !ExactRef.fromJson(OpportunityJson.toNode(actual.semantic().get("java_driver_facts_evidence"))).equals(basis.driverFacts())) throw new IllegalArgumentException("original fixture frame basis unavailable");
            return new DriverObservationAssembler.Complete(actual.identity(), actual.source(), actual.sessionId(), BigInteger.ONE, actual.semantic(), actual.originalEvidence(), actual.observedAt(), DriverObservationAssembler.bindingSha256(actual.semantic()));
        }
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value) { byte[] bytes = (value.requestId() + ":" + value.getClass().getSimpleName()).getBytes(StandardCharsets.UTF_8); ExactRef ref = ref("dispatch", bytes); dispatches.put(ref, value); return ref; }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref) { var value = dispatches.get(ref); if(value == null) throw new IllegalArgumentException("dispatch unavailable"); return value; }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value) { return dispatches.entrySet().stream().filter(row -> row.getValue().equals(value)).map(Map.Entry::getKey).findFirst().orElseThrow(() -> new IllegalArgumentException("dispatch not archived")); }
        @Override public ExactRef preserveReceipt(ActionReceipt value) { ExactRef ref = ref("receipt", (value.command().actionId()+":"+value.bodySha256()+":"+value.sequence()).getBytes(StandardCharsets.UTF_8)); receipts.put(ref, value); return ref; }
        @Override public ActionReceipt loadReceipt(ExactRef ref) { var value=receipts.get(ref); if(value==null)throw new IllegalArgumentException("receipt unavailable"); return value; }
        @Override public ExactRef receiptReferenceOf(ActionReceipt value) { return receipts.entrySet().stream().filter(row -> row.getValue().equals(value)).map(Map.Entry::getKey).findFirst().orElseThrow(); }
        @Override public ExactRef preserveMaterial(RawJson value) { ExactRef ref = ref("material",value.bytes()); materials.put(ref,value); return ref; }
        @Override public RawJson loadMaterial(ExactRef ref) { var value=materials.get(ref); if(value==null)throw new IllegalArgumentException("material unavailable"); return value; }
        @Override public ExactRef materialReferenceOf(RawJson value) { return materials.entrySet().stream().filter(row -> row.getValue().equals(value)).map(Map.Entry::getKey).findFirst().orElseThrow(); }
        @Override public byte[] loadNativeFrame(ExactRef ref) { var value=nativeFrames.get(ref); if(value==null)throw new IllegalArgumentException("native frame unavailable"); return value; }
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value) { throw new UnsupportedOperationException(); }
        @Override public ExactRef preserveRequest(NativeRequest value) { throw new UnsupportedOperationException(); }
        @Override public NativeRequest loadRequest(ExactRef ref) { throw new UnsupportedOperationException(); }
        @Override public ExactRef requestReferenceOf(NativeRequest value) { throw new UnsupportedOperationException(); }
        @Override public ExactRef preserveRead(PlanningReadReceipt value) { throw new UnsupportedOperationException(); }
        @Override public PlanningReadReceipt loadRead(ExactRef ref) { throw new UnsupportedOperationException(); }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt value) { throw new UnsupportedOperationException(); }
        @Override public ExactRef preserveRecord(ActionRecord value) { throw new UnsupportedOperationException(); }
        @Override public ActionRecord loadRecord(ExactRef ref) { throw new UnsupportedOperationException(); }
        @Override public ExactRef recordReferenceOf(ActionRecord value) { throw new UnsupportedOperationException(); }
    }
}
