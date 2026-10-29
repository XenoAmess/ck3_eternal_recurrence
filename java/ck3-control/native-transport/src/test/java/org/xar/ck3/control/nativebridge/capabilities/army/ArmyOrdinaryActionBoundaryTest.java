package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyCalls.Frame;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyCalls.*;

/** These vectors exercise production public decode, durable custody, native preparation and the no-replay guard. */
final class ArmyOrdinaryActionBoundaryTest {
    static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    static final ExactRef REF = new ExactRef("D:/contract-vectors/army-source.json", 1, "a".repeat(64));
    static final G2Source SOURCE = new G2Source("xenoamess-full-tower-eb9d2c1186", NOW.toString(), "1.20.0.4", REF);
    static final Revision REV = new Revision(new Present<>(BigInteger.TEN));
    static Context context() { return context(100); }
    static Context context(int dateRaw) {
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(7), BigInteger.valueOf(20), BigInteger.valueOf(dateRaw)), "native-20", BigInteger.TEN, "episode-original");
        var identity = new ProposalLifecycle.ObservationIdentity(SOURCE.machineId(), new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))), frame, 1);
        return new Context(identity, SOURCE, "session-original", NOW.plusSeconds(30));
    }
    static List<Call> calls() {
        return List.of(new CallAlly(REV, new FullId(Integer.MIN_VALUE), new FullId(Integer.MAX_VALUE)),
                new CreateMaa(REV, Integer.MAX_VALUE, "native-action", new Missing<>()),
                new Frame(PublicMethod.CLOSE_WAR_DECLARED_OVERVIEW_V1, REV), new Frame(PublicMethod.CLOSE_WAR_RESULTS_WINDOW_V1, REV),
                new Declaration(PublicMethod.DECLARE_WAR, REV, "8-9--1"), new Frame(PublicMethod.RAISE_TROOPS_DEFAULT, REV),
                new Move(REV, new PublicUnitId(0), new PositiveId(Integer.MAX_VALUE)),
                new Siege(PublicMethod.START_ASSAULT, REV, new PositiveId(Integer.MAX_VALUE)), new Siege(PublicMethod.STOP_ASSAULT, REV, new PositiveId(1)),
                new Unit(PublicMethod.DISBAND_ARMY, REV, new PublicUnitId(0)),
                new War(PublicMethod.ENFORCE_DEMANDS, REV, BigInteger.ZERO), new War(PublicMethod.SURRENDER_WAR, REV, BigInteger.ONE), new War(PublicMethod.OFFER_WHITE_PEACE, REV, BigInteger.ONE),
                new Hire(PublicMethod.HIRE_MERCENARY_V1, REV, new HireId(0)), new Hire(PublicMethod.HIRE_HOLY_ORDER_V1, REV, new HireId(4294967294L)),
                new AssignCommander(REV, new PublicUnitId(0), new PublicUnitId(0)), new Sampling(REV, false));
    }
    @Test void allSeventeenActualPublicSelectionsRoundTripThroughTheSingleCodec() {
        assertEquals(17, calls().size()); assertEquals(17, calls().stream().map(ArmyOrdinaryActionPreparation::kind).distinct().count());
        for (Call call : calls()) {
            Call decoded = ArmyCallCodec.decode(call.method(), ArmyCallCodec.encode(call)); assertEquals(call, decoded);
            var custody = new ArmyOrdinaryActionArguments(ArmyOrdinaryActionPreparation.kind(call), ArmyCallCodec.encode(call), List.of());
            assertEquals(call, ArmyCallCodec.decode(call.method(), ArmyOrdinaryActionArguments.decode(custody.raw()).publicArguments()));
        }
    }
    @Test void readAndCompositeMethodsCannotBeTurnedIntoNativeMutations() {
        for (Call call : List.of(new Empty(), new Frame(PublicMethod.QUERY_DECLARABLE_WARS, REV), new Unit(PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1, REV, new PublicUnitId(0)),
                new RetreatPreview(REV, new PublicUnitId(0), new PositiveId(1))))
            assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionPreparation.primitive(call, context(), List.of()));
        assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionPreparation.primitive(new AssignCommander(REV, new PublicUnitId(0), new PublicUnitId(0)), context(), List.of()));
        assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionPreparation.primitive(new Hire(PublicMethod.HIRE_MERCENARY_V1, REV, new HireId(0)), context(), List.of()));
    }
    @Test void wireFieldsRetainNativeNumbersAndPrivateQuoteOrderWithoutGenericStringification() {
        var call = new CallAlly(REV, new FullId(Integer.MIN_VALUE), new FullId(Integer.MAX_VALUE));
        List<Long> slots = List.of(Long.MIN_VALUE, -1L, 0L, 1L, 2L, 3L, 4L, 5L, 6L, Long.MAX_VALUE);
        var nativeRequest = ArmyOrdinaryActionPreparation.primitive(call, context(), slots);
        var fields = ArmyJson.parse(nativeRequest.additionalFields().bytes());
        assertEquals(Integer.MIN_VALUE, fields.get("war_id").intValue()); assertEquals(Integer.MAX_VALUE, fields.get("recipient_character_id").intValue());
        assertEquals(BigInteger.valueOf(Long.MIN_VALUE), fields.get("expected_send_cost_raw").get(0).bigIntegerValue());
        assertEquals(BigInteger.valueOf(Long.MAX_VALUE), fields.get("expected_send_cost_raw").get(9).bigIntegerValue());
        assertTrue(nativeRequest.requiredCapability().isEmpty()); assertFalse(fields.has("request_id")); assertFalse(fields.has("expected_revision"));
        assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionPreparation.primitive(call, context(), List.of()));
        var maa = ArmyOrdinaryActionPreparation.primitive(new CreateMaa(REV, 0, "a", new Missing<>()), context(), List.of());
        var sent = ArmyJson.parse(maa.additionalFields().bytes());
        assertEquals(context().nativeRevision(), sent.get("expected_snapshot_revision").bigIntegerValue());
        assertEquals(BigInteger.TEN, sent.get("expected_public_revision").bigIntegerValue()); assertEquals(0, sent.get("type_index").intValue());
    }
    @Test void wrongRuntimeIntegerTypesAndExtraPublicFieldsFailBeforePreparation() {
        for (String value : List.of("true", "false", "1.0", "\"1\"", "null", "[]", "{}")) {
            String json = "{\"army_id\":" + value + ",\"target_province_id\":123}";
            assertThrows(IllegalArgumentException.class, () -> ArmyCallCodec.decode(PublicMethod.MOVE_ARMY, new RawJson(json.getBytes(StandardCharsets.UTF_8))));
        }
        assertThrows(IllegalArgumentException.class, () -> ArmyCallCodec.decode(PublicMethod.MOVE_ARMY, new RawJson("{\"army_id\":0,\"target_province_id\":1,\"accepted\":true}".getBytes(StandardCharsets.UTF_8))));
        assertThrows(IllegalArgumentException.class, () -> ArmyCallCodec.decode(PublicMethod.MOVE_ARMY, new RawJson("{\"army_id\":0}".getBytes(StandardCharsets.UTF_8))));
    }
    @Test void publicZeroAndFullGenerationClaimsArePreserved() {
        var movement = ArmyOrdinaryActionPreparation.claims(new Move(REV, new PublicUnitId(0), new PositiveId(1)), context());
        assertEquals(Set.of(BigInteger.ZERO), movement.armyIds());
        var ally = ArmyOrdinaryActionPreparation.claims(new CallAlly(REV, new FullId(Integer.MIN_VALUE), new FullId(Integer.MIN_VALUE)), context());
        assertTrue(ally.allyCharacterIds().isEmpty()); assertTrue(ally.commitmentKeys().iterator().next().contains("-2147483648"));
    }
    @Test void unknownSameResourceCannotBeReplayedUnderANewActionId() {
        Call call = new Move(REV, new PublicUnitId(0), new PositiveId(1)); var source = context();
        var command = command(call, "original-root-id");
        var unknown = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command),
                new ActionState.Unknown(Optional.empty(), Optional.empty(), "original native outcome unknown", List.of(REF)));
        assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionService.rejectReplay(List.of(unknown), call, source));
        assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionService.rejectReplay(List.of(unknown), new Unit(PublicMethod.DISBAND_ARMY, REV, new PublicUnitId(0)), source));
        assertDoesNotThrow(() -> ArmyOrdinaryActionService.rejectReplay(List.of(unknown), new Move(REV, new PublicUnitId(1), new PositiveId(1)), source));
    }
    @Test void staleExpectedRevisionCannotPrepareASecondPrimitive() {
        assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionPreparation.primitive(new Move(new Revision(new Present<>(BigInteger.valueOf(9))), new PublicUnitId(0), new PositiveId(1)), context(), List.of()));
    }
    @Test void settledTerminalReplayFencesUseCompleteWarIdsAndKeepUnknownIsolation() throws Exception {
        for (var ids : List.of(List.of(BigInteger.valueOf(23), BigInteger.valueOf(24)),
                List.of(BigInteger.valueOf(16777239), BigInteger.valueOf(33554455)))) {
            BigInteger first = ids.get(0), second = ids.get(1);
            var otherSurrender = new War(PublicMethod.SURRENDER_WAR, REV, second);
            var otherWhite = new War(PublicMethod.OFFER_WHITE_PEACE, REV, second);
            for (PublicMethod method : List.of(PublicMethod.ENFORCE_DEMANDS, PublicMethod.SURRENDER_WAR, PublicMethod.OFFER_WHITE_PEACE)) {
                var old = settledWar(method, first);
                assertEquals(ActionReceipt.Outcome.REJECTED_CONFIRMED, old.outcome());
                assertEquals(Set.of(context().playerId()), old.command().claims().characterIds());
                assertTrue(old.command().claims().overlaps(ArmyOrdinaryActionPreparation.claims(otherSurrender, context())));
                assertDoesNotThrow(() -> ArmyOrdinaryActionService.rejectReplay(List.of(old), otherSurrender, context()));
                assertDoesNotThrow(() -> ArmyOrdinaryActionService.rejectReplay(List.of(old), otherWhite, context()));
                assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionService.rejectReplay(List.of(old),
                        new War(PublicMethod.SURRENDER_WAR, REV, first), context()));
                var unresolved = new ActionReceipt(1, 1, old.command(), old.bodySha256(),
                        new ActionState.Unknown(ActionTransitions.attempt(old.state()), Optional.empty(),
                                "synthetic original outcome unknown", List.of(REF)));
                assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionService.rejectReplay(List.of(unresolved),
                        otherSurrender, context()));
                if (method == PublicMethod.OFFER_WHITE_PEACE) {
                    var sameWhite = new War(PublicMethod.OFFER_WHITE_PEACE, REV, first);
                    assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionService.rejectReplay(List.of(old), sameWhite, context(819)));
                    assertDoesNotThrow(() -> ArmyOrdinaryActionService.rejectReplay(List.of(old), sameWhite, context(820)));
                }
            }
        }
    }
    /** Historical negative-ACK DATA for the pure replay fence; this does not qualify a Game or a writer. */
    private static ActionReceipt settledWar(PublicMethod method, BigInteger warId) throws Exception {
        var c = context(); var call = new War(method, REV, warId);
        var request = ArmyOrdinaryActionPreparation.primitive(call, c, List.of());
        var command = ActionCodec.decodeCommand(ActionCodec.encodeCommand(command(call, "old-" + request.step())));
        var operation = command.operation();
        var guard = new GuardEvidence(c.before(), c.source(), c.sessionId(), BigInteger.valueOf(5), operation,
                REF, REF, "software-fence-only", NOW, c.deadline());
        var attempt = new ActionState.Attempt("request-" + request.step(), NOW, guard, request);
        byte[] packet = org.xar.ck3.control.nativebridge.NativeWire.packet(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""
                + attempt.requestId() + "\",\"ok\":false,\"error\":\"synthetic native rejection\"}").getBytes(StandardCharsets.UTF_8));
        var decoded = assertInstanceOf(org.xar.ck3.control.nativebridge.NativeWire.CommandResult.class,
                org.xar.ck3.control.nativebridge.NativeWire.decode(packet));
        var ack = new NativeActionPort.AckReceived(decoded.requestId(), decoded.nativeOk(), Optional.empty(),
                new RawJson(decoded.payload().value()), decoded.packet().value());
        var original = new ExactRef("D:/contract-vectors/" + attempt.requestId() + ".bin", packet.length, ActionCodec.sha256(packet));
        var rejected = new ActionState.Rejected(attempt.requestId(), "synthetic native rejection", original);
        ActionEffects.validate(command, attempt, ack, rejected);
        return new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.Settled(attempt, ack, rejected));
    }
    private static ActionCommand command(Call call, String id) {
        var c = context(); var args = new ArmyOrdinaryActionArguments(ArmyOrdinaryActionPreparation.kind(call), ArmyCallCodec.encode(call), List.of());
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, c.before(), c.source(), "synthetic-boundary-only/v1", List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("actual"), true)));
        return new ActionCommand(id, c.before(), c.source(), c.sessionId(), new OperationKey(ArmyOrdinaryActionPreparation.primitive(call, c, List.of()).step()), args.encode(), expected, ArmyOrdinaryActionPreparation.claims(call, c), c.deadline());
    }
}
