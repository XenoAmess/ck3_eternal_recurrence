package org.xar.ck3.control.application.planning.events;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.OrdinaryHistory;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativeActiveEvent;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.registered.BookmarkRaiktorPolicy;
import org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge;
import org.xar.ck3.control.wave2.events.registered.RegisteredVanillaEventPolicy;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewedEventConsumer;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;

/** One automatic event-choice producer for actual ordinary requests and pending-observation DATA.
 * Native preparation, dispatch and independent results remain their existing owners. */
public final class PublicEventResolution {
    private static final String SCHEMA = "xar.public-event-resolution/v1";
    private static final Set<String> STRATEGIES = Set.of("dedicated-native-event-v1", "registered-native-event-v1",
        "source-reviewed-native-event-v1", "backend-neutral-event-v1", "user-first-displayed-event-v1");
    private static final Set<String> ROW_FIELDS = Set.of("event_index", "event_instance_id", "title", "visible_options",
        "selected_option_number", "selected_option_index", "selected_visible_text", "strategy", "source");
    private PublicEventResolution() { }

    public static OpportunityJson.Obj plan(PlanningRequest actual,Optional<Integer> expectedInstance,
            RegisteredEventKnowledge knowledge,TrustedEventSourceContext trusted,RegisteredEventCore.ContextValidator validator){
        Objects.requireNonNull(actual);Objects.requireNonNull(validator);
        var context=RegisteredEventCore.currentContext(actual,OrdinaryPolicy.Draft.empty(),validator).orElseThrow(()->new IllegalArgumentException("same-instance original event read unavailable"));
        return plan(EventDecisionInput.ordinary(actual,context),expectedInstance,knowledge,trusted);
    }
    public static OpportunityJson.Obj plan(EventDecisionInput actual,RegisteredEventKnowledge knowledge,TrustedEventSourceContext trusted){return plan(actual,Optional.empty(),knowledge,trusted);}
    public static OpportunityJson.Obj plan(EventDecisionInput actual,Optional<Integer> expectedInstance,
            RegisteredEventKnowledge knowledge,TrustedEventSourceContext trusted){
        Objects.requireNonNull(actual); Objects.requireNonNull(expectedInstance); Objects.requireNonNull(knowledge);
        Objects.requireNonNull(trusted);
        var snapshot = actual.snapshot();
        var event = obj(snapshot.get("active_event"), "actual normalized active event");
        BigInteger instance = positive(event.get("instance_id")), count = positive(event.get("option_count"));
        require(instance.bitLength() <= 31 && count.compareTo(BigInteger.valueOf(4096)) <= 0,
            "actual native event identity/count outside its existing contract");
        expectedInstance.ifPresent(value -> require(value > 0 && instance.equals(BigInteger.valueOf(value)), "active event instance mismatch"));
        require(actual.paused(), "automatic event resolution requires its original paused frame");
        var context = RegisteredEventCore.currentContext(actual)
            .orElseThrow(() -> new IllegalArgumentException("same-instance original event read unavailable"));
        require("available".equals(text(context.get("status"))), "same-instance event window unavailable");
        OpportunityJson.Obj normalized = normalized(event, snapshot);
        var dedicated = RegisteredEventCore.dedicatedRecommendation(actual, context);
        if (dedicated.isPresent()) {
            var choice = dedicated.orElseThrow();
            if (choice.status() != BookmarkRaiktorPolicy.Status.RECOMMENDED)
                return attach(blocked(actual, context, opportunity(choice.wire()), choice.wire().get("selected_step")), normalized, "dedicated-native-event-v1");
            var selected = PublicEventSelection.derivedPlan(actual, choice.nativeIndex().orElseThrow().add(BigInteger.ONE).intValueExact(),
                expectedInstance, knowledge, trusted).with("event_decision", opportunity(choice.wire()))
                .with("phase", new OpportunityJson.Text("active_event_raiktor_source_reviewed_choice"));
            return attach(selected, normalized, "dedicated-native-event-v1");
        }
        var history = new RetainedJson.ArrayValue(OrdinaryHistory.collect(actual.history()).rows().stream()
            .map(PublicEventResolution::retained).map(RetainedJson.Value.class::cast).toList());
        var recommendation = new RegisteredVanillaEventPolicy(knowledge).recommend(new RegisteredVanillaEventPolicy.Input(context,
            retained(obj(snapshot.get("played_character"), "actual player")).get("character_id"), new RetainedJson.IntegerValue(count), Optional.empty(),
            retained(obj(snapshot.get("played_character"), "actual player")), retainedField(snapshot, "event_opinion_observations"), history));
        if (recommendation.status() == RegisteredVanillaEventPolicy.Status.RECOMMENDED) {
            int number = recommendation.selection().orElseThrow().optionNumber().intValueExact();
            return attach(PublicEventSelection.derivedPlan(actual, number, expectedInstance, knowledge, trusted), normalized, "registered-native-event-v1");
        }
        var previous = new OrdinaryPolicy.Draft("one-life-turn-v1", "active_event_semantic_evidence_required", "retain the original registered decision",
            OrdinaryPolicy.Kind.FOREGROUND, Optional.empty(), OrdinaryPolicy.Purpose.READ_ONLY, Optional.empty(),
            new OpportunityJson.Obj(Map.of("event_decision", opportunity(recommendation.wire()))));
        var collected = EventPolicies.firstDisplayedPlan(actual, previous, (com.fasterxml.jackson.databind.node.ObjectNode)DriverJson.toNode(opportunity(context)), Optional.of(trusted))
            .orElseThrow(() -> new IllegalArgumentException("same-frame displayed event option projection unavailable"));
        var first = collected.plan();
        var capture = obj(first.get("unhandled_event_fallback"), "actual first-display capture");
        if (first.get("phase") instanceof OpportunityJson.Text phase && Set.of("active_event_source_reviewed_independence_refusal",
                "active_event_source_reviewed_populist_refusal").contains(phase.value()))
            return attach(first, normalized, "source-reviewed-native-event-v1");
        // Source knowledge does not grant a new choice when the actual first-display plan is blocked.
        if (first.get("selected_step") instanceof OpportunityJson.Nil)
            return attach(first, normalized, "user-first-displayed-event-v1");
        // Reuse the actual reader's typed result instead of reading the same knowledge twice.
        boolean reviewed = collected.sourceKnowledge().map(status -> status == SourceReviewedEventConsumer.KnowledgeStatus.SOURCE_REVIEWED)
            .orElseGet(() -> SourceReviewedEventConsumer.lookup(retained(capture), trusted).entry().isPresent());
        if (!reviewed)
            return attach(first, normalized, "user-first-displayed-event-v1");
        var eligible = new ArrayList<OpportunityJson.Value>();
        for (var raw : arr(normalized.get("options")).items()) {
            var option = obj(raw, "normalized option"); BigInteger number = positive(option.get("option_number"));
            boolean legal = ((RetainedJson.ArrayValue)context.get("options")).values().stream().filter(RetainedJson.ObjectValue.class::isInstance)
                .map(RetainedJson.ObjectValue.class::cast).anyMatch(row -> new RetainedJson.IntegerValue(number.subtract(BigInteger.ONE)).equals(row.get("native_option_index"))
                    && new RetainedJson.BooleanValue(true).equals(row.get("shown")) && new RetainedJson.BooleanValue(true).equals(row.get("enabled")));
            if (legal) eligible.add(option);
        }
        var chosen = NativeActiveEvent.chooseOptionNumber(DriverJson.toNode(normalized.with("options", new OpportunityJson.Arr(eligible))));
        if (chosen.isEmpty()) return attach(first.with("selected_step", OpportunityJson.Nil.INSTANCE)
            .with("reason", new OpportunityJson.Text("no original normalized option is both enabled and legally displayed")), normalized, "backend-neutral-event-v1");
        return attach(PublicEventSelection.derivedPlan(actual, chosen.orElseThrow().intValueExact(), expectedInstance, knowledge, trusted),
            normalized, "backend-neutral-event-v1");
    }

