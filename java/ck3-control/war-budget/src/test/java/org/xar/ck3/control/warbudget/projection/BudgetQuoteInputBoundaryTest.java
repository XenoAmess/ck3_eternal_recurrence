package org.xar.ck3.control.warbudget.projection;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.ServiceLoader;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionDispatcher;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.ProjectionWire;
import org.xar.ck3.control.warbudget.WarBudgetCodec;

/** Raw inputs reach the registered application through its real wire dispatcher. No test policy or transport. */
final class BudgetQuoteInputBoundaryTest {
    private static final String MISSING = "<missing-field>";

    @Test
    void registeredQuoteKeepsItsValidResultAndUnboundedPositiveWarIdentity() {
        byte[] raw = quote("11", "11", "1", "3", Optional.empty());
        ProjectionResult.Succeeded result = succeeded(raw);
        assertArrayEquals(WarBudgetCodec.evaluate(raw), result.result().bytes());
        JsonNode value = StrictJson.parse(result.result().bytes());
        assertTrue(value.path("applied").booleanValue());
        assertEquals(1, value.path("revision").path("level").intValue());
        assertEquals(100_000_000L, value.path("total_package_limit_raw").longValue());
        assertEquals(99_999_995L, value.path("finance").path("gold_after_contract_raw").longValue());
        assertEquals("budget-boundary", value.path("revision").path("epoch_id").textValue());
        assertFalse(value.path("crisis_spend_down_policy_eligible").booleanValue());

        String largeId = BigInteger.ONE.shiftLeft(90).toString();
        JsonNode large = result(quote(largeId, largeId, "1", "3", Optional.empty()));
        assertTrue(large.path("applied").booleanValue());
        assertEquals(new BigInteger(largeId), large.path("revision").path("policy_evidence").path("war_id").bigIntegerValue());
    }

    @Test
    void eligibleQuoteRejectsEachMissingNullBooleanFloatingOrNonpositiveWarIdentity() {
        for (String token : List.of(MISSING, "null", "true", "1.0", "0", "-1")) {
            refused(quote(token, "11", "1", "3", Optional.empty()), "positive exact war identities");
            refused(quote("11", token, "1", "3", Optional.empty()), "positive exact war identities");
            // Equal malformed identities used to pass equality, including both absent fields.
            refused(quote(token, token, "1", "3", Optional.empty()), "positive exact war identities");
        }
    }

    @Test
    void validDifferentWarsAndDisabledPolicyKeepTheirOriginalInactiveOutcome() {
        JsonNode different = result(quote("11", "12", "1", "3", Optional.empty()));
        assertFalse(different.path("applied").booleanValue());
        assertEquals("no_qualified_emergency_marginal_value", different.path("reason").textValue());
        String raw = new String(quote(MISSING, MISSING, "1", "3", Optional.empty()), StandardCharsets.UTF_8);
        assertTrue(raw.contains("\"eligible\":true"));
        JsonNode disabled = result(raw.replace("\"eligible\":true", "\"eligible\":false").getBytes(StandardCharsets.UTF_8));
        assertEquals(different, disabled);
    }

    @Test
    void rawWrongTypesAndOverflowAtAllThreeIntConversionsAreDomainInputRefusals() {
        for (String token : List.of("true", "1.0", "null", "2147483648", "-2147483649",
                "999999999999999999999999999999999999999999999999999999999999")) {
            String reason = token.equals("true") || token.equals("1.0") || token.equals("null")
                    ? "exact budget integer required" : "signed32 range";
            refused(quote("11", "11", token, "3", Optional.empty()), reason);
            refused(quote("11", "11", "1", token, Optional.empty()), reason);
            refused(quote("11", "11", "1", "3", Optional.of(token)), reason);
        }
        refused(quote("11", "11", MISSING, "3", Optional.empty()), "exact budget integer required");
        refused(quote("11", "11", "1", MISSING, Optional.empty()), "exact budget integer required");
    }

    @Test
    void missingPreviousLevelKeepsDefaultZeroAndExistingLevelKeepsItsLockedLimit() {
        JsonNode missing = result(quote("11", "11", "1", "3", Optional.of(MISSING)));
        assertTrue(missing.path("applied").booleanValue());
        assertEquals(1, missing.path("revision").path("level").intValue());
        assertFalse(missing.path("revision").path("reuses_locked_level_limit").booleanValue());
        assertEquals("prior-budget", missing.path("revision").path("epoch_id").textValue());

        JsonNode locked = result(quote("11", "11", "1", "3", Optional.of("1")));
        assertTrue(locked.path("applied").booleanValue());
        assertTrue(locked.path("revision").path("reuses_locked_level_limit").booleanValue());
        assertEquals(100_000_000L, locked.path("total_package_limit_raw").longValue());
    }

