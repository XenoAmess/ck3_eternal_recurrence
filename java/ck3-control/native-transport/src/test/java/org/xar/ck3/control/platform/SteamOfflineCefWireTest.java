package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import java.io.IOException;
import java.io.InputStream;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class SteamOfflineCefWireTest {
    private static JsonNode oracle() throws IOException {
        try (InputStream stream = SteamOfflineCefWireTest.class.getResourceAsStream("/steam-offline/python-producer-oracle03.json")) {
            if (stream == null) throw new IOException("Original producer oracle resource missing");
            return StrictJson.parse(stream.readAllBytes(), SteamOfflineObservationCodec.MAXIMUM_BYTES);
        }
    }
    @Test void everyOriginalGetterCaseAndExactReadOnlyExpressionMatches() throws Exception {
        JsonNode oracle = oracle(); String nonce = oracle.path("nonce").textValue();
        assertEquals(oracle.path("getter_expression").textValue(), SteamOfflineCefWire.getterExpression(nonce));
        for (JsonNode row : oracle.path("getter_cases")) {
            if (row.path("status").textValue().equals("reject")) {
                assertThrows(IllegalArgumentException.class, () -> SteamOfflineCefWire.parseGetter(row.get("raw"), nonce));
            } else assertEquals(row.path("status").textValue().equals("offline"), SteamOfflineCefWire.parseGetter(row.get("raw"), nonce));
        }
    }
    @Test void originalDiscoveryRejectsForeignAuthenticationAndMismatchedTargetIds() throws Exception {
        JsonNode input = oracle().path("discovery");
        var targets = SteamOfflineCefWire.targets(input.get("version"), input.get("targets"), false);
        assertEquals(1, targets.size()); assertEquals(input.path("expected").get(0).get(0).textValue(), targets.get(0).id());
        assertEquals(input.path("expected").get(0).get(1).textValue(), targets.get(0).url());
        assertEquals(input.path("expected").get(0).get(2).textValue(), targets.get(0).webSocketUrl());
    }
    @Test void unownedOrMalformedEndpointRejectsBeforeAnyNetworkConnection() {
        for (String url : List.of("ws://example.com:9/devtools/page/a", "ws://127.0.0.1:10/devtools/page/a",
                "ws://user@127.0.0.1:9/devtools/page/a", "http://127.0.0.1:9/devtools/page/a",
                "ws://127.0.0.1:9/devtools/page/a?secret=x", "ws://127.0.0.1:9/devtools/page/a#x")) {
            assertThrows(IllegalArgumentException.class, () -> SteamOfflineCefWire.endpoint(url, 9));
        }
    }
    @Test void onlyExactOriginalDebugPortSwitchesAreReadFromTheUnretainedCommandLine() {
        assertEquals(List.of(9, 9222), SteamOfflineCefProvider.parsePorts("helper --remote-debugging-port=9222 --remote-debugging-port 9 --remote-debugging-port=9222"));
        assertEquals(List.of(), SteamOfflineCefProvider.parsePorts("helper --remote-debugging-port=0 --remote-debugging-port=65536 --remote-debugging-port=9suffix"));
    }

    @Test void cefSourceRequiresTheExactVersionAndItsOwnImage() {
        var legacy = SteamOfflineCefProvider.sourceProfile("10.96.30.42").orElseThrow();
        var steam1123 = SteamOfflineCefProvider.sourceProfile("11.23.65.88").orElseThrow();
        assertEquals("steamui/chunk~2dcc5aaf7.js", legacy.relativePath());
        assertFalse(legacy.allowsStartupQuery());
        assertTrue(legacy.matches(14382868, "f9606b111203c9140dcdd6fc016a0ee00e4c8406aeb786187c42873f08d071fb"));
        assertEquals("steamui/sp.js", steam1123.relativePath());
        assertTrue(steam1123.allowsStartupQuery());
        assertTrue(steam1123.matches(16224005, "4b818cd371388e06c66fe8c0bb592b7dfd4a6fb55eb56844d1b360b64aec3046"));
        assertFalse(steam1123.matches(legacy.bytes(), legacy.sha256()));
        assertFalse(steam1123.matches(steam1123.bytes(), legacy.sha256()));
        assertFalse(steam1123.matches(legacy.bytes(), steam1123.sha256()));
        assertFalse(legacy.matches(steam1123.bytes(), steam1123.sha256()));
        assertTrue(SteamOfflineCefProvider.sourceProfile("11.23.65.89").isEmpty());
    }

    @Test void exactQuotedBrowserAndUnquotedRendererPortsRemainNecessaryForCandidates() {
        assertEquals(List.of(8080), SteamOfflineCefProvider.parsePorts(
                "steamwebhelper.exe \"-steampid=27432\" \"--remote-debugging-port=8080\" \"-uimode=7\""));
        assertEquals(List.of(8080), SteamOfflineCefProvider.parsePorts(
                "steamwebhelper.exe --type=renderer --remote-debugging-port=8080 --lang=zh-CN"));
        assertTrue(SteamOfflineCefProvider.parsePorts("steamwebhelper.exe --type=renderer --lang=zh-CN").isEmpty());
        assertTrue(SteamOfflineCefProvider.parsePorts("steamwebhelper.exe \"--remote-debugging-port=8080\"suffix").isEmpty());
    }

    @Test void actualElevenTwentyThreeStartupContextsSelectTheSharedTarget() throws Exception {
        JsonNode version = oracle().path("discovery").get("version");
        String url = "https://steamloopback.host/index.html?" + STARTUP_QUERY;
        for (String suffix : List.of("", "&SILENT_STARTUP=true", "&SILENT_STARTUP=false")) {
            assertEquals(List.of(new SteamOfflineCefWire.Target("actual", url + suffix, ACTUAL_SOCKET)),
                    SteamOfflineCefWire.targets(version, startupTargets(url + suffix, "SharedJSContext"), true));
            assertTrue(SteamOfflineCefWire.targets(version, startupTargets(url + suffix, "SharedJSContext"), false).isEmpty());
        }
    }

    @Test void startupDiscoveryRequiresTheExactOwnedContextAndNonAuthFields() throws Exception {
        JsonNode version = oracle().path("discovery").get("version");
        String prefix = "https://steamloopback.host/index.html?";
        for (String url : List.of(
                prefix + STARTUP_QUERY + "&access_token=forbidden",
                prefix + STARTUP_QUERY + "&CLIENT%5FSESSION=0",
                prefix + STARTUP_QUERY + "&SILENT_STARTUP=invalid",
                prefix + STARTUP_QUERY.replace("&ARCH=x64", ""),
                prefix + STARTUP_QUERY + "#unexpected",
                "https://other.host/index.html?" + STARTUP_QUERY,
                "https://user@steamloopback.host/index.html?" + STARTUP_QUERY,
                "https://steamloopback.host/login.html?" + STARTUP_QUERY)) {
            assertTrue(SteamOfflineCefWire.targets(version, startupTargets(url, "SharedJSContext"), true).isEmpty(), url);
        }
        assertTrue(SteamOfflineCefWire.targets(version, startupTargets(prefix + STARTUP_QUERY, "OtherPage"), true).isEmpty());
        assertTrue(SteamOfflineCefWire.targets(version, StrictJson.object().putArray("empty"), true).isEmpty());
    }

    private static final String STARTUP_QUERY =
            "LOCAL_HOSTNAME=DESKTOP-3FEVHD2&LANGUAGE=schinese&COUNTRY=JP&"
            + "LAUNCHER_TYPE=0&CLIENT_SESSION=1794940707&PACKAGE_CL=1794536281&"
            + "IN_CLIENT=true&PLATFORM=windows&ARCH=x64";
    private static final String ACTUAL_SOCKET = "ws://127.0.0.1:9/devtools/page/actual";

    private static ArrayNode startupTargets(String url, String title) {
        ArrayNode targets = StrictJson.object().putArray("targets");
        targets.addObject().put("type", "page").put("id", "actual").put("title", title)
                .put("url", url).put("webSocketDebuggerUrl", ACTUAL_SOCKET);
        return targets;
    }
}
