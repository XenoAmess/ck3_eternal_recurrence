package org.xar.ck3.control.application.planning;

import java.time.Clock;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.application.planning.family.FamilyOrdinaryPolicy;
import org.xar.ck3.control.application.planning.family.FamilyPorts;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.PlanningFixtures.*;

final class OrdinaryPlannerProductionAssemblyTest {
    @Test void missingOptionalFamilyReadPreservesPeacefulAdvanceAndLaterStages() {
        var operation = new OperationKey("life-advance");
        var current = request(snapshot(), List.of(), Set.of(operation));
        var chosen = command(current, operation, empty());
        var family = unavailableFamily(familyDocuments(cleanFamilyDomain()));
        var evaluated = optionalFamilyPlanner(chosen, family.policy()).plan(current);
        assertEquals(1, family.reads().get(), planningDiagnostic(evaluated));
        var result = assertInstanceOf(PlanningResult.ActionSelected.class, evaluated, planningDiagnostic(evaluated));
        assertSame(chosen, result.command());
        assertEquals(ActionCodec.bodySha256(chosen), ActionCodec.bodySha256(result.command()));
        var visit = result.trace().visits().stream()
                .filter(value -> value.stage() == PlanningStage.FAMILY_AND_EDUCATION).findFirst().orElseThrow();
        assertEquals(PlanTrace.Outcome.DEFERRED_INPUT, visit.outcome());
        assertNotNull(visit.evidence().orElseThrow().get("family_unavailable"));
        var stages = result.trace().visits().stream().map(PlanTrace.StageVisit::stage).toList();
        assertTrue(stages.containsAll(List.of(PlanningStage.COUNCIL, PlanningStage.FEAST,
                PlanningStage.REALM_MEMBERSHIP_PUBLICATION)));
        assertEquals(1, family.reads().get());
        assertEquals(0, family.prepares().get());
        assertEquals(result, PlanningWire.decodeResult(PlanningWire.encodeResult(result)));
    }

    @Test void missingOptionalFamilyReadNeverGrantsReplayOfAnUnknownOriginalAction() {
        var operation = new OperationKey("life-advance");
        var current = request(snapshot(), List.of(), Set.of(operation));
        var chosen = command(current, operation, empty());
        var family = unavailableFamily(familyDocuments(cleanFamilyDomain()));
        var unknown = withFacts(current, List.of(fact(chosen,
                org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalState.UNKNOWN)));
        var evaluated = optionalFamilyPlanner(chosen, family.policy()).plan(unknown);
        assertEquals(1, family.reads().get(), planningDiagnostic(evaluated));
        var result = assertInstanceOf(PlanningResult.Stopped.class, evaluated, planningDiagnostic(evaluated));
        assertEquals(PlanningResult.StopReason.UNKNOWN_ACTION_UNRESOLVED, result.reason());
        assertEquals(1, family.reads().get());
        assertEquals(0, family.prepares().get());
    }

    @Test void retainedFamilyMaterialDoesNotBecomeACleanOptionalDiscoveryAfterAReadFailure() {
        var operation = new OperationKey("life-advance");
        var current = request(snapshot(), List.of(), Set.of(operation));
        var chosen = command(current, operation, empty());
        // Opaque retained material remains a barrier; this does not qualify its outcome.
        var retained = new OpportunityJson.Obj(Map.of("episode_run_id", new OpportunityJson.Text("episode-1"),
                "status", new OpportunityJson.Text("refused")));
        var domain = cleanFamilyDomain().with("resolved", retained);
        var family = unavailableFamily(familyDocuments(domain));
        var result = assertInstanceOf(PlanningResult.ReadOnlyWait.class,
                optionalFamilyPlanner(chosen, family.policy()).plan(current));
        assertEquals(PlanTrace.Outcome.BLOCKED, result.trace().visits().getLast().outcome());
        assertEquals(PlanningStage.FAMILY_AND_EDUCATION, result.trace().visits().getLast().stage());
        assertEquals(1, family.reads().get());
        assertEquals(0, family.prepares().get());
    }

    @Test void missingCanonicalFamilyDocumentsRetainTheOriginalHardStop() {
        var operation = new OperationKey("life-advance");
        var current = request(snapshot(), List.of(), Set.of(operation));
        var chosen = command(current, operation, empty());
        var family = unavailableFamily(new FamilyPorts.MissingDocuments("original canonical family body is unavailable"));
        var result = assertInstanceOf(PlanningResult.Stopped.class,
                optionalFamilyPlanner(chosen, family.policy()).plan(current));
        assertEquals(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN, result.reason());
        assertEquals(0, family.reads().get());
        assertEquals(0, family.prepares().get());
    }