    private static OpportunityJson.Obj blocked(EventDecisionInput actual, RetainedJson.ObjectValue context,
            OpportunityJson.Obj decision, RetainedJson.Value required) {
        var fields = new LinkedHashMap<String, OpportunityJson.Value>();
        fields.put("policy", new OpportunityJson.Text("one-life-turn-v1")); fields.put("phase", new OpportunityJson.Text("active_event_dedicated_unavailable"));
        fields.put("reason", new OpportunityJson.Text("the existing dedicated policy retains priority; its current read or source contract is unavailable"));
        fields.put("selected_step", OpportunityJson.Nil.INSTANCE); fields.put("dedicated_policy_blocked", new OpportunityJson.Bool(true));
        fields.put("event_decision", decision); fields.put("event_window_context", opportunity(context));
        fields.put("event_read_binding", opportunity(RegisteredEventCore.binding(actual)));
        if (required instanceof RetainedJson.StringValue step) fields.put("required_step", new OpportunityJson.Text(step.value()));
        return new OpportunityJson.Obj(fields);
    }
    private static OpportunityJson.Obj normalized(OpportunityJson.Obj original, OpportunityJson.Obj snapshot) {
        String fallback = snapshot.get("source") instanceof OpportunityJson.Text value && !value.value().isEmpty() ? value.value() : "bridge";
        var node = NativeActiveEvent.normalize(DriverJson.toNode(original), fallback);
        var result = obj(DriverJson.fromNode(node), "normalized active event");
        // Retain the actual decimal token domain, including signed zero, when normalization did not alter its option rows.
        if (original.get("options") != null && DriverJson.toNode(original.get("options")).equals(node.get("options")))
            result = result.with("options", original.get("options"));
        return result;
    }
    private static OpportunityJson.Obj attach(OpportunityJson.Obj plan, OpportunityJson.Obj normalized, String strategy) {
        require(STRATEGIES.contains(strategy), "known automatic event strategy required");
        var number = plan.get("option_number");
        if (number == null && plan.get("unhandled_event_fallback") instanceof OpportunityJson.Obj capture)
            number = obj(capture.get("selection"), "actual captured selection").get("option_number");
        var fields = new LinkedHashMap<String, OpportunityJson.Value>();
        fields.put("schema", new OpportunityJson.Text(SCHEMA)); fields.put("selection_strategy", new OpportunityJson.Text(strategy));
        fields.put("normalized_active_event", normalized); fields.put("event_instance_id", normalized.get("instance_id"));
        fields.put("option_number", number == null ? OpportunityJson.Nil.INSTANCE : number);
        fields.put("selected_step", plan.get("selected_step") == null ? OpportunityJson.Nil.INSTANCE : plan.get("selected_step"));
        return plan.with("public_event_resolution", new OpportunityJson.Obj(fields)).with("public_explicit_selection", new OpportunityJson.Bool(false));
    }

