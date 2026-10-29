package org.xar.ck3.control.application.planning.prisoners;

import static org.xar.ck3.control.application.planning.OrdinaryPolicy.*;
import static org.xar.ck3.control.application.planning.prisoners.PrisonerPlanningPorts.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.governance.succession.SuccessionCodec;
import org.xar.ck3.control.wave2.governance.succession.SuccessionPlanningProducer;

/** Ordinary preflight/tail adapter. Pure projection is persisted only through the sole configured writer authority. */
public final class SuccessionOrdinaryPolicy12004 implements OrdinaryPolicy {
    private final PlanningStage stage;
    private final ExactRef source;
    private final Bindings bindings;
    private final PrisonerCollector12004 prisoners;
    public SuccessionOrdinaryPolicy12004(PlanningStage stage, ExactRef source, Bindings bindings) {
        StrictJson.require(stage == PlanningStage.SUCCESSION_PREFLIGHT || stage == PlanningStage.DEFERRED_SUCCESSION_ROOT, "unsupported succession stage");
        this.stage = stage; this.source = Objects.requireNonNull(source); this.bindings = Objects.requireNonNull(bindings);
        prisoners = new PrisonerCollector12004(bindings);
    }
    @Override public PlanningStage stage() { return stage; }
    @Override public ExactRef implementationSource() { return source; }
    @Override public Decision evaluate(PlanningRequest request, Draft previous) {
        JsonNode snapshot = StrictJson.parse(OpportunityJson.encode(request.observations().snapshot()), 131072);
        JsonNode terminal = snapshot.get("one_life_terminal_reason");
        boolean changed = terminal != null && terminal.isTextual() && terminal.textValue().equals("played_character_changed");
        boolean deferred = previous.detail().get("succession_deferred_root_required") instanceof OpportunityJson.Bool value && value.value();
        if (stage == PlanningStage.DEFERRED_SUCCESSION_ROOT) {
            if (!deferred) return new NotApplicable("no deferred initial succession root");
            if (previous.command().map(value -> value.operation().equals(PrisonerOrdinaryPolicy12004.RELEASE)).orElse(false))
                return new Keep("the current accepted release retains its one-turn priority over initial root enrichment");
        }
        if (!changed && terminal != null && !terminal.isNull()) return new NotApplicable("other terminal handling remains with the terminal owner");
        if (!request.observations().paused() || !request.observations().mapReady())
            return new NotApplicable("succession preflight requires the current paused map");
        JsonNode expectation = snapshot.get("succession_expectation");
        boolean expectationPresent = expectation != null && !expectation.isNull();
        if (changed) {
            if (!expectationPresent) return new Stop(PlanningResult.StopReason.NATURAL_SUCCESSION_REQUIRED, "actual successor requires an original retained predecessor estate; none may be reconstructed after death");
            JsonNode reconciliation = snapshot.get("succession_reconciliation");
            if (reconciliation != null && reconciliation.isObject() && sameFrame(reconciliation.get("successor_binding"), snapshot))
                return new Keep("current actual successor reconciliation is already retained");
        } else {
            if (request.observations().foregroundPresent()) return new NotApplicable("foreground work retains priority before ordinary estate refresh");
            if (expectationPresent && sameFrame(expectation.get("binding"), snapshot)) {
                try { SuccessionCodec.decodeExpectation(StrictJson.canonical(expectation, SuccessionCodec.MAX_BYTES)); }
                catch (IllegalArgumentException malformed) { return new Wait("current retained estate is malformed; it is not refreshed from an assumed predecessor"); }
                return new Keep("original current-frame retained estate is already available");
            }
            if (!expectationPresent && stage == PlanningStage.SUCCESSION_PREFLIGHT
                    && !request.observations().initialLifestyleFocusRequired() && prisoners.retainedReleaseReady(request))
                return annotation(previous, "succession_deferred_root_required", new OpportunityJson.Bool(true),
                        "current source-bound accepted release may precede initial succession enrichment");
        }
        try {
            TurnBundleRead result = bindings.queries().readTurnBundle(request);
            if(result instanceof TurnBundleUnavailable unavailable)return new Wait("succession root unavailable: "+unavailable.reason());
            var known=(ObservedTurnBundle)result;
            StrictJson.require(known.before().equals(request.before())&&known.source().equals(request.source())
                    &&known.sessionId().equals(request.sessionId()),"succession service aggregate crossed actual planner target");
            JsonNode bundle = StrictJson.parse(known.value().bytes(), SuccessionCodec.MAX_BYTES);
            if ("unavailable".equals(bundle.path("status").textValue()))
                return new Wait("accepted root observation is unavailable; no retained estate or action permission inferred");
            ObjectNode input = StrictJson.object().put("schema", SuccessionPlanningProducer.SCHEMA)
                    .put("operation", changed ? "reconcile" : "retain").put("expected_revision", request.before().frame().revision());
            input.set("snapshot", snapshot); input.set("turn_bundle", bundle);
            if (changed) input.set("expectation", expectation);
            byte[] producerRequest = StrictJson.canonical(input, SuccessionCodec.MAX_BYTES);
            byte[] produced = SuccessionPlanningProducer.apply(producerRequest);
            SuccessionRecord value = new SuccessionRecord(changed ? RecordOperation.RECONCILE : RecordOperation.RETAIN,
                    new RawJson(producerRequest), new RawJson(produced), List.of(request.source().sourceRef(), known.originalRoot()));
            RecordResult stored = bindings.succession().record(request, value);
            if (stored instanceof RecordUnavailable unavailable) return new Wait("sole succession writer unavailable: " + unavailable.reason());
            Recorded recorded = (Recorded) stored;
            StrictJson.require(recorded.before().equals(request.before())
                    && Arrays.equals(StrictJson.canonical(StrictJson.parse(recorded.observedProjection().bytes(), 131072), 131072),
                            StrictJson.canonical(StrictJson.parse(produced, 131072), 131072)), "persisted projection readback differs from original pure producer");
            OpportunityJson.Obj detail = previous.detail().with(changed ? "succession_reconciliation" : "succession_expectation", object(produced))
                    .with("succession_persisted_head", object(StrictJson.canonical(recorded.persistedHead().toJson())))
                    .with("succession_deferred_root_required", new OpportunityJson.Bool(false));
            return new Replace(new Draft(previous.policy(), previous.phase(), previous.reason(), previous.kind(), previous.command(),
                    previous.purpose(), previous.domain(), detail), "pure succession projection committed/read back by the unique owner; no episode continuation inferred");
        } catch (IllegalArgumentException | java.io.IOException rejected) {
            String reason = rejected.getMessage() == null ? "succession source rejected" : rejected.getMessage();
            return new Wait(reason.substring(0, Math.min(1024, reason.length())));
        }
    }
    private static boolean sameFrame(JsonNode binding, JsonNode snapshot) {
        if (binding == null || !binding.isObject()) return false;
        for (String key : List.of("snapshot_id", "revision", "native_revision", "date_raw"))
            if (!Objects.equals(binding.get(key), snapshot.get(key))) return false;
        return true;
    }
}
