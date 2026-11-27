package org.xar.ck3.control.application.session;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.List;
import java.util.Optional;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.StorageWriteGuardTestSupport;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

final class ExternalSaveRemountTest {
    @TempDir Path root;
    @Test void observedRemountDefersOnlyTheActualEmptyBatchAndPreservesOriginalSavedFrontier() throws Exception {
        try (var raw = getClass().getResourceAsStream("source56-named-remount.json.gz");
             var fixture = new GZIPInputStream(raw)) {
            var observed = StrictJson.parse(fixture.readAllBytes(), ContinuityJson.DOCUMENT_MAX_BYTES);
            var v1 = (ObjectNode) observed.get("v1");
            var previous = ExternalSaveOrigin.fromJson(v1.get("origin"));
            assertTrue(ContinuityJson.same(v1.get("origin"), previous.toJson()));
            var before = ContinuityState.fromJson((ObjectNode) observed.get("head"), previous.successor().machineId());
            var previousRef = ExactRef.fromJson(v1.get("origin_ref"));
            assertEquals(65, before.sequence());
            var game = new GameGeneration(previous.successor().game().pid() + 1, previous.successor().game().creationFiletime());
            var successor = new SessionIdentity(previous.successor().machineId(), game, "software-remount-successor");
            var session = new TransportSession(successor.machineId(), game, BigInteger.ONE, successor.sessionId());
            var opening = new ExternalSaveOrigin.NativeOpening(session, previous.opening().actor(),
                    previous.opening().dateRaw(), "native:1", BigInteger.ONE);
            var batch = before.toJson().get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD).path("batch_id").textValue();
            var loaded = previous.loadedFile();
            var oldSave = loaded.reference();
            var copy = new CheckpointPair.FileWitness(new ExactRef(oldSave.path() + ".software-test", oldSave.bytes(), oldSave.sha256()), loaded.identity());
            var remount = new ExternalSaveOrigin(before.sequence(), ContinuityJson.digest(before.toJson()),
                    previous.successor(), successor, previous.savedPair(), copy, previous.retiredActionHead(),
                    opening, Optional.of(previousRef), Optional.of(batch));
            remount.requirePreviousOrigin(previous);
            assertEquals(remount, ExternalSaveOrigin.fromJson(remount.toJson()));
            var archive = (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(getClass().getClassLoader(),
                    new Class<?>[]{ActionPorts.OutcomeArchive.class}, (proxy, method, args) -> {
                        throw new AssertionError("pure replay accessed an original: " + method);
                    });
            var cycles = new OrdinaryCycleTransitions(archive, (same, owner, original) -> { throw new AssertionError(); },
                    (same, owner, pair, proof) -> { throw new AssertionError(); },
                    new OriginalWindowReducer.Policy(before.origin().targetDays()), same -> { throw new AssertionError(); });
            var details = v1.deepCopy();
            details.put("source", ExternalSaveOrigin.REMOUNT_SOURCE);
            details.set("session", OrdinaryCycleTransitions.sessionToJson(successor));
            details.set("origin", remount.toJson());
            var reference = new ExactRef("software:remount-origin", 1, "a".repeat(64));
            details.set("origin_ref", reference.toJson());
            var semantic = (ObjectNode) details.get("semantic");
            var identity = (ObjectNode) semantic.get("frame");
            identity.set("game", game.toJson());
            ((ObjectNode) identity.get("frame")).put("native_revision", "1").put("revision", "1").put("snapshot_id", "native:1");
            var request = new WriterContracts.Request(OrdinaryCycleTransitions.CYCLE_KIND,
                    ContinuityJson.canonical(details), List.of());
            var after = actualWriterCommit(before, cycles, request);

            assertEquals(game, GameGeneration.fromJson(after.toJson().get("game_binding")));
            assertEquals(53179944, after.toJson().path("latest_binding").path("date_raw").longValue());
            assertEquals(53179344, after.settledDateRaw());
            assertEquals(471, (after.settledDateRaw() - after.origin().startDateRaw()) / 24);
            assertEquals(before.settledCycles(), after.settledCycles());
            assertEquals(57, after.toJson().path(OrdinaryCycleTransitions.STATE_FIELD).path("completed_cycles").longValue());
            assertEquals(ContinuityActionJournal.recordHead(before), ContinuityActionJournal.recordHead(after));
            var boundary = after.toJson().path(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD);
            assertEquals(batch, boundary.path("batch_id").textValue());
            assertEquals("BATCH_DEFERRED", boundary.path("boundary").textValue());
            assertEquals(previous.successor(), OrdinaryCycleTransitions.sessionFromJson(boundary.get("session")));
            assertEquals(reference, ExactRef.fromJson(after.toJson().get(WriterContracts.ORDINARY_EXTERNAL_SAVE_ORIGIN_FIELD)));

            var wrongFile = new CheckpointPair.FileWitness(new ExactRef(copy.reference().path(), oldSave.bytes(), "b".repeat(64)), loaded.identity());
            var wrong = new ExternalSaveOrigin(remount.predecessorSequence(), remount.predecessorDigest(),
                    remount.departed(), remount.successor(), remount.savedPair(), wrongFile, remount.retiredActionHead(),
                    remount.opening(), remount.previousOrigin(), remount.deferredBatch());
            assertThrows(IllegalArgumentException.class, () -> wrong.requirePreviousOrigin(previous));
        }
    }

