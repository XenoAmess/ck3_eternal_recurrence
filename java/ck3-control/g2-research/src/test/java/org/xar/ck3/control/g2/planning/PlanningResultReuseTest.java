package org.xar.ck3.control.g2.planning;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.math.BigInteger;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import javax.tools.ToolProvider;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m5.M5PayloadCodec;
import org.xar.ck3.control.g2.m5.M5Research;

/** Exact unchanged historical producer, with only its fact v1/v2 metadata projection checked separately. */
final class PlanningResultReuseTest {
    private static final String CODEC = "org.xar.ck3.control.g2.planning.ProposalLifecycleCodec";
    private static final String PLANNER = "org.xar.ck3.control.g2.planning.ProposalLifecycle";
    private static final String ORIGINAL_SHA = "9315838cc36bd6f41602655e707e5f184d13a2e66c63b823d35cc5a2ec75a037";
    @TempDir static Path temporary;
    private static URLClassLoader originalLoader;
    private static Method originalProducer;

    @BeforeAll static void compileActualOriginalWithoutRenamingOrRewritingIt() throws Exception {
        byte[] original = originalSource("ProposalLifecycleCodec.java");
        assertEquals(18206, original.length);
        assertEquals(ORIGINAL_SHA, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        Path source = temporary.resolve("original-source/ProposalLifecycleCodec.java");
        Path output = temporary.resolve("original-classes");
        Files.createDirectories(source.getParent()); Files.createDirectories(output); Files.write(source, original);
        byte[] planner = originalSource("ProposalLifecycle.java");
        assertEquals(15337, planner.length);
        assertEquals("e96ebe2888513a732b5c2644446342bb1adccbf8111cf9f1461619276d79b59c",
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(planner)));
        Path plannerSource = source.resolveSibling("ProposalLifecycle.java"); Files.write(plannerSource, planner);
        var compiler = ToolProvider.getSystemJavaCompiler();
        assertNotNull(compiler, "JDK compiler is required; absence is a failure, never a skipped differential");
        String classpath = System.getProperty("surefire.test.class.path", System.getProperty("java.class.path"));
        try (var files = compiler.getStandardFileManager(null, null, StandardCharsets.UTF_8)) {
            assertTrue(compiler.getTask(null, files, null,
                    List.of("--release", "21", "-Xlint:all", "-Werror", "-classpath", classpath, "-d", output.toString()),
                    null, files.getJavaFileObjects(source, plannerSource)).call(), "actual original must compile before its producer is used");
        }
        originalLoader = new URLClassLoader(new URL[] {output.toUri().toURL()}, PlanningResultReuseTest.class.getClassLoader()) {
            @Override protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
                synchronized (getClassLoadingLock(name)) {
                    if (name.equals(CODEC) || name.startsWith(CODEC + "$") || name.equals(PLANNER) || name.startsWith(PLANNER + "$")) {
                        Class<?> value = findLoadedClass(name);
                        if (value == null) value = findClass(name);
                        if (resolve) resolveClass(value);
                        return value;
                    }
                    return super.loadClass(name, resolve);
                }
            }
        };
        Class<?> originalClass = Class.forName(CODEC, true, originalLoader);
        assertNotSame(ProposalLifecycleCodec.class, originalClass);
        originalProducer = originalClass.getMethod("evaluateG2Payload", byte[].class, G2Source.class);
    }

    @AfterAll static void closeOriginalLoader() throws IOException {
        if (originalLoader != null) originalLoader.close();
    }

    @Test void allLifecycleBranchesRetainActualOriginalBytesAndStandaloneTamperValidation() throws Exception {
        for (ObjectNode input : lifecycleCases()) {
            byte[] actual = compareOriginal(input, source());
            assertArrayEquals(actual, ProposalLifecycleCodec.encode(ProposalLifecycleCodec.evaluate(raw(input), source())));
        }
        Proposed first = assertInstanceOf(Proposed.class, ProposalLifecycleCodec.evaluate(raw(request()), source()));
        Proposed forged = new Proposed(first.evaluation(), new ProposedAction(first.action().body(), "f".repeat(64)));
        assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.encode(forged));
    }

    @Test void everyRequestReevaluatesActionsFactsAndChangedBodiesInsteadOfReusingPriorProposals() throws Exception {
        ObjectNode input = request();
        JsonNode first = StrictJson.parse(compareOriginal(input, source()), ProposalLifecycleCodec.MAX_BYTES);
        String digest = first.at("/proposal/body_sha256").textValue();
        for (String state : List.of("UNKNOWN", "ACK_RECEIVED", "APPLIED_CONFIRMED", "REJECTED_CONFIRMED")) {
            ArrayNode facts = (ArrayNode) input.get("external_facts"); facts.removeAll();
            facts.add(ProposalLifecycleFixtures.fact("lifecycle-war0", digest, state, "GLOBAL", "war", -1));
            JsonNode actual = StrictJson.parse(compareOriginal(input, source()), ProposalLifecycleCodec.MAX_BYTES);
            assertEquals("DEFERRED", actual.get("status").textValue());
            assertEquals(state.equals("UNKNOWN") || state.equals("ACK_RECEIVED") ? "EXISTING_UNKNOWN" : "ALREADY_RECORDED",
                    actual.get("deferred_reason").textValue());
            ((ObjectNode) input.at("/intents/0/expected/values/0")).put("value", false);
            assertEquals("BODY_CONFLICT", StrictJson.parse(compareOriginal(input, source()), ProposalLifecycleCodec.MAX_BYTES).get("status").textValue());
            ((ObjectNode) input.at("/intents/0/expected/values/0")).put("value", true);
        }
        G2Source changed = new G2Source(source().machineId(), "2026-10-22T00:00:01Z", source().exactBuild(), source().sourceRef());
        assertEquals("BODY_CONFLICT", StrictJson.parse(compareOriginal(input, changed), ProposalLifecycleCodec.MAX_BYTES).get("status").textValue());
        ((ArrayNode) input.get("external_facts")).removeAll();
        ((ObjectNode) input.at("/intents/0")).put("action_id", "another-action");
        JsonNode next = StrictJson.parse(compareOriginal(input, changed), ProposalLifecycleCodec.MAX_BYTES);
        assertEquals("another-action", next.at("/proposal/body/action_id").textValue());
        assertNotEquals(digest, next.at("/proposal/body_sha256").textValue());
    }

    @Test void fullImmutableBodyContextAndExactIntegerAndUnicodeDomainsRemainOriginal() throws Exception {
        List<ObjectNode> inputs = new ArrayList<>();
        ObjectNode version = request(); ((ObjectNode) version.get("observation")).put("observation_version", 2); inputs.add(version);
        ObjectNode game = request(); ((ObjectNode) game.at("/observation/game")).put("pid", 8); inputs.add(game);
        ObjectNode birth = request(); ((ObjectNode) birth.at("/observation/game")).put("creation_filetime", "134371688739143607"); inputs.add(birth);
        ObjectNode frame = request(); changeFrame(frame.get("joint_budget_request"), new BigInteger("18446744073709551615")); inputs.add(frame);
        for (String text : List.of("x".repeat(70_001), "\ud83d\ude00".repeat(35_001))) {
            ObjectNode large = request(); ObjectNode value = (ObjectNode) large.at("/intents/0/expected/values/0");
            value.put("kind", "TEXT"); value.put("value", text); inputs.add(large);
        }
        ObjectNode presence = request(); ArrayNode values = (ArrayNode) presence.at("/intents/0/expected/values"); values.removeAll();
        values.addObject().put("field", "missing").put("kind", "ABSENT");
        values.addObject().put("field", "nullable").put("kind", "NULL").putNull("value");
        values.addObject().put("field", "count").put("kind", "INTEGER").put("value", StrictJson.MAX_SAFE_INTEGER); inputs.add(presence);
        for (double token : List.of(1.0, 1.25)) {
            ObjectNode decimal = request(); ((ObjectNode) decimal.at("/joint_budget_request/snapshot")).put("opaque_native_decimal", token); inputs.add(decimal);
        }
        for (ObjectNode input : inputs) compareOriginal(input, source());
        for (G2Source changed : List.of(
                new G2Source(source().machineId(), source().observedAtUtc(), "changed-build", source().sourceRef()),
                new G2Source(source().machineId(), source().observedAtUtc(), source().exactBuild(), new ExactRef("changed-source", 1, "1".repeat(64)))))
            compareOriginal(request(), changed);
    }

    @Test void productionM5OperationAndCompleteG2WireRetainActualOriginalBytesForAllBranches() throws Exception {
        for (ObjectNode input : lifecycleCases()) {
            ObjectNode operation = StrictJson.object(); operation.put("schema", M5PayloadCodec.OPERATION_SCHEMA);
            operation.put("operation", "proposal_lifecycle"); operation.set("request", input);
            G2Request request = new G2Request("reuse-consumer", Milestone.M5, source(),
                    ProjectionJson.object(raw(operation), M5PayloadCodec.MAXIMUM_BYTES));
            G2Response actual = new M5Research().evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(request)));
            G2Response consumed = G2Wire.decodeResponse(G2Wire.encodeResponse(actual));
            assertEquals(request.source(), consumed.source()); assertEquals(request.requestId(), consumed.requestId());
            assertArrayEquals(historicalExpected(input, source()), consumed.result().bytes());
            JsonNode result = StrictJson.parse(consumed.result().bytes(), ProposalLifecycleCodec.MAX_BYTES);
            for (String field : List.of("formal_action_ready", "resource_reservation_performed", "intent_durable"))
                assertFalse(result.get(field).booleanValue());
        }
    }

    @Test void invalidRuntimeInputsRetainActualOriginalFailuresBeforeAnyReusableBodyExists() throws Exception {
        String valid = new String(raw(request()), StandardCharsets.UTF_8);
        List<byte[]> invalid = new ArrayList<>();
        invalid.add((valid + " {}").getBytes(StandardCharsets.UTF_8));
        invalid.add(("{\"schema\":\"duplicate\"," + valid.substring(1)).getBytes(StandardCharsets.UTF_8));
        invalid.add(new byte[] {(byte) 0xc3, 0x28});
        ObjectNode extra = request(); extra.put("allow_submit", true); invalid.add(raw(extra));
        ObjectNode missing = request(); missing.remove("external_facts"); invalid.add(raw(missing));
        for (String token : List.of("true", "1.0", "\"1\"", "null", "2"))
            invalid.add(valid.replace("\"version\":1", "\"version\":" + token).getBytes(StandardCharsets.UTF_8));
        for (byte[] input : invalid) {
            InvocationTargetException old = assertThrows(InvocationTargetException.class, () -> original(input, source()));
            assertInstanceOf(IllegalArgumentException.class, old.getCause());
            assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.evaluateG2Payload(input, source()));
        }
        assertEquals("PROPOSED", StrictJson.parse(compareOriginal(request(), source()), ProposalLifecycleCodec.MAX_BYTES).get("status").textValue());
    }

    @Test void callerMutationCannotReachAnotherRequestOrTheImmutableInternalInput() throws Exception {
        ObjectNode request = request(); byte[] input = raw(request); byte[] before = input.clone();
        byte[] first = ProposalLifecycleCodec.evaluateG2Payload(input, source()); assertArrayEquals(before, input);
        byte[] expected = first.clone(); java.util.Arrays.fill(first, (byte) 0);
        assertArrayEquals(expected, ProposalLifecycleCodec.evaluateG2Payload(input, source()));
        Input decoded = ProposalLifecycleCodec.decode(input, source());
        assertThrows(UnsupportedOperationException.class, () -> decoded.intents().clear());
        assertThrows(UnsupportedOperationException.class, () -> decoded.intents().getFirst().expected().values().clear());
        ((ObjectNode) request.at("/intents/0/expected/values/0")).put("value", false);
        assertNotEquals(new String(expected, StandardCharsets.UTF_8), new String(compareOriginal(request, source()), StandardCharsets.UTF_8));
        assertEquals(true, ((ExpectedBoolean) decoded.intents().getFirst().expected().values().getFirst()).value());
    }

    private static List<ObjectNode> lifecycleCases() {
        List<ObjectNode> result = new ArrayList<>(); result.add(request());
        ObjectNode missingIntent = request(); ((ArrayNode) missingIntent.get("intents")).removeAll(); result.add(missingIntent);
        ObjectNode missing = request(); ((ArrayNode) missing.at("/joint_budget_request/assessments")).removeAll(); result.add(missing);
        ObjectNode wait = request(); wait.at("/joint_budget_request/assessments").forEach(value -> ((ObjectNode) value).put("benefit_units", 0)); result.add(wait);
        Proposed proposed = (Proposed) ProposalLifecycleCodec.evaluate(raw(request()), source());
        for (String state : List.of("UNKNOWN", "ACK_RECEIVED", "APPLIED_CONFIRMED", "REJECTED_CONFIRMED")) {
            ObjectNode input = request(); ((ArrayNode) input.get("external_facts")).add(ProposalLifecycleFixtures.fact(
                    "lifecycle-war0", proposed.action().bodySha256(), state, "GLOBAL", "war", -1)); result.add(input);
        }
        for (Map.Entry<String, Long> scope : Map.of("GLOBAL", -1L, "DOMAIN", -1L, "CLAIMS", 7L).entrySet()) {
            ObjectNode input = request(); ((ArrayNode) input.get("external_facts")).add(ProposalLifecycleFixtures.fact(
                    "other-action", "1".repeat(64), "UNKNOWN", scope.getKey(), "war", scope.getValue())); result.add(input);
        }
        ObjectNode independent = request(); ((ArrayNode) independent.get("external_facts")).add(ProposalLifecycleFixtures.fact(
                "other-action", "1".repeat(64), "UNKNOWN", "CLAIMS", "war", 999)); result.add(independent);
        ObjectNode conflict = request(); ((ArrayNode) conflict.get("external_facts")).add(ProposalLifecycleFixtures.fact(
                "lifecycle-war0", "f".repeat(64), "UNKNOWN", "GLOBAL", "war", -1)); result.add(conflict);
        return result;
    }

    private static void changeFrame(JsonNode node, BigInteger revision) {
        if (node instanceof ObjectNode object) {
            if (object.has("native_revision")) object.put("native_revision", revision);
            if (object.has("revision")) object.put("revision", revision);
        }
        if (node.isContainerNode()) node.forEach(value -> changeFrame(value, revision));
    }
    private static byte[] compareOriginal(ObjectNode input, G2Source source) throws Exception {
        byte[] payload = raw(input); byte[] before = payload.clone(); byte[] expected = historicalExpected(input, source);
        byte[] actual = ProposalLifecycleCodec.evaluateG2Payload(payload, source);
        assertArrayEquals(expected, actual, "complete historical result after explicit fact schema migration"); assertArrayEquals(before, payload);
        return actual;
    }
    private static byte[] historicalExpected(ObjectNode current, G2Source source) throws Exception {
        ObjectNode historical = current.deepCopy();
        for (JsonNode value : historical.get("external_facts")) {
            ExternalFact fact = ProposalLifecycleCodec.decodeFact(value);
            assertNotEquals(ExternalState.SEND_CONFIRMED, fact.state(), "the historical producer has no confirmed-send variant");
            ((ObjectNode) value).remove("schema");
            assertEquals(fact, ProposalLifecycleCodec.decodeHistoricalFactV1(value), "only version metadata may differ");
        }
        ObjectNode result = (ObjectNode) StrictJson.parse(original(raw(historical), source), ProposalLifecycleCodec.MAX_BYTES);
        ArrayNode facts = (ArrayNode) result.get("blocking_facts");
        for (int index = 0; index < facts.size(); index++)
            facts.set(index, ProposalLifecycleCodec.fact(ProposalLifecycleCodec.decodeHistoricalFactV1(facts.get(index))));
        return ProposalLifecycleCodec.encodePayload(result);
    }
    @Test void actualHistoricalProducerCannotGrantOrRepresentTheNewConfirmedSendState() {
        ObjectNode input = request(); Proposed first = (Proposed) ProposalLifecycleCodec.evaluate(raw(input), source());
        ObjectNode send = ProposalLifecycleFixtures.fact(first.action().body().actionId(), first.action().bodySha256(),
                "SEND_CONFIRMED", "GLOBAL", "war", -1);
        ((ArrayNode) input.get("external_facts")).add(send);
        assertThrows(AssertionError.class, () -> historicalExpected(input, source()));
        send.remove("schema");
        InvocationTargetException failure = assertThrows(InvocationTargetException.class, () -> original(raw(input), source()));
        assertInstanceOf(IllegalArgumentException.class, failure.getCause());
    }
    private static byte[] original(byte[] input, G2Source source) throws Exception {
        return (byte[]) originalProducer.invoke(null, input, source);
    }
    private static byte[] originalSource(String name) throws IOException {
        try (var resource = PlanningResultReuseTest.class.getResourceAsStream("/planningreuse/" + name)) {
            assertNotNull(resource, "the exact original production source is a required persistent test resource");
            return resource.readAllBytes();
        }
    }
    private static ObjectNode request() { return ProposalLifecycleFixtures.request(); }
    private static byte[] raw(ObjectNode input) { return ProposalLifecycleCodec.encodePayload(input); }
    private static G2Source source() { return ProposalLifecycleFixtures.source(); }
}
