package org.xar.ck3.control.reconciliation;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Assessment;
import org.xar.ck3.control.reconciliation.LateOutcome.Attempt;
import org.xar.ck3.control.reconciliation.LateOutcome.Outcome;
import org.xar.ck3.control.reconciliation.LateOutcome.ReadKind;
import org.xar.ck3.control.reconciliation.LateOutcome.Reason;

/** Portable assessment receipt. Digest equality binds context; it is not a writer qualification token. */
public final class AssessmentCodec {
    private static final String SCHEMA = "xar.clock-late-outcome-assessment/v1";
    private static final Set<String> FIELDS = Set.of("schema", "original_failure_sha256", "original_auto_sequence",
            "expected_head_sha256", "attempt_sha256", "outcome", "reason", "next_read", "wait_ms", "consumed_reads",
            "observed_sequences", "original_credit", "never_replay");
    private AssessmentCodec() { }
    public static byte[] encode(Attempt attempt, Assessment assessment) {
        ObjectNode row = StrictJson.object(); row.put("schema", SCHEMA);
        row.put("original_failure_sha256", attempt.original().receipt().sha256());
        row.put("original_auto_sequence", attempt.original().autoSequence()); row.put("expected_head_sha256", attempt.expectedHead().sha256());
        row.put("attempt_sha256", AttemptFingerprint.sha256(attempt));
        row.put("outcome", assessment.outcome().name()); row.put("reason", assessment.reason().name());
        if (assessment.nextRead() == null) { row.putNull("next_read"); } else { row.put("next_read", assessment.nextRead().name()); }
        row.put("wait_ms", assessment.waitMillis()); row.put("consumed_reads", assessment.consumedReads());
        var sequenceArray = row.putArray("observed_sequences"); assessment.observedSequences().forEach(sequenceArray::add);
        row.put("original_credit", 0); row.put("never_replay", true);
        return StrictJson.canonical(row, 16_384);
    }
    public static Assessment decode(byte[] raw, Attempt expected) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw), FIELDS);
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))), "assessment schema");
        StrictJson.require(AttemptFingerprint.sha256(expected).equals(StrictJson.text(row.get("attempt_sha256"))), "complete expected attempt binding mismatch");
        StrictJson.require(expected.original().receipt().sha256().equals(StrictJson.text(row.get("original_failure_sha256")))
                && expected.expectedHead().sha256().equals(StrictJson.text(row.get("expected_head_sha256")))
                && expected.original().autoSequence() == StrictJson.integer(row.get("original_auto_sequence"), 1, StrictJson.MAX_SAFE_INTEGER),
                "assessment original failure/writer head binding mismatch");
        StrictJson.integer(row.get("original_credit"), 0, 0); StrictJson.trueValue(row.get("never_replay"));
        JsonNode sequences = row.get("observed_sequences");
        StrictJson.require(sequences.isArray() && sequences.size() <= 64, "bounded observed sequence list");
        List<Long> parsed = new ArrayList<>();
        sequences.forEach(value -> parsed.add(StrictJson.integer(value, 1, StrictJson.MAX_SAFE_INTEGER)));
        return new Assessment(enumValue(Outcome.class, row.get("outcome")), enumValue(Reason.class, row.get("reason")),
                row.get("next_read").isNull() ? null : enumValue(ReadKind.class, row.get("next_read")),
                StrictJson.integer(row.get("wait_ms"), 0, 3_600_000), (int) StrictJson.integer(row.get("consumed_reads"), 0, 64), parsed);
    }
    private static <E extends Enum<E>> E enumValue(Class<E> type, JsonNode node) {
        String value = StrictJson.text(node);
        try { return Enum.valueOf(type, value); }
        catch (IllegalArgumentException error) { throw new ContractViolationException("unknown " + type.getSimpleName(), error); }
    }
}
