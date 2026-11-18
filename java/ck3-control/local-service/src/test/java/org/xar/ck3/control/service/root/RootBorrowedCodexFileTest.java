package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual Core/journal/writer lease and immutable archive. Observation metadata is DATA; no Game/read/action is issued. */
final class RootBorrowedCodexFileTest {
    @TempDir Path directory;
    private record Input(PlanningRequest request, PlanningResult.ActionSelected proposal) { }

    @Test @Timeout(30)
    void fileCliSelectAndArchiveFailureRetainTheOriginalBorrowedWriterAndUnknownSnapshot() throws Exception {
        for (boolean failArchive : List.of(false, true)) {
            Path root = directory.resolve("borrowed-" + failArchive);
            var fixture = RootManagedSessionScopeTest.dataCore(root.resolve("core"));
            try (var core = fixture.core()) {
                byte[] originalSnapshot = Files.readAllBytes(fixture.configuration().ledger().snapshot());
                Input input = input(fixture.configuration().machineId(), fixture.source());
                Path queue = root.resolve("codex"); Path materials = fixture.configuration().artifactRoot();
                var originalSession = new AtomicReference<ContinuityStorePort.Session>();
                var archived = new AtomicInteger();
                var selector = new RootOnlineDecisionSelector(new RootOrdinaryRuntimeConfiguration.DecisionProvider(queue.toUri(),
                        "codex-session", Duration.ofSeconds(8), 1, Duration.ZERO), Clock.systemUTC(), raw -> {
                    var same = core.writer().activeSession().orElseThrow();
                    assertSame(originalSession.get(), same); core.writer().requireSession(same);
                    assertThrows(IOException.class, () -> core.writer().locked(unexpected -> {
                        throw new AssertionError("selector must borrow the original writer instead of opening another Session");
                    }));
                    JsonNode value = FullJsonTree.parse(raw.bytes(), FullJsonTree.MAXIMUM_BYTES);
                    if ("xar.ordinary-codex-file-attempt/v1".equals(value.path("schema").asText())) {
                        archived.incrementAndGet();
                        if (failArchive) throw new IOException("controlled attempt archive failure");
                    }
                    return core.archive().withSession(same).preserveMaterial(raw);
                });
                var responder = CompletableFuture.supplyAsync(() -> {
                    try {
                        Path request = awaitReady(queue); String sha = ActionCodec.sha256(Files.readAllBytes(request));
                        // The independent file-side caller has no borrowed writer Session and never requests one.
                        assertThrows(IOException.class, () -> core.writer().borrowedSession());
                        JsonNode inspection = CodexSessionDecisionMain.execute(Clock.systemUTC(), "inspect", request.toString(), sha, materials.toString());
                        Path inspected = root.resolve("inspection.json"); Files.write(inspected, FullJsonTree.encode(inspection, 262144));
                        var pending = CodexSessionDecisionFiles.read(request, sha, materials, Clock.systemUTC());
                        Path selected = root.resolve("selection.json"); Files.write(selected, FullJsonTree.encode(
                                pending.selection(CodexSessionDecisionFiles.Decision.SELECT_PROPOSAL, "reviewed one original DATA proposal").toJson(), 262144));
                        CodexSessionDecisionMain.execute(Clock.systemUTC(), "respond", request.toString(), sha, materials.toString(), selected.toString(), inspected.toString());
                        return request;
                    } catch (Exception failure) { throw new java.util.concurrent.CompletionException(failure); }
                });
                OrdinaryDecisionSelector.Selection selection = core.withBorrowed(() -> {
                    var same = core.writer().borrowedSession(); originalSession.set(same);
                    String head = same.head().digest();
                    var actual = selector.select(input.request(), input.proposal());
                    assertSame(same, core.writer().borrowedSession()); core.writer().requireSession(same);
                    assertEquals(head, same.head().digest(), "file choice/material archival must not rewrite original ledger or UNKNOWN data");
                    return actual;
                });
                Path request = responder.get(5, TimeUnit.SECONDS);
                assertEquals(1, archived.get());
                assertEquals(failArchive ? OrdinaryDecisionSelector.Choice.WAIT : OrdinaryDecisionSelector.Choice.ACCEPT, selection.choice(), selection.reason());
                assertEquals(!failArchive, Files.isRegularFile(request.getParent().resolve("archived.json")));
                assertTrue(core.writer().activeSession().isEmpty(), "the outer original scope releases its Session normally");
                assertArrayEquals(originalSnapshot, Files.readAllBytes(fixture.configuration().ledger().snapshot()));
                // Handles from success and archive failure are both released after the original writer callback exits.
                Files.move(request, request.resolveSibling("released-request.json"));
                Files.move(request.getParent().resolve("response.json"), request.resolveSibling("released-response.json"));
            }
        }
    }

