package org.xar.ck3.control.application.advance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.PublicCUnitId;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.reconciliation.LateOutcome.*;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryPolicy;

/** Production branch/fault regressions ported from the original driver and native sentinel producer fixtures.
 * These are offline source tests, not a live CK3 qualification or a replacement for root graph/transport CI. */
final class AdvanceRegressionTest {
    private static final Instant NOW = Instant.parse("2026-10-23T16:00:00Z");
    private static final BigInteger START = BigInteger.valueOf(53_288_256);
    private static final ExactRef REF = new ExactRef("fixture/original-native-sentinel.json", 1, "a".repeat(64));
    private static final G2Source SOURCE = new G2Source("xenoamess-full-tower-eb9d2c1186", NOW.toString(), "1.20.0.4", REF);
    private static final Claims CLAIMS = new Claims(Set.of(), Set.of(), Set.of(), Set.of());
    private static final Set<OperationKey> STEPS = Set.of(new OperationKey("life-advance"), new OperationKey("life-advance-one-day"),
            new OperationKey("set-speed-1"), new OperationKey("set-speed-2"), new OperationKey("set-speed-3"),
            new OperationKey("set-speed-4"), new OperationKey("set-speed-5"), new OperationKey("pause-map"), new OperationKey("resume-map"));
    private static final Set<String> CAPS = Set.of(ClockStatusRead.ARM_CAP, ClockStatusRead.STATUS_CAP, ClockStatusRead.CANCEL_CAP);
    private static Obj json(String value) { return object(OpportunityJson.parse(value.getBytes(StandardCharsets.UTF_8)), "fixture"); }
    private static IntegerValue number(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static Obj basic() {
        return json("""
            {"snapshot_id":"native:1","revision":1,"native_revision":1,"date_raw":53288256,
             "paused":true,"map_ready":true,"speed":1,"episode_run_id":"fixture-episode","episode_character_id":29829,
             "local_player_id":0,"played_character":{"character_id":29829,"alive":true},
             "active_event":null,"pending_character_interaction":null,"one_life_terminal_reason":null,
             "diagnostics":{"bridge_pid":4242,"connection_generation":1},"player_armies":[],"active_wars":[],
             "top_exclusive_modal_choice_hint":{"status":"absent"},"war_objective_assault_supported":true}
            """);
    }
    private static ObservationIdentity identity(Obj semantic) {
        return new ObservationIdentity(SOURCE.machineId(), new GameGeneration(4242, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new ProposalFrame(new Frame(BigInteger.valueOf(29829), integer(semantic.get("native_revision"), "native_revision"), integer(semantic.get("date_raw"), "date_raw")),
                        text(semantic.get("snapshot_id"), "snapshot_id"), integer(semantic.get("revision"), "revision"), text(semantic.get("episode_run_id"), "episode")), 1);
    }
    private static PlanningRequest request(Obj semantic) {
        return new PlanningRequest(identity(semantic), SOURCE, "fixture-session", NOW.plusSeconds(30),
                new PlanningObservation(semantic, List.of(), STEPS, CAPS, Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false));
    }
    private static ActionCommand original(PlanningRequest request, String step) {
        return new ActionCommand("fixture-advance", request.before(), SOURCE, request.sessionId(), new OperationKey(step),
                new Obj(Map.of("caller_evidence", new Text("original-source-bound-call"))),
                new ExpectedPostcondition(1, request.before(), SOURCE, "fixture/skeleton-v1", List.of(new ExpectedBoolean(new FieldKey("paused"), true))), CLAIMS, request.deadline());
    }
    private static AdvanceObservationPort.Frame observed(Obj semantic) {
        return new AdvanceObservationPort.Frame(identity(semantic), SOURCE, "fixture-session", semantic, "native-read-" + integer(semantic.get("native_revision"), "revision"), NOW, REF);
    }
    @Test void originalStartingRichFrameSelectsThirtySevenAndOneDays() {
        assertEquals(30, AdvancePolicy.horizonDays(basic()));
        Obj war = basic().with("active_wars", new Arr(List.of(json("{\"war_id\":1,\"allied_armies\":[],\"enemy_armies\":[]}"))));
        assertEquals(7, AdvancePolicy.horizonDays(war));
        Obj moving = war.with("player_armies", new Arr(List.of(json("{\"army_id\":11,\"controllable\":true,\"army_state\":\"moving\",\"army_state_code\":7,\"in_combat\":false,\"retreating\":false}"))));
        assertEquals(1, AdvancePolicy.horizonDays(moving));
        assertEquals(new AdvancePolicy.Choice(1, 1, "player_tactical", false), AdvancePolicy.select(request(moving), "life-advance"));
        for (String state : List.of("combat", "retreating"))
            assertEquals(1, AdvancePolicy.horizonDays(war.with("player_armies", new Arr(List.of(json("{\"controllable\":true,\"army_state\":\"" + state + "\"}"))))));
    }
    @Test void exactGenericFastDayRetainsCombatAndMissingFlagExclusions() {
        Obj army = json("{\"controllable\":true,\"in_combat\":false,\"retreating\":false,\"army_state\":\"moving\",\"army_state_code\":7}");
        Obj frame = basic().with("player_armies", new Arr(List.of(army)));
        assertEquals(5, AdvancePolicy.select(request(frame), "life-advance-one-day").speed());
        for (Value value : List.of(new Bool(true), Nil.INSTANCE)) {
            Obj changed = frame.with("player_armies", new Arr(List.of(army.with("in_combat", value))));
            assertEquals(1, AdvancePolicy.select(request(changed), "life-advance-one-day").speed());
        }
        Obj running = frame.with("paused", new Bool(false));
        assertThrows(IllegalArgumentException.class, () -> AdvancePolicy.select(request(running), "life-advance-one-day"));
    }
    @Test void campaignLookupOneDayDoesNotReplaceActualThirtyDayHorizonAndCrownBound() {
        PlanningRequest request = request(basic()); ActionCommand original = original(request, "life-advance");
        var cap = new CampaignDeadline.Cap("campaign-fixture", CampaignDeadline.CALENDAR_PROFILE, START, START.add(BigInteger.valueOf(24)),
                START.add(BigInteger.valueOf(10 * 24)), START.add(BigInteger.valueOf(360 * 24)), START.add(BigInteger.valueOf(24)), CampaignDeadline.Status.ADVANCE);
        ActionCommand rewritten = AdvanceRewrite.rewrite(request, original, "life-advance", cap); AdvancePlan plan = AdvancePlan.decode(rewritten);
        assertEquals(10, plan.horizonDays()); assertEquals(START.add(BigInteger.valueOf(30 * 24)), plan.campaignDeadline().orElseThrow().requestedTargetDateRaw());
        assertEquals(original.actionId(), rewritten.actionId()); assertEquals(original.before(), rewritten.before()); assertEquals(original.source(), rewritten.source());
        assertEquals(original.sessionId(), rewritten.sessionId()); assertEquals(original.claims(), rewritten.claims()); assertEquals(original.deadline(), rewritten.deadline());
        assertEquals(original.arguments().get("caller_evidence"), rewritten.arguments().get("caller_evidence"));
        assertEquals(plan.expected(), rewritten.expected().values());
        assertEquals(3, AdvancePlan.decode(AdvanceRewrite.rewriteBound(request, original, "life-advance", Optional.of(cap), 3)).horizonDays());
    }
    @Test void planSerdeRejectsBooleanFloatMissingNullAndWrongFields() {
        PlanningRequest request = request(basic()); AdvancePlan plan = AdvancePlan.decode(AdvanceRewrite.exactDay(request, original(request, "life-advance")));
        Obj roundtrip = object(OpportunityJson.parse(OpportunityJson.encode(plan.json())), "roundtrip"); assertEquals(plan, AdvancePlan.decode(roundtrip));
        for (Value invalid : List.of(new Bool(true), new DecimalValue("1.0"), Nil.INSTANCE))
            assertThrows(IllegalArgumentException.class, () -> AdvancePlan.decode(roundtrip.with("horizon_days", invalid)));
        var missing = new java.util.LinkedHashMap<>(roundtrip.members()); missing.remove("target_date_raw");
        assertThrows(IllegalArgumentException.class, () -> AdvancePlan.decode(new Obj(missing)));
        assertThrows(IllegalArgumentException.class, () -> AdvancePlan.decode(roundtrip.with("target_date", number(1))));
    }
    // Values are the actual original ClockProvider fixture's native producer fields in
    // test_exact_day_native_clock_paused_next_frame.py, not a guessed ACK=>completed-day conversion.
    private static Status arm() {
        return new Status(State.ARMED, new CrossJsDecimalUInt64("37"), START.intValueExact(), START.add(BigInteger.valueOf(24)).intValueExact(), START.intValueExact(),
                0, 1, Mode.TERMINAL_OR_SENTINEL, 0, 0, 0, 0, 0, List.of(), 0, -1, false, false, false, false);
    }
    private static Status stop(String generation, long ticks, int overshoot) {
        int end = START.add(BigInteger.valueOf(24)).intValueExact();
        return new Status(State.TRIGGERED, new CrossJsDecimalUInt64(generation), START.intValueExact(), end, end, end, 1,
                Mode.TERMINAL_OR_SENTINEL, 0, 0, ticks, 0, 1, List.of("date_deadline"), 0, overshoot, true, true, false, false);
    }
    private static AdvancePlan clockPlan() { return new AdvancePlan(START, START.add(BigInteger.valueOf(24)), 1, 1, "fixture_exact_native_clock", true, AdvancePlan.ClockMode.EXACT_SENTINEL, Optional.empty()); }
    @Test void nativeOriginalStopNeedsMatchingGenerationTickDateAndPauseOwner() {
        AdvancePlan plan = clockPlan(); AdvanceClock.validateArm(arm(), plan);
        Status retained = SentinelObservation.decode(SentinelObservation.toJson(stop("37", 1, 0)));
        AdvanceClock.validateStop(arm(), retained, plan, plan.targetDateRaw());
        assertThrows(IllegalArgumentException.class, () -> AdvanceClock.validateStop(arm(), stop("38", 1, 0), plan, plan.targetDateRaw()));
        assertThrows(IllegalArgumentException.class, () -> AdvanceClock.validateStop(arm(), stop("37", 0, 0), plan, plan.targetDateRaw()));
        assertThrows(IllegalArgumentException.class, () -> AdvanceClock.validateStop(arm(), stop("37", 1, 1), plan, plan.targetDateRaw()));
        assertThrows(IllegalArgumentException.class, () -> AdvanceClock.validateStop(arm(), retained, plan, plan.targetDateRaw().add(BigInteger.valueOf(24))));
    }
    @Test void assaultStartedHistoryNeedsCurrentSameSiegeAndPreservesFailureAfterRestore() {
        Obj start = json("{\"command\":\"start-assault-19\",\"ok\":true,\"result\":{\"assault_action\":{\"status\":\"assault_started\",\"siege_id\":19,\"war_id\":1,\"province_id\":2510}}}");
        Obj frame = basic().with("active_wars", new Arr(List.of(json("{\"war_id\":1,\"objective_province_states\":[{\"province_id\":2510,\"siege_observable\":false}]}"))));
        var opened = AdvanceHistory.openAssaults(List.of(start)); assertEquals(1, opened.size());
        assertEquals("siege_unobservable_after_start", AdvanceHistory.unobservableAssaults(frame, List.of(start), opened).getFirst().reason());
        Obj restore = json("{\"command\":\"restore-checkpoint\",\"ok\":true,\"result\":{}}");
        assertTrue(AdvanceHistory.openAssaults(List.of(start, restore)).isEmpty());
        assertTrue(AdvanceHistory.unresolvedWarWatch(List.of(json("{\"result\":{\"schema\":\"xar.war-daily-watch-unresolved.v1\",\"never_replay\":true}}"))));
    }
    @Test void historicalHoldOnlyReleasesForActualOrdinaryCampaignIdentityAndIntegerVersion() {
        Obj held = basic().with("episode_run_id", new Text("native-29829-2bc2d599f7f9")); assertTrue(AdvanceReadiness.h3937(held));
        Obj goal = json("{\"format_version\":1,\"goal_key\":\"dynasty_continuity\",\"campaign_id\":\"native-29829-2bc2d599f7f9\",\"current_character_id\":29829}");
        Obj ordinary = held.with("succession_lifecycle", json("{\"lifecycle\":\"ordinary_campaign_succession\"}")).with("campaign_goal", goal);
        assertFalse(AdvanceReadiness.h3937(ordinary));
        assertTrue(AdvanceReadiness.h3937(ordinary.with("campaign_goal", goal.with("format_version", new Bool(true)))));
    }
    @Test void sameSourceCrownRetryRoundsUpAndMissingActualStateIsRefused() {
        var frame = observed(basic()); var crown = new CrownRetryPolicy.State(false, new CrownRetryPolicy.Hint(
                new CrownRetryPolicy.ContextKey(BigInteger.valueOf(4242), "fixture-episode"), BigInteger.valueOf(29829), START.add(BigInteger.valueOf(25)), "crown_authority_2", "{}"));
        assertEquals(2, AdvanceHistory.facts(frame, List.of(), STEPS, CAPS, crown, true, true, REF).crownRetryMaximumDays());
        assertThrows(NullPointerException.class, () -> AdvanceHistory.facts(frame, List.of(), STEPS, CAPS, null, true, true, REF));
    }
    private static Obj identityPending(Value subject) {
        Obj frame = basic().with("player_armies", new Arr(List.of(new Obj(Map.of("army_id", subject, "controllable", new Bool(true), "in_combat", new Bool(true))))));
        return frame.with("battle_control_snapshot_v1_status", new Text(AdvanceHistory.IDENTITY_PENDING))
                .with("battle_control_snapshot_v1_subject_army_id", subject)
                .with("battle_control_snapshot_v1_diagnostic_reason", new Text(AdvanceHistory.IDENTITY_DIAGNOSTIC))
                .with("battle_control_snapshot_v1_native_query_status", new Text("state_changed"))
                .with("battle_control_snapshot_v1_query_attempts", number(3)).with("battle_control_snapshot_v1", Nil.INSTANCE)
                .with("battle_control_snapshot_v1_queried_snapshot_id", frame.get("snapshot_id"))
                .with("battle_control_snapshot_v1_queried_revision", frame.get("revision"))
                .with("battle_control_snapshot_v1_queried_native_revision", frame.get("native_revision"));
    }
    @Test void materializationAcceptsPublicCunitZeroAndRejectsWrongIntegerDomains() {
        assertEquals(BigInteger.ZERO, AdvanceHistory.materializationSubject(identityPending(number(0))).orElseThrow());
        assertEquals(PublicCUnitId.MAXIMUM, AdvanceHistory.materializationSubject(identityPending(number(Integer.MAX_VALUE))).orElseThrow());
        for (Value wrong : List.of(new Bool(false), new DecimalValue("0.0"), Nil.INSTANCE, number(-1), number((long) Integer.MAX_VALUE + 1)))
            assertThrows(IllegalArgumentException.class, () -> AdvanceHistory.materializationSubject(identityPending(wrong)));
        Obj subject = identityPending(number(0));
        assertThrows(IllegalArgumentException.class, () -> AdvanceHistory.materializationSubject(subject.with("player_armies", new Arr(List.of()))));
        Obj absent = basic();
        assertTrue(AdvanceHistory.materializationSubject(absent).isEmpty());
    }
    @Test void actualAdvanceResultRoundtripFeedsStrictMaterializationHistory() {
        Obj before = identityPending(number(0));
        Obj ending = before.with("snapshot_id", new Text("native:2")).with("revision", number(2)).with("native_revision", number(2))
                .with("date_raw", new IntegerValue(START.add(AdvancePlan.DAY)));
        AdvancePlan plan = new AdvancePlan(START, START.add(AdvancePlan.DAY), 1, 1, "exact_one_day_battle_identity_materialization", true,
                AdvancePlan.ClockMode.POLLED, Optional.empty());
        ActionCommand command = new ActionCommand("materialize-public-zero", identity(before), SOURCE, "fixture-session", new OperationKey("life-advance"),
                new Obj(Map.of(AdvancePlan.KEY, plan.json())), new ExpectedPostcondition(1, identity(before), SOURCE, AdvancePlan.OBSERVER, plan.expected()), CLAIMS, NOW.plusSeconds(30));
        var diagnostics = new AdvanceClock.Diagnostics(START, START.add(AdvancePlan.DAY), 1, 1, 1, plan.policy(), AdvanceClock.ProgressStatus.POSTCONDITION,
                Optional.empty(), Optional.empty(), false, List.of(), 1, Optional.empty());
        Obj produced = new AdvanceResult(command, plan, observed(before), new AdvanceClock.Outcome(observed(ending), diagnostics), List.of()).json();
        Obj result = object(OpportunityJson.parse(OpportunityJson.encode(produced)), "serialized actual result");
        assertEquals(produced, result);
        assertTrue(AdvanceHistory.materializationConsumed(ending, List.of(successfulAdvance(result)), BigInteger.ZERO));
        for (String field : List.of("paused", "timeline_speed", "timeline_policy")) {
            var missing = new java.util.LinkedHashMap<>(result.members()); missing.remove(field);
            assertFalse(AdvanceHistory.materializationConsumed(ending, List.of(successfulAdvance(new Obj(missing))), BigInteger.ZERO));
            for (Value wrong : List.of(Nil.INSTANCE, new Bool(false), new DecimalValue("1.0"), new Text("wrong")))
                assertFalse(AdvanceHistory.materializationConsumed(ending, List.of(successfulAdvance(result.with(field, wrong))), BigInteger.ZERO));
        }
        assertFalse(AdvanceHistory.materializationConsumed(ending, List.of(successfulAdvance(result.with("timeline_speed", number(2)))), BigInteger.ZERO));
        Obj material = object(result.get("battle_identity_materialization"), "materialization");
        assertFalse(AdvanceHistory.materializationConsumed(ending, List.of(successfulAdvance(result.with("battle_identity_materialization", material.with("schema_version", new Bool(true))))), BigInteger.ZERO));
        assertFalse(AdvanceHistory.materializationConsumed(ending, List.of(successfulAdvance(result.with("battle_identity_materialization", material.with("ending_native_revision", number(1))))), BigInteger.ZERO));
    }
    private static Obj successfulAdvance(Obj result) {
        return new Obj(Map.of("command", new Text("life-advance"), "ok", new Bool(true), "result", result));
    }
    @Test void unknownDurableArmStopsBeforeAnyResumePauseOrCancel() {
        Obj semantic = basic().with("war_objective_assault_supported", new Bool(false));
        var frame = observed(semantic); PlanningRequest request = request(semantic); ActionCommand parent = AdvanceRewrite.exactDay(request, original(request, "life-advance"));
        AdvancePlan plan = AdvancePlan.decode(parent);
        List<ActionReceipt> attempted = new ArrayList<>();
        CompositeActionPort.Children children = new CompositeActionPort.Children() {
            @Override public String nextActionId() { return "fixture-advance.child." + attempted.size(); }
            @Override public List<ActionReceipt> completed() { return List.copyOf(attempted); }
            @Override public ActionReceipt submit(ActionCommand child) {
                ActionReceipt unknown = new ActionReceipt(1, attempted.size() + 1L, child, ActionCodec.bodySha256(child),
                        new ActionState.Unknown(Optional.empty(), Optional.empty(), "original native arm write outcome unknown", List.of(REF)));
                attempted.add(unknown); return unknown;
            }
        };
        AdvanceObservationPort frames = new AdvanceObservationPort() {
            @Override public Frame current(ActionCommand command, Instant deadline) { return frame; }
            @Override public Frame next(ActionCommand command, ObservationIdentity after, Instant deadline) { fail("UNKNOWN cannot authorize a fresh clock continuation"); return frame; }
        };
        PlanningReadPort reads = new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest read) { fail("UNKNOWN cannot authorize a Status query/cleanup branch"); return new PlanningReadResult.Unavailable<>("unreachable", Optional.empty()); }
        };
        ClockStatusRead statuses = new ClockStatusRead(reads, REF, new UnusedArchive());
        var timeline = new AdvanceClock(frames, statuses, (command, current) -> new AdvanceReadiness.Facts(current.identity(), STEPS, CAPS, false, false, false, 45, REF),
                Clock.fixed(NOW, ZoneOffset.UTC), 16, Duration.ofSeconds(1), Duration.ofSeconds(2));
        assertThrows(AdvanceClock.ChildUnresolved.class, () -> timeline.execute(parent, children, frame, plan));
        assertEquals(1, attempted.size()); assertEquals(plan.armStep(), attempted.getFirst().command().operation().value());
        assertFalse(LifeAdvanceComposite.accepts("life-advance-one-day-extra"));
    }
    private static final class UnusedArchive implements ActionPorts.OutcomeArchive {
        private static IllegalStateException unused() { return new IllegalStateException("unexpected evidence mutation in UNKNOWN regression"); }
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value) { throw unused(); }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef value) { throw unused(); }
        @Override public ExactRef preserveRequest(NativeRequest value) { throw unused(); }
        @Override public NativeRequest loadRequest(ExactRef value) { throw unused(); }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value) { throw unused(); }
        @Override public ExactRef requestReferenceOf(NativeRequest value) { throw unused(); }
        @Override public ExactRef preserveRead(PlanningReadReceipt value) { throw unused(); }
        @Override public PlanningReadReceipt loadRead(ExactRef value) { throw unused(); }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt value) { throw unused(); }
        @Override public ExactRef preserveRecord(ActionRecord value) { throw unused(); }
        @Override public ActionRecord loadRecord(ExactRef value) { throw unused(); }
        @Override public ExactRef recordReferenceOf(ActionRecord value) { throw unused(); }
        @Override public ExactRef preserveReceipt(ActionReceipt value) { throw unused(); }
        @Override public ActionReceipt loadReceipt(ExactRef value) { throw unused(); }
        @Override public ExactRef receiptReferenceOf(ActionReceipt value) { throw unused(); }
        @Override public ExactRef preserveMaterial(RawJson value) { throw unused(); }
        @Override public RawJson loadMaterial(ExactRef value) { throw unused(); }
        @Override public ExactRef materialReferenceOf(RawJson value) { throw unused(); }
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value) { throw unused(); }
        @Override public byte[] loadNativeFrame(ExactRef value) { throw unused(); }
    }
}
