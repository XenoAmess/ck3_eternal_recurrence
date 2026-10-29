package org.xar.ck3.control.application.planning.governance;

import java.util.HashSet;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceFixtures.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import static org.xar.ck3.control.application.planning.governance.FeastObservationSupplier.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Original Python ordinary guest-rule review holds. A native primitive permission is not an ordinary policy approval. */
final class OrdinaryFeastGuestRuleHoldTest {
    private static final OperationKey ACTIVATE=new OperationKey("activate-activity-feast-guest-rule-v1");
    private static final class UnexpectedReads implements FeastObservationSupplier {
        private AssertionError unexpected(){return new AssertionError("a rule permission must not start ordinary Feast reads or activation");}
        @Override public Read<State> state(PlanningRequest request){throw unexpected();}
        @Override public Read<Planner> planner(PlanningRequest request){throw unexpected();}
        @Override public Read<Hosted> hosted(PlanningRequest request){throw unexpected();}
        @Override public Read<Obj> root(PlanningRequest request){throw unexpected();}
        @Override public Read<OrdinaryFinanceCollector.Spending> spending(PlanningRequest request){throw unexpected();}
        @Override public Read<OrdinaryFinanceCollector.Feast> feast(PlanningRequest request,OrdinaryFinanceCollector.Spending spending){throw unexpected();}
    }
    @Test void registeredNativeActivationCannotMintAnOrdinaryPlanOrPassItsSubmissionRevalidation() {
        var original=request();var old=original.observations();var actions=new HashSet<>(old.actionSteps());actions.add(ACTIVATE);
        var observation=new PlanningObservation(old.snapshot(),old.history(),actions,old.bridgeCapabilities(),old.battleSpeedReadiness(),
                old.actionFacts(),old.campaignGoal(),old.crossRunPlan(),old.initialLifestyleFocusRequired());
        var request=new PlanningRequest(original.before(),original.source(),original.sessionId(),original.deadline(),observation);
        var policy=new OrdinaryFeastPolicy(REF,new UnexpectedReads(),(operation,current,arguments)->{throw new AssertionError("rule hold must not fabricate material effects");});
        var previous=advance(request);
        assertInstanceOf(OrdinaryPolicy.NotApplicable.class,policy.evaluate(request,previous));
        var advance=previous.command().orElseThrow();
        var forged=new ActionCommand("synthetic-rule-approval",request.before(),request.source(),request.sessionId(),ACTIVATE,
                new Obj(java.util.Map.of()).with("policy_approved",new Bool(true)),advance.expected(),advance.claims(),request.deadline());
        assertThrows(IllegalArgumentException.class,()->policy.revalidate(forged,request));
        assertEquals("life-advance",previous.command().orElseThrow().operation().value());
    }
}
