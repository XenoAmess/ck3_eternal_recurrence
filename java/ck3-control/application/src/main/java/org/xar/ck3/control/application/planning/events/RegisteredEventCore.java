package org.xar.ck3.control.application.planning.events;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.wave2.events.unhandledevent.EventOptionAvailability;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.planning.OrdinaryCorePolicy;
import org.xar.ck3.control.application.planning.OrdinaryHistory;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.planning.warentry.WarEntryCollector;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.registered.BookmarkRaiktorPolicy;
import org.xar.ck3.control.wave2.events.eventtraits.EventEffectPhase;
import org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge;
import org.xar.ck3.control.wave2.events.registered.RegisteredVanillaEventPolicy;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;

/**
 * Original strategy.py active-event branch at its real CORE call site.
 * Dedicated Raiktor precedes the complete registered producer; only the
 * later continuation stage resolves an unconsumed event; failed native reads
 * preserve the actual diagnostic before returning without an action.
 */
public final class RegisteredEventCore implements OrdinaryCorePolicy.CoreProducer {
    public static final String EVENT_QUERY = "query-current-event-window-context-v1";
    private static final String EVENT_SCOPE_CAPABILITY = "game.command.query-war-entry-assessments-raiktor-bookmark-saved-scope-v1";
    @FunctionalInterface public interface ReadContracts {
        Optional<EventReadBinding<?>> contract(OperationKey operation);
    }
    /** The production event-window codec validates historical/detail JSON before a policy sees it. */
    @FunctionalInterface public interface ContextValidator {
        Optional<ObjectValue> normalize(PlanningRequest request, ObjectValue rawContext);
    }
    /** This is the full outcome.py dispatcher, including dedicated army/religion/trait leaves. */
    @FunctionalInterface public interface MaterialPlanner {
        Optional<ObjectValue> plan(ObjectValue registryDecision, ObjectValue snapshot);
    }
    /** Exact source facts may annotate a plan; no fact is inferred from a window disappearance. */
    @FunctionalInterface public interface PhaseProjector {
        Optional<ObjectValue> project(ObjectValue registryDecision, ObjectValue knowledge);
    }
    private final RegisteredEventKnowledge knowledge;
    private final RegisteredVanillaEventPolicy policy;
    private final PlanningReadPort reads;
    private final ReadContracts contracts;
    private final ContextValidator contextValidator;
    private final MaterialPlanner materials;
    private final PhaseProjector phases;
    private final OrdinaryCorePolicy.CommandBinding binding;
    private final EventIncidentCapturePort incidentCapture;

    public RegisteredEventCore(RegisteredEventKnowledge knowledge, PlanningReadPort reads, ReadContracts contracts,
            ContextValidator contextValidator, MaterialPlanner materials, PhaseProjector phases, OrdinaryCorePolicy.CommandBinding binding) {
        this(knowledge, reads, contracts, contextValidator, materials, phases, binding, EventIncidentCapturePort.unavailable());
    }
    public RegisteredEventCore(RegisteredEventKnowledge knowledge, PlanningReadPort reads, ReadContracts contracts,
            ContextValidator contextValidator, MaterialPlanner materials, PhaseProjector phases, OrdinaryCorePolicy.CommandBinding binding,
            EventIncidentCapturePort incidentCapture) {
        this.incidentCapture = Objects.requireNonNull(incidentCapture);
        this.knowledge = Objects.requireNonNull(knowledge); this.policy = new RegisteredVanillaEventPolicy(knowledge);
        this.reads = Objects.requireNonNull(reads); this.contracts = Objects.requireNonNull(contracts);
        this.contextValidator = Objects.requireNonNull(contextValidator);
        this.materials = Objects.requireNonNull(materials); this.phases = Objects.requireNonNull(phases);
        this.binding = Objects.requireNonNull(binding);
    }
    public static PhaseProjector exactSourcePhases() {
        return (decision, knowledge) -> {
            Value rawProfile = decision.get("choice_effect_profile");
            if (!(rawProfile instanceof ObjectValue profile)) return Optional.empty();
            BigInteger index = integer(decision.get("selected_native_option_index"));
            if (index == null || index.signum() < 0 || index.bitLength() > 31) return Optional.empty();
            String key = text(decision.get("event_definition_key"));
            Value hashes = get(knowledge.get("analysis"),"source_sha256");
            for (Value anchor : profile.get("source_anchors") instanceof ArrayValue rows ? rows.values() : List.<Value>of()) {
                if (!(anchor instanceof StringValue named)) continue;
                String path = named.value(); int colon = path.lastIndexOf(':'); if (colon >= 0) path = path.substring(0,colon);
                Value rawDigest = profile.get("source_sha256");
                if (!(rawDigest instanceof StringValue)) rawDigest = get(hashes,path);
                if (!(rawDigest instanceof StringValue digest)) continue;
                var source = new EventEffectPhase.SourceBinding(text(decision.get("ck3_build")),text(decision.get("ck3_exe_sha256")),path,digest.value());
                Optional<EventEffectPhase.Phases> phases = EventEffectPhase.classify(key,source,index.intValueExact());
                if (phases.isPresent()) return Optional.of(RetainedJson.object(RetainedJson.parse(EventEffectPhase.encode(phases.orElseThrow()))));
            }
            return Optional.empty();
        };
    }

