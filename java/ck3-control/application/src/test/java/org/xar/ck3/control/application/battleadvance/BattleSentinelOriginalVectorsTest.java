package org.xar.ck3.control.application.battleadvance;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.reconciliation.LateOutcome.Mode;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;
import org.xar.ck3.control.application.action.RawJson;

/** The oracle was executed from unedited original native_driver.py AST nodes, with source SHA/line pins. */
final class BattleSentinelOriginalVectorsTest {
    @Test void actualA11FailedWindowArmAndSubmittedAcksCannotBecomeNativeStopProof() throws Exception {
        JsonNode failure;
        try (var input = getClass().getResourceAsStream("/battleadvance/a11_original_failed_route_window_5279.json")) {
            assertNotNull(input); failure = new ObjectMapper().readTree(input).get("result");
        }
        assertEquals("postcondition_failed", failure.path("progress_status").textValue());
        assertEquals(0, failure.path("elapsed_days").intValue()); assertFalse(failure.path("paused").booleanValue());
        assertTrue(failure.path("tactical_daily_sentinel").isNull());
        var arm = SentinelObservation.decode(failure.get("armed_tactical_daily_sentinel"));
        var watch = List.of(117440697, 234881394, 285212941);
        BattleSentinelValidation.arm(arm, 53274624, 53274696, 3, Mode.TERMINAL_OR_SENTINEL, watch, BattleAdvanceStep.Scope.ROUTE_CONTACT_WINDOW);
        assertThrows(IllegalArgumentException.class, () -> BattleSentinelValidation.stop(arm, arm, 53274624, 53274696, 53274624, 3, Mode.TERMINAL_OR_SENTINEL, watch));
        assertTrue(failure.path("managed_failure_cleanup").path("error").textValue().contains("pause_ack_statuses=['submitted', 'submitted']"));
        var decoded = BattleAdvanceResultCodec.decode(new RawJson(failure.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8)), BattleAdvanceResultCodec.Profile.LEGACY_NATIVE_V1);
        assertEquals(arm, decoded.armed().orElseThrow()); assertTrue(decoded.sentinel().isEmpty());
    }
    @Test void originalHelperAcceptanceAndRealFaultsMatchJava() throws Exception {
        JsonNode root;
        try (var input = getClass().getResourceAsStream("/battleadvance/original-sentinel-vectors01.json")) {
            assertNotNull(input, "required captured original oracle was not packaged"); root = new ObjectMapper().readTree(input);
        }
        assertEquals(17, root.path("cases").size());
        assertEquals("original unedited AST helpers, no Game", root.path("execution").textValue());
        var arm = SentinelObservation.decode(root.get("arm"));
        for (JsonNode row : root.get("cases")) {
            boolean accepted;
            try {
                var status = SentinelObservation.decode(row.get("status"));
                if (row.path("kind").textValue().equals("arm")) {
                    var scope = row.path("scope").textValue().equals("committed_route") ? BattleAdvanceStep.Scope.COMMITTED_ROUTE : BattleAdvanceStep.Scope.ACTIVE_BATTLE;
                    BattleSentinelValidation.arm(status, 100, 124, 3, Mode.DECISION_EPOCH, List.of(0), scope);
                } else BattleSentinelValidation.stop(status, arm, 100, 124, 124, 3, Mode.DECISION_EPOCH, List.of(0));
                accepted = true;
            } catch (IllegalArgumentException error) { accepted = false; }
            assertEquals(row.path("accepted").booleanValue(), accepted, row.path("name").textValue());
        }
    }
}
