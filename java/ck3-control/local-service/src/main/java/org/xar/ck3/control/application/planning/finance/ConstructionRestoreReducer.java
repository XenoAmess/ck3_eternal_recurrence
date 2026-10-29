package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Restores the qualified saved full body while retaining every current unresolved construction command. */
public final class ConstructionRestoreReducer {
    private ConstructionRestoreReducer() { }
    public record Canonical(ActionReceipt receipt, ExactRef originalReceipt) {
        public Canonical { Objects.requireNonNull(receipt); Objects.requireNonNull(originalReceipt); }
    }
    public static Obj reduce(ConstructionLedgerCodec.Ledger saved, Optional<ConstructionLedgerCodec.Ledger> current,
            List<Canonical> actualCanonical, ConstructionRestoreProvenance originalProvenance) {
        Objects.requireNonNull(saved); Objects.requireNonNull(current); actualCanonical = List.copyOf(actualCanonical); Objects.requireNonNull(originalProvenance);
        saved.pending().ifPresent(pending -> requireOwner(pending, originalProvenance));
        Optional<ConstructionLedgerCodec.Intent> retained = current.flatMap(ConstructionLedgerCodec.Ledger::pending);
        retained.ifPresent(pending -> requireOwner(pending, originalProvenance));
        if (retained.isPresent() && saved.pending().isPresent())
            require(sameOriginal(retained.orElseThrow(), saved.pending().orElseThrow()),
                    "two different original pending construction bodies require independent reconciliation; neither may be discarded");
        if (retained.isEmpty()) retained = saved.pending();
        List<Canonical> unresolved = actualCanonical.stream().filter(row -> !row.receipt().settled()
                && row.receipt().command().operation().equals(OrdinaryConstructionPolicy.OPERATION)).toList();
        require(unresolved.size() <= 1, "multiple canonical construction UNKNOWN guards cannot be collapsed during restore");
        Obj restored = saved.original();
        if (!unresolved.isEmpty()) {
            Canonical row = unresolved.getFirst(); ActionReceipt receipt = row.receipt();
            require(receipt.command().before().frame().episodeRunId().equals(originalProvenance.savedEpisodeRunId())
                    && receipt.command().before().frame().identity().player().equals(originalProvenance.savedActorCharacterId()),
                    "canonical construction UNKNOWN crossed the actual saved episode/player");
            if (retained.isEmpty()) {
                Obj derived = ConstructionDomainLifecycle.intent(ConstructionLedgerCodec.decodeLedger(encode(restored.with("pending", Nil.INSTANCE))), receipt.command());
                retained = Optional.of(ConstructionLedgerCodec.intent(object(derived.get("pending"), "actual canonical original intent")));
            }
            var pending = retained.orElseThrow();
            require(matches(pending, receipt), "restored pending differs from the actual canonical UNKNOWN construction");
            Obj original = pending.original().with("status", new Text("action_state_unknown"))
                    .with("java_original_coordinator_receipt", object(parse(StrictJson.canonical(row.originalReceipt().toJson())), "actual canonical receipt source"));
            restored = restored.with("pending", original);
        } else if (retained.isPresent()) {
            restored = restored.with("pending", retained.orElseThrow().original());
        }
        // The selected saved body and its source references remain complete. Future abandoned receipts receive no current credit.
        return restored.with("java_restored_construction_originals_v1", originalProvenance.toJson());
    }
    private static void requireOwner(ConstructionLedgerCodec.Intent pending, ConstructionRestoreProvenance original) {
        require(pending.identity().episode().equals(original.savedEpisodeRunId())
                && pending.identity().actor().equals(original.savedActorCharacterId()),
                "original pending construction crossed its saved episode/player");
    }
    private static boolean sameOriginal(ConstructionLedgerCodec.Intent current, ConstructionLedgerCodec.Intent saved) {
        return current.identity().equals(saved.identity()) && current.source().equals(saved.source())
                && current.proofEpoch().equals(saved.proofEpoch()) && current.coordinatorActionId().equals(saved.coordinatorActionId())
                && Objects.equals(current.original().get("coordinator_body_sha256"), saved.original().get("coordinator_body_sha256"))
                && Objects.equals(current.original().get("candidate"), saved.original().get("candidate"));
    }
    private static boolean matches(ConstructionLedgerCodec.Intent pending, ActionReceipt receipt) {
        var before = receipt.command().before();
        if (!Objects.equals(pending.original().get("candidate"), receipt.command().arguments().get("candidate"))
                || !new IntegerValue(pending.proofEpoch()).equals(receipt.command().arguments().get("pre_proof_epoch"))) return false;
        if (pending.coordinatorActionId().isPresent()
                && (!pending.coordinatorActionId().orElseThrow().equals(receipt.command().actionId())
                || !new Text(receipt.bodySha256()).equals(pending.original().get("coordinator_body_sha256")))) return false;
        if (!pending.identity().episode().equals(before.frame().episodeRunId())
                || !pending.identity().actor().equals(before.frame().identity().player())
                || !pending.source().nativeRevision().equals(before.frame().identity().nativeRevision())
                || !pending.source().dateRaw().equals(before.frame().identity().dateRaw())) return false;
        Obj cash = object(receipt.command().arguments().get("ordinary_cash_request"), "actual canonical construction cash source");
        Obj outlay = object(cash.get("quoted_outlay"), "actual canonical quoted outlay");
        Obj query = object(outlay.get("query_observation"), "actual canonical original construction query");
        Obj diagnostic = object(object(query.get("starting_snapshot"), "actual canonical before snapshot").get("diagnostics"), "actual canonical before process");
        if (!new IntegerValue(pending.source().process().pid()).equals(diagnostic.get("bridge_pid"))
                || !new Text(pending.source().process().legacyCreationToken()).equals(diagnostic.get("bridge_creation_date"))) return false;
        return pending.coordinatorActionId().filter(receipt.command().actionId()::equals).isPresent()
                || pending.identity().actionRequestId().equals(RequestIds.forActionBody(receipt.bodySha256()))
                || ActionTransitions.attempt(receipt.state()).filter(attempt -> attempt.requestId().equals(pending.identity().actionRequestId())).isPresent()
                || receipt.ack().filter(ack -> ack.requestId().equals(pending.identity().actionRequestId())).isPresent();
    }
}
