package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Routing regressions only. Software proof stubs do not grant actual Root or Game authority. */
final class RootExecutableBindingsHistoricalSourceTest {
    private static final ExactRef SOURCE = new ExactRef("D:/not-opened-origin-fixture/definition.java", 1, "a".repeat(64));
    private static final ExactRef OTHER = new ExactRef("D:/not-opened-origin-fixture/other.java", 1, "b".repeat(64));
    private static final Instant NOW = Instant.parse("2026-10-29T00:00:00Z");
    private static final class NoHistoricalFiles implements Session {
        private int captureCalls;
        private int verifyCalls;
        @Override public Pin capturePin(ExactRef ref, int maximumBytes) throws IOException {
            captureCalls++; throw new IOException("historical implementation file is unavailable");
        }
        @Override public void verifyPin(Pin pin) throws IOException {
            verifyCalls++; throw new IOException("historical implementation file must not be rechecked");
        }
        @Override public void requireWriter(Path lock) { throw unexpected(); }
        @Override public Head head() { throw unexpected(); }
        @Override public Prepared preview(Request request) { throw unexpected(); }
        @Override public Receipt commit(Prepared prepared) { throw unexpected(); }
        @Override public ExactRef persistedHead() { throw unexpected(); }
        private static AssertionError unexpected() { return new AssertionError("unexpected software Session call"); }
    }
    private abstract static class Proof implements ActionPorts.PreparationPort {
        ExactRef definition = SOURCE;
        final Optional<String> capability;
        final IOException refusal = new IOException("actual current origin refused");
        boolean refuse;
        int qualified;
        int prepared;
        Session qualifiedSession;
        ActionCommand qualifiedCommand;
        Proof(Optional<String> capability) { this.capability = capability; }
        final void qualify(Session session, ActionCommand command) throws IOException {
            qualified++; qualifiedSession = session; qualifiedCommand = command;
            if (refuse) throw refusal;
        }
        @Override public NativeRequest prepare(ActionCommand command) {
            prepared++;
            return new NativeRequest(command.operation().value(), capability,
                    new RawJson("{}".getBytes(StandardCharsets.UTF_8)), List.of(SOURCE));
        }
    }
    private static final class Operator extends Proof implements RootExecutableBindings.OperatorSourceOriginProof {
        int observed;
        boolean refuseObservation;
        Session observedSession;
        ActionReceipt observedReceipt;
        Instant observedDeadline;
        ActionPorts.OperatorReconciliationWork observedWork;
        final ActionPorts.Pending pending = new ActionPorts.Pending("source-owned pending without replay", List.of(SOURCE));
        Operator() { super(Optional.of(OperatorPlayerSwitch.CAPABILITY)); }
        @Override public ExactRef operatorDefinitionSource() { return definition; }
        @Override public void requireOperatorOrigin(Session session, ActionCommand command) throws IOException { qualify(session, command); }
        @Override public ActionPorts.PostconditionResult observeOperatorReconciliation(Session session, ActionReceipt receipt,
                Instant deadline, ActionPorts.OperatorReconciliationWork work) throws IOException {
            observed++; observedSession = session; observedReceipt = receipt; observedDeadline = deadline; observedWork = work;
            if (refuseObservation) throw refusal;
            return pending;
        }
    }
    private static final class Coa extends Proof implements RootExecutableBindings.CoaSourceOriginProof {
        Coa() { super(Optional.of("game.command.export-coat-of-arms-source-v1")); }
        @Override public ExactRef coaSourceDefinitionSource() { return definition; }
        @Override public void requireCoaSourceOrigin(Session session, ActionCommand command) throws IOException { qualify(session, command); }
    }
    private static final class Succession extends Proof implements RootExecutableBindings.SuccessionUiOriginProof {
        Succession() { super(Optional.empty()); }
        @Override public ExactRef successionUiDefinitionSource() { return definition; }
        @Override public void requireSuccessionOrigin(Session session, ActionCommand command) throws IOException { qualify(session, command); }
    }
    private record Route(RootExecutableBindings bindings, Proof proof, ActionCommand command) { }
    private static ProposalLifecycle.ObservationIdentity frame() {
        return new ProposalLifecycle.ObservationIdentity("source-routing", new GameGeneration(123, new PythonOnlyUInt64(BigInteger.valueOf(1001))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(3), BigInteger.TEN, BigInteger.valueOf(100)),
                        "snapshot", BigInteger.TEN, "episode"), 1);
    }
    private static ActionCommand command(String operation, boolean operator) {
        var before = frame(); var origin = new CommandOrigin.Gameplay(before);
        var source = new G2Source("source-routing", NOW.toString(), "1.19.0.6", SOURCE);
        CommandExpectation expectation = operator
                ? new CommandExpectation.OperatorRebind(new OperatorRebindExpectation(origin, source,
                        new OperatorPlayerSwitch.Request(7, BigInteger.TEN), "episode", 0, SOURCE))
                : new CommandExpectation.Gameplay(new ProposalLifecycle.ExpectedPostcondition(1, before, source, "routing-only/v1",
                        List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"), true))));
        return new ActionCommand("source-routing-" + operation, origin, source, "session", new OperationKey(operation),
                new OpportunityJson.Obj(Map.of()), expectation, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), NOW.plusSeconds(30));
    }
    private static Route route(int profile) {
        Proof proof = switch (profile) { case 0 -> new Operator(); case 1 -> new Coa(); case 2 -> new Succession(); default -> throw new AssertionError(profile); };
        String operation = switch (profile) { case 0 -> "set-played-character-v1-7"; case 1 -> "export-coat-of-arms-source-v1"; default -> "continue-death-succession-modal-v1"; };
        var effect = new NativeEffectRegistry.Binding(new OperationKey(operation), SOURCE, proof,
                (command, attempt, dispatch) -> { throw new AssertionError("routing fixture never observes a native effect"); });
        var action = switch (profile) {
            case 0 -> RootExecutableBindings.ActionBinding.operatorSource(effect, SOURCE, assertInstanceOf(Operator.class, proof));
            case 1 -> RootExecutableBindings.ActionBinding.coaSource(effect, SOURCE, assertInstanceOf(Coa.class, proof));
            default -> new RootExecutableBindings.ActionBinding(effect, ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION,
                    Optional.empty(), SOURCE, Optional.of(assertInstanceOf(Succession.class, proof)));
        };
        return new Route(RootExecutableBindings.freeze(List.of(action), RootReadContractCatalog.staticOnly(List.of()), List.of(), 4),
                proof, command(operation, profile == 0));
    }
    private static void noHistoricalFiles(NoHistoricalFiles same) {
        assertEquals(0, same.captureCalls); assertEquals(0, same.verifyCalls);
    }
    private static void reachesSameInstalledOriginAndPreparation(int profile) {
        var route = route(profile); var same = new NoHistoricalFiles();
        NativeRequest prepared = route.bindings().prepare(same, route.command(), "request");
        assertEquals(route.command().operation().value(), prepared.step());
        assertEquals(route.proof().capability, prepared.requiredCapability());
        assertEquals(1, route.proof().qualified); assertEquals(1, route.proof().prepared);
        assertSame(same, route.proof().qualifiedSession); assertSame(route.command(), route.proof().qualifiedCommand);
        noHistoricalFiles(same);
    }
    @Test void operatorStillUsesItsActualOriginWithoutHistoricalDefinitionIo() { reachesSameInstalledOriginAndPreparation(0); }
    @Test void coaStillUsesItsActualOriginWithoutHistoricalDefinitionIo() { reachesSameInstalledOriginAndPreparation(1); }
    @Test void successionStillUsesItsActualOriginWithoutHistoricalDefinitionIo() { reachesSameInstalledOriginAndPreparation(2); }
    @Test void eachActualOriginRefusalStillPreventsPreparation() {
        for (int profile = 0; profile < 3; profile++) {
            var route = route(profile); var same = new NoHistoricalFiles(); route.proof().refuse = true;
            var failure = assertThrows(UncheckedIOException.class, () -> route.bindings().prepare(same, route.command(), "request"));
            assertSame(route.proof().refusal, failure.getCause());
            assertEquals(1, route.proof().qualified); assertEquals(0, route.proof().prepared); noHistoricalFiles(same);
        }
    }
    @Test void everySpecialOriginStillRequiresTheBorrowedWriter() {
        for (int profile = 0; profile < 3; profile++) {
            var route = route(profile);
            assertThrows(IllegalStateException.class, () -> route.bindings().prepare(route.command()));
            assertEquals(0, route.proof().qualified); assertEquals(0, route.proof().prepared);
        }
    }
    @Test void installedDefinitionObjectDriftStillRejectsBeforeActualOrigin() {
        for (int profile = 0; profile < 3; profile++) {
            var route = route(profile); var same = new NoHistoricalFiles(); route.proof().definition = OTHER;
            assertThrows(IllegalArgumentException.class, () -> route.bindings().prepare(same, route.command(), "request"));
            assertEquals(0, route.proof().qualified); assertEquals(0, route.proof().prepared); noHistoricalFiles(same);
        }
    }
    @Test void operatorStillRequiresItsExactTypedExpectation() {
        var route = route(0); var same = new NoHistoricalFiles();
        var wrong = command(route.command().operation().value(), false);
        assertThrows(IllegalArgumentException.class, () -> route.bindings().prepare(same, wrong, "request"));
        assertEquals(0, route.proof().qualified); assertEquals(0, route.proof().prepared); noHistoricalFiles(same);
    }
    private static ActionReceipt pending(ActionCommand command) {
        return new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command),
                new ActionState.Unknown(Optional.empty(), Optional.empty(), "routing-only unknown", List.of(SOURCE)));
    }
    @Test void reconciliationLeavesPendingControlWithTheSameSourceAndNeverInvokesObserverItself() throws Exception {
        var route = route(0); var same = new NoHistoricalFiles(); var source = assertInstanceOf(Operator.class, route.proof());
        var receipt = pending(route.command()); var deadline = NOW.plusSeconds(45);
        ActionPorts.OperatorReconciliationWork work = () -> { throw new AssertionError("outer routing must not invoke the observer or replay UNKNOWN"); };
        assertSame(source.pending, route.bindings().observeOperatorReconciliation(same, receipt, deadline, work));
        assertEquals(1, source.observed); assertSame(same, source.observedSession); assertSame(receipt, source.observedReceipt);
        assertSame(deadline, source.observedDeadline); assertSame(work, source.observedWork);
        assertEquals(0, source.prepared); assertEquals(0, source.qualified); noHistoricalFiles(same);
    }
    @Test void reconciliationActualSourceRefusalStillPropagates() {
        var route = route(0); var same = new NoHistoricalFiles(); var source = assertInstanceOf(Operator.class, route.proof()); source.refuseObservation = true;
        var failure = assertThrows(IOException.class, () -> route.bindings().observeOperatorReconciliation(same,
                pending(route.command()), NOW.plusSeconds(45), () -> { throw new AssertionError("no observer after source refusal"); }));
        assertSame(source.refusal, failure); assertEquals(1, source.observed); assertEquals(0, source.prepared); noHistoricalFiles(same);
    }
    @Test void reconciliationWrongTypedExpectationCannotReachTheSource() {
        var route = route(0); var same = new NoHistoricalFiles(); var source = assertInstanceOf(Operator.class, route.proof());
        assertThrows(IllegalArgumentException.class, () -> route.bindings().observeOperatorReconciliation(same,
                pending(command(route.command().operation().value(), false)), NOW.plusSeconds(45),
                () -> { throw new AssertionError("wrong typed origin cannot observe"); }));
        assertEquals(0, source.observed); assertEquals(0, source.prepared); noHistoricalFiles(same);
    }
}
