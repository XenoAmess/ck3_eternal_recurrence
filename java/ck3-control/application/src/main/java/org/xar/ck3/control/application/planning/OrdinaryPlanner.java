package org.xar.ck3.control.application.planning;

import java.time.Clock;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmCompletion;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import static org.xar.ck3.control.application.planning.OrdinaryPolicy.*;
import static org.xar.ck3.control.application.planning.PlanTrace.*;
import static org.xar.ck3.control.application.planning.PlanningResult.*;

/**
 * Single ordinary application planner. Domain implementations are the actual
 * Java collectors/policies, not Python callbacks or research HTTP projections.
 * This class never submits, settles, writes a ledger or promotes an ACK.
 */
public final class OrdinaryPlanner {
    private final EnumMap<PlanningStage, OrdinaryPolicy> policies;
    private final Clock clock;
    private final RealmLifecycle realmLifecycle;
    private volatile OrdinaryDecisionSelector selector;
    private volatile boolean m5JointPeacetimeEnabled = true;

    /** One per-Game provider is shared by both actual planner factories. */
    public synchronized void bindSelector(OrdinaryDecisionSelector actual) {
        Objects.requireNonNull(actual);
        StrictJson.require(selector == null, "ordinary decision selector already bound");
        selector = actual;
    }

    public synchronized void setM5JointPeacetimeEnabled(boolean actual) {
        m5JointPeacetimeEnabled = actual;
    }

    public OrdinaryPlanner(List<OrdinaryPolicy> implementations, Clock clock, RealmLifecycle realmLifecycle) {
        Objects.requireNonNull(implementations); this.clock = Objects.requireNonNull(clock);
        this.realmLifecycle = Objects.requireNonNull(realmLifecycle);
        policies = new EnumMap<>(PlanningStage.class);
        for (OrdinaryPolicy policy : implementations) {
            Objects.requireNonNull(policy); Objects.requireNonNull(policy.stage());

            StrictJson.require(policy.stage() != PlanningStage.REALM_MEMBERSHIP_PUBLICATION || policy == realmLifecycle,
                    "realm publication must use the exact planner lifecycle instance");
            StrictJson.require(policies.putIfAbsent(policy.stage(), policy) == null, "one ordinary producer per stage");
        }
    }

    public List<PlanningStage> missingStages() {
        return java.util.Arrays.stream(PlanningStage.values()).filter(stage -> !policies.containsKey(stage)).toList();
    }

    /** Consume the original publication slot once for every authoritative outcome, including UNKNOWN. */
    public RealmCompletion afterExecution(ActionReceipt receipt) {
        return realmLifecycle.afterExecution(Objects.requireNonNull(receipt));
    }

    public PlanningResult plan(PlanningRequest request) {
        return planScoped(request, Optional.empty());
    }

    /** The ordinary Controller publishes its real preparatory READs before asking the online selector. */
    public PlanningResult plan(PlanningRequest request, OrdinaryPlanCompletion completion) {
        return planScoped(request, Optional.empty(), Optional.of(Objects.requireNonNull(completion)));
    }

    /** One fresh continuation after actual optional Sway work; all other ordinary producers still run. */
    public PlanningResult planAfterOptional(PlanningRequest fresh, PlanningStage completedOptional) {
        StrictJson.require(completedOptional == PlanningStage.ORDINARY_SWAY,
                "only the completed optional Sway stage may be suppressed for this one fresh continuation");
        return planScoped(fresh, Optional.of(completedOptional));
    }

    private PlanningResult planScoped(PlanningRequest request, Optional<PlanningStage> completedOptional) {
        return planScoped(request, completedOptional, Optional.empty());
    }

    private PlanningResult planScoped(PlanningRequest request, Optional<PlanningStage> completedOptional,
            Optional<OrdinaryPlanCompletion> completion) {
        Objects.requireNonNull(request);
        RealmLifecycle.Scope scope = realmLifecycle.begin(request);
        try {
            PlanningResult result = planBound(request, completedOptional);
            if (result instanceof ActionSelected selected) {
                Optional<OrdinaryPlanCompletion.Published> published = completion.flatMap(value -> value.beforeSelection(request, selected));
                if (published.isPresent()) {
                    Draft original = selected.trace().finalPlan().orElseThrow();
                    String reason = "actual_read_publication_requires_current_proposal";
                    Draft deferred = new Draft(original.policy(), original.phase(), reason, original.kind(), Optional.empty(),
                            Purpose.READ_ONLY, original.domain(), original.detail());
                    result = new RefreshRequired(request.before(), reason,
                            new PlanTrace(request.before(), selected.trace().visits(), Optional.of(deferred)));
                } else if (selector != null) result = selectProposal(request, selected);
            }
            realmLifecycle.finalizePlan(scope, result);
            return result;
        } catch (RuntimeException | Error failure) {
            try { realmLifecycle.cancel(scope); }
            catch (RuntimeException | Error cancellation) { failure.addSuppressed(cancellation); }
            throw failure;
        }
    }

