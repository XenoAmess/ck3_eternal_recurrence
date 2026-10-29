package org.xar.ck3.control.application.battleadvance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.NullNode;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.LinkedHashMap;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ObservationProvenanceCodec;
import org.xar.ck3.control.application.advance.AdvanceObservationPort.Frame;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;

/** Complete original tactical result material plus exact durable-child/source references. No ACK grants completion. */
public final class BattleAdvanceResultCodec {
    public static final String SCHEMA = "xar.ck3.java-battle-sentinel-result/v1";
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS).enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private BattleAdvanceResultCodec() { }
    public enum Profile { JAVA_V1, LEGACY_NATIVE_V1 }
    public record WarProgressIdentity(int dateRaw, List<Integer> warIds) {
        public WarProgressIdentity {
            warIds = List.copyOf(warIds);
            StrictJson.require(dateRaw >= 0 && warIds.stream().allMatch(id -> id > 0) && warIds.equals(warIds.stream().distinct().sorted().toList()), "complete normalized historical WarID identity required");
        }
    }
    /** Typed immutable read boundary for the historical envelope validator. It confers no writer/action qualification. */
    public record Decoded(Profile profile, RawJson original, OpportunityJson.Obj envelope, Optional<BattleAdvanceStep> step,
            Optional<BattleAdvancePlan> plan, Optional<Status> armed, Optional<Status> sentinel,
            Optional<WarProgressIdentity> warProgressBefore, Optional<WarProgressIdentity> warProgressAfter) {
        public Decoded {
            Objects.requireNonNull(profile); Objects.requireNonNull(original); Objects.requireNonNull(envelope);
            Objects.requireNonNull(step); Objects.requireNonNull(plan); Objects.requireNonNull(armed); Objects.requireNonNull(sentinel);
            Objects.requireNonNull(warProgressBefore); Objects.requireNonNull(warProgressAfter);
        }
    }
    /** Legacy numeric generation and Java decimal generation are explicit profiles, never alias fallbacks. */
    public static Decoded decode(RawJson original, Profile profile) {
        Objects.requireNonNull(profile); JsonNode node;
        try { node = JSON.readTree(original.bytes()); } catch (java.io.IOException error) { throw new IllegalArgumentException("invalid original battle result", error); }
        StrictJson.require(node.isObject(), "battle result object required");
        if (profile == Profile.JAVA_V1) StrictJson.require(node.path("schema").isTextual() && SCHEMA.equals(node.path("schema").textValue()), "Java battle result version differs");
        else StrictJson.require(!node.has("schema"), "legacy result profile cannot consume a versioned Java result");
        StrictJson.require(node.path("step").isTextual(), "battle result exact step required"); String step = node.path("step").textValue();
        Optional<Status> arm = status(node, "armed_tactical_daily_sentinel"), sentinel = status(node, "tactical_daily_sentinel");
        JsonNode generation = node.get("sentinel_generation"); StrictJson.require(generation != null, "missing sentinel generation differs from null");
        if (!generation.isNull()) {
            if (profile == Profile.JAVA_V1) new org.xar.ck3.control.contracts.CrossJsDecimalUInt64(StrictJson.text(generation));
            else StrictJson.integer(generation, java.math.BigInteger.ZERO, StrictJson.UINT64_MAX);
        }
        // The actual complete original token remains untouched. Only the validator's fixed finite envelope is projected.
        var selected = StrictJson.object();
        for (String key : List.of("schema", "step", "source", "starting_date_raw", "target_date_raw", "ending_date_raw", "elapsed_days", "requested_horizon_days",
                "timeline_speed", "timeline_policy", "sentinel_mode", "sentinel_scope", "watch_army_ids", "progress_status", "stop_kind", "terminal_reached",
                "one_life_terminal", "one_life_terminal_reason", "trigger_reasons", "sentinel_generation", "completed_daily_ticks", "intermediate_pause_count", "overshoot_days",
                "zero_intermediate_pause", "player_decision_boundary", "player_decision_boundary_cancel", "war_objective_hold_request", "war_objective_hold_admission", "war_objective_hold_post_stop",
                "exact_war_terminal_watch", "exact_active_war_set_watch", "maximum_omitted_state_detection_lag_days", "external_pause_count", "player_decision_boundary_pause_count",
                "external_rich_query_count", "managed_failure_cleanup", "paused", "active_event", "pending_character_interaction", "snapshot_id", "revision", "native_revision",
                "bridge_pid", "connection_generation", "episode_character_id", "episode_run_id", "played_character_id", "played_character_alive"))
            if (node.has(key)) selected.set(key, node.get(key));
        OpportunityJson.Obj envelope = OpportunityJson.object(OpportunityJson.parse(selected.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8)), "battle envelope");
        Optional<BattleAdvancePlan> plan = Optional.empty();
        if (profile == Profile.JAVA_V1) {
            StrictJson.require(node.get(BattleAdvancePlan.KEY) != null && node.get(BattleAdvancePlan.KEY).isObject(), "Java result lacks durable tactical plan");
            plan = Optional.of(BattleAdvancePlan.decode(OpportunityJson.object(OpportunityJson.parse(node.get(BattleAdvancePlan.KEY).toString().getBytes(java.nio.charset.StandardCharsets.UTF_8)), "battle plan"), step));
        }
        return new Decoded(profile, original, envelope, BattleAdvanceStep.parse(step), plan, arm, sentinel, warProgress(node, "war_progress_before"), warProgress(node, "war_progress_after"));
    }
    private static Optional<WarProgressIdentity> warProgress(JsonNode original, String key) {
        JsonNode value = original.get(key); if (value == null || value.isNull()) return Optional.empty();
        StrictJson.require(value.isObject() && value.path("wars").isArray(), "historical compact war progress identity required");
        int date = (int) StrictJson.integer(value.get("date_raw"), 0, Integer.MAX_VALUE); List<Integer> wars = new java.util.ArrayList<>();
        for (JsonNode war : value.get("wars")) wars.add((int) StrictJson.integer(war.get("war_id"), 1, Integer.MAX_VALUE));
        wars.sort(Integer::compareTo); return Optional.of(new WarProgressIdentity(date, wars));
    }
    private static Optional<Status> status(JsonNode node, String key) {
        JsonNode value = node.get(key); StrictJson.require(value != null, "missing sentinel slot differs from null: " + key);
        return value.isNull() ? Optional.empty() : Optional.of(SentinelObservation.decode(value));
    }
    public static Optional<BattleAdvanceFrame.Boundary> decodeBoundary(Decoded decoded) {
        var value = decoded.envelope().get("player_decision_boundary");
        if (value == null || value == OpportunityJson.Nil.INSTANCE) return Optional.empty();
        var row = OpportunityJson.object(value, "player_decision_boundary");
        var kind = BattleAdvanceFrame.Kind.valueOf(OpportunityJson.text(row.get("kind"), "kind").toUpperCase(Locale.ROOT));
        java.math.BigInteger connection;
        if (decoded.profile() == Profile.JAVA_V1) connection = new java.math.BigInteger(new org.xar.ck3.control.contracts.CrossJsDecimalUInt64(OpportunityJson.text(row.get("connection_generation"), "connection_generation")).decimal());
        else connection = OpportunityJson.integer(row.get("connection_generation"), "connection_generation");
        StrictJson.require(connection.signum() > 0 && connection.compareTo(StrictJson.UINT64_MAX) <= 0, "boundary connection generation required");
        var owner = new BattleAdvanceFrame.Owner(OpportunityJson.integer(row.get("observed_date_raw"), "observed_date_raw").intValueExact(),
                positive(row, "bridge_pid"), connection, positive(row, "episode_character_id"), OpportunityJson.text(row.get("episode_run_id"), "episode_run_id"), positive(row, "played_character_id"));
        var instance = row.get("instance_id");
        StrictJson.require(instance == null || instance == OpportunityJson.Nil.INSTANCE || instance instanceof OpportunityJson.Text || instance instanceof OpportunityJson.IntegerValue, "native boundary instance identity type differs");
        var reason = row.get("terminal_reason"); var alive = row.get("played_character_alive");
        List<Integer> before = kind == BattleAdvanceFrame.Kind.ACTIVE_WAR_SET_CHANGED ? ids(row, "before_war_ids") : List.of();
        List<Integer> after = kind == BattleAdvanceFrame.Kind.ACTIVE_WAR_SET_CHANGED ? ids(row, "after_war_ids") : List.of();
        var result = new BattleAdvanceFrame.Boundary(kind, instance == null || instance == OpportunityJson.Nil.INSTANCE ? Optional.empty() : Optional.of(instance),
                reason == null || reason == OpportunityJson.Nil.INSTANCE ? Optional.empty() : Optional.of(OpportunityJson.text(reason, "terminal_reason")),
                alive == null || alive == OpportunityJson.Nil.INSTANCE ? Optional.empty() : Optional.of(OpportunityJson.bool(alive, "played_character_alive")), owner, before, after);
        StrictJson.require(result.validIdentity() && owner.dateRaw() >= 0, "boundary actual identity invalid");
        if (kind == BattleAdvanceFrame.Kind.ACTIVE_WAR_SET_CHANGED) {
            StrictJson.require(ids(row, "added_war_ids").equals(after.stream().filter(id -> !before.contains(id)).toList())
                    && ids(row, "removed_war_ids").equals(before.stream().filter(id -> !after.contains(id)).toList()), "active-war-set boundary delta disagrees with full IDs");
        }
        return Optional.of(result);
    }
    private static java.math.BigInteger positive(OpportunityJson.Obj row, String key) { var result = OpportunityJson.integer(row.get(key), key); StrictJson.require(result.signum() > 0, "positive actual boundary owner required: " + key); return result; }
    private static List<Integer> ids(OpportunityJson.Obj row, String key) {
        List<Integer> result = OpportunityJson.array(row.get(key), key).stream().map(item -> OpportunityJson.integer(item, key).intValueExact()).toList();
        StrictJson.require(result.stream().allMatch(id -> id > 0) && result.equals(result.stream().distinct().sorted().toList()), "normalized full WarID list required: " + key); return result;
    }
    public static RawJson completed(BattleAdvanceComposite.Outcome result) {
        ObjectNode node = base(result.plan(), result.starting(), result.ending(), Optional.of(result.arm()), Optional.of(result.stop()), result.actions(), result.queryEvidence(), "postcondition");
        node.put("stop_kind", result.decisionBoundary().isPresent() ? "player_decision" : result.stop().terminalObserved() ? "terminal" : "decision_epoch");
        node.set("player_decision_boundary", result.decisionBoundary().<JsonNode>map(value -> boundary(value, result.ending())).orElse(NullNode.getInstance()));
        if (result.canceled()) {
            ObjectNode cancel = node.putObject("player_decision_boundary_cancel"); cancel.put("step", BattleAdvancePlan.CANCEL_PREFIX + result.arm().generation().decimal());
            cancel.put("status", "canceled"); cancel.put("generation", result.arm().generation().decimal());
        } else node.putNull("player_decision_boundary_cancel");
        if (result.plan().scope() == BattleAdvanceStep.Scope.STATIONARY_OBJECTIVE_HOLD) {
            var request = (BattleAdvanceStep.Hold) BattleAdvanceStep.parse(result.plan().step()).orElseThrow();
            node.set("war_objective_hold_admission", hold(result.starting(), result.plan(), request, result.holdAdmission().orElseThrow()));
            node.set("war_objective_hold_post_stop", hold(result.ending(), result.plan(), request, result.holdPostStop().orElseThrow()));
        }
        node.put("player_decision_boundary_pause_count", result.decisionBoundary().isPresent() ? result.actions().stream().filter(row -> row.command().operation().value().equals("pause-map")).count() : 0);
        node.putObject("managed_failure_cleanup").put("attempted", false).putNull("error");
        return raw(node);
    }
    /** Runtime producer: the result projection alone cannot substitute for archived child/read bodies. */
    public static RawJson completed(ActionCommand parent, BattleAdvanceComposite.Outcome result, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(parent); Objects.requireNonNull(archive);
        return archived(parent, result, archive, true);
    }
    private static RawJson archived(ActionCommand parent, BattleAdvanceComposite.Outcome result, ActionPorts.OutcomeArchive archive, boolean preserve) {
        ObjectNode node = (ObjectNode) org.xar.ck3.control.application.driver.DriverJson.toNode(org.xar.ck3.control.application.driver.DriverJson.object(completed(result).bytes(), RawJson.MAXIMUM_BYTES));
        node.put("archived_basis_schema", "xar.ck3.battle-archived-basis/v2");
        node.set("starting_driver_facts", driverFacts(result.starting()).toJson());
        node.set("ending_driver_facts", driverFacts(result.ending()).toJson());
        node.set("starting_provenance", ObservationProvenanceCodec.encode(result.starting().provenance()));
        node.set("ending_provenance", ObservationProvenanceCodec.encode(result.ending().provenance()));
        node.put("parent_action_id", parent.actionId()); node.put("parent_body_sha256", ActionCodec.bodySha256(parent));
        node.set("terminal_status_read", ref(preserve ? archive.preserveRead(result.nativeStopRead().receipt()) : archive.readReferenceOf(result.nativeStopRead().receipt())));
        var actions = node.withArray("actions");
        for (int index = 0; index < result.actions().size(); index++)
            ((ObjectNode) actions.get(index)).set("receipt_evidence", ref(preserve ? archive.preserveReceipt(result.actions().get(index)) : archive.receiptReferenceOf(result.actions().get(index))));
        return raw(node);
    }
    /** Cold Route-window report verification. All execution facts come from the owning archived replay;
     * this method rebuilds the original producer representation without preserving or writing anything. */
    public static void verifyWindowReport(BattleAdvanceArchivedReplay actualReplay, ActionCommand parent,
            BattleAdvancePlan plan, Frame starting, Frame ending,
            org.xar.ck3.control.application.advance.ClockStatusRead.Observation terminal,
            List<ActionReceipt> children, RawJson original, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(actualReplay); Objects.requireNonNull(archive);
        StrictJson.require(plan.scope() == BattleAdvanceStep.Scope.ROUTE_CONTACT_WINDOW, "only actual Route-window report verification is supported");
        actualReplay.verify(parent, plan, starting, ending, terminal, children, archive);
        var decoded = decode(original, Profile.JAVA_V1);
        StrictJson.require(decoded.plan().equals(Optional.of(plan)), "original window report differs from actual clock plan");
        JsonNode node = org.xar.ck3.control.application.driver.DriverJson.toNode(
                org.xar.ck3.control.application.driver.DriverJson.object(original.bytes(), RawJson.MAXIMUM_BYTES));
        JsonNode queryRows = node.get("status_query_evidence");
        StrictJson.require(queryRows != null && queryRows.isArray() && queryRows.size() >= 1 && queryRows.size() <= 65536,
                "original bounded complete clock-query reference list required");
        var queries = new java.util.ArrayList<ExactRef>();
        for (JsonNode row : queryRows) {
            ExactRef reference = ExactRef.fromJson(row);
            StrictJson.require(archive.referenceOf(archive.load(reference)).equals(reference), "original clock-query custody changed");
            queries.add(reference);
        }
        StrictJson.require(queries.contains(terminal.originalEvidence()), "actual final independent query absent from original clock report");
        List<ActionReceipt> armChildren = children.stream().filter(row -> row.command().operation().value().equals(plan.armStep())).toList();
        StrictJson.require(armChildren.size() == 1, "one actual original window arm required");
        var arm = org.xar.ck3.control.application.advance.AdvancePrimitives.acknowledgedSentinel(armChildren.getFirst().ack().orElseThrow(), plan.armStep());
        var boundary = BattleAdvanceFrame.boundary(BattleAdvanceFrame.decode(starting), BattleAdvanceFrame.decode(ending));
        boolean canceled = terminal.status().state() == org.xar.ck3.control.reconciliation.LateOutcome.State.IDLE;
        var actual = new BattleAdvanceComposite.Outcome(plan, starting, ending, arm, terminal.status(), boundary, canceled,
                children, queries, Optional.empty(), Optional.empty(), terminal);
        RawJson expected = archived(parent, actual, archive, false);
        StrictJson.require(org.xar.ck3.control.application.driver.DriverJson.object(expected.bytes(), RawJson.MAXIMUM_BYTES)
                .equals(org.xar.ck3.control.application.driver.DriverJson.object(original.bytes(), RawJson.MAXIMUM_BYTES)),
                "original complete window report differs from source-owned producer and archived execution facts");
    }
    private static ExactRef driverFacts(Frame frame) {
        var value = frame.semantic().get("java_driver_facts_evidence");
        StrictJson.require(value instanceof OpportunityJson.Obj, "tactical runtime frame requires the complete original Driver manifest");
        return ExactRef.fromJson(OpportunityJson.toNode(value));
    }
    public static RawJson failed(BattleAdvanceComposite.Failure result) {
        ObjectNode node = base(result.plan(), result.starting(), result.lastObserved(), result.arm(), result.stop(), result.actions(), result.queryEvidence(), "postcondition_failed");
        node.put("failure_reason", result.reason()); node.put("business_success_inferred", false);
        if (result.plan().scope() == BattleAdvanceStep.Scope.STATIONARY_OBJECTIVE_HOLD) {
            var request = (BattleAdvanceStep.Hold) BattleAdvanceStep.parse(result.plan().step()).orElseThrow();
            node.set("war_objective_hold_admission", hold(result.starting(), result.plan(), request, BattleAdvanceFrame.decode(result.starting()).hold(result.plan().watchArmyIds(), request)));
            node.putNull("war_objective_hold_post_stop");
        }
        ObjectNode cleanup = node.putObject("managed_failure_cleanup");
        cleanup.put("attempted", result.actions().stream().anyMatch(row -> row.command().operation().value().equals("pause-map")));
        if (result.cleanupError().isPresent()) cleanup.put("error", result.cleanupError().orElseThrow()); else cleanup.putNull("error");
        return raw(node);
    }
    public static RawJson readOnly(ActionCommand parent, BattleAdvanceComposite.ReadOnlyOutcome outcome) {
        ObjectNode node = StrictJson.object(); node.put("schema", "xar.ck3.java-battle-read-only-reconciliation/v1");
        node.put("machine_id", parent.before().machineId()); node.put("original_action_id", parent.actionId()); node.put("original_action_deadline", parent.deadline().toString());
        node.put("read_started_at", outcome.startedAt().toString()); node.put("read_deadline", outcome.deadline().toString());
        node.put("read_hard_deadline", outcome.budget().hardDeadline().toString()); node.put("maximum_duration_millis", outcome.budget().maximumDurationMillis());
        node.put("maximum_native_reads", outcome.budget().maximumReads()); node.put("read_operations", 3); node.putNull("actual_native_reads");
        node.put("submit_attempted", false); node.put("business_success_inferred", false);
        node.set("first_frame_evidence", ref(outcome.first().originalEvidence())); node.set("status_evidence", ref(outcome.statusEvidence())); node.set("ending_frame_evidence", ref(outcome.ending().originalEvidence()));
        node.set("tactical_daily_sentinel", SentinelObservation.toJson(outcome.status())); return raw(node);
    }
    private static ObjectNode base(BattleAdvancePlan plan, Frame start, Frame end, Optional<Status> arm, Optional<Status> stop,
            List<ActionReceipt> actions, List<ExactRef> queries, String progress) {
        ObjectNode node = StrictJson.object(); node.put("schema", SCHEMA); node.put("step", plan.step()); node.put("backend_id", "native-headless");
        node.put("source", "native-tactical-daily-sentinel-composite"); node.set("battle_advance_v1", OpportunityJson.toNode(plan.json()));
        int endingDate = end.identity().frame().identity().dateRaw().intValueExact(); int delta = endingDate - plan.startingDateRaw();
        node.put("starting_date_raw", plan.startingDateRaw()); node.put("target_date_raw", plan.targetDateRaw()); node.put("ending_date_raw", endingDate);
        node.putObject("starting_date").put("date_raw", plan.startingDateRaw()); node.putObject("ending_date").put("date_raw", endingDate);
        node.put("elapsed_days", delta >= 0 && delta % 24 == 0 ? delta / 24 : 0); node.put("requested_horizon_days", (plan.targetDateRaw() - plan.startingDateRaw()) / 24);
        node.put("timeline_speed", plan.speed()); String mode = plan.mode().name().toLowerCase(Locale.ROOT); node.put("timeline_policy", mode); node.put("sentinel_mode", mode);
        node.put("sentinel_scope", plan.scope().name().toLowerCase(Locale.ROOT)); var watch = node.putArray("watch_army_ids"); plan.watchArmyIds().forEach(watch::add);
        node.put("progress_status", progress); node.put("terminal_reached", stop.map(Status::terminalObserved).orElse(false));
        node.putNull("player_decision_boundary"); node.putNull("player_decision_boundary_cancel");
        // uint64 generation is decimal in Java result memory/JSON. The raw native status profile remains explicit below.
        if (stop.isPresent() || arm.isPresent()) node.put("sentinel_generation", stop.orElseGet(arm::orElseThrow).generation().decimal()); else node.putNull("sentinel_generation");
        node.put("native_status_wire_profile", SentinelObservation.NUMERIC_WIRE_PROFILE); node.put("status_memory_profile", SentinelObservation.MEMORY_PROFILE);
        node.set("armed_tactical_daily_sentinel", arm.<JsonNode>map(SentinelObservation::toJson).orElse(NullNode.getInstance()));
        node.set("tactical_daily_sentinel", stop.<JsonNode>map(SentinelObservation::toJson).orElse(NullNode.getInstance()));
        if (stop.isPresent()) {
            Status status = stop.orElseThrow(); node.put("completed_daily_ticks", status.completedDailyTicks()); node.put("intermediate_pause_count", status.intermediatePauseCount());
            node.put("overshoot_days", status.overshootDays()); node.put("zero_intermediate_pause", status.intermediatePauseCount() == 0);
            var reasons = node.putArray("trigger_reasons"); status.triggerReasons().forEach(reasons::add);
        } else { node.putNull("completed_daily_ticks"); node.putNull("intermediate_pause_count"); node.putNull("overshoot_days"); node.put("zero_intermediate_pause", false); node.putArray("trigger_reasons"); }
        node.set("war_progress_before", OpportunityJson.toNode(BattleWarProgress.summary(start.semantic()))); node.set("war_progress_after", OpportunityJson.toNode(BattleWarProgress.summary(end.semantic())));
        node.set("starting_frame_evidence", ref(start.originalEvidence())); node.set("ending_frame_evidence", ref(end.originalEvidence()));
        var queryRows = node.putArray("status_query_evidence"); queries.forEach(value -> queryRows.add(ref(value)));
        var childRows = node.putArray("actions");
        for (ActionReceipt action : actions) {
            ObjectNode child = childRows.addObject(); child.put("step", action.command().operation().value()); child.put("action_id", action.command().actionId());
            child.put("body_sha256", action.bodySha256()); child.put("ledger_sequence", action.sequence()); child.put("outcome", action.outcome().name());
            action.ack().ifPresent(ack -> ack.originalResultToken().ifPresent(value -> child.set("result", StrictJson.parse(value.bytes()))));
        }
        node.put("external_pause_count", actions.stream().filter(row -> row.command().operation().value().equals("pause-map")).count()); node.put("external_rich_query_count", 0);
        node.put("paused", OpportunityJson.bool(end.semantic().get("paused"), "paused"));
        for (String key : List.of("active_event", "pending_character_interaction", "one_life_terminal_reason")) node.set(key, OpportunityJson.toNode(end.semantic().get(key)));
        boolean terminal = end.semantic().get("one_life_terminal_reason") instanceof OpportunityJson.Text; node.put("one_life_terminal", terminal);
        if (OpportunityJson.bool(end.semantic().get("paused"), "paused") && end.semantic().get("active_event") == OpportunityJson.Nil.INSTANCE
                && end.semantic().get("pending_character_interaction") == OpportunityJson.Nil.INSTANCE && !terminal) node.put("final_screen", "map_hud"); else node.putNull("final_screen");
        node.put("snapshot_id", end.identity().frame().snapshotId()); node.put("revision", end.identity().frame().revision()); node.put("native_revision", end.identity().frame().identity().nativeRevision());
        node.put("machine_id", end.identity().machineId()); node.put("session_id", end.sessionId()); node.put("episode_run_id", end.identity().frame().episodeRunId());
        node.put("played_character_id", end.identity().frame().identity().player());
        var owner = BattleAdvanceFrame.decode(end).owner(); node.put("bridge_pid", owner.bridgePid()); node.put("connection_generation", owner.connectionGeneration().toString());
        node.put("episode_character_id", owner.episodeCharacterId());
        var alive = OpportunityJson.object(end.semantic().get("played_character"), "played_character").get("alive");
        node.set("played_character_alive", OpportunityJson.toNode(alive == null ? OpportunityJson.Nil.INSTANCE : alive));
        if (plan.scope() == BattleAdvanceStep.Scope.STATIONARY_OBJECTIVE_HOLD) {
            var request = (BattleAdvanceStep.Hold) BattleAdvanceStep.parse(plan.step()).orElseThrow();
            node.putObject("war_objective_hold_request").put("sentinel_scope", "stationary_objective_hold").put("war_id", request.warId())
                    .put("subject_army_id", request.armyId()).put("objective_province_id", request.objectiveProvinceId()).put("target_date_raw", plan.targetDateRaw());
            node.put("exact_war_terminal_watch", false); node.put("exact_active_war_set_watch", false); node.put("maximum_omitted_state_detection_lag_days", 7);
        }
        return node;
    }
    private static ObjectNode boundary(BattleAdvanceFrame.Boundary value, Frame actualEnding) {
        ObjectNode node = StrictJson.object(); node.put("kind", value.kind().name().toLowerCase(Locale.ROOT));
        node.set("instance_id", value.instanceId().<JsonNode>map(OpportunityJson::toNode).orElse(NullNode.getInstance()));
        value.terminalReason().ifPresent(reason -> node.put("terminal_reason", reason)); value.playedCharacterAlive().ifPresent(alive -> node.put("played_character_alive", alive));
        var owner = value.owner(); node.put("observed_date_raw", owner.dateRaw()); node.put("bridge_pid", owner.bridgePid()); node.put("connection_generation", owner.connectionGeneration().toString());
        node.put("episode_character_id", owner.episodeCharacterId()); node.put("episode_run_id", owner.episodeRunId()); node.put("played_character_id", owner.playedCharacterId());
        node.put("snapshot_id", actualEnding.identity().frame().snapshotId()); node.put("revision", actualEnding.identity().frame().revision()); node.put("native_revision", actualEnding.identity().frame().identity().nativeRevision());
        if (value.kind() == BattleAdvanceFrame.Kind.ACTIVE_WAR_SET_CHANGED) {
            var before = node.putArray("before_war_ids"); value.beforeWarIds().forEach(before::add); var after = node.putArray("after_war_ids"); value.afterWarIds().forEach(after::add);
            var added = node.putArray("added_war_ids"); value.afterWarIds().stream().filter(id -> !value.beforeWarIds().contains(id)).forEach(added::add);
            var removed = node.putArray("removed_war_ids"); value.beforeWarIds().stream().filter(id -> !value.afterWarIds().contains(id)).forEach(removed::add);
        }
        return node;
    }
    private static ObjectNode hold(Frame frame, BattleAdvancePlan plan, BattleAdvanceStep.Hold request, BattleAdvanceFrame.HoldState state) {
        var snapshot = BattleAdvanceFrame.decode(frame); ObjectNode node = StrictJson.object(); node.put("status", state.status().name().toLowerCase(Locale.ROOT));
        if (state.status() == BattleAdvanceFrame.HoldStatus.MATCHED) node.putNull("reason"); else node.put("reason", state.reason());
        node.put("sentinel_scope", "stationary_objective_hold"); node.put("war_id", request.warId()); node.put("subject_army_id", request.armyId()); node.put("objective_province_id", request.objectiveProvinceId());
        var watch = node.putArray("watch_army_ids"); plan.watchArmyIds().forEach(watch::add); node.put("paused_map_ready", snapshot.paused() && snapshot.mapReady()); node.put("player_decision_clear", snapshot.decision().isEmpty());
        node.put("complete_controllable_watch", snapshot.controllableIds().equals(plan.watchArmyIds())); node.put("all_player_armies_regular_idle_stationary", !snapshot.armies().isEmpty() && snapshot.armies().stream().allMatch(BattleAdvanceFrame.Army::stationary));
        node.put("player_active_siege", snapshot.wars().stream().anyMatch(BattleAdvanceFrame.War::playerSiege)); node.put("player_active_assault", snapshot.wars().stream().anyMatch(BattleAdvanceFrame.War::playerAssault));
        var war = snapshot.wars().stream().filter(row -> row.id() == request.warId()).findFirst(); node.put("war_active", war.isPresent()); node.put("objective_in_war", war.flatMap(BattleAdvanceFrame.War::objectiveProvinceIds).filter(ids -> ids.contains(request.objectiveProvinceId())).isPresent());
        var subject = snapshot.armies().stream().filter(row -> row.id().equals(Optional.of(request.armyId()))).findFirst();
        node.put("subject_controllable", subject.filter(BattleAdvanceFrame.Army::controllable).isPresent() && plan.watchArmyIds().contains(request.armyId()));
        var province = subject.flatMap(BattleAdvanceFrame.Army::currentProvince); if (province.isPresent()) node.put("subject_current_province_id", province.orElseThrow()); else node.putNull("subject_current_province_id");
        node.put("subject_at_objective", province.equals(Optional.of(request.objectiveProvinceId()))); node.put("exact_war_terminal_watch", false); node.put("exact_active_war_set_watch", false); return node;
    }
    private static ObjectNode ref(ExactRef ref) { ObjectNode node = StrictJson.object(); node.put("path", ref.path()); node.put("bytes", ref.bytes()); node.put("sha256", ref.sha256()); return node; }
    private static RawJson raw(ObjectNode node) { return new RawJson(node.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8)); }
}
