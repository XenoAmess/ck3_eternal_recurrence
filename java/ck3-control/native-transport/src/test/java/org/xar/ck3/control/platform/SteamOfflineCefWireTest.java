package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
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
        var targets = SteamOfflineCefWire.targets(input.get("version"), input.get("targets"));
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
}
