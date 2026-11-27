package org.xar.ck3.control.application.session;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
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
            var after = cycles.reduce(before, new WriterContracts.Request(OrdinaryCycleTransitions.CYCLE_KIND,
                    ContinuityJson.canonical(details), List.of()));

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
}
