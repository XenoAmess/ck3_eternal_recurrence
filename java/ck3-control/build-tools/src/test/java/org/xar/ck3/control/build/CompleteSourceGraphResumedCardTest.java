package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.build.CompleteSourceGraphMaterializer.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Real Card constructor and exact persisted reader; synthetic size metadata does not claim materialization. */
final class CompleteSourceGraphResumedCardTest {
    @TempDir Path temporary;
    private Card card(long maximum) throws Exception {
        Path original = temporary.resolve("original-contract.json");
        if (Files.notExists(original)) Files.writeString(original, "{\"scope\":\"source-only-card-boundary-test\"}");
        FileRef ref = FileRef.measure(original);
        return new Card("xar.complete-source-graph-operation-card/v1", "synthetic-r2-source-card", "/root/source03_audit",
                "2026-10-23T00:00:00Z", "2026-10-23T00:01:00Z", Operation.MATERIALIZE, ref, ref, ref, ref, ref, ref, null,
                temporary.resolve("new-source").toString(), temporary.resolve("new-metadata").toString(), maximum, 4L << 20,
                "FULL_GRAPH_SOURCE_OPERATION_ADMITTED");
    }
    @Test void actualR2CardConstructionPersistedReadAndProfileAdmissionAcceptExactlyEightyMiB() throws Exception {
        Card r2 = card(80L << 20); var mapper = ControlBuild.strictMapper();
        byte[] encoded = mapper.writeValueAsBytes(r2); Path saved = temporary.resolve("r2-operation-card.json"); Files.write(saved, encoded);
        assertEquals(r2, read(FileRef.measure(saved), Card.class));
        assertEquals(r2, mapper.readValue(encoded, Card.class));
        requireProfileBudget(CompleteSourceGraph.Profile.G2_FULL_PARITY_20261024_R2, r2.maxSourceNativeBytes());
        NativeSize aboveLegacy = new NativeSize(3000, 1000, 39L << 20, 60L << 20, 4096000, (60L << 20) + 4096000);
        requireSize(aboveLegacy, CompleteSourceGraph.Profile.G2_FULL_PARITY_20261024_R2);
        assertThrows(IllegalArgumentException.class, () -> requireSize(aboveLegacy, CompleteSourceGraph.Profile.G2_FULL_PARITY_20261024));
        assertFalse(Files.exists(Path.of(r2.sourceRoot()))); assertFalse(Files.exists(Path.of(r2.metadataRoot())));
    }
    @Test void oldProfileCapsRemainExactAndCannotAuthorizeAnR2Copy() throws Exception {
        for (CompleteSourceGraph.Profile profile : java.util.List.of(CompleteSourceGraph.Profile.G2_RESEARCH_20261023,
                CompleteSourceGraph.Profile.G2_STABILIZATION_20261023, CompleteSourceGraph.Profile.G2_FULL_PARITY_20261024)) {
            Card historical = card(profile.maxNativeBytes()); requireProfileBudget(profile, historical.maxSourceNativeBytes());
            assertThrows(IOException.class, () -> requireProfileBudget(CompleteSourceGraph.Profile.G2_FULL_PARITY_20261024_R2, historical.maxSourceNativeBytes()));
            assertThrows(IOException.class, () -> requireProfileBudget(profile, 80L << 20));
        }
        assertThrows(IllegalArgumentException.class, () -> card(79L << 20)); assertThrows(IllegalArgumentException.class, () -> card((80L << 20) + 1));
        ObjectNode fractional = ControlBuild.strictMapper().valueToTree(card(80L << 20)); fractional.put("max_source_native_bytes", 83886080.0);
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().treeToValue(fractional, Card.class));
    }
}
