package org.xar.ck3.control.application.planning.prisoners;

import static org.xar.ck3.control.application.planning.OrdinaryPolicy.*;
import static org.xar.ck3.control.application.planning.prisoners.PrisonerPlanningPorts.*;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Concrete ordinary producers and the unique pending-publication contributor. No method submits an action. */
public final class OrdinaryPrisonerPolicies12004 {
    private OrdinaryPrisonerPolicies12004() { }
    public record Sources(ExactRef prisoners, ExactRef succession) {
        public Sources { Objects.requireNonNull(prisoners); Objects.requireNonNull(succession);
            StrictJson.require(prisoners.bytes() > 0 && succession.bytes() > 0, "actual producer sources required"); }
    }
    public static List<OrdinaryPolicy> prisoners(Sources sources, Bindings bindings) {
        Objects.requireNonNull(sources); Objects.requireNonNull(bindings);
        return List.of(new PrisonerOrdinaryPolicy12004(PlanningStage.PRISONER_RELEASE_DISCOVERY, sources.prisoners(), bindings),
                new PrisonerOrdinaryPolicy12004(PlanningStage.PRISONER_RANSOM, sources.prisoners(), bindings),
                new PrisonerOrdinaryPolicy12004(PlanningStage.PRISONER_RELEASE, sources.prisoners(), bindings));
    }
    public static List<OrdinaryPolicy> succession(Sources sources, Bindings bindings) {
        Objects.requireNonNull(sources); Objects.requireNonNull(bindings);
        return List.of(new SuccessionOrdinaryPolicy12004(PlanningStage.SUCCESSION_PREFLIGHT, sources.succession(), bindings),
                new SuccessionOrdinaryPolicy12004(PlanningStage.DEFERRED_SUCCESSION_ROOT, sources.succession(), bindings));
    }
    /** Finance's sole PENDING_MATERIAL_PUBLICATION producer calls this before ordinary/foreground gates. */
    public static Optional<Decision> reconcilePending(PlanningRequest request, Draft previous,
            Bindings bindings, ActionJournal actions) {
        Objects.requireNonNull(request); Objects.requireNonNull(previous); Objects.requireNonNull(bindings); Objects.requireNonNull(actions);
        Optional<ActionReceipt> unresolved = actions.locked(journal -> journal.unresolved().stream()
                .filter(receipt -> receipt.command().operation().equals(PrisonerOrdinaryPolicy12004.RELEASE)
                        || receipt.command().operation().equals(PrisonerOrdinaryPolicy12004.RANSOM))
                .min(java.util.Comparator.comparingLong(ActionReceipt::sequence)));
        if (unresolved.isPresent()) {
            ActionReceipt original = unresolved.orElseThrow(); ActionCommand command = original.command();
            boolean same = command.before().machineId().equals(request.before().machineId())
                    && command.before().game().equals(request.before().game()) && command.source().equals(request.source())
                    && command.sessionId().equals(request.sessionId())
                    && command.before().frame().episodeRunId().equals(request.before().frame().episodeRunId())
                    && command.before().frame().identity().player().equals(request.before().frame().identity().player());
            var facts = request.observations().actionFacts().stream().filter(fact -> fact.actionId().equals(command.actionId())).toList();
            OpportunityJson.Obj detail = previous.detail().with("prisoner_material_result", new OpportunityJson.Bool(false));
            if (!same || facts.size() != 1 || !facts.getFirst().bodySha256().equals(original.bodySha256()))
                return Optional.of(new Defer("existing prisoner action binding is unavailable; retain UNKNOWN without replay",
                        detail.with("prisoner_pending_status", new OpportunityJson.Text("EXISTING_ACTION_SOURCE_REJECTED"))));
            return Optional.of(new ReconcileExisting(command.actionId(), detail.with("prisoner_pending_status",
                    new OpportunityJson.Text("UNKNOWN_READ_ONLY_RECONCILIATION")), "read only the original canonical prisoner action outcome"));
        }
        LedgerView view = bindings.ledgers().read(request);
        if (view instanceof LedgerUnavailable missing)
            return Optional.of(new Defer("prisoner domain bodies unavailable; no clear pending state inferred",
                    previous.detail().with("prisoner_pending_input_unavailable", new OpportunityJson.Text(missing.reason()))));
        KnownLedger ledger = (KnownLedger) view;
        Optional<Pending> selected = ledger.release().isPresent() ? ledger.release() : ledger.ransom();
        if (selected.isEmpty()) return Optional.empty();
        Pending pending = selected.orElseThrow();
        OpportunityJson.Obj detail = previous.detail().with("prisoner_pending", pending.original())
                .with("prisoner_pending_head", object(StrictJson.canonical(ledger.head().toJson())))
                .with("prisoner_pending_source", object(StrictJson.canonical(pending.source().toJson())))
                .with("prisoner_material_result", new OpportunityJson.Bool(false));
        try {
            OpportunityJson.Obj body = pending.original();
            long player = id(body.get("player_character_id"), "player_character_id");
            long target = id(body.get("prisoner_character_id"), "prisoner_character_id");
            StrictJson.require(player == request.before().frame().identity().player().longValueExact() && target != player,
                    "pending changed its actual actor/target");
            BigInteger nativeBefore = OpportunityJson.integer(body.get("pre_native_revision"), "pre_native_revision");
            BigInteger dateBefore = OpportunityJson.integer(body.get("pre_date_raw"), "pre_date_raw");
            StrictJson.require(nativeBefore.signum() > 0
                    && nativeBefore.compareTo(request.before().frame().identity().nativeRevision()) <= 0
                    && dateBefore.signum() > 0 && dateBefore.compareTo(request.before().frame().identity().dateRaw()) <= 0,
                    "pending predates no observed frame or is ahead");
            if (!body.members().containsKey("action_id"))
                return Optional.of(new Defer("legacy prisoner pending has no original Java action binding; retain UNKNOWN and never resubmit",
                        detail.with("prisoner_pending_status", new OpportunityJson.Text("LEGACY_ACTION_BINDING_UNAVAILABLE"))));
            String actionId = OpportunityJson.text(body.get("action_id"), "action_id");
            StrictJson.require(actionId.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"), "original action identity required");
            Optional<ActionReceipt> original = actions.locked(journal -> journal.find(actionId));
            StrictJson.require(original.isPresent(), "pending original action is absent from the sole journal");
            ActionReceipt receipt = original.orElseThrow(); ActionCommand command = receipt.command();
            OperationKey operation = pending.family() == Family.RELEASE ? PrisonerOrdinaryPolicy12004.RELEASE : PrisonerOrdinaryPolicy12004.RANSOM;
            StrictJson.require(command.operation().equals(operation) && command.before().machineId().equals(request.before().machineId())
                    && command.before().game().equals(request.before().game()) && command.source().equals(request.source())
                    && command.sessionId().equals(request.sessionId())
                    && command.before().frame().episodeRunId().equals(request.before().frame().episodeRunId())
                    && command.before().frame().identity().player().equals(BigInteger.valueOf(player))
                    && command.before().frame().identity().nativeRevision().equals(nativeBefore)
                    && command.before().frame().identity().dateRaw().equals(dateBefore)
                    && OpportunityJson.integer(command.arguments().get("prisoner_character_id"), "prisoner_character_id").equals(BigInteger.valueOf(target)),
                    "pending differs from original complete action identity");
            var facts = request.observations().actionFacts().stream().filter(fact -> fact.actionId().equals(actionId)).toList();
            StrictJson.require(facts.size() == 1 && facts.getFirst().bodySha256().equals(receipt.bodySha256()),
                    "pending original action has no exact authoritative current fact");
            return Optional.of(new ReconcileExisting(actionId, detail.with("prisoner_pending_status",
                    new OpportunityJson.Text(receipt.settled() ? "EXISTING_TERMINAL_RECEIPT" : "UNKNOWN_READ_ONLY_RECONCILIATION")),
                    "reconcile only the exact durable original prisoner action; no dispatch or inferred material result"));
        } catch (IllegalArgumentException | ArithmeticException rejected) {
            String reason = rejected.getMessage() == null ? "pending source rejected" : rejected.getMessage();
            return Optional.of(new Defer("prisoner pending source rejected; no action or material authority",
                    detail.with("prisoner_pending_status", new OpportunityJson.Text("SOURCE_REJECTED"))
                            .with("prisoner_pending_reason", new OpportunityJson.Text(reason.substring(0, Math.min(1024, reason.length()))))));
        }
    }
    private static long id(OpportunityJson.Value value, String field) {
        BigInteger id = OpportunityJson.integer(value, field);
        StrictJson.require(id.signum() > 0 && id.compareTo(BigInteger.valueOf(0xffff_fffeL)) <= 0, "valid full prisoner identity required");
        return id.longValueExact();
    }
}

