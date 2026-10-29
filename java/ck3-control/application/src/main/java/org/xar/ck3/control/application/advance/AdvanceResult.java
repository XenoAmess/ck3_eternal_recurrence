package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.routecontact.RouteContactSteps;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;

/** Single original-compatible result producer, persisted by the existing immutable OutcomeArchive. */
public record AdvanceResult(ActionCommand command, AdvancePlan plan, AdvanceObservationPort.Frame starting,
        AdvanceClock.Outcome outcome, List<ActionReceipt> children) {
    public static final String SCHEMA = "xar.ck3.java-life-advance-result/v1";
    public AdvanceResult {
        Objects.requireNonNull(command); Objects.requireNonNull(plan); Objects.requireNonNull(starting); Objects.requireNonNull(outcome);
        children = List.copyOf(children); require(children.size() <= 1024 && children.stream().allMatch(ActionReceipt::settled), "only complete actual durable child receipts can become an advance result");
        if (plan.policy().equals("exact_one_day_battle_identity_materialization")) validateMaterialization(starting, outcome.endingFrame());
    }
    public RawJson encode(ActionPorts.OutcomeArchive archive) {
        Value read = outcome.diagnostics().nativeStopRead().<Value>map(observed ->
                OpportunityJson.parse(StrictJson.canonical(archive.preserveRead(observed.receipt()).toJson()))).orElse(Nil.INSTANCE);
        return new RawJson(DriverJson.encode(json().with("native_stop_read_ref", read)));
    }
    public Obj json() {
        var now = outcome.endingFrame(); var info = outcome.diagnostics(); var fields = new LinkedHashMap<String, Value>();
        fields.put("schema", new Text(SCHEMA)); fields.put("step", new Text(command.operation().value()));
        fields.put("action_id", new Text(command.actionId())); fields.put("action_body_sha256", new Text(ActionCodec.bodySha256(command)));
        fields.put("machine_id", new Text(command.before().machineId())); fields.put("session_id", new Text(command.sessionId()));
        fields.put("episode_run_id", new Text(command.before().frame().episodeRunId()));
        fields.put("starting_snapshot_id", new Text(starting.identity().frame().snapshotId()));
        fields.put("starting_revision", new IntegerValue(starting.identity().frame().revision()));
        fields.put("starting_native_revision", new IntegerValue(starting.identity().frame().identity().nativeRevision()));
        fields.put("backend_id", new Text("native-headless")); fields.put("source", new Text("native-composite"));
        fields.put("starting_date", new Obj(Map.of("date_raw", new IntegerValue(info.startingDateRaw()))));
        fields.put("ending_date", new Obj(Map.of("date_raw", new IntegerValue(info.endingDateRaw()))));
        fields.put("starting_date_raw", new IntegerValue(info.startingDateRaw())); fields.put("ending_date_raw", new IntegerValue(info.endingDateRaw()));
        fields.put("elapsed_days", number(info.elapsedDays())); fields.put("requested_horizon_days", number(info.requestedHorizonDays()));
        fields.put("timeline_speed", number(info.timelineSpeed())); fields.put("timeline_policy", new Text(info.timelinePolicy()));
        fields.put("progress_status", new Text(progressStatus(info.progressStatus())));
        fields.put("war_progress_before", warSummary(starting.semantic())); fields.put("war_progress_after", warSummary(now.semantic()));
        fields.put("ordinary_events", new Arr(List.of()));
        fields.put("event_resolution", new Text(now.semantic().get("active_event") instanceof Obj ? "typed_query_required" : "none"));
        List<Value> actions = new ArrayList<>();
        for (ActionReceipt child : children) {
            Value token = child.ack().flatMap(NativeActionPort.AckReceived::originalResultToken)
                    .<Value>map(value -> DriverJson.object(value.bytes(), RawJson.MAXIMUM_BYTES)).orElse(Nil.INSTANCE);
            actions.add(new Obj(Map.of("step", new Text(child.command().operation().value()), "action_id", new Text(child.command().actionId()),
                    "body_sha256", new Text(child.bodySha256()), "outcome", new Text(child.outcome().name()), "result", token)));
        }
        fields.put("actions", new Arr(actions)); fields.put("paused", new Bool(AdvancePolicy.truth(now.semantic(), "paused")));
        fields.put("active_event", nullable(now.semantic(), "active_event")); fields.put("pending_character_interaction", nullable(now.semantic(), "pending_character_interaction"));
        fields.put("final_screen", AdvancePolicy.truth(now.semantic(), "paused") && now.semantic().get("active_event") == Nil.INSTANCE
                && now.semantic().get("pending_character_interaction") == Nil.INSTANCE ? new Text("map_hud") : Nil.INSTANCE);
        fields.put("snapshot_id", new Text(now.identity().frame().snapshotId())); fields.put("revision", new IntegerValue(now.identity().frame().revision()));
        fields.put("native_revision", new IntegerValue(now.identity().frame().identity().nativeRevision()));
        fields.put("full_wall_nanos", new Text(Long.toString(info.fullWallNanos())));
        fields.put("calendar_progress_verified", new Bool(info.elapsedDays() > 0));
        fields.put("saved_day_credit", number(0));
        if (info.progressStatus() == AdvanceClock.ProgressStatus.MODAL_INTERRUPTED)
            fields.put("top_exclusive_modal_choice_hint", nullable(now.semantic(), "top_exclusive_modal_choice_hint"));
        if (info.armed().isPresent()) {
            var clock = new LinkedHashMap<String, Value>();
            clock.put("armed", status(info.armed().orElseThrow()));
            clock.put("stopped", status(info.stopped().orElseThrow()));
            if (info.canceled()) {
                clock.put("modal_interrupted", new Bool(info.progressStatus() == AdvanceClock.ProgressStatus.MODAL_INTERRUPTED));
                clock.put("canceled", cancellationResult());
            }
            fields.put("exact_day_native_clock", new Obj(clock));
            if (plan.campaignDeadline().isPresent()) {
                clock.put("schema", new Text("xar.ck3.campaign-native-date-clock/v1")); clock.put("scope", new Text("campaign_date_deadline"));
                clock.put("starting_date_raw", new IntegerValue(plan.startingDateRaw())); clock.put("target_date_raw", new IntegerValue(plan.targetDateRaw()));
                clock.put("stopped", status(info.stopped().orElseThrow())); clock.put("early_boundary_cancel", info.canceled() ? cancellationResult() : Nil.INSTANCE);
                clock.put("exact_one_day_qualification_claimed", new Bool(false));
                boolean submitted = integer(starting.semantic().get("speed"), "speed").intValueExact() != plan.speed();
                clock.put("speed_configuration", submitted ? new Obj(Map.of("status", new Text("submitted"), "step", new Text("set-speed-" + plan.speed())))
                        : new Obj(Map.of("status", new Text("already_observed"), "submitted", new Bool(false), "observed_speed", number(plan.speed()),
                            "source_snapshot_id", new Text(starting.identity().frame().snapshotId()), "source_native_revision", new IntegerValue(starting.identity().frame().identity().nativeRevision()),
                            "source_date_raw", new IntegerValue(plan.startingDateRaw()))));
                fields.put("campaign_deadline_native_clock_v1", new Obj(clock));
                if (!plan.exactOneDay()) fields.remove("exact_day_native_clock");
            }
        }
        plan.campaignDeadline().ifPresent(cap -> fields.put("campaign_deadline_v1", AdvancePlan.capJson(cap)));
        plan.dailyWatch().ifPresent(watch -> fields.put("war_daily_watch_v1",new Obj(Map.of("scope",new Text(WarDailyWatch.POLICY),
                "speed",number(2),"watch_army_ids",new Arr(watch.watchArmyIds().stream().map(id -> (Value) number(id)).toList()),
                "roster",WarDailyWatch.encode(watch),"prediction_ready",new Bool(false),"retreat_authorized",new Bool(false)))));
        if (plan.policy().equals("exact_one_day_battle_identity_materialization")) fields.put("battle_identity_materialization", materialization());
        return new Obj(fields);
    }
    /** Reopens the actual clock originals and checks their complete existing report through this
     * same producer. Life settlement/canonical membership and Route history/proof/source admission
     * remain the owning caller's responsibility; this pure check grants no current/Root/Ready/day.
     * Route WINDOW has its separate Battle report schema and is deliberately not accepted here.
     * Full wall time is retained original metadata, never a clock/date or performance proof.
     */
    public static void verifyClockReport(AdvanceClockArchivedReplay actualReplay,ActionCommand parent,
            AdvancePlan plan,AdvanceObservationPort.Frame starting,AdvanceObservationPort.Frame ending,
            AdvanceClock.ProgressStatus actualProgress,Optional<ClockStatusRead.Observation> actualTerminal,
            List<ActionReceipt> actualClockChildren,RawJson original,ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(actualReplay);Objects.requireNonNull(parent);Objects.requireNonNull(plan);
        Objects.requireNonNull(starting);Objects.requireNonNull(ending);Objects.requireNonNull(actualProgress);
        Objects.requireNonNull(actualTerminal);Objects.requireNonNull(original);Objects.requireNonNull(archive);
        actualClockChildren=List.copyOf(actualClockChildren);
        String step=parent.operation().value();boolean life=LifeAdvanceComposite.accepts(step);
        require(life||(step.startsWith(RouteContactSteps.HORIZON)&&RouteContactSteps.supports(step)
                &&RouteContactSteps.parse(step).days()==1),"complete clock report requires a finite Life or Route HORIZON operation");
        if(life)require(AdvancePlan.decode(parent).equals(plan),"Life report plan differs from its exact command");
        actualReplay.verify(parent,plan,starting,ending,actualProgress,actualTerminal,actualClockChildren,archive);
        Obj retained=DriverJson.object(original.bytes(),RawJson.MAXIMUM_BYTES);
        Value wallValue=retained.get("full_wall_nanos");
        require(wallValue instanceof Text wall&&wall.value().matches("0|[1-9][0-9]*")&&wall.value().length()<=19,
                "original complete clock wall time must be canonical nonnegative long text");
        BigInteger wall=new BigInteger(((Text)wallValue).value());
        require(wall.compareTo(BigInteger.valueOf(Long.MAX_VALUE))<=0,"original clock wall time exceeds its producer domain");
        Optional<org.xar.ck3.control.reconciliation.LateOutcome.Status> armed=Optional.empty();
        if(plan.clockMode()!=AdvancePlan.ClockMode.POLLED) {
            ActionReceipt arm=actualClockChildren.stream().filter(child->child.command().operation().value().equals(plan.armStep()))
                    .findFirst().orElseThrow(()->new IllegalArgumentException("complete report lacks its actual arm child"));
            armed=Optional.of(AdvancePrimitives.acknowledgedSentinel(arm.ack().orElseThrow(),plan.armStep()));
        }
        boolean canceled=actualClockChildren.stream().anyMatch(child->child.command().operation().value().startsWith(ClockStatusRead.CANCEL_PREFIX));
        BigInteger end=ending.identity().frame().identity().dateRaw();
        var diagnostics=new AdvanceClock.Diagnostics(plan.startingDateRaw(),end,
                end.subtract(plan.startingDateRaw()).divide(AdvancePlan.DAY).intValueExact(),plan.horizonDays(),plan.speed(),plan.policy(),
                actualProgress,armed,actualTerminal.map(ClockStatusRead.Observation::status),canceled,
                actualClockChildren.stream().map(child->child.command().actionId()).toList(),wall.longValueExact(),actualTerminal);
        var actual=new AdvanceResult(parent,plan,starting,new AdvanceClock.Outcome(ending,diagnostics),actualClockChildren);
        Value read=actualTerminal.<Value>map(value->OpportunityJson.parse(StrictJson.canonical(archive.readReferenceOf(value.receipt()).toJson())))
                .orElse(Nil.INSTANCE);
        require(actual.json().with("native_stop_read_ref",read).equals(retained),
                "complete clock report differs from its exact original command/plan/frames/children/Status/progress");
    }
    /** The one shared consumer route for original-compatible history and restore serializers. */
    public static Optional<RawJson> compatibleResult(ActionReceipt receipt, ActionPorts.OutcomeArchive archive) {
        Optional<ActionState.EffectObservation> observed = ActionEffects.observation(receipt);
        if (observed.isEmpty() || !observed.orElseThrow().observerSchema().equals(AdvancePlan.OBSERVER)) return Optional.empty();
        List<ExpectedValue> actual = observed.orElseThrow().actual();
        Optional<ExpectedText> path = textField(actual, "advance.result.path"), sha = textField(actual, "advance.result.sha256");
        Optional<ExpectedInteger> bytes = integerField(actual, "advance.result.bytes");
        require(path.isPresent() == sha.isPresent() && path.isPresent() == bytes.isPresent(), "advance result reference is incomplete");
        if (path.isEmpty()) return Optional.empty(); // A later reconciliation must not manufacture an old full result.
        var ref = new ExactRef(path.orElseThrow().value(), bytes.orElseThrow().value().longValueExact(), sha.orElseThrow().value());
        RawJson original = archive.loadMaterial(ref);
        var row = OpportunityJson.toNode(DriverJson.object(original.bytes(), RawJson.MAXIMUM_BYTES));
        require(row.isObject() && SCHEMA.equals(StrictJson.text(row.get("schema")))
                && receipt.command().actionId().equals(StrictJson.text(row.get("action_id")))
                && receipt.bodySha256().equals(StrictJson.text(row.get("action_body_sha256")))
                && receipt.command().operation().value().equals(StrictJson.text(row.get("step")))
                && receipt.command().before().machineId().equals(StrictJson.text(row.get("machine_id")))
                && receipt.command().sessionId().equals(StrictJson.text(row.get("session_id")))
                && receipt.command().before().frame().episodeRunId().equals(StrictJson.text(row.get("episode_run_id"))), "archived original life result crossed action/body/source/session/episode");
        require(row.get("starting_date_raw").isIntegralNumber() && row.get("starting_date_raw").bigIntegerValue().equals(receipt.command().before().frame().identity().dateRaw()), "archived advance starting date differs");
        var ending = observed.orElseThrow().after().frame();
        require(row.get("ending_date_raw").isIntegralNumber() && row.get("ending_date_raw").bigIntegerValue().equals(ending.identity().dateRaw())
                && row.get("native_revision").isIntegralNumber() && row.get("native_revision").bigIntegerValue().equals(ending.identity().nativeRevision())
                && row.get("revision").isIntegralNumber() && row.get("revision").bigIntegerValue().equals(ending.revision())
                && ending.snapshotId().equals(StrictJson.text(row.get("snapshot_id"))), "archived advance ending frame differs from its actual settled observation");
        BigInteger actualDays = ending.identity().dateRaw().subtract(receipt.command().before().frame().identity().dateRaw()).divide(AdvancePlan.DAY);
        require(row.get("elapsed_days").isIntegralNumber() && row.get("elapsed_days").bigIntegerValue().equals(actualDays)
                && row.get("calendar_progress_verified").isBoolean() && row.get("calendar_progress_verified").booleanValue() == (actualDays.signum() > 0)
                && row.get("saved_day_credit").isIntegralNumber() && row.get("saved_day_credit").bigIntegerValue().signum() == 0,
                "archived advance day count or unearned save credit differs");
        var readRef = row.get("native_stop_read_ref");
        require(readRef != null, "advance native read reference field missing");
        if (!readRef.isNull()) {
            PlanningReadReceipt read = archive.loadRead(ExactRef.fromJson(readRef));
            require(read.request().source().equals(receipt.command().source()) && read.request().sessionId().equals(receipt.command().sessionId())
                    && read.request().before().game().equals(receipt.command().before().game()) && read.contractId().equals(ClockStatusRead.CONTRACT_ID)
                    && read.request().operation().value().equals(ClockStatusRead.STEP), "archived native stop read crossed registered operation/source/session/Game");
            var clock = row.has("campaign_deadline_native_clock_v1") ? row.get("campaign_deadline_native_clock_v1") : row.get("exact_day_native_clock");
            require(clock != null && clock.isObject() && clock.has("stopped")
                    && SentinelObservation.decode(clock.get("stopped")).equals(ClockStatusRead.decode(read.original())), "archived stop status differs from the actual independent original query");
        }
        return Optional.of(original);
    }
    private static Optional<ExpectedText> textField(List<ExpectedValue> values, String field) {
        List<ExpectedValue> found = values.stream().filter(value -> value.field().value().equals(field)).toList();
        require(found.size() <= 1, "duplicate advance result reference field");
        if (found.isEmpty()) return Optional.empty(); require(found.getFirst() instanceof ExpectedText, "advance result reference text has wrong type"); return Optional.of((ExpectedText) found.getFirst());
    }
    private static Optional<ExpectedInteger> integerField(List<ExpectedValue> values, String field) {
        List<ExpectedValue> found = values.stream().filter(value -> value.field().value().equals(field)).toList();
        require(found.size() <= 1, "duplicate advance result reference field");
        if (found.isEmpty()) return Optional.empty(); require(found.getFirst() instanceof ExpectedInteger, "advance result reference bytes has wrong type"); return Optional.of((ExpectedInteger) found.getFirst());
    }
    private Value cancellationResult() {
        return children.stream().filter(child -> child.command().operation().value().startsWith(ClockStatusRead.CANCEL_PREFIX))
                .reduce((first, second) -> second).flatMap(ActionReceipt::ack).flatMap(NativeActionPort.AckReceived::originalResultToken)
                .<Value>map(token -> DriverJson.object(token.bytes(), RawJson.MAXIMUM_BYTES)).orElseThrow(() -> new IllegalStateException("canceled native clock lacks exact original durable cancel result"));
    }
    private Obj materialization() {
        BigInteger subject = AdvanceHistory.materializationSubject(starting.semantic()).orElseThrow(); var now = outcome.endingFrame();
        var fields = new LinkedHashMap<String, Value>(); fields.put("schema_version", number(1)); fields.put("status", new Text("one_day_advanced"));
        fields.put("proof_kind", new Text("battle_identity_materialization")); fields.put("diagnostic_reason", new Text(AdvanceHistory.IDENTITY_DIAGNOSTIC));
        fields.put("subject_public_cunit_id", new IntegerValue(subject)); fields.put("elapsed_days", number(1)); fields.put("next_revision_requirement", new Text("full_combat_id"));
        for (String key : List.of("snapshot_id", "revision", "native_revision", "date_raw")) {
            fields.put("starting_" + key, nullable(starting.semantic(), key)); fields.put("ending_" + key, nullable(now.semantic(), key));
        }
        return new Obj(fields);
    }
    public static void validateMaterialization(AdvanceObservationPort.Frame before, AdvanceObservationPort.Frame after) {
        BigInteger subject = AdvanceHistory.materializationSubject(before.semantic()).orElseThrow();
        require(after.identity().frame().identity().dateRaw().equals(before.identity().frame().identity().dateRaw().add(AdvancePlan.DAY))
                && AdvancePolicy.truth(after.semantic(), "paused") && after.identity().frame().revision().compareTo(before.identity().frame().revision()) > 0
                && after.identity().frame().identity().nativeRevision().compareTo(before.identity().frame().identity().nativeRevision()) > 0
                && after.identity().frame().episodeRunId().equals(before.identity().frame().episodeRunId())
                && after.identity().frame().identity().player().equals(before.identity().frame().identity().player())
                && Objects.equals(after.semantic().get("episode_character_id"), before.semantic().get("episode_character_id"))
                && AdvancePolicy.players(after.semantic()).stream().anyMatch(army -> new IntegerValue(subject).equals(army.get("army_id"))
                    && AdvancePolicy.truth(army, "controllable") && AdvancePolicy.truth(army, "in_combat")), "battle identity materialization did not produce the exact next paused public combat revision");
    }
    public static Obj warSummary(Obj frame) {
        List<Value> wars = new ArrayList<>();
        for (Obj war : AdvancePolicy.wars(frame)) {
            var fields = new LinkedHashMap<String, Value>();
            for (String key : List.of("war_id", "player_relative_war_score", "enemy_primary_default_raise_province_id")) fields.put(key, nullable(war, key));
            fields.put("war_objective_province_ids", war.get("war_objective_province_ids") instanceof Arr array ? array : new Arr(List.of()));
            fields.put("objective_province_states", new Arr(AdvancePolicy.objects(war.get("objective_province_states"), "objective states").stream()
                    .filter(row -> row.get("active_siege") instanceof Obj).map(row -> (Value) row).toList()));
            fields.put("player_armies", armies(war.get("allied_armies"), true)); fields.put("enemy_armies", armies(war.get("enemy_armies"), false));
            wars.add(new Obj(fields));
        }
        return new Obj(Map.of("date_raw", nullable(frame, "date_raw"), "wars", new Arr(wars)));
    }
    private static Arr armies(Value source, boolean onlyControlled) {
        List<Obj> rows = new ArrayList<>();
        for (Obj army : AdvancePolicy.objects(source, "army observations")) {
            if (onlyControlled && !AdvancePolicy.truth(army, "controllable")) continue;
            var fields = new LinkedHashMap<String, Value>();
            for (String key : List.of("army_id", "current_province_id", "soldiers", "move_target_province_id")) fields.put(key, nullable(army, key));
            for (String key : List.of("in_combat", "retreating")) if (army.get(key) instanceof Bool) fields.put(key, army.get(key));
            for (String key : List.of("army_state", "army_state_code")) if (army.get(key) instanceof Text || army.get(key) instanceof IntegerValue) fields.put(key, army.get(key));
            for (String key : List.of("siege_days_left", "siege_province_holder_character_id", "siege_province_in_player_subrealm")) if (army.members().containsKey(key)) fields.put(key, army.get(key));
            if (army.get("route_province_ids") instanceof Arr route) fields.put("route_province_ids", route);
            rows.add(new Obj(fields));
        }
        rows.sort(Comparator.comparing(row -> row.get("army_id") instanceof IntegerValue id ? id.value() : BigInteger.valueOf(Integer.MAX_VALUE)));
        return new Arr(rows.stream().map(row -> (Value) row).toList());
    }
    /** The original compatible result uses the actual shared numeric Sentinel wire, never a guessed status map. */
    private static Obj status(org.xar.ck3.control.reconciliation.LateOutcome.Status actual) {
        return DriverJson.object(StrictJson.canonical(SentinelObservation.toJson(actual)), RawJson.MAXIMUM_BYTES);
    }
    public static String progressStatus(AdvanceClock.ProgressStatus status) { return status.name().toLowerCase(java.util.Locale.ROOT); }
    private static Value nullable(Obj object, String key) { return object.get(key) == null ? Nil.INSTANCE : object.get(key); }
    private static IntegerValue number(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
}
