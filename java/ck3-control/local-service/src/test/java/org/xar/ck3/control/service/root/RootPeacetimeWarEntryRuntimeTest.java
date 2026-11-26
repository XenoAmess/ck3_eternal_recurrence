package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.zip.ZipInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.AdvancePlan;
import org.xar.ck3.control.application.advance.AdvanceRewrite;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.warentry.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;

/** Actual retained original selector corpus -> Java declaration producer -> runtime adapter.
 * Frames are explicit software fixtures; no physical Game, actual reader or command preparation is qualified here.
 */
final class RootPeacetimeWarEntryRuntimeTest {
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    private static final ExactRef SOURCE = new ExactRef("D:/fixture/peacetime-software-producer.java", 1, "a".repeat(64));
    private static final GameGeneration GAME = new GameGeneration(123,
            new PythonOnlyUInt64(new BigInteger("134000000000000001")));
    private static final String ADMITTED_DECLARATION_CASE = "faction-False-False";

    @Test void qualifiedArchivedWarCooldownClipsNewLifeWithoutLosingEarlierLimits() {
        var input = cooldownFixture();
        PlanningRequest request = request(input, Set.of(ClockStatusRead.ARM_CAP, ClockStatusRead.STATUS_CAP, ClockStatusRead.CANCEL_CAP));
        Obj plan = selected(input);
        var operation = new OperationKey("life-advance");
        var original = command(request, operation);
        assertEquals(53158200, AdvancePlan.decode(AdvanceRewrite.rewriteBound(request, original, operation.value(), Optional.empty(), 8)).targetDateRaw().intValueExact(),
                "archived batch 129 originally requested eight days");
        Obj arguments = RootPeacetimeWarEntryRuntime.commandArguments(request, operation, plan);
        assertEquals(new IntegerValue(BigInteger.valueOf(53158152)), arguments.get("maximum_target_date_raw"));
        var bounded = command(request, operation, arguments);
        var polled = AdvanceRewrite.rewriteBound(request, bounded, operation.value(), Optional.empty(), 8);
        assertEquals(53158152, AdvancePlan.decode(polled).targetDateRaw().intValueExact());
        assertEquals(6, AdvancePlan.decode(polled).horizonDays());
        assertEquals(original.deadline(), polled.deadline());
        assertEquals(original.origin(), polled.origin());
        var start = request.before().frame().identity().dateRaw();
        var requested = start.add(AdvancePlan.DAY.multiply(BigInteger.valueOf(8)));
        var campaign = new CampaignDeadline.Cap("fixture-campaign", "ck3-1.20.0.4-cdate-fixed365-raw24/v1", start,
                requested, BigInteger.valueOf(53158176), BigInteger.valueOf(53407128), BigInteger.valueOf(53158176), CampaignDeadline.Status.ADVANCE);
        assertEquals(53158176, AdvancePlan.decode(AdvanceRewrite.rewriteBound(request, original, operation.value(), Optional.of(campaign), 8)).targetDateRaw().intValueExact(),
                "archived batch 130's campaign boundary was still one day after the actual cooldown");
        var sentinel = AdvancePlan.decode(AdvanceRewrite.rewriteBound(request, bounded, operation.value(), Optional.of(campaign), 8));
        assertEquals(53158152, sentinel.targetDateRaw().intValueExact());
        assertEquals(AdvancePlan.ClockMode.CAMPAIGN_SENTINEL, sentinel.clockMode());
        assertEquals(53158080, AdvancePlan.decode(AdvanceRewrite.rewriteBound(request, bounded, operation.value(), Optional.of(campaign), 3)).targetDateRaw().intValueExact(),
                "an already smaller bound must win");
    }