    private ContinuityState actualWriterCommit(ContinuityState before, OrdinaryCycleTransitions cycles,
            WriterContracts.Request request) throws Exception {
        byte[] initial = before.canonicalBytes();
        var anchor = Files.write(root.resolve("anchor.json"), initial);
        var source = new ExactRef(anchor.toString(), initial.length, ActionCodec.sha256(initial));
        var layout = new WriterContracts.Layout(Files.write(root.resolve("continuity.json"), initial), source, before.machineId());
        Files.createFile(layout.lock());
        Files.createDirectory(layout.events());
        var corruptBoundary = new AtomicBoolean();
        var authority = new WriterContracts.TransitionAuthority() {
            @Override public String revalidate(ContinuityState predecessor, WriterContracts.Request supplied) {
                return supplied.identity();
            }

            @Override public ContinuityState reduce(ContinuityState predecessor, WriterContracts.Request supplied) {
                var reduced = cycles.reduce(predecessor, supplied);
                if (!corruptBoundary.get()) return reduced;
                var body = reduced.toJson();
                ((ObjectNode) body.get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD)).put("boundary", "BATCH_FINISHED");
                return ContinuityState.fromJson(body, predecessor.machineId());
            }
        };
        var guard = StorageWriteGuardTestSupport.create(layout);
        var writer = new ContinuityWriter(layout, List.of(source), authority, Clock.systemUTC(), guard);

        writer.locked(same -> {
            var prepared = same.preview(request);
            corruptBoundary.set(true);
            try {
                assertThrows(ContractViolationException.class, () -> same.commit(prepared));
                assertArrayEquals(initial, Files.readAllBytes(layout.snapshot()));
                assertFalse(Files.exists(layout.event(before.sequence() + 1)));
            } finally {
                corruptBoundary.set(false);
            }
            return null;
        });

        var committed = writer.locked(same -> {
            var prepared = same.preview(request);
            var accepted = same.commit(prepared);
            same.requireCommitted(prepared, accepted);
            return accepted;
        });
        assertEquals(WriterContracts.Disposition.COMMITTED, committed.disposition());
        assertEquals(before.sequence() + 1, committed.head().sequence());
        assertTrue(Files.isRegularFile(layout.event(committed.head().sequence())));
        var reopened = new ContinuityWriter(layout, List.of(source), authority, Clock.systemUTC(), guard);
        reopened.locked(same -> {
            assertArrayEquals(committed.head().canonicalBytes(), same.head().state().canonicalBytes());
            return null;
        });
        return committed.head();
    }
}
