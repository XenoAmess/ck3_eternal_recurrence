package org.xar.ck3.control.wave2.events.choiceplanning;

/** Existing ordinary-planner consumer port. This interface has no submission capability. */
@FunctionalInterface
public interface ChoicePlanningPort {
    ChoicePlanningModel.PlanningResult plan(ChoicePlanningModel.PlanningInput input);
}
