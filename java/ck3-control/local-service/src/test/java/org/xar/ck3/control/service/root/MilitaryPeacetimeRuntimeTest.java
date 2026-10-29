package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;

import java.io.ByteArrayInputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.family.FamilyOrdinaryPolicy;
import org.xar.ck3.control.application.planning.family.FamilyPorts;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.military.M5PeacetimePolicy;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel;
import org.xar.ck3.control.wave3.planning.m5peacetimeassembly.PeacetimeAssembly;
import org.xar.ck3.control.wave3.planning.m5peacetimeassembly.PeacetimeAssemblyCodec;

/** Original source fixtures -> the same runtime faction capture -> real assembly/intake/selector/M5 policy.
 * Session/Native custody and the two final owning-consumer endpoints are explicit software fixtures.
 * No ManagedGame is constructed, no action is submitted, and no live capability is claimed. */
final class MilitaryPeacetimeRuntimeTest {
    private static final String SOURCE_SHA = "a".repeat(64);
    private static final String BUILDING = "building:501:701:1";
    private static final String GIFT = "diplomacy:faction-gift:801:41003";

    @Test void knownEmptyRootDoesNotReadGiftOrAlertsAndRetainsIndependentBuilding() throws Exception {
        Scenario scenario = new Scenario("known-empty-faction", true, false);
        Run run = scenario.run();
        assertEquals(List.of(FinanceReadContracts.Query.ROOT), scenario.reads);
        assertEquals(PeacetimeAssembly.FactionStatus.KNOWN_EMPTY, scenario.captured.status());
        assertEquals(new Text("known_empty"), run.collection().get("producer_faction_status"));
        assertEquals(BUILDING, run.selected());
        assertEquals(1, scenario.buildingRoutes);
        assertEquals(0, scenario.giftRoutes);
        assertFalse(run.plan().phase().equals("m5_joint_query_only_red"));
    }

    @Test void knownEmptyRootAndNoBuildingKeepTheLegalOrdinaryAdvance() throws Exception {
        Scenario scenario = new Scenario("empty-domains", true, false);
        Run run = scenario.run();
        assertEquals(List.of(FinanceReadContracts.Query.ROOT), scenario.reads);
        assertNull(run.selected());
        assertEquals(new Text("life-advance"), run.plan().detail().get("selected_step"));
        assertEquals(new Text("no_complete_feasible_proposal"), run.collection().get("status"));
        assertEquals(0, scenario.buildingRoutes + scenario.giftRoutes);
    }

    @Test void realDangerousNativeRowBeatsPositiveIncomeBuildingThroughTheSamePolicy() throws Exception {
        Scenario scenario = new Scenario("two-domains", false, true);
        Run run = scenario.run();
        assertEquals(List.of(FinanceReadContracts.Query.ROOT, FinanceReadContracts.Query.FACTION_GIFT,
                FinanceReadContracts.Query.FACTION_ALERTS), scenario.reads);
        assertEquals(GIFT, run.selected());
        assertEquals(new Text("observed"), run.threat().get("status"));
        assertEquals(new Bool(true), run.threat().get("dangerous_response_ready"));
        assertEquals(new Bool(false), run.threat().get("same_frame_history_reused"));
        assertEquals(0, scenario.buildingRoutes);
        assertEquals(1, scenario.giftRoutes);
        assertEquals(new Text("save-checkpoint"), run.plan().detail().get("selected_step"),
                "the actual M5 route still defers submission to the independent gift owner");
        assertEquals(new Bool(false), run.plan().detail().get("m5_joint_formal_action_ready"));
        assertEquals(2, OpportunityJson.array(run.collection().get("collected_candidate_ids"), "complete candidates").size());
    }

