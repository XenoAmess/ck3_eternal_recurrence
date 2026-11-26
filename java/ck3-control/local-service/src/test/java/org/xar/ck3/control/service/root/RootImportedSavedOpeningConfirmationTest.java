package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.Base64;
import java.util.List;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledOnOs;
import org.junit.jupiter.api.condition.OS;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.SavedContinuityBootstrap;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.PortableRecoveryDataArchive;
import org.xar.ck3.control.continuity.writer.StorageWriteGuard;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Exact Source56 import followed by an offline, software-only SAVE and same-Game recovery. */
@EnabledOnOs(OS.WINDOWS)
final class RootImportedSavedOpeningConfirmationTest {
    private static final int MAX_FIXTURE_BYTES = 1 << 20;
    private static final String FIXTURE = "/org/xar/ck3/control/application/session/source56-opening-confirmed-save.json.gz";
    @TempDir Path directory;

    @Test void confirmedSaveCanProjectAnUnissuedOpeningAfterLaterRecovery() throws IOException {
        checkProjection(false);
    }

    @Test void laterHeadCannotSubstituteTheOlderImportedCheckpointForTheConfirmedSave() throws IOException {
        checkProjection(true);
    }

    private void checkProjection(boolean replacePairAtHead) throws IOException {
        var fixture = readFixture();
        var event66 = ContinuityJson.parseObject(bytes(fixture.get("events").get(0)), MAX_FIXTURE_BYTES);
        var save = ContinuityJson.parseObject(bytes(fixture.get("events").get(1)), MAX_FIXTURE_BYTES);
        var recovery = ContinuityJson.parseObject(bytes(fixture.get("events").get(3)), MAX_FIXTURE_BYTES);
        var marker = SavedContinuityBootstrap.request(
                ContinuityJson.object(recovery.path("after").get(SavedContinuityBootstrap.FIELD))).detailsObject();
        var owner = OrdinaryCycleTransitions.sessionFromJson(marker.get("session"));
        var original = ProposalLifecycleCodec.decodeObservation(marker.get("opening"));
        var source = G2Wire.source(marker.get("source"));
        var originalPair = CheckpointPairCodec.decode(ContinuityJson.canonical(marker.get("checkpoint_pair")));
        var savedPair = CheckpointPairCodec.decode(ContinuityJson.canonical(save.path("details").get("checkpoint_pair")));
        var proof = OrdinaryCycleTransitions.proofFromJson(save.path("details").get("completed_cycle_proof"));
        var fresh = OrdinaryCycleTransitions.semanticFromJson(recovery.path("details").get("semantic")).frame();
        assertEquals(53179344L, originalPair.frame().frame().identity().dateRaw().longValueExact());
        assertEquals(53179392L, savedPair.frame().frame().identity().dateRaw().longValueExact());
        assertEquals(58L, proof.completedCycles());
        assertEquals(38L, fresh.frame().identity().nativeRevision().longValueExact());
        assertEquals(36L, savedPair.frame().frame().identity().nativeRevision().longValueExact());
        if (replacePairAtHead) {
            ContinuityJson.object(recovery.path("after").get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD))
                    .set("pair", marker.get("checkpoint_pair"));
        }

