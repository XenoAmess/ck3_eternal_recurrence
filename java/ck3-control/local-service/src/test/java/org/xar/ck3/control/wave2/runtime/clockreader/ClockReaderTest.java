package org.xar.ck3.control.wave2.runtime.clockreader;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.time.Duration;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.HashMap;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.AttemptFingerprint;
import org.xar.ck3.control.reconciliation.LateOutcome.*;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockCustodyGuard.Role;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockCustodyGuard.Source;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockPinnedFiles.Pin;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderPorts.*;
import static org.junit.jupiter.api.Assertions.*;

/** Actual file adapter + original-row producer fixture. No live Game or native qualification is implied. */
class ClockReaderTest {
    @TempDir Path temporary;
    private static final Instant NOW = Instant.parse("2026-10-22T14:00:00Z");
    private static CrossJsDecimalUInt64 u(long value) { return new CrossJsDecimalUInt64(Long.toString(value)); }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static byte[] resource(String name) throws IOException {
        try (var input = ClockReaderTest.class.getResourceAsStream("/clockreader/" + name)) {
            assertNotNull(input); return input.readAllBytes();
        }
    }
    private static ObjectNode object(byte[] raw) { return (ObjectNode) StrictJson.parse(raw); }
    private static ObjectNode json(String value) { return object(bytes(value)); }
    private static byte[] wire(JsonNode row) { return bytes(row.toString()); }
    private static ObjectNode at(ObjectNode row, String path) { return (ObjectNode) row.at(path); }
    private static ObjectNode body(ReadKind kind) throws IOException {
        if (kind == ReadKind.CURRENT_SEMANTIC_FRAME) { return object(resource("synthetic-late-semantic.json")); }
        ObjectNode result = StrictJson.object(); result.put("step", ClockMcpRowDecoder.STATUS_STEP);
        result.put("accepted", true); result.put("status", "available");
        result.set("tactical_daily_sentinel", object(resource("synthetic-late-status.json"))); return result;
    }
    private static ObjectNode originalRow(long sequence, ReadKind kind, ObjectNode payload) {
        ObjectNode row = StrictJson.object(); ObjectNode request = row.putObject("request");
        request.put("sequence", sequence); request.put("tool", ClockMcpRowDecoder.tool(kind)); request.putObject("arguments");
        ObjectNode result = row.putObject("result"); result.put("result_type", "complete"); result.put("is_error", false); result.set("structured_content", payload);
        ObjectNode text = result.putArray("content").addObject(); text.put("type", "text"); text.put("text", payload.toString());
        row.put("elapsed_seconds", 0.125); return row;
    }
    static final class Time implements TimeSource {
        Instant base = NOW;
        boolean realDelay;
        long elapsed;
        private SystemTimeSource processTime = new SystemTimeSource();
        CheckedAction onWait = () -> { };
        void startRealTime() {
            processTime = new SystemTimeSource(); realDelay = true; elapsed = 0; base = processTime.now().utc();
        }
        @Override public Tick now() {
            if (realDelay) { Tick measured = processTime.now(); elapsed = measured.elapsedMillis(); return measured; }
            return new Tick(elapsed, base.plusMillis(elapsed));
        }
        @Override public void waitMillis(long millis) throws InterruptedException {
            if (realDelay) { processTime.waitMillis(millis); } else { elapsed += millis; }
            try { onWait.run(); } catch (IOException error) { throw new IllegalStateException(error); }
        }
    }
    @FunctionalInterface interface CheckedAction { void run() throws IOException; }
    final class Fixture {
        final Path root;
        final Time time = new Time();
        final EnumMap<Role, Pin> pins = new EnumMap<>(Role.class);
        final Attempt attempt;
        final Pin manifest;
        final Set<String> served = new HashSet<>();
        final List<String> tools = new ArrayList<>();
        final ClockCustodyGuard guard;
        String currentMachine = "synthetic-machine";
        boolean processClosed;
        boolean replyEnabled = true;
        boolean unpaused;
        boolean firstArmed;
        boolean repeatSequence;
        boolean wrongSession;
        boolean driftAfterLastRead;
        long sequence = 11558;
        int measurements;
        Fixture() throws IOException { this("channel", new ProcessIdentity(23456, u(2000)), false); }
        Fixture(String channelName, ProcessIdentity queueIdentity, boolean realTime) throws IOException {
            this(channelName, queueIdentity, realTime, null);
        }
        /** An external head is only for binding the existing actual writer fixture in lock-refusal tests. */
        Fixture(String channelName, ProcessIdentity queueIdentity, boolean realTime, Pin externalExpectedHead) throws IOException {
            if (realTime) { time.startRealTime(); }
            root = Files.createDirectory(temporary.resolve(channelName));
            for (String name : List.of("requests", "replies", "originals", "guards", "receipts")) { Files.createDirectory(root.resolve(name)); }
            Path sourceRoot = Files.createDirectory(temporary.resolve("source"));
            Path executable = sourceRoot.resolve("process.exe"); Files.write(executable, bytes("synthetic binary only"));
            for (Role role : Role.values()) {
                if (role == Role.EXPECTED_HEAD && externalExpectedHead != null) { pins.put(role, externalExpectedHead); continue; }
                Path path = role == Role.GAME_EXECUTABLE || role == Role.QUEUE_EXECUTABLE || role == Role.APPLICATION_EXECUTABLE
                        ? executable : sourceRoot.resolve(role.name() + ".json");
                if (!Files.exists(path)) { Files.write(path, bytes(role == Role.MACHINE_RECEIPT ? "{\"machine_id\":\"synthetic-machine\"}" : "{\"fixture\":\"" + role + "\"}")); }
                pins.put(role, ClockPinnedFiles.capture(path.toAbsolutePath(), ClockPinnedFiles.hash(Files.readAllBytes(path)), 65_536));
            }
            Scope scope = new Scope("synthetic-machine", new ProcessIdentity(12345, u(1000)), queueIdentity,
                    new ProcessIdentity(34567, u(3000)), "same-original-session-token",
                    new SourceBinding(pins.get(Role.CLOSURE).sha256(), pins.get(Role.JAVA_BUILD).sha256(), pins.get(Role.PROVIDER).sha256(),
                            pins.get(Role.GAME_EXECUTABLE).sha256(), pins.get(Role.QUALIFICATION).sha256()), 1, 40526, "synthetic-episode", new WorldIdentity(u(111), u(222)));
            attempt = new Attempt(scope, new OriginalFailure(ref(Role.ORIGINAL_FAILURE), 11543, 11558, false, false),
                    new Arm(u(1), 53279400, 53279424, 3, Mode.TERMINAL_OR_SENTINEL, List.of(), 0), ref(Role.EXPECTED_HEAD), 3, u(101), u(201));
            List<Source> sources = pins.entrySet().stream().map(entry -> new Source(entry.getKey(), entry.getValue())).toList();
            guard = new ClockCustodyGuard(attempt, sources, pid -> {
                measurements++; if (processClosed) { throw new IOException("fixture kernel process exited"); }
                ProcessIdentity identity = pid == 12345 ? scope.game() : pid == scope.queue().pid() ? scope.queue() : scope.application();
                return new ProcessObservation(identity, executable.toAbsolutePath(), u(900100 + time.now().elapsedMillis()));
            }, () -> currentMachine);
            ObjectNode channel = StrictJson.object(); channel.put("schema", "xar.clock-fixed-reader-channel/v1");
            channel.put("machine_id", scope.machineId()); channel.put("session_id", scope.sessionId());
            channel.put("attempt_sha256", AttemptFingerprint.sha256(attempt)); channel.put("source_closure_sha256", scope.source().closureSha256());
            identities(channel, "game", scope.game()); identities(channel, "queue", scope.queue()); identities(channel, "application", scope.application());
            channel.put("lease_deadline_utc", time.base.plusSeconds(60).toString());
            Path manifestPath = root.resolve("CHANNEL.json"); Files.write(manifestPath, wire(channel));
            manifest = ClockPinnedFiles.capture(manifestPath.toAbsolutePath(), ClockPinnedFiles.hash(wire(channel)), 16_384);
            time.onWait = this::serve;
        }
        private ContentEvidenceRef ref(Role role) { Pin pin = pins.get(role); return new ContentEvidenceRef(pin.sha256(), pin.bytes(), role.name()); }
        private void identities(ObjectNode row, String prefix, ProcessIdentity value) {
            row.put(prefix + "_pid", value.pid()); row.put(prefix + "_creation_filetime", value.creationFiletime().decimal());
        }
        OriginalQueueFileReader open() throws IOException { return new OriginalQueueFileReader(root.toAbsolutePath(), manifest, attempt, guard, time); }
        Budget budget() { return new Budget(5000, 8, 2000, 0, time.base.plusSeconds(5)); }
        void serve() throws IOException {
            if (!replyEnabled) { return; }
            try (var requests = Files.newDirectoryStream(root.resolve("requests"), "*.json")) {
                for (Path path : requests) {
                    ObjectNode request = object(Files.readAllBytes(path)); String ticket = request.get("ticket").textValue();
                    if (!served.add(ticket)) { continue; }
                    ReadKind kind = ReadKind.valueOf(request.get("read_kind").textValue());
                    tools.add(ClockMcpRowDecoder.tool(kind)); if (!repeatSequence || sequence == 11558) { sequence++; }
                    ObjectNode payload = body(kind);
                    if (firstArmed && served.size() == 1) {
                        ObjectNode slot = at(payload, "/tactical_daily_sentinel"); slot.put("state", "armed"); slot.put("trigger_flags", 0);
                        slot.putArray("trigger_reasons"); slot.put("pause_observed", false); slot.put("trigger_date_raw", 0); slot.put("overshoot_days", -1);
                    }
                    if (unpaused && kind == ReadKind.CURRENT_SEMANTIC_FRAME) { payload.put("paused", false); at(payload, "/diagnostics/last_heartbeat/main_thread_query_mailbox_v1").put("paused", false); }
                    ObjectNode reply = StrictJson.object(); reply.put("schema", "xar.clock-fixed-read-reply/v1");
                    for (String key : List.of("ticket", "read_kind", "attempt_sha256", "session_id", "source_closure_sha256", "original_auto_sequence", "original_failure_sha256")) { reply.set(key, request.get(key)); }
                    if (wrongSession) { reply.put("session_id", "different-session"); }
                    reply.put("read_sequence", sequence); reply.set("original_row", artifact("originals/" + ticket + ".json", wire(originalRow(sequence, kind, payload))));
                    for (String phase : List.of("before", "after")) {
                        ObjectNode observation = StrictJson.object(); observation.put("schema", "xar.clock-fixed-reader-source-observation/v1");
                        observation.put("phase", phase); observation.put("read_sequence", sequence); observation.put("session_id", attempt.scope().sessionId());
                        observation.put("attempt_sha256", AttemptFingerprint.sha256(attempt)); observation.putObject("original_guard").put("fixture_only", true);
                        reply.set("guard_" + phase, artifact("guards/" + ticket + "-" + phase + ".json", wire(observation)));
                    }
                    Files.write(root.resolve("replies").resolve(ticket + ".json"), wire(reply));
                    if (driftAfterLastRead && served.size() == 3) { processClosed = true; }
                }
            }
        }
        private ObjectNode artifact(String name, byte[] raw) throws IOException {
            Files.write(root.resolve(name), raw); ObjectNode descriptor = StrictJson.object(); descriptor.put("path", name);
            descriptor.put("bytes", raw.length); descriptor.put("sha256", ClockPinnedFiles.hash(raw)); return descriptor;
        }
    }