    @Test void knownNonDangerousNativeRowRemainsObservedAndBuildingKeepsItsExistingPreference() throws Exception {
        Scenario scenario = new Scenario("two-domains", false, false);
        Run run = scenario.run();
        assertEquals(BUILDING, run.selected());
        assertEquals(new Text("observed"), run.threat().get("status"));
        assertEquals(new Bool(false), run.threat().get("dangerous_response_ready"));
        assertEquals(new Text("non_peasant_discontent_not_increasing"),
                object(run.threat().get("native_row")).get("danger_reason"));
        assertEquals(1, scenario.buildingRoutes);
        assertEquals(0, scenario.giftRoutes);
    }

    @Test void unavailableAlertPreservesBothLegalCandidatesAndDoesNotInventAWatchObservation() throws Exception {
        Scenario scenario = new Scenario("two-domains", false, false);
        scenario.alertFailure = true;
        Run run = scenario.run();
        assertEquals(BUILDING, run.selected());
        assertEquals(new Text("unavailable"), run.threat().get("status"));
        assertFalse(run.threat().members().containsKey("native_row"));
        assertEquals(2, OpportunityJson.array(run.collection().get("collected_candidate_ids"), "complete candidates").size());
        assertFalse(run.plan().phase().equals("m5_joint_query_only_red"));
    }

    @Test void completeUnavailableNativeFrameStaysUnknownAndKeepsTheIndependentCandidates() throws Exception {
        Scenario scenario = new Scenario("two-domains", false, false);
        Obj unavailable;
        try (var input = MilitaryPeacetimeRuntimeTest.class.getResourceAsStream("/factionalerts/original-producer-golden.json")) {
            assertNotNull(input);
            unavailable = object(object(object(OpportunityJson.parse(input.readNBytes(131073))).get("bases")).get("unavailable"));
        }
        Obj observed = object(scenario.alert.get("player_faction_alerts"));
        unavailable = unavailable.with("snapshot_revision", observed.get("snapshot_revision"))
                .with("date_raw", observed.get("date_raw")).with("provenance", observed.get("provenance"));
        scenario.alert = scenario.alert.with("status", new Text("unavailable"))
                .with("player_faction_alerts", unavailable).with("player_faction_alerts_ready", new Bool(false));
        Run run = scenario.run();
        assertEquals(BUILDING, run.selected());
        assertEquals(new Text("unavailable"), run.threat().get("status"));
        assertEquals(new Text("same_frame_stock_threat_not_observed"), run.threat().get("reason"));
        assertFalse(run.threat().members().containsKey("native_row"));
        assertEquals(2, OpportunityJson.array(run.collection().get("collected_candidate_ids"), "complete candidates").size());
    }

    @Test void sameFrameHistoryReusesTheCompleteActualAlertWithoutAnotherRead() throws Exception {
        Scenario scenario = new Scenario("two-domains", false, true);
        Obj history = obj("command", new Text(FactionAlertModel.STEP), "ok", new Bool(true), "result", scenario.alert);
        scenario.request = request(scenario.original.initialSnapshot(), List.of(scenario.rootHistory(), history));
        Run run = scenario.run();
        assertEquals(GIFT, run.selected());
        assertEquals(new Bool(true), run.threat().get("same_frame_history_reused"));
        assertEquals(List.of(FinanceReadContracts.Query.ROOT, FinanceReadContracts.Query.FACTION_GIFT), scenario.reads);
    }

    @Test void staleHistoryTriggersFreshReadAndWrongActorCannotBecomeObservedDanger() throws Exception {
        Scenario scenario = new Scenario("two-domains", false, true);
        Obj stale = scenario.alert.with("player_faction_alerts", object(scenario.alert.get("player_faction_alerts")).with("snapshot_revision", n(16)));
        scenario.request = request(scenario.original.initialSnapshot(), List.of(scenario.rootHistory(),
                obj("command", new Text(FactionAlertModel.STEP), "ok", new Bool(true), "result", stale)));
        assertEquals(GIFT, scenario.run().selected());
        assertEquals(1, scenario.reads.stream().filter(FinanceReadContracts.Query.FACTION_ALERTS::equals).count());
        Scenario wrong = new Scenario("two-domains", false, true);
        wrong.alert = wrong.alert.with("player_faction_alerts",
                object(wrong.alert.get("player_faction_alerts")).with("player_character_id", n(999)));
        Run result = wrong.run();
        assertEquals(BUILDING, result.selected());
        assertEquals(new Text("unavailable"), result.threat().get("status"));
        assertFalse(result.threat().members().containsKey("native_row"));
    }

