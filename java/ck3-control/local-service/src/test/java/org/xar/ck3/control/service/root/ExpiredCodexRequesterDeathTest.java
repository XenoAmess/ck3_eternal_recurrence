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
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.continuity.writer.StorageWriteGuardTestSupport;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Controlled disposable DATA-only JVM, actual Core/writer/file handles. Never creates a Game/model/HTTP/business worker. */
final class ExpiredCodexRequesterDeathTest {
    @TempDir Path directory;
    private record Input(PlanningRequest request, PlanningResult.ActionSelected proposal) { }

    public static void main(String[] args) throws Exception {
        if (args.length != 2 || !args[0].equals("requester-data")) throw new IllegalArgumentException("closed software fixture mode/root required");
        Path root = Path.of(args[1]); var opened = RootManagedSessionScopeTest.dataCore(root.resolve("core"));
        try (var core = opened.core()) {
            Clock clock = Clock.systemUTC(); var data = input(opened.configuration().machineId(), opened.source(), clock);
            var selector = new RootOnlineDecisionSelector(new RootOrdinaryRuntimeConfiguration.DecisionProvider(root.resolve("codex").toUri(),
                    "codex-session", Duration.ofSeconds(20), 1, Duration.ZERO), clock,
                    raw -> core.archive().withSession(core.writer().borrowedSession()).preserveMaterial(raw));
            core.withBorrowed(() -> selector.select(data.request(), data.proposal()));
            throw new AssertionError("fixture was expected to be terminated while its file request was pending");
        }
    }

