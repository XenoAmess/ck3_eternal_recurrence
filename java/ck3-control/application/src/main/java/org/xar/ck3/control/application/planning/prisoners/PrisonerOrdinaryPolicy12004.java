package org.xar.ck3.control.application.planning.prisoners;

import static org.xar.ck3.control.application.planning.OrdinaryPolicy.*;
import static org.xar.ck3.control.application.planning.prisoners.PrisonerPlanningPorts.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.OrdinaryPolicy.Decision;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Three real ordinary policy stages. Selection is not submission, acceptance, material settlement or ledger mutation. */
public final class PrisonerOrdinaryPolicy12004 implements OrdinaryPolicy {
    public static final OperationKey RELEASE = new OperationKey("submit-player-prisoner-release-private-v1");
    public static final OperationKey RANSOM = new OperationKey("submit-player-prisoner-ransom-private-v1");
    private final PlanningStage stage;
    private final ExactRef source;
    private final Bindings bindings;
    private final PrisonerCollector12004 collector;
    public PrisonerOrdinaryPolicy12004(PlanningStage stage, ExactRef source, Bindings bindings) {
        StrictJson.require(List.of(PlanningStage.PRISONER_RELEASE_DISCOVERY, PlanningStage.PRISONER_RELEASE,
                PlanningStage.PRISONER_RANSOM).contains(stage), "unsupported prisoner stage");
        this.stage = stage; this.source = Objects.requireNonNull(source); this.bindings = Objects.requireNonNull(bindings);
        collector = new PrisonerCollector12004(bindings);
    }
    @Override public PlanningStage stage() { return stage; }
    @Override public ExactRef implementationSource() { return source; }
    @Override public Decision evaluate(PlanningRequest request, Draft previous) {
        if (request.observations().foregroundPresent() || !request.observations().paused() || !request.observations().mapReady()
                || !eligibleBaseline(request, previous)) return new NotApplicable("original urgent/opening/action priority retained");
        OperationKey operation = stage == PlanningStage.PRISONER_RANSOM ? RANSOM : RELEASE;
        if (!request.observations().actionSteps().contains(operation)) return new NotApplicable("private prisoner action is not enabled in current exact operation set");
        LedgerView state = bindings.ledgers().read(request);
        if (state instanceof LedgerUnavailable missing)
            return annotation(previous, "prisoner_pending_unavailable", new OpportunityJson.Text(missing.reason()), "missing domain ledger is not empty");
        KnownLedger ledger = (KnownLedger) state;
        if (ledger.release().isPresent() || ledger.ransom().isPresent()) {
            OpportunityJson.Obj detail = previous.detail().with("prisoner_pending_head", object(StrictJson.canonical(ledger.head().toJson())));
            if (ledger.release().isPresent()) detail = detail.with("prisoner_release_pending", ledger.release().orElseThrow().original());
            if (ledger.ransom().isPresent()) detail = detail.with("prisoner_ransom_pending", ledger.ransom().orElseThrow().original());
            detail = detail.with("prisoner_material_result", new OpportunityJson.Bool(false));
            return new Replace(new Draft(previous.policy(), previous.phase(), previous.reason(), previous.kind(), previous.command(),
                    previous.purpose(), previous.domain(), detail), "independent material/UNKNOWN remains owned by the sole receipt authority");
        }
        try {
            PrisonerCollector12004.Result result = stage == PlanningStage.PRISONER_RANSOM
                    ? collector.collectRansom(request) : collector.collectRelease(request);
            if (result instanceof PrisonerCollector12004.Unavailable unavailable)
                return annotation(previous, "prisoner_observation_unavailable", new OpportunityJson.Text(unavailable.reason()), "unavailable observation does not become a prisoner action");
            if (result instanceof PrisonerCollector12004.Empty) return new Keep("complete current collection has no prisoners");
            var all = (PrisonerCollector12004.Collected) result;
            return stage == PlanningStage.PRISONER_RANSOM ? ransom(request, previous, all) : release(request, previous, all);
        } catch (IllegalArgumentException failure) {
            String reason = failure.getMessage() == null ? "prisoner domain rejected input" : failure.getMessage();
            return annotation(previous, "prisoner_observation_unavailable", new OpportunityJson.Text(reason.substring(0, Math.min(1024, reason.length()))),
                    "original policy rejected missing, changed or unsupported prisoner input");
        }
    }
    private Decision ransom(PlanningRequest request, Draft previous, PrisonerCollector12004.Collected all) {
        List<CollectionRead> reads = collector.ransomReads(all);
        var result = PrisonerRansomFormalPolicy12004.select(all.frame(), reads, all.wars());
        if (!(result instanceof Selected selected)) return new Keep("no accepted complete current ransom offer; original plan retained");
        var latest = collector.refresh(request, all, selected.choice().sourceOrdinal());
        var refreshed = PrisonerRansomFormalPolicy12004.refresh(selected, reads, collector.ransomRead(all.frame(), latest), all.wars());
        if (!(refreshed instanceof Selected current)) return annotation(previous, "prisoner_ransom_refresh", new OpportunityJson.Text("quote_changed_before_submit"), "changed quote is not a replacement submission");
        Choice choice = current.choice();
        ObjectNode arguments = StrictJson.object().put("quote_query_sequence", latest.collection().querySequence())
                .put("prisoner_character_id", choice.prisonerCharacterId()).put("payer_character_id", choice.payerCharacterId())
                .put("quoted_gold_raw", choice.quotedGoldRaw())
                .put("selected_option", choice.option().name().toLowerCase(java.util.Locale.ROOT))
                .put("amount_is_acceptance_time_quote", choice.amountIsAcceptanceTimeQuote())
                .put("pre_player_gold_raw", PrisonerActionBinding12004.gold(request.observations().snapshot()));
        arguments.set("selected_collection_read", latest.archivedRead().orElseThrow().toJson());
        retainWarProofs(arguments, all);
        ObjectNode original = StrictJson.object().put("source_ordinal", choice.sourceOrdinal())
                .put("prisoner_character_id", choice.prisonerCharacterId()).put("payer_character_id", choice.payerCharacterId())
                .put("selected_option", choice.option().name().toLowerCase(java.util.Locale.ROOT))
                .put("quoted_gold_raw", choice.quotedGoldRaw()).put("amount_is_acceptance_time_quote", choice.amountIsAcceptanceTimeQuote())
                .put("material_result", false);
        original.set("collection", StrictJson.parse(latest.original().bytes(), 131072));
        original.set("collection_read_receipt", latest.archivedRead().orElseThrow().toJson());
        var receipts = original.putArray("source_receipts"); all.originalReads().forEach(reference -> receipts.add(reference.toJson()));
        return propose(request, previous, RANSOM, choice.prisonerCharacterId(), arguments, original, "prisoner_ransom_typed_submit");
    }
    private Decision release(PlanningRequest request, Draft previous, PrisonerCollector12004.Collected all) {
        // Entries preserve last occurrence per ordinal; source ordinal itself is not recency.
        for (int index = all.entries().size() - 1; index >= 0; index--) {
            var observed = all.entries().get(index); int ordinal = observed.collection().selectedOrdinal();
            long prisoner = PrisonerCollector12004.selected(observed).prisonerCharacterId();
            if (!PrisonerCollector12004.acceptedRelease(observed, all.frame())
                    || PrisonerCollector12004.retained(all, prisoner) || PrisonerCollector12004.positiveRansomPriorityForRelease(observed, all.frame())) continue;
            var latest = collector.refresh(request, all, ordinal);
            if (PrisonerCollector12004.selected(latest).prisonerCharacterId() != prisoner
                    || latest.query().mask() != observed.query().mask()
                    || !PrisonerCollector12004.acceptedRelease(latest, all.frame())
                    || PrisonerCollector12004.positiveRansomPriorityForRelease(latest, all.frame())) continue;
            ObjectNode arguments = StrictJson.object().put("release_query_sequence", latest.collection().querySequence())
                    .put("prisoner_character_id", prisoner).put("release_option_mask_bits", latest.query().mask());
            arguments.set("selected_collection_read", latest.archivedRead().orElseThrow().toJson());
            retainWarProofs(arguments, all);
            ObjectNode choice = StrictJson.object().put("source_ordinal", ordinal).put("prisoner_character_id", prisoner)
                    .put("release_option_mask_bits", latest.query().mask()).put("material_result", false);
            var keys = choice.putArray("release_option_keys"); latest.query().options().forEach(option -> keys.add(option.key()));
            choice.set("collection", StrictJson.parse(latest.original().bytes(), 131072));
            choice.set("collection_read_receipt", latest.archivedRead().orElseThrow().toJson());
            var receipts = choice.putArray("source_receipts"); all.originalReads().forEach(reference -> receipts.add(reference.toJson()));
            return propose(request, previous, RELEASE, prisoner, arguments, choice, "prisoner_release_typed_submit");
        }
        return new Keep("no accepted release after positive-ransom and complete-war-retention priority");
    }
    private Decision propose(PlanningRequest request, Draft previous, OperationKey operation, long prisoner,
            ObjectNode arguments, ObjectNode choice, String phase) {
        var args = object(StrictJson.canonical(arguments)); var original = object(StrictJson.canonical(choice));
        var claims = claims(prisoner, request.before().frame().identity().player().longValueExact());
        Optional<ActionCommand> command = bindings.commands().bind(request, operation, args, claims, original);
        if (command.isEmpty()) return annotation(previous, "prisoner_observer_unavailable", new OpportunityJson.Text(operation.value()),
                "shared expected-postcondition binding is unavailable");
        ActionCommand value = command.orElseThrow();
        StrictJson.require(value.before().equals(request.before()) && value.source().equals(request.source())
                && value.sessionId().equals(request.sessionId()) && !value.deadline().isAfter(request.deadline())
                && value.operation().equals(operation) && value.arguments().equals(args) && value.claims().equals(claims),
                "shared action factory changed exact selected native intent");
        OpportunityJson.Obj detail = previous.detail().with("prisoner_choice", original)
                .with("prisoner_deferred_phase", new OpportunityJson.Text(previous.phase()))
                .with("prisoner_material_result", new OpportunityJson.Bool(false));
        return new Replace(new Draft("ordinary-prisoner-java-v1", phase, "current accepted native offer; material result remains unobserved",
                Kind.ORDINARY, command, Purpose.WORLD_ACTION, Optional.empty(), detail), "actual selected typed offer proposed through the one action contract");
    }
    private static void retainWarProofs(ObjectNode arguments, PrisonerCollector12004.Collected all) {
        var ids = arguments.putArray("active_war_ids"); all.frame().activeWarIds().forEach(ids::add);
        var reads = arguments.putArray("war_retention_reads");
        for (int index = 0; index < all.frame().activeWarIds().size(); index++) reads.add(all.originalReads().get(index).toJson());
    }
    private boolean eligibleBaseline(PlanningRequest request, Draft previous) {
        if (previous.kind() != Kind.ORDINARY) return false;
        String step = previous.command().map(value -> value.operation().value()).orElse("");
        boolean idle = previous.purpose() == Purpose.DATE_ADVANCE || step.equals("life-advance") || step.startsWith("advance-route-contact-horizon-v1-");
        boolean discovery = !request.observations().warInProgress() && List.of("query-campaign-root-context-v1",
                "query-declarable-wars", "query-arrange-marriage-choices").contains(step);
        return stage == PlanningStage.PRISONER_RANSOM ? idle : idle || discovery;
    }
}
