package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.military.MilitaryPlanningDecision;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyCallCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyCalls;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;

/** Actual admitted Root fixture assertions. No Core, Context, receipt or permission is created here. */
public final class RootRuntimeCommandsPolicyAssertions {
    private RootRuntimeCommandsPolicyAssertions(){ }
    /** The caller must supply the genuine original Root call, after physical planning freeze unwinds. Missing inputs mean NOT_RUN. */
    public static ActionCommand automaticSurrender(RootRuntimeCommands sameActualCommands,RootRuntimeContext actualContext,
            PlanningRequest actualOriginal,MilitaryPlanningDecision.Select actualChoice)throws Exception {
        assertTrue(actualChoice.operation().value().matches("surrender-war-[1-9][0-9]*"));
        var prepared=sameActualCommands.prepare(actualOriginal,actualChoice);
        ActionCommand actual=prepared.requireOriginalChoice(actualOriginal,actualChoice.operation(),actualChoice.arguments(),actualChoice.detail());
        assertSame(prepared.command(),actual);
        assertSame(actual,sameActualCommands.requireActualStrong(actualOriginal,actual));
        assertEquals(actualContext.source(),actual.source());
        assertEquals(actualContext.game().sessionId(),actual.sessionId());
        assertEquals(actualContext.game().generation(),actual.before().game());
        var original=ArmyOrdinaryActionArguments.decode(actual.arguments());
        assertEquals(ArmyOrdinaryActionArguments.Kind.SURRENDER_WAR,original.kind());
        assertEquals(ArmyOrdinaryActionArguments.ExecutionProfile.GENERIC_AUTOMATIC_SURRENDER,original.executionProfile());
        assertTrue(original.automaticSurrender().isPresent(),"the actual four-gate producer must retain its chosen original emergency variant");
        assertEquals(1,original.preflightReads().size(),"one actual original termination-options read is retained");
        var call=assertInstanceOf(ArmyCalls.War.class,ArmyCallCodec.decode(PublicMethod.SURRENDER_WAR,original.publicArguments()));
        assertEquals("surrender-war-"+call.warId(),actual.operation().value());
        ActionCommand cold=ActionCodec.decodeCommand(ActionCodec.encodeCommand(actual));
        assertArrayEquals(ActionCodec.encodeCommand(actual),ActionCodec.encodeCommand(cold));
        assertEquals(ActionCodec.bodySha256(actual),ActionCodec.bodySha256(cold));
        var retained=ArmyOrdinaryActionArguments.decode(cold.arguments());
        assertEquals(original,retained);assertEquals(original.automaticSurrender(),retained.automaticSurrender());
        return actual; // Preparation only. The sole Root still owns INTENT and the one physical submission.
    }
}