    @Test void malformedOrStaleRootCannotBecomeKnownEmptyOrTriggerPrivatePreview() throws Exception {
        for (Value count : List.<Value>of(new Bool(false), Nil.INSTANCE, n(-1),
                OpportunityJson.parse("0.0".getBytes(StandardCharsets.UTF_8)))) {
            Scenario scenario = new Scenario("known-empty-faction", true, false);
            Obj root = object(scenario.root.get("campaign_root_context"));
            scenario.root = scenario.root.with("campaign_root_context", root.with("player_targeting_faction_count", count));
            assertThrows(IllegalArgumentException.class, () -> MilitaryPeacetimeRuntime.captureFaction(
                    scenario.request, true, scenario::read));
            assertEquals(List.of(FinanceReadContracts.Query.ROOT), scenario.reads);
        }
        Scenario stale = new Scenario("known-empty-faction", true, false);
        stale.root = stale.root.with("campaign_root_context",
                object(stale.root.get("campaign_root_context")).with("snapshot_revision", n(16)));
        assertThrows(IllegalArgumentException.class,
                () -> MilitaryPeacetimeRuntime.captureFaction(stale.request, true, stale::read));
        assertEquals(List.of(FinanceReadContracts.Query.ROOT), stale.reads);
    }

    private record Run(OrdinaryPolicy.Draft plan, PeacetimeAssembly.Faction captured) {
        Obj collection() { return object(plan.detail().get("m5_joint_query_only")); }
        Obj threat() { return object(captured.originalCandidate().get("stock_threat_response")); }
        String selected() {
            Value value = object(collection().get("dispatch")).get("selected_candidate_id");
            return value == Nil.INSTANCE ? null : OpportunityJson.text(value, "actual selected candidate");
        }
    }

    private static final class Scenario {
        final PeacetimeAssembly.Inputs original;
        final List<FinanceReadContracts.Query> reads = new ArrayList<>();
        PlanningRequest request;
        Obj root, alert;
        final Obj preview;
        boolean alertFailure;
        PeacetimeAssembly.Faction captured;
        int buildingRoutes, giftRoutes;

        Scenario(String sample, boolean emptyRoot, boolean dangerous) throws Exception {
            original = PeacetimeAssemblyCodec.decodeHistoricalV1(OpportunityJson.encode(originalInput(sample)));
            Obj snapshot = original.initialSnapshot();
            Obj rawRoot = object(object(OpportunityJson.array(snapshot.get("native_command_history"), "root history").getFirst()).get("result"));
            root = rawRoot.with("campaign_root_context",
                    object(rawRoot.get("campaign_root_context")).with("player_targeting_faction_count", n(emptyRoot ? 0 : 1)));
            request = request(snapshot, List.of(rootHistory()));
            preview = preview(snapshot);
            alert = alert(snapshot, dangerous);
        }

        Obj rootHistory() { return obj("command", new Text("query-campaign-root-context-v1"), "ok", new Bool(true), "result", root); }

        Obj read(FinanceReadContracts.Query query) {
            reads.add(query);
            return switch (query) {
                case ROOT -> root;
                case FACTION_GIFT -> preview;
                case FACTION_ALERTS -> {
                    if (alertFailure) throw new IllegalStateException("explicit software observer unavailable");
                    yield alert;
                }
                default -> throw new AssertionError("unrelated query is forbidden: " + query);
            };
        }

