package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.ActionRow;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.CanonicalOnly;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.LegacyHistoryRow;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Stamp;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * NONBLIND public DATA witness; no main/reflection/native/writer.
 * Literal Driver and coverage rows are manually constructed public DATA, not an
 * actual canonical action, archive file, source qualification or observation replay.
 * Only observation:null uses Optional.empty(); the non-null case below must reject.
 * Expected rows/failures are literal; no Set construction or membership algorithm
 * from decodeKnownOriginal is reimplemented here.
 */
final class DriverSnapshotFactsPublicDataWitnessTest {
    private static final String SHA = "0".repeat(64);
    private static final String REF = "{\"path\":\"software-reference\",\"bytes\":1,\"sha256\":\"" + SHA + "\"}";
    private static final String TWO_HISTORY_ROWS = """
            [{"index":1,"command":"software-one","ok":true},
             {"index":2,"command":"software-two","ok":false}]
            """;

    @Test void emptyHistoryAndCoverageDecodeAsCompletePublicData() {
        Known actual = decode(wire("[]", "[]", "null"));
        assertEquals(List.of(), actual.driver().commandHistory());
        assertEquals(List.of(), actual.actionRows());
        assertEquals(7, actual.stamp().driverVersion());
        assertEquals(2, actual.stamp().episodeEpoch());
        assertEquals("software-episode", actual.stamp().episodeRunId());
        assertTrue(actual.loop().isEmpty());
        assertTrue(actual.observation().isEmpty());
        assertEquals("{\"opaque\":-0.00e+2}",
                new String(DriverJson.encode(actual.auxiliary()), StandardCharsets.UTF_8));
    }

    @Test void repeatedMixedLegacyAndCanonicalCoverageKeepsLiteralOrderAndRoles() {
        String rows = """
                [{"action_id":"legacy-one","body_sha256":"%s","durable_sequence":1,
                  "coverage_source":{"kind":"legacy-history-row","history_index":1,"original_row":%s}},
                 {"action_id":"canonical-two","body_sha256":"%s","durable_sequence":2,
                  "coverage_source":{"kind":"canonical-only","original_source":%s}},
                 {"action_id":"legacy-three","body_sha256":"%s","durable_sequence":3,
                  "coverage_source":{"kind":"legacy-history-row","history_index":2,"original_row":%s}},
                 {"action_id":"canonical-four","body_sha256":"%s","durable_sequence":4,
                  "coverage_source":{"kind":"canonical-only","original_source":%s}}]
                """.formatted(SHA, REF, SHA, REF, SHA, REF, SHA, REF);
        Known actual = decode(wire(TWO_HISTORY_ROWS, rows, "null"));
        ExactRef ref = new ExactRef("software-reference", 1, SHA);
        assertEquals(List.of(
                new ActionRow("legacy-one", SHA, 1, new LegacyHistoryRow(1, ref)),
                new ActionRow("canonical-two", SHA, 2, new CanonicalOnly(ref)),
                new ActionRow("legacy-three", SHA, 3, new LegacyHistoryRow(2, ref)),
                new ActionRow("canonical-four", SHA, 4, new CanonicalOnly(ref))), actual.actionRows());
        assertEquals(2, actual.driver().commandHistory().size());
    }

