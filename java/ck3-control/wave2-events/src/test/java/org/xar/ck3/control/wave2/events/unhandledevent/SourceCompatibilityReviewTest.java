package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;

import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.EnumMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge;
import org.xar.ck3.control.wave2.events.sourcecatalog.EventSourceCatalogue;

final class SourceCompatibilityReviewTest {
    @TempDir Path temporary;

    @Test void completeSourceReviewNeverGrantsNativeOrExecutableContracts() throws Exception {
        var review = SourceCompatibilityReview.load();
        assertEquals(RegisteredEventKnowledge.load().keys("1.20.0.4"), review.events().keySet());
        var counts = new EnumMap<SourceCompatibilityReview.Classification, Integer>(SourceCompatibilityReview.Classification.class);
        review.events().values().forEach(row -> counts.merge(row.classification(), 1, Integer::sum));
        assertEquals(Map.of(SourceCompatibilityReview.Classification.DEPENDENCIES_IDENTICAL, 10,
                SourceCompatibilityReview.Classification.DEFINITION_IDENTICAL_DEPENDENCIES_CHANGED, 144,
                SourceCompatibilityReview.Classification.DEFINITION_CHANGED, 42,
                SourceCompatibilityReview.Classification.LEGACY_SOURCE_UNAVAILABLE, 2), counts);
        for (String key : review.events().keySet()) {
            var result = review.query(key);
            assertEquals(new StringValue("unavailable"), result.get("status"));
            assertEquals(NULL, result.get("contract")); assertEquals(NULL, result.get("observations"));
            var analysis = object(result.get("analysis"));
            assertEquals(new StringValue("unqualified"), analysis.get("native_binding_status"));
            assertEquals(new BooleanValue(false), analysis.get("material_effects_verified"));
            assertFalse(analysis.fields().containsKey("recommended_option"));
        }
        assertEquals(NULL, review.query("unregistered.987654321").get("analysis"));
    }

    @Test void resourceRejectsAuthorityClaimsWrongVersionsAndNonIntegerSchema() throws Exception {
        var root = document();
        for (Value invalid : new Value[]{new BooleanValue(true), new FloatingValue(1.0), new StringValue("1")})
            rejected(root.with("schema_version", invalid));
        rejected(root.with("native_binding_qualified", new BooleanValue(true)));
        rejected(root.with("target_build", new StringValue("1.20.0.4")));
        rejected(root.with("target_exe_sha256", new StringValue("0".repeat(64))));
        rejected(root.with("unreviewed_extra", NULL));
        var files = new LinkedHashMap<>(object(root.get("files")).fields());
        files.remove(files.keySet().iterator().next()); rejected(root.with("files", new ObjectValue(files)));
        var events = object(root.get("events")); String key = "birth.1003";
        var changed = object(events.get(key)).with("classification", new StringValue("DEPENDENCIES_IDENTICAL"));
        rejected(root.with("events", events.with(key, changed)));
        var selected = object(object(events.get(key)).get("definition"));
        rejected(root.with("events", events.with(key, object(events.get(key)).with("definition",
                selected.with("target_source_options", new BooleanValue(true))))));
    }

    @Test void sameLexerIgnoresFormattingButRetainsQuotedValuesAndTokenBoundaries() {
        String original = "event.1 = { option = { name = \"hello world\" gold = 1 } }";
        String formatted = "# comment\nevent.1={ option={name=\"hello world\" # another\ngold=1}}";
        assertEquals(EventSourceCatalogue.sourceTokenSha256(original), EventSourceCatalogue.sourceTokenSha256(formatted));
        assertNotEquals(EventSourceCatalogue.sourceTokenSha256(original),
                EventSourceCatalogue.sourceTokenSha256(original.replace("hello world", "hello  world")));
        assertNotEquals(EventSourceCatalogue.sourceTokenSha256("ab cd"), EventSourceCatalogue.sourceTokenSha256("a bcd"));
    }

    @Test void unknownOrMixedStockCannotBecomeLegacyNativeSourceEvidence() throws Exception {
        Path stock = Files.createDirectory(temporary.resolve("stock"));
        Path state = Files.createDirectory(temporary.resolve("state"));
        for (String relative : ReviewedLetterSourceRebind.installedSourceHashes().keySet()) {
            Path target = stock.resolve(relative); Files.createDirectories(target.getParent()); Files.writeString(target, "unreviewed source");
        }
        assertThrows(TrustedEventSourceContext.UnavailableException.class,
                () -> TrustedEventSourceContext.open("test-machine", state, stock));
        var evidenceOnly = TrustedEventSourceContext.openEvidence(
                new org.xar.ck3.control.contracts.projection.EventSourceReadContext("test-machine", state, stock));
        assertTrue(evidenceOnly.reviewedSourceBuild().isEmpty());
        assertThrows(TrustedEventSourceContext.UnavailableException.class, () -> evidenceOnly.requireBuild("1.20.0.4"));
    }

    private static ObjectValue document() throws Exception {
        try (var input = SourceCompatibilityReviewTest.class.getResourceAsStream(SourceCompatibilityReview.RESOURCE)) {
            assertNotNull(input);
            return object(RetainedJson.parse(input.readAllBytes(), new ParseBudget(SourceCompatibilityReview.MAXIMUM_BYTES, 100000, 32)));
        }
    }
    private static void rejected(ObjectValue object) {
        assertThrows(IllegalArgumentException.class,
                () -> SourceCompatibilityReview.parse(RetainedJson.encode(object, SourceCompatibilityReview.MAXIMUM_BYTES)));
    }
}
