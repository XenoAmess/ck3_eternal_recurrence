package org.xar.ck3.control.continuity.writer;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Source-derived pure DATA checks: no file/Native/clock/dispatch or private admission. */
class WriterPureValues231Test {
    private static final String MACHINE = "writer-pure-values-fixture";
    private static final String A = "a".repeat(64), B = "b".repeat(64);

    @Test void canonicalHeadComparisonRetainsFiniteBinary64SignedZeroAndUnicode() {
        for (double number : new double[] { -0.0, 0.0, 1.0, -1.0, 365.25, 0.1,
                Double.MIN_VALUE, Double.MIN_NORMAL, Double.MAX_VALUE, Math.nextDown(1.0),
                Math.nextUp(1.0), 1e-5, 1e16, -1e308 }) {
            ObjectNode row = base();
            row.putObject("unknown_current").put("\uE000", "零\n\"\\😀").put("😀", number).putNull("missing_is_not_null");
            ContinuityState first = state(row);
            ObjectNode reordered = base();
            reordered.putObject("unknown_current").putNull("missing_is_not_null").put("😀", number).put("\uE000", "零\n\"\\😀");
            ContinuityState second = state(reordered);
            assertArrayEquals(first.canonicalBytes(), ContinuityJson.canonical(first.toJson()));
            assertArrayEquals(first.canonicalBytes(), second.canonicalBytes());
            assertTrue(ContinuityJson.same(first.toJson(), second.toJson()));
            ContinuityWriter.requireSameHead(head(first), head(second));
        }
    }

    @Test void completeUnknownStateChangesRemainDriftEvenWhenTypedCoordinatesMatch() {
        ObjectNode original = base(); original.putObject("unknown").put("number", -0.0).put("text", "unchanged");
        ContinuityState before = state(original);
        List<ObjectNode> changes = new ArrayList<>();
        ObjectNode zero = original.deepCopy(); ((ObjectNode) zero.get("unknown")).put("number", 0.0); changes.add(zero);
        ObjectNode unknown = original.deepCopy(); ((ObjectNode) unknown.get("unknown")).put("text", "changed"); changes.add(unknown);
        ObjectNode nullValue = original.deepCopy(); nullValue.putNull("previously_missing"); changes.add(nullValue);
        ObjectNode integer = original.deepCopy(); ((ObjectNode) integer.get("unknown")).put("number", 0); changes.add(integer);
        for (ObjectNode changed : changes) {
            ContinuityState after = state(changed);
            assertEquals(before.sequence(), after.sequence()); assertEquals(before.machineId(), after.machineId());
            assertFalse(ContinuityJson.same(before.toJson(), after.toJson()));
            assertThrows(ContractViolationException.class, () -> ContinuityWriter.requireSameHead(head(before), head(after)));
        }
    }

    @Test void everyHeadMetadataDimensionAndListOrderStillRejectsDrift() {
        Head before = head(state(base())); Pin first = before.documents().get(0), second = before.documents().get(1);
        List<Head> changes = new ArrayList<>();
        changes.add(new Head(before.state(), List.of(second, first), before.absent(), before.indexRepairs(), false));
        changes.add(new Head(before.state(), List.of(new Pin(new ExactRef("C:/writer-pure231/other.json", 1, A), first.identity()), second), before.absent(), before.indexRepairs(), false));
        changes.add(new Head(before.state(), List.of(new Pin(new ExactRef(first.reference().path(), 1, B), first.identity()), second), before.absent(), before.indexRepairs(), false));
        changes.add(new Head(before.state(), List.of(new Pin(first.reference(), new FileIdentity("1", "7", "3", "2026-01-01T00:00:00Z", 1)), second), before.absent(), before.indexRepairs(), false));
        changes.add(new Head(before.state(), before.documents(), List.of(before.absent().get(1), before.absent().get(0)), before.indexRepairs(), false));
        changes.add(new Head(before.state(), before.documents(), List.of(Path.of("C:/writer-pure231/different")), before.indexRepairs(), false));
        changes.add(new Head(before.state(), before.documents(), before.absent(), List.of(before.indexRepairs().get(1), before.indexRepairs().get(0)), false));
        changes.add(new Head(before.state(), before.documents(), before.absent(), List.of(new IndexRepair(Path.of("C:/writer-pure231/repair"), 3, B)), false));
        changes.add(new Head(before.state(), before.documents(), before.absent(), before.indexRepairs(), true));
        for (Head changed : changes) assertThrows(ContractViolationException.class, () -> ContinuityWriter.requireSameHead(before, changed));
        ContinuityWriter.requireSameHead(before, new Head(before.state(), before.documents(), before.absent(), before.indexRepairs(), false));
    }

