package org.xar.ck3.control.wave2.runtime.providerchain;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Locale;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.providerchain.OriginReadbackValues.Reply;
import static org.junit.jupiter.api.Assertions.*;

final class OriginReadbackCodecTest {
    private static JsonNode golden() throws IOException {
        try (InputStream stream = OriginReadbackCodecTest.class.getResourceAsStream("/providerchain/origin-readback-golden.json")) {
            if (stream == null) { throw new IOException("original origin value golden required, never skipped"); }
            return StrictJson.parse(stream.readAllBytes());
        }
    }

    private static ObjectNode fixture() throws IOException { return (ObjectNode) golden().get("cases").get(0).get("reply").deepCopy(); }

    @Test void originalIdentityHelpersAndExactPrivateAsciiLineRoundTrip() throws IOException {
        for (JsonNode sample : golden().get("cases")) {
            Reply value = OriginReadbackCodec.parseReply(sample.get("reply"));
            byte[] raw = OriginReadbackCodec.encodeReply(value);
            assertArrayEquals(sample.get("expected_wire_json").textValue().getBytes(StandardCharsets.UTF_8), raw);
            assertEquals(value, OriginReadbackCodec.decodeReply(raw));
            assertTrue(value.matchesExpected(value.sequence(), value.nonce(), value.body()));
            assertEquals("134368602545256921", value.body().target().creationFiletimeDecimal());
            assertEquals("000102030405060708090a0b0c0d0e0f", value.body().file().fileIdHex());
        }
        Reply wide = OriginReadbackCodec.parseReply(golden().get("cases").get(1).get("reply"));
        assertEquals("18446744073709551615", wide.body().file().volumeSerialDecimal());
        assertEquals(new BigInteger("18446744073709551619"), wide.body().file().size());
    }

    @Test void exactReplyBodyFieldsRejectMissingNullAndQualificationFlags() throws IOException {
        for (String field : List.of("kind", "sequence", "nonce", "body")) {
            ObjectNode missing = fixture(); missing.remove(field);
            assertThrows(ContractViolationException.class, () -> OriginReadbackCodec.parseReply(missing));
            ObjectNode nullable = fixture(); nullable.putNull(field);
            assertThrows(ContractViolationException.class, () -> OriginReadbackCodec.parseReply(nullable));
        }
        for (String field : List.of("epoch", "creator", "target", "file", "origin", "app")) {
            ObjectNode missing = fixture(); ((ObjectNode) missing.get("body")).remove(field);
            assertThrows(ContractViolationException.class, () -> OriginReadbackCodec.parseReply(missing));
            ObjectNode nullable = fixture(); ((ObjectNode) nullable.get("body")).putNull(field);
            assertThrows(ContractViolationException.class, () -> OriginReadbackCodec.parseReply(nullable));
        }
        ObjectNode forged = fixture(); forged.put("source_verified", true);
        assertThrows(ContractViolationException.class, () -> OriginReadbackCodec.parseReply(forged));
    }

    @Test void identityAndSequenceTokensRejectBooleanDecimalAndNumericStringAliases() throws IOException {
        for (String raw : List.of("true", "1.0", "\"1\"", "null", "0", "-1")) {
            JsonNode bad = StrictJson.parse(raw.getBytes(StandardCharsets.UTF_8));
            ObjectNode sequence = fixture(); sequence.set("sequence", bad);
            assertThrows(ContractViolationException.class, () -> OriginReadbackCodec.parseReply(sequence));
            ObjectNode pid = fixture(); ((ArrayNode) pid.get("body").get("target")).set(0, bad);
            assertThrows(ContractViolationException.class, () -> OriginReadbackCodec.parseReply(pid));
            ObjectNode size = fixture(); ((ArrayNode) size.get("body").get("file")).set(2, bad);
            assertThrows(ContractViolationException.class, () -> OriginReadbackCodec.parseReply(size));
        }
        for (String raw : List.of("134368602545256921", "134368602545256921.0", "true", "\"0134368602545256921\"",
                "\"18446744073709551616\"", "\"0\"", "null")) {
            ObjectNode changed = fixture();
            ((ArrayNode) changed.get("body").get("target")).set(1, StrictJson.parse(raw.getBytes(StandardCharsets.UTF_8)));
            assertThrows(ContractViolationException.class, () -> OriginReadbackCodec.parseReply(changed));
        }
        ObjectNode zeroVolume = fixture(); ((ArrayNode) zeroVolume.get("body").get("file")).set(0, StrictJson.parse("\"0\"".getBytes(StandardCharsets.UTF_8)));
        assertEquals("0", OriginReadbackCodec.parseReply(zeroVolume).body().file().volumeSerialDecimal());
    }

