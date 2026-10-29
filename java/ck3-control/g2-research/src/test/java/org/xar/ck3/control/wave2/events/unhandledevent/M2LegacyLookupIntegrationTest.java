package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.M2LifecycleFixtures.*;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m2.M2Payload;
import org.xar.ck3.control.g2.m2.M2Payload.Operation;
import org.xar.ck3.control.g2.m2.M2Research;

/** The old full reader and receipt ABIs through the common wire, using the sole existing offline publisher. */
final class M2LegacyLookupIntegrationTest {
    private static final String LOOKUP_INPUT = "xar.events-source-reviewed-lookup-input/v1";
    private static final String LOOKUP_RESULT = "xar.events-source-reviewed-lookup-result/v1";
    @TempDir Path temporary;

    @Test void fullLookupMovesFromUnknownToExactPublishedEntryAndReopenedReaderThroughTheCommonWire() throws IOException {
        Fixture fixture = fixture(temporary.resolve("lookup-lifecycle"));
        M2Research domain = new M2Research(fixture.sources());
        ObjectValue plan = object(exchange(domain, fixture.originalRequest(), Operation.EVENT_PLAN_CANDIDATE, o(fixture.row(), "request")));
        ObjectValue capture = o(plan, "unhandled_event_fallback");
        assertNotNull(capture);
        ObjectValue input = lookupInput(capture);
        ObjectValue unknown = object(exchange(domain, fixture.originalRequest(), Operation.EVENT_REGISTRY_LOOKUP, input));
        assertEquals(Set.of("schema", "entry", "audit"), unknown.fields().keySet());
        assertEquals(s(LOOKUP_RESULT), v(unknown, "schema"));
        assertEquals(NULL, v(unknown, "entry"), "unknown is explicit null rather than an invented known entry");
        assertEquals(s("unknown"), v(o(unknown, "audit"), "status"));
        assertFalse(Files.exists(fixture.state().resolve("evidence")), "read-only lookup cannot publish knowledge");

        ObjectValue before = object(exchange(domain, fixture.originalRequest(), Operation.EVENT_BEFORE, beforeInput(plan, "c".repeat(32))));
        ExactRef beforeRef = write(fixture.incidents().resolve("c".repeat(32) + ".before.json"), RetainedJson.encode(before));
        ObjectValue after = object(exchange(domain, fixture.originalRequest(), Operation.EVENT_AFTER,
                afterInput(ticket(before, beforeRef), acknowledgedOutcome(before, true))));
        assertEquals(reference(beforeRef), v(after, "before"));
        assertEquals(b(true), v(after, "event_instance_advanced_verified"));
        assertEquals(b(false), v(after, "replay_allowed"));
        OfflineEventBatchAnalyzer.Request batch = batch(fixture, "lookup-first", before, after);
        assertEquals(batch, OfflineEventBatchAnalyzer.decode(RetainedJson.encode(batchInput(batch))));
        OfflineEventBatchAnalyzer.Result publication = OfflineEventBatchAnalyzer.run(fixture.batchConfiguration(), batch);
        assertEquals(1, array(publication.reportDocument(), "entries").size());
        assertTrue(array(publication.reportDocument(), "unresolved").isEmpty());
        assertEquals(1, publication.grants().added());
        assertDoesNotThrow(() -> OfflineEventBatchAnalyzer.encode(publication));

        ObjectValue known = object(exchange(domain, fixture.originalRequest(), Operation.EVENT_REGISTRY_LOOKUP, input));
        assertEquals(Set.of("schema", "entry", "audit"), known.fields().keySet());
        assertEquals(s(LOOKUP_RESULT), v(known, "schema"));
        ObjectValue entry = o(known, "entry"), audit = o(known, "audit");
        assertNotNull(entry); assertNotNull(audit);
        assertEquals(s(SourceReviewedEventConsumer.SCHEMA), v(entry, "schema"));
        assertEquals(s("offline-source-reviewed"), v(audit, "status"));
        assertEquals(s("exact"), v(audit, "binding_mode"));
        assertEquals(b(false), v(entry, "material_effects_verified"));
        assertEquals(b(false), v(entry, "registry_contract_accepted"));
        assertEquals(b(false), v(audit, "material_effects_verified"));
        assertEquals(b(false), v(audit, "registry_contract_accepted"));
        Path published = Path.of(text(audit, "entry_path"));
        byte[] publishedRaw = Files.readAllBytes(published);
        assertEquals(entry, RetainedJson.parse(publishedRaw), "the full legacy entry is the actual persisted producer output");
        assertEquals(s(sha(publishedRaw)), v(audit, "entry_sha256"));
        assertTrue(publication.outputs().stream().anyMatch(ref -> ref.path().equals(published.toString())
                && ref.bytes() == publishedRaw.length && ref.sha256().equals(sha(publishedRaw))));
        SourceReviewedEventConsumer.ReviewLookup direct = SourceReviewedEventConsumer.lookup(capture, TrustedEventSourceContext.open(fixture.sources()));
        assertEquals(entry, direct.entry().orElseThrow()); assertEquals(audit, direct.audit());
        assertEquals(known, exchange(new M2Research(fixture.sources()), fixture.originalRequest(), Operation.EVENT_REGISTRY_LOOKUP, input));

        byte[] committed = Files.readAllBytes(Path.of(publication.report().path()));
        OfflineEventBatchAnalyzer.Result repeated = OfflineEventBatchAnalyzer.run(fixture.batchConfiguration(), batch);
        assertTrue(repeated.idempotent()); assertEquals(0, repeated.grants().added());
        assertArrayEquals(committed, Files.readAllBytes(Path.of(repeated.report().path())));
        assertEquals(known, exchange(domain, fixture.originalRequest(), Operation.EVENT_REGISTRY_LOOKUP, input));
    }

