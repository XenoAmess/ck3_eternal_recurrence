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
        var fixture = fixture();
        var archives = new LinkedHashMap<ExactRef, byte[]>();
        var queue = Files.createDirectory(root.resolve("queue"));
        var selector = new RootOnlineDecisionSelector(config(queue), fakeClock(Instant.parse("2026-11-27T12:35:58Z")),
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
        assertEquals("163fba97950fc26deead036e590c6b1f05db5d14d5238580afaefed2a243e91f", evidence.path("body_sha256").textValue());
        assertEquals(53180088, evidence.path("proposal").path("arguments").path("advance_v1").path("target_date_raw").longValue());
        try (var files = Files.list(queue)) {
            assertEquals(0, files.count());
        }
    }

    @Test void keepsNativeWarsAndForegroundsInTheOriginalReviewerPath() throws Exception {
        var fixture = fixture();
        var configured = config(Files.createDirectory(root.resolve("queue")));
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

    private Fixture fixture() throws Exception {
        try (var raw = getClass().getResourceAsStream("full111-peaceful-life-proposal.json")) {
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
        PlanningRequest withSnapshot(OpportunityJson.Obj snapshot) {
            var actual = request.observations();
            return new PlanningRequest(request.before(), request.source(), request.sessionId(), request.deadline(),
                    new PlanningObservation(snapshot, actual.history(), actual.actionSteps(), actual.bridgeCapabilities(),
                            actual.battleSpeedReadiness(), actual.actionFacts(), actual.campaignGoal(), actual.crossRunPlan(),
                            actual.initialLifestyleFocusRequired()));
        }
    }
}
