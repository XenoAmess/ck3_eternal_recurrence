package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.TestFactory;
import org.junit.jupiter.api.io.TempDir;

/** Replays original Python-produced facts against original stock bytes; no current installation qualification. */
final class OfflineEventSourceAnalyzerTest {
    @TempDir Path temporary;
    @TestFactory Stream<DynamicTest> originalSourceBodiesReproduceTheOriginalFactsForExactAndHistoricalBindings() throws IOException {
        ObjectValue corpus = SourceReviewedEventConsumerTest.golden();
        List<ObjectValue> pipelines = objects(corpus, "cases").stream().filter(row -> eq(row, "mode", s("pipeline"))).toList();
        assertEquals(9, pipelines.size());
        return pipelines.stream().map(row -> DynamicTest.dynamicTest(text(row, "name"), () -> {
            SourceReviewedEventConsumerTest.Relocated input = SourceReviewedEventConsumerTest.relocate(corpus, row, temporary.resolve(text(row, "name")));
            Path entry;
            try (Stream<Path> entries = Files.list(input.state().resolve("evidence/event-source-registry"))) {
                entry = entries.filter(path -> path.getFileName().toString().matches("[0-9a-f]{64}\\.json")).findFirst().orElseThrow();
            }
            ObjectValue originalEntry = RetainedJson.object(RetainedJson.parse(Files.readAllBytes(entry)));
            ObjectValue facts = RetainedJson.object(RetainedJson.parse(Files.readAllBytes(Path.of(text(o(originalEntry, "source_facts"), "path")))));
            Path source = Path.of(text(facts, "source_path")); byte[] originalSource = Files.readAllBytes(source);
            ObjectValue capture = o(RetainedJson.object(input.plan()), "unhandled_event_fallback");
            OfflineEventSourceAnalyzer.Analysis actual = OfflineEventSourceAnalyzer.analyzeReviewedBinding(o(facts, "binding"), capture,
                    source, text(facts, "source_relative"), originalSource);
            assertEquals(text(facts, "fingerprint"), actual.fingerprint());
            assertEquals(facts, actual.facts());
            ObjectValue wrongCount = capture.with("snapshot_option_count", new BooleanValue(true));
            assertThrows(IllegalArgumentException.class, () -> OfflineEventSourceAnalyzer.analyze(wrongCount, source, text(facts, "source_relative"), originalSource));
            byte[] drift = java.util.Arrays.copyOf(originalSource, originalSource.length + 1); drift[drift.length - 1] = '\n';
            assertNotEquals(actual.fingerprint(), OfflineEventSourceAnalyzer.analyzeReviewedBinding(o(facts, "binding"), capture,
                    source, text(facts, "source_relative"), drift).fingerprint());
        }));
    }
}
