package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.military.OrdinaryAutomaticSurrenderPolicy.Variant;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;

/** Canonical command and original UNKNOWN fence consumers; no synthetic Root/private authority is issued. */
final class ArmyAutomaticSurrenderDurableTest {
    private static final Instant NOW = Instant.parse("2026-10-24T10:00:00Z");
    private static final ExactRef REF = new ExactRef("D:/synthetic-no-authority/automatic-options.json", 12, "b".repeat(64));
    private static ArmyTypes.Context context() {
        var source = new G2Source("synthetic-no-game", NOW.toString(), "1.20.0.4", REF);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(7), BigInteger.valueOf(3), BigInteger.valueOf(100)), "native:3", BigInteger.TEN, "original-episode");
        var identity = new ProposalLifecycle.ObservationIdentity(source.machineId(), new GameGeneration(123, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1);
        return new ArmyTypes.Context(identity, source, "original-session", NOW.plusSeconds(30));
    }
    private static ArmyCalls.War call() { return new ArmyCalls.War(PublicMethod.SURRENDER_WAR,
            new ArmyCalls.Revision(new ArmyTypes.Present<>(BigInteger.TEN)), BigInteger.valueOf(23)); }
    private static ActionCommand command(ArmyOrdinaryActionArguments args) {
        var c = context();
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, c.before(), c.source(), "synthetic-contract-no-effect-authority/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("actual"), true)));
        return new ActionCommand("original-root-action", c.before(), c.source(), c.sessionId(), new OperationKey("surrender-war-23"),
                args.encode(), expected, ArmyOrdinaryActionPreparation.claims(call(), c), c.deadline());
    }
    @Test void coldCommandRetainsItsAutomaticVariantAndNeverBecomesExplicitSdk() {
        for (Variant variant : Variant.values()) {
            var args = new ArmyOrdinaryActionArguments(Kind.SURRENDER_WAR, ArmyCallCodec.encode(call()), List.of(REF), ExecutionProfile.GENERIC_AUTOMATIC_SURRENDER, Optional.of(variant));
            var original = command(args); var cold = ActionCodec.decodeCommand(ActionCodec.encodeCommand(original));
            assertEquals(original, cold); assertEquals(ActionCodec.bodySha256(original), ActionCodec.bodySha256(cold));
            var restored = decode(cold.arguments()); assertEquals(args, restored); assertEquals(variant, restored.automaticSurrender().orElseThrow());
            var sdk = command(new ArmyOrdinaryActionArguments(Kind.SURRENDER_WAR, ArmyCallCodec.encode(call()), List.of(REF)));
            assertNotEquals(ActionCodec.bodySha256(original), ActionCodec.bodySha256(sdk));
            var unknown = new ActionReceipt(1, 1, cold, ActionCodec.bodySha256(cold),
                    new ActionState.Unknown(Optional.empty(), Optional.empty(), "actual native outcome not observed", List.of(REF)));
            assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionService.rejectReplay(List.of(unknown), call(), context()),
                    "switching caller or profile cannot reissue an unresolved same-war surrender");
        }
    }
}