    @Test void staleForeignOrUnchangedLegacyWarPlansGainNoCooldownBound() {
        var input = cooldownFixture();
        Obj original = selected(input);
        var operation = new OperationKey("life-advance");
        var qualified = request(input);
        String key = DeclarationOpportunityCooldown.VIEW_KEY;
        Obj actualCooldown = object(input.path("snapshot").get(key));
        assertTrue(RootPeacetimeWarEntryRuntime.commandArguments(qualified, operation,
                original.with(key, actualCooldown.with("remaining_days", new IntegerValue(BigInteger.ONE)))).members().isEmpty());
        assertTrue(RootPeacetimeWarEntryRuntime.commandArguments(qualified, operation,
                original.with("phase", new Text("native_war_discovery_progress"))).members().isEmpty());
        for (Obj unqualified : List.of(
                actualCooldown.with("remaining_days", new IntegerValue(BigInteger.ONE)),
                actualCooldown.with("actor_character_id", new IntegerValue(BigInteger.ONE)),
                actualCooldown.with("episode_run_id", new Text("foreign-episode")),
                actualCooldown.with("cooldown_until_date_raw", new IntegerValue(BigInteger.valueOf(53158008))),
                new Obj(Map.of("status", new Text("active"))))) {
            var variant = input.deepCopy();
            ((ObjectNode) variant.get("snapshot")).set(key, DriverJson.toNode(unqualified));
            assertTrue(RootPeacetimeWarEntryRuntime.commandArguments(request(variant), operation, selected(variant)).members().isEmpty());
        }
    }

    private static ObjectNode cooldownFixture() {
        // Batch 130 supplies the actor, date, episode, revision and original cooldown. The remaining fields are software fixture setup.
        return (ObjectNode) StrictJson.parse("""
                {"snapshot":{"snapshot_id":"native:1433","revision":1328,"native_revision":1433,"date_raw":53158008,
                  "episode_run_id":"resume91_latest268_20261101_a02","paused":true,"map_ready":true,
                  "played_character":{"character_id":31254,"alive":true},"active_wars":[],"player_armies":[],
                  "diagnostics":{"bridge_pid":123,"connection_generation":1},
                  "declaration_opportunity_cooldown_v1":{"schema":"xar.ck3.declaration-opportunity-cooldown/v1",
                  "status":"active","actor_character_id":31254,"episode_run_id":"resume91_latest268_20261101_a02",
                  "consecutive_no_war_rounds":2,"cooldown_until_date_raw":53158152,"remaining_days":6,"pending_query_sequence":null}},
                 "history":[],"steps":["life-advance","set-speed-5","query-declarable-wars"]}
                """.getBytes(java.nio.charset.StandardCharsets.UTF_8));
    }

    @Test void originalProducerDeclarationIdentityReachesRuntimeWithoutTupleProjectionLoss() throws IOException {
        var row = row(ADMITTED_DECLARATION_CASE); var selected = selected(row);
        List<DeclarationContract.Choice> original = DeclarationContract.normalize(row.get("snapshot").get("declarable_wars"));
        assertEquals(1, original.size()); var actual = original.getFirst();
        var operation = new OperationKey(StrictJson.text(row.get("expected").get("selected_step")));
        RootPeacetimeWarEntryRuntime.requireSelectedDeclaration(selected, actual, operation);
        assertEquals(actual.claimantCharacterId(), BigInteger.valueOf(-1));
        assertEquals(List.of(BigInteger.valueOf(91)), actual.targetTitleIds());
        assertEquals(selected, DriverJson.object(OpportunityJson.encode(selected), DriverJson.MAX_NATIVE_BYTES));
        for (String field : List.of("declaration_id", "target_character_id", "casus_belli_index", "casus_belli_key",
                "configuration_index", "claimant_character_id", "target_title_ids")) {
            ObjectNode changed = (ObjectNode) OpportunityJson.toNode(selected);
            ((ObjectNode) changed.get("selected_declaration")).remove(field);
            Obj missingField = assertInstanceOf(Obj.class, DriverJson.fromNode(changed));
            assertThrows(IllegalArgumentException.class, () -> RootPeacetimeWarEntryRuntime.requireSelectedDeclaration(
                    missingField, actual, operation), field);
            changed = (ObjectNode) OpportunityJson.toNode(selected);
            ((ObjectNode) changed.get("selected_declaration")).put(field, true);
            Obj boolField = assertInstanceOf(Obj.class, DriverJson.fromNode(changed));
            assertThrows(IllegalArgumentException.class, () -> RootPeacetimeWarEntryRuntime.requireSelectedDeclaration(
                    boolField, actual, operation), field + " bool");
        }
    }