    @Test void lookupRequiresTheExactLegacyWrapperAndNeverTrustsCallerKnownOrRootAssertions() throws IOException {
        Fixture fixture = fixture(temporary.resolve("lookup-errors"));
        M2Research domain = new M2Research(fixture.sources());
        ObjectValue capture = o(object(exchange(domain, fixture.originalRequest(), Operation.EVENT_PLAN_CANDIDATE,
                o(fixture.row(), "request"))), "unhandled_event_fallback");
        ObjectValue valid = lookupInput(capture);
        List<ObjectValue> invalid = List.of(
                valid.with("schema", s("unsupported")),
                obj(f("schema", s(LOOKUP_INPUT))),
                valid.with("capture", NULL),
                valid.with("capture", b(true)),
                valid.with("capture", i(1)),
                valid.with("capture", new ArrayValue(List.of())),
                valid.with("state_directory", s(fixture.state().toString())),
                valid.with("known", b(true)));
        for (ObjectValue input : invalid) assertThrows(IllegalArgumentException.class,
                () -> exchange(domain, fixture.originalRequest(), Operation.EVENT_REGISTRY_LOOKUP, input));
        ObjectValue claimed = capture.with("registry_known", b(true)).with("offline_followup_required", b(false));
        ObjectValue actual = object(exchange(domain, fixture.originalRequest(), Operation.EVENT_REGISTRY_LOOKUP, lookupInput(claimed)));
        assertEquals(NULL, v(actual, "entry")); assertEquals(s("unknown"), v(o(actual, "audit"), "status"));
        assertFalse(Files.exists(fixture.state().resolve("evidence")));
    }

