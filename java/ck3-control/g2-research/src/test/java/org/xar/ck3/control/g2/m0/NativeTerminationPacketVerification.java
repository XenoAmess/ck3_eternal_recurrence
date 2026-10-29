package org.xar.ck3.control.g2.m0;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.DoubleNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.warpolicy.NativeTerminationOptions;
import org.xar.ck3.control.warpolicy.ReviewedSourceRegistry;
import org.xar.ck3.control.warpolicy.WarOutcomeStakesProjector;

/** Original complete cache/oracle corpus plus native-packet ingress regression after the shared extraction. */
public final class NativeTerminationPacketVerification {
    public record Counts(int originalVectors, int validCacheRows, int nativePacketComparisons, int additionalRefusals) { }
    private NativeTerminationPacketVerification() { }

    public static void main(String[] args) throws IOException {
        if (args.length != 1) { throw new IllegalArgumentException("actual existing original war-outcome corpus required"); }
        try (InputStream input = Files.newInputStream(Path.of(args[0]))) {
            System.out.println("M0_NATIVE_PACKET_PASS " + verify(input));
        }
    }
    public static Counts verify(InputStream input) throws IOException {
        if (input == null) { throw new IOException("original eleven-method native-cache corpus required"); }
        WarOutcomeStakesProjector projector = new WarOutcomeStakesProjector(ReviewedSourceRegistry.bundled());
        int vectors = 0; int validRows = 0; ObjectNode baseline = null;
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(input, StandardCharsets.UTF_8))) {
            String line = reader.readLine();
            if (line == null) { throw new IOException("original producer header missing"); }
            JsonNode header = StrictJson.parse(line.getBytes(StandardCharsets.UTF_8));
            check(header.path("tests_run").isIntegralNumber() && header.path("tests_run").intValue() == 11
                    && header.path("vector_count").isIntegralNumber() && header.path("vector_count").intValue() == 62,
                    "complete original eleven-method/62-vector corpus required");
            while ((line = reader.readLine()) != null) {
                JsonNode vector = StrictJson.parse(line.getBytes(StandardCharsets.UTF_8), StrictJson.EXPLICIT_MAX_BYTES);
                byte[] raw = StrictJson.text(vector.get("input_json")).getBytes(StandardCharsets.UTF_8);
                if (vector.path("expected_kind").asText().equals("invalid_contract")) {
                    refusal(() -> projector.project(raw));
                } else {
                    JsonNode actual = StrictJson.parse(projector.project(raw));
                    check(actual.equals(vector.get("expected")), "original fromCache consumer changed at vector " + vectors);
                    JsonNode source = StrictJson.parse(raw);
                    JsonNode rows = source.path("snapshot").get("war_termination_options");
                    if (rows != null && rows.isArray()) {
                        for (JsonNode row : rows) {
                            if (!row.isObject() || !row.path("war_id").isIntegralNumber()) { continue; }
                            try {
                                NativeTerminationOptions cache = NativeTerminationOptions.fromCache(row, row.path("war_id").intValue());
                                ObjectNode nativePacket = nativePacket((ObjectNode) row);
                                var parsed = NativeTerminationOptions.normalizeNativePacket(nativePacket, cache.warId());
                                check(parsed.warId() == cache.warId() && parsed.side() == cache.side() && parsed.primary() == cache.primary()
                                        && parsed.relativeScore() == cache.relativeScore() && parsed.activeCasusBelli() == cache.activeCasusBelli()
                                        && parsed.casusBelli().equals(cache.casusBelli()), "native/cache interpretations differ");
                                ObjectNode expectedPacket = nativePacket.deepCopy(); expectedPacket.put("source", "native");
                                check(parsed.normalized().equals(expectedPacket), "packet normalization changed native fields");
                                parsed.normalized().removeAll(); check(!parsed.normalized().isEmpty(), "packet accessor leaked mutable state");
                                if (baseline == null) { baseline = (ObjectNode) row.deepCopy(); }
                                validRows++;
                            } catch (ContractViolationException unavailableCacheRow) {
                                // The complete projector result above already matched the real oracle for this unavailable row.
                            }
                        }
                    }
                }
                vectors++;
            }
        }
        check(vectors == 62 && validRows > 0 && baseline != null, "original full cache consumers and valid rows required");
        int extra = 0; int warId = baseline.path("war_id").intValue();
        ObjectNode source = nativePacket(baseline); source.put("source", "forged"); refusal(() -> NativeTerminationOptions.normalizeNativePacket(source, warId)); extra++;
        ObjectNode sequence = nativePacket(baseline); sequence.put("query_sequence", 1); refusal(() -> NativeTerminationOptions.normalizeNativePacket(sequence, warId)); extra++;
        ObjectNode booleanId = nativePacket(baseline); booleanId.put("war_id", true); refusal(() -> NativeTerminationOptions.normalizeNativePacket(booleanId, warId)); extra++;
        ObjectNode floatId = nativePacket(baseline); floatId.set("war_id", DoubleNode.valueOf(warId)); refusal(() -> NativeTerminationOptions.normalizeNativePacket(floatId, warId)); extra++;
        ObjectNode wrongCache = baseline.deepCopy(); wrongCache.put("query_sequence", true); refusal(() -> NativeTerminationOptions.fromCache(wrongCache, warId)); extra++;
        ObjectNode missingSequence = baseline.deepCopy(); missingSequence.remove("query_sequence"); refusal(() -> NativeTerminationOptions.fromCache(missingSequence, warId)); extra++;
        return new Counts(vectors, validRows, validRows, extra);
    }
    private static ObjectNode nativePacket(ObjectNode cache) {
        ObjectNode packet = cache.deepCopy();
        for (String key : List.of("query_sequence", "queried_snapshot_id", "queried_revision", "queried_native_revision", "episode_run_id", "queried_connection_generation")) {
            packet.remove(key);
        }
        return packet;
    }
    private static void refusal(Runnable runnable) {
        try { runnable.run(); }
        catch (ContractViolationException expected) { return; }
        throw new AssertionError("wrong native/cache contract accepted");
    }
    private static void check(boolean condition, String message) { if (!condition) { throw new AssertionError(message); } }
}