    private PlanningResult selectProposal(PlanningRequest request, ActionSelected proposed) {
        OrdinaryDecisionSelector.Selection selection;
        try { selection = Objects.requireNonNull(selector.select(request, proposed)); }
        catch (RuntimeException failure) {
            selection = new OrdinaryDecisionSelector.Selection(OrdinaryDecisionSelector.Choice.WAIT,
                    "model_provider_failure:" + failure.getClass().getSimpleName(), Optional.empty());
        }
        List<StageVisit> visits = new ArrayList<>(proposed.trace().visits());
        if (selection.evidence().isPresent() && !visits.isEmpty()) {
            int last = visits.size() - 1;
            StageVisit visit = visits.get(last);
            org.xar.ck3.control.contracts.ExactRef ref = selection.evidence().orElseThrow();
            org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj evidence = visit.evidence()
                    .orElseGet(() -> new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of()));
            evidence = evidence.with("model_decision_receipt", new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(
                    java.util.Map.of("path", new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text(ref.path()),
                    "bytes", new org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue(java.math.BigInteger.valueOf(ref.bytes())),
                    "sha256", new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text(ref.sha256()))));
            visits.set(last, new StageVisit(visit.stage(), visit.outcome(), visit.reason(), visit.source(), Optional.of(evidence)));
        }
        Draft original = proposed.trace().finalPlan().orElseThrow();
        if (selection.choice() == OrdinaryDecisionSelector.Choice.ACCEPT
                && clock.instant().isBefore(request.deadline()) && clock.instant().isBefore(proposed.command().deadline()))
            return new ActionSelected(proposed.command(), new PlanTrace(proposed.trace().before(), visits, Optional.of(original)));
        String reason = selection.choice() == OrdinaryDecisionSelector.Choice.ACCEPT
                ? "model_decision_original_command_deadline_expired" : selection.reason();
        Draft waiting = new Draft(original.policy(), original.phase(), reason, original.kind(), Optional.empty(),
                Purpose.READ_ONLY, original.domain(), original.detail());
        return new ReadOnlyWait(request.before(), reason, new PlanTrace(proposed.trace().before(), visits, Optional.of(waiting)));
    }

    private PlanningResult planBound(PlanningRequest request, Optional<PlanningStage> completedOptional) {
        List<StageVisit> visits = new ArrayList<>();
        List<PlanningStage> missing = missingStages();
        if (!missing.isEmpty()) {
            for (PlanningStage stage : missing) visits.add(new StageVisit(stage, Outcome.MISSING_PRODUCER,
                    "the actual Java ordinary producer is not installed", Optional.empty(), Optional.empty()));
            return new IncompleteMigration(request.before(), missing, new PlanTrace(request.before(), visits, Optional.empty()));
        }
        State state = new State(request, visits, completedOptional);
        state.run(PlanningStage.SUCCESSION_PREFLIGHT);
        state.run(PlanningStage.PENDING_MATERIAL_PUBLICATION);
        state.run(PlanningStage.TERMINAL_AND_FOREGROUND_WINDOWS);
        if (state.result != null) return state.result;

        // Foreground work and independent due material reads retain their original priority.
        if (state.draft.kind() == Kind.FOREGROUND || state.draft.kind() == Kind.MATERIAL_RECEIPT
                || state.draft.kind() == Kind.TERMINAL) return finish(state);
        if (request.observations().initialLifestyleFocusRequired()) {
            state.run(PlanningStage.OPENING_LIFESTYLE_FOCUS);
            return finish(state);
        }

        // The formal exit producer runs before the ordinary tactical chooser. Its
        // guarded continue output is retained by that chooser's own current-frame adapter.
        state.run(PlanningStage.THREE_WAY_WAR_EXIT);
        if (state.result != null) return state.result;
        if (state.draft.kind() == Kind.WAR_EXIT) return finish(state);
        for (PlanningStage stage : List.of(
                PlanningStage.ORDINARY_CORE,
                PlanningStage.EVENT_AND_INTERACTION_CONTINUATION,
                PlanningStage.WAR_RENDEZVOUS,
                PlanningStage.SIEGE_AND_BATTLE_FORECAST,
                PlanningStage.ROUTE_ORIGIN_EXPOSURE,
                PlanningStage.ACTIVE_COMBAT_AND_DATE_GUARDS,
                PlanningStage.ORDINARY_RETREAT,
                PlanningStage.WAR_MERCENARY_CURRENT_CASH,
                PlanningStage.PRISONER_RELEASE_DISCOVERY,
                PlanningStage.HOLY_ORDER_REINFORCEMENT,
                PlanningStage.COMMANDER_QUALITY,
                PlanningStage.M5_JOINT_PEACETIME,
                PlanningStage.LIFESTYLE,
                PlanningStage.FACTION_GIFT,
                PlanningStage.CONSTRUCTION,
                PlanningStage.FAMILY_AND_EDUCATION,
                PlanningStage.PRISONER_RANSOM,
                PlanningStage.PRISONER_RELEASE,
                PlanningStage.M5_WARTIME_OBSERVATION,
                PlanningStage.COUNCIL,
                PlanningStage.CROWN_AUTHORITY,
                PlanningStage.FEAST)) state.run(stage);
        return finish(state);
    }

    private PlanningResult finish(State state) {
        if (state.result != null) return state.result;
        // An early selected war exit still needs the same read-only wartime risk
        // annotation. Keep its original position on the complete ordinary path
        // and let the policy itself decide whether this frame is in scope.
        if (state.visits.stream().noneMatch(visit -> visit.stage() == PlanningStage.M5_WARTIME_OBSERVATION))
            state.run(PlanningStage.M5_WARTIME_OBSERVATION);
        for (PlanningStage stage : List.of(PlanningStage.DEFERRED_SUCCESSION_ROOT,
                PlanningStage.HOLY_WAR_DEFENDER_OBSERVATION, PlanningStage.PREWAR_FORCE_COALITION,
                PlanningStage.ORDINARY_SWAY, PlanningStage.EVENT_MATERIAL_POSTCONDITION,
                PlanningStage.CAMPAIGN_ADVANCE_CAP, PlanningStage.REALM_MEMBERSHIP_PUBLICATION)) state.run(stage);
        if (state.result != null) return state.result;
        if (state.draft.command().isEmpty()) return new ReadOnlyWait(state.request.before(), state.draft.reason(), state.trace());
        ActionCommand command = state.draft.command().orElseThrow();
        if (!clock.instant().isBefore(command.deadline())) return state.stop(StopReason.DEADLINE, "selected action deadline expired during planning");
        if (!state.request.observations().actionSteps().contains(command.operation()))
            return state.stop(StopReason.UNSUPPORTED_ACTION, "selected operation is not routable in the current native capability set");
        Optional<ProposalLifecycle.ExternalFact> same = state.request.observations().actionFacts().stream()
                .filter(fact -> fact.actionId().equals(command.actionId())).findFirst();
        if (same.isPresent()) {
            String actual = ActionCodec.bodySha256(command);
            StrictJson.require(actual.equals(same.orElseThrow().bodySha256()), "same action ID has a different exact body");
            if (same.orElseThrow().unresolved())
                return state.stop(StopReason.UNKNOWN_ACTION_UNRESOLVED, "the action is already recorded; only the sole authority may reconcile it");
            return new ReadOnlyWait(state.request.before(), "the exact action already has a recorded terminal outcome: "
                    + same.orElseThrow().state().name() + "; do not submit it again", state.trace());
        }
        boolean blocked = state.request.observations().actionFacts().stream().filter(ProposalLifecycle.ExternalFact::unresolved)
                .anyMatch(fact -> fact.scope() == ProposalLifecycle.UnknownScope.GLOBAL
                        || fact.scope() == ProposalLifecycle.UnknownScope.DOMAIN && state.draft.domain().filter(fact.domain()::equals).isPresent()
                        || fact.affectedClaims().overlaps(command.claims()));
        if (blocked && state.draft.purpose() != Purpose.READ_ONLY)
            return state.stop(StopReason.UNKNOWN_ACTION_UNRESOLVED, "an unresolved authoritative action overlaps this new action");
        return new ActionSelected(command, state.trace());
    }

    private final class State {
        private final PlanningRequest request;
        private final List<StageVisit> visits;
        private final Optional<PlanningStage> completedOptional;
        private Draft draft = Draft.empty();
        private PlanningResult result;
        private State(PlanningRequest request, List<StageVisit> visits, Optional<PlanningStage> completedOptional) {
            this.request = request; this.visits = visits; this.completedOptional = completedOptional;
        }
        private PlanTrace trace() { return new PlanTrace(request.before(), visits, Optional.of(draft)); }
        private Stopped stop(StopReason reason, String detail) { return new Stopped(request.before(), reason, detail, trace()); }
        private void run(PlanningStage stage) {
            if (result != null) return;
            if (!clock.instant().isBefore(request.deadline())) { result = stop(StopReason.DEADLINE, "ordinary planning deadline expired"); return; }
            if (stage == PlanningStage.M5_JOINT_PEACETIME && !m5JointPeacetimeEnabled) {
                visits.add(new StageVisit(stage, Outcome.NOT_APPLICABLE, "m5_joint_peacetime_enabled=false", Optional.empty(), Optional.empty()));
                return;
            }
            OrdinaryPolicy policy = policies.get(stage);
            if (completedOptional.filter(stage::equals).isPresent()) {
                visits.add(visit(policy, Outcome.NOT_APPLICABLE,
                        "this optional stage already completed before the actual fresh ordinary continuation"));
                return;
            }
            Decision decision = Objects.requireNonNull(policy.evaluate(request, draft), "typed Java policy result required");
            Outcome outcome;
            switch (decision) {
                case Keep ignored -> outcome = Outcome.KEPT;
                case NotApplicable ignored -> outcome = Outcome.NOT_APPLICABLE;
                case Annotate annotation -> {
                    Draft retained = annotation.retained();
                    StrictJson.require(retained.command().equals(draft.command()) && retained.kind() == draft.kind()
                            && retained.purpose() == draft.purpose() && retained.domain().equals(draft.domain())
                            && retained.policy().equals(draft.policy()) && retained.phase().equals(draft.phase())
                            && retained.reason().equals(draft.reason()), "annotation may only update retained plan detail");
                    draft = retained; outcome = Outcome.KEPT;
                }
                case ReconcileExisting reconcile -> {
                    visits.add(visit(policy, Outcome.BLOCKED, reconcile.reason()));
                    result = new ExistingActionReconciliation(reconcile.actionId(), request.before(), reconcile.detail(), trace());
                    return;
                }
                case Refresh refresh -> { outcome = Outcome.REFRESH_REQUIRED; visits.add(visit(policy, outcome, refresh.reason())); result = new RefreshRequired(request.before(), refresh.reason(), trace()); return; }
                case Defer deferred -> {
                    visits.add(new StageVisit(policy.stage(), Outcome.DEFERRED_INPUT, deferred.reason(), Optional.ofNullable(policy.implementationSource()), Optional.of(deferred.evidence())));
                    return;
                }
                case Wait wait -> { outcome = Outcome.BLOCKED; visits.add(visit(policy, outcome, wait.reason())); result = new ReadOnlyWait(request.before(), wait.reason(), trace()); return; }
                case Stop stopped -> { outcome = Outcome.TERMINAL; visits.add(visit(policy, outcome, stopped.reason())); result = stop(stopped.stopReason(), stopped.reason()); return; }
                case Replace replacement -> {
                    Draft proposed = replacement.draft();
                    if (proposed.command().isPresent()) validateCommand(proposed.command().orElseThrow());
                    if ((draft.kind() == Kind.FOREGROUND || draft.kind() == Kind.OPENING_FOCUS || draft.kind() == Kind.MATERIAL_RECEIPT)
                            && !proposed.command().equals(draft.command()))
                        throw new IllegalArgumentException("a lower-priority policy replaced exclusive ordinary work");
                    draft = proposed; outcome = Outcome.REPLACED;
                }
            }
            visits.add(visit(policy, outcome, decision.reason()));
        }
        private StageVisit visit(OrdinaryPolicy policy, Outcome outcome, String reason) {
            return new StageVisit(policy.stage(), outcome, reason, Optional.ofNullable(policy.implementationSource()), Optional.empty());
        }
        private void validateCommand(ActionCommand command) {
            StrictJson.require(command.before().equals(request.before()) && command.source().equals(request.source())
                    && command.sessionId().equals(request.sessionId()) && !command.deadline().isAfter(request.deadline()),
                    "domain producer crossed the complete Game/session/frame/source/deadline binding");
        }
    }

}