    @Test void stateAndRequestNeverExposeTheirOwnedCanonicalArrays() {
        ContinuityState valid = state(base()); byte[] raw = valid.canonicalBytes();
        ContinuityState constructed = new ContinuityState(valid.machineId(), valid.sequence(), valid.origin(), valid.status(),
                valid.settledCycles(), valid.settledDateRaw(), raw);
        byte[] expected = constructed.canonicalBytes(); raw[0] = '!';
        byte[] exported = constructed.canonicalBytes(); exported[0] = '!';
        constructed.toJson().put("outside_mutation", true);
        assertArrayEquals(expected, constructed.canonicalBytes());
        ContinuityWriter.requireSameHead(head(valid), head(constructed));
        ObjectNode details = StrictJson.object().put("evidence_id", "pure-request").put("source", "source-data");
        byte[] input = ContinuityJson.canonical(details);
        List<ExactRef> evidence = new ArrayList<>(); evidence.add(new ExactRef("C:/writer-pure231/evidence", 1, A));
        Request request = new Request("pure-event", input, evidence);
        String identity = request.identity(), sourceKey = request.sourceKey();
        input[0] = '!'; request.details()[0] = '!'; request.detailsObject().put("evidence_id", "external"); evidence.clear();
        assertEquals(identity, request.identity()); assertEquals(sourceKey, request.sourceKey()); assertEquals(1, request.evidence().size());
    }

    @Test void aggregateLedgerStateAboveDocumentBudgetKeepsItsFullUnknownPayload() {
        ObjectNode row = base(); String payload = "😀retained:" + "x".repeat(100000);
        row.putObject("unknown_aggregate").put("payload", payload).put("binary64", -0.0);
        ContinuityState before = state(row);
        assertTrue(before.canonicalBytes().length > ContinuityJson.DOCUMENT_MAX_BYTES);
        assertTrue(before.canonicalBytes().length < ContinuityJson.LEDGER_MAX_BYTES);
        ContinuityState after = state(ContinuityJson.parseObject(before.canonicalBytes(), ContinuityJson.LEDGER_MAX_BYTES));
        assertEquals(payload, after.toJson().path("unknown_aggregate").path("payload").textValue());
        assertTrue(ContinuityJson.same(before.toJson(), after.toJson()));
        ContinuityWriter.requireSameHead(head(before), head(after));
    }

    @Test void validNoncanonicalBytesNormalizeWhileMalformedStateIsRejectedAtConstruction() {
        ContinuityState valid = state(base());
        byte[] noncanonical = (" \n" + base().toString() + "\n ").getBytes(StandardCharsets.UTF_8);
        ContinuityState normalized = new ContinuityState(valid.machineId(), valid.sequence(), valid.origin(), valid.status(),
                valid.settledCycles(), valid.settledDateRaw(), noncanonical);
        assertArrayEquals(valid.canonicalBytes(), normalized.canonicalBytes());
        ContinuityWriter.requireSameHead(head(valid), head(normalized));
        ObjectNode wrongMachine = base().put("machine_id", "other");
        assertThrows(ContractViolationException.class, () -> state(wrongMachine));
        ObjectNode nonfinite = base().put("unknown", Double.NaN);
        assertThrows(ContractViolationException.class, () -> state(nonfinite));
        ObjectNode missing = base(); missing.remove("status");
        assertThrows(ContractViolationException.class, () -> state(missing));
    }

    private static ContinuityState state(ObjectNode row) { return ContinuityState.fromJson(row, MACHINE); }
    private static Head head(ContinuityState state) {
        Pin one = new Pin(new ExactRef("C:/writer-pure231/one", 1, A), new FileIdentity("1", "2", "3", "2026-01-01T00:00:00Z", 1));
        Pin two = new Pin(new ExactRef("C:/writer-pure231/two", 1, B), new FileIdentity("1", "4", "5", "2026-01-01T00:00:00Z", 1));
        return new Head(state, List.of(one, two), List.of(Path.of("C:/writer-pure231/absent1"), Path.of("C:/writer-pure231/absent2")),
                List.of(new IndexRepair(Path.of("C:/writer-pure231/repair1"), 1, A), new IndexRepair(Path.of("C:/writer-pure231/repair2"), 2, B)), false);
    }
    private static ObjectNode base() {
        ObjectNode row = StrictJson.object().put("schema", "root.ck3.continuity-window/v1").put("machine_id", MACHINE)
                .put("sequence", 0).put("window_id", 1).put("status", "running").put("target_days", 10_958)
                .put("target_years", 30).put("calendar_year_days", 365.25).put("start_date_raw", 1000)
                .put("target_date_raw", 1000 + 10_958 * 24).put("last_settled_date_raw", 1000).put("last_settled_cycles", 1)
                .put("manual_repair_count", 1).put("automatic_recovery_count", 0).put("binding_lineage_count", 0);
        row.putObject("game_binding").put("pid", 123).put("creation_date", "2026-01-01T00:00:00Z");
        row.putNull("latest_binding"); row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11_558);
        row.put("NEXT", 11_559); return row;
    }
}