    @Override public OrdinaryPolicy.Decision evaluate(PlanningRequest request, OrdinaryPolicy.Draft previous) {
        Objects.requireNonNull(request); Objects.requireNonNull(previous);
        if (previous.command().isPresent() && previous.kind() == OrdinaryPolicy.Kind.FOREGROUND)
            return new OrdinaryPolicy.Keep("the selected foreground command retains its original priority");
        ObjectValue snapshot = retained(request.observations().snapshot());
        Value rawEvent = snapshot.contains("active_event") ? snapshot.get("active_event") : snapshot.get("current_event");
        if (!(rawEvent instanceof ObjectValue event)) return new OrdinaryPolicy.NotApplicable("the actual snapshot has no active event");
        StrictJson.require(positive(event.get("instance_id")) && positive(event.get("option_count")), "active event identity/count required");
        ObjectValue summary = object(Map.of("instance_id", event.get("instance_id"), "option_count", event.get("option_count"),
            "selected_option_number", RetainedJson.NULL, "selected_option_index", RetainedJson.NULL));
        if (!request.observations().paused()) return select(request, previous, plan("active_event_window_pause_required",
            "pause the map before querying the exact current event window", summary).with("selected_step", string("pause-map"))
                .with("required_step", string("pause-map")));
        if (!available(request, EVENT_QUERY)) return classified(previous, plan("active_event_window_query_unavailable",
            "the backend cannot query the exact paused active event", summary).with("required_step", string(EVENT_QUERY)));
        PlanningRequest current = request; java.util.HashSet<OperationKey> attempted = new java.util.HashSet<>();
        ObjectValue retainedRead = new ObjectValue(Map.of());
        for (int pass = 0; pass < 3; pass++) {
            Optional<ObjectValue> context = currentContext(current, previous, contextValidator);
            if (context.isEmpty()) {
                Collected collected = collect(current, new OperationKey(EVENT_QUERY), attempted);
                if (collected.request().isEmpty()) return collected.failure().orElseThrow();
                current = collected.request().orElseThrow(); retainedRead = collected.proof(); continue;
            }
            ObjectValue exact = context.orElseThrow();
            ObjectValue currentSnapshot = retained(current.observations().snapshot());
            ObjectValue fullSummary = summary.with("window_context_status", exact.getOrNull("status"))
                .with("window_match_count", exact.getOrNull("window_match_count")).with("readiness", exact.getOrNull("readiness"));
            ObjectValue base = plan("active_event_window_unavailable", "retain the same-frame event capture before continuation", fullSummary)
                .with("event_window_context", exact).with("event_read_binding", binding(current))
                .with("event_read_original_receipt", retainedRead);
            if (!is(exact.get("status"), "available"))
                return classified(previous, base.with("event_decision", object(Map.of("status", string("unavailable"),
                    "unavailable_reason", exact.getOrNull("unavailable_reason")))));
            List<Value> optionRows = array(exact.get("options"));
            long enabled = optionRows.stream().filter(row -> yes(get(row,"shown")) && yes(get(row,"enabled"))).count();
            long selectable = optionRows.stream().filter(row -> yes(get(row,"shown")) && EventOptionAvailability.selectionAllowed(exact, RetainedJson.object(row))).count();
            fullSummary = fullSummary.with("materialized_options", exact.get("options"))
                .with("materialized_option_count", number(optionRows.size())).with("enabled_materialized_option_count", number(enabled))
                .with("selectable_materialized_option_count", number(selectable))
                .with("semantic_decision_ready", bool(yes(get(exact.get("readiness"),"semantic_decision_ready"))));
            base = base.with("active_event", fullSummary);
            Optional<BookmarkRaiktorPolicy.Recommendation> dedicated = dedicatedRecommendation(current, exact);
            if (dedicated.isPresent()) {
                var chosen = dedicated.orElseThrow();
                ObjectValue dedicatedPlan = base.with("event_decision", chosen.wire())
                    .with("active_event", fullSummary.with("raiktor_decision", chosen.wire()));
                if (chosen.status() == BookmarkRaiktorPolicy.Status.BLOCKED)
                    return classified(previous, dedicatedPlan.with("phase", string("active_event_raiktor_contract_blocked"))
                        .with("reason", chosen.wire().get("reason")).with("dedicated_policy_blocked", bool(true)));
                if (chosen.status() == BookmarkRaiktorPolicy.Status.QUERY_REQUIRED) {
                    OperationKey operation = new OperationKey(text(chosen.wire().get("selected_step")));
                    Collected collected = collect(current, operation, attempted);
                    if (collected.request().isEmpty()) return collected.failure().orElseThrow();
                    current = collected.request().orElseThrow(); continue;
                }
                return select(current, previous, selected(dedicatedPlan, exact, chosen.nativeIndex().orElseThrow(),
                    "active_event_raiktor_source_reviewed_choice", text(chosen.wire().get("reason"))));
            }
            RegisteredVanillaEventPolicy.Recommendation recommendation = policy.recommend(new RegisteredVanillaEventPolicy.Input(
                exact, get(currentSnapshot.get("played_character"), "character_id"), event.get("option_count"), Optional.empty(),
                currentSnapshot.getOrNull("played_character"), currentSnapshot.getOrNull("event_opinion_observations"),
                retainedHistory(current)));
            ObjectValue decision = recommendation.wire();
            base = base.with("event_decision", decision).with("active_event", fullSummary.with("registry_decision", decision));
            if (recommendation.status() != RegisteredVanillaEventPolicy.Status.RECOMMENDED)
                return classified(previous, base.with("phase", string(recommendation.status() == RegisteredVanillaEventPolicy.Status.BLOCKED
                        ? "active_event_registry_contract_blocked" : "active_event_semantic_evidence_required"))
                    .with("reason", string("the exact-build registry did not produce a consumable option; preserve its original decision and capture")));
            // Original service.plan_turn captures fulfillment after the registered recommendation.
            OperationKey religionRead = new OperationKey("query-player-religion-context-v1");
            if ("rite_growth.0010".equals(text(decision.get("event_definition_key")))
                    && "1.20.0.4".equals(text(decision.get("ck3_build")))
                    && BigInteger.ZERO.equals(integer(decision.get("selected_native_option_index")))
                    && !currentSnapshot.contains("rite_growth_fulfillment_observation") && !attempted.contains(religionRead)) {
                Collected collected = collect(current, religionRead, attempted);
                if (collected.request().isPresent()) {
                    current = collected.request().orElseThrow(); retainedRead = collected.proof(); continue;
                }
                OrdinaryPolicy.Decision unavailable = collected.failure().orElseThrow();
                if (unavailable instanceof OrdinaryPolicy.Stop) return unavailable;
                // Independent material unavailability does not undo a legal reviewed modal choice.
                base = base.with("event_material_read_diagnosis", string(unavailable.reason()));
            }
            Optional<ObjectValue> material = Objects.requireNonNull(materials.plan(decision, currentSnapshot));
            if (material.isPresent()) base = base.with("event_material_postcondition", material.orElseThrow());
            String key = text(exact.get("event_definition_key"));
            Optional<ObjectValue> phase = Objects.requireNonNull(phases.project(decision, knowledge.query(
                text(decision.get("ck3_build")), key)));
            if (phase.isPresent()) base = base.with("event_effect_phase", phase.orElseThrow());
            String missing = materialGate(key, material);
            if (missing != null) return classified(previous, base.with("phase", string("active_event_registry_material_observation_blocked"))
                .with("reason", string("the selected source-reviewed option requires its same-frame material observation"))
                .with("event_decision", decision.with("status", string("blocked")).with("unavailable_reason", string(missing)))
                .with("material_policy_blocked", bool(true)));
            if (decision.get("campaign_utility_profile") instanceof ObjectValue utility) base = base.with("event_campaign_utility", utility);
            var selection = recommendation.selection().orElseThrow();
            ObjectValue selected = selected(base, exact, selection.nativeIndex(), "active_event_registry_choice",
                "the same-frame identity, player root, saved scopes and option projection match the exact-build registry");
            StrictJson.require(selection.optionNumber().equals(integer(selected.get("option_number")))
                && selection.renderedIndex().equals(integer(selected.get("rendered_index"))), "registry typed/native/rendered selection drift");
            return select(current, previous, selected);
        }
        return new OrdinaryPolicy.Wait("bounded event/read collection finished without a consumable same-frame policy result");
    }
    public static Optional<ObjectValue> currentContext(PlanningRequest request, OrdinaryPolicy.Draft previous, ContextValidator validator) {
        Objects.requireNonNull(validator);
        ObjectValue snapshot = retained(request.observations().snapshot());
        Value event = snapshot.contains("active_event") ? snapshot.get("active_event") : snapshot.get("current_event");
        if (!(event instanceof ObjectValue active)) return Optional.empty();
        List<OpportunityJson.Obj> history = OrdinaryHistory.collect(request.observations().history()).rows();
        for (int index = history.size()-1; index >= 0; index--) {
            OpportunityJson.Obj row = history.get(index);
            if (!OrdinaryHistory.successful(row) || !OrdinaryHistory.effectiveCommand(row).filter(EVENT_QUERY::equals).isPresent()) continue;
            Optional<OpportunityJson.Obj> result = OrdinaryHistory.effectiveCommandResult(row);
            if (result.isEmpty()) continue;
            ObjectValue wire = retained(result.orElseThrow()); Value candidate = wire.get("current_event_window_context");
            if (!(candidate instanceof ObjectValue context) || !sameFrame(snapshot,active,context)) continue;
            if (!is(wire.get("step"),EVENT_QUERY) || !yes(wire.get("accepted")) || !Objects.equals(wire.get("status"),context.get("status"))) continue;
            if (!Objects.equals(wire.get("queried_snapshot_id"),snapshot.get("snapshot_id"))
                || !Objects.equals(wire.get("queried_revision"),snapshot.get("revision"))
                || !Objects.equals(wire.get("queried_native_revision"),snapshot.get("native_revision"))
                || !Objects.equals(wire.get("snapshot_revision"),snapshot.get("native_revision"))
                || !Objects.equals(wire.get("current_event_instance_id"),active.get("instance_id"))
                || !Objects.equals(wire.get("date_raw"),snapshot.get("date_raw"))) continue;
            Optional<ObjectValue> normalized = normalized(request,active,context,validator);
            if (normalized.isPresent()) return normalized;
        }
        ObjectValue detail = retained(previous.detail());
        if (detail.get("event_window_context") instanceof ObjectValue context
                && binding(request).equals(detail.get("event_read_binding")) && sameFrame(snapshot,active,context))
            return normalized(request,active,context,validator);
        return Optional.empty();
    }
    /** Same pure dedicated producer for ordinary AUTO and the public resolver; no additional read or dispatch. */
    static Optional<BookmarkRaiktorPolicy.Recommendation> dedicatedRecommendation(PlanningRequest actual,ObjectValue context){
        return dedicatedRecommendation(EventDecisionInput.ordinary(actual,context),context);
    }
    static Optional<BookmarkRaiktorPolicy.Recommendation> dedicatedRecommendation(EventDecisionInput actual,ObjectValue context){
        Map<BigInteger,ObjectValue> assessments=new LinkedHashMap<>();
        WarEntryCollector.collect(actual.snapshot(),OrdinaryHistory.collect(actual.history()).rows()).assessments().forEach((id,row)->assessments.put(id,retained(row)));
        return BookmarkRaiktorPolicy.recommend(new BookmarkRaiktorPolicy.Input(context,retained(actual.snapshot()),assessments,
                actual.actionSteps().stream().map(OperationKey::value).collect(java.util.stream.Collectors.toUnmodifiableSet()),actual.focus(),actual.bridgeCapabilities().contains(EVENT_SCOPE_CAPABILITY)));
    }
    /** The real caller already normalized this exact original window. This pure guard grants no read authority. */
    static Optional<ObjectValue> currentContext(EventDecisionInput actual){
        ObjectValue snapshot=retained(actual.snapshot());Value event=snapshot.contains("active_event")?snapshot.get("active_event"):snapshot.get("current_event");
        return event instanceof ObjectValue active&&sameFrame(snapshot,active,actual.currentWindow())?Optional.of(actual.currentWindow()):Optional.empty();
    }
    private static Optional<ObjectValue> normalized(PlanningRequest request,ObjectValue event,ObjectValue raw,ContextValidator validator) {
        try {
            Optional<ObjectValue> result = Objects.requireNonNull(validator.normalize(request,raw));
            StrictJson.require(result.isEmpty() || sameFrame(retained(request.observations().snapshot()),event,result.orElseThrow()),
                "event normalizer changed exact instance/frame");
            return result;
        } catch (IllegalArgumentException rejected) { return Optional.empty(); }
    }
    private record Collected(Optional<PlanningRequest> request, ObjectValue proof, Optional<OrdinaryPolicy.Decision> failure) { }
    private Collected collect(PlanningRequest request, OperationKey operation, Set<OperationKey> attempted) {
        if (!attempted.add(operation)) return failed(EventPolicies.captureUnavailable(request, "same native query already returned no usable context", incidentCapture));
        Optional<EventReadBinding<?>> contract = Objects.requireNonNull(contracts.contract(operation));
        if (contract.isEmpty()) {
            String reason = "the composition root has no actual typed event/power read contract for " + operation.value();
            var captured = EventPolicies.captureUnavailable(request, reason, incidentCapture);
            return failed(captured instanceof OrdinaryPolicy.Stop ? captured : incomplete(reason));
        }
        StrictJson.require(contract.orElseThrow().supports(operation), "event read resolver changed selected operation");
        EventReadBinding.Outcome observed;
        try { observed = contract.orElseThrow().read(reads, request, operation, incidentCapture); }
        catch (IllegalArgumentException | java.io.UncheckedIOException rejected) {
            String reason = "actual event/power material selection rejected: " + rejected.getMessage();
            var capture = EventPolicies.captureUnavailable(request, reason, incidentCapture);
            return failed(capture instanceof OrdinaryPolicy.Stop ? capture : incomplete(reason));
        }
        EventReadBinding.Captured captured;
        switch (observed) {
            case EventReadBinding.Unavailable unavailable -> { return failed(EventPolicies.captureUnavailable(request, unavailable.result().reason(), incidentCapture)); }
            case EventReadBinding.Captured known -> captured = known;
        }
        EventPolicies.ReadPublication publication = captured.publication();
        PlanningObservation before = request.observations();
        OpportunityJson.Obj snapshot = publication.snapshot().orElse(before.snapshot());
        for (String key : List.of("active_event","current_event","pending_character_interaction","one_life_terminal_reason","paused","map_ready"))
            StrictJson.require(Objects.equals(before.snapshot().get(key),snapshot.get(key)), "event read changed frozen binding " + key);
        StrictJson.require(Objects.equals(get(retained(before.snapshot()).get("played_character"),"alive"),
            get(retained(snapshot).get("played_character"),"alive")), "event read changed player life state");
        List<OpportunityJson.Obj> history = new ArrayList<>(before.history());
        ObjectValue proof = RetainedJson.object(RetainedJson.parse(org.xar.ck3.control.contracts.StrictJson.canonical(captured.originalReceipt().toJson())));
        history.add(captured.history());
        PlanningObservation next = new PlanningObservation(snapshot,history,before.actionSteps(),before.bridgeCapabilities(),before.battleSpeedReadiness(),
            before.actionFacts(),before.campaignGoal(),before.crossRunPlan(),before.initialLifestyleFocusRequired());
        return new Collected(Optional.of(new PlanningRequest(request.before(),request.source(),request.sessionId(),request.deadline(),next)),proof,Optional.empty());
    }
    private static Collected failed(OrdinaryPolicy.Decision decision) { return new Collected(Optional.empty(),new ObjectValue(Map.of()),Optional.of(decision)); }
    private OrdinaryPolicy.Decision select(PlanningRequest request, OrdinaryPolicy.Draft previous, ObjectValue plan) {
        String step = text(plan.get("selected_step"));
        if (!available(request,step)) return classified(previous,plan.with("phase",string("active_event_registry_choice_unsupported"))
            .with("selected_step",RetainedJson.NULL).with("required_step",string(step)));
        OperationKey operation = new OperationKey(step); OpportunityJson.Obj args = opportunity(plan);
        OpportunityJson.Obj selectedArguments=step.equals("pause-map")?new OpportunityJson.Obj(Map.of()):args;
        var bound = Objects.requireNonNull(binding.propose(request,operation,selectedArguments,args,OrdinaryPolicy.Purpose.WORLD_ACTION,Optional.empty()));
        if (bound instanceof OrdinaryCorePolicy.MissingHandler missing) return incomplete(missing.reason());
        ActionCommand command=switch(bound) {
            case OrdinaryCorePolicy.OwnerPrepared owner->owner.preparation().requireOriginalChoice(request,operation,selectedArguments,args);
            case OrdinaryCorePolicy.Prepared exact->{
                StrictJson.require(exact.command().arguments().equals(selectedArguments),"exact event binding cannot enrich or replace selected arguments");yield exact.command();
            }
            case OrdinaryCorePolicy.MissingHandler missing->throw new IllegalStateException(missing.reason());
        };
        StrictJson.require(command.before().equals(request.before()) && command.source().equals(request.source())
            && command.sessionId().equals(request.sessionId()) && command.operation().equals(operation)
            && !command.deadline().isAfter(request.deadline()), "event ActionCommand adapter changed the original choice/source/frame");
        return new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft("one-life-turn-v1",text(plan.get("phase")),text(plan.get("reason")),
            OrdinaryPolicy.Kind.FOREGROUND,Optional.of(command),OrdinaryPolicy.Purpose.WORLD_ACTION,Optional.empty(),args),
            "the actual Java event producer selected one action for the sole coordinator");
    }
    private static OrdinaryPolicy.Decision classified(OrdinaryPolicy.Draft previous,ObjectValue plan) {
        return new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft("one-life-turn-v1",text(plan.get("phase")),text(plan.get("reason")),
            OrdinaryPolicy.Kind.FOREGROUND,Optional.empty(),OrdinaryPolicy.Purpose.READ_ONLY,Optional.empty(),opportunity(plan)),
            "retain the complete registered decision and exact event frame for the later continuation producer");
    }
    private static ObjectValue selected(ObjectValue plan,ObjectValue context,BigInteger nativeIndex,String phase,String reason) {
        List<ObjectValue> selected = array(context.get("options")).stream().filter(ObjectValue.class::isInstance).map(ObjectValue.class::cast)
            .filter(row -> nativeIndex.equals(integer(row.get("native_option_index")))).toList();
        StrictJson.require(selected.size()==1 && yes(selected.getFirst().get("shown")) && EventOptionAvailability.selectionAllowed(context, selected.getFirst()), "selected exact event option not uniquely legal");
        BigInteger number = nativeIndex.add(BigInteger.ONE), rendered = integer(selected.getFirst().get("rendered_index"));
        StrictJson.require(nativeIndex.signum()>=0 && rendered!=null && rendered.signum()>=0, "exact native/rendered option mapping required");
        ObjectValue summary = (ObjectValue)plan.get("active_event");
        summary = summary.with("selected_option_number",number(number)).with("selected_option_index",number(nativeIndex))
            .with("selected_native_option_index",number(nativeIndex)).with("selected_rendered_index",number(rendered)).with("semantic_optimal",bool(false));
        return plan.with("phase",string(phase)).with("reason",string(reason)).with("selected_step",string("select-event-option-"+number))
            .with("active_event",summary).with("event_instance_id",context.get("current_event_instance_id")).with("option_number",number(number))
            .with("native_option_index",number(nativeIndex)).with("rendered_index",number(rendered));
    }
    static String materialGate(String key,Optional<ObjectValue> raw) {
        ObjectValue value = raw.orElse(new ObjectValue(Map.of())); boolean ready = is(value.get("status"),"ready"); BigInteger start = integer(value.get("starting_value"));
        if (key.equals("tgp_japan_yearly_events.1190") && !(ready && is(value.get("metric"),"played_character_prestige.raw")
                && is(value.get("expected_relation"),"strictly_decreasing") && start!=null && start.compareTo(BigInteger.valueOf(7_500_000))>=0))
            return "r0100_prestige_budget_or_observation_unavailable";
        if (key.equals("epidemic_events.5007") && !(ready && is(value.get("expected_relation"),"strictly_increasing")))
            return "r0092_material_stress_observation_unavailable";
        if (key.equals("stress_threshold_special.1001") && !(ready && start!=null && start.signum()>0))
            return "r0065_positive_stress_observation_unavailable";
        if (key.equals("epidemic_events.1020") && !ready) return "epidemic_flower_player_gold_unavailable";
        return null;
    }
    static ObjectValue binding(PlanningRequest request){return binding(request.before(),retained(request.observations().snapshot()));}
    static ObjectValue binding(EventDecisionInput actual){return binding(actual.before(),retained(actual.snapshot()));}
    private static ObjectValue binding(org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity before,ObjectValue snapshot){
        Map<String,Value> fields=new LinkedHashMap<>();for(String key:List.of("snapshot_id","revision","native_revision","date_raw","episode_run_id"))fields.put(key,snapshot.getOrNull(key));
        fields.put("machine_id",string(before.machineId()));fields.put("actor_character_id",get(snapshot.get("played_character"),"character_id"));
        fields.put("connection_generation",get(snapshot.get("diagnostics"),"connection_generation"));fields.put("bridge_pid",get(snapshot.get("diagnostics"),"bridge_pid"));return object(fields);
    }
    private static boolean sameFrame(ObjectValue snapshot,ObjectValue active,ObjectValue context) {
        return Objects.equals(context.get("current_event_instance_id"),active.get("instance_id"))
            && Objects.equals(context.get("snapshot_revision"),snapshot.get("native_revision")) && Objects.equals(context.get("date_raw"),snapshot.get("date_raw"));
    }
    private static ObjectValue plan(String phase,String reason,ObjectValue summary) {
        return object(Map.of("policy",string("one-life-turn-v1"),"phase",string(phase),"reason",string(reason),
            "selected_step",RetainedJson.NULL,"active_event",summary));
    }
    private static ArrayValue retainedHistory(PlanningRequest request) { return new ArrayValue(OrdinaryHistory.collect(request.observations().history()).rows().stream().map(RegisteredEventCore::retained).map(Value.class::cast).toList()); }
    private static Set<String> steps(PlanningRequest request) { return request.observations().actionSteps().stream().map(OperationKey::value).collect(java.util.stream.Collectors.toUnmodifiableSet()); }
    private static boolean available(PlanningRequest request,String step) { return step!=null && request.observations().actionSteps().contains(new OperationKey(step)); }
    private static ObjectValue retained(OpportunityJson.Obj value) {
        return RetainedJson.object(RetainedJson.parse(OpportunityJson.encode(value), new RetainedJson.ParseBudget(FullJsonTree.MAXIMUM_BYTES, FullJsonTree.MAXIMUM_BYTES, 128)));
    }
    private static OpportunityJson.Obj opportunity(ObjectValue value) {
        return OpportunityJson.object(OpportunityJson.parseComplete(RetainedJson.encode(value, FullJsonTree.MAXIMUM_BYTES), FullJsonTree.MAXIMUM_BYTES),"complete event proposal");
    }
    private static Value get(Value value,String key) { return value instanceof ObjectValue object ? object.getOrNull(key) : RetainedJson.NULL; }
    private static boolean positive(Value value) { BigInteger n=integer(value);return n!=null&&n.signum()>0; }
    private static boolean yes(Value value) { return value instanceof BooleanValue booleanValue&&booleanValue.value(); }
    private static boolean is(Value value,String wanted) { return wanted.equals(value instanceof StringValue s?s.value():null); }
    private static String text(Value value) { StrictJson.require(value instanceof StringValue,"event text token required"); return ((StringValue)value).value(); }
    private static BigInteger integer(Value value) { return value instanceof IntegerValue n?n.value():null; }
    private static List<Value> array(Value value) { StrictJson.require(value instanceof ArrayValue,"event option vector required"); return ((ArrayValue)value).values(); }
    private static ObjectValue object(Map<String,Value> fields) { return new ObjectValue(fields); }
    private static StringValue string(String value) { return new StringValue(value); }
    private static IntegerValue number(long value) { return number(BigInteger.valueOf(value)); }
    private static IntegerValue number(BigInteger value) { return new IntegerValue(value); }
    private static BooleanValue bool(boolean value) { return new BooleanValue(value); }
    private static OrdinaryPolicy.Stop incomplete(String reason) { return new OrdinaryPolicy.Stop(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN,reason); }
}
