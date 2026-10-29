package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Real guarded writer/archive -> actual five-argument primitive producer -> scoped preparation -> request serde.
 * The unregistered Source below is interface DATA only. Its marker is not an estate/M3/Close proof and it cannot
 * authorize a canonical successor continuation, create Current/Ready, submit Native actions or advance a Game.
 * Genuine Root PendingDateSource capture/permission/Close/current-frame coverage belongs to its sole native owner.
 */
final class PendingUiLifeAdvanceScopeTest {
    @TempDir Path directory;
    private enum Mode { ORIGINAL, EMPTY_EVIDENCE, CHANGED_WIRE }
    private static final AdvanceObservationPort NO_OBSERVATION = new AdvanceObservationPort() {
        @Override public Frame current(ActionCommand command, Instant deadline) { throw new AssertionError("preparation cannot sample a replacement observation"); }
        @Override public Frame next(ActionCommand command, ObservationIdentity after, Instant deadline) { throw new AssertionError("preparation cannot poll or advance"); }
    };
    private static ActionCommand primitive(ActionCommand original, String step) {
        var operation = new OperationKey(step); var args = new Obj(Map.of());
        return new ActionCommand(original.actionId(), original.before(), original.source(), original.sessionId(), operation, args,
                AdvancePrimitives.expected(original.before(), original.source(), operation, args), original.claims(), original.deadline());
    }
    private static ClockStatusRead status(ActionWriterIntegrationFixture fixture) {
        return new ClockStatusRead(fixture.reads, ClockStatusRead.registeredContract(fixture.observationSource().sourceRef()), fixture.archive);
    }
    private static ActionCommand parent(ActionCommand actual) {
        var old = actual.before(); Instant now = Instant.now();
        var refs = java.util.stream.IntStream.range(0, 5).mapToObj(index -> new ExactRef("controlled-interface-original-" + index, 1,
                Integer.toString(index + 1).repeat(64))).toList();
        var identity = new LifecycleIdentity(old.machineId(), old.game(), actual.sessionId(), BigInteger.ONE,
                new LifecycleIdentity.Subject(BigInteger.ONE, "controlled-interface-predecessor", 1, 1),
                new LifecycleIdentity.Frame(old.frame().snapshotId(), BigInteger.ONE, BigInteger.ONE, old.frame().identity().dateRaw(), true, true),
                new LifecycleIdentity.Character(BigInteger.TWO, true), LifecycleIdentity.TerminalReason.CHANGED,
                new LifecycleIdentity.Evidence(refs.get(0), refs.get(1), refs.get(2), refs.get(3), refs.get(4)), now);
        var values = List.<ExpectedValue>of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), false),
                new ExpectedBoolean(new FieldKey("timeline.advance_verified"), false), new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"), false));
        var expected = new LifecycleExpectedPostcondition(identity, actual.source(), "controlled-pending-interface-parent/v1",
                LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR, values);
        return new ActionCommand("controlled-interface-parent", new CommandOrigin.LifecycleTerminal(identity), actual.source(), actual.sessionId(),
                expected.operation().key(), new Obj(Map.of()), new CommandExpectation.LifecycleTerminal(expected),
                new Claims(Set.of(), Set.of(), Set.of(), Set.of()), actual.deadline());
    }
    private static final class InterfaceSource implements PendingUiLifeAdvance.Source {
        private final ActionWriterIntegrationFixture fixture; private final ActionCommand ancestor;
        private Mode mode = Mode.ORIGINAL; private int preparations;
        private InterfaceSource(ActionWriterIntegrationFixture fixture, ActionCommand ancestor) { this.fixture = fixture; this.ancestor = ancestor; }
        @Override public ActionCommand originalParent() { return ancestor; }
        @Override public void requireCurrent(Session same) throws IOException { fixture.writer.requireSession(same); }
        @Override public <T> T withCurrent(Session same, Instant deadline, PendingUiLifeAdvance.Work<T> work) { throw new AssertionError("preparation cannot invent a private physical Current"); }
        @Override public <T> T withNext(Session same, ObservationIdentity after, Instant deadline, PendingUiLifeAdvance.Work<T> work) { throw new AssertionError("preparation cannot create a private next frame"); }
        @Override public NativeRequest preparePreclock(Session same, ActionCommand command, String requestId, NativeRequest base) throws IOException {
            requireCurrent(same); preparations++;
            assertEquals(RequestIds.forCommand(command), requestId); assertEquals("resume-map", command.operation().value());
            if (mode == Mode.EMPTY_EVIDENCE) return base;
            var marker = fixture.archive.withSession(same).preserveMaterial(new RawJson("{\"interface_data_only\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            return new NativeRequest(base.step(), base.requiredCapability(), mode == Mode.CHANGED_WIRE
                    ? new RawJson("{\"changed\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8)) : base.additionalFields(), List.of(marker));
        }
    }

    @Test void canonicalSessionProducerRetainsSourceOriginalsAndExactWireWithoutObservationOrDispatch() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(directory.resolve("active-originals"), false)) {
            var command = primitive(fixture.command("actual-resume-interface"), "resume-map");
            var borrowed = new AtomicReference<Session>(); var scope = new PendingUiLifeAdvance.Scope(borrowed::get);
            var source = new InterfaceSource(fixture, parent(command));
            var producer = new AdvancePrimitives(NO_OBSERVATION, status(fixture), Clock.systemUTC(), 8, scope);
            int reads = fixture.nativePacketReads(), writes = fixture.nativeActionWrites();
            fixture.writer.locked(same -> {
                borrowed.set(same); long sequence = same.head().state().sequence();
                scope.within(source, () -> {
                    assertTrue(scope.active()); assertThrows(IllegalArgumentException.class, () -> producer.prepare(command));
                    var request = producer.prepare(same, command, RequestIds.forCommand(command));
                    assertEquals(1, source.preparations); assertEquals(1, request.preparationEvidence().size());
                    var base = AdvancePrimitives.prepareRequest(command);
                    assertEquals(base.step(), request.step()); assertEquals(base.requiredCapability(), request.requiredCapability());
                    assertArrayEquals(base.additionalFields().bytes(), request.additionalFields().bytes());
                    var archive = fixture.archive.withSession(same); var ref = archive.preserveRequest(request); var restored = archive.loadRequest(ref);
                    assertEquals(request, restored); assertEquals(ref, archive.requestReferenceOf(restored));
                    assertEquals(new String(archive.loadMaterial(restored.preparationEvidence().getFirst()).bytes(), java.nio.charset.StandardCharsets.UTF_8), "{\"interface_data_only\":true}");
                    assertEquals(command, ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
                    var setter = primitive(command, "set-speed-1");
                    assertEquals(AdvancePrimitives.prepareRequest(setter), producer.prepare(same, setter, RequestIds.forCommand(setter)));
                    assertEquals(1, source.preparations); return null;
                });
                assertFalse(scope.active()); assertEquals(sequence, same.head().state().sequence()); borrowed.set(null); return null;
            });
            assertEquals(reads, fixture.nativePacketReads()); assertEquals(writes, fixture.nativeActionWrites());
        }
    }

    @Test void missingOriginalsChangedWireAndNestedSourceCannotBecomeAValidPrivatePreparation() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(directory.resolve("bad-originals"), false)) {
            var command = primitive(fixture.command("actual-bad-interface"), "resume-map");
            var borrowed = new AtomicReference<Session>(); var scope = new PendingUiLifeAdvance.Scope(borrowed::get);
            var source = new InterfaceSource(fixture, parent(command));
            var producer = new AdvancePrimitives(NO_OBSERVATION, status(fixture), Clock.systemUTC(), 8, scope);
            fixture.writer.locked(same -> {
                borrowed.set(same);
                scope.within(source, () -> {
                    for (Mode mode : List.of(Mode.EMPTY_EVIDENCE, Mode.CHANGED_WIRE)) {
                        source.mode = mode;
                        assertThrows(IllegalArgumentException.class, () -> producer.prepare(same, command, RequestIds.forCommand(command)));
                    }
                    assertThrows(IllegalArgumentException.class, () -> scope.within(source, () -> null)); return null;
                });
                assertFalse(scope.active()); source.mode = Mode.ORIGINAL;
                assertThrows(IOException.class, () -> scope.within(source, () -> { throw new IOException("actual callback failed"); }));
                assertFalse(scope.active()); borrowed.set(null); return null;
            });
            assertEquals(0, fixture.nativeActionWrites());
        }
    }

    @Test void staleCanonicalSessionAndEscapedScopeNeverReuseAFormerPrivateSource() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(directory.resolve("escaped-session"), false)) {
            var command = primitive(fixture.command("actual-escape-interface"), "resume-map");
            var stale = new AtomicReference<Session>(); fixture.writer.locked(same -> { stale.set(same); return null; });
            var borrowed = new AtomicReference<Session>(); var scope = new PendingUiLifeAdvance.Scope(borrowed::get);
            var source = new InterfaceSource(fixture, parent(command));
            var producer = new AdvancePrimitives(NO_OBSERVATION, status(fixture), Clock.systemUTC(), 8, scope);
            fixture.writer.locked(same -> {
                borrowed.set(same); assertNotSame(stale.get(), same);
                scope.within(source, () -> {
                    assertThrows(IllegalArgumentException.class, () -> producer.prepare(stale.get(), command, RequestIds.forCommand(command)));
                    assertEquals(0, source.preparations); return null;
                });
                assertFalse(scope.active()); assertTrue(producer.prepare(command).preparationEvidence().isEmpty());
                assertEquals(0, source.preparations); borrowed.set(null); return null;
            });
            assertEquals(0, fixture.nativeActionWrites());
        }
    }
}
