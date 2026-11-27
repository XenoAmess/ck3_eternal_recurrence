package org.xar.ck3.control.service.root;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryDecisionSelector;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanTrace;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;

class RootOnlineDecisionSelectorPeacefulLifeTest {
    @TempDir Path root;

    @Test void acceptsTheExactPreparedFull111ClockProposalAndArchivesTheOriginal() throws Exception {
        assertPreparedClockProposal(fixture("full111-peaceful-life-proposal.json"), Instant.parse("2026-11-27T12:35:58Z"),
                "163fba97950fc26deead036e590c6b1f05db5d14d5238580afaefed2a243e91f", 53180088);
    }

    @Test void acceptsTheExistingApprovedWholeMonthWithoutChangingItsTarget() throws Exception {
        assertPreparedClockProposal(fixture("full111-monthly-life-proposal.json"), Instant.parse("2026-11-27T13:00:31Z"),
                "27d60388b0685d8e6fd4969799fb2eb138293819d9721e17ca699e3605f716c2", 53180808);
    }

    @Test void acceptsTheOrdinaryLifeWithAnExactOneDayCadenceCap() throws Exception {
        assertPreparedClockProposal(fixture("full111-cadence-one-day-proposal.json"), Instant.parse("2026-11-27T13:50:53Z"),
                "71e4ba5d7abf4067cc2ce63c6f20b8bb5af96cac2742fae2521f791d3057b31f", 53180832);
    }

    @Test void onlyTheExactOriginalCadenceBoundaryCanUseOneDayApproval() throws Exception {
        var configured = config(Files.createDirectory(root.resolve("queue")));
        var fixture = fixture("full111-cadence-one-day-proposal.json");
        var selector = new RootOnlineDecisionSelector(configured, fakeClock(fixture.request().deadline().plusSeconds(1)),
                raw -> { throw new AssertionError("ineligible or expired selection archived evidence"); });
        var args = fixture.command().arguments();
        var plan = OpportunityJson.object(args.get("plan"), "planner choice");
        var advance = OpportunityJson.object(args.get("advance_v1"), "clock plan");
        var cap = OpportunityJson.object(advance.get("campaign_deadline"), "campaign boundary");
        var differentDate = new OpportunityJson.IntegerValue(java.math.BigInteger.valueOf(53180856));
        for (var different : List.of(
                args.with("maximum_target_date_raw", OpportunityJson.Nil.INSTANCE),
                args.with("plan", plan.with("maximum_target_date_raw", differentDate)),
                args.with("advance_v1", advance.with("campaign_deadline", cap.with("boundary_date_raw", differentDate))),
                args.with("advance_v1", advance.with("exact_one_day", new OpportunityJson.Bool(true))
                        .with("clock_mode", new OpportunityJson.Text("EXACT_SENTINEL"))))) {
            var changed = fixture.withCommandArguments(different);
            assertEquals("model_decision_deadline_exhausted", selector.select(fixture.request(), changed).reason());
        }
    }

    private void assertPreparedClockProposal(Fixture fixture, Instant now, String bodySha256, long target) throws Exception {
        var archives = new LinkedHashMap<ExactRef, byte[]>();
        var queue = Files.createDirectory(root.resolve("queue"));
        var selector = new RootOnlineDecisionSelector(config(queue), fakeClock(now),
                raw -> {
                    byte[] bytes = raw.bytes();
                    String sha = ActionCodec.sha256(bytes);
                    var ref = new ExactRef(root.resolve(sha).toString(), bytes.length, sha);
                    archives.put(ref, bytes);
                    return ref;
                });
        var picked = selector.select(fixture.request(), fixture.selected());
        assertEquals(OrdinaryDecisionSelector.Choice.ACCEPT, picked.choice());
        assertEquals("prepared_full111_peaceful_life", picked.reason());
        assertEquals(2, archives.size());
        assertArrayEquals(ActionCodec.encodeCommand(fixture.command()), archives.values().iterator().next());
        var evidence = FullJsonTree.parse(archives.get(picked.evidence().orElseThrow()), 65536);
        assertEquals("xar.ordinary-full111-peaceful-life-selection/v1", evidence.path("schema").textValue());
        assertEquals(bodySha256, evidence.path("body_sha256").textValue());
        assertEquals(target, evidence.path("proposal").path("arguments").path("advance_v1").path("target_date_raw").longValue());
        try (var files = Files.list(queue)) {
            assertEquals(0, files.count());
        }
    }

    @Test void keepsNativeWarsAndForegroundsInTheOriginalReviewerPath() throws Exception {
        var configured = config(Files.createDirectory(root.resolve("queue")));
        assertReviewStillRequired(configured, fixture("full111-peaceful-life-proposal.json"));
        assertReviewStillRequired(configured, fixture("full111-monthly-life-proposal.json"));
        assertReviewStillRequired(configured, fixture("full111-cadence-one-day-proposal.json"));
    }

