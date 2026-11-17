package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Explicit integration selectors require the two actual roots; missing inputs cannot count as skipped success. */
final class SourceCompatibilityInstalledSourcesIT {
    @TempDir Path temporary;

    @Test void javaProducerRebuildsPinnedReviewFromActualSourceRevisions() throws Exception {
        var compiled = SourceCompatibilityReviewCompiler.compile(source("xar.source.baseline"), source("xar.source.target"));
        byte[] bytes = RetainedJson.pythonCanonical(compiled.json(),
                new RetainedJson.CanonicalBudget(SourceCompatibilityReview.MAXIMUM_BYTES, 100000, 32)).bytes();
        assertEquals(SourceCompatibilityReview.RESOURCE_SHA256, SourceCompatibilityReview.sha(bytes));
    }

    @Test void currentSourceRevisionCannotBorrowOldNativeProofAndDetectsLaterMutation() throws Exception {
        Path stock = Files.createDirectory(temporary.resolve("stock")), state = Files.createDirectory(temporary.resolve("state"));
        for (String relative : SourceCompatibilityReview.load().targetStockHashes().keySet()) {
            Path target = stock.resolve(relative); Files.createDirectories(target.getParent());
            Files.copy(source("xar.source.target").resolve(relative), target);
        }
        var context = TrustedEventSourceContext.open("test-machine", state, stock);
        assertEquals(SourceCompatibilityReview.BUILD, context.reviewedSourceBuild().orElseThrow());
        assertThrows(IllegalArgumentException.class, () -> context.requireBuild("1.21.0"));
        assertThrows(IllegalArgumentException.class, () -> context.requireBuild("1.20.0.4"));
        context.verifyCurrentRoots();
        Files.writeString(stock.resolve("gui/event_windows/letter_event.gui"), "# changed installed source");
        assertThrows(TrustedEventSourceContext.UnavailableException.class, context::verifyCurrentRoots);
    }

    @Test void originalReviewedSourceStillRequiresOriginalNativeBuild() throws Exception {
        Path state = Files.createDirectory(temporary.resolve("state"));
        var context = TrustedEventSourceContext.open("test-machine", state, source("xar.source.baseline"));
        assertEquals("1.20.0.4", context.reviewedSourceBuild().orElseThrow());
        assertDoesNotThrow(() -> context.requireBuild("1.20.0.4"));
        assertThrows(IllegalArgumentException.class, () -> context.requireBuild("1.21.0"));
    }

    private static Path source(String property) throws Exception {
        String supplied = System.getProperty(property);
        assertNotNull(supplied, "explicit installed-source integration requires " + property);
        return Path.of(supplied).toRealPath();
    }
}