    @Test
    void existingMaintenanceWindowPolicyAndLevelTwoRemainUnchanged() {
        for (String token : List.of("0", "19", "-1")) {
            refused(quote("11", "11", "1", token, Optional.empty()), "declared allocation window/commitments invalid");
        }
        JsonNode levelTwo = result(quote("11", "11", "2", "3", Optional.empty()));
        assertTrue(levelTwo.path("applied").booleanValue());
        assertEquals(2, levelTwo.path("revision").path("level").intValue());
        assertFalse(levelTwo.path("crisis_spend_down_policy_eligible").booleanValue());
    }

    private static ProjectionResult dispatch(byte[] raw) {
        ProjectionDispatcher dispatcher = ProjectionDispatcher.fromCatalogs(ServiceLoader.load(ProjectionPortCatalog.class));
        ProjectionCall call = new ProjectionCall(
                new ProjectionCall.Identity("budget-quote-input-boundary", ProjectionOperation.WAR_BUDGET_EVALUATE),
                ProjectionJson.object(raw, 65_536));
        assertArrayEquals(raw, call.payload().bytes(), "raw numeric token types must reach the domain unchanged");
        return dispatcher.dispatch(ProjectionWire.encodeCall(call));
    }

    private static ProjectionResult.Succeeded succeeded(byte[] raw) {
        ProjectionResult.Succeeded value = assertInstanceOf(ProjectionResult.Succeeded.class, dispatch(raw));
        assertEquals(ProjectionOperation.WAR_BUDGET_EVALUATE, value.identity().operation());
        return value;
    }

    private static JsonNode result(byte[] raw) { return StrictJson.parse(succeeded(raw).result().bytes()); }

    private static void refused(byte[] raw, String reason) {
        ProjectionResult.Rejected rejection = assertInstanceOf(ProjectionResult.Rejected.class, dispatch(raw));
        assertEquals(ProjectionError.Code.DOMAIN_REJECTED, rejection.error().code());
        assertEquals(ProjectionOperation.WAR_BUDGET_EVALUATE, rejection.identity().orElseThrow().operation());
        assertTrue(rejection.error().message().contains(reason), rejection.error().message());
        // The original byte entrance still preserves its public ContractViolationException prototype.
        ContractViolationException legacy = assertThrows(ContractViolationException.class, () -> WarBudgetCodec.evaluate(raw));
        assertTrue(legacy.getMessage().contains(reason), legacy.getMessage());
    }

    private static String field(String name, String rawToken) {
        return rawToken.equals(MISSING) ? "" : "\"" + name + "\":" + rawToken + ",";
    }

    private static byte[] quote(String policyId, String focusId, String level, String window, Optional<String> previousLevel) {
        String previous = previousLevel.map(token -> ",\"emergency_budget_epoch_v1\":{\"epoch_id\":\"prior-budget\","
                + field("level", token) + "\"ordinary_reserve_target_raw\":0,\"total_package_limit_raw\":100000000}").orElse("");
        String raw = """
                {"schema":"g2.war-budget-request/v1","operation":"emergency_quote_budget_v1","arguments":{
                  "snapshot":{"played_character":{"character_id":7},"native_revision":2,"revision":4,"date_raw":3,
                    "snapshot_id":"native:2","episode_run_id":"budget-boundary","active_wars":[],
                    "played_character_gold":{"raw":100000000,"scale":100000}},
                  "policy":{"eligible":true,%s%s"fixed_gold_floor_raw":0,%s"other_reserved_gold_raw":0},
                  "focus":{%s"observed_player_raised_soldiers":1,"observed_enemy_raised_soldiers":2},
                  "local":{},"troops":2,"price":5,"contract_months":3,
                  "root":{"status":"available","player_character_id":7,"snapshot_revision":2,"date_raw":3,
                    "player_monthly_gold_income":{"raw":1000000,"scale":100000},
                    "player_max_monthly_gold_maintenance_v1":{"status":"available","value":{"raw":0,"scale":100000}}},
                  "normal_finance":{"status":"available","observed_treasury_raw":100000000,"required_gold_reserve_raw":0},
                  "package":{"anchor_action_request_id":"budget-boundary"%s}
                }}
                """.formatted(field("war_id", policyId), field("level", level), field("maintenance_window_months", window),
                        field("war_id", focusId), previous);
        return raw.getBytes(StandardCharsets.UTF_8);
    }
}