    @Test void chosenStrongCommandRetainsTheOriginalPlanAndCompleteRequestIdentity() throws IOException {
        var row = row(ADMITTED_DECLARATION_CASE); var plan = selected(row); var request = request(row);
        var calls = new AtomicInteger();
        var operation = new OperationKey(((Text) plan.get("selected_step")).value());
        ActionCommand fixtureCommand = command(request, operation);
        var decision = RootPeacetimeWarEntryRuntime.finishSelected(request, plan, (actual, step, complete) -> {
            calls.incrementAndGet(); assertSame(request, actual); assertSame(plan, complete);
            assertEquals(operation.value(), step); return new PeacetimeWarEntryPlanner.Ready(fixtureCommand);
        });
        var replacement = assertInstanceOf(OrdinaryPolicy.Replace.class, decision);
        assertSame(plan, replacement.draft().detail());
        assertSame(fixtureCommand, replacement.draft().command().orElseThrow());
        assertEquals(OrdinaryPolicy.Purpose.WORLD_ACTION, replacement.draft().purpose());
        assertEquals(1, calls.get());
        var crossed = new PlanningRequest(request.before(), request.source(), "different-session", request.deadline(), request.observations());
        assertThrows(IllegalArgumentException.class, () -> RootPeacetimeWarEntryRuntime.finishSelected(crossed, plan,
                (actual, step, complete) -> new PeacetimeWarEntryPlanner.Ready(fixtureCommand)));
    }

    @Test void absentStrongProducerStopsBeforeAnyReadyOrReplacementCanBeClaimed() throws IOException {
        var row = row(ADMITTED_DECLARATION_CASE); var request = request(row); var calls = new AtomicInteger();
        var decision = RootPeacetimeWarEntryRuntime.finishSelected(request, selected(row), (actual, step, plan) -> {
            calls.incrementAndGet(); return new PeacetimeWarEntryPlanner.Unavailable("actual same-writer Army declaration preparation missing");
        });
        var stopped = assertInstanceOf(OrdinaryPolicy.Stop.class, decision);
        assertEquals(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN, stopped.stopReason());
        assertTrue(stopped.reason().contains("Army declaration")); assertEquals(1, calls.get());
    }

    @Test void unknownContinuityPreservesOriginalNoCommandAndQueriesCannotBecomeWorldCommands() throws IOException {
        var row = row("continuity-unknownNone"); var request = request(row); var plan = selected(row);
        assertSame(Nil.INSTANCE, plan.get("selected_step")); var calls = new AtomicInteger();
        var originalPending = RootPeacetimeWarEntryRuntime.finishSelected(request, plan, (actual, step, complete) -> {
            calls.incrementAndGet(); throw new AssertionError("UNKNOWN continuity must not prepare or replay any command");
        });
        var held = assertInstanceOf(OrdinaryPolicy.Replace.class, originalPending);
        assertTrue(held.draft().command().isEmpty()); assertSame(plan, held.draft().detail());
        assertEquals(OrdinaryPolicy.Purpose.READ_ONLY, held.draft().purpose()); assertEquals(0, calls.get());
        Obj query = plan.with("selected_step", new Text("query-declarable-wars"));
        assertThrows(IllegalArgumentException.class, () -> RootPeacetimeWarEntryRuntime.finishSelected(request, query,
                (actual, step, complete) -> { calls.incrementAndGet(); throw new AssertionError("a read must use its original typed producer"); }));
        assertEquals(0, calls.get());
    }

    @Test void originalPowerQueryReachesTheStrictMilitarySelectionWithItsCompletePlan() throws IOException {
        var row = row("missing-power-query"); Obj plan = selected(row);
        var read = RootPeacetimeWarEntryRuntime.readSelection(plan);
        assertEquals(new OperationKey("query-war-entry-assessments-v1-1-909"), read.operation());
        assertEquals(OrdinaryPolicy.Purpose.READ_ONLY, read.purpose());
        assertSame(plan, read.detail());
        assertTrue(read.arguments().members().isEmpty());
        assertThrows(IllegalArgumentException.class, () -> RootPeacetimeWarEntryRuntime.readSelection(new Obj(Map.of())));
        Obj missingAlert = selected(row("general-actual-force-declare"));
        var alertRead = RootPeacetimeWarEntryRuntime.readSelection(missingAlert);
        assertEquals(new OperationKey("query-player-faction-alerts-v1"), alertRead.operation());
        assertEquals(OrdinaryPolicy.Purpose.READ_ONLY, alertRead.purpose());
        assertSame(missingAlert, alertRead.detail());
        Obj world = selected(row(ADMITTED_DECLARATION_CASE));
        assertEquals(new Text("declare-war-909-17-0"), world.get("selected_step"));
        assertThrows(IllegalArgumentException.class, () -> RootPeacetimeWarEntryRuntime.readSelection(world));
    }

