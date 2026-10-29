package org.xar.ck3.control.g2.m1;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionProtocolException;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmDifferenceCodec;

/** Default Surefire entry: real original corpora, then the public G2/M1 wire and source/result consumers. */
public final class M1ResearchTest {
    @Test void defaultVerificationExecutesCompleteDomainChecksWithoutSkippingMissingEvidence() throws IOException {
        byte[] realm = resource("/m1-domain/realmcompare.json");
        assertEquals("e41dcc3cc24699ea753618345bf6c89243ce4b7aa2ebcae64057b3e4cd2aa697", sha(realm));
        int checks = M1DomainChecks.run(realm,
                new String(resource("/m1/saved-membership.jsonl"), StandardCharsets.UTF_8).lines().toList(),
                resource("/m1/monthly-observation.json"));
        assertTrue(checks >= 50, "complete actual producer and new boundary cases must execute");
    }

    @Test void publicRequestAndResponseKeepExactSourceAndOriginalDecimalTokenBoundaries() throws IOException {
        ObjectNode input = firstDifference();
        String ordinary = new ObjectMapper().writeValueAsString(input);
        String fractional = ordinary.replace("\"native_revision\":42", "\"native_revision\":42.0");
        assertTrue(fractional.contains("\"native_revision\":42.0"));
        byte[] leaf = fractional.getBytes(StandardCharsets.UTF_8);
        byte[] payload = ("{\"input\":" + fractional + ",\"operation\":\"native-difference\"}").getBytes(StandardCharsets.UTF_8);
        G2Request original = request("m1-raw-decimal", payload);
        G2Request decoded = G2Wire.decodeRequest(G2Wire.encodeRequest(original));
        assertArrayEquals(payload, decoded.payload().bytes());
        G2Response result = new M1Research().evaluate(decoded);
        assertArrayEquals(RealmDifferenceCodec.evaluate(leaf), result.result().bytes());
        assertEquals("unavailable", StrictJson.parse(result.result().bytes()).path("status").textValue());
        G2Response consumed = G2Wire.decodeResponse(G2Wire.encodeResponse(result));
        assertEquals(original.source(), consumed.source());
        assertEquals(original.requestId(), consumed.requestId());
        assertEquals(Milestone.M1, consumed.milestone());
        assertArrayEquals(result.result().bytes(), consumed.result().bytes());
    }

    @Test void originalUint64SourceTokensCrossThePublicEnvelopeWithoutJavascriptNumberRounding() throws IOException {
        ObjectNode input = firstDifference();
        BigInteger identity = new BigInteger("9007199254740993");
        for (String side : new String[] {"previous", "observation"}) {
            ((ObjectNode) input.path(side).path("source_frame")).put("connection_generation", identity);
        }
        byte[] leaf = new ObjectMapper().writeValueAsBytes(input);
        byte[] payload = ("{\"operation\":\"native-difference\",\"input\":" + new String(leaf, StandardCharsets.UTF_8) + "}")
                .getBytes(StandardCharsets.UTF_8);
        G2Response result = new M1Research().evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(request("m1-uint64", payload))));
        JsonNode consumed = StrictJson.parse(G2Wire.decodeResponse(G2Wire.encodeResponse(result)).result().bytes(),
                StrictJson.EXPLICIT_MAX_BYTES);
        assertEquals("available", consumed.path("status").textValue());
        assertEquals(identity, consumed.path("before_source_frame").path("connection_generation").bigIntegerValue());
        assertEquals(identity, consumed.path("after_source_frame").path("connection_generation").bigIntegerValue());
    }

    @Test void unknownMissingAndRepeatedWrapperFieldsFailTheActualDomainEntry() {
        for (String payload : new String[] {
                "{\"operation\":\"native-difference\"}",
                "{\"operation\":\"native-difference\",\"input\":{},\"extra\":0}",
                "{\"operation\":\"invented\",\"input\":{}}"}) {
            assertThrows(ContractViolationException.class,
                    () -> new M1Research().evaluate(request("m1-invalid", payload.getBytes(StandardCharsets.UTF_8))));
        }
        assertThrows(ProjectionProtocolException.class, () -> request("m1-duplicate",
                "{\"operation\":\"native-difference\",\"operation\":\"native-cache\",\"input\":{}}".getBytes(StandardCharsets.UTF_8)));
    }

    private static ObjectNode firstDifference() throws IOException {
        return (ObjectNode) StrictJson.parse(resource("/m1-domain/realmcompare.json"), StrictJson.EXPLICIT_MAX_BYTES)
                .path("cases").get(0).path("request");
    }
    private static G2Request request(String id, byte[] payload) {
        G2Source source = new G2Source("xenoamess-full-tower-eb9d2c1186", "2026-10-22T20:45:06Z",
                "software-original-producer-fixture", new ExactRef("memory:m1-original-fixture", payload.length, sha(payload)));
        return new G2Request(id, Milestone.M1, source, ProjectionJson.object(payload, M1Research.MAX_BYTES));
    }
    private static byte[] resource(String name) throws IOException {
        try (InputStream stream = M1ResearchTest.class.getResourceAsStream(name)) {
            if (stream == null) throw new IOException("mandatory actual M1 corpus absent: " + name);
            return stream.readAllBytes();
        }
    }
    private static String sha(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (java.security.NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}
