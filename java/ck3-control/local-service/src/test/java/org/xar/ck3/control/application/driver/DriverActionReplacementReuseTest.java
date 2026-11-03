package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Real owned software writer/publisher, controlled public archive DATA fault edges. No Game or private issuer. */
final class DriverActionReplacementReuseTest {
    @TempDir Path directory;
    private static final OperationKey DIRECT = new OperationKey("fixture-replacement-rejection");
    private enum Mode { NORMAL_ALIAS, LOAD_EXCEPTION, READBACK_MISMATCH, SUBCLASS_FLIP }

    private static final class MutableActor extends BigInteger {
        private static final long serialVersionUID = 1L;
        private final String original;
        private boolean flipped;
        MutableActor(BigInteger value) { super(value.toString()); original = value.toString(); }
        @Override public String toString() { return flipped ? (original.equals("1") ? "2" : "1") : original; }
    }

    private final class Run implements AutoCloseable {
        final ActionWriterIntegrationFixture fixture;
        final DriverStateAssembler authority;
        final DriverFactsRepository facts;
        final DriverSnapshotFacts.Known before;
        final DriverActionHistoryPublisher publisher;
        final ActionReceipt receipt;
        final ArchiveEdge edge;
        final MutableActor actor;
        final byte[] expected;
        final int nativeReads, nativeWrites;
        Run(String name, Mode mode) throws Exception {
            var held = new AtomicReference<ActionWriterIntegrationFixture>();
            var scenario = new ActionWriterIntegrationFixture.SoftwareActionScenario(DIRECT,
                    "game.command." + DIRECT.value(), (command, attempt, dispatch) -> {
                var actual = held.get();
                var ack = (NativeActionPort.AckReceived) dispatch;
                return new ActionPorts.RejectionObserved(new ActionState.Rejected(attempt.requestId(),
                        "controlled software rejection", actual.archive.referenceOf(ack)));
            }, () -> {}, () -> new RawJson(DriverJson.encode(new Obj(Map.of("accepted", new Bool(false))))));
            fixture = new ActionWriterIntegrationFixture(directory.resolve(name), false, scenario);
            held.set(fixture);
            try {
            DriverSnapshotFacts.Known original = fixture.writer.locked(same ->
                    fixture.driverAuthority().withFrozenFacts(same, frozen -> (DriverSnapshotFacts.Known) frozen.state()));
            actor = mode == Mode.SUBCLASS_FLIP ? new MutableActor(original.driver().session().actorId()) : null;
            DriverStateSnapshot.Complete driver = original.driver();
            if (actor != null) {
                var s = driver.session();
                driver = new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session(s.pipeName(), s.bridgePid(), actor, s.episodeRunId()),
                        driver.commandHistory(), driver.lastCheckpoint(), driver.rollbackWarFailure(), driver.managedRestoreTransaction(),
                        driver.successionExpectation(), driver.successionLifecycle(), driver.campaignGoal(), driver.rollbackWarFailures());
            }
            before = new DriverSnapshotFacts.Known(driver, original.stamp(), original.originalHistoryBasis(),
                    original.actionRows(), original.auxiliary(), original.loop(), original.observation());
            expected = driver.encode();
            facts = new DriverFactsRepository(before);
            authority = new DriverStateAssembler(new ActionSnapshotReader(fixture.journal), facts,
                    frame -> { throw new AssertionError("publisher must not synthesize a new observation"); });
            edge = new ArchiveEdge(fixture.archive, expected, mode, actor);
            authority.bindHistoryArchive(edge.owner, fixture.journal::borrowedWriterSession);
            ExactRef witness = fixture.writer.locked(same -> fixture.archive.withSession(same)
                    .preserveMaterial(new RawJson(DriverJson.encode(new Obj(Map.of("owned_material", new Bool(true)))))));
            var materials = new ActualMaterials(this, witness);
            fixture.bindAdditionalArchivedVerifier(materials.binding());
            publisher = new DriverActionHistoryPublisher(authority, fixture.journal, edge.owner, materials,
                    List.of(fixture.observationSource().sourceRef()));
            fixture.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_ACTION_HISTORY_KIND, publisher);
            receipt = fixture.coordinator.execute(fixture.command("replacement-" + name));
            nativeReads = fixture.nativeReadWrites(); nativeWrites = fixture.nativeActionWrites();
            } catch (Exception | Error failure) {
                try { fixture.close(); } catch (Exception closing) { failure.addSuppressed(closing); }
                throw failure;
            }
        }
        DriverSnapshotFacts.Known current(Session same) throws IOException {
            return authority.withFrozenFacts(same, frozen -> (DriverSnapshotFacts.Known) frozen.state());
        }
        @Override public void close() throws IOException { fixture.close(); }
    }

    private static final class ArchiveEdge {
        final ActionPorts.OutcomeArchive owner;
        final byte[] expected;
        final Mode mode;
        final MutableActor actor;
        final List<String> calls = new ArrayList<>();
        final UncheckedIOException failure = new UncheckedIOException("controlled fresh readback failure", new IOException("fixture only"));
        ExactRef full;
        int realFullLoads;
        int laterBeforeReferences;
        ArchiveEdge(ActionPorts.OutcomeArchive original, byte[] expected, Mode mode, MutableActor actor) {
            this.expected = expected.clone(); this.mode = mode; this.actor = actor; owner = wrap(original);
        }
        private ActionPorts.OutcomeArchive wrap(ActionPorts.OutcomeArchive original) {
            return (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                    new Class<?>[] {ActionPorts.OutcomeArchive.class}, (proxy, method, args) -> {
                if (method.getDeclaringClass() == Object.class) {
                    if (method.getName().equals("equals")) return proxy == args[0];
                    if (method.getName().equals("hashCode")) return System.identityHashCode(proxy);
                    return "owned archive software edge";
                }
                Object result = invoke(original, method, args);
                if (method.getName().equals("withSession")) return wrap((ActionPorts.OutcomeArchive) result);
                if (method.getName().equals("preserveMaterial") && ((RawJson) args[0]).contentEquals(expected)) {
                    full = (ExactRef) result; calls.add("preserve-full");
                    byte[] detached = ((RawJson) args[0]).bytes(); Arrays.fill(detached, (byte) '!');
                }
                if (method.getName().equals("materialReferenceOf") && full != null) {
                    laterBeforeReferences++; calls.add("before-reference");
                }
                if (method.getName().equals("loadFullMaterial") && full != null && full.equals(args[0])) {
                    realFullLoads++; calls.add("real-load-full");
                    RawJson actual = (RawJson) result;
                    // Delegate physically reads before any controlled DATA callback mutation/fault below.
                    byte[] detached = actual.bytes(); Arrays.fill(detached, (byte) '?');
                    if (realFullLoads == 1) {
                        if (mode == Mode.LOAD_EXCEPTION) throw failure;
                        if (mode == Mode.SUBCLASS_FLIP) actor.flipped = true;
                        if (mode == Mode.READBACK_MISMATCH) {
                            var d = DriverStateSnapshot.decodeComplete(expected); var s = d.session();
                            var changed = new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session(s.pipeName() + ".other", s.bridgePid(), s.actorId(), s.episodeRunId()),
                                    d.commandHistory(), d.lastCheckpoint(), d.rollbackWarFailure(), d.managedRestoreTransaction(),
                                    d.successionExpectation(), d.successionLifecycle(), d.campaignGoal(), d.rollbackWarFailures());
                            return RawJson.fullMaterial(changed.encode());
                        }
                    }
                }
                return result;
            });
        }
        private static Object invoke(Object original, Method method, Object[] args) throws Throwable {
            try { return method.invoke(original, args); }
            catch (InvocationTargetException failure) { throw failure.getCause(); }
        }
    }

    private static final class ActualMaterials implements DriverActionHistoryPublisher.MaterialSource {
        private final Run run;
        private final ExactRef witness;
        ActualMaterials(Run run, ExactRef witness) { this.run = run; this.witness = witness; }
        NativeRecordedEvidenceVerifier.Binding binding() {
            return new NativeRecordedEvidenceVerifier.Binding(DIRECT, run.fixture.observationSource().sourceRef(),
                    (head, receipt, originals) -> requireRejection(receipt, originals));
        }
        @Override public List<ExactRef> sources() { return List.of(run.fixture.observationSource().sourceRef()); }
        @Override public void requireOwner(DriverStateAssembler authority, ActionJournal journal, ActionPorts.OutcomeArchive archive) {
            if (authority != run.authority || journal != run.fixture.journal || archive != run.edge.owner)
                throw new AssertionError("owned publisher graph changed");
        }
        private DriverActionHistoryCodec.CanonicalOnly material(ActionReceipt actual) {
            var attempt = ActionTransitions.attempt(actual.state()).orElseThrow();
            return new DriverActionHistoryCodec.CanonicalOnly(DriverActionHistoryCodec.CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,
                    List.of(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.NATIVE_FRAME, attempt.guard().nativeEvidence()),
                            new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL, witness)), sources());
        }
        @Override public DriverActionHistoryCodec.OriginalMaterial capture(Session same, ActionReceipt actual, ActionPorts.OutcomeArchive originals) throws IOException {
            var captured = material(actual); requireOriginal(same, actual, captured, originals); return captured;
        }
        @Override public void requireOriginal(Session same, ActionReceipt actual, DriverActionHistoryCodec.OriginalMaterial material,
                ActionPorts.OutcomeArchive originals) throws IOException {
            run.fixture.writer.requireSession(same);
            if (!material(actual).equals(material)) throw new AssertionError("owned material changed");
            var verifier = new NativeRecordedEvidenceVerifier(run.fixture.archive, run.fixture.journal::borrowedWriterSession,
                    (borrowed, ref, maximum) -> run.fixture.archive.readArtifact(borrowed, ref, maximum), run.fixture.frameLoader(), List.of(binding()));
            verifier.verify(same.head(), actual); requireRejection(actual, originals);
            var raw = originals.loadFullMaterial(witness);
            if (raw.bytes().length != witness.bytes() || !DriverJson.sha256(raw.bytes()).equals(witness.sha256()))
                throw new AssertionError("owned witness original changed");
        }
        private static void requireRejection(ActionReceipt actual, ActionPorts.OutcomeArchive originals) {
            if (!DIRECT.equals(actual.command().operation())) throw new AssertionError("controlled operation changed");
            var settled = (ActionState.Settled) actual.state(); var rejected = (ActionState.Rejected) settled.settlement();
            var ack = (NativeActionPort.AckReceived) settled.dispatch();
            if (!ack.requestId().equals(rejected.requestId()) || !originals.referenceOf(ack).equals(rejected.originalEvidence())
                    || !ack.equals(originals.load(rejected.originalEvidence()))) throw new AssertionError("actual software rejection originals changed");
        }
    }

    @Test void immutableReplacementSurvivesByteAliasesAndPublishesActualHash() throws Exception {
        try (var run = new Run("normal-alias", Mode.NORMAL_ALIAS)) {
            run.fixture.writer.locked(same -> {
                assertEquals(BigInteger.class, run.before.driver().session().actorId().getClass());
                var published = assertInstanceOf(DriverActionHistoryPublisher.Published.class,
                        run.publisher.completed(same, run.receipt));
                var current = run.current(same);
                assertEquals(run.before.stamp(), published.before());
                assertEquals(Math.addExact(run.before.stamp().driverVersion(), 1), published.after().driverVersion());
                assertEquals(published.after(), current.stamp());
                assertEquals(DriverJson.sha256(run.expected), published.after().driverSha256());
                assertArrayEquals(run.expected, current.driver().encode());
                assertTrue(current.actionRows().stream().anyMatch(row ->
                        row.actionId().equals(run.receipt.command().actionId())
                                && row.bodySha256().equals(run.receipt.bodySha256())
                                && row.durableSequence() == run.receipt.sequence()));
                assertTrue(run.edge.realFullLoads > 0, "the actual fresh full-material read must remain");
                assertTrue(run.edge.calls.indexOf("real-load-full") < run.edge.calls.indexOf("before-reference"));
                var originals = run.fixture.archive.withSession(same);
                var archived = originals.loadFullMaterial(published.fullDriver());
                assertArrayEquals(run.expected, archived.bytes());
                assertEquals(DriverJson.sha256(run.expected), published.fullDriver().sha256());
                byte[] detached = archived.bytes();
                Arrays.fill(detached, (byte) '!');
                assertArrayEquals(run.expected, archived.bytes());
                assertArrayEquals(run.expected, originals.loadFullMaterial(published.fullDriver()).bytes());
                assertArrayEquals(run.expected, current.driver().encode());
                assertFalse(run.publisher.hasPending(same));
                assertEquals(run.nativeReads, run.fixture.nativeReadWrites());
                assertEquals(run.nativeWrites, run.fixture.nativeActionWrites());
                return null;
            });
        }
    }

    @Test void freshReadbackFaultsAndValidMismatchAbortBeforeLaterPublication() throws Exception {
        for (Mode mode : List.of(Mode.LOAD_EXCEPTION, Mode.READBACK_MISMATCH)) {
            try (var run = new Run("fresh-" + mode.name(), mode)) {
                run.fixture.writer.locked(same -> {
                    String head = same.head().digest();
                    long sequence = same.head().state().sequence();
                    assertSame(run.before, run.current(same));
                    if (mode == Mode.LOAD_EXCEPTION) {
                        var failure = assertThrows(UncheckedIOException.class,
                                () -> run.publisher.completed(same, run.receipt));
                        assertSame(run.edge.failure, failure);
                    } else {
                        var failure = assertThrows(IllegalArgumentException.class,
                                () -> run.publisher.completed(same, run.receipt));
                        assertEquals("actual full Driver archive readback differs", failure.getMessage());
                    }
                    assertEquals(1, run.edge.realFullLoads);
                    assertEquals(0, run.edge.laterBeforeReferences);
                    assertEquals(List.of("preserve-full", "real-load-full"), run.edge.calls);
                    assertEquals(head, same.head().digest());
                    assertEquals(sequence, same.head().state().sequence());
                    assertSame(run.before, run.current(same));
                    assertArrayEquals(run.expected, run.before.driver().encode());
                    assertFalse(run.publisher.hasPending(same));
                    assertEquals(run.nativeReads, run.fixture.nativeReadWrites());
                    assertEquals(run.nativeWrites, run.fixture.nativeActionWrites());
                    return null;
                });
            }
        }
    }

    @Test void subclassMutationAtFreshReadRetainsOriginalEarlyMismatch() throws Exception {
        try (var run = new Run("subclass-fresh-mutation", Mode.SUBCLASS_FLIP)) {
            run.fixture.writer.locked(same -> {
                String head = same.head().digest();
                long sequence = same.head().state().sequence();
                assertNotEquals(BigInteger.class, run.before.driver().session().actorId().getClass());
                assertArrayEquals(run.expected, run.before.driver().encode());
                assertFalse(run.actor.flipped);
                var failure = assertThrows(IllegalArgumentException.class,
                        () -> run.publisher.completed(same, run.receipt));
                assertEquals("actual full Driver archive readback differs", failure.getMessage());
                assertTrue(run.actor.flipped, "controlled mutation occurs only after the real archive load");
                assertFalse(Arrays.equals(run.expected, run.before.driver().encode()));
                assertEquals(1, run.edge.realFullLoads);
                assertEquals(0, run.edge.laterBeforeReferences);
                assertEquals(List.of("preserve-full", "real-load-full"), run.edge.calls);
                assertEquals(head, same.head().digest());
                assertEquals(sequence, same.head().state().sequence());
                assertSame(run.before, run.current(same));
                assertFalse(run.publisher.hasPending(same));
                assertEquals(run.nativeReads, run.fixture.nativeReadWrites());
                assertEquals(run.nativeWrites, run.fixture.nativeActionWrites());
                return null;
            });
        }
    }

}
