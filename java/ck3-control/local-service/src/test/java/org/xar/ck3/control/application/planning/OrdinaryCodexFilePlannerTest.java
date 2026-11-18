package org.xar.ck3.control.application.planning;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.PlanningFixtures.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.*;

/** Real planner/selector/public file CLI; fixture policies never submit or settle an action. */
final class OrdinaryCodexFilePlannerTest {
    @TempDir Path directory;
    private final Clock clock = Clock.fixed(NOW, ZoneOffset.UTC);
    private volatile boolean failAttemptArchive;
    @Test @Timeout(20)
    void sessionWaitTraversesTheActualPlannerAndRemovesTheOriginalCommand() throws Exception {
        var op = new OperationKey("fixture-query"); var input = request(snapshot(), List.of(), Set.of(op));
        var original = command(input, op, new OpportunityJson.Obj(java.util.Map.of()));
        Path queue = directory.resolve("queue"); var planner = planner(original);
        planner.bindSelector(selector(queue));
        var result = CompletableFuture.supplyAsync(() -> planner.plan(input));
        Path file = awaitReady(queue); String sha = ActionCodec.sha256(Files.readAllBytes(file));
        Path materials = directory.resolve("materials");
        var inspection = CodexSessionDecisionMain.execute(clock, "inspect", file.toString(), sha, materials.toString());
        Path inspectionFile = directory.resolve("inspection.json"); Files.write(inspectionFile, FullJsonTree.encode(inspection, 262144));
        var pending = CodexSessionDecisionFiles.read(file, sha, materials, clock);
        Path choice = directory.resolve("choice.json");
        Files.write(choice, FullJsonTree.encode(pending.selection(CodexSessionDecisionFiles.Decision.WAIT, "review original and wait").toJson(), 262144));
        CodexSessionDecisionMain.execute(clock, "respond", file.toString(), sha, materials.toString(), choice.toString(), inspectionFile.toString());
        var waiting = assertInstanceOf(PlanningResult.ReadOnlyWait.class, result.get(5, TimeUnit.SECONDS));
        assertTrue(waiting.trace().finalPlan().orElseThrow().command().isEmpty());
        assertEquals(OrdinaryPolicy.Purpose.READ_ONLY, waiting.trace().finalPlan().orElseThrow().purpose());
        assertEquals(input.before(), waiting.trace().before());
        assertEquals("review original and wait", waiting.reason());
        assertEquals(ActionCodec.bodySha256(original), pending.selection(CodexSessionDecisionFiles.Decision.WAIT, "original").bodySha256());
    }

    @Test
    void originalUnknownAndSettledFactsPreventEvenCreatingAFileDecisionRequest() throws Exception {
        for (ExternalState state : List.of(ExternalState.UNKNOWN, ExternalState.APPLIED_CONFIRMED)) {
            var op = new OperationKey("fixture-query"); var input = request(snapshot(), List.of(), Set.of(op));
            var original = command(input, op, new OpportunityJson.Obj(java.util.Map.of()));
            var fact = new ExternalFact(original.actionId(), ActionCodec.bodySha256(original), input.before(), state,
                    UnknownScope.GLOBAL, org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain.council,
                    original.claims(), SOURCE);
            var obs = input.observations();
            var blocked = new PlanningRequest(input.before(), input.source(), input.sessionId(), input.deadline(),
                    new PlanningObservation(obs.snapshot(), obs.history(), obs.actionSteps(), obs.bridgeCapabilities(),
                            obs.battleSpeedReadiness(), List.of(fact), obs.campaignGoal(), obs.crossRunPlan(), obs.initialLifestyleFocusRequired()));
            Path queue = directory.resolve("blocked-" + state); var planner = planner(original); planner.bindSelector(selector(queue));
            var result = planner.plan(blocked);
            if (state == ExternalState.UNKNOWN) assertEquals(PlanningResult.StopReason.UNKNOWN_ACTION_UNRESOLVED,
                    assertInstanceOf(PlanningResult.Stopped.class, result).reason());
            else assertInstanceOf(PlanningResult.ReadOnlyWait.class, result);
            assertFalse(Files.exists(queue), "existing authoritative original must not be re-proposed to the file provider");
            assertEquals(List.of(fact), blocked.observations().actionFacts());
        }
    }

