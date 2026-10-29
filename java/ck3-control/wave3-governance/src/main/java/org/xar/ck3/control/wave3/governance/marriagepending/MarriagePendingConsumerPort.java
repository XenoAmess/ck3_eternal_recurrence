package org.xar.ck3.control.wave3.governance.marriagepending;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import java.util.Objects;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalCodec;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.ObjectValue;
import org.xar.ck3.control.wave2.governance.betrothal.MarriageProjectionJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.governance.marriagehandoff.MarriageHandoffCodec;
import org.xar.ck3.control.wave2.governance.marriagehandoff.MarriageHandoffModel.Ledger;
import static org.xar.ck3.control.wave3.governance.marriagepending.MarriagePendingModel.*;

/** Strict adapter for an already eligible original family planner; it emits the original plan shape. */
public final class MarriagePendingConsumerPort {
    public static final String SCHEMA = "xar.java-family-marriage-pending-read-request/v1";
    public static final String RESULT_STEP = "query-observed-first-heir-marriage-result-v1-private";
    private static final Set<String> FIELDS = Set.of("schema", "planned", "snapshot", "ledger", "bridge_identity");
    private static final JsonMapper JSON = JsonMapper.builder(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS, DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS, DeserializationFeature.FAIL_ON_TRAILING_TOKENS)
            .disable(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES).build();
    private MarriagePendingConsumerPort() { }

    public static Inputs decode(byte[] raw) { return boundary(raw).inputs(); }

    /** Validated input with no exposed mutable JSON tree and no process lookup side effect. */
    public static final class PreparedInput {
        private final Boundary boundary;
        private PreparedInput(Boundary boundary) { this.boundary = boundary; }
        public boolean needsCurrentProcess() {
            return boundary.identity() == null && MarriagePendingReadPolicy.requiresCurrentProcess(boundary.ledger(), boundary.frame());
        }
        public Inputs inputs() { return boundary.inputs(); }
    }
    public record AppliedPlan(boolean handled, ObjectValue planned) {
        public AppliedPlan { Objects.requireNonNull(planned); }
    }
    public static PreparedInput decodePrepared(byte[] raw) { return new PreparedInput(boundary(raw)); }
    /** handled=false means continue the original planner; it is never a completed non-pending plan. */
    public static byte[] apply(byte[] raw) { return encodeApplied(project(decodePrepared(raw))); }
    public static AppliedPlan project(PreparedInput prepared) {
        Boundary boundary = Objects.requireNonNull(prepared).boundary;
        Decision decision = MarriagePendingReadPolicy.decide(boundary.inputs());
        ObjectNode planned = boundary.planned().deepCopy(); ObjectNode plan = object(planned.get("plan"));
        boolean handled = !(decision instanceof NoPending);
        if (decision instanceof OtherEpisode) {
            plan.putNull("selected_step"); plan.put("reason", "unresolved marriage belongs to another episode");
        } else if (decision instanceof ReadResult read) {
            plan.put("phase", "first_heir_marriage_result_read"); plan.put("selected_step", RESULT_STEP);
            plan.set("family_marriage_pending", boundary.pending()); plan.put("family_marriage_cold_recovery", read.coldRecovery());
            plan.put("reason", "read proposal resolution and bilateral relation before another send");
        } else if (decision instanceof WaitLater wait) {
            plan.set("family_marriage_pending", boundary.pending());
            plan.put("family_marriage_status", wait.pending().coldAbsentRelationUnresolved() ? "cold_absent_relation_unresolved" : "await_later_paused_frame");
            if (wait.pending().lastOutboundPendingState() == null) { plan.putNull("family_marriage_outbound_pending_state"); }
            else { plan.put("family_marriage_outbound_pending_state", wait.pending().lastOutboundPendingState()); }
            plan.put("reason", "await later paused frame for marriage result without resubmitting");
        }
        return new AppliedPlan(handled, (ObjectValue) BetrothalCodec.projectEvidence(planned));
    }
    public static byte[] encodeApplied(AppliedPlan applied) {
        ObjectNode result = JSON.createObjectNode(); result.put("handled", applied.handled());
        result.set("planned", MarriageProjectionJson.value(BetrothalCodec.encodeEvidence(applied.planned()), MarriageHandoffCodec.MAXIMUM_BYTES));
        return bytes(result);
    }

