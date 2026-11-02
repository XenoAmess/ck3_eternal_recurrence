package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;

final class DriverBulkMembership309Test {
    @TempDir Path directory;
    private static final OperationKey OP = new OperationKey("bulk-membership-rejection");

    @Test void bulkMembershipValidatesTwoActualRejectionsWithoutChainMutation() throws Exception {
        var held = new AtomicReference<ActionWriterIntegrationFixture>();
        var scenario = new ActionWriterIntegrationFixture.SoftwareActionScenario(OP, "game.command." + OP.value(),
            (command, attempt, dispatch) -> {
                var actual = held.get();
                var ack = assertInstanceOf(NativeActionPort.AckReceived.class, dispatch);
                return new ActionPorts.RejectionObserved(new ActionState.Rejected(attempt.requestId(), "bulk rejection", actual.archive.referenceOf(ack)));
            }, () -> {}, () -> new RawJson(DriverJson.encode(new Obj(Map.of("accepted", new Bool(false))))));

        var reads = new ActionWriterIntegrationFixture.SoftwareReadScenario(
            ExactCk3Build.CK3_12004.executableSha256(), "ck3-1.20.0.4-msvc-x64",
            ignored -> List.of(), ignored -> { throw new AssertionError("no additional ordinary READ installed"); },
            Optional.of(ExactCk3Build.CK3_12004.version()), Set.of(NativeFreshSnapshotPort.CAPABILITY));
        try (var fixture = new ActionWriterIntegrationFixture(directory.resolve("bulk"), false, reads, List.of(scenario))) {
            fixture.configureSoftwareFreshRead179("success");
            held.set(fixture);
            var witness = fixture.writer.locked(same -> fixture.archive.withSession(same).preserveMaterial(RawJson.fullMaterial("{\"bulk\":true}".getBytes())));
            var materials = new ActualMaterials(fixture, witness);
            fixture.bindAdditionalArchivedVerifier(materials.binding());
            var publisher = new DriverActionHistoryPublisher(fixture.driverAuthority(), fixture.journal, fixture.archive, materials, List.of(fixture.observationSource().sourceRef()));
            fixture.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_ACTION_HISTORY_KIND, publisher);

            var receipt1 = fixture.coordinator.execute(fixture.command("bulk-1"));
            assertTrue(receipt1.settled());
            var coverage1 = fixture.writer.locked(same -> {
                var published = assertInstanceOf(DriverActionHistoryPublisher.Published.class, publisher.completed(same, receipt1));
                return DriverActionHistoryState.findCommittedCoverage(same, receipt1, fixture.archive.withSession(same)).orElseThrow();
            });

            var receipt2 = fixture.coordinator.execute(fixture.command("bulk-2"));
            assertTrue(receipt2.settled());
            var coverage2 = fixture.writer.locked(same -> {
                var published = assertInstanceOf(DriverActionHistoryPublisher.Published.class, publisher.completed(same, receipt2));
                return DriverActionHistoryState.findCommittedCoverage(same, receipt2, fixture.archive.withSession(same)).orElseThrow();
            });

            var pub1 = coverage1.publication();
            var pub2 = coverage2.publication();

            fixture.writer.locked(same -> {
                var head = same.head();
                var originals = fixture.archive.withSession(same);
                var src1 = DriverActionHistoryCodec.decode(originals.loadMaterial(pub1.originalSource()));
                var src2 = DriverActionHistoryCodec.decode(originals.loadMaterial(pub2.originalSource()));
                assertInstanceOf(DriverActionHistoryCodec.CanonicalOnly.class, src1.material());
                assertInstanceOf(DriverActionHistoryCodec.CanonicalOnly.class, src2.material());
                var driverBytes = fixture.driverAuthority().withFrozenFacts(same, frozen -> ((DriverSnapshotFacts.Known)frozen.state()).driver().encode());
                var actionWrites = fixture.nativeActionWrites();
                var readWrites = fixture.nativeReadWrites();

                var loadCount = new AtomicInteger(0);
                var lastRecord = new AtomicReference<ExactRef>();
                var handler = new InvocationHandler() {
                    @Override public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
                        if (method.getName().equals("loadRecord")) {
                            loadCount.incrementAndGet();
                            var ref = (ExactRef) args[0];
                            lastRecord.set(ref);
                        }
                        try {
                            return method.invoke(originals, args);
                        } catch (java.lang.reflect.InvocationTargetException e) {
                            throw e.getCause();
                        }
                    }
                };
                var counted = (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(originals.getClass().getClassLoader(), new Class<?>[]{ActionPorts.OutcomeArchive.class}, handler);

                loadCount.set(0);
                var single1 = ContinuityActionJournal.requireHistoricalReceipt(head.state(), receipt1, counted);
                var single2 = ContinuityActionJournal.requireHistoricalReceipt(head.state(), receipt2, counted);
                var singleCount = loadCount.get();

                loadCount.set(0);
                var bulk = ContinuityActionJournal.requireHistoricalReceipts(head.state(), List.of(receipt1, receipt2), counted);
                var bulkCount = loadCount.get();

                assertEquals(single1, bulk.get(0));
                assertEquals(single2, bulk.get(1));
                assertTrue(bulkCount > 0 && bulkCount < singleCount, "Bulk must reduce full-chain loadRecord invocations");

                loadCount.set(0);
                ContinuityActionJournal.requireHistoricalReceipts(head.state(), List.of(receipt1, receipt2), counted);
                assertEquals(bulkCount, loadCount.get(), "Same unchanged head must receive a fresh full bulk validation");

                DriverActionHistoryCodec.requireCanonicalMemberships(same, List.of(receipt1, receipt2), List.of(src1, src2), counted);
                DriverActionHistoryState.requireOriginals(same, List.of(pub1, pub2), List.of(receipt1, receipt2), counted);
                assertUnchanged(fixture, same, head.digest(), driverBytes, actionWrites, readWrites);
                var lateRecord = lastRecord.get();
                assertNotNull(lateRecord);

                assertThrows(IllegalArgumentException.class, () -> DriverActionHistoryState.requireOriginals(same, List.of(pub1, pub2), List.of(receipt2, receipt1), counted));
                assertUnchanged(fixture, same, head.digest(), driverBytes, actionWrites, readWrites);
                assertThrows(IllegalArgumentException.class, () -> DriverActionHistoryState.requireOriginals(same, List.of(pub1), List.of(receipt1, receipt2), counted));
                assertUnchanged(fixture, same, head.digest(), driverBytes, actionWrites, readWrites);

                var marker = new UncheckedIOException(new IOException("injected"));
                var failingHandler = new InvocationHandler() {
                    @Override public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
                        if (method.getName().equals("loadRecord") && args[0].equals(lateRecord)) throw marker;
                        try { return method.invoke(originals, args); } catch (java.lang.reflect.InvocationTargetException e) { throw e.getCause(); }
                    }
                };
                var failing = (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(originals.getClass().getClassLoader(), new Class<?>[]{ActionPorts.OutcomeArchive.class}, failingHandler);
                var thrown = assertThrows(UncheckedIOException.class, () -> DriverActionHistoryState.requireOriginals(same, List.of(pub1, pub2), List.of(receipt1, receipt2), failing));
                assertSame(marker, thrown);

                assertUnchanged(fixture, same, head.digest(), driverBytes, actionWrites, readWrites);
                return null;
            });
        }
    }

    private static void assertUnchanged(ActionWriterIntegrationFixture fixture, Session same,
            String head, byte[] driverBytes, int actionWrites, int readWrites) throws IOException {
        assertEquals(head, same.head().digest());
        assertEquals(actionWrites, fixture.nativeActionWrites());
        assertEquals(readWrites, fixture.nativeReadWrites());
        assertArrayEquals(driverBytes, fixture.driverAuthority().withFrozenFacts(same,
                frozen -> assertInstanceOf(DriverSnapshotFacts.Known.class, frozen.state()).driver().encode()));
    }

    private static final class ActualMaterials implements DriverActionHistoryPublisher.MaterialSource {
        private final ActionWriterIntegrationFixture fixture;
        private final ExactRef witness;
        ActualMaterials(ActionWriterIntegrationFixture fixture, ExactRef witness) { this.fixture = fixture; this.witness = witness; }
        NativeRecordedEvidenceVerifier.Binding binding() { return new NativeRecordedEvidenceVerifier.Binding(OP, fixture.observationSource().sourceRef(), (head, receipt, originals) -> requireRejection(receipt, originals)); }
        @Override public List<ExactRef> sources() { return List.of(fixture.observationSource().sourceRef()); }
        @Override public void requireOwner(DriverStateAssembler authority, ActionJournal journal, ActionPorts.OutcomeArchive archive) { assertSame(fixture.driverAuthority(), authority); assertSame(fixture.journal, journal); assertSame(fixture.archive, archive); }
        private DriverActionHistoryCodec.CanonicalOnly material(ActionReceipt actual) {
            var attempt = ActionTransitions.attempt(actual.state()).orElseThrow();
            return new DriverActionHistoryCodec.CanonicalOnly(DriverActionHistoryCodec.CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,
                List.of(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.NATIVE_FRAME, attempt.guard().nativeEvidence()),
                        new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL, witness)), sources());
        }
        @Override public DriverActionHistoryCodec.OriginalMaterial capture(Session same, ActionReceipt actual, ActionPorts.OutcomeArchive originals) throws IOException {
            var material = material(actual); requireOriginal(same, actual, material, originals); return material;
        }
        @Override public void requireOriginal(Session same, ActionReceipt actual, DriverActionHistoryCodec.OriginalMaterial material, ActionPorts.OutcomeArchive originals) throws IOException {
            fixture.writer.requireSession(same); assertEquals(material(actual), material);
            var verifier = new NativeRecordedEvidenceVerifier(fixture.archive, fixture.journal::borrowedWriterSession, (borrowed, ref, maximum) -> fixture.archive.readArtifact(borrowed, ref, maximum), fixture.frameLoader(), List.of(binding()));
            verifier.verify(same.head(), actual); requireRejection(actual, originals);
            var raw = originals.loadFullMaterial(witness); assertEquals(witness.bytes(), raw.bytes().length); assertEquals(witness.sha256(), DriverJson.sha256(raw.bytes()));
        }
        private static void requireRejection(ActionReceipt actual, ActionPorts.OutcomeArchive originals) {
            assertEquals(OP, actual.command().operation()); var settled = assertInstanceOf(ActionState.Settled.class, actual.state());
            var rejected = assertInstanceOf(ActionState.Rejected.class, settled.settlement()); var ack = assertInstanceOf(NativeActionPort.AckReceived.class, settled.dispatch());
            assertEquals(ack.requestId(), rejected.requestId()); assertEquals(originals.referenceOf(ack), rejected.originalEvidence()); assertEquals(ack, originals.load(rejected.originalEvidence()));
            assertEquals(new Bool(false), DriverJson.object(ack.originalResultToken().orElseThrow().bytes(), DriverJson.MAX_NATIVE_BYTES).get("accepted"));
        }
    }
}