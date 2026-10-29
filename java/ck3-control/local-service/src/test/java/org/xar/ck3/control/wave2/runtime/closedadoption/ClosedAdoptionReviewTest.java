package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure contract fixtures: no file reads/writes, processes, SDK measurements, or observed machine facts. */
class ClosedAdoptionReviewTest {
    private static final Path ROOT = Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize()
            .resolve("closedadoption-contract-fixture");
    private static final String MACHINE = "synthetic-contract-fixture";
    private static final String TICKET_NONCE = "0123456789abcdef0123456789abcdef";
    private static final Instant ISSUED = Instant.parse("2026-10-22T15:00:00Z");
    private static final Instant DEADLINE = ISSUED.plusSeconds(60);
    private static ExactRef ref(String relative) { return new ExactRef(ROOT.resolve(relative).toString(),17,"a".repeat(64)); }
    private static ClosedAdoptionReview.Plan plan() {
        ExactRef predecessor = ref("production/ROOT-CONTINUITY-WINDOW.json");
        return new ClosedAdoptionReview.Plan(MACHINE, ref("ticket.json"), TICKET_NONCE,
                new OriginalWriterTransaction.Target(Path.of(predecessor.path()), ref("original-writer.py")), predecessor,
                new FileStatIdentity(BigInteger.valueOf(17),"18446744073709551615","1720000000000000000"),DEADLINE);
    }
    private static ClosedAdoptionReview.Challenge challenge() {
        return ClosedAdoptionReview.createChallenge(plan(),ref("closed-adoption-result.json"),MACHINE,ref("ticket.json"),
                TICKET_NONCE,DEADLINE,DEADLINE,ISSUED);
    }
    private static ClosedAdoptionReview.Approval approval(ClosedAdoptionReview.Challenge challenge,
            ClosedAdoptionReview.Decision decision) {
        return new ClosedAdoptionReview.Approval(challenge,decision,ISSUED.plusSeconds(1));
    }
    private static ObjectNode object(ObjectNode row, String field) { return (ObjectNode) row.get(field); }
    private static ObjectNode challenge(ObjectNode row) { return object(row,"challenge"); }
    private static ObjectNode plan(ObjectNode row) { return object(challenge(row),"plan"); }
    private static ClosedAdoptionReview.Approval decode(ObjectNode row) {
        return ClosedAdoptionReview.Approval.decode(StrictJson.canonical(row));
    }
    @Test void bothDecisionsRoundTripAndValidateTheFullIssuedChallenge() {
        var expected = challenge();
        assertEquals(expected.plan(),ClosedAdoptionReview.Plan.decode(StrictJson.canonical(expected.plan().toJson())));
        assertEquals(expected,ClosedAdoptionReview.Challenge.decode(StrictJson.canonical(expected.toJson())));
        for (var decision : ClosedAdoptionReview.Decision.values()) {
            var supplied = approval(expected,decision);
            assertEquals(supplied,decode(supplied.toJson()));
            assertEquals(decision,ClosedAdoptionReview.validateApproval(expected,decode(supplied.toJson()),ISSUED.plusSeconds(2)));
        }
    }
    @Test void approveAndDeclineBothRejectEveryChangedBinding() {
        var expected = challenge();
        List<Consumer<ObjectNode>> mutations = List.of(
                row -> plan(row).put("machine_id","other-synthetic-machine"),
                row -> object(plan(row),"ticket_ref").put("sha256","b".repeat(64)),
                row -> plan(row).put("ticket_nonce","f".repeat(32)),
                row -> object(plan(row),"target").put("canonical_path",ROOT.resolve("other-head.json").toString()),
                row -> object(object(plan(row),"target"),"writer_source_ref").put("sha256","b".repeat(64)),
                row -> object(plan(row),"predecessor_ref").put("sha256","b".repeat(64)),
                row -> object(plan(row),"predecessor_identity").put("file_id","18446744073709551614"),
                row -> object(plan(row),"predecessor_identity").put("mtime_ns","1720000000000000001"),
                row -> plan(row).put("deadline_utc",DEADLINE.plusSeconds(1).toString()),
                row -> object(challenge(row),"temporary_result_ref").put("sha256","b".repeat(64)),
                row -> challenge(row).put("nonce",expected.nonce().equals("f".repeat(32)) ? "e".repeat(32) : "f".repeat(32)),
                row -> challenge(row).put("issued_at_utc",ISSUED.minusSeconds(1).toString()));
        for (var decision : ClosedAdoptionReview.Decision.values()) {
            for (var mutation : mutations) {
                ObjectNode row = approval(expected,decision).toJson(); mutation.accept(row);
                assertThrows(ContractViolationException.class, () ->
                        ClosedAdoptionReview.validateApproval(expected,decode(row),ISSUED.plusSeconds(2)));
            }
        }
    }
    @Test void rejectsWrongMissingNullAndExtraWireFields() {
        var expected = challenge();
        List<Consumer<ObjectNode>> mutations = List.of(
                row -> row.put("decision","yes"), row -> row.put("decision",true),
                row -> row.remove("decision"), row -> row.putNull("challenge"),
                row -> row.put("schema","unsupported"), row -> row.put("approved_at_utc",true),
                row -> row.put("approval_path",ROOT.resolve("alternate.json").toString()),
                row -> plan(row).put("approved",true),
                row -> plan(row).put("ticket_nonce","ABCDEF0123456789ABCDEF0123456789"),
                row -> challenge(row).put("nonce","short"),
                row -> object(plan(row),"ticket_ref").put("bytes",true),
                row -> object(plan(row),"predecessor_identity").put("file_id",1844674407370955161L));
        for (var mutation : mutations) {
            ObjectNode row = approval(expected,ClosedAdoptionReview.Decision.APPROVE).toJson(); mutation.accept(row);
            assertThrows(ContractViolationException.class, () -> decode(row));
        }
    }
    @Test void numericFloatTokensAreRejectedAtTheActualWireDecoder() {
        byte[] valid = StrictJson.canonical(approval(challenge(),ClosedAdoptionReview.Decision.APPROVE).toJson());
        String wire = new String(valid,StandardCharsets.UTF_8).replace("\"bytes\":17", "\"bytes\":17.0");
        assertNotEquals(new String(valid,StandardCharsets.UTF_8),wire);
        assertThrows(ContractViolationException.class, () ->
                ClosedAdoptionReview.Approval.decode(wire.getBytes(StandardCharsets.UTF_8)));
    }
    @Test void decisionsRequireIssuedApprovedNowOrderingAndUnexpiredDeadline() {
        var expected = challenge();
        for (var decision : ClosedAdoptionReview.Decision.values()) {
            assertThrows(ContractViolationException.class, () -> ClosedAdoptionReview.validateApproval(expected,
                    new ClosedAdoptionReview.Approval(expected,decision,ISSUED.minusNanos(1)),ISSUED.plusSeconds(2)));
            assertThrows(ContractViolationException.class, () -> ClosedAdoptionReview.validateApproval(expected,
                    new ClosedAdoptionReview.Approval(expected,decision,ISSUED.plusSeconds(3)),ISSUED.plusSeconds(2)));
            assertThrows(ContractViolationException.class, () ->
                    ClosedAdoptionReview.validateApproval(expected,approval(expected,decision),DEADLINE));
            assertEquals(decision,ClosedAdoptionReview.validateApproval(expected,
                    new ClosedAdoptionReview.Approval(expected,decision,ISSUED),ISSUED));
        }
    }
    @Test void issuingBindsActualMachineTicketNonceAndTheEarliestExistingLease() {
        var plan = plan(); ExactRef temporary = ref("closed-adoption-result.json");
        assertThrows(ContractViolationException.class, () -> ClosedAdoptionReview.createChallenge(plan,temporary,
                "other-machine",ref("ticket.json"),TICKET_NONCE,DEADLINE,DEADLINE,ISSUED));
        assertThrows(ContractViolationException.class, () -> ClosedAdoptionReview.createChallenge(plan,temporary,
                MACHINE,ref("other-ticket.json"),TICKET_NONCE,DEADLINE,DEADLINE,ISSUED));
        assertThrows(ContractViolationException.class, () -> ClosedAdoptionReview.createChallenge(plan,temporary,
                MACHINE,ref("ticket.json"),"f".repeat(32),DEADLINE,DEADLINE,ISSUED));
        assertThrows(ContractViolationException.class, () -> ClosedAdoptionReview.createChallenge(plan,temporary,
                MACHINE,ref("ticket.json"),TICKET_NONCE,DEADLINE.minusNanos(1),DEADLINE,ISSUED));
        assertThrows(ContractViolationException.class, () -> ClosedAdoptionReview.createChallenge(plan,temporary,
                MACHINE,ref("ticket.json"),TICKET_NONCE,DEADLINE,DEADLINE.minusNanos(1),ISSUED));
        assertThrows(ContractViolationException.class, () -> ClosedAdoptionReview.createChallenge(plan,temporary,
                MACHINE,ref("ticket.json"),TICKET_NONCE,DEADLINE,DEADLINE,DEADLINE));
    }
    @Test void actualPredecessorMustBelongToTheTargetAndMatchTheIdentitySize() {
        var plan = plan();
        assertThrows(ContractViolationException.class, () -> new ClosedAdoptionReview.Plan(MACHINE,plan.ticketRef(),TICKET_NONCE,
                plan.target(),ref("immutable-snapshot.json"),plan.predecessorIdentity(),DEADLINE));
        assertThrows(ContractViolationException.class, () -> new ClosedAdoptionReview.Plan(MACHINE,plan.ticketRef(),TICKET_NONCE,
                plan.target(),plan.predecessorRef(),new FileStatIdentity(BigInteger.valueOf(18),"1","2"),DEADLINE));
    }
    @Test void approvalLocationIsFixedUnderTheActualTicketOutputRoot() {
        assertEquals(ROOT.resolve("root-review-approval.json"),ClosedAdoptionReview.approvalPath(ROOT));
        assertThrows(ContractViolationException.class, () -> ClosedAdoptionReview.approvalPath(Path.of("relative")));
        assertThrows(ContractViolationException.class, () -> ClosedAdoptionReview.approvalPath(ROOT.resolve("child/../other")));
    }
}
