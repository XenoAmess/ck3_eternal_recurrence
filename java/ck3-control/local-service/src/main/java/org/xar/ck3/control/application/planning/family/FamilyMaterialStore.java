package org.xar.ck3.control.application.planning.family;

import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import static org.xar.ck3.control.application.planning.family.FamilyPorts.*;
import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.continuity.writer.ImmutableArtifactStore;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Concrete actual-read -> reducer -> original-writer import, with a fresh same-lock replay. */
public final class FamilyMaterialStore implements MaterialResults {
    private static final int MAX = org.xar.ck3.control.continuity.ContinuityJson.DOMAIN_MAX_BYTES;
    private final CurrentSession sessions;
    private final ImmutableArtifactStore artifacts;
    private final ActionPorts.OutcomeArchive outcomes;
    private final FamilyDomainSource.CurrentBridge bridge;
    private final Reads reads;
    public FamilyMaterialStore(CurrentSession sessions, ImmutableArtifactStore artifacts, ActionPorts.OutcomeArchive outcomes,
            FamilyDomainSource.CurrentBridge bridge, Reads reads) {
        this.sessions = Objects.requireNonNull(sessions); this.artifacts = Objects.requireNonNull(artifacts);
        this.outcomes = Objects.requireNonNull(outcomes); this.bridge = Objects.requireNonNull(bridge); this.reads = Objects.requireNonNull(reads);
    }
    @Override public boolean consume(PlanningRequest request, Query query, Obj arguments, ObservedRead observed) {
        try {
            var session = sessions.current();
            var archive = outcomes.withSession(session);
            var current = bridge.observe(request);
            if (current.isEmpty() || !bridge.verifyRetained(observed.receipt(), current.get())) return false;
            Slot slot = slot(query); DomainBodies.Read read = session.readDomain(slot);
            if (!(read instanceof DomainBodies.Available existing)) return false;
            if (!observed.originalReceipt().equals(archive.readReferenceOf(observed.receipt()))) throw new IllegalArgumentException("material read is not the original archived receipt");
            Obj prior = FamilyDomainSource.validate(slot, existing.canonicalBody());
            byte[] next = canonical(reduce(query, prior, arguments, observed.value(), current.get().identity(), observed.receipt()));
            var body = artifacts.publish(next, MAX);
            Obj input = obj("schema", t("xar.java.family-result-reducer-input/v1"), "query", t(query.name()),
                    "read_receipt", ref(observed.originalReceipt()), "previous_body", ref(existing.reference().payload()),
                    "bridge_pid", n(current.get().identity().pid()), "bridge_creation_date", t(current.get().identity().creationDate()),
                    "bridge_evidence", ref(current.get().evidence()));
            var imported = new DomainBodies.ImportRequest(slot, FamilyDomainSource.schema(slot), body.reference(), canonical(input),
                    List.of(observed.originalReceipt(), current.get().evidence()), "family-read-" + observed.receipt().requestId());
            var prepared = session.previewImport(imported);
            session.commitImport(prepared); return true;
        } catch (IOException | IllegalArgumentException unavailable) { return false; }
    }
    /** Register this exact source closure in the sole DomainBodies registry; it cannot bootstrap missing ledgers. */
    public DomainBodies.Registration registration(Slot slot, List<ExactRef> actualProducerSources) {
        FamilyDomainSource.schema(slot);
        return new DomainBodies.Registration(slot, FamilyDomainSource.schema(slot), MAX, actualProducerSources, (head, previous, request, actualBody) -> {
            var retained = previous.orElseThrow(() -> new IllegalArgumentException("UNIMPORTED family body needs actual original-document import; no implicit empty ledger"));
            Obj input = decode(request.producerInput());
            if (!"xar.java.family-result-reducer-input/v1".equals(text(input.get("schema")))) throw new IllegalArgumentException("family reducer input schema");
            Query query = Query.valueOf(text(input.get("query")));
            if (slot(query) != slot || request.slot() != slot || !FamilyDomainSource.schema(slot).equals(request.contractSchema())) throw new IllegalArgumentException("family reducer slot changed");
            ExactRef prior = ExactRef.fromJson(OpportunityJson.toNode(input.get("previous_body")));
            if (!prior.equals(retained.payload())) throw new IllegalArgumentException("family body predecessor changed");
            ExactRef receiptRef = ExactRef.fromJson(OpportunityJson.toNode(input.get("read_receipt")));
            ExactRef bridgeRef = ExactRef.fromJson(OpportunityJson.toNode(input.get("bridge_evidence")));
            if (!request.evidence().containsAll(List.of(receiptRef, bridgeRef))) throw new IllegalArgumentException("original read/Bridge evidence missing");
            var archive = outcomes.withSession(sessions.current());
            var receipt = archive.loadRead(receiptRef);
            if (!receiptRef.equals(archive.readReferenceOf(receipt)) || !receipt.request().before().machineId().equals(head.machineId())
                    || !receipt.request().operation().equals(query.operation())) throw new IllegalArgumentException("family reducer original read source changed");
            var identity = new BridgeIdentity(positive(input.get("bridge_pid")).longValueExact(), text(input.get("bridge_creation_date")));
            if (!bridge.verifyRetained(receipt, new FamilyDomainSource.BridgeObservation(identity, bridgeRef))) throw new IllegalArgumentException("retained Bridge evidence unqualified");
            Obj actualResult = reads.decode(query, receipt);
            Obj previousBody = FamilyDomainSource.validate(slot, artifacts.read(prior, MAX));
            Obj next = reduce(query, previousBody, receipt.request().arguments(), actualResult, identity, receipt);
            FamilyDomainSource.validate(slot, actualBody);
            if (!Arrays.equals(canonical(next), actualBody)) throw new IllegalArgumentException("family import body differs from actual reducer replay");
            return ActionCodec.sha256(canonical(obj("actual_head_digest", t(org.xar.ck3.control.continuity.ContinuityJson.digest(head.toJson())), "input", input, "output_sha256", t(ActionCodec.sha256(actualBody)))));
        });
    }
    private static Obj reduce(Query query, Obj ledger, Obj arguments, Obj result, BridgeIdentity bridge,
            org.xar.ck3.control.application.action.PlanningReadReceipt receipt) {
        var frame = receipt.request().before().frame();
        if (query == Query.CURRENT_RELATION)
            return FamilyResultReducer.matureWarm(ledger, result, bridge, frame.episodeRunId(), frame.identity().nativeRevision());
        return FamilyResultReducer.reduce(query, ledger, arguments, result, bridge, frame.identity().dateRaw());
    }
    private static Slot slot(Query query) {
        return switch (query) {
            case CURRENT_RELATION, FAMILY_RESULT, FAMILY_ALLIANCE -> Slot.FAMILY;
            case MATRILINEAL_RESULT, MATRILINEAL_ALLIANCE -> Slot.CHILD_MATRILINEAL;
            case DEFAULT_RESULT, DEFAULT_ALLIANCE -> Slot.DEFAULT_MARRIAGE;
            default -> throw new IllegalArgumentException("not a family material read");
        };
    }
    private static Obj ref(ExactRef reference) { return object(OpportunityJson.parse(reference.toJson().toString().getBytes(java.nio.charset.StandardCharsets.UTF_8))); }
    private static byte[] canonical(Obj value) { return org.xar.ck3.control.continuity.ContinuityJson.canonical(OpportunityJson.toNode(value), MAX); }
}