        Run run() {
            var sources = new M5PeacetimePolicy.SourceCollector() {
                @Override public M5PeacetimePolicy.Prior prior(PlanningRequest actual, OrdinaryPolicy.Draft baseline) {
                    assertSame(request, actual);
                    return new M5PeacetimePolicy.Prior(original.before(), original.constructionRelease());
                }
                @Override public M5PeacetimePolicy.Capture capture(PlanningRequest actual, OrdinaryPolicy.Draft baseline,
                        M5PeacetimePolicy.Prior prior) {
                    assertSame(request, actual);
                    captured = MilitaryPeacetimeRuntime.captureFaction(actual, true, Scenario.this::read);
                    var inputs = new PeacetimeAssembly.Inputs(original.scope(), actual.observations().snapshot(), baseline.detail(),
                            prior.ledgers(), original.after(), prior.constructionRelease(), original.construction(), captured, original.family());
                    PeacetimeAssembly.compose(inputs);
                    return new M5PeacetimePolicy.Capture(inputs, new ConstructionEconomyModel.NoCashObservation(), Optional.empty());
                }
            };
            OrdinaryPolicy construction = owner(PlanningStage.CONSTRUCTION, (actual, baseline) -> {
                buildingRoutes++;
                return replacement(baseline, baseline.detail().with("construction_private_query", original.construction().originalQuery()));
            });
            OrdinaryPolicy gift = owner(PlanningStage.FACTION_GIFT, (actual, baseline) -> {
                giftRoutes++;
                return replacement(baseline, baseline.detail().with("selected_step", new Text("save-checkpoint"))
                        .with("faction_gift_private_candidate_v1", captured.originalCandidate()));
            });
            var consumers = new M5PeacetimePolicy.Consumers(construction, gift, disabledFamily(request.source().sourceRef()));
            var policy = new M5PeacetimePolicy(request.source().sourceRef(), new M5PeacetimePolicy.Options(true, true, false),
                    sources, consumers, (r, p, d) -> { throw new AssertionError("root is already observed on this fixture frame"); });
            Obj baseline = original.baselinePlan().with("reason", new Text("original software peaceful baseline"));
            var draft = new OrdinaryPolicy.Draft("one-life-turn-v1", "peace_growth", "original software peaceful baseline",
                    OrdinaryPolicy.Kind.ORDINARY, Optional.empty(), OrdinaryPolicy.Purpose.DATE_ADVANCE, Optional.empty(), baseline);
            var outcome = policy.evaluate(request, draft);
            var changed = outcome instanceof OrdinaryPolicy.Replace replace ? replace.draft()
                    : assertInstanceOf(OrdinaryPolicy.Annotate.class, outcome).retained();
            assertNotNull(captured);
            assertTrue(changed.command().isEmpty(), "software owning endpoints do not mint action authority");
            return new Run(changed, captured);
        }
    }

