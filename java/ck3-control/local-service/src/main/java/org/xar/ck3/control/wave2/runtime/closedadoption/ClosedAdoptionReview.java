package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.security.SecureRandom;
import java.time.Instant;
import java.util.HexFormat;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;

/** Small review bindings only; the owning Main retains actual measurement and one-shot state. */
public final class ClosedAdoptionReview {
    private ClosedAdoptionReview() { }
    public enum Decision {
        APPROVE("approve"), DECLINE("decline");
        private final String wire;
        Decision(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Decision decode(String value) {
            StrictJson.require("approve".equals(value) || "decline".equals(value), "fixed Root review decision");
            return "approve".equals(value) ? APPROVE : DECLINE;
        }
    }
    public record Plan(String machineId, ExactRef ticketRef, String ticketNonce,
            OriginalWriterTransaction.Target target, ExactRef predecessorRef,
            FileStatIdentity predecessorIdentity, Instant deadlineUtc) {
        public Plan {
            StrictJson.text(machineId); Objects.requireNonNull(ticketRef); nonce(ticketNonce);
            Objects.requireNonNull(target); Objects.requireNonNull(predecessorRef);
            Objects.requireNonNull(predecessorIdentity); Objects.requireNonNull(deadlineUtc);
            Path canonical = target.canonicalPath();
            StrictJson.require(canonical.isAbsolute() && canonical.normalize().equals(canonical)
                    && Path.of(predecessorRef.path()).equals(canonical), "normalized production target and its actual predecessor");
            StrictJson.require(predecessorIdentity.bytes().equals(java.math.BigInteger.valueOf(predecessorRef.bytes())),
                    "production predecessor identity size");
        }
        public ObjectNode toJson() {
            ObjectNode row = StrictJson.object(); row.put("schema", "xar.closed-adoption-review-plan/v1");
            row.put("machine_id", machineId); row.set("ticket_ref", ticketRef.toJson()); row.put("ticket_nonce", ticketNonce);
            ObjectNode destination = row.putObject("target"); destination.put("canonical_path", target.canonicalPath().toString());
            destination.set("writer_source_ref", target.originalWriter().toJson());
            row.set("predecessor_ref", predecessorRef.toJson()); row.set("predecessor_identity", predecessorIdentity.toJson());
            row.put("deadline_utc", deadlineUtc.toString()); return row;
        }
        public static Plan decode(byte[] raw) { return fromJson(StrictJson.parse(raw)); }
        private static Plan fromJson(JsonNode value) {
            ObjectNode row = StrictJson.object(value, Set.of("schema", "machine_id", "ticket_ref", "ticket_nonce",
                    "target", "predecessor_ref", "predecessor_identity", "deadline_utc"));
            schema(row, "xar.closed-adoption-review-plan/v1");
            ObjectNode destination = StrictJson.object(row.get("target"), Set.of("canonical_path", "writer_source_ref"));
            var target = new OriginalWriterTransaction.Target(Path.of(text(destination, "canonical_path")),
                    ExactRef.fromJson(destination.get("writer_source_ref")));
            return new Plan(text(row, "machine_id"), ExactRef.fromJson(row.get("ticket_ref")), text(row, "ticket_nonce"), target,
                    ExactRef.fromJson(row.get("predecessor_ref")), FileStatIdentity.fromJson(row.get("predecessor_identity"),
                    FileStatIdentity.SCHEMA), instant(row, "deadline_utc"));
        }
    }
    public record Challenge(Plan plan, ExactRef temporaryResultRef, String nonce, Instant issuedAtUtc) {
        public Challenge {
            Objects.requireNonNull(plan); Objects.requireNonNull(temporaryResultRef); Objects.requireNonNull(issuedAtUtc);
            ClosedAdoptionReview.nonce(nonce);
            StrictJson.require(issuedAtUtc.isBefore(plan.deadlineUtc()), "finite review window");
        }
        public ObjectNode toJson() {
            ObjectNode row = StrictJson.object(); row.put("schema", "xar.closed-adoption-review-challenge/v1");
            row.set("plan", plan.toJson()); row.set("temporary_result_ref", temporaryResultRef.toJson());
            row.put("nonce", nonce); row.put("issued_at_utc", issuedAtUtc.toString()); return row;
        }
        public static Challenge decode(byte[] raw) { return fromJson(StrictJson.parse(raw)); }
        private static Challenge fromJson(JsonNode value) {
            ObjectNode row = StrictJson.object(value, Set.of("schema", "plan", "temporary_result_ref", "nonce", "issued_at_utc"));
            schema(row, "xar.closed-adoption-review-challenge/v1");
            return new Challenge(Plan.fromJson(row.get("plan")), ExactRef.fromJson(row.get("temporary_result_ref")),
                    text(row, "nonce"), instant(row, "issued_at_utc"));
        }
    }
    public record Approval(Challenge challenge, Decision decision, Instant approvedAtUtc) {
        public Approval {
            Objects.requireNonNull(challenge); Objects.requireNonNull(decision); Objects.requireNonNull(approvedAtUtc);
        }
        public ObjectNode toJson() {
            ObjectNode row = StrictJson.object(); row.put("schema", "xar.closed-adoption-root-review/v1");
            row.set("challenge", challenge.toJson()); row.put("decision", decision.wire());
            row.put("approved_at_utc", approvedAtUtc.toString()); return row;
        }
        public static Approval decode(byte[] raw) {
            ObjectNode row = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "challenge", "decision", "approved_at_utc"));
            schema(row, "xar.closed-adoption-root-review/v1");
            return new Approval(Challenge.fromJson(row.get("challenge")), Decision.decode(text(row, "decision")),
                    instant(row, "approved_at_utc"));
        }
    }
    /** Call only after publishing and rereading the temporary result; do not deserialize measured authority. */
    public static Challenge createChallenge(Plan plan, ExactRef temporaryResultRef, String actualMachineId,
            ExactRef actualTicketRef, String actualTicketNonce, Instant ticketReviewAt, Instant invocationDeadline, Instant now) {
        Objects.requireNonNull(plan); Objects.requireNonNull(now); Objects.requireNonNull(ticketReviewAt);
        Objects.requireNonNull(invocationDeadline); nonce(actualTicketNonce);
        StrictJson.require(plan.machineId().equals(actualMachineId) && plan.ticketRef().equals(actualTicketRef)
                && plan.ticketNonce().equals(actualTicketNonce), "actual owning machine and same measured ticket and nonce");
        StrictJson.require(!plan.deadlineUtc().isAfter(ticketReviewAt) && !plan.deadlineUtc().isAfter(invocationDeadline)
                && now.isBefore(plan.deadlineUtc()), "earliest existing finite lease");
        byte[] random = new byte[16]; new SecureRandom().nextBytes(random);
        return new Challenge(plan, temporaryResultRef, HexFormat.of().formatHex(random), now);
    }
    /** Both decisions require every binding; this does not consume the owning session's one-shot state. */
    public static Decision validateApproval(Challenge expected, Approval supplied, Instant now) {
        Objects.requireNonNull(expected); Objects.requireNonNull(supplied); Objects.requireNonNull(now);
        StrictJson.require(expected.equals(supplied.challenge()), "Root decision binds the complete issued challenge");
        StrictJson.require(!supplied.approvedAtUtc().isBefore(expected.issuedAtUtc()) && !supplied.approvedAtUtc().isAfter(now)
                && now.isBefore(expected.plan().deadlineUtc()), "issued <= approved <= current time < same review deadline");
        return supplied.decision();
    }
    public static Path approvalPath(Path actualTicketOutputRoot) {
        Objects.requireNonNull(actualTicketOutputRoot);
        StrictJson.require(actualTicketOutputRoot.isAbsolute() && actualTicketOutputRoot.normalize().equals(actualTicketOutputRoot),
                "actual normalized ticket output root");
        return actualTicketOutputRoot.resolve("root-review-approval.json");
    }
    private static void nonce(String value) {
        StrictJson.require(value != null && value.matches("[0-9a-f]{32}"), "32 lowercase hexadecimal nonce");
    }
    private static String text(ObjectNode row, String field) { return StrictJson.text(row.get(field)); }
    private static Instant instant(ObjectNode row, String field) { return Instant.parse(StrictJson.utc(text(row, field))); }
    private static void schema(ObjectNode row, String expected) {
        StrictJson.require(expected.equals(text(row, "schema")), "review schema");
    }
}
