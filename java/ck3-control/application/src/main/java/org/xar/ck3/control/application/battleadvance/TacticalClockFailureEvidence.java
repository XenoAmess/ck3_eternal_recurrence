package org.xar.ck3.control.application.battleadvance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.AdvanceObservationPort.Frame;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.session.AutoFailureDiagnostic;
import org.xar.ck3.control.application.routecontact.RouteContactComposite;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;

/** Actual tactical failure producer and archive reader. It never reads Native or changes an UNKNOWN verdict. */
public final class TacticalClockFailureEvidence implements AutoFailureDiagnostic.Port {
    public static final String BASIS_SCHEMA = "xar.java.tactical-clock-failure-originals/v1";
    public static final String PUBLIC_SCHEMA = "xar.tactical-clock-failure.v1";
    public static final String BASIS_FIELD = "tactical_clock_failure_originals_v1";
    private static final int MAX_ACTIONS = 12, MAX_WATCH = 32, MAX_TEXT = 1024;
    private final NativeEffectEvidence.FrameLoader frames;
    public TacticalClockFailureEvidence(NativeEffectEvidence.FrameLoader frames) { this.frames = Objects.requireNonNull(frames); }

    public static ExactRef preserve(ActionCommand parent, BattleAdvanceComposite.Failure actual, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(parent); Objects.requireNonNull(actual); Objects.requireNonNull(archive);
        require(actual.starting().identity().equals(parent.before()) && actual.plan().step().equals(parent.operation().value()), "tactical failure crossed the actual parent/entry frame");
        var body = StrictJson.object(); body.put("schema", BASIS_SCHEMA); body.put("parent_action_id", parent.actionId());
        body.put("machine_id", parent.before().machineId()); body.put("last_frame_observed_at_utc", actual.lastObserved().observedAt().toString());
        body.put("parent_body_sha256", ActionCodec.bodySha256(parent)); body.set("plan", OpportunityJson.toNode(actual.plan().json()));
        body.set("starting", preserveFrame(actual.starting(), archive)); body.set("ending", preserveFrame(actual.lastObserved(), archive));
        body.put("reason", actual.reason()); if (actual.cleanupError().isPresent()) body.put("cleanup_error", actual.cleanupError().orElseThrow()); else body.putNull("cleanup_error");
        body.set("armed", actual.arm().<JsonNode>map(SentinelObservation::toJson).orElseGet(() -> com.fasterxml.jackson.databind.node.NullNode.getInstance()));
        body.set("stopped", actual.stop().<JsonNode>map(SentinelObservation::toJson).orElseGet(() -> com.fasterxml.jackson.databind.node.NullNode.getInstance()));
        var actions = body.putArray("actions");
        for (ActionReceipt child : actual.actions()) actions.add(archive.preserveReceipt(child).toJson());
        var queries = body.putArray("status_queries");
        for (ExactRef ref : actual.queryEvidence()) { require(archive.referenceOf(archive.load(ref)).equals(ref), "tactical failure original query reference changed"); queries.add(ref.toJson()); }
        RawJson material = new RawJson(StrictJson.canonical(body)); ExactRef ref = archive.preserveMaterial(material);
        require(material.equals(archive.loadMaterial(ref)), "tactical failure basis archive readback differs");
        // The existing failed-result consumer still receives its original result schema.
        // The additional exact locator points to the complete source-bound basis.
        var compatible = (ObjectNode)StrictJson.parse(BattleAdvanceResultCodec.failed(actual).bytes()); compatible.set(BASIS_FIELD, ref.toJson());
        RawJson projection = new RawJson(StrictJson.canonical(compatible)); ExactRef projectedRef = archive.preserveMaterial(projection);
        require(projection.equals(archive.loadMaterial(projectedRef)), "tactical compatible failure archive readback differs"); return projectedRef;
    }
    private static ObjectNode preserveFrame(Frame actual, ActionPorts.OutcomeArchive archive) {
        var driver = actual.semantic().get("java_driver_facts_evidence");
        require(driver instanceof OpportunityJson.Obj, "actual tactical failure frame lacks its complete Driver manifest");
        ExactRef facts = ExactRef.fromJson(OpportunityJson.toNode(driver));
        exact(actual.originalEvidence(), archive.loadNativeFrame(actual.originalEvidence())); exact(facts, archive.loadFullMaterial(facts).bytes());
        var row = StrictJson.object(); row.set("native_frame", actual.originalEvidence().toJson()); row.set("driver_facts", facts.toJson());
        row.set("provenance", ObservationProvenanceCodec.encode(actual.provenance()));
        row.set("semantic", archive.preserveMaterial(RawJson.fullMaterial(org.xar.ck3.control.application.driver.DriverJson.encode(actual.semantic()))).toJson()); return row;
    }