    @Test void unknownFieldsAndCoverageKindKeepTheOriginalFirstFailure() {
        String root = wire("[]", "[]", "null").replace(
                "\"schema\":\"xar.java-driver-known-original/v1\"", "\"schema\":\"wrong\",\"unexpected\":0");
        var rootFailure = assertThrows(ContractViolationException.class, () -> decode(root));
        assertEquals("exact Known original fields required", rootFailure.getMessage());

        String extraAction = "[{\"action_id\":\"bad\",\"body_sha256\":\"" + SHA
                + "\",\"durable_sequence\":1,\"coverage_source\":{\"kind\":\"unknown\"},\"unexpected\":0}]";
        var actionFailure = assertThrows(ContractViolationException.class, () -> decode(wire("[]", extraAction, "null")));
        assertEquals("exact Known original fields required", actionFailure.getMessage());

        String extraLegacy = "[{\"action_id\":\"bad\",\"body_sha256\":\"" + SHA
                + "\",\"durable_sequence\":1,\"coverage_source\":{\"kind\":\"legacy-history-row\","
                + "\"history_index\":0,\"original_row\":" + REF + ",\"unexpected\":0}}]";
        var branchFailure = assertThrows(ContractViolationException.class, () -> decode(wire("[]", extraLegacy, "null")));
        assertEquals("exact Known original fields required", branchFailure.getMessage());

        String unknownKind = "[{\"action_id\":\"bad\",\"body_sha256\":\"" + SHA
                + "\",\"durable_sequence\":1,\"coverage_source\":{\"kind\":\"unknown\",\"unexpected\":0}}]";
        var kindFailure = assertThrows(IllegalArgumentException.class, () -> decode(wire("[]", unknownKind, "null")));
        assertEquals("unknown complete Known action coverage source", kindFailure.getMessage());
    }

    @Test void aNonNullObservationStillRequiresActualManifestReplay() {
        var failure = assertThrows(IllegalArgumentException.class, () -> decode(wire("[]", "[]", REF)));
        assertEquals("actual original observation-manifest replay is required", failure.getMessage());
    }

    @Test void publicForeignNumericDataStillReachesTheFirstDriverEncode() {
        var probe = new EncodingProbe();
        var session = new DriverStateSnapshot.Session("software-pipe", 1, probe, "software-episode");
        var nil = new DriverStateSnapshot.NullValue();
        var driver = new DriverStateSnapshot.Complete(session, List.of(), nil, nil, nil, nil, nil, nil, nil);
        var stamp = new Stamp(7, 2, new GameGeneration(1, new PythonOnlyUInt64(BigInteger.ONE)), "software-episode", SHA);
        probe.armed = true;
        // The deliberately wrong stamp cannot hide or replace the real first driver.encode().
        RuntimeException failure = assertThrows(RuntimeException.class,
                () -> new Known(driver, stamp, new ExactRef("software-reference", 1, SHA), List.of(),
                        new OpportunityJson.Obj(Map.of()), Optional.empty(), Optional.empty()));
        Throwable cause = failure;
        while (cause != null && cause != probe.failure) cause = cause.getCause();
        assertSame(probe.failure, cause);
    }

    private static Known decode(String literal) {
        return DriverSnapshotFacts.decodeKnownOriginal(RawJson.fullMaterial(literal.getBytes(StandardCharsets.UTF_8)), Optional.empty());
    }

    private static String wire(String history, String actionRows, String observation) {
        String driver = """
                {"format_version":2,"pipe_name":"software-pipe","bridge_pid":1,"episode_character_id":1,
                 "episode_run_id":"software-episode","command_history":%s,"last_checkpoint":null,
                 "rollback_war_failure":null,"managed_restore_transaction":null,"succession_expectation":null,
                 "succession_lifecycle":null,"campaign_goal":null,"rollback_war_failures":null}
                """.formatted(history);
        // This binding is fixture input computed by the real public Driver encoder, not a Known decoder oracle.
        String driverSha = DriverJson.sha256(DriverStateSnapshot.decodeComplete(driver.getBytes(StandardCharsets.UTF_8)).encode());
        return """
                {"schema":"xar.java-driver-known-original/v1","driver":%s,
                 "stamp":{"driver_version":7,"episode_epoch":2,"game":{"pid":1,"creation_filetime":"1"},
                          "episode_run_id":"software-episode","driver_sha256":"%s"},
                 "original_history_basis":%s,"action_rows":%s,"auxiliary":{"opaque":-0.00e+2},
                 "loop":null,"observation":%s}
                """.formatted(driver, driverSha, REF, actionRows, observation);
    }

    private static final class EncodingProbe extends BigInteger {
        private static final long serialVersionUID = 1L;
        private final RuntimeException failure = new IllegalStateException("software-foreign-first-encode");
        private boolean armed;
        private EncodingProbe() { super("1"); }
        @Override public String toString() { if (armed) throw failure; return super.toString(); }
        @Override public String toString(int radix) { if (armed) throw failure; return super.toString(radix); }
    }
}
