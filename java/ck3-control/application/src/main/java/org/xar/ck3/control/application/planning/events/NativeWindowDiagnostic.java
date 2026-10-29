package org.xar.ck3.control.application.planning.events;

import com.fasterxml.jackson.databind.node.NullNode;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One diagnostic body contract for ordinary and private pending native-window source DATA. */
public final class NativeWindowDiagnostic {
    private NativeWindowDiagnostic() { }

    public record Source(ObservationIdentity origin, OpportunityJson.Obj snapshot,
            List<OpportunityJson.Value> retainedHistory, Optional<OpportunityJson.Value> context,
            Optional<OpportunityJson.Obj> originalPlan, String reason) {
        public Source {
            Objects.requireNonNull(origin); Objects.requireNonNull(snapshot);
            retainedHistory = List.copyOf(Objects.requireNonNull(retainedHistory));
            Objects.requireNonNull(context); Objects.requireNonNull(originalPlan); StrictJson.text(reason);
        }
    }

    /** Classifies DATA only; this creates no action, token or read permission. */
    public static Optional<EpisodeIncidentJournal.Kind> foregroundKind(OpportunityJson.Obj snapshot) {
        var body=DriverJson.toNode(Objects.requireNonNull(snapshot));
        if(body.path("active_event").isObject())return Optional.of(EpisodeIncidentJournal.Kind.EVENT);
        if(body.path("pending_character_interaction").isObject())return Optional.of(EpisodeIncidentJournal.Kind.INTERACTION);
        var hint=body.path("top_exclusive_modal_choice_hint");
        return hint.isObject()&&"present".equals(hint.path("status").asText())
                ?Optional.of(EpisodeIncidentJournal.Kind.MANDATORY):Optional.empty();
    }

    /** Absence means this original snapshot has no observed native foreground kind. */
    public static Optional<OpportunityJson.Obj> plan(Source source) {
        Objects.requireNonNull(source);
        var snapshot = DriverJson.toNode(source.snapshot());
        var event = snapshot.get("active_event"); var interaction = snapshot.get("pending_character_interaction");
        var kind=foregroundKind(source.snapshot());if(kind.isEmpty())return Optional.empty();
        boolean isEvent=kind.orElseThrow()==EpisodeIncidentJournal.Kind.EVENT;
        boolean isInteraction=kind.orElseThrow()==EpisodeIncidentJournal.Kind.INTERACTION;
        var body = StrictJson.object().put("schema", "xar.unhandled-native-window-diagnostic/v1")
                .put("kind", isEvent ? "unhandled_event" : isInteraction ? "pending_character_interaction" : "unknown_mandatory_choice")
                .put("diagnostic_reason", source.reason()).put("offline_followup_required", true).putNull("selection");
        body.set("origin", ProposalLifecycleCodec.observation(source.origin())); body.set("snapshot", snapshot);
        body.set("context", source.context().<com.fasterxml.jackson.databind.JsonNode>map(DriverJson::toNode).orElse(NullNode.instance));
        body.set("original_plan", source.originalPlan().<com.fasterxml.jackson.databind.JsonNode>map(DriverJson::toNode).orElse(NullNode.instance));
        var history = body.putArray("retained_history"); source.retainedHistory().forEach(row -> history.add(DriverJson.toNode(row)));
        var context = source.context().map(DriverJson::toNode).orElse(null);
        if (isEvent) {
            body.set("current_event_instance_id", event.get("instance_id"));
            body.set("event_definition_key", context == null || !context.has("event_definition_key")
                    ? NullNode.instance : context.get("event_definition_key"));
        } else if(isInteraction) {
            body.set("pending_interaction_id", interaction.get("instance_id"));
            body.set("interaction_definition_key", context == null || !context.path("definition").has("canonical_key")
                    ? NullNode.instance : context.path("definition").get("canonical_key"));
        }
        if(kind.orElseThrow()==EpisodeIncidentJournal.Kind.MANDATORY)
            body.set("mandatory_choice_hint",snapshot.get("top_exclusive_modal_choice_hint"));
        var plan = StrictJson.object().putNull("selected_step"); plan.set("unhandled_native_window_diagnostic", body);
        return Optional.of(OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(plan, ActionCommand.MAX_ARGUMENT_BYTES)),
                "actual unavailable native window diagnostic"));
    }
}
