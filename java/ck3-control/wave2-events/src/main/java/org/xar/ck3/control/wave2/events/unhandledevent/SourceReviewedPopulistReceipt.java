package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;

/** The original populist response comparison. No source qualification, file read, writer, or replay authority. */
public final class SourceReviewedPopulistReceipt {
    public static final String SCHEMA = "xar.events-source-reviewed-receipt-input/v1";
    private static final String STEP = "select-event-option-4";
    private static final String FAILURE = "source-reviewed populist refusal receipt/selection differs; retain without replay";
    private SourceReviewedPopulistReceipt() { }

    public record Input(Optional<ObjectValue> body) {
        public Input { Objects.requireNonNull(body, "body"); body.ifPresent(SourceReviewedPopulistReceipt::validateBodyShapes); }
    }
    public static Input decode(byte[] raw) {
        ObjectValue root = o(parse(raw));
        require(root != null && root.fields().keySet().equals(Set.of("schema", "body"))
                && SCHEMA.equals(text(root, "schema")), "exact source-reviewed receipt wrapper required");
        Value body = root.get("body");
        require(body instanceof NullValue || body instanceof ObjectValue, "receipt body object or null required");
        return new Input(Optional.ofNullable(o(body)));
    }

    public static Optional<ObjectValue> verify(Input input) {
        ObjectValue body = input.body().orElse(null), plan = o(body, "plan");
        if (!eq(plan, "phase", s("active_event_source_reviewed_populist_refusal"))) return Optional.empty();
        ObjectValue capture = o(plan, "unhandled_event_fallback"), selection = o(capture, "selection");
        ObjectValue knowledge = o(capture, "source_knowledge"), decision = o(plan, "event_decision");
        ObjectValue summary = o(plan, "active_event"), binding = o(capture, "binding"), inner = o(body, "result");
        ObjectValue post = o(inner, "event_selection"), evidence = o(body, "unhandled_event_fallback_evidence");
        ObjectValue before = o(evidence, "before"), after = o(evidence, "after");
        boolean verified = eq(body, "status", s("executed")) && eq(body, "selected_step", s(STEP))
                && eq(plan, "selected_step", s(STEP)) && capture != null && selection != null && knowledge != null
                && decision != null && summary != null && binding != null
                && eq(capture, "policy", s("exact-source-reviewed-populist-refuse-preserve-realm"))
                && eq(capture, "event_definition_key", s("faction_demand.1001"))
                && eq(knowledge, "status", s("offline-source-reviewed"))
                && ExistingFactionEventPolicies.sourceKnownPopulist(capture, knowledge) && yes(capture, "registry_known")
                && eq(selection, "selected_step", s(STEP)) && eq(selection, "native_option_index", i(3))
                && eq(selection, "option_number", i(4)) && eq(selection, "rendered_index", i(1)) && yes(selection, "enabled")
                && eq(summary, "selected_native_option_index", i(3)) && eq(summary, "selected_option_number", i(4))
                && eq(summary, "selected_rendered_index", i(1)) && eq(decision, "selected_native_option_index", i(3))
                && eq(decision, "selected_option_number", i(4)) && eq(decision, "selected_rendered_index", i(1))
                && eq(decision, "material_effects_verified", b(false)) && inner != null && yes(inner, "accepted")
                && eq(inner, "step", s(STEP)) && eq(inner, "option_number", i(4)) && eq(inner, "option_index", i(3))
                && v(inner, "event_instance_id").equals(v(capture, "current_event_instance_id")) && post != null
                && eq(post, "status", s("event_instance_advanced")) && yes(post, "postcondition_verified")
                && v(post, "old_event_instance_id").equals(v(capture, "current_event_instance_id"))
                && !v(post, "new_event_instance_id").equals(v(capture, "current_event_instance_id"))
                && eq(post, "selected_option_number", i(4)) && eq(post, "selected_native_option_index", i(3))
                && v(post, "starting_snapshot_id").equals(v(binding, "snapshot_id"))
                && number(binding, "revision") != null && number(post, "starting_revision") != null
                && v(post, "starting_revision").equals(v(binding, "revision"))
                && v(post, "ending_snapshot_id").equals(v(inner, "snapshot_id"))
                && v(post, "ending_revision").equals(v(inner, "revision")) && number(post, "ending_revision") != null
                && number(post, "ending_revision").compareTo(number(post, "starting_revision")) > 0
                && List.of("episode_run_id", "connection_generation", "bridge_pid").stream()
                    .allMatch(key -> v(post, key).equals(v(binding, key)))
                && evidence != null && yes(evidence, "command_acknowledged") && yes(evidence, "event_instance_advanced_verified")
                && eq(evidence, "replay_allowed", b(false)) && nonempty(evidence, "incident_id")
                && reference(before) && reference(after);
        if (!verified) throw new ProjectionDomainRejection(FAILURE);
        return Optional.of(obj(f("schema", s("g2.queue.ordinary-result-credit/v1")), f("selected_step", s(STEP)),
                f("service_status", s("executed")), f("result_status", v(inner, "status")),
                f("category", s("source_reviewed_populist_refusal_ui_advanced")), f("primitive_accepted", b(true)),
                f("submitted_pending", b(false)), f("typed_nonmaterial_observation", b(false)),
                f("business_success_inferred", b(false)), f("war_started_verified", b(false)), f("victory_verified", b(false)),
                f("title_retention_verified", b(false)), f("replay_allowed", b(false))));
    }
    public static byte[] encodeResult(Optional<ObjectValue> result) {
        return encode(result.<Value>map(value -> value).orElse(NULL));
    }
    /** JSON token types belong to decode/typed construction, never an internal project failure. */
    private static void validateBodyShapes(ObjectValue body) {
        ObjectValue plan = o(body, "plan");
        if (!eq(plan, "phase", s("active_event_source_reviewed_populist_refusal"))) return;
        ObjectValue capture = o(plan, "unhandled_event_fallback"), binding = o(capture, "binding");
        ObjectValue inner = o(body, "result"), post = o(inner, "event_selection"), evidence = o(body, "unhandled_event_fallback_evidence");
        for (String key : List.of("revision", "bridge_pid", "connection_generation")) number(binding, key);
        for (String key : List.of("starting_revision", "ending_revision", "bridge_pid", "connection_generation",
                "old_event_instance_id", "new_event_instance_id")) number(post, key);
        number(capture, "current_event_instance_id"); number(inner, "event_instance_id"); number(inner, "revision");
        for (String key : List.of("snapshot_id", "episode_run_id")) text(binding, key);
        for (String key : List.of("starting_snapshot_id", "ending_snapshot_id", "episode_run_id")) text(post, key);
        text(inner, "snapshot_id"); text(evidence, "incident_id");
        for (String name : List.of("before", "after")) {
            ObjectValue reference = o(evidence, name); text(reference, "path"); text(reference, "sha256");
        }
        ObjectValue knowledge = o(capture, "source_knowledge");
        if ("populist1001_source_rebound".equals(text(knowledge, "binding_mode")))
            number(o(knowledge, "adapted_from"), "calculated_event_id");
    }
    private static boolean nonempty(ObjectValue value, String key) { String item = text(value, key); return item != null && !item.isEmpty(); }
    private static boolean reference(ObjectValue value) {
        String sha = text(value, "sha256");
        return value != null && nonempty(value, "path") && sha != null && sha.length() == 64;
    }
}
