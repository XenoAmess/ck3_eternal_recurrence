package org.xar.ck3.control.application.planning.military;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.advance.LifeAdvanceCommands;
import org.xar.ck3.control.application.checkpoint.CheckpointRequest;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryPlannerSelection;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Shared typed result of actual military collectors. No branch is a native permission. */
public sealed interface MilitaryPlanningDecision permits MilitaryPlanningDecision.Keep,
        MilitaryPlanningDecision.Hold, MilitaryPlanningDecision.Select,
        MilitaryPlanningDecision.Unavailable, MilitaryPlanningDecision.Replan,
        MilitaryPlanningDecision.ApplicationDecision {
    /** A real shared policy (for example the exact legacy exit boundary) already built its command. */
    record ApplicationDecision(OrdinaryPolicy.Decision decision) implements MilitaryPlanningDecision {
        public ApplicationDecision { Objects.requireNonNull(decision); }
    }
    /** Exact original recognized-transition continuation with a shorter owned history view. */
    record Replan(PlanningRequest requestWithTrimmedHistory, OpportunityJson.Obj annotations) implements MilitaryPlanningDecision {
        public Replan { Objects.requireNonNull(requestWithTrimmedHistory); Objects.requireNonNull(annotations); validate(annotations); }
    }
    /** Original input was inapplicable, or no replacement was found after real evaluation. */
    record Keep(OpportunityJson.Obj annotations) implements MilitaryPlanningDecision {
        public Keep { Objects.requireNonNull(annotations); validate(annotations); }
    }
    /** A real original guard selected no world action; retain exact diagnostic and required read. */
    record Hold(String policy, String phase, String reason, Optional<OperationKey> requiredObservation,
                OpportunityJson.Obj detail) implements MilitaryPlanningDecision {
        public Hold {
            StrictJson.text(policy); StrictJson.text(phase); StrictJson.text(reason);
            Objects.requireNonNull(requiredObservation); Objects.requireNonNull(detail); validate(detail);
        }
    }
    record Select(String policy, String phase, String reason, OperationKey operation,
                  OpportunityJson.Obj arguments, OrdinaryPolicy.Purpose purpose,
                  OpportunityJson.Obj detail) implements MilitaryPlanningDecision {
        public Select {
            StrictJson.text(policy); StrictJson.text(phase); StrictJson.text(reason);
            Objects.requireNonNull(operation); Objects.requireNonNull(arguments);
            Objects.requireNonNull(purpose); Objects.requireNonNull(detail);
            validate(arguments); validate(detail);
            OpportunityJson.Value selected=detail.get("selected_step");
            StrictJson.require(selected instanceof OpportunityJson.Text text
                    && operation.value().equals(text.value()), "military selection lost original exact operation");
            StrictJson.require(new OpportunityJson.Text(policy).equals(detail.get("policy"))
                    && new OpportunityJson.Text(phase).equals(detail.get("phase"))
                    && new OpportunityJson.Text(reason).equals(detail.get("reason")),
                    "military selection differs from original complete plan");
        }
    }
    /** Missing code/input/provider is explicit; it must not be disguised as an inapplicable policy. */
    record Unavailable(List<String> missing, String reason) implements MilitaryPlanningDecision {
        public Unavailable {
            missing=List.copyOf(missing); StrictJson.require(!missing.isEmpty(), "exact military dependencies required");
            missing.forEach(StrictJson::text); StrictJson.text(reason);
        }
    }

    /** Installed once by the composition root; shares coordinator expected-observer and claims contracts. */
    @FunctionalInterface interface CommandFactory {
        ActionCommand create(PlanningRequest request, Select selection);
        /** Existing factories retain exact arguments. Enriched families must opt into their strict owner decoder. */
        default PreparedSelection prepare(PlanningRequest request, Select selection) {
            return PreparedSelection.exact(request, selection, Objects.requireNonNull(create(request, selection)));
        }
    }

    /**
     * Custody of the original selection and the one prepared command. This is not
     * permission to submit, proof of preflight validity or evidence of an effect.
     * Only closed owner-specific argument decoders may retain enriched arguments.
     */
    final class PreparedSelection {
        private final PlanningRequest originalRequest;
        private final Select originalSelection;
        private final String originalActionId;
        private final ActionCommand command;

        private PreparedSelection(String actionId, PlanningRequest request, Select selection, ActionCommand actual) {
            StrictJson.text(actionId);
            originalRequest = Objects.requireNonNull(request);
            originalSelection = Objects.requireNonNull(selection);
            originalActionId = actionId;
            command = Objects.requireNonNull(actual);
            requireCommand();
        }

        /** A factory with no enrichment has no intermediate action ID to replace. */
        public static PreparedSelection exact(PlanningRequest request, Select selection, ActionCommand actual) {
            Objects.requireNonNull(actual);
            return exact(actual.actionId(), request, selection, actual);
        }

        public static PreparedSelection exact(String actionId, PlanningRequest request, Select selection, ActionCommand actual) {
            var prepared = new PreparedSelection(actionId, request, selection, actual);
            StrictJson.require(actual.arguments().equals(selection.arguments()),
                    "exact military preparation changed the original selected arguments");
            return prepared;
        }

        /** Rebuild the actual selected public Army call with the single application-layer owner mapper. */
        public static PreparedSelection army(String actionId, PlanningRequest request, Select selection, ActionCommand actual) {
            var prepared = new PreparedSelection(actionId, request, selection, actual);
            ArmyOrdinaryPlannerSelection.requirePrepared(selection.operation(), selection.arguments(),
                    request.before().frame().revision(), ArmyOrdinaryActionArguments.decode(actual.arguments()));
            return prepared;
        }

        /** Reuse the actual Life producer's complete original-plan and deterministic-command checks. */
        public static PreparedSelection life(String actionId, PlanningRequest request, Select selection, ActionCommand actual) {
            var prepared = new PreparedSelection(actionId, request, selection, actual);
            LifeAdvanceCommands.requirePrepared(request, selection.operation(), selection.arguments(), selection.detail(), actual);
            return prepared;
        }

        /** The SAVE owner keeps native arguments empty; the one original postwar history index remains planning DATA. */
        public static PreparedSelection checkpoint(String actionId, PlanningRequest request, Select selection,
                CheckpointRequest actual) {
            Objects.requireNonNull(actual);
            var prepared = new PreparedSelection(actionId, request, selection, actual.saveCommand());
            StrictJson.require(selection.operation().value().equals("save-checkpoint")
                    && selection.purpose() == OrdinaryPolicy.Purpose.WORLD_ACTION
                    && actual.saveCommand().arguments().members().isEmpty(),
                    "checkpoint preparation requires the original SAVE and unchanged empty native arguments");
            var arguments = selection.arguments().members();
            if (arguments.isEmpty()) {
                StrictJson.require(java.util.Set.of("baseline", "periodic_checkpoint", "post_milestone_checkpoint")
                        .contains(selection.phase()), "empty SAVE planning arguments belong to an original checkpoint phase");
            } else {
                StrictJson.require(arguments.keySet().equals(java.util.Set.of("postwar_disband_history_index"))
                        && selection.phase().equals("native_postwar_checkpoint"),
                        "only the original postwar checkpoint planning index may enrich SAVE");
                var index = selection.arguments().get("postwar_disband_history_index");
                StrictJson.require(index instanceof OpportunityJson.IntegerValue integer
                        && integer.value().signum() > 0
                        && integer.value().compareTo(java.math.BigInteger.valueOf(Integer.MAX_VALUE)) <= 0
                        && index.equals(selection.detail().get("postwar_disband_history_index")),
                        "postwar checkpoint index must be the exact positive original plan integer");
            }
            return prepared;
        }

        public ActionCommand command() { return command; }

        /** The ordinary core carries the identical request with its original public arguments and complete plan. */
        public ActionCommand requireOriginalChoice(PlanningRequest request, OperationKey operation,
                OpportunityJson.Obj arguments, OpportunityJson.Obj completePlan) {
            StrictJson.require(request == originalRequest
                    && originalSelection.operation().equals(Objects.requireNonNull(operation))
                    && originalSelection.arguments().equals(Objects.requireNonNull(arguments))
                    && originalSelection.detail().equals(Objects.requireNonNull(completePlan)),
                    "prepared command belongs to a different original core selection or complete plan");
            requireCommand();
            return command;
        }

        private ActionCommand requireOriginal(PlanningRequest request, Select selection) {
            StrictJson.require(request == originalRequest && selection == originalSelection,
                    "prepared military selection belongs to a different original request or choice");
            requireCommand();
            return command;
        }

        private void requireCommand() {
            StrictJson.require(command.actionId().equals(originalActionId)
                    && command.before().equals(originalRequest.before())
                    && command.source().equals(originalRequest.source())
                    && command.sessionId().equals(originalRequest.sessionId())
                    && command.deadline().equals(originalRequest.deadline())
                    && command.operation().equals(originalSelection.operation()),
                    "prepared military command changed the original action ID, frame, source, session, deadline or operation");
        }
    }
    @FunctionalInterface interface ApplicationAdapter {
        OrdinaryPolicy.Decision adapt(PlanningRequest request,OrdinaryPolicy.Draft previous,MilitaryPlanningDecision decision);
    }

    static OrdinaryPolicy.Draft draft(PlanningRequest request, Select selected, CommandFactory factory) {
        Objects.requireNonNull(request); Objects.requireNonNull(selected); Objects.requireNonNull(factory);
        PreparedSelection prepared = Objects.requireNonNull(factory.prepare(request, selected));
        ActionCommand command = prepared.requireOriginal(request, selected);
        return new OrdinaryPolicy.Draft(selected.policy(),selected.phase(),selected.reason(),
                OrdinaryPolicy.Kind.ORDINARY,Optional.of(command),selected.purpose(),
                Optional.of(org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain.war),
                selected.detail());
    }

    private static void validate(OpportunityJson.Obj value) {
        DriverJson.object(DriverJson.encode(value), DriverJson.MAX_NATIVE_BYTES);
    }
}
