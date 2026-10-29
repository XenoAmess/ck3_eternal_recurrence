package org.xar.ck3.control.application.planning.family;

import java.math.BigInteger;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Actual Root bindings, never a preselected family plan or an alternative writer. */
public final class FamilyPorts {
    private FamilyPorts() { }
    public enum Query {
        RULER_CHOICES("query-arrange-marriage-choices"),
        CURRENT_RELATION("query-current-first-heir-relationship-v1-private"),
        HEIR_LEGALITY("query-observed-first-heir-marriage-legality-v1"),
        HEIR_PROJECTION("query-first-heir-candidate-alliance-projection-v1-private"),
        CHILD_HOUSE_PREVIEW("read-family-obligations-private-12002"),
        FAMILY_RESULT("query-observed-first-heir-marriage-result-v1-private"),
        FAMILY_ALLIANCE("query-observed-first-heir-marriage-alliance-result-v1-private"),
        CHILD_SUBJECT("query-player-child-marriage-subject-v1-private"),
        CHILD_VALUE("query-player-child-marriage-value-v1-private"),
        MATRILINEAL_RESULT("query-player-child-matrilineal-marriage-result-v1-private"),
        MATRILINEAL_ALLIANCE("query-player-child-matrilineal-alliance-result-v1-private"),
        DEFAULT_RESULT("query-player-child-default-marriage-result-v1-private"),
        DEFAULT_ALLIANCE("query-player-child-default-alliance-result-v1-private"),
        CAMPAIGN_ROOT("query-campaign-root-context-v1"),
        CHILD_FOCUS("private-query-child-education-focus-v1"),
        CHILD_FOCUS_RECEIPT("private-query-child-education-focus-receipt-v1"),
        EDUCATION_CONTEXT("query-character-interaction-ordinary-v1");
        private final OperationKey operation;
        Query(String operation) { this.operation = new OperationKey(operation); }
        public OperationKey operation() { return operation; }
    }
    /** This catalog is supplied from the actual Root whitelist. Absence is unavailable. */
    public record Reads(Map<Query, ReadContract<Obj>> contracts, Map<Query, ProjectedSource> projections) {
        public Reads {
            contracts = Map.copyOf(contracts); projections = Map.copyOf(projections);
            contracts.forEach((query, contract) -> {
                Objects.requireNonNull(query); Objects.requireNonNull(contract);
                if (query == Query.EDUCATION_CONTEXT || query == Query.CAMPAIGN_ROOT || query == Query.HEIR_LEGALITY || query == Query.RULER_CHOICES)
                    throw new IllegalArgumentException("shared typed reads use their one actual projection source");
                if (!contract.operation().equals(query.operation())) throw new IllegalArgumentException("family read operation differs");
            });
            for (var binding : projections.entrySet()) {
                Objects.requireNonNull(binding.getKey()); Objects.requireNonNull(binding.getValue());
                if (contracts.containsKey(binding.getKey())) throw new IllegalArgumentException("family read has two producers");
            }
        }
        public Optional<ReadContract<Obj>> find(Query query) { return Optional.ofNullable(contracts.get(query)); }
        public Optional<ProjectedSource> projected(Query query) { return Optional.ofNullable(projections.get(query)); }
        public boolean available(Query query) { return projected(query).isPresent() || find(query).isPresent(); }
        public Obj decode(Query query, PlanningReadReceipt receipt) {
            if (!receipt.request().operation().equals(query.operation())) throw new IllegalArgumentException("family archived read operation differs");
            var projection = projected(query); if (projection.isPresent()) return projection.orElseThrow().decode(receipt);
            var contract = find(query).orElseThrow(() -> new IllegalArgumentException("actual family decoder absent"));
            if (!contract.contractId().equals(receipt.contractId())) throw new IllegalArgumentException("family archived contract differs");
            return contract.replay(receipt);
        }
    }
    /** Concrete adapters project one installed typed producer and replay its original receipt, without another native contract. */
    public interface ProjectedSource {
        ProjectedRead read(PlanningRequest request, Obj familyArguments);
        Obj decode(PlanningReadReceipt original);
    }
    public record ProjectedRead(Obj canonicalArguments, PlanningReadResult<Obj> result) {
        public ProjectedRead { Objects.requireNonNull(canonicalArguments); Objects.requireNonNull(result); }
    }
    public record BridgeIdentity(long pid, String creationDate) {
        public BridgeIdentity {
            if (pid <= 0 || creationDate == null || creationDate.isBlank()) throw new IllegalArgumentException("actual bridge identity required");
        }
        public boolean matches(Obj record, String prefix) {
            return record.get(prefix + "bridge_pid") instanceof org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue p
                    && p.value().equals(BigInteger.valueOf(pid))
                    && sameCreation(creationDate, record.get(prefix + "bridge_creation_date"));
        }
        private static boolean sameCreation(String current, org.xar.ck3.control.planning.opportunity.OpportunityJson.Value retained) {
            if (!(retained instanceof org.xar.ck3.control.planning.opportunity.OpportunityJson.Text text)) return false;
            if (current.equals(text.value())) return true;
            try { return org.xar.ck3.control.g2.m7.CheckpointContinuity.creationUtc(current).equals(org.xar.ck3.control.g2.m7.CheckpointContinuity.creationUtc(text.value())); }
            catch (IllegalArgumentException invalid) { return false; }
        }
    }
    public record Documents(Obj family, Obj matrilineal, Obj childDefault, BridgeIdentity bridge,
            ExactRef canonicalHead, java.util.List<ExactRef> importedDocuments) {
        public Documents {
            Objects.requireNonNull(family); Objects.requireNonNull(matrilineal); Objects.requireNonNull(childDefault);
            Objects.requireNonNull(bridge); Objects.requireNonNull(canonicalHead); importedDocuments = java.util.List.copyOf(importedDocuments);
            if (importedDocuments.size() != 3) throw new IllegalArgumentException("three original domain document refs required");
            for (Obj document : java.util.List.of(family, matrilineal, childDefault)) {
                for (String field : java.util.List.of("pending", "resolved")) {
                    var value = document.get(field);
                    if (value != org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE && !(value instanceof Obj))
                        throw new IllegalArgumentException("family ledger requires explicit nullable records");
                }
            }
        }
    }
    public sealed interface LedgerRead permits KnownDocuments, MissingDocuments { }
    public record KnownDocuments(Documents documents) implements LedgerRead { public KnownDocuments { Objects.requireNonNull(documents); } }
    public record MissingDocuments(String reason) implements LedgerRead {
        public MissingDocuments { if (reason == null || reason.isBlank()) throw new IllegalArgumentException("missing document reason"); }
    }
    @FunctionalInterface public interface LedgerSource { LedgerRead readCurrent(PlanningRequest request); }
    /** Borrows the already held original writer session; it never opens another lock scope. */
    @FunctionalInterface public interface CurrentSession { org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session current() throws java.io.IOException; }
    /** Actual preparation/postcondition binding is provided by the sole action coordinator. */
    @FunctionalInterface public interface Commands {
        Optional<ActionCommand> prepare(PlanningRequest request, OperationKey operation, Obj arguments, Obj completePlan);
    }
    /** Publishes a real read through the existing imported-document reducer under the sole writer. */
    @FunctionalInterface public interface MaterialResults {
        boolean consume(PlanningRequest request, Query query, Obj arguments, ObservedRead observed);
    }
    public record ObservedRead(Obj value, PlanningReadReceipt receipt, ExactRef originalReceipt) {
        public ObservedRead { Objects.requireNonNull(value); Objects.requireNonNull(receipt); Objects.requireNonNull(originalReceipt); }
    }
    public record Pair(BigInteger subject, BigInteger candidate) {
        public Pair {
            if (subject == null || candidate == null || subject.signum() <= 0 || candidate.signum() <= 0 || subject.equals(candidate))
                throw new IllegalArgumentException("distinct positive configured pair required");
        }
    }
    public record Settings(boolean familyEnabled, boolean fulfillCurrentBetrothal, boolean childFocusEnabled,
            boolean childDefaultEnabled, Optional<Pair> matrilinealPair) {
        public Settings { Objects.requireNonNull(matrilinealPair); }
    }
}
