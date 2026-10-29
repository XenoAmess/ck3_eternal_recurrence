package org.xar.ck3.control.g2.m0;

import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Default Surefire bridges to the same substantial verification implementations, never an optional skip. */
final class M0ResearchTest {
    @Test void productionV7PureDecisionBoundaries() {
        M0DomainVerification.main(new String[0]);
    }

    @Test void actualOriginalProducerPoliticalBranchesAndRoundtrip(@TempDir Path directory) throws Exception {
        String name = "/org/xar/ck3/control/warpolicy/war_outcome_stakes_golden_v1.jsonl";
        try (InputStream input = M0ResearchTest.class.getResourceAsStream(name)) {
            if (input == null) { throw new IllegalStateException("required real original-producer corpus absent: " + name); }
            byte[] raw = input.readNBytes(2 * 1024 * 1024 + 1);
            if (raw.length == 0 || raw.length > 2 * 1024 * 1024) { throw new IllegalStateException("original producer corpus outside byte contract"); }
            Path corpus = directory.resolve("actual-original-war-outcome-stakes.jsonl");
            Files.write(corpus, raw, StandardOpenOption.CREATE_NEW);
            M0PoliticalVerification.main(new String[] {corpus.toString()});
        }
    }
}
