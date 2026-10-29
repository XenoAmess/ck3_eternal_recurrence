package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Calls the complete real provider through the actual public decoder, handler and result encoder. */
final class VanillaEventKnowledgeMethodsTest {
    private static VanillaEventCatalog catalog;
    @TempDir Path temporary;
    @BeforeAll static void actualFullProvider() throws Exception { catalog = VanillaEventCatalog.load(); }
    private static ToolDescriptor descriptor() {
        var row = StrictJson.object().put("name", VanillaEventKnowledgeMethods.NAME);
        var schema = row.putObject("inputSchema").put("type", "object"); schema.putArray("required").add("event_definition_key");
        var properties = schema.putObject("properties"); properties.putObject("event_definition_key").put("type", "string");
        properties.putObject("ck3_build").put("type", "string").put("default", catalog.currentBuild());
        return new ToolDescriptor(VanillaEventKnowledgeMethods.NAME, raw(row));
    }
    @Test void allOriginalProviderQueryRowsSurviveActualPublicBindingWithoutFieldProjection() throws Exception {
        var service = new VanillaEventKnowledgeMethods(catalog, descriptor()); assertSame(catalog, service.catalog());
        var binding = service.actualMethods(source()).getFirst(); int rows = 0;
        for (String build : catalog.supportedBuilds()) for (String key : catalog.queryKeys(build)) {
            var arguments = StrictJson.object().put("event_definition_key", key).put("ck3_build", build);
            var result = invoke(binding, call(arguments));
            assertEquals(McpJson.parse(RetainedJson.encode(catalog.fullQuery(build, key))),
                    McpJson.parse(result.bytes()).get("structuredContent")); rows++;
        }
        assertTrue(rows > 0, "empty full catalog cannot count as public migration");
    }
    @Test void originalPublicDefaultDiffersFromRegistryDefaultAndWrongArgumentTypesDoNotReachProvider() {
        var service = new VanillaEventKnowledgeMethods(catalog, descriptor());
        assertEquals(catalog.currentBuild(), service.decode(arguments("{\"event_definition_key\":\"health.1015\"}")).ck3Build());
        for (String value : new String[]{"{}", "{\"event_definition_key\":null}", "{\"event_definition_key\":true}",
                "{\"event_definition_key\":1.0}", "{\"event_definition_key\":\"x\",\"ck3_build\":null}",
                "{\"event_definition_key\":\"x\",\"alias\":1}"})
            assertThrows(IllegalArgumentException.class, () -> service.decode(arguments(value)));
        for (String key : new String[]{"", " \t\n", "missing.event", " health.1015 "}) {
            var actual = service.query(new VanillaEventKnowledgeMethods.Request(key, catalog.currentBuild()));
            assertEquals(McpJson.parse(RetainedJson.encode(catalog.fullQuery(catalog.currentBuild(), key))),
                    McpJson.parse(actual.original().bytes()));
        }
    }
    @Test void sourceOwnedUnsupportedBuildEchoAboveTheSmallRetainedDefaultRemainsComplete() {
        var service = new VanillaEventKnowledgeMethods(catalog, descriptor()); String build = "unsupported-" + "x".repeat(600000);
        var actual = service.query(new VanillaEventKnowledgeMethods.Request("health.1015", build));
        assertTrue(actual.original().bytes().length > 512000);
        assertEquals(RetainedJson.pythonCanonical(catalog.fullQuery(build, "health.1015"),
                        new RetainedJson.CanonicalBudget(RawJson.MAXIMUM_BYTES, RawJson.MAXIMUM_BYTES, 1000)).sha256(),
                RetainedJson.pythonCanonical(RetainedJson.parse(actual.original().bytes(),
                                new RetainedJson.ParseBudget(RawJson.MAXIMUM_BYTES, RawJson.MAXIMUM_BYTES, 1000)),
                        new RetainedJson.CanonicalBudget(RawJson.MAXIMUM_BYTES, RawJson.MAXIMUM_BYTES, 1000)).sha256());
    }
    @Test void originalIndependentPythonProducerMatchesEveryActualFullPublicQueryAndDefault() throws Exception {
        String repository = System.getProperty("xar.repository.root");
        assertNotNull(repository, "required original-producer regression: provide canonical xar.repository.root; this test cannot skip");
        Path root = Path.of(repository).toRealPath();
        String python = System.getProperty("xar.python");
        assertNotNull(python, "required original-producer regression: provide canonical xar.python; no ambient interpreter fallback");
        var request = StrictJson.object(); var cases = request.putArray("cases");
        for (String build : catalog.supportedBuilds()) for (String key : catalog.queryKeys(build))
            cases.addObject().put("build", build).put("key", key);
        cases.addObject().put("build", "unsupported-build").put("key", "health.1015");
        cases.addObject().put("build", catalog.currentBuild()).put("key", " \t\n");
        Path output = temporary.resolve("actual-python-query.json");
        String script = """
                import json, pathlib, sys
                sys.path.insert(0, str(pathlib.Path(sys.argv[1]) / 'ck3_autonomous_player' / 'src'))
                from xar_autoplayer.vanilla_events import CURRENT_CK3_BUILD, query_vanilla_event_knowledge_v1
                request = json.load(sys.stdin)
                result = {'current_build': CURRENT_CK3_BUILD, 'rows': [query_vanilla_event_knowledge_v1(row['key'], ck3_build=row['build']) for row in request['cases']]}
                print(json.dumps(result, ensure_ascii=False, allow_nan=False))
                """;
        ProcessBuilder builder = new ProcessBuilder(python, "-c", script, root.toString()).directory(root.toFile())
                .redirectErrorStream(true).redirectOutput(output.toFile());
        builder.environment().put("XAR_SOURCE_REPOSITORY", root.toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONIOENCODING", "utf-8");
        Process process = builder.start();
        try {
            try (var input = process.getOutputStream()) { input.write(McpJson.encode(request)); }
            assertTrue(process.waitFor(60, TimeUnit.SECONDS), "original Python producer did not finish within its bounded regression deadline");
            assertEquals(0, process.exitValue(), "original Python query producer failed; inspect its exact test output");
            assertTrue(Files.size(output) <= 32L << 20, "original query regression output exceeded its explicit bound");
            JsonNode actual = McpJson.parse(Files.readAllBytes(output));
            assertEquals(catalog.currentBuild(), actual.get("current_build").textValue());
            var service = new VanillaEventKnowledgeMethods(catalog, descriptor());
            var binding = service.actualMethods(source()).getFirst();
            assertEquals(cases.size(), actual.get("rows").size());
            for (int index = 0; index < cases.size(); index++) {
                var row = cases.get(index); var arguments = StrictJson.object().put("event_definition_key", row.get("key").textValue())
                        .put("ck3_build", row.get("build").textValue());
                assertEquals(actual.get("rows").get(index), McpJson.parse(invoke(binding, call(arguments)).bytes()).get("structuredContent"));
            }
        } finally { if (process.isAlive()) process.destroyForcibly(); }
    }
    private static <Q,R> CallResult invoke(McpExecutableDirectory.DirectBinding<Q,R> binding, ToolCall call) throws Exception {
        Q request = binding.decoder().decode(call); return binding.encoder().encode(binding.actual().invoke(request));
    }
    private static Arguments arguments(String json) { return new Arguments(Presence.VALUE, Optional.of(new RawJson(json.getBytes(StandardCharsets.UTF_8)))); }
    private static ToolCall call(ObjectNode arguments) { return new ToolCall(VanillaEventKnowledgeMethods.NAME,
            new Arguments(Presence.VALUE, Optional.of(raw(arguments))), Optional.empty(), new McpCancellation()); }
    private static RawJson raw(JsonNode value) { return new RawJson(McpJson.encode(value)); }
    private static ExactRef source() { return new ExactRef("fixture/source", 1, "a".repeat(64)); }
}