    @Test @Timeout(60)
    void requesterDeathAndLateSelectAreArchivedAsUnknownWaitBeforeQueueReuse() throws Exception {
        Path root = directory.resolve("closed-requester"); Files.createDirectories(root); Path log = root.resolve("child.log");
        Path java = Path.of(System.getProperty("java.home"), "bin", "java.exe");
        Path childJna = Files.createDirectory(root.resolve("jna"));
        Process child = new ProcessBuilder(java.toString(), "-Djna.tmpdir=" + childJna, "-cp",
                System.getProperty("surefire.test.class.path", System.getProperty("java.class.path")),
                ExpiredCodexRequesterDeathTest.class.getName(), "requester-data", root.toString()).redirectErrorStream(true).redirectOutput(log.toFile()).start();
        Path request;
        try {
            request = awaitReady(root.resolve("codex"));
            child.destroyForcibly(); assertTrue(child.waitFor(8, TimeUnit.SECONDS), "only the owned disposable DATA JVM is terminated");
            assertNotEquals(0, child.exitValue());
        } finally { if (child.isAlive()) { child.destroyForcibly(); child.waitFor(8, TimeUnit.SECONDS); } }
        assertTrue(Files.size(log) <= 65536, "bounded software fixture output");
        byte[] requestBytes = Files.readAllBytes(request); JsonNode original = FullJsonTree.parse(requestBytes, 16384);
        assertFalse(Files.exists(request.getParent().resolve("archived.json")), "process death grants no original archive acknowledgement");
        JsonNode response = StrictJson.object().put("schema", CodexSessionDecisionFiles.RESPONSE_SCHEMA)
                .put("request_id", original.path("request_id").textValue()).put("request_sha256", ActionCodec.sha256(requestBytes));
        ((com.fasterxml.jackson.databind.node.ObjectNode) response).set("selection", new CodexSessionDecisionFiles.Selection(
                CodexSessionDecisionFiles.Decision.SELECT_PROPOSAL, original.path("proposal_id").textValue(),
                original.path("body_sha256").textValue(), "late software fixture selection").toJson());
        byte[] responseBytes = FullJsonTree.encode(response, 262144);
        Path config = root.resolve("core/configuration.json");
        var configuration = RootApplicationConfiguration.fromJson(StrictJson.parse(Files.readAllBytes(config), 1 << 20));
        byte[] snapshot = Files.readAllBytes(configuration.ledger().snapshot());
        Clock expired = Clock.fixed(Instant.parse(original.path("deadline_utc").textValue()).plusSeconds(1), ZoneOffset.UTC);
        try (var core = RootApplicationAssembly.open(configuration, expired, List.of(), Optional.empty(), StorageWriteGuardTestSupport.create(configuration.ledger()))) {
            core.withBorrowed(() -> {
                var same = core.writer().borrowedSession(); String head = same.head().digest();
                assertThrows(IOException.class, () -> RootExpiredCodexFileEvidence.archive(root.resolve("codex"), configuration.machineId(), expired,
                        raw -> { throw new IOException("controlled expired evidence archive failure"); },
                        expired.instant().plusSeconds(5), System.nanoTime() + TimeUnit.SECONDS.toNanos(5)));
                assertSame(same, core.writer().borrowedSession()); assertEquals(head, same.head().digest());
                assertFalse(Files.exists(request.getParent().resolve("expired.json")));
                assertArrayEquals(requestBytes, Files.readAllBytes(request));
                Path released = request.resolveSibling("released-probe.json"); Files.move(request, released); Files.move(released, request);
                return null;
            });
            var firstEvidence = core.withBorrowed(() -> {
                var same = core.writer().borrowedSession(); String head = same.head().digest();
                RootExpiredCodexFileEvidence.archive(root.resolve("codex"), configuration.machineId(), expired,
                        raw -> core.archive().withSession(same).preserveMaterial(raw), expired.instant().plusSeconds(5), System.nanoTime() + TimeUnit.SECONDS.toNanos(5));
                JsonNode marker = StrictJson.parse(Files.readAllBytes(request.getParent().resolve("expired.json")), 4096);
                RootExpiredCodexFileEvidence.requireReceipt(marker);
                var body = core.archive().withSession(same).loadMaterial(ExactRef.fromJson(marker.get("evidence"))).bytes();
                assertEquals(head, same.head().digest()); return FullJsonTree.parse(body, 524288);
            });
            assertTrue(firstEvidence.get("response_wire_base64").isNull(), "absence is captured before the late result arrives");
            Files.write(request.getParent().resolve("response.json"), responseBytes);
            var evidence = core.withBorrowed(() -> {
                var same = core.writer().borrowedSession();
                RootExpiredCodexFileEvidence.archive(root.resolve("codex"), configuration.machineId(), expired,
                        raw -> core.archive().withSession(same).preserveMaterial(raw), expired.instant().plusSeconds(5), System.nanoTime() + TimeUnit.SECONDS.toNanos(5));
                JsonNode marker = StrictJson.parse(Files.readAllBytes(request.getParent().resolve("expired-late.json")), 4096);
                RootExpiredCodexFileEvidence.requireReceipt(marker);
                return FullJsonTree.parse(core.archive().withSession(same).loadMaterial(ExactRef.fromJson(marker.get("evidence"))).bytes(), 524288);
            });
            assertTrue(evidence.hasNonNull("previous_expired_wire_base64"), "late result adds a new immutable receipt preserving the first one");
            assertEquals("UNKNOWN", evidence.path("requester_state").textValue());
            assertEquals("WAIT", evidence.path("effective_decision").textValue());
            assertArrayEquals(requestBytes, Base64.getDecoder().decode(evidence.path("request_wire_base64").textValue()));
            assertArrayEquals(responseBytes, Base64.getDecoder().decode(evidence.path("response_wire_base64").textValue()));
            Path queue = root.resolve("codex");
            var unpublished = new ArrayList<Path>();
            for (int n = 1; n < RootCodexFileDecisionExchange.MAX_ENTRIES; n++)
                unpublished.add(Files.createDirectory(queue.resolve("codex-" + UUID.randomUUID())));
            try (var slots = Files.list(queue)) {
                assertEquals(RootCodexFileDecisionExchange.MAX_ENTRIES, slots.count());
            }
            var current = input(configuration.machineId(), configuration.writerSources().getFirst(), expired);
            // The follow-up needs time to archive its own exact request and command before it reaches the queue.
            var selector = new RootOnlineDecisionSelector(new RootOrdinaryRuntimeConfiguration.DecisionProvider(queue.toUri(),
                    "codex-session", Duration.ofSeconds(12), 1, Duration.ZERO), expired,
                    raw -> core.archive().withSession(core.writer().borrowedSession()).preserveMaterial(raw));
            var choice = core.withBorrowed(() -> selector.select(current.request(), current.proposal()));
            assertEquals(OrdinaryDecisionSelector.Choice.WAIT, choice.choice(), "old late SELECT must not transfer to a new original request");
            assertFalse(Files.exists(request.getParent()), "only fully archived expired queue evidence can release a bounded slot");
            for (Path slot : unpublished) {
                try (var files = Files.list(slot)) { assertEquals(0, files.count(), "unpublished slots stay untouched"); }
            }
            try (var slots = Files.list(queue)) {
                var newRequests = slots.filter(slot -> Files.isRegularFile(slot.resolve("ready.json"))).toList();
                assertEquals(1, newRequests.size(), "the released slot can publish exactly one new request");
                assertNotEquals(request.getParent(), newRequests.getFirst());
            }
            assertArrayEquals(snapshot, Files.readAllBytes(configuration.ledger().snapshot()), "original pending/UNKNOWN state is unchanged");
        }
    }
    private static Input input(String machine, ExactRef originalSource, Clock clock) {
        var game = new GameGeneration(121, new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var before = new ObservationIdentity(machine, game, new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(73), BigInteger.ONE, BigInteger.valueOf(1000)),
                "file-data-frame", BigInteger.ONE, "file-data-episode"), 1);
        var source = new G2Source(machine, clock.instant().toString(), "archive-data-no-live-qualification", originalSource);
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
        var request = new PlanningRequest(before, source, "file-data-session", clock.instant().plusSeconds(30), observation);
        var command = new ActionCommand("file-data-original", before, source, request.sessionId(), operation,
                new OpportunityJson.Obj(Map.of()), new ExpectedPostcondition(1, before, source, "archive-data-expected/v1",
                List.of(new ExpectedBoolean(new FieldKey("paused"), true))),
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), request.deadline());
        var draft = new OrdinaryPolicy.Draft("file-data", "review", "no action is submitted", OrdinaryPolicy.Kind.ORDINARY,
                Optional.of(command), OrdinaryPolicy.Purpose.READ_ONLY, Optional.empty(), new OpportunityJson.Obj(Map.of()));
        return new Input(request, new PlanningResult.ActionSelected(command, new PlanTrace(before, List.of(), Optional.of(draft))));
    }
    private static Path awaitReady(Path queue) throws Exception {
        long until = System.nanoTime() + TimeUnit.SECONDS.toNanos(20);
        while (System.nanoTime() < until) {
            if (Files.isDirectory(queue)) try (var paths = Files.list(queue)) {
                var file = paths.map(path -> path.resolve("request.json")).filter(Files::isRegularFile)
                        .filter(path -> Files.isRegularFile(path.getParent().resolve("ready.json"))).findFirst();
                if (file.isPresent()) return file.orElseThrow();
            }
            Thread.sleep(5);
        }
        throw new IOException("controlled DATA requester did not publish its finite original request");
    }
}
