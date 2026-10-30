package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionIds;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.advance.LifeAdvanceCommands;
import org.xar.ck3.control.application.advance.LifeAdvanceComposite;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.OrdinaryCorePolicy;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.military.CommanderAssignmentPostcondition;
import org.xar.ck3.control.application.planning.military.CommanderBindings;
import org.xar.ck3.control.application.planning.military.MilitaryPlanningDecision;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyCalls;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionService;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryPlannerCalls;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Text;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** Concrete command preparation only. Native submission remains with the sole Root coordinator. */
public final class RootRuntimeCommands implements MilitaryPlanningDecision.CommandFactory, OrdinaryCorePolicy.CommandBinding {
    public static final class CommandUnavailable extends IllegalStateException {
        private static final long serialVersionUID = 1L;
        private final OperationKey operation;
        CommandUnavailable(OperationKey operation, String reason) {
            super("INCOMPLETE_ROOT_COMMAND: " + Objects.requireNonNull(operation).value() + ": " + StrictJson.text(reason));
            this.operation = operation;
        }
        public OperationKey operation() { return operation; }
    }

    private final RootRuntimeContext context;
    private final ArmyOrdinaryActionService army;
    private final LifeAdvanceCommands life;
    private final CommanderBindings commander;
    record Held(PlanningRequest request, OperationKey operation, Obj originalArguments, Obj originalPlan,
            ActionCommand command, Optional<ActionCommand> originalProposal, Optional<CampaignDeadline.Cap> deadlineCap) { }
    private final Map<String, Held> prepared = new LinkedHashMap<>();
    private final Map<String, RootSaveCheckpointCommandProducer.Prepared> checkpointPrepared = new LinkedHashMap<>();

    public RootRuntimeCommands(RootRuntimeContext actualContext, ArmyOrdinaryActionService actualArmy,
            LifeAdvanceCommands sharedLife, CommanderBindings sameCommander) {
        context = Objects.requireNonNull(actualContext); army = Objects.requireNonNull(actualArmy);
        life = Objects.requireNonNull(sharedLife); commander = Objects.requireNonNull(sameCommander);
    }
    public void requireArmy(ArmyOrdinaryActionService actual) {
        StrictJson.require(army == Objects.requireNonNull(actual), "Root commands and the caller must retain the same actual Army service");
    }
    public void requireOwner(RootRuntimeContext actual,LifeAdvanceCommands sharedLife) {
        StrictJson.require(context==Objects.requireNonNull(actual)&&life==Objects.requireNonNull(sharedLife),
                "campaign rewriting must use the identical physical Root and shared Life command producer");
    }
    /** Rebuilds supported deadline-capped selections through their original actual owner, never by editing a strong command. */
    public ActionCommand rewriteDeadline(PlanningRequest request,ActionCommand original,String effectiveStep,
            CampaignDeadline.Cap cap) throws IOException {
        Objects.requireNonNull(request);Objects.requireNonNull(original);Objects.requireNonNull(cap);
        OperationKey operation=new OperationKey(StrictJson.text(effectiveStep));Held retained=held(original.actionId());
        StrictJson.require(retained!=null&&retained.request()==request
                &&java.util.Arrays.equals(ActionCodec.encodeCommand(retained.command()),ActionCodec.encodeCommand(original)),
                "deadline rewriting requires the actual same-request retained original selection");
        if(!LifeAdvanceComposite.accepts(operation.value())||retained.originalProposal().isPresent())
            throw new CommandUnavailable(operation,"deadline-aware bare selection preparation is not implemented by this actual command owner");
        java.math.BigInteger effectiveMaximum=cap.boundaryDateRaw();
        var priorMaximum=retained.originalArguments().get("maximum_target_date_raw");
        if(priorMaximum!=null) {
            StrictJson.require(priorMaximum instanceof org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue,
                    "the original advance maximum must remain its strict integer JSON field");
            effectiveMaximum=effectiveMaximum.min(((org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue)priorMaximum).value());
        }
        var maximum=new org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue(effectiveMaximum);
        Obj args=retained.originalArguments().with("maximum_target_date_raw",maximum);
        Obj plan=retained.originalPlan().with("selected_step",new Text(operation.value())).with("maximum_target_date_raw",maximum);
        var selection=new MilitaryPlanningDecision.Select(text(plan,"policy"),text(plan,"phase"),text(plan,"reason"),
                operation,args,OrdinaryPolicy.Purpose.DATE_ADVANCE,plan);
        String actionId=decisionId(request,selection.operation(),selection.arguments(),selection.detail());
        ActionCommand actual=prepareOnce(request,selection,actionId,Optional.of(cap));
        StrictJson.require(actual.before().equals(original.before())&&actual.source().equals(original.source())
                &&actual.sessionId().equals(original.sessionId())&&actual.claims().equals(original.claims())
                &&actual.deadline().equals(original.deadline()),"actual capped preparation changed original ownership, reservations or deadline");
        return actual;
    }

