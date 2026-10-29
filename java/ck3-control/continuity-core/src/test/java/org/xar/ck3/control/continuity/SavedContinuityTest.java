package org.xar.ck3.control.continuity;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

class SavedContinuityTest {
    private static ObjectNode fixture(String name) throws IOException {
        try (InputStream input = SavedContinuityTest.class.getResourceAsStream("/" + name)) {
            assertNotNull(input, name); return ContinuityJson.parseObject(input.readAllBytes(), 65_536);
        }
    }
    private static ObjectNode request() throws IOException {
        ObjectNode old = fixture("n46-head240.actual.json"), basis = fixture("n46-prior-basis.actual.json");
        ObjectNode progress = ContinuityJson.object(basis.get("progress")).deepCopy();
        progress.put("ledger_cycles", old.get("last_settled_cycles").longValue());
        progress.put("ledger_date_raw", old.get("last_settled_date_raw").longValue());
        ObjectNode details = ContinuityJson.object(old.get("last_current_saved_cold")).deepCopy();
        ObjectNode row = StrictJson.object(); row.put("schema", SavedContinuityAttachment.REQUEST_SCHEMA);
        row.set("previous", old); row.set("expected_predecessor", old.deepCopy());
        row.set("details", details); row.set("expected_details", details.deepCopy()); row.set("basis", basis);
        row.set("progress", progress); row.set("game", old.get("game_binding").deepCopy());
        row.set("opening", basis.get("frame").deepCopy()); return row;
    }
    private static byte[] wire(ObjectNode row) { return ContinuityJson.canonical(row, 262_144); }
    @Test void retainedSmallActualHeadProjectsWithoutWritingSequenceOrOrigin() throws IOException {
        ObjectNode input = request(), before = input.deepCopy();
        ObjectNode after = ContinuityJson.parseObject(SavedContinuityAttachment.reduce(wire(input)), 65_536);
        assertTrue(ContinuityJson.same(input, before));
        assertEquals(240, after.get("sequence").longValue());
        assertEquals(input.get("previous").get("window_id"), after.get("window_id"));
        assertEquals(input.get("previous").get("start_date_raw"), after.get("start_date_raw"));
        assertEquals(input.get("previous").get("last_event_identity"), after.get("last_event_identity"));
        assertEquals(input.get("basis").get("completed_cycles"), after.get("last_settled_cycles"));
        assertEquals(-7, after.get("current_saved_reconciliation").get("already_settled_alignment_cycles").longValue());
        assertEquals(0, after.get("current_saved_reconciliation").get("ordinary_cycle_credit").intValue());
        assertEquals(input.get("previous").get("unsaved_tail_recovery"), after.get("unsaved_tail_recovery"));
        assertEquals(input.get("previous").get("interruption"), after.get("previous_interruption"));
    }
    @Test void pendingMissingNullAndPresentRemainDifferentAcrossReduction() throws IOException {
        for (int mode = 0; mode < 3; mode++) {
            ObjectNode input = request(), old = ContinuityJson.object(input.get("previous"));
            if (mode == 1) { old.putNull("pending_cycle"); }
            if (mode == 2) { old.set("pending_cycle", fixture("n46-raw-state.actual.json").get("pending_cycle")); }
            input.set("expected_predecessor", old.deepCopy());
            ContinuityState after = SavedContinuityAttachment.reduce(SavedContinuityAttachment.decode(wire(input)));
            if (mode == 0) { assertInstanceOf(ContinuityState.Missing.class, after.pendingCycle()); }
            if (mode == 1) { assertInstanceOf(ContinuityState.NullValue.class, after.pendingCycle()); }
            if (mode == 2) {
                assertInstanceOf(ContinuityState.Present.class, after.pendingCycle());
                assertEquals(old.get("pending_cycle"), after.toJson().get("pending_cycle"));
            }
        }
    }
    @Test void unknownAndUnsettledAutoHaveOneZeroCreditNoReplayWire() throws IOException {
        ObjectNode basis = fixture("n46-prior-basis.actual.json");
        for (var row : basis.get("unknown_requests")) {
            assertTrue(ContinuityJson.same(row, RetainedRequestState.Unknown.fromJson(row).toJson()));
            ObjectNode replayed = ContinuityJson.object(row).deepCopy(); replayed.put("replayed", true);
            assertThrows(ContractViolationException.class, () -> RetainedRequestState.Unknown.fromJson(replayed));
            ObjectNode credit = ContinuityJson.object(row).deepCopy(); credit.put("cycle_credit", false);
            assertThrows(ContractViolationException.class, () -> RetainedRequestState.Unknown.fromJson(credit));
        }
        var pending = fixture("n46-raw-state.actual.json").get("pending_cycle");
        var typed = RetainedRequestState.UnsettledAuto.fromJson(pending);
        assertEquals(5190, typed.globalTurn()); assertEquals(11558, typed.autoSequence());
        assertTrue(ContinuityJson.same(pending, typed.toJson()));
    }
    @Test void rejectsFrozenInputDriftBadCoordinateTypesReplayAndUnknownEnvelopeFields() throws IOException {
        for (String change : new String[]{"drift", "float", "bool", "replay", "credit", "extra", "missing", "null"}) {
            ObjectNode row = request();
            switch (change) {
                case "drift" -> ContinuityJson.object(row.get("expected_predecessor")).put("sequence", 241);
                case "float" -> ContinuityJson.object(row.get("progress")).put("ledger_cycles", 5189.0);
                case "bool" -> ContinuityJson.object(row.get("progress")).put("ledger_cycles", true);
                case "replay" -> {
                    ContinuityJson.object(row.get("details")).put("original_actions_replayed", true);
                    row.set("expected_details", row.get("details").deepCopy());
                }
                case "credit" -> {
                    ContinuityJson.object(row.get("details")).put("game_day_credit", 1);
                    row.set("expected_details", row.get("details").deepCopy());
                }
                case "extra" -> row.put("allow_replay", false);
                case "missing" -> row.remove("opening");
                case "null" -> row.putNull("opening");
                default -> throw new AssertionError(change);
            }
            assertThrows(ContractViolationException.class, () -> SavedContinuityAttachment.reduce(wire(row)), change);
        }
    }
    @Test void legacyFloatAndUnicodeCanonicalBytesKeepPythonAbi() {
        String input = "{\"z\":365.25,\"small\":5e-324,\"zero\":-0.0,\"large\":1e23,\"plain\":1e7,\"tiny\":1e-5,\"😀\":[],\"\":null}";
        String expected = "{\"large\":1e+23,\"plain\":10000000.0,\"small\":5e-324,\"tiny\":1e-05,\"z\":365.25,\"zero\":-0.0,\"\":null,\"😀\":[]}";
        assertEquals(expected, new String(ContinuityJson.canonical(ContinuityJson.parseObject(input.getBytes(StandardCharsets.UTF_8), 65_536)), StandardCharsets.UTF_8));
        assertThrows(ContractViolationException.class, () -> ContinuityJson.parseObject("{\"a\":1,\"a\":2}".getBytes(StandardCharsets.UTF_8), 65_536));
    }
    @Test void eventEnvelopeRoundTripRejectsDigestAndOriginChanges() throws IOException {
        ObjectNode input = request();
        var old = ContinuityState.fromJson(input.get("previous"), input.get("previous").get("machine_id").textValue());
        ObjectNode after = ContinuityJson.parseObject(SavedContinuityAttachment.reduce(wire(input)), 65_536);
        ObjectNode identityValue = StrictJson.object(); identityValue.put("kind", "saved-binding"); identityValue.set("details", input.get("details"));
        String identity = ContinuityJson.digest(identityValue);
        after.put("sequence", old.sequence() + 1); after.put("last_event_identity", identity);
        ObjectNode event = StrictJson.object(); event.put("sequence", old.sequence() + 1); event.put("at_utc", "2026-10-23T00:00:00Z");
        event.put("kind", "saved-binding"); event.set("details", input.get("details")); event.put("identity", identity);
        event.put("previous_sha256", ContinuityJson.digest(old.toJson())); event.set("after", after);
        assertTrue(ContinuityJson.same(event, ContinuityEvent.fromJson(event, old).toJson()));
        var recovered = ContinuityHistory.preview(old, old, java.util.List.of(ContinuityJson.canonical(event)));
        assertEquals(old.sequence() + 1, recovered.head().sequence());
        assertTrue(recovered.snapshotNeedsRecovery()); assertEquals(0, recovered.ledgerWrites());
        assertEquals(after.get("unsaved_tail_recovery"), recovered.head().toJson().get("unsaved_tail_recovery"));
        var current = ContinuityHistory.preview(old, ContinuityState.fromJson(after, old.machineId()),
                java.util.List.of(ContinuityJson.canonical(event)));
        assertFalse(current.snapshotNeedsRecovery());
        event.put("previous_sha256", "0".repeat(64));
        assertThrows(ContractViolationException.class, () -> ContinuityEvent.fromJson(event, old));
    }
}
