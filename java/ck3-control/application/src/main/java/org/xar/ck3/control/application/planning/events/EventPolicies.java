package org.xar.ck3.control.application.planning.events;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.OrdinaryCorePolicy;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.wave2.events.uirecoveryidentity.SourceReviewedMandatoryPlanner;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.choiceplanning.ChoicePlanningJson;
import org.xar.ck3.control.wave2.events.choiceplanning.MandatoryChoicePlanner;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome;
import org.xar.ck3.control.wave2.events.eventoutcome.RegisteredEventMaterial;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembership;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembershipCodec;
import org.xar.ck3.control.wave2.events.eventtraits.PoetTraitOutcome;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.wave2.events.unhandledevent.EventOptionAvailability;
import org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewedEventConsumer;
import org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewedInteractionContinuation;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventCodec;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback;
import org.xar.ck3.control.wave2.military.warresults.WarResultsCodec;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy;

/** Actual immutable-snapshot/history collectors feeding the existing Java producers. */
public final class EventPolicies {
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build());
    private static final String EVENT_QUERY = "query-current-event-window-context-v1";
    private static final String INTERACTION_QUERY = "query-pending-character-interaction-context-v1";
    private EventPolicies() { }

    /** The native observation owner supplies a real supported post-read contract, never a preselected action.
     * Absence explicitly blocks the command; adapters must not invent a schema, null window, or ACK effect. */
    @FunctionalInterface public interface NativeExpectationPort {
        Optional<ExpectedPostcondition> expected(PlanningRequest request, OperationKey operation,
            OpportunityJson.Obj retainedPlan, Optional<PoetTraitOutcome.Expectation> traitMaterial);
    }
    /** Domain decoders publish an actual query result and, when needed, its normalized same-frame SDK projection. */
    public record ReadPublication(OpportunityJson.Obj result, Optional<OpportunityJson.Obj> snapshot) {
        public ReadPublication { Objects.requireNonNull(result); Objects.requireNonNull(snapshot); }
    }
    public static List<OrdinaryPolicy> policies(ExactRef source, Optional<TrustedEventSourceContext> trusted, NativeExpectationPort observations,
            PlanningReadPort reads, List<EventReadBinding<?>> readContracts, RegisteredEventCore.ContextValidator contextValidator,
            EventIncidentCapturePort incidentCapture, OrdinaryCorePolicy.CommandBinding sameSharedBinding) {
        return policies(source,trusted,observations,reads,readContracts,contextValidator,incidentCapture,sameSharedBinding,Optional.empty());
    }
    public static List<OrdinaryPolicy> policies(ExactRef source, Optional<TrustedEventSourceContext> trusted, NativeExpectationPort observations,
            PlanningReadPort reads, List<EventReadBinding<?>> readContracts, RegisteredEventCore.ContextValidator contextValidator,
            EventIncidentCapturePort incidentCapture, OrdinaryCorePolicy.CommandBinding sameSharedBinding,
            Optional<EventSourceReadContext> mandatorySources) {
        Objects.requireNonNull(mandatorySources);
        Objects.requireNonNull(source); Objects.requireNonNull(trusted); Objects.requireNonNull(observations);
        Objects.requireNonNull(reads); Objects.requireNonNull(contextValidator); readContracts = List.copyOf(readContracts);
        Objects.requireNonNull(incidentCapture);Objects.requireNonNull(sameSharedBinding);
        StrictJson.require(readContracts.size() <= 8 && readContracts.stream().map(EventReadBinding::operation).distinct().count() == readContracts.size(), "finite unique exact query contracts required");
        return List.of(new Policy(PlanningStage.TERMINAL_AND_FOREGROUND_WINDOWS, source, trusted, observations, reads, readContracts, contextValidator, incidentCapture,sameSharedBinding,mandatorySources),
            new Policy(PlanningStage.EVENT_AND_INTERACTION_CONTINUATION, source, trusted, observations, reads, readContracts, contextValidator, incidentCapture,sameSharedBinding,mandatorySources),
            new Policy(PlanningStage.EVENT_MATERIAL_POSTCONDITION, source, trusted, observations, reads, readContracts, contextValidator, incidentCapture,sameSharedBinding,mandatorySources));
    }
    private record Policy(PlanningStage stage, ExactRef implementationSource, Optional<TrustedEventSourceContext> trusted,
                          NativeExpectationPort nativeObservations, PlanningReadPort reads, List<EventReadBinding<?>> readContracts,
                          RegisteredEventCore.ContextValidator contextValidator, EventIncidentCapturePort incidentCapture,
                          OrdinaryCorePolicy.CommandBinding sameSharedBinding,Optional<EventSourceReadContext> mandatorySources) implements OrdinaryPolicy {
        @Override public Decision evaluate(PlanningRequest request, Draft previous) {
            Objects.requireNonNull(request); Objects.requireNonNull(previous);
            PlanningRequest current = request; Set<OperationKey> attempted = new HashSet<>();
            for (int count = 0; count <= 5; count++) {
                Decision result = evaluateCollected(current, previous);
                if (!(result instanceof Replace replacement) || !replacement.draft().policy().equals("native-read-collector")) return result;
                OperationKey operation = new OperationKey(replacement.draft().phase());
                if (!attempted.add(operation)) return diagnosticWait(current, null, "same native query already returned no usable window", incidentCapture);
                Optional<EventReadBinding<?>> contract = readContracts.stream().filter(row -> row.supports(operation)).findFirst();
                if (contract.isEmpty()) {
                    Decision capture = diagnosticWait(current, null, "missing actual typed native read binding: " + operation.value(), incidentCapture);
                    return capture instanceof Stop ? capture : incomplete("the composition root has no exact typed read binding for " + operation.value());
                }
                EventReadBinding.Outcome observed;
                try { observed = contract.orElseThrow().read(reads, current, operation, incidentCapture); }
                catch (IllegalArgumentException | java.io.UncheckedIOException rejected) {
                    String reason = "actual native material/read selection rejected: " + rejected.getMessage();
                    Decision capture = diagnosticWait(current, null, reason, incidentCapture);
                    return capture instanceof Stop ? capture : incomplete(reason);
                }
                EventReadBinding.Captured captured;
                switch (observed) {
                    case EventReadBinding.Unavailable unavailable -> { return diagnosticWait(current, null, unavailable.result().reason(), incidentCapture); }
                    case EventReadBinding.Captured known -> captured = known;
                }
                ReadPublication publication = captured.publication();
                PlanningObservation base = current.observations(); OpportunityJson.Obj next = publication.snapshot().orElse(base.snapshot());
                for (String key : List.of("active_event", "pending_character_interaction", "one_life_terminal_reason", "paused", "map_ready"))
                    StrictJson.require(Objects.equals(base.snapshot().get(key), next.get(key)), "read publication changed native binding field " + key);
                StrictJson.require(Objects.equals(object(base.snapshot().get("played_character")).get("alive"), object(next.get("played_character")).get("alive")), "read publication changed player life state");
                List<OpportunityJson.Obj> history = new ArrayList<>(base.history());
                history.add(captured.history());
                current = new PlanningRequest(current.before(), current.source(), current.sessionId(), current.deadline(),
                    new PlanningObservation(next, history, base.actionSteps(), base.bridgeCapabilities(), base.battleSpeedReadiness(),
                        base.actionFacts(), base.campaignGoal(), base.crossRunPlan(), base.initialLifestyleFocusRequired()));
            }
            return new Wait("bounded native foreground query budget reached");
        }
        private Decision evaluateCollected(PlanningRequest request, Draft previous) {
            return switch (stage) {
                case TERMINAL_AND_FOREGROUND_WINDOWS -> foreground(request, previous, sameSharedBinding, mandatorySources, incidentCapture, readContracts);
                case EVENT_AND_INTERACTION_CONTINUATION -> continuation(request, previous, trusted, nativeObservations, contextValidator, incidentCapture);
                case EVENT_MATERIAL_POSTCONDITION -> material(request, previous, nativeObservations);
                default -> throw new IllegalStateException("event policy owns exactly three declared stages");
            };
        }
    }

    private static OrdinaryPolicy.Decision foreground(PlanningRequest request, OrdinaryPolicy.Draft previous, OrdinaryCorePolicy.CommandBinding sameSharedBinding, Optional<EventSourceReadContext> mandatorySources, EventIncidentCapturePort captures, List<EventReadBinding<?>> readContracts) {
        if (previous.kind() == OrdinaryPolicy.Kind.TERMINAL) return new OrdinaryPolicy.Keep("terminal owner retains priority");
        ObjectNode snapshot = snapshot(request);
        for (WarResultsPolicy.WindowKind kind : WarResultsPolicy.WindowKind.values()) {
            ObjectNode input = wrapper(request, kind.inputSchema()); input.set("snapshot", windowProjection(snapshot, kind));
            OperationKey query = new OperationKey(kind.queryStep());
            boolean installedRead = request.observations().bridgeCapabilities().contains(kind.queryCapability())
                    && readContracts.stream().anyMatch(binding -> binding.supports(query));
            // Typed READ availability belongs to this collector; world-action authority stays unchanged.
            if (installedRead && !request.observations().actionSteps().contains(query)) input.withArray("action_steps").add(query.value());
            Optional<WarResultsPolicy.Plan> planned = WarResultsPolicy.plan(WarResultsCodec.decode(bytes(input), kind), kind);
            if (planned.isPresent()) {
                if (installedRead && planned.orElseThrow().selectedStep().equals(Optional.of(WarResultsPolicy.SelectedStep.QUERY)))
                    return readNeeded(query.value());
                return proposeForeground(request, parse(WarResultsCodec.encodePlan(planned, kind)), sameSharedBinding);
            }
        }
        ObjectNode mandatory = wrapper(request, ChoicePlanningJson.SCHEMA);
        ObjectNode modalSnapshot = pick(snapshot, List.of("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id",
            "active_event", "pending_character_interaction", "top_exclusive_modal_choice_hint"));
        actorAndDiagnostics(snapshot, modalSnapshot); mandatory.set("snapshot", modalSnapshot);
        var commands = mandatory.putArray("commands"); request.observations().history().forEach(row -> commands.add(parse(OpportunityJson.encode(row))));
        var input = ChoicePlanningJson.decodeRetained(mandatory);
        JsonNode result = mandatorySources.isPresent()
                ? parse(SourceReviewedMandatoryPlanner.encode(new SourceReviewedMandatoryPlanner(mandatorySources.orElseThrow()).plan(new SourceReviewedMandatoryPlanner.Input(input))))
                : parse(ChoicePlanningJson.encode(new MandatoryChoicePlanner().plan(input)));
        if (result instanceof ObjectNode planned) {
            for (int index=request.observations().history().size()-1;index>=0;index--) {
                var row=request.observations().history().get(index);
                if (new OpportunityJson.Text("query-mandatory-choice-v1").equals(row.get("command"))) {
                    OpportunityJson.Value reference=row.get("native_read_original_receipt");
                    if(reference!=null)planned.set("mandatory_choice_original_read",parse(OpportunityJson.encode(reference)));
                    break;
                }
            }
        }
        if (!result.isNull()) {
            if(result instanceof ObjectNode blocked&&blocked.path("selected_step").isNull()) {
                var plan=OpportunityJson.object(OpportunityJson.parse(bytes(blocked)),"actual blocked mandatory plan");
                var diagnostic=NativeWindowDiagnostic.plan(new NativeWindowDiagnostic.Source(request.before(),request.observations().snapshot(),
                        new ArrayList<>(request.observations().history()),Optional.empty(),Optional.of(plan),blocked.path("reason").asText("native modal selection unavailable")));
                try { if(diagnostic.isPresent())captures.captureBlocked(request,diagnostic.orElseThrow()); }
                catch(IOException failure){return incomplete("actual blocked mandatory capture unavailable: "+failure.getMessage());}
            }
            return proposeForeground(request, result, sameSharedBinding);
        }
        return new OrdinaryPolicy.NotApplicable("both real war-window policies and native mandatory-choice producer returned no candidate");
    }

    /** Delegate to the actual Root owner: public planning may already own the scope, while
     * ordinary AUTO preparation re-enters currentPlanning and validates this original request.
     * The owner retains the complete canonical command, read receipts, claims, origin and contract.
     * Preparation is not dispatch; only the sole coordinator may submit after the owned freeze exits. */
    private static OrdinaryPolicy.Decision proposeForeground(PlanningRequest request,JsonNode rawPlan,OrdinaryCorePolicy.CommandBinding sameSharedBinding) {
        if(!(rawPlan instanceof ObjectNode plan))return incomplete("foreground producer returned no object proposal");
        JsonNode selected=plan.get("selected_step");
        if(selected==null||selected.isNull())return new OrdinaryPolicy.Wait(plan.path("reason").asText("native foreground producer is blocked or awaiting its prior result"));
        OperationKey operation=new OperationKey(text(selected));
        if(!request.observations().actionSteps().contains(operation))return incomplete("selected exact native step is not advertised: "+operation.value());
        if(operation.value().startsWith("query-"))return readNeeded(operation.value());
        OpportunityJson.Obj retainedPlan=OpportunityJson.object(OpportunityJson.parse(bytes(plan)),"original foreground plan");
        boolean windowClose=java.util.Arrays.stream(WarResultsPolicy.WindowKind.values()).anyMatch(kind->kind.closeStep().equals(operation.value()));
        // Window2 close decoders consume empty caller arguments; their owner derives the actual
        // expected revision and preflight receipt vector from this same request. The raw plan is audit detail.
        OpportunityJson.Obj selectedArguments=windowClose||operation.value().equals("pause-map")?new OpportunityJson.Obj(Map.of()):retainedPlan;
        var bound=Objects.requireNonNull(sameSharedBinding.propose(request,operation,selectedArguments,retainedPlan,OrdinaryPolicy.Purpose.WORLD_ACTION,Optional.empty()));
        if(bound instanceof OrdinaryCorePolicy.MissingHandler missing)return incomplete(missing.reason());
        ActionCommand command=switch(bound) {
            case OrdinaryCorePolicy.OwnerPrepared owner->owner.preparation().requireOriginalChoice(request,operation,selectedArguments,retainedPlan);
            case OrdinaryCorePolicy.Prepared exact->{
                StrictJson.require(exact.command().arguments().equals(selectedArguments),"exact foreground binding cannot enrich or replace selected arguments");yield exact.command();
            }
            case OrdinaryCorePolicy.MissingHandler missing->throw new IllegalStateException(missing.reason());
        };
        StrictJson.require(command.before().equals(request.before())&&command.source().equals(request.source())
            &&command.sessionId().equals(request.sessionId())&&command.operation().equals(operation)&&!command.deadline().isAfter(request.deadline()),
            "shared foreground preparation changed the original Root frame/source/session/selected operation or extended its deadline");
        return new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft(plan.path("policy").asText("one-life-turn-v1"),plan.path("phase").asText("native_window"),
            plan.path("reason").asText("native foreground selected one owned operation"),OrdinaryPolicy.Kind.FOREGROUND,Optional.of(command),
            OrdinaryPolicy.Purpose.WORLD_ACTION,Optional.empty(),retainedPlan),"retain the actual shared owner's complete prepared command; no raw-plan reconstruction or native dispatch");
    }

    record FirstDisplayed(OpportunityJson.Obj plan, Optional<SourceReviewedEventConsumer.KnowledgeStatus> sourceKnowledge) {
        FirstDisplayed { Objects.requireNonNull(plan); Objects.requireNonNull(sourceKnowledge); }
    }
    /** Shared original capture/source-knowledge reader. No additional native observation, preparation or dispatch. */
    static Optional<FirstDisplayed> firstDisplayedPlan(PlanningRequest request,OrdinaryPolicy.Draft previous,
            ObjectNode currentContext,Optional<TrustedEventSourceContext> trusted){
        return firstDisplayedPlan(EventDecisionInput.ordinary(request,retained(currentContext)),previous,currentContext,trusted);
    }
    @FunctionalInterface
    private interface BlockedSourceFailureCapture {
        void capture(OpportunityJson.Obj originalPlan) throws IOException;
    }
    private static Optional<FirstDisplayed> firstDisplayedPlan(PlanningRequest request,OrdinaryPolicy.Draft previous,
            ObjectNode currentContext,Optional<TrustedEventSourceContext> trusted,BlockedSourceFailureCapture failureCapture){
        return firstDisplayedPlan(EventDecisionInput.ordinary(request,retained(currentContext)),previous,currentContext,trusted,failureCapture);
    }
    static Optional<FirstDisplayed> firstDisplayedPlan(EventDecisionInput request,OrdinaryPolicy.Draft previous,
            ObjectNode currentContext,Optional<TrustedEventSourceContext> trusted){
        return firstDisplayedPlan(request,previous,currentContext,trusted,ignored->{ });
    }
    private static Optional<FirstDisplayed> firstDisplayedPlan(EventDecisionInput request,OrdinaryPolicy.Draft previous,
            ObjectNode currentContext,Optional<TrustedEventSourceContext> trusted,BlockedSourceFailureCapture failureCapture){
        ObjectNode snapshot = (ObjectNode) parse(OpportunityJson.encode(request.snapshot())); JsonNode event = snapshot.get("active_event");
        Optional<ObjectNode> context = Optional.of(currentContext);
        ObjectNode frame = frame(snapshot); var options = new ArrayList<UnhandledEventFallback.Option>();
        JsonNode rawOptions = context.orElseThrow().get("options");
        if (rawOptions == null || !rawOptions.isArray()) return Optional.empty();
        RetainedJson.ObjectValue retainedContext = retained(currentContext);
        for (JsonNode row : rawOptions) options.add(new UnhandledEventFallback.Option(integer(row.get("rendered_index")), integer(row.get("native_option_index")),
            bool(row.get("shown")), bool(row.get("enabled")), row.path("resolved_name").asText(null),
            EventOptionAvailability.observation(retainedContext, RetainedJson.object(RetainedJson.parse(bytes(row))))));
        var binding = new UnhandledEventFallback.FrameBinding(text(frame.get("snapshot_id")), integer(frame.get("revision")), integer(frame.get("native_revision")),
            integer(frame.get("date_raw")), text(frame.get("episode_run_id")), integer(frame.get("connection_generation")), integer(frame.get("bridge_pid")),
            bool(frame.get("paused")), bool(frame.get("map_ready")), integer(frame.get("actor_character_id")));
        var sourceContext = context.orElseThrow();
        var input = new UnhandledEventFallback.Request(new UnhandledEventFallback.Snapshot(binding,
            new UnhandledEventFallback.ActiveEvent(integer(event.get("instance_id")), integer(event.get("option_count"))), retainedSnapshot(snapshot)),
            new UnhandledEventFallback.Context(integer(sourceContext.get("current_event_instance_id")), integer(sourceContext.get("snapshot_revision")),
                integer(sourceContext.get("date_raw")), sourceContext.path("event_definition_key").asText(null), options, retained(sourceContext)),
            retained((ObjectNode) event), retained(previousPlan(previous)), steps(request));
        var fallback = UnhandledEventFallback.planFirstDisplayed(input);
        if (fallback.isEmpty()) return Optional.empty();
        ObjectNode fallbackPlan = (ObjectNode) parse(UnhandledEventCodec.encode(fallback));
        if (trusted.isPresent()) {
            try {
                var reviewed = SourceReviewedEventConsumer.continueWithExistingPlan(retained(fallbackPlan), retainedSnapshot(snapshot), steps(request), trusted.orElseThrow());
                return Optional.of(new FirstDisplayed(opportunityPlan(nativeEventArguments((ObjectNode) parse(reviewed.encode()), context.orElseThrow())), Optional.of(reviewed.status())));
            } catch (TrustedEventSourceContext.UnavailableException unavailable) {
                if (fallback.orElseThrow().selectedStep() == null) {
                    try { failureCapture.capture(opportunityPlan(fallbackPlan)); }
                    catch (IOException | RuntimeException captureFailure) {
                        if (captureFailure != unavailable) unavailable.addSuppressed(captureFailure);
                    }
                }
                throw unavailable;
            }
        }
        // The raw same-frame capture and exact first display/native mapping remain in the complete detail.
        // Registry source knowledge is optional for an unfamiliar legal option, not a long-game stop gate.
        return Optional.of(new FirstDisplayed(opportunityPlan(nativeEventArguments(fallbackPlan, context.orElseThrow())), Optional.empty()));
    }
    private static OpportunityJson.Obj opportunityPlan(JsonNode plan) {
        return OpportunityJson.object(OpportunityJson.parse(bytes(plan)), "original captured first-display plan");
    }

    private static OrdinaryPolicy.Decision continuation(PlanningRequest request, OrdinaryPolicy.Draft previous,
            Optional<TrustedEventSourceContext> trusted, NativeExpectationPort observations, RegisteredEventCore.ContextValidator contextValidator,
            EventIncidentCapturePort incidentCapture) {
        if (previous.command().isPresent()) return new OrdinaryPolicy.Keep("the existing dedicated selected action has priority");
        ObjectNode snapshot = snapshot(request); JsonNode event = snapshot.get("active_event"), pending = snapshot.get("pending_character_interaction");
        if (event != null && event.isObject()) {
            if (previous.detail().get("dedicated_policy_blocked") instanceof OpportunityJson.Bool blocked && blocked.value())
                return new OrdinaryPolicy.Wait("the actual dedicated event policy is blocked; retain its full native evidence");
            Optional<ObjectNode> context = RegisteredEventCore.currentContext(request, previous, contextValidator)
                .map(value -> (ObjectNode) parse(RetainedJson.encode(value)));
            if (context.isEmpty()) return query(request, EVENT_QUERY, "active_event_window_query", observations, incidentCapture);
            if (previous.detail().get("material_policy_blocked") instanceof OpportunityJson.Bool blocked && blocked.value()) {
                var diagnostic=NativeWindowDiagnostic.plan(new NativeWindowDiagnostic.Source(request.before(),request.observations().snapshot(),
                        new ArrayList<>(request.observations().history()),Optional.of(OpportunityJson.parse(bytes(context.orElseThrow()))),
                        Optional.of(previous.detail()),previous.reason()));
                try { if(diagnostic.isPresent())incidentCapture.captureBlocked(request,diagnostic.orElseThrow()); }
                catch(IOException failure){return incomplete("registered material diagnosis capture failed: "+failure.getMessage());}
            }
            Optional<FirstDisplayed> fallback = firstDisplayedPlan(request, previous, context.orElseThrow(), trusted,
                    originalPlan -> incidentCapture.captureBlocked(request, originalPlan));
            if (fallback.isEmpty()) return diagnosticWait(request, context.orElseThrow(), "same-frame event/native option projection unavailable", incidentCapture);
            return propose(request, parse(OpportunityJson.encode(fallback.orElseThrow().plan())), observations, Optional.empty(), incidentCapture);
        }
        if (pending != null && pending.isObject()) {
            if (SourceReviewedInteractionContinuation.originalPlan(retained(previousPlan(previous))).blockedMarriageReply())
                return new OrdinaryPolicy.Wait("retain the exact blocked marriage diagnosis and its ordinary continuation");
            Optional<ObjectNode> context = currentContext(request, INTERACTION_QUERY, "pending_character_interaction_context", "pending_interaction_id", pending.get("instance_id"));
            if (context.isEmpty()) return query(request, INTERACTION_QUERY, "pending_character_interaction_context_query", observations, incidentCapture);
            if (trusted.isEmpty()) return diagnosticWait(request, context.orElseThrow(), "stock GUI left-reply semantics have no actual source binding", incidentCapture);
            ObjectNode input = StrictJson.object(); input.put("schema", SourceReviewedInteractionContinuation.SCHEMA).put("registry_requested", true);
            input.set("snapshot", snapshot); input.set("context", context.orElseThrow()); input.set("original_plan", previousPlan(previous));
            var actions = input.putArray("action_steps"); steps(request).forEach(actions::add);
            JsonNode result = parse(SourceReviewedInteractionContinuation.encode(SourceReviewedInteractionContinuation.plan(
                SourceReviewedInteractionContinuation.decode(bytes(input)), trusted.orElseThrow())));
            if (result.isNull()) return diagnosticWait(request, context.orElseThrow(), "current native interaction has no materializable left reply", incidentCapture);
            return propose(request, result, observations, Optional.empty(), incidentCapture);
        }
        return new OrdinaryPolicy.NotApplicable("no active event or pending character interaction in the actual snapshot");
    }

    public static OrdinaryPolicy.Decision captureUnavailable(PlanningRequest actual, String diagnosis, EventIncidentCapturePort captures) {
        return diagnosticWait(actual, null, diagnosis, captures);
    }

    private static OrdinaryPolicy.Decision diagnosticWait(PlanningRequest request, JsonNode actualContext, String reason, EventIncidentCapturePort incidentCapture) {
        var source = new NativeWindowDiagnostic.Source(request.before(),
                OpportunityJson.object(request.observations().snapshot(), "actual diagnostic snapshot"),
                new ArrayList<>(request.observations().history()),
                Optional.ofNullable(actualContext).map(node -> OpportunityJson.parse(bytes(node))), Optional.empty(), reason);
        var plan = NativeWindowDiagnostic.plan(source);
        if (plan.isEmpty()) return new OrdinaryPolicy.Wait(reason);
        try { incidentCapture.captureBlocked(request, plan.orElseThrow()); }
        catch (IOException failure) { return incomplete("actual unavailable-window capture failed: " + failure.getMessage()); }
        return new OrdinaryPolicy.Wait(reason);
    }

    private static OrdinaryPolicy.Decision material(PlanningRequest request, OrdinaryPolicy.Draft previous, NativeExpectationPort observations) {
        if (previous.command().isEmpty() || !previous.command().orElseThrow().operation().value().startsWith("select-event-option-"))
            return new OrdinaryPolicy.NotApplicable("the selected ordinary action is not an event option");
        ObjectNode snapshot = snapshot(request); JsonNode event = snapshot.get("active_event");
        if (event == null || !event.isObject()) return incomplete("event material planning lost the active native instance");
        Optional<ObjectNode> context = currentContext(request, EVENT_QUERY, "current_event_window_context", "current_event_instance_id", event.get("instance_id"));
        if (context.isEmpty()) return incomplete("event material planning requires the same-frame native event context");
        String key = context.orElseThrow().path("event_definition_key").asText();
        if (!PoetTraitOutcome.EVENT.equals(key)) return new OrdinaryPolicy.Keep("retain the core producer's existing scalar or dedicated material postcondition");
        ActionCommand old = previous.command().orElseThrow(); int index = Integer.parseInt(old.operation().value().substring("select-event-option-".length())) - 1;
        if (index != 0 && index != 1) return new OrdinaryPolicy.Keep("poet native2 uses the existing scalar stress branch");
        OpportunityJson.Value actualDecision = old.arguments().get("event_decision");
        if (!(actualDecision instanceof OpportunityJson.Obj)) actualDecision = previous.detail().get("event_decision");
        if (!(actualDecision instanceof OpportunityJson.Obj decision))
            return incomplete("poet material requires the original source-bound registered event decision; a reconstructed recommendation is not evidence");
        Optional<PoetTraitOutcome.Expectation> expected = RegisteredEventMaterial.poet(
            RetainedJson.object(RetainedJson.parse(OpportunityJson.encode(decision))), retainedSnapshot(snapshot));
        if (expected.isEmpty()) return incomplete("the dedicated trait material route did not handle its exact source-reviewed option");
        OpportunityJson.Obj arguments = old.arguments().with("event_material_postcondition", OpportunityJson.parse(PoetTraitOutcome.encode(expected.orElseThrow())));
        Optional<ExpectedPostcondition> nativeExpected = observations.expected(request, old.operation(), arguments, expected);
        if (nativeExpected.isEmpty()) return incomplete("native observation owner has not supplied the independent trait-plus-window postcondition contract");
        ActionCommand annotated = new ActionCommand(old.actionId(), old.before(), old.source(), old.sessionId(), old.operation(), arguments, nativeExpected.orElseThrow(), old.claims(), old.deadline());
        return new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft(previous.policy(), previous.phase(), previous.reason(), previous.kind(), Optional.of(annotated), previous.purpose(),
            previous.domain(), retainedPlanDetail(previous, arguments)),
            "attach the native trait material expectation to the existing sole event command; no second action");
    }

    private static OrdinaryPolicy.Decision query(PlanningRequest request, String step, String phase, NativeExpectationPort observations,
            EventIncidentCapturePort incidentCapture) {
        if (!request.observations().actionSteps().contains(new OperationKey(step))) {
            String reason="actual backend does not advertise required typed query " + step;
            var captured=diagnosticWait(request,null,reason,incidentCapture);
            return captured instanceof OrdinaryPolicy.Stop ? captured : incomplete(reason);
        }
        return readNeeded(step);
    }
    /** One native argument ABI. The retained choice must match a uniquely displayed, selectable row. */
    private static ObjectNode nativeEventArguments(ObjectNode plan, ObjectNode context) {
        if (plan.get("selected_step") == null || plan.get("selected_step").isNull()) return plan;
        JsonNode decision = plan.get("event_decision");
        StrictJson.require(decision != null && decision.isObject(), "original native event decision required");
        BigInteger nativeIndex = integer(decision.get("selected_native_option_index"));
        BigInteger number = integer(decision.get("selected_option_number"));
        StrictJson.require(nativeIndex.signum() >= 0 && number.equals(nativeIndex.add(BigInteger.ONE))
                && ("select-event-option-" + number).equals(text(plan.get("selected_step"))), "event decision number/native step differs");
        List<JsonNode> matching = new ArrayList<>();
        JsonNode options = context.get("options");
        StrictJson.require(options != null && options.isArray(), "actual normalized native options required");
        for (JsonNode row : options) if (nativeIndex.equals(integer(row.get("native_option_index")))) matching.add(row);
        StrictJson.require(matching.size() == 1, "selected native event index is not unique in the current display");
        JsonNode selected = matching.getFirst();
        StrictJson.require(bool(selected.get("shown")) && EventOptionAvailability.selectionAllowed(retained(context),
            RetainedJson.object(RetainedJson.parse(bytes(selected)))), "selected exact native event option is not displayed/selectable");
        BigInteger rendered = integer(selected.get("rendered_index"));
        StrictJson.require(rendered.signum() >= 0, "actual nonnegative rendered option index required");
        if (decision.has("selected_rendered_index")) StrictJson.require(rendered.equals(integer(decision.get("selected_rendered_index"))), "event producer rendered mapping differs");
        plan.put("event_instance_id", integer(context.get("current_event_instance_id")));
        plan.put("option_number", number); plan.put("native_option_index", nativeIndex); plan.put("rendered_index", rendered);
        return plan;
    }
    private static OrdinaryPolicy.Decision propose(PlanningRequest request, JsonNode rawPlan, NativeExpectationPort observations,
            Optional<PoetTraitOutcome.Expectation> material, EventIncidentCapturePort incidentCapture) {
        if (!rawPlan.isObject()) return incomplete("domain producer returned no object proposal");
        ObjectNode plan = (ObjectNode) rawPlan; JsonNode selected = plan.get("selected_step");
        if (selected == null || selected.isNull()) {
            if (plan.path("unhandled_event_fallback").isObject() || plan.path("unhandled_interaction_fallback").isObject()) {
                try { incidentCapture.captureBlocked(request, OpportunityJson.object(OpportunityJson.parse(bytes(plan)), "actual blocked native fallback")); }
                catch (IOException failure) { return incomplete("actual blocked-window incident capture unavailable: " + failure.getMessage()); }
            }
            return new OrdinaryPolicy.Wait(plan.path("reason").asText("native domain producer is blocked or awaiting its prior outcome"));
        }
        OperationKey operation = new OperationKey(text(selected));
        if (!request.observations().actionSteps().contains(operation)) return incomplete("selected exact native step is not advertised: " + operation.value());
        if (operation.value().startsWith("query-")) return readNeeded(operation.value());
        OpportunityJson.Obj retainedPlan = OpportunityJson.object(OpportunityJson.parse(bytes(plan)), "event/native domain plan");
        Optional<ExpectedPostcondition> expected = observations.expected(request, operation, retainedPlan, material);
        if (expected.isEmpty()) {
            if (plan.path("unhandled_event_fallback").isObject() || plan.path("unhandled_interaction_fallback").isObject()) {
                ObjectNode unsubmitted = plan.deepCopy(); unsubmitted.put("unsubmitted_candidate_step", operation.value()).putNull("selected_step");
                try { incidentCapture.captureBlocked(request, OpportunityJson.object(OpportunityJson.parse(bytes(unsubmitted)), "actual unsubmitted native candidate")); }
                catch (IOException failure) { return incomplete("actual unsubmitted-window capture failed: " + failure.getMessage()); }
            }
            return incomplete("native observation owner has no real independent postcondition for " + operation.value());
        }
        String id = "event-" + digest(request.sessionId() + "|" + request.before().frame().snapshotId() + "|" + operation.value() + "|" + new String(bytes(plan), StandardCharsets.UTF_8));
        Claims claims = new Claims(Set.of(), Set.of(), Set.of(request.before().frame().identity().player()), Set.of("foreground-window"));
        ActionCommand command = new ActionCommand(id, request.before(), request.source(), request.sessionId(), operation, retainedPlan, expected.orElseThrow(), claims, request.deadline());
        boolean read = operation.value().startsWith("query-");
        return new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft(plan.path("policy").asText("one-life-turn-v1"), plan.path("phase").asText("native_window"),
            plan.path("reason").asText("native domain producer selected an exact typed operation"), OrdinaryPolicy.Kind.FOREGROUND, Optional.of(command),
            read ? OrdinaryPolicy.Purpose.READ_ONLY : OrdinaryPolicy.Purpose.WORLD_ACTION, Optional.empty(), retainedPlan), "actual collector to Java producer to the shared sole ActionCommand");
    }
    private static Optional<ObjectNode> currentContext(PlanningRequest request, String query, String field, String instanceField, JsonNode instance) {
        ObjectNode snapshot = snapshot(request);
        List<OpportunityJson.Obj> history = request.observations().history();
        for (int index = history.size() - 1; index >= 0; index--) {
            JsonNode row = parse(OpportunityJson.encode(history.get(index))); JsonNode result = row.get("result");
            if ("auto-turn".equals(row.path("command").asText()) && result != null && result.path("auto_turn").isObject()) {
                JsonNode auto = result.get("auto_turn"); if (!query.equals(auto.path("selected_step").asText())) continue; result = auto.get("result");
            } else if (!query.equals(row.path("command").asText())) continue;
            if (!row.path("ok").isBoolean() || !row.path("ok").booleanValue() || result == null || !result.isObject()) continue;
            JsonNode context = result.get(field);
            if (context == null || !context.isObject() || !Objects.equals(context.get(instanceField), instance)) continue;
            if (!query.equals(result.path("step").asText()) || !result.path("accepted").isBoolean()
                || !result.path("accepted").booleanValue() || !Objects.equals(result.get("status"), context.get("status"))
                || !"available".equals(context.path("status").asText())) continue;
            if (!Objects.equals(context.get("snapshot_revision"), snapshot.get("native_revision")) || !Objects.equals(context.get("date_raw"), snapshot.get("date_raw"))) continue;
            if (!Objects.equals(result.get("queried_snapshot_id"), snapshot.get("snapshot_id"))
                || !Objects.equals(result.get("queried_revision"), snapshot.get("revision"))
                || !Objects.equals(result.get("queried_native_revision"), snapshot.get("native_revision"))) continue;
            return Optional.of((ObjectNode) context);
        }
        return Optional.empty();
    }
    private static ObjectNode wrapper(PlanningRequest request, String schema) {
        ObjectNode object = StrictJson.object(); object.put("schema", schema);
        var steps = object.putArray("action_steps"); steps(request).forEach(steps::add);
        var caps = object.putArray("bridge_capabilities"); request.observations().bridgeCapabilities().stream().sorted().forEach(caps::add); return object;
    }
    private static ObjectNode windowProjection(ObjectNode snapshot, WarResultsPolicy.WindowKind kind) {
        ObjectNode result = pick(snapshot, List.of("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id", "paused", "map_ready",
            kind.publicPrefix() + "_observation", kind.publicPrefix() + "_query_attempt", kind.publicPrefix() + "_close_pending", "war_results_window_v1_check_due", "war_results_window_v1_next_check_date_raw"));
        actorAndDiagnostics(snapshot, result); return result;
    }
    private static void actorAndDiagnostics(ObjectNode snapshot, ObjectNode result) {
        JsonNode actor = snapshot.get("played_character"), diagnostics = snapshot.get("diagnostics");
        if (actor instanceof ObjectNode object) result.set("played_character", pick(object, List.of("character_id")));
        else if (actor != null) result.set("played_character", actor);
        if (diagnostics instanceof ObjectNode object) result.set("diagnostics", pick(object, List.of("connection_generation", "bridge_pid")));
        else if (diagnostics != null) result.set("diagnostics", diagnostics);
    }
    private static ObjectNode frame(ObjectNode snapshot) {
        ObjectNode frame = pick(snapshot, List.of("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id", "paused", "map_ready"));
        frame.set("actor_character_id", snapshot.path("played_character").get("character_id"));
        frame.set("connection_generation", snapshot.path("diagnostics").get("connection_generation")); frame.set("bridge_pid", snapshot.path("diagnostics").get("bridge_pid")); return frame;
    }
    private static ObjectNode pick(ObjectNode source, List<String> fields) { ObjectNode result = StrictJson.object(); fields.forEach(key -> { if (source.has(key)) result.set(key, source.get(key)); }); return result; }
    private static ObjectNode previousPlan(OrdinaryPolicy.Draft draft) {
        ObjectNode result = (ObjectNode) parse(OpportunityJson.encode(draft.detail()));
        if (!result.has("policy")) result.put("policy", draft.policy());
        if (!result.has("phase")) result.put("phase", draft.phase());
        if (!result.has("reason")) result.put("reason", draft.reason());
        if (!result.has("selected_step")) result.putNull("selected_step");
        return result;
    }
    private static OpportunityJson.Obj retainedPlanDetail(OrdinaryPolicy.Draft draft, OpportunityJson.Obj arguments) {
        return draft.detail().with("event_material_postcondition", arguments.get("event_material_postcondition"));
    }
    private static ObjectNode snapshot(PlanningRequest request) { return (ObjectNode) parse(OpportunityJson.encode(request.observations().snapshot())); }
    private static List<String> steps(EventDecisionInput request){return request.actionSteps().stream().map(OperationKey::value).sorted().toList();}
    private static List<String> steps(PlanningRequest request) { return request.observations().actionSteps().stream().map(OperationKey::value).sorted().toList(); }
    private static RetainedJson.ObjectValue retained(ObjectNode node) { return RetainedJson.object(RetainedJson.parse(bytes(node))); }
    private static RetainedJson.ObjectValue retainedSnapshot(ObjectNode node) {
        return RetainedJson.object(RetainedJson.parse(bytes(node), new RetainedJson.ParseBudget(DriverJson.MAX_NATIVE_BYTES, DriverJson.MAX_NATIVE_BYTES, 128)));
    }
    private static OpportunityJson.Obj object(OpportunityJson.Value value) { return OpportunityJson.object(value, "event native projection object"); }
    private static OrdinaryPolicy.Replace readNeeded(String step) {
        return new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft("native-read-collector", step, "collect the registered typed query synchronously in the original paused frame",
            OrdinaryPolicy.Kind.FOREGROUND, Optional.empty(), OrdinaryPolicy.Purpose.READ_ONLY, Optional.empty(),
            new OpportunityJson.Obj(Map.of("selected_step", new OpportunityJson.Text(step)))), "read collection precedes the domain producer; no query ActionCommand");
    }
    private static BigInteger integer(JsonNode node) { StrictJson.require(node != null && node.isIntegralNumber(), "exact native integer required"); return node.bigIntegerValue(); }
    private static Boolean bool(JsonNode node) { StrictJson.require(node != null && node.isBoolean(), "exact native boolean required"); return node.booleanValue(); }
    private static String text(JsonNode node) { return StrictJson.text(node); }
    private static byte[] bytes(JsonNode node) { try { return JSON.writeValueAsBytes(node); } catch (IOException error) { throw new IllegalArgumentException("event boundary JSON encoding failed", error); } }
    private static JsonNode parse(byte[] bytes) { try { return JSON.readTree(bytes); } catch (IOException error) { throw new IllegalArgumentException("event boundary JSON decoding failed", error); } }
    private static OrdinaryPolicy.Stop incomplete(String reason) { return new OrdinaryPolicy.Stop(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN, reason); }
    private static String digest(String text) { try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(text.getBytes(StandardCharsets.UTF_8))); } catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); } }
}
