package org.xar.ck3.control.wave2.events.unhandledevent;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ArrayValue;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.NullValue;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ObjectValue;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.Value;

/** Exact continuation request. Filesystem context is supplied exclusively by the resident host. */
public final class SourceReviewedPlanJson {
    public static final String SCHEMA = "xar.events-source-reviewed-continuation-input/v1";
    public record Input(ObjectValue plan, ObjectValue snapshot, List<String> actionSteps) {
        public Input { Objects.requireNonNull(plan); actionSteps = List.copyOf(actionSteps); }
    }
    private SourceReviewedPlanJson() { }

    public static Input decode(byte[] raw) {
        ObjectValue root = RetainedJson.object(RetainedJson.parse(raw));
        StrictJson.require(root.fields().keySet().equals(Set.of("schema", "plan", "snapshot", "action_steps")), "exact source-review continuation fields required");
        StrictJson.require(SCHEMA.equals(RetainedJson.string(root.get("schema"))), "source-review continuation schema");
        ObjectValue plan = RetainedJson.object(root.get("plan"));
        ObjectValue capture = RetainedJson.object(plan.get("unhandled_event_fallback"));
        StrictJson.require(UnhandledEventFallback.SCHEMA.equals(RetainedJson.string(capture.get("schema"))), "original unhandled event capture required");
        StrictJson.require(Boolean.FALSE.equals(RetainedJson.bool(capture.getOrNull("semantic_optimal")))
                && Boolean.FALSE.equals(RetainedJson.bool(capture.getOrNull("native_ai_equivalent"))), "source review cannot import caller semantic authority");
        RetainedJson.object(plan.get("event_decision")); RetainedJson.object(plan.get("active_event"));
        Value snapshotValue = root.get("snapshot");
        ObjectValue snapshot = snapshotValue instanceof NullValue ? null : RetainedJson.object(snapshotValue);
        Value stepValue = root.get("action_steps");
        StrictJson.require(stepValue instanceof ArrayValue, "source-review action step array required");
        List<Value> rawSteps = ((ArrayValue) stepValue).values();
        StrictJson.require(rawSteps.size() <= 4_096, "bounded source-review action steps required");
        List<String> steps = new ArrayList<>();
        for (Value step : rawSteps) {
            String value = RetainedJson.string(step); StrictJson.require(value != null, "source-review action step string required");
            steps.add(StrictJson.text(value));
        }
        return new Input(plan, snapshot, steps);
    }

    public static byte[] encode(SourceReviewedEventConsumer.ReviewedPlan result) {
        return Objects.requireNonNull(result, "reviewed plan").encode();
    }
}
