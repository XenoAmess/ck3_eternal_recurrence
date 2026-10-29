package org.xar.ck3.control.application.planning;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.PlanningFixtures.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual command and ordinary wire consumers, with original decimal tokens rather than equal rounded numbers. */
final class PlanningWireNumericTokenTest {
    private static final OperationKey OP = new OperationKey("fixture-numeric-action");
    private static Obj numeric() {
        return DriverJson.object(("{\"strategy_score\":-0.0,\"scaled\":1.00,\"exponent\":1E+17,"
                + "\"huge\":184467440737095516170000000000000001,"
                + "\"nested\":[{\"emoji\":\"\uD83D\uDD25\",\"token\":-0.000}],"
                + "\"\uD83D\uDD25\":null}").getBytes(StandardCharsets.UTF_8), DriverJson.MAX_NATIVE_BYTES);
    }
    private static PlanTrace trace(PlanningRequest request, Obj data) {
        var actual = command(request, OP, data);
        var draft = new OrdinaryPolicy.Draft("fixture-original-producer", "selected", "native score retained",
                OrdinaryPolicy.Kind.FOREGROUND, Optional.of(actual), OrdinaryPolicy.Purpose.WORLD_ACTION,
                Optional.empty(), data);
        return new PlanTrace(request.before(), List.of(new PlanTrace.StageVisit(
                PlanningStage.TERMINAL_AND_FOREGROUND_WINDOWS, PlanTrace.Outcome.REPLACED,
                "original typed score", Optional.of(SOURCE), Optional.of(data))), Optional.of(draft));
    }
    @Test void requestPreservesSnapshotHistoryBattleAndCrossRunTokens() {
        Obj original = numeric();
        PlanningRequest base = request(snapshot().with("original_numeric", original),
                List.of(new Obj(Map.of("original_numeric", original))), Set.of(OP));
        var old = base.observations();
        var observed = new PlanningObservation(old.snapshot(), old.history(), old.actionSteps(),
                old.bridgeCapabilities(), Optional.of(original), old.actionFacts(), old.campaignGoal(),
                Optional.of(original), old.initialLifestyleFocusRequired());
        var actual = new PlanningRequest(base.before(), base.source(), base.sessionId(), base.deadline(), observed);
        byte[] encoded = PlanningWire.encodeRequest(actual);
        var roundTrip = PlanningWire.decodeRequest(encoded);
        assertEquals(actual, roundTrip);
        assertArrayEquals(encoded, PlanningWire.encodeRequest(roundTrip));
        assertTokens(roundTrip.observations().battleSpeedReadiness().orElseThrow());
        assertTokens(roundTrip.observations().crossRunPlan().orElseThrow());
    }
    @Test void selectedCommandTraceEvidenceAndFinalDraftUseSameActualActionCodec() {
        var request = request(snapshot(), List.of(), Set.of(OP));
        var trace = trace(request, numeric());
        var actualCommand = trace.finalPlan().orElseThrow().command().orElseThrow();
        var producer = new PlanningResult.ActionSelected(actualCommand, trace);
        byte[] standalone = ActionCodec.encodeCommand(actualCommand);
        assertEquals(actualCommand, ActionCodec.decodeCommand(standalone));
        byte[] encoded = PlanningWire.encodeResult(producer);
        var decoded = assertInstanceOf(PlanningResult.ActionSelected.class, PlanningWire.decodeResult(encoded));
        assertEquals(producer, decoded);
        assertArrayEquals(standalone, ActionCodec.encodeCommand(decoded.command()));
        assertTokens(decoded.command().arguments());
        assertTokens(decoded.trace().visits().getFirst().evidence().orElseThrow());
        assertTokens(decoded.trace().finalPlan().orElseThrow().detail());
        assertArrayEquals(encoded, PlanningWire.encodeResult(decoded));
        assertTrue(new String(encoded, StandardCharsets.UTF_8).contains("\"strategy_score\":-0.0"));
    }
    @Test void everyResultBranchRetainsItsTraceAndReconciliationDetail() {
        var request = request(snapshot(), List.of(), Set.of(OP));
        PlanTrace trace = trace(request, numeric());
        List<PlanningResult> actual = List.of(
                new PlanningResult.ReadOnlyWait(request.before(), "actual wait", trace),
                new PlanningResult.RefreshRequired(request.before(), "actual refresh", trace),
                new PlanningResult.Stopped(request.before(), PlanningResult.StopReason.POLICY_BLOCKED, "actual stop", trace),
                new PlanningResult.IncompleteMigration(request.before(), List.of(PlanningStage.ORDINARY_CORE), trace),
                new PlanningResult.ExistingActionReconciliation("retained-action", request.before(), numeric(), trace));
        for (PlanningResult result : actual) {
            byte[] encoded = PlanningWire.encodeResult(result);
            assertEquals(result, PlanningWire.decodeResult(encoded));
            assertArrayEquals(encoded, PlanningWire.encodeResult(PlanningWire.decodeResult(encoded)));
        }
    }
    @Test void closedSchemaAndExactTypesStillRejectWrongFieldsAndDuplicateInputs() {
        var request = request(snapshot(), List.of(), Set.of(OP));
        String encoded = new String(PlanningWire.encodeRequest(request), StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> PlanningWire.decodeRequest(
                encoded.replace("\"schema\":", "\"unexpected\":0,\"schema\":").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> PlanningWire.decodeRequest(
                encoded.replace("\"initial_lifestyle_focus_required\":false",
                        "\"initial_lifestyle_focus_required\":0").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> PlanningWire.decodeRequest(
                encoded.replace("\"schema\":", "\"session_id\":\"forged\",\"schema\":").getBytes(StandardCharsets.UTF_8)));
        var selected = new PlanningResult.ActionSelected(trace(request, numeric()).finalPlan().orElseThrow()
                .command().orElseThrow(), trace(request, numeric()));
        String result = new String(PlanningWire.encodeResult(selected), StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> PlanningWire.decodeResult(
                result.replace("\"visits\":[", "\"visits\":false,\"unknown_visits\":[").getBytes(StandardCharsets.UTF_8)));
    }
    @Test void explicitTypedByteLeaseChecksLimitsAndActualUtf8Extent() {
        var text = new Text("\uD83D\uDD25");
        byte[] actual = PublicDataJson.encodeTypedBytes(text, 6);
        assertEquals(6, actual.length);
        assertArrayEquals("\"\uD83D\uDD25\"".getBytes(StandardCharsets.UTF_8), actual);
        assertThrows(IllegalArgumentException.class, () -> PublicDataJson.encodeTypedBytes(text, 5));
        assertThrows(IllegalArgumentException.class, () -> PublicDataJson.encodeTypedBytes(text, 0));
        assertThrows(IllegalArgumentException.class, () -> PublicDataJson.encodeTypedBytes(text, PlanningWire.MAX_BYTES + 1));
        assertEquals(256 * 1024 * 1024, PlanningWire.MAX_BYTES);
    }
    private static void assertTokens(Obj actual) {
        assertEquals(new DecimalValue("-0.0"), actual.get("strategy_score"));
        assertEquals(new DecimalValue("1.00"), actual.get("scaled"));
        assertEquals(new DecimalValue("1E+17"), actual.get("exponent"));
        assertEquals(new IntegerValue(new BigInteger("184467440737095516170000000000000001")), actual.get("huge"));
        assertEquals(numeric(), actual);
    }
}
