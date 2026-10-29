package org.xar.ck3.control.application.battleadvance;

import java.util.Map;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.advance.AdvanceObservationPort.Frame;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual ordinary planner normalization after campaign cap, before display/publication/parent intent. */
public final class BattleAdvanceRewrite {
    private BattleAdvanceRewrite() { }
    public static ActionCommand rewrite(ActionCommand original, Frame actualSourceFrame, BattleAdvancePlan.Configuration configuration) {
        BattleAdvanceFrame.Snapshot source = BattleAdvanceFrame.decode(actualSourceFrame);
        BattleAdvanceFrame.bind(original, source, true);
        BattleAdvanceStep step = BattleAdvanceStep.parse(original.operation().value()).orElseThrow(() -> new IllegalArgumentException("not a migrated tactical sentinel composite"));
        BattleAdvancePlan plan = BattleAdvancePlan.create(step, source, configuration);
        StrictJson.require(original.claims().armyIds().containsAll(plan.watchArmyIds().stream().map(java.math.BigInteger::valueOf).toList()),
                "timeline action must reserve the complete actual controllable watch set");
        return new ActionCommand(original.actionId(), actualSourceFrame.identity(), original.source(), original.sessionId(), original.operation(),
                new OpportunityJson.Obj(Map.of(BattleAdvancePlan.KEY, plan.json())),
                new ProposalLifecycle.ExpectedPostcondition(1, actualSourceFrame.identity(), original.source(), BattleAdvancePlan.OBSERVER, plan.expected()),
                original.claims(), original.deadline());
    }
}
