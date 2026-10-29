package org.xar.ck3.control.application.action.council;

import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** One original Council action and its immutable, separately durable continuation requests. */
public final class CouncilContinuationModel {
    public static final String SCHEMA = "xar.java-council-continuations/v1";
    public static final int MAX_BODY_BYTES = 1_048_576;
    public static final int MAX_ACTIVE_REQUESTS = 1024;
    private CouncilContinuationModel() { }
    public enum Stage {
        HELPER_STATUS("private-council-application-main-status-v1"),
        RECEIPT_QUERY("private-query-assign-councillor-receipt-v1"),
        RECEIPT_STATUS("private-council-application-main-status-v1");
        private final String step;
        Stage(String step) { this.step = step; }
        public String step() { return step; }
    }
    public enum Status { ISSUED, ACK, UNKNOWN }
    public record Scope(String parentActionId, String parentBodySha256, String originalAttemptRequestId) {
        public Scope { StrictJson.text(parentActionId); digest(parentBodySha256); StrictJson.text(originalAttemptRequestId); }
    }
    public record Request(Scope scope, String requestId, Stage stage, ExactRef originalParentReceipt,
            ExactRef preparedRequest, GuardEvidence guard, Instant issuedAt, Instant deadline,
            long issuedSequence, List<ExactRef> supportingEvidence) {
        public Request {
            Objects.requireNonNull(scope); StrictJson.text(requestId); Objects.requireNonNull(stage);
            Objects.requireNonNull(originalParentReceipt); Objects.requireNonNull(preparedRequest); Objects.requireNonNull(guard);
            Objects.requireNonNull(issuedAt); Objects.requireNonNull(deadline); StrictJson.safe(issuedSequence, 1);
            StrictJson.require(issuedAt.isBefore(deadline) && !requestId.equals(scope.originalAttemptRequestId()), "fresh bounded continuation request required");
            supportingEvidence = List.copyOf(supportingEvidence);
            StrictJson.require(!supportingEvidence.isEmpty() && supportingEvidence.size() <= 48, "complete bounded Council preflight/source evidence required");
            StrictJson.require(new java.util.HashSet<>(supportingEvidence).size() == supportingEvidence.size(), "continuation evidence cannot repeat a reference");
        }
    }
    public record IssuedCustody(ExactRef record, ExactRef domainPayload, ExactRef event) {
        public IssuedCustody { Objects.requireNonNull(record); Objects.requireNonNull(domainPayload); Objects.requireNonNull(event); }
    }
    public record Entry(Request request, Status status, Optional<ExactRef> outcome, Optional<IssuedCustody> issued, long resultSequence) {
        public Entry {
            Objects.requireNonNull(request); Objects.requireNonNull(status); Objects.requireNonNull(outcome); Objects.requireNonNull(issued);
            StrictJson.require((status == Status.ISSUED) == (outcome.isEmpty() && issued.isEmpty()), "continuation result keeps its exact issued custody and original outcome");
            if (status != Status.ISSUED) StrictJson.require(outcome.isPresent() && issued.isPresent(), "resolved/unknown continuation needs original custody");
            StrictJson.safe(resultSequence, 0); StrictJson.require((status == Status.ISSUED) == (resultSequence == 0), "only an actual result records its expected canonical sequence");
            StrictJson.require(status == Status.ISSUED || resultSequence > request.issuedSequence(), "result must follow its original issued event");
        }
    }
    public record Retained(ExactRef reference, Entry entry) {
        public Retained { Objects.requireNonNull(reference); Objects.requireNonNull(entry); }
        public Request request() { return entry.request(); }
        public Status status() { return entry.status(); }
    }
    public record State(String machineId, Optional<Scope> active, List<ExactRef> records, Optional<ExactRef> completedScopeChain) {
        public State {
            StrictJson.text(machineId); Objects.requireNonNull(active); records = List.copyOf(records); Objects.requireNonNull(completedScopeChain);
            StrictJson.require(records.size() <= MAX_ACTIVE_REQUESTS && (active.isPresent() || records.isEmpty()), "bounded explicit active continuation scope required");
            StrictJson.require(new java.util.HashSet<>(records).size() == records.size(), "continuation manifest cannot repeat an immutable row");
        }
    }
    static void digest(String value) { StrictJson.require(value != null && value.matches("[0-9a-f]{64}"), "canonical action body SHA required"); }
}
