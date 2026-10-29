package org.xar.ck3.control.vanilla.schemesway;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Locale;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import static org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService.*;

/** Central conversion of the unchanged formal/lifecycle producer result and versioned Java execution result. */
public final class OrdinarySwayExecutionWire {
    private static final ObjectMapper JSON = new ObjectMapper()
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS);
    private OrdinarySwayExecutionWire() { }

    public static FormalResult formal(byte[] raw) {
        ProjectionJson evidence = ProjectionJson.object(raw, ProjectionJson.MAX_BYTES);
        JsonNode row = read(evidence);
        String status = StrictJson.text(row.get("status"));
        FormalStatus kind = switch (status) {
            case "applied" -> FormalStatus.APPLIED;
            case "receipt_pending" -> FormalStatus.RECEIPT_PENDING;
            case "postcondition_pending" -> FormalStatus.POSTCONDITION_PENDING;
            case "submission_unresolved" -> FormalStatus.SUBMISSION_UNRESOLVED;
            case "pending_recovery" -> FormalStatus.PENDING_RECOVERY;
            case "no_positive_opportunity" -> FormalStatus.NO_POSITIVE_OPPORTUNITY;
            case "already_applied" -> FormalStatus.ALREADY_APPLIED;
            default -> FormalStatus.OTHER_OBSERVED;
        };
        JsonNode post = row.get("postcondition_verified");
        StrictJson.require(post == null || post.isNull() || post.isBoolean(), "postcondition must retain boolean/null/absent");
        Optional<String> action = text(row.get("action_id"));
        Optional<Followup> following = Optional.empty();
        JsonNode followup = row.get("followup");
        if (followup != null && !followup.isNull()) {
            StrictJson.require(followup.isObject(), "formal followup must be an object");
            Optional<String> decision = text(followup.get("decision"));
            if (decision.isPresent()) {
                following = Optional.of(switch (decision.orElseThrow()) {
                    case "finish_selected_relation" -> Followup.FINISH_SELECTED_RELATION;
                    case "return_to_opportunity_selection" -> Followup.RETURN_TO_OPPORTUNITY_SELECTION;
                    case "native_start_unavailable" -> Followup.NATIVE_START_UNAVAILABLE;
                    default -> Followup.OTHER;
                });
            }
        }
        return new FormalResult(kind, post != null && post.isBoolean() && post.booleanValue(), action, following, evidence);
    }

    public static LifecycleResult lifecycle(byte[] raw) {
        ProjectionJson evidence = ProjectionJson.object(raw, ProjectionJson.MAX_BYTES);
        JsonNode row = read(evidence);
        return new LifecycleResult("observed".equals(StrictJson.text(row.get("status")))
                ? LifecycleStatus.OBSERVED : LifecycleStatus.UNAVAILABLE, evidence);
    }

    public static byte[] encode(Execution execution) {
        ObjectNode row = StrictJson.object(); row.put("schema", "xar.java-ordinary-sway-execution/v1");
        if (execution instanceof Started started) {
            row.put("status", "executed"); row.put("selected_step", STEP);
            row.set("result", result(started.result())); row.set("ordinary_sway_optional", receipt(started.receipt()));
            row.putNull("following_plan");
        } else if (execution instanceof Continued continued) {
            row.put("status", "continued_ordinary");
            row.set("ordinary", read(continued.ordinary().outcome()));
            row.set("following_plan", read(continued.ordinary().followingPlan()));
            if (continued.receipt().isPresent()) { row.set("ordinary_sway_optional", receipt(continued.receipt().orElseThrow())); }
            else { row.set("ordinary_sway_optional", result(continued.unavailable().orElseThrow())); }
        } else { throw new IllegalArgumentException("unknown execution branch"); }
        row.put("native_ai_equivalence_claimed", false); row.put("ledger_committed", false);
        // Opaque formal/ordinary evidence may contain legitimate decimal values.
        // Only the interpreted fields above use the compact strict integer contract.
        try {
            byte[] encoded = JSON.writeValueAsBytes(row);
            ProjectionJson.object(encoded, ProjectionJson.MAX_BYTES);
            return encoded;
        } catch (IOException failure) { throw new IllegalArgumentException("execution serialization failed", failure); }
    }

    private static ObjectNode receipt(Receipt receipt) {
        ObjectNode row = StrictJson.object(); row.put("job", name(receipt.job())); row.put("outcome", name(receipt.outcome()));
        if (receipt.targetCharacterId().isPresent()) { row.put("target_character_id", receipt.targetCharacterId().orElseThrow()); }
        else { row.putNull("target_character_id"); }
        row.set("result", result(receipt.result()));
        row.set("scheduler_state", StrictJson.parse(SwayScheduleWire.encodeState(receipt.schedulerState())));
        receipt.stateWriteError().ifPresent(value -> row.put("scheduler_state_write_error", value));
        row.put("same_pid_or_runtime_claim", false); return row;
    }
    private static JsonNode result(CheckResult result) {
        if (result instanceof FormalResult formal) { return read(formal.evidence()); }
        if (result instanceof LifecycleResult lifecycle) { return read(lifecycle.evidence()); }
        if (result instanceof LocalResult local) {
            ObjectNode row = StrictJson.object();
            row.put("status", local.status() == LocalStatus.INPUTS_ABSENT ? "unavailable" : name(local.status()));
            if (local.status() == LocalStatus.INPUTS_ABSENT) { row.put("reason", "state_dir_absent"); }
            if (local.status() == LocalStatus.ORIGINAL_PENDING_PRESERVED || local.status() == LocalStatus.PENDING_IDENTITY_CHANGED) {
                row.put("submit_attempted", false);
            }
            local.error().ifPresent(value -> row.put("error", value)); return row;
        }
        throw new IllegalArgumentException("unknown result branch");
    }
    private static Optional<String> text(JsonNode value) {
        return value == null || value.isNull() ? Optional.empty() : Optional.of(StrictJson.text(value));
    }
    private static JsonNode read(ProjectionJson value) {
        // ProjectionJson already validates UTF-8, duplicate fields, structure and its 8 MiB role budget.
        // StrictJson's compact 1 MiB ceiling is a different contract, even when the actual value is tiny.
        try { return JSON.readTree(value.bytes()); }
        catch (IOException failure) { throw new IllegalArgumentException("invalid validated evidence", failure); }
    }
    private static String name(Enum<?> value) { return value.name().toLowerCase(Locale.ROOT); }
}