    private void assertReviewStillRequired(RootOrdinaryRuntimeConfiguration.DecisionProvider configured, Fixture fixture) {
        var expired = fakeClock(fixture.request().deadline().plusSeconds(1));
        var selector = new RootOnlineDecisionSelector(configured, expired, raw -> { throw new AssertionError("expired selection archived evidence"); });
        assertEquals("peaceful_life_selection_deadline_exhausted", selector.select(fixture.request(), fixture.selected()).reason());
        var source = fixture.request().observations().snapshot();
        var evidence = new OpportunityJson.Obj(java.util.Map.of());
        for (var incompatible : List.of(
                source.with("active_wars", new OpportunityJson.Arr(List.of(evidence))),
                source.with("player_armies", new OpportunityJson.Arr(List.of(evidence))),
                source.with("active_event", evidence),
                source.with("pending_character_interaction", evidence),
                source.with("top_exclusive_modal_choice_hint", evidence),
                source.with("adapter_id", new OpportunityJson.Text("unavailable")),
                source.with("diagnostics", evidence))) {
            assertEquals("model_decision_deadline_exhausted",
                    selector.select(fixture.withSnapshot(incompatible), fixture.selected()).reason());
        }
        var original = fixture.selected().trace().finalPlan().orElseThrow();
        var otherPurpose = new OrdinaryPolicy.Draft(original.policy(), original.phase(), original.reason(),
                OrdinaryPolicy.Kind.FOREGROUND, original.command(), OrdinaryPolicy.Purpose.WORLD_ACTION,
                original.domain(), original.detail());
        var changedSelection = new PlanningResult.ActionSelected(fixture.command(),
                new PlanTrace(fixture.request().before(), List.of(), Optional.of(otherPurpose)));
        assertEquals("model_decision_deadline_exhausted", selector.select(fixture.request(), changedSelection).reason());
    }

    private static RootOrdinaryRuntimeConfiguration.DecisionProvider config(Path queue) {
        return new RootOrdinaryRuntimeConfiguration.DecisionProvider(queue.toUri(), "codex-session", Duration.ofSeconds(120), 1, Duration.ZERO);
    }

    private static Clock fakeClock(Instant time) {
        return Clock.fixed(time, ZoneOffset.UTC);
    }

    private Fixture fixture(String name) throws Exception {
        try (var raw = getClass().getResourceAsStream(name)) {
            var input = FullJsonTree.parse(raw.readAllBytes(), 65536);
            var command = ActionCodec.decodeCommand(FullJsonTree.encode(input.get("command"), 65536));
            var snapshot = OpportunityJson.object(OpportunityJson.parse(FullJsonTree.encode(input.get("snapshot"), 65536)), "Full111 snapshot");
            var steps = StreamSupport.stream(input.get("routable_operations").spliterator(), false)
                    .map(item -> new OperationKey(item.textValue())).collect(Collectors.toSet());
            var caps = StreamSupport.stream(input.get("capabilities").spliterator(), false)
                    .map(com.fasterxml.jackson.databind.JsonNode::textValue).collect(Collectors.toSet());
            var observations = new PlanningObservation(snapshot, List.of(), steps, caps, Optional.empty(), List.of(),
                    Optional.empty(), Optional.empty(), false);
            var request = new PlanningRequest(command.before(), command.source(), command.sessionId(),
                    Instant.parse(input.get("planning_deadline").textValue()), observations);
            var plan = OpportunityJson.object(command.arguments().get("plan"), "original prepared plan");
            var choice = new OrdinaryPolicy.Draft(OpportunityJson.text(plan.get("policy"), "policy"),
                    OpportunityJson.text(plan.get("phase"), "phase"), OpportunityJson.text(plan.get("reason"), "reason"),
                    OrdinaryPolicy.Kind.ORDINARY, Optional.of(command), OrdinaryPolicy.Purpose.DATE_ADVANCE, Optional.empty(), plan);
            return new Fixture(command, request, new PlanningResult.ActionSelected(command,
                    new PlanTrace(command.before(), List.of(), Optional.of(choice))));
        }
    }

    private record Fixture(ActionCommand command, PlanningRequest request, PlanningResult.ActionSelected selected) {
        PlanningResult.ActionSelected withCommandArguments(OpportunityJson.Obj args) {
            var changed = new ActionCommand(command.actionId(), command.before(), command.source(), command.sessionId(),
                    command.operation(), args, command.expected(), command.claims(), command.deadline());
            var plan = selected.trace().finalPlan().orElseThrow();
            var changedPlan = new OrdinaryPolicy.Draft(plan.policy(), plan.phase(), plan.reason(), plan.kind(), Optional.of(changed),
                    plan.purpose(), plan.domain(), OpportunityJson.object(args.get("plan"), "altered plan"));
            return new PlanningResult.ActionSelected(changed,
                    new PlanTrace(request.before(), List.of(), Optional.of(changedPlan)));
        }

        PlanningRequest withSnapshot(OpportunityJson.Obj snapshot) {
            var actual = request.observations();
            return new PlanningRequest(request.before(), request.source(), request.sessionId(), request.deadline(),
                    new PlanningObservation(snapshot, actual.history(), actual.actionSteps(), actual.bridgeCapabilities(),
                            actual.battleSpeedReadiness(), actual.actionFacts(), actual.campaignGoal(), actual.crossRunPlan(),
                            actual.initialLifestyleFocusRequired()));
        }
    }
}
