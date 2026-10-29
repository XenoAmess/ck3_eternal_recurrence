package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.List;
import java.util.stream.Stream;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;

final class UnhandledEventEvidenceJsonTest {
    private static ObjectValue golden() throws IOException {
        try (InputStream resource = UnhandledEventEvidenceJsonTest.class.getResourceAsStream("/unhandledevent/unhandled-event-evidence-body-golden-v1.json.gz")) {
            if (resource == null) throw new IOException("mandatory actual original before/after bodies missing; NOT RUN");
            byte[] packed = resource.readNBytes(65_537); assertTrue(packed.length <= 65_536);
            try (InputStream stream = new GZIPInputStream(new ByteArrayInputStream(packed))) {
                byte[] raw = stream.readNBytes(1_048_577); assertTrue(raw.length <= 1_048_576);
                ObjectValue root = object(parse(raw));
                assertEquals("xar.ck3.unhandled-event-golden/v1", text(root, "schema"));
                assertEquals(10, objects(root, "body_cases").size(), "all real old before/after paths are mandatory");
                return root;
            }
        }
    }

    @TestFactory Stream<DynamicTest> actualOldProducerBodies() throws IOException {
        return objects(golden(), "body_cases").stream().map(row -> DynamicTest.dynamicTest(text(row, "name"), () -> {
            byte[] beforeRequest = encode(row.get("before_request"));
            Value before = parse(UnhandledEventEvidenceJson.encodeBody(UnhandledEventEvidenceJson.before(
                    UnhandledEventEvidenceJson.decodeBefore(beforeRequest))));
            assertEquals(row.get("expected_before"), before);
            Value after = parse(UnhandledEventEvidenceJson.encodeBody(UnhandledEventEvidenceJson.after(
                    UnhandledEventEvidenceJson.decodeAfter(encode(row.get("after_request"))))));
            assertEquals(row.get("expected_after"), after);
            assertFalse(yes(object(after), "replay_allowed"));
        }));
    }

    @Test void wrapperAndIdentityTokensRejectTypeChanges() throws IOException {
        ObjectValue request = o(objects(golden(), "body_cases").getFirst(), "before_request");
        assertThrows(IllegalArgumentException.class, () -> UnhandledEventEvidenceJson.decodeBefore(encode(request.with("unknown", NULL))));
        ObjectValue planned = o(request, "planned");
        for (Value invalid : List.of(new BooleanValue(true), new FloatingValue(3.0))) {
            ObjectValue changed = request.with("planned", planned.with("revision", invalid));
            assertThrows(IllegalArgumentException.class, () -> UnhandledEventEvidenceJson.before(
                    UnhandledEventEvidenceJson.decodeBefore(encode(changed))));
        }
        ObjectValue afterRequest = o(objects(golden(), "body_cases").getFirst(), "after_request");
        ObjectValue noTicket = afterRequest.with("ticket", NULL);
        assertEquals(NULL, parse(UnhandledEventEvidenceJson.encodeBody(UnhandledEventEvidenceJson.after(
                UnhandledEventEvidenceJson.decodeAfter(encode(noTicket))))));
    }
}