    @Test void fileIdentityPreservesAllSixteenBytesAndItsIndependentDigest() throws IOException {
        for (String value : List.of("00".repeat(15), "00".repeat(17), "FF".repeat(16), "garbage")) {
            ObjectNode changed = fixture(); ((ArrayNode) changed.get("body").get("file")).set(1,
                    StrictJson.parse(("\"" + value + "\"").getBytes(StandardCharsets.UTF_8)));
            assertThrows(ContractViolationException.class, () -> OriginReadbackCodec.parseReply(changed));
        }
        Reply base = OriginReadbackCodec.parseReply(fixture());
        for (int field : List.of(0, 1, 3, 4)) {
            ObjectNode changed = fixture(); ArrayNode file = (ArrayNode) changed.get("body").get("file");
            String next = switch (field) { case 0 -> "2"; case 1 -> "ff".repeat(16); case 3 -> "f".repeat(64); default -> "C:/other/lease.bin"; };
            file.set(field, StrictJson.parse(("\"" + next + "\"").getBytes(StandardCharsets.UTF_8)));
            Reply other = OriginReadbackCodec.parseReply(changed);
            assertFalse(base.matchesExpected(base.sequence(), base.nonce(), other.body()));
        }
    }

    @Test void changedEpochGenerationNonceSequenceAndCaseCannotMatchExpectedValues() throws IOException {
        Reply expected = OriginReadbackCodec.parseReply(fixture());
        ObjectNode opaqueEpoch = fixture(); ((ObjectNode) opaqueEpoch.get("body")).put("epoch", "actual");
        assertEquals("actual", OriginReadbackCodec.parseReply(opaqueEpoch).body().epoch().value(),
                "existing original consumer fixtures use an opaque epoch, not an extra hash-field contract");
        assertFalse(expected.matchesExpected(expected.sequence().add(BigInteger.ONE), expected.nonce(), expected.body()));
        assertFalse(expected.matchesExpected(expected.sequence(), "0".repeat(32), expected.body()));
        for (String field : List.of("epoch", "creator")) {
            ObjectNode changed = fixture(); ((ObjectNode) changed.get("body")).put(field, "0".repeat(64));
            assertFalse(expected.matchesExpected(expected.sequence(), expected.nonce(), OriginReadbackCodec.parseReply(changed).body()));
        }
        ObjectNode changedBirth = fixture(); ((ArrayNode) changedBirth.get("body").get("target")).set(1,
                StrictJson.parse("\"134368602545256922\"".getBytes(StandardCharsets.UTF_8)));
        assertFalse(expected.matchesExpected(expected.sequence(), expected.nonce(), OriginReadbackCodec.parseReply(changedBirth).body()));
        ObjectNode changedCase = fixture(); ArrayNode target = (ArrayNode) changedCase.get("body").get("target");
        ObjectNode uppercase = StrictJson.object(); uppercase.put("path", target.get(2).textValue().toUpperCase(Locale.ROOT));
        target.set(2, uppercase.get("path"));
        assertFalse(expected.matchesExpected(expected.sequence(), expected.nonce(), OriginReadbackCodec.parseReply(changedCase).body()));
    }

    @Test void rawOriginalWireFloatAndBooleanTokensReachTheActualDecoderUnchanged() throws IOException {
        String original = golden().get("cases").get(0).get("expected_wire_json").textValue();
        for (String token : List.of("7.0", "true", "\"7\"")) {
            String changed = original.replace("\"sequence\":7,", "\"sequence\":" + token + ",");
            assertNotEquals(original, changed, "the raw original sequence token must actually change");
            assertThrows(ContractViolationException.class,
                    () -> OriginReadbackCodec.decodeReply(changed.getBytes(StandardCharsets.UTF_8)));
        }
        String pidFloat = original.replace("\"target\":[71,", "\"target\":[71.0,");
        assertNotEquals(original, pidFloat);
        assertThrows(ContractViolationException.class,
                () -> OriginReadbackCodec.decodeReply(pidFloat.getBytes(StandardCharsets.UTF_8)));
    }

    @Test void privateMessageBoundDuplicateFieldsAndMalformedUtf8RemainRejected() throws IOException {
        Reply expected = OriginReadbackCodec.parseReply(fixture());
        byte[] raw = OriginReadbackCodec.encodeReply(expected);
        String text = new String(raw, StandardCharsets.UTF_8).stripTrailing();
        String duplicate = text.substring(0, text.length() - 1) + ",\"sequence\":7}";
        assertThrows(ContractViolationException.class, () -> OriginReadbackCodec.decodeReply(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> OriginReadbackCodec.decodeReply((text + "{}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> OriginReadbackCodec.decodeReply(new byte[16_385]));
        assertThrows(ContractViolationException.class, () -> OriginReadbackCodec.decodeReply(new byte[] {(byte) 0xff}));
    }
}
