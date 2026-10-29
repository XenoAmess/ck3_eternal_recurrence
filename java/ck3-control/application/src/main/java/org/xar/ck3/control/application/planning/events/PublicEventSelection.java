package org.xar.ck3.control.application.planning.events;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryHistory;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.eventoutcome.RegisteredEventMaterial;
import org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge;
import org.xar.ck3.control.wave2.events.registered.RegisteredVanillaEventPolicy;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewedEventConsumer;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventCodec;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback;

/** Pure exact-option selection over the caller's original observed event DATA.
 * This producer grants no read, private-token or native-submit authority. */
public final class PublicEventSelection {
    private PublicEventSelection() { }

    /** Same exact-row preparation input after an automatic producer has chosen its option.
     * Selection provenance remains automatic; it must not be represented as a caller's explicit choice.
     */
    static OpportunityJson.Obj derivedPlan(PlanningRequest actual, int optionNumber, Optional<Integer> expectedInstance,
            RegisteredEventKnowledge knowledge, TrustedEventSourceContext trusted, RegisteredEventCore.ContextValidator validator) {
        // The existing typed EXPLICIT_REQUESTED capture records the exact option passed to
        // this shared row validator. Automatic policy provenance lives only in resolution metadata.
        return plan(actual, optionNumber, expectedInstance, knowledge, trusted, validator)
            .with("public_explicit_selection", new OpportunityJson.Bool(false));
    }

