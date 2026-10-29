package org.xar.ck3.control.g2.context;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.RootSoftwareChildBootstrap;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;

/** Actual child/kernel/HTTP proof only. The JDK server is a test fixture, never the qualified Quarkus host. */
final class RootSoftwareChildTransportTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final String ORIGINAL_REQUEST_SHA = "bc066714ee3882d72e4b94b1b234f16390d274bb3eb90bbaa1adeb67b7869738";
    @Test void actualIndependentChildrenConsumeRootIssuedRequestOnce() throws Exception {
        Path root = root("-handoff02");
        byte[] original;
        try (var input = getClass().getResourceAsStream("/g2-context/evaluate-request.json")) {
            if (input == null) { throw new IllegalStateException("actual original producer request resource required"); }
            original = input.readAllBytes();
        }
        assertEquals(ORIGINAL_REQUEST_SHA, G2RetainedNativeSourceProvider.sha256(original));
        Path requestFile = root.resolve("actual-original-producer-request.json"); Files.write(requestFile, original);
        G2Request request = G2Wire.decodeRequest(original);
        Path payloadFile = root.resolve("exact-derived-original-payload.json"); Files.write(payloadFile, request.payload().bytes());
        // This visibly fixture-only document cannot qualify load_java_projection_service_v1.
        ObjectNode fixtureProgram = StrictJson.object(); fixtureProgram.put("schema", "xar.software-transport-test-program/v1");
        fixtureProgram.put("scope", "NOT_A_QUALIFIED_SERVICE_PROGRAM");
        Path classFile = Path.of(G2SoftwareFixtureSourceProvider.class.getResource("G2SoftwareFixtureSourceProvider.class").toURI());
        fixtureProgram.set("actual_loaded_class_ref", exact(classFile).toJson());
        Path programFile = root.resolve("transport-fixture-program.json"); Files.write(programFile, StrictJson.canonical(fixtureProgram));
        G2SoftwareFixtureSourceProvider.Origin origin = new G2SoftwareFixtureSourceProvider.Origin(WindowsJobProcess.currentMachineId(),
                Instant.now().toString(), exact(programFile), List.of(exact(classFile)), List.of(exact(requestFile)), List.of(request.milestone()),
                exact(requestFile), exact(payloadFile), request.milestone());
        Path originFile = root.resolve("software-transport-origin.json");
        G2SoftwareFixtureSourceProvider provider = G2SoftwareFixtureSourceProvider.load(G2SoftwareFixtureSourceProvider.writeOrigin(origin, originFile));
        RootG2RequestHandoff custody = new RootG2RequestHandoff(8);
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext(RootG2HandoffWire.HTTP_PATH, exchange -> {
            byte[] body; int status;
            try {
                RootG2HandoffWire.Input input = RootG2HandoffWire.decode(exchange.getRequestBody().readNBytes(RootG2HandoffWire.MAX_INPUT_BYTES + 1));
                G2CallContextProducer.Result result = custody.redeem(input.ticketId(), input.childPid(), input.childCreationFiletimeDecimal(), input.milestone(), input.payload());
                if (result instanceof G2CallContextProducer.Available available) { status = 200; body = G2CallContextWire.encodeContext(available.context()); }
                else { status = 503; body = G2Wire.encodeError(new G2HttpError(G2HttpError.SCHEMA, G2HttpError.Code.ENGINE_UNAVAILABLE, "source unavailable")); }
            } catch (IOException | RuntimeException error) { status = 400; body = "{}".getBytes(StandardCharsets.UTF_8); }
            exchange.sendResponseHeaders(status, body.length); exchange.getResponseBody().write(body); exchange.close();
        });
        server.start();
        String priorTicket = null;
        try {
            for (int index = 0; index < 2; index++) {
                Path run = root.resolve("independent-child-" + index); Files.createDirectory(run);
                Path hello = run.resolve("hello.json"), ticketFile = run.resolve("root-issued-ticket.json");
                String source = """
                    import hashlib,http.client,json,os,pathlib,sys,time
                    hello,ticket,payload,port=sys.argv[1:]
                    hello_tmp=pathlib.Path(hello+'.complete'); hello_tmp.write_text(json.dumps({'pid':os.getpid()}),encoding='utf-8'); hello_tmp.replace(hello)
                    until=time.monotonic()+10
                    while not pathlib.Path(ticket).exists():
                        if time.monotonic()>until:raise RuntimeError('Root ticket not issued')
                        time.sleep(.01)
                    claim=json.loads(pathlib.Path(ticket).read_bytes()); raw=pathlib.Path(payload).read_bytes()
                    request=json.dumps(claim,separators=(',',':')).encode('utf-8')[:-1]+b',"payload":'+raw+b'}'
                    outcomes=[]
                    for expected in (200,503):
                        connection=http.client.HTTPConnection('127.0.0.1',int(port),timeout=5)
                        connection.request('POST','/v1/g2-research/context/handoff',request,{'Content-Type':'application/json'})
                        response=connection.getresponse();body=response.read();status=response.status;connection.close()
                        if status!=expected:raise AssertionError((status,expected,body))
                        if status==200:
                            context=json.loads(body)
                            if context['payload_sha256']!=hashlib.sha256(raw).hexdigest():raise AssertionError('payload changed')
                            if not context['source']['exact_build'].startswith('SOFTWARE_FIXTURE@sha256:'):raise AssertionError('scope changed')
                        outcomes.append(status)
                    print(json.dumps({'scope':'SOFTWARE_TRANSPORT_TEST_ONLY','pid':os.getpid(),'outcomes':outcomes}))
                    """;
                WindowsJobProcess.CommandSpec command = command(run, List.of("-I", "-S", "-B", "-X", "utf8", "-c", source,
                        hello.toString(), ticketFile.toString(), payloadFile.toString(), Integer.toString(server.getAddress().getPort())));
                try (WindowsJobProcess child = WindowsJobProcess.start(command, WindowsJobProcess.ConsoleMode.NO_WINDOW)) {
                    awaitFile(hello);
                    long pid = StrictJson.integer(StrictJson.parse(Files.readAllBytes(hello)).get("pid"), 1, 0xffff_ffffL);
                    RootG2RequestHandoff.Ticket ticket = custody.issueSoftware(provider, pid, request.milestone(), request.payload(), Instant.now().plusSeconds(15));
                    assertEquals(RootG2RequestHandoff.Scope.SOFTWARE_FIXTURE_ONLY, ticket.scope());
                    if (priorTicket != null) { assertTrue(!priorTicket.equals(ticket.ticketId())); } priorTicket = ticket.ticketId();
                    ObjectNode claim = StrictJson.object(); claim.put("ticket_id", ticket.ticketId()); claim.put("child_pid", ticket.childPid());
                    claim.put("child_creation_filetime_decimal", ticket.childCreationFiletimeDecimal()); claim.put("milestone", "G2-" + ticket.milestone().name());
                    Path completeTicket = ticketFile.resolveSibling("root-issued-ticket.complete");
                    Files.write(completeTicket, StrictJson.canonical(claim));
                    Files.move(completeTicket, ticketFile, java.nio.file.StandardCopyOption.ATOMIC_MOVE);
                    WindowsJobProcess.CommandResult result = child.await(Duration.ofSeconds(20), Instant.now().plusSeconds(25), () -> { });
                    retainResult(run, result); assertTrue(result.passed(), "actual child exit/timeout/whole Job must pass");
                    assertEquals(0, result.accounting().activeProcesses());
                    assertTrue(Files.readString(run.resolve("stdout.log")).contains("[200, 503]"));
                }
            }
        } finally { server.stop(0); }
        RootG2RequestHandoff.Ticket wrong = custody.issueSoftware(provider, ProcessHandle.current().pid(), request.milestone(), request.payload(), Instant.now().plusSeconds(10));
        assertTrue(custody.redeem(wrong.ticketId(), wrong.childPid(), "1", request.milestone(), request.payload()) instanceof G2CallContextProducer.Unavailable);
        assertTrue(custody.redeem(wrong.ticketId(), wrong.childPid(), wrong.childCreationFiletimeDecimal(), request.milestone(), request.payload()) instanceof G2CallContextProducer.Unavailable);
        byte[] malformed = ("{\"ticket_id\":\"" + "0".repeat(64) + "\",\"child_pid\":true,\"child_creation_filetime_decimal\":\"1\",\"milestone\":\"G2-M1\",\"payload\":{}}").getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> RootG2HandoffWire.decode(malformed));
        assertArrayEquals(request.payload().bytes(), Files.readAllBytes(payloadFile));
    }
    @Test void invalidBootstrapFailsInActualChildBeforeCanonicalImports() throws Exception {
        Path root = root("-bootstrap-reject02");
        Path invalid = root.resolve("invalid-explicit-bootstrap.json"); Files.writeString(invalid, "{\"schema\":\"xar.root-software-child-bootstrap/v1\",\"scope\":\"LIVE\"}");
        String prelude = "import json,sys\nroot_bootstrap_ref=json.loads(sys.argv[1])\n";
        String body = prelude + "try:\n" + RootSoftwareChildBootstrap.pythonPrefix().indent(4)
                + "except RuntimeError:\n    assert 'tools.g2_saved_campaign.java_map_admission_client_v1' not in sys.modules\n    print('BOOTSTRAP_REJECTED_BEFORE_CANONICAL_IMPORTS')\nelse:\n    raise AssertionError('invalid bootstrap was accepted')\nfinally:\n    if '_xar_root_stack' in globals(): _xar_root_stack.close()\n";
        String reference = JSON.writeValueAsString(ControlBuild.FileRef.measure(invalid));
        try (WindowsJobProcess child = WindowsJobProcess.start(command(root, List.of("-I", "-S", "-B", "-X", "utf8", "-c", body, reference)), WindowsJobProcess.ConsoleMode.NO_WINDOW)) {
            WindowsJobProcess.CommandResult result = child.await(Duration.ofSeconds(15), Instant.now().plusSeconds(20), () -> { });
            retainResult(root, result); assertTrue(result.passed()); assertEquals(0, result.accounting().activeProcesses());
            assertTrue(Files.readString(root.resolve("stdout.log")).contains("BOOTSTRAP_REJECTED_BEFORE_CANONICAL_IMPORTS"));
        }
    }
    @Test void directPythonConsoleModesRetainActualStreamsAndExpectedExitOne() throws Exception {
        Path root = root("-direct-python-modes02");
        for (WindowsJobProcess.ConsoleMode mode : List.of(WindowsJobProcess.ConsoleMode.DETACHED, WindowsJobProcess.ConsoleMode.NO_WINDOW)) {
            Path run = root.resolve(mode.name()); Files.createDirectory(run);
            String body = "import sys;print('ROOT_DIRECT_STDOUT');print('ROOT_DIRECT_STDERR',file=sys.stderr);sys.exit(1)";
            try (WindowsJobProcess child = WindowsJobProcess.start(command(run, List.of("-I", "-S", "-B", "-c", body)), mode)) {
                WindowsJobProcess.CommandResult actual = child.await(Duration.ofSeconds(10), Instant.now().plusSeconds(15), () -> { });
                retainResult(run, actual);
                assertEquals(1, actual.exitCode(), "raw diagnostic child exit1 is retained, never recast as ordinary child PASS");
                assertEquals(0, actual.accounting().activeProcesses());
                if (mode == WindowsJobProcess.ConsoleMode.NO_WINDOW) {
                    assertTrue(Files.readString(run.resolve("stdout.log")).contains("ROOT_DIRECT_STDOUT"));
                    assertTrue(Files.readString(run.resolve("stderr.log")).contains("ROOT_DIRECT_STDERR"));
                }
            }
        }
    }
    private static Path root(String suffix) throws IOException {
        String base = System.getProperty("xar.rootContext.testRoot");
        if (base == null || base.isBlank()) { throw new IllegalStateException("explicit bounded rootContext testRoot required"); }
        Path root = Path.of(base + suffix).toAbsolutePath().normalize(); Files.createDirectory(root); return root;
    }
    private static WindowsJobProcess.CommandSpec command(Path root, List<String> args) {
        String python = System.getProperty("xar.rootContext.pythonExecutable");
        if (python == null || python.isBlank()) { throw new IllegalStateException("explicit actual Python executable required"); }
        return new WindowsJobProcess.CommandSpec(Path.of(python).toAbsolutePath().normalize(), args, root,
                Map.copyOf(System.getenv()), root.resolve("stdout.log"), root.resolve("stderr.log"), 64 * 1024 * 1024);
    }
    private static void awaitFile(Path file) throws Exception {
        Instant deadline = Instant.now().plusSeconds(10);
        while (!Files.exists(file)) { if (!Instant.now().isBefore(deadline)) { throw new IOException("actual child did not publish hello"); } Thread.sleep(5); }
    }
    private static void retainResult(Path root, WindowsJobProcess.CommandResult result) throws IOException {
        ObjectNode row = StrictJson.object(); row.put("schema", "xar.root-software-transport-child/v1"); row.put("machine_id", WindowsJobProcess.currentMachineId());
        row.put("observed_at_utc", Instant.now().toString()); row.put("scope", "SOFTWARE_TRANSPORT_ONLY_NOT_QUALIFIED_QUARKUS_SDK");
        row.set("result", JSON.valueToTree(result)); Files.write(root.resolve("actual-native-child.json"), JSON.writeValueAsBytes(row));
    }
    private static ExactRef exact(Path path) throws IOException {
        ControlBuild.FileRef ref = ControlBuild.FileRef.measure(path); return new ExactRef(ref.path(), ref.bytes(), ref.sha256());
    }
}