    @Override public Optional<AutoFailureDiagnostic> project(ActionReceipt parent, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(parent); Objects.requireNonNull(archive);
        if (!(parent.state() instanceof ActionState.CompositeUnknown unresolved)) return Optional.empty();
        require(parent.bodySha256().equals(ActionCodec.bodySha256(parent.command())), "retained tactical parent body changed");
        var results = new ArrayList<AutoFailureDiagnostic>();
        for (ExactRef ref : unresolved.evidence()) {
            RawJson raw;
            try { raw = archive.loadMaterial(ref); } catch (IllegalArgumentException | UnsupportedOperationException unavailable) { continue; }
            exact(ref, raw.bytes());
            JsonNode projection = StrictJson.parse(raw.bytes());
            if (!projection.isObject() || !projection.has(BASIS_FIELD)) continue;
            ExactRef originalBasis = ExactRef.fromJson(projection.get(BASIS_FIELD)); RawJson originals = archive.loadMaterial(originalBasis); exact(originalBasis, originals.bytes());
            JsonNode node = StrictJson.parse(originals.bytes());
            require(node.isObject() && node.path("schema").isTextual() && BASIS_SCHEMA.equals(node.path("schema").textValue()), "tactical original-basis locator has an unsupported schema");
            if (!node.path("plan").path("scope").isTextual() || !BattleAdvanceStep.Scope.ROUTE_CONTACT_WINDOW.name().equals(node.path("plan").path("scope").textValue())) continue;
            var compatible = ((ObjectNode)projection).deepCopy(); compatible.remove(BASIS_FIELD);
            results.add(load(parent, unresolved, originalBasis, originals, compatible, archive));
        }
        require(results.size() <= 1, "two original tactical failure bases claim the same retained parent");
        return results.stream().findFirst();
    }
    private AutoFailureDiagnostic load(ActionReceipt parent, ActionState.CompositeUnknown retained, ExactRef basis, RawJson raw, JsonNode compatible, ActionPorts.OutcomeArchive archive) {
        exact(basis, raw.bytes());
        var row = StrictJson.object(StrictJson.parse(raw.bytes()), Set.of("schema", "machine_id", "last_frame_observed_at_utc", "parent_action_id", "parent_body_sha256", "plan", "starting", "ending", "reason", "cleanup_error", "armed", "stopped", "actions", "status_queries"));
        require(parent.command().actionId().equals(StrictJson.text(row.get("parent_action_id"))) && parent.bodySha256().equals(StrictJson.text(row.get("parent_body_sha256"))), "tactical basis crossed its retained parent body");
        require(parent.command().before().machineId().equals(StrictJson.text(row.get("machine_id")))
                && retained.execution().handlerId().equals(RouteContactComposite.HANDLER), "tactical public failure did not originate in the actual route-window parent handler/machine");
        BattleAdvancePlan plan = BattleAdvancePlan.decode(OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(row.get("plan"))), "plan"), parent.command().operation().value());
        require(plan.scope() == BattleAdvanceStep.Scope.ROUTE_CONTACT_WINDOW, "only original route-window failures carry the tactical public diagnostic");
        Frame starting = loadFrame(row.get("starting"), parent.command(), archive), ending = loadFrame(row.get("ending"), parent.command(), archive);
        require(ending.observedAt().toString().equals(StrictJson.text(row.get("last_frame_observed_at_utc"))), "tactical diagnostic original observation time changed");
        require(starting.identity().equals(parent.command().before()) && retained.execution().guard().observed().equals(parent.command().before())
                && retained.execution().guard().source().equals(parent.command().source()) && retained.execution().guard().sessionId().equals(parent.command().sessionId()), "tactical failure source/entry guard differs");
        require(plan.startingDateRaw() == starting.identity().frame().identity().dateRaw().intValueExact()
                && parent.command().claims().armyIds().containsAll(plan.watchArmyIds().stream().map(java.math.BigInteger::valueOf).toList()), "tactical failure plan/watch differs from original parent claims");
        List<ActionReceipt> children = loadChildren(row.get("actions"), parent, retained.execution(), archive);
        Optional<Status> arm = optionalStatus(row.get("armed")), stop = optionalStatus(row.get("stopped"));
        List<ExactRef> queryRefs = references(row.get("status_queries"));
        for (ExactRef queryRef : queryRefs) require(archive.referenceOf(archive.load(queryRef)).equals(queryRef), "retained original Status packet reference changed");
        if (arm.isPresent()) {
            List<ActionReceipt> arms = children.stream().filter(child -> child.command().operation().value().equals(plan.armStep())).toList();
            require(arms.size() == 1 && arms.getFirst().ack().isPresent()
                    && arm.orElseThrow().equals(AdvancePrimitives.acknowledgedSentinel(arms.getFirst().ack().orElseThrow(), plan.armStep())), "tactical armed Status is not its actual original ACK");
        }
        if (stop.isPresent()) {
            require(!queryRefs.isEmpty() && archive.load(queryRefs.getLast()) instanceof NativeActionPort.AckReceived, "observed stopped Status lacks an original independent query");
            require(stop.orElseThrow().equals(ClockStatusRead.decode((NativeActionPort.AckReceived)archive.load(queryRefs.getLast()))), "tactical stopped Status differs from last actual query");
        }
        String reason = StrictJson.text(row.get("reason"));
        Optional<String> cleanup = row.get("cleanup_error").isNull() ? Optional.empty() : Optional.of(StrictJson.text(row.get("cleanup_error")));
        var actual = new BattleAdvanceComposite.Failure(plan, starting, ending, children, queryRefs, arm, stop, reason, cleanup);
        require(compatible.equals(StrictJson.parse(BattleAdvanceResultCodec.failed(actual).bytes())), "existing tactical failure projection differs from the actual original frame/child/Status basis");
        int unreturned = retained.execution().children().size() - children.size();
        RawJson diagnostic = projectActual(parent.command(), actual, unreturned, basis);
        return new AutoFailureDiagnostic(AutoFailureDiagnostic.Kind.TACTICAL_CLOCK, parent.command().actionId(), parent.bodySha256(), bounded(reason), diagnostic, basis);
    }
    private Frame loadFrame(JsonNode value, ActionCommand parent, ActionPorts.OutcomeArchive archive) {
        var row = StrictJson.object(value, Set.of("native_frame", "driver_facts", "provenance", "semantic"));
        ExactRef nativeRef = ExactRef.fromJson(row.get("native_frame")), facts = ExactRef.fromJson(row.get("driver_facts")), semantic = ExactRef.fromJson(row.get("semantic"));
        exact(nativeRef, archive.loadNativeFrame(nativeRef)); exact(facts, archive.loadFullMaterial(facts).bytes());
        RawJson originalSemantic = archive.loadFullMaterial(semantic); exact(semantic, originalSemantic.bytes());
        var actual = frames.load(new NativeEffectEvidence.FrameBasis(nativeRef, facts), archive);
        var push = new ObservationProvenance.Push(actual.identity().frame().snapshotId(), actual.identity().frame().identity().nativeRevision(), actual.originalEvidence());
        require(push.equals(ObservationProvenanceCodec.decode(row.get("provenance"))) && actual.semantic().equals(org.xar.ck3.control.application.driver.DriverJson.object(originalSemantic.bytes(), RawJson.MAXIMUM_BYTES))
                && actual.source().equals(parent.source()) && actual.sessionId().equals(parent.sessionId()) && actual.identity().game().equals(parent.before().game())
                && actual.identity().frame().episodeRunId().equals(parent.before().frame().episodeRunId()), "tactical original native/Driver frame provenance changed");
        return new Frame(actual.identity(), actual.source(), actual.sessionId(), actual.semantic(), push, actual.observedAt(), actual.originalEvidence());
    }
    private static List<ActionReceipt> loadChildren(JsonNode rows, ActionReceipt parent, CompositeExecution execution, ActionPorts.OutcomeArchive archive) {
        List<ExactRef> refs = references(rows); require(refs.size() <= execution.children().size(), "tactical diagnostic invented original children");
        var children = new ArrayList<ActionReceipt>(); var ids = new java.util.HashSet<String>(); int cursor = 0;
        for (ExactRef ref : refs) {
            ActionReceipt actual = archive.loadReceipt(ref); var command = actual.command();
            require(actual.bodySha256().equals(ActionCodec.bodySha256(command)) && archive.receiptReferenceOf(actual).equals(ref) && ids.add(command.actionId())
                    && command.source().equals(parent.command().source()) && command.sessionId().equals(parent.command().sessionId())
                    && command.before().game().equals(parent.command().before().game()) && command.claims().equals(parent.command().claims())
                    && command.before().machineId().equals(parent.command().before().machineId())
                    && command.before().frame().episodeRunId().equals(parent.command().before().frame().episodeRunId())
                    && !command.deadline().isAfter(parent.command().deadline()) && AdvancePrimitives.supports(command.operation()), "tactical diagnostic child source/body changed");
            while (cursor < execution.children().size() && !execution.children().get(cursor).actionId().equals(command.actionId())) cursor++;
            require(cursor < execution.children().size() && execution.children().get(cursor).bodySha256().equals(actual.bodySha256()), "tactical original child absent, reordered or body-drifted");
            cursor++; children.add(actual);
        }
        return List.copyOf(children);
    }
    private static Optional<Status> optionalStatus(JsonNode value) { require(value != null, "missing tactical Status differs from explicit unobserved null"); return value.isNull() ? Optional.empty() : Optional.of(SentinelObservation.decode(value)); }
    private static List<ExactRef> references(JsonNode value) { require(value != null && value.isArray() && value.size() <= 256, "bounded explicit original references required"); var result = new ArrayList<ExactRef>(); for (JsonNode ref : value) result.add(ExactRef.fromJson(ref)); return List.copyOf(result); }

    /** Public fields come only from the typed actual failure; this projection grants no settlement or retry credit. */
    static RawJson projectActual(ActionCommand parent, BattleAdvanceComposite.Failure actual, int unreturnedChildren, ExactRef actualBasis) {
        require(actual.plan().scope() == BattleAdvanceStep.Scope.ROUTE_CONTACT_WINDOW && unreturnedChildren >= 0, "typed original route-window failure required");
        var original = StrictJson.parse(BattleAdvanceResultCodec.failed(actual).bytes());
        var result = StrictJson.object();
        for (String name : List.of("step", "source", "sentinel_scope", "progress_status", "backend_id", "starting_date_raw", "target_date_raw", "ending_date_raw", "elapsed_days", "requested_horizon_days", "timeline_speed", "timeline_policy", "sentinel_mode", "sentinel_generation", "completed_daily_ticks", "intermediate_pause_count", "overshoot_days", "paused", "snapshot_id", "revision", "native_revision", "bridge_pid", "connection_generation", "episode_character_id", "episode_run_id", "played_character_id", "played_character_alive", "external_pause_count", "managed_failure_cleanup", "player_decision_boundary_cancel")) {
            JsonNode value = original.get(name); result.set(name, value == null ? com.fasterxml.jackson.databind.node.NullNode.getInstance() : value.deepCopy());
        }
        for (String name : List.of("sentinel_generation", "revision", "native_revision", "connection_generation")) if (!result.path(name).isNull()) result.put(name, result.get(name).asText());
        long dateDelta = (long) actual.lastObserved().identity().frame().identity().dateRaw().intValueExact() - actual.plan().startingDateRaw();
        if (dateDelta < 0 || dateDelta % 24 != 0) result.putNull("elapsed_days");
        result.putNull("player_decision_boundary_pause_count");
        result.set("armed_tactical_daily_sentinel", statusProjection(actual.arm())); result.set("tactical_daily_sentinel", statusProjection(actual.stop()));
        var watch = result.putArray("watch_army_ids"); boolean watchOmitted = actual.plan().watchArmyIds().size() > MAX_WATCH;
        if (watchOmitted) result.putNull("watch_army_ids"); else actual.plan().watchArmyIds().forEach(watch::add);
        var actions = result.putArray("actions");
        for (ActionReceipt child : actual.actions().stream().limit(MAX_ACTIONS).toList()) {
            var row = actions.addObject(); row.put("step", child.command().operation().value()); row.putNull("purpose"); row.putNull("error");
            var ack = child.ack(); row.put("result_observed", ack.isPresent() && ack.orElseThrow().originalResultToken().isPresent()); var projected = row.putObject("result");
            if (ack.isPresent() && ack.orElseThrow().originalResultToken().isPresent()) {
                var token = StrictJson.parse(ack.orElseThrow().originalResultToken().orElseThrow().bytes());
                for (String name : List.of("step", "status")) { var value = token.get(name); projected.set(name, value != null && value.isTextual() && value.textValue().length() <= MAX_TEXT ? value.deepCopy() : com.fasterxml.jackson.databind.node.NullNode.getInstance()); }
                var accepted = token.get("accepted"); projected.set("accepted", accepted != null && accepted.isBoolean() ? accepted.deepCopy() : com.fasterxml.jackson.databind.node.NullNode.getInstance());
                projected.put("request_id", bounded(ack.orElseThrow().requestId())); projected.set("native_request_id", identityScalar(token.get("native_request_id")));
            } else for (String name : List.of("step", "accepted", "status", "request_id", "native_request_id")) projected.putNull(name);
        }
        int omitted = Math.max(0, actual.actions().size() - MAX_ACTIONS) + unreturnedChildren; result.put("actions_omitted_count", omitted);
        var body = StrictJson.object(); body.put("schema", PUBLIC_SCHEMA); body.put("is_error", true); body.put("never_replay", true); body.put("credit", 0);
        body.put("selected_step", parent.operation().value()); body.put("primitive_step", actual.plan().step()); body.set("step_result", result);
        body.putNull("wait_progress"); body.put("truncated", watchOmitted || omitted > 0); body.put("identity_scalar_profile", "canonical_decimal_identity_v1");
        body.put("machine_id", parent.before().machineId()); body.put("last_frame_observed_at_utc", actual.lastObserved().observedAt().toString()); body.set("original_failure_basis", actualBasis.toJson());
        RawJson raw = new RawJson(StrictJson.canonical(body)); require(raw.bytes().length <= AutoFailureDiagnostic.Kind.TACTICAL_CLOCK.maximumBytes(), "bounded tactical diagnostic exceeded its actual public contract"); return raw;
    }
    private static JsonNode statusProjection(Optional<Status> status) { if (status.isEmpty()) return com.fasterxml.jackson.databind.node.NullNode.getInstance(); var row = SentinelObservation.toJson(status.orElseThrow()); row.put("generation", status.orElseThrow().generation().decimal()); return row; }
    private static JsonNode identityScalar(JsonNode value) {
        if (value != null && (value.isTextual() || value.isIntegralNumber())) { String exact = value.isTextual() ? value.textValue() : value.bigIntegerValue().toString(); if (exact.length() <= MAX_TEXT) return new com.fasterxml.jackson.databind.node.TextNode(exact); }
        return com.fasterxml.jackson.databind.node.NullNode.getInstance();
    }
    private static String bounded(String value) { return value.length() <= MAX_TEXT ? value : value.substring(0, MAX_TEXT); }
    private static void exact(ExactRef ref, byte[] body) { require(ref.bytes() == body.length && ref.sha256().equals(ActionCodec.sha256(body)), "tactical original bytes/SHA changed"); }
}
