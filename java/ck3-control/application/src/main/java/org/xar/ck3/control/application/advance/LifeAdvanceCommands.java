package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionIds;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.family.FamilyPorts;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Text;

/** One ordinary/family/military date-command producer over the actual shared Life composite. */
public final class LifeAdvanceCommands implements FamilyPorts.Commands {
    private final LifeAdvanceComposite shared;
    private final Optional<PendingUiLifeAdvance.Scope> pendingUi;
    public LifeAdvanceCommands(LifeAdvanceComposite shared) { this.shared = Objects.requireNonNull(shared); pendingUi = Optional.empty(); }
    public LifeAdvanceCommands(LifeAdvanceComposite shared, PendingUiLifeAdvance.Scope actualPendingUi) {
        this.shared = Objects.requireNonNull(shared); pendingUi = Optional.of(Objects.requireNonNull(actualPendingUi));
    }

    /** DATA preparation for the registered private continuation source; no ordinary PlanningRequest or Ready.
     * The caller retains the canonical next child ID and actual once intent. The coordinator independently
     * verifies its private DATE token, original Continue ancestry and exact command before dispatch.
     */
    public ActionCommand preparePendingUiDateAdvance(PendingUiLifeAdvance.Source source, String actualChildId,
            java.time.Instant deadline) throws java.io.IOException {
        Objects.requireNonNull(source); Objects.requireNonNull(deadline);
        org.xar.ck3.control.contracts.StrictJson.text(actualChildId);
        ActionCommand ancestor = Objects.requireNonNull(source.originalParent());
        require(ancestor.origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.LifecycleTerminal
                && ancestor.lifecycleExpected().operation() == org.xar.ck3.control.application.action.LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR,
                "private date producer needs the source's original successor Continue ancestor");
        PendingUiLifeAdvance.Scope scope = pendingUi.orElseThrow(() -> new IllegalStateException("this ordinary-only Life producer has no actual pending source scope"));
        return scope.capture(source, deadline, actual -> {
            var frame = actual.originalFrame();
            require(frame.source().equals(ancestor.source()) && frame.sessionId().equals(ancestor.sessionId())
                    && frame.identity().game().equals(ancestor.origin().game()) && deadline.isAfter(frame.observedAt()),
                    "pending date child left the actual private source Game/session or fresh deadline");
            require(ClockStatusRead.available(actual.actualBridgeCapabilities()), "private one-day purpose needs the actual native Arm/Status/Cancel capability");
            var start = frame.identity().frame().identity().dateRaw();
            var plan = new AdvancePlan(start, start.add(AdvancePlan.DAY), 1, 1, PendingUiLifeAdvance.POLICY,
                    true, AdvancePlan.ClockMode.EXACT_SENTINEL, Optional.empty(), Optional.empty());
            var expected = new ExpectedPostcondition(ProposalLifecycle.POSTCONDITION_VERSION, frame.identity(), frame.source(), AdvancePlan.OBSERVER, plan.expected());
            var actualCommand = new ActionCommand(actualChildId, frame.identity(), frame.source(), frame.sessionId(), new OperationKey("life-advance"),
                    new Obj(java.util.Map.of(AdvancePlan.KEY, plan.json())), expected, new Claims(Set.of(), Set.of(), Set.of(), Set.of()), deadline);
            PendingUiLifeAdvance.requirePurpose(actualCommand);
            AdvanceReadiness.verify(actualCommand, frame, plan, PendingUiLifeAdvance.facts(actualCommand, actual));
            require(!AdvancePolicy.present(frame.semantic().get("active_event")) && !AdvancePolicy.present(frame.semantic().get("pending_character_interaction"))
                    && !AdvancePolicy.modalPresent(frame.semantic()) && !AdvancePolicy.present(frame.semantic().get("one_life_terminal_reason")),
                    "private date preparation must consume the actual cleared living foreground boundary");
            return actualCommand;
        });
    }