    /** A missing owner preparation is a migration gap; installing a native handler alone never makes it supported. */
    public boolean supports(OperationKey operation) {
        Objects.requireNonNull(operation);
        return RootSaveCheckpointCommandProducer.supports(operation)
                || LifeAdvanceComposite.accepts(operation.value()) || ArmyOrdinaryPlannerCalls.supports(operation)
                || operation.value().matches("assign-army-commander-v1-army-[1-9][0-9]*-to-character-[0-9]+");
    }

    public List<OperationKey> missingPreparations(List<OperationKey> actualRequiredOperations) {
        return List.copyOf(actualRequiredOperations).stream().filter(operation -> !supports(operation)).distinct().toList();
    }

    @Override public ActionCommand create(PlanningRequest request, MilitaryPlanningDecision.Select selection) {
        return prepare(request, selection).command();
    }

    @Override public MilitaryPlanningDecision.PreparedSelection prepare(PlanningRequest request, MilitaryPlanningDecision.Select selection) {
        Objects.requireNonNull(request); Objects.requireNonNull(selection);
        String actionId = decisionId(request, selection.operation(), selection.arguments(), selection.detail());
        ActionCommand actual = prepareOnce(request, selection, actionId, Optional.empty());
        if (RootSaveCheckpointCommandProducer.supports(selection.operation())) {
            var checkpoint = checkpoint(actionId);
            StrictJson.require(checkpoint.original()==request&&checkpoint.command().equals(actual),
                    "SAVE selection lost its actual original typed checkpoint preparation");
            return MilitaryPlanningDecision.PreparedSelection.checkpoint(actionId,request,selection,checkpoint.request());
        }
        if (LifeAdvanceComposite.accepts(selection.operation().value()))
            return MilitaryPlanningDecision.PreparedSelection.life(actionId, request, selection, actual);
        if (ArmyOrdinaryPlannerCalls.supports(selection.operation()))
            return MilitaryPlanningDecision.PreparedSelection.army(actionId, request, selection, actual);
        return MilitaryPlanningDecision.PreparedSelection.exact(actionId, request, selection, actual);
    }

    @Override public OrdinaryCorePolicy.Bound propose(PlanningRequest request, OperationKey operation, Obj arguments,
            Obj originalPlan, OrdinaryPolicy.Purpose purpose, Optional<Domain> domain) {
        Objects.requireNonNull(purpose); Objects.requireNonNull(domain);
        try {
            var selected = new MilitaryPlanningDecision.Select(text(originalPlan, "policy"), text(originalPlan, "phase"),
                    text(originalPlan, "reason"), operation, arguments, purpose, originalPlan);
            return new OrdinaryCorePolicy.OwnerPrepared(prepare(request, selected));
        } catch (CommandUnavailable unavailable) {
            return new OrdinaryCorePolicy.MissingHandler(unavailable.getMessage());
        }
    }

    /** Only new same-frame proposals reach this method. ReconcileExisting keeps its durable original untouched. */
    public ActionCommand requireActualStrong(PlanningRequest request, ActionCommand proposed) {
        OriginalCommandClocks.requireCurrentProposal(request, proposed);
        try {
            return context.withSession(same -> {
                requireRequest(request);
                requireNewAction(same, proposed.actionId(), proposed.operation());
                Held held = held(proposed.actionId(), request);
                if (held != null) {
                    StrictJson.require(held.request() == request && held.operation().equals(proposed.operation())
                            && (held.command().equals(proposed) || held.originalProposal().filter(proposed::equals).isPresent()),
                            "Root strong preparation cannot replace an existing original selection or its canonical command");
                    ActionCommand actual = held.command();
                    context.collector().currentPlanning(same, request, request.deadline(), (original, lease) -> {
                        var composite = context.bindings().composites().find(actual.operation());
                        if (composite.isPresent()) composite.orElseThrow().validate(actual);
                        else context.bindings().prepare(same, actual, actual.actionId());
                        return null;
                    });
                    return OriginalCommandClocks.requireRebound(request, proposed, actual);
                }
                ActionCommand actual;
                if (LifeAdvanceComposite.accepts(proposed.operation().value())) {
                    actual = context.collector().currentPlanning(same, request, request.deadline(),
                            (original, lease) -> life.prepareExistingProposal(request, proposed));
                } else {
                    actual = dispatch(request, proposed.operation(), proposed.arguments(), proposed.arguments(), proposed.actionId(), Optional.empty());
                }
                OriginalCommandClocks.requireRebound(request, proposed, actual);
                retain(proposed.actionId(), new Held(request, proposed.operation(), proposed.arguments(), proposed.arguments(),
                        actual, Optional.of(proposed), Optional.empty()));
                return actual;
            });
        } catch (IOException failure) {
            throw new UncheckedIOException("actual original strong proposal validation is unavailable; no new action was submitted", failure);
        }
    }