    public static OpportunityJson.Obj plan(PlanningRequest actual, int optionNumber, Optional<Integer> expectedInstance,
            RegisteredEventKnowledge knowledge, TrustedEventSourceContext trusted, RegisteredEventCore.ContextValidator validator) {
        return plan(actual, optionNumber, expectedInstance, knowledge, Optional.of(Objects.requireNonNull(trusted)), validator);
    }
    public static OpportunityJson.Obj plan(PlanningRequest actual,int optionNumber,Optional<Integer> expectedInstance,
            RegisteredEventKnowledge knowledge,Optional<TrustedEventSourceContext> trusted,RegisteredEventCore.ContextValidator validator){
        Objects.requireNonNull(actual);Objects.requireNonNull(validator);
        var context=RegisteredEventCore.currentContext(actual,OrdinaryPolicy.Draft.empty(),validator).orElseThrow(()->new IllegalArgumentException("same-instance original event read unavailable"));
        return plan(EventDecisionInput.ordinary(actual,context),optionNumber,expectedInstance,knowledge,trusted);
    }
    static OpportunityJson.Obj derivedPlan(EventDecisionInput actual,int optionNumber,Optional<Integer> expectedInstance,
            RegisteredEventKnowledge knowledge,TrustedEventSourceContext trusted){return plan(actual,optionNumber,expectedInstance,knowledge,trusted).with("public_explicit_selection",new OpportunityJson.Bool(false));}
    public static OpportunityJson.Obj plan(EventDecisionInput actual,int optionNumber,Optional<Integer> expectedInstance,
            RegisteredEventKnowledge knowledge,TrustedEventSourceContext trusted){return plan(actual,optionNumber,expectedInstance,knowledge,Optional.of(Objects.requireNonNull(trusted)));}
    public static OpportunityJson.Obj plan(EventDecisionInput actual,int optionNumber,Optional<Integer> expectedInstance,
            RegisteredEventKnowledge knowledge,Optional<TrustedEventSourceContext> trusted){
        Objects.requireNonNull(actual); Objects.requireNonNull(expectedInstance); Objects.requireNonNull(knowledge);
        Objects.requireNonNull(trusted);
        StrictJson.require(optionNumber > 0 && optionNumber <= 4096, "bounded authored native option number required");
        expectedInstance.ifPresent(value -> StrictJson.require(value > 0, "positive full int32 event instance required"));
        StrictJson.require(actual.paused(), "public event selection requires its original paused planning frame");
        ObjectValue snapshot = retained(actual.snapshot());
        Value rawEvent = snapshot.contains("active_event") ? snapshot.get("active_event") : snapshot.get("current_event");
        StrictJson.require(rawEvent instanceof ObjectValue, "actual active event required");
        ObjectValue event = (ObjectValue) rawEvent;
        BigInteger instance = integer(event.get("instance_id")), count = integer(event.get("option_count"));
        StrictJson.require(instance.signum() > 0 && instance.bitLength() <= 31 && count.signum() > 0 && count.compareTo(BigInteger.valueOf(4096)) <= 0,
            "actual event identity/count outside its native contract");
        expectedInstance.ifPresent(value -> StrictJson.require(instance.equals(BigInteger.valueOf(value)), "actual event instance differs from public expectation"));
        StrictJson.require(BigInteger.valueOf(optionNumber).compareTo(count) <= 0, "requested option is outside the actual authored event count");
        ObjectValue context = RegisteredEventCore.currentContext(actual)
            .orElseThrow(() -> new IllegalArgumentException("same-instance original event read is unavailable; no explicit option was submitted"));
        StrictJson.require("available".equals(text(context.get("status"))), "same-instance event window unavailable");
        BigInteger nativeIndex = BigInteger.valueOf(optionNumber - 1L);
        List<ObjectValue> rows = array(context.get("options")).stream().map(RetainedJson::object).toList();
        StrictJson.require(rows.stream().map(row -> integer(row.get("native_option_index"))).distinct().count() == rows.size(), "duplicate actual native option index");
        StrictJson.require(rows.stream().map(row -> integer(row.get("rendered_index"))).distinct().count() == rows.size(), "duplicate actual rendered option index");
        ObjectValue selected = rows.stream().filter(row -> nativeIndex.equals(integer(row.get("native_option_index")))).findFirst()
            .orElseThrow(() -> new IllegalArgumentException("requested authored native option is absent from the actual window"));
        BigInteger rendered = integer(selected.get("rendered_index"));
        StrictJson.require(rendered.signum() >= 0 && bool(selected.get("shown")) && bool(selected.get("enabled")), "requested actual option is hidden or disabled");
        OperationKey operation = new OperationKey("select-event-option-" + optionNumber);
        boolean advertised = actual.actionSteps().contains(operation);
        var recommendation = new RegisteredVanillaEventPolicy(knowledge).recommend(new RegisteredVanillaEventPolicy.Input(context,
            field(snapshot, "played_character", "character_id"), event.get("option_count"), Optional.empty(), snapshot.getOrNull("played_character"),
            snapshot.getOrNull("event_opinion_observations"), new ArrayValue(OrdinaryHistory.collect(actual.history()).rows().stream()
                .map(PublicEventSelection::retained).map(Value.class::cast).toList())));
        ObjectValue plan = fallback(actual, snapshot, event, context, selected, optionNumber, advertised, recommendation.wire(), trusted);
        if (recommendation.status() == RegisteredVanillaEventPolicy.Status.RECOMMENDED
                && recommendation.selection().orElseThrow().nativeIndex().equals(nativeIndex)) {
            ObjectValue decision = recommendation.wire();
            Optional<ObjectValue> material = RegisteredEventMaterial.plan(decision, snapshot);
            plan = plan.with("event_decision", decision).with("registered_requested_option_match", new BooleanValue(true));
            if (material.isPresent()) plan = plan.with("event_material_postcondition", material.orElseThrow());
            String gate = RegisteredEventCore.materialGate(text(context.get("event_definition_key")), material);
            if (gate != null) plan = plan.with("selected_step", RetainedJson.NULL).with("reason", new StringValue(gate));
            Optional<ObjectValue> phases = RegisteredEventCore.exactSourcePhases().project(decision,
                knowledge.query(text(decision.get("ck3_build")), text(context.get("event_definition_key"))));
            if (phases.isPresent()) plan = plan.with("event_effect_phase", phases.orElseThrow());
        }
        // The original requested row is provenance. Its indicators are not a complete predicted effect or an ACK.
        return opportunity(plan.with("event_window_context", context).with("event_read_binding", RegisteredEventCore.binding(actual))
            .with("event_instance_id", new IntegerValue(instance)).with("option_number", new IntegerValue(BigInteger.valueOf(optionNumber)))
            .with("native_option_index", new IntegerValue(nativeIndex)).with("rendered_index", new IntegerValue(rendered))
            .with("selected_native_event_option", selected).with("public_explicit_selection", new BooleanValue(true))
            .with("material_effects_verified", new BooleanValue(false)));
    }
    private static ObjectValue fallback(EventDecisionInput actual, ObjectValue snapshot, ObjectValue event, ObjectValue context,
            ObjectValue selected, int optionNumber, boolean advertised, ObjectValue registry, Optional<TrustedEventSourceContext> trusted) {
        ObjectValue diagnostics = RetainedJson.object(snapshot.get("diagnostics"));
        var frame = new UnhandledEventFallback.FrameBinding(text(snapshot.get("snapshot_id")), integer(snapshot.get("revision")), integer(snapshot.get("native_revision")),
            integer(snapshot.get("date_raw")), text(snapshot.get("episode_run_id")), integer(diagnostics.get("connection_generation")), integer(diagnostics.get("bridge_pid")),
            bool(snapshot.get("paused")), bool(snapshot.get("map_ready")), integer(field(snapshot, "played_character", "character_id")));
        BigInteger nativeIndex = BigInteger.valueOf(optionNumber - 1L);
        String operation = "select-event-option-" + optionNumber;
        var selection = new UnhandledEventFallback.Selection(integer(selected.get("rendered_index")), nativeIndex, BigInteger.valueOf(optionNumber),
            nullableText(selected.get("resolved_name")), true, operation, List.of());
        var fallback = new UnhandledEventFallback.Plan(advertised ? UnhandledEventFallback.Phase.FIRST_RENDERED_OPTION : UnhandledEventFallback.Phase.FIRST_RENDERED_UNSUPPORTED,
            advertised ? operation : null, advertised ? "retain and submit the caller's exact legal native option" : "the actual backend has no requested native event step",
            text(context.get("event_definition_key")), integer(event.get("instance_id")), integer(event.get("option_count")), frame, selection, context, registry, event,
            UnhandledEventFallback.DisplayPolicy.EXPLICIT_REQUESTED);
        ObjectValue plan = UnhandledEventCodec.legacyPlan(fallback);
        if (trusted.isPresent()) {
            ObjectValue capture = RetainedJson.object(plan.get("unhandled_event_fallback"));
            var reviewed = SourceReviewedEventConsumer.lookup(capture, trusted.orElseThrow());
            boolean known = reviewed.entry().isPresent();
            plan = plan.with("unhandled_event_fallback", capture.with("registry_known", new BooleanValue(known))
                .with("offline_followup_required", new BooleanValue(!known)).with("source_knowledge", reviewed.audit()));
        }
        return plan;
    }
    private static Value field(ObjectValue value, String object, String key) { return RetainedJson.object(value.get(object)).getOrNull(key); }
    private static ObjectValue retained(OpportunityJson.Obj value) { return RetainedJson.object(RetainedJson.parse(OpportunityJson.encode(value))); }
    private static OpportunityJson.Obj opportunity(ObjectValue value) { return OpportunityJson.object(OpportunityJson.parse(RetainedJson.encode(value)), "public exact native event plan"); }
    private static BigInteger integer(Value value) { StrictJson.require(value instanceof IntegerValue, "exact event integer required"); return ((IntegerValue)value).value(); }
    private static String text(Value value) { StrictJson.require(value instanceof StringValue, "event text required"); return ((StringValue)value).value(); }
    private static String nullableText(Value value) { return value == null || value instanceof NullValue ? null : text(value); }
    private static boolean bool(Value value) { StrictJson.require(value instanceof BooleanValue, "exact event boolean required"); return ((BooleanValue)value).value(); }
    private static List<Value> array(Value value) { StrictJson.require(value instanceof ArrayValue, "actual event option vector required"); return ((ArrayValue)value).values(); }
}
