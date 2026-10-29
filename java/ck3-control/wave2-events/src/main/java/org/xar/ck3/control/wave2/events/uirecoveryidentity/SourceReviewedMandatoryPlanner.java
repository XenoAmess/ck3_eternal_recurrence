package org.xar.ck3.control.wave2.events.uirecoveryidentity;

import static org.xar.ck3.control.wave2.events.uirecoveryidentity.UiRecoveryEvidenceLookup.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.EvidenceDocument;
import org.xar.ck3.control.wave2.events.choiceplanning.ChoicePlanningJson;
import org.xar.ck3.control.wave2.events.choiceplanning.ChoicePlanningModel;
import org.xar.ck3.control.wave2.events.choiceplanning.MandatoryChoicePlanner;

/** The existing live planner, with its observed-UI evidence rule shared with the actual offline producer. */
public final class SourceReviewedMandatoryPlanner {
    private final EventSourceReadContext configured;
    public record Input(ChoicePlanningModel.PlanningInput planning) { public Input { Objects.requireNonNull(planning); } }
    public SourceReviewedMandatoryPlanner(EventSourceReadContext configured) { this.configured = Objects.requireNonNull(configured); }
    public static Input decode(byte[] raw) { return new Input(ChoicePlanningJson.decode(raw)); }
    public EvidenceDocument plan(Input input) {
        byte[] original = ChoicePlanningJson.encode(new MandatoryChoicePlanner().plan(input.planning()));
        JsonNode node = parse(original, WIRE_LIMIT);
        if (!(node instanceof ObjectNode plan) || !plan.path("unknown_mandatory_choice_v1").isObject()
                || input.planning().snapshot().isEmpty() || input.planning().snapshot().orElseThrow().frame().isEmpty()) {
            return new EvidenceDocument(new String(original, StandardCharsets.UTF_8));
        }
        long gamePid = input.planning().snapshot().orElseThrow().frame().orElseThrow().gamePid();
        ObjectNode capture = object(plan.get("unknown_mandatory_choice_v1"));
        Optional<EvidenceDocument> known = new UiRecoveryEvidenceLookup(configured).lookup(capture.get("native_window"), BigInteger.valueOf(gamePid), null);
        if (known.isPresent()) {
            ObjectNode fact = object(parse(known.orElseThrow().json().getBytes(StandardCharsets.UTF_8), WIRE_LIMIT));
            capture.set("known_ui_recovery_source", fact.deepCopy()); plan.set("known_ui_recovery_source", fact);
            plan.put("phase", "known_observed_ui_recovery_first_enabled");
        }
        return document(plan, WIRE_LIMIT);
    }
    public static byte[] encode(EvidenceDocument document) {
        byte[] raw = document.json().getBytes(StandardCharsets.UTF_8); parse(raw, WIRE_LIMIT); return raw;
    }
}
