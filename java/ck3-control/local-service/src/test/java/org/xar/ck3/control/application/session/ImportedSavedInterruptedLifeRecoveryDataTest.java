package org.xar.ck3.control.application.session;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.time.Instant;
import java.util.Base64;
import java.util.List;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.ActionReceipt;
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

    private static final class Fixture implements ContinuityStorePort {
        private final byte[] originalHead;
        private final ContinuityState originalState;
        private final SessionIdentity owner;
        private final JsonNode artifacts;
        private final ExactRef initialDriverFacts;
        private final OutcomeArchive archive;
        private final ContinuityBatchJournal journal;
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
            var transitions = new OrdinaryCycleTransitions(archive, (session, identity, semantic) -> { throw unavailable(); },
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
        try (var original = ImportedSavedInterruptedLifeRecoveryDataTest.class.getResourceAsStream("source56-interrupted-recovery-prefix.json.gz")) {
            assertNotNull(original);
            try (var input = new GZIPInputStream(original)) {
                byte[] bytes = input.readNBytes(1 << 20);
                assertTrue(bytes.length < 1 << 20);
                return FullJsonTree.parse(bytes, 1 << 20);
            }
        }
    }
}
