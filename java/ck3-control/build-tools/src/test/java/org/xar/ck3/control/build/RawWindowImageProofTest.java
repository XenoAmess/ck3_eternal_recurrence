package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import static org.junit.jupiter.api.Assertions.*;

/** Reads the retained actual producer original as a fixture; never opens that machine's historical EXE path. */
final class RawWindowImageProofTest {
    @TempDir Path temporary;
    private static final String ACTUAL_SHA = "4fe465cf2fe32ba51e1df1d318b0318bb3444aa394e6c37a4083cd082e43cd17";
    @Test void actualRetainedFullHashProducerDecodesAndRoundTripsIdentityWithoutAnotherImageHash() throws Exception {
        byte[] raw = actual(); assertEquals(6746, raw.length); assertEquals(ACTUAL_SHA, RawWindowCaptureJson.hash(raw));
        var proof = decode(raw);
        assertEquals("xenoamess-full-tower-eb9d2c1186", proof.machineId());
        assertEquals("98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518", proof.sha256());
        assertEquals("281474999561719", proof.identity().fileId128Decimal());
        assertEquals("15312367356600444416", proof.identity().volumeSerial64Decimal());
        assertEquals(101040248, proof.identity().size());
        assertEquals("134370711579008289", proof.identity().changeFiletime());
    }
    @Test void originalPinAndHistoricalBeforeAfterDriftCannotBorrowCurrentIdentity() throws Exception {
        byte[] raw = actual();
        assertThrows(IOException.class, () -> RawWindowImageProof.decode(new FileRef(temporary.resolve("original.json").toString(), raw.length, "0".repeat(64)), raw));
        ObjectNode root = tree(raw); root.withObject("after").put("change_filetime", "134370711579008290"); rejects(root);
        root = tree(raw); root.withObject("before").put("file_id128_decimal", "281474999561720"); rejects(root);
    }
    @Test void exactIdentityAndFullHashStreamLengthRejectCoercionMissingAndExtraFields() throws Exception {
        byte[] raw = actual(); ObjectNode root = tree(raw); root.withObject("before").put("file_id128_decimal", 281474999561719L); rejects(root);
        root = tree(raw); root.withObject("before").put("size", true); rejects(root);
        root = tree(raw); root.withObject("budget").put("one_full_sha_stream_bytes", 101040248.0); rejects(root);
        root = tree(raw); root.withObject("budget").put("one_full_sha_stream_bytes", 1); rejects(root);
        root = tree(raw); root.remove("sha256"); rejects(root);
        root = tree(raw); root.put("unknown", true); rejects(root);
        root = tree(raw); root.withObject("before").put("file_id128_decimal", "0281474999561719"); rejects(root);
    }
    @Test void inheritedOrSourceOnlyClaimsCannotReplaceTheKnownActualWholeHashProducer() throws Exception {
        byte[] raw = actual(); ObjectNode root = tree(raw); root.put("schema", "xar.g2.m6.activity-save-actual-secondary-source/v18b"); rejects(root);
        root = tree(raw); root.put("status", "SOURCE_ONLY_NOT_RUN"); rejects(root);
        root = tree(raw); root.put("handle_policy", "current path size and mtime only"); rejects(root);
    }
    private RawWindowImageProof.Proof decode(byte[] raw) throws IOException {
        return RawWindowImageProof.decode(new FileRef(temporary.resolve("original.json").toString(), raw.length, RawWindowCaptureJson.hash(raw)), raw);
    }
    private void rejects(ObjectNode root) { assertThrows(Exception.class, () -> decode(root.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8))); }
    private static ObjectNode tree(byte[] raw) throws IOException { return (ObjectNode) RawWindowCaptureJson.tree(raw); }
    private static byte[] actual() throws IOException {
        try (InputStream input = RawWindowImageProofTest.class.getResourceAsStream("/native-raw-window/fullhash-source17-original.json")) {
            if (input == null) throw new IOException("required retained actual full-hash original fixture missing; not skipped"); return input.readAllBytes();
        }
    }
}