    @Test void allElevenOriginalReceiptProducerVectorsPreserveFullResultOrExactRejectionAndNullableResult() throws IOException {
        Fixture source = fixture(temporary.resolve("receipt-source"));
        ObjectValue corpus = resource("/unhandledevent/source-reviewed-populist-receipt-golden-v1.json.gz", true);
        assertEquals(s("xar.source-reviewed-populist-receipt-golden/v1"), v(corpus, "schema"));
        List<ObjectValue> rows = objects(corpus, "cases"); assertEquals(11, rows.size());
        Set<String> names = new HashSet<>(); int nullResults = 0;
        for (ObjectValue row : rows) {
            String name = text(row, "name"); assertNotNull(name); assertTrue(names.add(name));
            ObjectValue input = obj(f("schema", s(SourceReviewedPopulistReceipt.SCHEMA)), f("body", v(row, "body")));
            if (yes(row, "rejected")) {
                ProjectionDomainRejection error = assertThrows(ProjectionDomainRejection.class,
                        () -> exchange(new M2Research(), source.originalRequest(), Operation.EVENT_SOURCE_REVIEWED_RECEIPT, input), name);
                assertEquals(text(row, "error"), error.getMessage(), name);
            } else {
                Value result = exchange(new M2Research(), source.originalRequest(), Operation.EVENT_SOURCE_REVIEWED_RECEIPT, input);
                assertEquals(v(row, "expected"), result, name);
                if (result instanceof NullValue) nullResults++;
                else {
                    ObjectValue credit = object(result);
                    for (String key : List.of("business_success_inferred", "war_started_verified", "victory_verified",
                            "title_retention_verified", "replay_allowed")) assertEquals(b(false), v(credit, key), name + ": " + key);
                }
            }
        }
        assertTrue(nullResults > 0, "the original receipt ABI explicitly permits null");
        ObjectValue body = o(rows.getFirst(), "body"), result = o(body, "result"), post = o(result, "event_selection");
        for (Value invalid : List.of(b(true), RetainedJson.parse("1.0".getBytes(StandardCharsets.UTF_8)), s("1"))) {
            ObjectValue changed = body.with("result", result.with("event_selection", post.with("ending_revision", invalid)));
            ObjectValue input = obj(f("schema", s(SourceReviewedPopulistReceipt.SCHEMA)), f("body", changed));
            assertThrows(IllegalArgumentException.class,
                    () -> exchange(new M2Research(), source.originalRequest(), Operation.EVENT_SOURCE_REVIEWED_RECEIPT, input));
        }
        for (ObjectValue invalid : List.of(
                obj(f("schema", s(SourceReviewedPopulistReceipt.SCHEMA))),
                obj(f("schema", s(SourceReviewedPopulistReceipt.SCHEMA)), f("body", b(true))),
                obj(f("schema", s(SourceReviewedPopulistReceipt.SCHEMA)), f("body", NULL), f("extra", NULL)))) {
            assertThrows(IllegalArgumentException.class,
                    () -> exchange(new M2Research(), source.originalRequest(), Operation.EVENT_SOURCE_REVIEWED_RECEIPT, invalid));
        }
    }

    private static ObjectValue lookupInput(ObjectValue capture) {
        return obj(f("schema", s(LOOKUP_INPUT)), f("capture", capture));
    }

    private static Value exchange(M2Research domain, ExactRef source, Operation operation, ObjectValue input) {
        ProjectionJson payload = M2Payload.input(operation, ProjectionJson.object(RetainedJson.encode(input), M2Payload.MAX_BYTES));
        G2Request request = new G2Request("m2-legacy-" + operation.wire(), Milestone.M2,
                new G2Source(MACHINE, TIME, "1.20.0.4", source), payload);
        G2Request transported = G2Wire.decodeRequest(G2Wire.encodeRequest(request));
        assertEquals(request.requestId(), transported.requestId()); assertEquals(request.milestone(), transported.milestone());
        assertEquals(request.source(), transported.source()); assertArrayEquals(request.payload().bytes(), transported.payload().bytes());
        G2Response response = domain.evaluate(transported);
        G2Response reloaded = G2Wire.decodeResponse(G2Wire.encodeResponse(response));
        assertEquals(request.requestId(), reloaded.requestId()); assertEquals(request.source(), reloaded.source());
        assertEquals(Milestone.M2, reloaded.milestone()); assertArrayEquals(response.result().bytes(), reloaded.result().bytes());
        M2Payload.Result decoded = M2Payload.decodeResult(reloaded.result()); assertEquals(operation, decoded.operation());
        return RetainedJson.parse(decoded.result().bytes());
    }
}

