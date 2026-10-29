package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.service.root.CanonicalSaveReceiptVerifier;
import org.xar.ck3.control.service.root.RootSaveRuntime;

/** Thin assertions/physical file edge for the one real Root fixture. Creates no Root, guard, receipt, lease or private proof. */
public final class RootFirstCheckpointTestSupport {
    private RootFirstCheckpointTestSupport() { }
    /** Archived DATA, never a permission or a replacement for the original active physical lease. */
    public record GuardOriginals(Complete frame, SemanticEvidence semantic, DriverStateSnapshot.Complete driver,
            ExactRef sourceQualification, RootGuardEvidence.WriterPoint writerPoint) { }
    public record SavedPairOriginals(CheckpointPair pair, DriverStateSnapshot.Complete savedDriver,
            ActionReceipt canonicalSave, GuardOriginals submittedGuard) { }

    /**
     * Reads roles through the sole production v3 codec, then replays all four SEM originals. The caller supplies
     * the independently owned candidate identity/source; deriving them from the proposed guard proves nothing.
     */
    public static GuardOriginals requireGuardOriginals(ContinuityStorePort.Session same, ContinuityWriter writer,
            NativeOutcomeArchive archive, NativeEffectEvidence.FrameLoader actualFrameLoader, GuardEvidence actualGuard,
            SessionIdentity expectedOwner, G2Source expectedSource, String expectedRootAuthority) throws IOException {
        writer.requireSession(same); assertSame(writer, archive.writer()); String head = same.head().digest();
        assertInstanceOf(CommandOrigin.Gameplay.class, actualGuard.origin());
        assertEquals(RootSaveRuntime.OPERATION, actualGuard.operation()); assertEquals(expectedRootAuthority, actualGuard.authorityId());
        assertEquals(expectedSource, actualGuard.source()); assertEquals(expectedOwner.machineId(), actualGuard.origin().machineId());
        assertEquals(expectedOwner.game(), actualGuard.origin().game()); assertEquals(expectedOwner.sessionId(), actualGuard.sessionId());
        assertEquals(1, actualGuard.supportingEvidence().size(), "first SAVE has one actual Root v3 basis, never a flattened guard");
        var bound = archive.withSession(same);
        // Same-package access intentionally reuses the sole closed body parser; there is no copied v3 field table.
        var body = RootGuardEvidence.body(actualGuard, bound);
        assertEquals(RootGuardEvidence.SCHEMA, StrictJson.text(body.get("schema")));
        RootGuardEvidence.requireHistory(actualGuard, bound, same);
        Complete frame = RootGuardEvidence.loadFrame(actualGuard, bound, actualFrameLoader);
        var driverRoles = RootGuardEvidence.originalDriverSource(actualGuard, bound);
        var semantic = new SemanticEvidence(frame.identity(), ExactRef.fromJson(body.get("semantic")), frame.originalEvidence(),
                driverRoles.stampRef(), driverRoles.driverRef(), frame.observedAt());
        new NativeSemanticEvidenceVerifier(archive::readArtifact).verify(same, expectedOwner, semantic);
        DriverStateSnapshot.Complete driver = DriverStateSnapshot.decodeComplete(bound.loadMaterial(driverRoles.driverRef()).bytes());
        assertEquals(frame.identity().frame().episodeRunId(), driver.session().episodeRunId());
        assertEquals(frame.identity().frame().identity().player(), driver.session().actorId());
        assertEquals(expectedOwner.game().pid(), driver.session().bridgePid());
        ExactRef sourceProof = RootGuardEvidence.sourceQualification(actualGuard, bound).orElseThrow();
        var sourceBody = org.xar.ck3.control.application.driver.DriverJson.object(archive.readArtifact(same, sourceProof, 16 << 20), 16 << 20);
        assertEquals(new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text("xar.java-root-native-source-proof/v2"), sourceBody.get("schema"));
        assertEquals(new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text(expectedOwner.machineId()), sourceBody.get("machine_id"));
        assertEquals(new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text(expectedOwner.sessionId()), sourceBody.get("session_id"));
        assertEquals(expectedSource.sourceRef(), DriverObservationEvidenceReader.reference(sourceBody.get("source")));
        assertEquals(head, same.head().digest(), "archived first SAVE guard replay cannot change the original writer");
        return new GuardOriginals(frame, semantic, driver, sourceProof, RootGuardEvidence.writerPoint(actualGuard, bound));
    }

