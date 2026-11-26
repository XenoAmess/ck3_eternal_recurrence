package org.xar.ck3.control.application.session;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.time.Instant;
import java.util.Base64;
import java.util.List;
import java.util.Optional;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.SavedContinuityBootstrap;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.PortableRecoveryDataArchive;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;

/** Recovery04 through the original imported-save admission; the Driver payload and full event history are separate evidence. */
final class ImportedSavedInterruptedLifeRecoveryDataTest {
    private static final String HEAD_SHA = "2712b29737154b0fa7ac10c814961fb36f310df560aaf3f566d3438f77656718";
    private static final String OLD_FRONTIER_FAILURE = "settled recovery requires its unsaved or fully replayable actual saved frontier";

    @Test void theNextInterruptedLifeReachesItsOriginalDriverRead() throws IOException {
        var fixture = new Fixture();
        assertEquals(57, fixture.state.sequence());
        assertEquals(56, fixture.state.settledCycles());
        assertEquals(53179344, fixture.state.settledDateRaw());

        var original = fixture.readOnlyParent();
        assertEquals(56, original.sequence());
        assertEquals(ActionReceipt.Outcome.UNRESOLVED, original.outcome());
        assertEquals(Instant.parse("2026-11-26T11:18:00.125727300Z"), original.command().deadline());
        byte[] command = ActionCodec.encodeCommand(original.command());

        assertSame(fixture.driverRead, assertThrows(IllegalStateException.class, fixture::recover));
        assertEquals(1, fixture.driverReads);
        assertArrayEquals(command, ActionCodec.encodeCommand(fixture.readOnlyParent().command()));
        assertEquals(HEAD_SHA, ActionCodec.sha256(fixture.originalHead));
    }

