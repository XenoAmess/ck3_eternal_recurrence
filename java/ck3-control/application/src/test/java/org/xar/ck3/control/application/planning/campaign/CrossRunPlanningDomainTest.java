package org.xar.ck3.control.application.planning.campaign;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.campaign.CrossRunPlanningDomain.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.LifecycleIdentity;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Software port fixtures exercise the registered producer/reader boundary; no Game or storage qualification. */
final class CrossRunPlanningDomainTest {
    private static final Instant TIME = Instant.parse("2026-10-24T00:00:00Z");
    private static final ExactRef SOURCE = ref("software-source", 1, "a".repeat(64));
    private static final ObservationIdentity FRAME = new ObservationIdentity("cross-run-software-machine",
            new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("18446744073709551615"))),
            new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(100), BigInteger.TWO,
                    BigInteger.valueOf(24000)), "original-native-snapshot", BigInteger.valueOf(3), "original-episode"), 1);
    private static final G2Source ORIGIN = new G2Source(FRAME.machineId(), TIME.toString(), "software-only", SOURCE);

    @Test void originalStateImportThenActualTerminalProducerThenFreshNextPlanReader() throws IOException {
        Fixture fixture = new Fixture();
        Input initial = fixture.initialInput("original-import");
        fixture.capture = new Initialized(initial, fixture.previous);
        byte[] unchanged = CrossRunPlanning.encodeState(CrossRunPlanningDomain.produce(fixture.capture));
        var initialRequest = request(initial, unchanged);
        assertEquals(64, fixture.domain.verify(fixture.head(), Optional.empty(), initialRequest, unchanged).length());
        assertEquals(1, fixture.calls);
        assertThrows(IllegalArgumentException.class, () -> fixture.domain.verify(fixture.head(), Optional.empty(),
                request(initial, episodeState(fixture.previous.state())), episodeState(fixture.previous.state())));
        fixture.importPrevious();
        Input terminal = fixture.terminalInput();
        fixture.capture = new Recorded(terminal, fixture.previous, fixture.rows, fixture.terminal);
        CrossRunPlanning.State expected = CrossRunPlanningDomain.produce(fixture.capture);
        byte[] next = CrossRunPlanning.encodeState(expected);
        assertEquals(64, fixture.domain.verify(fixture.head(), Optional.of(fixture.body), request(terminal, next), next).length());
        assertTrue(expected.episodes().getFirst().achievements().palermoHolyWarWon());
        fixture.read = new DomainBodies.Available(body(document("after-state", next).reference()), next, SOURCE, List.of());
        var known = assertInstanceOf(KnownState.class, fixture.domain.read(fixture.session));
        assertEquals(expected, known.state()); assertEquals(expected.nextRunPlan(), known.nextPlan());
        assertEquals(Optional.of("war"), CrossRunPlanning.focus(known.nextPlan()));
        assertFalse(known.nextPlan().continueAsHeirAfterDeath());
    }

    @Test void missingStateCannotBeInventedOrUsedToRecordATerminalAndImportedStateCannotReset() throws IOException {
        Fixture fixture = new Fixture();
        var missing = assertInstanceOf(MissingState.class, fixture.domain.read(fixture.session));
        assertEquals(DomainBodies.Reason.UNIMPORTED, missing.original().reason());
        Input terminal = fixture.terminalInput();
        fixture.capture = new Recorded(terminal, fixture.previous, fixture.rows, fixture.terminal);
        byte[] next = CrossRunPlanning.encodeState(CrossRunPlanningDomain.produce(fixture.capture));
        assertThrows(IllegalArgumentException.class, () -> fixture.domain.verify(fixture.head(), Optional.empty(), request(terminal, next), next));
        assertEquals(0, fixture.calls);
        fixture.importPrevious();
        Input initial = fixture.initialInput("reset");
        fixture.capture = new Initialized(initial, fixture.previous); byte[] old = fixture.previous.bytes();
        assertThrows(IllegalArgumentException.class, () -> fixture.domain.verify(fixture.head(), Optional.of(fixture.body), request(initial, old), old));
        assertEquals(0, fixture.calls);
    }

    @Test void headOnlyForeignPredecessorLostLeaseAndActualCaptureFailureCannotQualify() throws IOException {
        Fixture fixture = new Fixture(); fixture.importPrevious(); Input terminal = fixture.terminalInput();
        fixture.capture = new Recorded(terminal, fixture.previous, fixture.rows, fixture.terminal);
        byte[] next = CrossRunPlanning.encodeState(CrossRunPlanningDomain.produce(fixture.capture)); var request = request(terminal, next);
        assertThrows(IOException.class, () -> fixture.domain.verify(fixture.state, Optional.of(fixture.body), request, next));
        fixture.open = false;
        assertThrows(IOException.class, () -> fixture.domain.verify(fixture.head(), Optional.of(fixture.body), request, next));
        assertEquals(0, fixture.calls); fixture.open = true;
        assertThrows(IllegalArgumentException.class, () -> fixture.domain.verify(fixture.head(), Optional.empty(), request, next));
        fixture.failCapture = true;
        assertThrows(IOException.class, () -> fixture.domain.verify(fixture.head(), Optional.of(fixture.body), request, next));
        assertEquals(1, fixture.calls);
    }

    @Test void strictInputRoundtripPreservesExactBirthAndRejectsWrongMissingAndNullTokens() {
        Fixture fixture = new Fixture(); Input input = fixture.terminalInput(); byte[] raw = encodeInput(input);
        assertEquals(input, decodeInput(raw));
        assertTrue(new String(raw, StandardCharsets.UTF_8).contains("\"creation_filetime\":\"18446744073709551615\""));
        ObjectNode numeric = (ObjectNode) StrictJson.parse(raw);
        ((ObjectNode) numeric.path("origin").path("identity").path("game")).put("creation_filetime", new BigInteger("18446744073709551615"));
        assertThrows(IllegalArgumentException.class, () -> decodeInput(numeric.toString().getBytes(StandardCharsets.UTF_8)));
        ObjectNode missing = (ObjectNode) StrictJson.parse(raw); ((ObjectNode)missing.path("origin")).remove("references");
        assertThrows(IllegalArgumentException.class, () -> decodeInput(missing.toString().getBytes(StandardCharsets.UTF_8)));
        ObjectNode nullRefs = (ObjectNode) StrictJson.parse(raw); ((ObjectNode)nullRefs.path("origin")).putNull("references");
        assertThrows(IllegalArgumentException.class, () -> decodeInput(nullRefs.toString().getBytes(StandardCharsets.UTF_8)));
        ObjectNode bool = (ObjectNode) StrictJson.parse(raw); ((ObjectNode) bool.path("origin").path("identity").path("subject")).put("driver_version", true);
        assertThrows(IllegalArgumentException.class, () -> decodeInput(bool.toString().getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> new Recorded(input, fixture.previous, fixture.rows,
                json("{\"terminal\":true,\"score\":null}")));
        assertThrows(IllegalArgumentException.class, () -> new StateDocument(fixture.previous.reference(), new byte[] {123, 125}));
    }

    @Test void wrongCompleteEvidenceClosureOrCrossedActualCaptureCannotPublishTheCandidate() throws IOException {
        Fixture fixture = new Fixture(); fixture.importPrevious(); Input input = fixture.terminalInput();
        fixture.capture = new Recorded(input, fixture.previous, fixture.rows, fixture.terminal);
        byte[] next = CrossRunPlanning.encodeState(CrossRunPlanningDomain.produce(fixture.capture));
        var missingEvidence = new DomainBodies.ImportRequest(DomainBodies.Slot.CROSS_RUN_PLANNING, CONTRACT_SCHEMA,
                document("candidate", next).reference(), encodeInput(input), List.of(fixture.previous.reference()), input.evidenceId());
        assertThrows(IllegalArgumentException.class, () -> fixture.domain.verify(fixture.head(), Optional.of(fixture.body), missingEvidence, next));
        assertEquals(0, fixture.calls);
        Input changed = new Input("different-settlement",input.origin(),input.previousState(),input.producedAt());
        assertThrows(IllegalArgumentException.class, () -> fixture.domain.verify(fixture.head(), Optional.of(fixture.body), request(changed, next), next));
        assertEquals(1, fixture.calls);
    }

    private static final class Fixture {
        final StateDocument previous = document("previous-state", CrossRunPlanning.encodeState(CrossRunPlanning.empty()));
        final DomainBodies.BodyRef body = body(previous.reference());
        ContinuityState state = initial(); boolean open = true, failCapture; int calls; Captured capture;
        DomainBodies.Read read = new DomainBodies.Unavailable(DomainBodies.Reason.UNIMPORTED, Optional.of(SOURCE), "original state has not been imported");
        final List<OpportunityJson.Obj> rows = List.of(json("{\"command\":\"enforce-demands-9\",\"ok\":true,\"result\":{\"war_victory\":{\"status\":\"victory_enforced\"}}}"));
        final OpportunityJson.Obj terminal = terminalResult(previous.state(),rows);
        final ContinuityStorePort.Session session = new TestSession() {
            @Override public WriterContracts.Head head() throws IOException { requireOpen(); return Fixture.this.head(); }
            @Override public DomainBodies.Read readDomain(DomainBodies.Slot slot) throws IOException { requireOpen(); assertEquals(DomainBodies.Slot.CROSS_RUN_PLANNING, slot); return read; }
        };
        final CrossRunPlanningDomain domain = new CrossRunPlanningDomain(() -> { requireOpen(); return session; }, (original, actualHead, input) -> {
            assertSame(session, original); assertEquals(head().digest(), actualHead.digest()); requireOpen(); calls++;
            if (failCapture) throw new IOException("actual native/score/history evidence changed");
            return capture;
        });
        void requireOpen() throws IOException { if (!open) throw new IOException("original writer lease is not held"); }
        WriterContracts.Head head() { return new WriterContracts.Head(state, List.of(), List.of(), List.of(), false); }
        void importPrevious() { state = DomainBodies.reduceImport(state, body); read = new DomainBodies.Available(body, previous.bytes(), SOURCE, List.of()); }
        Input initialInput(String evidence){return new Input(evidence,new EntryOrigin(FRAME,ORIGIN,SOURCE,Path.of("D:/software-fixtures/strategy/one-life-history.json"),Optional.empty()),previous.reference(),TIME);}
        Input terminalInput() {return new Input("terminal-original-episode",new TerminalOrigin(lifecycle(),ORIGIN,"actual-controlled-death-parent",new TerminalReferences(SOURCE, ref("score", 1, "b".repeat(64)), ref("full-history", 1, "c".repeat(64)),ref("native", 1, "d".repeat(64)), ref("complete-driver", 1, "e".repeat(64)))),previous.reference(),TIME);}
    }

    private abstract static class TestSession implements ContinuityStorePort.Session {
        @Override public void requireWriter(Path path) throws IOException { throw new IOException("unrequested test writer operation"); }
        @Override public WriterContracts.Pin capturePin(ExactRef ref, int max) throws IOException { throw new IOException("unrequested test pin operation"); }
        @Override public void verifyPin(WriterContracts.Pin pin) throws IOException { throw new IOException("unrequested test pin operation"); }
        @Override public WriterContracts.Prepared preview(WriterContracts.Request request) throws IOException { throw new IOException("unrequested test mutation"); }
        @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared) throws IOException { throw new IOException("unrequested test mutation"); }
        @Override public ExactRef persistedHead() throws IOException { throw new IOException("unrequested test storage operation"); }
    }
    private static DomainBodies.ImportRequest request(Input input, byte[] candidate) {
        return new DomainBodies.ImportRequest(DomainBodies.Slot.CROSS_RUN_PLANNING, CONTRACT_SCHEMA, document("candidate", candidate).reference(),
                encodeInput(input), input.evidence(), input.evidenceId());
    }
    private static byte[] episodeState(CrossRunPlanning.State previous) {
        return CrossRunPlanning.encodeState(CrossRunPlanning.recordEpisode(previous, "wrong-episode", List.of(), json("{\"terminal\":true,\"score\":123}"), TIME));
    }
    private static OpportunityJson.Obj terminalResult(CrossRunPlanning.State previous,List<OpportunityJson.Obj> rows){
        var terminal=json("{\"terminal\":true,\"terminal_reason\":\"player_death\",\"technical_settlement_handoff\":false,\"settlement_status\":\"complete\",\"score\":123}");
        // A controlled already-produced result for verifier boundary tests; the actual LifecycleReducer producer is exercised separately.
        var produced=CrossRunPlanning.recordScoredTerminal(previous,"original-episode",rows,terminal,TIME);
        var state=OpportunityJson.object(OpportunityJson.parse(CrossRunPlanning.encodeState(produced)),"controlled strategy");
        return terminal.with("cross_run_strategy",state.with("recorded_episode",CrossRunPlanning.episodeJson(produced.episodes().getLast())));
    }
    private static LifecycleIdentity lifecycle(){return new LifecycleIdentity(FRAME.machineId(),FRAME.game(),"software-session",BigInteger.ONE,
        new LifecycleIdentity.Subject(BigInteger.valueOf(100),"original-episode",0,0),new LifecycleIdentity.Frame("original-native-snapshot",BigInteger.valueOf(3),BigInteger.TWO,BigInteger.valueOf(24000),true,true),
        new LifecycleIdentity.Character(BigInteger.valueOf(100),false),LifecycleIdentity.TerminalReason.DEAD,
        new LifecycleIdentity.Evidence(ref("native",1,"b".repeat(64)),ref("hello",1,"c".repeat(64)),ref("manifest",1,"d".repeat(64)),ref("driver",1,"e".repeat(64)),ref("qualification",1,"f".repeat(64))),TIME);}
    private static StateDocument document(String name, byte[] bytes) { return new StateDocument(ref(name, bytes.length, ActionCodec.sha256(bytes)), bytes); }
    private static DomainBodies.BodyRef body(ExactRef payload) {
        return new DomainBodies.BodyRef(DomainBodies.Slot.CROSS_RUN_PLANNING, CONTRACT_SCHEMA, payload,
                new WriterContracts.FileIdentity("1", "9007199254740993", "134000000000000001", TIME.toString(), payload.bytes()), List.of(SOURCE));
    }
    private static ExactRef ref(String name, long bytes, String sha) { return new ExactRef("D:/software-fixtures/" + name + ".json", bytes, sha); }
    private static OpportunityJson.Obj json(String text) { return OpportunityJson.object(OpportunityJson.parse(text.getBytes(StandardCharsets.UTF_8)), "software fixture"); }
    private static ContinuityState initial() {
        ObjectNode row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", FRAME.machineId());
        row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running"); row.put("start_date_raw", 24000);
        row.put("target_date_raw", 24240); row.put("target_days", 10); row.put("last_settled_cycles", 0); row.put("last_settled_date_raw", 24000);
        return ContinuityState.fromJson(row, FRAME.machineId());
    }
}
