package org.xar.ck3.control.governance.council;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.OptionalInt;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.governance.council.CouncilCodec.*;
import static org.xar.ck3.control.governance.council.CouncilModels.*;

/** Council22 native helper invocation and later incumbent material are different typed states. */
public final class CouncilActionCodec {
    private CouncilActionCodec() { }
    public static final String PRIVATE_ASSIGN = "private-assign-councillor-v1";
    public static final String ASSIGN = "assign-councillor-v1";
    public static final String PRIVATE_RECEIPT = "private-query-assign-councillor-receipt-v1";
    public static final String RECEIPT = "query-assign-councillor-receipt-v1";
    private static final Set<String> ACK_FIELDS = Set.of("status", "failure", "action_request_id", "pre_snapshot_id", "pre_public_revision", "pre_native_revision", "pre_date_raw", "owner_character_id", "position_key", "active_task_id", "candidate_character_id", "had_incumbent", "previous_incumbent_character_id", "route", "native_helper_invoked", "queue_acceptance_observed", "verification_pending", "native_reason_key");
    private static final Set<String> RECEIPT_FIELDS = Set.of("status", "rejected_action_failure", "action_request_id", "post_snapshot_id", "post_public_revision", "post_native_revision", "post_date_raw", "owner_character_id", "position_key", "incumbent_character_id", "incumbent_identity_round_trip", "postcondition_verified", "reason");
    private static final Set<String> FAILURES = Set.of("none", "request_contract_invalid", "exact_build_mismatch", "private_candidate_not_admitted", "application_main_thread_required", "callbacks_unavailable", "observation_unavailable", "not_paused", "snapshot_binding_mismatch", "position_outside_coverage", "active_task_identity_unavailable", "incumbent_identity_unavailable", "candidate_equals_incumbent", "final_legality_unavailable", "candidate_not_in_exact_collection", "candidate_identity_mismatch", "candidate_already_councillor", "candidate_is_guest", "pending_character_interaction", "incumbent_cannot_be_replaced", "state_changed_before_submit", "native_helper_not_invoked");
    public record Request(String requestId, Frame frame, Position position, int candidateId, OptionalInt incumbentId) {
        public Request {
            token(requestId, false); Objects.requireNonNull(frame); Objects.requireNonNull(position); Objects.requireNonNull(incumbentId);
            positive(frame.ownerId()); positive(candidateId); incumbentId.ifPresent(CouncilActionCodec::positive);
            StrictJson.require(position != Position.SPYMASTER && (!incumbentId.isPresent() || incumbentId.orElseThrow() != candidateId), "Council action role/incumbent outside original coverage");
            token(frame.snapshotId(), false);
        }
    }
    public enum AckStatus { HELPER_INVOKED_VERIFICATION_PENDING, REJECTED_BEFORE_SUBMIT }
    /** The native catch and retained prior assignment cannot release the current held mailbox. */
    public enum HelperDisposition { INVOCATION_PENDING, REJECTED_WITHOUT_INVOCATION, DISPATCH_UNRESOLVED, PRIOR_ASSIGNMENT_UNRESOLVED }
    public record Ack(AckStatus status, String failure, Request request, int activeTaskId, boolean helperInvoked,
            boolean queueAcceptanceObserved, boolean verificationPending, String nativeReason, JsonBody original) {
        public Ack { Objects.requireNonNull(status); Objects.requireNonNull(failure); Objects.requireNonNull(request); Objects.requireNonNull(nativeReason); Objects.requireNonNull(original); }
        /** Called only after decodeAck has validated the entire native original and request binding. */
        public HelperDisposition disposition() {
            if (status == AckStatus.HELPER_INVOKED_VERIFICATION_PENDING) return HelperDisposition.INVOCATION_PENDING;
            if (nativeReason.equals("action_executor_exception")) return HelperDisposition.DISPATCH_UNRESOLVED;
            if (nativeReason.equals("pending_assignment_unresolved")) return HelperDisposition.PRIOR_ASSIGNMENT_UNRESOLVED;
            return HelperDisposition.REJECTED_WITHOUT_INVOCATION;
        }
    }
    public enum ReceiptStatus { APPLIED, POSTCONDITION_FAILED, REJECTED }
    public record Receipt(ReceiptStatus status, Ack ack, String failure, String postSnapshotId, BigInteger postPublicRevision,
            BigInteger postNativeRevision, int postDateRaw, int ownerId, Position position, int incumbentId,
            boolean incumbentRoundTrip, boolean verified, String reason, JsonBody original) {
        public Receipt { Objects.requireNonNull(status); Objects.requireNonNull(ack); Objects.requireNonNull(postSnapshotId); Objects.requireNonNull(postPublicRevision); Objects.requireNonNull(postNativeRevision); Objects.requireNonNull(position); Objects.requireNonNull(original); }
    }
    public static Request request(Candidates candidates, int candidateId, String requestId) {
        StrictJson.require(candidates.candidates().stream().filter(row -> row.characterId() == candidateId).count() == 1, "selected Council candidate is outside the exact native collection");
        return new Request(requestId, candidates.frame(), candidates.seat().position(), candidateId, candidates.seat().incumbentId());
    }
    public static ObjectNode wireFields(Request request, boolean privateRoute) {
        ObjectNode fields = StrictJson.object().put("candidate_character_id", request.candidateId());
        if (privateRoute) return fields;
        return fields.put("position_key", request.position().key()).put("expected_snapshot_id", request.frame().snapshotId())
                .put("expected_public_revision", request.frame().publicRevision()).put("expected_native_revision", request.frame().nativeRevision())
                .put("expected_date_raw", request.frame().dateRaw()).put("expected_owner_character_id", request.frame().ownerId())
                .put("expected_has_incumbent", request.incumbentId().isPresent())
                .put("expected_incumbent_character_id", request.incumbentId().orElse(-1));
    }
    public static Ack decodeAck(byte[] bytes, Request request) {
        ObjectNode value = StrictJson.object(StrictJson.parse(bytes), ACK_FIELDS);
        String failure = text(value, "failure"); StrictJson.require(FAILURES.contains(failure), "unknown Council ACK failure");
        StrictJson.require(tokenText(value, "action_request_id", false).equals(request.requestId())
                && text(value, "position_key").equals(request.position().key())
                && number(value, "candidate_character_id", 1, Integer.MAX_VALUE) == request.candidateId(), "Council ACK request identity drift");
        boolean helper = bool(value.get("native_helper_invoked")), queued = bool(value.get("queue_acceptance_observed")), pending = bool(value.get("verification_pending"));
        boolean had = bool(value.get("had_incumbent")); int previous = (int) number(value, "previous_incumbent_character_id", Integer.MIN_VALUE, Integer.MAX_VALUE);
        String reason = tokenText(value, "native_reason_key", true); int active = (int) number(value, "active_task_id", Integer.MIN_VALUE, Integer.MAX_VALUE);
        AckStatus status;
        if (text(value, "status").equals("native_helper_invoked_verification_pending")) {
            Frame frame = request.frame();
            StrictJson.require(failure.equals("none") && text(value, "pre_snapshot_id").equals(frame.snapshotId())
                    && u64(value.get("pre_public_revision"), true).equals(frame.publicRevision())
                    && u64(value.get("pre_native_revision"), true).equals(frame.nativeRevision())
                    && number(value, "pre_date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE) == frame.dateRaw()
                    && number(value, "owner_character_id", 1, Integer.MAX_VALUE) == frame.ownerId() && active > 0
                    && had == request.incumbentId().isPresent() && previous == request.incumbentId().orElse(-1)
                    && text(value, "route").equals(had ? "replace_incumbent" : "assign_vacant")
                    && helper && !queued && pending && reason.isEmpty(), "Council helper ACK is internally inconsistent");
            status = AckStatus.HELPER_INVOKED_VERIFICATION_PENDING;
        } else {
            StrictJson.require(text(value, "status").equals("rejected_before_submit") && !failure.equals("none")
                    && emptyText(value.get("pre_snapshot_id")).isEmpty() && u64(value.get("pre_public_revision"), false).signum() == 0
                    && u64(value.get("pre_native_revision"), false).signum() == 0 && number(value, "pre_date_raw", 0, 0) == 0
                    && number(value, "owner_character_id", -1, -1) == -1 && active == -1 && !had && previous == -1
                    && text(value, "route").equals("none") && !helper && !queued && !pending, "Council rejected ACK is inconsistent or not a rejection");
            StrictJson.require(!reason.equals("action_executor_exception") || failure.equals("native_helper_not_invoked"),
                    "Council executor exception crossed its actual native failure route");
            StrictJson.require(!reason.equals("pending_assignment_unresolved") || failure.equals("callbacks_unavailable"),
                    "Council retained prior assignment crossed its actual native failure route");
            status = AckStatus.REJECTED_BEFORE_SUBMIT;
        }
        return new Ack(status, failure, request, active, helper, queued, pending, reason, new JsonBody(bytes));
    }
    public static Receipt decodeReceipt(byte[] bytes, Ack ack) {
        ObjectNode value = StrictJson.object(StrictJson.parse(bytes), RECEIPT_FIELDS);
        String failure = text(value, "rejected_action_failure"); StrictJson.require(FAILURES.contains(failure), "unknown Council receipt failure");
        StrictJson.require(tokenText(value, "action_request_id", false).equals(ack.request().requestId()), "Council receipt lost original request identity");
        String snapshot = emptyText(value.get("post_snapshot_id")), reason = tokenText(value, "reason", true);
        BigInteger pub = u64(value.get("post_public_revision"), false), nat = u64(value.get("post_native_revision"), false);
        int date = (int) number(value, "post_date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE), owner = (int) number(value, "owner_character_id", Integer.MIN_VALUE, Integer.MAX_VALUE);
        int incumbent = (int) number(value, "incumbent_character_id", Integer.MIN_VALUE, Integer.MAX_VALUE);
        Position role = Position.exact(text(value, "position_key"));
        boolean roundTrip = bool(value.get("incumbent_identity_round_trip")), verified = bool(value.get("postcondition_verified"));
        ReceiptStatus status;
        switch (text(value, "status")) {
            case "applied" -> {
                Frame pre = ack.request().frame(); token(snapshot, false);
                StrictJson.require(ack.status() == AckStatus.HELPER_INVOKED_VERIFICATION_PENDING && failure.equals("none")
                        && !snapshot.equals(pre.snapshotId()) && pub.compareTo(pre.publicRevision()) > 0 && nat.compareTo(pre.nativeRevision()) > 0
                        && date >= pre.dateRaw() && owner == pre.ownerId() && role == ack.request().position()
                        && incumbent == ack.request().candidateId() && roundTrip && verified && reason.isEmpty(), "Council applied receipt lacks independent incumbent material");
                status = ReceiptStatus.APPLIED;
            }
            case "postcondition_failed" -> {
                StrictJson.require(ack.status() == AckStatus.HELPER_INVOKED_VERIFICATION_PENDING && failure.equals("none") && !verified
                        && Set.of("invalid_ack", "post_observation_unavailable", "no_new_paused_frame", "owner_or_position_changed", "active_task_changed", "candidate_not_observed_as_incumbent").contains(reason), "Council failed postcondition receipt is inconsistent");
                status = ReceiptStatus.POSTCONDITION_FAILED;
            }
            case "rejected" -> {
                StrictJson.require(ack.status() == AckStatus.REJECTED_BEFORE_SUBMIT && failure.equals(ack.failure()) && !verified && reason.equals("action_rejected"), "Council rejected receipt is inconsistent");
                status = ReceiptStatus.REJECTED;
            }
            default -> throw new IllegalArgumentException("unknown Council receipt state");
        }
        return new Receipt(status, ack, failure, snapshot, pub, nat, date, owner, role, incumbent, roundTrip, verified, reason, new JsonBody(bytes));
    }
    private static void positive(int value) { StrictJson.require(value > 0, "original Council22 action requires positive int32 identity"); }
    private static String tokenText(ObjectNode value, String field, boolean empty) { String result = emptyText(value.get(field)); token(result, empty); return result; }
    private static void token(String value, boolean empty) { StrictJson.require(value != null && (empty && value.isEmpty() || value.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,63}")), "Council bounded native token required"); }
    private static String emptyText(JsonNode value) { StrictJson.require(value != null && value.isTextual(), "exact native string required"); return value.textValue(); }
}
