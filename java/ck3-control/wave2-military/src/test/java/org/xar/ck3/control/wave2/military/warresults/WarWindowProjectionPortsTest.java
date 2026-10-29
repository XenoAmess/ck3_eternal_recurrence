package org.xar.ck3.control.wave2.military.warresults;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertTrue;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionDispatcher;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.ProjectionWire;
import org.xar.ck3.control.wave2.military.warexitterms.WarExitTerms;

final class WarWindowProjectionPortsTest {
    private final ProjectionDispatcher dispatcher = ProjectionDispatcher.fromCatalogs(List.of(() -> WarWindowProjectionPorts.registrations(new WarWindowProjectionPorts.Operations(ProjectionOperation.MILITARY_WAR_RESULTS_PLAN, ProjectionOperation.MILITARY_WAR_OVERVIEW_PLAN, ProjectionOperation.MILITARY_WAR_RESULTS_PRESENCE, ProjectionOperation.MILITARY_WAR_OVERVIEW_PRESENCE, ProjectionOperation.MILITARY_WAR_RESULTS_QUERY_FRAME, ProjectionOperation.MILITARY_WAR_OVERVIEW_QUERY_FRAME, ProjectionOperation.MILITARY_WAR_RESULTS_NORMALIZE, ProjectionOperation.MILITARY_WAR_RESULTS_SOURCE_OWNER, ProjectionOperation.MILITARY_DEJURE_BASELINE_NORMALIZE, ProjectionOperation.MILITARY_WAR_EXIT_TERMS_NORMALIZE))));
    private ProjectionResult call(ProjectionOperation operation, String raw) {
        return dispatcher.dispatch(ProjectionWire.encodeCall(new ProjectionCall(new ProjectionCall.Identity("catalog-negative", operation),
                ProjectionJson.object(raw.getBytes(StandardCharsets.UTF_8), 1_048_576))));
    }
    private String window(String schema, String prefix, String extra) {
        return "{\"schema\":\"" + schema + "\",\"snapshot\":{\"snapshot_id\":\"native:1\",\"revision\":1,\"native_revision\":1,\"date_raw\":24,"
                + "\"episode_run_id\":\"offline\",\"played_character\":{\"character_id\":1},\"diagnostics\":{\"connection_generation\":1},"
                + "\"paused\":true,\"map_ready\":true" + extra + "},\"action_steps\":[\"query-" + prefix + "-v1\",\"close-" + prefix
                + "-v1\"],\"bridge_capabilities\":[\"game.command.query-" + prefix + "-v1\",\"game.command.close-" + prefix + "-v1\"]}";
    }
    @Test void actualPortsKeepUnknownPendingUnreplayedAndAckWithoutPostUnknown() {
        for (boolean overview : List.of(false, true)) {
            String prefix = overview ? "war-declared-overview" : "war-results-window";
            String publicPrefix = prefix.replace('-', '_');
            String schema = overview ? "xar.ck3.war-declared-overview-priority-input/v1" : WarResultsCodec.SCHEMA;
            var operation = overview ? ProjectionOperation.MILITARY_WAR_OVERVIEW_PLAN : ProjectionOperation.MILITARY_WAR_RESULTS_PLAN;
            String raw = window(schema, prefix, ",\"" + publicPrefix + "_v1_close_pending\":{\"native_request_id\":\"UNKNOWN-original\",\"status\":\"unknown\"}");
            var success = assertInstanceOf(ProjectionResult.Succeeded.class, call(operation, raw));
            var result = StrictJson.parse(success.result().bytes());
            assertFalse(result.get(publicPrefix).get("close_action_credit").booleanValue());
            assertFalse(result.get("selected_step").asText().startsWith("close-"));
            String ack = window(schema, prefix, ",\"" + publicPrefix + "_v1_observation\":{\"available\":true,\"accepted\":true,\"dispatch_attempted\":true,\"dispatch_invoked\":true}");
            var presence = assertInstanceOf(ProjectionResult.Succeeded.class, call(overview
                    ? ProjectionOperation.MILITARY_WAR_OVERVIEW_PRESENCE : ProjectionOperation.MILITARY_WAR_RESULTS_PRESENCE, ack));
            assertEquals("unknown", StrictJson.parse(presence.result().bytes()).textValue());
        }
    }
    @Test void originalFloatingTokensReachActualDomainBoundaryAndCrossSchemaRejects() {
        String valid = window(WarResultsCodec.SCHEMA, "war-results-window", "");
        for (String token : List.of("1.0", "1e0", "true", "\"1\"")) {
            assertInstanceOf(ProjectionResult.Rejected.class, call(ProjectionOperation.MILITARY_WAR_RESULTS_PLAN,
                    valid.replace("\"native_revision\":1", "\"native_revision\":" + token)));
        }
        assertInstanceOf(ProjectionResult.Rejected.class, call(ProjectionOperation.MILITARY_WAR_OVERVIEW_PLAN, valid));
    }
    @Test void independentOwnerUsesOriginalReceiptAndStrictUint64Domain() {
        String id = "18446744073709551615";
        String owner = "{\"schema\":\"xar.ck3.war-results-owner-receipt-input/v1\",\"expected_request_id\":\"owner-1\",\"owner_receipt\":{"
                + "\"request_id\":\"owner-1\",\"ticket_sequence\":" + id + ",\"executor_started_sequence\":" + id
                + ",\"completed_sequence\":" + id + ",\"pump_epoch\":" + id + ",\"thread_id\":4294967295,\"date_raw\":24,\"connection_generation\":1}}";
        var actual = assertInstanceOf(ProjectionResult.Succeeded.class, call(ProjectionOperation.MILITARY_WAR_RESULTS_SOURCE_OWNER, owner));
        assertEquals(StrictJson.UINT64_MAX, StrictJson.parse(actual.result().bytes()).get("ticket_sequence").bigIntegerValue());
        assertInstanceOf(ProjectionResult.Rejected.class, call(ProjectionOperation.MILITARY_WAR_RESULTS_SOURCE_OWNER,
                owner.replace("\"expected_request_id\":\"owner-1\"", "\"expected_request_id\":\"foreign\"")));
        assertInstanceOf(ProjectionResult.Rejected.class, call(ProjectionOperation.MILITARY_WAR_RESULTS_SOURCE_OWNER,
                owner.replace("\"thread_id\":4294967295", "\"thread_id\":4294967295.0")));
    }
    @Test void mandatoryRealBaselineRejectsH2743AndExitCollectorStaysDisabled() throws IOException {
        byte[] golden;
        try (var input = getClass().getResourceAsStream("/dejureexitterms/baseline-input.json")) {
            if (input == null) { throw new IOException("mandatory real producer baseline missing"); }
            golden = input.readAllBytes();
        }
        var observation = (com.fasterxml.jackson.databind.node.ObjectNode) StrictJson.parse(golden);
        observation.putObject("h2743_stock_predicate_evidence_v1").put("same_frame_stable", true);
        var root = StrictJson.object(); root.put("schema", "xar.ck3.dejure-baseline-input/v1"); root.set("observation", observation);
        var frame = root.putObject("expected_frame"); frame.put("war_id", 16777231).put("native_revision", 3).put("date_raw", 53217264)
                .put("defender_id", 29829).put("attacker_id", 30097).putArray("target_title_ids").add(2128);
        assertInstanceOf(ProjectionResult.Rejected.class, call(ProjectionOperation.MILITARY_DEJURE_BASELINE_NORMALIZE,
                new String(StrictJson.canonical(root), StandardCharsets.UTF_8)));
        assertFalse(WarExitTerms.PRODUCTION_ENABLED);
        assertTrue(dispatcher.profiles().stream().noneMatch(row -> row.operation().wire().contains("submit")));
    }
}
