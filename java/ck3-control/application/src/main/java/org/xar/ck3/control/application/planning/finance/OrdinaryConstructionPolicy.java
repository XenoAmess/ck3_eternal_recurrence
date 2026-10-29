package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeConstructionEffects;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessmentCodec;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryCodec;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQuoteIdentity;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryConstructionOpportunity;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.*;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionConsumer;

/** Single real ordinary construction factory. Planning produces one command; only the coordinator submits it. */
public final class OrdinaryConstructionPolicy implements OrdinaryPolicy {
    public static final OperationKey OPERATION = new OperationKey("g2_player_world_building_action_private_v1");
    @FunctionalInterface public interface Effects {
        Optional<ExpectedPostcondition> expected(PlanningRequest request, Obj exactArguments);
    }
    /** Completion/cold material publication must use the registered original-body reducer under the sole writer lock. */
    @FunctionalInterface public interface MaterialFollowup {
        Decision observeAndPublish(PlanningRequest request, Draft original, ConstructionLedgerCodec.Ledger ledger,
                ConstructionLedgerCodec.Receipt receipt, Followup reason);
    }
    public enum Followup { COLD_MATERIAL, COMPLETED_CASH, COMPLETED_PROVINCE, MONTHLY_COMPLETION }
    private final ExactRef source;
    private final OrdinaryConstructionCollector collector;
    private final Effects effects;
    private final MaterialFollowup material;
    public OrdinaryConstructionPolicy(ExactRef source, OrdinaryConstructionCollector collector, Effects effects, MaterialFollowup material) {
        this.source = Objects.requireNonNull(source); this.collector = Objects.requireNonNull(collector);
        this.effects = Objects.requireNonNull(effects); this.material = Objects.requireNonNull(material);
        require(source.bytes() > 0, "actual complete construction implementation source required");
    }
    @Override public PlanningStage stage() { return PlanningStage.CONSTRUCTION; }
    @Override public ExactRef implementationSource() { return source; }
    @Override public Decision evaluate(PlanningRequest request, Draft previous) {
        Objects.requireNonNull(request); Objects.requireNonNull(previous);
        if (!request.observations().paused() || !request.observations().mapReady() || request.observations().foregroundPresent())
            return new NotApplicable("construction preserves actual foreground or non-paused work");
        try {
            FinanceStatePort.Result state = collector.state(request);
            if (!(state instanceof FinanceStatePort.Known known)) return deferred(((FinanceStatePort.Missing) state).reason());
            var domain = known.snapshot().ledger(FinanceStatePort.Domain.CONSTRUCTION);
            if (domain.isEmpty()) return deferred("actual original construction body is unimported");
            ConstructionLedgerCodec.Ledger ledger = ConstructionLedgerCodec.decodeLedger(encode(domain.orElseThrow().original()));
            List<ActionReceipt> unresolvedConstruction = known.snapshot().unresolved().stream()
                    .filter(row -> row.command().operation().equals(OPERATION)).toList();
            if (ledger.pending().isEmpty() && !unresolvedConstruction.isEmpty()) {
                if (unresolvedConstruction.size() != 1) return new Wait("multiple original construction actions remain unresolved; no new expenditure is allowed");
                var original = unresolvedConstruction.getFirst();
                return new ReconcileExisting(original.command().actionId(),
                        obj("construction_pending_domain_body", Nil.INSTANCE, "new_native_submit_calls", new IntegerValue(BigInteger.ZERO)),
                        "original coordinator intent is unresolved before domain publication; independently reconcile it without replay");
            }
            if (ledger.pending().isPresent()) {
                var pending = ledger.pending().orElseThrow();
                if (!pending.identity().episode().equals(request.before().frame().episodeRunId()))
                    return new Defer("retain the old episode's unresolved construction and defer optional new construction while other ordinary work continues",
                            obj("construction_previous_episode_pending", pending.original(), "actions_replayed", new Bool(false),
                                    "continue_ordinary_war", new Bool(true), "business_submission", new Bool(false),
                                    "future_funding_credited_raw", new IntegerValue(BigInteger.ZERO)));
                List<ActionReceipt> original = unresolvedConstruction.stream()
                        .filter(row -> pending.coordinatorActionId().filter(row.command().actionId()::equals).isPresent()
                                || ActionTransitions.attempt(row.state()).filter(attempt -> attempt.requestId().equals(pending.identity().actionRequestId())).isPresent()
                                || row.ack().map(ack -> ack.requestId().equals(pending.identity().actionRequestId())).orElse(false)
                                || row.command().actionId().equals(pending.identity().actionRequestId())).toList();
                if (original.size() != 1) return new Wait("original construction pending intent has no unique imported coordinator receipt; UNKNOWN is never replayed");
                return new ReconcileExisting(original.getFirst().command().actionId(),
                        obj("construction_pending_action", pending.original(), "new_native_submit_calls", new IntegerValue(BigInteger.ZERO)),
                        "independently reconcile the already durable original construction command");
            }
            String episode = request.before().frame().episodeRunId();
            List<ConstructionLedgerCodec.Receipt> receipts = ledger.receipts(episode);
            for (Followup reason : Followup.values()) for (var receipt : receipts)
                if (due(request, receipt, reason)) return Objects.requireNonNull(material.observeAndPublish(request, previous, ledger, receipt, reason));
            if (ledger.applied().filter(row -> row.identity().episode().equals(episode)).isPresent()) {
                var newest = ledger.applied().orElseThrow(); var now = request.before().frame().identity();
                if (now.nativeRevision().compareTo(newest.observed().nativeRevision()) <= 0 || now.dateRaw().compareTo(newest.observed().dateRaw()) <= 0)
                    return new Keep("prior verified construction is consumed before another later game day may spend");
            }
            Selection selection = selection(previous);
            if (!selection.opportunity().admitsOptionalQuote()) return new NotApplicable("selected concrete war or ordinary work keeps priority over optional construction");
            Obj procurement = previous.detail().get("war_mercenary_decision_v1") instanceof Obj value ? value : obj();
            String kind = previous.detail().get("construction_expenditure_kind") instanceof Text value ? value.value() : "new_building";
            var current = collector.before(request, selection, procurement, kind);
            if (current instanceof OrdinaryConstructionCollector.FrameChanged changed) return new Refresh(changed.reason());
            if (current instanceof OrdinaryConstructionCollector.Missing missing) return deferred(missing.reason());
            var prepared = ((OrdinaryConstructionCollector.Available) current).value();
            Optional<Obj> recovery = emergencyRecovery(request.observations().snapshot(),
                    prepared.current().state().ledger(FinanceStatePort.Domain.MERCENARY)
                            .orElseThrow(() -> new IllegalArgumentException("actual complete mercenary recovery body unavailable")),
                    Optional.of(prepared.current().root()));
            if (recovery.filter(value -> bool(value.get("defer_new_economic_construction"), "current emergency recovery deferral")).isPresent())
                return new Defer("restore the actual military cash buffer after emergency expenditure before optional construction",
                        obj("war_emergency_recovery_v1", recovery.orElseThrow(), "continue_ordinary_war", new Bool(true),
                                "future_funding_credited_raw", new IntegerValue(BigInteger.ZERO), "business_submission", new Bool(false)));
            if (prepared.current().priority().deferredOptionalConstruction()) {
                var financing = EmergencyFinancingAssessmentCodec.assess(EmergencyFinancingAssessmentCodec.decode(encode(prepared.financing())));
                return new Defer("current losing war, threatened titles or defensive siege protect military cash before optional construction",
                        obj("war_spending_priority_v1", object(parse(prepared.current().priority().toJson()), "actual war priority"),
                                "emergency_financing_assessment", DriverJson.object(EmergencyFinancingAssessmentCodec.encode(financing), 262_144),
                                "continue_ordinary_war", new Bool(true), "future_funding_credited_raw", new IntegerValue(BigInteger.ZERO)));
            }
            // The same pre-query request must never be passed as the quoted request (or vice versa).
            if (prepared.fundingSource() instanceof CanonicalFundingPending.Unavailable missing)
                return deferred("actual owned-submission inventory unavailable: " + missing.reason());
            Result before = OrdinaryWartimeConstruction.compose(prepared.before().input());
            if (before.disposition() != Disposition.OPTIONAL_QUERY_ALLOWED) return deferred(reason(before));
            var quote = collector.quote(prepared);
            if (quote instanceof OrdinaryConstructionCollector.QuoteFrameChanged changed) return new Refresh(changed.reason());
            if (quote instanceof OrdinaryConstructionCollector.QuoteMissing missing) return deferred(missing.reason());
            var quoted = (OrdinaryConstructionCollector.Quoted) quote;
            Result result = OrdinaryWartimeConstructionConsumer.plan(() -> prepared.before(),
                    () -> new OrdinaryWartimeConstructionConsumer.ObservedQuote(quoted.value()));
            if (result.disposition() != Disposition.QUOTED_CANDIDATE) return deferred(reason(result));
            if (!(quoted.fundingSource() instanceof CanonicalFundingPending.Observed funding))
                return deferred("actual owned-submission inventory unavailable at the quoted outlay: "
                        + ((CanonicalFundingPending.Unavailable) quoted.fundingSource()).reason());
            Obj finalized = object(parse(ConstructionQueryCodec.finalizeObservation(
                    quoted.value().input().quoted().orElseThrow().nativeQuote().original())), "original finalized quote");
            Obj candidate = object(finalized.get("candidate"), "complete selected construction candidate");
            Obj args = obj("candidate", candidate, "pre_proof_epoch", finalized.get("proof_epoch"),
                    "ordinary_cash_request", DriverJson.object(quoted.value().original(), OrdinaryWartimeConstructionCodec.MAX_BYTES),
                    "ordinary_cash_result", DriverJson.object(OrdinaryWartimeConstructionCodec.encode(result), OrdinaryWartimeConstructionCodec.MAX_BYTES),
                    ConstructionFundingEvidence.FIELD, ConstructionFundingEvidence.capture(funding, quoted.financing()));
            if (!request.observations().actionSteps().contains(OPERATION)) return deferred("actual construction action registration absent");
            Optional<ExpectedPostcondition> expected = effects.expected(request, args);
            if (expected.isEmpty()) return deferred("actual independent construction material observer is unregistered");
            require(expected.orElseThrow().equals(NativeConstructionEffects.expected(request.before(), request.source(), args)),
                    "registered material postcondition differs from the exact construction tuple");
            String actionId = ActionIds.forDecision(request.sessionId(), request.before(), OPERATION.value() + ":" + ActionCodec.sha256(encode(args)));
            Claims claims = new Claims(Set.of(), Set.of(), Set.of(), Set.of("construction:" + integer(candidate.get("barony_title_id"), "barony")
                    + ":" + integer(candidate.get("province_id"), "province") + ":" + integer(candidate.get("slot_index"), "slot")));
            ActionCommand command = new ActionCommand(actionId, request.before(), request.source(), request.sessionId(), OPERATION,
                    args, expected.orElseThrow(), claims, request.deadline());
            String phase = selection.opportunity() == Opportunity.PREWAR_ARBITRATION ? "construction_prewar_typed_submit"
                    : request.observations().warInProgress() ? "construction_wartime_typed_submit" : "construction_typed_submit";
            return new Replace(new Draft("ordinary-construction-java-v1", phase, "native legal quoted construction retains actual military, commitments and emergency reserves",
                    Kind.ORDINARY, Optional.of(command), Purpose.OPTIONAL_CONSTRUCTION, Optional.of(Domain.building),
                    previous.detail().with("selected_step", new Text(OPERATION.value())).with("arguments", args)
                            .with("construction_private_query", finalized)), "one native legal budgeted construction selected");
        } catch (IllegalArgumentException rejected) { return deferred("optional construction source rejected: " + rejected.getMessage()); }
    }
    /** Registered preparation calls this under the coordinator's existing writer lock; no second lock is acquired. */
    public void revalidateConstruction(Session originalWriterSession, ActionCommand command, PlanningRequest fresh) {
        Objects.requireNonNull(originalWriterSession);
        require(command.operation().equals(OPERATION) && command.before().equals(fresh.before()) && command.source().equals(fresh.source())
                && command.sessionId().equals(fresh.sessionId()), "construction dispatch complete source drift");
        var planned = new OrdinaryWartimeConstructionCodec.ObservedRequest(encode(object(command.arguments().get("ordinary_cash_request"), "planned quoted request")));
        Obj original = DriverJson.object(planned.original(), OrdinaryWartimeConstructionCodec.MAX_BYTES);
        Obj originalCash = object(original.get("cash_input"), "planned cash input");
        Obj procurement = originalCash.get("procurement_decision") instanceof Obj value ? value : obj();
        var current = collector.before(originalWriterSession, fresh, planned.input().selection(), procurement, planned.input().current().kindWire());
        require(current instanceof OrdinaryConstructionCollector.Available, "fresh construction zero-spend/current source deferred");
        var prepared = ((OrdinaryConstructionCollector.Available) current).value();
        Optional<Obj> recovery = emergencyRecovery(fresh.observations().snapshot(),
                prepared.current().state().ledger(FinanceStatePort.Domain.MERCENARY)
                        .orElseThrow(() -> new IllegalArgumentException("actual complete mercenary recovery body unavailable at INTENT")),
                Optional.of(prepared.current().root()));
        require(recovery.filter(value -> bool(value.get("defer_new_economic_construction"), "current emergency recovery deferral")).isEmpty(),
                "current military cash buffer still requires recovery after emergency expenditure");
        require(prepared.current().state().unresolved().stream().noneMatch(row -> row.command().operation().equals(OPERATION)),
                "an original construction intent became unresolved before the new intent; never spend or replay");
        require(!prepared.current().priority().deferredOptionalConstruction(), "fresh war crisis protects emergency military funds");
        require(OrdinaryWartimeConstruction.compose(prepared.before().input()).disposition() == Disposition.OPTIONAL_QUERY_ALLOWED,
                "fresh pre-query reserves or funding ledger deferred optional construction");
        var query = collector.quote(originalWriterSession, prepared); require(query instanceof OrdinaryConstructionCollector.Quoted, "fresh native quote unavailable or frame changed");
        var quoted = (OrdinaryConstructionCollector.Quoted) query;
        require(quoted.fundingSource() instanceof CanonicalFundingPending.Observed, "fresh actual owned-submission inventory unavailable");
        ConstructionFundingEvidence.requireCurrent(command, (CanonicalFundingPending.Observed) quoted.fundingSource(), quoted.financing());
        var observed = quoted.value();
        Result now = OrdinaryWartimeConstruction.compose(observed.input());
        require(now.disposition() == Disposition.QUOTED_CANDIDATE, "fresh actual cost/current commitments deferred optional construction");
        Result before = OrdinaryWartimeConstruction.compose(planned.input());
        require(before.disposition() == Disposition.QUOTED_CANDIDATE && sameQuote(before.candidate().orElseThrow().original().bytes(), now.candidate().orElseThrow().original().bytes()),
                "fresh complete native construction selection changed; replan required");
        require(NativeConstructionEffects.expected(fresh.before(), fresh.source(), command.arguments()).equals(command.expected()), "construction expected tuple changed");
    }
    /** Only transport request identity and monotonically refreshed probe counter may differ in a fresh quote. */
    public static boolean sameQuote(byte[] planned, byte[] current) {
        return ConstructionQuoteIdentity.same(planned, current);
    }
    /** Reevaluate the one finance recovery producer from its actual archived full body; no second reserve formula. */
    static Optional<Obj> emergencyRecovery(Obj actualSnapshot, FinanceStatePort.Ledger actualMercenaryBody, Optional<Obj> actualRoot) {
        Objects.requireNonNull(actualSnapshot); Objects.requireNonNull(actualMercenaryBody); Objects.requireNonNull(actualRoot);
        require(actualMercenaryBody.document().domain() == FinanceStatePort.Domain.MERCENARY, "actual original mercenary domain required");
        var ledger = MercenaryProcurement.decode(actualMercenaryBody.document().bytes());
        require(ledger.original().equals(actualMercenaryBody.original())
                && (actualMercenaryBody.pending() == FinanceStatePort.Pending.PENDING) == ledger.pending().isPresent(),
                "mercenary recovery projection differs from its actual original body");
        return MercenaryProcurement.recovery(actualSnapshot, ledger, actualRoot);
    }
    public static Selection selection(Draft draft) {
        Optional<String> step = draft.detail().get("selected_step") instanceof Text text ? Optional.of(text.value())
                : draft.command().map(command -> command.operation().value());
        Optional<String> phase = Optional.of(draft.phase()); Opportunity opportunity = Opportunity.CONTINUE_SELECTED_WORK;
        if (draft.kind() == Kind.ORDINARY) {
            if (step.filter("life-advance"::equals).isPresent()) opportunity = Opportunity.ORDINARY_ADVANCE;
            else if (step.filter(DeclarationContract::isNativeDeclarationStep).isPresent()) opportunity = Opportunity.PREWAR_ARBITRATION;
            else if (draft.phase().equals("native_war_route_contact_horizon_progress")
                    && step.filter(OrdinaryConstructionOpportunity::isAdvanceRouteContactHorizon).isPresent()) opportunity = Opportunity.QUIET_ROUTE_ADVANCE;
        }
        return new Selection(step, phase, opportunity);
    }
    private static boolean due(PlanningRequest request, ConstructionLedgerCodec.Receipt receipt, Followup reason) {
        var now = request.before().frame().identity(); var scope = receipt.observed();
        Obj diagnostics = object(request.observations().snapshot().get("diagnostics"), "actual native diagnostics");
        boolean sameProcess = new IntegerValue(scope.process().pid()).equals(diagnostics.get("bridge_pid"))
                && new Text(scope.process().legacyCreationToken()).equals(diagnostics.get("bridge_creation_date"));
        return switch (reason) {
            case COLD_MATERIAL -> !sameProcess || now.nativeRevision().compareTo(scope.nativeRevision()) < 0 || now.dateRaw().compareTo(scope.dateRaw()) < 0;
            case COMPLETED_CASH -> receipt.completed() && (receipt.economy().postGross().isEmpty() || receipt.economy().postCash().isEmpty());
            case COMPLETED_PROVINCE -> receipt.completed() && receipt.economy().postProvince().filter(ConstructionEconomyModel.ProvinceObservation::observed).isEmpty()
                    && receipt.lastCheck().filter(date -> now.dateRaw().compareTo(date.add(BigInteger.valueOf(720))) >= 0).isPresent();
            case MONTHLY_COMPLETION -> !receipt.completed()
                    && receipt.lastCheck().filter(date -> now.dateRaw().compareTo(date.add(BigInteger.valueOf(720))) >= 0).isPresent();
        };
    }
    private static String reason(Result result) { return "optional construction deferred: " + result.reason().map(Enum::name).orElse(result.disposition().name()); }
    public static Defer deferred(String reason) { return new Defer(reason, obj("domain", new Text("new_building_upgrade_or_holding"),
            "future_funding_credited_raw", new IntegerValue(BigInteger.ZERO), "continue_ordinary_war", new Bool(true), "business_submission", new Bool(false))); }
}
