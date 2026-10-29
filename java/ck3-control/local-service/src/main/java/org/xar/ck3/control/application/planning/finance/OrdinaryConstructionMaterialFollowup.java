package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts.Head;

/** Planning is observation-only. Actual body publication runs after the frozen planning scope has ended. */
public final class OrdinaryConstructionMaterialFollowup implements OrdinaryConstructionPolicy.MaterialFollowup, OrdinaryPlanCompletion {
    public static final String FIELD = "construction_material_followup_v1";
    @FunctionalInterface public interface SnapshotVerifier {
        void verify(Head actualLockedHead, Obj originalSnapshot, List<PlanningReadReceipt> originalReads) throws IOException;
    }
    @FunctionalInterface public interface Borrowed { ContinuityStorePort.Session current() throws IOException; }
    @FunctionalInterface public interface MaterialScope {
        OrdinaryConstructionCollector.MaterialRead collect(ContinuityStorePort.Session borrowed, PlanningRequest original) throws IOException;
    }
    private final ConstructionDomainLifecycle.Prepared lifecycle;
    private final MaterialScope materialScope;
    private final Borrowed borrowed;
    public OrdinaryConstructionMaterialFollowup(ConstructionDomainLifecycle.Prepared lifecycle, MaterialScope materialScope, Borrowed borrowed) {
        this.lifecycle = Objects.requireNonNull(lifecycle); this.materialScope = Objects.requireNonNull(materialScope); this.borrowed = Objects.requireNonNull(borrowed);
    }
    @Override public OrdinaryPolicy.Decision observeAndPublish(PlanningRequest request, OrdinaryPolicy.Draft original,
            ConstructionLedgerCodec.Ledger ledger, ConstructionLedgerCodec.Receipt receipt, OrdinaryConstructionPolicy.Followup reason) {
        Objects.requireNonNull(request); Objects.requireNonNull(original); Objects.requireNonNull(ledger); Objects.requireNonNull(receipt); Objects.requireNonNull(reason);
        Obj directive = obj("action_request_id", new Text(receipt.identity().actionRequestId()), "reason", new Text(reason.name()),
                "original_body_sha256", new Text(ActionCodec.sha256(encode(ledger.original()))));
        var retained = new OrdinaryPolicy.Draft(original.policy(), original.phase(), original.reason(), original.kind(), original.command(), original.purpose(),
                original.domain(), original.detail().with(FIELD, directive));
        return new OrdinaryPolicy.Annotate(retained, "read-only construction material follow-up queued for the actual completion boundary");
    }
    @Override public PlanningDisposition afterPlanning(PlanningRequest original, PlanningResult planned) {
        try {
            ContinuityStorePort.Session session = borrowed.current();
            if (lifecycle.hasRecoverablePreparedHead(session)) {
                var observed = materialScope.collect(session, original);
                if (observed instanceof OrdinaryConstructionCollector.MaterialAvailable material) {
                    var recovered = lifecycle.recoverPreparedWithoutIntent(session, original, material);
                    if (recovered.isPresent()) return recovered.orElseThrow().completion();
                }
                return new Unchanged("prepared pre-INTENT failure retains its original guard until complete independent project/wallet proof is available");
            }
            Optional<Obj> detail = planned.trace().finalPlan().map(OrdinaryPolicy.Draft::detail);
            if (detail.isEmpty() || detail.orElseThrow().get(FIELD) == null) return new Unchanged("no construction material follow-up is requested");
            Obj directive = object(detail.orElseThrow().get(FIELD), "construction material directive");
            require(directive.members().keySet().equals(Set.of("action_request_id", "reason", "original_body_sha256")), "exact material directive required");
            var reason = OrdinaryConstructionPolicy.Followup.valueOf(text(directive.get("reason"), "material reason"));
            var ledger = lifecycle.read(session);
            if (!new Text(ActionCodec.sha256(encode(ledger.original()))).equals(directive.get("original_body_sha256")))
                return new Blocked("construction body changed after planning; acquire a new ordinary observation", List.of());
            String action = text(directive.get("action_request_id"), "original action identity");
            require(ledger.receipts(original.before().frame().episodeRunId()).stream().filter(row -> row.identity().actionRequestId().equals(action)).count() == 1,
                    "material directive has no unique actual original receipt");
            var observed = materialScope.collect(session, original);
            if (observed instanceof OrdinaryConstructionCollector.MaterialFrameChanged changed) return new Blocked(changed.reason(), List.of());
            if (observed instanceof OrdinaryConstructionCollector.MaterialMissing missing)
                return new Unchanged("optional construction material remains unavailable; retain the selected ordinary work: " + missing.reason());
            return lifecycle.publishMaterial(session, ledger, refreshKind(reason), action, (OrdinaryConstructionCollector.MaterialAvailable) observed).completion();
        } catch (IOException | IllegalArgumentException unavailable) {
            return new Unchanged("construction material remains unqualified; selected ordinary work continues: " + unavailable.getMessage());
        }
    }
    private static ConstructionMaterialReducer.RefreshKind refreshKind(OrdinaryConstructionPolicy.Followup reason) {
        return switch (reason) {
            case COLD_MATERIAL -> ConstructionMaterialReducer.RefreshKind.COLD_MATERIAL;
            case COMPLETED_CASH -> ConstructionMaterialReducer.RefreshKind.COMPLETED_CASH;
            case COMPLETED_PROVINCE -> ConstructionMaterialReducer.RefreshKind.COMPLETED_PROVINCE;
            case MONTHLY_COMPLETION -> ConstructionMaterialReducer.RefreshKind.MONTHLY_COMPLETION;
        };
    }
    @Override public ExecutionDisposition afterExecution(ActionReceipt actual) {
        if (!actual.command().operation().equals(OrdinaryConstructionPolicy.OPERATION)) return new Unchanged("actual action is outside construction");
        try {
            var published = lifecycle.synchronizeOutcome(borrowed.current(), actual);
            return published.<ExecutionDisposition>map(ConstructionDomainLifecycle.Publication::completion)
                    .orElseGet(() -> new Unchanged("construction original outcome is already consumed"));
        } catch (IOException | IllegalArgumentException unavailable) {
            return new Blocked("construction outcome body publication failed; retain the original pending command: " + unavailable.getMessage(), List.of());
        }
    }
}
