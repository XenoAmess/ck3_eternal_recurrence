package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeWarExitEffects;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;

/** Actual Army public producer -> Root expected producer -> shared M0 operation parser -> consumer.
 * DATA vectors only. No constructor grants an original-pending Root lease or native permission.
 */
final class RootWarExitTruceGrammarTest {
    private static ArmyTypes.Context context() {
        var now=Instant.parse("2026-10-24T00:00:00Z");var ref=new ExactRef("memory/war-exit-data-only",1,"a".repeat(64));
        var source=new G2Source("software-only-machine",now.toString(),"1.20.0.4",ref);
        var identity=new ProposalLifecycle.ObservationIdentity(source.machineId(),new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.valueOf(9),BigInteger.valueOf(10660101)),"before9",BigInteger.TEN,"episode-original"),1);
        return new ArmyTypes.Context(identity,source,"held-original",now.plusSeconds(30));
    }
    private static ArmyCalls.War call(PublicMethod method,BigInteger war) {
        return new ArmyCalls.War(method,new ArmyCalls.Revision(new ArmyTypes.Present<>(BigInteger.TEN)),war);
    }
    private static ActionCommand command(ArmyCalls.War selected) {
        var current=context();var decoded=ArmyCallCodec.decode(selected.method(),ArmyCallCodec.encode(selected));assertEquals(selected,decoded);
        var request=ArmyOrdinaryActionPreparation.primitive(decoded,current,List.of());
        var args=new ArmyOrdinaryActionArguments(ArmyOrdinaryActionPreparation.kind(decoded),ArmyCallCodec.encode(decoded),List.of());
        var operation=new OperationKey(request.step());
        var expected=RootArmyOrdinaryRuntimeInputs.warExitExpected(current.before(),current.source(),operation,args.raw());
        var command=new ActionCommand("data-only-"+request.step(),current.before(),current.source(),current.sessionId(),operation,args.encode(),expected,
                ArmyOrdinaryActionPreparation.claims(decoded,current),current.deadline());
        return ActionCodec.decodeCommand(ActionCodec.encodeCommand(command));
    }
    @Test void enforceZeroAndFullSafeIntegerRetainTheOriginalProducerRange() {
        for(BigInteger war:List.of(BigInteger.ZERO,BigInteger.ONE,new BigInteger("9007199254740991"))) {
            var command=command(call(PublicMethod.ENFORCE_DEMANDS,war));
            assertEquals(war.longValueExact(),NativeWarExitEffects.warId(command.operation()));assertTrue(RootWarExitTruceReads.accepts(command));
        }
    }
    @Test void whitePeaceAndSurrenderKeepTheirSeparatePositiveInt32Range() {
        for(PublicMethod method:List.of(PublicMethod.OFFER_WHITE_PEACE,PublicMethod.SURRENDER_WAR)) {
            for(BigInteger war:List.of(BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE)))assertTrue(RootWarExitTruceReads.accepts(command(call(method,war))));
            assertThrows(IllegalArgumentException.class,()->call(method,BigInteger.ZERO));
            assertThrows(IllegalArgumentException.class,()->call(method,BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE)));
        }
        assertThrows(IllegalArgumentException.class,()->call(PublicMethod.ENFORCE_DEMANDS,new BigInteger("9007199254740992")));
    }
    @Test void unrelatedOperationCannotAcquireAQueryCandidateFromObserverSchemaAlone() {
        var original=command(call(PublicMethod.ENFORCE_DEMANDS,BigInteger.ZERO));
        var wrong=new ActionCommand(original.actionId(),original.before(),original.source(),original.sessionId(),new OperationKey("query-raiktor-actual-truce-expiry-v1-73"),
                original.arguments(),original.expected(),original.claims(),original.deadline());assertFalse(RootWarExitTruceReads.accepts(wrong));
    }
}