    @FunctionalInterface private interface OwnerDecision {
        OrdinaryPolicy.Decision evaluate(PlanningRequest request, OrdinaryPolicy.Draft baseline);
    }
    private static OrdinaryPolicy owner(PlanningStage stage, OwnerDecision result) {
        return new OrdinaryPolicy() {
            @Override public PlanningStage stage() { return stage; }
            @Override public ExactRef implementationSource() { return source().sourceRef(); }
            @Override public Decision evaluate(PlanningRequest request, Draft baseline) { return result.evaluate(request, baseline); }
        };
    }
    private static OrdinaryPolicy.Decision replacement(OrdinaryPolicy.Draft previous, Obj detail) {
        return new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft(previous.policy(), previous.phase(), previous.reason(),
                previous.kind(), Optional.empty(), previous.purpose(), previous.domain(), detail), "software owning consumer endpoint");
    }
    private static FamilyOrdinaryPolicy disabledFamily(ExactRef source) {
        return new FamilyOrdinaryPolicy(source, new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
                throw new AssertionError("disabled family cannot read");
            }
        }, new FamilyPorts.Reads(Map.of(), Map.of()),
                request -> { throw new AssertionError("disabled family cannot load"); },
                (request, operation, arguments, plan) -> { throw new AssertionError("disabled family cannot prepare"); },
                (request, query, arguments, observed) -> { throw new AssertionError("disabled family cannot consume"); },
                new FamilyPorts.Settings(false, false, false, false, Optional.empty()));
    }

    private static PlanningRequest request(Obj snapshot, List<Obj> history) {
        var source = source();
        Obj actor = object(snapshot.get("played_character"));
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(
                OpportunityJson.integer(actor.get("character_id"), "actor"), OpportunityJson.integer(snapshot.get("native_revision"), "native revision"),
                OpportunityJson.integer(snapshot.get("date_raw"), "date")), OpportunityJson.text(snapshot.get("snapshot_id"), "snapshot"),
                OpportunityJson.integer(snapshot.get("revision"), "public revision"), OpportunityJson.text(snapshot.get("episode_run_id"), "episode"));
        return new PlanningRequest(new ObservationIdentity(source.machineId(), new GameGeneration(123, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1),
                source, "software-m5-runtime-session", Instant.parse("2026-10-27T12:00:00Z"),
                new PlanningObservation(snapshot, history, Set.of(new OperationKey("life-advance")),
                        Set.of("game.query.player-faction-alerts-v1"), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false));
    }
    private static G2Source source() {
        return new G2Source("software-m5-runtime-no-game", "2026-10-27T00:00:00Z", "1.20.0.4",
                new ExactRef("software-m5-runtime-original-source", 1, SOURCE_SHA));
    }

    private static Obj originalInput(String name) throws Exception {
        try (var stream = MilitaryPeacetimeRuntimeTest.class.getResourceAsStream("/m5peacetimeassembly/producer-golden-v1.json.gz")) {
            assertNotNull(stream, "existing original thirteen-case producer corpus is required");
            byte[] compressed = stream.readNBytes(65537); assertTrue(compressed.length <= 65536);
            assertEquals("61374f70cb7398c98bf88a16d7a797106ecdd47e1e8ee86c83b483461b5df6e6",
                    HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(compressed)));
            byte[] raw;
            try (var gzip = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
                raw = gzip.readNBytes(1048577); assertTrue(raw.length <= 1048576); assertEquals(-1, gzip.read());
            }
            var tree = StrictJson.parse(raw, 1048576);
            assertEquals("MATCH", tree.get("source_postcheck").textValue());
            for (var sample : tree.get("cases")) if (sample.get("name").textValue().equals(name)) {
                assertTrue(sample.get("accepted").booleanValue());
                return object(OpportunityJson.parse(StrictJson.canonical(sample.get("input"), 131072)));
            }
            throw new IllegalArgumentException("missing original fixture " + name);
        }
    }

    /** Original producer native preview, with software frame/identity/treasury rebinding explicitly below.
     * Source: wave2-finance/src/test/resources/factioncandidate/python-golden-v1.json, case private-native-selected.
     * Full source SHA-256: b688e3dd381e7890c2d916cf55d998e38075097179f1aca713189b5ee844d8c2.
     * This historical synthetic fixture is not a current Native receipt. */
    private static Obj preview(Obj snapshot) {
        Obj original = object(OpportunityJson.parse(PRIVATE_PREVIEW.getBytes(StandardCharsets.UTF_8)));
        Obj nativePart = object(original.get("native")), observation = object(nativePart.get("observation"));
        observation = observation.with("snapshot_revision", snapshot.get("native_revision"))
                .with("native_snapshot_revision", snapshot.get("native_revision")).with("observed_date_raw", snapshot.get("date_raw"))
                .with("player_character_id", n(29829)).with("player_gold_raw", object(snapshot.get("played_character_gold")).get("raw"))
                .with("queried_source_faction_id", n(801)).with("source_faction_target_character_id", n(29829))
                .with("source_faction_leader_character_id", n(41003)).with("source_faction_member_character_ids", new Arr(List.of(n(41003))))
                .with("recipient_character_id", n(41003));
        return original.with("native", nativePart.with("source_faction_id", n(801)).with("recipient_character_id", n(41003))
                .with("observation", observation));
    }

    /** Complete existing source contract, retaining real stock predicate inputs from the original full corpus.
     * Only the fixture frame, identity set and one-row inventory are rebound; dangerous is never supplied by a ready flag. */
    private static Obj alert(Obj snapshot, boolean dangerous) throws Exception {
        byte[] raw;
        try (var input = MilitaryPeacetimeRuntimeTest.class.getResourceAsStream("/factionalerts/original-producer-golden.json")) {
            assertNotNull(input, "existing full original native alert fixture is required");
            raw = input.readNBytes(131073); assertTrue(raw.length <= 131072);
        }
        assertEquals("41b30820281d4d58163826fb1c6aa7c5f487323737b37e8f4e60e9647e057837",
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
        Obj corpus = object(OpportunityJson.parse(raw));
        Obj original = object(object(corpus.get("bases")).get("full"));
        Obj row = object(OpportunityJson.array(original.get("targeting_factions"), "full native rows").get(dangerous ? 1 : 0))
                .with("faction_id", n(801)).with("target_character_id", n(29829)).with("leader_character_id", n(41003))
                .with("character_member_ids", new Arr(List.of(n(41003))));
        Obj planner = object(original.get("planner_projection"))
                .with("dangerous", row.get("dangerous_by_stock_rule"))
                .with("dangerous_faction_ids", new Arr(dangerous ? List.of(n(801)) : List.of()))
                .with("watch_faction_ids", new Arr(dangerous ? List.of() : List.of(n(801))))
                .with("war_handoff_faction_ids", new Arr(List.of())).with("exposed_county_title_ids", new Arr(List.of()));
        var build = FactionAlertModel.Build.CK3_12004;
        Obj provenance = obj("game_version", new Text(build.version()), "executable_sha256", new Text(build.sha256()),
                "backend_id", new Text(build.backendId()));
        Obj alert = original.with("snapshot_revision", snapshot.get("native_revision")).with("date_raw", snapshot.get("date_raw"))
                .with("player_character_id", n(29829)).with("targeting_faction_count", n(1))
                .with("targeting_factions", new Arr(List.of(row))).with("county_exposures", new Arr(List.of()))
                .with("planner_projection", planner).with("provenance", provenance);
        return obj("step", new Text(FactionAlertModel.STEP), "accepted", new Bool(true), "status", alert.get("status"),
                "query_sequence", n(1), "snapshot_revision", snapshot.get("native_revision"), "player_faction_alerts", alert,
                "player_faction_alerts_ready", new Bool(true), "backend_id", new Text("native-headless"));
    }

    private static Obj object(Value value) { return OpportunityJson.object(value, "original M5 runtime fixture object"); }
    private static IntegerValue n(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static final String PRIVATE_PREVIEW = """
{"step":"private-query-faction-gift-member-v1","accepted":true,"private_build":true,"advertised":false,"status":"preview_ready","native":{"completion":"preview_ready","failure_flags":0,"source_faction_id":771,"recipient_character_id":33011,"observation":{"available":true,"paused":true,"snapshot_revision":412,"native_snapshot_revision":414,"observed_date_raw":53789952,"player_resources_query_complete":true,"player_character_id":32904,"player_gold_raw":25000000,"player_gold_scale":100000,"source_faction_requery_complete":true,"queried_source_faction_id":771,"source_faction_present":true,"source_faction_target_character_id":32904,"source_faction_targeting_player":true,"source_faction_at_war":false,"source_faction_leader_character_id":33011,"source_faction_member_character_ids":[33011],"source_faction_metrics_available":true,"source_faction_power_raw":65000000,"source_faction_discontent_raw":45000000,"source_faction_metric_scale":100000,"recipient_identity_resolved":true,"recipient_character_id":33011,"recipient_alive":true,"recipient_is_ai":true,"recipient_is_direct_landed_vassal":true,"recipient_opinion_query_complete":true,"recipient_opinion_of_player":-40,"gift_opinion_present":false,"gift_preview":{"available":true,"definition_key":"gift_interaction","definition_stable_hash":1234567890,"interaction_legal":true,"auto_accept":true,"gold_cost_raw":7500000,"gold_scale":100000,"opinion_delta":25}}}}
""";
}
