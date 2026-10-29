package org.xar.ck3.control.application.planning;

import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Text;

/** Original service._route_plan_to_available_step; pure selection DATA, never an action permission. */
public final class OriginalPlanRouting {
    private OriginalPlanRouting() { }
    private static final Set<String> REQUIRED = Set.of("death-terminal", "strategy-review",
            "resolve-current-event", "select-mandatory-choice-v1");
    private static final List<String> REQUIRED_PREFIXES = List.of("declare-war-", "war-declare-",
            "offer-white-peace-", "surrender-war-", "query-war-termination-options-",
            "query-war-termination-terms-v1-", "query-war-termination-exit-terms-v2-",
            "query-combat-simulation-inputs-v2-", "query-combat-simulation-inputs-v3-",
            "query-war-entry-assessments-v1-", "enforce-demands-");

    public static Obj route(Obj original, Set<OperationKey> actualAvailableSteps) {
        Objects.requireNonNull(original); actualAvailableSteps = Set.copyOf(actualAvailableSteps);
        if (!(original.get("selected_step") instanceof Text selected)) return original;
        String step = selected.value();
        if (actualAvailableSteps.stream().anyMatch(available -> available.value().equals(step))) return original;
        if (REQUIRED.contains(step) || REQUIRED_PREFIXES.stream().anyMatch(step::startsWith))
            return original.with("selected_step", OpportunityJson.Nil.INSTANCE)
                    .with("required_step", selected)
                    .with("reason", new Text("selected backend does not implement required step " + step));
        if (actualAvailableSteps.contains(new OperationKey("life-advance")))
            return original.with("phase", new Text("capability_progress"))
                    .with("deferred_phase", original.members().containsKey("phase") ? original.get("phase") : OpportunityJson.Nil.INSTANCE)
                    .with("selected_step", new Text("life-advance"))
                    .with("required_step", selected)
                    .with("reason", new Text("selected backend does not yet implement " + step
                            + "; continue the current life through native events"));
        return original.with("selected_step", OpportunityJson.Nil.INSTANCE)
                .with("required_step", selected)
                .with("reason", new Text("selected backend does not implement gameplay step " + step));
    }
}