    private ActionCommand prepareOnce(PlanningRequest request, MilitaryPlanningDecision.Select selection, String actionId,
            Optional<CampaignDeadline.Cap> deadlineCap) {
        Objects.requireNonNull(deadlineCap);
        try {
            return context.withSession(same -> {
                requireRequest(request);
                requireNewAction(same, actionId, selection.operation());
                Held held = held(actionId, request);
                if (held != null) {
                    StrictJson.require(held.request() == request && held.operation().equals(selection.operation())
                            && held.originalArguments().equals(selection.arguments()) && held.originalPlan().equals(selection.detail())
                            && held.originalProposal().isEmpty() && held.deadlineCap().equals(deadlineCap),
                            "same decision identity cannot change its original selection, campaign cap or preparation route");
                    return held.command();
                }
                ActionCommand command = dispatch(request, selection.operation(), selection.arguments(), selection.detail(), actionId, deadlineCap);
                retain(actionId, new Held(request, selection.operation(), selection.arguments(), selection.detail(), command, Optional.empty(), deadlineCap));
                return command;
            });
        } catch (IOException failure) {
            throw new UncheckedIOException("actual same-writer preparation retention is unavailable", failure);
        }
    }

    private synchronized Held held(String actionId) { return prepared.get(actionId); }
    private synchronized Held held(String actionId, PlanningRequest request) {
        return currentHeld(actionId, request, prepared, checkpointPrepared);
    }
    static Held currentHeld(String actionId, PlanningRequest request, Map<String, Held> prepared,
            Map<String, RootSaveCheckpointCommandProducer.Prepared> checkpoints) {
        // An equal frame may start a new planning round. Only the actual request owns temporary preparations.
        prepared.entrySet().removeIf(row -> row.getValue().request() != request);
        checkpoints.entrySet().removeIf(row -> row.getValue().original() != request);
        return prepared.get(actionId);
    }
    private synchronized RootSaveCheckpointCommandProducer.Prepared checkpoint(String actionId) {
        var actual=checkpointPrepared.get(actionId);
        StrictJson.require(actual!=null,"original typed checkpoint preparation is unavailable");return actual;
    }
    private synchronized void retainCheckpoint(RootSaveCheckpointCommandProducer.Prepared actual) {
        String id=actual.command().actionId();var old=checkpointPrepared.get(id);
        StrictJson.require(old==null||old==actual,"original typed checkpoint preparation cannot be replaced");
        checkpointPrepared.entrySet().removeIf(row->!row.getValue().original().before().equals(actual.original().before()));
        StrictJson.require(checkpointPrepared.size()<4096||old==actual,"bounded same-frame checkpoint preparations required");
        checkpointPrepared.put(id,actual);
    }
    private synchronized void retain(String actionId, Held held) {
        // This is only transient new-proposal custody. Durable UNKNOWN uses its original canonical journal and never this cache.
        prepared.entrySet().removeIf(row -> !row.getValue().request().before().equals(held.request().before()));
        checkpointPrepared.entrySet().removeIf(row -> !row.getValue().original().before().equals(held.request().before()));
        StrictJson.require(prepared.size() < 4096 && !prepared.containsKey(actionId), "bounded unique same-frame Root preparations required");
        prepared.put(actionId, held);
    }

