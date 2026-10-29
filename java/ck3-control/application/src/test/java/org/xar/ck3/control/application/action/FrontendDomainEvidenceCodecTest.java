package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;

final class FrontendDomainEvidenceCodecTest {
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    private static ExactRef ref(String name, char digest) { return new ExactRef("D:/fixture/" + name, 10, String.valueOf(digest).repeat(64)); }
    private static FrontendEffectObservation effect(List<ExactRef> supporting) {
        var packet = ref("route.packet", 'a');
        var identity = new FrontendIdentity("frontend-fixture", new GameGeneration(123,
                new PythonOnlyUInt64(new BigInteger("133700000000000001"))), "held-session", new BigInteger("18446744073709551615"),
                123, new FrontendFrame.Menu(BigInteger.TWO), packet, ref("hello.packet", 'b'));
        return new FrontendEffectObservation(identity, new G2Source(identity.machineId(), NOW.toString(), "1.20.0.4", ref("source.java", 'c')),
                "held-session", "frontend-domain/v1", List.of(), "independent-route-2", NOW, packet, supporting);
    }
    @Test void domainBasisRoundTripsThroughTheSoleCodecAndKeepsItsOriginalPacketSeparate() {
        var original = effect(List.of(ref("domain-basis.json", 'd')));
        var row = CommandOriginCodec.frontendEffect(original);
        assertEquals("xar.frontend-effect/v2", row.get("schema").textValue());
        assertEquals(original, CommandOriginCodec.frontendEffect(row));
        assertEquals(List.of(original.originalEvidence(), ref("domain-basis.json", 'd')), original.references());
        assertEquals("18446744073709551615", row.get("after").get("connection_generation").textValue());
    }
    @Test void historicalEmptySupportKeepsTheExactV1FieldDomain() {
        var original = effect(List.of()); var row = CommandOriginCodec.frontendEffect(original);
        assertEquals("xar.frontend-effect/v1", row.get("schema").textValue()); assertFalse(row.has("supporting_evidence"));
        assertEquals(original, CommandOriginCodec.frontendEffect(row));
        row.putArray("supporting_evidence");
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.frontendEffect(row));
    }
    @Test void missingNullWrongTypedEmptyAndDuplicateDomainReferencesAreRejected() {
        var original = effect(List.of(ref("domain-basis.json", 'd')));
        var missing = CommandOriginCodec.frontendEffect(original); missing.remove("supporting_evidence");
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.frontendEffect(missing));
        var nullValue = CommandOriginCodec.frontendEffect(original); nullValue.putNull("supporting_evidence");
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.frontendEffect(nullValue));
        var wrong = CommandOriginCodec.frontendEffect(original); wrong.put("supporting_evidence", true);
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.frontendEffect(wrong));
        var empty = CommandOriginCodec.frontendEffect(original); empty.putArray("supporting_evidence");
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.frontendEffect(empty));
        var duplicate = CommandOriginCodec.frontendEffect(original);
        duplicate.withArray("supporting_evidence").add(ref("domain-basis.json", 'd').toJson());
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.frontendEffect(duplicate));
        assertThrows(IllegalArgumentException.class, () -> effect(List.of(original.originalEvidence())));
    }
}