    /** Existing owned proposals retain their caller's original identity and claims.
     * Root must establish their source custody before calling; this never mints
     * an ordinary selected-command token or substitutes for actual dispatch.
     */
    public ActionCommand prepareExistingProposal(PlanningRequest request, ActionCommand original) {
        Objects.requireNonNull(request); Objects.requireNonNull(original);
        require(LifeAdvanceComposite.accepts(original.operation().value())
                && request.observations().actionSteps().contains(original.operation())
                && original.before().equals(request.before()) && original.source().equals(request.source())
                && original.sessionId().equals(request.sessionId()) && !original.deadline().isAfter(request.deadline()),
                "existing life proposal crossed the actual planning origin or available operation");
        ActionCommand actual=shared.prepare(request,original);
        AdvancePlan plan=AdvancePlan.decode(actual);
        require(actual.actionId().equals(original.actionId()) && actual.origin().equals(original.origin())
                && actual.source().equals(original.source()) && actual.sessionId().equals(original.sessionId())
                && actual.operation().equals(original.operation()) && actual.claims().equals(original.claims())
                && actual.deadline().equals(original.deadline())
                && actual.arguments().equals(original.arguments().with(AdvancePlan.KEY,plan.json()))
                && plan.startingDateRaw().equals(request.before().frame().identity().dateRaw())
                && (!actual.operation().value().equals("life-advance-one-day") || plan.exactOneDay())
                && actual.expected().observerSchema().equals(AdvancePlan.OBSERVER)
                && actual.expected().values().equals(plan.expected()),
                "shared life readiness changed the existing proposal custody or omitted its actual clock plan");
        return actual;
    }

    /** Prepare one explicitly requested public Life step using the caller's canonical action identity.
     * The same shared producer derives its actual readiness, bounded clock plan and expected result.
     * Public request parsing and the sole coordinator retain source/once-dispatch authority.
     */
    public ActionCommand preparePublic(PlanningRequest request, OperationKey operation, String actualActionId) {
        Objects.requireNonNull(request); Objects.requireNonNull(operation);
        org.xar.ck3.control.contracts.StrictJson.text(actualActionId);
        require(LifeAdvanceComposite.accepts(operation.value()) && request.observations().actionSteps().contains(operation),
                "public Life request needs its exact actual installed and observed Life operation");
        var provisional = new ExpectedPostcondition(ProposalLifecycle.POSTCONDITION_VERSION, request.before(), request.source(), AdvancePlan.OBSERVER,
                List.of(new ExpectedBoolean(new FieldKey("paused"), true)));
        var seed = new ActionCommand(actualActionId, request.before(), request.source(), request.sessionId(), operation,
                new Obj(java.util.Map.of()), provisional, new Claims(Set.of(), Set.of(), Set.of(), Set.of()), request.deadline());
        return prepareExistingProposal(request, seed);
    }

    /** The temporary intent below is never submitted; shared.prepare installs the actual frame-bound plan and expected result. */
    @Override public Optional<ActionCommand> prepare(PlanningRequest request, OperationKey operation, Obj arguments, Obj completePlan) {
        return prepare(request, operation, arguments, completePlan, Optional.empty());
    }
    /** The actual campaign owner supplies its derived cap separately from selected JSON arguments. */
    public Optional<ActionCommand> prepare(PlanningRequest request, OperationKey operation, Obj arguments, Obj completePlan,
            CampaignDeadline.Cap actualCap) {
        return prepare(request, operation, arguments, completePlan, Optional.of(Objects.requireNonNull(actualCap)));
    }
    private Optional<ActionCommand> prepare(PlanningRequest request, OperationKey operation, Obj arguments, Obj completePlan,
            Optional<CampaignDeadline.Cap> actualCap) {
        Objects.requireNonNull(request); Objects.requireNonNull(operation); Objects.requireNonNull(arguments); Objects.requireNonNull(completePlan);
        Objects.requireNonNull(actualCap);
        if (!LifeAdvanceComposite.accepts(operation.value()) || !request.observations().actionSteps().contains(operation)) return Optional.empty();
        require(new Text(operation.value()).equals(completePlan.get("selected_step")), "life command differs from the actual selected planning step");
        require(!arguments.members().containsKey(AdvancePlan.KEY) && !arguments.members().containsKey("plan"), "only the shared Life producer may create the selected and native clock plan");
        if (actualCap.isPresent() && !ClockStatusRead.available(request.observations().bridgeCapabilities())) return Optional.empty();
        Obj payload = arguments.with("plan",completePlan);
        var provisional = new ExpectedPostcondition(ProposalLifecycle.POSTCONDITION_VERSION,request.before(),request.source(),AdvancePlan.OBSERVER,
                List.of(new ExpectedBoolean(new FieldKey("paused"),true)));
        // A date command reserves no money, characters, alliance or commitment. All
        // native children retain these exact claims under the sole coordinator.
        var seed = new ActionCommand(decisionId(request,operation,arguments,completePlan),request.before(),request.source(),request.sessionId(),
                operation,payload,provisional,new Claims(Set.of(),Set.of(),Set.of(),Set.of()),request.deadline());
        ActionCommand actual = actualCap.isPresent()
                ? shared.rewrite(request, seed, operation.value(), actualCap.orElseThrow())
                : shared.prepare(request, seed);
        require(actual.actionId().equals(seed.actionId()) && actual.before().equals(request.before()) && actual.source().equals(request.source())
                && actual.sessionId().equals(request.sessionId()) && actual.operation().equals(operation) && actual.claims().equals(seed.claims())
                && actual.deadline().equals(seed.deadline()) && actual.expected().observerSchema().equals(AdvancePlan.OBSERVER)
                && actual.expected().values().equals(AdvancePlan.decode(actual).expected()), "shared Life preparation changed original command custody or omitted its actual native plan");
        requirePrepared(request,operation,arguments,completePlan,actual);
        return Optional.of(actual);
    }

