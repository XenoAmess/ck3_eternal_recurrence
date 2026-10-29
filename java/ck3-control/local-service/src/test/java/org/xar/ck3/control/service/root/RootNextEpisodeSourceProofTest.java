package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.readiness.NativeSourceFileIdentity;
import org.xar.ck3.control.application.readiness.NativeSourceFileIdentity.SourceWitness;
import org.xar.ck3.control.application.readiness.NativeSourceProofCodec;
import org.xar.ck3.control.application.readiness.NativeSourceProofDocument;
import org.xar.ck3.control.contracts.ExactRef;

/** The actual NEXT historical consumer uses the sole v3 codec, without issuing a live source lease. */
final class RootNextEpisodeSourceProofTest {
    private static final String SHA = "a".repeat(64);
    private static ExactRef reference(String name) { return new ExactRef("D:/software-data-only/next-source/" + name, 3, SHA); }
    private static NativeSourceProofDocument document() {
        var host = reference("host.json"); var game = reference("ck3.exe"); var evidence = reference("native.json");
        var identity = new NativeSourceFileIdentity("18446744073709551615", "340282366920938463463374607431768211455",
                "4294967295", "ffffffffffffffff", "18446744073709551615", "9007199254740993", "9007199254740995", 3, 4096, 1);
        return new NativeSourceProofDocument("software-data-machine", "software-data-session", "2026-10-24T19:00:00Z",
                NativeSourceProofDocument.Mode.MCP_STDIO, host, reference("source.json"), SHA, reference("epoch.json"),
                game, List.of(game, evidence), List.of(new SourceWitness(host, identity), new SourceWitness(game, identity),
                        new SourceWitness(evidence, identity)));
    }
    @Test void soleCodecRetainsOriginalWitnessesAndConsumerBindsExactHistoricalSource() throws Exception {
        var original = document(); byte[] encoded = NativeSourceProofCodec.encode(original);
        var retained = RootNextEpisodeDomainReads.requireCapturedSourceProof(encoded, original.machineId(), original.sessionId(), original.source());
        assertEquals(original, retained); assertArrayEquals(encoded, NativeSourceProofCodec.encode(retained));
        assertEquals("340282366920938463463374607431768211455", retained.liveWitnesses().getFirst().nativeFile().fileIdDecimal());
        assertThrows(IllegalArgumentException.class, () -> RootNextEpisodeDomainReads.requireCapturedSourceProof(encoded,
                "another-machine", original.sessionId(), original.source()));
        assertThrows(IllegalArgumentException.class, () -> RootNextEpisodeDomainReads.requireCapturedSourceProof(encoded,
                original.machineId(), "another-session", original.source()));
        assertThrows(IllegalArgumentException.class, () -> RootNextEpisodeDomainReads.requireCapturedSourceProof(encoded,
                original.machineId(), original.sessionId(), reference("another-source.json")));
    }
    @Test void matchingHashOnlyV2AndLostOrRoundedWitnessCannotEnterNextHistory() throws Exception {
        var original = document(); ObjectMapper json = new ObjectMapper();
        ObjectNode old = (ObjectNode) json.readTree(NativeSourceProofCodec.encode(original));
        old.put("schema", "xar.java-root-native-source-proof/v2"); old.remove("live_witnesses");
        assertThrows(IOException.class, () -> RootNextEpisodeDomainReads.requireCapturedSourceProof(json.writeValueAsBytes(old),
                original.machineId(), original.sessionId(), original.source()));
        ObjectNode lost = (ObjectNode) json.readTree(NativeSourceProofCodec.encode(original)); lost.remove("live_witnesses");
        assertThrows(IOException.class, () -> RootNextEpisodeDomainReads.requireCapturedSourceProof(json.writeValueAsBytes(lost),
                original.machineId(), original.sessionId(), original.source()));
        ObjectNode rounded = (ObjectNode) json.readTree(NativeSourceProofCodec.encode(original));
        ((ObjectNode) rounded.get("live_witnesses").get(0).get("native_file")).put("file_id_decimal", 9_007_199_254_740_992L);
        assertThrows(IOException.class, () -> RootNextEpisodeDomainReads.requireCapturedSourceProof(json.writeValueAsBytes(rounded),
                original.machineId(), original.sessionId(), original.source()));
    }
}