    private record Boundary(Ledger ledger, Pending projection, Frame frame, ProcessIdentity identity,
                            ObjectNode planned, ObjectNode pending) {
        Inputs inputs() { return new Inputs(ledger, projection, frame, identity); }
    }
    private static Boundary boundary(byte[] raw) {
        ObjectNode request = StrictJson.object(parse(raw), FIELDS);
        StrictJson.require(SCHEMA.equals(StrictJson.text(request.get("schema"))), "family pending read schema differs");
        ObjectNode planned = object(request.get("planned")); object(planned.get("plan"));
        ObjectNode snapshot = object(request.get("snapshot"));
        Frame frame = new Frame(StrictJson.text(snapshot.get("episode_run_id")), optionalRevision(snapshot.get("native_revision")));
        Ledger ledger = MarriageHandoffCodec.decodeLedger(bytes(request.get("ledger")));
        ObjectNode pending = ledger.pending() == null ? null : object(request.get("ledger").get("pending"));
        Pending projection = pending == null ? null : new Pending(ledger.pending(), retained(pending, "source_bridge_pid", "source_bridge_creation_date"),
                retained(pending, "last_checked_bridge_pid", "last_checked_bridge_creation_date"), effectiveLastRevision(pending), optionalBoolean(pending.get("cold_absent_relation_unresolved")), optionalText(pending.get("last_outbound_pending_state")));
        JsonNode bridge = request.get("bridge_identity"); ProcessIdentity identity = null;
        if (!bridge.isNull()) {
            ObjectNode row = StrictJson.object(bridge, Set.of("pid", "creation_date"));
            identity = new ProcessIdentity(pid(row.get("pid")), StrictJson.text(row.get("creation_date")));
        }
        return new Boundary(ledger, projection, frame, identity, planned, pending);
    }
    private static RetainedProcess retained(ObjectNode value, String pidKey, String creationKey) {
        JsonNode process = value.get(pidKey); Long retainedPid = process == null || process.isNull() ? null : pid(process);
        return new RetainedProcess(retainedPid, optionalText(value.get(creationKey)));
    }
    private static BigInteger effectiveLastRevision(ObjectNode pending) {
        JsonNode last = pending.has("last_checked_native_revision") ? pending.get("last_checked_native_revision") : pending.get("pre_native_revision");
        if (last == null) { return BigInteger.ZERO; }
        StrictJson.require(!last.isNull(), "explicit null checked revision is not a comparable integer");
        return revision(last);
    }
    private static BigInteger optionalRevision(JsonNode value) { return value == null || value.isNull() ? null : revision(value); }
    private static BigInteger revision(JsonNode value) { return StrictJson.integer(value, BigInteger.ZERO, StrictJson.UINT64_MAX); }
    private static long pid(JsonNode value) { return StrictJson.integer(value, 1, 0xffff_ffffL); }
    private static boolean optionalBoolean(JsonNode value) {
        if (value == null || value.isNull()) { return false; }
        StrictJson.require(value.isBoolean(), "actual pending flag boolean required"); return value.booleanValue();
    }
    private static String optionalText(JsonNode value) { return value == null || value.isNull() ? null : StrictJson.text(value); }
    private static ObjectNode object(JsonNode value) { StrictJson.require(value != null && value.isObject(), "JSON object required"); return (ObjectNode) value; }
    private static JsonNode parse(byte[] raw) {
        StrictJson.parse(raw, MarriageHandoffCodec.MAXIMUM_BYTES);
        try { return JSON.readTree(raw); } catch (IOException error) { throw new IllegalArgumentException("strict JSON parse failed", error); }
    }
    private static byte[] bytes(JsonNode value) {
        byte[] result = value.toString().getBytes(StandardCharsets.UTF_8);
        StrictJson.require(result.length <= MarriageHandoffCodec.MAXIMUM_BYTES, "pending plan exceeds explicit JSON budget"); return result;
    }
}