    @Test @Timeout(20)
    void failedAttemptArchiveReleasesBothNativeHandlesWithoutAcknowledgingTheQueue() throws Exception {
        failAttemptArchive = true;
        var op = new OperationKey("fixture-query"); var input = request(snapshot(), List.of(), Set.of(op));
        var original = command(input, op, new OpportunityJson.Obj(java.util.Map.of()));
        Path queue = directory.resolve("archive-failure"); var planner = planner(original); planner.bindSelector(selector(queue));
        var result = CompletableFuture.supplyAsync(() -> planner.plan(input)); Path file = awaitReady(queue);
        var pending = CodexSessionDecisionFiles.read(file, ActionCodec.sha256(Files.readAllBytes(file)), directory.resolve("materials"), clock);
        CodexSessionDecisionFiles.respond(pending, pending.selection(CodexSessionDecisionFiles.Decision.WAIT, "fixture waits"));
        assertInstanceOf(PlanningResult.ReadOnlyWait.class, result.get(5, TimeUnit.SECONDS));
        assertFalse(Files.exists(file.getParent().resolve("archived.json")));
        Files.move(file, file.resolveSibling("released-request.json"));
        Files.move(file.getParent().resolve("response.json"), file.resolveSibling("released-response.json"));
    }

    private OrdinaryPlanner planner(ActionCommand command) {
        var realm = new RealmLifecycle(SOURCE); var policies = new ArrayList<OrdinaryPolicy>();
        for (PlanningStage stage : PlanningStage.values()) {
            if (stage == PlanningStage.REALM_MEMBERSHIP_PUBLICATION) { policies.add(realm); continue; }
            policies.add(new OrdinaryPolicy() {
                @Override public PlanningStage stage() { return stage; }
                @Override public ExactRef implementationSource() { return SOURCE; }
                @Override public Decision evaluate(PlanningRequest input, Draft previous) {
                    return stage == PlanningStage.ORDINARY_CORE ? new Replace(new Draft("fixture", "query", "original proposal",
                            Kind.ORDINARY, Optional.of(command), Purpose.READ_ONLY, Optional.empty(), new OpportunityJson.Obj(java.util.Map.of())),
                            "original proposal") : new Keep("fixture unchanged");
                }
            });
        }
        return new OrdinaryPlanner(policies, clock, realm);
    }
    private RootOnlineDecisionSelector selector(Path queue) {
        return new RootOnlineDecisionSelector(new RootOrdinaryRuntimeConfiguration.DecisionProvider(queue.toUri(), "codex-session",
                Duration.ofSeconds(5), 1, Duration.ZERO), clock, material -> {
            byte[] bytes = material.bytes(); String sha = ActionCodec.sha256(bytes);
            if (failAttemptArchive && "xar.ordinary-codex-file-attempt/v1".equals(
                    FullJsonTree.parse(bytes, FullJsonTree.MAXIMUM_BYTES).path("schema").asText()))
                throw new java.io.IOException("fixture archive failure");
            Path root = directory.resolve("materials"); Files.createDirectories(root); Path file = root.resolve(sha + ".json");
            if (!Files.exists(file)) Files.write(file, bytes);
            return new ExactRef(file.toString(), bytes.length, sha);
        });
    }
    private static Path awaitReady(Path queue) throws Exception {
        long end = System.nanoTime() + TimeUnit.SECONDS.toNanos(5);
        while (System.nanoTime() < end) {
            if (Files.isDirectory(queue)) try (var paths = Files.list(queue)) {
                var file = paths.map(path -> path.resolve("request.json")).filter(Files::isRegularFile)
                        .filter(path -> Files.isRegularFile(path.getParent().resolve("ready.json"))).findFirst();
                if (file.isPresent()) return file.orElseThrow();
            }
            Thread.sleep(5);
        }
        throw new IllegalStateException("actual original READY file was not published");
    }
}