    /** Software history explicitly reaches the real postwar checkpoint branch; no native result is qualified. */
    private static PlanningRequest postDisbandCheckpointRequest() {
        var disbanded = new OpportunityJson.Obj(Map.of("command", new OpportunityJson.Text("disband-army-1"),
                "ok", new OpportunityJson.Bool(true)));
        return request(snapshot(), List.of(disbanded), Set.of(new OperationKey("save-checkpoint")));
    }

    private static String planningDiagnostic(PlanningResult result) {
        return result.trace().visits().stream().filter(visit -> visit.stage() == PlanningStage.ORDINARY_CORE
                || visit.stage() == PlanningStage.FAMILY_AND_EDUCATION).map(visit -> visit.stage() + ":" + visit.outcome()
                + ":" + visit.reason()).collect(java.util.stream.Collectors.joining("; "));
    }

    private record UnavailableFamily(FamilyOrdinaryPolicy policy,
            java.util.concurrent.atomic.AtomicInteger reads, java.util.concurrent.atomic.AtomicInteger prepares) { }

    private static OpportunityJson.Obj cleanFamilyDomain() {
        return new OpportunityJson.Obj(Map.of("pending", OpportunityJson.Nil.INSTANCE, "resolved", OpportunityJson.Nil.INSTANCE));
    }

    private static FamilyPorts.KnownDocuments familyDocuments(OpportunityJson.Obj family) {
        return new FamilyPorts.KnownDocuments(new FamilyPorts.Documents(family, cleanFamilyDomain(), cleanFamilyDomain(),
                new FamilyPorts.BridgeIdentity(123, NOW.toString()), SOURCE, List.of(SOURCE, SOURCE, SOURCE)));
    }

