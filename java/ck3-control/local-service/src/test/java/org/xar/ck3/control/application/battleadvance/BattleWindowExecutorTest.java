package org.xar.ck3.control.application.battleadvance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.battleadvance.BattleAdvanceFixture.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.AdvanceObservationPort.Frame;
import org.xar.ck3.control.application.routecontact.RouteContactSteps;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Mode;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;
import org.xar.ck3.control.service.root.RootBattleAdvancePublicResult;

/** Same production engine and codec against explicit scripted DATA. No physical/canonical Root qualification. */
final class BattleWindowExecutorTest {
    private static Frame peaceful(int revision,int date) {
        Frame original=frame(revision,date,true,false);
        String json=new String(OpportunityJson.encode(original.semantic()),StandardCharsets.UTF_8)
                .replace("\"army_state\":\"combat\"","\"army_state\":\"regular\"")
                .replace("\"army_state_code\":2","\"army_state_code\":1")
                .replace("\"in_combat\":true","\"in_combat\":false")
                .replace("\"combat_id\":281474976710657","\"combat_id\":-1");
        return new Frame(original.identity(),original.source(),original.sessionId(),OpportunityJson.object(OpportunityJson.parse(json.getBytes(StandardCharsets.UTF_8)),"scripted unit frame"),
                original.provenance(),original.observedAt(),original.originalEvidence());
    }
    private static Status terminal(Status base) {
        return new Status(base.state(),base.generation(),100,148,base.state()==org.xar.ck3.control.reconciliation.LateOutcome.State.ARMED?100:148,
                base.state()==org.xar.ck3.control.reconciliation.LateOutcome.State.ARMED?0:148,3,Mode.TERMINAL_OR_SENTINEL,
                base.armyCount(),base.combatCount(),base.state()==org.xar.ck3.control.reconciliation.LateOutcome.State.ARMED?0:2,base.intermediatePauseCount(),base.triggerFlags(),base.triggerReasons(),
                base.signedDateDeltaFromTargetRaw(),base.overshootDays(),base.pauseWrapperCalled(),base.pauseObserved(),base.terminalObserved(),base.abnormal());
    }
    @Test void windowOnlyViewUsesOneActualEngineAndOriginalReportWithoutAReconciliationProvider() throws Exception {
        var fixture=new BattleAdvanceFixture();Frame start=peaceful(1,100);
        fixture.frames.addAll(List.of(peaceful(2,100),peaceful(3,100),peaceful(4,148),peaceful(5,148)));
        fixture.statusReads.addAll(List.of(terminal(armed()),terminal(stopped())));
        var base=parent();String step=RouteContactSteps.format(new RouteContactSteps.Request(0,7,List.of(1),2),RouteContactSteps.WINDOW);
        var command=new ActionCommand(base.actionId(),start.identity(),base.source(),base.sessionId(),new OperationKey(step),
                new OpportunityJson.Obj(Map.of()),base.expected(),base.claims(),base.deadline());
        var outcome=fixture.windowExecutor().executeWindow(command,fixture,start,new BattleAdvanceComposite.WindowRequest(List.of(0),148,3));
        assertEquals(2,outcome.elapsedDays());assertEquals(Mode.TERMINAL_OR_SENTINEL,outcome.plan().mode());
        assertEquals(1,fixture.steps.stream().filter("resume-map"::equals).count());assertEquals(2,fixture.children.size());
        var report=BattleAdvanceResultCodec.completed(outcome);
        var encoded=RootBattleAdvancePublicResult.encodeClockReport(report,command.operation());
        assertEquals(OpportunityJson.parse(report.bytes()),OpportunityJson.parse(RootBattleAdvancePublicResult.decodeClockReport(encoded,command.operation()).bytes()));
        assertFalse(fixture.windowExecutor() instanceof CompositeActionPort);
    }
}
