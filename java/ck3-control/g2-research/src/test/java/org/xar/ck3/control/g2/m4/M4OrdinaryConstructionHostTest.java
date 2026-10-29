package org.xar.ck3.control.g2.m4;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionCodec;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec;
import org.xar.ck3.control.g2.common.G2Response;
import java.util.concurrent.atomic.AtomicInteger;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionConsumer;

/** Same host entry and real common wire, separated from the domain test to avoid a Maven module cycle. */
final class M4OrdinaryConstructionHostTest {
    @Test void sameM4HostRouteAndCommonWireCarryEveryOriginalProducerVector() throws Exception {
        byte[] compressed; String configured = System.getProperty("wartime.original.corpus");
        if (configured == null) {
            try (InputStream resource = getClass().getResourceAsStream("/m4producer/wartime-original02.json.gz")) {
                if (resource == null) throw new IOException("required unchanged original wartime31 resource absent");
                compressed = resource.readNBytes(32_001);
            }
        } else compressed = Files.readAllBytes(Path.of(configured));
        assertEquals(6379, compressed.length); String digest = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(compressed));
        assertEquals("4b3cf840085e5f3d53e290b4ea862e1357a3341a55180ff3670675caa5f6a585", digest);
        JsonNode golden;
        try (GZIPInputStream gzip = new GZIPInputStream(new java.io.ByteArrayInputStream(compressed))) {
            byte[] raw = gzip.readNBytes(524_289); assertTrue(raw.length <= 524_288); golden = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).readTree(raw);
        }
        assertEquals(31, golden.get("cases").size());
        G2Source source = new G2Source("xenoamess-full-tower-eb9d2c1186", "2026-10-22T23:00:00Z", "synthetic-original31-corpus-not-live",
                new ExactRef("retained-original-wartime31", compressed.length, digest));
        AtomicInteger contextReads = new AtomicInteger();
        M4OrdinaryConstructionPort adapter = new M4OrdinaryConstructionPort(new M4Research()::evaluate, () -> {
            contextReads.incrementAndGet(); return new M4OrdinaryConstructionPort.Context("ordinary-port", source);
        });
        byte[] lastInput = null; byte[] ampleInput = null;
        for (JsonNode row : golden.get("cases")) {
            ObjectNode input = StrictJson.object(); input.put("schema", OrdinaryWartimeConstructionCodec.SCHEMA);
            input.put("stage", "BEFORE_OPTIONAL_QUERY"); input.put("original_selected_step", "native-war-army-route-v1");
            input.putNull("original_phase");
            input.put("opportunity", "CONTINUE_SELECTED_WORK"); input.set("cash_input", row.get("request"));
            input.putNull("quoted_outlay"); input.putNull("financing_request"); byte[] raw = StrictJson.canonical(input, OrdinaryWartimeConstructionCodec.MAX_BYTES);
            G2Request request = new G2Request("ordinary-construction-new-composition", Milestone.M4, source,
                    ProjectionJson.object(raw, OrdinaryWartimeConstructionCodec.MAX_BYTES));
            G2Request decoded = G2Wire.decodeRequest(G2Wire.encodeRequest(request)); assertArrayEquals(raw, decoded.payload().bytes());
            var response = G2Wire.decodeResponse(G2Wire.encodeResponse(new M4Research().evaluate(decoded)));
            assertEquals(source, response.source()); assertEquals(request.requestId(), response.requestId());
            var actual = OrdinaryWartimeConstructionCodec.verifyResponse(raw, response.result().bytes());
            var portActual = adapter.evaluate(new OrdinaryWartimeConstructionCodec.ObservedRequest(raw));
            assertArrayEquals(OrdinaryWartimeConstructionCodec.encode(actual), OrdinaryWartimeConstructionCodec.encode(portActual));
            assertEquals("native-war-army-route-v1", actual.selectedStep().orElseThrow()); assertTrue(actual.continueOrdinaryPlanner()); assertFalse(actual.canSubmitAction());
            G2Request old = new G2Request("old-cash-route", Milestone.M4, source,
                    ProjectionJson.object(StrictJson.canonical(row.get("request")), WartimeConstructionCodec.MAX_BYTES));
            assertEquals(row.get("expected"), StrictJson.parse(new M4Research().evaluate(old).result().bytes()));
            if ("exact_ample_threshold".equals(row.get("name").textValue())) ampleInput = raw;
            lastInput = raw;
        }
        assertEquals(31, contextReads.get()); byte[] retained = java.util.Objects.requireNonNull(lastInput);
        var observed = new OrdinaryWartimeConstructionCodec.ObservedRequest(retained);
        G2Source foreign = new G2Source("foreign-machine", source.observedAtUtc(), source.exactBuild(), source.sourceRef());
        var wrongSource = new M4OrdinaryConstructionPort(request -> {
            var response = new M4Research().evaluate(request);
            return new G2Response(response.requestId(), response.milestone(), foreign, response.result());
        }, () -> new M4OrdinaryConstructionPort.Context("wrong-source", source));
        assertThrows(IllegalArgumentException.class, () -> wrongSource.evaluate(observed));
        var wrongResult = new M4OrdinaryConstructionPort(request -> new G2Response(request.requestId(), Milestone.M4, source,
                ProjectionJson.object(StrictJson.canonical(StrictJson.object().put("schema", "invented-result")), 4096)),
                () -> new M4OrdinaryConstructionPort.Context("wrong-result", source));
        assertThrows(IllegalArgumentException.class, () -> wrongResult.evaluate(observed));
        // Exercise the existing consumer through the real registered M4 evaluator with
        // the retained observation's actual absent financing; no NoPending is inferred.
        ObjectNode optional = (ObjectNode) StrictJson.parse(java.util.Objects.requireNonNull(ampleInput), OrdinaryWartimeConstructionCodec.MAX_BYTES);
        optional.put("original_selected_step", "life-advance"); optional.put("opportunity", "ORDINARY_ADVANCE");
        var optionalObserved = new OrdinaryWartimeConstructionCodec.ObservedRequest(
                StrictJson.canonical(optional, OrdinaryWartimeConstructionCodec.MAX_BYTES));
        AtomicInteger optionalQueries = new AtomicInteger();
        var deferred = OrdinaryWartimeConstructionConsumer.plan(() -> optionalObserved, () -> {
            optionalQueries.incrementAndGet();
            return new OrdinaryWartimeConstructionConsumer.UnavailableQuote(
                    OrdinaryWartimeConstructionConsumer.UnavailableReason.NATIVE_PROVIDER_UNAVAILABLE);
        }, adapter);
        assertEquals(0, optionalQueries.get());
        assertEquals("DEFER_OPTIONAL_CONSTRUCTION", deferred.disposition().name());
        assertEquals("FINANCING_OBSERVATION_UNAVAILABLE", deferred.reason().orElseThrow().name());
        assertTrue(deferred.continueOrdinaryPlanner()); assertFalse(deferred.canSubmitAction());
    }
}

