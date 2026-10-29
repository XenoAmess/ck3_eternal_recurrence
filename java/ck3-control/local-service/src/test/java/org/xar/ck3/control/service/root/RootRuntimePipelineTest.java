package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.ExactRef;

/** Scoped composition regressions. These fixtures never grant native, Source or full runtime qualification. */
final class RootRuntimePipelineTest {
    private static final ExactRef SOURCE=new ExactRef("D:/fixture/actual-policy.java",1,"a".repeat(64));
    private static OrdinaryPolicy policy(PlanningStage stage) {
        return new OrdinaryPolicy() {
            @Override public PlanningStage stage(){return stage;}
            @Override public ExactRef implementationSource(){return SOURCE;}
            @Override public Decision evaluate(PlanningRequest original,Draft previous){throw new AssertionError("composition fixture cannot play");}
        };
    }
    private static RootDomainInstallation domain(String id,List<OrdinaryPolicy> actual) {
        return new RootDomainInstallation(id,List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),
                List.of(),List.of(),List.of(),Set.of(),actual,List.of(),List.of(),List.of(),List.of());
    }
    @Test void actualPartialInstallationsCannotConstructTheFullOrdinaryPipeline() {
        var selected=List.of(domain("construction",List.of(policy(PlanningStage.CONSTRUCTION))));
        var missing=RootRuntimePipeline.missing(selected);
        assertFalse(missing.contains(PlanningStage.CONSTRUCTION));assertTrue(missing.contains(PlanningStage.ORDINARY_CORE));
        assertTrue(missing.contains(PlanningStage.REALM_MEMBERSHIP_PUBLICATION));
        assertEquals(PlanningStage.values().length-1,missing.size());
        assertThrows(IllegalArgumentException.class,()->RootRuntimePipeline.assemble(selected));
    }
    @Test void twoActualInstallersCannotSilentlyReplaceOnePlanningStage() {
        var actual=List.of(domain("first",List.of(policy(PlanningStage.CONSTRUCTION))),
                domain("second",List.of(policy(PlanningStage.CONSTRUCTION))));
        assertThrows(IllegalArgumentException.class,()->RootRuntimePipeline.missing(actual));
    }
    @Test void blockedDomainStopsLaterPlanningPublishers() {
        var later=new AtomicInteger();
        OrdinaryPlanCompletion blocked=new OrdinaryPlanCompletion() {
            @Override public PlanningDisposition afterPlanning(PlanningRequest original,PlanningResult planned){return new Blocked("original source unavailable",List.of(SOURCE));}
            @Override public ExecutionDisposition afterExecution(ActionReceipt actual){return new Unchanged("unrelated");}
        };
        OrdinaryPlanCompletion second=new OrdinaryPlanCompletion() {
            @Override public PlanningDisposition afterPlanning(PlanningRequest original,PlanningResult planned){later.incrementAndGet();return new Unchanged("later");}
            @Override public ExecutionDisposition afterExecution(ActionReceipt actual){later.incrementAndGet();return new Unchanged("later");}
        };
        var result=new RootRuntimePipeline.Completion(List.of(blocked,second)).afterPlanning(null,null);
        assertInstanceOf(OrdinaryPlanCompletion.Blocked.class,result);assertEquals(0,later.get());
    }
    @Test void blockedExecutionCannotProceedToAnotherDomainHead() {
        var later=new AtomicInteger();
        OrdinaryPlanCompletion blocked=new OrdinaryPlanCompletion() {
            @Override public PlanningDisposition afterPlanning(PlanningRequest original,PlanningResult planned){return new Unchanged("unrelated");}
            @Override public ExecutionDisposition afterExecution(ActionReceipt actual){return new Blocked("canonical original outcome unavailable",List.of(SOURCE));}
        };
        OrdinaryPlanCompletion second=new OrdinaryPlanCompletion() {
            @Override public PlanningDisposition afterPlanning(PlanningRequest original,PlanningResult planned){return new Unchanged("unrelated");}
            @Override public ExecutionDisposition afterExecution(ActionReceipt actual){later.incrementAndGet();return new Unchanged("later");}
        };
        assertInstanceOf(OrdinaryPlanCompletion.Blocked.class,new RootRuntimePipeline.Completion(List.of(blocked,second)).afterExecution(null));
        assertEquals(0,later.get());
    }
}

