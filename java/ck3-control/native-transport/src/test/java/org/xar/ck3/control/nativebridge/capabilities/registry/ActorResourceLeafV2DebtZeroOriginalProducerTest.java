package org.xar.ck3.control.nativebridge.capabilities.registry;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Locale;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;

/** Actual C++ RAM formatter originals only; no expected JSON is promoted to producer evidence. */
final class ActorResourceLeafV2DebtZeroOriginalProducerTest {
    private static ActorResourceLeafV2.Partial read(String kind)throws Exception {
        String prefix="xar.resource.leaf.v2."+kind;
        String file=System.getProperty(prefix+".file"),sha=System.getProperty(prefix+".sha256");
        assertNotNull(file,"NOT_RUN: actual C++ --emit "+kind+" original path required");
        assertNotNull(sha,"NOT_RUN: actual C++ original SHA256 required");
        Path path=Path.of(file);assertTrue(path.isAbsolute());assertTrue(sha.matches("[0-9A-Fa-f]{64}"));
        byte[] bytes=Files.readAllBytes(path);
        assertEquals(sha.toLowerCase(Locale.ROOT),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        return assertInstanceOf(ActorResourceLeafV2.Partial.class,
                ActorResourceLeafV2.decodePacket(new RawJson(bytes),"ram-resource-leaf-v2"));
    }
    @Test void oneQuantumDebtAndLegalZeroNeverBecomeGovernmentTreasury()throws Exception {
        var debt=read("debt");var amounts=debt.observedNonCash().orElseThrow();
        assertEquals(-200000,amounts.prestige().raw());assertEquals(-1,amounts.piety().raw());
        assertEquals(100000,amounts.piety().scale());assertEquals(-500000,debt.goldInterval().before().raw());
        assertEquals(debt.goldInterval().before(),debt.goldInterval().after());
        assertEquals(ActorResourceLeafV2.TREASURY_UNKNOWN,debt.trueTreasury().reason());
        assertEquals(ActorResourceLeafV2.RENOWN_UNKNOWN,debt.renown().reason());
        var zero=read("zero");var zeroAmounts=zero.observedNonCash().orElseThrow();
        assertEquals(0,zeroAmounts.prestige().raw());assertEquals(0,zeroAmounts.piety().raw());
        assertEquals(0,zero.goldInterval().before().raw());
        assertEquals(zero,ActorResourceLeafV2.decode(ActorResourceLeafV2.encode(zero)));
        var encoded=RegistryJson.object(ActorResourceLeafV2.encode(zero));
        assertEquals("available",encoded.path("resources").path("prestige").path("status").textValue());
        assertEquals(0,encoded.path("resources").path("piety").path("amount").path("raw").longValue());
        assertEquals("unavailable",encoded.path("resources").path("true_treasury").path("status").textValue());
        assertTrue(encoded.path("resources").path("true_treasury").path("amount").isNull());
        assertTrue(encoded.path("resources").path("renown").path("amount").isNull());
        assertFalse(encoded.get("root_ready").booleanValue());assertFalse(encoded.get("formal_action_ready").booleanValue());
    }
}