    private ActionCommand dispatch(PlanningRequest request, OperationKey operation, Obj arguments, Obj completePlan, String actionId,
            Optional<CampaignDeadline.Cap> deadlineCap) {
        StrictJson.require(deadlineCap.isEmpty() || LifeAdvanceComposite.accepts(operation.value()),
                "a typed campaign cap belongs only to its original Life selection");
        Objects.requireNonNull(request); Objects.requireNonNull(operation); Objects.requireNonNull(arguments); Objects.requireNonNull(completePlan);
        if (!supports(operation)) throw new CommandUnavailable(operation, "the actual owner command preparation is absent");
        try {
            return context.withSession(same -> {
                requireRequest(request);
                requireNewAction(same, actionId, operation);
                ActionCommand actual;
                if (RootSaveCheckpointCommandProducer.supports(operation)) {
                    // The factory must open its own original readiness after every held planning callback has unwound.
                    var checkpoint=RootSaveCheckpointCommandProducer.prepare(context,request,actionId);
                    if(!(context.actions() instanceof RootApplicationSession root))throw new IOException("actual Root SAVE owner is absent");
                    root.retainPlannedCheckpoint(checkpoint);retainCheckpoint(checkpoint);actual=checkpoint.command();
                } else actual = context.collector().currentPlanning(same, request, request.deadline(), (original, lease) -> {
                    StrictJson.require(original == request, "Root command preparation replaced the original collector request");
                    if (LifeAdvanceComposite.accepts(operation.value())) {
                        var selected = deadlineCap.isPresent()
                                ? life.prepare(request, operation, arguments, completePlan, deadlineCap.orElseThrow())
                                : life.prepare(request, operation, arguments, completePlan);
                        ActionCommand prepared = selected.orElseThrow(() -> new CommandUnavailable(operation,
                                "the same shared Life composite cannot prepare this current step"));
                        StrictJson.require(prepared.actionId().equals(actionId), "Root Life proposal differs from the sole deterministic Life identity");
                        return prepared;
                    }
                    if (ArmyOrdinaryPlannerCalls.supports(operation)) {
                        var input = ArmyOrdinaryPlannerCalls.decode(operation, arguments, request.before().frame().revision(), actionId);
                        var actualSource = new ArmyTypes.Context(request.before(), request.source(), request.sessionId(), request.deadline());
                        var selected = org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryPlannerSelection.decode(
                                operation, arguments, request.before().frame().revision());
                        return army.preparePlannerCommand(same, input, actualSource, actionId, selected);
                    }
                    var input = CommanderAssignmentPostcondition.arguments(arguments);
                    StrictJson.require(input.step().equals(operation.value()), "Commander operation differs from its actual canonical arguments");
                    return commander.assignment(request, input, context.bindings(), actionId);
                });
                OriginalCommandClocks.requireCurrentProposal(request, actual);
                StrictJson.require(actual.actionId().equals(actionId) && actual.operation().equals(operation),
                        "actual command preparer changed the original decision identity or operation");
                return actual;
            });
        } catch (IOException failure) {
            throw new UncheckedIOException("actual same-writer command preparation is unavailable; no native command was submitted", failure);
        }
    }

    private void requireRequest(PlanningRequest request) throws IOException {
        context.requireCurrent(request.deadline());
        StrictJson.require(request.source().equals(context.source()) && request.sessionId().equals(context.game().sessionId())
                && request.before().machineId().equals(context.game().machineId()) && request.before().game().equals(context.game().generation()),
                "command preparation crossed the retained actual physical Game/source/session");
    }
    private void requireNewAction(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            String actionId, OperationKey operation) throws IOException {
        context.writer().requireSession(same);
        if (org.xar.ck3.control.application.action.ContinuityActionJournal.lookup(same.head().state(), actionId,
                context.archive().withSession(same)).isPresent())
            throw new CommandUnavailable(operation, "an existing canonical intent must reconcile its original command without preparation or replay");
    }

    /** The same recipe is used by LifeAdvanceCommands; the complete original plan participates in intent identity. */
    private static String decisionId(PlanningRequest request, OperationKey operation, Obj arguments, Obj completePlan) {
        Objects.requireNonNull(request); Objects.requireNonNull(operation); Objects.requireNonNull(arguments); Objects.requireNonNull(completePlan);
        if (LifeAdvanceComposite.accepts(operation.value())) return LifeAdvanceCommands.decisionId(request, operation, arguments, completePlan);
        StrictJson.require(new Text(operation.value()).equals(completePlan.get("selected_step")),
                "Root command operation differs from the actual complete selected plan");
        String decision = operation.value() + ":" + ActionCodec.sha256(DriverJson.encode(arguments.with("plan", completePlan)));
        return ActionIds.forDecision(request.sessionId(), request.before(), decision);
    }
    private static String text(Obj originalPlan, String field) {
        StrictJson.require(originalPlan.get(field) instanceof Text, "original complete plan requires text " + field);
        return ((Text) originalPlan.get(field)).value();
    }
}
