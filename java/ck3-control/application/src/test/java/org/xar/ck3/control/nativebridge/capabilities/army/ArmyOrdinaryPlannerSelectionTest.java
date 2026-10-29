package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

final class ArmyOrdinaryPlannerSelectionTest {
    private static final BigInteger REVISION = new BigInteger("18446744073709551615");
    private static final Obj EMPTY = object("{}");
    private static Obj object(String json) { return DriverJson.object(json.getBytes(java.nio.charset.StandardCharsets.UTF_8), 65536); }
    @Test void actualTerminalShapeKeepsItsOutcomeAndNeverCopiesApplicationPlanIntoPublicArguments() {
        for (String outcome : List.of("player_victory", "white_peace", "surrender")) {
            String prefix = switch (outcome) { case "player_victory" -> "enforce-demands-"; case "white_peace" -> "offer-white-peace-"; default -> "surrender-war-"; };
            var operation = new OperationKey(prefix + "23");
            Obj original = object("{\"war_id\":23,\"requested_outcome\":\"" + outcome + "\",\"postcondition_plan\":null}");
            var selection = ArmyOrdinaryPlannerSelection.decode(operation, original, REVISION);
            Obj publicArgs = DriverJson.object(selection.publicArguments().bytes(), 65536);
            assertEquals(object("{\"war_id\":23,\"expected_revision\":\"18446744073709551615\"}"), publicArgs);
            var actual = new ArmyOrdinaryActionArguments(selection.kind(), selection.publicArguments(), List.of());
            assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryPlannerSelection.requirePrepared(operation, original, REVISION, actual));
            var retained = actual.withTerminalSelection(selection.terminalSelection());
            ArmyOrdinaryPlannerSelection.requirePrepared(operation, original, REVISION, ArmyOrdinaryActionArguments.decode(retained.raw()));
            assertEquals(original, OpportunityJson.parse(OpportunityJson.encode(original)));
        }
    }
    @Test void wrongFieldMissingFieldWrongIntegerAndOutcomeFailBeforeAnyNativeAdapter() {
        var operation = new OperationKey("offer-white-peace-23");
        for (String args : List.of(
                "{\"war_id\":23}",
                "{\"war_id\":true,\"requested_outcome\":\"white_peace\",\"postcondition_plan\":null}",
                "{\"war_id\":23.0,\"requested_outcome\":\"white_peace\",\"postcondition_plan\":null}",
                "{\"war_id\":\"23\",\"requested_outcome\":\"white_peace\",\"postcondition_plan\":null}",
                "{\"war_id\":24,\"requested_outcome\":\"white_peace\",\"postcondition_plan\":null}",
                "{\"war_id\":23,\"requested_outcome\":\"surrender\",\"postcondition_plan\":null}",
                "{\"war_id\":23,\"requested_outcome\":\"white_peace\",\"postcondition_plan\":[]}",
                "{\"war_id\":23,\"requested_outcome\":\"white_peace\",\"postcondition_plan\":null,\"native_ok\":true}"))
            assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryPlannerSelection.decode(operation, object(args), REVISION), args);
        assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryPlannerSelection.decode(new OperationKey("move-army-1-to-2"), object("{\"army_id\":1}"), REVISION));
    }
    @Test void preparationCustodyRejectsChangedKindSelectionRevisionAndExtraPublicArguments() {
        var operation = new OperationKey("move-army-0-to-31");
        var selected = ArmyOrdinaryPlannerSelection.decode(operation, EMPTY, REVISION);
        for (String changed : List.of(
                "{\"army_id\":1,\"target_province_id\":31,\"expected_revision\":\"18446744073709551615\"}",
                "{\"army_id\":0,\"target_province_id\":32,\"expected_revision\":\"18446744073709551615\"}",
                "{\"army_id\":0,\"target_province_id\":31,\"expected_revision\":\"18446744073709551614\"}",
                "{\"army_id\":0,\"target_province_id\":31,\"expected_revision\":\"18446744073709551615\",\"accepted\":true}")) {
            var actual = new ArmyOrdinaryActionArguments(selected.kind(), new org.xar.ck3.control.application.action.RawJson(DriverJson.encode(object(changed))), List.of());
            assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryPlannerSelection.requirePrepared(operation, EMPTY, REVISION, actual));
        }
        var wrongKind = new ArmyOrdinaryActionArguments(ArmyOrdinaryActionArguments.Kind.DISBAND_ARMY, selected.publicArguments(), List.of());
        assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryPlannerSelection.requirePrepared(operation, EMPTY, REVISION, wrongKind));
    }
    @Test void canonicalStepAndRangeBoundariesDoNotCreateFallbackRoutes() {
        for (String step : List.of("move-army-00-to-2", "start-assault-01", "advance-days-1", "merge-armies-1-with-2", "query-war-termination-options-23")) {
            var operation = new OperationKey(step); assertFalse(ArmyOrdinaryPlannerSelection.supports(operation));
            assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryPlannerSelection.decode(operation, EMPTY, REVISION));
        }
        for (String step : List.of("start-assault-0", "move-army-0-to-0", "surrender-war-2147483648", "enforce-demands-9007199254740992"))
            assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryPlannerSelection.decode(new OperationKey(step), EMPTY, REVISION));
        for (BigInteger revision : List.of(BigInteger.ZERO, BigInteger.ONE.negate(), REVISION.add(BigInteger.ONE)))
            assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryPlannerSelection.decode(new OperationKey("raise-troops-default"), EMPTY, revision));
    }
    @Test void actualPostwarCorePayloadRetainsExactArmyIdentityAndRejectsAliases() {
        var operation = new OperationKey("disband-army-7");
        var actual = ArmyOrdinaryPlannerSelection.decode(operation, object("{\"army_id\":7}"), REVISION);
        var empty = ArmyOrdinaryPlannerSelection.decode(operation, EMPTY, REVISION);
        assertEquals(empty, actual);
        ArmyOrdinaryPlannerSelection.requirePrepared(operation, object("{\"army_id\":7}"), REVISION,
                new ArmyOrdinaryActionArguments(actual.kind(), actual.publicArguments(), List.of()));
        for (String invalid : List.of("{\"army_id\":true}", "{\"army_id\":7.0}", "{\"army_id\":\"7\"}", "{\"army_id\":8}",
                "{\"army_id\":7,\"selected_army\":7}", "{\"selected_army\":7}"))
            assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryPlannerSelection.decode(operation, object(invalid), REVISION));
    }
}
