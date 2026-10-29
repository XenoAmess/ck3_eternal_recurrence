package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.NativeArchiveDataCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.*;
import org.xar.ck3.control.nativebridge.capabilities.religion.*;
import org.xar.ck3.control.service.mcp.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionContract.*;

/**
 * Required original DATA -> sole archive codec -> original contract replay -> real public
 * formatter -> actual Root bindings -> original SDK directory. Never constructs Root, Core,
 * writer, transport, HELLO, Complete or a live read permit. Missing originals fail, never skip.
 */
final class ReligionMasterPublicSdkParityTest {
    private static final String PREFIX = "xar.religion.master.parity";
    private static final String SCHEMA = "xar.religion.master-public-sdk-parity-fixture/v1";
    private static final int MANIFEST_MAX = 262_144, DATA_MAX = 8 << 20, FRAME_MAX = 64 << 20;
    private static final Set<String> METHODS = Set.copyOf(ReligionService.actualReadNames());
    private static final PlanningReadPort NEVER_LIVE = new PlanningReadPort() {
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
            throw new AssertionError("retained DATA parity must never invoke a live read");
        }
    };
    private record Case(String id, String method, ExactRef arguments, ExactRef readMetadata,
            ExactRef nativeFrame, ExactRef driverFacts, ExactRef pythonFullResponse) { }
    private record Fixture(String machine, ExactRef supplier, List<ExactRef> producerSources,
            List<ReligionCapabilities.ReadSource> reads, List<ReligionCapabilities.ActionSource> actions,
            PlayerReligionContextRead.Sources religion, PlayerHolyOrderContextRead.Sources holyOrders,
            List<Case> cases) {
        Fixture { producerSources = List.copyOf(producerSources); reads = List.copyOf(reads);
            actions = List.copyOf(actions); cases = List.copyOf(cases); }
    }

    @Test void actualOriginalFullResponsesReachAllThirteenMasterSdkConsumers() throws Exception {
        Fixture fixture = fixture();
        var fixed = fixed(fixture);
        var existing = existing(fixture);
        for (Case cell : fixture.cases()) {
            var data = NativeArchiveDataCodec.retainedFiles().readData(cell.readMetadata());
            var actual = frame(fixture, cell, data.receipt());
            Request expectedRequest = ReligionCodec.decode(cell.method(), new RawJson(bytes(cell.arguments(), DATA_MAX)));
            assertEquals(data.receipt().request().before().frame().revision(), expectedRequest.expectedRevision(), cell.id());
            AtomicInteger invocations = new AtomicInteger();
            var directory = directory(fixture, request -> {
                invocations.incrementAndGet(); assertEquals(expectedRequest, request, cell.id());
                return response(request, actual, data, fixed, existing);
            });
            var call = call(cell.method(), new RawJson(bytes(cell.arguments(), DATA_MAX)));
            ObjectNode sdk = ReligionCodec.object(new RawJson(directory.invoke(call).bytes()));
            assertEquals(1, invocations.get(), cell.id());
            assertFalse(sdk.get("isError").booleanValue(), cell.id());
            assertEquals("complete", sdk.get("resultType").textValue(), cell.id());
            // The unchanged Python's entire business result is retained separately, not rebuilt
            // from the Java decoder or a hand-selected expected field list.
            ObjectNode python = ReligionCodec.object(new RawJson(bytes(cell.pythonFullResponse(), DATA_MAX)));
            ObjectNode expected = ReligionCodec.publicResult(expectedRequest.method(), python);
            assertEquals(expected, sdk.get("structuredContent"), cell.id() + " complete Python business response");
            JsonNode content = sdk.get("content");
            assertTrue(content.isArray() && content.size() == 1, cell.id());
            assertEquals("text", content.get(0).get("type").textValue(), cell.id());
            assertEquals(expected, ReligionCodec.object(new RawJson(content.get(0).get("text").textValue()
                    .getBytes(java.nio.charset.StandardCharsets.UTF_8))), cell.id());
        }
    }

    @Test void actualSdkRejectsWrongPublicRevisionTypesBeforeArchiveReplay() throws Exception {
        Fixture fixture = fixture();
        AtomicInteger calls = new AtomicInteger();
        var directory = directory(fixture, request -> {
            calls.incrementAndGet(); throw new AssertionError("malformed SDK arguments reached archive replay");
        });
        for (Case cell : fixture.cases()) {
            ObjectNode original = ReligionCodec.object(new RawJson(bytes(cell.arguments(), DATA_MAX)));
            var missing = original.deepCopy(); missing.remove("expected_revision");
            for (ObjectNode bad : List.of(missing, original.deepCopy().putNull("expected_revision"),
                    original.deepCopy().put("expected_revision", true),
                    original.deepCopy().put("expected_revision", 1.0),
                    original.deepCopy().put("expected_revision", 9007199254740992L)))
                assertThrows(PublicMcpDirectory.ToolFailure.class,
                        () -> directory.invoke(call(cell.method(), ReligionCodec.raw(bad))), cell.id());
        }
        assertEquals(0, calls.get());
    }

    private static List<ReligionService.FixedRead> fixed(Fixture fixture) {
        var registration = new ReligionCapabilities.Registration(fixture.reads(), fixture.actions(), List.of(),
                (kind, request) -> { throw new AssertionError("pure replay grants no live Religion admission"); },
                (kind, command) -> { throw new AssertionError("READ parity grants no mutation admission"); });
        return ReligionService.fixedReads(registration);
    }
    private static ReligionService.ExistingReads existing(Fixture fixture) {
        return new ReligionService.ExistingReads(
                new PlayerReligionContextRead(NEVER_LIVE, fixture.religion(),
                        (sources, request) -> { throw new AssertionError("pure replay grants no live context admission"); }),
                new PlayerHolyOrderContextRead(NEVER_LIVE, fixture.holyOrders(),
                        (sources, request) -> { throw new AssertionError("pure replay grants no live holy-order admission"); }));
    }
    private static Response response(Request request, ReligionService.ActualFrame actual,
            NativeArchiveDataCodec.ReadData data, List<ReligionService.FixedRead> fixed,
            ReligionService.ExistingReads existing) {
        ReligionService.requireGuards(data.receipt());
        assertEquals(request.expectedRevision(), actual.frame().identity().frame().revision());
        if (request.method().name().equals("ck3_query_player_religion_context_v1")) {
            var observed = existing.religion().contract().replay(data.receipt());
            return new Response(request.method(), ReligionCodec.raw(ReligionCodec.publicResult(request.method(),
                    PlayerReligionContextRead.flattened(observed))));
        }
        if (request.method().name().equals("ck3_query_player_holy_order_context_v1")) {
            var observed = existing.holyOrders().contract().replay(data.receipt());
            return new Response(request.method(), ReligionCodec.raw(ReligionCodec.publicResult(request.method(),
                    PlayerHolyOrderContextRead.flattened(observed))));
        }
        var choices = fixed.stream().filter(read -> read.contract().operation()
                .equals(data.receipt().request().operation())).toList();
        assertEquals(1, choices.size(), "exact original fixed READ operation required");
        var chosen = choices.getFirst();
        assertNotEquals(ReligionCapabilities.ReadKind.EPIDEMIC, chosen.kind(), "R1 owns Epidemic parity");
        return present(chosen.kind(), chosen.contract(), actual, request, data);
    }
    private static <T> Response present(ReligionCapabilities.ReadKind kind, ReadContract<T> contract,
            ReligionService.ActualFrame actual, Request request, NativeArchiveDataCodec.ReadData data) {
        T original = contract.replay(data.receipt());
        return ReligionService.presentRead(kind, actual, request,
                new PlanningReadResult.Known<>(original, data.receipt(), data.original()));
    }
    private static ReligionService.ActualFrame frame(Fixture fixture, Case cell, PlanningReadReceipt read) throws IOException {
        assertEquals(cell.nativeFrame(), read.before().binding().nativeEvidence(), cell.id());
        RawJson facts = new RawJson(bytes(cell.driverFacts(), DATA_MAX));
        byte[] nativePacket = bytes(cell.nativeFrame(), FRAME_MAX);
        var observed = DriverObservationEvidenceReader.nativeFrame(cell.driverFacts(), facts, nativePacket);
        ExactRef driver = DriverObservationEvidenceReader.currentDriverReference(cell.driverFacts(), facts);
        var joined = DriverObservationEvidenceReader.decode(cell.driverFacts(), facts,
                new RawJson(bytes(driver, DATA_MAX)), observed);
        var decoded = new DriverObservationAssembler().assemble(observed, joined, cell.nativeFrame());
        var complete = assertInstanceOf(DriverObservationAssembler.Complete.class, decoded, cell.id());
        assertEquals(fixture.machine(), complete.identity().machineId(), cell.id());
        assertEquals(read.request().before(), complete.identity(), cell.id());
        assertEquals(read.request().source(), complete.source(), cell.id());
        assertEquals(read.request().sessionId(), complete.sessionId(), cell.id());
        assertEquals(read.before().binding().connectionGeneration(), complete.connectionGeneration(), cell.id());
        assertEquals(read.before().originalBindingSha256(), complete.fullBindingSha256(), cell.id());
        // Negative actor support is a deliberate Java correction to old Python behavior and has
        // separate source regressions. Do not invent a Python-supported negative-actor oracle.
        assertTrue(complete.identity().frame().identity().player().signum() > 0, cell.id());
        var hello = assertInstanceOf(NativeWire.Hello.class,
                NativeWire.decode(bytes(read.before().binding().capabilityEvidence(), FRAME_MAX)), cell.id());
        ReligionService.requireGuards(read);
        return new ReligionService.ActualFrame(complete, hello, read.request().deadline());
    }
    private static PublicMcpDirectory.ToolCall call(String method, RawJson arguments) {
        return new PublicMcpDirectory.ToolCall(method,
                new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE, Optional.of(arguments)),
                Optional.empty(), new McpCancellation());
    }
    private static PublicMcpDirectory directory(Fixture fixture,
            org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes.Handler<Request, Response> actual)
            throws Exception {
        var bindings = RootReligionPublicProducts.bindings(fixture.supplier(), actual);
        assertEquals(METHODS, bindings.stream().map(McpExecutableDirectory.DirectBinding::name)
                .collect(java.util.stream.Collectors.toSet()));
        McpCoverage.Catalog original;
        try (InputStream input = ReligionMasterPublicSdkParityTest.class.getResourceAsStream("/mcp/original-tool-catalog.json")) {
            assertNotNull(input, "mandatory original catalog missing");
            original = McpCoverage.readCatalog(new RawJson(input.readAllBytes()));
        }
        var declarations = original.declarations().stream().filter(row -> METHODS.contains(row.name())).toList();
        assertEquals(13, declarations.size());
        var decisions = declarations.stream().map(row -> new McpCoverage.Decision(row.name(),
                McpCoverage.Admission.ADMITTED, fixture.supplier(), "original retained DATA replay and SDK parity only")).toList();
        var tools = RootOriginalPublicTestInputs.tools().stream().filter(tool -> METHODS.contains(tool.name())).toList();
        assertEquals(13, tools.size(), "mandatory original SDK descriptors incomplete");
        var registry = new org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings();
        registry.freeze(Set.of());
        return assertInstanceOf(McpExecutableDirectory.Partial.class, McpExecutableDirectory.assemble(
                new McpCoverage.Catalog(declarations), decisions, tools, List.of(), registry, bindings)).softwareDirectory();
    }

    private static Fixture fixture() throws IOException {
        String path = required(PREFIX + ".path"), length = required(PREFIX + ".bytes");
        assertTrue(length.matches("[1-9][0-9]*"), "canonical positive fixture length required");
        ExactRef reference = new ExactRef(path, new BigInteger(length).longValueExact(), required(PREFIX + ".sha256"));
        ObjectNode root = StrictJson.object(StrictJson.parse(bytes(reference, MANIFEST_MAX), MANIFEST_MAX),
                Set.of("schema", "machine_id", "observed_at_utc", "supplier_source", "producer_sources",
                        "read_sources", "action_sources", "religion_context_sources", "holy_order_context_sources", "cases"));
        assertEquals(SCHEMA, text(root, "schema")); Instant.parse(text(root, "observed_at_utc"));
        String machine = text(root, "machine_id"); assertNotEquals("unknown", machine);
        ExactRef supplier = exact(root.get("supplier_source")); bytes(supplier, DATA_MAX);
        List<ExactRef> producers = references(root.get("producer_sources"));
        assertTrue(producers.size() >= 2, "actual unchanged Python producer closure is mandatory");
        for (ExactRef producer : producers) { assertTrue(producer.path().endsWith(".py")); bytes(producer, DATA_MAX); }
        var reads = new ArrayList<ReligionCapabilities.ReadSource>();
        for (JsonNode value : array(root.get("read_sources"), 12, 12)) {
            ObjectNode row = StrictJson.object(value, Set.of("kind", "source"));
            ExactRef source = exact(row.get("source")); bytes(source, DATA_MAX);
            reads.add(new ReligionCapabilities.ReadSource(ReligionCapabilities.ReadKind.valueOf(text(row, "kind")), source));
        }
        var actions = new ArrayList<ReligionCapabilities.ActionSource>();
        for (JsonNode value : array(root.get("action_sources"), 4, 4)) {
            ObjectNode row = StrictJson.object(value, Set.of("kind", "source"));
            ExactRef source = exact(row.get("source")); bytes(source, DATA_MAX);
            actions.add(new ReligionCapabilities.ActionSource(ReligionCapabilities.MutationSource.valueOf(text(row, "kind")), source));
        }
        ObjectNode religion = StrictJson.object(root.get("religion_context_sources"),
                Set.of("python_producer", "native_mailbox", "native_context"));
        var religionSources = new PlayerReligionContextRead.Sources(exact(religion.get("python_producer")),
                exact(religion.get("native_mailbox")), exact(religion.get("native_context")));
        ObjectNode orders = StrictJson.object(root.get("holy_order_context_sources"), Set.of("python_producer",
                "python_cost_normalizer", "python_reinforcement_normalizer", "native_mailbox", "native_wire",
                "native_context", "native_reinforcement", "native_build4_binding"));
        var orderSources = new PlayerHolyOrderContextRead.Sources(exact(orders.get("python_producer")),
                exact(orders.get("python_cost_normalizer")), exact(orders.get("python_reinforcement_normalizer")),
                exact(orders.get("native_mailbox")), exact(orders.get("native_wire")), exact(orders.get("native_context")),
                exact(orders.get("native_reinforcement")), exact(orders.get("native_build4_binding")));
        for (ExactRef source : List.of(religionSources.pythonProducer(), religionSources.nativeMailbox(), religionSources.nativeContext()))
            bytes(source, DATA_MAX);
        for (ExactRef source : orderSources.all()) bytes(source, DATA_MAX);
        var cases = new ArrayList<Case>(); Set<String> ids = new HashSet<>(), seen = new HashSet<>();
        for (JsonNode value : array(root.get("cases"), 13, 256)) {
            ObjectNode row = StrictJson.object(value, Set.of("id", "method", "arguments", "read_metadata",
                    "native_frame", "driver_facts", "python_full_response"));
            String id = text(row, "id"), method = text(row, "method");
            assertTrue(ids.add(id), "duplicate actual corpus case"); assertTrue(METHODS.contains(method));
            seen.add(method);
            cases.add(new Case(id, method, exact(row.get("arguments")), exact(row.get("read_metadata")),
                    exact(row.get("native_frame")), exact(row.get("driver_facts")), exact(row.get("python_full_response"))));
        }
        assertEquals(METHODS, seen, "all thirteen actual full-response methods must have original retained cases");
        return new Fixture(machine, supplier, producers, reads, actions, religionSources, orderSources, cases);
    }
    private static List<ExactRef> references(JsonNode array) {
        var result = new ArrayList<ExactRef>(); for (JsonNode value : array(array, 2, 64)) result.add(exact(value));
        return List.copyOf(result);
    }
    private static List<JsonNode> array(JsonNode value, int minimum, int maximum) {
        assertTrue(value != null && value.isArray() && value.size() >= minimum && value.size() <= maximum,
                "mandatory bounded original fixture array required");
        var result = new ArrayList<JsonNode>(); value.forEach(result::add); return List.copyOf(result);
    }
    private static ExactRef exact(JsonNode node) { return ExactRef.fromJson(node); }
    private static String text(ObjectNode node, String field) { return StrictJson.text(node.get(field)); }
    private static String required(String property) {
        String value = System.getProperty(property);
        if (value == null || value.isEmpty()) throw new IllegalStateException("mandatory actual retained fixture missing: " + property);
        return value;
    }
    private static byte[] bytes(ExactRef ref, int maximum) throws IOException {
        Path path = Path.of(ref.path());
        if (!path.isAbsolute() || !path.normalize().equals(path) || ref.bytes() < 1 || ref.bytes() > maximum)
            throw new IOException("explicit bounded absolute original DATA reference required");
        if (path.getFileName().toString().toLowerCase(java.util.Locale.ROOT).endsWith(".exe"))
            throw new IOException("SDK parity is not an EXE reader");
        if (Files.size(path) != ref.bytes()) throw new IOException("required retained original absent or changed length");
        var before = SharedSourceFiles.observe(path);
        if (before.source().bytes() != ref.bytes() || !before.source().sha256().equals(ref.sha256()))
            throw new IOException("required retained original byte/hash drift");
        byte[] original;
        try (InputStream input = Files.newInputStream(path)) { original = input.readNBytes(maximum + 1); }
        SharedSourceFiles.assertUnchanged(before);
        if (original.length != ref.bytes() || !DriverJson.sha256(original).equals(ref.sha256()))
            throw new IOException("retained original changed during DATA read");
        return original;
    }
}
