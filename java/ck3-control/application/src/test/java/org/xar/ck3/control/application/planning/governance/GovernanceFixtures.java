package org.xar.ck3.control.application.planning.governance;

import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinCodec;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy;
import org.xar.ck3.control.planning.optionalcadence.CadenceModels;
import org.xar.ck3.control.wave2.planning.lifestyleconsumer.LifestyleConsumer;
import org.xar.ck3.control.wave3.governance.lifestylehistory.LifestyleHistory;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import static org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Explicit synthetic unit values, never native captures, source qualification or handwritten golden files. */
final class GovernanceFixtures {
    private GovernanceFixtures() { }
    static final Instant NOW = Instant.parse("2026-10-23T16:00:00Z");
    static final ExactRef REF = new ExactRef("unit-fixture/original.json", 1, "a".repeat(64));
    static final G2Source SOURCE = new G2Source("xenoamess-full-tower-eb9d2c1186", NOW.toString(), "1.20.0.4", REF);
    static IntegerValue n(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    static ObservationIdentity identity(int revision) {
        return new ObservationIdentity(SOURCE.machineId(), new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.valueOf(revision), BigInteger.valueOf(100)),
                        "native-" + revision, BigInteger.valueOf(revision), "unit-episode"), 1);
    }
    static PlanningRequest request(int revision, boolean opening, List<Obj> history) {
        Obj snapshot = new Obj(java.util.Map.of()).with("snapshot_id", new Text("native-" + revision)).with("revision", n(revision)).with("native_revision", n(revision)).with("date_raw", n(100)).with("proof_epoch", n(1)).with("episode_run_id", new Text("unit-episode")).with("paused", new Bool(true)).with("map_ready", new Bool(true)).with("played_character", new Obj(java.util.Map.of()).with("character_id", n(29829)).with("alive", new Bool(true))).with("active_wars", new Arr(List.of())).with("player_armies", new Arr(List.of())).with("active_event", Nil.INSTANCE).with("pending_character_interaction", Nil.INSTANCE);
        Set<OperationKey> actions = Set.of(new OperationKey("life-advance"), GovernancePolicies.COUNCIL, GovernancePolicies.CORE_COUNCIL,
                GovernancePolicies.FOCUS, GovernancePolicies.PERK, GovernancePolicies.CROWN);
        var observation = new PlanningObservation(snapshot, history, actions,
                Set.of("game.query.council-composition-candidates-v1", "game.action.assign-councillor-v1"), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), opening);
        return new PlanningRequest(identity(revision), SOURCE, "unit-session", NOW.plusSeconds(30), observation);
    }
    static PlanningRequest request() { return request(9, false, List.of()); }
    static OrdinaryPolicy.Draft advance(PlanningRequest request) {
        var expected = new ExpectedPostcondition(1, request.before(), SOURCE, "unit-timeline/v1", List.of(new ExpectedBoolean(new FieldKey("paused"), true)));
        var command = new ActionCommand("unit-advance", request.before(), SOURCE, request.sessionId(), new OperationKey("life-advance"), new Obj(java.util.Map.of()), expected,
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), request.deadline());
        return new OrdinaryPolicy.Draft("unit-core", "ordinary", "original advance", OrdinaryPolicy.Kind.ORDINARY,
                Optional.of(command), OrdinaryPolicy.Purpose.DATE_ADVANCE, Optional.empty(), new Obj(java.util.Map.of()).with("original_marker", new Text("preserve")));
    }
    static DomainState clear() { return new DomainState(DomainStatus.KNOWN_CLEAR, Optional.empty(), Optional.empty(), new Obj(java.util.Map.of())); }
    static Durable durable(PlanningRequest request) {
        return new Durable(request.before(), request.sessionId(), Optional.of(CadenceModels.State.empty("unit-episode")),
                Optional.of(new OpeningGate("unit-episode", BigInteger.valueOf(100), OpeningStage.AWAIT_SUBMIT, Optional.empty(), Optional.empty())), Optional.of(clear()), Optional.of(clear()));
    }
    static Life life(PlanningRequest request, String preferred, boolean opening) {
        String targetLifestyle = preferred.equals(MARTIAL_FOCUS) ? MARTIAL : STEWARDSHIP;
        var focus = new Focus(Field.of(opening ? "absent" : "present"), opening ? Field.nullValue() : Field.of(WEALTH_FOCUS),
                opening ? Field.nullValue() : Field.of(STEWARDSHIP));
        var current = new Progress(Field.of(opening ? "absent" : "present"), opening ? Field.nullValue() : Field.of(STEWARDSHIP),
                opening ? Field.nullValue() : Field.of(BigInteger.ONE));
        var candidates = new Candidates(Field.of("available"), Field.of(List.of(new Candidate("cutting_corners_perk", STEWARDSHIP))));
        var legalFocus = new Candidates(Field.of("available"), Field.of(List.of(new Candidate(WEALTH_FOCUS, STEWARDSHIP), new Candidate(MARTIAL_FOCUS, MARTIAL))));
        var readiness = new Readiness(Field.of(true), Field.of(true), Field.of(true), Field.of(true), Field.of(true), Field.of(true));
        var frame = request.before().frame();
        var snapshot = new Snapshot(Field.of("available"), Field.of(frame.snapshotId()), Field.of(frame.episodeRunId()), Field.of(frame.revision()),
                Field.of(frame.identity().nativeRevision()), Field.of(BigInteger.ONE), Field.of(frame.identity().dateRaw()), Field.of(frame.identity().player()),
                Field.of(focus), Field.of(current), Field.of(new Progress(Field.of("present"), Field.of(targetLifestyle), Field.of(BigInteger.ZERO))),
                Field.of(List.of()), Field.of(candidates), Field.of(legalFocus), Field.of(readiness));
        var minimum = new Request(Field.of(snapshot), Field.of(true), Field.of(true), Field.of(true), false, opening, preferred, Field.nullValue(), Field.of(true));
        var routed = new LifestyleMinCodec.RoutedRequest(minimum, LifestyleMinCodec.ProgressRoute.LIFE2, Field.missing());
        var scope = new LifestyleConsumer.Scope(LifestyleConsumer.ScopeStatus.ADMITTED, Field.of(true), Field.of(true), Field.of("feudal_government"), frame.identity().nativeRevision(), frame.identity().player());
        var observed = new LifestyleConsumer.AvailableQuery(opening ? LifestyleConsumer.ObservationStatus.STOCK_FOCUS_AVAILABLE : LifestyleConsumer.ObservationStatus.AVAILABLE,
                opening ? "stock_focus_ready" : "ready", routed);
        Obj node = object(parse(StrictJson.canonical(LifestyleMinCodec.requestNode(minimum).get("snapshot"))), "snapshot");
        Obj original = new Obj(java.util.Map.of()).with("status", new Text(opening ? "stock_focus_available" : "available")).with("snapshot", node).with("source_frame", new Obj(java.util.Map.of()).with("snapshot_id", new Text(frame.snapshotId())).with("revision", new IntegerValue(frame.revision())).with("native_revision", new IntegerValue(frame.identity().nativeRevision())).with("date_raw", new IntegerValue(frame.identity().dateRaw())));
        return new Life(new LifestyleConsumer.Request(true, scope, observed), new LifestyleHistory.Input(frame.episodeRunId(), List.of()), original);
    }
    static Obj councilRaw(PlanningRequest request, CouncilSelection.Position role, int incumbentSkill, int firstSkill, int secondSkill) {
        var frame = request.before().frame(); Obj readiness = new Obj(java.util.Map.of());
        for (String key : List.of("identity_ready", "candidate_collection_ready", "incumbent_ready", "incumbent_main_skill_ready", "candidate_legality_ready", "main_skill_ready", "action_route_ready", "same_frame_ready", "ready")) readiness = readiness.with(key, new Bool(true));
        Obj position = new Obj(java.util.Map.of()).with("position_key", new Text(role.key())).with("incumbent_character_id", n(20)).with("incumbent_main_skill", new Obj(java.util.Map.of()).with("key", new Text(role.skill())).with("value", n(incumbentSkill))).with("vacant", new Bool(false)).with("action_route", new Text("replace"));
        List<Value> candidates = new ArrayList<>(), gates = new ArrayList<>();
        int[] skills = { firstSkill, secondSkill };
        for (int index = 0; index < skills.length; index++) {
            candidates.add(new Obj(java.util.Map.of()).with("character_id", n(31 - index)).with("native_collection_ordinal", n(index)).with("eligible", new Bool(true)).with("eligibility_reason", new Text("native_candidate_provider_accepted")).with("main_skill", new Obj(java.util.Map.of()).with("key", new Text(role.skill())).with("value", n(skills[index]))).with("action_route", new Text("replace")));
            gates.add(new Obj(java.util.Map.of()).with("character_id", n(31 - index)).with("native_collection_ordinal", n(index)).with("final_gate_available", new Bool(true)).with("candidate_already_councillor", new Bool(false)).with("candidate_is_guest", new Bool(false)).with("pending_character_interaction", new Bool(false)).with("incumbent_fireability_evaluated", new Bool(true)).with("incumbent_can_be_fired", new Bool(true)));
        }
        Obj payload = new Obj(java.util.Map.of()).with("snapshot", new Obj(java.util.Map.of()).with("snapshot_id", new Text("native:" + frame.identity().nativeRevision())).with("public_revision", new IntegerValue(frame.identity().nativeRevision())).with("native_revision", new IntegerValue(frame.identity().nativeRevision())).with("date_raw", new IntegerValue(frame.identity().dateRaw())).with("paused", new Bool(true))).with("owner_character_id", new IntegerValue(frame.identity().player())).with("position", position).with("candidate_collection_complete", new Bool(true)).with("candidates", new Arr(candidates)).with("readiness", readiness);
        return new Obj(java.util.Map.of()).with("status", new Text("available")).with("council_composition_candidates", payload).with("queried_snapshot_id", new Text(frame.snapshotId())).with("queried_revision", new IntegerValue(frame.revision())).with("queried_native_revision", new IntegerValue(frame.identity().nativeRevision())).with("source_frame", new Obj(java.util.Map.of()).with("snapshot_id", new Text(frame.snapshotId())).with("revision", new IntegerValue(frame.revision())).with("native_revision", new IntegerValue(frame.identity().nativeRevision())).with("date_raw", new IntegerValue(frame.identity().dateRaw())).with("player_character_id", new IntegerValue(frame.identity().player())).with("paused", new Bool(true))).with("council_final_gates", new Obj(java.util.Map.of()).with("status", new Text("available")).with("candidate_count", n(2)).with("rows", new Arr(gates)));
    }
    static GovernanceObservationSupplier.Crown crown(PlanningRequest request) {
        var frame = request.before().frame(); List<CrownAuthorityPolicy.Balance> balances = new ArrayList<>();
        for (var currency : CrownAuthorityPolicy.Currency.values()) balances.add(new CrownAuthorityPolicy.Balance(currency, BigInteger.valueOf(1000)));
        var source = new CrownAuthorityPolicy.SourceFrame(frame.identity().nativeRevision(), frame.identity().nativeRevision(), BigInteger.ONE,
                frame.identity().dateRaw(), frame.identity().player(), "1.20.0.4", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
                frame.snapshotId(), frame.revision(), frame.identity().nativeRevision());
        var nativeRead = new CrownAuthorityPolicy.Readback(CrownAuthorityPolicy.READ_SCHEMA, true, true, "crown_authority", "crown_authority_0",
                List.of(new CrownAuthorityPolicy.Candidate("crown_authority_0", true, true, false, "already_active", List.of()),
                        new CrownAuthorityPolicy.Candidate("crown_authority_1", false, true, true, "", List.of(new CrownAuthorityPolicy.Cost(CrownAuthorityPolicy.Currency.GOLD, BigInteger.valueOf(100))))),
                balances, new CrownAuthorityPolicy.TitleSuccessors(BigInteger.valueOf(50), List.of(new CrownAuthorityPolicy.HeldTitle(BigInteger.valueOf(50), true, List.of(BigInteger.valueOf(40))))), source, true, false);
        return new GovernanceObservationSupplier.Crown(nativeRead,
                object(parse(org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec.encodeReadback(nativeRead)), "Crown readback"));
    }
    static final class Supplier implements GovernanceObservationSupplier {
        Durable state; int lifeReads; int councilReads; final List<String> focusTargets = new ArrayList<>();
        boolean missingState; final EnumMap<CouncilSelection.Position, CouncilSelection.Query> councils = new EnumMap<>(CouncilSelection.Position.class);
        Supplier(PlanningRequest request) { state = GovernanceFixtures.durable(request); }
        @Override public Read<Durable> durable(PlanningRequest request) { return missingState ? new Unavailable<>("actual domain slots are absent") : new Known<>(state, List.of(REF)); }
        @Override public Read<Life> lifestyle(PlanningRequest request, String preferred, boolean opening) {
            lifeReads++; focusTargets.add(preferred); return new Known<>(life(request, preferred, opening), List.of(REF));
        }
        @Override public Read<OpeningComparison> openingComparison(PlanningRequest request) {
            var progress = new FocusProgress(BigInteger.ZERO, BigInteger.ZERO, BigInteger.valueOf(100), BigInteger.ZERO, BigInteger.ZERO);
            var comparison = new FirstFocusRequest(Field.of(new FocusObservation("observed", Field.of(true), WEALTH_FOCUS, STEWARDSHIP, "present", Field.of(progress))),
                    Field.of(new FocusObservation("observed", Field.of(true), MARTIAL_FOCUS, MARTIAL, "present", Field.of(progress))),
                    Field.of(new Traits(Field.of("available"), Field.of(List.of("education_martial_4")))), true);
            return new Known<>(new OpeningComparison(comparison, new Obj(java.util.Map.of())), List.of(REF));
        }
        @Override public Read<CouncilSelection.Query> council(PlanningRequest request, CouncilSelection.Position position) {
            councilReads++; return new Known<>(councils.getOrDefault(position, CouncilSelection.decode(request, position, councilRaw(request, position, 10, 9, 8))), List.of(REF));
        }
        @Override public Read<CouncilSelection.Query> coreCouncil(PlanningRequest request) {
            var frame = request.before().frame();
            Obj payload = object(councilRaw(request, CouncilSelection.Position.STEWARD, 10, 12, 12).get("council_composition_candidates"), "payload");
            Obj snapshot = object(payload.get("snapshot"), "snapshot").with("snapshot_id", new Text(frame.snapshotId())).with("public_revision", new IntegerValue(frame.revision()));
            return new Known<>(CouncilSelection.decodeComposition(request, payload.with("snapshot", snapshot)), List.of(REF));
        }
        @Override public Read<CouncilRoot> councilRoot(PlanningRequest request) {
            List<Value> rows = new ArrayList<>();
            for (CouncilSelection.Position position : CouncilSelection.Position.values()) {
                String task = switch (position) {
                    case STEWARD -> "task_collect_taxes";
                    case CHANCELLOR -> "task_domestic_affairs";
                    case CHAPLAIN -> "task_religious_relations";
                };
                rows.add(new Obj(java.util.Map.of()).with("position_key", new Text(position.key())).with("incumbent_character_id", n(20))
                        .with("task_key", new Text(task)).with("task_type", new Text("general")).with("target", Nil.INSTANCE).with("frozen", new Bool(false))
                        .with("progress", new Obj(java.util.Map.of()).with("kind", new Text("infinite")).with("current", Nil.INSTANCE).with("maximum", Nil.INSTANCE)));
            }
            var frame = request.before().frame();
            Obj root = new Obj(java.util.Map.of()).with("status", new Text("available"))
                    .with("snapshot_revision", new IntegerValue(frame.identity().nativeRevision())).with("date_raw", new IntegerValue(frame.identity().dateRaw()))
                    .with("player_character_id", new IntegerValue(frame.identity().player()))
                    .with("council", new Obj(java.util.Map.of()).with("status", new Text("available")).with("positions", new Arr(rows)));
            return new Known<>(new CouncilRoot(List.of(CouncilSelection.Position.values()).stream().map(position -> new Seat(position, Optional.of(BigInteger.valueOf(20)))).toList(),
                    new Obj(java.util.Map.of()).with("campaign_root_context", root)), List.of(REF));
        }
        @Override public Read<GovernanceObservationSupplier.Crown> crown(PlanningRequest request) { return new Known<>(GovernanceFixtures.crown(request), List.of(REF)); }
        @Override public Read<org.xar.ck3.control.wave3.governance.crownretry.CrownRetryCodec.MatchRequest> crownRetry(PlanningRequest request, String lawKey) { return new Unavailable<>("unit fixture has no retry source"); }
        @Override public Read<org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldownCodec.ClockRequest> crownCooldown(PlanningRequest request) { return new Unavailable<>("unit fixture has no clock source"); }
    }
}