    /** Original ordinary_events row from the exact prepared plan; this is selection metadata, never effect proof. */
    public static OpportunityJson.Obj ordinaryEvent(OpportunityJson.Obj preparedPlan) {
        var metadata = obj(preparedPlan.get("public_event_resolution"), "original resolution metadata");
        require(metadata.members().keySet().equals(Set.of("schema", "selection_strategy", "normalized_active_event", "event_instance_id", "option_number", "selected_step"))
            && SCHEMA.equals(text(metadata.get("schema"))), "exact original resolution metadata contract required");
        int instance = positive(metadata.get("event_instance_id")).intValueExact(), number = positive(metadata.get("option_number")).intValueExact();
        String step = "select-event-option-" + number;
        require(new OpportunityJson.Text(step).equals(metadata.get("selected_step")) && metadata.get("selected_step").equals(preparedPlan.get("selected_step"))
            && metadata.get("event_instance_id").equals(preparedPlan.get("event_instance_id")) && metadata.get("option_number").equals(preparedPlan.get("option_number"))
            && new OpportunityJson.IntegerValue(BigInteger.valueOf(number - 1L)).equals(preparedPlan.get("native_option_index")), "resolution metadata changed the actual prepared option");
        var event = obj(metadata.get("normalized_active_event"), "original normalized event");
        require(event.members().keySet().equals(Set.of("source", "instance_id", "option_count", "title", "options"))
            && event.get("instance_id").equals(metadata.get("event_instance_id")), "resolution normalized event fields or instance changed");
        BigInteger count = positive(event.get("option_count"));
        require(count.compareTo(BigInteger.valueOf(4096)) <= 0 && count.equals(BigInteger.valueOf(arr(event.get("options")).items().size())),
            "resolution normalized option count changed");
        var selected = arr(event.get("options")).items().stream().map(row -> obj(row, "normalized option"))
            .filter(row -> metadata.get("option_number").equals(row.get("option_number"))).findFirst().orElseThrow();
        var row = new OpportunityJson.Obj(Map.of("event_index", integer(1), "event_instance_id", metadata.get("event_instance_id"),
            "title", event.get("title"), "visible_options", event.get("options"), "selected_option_number", metadata.get("option_number"),
            "selected_option_index", integer(number - 1L), "selected_visible_text", selected.get("label"),
            "strategy", metadata.get("selection_strategy"), "source", event.get("source")));
        return validateOrdinaryEvent(row, instance, number);
    }
    public static OpportunityJson.Obj validateOrdinaryEvent(OpportunityJson.Obj row, int actualInstance, int actualOption) {
        require(actualInstance > 0 && actualOption > 0 && actualOption <= 4096 && row.members().keySet().equals(ROW_FIELDS), "exact ordinary event identity/fields required");
        require(integer(1).equals(row.get("event_index")) && integer(actualInstance).equals(row.get("event_instance_id"))
            && integer(actualOption).equals(row.get("selected_option_number")) && integer(actualOption - 1L).equals(row.get("selected_option_index"))
            && STRATEGIES.contains(text(row.get("strategy"))), "ordinary event does not describe its actual prepared choice");
        require(row.get("title") == OpportunityJson.Nil.INSTANCE || row.get("title") instanceof OpportunityJson.Text, "nullable original title required");
        String source = text(row.get("source")); require(!source.isEmpty(), "original event source required");
        var options = arr(row.get("visible_options")); require(options.items().size() <= 4096, "bounded original option rows required");
        var raw = new OpportunityJson.Obj(Map.of("source", row.get("source"), "instance_id", row.get("event_instance_id"),
            "title", row.get("title"), "options", options));
        var normalized = NativeActiveEvent.normalize(DriverJson.toNode(raw), source);
        require(DriverJson.toNode(options).equals(normalized.get("options")), "ordinary option fields differ from original normalized contract");
        var selected = options.items().stream().map(value -> obj(value, "original normalized option"))
            .filter(value -> integer(actualOption).equals(value.get("option_number"))).findFirst().orElseThrow();
        require(new OpportunityJson.Bool(true).equals(selected.get("enabled")) && Objects.equals(selected.get("label"), row.get("selected_visible_text")),
            "ordinary selected label or enabled flag changed");
        return row;
    }
    private static OpportunityJson.Obj obj(OpportunityJson.Value value, String field) { return OpportunityJson.object(value, field); }
    private static OpportunityJson.Arr arr(OpportunityJson.Value value) { require(value instanceof OpportunityJson.Arr, "event option array required"); return (OpportunityJson.Arr)value; }
    private static BigInteger positive(OpportunityJson.Value value) { require(value instanceof OpportunityJson.IntegerValue && ((OpportunityJson.IntegerValue)value).value().signum() > 0, "positive exact event integer required"); return ((OpportunityJson.IntegerValue)value).value(); }
    private static String text(OpportunityJson.Value value) { require(value instanceof OpportunityJson.Text, "event text required"); return ((OpportunityJson.Text)value).value(); }
    private static String text(RetainedJson.Value value) { require(value instanceof RetainedJson.StringValue, "event text required"); return ((RetainedJson.StringValue)value).value(); }
    private static OpportunityJson.IntegerValue integer(long value) { return new OpportunityJson.IntegerValue(BigInteger.valueOf(value)); }
    private static RetainedJson.ObjectValue retained(OpportunityJson.Obj value) { return RetainedJson.object(RetainedJson.parse(DriverJson.encode(value))); }
    private static RetainedJson.Value retainedField(OpportunityJson.Obj value, String key) { return value.get(key) == null ? RetainedJson.NULL : RetainedJson.parse(DriverJson.encode(value.get(key))); }
    private static OpportunityJson.Obj opportunity(RetainedJson.ObjectValue value) { return DriverJson.object(RetainedJson.encode(value), DriverJson.MAX_NATIVE_BYTES); }
    private static void require(boolean value, String message) { StrictJson.require(value, message); }
}