    @Test void theHistoricalReaderRejectsAnotherBasisOrAnUninterruptedBatch() throws IOException {
        var fixture = new Fixture();
        var differentBasis = fixture.state.toJson();
        ((ObjectNode) differentBasis.get(WriterContracts.ORDINARY_CYCLE_FIELD)).put("basis_cycles", 55);
        fixture.state = ContinuityState.fromJson(differentBasis, fixture.owner.machineId());
        assertEquals(OLD_FRONTIER_FAILURE, assertThrows(ContractViolationException.class, fixture::recover).getMessage());

        var unfinished = fixture.originalState.toJson();
        ((ObjectNode) unfinished.get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD)).put("boundary", "BATCH_STARTED");
        fixture.state = ContinuityState.fromJson(unfinished, fixture.owner.machineId());
        assertEquals(OLD_FRONTIER_FAILURE, assertThrows(ContractViolationException.class, fixture::recover).getMessage());
        assertEquals(0, fixture.driverReads);
    }

    @Test void partialExpiryUsesTheLastObservedCycleInsteadOfThePhysicalSaveDate() throws IOException {
        var fixture = new Fixture();
        var original = fixture.readOnlyParent();
        var whole = fixture.state.toJson();
        var cycle = whole.get(WriterContracts.ORDINARY_CYCLE_FIELD);
        var opening = org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.decodeObservation(
                whole.get(SavedContinuityBootstrap.FIELD).get("opening"));
        assertEquals(53179344, opening.frame().identity().dateRaw().longValueExact());
        assertEquals(53179368, original.command().before().frame().identity().dateRaw().longValueExact());
        fixture.locked(session -> {
            var originals = fixture.archive.withSession(session);
            assertTrue(ContinuityBatchJournal.expiredPartialStartsAtFrontier(
                    fixture.state, whole, cycle, fixture.owner, original.command().before(), originals));
            assertFalse(ContinuityBatchJournal.expiredPartialStartsAtFrontier(
                    fixture.state, whole, cycle, fixture.owner, opening, originals));
            var actions = ContinuityActionJournal.receipts(fixture.state, originals);
            assertTrue(ContinuityBatchJournal.readOnlyPartialLifeTerminalRoot(
                    fixture.state, fixture.owner, actions, originals).isEmpty());
            assertTrue(ContinuityBatchJournal.readOnlyPendingPartialLifeCycle(
                    fixture.state, fixture.owner, actions, originals).isEmpty());
            return null;
        });
    }

    @Test void secondSoftwareSettlementKeepsTheImportedPhysicalFrontier() throws IOException {
        var fixture = new Fixture();
        var genuine = fixtureData("source56-first-imported-settlement.json.gz");
        assertEquals(2, genuine.size());
        var retain = genuine.get(0);
        var settle = genuine.get(1);
        assertEquals("43f4bb73939a748ffb52d3afd580b4a5cd56b96c88b5941e772eaf1a6eb67d04",
                ActionCodec.sha256(ContinuityJson.canonical(retain)));
        assertEquals("9997b9d453b28fc3abccd2a8f6db4e65831df77f748e5f534b1033e6d481e609",
                ActionCodec.sha256(ContinuityJson.canonical(settle)));

        fixture.state = ContinuityState.fromJson(retain.get("after"), fixture.owner.machineId());
        var firstDetails = (ObjectNode) settle.get("details");
        fixture.applyCycle(firstDetails);
        assertArrayEquals(ContinuityJson.canonical(settle.get("after")), fixture.state.canonicalBytes());
        var originalPair = fixture.state.toJson().path(SavedContinuityBootstrap.FIELD).get("checkpoint_pair");
        var firstCycle = fixture.state.toJson().get(WriterContracts.ORDINARY_CYCLE_FIELD);
        assertEquals(57, firstCycle.path("completed_cycles").asLong());

        // The new action, SEM and record below are independent software reducer inputs.
        // This fixture never supplies their native or writer admission and never updates head57.
        String batchId = "source56-software-recovery-1";
        fixture.applyBoundary(batchId, SessionPorts.JournalKind.BATCH_STARTED);
        fixture.applyBoundary(batchId, SessionPorts.JournalKind.BATCH_INTERRUPTED);
        byte[] receiptToken = "isolated software receipt without native authority".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        var receipt = new ExactRef("software-only/second-life-receipt.json", receiptToken.length, ActionCodec.sha256(receiptToken));

        var nextRetain = firstDetails.deepCopy();
        nextRetain.put("operation", "RETAIN").put("evidence_id", "RETAIN:" + receipt.sha256());
        nextRetain.set("receipt_ref", receipt.toJson());
        for (String field : List.of("semantic", "cycle_record_ref", "cycle_record")) nextRetain.putNull(field);
        fixture.applyCycle(nextRetain);

        var nextSettle = firstDetails.deepCopy();
        var semantic = (ObjectNode) nextSettle.get("semantic");
        var frame = (ObjectNode) semantic.path("frame").path("frame");
        frame.put("date_raw", "53179392").put("native_revision", "28").put("revision", "14").put("snapshot_id", "native:28");
        semantic.put("observed_at", Instant.parse(semantic.path("observed_at").asText()).plusSeconds(1).toString());
        var record = (ObjectNode) nextSettle.get("cycle_record");
        record.put("completed_cycles", 58).put("classification", "VISIBLE_GAMEPLAY");
        record.set("previous", firstCycle.get("head"));
        record.set("receipt_ref", receipt.toJson());
        record.set("semantic", semantic);
        byte[] recordBytes = ContinuityJson.canonical(record);
        var recordRef = new ExactRef("software-only/second-cycle-record.json", recordBytes.length, ActionCodec.sha256(recordBytes));
        nextSettle.put("evidence_id", "SETTLE:" + receipt.sha256() + ":" + ExactRef.fromJson(semantic.get("semantic")).sha256());
        nextSettle.set("receipt_ref", receipt.toJson());
        nextSettle.set("cycle_record_ref", recordRef.toJson());
        fixture.applyCycle(nextSettle);
        assertEquals(45, fixture.state.sequence());
        assertSecondUnsavedFrontier(fixture, originalPair, recordRef);

        fixture.state = fixture.originalState;
        assertEquals(ActionReceipt.Outcome.UNRESOLVED, fixture.readOnlyParent().outcome());
        fixture.locked(same -> {
            var resume = ContinuityActionJournal.receipts(fixture.originalState, fixture.archive.withSession(same)).stream()
                    .filter(action -> action.sequence() == 55).findFirst().orElseThrow();
            assertInstanceOf(ActionState.Unknown.class, resume.state());
            assertTrue(resume.ack().orElseThrow().nativeOk());
            return null;
        });
        assertEquals(HEAD_SHA, ActionCodec.sha256(fixture.originalHead));
    }

    private static void assertSecondUnsavedFrontier(Fixture fixture, JsonNode originalPair, ExactRef recordRef) {
        var whole = fixture.state.toJson();
        var cycle = whole.get(WriterContracts.ORDINARY_CYCLE_FIELD);
        assertEquals(58, cycle.path("completed_cycles").asLong());
        assertEquals(56, cycle.path("basis_cycles").asLong());
        assertEquals(recordRef, ExactRef.fromJson(cycle.get("head")));
        assertTrue(cycle.path("pending_receipt").isNull());
        assertEquals(originalPair, whole.path(SavedContinuityBootstrap.FIELD).get("checkpoint_pair"));
        assertEquals(56, fixture.state.settledCycles());
        assertEquals(53179344, fixture.state.settledDateRaw());
        assertFalse(whole.hasNonNull(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD));
        assertEquals(ContinuityState.Status.RUNNING, fixture.state.status());
        assertEquals(SessionPorts.JournalKind.BATCH_INTERRUPTED.name(),
                whole.path(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD).path("boundary").asText());

        // A cold reader gets past the imported physical frontier but still requires the original Driver.
        assertSame(fixture.driverRead, assertThrows(IllegalStateException.class, fixture::recoverSettled));
        assertEquals(1, fixture.driverReads);
    }

    private static final class Fixture implements ContinuityStorePort {
        private final byte[] originalHead;
        private final ContinuityState originalState;
        private final SessionIdentity owner;
        private final JsonNode artifacts;
        private final ExactRef initialDriverFacts;
        private final OutcomeArchive archive;
        private final ContinuityBatchJournal journal;
        private final OrdinaryCycleTransitions transitions;
        private final IllegalStateException driverRead = new IllegalStateException("fixture reached the original saved Driver read");
        private boolean held;
        private int driverReads;
        private ContinuityState state;

        private final Session same = (Session) Proxy.newProxyInstance(getClass().getClassLoader(), new Class<?>[]{Session.class},
                (proxy, method, args) -> {
                    requireSession((Session) proxy);
                    if (method.getName().equals("head"))
                        return new WriterContracts.Head(state, List.of(), List.of(), List.of(), false);
                    throw new AssertionError("test archive prefix cannot perform " + method.getName());
                });

        private Fixture() throws IOException {
            var data = fixtureData();
            originalHead = binary(data.get("head"));
            assertEquals(HEAD_SHA, ActionCodec.sha256(originalHead));
            var row = ContinuityJson.parseObject(originalHead, 1 << 20);
            originalState = ContinuityState.fromJson(row, row.get("machine_id").textValue());
            state = originalState;
            var marker = SavedContinuityBootstrap.request((ObjectNode) row.get(SavedContinuityBootstrap.FIELD)).detailsObject();
            owner = OrdinaryCycleTransitions.sessionFromJson(marker.get("session"));
            initialDriverFacts = ExactRef.fromJson(marker.get("driver_facts"));
            artifacts = data.get("artifacts");
            // Immutable locators inside the originals are archive metadata. The software test resolves only bundled bytes.
            archive = new PortableRecoveryDataArchive(this::requireSession, (reference, maximumBytes) -> {
                assertTrue(held);
                if (reference.equals(initialDriverFacts)) {
                    driverReads++;
                    throw driverRead;
                }
                var material = artifacts.get(reference.sha256());
                assertNotNull(material, "fixture archive is missing " + reference.sha256());
                return binary(material);
            }).proxy();
            transitions = new OrdinaryCycleTransitions(archive, (session, identity, semantic) -> { throw unavailable(); },
                    (session, identity, pair, settlement) -> { throw unavailable(); },
                    new OriginalWindowReducer.Policy(originalState.origin().targetDays()), this::requireSession);
            journal = new ContinuityBatchJournal(this, transitions);
        }

        private ActionReceipt readOnlyParent() throws IOException {
            return locked(session -> ContinuityBatchJournal.readOnlyLifeRecoveryRoot(
                    ContinuityActionJournal.receipts(state, archive.withSession(session))).orElseThrow());
        }

        private ContinuityBatchJournal.UnresolvedSameGameData recover() throws IOException {
            return locked(session -> journal.readUnresolvedSameGame(session, owner));
        }

        private ContinuityBatchJournal.SettledSameGameData recoverSettled() throws IOException {
            return locked(session -> journal.readSettledSameGame(session, owner));
        }

        private void applyCycle(ObjectNode details) {
            apply(new WriterContracts.Request(OrdinaryCycleTransitions.CYCLE_KIND, ContinuityJson.canonical(details), List.of()));
        }

        private void applyBoundary(String batch, SessionPorts.JournalKind kind) {
            apply(transitions.batchRequest(new SessionPorts.JournalInput(owner, batch, kind,
                    Optional.empty(), Optional.empty(), Optional.empty(), List.of())));
        }

        private void apply(WriterContracts.Request request) {
            var next = transitions.reduce(state, request).toJson();
            next.put("sequence", state.sequence() + 1);
            next.put("last_event_identity", request.identity());
            state = ContinuityState.fromJson(next, owner.machineId());
        }

        @Override public void requireSession(Session session) { assertTrue(held); assertSame(same, session); }
        @Override public <T> T locked(SessionWork<T> work) throws IOException {
            assertFalse(held);
            held = true;
            try { return work.run(same); }
            finally { held = false; }
        }
        @Override public WriterContracts.Prepared preview(WriterContracts.Request ignored) { throw unavailable(); }
        @Override public WriterContracts.Receipt commit(WriterContracts.Prepared ignored) { throw unavailable(); }
        @Override public ExactRef persistedHead() { throw unavailable(); }

        private static AssertionError unavailable() { return new AssertionError("fixture has no writer, SAVE or Native authority"); }
    }

    private static byte[] binary(JsonNode value) { return Base64.getDecoder().decode(value.textValue()); }

    private static JsonNode fixtureData() throws IOException {
        return fixtureData("source56-interrupted-recovery-prefix.json.gz");
    }

    private static JsonNode fixtureData(String resource) throws IOException {
        try (var original = ImportedSavedInterruptedLifeRecoveryDataTest.class.getResourceAsStream(resource)) {
            assertNotNull(original);
            try (var input = new GZIPInputStream(original)) {
                byte[] bytes = input.readNBytes(1 << 20);
                assertTrue(bytes.length < 1 << 20);
                return FullJsonTree.parse(bytes, 1 << 20);
            }
        }
    }
}
