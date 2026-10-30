package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Assertions;

/**
 * Normal JUnit5 test consuming shared golden resources prepared by the native fixture.
 * It frames the raw JSON bytes with NativeWire.packet and decodes them with the actual
 * NativeWire.decode, verifying envelope fields, exact status text, and byte-for-byte
 * payload retention without reserialization.
 */
public final class CommandResultDiagnosticJsonTest {

    private static final String RESOURCE_PREFIX = "/org/xar/ck3/control/nativebridge/command-result-json-v1/";

    private static final String NONWAR_REQUEST_ID = "fixture-nonwar";
    private static final String CONTROLS_REQUEST_ID = "fixture-controls";
    private static final String STEP = "private-query-fixture-v1";

    // Exact expected nonwar diagnostic from the working fixture/golden
    private static final String NONWAR_ERROR =
        "nonwar private snapshot revision is stale or malformed: cause=full_snapshot_changed expected_revision=3 native_revision=3 changed_snapshot_fields=[\"date_raw\"]";

    // Build control expected string using explicit (char)1 and (char)0 to avoid literal NUL in source
    private static final String CONTROLS_STATUS =
        "path=C:\\save\\slot\nnext\t" + (char)1 + (char)0 + "\"quoted\"";

    private static byte[] readResource(String name) throws IOException {
        InputStream stream = CommandResultDiagnosticJsonTest.class.getResourceAsStream(RESOURCE_PREFIX + name);
        if (stream == null) {
            throw new AssertionError("missing golden resource: " + RESOURCE_PREFIX + name);
        }
        try (InputStream input = stream) {
            return input.readAllBytes();
        }
    }

    @Test
    void nonwarCommandResultDecodesWithExactErrorAndAbsentResult() throws Exception {
        byte[] rawJson = readResource("nonwar.json");
        byte[] framed = NativeWire.packet(rawJson);
        NativeWire.Frame frame = NativeWire.decode(framed);

        Assertions.assertTrue(frame instanceof NativeWire.CommandResult, "command_result required");
        NativeWire.CommandResult result = (NativeWire.CommandResult) frame;

        Assertions.assertEquals(NONWAR_REQUEST_ID, result.requestId());
        Assertions.assertFalse(result.nativeOk());

        // error present, result absent
        Assertions.assertEquals(NativeWire.Presence.VALUE, result.error().presence());
        Assertions.assertEquals(NativeWire.Presence.ABSENT, result.result().presence());

        // exact error text
        String actualError = NativeWire.text(NativeWire.parse(result.error().token().orElseThrow().value()));
        Assertions.assertEquals(NONWAR_ERROR, actualError);

        // retained payload and packet equal original bytes, no reserialization
        Assertions.assertTrue(Arrays.equals(rawJson, result.payload().value()), "payload must equal original JSON bytes");
        Assertions.assertTrue(Arrays.equals(framed, result.packet().value()), "packet must equal framed bytes");
    }

    @Test
    void controlsCommandResultDecodesWithExactStatusAndAbsentError() throws Exception {
        byte[] rawJson = readResource("controls.json");
        byte[] framed = NativeWire.packet(rawJson);
        NativeWire.Frame frame = NativeWire.decode(framed);

        Assertions.assertTrue(frame instanceof NativeWire.CommandResult, "command_result required");
        NativeWire.CommandResult result = (NativeWire.CommandResult) frame;

        Assertions.assertEquals(CONTROLS_REQUEST_ID, result.requestId());
        Assertions.assertTrue(result.nativeOk());

        // result present, error absent
        Assertions.assertEquals(NativeWire.Presence.VALUE, result.result().presence());
        Assertions.assertEquals(NativeWire.Presence.ABSENT, result.error().presence());

        // parse result body and check step/accepted/status
        var body = NativeWire.parse(result.result().token().orElseThrow().value());
        Assertions.assertTrue(body.path("accepted").asBoolean(), "accepted must be true");
        Assertions.assertEquals(STEP, body.path("step").asText());

        String actualStatus = NativeWire.text(body.get("status"));
        Assertions.assertEquals(CONTROLS_STATUS, actualStatus);

        // retained payload and packet equal original bytes, no reserialization
        Assertions.assertTrue(Arrays.equals(rawJson, result.payload().value()), "payload must equal original JSON bytes");
        Assertions.assertTrue(Arrays.equals(framed, result.packet().value()), "packet must equal framed bytes");
    }
}
