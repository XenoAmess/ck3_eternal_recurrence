package org.xar.ck3.control.g2.m4;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.OffsetDateTime;
import java.util.HexFormat;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionCodec;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionConsumers;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionModel;

/** Finite offline verification of the actual G2 M4 entry, using the preserved original producer corpus. */
public final class M4ResearchVerification {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);
    private static final int EXPANDED_LIMIT = 524_288;
    private M4ResearchVerification() { }

    public record Result(int originalProducerVectors, int rejectedBoundaryInputs, int freshConsumerReads) { }

    public static Result verify(Path corpus) throws IOException, NoSuchAlgorithmException {
        byte[] compressed = Files.readAllBytes(corpus);
        check(compressed.length <= 32_000, "compressed corpus budget");
        JsonNode golden;
        try (InputStream input = new GZIPInputStream(new java.io.ByteArrayInputStream(compressed))) {
            byte[] expanded = input.readNBytes(EXPANDED_LIMIT + 1);
            check(expanded.length <= EXPANDED_LIMIT, "expanded corpus budget");
            golden = JSON.readTree(expanded);
        }
        check("xar.wartime-construction-original-producer-golden.v1".equals(golden.path("schema").textValue()), "corpus schema");
        check(golden.path("cases").size() == 31, "complete original vector set");
        check(golden.path("original_consumer_regressions").size() == 2, "original full consumer provenance");
        String digest = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(compressed));
        // The original producer records an explicit +00:00 offset; common wire requires Z.
        // Convert the same instant rather than changing the original corpus provenance.
        String sourceInstant = OffsetDateTime.parse(golden.path("observed_at_utc").textValue()).toInstant().toString();
        G2Source source = new G2Source(golden.path("machine_id").textValue(), sourceInstant,
                "1.20.0.4", new ExactRef(corpus.toAbsolutePath().toString(), compressed.length, digest));
        M4Research domain = new M4Research();
        int vectors = 0;
        for (JsonNode vector : golden.path("cases")) {
            G2Request request = request(source, Milestone.M4, bytes(vector.get("request")));
            G2Request decoded = G2Wire.decodeRequest(G2Wire.encodeRequest(request));
            check(java.util.Arrays.equals(request.payload().bytes(), decoded.payload().bytes()), "opaque request persistence");
            G2Response response = G2Wire.decodeResponse(G2Wire.encodeResponse(domain.evaluate(decoded)));
            check(response.requestId().equals(request.requestId()) && response.milestone() == Milestone.M4,
                    "response identity binding");
            check(response.source().equals(source), "response evidence binding");
            check(vector.get("expected").equals(JSON.readTree(response.result().bytes())),
                    "original producer mismatch: " + vector.path("name").asText());
            vectors++;
        }

        ObjectNode original = (ObjectNode) named(golden, "exact_ample_threshold").get("request");
        int rejected = 0;
        for (String token : new String[]{"23000000.0", "true", "\"23000000\""}) {
            String text = JSON.writeValueAsString(original);
            check(text.contains("\"construction_gold_raw\":23000000"), "raw-token fixture cost");
            byte[] changed = text.replace("\"construction_gold_raw\":23000000", "\"construction_gold_raw\":" + token)
                    .getBytes(StandardCharsets.UTF_8);
            rejects(() -> domain.evaluate(request(source, Milestone.M4, changed))); rejected++;
        }
        ObjectNode missing = original.deepCopy(); missing.remove("root");
        rejects(() -> domain.evaluate(request(source, Milestone.M4, bytes(missing)))); rejected++;
        ObjectNode extra = original.deepCopy(); extra.put("priority_ready", true);
        rejects(() -> domain.evaluate(request(source, Milestone.M4, bytes(extra)))); rejected++;
        ObjectNode version = original.deepCopy(); version.put("schema", "xar.wartime-construction-cash-input.v2");
        rejects(() -> domain.evaluate(request(source, Milestone.M4, bytes(version)))); rejected++;
        rejects(() -> domain.evaluate(request(source, Milestone.M0, bytes(original)))); rejected++;
        for (byte[] malformed : new byte[][]{
                "{\"schema\":1,\"schema\":2}".getBytes(StandardCharsets.UTF_8),
                "{} {}".getBytes(StandardCharsets.UTF_8), new byte[]{(byte) 0xc3, 0x28}}) {
            rejects(() -> domain.evaluate(request(source, Milestone.M4, malformed))); rejected++;
        }

        WartimeConstructionModel.Input current = WartimeConstructionCodec.decode(bytes(original));
        WartimeConstructionModel.Input unavailable = WartimeConstructionCodec.decode(
                bytes(named(golden, "market_unavailable").get("request")));
        AtomicInteger reads = new AtomicInteger();
        WartimeConstructionModel.Decision prequote = WartimeConstructionConsumers.observeBeforeOptionalQuery(() -> {
            reads.incrementAndGet(); return current;
        });
        check(prequote.newSpendAllowed() && prequote.quotedCost().value().equals(BigInteger.ZERO), "zero-spend prequote");
        check(WartimeConstructionConsumers.observeQuotedOutlay(() -> { reads.incrementAndGet(); return current; })
                .newSpendAllowed(), "actual full quote");
        try {
            WartimeConstructionConsumers.requireCurrentBeforeIntent(() -> { reads.incrementAndGet(); return unavailable; });
            throw new AssertionError("fresh unavailable context must prevent intent");
        } catch (WartimeConstructionConsumers.DeferredConstructionException expected) {
            check(expected.decision().reason().orElseThrow() == WartimeConstructionModel.Reason.MARKET,
                    "fresh final rejection reason");
        }
        check(reads.get() == 3, "each guard must obtain current input");
        return new Result(vectors, rejected, reads.get());
    }

    private static G2Request request(G2Source source, Milestone milestone, byte[] raw) {
        return new G2Request("m4-offline-verified-request", milestone, source,
                ProjectionJson.object(raw, M4Research.MAXIMUM_PAYLOAD_BYTES));
    }
    private static JsonNode named(JsonNode golden, String name) {
        for (JsonNode vector : golden.path("cases")) if (name.equals(vector.path("name").textValue())) return vector;
        throw new AssertionError("original vector missing: " + name);
    }
    private static byte[] bytes(JsonNode value) {
        try { return JSON.writeValueAsBytes(value); }
        catch (IOException error) { throw new IllegalStateException("test JSON encoding", error); }
    }
    private static void rejects(Runnable action) {
        try { action.run(); }
        catch (IllegalArgumentException expected) { return; }
        throw new AssertionError("malformed M4 input was accepted");
    }
    private static void check(boolean passed, String reason) {
        if (!passed) throw new AssertionError(reason);
    }
}