    @Test void actualFileAdapterProducesBoundedThreeReadProposalAndPreservesOriginalFailure() throws Exception {
        Fixture f = new Fixture(); byte[] original = Files.readAllBytes(f.pins.get(Role.ORIGINAL_FAILURE).path());
        try (var reader = f.open()) {
            var result = new ClockReaderApplication(reader, f.time).run(f.attempt, f.budget(), new ReadLedger(List.of()));
            assertEquals(Outcome.PROPOSED, result.assessment().outcome()); assertEquals(0, result.originalCredit()); assertTrue(result.neverReplay());
            assertEquals(List.of(ClockMcpRowDecoder.STATUS_TOOL, ClockMcpRowDecoder.SEMANTIC_TOOL, ClockMcpRowDecoder.STATUS_TOOL), f.tools);
            assertEquals(List.of(11559L, 11560L, 11561L), result.assessment().observedSequences());
            assertEquals(3, reader.completedReadCount(f.attempt)); assertEquals(3, result.ledger().reads().size());
            assertFalse(Files.exists(f.root.resolve("ACTIVE-READ.json"))); assertTrue(f.measurements >= 27);
        }
        assertArrayEquals(original, Files.readAllBytes(f.pins.get(Role.ORIGINAL_FAILURE).path()));
    }
    private static Path repo() {
        String configured = System.getProperty("xar.repo", System.getenv("XAR_REPO_ROOT"));
        if (configured != null) {
            Path exact = Path.of(configured);
            assertTrue(exact.isAbsolute() && Files.isRegularFile(exact.resolve("tools/g2_saved_campaign/current_saved_campaign_preflight_v1.py")),
                    "explicit actual canonical repository fixture root required");
            return exact.normalize();
        }
        Path at = Path.of(System.getProperty("user.dir")).toAbsolutePath();
        while (at != null && !Files.isRegularFile(at.resolve("tools/g2_saved_campaign/current_saved_campaign_preflight_v1.py"))) { at = at.getParent(); }
        assertNotNull(at, "actual canonical producer source is required"); return at;
    }
    private enum ReceiverScenario {
        COMPLETE(3, 3, false), SLOW_GUARD(1, 1, false), MCP_ERROR(1, 1, false), CLIENT_ERROR(1, 1, false),
        FLOAT_STATUS(1, 0, true), FLOAT_SEMANTIC(2, 1, true), NONCOMPLETE(1, 0, true);
        final int submittedReads;
        final int completedReads;
        final boolean rejected;
        ReceiverScenario(int submittedReads, int completedReads, boolean rejected) {
            this.submittedReads = submittedReads; this.completedReads = completedReads; this.rejected = rejected;
        }
    }
    @Test void actualCanonicalPythonReceiverProducesRowsConsumedByJavaFileApplication() throws Exception {
        actualCanonicalReceiver(ReceiverScenario.COMPLETE);
    }
    @Test void actualCanonicalReceiverPreservesCompletedMcpErrorWithoutNewCreditOrReplay() throws Exception {
        actualCanonicalReceiver(ReceiverScenario.MCP_ERROR);
    }
    @Test void actualCanonicalReceiverAllowsGuardInsideUnchangedRealDeadline() throws Exception {
        actualCanonicalReceiver(ReceiverScenario.SLOW_GUARD);
    }
    @Test void actualCanonicalReceiverPreservesClientErrorWithoutNewCreditOrReplay() throws Exception {
        actualCanonicalReceiver(ReceiverScenario.CLIENT_ERROR);
    }
    @Test void actualCanonicalReceiverRetainsRawStatusFloatAndUniqueUnresolvedIntent() throws Exception {
        actualCanonicalReceiver(ReceiverScenario.FLOAT_STATUS);
    }
    @Test void actualCanonicalReceiverRetainsRawSemanticFloatAndUniqueUnresolvedIntent() throws Exception {
        actualCanonicalReceiver(ReceiverScenario.FLOAT_SEMANTIC);
    }
    @Test void actualCanonicalReceiverRejectsNoncompletePinnedMcpResultBeforeNativeFacts() throws Exception {
        actualCanonicalReceiver(ReceiverScenario.NONCOMPLETE);
    }
    private void actualCanonicalReceiver(ReceiverScenario scenario) throws Exception {
        // Only the native body and Game facts are synthetic. The cross-process receiver is the real canonical function.
        String script = """
            import asyncio,copy,json,os,sys,time,uuid
            from importlib.metadata import version
            from datetime import datetime,timezone
            from pathlib import Path
            from types import SimpleNamespace
            from mcp.types import CallToolResult,TextContent
            from tools.g2_saved_campaign import current_saved_campaign_preflight_v1 as core
            assert version('mcp')=='2.0.0' and version('mcp_types')=='2.0.0'
            root=Path(sys.argv[1]); source=Path(sys.argv[2]); scenario=sys.argv[3]; expected_calls=int(sys.argv[4])
            # A Windows venv launcher may own a different PID from this actual Python receiver.
            core._clock_publish_v1(root/'RECEIVER-PROCESS.json',json.dumps({
                'schema':'xar.clock-reader-fixture-process/v1','queue_pid':os.getpid()}).encode())
            until=time.monotonic()+20
            while not (root/'START').exists():
                if time.monotonic()>until: raise TimeoutError('fixture start deadline')
                time.sleep(.01)
            semantic_body=json.loads((source/'synthetic-late-semantic.json').read_bytes())
            status_body=json.loads((source/'synthetic-late-status.json').read_bytes())
            core.current_execution_machine_id_v1=lambda:'synthetic-machine'
            uuid.uuid4=lambda:SimpleNamespace(hex='same-original-session-token')
            class Queue:
                next_sequence=11559
                halted={'request':{'sequence':11558}}
                current_attempt=object()
                full_loop_state=object()
                recording_paused=False
                last_guard_observation=None
                def consume_sequence(self,request:core.JsonObject)->int:
                    assert type(request['sequence']) is int and request['sequence']==self.next_sequence
                    self.next_sequence+=1
                    return request['sequence']
                def call_budget(self,tool:str)->float: return 10.0
            class Session:
                def __init__(self)->None: self.calls:list[str]=[]
                async def call_tool(self,tool:str,arguments:core.JsonObject,*,read_timeout_seconds:float)->CallToolResult:
                    assert arguments=={} and 0<read_timeout_seconds<=10
                    self.calls.append(tool)
                    if scenario=='CLIENT_ERROR': raise TimeoutError('actual receiver fixture transport timeout')
                    if tool==core.SEMANTIC_TOOL:
                        payload=copy.deepcopy(semantic_body)
                        # Native facts remain synthetic, but a frame taken now must have a fresh synthetic heartbeat.
                        began=datetime.fromisoformat((root/'READ-CLOCK-START.txt').read_text().replace('Z','+00:00'))
                        payload['diagnostics']['last_heartbeat']['monotonic_ms']=900000+max(0,int((datetime.now(timezone.utc)-began).total_seconds()*1000))
                        if scenario=='FLOAT_SEMANTIC': payload['native_revision']=3.0
                    else:
                        assert tool=='ck3_read_tactical_daily_sentinel_status_private_v1'
                        payload={'step':'research-query-tactical-daily-sentinel-v1','accepted':True,'status':'available',
                            'tactical_daily_sentinel':copy.deepcopy(status_body)}
                        if scenario=='FLOAT_STATUS': payload['tactical_daily_sentinel']['generation']=1.0
                    result=CallToolResult(is_error=scenario=='MCP_ERROR',structured_content=payload,
                        result_type='input_required' if scenario=='NONCOMPLETE' else 'complete',
                        content=[TextContent(type='text',text=json.dumps(payload))])
                    assert result.model_dump(mode='json')['result_type']==('input_required' if scenario=='NONCOMPLETE' else 'complete')
                    return result
            queue,session=Queue(),Session()
            original_halted,original_attempt,original_state=queue.halted,queue.current_attempt,queue.full_loop_state
            core.bind_java_clock_reader_session_v1(queue,session,runtime_root=root)
            phases=[]
            def guard()->None:
                if scenario=='SLOW_GUARD' and not phases: time.sleep(2.1)
                phases.append({'phase':'original_guard','next_sequence':queue.next_sequence,'monotonic':time.monotonic()})
                queue.last_guard_observation={'fixture_original_guard':'executed','next_sequence':queue.next_sequence}
            async def run()->None:
                # SESSION only binds identity. READY also proves imports, event-loop setup and an actual idle poll.
                try:
                    await core.poll_java_clock_reader_v1(queue,session,runtime_root=root,original_guard=guard,ordinary_pending=False)
                except Exception:
                    print(json.dumps({'phase':'initial_poll_failed','actual_queue_pid':os.getpid(),
                        'channel':json.loads((root/'java-clock-reader'/'CHANNEL.json').read_bytes()),
                        'session':json.loads((root/'java-clock-reader'/'SESSION.json').read_bytes())}),file=sys.stderr,flush=True)
                    raise
                assert not session.calls and queue.next_sequence==11559
                core._clock_publish_v1(root/'RECEIVER-READY.json',json.dumps({
                    'schema':'xar.clock-reader-fixture-ready/v1','queue_pid':os.getpid(),
                    'session_id':'same-original-session-token','next_sequence':queue.next_sequence,
                    'submissions':len(session.calls),'phase':'request-loop-ready'}).encode())
                while not (root/'STOP').exists():
                    if time.monotonic()>until: raise TimeoutError('fixture receiver deadline')
                    before=len(session.calls); began=time.monotonic()
                    try:
                        await core.poll_java_clock_reader_v1(queue,session,runtime_root=root,original_guard=guard,ordinary_pending=False)
                    except Exception:
                        print(json.dumps({'phase':'poll_failed','next_sequence':queue.next_sequence,'phases':phases}),file=sys.stderr,flush=True)
                        raise
                    if len(session.calls)!=before:
                        phases.append({'phase':'fixed_read_published','elapsed_seconds':time.monotonic()-began,'next_sequence':queue.next_sequence})
                    await asyncio.sleep(.005)
                # Re-poll claimed tickets on the real receiver; a read result never authorizes re-submission.
                before=len(session.calls)
                await core.poll_java_clock_reader_v1(queue,session,runtime_root=root,original_guard=guard,ordinary_pending=False)
                assert len(session.calls)==before==expected_calls
            asyncio.run(run())
            assert queue.next_sequence==11559+expected_calls and queue.halted is original_halted
            assert queue.halted['request']['sequence']==11558
            assert queue.current_attempt is original_attempt and queue.full_loop_state is original_state
            print(json.dumps({'queue_pid':os.getpid(),'calls':session.calls,'next_sequence':queue.next_sequence,'halt_sequence':11558,'phases':phases}),flush=True)
            """;
        Path repository = repo();
        String configuredPython = System.getProperty("xar.python");
        if (configuredPython == null || configuredPython.isBlank()) { configuredPython = System.getenv("XAR_ORACLE_PYTHON"); }
        Path python = configuredPython == null || configuredPython.isBlank()
                ? repository.resolve("tools/.venv/Scripts/python.exe") : Path.of(configuredPython);
        var environment = new HashMap<>(System.getenv()); environment.put("PYTHONDONTWRITEBYTECODE", "1");
        environment.put("PYTHONPATH", repository + java.io.File.pathSeparator + repository.resolve("ck3_autonomous_player/src"));
        var specification = new WindowsJobProcess.CommandSpec(python.toAbsolutePath(), List.of("-B", "-X", "utf8", "-c", script,
                temporary.toString(), repository.resolve("java/ck3-control/wave2-runtime/src/test/resources/clockreader").toString(),
                scenario.name(), Integer.toString(scenario.submittedReads)),
                repository, environment, temporary.resolve("receiver.stdout.log"), temporary.resolve("receiver.stderr.log"), 512L * 1024 * 1024);
        try (var process = WindowsJobProcess.start(specification)) {
            var launcher = process.identity();
            long identityWaitUntil = System.nanoTime() + Duration.ofSeconds(10).toNanos();
            while (!Files.exists(temporary.resolve("RECEIVER-PROCESS.json"))) {
                assertTrue(process.isRunning(), () -> "receiver exited before identity: " + readLog(temporary.resolve("receiver.stderr.log")));
                assertTrue(System.nanoTime() < identityWaitUntil, "canonical receiver process identity timeout");
                Thread.sleep(10);
            }
            ObjectNode announced = StrictJson.object(StrictJson.parse(Files.readAllBytes(temporary.resolve("RECEIVER-PROCESS.json"))),
                    Set.of("schema", "queue_pid"));
            assertEquals("xar.clock-reader-fixture-process/v1", StrictJson.text(announced.get("schema")));
            long receiverPid = StrictJson.integer(announced.get("queue_pid"), 1, 0xffff_ffffL);
            var identity = WindowsJobProcess.observeLiveProcess(receiverPid).identity();
            assertTrue(receiverPid == launcher.pid() || ProcessHandle.of(receiverPid).flatMap(ProcessHandle::parent)
                    .map(parent -> parent.pid() == launcher.pid()).orElse(false),
                    () -> "actual receiver PID " + receiverPid + " must be managed root PID " + launcher.pid()
                            + " or its observed direct venv child");
            Fixture f = new Fixture("java-clock-reader",
                    new ProcessIdentity(identity.pid(), new CrossJsDecimalUInt64(identity.creationFiletimeDecimal())), true);
            for (String name : List.of("p37-queue", "p37-requests", "p37-responses")) { Files.createDirectory(temporary.resolve(name)); }
            Files.write(temporary.resolve("p37-responses/11558-1-result.json"), Files.readAllBytes(f.pins.get(Role.ORIGINAL_FAILURE).path()));
            f.time.onWait = () -> assertTrue(process.isRunning(),
                    () -> "receiver exited during fixed read: " + readLog(temporary.resolve("receiver.stderr.log")));
            Files.writeString(temporary.resolve("START"), "fixture start");
            long waitUntil = System.nanoTime() + Duration.ofSeconds(10).toNanos();
            while (!Files.exists(temporary.resolve("RECEIVER-READY.json"))) {
                assertTrue(process.isRunning(), () -> "receiver exited; launcher_pid=" + launcher.pid()
                        + "; receiver_pid=" + identity.pid() + ": " + readLog(temporary.resolve("receiver.stderr.log")));
                assertTrue(System.nanoTime() < waitUntil,
                        () -> "canonical receiver startup timeout: " + readLog(temporary.resolve("receiver.stderr.log")));
                Thread.sleep(10);
            }
            ObjectNode ready = StrictJson.object(StrictJson.parse(Files.readAllBytes(temporary.resolve("RECEIVER-READY.json"))),
                    Set.of("schema", "queue_pid", "session_id", "next_sequence", "submissions", "phase"));
            assertEquals("xar.clock-reader-fixture-ready/v1", StrictJson.text(ready.get("schema")));
            assertEquals("request-loop-ready", StrictJson.text(ready.get("phase")));
            assertEquals(identity.pid(), StrictJson.integer(ready.get("queue_pid"), 1, 0xffff_ffffL));
            assertEquals(f.attempt.scope().sessionId(), StrictJson.text(ready.get("session_id")));
            ObjectNode bound = StrictJson.object(StrictJson.parse(Files.readAllBytes(f.root.resolve("SESSION.json"))),
                    Set.of("schema", "machine_id", "session_id", "queue_pid", "observed_at_utc", "qualification"));
            assertEquals("xar.clock-fixed-reader-original-session/v1", StrictJson.text(bound.get("schema")));
            assertEquals(f.attempt.scope().machineId(), StrictJson.text(bound.get("machine_id")));
            assertEquals("session_binding_only", StrictJson.text(bound.get("qualification")));
            StrictJson.utc(StrictJson.text(bound.get("observed_at_utc")));
            assertEquals(identity.pid(), StrictJson.integer(bound.get("queue_pid"), 1, 0xffff_ffffL));
            assertEquals(f.attempt.scope().sessionId(), StrictJson.text(bound.get("session_id")));
            assertEquals(11559, StrictJson.integer(ready.get("next_sequence"), 1, StrictJson.MAX_SAFE_INTEGER));
            assertEquals(0, StrictJson.integer(ready.get("submissions"), 0, 0));
            assertEquals(identity, WindowsJobProcess.observeLiveProcess(receiverPid).identity(),
                    "actual receiver birth/image must remain unchanged from PROCESS through READY");
            // No fixed read has been issued. Start its unchanged 5 s budget only after the real loop is ready.
            f.time.startRealTime();
            Files.writeString(temporary.resolve("READ-CLOCK-START.txt"), f.time.base.toString(), StandardCharsets.UTF_8);
            try (var reader = f.open()) {
                var application = new ClockReaderApplication(reader, f.time);
                if (scenario == ReceiverScenario.SLOW_GUARD) {
                    // Accelerated fixture time could exhaust a real 5 s read after about 2 s of wall time.
                    Read read = reader.read(new ReadCommand(f.attempt, ReadKind.CURRENT_SENTINEL_STATUS,
                            "f".repeat(32), 8192, 5000, f.budget().hardDeadline()));
                    assertInstanceOf(StatusRead.class, read);
                    assertTrue(f.time.now().elapsedMillis() >= 2100);
                    assertFalse(Files.exists(f.root.resolve("ACTIVE-READ.json")));
                } else if (scenario.rejected) {
                    IOException failure = assertThrows(IOException.class,
                            () -> application.run(f.attempt, f.budget(), new ReadLedger(List.of())));
                    assertInstanceOf(ContractViolationException.class, failure.getCause());
                    assertTrue(Files.exists(f.root.resolve("ACTIVE-READ.json")));
                    assertThrows(IOException.class, () -> reader.verifyCustody(f.attempt));
                } else {
                    var result = application.run(f.attempt, f.budget(), new ReadLedger(List.of()));
                    assertEquals(scenario == ReceiverScenario.COMPLETE ? Outcome.PROPOSED : Outcome.UNRESOLVED,
                            result.assessment().outcome());
                    if (scenario != ReceiverScenario.COMPLETE) {
                        assertEquals(Reason.READ_UNAVAILABLE, result.assessment().reason());
                        assertInstanceOf(UnavailableRead.class, result.ledger().reads().get(0));
                        var unchanged = application.run(f.attempt, f.budget(), result.ledger());
                        assertEquals(result.ledger(), unchanged.ledger());
                        assertEquals(Reason.READ_UNAVAILABLE, unchanged.assessment().reason());
                    }
                    assertEquals(0, result.originalCredit()); assertTrue(result.neverReplay());
                    assertFalse(Files.exists(f.root.resolve("ACTIVE-READ.json")));
                }
                assertEquals(scenario.completedReads, reader.completedReadCount(f.attempt));
            } catch (Exception | AssertionError failure) {
                failure.addSuppressed(new AssertionError("canonical receiver diagnostic; elapsed_millis="
                        + f.time.now().elapsedMillis() + "; launcher_pid=" + launcher.pid() + "; receiver_pid=" + identity.pid()
                        + "; stdout=" + readLog(temporary.resolve("receiver.stdout.log"))
                        + "; stderr=" + readLog(temporary.resolve("receiver.stderr.log"))
                        + "; transport=" + receiverArtifacts(f)));
                throw failure;
            } finally { Files.writeString(temporary.resolve("STOP"), "fixture complete"); }
            var ended = process.await(Duration.ofSeconds(10), Instant.now().plusSeconds(10), () -> { });
            assertTrue(ended.passed(), () -> "receiver terminal failure: " + readLog(temporary.resolve("receiver.stderr.log")));
            assertEquals(0, ended.accounting().activeProcesses());
            ObjectNode summary = object(Files.readAllBytes(temporary.resolve("receiver.stdout.log")));
            assertEquals(identity.pid(), StrictJson.integer(summary.get("queue_pid"), 1, 0xffff_ffffL));
            assertEquals(11559 + scenario.submittedReads, summary.get("next_sequence").intValue());
            assertEquals(11558, summary.get("halt_sequence").intValue());
            List<String> expectedTools = scenario == ReceiverScenario.COMPLETE
                    ? List.of(ClockMcpRowDecoder.STATUS_TOOL, ClockMcpRowDecoder.SEMANTIC_TOOL, ClockMcpRowDecoder.STATUS_TOOL)
                    : scenario == ReceiverScenario.FLOAT_SEMANTIC
                    ? List.of(ClockMcpRowDecoder.STATUS_TOOL, ClockMcpRowDecoder.SEMANTIC_TOOL)
                    : List.of(ClockMcpRowDecoder.STATUS_TOOL);
            List<String> actualTools = new ArrayList<>();
            for (JsonNode tool : summary.get("calls")) { actualTools.add(StrictJson.text(tool)); }
            assertEquals(expectedTools, actualTools);
            assertCanonicalReceiverOriginals(f, scenario);
            if (scenario.rejected) {
                try (var restarted = f.open()) { assertThrows(IOException.class, () -> restarted.verifyCustody(f.attempt)); }
            }
        }
    }
    private void assertCanonicalReceiverOriginals(Fixture fixture, ReceiverScenario scenario) throws IOException {
        try (var requests = Files.list(fixture.root.resolve("requests"));
             var originals = Files.list(fixture.root.resolve("originals"))) {
            assertEquals(scenario.submittedReads, requests.count());
            List<Path> rows = originals.toList(); assertEquals(scenario.submittedReads, rows.size());
            for (Path path : rows) {
                byte[] raw = Files.readAllBytes(path); ObjectNode row = object(raw);
                long sequence = row.at("/request/sequence").longValue();
                assertArrayEquals(raw, Files.readAllBytes(temporary.resolve("p37-responses/" + sequence + "-1-result.json")));
                assertFalse(row.get("replay_allowed").booleanValue());
                assertEquals(0, row.get("ordinary_cycle_credit").intValue()); assertEquals(0, row.get("day_credit").intValue());
                ObjectNode reply = object(Files.readAllBytes(fixture.root.resolve("replies/" + path.getFileName())));
                assertEquals(ClockPinnedFiles.hash(raw), reply.at("/original_row/sha256").textValue());
                assertEquals(raw.length, reply.at("/original_row/bytes").intValue());
                if (scenario == ReceiverScenario.CLIENT_ERROR) {
                    assertFalse(row.has("result")); assertTrue(row.get("client_error").textValue().contains("TimeoutError"));
                } else {
                    assertEquals(scenario == ReceiverScenario.NONCOMPLETE ? "input_required" : "complete",
                            row.at("/result/result_type").textValue());
                    assertEquals(scenario == ReceiverScenario.MCP_ERROR, row.at("/result/is_error").booleanValue());
                }
                if (scenario == ReceiverScenario.FLOAT_STATUS || scenario == ReceiverScenario.FLOAT_SEMANTIC
                        && sequence == 11560) {
                    String key = scenario == ReceiverScenario.FLOAT_STATUS ? "generation" : "native_revision";
                    String token = scenario == ReceiverScenario.FLOAT_STATUS ? "1.0" : "3.0";
                    assertTrue(new String(raw, StandardCharsets.UTF_8).contains("\"" + key + "\":" + token),
                            "actual opaque Python serialization must retain the float token rejected by Java");
                }
                assertTrue(Files.exists(fixture.root.resolve("receipts/CLAIM-" + path.getFileName())));
            }
        }
        assertArrayEquals(Files.readAllBytes(fixture.pins.get(Role.ORIGINAL_FAILURE).path()),
                Files.readAllBytes(temporary.resolve("p37-responses/11558-1-result.json")));
    }
    private static String readLog(Path path) {
        try { return Files.readString(path, StandardCharsets.UTF_8); } catch (IOException error) { return error.toString(); }
    }
    private static String receiverArtifacts(Fixture fixture) {
        try (var requests = Files.list(fixture.root.resolve("requests"));
             var originals = Files.list(fixture.root.resolve("originals"));
             var receipts = Files.list(fixture.root.resolve("receipts"))) {
            return "requests=" + requests.map(path -> path.getFileName().toString()).toList()
                    + ", originals=" + originals.map(path -> path.getFileName().toString()).toList()
                    + ", receipts=" + receipts.map(path -> path.getFileName().toString()).toList()
                    + ", active=" + readLog(fixture.root.resolve("ACTIVE-READ.json"));
        } catch (IOException error) { return error.toString(); }
    }
    @Test void armedGuardIsPolledWithoutCancelBeforeLateThreeReadProposal() throws Exception {
        Fixture f = new Fixture(); f.firstArmed = true;
        try (var reader = f.open()) {
            var result = new ClockReaderApplication(reader, f.time).run(f.attempt, f.budget(), new ReadLedger(List.of()));
            assertEquals(Outcome.PROPOSED, result.assessment().outcome()); assertEquals(4, f.tools.size());
            assertEquals(ClockMcpRowDecoder.STATUS_TOOL, f.tools.get(1));
        }
    }
    @Test void unpausedFramesConsumeFiniteBudgetAndDoNotPropose() throws Exception {
        Fixture f = new Fixture(); f.unpaused = true;
        try (var reader = f.open()) {
            var result = new ClockReaderApplication(reader, f.time).run(f.attempt, f.budget(), new ReadLedger(List.of()));
            assertEquals(Outcome.UNRESOLVED, result.assessment().outcome()); assertEquals(Reason.BUDGET_EXHAUSTED, result.assessment().reason());
            assertEquals(8, reader.completedReadCount(f.attempt)); assertFalse(f.tools.stream().anyMatch(tool -> tool.contains("cancel")));
        }
    }
    @Test void timeoutRetainsUniqueIntentAndBlocksReplacementAcrossClientRestart() throws Exception {
        Fixture f = new Fixture(); f.replyEnabled = false;
        try (var reader = f.open()) {
            assertThrows(IOException.class, () -> reader.read(new ReadCommand(f.attempt, ReadKind.CURRENT_SENTINEL_STATUS, "a".repeat(32), 8192, 50, NOW.plusMillis(50))));
            assertThrows(IOException.class, () -> reader.verifyCustody(f.attempt));
        }
        try (var restarted = f.open()) { assertThrows(IOException.class, () -> restarted.verifyCustody(f.attempt)); }
        assertTrue(Files.exists(f.root.resolve("ACTIVE-READ.json")));
        try (var requests = Files.list(f.root.resolve("requests"))) { assertEquals(1, requests.count()); }
    }
    @Test void persistedReadCountCannotBeResetByEmptyCallerHistory() throws Exception {
        Fixture f = new Fixture();
        try (var reader = f.open()) { reader.read(new ReadCommand(f.attempt, ReadKind.CURRENT_SENTINEL_STATUS, "b".repeat(32), 8192, 1000, NOW.plusSeconds(1))); }
        try (var restarted = f.open()) {
            var result = new ClockReaderApplication(restarted, f.time).run(f.attempt, f.budget(), new ReadLedger(List.of()));
            assertEquals(Reason.HISTORY_INCOMPLETE, result.assessment().reason()); assertEquals(1, f.served.size());
        }
    }
    @Test void equalCountForgedCallerHistoryCannotReplaceOriginalReadFacts() throws Exception {
        Fixture f = new Fixture(); Read original;
        try (var reader = f.open()) { original = reader.read(new ReadCommand(f.attempt, ReadKind.CURRENT_SENTINEL_STATUS, "c".repeat(32), 8192, 1000, NOW.plusSeconds(1))); }
        Status actual = ((StatusRead) original).status();
        Status forged = new Status(actual.state(), u(2), actual.startingDateRaw(), actual.targetDateRaw(), actual.lastObservedDateRaw(), actual.triggerDateRaw(),
                actual.speed(), actual.mode(), actual.armyCount(), actual.combatCount(), actual.completedDailyTicks(), actual.intermediatePauseCount(),
                actual.triggerFlags(), actual.triggerReasons(), actual.signedDateDeltaFromTargetRaw(), actual.overshootDays(), actual.pauseWrapperCalled(),
                actual.pauseObserved(), actual.terminalObserved(), actual.abnormal());
        try (var restarted = f.open()) {
            ReadLedger fake = new ReadLedger(List.of(new StatusRead(original.evidence(), forged)));
            assertThrows(IOException.class, () -> new ClockReaderApplication(restarted, f.time).run(f.attempt, f.budget(), fake));
            assertEquals(1, f.served.size());
            restarted.verifyCompleteLedger(f.attempt, new ReadLedger(List.of(original)));
        }
    }
    @Test void changedOriginalArtifactCannotSupplyPreviouslyCollectedFacts() throws Exception {
        Fixture f = new Fixture(); Read original;
        try (var reader = f.open()) { original = reader.read(new ReadCommand(f.attempt, ReadKind.CURRENT_SENTINEL_STATUS, "d".repeat(32), 8192, 1000, NOW.plusSeconds(1))); }
        Files.write(f.root.resolve("originals").resolve("d".repeat(32) + ".json"), bytes("{}"));
        try (var restarted = f.open()) { assertThrows(IOException.class, () -> restarted.verifyCompleteLedger(f.attempt, new ReadLedger(List.of(original)))); }
    }
    @Test void kernelFailureAtFinalCollectionPreservesRawReplyAndNoProposal() throws Exception {
        Fixture f = new Fixture(); f.driftAfterLastRead = true;
        try (var reader = f.open()) { assertThrows(IOException.class, () -> new ClockReaderApplication(reader, f.time).run(f.attempt, f.budget(), new ReadLedger(List.of()))); }
        assertEquals(3, f.served.size()); assertTrue(Files.exists(f.root.resolve("ACTIVE-READ.json")));
    }
    @Test void actualHostMismatchRejectsBeforeTransport() throws Exception {
        Fixture f = new Fixture(); f.currentMachine = "another-machine";
        assertThrows(IOException.class, f::open); assertTrue(f.served.isEmpty());
    }
    @Test void changedPinnedSourceRejectsBeforeTransport() throws Exception {
        Fixture f = new Fixture(); Files.write(f.pins.get(Role.QUEUE_SOURCE).path(), bytes("changed source"));
        assertThrows(IOException.class, f::open); assertTrue(f.served.isEmpty());
    }
    @Test void sessionDriftAndRepeatedOwnerSequenceRetainUnresolvedIntent() throws Exception {
        Fixture f = new Fixture(); f.wrongSession = true;
        try (var reader = f.open()) { assertThrows(IOException.class, () -> new ClockReaderApplication(reader, f.time).run(f.attempt, f.budget(), new ReadLedger(List.of()))); }
        assertTrue(Files.exists(f.root.resolve("ACTIVE-READ.json")));
    }
    @Test void repeatedOwnerSequenceIsNotDeduplicated() throws Exception {
        Fixture f = new Fixture(); f.repeatSequence = true;
        try (var reader = f.open()) { assertThrows(IOException.class, () -> new ClockReaderApplication(reader, f.time).run(f.attempt, f.budget(), new ReadLedger(List.of()))); }
        assertEquals(2, f.served.size()); assertTrue(Files.exists(f.root.resolve("ACTIVE-READ.json")));
    }
    @Test void twoClientsCannotBorrowOriginalQueueAtOnce() throws Exception {
        Fixture f = new Fixture();
        try (var reader = f.open()) { assertThrows(IOException.class, f::open); assertEquals(0, reader.completedReadCount(f.attempt)); }
    }
    @Test void anEqualManifestAtAnotherPathDoesNotMeasureThisChannel() throws Exception {
        Fixture f = new Fixture(); Path copy = temporary.resolve("different-channel.json");
        byte[] raw = Files.readAllBytes(f.manifest.path()); Files.write(copy, raw);
        Pin other = ClockPinnedFiles.capture(copy.toAbsolutePath(), ClockPinnedFiles.hash(raw), 16_384);
        assertThrows(IOException.class, () -> new OriginalQueueFileReader(f.root.toAbsolutePath(), other, f.attempt, f.guard, f.time));
    }
    private Evidence evidence(Fixture f) { return new Evidence(f.attempt.scope(), f.attempt.scope(), 11559,
            new ContentEvidenceRef("a".repeat(64), 1, "raw-fixture"), 100, NOW.plusMillis(100), u(900100)); }
    @Test void originalSemanticProjectionDecodesExactSelectedProducerFacts() throws Exception {
        Fixture f = new Fixture(); ObjectNode projected = object(resource("original-n46-11541.semantic-projection.json"));
        ObjectNode payload = (ObjectNode) projected.get("payload");
        SemanticRead read = (SemanticRead) ClockMcpRowDecoder.decode(wire(originalRow(11559, ReadKind.CURRENT_SEMANTIC_FRAME, payload)), ReadKind.CURRENT_SEMANTIC_FRAME, evidence(f), 8192);
        assertEquals(50688, read.semantic().bridgePid()); assertEquals(53279400, read.semantic().dateRaw());
        assertEquals("54202", read.semantic().verifiedPumpEpoch().decimal()); assertEquals("1895661937", read.semantic().heartbeatMillis().decimal());
        assertEquals("e08df7791ec19d651200f384654f6924f8a7d2e1500451b7f6e233f951ca2057", projected.get("source_sha256").textValue());
    }
    @Test void rawFloatCriticalTokenCannotNormalizeIntoValidInteger() throws Exception {
        Fixture f = new Fixture(); byte[] valid = wire(originalRow(11559, ReadKind.CURRENT_SENTINEL_STATUS, body(ReadKind.CURRENT_SENTINEL_STATUS)));
        for (String token : List.of("1.0", "1e0", "true", "\"1\"", "null")) {
            byte[] invalid = bytes(new String(valid, StandardCharsets.UTF_8).replace("\"generation\":1,", "\"generation\":" + token + ","));
            assertThrows(ContractViolationException.class, () -> ClockMcpRowDecoder.decode(invalid, ReadKind.CURRENT_SENTINEL_STATUS, evidence(f), 8192), token);
        }
    }
    @Test void pinnedMcpModelRequiresTextualCompleteBeforeNativeOrErrorDecoding() throws Exception {
        Fixture f = new Fixture();
        for (ReadKind kind : List.of(ReadKind.CURRENT_SENTINEL_STATUS, ReadKind.CURRENT_SEMANTIC_FRAME)) {
            ObjectNode row = originalRow(11559, kind, body(kind));
            Class<? extends Read> expectedType = kind == ReadKind.CURRENT_SENTINEL_STATUS ? StatusRead.class : SemanticRead.class;
            assertInstanceOf(expectedType, ClockMcpRowDecoder.decode(wire(row), kind, evidence(f), 8192));
            for (boolean isError : List.of(false, true)) {
                at(row, "/result").put("is_error", isError);
                String completed = new String(wire(row), StandardCharsets.UTF_8);
                for (String token : List.of("\"input_required\"", "\"task\"", "\"extension\"", "null", "true", "false", "1", "1.0", "1e0")) {
                    byte[] invalid = bytes(completed.replace("\"result_type\":\"complete\"", "\"result_type\":" + token));
                    assertThrows(ContractViolationException.class,
                            () -> ClockMcpRowDecoder.decode(invalid, kind, evidence(f), 8192), kind + ": " + token + ", is_error=" + isError);
                }
                byte[] missing = bytes(completed.replace("\"result_type\":\"complete\",", ""));
                assertThrows(ContractViolationException.class,
                        () -> ClockMcpRowDecoder.decode(missing, kind, evidence(f), 8192), kind + ": missing, is_error=" + isError);
            }
        }
    }
    @Test void completedMcpErrorRemainsUnavailable() throws Exception {
        Fixture f = new Fixture();
        for (ReadKind kind : List.of(ReadKind.CURRENT_SENTINEL_STATUS, ReadKind.CURRENT_SEMANTIC_FRAME)) {
            ObjectNode row = originalRow(11559, kind, body(kind)); at(row, "/result").put("is_error", true);
            assertInstanceOf(UnavailableRead.class, ClockMcpRowDecoder.decode(wire(row), kind, evidence(f), 8192));
        }
    }
    @Test void textAndStructuredDisagreementWrongToolAndArgumentsAreRejected() throws Exception {
        Fixture f = new Fixture(); ObjectNode row = originalRow(11559, ReadKind.CURRENT_SENTINEL_STATUS, body(ReadKind.CURRENT_SENTINEL_STATUS));
        at(row, "/result/structured_content/tactical_daily_sentinel").put("generation", 2);
        assertThrows(ContractViolationException.class, () -> ClockMcpRowDecoder.decode(wire(row), ReadKind.CURRENT_SENTINEL_STATUS, evidence(f), 8192));
        at(row, "/request").put("tool", "ck3_execute_step");
        assertThrows(ContractViolationException.class, () -> ClockMcpRowDecoder.decode(wire(row), ReadKind.CURRENT_SENTINEL_STATUS, evidence(f), 8192));
        at(row, "/request").put("tool", ClockMcpRowDecoder.STATUS_TOOL); at(row, "/request/arguments").put("step", "resume-map");
        assertThrows(ContractViolationException.class, () -> ClockMcpRowDecoder.decode(wire(row), ReadKind.CURRENT_SENTINEL_STATUS, evidence(f), 8192));
    }
    @Test void unavailableOriginalTransportCannotBecomeEmptySuccessOrRetry() throws Exception {
        Fixture f = new Fixture(); ObjectNode row = originalRow(11559, ReadKind.CURRENT_SENTINEL_STATUS, body(ReadKind.CURRENT_SENTINEL_STATUS));
        row.remove("result"); row.put("client_error", "original timeout"); row.put("replay_allowed", false);
        assertInstanceOf(UnavailableRead.class, ClockMcpRowDecoder.decode(wire(row), ReadKind.CURRENT_SENTINEL_STATUS, evidence(f), 8192));
        row.putObject("result").put("result_type", "input_required");
        assertInstanceOf(UnavailableRead.class, ClockMcpRowDecoder.decode(wire(row), ReadKind.CURRENT_SENTINEL_STATUS, evidence(f), 8192));
        row.put("replay_allowed", true);
        assertThrows(ContractViolationException.class, () -> ClockMcpRowDecoder.decode(wire(row), ReadKind.CURRENT_SENTINEL_STATUS, evidence(f), 8192));
    }
    @Test void artifactTraversalNullKindAndMissingMcpContentAreRejected() throws Exception {
        for (String path : List.of("../outside", "guards/../../outside", "/outside", "C:/outside", "guards//x")) {
            assertThrows(ContractViolationException.class, () -> new ClockQueueProtocol.Artifact(path, 1, "a".repeat(64)));
        }
        assertThrows(NullPointerException.class, () -> ClockMcpRowDecoder.tool(null));
        Fixture f = new Fixture(); ObjectNode row = originalRow(11559, ReadKind.CURRENT_SENTINEL_STATUS, body(ReadKind.CURRENT_SENTINEL_STATUS));
        at(row, "/result").remove("content");
        assertThrows(ContractViolationException.class, () -> ClockMcpRowDecoder.decode(wire(row), ReadKind.CURRENT_SENTINEL_STATUS, evidence(f), 8192));
    }
}
