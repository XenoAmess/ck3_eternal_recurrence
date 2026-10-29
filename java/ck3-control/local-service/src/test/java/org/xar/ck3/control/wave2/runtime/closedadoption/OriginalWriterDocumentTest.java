package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;

class OriginalWriterDocumentTest {
    private static ObjectNode envelope(byte[] raw) {
        ObjectNode row = StrictJson.object();
        row.set("ref",new ExactRef("fixture-head.json",raw.length,RecoveryEvidence.sha256(raw)).toJson());
        row.set("identity",new FileStatIdentity(BigInteger.valueOf(raw.length),"1","1").toJson());
        row.put("raw_utf8",new String(raw,StandardCharsets.UTF_8)); return row;
    }
    private static byte[] actualHead() throws IOException {
        String explicit = System.getProperty("xar.repo");
        if (explicit == null || explicit.isBlank()) { explicit = System.getenv("XAR_REPO_ROOT"); }
        Path current = Path.of(explicit == null || explicit.isBlank() ? System.getProperty("user.dir") : explicit).toAbsolutePath();
        for (int count = 0; count < 6 && current != null; count++, current = current.getParent()) {
            Path source = current.resolve("java/ck3-control/admission-contracts/src/test/resources/closedpartial/n46-head240.actual.json");
            if (Files.isRegularFile(source)) {
                try (var input = Files.newInputStream(source)) { byte[] raw = input.readNBytes(RecoveryEvidence.MAX_BYTES+1); assertTrue(raw.length <= RecoveryEvidence.MAX_BYTES); return raw; }
            }
        }
        throw new IllegalStateException("UNAVAILABLE: actual head240 metadata fixture required; set xar.repo or XAR_REPO_ROOT");
    }
    @Test void actualHeadIsACompleteDocumentBeyondTheGenericValueTextCap() throws Exception {
        byte[] raw = actualHead(); String text = new String(raw,StandardCharsets.UTF_8);
        assertEquals(37_424,raw.length); assertEquals(37_424,text.codePointCount(0,text.length()));
        assertEquals("86af210b06d5d60b2d1f6ac5f1f0a6d31098b518583da06270596a71b068463a",RecoveryEvidence.sha256(raw));
        assertThrows(ContractViolationException.class,() -> StrictJson.text(text));
        OriginalWriterTransaction.Document decoded = OriginalWriterTransaction.Document.decode(envelope(raw));
        assertArrayEquals(raw,decoded.evidence().bytes()); assertEquals(240,decoded.value().get("sequence").longValue());
    }
    @Test void readbackRetainsExactHashLengthIdentityAndJsonObjectGuards() {
        byte[] raw = "{}".getBytes(StandardCharsets.UTF_8); ObjectNode hash = envelope(raw);
        ((ObjectNode)hash.get("ref")).put("sha256","0".repeat(64));
        assertThrows(ContractViolationException.class,() -> OriginalWriterTransaction.Document.decode(hash));
        ObjectNode identity = envelope(raw); ((ObjectNode)identity.get("identity")).put("bytes",3);
        assertThrows(ContractViolationException.class,() -> OriginalWriterTransaction.Document.decode(identity));
        assertThrows(ContractViolationException.class,() -> OriginalWriterTransaction.Document.decode(envelope("[]".getBytes(StandardCharsets.UTF_8))));
        ObjectNode wrongType = envelope(raw); wrongType.put("raw_utf8",true);
        assertThrows(ContractViolationException.class,() -> OriginalWriterTransaction.Document.decode(wrongType));
    }
    @Test void documentByteBudgetAndMalformedUnicodeRemainRejected() {
        byte[] atCap = ("{\"x\":\""+"a".repeat(RecoveryEvidence.MAX_BYTES-8)+"\"}").getBytes(StandardCharsets.UTF_8);
        assertEquals(RecoveryEvidence.MAX_BYTES,atCap.length);
        assertArrayEquals(atCap,OriginalWriterTransaction.Document.decode(envelope(atCap)).evidence().bytes());
        byte[] overflow = ("{\"x\":\""+"a".repeat(RecoveryEvidence.MAX_BYTES-7)+"\"}").getBytes(StandardCharsets.UTF_8);
        assertThrows(ContractViolationException.class,() -> OriginalWriterTransaction.Document.decode(envelope(overflow)));
        ObjectNode invalid = envelope("{}".getBytes(StandardCharsets.UTF_8)); invalid.put("raw_utf8","\ud800");
        assertThrows(ContractViolationException.class,() -> OriginalWriterTransaction.Document.decode(invalid));
        byte[] multibyteOverflow = ("{\"x\":\""+"中".repeat(22_000)+"\"}").getBytes(StandardCharsets.UTF_8);
        assertThrows(ContractViolationException.class,() -> OriginalWriterTransaction.Document.decode(envelope(multibyteOverflow)));
    }
}