    /** Real canonical SAVE/pair replay, without calling execute, reconcile, or any Root private-proof constructor. */
    public static SavedPairOriginals requireCanonicalSavedPair(ContinuityStorePort.Session same, ContinuityWriter writer,
            NativeOutcomeArchive archive, ActionSnapshotReader actions, DriverCheckpointStore drivers,
            CanonicalSaveReceiptVerifier originalVerifier, NativeEffectEvidence.FrameLoader actualFrameLoader,
            ActionReceipt proposedOriginal, SessionIdentity expectedOwner, G2Source expectedSource,
            String expectedRootAuthority) throws IOException {
        writer.requireSession(same); String head = same.head().digest();
        ActionReceipt canonical = actions.withFrozen(same, held -> {
            ActionReceipt retained = held.find(proposedOriginal.command().actionId()).orElseThrow(); held.assertCurrent(); return retained;
        });
        assertEquals(proposedOriginal, canonical); assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED, canonical.outcome());
        assertInstanceOf(ActionState.Settled.class, canonical.state());
        assertEquals(RootSaveRuntime.OPERATION, canonical.command().operation());
        var bound = archive.withSession(same);
        assertEquals(canonical, bound.loadReceipt(bound.receiptReferenceOf(canonical)));
        // This real verifier reopens durable preparation/outbound/ACK/pair/full saved Driver and native poststate.
        originalVerifier.archivedBinding(expectedSource.sourceRef(), () -> same).verifier().verify(same.head(), canonical, bound);
        var applied = canonical.applied().orElseThrow().observation(); assertEquals(2, applied.supportingEvidence().size());
        CheckpointPair pair = CheckpointPairCodec.decode(bound.loadMaterial(applied.supportingEvidence().getFirst()).bytes());
        assertEquals(canonical.command().actionId(), pair.saveActionId()); assertEquals(expectedOwner.game(), pair.frame().game());
        assertEquals(expectedOwner.machineId(), pair.frame().machineId()); drivers.verify(pair);
        var saved = originalVerifier.retainedDriver(same, pair);
        assertArrayEquals(saved.encode(), DriverStateSnapshot.decodeComplete(bound.loadMaterial(applied.supportingEvidence().get(1)).bytes()).encode());
        assertEquals(pair.frame().frame().episodeRunId(), saved.session().episodeRunId());
        assertEquals(pair.frame().frame().identity().player(), saved.session().actorId());
        GuardOriginals guard = requireGuardOriginals(same, writer, archive, actualFrameLoader,
                ActionTransitions.attempt(canonical.state()).orElseThrow().guard(), expectedOwner, expectedSource, expectedRootAuthority);
        assertEquals(head, same.head().digest());
        return new SavedPairOriginals(pair, saved, canonical, guard);
    }

    /**
     * Finite software SAVE producer at the actual NativePacketPort write hook. It emits a real file only after
     * the real coordinator has durably entered Submitting with its actual produced guard. The fixture owns ACK
     * bytes and post-SAVE snapshots. This edge creates neither ACK nor GuardEvidence nor a business result.
     */
    public static final class NativeSaveFileEdge {
        private final ContinuityWriter writer; private final ActionSnapshotReader actions;
        private final NativeOutcomeArchive archive; private final NativeEffectEvidence.FrameLoader frames;
        private final CheckpointFiles files; private final Path savePath; private final byte[] softwareSaveContents;
        private final SessionIdentity owner; private final G2Source source; private final String authority; private final Clock clock;
        private int entered; private CheckpointPair.FileWitness emitted; private NativeWire.ExecuteRequest original;
        public NativeSaveFileEdge(ContinuityWriter writer, ActionSnapshotReader actions, NativeOutcomeArchive archive,
                CheckpointFiles files, Path canonicalSavePath, byte[] softwareSaveContents, SessionIdentity expectedOwner,
                G2Source expectedSource, String expectedRootAuthority, NativeEffectEvidence.FrameLoader actualFrameLoader, Clock clock) {
            this.writer = Objects.requireNonNull(writer); this.actions = Objects.requireNonNull(actions); this.archive = Objects.requireNonNull(archive);
            this.files = Objects.requireNonNull(files); savePath = Objects.requireNonNull(canonicalSavePath); this.frames = Objects.requireNonNull(actualFrameLoader);
            assertTrue(savePath.isAbsolute()); assertEquals("xar_checkpoint.ck3", savePath.getFileName().toString());
            this.softwareSaveContents = Objects.requireNonNull(softwareSaveContents).clone();
            assertTrue(this.softwareSaveContents.length > 0 && this.softwareSaveContents.length <= 65_536, "finite complete software file payload required");
            owner = Objects.requireNonNull(expectedOwner); source = Objects.requireNonNull(expectedSource);
            authority = StrictJson.text(expectedRootAuthority); this.clock = Objects.requireNonNull(clock);
        }
        public synchronized CheckpointPair.FileWitness onOriginalWrite(byte[] actualOutboundPacket, Instant deadline) throws IOException {
            assertEquals(0, entered, "the first SAVE must never be written again, including after UNKNOWN");
            assertTrue(clock.instant().isBefore(deadline)); var same = writer.borrowedSession(); writer.requireSession(same);
            NativeWire.ExecuteRequest wire = NativeWire.decodeExecuteRequest(actualOutboundPacket);
            assertEquals(RootSaveRuntime.OPERATION.value(), wire.step());
            try {
                actions.withFrozen(same, held -> {
                    ActionReceipt actual = held.find(held.activeActionId().orElseThrow()).orElseThrow();
                    assertInstanceOf(ActionState.Submitting.class, actual.state()); assertFalse(actual.settled());
                    var attempt = ActionTransitions.attempt(actual.state()).orElseThrow();
                    assertEquals(wire.requestId(), attempt.requestId()); assertEquals(RootSaveRuntime.OPERATION, actual.command().operation());
                    assertEquals(source, actual.command().source()); assertEquals(owner.sessionId(), actual.command().sessionId());
                    assertEquals(actual.command().before().frame().identity().nativeRevision(), wire.expectedRevision().or(wire::expectedSnapshotRevision).orElseThrow());
                    assertTrue(clock.instant().isBefore(actual.command().deadline())); assertTrue(clock.instant().isBefore(attempt.guard().validUntil()));
                    try { requireGuardOriginals(same, writer, archive, frames, attempt.guard(), owner, source, authority); }
                    catch (IOException failure) { throw new UncheckedIOException(failure); }
                    held.assertCurrent(); return null;
                });
            } catch (UncheckedIOException failure) { throw failure.getCause(); }
            // Mark write entry before filesystem mutation: a failed/unknown write cannot be replayed by this edge.
            entered++; original = wire;
            Optional<CheckpointPair.FileWitness> previous = files.observe(savePath);
            emitted = files.replace(savePath, softwareSaveContents.clone()); files.verify(emitted);
            assertEquals(emitted, files.observe(savePath).orElseThrow(), "the configured SAVE path must resolve to the same actual emitted file witness");
            assertTrue(previous.isEmpty() || !previous.orElseThrow().equals(emitted), "SAVE must change actual file identity/content/time");
            assertArrayEquals(softwareSaveContents, files.read(emitted, 65_536));
            return emitted;
        }
        public synchronized int enteredWrites() { return entered; }
        public synchronized Optional<CheckpointPair.FileWitness> emittedFile() { return Optional.ofNullable(emitted); }
        public synchronized Optional<NativeWire.ExecuteRequest> originalPacket() { return Optional.ofNullable(original); }
    }
}