    /** Real family orchestration consumes an explicit software unavailable read; no native custody is claimed. */
    private static UnavailableFamily unavailableFamily(FamilyPorts.LedgerRead ledger) {
        var reads = new java.util.concurrent.atomic.AtomicInteger();
        var prepares = new java.util.concurrent.atomic.AtomicInteger();
        var projection = new FamilyPorts.ProjectedSource() {
            @Override public FamilyPorts.ProjectedRead read(PlanningRequest request, OpportunityJson.Obj arguments) {
                reads.incrementAndGet();
                return new FamilyPorts.ProjectedRead(arguments,
                        new PlanningReadResult.Unavailable<>("software current-heir native input unavailable", Optional.empty()));
            }
            @Override public OpportunityJson.Obj decode(PlanningReadReceipt receipt) {
                throw new AssertionError("an unavailable read has no receipt to replay");
            }
        };
        var unused = new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
                throw new AssertionError("the actual CURRENT_RELATION projection owns this read");
            }
        };
        var policy = new FamilyOrdinaryPolicy(SOURCE, unused,
                new FamilyPorts.Reads(Map.of(), Map.of(FamilyPorts.Query.CURRENT_RELATION, projection)), request -> ledger,
                (request, operation, arguments, detail) -> {
                    prepares.incrementAndGet(); throw new AssertionError("missing family input cannot prepare a command");
                }, (request, query, arguments, observed) -> {
                    throw new AssertionError("missing family input cannot publish material");
                }, new FamilyPorts.Settings(true, false, false, false, Optional.empty()));
        return new UnavailableFamily(policy, reads, prepares);
    }

    private static OrdinaryPlanner optionalFamilyPlanner(ActionCommand chosen, FamilyOrdinaryPolicy family) {
        var producers = new EnumMap<PlanningStage, OrdinaryPolicy>(PlanningStage.class);
        for (var stage : PlanningStage.values()) producers.put(stage, keep(stage));
        producers.put(PlanningStage.FAMILY_AND_EDUCATION, family);
        var actualCore = core((input, previous) -> new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft(
                "software-independent-advance", "ordinary", "retain the independent ordinary advance",
                OrdinaryPolicy.Kind.ORDINARY, Optional.of(chosen), OrdinaryPolicy.Purpose.DATE_ADVANCE, Optional.empty(),
                new OpportunityJson.Obj(Map.of("selected_step", new OpportunityJson.Text(chosen.operation().value())))),
                "retain the independent ordinary advance"));
        return pipeline(producers, actualCore.core(), new RealmLifecycle(SOURCE)).create(Clock.fixed(NOW, ZoneOffset.UTC));
    }

    @Test void dynamicMilitaryReadUsesTheActualRequestAndSelectionWithoutAnUntypedContractCast() {
        PlanningRequest current = request(snapshot(), List.of(), Set.of());
        var selected = new MilitaryPlanningDecision.Select("one-life-turn-v1", "native_dynamic_forecast",
                "the exact actual native family is required", new OperationKey("fixture-dynamic-read"),
                empty(), OrdinaryPolicy.Purpose.READ_ONLY, new OpportunityJson.Obj(Map.of(
                        "policy", new OpportunityJson.Text("one-life-turn-v1"),
                        "phase", new OpportunityJson.Text("native_dynamic_forecast"),
                        "reason", new OpportunityJson.Text("the exact actual native family is required"),
                        "selected_step", new OpportunityJson.Text("fixture-dynamic-read"))));
        var calls = new java.util.concurrent.atomic.AtomicInteger();
        PlanningReadPort shared = new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
                throw new AssertionError("the typed dispatcher owns the family contract");
            }
        };
        var war = new WarCorePlanner(List.of(), ignored -> { throw new AssertionError("no route collection"); },
                (input, choice) -> { throw new AssertionError("a read cannot become a world command"); },
                shared, (input, choice) -> {
                    assertSame(current, input); assertSame(selected, choice); calls.incrementAndGet();
                    return new PlanningReadResult.Unavailable<OpportunityJson.Obj>("exact family source frame is unavailable", Optional.empty());
                }, (input, previous) -> { throw new AssertionError("no transition continuation"); });
        var result = assertInstanceOf(OrdinaryPolicy.Wait.class, war.decision(current, OrdinaryPolicy.Draft.empty(), selected));
        assertEquals("exact family source frame is unavailable", result.reason());
        assertEquals(1, calls.get());
    }
    @Test void absentSourceNormalPolicyRunsAndRetainsEmptyTraceSource() {
        var request = postDisbandCheckpointRequest();
        var producers = new EnumMap<PlanningStage, OrdinaryPolicy>(PlanningStage.class);
        for (var stage : PlanningStage.values()) producers.put(stage, keep(stage));
        producers.put(PlanningStage.COUNCIL, new OrdinaryPolicy() {
            @Override public PlanningStage stage() { return PlanningStage.COUNCIL; }
            @Override public ExactRef implementationSource() { return null; }
            @Override public Decision evaluate(PlanningRequest request, Draft previous) { return new Keep("absent source normal policy"); }
        });
        var core = core((input, previous) -> new OrdinaryPolicy.Keep("actual registered registry checked"));
        var realm = new RealmLifecycle(SOURCE);
        var complete = pipeline(producers, core.core(), realm);
        var planner = complete.create(Clock.fixed(NOW, ZoneOffset.UTC));
        assertTrue(planner.missingStages().isEmpty());
        var planned = planner.plan(request);
        var selected = assertInstanceOf(PlanningResult.ActionSelected.class, planned, planningDiagnostic(planned));
        assertEquals("save-checkpoint", selected.command().operation().value());
        var visit = selected.trace().visits().stream().filter(v -> v.stage() == PlanningStage.COUNCIL).findFirst().orElseThrow();
        assertEquals(PlanTrace.Outcome.KEPT, visit.outcome());
        assertEquals(Optional.empty(), visit.source());
        assertEquals(selected, PlanningWire.decodeResult(PlanningWire.encodeResult(selected)));
    }

    @Test void absentSourceDeferPolicyRetainsEvidenceAndEmptyTraceSource() {
        var request = postDisbandCheckpointRequest();
        var producers = new EnumMap<PlanningStage, OrdinaryPolicy>(PlanningStage.class);
        for (var stage : PlanningStage.values()) producers.put(stage, keep(stage));
        var evidence = new OpportunityJson.Obj(Map.of("defer_reason", new OpportunityJson.Text("missing optional input")));
        producers.put(PlanningStage.ORDINARY_SWAY, new OrdinaryPolicy() {
            @Override public PlanningStage stage() { return PlanningStage.ORDINARY_SWAY; }
            @Override public ExactRef implementationSource() { return null; }
            @Override public Decision evaluate(PlanningRequest request, Draft previous) { return new Defer("missing optional input", evidence); }
        });
        var core = core((input, previous) -> new OrdinaryPolicy.Keep("actual registered registry checked"));
        var realm = new RealmLifecycle(SOURCE);
        var complete = pipeline(producers, core.core(), realm);
        var planner = complete.create(Clock.fixed(NOW, ZoneOffset.UTC));
        assertTrue(planner.missingStages().isEmpty());
        var planned = planner.plan(request);
        var selected = assertInstanceOf(PlanningResult.ActionSelected.class, planned, planningDiagnostic(planned));
        assertEquals("save-checkpoint", selected.command().operation().value());
        var visit = selected.trace().visits().stream().filter(v -> v.stage() == PlanningStage.ORDINARY_SWAY).findFirst().orElseThrow();
        assertEquals(PlanTrace.Outcome.DEFERRED_INPUT, visit.outcome());
        assertEquals(Optional.empty(), visit.source());
        assertEquals(Optional.of(evidence), visit.evidence());
        assertEquals(selected, PlanningWire.decodeResult(PlanningWire.encodeResult(selected)));
    }

    @Test void completeTypedCompositionRunsTheActualCoreThroughAllOrdinaryConsumers() {
        var request = postDisbandCheckpointRequest();
        var producers = new EnumMap<PlanningStage, OrdinaryPolicy>(PlanningStage.class);
        for (var stage : PlanningStage.values()) producers.put(stage, keep(stage));
        var core = core((input, previous) -> new OrdinaryPolicy.Keep("actual registered registry checked"));
        var realm = new RealmLifecycle(SOURCE);
        var complete = pipeline(producers, core.core(), realm);
        var planner = complete.create(Clock.fixed(NOW, ZoneOffset.UTC));
        assertTrue(planner.missingStages().isEmpty());
        assertEquals(34, complete.policies().size());
        assertSame(realm, complete.policies().getLast());
        var planned = planner.plan(request);
        var selected = assertInstanceOf(PlanningResult.ActionSelected.class, planned, planningDiagnostic(planned));
        assertEquals("save-checkpoint", selected.command().operation().value());
        var stages = selected.trace().visits().stream().map(PlanTrace.StageVisit::stage).toList();
        assertEquals(33, stages.size());
        assertFalse(stages.contains(PlanningStage.OPENING_LIFESTYLE_FOCUS));
        assertTrue(stages.indexOf(PlanningStage.THREE_WAY_WAR_EXIT) < stages.indexOf(PlanningStage.ORDINARY_CORE));
        assertEquals(1, stages.stream().filter(stage -> stage == PlanningStage.M5_WARTIME_OBSERVATION).count());
        assertTrue(stages.indexOf(PlanningStage.M5_WARTIME_OBSERVATION) < stages.indexOf(PlanningStage.COUNCIL));
        assertEquals(List.of(PlanningStage.DEFERRED_SUCCESSION_ROOT, PlanningStage.HOLY_WAR_DEFENDER_OBSERVATION,
                PlanningStage.PREWAR_FORCE_COALITION, PlanningStage.ORDINARY_SWAY,
                PlanningStage.EVENT_MATERIAL_POSTCONDITION, PlanningStage.CAMPAIGN_ADVANCE_CAP,
                PlanningStage.REALM_MEMBERSHIP_PUBLICATION), stages.subList(stages.size() - 7, stages.size()));
        assertEquals(selected, PlanningWire.decodeResult(PlanningWire.encodeResult(selected)));
    }

    @Test void selectedWarExitRunsTheActualM5ObservationBeforeReturningTheSameExactCommand() {
        var operation = new OperationKey("software-native-war-exit");
        var current = wartimeObservationRequest(operation);
        var chosen = command(current, operation, empty());
        var result = assertInstanceOf(PlanningResult.ActionSelected.class, warExitObservationPlanner(chosen).plan(current));
        assertSame(chosen, result.command());
        assertEquals(ActionCodec.bodySha256(chosen), ActionCodec.bodySha256(result.command()));
        var finalPlan = result.trace().finalPlan().orElseThrow();
        assertEquals(OrdinaryPolicy.Kind.WAR_EXIT, finalPlan.kind());
        assertEquals("software-native-war-exit", finalPlan.policy());
        assertEquals("native-offer-selected", finalPlan.phase());
        assertEquals("retain the exact native war offer", finalPlan.reason());
        assertEquals(OrdinaryPolicy.Purpose.WORLD_ACTION, finalPlan.purpose());
        assertTrue(finalPlan.domain().isEmpty());
        assertEquals(new OpportunityJson.Text("construction_observation_unavailable"),
                OpportunityJson.object(finalPlan.detail().get("m5_joint_wartime_observation"), "actual M5 observation").get("status"));
        var risk = OpportunityJson.object(finalPlan.detail().get("m5_nonprimary_war_risk"), "actual typed risk");
        assertEquals(new OpportunityJson.Bool(true), risk.get("read_only"));
        assertEquals(new OpportunityJson.Bool(false), risk.get("action_authorized"));
        assertEquals(new OpportunityJson.Bool(false), risk.get("political_and_territorial_consequences_assessed"));
        assertInstanceOf(org.xar.ck3.control.wave3.planning.participatingwar.ParticipatingWarThreats.UnavailableNonPrimaryRisk.class,
                org.xar.ck3.control.wave3.planning.participatingwar.ParticipatingWarThreatsCodec.decodeNonPrimaryRisk(OpportunityJson.encode(risk)));
        var visits = result.trace().visits().stream().map(PlanTrace.StageVisit::stage).toList();
        assertFalse(visits.contains(PlanningStage.ORDINARY_CORE), "the native war-exit priority stays intact");
        assertEquals(1, visits.stream().filter(stage -> stage == PlanningStage.M5_WARTIME_OBSERVATION).count());
        assertTrue(visits.indexOf(PlanningStage.M5_WARTIME_OBSERVATION) < visits.indexOf(PlanningStage.REALM_MEMBERSHIP_PUBLICATION));
        assertEquals(result, PlanningWire.decodeResult(PlanningWire.encodeResult(result)));
    }

    @Test void earlyWarExitObservationDoesNotGrantReplayOfAnUnresolvedAuthoritativeAction() {
        var operation = new OperationKey("software-native-war-exit");
        var current = wartimeObservationRequest(operation);
        var chosen = command(current, operation, empty());
        var recorded = withFacts(current, List.of(fact(chosen,
                org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalState.UNKNOWN)));
        var result = assertInstanceOf(PlanningResult.Stopped.class, warExitObservationPlanner(chosen).plan(recorded));
        assertEquals(PlanningResult.StopReason.UNKNOWN_ACTION_UNRESOLVED, result.reason());
        assertNotNull(result.trace().finalPlan().orElseThrow().detail().get("m5_nonprimary_war_risk"));
        assertEquals(result, PlanningWire.decodeResult(PlanningWire.encodeResult(result)));
    }

    private static PlanningRequest wartimeObservationRequest(OperationKey operation) {
        var war = new OpportunityJson.Obj(Map.of("war_id", integer(1)));
        var observed = snapshot().with("active_wars", new OpportunityJson.Arr(List.of(war)));
        return request(observed, List.of(), Set.of(operation));
    }

    /** The exit selection is a software fixture; the scheduler and M5 policy are the actual shared producers. */
    private static OrdinaryPlanner warExitObservationPlanner(ActionCommand chosen) {
        var producers = new EnumMap<PlanningStage, OrdinaryPolicy>(PlanningStage.class);
        for (var stage : PlanningStage.values()) producers.put(stage, keep(stage));
        producers.put(PlanningStage.THREE_WAY_WAR_EXIT, new OrdinaryPolicy() {
            @Override public PlanningStage stage() { return PlanningStage.THREE_WAY_WAR_EXIT; }
            @Override public ExactRef implementationSource() { return SOURCE; }
            @Override public Decision evaluate(PlanningRequest request, Draft previous) {
                return new Replace(new Draft("software-native-war-exit", "native-offer-selected", "retain the exact native war offer",
                        Kind.WAR_EXIT, Optional.of(chosen), Purpose.WORLD_ACTION, Optional.empty(), empty()), "native war exit selected");
            }
        });
        producers.put(PlanningStage.M5_WARTIME_OBSERVATION, new M5WartimeObservationPolicy(SOURCE, true));
        var actualCore = core((input, previous) -> { throw new AssertionError("a selected native war exit retains its priority"); });
        return pipeline(producers, actualCore.core(), new RealmLifecycle(SOURCE)).create(Clock.fixed(NOW, ZoneOffset.UTC));
    }

    @Test void aMisplacedOrMissingProducerCannotBeConvertedIntoCompleteProductionComposition() {
        var producers = new EnumMap<PlanningStage, OrdinaryPolicy>(PlanningStage.class);
        for (var stage : PlanningStage.values()) producers.put(stage, keep(stage));
        var core = core((input, previous) -> new OrdinaryPolicy.Keep("registry checked"));
        var realm = new RealmLifecycle(SOURCE);
        producers.put(PlanningStage.CONSTRUCTION, keep(PlanningStage.FAMILY_AND_EDUCATION));
        assertThrows(IllegalArgumentException.class, () -> pipeline(producers, core.core(), realm));
        producers.put(PlanningStage.CONSTRUCTION, null);
        assertThrows(NullPointerException.class, () -> pipeline(producers, core.core(), realm));
    }

    @Test void recognizedTransitionReentersTheSameActualCoreAndCannotRunDuringAssembly() {
        var history = List.of(new OpportunityJson.Obj(Map.of("command", new OpportunityJson.Text("first"))),
                new OpportunityJson.Obj(Map.of("command", new OpportunityJson.Text("second"))));
        var original = request(snapshot(), history, Set.of());
        var trimmed = original.withHistory(List.of(history.getLast()));
        var assembly = OrdinaryCorePolicy.assemble(SOURCE, continuation -> {
            assertThrows(IllegalArgumentException.class, () -> continuation.plan(trimmed, OrdinaryPolicy.Draft.empty()));
            return war(List.of(), continuation);
        }, (input, previous) -> new OrdinaryPolicy.Wait("actual core history rows=" + input.observations().history().size()),
                (input, previous) -> { throw new AssertionError("registry wait must retain priority"); },
                (input, previous) -> { throw new AssertionError("registry wait must retain priority"); },
                (input, previous) -> { throw new AssertionError("registry wait must retain priority"); },
                (input, operation, arguments, plan, purpose, domain) -> { throw new AssertionError("replan does not submit"); },
                step -> step.equals("life-advance"));
        var outcome = assembly.war().decision(original, OrdinaryPolicy.Draft.empty(),
                new MilitaryPlanningDecision.Replan(trimmed, empty()));
        assertEquals("actual core history rows=1", assertInstanceOf(OrdinaryPolicy.Wait.class, outcome).reason());
        assertThrows(IllegalArgumentException.class, () -> assembly.war().decision(original,
                OrdinaryPolicy.Draft.empty(), new MilitaryPlanningDecision.Replan(original, empty())));
    }

    @Test void fullNativeSummarySurvivesTheActualLargeSnapshotSplitRecoveryGuardAndResultRoundTrip() {
        var warRow = new OpportunityJson.Obj(Map.of("war_id", integer(1),
                "allied_armies", new OpportunityJson.Arr(List.of()), "enemy_armies", new OpportunityJson.Arr(List.of())));
        var snapshot = snapshot().with("full_native_payload", new OpportunityJson.Text("x".repeat(150_000)))
                .with("active_wars", new OpportunityJson.Arr(List.of(warRow)))
                .with("player_armies", new OpportunityJson.Arr(List.of(army(0), army(7), army(9))));
        var split = new OpportunityJson.Obj(Map.of("command", new OpportunityJson.Text("split-army-half-0"),
                "ok", new OpportunityJson.Bool(true), "result", new OpportunityJson.Obj(Map.of("war_action",
                new OpportunityJson.Obj(Map.of("status", new OpportunityJson.Text("split_submitted"),
                        "source_army_id", integer(0), "submitted_date_raw", integer(24000),
                        "player_army_ids_before", new OpportunityJson.Arr(List.of(integer(0)))))))));
        var request = request(snapshot, List.of(split), Set.of());
        var summary = new OpportunityJson.Arr(List.of(warRow.with("native_end_conditions",
                new OpportunityJson.Obj(Map.of("can_enforce", new OpportunityJson.Bool(false),
                        "exact_native_evidence", new OpportunityJson.Text("e".repeat(150_000)))))
                .with("explicit_null", OpportunityJson.Nil.INSTANCE)));
        var leaves = new ArrayList<WarCorePlanner.Leaf>();
        for (var boundary : WarCorePlanner.Boundary.values()) leaves.add(new WarCorePlanner.Leaf(boundary, SOURCE,
                (input, previous) -> new MilitaryPlanningDecision.Keep(boundary == WarCorePlanner.Boundary.WAR_SUMMARY_AND_ASSAULT_LIFECYCLE
                        ? new OpportunityJson.Obj(Map.of("active_wars", summary)) : empty())));
        var result = assertInstanceOf(OrdinaryPolicy.Replace.class,
                war(leaves, (input, previous) -> { throw new AssertionError("split hold must not replan"); })
                        .evaluate(request, OrdinaryPolicy.Draft.empty()));
        assertEquals("native_war_merge_recovery_blocked", result.draft().phase());
        assertSame(summary, result.draft().detail().get("active_wars"));
        var waiting = new PlanningResult.ReadOnlyWait(request.before(), result.reason(),
                new PlanTrace(request.before(), List.of(), Optional.of(result.draft())));
        assertEquals(waiting, PlanningWire.decodeResult(PlanningWire.encodeResult(waiting)));
    }

    private static OrdinaryCorePolicy.Assembly core(OrdinaryCorePolicy.CoreProducer registry) {
        return OrdinaryCorePolicy.assemble(SOURCE, continuation -> {
            var leaves = new ArrayList<WarCorePlanner.Leaf>();
            for (var boundary : WarCorePlanner.Boundary.values())
                leaves.add(new WarCorePlanner.Leaf(boundary, SOURCE, (input, previous) -> new MilitaryPlanningDecision.Keep(empty())));
            return war(leaves, continuation);
        }, registry, (input, previous) -> new OrdinaryPolicy.Keep("council checked"),
                (input, previous) -> new OrdinaryPolicy.Keep("marriage checked"),
                (input, previous) -> new OrdinaryPolicy.Keep("entry checked"),
                (input, operation, arguments, plan, purpose, domain) -> new OrdinaryCorePolicy.Prepared(command(input, operation, arguments)),
                step -> step.equals("life-advance"));
    }

    private static WarCorePlanner war(List<WarCorePlanner.Leaf> leaves, WarCorePlanner.CoreContinuation continuation) {
        PlanningReadPort reads = new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
                throw new AssertionError("no query in these regression paths");
            }
        };
        return new WarCorePlanner(leaves,
                input -> new WarCorePlanner.KnownTactics(input.before(), new WarCorePlanner.RouteTactics(Set.of(), Set.of())),
                (input, selection) -> { throw new AssertionError("no world submit through military fixture"); },
                reads, (input, selection) -> { throw new AssertionError("no readonly query in this production regression path"); }, continuation);
    }

    private static OrdinaryPolicy keep(PlanningStage stage) {
        return new OrdinaryPolicy() {
            @Override public PlanningStage stage() { return stage; }
            @Override public ExactRef implementationSource() { return SOURCE; }
            @Override public Decision evaluate(PlanningRequest request, Draft previous) { return new Keep("fixture retains the actual core command"); }
        };
    }
    private static OpportunityJson.Obj army(int id) {
        return new OpportunityJson.Obj(Map.of("army_id", integer(id), "controllable", new OpportunityJson.Bool(true),
                "owner_character_id", integer(29829), "current_province_id", integer(20),
                "army_state", new OpportunityJson.Text("idle")));
    }
    private static OpportunityJson.Obj empty() { return new OpportunityJson.Obj(Map.of()); }

    private static OrdinaryPlanningPipeline pipeline(Map<PlanningStage, OrdinaryPolicy> policies,
            OrdinaryCorePolicy core, RealmLifecycle realm) {
        return new OrdinaryPlanningPipeline(policies.get(PlanningStage.SUCCESSION_PREFLIGHT),
                policies.get(PlanningStage.PENDING_MATERIAL_PUBLICATION), policies.get(PlanningStage.TERMINAL_AND_FOREGROUND_WINDOWS),
                policies.get(PlanningStage.OPENING_LIFESTYLE_FOCUS), core, policies.get(PlanningStage.THREE_WAY_WAR_EXIT),
                policies.get(PlanningStage.EVENT_AND_INTERACTION_CONTINUATION), policies.get(PlanningStage.WAR_RENDEZVOUS),
                policies.get(PlanningStage.SIEGE_AND_BATTLE_FORECAST), policies.get(PlanningStage.ROUTE_ORIGIN_EXPOSURE),
                policies.get(PlanningStage.ACTIVE_COMBAT_AND_DATE_GUARDS), policies.get(PlanningStage.ORDINARY_RETREAT),
                policies.get(PlanningStage.WAR_MERCENARY_CURRENT_CASH), policies.get(PlanningStage.PRISONER_RELEASE_DISCOVERY),
                policies.get(PlanningStage.HOLY_ORDER_REINFORCEMENT), policies.get(PlanningStage.COMMANDER_QUALITY),
                policies.get(PlanningStage.M5_JOINT_PEACETIME), policies.get(PlanningStage.LIFESTYLE),
                policies.get(PlanningStage.FACTION_GIFT), policies.get(PlanningStage.CONSTRUCTION),
                policies.get(PlanningStage.FAMILY_AND_EDUCATION), policies.get(PlanningStage.PRISONER_RANSOM),
                policies.get(PlanningStage.PRISONER_RELEASE), policies.get(PlanningStage.M5_WARTIME_OBSERVATION),
                policies.get(PlanningStage.COUNCIL), policies.get(PlanningStage.CROWN_AUTHORITY), policies.get(PlanningStage.FEAST),
                policies.get(PlanningStage.DEFERRED_SUCCESSION_ROOT), policies.get(PlanningStage.HOLY_WAR_DEFENDER_OBSERVATION),
                policies.get(PlanningStage.PREWAR_FORCE_COALITION), policies.get(PlanningStage.ORDINARY_SWAY),
                policies.get(PlanningStage.EVENT_MATERIAL_POSTCONDITION), policies.get(PlanningStage.CAMPAIGN_ADVANCE_CAP), realm);
    }

    /** The remaining stages are explicit software fixtures, never a substitute for actual Root's34-stage installation. */
    private static OrdinaryPlanner recordedActionPlanner(OperationKey operation) {
        var producers=new EnumMap<PlanningStage,OrdinaryPolicy>(PlanningStage.class);
        for(var stage:PlanningStage.values())producers.put(stage,keep(stage));
        var actualCore=core((input,previous)->new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft("software-recorded-action","ordinary",
                "exercise the actual final admission consumer",OrdinaryPolicy.Kind.ORDINARY,Optional.of(command(input,operation,empty())),
                OrdinaryPolicy.Purpose.WORLD_ACTION,Optional.of(org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain.marriage),
                new OpportunityJson.Obj(Map.of("policy",new OpportunityJson.Text("software-recorded-action"),
                        "phase",new OpportunityJson.Text("ordinary"),"reason",new OpportunityJson.Text("exercise the actual final admission consumer"),
                        "selected_step",new OpportunityJson.Text(operation.value())))),"exercise the actual final admission consumer"));
        return pipeline(producers,actualCore.core(),new RealmLifecycle(SOURCE)).create(Clock.fixed(NOW,ZoneOffset.UTC));
    }
    private static PlanningRequest withFacts(PlanningRequest original,List<org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalFact> facts) {
        var old=original.observations();
        var observation=new PlanningObservation(old.snapshot(),old.history(),old.actionSteps(),old.bridgeCapabilities(),old.battleSpeedReadiness(),
                facts,old.campaignGoal(),old.crossRunPlan(),old.initialLifestyleFocusRequired());
        return new PlanningRequest(original.before(),original.source(),original.sessionId(),original.deadline(),observation);
    }
    private static org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalFact fact(ActionCommand actual,
            org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalState state) {
        return new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalFact(actual.actionId(),ActionCodec.bodySha256(actual),actual.before(),state,
                org.xar.ck3.control.g2.planning.ProposalLifecycle.UnknownScope.GLOBAL,
                org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain.marriage,actual.claims(),SOURCE);
    }
    @Test void everyRecordedTerminalActionWaitsWithoutAnUnknownLabelOrAnotherSubmission() {
        var operation=new OperationKey("software-family-command");var base=request(snapshot(),List.of(),Set.of(operation));
        var selected=assertInstanceOf(PlanningResult.ActionSelected.class,recordedActionPlanner(operation).plan(base)).command();
        for(var terminal:List.of(org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalState.SEND_CONFIRMED,
                org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalState.APPLIED_CONFIRMED,
                org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalState.REJECTED_CONFIRMED,
                org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalState.TERMINAL_WITHOUT_EFFECT)) {
            var current=withFacts(base,List.of(fact(selected,terminal)));
            assertEquals(current,PlanningWire.decodeRequest(PlanningWire.encodeRequest(current)),"current fact-v2 request round trip");
            var result=assertInstanceOf(PlanningResult.ReadOnlyWait.class,recordedActionPlanner(operation).plan(current));
            assertTrue(result.reason().contains(terminal.name()));
            assertEquals(result,PlanningWire.decodeResult(PlanningWire.encodeResult(result)));
        }
    }
    @Test void recordedUnknownAndAckStillBlockAndTerminalStateNeverWeakensExactBodyCustody() {
        var operation=new OperationKey("software-family-command");var base=request(snapshot(),List.of(),Set.of(operation));
        var selected=assertInstanceOf(PlanningResult.ActionSelected.class,recordedActionPlanner(operation).plan(base)).command();
        for(var unresolved:List.of(org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalState.UNKNOWN,
                org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalState.ACK_RECEIVED)) {
            var result=assertInstanceOf(PlanningResult.Stopped.class,recordedActionPlanner(operation).plan(withFacts(base,List.of(fact(selected,unresolved)))));
            assertEquals(PlanningResult.StopReason.UNKNOWN_ACTION_UNRESOLVED,result.reason());
        }
        var original=fact(selected,org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalState.SEND_CONFIRMED);
        var changed=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalFact(original.actionId(),"b".repeat(64),original.origin(),original.state(),
                original.scope(),original.domain(),original.affectedClaims(),original.originalEvidenceRef());
        assertThrows(IllegalArgumentException.class,()->recordedActionPlanner(operation).plan(withFacts(base,List.of(changed))));
    }
    @Test void aDifferentTerminalFamilySendDoesNotBecomeANewGlobalUnknown() {
        var operation=new OperationKey("software-family-command");var base=request(snapshot(),List.of(),Set.of(operation));
        var selected=assertInstanceOf(PlanningResult.ActionSelected.class,recordedActionPlanner(operation).plan(base)).command();
        var original=new ActionCommand("previous-recorded-family",selected.before(),selected.source(),selected.sessionId(),selected.operation(),
                selected.arguments(),selected.expected(),selected.claims(),selected.deadline());
        var terminal=withFacts(base,List.of(fact(original,org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalState.SEND_CONFIRMED)));
        assertInstanceOf(PlanningResult.ActionSelected.class,recordedActionPlanner(operation).plan(terminal));
        var unknown=withFacts(base,List.of(fact(original,org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalState.UNKNOWN)));
        assertEquals(PlanningResult.StopReason.UNKNOWN_ACTION_UNRESOLVED,
                assertInstanceOf(PlanningResult.Stopped.class,recordedActionPlanner(operation).plan(unknown)).reason());
    }
}
