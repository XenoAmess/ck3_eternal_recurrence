package org.xar.ck3.control.wave2.events.uirecoveryidentity;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.uirecoveryidentity.UiRecoverySourceModel.*;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Optional;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;

final class UiRecoverySourceFingerprintTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);
    @TestFactory Stream<DynamicTest> actualUnmodifiedStableSourceProducerGolden() throws IOException {
        JsonNode golden = golden(); assertEquals(20, golden.path("cases").size());
        return StreamSupport.stream(golden.path("cases").spliterator(), false).map(row ->
                DynamicTest.dynamicTest(row.path("name").textValue(), () -> {
                    JsonNode actual = JSON.readTree(UiRecoveryIdentityJson.fingerprint(JSON.writeValueAsBytes(row.get("request"))));
                    assertEquals(row.get("output"), actual, "legacy stable source key and exact normalized source");
                }));
    }
    @Test void canonicalBytesHashAndIdentityConsumerUseExactSourceWithoutBusinessCredit() throws Exception {
        ObjectNode request = request("native_numeric_rva_parallel_catalogue");
        Ready ready = (Ready) UiRecoveryIdentityJson.decode(JSON.writeValueAsBytes(request));
        UiRecoveryIdentityPort consumer = new UiRecoverySourceFingerprint();
        Fingerprint fingerprint = consumer.identify(ready.input()).orElseThrow();
        String canonical = StableSourceCanonical.source(fingerprint.stableSource());
        assertEquals(fingerprint.sourceKey(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(canonical.getBytes(StandardCharsets.UTF_8))));
        JsonNode output = JSON.readTree(UiRecoveryIdentityJson.fingerprint(JSON.writeValueAsBytes(request), consumer));
        assertEquals(JSON.readTree(canonical), output.get("stable_source"));
        assertFalse(fingerprint.observedUiRecoveryVerified()); assertFalse(fingerprint.businessEffectKnown());
        assertFalse(fingerprint.semanticOptimal()); assertFalse(fingerprint.replayAllowed());
        assertThrows(UnsupportedOperationException.class, () -> ready.input().source().catalogue().clear());
    }
    @Test void rawBoolAndFloatRvaTokensAndDuplicateDisplayIdentitiesCannotMintSourceKeys() throws IOException {
        String baseline = JSON.writeValueAsString(request("native_numeric_rva_parallel_catalogue"));
        for (String token : new String[] {"true", "1.0", "0", "-1", "18446744073709551616"}) {
            String raw = baseline.replace("\"root_vtable_module_rva\":1193046", "\"root_vtable_module_rva\":" + token);
            assertNotEquals(baseline, raw, "negative test must deliver actual wrong JSON token");
            assertTrue(JSON.readTree(UiRecoveryIdentityJson.fingerprint(raw.getBytes(StandardCharsets.UTF_8))).isNull());
        }
        ObjectNode input = request("native_numeric_rva_parallel_catalogue");
        ((ObjectNode) input.path("window").path("choices").get(0)).put("choice_id", 1);
        ((ObjectNode) input.path("window").path("choices").get(1)).put("choice_id", "1");
        assertTrue(JSON.readTree(UiRecoveryIdentityJson.fingerprint(JSON.writeValueAsBytes(input))).isNull());
    }
    @Test void strictWrapperAndMalformedEncodingRejectWhileNativeExtensionsAreProjected() throws IOException {
        ObjectNode input = request("native_numeric_rva_parallel_catalogue");
        ObjectNode missing = input.deepCopy(); missing.remove("backend_sha256");
        assertThrows(IllegalArgumentException.class, () -> UiRecoveryIdentityJson.decode(JSON.writeValueAsBytes(missing)));
        ObjectNode unknown = input.deepCopy(); unknown.put("known_source", true);
        assertThrows(IllegalArgumentException.class, () -> UiRecoveryIdentityJson.decode(JSON.writeValueAsBytes(unknown)));
        String valid = JSON.writeValueAsString(input);
        assertThrows(IllegalArgumentException.class, () -> UiRecoveryIdentityJson.decode(("{\"schema\":\"duplicate\"," + valid.substring(1)).getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> UiRecoveryIdentityJson.decode((valid + " null").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> UiRecoveryIdentityJson.decode(new byte[] {(byte) 0xc3, 0x28}));
        ((ObjectNode) input.get("window")).put("sdk_extension", "ignored container extension");
        assertFalse(JSON.readTree(UiRecoveryIdentityJson.fingerprint(JSON.writeValueAsBytes(input))).isNull());
    }
    @Test void missingAndNullRoleRemainDifferentBeforeCanonicalNormalization() throws IOException {
        Ready missing = (Ready) UiRecoveryIdentityJson.decode(JSON.writeValueAsBytes(request("existing_symbolic_rva_producer")));
        assertEquals(org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.Presence.MISSING,
                missing.input().source().catalogue().getFirst().role().presence());
        Ready nullable = (Ready) UiRecoveryIdentityJson.decode(JSON.writeValueAsBytes(request("missing_label_and_null_catalogue_role")));
        assertEquals(org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.Presence.NULL,
                nullable.input().source().catalogue().getFirst().role().presence());
        Optional<Fingerprint> result = new UiRecoverySourceFingerprint().identify(nullable.input());
        assertTrue(result.orElseThrow().stableSource().catalogue().getFirst().role().isEmpty());
        assertTrue(result.orElseThrow().stableSource().catalogue().getFirst().label().isEmpty());
    }
    private static JsonNode golden() throws IOException {
        try (InputStream input = UiRecoverySourceFingerprintTest.class.getResourceAsStream("/uirecoveryidentity/producer-golden-v1.json")) {
            if (input == null) { throw new IOException("actual stable_source_key golden missing; capture has not run"); }
            return JSON.readTree(input);
        }
    }
    private static ObjectNode request(String name) throws IOException {
        for (JsonNode row : golden().path("cases")) { if (name.equals(row.path("name").textValue())) { return (ObjectNode) row.get("request").deepCopy(); } }
        throw new IOException("missing producer vector " + name);
    }
}