    private static Input input(String machine, ExactRef originalSource) {
        var game = new GameGeneration(121, new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var before = new ObservationIdentity(machine, game, new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(73), BigInteger.ONE, BigInteger.valueOf(1000)),
                "file-data-frame", BigInteger.ONE, "file-data-episode"), 1);
        var source = new G2Source(machine, Instant.now().toString(), "archive-data-no-live-qualification", originalSource);
        var snapshot = new OpportunityJson.Obj(Map.ofEntries(
                Map.entry("paused", new OpportunityJson.Bool(true)), Map.entry("map_ready", new OpportunityJson.Bool(true)),
                Map.entry("snapshot_id", new OpportunityJson.Text("file-data-frame")),
                Map.entry("episode_run_id", new OpportunityJson.Text("file-data-episode")),
                Map.entry("revision", new OpportunityJson.IntegerValue(BigInteger.ONE)),
                Map.entry("native_revision", new OpportunityJson.IntegerValue(BigInteger.ONE)),
                Map.entry("date_raw", new OpportunityJson.IntegerValue(BigInteger.valueOf(1000))),
                Map.entry("played_character", new OpportunityJson.Obj(Map.of("character_id", new OpportunityJson.IntegerValue(BigInteger.valueOf(73))))),
                Map.entry("active_wars", new OpportunityJson.Arr(List.of())), Map.entry("player_armies", new OpportunityJson.Arr(List.of()))));
        var operation = new OperationKey("fixture-archive-data-choice");
        var observation = new PlanningObservation(snapshot, List.of(), Set.of(operation), Set.of(), Optional.empty(),
                List.of(), Optional.empty(), Optional.empty(), false);
        var request = new PlanningRequest(before, source, "file-data-session", Instant.now().plusSeconds(30), observation);
        var command = new ActionCommand("file-data-original", before, source, request.sessionId(), operation,
                new OpportunityJson.Obj(Map.of()), new ExpectedPostcondition(1, before, source, "archive-data-expected/v1",
                List.of(new ExpectedBoolean(new FieldKey("paused"), true))),
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), request.deadline());
        var draft = new OrdinaryPolicy.Draft("file-data", "review", "no action is submitted", OrdinaryPolicy.Kind.ORDINARY,
                Optional.of(command), OrdinaryPolicy.Purpose.READ_ONLY, Optional.empty(), new OpportunityJson.Obj(Map.of()));
        return new Input(request, new PlanningResult.ActionSelected(command, new PlanTrace(before, List.of(), Optional.of(draft))));
    }
    private static Path awaitReady(Path queue) throws Exception {
        long end = System.nanoTime() + TimeUnit.SECONDS.toNanos(8);
        while (System.nanoTime() < end) {
            if (Files.isDirectory(queue)) try (var paths = Files.list(queue)) {
                var file = paths.map(path -> path.resolve("request.json")).filter(Files::isRegularFile)
                        .filter(path -> Files.isRegularFile(path.getParent().resolve("ready.json"))).findFirst();
                if (file.isPresent()) return file.orElseThrow();
            }
            Thread.sleep(5);
        }
        throw new IOException("original READY was not published");
    }
}
