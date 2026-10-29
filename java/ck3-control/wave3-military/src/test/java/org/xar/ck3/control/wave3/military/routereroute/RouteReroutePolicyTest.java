package org.xar.ck3.control.wave3.military.routereroute;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.StrictJson;

/** Default Surefire entry: the historical original callable oracle is mandatory, never a skipped environment. */
final class RouteReroutePolicyTest {
    @TempDir Path temporary;
    @Test void actualOriginalProducerToTypedPreviewConsumerCostsCacheAndHalt() throws Exception {
        byte[] resource;
        try (var input = getClass().getResourceAsStream("/routereroute/original-source-bound-fixture01.json")) {
            assertNotNull(input, "exact original callable fixture is required"); resource = input.readNBytes(65_537);
        }
        assertTrue(resource.length <= 65_536);
        ObjectNode fixture = StrictJson.object(StrictJson.parse(resource), Set.of("schema", "machine_id", "captured_at_utc", "origins", "files"));
        assertEquals("xar.route-reroute-original-callable-fixture/v1", fixture.path("schema").textValue());
        assertEquals(4, fixture.path("origins").size());
        ObjectNode manifest = StrictJson.object(); manifest.put("schema", "xar.route-reroute-regression-input/v1");
        // The archive identifies its source machine; a CI execution must supply its own identity independently.
        manifest.put("machine_id", System.getProperty("xar.route.reroute.machine-id", "unknown")); manifest.put("repository", temporary.toString());
        String python = System.getProperty("xar.python");
        assertNotNull(python, "xar.python must explicitly identify the original-producer interpreter");
        assertFalse(python.isBlank(), "xar.python must not be blank");
        manifest.put("python", python);
        manifest.put("result_path", temporary.resolve("ACTUAL.json").toString()); var sources = manifest.putArray("sources");
        for (JsonNode file : fixture.get("files")) {
            String relative = StrictJson.text(file.get("path")); Path path = temporary.resolve(relative).normalize();
            assertTrue(path.startsWith(temporary) && !path.equals(temporary), "fixture path containment");
            byte[] bytes = StrictJson.text(file.get("utf8")).getBytes(StandardCharsets.UTF_8);
            assertEquals(StrictJson.integer(file.get("bytes"), 1, 65_536), bytes.length);
            assertEquals(StrictJson.text(file.get("sha256")), StockRouteRuleReader.sha256(bytes));
            Files.createDirectories(path.getParent()); Files.write(path, bytes, StandardOpenOption.CREATE_NEW);
            ObjectNode pin = sources.addObject(); pin.put("path", path.toString()); pin.put("bytes", bytes.length);
            pin.put("sha256", StockRouteRuleReader.sha256(bytes));
            if (relative.endsWith("/00_ai.route-excerpt.txt")) {
                manifest.put("stock_defines", path.toString()); manifest.put("stock_sha256", StockRouteRuleReader.sha256(bytes));
            }
        }
        Path input = temporary.resolve("INPUT.json"); Files.write(input, StrictJson.canonical(manifest), StandardOpenOption.CREATE_NEW);
        RouteRerouteRegression.main(new String[]{input.toString()});
        JsonNode actual = StrictJson.parse(Files.readAllBytes(temporary.resolve("ACTUAL.json")));
        assertEquals("PASS", actual.path("status").textValue()); assertEquals(24, actual.path("source_bound_original_cases").intValue());
        assertEquals(0, actual.path("game_actions").intValue()); assertFalse(actual.path("live_host_adoption").booleanValue());
    }
}