    @Test void lateOriginalArchiveKeepsTheCompleteDeclarationAndIntegerScopeBeforeRuntimeRefresh() throws IOException {
        var original = lateAvailable();
        Obj encoded = ArmyDeclarationCollectionCodec.encode(original);
        var archived = ArmyDeclarationCollectionCodec.decode(object(StrictJson.parse(OpportunityJson.encode(encoded))));
        var available = assertInstanceOf(ArmyDeclarationCollection.Available.class, archived);
        assertEquals(original.declarations(), available.declarations());
        assertEquals(original.nativeResultFrame(), available.nativeResultFrame());
        assertEquals(new BigInteger("18446744073709551615"), available.scope().currentBinding().connectionGeneration());
        assertEquals(encoded, ArmyDeclarationCollectionCodec.encode(available));
        var selected = selected(row(ADMITTED_DECLARATION_CASE));
        var actual = available.declarations().choices().getFirst();
        RootPeacetimeWarEntryRuntime.requireSelectedDeclaration(selected, actual,
                new OperationKey(actual.step().wire()));
        var decision = RootPeacetimeWarEntryRuntime.collectionDecision(available);
        assertInstanceOf(OrdinaryPolicy.Refresh.class, decision);
        assertTrue(decision.reason().contains(available.scope().requestId()));
        assertFalse(decision instanceof OrdinaryPolicy.Replace);
    }

    @Test void pendingStaleAndOriginalRejectionRemainDistinctAfterArchiveAndRuntimeConsumption() throws IOException {
        var available = lateAvailable(); var scope = available.scope(); var b = scope.currentBinding();
        var changed = new ArmyDeclarationCollection.Binding(b.snapshotId(), b.publicRevision().add(BigInteger.ONE),
                b.nativeRevision(), b.episode(), b.dateRaw(), b.paused(), b.mapReady(), b.playerCharacterId(),
                b.bridgePid(), b.connectionGeneration());
        var rejectedNode = (ObjectNode) StrictJson.parse(available.nativeResultFrame().bytes());
        rejectedNode.put("ok", false); rejectedNode.remove("result"); rejectedNode.put("error", "original native query rejected");
        List<ArmyDeclarationCollection.Result> original = List.of(new ArmyDeclarationCollection.Pending(scope),
                new ArmyDeclarationCollection.Stale(new ArmyDeclarationCollection.Scope(scope.requestId(),
                        scope.originalBinding(), changed), Optional.empty()),
                new ArmyDeclarationCollection.NativeRejected(scope, new RawJson(StrictJson.canonical(rejectedNode))));
        for (var result : original) {
            Obj encoded = ArmyDeclarationCollectionCodec.encode(result);
            var archived = ArmyDeclarationCollectionCodec.decode(object(StrictJson.parse(OpportunityJson.encode(encoded))));
            assertEquals(result.status(), archived.status());
            assertEquals(encoded, ArmyDeclarationCollectionCodec.encode(archived));
            var decision = RootPeacetimeWarEntryRuntime.collectionDecision(archived);
            if (archived instanceof ArmyDeclarationCollection.Pending) assertInstanceOf(OrdinaryPolicy.Wait.class, decision);
            else assertEquals(archived instanceof ArmyDeclarationCollection.Stale
                            ? PlanningResult.StopReason.INVALID_FRAME : PlanningResult.StopReason.POLICY_BLOCKED,
                    assertInstanceOf(OrdinaryPolicy.Stop.class, decision).stopReason());
            assertTrue(decision.reason().contains(scope.requestId()));
            assertTrue(decision.reason().contains(result.status().wire()));
            assertFalse(decision instanceof OrdinaryPolicy.Refresh);
            assertFalse(decision instanceof OrdinaryPolicy.Replace);
        }
    }

