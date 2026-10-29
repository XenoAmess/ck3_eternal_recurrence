package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.io.InputStream;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;

final class SourceReviewedPopulistReceiptTest {
    private static final String RESOURCE = "/unhandledevent/source-reviewed-populist-receipt-golden-v1.json.gz";
    @Test void originalProducerThroughComparatorAndSerializer() throws Exception {
        ObjectValue fixture = fixture();
        assertEquals("xar.source-reviewed-populist-receipt-golden/v1", text(fixture, "schema"));
        assertEquals(11, objects(fixture, "cases").size());
        Set<String> names = new java.util.HashSet<>();
        for (ObjectValue row : objects(fixture, "cases")) {
            assertTrue(names.add(text(row, "name")), "actual producer case name must be unique");
            byte[] request = encode(obj(f("schema", s(SourceReviewedPopulistReceipt.SCHEMA)), f("body", v(row, "body"))));
            if (yes(row, "rejected")) {
                ProjectionDomainRejection error = assertThrows(ProjectionDomainRejection.class,
                        () -> SourceReviewedPopulistReceipt.verify(SourceReviewedPopulistReceipt.decode(request)), text(row, "name"));
                assertEquals(text(row, "error"), error.getMessage());
            } else {
                Value result = parse(SourceReviewedPopulistReceipt.encodeResult(
                        SourceReviewedPopulistReceipt.verify(SourceReviewedPopulistReceipt.decode(request))));
                assertEquals(v(row, "expected"), result, text(row, "name"));
                if (result instanceof ObjectValue credit) {
                    assertEquals(b(false), credit.get("business_success_inferred"));
                    assertEquals(b(false), credit.get("war_started_verified"));
                    assertEquals(b(false), credit.get("victory_verified"));
                    assertEquals(b(false), credit.get("title_retention_verified"));
                    assertEquals(b(false), credit.get("replay_allowed"));
                }
            }
        }
    }
    @Test void revisionsRejectBooleanAndFloatingPointRepresentations() throws Exception {
        ObjectValue body = o(objects(fixture(), "cases").getFirst(), "body");
        ObjectValue result = o(body, "result"), post = o(result, "event_selection");
        for (Value invalid : java.util.List.of(b(true), parse("1.0".getBytes(java.nio.charset.StandardCharsets.UTF_8)))) {
            ObjectValue changed = put(body, f("result", put(result, f("event_selection", put(post, f("ending_revision", invalid))))));
            assertThrows(IllegalArgumentException.class, () -> SourceReviewedPopulistReceipt.verify(
                    SourceReviewedPopulistReceipt.decode(encode(obj(f("schema", s(SourceReviewedPopulistReceipt.SCHEMA)), f("body", changed))))));
        }
    }
    @Test void exactVersionedWrapperRejectsExtraAndWrongBodyTypes() {
        assertThrows(IllegalArgumentException.class, () -> SourceReviewedPopulistReceipt.decode(
                encode(obj(f("schema", s(SourceReviewedPopulistReceipt.SCHEMA)), f("body", NULL), f("extra", NULL)))));
        assertThrows(IllegalArgumentException.class, () -> SourceReviewedPopulistReceipt.decode(
                encode(obj(f("schema", s(SourceReviewedPopulistReceipt.SCHEMA)), f("body", b(true))))));
    }
    private static ObjectValue fixture() throws Exception {
        try (InputStream resource = SourceReviewedPopulistReceiptTest.class.getResourceAsStream(RESOURCE)) {
            assertNotNull(resource, "actual original producer golden is required; absence is RED");
            try (InputStream gzip = new GZIPInputStream(resource)) {
                byte[] raw = gzip.readNBytes(1_048_577);
                assertTrue(raw.length <= 1_048_576, "original producer decompressed bound");
                return RetainedJson.object(parse(raw));
            }
        }
    }
}