        // The earlier canonical APPLIED SAVE after-state is the trusted start of this small test slice.
        var anchor = Files.write(directory.resolve("anchor.json"), ContinuityJson.canonical(event66.get("after")));
        var snapshot = Files.write(directory.resolve("continuity.json"), ContinuityJson.canonical(recovery.get("after")));
        var reviewed = Files.writeString(directory.resolve("reviewed.txt"), "Source56 offline SAVE confirmation test slice");
        var files = new NativeCheckpointFiles();
        var layout = new WriterContracts.Layout(snapshot, files.observe(anchor).orElseThrow().reference(), owner.machineId());
        Files.createFile(layout.lock());
        Files.createDirectory(layout.events());
        Files.write(layout.event(67), bytes(fixture.get("events").get(1)));
        Files.write(layout.event(68), bytes(fixture.get("events").get(2)));
        Files.write(layout.event(69), replacePairAtHead ? ContinuityJson.canonical(recovery) : bytes(fixture.get("events").get(3)));
        try (var storage = StorageWriteGuard.noWrites()) {
            var writer = ContinuityWriter.readOnlyExisting(layout, List.of(files.observe(reviewed).orElseThrow().reference()),
                    new WriterContracts.TransitionAuthority() {
                        @Override public String revalidate(ContinuityState before, WriterContracts.Request request) {
                            throw new AssertionError("historical projection cannot prepare a write");
                        }
                        @Override public ContinuityState reduce(ContinuityState before, WriterContracts.Request request) {
                            throw new AssertionError("historical projection cannot write a new edge");
                        }
                    }, Clock.systemUTC(), ContinuityWriter.Extensions.none(), storage);
            var archive = new PortableRecoveryDataArchive(writer::requireSession, (ref, maximum) -> {
                var object = fixture.path("cas").get(ref.sha256());
                if (ref.bytes() > maximum || object == null) throw new IOException("missing bounded software fixture archive " + ref.sha256());
                return bytes(object);
            }).proxy();
            var cycles = new OrdinaryCycleTransitions(archive, (session, actualOwner, evidence) -> {
                writer.requireSession(session);
                assertEquals(owner, actualOwner);
                // The portable fixture omits Full Driver and Native SEM payloads. Require the exact original four refs.
                assertEquals(proof.semantic(), evidence);
                return new OrdinaryCycleTransitions.VerifiedSemantic(evidence.frame(), evidence.observedAt(),
                        "source56-confirmed-save-test", evidence.semantic().sha256());
            }, (session, actualOwner, pair, completed) -> {
                throw new AssertionError("historical projection cannot verify physical SAVE again");
            }, new OriginalWindowReducer.Policy(10958), writer::requireSession);
            var journal = new ContinuityBatchJournal(writer, cycles);
            writer.locked(same -> {
                var before = same.head();
                var gate = DomainBodies.reference(before.state(), DomainBodies.Slot.OPENING_GATE).orElseThrow();
                assertEquals(69, before.state().sequence());
                assertEquals(58, before.state().settledCycles());
                assertEquals("793ad907e8387ea78b2b0d6ec153a176943336e632a6b920cccb85efdfc2171c", gate.payload().sha256());
                if (replacePairAtHead) {
                    var failure = assertThrows(IOException.class,
                            () -> journal.openingDateEvidence(same, owner, original, source, fresh));
                    assertEquals("Opening SAVE has no actual canonical receipt", failure.getMessage());
                } else {
                    var found = journal.openingDateEvidence(same, owner, original, source, fresh);
                    var verified = found.orElseThrow();
                    assertEquals(53179392L, verified.semantic().frame().frame().identity().dateRaw().longValueExact());
                    assertTrue(verified.evidence().containsAll(proof.semantic().references()));
                    assertTrue(verified.evidence().contains(ExactRef.fromJson(save.path("after")
                            .path(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD).path("state").get("head"))));
                    assertEquals(found, journal.openingDateEvidence(same, owner, original, source, fresh));
                    assertThrows(ContractViolationException.class,
                            () -> journal.openingDateEvidence(same, owner, original, source, savedPair.frame()));
                }
                assertEquals(before.digest(), same.head().digest());
                assertEquals(gate, DomainBodies.reference(same.head().state(), DomainBodies.Slot.OPENING_GATE).orElseThrow());
                return null;
            });
        }
    }

    private static com.fasterxml.jackson.databind.node.ObjectNode readFixture() throws IOException {
        try (var raw = RootImportedSavedOpeningConfirmationTest.class.getResourceAsStream(FIXTURE)) {
            assertNotNull(raw);
            try (var gzip = new GZIPInputStream(raw)) {
                byte[] actual = gzip.readNBytes(MAX_FIXTURE_BYTES + 1);
                assertTrue(actual.length <= MAX_FIXTURE_BYTES);
                return ContinuityJson.parseObject(actual, MAX_FIXTURE_BYTES);
            }
        }
    }

    private static byte[] bytes(com.fasterxml.jackson.databind.JsonNode node) {
        return Base64.getDecoder().decode(node.textValue());
    }
}