    /** The Root and this producer share one deterministic identity recipe before command preparation. */
    public static String decisionId(PlanningRequest request, OperationKey operation, Obj selectedArguments, Obj selectedDetail) {
        Objects.requireNonNull(request); Objects.requireNonNull(operation); Objects.requireNonNull(selectedArguments); Objects.requireNonNull(selectedDetail);
        require(LifeAdvanceComposite.accepts(operation.value()) && request.observations().actionSteps().contains(operation)
                && new Text(operation.value()).equals(selectedDetail.get("selected_step"))
                && !selectedArguments.members().containsKey(AdvancePlan.KEY) && !selectedArguments.members().containsKey("plan"),
                "life identity needs its actual unmodified selected ancestor");
        String decision = operation.value() + ":" + ActionCodec.sha256(DriverJson.encode(selectedArguments.with("plan",selectedDetail)));
        return ActionIds.forDecision(request.sessionId(),request.before(),decision);
    }

    /** Pure planner boundary for this producer's only permitted enrichment.
     * Readiness and current Native admission remain the actual composite's responsibility.
     */
    public static void requirePrepared(PlanningRequest request, OperationKey operation,
            Obj selectedArguments, Obj selectedDetail, ActionCommand actual) {
        Objects.requireNonNull(request); Objects.requireNonNull(operation); Objects.requireNonNull(selectedArguments);
        Objects.requireNonNull(selectedDetail); Objects.requireNonNull(actual);
        require(LifeAdvanceComposite.accepts(operation.value()) && request.observations().actionSteps().contains(operation),
                "selected life operation is unavailable in the original request");
        require(new Text(operation.value()).equals(selectedDetail.get("selected_step"))
                && !selectedArguments.members().containsKey(AdvancePlan.KEY) && !selectedArguments.members().containsKey("plan"), "selected life ancestor already contains a selected/native plan or another step");
        Obj ancestor = selectedArguments.with("plan",selectedDetail);
        AdvancePlan plan = AdvancePlan.decode(actual);
        require(actual.arguments().equals(ancestor.with(AdvancePlan.KEY,plan.json())),
                "prepared life arguments changed the exact selected ancestor or canonical plan encoding");
        require(plan.startingDateRaw().equals(request.before().frame().identity().dateRaw())
                && (!operation.value().equals("life-advance-one-day") || plan.exactOneDay()),
                "prepared life plan crossed the actual starting date or exact-day operation");
        require(actual.actionId().equals(decisionId(request,operation,selectedArguments,selectedDetail))
                && actual.before().equals(request.before()) && actual.source().equals(request.source())
                && actual.sessionId().equals(request.sessionId()) && actual.operation().equals(operation)
                && actual.deadline().equals(request.deadline())
                && actual.claims().equals(new Claims(Set.of(),Set.of(),Set.of(),Set.of()))
                && actual.expected().observerSchema().equals(AdvancePlan.OBSERVER)
                && actual.expected().values().equals(plan.expected()), "prepared life command changed its actual original custody or expected plan");
    }
}
