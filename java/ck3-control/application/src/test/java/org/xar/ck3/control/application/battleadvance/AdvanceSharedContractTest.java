package org.xar.ck3.control.application.battleadvance;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;

/** Source-owner production seams used by the real Root/basic factory and installed typed read catalog. */
final class AdvanceSharedContractTest {
    @Test void rootAndOriginalChildShareOneExactExpectedProducerForEveryPrimitiveFamily() {
        var parent=BattleAdvanceFixture.parent();var frame=BattleAdvanceFixture.frame(1,100,true,false);
        for(String step:List.of("pause-map","resume-map","set-speed-1","set-speed-2","set-speed-3","set-speed-4","set-speed-5",
                ClockStatusRead.ARM_PREFIX+"100-to-124-speed-2-mode-terminal-a-3-11-22-33",ClockStatusRead.CANCEL_PREFIX+"37")){
            var operation=new OperationKey(step);
            var original=AdvancePrimitives.child(parent,frame,"actual-"+step,step,parent.deadline());
            assertEquals(original.expected(),AdvancePrimitives.expected(frame.identity(),frame.source(),operation,new OpportunityJson.Obj(Map.of())));
            assertEquals(frame.identity(),original.before());assertEquals(parent.claims(),original.claims());
        }
    }
    @Test void rootExpectedRejectsExtraWrongTypedArgumentsForeignOperationAndArmDate() {
        var frame=BattleAdvanceFixture.frame(1,100,true,false);
        assertThrows(IllegalArgumentException.class,()->AdvancePrimitives.expected(frame.identity(),frame.source(),new OperationKey("pause-map"),
                new OpportunityJson.Obj(Map.of("accepted",new OpportunityJson.Bool(true)))));
        for(String invalid:List.of("set-speed-6","other-pause-map",ClockStatusRead.CANCEL_PREFIX+"0",
                ClockStatusRead.ARM_PREFIX+"101-to-125-speed-2-mode-terminal-a-0"))
            assertThrows(IllegalArgumentException.class,()->AdvancePrimitives.expected(frame.identity(),frame.source(),new OperationKey(invalid),new OpportunityJson.Obj(Map.of())));
    }
    @Test void statusConsumerUsesTheExactEarlyInstalledSourceFactoryObjectAndPureReplay() {
        var fixture=new BattleAdvanceFixture();
        ReadContract<Status> installed=ClockStatusRead.registeredContract(BattleAdvanceFixture.REF);
        var status=new ClockStatusRead(fixture,installed,fixture.archiveForTest());
        assertSame(installed,status.contract());assertTrue(installed.hasPureReplay());
        assertEquals(ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,installed.guardMode());
        assertEquals(Optional.of(ClockStatusRead.STATUS_CAP),installed.requiredCapability());
        var parent=BattleAdvanceFixture.parent();
        var wrong=new PlanningReadRequest(parent.before(),parent.source(),parent.sessionId(),new OperationKey(ClockStatusRead.STEP),
                new OpportunityJson.Obj(Map.of("unregistered",new OpportunityJson.Bool(true))),parent.deadline());
        assertThrows(IllegalArgumentException.class,()->installed.prepare(wrong,"original-test-query"));
        var legacy=new ClockStatusRead(fixture,BattleAdvanceFixture.REF,fixture.archiveForTest());
        assertEquals(installed.sourceRef(),legacy.contract().sourceRef());assertEquals(installed.contractId(),legacy.contract().contractId());
        assertEquals(0,fixture.frameReads);assertTrue(fixture.steps.isEmpty());
    }
    @Test void matchingMetadataCannotReplaceTheActualInstalledStatusDecoderObject() {
        var fixture=new BattleAdvanceFixture();
        var forged=new ReadContract<Status>(ClockStatusRead.CONTRACT_ID,new OperationKey(ClockStatusRead.STEP),Optional.of(ClockStatusRead.STATUS_CAP),
                "tactical-daily-sentinel-status-v1",ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,BattleAdvanceFixture.REF,
                (request,id)->new NativeRequest(ClockStatusRead.STEP,ClockStatusRead.STATUS_CAP,new RawJson(new byte[]{123,125})),
                receipt->ClockStatusRead.decode(receipt.original()),receipt->ClockStatusRead.decode(receipt.original()));
        assertThrows(IllegalArgumentException.class,()->new ClockStatusRead(fixture,forged,fixture.archiveForTest()));
        assertEquals(0,fixture.frameReads);assertTrue(fixture.steps.isEmpty());
    }
}