    private static ArmyDeclarationCollection.Available lateAvailable() throws IOException {
        JsonNode retained = row(ADMITTED_DECLARATION_CASE);
        var choices = DeclarationContract.normalize(retained.get("snapshot").get("declarable_wars"));
        var frame = (ObjectNode) StrictJson.parse("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"original-late-fixture\",\"ok\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        var result = frame.putObject("result").put("step", "query-declarable-wars").put("accepted", true)
                .put("status", "available").put("query_sequence", 5);
        result.set("declarable_wars", DeclarationContract.encode(choices));
        var declarations = new ArmyWarReadCodec.Declarations(choices, ArmyTypes.UInt64.positive(BigInteger.valueOf(5)),
                DriverJson.object(StrictJson.canonical(result), DriverJson.MAX_NATIVE_BYTES));
        var binding = new ArmyDeclarationCollection.Binding("synthetic-current", BigInteger.valueOf(3), BigInteger.TWO,
                "synthetic-episode", 1, true, true, 1, 123, new BigInteger("18446744073709551615"));
        return new ArmyDeclarationCollection.Available(new ArmyDeclarationCollection.Scope("original-late-fixture", binding, binding),
                new RawJson(StrictJson.canonical(frame)), declarations);
    }

    private static Obj selected(JsonNode row) {
        Obj snapshot = object(row.get("snapshot"));
        List<Obj> history = java.util.stream.StreamSupport.stream(row.get("history").spliterator(), false)
                .map(RootPeacetimeWarEntryRuntimeTest::object).toList();
        Set<String> steps = java.util.stream.StreamSupport.stream(row.get("steps").spliterator(), false)
                .map(JsonNode::textValue).collect(java.util.stream.Collectors.toUnmodifiableSet());
        return PeacetimeWarEntryPlanner.select(snapshot, history, steps).orElseThrow();
    }
    private static PlanningRequest request(JsonNode row) {
        return request(row, Set.of());
    }
    private static PlanningRequest request(JsonNode row, Set<String> capabilities) {
        ObjectNode raw = row.get("snapshot").deepCopy();
        // The older peaceful selector cases predate the full Driver's explicit owned-army roster.
        if (!raw.has("player_armies")) raw.putArray("player_armies");
        Obj snapshot = object(raw);
        String episode = StrictJson.text(raw.get("episode_run_id"));
        var before = new ObservationIdentity("fixture-machine", GAME, new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(raw.get("played_character").get("character_id").bigIntegerValue(),
                        raw.get("native_revision").bigIntegerValue(), raw.get("date_raw").bigIntegerValue()),
                StrictJson.text(raw.get("snapshot_id")), raw.get("revision").bigIntegerValue(), episode), 1);
        var source = new G2Source(before.machineId(), NOW.toString(), "fixture-build", SOURCE);
        Set<OperationKey> steps = java.util.stream.StreamSupport.stream(row.get("steps").spliterator(), false)
                .map(value -> new OperationKey(StrictJson.text(value))).collect(java.util.stream.Collectors.toUnmodifiableSet());
        List<Obj> history = java.util.stream.StreamSupport.stream(row.get("history").spliterator(), false)
                .map(RootPeacetimeWarEntryRuntimeTest::object).toList();
        return new PlanningRequest(before, source, "fixture-session", NOW.plusSeconds(60),
                new PlanningObservation(snapshot, history, steps, capabilities, Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false));
    }
    private static ActionCommand command(PlanningRequest request, OperationKey operation) {
        return command(request, operation, new Obj(Map.of()));
    }
    private static ActionCommand command(PlanningRequest request, OperationKey operation, Obj arguments) {
        return new ActionCommand("fixture-peacetime-command", request.before(), request.source(), request.sessionId(), operation,
                arguments, new ExpectedPostcondition(1, request.before(), request.source(), "fixture-observer/v1",
                        List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true))),
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), request.deadline());
    }
    private static Obj object(JsonNode value) {
        return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(value)), "original retained peacetime producer");
    }
    private static JsonNode row(String name) throws IOException {
        try (var stream = RootPeacetimeWarEntryRuntimeTest.class.getResourceAsStream("/warentry/original-producer-golden.zip")) {
            if (stream == null) throw new IOException("exact retained original peacetime producer corpus required; absent is NOT_RUN");
            try (var archive = new ZipInputStream(stream)) {
                var entry = archive.getNextEntry();
                if (entry == null || !entry.getName().equals("original-producer-golden.json")) throw new IOException("original producer archive entry changed");
                byte[] body = archive.readNBytes((1 << 20) + 1);
                if (body.length == 0 || body.length > (1 << 20) || archive.getNextEntry() != null) throw new IOException("bounded original producer archive required");
                JsonNode source = StrictJson.parse(body, 1 << 20);
                assertEquals("xar.ck3.peacetime-war-entry.original-producer-golden/v1", StrictJson.text(source.get("schema")));
                for (JsonNode row : source.get("cases")) if (name.equals(StrictJson.text(row.get("name")))) return row;
                throw new IOException("actual original producer case missing: " + name);
            }
        }
    }
}
