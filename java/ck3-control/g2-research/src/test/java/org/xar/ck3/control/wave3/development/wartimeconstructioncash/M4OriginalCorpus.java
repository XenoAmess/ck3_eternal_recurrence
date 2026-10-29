package org.xar.ck3.control.wave3.development.wartimeconstructioncash;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.M4WartimeInputProducer.Context;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.M4WartimeInputProducer.CopiedObject;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.M4WartimeInputProducer.Outlay;

/** Shared test inputs are the unchanged captured original bytes; no synthetic finance policy or fallback. */
public final class M4OriginalCorpus {
    private M4OriginalCorpus() { }

    public static JsonNode wartime() throws IOException {
        try (InputStream input = resource("/m4producer/wartime-original02.json.gz");
                GZIPInputStream gzip = new GZIPInputStream(input)) {
            byte[] raw = gzip.readNBytes(524_289);
            if (raw.length > 524_288) { throw new IOException("wartime original exceeds its admitted expansion"); }
            return StrictJson.parse(raw, 524_288);
        }
    }

    public static JsonNode wartimeCase(String name) throws IOException {
        for (JsonNode row : wartime().path("cases")) {
            if (name.equals(row.path("name").textValue())) { return row; }
        }
        throw new IOException("captured original wartime case missing: " + name);
    }

    public static Context context(JsonNode request) {
        return new Context(new CopiedObject(wire(required(request, "snapshot"))),
                nullableObject(request, "root"), nullableObject(request, "spending"), nullableObject(request, "market"),
                nullableObject(request, "market_source_frame"), nullableObject(request, "mercenary_ledger"),
                nullableObject(request, "procurement_decision"));
    }

    public static Outlay outlay(JsonNode request) {
        JsonNode kind = required(request, "kind"), amount = required(request, "construction_gold_raw");
        StrictJson.require(kind.isTextual(), "captured kind must be a string");
        StrictJson.require(amount.isNull() || amount.isIntegralNumber(), "captured outlay must remain an integer or null");
        Optional<BigInteger> cost = amount.isNull() ? Optional.empty() : Optional.of(amount.bigIntegerValue());
        return new Outlay(kind.textValue(), cost);
    }

    public record LoanVector(String operation, String expectedKind, byte[] requestUtf8, JsonNode expected) {
        public LoanVector { requestUtf8 = requestUtf8.clone(); }
        @Override public byte[] requestUtf8() { return requestUtf8.clone(); }
    }
    public record LoanCorpus(JsonNode header, List<LoanVector> vectors) {
        public LoanCorpus { vectors = List.copyOf(vectors); }
    }

    public static LoanCorpus loan() throws IOException {
        try (InputStream input = resource("/m4producer/holyloan-original02.jsonl.gz");
                GZIPInputStream gzip = new GZIPInputStream(input)) {
            byte[] raw = gzip.readNBytes(4_194_305);
            if (raw.length > 4_194_304) { throw new IOException("loan original exceeds its admitted expansion"); }
            try (BufferedReader lines = new BufferedReader(new InputStreamReader(
                    new java.io.ByteArrayInputStream(raw), StandardCharsets.UTF_8))) {
                String first = lines.readLine();
                if (first == null) { throw new IOException("original loan corpus header missing"); }
                JsonNode header = StrictJson.parse(first.getBytes(StandardCharsets.UTF_8));
                List<LoanVector> vectors = new ArrayList<>();
                String metadata;
                while ((metadata = lines.readLine()) != null) {
                    JsonNode row = StrictJson.parse(metadata.getBytes(StandardCharsets.UTF_8));
                    String request = lines.readLine(), expected = lines.readLine();
                    if (request == null || expected == null || vectors.size() >= 1000
                            || row.path("ordinal").intValue() != vectors.size() + 1) {
                        throw new IOException("original loan corpus incomplete or sequence changed");
                    }
                    byte[] requestUtf8 = request.getBytes(StandardCharsets.UTF_8);
                    JsonNode decodedRequest = StrictJson.parse(requestUtf8);
                    vectors.add(new LoanVector(decodedRequest.path("operation").textValue(),
                            row.path("expected_kind").textValue(), requestUtf8,
                            StrictJson.parse(expected.getBytes(StandardCharsets.UTF_8))));
                }
                if (vectors.size() != header.path("vector_count").intValue()) {
                    throw new IOException("original loan corpus vector count changed");
                }
                return new LoanCorpus(header, vectors);
            }
        }
    }

    public static byte[] wire(JsonNode node) { return SdkProjectionJson.encode(node); }

    private static JsonNode required(JsonNode value, String field) {
        JsonNode child = value.get(field);
        StrictJson.require(child != null, "captured request field must be present: " + field);
        return child;
    }

    private static Optional<CopiedObject> nullableObject(JsonNode request, String field) {
        JsonNode child = required(request, field);
        return child.isNull() ? Optional.empty() : Optional.of(new CopiedObject(wire(child)));
    }

    private static InputStream resource(String path) throws IOException {
        InputStream result = M4OriginalCorpus.class.getResourceAsStream(path);
        if (result == null) { throw new IOException("actual original corpus required; missing is not a skip: " + path); }
        return result;
    }
}
